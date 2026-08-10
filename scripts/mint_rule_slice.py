"""SELF-BUILD slice — the agent MINTS a brand-new LIVE rule from a Rule node it composed.

The jabberwock's choice: mint rides the same pending_rule_edits queue as set_rule_clause. The agent builds a
type="Rule" node (id/match/where/effect as graph data) and a minting rule emits
set_rule_clause(<id>, "__mint__", <that node>); Substrate::run_rules compiles it via rule_from_node + add_rule
so it runs LIVE on the next pass (on the one proven struct engine, JIT'd + access-derived). Name-guarded =>
idempotent. This is the create-twin of the rewrite the fault-fixing system already trusts — the capability
that lets the agent build its own seeds.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/mint_rule_slice.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter

LIT_T = {"type": "Lit", "value": True}


def main():
    a = WorldAdapter()
    s = a.s

    # the target the minted rule will act on
    anchor = s.add_node("Anchor", {})
    t = s.add_node("Probe", {})
    a.inner.add_edge_unchecked(anchor, "trig", t)

    # the agent COMPOSES a Rule node (graph data) — id/match/where/effect — to be minted live
    rn = s.add_node("Rule", {
        "id": "minted_test",
        "match": [["anc", "trig", "tg"]],
        "where": LIT_T,
        "effect": [["set_attr", "tg", "out", {"__term__": {"type": "Lit", "value": "minted"}}]],
        "minted": 0.0,
    })
    minter = s.add_node("Minter", {})
    a.inner.add_edge_unchecked(minter, "wants_mint", rn)

    # the minting rule (a struct rule): when something wants a Rule node minted and it isn't yet, emit
    # set_rule_clause(<id>, "__mint__", <the Rule node>) -> the drain compiles it into a live struct rule.
    a.inner.add_rule({
        "name": "mint_pending",
        "match": [["m", "wants_mint", "rn"]],
        "where": {"type": "Lt", "a": {"type": "Plus", "items": [
            {"type": "Attr", "node": {"type": "Var", "name": "rn"}, "key": "minted"}, {"type": "Lit", "value": 0.0}]},
            "b": {"type": "Lit", "value": 0.5}},
        "effects": [
            ["set_rule_clause", {"__term__": {"type": "Attr", "node": {"type": "Var", "name": "rn"}, "key": "id"}},
             "__mint__", {"__term__": {"type": "Var", "name": "rn"}}],
            ["set_attr", "rn", "minted", 1.0],
        ],
    })

    n0 = a.inner.rule_count()
    print("SELF-BUILD slice — the agent mints a live rule from a Rule node it composed.\n")
    print(f"  before: probe.out={s.node(t)['attrs'].get('out')!r}; rule_count={n0}")
    a.inner.run_rules(500)
    n1 = a.inner.rule_count()
    out1 = s.node(t)["attrs"].get("out")
    print(f"  after run_rules: probe.out={out1!r} (expect 'minted' — the minted rule fired LIVE); rule_count={n1} (expect {n0}+1)")
    # idempotence: run again, must NOT mint a duplicate
    a.inner.set_attr(minter, "x", 1.0)  # touch to allow another pass
    a.inner.run_rules(500)
    n2 = a.inner.rule_count()
    print(f"  re-run: rule_count={n2} (expect still {n0}+1 — idempotent, +1 not +N)")

    ok = out1 == "minted" and n1 == n0 + 1 and n2 == n0 + 1
    print(f"\n  {'PASS' if ok else 'FAIL'} — the agent composed a Rule node and MINTED it into a live struct "
          f"rule that fired the same session, idempotently. This is the create-twin of set_rule_clause — the "
          f"agent can now build its own live rules (and persist them to its library).")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
