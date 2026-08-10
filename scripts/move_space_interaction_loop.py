"""MOVE-SPACE INTERACTION-FRONTIER LOOP — recognise -> frontier -> learn, for the ls20 move-space.

The same loop the comprehension pivot closed, applied to the planner: when the move-space planner recognises a
CLOSED chamber (movement exhausted) it mints a Hypothesis{need_non_movement_affordance} — a FRONTIER. The agent
then INVESTIGATES it by trying its non-movement (interaction) affordances and LEARNS which one changes the
world: the interaction that makes a previously-dead move yield a NEW configuration is the opener; the move-space
REOPENS. recognise (closed) -> frontier (an interaction is needed) -> investigate (try interactions) -> learn
(the opener) -> reopened. donkey=0, controlled slider sim.

This is predict->surprise->learn at the move-space level: the agent's prior is "an interaction does nothing";
the opener SURPRISES (a door opens, a new config appears) and that surprise is the lesson.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/move_space_interaction_loop.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from move_space_planner import MoveSpacePlanner

DIRS = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}
A, B, C, D, E = (0, 0), (0, 5), (5, 0), (5, 5), (10, 5)   # 4 chamber corners + a door config E behind D


class SliderSim:
    """A 5-slider in a closed chamber (4 corners). A DOOR below D opens only after the 'push' interaction —
    then Down from D slides to a NEW config E. select/wait do nothing. The agent cannot see door_open; it only
    perceives where a press lands."""
    def __init__(self):
        self.door_open = False

    def slide(self, pos, action):                        # movement affordance -> the rest pose it lands on
        if action == "Down" and pos == D:
            return E if self.door_open else D            # the dead move that the opener enables
        table = {
            A: {"Right": B, "Down": C}, B: {"Left": A, "Down": D},
            C: {"Up": A, "Right": D}, D: {"Up": B, "Left": C},
            E: {"Up": D},
        }
        return table.get(pos, {}).get(action, pos)       # unl­isted = slide into a wall (no-op)

    def interact(self, interaction):                     # non-movement affordance
        if interaction == "push":
            self.door_open = True
            return True
        return False


def _build_move_space(pl, sim):
    """Learn the move-space by observing every affordance from every reachable stop (the agent acting)."""
    seen, work = {A}, [A]
    while work:
        cur = work.pop()
        for act in DIRS:
            nxt = sim.slide(cur, act)
            pl.observe(cur, act, nxt)
            if nxt != cur and nxt not in seen:
                seen.add(nxt); work.append(nxt)
    return seen


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    print("=" * 94)
    print("MOVE-SPACE INTERACTION-FRONTIER LOOP — recognise CLOSED -> frontier -> learn the opener -> reopen")
    print("=" * 94)

    sim = SliderSim()
    pl = MoveSpacePlanner(a, list(DIRS.keys()))
    seen = _build_move_space(pl, sim)
    pl.set_current(A)
    act, mode = pl.plan()
    closed = a.s.node(pl.p)["attrs"].get("closed") == 1.0
    hyp = next(iter(a.inner.neighbours(pl.p, "minted")), None)
    kind = a.s.node(hyp)["attrs"].get("kind") if hyp else None
    print(f"\n  built the move-space: {len(seen)} stops {sorted(seen)}")
    print(f"  RECOGNISE: plan -> mode={mode!r}, closed={closed}; minted FRONTIER hypothesis = {kind!r}")

    # INVESTIGATE the interaction frontier: try each non-movement affordance; the opener makes a dead move
    # yield a NEW config (the surprise). The agent picks what to try; the sim is the world.
    print("\n  INVESTIGATE the frontier (try interactions; learn the one that changes the move-space):")
    learned, before = None, set(pl.by_key)
    for interaction in ["select", "wait", "push"]:
        sim.interact(interaction)
        new_config = None
        for cfg in list(seen):                           # re-act + perceive: did a dead move open up?
            for act2 in DIRS:
                nxt = sim.slide(cfg, act2)
                key = tuple(float(x) for x in nxt)
                if nxt != cfg and key not in pl.by_key:
                    pl.observe(cfg, act2, nxt); seen.add(nxt); new_config = nxt
        if new_config:
            learned = interaction
            print(f"    tried {interaction!r:8} -> SURPRISE: a new stop {new_config} opened up -> LEARNED opener")
            break
        print(f"    tried {interaction!r:8} -> no change (the move-space is unchanged)")

    pl.set_current(D)
    act2, mode2 = pl.plan()                               # the move-space reopened?
    reopened = mode2 != "closed"
    print(f"\n  REOPENED: plan from D -> mode={mode2!r} (action {act2!r}); the agent can move again "
          f"({len(pl.by_key)} stops now)")

    print("\n" + "=" * 94)
    print(f"  donkey (LLM calls): {donkey['n']}")
    ok = closed and kind == "need_non_movement_affordance" and learned == "push" and reopened
    print(f"  {'PASS' if ok else 'FAIL'} — the planner RECOGNISED the closed chamber and minted the interaction")
    print("  FRONTIER; the agent INVESTIGATED it (tried interactions), LEARNED that 'push' opens the way (the")
    print("  surprise: a dead move now yields a new stop), and the move-space REOPENED. recognise -> frontier")
    print("  -> learn, the same loop the comprehension pivot closed, now driving the ls20 move-space. donkey=0.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
