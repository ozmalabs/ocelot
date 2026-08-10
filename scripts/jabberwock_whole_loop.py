"""The WHOLE loop, no nudge: the jabberwock feels its sight fail, names the gap, routes itself to authoring,
and authors its retaining visual cortex — start to finish on its own. Only the bootstrap is wired."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from _arc3_load_key import load_arc_api_key
from arc3_live_env import Arc3LiveEnv
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import spatial_sense
from domains import perception_self_assessment as psa
from domains.wiki_teacher import wire_wikipedia_teacher
import scripts.arc_run as ar

def motion_class(prev, cur):
    if cur is None: return "ABSENT"
    if prev is None: return "REACQUIRE"
    d = abs(cur[0]-prev[0]) + abs(cur[1]-prev[1])
    return "STAY" if d == 0 else "SMOOTH" if d <= 7 else "JUMP"

def main():
    load_arc_api_key()
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)
    agent.wire_autonomy_faculty(); agent.wire_enact_faculty(); spatial_sense.install(agent)
    psa.install_self_assessment(agent.s); agent.wire_escalation_faculties(); wire_wikipedia_teacher(agent)
    arc_world = ArcWorld(Arc3LiveEnv("ls20-9607627b")); agent._speech_world = arc_world
    mt = agent.s.add_node("Microtheory", {"name": "arc_world", "domain": "arc"})
    agent.inner.add_edge_unchecked(agent.agent, "operates_in", mt)
    agent._spatial = {"frame":0,"last_disp":(0,0),"prev_grid":None,"last_slide":1,"prev_av_pos":None,
                      "nav_stuck":0,"prev_cell":None,"blocked":{},"near_mover":set(),"prev_reached":None}
    agent._score = 0
    sub, ctx = arc_world.reset(); agent.perceive_frame(sub)
    stream = []; prev = None
    for fr in range(60):
        agent._spatial["frame"] = fr; agent.master_tick(); agent.tick()
        g = ar._game_node(agent); ga = agent.s.node(g)["attrs"] if g else {}
        act = ga.get("chosen_action") or spatial_sense.BOOTSTRAP[fr % 4]
        u = ar._understanding(agent); cur = tuple(u["avatar"]) if u.get("has_avatar") else None
        stream.append(motion_class(prev, cur)); prev = cur
        sub, ctx = arc_world.apply((act,)); agent._score = ctx.get("score", 0)
        agent._spatial["last_disp"] = spatial_sense.DISP.get(act, (0, 0)); agent.perceive_frame(sub)
        if ctx.get("over") or ctx.get("won"): break
    vocab = {t: i for i, t in enumerate(sorted(set(stream)))}
    psa.assess_signal(agent.s, [[vocab[t] for t in stream]], signal="vision")
    # DRIVE — no manual impasse, no manual needs_tool. master_tick does it all.
    for step in range(12):
        agent.master_tick(); agent.inner.run_rules()
        if [n for n in agent.s.nodes("Operator")
                if agent.s.node(n)["attrs"].get("authored_by_escalation") == 1.0]:
            break
    vax = next((n for n in agent.s.nodes("CapabilityAxis")
                if agent.s.node(n)["attrs"].get("signal") == "vision"
                and agent.s.node(n)["attrs"].get("origin") == "perception_self_assessment:units_failing"), None)
    minted = vax is not None
    tool_impasses = [agent.s.node(m)["attrs"] for m in (agent.inner.neighbours(vax, "has_tool_impasse") if vax else [])]
    routed_by_rule = any("no faculty to address it" in str(a.get("why", "")) for a in tool_impasses)
    authored = [agent.s.node(n)["attrs"] for n in agent.s.nodes("Operator")
                if agent.s.node(n)["attrs"].get("authored_by_escalation") == 1.0]
    bound = vax is not None and any(
        n in agent.inner.neighbours(vax, "investigated_by") for n in agent.s.nodes("Operator")
        if agent.s.node(n)["attrs"].get("authored_by_escalation") == 1.0)
    print(f"  1. MINTED its own vision axis:                     {minted}")
    print(f"  2. ROUTED it to authoring (by the RULE, no nudge): {routed_by_rule}")
    print(f"  3. AUTHORED + bound the retaining cortex:          {bool(authored)} "
          f"({authored[0].get('name') if authored else None}, bound={bound})")
    ok = minted and routed_by_rule and bool(authored) and bound
    print(f"\nWHOLE LOOP ran with zero nudge: {ok}")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
