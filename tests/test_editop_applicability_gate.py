"""test_editop_applicability_gate — SHAPE_AUDIT.md §2.1 site A4: applicability
as a genuine INPUT to the `_compose_structural_variant` EditOp Argmax, not
just a post-hoc execution check.

Companion to `tests/test_structural_variant.py` (which this rung does not
touch — see `EDIT_OP_APPLICABILITY_GATE_PREREG.md`'s correction: those tests
route through `ground_concern`, which for a 'test'-anchored concern always
resolves via the GRAPH-RESIDENT twin `composer_experiment_graph.json`
(`served_by: "graph"`), never reaching `_compose_structural_variant` at all
— confirmed live, see `test_ground_concern_does_not_reach_compose_structural_variant`
below). This file exercises `_compose_structural_variant` DIRECTLY — the
only way to test the code this rung actually changed.

The defect (`RULES_AS_SHAPE_DESIGN_SPIKE.md` §4.2's MAC/FAC diagnosis,
verbatim for this site): `_EDIT_OPS`'s four kinds were Argmax-ranked purely
by `StringIndexOf` keyword overlap against a hand-written blurb, with no
structural input — so a rule for which one op is a GUARANTEED NULL (e.g.
`drop_match_edge` on a rule with only one match edge) could still WIN the
Argmax purely because a concern's words happened to overlap its blurb more
than any applicable op's blurb, wasting the pick.

The fix: `_editop_applicable_kinds(rule_json, edit_ops)` computes, in Python,
from the ALREADY-RESOLVED `rule_json` dict (the same data `_pick_acting_rule`
already produced), which of the four kinds are structurally possible on this
rule (reusing `edit_ops.find_comparison_nodes` / `find_attr_keys` / `len(match)`
— the SAME predicates the post-hoc apply branches already used). That list
becomes an `Or(Eq(kind, ...))` predicate feeding a `Filter` that restricts the
EditOp Argmax's candidate set — mirroring `_pick_acting_rule`'s own
`skippable`-restriction `Filter` precedent — BEFORE the keyword-overlap
Argmax runs. The keyword signal itself is unchanged; only the candidate set
narrows to what could possibly succeed.
"""
from __future__ import annotations

import json
import os

import pytest

from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for
import domains.reflective_faculty as rf
import domains.edit_ops as eo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_GRID_NAV = json.load(open(os.path.join(ROOT, "seeds", "grid_navigation.json")))
_HOP = next(r for r in _GRID_NAV["rules"] if r["name"] == "hop_descend_gradient")
_FOOTPRINT = next(r for r in _GRID_NAV["rules"] if r["name"] == "mark_visited_footprint")


class _Agent:
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


def _fresh_agent_with_lexicon() -> _Agent:
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    ag.s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag.agent)
    return ag


def _agent_with_grid_navigation() -> _Agent:
    ag = _fresh_agent_with_lexicon()
    ag.s._inner.load_seed_manifest(manifest_for("grid_navigation"), ag.agent)
    ag.s.add_node("SeedSummary", {"seed_id": "grid_navigation",
                                  "keywords_text": "grid navigation gradient hop descend row col",
                                  "skippable": 1.0})
    return ag


def _mint_axis(ag, key, residual):
    ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": [key], "induced": 1.0,
        "residual_predicates": list(residual),
        "from_observation": 1.0, "source": "concern_induction",
    })


# ---------------------------------------------------------------------------
# 1 — `_editop_applicable_kinds` itself: a pure, mechanical read reusing the
#     SAME predicates the post-hoc apply branches already used.
# ---------------------------------------------------------------------------
def test_applicable_kinds_on_hop_descend_gradient():
    # single match edge -> drop_match_edge inapplicable; 4 comparison nodes
    # and row/col (4 refs each) -> flip_comparison + swap_term_leaf applicable;
    # non-empty match[0] -> add_match_guard applicable.
    kinds = rf._editop_applicable_kinds(_HOP, eo)
    assert set(kinds) == {"flip_comparison", "swap_term_leaf", "add_match_guard"}
    assert "drop_match_edge" not in kinds


def test_applicable_kinds_on_mark_visited_footprint():
    # 2 match edges -> drop_match_edge applicable here (the sibling rule
    # where it ISN'T inert — confirms the predicate is rule-specific, not a
    # blanket exclusion of drop_match_edge).
    assert len(_FOOTPRINT["match"]) == 2
    kinds = rf._editop_applicable_kinds(_FOOTPRINT, eo)
    assert "drop_match_edge" in kinds


def test_applicable_kinds_empty_on_a_degenerate_rule():
    degenerate = {"name": "degenerate", "match": [], "where": None, "effects": []}
    assert rf._editop_applicable_kinds(degenerate, eo) == []


# ---------------------------------------------------------------------------
# 2 — ground_concern does NOT reach _compose_structural_variant for a
#     'test'-anchored concern (discovered during this rung's own baseline
#     capture; registered in the PREREG's correction). This is why every
#     test below calls _compose_structural_variant DIRECTLY.
# ---------------------------------------------------------------------------
def test_ground_concern_does_not_reach_compose_structural_variant():
    ag = _agent_with_grid_navigation()
    _mint_axis(ag, "gc_probe", ["test", "send", "judge", "structure", "gradient", "flip"])
    res = rf.ground_concern(ag, ["gc_probe"])
    assert res.get("served_by") == "graph", (
        "if this ever changes (the graph-resident twin no longer shadows A4), "
        "test_structural_variant.py's ground_concern-routed assertions would "
        "start exercising _compose_structural_variant and this rung's PREREG "
        "correction would need revisiting")


