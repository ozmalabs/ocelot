#!/usr/bin/env python3
"""Independent phase oracle and reproducibility gates for proposal revision v1."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/"evaluation/reports/conflict_proposal_revision_invalidation_v1_20260928.json";OUT=ROOT/"evaluation/reports/conflict_proposal_revision_invalidation_v1_analysis_20260928.json";SIZES=(2,8,32,64)
def main():
 d=json.loads(RAW.read_text());runs=d["runs"];g={"three_workers":len(runs)==3,"locked_inputs_match":all(r["started_inputs"]==d["locked_inputs"] for r in runs),"all_sizes":all([c["n"] for c in r["cells"]]==list(SIZES) for r in runs)};normalized=[]
 for r in runs:
  out=[]
  for c in r["cells"]:
   n=c["n"]
   expected={"initial_unique":(n-1,[f"p{n-1:03d}"],False,f"p{n-1:03d}"),"add_higher":(n+5,["p_high"],False,"p_high"),"add_tie":(n+5,["p_high","p_tie"],True,""),"remove_tie":(n+5,["p_high"],False,"p_high"),"lower_high_score":(n-1,[f"p{n-1:03d}"],False,f"p{n-1:03d}")}
   phases=[]
   for ph in c["phases"]:
    name=ph["name"];mx,tops,amb,sel=expected[name];prefix=f"{r['worker_id']}_{n}_{name}";ta=ph["target"];oracle=ph["score_oracle"]
    g[prefix+"_fixedpoint"]=(ph["report"]["status"]=="fixed_point")
    g[prefix+"_independent_score_oracle"]=(oracle["maximum"]==mx and oracle["top_labels"]==tops)
    g[prefix+"_materialized_state"]=(ta["max_score"]==mx and ta["top_count"]==len(tops) and ta["ambiguous"] is amb and ta["selected_label"]==sel)
    g[prefix+"_top_flags"]=(sorted(k for k,v in ph["top_flags"].items() if v is True)==tops and all(v is (k in tops) for k,v in ph["top_flags"].items()))
    metrics={k:v for k,v in ph["metrics"].items() if not k.endswith("_ns")}
    phases.append({"name":name,"expected_max":mx,"oracle_top_labels":oracle["top_labels"],"state":ta,"top_flags":ph["top_flags"],"progress":ph["report"]["progress_steps"],"term_evaluations":metrics.get("term_evals_total",0),"candidate_tests":metrics.get("cand_tested",0),"integer_metrics":metrics,"elapsed_ns":ph["elapsed_ns"]})
   out.append({"n":n,"phases":phases})
  normalized.append(out)
 sig=lambda xs:[[{k:v for k,v in p.items() if k!="elapsed_ns"} for p in c["phases"]] for c in xs]
 g["integer_work_counts_replicate"]=sig(normalized[0])==sig(normalized[1])==sig(normalized[2])
 summary=[]
 for c in normalized[0]:summary.append({"n":c["n"],"phase_term_evaluations":{p["name"]:p["term_evaluations"] for p in c["phases"]},"selected_states":{p["name"]:{"selected":p["state"]["selected_label"],"ambiguous":p["state"]["ambiguous"],"top_count":p["state"]["top_count"]} for p in c["phases"]}})
 report={"analysis":"Proposal revision and resolver invalidation v1","all_gates_pass":all(g.values()),"gates":g,"summary":summary,"workers":normalized,"interpretation":"The refreshed materialized resolver tracks a controlled series of proposal additions, tie creation/removal, and score mutation by rewriting derived values, including false and empty sentinels. These observations are checked against an independent score oracle.","limits":["One controlled proposal family and four sizes.","The empty string is a chosen selection sentinel; no general truth-maintenance or deletion semantics are implied.","No concurrency, learned proposal generation, or asymptotic guarantee is measured."]}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_gates_pass":report["all_gates_pass"],"failed":[k for k,v in g.items() if not v],"summary":summary,"analysis":str(OUT.relative_to(ROOT))},indent=2))
 if not report["all_gates_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
