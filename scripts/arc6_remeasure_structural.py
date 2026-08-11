#!/usr/bin/env python
"""arc6_remeasure_structural — RE-RUN the structural-ceiling residual, on THIS
engine.  The SECOND runner in the executor's capability table (A15, the
second-`ExecClass` ceiling probe:
`docs/research/program_synthesis/PROGRAM_SYNTHESIS_ARC6_SECOND_EXECCLASS.md`).
`seeds/arc_executor.json` ships a second `ExecClass{name:"re_measure",
runner:"arc6_remeasure_structural"}` row, keyed (like the first) on the
three-part cue (kind + evidence_artifact + source_rid), and this is MECHANICAL
I/O end to end: it re-runs a measurement that already exists as a script, on
the current binary, and writes the result to a NEW path.  It makes no
decision — the decision that this is the job was the graph's collapse.

WHAT "RE-MEASURE" MEANS HERE, EXACTLY.  `results/arc6_structural_ceiling.json`
is produced by ONE existing script, `scripts/arc6_structural_ceiling.py`,
with no argv and no seed patch/revert dance — unlike the row-verdict runner,
this residual is not an A/B comparison, it is a single ceiling measurement.
Re-measuring it is running that same script again, on THIS binary.  Nothing
is re-implemented and nothing is approximated.

FROZEN ARTIFACT STAYS BYTE-FROZEN.  `arc6_structural_ceiling.py` hard-codes
its own output path (`OUT = results/arc6_structural_ceiling.json`), so this
runner SAVES that one committed artifact up front and RESTORES it byte-for-
byte in a `finally`, after moving the fresh measurement to
`results/arc6_structural_ceiling_remeasure_<tag>.json`.  A run that dies half
way leaves the tree exactly as it found it — the SAME discipline
`arc6_remeasure_row_verdict.py` uses, sized to a one-script job.

A READ-ONLY DEPENDENCY, NAMED SO IT IS NEVER MISTAKEN FOR A WRITE ONE.
`arc6_structural_ceiling.py` itself READS
`results/arc6_a_ceiling.json::blocker_split.ids_over_live_unreached.
missing_structural_primitive` (an upstream ceiling) but never writes it.
This runner does not stash that file — there is nothing to restore — but it
DOES assert the file is present before running, because a KeyError deep
inside the measurement script from a missing upstream file is a worse
failure mode than a clean refusal at the boundary.

Run:  python scripts/arc6_remeasure_structural.py <tag>
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

#  The one file this runner is allowed to disturb, and which it restores.
PROTECTED = (
    os.path.join(RESULTS, "arc6_structural_ceiling.json"),
)
#  Read-only upstream input.  Never stashed (never written here); only
#  checked, so a missing dependency refuses cleanly instead of surfacing as a
#  KeyError from inside the measurement script.
UPSTREAM_READ_ONLY = os.path.join(RESULTS, "arc6_a_ceiling.json")


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
    """Run the one step; return the fresh artifact's path + provenance."""
    if not os.path.exists(UPSTREAM_READ_ONLY):
        raise RuntimeError(
            "arc6_remeasure_structural: upstream read-only dependency "
            "missing: %s (arc6_structural_ceiling.py reads it and would "
            "fail with a KeyError, not a clean refusal)" % UPSTREAM_READ_ONLY)

    out_path = os.path.join(
        RESULTS, "arc6_structural_ceiling_remeasure_%s.json" % tag)
    stash = tempfile.mkdtemp(prefix="arc6_remeasure_structural_")
    before_shas = {}
    t0 = time.time()
    try:
        for p in PROTECTED:
            before_shas[p] = _sha256(p)
            shutil.copy2(p, os.path.join(stash, os.path.basename(p)))

        _run(os.path.join(SCRIPTS, "arc6_structural_ceiling.py"))

        shutil.copy2(PROTECTED[0], out_path)
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
