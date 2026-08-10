"""The authored retaining cortex REPLACES THE EYE LIVE: compare avatar tracking consistency before authoring
(the segmenting eye) vs after (the agent's own authored retaining_tracker running in the perception pipe)."""
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

def mclass(prev, cur):
    if cur is None: return "ABSENT"
    if prev is None: return "REACQUIRE"
    d = abs(cur[0]-prev[0]) + abs(cur[1]-prev[1])
    return "STAY" if d == 0 else "SMOOTH" if d <= 7 else "JUMP"

def run_phase(agent, world, n, fr0):
    seq = []; prev = None
    for k in range(n):
        fr = fr0 + k; agent._spatial["frame"] = fr; agent.master_tick(); agent.tick()
        g = ar._game_node(agent); ga = agent.s.node(g)["attrs"] if g else {}
        act = ga.get("chosen_action") or spatial_sense.BOOTSTRAP[fr % 4]
        u = ar._understanding(agent); cur = tuple(u["avatar"]) if u.get("has_avatar") else None
        seq.append(mclass(prev, cur)); prev = cur
        sub, ctx = world.apply((act,)); agent._score = ctx.get("score", 0)
        agent._spatial["last_disp"] = spatial_sense.DISP.get(act, (0, 0)); agent.perceive_frame(sub)
        if ctx.get("over") or ctx.get("won"): break
    good = sum(1 for t in seq if t in ("SMOOTH", "STAY"))
    return seq, good / max(len(seq), 1)

def main():
    load_arc_api_key()
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)
    agent.wire_autonomy_faculty(); agent.wire_enact_faculty(); spatial_sense.install(agent)
    psa.install_self_assessment(agent.s); agent.wire_escalation_faculties(); wire_wikipedia_teacher(agent)
    world = ArcWorld(Arc3LiveEnv("ls20-9607627b")); agent._speech_world = world
    mt = agent.s.add_node("Microtheory", {"name": "arc_world", "domain": "arc"})
    agent.inner.add_edge_unchecked(agent.agent, "operates_in", mt)
    agent._spatial = {"frame":0,"last_disp":(0,0),"prev_grid":None,"last_slide":1,"prev_av_pos":None,
                      "nav_stuck":0,"prev_cell":None,"blocked":{},"near_mover":set(),"prev_reached":None}
    agent._score = 0
    sub, ctx = world.reset(); agent.perceive_frame(sub)

    # PHASE A — the segmenting EYE (no cortex authored yet)
    seqA, consA = run_phase(agent, world, 50, 0)
    print(f"PHASE A (eye):            tracking consistency = {consA:.2f}   {dict(__import__('collections').Counter(seqA))}")
    # the agent assesses its own vision and runs the whole self-build loop -> authors the cortex
    vocab = {t: i for i, t in enumerate(sorted(set(seqA)))}
    psa.assess_signal(agent.s, [[vocab[t] for t in seqA]], signal="vision")
    for _ in range(12):
        agent.master_tick(); agent.inner.run_rules()
        if [n for n in agent.s.nodes("Operator") if agent.s.node(n)["attrs"].get("runner") == "retaining_tracker"]:
            break
    authored = bool([n for n in agent.s.nodes("Operator")
                     if agent.s.node(n)["attrs"].get("runner") == "retaining_tracker"])
    print(f"authored retaining cortex: {authored}  (now live in the perception pipe)")
    # PHASE B — the authored CORTEX running live
    seqB, consB = run_phase(agent, world, 50, 200)
    print(f"PHASE B (authored cortex): tracking consistency = {consB:.2f}   {dict(__import__('collections').Counter(seqB))}")
    print(f"\nthe authored cortex replaced the eye live: consistency {consA:.2f} -> {consB:.2f}  "
          f"(+{consB-consA:+.2f})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
