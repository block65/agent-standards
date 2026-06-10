#!/usr/bin/env python3
"""
moonrepo knowledge-base sync — fetch once, cache, update with one command.

Pulls a curated slice of the moonrepo/moon repo at a pinned git ref and builds a
local, versioned knowledge base the `moonrepo` skill reads from. Three tracks:

  1. SCHEMAS (lossless, deterministic — no LLM). The JSON Schemas under
     website/static/schemas/<v>/ are the ground truth for every config option.
     We cache the raw JSON *and* render each into a dense, flat field reference
     (path · type · default · required · description) so the agent can answer
     "what options exist and why" without burning tokens on 2000-line JSON.

  2. DOCS (raw + optional distilled). Curated .mdx from website/docs/{config,
     concepts,guides}. Cached raw for exact wording; optionally LLM-distilled
     into dense rules (--distill) for cheap reads, rust-book style.

  3. debug-task (vendored). The official moonrepo/moon skills/debug-task SKILL.md
     + references, pinned at the same ref. Lighter and more robust than a git
     submodule of the whole moon repo, same "track upstream" property.

Re-running is cheap: a manifest records each source blob's git SHA, so unchanged
files are skipped — we don't re-download the docs every time.

Usage:
  python sync.py                         # sync v2 (default) from master
  python sync.py --version v1            # also build the v1 (frozen) tree
  python sync.py --ref v2.3.1            # pin to a tag for reproducibility
  python sync.py --distill               # also LLM-distill prose (needs a CLI)
  python sync.py --force                 # ignore manifest, re-fetch everything

Distill providers (no API keys; uses a local CLI):
  claude-cli (default) · gemini-cli · copilot-cli
"""

import argparse
import json
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = "moonrepo/moon"
GITHUB_TREE = "https://api.github.com/repos/{repo}/git/trees/{ref}?recursive=1"
GITHUB_RAW = "https://raw.githubusercontent.com/{repo}/{ref}/{path}"

DEFAULT_CACHE = Path.home() / ".claude" / "skills" / "moonrepo" / "cache"

# The entire docs library is cached — every .mdx/.md under website/docs is gold
# for authoring, migration, plugins, and edge cases. Raw markdown is cheap to
# store; the generated docs/_index.md keeps it navigable.

DISTILL_PROMPT = """\
You are a senior moonrepo (moon) build engineer. Read this documentation page and \
extract ONLY actionable rules, config field names, exact syntax, and canonical \
patterns a developer needs to author or fix moon config (.moon/* and moon.yml). \
Strip narrative, history, and motivation. Preserve EVERY config field, option, \
target-scope symbol (^: ~: :), and CLI flag mentioned verbatim — do not paraphrase \
identifiers. Output a dense Markdown bullet list. If the page describes v1-vs-v2 \
differences, keep them as explicit old→new pairs. Be ruthlessly concise.\
"""

CLI_COMMANDS = {
    "claude-cli": ["claude", "-p", DISTILL_PROMPT],
    "gemini-cli": ["gemini", DISTILL_PROMPT],
    "copilot-cli": ["copilot", DISTILL_PROMPT],
}


# --------------------------------------------------------------------------- #
# HTTP / GitHub
# --------------------------------------------------------------------------- #
def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "moonrepo-skill-sync"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def list_repo_tree(ref: str) -> dict:
    """path -> blob sha for the whole repo at `ref` (one API call)."""
    data = json.loads(http_get(GITHUB_TREE.format(repo=REPO, ref=ref)).decode("utf-8"))
    if data.get("truncated"):
        print("  [warn] git tree response truncated; some files may be missed", file=sys.stderr)
    return {e["path"]: e["sha"] for e in data.get("tree", []) if e["type"] == "blob"}


def select_sources(tree: dict, version: str) -> dict:
    """Pick the repo paths we care about → logical destination kind."""
    picked = {}  # repo_path -> (kind, dest_rel)
    for path in tree:
        # Schemas for this version
        m = re.match(rf"^website/static/schemas/{version}/(.+\.json)$", path)
        if m:
            picked[path] = ("schema", m.group(1))
            continue
        # The whole docs library — every page, not a curated slice
        m = re.match(r"^website/docs/(.+\.mdx?)$", path)
        if m:
            picked[path] = ("doc", m.group(1))
            continue
        # Vendored official debug-task skill
        m = re.match(r"^skills/debug-task/(.+\.md)$", path)
        if m:
            picked[path] = ("debug", m.group(1))
            continue
    return picked


# --------------------------------------------------------------------------- #
# Deterministic JSON Schema -> dense field reference
# --------------------------------------------------------------------------- #
def _resolve_ref(ref: str, defs: dict):
    name = ref.split("/")[-1]
    return name, defs.get(name, {})


def _first_sentence(text: str, limit: int = 160) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return ""
    cut = text.split(". ")[0].rstrip(".")
    if len(cut) > limit:
        cut = cut[:limit].rstrip() + "…"
    return cut


