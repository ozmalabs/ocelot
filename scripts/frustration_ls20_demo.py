#!/usr/bin/env python3
"""frustration_ls20_demo — BLOCK 226000 ls20 DEMONSTRATION (honest scope).

Wires the frustration modulator to the ACTUAL 221000 understanding signals
(per-cycle surprise + model accuracy from `investigate`) on the OFFLINE
arc_ls20_scenario corpus (reproducible; no live API). Two runs:

  PRODUCTIVE (clean perception): the agent probes and LEARNS -- surprise drops,
    model accuracy climbs -> each probe cycle yields understanding -> the repeats
    are NOT futile -> frustration stays flat -> NO break.
  FUTILE (perception thrashing, huge sigma): recognition keeps FAILING
    inconsistently -> surprise stays high, accuracy stays 0 -> the same probe
    action recurs with NO understanding-gain -> frustration RISES -> break_now
    fires -> the agent STOPS (the emotional reaction the owner asked for).

HONEST FRAMING: the live ls20 cycling the owner saw is partly the naive
live-harness action policy; this demonstrates the CAPABILITY (emotional
regulation against futile repetition) on the real understanding signal. The
per-cycle observables fed to the modulator are MECHANICAL reads of the 221000
`investigate` outputs; every frustration/stop DECISION is the graph rule.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.join(_ROOT, "runners", "dsl", "python"),
           os.path.join(_ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np  # noqa: E402
from worlds.arc_ls20_understanding import investigate  # noqa: E402
from arc_ls20_understanding_measure import ALL6, build_station_set, _noisy_observe  # noqa: E402
from domains.frustration_world import FrustrationWorld  # noqa: E402


def _run(kind, seed, cycles=10):
    rng = np.random.default_rng(seed)
    stset = build_station_set(rng, ALL6)
    obs = (None if kind == "productive"
           else (lambda f, p, _r=rng: _noisy_observe(f, p, 64.0, _r)))
    res = investigate(stset, (0, 0), (15, 15), cycles=cycles, observe_fn=obs)
    surprise = res["surprise"]          # per-cycle residual (0 = predicted right)
    accuracy = res["accuracy"]          # per-cycle model accuracy (oracle read)

    # feed the REAL 221000 per-cycle signals into the frustration modulator.
    # sig = "probe" (the agent repeats the SAME kind of action -- probing);
    # d_hyp = 1 iff the model gained an accurate station this cycle (accuracy up);
    # s_drop = 1 iff this cycle's surprise is a strict new running-minimum.
    w = FrustrationWorld(enabled=True)
    smin = None; prev_acc = 0.0
    traj = []; break_cycle = None; narration = None
    for t in range(len(surprise)):
        s = surprise[t]; acc = accuracy[t]
        s_drop = 1 if (smin is None or s < smin) else 0
        smin = s if smin is None else min(smin, s)
        d_hyp = 1 if acc > prev_acc + 1e-9 else 0
        prev_acc = acc
        frust, brk = w.observe("probe", d_hyp=d_hyp, d_state=0, s_drop=s_drop)
        traj.append(frust)
        if brk == 1.0 and break_cycle is None:
            break_cycle = t; narration = w.narrate()
            break
    return {"kind": kind, "seed": int(seed), "surprise": surprise,
            "accuracy": accuracy, "frustration_traj": traj,
            "break_cycle": break_cycle, "narration": narration}


def main():
    out = {"block": 226000, "note": (
        "ls20 demonstration on the OFFLINE arc_ls20_scenario corpus; frustration "
        "wired to the REAL 221000 per-cycle surprise/accuracy. Honest: the live "
        "cycling is partly the naive harness policy; this shows the CAPABILITY.")}
    prod = _run("productive", 226500)
    fut = _run("futile", 226501)
    out["productive"] = prod
    out["futile"] = fut
    dst = os.path.join(_ROOT, "results", "frustration_ls20_demo.json")
    with open(dst, "w") as f:
        json.dump(out, f, indent=1)
    print("PRODUCTIVE ls20 (learns): surprise", prod["surprise"])
    print("  frustration_traj", prod["frustration_traj"], "break", prod["break_cycle"])
    print("FUTILE ls20 (thrashes): surprise", fut["surprise"])
    print("  frustration_traj", fut["frustration_traj"], "break", fut["break_cycle"])
    print("  narration:", fut["narration"])
    print("wrote", dst)


if __name__ == "__main__":
    main()
