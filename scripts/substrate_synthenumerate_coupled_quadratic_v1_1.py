#!/usr/bin/env python3
"""Locked bounded nonlinear-map induction through native SynthEnumerate."""
from __future__ import annotations
import hashlib, json, platform, random, resource, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
from domains.engine_provenance import engine_preamble, engine_provenance, provenance_line
engine_preamble()
import substrate_rs as srs
from domains.prog_synthesis import _wire_rows

STEM = "synthenumerate_coupled_quadratic_v1_1_20261005"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_SYNTHENUMERATE_COUPLED_QUADRATIC_V1_1_AMENDMENT_20261005.md"
LOCK = ROOT / f"evaluation/substrate_capability/{STEM}_lock.json"
RAW = ROOT / f"evaluation/reports/{STEM}_raw.jsonl"
ANALYZER = ROOT / "scripts/analyze_substrate_synthenumerate_coupled_quadratic_v1_1.py"
NATIVE = Path(srs._native.__file__).resolve()
REPEATS, CANDIDATE_CAP, SCHEDULE_SEED = 10, 150_000, 20261005
REUSE_COUNTS = (1, 2, 5, 100)

TASKS = {
    "linear_control": {"formula": "(r+c,2*c)", "train": [(0,0),(1,0),(0,1),(1,1),(0,2),(1,2)],
                       "heldout": [(0,3),(2,3),(1,4),(4,4),(2,5),(5,5)]},
    "coupled_quadratic": {"formula": "(r+r*c,c+r*r)", "train": [(0,0),(1,0),(0,1),(1,1),(0,2),(1,2)],
                           "heldout": [(0,0),(2,0),(0,2),(2,2),(1,3),(3,3)]},
}
GRAMMARS = {
    "plus_tuple": {"ops": ["Plus", "TupleOf"], "consts": [], "max_size": 11},
    "plus_times_tuple": {"ops": ["Plus", "Times", "TupleOf"], "consts": [], "max_size": 11},
}
PAIRS = (("linear_control", "plus_tuple"), ("coupled_quadratic", "plus_tuple"),
         ("coupled_quadratic", "plus_times_tuple"))
SOURCE_PATHS = ("domains/prog_synthesis.py", "domains/engine_provenance.py", "runners/dsl/src/synth_enumerate.rs",
                "runners/dsl/src/term.rs", "runners/dsl/src/persist.rs", "runners/dsl/src/py.rs",
                "runners/dsl/python/substrate_rs/__init__.py", "runners/dsl/python/substrate_rs/_native.build.json")

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()

def target(task, r, c):
    if task == "linear_control": return (r + c, 2*c)
    if task == "coupled_quadratic": return (r + r*c, c + r*r)
    raise KeyError(task)

def lock_body():
    cases = []
    for task, grammar in PAIRS:
        t = TASKS[task]
        g = GRAMMARS[grammar]
        train = [{"inputs": {"r": r, "c": c}, "output": target(task, r, c)} for r,c in t["train"]]
        heldout = [{"inputs": {"r": r, "c": c}, "output": target(task, r, c)} for r,c in t["heldout"]]
        cases.append({"task": task, "grammar": grammar, "training": train, "heldout": heldout,
                      "ops": g["ops"], "constants": g["consts"], "max_size": g["max_size"],
                      "max_candidates": CANDIDATE_CAP, "repetitions": REPEATS})
    return {"schema": 1, "protocol": STEM, "tasks": TASKS, "grammars": GRAMMARS,
            "registered_pairs": [list(p) for p in PAIRS], "cases": cases,
            "candidate_cap": CANDIDATE_CAP, "repetitions": REPEATS,
            "schedule_seed": SCHEDULE_SEED, "reuse_counts": list(REUSE_COUNTS)}

def lock_payload():
    return {"protocol_sha256": sha(PROTOCOL), "runner_sha256": sha(__file__),
            "analyzer_sha256": sha(ANALYZER), "source_sha256": {p: sha(ROOT/p) for p in SOURCE_PATHS},
            "native_extension": {"path": str(NATIVE), "sha256": sha(NATIVE)},
            "engine_provenance": engine_provenance(), "inputs": lock_body()}

def check_lock(write=False):
    payload = json.loads(json.dumps(lock_payload(), sort_keys=True))
    if write:
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        print(f"locked {LOCK}"); return payload
    if not LOCK.exists() or json.loads(LOCK.read_text()) != payload:
        raise SystemExit("missing or stale source/input lock; preserve prior artifacts and create a versioned amendment")
    return payload

