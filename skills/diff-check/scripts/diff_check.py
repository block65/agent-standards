#!/usr/bin/env python3
"""Scope failure-mode checks to the lines a change actually touched.

Repo-wide these checks are noise — the same rules that yield 0-3 findings on a
commit yield four figures across a monorepo, and a check nobody can act on gets
muted. Every candidate here comes from an added line in the diff.

Findings are either `flag` (the pattern alone is the defect) or `judge` (a human
or agent has to decide against the named standard). The script never decides a
`judge` case; it hands over the context needed to decide it.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field

# Comment syntax by extension. Only leading-position comments are detected:
# a trailing comment on a code line is a different (and much noisier) case.
COMMENT_PREFIXES: dict[str, tuple[str, ...]] = {
    ".ts": ("//", "/*", "*", "*/"),
    ".tsx": ("//", "/*", "*", "*/"),
    ".js": ("//", "/*", "*", "*/"),
    ".jsx": ("//", "/*", "*", "*/"),
    ".mjs": ("//", "/*", "*", "*/"),
    ".cjs": ("//", "/*", "*", "*/"),
    ".rs": ("//", "///", "//!", "/*", "*"),
    ".go": ("//", "/*", "*"),
    ".java": ("//", "/*", "*"),
    ".c": ("//", "/*", "*"),
    ".h": ("//", "/*", "*"),
    ".css": ("/*", "*"),
    ".sql": ("--", "/*", "*"),
    ".py": ("#",),
    ".sh": ("#",),
    ".bash": ("#",),
    ".rb": ("#",),
    ".yaml": ("#",),
    ".yml": ("#",),
    ".toml": ("#",),
}

SHELL_LIKE = {".sh", ".bash", ".zsh", ".py", ".yaml", ".yml"}
SHELL_LIKE_NAMES = {"Dockerfile", "Tiltfile", "Makefile", "justfile", "compose.yaml"}

# The code checks match source syntax. Run over prose they fire on any sentence
# quoting the pattern under discussion, and a check that cries wolf gets muted.
CODE_EXTENSIONS = {
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".rs", ".go", ".java",
    ".c", ".h", ".sql", ".py", ".sh", ".bash", ".zsh", ".rb",
    ".yaml", ".yml", ".toml",
}

# `?? <empty value>` — the sentinel that turns "missing" into "present and wrong".
SENTINEL_RE = re.compile(r"\?\?\s*(\"\"|''|``|\[\]|\{\}|0\b)")

# `${VAR:-value}` and `${VAR:=value}` — a default for a value that may be required.
SHELL_DEFAULT_RE = re.compile(r"\$\{[A-Za-z_][A-Za-z0-9_]*:[-=]([^}]*)\}")

# A state/status column compared by negation rather than by the states accepted.
NEGATED_STATE_RE = re.compile(
    r"\b(state|status|kind|type|phase|stage)\b\s*(<>|!=|\bNOT\s+IN\b)",
    re.IGNORECASE,
)

# Paths whose numeric or comment density is inherent, not a defect.
DEFAULT_EXCLUDES = (
    "/generated/",
    "/node_modules/",
    "/dist/",
    "/build/",
    "/target/",
    ".css.ts",
    ".gen.ts",
    "-lock.json",
    ".lock",
    ".snap",
)

# JSDoc attaches to a declaration. Anything a `/** */` block can sit above that
# is not one of these is a line comment written in the wrong syntax.
DECLARATION_RE = re.compile(
    r"^(export\b|declare\b|default\b|abstract\b|async\s+function\b|function\b"
    r"|class\b|interface\b|type\s+\w+\s*[=<]|enum\b|namespace\b|@\w+)"
)

TS_EXTENSIONS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")

RULES = {
    "comment-on-deletion": "engineering/comments.md — never narrate past state in prose",
    "comment-added": "engineering/comments.md — comment the non-obvious, never the obvious",
    "jsdoc-misuse": "engineering/comments.md — JSDoc documents a declaration; use // for a line",
    "bare-block": "engineering/comments.md — never a bare /* */ block",
    "sentinel": "lang/javascript.md — never a sentinel; missing must stay distinguishable",
    "shell-default": "a required value has no default; missing means exit non-zero",
    "negated-state": "enumerate the states you accept, not the one you exclude",
    "magic-number": "lang/typescript.md — name the value or explain the literal",
}


@dataclass
class Finding:
    path: str
    line: int
    kind: str
    disposition: str
    snippet: str
    context: list[str] = field(default_factory=list)
    follows: str = ""

    def as_dict(self) -> dict:
        out = {
            "path": self.path,
            "line": self.line,
            "kind": self.kind,
            "disposition": self.disposition,
            "rule": RULES[self.kind],
            "snippet": self.snippet,
        }
        if self.context:
            out["removed"] = self.context
        if self.follows:
            out["describes"] = self.follows
        return out


@dataclass
class Hunk:
    path: str
    added: list[tuple[int, str]] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)


HUNK_HEADER_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def run_git(args: list[str], cwd: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise SystemExit(proc.returncode)
    return proc.stdout


def parse_diff(diff: str) -> list[Hunk]:
    """Split a `-U0` unified diff into hunks, keeping added lines with their
    new-file line numbers and the deletions they sit alongside."""
    hunks: list[Hunk] = []
    path = ""
    current: Hunk | None = None
    next_line = 0

    for raw in diff.splitlines():
        if raw.startswith("+++ "):
            target = raw[4:].strip()
            path = target[2:] if target.startswith("b/") else target
            current = None
            continue
        if raw.startswith("--- ") or raw.startswith("diff --git"):
            continue

        header = HUNK_HEADER_RE.match(raw)
        if header:
            next_line = int(header.group(1))
            current = Hunk(path=path)
            hunks.append(current)
            continue

        if current is None or path in ("", "/dev/null"):
            continue

        if raw.startswith("+"):
            current.added.append((next_line, raw[1:]))
            next_line += 1
        elif raw.startswith("-"):
            current.removed.append(raw[1:])

    return [h for h in hunks if h.added]


def untracked_hunks(cwd: str) -> list[Hunk]:
    """A new file is entirely added lines. `git diff` never shows it, and a new
    file is the most common thing a change contributes."""
    listing = run_git(["ls-files", "--others", "--exclude-standard"], cwd)
    hunks: list[Hunk] = []

    for path in listing.splitlines():
        if not path.strip():
            continue
        try:
            with open(os.path.join(cwd, path), encoding="utf-8", errors="replace") as fh:
                body = fh.read().splitlines()
        except (OSError, UnicodeError):
            continue
        if body:
            hunks.append(Hunk(path=path, added=list(enumerate(body, start=1))))

    return hunks


def is_excluded(path: str, excludes: tuple[str, ...]) -> bool:
    probe = "/" + path
    return any(token in probe for token in excludes)


def comment_prefixes(path: str) -> tuple[str, ...]:
    _, ext = os.path.splitext(path)
    if ext in COMMENT_PREFIXES:
        return COMMENT_PREFIXES[ext]
    if os.path.basename(path) in SHELL_LIKE_NAMES:
        return ("#",)
    return ()


def is_comment(line: str, prefixes: tuple[str, ...]) -> bool:
    stripped = line.strip()
    if not stripped or not prefixes:
        return False
    if stripped.startswith("#!"):
        return False
    return stripped.startswith(prefixes)


def is_code(path: str) -> bool:
    _, ext = os.path.splitext(path)
    return ext in CODE_EXTENSIONS or os.path.basename(path) in SHELL_LIKE_NAMES


def is_shell_like(path: str) -> bool:
    _, ext = os.path.splitext(path)
    return ext in SHELL_LIKE or os.path.basename(path) in SHELL_LIKE_NAMES


def block_snippet(lines: list[str]) -> str:
    return "\n".join(line.strip() for line in lines)


def classify(path: str, block: list[str], follows: str, deletes_code: bool) -> tuple[str, str]:
    """Pick the most specific rule the comment breaks. The two syntax rules are
    decidable from the text alone, so they flag; anything left needs judgement."""
    head = block[0]

    if os.path.splitext(path)[1] in TS_EXTENSIONS:
        if head.startswith("/**"):
            if not DECLARATION_RE.match(follows):
                return "jsdoc-misuse", "flag"
        elif head.startswith("/*"):
            return "bare-block", "flag"

    if deletes_code:
        return "comment-on-deletion", "flag"
    return "comment-added", "judge"


def describes(path: str, cwd: str, after: int) -> str:
    """The first line of code the comment block sits above. A comment cannot be
    rated without the code it claims to explain."""
    try:
        with open(os.path.join(cwd, path), encoding="utf-8", errors="replace") as fh:
            body = fh.read().splitlines()
    except OSError:
        return ""

    prefixes = comment_prefixes(path)
    for line in body[after - 1 : after + 12]:
        stripped = line.strip()
        if stripped and not is_comment(line, prefixes):
            return stripped
    return ""


def group_comments(
    lines: list[tuple[int, str]], prefixes: tuple[str, ...]
) -> list[tuple[int, list[str]]]:
    """Contiguous comment lines are one comment, and are rated as one. Returns
    each block's starting line number with its stripped lines."""
    blocks: list[tuple[int, list[str]]] = []
    current: list[str] = []
    start = 0
    previous = -2

    for line_no, text in lines:
        if is_comment(text, prefixes):
            if line_no != previous + 1 or not current:
                current = []
                blocks.append((line_no, current))
                start = line_no
            current.append(text.strip())
            previous = line_no
        else:
            current = []
            previous = -2

    return [(start, block) for start, block in blocks if block]


