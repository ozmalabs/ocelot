#!/usr/bin/env python3
"""Public mutation invalidation panel for ReachableFrom's persistent EvalCache."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts")]
from domains.engine_provenance import build_is_stale
from substrate.world_adapter import WorldAdapter
from substrate_run_manifest import capture_run_manifest, finish_console_capture, start_console_capture
from substrate_rs import _native

PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_REACHABLE_CACHE_MUTATION_V1_PREREG_20260928.md"
LOCK = ROOT / "evaluation/substrate_capability/reachable_cache_mutation_v1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/substrate_reachable_cache_mutation_v1_20260928.json"
RUN_ID = "substrate-reachable-cache-mutation-v1-20260928"
CASES = ("add_node", "insert_edges_unchecked", "insert_edge_checked", "remove_edge",
         "remove_edges_batch", "remove_node", "set_attr", "set_attr_many", "set_attr_each", "set_type")
REPS = 3
FILES = (
    "scripts/substrate_reachable_cache_mutation_v1.py",
    "scripts/analyze_substrate_reachable_cache_mutation_v1.py",
    "scripts/substrate_run_manifest.py", "domains/engine_provenance.py",
    "substrate/world_adapter.py", "substrate/boot_core.py", "substrate/seed_loader.py",
    "seeds/browser_affordance_reach.json", "runners/dsl/src/term.rs",
    "runners/dsl/src/substrate.rs", "runners/dsl/src/py.rs", "runners/dsl/src/rewrite.rs",
    "runners/dsl/src/graph.rs", "runners/dsl/python/substrate_rs/_native.build.json",
    "runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock", str(PROTOCOL.relative_to(ROOT)),
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint() -> dict:
    native = Path(_native.__file__).resolve()
    return {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "files": {p: sha(ROOT / p) for p in FILES}, "native_path": str(native),
            "native_sha256": sha(native), "native_build_stale": build_is_stale(str(ROOT))}


def make_world(cache: bool):
    world = WorldAdapter(seeds=("browser_affordance_reach",), shadow_read=False, deep_ingest=False)
    world.inner.set_reachable_cache(cache)
    session = world.s.add_node("WorldInstance", {"world_type": "Session", "id": "session"})
    elements, affordances = [], []
    for i in range(4):
        element = world.s.add_node("WorldInstance", {"world_type": "Element", "id": f"e{i}",
            "present": 1.0, "tag": "a", "text": f"element {i}"})
        affordance = world.s.add_node("Affordance", {"world_id": f"a{i}", "kind": "navigate"})
        world.inner.add_edge_unchecked(session, "contains", element, {})
        world.inner.add_edge_unchecked(element, "affords", affordance, {})
        world.inner.add_edge_unchecked(session, "has_affordance", affordance, {})
        elements.append(element)
        affordances.append(affordance)
    return world, session, elements, affordances


def add_candidate(world, session, checked: bool):
    element = world.s.add_node("WorldInstance", {"world_type": "Element", "id": "e-new",
        "present": 1.0, "tag": "a", "text": "new element"})
    affordance = world.s.add_node("Affordance", {"world_id": "a-new", "kind": "navigate"})
    if checked:
        world.s.add_production({"src": {"type": "WorldInstance", "var": "s"},
            "edge_type": "contains", "tgt": {"type": "WorldInstance", "var": "t"},
            "where": None, "weight": {"type": "Lit", "value": 1.0},
            "provenance": "reachable_cache_mutation_v1"})
        world.s.add_edge(session, "contains", element)
    else:
        world.inner.add_edge_unchecked(session, "contains", element, {})
    world.inner.add_edge_unchecked(element, "affords", affordance, {})
    # Keep the rule effect idempotent so the refreshed cache remains observable
    # after fixpoint: derived mirror-edge insertion itself clears graph memos.
    world.inner.add_edge_unchecked(session, "has_affordance", affordance, {})
    return element, affordance


def mutate(world, session, elements, affordances, case: str):
    if case == "add_node":
        world.s.add_node("MutationSentinel", {"id": "isolated"})
        expected = 4
    elif case in ("insert_edges_unchecked", "insert_edge_checked"):
        _, new_aff = add_candidate(world, session, case == "insert_edge_checked")
        affordances.append(new_aff)
        expected = 5
    elif case == "remove_edge":
        world.s.remove_edge(session, "contains", elements[0])
        expected = 3
    elif case == "remove_edges_batch":
        outcomes = world.inner.remove_edges_batch([(session.value, "contains", elements[0].value),
                                                   (session.value, "contains", elements[1].value)])
        if outcomes != [True, True]:
            raise AssertionError(f"batch deletion results {outcomes}")
        expected = 2
    elif case == "remove_node":
        world.s.remove_node(elements[0])
        affordances.remove(affordances[0])
        expected = 3
    elif case == "set_attr":
        world.s.set_attr(elements[0], "present", 2.0)
        expected = 4
    elif case == "set_attr_many":
        world.s.set_attr_many(elements[:2], "present", 2.0)
        expected = 4
    elif case == "set_attr_each":
        world.s.set_attr_each(elements[:2], "present", [2.0, 2.0])
        expected = 4
    elif case == "set_type":
        world.s.set_type(elements[0], "RenamedWorldElement")
        expected = 4
    else:
        raise ValueError(case)
    return expected


def one_arm(case: str, cache: bool) -> dict:
    world, session, elements, affordances = make_world(cache)
    loaded = sorted(row[1] for row in world.inner.rule_access_sets())
    prime_steps = int(world.inner.run_rules(100_000))
    before = {str(k): int(v) for k, v in dict(world.inner.reachable_cache_stats()).items()}
    # This resets only hit/miss counters. A live one-entry memo must remain.
    world.inner.reachable_cache_stats_reset()
    expected_reachable = mutate(world, session, elements, affordances, case)
    steps = int(world.inner.run_rules(100_000))
    after = {str(k): int(v) for k, v in dict(world.inner.reachable_cache_stats()).items()}
    mirror = sum(bool(world.inner.has_edge(session, "has_affordance", aff)) for aff in affordances)
    graph = world.inner.graph_to_dict()
    world.close()
    return {"cache": cache, "loaded_rule_names": loaded, "prime_steps": prime_steps,
        "before_stats": before, "expected_reachable": expected_reachable, "steps": steps,
        "after_stats": after, "mirror_count": mirror, "graph": graph}


def worker(case: str, replicate: int) -> dict:
    before = fingerprint()
    order = [False, True] if replicate % 2 == 0 else [True, False]
    arms = {str(cache).lower(): one_arm(case, cache) for cache in order}
    after = fingerprint()
    return {"case": case, "replicate": replicate, "pid": os.getpid(),
        "arm_order": [str(c).lower() for c in order], "before": before, "after": after, "arms": arms}


def main() -> int:
    if sys.argv[1:] == ["--lock"]:
        fp = fingerprint()
        if fp["native_build_stale"]:
            raise SystemExit("native build is stale")
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps(fp, indent=2, sort_keys=True) + "\n")
        print(LOCK)
        return 0
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        print(json.dumps(worker(sys.argv[2], int(sys.argv[3])), sort_keys=True))
        return 0
    initial = fingerprint()
    if initial["native_build_stale"] or not LOCK.exists() or json.loads(LOCK.read_text()) != initial:
        raise SystemExit("missing/stale source lock or native build")
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join((str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts"), env.get("PYTHONPATH", "")))
    started = datetime.now(timezone.utc).isoformat()
    log = start_console_capture(RUN_ID)
    rows = []
    try:
        for case in CASES:
            for rep in range(REPS):
                cp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", case, str(rep)],
                    cwd=ROOT, env=env, text=True, capture_output=True, check=True)
                rows.append(json.loads(cp.stdout))
    except Exception:
        finish_console_capture(log)
        raise
    final = fingerprint()
    checks = {
        "complete_30_worker_matrix": len(rows) == len(CASES) * REPS and all(sum(r["case"] == c for r in rows) == REPS for c in CASES),
        "unique_workers_and_counterbalanced_cache_order": len({r["pid"] for r in rows}) == len(rows) and all(r["arm_order"] == (["false", "true"] if r["replicate"] % 2 == 0 else ["true", "false"]) for r in rows),
        "stable_source_native_lock": initial == final and all(r["before"] == initial == r["after"] for r in rows),
        "fresh_native_build": not initial["native_build_stale"],
        "loaded_browser_rules": all(set(a["loaded_rule_names"]) == {"browser_mirror_has_affordance_reachable", "browser_drop_has_affordance_stale"} for r in rows for a in r["arms"].values()),
        "live_cache_primed_before_each_mutation": all((not a["cache"] or (a["before_stats"]["entries"] == 1 and a["before_stats"]["result_values"] == 4)) and a["prime_steps"] == 0 for r in rows for a in r["arms"].values()),
        "off_cache_stats_zero": all(not any(a["after_stats"].get(k, 0) for k in ("hits", "misses", "entries", "result_values", "footprint_nodes", "estimated_payload_bytes")) for r in rows for a in r["arms"].values() if not a["cache"]),
        "on_cache_fresh_miss_and_one_result": all(a["after_stats"]["misses"] > 0 and a["after_stats"]["entries"] == 1 and a["after_stats"]["result_values"] == a["expected_reachable"] for r in rows for a in r["arms"].values() if a["cache"]),
        "cache_on_off_semantic_parity": all(r["arms"]["false"]["graph"] == r["arms"]["true"]["graph"] and r["arms"]["false"]["steps"] == r["arms"]["true"]["steps"] and r["arms"]["false"]["mirror_count"] == r["arms"]["true"]["mirror_count"] for r in rows),
        "reachable_set_expectations": all(a["after_stats"].get("result_values", 0) == a["expected_reachable"] for r in rows for a in r["arms"].values() if a["cache"]),
    }
    logref = finish_console_capture(log)
    manifest = capture_run_manifest(run_id=RUN_ID, runner="scripts/substrate_reachable_cache_mutation_v1.py",
        protocol_files=(str(PROTOCOL.relative_to(ROOT)), str(LOCK.relative_to(ROOT))),
        source_files=tuple(p for p in FILES if p.startswith(("runners/", "substrate/", "seeds/"))),
        analysis_files=("scripts/analyze_substrate_reachable_cache_mutation_v1.py",),
        started_utc=started, exit_status=0 if all(checks.values()) else 1, stdout_stderr_capture=logref)
    raw = {"schema_version": 1, "run_id": RUN_ID, "locked_inputs": initial, "post_run_inputs": final,
        "checks": checks, "all_checks_pass": all(checks.values()), "cases": list(CASES), "runs": rows,
        "run_manifest": manifest,
        "claim_boundary": "Public Python/native mutation-path freshness and cache-on/off parity for browser_affordance_reach. Deletion cases do not test retraction of stale derived mirror edges; no timing or natural workload claim."}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "all_checks_pass": raw["all_checks_pass"], "raw": str(RAW.relative_to(ROOT))}, indent=2))
    return 0 if raw["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
