#!/usr/bin/env python3
"""Independent validation and paired summaries for snapshot clone diagnostic."""
import hashlib,json,statistics,sys
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/"evaluation/reports/substrate_scoped_snapshot_clone_cost_v1_20260926.json"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pct(v,q):
 v=sorted(v);x=(len(v)-1)*q;lo=int(x);hi=min(lo+1,len(v)-1);return v[lo]+(v[hi]-v[lo])*(x-lo)
def main():
 d=json.loads(RAW.read_text());paths={"protocol":ROOT/"docs/research/engine_substrate/SUBSTRATE_SCOPED_SNAPSHOT_CLONE_COST_PREREG_20260926.md","runner":ROOT/"scripts/substrate_scoped_snapshot_clone_cost_v1.py","native":ROOT/"runners/dsl/python/substrate_rs/_native.abi3.so"}
 for k,p in {"graph_rs":"runners/dsl/src/graph.rs","substrate_rs":"runners/dsl/src/substrate.rs","rewrite_rs":"runners/dsl/src/rewrite.rs","py_rs":"runners/dsl/src/py.rs","scale_audit_rs":"runners/dsl/src/scale_audit.rs"}.items():paths[k]=ROOT/p
 integrity={k:sha(p)==d["inputs"][k] for k,p in paths.items()}
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 integrity["rust_source_fingerprint"]=rust_source_fingerprint(str(ROOT))==d["inputs"]["rust_source_fingerprint"];integrity["build_current"]=not build_is_stale(str(ROOT))
 checks=[];groups=defaultdict(list);cell={}
 for r in d["rows"]:
  n,en,fn=int(r["active"]),int(r["match_edges_per_rule"]),int(r["effects_per_rule"]);iters=int(r["profile_iterations"]);calls=int(r["scoped_calls"])
  check={"profile_active_count_exact":int(r["profile_active_count"])==n,"profile_clone_count_exact":int(r["profile_copied_rules"])==n*iters,
   "scoped_zero_progress":r["scoped_outcomes"]==[0]*calls,"state_unchanged":r["before"]==r["after"],"active_count_exact":int(r["before"][-1])==n,
   "slot_count_exact":int(r["before"][-2])==n,"zero_candidate_term_work":int(r["counters"].get("cand_enum",0))==0 and int(r["counters"].get("term_evals_total",0))==0,
   "audit_counters_zero":all(int(v)==0 for v in r["counters"].values())}
  checks.append(check);key=(n,en,fn);groups[key].append(r)
  cell[(n,en,fn,int(r["repeat"]))]=r
 summaries=[]
 for key,rows in sorted(groups.items()):
  clone=[float(r["profile_ns_per_snapshot"]) for r in rows];scope=[float(r["scoped_ns_per_call"]) for r in rows];ratios=[a/b for a,b in zip(clone,scope)]
  summaries.append({"active":key[0],"match_edges":key[1],"effects":key[2],"repeats":len(rows),"clone_median_ns":statistics.median(clone),"clone_p10_ns":pct(clone,.1),"clone_p90_ns":pct(clone,.9),"scoped_median_ns":statistics.median(scope),"scoped_p10_ns":pct(scope,.1),"scoped_p90_ns":pct(scope,.9),"paired_clone_to_scoped_median_ratio":statistics.median(ratios)})
 contrasts=[]
 for n in d["active_counts"]:
  for axis in ("effects","match_edges"):
   clone_deltas=[];scoped_deltas=[]
   for rep in range(int(d["repeats"])):
    if axis=="effects":lo=cell[(n,1,1,rep)];hi=cell[(n,1,8,rep)]
    else:lo=cell[(n,1,1,rep)];hi=cell[(n,8,1,rep)]
    clone_deltas.append(float(hi["profile_ns_per_snapshot"])-float(lo["profile_ns_per_snapshot"]))
    scoped_deltas.append(float(hi["scoped_ns_per_call"])-float(lo["scoped_ns_per_call"]))
   clone_med=statistics.median(clone_deltas);scoped_med=statistics.median(scoped_deltas)
   contrasts.append({"active":int(n),"axis":axis,"clone_delta_median_ns":clone_med,"clone_delta_p10_ns":pct(clone_deltas,.1),"clone_delta_p90_ns":pct(clone_deltas,.9),"scoped_delta_median_ns":scoped_med,"scoped_delta_p10_ns":pct(scoped_deltas,.1),"scoped_delta_p90_ns":pct(scoped_deltas,.9),"clone_increment_over_scoped_increment":clone_med/scoped_med if scoped_med else None})
 result={"all_gates_pass":all(integrity.values()) and all(all(c.values()) for c in checks),"integrity":integrity,"cell_checks":checks,"summaries":summaries,"clone_axis_contrasts":contrasts}
 out=RAW.with_name("substrate_scoped_snapshot_clone_cost_v1_20260926_analysis.json");out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"analysis":str(out),"all_gates_pass":result["all_gates_pass"],"integrity":integrity,"summaries":summaries,"clone_axis_contrasts":contrasts},indent=2))
 if not result["all_gates_pass"]:raise SystemExit("snapshot clone analysis gate failed")
if __name__=="__main__":main()
