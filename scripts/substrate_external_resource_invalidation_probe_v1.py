#!/usr/bin/env python3
"""Fresh-process probe for resource-only invalidation of UseTool predicates."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_EXTERNAL_RESOURCE_INVALIDATION_PROBE_V1_PREREG_20260928.md"
ANALYZER = ROOT / "scripts/analyze_external_resource_invalidation_probe_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/external_resource_invalidation_probe_v1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/external_resource_invalidation_probe_v1_20260928.json"
SOURCE_PATHS = (
    "runners/dsl/src/term.rs", "runners/dsl/src/rewrite.rs", "runners/dsl/src/py.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "scripts/substrate_external_resource_invalidation_probe_v1.py",
    "scripts/analyze_external_resource_invalidation_probe_v1.py",
    "docs/research/engine_substrate/SUBSTRATE_EXTERNAL_RESOURCE_INVALIDATION_PROBE_V1_PREREG_20260928.md",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lock_inputs() -> dict:
    from substrate_rs import _native
    ext = Path(_native.__file__).resolve()
    return {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_sha256": {name: sha(ROOT / name) for name in SOURCE_PATHS},
        "native_extension_path": str(ext), "native_extension_sha256": sha(ext),
        "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
    }


def accepted_targets(graph: dict, target_ids: list[int]) -> list[bool]:
    attrs = {int(n["id"]): n.get("attrs", {}) for n in graph.get("nodes", [])}
    return [attrs.get(i, {}).get("accepted") == 1 for i in target_ids]


def worker(worker_id: int) -> dict:
    from substrate_rs import Lit, Substrate, Term, _native
    started_inputs = lock_inputs()
    if json.loads(LOCK.read_text())["locked_inputs"] != started_inputs:
        raise RuntimeError("source/native inputs differ from locked inputs")
    _native.clear_tool_handlers()
    callbacks: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="substrate-resource-invalidation-") as td:
        resource = Path(td) / "resource.txt"

        def handler(_arg):
            value = resource.read_text(encoding="utf-8")
            callbacks.append({"value": value})
            return value

        _native.register_tool_handler("resource_value", handler)
        sub = Substrate()
        inner = sub._inner
        x1, y1 = inner.add_node("ResourceProbe", {}), inner.add_node("ResourceProbe", {})
        inner.add_edge_unchecked(x1, "trigger", y1, {})
        pred = Term("Eq", a=Term("UseTool", tool="resource_value", args=[Lit("resource")]), b=Lit("1"))
        rule_idx = inner.add_rule({
            "name": "external_resource_guard", "match": [["x", "trigger", "y"]],
            "where": pred.to_dict(), "effects": [["set_attr", "y", "accepted", 1]],
        })
        access = inner.rule_access_sets()[rule_idx]
        phases = []

        def settle(label: str, content: str, mutate=None):
            resource.write_text(content, encoding="utf-8")
            resource_hash = sha(resource)
            if mutate:
                mutate()
            callbacks.clear()
            before = int(_native.tool_fire_count())
            progress = int(inner.run_rules(100))
            after = int(_native.tool_fire_count())
            graph = inner.graph_to_dict()
            ids = [y1]
            if "y2" in locals():
                ids.append(y2)
            phases.append({
                "phase": label, "resource_value": content, "resource_sha256": resource_hash,
                "progress": progress, "callback_log": list(callbacks),
                "callback_count": len(callbacks), "native_fire_delta": after - before,
                "accepted_targets": accepted_targets(graph, target_ids), "graph": graph,
            })

        target_ids = [y1]
        settle("A_false_initial", "0")
        settle("B_resource_only_flip_true", "1")

        def add_second_match():
            nonlocal y2
            x2 = inner.add_node("ResourceProbe", {})
            y2 = inner.add_node("ResourceProbe", {})
            inner.add_edge_unchecked(x2, "trigger", y2, {})
            target_ids.append(y2)
        y2 = None
        settle("C_resource_false_plus_new_graph_match", "0", add_second_match)
        _native.clear_tool_handlers()
        return {
            "worker_id": worker_id, "pid": os.getpid(), "python": sys.version,
            "platform": platform.platform(), "started_inputs": started_inputs,
            "static_access": {"reads": sorted(map(str, access[3])), "reads_any": bool(access[6])},
            "phases": phases,
        }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", type=int)
    ap.add_argument("--write-lock", action="store_true")
    args = ap.parse_args()
    if args.write_lock:
        if LOCK.exists():
            raise SystemExit(f"refusing to overwrite lock {LOCK}")
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps({"lock_id": "external_resource_invalidation_probe_v1_20260928", "locked_inputs": lock_inputs()}, indent=2, sort_keys=True) + "\n")
        print(str(LOCK.relative_to(ROOT)))
        return
    if args.worker is not None:
        print(json.dumps(worker(args.worker), sort_keys=True))
        return
    if RAW.exists():
        raise SystemExit(f"refusing to overwrite raw capture {RAW}")
    lock = json.loads(LOCK.read_text())
    if lock_inputs() != lock["locked_inputs"]:
        raise SystemExit("source/native inputs differ from lock")
    runs = []
    for worker_id in range(1, 4):
        argv = [sys.executable, str(Path(__file__).resolve()), "--worker", str(worker_id)]
        proc = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True)
        if proc.returncode:
            raise SystemExit(f"worker {worker_id} failed: {proc.stderr[-2000:]}")
        runs.append(json.loads(proc.stdout.strip().splitlines()[-1]))
    report = {
        "run_id": "external_resource_invalidation_probe_v1_20260928",
        "protocol_sha256": sha(PROTOCOL), "analyzer_sha256": sha(ANALYZER),
        "lock_sha256": sha(LOCK), "locked_inputs": lock["locked_inputs"], "runs": runs,
        "claim_boundary": "Three fresh synthetic file-backed UseTool predicate workers. Measures whether a mutable callback resource change alone or with a new graph match causes predicate invocations and effects. Does not establish behavior for all host reads, Term variants, or real production resource watchers.",
    }
    RAW.parent.mkdir(parents=True, exist_ok=True)
    with RAW.open("x", encoding="utf-8") as f:
        f.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"workers": len(runs), "phases_per_worker": len(runs[0]["phases"]), "raw": str(RAW.relative_to(ROOT))}))


if __name__ == "__main__":
    main()
