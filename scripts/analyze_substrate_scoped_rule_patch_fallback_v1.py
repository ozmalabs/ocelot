#!/usr/bin/env python3
"""Independent analyzer for graph-native RulePatch fallback study."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_scoped_rule_patch_fallback_v1_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/scoped_rule_patch_fallback_lock_20260926.json"
PATHS={"protocol":ROOT/"docs/research/engine_substrate/SUBSTRATE_SCOPED_RULE_PATCH_FALLBACK_PREREG_20260926.md",
"runner":ROOT/"scripts/substrate_scoped_rule_patch_fallback_v1.py","analyzer":ROOT/"scripts/analyze_substrate_scoped_rule_patch_fallback_v1.py",
"rewrite":ROOT/"runners/dsl/src/rewrite.rs","substrate":ROOT/"runners/dsl/src/substrate.rs","graph_rules":ROOT/"runners/dsl/src/graph_rules.rs","py_binding":ROOT/"runners/dsl/src/py.rs","native_build_manifest":ROOT/"runners/dsl/python/substrate_rs/_native.build.json"}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());hashes={k:sha(v) for k,v in PATHS.items()}
 cells={(x["count"],x["replicate"],x["arm"]):x for x in raw["runs"]};sizes=(1,2,4);reps=(0,1)
 expected={(n,r,a) for n in sizes for r in reps for a in ("full","scoped_only","scoped_fallback")}
 checks={"locked_hashes_match":hashes==lock==raw["locked_inputs"],"complete_matrix":set(cells)==expected and len(raw["runs"])==18,
 "fresh_pid_per_worker":len({x["pid"] for x in raw["runs"]})==18,"native_build_uniform":len({x["native_extension_sha256"] for x in raw["runs"]})==1,
 "scoped_arms_surface_pending":all(cells[n,r,a]["scoped_report"]["deferred_effects_pending"] and cells[n,r,a]["scoped_report"]["hit_progress_budget"] and cells[n,r,a]["scoped_report"]["progress_steps"]==1 for n in sizes for r in reps for a in ("scoped_only","scoped_fallback")),
 "full_and_fallback_settle":all(cells[n,r,a]["global_report"]["status"]=="fixed_point" and cells[n,r,a]["terminal_status"]=="fixed_point" and cells[n,r,a]["terminal_progress"]==0 for n in sizes for r in reps for a in ("full","scoped_fallback")),
 "patch_committed_and_revision_advanced":all(cells[n,r,a]["state"]["patch_status"]=="committed" and cells[n,r,a]["state"]["patch_reason"]=="ok" and cells[n,r,a]["state"]["patch_result_revision"]==1 and cells[n,r,a]["state"]["target_revision"]==1 for n in sizes for r in reps for a in ("full","scoped_fallback")),
 "patched_rule_reaches_every_frame":all(all(cells[n,r,a]["state"]["outputs"]) and len(cells[n,r,a]["state"]["outputs"])==n for n in sizes for r in reps for a in ("full","scoped_fallback")),
 "fallback_exact_full_state_parity":all(cells[n,r,"full"]["state"]==cells[n,r,"scoped_fallback"]["state"] for n in sizes for r in reps),
 "scoped_only_is_incomplete_control":all(cells[n,r,"scoped_only"]["state"]["target_revision"]==0 and cells[n,r,"scoped_only"]["state"]["patch_status"]=="pending" and not any(cells[n,r,"scoped_only"]["state"]["outputs"]) for n in sizes for r in reps)}
 report={"run_id":raw["run_id"],"raw_sha256":sha(RAW),"checks":checks,"all_checks_pass":all(checks.values()),
  "summary":{"workers":len(raw["runs"]),"frame_sizes":[1,2,4],"fallback_pairs":sum(cells[n,r,"full"]["state"]==cells[n,r,"scoped_fallback"]["state"] for n in sizes for r in reps)},"claim_boundary":raw["claim_boundary"]}
 out=ROOT/"evaluation/reports/substrate_scoped_rule_patch_fallback_v1_analysis_20260926.json";out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"analysis":str(out.relative_to(ROOT)),"all_checks_pass":report["all_checks_pass"],"checks":checks,"summary":report["summary"]},indent=2))
 if not report["all_checks_pass"]:raise SystemExit("RulePatch fallback gate failed; preserve capture")
if __name__=="__main__":main()
