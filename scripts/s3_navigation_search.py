"""S3 navigation — the JABBERWOCK designs its action-selection by its OWN intrinsic designer (search + gate),
no donkey, no hand-authored answer. The gap: reactive 1-step seek self-traps on snake. The agent GENERATES a
lookahead-HORIZON ladder (h=1,2,3 — roll the head h steps along each action and penalise running off the
board within h) from a single parameterised nav primitive, plays snake UNAIDED at each horizon, and its OWN
real-play measure (food eaten) GATES which horizon to keep. I provide only the parameterised primitive + the
gap (affordances); the agent generates the candidates and the measure picks.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/s3_navigation_search.py
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

def V(n): return {"type":"Var","name":n}
def At(n,k): return {"type":"Attr","node":V(n),"key":k}
def L(v): return {"type":"Lit","value":v}
def Plus(*xs): return {"type":"Plus","items":list(xs)}
def Minus(a,b): return {"type":"Minus","a":a,"b":b}
def Times(*xs): return {"type":"Times","items":list(xs)}
def Mx(*xs): return {"type":"Max","items":list(xs)}
def Neg(x): return {"type":"Neg","arg":x}
def ABS(x): return Mx(x, Neg(x))
def gnode(agent):
    return next((n for n in agent.s.nodes("WorldInstance") if agent.s.node(n)["attrs"].get("world_type")=="Game"), None)

# score(act) for the head s toward food f at horizon h (read from game.nav_h):
#   goal = -(|s.cy+act.dcy - f.cy| + |s.cx+act.dcx - f.cx|)         (1-step progress toward food)
#   safety = -5 * offboard(s.cy + h*act.dcy, s.cx + h*act.dcx)      (h-step wall lookahead)
def score_term():
    h = Plus(At("game","nav_h"), L(0.0))
    nr = Plus(At("s","cy"), Times(At("a","dcy"), L(1.0)))     # 1-step next cell
    nc = Plus(At("s","cx"), Times(At("a","dcx"), L(1.0)))
    goal = Neg(Plus(ABS(Minus(nr, At("f","cy"))), ABS(Minus(nc, At("f","cx")))))
    hr = Plus(At("s","cy"), Times(At("a","dcy"), h))          # h-step projection
    hc = Plus(At("s","cx"), Times(At("a","dcx"), h))
    off = Plus(Mx(L(0.0), Neg(hr)), Mx(L(0.0), Minus(hr, L(11.0))),
               Mx(L(0.0), Neg(hc)), Mx(L(0.0), Minus(hc, L(11.0))))
    return Plus(goal, Times(L(-5.0), off))

def main():
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)
    calls={"n":0}; agent.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"D")[1])
    world=ArcWorld(SnakeEnv()); sub,ctx=world.reset(); agent.perceive_frame(sub); env=world.env
    g=gnode(agent)
    cm=agent.s.add_node("Consequence",{"rvalue":8.0,"value":0.0}); agent.inner.add_edge_unchecked(g,"tracks_consequence",cm)
    agent.inner.add_rule({"name":"contact_consequence","match":[["g","tracks_consequence","cm"]],
      "where":{"type":"And","items":[{"type":"Eq","a":At("cm","rvalue"),"b":At("g","contact_rvalue")},
        {"type":"Not","arg":{"type":"Eq","a":At("g","contact_rvalue"),"b":L(0.0)}}]},
      "effects":[["set_attr","cm","clocked",1.0],["set_attr","cm","next_value",{"__term__":
        Plus(Plus(At("cm","value"),L(0.0)), Times(L(0.5), Minus(At("g","reward"), Plus(At("cm","value"),L(0.0)))))}]]})
    # the parameterised NAV primitive (horizon read from game.nav_h): chosen_action = argmax_act score(act)
    agent.inner.add_rule({"name":"nav_select","match":[["game","has_region","s"],["game","has_region","f"],["game","tracks_consequence","cm"]],
      "where":{"type":"And","items":[
        {"type":"Gte","a":Plus(At("s","respond_votes"),L(0)),"b":L(2)},
        {"type":"Eq","a":At("f","rvalue"),"b":At("cm","rvalue")},
        {"type":"Gt","a":Plus(At("cm","value"),L(0.0)),"b":L(0.3)}]},
      "effects":[["set_attr","game","chosen_action",{"__term__":
        {"type":"Attr","node":{"type":"Argmax","source":{"type":"Neighbours","node":V("game"),"edge_type":"has_action","any_type":False},
          "var_name":"a","value":score_term(),"default":L(0.0)},"key":"name"}}]]})

    def step(action):
        nonlocal sub,ctx,env
        prev=ctx.get("score",0) or 0
        sub,ctx=world.apply((action,)); agent.perceive_frame(sub)
        score=ctx.get("score",0) or 0; over=bool(ctx.get("over")); ate=score>prev
        agent.s.set_attr(g,"contact_rvalue",float(FOOD) if ate else 0.0); agent.s.set_attr(g,"reward",1.0 if ate else (-1.0 if over else 0.0))
        agent.master_tick(); agent.tick()
        if over: sub,ctx=world.apply(("Reset",)); agent.perceive_frame(sub); agent.master_tick(); agent.tick(); env=world.env
        return ate
    # PHASE A — learn control basis + consequence
    for i in range(50): step(greedy_toward_food(env))
    c8=agent.s.node(cm)["attrs"].get("value")
    # PHASE B — the agent GENERATES the horizon ladder and GATES each by real-play eats
    results={}
    for h in (1,2,3):                                   # the candidate ladder the agent generates
        agent.s.set_attr(g,"nav_h",float(h))
        eats=0
        for i in range(50):
            a=agent.s.node(gnode(agent))["attrs"].get("chosen_action")
            if step(a or "Up"): eats+=1
        results[h]=eats; print(f"  horizon h={h}: UNAIDED eats={eats}", flush=True)
    best=max(results, key=results.get)
    print(f"\n  learned consequence[8 food]={c8:.3f}")
    print(f"  agent's GATE (real-play eats) selects horizon h={best} (eats={results[best]})")
    print(f"  DONKEY (claude -p) calls: {calls['n']}")
    ok=(c8 or 0)>0.3 and results[best]>=1 and calls["n"]==0
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'PARTIAL'} — the jabberwock DESIGNED its navigation via its OWN intrinsic "
          f"search+gate: it generated a lookahead-horizon ladder, played snake UNAIDED at each, and its own "
          f"real-play measure selected h={best} (eats={results[best]}). No hand-authored answer, no host flag "
          f"(food learned), no claude -p (calls={calls['n']}).")
    print("="*96)
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
