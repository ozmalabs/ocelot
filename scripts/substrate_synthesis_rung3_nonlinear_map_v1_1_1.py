#!/usr/bin/env python3
"""Locked end-to-end Rung 3 program synthesis on four integer maps."""
from __future__ import annotations
import hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
from domains.engine_provenance import engine_preamble, engine_provenance
engine_preamble()
import substrate_rs as srs
import domains.prog_synthesis as psy

STEM = "synthesis_rung3_nonlinear_map_v1_1_1_20260929"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_SYNTHESIS_RUNG3_NONLINEAR_MAP_V1_1_1_AMENDMENT_20260929.md"
LOCK = ROOT / f"evaluation/substrate_capability/{STEM}_lock.json"
RAW = ROOT / f"evaluation/reports/{STEM}_raw.jsonl"
ANALYZER = ROOT / "scripts/analyze_substrate_synthesis_rung3_nonlinear_map_v1.py"
REPETITIONS = 5
SOURCE_PATHS = (
    "domains/prog_synthesis.py", "domains/engine_provenance.py",
    "seeds/program_synthesis.json", "seeds/program_synthesis_opgrammar.json",
    "runners/dsl/src/synth_enumerate.rs", "runners/dsl/src/prog_eval.rs",
    "runners/dsl/src/term.rs", "runners/dsl/src/py.rs",
    "runners/dsl/src/graph_rules.rs", "runners/dsl/src/substrate.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
)
TASKS = {
    "linear": {
        "request": "write a function map_linear that returns a transformed pair",
        "formula": "(r+c,c+c)",
        "training": [(0,0),(1,0),(0,1),(1,1),(0,2),(1,2)],
        "heldout": [(0,3),(2,3),(1,4),(4,4),(2,5),(5,5)],
    },
    "quadratic_shear": {
        "request": "write a function map_quad that returns a transformed pair",
        "formula": "(r+c*c,c)",
        "training": [(0,0),(1,0),(0,1),(1,1),(0,2),(1,2)],
        "heldout": [(0,3),(2,3),(1,4),(4,4),(2,5),(5,5)],
    },
    "hinge_shear": {
        "request": "write a function map_hinge that returns a transformed pair",
        "formula": "(r+max(c-1,0),c)",
        "training": [(0,0),(1,0),(0,1),(1,1),(0,2),(1,2)],
        "heldout": [(0,3),(2,3),(1,4),(4,4),(2,5),(5,5)],
    },
    "absolute_shear": {
        "request": "write a function map_absolute that returns a transformed pair",
        "formula": "(r+abs(c-2),c)",
        "training": [(0,0),(1,0),(0,1),(1,1),(0,3),(1,3),(0,4),(1,4)],
        "heldout": [(0,-1),(2,-1),(1,2),(4,2),(2,5),(5,5)],
    },
}

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def expected(task, r, c):
    if task == "linear": return [r+c, c+c]
    if task == "quadratic_shear": return [r+c*c, c]
    if task == "hinge_shear": return [r+max(c-1,0), c]
    if task == "absolute_shear": return [r+abs(c-2), c]
    raise KeyError(task)

def task_rows(task, split):
    t = TASKS[task]
    return [{"inputs": {"r": r, "c": c}, "output": expected(task,r,c)}
            for r,c in t[split]]

def lock_body():
    return {"schema": 1, "protocol": STEM, "tasks": json.loads(json.dumps(TASKS)),
            "repetitions": REPETITIONS, "entrypoint": "ensure_program_synthesis -> ingest_spec -> pump"}

def lock_payload():
    native = Path(srs._native.__file__).resolve()
    return {"protocol_sha256": sha(PROTOCOL), "runner_sha256": sha(__file__),
            "analyzer_sha256": sha(ANALYZER),
            "source_sha256": {p: sha(ROOT/p) for p in SOURCE_PATHS},
            "native_extension": {"path": str(native), "sha256": sha(native)},
            "engine_provenance": engine_provenance(), "inputs": lock_body()}

def get_goal(sub, message):
    goals = sub.in_neighbours(message, "about_message")
    if len(goals) != 1:
        raise RuntimeError(f"expected exactly one goal, found {len(goals)}")
    return goals[0], psy.read_goal(sub, goals[0])