def scan_comments(hunks: list[Hunk], excludes: tuple[str, ...], cwd: str) -> list[Finding]:
    findings: list[Finding] = []

    for hunk in hunks:
        if is_excluded(hunk.path, excludes):
            continue

        prefixes = comment_prefixes(hunk.path)
        deletes_code = any(
            line.strip() and not is_comment(line, prefixes) for line in hunk.removed
        )

        for start, block in group_comments(hunk.added, prefixes):
            follows = describes(hunk.path, cwd, start + len(block))
            kind, disposition = classify(hunk.path, block, follows, deletes_code)
            findings.append(
                Finding(
                    path=hunk.path,
                    line=start,
                    kind=kind,
                    disposition=disposition,
                    snippet=block_snippet(block),
                    context=[line.strip() for line in hunk.removed[:4]],
                    follows=follows,
                )
            )

    return findings


def scan_code(hunks: list[Hunk], excludes: tuple[str, ...]) -> list[Finding]:
    findings: list[Finding] = []

    for hunk in hunks:
        if is_excluded(hunk.path, excludes):
            continue
        if not is_code(hunk.path):
            continue

        prefixes = comment_prefixes(hunk.path)

        for line_no, text in hunk.added:
            if not text.strip() or is_comment(text, prefixes):
                continue

            if SENTINEL_RE.search(text):
                findings.append(
                    Finding(hunk.path, line_no, "sentinel", "judge", text.strip())
                )

            if NEGATED_STATE_RE.search(text):
                findings.append(
                    Finding(hunk.path, line_no, "negated-state", "flag", text.strip())
                )

            if is_shell_like(hunk.path) and SHELL_DEFAULT_RE.search(text):
                findings.append(
                    Finding(hunk.path, line_no, "shell-default", "judge", text.strip())
                )

    return findings


