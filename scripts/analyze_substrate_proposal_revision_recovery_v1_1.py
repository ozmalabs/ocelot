#!/usr/bin/env python3
"""Independent gates for fail-closed, resumable proposal revision stages."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/"evaluation/reports/proposal_revision_recovery_v1_1_20260928.json";OUT=ROOT/"evaluation/reports/proposal_revision_recovery_v1_1_analysis_20260928.json";SIZES=(2,8,32,64);CUTS=(0,1,2,3)
def clean(stages):return [{"stage":x["stage"],"report":x["report"],"metrics":{k:v for k,v in x["metrics"].items() if not k.endswith("_ns")}} for x in stages]
def main():
 d=json.loads(RAW.read_text());runs=d["runs"];g={"three_workers":len(runs)==3,"locked_inputs_match":all(r["started_inputs"]==d["locked_inputs"] for r in runs),"all_16_cells":all(len(r["cells"])==16 for r in runs)};norm=[]
 for r in runs:
  cells=[]
  for c in r["cells"]:
   n=c["n"];cut=c["cut_after_stages"];pre=f"{r['worker_id']}_{n}_cut{cut}";initial=c["initial_state"];before=c["pre_recovery"];final=c["final_state"];ta=final["target"];oracle=final["oracle"]
   g[pre+"_initial_committed"]=(initial["target"].get("resolved_revision")==0 and initial["target"].get("max_revision")==0 and initial["target"].get("count_revision")==0 and initial["target"].get("decision_revision")==0 and initial["target"].get("selected_label")==f"p{n-1:03d}")
   g[pre+"_fail_closed_before_resume"]=(before["advertises_current_commit"] is False and before["stamps"]["resolved_revision"]==0)
   expected_resume=(["count","decision"] if cut==1 else ["decision"] if cut==2 else [] if cut==3 else ["max","count","decision"])
   g[pre+"_resumes_missing_stages"]=[x["stage"] for x in c["resume_stages"][:-1]]==expected_resume
   g[pre+"_commit_after_resume"]=(len(c["resume_stages"])>=1 and c["resume_stages"][-1]["stage"]=="commit" and all(x["report"]["status"]=="fixed_point" for x in c["resume_stages"]))
   g[pre+"_final_oracle_correct"]=(ta.get("max_score")==n-2 and ta.get("top_count")==1 and ta.get("ambiguous") is False and ta.get("selected_label")==f"p{n-2:03d}" and oracle["max_score"]==n-2 and oracle["top_labels"]==[f"p{n-2:03d}"])
   g[pre+"_all_stamps_committed"]=(all(ta.get(k)==1 for k in ("max_revision","count_revision","decision_revision","resolved_revision")) and final["revision_nodes"]==1)
   g[pre+"_setup_fixedpoint"]=(len(c["initial_setup_stages"])==4 and all(x["report"]["status"]=="fixed_point" for x in c["initial_setup_stages"]))
   cells.append({"n":n,"cut":cut,"pre_resume_stamps":before["stamps"],"pre_resume_advertised":before["advertises_current_commit"],"interrupted_stages":clean(c["interrupted_stages"]),"resume_stages":clean(c["resume_stages"]),"final_target":ta,"final_oracle":oracle,"revision_nodes":final["revision_nodes"]})
  norm.append(cells)
 g["integer_counts_replicate"]=norm[0]==norm[1]==norm[2]
 summary=[]
 for n in SIZES:
  subset=[c for c in norm[0] if c["n"]==n];summary.append({"n":n,"cuts":{str(c["cut"]):{"pre_resume_committed":c["pre_resume_stamps"]["resolved_revision"],"resume_stages":[x["stage"] for x in c["resume_stages"]],"final_selected":c["final_target"]["selected_label"],"final_revision":c["final_target"]["resolved_revision"]} for c in subset}})
 report={"analysis":"Staged proposal-revision recovery v1","all_gates_pass":all(g.values()),"gates":g,"summary":summary,"cells_by_worker":norm,"interpretation":"Revision stamps fail closed before commit and let the orchestrator resume only the missing completed stages at injected closure boundaries. The final commit matches the independent score oracle at each cut depth.","limits":["Cuts are only between completed closure calls in one live process.","No crash/persistence recovery, torn effect handling inside a closure, concurrent mutation, or asymptotic claim.","Host orchestration, durable logging, and atomic visibility to consumers are not established."]}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_gates_pass":report["all_gates_pass"],"failed":[k for k,v in g.items() if not v],"summary":summary,"analysis":str(OUT.relative_to(ROOT))},indent=2))
 if not report["all_gates_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
