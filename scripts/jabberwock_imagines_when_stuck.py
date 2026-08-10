#!/usr/bin/env python3
"""jabberwock_imagines_when_stuck -- TIER 3 COGNITION gate, console form.

Companion to tests/test_imagination_cognition.py (the fast pytest
regression this script's assertions mirror). Demonstrates, on a real
booted agent, that active cognition -- an escalated Impasse, `kind`
`grounding_gap` OR `cost_worth_refining`, the SAME two arms
`seeds/composer_grounding_guard_graph.json` / `seeds/composer_escalation_
gate_graph.json` already mint `agent -surprised_by-> impasse` into -- now
IMAGINES a detached counterfactual before/alongside re-grinding, instead
of only re-grinding (`seeds/autonomy.json`'s standing `mint_goal_from_
surprise`).

Nothing here hand-authors the engage/judge rules -- both are minted live
by the agent's own composer (`ground_concern([...,"imagine",...])` ->
`seeds/composer_imagination_graph.json`'s meta-rule), read back and
printed verbatim. `domains/imagination_dispatch.py:scan_and_imagine` is
the ONLY host-side call this script makes beyond graph I/O -- the
mechanical hook that runs what the agent's rule requested (`imagine()`/
`reground()` cannot execute inside a Rust rule effect).
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.boot_core import boot_core                    # noqa: E402
from substrate.seed_loader import manifest_for                # noqa: E402
import domains.reflective_faculty as rf                        # noqa: E402
from domains import grounding_reach as gr                      # noqa: E402
from domains import imagination_dispatch as idisp              # noqa: E402


class _Agent:
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


def _fresh_agent(*, with_autonomy=True):
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    ag.s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag.agent)
    ag.s._inner.load_seed_manifest(manifest_for("composer_dispatch"), ag.agent)
    if with_autonomy:
        ag.s._inner.load_seed_manifest(manifest_for("autonomy"), ag.agent)
    return ag


def _ground(ag, cue_clause, name_hint):
    ind = rf.induce_concern(ag, [cue_clause], name_hint=name_hint)
    assert ind.get("minted") is True, ind
    g = rf.ground_concern(ag, [ind["capability_key"]])
    assert g.get("grounded") is True and g.get("served_by") == "graph", g
    return g


def _install_guard_and_gate(ag):
    """Author BOTH escalation arms + the imagination engage/judge rules --
    everything via ground_concern's composer, nothing hand-installed."""
    g1 = _ground(ag, ["escalate", "COLLAPSE", "when", "UNGROUNDED"], "grounding_guard_demo")
    g2 = _ground(ag, ["worth", "REFINEMENT", "by", "RESIDUAL_MINUS_COST"], "escalation_gate_demo")
    g3 = _ground(ag, ["imagine", "COLLAPSE", "from", "IMPASSE"], "imagination_demo")
    return g1, g2, g3


def _install_survive_discard_fixture(ag):
    """The SAME shape tests/test_imagination.py's own fixture rules use
    (`_install_contradiction_rules`/`_install_revise_rule`), keyed on the
    "contradicts" edge the agent's OWN authored engage rule's hypothesis_
    template already wires from the injected Hypothesis to the resolved
    focus. Two outcomes from ONE `h -contradicts-> foc` edge:
      - `derive_conclusion_when_ungrounded`: mints a brand-new Conclusion
        node (kind node_added) -- always SURVIVES reground (nothing live
        to contradict by identity).
      - `mutate_implied_when_ungrounded`: sets a DIFFERENT, live-GROUNDED
        node's attr (kind node_changed) -- DISCARDED by reground (it
        contradicts a grounded live fact)."""
    def _foc_ungrounded():
        return {"type": "Eq", "a": {"type": "Count", "source": {
            "type": "Neighbours", "node": {"type": "Var", "name": "foc"},
            "edge_type": "grounded_in"}}, "b": {"type": "Lit", "value": 0}}

    def _not_yet(var, edge_type):
        return {"type": "Eq", "a": {"type": "Count", "source": {
            "type": "Neighbours", "node": {"type": "Var", "name": var},
            "edge_type": edge_type}}, "b": {"type": "Lit", "value": 0}}

    ag.s.add_node("Rule", {
        "id": "derive_conclusion_when_ungrounded",
        "match": [["h", "contradicts", "foc"]],
        "where": {"type": "And", "items": [_foc_ungrounded(), _not_yet("h", "yields")]},
        "effect": [["add_node", "c", "Conclusion", {"derived_from_imagination": True}],
                   ["add_edge", "h", "yields", "c", {}]],
    })
    ag.s.add_node("Rule", {
        "id": "mutate_implied_when_ungrounded",
        "match": [["h", "contradicts", "foc"], ["foc", "implies", "tgt"]],
        "where": {"type": "And", "items": [_foc_ungrounded(), _not_yet("h", "revised")]},
        "effect": [["set_attr", "tgt", "value", "MUTATED_BY_IMAGINATION"],
                   ["add_edge", "h", "revised", "tgt", {}]],
    })


def _mk_grounding_gap_scenario(ag):
    """A confident-but-ungrounded Collapse node (`foc`), structurally
    linked (`implies`) to a SEPARATE, live-GROUNDED Fact (`tgt`) -- the
    survive/discard fork the fixture rules above key on."""
    s = ag.s
    anchor = s.add_node("RealityAnchor", {})
    tgt = s.add_node("Fact", {"value": "blue"})
    s._inner.add_edge_unchecked(tgt, "grounded_in", anchor)
    foc = s.add_node("Collapse", {"residual": 0.01, "confidence": 0.97})
    s._inner.add_edge_unchecked(foc, "implies", tgt)
    return {"anchor": anchor, "tgt": tgt, "foc": foc}


