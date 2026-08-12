#!/usr/bin/env python3
"""Tree-wide per-file sweep that produces THE LIST — the node ids a baseline licenses.

WHY THIS EXISTS (VISION_GATE_SCOPE_B_RESULTS.md §10): the tree's baseline convention is a
COUNT ("held the bench at the exact pre-existing 19-failure baseline"). A count matches the
SHAPE of the answer without touching its CONTENT — the same defect as a substring selector,
one level up. 19 became 144 with nobody negligent, because a count cannot distinguish a new
red from an old one, and cannot notice when an entry is FIXED.

THE OUTPUT IS A LIST OF NODE IDS, and `results/failure_baseline.json` carries an explicit
COVERAGE block: every file that did not complete inside its budget is recorded
NOT_ESTABLISHED, never green and never red (§1.9-proposed — a wall-clock cutoff is an
authored constant on the measurement path, and reading an exit-124 as a RED already
manufactured one false failure in this tree).

CPU DISCIPLINE: default 2 workers. Load average is recorded with the result.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# pytest short-summary lines: "FAILED tests/x.py::test_y - AssertionError: ..."
#
# `(\S+)` FOR THE NODE ID SILENTLY DROPPED REDS, and it is the instrument
# mis-recording the thing it exists to record (the same disease as the COLUMNS=80
# truncation below). A PARAMETRIZED TEST ID CAN CONTAIN A SPACE —
# `test_tracked[OLD SULTAN-leads0]` is real, in tests/test_deep_comprehension.py —
# and `\S+` stops at that space, after which the ` - ` alternation no longer
# matches, so the WHOLE LINE was discarded and the file was filed
# NONZERO_NO_NODES: exit 1, no node ids, a red that a LIST cannot enumerate. The
# node id is therefore everything up to the FIRST ` - `, which is where pytest
# puts the separator.
_SUMMARY = re.compile(r"^(FAILED|ERROR)\s+(.+?)(?:\s+-\s+(.*))?$")


def sweep_one(path: str, timeout: int) -> dict:
    """Run ONE test file in its own process. Never interprets a timeout as a failure.

    `COLUMNS` IS LOAD-BEARING AND ITS ABSENCE COST A WHOLE SWEEP. pytest truncates its
    `-rfE` short-summary lines to the terminal width, and a captured (non-tty) pipe
    reports 80. The first run of this sweep therefore harvested 648 files' worth of
    correct NODE IDS attached to messages like `As...` and `Ass...`, and 472 entries
    with no message at all — so every entry classified UNCLASSIFIED, in the artifact
    whose own gate requires a class. The node ids were never wrong; the DIAGNOSIS was
    silently amputated at column 80.
    """
    t0 = time.time()
    env = dict(os.environ, COLUMNS="250")
    try:
        r = subprocess.run(
            [sys.executable, "-W", "ignore", "-m", "pytest", "-q", "-p", "no:randomly",
             "--tb=no", "-rfE", path],
            cwd=ROOT, capture_output=True, text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return {"file": path, "status": "NOT_ESTABLISHED",
                "reason": f"exceeded {timeout}s budget (NOT a red — protocol 1.9)",
                "seconds": round(time.time() - t0, 1), "nodes": []}
    out = r.stdout + r.stderr
    nodes = []
    for line in out.splitlines():
        m = _SUMMARY.match(line.strip())
        if m:
            nodes.append({"node": m.group(2), "kind": m.group(1),
                          "message": (m.group(3) or "").strip()[:400]})
    # EXIT 5 IS "no tests ran", and a file whose every test SKIPPED exits 5. That
    # is not a red and not an unexplained nonzero — it is the CORRECT outcome of an
    # honest guard (an absent optional dependency, an unresolvable provenance pin),
    # and filing it as NONZERO_NO_NODES makes the (b)-class fix look like a new
    # anomaly. Named as its own status so a reader can see how much of the tree is
    # guarded rather than measured.
    all_skipped = (not nodes and r.returncode == 5
                   and re.search(r"\d+ skipped", out) is not None)
    status = "ALL_SKIPPED" if all_skipped else (
        "GREEN" if not nodes and r.returncode == 0 else (
            "RED" if nodes else "NONZERO_NO_NODES"))
    return {"file": path, "status": status, "returncode": r.returncode,
            "seconds": round(time.time() - t0, 1), "nodes": nodes,
            "tail": "" if status in ("GREEN", "ALL_SKIPPED") else out.strip()[-600:]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=420)
    ap.add_argument("--out", default="results/failure_baseline_sweep_raw.json")
    ap.add_argument("--glob", default="tests/test_*.py")
    ap.add_argument("--files-from", default=None,
                    help="newline-delimited file list; re-measures a named subset "
                         "(also a REPRODUCIBILITY check on the previous verdict)")
    args = ap.parse_args()

    if args.files_from:
        files = [ln.strip() for ln in Path(args.files_from).read_text().splitlines()
                 if ln.strip()]
    else:
        files = sorted(str(p.relative_to(ROOT)) for p in ROOT.glob(args.glob))
    load_start = os.getloadavg()
    t0 = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for i, res in enumerate(ex.map(lambda f: sweep_one(f, args.timeout), files), 1):
            results.append(res)
            print(f"[{i}/{len(files)}] {res['status']:16s} {res['seconds']:7.1f}s "
                  f"{res['file']}", flush=True)

    payload = {
        "head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                               capture_output=True, text=True).stdout.strip(),
        "files": len(files),
        "workers": args.workers,
        "per_file_timeout_s": args.timeout,
        "loadavg_start": load_start,
        "loadavg_end": os.getloadavg(),
        "wall_s": round(time.time() - t0, 1),
        "results": results,
    }
    (ROOT / args.out).write_text(json.dumps(payload, indent=1))
    print(f"== wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
