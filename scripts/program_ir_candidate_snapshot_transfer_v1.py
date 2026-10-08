#!/usr/bin/env python3
"""Evaluate learned Program/IR snapshots through eager and graph-page forks."""
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

STEM = "program_ir_candidate_snapshot_transfer_v1_20260930"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_PROGRAM_IR_CANDIDATE_SNAPSHOT_V1_PREREG_20260930.md"
LOCK = ROOT / f"evaluation/substrate_capability/{STEM}_lock.json"
RAW = ROOT / f"evaluation/reports/{STEM}_raw.json"
ANALYZER = ROOT / "scripts/analyze_program_ir_candidate_snapshot_transfer_v1.py"
REPS = 5
SEED = 20260930
TASKS = {
    "clamp_0_5": {
        "low": 0, "high": 5,
        "request": "write a function clamp_value between bounds 0 and 5",
        "training": [[-2, 0], [0, 0], [1, 1], [4, 4], [5, 5], [7, 5]],
        "heldout": [-6, -4, -1, 2, 6, 9],
    },
    "clamp_neg2_4": {
        "low": -2, "high": 4,
        "request": "write a function clamp_value within limits negative two and 4",
        "training": [[-5, -2], [-2, -2], [-1, -1], [1, 1], [4, 4], [7, 4]],
        "heldout": [-8, -3, 0, 2, 6, 9],
    },
}
SOURCE_FILES = (
    "scripts/program_ir_candidate_snapshot_transfer_v1.py",
    "scripts/analyze_program_ir_candidate_snapshot_transfer_v1.py",
    "docs/research/engine_substrate/SUBSTRATE_PROGRAM_IR_CANDIDATE_SNAPSHOT_V1_PREREG_20260930.md",
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


def canonical_digest(substrate) -> str:
    native = substrate._inner
    grammar = native.grammar_to_json()
    if isinstance(grammar, str):
        grammar = json.loads(grammar)
    state = {"graph": native.graph_to_dict(), "grammar": grammar, "rules": native.export_rules()}
    return hashlib.sha256(json.dumps(state, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def oracle(task: str, x: int) -> int:
    spec = TASKS[task]
    return min(max(x, spec["low"]), spec["high"])


def lock_payload() -> dict:
    ext = Path(srs._native.__file__).resolve()
    return {
        "schema_version": 1,
        "source_sha256": {name: sha(ROOT / name) for name in SOURCE_FILES},
        "native_extension": {"path": str(ext), "sha256": sha(ext)},
        "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
        "engine_provenance": engine_provenance(),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "design": {"tasks": TASKS, "repetitions": REPS, "schedule_seed": SEED,
                   "arms": ["candidate", "frozen", "exposure_without_pump"],
                   "candidate_validation_backends": ["eager", "shared_graph_pages"]},
    }


def eval_child(source, backend: str, program_id, task: str, base_digest: str) -> dict:
    wall0, cpu0 = time.perf_counter(), time.process_time()
    source_digest = canonical_digest(source)
    fork0 = time.perf_counter()
    branch = (source.fork_shared_graph_pages_experiment() if backend == "shared_graph_pages"
              else source.fork_full_copy_experiment())
    fork_wall = time.perf_counter() - fork0
    program_nodes = list(branch.nodes("Program"))
    ir_roots = list(branch.neighbours(program_id, "ir_subgraph")) if program_id is not None else []
    outputs = []
    if len(ir_roots) == 1:
        root = ir_roots[0]
        for x in TASKS[task]["heldout"]:
            value = None
            trap = "unknown"
            halted = False
            try:
                result = branch._inner.evaluate(
                    {"type": "ProgEval", "prog": {"type": "Var", "name": "p"},
                     "env": {"type": "Var", "name": "e"}, "oracles": None,
                     "fuel": 10000, "field": ""},
                    {"p": root, "e": {"value": x}},
                )
                trap = result.get("trap")
                halted = bool(result.get("halted"))
                if halted and trap is None:
                    value = result.get("result")
            except Exception as exc:
                trap = f"{type(exc).__name__}: {exc}"
            expected = oracle(task, x)
            outputs.append({"input": x, "expected": expected, "predicted": value,
                            "halted": halted, "trap": trap,
                            "exact": halted and trap is None and value == expected})
    source_unchanged = canonical_digest(source) == source_digest
    return {
        "backend": backend,
        "fork_wall_s": fork_wall,
        "branch_wall_s": time.perf_counter() - wall0,
        "branch_cpu_s": time.process_time() - cpu0,
        "program_node_count": len(program_nodes),
        "task_program_present": any(branch.node(n)["attrs"].get("name") == task for n in program_nodes),
        "ir_root_count": len(ir_roots),
        "outputs": outputs,
        "source_digest_before": source_digest,
        "source_unchanged": source_unchanged,
        "source_digest_expected": base_digest,
        "result_digest": canonical_digest(branch),
    }


def worker(task: str, rep: int) -> dict:
    started, cpu0 = time.perf_counter(), time.process_time()
    baseline = srs.Substrate()
    agent = baseline.add_node("Agent", {})
    baseline_digest = canonical_digest(baseline)

    # Learn on an isolated shared-page branch.
    candidate = baseline.fork_shared_graph_pages_experiment()
    candidate_agent = agent
    examples = [({"value": x}, expected) for x, expected in TASKS[task]["training"]]
    train0, train_cpu0 = time.perf_counter(), time.process_time()
    outcome = psy.synthesize_from_request(candidate, candidate_agent, TASKS[task]["request"],
                                           examples, name=task)
    train_wall = time.perf_counter() - train0
    train_cpu = time.process_time() - train_cpu0
    candidate_digest = canonical_digest(candidate)
    program_id = outcome.get("program")
    program_attrs = outcome.get("program_attrs") or {}
    ir_roots = list(candidate.neighbours(program_id, "ir_subgraph")) if program_id is not None else []

    eager = eval_child(candidate, "eager", program_id, task, candidate_digest)
    shared = eval_child(candidate, "shared_graph_pages", program_id, task, candidate_digest)

    # Frozen: no request/examples/pump. Exposure: request/examples ingested, but
    # the acquisition/consolidation pump is intentionally withheld.
    frozen = baseline.fork_full_copy_experiment()
    frozen_eval = eval_child(frozen, "eager", None, task, baseline_digest)
    exposure = baseline.fork_shared_graph_pages_experiment()
    psy.ensure_program_synthesis(exposure, exposure._inner, agent)
    ingest0, ingest_cpu0 = time.perf_counter(), time.process_time()
    message = psy.ingest_spec(exposure, agent, TASKS[task]["request"], examples, name=task)
    ingest_wall = time.perf_counter() - ingest0
    ingest_cpu = time.process_time() - ingest_cpu0
    exposure_programs_before_eval = [n for n in exposure.nodes("Program")
                                     if exposure.node(n)["attrs"].get("name") == task]
    exposure_eval = eval_child(exposure, "shared_graph_pages", None, task, canonical_digest(exposure))

    return {
        "task": task, "replicate": rep, "pid": os.getpid(),
        "baseline_digest": baseline_digest,
        "candidate": {"status": outcome.get("status"), "rungs": outcome.get("rungs"),
                      "construction": outcome.get("construction"),
                      "enumerate_outcome": outcome.get("enumerate_outcome"),
                      "program_id": str(program_id) if program_id is not None else None,
                      "program_attrs": program_attrs,
                      "ir": outcome.get("ir"), "ir_root_count": len(ir_roots),
                      "program_count": len(list(candidate.nodes("Program"))),
                      "training_rows": TASKS[task]["training"],
                      "train_wall_s": train_wall, "train_cpu_s": train_cpu,
                      "snapshot_digest": candidate_digest,
                      "eager": eager, "shared_graph_pages": shared,
                      "snapshot_unchanged_after_eval": canonical_digest(candidate) == candidate_digest},
        "frozen": {"program_count": len(list(frozen.nodes("Program"))),
                   "task_program_count": sum(frozen.node(n)["attrs"].get("name") == task
                                             for n in frozen.nodes("Program")),
                   "evaluation": frozen_eval},
        "exposure_without_pump": {"ingest_wall_s": ingest_wall, "ingest_cpu_s": ingest_cpu,
                                   "message_id": str(message),
                                   "request": TASKS[task]["request"],
                                   "training_rows": TASKS[task]["training"],
                                   "task_program_count_before_eval": len(exposure_programs_before_eval),
                                   "evaluation": exposure_eval},
        "isolation": {"baseline_unchanged": canonical_digest(baseline) == baseline_digest,
                      "baseline_digest_after": canonical_digest(baseline),
                      "candidate_snapshot_distinct": candidate_digest != baseline_digest,
                      "candidate_snapshot_unchanged": canonical_digest(candidate) == candidate_digest,
                      "frozen_source_unchanged": frozen_eval["source_unchanged"],
                      "exposure_source_unchanged": exposure_eval["source_unchanged"]},
        "elapsed_wall_s": time.perf_counter() - started,
        "elapsed_cpu_s": time.process_time() - cpu0,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", action="store_true")
    parser.add_argument("--worker", nargs=2, metavar=("TASK", "REP"))
    args = parser.parse_args()
    lock = json.loads(json.dumps(lock_payload()))
    if args.lock:
        print(json.dumps(lock, indent=2, sort_keys=True))
        return
    if args.worker:
        print(json.dumps(worker(args.worker[0], int(args.worker[1])), sort_keys=True, default=str))
        return
    if not LOCK.exists() or json.loads(LOCK.read_text()) != lock:
        raise SystemExit("missing or stale lock; write --lock output before confirmatory capture")
    if RAW.exists():
        raise SystemExit(f"refusing to overwrite {RAW}")
    schedule = [(task, rep) for rep in range(1, REPS + 1) for task in TASKS]
    random.Random(SEED).shuffle(schedule)
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT}:{ROOT / 'scripts'}:{ROOT / 'runners/dsl/python'}:{env.get('PYTHONPATH', '')}"
    rows, started = [], time.perf_counter()
    for i, (task, rep) in enumerate(schedule, 1):
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", task, str(rep)],
                              cwd=ROOT, env=env, text=True, capture_output=True, check=False, timeout=300)
        if proc.returncode:
            row = {"task": task, "replicate": rep, "pid": None,
                   "worker_error": f"exit={proc.returncode}: {proc.stderr[-2000:]}"}
        else:
            try:
                row = json.loads(proc.stdout.strip().splitlines()[-1])
                row["worker_error"] = None
            except Exception as exc:
                row = {"task": task, "replicate": rep, "pid": None,
                       "worker_error": f"output parse: {type(exc).__name__}: {exc}"}
        rows.append(row)
        print(f"worker={i}/{len(schedule)} task={task} rep={rep} status={(row.get('candidate') or {}).get('status')} error={row.get('worker_error')}", flush=True)
    raw = {"protocol": STEM, "locked_inputs": lock, "lock_sha256": sha(LOCK),
           "schedule": [list(x) for x in schedule], "workers": rows,
           "worker_failures": [r for r in rows if r.get("worker_error")],
           "worker_count": len(rows), "parent_elapsed_s": time.perf_counter() - started,
           "environment": {"python": sys.version, "platform": platform.platform(),
                           "OZMA_NO_LLM": os.environ.get("OZMA_NO_LLM"),
                           "OZMA_SEED_PERSIST_DISABLED": os.environ.get("OZMA_SEED_PERSIST_DISABLED")},
           "claim_boundary": "isolated acquisition and exact Program/IR execution on two authored clamp tasks; not natural-task capability, formal P3-E1, or general CoW performance"}
    RAW.write_text(json.dumps(raw, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"output": str(RAW), "workers": len(rows), "failures": len(raw["worker_failures"]),
                      "elapsed_s": raw["parent_elapsed_s"]}, indent=2))


if __name__ == "__main__":
    main()
