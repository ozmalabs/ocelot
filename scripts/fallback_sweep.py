"""Run the pre-registered 26 fallback probes: BASELINE + 25 whole-seed ablations.

The 25 targets are EXACTLY the redundancy audit's `TARGETS` (blast radius >= 2
on the rung-7 bench). That selection rule was fixed in
`VISION_FALLBACK_VOCAB_PREREG.md` §6 before any run: they are the only seeds
with a measured before/after, which is what makes a conjunction gate possible.

One isolated subprocess per arm, BLAS threads pinned for every one of them —
the audit discarded a whole sweep and re-ran it for exactly this reason ("an
instrument that varies between configs is not one instrument").
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT_DIR = os.path.join(ROOT, "results", "fallback")

# Verbatim from scripts/redundancy_sweep.py — not re-derived, so the coverage
# claim is exactly the audit's and can be compared line for line.
TARGETS = [
    "decision_core", "epistemics_core", "experimentation_core", "goal_construction",
    "learning_core", "memory_core", "motor_core", "perception_core", "reflex_core",
    "self_monitoring", "theorem_core", "vision_waves", "vision_onoff", "vision_maps",
    "vision_lateral", "vision_floor", "vision_complex", "vision_compose",
    "vision_dorsal", "vision_eye", "vision_growth", "sensory_convolution",
    "shape_decode_loop", "math_capability_shapes", "self_design_axis",
]


def run_one(target: str, count_totals: bool) -> tuple[str, int]:
    name = target or "BASELINE"
    out = os.path.join(OUT_DIR, f"{name}.json")
    if os.path.exists(out):
        return name, 0
    env = dict(os.environ)
    for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
              "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        env[v] = "1"
    env["FALLBACK_COUNT_TOTALS"] = "1" if count_totals else "0"
    cmd = [sys.executable, "-W", "ignore",
           os.path.join(ROOT, "scripts", "fallback_probe.py"), target, out]
    p = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=3600)
    if not os.path.exists(out):
        with open(out, "w") as f:
            json.dump({"crashed": True, "target": target,
                       "stdout": p.stdout[-4000:], "stderr": p.stderr[-4000:]}, f, indent=1)
    return name, p.returncode


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    count_totals = os.environ.get("FALLBACK_COUNT_TOTALS", "1") == "1"
    arms = [""] + TARGETS
    workers = int(os.environ.get("FALLBACK_WORKERS", "5"))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for name, rc in ex.map(lambda t: run_one(t, count_totals), arms):
            print(f"  {name:28s} rc={rc}")
    print(f"[fallback_sweep] {len(arms)} arms -> {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
