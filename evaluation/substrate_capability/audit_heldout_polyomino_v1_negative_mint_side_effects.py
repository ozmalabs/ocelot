#!/usr/bin/env python3
"""Measure graph mutations for distinct saved added-cell controls."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_HELDOUT_POLYOMINO_V1_NEGATIVE_MINT_SIDE_EFFECT_AUDIT_20260929.md"
RUNNER = Path(__file__).resolve()
RAW = ROOT / "evaluation/reports/heldout_polyomino_transform_transfer_v1/capture.json"
LOCK = ROOT / "evaluation/substrate_capability/heldout_polyomino_v1_negative_mint_side_effects_lock_20260929.json"
OUT = ROOT / "evaluation/reports/heldout_polyomino_transform_transfer_v1_graph_replay/negative_mint_side_effects.json"
SOURCES = (
    "worlds/arc_ls20_scenario.py",
    "worlds/arc.py",
    "substrate/boot_core.py",
    "substrate/graph.py",
    "domains/reflective_faculty.py",
    "seeds/shape_decode_loop.json",
    "runners/dsl/src/shape_decode.rs",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
    "runners/dsl/python/substrate_rs/_native.build.json",
)


def digest(path: Path) -> dict:
    data = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def input_lock() -> dict:
    return {
        "schema_version": 1,
        "protocol": digest(PROTOCOL), "runner": digest(RUNNER),
        "raw_capture": digest(RAW),
        "sources": [digest(ROOT / path) for path in SOURCES],
        "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                    text=True, capture_output=True,
                                    check=True).stdout.strip(),
    }


def atomic(path: Path, value: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")
    tmp.replace(path)


def node_counts(graph) -> dict:
    return {kind: len(list(graph.nodes(kind)))
            for kind in ("Agent", "ShapeSignature", "CapabilityAxis",
                         "Observation", "LatentDimension")}


def replay(base_sig: list, goal_sig: list) -> dict:
    from substrate.boot_core import boot_core
    from domains import reflective_faculty as rf
    from worlds.arc_ls20_scenario import DT

    graph, agent = boot_core()
    native = rf._native_eval2(graph)
    rf._ensure_shape_decode_loop(graph, native, agent)
    before_counts = node_counts(graph)
    before_epoch = graph.node(agent)["attrs"].get("codebook_epoch")
    graph.add_node("ShapeSignature", {
        "name": "sym", "signature": json.dumps(base_sig),
        "kind": "faculty", "faculty": "sym", "dim_types": DT,
    })
    observation = graph.add_node("Observation", {
        "signature": goal_sig, "key": ["negative_mint_audit"],
        "status": "decoded", "residual": goal_sig,
        "decoded_epoch": before_epoch or 0.0, "dim_types": DT,
    })
    graph.add_edge(agent, "observed", observation)
    native.run_rules()
    after_counts = node_counts(graph)
    after_epoch = graph.node(agent)["attrs"].get("codebook_epoch")
    minted = [dict(graph.node(n)["attrs"])
              for n in graph.neighbours(observation, "minted")]
    transforms = [dict(graph.node(n)["attrs"])
                 for n in graph.neighbours(observation, "has_transform")]
    new_axes = after_counts["CapabilityAxis"] - before_counts["CapabilityAxis"]
    return {
        "before_node_counts": before_counts,
        "after_node_counts": after_counts,
        "new_capability_axis_count": new_axes,
        "codebook_epoch_before": before_epoch,
        "codebook_epoch_after": after_epoch,
        "observation": dict(graph.node(observation)["attrs"]),
        "minted_edge_targets": minted,
        "has_transform_targets": transforms,
    }


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or OUT.exists():
            raise SystemExit("refusing to overwrite lock or audit capture")
        atomic(LOCK, input_lock())
        print(LOCK.relative_to(ROOT))
        return
    locked = json.loads(LOCK.read_text())
    if input_lock() != locked:
        raise SystemExit("mint side-effect audit input/source lock drift")

    raw = json.loads(RAW.read_text())
    unique: dict[str, dict] = {}
    for group in raw["groups"]:
        if group["case_type"] != "negative":
            continue
        observations = [group["clean"]] + [
            row for rows in group["noisy"].values() for row in rows]
        for result in observations:
            pair = result["seen_signatures"]
            key = json.dumps(pair, sort_keys=True, separators=(",", ":"))
            entry = unique.setdefault(key, {
                "shape_ids": set(), "group_ids": set(), "row_count": 0,
                "base_signature": pair[0], "goal_signature": pair[1],
            })
            entry["shape_ids"].add(group["shape_id"])
            entry["group_ids"].add(group["group_id"])
            entry["row_count"] += 1

    rows = []
    for key, entry in sorted(unique.items()):
        rows.append({
            "signature_pair_sha256": hashlib.sha256(key.encode()).hexdigest(),
            "shape_ids": sorted(entry["shape_ids"]),
            "group_ids": sorted(entry["group_ids"]),
            "source_observation_rows": entry["row_count"],
            "graph_replay": replay(entry["base_signature"], entry["goal_signature"]),
        })
    post = input_lock()
    if post != locked:
        raise SystemExit("post-run mint side-effect audit lock drift")
    output = {
        "schema_version": 1,
        "run_id": "heldout-polyomino-v1-negative-mint-side-effects-20260929",
        "status": "complete", "input_lock": locked,
        "post_run_input_lock": post,
        "unique_negative_signature_pairs": len(rows),
        "source_negative_observation_rows": sum(r["source_observation_rows"] for r in rows),
        "rows": rows,
    }
    atomic(OUT, output)
    print(json.dumps({
        "capture": str(OUT.relative_to(ROOT)),
        "unique_negative_signature_pairs": len(rows),
        "source_negative_observation_rows": output["source_negative_observation_rows"],
        "statuses": {status: sum(r["graph_replay"]["observation"].get("status") == status
                                 for r in rows)
                     for status in sorted({r["graph_replay"]["observation"].get("status")
                                           for r in rows})},
        "new_axes": sum(r["graph_replay"]["new_capability_axis_count"] for r in rows),
    }, indent=2))


if __name__ == "__main__":
    main()