def _type_label(node: dict, defs: dict, chain: tuple):
    """Return (label, children_node_or_None, is_map). children gets recursed."""
    if "$ref" in node:
        name, target = _resolve_ref(node["$ref"], defs)
        if name in chain:  # cycle guard
            return name, None, False
        return _type_label(target, defs, chain + (name,))

    if "const" in node:
        return f"'{node['const']}'", None, False

    if "enum" in node:
        vals = "|".join(str(v) for v in node["enum"])
        return f"enum({vals})", None, False

    for combiner in ("anyOf", "oneOf"):
        if combiner in node:
            variants = node[combiner]
            non_null = [v for v in variants if v.get("type") != "null"]
            nullable = len(non_null) != len(variants)
            if len(non_null) == 1:
                label, child, is_map = _type_label(non_null[0], defs, chain)
                return (label + "?" if nullable else label), child, is_map
            # Collapse a run of consts into one enum() and dedupe repeats
            consts = [v["const"] for v in non_null if "const" in v]
            others, seen = [], set()
            for v in non_null:
                if "const" in v:
                    continue
                lab = _type_label(v, defs, chain)[0]
                if lab not in seen:
                    seen.add(lab)
                    others.append(lab)
            parts = []
            if consts:
                parts.append("enum(" + "|".join(str(c) for c in consts) + ")")
            for lab in others:
                if lab not in (p for p in parts):
                    parts.append(lab)
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
        items = node.get("items", {})
        ilabel, ichild, _ = _type_label(items, defs, chain)
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


def _walk(node: dict, defs: dict, prefix: str, required: set, rows: list,
          chain: tuple, depth: int, is_map_key: bool = False):
    if depth > 7:
        return
    props = node.get("properties", {})
    req = set(node.get("required", []))
    for field, sub in sorted(props.items()):
        path = f"{prefix}{field}"
        label, child, is_map = _type_label(sub, defs, chain)
        desc = _first_sentence(sub.get("markdownDescription") or sub.get("description"))
        default = sub.get("default", sub.get("const"))
        rows.append({
            "path": path,
            "type": label,
            "required": field in req,
            "default": default,
            "desc": desc,
        })
        if child is not None and child is not sub or (child is sub and child.get("properties")):
            nxt = f"{path}.*." if is_map else f"{path}."
            _walk(child, defs, nxt, required, rows, chain, depth + 1)


def render_schema(raw: str, source_name: str) -> str:
    schema = json.loads(raw)
    defs = schema.get("$defs", schema.get("definitions", {}))
    title = schema.get("title", source_name)
    rows: list = []
    _walk(schema, defs, "", set(schema.get("required", [])), rows, (), 0)

    lines = [
        f"# Schema: {source_name}  ({title})",
        "",
        f"> Lossless field reference rendered from `{source_name}`. "
        f"Every field is listed; `?` = nullable, `*` = arbitrary map key.",
        "",
        "| Field | Type | Req | Default | Notes |",
        "|-------|------|-----|---------|-------|",
    ]
    for r in rows:
        dflt = "" if r["default"] is None else f"`{json.dumps(r['default'])}`"
        req = "✓" if r["required"] else ""
        note = r["desc"].replace("|", "\\|")
        lines.append(f"| `{r['path']}` | {r['type']} | {req} | {dflt} | {note} |")
    if not rows:
        lines.append("| _(no object properties — see raw schema)_ |  |  |  |  |")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# Optional LLM distillation of prose docs