def synth_term(case):
    rows = _wire_rows([{"inputs": row["inputs"], "output": tuple(row["output"])}
                       for row in case["training"]])
    return {"type": "SynthEnumerate", "examples": {"type": "Lit", "value": rows},
            "ops": {"type": "Lit", "value": case["ops"]},
            "consts": {"type": "Lit", "value": case["constants"]},
            "max_size": case["max_size"], "max_candidates": case["max_candidates"],
            "saturate_k": 0, "field": ""}

def apply_holdout(sub, term, rows):
    out = []
    for row in rows:
        got = sub._inner.evaluate(term, dict(row["inputs"]))
        expected = tuple(row["output"])
        out.append({"inputs": row["inputs"], "expected": list(expected),
                    "predicted": list(got) if isinstance(got, (list, tuple)) else got,
                    "exact": isinstance(got, (list, tuple)) and tuple(got) == expected})
    return out

def time_reuse(sub, term, rows, count):
    start_wall, start_cpu = time.perf_counter_ns(), time.process_time_ns()
    checksum = 0
    for i in range(count):
        row = rows[i % len(rows)]
        got = sub._inner.evaluate(term, dict(row["inputs"]))
        expected = tuple(row["output"])
        if not isinstance(got, (list, tuple)) or tuple(got) != expected:
            raise RuntimeError("reused candidate failed a held-out row")
        checksum += sum(got)
    return {"calls": count, "wall_ns": time.perf_counter_ns()-start_wall,
            "process_cpu_ns": time.process_time_ns()-start_cpu, "checksum": checksum}

def run_case(case, repetition):
    sub = srs.Substrate()
    request = synth_term(case)
    start_wall, start_cpu = time.perf_counter_ns(), time.process_time_ns()
    result = sub._inner.evaluate(request, {})
    acquire_wall = time.perf_counter_ns()-start_wall
    acquire_cpu = time.process_time_ns()-start_cpu
    found = bool(result.get("found"))
    term = json.loads(result["term"]) if found else None
    held = apply_holdout(sub, term, case["heldout"]) if found else []
    reuse = [time_reuse(sub, term, case["heldout"], n) for n in REUSE_COUNTS] if found else []
    return {"task": case["task"], "grammar": case["grammar"], "repetition": repetition,
            "found": found, "halt_reason": result.get("halt_reason"),
            "tested_candidates": result.get("tested"), "distinct_behaviours": result.get("distinct"),
            "term": term, "term_str": result.get("term_str"),
            "acquisition_wall_ns": acquire_wall, "acquisition_cpu_ns": acquire_cpu,
            "heldout": held, "reuse_batches": reuse,
            "peak_process_rss_bytes": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss *
                (1024 if sys.platform.startswith("linux") else 1))}

def main():
    if sys.argv[1:] == ["--lock"]:
        check_lock(write=True); return
    if sys.argv[1:]: raise SystemExit("usage: substrate_synthenumerate_nonlinear_map_v1.py [--lock]")
    lock = check_lock()
    if RAW.exists(): raise SystemExit(f"refusing to overwrite {RAW}")
    cases = lock["inputs"]["cases"]
    schedule = [(case, rep) for case in cases for rep in range(case["repetitions"])]
    random.Random(SCHEDULE_SEED).shuffle(schedule)
    raw = RAW.open("x", encoding="utf-8")
    raw.write(json.dumps({"kind": "header", "run_id": STEM, "lock": lock,
                          "schedule": [[c["task"], c["grammar"], r] for c,r in schedule]},
                         separators=(",", ":"), sort_keys=True) + "\n")
    raw.flush()
    start, cpu_start = time.perf_counter_ns(), time.process_time_ns()
    for i, (case, rep) in enumerate(schedule, 1):
        row = run_case(case, rep)
        raw.write(json.dumps({"kind": "worker", **row}, separators=(",", ":"), sort_keys=True) + "\n")
        raw.flush()
        print(f"worker={i}/{len(schedule)} task={row['task']} grammar={row['grammar']} rep={rep+1} found={row['found']}", flush=True)
    post = json.loads(json.dumps(lock_payload(), sort_keys=True))
    footer = {"kind": "footer", "source_native_stable": post == lock,
              "post_lock_payload": post, "run_wall_ns": time.perf_counter_ns()-start,
              "run_process_cpu_ns": time.process_time_ns()-cpu_start}
    raw.write(json.dumps(footer, separators=(",", ":"), sort_keys=True) + "\n")
    raw.close()
    if not footer["source_native_stable"]: raise SystemExit("source or native extension drift during run")
    print(json.dumps({"raw": str(RAW.relative_to(ROOT)), "workers": len(schedule),
                      "run_seconds": footer["run_wall_ns"]/1e9}, indent=2))

if __name__ == "__main__": main()
