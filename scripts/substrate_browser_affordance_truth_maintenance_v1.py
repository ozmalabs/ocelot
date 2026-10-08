#!/usr/bin/env python3
"""Truth-maintenance replay for the authored BrowserWorld affordance mirror."""
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

PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_BROWSER_AFFORDANCE_TRUTH_MAINTENANCE_V1_PREREG_20260928.md"
LOCK = ROOT / "evaluation/substrate_capability/browser_affordance_truth_maintenance_v1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/browser_affordance_truth_maintenance_v1_20260928.json"
RUN_ID = "browser-affordance-truth-maintenance-v1-20260928"
REPS = 5
FILES = (
    "scripts/substrate_browser_affordance_truth_maintenance_v1.py",
    "scripts/analyze_substrate_browser_affordance_truth_maintenance_v1.py",
    "scripts/substrate_run_manifest.py", "domains/engine_provenance.py",
    "substrate/world_adapter.py", "substrate/boot_core.py", "substrate/seed_loader.py",
    "seeds/browser_affordance_reach.json", "runners/dsl/src/term.rs",
    "runners/dsl/src/substrate.rs", "runners/dsl/src/rewrite.rs", "runners/dsl/src/py.rs",
    "runners/dsl/src/graph.rs", "runners/dsl/python/substrate_rs/_native.build.json",
    "runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock", str(PROTOCOL.relative_to(ROOT)),
)
CHECKPOINTS = ("initial", "session_detached", "session_restored", "presence_disabled",
               "presence_restored", "leaf_detached", "leaf_restored")
EXPECTED = {"initial": 2, "session_detached": 0, "session_restored": 2,
            "presence_disabled": 1, "presence_restored": 2,
            "leaf_detached": 1, "leaf_restored": 2}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint() -> dict:
    native = Path(_native.__file__).resolve()
    return {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "files": {p: sha(ROOT / p) for p in FILES}, "native_path": str(native),
        "native_sha256": sha(native), "native_build_stale": build_is_stale(str(ROOT))}


def run_one(cache: bool) -> dict:
    world = WorldAdapter(seeds=("browser_affordance_reach",), shadow_read=False, deep_ingest=False)
    inner = world.inner
    inner.set_reachable_cache(cache)
    session = world.s.add_node("WorldInstance", {"world_type": "Session", "id": "session"})
    parent = world.s.add_node("WorldInstance", {"world_type": "Element", "id": "parent", "present": 1.0})
    leaves, affordances = [], []
    for i in range(2):
        leaf = world.s.add_node("WorldInstance", {"world_type": "Element", "id": f"leaf-{i}",
            "present": 1.0, "tag": "a", "text": f"link {i}"})
        aff = world.s.add_node("Affordance", {"world_id": f"aff-{i}", "kind": "navigate"})
        inner.add_edge_unchecked(leaf, "affords", aff, {})
        leaves.append(leaf)
        affordances.append(aff)
    inner.add_edge_unchecked(session, "contains", parent, {})
    for leaf in leaves:
        inner.add_edge_unchecked(parent, "contains", leaf, {})

    def settle(label: str) -> dict:
        steps = int(inner.run_rules(100_000))
        mirror = sum(bool(inner.has_edge(session, "has_affordance", aff)) for aff in affordances)
        return {"label": label, "steps": steps, "mirror_count": mirror,
            "graph": inner.graph_to_dict(),
            "cache_stats": {str(k): int(v) for k, v in dict(inner.reachable_cache_stats()).items()}}

    loaded_rules = sorted(row[1] for row in inner.rule_access_sets())
    rows = [settle("initial")]
    world.s.remove_edge(session, "contains", parent)
    rows.append(settle("session_detached"))
    inner.add_edge_unchecked(session, "contains", parent, {})
    rows.append(settle("session_restored"))
    world.s.set_attr(leaves[0], "present", 0.0)
    rows.append(settle("presence_disabled"))
    world.s.set_attr(leaves[0], "present", 1.0)
    rows.append(settle("presence_restored"))
    world.s.remove_edge(parent, "contains", leaves[0])
    rows.append(settle("leaf_detached"))
    inner.add_edge_unchecked(parent, "contains", leaves[0], {})
    rows.append(settle("leaf_restored"))
    try:
        world.close()
    except Exception:
        pass
    return {"cache": cache, "loaded_rule_names": loaded_rules, "checkpoints": rows}