# --------------------------------------------------------------------------- #
def build_docs_index(cache: Path) -> int:
    """Scan cached docs and write docs/_index.md (path -> title) for navigation."""
    docs_dir = cache / "docs"
    if not docs_dir.exists():
        return 0
    rows = []
    for f in sorted(docs_dir.rglob("*")):
        if f.suffix not in (".md", ".mdx") or f.name == "_index.md":
            continue
        rel = f.relative_to(docs_dir).as_posix()
        if rel.startswith("__partials__/"):
            continue  # MDX include fragments — cached, but noise in the index
        title = ""
        try:
            text = f.read_text(encoding="utf-8")
            fm = re.search(r"^---\n(.*?)\n---", text, re.DOTALL)
            if fm:
                t = re.search(r"^title:\s*['\"]?(.+?)['\"]?\s*$", fm.group(1), re.MULTILINE)
                if t:
                    title = t.group(1)
            if not title:
                h = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
                title = h.group(1) if h else ""
        except Exception:
            pass
        rows.append((rel, title))
    lines = [
        "# moon docs — cached library index",
        "",
        f"> {len(rows)} pages cached locally. Read a page by its path under `docs/`.",
        "> Live URL = `https://moonrepo.dev/docs/<path without .mdx>`.",
        "",
        "| Page | Title |",
        "|------|-------|",
    ]
    for rel, title in rows:
        lines.append(f"| `{rel}` | {title.replace('|', '\\|')} |")
    (docs_dir / "_index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(rows)


def distill(provider: str, model, text: str) -> str:
    cmd = list(CLI_COMMANDS[provider])
    if model and provider != "copilot-cli":
        cmd = cmd[:-1] + ["--model", model] + [cmd[-1]]
    res = subprocess.run(cmd, input=text, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"{provider} exited {res.returncode}: {res.stderr.strip() or '(no stderr)'}")
    out = res.stdout.strip()
    if not out:
        raise RuntimeError(f"{provider} returned empty output")
    return out


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    p = argparse.ArgumentParser(description="Sync the moonrepo knowledge-base cache.")
    p.add_argument("--version", default="v2", choices=["v1", "v2"],
                   help="Schema/doc version tree to build (default: v2)")
    p.add_argument("--ref", default="master", help="Git ref of moonrepo/moon to pull (default: master)")
    p.add_argument("--cache-dir", default=str(DEFAULT_CACHE), help=f"Cache root (default: {DEFAULT_CACHE})")
    p.add_argument("--distill", action="store_true", help="Also LLM-distill prose docs into dense rules")
    p.add_argument("--provider", default="claude-cli", choices=list(CLI_COMMANDS))
    p.add_argument("--model", default=None)
    p.add_argument("--force", action="store_true", help="Ignore manifest; re-fetch everything")
    args = p.parse_args()

    cache = Path(args.cache_dir).expanduser().resolve() / args.version
    cache.mkdir(parents=True, exist_ok=True)
    manifest_path = cache / "manifest.json"
    old = {}
    if manifest_path.exists() and not args.force:
        try:
            old = json.loads(manifest_path.read_text()).get("files", {})
        except Exception:
            old = {}

    print(f"moonrepo sync — version={args.version} ref={args.ref}")
    print(f"  cache: {cache}")
    print("  listing repo tree…")
    try:
        tree = list_repo_tree(args.ref)
    except Exception as e:
        print(f"Error: could not list repo tree at {args.ref}: {e}", file=sys.stderr)
        sys.exit(1)

    sources = select_sources(tree, args.version)
    if not sources:
        print(f"Error: no sources matched for version {args.version} at ref {args.ref}.", file=sys.stderr)
        print("       (v1 schemas live under website/static/schemas/v1; check the ref.)", file=sys.stderr)
        sys.exit(1)

    new_manifest = {}
    fetched = skipped = 0
    schema_files, doc_files = [], []

    for repo_path, (kind, dest_rel) in sorted(sources.items()):
        sha = tree[repo_path]
        new_manifest[repo_path] = sha

        if kind == "schema":
            schema_files.append(dest_rel)
        elif kind == "doc":
            doc_files.append(dest_rel)

        if old.get(repo_path) == sha and not args.force:
            skipped += 1
            continue

        try:
            raw = http_get(GITHUB_RAW.format(repo=REPO, ref=args.ref, path=repo_path)).decode("utf-8")
        except Exception as e:
            print(f"  [error] {repo_path}: {e}", file=sys.stderr)
            new_manifest.pop(repo_path, None)
            continue

        if kind == "schema":
            (cache / "schemas" / "raw").mkdir(parents=True, exist_ok=True)
            (cache / "schemas" / "raw" / dest_rel).write_text(raw, encoding="utf-8")
            md_name = Path(dest_rel).stem + ".md"
            try:
                (cache / "schemas" / md_name).write_text(render_schema(raw, dest_rel), encoding="utf-8")
            except Exception as e:
                print(f"  [warn] schema render failed for {dest_rel}: {e}", file=sys.stderr)
            print(f"  [schema] {dest_rel} → schemas/{md_name}")

        elif kind == "doc":
            out = cache / "docs" / dest_rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(raw, encoding="utf-8")
            print(f"  [doc]    {dest_rel}")
            if args.distill:
                try:
                    digest = distill(args.provider, args.model, raw)
                    dpath = cache / "digests" / (dest_rel.replace("/", "__").replace(".mdx", ".md"))
                    dpath.parent.mkdir(parents=True, exist_ok=True)
                    dpath.write_text(f"# Distilled: {dest_rel}\n\n{digest}\n", encoding="utf-8")
                    print(f"  [digest] {dpath.name}")
                except Exception as e:
                    print(f"  [warn] distill failed for {dest_rel}: {e}", file=sys.stderr)

        elif kind == "debug":
            out = cache / "debug-task" / dest_rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(raw, encoding="utf-8")
            print(f"  [debug]  {dest_rel}")

        fetched += 1

    n_indexed = build_docs_index(cache)

    manifest_path.write_text(json.dumps({
        "version": args.version,
        "ref": args.ref,
        "repo": REPO,
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "distilled": args.distill,
        "files": new_manifest,
    }, indent=2), encoding="utf-8")

    print()
    print(f"Done. fetched={fetched} skipped={skipped} (unchanged)  schemas={len(schema_files)} docs={n_indexed}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
