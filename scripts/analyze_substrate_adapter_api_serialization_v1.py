#!/usr/bin/env python3
"""Independently validate adapter public API conversation/tick serialization."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_live_describe_scene_adapter_api_serialization_v1_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/live_describe_scene_adapter_api_serialization_v1_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_adapter_api_serialization_v1_analysis_20260926.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());locked=json.loads(LOCK.read_text())["locked_inputs"];runs=raw["runs"]
 checks={"raw_lock_matches":raw["locked_inputs"]==locked and raw["lock_sha256"]==sha(LOCK),
  "three_source_stable_workers":len(runs)==3 and len({r["pid"] for r in runs})==3 and raw["post_run_inputs"]==locked and all(r["worker_started_inputs"]==locked and r["worker_finished_inputs"]==locked for r in runs),
  "tick_waited_for_conversation_transaction":all(r["b_was_serialized"] and r["b_entered_after_release"] and r["pause_gate"] and not r["b_completed_while_a_blocked"] for r in runs),
  "conversation_goal_lifecycle_and_reply":all(r["event_order_gate"] and r["identity_gate"] and r["lifecycle_gate"] and r["reply_parity"] for r in runs),
  "tick_completed_and_threads_clean":all(type(r["b_tick_steps"]) is int and r["b_tick_steps"]>=0 and r["threads_joined"] and not r["errors"] for r in runs),
  "repeated_semantic_shape":len({json.dumps({k:r[k] for k in ("event_order_gate","identity_gate","lifecycle_gate","pause_gate","reply_parity")},sort_keys=True) for r in runs})==1}
 out={"schema_version":1,"raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"checks":checks,"finding":"A public WorldAdapter.tick call attempts the same per-instance lock while a describe-scene converse transaction is paused. It does not enter the protected method body until conversation finishes. Across three source-stable workers, the conversation lifecycle and baseline reply remain intact, tick completes, and neither thread raises.","limits":"One public-method pair and schedule only. Direct native object access, other adapter methods, multi-adapter sharing, autonomous workers, other schedules, and performance impact remain unverified."}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks},indent=2))
 if not all(checks.values()):raise SystemExit("adapter API serialization analysis failed")
if __name__=="__main__":main()
