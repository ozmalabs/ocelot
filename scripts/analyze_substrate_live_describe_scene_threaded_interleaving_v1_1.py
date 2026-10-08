#!/usr/bin/env python3
"""Independently analyze the threaded live describe-scene capture."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_live_describe_scene_threaded_interleaving_v1_1_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/live_describe_scene_threaded_interleaving_v1_1_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_live_describe_scene_threaded_interleaving_v1_1_analysis_20260926.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());locked=json.loads(LOCK.read_text())["locked_inputs"];runs=raw["runs"]
 stable_errors=[]
 for r in runs:
  errs=r["errors"]
  stable_errors.append(len(errs)==1 and errs[0]["thread"]=="B" and errs[0]["type"]=="RuntimeError" and errs[0]["message"]=="Already mutably borrowed" and "world_adapter.py\", line 8082" in errs[0]["traceback"] and "substrate_rs/__init__.py\", line 765" in errs[0]["traceback"])
 checks={"raw_digest_matches_lock":raw["lock_sha256"]==sha(LOCK),"raw_inputs_match_lock":raw["locked_inputs"]==locked,
  "three_distinct_workers":len(runs)==3 and len({r["pid"] for r in runs})==3,
  "source_stable_workers_and_postrun":raw["post_run_inputs"]==locked and all(r["worker_started_inputs"]==locked and r["worker_finished_inputs"]==locked for r in runs),
  "A_blocked_while_B_reached_result":all(r["b_completed_while_a_blocked"] and r["pause_gate"] for r in runs),
  "identity_and_lifecycle_survive_before_reply_failure":all(r["identity_gate"] and r["lifecycle_gate"] and r["event_order_gate"] for r in runs),
  "B_borrow_error_repeats_at_converse_node_read":all(stable_errors),
  "B_reply_missing_and_A_reply_preserved":all(set(r["replies"])=={"A"} and r["reply_parity"] is False for r in runs),
  "native_source_has_mutable_gil_releasing_run_rules":all("native_py" in r["worker_started_inputs"]["source_sha256"] for r in runs)}
 out={"schema_version":1,"raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"checks":checks,
  "finding":"The controlled overlap consistently completes B's identity-bound lifecycle while A is blocked, but B then fails in WorldAdapter.converse at the MessageInterpretation node read with RuntimeError: Already mutably borrowed. The exception originates at substrate_rs.Substrate.node. A returns its baseline reply; B has no reply. Thus graph lifecycle identity survives, but this live route is not safe for this concurrent call pattern.",
  "root_cause_assessment":"The traceback plus runners/dsl/src/py.rs show run_rules is declared with &mut self while using py.allow_threads around an Arc<Mutex<SubstrateRs>> operation. This suggests PyO3's exclusive PyClass borrow outlives GIL release and conflicts with another thread's node read. Treat this as a source-supported diagnosis, not a verified fix; arbitrary concurrent access needs a broader borrow/API audit.",
  "limits":"One controlled route and barrier schedule, three fresh workers. Does not establish all concurrent schedules or other WorldAdapter methods."}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks},indent=2))
 if not all(checks.values()):raise SystemExit("threaded capture analysis validity failed")
if __name__=="__main__":main()
