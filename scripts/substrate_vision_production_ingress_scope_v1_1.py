#!/usr/bin/env python3
"""Image-ingress scope pilot using the production WaveWorld frame adapter."""
from __future__ import annotations

import hashlib, json, os, platform, resource, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "runners/dsl/python")]
import substrate_vision_shared_substrate_multisheet_task_pilot_v1_4 as base
from domains.complex_cells import grating
from scripts.rung8_lib import H, W

STEM = "vision_production_ingress_scope_v1_1_20260929"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_VISION_PRODUCTION_INGRESS_SCOPE_V1_1_AMENDMENT_20260929.md"
LOCK = ROOT / f"evaluation/substrate_capability/{STEM}_lock.json"
RAW = ROOT / f"evaluation/reports/{STEM}_raw.json"
ANALYZER = ROOT / "scripts/analyze_substrate_vision_production_ingress_scope_v1.py"
CHECKPOINT_DIR = ROOT / "evaluation/reports/vision_multiseed_checkpoints_v2_0"
SEEDS = (20260935, 20260936, 20260937)
ANGLES = (0, 45, 90, 135)
PHASES = (0.0, float(__import__("math").pi / 2), float(__import__("math").pi), float(3 * __import__("math").pi / 2))
SCOPES = ("global", "root_scoped")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_inputs():
    from domains.engine_provenance import engine_provenance
    from substrate_rs import _native
    checkpoint_files = {str(s): CHECKPOINT_DIR / f"seed_{s}.json" for s in SEEDS}
    return {
        "protocol_sha256": sha(PROTOCOL), "runner_sha256": sha(__file__),
        "analyzer_sha256": sha(ANALYZER), "base_builder_sha256": sha(Path(base.__file__)),
        "base_source_inputs": base.source_inputs(),
        "wave_world_sha256": sha(ROOT / "domains/wave_world.py"),
        "complex_cells_sha256": sha(ROOT / "domains/complex_cells.py"),
        "checkpoints": {k: sha(v) for k, v in checkpoint_files.items()},
        "checkpoint_summary_sha256": sha(ROOT / "evaluation/reports/vision_multiseed_checkpoint_replication_v2_0_20260927.json"),
        "checkpoint_lock_sha256": sha(ROOT / "evaluation/substrate_capability/vision_multiseed_checkpoint_replication_v2_0_lock_20260927.json"),
        "native_extension_sha256": sha(Path(_native.__file__).resolve()),
        "engine_provenance": engine_provenance(), "python": sys.version,
        "platform": platform.platform(), "angles": list(ANGLES), "phases": list(PHASES),
    }


def peak_rss_bytes():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value * (1024 if sys.platform.startswith("linux") else 1))


def state(s, units):
    keys = ("act", "act_next", "theta", "rate", "act_step", "rate_step", "aff", "aff_step")
    return {k: [float(s.node(u)["attrs"].get(k, 0.0)) for u in units] for k in keys}


def verify_rule_variant(inner, scoped):
    rules = inner.export_rules()
    named = [r for r in rules if r.get("name") in ("st_settle", "st_settle_root_scoped_benchmark")]
    expected = "st_settle_root_scoped_benchmark" if scoped else "st_settle"
    if len(named) != 1 or named[0].get("name") != expected:
        raise RuntimeError(f"wrong settle rule variant: {[r.get('name') for r in named]}")
    encoded = json.dumps(named[0], sort_keys=True)
    if scoped and ("Neighbours" not in encoded or "has_sunit" not in encoded):
        raise RuntimeError("scoped settle rule lacks the root-owned SUnit traversal")
    if not scoped and ("NodesOfType" not in encoded or '"SUnit"' not in encoded):
        raise RuntimeError("global settle rule lacks the global SUnit population")


