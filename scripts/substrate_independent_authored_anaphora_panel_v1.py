#!/usr/bin/env python3
"""Source-locked default-boot anaphora transfer and cost panel."""
from __future__ import annotations
import hashlib, json, os, platform, random, resource, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_INDEPENDENT_AUTHORED_ANAPHORA_PANEL_V1_PREREG_20260929.md"
SUITE = ROOT / "evaluation/substrate_capability/anaphora_independent_task_suite_v1.json"
ANALYZER = ROOT / "scripts/analyze_substrate_independent_authored_anaphora_panel_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/independent_authored_anaphora_panel_v1_lock_20260929.json"
RAW = ROOT / "evaluation/reports/independent_authored_anaphora_panel_v1_raw_20260929.json"
SUMMARY = ROOT / "evaluation/reports/independent_authored_anaphora_panel_v1_20260929.json"
CASES = {row["case_id"]: row for row in json.loads(SUITE.read_text())["cases"]}
REPEATS = tuple(range(10))
CAP = 100_000

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def seed_paths():
    from substrate.boot_core import CORE_SEEDS
    from substrate.seeds import REGISTRY
    import domains.seed_registry
    closure = REGISTRY.resolve((*CORE_SEEDS, "intent"))
    return sorted({f"seeds/{seed.id}.json" for seed in closure})

def fingerprint():
    from substrate_rs import _native
    from domains.engine_provenance import build_is_stale
    paths = seed_paths() + [
        str(p.relative_to(ROOT)) for p in (PROTOCOL, SUITE, ANALYZER, Path(__file__),
            ROOT / "substrate/world_adapter.py", ROOT / "substrate/boot_core.py",
            ROOT / "substrate/seed_loader.py", ROOT / "substrate/seeds.py",
            ROOT / "domains/seed_registry.py", ROOT / "domains/engine_provenance.py",
            ROOT / "domains/language_world.py", ROOT / "runners/dsl/src/substrate.rs",
            ROOT / "runners/dsl/src/rewrite.rs", ROOT / "runners/dsl/src/py.rs",
            ROOT / "runners/dsl/src/scale_audit.rs",
            ROOT / "runners/dsl/python/substrate_rs/_native.build.json")]
    return {"files": {p: sha(ROOT / p) for p in sorted(set(paths))},
            "native_sha256": sha(Path(_native.__file__).resolve()),
            "native_path": str(Path(_native.__file__).resolve()),
            "cargo_lock_sha256": sha(ROOT / "runners/dsl/Cargo.lock"),
            "build_stale": build_is_stale(str(ROOT)),
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()}

