#!/usr/bin/env python3
"""Independent source and semantic audit of concurrent CoW lifecycle data."""
from __future__ import annotations
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CAPTURE=ROOT/"evaluation/reports/cow_concurrent_branch_lifecycle_v1.json"
RUNNER="evaluation/substrate_capability/cow_concurrent_branch_lifecycle_v1.py"
ANALYZER="scripts/analyze_cow_concurrent_branch_lifecycle_v1.py"
def sha(path):return "sha256:"+hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
 d=json.loads(CAPTURE.read_text())
 if d.get("schema")!="CowConcurrentBranchLifecycleCaptureV1":raise SystemExit("bad capture schema")
 if d["source_sha256"].get(RUNNER)!=sha(ROOT/RUNNER):raise SystemExit("runner hash mismatch")
 if d["source_sha256"].get(ANALYZER)!=sha(ROOT/ANALYZER):raise SystemExit("analyzer hash mismatch")
 for name,want in d["source_sha256"].items():
  if sha(ROOT/name)!=want:raise SystemExit(f"source changed: {name}")
 binary=Path(d["probe_binary"]["path"])
 if binary.exists() and sha(binary)!=d["probe_binary"]["sha256"]:raise SystemExit("probe binary changed")
 rows=d["measurements"]["rows"]
 if len(rows)!=60:raise SystemExit(f"expected 60 rows, got {len(rows)}")
 semantic=("all_semantics_pass","primary_unchanged","all_live_bytes_increased","cancel_reduced_live_bytes","mutation_adjusted_reclamation_pass")
 if not all(all(r.get(k) is True for k in semantic) and r["mutation_adjusted_after_drop_bytes"]==0 for r in rows):
  raise SystemExit("one or more semantic/allocation lifecycle gates failed")
 cells=[]
 for n in (10000,50000):
  for fanout in (1,4,16):
   pair={}
   for backend in ("shared_snapshot","eager_copy"):
    cell=[r for r in rows if r["size_nodes"]==n and r["fanout"]==fanout and r["backend"]==backend]
    if len(cell)!=5:raise SystemExit(f"repeat count mismatch: {n=} {fanout=} {backend=}")
    pair[backend]=cell
   for i in range(5):
    a,b=pair["shared_snapshot"][i],pair["eager_copy"][i]
    if a["repeat"]!=b["repeat"]:raise SystemExit("paired repeat mismatch")
    if a["branch_added_ids"]!=b["branch_added_ids"]:raise SystemExit("backend branch allocation/outcome parity mismatch")
    if (a["all_semantics_pass"],a["primary_unchanged"])!=(b["all_semantics_pass"],b["primary_unchanged"]):
     raise SystemExit("backend semantic parity mismatch")
   cells.append({"size_nodes":n,"fanout":fanout,"repeats":5,
    "shared_snapshot_median_us":statistics.median(r["wave_wall_us"] for r in pair["shared_snapshot"]),
    "eager_copy_median_us":statistics.median(r["wave_wall_us"] for r in pair["eager_copy"]),
    "shared_snapshot_all_live_delta_median_bytes":statistics.median(r["all_live_delta_bytes"] for r in pair["shared_snapshot"]),
    "eager_copy_all_live_delta_median_bytes":statistics.median(r["all_live_delta_bytes"] for r in pair["eager_copy"]),
    "shared_snapshot_after_cancel_delta_median_bytes":statistics.median(r["after_cancel_delta_bytes"] for r in pair["shared_snapshot"]),
    "eager_copy_after_cancel_delta_median_bytes":statistics.median(r["after_cancel_delta_bytes"] for r in pair["eager_copy"]),
    "fork_control_delta_shared_median_bytes":statistics.median(r["fork_only_control_after_drop_delta_bytes"] for r in pair["shared_snapshot"]),
    "fork_control_delta_eager_median_bytes":statistics.median(r["fork_only_control_after_drop_delta_bytes"] for r in pair["eager_copy"]),
    "adjusted_post_drop_residual_max_abs_bytes":max(abs(r["mutation_adjusted_after_drop_bytes"]) for arm in pair.values() for r in arm),
    "all_gates_pass":True})
 out={"schema":"CowConcurrentBranchLifecycleAnalysisV1","capture":str(CAPTURE),"worker_rows":len(rows),
  "cell_count":len(cells),"all_semantic_and_adjusted_reclamation_gates_pass":True,
  "cells":cells,"claim_boundary":"concurrent native Substrate branch lifecycle and requested Rust allocation bytes; not general performance, serving, or KV-cache evidence"}
 dest=ROOT/"evaluation/reports/cow_concurrent_branch_lifecycle_v1_analysis.json"
 dest.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"rows":len(rows),"cells":len(cells),"all_gates_pass":True,"analysis":str(dest.relative_to(ROOT))},sort_keys=True))
if __name__=="__main__":main()
