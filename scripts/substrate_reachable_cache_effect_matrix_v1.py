#!/usr/bin/env python3
"""Same-pass cache invalidation matrix across graph-mutating rule effects."""
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

PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_REACHABLE_CACHE_EFFECT_MATRIX_V1_PREREG_20260928.md"
LOCK = ROOT / "evaluation/substrate_capability/reachable_cache_effect_matrix_v1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/substrate_reachable_cache_effect_matrix_v1_20260928.json"
RUN_ID = "substrate-reachable-cache-effect-matrix-v1-20260928"
CASES = ("add_edge", "del_edge", "add_node", "add_node_if_absent", "del_node",
         "set_attr", "set_attr_if_different", "replace_value")
REPS = 5
FILES = (
    "scripts/substrate_reachable_cache_effect_matrix_v1.py",
    "scripts/analyze_substrate_reachable_cache_effect_matrix_v1.py",
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


def reachable(var: str) -> dict:
    return {"type": "In", "member": {"type": "Var", "name": var},
        "container": {"type": "ReachableFrom", "node": {"type": "Var", "name": "s"}, "edge_type": "path"}}


def positive_attr_where(var: str) -> dict:
    return {"type": "And", "items": [reachable(var),
        {"type": "Gt", "a": {"type": "Attr", "node": {"type": "Var", "name": var}, "key": "enabled"},
         "b": {"type": "Lit", "value": 0.0}}]}


def rule_specs(case: str, root, subject, middle, new):
    positive = case not in ("del_edge", "del_node", "replace_value")
    detector = new if case == "add_edge" else subject
    detect_where = reachable("t") if positive else {"type": "Not", "arg": reachable("t")}
    if case in ("set_attr", "set_attr_if_different"):
        detect_where = positive_attr_where("t")
    if case == "add_edge":
        mut_match = [["s", "mutate", "t"]]
        mut_effect = ["add_edge", "s", "path", "t"]
        mut_target = new
    elif case == "del_edge":
        mut_match = [["s", "mutate", "t"]]
        mut_effect = ["del_edge", "s", "path", "t"]
        mut_target = subject
    elif case in ("add_node", "add_node_if_absent"):
        mut_match = [["s", "mutate", "t"]]
        mut_effect = ["add_node" if case == "add_node" else "add_node_if_absent",
                      "minted", "Minted", {"id": f"new-{case}"}]
        mut_target = subject
    elif case == "del_node":
        mut_match = [["s", "mutate", "m"]]
        mut_effect = ["del_node", "m"]
        mut_target = subject
    elif case in ("set_attr", "set_attr_if_different"):
        mut_match = [["s", "mutate", "t"]]
        mut_effect = [case, "t", "enabled", 1.0]
        mut_target = subject
    elif case == "replace_value":
        mut_match = [["s", "mutate", "m"], ["s", "replacement", "n"]]
        mut_effect = ["replace_value", "m", "n"]
        mut_target = subject
    else:
        raise ValueError(case)
    prime = {"name": "prime_reachable", "match": [["s", "probe", "x"]],
        "where": reachable("x"), "effects": [["add_edge", "s", "marker", "x"]]}
    mutation = {"name": f"mutate_{case}", "match": mut_match, "effects": [mut_effect]}
    consume = {"name": "consume_reachable", "match": [["s", "detect", "t"]],
        "where": detect_where, "effects": [["add_edge", "s", "detected", "t"]]}
    return prime, mutation, consume, mut_target, positive


def arm(case: str, cache: bool) -> dict:
    substrate = Substrate()
    native = substrate._inner
    native.set_reachable_cache(cache)
    root = substrate.add_node("N")
    subject = substrate.add_node("N", {"enabled": 0.0})
    middle = substrate.add_node("N")
    new = substrate.add_node("N")
    if case in ("del_node", "replace_value"):
        substrate.add_edge_unchecked(root, "path", middle)
        substrate.add_edge_unchecked(middle, "path", subject)
    else:
        substrate.add_edge_unchecked(root, "path", subject)
    # Prime inputs are stable and their output is idempotent.
    substrate.add_edge_unchecked(root, "probe", subject)
    substrate.add_edge_unchecked(root, "marker", subject)
    prime, mutation, consume, mut_target, positive = rule_specs(case, root, subject, middle, new)
    if case == "add_edge":
        substrate.add_edge_unchecked(root, "mutate", new)
        substrate.add_edge_unchecked(root, "detect", new)
    elif case == "del_node":
        substrate.add_edge_unchecked(root, "mutate", middle)
        substrate.add_edge_unchecked(root, "detect", subject)
    elif case == "replace_value":
        substrate.add_edge_unchecked(root, "mutate", middle)
        substrate.add_edge_unchecked(root, "replacement", new)
        substrate.add_edge_unchecked(root, "detect", subject)
    else:
        substrate.add_edge_unchecked(root, "mutate", subject)
        substrate.add_edge_unchecked(root, "detect", subject)
    if case in ("set_attr", "set_attr_if_different"):
        pass  # enabled starts false; the effect makes the detector true.
    substrate._inner.add_rule(prime)
    prime_steps = int(native.run_rules(100))
    primed_stats = {str(k): int(v) for k, v in dict(native.reachable_cache_stats()).items()}
    native.reachable_cache_stats_reset()
    # Adding rule definitions after priming leaves the live graph memo intact.
    native.add_rule(mutation)
    native.add_rule(consume)
    rule_access = [list(row) for row in native.rule_access_sets()]
    steps = int(native.run_rules(100))
    graph = native.graph_to_dict()
    detected = bool(native.has_edge(root, "detected", mut_target))
    stats = {str(k): int(v) for k, v in dict(native.reachable_cache_stats()).items()}
    try:
        native = None
        substrate = None
    except Exception:
        pass
    return {"cache": cache, "prime_steps": prime_steps, "primed_stats": primed_stats,
        "rule_access_sets": rule_access, "steps": steps, "graph": graph,
        "detected": detected, "expected_detected": True, "positive_query": positive,
        "cache_stats": stats}


def worker(case: str, rep: int) -> dict:
    before = fingerprint()
    order = [False, True] if rep % 2 == 0 else [True, False]
    arms = {str(cache).lower(): arm(case, cache) for cache in order}
    after = fingerprint()
    return {"case": case, "replicate": rep, "pid": os.getpid(),
        "arm_order": [str(cache).lower() for cache in order], "before": before, "after": after, "arms": arms}


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
        "complete_40_worker_matrix": len(rows) == len(CASES) * REPS and all(sum(r["case"] == c for r in rows) == REPS for c in CASES),
        "fresh_workers_and_counterbalanced_order": len({r["pid"] for r in rows}) == 40 and all(r["arm_order"] == (["false", "true"] if r["replicate"] % 2 == 0 else ["true", "false"]) for r in rows),
        "source_lock_and_current_build": initial == final and not initial["native_build_stale"] and all(r["before"] == initial == r["after"] for r in rows),
        "cache_primed_before_effects": all(a["prime_steps"] == 0 and (not a["cache"] or (a["primed_stats"]["entries"] == 1 and a["primed_stats"]["result_values"] == (2 if r["case"] in ("del_node", "replace_value") else 1))) for r in rows for a in r["arms"].values()),
        "expected_detection_in_both_modes": all(a["detected"] and a["expected_detected"] for r in rows for a in r["arms"].values()),
        "cache_on_post_effect_misses": all(a["cache_stats"]["misses"] >= 1 for r in rows for a in r["arms"].values() if a["cache"]),
        "cache_off_stats_zero": all(not any(a["cache_stats"].get(k, 0) for k in ("hits", "misses", "entries", "result_values", "footprint_nodes")) for r in rows for a in r["arms"].values() if not a["cache"]),
        "exact_graph_and_progress_parity": all(r["arms"]["false"]["graph"] == r["arms"]["true"]["graph"] and r["arms"]["false"]["steps"] == r["arms"]["true"]["steps"] for r in rows),
        "query_dependency_visible": all(len(a["rule_access_sets"]) == 3 and "edge:path" in a["rule_access_sets"][2][3] for r in rows for a in r["arms"].values()),
    }
    logref = finish_console_capture(log)
    manifest = capture_run_manifest(run_id=RUN_ID, runner="scripts/substrate_reachable_cache_effect_matrix_v1.py",
        protocol_files=(str(PROTOCOL.relative_to(ROOT)), str(LOCK.relative_to(ROOT))),
        source_files=tuple(p for p in FILES if p.startswith("runners/")),
        analysis_files=("scripts/analyze_substrate_reachable_cache_effect_matrix_v1.py",),
        started_utc=started, exit_status=0 if all(checks.values()) else 1, stdout_stderr_capture=logref)
    raw = {"schema_version": 1, "run_id": RUN_ID, "locked_inputs": initial, "post_run_inputs": final,
        "cases": list(CASES), "checks": checks, "all_checks_pass": all(checks.values()),
        "runs": rows, "run_manifest": manifest,
        "claim_boundary": "Eight same-pass rule-effect freshness cases in a minimal substrate. No timing, natural workload, deferred-effect, or universal dynamic-dependency claim."}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "all_checks_pass": raw["all_checks_pass"], "raw": str(RAW.relative_to(ROOT))}, indent=2))
    return 0 if raw["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
