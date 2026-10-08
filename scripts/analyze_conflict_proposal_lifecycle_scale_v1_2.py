#!/usr/bin/env python3
"""Independent gates and scaling summaries for lifecycle scale v1.2."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/conflict_proposal_lifecycle_scale_v1_2_20260928.json"
OUT=ROOT/"evaluation/reports/conflict_proposal_lifecycle_scale_v1_2_analysis_20260928.json"
SIZES=(2,4,8,16,32,64)
def main():
 d=json.loads(RAW.read_text());runs=d["runs"];g={"three_workers":len(runs)==3,"locked_inputs_match":all(r["started_inputs"]==d["locked_inputs"] for r in runs),"all_cells":all(len(r["cells"])==12 for r in runs)};norm=[]
 for r in runs:
  cells=[]
  for c in r["cells"]:
   n=c["n"];dist=c["distribution"];gen=c["generation"];rep=c["idempotent_resettle"];res=c["resolution"];prefix=f"{r['worker_id']}_{n}_{dist}"
   g[prefix+"_generated_exactly"]=(gen["report"]["status"]=="fixed_point" and c["proposal_labels"]==[f"p{i:03d}" for i in range(n)] and c["proposal_edge_count"]==n)
   g[prefix+"_idempotent"]=(rep["report"]["status"]=="fixed_point" and rep["report"]["progress_steps"]==0 and rep["metrics"].get("graph_writes",0)==0)
   if dist=="unique_max": g[prefix+"_unique_correct"]=(res["report"]["status"]=="fixed_point" and res["selected"]==f"p{n-1:03d}" and res["ambiguous"] is None)
   else: g[prefix+"_tie_explicit"]=(res["report"]["status"]=="fixed_point" and res["ambiguous"] is True and res["selected"] is None)
   metrics={k:v for k,v in res["metrics"].items() if not k.endswith("_ns")}
   cells.append({"n":n,"distribution":dist,"generation_progress":gen["report"]["progress_steps"],"generation_candidate_tests":gen["metrics"].get("cand_tested",0),"idempotent_progress":rep["report"]["progress_steps"],"resolution_status":res["report"]["status"],"selected":res["selected"],"ambiguous":res["ambiguous"],"term_evaluations":metrics.get("term_evals_total",0),"maxover_evaluations":metrics.get("term_eval:MaxOver",0),"candidate_tests":metrics.get("cand_tested",0),"integer_metrics":metrics,"elapsed_ns":{"generation":gen["elapsed_ns"],"repeat":rep["elapsed_ns"],"resolution":res["elapsed_ns"]}})
  norm.append(cells)
 sig=lambda row:[{k:v for k,v in c.items() if k!="elapsed_ns"} for c in row]
 g["integer_work_counts_replicate"]=sig(norm[0])==sig(norm[1])==sig(norm[2])
 summary=[]
 for n in SIZES:
  u=next(c for c in norm[0] if c["n"]==n and c["distribution"]=="unique_max");t=next(c for c in norm[0] if c["n"]==n and c["distribution"]=="tied_max")
  summary.append({"n":n,"generation_progress":u["generation_progress"],"generation_candidate_tests":u["generation_candidate_tests"],"unique_term_evaluations":u["term_evaluations"],"unique_maxover_evaluations":u["maxover_evaluations"],"tie_term_evaluations":t["term_evaluations"],"tie_maxover_evaluations":t["maxover_evaluations"],"tie_ambiguous":t["ambiguous"],"tie_selected":t["selected"]})
 report={"analysis":"Conflict proposal lifecycle scale v1.2","all_gates_pass":all(g.values()),"gates":g,"scale_summary":summary,"cells_by_worker":norm,"interpretation":"The existing Count(Filter(...)) plus guarded graph rules express stable unique-max selection and explicit tied-max ambiguity for this fixture. Operation counts are empirical for the authored composition and may scale faster than proposal generation.","limits":["N is capped at 64 and one generated fixture family is used.","No learned proposal generation, score quality, natural tie rate, or general rung-3 induction is measured.","No asymptotic theorem follows from this panel."]}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_gates_pass":report["all_gates_pass"],"failed":[k for k,v in g.items() if not v],"summary":summary,"analysis":str(OUT.relative_to(ROOT))},indent=2))
 if not report["all_gates_pass"]: raise SystemExit(1)
if __name__=="__main__":main()
