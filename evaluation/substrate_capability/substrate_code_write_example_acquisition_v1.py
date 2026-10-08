#!/usr/bin/env python3
"""Locked fresh-process evaluation of code-write construction growth by example."""
from __future__ import annotations

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

ROOT = Path(__file__).resolve().parents[2]
RUNNER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_CODE_WRITE_EXAMPLE_ACQUISITION_V1_PREREG_20261001.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_CODE_WRITE_EXAMPLE_ACQUISITION_V1_PRECAPTURE_AMENDMENT_20261001.md"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_substrate_code_write_example_acquisition_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/substrate_code_write_example_acquisition_v1_lock_20261001.json"
RAW = ROOT / "evaluation/reports/substrate_code_write_example_acquisition_v1_raw_20261001.json"
SEED = 20261017
REPETITIONS = 5
TASKS = {
    "parity": {
        "request": "Write a function that returns the parity of an integer.",
        "func_name": "parity",
        "source": "def parity(value):\n    return value % 2 == 0\n",
        "heldout": [{"value": x} for x in range(-20, 21)],
    },
    "clamp": {
        "request": "Write a function that clamps a value between lower and upper bounds.",
        "func_name": "clamp_value",
        "source": "def clamp_value(value, lower, upper):\n    return lower if value < lower else (upper if value > upper else value)\n",
        "heldout": [
            {"value": -20, "lower": -4, "upper": 8}, {"value": -4, "lower": -4, "upper": 8},
            {"value": -3, "lower": -4, "upper": 8}, {"value": 0, "lower": -4, "upper": 8},
            {"value": 7, "lower": -4, "upper": 8}, {"value": 8, "lower": -4, "upper": 8},
            {"value": 9, "lower": -4, "upper": 8}, {"value": 20, "lower": -4, "upper": 8},
            {"value": -9, "lower": -9, "upper": -2}, {"value": -10, "lower": -9, "upper": -2},
            {"value": -5, "lower": -9, "upper": -2}, {"value": -2, "lower": -9, "upper": -2},
            {"value": 0, "lower": -9, "upper": -2}, {"value": 12, "lower": -9, "upper": -2},
            {"value": 2, "lower": 1, "upper": 5}, {"value": 1, "lower": 1, "upper": 5},
            {"value": 3, "lower": 1, "upper": 5}, {"value": 5, "lower": 1, "upper": 5},
            {"value": 7, "lower": 1, "upper": 5}, {"value": -1, "lower": 1, "upper": 5},
        ],
    },
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def tree_sha(paths: tuple[str, ...], suffixes: tuple[str, ...]) -> str:
    entries = []
    for rel in paths:
        base = ROOT / rel
        candidates = [base] if base.is_file() else sorted(p for p in base.rglob("*") if p.is_file())
        for path in candidates:
            if path.suffix in suffixes or path.name in {"_native.abi3.so", "_native.build.json"}:
                entries.append((path.relative_to(ROOT).as_posix(), sha(path)))
    digest = hashlib.sha256()
    for rel, value in sorted(entries):
        digest.update(rel.encode()); digest.update(b"\0"); digest.update(value.encode()); digest.update(b"\n")
    return digest.hexdigest()


def seed_manifest_sha() -> str:
    # load_all_seeds reads the flat manifests plus seeds/generated/*.json;
    # nested corpora and media are data payloads, not boot manifests.
    files=sorted([*ROOT.joinpath("seeds").glob("*.json"),
                  *ROOT.joinpath("seeds/generated").glob("*.json")])
    digest=hashlib.sha256()
    for path in files:
        digest.update(path.relative_to(ROOT).as_posix().encode()); digest.update(b"\0")
        digest.update(sha(path).encode()); digest.update(b"\n")
    return digest.hexdigest()


ACTIVE_FILES=(
    "domains/code_reading.py", "domains/code_writing.py", "domains/code_write_growth.py",
    "domains/ast_to_term.py", "domains/teach.py", "domains/reflective_faculty.py",
    "domains/engine_provenance.py", "substrate/world_adapter.py", "substrate/boot_all.py",
    "substrate/boot_core.py", "substrate/seed_loader.py",
    "runners/dsl/src/term.rs", "runners/dsl/src/py.rs", "runners/dsl/src/graph_rules.rs",
    "runners/dsl/src/substrate.rs", "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
    "seeds/code_constructions.json", "seeds/code_write_constructions.json",
    "seeds/code_write_request_cues.json", "seeds/code_write_gap.json",
    "seeds/gap_awareness.json", "seeds/shape_decode_loop.json",
    "seeds/math_capability_shapes.json",
)


def active_payload() -> dict[str,str]:
    result={rel:sha(ROOT/rel) for rel in ACTIVE_FILES}
    import substrate_rs as srs
    result["native_binary"] = sha(Path(srs._native.__file__).resolve())
    return result


def input_payload() -> dict:
    sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
    import substrate_rs as srs
    return {
        "schema": "SubstrateCodeWriteExampleAcquisitionV1Lock",
        "harness_sha256": {str(RUNNER.relative_to(ROOT)): sha(RUNNER),
                           str(ANALYZER.relative_to(ROOT)): sha(ANALYZER),
                           str(PROTOCOL.relative_to(ROOT)): sha(PROTOCOL),
                           str(AMENDMENT.relative_to(ROOT)): sha(AMENDMENT)},
        "tree_sha256": {
            "domains_py": tree_sha(("domains",), (".py",)),
            "substrate_py": tree_sha(("substrate",), (".py",)),
            "loaded_seed_manifests": seed_manifest_sha(),
            "rust_dsl": tree_sha(("runners/dsl/src",), (".rs",)),
            "python_native": tree_sha(("runners/dsl/python/substrate_rs",), (".py",)),
        },
        "native_binary_sha256": sha(Path(srs._native.__file__).resolve()),
        "active_sha256": active_payload(),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "design": {"tasks": TASKS, "repetitions": REPETITIONS, "seed": SEED,
                   "boot": "WorldAdapter(seeds=()) then load_all_seeds", "oracle_in_runner": False,
                   "example_source_is_external": True},
    }


def worker(task: str, repetition: int) -> dict:
    os.environ.setdefault("OZMA_NO_LLM", "1")
    os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    expected_lock=json.loads(LOCK.read_text())
    before = active_payload()
    if before != expected_lock["active_sha256"]:
        raise RuntimeError("active worker sources differ from pre-run lock")
    from domains import code_reading as cdr
    from domains import code_writing as cw
    from domains import code_write_growth as cwg
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter

    fixture = TASKS[task]
    agent = WorldAdapter(seeds=())
    boot_start = time.perf_counter_ns(); boot_cpu = time.process_time_ns()
    boot = load_all_seeds(agent)
    boot_ns = time.perf_counter_ns() - boot_start; boot_cpu_ns = time.process_time_ns() - boot_cpu
    sub, native, agent_node = cdr._resolve(agent)

    baseline_start = time.perf_counter_ns()
    baseline = cw.write_function_from_request(agent, fixture["request"], name="heldout_candidate")
    baseline_ns = time.perf_counter_ns() - baseline_start
    baseline_shapes = [sub.node(n)["attrs"].get("name") for n in sub.nodes("ShapeSignature")
                       if sub.node(n)["attrs"].get("kind") == "code_write_construction"]

    teach_start = time.perf_counter_ns(); teach_cpu = time.process_time_ns()
    taught = cwg.teach_write_shape_from_example(agent, fixture["source"],
                                                  request_text=fixture["request"])
    teach_ns = time.perf_counter_ns() - teach_start; teach_cpu_ns = time.process_time_ns() - teach_cpu
    teach_shapes = [n for n in sub.nodes("ShapeSignature")
                    if sub.node(n)["attrs"].get("name") == taught.get("shape")]
    teach_attrs = sub.node(teach_shapes[-1])["attrs"] if teach_shapes else {}

    compose_start = time.perf_counter_ns()
    composed = cw.compose_function_from_request(agent, fixture["request"])
    compose_ns = time.perf_counter_ns() - compose_start
    write_start = time.perf_counter_ns()
    written = cw.write_function_from_request(agent, fixture["request"], name="heldout_candidate")
    write_ns = time.perf_counter_ns() - write_start

    exec_ns: dict[str, Any] = {}
    exec(written.get("source", ""), exec_ns)
    fn = exec_ns.get("heldout_candidate")
    rows = []
    native_start = time.perf_counter_ns(); native_cpu = time.process_time_ns()
    python_start = time.perf_counter_ns(); python_cpu = time.process_time_ns()
    for env in fixture["heldout"]:
        native_value = native.evaluate(composed["term"], env) if composed.get("ok") else None
        python_value = fn(**env) if callable(fn) else None
        rows.append({"input": env, "native_output": native_value, "python_output": python_value})
    python_ns = time.perf_counter_ns() - python_start; python_cpu_ns = time.process_time_ns() - python_cpu
    native_ns = time.perf_counter_ns() - native_start; native_cpu_ns = time.process_time_ns() - native_cpu

    after = active_payload()
    return {
        "kind": "worker", "task": task, "repetition": repetition, "pid": os.getpid(),
        "source_stable": before == after, "active_source_before": before, "active_source_after": after,
        "boot_ns": boot_ns, "boot_cpu_ns": boot_cpu_ns,
        "boot_report": {"loaded": len(getattr(boot, "loaded", []) or []), "type": type(boot).__name__},
        "baseline": baseline, "baseline_shape_names": baseline_shapes, "baseline_ns": baseline_ns,
        "teach": taught, "teach_ns": teach_ns, "teach_cpu_ns": teach_cpu_ns,
        "new_shape_attrs": teach_attrs, "write_codebook_epoch": sub.node(agent_node)["attrs"].get("write_codebook_epoch", 0),
        "compose": composed, "compose_ns": compose_ns,
        "written": {"ok": written.get("ok"), "source": written.get("source"),
                    "construction": written.get("construction"), "args": written.get("args"),
                    "term": written.get("term"), "sample_ok": written.get("sample_ok")},
        "write_ns": write_ns, "heldout": rows,
        "heldout_native_ns": native_ns, "heldout_native_cpu_ns": native_cpu_ns,
        "heldout_python_ns": python_ns, "heldout_python_cpu_ns": python_cpu_ns,
        "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
    }


def main() -> None:
    if sys.argv[1:] == ["--lock"]:
        current = input_payload()
        if LOCK.exists() or RAW.exists(): raise SystemExit("refusing to overwrite lock or capture")
        LOCK.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT)); return
    current = input_payload()
    if not LOCK.is_file() or json.loads(LOCK.read_text()) != current:
        raise SystemExit("missing/stale input lock")
    if RAW.exists(): raise SystemExit(f"refusing to overwrite {RAW}")
    schedule = [(task, rep) for task in TASKS for rep in range(1, REPETITIONS + 1)]
    random.Random(SEED).shuffle(schedule)
    env = dict(os.environ); env["OZMA_NO_LLM"] = "1"; env["OZMA_SEED_PERSIST_DISABLED"] = "1"
    env["PYTHONPATH"] = f"{ROOT}:{ROOT / 'runners/dsl/python'}:{env.get('PYTHONPATH', '')}"
    rows=[]; started=time.perf_counter()
    for i, (task, rep) in enumerate(schedule, 1):
        try:
            proc=subprocess.run([sys.executable,str(RUNNER),"--worker",task,str(rep)],cwd=ROOT,
                                env=env,text=True,capture_output=True,timeout=120)
            row=json.loads(proc.stdout.strip().splitlines()[-1]) if proc.returncode == 0 else {
                "kind":"worker_error","task":task,"repetition":rep,"error":proc.stderr[-4000:]}
        except subprocess.TimeoutExpired:
            row={"kind":"worker_error","task":task,"repetition":rep,"error":"120 second worker timeout"}
        rows.append(row); print(f"{i}/10 {task} r={rep} {row['kind']} teach={row.get('teach',{}).get('ok')}",flush=True)
    post=input_payload()
    capture={"schema":"SubstrateCodeWriteExampleAcquisitionV1Capture","lock":current,
             "post_lock":post,"schedule":[{"task":t,"repetition":r} for t,r in schedule],
             "workers":rows,"elapsed_seconds":time.perf_counter()-started,
             "environment":{"python":sys.version,"platform":platform.platform()}}
    RAW.write_text(json.dumps(capture,indent=2,sort_keys=True,default=str)+"\n")
    print(json.dumps({"raw":RAW.relative_to(ROOT).as_posix(),"workers":len(rows),
                      "errors":sum(r.get("kind")!="worker" for r in rows),"source_stable":current==post}))


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        print(json.dumps(worker(sys.argv[2], int(sys.argv[3])), sort_keys=True, default=str))
    else:
        main()
