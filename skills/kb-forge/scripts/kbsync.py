#!/usr/bin/env python3
"""
kbsync — declarative, versioned, SWR-style knowledge-base sync for skills.

ONE engine behind every "docs expert" skill. You declare a documentation source
in a `kb.toml`; this script fetches the declared slice at a pinned version,
records each item's content hash (the revalidation key / ETag), renders it per
the declared track, and writes a local cache the skill reads from. Re-running is
cheap: unchanged items are skipped via the manifest — stale-while-revalidate
without a server.

Why it exists: a model's training is stale and lossy. A skill that answers from
a locally cached, tightly pinned copy of the *real* docs is neither. Bump the
source `ref`/version to track a fast-moving upstream on YOUR schedule.

  kb.toml shape
  -------------
    name    = "cloudflare-workflows"
    version = "v1"                  # cache subdir (default: "current")

    [source]                        # ONE of: github | git | web | local | cli
    kind = "github"
    repo = "cloudflare/cloudflare-docs"
    ref  = "production"
    root = "src/content/docs/workflows"   # specialise a slice (str or list)

    [[track]]                       # one or more render tracks
    kind   = "distill"              # schema | distill | raw | vendor
    select = "**/*.mdx"             # glob(s) over item paths (str or list)

  Source kinds (everything, not just GitHub)
  ------------------------------------------
    github  owner/repo via the tree+raw API. Fast: blob SHA known without fetch.
    git     ANY git host (gitlab/bitbucket/PRIVATE) — shallow clone at `ref`,
            uses your system git credentials. Pins to the resolved commit.
    web     a docs WEBSITE with no repo. `urls = [...]`; HTML stripped to text.
    local   a local dir (/usr/share/doc/foo, a vendored tree). `path = "..."`.
    cli     an obscure CLI whose only docs are `--help`. Captures command output;
            pins to the tool's `--version`.

  Tracks (how each item is rendered)
  ----------------------------------
    schema  JSON-Schema -> dense flat field table (lossless, deterministic).
    distill LLM-compress prose into dense rules via a LOCAL CLI (no API keys).
    raw     cache verbatim (exact wording / real source files).
    vendor  cache verbatim under vendor/ (an upstream skill, example tree, ...).

Usage:
  python kbsync.py --kb path/to/kb.toml                 # sync per the declaration
  python kbsync.py --kb path/to/kb.toml --force         # ignore manifest, refetch all
  python kbsync.py --kb path/to/kb.toml --ref v2.3.1    # override the pinned ref (git/github)
  python kbsync.py --kb path/to/kb.toml --limit 10      # cap distill calls (warm incrementally)
  python kbsync.py --kb path/to/kb.toml --provider gemini-cli

Distill providers (no API keys; shells to a local CLI):
  claude-cli (default) · gemini-cli · copilot-cli
"""

import argparse
import hashlib
import io
import json
import re
import shlex
import subprocess
import sys
import tarfile
import time
import tomllib
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_CACHE_ROOT = Path.home() / ".claude" / "skills"

DEFAULT_DISTILL_PROMPT = """\
You are a senior engineer writing a dense reference for another engineer. Read this \
documentation and extract ONLY the actionable 'what' and 'how': API names, \
function/CLI signatures, config field names and types, exact syntax, required vs \
optional, defaults, and canonical copy-pasteable patterns. Preserve every identifier \
verbatim — do NOT paraphrase names, flags, or symbols. Strip narrative, history, \
motivation, and marketing. If it documents version differences or deprecations, keep \
them as explicit old->new pairs. Output a dense Markdown bullet list. Be ruthlessly \
concise — every line must be directly useful when writing or fixing code.\
"""

CLI_COMMANDS = {"claude-cli": ["claude", "-p"], "gemini-cli": ["gemini"], "copilot-cli": ["copilot"]}
CLI_SUPPORTS_MODEL = {"claude-cli", "gemini-cli"}
DEST_DEFAULTS = {"schema": "schemas", "distill": "distilled", "raw": "docs", "vendor": "vendor"}


