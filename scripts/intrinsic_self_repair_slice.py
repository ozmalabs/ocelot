"""INTRINSIC SELF-REPAIR on the LIVE engine — a rule rewrites a rule, inside run_rules.

The jabberwock's revised design: the agent's live cognition runs STRUCT rules via run_rules (NOT the
dormant graph_rules/Rule-node path). So self-repair must edit a struct rule from inside run_rules. Its
mechanism — realised here — is a new graph-native effect `set_rule_clause(rule_name, field, term)`:

  · a deliberately-broken target STRUCT rule R_target (where=False, so it never fires) — the fault
  · a Fault node carrying the target's name, the field to fix, and the corrected clause as graph data
  · a REPAIR struct rule R_repair: match the Fault; effect set_rule_clause(f.target, f.field, f.corrected)
  · the effect can't touch the rule list from apply (only &mut graph), so it QUEUES the edit on the graph;
    Substrate::run_rules drains it between passes, swaps R_target's `where` in place, recomputes access,
    drops the stale JIT/cursor, marks it dirty — so R_target runs its NEW body the next pass and fires
  · revert = a second set_rule_clause back to the old clause (keep-or-revert, the effect-gate's lever)

No Python orchestrator, no external world, no graph_rules: a struct rule edits a struct rule from inside
the agent's actual run_rules loop. This is the primitive intrinsic self-repair composes from — and the
discriminator (classify_axis_compensated, a struct) is reachable the same way, by name.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/intrinsic_self_repair_slice.py
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
LIT_F = {"type": "Lit", "value": False}


def _attr(var, key):
    return {"type": "Attr", "node": {"type": "Var", "name": var}, "key": key}


def main():
    a = WorldAdapter()                      # the agent's live loop runs STRUCT rules via run_rules
    s = a.s

    g = s.add_node("Anchor", {})
    p = s.add_node("Probe", {})
    a.inner.add_edge_unchecked(g, "has_probe", p)
    h = s.add_node("FaultAnchor", {})
    # the fault as graph data: which rule, which clause, and the corrected clause Term
    f = s.add_node("Fault", {"target_rule": "R_target", "field": "where", "corrected": LIT_T,
                             "applied": 0.0, "about": "R_target never fires; its where gate is False"})
    a.inner.add_edge_unchecked(h, "has_fault", f)

    # the BROKEN target — a STRUCT rule (run by run_rules) whose where=False, so it never fires
    a.inner.add_rule({
        "name": "R_target",
        "match": [["g", "has_probe", "p"]],
        "where": LIT_F,
        "effects": [["set_attr", "p", "out", {"__term__": {"type": "Lit", "value": "ok"}}]],
    })
    # the REPAIR — also a STRUCT rule: when the Fault is unapplied, rewrite the named rule's clause,
    # then mark it applied (single-fire). set_rule_clause reads the target/field/corrected off the Fault.
    a.inner.add_rule({
        "name": "R_repair",
        "match": [["h", "has_fault", "f"]],
        "where": {"type": "Lt", "a": {"type": "Plus", "items": [_attr("f", "applied"),
                                                                {"type": "Lit", "value": 0.0}]},
                  "b": {"type": "Lit", "value": 0.5}},
        "effects": [
            ["set_rule_clause", {"__term__": _attr("f", "target_rule")},
                                {"__term__": _attr("f", "field")},
                                {"__term__": _attr("f", "corrected")}],
            ["set_attr", "f", "applied", 1.0],
        ],
    })

    print("INTRINSIC SELF-REPAIR on the LIVE engine — a struct rule rewrites a struct rule.\n")
    print(f"  before: probe.out = {s.node(p)['attrs'].get('out')!r}   (R_target where=False -> never fires)")

    a.inner.run_rules(5000)                 # the agent's live engine: R_repair rewrites R_target, which then fires
    out = s.node(p)["attrs"].get("out")
    print(f"  after run_rules: probe.out = {out!r}   (R_repair rewrote R_target's where -> True, it fired)")
    repaired = out == "ok"

    # effect-gate REVERT: a second clause-edit puts the old (broken) where back.
    a.inner.set_attr(f, "corrected", LIT_F)
    a.inner.set_attr(f, "applied", 0.0)
    a.inner.run_rules(5000)                 # rewrites R_target.where -> False again
    # now prove the reverted rule no longer fires: clear the probe and run once more.
    a.inner.set_attr(p, "out", None)
    a.inner.run_rules(5000)
    out2 = s.node(p)["attrs"].get("out")
    reverted = out2 is None
    print(f"  effect-gate revert (set the old clause back): probe.out = {out2!r}  (stops firing: {reverted})")

    ok = repaired and reverted
    print(f"\n  {'PASS' if ok else 'FAIL'} — a STRUCT rule rewrote another STRUCT rule's clause from inside "
          f"the agent's live run_rules loop (set_rule_clause effect), and a second edit reverted it. No "
          f"Python orchestrator, no external world, no dormant graph_rules path. The discriminator "
          f"(classify_axis_compensated) is reachable by name the same way.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
