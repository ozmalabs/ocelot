"""code_synthesis_baseline_build — P0 of PROGRAM_SYNTHESIS_PLAN.md: freeze the
ENUMERATED code-synthesis baseline as a LIST, never a count.

Measures, fresh, through the SAME code paths the CODE-CURRICULUM run used
(domains/code_curriculum.py's `scan_repo_functions` / `run_write_battery`,
`scripts/code_curriculum_run.py`'s WRITE_BATTERY — imported, never forked):

  * the full `domains/` scan: EVERY top-level function enumerated with its
    file, qualname, construction label, emittability, and predict outcome
    (the 2026-07-21 retraction rule: a baseline must be a list of ids, never
    a count — a count can be held; a list has to be read);
  * the exact list of Term-emittable functions (identity = file + qualname);
  * the frozen 26-item NL write battery with per-item outcome
    (ok / construction / failure-reason string);
  * the deterministic 2-file fixture corpus scan
    (tests/fixtures/code_curriculum/measurement_corpus) — the small live
    re-verification subset the gate re-runs.

Scan scope is `domains/` only, matching the curriculum run — `scripts/` is
documented pathologically slow for this scan (see
code_curriculum_run.baseline_measurement's measured scoping note).

Output: results/code_synthesis_baseline.json
Gate:   tests/test_code_synthesis_baseline_migrated.py

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
     OZMA_SEED_PERSIST_DISABLED=1 python3 scripts/code_synthesis_baseline_build.py
"""
from __future__ import annotations

import json
import os
import platform
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
          os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.boot_all import load_all_seeds             # noqa: E402
from domains import code_curriculum as cc                 # noqa: E402
from scripts.code_curriculum_run import WRITE_BATTERY     # noqa: E402

OUT_PATH = os.path.join(ROOT, "results", "code_synthesis_baseline.json")
SCAN_ROOTS = ["domains"]
FIXTURE_ROOT = "tests/fixtures/code_curriculum/measurement_corpus"


def _head_commit() -> str:
    """Resolve HEAD mechanically by file reads (never a git subprocess — a
    parallel agent shares this worktree). Walks .git file → gitdir → HEAD →
    ref, with packed-refs fallback."""
    d = ROOT
    gitdir = None
    while d != os.path.dirname(d):
        cand = os.path.join(d, ".git")
        if os.path.isdir(cand):
            gitdir = cand
            break
        if os.path.isfile(cand):
            line = open(cand).read().strip()
            if line.startswith("gitdir:"):
                gitdir = line.split(":", 1)[1].strip()
                if not os.path.isabs(gitdir):
                    gitdir = os.path.normpath(os.path.join(d, gitdir))
                break
        d = os.path.dirname(d)
    if gitdir is None:
        return "UNKNOWN"
    head = open(os.path.join(gitdir, "HEAD")).read().strip()
    if not head.startswith("ref:"):
        return head
    ref = head.split(":", 1)[1].strip()
    common = gitdir
    cd_file = os.path.join(gitdir, "commondir")
    if os.path.isfile(cd_file):
        cd = open(cd_file).read().strip()
        common = cd if os.path.isabs(cd) else os.path.normpath(os.path.join(gitdir, cd))
    ref_path = os.path.join(common, ref)
    if os.path.isfile(ref_path):
        return open(ref_path).read().strip()
    packed = os.path.join(common, "packed-refs")
    if os.path.isfile(packed):
        for line in open(packed):
            if line.strip().endswith(ref):
                return line.split()[0]
    return "UNKNOWN"


def _scan_functions(scan: dict) -> list[dict]:
    """One entry per top-level function, in the scan's own deterministic
    (sorted-path, document) order. qualname == name (scan_repo_functions
    enumerates top-level FunctionDefs only)."""
    return [{"file": row["file"], "qualname": row["name"],
             "construction": row["construction"],
             "emittable": bool(row["emittable"]),
             "predict_correct": row["predict_correct"]}
            for row in scan["rows"]]


