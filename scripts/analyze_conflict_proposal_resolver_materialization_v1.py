#!/usr/bin/env python3
"""Compare staged resolver gates/work against immutable lifecycle scale v1.2."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/"evaluation/reports/conflict_proposal_resolver_materialization_v1_20260928.json";BASE=ROOT/"evaluation/reports/conflict_proposal_lifecycle_scale_v1_2_20260928.json";OUT=ROOT/"evaluation/reports/conflict_proposal_resolver_materialization_v1_analysis_20260928.json";SIZES=(2,4,8,16,32,64)
def main():
 d=json.loads(RAW.read_text());base=json.loads(BASE.read_text());runs=d["runs"];g={"three_workers":len(runs)==3,"same_locked_engine":all(r["started_inputs"]["native_extension_sha256"]==base["locked_inputs"]["native_extension_sha256"] and r["started_inputs"]["native_build_manifest_sha256"]==base["locked_inputs"]["native_build_manifest_sha256"] for r in runs),"12_cells_each":all(len(r["cells"])==12 for r in runs)};normalized=[]
 for r in runs:
  cs=[]
  for c in r["cells"]:
   n=c["n"];dist=c["distribution"];p=f"{r['worker_id']}_{n}_{dist}";gen=c["generation"];rep=c["repeat"];res=c["resolution"]
   g[p+"_proposal_invariants"]=(gen["report"]["status"]=="fixed_point" and c["proposal_labels"]==[f"p{i:03d}" for i in range(n)] and c["proposal_edge_count"]==n)
   g[p+"_idempotent"]=(rep["report"]["status"]=="fixed_point" and rep["report"]["progress_steps"]==0 and rep["metrics"].get("graph_writes",0)==0)
   if dist=="unique_max":g[p+"_unique_semantics"]=(res["report"]["status"]=="fixed_point" and res["selected"]==f"p{n-1:03d}" and res["ambiguous"] is None and res["top_count"]==1)
   else:g[p+"_tie_semantics"]=(res["report"]["status"]=="fixed_point" and res["selected"] is None and res["ambiguous"] is True and res["top_count"]==2)
   old=next(x for x in base["runs"][0]["cells"] if x["n"]==n and x["distribution"]==dist)
   m={k:v for k,v in res["metrics"].items() if not k.endswith("_ns")};terms=m.get("term_evals_total",0);oldterms=next(x for x in json.loads((ROOT/"evaluation/reports/conflict_proposal_lifecycle_scale_v1_2_analysis_20260928.json").read_text())["cells_by_worker"][0] if x["n"]==n and x["distribution"]==dist)["term_evaluations"]
   g[p+"_fewer_term_evaluations"]=(terms<oldterms)
   cs.append({"n":n,"distribution":dist,"term_evaluations":terms,"baseline_term_evaluations":oldterms,"term_reduction":oldterms-terms,"candidate_tests":m.get("cand_tested",0),"maxover_evaluations":m.get("term_eval:MaxOver",0),"count_evaluations":m.get("term_eval:Count",0),"selected":res["selected"],"ambiguous":res["ambiguous"],"top_count":res["top_count"],"integer_metrics":m,"elapsed_ns":{"generation":gen["elapsed_ns"],"repeat":rep["elapsed_ns"],"resolution":res["elapsed_ns"]}})
  normalized.append(cs)
 sig=lambda row:[{k:v for k,v in c.items() if k!="elapsed_ns"} for c in row]
 g["integer_work_counts_replicate"]=sig(normalized[0])==sig(normalized[1])==sig(normalized[2])
 summary=[]
 for n in SIZES:
  u=next(x for x in normalized[0] if x["n"]==n and x["distribution"]=="unique_max");t=next(x for x in normalized[0] if x["n"]==n and x["distribution"]=="tied_max")
  summary.append({"n":n,"unique_term_evals":u["term_evaluations"],"unique_baseline":u["baseline_term_evaluations"],"unique_reduction":u["term_reduction"],"tie_term_evals":t["term_evaluations"],"tie_baseline":t["baseline_term_evaluations"],"tie_reduction":t["term_reduction"],"unique_maxover_evals":u["maxover_evaluations"],"unique_count_evals":u["count_evaluations"],"tie_maxover_evals":t["maxover_evaluations"],"tie_count_evals":t["count_evaluations"]})
 report={"analysis":"Materialized proposal resolver comparison v1","all_gates_pass":all(g.values()),"gates":g,"scale_summary":summary,"cells_by_worker":normalized,"interpretation":"For this fixture the staged resolver computes MaxOver and the tie count once per target, marks top proposals, then selects only a unique top. Work reduction is measured against the immutable v1.2 nested resolver raw capture on the same native extension/build.","limits":["One authored proposal family and N through 64; no asymptotic theorem.","No proposal-set mutation after the cached result, production integration, natural tie prevalence, or learned proposal quality is measured.","The experiment compares operation counts, not uninstrumented latency or memory."]}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_gates_pass":report["all_gates_pass"],"failed":[k for k,v in g.items() if not v],"summary":summary,"analysis":str(OUT.relative_to(ROOT))},indent=2))
 if not report["all_gates_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
