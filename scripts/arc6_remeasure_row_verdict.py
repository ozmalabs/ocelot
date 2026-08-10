#!/usr/bin/env python
"""arc6_remeasure_row_verdict — RE-RUN the row-verdict ceiling, on THIS engine.

This is the ONE runner the executor's route table knows (`seeds/arc_executor.json`
ships `ExecClass{name:"re_measure", runner:"arc6_remeasure_row_verdict"}`), and
it is MECHANICAL I/O end to end: it re-runs a measurement that already exists as
a script, on the current binary, and writes the result to a NEW path.  It makes
no decision — the decision that this is the job was the graph's collapse.

WHAT "RE-MEASURE" MEANS HERE, EXACTLY.  `results/arc6_verdict_pricing.json` was
produced by three existing scripts run in sequence on engine `48da7257f35d`:

    arc6_verdict_battery.py before          (baseline seed)
    arc6_verdict_patch.py apply
    arc6_verdict_battery.py after           (candidate seed)
    arc6_verdict_patch.py revert
    arc6_verdict_report.py                  (constructed-witness sweep)

Re-measuring it is running that same sequence on THIS binary.  Nothing is
re-implemented and nothing is approximated: the same three scripts run, in the
same order, with the same arguments.

FROZEN ARTIFACTS STAY BYTE-FROZEN.  `arc6_verdict_report.py` hard-codes its
input labels (`before`/`after`) and its output path, so this runner SAVES the
three committed artifacts and `seeds/program_synthesis.json` up front and
RESTORES them byte-for-byte in a `finally`, after moving the fresh pricing
report to `results/arc6_verdict_pricing_remeasure_<tag>.json`.  A run that dies
half way leaves the tree exactly as it found it — including the seed patch,
whose revert is in the same `finally`.

Run:  python scripts/arc6_remeasure_row_verdict.py <tag>
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
SCRIPTS = os.path.join(ROOT, "scripts")
PS_SEED = os.path.join(ROOT, "seeds", "program_synthesis.json")

#  Every file this runner is allowed to disturb, and which it restores.
PROTECTED = (
    os.path.join(RESULTS, "arc6_verdict_before.json"),
    os.path.join(RESULTS, "arc6_verdict_after.json"),
    os.path.join(RESULTS, "arc6_verdict_pricing.json"),
    PS_SEED,
)
PRICING = os.path.join(RESULTS, "arc6_verdict_pricing.json")


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _run(*argv: str) -> None:
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    env["PYTHONPATH"] = os.pathsep.join(
        [os.path.join(ROOT, "runners", "dsl", "python"), ROOT,
         env.get("PYTHONPATH", "")]).rstrip(os.pathsep)
    subprocess.run([sys.executable] + list(argv), cwd=ROOT, env=env, check=True)


def remeasure(tag: str) -> dict:
    """Run the five steps; return the fresh artifact's path + provenance."""
    out_path = os.path.join(RESULTS, "arc6_verdict_pricing_remeasure_%s.json" % tag)
    stash = tempfile.mkdtemp(prefix="arc6_remeasure_")
    before_shas = {}
    t0 = time.time()
    try:
        for p in PROTECTED:
            before_shas[p] = _sha256(p)
            shutil.copy2(p, os.path.join(stash, os.path.basename(p)))

        _run(os.path.join(SCRIPTS, "arc6_verdict_battery.py"), "before")
        _run(os.path.join(SCRIPTS, "arc6_verdict_patch.py"), "apply")
        try:
            _run(os.path.join(SCRIPTS, "arc6_verdict_battery.py"), "after")
        finally:
            _run(os.path.join(SCRIPTS, "arc6_verdict_patch.py"), "revert")
        _run(os.path.join(SCRIPTS, "arc6_verdict_report.py"))

        shutil.copy2(PRICING, out_path)
    finally:
        for p in PROTECTED:
            src = os.path.join(stash, os.path.basename(p))
            if os.path.exists(src):
                shutil.copy2(src, p)
        restored = {p: _sha256(p) for p in PROTECTED if os.path.exists(p)}
        shutil.rmtree(stash, ignore_errors=True)

    unchanged = all(restored.get(p) == before_shas.get(p) for p in PROTECTED)
    doc = json.load(open(out_path))
    return {
        "artifact": os.path.relpath(out_path, ROOT),
        "artifact_sha256": _sha256(out_path),
        "elapsed_seconds": round(time.time() - t0, 2),
        "engine_sha256": (doc.get("engine_provenance") or {}).get("sha256"),
        "protected_files_restored_byte_identical": unchanged,
        "protected_files": {os.path.relpath(p, ROOT): before_shas[p]
                            for p in PROTECTED},
    }


def main() -> None:
    tag = sys.argv[1] if len(sys.argv) > 1 else "manual"
    rec = remeasure(tag)
    print(json.dumps(rec, indent=2))


if __name__ == "__main__":
    main()
