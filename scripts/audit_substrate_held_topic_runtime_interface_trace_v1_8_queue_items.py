#!/usr/bin/env python3
"""Independent queue-item applicability audit for the v1.8 whole-worker trace."""
from __future__ import annotations
import collections, gzip, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STEM="held_topic_runtime_interface_trace_v1_8_20261001"
CAP=ROOT/f"evaluation/reports/{STEM}/capture.json.gz"
LOCK=ROOT/f"evaluation/substrate_capability/{STEM}_lock.json"
OUT=ROOT/f"evaluation/reports/{STEM}/queue_item_audit_v1.json"

def sha(path:Path)->str:
 return "sha256:"+hashlib.sha256(path.read_bytes()).hexdigest()

def main()->None:
 capture=json.loads(gzip.decompress(CAP.read_bytes()))
 lock=json.loads(LOCK.read_text())
 worker_rows=[]
 for worker in capture["workers"]:
  rows=worker["payload"]["worker_operation_work_trace"]["rows"]
  counts=collections.Counter()
  for row in rows:
   if row["kind"].startswith("deferred_queue_"):
    counts[(row["kind"],row.get("subject"))]+=int(row["units"])
  worker_rows.append({"replicate":worker["payload"]["replicate"],"queue_work":[
   {"kind":kind,"family_code":family,"units":units}
   for (kind,family),units in sorted(counts.items(),key=lambda item:str(item[0]))]})
 item_kinds={"deferred_queue_enqueue_items","deferred_queue_drained_items"}
 item_rows=[row for worker in worker_rows for row in worker["queue_work"] if row["kind"] in item_kinds]
 all_queue_rows=[row for worker in worker_rows for row in worker["queue_work"]]
 result={"schema":"HeldTopicDeferredQueueItemAuditV1","capture_sha256":sha(CAP),
  "capture_lock_sha256":sha(LOCK),"locked_native_extension_sha256":lock["native_extension_sha256"],
  "worker_count":len(worker_rows),"workers":worker_rows,
  "enqueue_item_events_observed":sum(row["units"] for row in all_queue_rows if row["kind"]=="deferred_queue_enqueue_items"),
  "drained_item_events_observed":sum(row["units"] for row in all_queue_rows if row["kind"]=="deferred_queue_drained_items"),
  "drain_batch_events_observed":sum(row["units"] for row in all_queue_rows if row["kind"]=="deferred_queue_drain_batches"),
  "queue_item_flow_exercised":bool(item_rows),
  "queue_item_balance_status":"not_evaluated_no_enqueue_or_drained_item_rows" if not item_rows else "item_rows_present_review_family_counts",
  "scope_limit":"This capture measures deferred queue work on one seven-turn held-topic route. Empty drain batches do not demonstrate enqueue/drain item accounting or general deferred-queue correctness."}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"audit":str(OUT.relative_to(ROOT)),"queue_item_flow_exercised":result["queue_item_flow_exercised"],
  "enqueue_item_events_observed":result["enqueue_item_events_observed"],
  "drained_item_events_observed":result["drained_item_events_observed"],
  "drain_batch_events_observed":result["drain_batch_events_observed"]},indent=2))

if __name__=="__main__":main()