def one_trial(seed, angle, scope, omission=False):
    import numpy as np
    checkpoint = json.loads((CHECKPOINT_DIR / f"seed_{seed}.json").read_text())
    graph = checkpoint["graph"]
    expected_hash = checkpoint["prepared_graph_sha256"]
    if base.graph_digest(graph) != expected_hash:
        raise RuntimeError(f"seed {seed}: checkpoint graph digest mismatch")
    s, (wa, wb), (ua, ub), topology, _ = base.build_pair(seed, scope == "root_scoped")
    inner = s._inner
    verify_rule_variant(inner, scope == "root_scoped")
    inner.graph_from_dict(graph)
    if base.graph_digest(inner.graph_to_dict()) != expected_hash:
        raise RuntimeError(f"seed {seed}: restored graph digest mismatch")
    roots = (wa.retina, wb.retina)
    memberships = [set(inner.neighbours(r, "has_sunit")) for r in roots]
    if memberships != [set(ua), set(ub)] or memberships[0] & memberships[1]:
        raise RuntimeError("restored root ownership differs from checkpoint topology")
    omitted_index = None
    if omission:
        if angle != 0 or seed != SEEDS[0]:
            raise RuntimeError("omission control outside registered cell")
        omitted_index = 0
        inner.remove_edge_unchecked(roots[0], "has_sunit", ua[omitted_index])
        memberships[0].remove(ua[omitted_index])

    blank = np.zeros((H, W), dtype=np.float32)
    rows = []
    target_frames = [blank] * len(PHASES) if angle is None else [
        grating((H, W), angle, phase, 4.0) for phase in PHASES
    ]
    worker_start = time.perf_counter_ns()
    cpu_start = time.process_time_ns()
    for phase_index, target_frame in enumerate(target_frames):
        phase = PHASES[phase_index]
        phase_record = {"phase_index": phase_index, "phase_radians": phase, "target_frame_sha256": hashlib.sha256(target_frame.tobytes()).hexdigest(), "calls": []}
        for world, units, frame, label in ((wa, ua, target_frame, "target"), (wb, ub, blank, "sibling_blank")):
            call_start = time.perf_counter_ns(); call_cpu = time.process_time_ns()
            step = int(world.step(frame=frame))
            call_wall = time.perf_counter_ns() - call_start; call_cpu_ns = time.process_time_ns() - call_cpu
            # WaveWorld.drive records the exact luminance image before rule phases.
            image = np.asarray(frame, dtype=float)
            delivered = [float(s.node(world.cells[(r, c)])["attrs"].get("lum_raw", float("nan")))
                         for r in range(world.h) for c in range(world.w)]
            expected = image.reshape(-1).astype(float).tolist()
            image_mismatches = sum(a != b for a, b in zip(delivered, expected))
            phase_record["calls"].append({
                "label": label, "step_return": step, "root_step": float(s.node(world.retina)["attrs"].get("step", 0.0)),
                "input_pixels": int(np.count_nonzero(image)), "lum_raw_mismatches": image_mismatches,
                "state": state(s, units), "wall_ns": call_wall, "process_cpu_ns": call_cpu_ns,
                "rss_high_water_bytes": peak_rss_bytes(),
            })
        rows.append(phase_record)
    worker_wall = time.perf_counter_ns() - worker_start
    worker_cpu = time.process_time_ns() - cpu_start
    final = rows[-1]["calls"]
    graph = inner.graph_to_dict()
    return {
        "seed": seed, "condition": "blank" if angle is None else f"orientation_{angle}",
        "angle_label_deg": angle, "scope": scope, "omission": omission,
        "omitted_unit": None if omitted_index is None else int(ua[omitted_index].value if hasattr(ua[omitted_index], "value") else ua[omitted_index]),
        "target_member_count": len(memberships[0]), "sibling_member_count": len(memberships[1]),
        "target_unit_count": len(ua), "sibling_unit_count": len(ub),
        "topology": topology, "checkpoint_sha256": expected_hash,
        "phases": rows, "worker_wall_ns": worker_wall, "worker_process_cpu_ns": worker_cpu,
        "peak_rss_bytes": peak_rss_bytes(), "graph_node_count": len(graph.get("nodes", [])),
        "graph_edge_count": len(graph.get("edges", [])),
        "final_graph_sha256": base.graph_digest(graph),
        "rate_equation_max_abs_residual": max((abs(r - max(a - t, 0.0)) for call in final for a, t, r in zip(call["state"]["act"], call["state"]["theta"], call["state"]["rate"])), default=0.0),
        "source_stable": source_inputs() == LOCKED_INPUTS,
    }


def expected_cells():
    return [(seed, angle, scope, False) for seed in SEEDS for angle in (None, *ANGLES) for scope in SCOPES] + [
        (SEEDS[0], 0, scope, True) for scope in SCOPES
    ]


def main():
    global LOCKED_INPUTS
    if sys.argv[1:] == ["--lock"]:
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        inputs = source_inputs()
        LOCK.write_text(json.dumps({"locked_inputs": inputs}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT)); return
    LOCKED_INPUTS = source_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != LOCKED_INPUTS:
        raise SystemExit("missing or stale source lock")
    if RAW.exists():
        raise SystemExit(f"refusing to overwrite {RAW}")
    records = []
    for index, (seed, angle, scope, omission) in enumerate(expected_cells(), 1):
        row = one_trial(seed, angle, scope, omission)
        records.append(row)
        RAW.parent.mkdir(parents=True, exist_ok=True)
        RAW.write_text(json.dumps({"run_id": STEM, "locked_inputs": LOCKED_INPUTS,
                                   "expected_workers": len(expected_cells()), "workers": records,
                                   "source_stable": source_inputs() == LOCKED_INPUTS}, indent=2, sort_keys=True) + "\n")
        print(f"worker={index}/{len(expected_cells())} seed={seed} condition={row['condition']} scope={scope} omission={omission} wall_s={row['worker_wall_ns']/1e9:.3f}", flush=True)
    if source_inputs() != LOCKED_INPUTS:
        raise SystemExit("source drift during capture")


if __name__ == "__main__":
    LOCKED_INPUTS = {}
    main()
