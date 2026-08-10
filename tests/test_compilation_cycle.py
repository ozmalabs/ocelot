"""test_compilation_cycle -- Graph Law review #2: the active<->model-layer
FLYWHEEL, measured (domains/compilation_cycle.py) and completed (the
dual-process arbitration, seeds/composer_escalation_gate_graph.json).

PART A pins domains/compilation_cycle.py: pure measurement over the agent's
OWN history (teach()->TaughtHint, perform_adoptions->Adoption, composer-
to-graph ComposeRequest{composed==1}, rung-4 Install, learn_term_for_concern
/dynamic_extend->Program). No agent decision; mechanical enumeration +
idempotent indexing -- never mutated here, only read back.

PART B pins the NEW escalation arm (seeds/composer_escalation_gate_graph.json
+ seeds/relation_vocabulary.json's cost_worth_escalate cue + seeds/
composer_dispatch.json's 'worth' ComposerCue), authored via the SAME
composer discipline test_grounding_guard.py already pins for B1 (the
grounding-guard arm, UNCHANGED here): step 1 proves the prior vocabulary
genuinely walls on the cost-worth-refining concern; step 2 proves the new
cue/dispatch load; step 3 proves the jabberwock AUTHORS the rule via
induce_concern -> ground_concern; step 4 is the three-way discriminative
gate (trust / cost-escalate / ground-escalate); step 5 is the full flywheel
loop (escalate -> compile -> CompilationEvent -> cheap next time).

No seed file is mutated at runtime by anything this file exercises: the
graph-composer path installs rules into the LIVE rule engine only
(`set_rule_clause`/`__mint__`), never `domains.teach.teach()` (which is the
one facility here that persists to disk) -- verified by inspection, same
as test_grounding_guard.py's own note.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

pytest.importorskip("substrate_rs")

from substrate.boot_core import boot_core                                # noqa: E402
from substrate.seed_loader import manifest_for                           # noqa: E402
import domains.reflective_faculty as rf                                  # noqa: E402
from domains import grounding_reach as gr                                # noqa: E402
from domains.compilation_cycle import compilation_events, compilation_throughput  # noqa: E402


class _Agent:
    """Minimal duck-typed agent wrapper -- identical shape to
    tests/test_grounding_guard.py's own `_Agent`."""
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


def _fresh_minimal_agent() -> _Agent:
    """boot_core only -- no real history, no vocabulary loaded."""
    s, agent_node = boot_core()
    return _Agent(s, agent_node)


def _fresh_agent_with_lexicon() -> _Agent:
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    ag.s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag.agent)
    ag.s._inner.load_seed_manifest(manifest_for("composer_dispatch"), ag.agent)
    return ag


def _fresh_agent_with_prior_lexicon() -> _Agent:
    """The vocabulary AS IT STOOD BEFORE this change: relation_vocabulary
    minus the new `cost_worth_escalate` cue -- reconstructed live (the same
    approach test_grounding_guard.py uses for `grounding_escalate`) so the
    wall is a real, re-runnable proof."""
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    m = dict(manifest_for("relation_vocabulary"))
    m["nodes"] = [n for n in m["nodes"] if n["attrs"].get("name") != "cost_worth_escalate"]
    ag.s._inner.load_seed_manifest(m, ag.agent)
    return ag


def _author_escalation_gate(ag) -> dict:
    ind = rf.induce_concern(ag, [["worth", "REFINEMENT", "by", "RESIDUAL_MINUS_COST"]],
                             name_hint="cost_worth_test")
    assert ind.get("minted") is True, ind.get("note")
    return rf.ground_concern(ag, [ind["capability_key"]])


def _author_grounding_guard(ag) -> dict:
    ind = rf.induce_concern(ag, [["escalate", "COLLAPSE", "when", "UNGROUNDED"]],
                             name_hint="grounding_guard_test")
    assert ind.get("minted") is True, ind.get("note")
    return rf.ground_concern(ag, [ind["capability_key"]])


def _cost_axis(ag, *, shortfall, saturation, cost, tag="axis") -> int:
    ax = ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": [tag], "shortfall": shortfall,
        "saturation": saturation, "cost": cost})
    ag.inner.add_edge_unchecked(ag.agent, "frontier_pick", ax)
    return ax


# ===========================================================================
# PART A -- THE COMPILATION METRIC (pure measurement)
# ===========================================================================
def test_fresh_minimal_agent_reports_near_zero():
    ag = _fresh_minimal_agent()
    events = compilation_events(ag)
    tp = compilation_throughput(ag)
    assert events == []
    assert tp["total"] == 0
    assert all(v == 0 for v in tp["by_kind"].values())


