from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mba_blanket import compute_blanket
from mba_field import load_state, reconstruct_field
from mba_index import build_index, choose_seed


DEFAULT_PROBES = [
    ("circularity", "Circularity", "Thuion circular reasoning distinction continuity memory coherence source mystery"),
    ("falsifiability_gap", "Falsifiability gap", "Thuion falsifiability prediction test failure operational definition"),
    ("scope_creep", "Scope creep", "Thuion explains everything life awareness memory geometry source too broad"),
    ("metaphor_leakage", "Metaphor leakage", "Thuion metaphor physics biology consciousness projection light geometry"),
    ("escape_hatch", "Escape hatch", "Thuion source mystery unknowable explanatory gap boundary condition"),
    ("app_layer_bias", "App-layer bias", "Thuion Markov blanket app maintenance trace contamination continuity anchors"),
]


def run_adversarial_evaluation(vault: str | Path, seed: str | None = None, out: str | Path | None = None) -> dict[str, Any]:
    root = Path(vault).expanduser().resolve()
    index = build_index(root)
    seed_path = choose_seed(index, seed)
    trace_memory, maintenance_report = load_state(root)
    probe_results = []

    for probe_id, label, prompt in DEFAULT_PROBES:
        signals = [
            {"type": "active_note", "value": seed_path, "weight": 1, "source": "mba-adversarial"},
            {"type": "query", "value": prompt, "weight": 1, "source": "mba-adversarial"},
            {"type": "title_term", "value": "Thuion", "weight": 1, "source": "mba-adversarial"},
        ]
        blanket = compute_blanket(index, seed_path, prompt, signals)
        field = reconstruct_field(prompt, blanket, trace_memory, maintenance_report)
        scores = score_field(field, probe_id)
        probe_results.append({
            "id": probe_id,
            "label": label,
            "prompt": prompt,
            "topAttractors": field["conceptualAttractors"],
            "unresolvedTensions": field["unresolvedTensions"],
            "scores": scores,
        })

    highest = sorted(
        [{"id": p["id"], "label": p["label"], "score": p["scores"]["total"]} for p in probe_results],
        key=lambda item: (-item["score"], item["id"]),
    )
    report = {
        "seedPath": seed_path,
        "probes": probe_results,
        "summary": {
            "highestRisks": highest,
            "verdict": verdict(highest),
        },
    }
    output = Path(out).expanduser().resolve() if out else root / ".markov" / "adversarial-evaluation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def score_field(field: dict[str, Any], probe_id: str) -> dict[str, float]:
    paths = [item["path"] for item in field["conceptualAttractors"]]
    anchors = [item["path"] for item in field["continuityAnchors"]]
    scores = {
        "circularity": keyword_share(paths, ["distinction", "continuity", "memory", "coherence", "source"], 4) if probe_id == "circularity" else 0,
        "falsifiabilityGap": falsifiability_gap(paths) if probe_id == "falsifiability_gap" else 0,
        "scopeCreep": keyword_share(paths, ["life", "awareness", "memory", "geometry", "source"], 5) if probe_id == "scope_creep" else 0,
        "metaphorLeakage": keyword_share(paths, ["light", "projection", "geometry", "lattice", "awareness"], 4) if probe_id == "metaphor_leakage" else 0,
        "escapeHatch": keyword_share(paths[:3], ["source", "mystery", "unknowable", "boundary"], 2) if probe_id == "escape_hatch" else 0,
        "appLayerBias": app_layer_anchor_share(anchors) if probe_id == "app_layer_bias" else 0,
    }
    scores["total"] = round(max(scores.values()), 3)
    return scores


def falsifiability_gap(paths: list[str]) -> float:
    operational = count_matches(paths, ["test", "prediction", "failure", "falsifi", "operational", "definition"])
    fallback = count_matches(paths, ["distinction", "source", "mystery", "memory", "life", "geometry", "awareness"])
    if operational:
        return round(max(0, 0.45 - operational * 0.15), 3)
    return round(min(1, fallback / 4), 3)


def app_layer_anchor_share(paths: list[str]) -> float:
    if not paths:
        return 0
    app = sum(1 for path in paths if path.startswith(("src/", "docs/", "tests/", "memory/")) or path == "README.md")
    return round(app / len(paths), 3)


def keyword_share(paths: list[str], keywords: list[str], denominator: int) -> float:
    return round(min(1, count_matches(paths, keywords) / denominator), 3)


def count_matches(paths: list[str], keywords: list[str]) -> int:
    lowered = [path.lower() for path in paths]
    return sum(1 for keyword in keywords if any(keyword in path for path in lowered))


def verdict(highest: list[dict[str, Any]]) -> str:
    top = highest[0]["score"] if highest else 0
    if top >= 0.7:
        return "The theory is underconstrained: adversarial probes activate its core ontology more readily than independent failure surfaces."
    if top >= 0.4:
        return "The theory has visible pressure points, but the adversarial surface is partially constrained."
    return "The adversarial suite found no dominant risk in the reconstructed field."