# ---------------------------------------------------------------------------
# 3 — THE LIVE DEMONSTRATION: a residual that keyword-favours the
#     INAPPLICABLE op (drop_match_edge, on hop_descend_gradient's single
#     match edge) by the widest margin, while an APPLICABLE op
#     (flip_comparison) scores second-best and nonzero.
#
#     "OLD" is reconstructed explicitly (the unfiltered Argmax over ALL four
#     _EDIT_OPS blurbs, the exact StringIndexOf-substring-count shape the
#     pre-fix Argmax used) rather than by literally reverting the code, so
#     the comparison survives as a permanent regression check: if a future
#     edit ever re-widens the candidate set back to all four kinds
#     unconditionally, this test's OLD-reconstruction assertion still holds
#     but the NEW assertion (calling the real function) would fail, catching
#     the regression.
# ---------------------------------------------------------------------------
_DEMO_RESIDUAL = ["test", "send", "judge", "structure", "gradient",
                  "drop", "match", "edge", "gate"]


def _old_unfiltered_argmax_kind(residual):
    """Reconstruction of the PRE-FIX selection rule: Argmax over ALL FOUR
    _EDIT_OPS by StringIndexOf-substring overlap count, no applicability
    filter — byte-identical in spirit to the Term
    `_compose_structural_variant` built before this rung (Filter absent)."""
    best_kind, best_score = None, -1
    for op in rf._EDIT_OPS:
        score = sum(1 for w in residual if w in op["keywords_text"])
        if score > best_score:
            best_kind, best_score = op["kind"], score
    return best_kind, best_score


def test_old_reconstruction_would_pick_the_inapplicable_op():
    kind, score = _old_unfiltered_argmax_kind(_DEMO_RESIDUAL)
    assert kind == "drop_match_edge" and score == 3
    # and it really is inapplicable to hop_descend_gradient:
    assert "drop_match_edge" not in rf._editop_applicable_kinds(_HOP, eo)
    # confirmed via the mechanical applier itself: a guaranteed null
    assert eo.apply_drop_match_edge(_HOP, 0, "would_be_null") is None


def test_new_behavior_picks_the_applicable_op_and_succeeds():
    ag = _agent_with_grid_navigation()
    _mint_axis(ag, "demo_gate", _DEMO_RESIDUAL)
    sv = rf._compose_structural_variant(ag, ["demo_gate"], "demo")
    print("\nNEW _compose_structural_variant result:", json.dumps(sv, default=str))
    assert sv.get("built") is True, sv
    assert sv.get("kind") == "flip_comparison"
    assert sv.get("removed_rule") == "hop_descend_gradient"
    assert sv.get("rule") is not None


def test_wall_message_names_the_applicability_restriction_on_pure_abstain():
    # 'drop' alone: no OTHER op's blurb overlaps a bare "drop", so after
    # filtering out the inapplicable drop_match_edge, every remaining
    # candidate scores 0 and the (unchanged) abstain-on-zero wrapper fires —
    # an honest abstain BEFORE a doomed op is ever picked, not a fabricated
    # substitute pick.
    ag = _agent_with_grid_navigation()
    _mint_axis(ag, "drop_alone", ["test", "send", "judge", "structure", "gradient", "drop"])
    sv = rf._compose_structural_variant(ag, ["drop_alone"], "dropalone")
    assert sv.get("built") is False
    assert sv.get("kind") is None
    assert "APPLICABLE" in sv.get("wall", "")
    assert "drop_match_edge" not in sv.get("wall", "")   # never named as a candidate


def test_no_applicable_kind_at_all_abstains_before_any_argmax():
    # A synthetic RuleSummary whose rule_json is inert for ALL four ops:
    # no comparison nodes, <2 distinct Attr keys, <=1 match edge. Reached by
    # directly minting a RuleSummary (bypassing _ensure_acting_rule_provenance's
    # real-rule scan) so _pick_acting_rule's Argmax can pick it.
    ag = _fresh_agent_with_lexicon()
    degenerate_rule = {
        "name": "degenerate_acting_rule",
        "match": [],
        "where": None,
        "effects": [],
    }
    assert rf._editop_applicable_kinds(degenerate_rule, eo) == []   # sanity: truly all-inapplicable
    ag.s.add_node("RuleSummary", {
        "name": "degenerate_acting_rule",
        "keywords_text": "degenerate acting rule structure flip",
        "writes_chosen_action": 1.0,
        "skippable": 1.0,
        "shift_count": 0.0,
        "rule_json": json.dumps(degenerate_rule),
        "from_seed": "",
    })
    _mint_axis(ag, "degenerate_probe", ["structure", "flip", "degenerate"])
    sv = rf._compose_structural_variant(ag, ["degenerate_probe"], "deg")
    print("\nAll-inapplicable result:", json.dumps(sv, default=str))
    assert sv.get("built") is False
    assert "structurally applicable" in sv.get("wall", "")
    assert "Argmax" in sv.get("wall", "")