def digest(graph):
    return hashlib.sha256(json.dumps(graph, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()

def nid(value):
    return int(value.value if hasattr(value, "value") else value)

def inspect_case(wa, message_id, pronoun):
    mentions = [n for n in wa.inner.neighbours(message_id, "has_mention")
                if wa.s.node(n)["attrs"].get("text", "").lower() == pronoun]
    refs = [r for m in mentions for r in wa.inner.neighbours(m, "refers_to")]
    names = sorted(str(wa.s.node(r)["attrs"].get("name")) for r in refs if wa.s.has_node(r))
    intent = wa.intent_of(message_id)
    about = [] if intent is None else [str(wa.s.node(c)["attrs"].get("name"))
                                        for c in wa.inner.neighbours(intent, "about_concept")]
    return {"pronoun_count": len(mentions), "referent_names": names,
            "intent_exists": intent is not None, "intent_about_names": sorted(about)}

def run_case(case_id, task):
    from substrate.world_adapter import WorldAdapter
    adapter_start_wall, adapter_start_cpu = time.perf_counter_ns(), time.process_time_ns()
    wa = WorldAdapter()
    adapter_init_wall = time.perf_counter_ns() - adapter_start_wall
    adapter_init_cpu = time.process_time_ns() - adapter_start_cpu
    turns = []
    final_mid = None
    for text in task["turns"]:
        t0, c0 = time.perf_counter_ns(), time.process_time_ns()
        mid = wa.receive_utterance(text, speech_act="statement", speaker="user")
        receive_wall, receive_cpu = time.perf_counter_ns() - t0, time.process_time_ns() - c0
        t0, c0 = time.perf_counter_ns(), time.process_time_ns()
        progress = int(wa.comprehend())
        comprehend_wall, comprehend_cpu = time.perf_counter_ns() - t0, time.process_time_ns() - c0
        turns.append({"message_id": nid(mid), "text": text, "receive_wall_ns": receive_wall,
                      "receive_cpu_ns": receive_cpu, "comprehend_wall_ns": comprehend_wall,
                      "comprehend_cpu_ns": comprehend_cpu, "comprehend_progress": progress})
        final_mid = mid
    pronoun = task["pronoun"]
    projection = inspect_case(wa, final_mid, pronoun)
    graph = wa.inner.graph_to_dict()
    return {"case_id": case_id, "turns": turns,
            "default_adapter_init_wall_ns": adapter_init_wall,
            "default_adapter_init_cpu_ns": adapter_init_cpu,
            "projection": projection,
            "expected_referent": task["expected_referent"],
            "expected_intent_about": task["expected_intent_about"],
            "graph_digest": digest(graph), "graph_nodes": len(graph["nodes"]),
            "graph_edges": len(graph["edges"])}

def worker(rep):
    start_wall, start_cpu = time.perf_counter_ns(), time.process_time_ns()
    rows = []
    for case_id, task in CASES.items():
        t0, c0 = time.perf_counter_ns(), time.process_time_ns()
        row = run_case(case_id, task)
        row["adapter_and_case_wall_ns"] = time.perf_counter_ns() - t0
        row["adapter_and_case_cpu_ns"] = time.process_time_ns() - c0
        rows.append(row)
    return {"replicate": rep, "pid": os.getpid(), "cases": rows,
            "worker_wall_ns": time.perf_counter_ns() - start_wall,
            "worker_cpu_ns": time.process_time_ns() - start_cpu,
            "peak_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)}

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        before = fingerprint(); data = worker(int(sys.argv[2])); after = fingerprint()
        print(json.dumps({"before": before, "after": after, "worker": data}, sort_keys=True)); return 0
    if sys.argv[1:] == ["--lock"]:
        inputs = fingerprint()
        if inputs["build_stale"]: raise SystemExit("native build is stale")
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        if LOCK.exists(): raise SystemExit("refusing to overwrite lock")
        LOCK.write_text(json.dumps({"locked_inputs": inputs}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT)); return 0
    locked = fingerprint()
    if locked["build_stale"] or not LOCK.is_file() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale source/native lock")
    if RAW.exists() or SUMMARY.exists(): raise SystemExit("refusing to overwrite capture")
    env = dict(os.environ)
    env.update({"PYTHONPATH": os.pathsep.join((str(ROOT), str(ROOT / "runners/dsl/python"), env.get("PYTHONPATH", ""))),
                "PYTHONHASHSEED": "0", "OZMA_NO_LLM": "1", "OZMA_SEED_PERSIST_DISABLED": "1"})
    order = list(REPEATS); random.Random(20260929).shuffle(order); runs = []
    for index, rep in enumerate(order, 1):
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(rep)],
                              cwd=ROOT, env=env, text=True, capture_output=True)
        runs.append(json.loads(proc.stdout) if proc.returncode == 0 else
                    {"replicate": rep, "worker_error": proc.stderr[-4000:]})
        RAW.write_text(json.dumps({"schema_version": 1, "run_id": "independent-authored-anaphora-panel-v1-20260929", "locked_inputs": locked,
                                   "post_run_inputs": fingerprint(), "runs": runs},
                                  indent=2, sort_keys=True) + "\n")
        print(f"worker {index}/10 replicate={rep} rc={proc.returncode}", flush=True)
    post = fingerprint()
    payload = {"schema_version": 1, "run_id": "independent-authored-anaphora-panel-v1-20260929",
               "locked_inputs": locked, "post_run_inputs": post,
               "raw_path": str(RAW.relative_to(ROOT)), "case_ids": list(CASES),
               "environment": {"python": sys.version, "platform": platform.platform()}}
    SUMMARY.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"raw": str(RAW.relative_to(ROOT)), "summary": str(SUMMARY.relative_to(ROOT)),
                      "source_stable": locked == post, "worker_count": len(runs)}, indent=2))
    return 0 if locked == post and len(runs) == len(REPEATS) and all("worker_error" not in r for r in runs) else 1

if __name__ == "__main__": raise SystemExit(main())
