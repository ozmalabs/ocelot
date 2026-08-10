"""The jabberwock plays ls20 and DIAGNOSES ITSELF through its own faculties: its perception self-assessment
(is what I see predictable?) and its action-correlation as a MOTOR prediction-error (does the body move as my
action predicts?). The verdicts are the agent's own measures, not mine."""
import os, sys
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from _arc3_load_key import load_arc_api_key
from arc3_live_env import Arc3LiveEnv
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import spatial_sense, perception_self_assessment as psa
import scripts.arc_run as ar

def mclass(prev, cur):
    if cur is None: return "ABSENT"
    if prev is None: return "REACQUIRE"
    d = abs(cur[0]-prev[0]) + abs(cur[1]-prev[1])
    return "STAY" if d == 0 else "SMOOTH" if d <= 7 else "JUMP"

def main():
    load_arc_api_key()
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)
    agent.wire_autonomy_faculty(); agent.wire_enact_faculty(); spatial_sense.install(agent)
    psa.install_self_assessment(agent.s)
    agent._spatial = {"frame":0,"last_disp":(0,0),"prev_grid":None,"last_slide":1,"prev_av_pos":None,
                      "nav_stuck":0,"prev_cell":None,"blocked":{},"near_mover":set(),"prev_reached":None}
    agent._score = 0
    world = ArcWorld(Arc3LiveEnv("ls20-9607627b")); sub,ctx=world.reset(); agent.perceive_frame(sub)
    vision=[]; prev=None; moved=matched=0; visited=set()
    for fr in range(90):
        agent._spatial["frame"]=fr; agent.master_tick(); agent.tick()
        g=ar._game_node(agent); ga=agent.s.node(g)["attrs"] if g else {}
        act = ga.get("chosen_action") or spatial_sense.BOOTSTRAP[fr%4]
        pred = spatial_sense.DISP.get(act,(0,0))
        sub,ctx=world.apply((act,)); agent._score=ctx.get("score",0)
        agent._spatial["last_disp"]=pred; agent.perceive_frame(sub)
        u=ar._understanding(agent); cur=tuple(u["avatar"]) if u.get("has_avatar") else None
        vision.append(mclass(prev,cur))
        if prev and cur and cur!=prev:   # the body MOVED — did it move as my action predicted?
            moved += 1
            obs=(cur[0]-prev[0], cur[1]-prev[1])
            if abs(obs[0]-pred[0])+abs(obs[1]-pred[1]) <= 3: matched += 1
        if cur: visited.add(cur)
        prev=cur
        if ctx.get("over") or ctx.get("won"): break
    # the agent's OWN faculties produce the verdicts
    vocab={t:i for i,t in enumerate(sorted(set(vision)))}
    psa.assess_signal(agent.s, [[vocab[t] for t in vision]], signal="vision")
    for _ in range(8): agent.inner.run_rules()
    vroot=[agent.s.node(n)["attrs"] for n in agent.s.nodes("PerceptionSelfRoot") if agent.s.node(n)["attrs"].get("signal")=="vision"]
    vverdict = vroot[0].get("frontier") if vroot else "?"
    motor_match = matched/max(moved,1)
    print("== THE JABBERWOCK'S SELF-DIAGNOSIS OF ITS ls20 PLAY ==")
    print(f"  vision (my perception self-assessment): frontier={vverdict!r}  stream={dict(Counter(vision))}")
    print(f"  motor (does the body move as my action PREDICTS?): match-rate = {motor_match:.0%}  ({matched}/{moved} moves)")
    print(f"  coverage: {len(visited)} distinct cells   score: {agent._score}")
    print("  -- the agent's conclusion --")
    if motor_match < 0.5:
        print(f"  MY MOTOR MODEL IS WRONG: I move as my action predicts only {motor_match:.0%} of the time —")
        print("  I press a direction and the body goes elsewhere. I cannot navigate on a kinematics I mis-predict.")
    if vverdict == "perception":
        print("  MY VISION IS UNRELIABLE: my perceived units are not predictable (flagged perception).")
    if motor_match >= 0.5 and vverdict != "perception":
        print("  perception + motor look ok; the limit is elsewhere (coverage/exploration).")
    return 0

if __name__ == "__main__":
    sys.exit(main())
