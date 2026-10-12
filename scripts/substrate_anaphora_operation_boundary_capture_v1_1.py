#!/usr/bin/env python3
"""Capture message-turn state/access boundaries on the frozen anaphora suite."""
from __future__ import annotations
import hashlib, json, os, platform, random, resource, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_ANAPHORA_OPERATION_BOUNDARY_CAPTURE_V1_1_AMENDMENT_20260929.md"
SUITE = ROOT / "evaluation/substrate_capability/anaphora_independent_task_suite_v1.json"
ANALYZER = ROOT / "scripts/analyze_substrate_anaphora_operation_boundary_capture_v1_1.py"
LOCK = ROOT / "evaluation/substrate_capability/anaphora_operation_boundary_capture_v1_1_lock_20260929.json"
RAW = ROOT / "evaluation/reports/anaphora_operation_boundary_capture_v1_1_raw_20260929.json"
SUMMARY = ROOT / "evaluation/reports/anaphora_operation_boundary_capture_v1_1_20260929.json"
CASES = json.loads(SUITE.read_text())["cases"]
GLOBAL_TYPES = {"Agent", "Concept", "CommonGround", "DiscourseState", "Interlocutor",
                "LexicalEntry", "Microtheory", "Rule", "Seed", "SeedSummary"}
CAP = 100_000

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def seed_paths():
    from substrate.boot_core import CORE_SEEDS
    from substrate.seeds import REGISTRY
    import domains.seed_registry
    return sorted({f"seeds/{s.id}.json" for s in REGISTRY.resolve((*CORE_SEEDS, "intent"))})

def fingerprint():
    from substrate_rs import _native
    from domains.engine_provenance import build_is_stale
    paths = seed_paths() + [str(p.relative_to(ROOT)) for p in (
        PROTOCOL, SUITE, ANALYZER, Path(__file__), ROOT / "substrate/world_adapter.py",
        ROOT / "substrate/boot_core.py", ROOT / "substrate/seed_loader.py",
        ROOT / "substrate/seeds.py", ROOT / "domains/seed_registry.py",
        ROOT / "domains/engine_provenance.py", ROOT / "domains/language_world.py",
        ROOT / "domains/comprehend_text.py", ROOT / "runners/dsl/src/substrate.rs",
        ROOT / "runners/dsl/src/rewrite.rs", ROOT / "runners/dsl/src/py.rs",
        ROOT / "runners/dsl/src/access_trace.rs", ROOT / "runners/dsl/src/scale_audit.rs",
        ROOT / "runners/dsl/python/substrate_rs/_native.build.json")]
    return {"files": {p: sha(ROOT / p) for p in sorted(set(paths))},
            "native_sha256": sha(Path(_native.__file__).resolve()),
            "native_path": str(Path(_native.__file__).resolve()),
            "cargo_lock_sha256": sha(ROOT / "runners/dsl/Cargo.lock"),
            "build_stale": build_is_stale(str(ROOT)),
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()}

def nid(value): return int(value.value if hasattr(value, "value") else value)

