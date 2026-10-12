#!/usr/bin/env python3
"""Analyze pass-level progress budget overshoot and closure idempotence."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/"evaluation/reports/rule_run_progress_budget_overshoot_v1_1_20260928.json";OUT=ROOT/"evaluation/reports/rule_run_progress_budget_overshoot_v1_1_analysis_20260928.json";SIZES=(1,2,4,8,16,32,64)
def int_metrics(m):return {k:v for k,v in m.items() if not k.endswith("_ns")}
def main():
 d=json.loads(RAW.read_text());runs=d["runs"];g={"three_workers":len(runs)==3,"locked_inputs_match":all(r["started_inputs"]==d["locked_inputs"] for r in runs),"all_sizes":all([c["n"] for c in r["cells"]]==list(SIZES) for r in runs)};norm=[]
 for r in runs:
  cells=[]
  for c in r["cells"]:
   n=c["n"];f=c["first"];q=c["second"];p=f"{r['worker_id']}_{n}"
   g[p+"_single_pass_batch_applied"]=(f["report"]["status"]=="progress_budget_reached" and f["report"]["requested_progress_budget"]==1 and f["report"]["progress_steps"]==n and f["report"]["budget_overshoot"]==max(n-1,0) and f["attribute_count"]==n and f["metrics"].get("rule_effect_attr_set_attempts",0)==n and all(f["attrs"].get(f"written_{i:03d}")==i+1 for i in range(n)))
   g[p+"_repeat_fixedpoint"]=(q["report"]["status"]=="fixed_point" and q["report"]["progress_steps"]==0 and q["metrics"].get("rule_effect_attr_set_attempts",0)==0 and q["attrs"]==f["attrs"])
   cells.append({"n":n,"first":{"status":f["report"]["status"],"progress_steps":f["report"]["progress_steps"],"budget":f["report"]["requested_progress_budget"],"overshoot":f["report"]["budget_overshoot"],"attribute_set_attempts":f["metrics"].get("rule_effect_attr_set_attempts",0),"candidate_tests":f["metrics"].get("cand_tested",0),"term_evaluations":f["metrics"].get("term_evals_total",0),"integer_metrics":int_metrics(f["metrics"]),"elapsed_ns":f["elapsed_ns"]},"repeat":{"status":q["report"]["status"],"progress_steps":q["report"]["progress_steps"],"attribute_set_attempts":q["metrics"].get("rule_effect_attr_set_attempts",0),"integer_metrics":int_metrics(q["metrics"]),"elapsed_ns":q["elapsed_ns"]}})
  norm.append(cells)
 def sig(cells):return [{"n":x["n"],"first":{k:v for k,v in x["first"].items() if k!="elapsed_ns"},"repeat":{k:v for k,v in x["repeat"].items() if k!="elapsed_ns"}} for x in cells]
 g["integer_work_counts_replicate"]=sig(norm[0])==sig(norm[1])==sig(norm[2])
 report={"analysis":"Rule-run progress-budget overshoot v1.1","all_gates_pass":all(g.values()),"gates":g,"scale_summary":[{ "n":x["n"],"requested_budget":x["first"]["budget"],"actual_progress":x["first"]["progress_steps"],"overshoot":x["first"]["overshoot"],"status":x["first"]["status"],"attribute_set_attempts":x["first"]["attribute_set_attempts"]} for x in norm[0]],"cells_by_worker":norm,"interpretation":"The current implementation applies all eligible independent rules in its dirty batch before checking the outer-loop progress budget again. For this family, overshoot is N-1 and the call returns with the graph changed; the budget is a pass-level stopping threshold rather than a strict per-firing cap.","limits":["One authored independent-rule family; no universal bound on batch size.","Does not inject OS cancellation or a panic inside a pass.","Progress-step counts do not directly bound wall time or memory."]}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_gates_pass":report["all_gates_pass"],"failed":[k for k,v in g.items() if not v],"summary":report["scale_summary"],"analysis":str(OUT.relative_to(ROOT))},indent=2))
 if not report["all_gates_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
