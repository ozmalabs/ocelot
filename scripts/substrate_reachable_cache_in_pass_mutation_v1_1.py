#!/usr/bin/env python3
"""Locked reproducer for stale ReachableFrom reads after an in-pass rule write."""
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
from substrate_run_manifest import capture_run_manifest, finish_console_capture, start_console_capture
from substrate_rs import Substrate, _native

PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_REACHABLE_CACHE_IN_PASS_MUTATION_V1_1_PREREG_20260928.md"
LOCK = ROOT / "evaluation/substrate_capability/reachable_cache_in_pass_mutation_v1_1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/substrate_reachable_cache_in_pass_mutation_v1_1_20260928.json"
RUN_ID = "substrate-reachable-cache-in-pass-mutation-v1-1-20260928"
REPS = 5
FILES = (
    "scripts/substrate_reachable_cache_in_pass_mutation_v1_1.py",
    "scripts/analyze_substrate_reachable_cache_in_pass_mutation_v1_1.py",
    "scripts/substrate_run_manifest.py", "domains/engine_provenance.py",
    "runners/dsl/src/term.rs", "runners/dsl/src/substrate.rs", "runners/dsl/src/rewrite.rs",
    "runners/dsl/src/py.rs", "runners/dsl/src/graph.rs",
    "runners/dsl/python/substrate_rs/_native.build.json", "runners/dsl/Cargo.toml",
    "runners/dsl/Cargo.lock", str(PROTOCOL.relative_to(ROOT)),
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint() -> dict:
    native = Path(_native.__file__).resolve()
    return {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "files": {p: sha(ROOT / p) for p in FILES}, "native_path": str(native),
        "native_sha256": sha(native), "native_build_stale": build_is_stale(str(ROOT))}


def rule_defs() -> list[dict]:
    reachable = lambda var: {"type": "In", "member": {"type": "Var", "name": var},
        "container": {"type": "ReachableFrom", "node": {"type": "Var", "name": "s"}, "edge_type": "path"}}
    return [
        {"name": "prime_reachable", "match": [["s", "probe", "a"]],
         "where": reachable("a"), "effects": [["add_edge", "s", "marker", "a"]]},
        {"name": "insert_path", "match": [["s", "add_path", "t"]],
         "effects": [["add_edge", "s", "path", "t"]]},
        {"name": "detect_new_reachable", "match": [["s", "detect", "t"]],
         "where": reachable("t"), "effects": [["add_edge", "s", "detected", "t"]]},
    ]


def arm(cache: bool) -> dict:
    substrate = Substrate()
    native = substrate._inner
    native.set_reachable_cache(cache)
    root = substrate.add_node("N")
    old = substrate.add_node("N")
    new = substrate.add_node("N")
    for src, et, tgt in ((root, "path", old), (root, "probe", old), (root, "marker", old),
                         (root, "add_path", new), (root, "detect", new)):
        substrate.add_edge_unchecked(src, et, tgt)
    rule_ids = [native.add_rule(rule) for rule in rule_defs()]
    access = native.rule_access_sets()
    steps = int(native.run_rules(100))
    graph = native.graph_to_dict()
    detected = bool(native.has_edge(root, "detected", new))
    stats = {str(k): int(v) for k, v in dict(native.reachable_cache_stats()).items()}
    return {"cache": cache, "rule_ids": rule_ids, "rule_access_sets": [list(row) for row in access],
        "steps": steps, "detected": detected, "graph": graph, "cache_stats": stats}


def worker(rep: int) -> dict:
    before = fingerprint()
    order = [False, True] if rep % 2 == 0 else [True, False]
    arms = {str(cache).lower(): arm(cache) for cache in order}
    after = fingerprint()
    return {"replicate": rep, "pid": os.getpid(), "arm_order": [str(x).lower() for x in order],
        "before": before, "after": after, "arms": arms}


def main() -> int:
    if sys.argv[1:] == ["--lock"]:
        fp = fingerprint()
        if fp["native_build_stale"]:
            raise SystemExit("native build is stale")
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps(fp, indent=2, sort_keys=True) + "\n")
        print(LOCK)
        return 0
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True))
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
        for rep in range(REPS):
            cp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(rep)], cwd=ROOT,
                env=env, text=True, capture_output=True, check=True)
            rows.append(json.loads(cp.stdout))
    except Exception:
        finish_console_capture(log)
        raise
    final = fingerprint()
    checks = {
        "five_fresh_counterbalanced_workers": len(rows) == 5 and len({r["pid"] for r in rows}) == 5 and all(r["arm_order"] == (["false", "true"] if r["replicate"] % 2 == 0 else ["true", "false"]) for r in rows),
        "stable_source_lock_and_fresh_native": initial == final and not initial["native_build_stale"] and all(r["before"] == initial == r["after"] for r in rows),
        "three_rule_read_write_dependencies": all(len(a["rule_access_sets"]) == 3 and "edge:path" in a["rule_access_sets"][2][3] and "edge:path" in a["rule_access_sets"][1][5] for r in rows for a in r["arms"].values()),
        "cache_off_detects_new_reachable_node": all(r["arms"]["false"]["detected"] and r["arms"]["false"]["steps"] == 2 for r in rows),
        "cache_on_and_off_detect_new_reachable_node": all(r["arms"]["true"]["detected"] and r["arms"]["false"]["detected"] and r["arms"]["true"]["steps"] == r["arms"]["false"]["steps"] == 2 for r in rows),
        "final_graphs_match_exactly": all(r["arms"]["false"]["graph"] == r["arms"]["true"]["graph"] for r in rows),
        "cache_stats_match_execution_modes": all(r["arms"]["false"]["cache_stats"]["hits"] == r["arms"]["false"]["cache_stats"]["misses"] == 0 and r["arms"]["true"]["cache_stats"]["misses"] >= 2 for r in rows),
    }
    logref = finish_console_capture(log)
    manifest = capture_run_manifest(run_id=RUN_ID, runner="scripts/substrate_reachable_cache_in_pass_mutation_v1_1.py",
        protocol_files=(str(PROTOCOL.relative_to(ROOT)), str(LOCK.relative_to(ROOT))),
        source_files=tuple(p for p in FILES if p.startswith("runners/")),
        analysis_files=("scripts/analyze_substrate_reachable_cache_in_pass_mutation_v1_1.py",),
        started_utc=started, exit_status=0 if all(checks.values()) else 1, stdout_stderr_capture=logref)
    raw = {"schema_version": 1, "run_id": RUN_ID, "locked_inputs": initial, "post_run_inputs": final,
        "checks": checks, "all_checks_pass": all(checks.values()), "runs": rows, "run_manifest": manifest,
        "claim_boundary": "Locked minimal in-pass mutation regression: immediate cache invalidation preserves cache-on/off fixed-point semantics for one monotone three-rule probe. No natural workload or timing claim."}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "all_checks_pass": raw["all_checks_pass"], "raw": str(RAW.relative_to(ROOT))}, indent=2))
    return 0 if raw["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
