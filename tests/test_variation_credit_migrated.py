"""OUTCOME-CREDITED VARIATION POLICY — gate for seeds/variation_credit.json and
variation_ops v1.5.0 (RECURSIVE_SELF_IMPROVEMENT_PLAN_20261006.md WP2).

Pinned claims:
  * without a VariationPolicy node, variation_pick is unchanged;
  * judged experiments are credited to VariationCredit{op, kind} by graph rules,
    with derived trials/supports;
  * exclude_refuted stops a refuted family being retried for the same concern;
  * use_credit changes the FIRST choice for a NEW concern of the same kind
    (the improver's choice learns from its own outcomes) -- and only for that
    kind; use_credit=0 is a frozen policy over the same evidence.
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from domains.variation_credit_lab import VariationLab  # noqa: E402

CONVO = ["test", "replay", "send", "judge", "adopt"]


def test_no_policy_node_pick_is_unchanged():
    lab = VariationLab(credit=False)
    assert not list(lab.s.nodes("VariationPolicy"))
    assert lab.pick(lab.concern("reply_fix"), CONVO) == "reply_ablation"
    assert lab.pick(lab.concern("instruction"), CONVO) == "cue_set_edit"
    assert lab.pick(lab.concern("x")) == "knob_edit"            # lowest priority among all-eligible


def test_policy_with_no_history_is_unchanged():
    lab = VariationLab(credit=True)
    assert lab.pick(lab.concern("reply_fix"), CONVO) == "reply_ablation"
    assert lab.pick(lab.concern("x")) == "knob_edit"


def test_judged_experiment_is_credited_with_derived_counts():
    lab = VariationLab(credit=True)
    k = lab.concern("reply_fix")
    lab.trial(k, "knob_edit", "refuted")
    lab.trial(lab.concern("reply_fix"), "knob_edit", "supported")
    lab.trial(lab.concern("reply_fix"), "knob_edit", "inconclusive")
    assert lab.credits()[("knob_edit", "reply_fix")] == (3, 1)


def test_unjudged_experiment_is_not_credited():
    lab = VariationLab(credit=True)
    k = lab.concern("reply_fix")
    exp = lab.s.add_node("Experiment", {"status": "requested", "axis_tag": k})
    d = lab.s.add_node("SeedDelta", {"variation_op": "knob_edit", "concern_key": k})
    lab.native.add_edge_unchecked(exp, "has_delta", d)
    lab.native.run_rules()
    assert lab.credits() == {}


def test_refuted_family_is_not_retried_for_the_same_concern():
    lab = VariationLab(credit=True)
    k = lab.concern("reply_fix")
    assert lab.pick(k) == "knob_edit"
    lab.trial(k, "knob_edit", "refuted")
    assert lab.pick(k) != "knob_edit"


def test_frozen_policy_retries_nothing_but_does_not_learn():
    lab = VariationLab(credit=True, use_credit=False)
    for _ in range(3):
        assert lab.episode("reply_fix", fixes="shape_mint") == ["knob_edit", "datum_feedback_rule", "shape_mint"]


def test_credit_changes_the_first_choice_for_a_new_concern_of_that_kind_only():
    lab = VariationLab(credit=True)
    first = lab.episode("reply_fix", fixes="shape_mint")
    assert first == ["knob_edit", "datum_feedback_rule", "shape_mint"]
    assert lab.episode("reply_fix", fixes="shape_mint") == ["shape_mint"]
    assert lab.pick(lab.concern("comprehension")) == "knob_edit", "credit is per concern kind"


def test_credit_recovers_when_the_world_changes():
    lab = VariationLab(credit=True)
    for _ in range(3):
        lab.episode("reply_fix", fixes="shape_mint")
    tries = [len(lab.episode("reply_fix", fixes="knob_edit")) for _ in range(6)]
    assert tries[-1] == 1, tries


def test_recency_window_forgets_old_supports():
    lab = VariationLab(credit=True, window=2)
    for _ in range(5):
        lab.episode("reply_fix", fixes="shape_mint")
    assert lab.credits()[("shape_mint", "reply_fix")] == (2, 2)
    lab.episode("reply_fix", fixes="knob_edit")
    t, s = lab.credits()[("shape_mint", "reply_fix")]
    assert (t, s) == (2, 1), "a refute displaces the oldest support from a window of 2"


def test_no_window_attr_counts_whole_history():
    lab = VariationLab(credit=True)
    assert all(lab.s.node(p)["attrs"].get("window") is None for p in lab.s.nodes("VariationPolicy"))
    for _ in range(5):
        lab.episode("reply_fix", fixes="shape_mint")
    assert lab.credits()[("shape_mint", "reply_fix")][0] >= 5


# --- tranche 9: opt-in exclude_inconclusive / credit_internal_exempt ------------

def _set_policy(lab, **kv):
    for p in lab.s.nodes("VariationPolicy"):
        for k, v in kv.items():
            lab.s.set_attr(p, k, v)


def test_inconclusive_family_is_retried_unless_policy_excludes_it():
    lab = VariationLab(credit=True, use_credit=False)
    k = lab.concern("reply_fix")
    lab.trial(k, "knob_edit", "inconclusive")
    assert lab.pick(k) != "knob_edit", "default since variation_credit v1.2.0: inconclusive excludes"
    _set_policy(lab, exclude_inconclusive=0)
    assert lab.pick(k) == "knob_edit", "policy off: an inconclusive family is retried"


def test_retry_internal_trial_with_alternative_is_not_charged_in_its_own_concern():
    """cue_set_edit (priority 10, retry_internal) vs reply_ablation edited to 8:
    after one inconclusive reply_ablation and one refuted routed cue_set_edit
    on the SAME concern, per-trial credit scores cue_set_edit 10*4/3 against
    reply_ablation 8*4/3 and leaves the family; the exemption scores
    cue_set_edit 10*1 in this concern only, so its next route is tried."""
    lab = VariationLab(credit=True)
    _set_policy(lab, credit_internal_exempt=0, exclude_inconclusive=0)   # start from per-trial credit
    for n in lab.s.nodes("VariationOp"):
        if lab.s.node(n)["attrs"].get("name") == "reply_ablation":
            lab.s.set_attr(n, "priority", 8)
    k = lab.concern("instruction")
    lab.trial(k, "reply_ablation", "inconclusive")
    assert lab.pick(k, CONVO) == "cue_set_edit"
    _e, d = lab.trial(k, "cue_set_edit", "refuted")
    lab.s.set_attr(d, "cue_route", "comprehend_text")
    assert lab.pick(k, CONVO) == "reply_ablation", "per-trial credit leaves the family"
    _set_policy(lab, credit_internal_exempt=1)
    assert lab.pick(k, CONVO) == "cue_set_edit"
    # a NEW concern of the same kind is still charged for that trial
    k2 = lab.concern("instruction")
    assert lab.credits()[("cue_set_edit", "instruction")] == (1, 0)
    assert lab.pick(k2, CONVO) == "reply_ablation"


def test_tranche9_policy_is_the_seed_default():
    lab = VariationLab(credit=True)
    pol = [lab.s.node(p)["attrs"] for p in lab.s.nodes("VariationPolicy")]
    assert pol and pol[0].get("credit_internal_exempt") == 1 and pol[0].get("exclude_inconclusive") == 1


# --- tranche 11: an abstained (empty) variant is not a trial --------------------

def test_abstained_variant_is_closed_uncredited_and_excluded():
    from domains import reflective_faculty as rf
    lab = VariationLab(credit=True)
    rf._ensure_seed_chain(lab.s, lab.native, lab.ag, ("self_optimisation",))   # close_abstained_variant lives there
    k = lab.concern("reply_fix")
    assert lab.pick(k) == "knob_edit"
    exp = lab.s.add_node("Experiment", {"status": "requested", "axis_tag": k})
    d = lab.s.add_node("SeedDelta", {"variation_op": "knob_edit", "concern_key": k, "variant_abstained": 1.0})
    lab.native.add_edge_unchecked(exp, "has_delta", d)
    lab.native.run_rules()
    at = lab.s.node(exp)["attrs"]
    assert at.get("status") == "done" and at.get("outcome") == "abstained"
    assert lab.credits() == {}, "an empty delta is never credited"
    assert lab.pick(k) != "knob_edit", "the abstaining family is not re-picked for this concern"
    assert lab.pick(lab.concern("reply_fix")) == "knob_edit", "other concerns are unaffected"
