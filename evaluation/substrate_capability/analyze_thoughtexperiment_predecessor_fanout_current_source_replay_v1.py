#!/usr/bin/env python3
"""Independent analysis of the current-source 100k predecessor fanout replay."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
RUNNER = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_current_source_replay_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_current_source_replay_v1_lock_20261004.json"
CAPTURE = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_current_source_replay_v1_20261004.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_current_source_replay_v1_analysis_20261004.json"
CONFIGS = {(b, r) for b in ("full_copy", "shared_graph_pages") for r in range(3)}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_inputs():
    spec = importlib.util.spec_from_file_location("current_fanout_runner", RUNNER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.locked_inputs()


def med(values):
    return statistics.median(values) if values else None


def main():
    capture = json.loads(CAPTURE.read_text())
    lock = json.loads(LOCK.read_text())
    rows = capture.get("runs", [])
    observed = {(r["configuration"]["backend"], r["configuration"]["replicate"]) for r in rows}
    checks = {
        "pre_run_lock_matches_capture": capture.get("locked_inputs") == lock.get("locked_inputs"),
        "current_source_lock_recomputes": source_inputs() == lock.get("locked_inputs"),
        "source_stable_during_capture": capture.get("source_stable") is True and capture.get("post_run_locked_inputs") == lock.get("locked_inputs"),
        "six_unique_workers": len(rows) == 6 and len({r.get("pid") for r in rows}) == 6 and observed == CONFIGS,
        "no_worker_failures": capture.get("worker_failures") == [],
        "fixed_configuration": all(r["configuration"].get("frames") == 4
            and r["configuration"].get("topology") == "independent_states"
            and r["configuration"].get("fanout") == 4
            and r["configuration"].get("noise_nodes") == 100_000 for r in rows),
        "candidate_selection_and_semantics": all(len(r["valid_candidate_ids"]) == 1
            and r["selected_candidate_id"] == r["correct_candidate_position"]
            and r["selected_branch_matches_monolithic_oracle"]
            and r["primary_matches_monolithic_oracle"]
            and r["oracle_grounded_frame_count"] == 4 and r["oracle_grounded_evidence_exact"]
            for r in rows),
        "only_correct_candidate_grounded": all(sum(x["grounding_status"] == "candidate_grounded"
            and x["evidence"] == "CommunicationInterpretation -> discourse-scoped DiscourseState -> prior grounded DiscourseEvent -> matching action-target head"
            for x in r["candidate_outcomes"]) == 1
            and all(x["grounding_status"] == "unresolved" for x in r["candidate_outcomes"]
                    if x["candidate_id"] != r["correct_candidate_position"])
            for r in rows),
        "primary_isolation_stale_rejection_and_rules": all(r["primary_unchanged_before_return"]
            and r["stale_residual_rejected"] and r["stale_retry_left_primary_unchanged"]
            and r["all_primary_rules_preserved"] for r in rows),
        "all_candidate_sweeps_quiescent": all(len(r["candidate_outcomes"]) == 4
            and all(x["quiescent"] and x["terminal_zero_progress_sweep"]
                    and x["grounded_evidence_exact"] for x in r["candidate_outcomes"])
            for r in rows),
    }
    summaries = {}
    for backend in ("full_copy", "shared_graph_pages"):
        group = [r for r in rows if r["configuration"]["backend"] == backend]
        life = [r["lifecycle_wall_ns"] for r in group]
        phase = [sum(r["phase_ns"].values()) for r in group]
        remainder = [a - b for a, b in zip(life, phase)]
        summaries[backend] = {
            "replicates": len(group),
            "median_lifecycle_ms": med(life) / 1e6 if life else None,
            "median_named_phase_sum_ms": med(phase) / 1e6 if phase else None,
            "median_unattributed_remainder_ms": med(remainder) / 1e6 if remainder else None,
            "median_named_phase_coverage": med([a / b for a, b in zip(phase, life) if b]) if life else None,
            "median_candidate_forks_ms": med([r["phase_ns"]["candidate_forks_total"] for r in group]) / 1e6 if group else None,
            "median_nodes": med([r["node_count"] for r in group]),
            "median_edges": med([r["edge_count"] for r in group]),
        }
    result = {"schema": "ThoughtexperimentPredecessorFanoutCurrentSourceReplayV1Analysis",
        "capture_sha256": sha(CAPTURE), "locked_inputs": lock.get("locked_inputs"),
        "checks": checks, "summaries": summaries,
        "interpretation": "A passing result confirms this one authored 100k workload on the captured engine. Named-phase remainder remains unattributed; do not infer that digesting alone causes it.",
        "claim_boundary": "One host, four independent-state frames, four supplied candidates, 100k unrelated nodes; no natural task prevalence, open-ended candidate generation, or scaling law."}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks, "summaries": summaries}, indent=2, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
