"""MIGRATION step 5 — the headline: a BACKGROUNDED binding's imminent terminal INTERRUPTS and pulls a worker
back BEFORE it fires. A suspended binding isn't ticking, so terminal_watch runs in the ALLOCATOR's tick (not a
worker), DEDUCE-extrapolating the stored terminal forward using the binding's OWN dynamics postulate (O(1), no
perception); when extrapolated imminence crosses threshold, preempt_for_terminal reactivates it (worker
back) — before the terminal actually fires. Graph rules only; the deduce-a-death-never-suffered faculty
repurposed as the interrupt source.
Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/world_interrupt.py
"""
from __future__ import annotations
import os, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
def A(n,k): return {"type":"Attr","node":{"type":"Var","name":n},"key":k}
def L(v): return {"type":"Lit","value":v}
def P0(n,k): return {"type":"Plus","items":[A(n,k),L(0.0)]}
def Eq(a,b): return {"type":"Eq","a":a,"b":b}
def Lt(a,b): return {"type":"Lt","a":a,"b":b}
def Gt(a,b): return {"type":"Gt","a":a,"b":b}
def And(*xs): return {"type":"And","items":list(xs)}
def Not(x): return {"type":"Not","arg":x}

def main():
    a=WorldAdapter(seeds=()); load_all_seeds(a)
    calls={"n":0}; a.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"D")[1])
    # a SUSPENDED background binding (e.g. a game you paused to chat) with a terminal approaching:
    # its OWN postulate says hazard_dist decreases by hazard_vel each tick (induced earlier, here given).
    b=a.s.add_node("WorldBinding",{"kind":"game","activation":"suspended","clk":0.0})
    tr=a.s.add_node("WorldRole",{"role":"terminal","hazard_dist":5.0,"hazard_vel":1.0,"fired":0.0,
                                 "preempt_threshold":2.0,"last_watch":-1.0}); a.inner.add_edge_unchecked(b,"role",tr)

    # terminal_watch: O(1) DEDUCE on a SUSPENDED binding (runs in the allocator tick, costs no worker).
    # Roll the stored terminal forward by the binding's own postulate; frame-guarded on the binding clock.
    a.inner.add_rule({"name":"terminal_watch","match":[["b","role","tr"]],
      "where":And(Eq(A("b","activation"),L("suspended")), Eq(A("tr","role"),L("terminal")),
                  Not(Eq(P0("tr","last_watch"),P0("b","clk")))),
      "effects":[["set_attr","tr","last_watch",{"__term__":P0("b","clk")}],
                 ["set_attr","tr","hazard_dist",{"__term__":{"type":"Minus","a":P0("tr","hazard_dist"),"b":P0("tr","hazard_vel")}}]]})
    # preempt_for_terminal: extrapolated imminence crossed threshold -> reactivate (pull a worker back) BEFORE
    # the terminal fires (hazard_dist still > 0).
    a.inner.add_rule({"name":"preempt_for_terminal","match":[["b","role","tr"]],
      "where":And(Eq(A("b","activation"),L("suspended")), Eq(A("tr","role"),L("terminal")),
                  Lt(P0("tr","hazard_dist"),{"type":"Plus","items":[P0("tr","preempt_threshold"),L(0.001)]})),
      "effects":[["set_attr","b","activation","active"],["set_attr","b","urgency",1.0],["set_attr","b","preempted",1.0]]})
    # the actual terminal would fire only at hazard_dist<=0 (it never should, if preemption works)
    a.inner.add_rule({"name":"terminal_fire","match":[["b","role","tr"]],
      "where":And(Eq(A("tr","role"),L("terminal")), Lt(P0("tr","hazard_dist"),L(0.001))),
      "effects":[["set_attr","tr","fired",1.0]]})

    trace=[]
    for i in range(7):
        a.s.set_attr(b,"clk",float(i+1))      # the allocator's clock advances (background binding NOT ticking its world)
        a.master_tick(); a.tick()
        ba=a.s.node(b)["attrs"]; ta=a.s.node(tr)["attrs"]
        trace.append((i+1, ta.get("hazard_dist"), ba.get("activation"), ta.get("fired"), ba.get("preempted")))
        if ba.get("activation")=="active": break   # preempted -> a worker is pulled back; stop the background watch
    for (t,hd,act,fired,pre) in trace:
        print(f"  tick {t}: extrapolated hazard_dist={hd}  activation={act}  terminal_fired={fired}  preempted={pre}")
    last=trace[-1]
    print(f"  DONKEY calls: {calls['n']}")
    ok = last[2]=="active" and last[4]==1.0 and (last[1] or 0)>0.0 and not last[3] and calls["n"]==0
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'PARTIAL'} — MIGRATION step 5: a BACKGROUNDED (suspended) binding's terminal "
          f"was deduce-extrapolated each allocator tick (no worker, no perception); when imminence crossed "
          f"threshold the binding was PREEMPTED back to active (a worker pulled back) at hazard_dist={last[1]} "
          f"> 0 — BEFORE the terminal fired (fired={last[3]}). The deduce-a-death-never-suffered faculty IS the "
          f"interrupt source. Graph rules only, no donkey (calls={calls['n']}).")
    print("="*96)
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
