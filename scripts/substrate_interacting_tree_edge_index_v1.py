#!/usr/bin/env python3
"""Replay interacting-tree construction after adaptive high-degree edge indexing."""
from __future__ import annotations

import hashlib
import json
import os
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
from substrate_rs import Substrate, _native  # noqa: E402
from domains.engine_provenance import build_is_stale  # noqa: E402
from substrate_run_manifest import capture_run_manifest, finish_console_capture, start_console_capture  # noqa: E402
from substrate_interacting_tree_closure_scale_v1 import worker as scale_worker  # noqa: E402

PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_INTERACTING_TREE_EDGE_INDEX_V1_PREREG_20260928.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_INTERACTING_TREE_EDGE_INDEX_V1_2_AMENDMENT_20260928.md"
LOCK = ROOT / "evaluation/substrate_capability/interacting_tree_edge_index_v1_2_lock_20260928.json"
RAW = ROOT / "evaluation/reports/substrate_interacting_tree_edge_index_v1_2_20260928.json"
RUN_ID = "substrate-interacting-tree-edge-index-v1-2-20260928"
FILES = (
    "scripts/substrate_interacting_tree_edge_index_v1.py",
    "scripts/analyze_substrate_interacting_tree_edge_index_v1.py",
    "scripts/substrate_interacting_tree_closure_scale_v1.py",
    "scripts/analyze_substrate_interacting_tree_closure_scale_v1.py",
    "scripts/substrate_run_manifest.py",
    "domains/engine_provenance.py",
    "docs/research/engine_substrate/SUBSTRATE_INTERACTING_TREE_EDGE_INDEX_V1_PREREG_20260928.md",
    "docs/research/engine_substrate/SUBSTRATE_INTERACTING_TREE_EDGE_INDEX_V1_1_AMENDMENT_20260928.md",
    "docs/research/engine_substrate/SUBSTRATE_INTERACTING_TREE_EDGE_INDEX_V1_2_AMENDMENT_20260928.md",
    "docs/research/engine_substrate/SUBSTRATE_INTERACTING_TREE_CLOSURE_SCALE_V1_PREREG_20260928.md",
    "docs/research/engine_substrate/SUBSTRATE_INTERACTING_TREE_CLOSURE_SCALE_V1_PILOT_AMENDMENT_20260928.md",
    "runners/dsl/src/graph.rs",
    "runners/dsl/src/py.rs",
    "runners/dsl/src/substrate.rs",
    "runners/dsl/src/rewrite.rs",
    "runners/dsl/src/scale_audit.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/Cargo.toml",
    "runners/dsl/Cargo.lock",
    "runners/dsl/python/substrate_rs/_native.build.json",
)
SIZES = (100_000, 1_000_000)
TOPOLOGIES = ("balanced", "star")
REPLICATES = (0, 1, 2)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint() -> dict:
    native = Path(_native.__file__).resolve()
    return {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "files": {name: sha(ROOT / name) for name in FILES},
        "native_path": str(native),
        "native_sha256": sha(native),
        "native_build_stale": build_is_stale(str(ROOT)),
    }


def worker_fingerprint_matches_lock(worker_fp: dict, locked_fp: dict) -> bool:
    return (
        worker_fp.get("commit") == locked_fp.get("commit")
        and worker_fp.get("native_path") == locked_fp.get("native_path")
        and worker_fp.get("native_sha256") == locked_fp.get("native_sha256")
        and not worker_fp.get("native_build_stale")
        and all(locked_fp.get("files", {}).get(name) == digest
                for name, digest in worker_fp.get("files", {}).items())
    )


def semantic_probe() -> dict:
    native = _native.Substrate()
    source = native.add_node("IndexProbe", {"role": "source"})
    targets = [native.add_node("IndexProbe", {"role": "target", "ordinal": i}) for i in range(20)]
    for i, target in enumerate(targets[:17]):
        native.add_edge_unchecked(source, "hub", target, {"revision": 0} if i == 0 else None)
    count_at_17 = native.edge_count()
    duplicate_found_before = native.has_edge(source, "hub", targets[0])
    native.add_edge_unchecked(source, "hub", targets[0], {"revision": 1})
    duplicate_keeps_count = native.edge_count() == count_at_17
    replaced = next(e for e in native.graph_to_dict()["edges"]
                    if e["src"] == source.value and e["type"] == "hub" and e["tgt"] == targets[0].value)
    replaced_attrs = replaced.get("attrs", {}).get("revision") == 1
    removed = native.remove_edge(source, "hub", targets[1])
    removed_lookup_false = not native.has_edge(source, "hub", targets[1])
    for target in targets[2:4]:
        native.remove_edge(source, "hub", target)
    demoted_count = native.edge_count() == 14
    lookups_after_demotion = all(native.has_edge(source, "hub", target) for target in [targets[0], *targets[4:17]])
    native.add_edge_unchecked(source, "hub", targets[17])
    native.add_edge_unchecked(source, "hub", targets[18])
    reinsertion_count = native.edge_count() == 16
    recreated_index_lookup = native.has_edge(source, "hub", targets[18])
    sparse = native.add_node("IndexProbe", {"role": "sparse"})
    sparse_target = targets[19]
    native.add_edge_unchecked(sparse, "one", sparse_target)
    sparse_lookup = native.has_edge(sparse, "one", sparse_target)
    return {
        "count_at_17": count_at_17,
        "duplicate_found_before": duplicate_found_before,
        "duplicate_keeps_count": duplicate_keeps_count,
        "replacement_attrs_correct": replaced_attrs,
        "deletion_succeeded": removed,
        "removed_lookup_false": removed_lookup_false,
        "demotion_count_correct": demoted_count,
        "lookups_after_demotion": lookups_after_demotion,
        "reinsertion_count_correct": reinsertion_count,
        "recreated_index_lookup": recreated_index_lookup,
        "sparse_lookup": sparse_lookup,
        "final_edge_count": native.edge_count(),
    }


