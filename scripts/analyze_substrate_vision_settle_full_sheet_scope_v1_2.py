#!/usr/bin/env python3
"""Independent recomputation of full-sheet settle equation and provenance."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_vision_settle_full_sheet_scope_v1_2_20260925.json"
LOCK=ROOT/"evaluation/substrate_capability/vision_settle_full_sheet_scope_v1_2_lock_20260925.json"
OUT=ROOT/"evaluation/reports/substrate_vision_settle_full_sheet_scope_v1_2_analysis_20260925.json"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def recompute(arm,n):
 x=arm["act"]; aff=arm["aff"]; mean=sum(x)/len(x); pred=[]
 for i in range(n):
  for j in range(n):
   q=i*n+j
   ids=[a*n+b for a in range(max(0,i-1),min(n,i+2)) for b in range(max(0,j-1),min(n,j+2)) if (a,b)!=(i,j)]
   local=sum(x[k] for k in ids)/len(ids) if ids else 0.0
   pred.append(max(aff[q]+local-mean,0.0))
 return max(abs(a-b) for a,b in zip(pred,x)),pred
def main():
 raw=json.loads(RAW.read_text()); lock=json.loads(LOCK.read_text()); p=raw["provenance"]
 allarms=[a for c in raw["cases"] for a in c["arms"]]
 audits=[]
 for c in raw["cases"]:
  audits.append({"seed":c["seed"],"n_side":c["n_side"],"arms":[{"variant":a["variant"],"residual":recompute(a,c["n_side"])[0],"progress":a["progress_applications"],"exact_fixpoint_before_cap":a["engine_fixpoint_before_cap"]} for a in c["arms"]]})
 checks={"runner_protocol_seed_hashes_match":lock["hashes"]["runner"]==p["runner_sha256"] and lock["hashes"]["protocol"]==p["protocol_sha256"] and lock["hashes"]["seed"]==p["seed_sha256"],"analyzer_hash_matches_lock":lock["hashes"]["analyzer"]==sha(Path(__file__)),"native_extension_matches_lock":lock["native_extension_sha256"]==p["native_extension_sha256"],"engine_matches_source":p["engine_provenance"]["source_match"] in ("own","shared") and not p["engine_provenance"]["stale_rust"],"four_registered_pairs":len(raw["cases"])==4 and len(allarms)==8,"root_owns_all_units":all(a["root_membership_count"]==a["n_units"] for a in allarms),"only_settle_and_commit_retained":all(a["removed_other_rules"]>0 for a in allarms),"paired_terminal_arrays_equal":all(c["arms"][0]["act"]==c["arms"][1]["act"] for c in raw["cases"]),"paired_progress_equal":all(c["arms"][0]["progress_applications"]==c["arms"][1]["progress_applications"] for c in raw["cases"]),"independent_residual_within_tolerance":all(q["residual"]<=1e-12 for c in audits for q in c["arms"]),"stored_residual_matches_recompute":all(abs(q["residual"]-a["equation_max_residual"])<=1e-15 for c,qc in zip(raw["cases"],audits) for a,q in zip(c["arms"],qc["arms"]))}
 result={"run_id":"vision-settle-full-sheet-scope-independent-audit-v1.2","raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"analyzer_sha256":sha(Path(__file__)),"case_audits":audits,"checks":checks,"pass":all(checks.values()),"claim_boundary":["Four full build_sheet anatomical workloads show global and Retina-root-scoped rules produce identical states and progress counts.","Three native runs reach the 10,000-application cap; their residuals are at floating-point scale. This is numerical convergence, not exact engine termination.","No orientation task quality, multi-sheet full anatomy, or cost advantage is established."]}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT.relative_to(ROOT)),"checks":checks,"pass":result["pass"]},indent=2))
 if not result["pass"]:raise SystemExit("independent audit failed")
if __name__=="__main__":main()
