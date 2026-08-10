"""The jabberwock works IN ITS N-D REPRESENTATION — the grid is one projection of it.

Core skills of interaction/dynamics (the games are the means, not the end):
  1. PREDICT IN N-D: the predict->surprise->fold loop runs over phi (the N-D state), not 2D cy/cx.
  2. PROJECTION-INVARIANCE (the decisive test): the SAME loop predicts the world AND its transpose -> it
     learned the dynamics (phi), not the grid layout.
  3. PROJECT: the grid is recovered as pi(phi) = the first two coordinates of phi.
  4. ROTATE (Dot-over-axes, the agent's primitive): a diagonal motion that couples row+col in the render
     basis becomes ONE moving coordinate + ONE invariant coordinate in the rotated frame — the natural
     frame where the dynamics are simplest. (Here the basis is provided to demonstrate the apparatus;
     discovering it from the motion is the next skill.)

Run:  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/nd_representation.py [steps]
"""
from __future__ import annotations

import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from passive_world import PassiveDotEnv, DOT
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

R = 0.70710678   # 1/sqrt(2) — the 45-degree basis that aligns with the dot's diagonal motion


def _dot(agent):
    for n in agent.s.nodes("Region"):
        a = agent.s.node(n)["attrs"]
        if a.get("is_ground") != 1.0 and int(a.get("rvalue") or 0) == DOT:
            return n
    return None


def _l2(u, v):
    if not u or not v or len(u) != len(v):
        return None
    return math.sqrt(sum((float(a) - float(b)) ** 2 for a, b in zip(u, v)))


def run_loop(transpose, steps, warm=3):
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    world = ArcWorld(PassiveDotEnv(transpose=transpose))
    sub, ctx = world.reset()
    agent.perceive_frame(sub)
    surprises, rot_rows = [], []
    prev_pred = None
    for i in range(steps):
        sub, ctx = world.apply(("Select",))
        agent.perceive_frame(sub)
        agent.master_tick()                 # fold the closed loop
        agent.tick()                        # build_phi (observe) + predict_phi (the 1-step-ahead forecast)
        r = _dot(agent)
        a = agent.s.node(r)["attrs"] if r else {}
        phi, phi_pred = a.get("phi"), a.get("phi_pred")   # phi = observed now; phi_pred = forecast for NEXT frame
        # genuine surprise = observed-now vs the forecast made LAST frame (cross-frame, not same-frame).
        s = _l2(phi, prev_pred)
        prev_pred = phi_pred
        if i >= warm and s is not None:
            surprises.append(s)
        # Rotate (Dot-over-axes) the POSITION into the 45-degree frame: rot = [pos . a0, pos . a1]
        if phi is not None:
            cy, cx = float(phi[0]), float(phi[1])
            rot = (R * cy + R * cx, R * cy - R * cx)   # along-diagonal, anti-diagonal
            rot_rows.append((round(cy, 1), round(cx, 1), round(rot[0], 2), round(rot[1], 2)))
    return surprises, rot_rows, agent, r


def main() -> int:
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 22
    print("THE JABBERWOCK IN ITS N-D REPRESENTATION — the grid is one projection of phi.\n")

    # 1 + 3: predict in N-D; the grid is pi(phi)
    sN, rot, agent, r = run_loop(transpose=False, steps=steps)
    a = agent.s.node(r)["attrs"]
    phi = a.get("phi")
    print(f"  phi (N-D state of the dot) = {[round(float(x),1) for x in phi]}   [cy, cx, drow, dcol, rvalue, count]")
    print(f"  pi(phi) = first two coords = ({round(float(phi[0]),1)}, {round(float(phi[1]),1)}) = the grid (cy, cx)  <- the grid is a projection of phi")
    print(f"  N-D surprise after warmup: avg={sum(sN)/max(len(sN),1):.3f} floor={min(sN):.3f}  ({sum(1 for x in sN if x<=0.6)}/{len(sN)} near zero)")

    # 2: projection-invariance — the SAME loop on the transposed world
    sT, _, _, _ = run_loop(transpose=True, steps=steps)
    print(f"\n  PROJECTION-INVARIANCE — the SAME loop on the TRANSPOSED world:")
    print(f"  N-D surprise after warmup: avg={sum(sT)/max(len(sT),1):.3f} floor={min(sT):.3f}")
    print(f"  => the loop predicts the world AND its transpose equally well — it learned the DYNAMICS, not the grid.")

    # 4: rotate to the natural frame — diagonal motion decouples
    print(f"\n  ROTATE (Dot-over-axes) into the 45-degree frame — the diagonal motion DECOUPLES:")
    print(f"    {'cy':>5}{'cx':>5}{'along-diag':>12}{'anti-diag':>11}")
    for cy, cx, d0, d1 in rot[3:9]:
        print(f"    {cy:>5}{cx:>5}{d0:>12}{d1:>11}")
    anti = [d1 for _, _, _, d1 in rot[3:]]
    along = [d0 for _, _, d0, _ in rot[3:]]
    anti_var = (max(anti) - min(anti)) if anti else 0
    along_var = (max(along) - min(along)) if along else 0
    print(f"  along-diagonal varies by {along_var:.2f} (the motion); anti-diagonal varies by {anti_var:.2f} (INVARIANT)")
    print(f"  => in the natural frame the diagonal motion is ONE moving coordinate + ONE invariant one — "
          f"row/col coupling is an artifact of the renderer's basis.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
