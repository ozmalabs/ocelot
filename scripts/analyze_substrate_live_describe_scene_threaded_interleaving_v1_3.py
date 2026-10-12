#!/usr/bin/env python3
"""Independent checks for the serialized threaded describe-scene capture."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_live_describe_scene_threaded_interleaving_v1_3_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/live_describe_scene_threaded_interleaving_v1_3_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_live_describe_scene_threaded_interleaving_v1_3_analysis_20260926.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());locked=json.loads(LOCK.read_text())["locked_inputs"];runs=raw["runs"]
 work_profiles=[];per_kind=[]
 for run in runs:
  profile=[];totals={"candidate_pairs":0,"term_evaluations":0,"elapsed_ns":0};kind_counts={}
  for row in run.get("producer_work",[]):
   c=row["counters"]["scale"];pr={}
   for _,metric,value in row["counters"]["per_rule"]:pr[metric]=pr.get(metric,0)+value
   profile.append((row["thread"],row["kind"],c.get("cand_enum",0),c.get("term_evals_total",0)))
   totals["candidate_pairs"]+=c.get("cand_enum",0);totals["term_evaluations"]+=c.get("term_evals_total",0);totals["elapsed_ns"]+=row["elapsed_ns"]
   kind_counts.setdefault(row["kind"],{"calls":0,"candidate_pairs":0,"term_evaluations":0,"elapsed_ns":[]})
   k=kind_counts[row["kind"]];k["calls"]+=1;k["candidate_pairs"]+=c.get("cand_enum",0);k["term_evaluations"]+=c.get("term_evals_total",0);k["elapsed_ns"].append(row["elapsed_ns"])
   profile[-1]=profile[-1]+(c.get("cand_enum",0)==pr.get("candidate_pairs",0),c.get("term_evals_total",0)==pr.get("term_evaluations",0),c.get("term_evals_total",0)==sum(v for key,v in c.items() if key.startswith("term_eval:")))
  work_profiles.append(profile);per_kind.append({"replicate":run["replicate"],"totals":totals,"by_event_kind":kind_counts})
 checks={"raw_digest_matches_lock":raw["lock_sha256"]==sha(LOCK),"raw_inputs_match_lock":raw["locked_inputs"]==locked,
  "three_distinct_workers":len(runs)==3 and len({r["pid"] for r in runs})==3,
  "source_stable_workers_and_postrun":raw["post_run_inputs"]==locked and all(r["worker_started_inputs"]==locked and r["worker_finished_inputs"]==locked for r in runs),
  "lock_blocks_B_while_A_is_paused":all(r["b_was_serialized"] and r["pause_gate"] for r in runs),
  "sequential_lifecycle_ownership":all(r["event_order_gate"] and r["identity_gate"] and r["lifecycle_gate"] for r in runs),
  "both_baseline_replies_and_joined_threads":all(r["reply_parity"] and r["threads_joined"] and not r["errors"] for r in runs),
  "normalized_shape_repeats":len({json.dumps({k:r[k] for k in ("event_order_gate","identity_gate","lifecycle_gate","pause_gate","reply_parity")},sort_keys=True) for r in runs})==1,
  "six_producer_calls_each":all(len(r.get("producer_work",[]))==6 for r in runs),
  "producer_counter_conservation":all(all(row[4:]) for profile in work_profiles for row in profile),
  "producer_work_replicates_exactly":len({json.dumps(p,sort_keys=True) for p in work_profiles})==1}
 producer_summary={}
 for kind in ("selection","execution","action_result"):
  rows=[row for arm in per_kind for row in arm["by_event_kind"][kind]["elapsed_ns"]]
  item=per_kind[0]["by_event_kind"][kind]
  producer_summary[kind]={"calls_per_run":item["calls"],"candidate_pairs_per_run":item["candidate_pairs"],"term_evaluations_per_run":item["term_evaluations"],"elapsed_ns_median":sorted(rows)[len(rows)//2],"elapsed_ns_range":[min(rows),max(rows)]}
 out={"schema_version":1,"raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"checks":checks,
  "producer_work_profiles":per_kind,"producer_work_summary":producer_summary,
  "finding":"With the WorldAdapter per-instance RLock, B waits while A is paused after selection. The three source-locked workers preserve identity and lifecycle semantics, and the six calls to the production lifecycle event helper have exactly replicated candidate/Term counts with per-rule counter conservation.",
  "limits":"This is one controlled describe_scene schedule and one adapter entry point. It does not establish safety for arbitrary adapter/native concurrency, other routes, or workload prevalence. Helper elapsed time includes event preparation and native closure, and no unlocked counterfactual is measured."}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks},indent=2))
 if not all(checks.values()):raise SystemExit("serialized threaded capture analysis failed")
if __name__=="__main__":main()
