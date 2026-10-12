#!/usr/bin/env python3
"""Analyze selected-area response and full residual continuation."""
from __future__ import annotations
import gzip,hashlib,json,statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CAPTURE=ROOT/"evaluation/reports/response_priority_residual_continuation_v1_2_confirmatory_20261006/capture.json.gz"
LOCK=ROOT/"evaluation/substrate_capability/response_priority_residual_continuation_v1_2_confirmatory_20261006_lock.json"
OUT=ROOT/"evaluation/reports/response_priority_residual_continuation_v1_2_confirmatory_analysis_20261006.json"
ANALYZER=Path(__file__).resolve()

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canonical(value): return json.dumps(value,sort_keys=True,separators=(",",":"),default=str)
def semantic_outcome(row):
    def clean(value):
        if isinstance(value,dict):
            return {k:clean(v) for k,v in value.items() if k!="id" and not k.endswith("_id") and not k.endswith("_ids")}
        if isinstance(value,list): return [clean(v) for v in value]
        return value
    return clean({k:row.get(k) for k in ("reply","expected_topic","expected_path","message","comprehension","goals","evidence","receipts","held_answers","reply_messages")})

raw=CAPTURE.read_bytes();capture=json.loads(gzip.decompress(raw));runs=capture["runs"]
checks={
 "six_workers":len(runs)==6,
 "three_workers_per_arm":all(sum(r["arm"]==a for r in runs)==3 for a in ("global","priority")),
 "distinct_pids":len({r["pid"] for r in runs})==6,
 "source_lock_matches":json.loads(LOCK.read_text())==capture["locked_inputs"],
 "source_stable":capture["post_run_inputs"]==capture["locked_inputs"] and all(r["worker_source_stable"] for r in runs),
 "fixed_hash_seed":all(r["environment"].get("PYTHONHASHSEED")=="0" for r in runs),
 "seven_turns_each":all(len(r["turns"])==7 for r in runs),
 "priority_area_partition":all(set(r["area_assignments"].values())=={"response_critical","ambient_work"} and
     all(r["area_assignments"].get(n)=="ambient_work" for n in capture["locked_inputs"]["design"]["ambient_rules"]) for r in runs if r["arm"]=="priority"),
}
per_turn=[]
for ti in range(7):
    arm_rows={a:[r["turns"][ti] for r in runs if r["arm"]==a] for a in ("global","priority")}
    reference=arm_rows["global"][0]
    global_out=[canonical(semantic_outcome(row)) for row in arm_rows["global"]]
    priority_out=[canonical(semantic_outcome(row)) for row in arm_rows["priority"]]
    global_graph=[row["response_priority"]["post_continuation_semantic_sha256"] for row in arm_rows["global"]]
    priority_graph=[row["response_priority"]["post_continuation_semantic_sha256"] for row in arm_rows["priority"]]
    checks[f"global_worker_outcome_repeat__{ti}"]=len(set(global_out))==1
    checks[f"priority_worker_outcome_repeat__{ti}"]=len(set(priority_out))==1
    checks[f"reply_semantic_parity__{ti}"]=set(global_out)==set(priority_out)
    checks[f"global_worker_continuation_repeat__{ti}"]=len(set(global_graph))==1
    checks[f"priority_worker_continuation_repeat__{ti}"]=len(set(priority_graph))==1
    checks[f"post_continuation_graph_parity__{ti}"]=set(global_graph)==set(priority_graph)
    checks[f"post_continuation_cardinality_parity__{ti}"]=len({(r["response_priority"]["post_continuation_node_count"],r["response_priority"]["post_continuation_edge_count"]) for a in arm_rows.values() for r in a})==1
    checks[f"all_continuations_converge__{ti}"]=all(not r["response_priority"]["continuation_hit_max_rounds"] and not r["response_priority"]["continuation_residual_by_area"] for a in arm_rows.values() for r in a)
    priority_calls=[call for row in arm_rows["priority"] for call in row["response_priority"]["selected_calls"]]
    checks[f"selected_calls_restrict_to_priority__{ti}"]=all(
       set(call["requested_areas"])=={"response_critical","global"} and
       set(call["selected_areas"]).issubset({"response_critical","global"}) and
       all(x["area"] in {"response_critical","global"} for rnd in call["round_rows"] for x in rnd["rows"])
       for call in priority_calls)
    pre_residual=[sum(item["residual"] for call in row["response_priority"]["selected_calls"][-1:] for item in call["residual_by_area"] if item["area"]=="ambient_work") for row in arm_rows["priority"]]
    per_turn.append({"turn_index":ti,"prompt":reference.get("prompt"),
      "reply":reference.get("reply"),"reply_parity":checks[f"reply_semantic_parity__{ti}"],
      "post_continuation_graph_parity":checks[f"post_continuation_graph_parity__{ti}"],
      "post_continuation_counts":[[r["response_priority"]["post_continuation_node_count"],r["response_priority"]["post_continuation_edge_count"]] for a in arm_rows.values() for r in a],
      "priority_pre_continuation_ambient_residual_by_worker":pre_residual,
      "priority_response_elapsed_ns":[r["response_priority"]["response_elapsed_ns"] for r in arm_rows["priority"]],
      "global_response_elapsed_ns":[r["response_priority"]["response_elapsed_ns"] for r in arm_rows["global"]],
      "priority_continuation_elapsed_ns":[r["response_priority"]["continuation_elapsed_ns"] for r in arm_rows["priority"]],
      "priority_continuation_steps":[r["response_priority"]["continuation_steps"] for r in arm_rows["priority"]]})

priority_times=[r["response_priority"]["response_elapsed_ns"] for run in runs if run["arm"]=="priority" for r in run["turns"]]
global_times=[r["response_priority"]["response_elapsed_ns"] for run in runs if run["arm"]=="global" for r in run["turns"]]
continuation_times=[r["response_priority"]["continuation_elapsed_ns"] for run in runs if run["arm"]=="priority" for r in run["turns"]]
failed=[k for k,v in checks.items() if not v]
analysis={"schema_version":1,"capture_path":str(CAPTURE.relative_to(ROOT)),"capture_sha256":hashlib.sha256(raw).hexdigest(),
 "capture_bytes_gzip":CAPTURE.stat().st_size,"lock_sha256":sha(LOCK),"analyzer_sha256":sha(ANALYZER),
 "checks":checks,"capture_integrity_pass":all(checks[k] for k in ("six_workers","three_workers_per_arm","distinct_pids","source_lock_matches","source_stable","fixed_hash_seed","seven_turns_each","priority_area_partition")),
 "reply_and_continuation_parity_pass":all(v for k,v in checks.items() if "parity__" in k or "worker_" in k or "converge" in k or "restrict" in k),
 "all_checks_pass":not failed,"failed_checks":failed,"per_turn":per_turn,
 "response_time_ns":{"global_median":statistics.median(global_times),"priority_median":statistics.median(priority_times),
    "priority_continuation_median":statistics.median(continuation_times)},
 "interpretation":"Response and continuation costs are measured separately on one held-topic family. Timing is descriptive and does not establish a broad speed advantage or natural-task prevalence."}
OUT.write_text(json.dumps(analysis,indent=2,sort_keys=True)+"\n")
print(json.dumps({"analysis":str(OUT.relative_to(ROOT)),"capture_integrity_pass":analysis["capture_integrity_pass"],
 "reply_and_continuation_parity_pass":analysis["reply_and_continuation_parity_pass"],"all_checks_pass":analysis["all_checks_pass"],"failed_checks":failed},indent=2))
