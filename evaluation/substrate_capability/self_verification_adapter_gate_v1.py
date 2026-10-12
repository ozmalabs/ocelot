#!/usr/bin/env python3
"""Source-locked positive/negative gate replay through WorldAdapter."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_SELF_VERIFICATION_ADAPTER_GATE_V1_PREREG_20260929.md"
RUNNER = Path(__file__).resolve()
LOCK = ROOT / "evaluation/substrate_capability/self_verification_adapter_gate_v1_lock_20260929.json"
OUT = ROOT / "evaluation/reports/self_verification_adapter_gate_v1"
CAPTURE = OUT / "capture.json"
SOURCES = (
    "domains/self_verification.py", "domains/substrate_extension.py",
    "domains/reflective_faculty.py", "domains/grounding_reach.py",
    "substrate/boot_core.py", "substrate/world_adapter.py", "substrate/graph.py",
    "substrate/seed_loader.py", "seeds/composer_faculty_pipeline.json",
    "seeds/shape_decode_loop.json", "runners/dsl/src/shape_decode.rs",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
    "runners/dsl/python/substrate_rs/_native.build.json",
)
GAP = {"faculty": "verification_gate_probe", "observation": [
    ["classify the item", "self", "input"],
    ["route to a handler", "input", "handler"],
    ["mark handled", "handler", "done"]], "status": "perceived"}
HELD = [[5, "low"], [12, "high"]]
PRIOR = [[20, "high"], [1, "low"]]
REPLICATES = (1, 2, 3)


def digest(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}


def input_lock() -> dict:
    return {"schema_version": 1, "protocol": digest(PROTOCOL), "runner": digest(RUNNER),
            "sources": [digest(ROOT / x) for x in SOURCES], "gap_fixture": GAP,
            "held": HELD, "prior": PRIOR, "replicates": list(REPLICATES),
            "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                         text=True, capture_output=True, check=True).stdout.strip()}


def atomic(path: Path, obj: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, sort_keys=True, indent=2, default=str) + "\n")
    tmp.replace(path)


def gate_state(sub, native, result: dict) -> dict:
    claims = list(sub.nodes("VClaim"))
    probes = list(sub.nodes("ControlProbe"))
    gates = [n for n in sub.nodes("Rule") if sub.node(n)["attrs"].get("id") == "self_verify_gate"]
    native_gates = [r for r in native.export_rules() if r.get("name") == "self_verify_gate"]
    claim_attrs = dict(sub.node(result["claim_node"])["attrs"])
    probe_attrs = dict(sub.node(result["probe_node"])["attrs"])
    return {"claim_attrs": claim_attrs, "probe_attrs": probe_attrs,
            "graph_claim_count": len(claims), "graph_probe_count": len(probes),
            "graph_gate_rule_count": len(gates), "native_gate_rule_count": len(native_gates),
            "native_gate_rule_names": [r.get("name") for r in native_gates]}


def real(rep: int) -> dict:
    from substrate.world_adapter import WorldAdapter
    from domains import reflective_faculty as rf
    from domains import substrate_extension as se
    agent = WorldAdapter(seeds=())
    sub, native, _ = rf._resolve_agent(agent)
    gap = sub.add_node("CapabilityGap", dict(GAP))
    started = time.perf_counter()
    outcome = se.extend_for_gap(agent, gap, verify=True)
    elapsed = time.perf_counter() - started
    result = outcome["verified"]
    return {"kind": "composed_pipeline", "replicate": rep, "outcome": outcome,
            "elapsed_seconds": elapsed, "gate_state": gate_state(sub, native, result)}


def fake_mechanism(case) -> bool:
    value, label = case
    return (value >= 3) == (label == "high")


def ground_sensor(sub, native):
    agent = sub.add_node("Agent", {})
    percept = sub.add_node("VisionPercept", {})
    native.add_edge_unchecked(agent, "perceives", percept)
    support = sub.add_node("Collapse", {"label": "support"})
    native.add_edge_unchecked(support, "grounded_in", percept)
    return support


def fake(rep: int) -> dict:
    from substrate.world_adapter import WorldAdapter
    from domains import reflective_faculty as rf
    from domains.self_verification import Claim, verify_claim
    agent = WorldAdapter(seeds=())
    sub, native, _ = rf._resolve_agent(agent)
    claim = Claim("known fake threshold on held values", fake_mechanism, HELD,
                  fake_mechanism, PRIOR,
                  ground_support=lambda s: ground_sensor(s, native))
    started = time.perf_counter()
    result = verify_claim(agent, claim)
    elapsed = time.perf_counter() - started
    return {"kind": "known_fake", "replicate": rep, "result": result,
            "elapsed_seconds": elapsed, "gate_state": gate_state(sub, native, result)}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or CAPTURE.exists():
            raise SystemExit("refusing to overwrite existing lock/capture")
        atomic(LOCK, input_lock()); print(LOCK.relative_to(ROOT)); return
    locked = json.loads(LOCK.read_text())
    if input_lock() != locked:
        raise SystemExit("source/fixture lock drift")
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    rows = [real(rep) for rep in REPLICATES] + [fake(rep) for rep in REPLICATES]
    post = input_lock()
    if post != locked:
        raise SystemExit("post-run source/fixture lock drift")
    capture = {"schema_version": 1, "run_id": "self-verification-adapter-gate-v1-20260929",
               "status": "complete", "input_lock": locked, "post_run_input_lock": post,
               "cases": rows, "process": {"wall_seconds": time.perf_counter()-start_wall,
                                            "cpu_seconds": time.process_time()-start_cpu}}
    atomic(CAPTURE, capture)
    print(json.dumps({"capture": str(CAPTURE.relative_to(ROOT)), "cases": len(rows),
                      "wall_seconds": capture["process"]["wall_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
