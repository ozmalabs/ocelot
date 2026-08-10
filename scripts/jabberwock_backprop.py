"""BACKPROP — the trainer primitive, LAYERED. The single-layer delta rule (jabberwock_trainer) cannot solve a
problem that isn't linearly separable; this scales it to a multi-layer net with graph-native backpropagation
(credit assignment through a hidden layer) and learns XOR -- the canonical proof that one layer provably can't
and a hidden layer can. This is the faculty the two-rules re-decision needs for the handwriting metric net.

A 2-4-1 sigmoid MLP, all weights as attrs on one Net node; sigmoid s(z)=1/(1+exp(-z)) built from the Exp term,
derivative s(1-s). Two graph Rules do a full online backprop step each tick:
  FORWARD :  h_j = s( x.w_j + b_j ) ;  out = s( h.v + c )
  BACKWARD:  do = (t-out) out (1-out) ;  dh_j = do v_j h_j (1-h_j)            <- credit assigned through the layer
             v_j += lr do h_j ; c += lr do ;  w_ij += lr dh_j x_i ; b_j += lr dh_j
Every gradient/update is a graph Term; the host only presents the XOR patterns and beats master_tick;tick, and
random-inits the weights (symmetry breaking). Backprop = the delta rule, layered -- proven in the graph.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_backprop.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np
from substrate.world_adapter import WorldAdapter

SEP = "=" * 100
H = 4
LR = 0.5
EPOCHS = 1500
XOR = [(0.0, 0.0, 0.0), (0.0, 1.0, 1.0), (1.0, 0.0, 1.0), (1.0, 1.0, 0.0)]


def _V(n): return {"type": "Var", "name": n}
def A(k): return {"type": "Attr", "node": _V("n"), "key": k}
def _L(v): return {"type": "Lit", "value": v}
def _Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def _And(*xs): return {"type": "And", "items": list(xs)}
def _Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def _Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def _Plus(*xs): return {"type": "Plus", "items": list(xs)}
def _Times(*xs): return {"type": "Times", "items": list(xs)}
def _Exp(a): return {"type": "Exp", "arg": a}
def _Div(a, b): return {"type": "Div", "a": a, "b": b}


def SIG(z):
    return _Div(_L(1.0), _Plus(_L(1.0), _Exp(_Minus(_L(0.0), z))))


# FORWARD: hidden activations then output, all sigmoid. Stores h_j and out for the backward pass.
FORWARD = {
    "id": "fwd", "name": "fwd",
    "match": [["r", "has_net", "n"]],
    "where": _Gt(A("frame"), A("fwd_frame")),
    "effects": (
        [["set_attr", "n", f"h{j}", {"__term__": SIG(_Plus(_Times(A("x0"), A(f"w0{j}")),
                                                           _Times(A("x1"), A(f"w1{j}")), A(f"b{j}")))}]
         for j in range(H)]
        + [["set_attr", "n", "out", {"__term__": SIG(_Plus(*[_Times(A(f"h{j}"), A(f"v{j}")) for j in range(H)], A("c")))}]]
        + [["set_attr", "n", "fwd_frame", {"__term__": A("frame")}]])}

# BACKWARD: output delta, then hidden deltas (credit through the layer), then weight updates. dh_j uses the OLD
# v_j (computed + stored before v_j is updated). Skipped when frozen (eval).
DO = _Times(_Minus(A("t"), A("out")), A("out"), _Minus(_L(1.0), A("out")))
BACKWARD = {
    "id": "bwd", "name": "bwd",
    "match": [["r", "has_net", "n"]],
    "where": _And(_Eq(A("fwd_frame"), A("frame")), _Gt(A("frame"), A("bwd_frame")), _Eq(A("freeze"), _L(0.0))),
    "effects": (
        [["set_attr", "n", "do", {"__term__": DO}]]
        + [["set_attr", "n", f"dh{j}", {"__term__": _Times(A("do"), A(f"v{j}"), A(f"h{j}"), _Minus(_L(1.0), A(f"h{j}")))}]
           for j in range(H)]
        + [["set_attr", "n", f"v{j}", {"__term__": _Plus(A(f"v{j}"), _Times(_L(LR), A("do"), A(f"h{j}")))}] for j in range(H)]
        + [["set_attr", "n", "c", {"__term__": _Plus(A("c"), _Times(_L(LR), A("do")))}]]
        + [["set_attr", "n", f"w0{j}", {"__term__": _Plus(A(f"w0{j}"), _Times(_L(LR), A(f"dh{j}"), A("x0")))}] for j in range(H)]
        + [["set_attr", "n", f"w1{j}", {"__term__": _Plus(A(f"w1{j}"), _Times(_L(LR), A(f"dh{j}"), A("x1")))}] for j in range(H)]
        + [["set_attr", "n", f"b{j}", {"__term__": _Plus(A(f"b{j}"), _Times(_L(LR), A(f"dh{j}")))}] for j in range(H)]
        + [["set_attr", "n", "bwd_frame", {"__term__": A("frame")}]])}


def main():
    print(SEP)
    print("BACKPROP — the trainer LAYERED: a 2-4-1 sigmoid MLP learns XOR via graph-native backpropagation.")
    print(SEP)

    agent = WorldAdapter(seeds=())                 # minimal boot -- only the MLP rules run (fast ticks)
    rng = np.random.default_rng(0)
    init = {"x0": 0.0, "x1": 0.0, "t": 0.0, "out": 0.0, "do": 0.0,
            "frame": 0.0, "fwd_frame": -1.0, "bwd_frame": -1.0, "freeze": 0.0}
    for j in range(H):
        init[f"w0{j}"] = float(rng.normal(0, 1)); init[f"w1{j}"] = float(rng.normal(0, 1))
        init[f"b{j}"] = float(rng.normal(0, 1)); init[f"v{j}"] = float(rng.normal(0, 1))
        init[f"h{j}"] = 0.0; init[f"dh{j}"] = 0.0
    init["c"] = float(rng.normal(0, 1))
    n = agent.s.add_node("Net", init)
    root = agent.s.add_node("Root", {"is_root": 1.0})
    agent.inner.add_edge_unchecked(root, "has_net", n)
    for r in (FORWARD, BACKWARD):
        agent.inner.add_rule(r)

    fr = [0]

    def present(x0, x1, t):
        fr[0] += 1
        agent.s.set_attr(n, "x0", x0); agent.s.set_attr(n, "x1", x1); agent.s.set_attr(n, "t", t)
        agent.s.set_attr(n, "frame", float(fr[0]))
        agent.master_tick(); agent.tick()

    def evaluate():
        agent.s.set_attr(n, "freeze", 1.0)         # forward only, no weight update
        ok, outs = 0, []
        for x0, x1, t in XOR:
            present(x0, x1, t)
            out = agent.s.node(n)["attrs"]["out"]
            outs.append(out)
            ok += (round(out) == t)
        agent.s.set_attr(n, "freeze", 0.0)
        return ok, outs

    acc0, outs0 = evaluate()
    print(f"\n  before training: {acc0}/4 correct  outputs {[f'{o:.2f}' for o in outs0]}")
    print(f"  training {EPOCHS} epochs of online backprop in the heartbeat (2-{H}-1 sigmoid, lr={LR})...\n")
    curve = []
    for e in range(EPOCHS):
        for x0, x1, t in XOR:
            present(x0, x1, t)
        if e in (50, 200, 600, EPOCHS - 1):
            acc, _ = evaluate()
            curve.append((e + 1, acc))
            print(f"    epoch {e+1:5d}:  {acc}/4 correct")

    acc, outs = evaluate()
    print(f"\n  after training: {acc}/4 correct  outputs {[f'{o:.3f}' for o in outs]}  (targets [0, 1, 1, 0])")
    ok = (acc0 < 4 and acc == 4)
    print("\n" + SEP)
    print(f"  {'PASS' if ok else 'PARTIAL'} — graph-native BACKPROP. A single layer (the delta rule) provably cannot separate")
    print(f"  XOR; this 2-{H}-1 net assigns credit THROUGH its hidden layer (dh_j = do * v_j * h_j(1-h_j)) and learns")
    print(f"  it to {acc}/4, every gradient a graph Term, every update a Rule in the heartbeat. The trainer primitive")
    print(f"  scales: backprop IS the delta rule, layered -- the faculty the handwriting metric net needs (rule 2),")
    print(f"  still cheap and online (rule 1). From single-tap LMS to a multi-layer net, the agent's own learning.")
    print(SEP)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
