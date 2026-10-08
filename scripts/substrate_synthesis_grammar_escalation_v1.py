#!/usr/bin/env python3
"""Measure caller-directed grammar escalation, including an absent primitive."""
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
from domains.generator import synthesize, DEFAULT_OPS
from substrate_rs import _native

STEM = "synthesis_grammar_escalation_v1_20261001"
LOCK = ROOT / f"evaluation/substrate_capability/{STEM}_lock.json"
RAW = ROOT / f"evaluation/reports/{STEM}_raw.json"
PROTOCOL = "docs/research/engine_substrate/SUBSTRATE_SYNTHESIS_GRAMMAR_ESCALATION_V1_PREREG_20261001.md"
RUNNER = "scripts/substrate_synthesis_grammar_escalation_v1.py"
ANALYZER = "scripts/analyze_substrate_synthesis_grammar_escalation_v1.py"
SOURCES = (PROTOCOL, RUNNER, ANALYZER, "domains/generator.py", "domains/engine_provenance.py",
           "runners/dsl/python/substrate_rs/__init__.py", "runners/dsl/python/substrate_rs/_native.build.json")
NUMERIC = ["Plus", "Times", "Minus", "Div", "Min", "Max", "Abs", "Neg"]
GRAMMARS = {
    "arithmetic": ["Plus", "Times", "Minus"],
    "numeric": NUMERIC,
    "full": NUMERIC + ["Gt", "Lt", "Eq", "IfThenElse"],
}
TASKS = {
    "division": {"training": [0, 2, 4, 6], "heldout": [-5, -3, -1, 1, 3, 5, 9],
                 "target": "x / 2", "required_primitive": "Div"},
    "modulo": {"training": list(range(7)), "heldout": [8, 9, 10, 11, 12, 14, 17],
               "target": "x % 3", "required_primitive": "Mod"},
}
CONSTS = [0, 1, 2, -1]
MAX_SIZE, TIMEOUT_S, PARENT_TIMEOUT_S = 5, 3.0, 10.0
REPETITIONS, SEED = 5, 20261001


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lock_payload() -> dict:
    native = Path(_native.__file__).resolve()
    return {"schema": STEM, "sources": {name: sha(ROOT / name) for name in SOURCES},
            "native": {"path": str(native), "sha256": sha(native)},
            "build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
            "engine_provenance": engine_provenance(),
            "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "design": {"tasks": TASKS, "grammars": GRAMMARS, "constants": CONSTS,
                       "max_size": MAX_SIZE, "timeout_s": TIMEOUT_S,
                       "parent_timeout_s": PARENT_TIMEOUT_S, "repetitions": REPETITIONS,
                       "schedule_seed": SEED, "saturation_disabled": True,
                       "include_output_constants": False}}


def oracle(task: str, x: int):
    return x / 2 if task == "division" else x % 3


def worker(task: str, repetition: int) -> dict:
    substrate = _native.Substrate()
    rows = [({"x": x}, oracle(task, x)) for x in TASKS[task]["training"]]
    stages = []
    started_all, cpu_all = time.perf_counter(), time.process_time()
    selected = None
    for stage, ops in GRAMMARS.items():
        wall0, cpu0 = time.perf_counter(), time.process_time()
        result = synthesize(substrate, rows, ops=ops, consts=CONSTS,
                            max_size=MAX_SIZE, timeout_s=TIMEOUT_S,
                            saturate_k=999999, include_output_constants=False)
        stage_result = {"stage": stage, "grammar": ops, "status": "accepted" if result.get("term") else "no_fit",
                        "halt_reason": result.get("halt_reason"), "term": result.get("term_str"),
                        "term_size": result.get("size"), "explored": result.get("explored"),
                        "distinct": result.get("distinct"),
                        "wall_s": time.perf_counter()-wall0, "cpu_s": time.process_time()-cpu0}
        stages.append(stage_result)
        if result.get("term") is not None:
            selected = result["term"]
            break
    predictions = []
    if selected is not None:
        for x in TASKS[task]["heldout"]:
            predicted = selected.evaluate({"x": x}, substrate)
            expected = oracle(task, x)
            exact = isinstance(predicted, (int, float)) and abs(float(predicted)-float(expected)) <= 1e-9
            predictions.append({"x":x, "predicted":predicted, "expected":expected, "exact":exact})
    return {"kind":"worker", "task":task, "repetition":repetition, "pid":os.getpid(),
            "target":TASKS[task]["target"], "required_primitive":TASKS[task]["required_primitive"],
            "stages":stages, "selected_stage":stages[-1]["stage"] if selected is not None else None,
            "selected_term":stages[-1]["term"] if selected is not None else None,
            "heldout":predictions,
            "total_wall_s":time.perf_counter()-started_all, "total_cpu_s":time.process_time()-cpu_all}


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--lock",action="store_true")
    parser.add_argument("--worker",nargs=2,metavar=("TASK","REPETITION")); args=parser.parse_args()
    current=lock_payload()
    if args.lock:
        print(json.dumps(current,indent=2,sort_keys=True)); return
    if not LOCK.is_file() or json.loads(LOCK.read_text()) != current:
        raise SystemExit("source lock absent or stale")
    if args.worker:
        print(json.dumps(worker(args.worker[0],int(args.worker[1])),sort_keys=True,default=str)); return
    if RAW.exists(): raise SystemExit(f"refusing to overwrite {RAW}")
    schedule=[(task,rep) for task in TASKS for rep in range(REPETITIONS)]
    random.Random(SEED).shuffle(schedule)
    env=dict(os.environ); env["PYTHONPATH"]=f"{ROOT}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}"
    rows=[]; started=time.perf_counter()
    for i,(task,rep) in enumerate(schedule,1):
        try:
            proc=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",task,str(rep)],
                                cwd=ROOT,env=env,text=True,capture_output=True,timeout=PARENT_TIMEOUT_S)
            row=(json.loads(proc.stdout.strip().splitlines()[-1]) if proc.returncode == 0 else
                 {"kind":"worker_error","task":task,"repetition":rep,"error":proc.stderr[-3000:]})
        except subprocess.TimeoutExpired:
            row={"kind":"worker_error","task":task,"repetition":rep,"error":"parent timeout"}
        rows.append(row); print(f"{i}/{len(schedule)} {task} rep={rep} {row['kind']}",flush=True)
    raw={"protocol":STEM,"lock":current,"schedule":[list(x) for x in schedule],"workers":rows,
         "elapsed_s":time.perf_counter()-started,"environment":{"python":sys.version,"platform":platform.platform()}}
    RAW.write_text(json.dumps(raw,indent=2,sort_keys=True,default=str)+"\n")
    print(json.dumps({"raw":str(RAW),"workers":len(rows),"errors":sum(r.get('kind')!='worker' for r in rows)}))


if __name__ == "__main__": main()
