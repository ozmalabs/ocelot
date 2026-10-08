#!/usr/bin/env python3
"""Unsupervised phase-0 learning with position-held-out orientation probes."""
from __future__ import annotations

import hashlib
import json
import os
import random
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
import domains.seed_registry
from domains.engine_provenance import assert_measuring_engine
from domains.eye_world import PreVisualWorld, set_params, rf_centre, rf_spread
from domains.wave_world import WaveWorld
from substrate.boot_core import boot_core, load_seeds_into
from substrate_rs import _native

RUNNER = Path(__file__).resolve()
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_vision_eye_position_heldout_orientation_v1.py"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_VISION_EYE_POSITION_HELDOUT_ORIENTATION_V1_PREREG_20261005.md"
LOCK = ROOT / "evaluation/substrate_capability/vision_eye_position_heldout_orientation_v1_lock_20261005.json"
OUT = ROOT / "evaluation/reports/vision_eye_position_heldout_orientation_v1_20261005.json"
SOURCES = ("substrate/boot_core.py", "substrate/seed_loader.py", "domains/eye_world.py",
           "domains/wave_world.py", "runners/dsl/src/py.rs", "runners/dsl/src/term.rs",
           "runners/dsl/src/substrate.rs", "runners/dsl/src/rewrite.rs",
           "runners/dsl/src/persist.rs", "runners/dsl/python/substrate_rs/_native.build.json",
           "runners/dsl/Cargo.lock")
SEED_FILES = ("vision_eye.json", "vision_waves.json")
SEEDS = (40, 41, 42, 43, 44, 45)
COORDS = (3, 6, 9, 12)
ALL_SITES = tuple((y, x) for y in COORDS for x in COORDS)
HELDOUT = ((3, 3), (3, 12), (12, 3), (12, 12))
TRAIN_SITES = tuple(p for p in ALL_SITES if p not in HELDOUT)
LABELS = ("horizontal", "vertical")
H = W = 16
N_UNITS = 8
EXPOSURES = 400
STEPS = len(TRAIN_SITES) * len(LABELS) * EXPOSURES
CAP = 200_000
ETA = 0.0005


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest() -> dict:
    provenance = assert_measuring_engine()
    return {"runner_sha256": sha(RUNNER), "analyzer_sha256": sha(ANALYZER),
        "protocol_sha256": sha(PROTOCOL), "native_sha256": sha(Path(_native.__file__).resolve()),
        "engine_fingerprint": provenance["source_fingerprint"],
        "seed_sha256": {name: sha(ROOT / "seeds" / name) for name in SEED_FILES},
        "sources": {name: sha(ROOT / name) for name in SOURCES}}


def mask(site, label):
    y, x = site
    return {(y, x + dx) for dx in (-2, -1, 0, 1, 2)} if label == "horizontal" else {
        (y + dy, x) for dy in (-2, -1, 0, 1, 2)}


def mask_indices(site, label):
    return {y * W + x for y, x in mask(site, label)}


def capture_fields(eye):
    out = []
    for i in range(N_UNITS):
        rf = eye.rf(i)
        cy, cx = rf_centre(rf)
        out.append({"unit": i, "center": [float(cy), float(cx)],
                    "spread": float(rf_spread(rf)),
                    "weights": [float(v) for v in rf.reshape(-1)]})
    return out


def readout(s, eye, step):
    acts, winners = [], []
    for i, node in enumerate(eye.units):
        attrs = s.node(node)["attrs"]
        acts.append(float(attrs["act"]))
        if int(attrs.get("win_step", -1)) == step and float(attrs.get("winner", 0.0)) == 1.0:
            winners.append(i)
    return acts, winners


