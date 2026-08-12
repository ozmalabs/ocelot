#!/usr/bin/env python3
"""Merge SHARDED `failure_baseline_sweep.py` outputs into ONE raw payload that
`scripts/failure_baseline.py build` consumes unchanged.

WHY SHARD AT ALL (red-test triage, 2026-08-12). The sweep reports through
`ThreadPoolExecutor.map`, which yields IN SUBMISSION ORDER: one pathological
file blocks every completed result behind it, and a 1092-file sweep looked
stalled at 12/1092 for six minutes while five workers were in fact well past
it. Worse, the whole run writes its artifact only at the end, so an abort
loses everything measured. N single-worker shards over an interleaved split
fix both: each shard lands its own artifact as it finishes, and progress is
readable per shard.

    for i in $(seq -w 0 11); do
      python3 scripts/failure_baseline_sweep.py --workers 1 \
        --files-from shard_$i.txt --out results/sweep_$i.json &
    done
    python3 scripts/failure_baseline_merge.py 'results/sweep_*.json' results/raw.json
    python3 scripts/failure_baseline.py build --raw results/raw.json \
        --condition '...'

`head` must AGREE across shards — a merge of two tree states is not a
measurement, and the assert below is what makes that unmissable."""
import glob
import json
import sys
from pathlib import Path

pat, out = sys.argv[1], sys.argv[2]
paths = sorted(glob.glob(pat))
results, heads, ws, to = [], set(), set(), set()
la_start, la_end, wall = None, None, 0.0
for p in paths:
    d = json.loads(Path(p).read_text())
    results.extend(d["results"])
    heads.add(d["head"])
    ws.add(d["workers"])
    to.add(d["per_file_timeout_s"])
    la_start = la_start or d["loadavg_start"]
    la_end = d["loadavg_end"]
    wall = max(wall, d["wall_s"])
assert len(heads) == 1, heads
results.sort(key=lambda r: r["file"])
payload = {
    "head": heads.pop(),
    "files": len(results),
    "workers": f"{len(paths)} shards x {sorted(ws)} worker",
    "per_file_timeout_s": sorted(to)[0],
    "loadavg_start": la_start,
    "loadavg_end": la_end,
    "wall_s": wall,
    "shards": len(paths),
    "results": results,
}
Path(out).write_text(json.dumps(payload, indent=1))
n_red = sum(1 for r in results if r["status"] == "RED")
print(f"merged {len(paths)} shards -> {out}: {len(results)} files, {n_red} RED, "
      f"{sum(len(r['nodes']) for r in results)} node ids")
