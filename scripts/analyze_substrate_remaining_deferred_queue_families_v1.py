#!/usr/bin/env python3
"""Independent queue conservation and semantic parity analysis."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_remaining_deferred_queue_families_v1_workers_raw_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_remaining_deferred_queue_families_v1_analysis_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/remaining_deferred_queue_families_v1_lock_20260926.json"
FAMILIES=("rule_edits","fb_samples")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw["runs"]
 checks={"12_fresh_workers_cover_sizes_repeats":len(runs)==12 and {(r["n"],r["replicate"]) for r in runs}=={(n,rep) for n in (1,2,4,8) for rep in range(3)},"fresh_pid_each_worker":len({r["pid"] for r in runs})==12,"source_lock_stable":raw["locked_inputs"]==lock==raw["post_run_inputs"] and all(r["before"]==lock==r["after"] for r in runs)}
 for r in runs:
  n=r["n"];rep=r["replicate"];plain=r["plain"];audit=r["audit"];c=audit["counters"];pre=f"n{n}_r{rep}"
  checks[pre+"_audit_on_off_graph_report_parity"]=plain["graph"]==audit["graph"] and plain["report"]==audit["report"]
  checks[pre+"_fixedpoint_and_task_outputs"]=audit["report"]["status"]=="fixed_point" and audit["seen_edges"]==n and audit["grid_cells"]==4*n
  checks[pre+"_queue_items_drained"]=all(c.get(f"deferred_queue:{family}:enqueued_items")==n and c.get(f"deferred_queue:{family}:drained_items")==n for family in FAMILIES)
  checks[pre+"_single_drain_batch_and_timing"]=all(c.get(f"deferred_queue:{family}:drain_batches")==1 and c.get(f"deferred_queue:{family}:drain_ns",-1)>=0 for family in FAMILIES)
  writers={int(x["rule_index"]):x["name"] for x in audit["writers"]}
  for family in FAMILIES:
   metric=f"deferred_queue_enqueued:{family}";rows=[(int(i),name,int(count)) for i,name,count in audit["per_rule"] if name==metric]
   attributed={idx:count for idx,_,count in rows}
   checks[pre+"_"+family+"_producer_attribution"]={idx:attributed.get(idx,0) for idx in writers}=={idx:1 for idx in writers}
 rows=[{"n":r["n"],"replicate":r["replicate"],"queues":{f:{"enqueued":r["audit"]["counters"].get(f"deferred_queue:{f}:enqueued_items"),"drained":r["audit"]["counters"].get(f"deferred_queue:{f}:drained_items"),"batches":r["audit"]["counters"].get(f"deferred_queue:{f}:drain_batches"),"drain_ns":r["audit"]["counters"].get(f"deferred_queue:{f}:drain_ns")} for f in FAMILIES}} for r in runs]
 payload={"schema_version":1,"raw_sha256":sha(RAW),"analysis_sha256":sha(Path(__file__).resolve()),"checks":checks,"all_checks_pass":all(checks.values()),"checks_passed":sum(checks.values()),"checks_total":len(checks),"rows":rows,"claim_boundary":"Two previously unexercised deferred queue families are dynamically exercised and conserved in one authored framebuffer/rule-edit workload, with audit-on/off graph/report parity. No scoped fallback, writer concurrency, natural queue frequency or throughput claim."}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":payload["all_checks_pass"],"checks_passed":payload["checks_passed"],"checks_total":payload["checks_total"]},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
