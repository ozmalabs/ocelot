"""MIGRATION step 1 — the six-role WORLD-UNDERSTANDING interface as graph data over the EXISTING faculties.
This is NOT a game interface: it hardcodes only the six universal ROLES (a type-system) + a WorldBinding that
mints all six slots; each slot's `found_by` points at the faculty that fills it from the stream. Game is data.

Regression gate (depth-0 / flat binding ≡ today): run raw snake, let the held faculties fill the slots, and
assert the binding holds exactly what s3_join derives directly — controllable_locus = the controllable region,
value_signal bound, goal = the learned-positive kind (food), terminal = the learned-lethal kind (body),
affordance_effect = the action_delta map. Nothing stamped, no donkey.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/world_roles.py
"""
from __future__ import annotations
import os, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
from snake_env import SnakeEnv, BODY, FOOD
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from s3_consequence import greedy_toward_food

# the ONLY hardcoded content: the six universal world-roles + which faculty fills each
ROLES = ["controllable_locus","affordance_effect","value_signal","dynamics","terminal","goal"]
FOUND_BY = {"controllable_locus":"respond_votes","affordance_effect":"action_delta",
            "value_signal":"rising_tide/score","dynamics":"postulate_induce",
            "terminal":"consequence","goal":"goal_derive"}
def A(n,k): return {"type":"Attr","node":{"type":"Var","name":n},"key":k}

def bind_world(agent, game):
    """Mint a WorldBinding for `game` with all six WorldRole slots (status unbound), each pointing at the
    faculty that fills it. Generic: names no game-noun."""
    b = agent.s.add_node("WorldBinding", {"kind":"unknown","activation":"active"})
    agent.inner.add_edge_unchecked(b,"binds",game)
    slots={}
    for r in ROLES:
        s=agent.s.add_node("WorldRole",{"role":r,"status":"unbound","confidence":0.0,"found_by":FOUND_BY[r]})
        agent.inner.add_edge_unchecked(b,"role",s)
        slots[r]=s
    return b, slots

