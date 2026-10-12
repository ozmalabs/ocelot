#!/usr/bin/env python3
"""Independent checks and cost reconstruction for common-ground identity probe."""
from __future__ import annotations
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_common_ground_task_identity_replication_v1_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/common_ground_task_identity_replication_lock_20260926.json"
FIXTURE=ROOT/"tests/fixtures/conversational_manifold/phase3_common_ground_stress.json"
OUT=ROOT/"evaluation/reports/substrate_common_ground_task_identity_replication_v1_analysis_20260926.json"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());fixture=json.loads(FIXTURE.read_text());runs=raw["runs"]
 by={(x["arm"],int(x["replicate"])):x for x in runs};pair_gates={};summary={}
 expected={"0":[4,5,6],"1":[7,8,9]};wrong={"0":[4,5,6],"1":[4,5,6]}
 for arm in ("temporal","recipient","explicit"):
  pair_gates[arm]={}
  for rep in range(3):
   r=by[(arm,rep)];all_event_frames={cp["event_index"]:cp["frame"] for cp in r["checkpoints"]}
   pair_gates[arm][str(rep)]={"ten_events_and_two_origins":r["event_count"]==10 and r["frame_count"]==2 and r["goal_count"]==2,
    "all_native_closures_fixed":r["all_checkpoints_fixed"] and len(r["checkpoints"])==len(fixture["events"]),
    "common_ground_oracle":r["common_ground_oracle_pass"],
    "identity_edges_match_arm_contract":r["fixture_links_added"]==(6 if arm=="explicit" else 0),
    "temporal_controls_replay_misassociation":r["final_paths"]==wrong if arm in ("temporal","recipient") else True,
    "explicit_replay_matches_task_oracle":r["final_paths"]==expected if arm=="explicit" else True,
    "fixture_frames_align_with_task_sequences":all(all_event_frames[i]==(0 if i<3 else 1) for i in range(10))}
  rows=[]
  for rep in range(3):
   r=by[(arm,rep)];counter={}
   for cp in r["checkpoints"]:
    for k,v in cp["counters"].items():counter[k]=counter.get(k,0)+int(v)
   rows.append({"replicate":rep,"candidate_pairs":counter.get("cand_tested",0),"term_evaluations":counter.get("term_evals_total",0),
    "closure_wall_ns":sum(int(cp["wall_ns"]) for cp in r["checkpoints"]),"construction_ns":r["construction_ns"],"peak_rss_kib":r["peak_rss_kib"],
    "final_paths":r["final_paths"],"final_digest":r["final_digest"]})
  summary[arm]={"per_replicate":rows}
  for k in ("candidate_pairs","term_evaluations","closure_wall_ns","construction_ns","peak_rss_kib"):
   vals=[x[k] for x in rows];summary[arm][k+"_median"]=statistics.median(vals);summary[arm][k+"_range"]=[min(vals),max(vals)]
  summary[arm]["path_counts"]={json.dumps(x["final_paths"],sort_keys=True):sum(y["final_paths"]==x["final_paths"] for y in rows) for x in rows}
 checks={"lock_hash_and_inputs_match":raw["locked_inputs"]==lock["locked_inputs"] and raw["lock_sha256"]==sha(LOCK)
   and raw["locked_inputs"]["fixture_sha256"]==sha(FIXTURE),
  "all_nine_pids_unique":len(runs)==9 and len({r["pid"] for r in runs})==9,
  "complete_3_by_3_matrix":len(by)==9,
  "independent_task_identity_gates_pass":all(all(v.values()) for rows in pair_gates.values() for v in rows.values()),
  "within_arm_graph_digests_reproduce":all(len({by[(arm,r)]["final_digest"] for r in range(3)})==1 for arm in ("temporal","recipient","explicit")),
  "runner_check_reproduction":all(raw["checks"].values()),
  "cost_counts_reconstruct_runner":all(summary[a]["candidate_pairs_median"]==raw["summary"][a]["candidate_pairs_median"] and summary[a]["term_evaluations_median"]==raw["summary"][a]["term_evaluations_median"] for a in summary)}
 result={"schema_version":1,"run_id":"substrate-common-ground-task-identity-replication-v1-analysis-20260926",
  "raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"fixture_sha256":sha(FIXTURE),"checks":checks,"replicate_gates":pair_gates,
  "summary":summary,"claim_boundary":raw["claim_boundary"],
  "interpretation":"On a separately authored two-goal common-ground fixture, current temporal-only and addressee-only controls reproducibly send indices 4/5/6 to both Goals; explicit fixture-supplied for_goal relations separate 4/5/6 from 7/8/9. This does not show the production event producer emits those explicit links or establish prevalence."}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks,"summary":summary},indent=2))
 if not all(checks.values()):raise SystemExit("independent common-ground identity analysis failed")
if __name__=="__main__":main()