def run_worker(task, repetition):
    pre = lock_payload()
    sub = srs.Substrate()
    agent = sub.add_node("Agent", {})
    psy.ensure_program_synthesis(sub, sub._inner, agent)
    train = [(row["inputs"], tuple(row["output"])) for row in task_rows(task, "training")]
    message = psy.ingest_spec(sub, agent, TASKS[task]["request"], train)
    wall0, cpu0 = time.perf_counter_ns(), time.process_time_ns()
    psy.pump(sub, agent)
    wall_ns, cpu_ns = time.perf_counter_ns()-wall0, time.process_time_ns()-cpu0
    goal, result = get_goal(sub, message)
    attrs = sub.node(goal)["attrs"]
    program_nodes = sub.nodes("Program")
    outputs, reflect_roots, eval_errors = [], [], []
    if result.get("status") == "accepted" and result.get("program") is not None:
        program = result["program"]
        reflect_roots = sub.neighbours(program, "ir_subgraph")
        for row in task_rows(task, "heldout"):
            if len(reflect_roots) != 1:
                outputs.append({"inputs": row["inputs"], "expected": row["output"],
                                "predicted": None, "exact": False, "error": "ir_root_count"})
                continue
            try:
                out = sub._inner.evaluate(
                    {"type": "ProgEval", "prog": {"type": "Var", "name": "p"},
                     "env": {"type": "Var", "name": "e"}, "oracles": None,
                     "fuel": 10000, "field": ""},
                    {"e": row["inputs"], "p": reflect_roots[0]})
                pred = out.get("result") if out.get("trap") is None and out.get("halted") else None
                pred = list(pred) if isinstance(pred, (list, tuple)) else pred
                outputs.append({"inputs": row["inputs"], "expected": row["output"],
                                "predicted": pred, "exact": pred == row["output"],
                                "trap": out.get("trap"), "halted": out.get("halted")})
            except Exception as e:
                eval_errors.append(type(e).__name__ + ": " + str(e)[:200])
                outputs.append({"inputs": row["inputs"], "expected": row["output"],
                                "predicted": None, "exact": False, "error": eval_errors[-1]})
    program_summary = []
    for node in program_nodes:
        a = sub.node(node)["attrs"]
        program_summary.append({"node": str(node), "name": a.get("name"),
                                "program_json": a.get("program")})
    picked = {k: attrs.get(k) for k in (
        "ps_enum_ops", "ps_enum_gamma_ops_admitted", "ps_enum_gamma_ops_used",
        "ps_enumerate_outcome", "ps_enum_candidates", "ps_enum_tested",
        "ps_enum_halt_reason", "ps_enum_note", "ps_attempts", "ps_status",
        "ps_gap_reason", "ps_rung_enumerate")}
    post = lock_payload()
    return {"kind": "worker", "task": task, "repetition": repetition,
            "source_native_stable": pre == post,
            "status": result.get("status"), "gap_reason": result.get("gap_reason"),
            "rungs": result.get("rungs"), "enumerate_outcome": result.get("enumerate_outcome"),
            "enumerate_note": result.get("enumerate_note"), "attempts": result.get("attempts"),
            "goal_facts": picked, "program_count": len(program_nodes),
            "programs": program_summary, "ir_root_count": len(reflect_roots),
            "heldout": outputs, "evaluation_errors": eval_errors,
            "acquisition_wall_ns": wall_ns, "acquisition_cpu_ns": cpu_ns,
            "peak_rss_bytes": int(__import__("resource").getrusage(__import__("resource").RUSAGE_SELF).ru_maxrss*1024),
            "engine_provenance": post["engine_provenance"]}

def main():
    if sys.argv[1:] == ["--lock"]:
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps(lock_payload(), indent=2, sort_keys=True)+"\n")
        print(f"locked {LOCK.relative_to(ROOT)}")
        return
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        os.environ["OZMA_NO_LLM"] = "1"
        os.environ["OZMA_SEED_PERSIST_DISABLED"] = "1"
        print(json.dumps(run_worker(sys.argv[2], int(sys.argv[3])), sort_keys=True))
        return
    if sys.argv[1:]: raise SystemExit("usage: runner.py [--lock | --worker TASK REP]")
    if not LOCK.exists() or json.loads(LOCK.read_text()) != lock_payload():
        raise SystemExit("missing/stale lock; preserve artifacts and create a versioned amendment")
    if RAW.exists(): raise SystemExit(f"refusing to overwrite {RAW}")
    os.environ["OZMA_NO_LLM"] = "1"
    os.environ["OZMA_SEED_PERSIST_DISABLED"] = "1"
    schedule = [(task, rep) for task in TASKS for rep in range(REPETITIONS)]
    rows, start = [], time.perf_counter_ns()
    for i,(task,rep) in enumerate(schedule,1):
        proc = subprocess.run([sys.executable, str(__file__), "--worker", task, str(rep)],
                              cwd=ROOT, env=os.environ.copy(), text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if proc.returncode:
            row = {"kind":"worker", "task":task, "repetition":rep,
                   "worker_failed":True, "returncode":proc.returncode,
                   "stdout_tail":proc.stdout[-1000:], "stderr_tail":proc.stderr[-2000:]}
        else:
            try: row = json.loads(proc.stdout.strip().splitlines()[-1])
            except Exception as e:
                row = {"kind":"worker", "task":task, "repetition":rep,
                       "worker_failed":True, "parse_error":str(e),
                       "stdout_tail":proc.stdout[-1000:], "stderr_tail":proc.stderr[-2000:]}
        rows.append(row)
        print(f"worker={i}/{len(schedule)} task={task} rep={rep+1} status={row.get('status')} enum={row.get('enumerate_outcome')}", flush=True)
    post = lock_payload()
    with RAW.open("x", encoding="utf-8") as f:
        f.write(json.dumps({"kind":"header", "run_id":STEM, "lock":json.loads(LOCK.read_text()),
                            "schedule":[[t,r] for t,r in schedule]},sort_keys=True,separators=(",",":"))+"\n")
        for row in rows: f.write(json.dumps(row,sort_keys=True,separators=(",",":"))+"\n")
        f.write(json.dumps({"kind":"footer", "source_native_stable":post==json.loads(LOCK.read_text()),
                            "post_lock_payload":post, "capture_wall_ns":time.perf_counter_ns()-start},
                           sort_keys=True,separators=(",",":"))+"\n")
    print(f"raw={RAW.relative_to(ROOT)} workers={len(rows)}")

if __name__ == "__main__": main()
