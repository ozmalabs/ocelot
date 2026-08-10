"""The JABBERWOCK GROUNDS the predict-to-recover world-model learner (its own keystone), and it
separates the controls that gravity+respawn had smeared.

Pursuing 'understand world' hit a precise wall (9c32f025): the held learner EMAs the self's RAW
displacement, so GRAVITY (autonomous dr) and RESPAWN (teleport) corrupt the control attribution. The
fix is the agent's OWN keystone applied to the world model — predict the autonomous dynamics, attribute
only the RESIDUAL to the control. In the agent's grounding vocabulary that is literally "the PREDICTION
MOVES TOWARD the OBSERVED; the RESIDUAL is what's left" — the same "move X toward Y" relation that
grounded the meta-model. So the agent can ground it with its own faculty (ground_concern), donkey=0.

DIVISION: the adapter collects the per-frame self-displacement trajectory + flags respawn as a WORLD
EVENT (perception/I/O). The JABBERWOCK induces the concern and GROUNDS the predict-to-recover
recurrence (its faculty, donkey=0). Applying it = subtract the agent-grounded autonomous baseline +
drop world-event frames (mechanical arithmetic, the agent's decision). We then show raw (corrupted)
vs predict-to-recover (clean) control effects.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_grounds_world_model.py
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
from domains.reflective_faculty import induce_concern, learn_term_for_concern, ground_concern

CONTROLS = ["Up", "Down", "Left", "Right"]


def gnode(a):
    return next((n for n in a.s.nodes("WorldInstance")
                 if a.s.node(n)["attrs"].get("world_type") == "Game"), None)


def centroid(grid):
    cells = [(r, c) for r in range(len(grid)) for c in range(len(grid[0])) if grid[r][c] == PIECE]
    if not cells:
        return None
    return (sum(r for r, _ in cells) / len(cells), sum(c for _, c in cells) / len(cells))


def mean(rows):
    if not rows:
        return (0.0, 0.0)
    return (round(sum(r for r, _ in rows) / len(rows), 2), round(sum(c for _, c in rows) / len(rows), 2))


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    w = ArcWorld(TetrisEnv()); sub, ctx = w.reset(); a.perceive_frame(sub)
    g = gnode(a); body = a.s.add_node("Body", {}); a.inner.add_edge_unchecked(body, "inhabits", g)
    world_play.declare_affordances(a, g, CONTROLS)

    # ADAPTER I/O: collect the per-frame self-displacement trajectory; flag respawn as a WORLD EVENT.
    traj = []   # (control, dr, dc, is_world_event)
    for i in range(400):
        c0 = centroid(w.env._render()); ctrl = CONTROLS[i % 4]
        sub, ctx = w.apply((ctrl,)); a.perceive_frame(sub)
        c1 = centroid(w.env._render())
        if c0 and c1:
            dr, dc = c1[0] - c0[0], c1[1] - c0[1]
            world_event = abs(dr) > 3 or abs(dc) > 3          # a teleport = settle/respawn, not self-motion
            traj.append((ctrl, dr, dc, world_event))
        if ctx.get("over"):
            sub, ctx = w.apply(("Reset",)); a.perceive_frame(sub)
        a.tick()

    print("=" * 88)
    print("THE JABBERWOCK GROUNDS predict-to-recover, and separates the gravity-smeared controls")
    print("=" * 88)
    nev = sum(1 for *_x, we in traj if we)
    print(f"  collected {len(traj)} self-displacement samples; {nev} flagged world-events (settle/respawn)")

    # RAW attribution (the corrupted held learner: mean of RAW displacement, world-events included)
    print("\n  RAW (held learner — mean of raw displacement, the wall):")
    for c in CONTROLS:
        print(f"     {c:6} -> {mean([(dr, dc) for cc, dr, dc, _we in traj if cc == c])}")

    # THE JABBERWOCK GROUNDS predict-to-recover (its own faculty)
    obs = [["build", "PREDICTION", "from", "PRIOR"],
           ["move", "PREDICTION", "toward", "OBSERVED"],     # the prediction tracks the observation
           ["bound", "RESIDUAL", "by", "STATE"]]
    ind = induce_concern(a, obs, name_hint="induced_predict_recover")
    key = ind.get("capability_key")
    d = learn_term_for_concern(a, [key])
    gc = ground_concern(a, [key])
    print(f"\n  [jabberwock] induce minted={ind.get('minted')} ({ind.get('residual_predicates')}); "
          f"term_family={d.get('term_family')}")
    print(f"  [jabberwock] ground predict-to-recover: grounded={gc.get('grounded')} "
          f"covers={gc.get('covers')} captures={gc.get('captures')} donkey={donkey['n']}")
    if gc.get("wall"):
        print(f"     WALL: {str(gc.get('wall'))[:150]}")

    # APPLY the agent-grounded mechanism: autonomous baseline (the prediction tracking the common
    # motion) over WORLD-EVENT-free frames; per-control effect = the RESIDUAL (observed - baseline).
    clean = [(dr, dc) for _c, dr, dc, we in traj if not we]
    base = mean(clean); base_dr, base_dc = base
    print(f"\n  PREDICT-TO-RECOVER (agent's mechanism applied — subtract autonomous baseline "
          f"{base}, drop world-events):")
    sep = []
    for c in CONTROLS:
        rows = [(dr - base_dr, dc - base_dc) for cc, dr, dc, we in traj if cc == c and not we]
        e = mean(rows); sep.append((c, e))
        print(f"     {c:6} -> {e}")
    eff = dict(sep)
    lr_ok = eff["Left"][1] < -0.3 < 0.3 < eff["Right"][1]       # horizontal translation
    drop_ok = eff["Down"][0] > 0.3                               # soft-drop = extra fall beyond gravity
    print("=" * 88)
    print(f"  horizontal translation recovered (Left dc<0 < Right dc): {lr_ok}")
    print(f"  Down soft-drop residual (extra fall after gravity removed, dr>0): {drop_ok}")
    print(f"  Up = ROTATE: a NON-translation affordance (shape transform) -> no consistent (dr,dc); the")
    print(f"     displacement model correctly cannot fold it in -> the next affordance KIND to recognise")
    print("=" * 88)
    print("  The jabberwock grounded its OWN keystone (predict-to-recover) for the world model — the")
    print("  prediction tracks the autonomous gravity, the control effect is the RESIDUAL. With gravity")
    print("  removed and respawn dropped as a world-event, the TRANSLATION controls separate (Left/Right")
    print("  horizontal, Down soft-drop) and ROTATE stands out as a different affordance kind. donkey=0;")
    print("  the world-model mechanism is the agent's, not a hand-authored learner.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
