#!/usr/bin/env python3
"""Independent checks for the locked native scoped owner effect matrix."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_native_scoped_owner_effect_matrix_v1_20260926.json"
LOCK = ROOT / "evaluation/substrate_capability/native_scoped_owner_effect_matrix_v1_2_lock_20260926.json"
PATHS = {
    "protocol": ROOT / "docs/research/engine_substrate/SUBSTRATE_NATIVE_SCOPED_OWNER_EFFECT_MATRIX_PREREG_20260926.md",
    "runner": ROOT / "scripts/substrate_native_scoped_owner_effect_matrix_v1.py",
    "analyzer": ROOT / "scripts/analyze_substrate_native_scoped_owner_effect_matrix_v1.py",
    "rewrite": ROOT / "runners/dsl/src/rewrite.rs",
    "substrate": ROOT / "runners/dsl/src/substrate.rs",
    "py_binding": ROOT / "runners/dsl/src/py.rs",
    "native_build_manifest": ROOT / "runners/dsl/python/substrate_rs/_native.build.json",
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    raw = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    hashes = {key: sha(path) for key, path in PATHS.items()}
    keyed = {(r["case"], r["size"], r["replicate"], r["arm"]): r for r in raw["runs"]}
    expected_n = 5 * 3 * 2 * 2
    gates = {
        "lock_hashes_match": hashes == lock == raw["locked_inputs"],
        "matrix_complete": len(keyed) == expected_n and len(raw["runs"]) == expected_n,
        "fresh_process_per_worker": len({r["pid"] for r in raw["runs"]}) == expected_n,
        "native_build_identity_uniform": len({r["native_extension_sha256"] for r in raw["runs"]}) == 1,
        "settled_no_budget_or_deferred": all(
            r["progress_steps"] > 0 and not r["hit_progress_budget"] and not r["deferred_effects_pending"]
            and r["terminal_progress_steps"] == 0 and not r["terminal_deferred_effects_pending"]
            and (r["arm"] != "oracle" or (r["status"] == "fixed_point" and r["exact_graph_state_diff"]))
            for r in raw["runs"]),
        "paired_state_parity": all(
            keyed[(c, n, rep, "scoped")]["state"] == keyed[(c, n, rep, "oracle")]["state"]
            for c in ("shared_add_edge", "shared_del_edge", "shared_set_attr", "owned_node_birth", "owned_node_deletion")
            for n in (2, 4, 8) for rep in range(2)),
        "exact_owner_parity": all(
            keyed[(c, n, rep, "scoped")]["owner_names"] == keyed[(c, n, rep, "oracle")]["owner_names"]
            for c in ("shared_add_edge", "shared_del_edge", "shared_set_attr", "owned_node_birth", "owned_node_deletion")
            for n in (2, 4, 8) for rep in range(2)),
        "scoped_targets_cover_snapshot": all(
            set(keyed[(c, n, rep, "oracle")]["affected_nodes"]) <= set(keyed[(c, n, rep, "scoped")]["affected_nodes"])
            and {tuple(e) for e in keyed[(c, n, rep, "oracle")]["affected_edges"]}
            <= {tuple(e) for e in keyed[(c, n, rep, "scoped")]["affected_edges"]}
            for c in ("shared_add_edge", "shared_del_edge", "shared_set_attr", "owned_node_birth", "owned_node_deletion")
            for n in (2, 4, 8) for rep in range(2)),
    }
    expected = {
        "shared_add_edge": lambda n: {"controller", "frame_0", f"frame_{n-1}"},
        "shared_del_edge": lambda n: {"controller", "frame_0", f"frame_{n-1}"},
        "shared_set_attr": lambda n: {"controller", "frame_0"},
        "owned_node_birth": lambda n: {"controller"},
        # Deleting src also removes src->tgt, so both endpoint owners are affected.
        "owned_node_deletion": lambda n: {"controller", "frame_0", f"frame_{n-1}"},
    }
    gates["expected_owners_only"] = all(
        set(keyed[(c, n, rep, arm)]["owner_names"]) == expected[c](n)
        for c in expected for n in (2, 4, 8) for rep in range(2) for arm in ("scoped", "oracle"))
    outcome = {"shared_add_edge": lambda s: s["derived_edge"] is True,
               "shared_del_edge": lambda s: s["derived_edge"] is False,
               "shared_set_attr": lambda s: s["src_value"] == 9.0,
               "owned_node_birth": lambda s: s["witness_count"] == 1,
               "owned_node_deletion": lambda s: s["src_live"] is False}
    gates["expected_effect_outcomes"] = all(
        outcome[c](keyed[(c, n, rep, arm)]["state"])
        and keyed[(c, n, rep, arm)]["state"]["trigger_active"] == 0.0
        for c in outcome for n in (2, 4, 8) for rep in range(2) for arm in ("scoped", "oracle"))
    report = {"run_id": raw["run_id"], "raw_sha256": sha(RAW), "checks": gates,
              "all_checks_pass": all(gates.values()),
              "summary": {c: {"n": 12, "owner_sets": sorted({tuple(keyed[(c,n,r,a)]["owner_names"])
                    for n in (2,4,8) for r in range(2) for a in ("scoped","oracle")})}
                    for c in expected},
              "claim_boundary": raw["claim_boundary"]}
    dest = ROOT / "evaluation/reports/substrate_native_scoped_owner_effect_matrix_v1_analysis_20260926.json"
    dest.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(dest.relative_to(ROOT)), "all_checks_pass": report["all_checks_pass"],
                      "checks": gates, "summary": report["summary"]}, indent=2))
    if not report["all_checks_pass"]:
        raise SystemExit("one or more locked gates failed; retain raw and analysis")


if __name__ == "__main__":
    main()
