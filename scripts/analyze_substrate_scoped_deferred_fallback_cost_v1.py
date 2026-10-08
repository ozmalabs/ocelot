#!/usr/bin/env python3
"""Independent cost summaries and semantic gates for fallback economics."""
from __future__ import annotations
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_scoped_deferred_fallback_cost_v1_1_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/scoped_deferred_fallback_cost_v1_1_lock_20260926.json"
PATHS={"protocol":ROOT/"docs/research/engine_substrate/SUBSTRATE_SCOPED_DEFERRED_FALLBACK_COST_PREREG_20260926.md",
"runner":ROOT/"scripts/substrate_scoped_deferred_fallback_cost_v1.py","analyzer":ROOT/"scripts/analyze_substrate_scoped_deferred_fallback_cost_v1.py",
"rewrite":ROOT/"runners/dsl/src/rewrite.rs","substrate":ROOT/"runners/dsl/src/substrate.rs","term":ROOT/"runners/dsl/src/term.rs","py_binding":ROOT/"runners/dsl/src/py.rs","native_build_manifest":ROOT/"runners/dsl/python/substrate_rs/_native.build.json"}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def med(rows,key):return statistics.median(x[key] for x in rows)
def main():
 raw=json.loads(RAW.read_text());locked=json.loads(LOCK.read_text());hashes={k:sha(v) for k,v in PATHS.items()}
 cells={(x["pair_count"],x["replicate"],x["arm"]):x for x in raw["runs"]};sizes=(1,2,4,8,16);reps=range(12)
 expected={(n,r,a) for n in sizes for r in reps for a in ("full","scoped_fallback")}
 checks={"lock_hashes_match":hashes==locked==raw["locked_inputs"],"matrix_complete":set(cells)==expected and len(raw["runs"])==120,
 "fresh_pid_per_worker":len({x["pid"] for x in raw["runs"]})==120,"native_build_identity_uniform":len({x["native_extension_sha256"] for x in raw["runs"]})==1,
 "all_global_closures_fixed_point":all(x["global_report"]["status"]=="fixed_point" and x["terminal_status"]=="fixed_point" and x["terminal_progress"]==0 for x in raw["runs"]),
 "fallback_pending_and_bounded":all(x["scoped_report"] is not None and x["scoped_report"]["deferred_effects_pending"] and x["scoped_report"]["hit_progress_budget"] and x["scoped_report"]["progress_steps"]==1 for x in raw["runs"] if x["arm"]=="scoped_fallback"),
 "fallback_state_matches_full":all(cells[n,r,"full"]["identities"]==cells[n,r,"scoped_fallback"]["identities"] for n in sizes for r in reps),
 "identity_assignments_present":all(all(v is not None for v in x["identities"]["previous"]+x["identities"]["current"]) for x in raw["runs"]),
 "full_arm_progress_and_fallback_pending":all(cells[n,r,"full"]["global_report"]["progress_steps"]>0 and cells[n,r,"scoped_fallback"]["scoped_report"]["progress_steps"]==1 and cells[n,r,"scoped_fallback"]["global_report"]["status"]=="fixed_point" for n in sizes for r in reps)}
 summary={}
 for n in sizes:
  f=[cells[n,r,"full"] for r in reps];b=[cells[n,r,"scoped_fallback"] for r in reps]
  wr=[b[i]["settlement_wall_ns"]/f[i]["settlement_wall_ns"] for i in reps]
  cr=[b[i]["settlement_cpu_ns"]/f[i]["settlement_cpu_ns"] for i in reps]
  summary[str(2*n)]={"frames":2*n,"pairs":n,"repeats":12,
   "full_median_wall_ms":med(f,"global_wall_ns")/1e6,"fallback_total_median_wall_ms":med(b,"settlement_wall_ns")/1e6,
   "fallback_scoped_median_wall_ms":med(b,"scoped_wall_ns")/1e6,"fallback_drain_median_wall_ms":med(b,"global_wall_ns")/1e6,
   "full_median_cpu_ms":med(f,"global_cpu_ns")/1e6,"fallback_total_median_cpu_ms":med(b,"settlement_cpu_ns")/1e6,
   "paired_wall_ratio_median":statistics.median(wr),"paired_wall_ratio_range":[min(wr),max(wr)],
   "paired_cpu_ratio_median":statistics.median(cr),"median_setup_ms":med(f,"setup_wall_ns")/1e6,
   "median_worker_elapsed_ms_full":med(f,"worker_elapsed_ns")/1e6,"median_worker_elapsed_ms_fallback":med(b,"worker_elapsed_ns")/1e6,
   "median_rss_peak_kib":statistics.median(x["rss_peak_kib"] for x in f+b)}
 report={"run_id":raw["run_id"],"raw_sha256":sha(RAW),"checks":checks,"all_checks_pass":all(checks.values()),"summary_by_frame_count":summary,
  "claim_boundary":raw["claim_boundary"]}
 out=ROOT/"evaluation/reports/substrate_scoped_deferred_fallback_cost_v1_1_analysis_20260926.json";out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"analysis":str(out.relative_to(ROOT)),"all_checks_pass":report["all_checks_pass"],"checks":checks,"summary_by_frame_count":summary},indent=2))
 if not report["all_checks_pass"]:raise SystemExit("fallback cost gate failed; retain capture")
if __name__=="__main__":main()