def main() -> int:
    if sys.argv[1:] == ["--lock"]:
        fp = fingerprint()
        if fp["native_build_stale"]:
            raise SystemExit("native build is stale; run scripts/engine_build.sh")
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps(fp, indent=2, sort_keys=True) + "\n")
        print(LOCK)
        return 0
    if len(sys.argv) == 5 and sys.argv[1] == "--worker":
        n, topology, replicate = int(sys.argv[2]), sys.argv[3], int(sys.argv[4])
        print(json.dumps(scale_worker(n, topology, replicate, False), sort_keys=True))
        return 0
    before = fingerprint()
    if before["native_build_stale"] or not LOCK.exists() or json.loads(LOCK.read_text()) != before:
        raise SystemExit("missing/stale lock or native build")
    log = start_console_capture(RUN_ID)
    started = datetime.now(timezone.utc).isoformat()
    semantic = semantic_probe()
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join((str(ROOT), str(ROOT / "runners/dsl/python"), env.get("PYTHONPATH", "")))
    jobs = [(n, topo, rep) for n in SIZES for topo in TOPOLOGIES for rep in REPLICATES]
    random.Random(20260928).shuffle(jobs)
    runs = []
    for n, topo, rep in jobs:
        cp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(n), topo, str(rep)],
                            cwd=ROOT, env=env, text=True, capture_output=True, check=True)
        row = json.loads(cp.stdout)
        row["worker_returncode"] = cp.returncode
        row["worker_stderr"] = cp.stderr
        runs.append(row)
    after = fingerprint()
    semantic_expected = all(v is True for k, v in semantic.items() if isinstance(v, bool))
    checks = {
        "semantic_index_transition_and_mutation_controls": semantic_expected,
        "twelve_workers": len(runs) == 12,
        "three_replicates_per_size_topology": all(sum(r["n"] == n and r["topology"] == t for r in runs) == 3
                                                   for n in SIZES for t in TOPOLOGIES),
        "unique_worker_pids": len({r["pid"] for r in runs}) == len(runs),
        "stable_locked_source": before == after and all(
            r["before"] == r["after"] and worker_fingerprint_matches_lock(r["before"], before)
            for r in runs),
        "exact_terminal_oracle": all(r["report"]["status"] == "fixed_point" and r["report"]["budget_overshoot"] == 0
                                     and r["pending_count"] == r["ready_count"] == 0 and r["active_count"] == r["n"]
                                     for r in runs),
        "exact_graph_and_sample_oracle": all(r["nodes"] == r["n"] and r["edges"] == 2 * (r["n"] - 1)
                                              and len(r["samples"]) == 3 for r in runs),
    }
    manifest_log = finish_console_capture(log)
    manifest = capture_run_manifest(
        run_id=RUN_ID, runner="scripts/substrate_interacting_tree_edge_index_v1.py",
        protocol_files=(str(PROTOCOL.relative_to(ROOT)), str(AMENDMENT.relative_to(ROOT)),
                        str(LOCK.relative_to(ROOT))),
        source_files=tuple(p for p in FILES if p.startswith("runners/")) +
                     ("scripts/substrate_interacting_tree_closure_scale_v1.py", "scripts/substrate_run_manifest.py"),
        analysis_files=("scripts/analyze_substrate_interacting_tree_edge_index_v1.py",),
        started_utc=started, exit_status=0 if all(checks.values()) else 1,
        stdout_stderr_capture=manifest_log,
    )
    result = {
        "schema_version": 1, "run_id": RUN_ID, "started_utc": started,
        "locked_inputs": before, "post_run_inputs": after, "semantic_probe": semantic,
        "schedule": jobs, "checks": checks, "all_checks_pass": all(checks.values()),
        "runs": runs, "run_manifest": manifest,
        "claim_boundary": "One adaptive index implementation replayed on the prior two tree shapes; three replicates per cell; no general complexity theorem.",
    }
    RAW.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"workers": len(runs), "checks": checks, "all_checks_pass": result["all_checks_pass"],
                      "raw": str(RAW.relative_to(ROOT))}, indent=2, sort_keys=True))
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
