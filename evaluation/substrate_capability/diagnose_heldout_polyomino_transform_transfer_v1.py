#!/usr/bin/env python3
"""Replay saved v1 perceived signatures and retain graph-level outcomes."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]

PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_HELDOUT_POLYOMINO_TRANSFORM_TRANSFER_V1_GRAPH_REPLAY_DIAGNOSTIC_20260929.md"
RUNNER = Path(__file__).resolve()
RAW = ROOT / "evaluation/reports/heldout_polyomino_transform_transfer_v1/capture.json"
LOCK = ROOT / "evaluation/substrate_capability/heldout_polyomino_transform_transfer_v1_graph_replay_lock_20260929.json"
OUT = ROOT / "evaluation/reports/heldout_polyomino_transform_transfer_v1_graph_replay"
CAPTURE = OUT / "graph_replay.json"
SOURCES = (
    "worlds/arc_ls20_scenario.py",
    "worlds/arc.py",
    "substrate/boot_core.py",
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
        "protocol": digest(PROTOCOL),
        "runner": digest(RUNNER),
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


def graph_replay(base_sig: list, goal_sig: list) -> dict:
    from substrate.boot_core import boot_core
    from domains import reflective_faculty as rf
    from worlds.arc_ls20_scenario import DT

    s, agent = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, agent)
    s.add_node("ShapeSignature", {
        "name": "sym", "signature": json.dumps(base_sig), "kind": "faculty",
        "faculty": "sym", "dim_types": DT,
    })
    epoch = s.node(agent)["attrs"].get("codebook_epoch") or 0.0
    observation = s.add_node("Observation", {
        "signature": goal_sig, "key": ["heldout_graph_replay"],
        "status": "decoded", "residual": goal_sig,
        "decoded_epoch": epoch, "dim_types": DT,
    })
    s.add_edge(agent, "observed", observation)
    native.run_rules()
    attrs = s.node(observation)["attrs"]
    transforms = [dict(s.node(node)["attrs"])
                  for node in s.neighbours(observation, "has_transform")]
    latent = [dict(s.node(node)["attrs"])
              for node in s.neighbours(observation, "has_latent_dimension")]
    return {
        "status": attrs.get("status"),
        "covered_by": attrs.get("covered_by"),
        "transform_checked": attrs.get("transform_checked"),
        "transform_explained": attrs.get("transform_explained"),
        "dim_checked": attrs.get("dim_checked"),
        "dim_explained": attrs.get("dim_explained"),
        "transform": attrs.get("transform"),
        "dim_infer": attrs.get("dim_infer"),
        "has_transform": transforms,
        "has_latent_dimension": latent,
    }


def observations(raw: dict):
    for group in raw["groups"]:
        yield group, "clean", None, None, group["clean"]
        for sigma, rows in group["noisy"].items():
            for rep, row in enumerate(rows, 1):
                yield group, "noisy", int(sigma), rep, row


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or CAPTURE.exists():
            raise SystemExit("refusing to overwrite lock or diagnostic capture")
        atomic(LOCK, input_lock())
        print(LOCK.relative_to(ROOT))
        return
    locked = json.loads(LOCK.read_text())
    if input_lock() != locked:
        raise SystemExit("diagnostic input/source lock drift")

    raw = json.loads(RAW.read_text())
    unique: dict[str, dict] = {}
    rows = []
    for group, arm, sigma, rep, result in observations(raw):
        seen = result["seen_signatures"]
        if len(seen) != 2:
            raise SystemExit(f"expected two seen signatures in {group['group_id']}")
        key = json.dumps(seen, sort_keys=True, separators=(",", ":"))
        if key not in unique:
            unique[key] = graph_replay(seen[0], seen[1])
        rows.append({
            "group_id": group["group_id"], "case_type": group["case_type"],
            "shape_id": group["shape_id"], "arm": arm, "sigma": sigma,
            "replicate": rep, "adapter_key": result["recognized_key"],
            "signature_pair_sha256": hashlib.sha256(key.encode()).hexdigest(),
            "graph": unique[key],
        })

    post = input_lock()
    if post != locked:
        raise SystemExit("post-run diagnostic input/source lock drift")
    output = {
        "schema_version": 1,
        "run_id": "heldout-polyomino-transform-transfer-v1-graph-replay-20260929",
        "status": "complete",
        "input_lock": locked,
        "post_run_input_lock": post,
        "raw_capture_sha256": locked["raw_capture"]["sha256"],
        "unique_signature_pairs": len(unique),
        "observation_count": len(rows),
        "rows": rows,
    }
    atomic(CAPTURE, output)
    print(json.dumps({"capture": str(CAPTURE.relative_to(ROOT)),
                      "unique_signature_pairs": len(unique),
                      "observations": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
