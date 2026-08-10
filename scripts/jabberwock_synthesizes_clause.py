"""NOVEL CLAUSE SYNTHESIS (extension a) — the agent BUILDS a repair clause from live operands, not a copy.

Two rules gate on a threshold that's wrong (set too high, so they never fire). Two synth Faults of shape
`threshold_gate` carry DIFFERENT live operands (good_thresh 3 vs 50). The clause_synthesis faculty builds each
corrected `where` clause via MkDict from those live operands — two DIFFERENT clauses from ONE template — and
repair_apply installs them. Result: rule A (5 > 3) fires, rule B (5 > 50) does not. The synthesis is genuinely
novel (parameterised by the fault), pure graph data, no Rust.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_synthesizes_clause.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds


def gate_rule(name, edge):
    return {"name": name, "match": [["g", edge, "x"]],
            "where": {"type": "Gt", "a": {"type": "Attr", "node": {"type": "Var", "name": "x"}, "key": "v"},
                      "b": {"type": "Lit", "value": 100.0}},   # bad threshold: never fires (v=5)
            "effects": [["set_attr", "x", "out", {"__term__": {"type": "Lit", "value": "fired"}}]]}


def mint_synth_fault(agent, target, thresh):
    f = agent.s.add_node("Fault", {"target_rule": target, "field": "where", "shape": "threshold_gate",
                                   "gate_var": "x", "gate_attr": "v", "good_thresh": float(thresh),
                                   "awaiting_synth": 1.0, "applied": 0.0})
    agent.inner.add_edge_unchecked(agent.agent, "has_fault", f)
    return f


def thresh_of(corrected):
    """Pull the synthesised threshold out of the corrected where-clause value (Gt.b.value)."""
    try:
        return corrected["b"]["value"]
    except Exception:
        try:
            d = dict(corrected); b = dict(d["b"]); return b["value"]
        except Exception:
            return None


def main():
    print("=" * 92)
    print("NOVEL CLAUSE SYNTHESIS — one template, live operands, two DIFFERENT synthesised clauses.")
    print("=" * 92)
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)
    g = agent.s.add_node("Anchor", {})
    pa = agent.s.add_node("Probe", {"v": 5.0})
    pb = agent.s.add_node("Probe", {"v": 5.0})
    agent.inner.add_edge_unchecked(g, "has_pa", pa)
    agent.inner.add_edge_unchecked(g, "has_pb", pb)
    agent.inner.add_rule(gate_rule("R_gate_a", "has_pa"))
    agent.inner.add_rule(gate_rule("R_gate_b", "has_pb"))
    for _ in range(2):
        agent.master_tick(); agent.tick()
    print(f"  before: probe_a.out={agent.s.node(pa)['attrs'].get('out')!r}, "
          f"probe_b.out={agent.s.node(pb)['attrs'].get('out')!r}  (both gates threshold=100, v=5 -> never fire)")

    fa = mint_synth_fault(agent, "R_gate_a", 3.0)     # synthesise Gt(x.v, 3)  -> 5>3 fires
    fb = mint_synth_fault(agent, "R_gate_b", 50.0)    # synthesise Gt(x.v, 50) -> 5<50 does not
    for _ in range(5):
        agent.master_tick(); agent.tick()

    ca = agent.s.node(fa)["attrs"].get("corrected")
    cb = agent.s.node(fb)["attrs"].get("corrected")
    ta, tb = thresh_of(ca), thresh_of(cb)
    oa = agent.s.node(pa)["attrs"].get("out")
    ob = agent.s.node(pb)["attrs"].get("out")
    print(f"\n  synthesised clause A threshold={ta}; clause B threshold={tb}  (built from each fault's live operand)")
    print(f"  after repair: probe_a.out={oa!r} (expect 'fired', 5>3), probe_b.out={ob!r} (expect None, 5<50)")

    ok = ta == 3.0 and tb == 50.0 and ta != tb and oa == "fired" and ob is None
    print("\n" + "=" * 92)
    print(f"  {'PASS' if ok else 'FAIL'} — the agent SYNTHESISED two different repair clauses from one "
          f"parameterised template by splicing each fault's live operands (MkDict), and repair_apply installed "
          f"them by name. Novel clause synthesis, pure graph data, no stored copy, no Rust.")
    print("=" * 92)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
