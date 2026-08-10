"""Q-B: LIVE RUNTIME EXPOSURE of the four largest static race consumers.

`impasse_escalation` (41 race-constructible pairs -- the largest), `goal_derivation`
(23), `nav_intent` (20) and `grid_navigation` (16) were named as entirely
unmeasured. Executing the selection rule showed WHY: none of the 95
result-producing scripts boots any of them, so they have NO LANDED NUMBER that
could move. That makes them a DIFFERENT question, asked here and never conflated
with the landed-number question (Q-A):

    does the defect actually FIRE in the agent's live nav / escalation path?

Method: find every module that names one of the four seeds (AST-free literal
search is fine here -- this is SELECTION of candidates to RUN, and every
candidate is then actually executed; a false positive costs a run, not a claim),
execute it under the REVERTED+counter engine with a timeout, and read
HARMFUL_SKIPS in-process.

A script that fails or times out is reported NOT RUN -- never as zero exposure.
That distinction is the whole point: "the defect did not fire" and "I could not
run it" are different facts, and only the first is a measurement.
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
SEEDS = ["impasse_escalation", "goal_derivation", "nav_intent", "grid_navigation"]
TIMEOUT = 180


def candidates():
    out = {}
    # EXCLUDE THIS FILE AND ITS HARNESS SIBLINGS. The first version matched its
    # OWN source (it names all four seeds in its docstring) and duly executed
    # itself -- a selector that matches itself, the trap PROTOCOL S12 names.
    _self = {"fixpoint_coverage_qb.py", "fixpoint_coverage_run.py",
             "fixpoint_coverage_wrap.py", "fixpoint_coverage_compare.py",
             "fixpoint_coverage_select.py"}
    for p in sorted(list((ROOT / "scripts").glob("*.py"))):
        if p.name in _self:
            continue
        try:
            src = p.read_text(errors="replace")
        except OSError:
            continue
        hit = [s for s in SEEDS if re.search(rf'["\']{s}["\']', src)]
        if hit:
            out[p.name] = hit
    return out


def main():
    outdir = pathlib.Path(sys.argv[1]); outdir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT}:{ROOT / 'runners' / 'dsl' / 'python'}"

    engine = subprocess.run(
        [sys.executable, "-c",
         "import sys;sys.path.insert(0,'.');"
         "from domains.engine_provenance import provenance_line;print(provenance_line())"],
        cwd=ROOT, env=env, capture_output=True, text=True).stdout.strip()

    cands = candidates()
    records = []
    for i, (name, seeds) in enumerate(sorted(cands.items()), 1):
        ctr = outdir / f"_ctr_{name}.json"
        t0 = time.time()
        try:
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "fixpoint_coverage_wrap.py"),
                 str(ROOT / "scripts" / name), str(ctr)],
                cwd=ROOT, env=env, capture_output=True, text=True, timeout=TIMEOUT)
            rc, tail = proc.returncode, (proc.stderr or "")[-300:]
        except subprocess.TimeoutExpired:
            rc, tail = "TIMEOUT", f"exceeded {TIMEOUT}s"
        wall = time.time() - t0

        counters = {}
        if ctr.exists():
            try:
                counters = json.loads(ctr.read_text())
            except json.JSONDecodeError:
                pass
            ctr.unlink()

        hs = counters.get("harmful_skips")
        records.append({
            "script": name, "seeds_named": seeds, "rc": rc,
            "harmful_skips": hs if rc == 0 else None,
            "run_rules_calls": counters.get("run_rules_calls") if rc == 0 else None,
            "measured": rc == 0,
            "reason_not_run": None if rc == 0 else f"rc={rc}",
            "wall_s_CONTAMINABLE": round(wall, 2),
            "stderr_tail": "" if rc == 0 else tail,
        })
        print(f"[{i}/{len(cands)}] {name:44} rc={str(rc):8} skips={hs} "
              f"{'/'.join(seeds)}", flush=True)
        (outdir / "qb_index.json").write_text(json.dumps(
            {"engine": engine, "timeout_s": TIMEOUT, "seeds": SEEDS,
             "n_candidates": len(cands), "records": records}, indent=1))

    ok = [r for r in records if r["measured"]]
    print(f"\nQ-B: {len(ok)}/{len(records)} candidates actually ran. engine: {engine}")
    for s in SEEDS:
        rs = [r for r in ok if s in r["seeds_named"]]
        tot = sum(r["harmful_skips"] or 0 for r in rs)
        print(f"  {s:22} ran={len(rs):2}  total_harmful_skips={tot}")


if __name__ == "__main__":
    main()
