"""The jabberwock assesses its OWN vision and mints its own vision gap — bridging the last seam.

It already has: the concepts (learned from Wikipedia), the shapes (delayed_persistence / associative_recall /
prediction_minus_observation), the Wikipedia teacher, and the now-signal-agnostic perception self-assessment
(assess_signal + install_self_assessment, which mints a CapabilityAxis from felt shortfall). The only missing
seam is the VISUAL READOUT: turning its perceived visual stream into ordered unit-ids, the way read_unit_sequences
does for speech. The readout here is mechanical perception (like the eye firing): per frame, the avatar's
perceived motion-class — ABSENT (object permanence broke: it vanished), STAY, SMOOTH (moved ~one slide), or
JUMP (the tracker leapt). Good vision => a predictable stream of SMOOTH/STAY; the verified ls20 eye drops and
jumps the avatar => an UNPREDICTABLE stream => the agent FEELS its sight is poor and mints its own vision axis.
No axis handed in; the maths/decision are the agent's own generalized faculty.
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
import scripts.arc_run as ar

def motion_class(prev, cur):
    if cur is None: return "ABSENT"                    # object permanence broke — it vanished
    if prev is None: return "REACQUIRE"
    d = abs(cur[0]-prev[0]) + abs(cur[1]-prev[1])
    return "STAY" if d == 0 else "SMOOTH" if d <= 7 else "JUMP"

def main():
    load_arc_api_key()
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)
    agent.wire_autonomy_faculty(); agent.wire_enact_faculty(); spatial_sense.install(agent)
    psa.install_self_assessment(agent.s)               # the agent's own gap-minting loop, per signal
    agent._spatial = {"frame":0,"last_disp":(0,0),"prev_grid":None,"last_slide":1,"prev_av_pos":None,
                      "nav_stuck":0,"prev_cell":None,"blocked":{},"near_mover":set(),"prev_reached":None}
    agent._score = 0
    world = ArcWorld(Arc3LiveEnv("ls20-9607627b")); sub,ctx = world.reset(); agent.perceive_frame(sub)
    # READ OUT the visual unit-stream over ~60 frames (mechanical perception)
    stream = []; prev = None
    for fr in range(60):
        agent._spatial["frame"] = fr
        agent.master_tick(); agent.tick()
        g = ar._game_node(agent); ga = agent.s.node(g)["attrs"] if g else {}
        act = ga.get("chosen_action") or spatial_sense.BOOTSTRAP[fr % 4]
        u = ar._understanding(agent); cur = tuple(u["avatar"]) if u.get("has_avatar") else None
        stream.append(motion_class(prev, cur)); prev = cur
        sub,ctx = world.apply((act,)); agent._score = ctx.get("score",0)
        agent._spatial["last_disp"] = spatial_sense.DISP.get(act,(0,0)); agent.perceive_frame(sub)
        if ctx.get("over") or ctx.get("won"): break
    from collections import Counter
    print("vision unit-stream over", len(stream), "frames:", dict(Counter(stream)))
    # map tokens -> ids and ASSESS — the agent's own faculty judges predictability + mints the gap
    vocab = {t:i for i,t in enumerate(sorted(set(stream)))}
    seqs = [[vocab[t] for t in stream]]
    psa.assess_signal(agent.s, seqs, signal="vision")
    for _ in range(8): agent.inner.run_rules()
    # what did the agent conclude about its OWN sight?
    vroot = [agent.s.node(n)["attrs"] for n in agent.s.nodes("PerceptionSelfRoot")
             if agent.s.node(n)["attrs"].get("signal") == "vision"]
    if vroot:
        r = vroot[0]
        print(f"agent's verdict on its VISION: frontier={r.get('frontier')!r} reliability={r.get('reliability')!r} "
              f"predict_over_freq={r.get('predict_over_freq'):.2f} compress={r.get('compress_ratio'):.2f}")
    minted = [agent.s.node(n)["attrs"] for n in agent.s.nodes("CapabilityAxis")
              if agent.s.node(n)["attrs"].get("signal") == "vision"
              and agent.s.node(n)["attrs"].get("origin") == "perception_self_assessment:units_failing"]
    print(f"vision CapabilityAxis the JABBERWOCK minted itself: {len(minted)}")
    for m in minted[:1]:
        print("   gap:", (m.get("gap_text") or "")[:80])
        print("   capability_keys:", m.get("capability_keys"))
    return 0

if __name__ == "__main__":
    sys.exit(main())
