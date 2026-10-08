#!/usr/bin/env python3
"""Independent checks for the serialized threaded describe-scene capture."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_live_describe_scene_threaded_interleaving_v1_2_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/live_describe_scene_threaded_interleaving_v1_2_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_live_describe_scene_threaded_interleaving_v1_2_analysis_20260926.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());locked=json.loads(LOCK.read_text())["locked_inputs"];runs=raw["runs"]
 checks={"raw_digest_matches_lock":raw["lock_sha256"]==sha(LOCK),"raw_inputs_match_lock":raw["locked_inputs"]==locked,
  "three_distinct_workers":len(runs)==3 and len({r["pid"] for r in runs})==3,
  "source_stable_workers_and_postrun":raw["post_run_inputs"]==locked and all(r["worker_started_inputs"]==locked and r["worker_finished_inputs"]==locked for r in runs),
  "lock_blocks_B_while_A_is_paused":all(r["b_was_serialized"] and r["pause_gate"] for r in runs),
  "sequential_lifecycle_ownership":all(r["event_order_gate"] and r["identity_gate"] and r["lifecycle_gate"] for r in runs),
  "both_baseline_replies_and_joined_threads":all(r["reply_parity"] and r["threads_joined"] and not r["errors"] for r in runs),
  "normalized_shape_repeats":len({json.dumps({k:r[k] for k in ("event_order_gate","identity_gate","lifecycle_gate","pause_gate","reply_parity")},sort_keys=True) for r in runs})==1}
 out={"schema_version":1,"raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"checks":checks,
  "finding":"With the WorldAdapter per-instance RLock, B is observed attempting lock acquisition while A is paused after selection and emits no selection until A finishes. In all three fresh workers, A and B then emit separate ordered lifecycle blocks, each Goal resolves and closes with correct message/origin ownership, both baseline replies are returned, and both threads join without exceptions.",
  "limits":"This verifies one controlled describe_scene schedule and the one adapter-level conversation entry point. It does not establish safety for concurrent calls to other WorldAdapter methods, direct native API calls, other routes or schedules, multiple adapters sharing lower-level state, or external-effect handlers. The probe does not compare complete-turn latency with an unlocked code revision, so lock overhead remains unquantified."}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks},indent=2))
 if not all(checks.values()):raise SystemExit("serialized threaded capture analysis failed")
if __name__=="__main__":main()
