"""Run the climb: the jabberwock authors its OWN retaining visual cortex end-to-end.

Wiring (the bootstrap): autonomy + enact + self-assessment + escalation faculties + the Wikipedia teacher +
the ARC WORLD as the investigation handle (so order-4 self-extension calls ArcWorld.author_faculty) + the agent
operates_in the arc world. Then: the agent reads its own ls20 vision -> assess_signal mints its OWN vision
CapabilityAxis -> the order-4 routing (needs_tool, the rung the ladder produces) -> _self_extend_reflex calls
ArcWorld.author_faculty -> authors the retaining_tracker (value-preserving translation) -> binds it to the axis.
The authoring decision + the effect-gated faculty are the agent's; we only lay the wire.
"""
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
    psa.install_self_assessment(agent.s)
    agent.wire_escalation_faculties()
    wire_wikipedia_teacher(agent)
    arc_world = ArcWorld(Arc3LiveEnv("ls20-9607627b"))
    agent._speech_world = arc_world                      # the investigation handle order-4 consults
    mt = agent.s.add_node("Microtheory", {"name": "arc_world", "domain": "arc"})
    agent.inner.add_edge_unchecked(agent.agent, "operates_in", mt)
    agent._spatial = {"frame":0,"last_disp":(0,0),"prev_grid":None,"last_slide":1,"prev_av_pos":None,
                      "nav_stuck":0,"prev_cell":None,"blocked":{},"near_mover":set(),"prev_reached":None}
    agent._score = 0

    # 1. the agent reads its OWN ls20 vision and mints its OWN vision axis
    sub, ctx = arc_world.reset(); agent.perceive_frame(sub)
    stream = []; prev = None
    for fr in range(40):
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
    for _ in range(8): agent.inner.run_rules()
    vax = next((n for n in agent.s.nodes("CapabilityAxis")
                if agent.s.node(n)["attrs"].get("signal") == "vision"
                and agent.s.node(n)["attrs"].get("origin") == "perception_self_assessment:units_failing"), None)
    print("1. vision axis the agent MINTED:", vax is not None,
          "| keys:", agent.s.node(vax)["attrs"].get("capability_keys") if vax else None)
    if vax is None: return 1

    # 2. the order-4 routing (needs_tool) -> the climb reaches authoring for this no-operator axis
    mi = agent.s.add_node("Impasse", {"resolved": False, "kind": "escalation", "order": 4, "acted_order": 4})
    agent.inner.add_edge_unchecked(mi, "about_axis", vax)
    agent.inner.add_edge_unchecked(mi, "needs_tool", vax)

    before = [agent.s.node(n)["attrs"].get("name") for n in agent.s.nodes("Operator")
              if agent.s.node(n)["attrs"].get("authored_by_escalation") == 1.0]
    # 3. RUN the climb: the self-extend reflex authors via ArcWorld.author_faculty
    agent.master_tick()
    after = [(n, agent.s.node(n)["attrs"]) for n in agent.s.nodes("Operator")
             if agent.s.node(n)["attrs"].get("authored_by_escalation") == 1.0]
    print(f"2. self-authored operators: {len(before)} -> {len(after)}")
    for nid, a in after:
        bound = vax in agent.inner.neighbours(vax, "investigated_by") or \
                nid in agent.inner.neighbours(vax, "investigated_by")
        print(f"   AUTHORED: {a.get('name')!r}  runner={a.get('runner')!r}  approach={a.get('approach')!r}")
        print(f"   bound to the vision axis (investigated_by): "
              f"{nid in agent.inner.neighbours(vax, 'investigated_by')}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