def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "kbsync"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run(cmd: list, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


# ===========================================================================
# Sources — each yields Items and knows how to fetch one. An Item carries a
# logical `path` (what selectors match) and, when cheaply knowable WITHOUT
# fetching (git blob SHA), an `ident` so we can skip the fetch entirely.
# ===========================================================================
class Item:
    __slots__ = ("path", "ident", "_ref")

    def __init__(self, path, ident=None, ref=None):
        self.path = path        # logical relative path; selectors match this
        self.ident = ident      # content identity known pre-fetch, else None
        self._ref = ref         # source-private handle used by fetch()


class Source:
    tier = "primary"   # primary | secondary | tertiary — confidence label for the cache

    def resolved_version(self) -> dict:
        """Tight version info recorded in the manifest header (what we're pinned to)."""
        return {}

    def latest_version(self):
        """Best-effort: the newest version available upstream, or None if undiscoverable.

        Lets a skill compare what it's pinned to against what's current and offer
        to bump. Discovery is per-source: a release tag, a crates.io version, a
        CLI's --version. None means 'can't tell' (e.g. a frozen local dir)."""
        return None

    def enumerate(self) -> list:
        raise NotImplementedError

    def fetch(self, item: Item) -> str:
        raise NotImplementedError


class GithubSource(Source):
    TREE = "https://api.github.com/repos/{repo}/git/trees/{sha}?recursive=1"
    SHALLOW = "https://api.github.com/repos/{repo}/git/trees/{sha}"
    RAW = "https://raw.githubusercontent.com/{repo}/{ref}/{path}"

    def __init__(self, cfg, ref_override=None):
        self.repo = cfg["repo"]
        self.ref = ref_override or cfg.get("ref", "main")
        roots = cfg.get("root", "")
        self.roots = ([roots] if isinstance(roots, str) else list(roots)) or [""]
        self._commit = None

    def _subtree_sha(self, path):
        sha = self.ref
        for seg in [s for s in path.strip("/").split("/") if s]:
            data = json.loads(http_get(self.SHALLOW.format(repo=self.repo, sha=sha)).decode())
            m = next((e for e in data.get("tree", []) if e["path"] == seg and e["type"] == "tree"), None)
            if m is None:
                raise FileNotFoundError(f"'{seg}' not found under root '{path}' at {self.ref}")
            sha = m["sha"]
        return sha

    def resolved_version(self):
        try:
            ref_data = json.loads(http_get(
                f"https://api.github.com/repos/{self.repo}/commits/{self.ref}").decode())
            self._commit = ref_data.get("sha")
        except Exception:
            pass
        return {"repo": self.repo, "ref": self.ref, "commit": self._commit, "roots": self.roots}

    def enumerate(self):
        items = {}
        for root in self.roots:
            data = json.loads(http_get(self.TREE.format(repo=self.repo, sha=self._subtree_sha(root))).decode())
            if data.get("truncated"):
                print(f"  [warn] tree under '{root or '<root>'}' truncated; narrow `root`", file=sys.stderr)
            prefix = (root.strip("/") + "/") if root else ""
            for e in data.get("tree", []):
                if e["type"] == "blob":
                    items[prefix + e["path"]] = Item(prefix + e["path"], ident=e["sha"], ref=prefix + e["path"])
        return list(items.values())

    def fetch(self, item):
        return http_get(self.RAW.format(repo=self.repo, ref=self.ref, path=item._ref)).decode("utf-8")


class GitSource(Source):
    """Any git host incl. private — shallow clone, ls-tree for blob SHAs."""

    def __init__(self, cfg, cache_dir, ref_override=None):
        self.url = cfg["url"]
        self.ref = ref_override or cfg.get("ref", "HEAD")
        roots = cfg.get("root", "")
        self.roots = ([roots] if isinstance(roots, str) else list(roots)) or [""]
        self.work = cache_dir / ".gitsrc"
        self._commit = None

    def _ensure_clone(self):
        if (self.work / ".git").exists():
            run(["git", "-C", str(self.work), "fetch", "--depth", "1", "origin", self.ref])
            run(["git", "-C", str(self.work), "checkout", "-q", "FETCH_HEAD"])
        else:
            self.work.parent.mkdir(parents=True, exist_ok=True)
            r = run(["git", "clone", "--depth", "1", "--branch", self.ref, self.url, str(self.work)])
            if r.returncode != 0:  # ref may be a bare sha — fall back to a full clone + checkout
                run(["git", "clone", self.url, str(self.work)])
                run(["git", "-C", str(self.work), "checkout", "-q", self.ref])
        c = run(["git", "-C", str(self.work), "rev-parse", "HEAD"])
        self._commit = c.stdout.strip() or None

    def resolved_version(self):
        return {"url": self.url, "ref": self.ref, "commit": self._commit, "roots": self.roots}

    def enumerate(self):
        self._ensure_clone()
        items = {}
        for root in self.roots:
            r = run(["git", "-C", str(self.work), "ls-tree", "-r", "HEAD",
                     "--format=%(objectname) %(path)", root or "."])
            for line in r.stdout.splitlines():
                sha, _, path = line.partition(" ")
                if path:
                    items[path] = Item(path, ident=sha, ref=path)
        return list(items.values())

    def fetch(self, item):
        return (self.work / item._ref).read_text(encoding="utf-8", errors="replace")


class LocalSource(Source):
    """A local directory: /usr/share/doc/foo, a vendored tree, etc."""

    def __init__(self, cfg):
        self.base = Path(cfg["path"]).expanduser().resolve()
        roots = cfg.get("root", "")
        self.roots = ([roots] if isinstance(roots, str) else list(roots)) or [""]

    def resolved_version(self):
        return {"path": str(self.base), "snapshot_at": _now()}

    def enumerate(self):
        if not self.base.exists():
            raise FileNotFoundError(f"local source path does not exist: {self.base}")
        items = {}
        for root in self.roots:
            start = (self.base / root) if root else self.base
            for f in sorted(start.rglob("*")):
                if f.is_file():
                    rel = f.relative_to(self.base).as_posix()
                    items[rel] = Item(rel, ident=None, ref=str(f))
        return list(items.values())

    def fetch(self, item):
        return Path(item._ref).read_text(encoding="utf-8", errors="replace")


class WebSource(Source):
    """A docs website with no repo. Explicit URL list; HTML stripped to text."""

    def __init__(self, cfg):
        urls = cfg.get("urls") or ([cfg["url"]] if cfg.get("url") else [])
        if not urls:
            raise ValueError("web source needs `urls = [...]` (or a single `url`)")
        self.urls = list(urls)

    def resolved_version(self):
        return {"urls": self.urls, "snapshot_at": _now()}

    @staticmethod
    def _slug(url):
        s = re.sub(r"^https?://", "", url)
        s = re.sub(r"[?#].*$", "", s)
        s = re.sub(r"[^A-Za-z0-9._/-]", "_", s).strip("/")
        return (s or "index") + ".md"

    def enumerate(self):
        return [Item(self._slug(u), ident=None, ref=u) for u in self.urls]

    def fetch(self, item):
        html = http_get(item._ref).decode("utf-8", errors="replace")
        return html_to_text(html)


class CliSource(Source):
    """An obscure CLI whose only docs are --help. Captures command output."""

    def __init__(self, cfg):
        self.version_cmd = cfg.get("version_cmd")
        self.commands = cfg.get("command") or []
        if not self.commands:
            raise ValueError("cli source needs at least one [[source.command]] with `run`")
        self._version = None

    def resolved_version(self):
        if self.version_cmd and self._version is None:
            r = run(shlex.split(self.version_cmd))
            self._version = (r.stdout or r.stderr).strip()
        return {"version_cmd": self.version_cmd, "version": self._version, "captured_at": _now()}

    def enumerate(self):
        out = []
        for c in self.commands:
            name = c.get("name") or re.sub(r"[^A-Za-z0-9]+", "_", c["run"]).strip("_")
            out.append(Item(f"{name}.txt", ident=None, ref=c["run"]))
        return out

    def fetch(self, item):
        r = run(shlex.split(item._ref))
        body = r.stdout if r.stdout.strip() else r.stderr  # many CLIs print --help to stderr
        if not body.strip():
            raise RuntimeError(f"command produced no output: {item._ref}")
        return f"$ {item._ref}\n\n{body}"


def _now():
    return datetime.now(timezone.utc).isoformat()


def html_to_text(html: str) -> str:
    """Crude but dependency-free HTML -> text: keep readable prose for distillation."""
    html = re.sub(r"(?is)<(script|style|nav|footer|header)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?is)<!--.*?-->", " ", html)
    html = re.sub(r"(?i)<(/p|/div|/li|/h[1-6]|br|/tr)\s*/?>", "\n", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    text = (text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
                .replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " "))
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


def make_source(kb: dict, cache_dir: Path, ref_override):
    src = kb.get("source")
    if not src or not src.get("kind"):
        raise ValueError("kb.toml needs a [source] table with a `kind`")
    kind = src["kind"]
    if kind == "github":
        return GithubSource(src, ref_override)
    if kind == "git":
        return GitSource(src, cache_dir, ref_override)
    if kind == "local":
        return LocalSource(src)
    if kind == "web":
        return WebSource(src)
    if kind == "cli":
        return CliSource(src)
    raise ValueError(f"unknown source.kind: {kind!r} (want github|git|web|local|cli)")


# ===========================================================================
# Selection
# ===========================================================================
def glob_to_regex(glob: str) -> re.Pattern:
    i, n, out = 0, len(glob), []
    while i < n:
        c = glob[i]
        if c == "*":
            if i + 1 < n and glob[i + 1] == "*":
                j = i + 2
                if j < n and glob[j] == "/":
                    out.append("(?:.*/)?")
                    i = j + 1
                    continue
                out.append(".*")
                i += 2
                continue
            out.append("[^/]*")
            i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def compile_selectors(select):
    pats = [select] if isinstance(select, str) else list(select)
    return [glob_to_regex(p) for p in pats]


# ===========================================================================
# Render tracks (source-agnostic)
# ===========================================================================
def _resolve_ref(ref, defs):
    name = ref.split("/")[-1]
    return name, defs.get(name, {})


def _first_sentence(text, limit=160):
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return ""
    cut = text.split(". ")[0].rstrip(".")
    return cut[:limit].rstrip() + "…" if len(cut) > limit else cut


def _type_label(node, defs, chain):
    if "$ref" in node:
        name, target = _resolve_ref(node["$ref"], defs)
        if name in chain:
            return name, None, False
        return _type_label(target, defs, chain + (name,))
    if "const" in node:
        return f"'{node['const']}'", None, False
    if "enum" in node:
        return f"enum({'|'.join(str(v) for v in node['enum'])})", None, False
    for combiner in ("anyOf", "oneOf"):
        if combiner in node:
            non_null = [v for v in node[combiner] if v.get("type") != "null"]
            nullable = len(non_null) != len(node[combiner])
            if len(non_null) == 1:
                label, child, is_map = _type_label(non_null[0], defs, chain)
                return (label + "?" if nullable else label), child, is_map
            consts = [v["const"] for v in non_null if "const" in v]
            others, seen = [], set()
            for v in non_null:
                if "const" in v:
                    continue
                lab = _type_label(v, defs, chain)[0]
                if lab not in seen:
                    seen.add(lab)
                    others.append(lab)
            parts = (["enum(" + "|".join(str(c) for c in consts) + ")"] if consts else []) + others
            lab = parts[0] if len(parts) == 1 else "union(" + " | ".join(parts) + ")"
            return (lab + "?" if nullable else lab), None, False
    if "allOf" in node:
        for v in node["allOf"]:
            if "$ref" in v or "properties" in v:
                return _type_label(v, defs, chain)
    t = node.get("type")
    if isinstance(t, list):
        t = "|".join(x for x in t if x != "null")
    if t == "array":
        ilabel, ichild, _ = _type_label(node.get("items", {}), defs, chain)
        return f"array<{ilabel}>", ichild, False
    if t == "object" or "properties" in node or "additionalProperties" in node:
        if node.get("properties"):
            return "object", node, False
        ap = node.get("additionalProperties")
        if isinstance(ap, dict):
            vlabel, vchild, _ = _type_label(ap, defs, chain)
            return f"map<{vlabel}>", vchild, True
        return "object", None, False
    return t or "any", None, False


def _walk(node, defs, prefix, rows, chain, depth):
    if depth > 7:
        return
    req = set(node.get("required", []))
    for field, sub in sorted(node.get("properties", {}).items()):
        path = f"{prefix}{field}"
        label, child, is_map = _type_label(sub, defs, chain)
        rows.append({"path": path, "type": label, "required": field in req,
                     "default": sub.get("default", sub.get("const")),
                     "desc": _first_sentence(sub.get("markdownDescription") or sub.get("description"))})
        if child is not None and (child is not sub or child.get("properties")):
            _walk(child, defs, f"{path}.*." if is_map else f"{path}.", rows, chain, depth + 1)


def render_schema(raw, source_name):
    schema = json.loads(raw)
    defs = schema.get("$defs", schema.get("definitions", {}))
    rows = []
    _walk(schema, defs, "", rows, (), 0)
    lines = [f"# Schema: {source_name}  ({schema.get('title', source_name)})", "",
             f"> Lossless field reference from `{source_name}`. `?` = nullable, `*` = map key.", "",
             "| Field | Type | Req | Default | Notes |", "|-------|------|-----|---------|-------|"]
    for r in rows:
        dflt = "" if r["default"] is None else f"`{json.dumps(r['default'])}`"
        lines.append(f"| `{r['path']}` | {r['type']} | {'✓' if r['required'] else ''} | {dflt} | {r['desc'].replace('|', chr(92) + '|')} |")
    if not rows:
        lines.append("| _(no object properties — see raw schema)_ |  |  |  |  |")
    return "\n".join(lines) + "\n"


def distill(provider, model, prompt, text):
    cmd = list(CLI_COMMANDS[provider])
    if model and provider in CLI_SUPPORTS_MODEL:
        cmd += ["--model", model]
    cmd.append(prompt)
    res = subprocess.run(cmd, input=text, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"{provider} exited {res.returncode}: {res.stderr.strip() or '(no stderr)'}")
    if not res.stdout.strip():
        raise RuntimeError(f"{provider} returned empty output")
    return res.stdout.strip()


def build_index(cache, subdir, header):
    docs_dir = cache / subdir
    if not docs_dir.exists():
        return 0
    rows = []
    for f in sorted(docs_dir.rglob("*")):
        if f.is_dir() or f.name == "_index.md":
            continue
        rel = f.relative_to(docs_dir).as_posix()
        title = ""
        try:
            text = f.read_text(encoding="utf-8")
            fm = re.search(r"^---\n(.*?)\n---", text, re.DOTALL)
            if fm and (t := re.search(r"^title:\s*['\"]?(.+?)['\"]?\s*$", fm.group(1), re.MULTILINE)):
                title = t.group(1)
            if not title and (h := re.search(r"^#\s+(.+)$", text, re.MULTILINE)):
                title = h.group(1)
        except Exception:
            pass
        rows.append((rel, title))
    lines = [f"# {subdir} — cached index ({header})", "",
             f"> {len(rows)} files cached locally. Read one by its path under `{subdir}/`.", "",
             "| File | Title |", "|------|-------|"]
    for rel, title in rows:
        lines.append(f"| `{rel}` | {title.replace('|', chr(92) + '|')} |")
    (docs_dir / "_index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(rows)


# ===========================================================================
# Declaration
# ===========================================================================
def load_kb(path):
    kb = tomllib.loads(path.read_text(encoding="utf-8"))
    if not kb.get("name"):
        raise ValueError("kb.toml missing required field: name")
    kb.setdefault("version", "current")
    if not kb.get("track"):
        raise ValueError("kb.toml declares no [[track]] entries")
    for t in kb["track"]:
        if t.get("kind") not in DEST_DEFAULTS:
            raise ValueError(f"track has invalid kind: {t.get('kind')!r} (want {list(DEST_DEFAULTS)})")
        if not t.get("select"):
            raise ValueError(f"{t['kind']} track missing `select`")
        t.setdefault("dest", DEST_DEFAULTS[t["kind"]])
        t["_patterns"] = compile_selectors(t["select"])
    return kb


# ===========================================================================
# Main
# ===========================================================================
def main():
    p = argparse.ArgumentParser(description="Sync a declarative knowledge-base cache from a kb.toml.")
    p.add_argument("--kb", required=True)
    p.add_argument("--ref", default=None, help="Override the pinned ref (github/git sources)")
    p.add_argument("--cache-root", default=str(DEFAULT_CACHE_ROOT))
    p.add_argument("--provider", default="claude-cli", choices=list(CLI_COMMANDS))
    p.add_argument("--model", default=None)
    p.add_argument("--limit", type=int, default=0, help="Max distill calls this run (0 = no cap)")
    p.add_argument("--delay", type=float, default=1.0)
    p.add_argument("--force", action="store_true")
    args = p.parse_args()

    kb_path = Path(args.kb).expanduser().resolve()
    if not kb_path.exists():
        sys.exit(f"Error: kb.toml not found: {kb_path}")
    try:
        kb = load_kb(kb_path)
    except Exception as e:
        sys.exit(f"Error: invalid kb.toml: {e}")

    cache = Path(args.cache_root).expanduser().resolve() / kb["name"] / "cache" / kb["version"]
    cache.mkdir(parents=True, exist_ok=True)
    manifest_path = cache / "manifest.json"
    old = {}
    if manifest_path.exists() and not args.force:
        try:
            old = json.loads(manifest_path.read_text()).get("files", {})
        except Exception:
            old = {}

    try:
        source = make_source(kb, cache, args.ref)
    except Exception as e:
        sys.exit(f"Error: {e}")

    print(f"kbsync — {kb['name']}  [{kb['source']['kind']}]")
    print(f"  cache: {cache}")
    try:
        version_meta = source.resolved_version()
        items = source.enumerate()
    except Exception as e:
        sys.exit(f"Error: could not read source: {e}")
    if not items:
        sys.exit("Error: source produced no items (check root/select/path).")
    print(f"  source pinned: {json.dumps(version_meta)}")
    print(f"  items discovered: {len(items)}")

    # Assign each item to the FIRST track whose selectors match.
    work = []
    for it in items:
        for track in kb["track"]:
            if any(pat.match(it.path) for pat in track["_patterns"]):
                work.append((it, track))
                break

    new_manifest = {}
    fetched = skipped = distills = 0
    index_dirs = set()

    for it, track in work:
        kind, dest = track["kind"], track["dest"]
        if kind in ("raw", "distill"):
            index_dirs.add(dest)

        # SWR skip #1: identity known without fetching (git blob SHA).
        if it.ident is not None and old.get(it.path) == it.ident and not args.force:
            new_manifest[it.path] = it.ident
            skipped += 1
            continue

        try:
            content = source.fetch(it)
        except Exception as e:
            print(f"  [error] {it.path}: {e}", file=sys.stderr)
            continue

        cur = it.ident or sha256(content)
        # SWR skip #2: content hash unchanged (web/local/cli — fetched but no re-render).
        if old.get(it.path) == cur and not args.force:
            new_manifest[it.path] = cur
            skipped += 1
            continue

        if kind == "schema":
            (cache / dest / "raw").mkdir(parents=True, exist_ok=True)
            (cache / dest / "raw" / Path(it.path).name).write_text(content, encoding="utf-8")
            md = Path(it.path).stem + ".md"
            try:
                (cache / dest / md).write_text(render_schema(content, it.path), encoding="utf-8")
                print(f"  [schema] {it.path} → {dest}/{md}")
            except Exception as e:
                print(f"  [warn] schema render failed for {it.path}: {e}", file=sys.stderr)

        elif kind in ("raw", "vendor"):
            out = cache / dest / it.path
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(content, encoding="utf-8")
            print(f"  [{kind}] {dest}/{it.path}")

        elif kind == "distill":
            if args.limit and distills >= args.limit:
                continue  # not recorded → a later run retries it
            prompt = track.get("prompt") or kb.get("distill_prompt") or DEFAULT_DISTILL_PROMPT
            try:
                digest = distill(args.provider, args.model, prompt, content)
            except Exception as e:
                print(f"  [warn] distill failed for {it.path}: {e}", file=sys.stderr)
                continue
            out = cache / dest / (re.sub(r"\.(mdx?|adoc|rst|txt|html?)$", "", it.path) + ".md")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(f"# Distilled: {it.path}\n\n---\n\n{digest}\n", encoding="utf-8")
            print(f"  [distill] {it.path} → {dest}/{out.name} ({len(digest):,} chars)")
            distills += 1
            if args.delay > 0:
                time.sleep(args.delay)

        new_manifest[it.path] = cur
        fetched += 1

    header = f"{kb['name']} @ {version_meta.get('commit') or version_meta.get('version') or version_meta.get('snapshot_at') or kb['version']}"
    for d in sorted(index_dirs):
        build_index(cache, d, header)

    manifest_path.write_text(json.dumps({
        "name": kb["name"], "version": kb["version"], "source_kind": kb["source"]["kind"],
        "pinned": version_meta, "synced_at": _now(), "files": new_manifest,
    }, indent=2), encoding="utf-8")

    capped = f"  [distill cap {args.limit} hit — re-run to continue]" if (args.limit and distills >= args.limit) else ""
    print(f"\nDone. fetched={fetched} skipped={skipped} (unchanged) distilled={distills}{capped}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
