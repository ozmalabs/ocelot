#!/usr/bin/env python3
"""Independent source, semantic, and scaling checks for predecessor fanout."""
from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_v1.py"
CAPTURE = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_v1_20261003.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_v1_analysis_20261003.json"
FRAMES = (1, 4, 8)
TOPOLOGIES = ("chained_state", "independent_states")
FANOUTS = (1, 4, 16)
NOISE = (0, 10_000)
BACKENDS = ("full_copy", "shared_graph_pages")
REPLICATES = (0, 1, 2)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def median(values):
    clean = [x for x in values if x is not None]
    return statistics.median(clean) if clean else None


def main() -> None:
    raw = json.loads(CAPTURE.read_text())
    spec = importlib.util.spec_from_file_location("predecessor_fanout_runner", RUNNER)
    runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
    rows = raw.get("runs", [])
    expected = list(itertools.product(FRAMES, TOPOLOGIES, FANOUTS, NOISE, BACKENDS, REPLICATES))
    observed = [(r["configuration"]["frames"], r["configuration"]["topology"],
        r["configuration"]["fanout"], r["configuration"]["noise_nodes"],
        r["configuration"]["backend"], r["configuration"]["replicate"]) for r in rows]
    checks = {
        "schema": raw.get("schema") == "ThoughtexperimentPredecessorFanoutV1",
        "complete_current_source_lock": runner.source_lock() == raw.get("locked_inputs") == raw.get("post_run_inputs"),
        "runner_hash_locked": sha(RUNNER) == raw.get("locked_inputs", {}).get(
            "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_v1.py"),
        "complete_unique_216_cell_matrix": len(rows) == 216 and len(set(observed)) == 216 and
            set(observed) == set(expected),
        "fresh_process_per_cell": len({r["pid"] for r in rows}) == 216,
        "all_registered_seed_loads": all("communication_intent_arbitration" in r["loaded_seed_ids"] for r in rows),
        "exactly_one_grounded_hypothesis": all(r["valid_candidate_ids"] == [r["correct_candidate_position"]] for r in rows),
        "all_decoy_candidates_abstain": all(sum(x["grounding_status"] == "unresolved" for x in r["candidate_outcomes"]) == r["configuration"]["fanout"] - 1 for r in rows),
        "all_frame_sweeps_quiescent": all(all(x["quiescent"] and x["terminal_zero_progress_sweep"] for x in r["candidate_outcomes"]) for r in rows),
        "all_frames_match_semantic_oracle": all(all(
            x["grounded_frame_count"] == r["configuration"]["frames"] -
                (0 if x["candidate_id"] == r["correct_candidate_position"] else 1)
            and x["grounded_evidence_exact"] for x in r["candidate_outcomes"])
            and r["oracle_grounded_frame_count"] == r["configuration"]["frames"]
            and r["oracle_grounded_evidence_exact"] for r in rows),
        "return_isolation_and_stale_retry_atomic": all(r["primary_unchanged_before_return"] and
            r["returned_branch_matches"] and r["stale_residual_rejected"] and
            r["stale_retry_left_primary_unchanged"] for r in rows),
        "selected_graph_matches_monolithic_oracle": all(r["primary_matches_monolithic_oracle"] and
            r["selected_branch_matches_monolithic_oracle"] for r in rows),
        "source_runner_checks_pass": all(raw.get("checks", {}).values()),
    }
    summary = {}
    keyset = sorted({(r["configuration"]["frames"], r["configuration"]["topology"],
        r["configuration"]["fanout"], r["configuration"]["noise_nodes"],
        r["configuration"]["backend"]) for r in rows})
    for frames, topology, fanout, noise, backend in keyset:
        group = [r for r in rows if r["configuration"]["frames"] == frames and
            r["configuration"]["topology"] == topology and r["configuration"]["fanout"] == fanout and
            r["configuration"]["noise_nodes"] == noise and r["configuration"]["backend"] == backend]
        entry = {"replicates": len(group), "node_count_median": median([r["node_count"] for r in group]),
            "edge_count_median": median([r["edge_count"] for r in group]),
            "lifecycle_ms_median": median([r["lifecycle_wall_ns"] / 1e6 for r in group]),
            "oracle_ms_median": median([r["monolithic_oracle_ns"] / 1e6 for r in group]),
            "candidate_work_median": median([sum(x["work_steps"] for x in r["candidate_outcomes"]) for r in group]),
            "candidate_scope_calls_median": median([sum(x["scope_calls"] for x in r["candidate_outcomes"]) for r in group]),
            "fanout_pss_delta_mib_median": median([
                (r["memory_kib"]["retained_fanout_pss"] - r["memory_kib"]["baseline_pss"]) / 1024
                for r in group if r["memory_kib"]["retained_fanout_pss"] is not None and r["memory_kib"]["baseline_pss"] is not None]),
            "post_drop_pss_delta_mib_median": median([
                (r["memory_kib"]["after_drop_pss"] - r["memory_kib"]["baseline_pss"]) / 1024
                for r in group if r["memory_kib"]["after_drop_pss"] is not None and r["memory_kib"]["baseline_pss"] is not None]),
            "peak_rss_mib_median": median([r["memory_kib"]["peak_rss_retained"] / 1024 for r in group]),
            "selected_candidate_positions": [r["selected_candidate_id"] for r in group],
        }
        summary[f"n{frames}/{topology}/k{fanout}/noise{noise}/{backend}"] = entry
    output = {"schema": "ThoughtexperimentPredecessorFanoutAnalysisV1",
        "capture_sha256": sha(CAPTURE), "checks": checks, "cell_count": len(rows),
        "summary_by_workload": summary}
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    OUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": OUT.relative_to(ROOT).as_posix(), "checks": checks,
        "cell_count": len(rows)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("independent predecessor fanout analysis failed")


if __name__ == "__main__":
    main()
