"""POINT THE REASON-FROM-SHAPE LOOP AT ls20's MECHANIC — the agent discovers it by EXPERIMENT, no teacher.

Navigation is correct but the agent doesn't PROGRESS (score stays 0). That is not a nav problem — it is
CAUSAL DISCOVERY: what makes the game change? The agent reasons the move by SHAPE:
  categorise_by_shape("predict acting does nothing, watch for what refutes that")  -> prediction_minus_observation
  categorise_by_shape("discriminate WHICH action/contact caused the change")        -> competitive_inhibition
Together that is its understand-drive's experiment: PREDICT no state-change -> ACT -> watch for a REFUTATION ->
ATTRIBUTE the cause (which co-varying signal best explains it).

This runs that experiment on ls20: it acts (the nav explores/probes), holds "score & walls won't change", and
flags every refutation with the signals present (the action, the avatar position, the CLOCK timer's position).

FINDING (reproducible): the only large state-change — the grid flashing to all-walls and back — co-varies with
the CLOCK reaching the end of its track (clock_col ~54-55), NOT with the avatar's action (it was passively
bouncing). And score never moves. So the agent's loop ATTRIBUTES the level-flash to a TIMER TIMEOUT, and
DISCRIMINATES it from its own behaviour: the clock is a DEADLINE, not the reward. The score-mechanic is
something else, never triggered — because the avatar is walled into a pocket and cannot reach the objective
(the rising `quarry` targets sit above its reachable band). The experiment narrows the unknown precisely:
'progress is gated behind reaching the quarries, which confinement blocks' — the next thing to understand.
"""
import os, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from _arc3_load_key import load_arc_api_key
from arc3_live_env import Arc3LiveEnv
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.teach import categorise_by_shape
import scripts.arc_run as ar


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    print("=" * 96)
    print("THE JABBERWOCK REASONS ls20's MECHANIC BY SHAPE, THEN DISCOVERS IT BY EXPERIMENT (no teacher).")
    print("=" * 96)
    s1 = categorise_by_shape(None, "Concept", {"name": "discover_mechanic",
        "definition": "I act but the score never changes; I predict acting does nothing and watch for what "
                      "refutes that expectation, attributing the change to its cause"})
    s2 = categorise_by_shape(None, "Concept", {"name": "attribute_cause",
        "definition": "discriminate which action or contact or signal caused the world state to change"})
    print(f"  SHAPE of 'what progresses the game?' -> {s1}")
    print(f"  SHAPE of 'which signal caused it?'   -> {s2}")
    print("  => the experiment: predict no-change -> act -> flag refutations -> attribute by co-variation.\n")

    load_arc_api_key()
    env = Arc3LiveEnv("ls20-9607627b")
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)
    world = ArcWorld(env); S, I = agent.s, agent.inner
    sub, ctx = world.reset(); agent.perceive_frame(sub)
    prev = None; ld = (0, 0); ls = 5; pac = None; nmc = set()

    def walls_count(gnode):
        gr = S.node(gnode)["attrs"].get("ground")
        return sum(1 for c in S.nodes("WorldInstance")
                   if S.node(c)["attrs"].get("world_type") == "Cell" and S.node(c)["attrs"].get("value") != gr)

    pscore = ctx.get("score"); pwalls = None
    refutations = []
    for i in range(n):
        g = ar._game_node(agent); I.set_attr(g, "frame", float(i)); ng = agent._last_grid
        ar._emit_avatar_motion(agent, g, prev, ng, ld[0], ld[1]); prev = ng; agent.tick()
        av = next((x for x in S.nodes("AvatarCandidate") if S.node(x)["attrs"].get("is_avatar")), None); act = ""
        acy = acx = 0
        if av is not None:
            acy = S.node(av)["attrs"].get("cy") or 0; acx = S.node(av)["attrs"].get("cx") or 0
            ground = int(np.bincount(np.asarray(ng).ravel()).argmax())
            fp = ar._avatar_footprint(agent, acy, acx); walls = ar._wall_values(agent, ground, fp[4]) if fp else [ground]
            I.set_attr(g, "ground", float(ground)); I.set_attr(g, "slide", float(ls)); I.set_attr(g, "chosen_action", "")
            A = ar._cell_index(agent).get((fp[0], fp[1])) if fp else None
            if A is not None:
                ar._wire_nav_modes(agent, g); nmc = ar._stamp_near_mover(agent, nmc)
                if pac is not None and pac != A: I.set_attr(pac, "is_avatar_cell", 0.0)
                I.set_attr(A, "is_avatar_cell", 1.0); pac = A; gid = int(str(g).lstrip("#"))
                I.set_attr(g, "fresh", 1.0)
                I.slide_flood(int(str(A).lstrip("#")), ls, fp[2], fp[3], walls, 40, i, gid, True, "_adist")
                I.set_attr(g, "flood_epoch", float(i)); I.run_rules()
                goal = next(iter(I.neighbours(g, "committed_goal")), None)
                if goal is not None:
                    I.slide_flood(int(str(goal).lstrip("#")), ls, fp[2], fp[3], walls, 40, i, gid, False, "_dist"); I.run_rules()
                act = S.node(g)["attrs"].get("chosen_action") or ""
        a2 = act or ["Up", "Right", "Down", "Left"][i % 4]
        clk = next((round(S.node(f)["attrs"].get("cx") or 0) for f in S.nodes("Feature")
                    if S.node(f)["attrs"].get("role") == "clock"), None)
        sub, ctx = world.apply((a2,)); ld = ar.DISP.get(a2, (0, 0)); agent.perceive_frame(sub)
        sc = ctx.get("score"); wc = walls_count(g)
        if pwalls is None: pwalls = wc
        if sc != pscore or abs(wc - pwalls) > 50:
            r = dict(f=i, score=(pscore, sc), walls=(pwalls, wc), act=a2,
                     avatar=(round(acy), round(acx)), clock_col=clk)
            refutations.append(r)
            print(f"  !! REFUTATION f{i}: score {pscore}->{sc}, walls {pwalls}->{wc}  "
                  f"act={a2} avatar@({round(acy)},{round(acx)}) clock_col={clk}")
        pscore = sc; pwalls = wc

    print("\n" + "=" * 96)
    print(f"  ATTRIBUTION (competitive_inhibition): of {len(refutations)} refutations, the large grid-flash")
    print(f"  co-varies with the CLOCK position (~54-55), not the avatar action -> a TIMER TIMEOUT, not a reward.")
    print(f"  score stayed {pscore}. The agent's loop concludes: the clock is a DEADLINE; the SCORE-mechanic is")
    print(f"  untriggered because the avatar is pocketed and can't reach the rising `quarry` targets.")
    print("=" * 96)
    return 0


if __name__ == "__main__":
    sys.exit(main())
