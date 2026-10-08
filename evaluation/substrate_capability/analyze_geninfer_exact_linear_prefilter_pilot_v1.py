#!/usr/bin/env python3
"""Analyze the gate-paired engineering pilot; emits no admission decision."""
from __future__ import annotations
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "evaluation/reports/geninfer_exact_linear_prefilter_pilot_v1_20261006.json"
OUT = ROOT / "evaluation/reports/geninfer_exact_linear_prefilter_pilot_v1_analysis_20261006.json"


def semantic_projection(row: dict) -> dict:
    tr = row["training"]
    held = row["heldout"]
    return {
        "training_status": tr["status"],
        "generator_payloads": tr["generator_payloads"],
        "training_residual": tr["residual"],
        "heldout_status": held["status"],
        "heldout_base": held["base"],
        "heldout_dim_infer": held["dim_infer"],
        "receipts": held["transform_receipts"],
        "reload_payloads": row["reload"]["generator_payloads"],
    }


def main() -> int:
    raw = json.loads(RAW.read_text())
    groups: dict[tuple[int, bool], dict[bool, dict]] = {}
    for row in raw["rows"]:
        key = (row["pilot_repeat"], row["audit"])
        gates = groups.setdefault(key, {})
        gate = row["prefilter_gate"]
        if gate in gates:
            raise SystemExit(f"duplicate paired cell {key} gate={gate}")
        gates[gate] = row
    pairs = []
    for (repeat, audit), gates in sorted(groups.items()):
        if set(gates) != {False, True}:
            raise SystemExit(f"incomplete pair {(repeat, audit)}")
        off, on = gates[False], gates[True]
        semantic_equal = semantic_projection(off) == semantic_projection(on)
        c = on["training"]["counters"]
        count_identity = c.get("gen_infer_prefilter_attempts", 0) == sum(c.get(k, 0) for k in (
            "gen_infer_prefilter_solved", "gen_infer_prefilter_proven_no_fit", "gen_infer_prefilter_fallback"))
        pairs.append({"repeat": repeat, "audit": audit, "semantic_equal": semantic_equal,
                      "counter_identity": count_identity,
                      "off_closure_ns": off["training"]["closure_ns"],
                      "on_closure_ns": on["training"]["closure_ns"],
                      "off_matrix_attempts": off["training"]["counters"].get("gen_infer_matrix_attempts", 0),
                      "on_matrix_attempts": c.get("gen_infer_matrix_attempts", 0),
                      "prefilter_attempts": c.get("gen_infer_prefilter_attempts", 0),
                      "prefilter_solved": c.get("gen_infer_prefilter_solved", 0),
                      "prefilter_proven_no_fit": c.get("gen_infer_prefilter_proven_no_fit", 0),
                      "prefilter_fallback": c.get("gen_infer_prefilter_fallback", 0)})
    audit_semantic_equal = True
    for repeat in range(1, raw["repeats_per_gate"] + 1):
        for gate in (False, True):
            no_audit = next(r for r in raw["rows"] if r["pilot_repeat"] == repeat and r["prefilter_gate"] == gate and not r["audit"])
            with_audit = next(r for r in raw["rows"] if r["pilot_repeat"] == repeat and r["prefilter_gate"] == gate and r["audit"])
            audit_semantic_equal &= semantic_projection(no_audit) == semantic_projection(with_audit)
    clean = [p for p in pairs if not p["audit"]]
    audit = [p for p in pairs if p["audit"]]
    summarize = lambda key: {"median": statistics.median(p[key] for p in clean),
                             "min": min(p[key] for p in clean), "max": max(p[key] for p in clean)}
    out = {
        "schema": "GenInferExactLinearPrefilterPilotV1Analysis",
        "status": "pilot_not_admission",
        "raw_sha256": __import__("hashlib").sha256(RAW.read_bytes()).hexdigest(),
        "complete_pairs": len(pairs),
        "audit_off_timing_pairs": len(clean),
        "audit_on_counter_pairs": len(audit),
        "all_semantic_pairs_equal": all(p["semantic_equal"] for p in pairs),
        "audit_on_off_semantics_equal": audit_semantic_equal,
        "all_counter_identities_hold": all(p["counter_identity"] for p in audit),
        "audit_off_training_closure_ns": {"gate_off": summarize("off_closure_ns"),
                                           "gate_on": summarize("on_closure_ns")},
        "audit_off_matrix_attempts": {"gate_off": summarize("off_matrix_attempts"),
                                      "gate_on": summarize("on_matrix_attempts")},
        "audit_on_prefilter_counts_total": {name: sum(p[name] for p in audit) for name in (
            "prefilter_attempts", "prefilter_solved", "prefilter_proven_no_fit", "prefilter_fallback")},
        "audit_on_matrix_attempts": {"gate_off": {"median": statistics.median(p["off_matrix_attempts"] for p in audit), "total": sum(p["off_matrix_attempts"] for p in audit)},
                                      "gate_on": {"median": statistics.median(p["on_matrix_attempts"] for p in audit), "total": sum(p["on_matrix_attempts"] for p in audit)}},
        "pairs": pairs,
        "interpretation_limit": "One linear-positive condition and ten repeats; same feature-on binary with runtime gate toggled. Engineering pilot only; not a three-build source-matched admission evaluation.",
    }
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
