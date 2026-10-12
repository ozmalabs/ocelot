#!/usr/bin/env python3
"""Independent selection, integrity, and rung-entry analysis."""
from __future__ import annotations
import collections, hashlib, json, math, re, statistics, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRAME = ROOT / "evaluation/reports/naturalproofs_rung_stream_frame_v1_20260927.json"
RAW = ROOT / "evaluation/reports/naturalproofs_rung_entry_panel_v1_20260927.json"
DATA = ROOT / "data/naturalproofs"
DOMAIN = b"ocelot-rung-stream-naturalproofs-test-v1\0"

def norm(title): return re.sub(r"\s+", " ", str(title or "").replace("_", " ").strip().lower())
def quantile(values, q):
    xs = sorted(values)
    if not xs: return None
    return xs[min(len(xs)-1, max(0, math.ceil(len(xs)*q)-1))]

def recompute_frame():
    shards = {}
    for split in ("train", "valid", "test"):
        path = next(iter(sorted((DATA / split).glob("*.jsonl"))))
        shards[split] = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    seen = {norm(row.get("title")) for split in ("train", "valid") for row in shards[split]}
    candidates = []
    for line, row in enumerate(shards["test"], 1):
        if not row.get("title") or not row.get("text", "").strip() or not row.get("target", "").strip(): continue
        if norm(row["title"]) in seen: continue
        identity = json.dumps(row.get("id"), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        rank = hashlib.sha256(DOMAIN + identity.encode()).hexdigest()
        candidates.append((rank, str(row.get("id")), row, line))
    candidates.sort(key=lambda x: (x[0], x[1]))
    return shards, candidates

def analyze(raw, frame):
    shards, candidates = recompute_frame()
    expected = candidates[:64]
    expected_ids = [x[2].get("id") for x in expected]
    expected_hashes = [hashlib.sha256(x[2]["text"].encode()).hexdigest() for x in expected]
    checks = {"eligible_test_count_1135": len(candidates) == 1135,
              "test_shard_record_count": len(shards["test"]) == 1135,
              "title_disjoint_test_train_valid": not any(norm(row.get("title")) in
                   {norm(r.get("title")) for split in ("train", "valid") for r in shards[split]}
                   for row in shards["test"]),
              "frame_matches_independent_hash_selection": [x.get("id") for x in frame.get("selected", [])] == expected_ids and
                   [x.get("statement_sha256") for x in frame.get("selected", [])] == expected_hashes}
    runs = raw.get("runs", [])
    checks["two_workers"] = len(runs) == 2 and len({r.get("pid") for r in runs}) == 2
    checks["all_workers_64_rows"] = all(len(r.get("tasks", [])) == 64 for r in runs)
    checks["worker_source_stability"] = all(r.get("source_stable") and
        r.get("locked_inputs_before") == raw.get("locked_inputs") == r.get("locked_inputs_after") for r in runs)
    checks["parent_lock_stability"] = raw.get("locked_inputs") == raw.get("post_run_inputs")
    checks["worker_process_success"] = all(r.get("worker_returncode") == 0 and r.get("boot", {}).get("loaded", 0) > 0 for r in runs)
    checks["all_task_hashes_match"] = all(
        [t.get("sample_id") for t in r.get("tasks", [])] == expected_ids and
        [t.get("statement_sha256_observed") for t in r.get("tasks", [])] == expected_hashes and
        [t.get("statement_sha256_expected") for t in r.get("tasks", [])] == expected_hashes
        for r in runs)
    worker_summaries = []
    for run in runs:
        tasks = run.get("tasks", [])
        statuses, linked_statuses = {}, {}
        entry_all = [t for t in tasks if t.get("receipt_delta", 0) > 0]
        entry_post = [t for t in tasks[1:] if t.get("receipt_delta", 0) > 0]
        cold = tasks[0] if tasks else {}
        cold_keys = [o.get("key") for o in cold.get("new_observations", [])]
        cold_setup = len(cold_keys) == 1 and cold_keys[0] == ["conceptualizer_live"]
        ambiguous = 0
        for t in tasks:
            for obs in t.get("new_observations", []):
                st = obs.get("status") or "missing"
                statuses[st] = statuses.get(st, 0) + 1
            if t.get("receipt_delta") == 1 and len(t.get("new_observations", [])) == 1:
                obs = t["new_observations"][0]
                st = obs.get("status") or "missing"
                linked_statuses[st] = linked_statuses.get(st, 0) + 1
            elif t.get("receipt_delta", 0) or t.get("new_observations"):
                ambiguous += 1
        checks[f"worker{run.get('replicate')}_first_use_separate"] = cold_setup and not any(
            any(o.get("key") == ["conceptualizer_live"] for o in t.get("new_observations", []))
            for t in tasks[1:])
        checks[f"worker{run.get('replicate')}_no_task_text_or_proof_in_raw"] = all(
            "statement" not in t and "proof" not in t
            for t in tasks)
        wall = [int(t.get("task_wall_ns", 0)) for t in tasks]
        cpu = [int(t.get("task_cpu_ns", 0)) for t in tasks]
        all_axes = [axis for t in tasks for axis in t.get("new_capability_axes", [])]
        linked_axis_ids = {axis_id for t in tasks for obs in t.get("new_observations", [])
                           for axis_id in obs.get("minted_axis_ids", [])}
        linked_mints = [axis for axis in all_axes if axis.get("id") in linked_axis_ids]
        induced_marked = [axis for axis in all_axes if axis.get("induced")]
        kinds = collections.Counter(str(axis.get("kind") or "missing") for axis in all_axes)
        token_hashes = {axis.get("word_sha256") for axis in all_axes if axis.get("word_sha256")}
        worker_summaries.append({
            "replicate": run.get("replicate"), "task_count": len(tasks),
            "all_task_entry_count": len(entry_all), "all_task_entry_rate": len(entry_all) / len(tasks) if tasks else None,
            "post_cold_entry_count": len(entry_post), "post_cold_denominator": max(0, len(tasks)-1),
            "post_cold_entry_rate": len(entry_post) / (len(tasks)-1) if len(tasks) > 1 else None,
            "cold_task_receipt_count": cold.get("receipt_delta"), "cold_task_observation_keys": cold_keys,
            "new_observation_statuses": statuses, "unambiguously_linked_observation_statuses": linked_statuses,
            "ambiguous_receipt_observation_task_intervals": ambiguous,
            "capability_axis_type_nodes_added": len(all_axes),
            "observation_minted_edge_axis_count": len(linked_axis_ids),
            "observation_linked_new_axis_count": len(linked_mints),
            "new_axes_induced_marker_count": len(induced_marked),
            "unclassified_capability_axis_type_growth": sum(1 for axis in all_axes
                if axis.get("id") not in linked_axis_ids and not axis.get("induced")),
            "capability_axis_type_nodes_by_kind": dict(kinds),
            "understand_word_frontier_count": kinds.get("understand_word", 0),
            "distinct_understand_word_token_hashes": len({axis.get("word_sha256") for axis in all_axes
                if axis.get("kind") == "understand_word" and axis.get("word_sha256")}),
            "distinct_token_hashes_all_kinds": len(token_hashes),
            "new_shape_signature_count": sum(len(t.get("new_shape_signatures", [])) for t in tasks),
            "transforms_total": sum(len(t.get("new_transforms", [])) for t in tasks),
            "task_errors": sum(t.get("error") is not None for t in tasks),
            "tasks_without_reply": sum(not t.get("reply_present") for t in tasks),
            "task_wall_ns_median": statistics.median(wall) if wall else None,
            "task_wall_ns_p95_nearest_rank": quantile(wall, .95),
            "task_cpu_ns_median": statistics.median(cpu) if cpu else None,
            "boot_wall_ns": run.get("boot", {}).get("wall_ns"),
            "peak_rss_bytes": run.get("runtime", {}).get("peak_rss_bytes"),
        })
    checks["worker_schedule_parity"] = len(runs) == 2 and (
        [(t.get("sample_id"), t.get("receipt_delta"), t.get("new_observations"),
          len(t.get("new_induced_axes", [])), len(t.get("new_shape_signatures", [])),
          len(t.get("new_transforms", []))) for t in runs[0].get("tasks", [])] ==
        [(t.get("sample_id"), t.get("receipt_delta"), t.get("new_observations"),
          len(t.get("new_induced_axes", [])), len(t.get("new_shape_signatures", [])),
          len(t.get("new_transforms", []))) for t in runs[1].get("tasks", [])])
    return {"checks": checks, "pass": all(checks.values()),
            "summary": {"selected_records": len(expected), "workers": worker_summaries,
                        "claim_boundary": "Reading-path receipt incidence on this selected statement stream and runtime profile only; no proof accuracy or broad prevalence."}}

if __name__ == "__main__":
    frame = json.loads(FRAME.read_text())
    raw = json.loads(Path(sys.argv[1]).read_text()) if len(sys.argv) > 1 else json.loads(RAW.read_text())
    result = analyze(raw, frame)
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["pass"]: raise SystemExit(1)