def worker(rep: int) -> dict:
    before = fingerprint()
    order = [False, True] if rep % 2 == 0 else [True, False]
    arms = {str(cache).lower(): run_one(cache) for cache in order}
    after = fingerprint()
    return {"replicate": rep, "pid": os.getpid(), "arm_order": [str(c).lower() for c in order],
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
            cp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(rep),
                ], cwd=ROOT, env=env, text=True, capture_output=True, check=True)
            rows.append(json.loads(cp.stdout))
    except Exception:
        finish_console_capture(log)
        raise
    final = fingerprint()
    checks = {
        "five_fresh_counterbalanced_workers": len(rows) == 5 and len({r["pid"] for r in rows}) == 5 and all(r["arm_order"] == (["false", "true"] if r["replicate"] % 2 == 0 else ["true", "false"]) for r in rows),
        "stable_locked_sources_and_build": initial == final and not initial["native_build_stale"] and all(r["before"] == initial == r["after"] for r in rows),
        "expected_authored_rules_loaded": all(set(a["loaded_rule_names"]) == {"browser_mirror_has_affordance_reachable", "browser_drop_has_affordance_stale"} for r in rows for a in r["arms"].values()),
        "all_seven_checkpoint_mirror_counts": all([c["mirror_count"] for c in a["checkpoints"]] == [EXPECTED[k] for k in CHECKPOINTS] for r in rows for a in r["arms"].values()),
        "cache_modes_match_at_every_checkpoint": all(all(a["checkpoints"][i]["graph"] == b["checkpoints"][i]["graph"] and a["checkpoints"][i]["steps"] == b["checkpoints"][i]["steps"] and a["checkpoints"][i]["mirror_count"] == b["checkpoints"][i]["mirror_count"] for i in range(len(CHECKPOINTS)) for a,b in [(r["arms"]["false"],r["arms"]["true"])]) for r in rows),
        "cache_is_active_in_enabled_arms": all(any(c["cache_stats"].get("hits",0) or c["cache_stats"].get("misses",0) for c in r["arms"]["true"]["checkpoints"]) for r in rows),
        "disabled_cache_counters_zero": all(not any(c["cache_stats"].get(k,0) for k in ("hits","misses","entries","result_values")) for r in rows for c in r["arms"]["false"]["checkpoints"]),
    }
    logref = finish_console_capture(log)
    manifest = capture_run_manifest(run_id=RUN_ID, runner="scripts/substrate_browser_affordance_truth_maintenance_v1.py",
        protocol_files=(str(PROTOCOL.relative_to(ROOT)), str(LOCK.relative_to(ROOT))),
        source_files=tuple(p for p in FILES if p.startswith(("runners/", "substrate/", "seeds/"))),
        analysis_files=("scripts/analyze_substrate_browser_affordance_truth_maintenance_v1.py",),
        started_utc=started, exit_status=0 if all(checks.values()) else 1, stdout_stderr_capture=logref)
    raw = {"schema_version": 1, "run_id": RUN_ID, "locked_inputs": initial, "post_run_inputs": final,
        "checkpoints": list(CHECKPOINTS), "expected_mirror_counts": EXPECTED,
        "checks": checks, "all_checks_pass": all(checks.values()), "runs": rows, "run_manifest": manifest,
        "claim_boundary": "Selected public topology and presence changes for the authored browser affordance mirror seed. No broad rule-family or natural browser workload claim."}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "all_checks_pass": raw["all_checks_pass"], "raw": str(RAW.relative_to(ROOT))}, indent=2))
    return 0 if raw["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
