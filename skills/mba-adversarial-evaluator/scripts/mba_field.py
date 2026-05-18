from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_state(vault: str | Path) -> tuple[dict[str, Any], dict[str, Any] | None]:
    markov = Path(vault).expanduser().resolve() / ".markov"
    trace = {
        "attractors": read_json(markov / "trace-memory" / "attractors.json", {"notes": {}}),
        "transitions": read_json(markov / "trace-memory" / "transitions.json", {"paths": {}}),
        "contamination": read_json(markov / "trace-memory" / "contamination.json", {"transitions": {}}),
        "proceduralChains": read_json(markov / "trace-memory" / "procedural-chains.json", {"chains": {}}),
        "maintenanceHistory": read_json(markov / "trace-memory" / "maintenance-history.json", []),
    }
    report = read_json(markov / "maintenance-report.json", None)
    return trace, report


def reconstruct_field(
    prompt: str,
    blanket: dict[str, Any],
    trace_memory: dict[str, Any] | None = None,
    maintenance_report: dict[str, Any] | None = None,
    max_items: int = 6,
) -> dict[str, Any]:
    trace_memory = trace_memory or {"attractors": {"notes": {}}}
    attractor_trace = trace_memory.get("attractors", {}).get("notes", {})
    report_attractors = {item["path"]: item for item in (maintenance_report or {}).get("strengthenedAttractors", [])}

    attractors = []
    for candidate in blanket.get("candidates", []):
        path = candidate["node"]["path"]
        boost = report_attractors.get(path, {}).get("persistence", 0) + attractor_trace.get(path, {}).get("persistence", 0)
        attractors.append({
            "path": path,
            "label": candidate["node"]["title"],
            "strength": round(candidate["score"]["total"] + boost, 3),
            "reasons": unique([p["reason"] for p in candidate.get("provenance", [])]),
        })
    attractors.sort(key=lambda item: (-item["strength"], item["path"]))

    anchors = []
    for item in attractor_trace.values():
        anchors.append({
            "path": item["path"],
            "persistence": item.get("persistence", 0),
            "continuity": item.get("averageContinuity", 0),
        })
    for item in (maintenance_report or {}).get("anchorPersistenceChanges", []):
        anchors.append({
            "path": item["path"],
            "persistence": item.get("persistence", 0),
            "continuity": item.get("averageContinuity", 0),
        })
    anchors = merge_anchors(anchors)[:max_items]

    return {
        "prompt": prompt,
        "orientation": f"Current prompt terms: {', '.join(tokenize(prompt)[:6])}. Active attractor region: {', '.join(a['label'] for a in attractors[:3])}.",
        "conceptualAttractors": attractors[:max_items],
        "continuityAnchors": anchors,
        "unresolvedTensions": [f"Continue from current conceptual pressure: {prompt[:140]}."],
        "activeAssumptions": [
            "The cognitive field is non-authoritative and must not override canonical vault truth.",
            "Preserve orientation and unresolved structure rather than replaying note text.",
            "Use maintained tendencies as continuity signals, not semantic facts.",
        ],
    }


def compile_field(field: dict[str, Any], max_length: int = 2400) -> str:
    lines = [
        "ACTIVE COGNITIVE FIELD",
        "Use this as non-authoritative state-space steering. The vault remains canonical.",
        "",
        "Conceptual Orientation",
        f"- {field['orientation']}",
        "",
        "Conceptual Attractors",
    ]
    for item in field["conceptualAttractors"]:
        lines.append(f"- {item['path']} | strength {item['strength']} | {', '.join(item['reasons'])}")
    lines.extend(["", "Continuity Anchors"])
    for item in field["continuityAnchors"]:
        lines.append(f"- {item['path']} | persistence {item['persistence']} | continuity {item['continuity']}")
    lines.extend(["", "Unresolved Tensions"])
    lines.extend(f"- {item}" for item in field["unresolvedTensions"])
    text = "\n".join(lines)
    if len(text) <= max_length:
        return text
    return text[: max_length - 28].rstrip() + "\n[FIELD TRUNCATED BY BOUND]"


def read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback


def merge_anchors(anchors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_path: dict[str, dict[str, Any]] = {}
    for anchor in anchors:
        existing = by_path.get(anchor["path"])
        if not existing or anchor.get("persistence", 0) > existing.get("persistence", 0):
            by_path[anchor["path"]] = anchor
    return sorted(by_path.values(), key=lambda item: (-item.get("persistence", 0), -item.get("continuity", 0), item["path"]))


def tokenize(text: str) -> list[str]:
    import re

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
