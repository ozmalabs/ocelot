#!/usr/bin/env python3
"""Independent validation of scoped NetCollapse fallback parity."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_scoped_net_collapse_fallback_v1_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/scoped_net_collapse_fallback_lock_20260926.json"
PATHS={"protocol":ROOT/"docs/research/engine_substrate/SUBSTRATE_SCOPED_NET_COLLAPSE_FALLBACK_PREREG_20260926.md",
"runner":ROOT/"scripts/substrate_scoped_net_collapse_fallback_v1.py","analyzer":ROOT/"scripts/analyze_substrate_scoped_net_collapse_fallback_v1.py",
"rewrite":ROOT/"runners/dsl/src/rewrite.rs","substrate":ROOT/"runners/dsl/src/substrate.rs","net_forward":ROOT/"runners/dsl/src/net_forward.rs","py_binding":ROOT/"runners/dsl/src/py.rs","native_build_manifest":ROOT/"runners/dsl/python/substrate_rs/_native.build.json"}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());locked=json.loads(LOCK.read_text());hashes={k:sha(v) for k,v in PATHS.items()}
 cells={(x["count"],x["replicate"],x["arm"]):x for x in raw["runs"]};sizes=(1,2,4);reps=(0,1)
 expected={(n,r,a) for n in sizes for r in reps for a in ("full","scoped_only","scoped_fallback")}
 def weights_nonzero(state):return all(x["w2"]==[[0.05]] and x["b2"]==[0.05] for x in state["nets"])
 checks={"lock_hashes_match":hashes==locked==raw["locked_inputs"],"complete_matrix":set(cells)==expected and len(raw["runs"])==18,
 "fresh_pids":len({x["pid"] for x in raw["runs"]})==18,"native_build_uniform":len({x["native_extension_sha256"] for x in raw["runs"]})==1,
 "scoped_reports_deferred_and_budgeted":all(cells[n,r,a]["scoped_report"]["deferred_effects_pending"] and cells[n,r,a]["scoped_report"]["hit_progress_budget"] and cells[n,r,a]["scoped_report"]["progress_steps"]==1 for n in sizes for r in reps for a in ("scoped_only","scoped_fallback")),
 "full_and_fallback_settle":all(cells[n,r,a]["global_report"]["status"]=="fixed_point" and cells[n,r,a]["terminal_status"]=="fixed_point" and cells[n,r,a]["terminal_progress"]==0 for n in sizes for r in reps for a in ("full","scoped_fallback")),
 "fallback_applied_all_net_updates":all(weights_nonzero(cells[n,r,"scoped_fallback"]["state"]) for n in sizes for r in reps),
 "scoped_only_negative_control":all(any(x["w2"]==[[0.0]] and x["observation_status"]=="consumed" for x in cells[n,r,"scoped_only"]["state"]["nets"]) for n in sizes for r in reps),
 "fallback_exact_state_parity":all(cells[n,r,"full"]["state"]==cells[n,r,"scoped_fallback"]["state"] for n in sizes for r in reps),
 "full_updates_all_nets":all(weights_nonzero(cells[n,r,"full"]["state"]) for n in sizes for r in reps)}
 summary={str(n):{"nets":n,"pairs":2,"fallback_matches_full":sum(cells[n,r,"full"]["state"]==cells[n,r,"scoped_fallback"]["state"] for r in reps),"scoped_pending":sum(cells[n,r,"scoped_only"]["scoped_report"]["deferred_effects_pending"] for r in reps)} for n in sizes}
 report={"run_id":raw["run_id"],"raw_sha256":sha(RAW),"checks":checks,"all_checks_pass":all(checks.values()),"summary":summary,"claim_boundary":raw["claim_boundary"]}
 out=ROOT/"evaluation/reports/substrate_scoped_net_collapse_fallback_v1_analysis_20260926.json";out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"analysis":str(out.relative_to(ROOT)),"all_checks_pass":report["all_checks_pass"],"checks":checks,"summary":summary},indent=2))
 if not report["all_checks_pass"]:raise SystemExit("NetCollapse fallback gate failed; preserve capture")
if __name__=="__main__":main()