def worker(seed, frozen):
    before = manifest()
    if before != frozen:
        raise RuntimeError("worker inputs differ from analysis lock")
    s, agent = boot_core()
    load_seeds_into(s, agent, ["vision_waves", "vision_eye"])
    params = s.nodes("WaveParams")[0]
    for key, value in (("propagate", 0.0), ("oja", 1.0), ("oja_eta", 0.0)):
        s.set_attr(params, key, value)
    wave = WaveWorld(s, h=H, w=W, seed=seed)
    eye = PreVisualWorld(wave, n_units=N_UNITS, seed=seed)
    set_params(eye, eye=1.0, phase0=1.0, eye_open=0.0, saw=0.0, ph0_eta=ETA, frozen=0.0)
    cell_by_index = {r * W + c: node for (r, c), node in wave.cells.items()}
    initial_fields = capture_fields(eye)
    pair_schedule = [(site, label) for site in TRAIN_SITES for label in LABELS for _ in range(EXPOSURES)]
    random.Random(610_000 + seed).shuffle(pair_schedule)
    current = set()
    exposure = {f"{site[0]},{site[1]}:{label}": 0 for site in TRAIN_SITES for label in LABELS}
    writes = progress = input_ns = closure_ns = switches = 0
    sequence_hash = hashlib.sha256()
    s._inner.scale_audit_set_enabled(False)
    s._inner.scale_audit_set_per_rule_enabled(False)
    s._inner.scale_audit_reset()
    s._inner.scale_audit_per_rule_reset()
    for step, (site, label) in enumerate(pair_schedule, 1):
        target = mask_indices(site, label)
        if target != current:
            switches += 1
        started = time.perf_counter_ns()
        for idx in current - target:
            s.set_attr(cell_by_index[idx], "bursting", 0.0)
            writes += 1
        for idx in target - current:
            s.set_attr(cell_by_index[idx], "bursting", 1.0)
            writes += 1
        input_ns += time.perf_counter_ns() - started
        current = target
        exposure[f"{site[0]},{site[1]}:{label}"] += 1
        sequence_hash.update(json.dumps([list(site), label], separators=(",", ":")).encode())
        s.set_attr(eye.eye, "step", float(step))
        started = time.perf_counter_ns()
        progress += int(s._inner.run_rules(CAP))
        closure_ns += time.perf_counter_ns() - started
    learned_fields = capture_fields(eye)
    set_params(eye, frozen=1.0)
    freeze_value = float(s.node(s.nodes("EyeParams")[0])["attrs"]["frozen"])
    probes = []
    index = 0
    for site in ALL_SITES:
        for label in LABELS:
            target = mask_indices(site, label)
            step = STEPS + index + 1
            started = time.perf_counter_ns()
            for idx in current - target:
                s.set_attr(cell_by_index[idx], "bursting", 0.0)
                writes += 1
            for idx in target - current:
                s.set_attr(cell_by_index[idx], "bursting", 1.0)
                writes += 1
            input_ns += time.perf_counter_ns() - started
            current = target
            s.set_attr(eye.eye, "step", float(step))
            started = time.perf_counter_ns()
            progress += int(s._inner.run_rules(CAP))
            closure_ns += time.perf_counter_ns() - started
            acts, winners = readout(s, eye, step)
            probes.append({"probe_index": index, "site": list(site), "label": label,
                "split": "heldout" if site in HELDOUT else "train", "mask": sorted(target),
                "active_count": len(target), "acts": acts, "winners": winners})
            index += 1
    post_probe_fields = capture_fields(eye)
    after = manifest()
    return {"pid": os.getpid(), "source_before": before, "source_after": after,
        "source_stable": before == after, "result": {"seed": seed, "steps": STEPS,
        "train_sites": [list(x) for x in TRAIN_SITES], "heldout_sites": [list(x) for x in HELDOUT],
        "n_units": N_UNITS, "eta": ETA, "exposures": exposure,
        "schedule_sha256": sequence_hash.hexdigest(), "switches": switches,
        "input_writes": writes, "input_update_ns": input_ns, "closure_ns": closure_ns,
        "progress": progress, "initial_fields": initial_fields,
        "learned_fields": learned_fields, "post_probe_fields": post_probe_fields,
        "freeze_value": freeze_value, "probes": probes}}


