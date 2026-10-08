#!/usr/bin/env python3
"""Oracle gates for bounded-pass stage-order falsifier and guarded recovery."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/"evaluation/reports/budgeted_revision_pipeline_order_v1_20260928.json";OUT=ROOT/"evaluation/reports/budgeted_revision_pipeline_order_v1_analysis_20260928.json";SIZES=(2,8,64);ORDERS=("normal","reverse");GUARDS=("unguarded","guarded")
def metrics(c):return {k:v for k,v in c.items() if not k.endswith("_ns")}
def main():
 d=json.loads(RAW.read_text());runs=d["runs"];g={"three_workers":len(runs)==3,"lock_match":all(r["started_inputs"]==d["locked_inputs"] for r in runs),"all_cells":all(len(r["cells"])==12 for r in runs)};norm=[]
 for r in runs:
  cells=[]
  for c in r["cells"]:
   n,o,guard=c["n"],c["order"],c["guard"];p=f"{r['worker_id']}_{n}_{o}_{guard}";lim=c["limited"];res=c["resumed"];la=lim["attrs"];ra=res["attrs"];exp=c["expected"]
   g[p+"_budget_returned"]=(lim["report"]["status"]=="progress_budget_reached" and lim["report"]["requested_progress_budget"]==1 and lim["report"]["progress_steps"]>=1 and lim["report"]["budget_overshoot"]==lim["report"]["progress_steps"]-1)
   if o=="reverse" and guard=="unguarded":
    g[p+"_negative_control_false_commit"]=(la.get("resolved_revision")==1 and (la.get("max_score"),la.get("top_count"),la.get("selected_label"))!=(exp["max_score"],exp["top_count"],exp["selected_label"]) and res["report"]["status"]=="fixed_point" and (ra.get("max_score"),ra.get("top_count"),ra.get("selected_label"))!=(exp["max_score"],exp["top_count"],exp["selected_label"]))
   else:
    g[p+"_no_false_commit_on_cut"]=(la.get("resolved_revision")==1 if (la.get("max_score"),la.get("top_count"),la.get("selected_label"))==(exp["max_score"],exp["top_count"],exp["selected_label"]) else la.get("resolved_revision")==0)
    g[p+"_resume_oracle_correct"]=(res["report"]["status"]=="fixed_point" and ra.get("resolved_revision")==1 and ra.get("max_revision")==ra.get("count_revision")==ra.get("decision_revision")==1 and ra.get("max_score")==exp["max_score"] and ra.get("top_count")==exp["top_count"] and ra.get("selected_label")==exp["selected_label"] and ra.get("ambiguous") is False)
   cells.append({"n":n,"order":o,"guard":guard,"limited":{"status":lim["report"]["status"],"progress":lim["report"]["progress_steps"],"overshoot":lim["report"]["budget_overshoot"],"attrs":la,"term_evaluations":lim["metrics"].get("term_evals_total",0),"candidate_tests":lim["metrics"].get("cand_tested",0),"integer_metrics":metrics(lim["metrics"]),"elapsed_ns":lim["elapsed_ns"]},"resumed":{"status":res["report"]["status"],"progress":res["report"]["progress_steps"],"attrs":ra,"term_evaluations":res["metrics"].get("term_evals_total",0),"candidate_tests":res["metrics"].get("cand_tested",0),"integer_metrics":metrics(res["metrics"]),"elapsed_ns":res["elapsed_ns"]}})
  norm.append(cells)
 def sig(cells):return [{"n":x["n"],"order":x["order"],"guard":x["guard"],"limited":{k:v for k,v in x["limited"].items() if k!="elapsed_ns"},"resumed":{k:v for k,v in x["resumed"].items() if k!="elapsed_ns"}} for x in cells]
 g["integer_counts_replicate"]=sig(norm[0])==sig(norm[1])==sig(norm[2])
 summary=[]
 for n in SIZES:
  summary.append({"n":n,"arms":{f"{x['order']}_{x['guard']}":{"limited":{"progress":x["limited"]["progress"],"overshoot":x["limited"]["overshoot"],"resolved":x["limited"]["attrs"].get("resolved_revision"),"selected":x["limited"]["attrs"].get("selected_label")},"after_resume":{"resolved":x["resumed"]["attrs"].get("resolved_revision"),"selected":x["resumed"]["attrs"].get("selected_label"),"resume_terms":x["resumed"]["term_evaluations"]}} for x in norm[0] if x["n"]==n}})
 report={"analysis":"Budgeted staged-revision order v1","all_gates_pass":all(g.values()),"gates":g,"summary":summary,"cells_by_worker":norm,"interpretation":"Unguarded reverse-order rules can stamp and commit values calculated from stale upstream fields in the budget-limited pass. Readiness guards prevent downstream stages from advancing until upstream stamps match, allowing the next closure to recover correctly.","limits":["Sequential authored rules and one score mutation family only.","No concurrency or OS kill inside native execution.","Readiness guards are not automatically enforced for arbitrary rule stores."]}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_gates_pass":report["all_gates_pass"],"failed":[k for k,v in g.items() if not v],"summary":summary,"analysis":str(OUT.relative_to(ROOT))},indent=2))
 if not report["all_gates_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