def scan_file_comments(paths: list[str], cwd: str) -> list[Finding]:
    """Every comment in a file, with no diff involved — for rating comments that
    are already committed."""
    findings: list[Finding] = []

    for path in paths:
        prefixes = comment_prefixes(path)
        if not prefixes:
            continue
        try:
            with open(os.path.join(cwd, path), encoding="utf-8", errors="replace") as fh:
                body = fh.read().splitlines()
        except OSError:
            sys.stderr.write(f"diff-check: cannot read {path}\n")
            continue

        numbered = list(enumerate(body, start=1))
        for start, block in group_comments(numbered, prefixes):
            follows = describes(path, cwd, start + len(block))
            kind, disposition = classify(path, block, follows, deletes_code=False)
            findings.append(
                Finding(
                    path=path,
                    line=start,
                    kind=kind,
                    disposition=disposition,
                    snippet=block_snippet(block),
                    follows=follows,
                )
            )

    return findings


OXLINT_CONFIG = {
    "plugins": [],
    "categories": {},
    "rules": {
        "no-magic-numbers": [
            "error",
            {
                "ignore": [0, 1, -1, 2, 3, 4, -2],
                "ignoreArrayIndexes": True,
                "ignoreDefaultValues": True,
                "detectObjects": False,
            },
        ]
    },
}


