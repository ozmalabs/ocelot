"""ARM RUNNER for the fixpoint coverage sweep (seeds 98000-98999).

Runs every SELECTED script (see `fixpoint_coverage_select.py` -- the rule is
executed, never hand-listed) and captures, per script:

  * exit code and wall time;
  * the engine's HARMFUL_SKIPS / run_rules call counts, read in-process;
  * every `results/*.json` the script ACTUALLY REWROTE, attributed by a
    before/after mtime snapshot of the whole directory.

THE INHERITED DEFECT, EXPLICITLY NOT INHERITED. The predecessor's runner copied
`results/*.json` even when the script FAILED, so a failed run would have compared
identical-to-committed and counted as coverage. Here an artifact is captured only
when BOTH hold:

    rc == 0                        (the script succeeded), AND
    the file's MTIME changed       (the script actually touched it this run)

Everything else is recorded as an explicit NOT_RUN with a reason. A stale
committed file is never evidence.

Attribution is by SNAPSHOT, not by the selector's doc->script map: that map
over-maps (a script that merely READS results/X.json matches the literal). The
map selects WHICH scripts to run; the snapshot decides WHAT each one produced.
Consequence: scripts must run SEQUENTIALLY, or two concurrent writers would be
cross-attributed.

Usage:  python3 scripts/fixpoint_coverage_run.py <arm-name> <outdir> [--limit N]
"""
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
TIMEOUT = 600


def snapshot():
    """(mtime_ns, content hash) of every results/*.json.

    ATTRIBUTION IS BY MTIME, NOT BY CONTENT. A first version of this keyed
    capture on the CONTENT hash and was WRONG in a way that would have silently
    destroyed the result: a DETERMINISTIC script re-run writes identical bytes,
    so "content changed" is false, so the document would have been recorded as
    never produced. Since byte-identity between arms is precisely what this rung
    MEASURES, using it as the CAPTURE criterion discards every unmoved document
    -- i.e. it throws away the null and keeps only the movers. Caught when a
    script that captured 1 doc in the smoke run captured 0 on a re-run.

    "Rewritten" therefore means the script TOUCHED the file during this run.
    """
    out = {}
    for p in sorted(RESULTS.glob("*.json")):
        try:
            st = p.stat()
            out[p.name] = (st.st_mtime_ns, hashlib.sha256(p.read_bytes()).hexdigest())
        except OSError:
            pass
    return out


def selected_scripts():
    sel = json.loads(subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "fixpoint_coverage_select.py"), str(ROOT)],
        capture_output=True, text=True, check=True).stdout)
    return sorted({s for v in sel["mapped"].values() for s in v}), sel


def main():
    arm = sys.argv[1]
    outdir = pathlib.Path(sys.argv[2]); outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "docs").mkdir(exist_ok=True)
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    scripts, sel = selected_scripts()
    if limit:
        scripts = scripts[:limit]

    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT}:{ROOT / 'runners' / 'dsl' / 'python'}"

    engine = subprocess.run(
        [sys.executable, "-c",
         "import sys;sys.path.insert(0,'.');"
         "from domains.engine_provenance import provenance_line;print(provenance_line())"],
        cwd=ROOT, env=env, capture_output=True, text=True).stdout.strip()

    records = []
    for i, name in enumerate(scripts, 1):
        ctr = outdir / f"_ctr_{name}.json"
        before = snapshot()
        t0 = time.time()
        try:
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "fixpoint_coverage_wrap.py"),
                 str(ROOT / "scripts" / name), str(ctr)],
                cwd=ROOT, env=env, capture_output=True, text=True, timeout=TIMEOUT)
            rc, tail = proc.returncode, (proc.stderr or "")[-400:]
        except subprocess.TimeoutExpired:
            rc, tail = "TIMEOUT", f"exceeded {TIMEOUT}s"
        wall = time.time() - t0
        after = snapshot()

        counters = {}
        if ctr.exists():
            try:
                counters = json.loads(ctr.read_text())
            except json.JSONDecodeError:
                pass
            ctr.unlink()

        # mtime-based: the script TOUCHED it this run (see snapshot()).
        changed = sorted(d for d in after
                         if before.get(d, (None, None))[0] != after[d][0])
        # content-identity is REPORTED, never used to decide capture
        rewritten_same_bytes = sorted(
            d for d in changed
            if before.get(d, (None, None))[1] == after[d][1])

        captured, not_run = [], []
        for d in changed:
            if rc == 0:
                shutil.copy2(RESULTS / d, outdir / "docs" / d)
                captured.append(d)
            else:
                not_run.append({"doc": d, "reason": f"rc={rc}"})

        rec = {
            "script": name,
            "rc": rc,
            "wall_s_CONTAMINABLE": round(wall, 2),
            "harmful_skips": counters.get("harmful_skips"),
            "run_rules_calls": counters.get("run_rules_calls"),
            "docs_captured": captured,
            "docs_not_run": not_run,
            "n_docs_rewritten": len(changed),
            "n_rewritten_identical_bytes": len(rewritten_same_bytes),
            "stderr_tail": tail if rc != 0 else "",
        }
        records.append(rec)
        print(f"[{i}/{len(scripts)}] {name:46} rc={str(rc):8} "
              f"skips={counters.get('harmful_skips')} docs={len(captured)} "
              f"{wall:.1f}s", flush=True)

        (outdir / "index.json").write_text(json.dumps(
            {"arm": arm, "engine": engine, "timeout_s": TIMEOUT,
             "n_selected": len(scripts), "records": records}, indent=1))

    print(f"\nARM {arm} done. engine: {engine}")


if __name__ == "__main__":
    main()
