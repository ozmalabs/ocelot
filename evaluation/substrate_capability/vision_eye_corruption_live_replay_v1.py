#!/usr/bin/env python3
"""Live graph-rule replay of the locked phase-0 corruption masks."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import random
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
from domains.engine_provenance import assert_measuring_engine

V2_PATH = ROOT / "evaluation/substrate_capability/vision_eye_phase0_dense_map_morphology_transfer_v2_1.py"
SPEC = importlib.util.spec_from_file_location("phase0_morphology_v2_1", V2_PATH)
V2 = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(V2)
BASE = V2.BASE
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_vision_eye_corruption_live_replay_v1.py"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_VISION_EYE_CORRUPTION_LIVE_REPLAY_V1_PREREG_20261005.md"
LOCK = ROOT / "evaluation/substrate_capability/vision_eye_corruption_live_replay_v1_lock_20261005.json"
OUT = ROOT / "evaluation/reports/vision_eye_corruption_live_replay_v1_20261005.json"
V2_CAPTURE = ROOT / "evaluation/reports/vision_eye_phase0_dense_map_morphology_transfer_v2_1_20261005.json"
V2_ANALYSIS = ROOT / "evaluation/reports/vision_eye_phase0_dense_map_morphology_transfer_v2_1_analysis_20261005.json"
OFFLINE_REPORT = ROOT / "evaluation/reports/vision_eye_corruption_replay_posthoc_v1_2_20261005.json"
SEEDS = (30, 31, 32, 33, 34, 35)
MORPHOLOGIES = ("square", "cross")
CONDITIONS = (
    ("drop_active_25pct", 0.25), ("drop_active_50pct", 0.50),
    ("drop_active_75pct", 0.75), ("add_background_25pct", 0.25),
    ("add_background_50pct", 0.50),
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest() -> dict:
    provenance = assert_measuring_engine()
    sources = set(BASE.SOURCES)
    sources.update(("domains/eye_world.py", "domains/wave_world.py", "substrate/boot_core.py",
                    "substrate/seed_loader.py", "runners/dsl/src/term.rs", "runners/dsl/src/substrate.rs",
                    "runners/dsl/src/rewrite.rs", "runners/dsl/src/persist.rs",
                    "runners/dsl/python/substrate_rs/_native.build.json", "runners/dsl/Cargo.lock"))
    return {
        "runner_sha256": sha(Path(__file__).resolve()), "analyzer_sha256": sha(ANALYZER),
        "protocol_sha256": sha(PROTOCOL), "v2_1_runner_sha256": sha(V2_PATH),
        "v2_1_capture_sha256": sha(V2_CAPTURE), "v2_1_analysis_sha256": sha(V2_ANALYSIS),
        "offline_corruption_report_sha256": sha(OFFLINE_REPORT),
        "native_sha256": sha(Path(BASE._native.__file__).resolve()),
        "engine_fingerprint": provenance["source_fingerprint"],
        "seed_sha256": {name: sha(ROOT / "seeds" / name) for name in BASE.SEEDS},
        "sources": {name: sha(ROOT / name) for name in sorted(sources)},
    }


def corrupt(original: set[int], condition: str, fraction: float, seed_material: str) -> set[int]:
    seed = int.from_bytes(hashlib.sha256(seed_material.encode()).digest()[:8], "big")
    rng = random.Random(seed)
    out = set(original)
    if condition.startswith("drop_active"):
        count = max(1, round(len(original) * fraction))
        out.difference_update(rng.sample(sorted(original), count))
    else:
        count = math.ceil(len(original) * fraction)
        inactive = sorted(set(range(BASE.W * BASE.W)) - original)
        out.update(rng.sample(inactive, count))
    return out


def read_acts_and_winners(s, eye, step):
    acts, winners = [], []
    for i, node in enumerate(eye.units):
        attrs = s.node(node)["attrs"]
        acts.append(float(attrs["act"]))
        if int(attrs.get("win_step", -1)) == step and float(attrs.get("winner", 0.0)) == 1.0:
            winners.append(i)
    return acts, winners


def worker(seed: int, morphology: str, frozen: dict) -> dict:
    V2.prepare_base()
    before = manifest()
    if before != frozen:
        raise RuntimeError("worker inputs differ from source lock")
    from domains.eye_world import PreVisualWorld, set_params
    from domains.wave_world import WaveWorld

    s, agent = BASE.boot_core()
    BASE.load_seeds_into(s, agent, ["vision_waves", "vision_eye"])
    wave_params = s.nodes("WaveParams")[0]
    for key, value in (("propagate", 0.0), ("oja", 1.0), ("oja_eta", 0.0)):
        s.set_attr(wave_params, key, value)
    wave = WaveWorld(s, h=BASE.H, w=BASE.W, seed=seed)
    eye = PreVisualWorld(wave, n_units=BASE.N_UNITS, seed=seed)
    set_params(eye, eye=1.0, phase0=1.0, eye_open=0.0, saw=0.0,
               ph0_eta=BASE.ETA, frozen=0.0)
    cells = {r * BASE.W + c: node for (r, c), node in wave.cells.items()}
    train_masks = [BASE.mask(site, morphology) for site in BASE.TRAIN_SITES]
    current: set[int] = set()
    exposures = [0] * len(BASE.TRAIN_SITES)
    switches = writes = progress = train_input_ns = train_closure_ns = 0
    start = seed % len(BASE.TRAIN_SITES)
    order = [(start + i) % len(BASE.TRAIN_SITES) for i in range(len(BASE.TRAIN_SITES))]
    steps = len(BASE.TRAIN_SITES) * BASE.EXPOSURE
    s._inner.scale_audit_set_enabled(False)
    s._inner.scale_audit_set_per_rule_enabled(False)
    s._inner.scale_audit_reset()
    s._inner.scale_audit_per_rule_reset()
    for step in range(1, steps + 1):
        site = order[(step - 1) // BASE.EXPOSURE]
        target = train_masks[site]
        exposures[site] += 1
        if current and current != target:
            switches += 1
        started = time.perf_counter_ns()
        for idx in current - target:
            s.set_attr(cells[idx], "bursting", 0.0)
            writes += 1
        for idx in target - current:
            s.set_attr(cells[idx], "bursting", 1.0)
            writes += 1
        train_input_ns += time.perf_counter_ns() - started
        current = set(target)
        s.set_attr(eye.eye, "step", float(step))
        started = time.perf_counter_ns()
        progress += int(s._inner.run_rules(BASE.CAP))
        train_closure_ns += time.perf_counter_ns() - started

    learned = BASE.fields(s, eye)
    set_params(eye, frozen=1.0)
    freeze_value = float(s.node(s.nodes("EyeParams")[0])["attrs"]["frozen"])
    clean_rows = []
    probe_index = 0
    probe_input_ns = probe_closure_ns = probe_writes = 0
    all_sites = BASE.TRAIN_SITES + BASE.HELDOUT_SITES
    for rep in range(BASE.REPEATS):
        for site_index, site in enumerate(all_sites):
            target = BASE.mask(site, morphology)
            step = steps + probe_index + 1
            started = time.perf_counter_ns()
            for idx in current - target:
                s.set_attr(cells[idx], "bursting", 0.0)
                probe_writes += 1
            for idx in target - current:
                s.set_attr(cells[idx], "bursting", 1.0)
                probe_writes += 1
            probe_input_ns += time.perf_counter_ns() - started
            current = set(target)
            s.set_attr(eye.eye, "step", float(step))
            started = time.perf_counter_ns()
            progress += int(s._inner.run_rules(BASE.CAP))
            probe_closure_ns += time.perf_counter_ns() - started
            acts, winners = read_acts_and_winners(s, eye, step)
            clean_rows.append({"probe_index": probe_index, "rep": rep, "site_index": site_index,
                               "location_status": "trained" if site_index < 9 else "heldout",
                               "site": list(site), "mask": sorted(target),
                               "active_count": len(target), "acts": acts, "winners": winners})
            probe_index += 1

    corruption_rows = []
    for clean in clean_rows:
        if clean["location_status"] != "heldout":
            continue
        original = set(clean["mask"])
        for condition, fraction in CONDITIONS:
            target = corrupt(original, condition, fraction,
                             f"phase0-v2.1|{seed}|{morphology}|{clean['probe_index']}|{condition}")
            step = steps + probe_index + 1
            started = time.perf_counter_ns()
            for idx in current - target:
                s.set_attr(cells[idx], "bursting", 0.0)
                probe_writes += 1
            for idx in target - current:
                s.set_attr(cells[idx], "bursting", 1.0)
                probe_writes += 1
            probe_input_ns += time.perf_counter_ns() - started
            current = set(target)
            s.set_attr(eye.eye, "step", float(step))
            started = time.perf_counter_ns()
            progress += int(s._inner.run_rules(BASE.CAP))
            probe_closure_ns += time.perf_counter_ns() - started
            acts, winners = read_acts_and_winners(s, eye, step)
            corruption_rows.append({
                "probe_index": clean["probe_index"], "condition": condition,
                "fraction": fraction, "site": clean["site"],
                "mask": sorted(target), "active_count": len(target),
                "mask_sha256": hashlib.sha256(json.dumps(sorted(target)).encode()).hexdigest(),
                "acts": acts, "winners": winners,
            })
            probe_index += 1
    post_probe_fields = BASE.fields(s, eye)
    after = manifest()
    return {
        "pid": os.getpid(), "source_before": before, "source_after": after,
        "source_stable": before == after,
        "result": {"seed": seed, "morphology": morphology,
                   "sites": [list(x) for x in BASE.TRAIN_SITES],
                   "heldout_sites": [list(x) for x in BASE.HELDOUT_SITES],
                   "site_order": order, "steps": steps, "exposures_per_site": exposures,
                   "switches": switches, "train_input_writes": writes,
                   "probe_input_writes": probe_writes, "train_input_update_ns": train_input_ns,
                   "train_closure_ns": train_closure_ns, "probe_input_ns": probe_input_ns,
                   "probe_closure_ns": probe_closure_ns, "progress": progress,
                   "freeze_value": freeze_value, "learned_fields": learned,
                   "post_probe_fields": post_probe_fields,
                   "clean_probes": clean_rows, "corrupted_probes": corruption_rows},
    }


def main() -> int:
    if sys.argv[1:2] == ["--lock"]:
        if LOCK.exists() or OUT.exists():
            raise SystemExit("refusing to overwrite live corruption replay artifacts")
        V2.prepare_base()
        lock = {"schema": "VisionEyeCorruptionLiveReplayV1Lock", "inputs": manifest(),
                "seeds": list(SEEDS), "morphologies": list(MORPHOLOGIES),
                "conditions": [{"condition": c, "fraction": f} for c, f in CONDITIONS],
                "train_sites": [list(x) for x in BASE.TRAIN_SITES],
                "heldout_sites": [list(x) for x in BASE.HELDOUT_SITES],
                "exposure_per_site": BASE.EXPOSURE, "repeats": BASE.REPEATS}
        LOCK.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT).as_posix())
        return 0
    if sys.argv[1:2] == ["--worker"]:
        seed, morphology = int(sys.argv[2]), sys.argv[3]
        print(json.dumps(worker(seed, morphology, json.loads(LOCK.read_text())["inputs"]), sort_keys=True))
        return 0

    if not LOCK.exists():
        raise SystemExit("missing source lock; run --lock after protocol and analyzer are final")
    frozen = json.loads(LOCK.read_text())
    V2.prepare_base()
    if manifest() != frozen["inputs"]:
        raise SystemExit("stale live corruption source lock")
    jobs = [(seed, morphology) for seed in SEEDS for morphology in MORPHOLOGIES]
    random.Random(20261009).shuffle(jobs)
    env = {**os.environ, "OZMA_NO_LLM": "1", "OZMA_SEED_PERSIST_DISABLED": "1"}

    def launch(job):
        seed, morphology = job
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(seed), morphology],
                              cwd=ROOT, env=env, text=True, capture_output=True)
        try:
            payload = json.loads(proc.stdout)
        except Exception:
            payload = None
        failure = None
        if proc.returncode or payload is None:
            failure = {"seed": seed, "morphology": morphology, "returncode": proc.returncode,
                       "stdout_tail": proc.stdout[-2000:], "stderr_tail": proc.stderr[-2000:]}
        return ({"seed": seed, "morphology": morphology, "worker": payload} if payload else None), failure

    with ThreadPoolExecutor(max_workers=12) as pool:
        launched = list(pool.map(launch, jobs))
    rows = [row for row, _ in launched if row is not None]
    failures = [failure for _, failure in launched if failure is not None]
    V2.prepare_base()
    post = manifest()
    results = [row["worker"]["result"] for row in rows]
    output = {
        "schema": "VisionEyeCorruptionLiveReplayV1Capture",
        "run_id": "vision-eye-corruption-live-replay-v1-20261005",
        "lock_path": str(LOCK.relative_to(ROOT)), "lock_sha256": sha(LOCK),
        "locked_inputs": frozen["inputs"], "post_run_inputs": post,
        "worker_order": [[seed, morphology] for seed, morphology in jobs],
        "rows": rows, "process_failures": failures,
        "checks": {
            "source_stable": post == frozen["inputs"] and all(r["worker"]["source_stable"] for r in rows),
            "twelve_workers": len(rows) == 12,
            "six_complete_seed_pairs": len({r["seed"] for r in rows}) == 6 and all(sum(x["seed"] == seed for x in rows) == 2 for seed in SEEDS),
            "distinct_worker_pids": len({r["worker"]["pid"] for r in rows}) == len(rows),
            "exact_clean_and_corruption_probe_counts": all(len(r["clean_probes"]) == 75 and len(r["corrupted_probes"]) == 240 for r in results),
            "exact_training_schedule": all(r["steps"] == 36000 and r["exposures_per_site"] == [4000] * 9 and r["switches"] == 8 for r in results),
            "unique_clean_winners": all(len(p["winners"]) == 1 for r in results for p in r["clean_probes"]),
            "weights_unchanged_after_freeze": all(r["freeze_value"] == 1.0 and r["learned_fields"] == r["post_probe_fields"] for r in results),
            "processes_succeeded": not failures,
        },
    }
    output["passed"] = all(output["checks"].values())
    OUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": output["passed"], "checks": output["checks"],
                      "workers": len(rows), "failures": len(failures),
                      "output": OUT.relative_to(ROOT).as_posix()}))
    return 0 if output["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