def main():
    if sys.argv[1:2] == ["--lock"]:
        if LOCK.exists() or OUT.exists():
            raise SystemExit("refusing to overwrite position-heldout-orientation artifacts")
        value = {"schema": "VisionEyePositionHeldoutOrientationV1Lock", "inputs": manifest(),
                 "seeds": list(SEEDS), "train_sites": [list(x) for x in TRAIN_SITES],
                 "heldout_sites": [list(x) for x in HELDOUT], "labels": list(LABELS),
                 "exposures_per_training_pair": EXPOSURES, "steps": STEPS}
        LOCK.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT).as_posix())
        return 0
    if sys.argv[1:2] == ["--worker"]:
        seed = int(sys.argv[2])
        print(json.dumps(worker(seed, json.loads(LOCK.read_text())["inputs"]), sort_keys=True))
        return 0
    if not LOCK.exists():
        raise SystemExit("missing source lock; run --lock")
    lock = json.loads(LOCK.read_text())
    if manifest() != lock["inputs"]:
        raise SystemExit("stale source lock")
    env = {**os.environ, "OZMA_NO_LLM": "1", "OZMA_SEED_PERSIST_DISABLED": "1"}
    def launch(seed):
        proc = subprocess.run([sys.executable, str(RUNNER), "--worker", str(seed)],
            cwd=ROOT, env=env, text=True, capture_output=True)
        try:
            payload = json.loads(proc.stdout)
        except Exception:
            payload = None
        failure = None if proc.returncode == 0 and payload else {
            "seed": seed, "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-2000:], "stderr_tail": proc.stderr[-2000:]}
        return payload, failure
    with ThreadPoolExecutor(max_workers=6) as pool:
        completed = list(pool.map(launch, SEEDS))
    workers = [x for x, _ in completed if x]
    failures = [x for _, x in completed if x]
    post = manifest()
    results = [x["result"] for x in workers]
    checks = {"source_stable": post == lock["inputs"] and all(x["source_stable"] for x in workers),
        "six_unique_workers": len(workers) == 6 and len({x["pid"] for x in workers}) == 6,
        "all_seed_ids_present": sorted(r["seed"] for r in results) == list(SEEDS),
        "exact_schedule_and_exposure": all(r["steps"] == STEPS and len(r["probes"]) == 32 and
            set(r["exposures"].values()) == {EXPOSURES} for r in results),
        "exact_pattern_geometry": all(all(p["active_count"] == 5 and len(p["mask"]) == 5 for p in r["probes"]) for r in results),
        "freeze_and_weight_preservation": all(r["freeze_value"] == 1.0 and r["learned_fields"] == r["post_probe_fields"] for r in results),
        "native_rule_progress": all(r["progress"] > 0 and r["switches"] > 0 for r in results),
        "processes_succeeded": not failures}
    report = {"schema": "VisionEyePositionHeldoutOrientationV1Capture",
        "run_id": "vision-eye-position-heldout-orientation-v1-20261005",
        "lock_path": str(LOCK.relative_to(ROOT)), "lock_sha256": sha(LOCK),
        "locked_inputs": lock["inputs"], "post_run_inputs": post,
        "seeds": list(SEEDS), "train_sites": [list(x) for x in TRAIN_SITES],
        "heldout_sites": [list(x) for x in HELDOUT], "labels": list(LABELS),
        "workers": workers, "process_failures": failures, "checks": checks,
        "passed": all(checks.values()),
        "claim_limit": "Unsupservised phase-0 substrate representation evaluated with an external nearest-class-mean probe on position-held-out centered bars; no substrate label supervision, semantic vision, or general self-improvement claim."}
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": report["passed"], "checks": checks,
        "workers": len(workers), "failures": len(failures), "output": OUT.relative_to(ROOT).as_posix()}))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
