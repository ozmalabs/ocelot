#!/usr/bin/env python3
"""Independent scoped-pending/fallback analysis for two deferred queues."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_remaining_deferred_queue_fallback_v1_workers_raw_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_remaining_deferred_queue_fallback_v1_analysis_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/remaining_deferred_queue_fallback_v1_lock_20260926.json"
FAMILIES=("rule_edits","fb_samples")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw["runs"]
 checks={"12_workers_complete_size_replicates":len(runs)==12 and {(r["n"],r["replicate"]) for r in runs}=={(n,rep) for n in (1,2,4,8) for rep in range(3)},"fresh_pid_per_worker":len({r["pid"] for r in runs})==12,"locked_inputs_stable":raw["locked_inputs"]==lock==raw["post_run_inputs"] and all(r["before"]==lock==r["after"] for r in runs)}
 rows=[]
 for r in runs:
  n=r["n"];rep=r["replicate"];arms=r["arms"];full=arms["full"];scoped=arms["scoped_only"];fallback=arms["scoped_fallback"];pre=f"n{n}_r{rep}"
  checks[pre+"_full_fallback_graph_equal"]=full["graph"]==fallback["graph"]
  checks[pre+"_full_and_fallback_outputs"]=full["seen_edges"]==fallback["seen_edges"]==n and full["grid_cells"]==fallback["grid_cells"]==4*n
  checks[pre+"_full_fixedpoint"]=full["phases"]["full"]["report"]["status"]=="fixed_point"
  checks[pre+"_scoped_and_fallback_start_pending"]=scoped["phases"]["scoped"]["report"]["deferred_effects_pending"] and fallback["phases"]["scoped"]["report"]["deferred_effects_pending"]
  checks[pre+"_scoped_only_incomplete"]=scoped["seen_edges"]==0 and scoped["grid_cells"]==0
  for arm_name,arm,phase,enq,drain,batches in (("full",full,"full",n,n,1),("scoped",scoped,"scoped",n,0,0),("fallback_scoped",fallback,"scoped",n,0,0),("fallback_global",fallback,"fallback",0,n,1)):
   audit=arm["phases"][phase]["audit"];g=audit["global"]
   for family in FAMILIES:
    checks[f"{pre}_{arm_name}_{family}_queue_counts"]=(g.get(f"deferred_queue:{family}:enqueued_items",0)==enq and g.get(f"deferred_queue:{family}:drained_items",0)==drain and g.get(f"deferred_queue:{family}:drain_batches",0)==batches)
   if arm_name in ("scoped","fallback_scoped"):
    writer_ids={int(x["rule_index"]) for x in arm["writers"]}
    for family in FAMILIES:
     metric=f"deferred_queue_enqueued:{family}";found={int(i):int(v) for i,name,v in audit["per_rule"] if name==metric and int(i) in writer_ids}
     checks[f"{pre}_{arm_name}_{family}_writer_attribution"]=found=={i:1 for i in writer_ids}
   rows.append({"n":n,"replicate":rep,"arm":arm_name,"phase":phase,"enqueued":enq,"drained":drain,"batches":batches})
 payload={"schema_version":1,"raw_sha256":sha(RAW),"analysis_sha256":sha(Path(__file__).resolve()),"checks":checks,"all_checks_pass":all(checks.values()),"checks_passed":sum(checks.values()),"checks_total":len(checks),"rows":rows,"claim_boundary":"For two deferred queue families only, a synthetic scoped run retains records and global fallback drains them to exact full-closure state. Not a general scoped scheduler correctness or natural-locality result."}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":payload["all_checks_pass"],"checks_passed":payload["checks_passed"],"checks_total":payload["checks_total"]},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