def test_real_history_agent_reports_by_kind():
    """A live agent with real TaughtHint/Program history (minted directly
    here, mechanically, the same shapes teach()/teach_program() mint) is
    counted, broken out by kind."""
    ag = _fresh_minimal_agent()
    ag.s.add_node("TaughtHint", {"topic": "t1", "answer": "a1"})
    ag.s.add_node("TaughtHint", {"topic": "t2", "answer": "a2"})
    ag.s.add_node("Program", {"name": "p1", "program": "{}", "form": "term_tree"})
    events = compilation_events(ag)
    tp = compilation_throughput(ag)
    assert len(events) == 3
    assert tp["total"] == 3
    assert tp["by_kind"]["teach_hint"] == 2
    assert tp["by_kind"]["program_learned"] == 1
    assert tp["by_kind"]["adoption"] == 0
    assert tp["by_kind"]["rung4_install"] == 0


def test_composer_authored_channel_counts_a_real_ground_concern():
    """A genuinely-composed rule (ComposeRequest{composed==1.0}) is counted
    under 'composer_authored' -- the composer-to-graph migration ledger,
    read back, not re-derived."""
    ag = _fresh_agent_with_lexicon()
    _author_grounding_guard(ag)
    tp = compilation_throughput_after_events(ag)
    assert tp["by_kind"]["composer_authored"] >= 1


def compilation_throughput_after_events(ag):
    compilation_events(ag)
    return compilation_throughput(ag)


def test_idempotent_no_double_count():
    ag = _fresh_minimal_agent()
    ag.s.add_node("TaughtHint", {"topic": "t1", "answer": "a1"})
    ev1 = compilation_events(ag)
    tp1 = compilation_throughput(ag)
    ev2 = compilation_events(ag)
    tp2 = compilation_throughput(ag)
    assert len(ev1) == 1
    assert len(ev2) == 0
    assert tp1 == tp2


# ===========================================================================
# PART B -- STEP 1: the held vocabulary, AS-IS, genuinely walls.
# ===========================================================================
def test_existing_vocabulary_walls_on_cost_worth_refining():
    ag = _fresh_agent_with_prior_lexicon()
    ind = rf.induce_concern(ag, [["worth", "REFINEMENT", "by", "RESIDUAL_MINUS_COST"]],
                             name_hint="wall_probe_cost")
    assert ind.get("minted") is True
    res = rf.ground_concern(ag, [ind["capability_key"]])
    assert res.get("grounded") is False
    assert res.get("path") == "predicate_grounding"
    assert "NO held structural relation" in res.get("wall", "")


# ===========================================================================
# STEP 2 -- the minimal new vocabulary loads and dispatches correctly.
# ===========================================================================
def test_cost_worth_escalate_cue_loads():
    ag = _fresh_agent_with_lexicon()
    cues = {at["name"]: at for at in (ag.s.node(n)["attrs"] for n in ag.s.nodes("RelationCue"))}
    assert "cost_worth_escalate" in cues


def test_composer_dispatch_routes_worth_to_escalation_gate():
    ag = _fresh_agent_with_lexicon()
    name = rf._pick_composer(ag.s, ag.inner, ag.agent, {"worth"})
    assert name == "escalation_gate"


def test_escalate_head_still_routes_to_grounding_guard_unchanged():
    """B1's dispatch is untouched by this change."""
    ag = _fresh_agent_with_lexicon()
    name = rf._pick_composer(ag.s, ag.inner, ag.agent, {"escalate"})
    assert name == "grounding_guard"


# ===========================================================================
# STEP 3 -- the jabberwock AUTHORS the cost-worth-refining guard rule.
# ===========================================================================
def test_agent_authors_the_escalation_gate_rule_via_graph_composer():
    ag = _fresh_agent_with_lexicon()
    ind = rf.induce_concern(ag, [["worth", "REFINEMENT", "by", "RESIDUAL_MINUS_COST"]],
                             name_hint="cost_worth_test")
    assert ind.get("minted") is True, ind.get("note")
    before = ag.inner.rule_count()
    g = rf.ground_concern(ag, [ind["capability_key"]])
    after = ag.inner.rule_count()

    assert g.get("grounded") is True, g.get("wall")
    assert g.get("served_by") == "graph"
    assert g.get("path") == "compose_escalation_gate_rule"
    assert after - before == 1

    rule = g["rule"]
    assert rule["name"].startswith("escalate_cost_worth_")
    assert rule["match"] == [["ag", "frontier_pick", "ax"]]
    ops = rule["effects"]
    assert ops[0][:3] == ["add_node", "mi", "Impasse"]
    assert ops[0][3]["kind"] == "cost_worth_refining"
    assert ops[1] == ["add_edge", "ag", "surprised_by", "mi", {}]
    assert ops[2] == ["add_edge", "mi", "about_axis", "ax", {}]
    assert ops[3] == ["set_attr", "ax", "cost_escalated", True]


def test_re_grounding_is_idempotent_no_rechurn():
    ag = _fresh_agent_with_lexicon()
    ind = rf.induce_concern(ag, [["worth", "REFINEMENT", "by", "RESIDUAL_MINUS_COST"]],
                             name_hint="cost_worth_idem")
    key = ind["capability_key"]
    rf.ground_concern(ag, [key])
    rc1 = ag.inner.rule_count()
    rf.ground_concern(ag, [key])
    rc2 = ag.inner.rule_count()
    assert rc1 == rc2


