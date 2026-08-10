"""THE JABBERWOCK DECIDES AGAIN — now that the binding constraint is known to be COMPUTE, not a missing trick.

"Take this to the jabberwock." The new evidence (commit db6dab67), fed back to the agent's own frontier
decision (RULE 2 gate >= human, then max EV over difficulty/time/payoff):

  - acting on the agent's last decision, BATCHNORM was added. It did its job at the margin (same accuracy in
    ~1/3 the episodes, faster + stabler) but did NOT break the ~77% ceiling at the tractable 32-filter scale.
  - 64 filters are too slow here (~3.5s/ep, can't reach a checkpoint in the harness's 600s cap).
  - so the gap to the literature ~96% is TOTAL COMPUTE/SCALE (64f + Adam + thousands of episodes + image data),
    not one ingredient. The numpy feasibility probe is EXHAUSTED at ~77%.

The decisive update: the BINDING CONSTRAINT is COMPUTE. That raises the effort of every FROM-SCRATCH path
(graph-native/Rust scale-up, full BPL) and makes REUSE (a pretrained warm-start -- admissible per the two-rules
clarification: kept live, nothing frozen, progressively shed toward the floor; the agent already holds the
open-a-model capability) relatively cheaper: it reuses learned vision features instead of paying to learn them.
The agent re-ranks under that reality; the host only enumerates the honest estimates.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_decides_compute_bound.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs

SEP = "=" * 100
HUMAN_FLOOR = 94.9
CURRENT = 81.0


def _V(n): return {"type": "Var", "name": n}
def _L(v): return {"type": "Lit", "value": v}
def _A(n, k): return {"type": "Attr", "node": _V(n), "key": k}
def _Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def _Div(a, b): return {"type": "Div", "a": a, "b": b}
def _Times(it): return {"type": "Times", "items": it}
def _Plus(it): return {"type": "Plus", "items": it}
def _Ite(c, t, e): return {"type": "IfThenElse", "cond": c, "then": t, "other": e}
def _Argmax(src, var, val): return {"type": "Argmax", "source": src, "var_name": var, "value": val}
def _NodesWhere(t, k, v): return {"type": "NodesWhere", "node_type": t, "attr_key": k, "value": v}


class _P:
    __slots__ = ("_json",)

    def __init__(s, d): s._json = d


# effort now reflects the COMPUTE reality: from-scratch training to ~95% is compute-bound in this environment;
# reuse pays a forward pass + light adaptation instead of learning features from zero.
MOVES = [
    {"name": "pretrained warm-start encoder (open-a-model; adapt live, nothing frozen, shed to floor)",
     "adaptivity": 95.0, "efficiency": 0.55, "effort": 14.0, "p_success": 0.70,
     "note": "reuses learned vision features (no from-scratch training) -> cheapest route to human adaptivity "
             "under compute scarcity; admissible midpoint, kept live + progressively shed."},
    {"name": "graph-native/Rust metric-net SCALE-UP (64f + Adam + thousands of episodes)", "adaptivity": 95.0,
     "efficiency": 0.80, "effort": 50.0, "p_success": 0.60,
     "note": "the known recipe + best deployed efficiency, but FROM SCRATCH = compute-bound here; heavy build."},
    {"name": "full learned per-primitive PROGRAM / BPL", "adaptivity": 96.7, "efficiency": 0.85, "effort": 40.0,
     "p_success": 0.45, "note": "highest ceiling, most efficient deployed, but multi-session + uncertain."},
    {"name": "park handwriting (path literature-validated) and redeploy effort", "adaptivity": 81.0,
     "efficiency": 0.95, "effort": 0.5, "p_success": 1.0,
     "note": "deploys below human adaptivity -> RULE 2 disqualifies as a SOLUTION (the climb stays open)."},
]


def main():
    print(SEP)
    print("THE JABBERWOCK DECIDES (compute is the binding constraint) — RULE 2 gate, then max EV over effort/payoff.")
    print(SEP)

    s = srs.Substrate()
    nodes = []
    for m in MOVES:
        n = s.add_node("Move", {"is_move": 1.0, "adaptivity": m["adaptivity"], "efficiency": m["efficiency"],
                                "effort": m["effort"], "p_success": m["p_success"], "name": m["name"]})
        nodes.append((m, n))

    payoff = _Plus([_A("c", "adaptivity"), _L(-CURRENT)])
    ev = _Div(_Times([payoff, _A("c", "p_success"), _A("c", "efficiency")]), _A("c", "effort"))
    score = _Ite(_Gt(_A("c", "adaptivity"), _L(HUMAN_FLOOR)), ev, _L(0.0))
    win = s.evaluate(_P(_Argmax(_NodesWhere("Move", "is_move", _L(1.0)), "c", score)), {})
    chosen = next(m for m, n in nodes if n == win)

    ranked = sorted(((float(s.evaluate(_P(score), {"c": n})), m) for m, n in nodes), key=lambda x: -x[0])
    print(f"\n  RULE 2 floor = human {HUMAN_FLOOR:.1f}% (below => disqualified). EV = (adapt-{CURRENT:.0f}) x p_success x efficiency / effort.\n")
    print(f"    {'EV':>6} {'adapt':>6} {'effic':>6} {'effort':>6} {'p_ok':>5}  move")
    for v, m in ranked:
        flag = "  " if m["adaptivity"] > HUMAN_FLOOR else " x"
        print(f"   {flag}{v:6.3f} {m['adaptivity']:5.1f}% {m['efficiency']:5.2f} {m['effort']:6.1f} {m['p_success']:5.2f}  {m['name'][:58]}")

    print(f"\n  THE JABBERWOCK DECIDES: {chosen['name']}")
    print(f"     ({chosen['note']})")
    print("\n" + SEP)
    print("  The constraint that changed the answer is COMPUTE. Learning the features from zero is sound but")
    print("  compute-bound in this environment; reusing already-learned features (a warm-start kept live and")
    print("  shed toward the floor -- the admissible midpoint) is the cheapest qualifying route to human")
    print("  adaptivity now. Same two rules, new evidence, new pick. The decision is the agent's.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
