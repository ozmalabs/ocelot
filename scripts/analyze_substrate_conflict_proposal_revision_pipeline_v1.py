#!/usr/bin/env python3
"""Independent score oracle, stage, and reproducibility gates."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/"evaluation/reports/conflict_proposal_revision_pipeline_v1_20260928.json";OUT=ROOT/"evaluation/reports/conflict_proposal_revision_pipeline_v1_analysis_20260928.json";SIZES=(2,8,32,64)
def main():
 d=json.loads(RAW.read_text());runs=d["runs"];g={"three_workers":len(runs)==3,"locked_inputs_match":all(r["started_inputs"]==d["locked_inputs"] for r in runs),"all_sizes":all([c["n"] for c in r["cells"]]==list(SIZES) for r in runs)};normalized=[]
 for r in runs:
  cells=[]
  for c in r["cells"]:
   n=c["n"];exp={"initial":(n-1,[f"p{n-1:03d}"],False,f"p{n-1:03d}"),"add_higher":(n+5,["p_high"],False,"p_high"),"add_tie":(n+5,["p_high","p_tie"],True,""),"remove_tie":(n+5,["p_high"],False,"p_high"),"lower_higher_score":(n-1,[f"p{n-1:03d}"],False,f"p{n-1:03d}")};revs=[]
   for rev in c["revisions"]:
    mx,tops,amb,sel=exp[rev["action"]];ta=rev["target"];oracle=rev["oracle"];prefix=f"{r['worker_id']}_{n}_{rev['action']}"
    g[prefix+"_oracle"]=(oracle["max_score"]==mx and oracle["top_labels"]==tops)
    g[prefix+"_resolved_state"]=(ta["max_score"]==mx and ta["top_count"]==len(tops) and ta["ambiguous"] is amb and ta["selected_label"]==sel)
    g[prefix+"_ordered_stages"]=[x["stage"] for x in rev["stages"]]==["compute_max","compute_count","compute_decision"] and all(x["report"]["status"]=="fixed_point" for x in rev["stages"])
    stages=[]
    for x in rev["stages"]:
     m={k:v for k,v in x["metrics"].items() if not k.endswith("_ns")};stages.append({"stage":x["stage"],"progress":x["report"]["progress_steps"],"term_evaluations":m.get("term_evals_total",0),"candidate_tests":m.get("cand_tested",0),"integer_metrics":m,"elapsed_ns":x["elapsed_ns"]})
    revs.append({"action":rev["action"],"expected_max":mx,"expected_top_labels":tops,"state":ta,"stage_work":stages})
   cells.append({"n":n,"revisions":revs})
  normalized.append(cells)
 sig=lambda xs:[[{"action":v["action"],"state":v["state"],"stage_work":[{k:y for k,y in st.items() if k!="elapsed_ns"} for st in v["stage_work"]]} for v in c["revisions"]] for c in xs]
 g["integer_work_counts_replicate"]=sig(normalized[0])==sig(normalized[1])==sig(normalized[2])
 summary=[]
 for c in normalized[0]:summary.append({"n":c["n"],"revision_total_term_evaluations":{v["action"]:sum(s["term_evaluations"] for s in v["stage_work"]) for v in c["revisions"]},"phase_states":{v["action"]:{"max_score":v["state"]["max_score"],"top_count":v["state"]["top_count"],"ambiguous":v["state"]["ambiguous"],"selected_label":v["state"]["selected_label"]} for v in c["revisions"]}})
 report={"analysis":"Explicit revision pipeline for proposal resolution v1","all_gates_pass":all(g.values()),"gates":g,"summary":summary,"workers":normalized,"interpretation":"Explicit unique revision events and ordered max/count/decision closures keep materialized outputs aligned with independent score oracles across the tested mutation sequence.","limits":["Caller must emit an event and execute all three stages after every relevant mutation.","Host mutation/event creation and failure recovery between stages are outside captured native counters.","One proposal family through N=64; no automatic invalidation or asymptotic guarantee."]}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_gates_pass":report["all_gates_pass"],"failed":[k for k,v in g.items() if not v],"summary":summary,"analysis":str(OUT.relative_to(ROOT))},indent=2))
 if not report["all_gates_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
