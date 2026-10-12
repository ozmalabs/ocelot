#!/usr/bin/env python3
"""Paired replay comparing predicate and canonical D4 structure keys."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_POLYOMINO_CONCERN_KEY_IDENTITY_COMPARISON_V1_PREREG_20260929.md"
RUNNER = Path(__file__).resolve()
BASE_RUNNER = ROOT / "evaluation/substrate_capability/polyomino_concern_key_recurrence_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/polyomino_concern_key_identity_comparison_v1_lock_20260929.json"
OUT = ROOT / "evaluation/reports/polyomino_concern_key_identity_comparison_v1"
CAPTURE = OUT / "capture.json"
SPEC = importlib.util.spec_from_file_location("recurrence_case_source", BASE_RUNNER)
CASES = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(CASES)
SOURCES = (
    "domains/reflective_faculty.py", "substrate/boot_core.py",
    "substrate/graph.py", "worlds/arc.py", "seeds/shape_decode_loop.json",
    "runners/dsl/src/shape_decode.rs",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
    "runners/dsl/python/substrate_rs/_native.build.json",
)
VARIANTS = ("predicate", "shape_d4")


def digest(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}


def input_lock() -> dict:
    return {
        "schema_version": 1,
        "protocol": digest(PROTOCOL), "runner": digest(RUNNER),
        "case_source": digest(BASE_RUNNER),
        "sources": [digest(ROOT / src) for src in SOURCES],
        "shapes": {key: [list(point) for point in coords]
                   for key, coords in CASES.SHAPES.items()},
        "sequences": list(CASES.SEQUENCES), "variants": list(VARIANTS),
        "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                    text=True, capture_output=True,
                                    check=True).stdout.strip(),
    }


def atomic(path: Path, value: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")
    tmp.replace(path)


def normalized(points: set[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    mr = min(r for r, _ in points)
    mc = min(c for _, c in points)
    return tuple(sorted((r - mr, c - mc) for r, c in points))


def d4_canonical(signature: list) -> tuple[tuple[int, int], ...]:
    points = {(int(rel[1]), int(rel[2])) for rel in signature}
    forms = (
        points, {(r, -c) for r, c in points}, {(-r, c) for r, c in points},
        {(-r, -c) for r, c in points}, {(c, r) for r, c in points},
        {(c, -r) for r, c in points}, {(-c, r) for r, c in points},
        {(-c, -r) for r, c in points},
    )
    return min(normalized(form) for form in forms)


def count_nodes(sub, kind: str) -> int:
    return len(list(sub.nodes(kind)))


def run_arm(spec: dict, variant: str) -> dict:
    from substrate.boot_core import boot_core
    from domains import reflective_faculty as rf
    from worlds.arc import cells_to_signature

    sub, agent = boot_core()
    native = rf._native_eval2(sub)
    rf._ensure_shape_decode_loop(sub, native, agent)
    base = cells_to_signature([(r, c, CASES.COLOR)
                               for r, c in CASES.SHAPES[spec["first"]]])
    sub.add_node("ShapeSignature", {
        "name": "sequence_base", "signature": json.dumps(base),
        "kind": "faculty", "faculty": "sequence_base",
        "dim_types": ["pred", "coord:r", "coord:c", "val"],
    })
    events = []
    for ordinal, shape_id in enumerate((spec["first"], spec["second"]), 1):
        cells = CASES.make_cells(shape_id)
        signature = cells_to_signature(cells)
        key_start = time.perf_counter()
        if variant == "shape_d4":
            canonical = d4_canonical(signature)
            key_hint = "shape_d4_" + hashlib.sha256(json.dumps(
                canonical, separators=(",", ":")).encode()).hexdigest()
        else:
            predicates = sorted(rel[0] for rel in signature if isinstance(rel, list) and rel)
            key_hint = "induced_" + "_".join(predicates)
        key_compute = time.perf_counter() - key_start

        before_axes = count_nodes(sub, "CapabilityAxis")
        before_epoch = sub.node(agent)["attrs"].get("codebook_epoch")
        started_wall, started_cpu = time.perf_counter(), time.process_time()
        if variant == "shape_d4":
            result = rf.induce_concern(sub, signature, name_hint=key_hint)
        else:
            result = rf.induce_concern(sub, signature)
        wall, cpu = time.perf_counter() - started_wall, time.process_time() - started_cpu
        obs_id = list(sub.nodes("Observation"))[-1]
        obs_attrs = dict(sub.node(obs_id)["attrs"])
        after_axes = count_nodes(sub, "CapabilityAxis")
        after_epoch = sub.node(agent)["attrs"].get("codebook_epoch")
        minted = [dict(sub.node(n)["attrs"]) for n in sub.neighbours(obs_id, "minted")]
        events.append({
            "ordinal": ordinal, "shape_id": shape_id,
            "signature": signature,
            "signature_sha256": hashlib.sha256(json.dumps(
                signature, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "d4_canonical": [list(p) for p in d4_canonical(signature)],
            "effective_key": list(obs_attrs.get("key") or []),
            "returned_capability_key": result.get("capability_key"),
            "status": obs_attrs.get("status"), "result": result,
            "minted_edge_targets": minted,
            "axis_count_before": before_axes, "axis_count_after": after_axes,
            "axis_delta": after_axes - before_axes,
            "codebook_epoch_before": before_epoch,
            "codebook_epoch_after": after_epoch,
            "key_compute_seconds": key_compute,
            "wall_seconds": wall, "cpu_seconds": cpu,
        })
    return {**spec, "variant": variant, "events": events}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or CAPTURE.exists():
            raise SystemExit("refusing to overwrite lock or capture")
        atomic(LOCK, input_lock())
        print(LOCK.relative_to(ROOT))
        return
    locked = json.loads(LOCK.read_text())
    if input_lock() != locked:
        raise SystemExit("source/case lock drift")
    started_wall, started_cpu = time.perf_counter(), time.process_time()
    rows = [run_arm(spec, variant)
            for spec in CASES.SEQUENCES for variant in VARIANTS]
    post = input_lock()
    if post != locked:
        raise SystemExit("post-run source/case lock drift")
    capture = {
        "schema_version": 1,
        "run_id": "polyomino-concern-key-identity-comparison-v1-20260929",
        "status": "complete", "input_lock": locked,
        "post_run_input_lock": post, "arms": rows,
        "process": {"wall_seconds": time.perf_counter() - started_wall,
                    "cpu_seconds": time.process_time() - started_cpu},
    }
    atomic(CAPTURE, capture)
    print(json.dumps({"capture": str(CAPTURE.relative_to(ROOT)),
                      "arms": len(rows),
                      "observations": sum(len(a["events"]) for a in rows),
                      "wall_seconds": capture["process"]["wall_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
