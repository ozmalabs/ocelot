#!/usr/bin/env python3
"""Source-locked 10M balanced-tree closure control for the edge-index work."""
from __future__ import annotations

import json
import hashlib
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts")]
from substrate_rs import _native  # noqa: E402
from domains.engine_provenance import build_is_stale  # noqa: E402
from substrate_run_manifest import capture_run_manifest, finish_console_capture, start_console_capture  # noqa: E402
from substrate_interacting_tree_closure_scale_v1 import worker as scale_worker  # noqa: E402
from substrate_interacting_tree_edge_index_v1 import semantic_probe  # noqa: E402
from substrate_interacting_tree_edge_index_scale_v1_3 import worker_projection_matches  # noqa: E402

PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_INTERACTING_TREE_EDGE_INDEX_V1_4_BALANCED_SCALE_PREREG_20260928.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_INTERACTING_TREE_EDGE_INDEX_V1_4_1_AMENDMENT_20260928.md"
LOCK = ROOT / "evaluation/substrate_capability/interacting_tree_edge_index_v1_4_1_balanced_lock_20260928.json"
RAW = ROOT / "evaluation/reports/substrate_interacting_tree_edge_index_v1_4_1_balanced_20260928.json"
RUN_ID = "substrate-interacting-tree-edge-index-v1-4-1-balanced-scale-20260928"
FILES = (
    "scripts/substrate_interacting_tree_edge_index_scale_v1_4_balanced.py",
    "scripts/analyze_substrate_interacting_tree_edge_index_v1_4_balanced.py",
    "scripts/substrate_interacting_tree_edge_index_scale_v1_3.py",
    "scripts/substrate_interacting_tree_edge_index_v1.py",
    "scripts/substrate_interacting_tree_closure_scale_v1.py",
    "scripts/analyze_substrate_interacting_tree_closure_scale_v1.py",
    "scripts/substrate_run_manifest.py",
    "domains/engine_provenance.py",
    "docs/research/engine_substrate/SUBSTRATE_INTERACTING_TREE_CLOSURE_SCALE_V1_PREREG_20260928.md",
    "docs/research/engine_substrate/SUBSTRATE_INTERACTING_TREE_CLOSURE_SCALE_V1_PILOT_AMENDMENT_20260928.md",
    "docs/research/engine_substrate/SUBSTRATE_INTERACTING_TREE_EDGE_INDEX_V1_PREREG_20260928.md",
    "docs/research/engine_substrate/SUBSTRATE_INTERACTING_TREE_EDGE_INDEX_V1_1_AMENDMENT_20260928.md",
    "docs/research/engine_substrate/SUBSTRATE_INTERACTING_TREE_EDGE_INDEX_V1_2_AMENDMENT_20260928.md",
    "docs/research/engine_substrate/SUBSTRATE_INTERACTING_TREE_EDGE_INDEX_V1_3_SCALE_PREREG_20260928.md",
    "docs/research/engine_substrate/SUBSTRATE_INTERACTING_TREE_EDGE_INDEX_V1_4_BALANCED_SCALE_PREREG_20260928.md",
    "docs/research/engine_substrate/SUBSTRATE_INTERACTING_TREE_EDGE_INDEX_V1_4_1_AMENDMENT_20260928.md",
    "evaluation/reports/substrate_interacting_tree_edge_index_v1_2_20260928.json",
    "evaluation/reports/substrate_interacting_tree_edge_index_v1_2_analysis_20260928.json",
    "evaluation/substrate_capability/interacting_tree_edge_index_v1_2_lock_20260928.json",
    "runners/dsl/src/graph.rs",
    "runners/dsl/src/py.rs",
    "runners/dsl/src/substrate.rs",
    "runners/dsl/src/rewrite.rs",
    "runners/dsl/src/scale_audit.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
    "runners/dsl/Cargo.toml",
    "runners/dsl/Cargo.lock",
)


def fingerprint(root: Path, files: tuple[str, ...]) -> dict:
    native = Path(_native.__file__).resolve()
    return {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "files": {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in files},
        "native_path": str(native),
        "native_sha256": hashlib.sha256(native.read_bytes()).hexdigest(),
        "native_build_stale": build_is_stale(str(root)),
    }