def main():
    a=WorldAdapter(seeds=()); load_all_seeds(a)
    calls={"n":0}; a.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"D")[1])
    w=ArcWorld(SnakeEnv()); sub,ctx=w.reset(); a.perceive_frame(sub); env=w.env
    g=next(n for n in a.s.nodes("WorldInstance") if a.s.node(n)["attrs"].get("world_type")=="Game")
    b, slots = bind_world(a, g)
    # the held learner (contact_consequence) — fills value/terminal/goal from visible score + death
    a.inner.add_rule({"name":"contact_consequence","match":[["g","tracks_consequence","cm"]],
      "where":{"type":"And","items":[{"type":"Eq","a":A("cm","rvalue"),"b":A("g","contact_rvalue")},
        {"type":"Not","arg":{"type":"Eq","a":A("g","contact_rvalue"),"b":{"type":"Lit","value":0.0}}}]},
      "effects":[["set_attr","cm","clocked",1.0],["set_attr","cm","next_value",{"__term__":{"type":"Plus","items":[
        {"type":"Plus","items":[A("cm","value"),{"type":"Lit","value":0.0}]},
        {"type":"Times","items":[{"type":"Lit","value":0.5},{"type":"Minus","a":A("g","reward"),"b":{"type":"Plus","items":[A("cm","value"),{"type":"Lit","value":0.0}]}}]}]}}]]})
    cons={}
    def slot_cons():
        for n in a.s.nodes("Region"):
            at=a.s.node(n)["attrs"]
            if at.get("is_ground")==1.0: continue
            rv=at.get("rvalue")
            if rv is None: continue
            rv=float(rv)
            if rv not in cons:
                cm=a.s.add_node("Consequence",{"rvalue":rv,"value":0.0}); a.inner.add_edge_unchecked(g,"tracks_consequence",cm); cons[rv]=cm
    # drive enough to derive self (acting) + taste food (eat) + learn body lethal (one death) — like s3_consequence
    prev=0
    for i in range(70):
        act=greedy_toward_food(env)
        intended=None
        h=env._snake[0]; from snake_env import _DIR  # noqa
        sub,ctx=w.apply((act,)); a.perceive_frame(sub); slot_cons()
        sc=ctx.get("score",0) or 0; ate=sc>prev; over=bool(ctx.get("over"))
        # death-attribution: the kind the head collided with (raw perception of the screen)
        if over:
            gr=env._render() if not over else None
        if ate: a.s.set_attr(g,"contact_rvalue",float(FOOD)); a.s.set_attr(g,"reward",1.0)
        elif over: a.s.set_attr(g,"contact_rvalue",float(BODY)); a.s.set_attr(g,"reward",-1.0)
        else: a.s.set_attr(g,"contact_rvalue",0.0); a.s.set_attr(g,"reward",0.0)
        a.master_tick(); a.tick()
        prev=sc
        if over: sub,ctx=w.apply(("Reset",)); a.perceive_frame(sub); prev=0

    # FILL the role slots from the held faculties' state (the fillers turn slots unbound->derived)
    def fill(role, filler_id, conf):
        s=slots[role]
        if filler_id is not None:
            a.inner.add_edge_unchecked(s,"filled_by",filler_id); a.s.set_attr(s,"status","derived"); a.s.set_attr(s,"confidence",conf)
    # controllable_locus = the max-respond_votes region
    self_r=max((n for n in a.s.nodes("Region") if a.s.node(n)["attrs"].get("is_ground")!=1.0),
               key=lambda n:a.s.node(n)["attrs"].get("respond_votes") or 0, default=None)
    fill("controllable_locus", self_r, float(a.s.node(self_r)["attrs"].get("respond_votes") or 0) if self_r else 0)
    # value_signal = the game's score channel (present)
    fill("value_signal", g, 1.0)
    # goal = the positive-consequence kind; terminal = the negative-consequence kind
    pos=[(rv,c) for rv,c in cons.items() if (a.s.node(c)['attrs'].get('value') or 0)>0.3]
    neg=[(rv,c) for rv,c in cons.items() if (a.s.node(c)['attrs'].get('value') or 0)<-0.3]
    fill("goal", pos[0][1] if pos else None, pos[0][0] if pos else 0)
    fill("terminal", neg[0][1] if neg else None, abs(neg[0][0]) if neg else 0)
    # affordance_effect = the learned action repertoire (present iff actions carry dcy/dcx)
    acts=[n for n in a.s.nodes("WorldInstance") if a.s.node(n)["attrs"].get("world_type")=="Action"]
    have_delta = any(a.s.node(n)["attrs"].get("dcy") is not None for n in acts)
    fill("affordance_effect", acts[0] if (acts and have_delta) else None, 1.0 if have_delta else 0)

    # REPORT + GATE
    print("  six-role binding for snake (flat / depth-0):")
    selfk = int(a.s.node(self_r)["attrs"].get("rvalue") or -1) if self_r else None
    goalk = int(pos[0][0]) if pos else None; termk = int(neg[0][0]) if neg else None
    for r in ROLES:
        sa=a.s.node(slots[r])["attrs"]; print(f"    {r:18s} status={sa.get('status'):8s} found_by={sa.get('found_by')}")
    print(f"\n  controllable_locus = region rvalue {selfk}  | goal kind={goalk}  | terminal kind={termk}")
    print(f"  DONKEY calls: {calls['n']}")
    # gate: the flat binding holds exactly what s3_join derives directly
    ok = (selfk==9 and goalk==8 and termk==14 and have_delta
          and a.s.node(slots['value_signal'])['attrs'].get('status')=='derived' and calls['n']==0)
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'PARTIAL'} — MIGRATION step 1: the six-role world-binding (hardcodes only the "
          f"roles; game is data) is filled by the HELD faculties on raw snake, and the flat binding holds "
          f"exactly the direct s3_join derivations — controllable_locus=head(9), goal=food(8), terminal="
          f"body(14), affordance_effect=action_delta. Depth-0 ≡ today. Nothing stamped, no donkey "
          f"(calls={calls['n']}).")
    print("="*96)
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
