"""Drive the pre-registered redundancy ablation sweep (VISION_REDUNDANCY_PREREG.md).

Mechanical harness: builds the pre-registered config list, runs each as an
isolated pytest process over the rung-7 vision bench, writes one JSON per
config. Resumable — an existing output file is not recomputed.

Nothing on disk under `seeds/` is ever modified; the ablation is the in-process
manifest filter in `redundancy_ablate_plugin`.
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import random
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "results", "redundancy")

# Selection rule (PREREG §2): blast radius >= 2 on the bench seed map.
TARGETS = [
    "decision_core", "epistemics_core", "experimentation_core", "goal_construction",
    "learning_core", "memory_core", "motor_core", "perception_core", "reflex_core",
    "self_monitoring", "theorem_core",
    "vision_waves", "vision_onoff", "vision_maps", "vision_lateral", "vision_floor",
    "vision_complex", "vision_compose", "vision_dorsal", "vision_eye", "vision_growth",
    "sensory_convolution", "shape_decode_loop", "math_capability_shapes",
    "self_design_axis",
]

# PREREG §3 Arm 3: nested severity sweep for 2 <= n <= 15. RNG seeds 59000/59001
# from the allocated block 59000-59999.
SWEEP_MIN, SWEEP_MAX = 2, 15
PERM_SEEDS = [59000, 59001]


def bench_files() -> list[str]:
    out = []
    with open(os.path.join(ROOT, "scripts", "rung7_vision_bench.sh")) as fh:
        for ln in fh:
            ln = ln.strip()
            if ln.startswith("tests/"):
                out.append(ln.rstrip(" \\"))
    return out


def seed_rules(sid: str) -> list[str]:
    with open(os.path.join(ROOT, "seeds", f"{sid}.json")) as fh:
        d = json.load(fh)
    return [r.get("name", "") for r in d.get("rules", [])]


def configs() -> list[dict]:
    cfgs: list[dict] = []
    # Arm 0 -- baseline determinism + concurrency gate.
    for i in range(3):
        cfgs.append({"tag": f"baseline_{i}", "seed": "", "rules": "", "census": False})
    # Arm 1 -- rule-firing census.
    cfgs.append({"tag": "census", "seed": "", "rules": "", "census": True})
    # Arm 2 -- whole-seed ablation matrix.
    for sid in TARGETS:
        cfgs.append({"tag": f"whole__{sid}", "seed": sid, "rules": "*", "census": False})
    # Arm 3 -- nested severity curves. k = n reuses Arm 2 (identical set), so the
    # sweep runs k = 1..n-1 only. Logged, not silently dropped.
    for sid in TARGETS:
        rules = seed_rules(sid)
        n = len(rules)
        if not (SWEEP_MIN <= n <= SWEEP_MAX):
            continue
        for ps in PERM_SEEDS:
            perm = list(rules)
            random.Random(ps).shuffle(perm)
            for k in range(1, n):
                cfgs.append({"tag": f"sev__{sid}__p{ps}__k{k}", "seed": sid,
                             "rules": ",".join(perm[:k]), "census": False})
    return cfgs


def run_one(cfg: dict) -> tuple[str, int]:
    out = os.path.join(OUTDIR, cfg["tag"] + ".json")
    if os.path.exists(out):
        return cfg["tag"], -1
    env = dict(os.environ)
    env["REDUNDANCY_ABLATE_SEED"] = cfg["seed"]
    env["REDUNDANCY_ABLATE_RULES"] = cfg["rules"]
    env["REDUNDANCY_CENSUS"] = "1" if cfg["census"] else "0"
    env["REDUNDANCY_OUT"] = out
    env["TMPDIR"] = os.path.join("/tmp", "redundancy_" + cfg["tag"])
    os.makedirs(env["TMPDIR"], exist_ok=True)
    # PIN the numeric environment for EVERY config. Concurrent pytest processes
    # each spawning a BLAS thread pool oversubscribed 12 cores; worse, BLAS
    # thread count can change floating-point reduction order, so an unpinned
    # environment is not merely slow, it is a instrument that varies between
    # configs. Fixed here so every run in the sweep shares one environment.
    for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
               "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        env[_v] = "1"
    cmd = [sys.executable, "-W", "ignore", "-m", "pytest", "-q", "-p", "no:randomly",
           "-p", "scripts.redundancy_ablate_plugin", *bench_files()]
    p = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True,
                       timeout=3600)
    # A run that dies before sessionfinish writes nothing -- record it as a CRASH
    # rather than letting the config vanish (PREREG §4: a crash is a result).
    if not os.path.exists(out):
        with open(out, "w") as fh:
            json.dump({"seed": cfg["seed"], "rules_dropped": cfg["rules"],
                       "exitstatus": p.returncode, "crashed_before_report": True,
                       "stdout_tail": p.stdout[-8000:], "stderr_tail": p.stderr[-8000:],
                       "per_file": {}, "passed": 0, "failed": 0, "errors": []}, fh, indent=1)
    return cfg["tag"], p.returncode


def main() -> int:
    os.makedirs(OUTDIR, exist_ok=True)
    cfgs = configs()
    todo = [c for c in cfgs if not os.path.exists(os.path.join(OUTDIR, c["tag"] + ".json"))]
    print(f"[sweep] {len(cfgs)} configs, {len(todo)} to run", flush=True)
    workers = int(os.environ.get("REDUNDANCY_WORKERS", "5"))
    done = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        for tag, rc in ex.map(run_one, todo):
            done += 1
            print(f"[sweep] {done}/{len(todo)} {tag} rc={rc}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
