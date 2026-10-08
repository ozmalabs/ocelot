#!/usr/bin/env python3
"""Independent validation and scaling summary for the event-reasoning envelope."""
from __future__ import annotations
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_event_reasoning_stage_a_envelope_v1_1_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_event_reasoning_stage_a_envelope_v1_1_analysis_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/event_reasoning_stage_a_envelope_v1_1_lock_20260926.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def graph_oracle(g,n):
 entities=[x for x in g["nodes"] if x["type"]=="Entity"]
 expected=("on_floor","on_floor_inferred","broken","broken_inferred","worthless","worthless_inferred")
 eids={x["id"] for x in entities}
 edges=[e for e in g["edges"] if e["type"]=="is_entity"]
 return len(entities)==n and len(edges)==n and all(e["src"]==e["tgt"] and e["src"] in eids for e in edges) and all(all(x["attrs"].get(k)==1 for k in expected) and x["attrs"].get("fell")==1 and x["attrs"].get("fragile")==1 for x in entities)
def main():
 p=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());cells=p["cells"];workers=p["worker_processes"]
 orders={tuple(c["arm_order"]) for c in cells if c["size"]==1}
 manifest=p["run_manifest"];log=manifest.get("stdout_stderr_capture") or {};log_path=ROOT/log.get("path","__missing__");streams=p.get("worker_streams",[])
 def worker_payload(rep):
  w=next(w for w in workers if w["replicate"]==rep)
  return {**w,"cells":[c for c in cells if c["replicate"]==rep]}
 children_ok=len(streams)==6 and all(x["stdout_sha256"]==hashlib.sha256((json.dumps(worker_payload(x["replicate"]),sort_keys=True)+"\n").encode()).hexdigest() and x["stderr_bytes"]==0 and x["stderr_sha256"]==hashlib.sha256(b"").hexdigest() for x in streams)
 checks={"schema_and_cell_count":p.get("schema_version")==1 and len(cells)==30,"source_lock_and_capture_hash":p["locked_inputs"]==lock["locked_inputs"] and p["lock_sha256"]==sha(LOCK) and p["post_run_inputs"]==p["locked_inputs"],"shared_manifest_valid":manifest.get("manifest_schema")=="substrate-run-manifest-v1" and manifest.get("exit_status")==0 and manifest.get("engine",{}).get("build_is_stale") is False and all(v.get("exists") and sha(ROOT/name)==v.get("sha256") for name,v in manifest.get("explicit_inputs",{}).items()),"parent_log_hash_valid":log_path.is_file() and sha(log_path)==log.get("sha256") and log_path.stat().st_size==log.get("bytes",-1),"child_process_logs_valid":children_ok,"six_distinct_fresh_workers":len(workers)==6 and len({x["pid"] for x in workers})==6,"source_stability_inside_workers":all(w["started_inputs"]==p["locked_inputs"]==w["finished_inputs"] for w in workers) and all(a["inputs_start"]==p["locked_inputs"]==a["inputs_end"] for c in cells for a in (c["ordinary"],c["compare_only"],c["stage_a_enabled"])),"complete_size_replication":all(sum(c["size"]==n for c in cells)==6 for n in (1,4,16,64,256)),"six_arm_orders_counterbalanced":len(orders)==6,"independent_graph_oracle_all_arms":all(graph_oracle(c[a]["graph"],c["size"]) for c in cells for a in ("ordinary","compare_only","stage_a_enabled")),"exact_ordinary_enabled_parity":all(c["exact_graph_parity"] and c["progress_parity"] for c in cells),"eligibility_and_fallback_counts_reconcile":all(c["eligible_drain_count"]==3 and c["excluded_drain_count"]==0 and c["fallback_count"]==0 and c["eligible_drain_share"]==1.0 and c["fallback_rate"]==0.0 and c["compare_only"]["stage_a_compare_stats"]["diverged_drains"]==0 and c["compare_only"]["stage_a_compare_stats"]["unsound_drains"]==0 for c in cells),"proposal_count_scales_with_entities":all(c["stage_a_enabled"]["stage_a_stats"]["proposals"]==3*c["size"] for c in cells),"terminal_and_budget_status":all(x["terminal_probe"]==0 and x["progress"]<1000 for c in cells for x in (c["ordinary"],c["compare_only"],c["stage_a_enabled"]))}
 summary=[]
 for n in (1,4,16,64,256):
  cs=[c for c in cells if c["size"]==n]
  base=statistics.median(c["ordinary"]["wall_time_ns"] for c in cs);stage=statistics.median(c["stage_a_enabled"]["wall_time_ns"] for c in cs)
  summary.append({"entities":n,"replicates":len(cs),"compared_drains":sum(c["eligible_drain_count"] for c in cs),"stage_a_proposals":sum(c["stage_a_enabled"]["stage_a_stats"]["proposals"] for c in cs),"fallbacks":sum(c["fallback_count"] for c in cs),"median_ordinary_wall_ns":int(base),"median_stage_a_wall_ns":int(stage),"median_cpu_ns_ordinary":int(statistics.median(c["ordinary"]["cpu_time_ns"] for c in cs)),"median_cpu_ns_stage_a":int(statistics.median(c["stage_a_enabled"]["cpu_time_ns"] for c in cs)),"median_wall_ratio_stage_a_over_ordinary":statistics.median(c["stage_a_enabled"]["wall_time_ns"]/c["ordinary"]["wall_time_ns"] for c in cs)})
 out={"schema_version":1,"raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"checks":checks,"passed":all(checks.values()),"cell_count":len(cells),"summary_by_size":summary,"claim_boundary":p["claim_boundary"]}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,indent=2))
 if not out["passed"]:raise SystemExit("independent analysis failed")
if __name__=="__main__":main()
