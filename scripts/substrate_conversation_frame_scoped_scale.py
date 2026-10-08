#!/usr/bin/env python3
"""Compare full and frame-scoped closure on live conversation deliberation."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import random
import resource
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_CONVERSATION_FRAME_SCOPED_SCALE_PREREG_20260925.md"
LOCK = ROOT / "evaluation/substrate_capability/conversation_frame_scoped_scale_lock_20260925.json"
OUT = ROOT / "evaluation/reports/substrate_conversation_frame_scoped_scale_20260925.json"
SEED = ROOT / "seeds/conversation_deliberation_phase4a.json"
MATERIALIZER = ROOT / "domains/conversation_deliberation.py"
SIZES = (1, 2, 4, 8)
REPLICATES = 3
ARMS = ("full", "scoped")
CAP = 100_000


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def projection(adapter, deliberations: list[tuple[str, object]]) -> list[dict]:
    rows = []
    for key, d in deliberations:
        attrs = adapter.s.node(d)["attrs"]
        candidates = {}
        for c in adapter.inner.neighbours(d, "has_candidate"):
            ca = adapter.s.node(c)["attrs"]
            candidates[ca["candidate_id"]] = {
                "status": ca.get("status"),
                "reason": ca.get("rejection_reason"),
                "score": ca.get("arbitration_score"),
                "valuation_trace": ca.get("valuation_trace"),
                "rejection_trace": ca.get("rejection_trace"),
            }
        selections = [adapter.s.node(x)["attrs"].get("selected_candidate_id")
                      for x in adapter.inner.neighbours(d, "has_selection")]
        rows.append({"frame": key, "status": attrs.get("status"),
                     "candidate_trace_complete": attrs.get("candidate_trace_complete"),
                     "selection": selections, "candidates": candidates})
    return rows


def run_arm(size: int, rep: int, arm: str) -> dict:
    from substrate.world_adapter import WorldAdapter
    from substrate.seed_loader import manifest_for
    from substrate_rs import _native
    from domains.conversation_deliberation import materialize_deliberation

    adapter = WorldAdapter(seeds=())
    adapter.inner.load_seed_manifest(manifest_for("conversation_deliberation_phase4a"), adapter.agent)
    tasks = []
    mts = []
    for i in range(size):
        key = f"frame_{i}"
        goal = adapter.s.add_node("Goal", {"kind": "answer", "status": "active", "frame_key": key})
        candidates = [
            {"candidate_id": f"{key}_repair", "kind": "repair", "grounding": 1.0,
             "expected_value": 0.55, "residual_cost": 0.1, "consequence": 0.2,
             "novelty": 0.1, "evidence_path": "goal->gap->repair"},
            {"candidate_id": f"{key}_answer", "kind": "answer", "grounding": 1.0,
             "expected_value": 0.8, "residual_cost": 0.1, "consequence": 0.5,
             "novelty": 0.2, "evidence_path": "goal->referent->fact"},
            {"candidate_id": f"{key}_unsupported", "kind": "answer", "grounding": 0.0,
             "expected_value": 1.0, "residual_cost": 0.0, "consequence": 1.0,
             "novelty": 1.0, "evidence_path": ""},
        ]
        d = materialize_deliberation(adapter, goal=goal, candidates=candidates)
        mt = adapter.inner.add_node("Microtheory", {"name": key})
        owned = [goal, d, *adapter.inner.neighbours(d, "has_candidate")]
        for node in owned:
            adapter.inner.add_edge_unchecked(mt, "has_concept", node, {})
        tasks.append((key, d))
        mts.append(mt)

    adapter.inner.scale_audit_reset()
    adapter.inner.scale_audit_per_rule_reset()
    adapter.inner.scale_audit_set_enabled(True)
    adapter.inner.scale_audit_set_per_rule_enabled(True)
    wall0, cpu0 = time.perf_counter_ns(), time.process_time_ns()
    if arm == "full":
        settle = adapter.inner.run_rules_report(CAP, False)
        turns = 0
        progress_applied = int(settle["progress_steps"])
    else:
        moved = rounds = turns = 0
        while rounds < CAP:
            rounds += 1
            round_progress = 0
            for mt in mts:
                count = int(adapter.inner.run_rules_scoped(CAP - moved, False, mt))
                moved += count
                round_progress += count
                turns += 1
                if moved >= CAP:
                    break
            if round_progress == 0 or moved >= CAP:
                break
        settle = adapter.inner.run_rules_report(CAP, False)
        progress_applied = moved
    wall_ns, cpu_ns = time.perf_counter_ns() - wall0, time.process_time_ns() - cpu0
    scale = dict(adapter.inner.scale_audit_snapshot())
    access = adapter.inner.rule_access_sets()
    rule_names = {int(row[0]): str(row[1]) for row in access}
    per_rule = [{"rule_index": int(idx), "rule_name": rule_names.get(int(idx), "?"),
                 "metric": str(metric), "count": int(count)}
                for idx, metric, count in adapter.inner.scale_audit_per_rule_snapshot()]
    adapter.inner.scale_audit_set_per_rule_enabled(False)
    adapter.inner.scale_audit_set_enabled(False)
    results = projection(adapter, tasks)
    checks = []
    for row in results:
        key = row["frame"]
        checks.append(row["status"] == "selected"
                      and row["selection"] == [f"{key}_answer"]
                      and row["candidates"][f"{key}_answer"]["status"] == "selected"
                      and row["candidates"][f"{key}_repair"]["status"] == "rejected"
                      and row["candidates"][f"{key}_unsupported"]["status"] == "rejected"
                      and row["candidates"][f"{key}_unsupported"]["reason"] == "missing_grounding_evidence")
    native_path = Path(_native.__file__).resolve()
    return {
        "size": size, "replicate": rep, "arm": arm,
        "rule_count": sum(1 for r in access if r[2]),
        "outcome": settle,
        "progress_applied": progress_applied,
        "frame_turns": turns,
        "wall_ns": wall_ns, "cpu_ns": cpu_ns,
        "peak_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        "scale_audit": scale,
        "per_rule_audit": per_rule,
        "projection": results,
        "expected_task_outcomes": checks,
        "all_expected_task_outcomes": all(checks),
        "provenance": {"python": sys.version, "platform": platform.platform(),
                       "native_extension_path": str(native_path),
                       "native_extension_sha256": sha(native_path)},
    }


def main() -> None:
    if len(sys.argv) == 5 and sys.argv[1] == "--worker":
        print(json.dumps(run_arm(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]), sort_keys=True))
        return
    locked = {
        "preregistration_sha256": sha(PREREG),
        "runner_sha256": sha(Path(__file__).resolve()),
        "seed_sha256": sha(SEED),
        "materializer_sha256": sha(MATERIALIZER),
        "rewrite_sha256": sha(ROOT / "runners/dsl/src/rewrite.rs"),
        "substrate_sha256": sha(ROOT / "runners/dsl/src/substrate.rs"),
        "py_binding_sha256": sha(ROOT / "runners/dsl/src/py.rs"),
    }
    if len(sys.argv) == 2 and sys.argv[1] == "--lock":
        print(json.dumps(locked, indent=2, sort_keys=True)); return
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing lock or locked inputs changed")
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT}:{ROOT / 'runners/dsl/python'}:{env.get('PYTHONPATH', '')}"
    stale = subprocess.check_output(
        [sys.executable, "-c", "from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"],
        cwd=ROOT, env=env, text=True).strip()
    if stale:
        raise SystemExit("native build stale:\n" + stale)
    jobs = [(n, rep, arm) for n in SIZES for rep in range(REPLICATES) for arm in ARMS]
    random.Random(20260925).shuffle(jobs)
    records = []
    for n, rep, arm in jobs:
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                               "--worker", str(n), str(rep), arm], cwd=ROOT, env=env,
                              text=True, capture_output=True, check=True)
        row = json.loads(proc.stdout.strip())
        records.append(row)
        print(f"n={n} rep={rep} arm={arm} status={row['outcome']['status']} "
              f"wall_ms={row['wall_ns']/1e6:.2f}", flush=True)
    indexed = {(r["size"], r["replicate"], r["arm"]): r for r in records}
    pairs = []
    for n in SIZES:
        for rep in range(REPLICATES):
            full = indexed[n, rep, "full"]
            scoped = indexed[n, rep, "scoped"]
            pairs.append({"size": n, "replicate": rep,
                          "projection_equal": full["projection"] == scoped["projection"],
                          "fixed_point_both": full["outcome"]["status"] == scoped["outcome"]["status"] == "fixed_point",
                          "full_progress": full["progress_applied"],
                          "scoped_progress": scoped["progress_applied"],
                          "full_wall_ns": full["wall_ns"], "scoped_wall_ns": scoped["wall_ns"],
                          "full_cpu_ns": full["cpu_ns"], "scoped_cpu_ns": scoped["cpu_ns"],
                          "full_candidates": full["scale_audit"].get("cand_enum", 0),
                          "scoped_candidates": scoped["scale_audit"].get("cand_enum", 0),
                          "full_term_units": full["scale_audit"].get("term_units_total", 0),
                          "scoped_term_units": scoped["scale_audit"].get("term_units_total", 0),
                          "scoped_frame_turns": scoped["frame_turns"]})
    checks = {
        "worker_count_24": len(records) == 24,
        "all_task_outcomes_expected": all(r["all_expected_task_outcomes"] for r in records),
        "all_fixed_point_reports": all(r["outcome"]["status"] == "fixed_point" for r in records),
        "all_counter_parity_pairs": all(p["projection_equal"] and p["fixed_point_both"] and
                                         p["full_progress"] == p["scoped_progress"] for p in pairs),
        "all_sizes_and_replicates_present": len(pairs) == 12,
    }
    summaries = []
    for n in SIZES:
        group = [p for p in pairs if p["size"] == n]
        summaries.append({"size": n, "replicates": len(group),
                          "median_full_candidates": int(statistics.median(p["full_candidates"] for p in group)),
                          "median_scoped_candidates": int(statistics.median(p["scoped_candidates"] for p in group)),
                          "median_full_term_units": int(statistics.median(p["full_term_units"] for p in group)),
                          "median_scoped_term_units": int(statistics.median(p["scoped_term_units"] for p in group)),
                          "median_full_wall_ns": int(statistics.median(p["full_wall_ns"] for p in group)),
                          "median_scoped_wall_ns": int(statistics.median(p["scoped_wall_ns"] for p in group)),
                          "median_scoped_frame_turns": int(statistics.median(p["scoped_frame_turns"] for p in group))})
    payload = {"schema_version": 1, "run_id": "conversation-frame-scoped-scale-20260925-v1",
               "claim_boundary": "disconnected task frames on one conversation deliberation rule path; not cross-frame conversation prevalence",
               "locked_inputs": locked, "lock_sha256": sha(LOCK),
               "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
               "configuration": {"sizes": SIZES, "replicates": REPLICATES, "arms": ARMS},
               "checks": checks, "summaries": summaries, "paired": pairs, "runs": records}
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks,
                      "summaries": summaries}, indent=2))
    if not all(checks.values()):
        raise SystemExit("conversation frame-scoped scale gate failed; preserve raw data")


if __name__ == "__main__":
    main()
