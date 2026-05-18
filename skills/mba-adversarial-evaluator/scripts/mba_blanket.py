from __future__ import annotations

import math
import re
from typing import Any


DEFAULT_SETTINGS = {
    "max_results": 12,
    "graph_depth": 2,
    "weight_direct_link": 4.0,
    "weight_backlink": 4.0,
    "weight_co_parent": 2.0,
    "weight_shared_tag": 1.5,
    "weight_recency": 1.0,
    "weight_active_context": 3.0,
    "weight_query_term": 2.0,
    "include_folders": True,
}


def compute_blanket(
    index: dict[str, Any],
    seed_path: str | None,
    query: str = "",
    context_signals: list[dict[str, Any]] | None = None,
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = {**DEFAULT_SETTINGS, **(settings or {})}
    signals = context_signals or []
    query_terms = tokenize(query)
    drafts: dict[str, dict[str, Any]] = {}
    nodes = index["nodes"]

    if seed_path and seed_path in nodes:
        seed = nodes[seed_path]
        add_seed_graph(index, seed_path, drafts)
        expand_by_depth(index, seed_path, drafts, int(cfg["graph_depth"]))
        add_same_folder(index, seed, drafts, bool(cfg["include_folders"]))
        add_recency_cluster(index, seed, drafts)

    add_query_matches(index, drafts, query_terms)
    add_active_context_overlap(drafts, signals)

    candidates = []
    for path, draft in drafts.items():
        if path == seed_path:
            continue
        draft["score"] = score_candidate(draft, cfg)
        if draft["score"]["total"] > -100:
            candidates.append(draft)

    candidates.sort(key=lambda item: (-item["score"]["total"], item["node"]["path"]))
    return {
        "seedPath": seed_path,
        "query": query,
        "activeNotePath": next((s["value"] for s in signals if s.get("type") == "active_note"), None),
        "contextSignals": signals,
        "candidates": candidates[: int(cfg["max_results"])],
        "diagnostics": [
            "Vault graph treated as latent geometry; result is a runtime activation shell.",
            f"Candidate count before max_results: {len(drafts)}.",
        ],
    }


def add_seed_graph(index: dict[str, Any], seed_path: str, drafts: dict[str, dict[str, Any]]) -> None:
    for target in index["forward"].get(seed_path, []):
        add_candidate(index, drafts, target, "child", 1, "direct_link", 1)
    for source in index["backlinks"].get(seed_path, []):
        add_candidate(index, drafts, source, "parent", 1, "backlink", 1)
    for related in co_parents(index, seed_path):
        add_candidate(index, drafts, related, "co-parent", 1, "co_parent", 1)
    seed = index["nodes"][seed_path]
    for path, node in index["nodes"].items():
        if path == seed_path:
            continue
        shared = sorted(set(seed["tags"]).intersection(node["tags"]))
        if shared:
            add_candidate(index, drafts, path, "tag-neighbor", 1, "shared_tag", len(shared))
            drafts[path]["sharedTags"] = unique(drafts[path]["sharedTags"] + shared)


def expand_by_depth(index: dict[str, Any], seed_path: str, drafts: dict[str, dict[str, Any]], graph_depth: int) -> None:
    frontier = {seed_path}
    visited = {seed_path}
    for depth in range(1, graph_depth + 1):
        next_frontier = set()
        for path in frontier:
            neighbors = index["forward"].get(path, []) + index["backlinks"].get(path, [])
            for neighbor in neighbors:
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                next_frontier.add(neighbor)
                if depth > 1:
                    add_candidate(index, drafts, neighbor, "semantic-placeholder", depth, "graph_depth", 1 / depth)
        frontier = next_frontier


def add_same_folder(index: dict[str, Any], seed: dict[str, Any], drafts: dict[str, dict[str, Any]], include: bool) -> None:
    if not include or not seed["folder"]:
        return
    for path, node in index["nodes"].items():
        if path != seed["path"] and node["folder"] == seed["folder"]:
            add_candidate(index, drafts, path, "same-folder", 2, "same_folder", 1)


def add_recency_cluster(index: dict[str, Any], seed: dict[str, Any], drafts: dict[str, dict[str, Any]]) -> None:
    for path, node in index["nodes"].items():
        if path == seed["path"]:
            continue
        days = abs(node["mtime"] - seed["mtime"]) / 86_400_000
        if days > 7:
            continue
        strength = 1 - days / 7
        add_candidate(index, drafts, path, "recency-cluster", 2, "recency_cluster", strength)
        drafts[path]["recencyClusterStrength"] = max(drafts[path]["recencyClusterStrength"], strength)


def add_query_matches(index: dict[str, Any], drafts: dict[str, dict[str, Any]], query_terms: list[str]) -> None:
    if not query_terms:
        return
    for path, node in index["nodes"].items():
        haystack = searchable_terms(node)
        overlap = sorted(set(query_terms).intersection(haystack))
        if not overlap:
            continue
        add_candidate(index, drafts, path, "semantic-placeholder", 1, "query_overlap", len(overlap))
        title_overlap = sorted(set(query_terms).intersection(tokenize(node["title"])))
        draft = drafts[path]
        draft["queryTerms"] = query_terms
        draft["queryOverlapTerms"] = unique(draft["queryOverlapTerms"] + overlap)
        draft["titleOverlapTerms"] = unique(draft["titleOverlapTerms"] + title_overlap)
        if title_overlap:
            draft["provenance"].append({"reason": "title_overlap", "detail": "Title terms matched.", "strength": len(title_overlap)})


def add_active_context_overlap(drafts: dict[str, dict[str, Any]], signals: list[dict[str, Any]]) -> None:
    terms = []
    for signal in signals:
        if signal.get("type") not in ("recent_note", "active_note"):
            terms.extend(tokenize(str(signal.get("value", ""))))
    for draft in drafts.values():
        overlap = sorted(set(terms).intersection(searchable_terms(draft["node"])))
        if overlap:
            draft["activeContextOverlap"] = unique(draft["activeContextOverlap"] + overlap)
            draft["provenance"].append({"reason": "active_context_overlap", "detail": "Active context overlap.", "strength": len(overlap)})


def add_candidate(index: dict[str, Any], drafts: dict[str, dict[str, Any]], path: str, relation: str, depth: int, reason: str, strength: float) -> None:
    node = index["nodes"].get(path)
    if not node:
        return
    if path not in drafts:
        drafts[path] = {
            "node": node,
            "relationTypes": [],
            "provenance": [],
            "depth": depth,
            "linkCount": 0,
            "sharedTags": [],
            "queryTerms": [],
            "queryOverlapTerms": [],
            "titleOverlapTerms": [],
            "activeContextOverlap": [],
            "recencyClusterStrength": 0,
            "coActivationAffinity": 0,
            "score": {"total": 0, "contributions": []},
        }
    draft = drafts[path]
    draft["relationTypes"] = unique(draft["relationTypes"] + [relation])
    draft["depth"] = min(draft["depth"], depth)
    if reason in ("direct_link", "backlink", "co_parent"):
        draft["linkCount"] += 1
    draft["provenance"].append({"reason": reason, "detail": reason, "strength": strength})


def score_candidate(candidate: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    reasons = {p["reason"]: p for p in candidate["provenance"]}
    contributions = []
    add_score(contributions, "direct_link", cfg["weight_direct_link"] if "direct_link" in reasons else 0)
    add_score(contributions, "backlink", cfg["weight_backlink"] if "backlink" in reasons else 0)
    add_score(contributions, "co_parent", cfg["weight_co_parent"] if "co_parent" in reasons else 0)
    add_score(contributions, "shared_tag", cfg["weight_shared_tag"] * len(candidate["sharedTags"]))
    add_score(contributions, "recency_cluster", cfg["weight_recency"] * candidate["recencyClusterStrength"])
    add_score(contributions, "query_overlap", cfg["weight_query_term"] * len(candidate["queryOverlapTerms"]))
    add_score(contributions, "title_overlap", cfg["weight_query_term"] * len(candidate["titleOverlapTerms"]))
    add_score(contributions, "active_context_overlap", cfg["weight_active_context"] * len(candidate["activeContextOverlap"]))
    add_score(contributions, "graph_depth", 1 / candidate["depth"] if "graph_depth" in reasons else 0)
    total = round(sum(item["value"] for item in contributions), 3)
    return {"total": total, "contributions": contributions}


def add_score(contributions: list[dict[str, Any]], reason: str, value: float) -> None:
    if value > 0:
        contributions.append({"reason": reason, "label": reason, "value": round(value, 3), "detail": reason})


def co_parents(index: dict[str, Any], path: str) -> list[str]:
    children = index["forward"].get(path, [])
    parents = index["backlinks"].get(path, [])
    related = set()
    for source, links in index["forward"].items():
        if source != path and any(link in children for link in links):
            related.add(source)
    for parent in parents:
        for sibling in index["forward"].get(parent, []):
            if sibling != path:
                related.add(sibling)
    return sorted(related)


def searchable_terms(node: dict[str, Any]) -> list[str]:
    terms = tokenize(node["path"]) + tokenize(node["title"])
    for value in node.get("tags", []) + node.get("aliases", []) + node.get("headings", []):
        terms.extend(tokenize(value))
    for key, value in node.get("frontmatter", {}).items():
        terms.extend(tokenize(key))
        terms.extend(tokenize(str(value)))
    return unique(terms)


def tokenize(text: str) -> list[str]:
    return unique(re.findall(r"[a-z0-9]+", text.lower()))


def unique(values: list[Any]) -> list[Any]:
    seen = set()
    out = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out
