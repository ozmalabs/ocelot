#!/usr/bin/env python3
"""Measure hinge-map ambiguity and one-counterexample response in isolated snapshots."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import resource
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "runners/dsl/python")]
from domains.engine_provenance import engine_preamble, engine_provenance, rust_source_fingerprint
engine_preamble()
import substrate_rs as srs
import domains.prog_synthesis as psy

STEM = "synthesis_ambiguity_counterexample_v1_20260930"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_SYNTHESIS_AMBIGUITY_COUNTEREXAMPLE_V1_PREREG_20260930.md"
LOCK = ROOT / f"evaluation/substrate_capability/{STEM}_lock.json"
RAW = ROOT / f"evaluation/reports/{STEM}_raw.json"
ANALYZER = ROOT / "scripts/analyze_synthesis_ambiguity_counterexample_v1.py"
REPS = 5
SEED = 20260930
DEFAULT_CAP = 200000
OPS = ["Plus", "Minus", "Max", "TupleOf"]
TRAIN_SPARSE = [(r, c) for c in (0, 1, 2) for r in (0, 1)]
COUNTEREXAMPLE = (0, 3)
HOLDOUT = [(1, 3), (2, 3), (1, 4), (4, 4), (2, 5), (5, 5)]
ARMS = ("ambiguous_default", "counterexample_default", "counterexample_oracle_grammar")

SOURCE_FILES = (
    "scripts/synthesis_ambiguity_counterexample_v1.py",
    "scripts/analyze_synthesis_ambiguity_counterexample_v1.py",
    "docs/research/engine_substrate/SUBSTRATE_SYNTHESIS_AMBIGUITY_COUNTEREXAMPLE_V1_PREREG_20260930.md",
    "domains/prog_synthesis.py", "domains/engine_provenance.py", "domains/code_writing.py",
    "domains/prog_retrieval.py", "seeds/program_synthesis.json",
    "seeds/program_synthesis_grounding.json", "seeds/program_synthesis_opgrammar.json",
    "seeds/code_write_request_cues.json", "seeds/exact_families.json",
    "runners/dsl/src/synth_enumerate.rs", "runners/dsl/src/prog_eval.rs",
    "runners/dsl/src/term.rs", "runners/dsl/src/py.rs",
    "runners/dsl/src/graph_rules.rs", "runners/dsl/src/substrate.rs",
    "runners/dsl/src/graph.rs", "runners/dsl/src/persist.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def target(r: int, c: int) -> list[int]:
    return [r + max(c - 1, 0), c]


def canonical_digest(sub) -> str:
    native = sub._inner
    grammar = native.grammar_to_json()
    if isinstance(grammar, str):
        grammar = json.loads(grammar)
    state = {"graph": native.graph_to_dict(), "grammar": grammar, "rules": native.export_rules()}
    return hashlib.sha256(json.dumps(state, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def train_rows(arm: str) -> list[tuple[int, int]]:
    return TRAIN_SPARSE + ([COUNTEREXAMPLE] if arm != "ambiguous_default" else [])


def lock_payload() -> dict:
    extension = Path(srs._native.__file__).resolve()
    return {
        "schema_version": 1,
        "source_sha256": {name: sha(ROOT / name) for name in SOURCE_FILES},
        "native_extension": {"path": str(extension), "sha256": sha(extension)},
        "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
        "engine_provenance": engine_provenance(),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "design": {"formula": "(r + max(c-1,0), c)", "sparse_training": TRAIN_SPARSE,
                   "counterexample": COUNTEREXAMPLE, "holdout": HOLDOUT, "arms": ARMS,
                   "oracle_ops": OPS, "candidate_cap": DEFAULT_CAP,
                   "repetitions": REPS, "schedule_seed": SEED},
    }


def evaluate_child(source, backend: str, program_id, arm: str, candidate_digest: str) -> dict:
    started, cpu0 = time.perf_counter(), time.process_time()
    source_digest = canonical_digest(source)
    fork0 = time.perf_counter()
    branch = source.fork_shared_graph_pages_experiment() if backend == "shared_graph_pages" else source.fork_full_copy_experiment()
    fork_wall = time.perf_counter() - fork0
    roots = list(branch.neighbours(program_id, "ir_subgraph")) if program_id is not None else []
    examples = [{"r": r, "c": c} for r, c in train_rows(arm)]
    evaluations = []
    if len(roots) == 1:
        for split, pairs in (("training", train_rows(arm)), ("heldout", HOLDOUT)):
            for r, c in pairs:
                env = {"r": r, "c": c}
                expected = target(r, c)
                value, trap, halted = None, "no_result", False
                try:
                    result = branch._inner.evaluate(
                        {"type": "ProgEval", "prog": {"type": "Var", "name": "p"},
                         "env": {"type": "Var", "name": "e"}, "oracles": None,
                         "fuel": 10000, "field": ""},
                        {"p": roots[0], "e": env},
                    )
                    trap = result.get("trap")
                    halted = bool(result.get("halted"))
                    if halted and trap is None:
                        out = result.get("result")
                        value = list(out) if isinstance(out, (list, tuple)) else out
                except Exception as exc:
                    trap = f"{type(exc).__name__}: {exc}"
                evaluations.append({"split": split, "inputs": env, "expected": expected,
                                    "predicted": value, "halted": halted, "trap": trap,
                                    "exact": halted and trap is None and value == expected})
    return {
        "backend": backend, "fork_wall_s": fork_wall,
        "validation_wall_s": time.perf_counter() - started,
        "validation_cpu_s": time.process_time() - cpu0,
        "ir_root_count": len(roots), "evaluations": evaluations,
        "source_digest_before": source_digest,
        "source_unchanged": canonical_digest(source) == source_digest,
        "source_equals_candidate_snapshot": source_digest == candidate_digest,
        "result_digest": canonical_digest(branch),
    }


def worker(arm: str, rep: int) -> dict:
    if arm not in ARMS:
        raise ValueError(f"unknown arm {arm}")
    started, cpu0 = time.perf_counter(), time.process_time()
    base = srs.Substrate()
    agent = base.add_node("Agent", {})
    base_digest = canonical_digest(base)
    candidate = base.fork_shared_graph_pages_experiment()
    psy.ensure_program_synthesis(candidate, candidate._inner, agent)
    examples = [({"r": r, "c": c}, tuple(target(r, c))) for r, c in train_rows(arm)]
    message = psy.ingest_spec(candidate, agent,
                              "write a function map_hinge that returns a transformed pair",
                              examples, name=f"hinge_{arm}")
    if arm == "counterexample_oracle_grammar":
        candidate.set_attr(message, "ps_enum_ops", OPS)
    pump0, pump_cpu0 = time.perf_counter(), time.process_time()
    psy.pump(candidate, agent)
    pump_wall, pump_cpu = time.perf_counter() - pump0, time.process_time() - pump_cpu0
    goals = candidate.in_neighbours(message, "about_message")
    if len(goals) != 1:
        raise RuntimeError(f"expected one Goal, found {len(goals)}")
    goal = goals[0]
    outcome = psy.read_goal(candidate, goal)
    program_id = outcome.get("program")
    candidate_digest = canonical_digest(candidate)
    eager = evaluate_child(candidate, "eager", program_id, arm, candidate_digest)
    shared = evaluate_child(candidate, "shared_graph_pages", program_id, arm, candidate_digest)
    return {
        "arm": arm, "replicate": rep, "pid": os.getpid(),
        "training": [{"inputs": {"r": r, "c": c}, "output": target(r, c)} for r, c in train_rows(arm)],
        "holdout": [{"inputs": {"r": r, "c": c}, "output": target(r, c)} for r, c in HOLDOUT],
        "candidate": {"status": outcome.get("status"), "gap_reason": outcome.get("gap_reason"),
                      "enumerate_outcome": outcome.get("enumerate_outcome"),
                      "enumerate": outcome.get("enumerate"), "rungs": outcome.get("rungs"),
                      "program_id": str(program_id) if program_id is not None else None,
                      "ir": outcome.get("ir"), "program_attrs": outcome.get("program_attrs"),
                      "candidate_digest": candidate_digest, "eager": eager, "shared_graph_pages": shared,
                      "snapshot_unchanged": canonical_digest(candidate) == candidate_digest},
        "primary": {"digest_before": base_digest, "digest_after": canonical_digest(base),
                    "unchanged": canonical_digest(base) == base_digest},
        "pump_wall_s": pump_wall, "pump_cpu_s": pump_cpu,
        "elapsed_wall_s": time.perf_counter() - started,
        "elapsed_cpu_s": time.process_time() - cpu0,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", action="store_true")
    parser.add_argument("--worker", nargs=2, metavar=("ARM", "REP"))
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(args.worker[0], int(args.worker[1])), sort_keys=True, default=str))
        return
    lock = json.loads(json.dumps(lock_payload()))
    if args.lock:
        print(json.dumps(lock, indent=2, sort_keys=True))
        return
    if not LOCK.exists() or json.loads(LOCK.read_text()) != lock:
        raise SystemExit("missing or stale source/task lock; preserve prior evidence and amend")
    if RAW.exists():
        raise SystemExit(f"refusing to overwrite {RAW}")
    schedule = [(arm, rep) for rep in range(1, REPS + 1) for arm in ARMS]
    random.Random(SEED).shuffle(schedule)
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT}:{ROOT / 'scripts'}:{ROOT / 'runners/dsl/python'}:{env.get('PYTHONPATH', '')}"
    rows, started = [], time.perf_counter()
    for i, (arm, rep) in enumerate(schedule, 1):
        process = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", arm, str(rep)],
                                 cwd=ROOT, env=env, text=True, capture_output=True, check=False, timeout=300)
        if process.returncode:
            row = {"arm": arm, "replicate": rep, "pid": None,
                   "worker_error": f"exit={process.returncode}: {process.stderr[-2000:]}"}
        else:
            try:
                row = json.loads(process.stdout.strip().splitlines()[-1])
                row["worker_error"] = None
            except Exception as exc:
                row = {"arm": arm, "replicate": rep, "pid": None,
                       "worker_error": f"output parse: {type(exc).__name__}: {exc}"}
        rows.append(row)
        print(f"worker={i}/{len(schedule)} arm={arm} rep={rep} status={(row.get('candidate') or {}).get('status')} tested={((row.get('candidate') or {}).get('enumerate') or {}).get('tested')} error={row.get('worker_error')}", flush=True)
    raw = {"protocol": STEM, "locked_inputs": lock, "lock_sha256": sha(LOCK),
           "schedule": [list(x) for x in schedule], "workers": rows,
           "worker_count": len(rows), "worker_failures": [r for r in rows if r.get("worker_error")],
           "parent_elapsed_s": time.perf_counter() - started,
           "environment": {"python": sys.version, "platform": platform.platform(),
                           "OZMA_NO_LLM": os.environ.get("OZMA_NO_LLM"),
                           "OZMA_SEED_PERSIST_DISABLED": os.environ.get("OZMA_SEED_PERSIST_DISABLED")},
           "claim_boundary": "fixed hinge ambiguity and one externally selected distinguishing example; the oracle grammar is supplied information, and no autonomous query policy is tested"}
    RAW.write_text(json.dumps(raw, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"output": str(RAW), "workers": len(rows), "failures": len(raw["worker_failures"]),
                      "elapsed_s": raw["parent_elapsed_s"]}, indent=2))


if __name__ == "__main__":
    main()
