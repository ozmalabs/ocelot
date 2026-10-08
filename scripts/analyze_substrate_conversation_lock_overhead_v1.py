#!/usr/bin/env python3
"""Independently validate and summarize paired lock-overhead timings."""
from __future__ import annotations
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_conversation_lock_overhead_v1_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/conversation_lock_overhead_v1_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_conversation_lock_overhead_v1_analysis_20260926.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def p90(values):return sorted(values)[int(.9*(len(values)-1))]
def main():
 raw=json.loads(RAW.read_text());locked=json.loads(LOCK.read_text())["locked_inputs"];pairs=raw["pairs_raw"]
 all_rows=[r for pair in pairs for r in pair["rows"]]
 guarded=[r["elapsed_ns"] for r in all_rows if r["condition"]=="guarded"];noop=[r["elapsed_ns"] for r in all_rows if r["condition"]=="noop"]
 deltas=[pair["paired_delta_ns"] for pair in pairs]
 checks={"raw_inputs_match_lock":raw["locked_inputs"]==locked,"lock_digest_matches":raw["lock_sha256"]==sha(LOCK),
  "source_stable":raw["post_run_inputs"]==locked==raw["started_inputs"]==raw["finished_inputs"],
  "twenty_complete_pairs":len(pairs)==20 and len(guarded)==20 and len(noop)==20 and all({r["condition"] for r in p["rows"]}=={"guarded","noop"} for p in pairs),
  "all_replies_match_baseline":raw["reply_parity"] and all(r["reply_matches_baseline"] for r in all_rows),
  "summary_reproduces":raw["summary"]["guarded_median_ns"]==statistics.median(guarded) and raw["summary"]["noop_median_ns"]==statistics.median(noop) and raw["summary"]["paired_delta_median_ns"]==statistics.median(deltas) and raw["summary"]["guarded_p90_ns"]==p90(guarded) and raw["summary"]["noop_p90_ns"]==p90(noop)}
 summary={"guarded_median_ns":statistics.median(guarded),"noop_median_ns":statistics.median(noop),"paired_delta_median_ns":statistics.median(deltas),"guarded_p90_ns":p90(guarded),"noop_p90_ns":p90(noop),"paired_delta_min_ns":min(deltas),"paired_delta_max_ns":max(deltas),"paired_deltas_ns":deltas}
 out={"schema_version":1,"raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"checks":checks,"summary":summary,"interpretation_limit":"Sequential same-adapter repeated-turn sample; the no-op context manager is a control for lock acquisition/wrapper cost, not an alternative supported API. Graph state evolves during pairs. Does not measure concurrency throughput or other routes."}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks,"summary":summary},indent=2))
 if not all(checks.values()):raise SystemExit("overhead capture analysis failed")
if __name__=="__main__":main()
