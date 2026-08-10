#!/usr/bin/env python3
"""arc6_valuelayer_sweep — per-file test sweep that WORKS IN A WORKTREE.

Same shape as `scripts/failure_baseline_sweep.py` (per-file subprocess, a
LIST of node ids and never a count, a timeout is NOT_ESTABLISHED and never
a red, `COLUMNS=250` so `-rfE` lines are not amputated at 80) with ONE
correction that is load-bearing here and nowhere else:

    **`--confcutdir=<this tree>`**

This worktree is nested inside the canonical repo, so without it pytest
walks up, loads the PARENT tree's `conftest.py`, and every module collapses
to `ImportError: cannot import name 'prog_synthesis' from 'domains'
(/home/matt/.../gamma-substrate/domains/__init__.py)` — the parent's
`domains`, not this tree's. Measured here: the shared sweep script reports
`tests/test_arc6_valuelayer_migrated.py` RED, and the same file is 34/34
green with the flag. **In a worktree the shared instrument reports a red
for essentially every file, and none of them are reds.**

The shared script is deliberately NOT modified: it is the instrument the
frozen `results/failure_baseline.json` gate was measured with.

  python scripts/arc6_valuelayer_sweep.py --out results/x.json [--files-from f]
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
_SUMMARY = re.compile(r"^(FAILED|ERROR)\s+(\S+)(?:\s+-\s+(.*))?$")


def sweep_one(path: str, timeout: int) -> dict:
    t0 = time.time()
    env = dict(os.environ, COLUMNS="250", OZMA_NO_LLM="1",
               OZMA_SEED_PERSIST_DISABLED="1")
    env["PYTHONPATH"] = os.pathsep.join(
        [str(ROOT / "runners" / "dsl" / "python"), str(ROOT), str(ROOT / "scripts")]
        + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
    try:
        r = subprocess.run(
            [sys.executable, "-W", "ignore", "-m", "pytest", "-q", "-p", "no:randomly",
             "--confcutdir=%s" % ROOT, "--tb=no", "-rfE", path],
            cwd=ROOT, capture_output=True, text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return {"file": path, "status": "NOT_ESTABLISHED",
                "reason": f"exceeded {timeout}s budget (NOT a red)",
                "seconds": round(time.time() - t0, 1), "nodes": []}
    out = r.stdout + r.stderr
    nodes = []
    for line in out.splitlines():
        m = _SUMMARY.match(line.strip())
        if m:
            nodes.append({"node": m.group(2), "kind": m.group(1),
                          "message": (m.group(3) or "").strip()[:400]})
    status = "GREEN" if not nodes and r.returncode == 0 else (
        "RED" if nodes else "NONZERO_NO_NODES")
    return {"file": path, "status": status, "returncode": r.returncode,
            "seconds": round(time.time() - t0, 1), "nodes": nodes,
            "tail": "" if status == "GREEN" else out.strip()[-600:]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--out", required=True)
    ap.add_argument("--glob", default="tests/test_*.py")
    ap.add_argument("--files-from", default=None)
    args = ap.parse_args()

    if args.files_from:
        files = [ln.strip() for ln in Path(args.files_from).read_text().splitlines()
                 if ln.strip()]
    else:
        files = sorted(str(p.relative_to(ROOT)) for p in ROOT.glob(args.glob))
    t0 = time.time()
    results = []
    # as_completed order, so a slow file cannot hide the progress of fast ones
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(sweep_one, f, args.timeout): f for f in files}
        from concurrent.futures import as_completed
        for i, fut in enumerate(as_completed(futs), 1):
            res = fut.result()
            results.append(res)
            print(f"[{i}/{len(files)}] {res['status']:16s} {res['seconds']:7.1f}s "
                  f"{res['file']}", flush=True)
            # write incrementally: a killed sweep still leaves a usable LIST
            (ROOT / args.out).write_text(json.dumps({
                "engine_sha256": _engine_sha(),
                "files_requested": len(files), "files_done": len(results),
                "workers": args.workers, "per_file_timeout_s": args.timeout,
                "wall_s": round(time.time() - t0, 1), "results": results}, indent=1))
    print(f"== wrote {args.out}")
    return 0


def _engine_sha() -> str:
    import hashlib
    p = ROOT / "runners" / "dsl" / "python" / "substrate_rs" / "_native.abi3.so"
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