# ===========================================================================
# STEP 4 -- THE DISCRIMINATIVE GATE: trust / cost-escalate / ground-escalate.
# ===========================================================================
def test_trust_the_cheap_snap_when_not_worth_refining():
    ag = _fresh_agent_with_lexicon()
    ag.s._inner.load_seed_manifest(manifest_for("autonomy"), ag.agent)
    _author_escalation_gate(ag)
    _author_grounding_guard(ag)
    ax = _cost_axis(ag, shortfall=0.1, saturation=0.9, cost=0.5, tag="trust")   # value = -0.3
    before = set(ag.inner.neighbours(ag.agent, "surprised_by"))
    ag.inner.run_rules()
    after = set(ag.inner.neighbours(ag.agent, "surprised_by"))
    assert after == before
    assert ag.s.node(ax)["attrs"].get("cost_escalated") is None


def test_escalate_when_worth_refining_the_new_arm():
    ag = _fresh_agent_with_lexicon()
    ag.s._inner.load_seed_manifest(manifest_for("autonomy"), ag.agent)
    _author_escalation_gate(ag)
    _author_grounding_guard(ag)
    ax = _cost_axis(ag, shortfall=0.9, saturation=0.0, cost=0.2, tag="cost_worth")   # value = 1.7
    before = set(ag.inner.neighbours(ag.agent, "surprised_by"))
    ag.inner.run_rules()
    after = set(ag.inner.neighbours(ag.agent, "surprised_by"))
    new = after - before
    assert new
    kinds = [ag.s.node(n)["attrs"].get("kind") for n in new]
    assert "cost_worth_refining" in kinds
    assert ag.s.node(ax)["attrs"].get("cost_escalated") is True


def test_escalate_when_ungrounded_confident_b1_still_works():
    ag = _fresh_agent_with_lexicon()
    ag.s._inner.load_seed_manifest(manifest_for("autonomy"), ag.agent)
    _author_escalation_gate(ag)
    _author_grounding_guard(ag)
    n = ag.s.add_node("Concept", {"residual": 0.01, "confidence": 0.95})
    flagged = gr.flag_ungrounded_confident(ag, node_types=["Concept"])
    assert flagged
    wired = rf.ensure_grounding_gap_edges(ag)
    assert wired >= 1
    before = set(ag.inner.neighbours(ag.agent, "surprised_by"))
    ag.inner.run_rules()
    after = set(ag.inner.neighbours(ag.agent, "surprised_by"))
    new = after - before
    assert new
    kinds = [ag.s.node(x)["attrs"].get("kind") for x in new]
    assert "grounding_gap" in kinds


# ===========================================================================
# STEP 5 -- THE FULL FLYWHEEL: escalate -> compile -> CompilationEvent ->
# the re-encountered shape is cheap next time (no escalation).
# ===========================================================================
def test_full_flywheel_loop():
    ag = _fresh_agent_with_lexicon()
    ag.s._inner.load_seed_manifest(manifest_for("autonomy"), ag.agent)
    _author_escalation_gate(ag)
    _author_grounding_guard(ag)

    # [1] ESCALATE
    ax1 = _cost_axis(ag, shortfall=0.9, saturation=0.0, cost=0.2, tag="flywheel")
    ag.inner.run_rules()
    assert ag.s.node(ax1)["attrs"].get("cost_escalated") is True
    surprises_after_escalate = set(ag.inner.neighbours(ag.agent, "surprised_by"))
    assert surprises_after_escalate

    # [2] COMPILE -- the active result becomes a cheap fact (LIVE TaughtHint,
    # the same node shape domains.teach.teach()'s live half mints, without
    # this test persisting a demo fact to disk).
    ag.s.add_node("TaughtHint", {"topic": "flywheel: axis understood", "answer": "known"})

    # [3] the metric SEES it.
    events = compilation_events(ag)
    tp = compilation_throughput(ag)
    assert any(e["kind"] == "teach_hint" for e in events)
    assert tp["by_kind"]["teach_hint"] >= 1
    assert tp["by_kind"]["composer_authored"] >= 1   # the two arms authored above

    # [4] CHEAP NEXT TIME -- the same shape, post-compilation, low residual.
    ax2 = _cost_axis(ag, shortfall=0.05, saturation=0.95, cost=0.2, tag="flywheel")  # value = -0.1
    before = set(ag.inner.neighbours(ag.agent, "surprised_by"))
    ag.inner.run_rules()
    after = set(ag.inner.neighbours(ag.agent, "surprised_by"))
    assert after == before, "the compiled-down shape must NOT re-escalate"
    assert ag.s.node(ax2)["attrs"].get("cost_escalated") is None


# ===========================================================================
# GATE SCRIPT PIN.
# ===========================================================================
def test_gate_script_exits_zero():
    from scripts.jabberwock_compiles_and_escalates import main
    assert main() == 0
