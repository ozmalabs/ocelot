#!/usr/bin/env python3
"""Locked semantic probe for mixed-topology public remove_node."""
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
from substrate_rs import _native  # noqa: E402
from domains.engine_provenance import build_is_stale  # noqa: E402
from substrate_run_manifest import capture_run_manifest, finish_console_capture, start_console_capture  # noqa: E402

PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_MIXED_NODE_DELETE_SEMANTICS_V1_PREREG_20260928.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_MIXED_NODE_DELETE_SEMANTICS_V1_1_AMENDMENT_20260928.md"
LOCK = ROOT / "evaluation/substrate_capability/mixed_node_delete_semantics_v1_1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/substrate_mixed_node_delete_semantics_v1_1_20260928.json"
RUN_ID = "substrate-mixed-node-delete-semantics-v1-1-20260928"
FILES = (
    "scripts/substrate_mixed_node_delete_semantics_v1.py",
    "scripts/analyze_substrate_mixed_node_delete_semantics_v1.py",
    "scripts/substrate_run_manifest.py",
    "domains/engine_provenance.py",
    "docs/research/engine_substrate/SUBSTRATE_MIXED_NODE_DELETE_SEMANTICS_V1_PREREG_20260928.md",
    "docs/research/engine_substrate/SUBSTRATE_MIXED_NODE_DELETE_SEMANTICS_V1_1_AMENDMENT_20260928.md",
    "runners/dsl/src/graph.rs",
    "runners/dsl/src/substrate.rs",
    "runners/dsl/src/py.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
    "runners/dsl/Cargo.toml",
    "runners/dsl/Cargo.lock",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint() -> dict:
    native = Path(_native.__file__).resolve()
    return {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "files": {p: sha(ROOT / p) for p in FILES}, "native_path": str(native),
            "native_sha256": sha(native), "native_build_stale": build_is_stale(str(ROOT))}


def worker(rep: int) -> dict:
    before = fingerprint()
    s = _native.Substrate()
    node_events, edge_events = [], []
    s.register_hook("node_deleted", lambda nid, ty: node_events.append([nid.value, ty]))
    s.register_hook("edge_deleted", lambda src, et, tgt: edge_events.append([src.value, et, tgt.value]))
    outside_a = s.add_node("Outside", {"keep": "a"})
    doomed = s.add_node("Doomed", {"payload": 7})
    outside_b = s.add_node("Outside", {"keep": "b"})
    outside_c = s.add_node("Outside", {"keep": "c"})
    specs = [
        (outside_a, "incoming_alpha", doomed, {"weight": 11}),
        (outside_b, "incoming_beta", doomed, {"weight": 12}),
        (doomed, "outgoing_alpha", outside_a, {"weight": 21}),
        (doomed, "outgoing_beta", outside_b, {"weight": 22}),
        (doomed, "outgoing_alpha", outside_c, {"weight": 23}),
        (doomed, "self_loop", doomed, {"weight": 31}),
        (outside_a, "unrelated", outside_c, {"weight": 99}),
    ]
    for src, et, tgt, attrs in specs:
        s.add_edge_unchecked(src, et, tgt, attrs)
    before_graph = s.graph_to_dict()
    removed = s.remove_node(doomed)
    after_graph = s.graph_to_dict()
    lookups = [s.has_edge(src, et, tgt) for src, et, tgt, _ in specs]
    after = fingerprint()
    return {"replicate": rep, "pid": os.getpid(), "before": before, "after": after,
            "ids": {"doomed": doomed.value, "type": "Doomed"}, "specs": [[a.value, b, c.value, d] for a,b,c,d in specs],
            "before_graph": before_graph, "after_graph": after_graph, "lookups": lookups,
            "removed": removed, "node_count": s.node_count(), "edge_count": s.edge_count(),
            "node_events": node_events, "edge_events": edge_events}


def expected_after(row: dict) -> dict:
    dead = row["ids"]["doomed"]
    graph = row["before_graph"]
    nodes = [n for n in graph["nodes"] if n["id"] != dead]
    edges = [e for e in graph["edges"] if e["src"] != dead and e["tgt"] != dead]
    return {**graph, "nodes": nodes, "edges": edges}


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
    before = fingerprint()
    if before["native_build_stale"] or not LOCK.exists() or json.loads(LOCK.read_text()) != before:
        raise SystemExit("missing/stale source lock or native build")
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join((str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts"), env.get("PYTHONPATH", "")))
    started = datetime.now(timezone.utc).isoformat()
    log = start_console_capture(RUN_ID)
    rows = []
    for rep in range(3):
        cp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(rep)], cwd=ROOT,
                            env=env, text=True, capture_output=True, check=True)
        rows.append(json.loads(cp.stdout))
    after = fingerprint()
    checks = {
        "three_fresh_workers": len(rows) == 3 and len({r["pid"] for r in rows}) == 3,
        "source_lock_stable": before == after and all(r["before"] == before == r["after"] for r in rows),
        "native_build_fresh": not before["native_build_stale"],
        "exact_expected_post_state": all(r["after_graph"] == expected_after(r) for r in rows),
        "counts_and_edge_lookups": all(r["removed"] and r["node_count"] == 3 and r["edge_count"] == 1
            and r["lookups"] == [False, False, False, False, False, False, True] for r in rows),
        "node_hook_only_contract": all(r["node_events"] == [[r["ids"]["doomed"], "Doomed"]]
            and r["edge_events"] == [] for r in rows),
        "fixture_has_mixed_topology": all(len(r["specs"]) == 7 and sum(1 for x in r["specs"] if x[0] == x[2]) == 1
            and len({x[1] for x in r["specs"]}) == 6 for r in rows),
    }
    log_ref = finish_console_capture(log)
    manifest = capture_run_manifest(run_id=RUN_ID, runner="scripts/substrate_mixed_node_delete_semantics_v1.py",
        protocol_files=(str(PROTOCOL.relative_to(ROOT)), str(AMENDMENT.relative_to(ROOT)), str(LOCK.relative_to(ROOT))),
        source_files=tuple(p for p in FILES if p.startswith("runners/")) + ("scripts/substrate_run_manifest.py", "domains/engine_provenance.py"),
        analysis_files=("scripts/analyze_substrate_mixed_node_delete_semantics_v1.py",), started_utc=started,
        exit_status=0 if all(checks.values()) else 1, stdout_stderr_capture=log_ref)
    raw = {"schema_version": 1, "run_id": RUN_ID, "locked_inputs": before, "post_run_inputs": after,
           "checks": checks, "all_checks_pass": all(checks.values()), "runs": rows, "run_manifest": manifest,
           "claim_boundary": "Mixed-topology public remove_node semantics on one deterministic attributed fixture; no timing or active-rule invalidation claim."}
    RAW.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "all_checks_pass": raw["all_checks_pass"], "raw": str(RAW.relative_to(ROOT))}, indent=2))
    return 0 if raw["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