def main() -> int:
    if sys.argv[1:] == ["--lock"]:
        fp = fingerprint(ROOT, FILES)
        if fp["native_build_stale"]:
            raise SystemExit("native build is stale")
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps(fp, indent=2, sort_keys=True) + "\n")
        print(LOCK)
        return 0
    if sys.argv[1:] == ["--worker"]:
        print(json.dumps(scale_worker(10_000_000, "balanced", int(os.environ.get("EDGE_INDEX_REP", "0")), False),
                         sort_keys=True))
        return 0
    before = fingerprint(ROOT, FILES)
    if before["native_build_stale"] or not LOCK.exists() or json.loads(LOCK.read_text()) != before:
        raise SystemExit("missing/stale source lock or native build")
    log = start_console_capture(RUN_ID)
    started = datetime.now(timezone.utc).isoformat()
    semantics = semantic_probe()
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join((str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts"), env.get("PYTHONPATH", "")))
    rows = []
    for replicate in range(3):
        child_env = dict(env)
        child_env["EDGE_INDEX_REP"] = str(replicate)
        cp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker"], cwd=ROOT,
                            env=child_env, text=True, capture_output=True, check=True)
        row = json.loads(cp.stdout)
        row["worker_returncode"] = cp.returncode
        row["worker_stderr"] = cp.stderr
        rows.append(row)
    after = fingerprint(ROOT, FILES)
    checks = {
        "index_semantics_pass": all(v is True for v in semantics.values() if isinstance(v, bool)),
        "three_fresh_workers": len(rows) == 3 and len({r["pid"] for r in rows}) == 3,
        "parent_source_lock_stable": before == after,
        "worker_source_locks_match_parent": all(r["before"] == r["after"]
                                                  and worker_projection_matches(r["before"], before)
                                                  for r in rows),
        "exact_graph_counts": all(r["nodes"] == 10_000_000 and r["edges"] == 19_999_998 for r in rows),
        "exact_terminal_oracle": all(r["report"]["status"] == "fixed_point"
                                     and r["report"]["budget_overshoot"] == 0
                                     and r["pending_count"] == r["ready_count"] == 0
                                     and r["active_count"] == 10_000_000 for r in rows),
        "sampled_attrs_and_parents": all(len(r["samples"]) == 3 and all(
            s["status"] == "active" and s["ordinal"] == s["id"]
            and s["bucket"] == s["expected_bucket"] and s["depth"] == s["expected_depth"]
            and s["parents"] == s["expected_parents"] for s in r["samples"]) for r in rows),
        "positive_phase_timings": all(all(r[k] > 0 for k in (
            "node_build_wall_ns", "edge_build_wall_ns", "closure_wall_ns", "validation_wall_ns")) for r in rows),
    }
    log_ref = finish_console_capture(log)
    manifest = capture_run_manifest(
        run_id=RUN_ID, runner="scripts/substrate_interacting_tree_edge_index_scale_v1_4_balanced.py",
        protocol_files=(str(PROTOCOL.relative_to(ROOT)), str(AMENDMENT.relative_to(ROOT)),
                        str(LOCK.relative_to(ROOT))),
        source_files=tuple(p for p in FILES if p.startswith("runners/")) +
                     ("scripts/substrate_interacting_tree_closure_scale_v1.py", "scripts/substrate_run_manifest.py"),
        analysis_files=("scripts/analyze_substrate_interacting_tree_edge_index_v1_4_balanced.py",),
        started_utc=started, exit_status=0 if all(checks.values()) else 1,
        stdout_stderr_capture=log_ref,
    )
    result = {"schema_version": 1, "run_id": RUN_ID, "started_utc": started,
              "locked_inputs": before, "post_run_inputs": after, "semantic_probe": semantics,
              "checks": checks, "all_checks_pass": all(checks.values()), "runs": rows,
              "run_manifest": manifest,
              "claim_boundary": "Three-worker exact 10M balanced-tree construction and two-rule closure on one host; no general closure scaling claim."}
    RAW.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"worker_count": len(rows), "checks": checks, "all_checks_pass": result["all_checks_pass"],
                      "raw": str(RAW.relative_to(ROOT))}, indent=2, sort_keys=True))
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
