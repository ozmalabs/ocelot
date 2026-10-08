#!/usr/bin/env python3
"""Independently validate lifecycle interleaving capture and semantic controls."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_native_goal_lifecycle_interleaving_v1_1_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/native_goal_lifecycle_interleaving_v1_1_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_native_goal_lifecycle_interleaving_v1_1_analysis_20260926.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text())["locked_inputs"];runs=raw["runs"]
 checks={"raw_lock_digest_matches":raw["lock_sha256"]==sha(LOCK),"raw_inputs_match_lock":raw["locked_inputs"]==lock,
  "three_distinct_pids":len(runs)==3 and len({r["pid"] for r in runs})==3,
  "source_stable_workers_and_postrun":raw["post_run_inputs"]==lock and all(r["worker_started_inputs"]==lock and r["worker_finished_inputs"]==lock for r in runs),
  "six_interleaved_checkpoints_replicate":all(len(r["checkpoints"])==6 and r["positive_identity_gate"] for r in runs),
  "missing_owner_does_not_transition":all(not r["missing_owner"]["for_goal_ids"] and all(g["status"]=="proposed" for g in r["missing_owner"]["goals"]) for r in runs),
  "ambiguous_owner_link_detected":all(len(r["ambiguous_owner"]["for_goal_ids"])==2 for r in runs),
  "ambiguous_owner_rejected":all([g["status"] for g in r["ambiguous_owner"]["goals"]]==["proposed","proposed"] for r in runs)}
 out={"schema_version":1,"raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"checks":checks,
  "finding":"Explicit identity preserves the intended interleaved lifecycle sequence; events with zero or multiple for_goal owners transition neither Goal.",
  "limits":"Fixture-level native rule semantics only; not thread concurrency, live action producer execution, performance, or general scheduler completeness."}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks},indent=2))
 if not all(checks.values()):raise SystemExit("capture analysis validity failed")
if __name__=="__main__":main()
