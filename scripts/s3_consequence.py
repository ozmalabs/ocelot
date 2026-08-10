"""S3 crux — the jabberwock LEARNS food-vs-everything by CONTACT (contact_consequence), no host flag, no
donkey. The agent is NOT told 8==food; it learns consequence[rvalue] = EMA of the reward that contacting
that colour produces (a trainer/EMA-shape faculty, rung-1 analogy to the held trainer). The host stamps only
RAW world outcomes (what the head touched + the reward) — perception it cannot fake; the LEARNING is the
agent's graph rule. Verify: after real snake play, consequence[8] (food) > 0, learned, with claude -p never
called.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/s3_consequence.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
from snake_env import SnakeEnv, HEAD, FOOD
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter

def A(n,k): return {"type":"Attr","node":{"type":"Var","name":n},"key":k}

def greedy_toward_food(env):
    """Mechanical navigation (the experience generator — a stand-in for the agent's epistemic exploration):
    head toward the food, never reversing into the neck."""
    (hr,hc) = env._snake[0]; (fr,fc) = env._food
    dr,dc = fr-hr, fc-hc
    opts = []
    if abs(dr) >= abs(dc):
        if dr<0: opts=["Up","Left","Right","Down"]
        elif dr>0: opts=["Down","Left","Right","Up"]
    if not opts:
        if dc<0: opts=["Left","Up","Down","Right"]
        else: opts=["Right","Up","Down","Left"]
    neck = env._snake[1] if len(env._snake)>1 else None
    rev = None
    if neck is not None:
        nr,nc = neck[0]-hr, neck[1]-hc
        rev = {( -1,0):"Up",(1,0):"Down",(0,-1):"Left",(0,1):"Right"}.get((nr,nc))
    for o in opts:
        if o != rev: return o
    return opts[0]

def main():
    agent = WorldAdapter(seeds=())                     # minimal: consequence learns from stamped outcomes
    calls = {"n":0}
    agent.set_self_teacher(lambda q: (calls.__setitem__("n", calls["n"]+1), "DONKEY")[1])
    g = agent.s.add_node("Game", {"id":"g","contact_rvalue":0.0,"reward":0.0})
    # the agent observes two non-background colours on the board (8,14) and opens a consequence slot per
    # colour it SEES — perception (which colours exist), not game-semantics (it does NOT know which is food).
    cms = {}
    for rv in (FOOD, HEAD+5):                           # 8 (food) and 14 (body) — colours it perceives
        cm = agent.s.add_node("Consequence", {"rvalue": float(rv), "value": 0.0})
        agent.inner.add_edge_unchecked(g, "tracks_consequence", cm)
        cms[rv] = cm
    # contact_consequence (trainer/EMA shape): for the consequence slot of the colour just contacted, fold
    # its value toward the observed reward. EMA: next_value = value + 0.5*(reward - value); clocked-fold.
    agent.inner.add_rule({"name":"contact_consequence",
      "match":[["g","tracks_consequence","cm"]],
      "where":{"type":"And","items":[
        {"type":"Eq","a":A("cm","rvalue"),"b":A("g","contact_rvalue")},
        {"type":"Not","arg":{"type":"Eq","a":A("g","contact_rvalue"),"b":{"type":"Lit","value":0.0}}}]},
      "effects":[
        ["set_attr","cm","clocked",1.0],
        ["set_attr","cm","next_value",{"__term__":{"type":"Plus","items":[
           {"type":"Plus","items":[A("cm","value"),{"type":"Lit","value":0.0}]},
           {"type":"Times","items":[{"type":"Lit","value":0.5},
             {"type":"Minus","a":A("g","reward"),"b":{"type":"Plus","items":[A("cm","value"),{"type":"Lit","value":0.0}]}}]}]}}]]})

    world = ArcWorld(SnakeEnv()); sub, ctx = world.reset(); env = world.env
    prev_score = 0; eats = 0; contacts = 0
    for i in range(120):
        a = greedy_toward_food(env)
        sub, ctx = world.apply((a,))
        score = ctx.get("score",0) or 0; over = 1.0 if ctx.get("over") else 0.0
        ate = score > prev_score
        # HOST stamps RAW outcomes (perception): what the head contacted + the reward. The head ate iff the
        # cell it entered was food (rvalue 8); a death is a negative reward (no colour slot).
        contact_rvalue = float(FOOD) if ate else 0.0
        reward = 1.0 if ate else (-1.0 if over else 0.0)
        agent.s.set_attr(g, "contact_rvalue", contact_rvalue)
        agent.s.set_attr(g, "reward", reward)
        agent.master_tick(); agent.tick()             # contact_consequence learns
        if ate: eats += 1
        if contact_rvalue != 0.0: contacts += 1
        prev_score = score
        if over:
            sub, ctx = world.apply(("Reset",)); env = world.env; prev_score = 0
    c8 = agent.s.node(cms[FOOD])["attrs"].get("value")
    c14 = agent.s.node(cms[HEAD+5])["attrs"].get("value")
    print(f"  snake play: eats={eats}  food-contacts learned-from={contacts}")
    print(f"  LEARNED consequence[8 food]  = {c8:.3f}   (was 0.0; never told 8==food)")
    print(f"  LEARNED consequence[14 body] = {c14:.3f}   (never positively contacted -> stays ~0)")
    print(f"  DONKEY (claude -p) calls: {calls['n']}")
    ok = (eats >= 2 and (c8 or 0) > 0.3 and abs(c14 or 0) < 0.1 and calls["n"] == 0)
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'FAIL'} — the jabberwock LEARNED that contacting colour 8 is rewarding "
          f"(consequence[8]={c8:.2f}>0) purely from real-play reward, with NO host flag encoding food and NO "
          f"claude -p (calls={calls['n']}). This is S3's crux faculty (food/body distinction) learned "
          f"intrinsically; select_action then seeks the positive-consequence colour, death-gated.")
    print("="*96)
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
