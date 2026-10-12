#!/usr/bin/env python3
"""Independent validation of stale and conflicting deferred RulePatch runs."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_scoped_rule_patch_conflict_fallback_v1_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/scoped_rule_patch_conflict_fallback_lock_20260926.json"
PATHS={"protocol":ROOT/"docs/research/engine_substrate/SUBSTRATE_SCOPED_RULE_PATCH_CONFLICT_FALLBACK_PREREG_20260926.md",
"runner":ROOT/"scripts/substrate_scoped_rule_patch_conflict_fallback_v1.py","analyzer":ROOT/"scripts/analyze_substrate_scoped_rule_patch_conflict_fallback_v1.py",
"rewrite":ROOT/"runners/dsl/src/rewrite.rs","substrate":ROOT/"runners/dsl/src/substrate.rs","graph_rules":ROOT/"runners/dsl/src/graph_rules.rs","py_binding":ROOT/"runners/dsl/src/py.rs","native_build_manifest":ROOT/"runners/dsl/python/substrate_rs/_native.build.json"}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());hashes={k:sha(v) for k,v in PATHS.items()}
 cells={(x["case"],x["count"],x["replicate"],x["arm"]):x for x in raw["runs"]};cases=("stale_at_submission","same_revision_race");sizes=(1,2,4);reps=(0,1)
 expected={(c,n,r,a) for c in cases for n in sizes for r in reps for a in ("full","scoped_only","scoped_fallback")}
 pair=lambda x,y:x["state"]==y["state"]
 checks={"locked_hashes_match":hashes==lock==raw["locked_inputs"],"complete_matrix":set(cells)==expected and len(raw["runs"])==36,
 "fresh_pid_per_worker":len({x["pid"] for x in raw["runs"]})==36,"native_build_uniform":len({x["native_extension_sha256"] for x in raw["runs"]})==1,
 "scoped_arms_report_pending_budget":all(cells[c,n,r,a]["scoped_report"]["deferred_effects_pending"] and cells[c,n,r,a]["scoped_report"]["hit_progress_budget"] and cells[c,n,r,a]["scoped_report"]["progress_steps"]==1 for c in cases for n in sizes for r in reps for a in ("scoped_only","scoped_fallback")),
 "full_and_fallback_settle":all(cells[c,n,r,a]["global_report"]["status"]=="fixed_point" and cells[c,n,r,a]["terminal_status"]=="fixed_point" and cells[c,n,r,a]["terminal_progress"]==0 for c in cases for n in sizes for r in reps for a in ("full","scoped_fallback")),
 "fallback_exactly_matches_full":all(pair(cells[c,n,r,"full"],cells[c,n,r,"scoped_fallback"]) for c in cases for n in sizes for r in reps),
 "stale_patch_refusal_preserves_target":all((lambda s:s["target_revision"]==0 and not any(s["outputs"]) and s["patches"]==[{"name":"patch_0","status":"refused","reason":"stale_revision","result_revision":0}])(cells["stale_at_submission",n,r,a]["state"]) for n in sizes for r in reps for a in ("full","scoped_fallback")),
 "same_revision_conflict_is_ordered_commit_then_refusal":all((lambda s:s["target_revision"]==1 and all(s["outputs"]) and s["patches"]==[{"name":"patch_0","status":"committed","reason":"ok","result_revision":1},{"name":"patch_1","status":"refused","reason":"stale_revision","result_revision":1}])(cells["same_revision_race",n,r,a]["state"]) for n in sizes for r in reps for a in ("full","scoped_fallback")),
 "scoped_only_controls_remain_pending":all(all(p["status"]=="pending" for p in cells[c,n,r,"scoped_only"]["state"]["patches"]) and cells[c,n,r,"scoped_only"]["state"]["target_revision"]==0 and not any(cells[c,n,r,"scoped_only"]["state"]["outputs"]) for c in cases for n in sizes for r in reps)}
 report={"run_id":raw["run_id"],"raw_sha256":sha(RAW),"checks":checks,"all_checks_pass":all(checks.values()),
 "summary":{"workers":len(raw["runs"]),"cases":list(cases),"frames":[1,2,4],"fallback_pairs":sum(pair(cells[c,n,r,"full"],cells[c,n,r,"scoped_fallback"]) for c in cases for n in sizes for r in reps)},"claim_boundary":raw["claim_boundary"]}
 out=ROOT/"evaluation/reports/substrate_scoped_rule_patch_conflict_fallback_v1_analysis_20260926.json";out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"analysis":str(out.relative_to(ROOT)),"all_checks_pass":report["all_checks_pass"],"checks":checks,"summary":report["summary"]},indent=2))
 if not report["all_checks_pass"]:raise SystemExit("RulePatch conflict gate failed; preserve capture")
if __name__=="__main__":main()
