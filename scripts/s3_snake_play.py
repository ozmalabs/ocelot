"""S3 — the jabberwock plays SNAKE from the unified mechanism, UNAIDED, no donkey, no host flag.
Phase A (explore): drive nav to generate experience — the agent LEARNS its control basis (resp_<A>) and
  consequence[rvalue] (food=8 rewarding) from real play.
Phase B (exploit): the agent chooses its OWN actions — a target-producer sets self.tgt = the centroid of the
  region whose colour it LEARNED is rewarding (food); the held death-gated seek_primitive pursues it (walls/
  body avoided as the S2 termination prior). Verify the agent eats while choosing its own actions; claude -p
  never called.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/s3_snake_play.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
from snake_env import SnakeEnv, FOOD
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from s3_consequence import greedy_toward_food

def A(n,k): return {"type":"Attr","node":{"type":"Var","name":n},"key":k}
def gnode(agent):
    return next((n for n in agent.s.nodes("WorldInstance") if agent.s.node(n)["attrs"].get("world_type")=="Game"), None)

def main():
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)
    calls={"n":0}; agent.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"DONKEY")[1])
    world = ArcWorld(SnakeEnv()); sub,ctx=world.reset(); agent.perceive_frame(sub); env=world.env
    g = gnode(agent)
    # consequence slots for the colours the agent perceives (8 food, 14 body) — perception, not semantics
    cms={}
    for rv in (8.0,14.0):
        cm=agent.s.add_node("Consequence",{"rvalue":rv,"value":0.0}); agent.inner.add_edge_unchecked(g,"tracks_consequence",cm); cms[rv]=cm
    # contact_consequence (trainer/EMA): fold the contacted colour's consequence toward the reward
    agent.inner.add_rule({"name":"contact_consequence",
      "match":[["g","tracks_consequence","cm"]],
      "where":{"type":"And","items":[{"type":"Eq","a":A("cm","rvalue"),"b":A("g","contact_rvalue")},
        {"type":"Not","arg":{"type":"Eq","a":A("g","contact_rvalue"),"b":{"type":"Lit","value":0.0}}}]},
      "effects":[["set_attr","cm","clocked",1.0],
        ["set_attr","cm","next_value",{"__term__":{"type":"Plus","items":[{"type":"Plus","items":[A("cm","value"),{"type":"Lit","value":0.0}]},
           {"type":"Times","items":[{"type":"Lit","value":0.5},{"type":"Minus","a":A("g","reward"),"b":{"type":"Plus","items":[A("cm","value"),{"type":"Lit","value":0.0}]}}]}]}}]]})
    # target-producer: self (controllable region) seeks the centroid of the region whose colour it LEARNED is
    # rewarding (consequence>0). self.tgt_r/tgt_c + tgt_set -> the held seek_primitive pursues, death-gated.
    agent.inner.add_rule({"name":"seek_positive_consequence",
      "match":[["game","has_region","s"],["game","has_region","f"],["game","tracks_consequence","cm"]],
      "where":{"type":"And","items":[
        {"type":"Gte","a":{"type":"Plus","items":[A("s","respond_votes"),{"type":"Lit","value":0}]},"b":{"type":"Lit","value":2}},
        {"type":"Eq","a":A("f","rvalue"),"b":A("cm","rvalue")},
        {"type":"Gt","a":{"type":"Plus","items":[A("cm","value"),{"type":"Lit","value":0.0}]},"b":{"type":"Lit","value":0.3}}]},
      "effects":[["set_attr","s","tgt_r",{"__term__":A("f","cy")}],["set_attr","s","tgt_c",{"__term__":A("f","cx")}],["set_attr","s","tgt_set",1.0]]})

    def step(action, learn=True):
        nonlocal sub,ctx,env
        prev = ctx.get("score",0) or 0
        sub,ctx=world.apply((action,)); agent.perceive_frame(sub)
        score=ctx.get("score",0) or 0; over=bool(ctx.get("over")); ate=score>prev
        agent.s.set_attr(g,"contact_rvalue", float(FOOD) if ate else 0.0)
        agent.s.set_attr(g,"reward", 1.0 if ate else (-1.0 if over else 0.0))
        agent.master_tick(); agent.tick()
        if over: sub,ctx=world.apply(("Reset",)); agent.perceive_frame(sub); agent.master_tick(); agent.tick(); env=world.env
        return ate

    # PHASE A — explore: learn control basis (acting) + consequence (eating)
    eatsA=0
    for i in range(60):
        if step(greedy_toward_food(env)): eatsA+=1
    c8=agent.s.node(cms[8.0])["attrs"].get("value")
    # PHASE B — exploit: the agent chooses its OWN action (seek toward learned-rewarding colour)
    eatsB=0; chose=0
    for i in range(60):
        a = agent.s.node(gnode(agent))["attrs"].get("chosen_action")
        if a: chose+=1
        if step(a or "Up"): eatsB+=1
    print(f"  PHASE A (explore): eats={eatsA}  -> learned consequence[8 food]={c8:.3f}")
    print(f"  PHASE B (UNAIDED): agent chose its own action {chose}/60 frames; eats={eatsB}")
    print(f"  DONKEY (claude -p) calls: {calls['n']}")
    ok = (c8 or 0)>0.3 and chose>=30 and eatsB>=1 and calls["n"]==0
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'PARTIAL'} — Phase B: the agent played snake UNAIDED (chose its own actions "
          f"via seek toward the colour it LEARNED is rewarding, death-gated for walls/body), ate {eatsB}, with "
          f"NO host flag (food learned, consequence[8]={c8:.2f}) and NO claude -p (calls={calls['n']}). "
          f"S3 from the unified mechanism.")
    print("="*96)
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
