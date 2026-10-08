#!/usr/bin/env python3
"""Independent validator for deferred-effect fallback capture."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_scoped_deferred_fallback_v1_2_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/scoped_deferred_fallback_v1_2_lock_20260926.json"
PATHS={"protocol":ROOT/"docs/research/engine_substrate/SUBSTRATE_SCOPED_DEFERRED_FALLBACK_PREREG_20260926.md",
"runner":ROOT/"scripts/substrate_scoped_deferred_fallback_v1.py",
"analyzer":ROOT/"scripts/analyze_substrate_scoped_deferred_fallback_v1.py",
"rewrite":ROOT/"runners/dsl/src/rewrite.rs","substrate":ROOT/"runners/dsl/src/substrate.rs",
"term":ROOT/"runners/dsl/src/term.rs","py_binding":ROOT/"runners/dsl/src/py.rs",
"native_build_manifest":ROOT/"runners/dsl/python/substrate_rs/_native.build.json"}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 raw=json.loads(RAW.read_text()); locked=json.loads(LOCK.read_text())
 hashes={k:sha(v) for k,v in PATHS.items()}
 cells={(r["pair_count"],r["replicate"],r["arm"]):r for r in raw["runs"]}
 expected={(n,r,a) for n in (1,2,4) for r in range(2) for a in ("full","scoped_only","scoped_fallback")}
 keys=(1,2,4); reps=(0,1)
 checks={"lock_hashes_match":hashes==locked==raw["locked_inputs"],
 "matrix_complete":set(cells)==expected and len(raw["runs"])==18,
 "unique_fresh_processes":len({x["pid"] for x in raw["runs"]})==18,
 "native_build_identity_uniform":len({x["native_extension_sha256"] for x in raw["runs"]})==1,
 "scoped_path_surfaces_deferred_queue":all((lambda q:q is not None and q["deferred_effects_pending"] and q["progress_steps"]>0)(cells[n,r,a]["scoped_report"]) for n in keys for r in reps for a in ("scoped_only","scoped_fallback")),
 "scoped_path_is_explicitly_budgeted":all(cells[n,r,a]["scoped_report"]["hit_progress_budget"] for n in keys for r in reps for a in ("scoped_only","scoped_fallback")),
 "scoped_only_control_exposes_stale_state":all(all(x is None for x in cells[n,r,"scoped_only"]["identities"]["previous"]+cells[n,r,"scoped_only"]["identities"]["current"]) and cells[n,r,"scoped_only"]["identities"]["controller_done"] is True for n in keys for r in reps),
 "full_closure_settles":all(cells[n,r,"full"]["global_report"]["status"]=="fixed_point" and not cells[n,r,"full"]["global_report"].get("hit_progress_budget",False) for n in keys for r in reps),
 "fallback_is_invoked_only_after_pending":all(cells[n,r,"scoped_fallback"]["global_report"] is not None and cells[n,r,"scoped_fallback"]["global_report"]["status"]=="fixed_point" and not cells[n,r,"scoped_fallback"]["global_report"].get("hit_progress_budget",False) for n in keys for r in reps),
 "fallback_matches_full_identity_projection":all(cells[n,r,"scoped_fallback"]["identities"]==cells[n,r,"full"]["identities"] for n in keys for r in reps),
 "identity_correspondences_present":all(len(cells[n,r,"full"]["identities"]["previous"])==n and len(cells[n,r,"full"]["identities"]["current"])==n and all(x is not None for x in cells[n,r,"full"]["identities"]["previous"]+cells[n,r,"full"]["identities"]["current"]) for n in keys for r in reps),
 "fallback_terminal_global_closure_zero_work":all(cells[n,r,"scoped_fallback"]["terminal_global_status"]=="fixed_point" and cells[n,r,"scoped_fallback"]["terminal_global_progress"]==0 for n in keys for r in reps)}
 report={"run_id":raw["run_id"],"raw_sha256":sha(RAW),"checks":checks,"all_checks_pass":all(checks.values()),
 "summary":{"workers":len(raw["runs"]),"frames":[2,4,8],"fallback_pairs":sum(cells[n,r,"scoped_fallback"]["identities"]==cells[n,r,"full"]["identities"] for n in keys for r in reps),"scoped_pending_pairs":sum(cells[n,r,"scoped_only"]["scoped_report"]["deferred_effects_pending"] for n in keys for r in reps)},
 "claim_boundary":raw["claim_boundary"]}
 out=ROOT/"evaluation/reports/substrate_scoped_deferred_fallback_v1_2_analysis_20260926.json";out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"analysis":str(out.relative_to(ROOT)),"all_checks_pass":report["all_checks_pass"],"checks":checks,"summary":report["summary"]},indent=2))
 if not report["all_checks_pass"]: raise SystemExit("deferred fallback gate failed; preserve capture")
if __name__=="__main__":main()
