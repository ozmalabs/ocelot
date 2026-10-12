#!/usr/bin/env python3
"""Measure bounded synthesis before and after a declared grammar expansion."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]

from domains.engine_provenance import engine_preamble, engine_provenance, rust_source_fingerprint
engine_preamble()
from domains.generator import synthesize
from substrate_rs import _native

STEM = "synthesis_declared_grammar_expansion_v1_20261001"
LOCK = ROOT / f"evaluation/substrate_capability/{STEM}_lock.json"
RAW = ROOT / f"evaluation/reports/{STEM}_raw.json"
PROTOCOL = "docs/research/engine_substrate/SUBSTRATE_SYNTHESIS_DECLARED_GRAMMAR_EXPANSION_V1_PREREG_20261001.md"
RUNNER = "scripts/substrate_synthesis_declared_grammar_expansion_v1.py"
ANALYZER = "scripts/analyze_substrate_synthesis_declared_grammar_expansion_v1.py"
SOURCES = (PROTOCOL, RUNNER, ANALYZER, "domains/generator.py", "domains/engine_provenance.py",
           "runners/dsl/python/substrate_rs/__init__.py", "runners/dsl/python/substrate_rs/_native.build.json")
TASK = {"training": [[0, 0.0], [2, 1.0], [4, 2.0], [6, 3.0]],
        "heldout": [-5, -3, -1, 1, 3, 5, 9], "max_size": 5,
        "constants": [0, 1, 2, -1], "timeout_s": 5.0, "parent_timeout_s": 12.0}
GRAMMARS = {
    "operator_absent": ["Plus", "Times", "Minus", "Min", "Max", "Abs", "Neg"],
    "expanded_with_div": ["Plus", "Times", "Minus", "Div", "Min", "Max", "Abs", "Neg"],
}
REPETITIONS = 5
SEED = 20261001


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lock_payload() -> dict:
    native = Path(_native.__file__).resolve()
    return {
        "schema": STEM,
        "sources": {name: sha(ROOT / name) for name in SOURCES},
        "native": {"path": str(native), "sha256": sha(native)},
        "build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
        "engine_provenance": engine_provenance(),
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "design": {"task": TASK, "grammars": GRAMMARS, "repetitions": REPETITIONS,
                   "schedule_seed": SEED, "saturation_disabled": True,
                   "include_output_constants": False},
    }


def worker(condition: str, repetition: int) -> dict:
    grammar = GRAMMARS[condition]
    examples = [({"x": x}, y) for x, y in TASK["training"]]
    started, cpu_started = time.perf_counter(), time.process_time()
    substrate = _native.Substrate()
    result = synthesize(substrate, examples, ops=grammar, consts=TASK["constants"],
                        max_size=TASK["max_size"], timeout_s=TASK["timeout_s"],
                        saturate_k=999999, include_output_constants=False)
    wall_s, cpu_s = time.perf_counter() - started, time.process_time() - cpu_started
    term = result.get("term")
    heldout = []
    if term is not None:
        for x in TASK["heldout"]:
            predicted = term.evaluate({"x": x}, substrate)
            expected = x / 2
            exact = isinstance(predicted, (int, float)) and abs(float(predicted) - expected) <= 1e-9
            heldout.append({"x": x, "predicted": predicted, "expected": expected, "exact": exact})
    return {
        "kind": "worker", "condition": condition, "repetition": repetition,
        "pid": os.getpid(), "grammar": grammar, "status": "accepted" if term is not None else "no_fit",
        "halt_reason": result.get("halt_reason"), "term": result.get("term_str"),
        "term_size": result.get("size"), "explored": result.get("explored"),
        "distinct": result.get("distinct"), "training_count": len(examples),
        "heldout": heldout, "wall_s": wall_s, "cpu_s": cpu_s,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", action="store_true")
    parser.add_argument("--worker", nargs=2, metavar=("CONDITION", "REPETITION"))
    args = parser.parse_args()
    current_lock = lock_payload()
    if args.lock:
        print(json.dumps(current_lock, indent=2, sort_keys=True))
        return
    if not LOCK.is_file() or json.loads(LOCK.read_text()) != current_lock:
        raise SystemExit("source lock absent or stale")
    if args.worker:
        condition, repetition = args.worker
        print(json.dumps(worker(condition, int(repetition)), sort_keys=True, default=str))
        return
    if RAW.exists():
        raise SystemExit(f"refusing to overwrite {RAW}")
    schedule = [(condition, rep) for condition in GRAMMARS for rep in range(REPETITIONS)]
    random.Random(SEED).shuffle(schedule)
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT}:{ROOT / 'runners/dsl/python'}:{env.get('PYTHONPATH', '')}"
    rows = []
    start = time.perf_counter()
    for index, (condition, rep) in enumerate(schedule, 1):
        try:
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker",
                                   condition, str(rep)], cwd=ROOT, env=env,
                                  text=True, capture_output=True, timeout=TASK["parent_timeout_s"])
            if proc.returncode:
                row = {"kind": "worker_error", "condition": condition, "repetition": rep,
                       "error": proc.stderr[-3000:]}
            else:
                row = json.loads(proc.stdout.strip().splitlines()[-1])
        except subprocess.TimeoutExpired:
            row = {"kind": "worker_error", "condition": condition, "repetition": rep,
                   "error": "parent timeout"}
        rows.append(row)
        print(f"{index}/{len(schedule)} {condition} rep={rep} kind={row['kind']}", flush=True)
    raw = {"protocol": STEM, "lock": current_lock, "schedule":[list(x) for x in schedule],
           "workers": rows, "elapsed_s": time.perf_counter()-start,
           "environment":{"python":sys.version, "platform":platform.platform()}}
    RAW.write_text(json.dumps(raw, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"raw":str(RAW), "workers":len(rows),
                      "errors":sum(row["kind"] != "worker" for row in rows)}))


if __name__ == "__main__":
    main()
