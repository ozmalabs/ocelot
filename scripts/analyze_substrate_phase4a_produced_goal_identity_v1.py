#!/usr/bin/env python3
"""Independent validation of the Phase 4A produced-identity capture."""
from __future__ import annotations
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_phase4a_produced_goal_identity_v1_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/phase4a_produced_goal_identity_lock_20260926.json"
DIAG=ROOT/"evaluation/reports/phase4a_goal_identity_graph_diff_diagnostic_20260926.json"
FIXTURE_SIZES=(2,4,8); ARMS=("full","scoped")
OUT=ROOT/"evaluation/reports/substrate_phase4a_produced_goal_identity_v1_analysis_20260926.json"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());diag=json.loads(DIAG.read_text());runs=raw["runs"]
 cells={(int(r["size"]),int(r["replicate"]),r["arm"]):r for r in runs};gates={};summary={}
 for n in FIXTURE_SIZES:
  gates[str(n)]={}
  for rep in range(3):
   f=cells[n,rep,"full"];s=cells[n,rep,"scoped"]
   def identity_ok(run):
    rows=run["projection"]
    return len(rows)==n and all(row["task"]==i and row["goal_status"]=="active"
     and row["deliberation_status"]=="resolved" and row["selection"]==[f"has_goal_evidence:answer_{i}"]
     and row["execution_traces_for_goal"]==[{"candidate":f"has_goal_evidence:answer_{i}","status":"resolved"}]
     and row["settlements"]==[{"candidate":f"has_goal_evidence:answer_{i}","goal_link":True}]
     and row["source_link"] for i,row in enumerate(rows))
   gates[str(n)][str(rep)]={"both_fixed_and_uncapped":f["complete"] and s["complete"]
     and all(not r.get("hit_progress_budget",False) and not r.get("deferred_effects_pending",False) for x in (f,s) for r in x["reports"]),
    "full_and_scoped_identity_oracles":identity_ok(f) and identity_ok(s),
    "producer_provenance_each_arm":f["source_provenance_all_tasks"] and s["source_provenance_all_tasks"],
    "normalized_projection_parity":f["projection"]==s["projection"]}
  summary[str(n)]={}
  for arm in ARMS:
   rows=[]
   for rep in range(3):
    r=cells[n,rep,arm];c=r["counters"]
    rows.append({"replicate":rep,"candidate_pairs":int(c.get("cand_tested",0)),"term_evaluations":int(c.get("term_evals_total",0)),
      "wall_ns":int(r["wall_ns"]),"cpu_ns":int(r["cpu_ns"]),"construction_ns":int(r["construction_ns"]),
      "scoped_turns":int(r["turns"]),"peak_rss_kib":int(r["peak_rss_kib"])})
   summary[str(n)][arm]={"per_replicate":rows}
   for key in rows[0]:
    if key=="replicate":continue
    vals=[r[key] for r in rows];summary[str(n)][arm][key+"_median"]=statistics.median(vals);summary[str(n)][arm][key+"_range"]=[min(vals),max(vals)]
  summary[str(n)]["scoped_over_full_ratios"]={k:summary[str(n)]["scoped"][k+"_median"]/max(1,summary[str(n)]["full"][k+"_median"])
    for k in ("candidate_pairs","term_evaluations","wall_ns")}
 checks={"runner_checks_pass":all(raw["checks"].values()),"locked_inputs_match":raw["locked_inputs"]==lock["locked_inputs"] and raw["lock_sha256"]==sha(LOCK),
  "18_distinct_worker_pids":len(runs)==18 and len({r["pid"] for r in runs})==18,
  "complete_18_cell_matrix":len(cells)==18 and all((n,r,a) in cells for n in FIXTURE_SIZES for r in range(3) for a in ARMS),
  "all_independent_identity_and_parity_gates":all(all(x.values()) for nr in gates.values() for x in nr.values()),
  "n2_graph_isomorphism_diagnostic_passes":all(diag["comparison"][k] for k in ("node_descriptor_multisets_equal","all_nodes_mapped","typed_edges_equal_after_descriptor_mapping","normalized_task_projection_equal")),
  "counter_summary_reconstruction":all(summary[str(n)][arm]["candidate_pairs_median"]==raw["summary"][str(n)][arm]["candidate_pairs_median"]
    and summary[str(n)][arm]["term_evaluations_median"]==raw["summary"][str(n)][arm]["term_evaluations_median"]
    for n in FIXTURE_SIZES for arm in ARMS)}
 result={"schema_version":1,"run_id":"substrate-phase4a-produced-goal-identity-v1-analysis-20260926",
  "raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"graph_diagnostic_sha256":sha(DIAG),"checks":checks,"replicate_gates":gates,"summary":summary,
  "claim_boundary":raw["claim_boundary"],"interpretation":"Phase 4A's production materializer and native for_goal trace producer preserve per-task identity under full and scoped closure in this generated workload. Scoped execution repeats rules substantially more than full closure. Raw whole-graph digests differ; a follow-up N=2 descriptor mapping shows exact typed-edge isomorphism for one pair, but this check is not yet repeated across the full scale matrix. The runner-authored partition and evidence do not establish natural frame locality."}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks,"summary":summary},indent=2))
 if not all(checks.values()):raise SystemExit("independent Phase 4A identity reconstruction failed")
if __name__=="__main__":main()
