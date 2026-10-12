#!/usr/bin/env python3
"""Independent analysis of adapter direct-native-access serialization."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_direct_native_access_serialization_v1_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/direct_native_access_serialization_v1_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_direct_native_access_serialization_v1_analysis_20260926.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());locked=json.loads(LOCK.read_text())["locked_inputs"];runs=raw["runs"]
 checks={"raw_and_lock_match":raw["locked_inputs"]==locked and raw["lock_sha256"]==sha(LOCK),
  "three_source_stable_processes":len({r["pid"] for r in runs})==3 and raw["post_run_inputs"]==locked and all(r["worker_started_inputs"]==locked==r["worker_finished_inputs"] for r in runs),
  "four_handle_calls_blocked_then_entered":all(r["pause_gate"] and all(r["attempted"].values()) and all(r["entered"].values()) for r in runs),
  "all_expected_paths_complete":all(r["operation_set_complete"] and set(r["operations"])=={"adapter_tick","inner_node","s_node","s_inner_node"} for r in runs),
  "conversation_semantics_preserved":all(r["reply_parity"] and r["event_order_gate"] and r["identity_gate"] and r["lifecycle_gate"] for r in runs),
  "no_thread_errors":all(r["joined"] and not r["errors"] for r in runs),
  "normalized_shape_repeats":len({json.dumps({k:r[k] for k in ("pause_gate","event_order_gate","identity_gate","lifecycle_gate","reply_parity","operation_set_complete")},sort_keys=True) for r in runs})==1}
 out={"schema_version":1,"raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"checks":checks,"finding":"All four tested adapter entry paths—public tick(), adapter.inner.node(), adapter.s.node(), and adapter.s._inner.node()—attempt the same per-instance RLock while converse is paused, remain outside the protected body until release, and then complete. Across three fresh workers the conversation Goal lifecycle and baseline reply are preserved, with no thread errors.","limits":"This covers only the tested adapter-owned references. Handles retained before wrapping, access to facade internals, separate adapters around one native object, autonomous workers, external PyO3 references, other schedules, and throughput remain outside the evidence."}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks},indent=2))
 if not all(checks.values()):raise SystemExit("direct-access serialization analysis failed")
if __name__=="__main__":main()
