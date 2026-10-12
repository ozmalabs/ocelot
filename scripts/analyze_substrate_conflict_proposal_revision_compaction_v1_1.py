#!/usr/bin/env python3
"""Check revision compaction semantics and compare work to unpruned v1."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/"evaluation/reports/conflict_proposal_revision_compaction_v1_1_20260928.json";BASE=ROOT/"evaluation/reports/conflict_proposal_revision_pipeline_v1_analysis_20260928.json";OUT=ROOT/"evaluation/reports/conflict_proposal_revision_compaction_v1_1_analysis_20260928.json";SIZES=(2,8,32,64)
def main():
 d=json.loads(RAW.read_text());base=json.loads(BASE.read_text());runs=d["runs"];g={"three_workers":len(runs)==3,"locked_inputs_match":all(r["started_inputs"]==d["locked_inputs"] for r in runs),"all_sizes":all([c["n"] for c in r["cells"]]==list(SIZES) for r in runs)};norm=[]
 exp={"initial":lambda n:(n-1,[f"p{n-1:03d}"],False,f"p{n-1:03d}"),"add_higher":lambda n:(n+5,["p_high"],False,"p_high"),"add_tie":lambda n:(n+5,["p_high","p_tie"],True,""),"remove_tie":lambda n:(n+5,["p_high"],False,"p_high"),"lower_higher_score":lambda n:(n-1,[f"p{n-1:03d}"],False,f"p{n-1:03d}")}
 for r in runs:
  cells=[]
  for c in r["cells"]:
   n=c["n"];rr=[]
   for i,v in enumerate(c["revisions"]):
    mx,tops,amb,sel=exp[v["action"]](n);ta=v["target"];ora=v["oracle"];pre=f"{r['worker_id']}_{n}_{v['action']}"
    g[pre+"_correct_oracle"]=(ora["max_score"]==mx and ora["top_labels"]==tops and ta["max_score"]==mx and ta["top_count"]==len(tops) and ta["ambiguous"] is amb and ta["selected_label"]==sel)
    g[pre+"_three_fixed_stages"]=(len(v["stages"])==3 and [x["stage"] for x in v["stages"]]==["compute_max","compute_count","compute_decision"] and all(x["report"]["status"]=="fixed_point" for x in v["stages"]))
    cl=v["cleanup"];g[pre+"_bounded_event_state"]=(cl["revision_nodes_after_revision"]==1 and cl["revision_nodes_after_removal"]==0 and (i==0 or (cl["removed_node"] and cl["nodes_before"]-cl["nodes_after_removal"]==1 and cl["edges_before"]-cl["edges_after_removal"]==5)))
    stage=[]
    for x in v["stages"]:
     m={k:y for k,y in x["metrics"].items() if not k.endswith("_ns")};stage.append({"stage":x["stage"],"term_evaluations":m.get("term_evals_total",0),"candidate_tests":m.get("cand_tested",0),"integer_metrics":m,"elapsed_ns":x["elapsed_ns"]})
    basecell=next(b for b in base["workers"][0] if b["n"]==n)
    base_rev=next(b for b in basecell["revisions"] if b["action"]==v["action"])
    baseterm=sum(x["term_evaluations"] for x in base_rev["stage_work"]);thisterm=sum(x["term_evaluations"] for x in stage)
    if i>0:g[pre+"_no_more_closure_work_than_unpruned"]=(thisterm<=baseterm)
    rr.append({"action":v["action"],"target":ta,"oracle":ora,"stages":stage,"closure_term_evaluations":thisterm,"unpruned_term_evaluations":baseterm,"cleanup":cl})
   cells.append({"n":n,"revisions":rr})
  norm.append(cells)
 sig=lambda xs:[[{"action":v["action"],"target":v["target"],"stage_work":[{k:y for k,y in x.items() if k!="elapsed_ns"} for x in v["stages"]]} for v in c["revisions"]] for c in xs]
 g["integer_work_counts_replicate"]=sig(norm[0])==sig(norm[1])==sig(norm[2])
 summary=[]
 for c in norm[0]:summary.append({"n":c["n"],"closure_terms_by_revision":{v["action"]:v["closure_term_evaluations"] for v in c["revisions"]},"unpruned_terms_by_revision":{v["action"]:v["unpruned_term_evaluations"] for v in c["revisions"]},"cleanup_ms_by_revision":{v["action"]:round(v["cleanup"]["elapsed_ns"]/1e6,4) for v in c["revisions"]},"event_nodes_after_revision":{v["action"]:v["cleanup"]["revision_nodes_after_revision"] for v in c["revisions"]}})
 report={"analysis":"Bounded proposal revision-event retention v1.1","all_gates_pass":all(g.values()),"gates":g,"summary":summary,"workers":norm,"interpretation":"Deleting the previous revision node bounds graph-resident event state and is compared with the retained-event v1 closure work. Cleanup timing is host-side and descriptive.","limits":["Caller-managed event deletion only; not built-in compaction.","Interruption recovery, audit-log retention, concurrency, and asymptotic complexity are not established.","Graph mutation and serialization costs are not included in native Term counts."]}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_gates_pass":report["all_gates_pass"],"failed":[k for k,v in g.items() if not v],"summary":summary,"analysis":str(OUT.relative_to(ROOT))},indent=2))
 if not report["all_gates_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