def digest(graph):
    return hashlib.sha256(json.dumps(graph, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()

def static_access(inner):
    result = []
    for index, name, active, reads, term_edges, writes, reads_any, writes_any in inner.rule_access_sets():
        meta = inner.rule_metadata(index)
        result.append({"index": int(index), "uid": int(meta["rule_uid"]), "name": str(name),
                       "active": bool(active), "reads": sorted(set(reads) | set(term_edges)),
                       "writes": sorted(writes), "reads_any": bool(reads_any),
                       "writes_any": bool(writes_any)})
    return result

def run_case(task, traced):
    from substrate.world_adapter import WorldAdapter
    wa = WorldAdapter()
    frame_ids = []
    owner = {}
    checkpoints = []
    turns = []
    before_graph = wa.inner.graph_to_dict()
    known_ids = {int(n["id"]) for n in before_graph["nodes"]}
    boot_global_ids = sorted(known_ids)
    for turn_index, text in enumerate(task["turns"]):
        receive_start, receive_cpu = time.perf_counter_ns(), time.process_time_ns()
        message = wa.receive_utterance(text, speech_act="statement", speaker="user")
        receive_wall = time.perf_counter_ns() - receive_start
        receive_cpu = time.process_time_ns() - receive_cpu
        wa.inner.runtime_access_trace_reset()
        wa.inner.runtime_access_trace_set_enabled(traced)
        comprehend_start, comprehend_cpu = time.perf_counter_ns(), time.process_time_ns()
        progress = int(wa.comprehend())
        comprehend_wall = time.perf_counter_ns() - comprehend_start
        comprehend_cpu = time.process_time_ns() - comprehend_cpu
        wa.inner.runtime_access_trace_set_enabled(False)
        access_rows, dropped = wa.inner.runtime_access_trace_snapshot()
        graph = wa.inner.graph_to_dict()
        types = {int(n["id"]): str(n["type"]) for n in graph["nodes"]}
        new_ids = sorted(set(types) - known_ids)
        owned = [n for n in new_ids if types[n] not in GLOBAL_TYPES]
        global_new = [n for n in new_ids if types[n] in GLOBAL_TYPES]
        owner.update({n: turn_index for n in owned})
        frame_ids.append(nid(message))
        turns.append({"turn_index": turn_index, "message_id": nid(message), "text": text,
                      "receive_wall_ns": receive_wall, "receive_cpu_ns": receive_cpu,
                      "comprehend_wall_ns": comprehend_wall, "comprehend_cpu_ns": comprehend_cpu,
                      "comprehend_progress": progress, "new_node_ids": new_ids,
                      "owned_node_ids": owned, "global_new_node_ids": global_new})
        checkpoints.append({"turn_index": turn_index, "graph_sha256": digest(graph),
                            "node_count": len(graph["nodes"]), "edge_count": len(graph["edges"]),
                            "graph": graph if traced else None,
                            "trace_rows": [[int(uid), str(kind), None if node is None else int(node),
                                            None if resource is None else str(resource),
                                            None if peer is None else int(peer), int(count)]
                                           for uid, kind, node, resource, peer, count in access_rows],
                            "trace_dropped": int(dropped)})
        known_ids = set(types)
    final_mid = message
    pronoun = task["pronoun"]
    mentions = [n for n in wa.inner.neighbours(final_mid, "has_mention")
                if wa.s.node(n)["attrs"].get("text", "").lower() == pronoun]
    refs = [r for m in mentions for r in wa.inner.neighbours(m, "refers_to")]
    referents = sorted(str(wa.s.node(r)["attrs"].get("name")) for r in refs if wa.s.has_node(r))
    intent = wa.intent_of(message)
    about = [] if intent is None else sorted(str(wa.s.node(c)["attrs"].get("name"))
                                              for c in wa.inner.neighbours(intent, "about_concept"))
    final_graph = wa.inner.graph_to_dict()
    return {"case_id": task["case_id"], "traced": traced, "turns": turns,
            "frame_message_ids": frame_ids, "frame_owner": [[n, owner[n]] for n in sorted(owner)],
            "boot_global_node_ids": boot_global_ids,
            "task_projection": {"pronoun_count": len(mentions), "referent_names": referents,
                                "intent_exists": intent is not None, "intent_about_names": about},
            "task_oracle_pass": referents == ([task["expected_referent"]] if task["expected_referent"] else [])
                and (task["expected_intent_about"] is None or
                     ((intent is not None and task["expected_referent"] in about)
                      == task["expected_intent_about"])),
            "checkpoints": checkpoints, "final_graph_sha256": digest(final_graph),
            "final_node_count": len(final_graph["nodes"]), "final_edge_count": len(final_graph["edges"]),
            "final_graph": final_graph if traced else None,
            "static_rule_access": static_access(wa.inner) if traced else None}

def worker(rep):
    started_wall, started_cpu = time.perf_counter_ns(), time.process_time_ns()
    pairs = []
    for task in CASES:
        plain = run_case(task, False)
        traced = run_case(task, True)
        pairs.append({"case_id": task["case_id"], "plain": plain, "trace": traced})
    return {"replicate": rep, "pid": os.getpid(), "pairs": pairs,
            "worker_wall_ns": time.perf_counter_ns() - started_wall,
            "worker_cpu_ns": time.process_time_ns() - started_cpu,
            "peak_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)}

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        before = fingerprint(); result = worker(int(sys.argv[2])); after = fingerprint()
        print(json.dumps({"before": before, "after": after, "worker": result}, sort_keys=True)); return 0
    if sys.argv[1:] == ["--lock"]:
        inputs = fingerprint()
        if inputs["build_stale"]: raise SystemExit("native build is stale")
        if LOCK.exists(): raise SystemExit("refusing to overwrite lock")
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps({"locked_inputs": inputs}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT)); return 0
    locked = fingerprint()
    if locked["build_stale"] or not LOCK.is_file() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale source/native lock")
    if RAW.exists() or SUMMARY.exists(): raise SystemExit("refusing to overwrite capture")
    env = dict(os.environ)
    env.update({"PYTHONPATH": os.pathsep.join((str(ROOT), str(ROOT / "runners/dsl/python"), env.get("PYTHONPATH", ""))),
                "PYTHONHASHSEED": "0", "OZMA_NO_LLM": "1", "OZMA_SEED_PERSIST_DISABLED": "1"})
    order = list(range(10)); random.Random(20260929).shuffle(order); runs = []
    for index, rep in enumerate(order, 1):
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(rep)], cwd=ROOT,
                              env=env, text=True, capture_output=True)
        runs.append(json.loads(proc.stdout) if proc.returncode == 0 else
                    {"replicate": rep, "worker_error": proc.stderr[-5000:]})
        RAW.write_text(json.dumps({"schema_version": 1, "run_id": "anaphora-operation-boundary-capture-v1_1-20260929", "locked_inputs": locked,
                                   "post_run_inputs": fingerprint(), "runs": runs},
                                  separators=(",", ":"), sort_keys=True) + "\n")
        print(f"worker {index}/10 replicate={rep} rc={proc.returncode}", flush=True)
    post = fingerprint()
    payload = {"schema_version": 1, "run_id": "anaphora-operation-boundary-capture-v1_1-20260929",
               "locked_inputs": locked, "post_run_inputs": post,
               "raw_path": str(RAW.relative_to(ROOT)), "suite_sha256": sha(SUITE),
               "environment": {"python": sys.version, "platform": platform.platform()}}
    SUMMARY.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"raw": str(RAW.relative_to(ROOT)), "summary": str(SUMMARY.relative_to(ROOT)),
                      "source_stable": locked == post, "workers": len(runs)}, indent=2))
    return 0 if locked == post and len(runs) == 10 and all("worker_error" not in r for r in runs) else 1

if __name__ == "__main__": raise SystemExit(main())
