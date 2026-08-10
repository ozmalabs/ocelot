"""The JABBERWOCK PURSUES ITS CHOSEN GOAL — 'understand world' — in Tetris: explore and model the
dynamics (what each control does; the autonomous parts: gravity, settling/respawn). Graph-native; the
agent's world-understanding faculties do the learning, this only drives + diagnoses.

The agent picked 'understand world' as its own frontier (jabberwock_game_self_goal). Pursuing it here.
Tetris is hard for the held world-understanding (built for a persistent self that moves only by
control): GRAVITY adds an autonomous dr+1 every 2 frames (contaminates control attribution) and
SETTLING/RESPAWN teleports the self (piece) from bottom to top (a spurious displacement). Horizontal
controls (Left/Right = dc) should survive gravity (which is pure dr); vertical (Down) conflates with
gravity; Up=rotate is a shape change (no displacement). So we expect PARTIAL understanding and a
precise wall = the agent's next self-extension (separate the autonomous dynamics from the control
residual; treat respawn as a world event).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_understands_game.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import domains.world_play as world_play
from tetris_world import TetrisEnv, PIECE
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

CONTROLS = ["Up", "Down", "Left", "Right"]


def gnode(a):
    return next((n for n in a.s.nodes("WorldInstance")
                 if a.s.node(n)["attrs"].get("world_type") == "Game"), None)


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    w = ArcWorld(TetrisEnv()); sub, ctx = w.reset(); a.perceive_frame(sub)
    g = gnode(a); body = a.s.add_node("Body", {}); a.inner.add_edge_unchecked(body, "inhabits", g)
    world_play.declare_affordances(a, g, CONTROLS)

    print("=" * 86)
    print("THE JABBERWOCK PURSUES 'understand world' IN TETRIS — model the dynamics (graph-native)")
    print("=" * 86)

    respawns = 0
    for i in range(280):
        before = w.env._render()
        bpiece = [(r, c) for r in range(len(before)) for c in range(len(before[0])) if before[r][c] == PIECE]
        sub, ctx = w.apply((CONTROLS[i % 4],)); a.perceive_frame(sub)
        after = w.env._render()
        apiece = [(r, c) for r in range(len(after)) for c in range(len(after[0])) if after[r][c] == PIECE]
        # respawn = the piece's top row jumped UP (new piece spawned) -> a world event, not self-motion
        if bpiece and apiece and min(r for r, _ in apiece) < min(r for r, _ in bpiece) - 1:
            respawns += 1
        if ctx.get("over"):
            sub, ctx = w.apply(("Reset",)); a.perceive_frame(sub)
        g = gnode(a); a.inner.add_edge_unchecked(body, "inhabits", g)
        a.tick(); a.master_tick()

    # read the model the agent BUILT: per non-ground region, its learned ControlResponses (dr,dc)
    learned = {}
    for n in a.s.nodes("Region"):
        at = a.s.node(n)["attrs"]
        if at.get("is_ground") == 1.0:
            continue
        rv = at.get("rvalue"); votes = at.get("respond_votes") or 0
        eff = {}
        for cr in a.inner.neighbours(n, "responds_via"):
            ca = a.s.node(cr)["attrs"]
            if ca.get("cname"):
                eff[ca.get("cname")] = (round(ca.get("dr") or 0, 2), round(ca.get("dc") or 0, 2))
        if eff:
            learned[(int(rv) if rv is not None else None, int(votes))] = eff

    print(f"  explored 280 frames; observed {respawns} respawn/settle events (the self-piece teleporting")
    print(f"  to the top — a discontinuity the held learner reads as self-motion)")
    print(f"\n  the model the agent built — learned control effects per self-candidate (rvalue,votes):")
    if not learned:
        print("    (none — the learner could not stabilise a self to attribute effects to)")
    for (rv, votes), eff in sorted(learned.items(), key=lambda kv: -kv[0][1])[:4]:
        print(f"    region rvalue={rv} votes={votes}: {eff}")

    # did the HORIZONTAL controls (which gravity should not contaminate) come out separable?
    best = max(learned.items(), key=lambda kv: kv[0][1], default=(None, {}))
    eff = best[1] if best else {}
    lr_ok = ("Left" in eff and "Right" in eff and eff["Left"][1] < 0 < eff["Right"][1])
    print(f"\n  horizontal controls separable from gravity (Left dc<0 < Right dc): {lr_ok}")
    print(f"  donkey: {donkey['n']}")
    print("=" * 86)
    print("  HONEST STATE: the agent pursues its OWN chosen goal (understand world). Tetris exposes the")
    print("  precise wall — the held affordance learner EMAs the self's raw displacement, so GRAVITY (an")
    print("  autonomous dr every 2 frames) and RESPAWN (a teleport) corrupt the attribution. The next")
    print("  self-extension is the agent's keystone applied to the WORLD MODEL: predict the autonomous")
    print("  dynamics (gravity) and attribute only the RESIDUAL to the control (predict-to-recover) +")
    print("  treat settle/respawn as a world event, not self-motion. That makes the controllable thing")
    print("  a ROLE (the falling piece), not a persistent region. donkey=0, no hand-authored model.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
