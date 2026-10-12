#!/usr/bin/env python3
"""Independent analysis of shared-native facade lock serialization."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_shared_native_facade_serialization_v1_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/shared_native_facade_serialization_v1_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_shared_native_facade_serialization_v1_analysis_20260926.json"
OPS={"adapter_tick","inner_node","s_node","s_inner_node","second_facade_node"}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());locked=json.loads(LOCK.read_text())["locked_inputs"];runs=raw["runs"]
 checks={"raw_and_lock_match":raw["locked_inputs"]==locked and raw["lock_sha256"]==sha(LOCK),
  "three_source_stable_processes":len({r["pid"] for r in runs})==3 and raw["post_run_inputs"]==locked and all(r["worker_started_inputs"]==locked==r["worker_finished_inputs"] for r in runs),
  "all_five_contenders_wait_then_enter":all(r["pause_gate"] and set(r["attempted"])=={"race-"+op for op in OPS} and set(r["entered"])=={"race-"+op for op in OPS} and all(r["attempted"].values()) and all(r["entered"].values()) for r in runs),
  "facades_share_lock_identity":all(r["second_facade_initial_shared_lock"] for r in runs),
  "all_operations_and_threads_clean":all(set(r["operations"])==OPS and r["operation_set_complete"] and r["joined"] and not r["errors"] for r in runs),
  "conversation_semantics_preserved":all(r["reply_parity"] and r["event_order_gate"] and r["identity_gate"] and r["lifecycle_gate"] for r in runs),
  "normalized_shape_repeats":len({json.dumps({k:r[k] for k in ("pause_gate","event_order_gate","identity_gate","lifecycle_gate","reply_parity","operation_set_complete","second_facade_initial_shared_lock")},sort_keys=True) for r in runs})==1}
 out={"schema_version":1,"raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"checks":checks,"finding":"Five paths—public tick(), adapter.inner.node(), adapter.s.node(), adapter.s._inner.node(), and a separately constructed native facade's node()—share the same lock and wait for the active conversation in all three workers. Every operation then completes; Goal identity/lifecycle and the expected reply are preserved without thread errors.","limits":"One shared PyO3 object, two facades, and one controlled schedule. This does not test two complete WorldAdapter instances sharing one substrate, raw handle escape, external callers, autonomous workers, all operations, or throughput."}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks},indent=2))
 if not all(checks.values()):raise SystemExit("shared native facade analysis failed")
if __name__=="__main__":main()
