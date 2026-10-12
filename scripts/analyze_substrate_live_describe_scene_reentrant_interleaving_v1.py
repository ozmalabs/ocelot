#!/usr/bin/env python3
"""Independently validate same-thread reentrant describe-scene execution."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_live_describe_scene_reentrant_interleaving_v1_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/live_describe_scene_reentrant_interleaving_v1_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_live_describe_scene_reentrant_interleaving_v1_analysis_20260926.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text())["locked_inputs"];runs=raw["runs"]
 checks={"raw_lock_hash_matches":raw["lock_sha256"]==sha(LOCK),"raw_inputs_match_lock":raw["locked_inputs"]==lock,
  "three_distinct_processes":len(runs)==3 and len({r["pid"] for r in runs})==3,
  "source_stable_workers_and_postrun":raw["post_run_inputs"]==lock and all(r["worker_started_inputs"]==lock and r["worker_finished_inputs"]==lock for r in runs),
  "event_order_gate_all_runs":all(r["event_order_gate"] for r in runs),"a_stays_active_while_b_finishes":all(r["pause_state_gate"] and r["a_pause"]["active"] and r["after_b"]["a"]["status"]=="selected" and r["after_b"]["b"][0]["status"]=="resolved" for r in runs),
  "unique_goal_and_origin_identity":all(r["identity_gate"] for r in runs),"both_replies_match_baseline":all(r["reply_parity"] for r in runs),
  "normalized_semantic_shape_repeats":len({json.dumps({"order":[e["kind"] for e in r["event_rows"]],"owners":r["event_order_gate"],"identity":r["identity_gate"],"pause":r["pause_state_gate"],"reply":r["reply_parity"]},sort_keys=True) for r in runs})==1}
 out={"schema_version":1,"raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"checks":checks,"summary":raw.get("summary",{}),
  "interpretation":"Same-thread reentrant live calls are correctly interleaved: B completes while A remains selected and active, then A resumes; both keep distinct Goal/event ownership and return baseline replies. This is not thread concurrency."}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks},indent=2))
 if not all(checks.values()):raise SystemExit("reentrant analysis failed")
if __name__=="__main__":main()
