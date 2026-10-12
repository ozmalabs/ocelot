#!/usr/bin/env python3
"""Independent integrity, gate, and factorial analysis for scoped body probe."""
import hashlib,json,statistics,sys
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/"evaluation/reports/substrate_scoped_rule_body_factorial_v1_20260926.json"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def percentile(v,q):
 v=sorted(v);x=(len(v)-1)*q;lo=int(x);hi=min(lo+1,len(v)-1);return v[lo]+(v[hi]-v[lo])*(x-lo)
def main():
 d=json.loads(RAW.read_text());paths={"protocol":ROOT/"docs/research/engine_substrate/SUBSTRATE_SCOPED_RULE_BODY_FACTORIAL_PREREG_20260926.md","runner":ROOT/"scripts/substrate_scoped_rule_body_factorial_v1.py","native":ROOT/"runners/dsl/python/substrate_rs/_native.abi3.so"}
 for k,p in {"graph_rs":"runners/dsl/src/graph.rs","substrate_rs":"runners/dsl/src/substrate.rs","rewrite_rs":"runners/dsl/src/rewrite.rs","py_rs":"runners/dsl/src/py.rs","scale_audit_rs":"runners/dsl/src/scale_audit.rs"}.items():paths[k]=ROOT/p
 integrity={k:sha(p)==d["inputs"][k] for k,p in paths.items()}
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 integrity["rust_source_fingerprint"]=rust_source_fingerprint(str(ROOT))==d["inputs"]["rust_source_fingerprint"];integrity["build_current"]=not build_is_stale(str(ROOT))
 checks=[];groups=defaultdict(list);byrep={}
 for r in d["rows"]:
  n,e,f=int(r["active"]),int(r["match_edges_per_rule"]),int(r["effects_per_rule"])
  checks.append({"zero_progress":r["outcomes"]==[0]*int(r["calls"]),"state_unchanged":r["before"]==r["after"],"exact_rule_slots":int(r["before"][-2])==n,"exact_active_rules":int(r["before"][-1])==n,"zero_candidates_terms":int(r["counters"].get("cand_enum",0))==0 and int(r["counters"].get("term_evals_total",0))==0,"audit_off_zero":all(int(v)==0 for v in r["counters"].values())})
  key=(n,e,f);groups[key].append(float(r["ns_per_call"]));byrep[(n,int(r["repeat"]),e,f)]=float(r["ns_per_call"])
 summaries=[]
 for key,vals in sorted(groups.items()):summaries.append({"active":key[0],"match_edges":key[1],"effects":key[2],"repeats":len(vals),"median_ns_per_call":statistics.median(vals),"p10_ns_per_call":percentile(vals,.1),"p90_ns_per_call":percentile(vals,.9)})
 contrasts=[]
 for n in d["active_counts"]:
  per={"match_edge_effect":[],"effect_match_edge":[],"interaction":[]}
  for rep in range(int(d["repeats"])):
   # Paired repeat contrasts on the raw per-call observations.
   a=byrep[(n,rep,8,1)]-byrep[(n,rep,1,1)];b=byrep[(n,rep,8,8)]-byrep[(n,rep,1,8)]
   c=byrep[(n,rep,1,8)]-byrep[(n,rep,1,1)];e=byrep[(n,rep,8,8)]-byrep[(n,rep,8,1)]
   per["match_edge_effect"].append((a+b)/2);per["effect_match_edge"].append((c+e)/2);per["interaction"].append(b-a)
  contrasts.append({"active":int(n),**{k:{"median_ns_per_call":statistics.median(v),"p10_ns_per_call":percentile(v,.1),"p90_ns_per_call":percentile(v,.9)} for k,v in per.items()}})
 result={"all_gates_pass":all(integrity.values()) and all(all(x.values()) for x in checks),"integrity":integrity,"checks":checks,"summaries":summaries,"paired_factorial_contrasts":contrasts}
 out=RAW.with_name("substrate_scoped_rule_body_factorial_v1_20260926_analysis.json");out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"analysis":str(out),"all_gates_pass":result["all_gates_pass"],"integrity":integrity,"summaries":summaries,"paired_factorial_contrasts":contrasts},indent=2))
 if not result["all_gates_pass"]:raise SystemExit("factorial probe analysis failed")
if __name__=="__main__":main()
