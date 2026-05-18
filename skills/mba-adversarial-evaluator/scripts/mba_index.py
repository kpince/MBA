from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any


WIKI_LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)
TAG_RE = re.compile(r"(^|\s)#([A-Za-z0-9_/-]+)")


def build_index(vault: str | Path) -> dict[str, Any]:
    """Build a lightweight metadata/link index for a markdown vault."""
    root = Path(vault).expanduser().resolve()
    nodes: dict[str, dict[str, Any]] = {}
    raw_links: dict[str, list[str]] = {}

    for file_path in sorted(root.rglob("*.md")):
        rel = file_path.relative_to(root).as_posix()
        text = file_path.read_text(encoding="utf-8", errors="replace")
        frontmatter = parse_frontmatter(text)
        stat = file_path.stat()
        node = {
            "path": rel,
            "title": file_path.stem,
            "folder": "" if file_path.parent == root else file_path.parent.relative_to(root).as_posix(),
            "aliases": string_list(frontmatter.get("aliases", frontmatter.get("alias"))),
            "tags": unique(string_list(frontmatter.get("tags")) + inline_tags(text)),
            "frontmatter": frontmatter,
            "headings": headings(text),
            "links": [],
            "mtime": int(stat.st_mtime * 1000),
        }
        nodes[rel] = node
        raw_links[rel] = wiki_links(text)

    title_to_path = {node["title"].lower(): path for path, node in nodes.items()}
    forward: dict[str, list[str]] = {}
    for source, links in raw_links.items():
        resolved = [resolve_link(link, nodes, title_to_path) for link in links]
        forward[source] = unique([link for link in resolved if link])
        nodes[source]["links"] = forward[source]

    backlinks: dict[str, list[str]] = {path: [] for path in nodes}
    for source, links in forward.items():
        for target in links:
            backlinks.setdefault(target, []).append(source)

    return {
        "vault": str(root),
        "nodes": nodes,
        "forward": forward,
        "backlinks": backlinks,
    }


def parse_frontmatter(text: str) -> dict[str, Any]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    data: dict[str, Any] = {}
    for line in text[4:end].splitlines():
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not match:
            continue
        key, raw = match.group(1), match.group(2).strip()
        if raw.startswith("[") and raw.endswith("]"):
            values = [item.strip().strip("\"'") for item in raw[1:-1].split(",") if item.strip()]
            data[key] = values
        else:
            data[key] = raw.strip("\"'")
    return data


def string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [clean_tag(str(item)) for item in value if clean_tag(str(item))]
    return [clean_tag(item) for item in re.split(r"[,\s]+", str(value)) if clean_tag(item)]


def inline_tags(text: str) -> list[str]:
    return unique(clean_tag(match.group(2)) for match in TAG_RE.finditer(text))


def headings(text: str) -> list[str]:
    return [match.group(1).strip() for match in HEADING_RE.finditer(text)]


def wiki_links(text: str) -> list[str]:
    return [match.group(1).strip() for match in WIKI_LINK_RE.finditer(text)]


def resolve_link(link: str, nodes: dict[str, dict[str, Any]], title_to_path: dict[str, str]) -> str | None:
    normalized = link if link.endswith(".md") else f"{link}.md"
    normalized = normalized.replace(os.sep, "/")
    if normalized in nodes:
        return normalized
    return title_to_path.get(link.removesuffix(".md").lower())


def clean_tag(value: str) -> str:
    return value.strip().removeprefix("#")


def unique(values: Any) -> list[Any]:
    seen = set()
    out = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def choose_seed(index: dict[str, Any], seed: str | None = None) -> str:
    nodes = index["nodes"]
    if seed:
        if seed in nodes:
            return seed
        with_suffix = seed if seed.endswith(".md") else f"{seed}.md"
        if with_suffix in nodes:
            return with_suffix
        lowered = seed.removesuffix(".md").lower()
        for path, node in nodes.items():
            if node["title"].lower() == lowered or path.lower() == lowered:
                return path
        raise ValueError(f"Seed not found in vault index: {seed}")

    for path, node in nodes.items():
        if node["title"].lower() == "thuion":
            return path
    for path in nodes:
        if "thuion" in path.lower():
            return path
    raise ValueError("No seed supplied and no Thuion-like note found.")