def main() -> int:
    print("=" * 78)
    print("TIER 3 -- imagine-on-escalation, graph-authored (CLAUDE.md discipline)")
    print("=" * 78)

    # ---- CONTRAST: escalation WITHOUT the imagination composer -----------
    print("\n--- CONTRAST: escalation without the imagination engage rule ---")
    ag0 = _fresh_agent()
    _ground(ag0, ["escalate", "COLLAPSE", "when", "UNGROUNDED"], "contrast_guard")
    n0 = _mk_grounding_gap_scenario(ag0)
    gr.ensure_grounding_edges(ag0)
    gr.flag_ungrounded_confident(ag0, node_types=["Collapse"])
    rf.ensure_grounding_gap_edges(ag0)
    ag0.inner.run_rules(2000)
    impasses0 = list(ag0.s.nodes("Impasse"))
    requests0 = list(ag0.s.nodes("ImagineRequest"))
    print(f"Impasse count: {len(impasses0)}  ImagineRequest count: {len(requests0)}")
    assert len(impasses0) >= 1, "the guard must still escalate"
    assert len(requests0) == 0, "WITHOUT the engage rule, no imagination fires -- only re-grind"
    print("CONFIRMED: escalation alone (no engage rule) never imagines -- only re-grinds "
          "(mint_goal_from_surprise, unchanged, still turns the impasse into a wanted Goal).")

    # ---- THE REAL PIPELINE -------------------------------------------------
    print("\n--- ACTIVE COGNITION NOW IMAGINES ---")
    ag = _fresh_agent()
    g1, g2, g3 = _install_guard_and_gate(ag)
    print(f"\nAUTHORED (grounding_guard):  path={g1['path']}  served_by={g1['served_by']}")
    print(f"AUTHORED (escalation_gate):  path={g2['path']}  served_by={g2['served_by']}")
    print(f"AUTHORED (imagination):      path={g3['path']}  served_by={g3['served_by']}")
    for r in g3["rules"]:
        print(f"\n  RULE {r['name']!r}")
        print(f"    match : {r['match']}")
        print(f"    where : {r['where']}")
        print(f"    effect: {r['effects']}")

    _install_survive_discard_fixture(ag)
    n = _mk_grounding_gap_scenario(ag)

    gr.ensure_grounding_edges(ag)
    gr.flag_ungrounded_confident(ag, node_types=["Collapse"])
    rf.ensure_grounding_gap_edges(ag)
    ag.inner.run_rules(2000)

    impasses = list(ag.s.nodes("Impasse"))
    requests = [r for r in ag.s.nodes("ImagineRequest")]
    print(f"\nImpasse count: {len(impasses)}   ImagineRequest count (before scan): {len(requests)}")
    assert len(requests) >= 1, "the engage rule must mint an ImagineRequest on escalation"
    req_kinds = {ag.s.node(r)["attrs"].get("kind") for r in requests}
    print(f"ImagineRequest kinds seen: {sorted(req_kinds)}")
    assert "grounding_gap" in req_kinds

    touched = idisp.scan_and_imagine(ag)
    print(f"scan_and_imagine processed: {len(touched)} request(s)")
    assert len(touched) >= 1

    imaginations = list(ag.s.nodes("Imagination"))
    conclusions = list(ag.s.nodes("ImaginedConclusion"))
    print(f"Imagination trace nodes: {len(imaginations)}   ImaginedConclusion nodes: {len(conclusions)}")
    assert imaginations and conclusions, "the imagination + conclusion trace must appear"

    # ---- run again so the agent's own judge rule fires on the new edges --
    ag.inner.run_rules(2000)

    survived = [c for c in conclusions if ag.s.has_node(c) and ag.s.node(c)["attrs"].get("status") == "survived"]
    discarded = [c for c in conclusions if ag.s.has_node(c) and ag.s.node(c)["attrs"].get("status") == "discarded"]
    print(f"\nreground verdicts -- survived: {len(survived)}  discarded: {len(discarded)}")
    assert survived and discarded, "the fixture must produce BOTH a survivor and a discard"

    acted_survived = [c for c in survived if ag.s.node(c)["attrs"].get("acted") is True]
    acted_discarded = [c for c in discarded if ag.s.node(c)["attrs"].get("acted") is True]
    print(f"JUDGE acted on survivors: {len(acted_survived)}/{len(survived)}   "
          f"acted on discarded: {len(acted_discarded)}/{len(discarded)}")
    assert len(acted_survived) == len(survived), "every survivor must be acted on"
    assert len(acted_discarded) == 0, "no discarded conclusion may ever be acted on"

    print(f"agent -wants_to_commit-> imagination: {ag.s.has_edge(ag.agent, 'wants_to_commit', imaginations[0])}")

    # ---- reversibility: the LIVE domain fact is untouched -----------------
    live_value = ag.s.node(n["tgt"])["attrs"]["value"]
    print(f"\nlive Fact value after imagination + judge: {live_value!r} (must still be 'blue')")
    assert live_value == "blue", "imagine()/reground()/the judge rule must never mutate live domain facts"

    print("\n" + "=" * 78)
    print("PASS -- active cognition imagines on escalation; survivors acted on, "
          "fantasies dropped; reversibility preserved.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
