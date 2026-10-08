#!/usr/bin/env python3
"""Independent gates for simultaneous mixed deferred-queue fallback."""
from __future__ import annotations
import hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_mixed_deferred_queue_fallback_v1_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/mixed_deferred_queue_fallback_lock_20260926.json"
PATHS={"protocol":ROOT/"docs/research/engine_substrate/SUBSTRATE_MIXED_DEFERRED_QUEUE_FALLBACK_PREREG_20260926.md",
"runner":ROOT/"scripts/substrate_mixed_deferred_queue_fallback_v1.py","analyzer":ROOT/"scripts/analyze_substrate_mixed_deferred_queue_fallback_v1.py",
"rewrite":ROOT/"runners/dsl/src/rewrite.rs","substrate":ROOT/"runners/dsl/src/substrate.rs","graph_rules":ROOT/"runners/dsl/src/graph_rules.rs","net_forward":ROOT/"runners/dsl/src/net_forward.rs","term":ROOT/"runners/dsl/src/term.rs","py_binding":ROOT/"runners/dsl/src/py.rs","native_build_manifest":ROOT/"runners/dsl/python/substrate_rs/_native.build.json"}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def successful(s,n):
 return s["target_revision"]==1 and s["patch_status"]=="committed" and s["patch_reason"]=="ok" and s["patch_result_revision"]==1 and s["trigger_fired"] is True and s["observation_status"]=="consumed" and len(s["identities"]["previous"])==n and len(s["identities"]["current"])==n and all(v is not None for v in s["identities"]["previous"]+s["identities"]["current"]) and s["identities"]["previous"]==s["identities"]["current"] and s["weights"]["W2"]==[[0.05]] and s["weights"]["b2"]==[0.05] and math.isclose(s["surprise"],0.15,rel_tol=0,abs_tol=1e-12) and len(s["outputs"])==n and all(s["outputs"])
def incomplete(s,n):
 return s["target_revision"]==0 and s["patch_status"]=="pending" and s["trigger_fired"] is True and s["observation_status"]=="consumed" and all(v is None for v in s["identities"]["previous"]+s["identities"]["current"]) and s["weights"]["W2"]==[[0.0]] and s["weights"]["b2"]==[0.0] and s["surprise"]==0.0 and len(s["outputs"])==n and not any(s["outputs"])
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());hashes={k:sha(v) for k,v in PATHS.items()}
 cells={(x["count"],x["replicate"],x["arm"]):x for x in raw["runs"]};counts=(1,2,4);reps=(0,1)
 expected={(n,r,a) for n in counts for r in reps for a in ("full","scoped_only","scoped_fallback")}
 checks={"locked_hashes_match":hashes==lock==raw["locked_inputs"],"complete_matrix":set(cells)==expected and len(raw["runs"])==18,
 "fresh_pids":len({x["pid"] for x in raw["runs"]})==18,"native_build_uniform":len({x["native_extension_sha256"] for x in raw["runs"]})==1,
 "scoped_call_queues_mixed_work":all(cells[n,r,a]["scoped_report"]["progress_steps"]==1 and cells[n,r,a]["scoped_report"]["hit_progress_budget"] and cells[n,r,a]["scoped_report"]["deferred_effects_pending"] for n in counts for r in reps for a in ("scoped_only","scoped_fallback")),
 "full_and_fallback_reach_fixed_point":all(cells[n,r,a]["global_report"]["status"]=="fixed_point" and cells[n,r,a]["terminal_status"]=="fixed_point" and cells[n,r,a]["terminal_progress"]==0 for n in counts for r in reps for a in ("full","scoped_fallback")),
 "all_three_deferred_effects_resolve":all(successful(cells[n,r,a]["state"],n) for n in counts for r in reps for a in ("full","scoped_fallback")),
 "fallback_exact_state_parity":all(cells[n,r,"full"]["state"]==cells[n,r,"scoped_fallback"]["state"] for n in counts for r in reps),
 "scoped_only_shows_consequential_pending_state":all(incomplete(cells[n,r,"scoped_only"]["state"],n) for n in counts for r in reps)}
 summary={"workers":len(raw["runs"]),"pairs_per_cell":2,"frame_counts":[2*n for n in counts],"fallback_matches_full":sum(cells[n,r,"full"]["state"]==cells[n,r,"scoped_fallback"]["state"] for n in counts for r in reps)}
 report={"run_id":raw["run_id"],"raw_sha256":sha(RAW),"checks":checks,"all_checks_pass":all(checks.values()),"summary":summary,"claim_boundary":raw["claim_boundary"]}
 out=ROOT/"evaluation/reports/substrate_mixed_deferred_queue_fallback_v1_analysis_20260926.json";out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"analysis":str(out.relative_to(ROOT)),"all_checks_pass":report["all_checks_pass"],"checks":checks,"summary":summary},indent=2))
 if not report["all_checks_pass"]:raise SystemExit("mixed deferred queue fallback gate failed; preserve capture")
if __name__=="__main__":main()