def main() -> int:
    t0 = time.time()
    # TWO fresh agents, deliberately. The read codebook MINTS while it scans,
    # so labels are a function of (fresh boot, scan order). The gate's live
    # re-verification subset (battery + fixture corpus) must be measured
    # against FRESH-BOOT state — the state a re-verifying test can reproduce —
    # not against an agent already mutated by the 7k-function scan (measured:
    # the same fixture function labels `learned_code_import_return` after the
    # big scan vs `learned_code_while_return` fresh, the label the existing
    # curriculum gate pins). The full scan gets its own fresh agent, matching
    # code_curriculum_run.baseline_measurement's own conditions.
    print("== boot agent 1 (fresh, full seed set) — gate subset ==")
    a1 = WorldAdapter(seeds=())
    load_all_seeds(a1)

    print("== write battery (%d items, frozen) ==" % len(WRITE_BATTERY))
    battery = cc.run_write_battery(a1, WRITE_BATTERY)
    items = [{"request": r["request"], "ok": bool(r["ok"]),
              "construction": r["construction"],
              "reason": None if r["ok"] else str(r["reason"])}
             for r in battery["rows"]]
    print("  %d/%d ok" % (battery["n_ok"], battery["n"]))

    print("== fixture corpus scan: %s ==" % FIXTURE_ROOT)
    fscan = cc.scan_repo_functions(a1, [FIXTURE_ROOT])
    ffunctions = _scan_functions(fscan)
    print("  %d functions over %d files" % (fscan["n_functions"], fscan["n_files"]))

    print("== boot agent 2 (fresh, full seed set) — full scan ==")
    a2 = WorldAdapter(seeds=())
    load_all_seeds(a2)

    print("== scan: %s ==" % SCAN_ROOTS)
    scan = cc.scan_repo_functions(a2, SCAN_ROOTS)
    functions = _scan_functions(scan)
    emittable = [{"file": f["file"], "qualname": f["qualname"],
                  "construction": f["construction"]}
                 for f in functions if f["emittable"]]
    print("  %d functions over %d files; %d term-emittable; counts=%s"
          % (scan["n_functions"], scan["n_files"], len(emittable), scan["counts"]))

    data = {
        "_README": [
            "P0 ENUMERATED BASELINE for PROGRAM_SYNTHESIS_PLAN.md — a LIST, never a count",
            "(the 2026-07-21 retraction rule). Every total below is DERIVED from its list;",
            "the gate (tests/test_code_synthesis_baseline_migrated.py) rejects an authored one.",
            "Rebuild: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 "
            "OZMA_SEED_PERSIST_DISABLED=1 python3 scripts/code_synthesis_baseline_build.py",
        ],
        "head": _head_commit(),
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "engine": {
            "python": platform.python_version(),
            "substrate_rs": "prebuilt runners/dsl/python/substrate_rs/_native.abi3.so",
            "boot": "WorldAdapter(seeds=()) + load_all_seeds (full set)",
        },
        "condition": {
            "env": {"OZMA_NO_LLM": "1", "OZMA_SEED_PERSIST_DISABLED": "1"},
            "scan_scope": SCAN_ROOTS,
            "scan_scope_note": (
                "domains/ only, matching the CODE-CURRICULUM run: scripts/ is documented "
                "pathologically slow for this scan (code_curriculum_run.baseline_measurement). "
                "Eval-subset coverage is part of every claim built on this baseline."),
            "battery_source": "scripts/code_curriculum_run.py WRITE_BATTERY (imported, frozen)",
            "battery_path": "code_curriculum.run_write_battery -> "
                            "code_writing.write_function_from_request (never converse; "
                            "no gap filing, no conversation state)",
            "measurement_order": (
                "TWO fresh agents: agent1 (fresh boot) -> battery, then fixture "
                "scan; agent2 (fresh boot) -> full domains/ scan. The read "
                "codebook mints while scanning, so labels are a function of "
                "(fresh boot, sorted scan order); the gate's live subset is "
                "frozen at the fresh-boot state a test can reproduce."),
        },
        "scan": {
            "roots": SCAN_ROOTS,
            "n_files": scan["n_files"],
            "n_functions": len(functions),
            "counts": scan["counts"],
            "functions": functions,
        },
        "term_emittable": {
            "total": len(emittable),
            "entries": emittable,
        },
        "write_battery": {
            "n": len(items),
            "n_ok": sum(1 for i in items if i["ok"]),
            "items": items,
        },
        "fixture_scan": {
            "root": FIXTURE_ROOT,
            "n_files": fscan["n_files"],
            "n_functions": len(ffunctions),
            "functions": ffunctions,
        },
        "elapsed_seconds": round(time.time() - t0, 1),
        "loadavg": list(os.getloadavg()),
    }
    # internal consistency before writing — the builder must never author a count.
    assert data["scan"]["counts"]["term_emittable"] == len(emittable)
    assert data["scan"]["counts"]["parseable"] == len(functions)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(data, f, indent=1)
        f.write("\n")
    print("== written: %s (%.1fs) ==" % (OUT_PATH, data["elapsed_seconds"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