def lint_changed(
    hunks: list[Hunk], cwd: str, excludes: tuple[str, ...]
) -> list[Finding]:
    """Run oxlint's no-magic-numbers over changed files, then keep only the
    findings that land on a line this change added."""
    import shutil
    import tempfile

    if shutil.which("oxlint") is None:
        sys.stderr.write("diff-check: oxlint not on PATH, skipping --lint\n")
        return []

    changed: dict[str, set[int]] = {}
    for hunk in hunks:
        if is_excluded(hunk.path, excludes):
            continue
        if os.path.splitext(hunk.path)[1] not in (".ts", ".tsx", ".js", ".jsx", ".mjs"):
            continue
        changed.setdefault(hunk.path, set()).update(no for no, _ in hunk.added)

    if not changed:
        return []

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        json.dump(OXLINT_CONFIG, handle)
        config_path = handle.name

    try:
        proc = subprocess.run(
            ["oxlint", "-c", config_path, "--format", "json", *sorted(changed)],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        try:
            report = json.loads(proc.stdout or "{}")
        except json.JSONDecodeError:
            sys.stderr.write("diff-check: could not parse oxlint output\n")
            return []
    finally:
        os.unlink(config_path)

    findings: list[Finding] = []
    for diag in report.get("diagnostics", []):
        path = diag.get("filename", "")
        labels = diag.get("labels") or []
        line = (labels[0].get("span", {}) if labels else {}).get("line", 0)
        if line in changed.get(path, ()):
            findings.append(
                Finding(
                    path=path,
                    line=line,
                    kind="magic-number",
                    disposition="judge",
                    snippet=diag.get("message", "").strip(),
                )
            )
    return findings


def diff_args(args: argparse.Namespace) -> list[str]:
    base = ["diff", "-U0", "--no-color", "--no-ext-diff"]
    if args.range:
        return [*base, args.range]
    if args.staged:
        return [*base, "--cached"]
    return [*base, "HEAD"]


def render(findings: list[Finding]) -> str:
    if not findings:
        return "diff-check: no candidates on changed lines."

    order = {"flag": 0, "judge": 1}
    findings.sort(key=lambda f: (order[f.disposition], f.path, f.line))

    lines = []
    for finding in findings:
        marker = "FLAG " if finding.disposition == "flag" else "JUDGE"
        lines.append(f"{marker} {finding.path}:{finding.line}  [{finding.kind}]")
        for text in finding.snippet.splitlines():
            lines.append(f"      {text}")
        if finding.follows:
            lines.append(f"      describes: {finding.follows}")
        for removed in finding.context:
            lines.append(f"      removed:   {removed}")
        lines.append(f"      rule: {RULES[finding.kind]}")
        lines.append("")

    flags = sum(1 for f in findings if f.disposition == "flag")
    lines.append(f"{flags} to fix, {len(findings) - flags} to judge.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--staged", action="store_true", help="only staged changes")
    group.add_argument("--range", help="a git revision or range, e.g. HEAD~1 or main...")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--lint", action="store_true", help="also run oxlint")
    parser.add_argument(
        "--include-generated",
        action="store_true",
        help="do not skip generated, vendored and lockfile paths",
    )
    parser.add_argument("--repo", default=".", help="repository root (default: cwd)")
    parser.add_argument(
        "--comments", action="store_true", help="only comments, rated on their own"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="files to read comments from directly, ignoring the diff",
    )
    args = parser.parse_args()

    cwd = os.path.abspath(args.repo)
    excludes = () if args.include_generated else DEFAULT_EXCLUDES

    if args.paths:
        findings = scan_file_comments(args.paths, cwd)
    else:
        hunks = parse_diff(run_git(diff_args(args), cwd))
        if not args.range and not args.staged:
            hunks.extend(untracked_hunks(cwd))
        findings = scan_comments(hunks, excludes, cwd)
        if not args.comments:
            findings.extend(scan_code(hunks, excludes))
            if args.lint:
                findings.extend(lint_changed(hunks, cwd, excludes))

    if args.json:
        print(json.dumps([f.as_dict() for f in findings], indent=2))
    else:
        print(render(findings))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
