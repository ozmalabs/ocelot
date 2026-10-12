#!/usr/bin/env python3
"""Offline integrity analysis for the live self-report route probe."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/live_self_report_route_regression_v1_20260927.json"
LOCK=ROOT/"evaluation/substrate_capability/live_self_report_route_regression_v1_lock_20260927.json"
OUT=ROOT/"evaluation/reports/live_self_report_route_regression_v1_analysis_20260927.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());locked=json.loads(LOCK.read_text());runs=raw["runs"];source_lock=locked["source_lock"]
 checks={"three_distinct_processes":len(runs)==3 and len({r["pid"] for r in runs})==3,
  "probe_protocol_and_runner_match_lock":raw["protocol_sha256"]==locked["protocol_sha256"] and raw["runner_sha256"]==locked["runner_sha256"],
  "all_worker_and_driver_fingerprints_match":raw["locked_inputs"]==raw["post_run_inputs"]==source_lock and all(r["worker_start_lock"]==source_lock==r["worker_end_lock"] for r in runs),
  "failure_behavior_repeats":all(r["route"] is None and r["goal_count"]==0 and r["goals"]==[] and r["reply"]==runs[0]["reply"] and "no faculty for it yet" in r["reply"] for r in runs),
  "boot_failures_and_loaded_manifests_repeat":all(r["failed_seeds"]==runs[0]["failed_seeds"] and r["loaded_seed_count"]==runs[0]["loaded_seed_count"] and r["conversation_seeds_loaded"]==runs[0]["conversation_seeds_loaded"] for r in runs),
  "semantic_graph_repeats":len({(r["graph_nodes"],r["graph_edges"],r["semantic_graph_sha256"]) for r in runs})==1}
 payload={"schema_version":1,"raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"checks":checks,"all_checks_pass":all(checks.values()),"summary":{"replicates":len(runs),"loaded_seed_count":runs[0]["loaded_seed_count"],"failed_seed_count":len(runs[0]["failed_seeds"]),"failed_seeds":runs[0]["failed_seeds"],"route":runs[0]["route"],"reply":runs[0]["reply"],"goal_count":runs[0]["goal_count"],"graph_nodes":runs[0]["graph_nodes"],"graph_edges":runs[0]["graph_edges"],"semantic_graph_sha256":runs[0]["semantic_graph_sha256"]},"claim_boundary":"This confirms one source-locked current full-boot self-report route failure in three fresh processes. It does not establish causality between boot seed failures and route selection, general conversational failure prevalence, or tractability."}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks,"all_checks_pass":payload["all_checks_pass"],"summary":payload["summary"]},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit("independent route-regression analysis failed")
if __name__=="__main__":main()
