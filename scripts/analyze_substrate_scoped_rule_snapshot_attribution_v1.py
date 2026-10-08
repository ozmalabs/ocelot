#!/usr/bin/env python3
"""Independent validation and contrasts for scoped snapshot attribution."""
import hashlib,json,statistics,sys
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; RAW=ROOT/"evaluation/reports/substrate_scoped_rule_snapshot_attribution_v1_20260926.json"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def pct(xs,q):
    xs=sorted(xs); return xs[round((len(xs)-1)*q)]
def main():
 d=json.loads(RAW.read_text()); paths={"protocol":ROOT/"docs/research/engine_substrate/SUBSTRATE_SCOPED_RULE_SNAPSHOT_ATTRIBUTION_PREREG_20260926.md",
 "runner":ROOT/"scripts/substrate_scoped_rule_snapshot_attribution_v1.py","native":ROOT/"runners/dsl/python/substrate_rs/_native.abi3.so"}
 for k,p in {"graph_rs":"runners/dsl/src/graph.rs","substrate_rs":"runners/dsl/src/substrate.rs","rewrite_rs":"runners/dsl/src/rewrite.rs","py_rs":"runners/dsl/src/py.rs","scale_audit_rs":"runners/dsl/src/scale_audit.rs"}.items(): paths[k]=ROOT/p
 integrity={k:sha(p)==d["inputs"][k] for k,p in paths.items()}
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 integrity["rust_source_fingerprint"]=rust_source_fingerprint(str(ROOT))==d["inputs"]["rust_source_fingerprint"]
 integrity["build_current"]=not build_is_stale(str(ROOT))
 checks=[]; groups=defaultdict(list)
 for r in d["rows"]:
  a,t,shape=int(r["active"]),int(r["tombstones"]),r["shape"]
  checks.append({"zero_progress":r["results"]==[0]*int(r["calls"]),"unchanged_state":r["before"]==r["after"],
   "correct_slot_count":int(r["before"][-2])==a+t,"correct_active_count":int(r["before"][-1])==a,"zero_candidate_and_term_work":int(r["counters"].get("cand_enum",0))==0 and int(r["counters"].get("term_evals_total",0))==0,
   "audit_off_counters_zero":all(int(v)==0 for v in r["counters"].values())})
  groups[(a,t,shape)].append(float(r["ns_per_call"]))
 summary=[]
 for key,vals in sorted(groups.items()): summary.append({"active":key[0],"tombstones":key[1],"shape":key[2],"repeats":len(vals),"median_ns_per_call":statistics.median(vals),"p10_ns_per_call":pct(vals,.1),"p90_ns_per_call":pct(vals,.9)})
 indexed={(x["active"],x["tombstones"],x["shape"]):x["median_ns_per_call"] for x in summary}; contrasts=[]
 for a in d["active_counts"]:
  for sh in ("small","large"):
   base=indexed[(a,0,sh)]; dead=indexed[(a,a,sh)]
   contrasts.append({"active":a,"shape":sh,"tombstone_delta_ns_per_call":dead-base,"tombstone_ratio":dead/base})
  contrasts.append({"active":a,"contrast":"large_minus_small_no_tombstones_ns_per_call","value":indexed[(a,0,"large")]-indexed[(a,0,"small")]})
 result={"all_gates_pass":all(integrity.values()) and all(all(c.values()) for c in checks),"integrity":integrity,"cell_checks":checks,"summaries":summary,"contrasts":contrasts}
 out=RAW.with_name("substrate_scoped_rule_snapshot_attribution_v1_20260926_analysis.json");out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"analysis":str(out),"all_gates_pass":result["all_gates_pass"],"integrity":integrity,"summaries":summary,"contrasts":contrasts},indent=2))
 if not result["all_gates_pass"]: raise SystemExit("analysis gate failed")
if __name__=="__main__": main()
