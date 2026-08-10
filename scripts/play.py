"""play — the UNIVERSAL world loop. The world adapter is the only world-specific thing; master_tick does
everything else (see, navigate, understand, escalate). The loop body is:

    perceive_frame(frame) -> master_tick() ; tick() -> read chosen_action -> world.apply(action)

Nothing after the adapter is arc-specific: the spatial sense is a graph reflex (domains/spatial_sense), the nav
is graph rules (seeds/grid_navigation), the understand-drive + order-N escalation are the wired autonomy
faculties. Swap ArcWorld for any other adapter and the same loop drives it.

Run:  PYTHONPATH=runners/dsl/python:. python3 scripts/play.py [game] [actions]
"""
import os, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from _arc3_load_key import load_arc_api_key
from arc3_live_env import Arc3LiveEnv
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import spatial_sense
import scripts.arc_run as ar       # display-only helpers (_understanding/_game_node read graph state)


def main():
    game = sys.argv[1] if len(sys.argv) > 1 else "ls20-9607627b"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    t0 = time.time()

    load_arc_api_key()
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)
    # WIRE the generic faculties master_tick fires; NONE of this is world-specific.
    agent.wire_autonomy_faculty()        # the understand-drive (frontier_pick -> goal -> investigate -> order-N)
    agent.wire_enact_faculty()
    spatial_sense.install(agent)         # the spatial sense, as a reflex master_tick fires
    # the local Wikipedia as the agent's teacher: on a knowledge impasse it learns the concept it lacks
    # (and the order-4 self-extension can author the faculty it needs). The same path it used to learn the
    # visual-cortex concepts now seeded in perception_concepts.json.
    from domains.wiki_teacher import wire_wikipedia_teacher
    if wire_wikipedia_teacher(agent):
        print("wikipedia teacher wired (local snapshot).")
    agent._spatial = {"frame": 0, "last_disp": (0, 0), "prev_grid": None, "last_slide": 1,
                      "prev_av_pos": None, "nav_stuck": 0, "prev_cell": None,
                      "blocked": {}, "near_mover": set(), "prev_reached": None}
    agent._score = 0

    world = ArcWorld(Arc3LiveEnv(game))          # <-- THE ADAPTER: the ONLY world-specific line.
    sub, ctx = world.reset(); agent.perceive_frame(sub)
    print(f"play {game}: START + KEEP TICKING. The agent runs on its OWN clock (ticks != game frames),\n"
          f"decides when to act, and its budget machinery + game-over govern the lifetime.\n")

    # --- domain-independent action->effect seam ------------------------------------------------------
    # The agent's act-by-curiosity is now INTRINSIC (jabberwock_decides_intrinsic_action): the adapter
    # (worlds/arc.py) publishes the interaction affordance repertoire + world_signal as world I/O, and the
    # graph rule world_curiosity.enact_forced_action bridges the babble decision (forced_action) into
    # chosen_action. play.py no longer publishes the repertoire, stamps signals, or assembles actions — it
    # only links the game to the action_effect axis it probes (a graph wiring, not a decision), then reads
    # the action the GRAPH chose. The decision lives in the graph; this loop only translates I/O.
    gnode0 = ar._game_node(agent)
    if gnode0 is not None:
        ax = next((n for n in agent.s.nodes("CapabilityAxis")
                   if agent.s.node(n)["attrs"].get("name") == "action_effect"), None)
        if ax is not None:
            agent.inner.add_edge_unchecked(gnode0, "probes_axis", ax)

    def avatar_seen():
        return any(agent.s.node(x)["attrs"].get("is_avatar") for x in agent.s.nodes("AvatarCandidate"))

    def budget_spent():
        gn = ar._game_node(agent)
        if gn is None or agent.s.node(gn)["attrs"].get("budget_spent") != 1.0:
            return False
        ga = agent.s.node(gn)["attrs"]
        # NOT done while the action->effect question is open: identifying what things ARE is not knowing what
        # acting CAUSES. Keep going until it either FINDS the mechanic or has genuinely tried acting on every
        # feature with no effect. Only then is the curiosity actually spent.
        if ga.get("mechanic_found") == 1.0:            # real progress (the score setpoint moved)
            return True
        if ga.get("lead_active") == 1.0:               # mid re-test of a lead — not done
            return False
        return (ga.get("click_rank") or 0) >= len(agent.s.nodes("Feature"))

    frame = 0          # game frames (one per ACTION the agent emits)
    tick = 0           # the agent's OWN ticks (master_tick) — NOT synchronous with frames
    HARD = 5000        # hard safety ONLY (not a budget): the AGENT declares budget_spent when its curiosity plateaus.
    while tick < HARD and not budget_spent() and not (ctx.get("over") or ctx.get("won")):
        tick += 1
        agent._spatial["frame"] = frame
        agent.master_tick()                      # the agent's clock: see, navigate, be curious, decide
        agent.tick()                             # run_rules: nav + curiosity + autonomy
        gnode = ar._game_node(agent)
        ga0 = agent.s.node(gnode)["attrs"] if gnode else {}
        # Read the action the GRAPH chose. world_curiosity.enact_forced_action has already bridged any
        # babble decision into chosen_action; the nav cortex writes chosen_action too; break_dir is the
        # cortex's oscillation-break. The host only READS — it no longer assembles or decides.
        action = (ga0.get("chosen_action") or ga0.get("break_dir")
                  or (agent.s.node(agent.agent)["attrs"].get("chosen_action") or ""))
        if not action:
            if not avatar_seen():
                action = spatial_sense.BOOTSTRAP[frame % 4]   # act to perceive (it hasn't seen the avatar yet)
            else:
                continue                         # the agent ticked WITHOUT acting yet — keep thinking (async)
        # the agent DECIDED to act -> spend one game frame; budget machinery accounts for it.
        sub, ctx = world.apply((action,))
        agent._score = ctx.get("score", 0)
        agent._spatial["last_disp"] = spatial_sense.DISP.get(action, (0, 0))
        agent.perceive_frame(sub)
        frame += 1
        # world_signal / score / last_action are now stamped by the ADAPTER (worlds/arc.py build_world)
        # as world I/O — the agent's curiosity reads its SURPRISE off them. Nothing to publish here.
        u = ar._understanding(agent)
        ga = agent.s.node(gnode)["attrs"] if gnode else {}
        mode = ga.get("nav_mode") or "—"
        plateau = int(ga.get("plateau") or 0)
        # collapse efficiency: features explained, how many were PROBED directly vs COLLAPSED by leverage,
        # and the total probe effort spent. Maximum collapse (explained) for minimum effort (probes).
        feats = [agent.s.node(f)["attrs"] for f in agent.s.nodes("Feature")]
        explained = sum(1 for a in feats if a.get("resolved") == 1.0)
        # action->effect: which interaction actions has it tried, did it find a transition?
        tried = [agent.s.node(a)["attrs"].get("name") for a in agent.s.nodes("Action")
                 if agent.s.node(a)["attrs"].get("tried") == 1.0]
        mech = ga.get("effective_action") if ga.get("mechanic_found") == 1.0 else None
        lead = ga.get("lead_action") if ga.get("lead_active") == 1.0 else None
        inh = int(ga.get("leads_inhibited") or 0)
        surprise = ga.get("outcome_delta")
        if frame % 5 == 0 or lead or budget_spent() or mech:
            if mech:
                eff = f"PROGRESS via {mech} (score moved)!"
            elif lead:
                eff = f"re-testing lead={lead} (try {int(ga.get('lead_tries') or 0)}/3, surprise {ga.get('lead_surprise'):.0f})"
            else:
                eff = f"searching ({inh} dead leads inhibited) surprise={surprise:+.0f}" if surprise is not None else "searching"
            print(f"  tick{tick:3} f{frame:3} {str(action)[:13]:13s} "
                  f"{('av@'+str(u['avatar'])) if u['has_avatar'] else 'no-av':13s} | "
                  f"act->effect: {eff} | score={agent._score}", flush=True)
        if ctx.get("over") or ctx.get("won"):
            print("  game", "WON" if ctx.get("won") else "OVER"); break

    why = ("the AGENT declared its budget spent (curiosity plateaued)" if budget_spent()
           else "game over" if (ctx.get("over") or ctx.get("won")) else "hard safety cap")
    print(f"\ndone: {tick} ticks, {frame} frames, {time.time()-t0:.1f}s — stopped because {why}. "
          f"(no clock, no fixed cap: the budget was self-defined.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
