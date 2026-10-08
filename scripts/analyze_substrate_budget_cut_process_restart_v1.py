#!/usr/bin/env python3
"""Verify checkpoint integrity and gated recovery after a budget cut."""
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/budget_cut_process_restart_v1_20260928.json"
OUT=ROOT/"evaluation/reports/budget_cut_process_restart_v1_analysis_20260928.json"
SIZES=(2,64); ARMS=(("reverse","guarded"),("reverse","unguarded"),("normal","guarded"))
def stable(x):
 if isinstance(x,dict): return {k:stable(v) for k,v in x.items() if not k.endswith("_ns") and k not in ("pid","path")}
 if isinstance(x,list): return [stable(v) for v in x]
 return x
def main():
 d=json.loads(RAW.read_text()); runs=d["runs"]; gates={"three_workers":len(runs)==3}
 gates["six_cells_each"]=all(len(r["cells"])==len(SIZES)*len(ARMS) for r in runs)
 gates["worker_source_locks_match"]=all(r["started_inputs"]==d["locked_inputs"] for r in runs)
 summaries=[]
 for r in runs:
  for c in r["cells"]:
   n,o,guard=c["n"],c["order"],c["guard"]; tag=f"w{r['worker_id']}_n{n}_{o}_{guard}"
   p=c["producer"]; z=c["resume"]; expected=f"p{n-2:03d}"
   gates[tag+"_fresh_process"]=p["pid"]!=z["pid"]
   gates[tag+"_checkpoint_hash"]=c["checkpoint"]["matches_manifest"] and c["checkpoint"]["bytes"]==p["bytes"]
   gates[tag+"_restoration"]=z["graph_exact"] and z["grammar_exact"] and z["rules_semantic"]
   gates[tag+"_budget_cut"]=p["limited"]["report"]["status"]=="progress_budget_reached" and p["limited"]["report"]["requested_progress_budget"]==1
   a=p["target"]; b=z["target"]; oracle=p["oracle"]
   if o=="reverse" and guard=="unguarded":
    gates[tag+"_false_commit_survives_restart"]=(a.get("resolved_revision")==1 and a.get("selected_label")!=expected and z["resume"]["report"]["status"]=="fixed_point" and b.get("resolved_revision")==1 and b.get("selected_label")!=expected)
   else:
    if o=="reverse":
     gates[tag+"_guarded_commit_not_advanced_at_cut"]=(a.get("resolved_revision")==0 and a.get("consumed_revision")==0)
    else:
     gates[tag+"_normal_order_positive_control"]=(a.get("resolved_revision")==1 and a.get("consumed_revision")==1 and a.get("selected_label")==expected and a.get("max_score")==n-2)
    gates[tag+"_restart_reaches_oracle"]=(z["resume"]["report"]["status"]=="fixed_point" and b.get("max_revision")==b.get("count_revision")==b.get("decision_revision")==b.get("resolved_revision")==b.get("consumed_revision")==1 and b.get("max_score")==oracle["max_score"]==n-2 and b.get("selected_label")==expected and b.get("top_count")==oracle["top_count"]==1 and b.get("ambiguous") is False)
   summaries.append({"worker":r["worker_id"],"n":n,"order":o,"guard":guard,"producer_pid":p["pid"],"resume_pid":z["pid"],"budget_report":p["limited"]["report"],"before_restart":a,"after_restart":b,"oracle":oracle,"checkpoint":c["checkpoint"],"work":{"limited":p["limited"]["metrics"],"resume":z["resume"]["metrics"]}})
 signatures=[]
 for r in runs:
   signatures.append(stable([{ "n":c["n"],"order":c["order"],"guard":c["guard"],"producer":{"limited":c["producer"]["limited"],"target":c["producer"]["target"],"oracle":c["producer"]["oracle"],"revision_nodes":c["producer"]["revision_nodes"]},"resume":{"resume":c["resume"]["resume"],"target":c["resume"]["target"],"oracle":c["resume"]["oracle"],"revision_nodes":c["resume"]["revision_nodes"],"graph_exact":c["resume"]["graph_exact"],"grammar_exact":c["resume"]["grammar_exact"],"rules_semantic":c["resume"]["rules_semantic"]}} for c in r["cells"]]))
 gates["work_and_state_replicate"]=signatures[0]==signatures[1]==signatures[2]
 report={"analysis":"Budget-cut process restart v1","all_gates_pass":all(gates.values()),"gates":gates,"cells":summaries,"interpretation":"A fresh process restores the serialized state and authored rules. Readiness guards preserve the previous resolved/consumed revision at the budget cut and permit correct recovery after restart. The unguarded reverse-order control persists a false commit; restart preserves that semantically wrong but internally restored state.","limits":["Clean process exit and one fsync'ed JSON checkpoint; no kill during native execution or power-loss test.","One proposal family, one revision mutation, two rule orders, and two graph sizes.","Readiness guards are authored policies, not automatic engine contracts."]}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"all_gates_pass":report["all_gates_pass"],"failed":[k for k,v in gates.items() if not v],"cells":len(summaries),"analysis":str(OUT.relative_to(ROOT))},indent=2))
 if not report["all_gates_pass"]: raise SystemExit(1)
if __name__=="__main__": main()
