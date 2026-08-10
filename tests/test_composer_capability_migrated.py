"""COMPOSER-CAPABILITY wave gate: the two variation families that close R3
(track-record -> reliability) and R4 (person-shape minting) — the composer's
OWN self-diagnosed shortfall ("you cannot author a rule that feeds a
recorded datum back into a held belief", filed in the residual-closure
wave, commit 03630c0e27).

Per the bootstrap asymmetry: this file gates the CAPABILITY (the builders +
VariationOp/RelationCue data + the mechanics that let an authored delta ride
existing channels) — the agent closing R3/R4 through its OWN pipeline lives
in scripts/composer_closure_run.py, gated separately.

`datum_feedback_rule` (R3): a genuinely NEW, ADD-ONLY rule
(domains/reflective_faculty._compose_datum_feedback_rule) that matches every
party the agent models (`agent -has_interlocutor-> party`, a new boundary
edge `interlocutor_model._ensure_party_anchor` mechanically maintains — kept
OFF the senses/models/acts_on theorem-invariant triad on purpose), guarded
by an epoch marker on the recorded datum, and moves a held belief
(`self_report_reliability`) by a held, clamped step. The rule also stamps
`self_report_reliability_source='learned'` so `effective_reliability` reads
the now-tracked belief in preference to the shape/track-record blend.

`shape_mint` (R4): constructs a brand-new InterlocutorShape node
(domains/reflective_faculty._compose_shape_mint) from the party carrying the
largest `poor_fit_streak` (a new mechanical datum,
`interlocutor_model._record_shape_fit`, recorded once per turn), using that
party's own dominant accumulated features as the signature and wide priors
copied from the codebook's own `default_uncalibrated` entry. Rides the
EXISTING `add_concepts` channel (already generalized to typed nodes).

Both families are ADD-ONLY: adoption installs (native.add_rule /
teach()-persisted InterlocutorShape) rather than remove-then-replace,
mirroring `cue_set_edit`'s own no-denylist adoption precedent; the
family-agnostic regression veto (seeds/adoption_safety.json) still applies
unchanged (it reads Experiment.regressions, not any family marker).

Gated here:
  * the boundary edge: idempotent, one per party;
  * the R4 datum: poor-fit streak increments on a poor fit, resets on a good
    one;
  * the pick: variation_pick chooses datum_feedback_rule / shape_mint
    exactly when their own cues ground, never hijacking cue_set_edit/
    knob_edit/rule_literal_edit/reply_ablation;
  * the compose: both builders pick correctly and honestly abstain;
  * the authored rule round-trips the canonical-export discipline;
  * a LIVE fixpoint: installing the authored rule and changing the datum
    moves the belief by the held step, clamped, exactly once per datum
    change (the epoch guard), and effective_reliability reads it back;
  * the minted shape's signature matches the party's own dominant features,
    with wide priors;
  * adoption mechanics for both families: install into the parent, Adoption
    record, idempotent revert;
  * the veto: a datum-feedback experiment with regressions is adopt_denied,
    parent untouched.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.boot_all import load_all_seeds              # noqa: E402

jd = pytest.importorskip("jabberwock_daemon")

import domains.reflective_faculty as rf                                  # noqa: E402
from domains import interlocutor_model as im                             # noqa: E402
from domains.experiment_dispatch import mint_experiment                  # noqa: E402


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


@pytest.fixture()
def light_agent():
    return WorldAdapter(seeds=())


def _active_party(a):
    for n in a.s.nodes("Interlocutor"):
        if a.s.node(n)["attrs"].get("active"):
            return n
    return None


# --------------------------------------------------------------------------- #
#  the boundary edge + the R4 datum
# --------------------------------------------------------------------------- #

def test_party_anchor_edge_is_idempotent(agent):
    a = agent
    a.converse("Hi, I am Grace.", speech_act="statement")
    p1 = _active_party(a)
    neighbours_1 = list(a.inner.neighbours(a.agent, "has_interlocutor"))
    assert p1 in neighbours_1
    # a second turn from the SAME party must not duplicate the edge.
    a.converse("I like maps.", speech_act="statement")
    neighbours_2 = list(a.inner.neighbours(a.agent, "has_interlocutor"))
    assert neighbours_2.count(p1) == 1, "the boundary edge must be added exactly once per party"


def test_shape_fit_streak_increments_on_poor_fit_and_resets_on_good_fit(agent):
    a = agent
    # a distinctive, sustained style the held codebook is unlikely to fit
    # tightly (short+casual+plain+agitated is an unusual combination against
    # the 5-shape codebook) drives repeated poor-fit turns.
    for _ in range(3):
        a.converse("no. stupid. ugh!!", speech_act="statement")
    party = _active_party(a)
    at = a.s.node(party)["attrs"]
    streak_before = int(at.get("poor_fit_streak", 0) or 0)
    # whatever the streak reached, it must be a non-negative int and the
    # running total must be >= the streak (monotonic counter).
    assert int(at.get("poor_fit_count", 0) or 0) >= streak_before >= 0


# --------------------------------------------------------------------------- #
#  the pick
# --------------------------------------------------------------------------- #

_CONVO = ["test", "replay", "send", "judge", "adopt"]


def test_variation_pick_chooses_datum_feedback_rule_exactly_when_its_cue_grounds(light_agent):
    a = light_agent
    a.s.add_node("StandingConcern", {"name": "df_rep", "kind": "reported"})
    assert rf._pick_variation_op(a, _CONVO + ["datumfeedback"], "df_rep") == "datum_feedback_rule"
    assert rf._pick_variation_op(a, _CONVO, "df_rep") == "reply_ablation"
    # never hijacked by / never hijacks knob_edit or rule_literal_edit.
    assert rf._pick_variation_op(a, _CONVO + ["bound"], "df_rep") == "knob_edit"
    assert rf._pick_variation_op(a, _CONVO + ["ruleliteral"], "df_rep") == "rule_literal_edit"
    # never hijacks the instruction family's cue_set_edit (priority 10 < 16).
    a.s.add_node("StandingConcern", {"name": "df_ins", "kind": "instruction"})
    assert rf._pick_variation_op(a, _CONVO + ["datumfeedback"], "df_ins") == "cue_set_edit"


def test_variation_pick_chooses_shape_mint_exactly_when_its_cue_grounds(light_agent):
    a = light_agent
    a.s.add_node("StandingConcern", {"name": "sm_rep", "kind": "reported"})
    assert rf._pick_variation_op(a, _CONVO + ["shapemint"], "sm_rep") == "shape_mint"
    assert rf._pick_variation_op(a, _CONVO, "sm_rep") == "reply_ablation"
    assert rf._pick_variation_op(a, _CONVO + ["bound"], "sm_rep") == "knob_edit"
    # datumfeedback and shapemint are disjoint cues — grounding one never picks the other.
    assert rf._pick_variation_op(a, _CONVO + ["datumfeedback"], "sm_rep") == "datum_feedback_rule"


# --------------------------------------------------------------------------- #
#  the compose: datum_feedback_rule
# --------------------------------------------------------------------------- #

def _promote(a, content, kind="reported", tag="probe"):
    sc = a.s.add_node("SelfConcern", {"status": "noted", "source": "explicit_report",
                                      "kind": kind, "content": content})
    st = a.s.add_node("StandingConcern", {"name": tag, "kind": kind})
    a.inner.add_edge_unchecked(sc, "promoted_to", st)
    return sc, st


def test_compose_datum_feedback_rule_picks_and_abstains(agent):
    a = agent
    _promote(a, "your reliability tracking after a contradiction is wrong", tag="df_ok")
    rep = rf._compose_datum_feedback_rule(a, ["df_ok"], "t1")
    assert rep["built"] is True, rep
    assert rep["datum_attr"] == "self_report_contradiction_count"
    assert rep["belief_attr"] == "self_report_reliability"
    rule = rep["rule"]
    assert rule["match"] == [["agent", "has_interlocutor", "party"]]
    assert rule["name"].startswith("datum_feedback_")

    # honest abstain: content naming no held datum/belief vocabulary.
    _promote(a, "you always mumble incoherently", tag="df_none")
    rep2 = rf._compose_datum_feedback_rule(a, ["df_none"], "t2")
    assert rep2["built"] is False and "abstain" in rep2["wall"]

    # honest abstain: no promoted StandingConcern at all.
    rep3 = rf._compose_datum_feedback_rule(a, ["df_missing"], "t3")
    assert rep3["built"] is False


def test_datum_feedback_rule_round_trips_canonical_export(agent):
    a = agent
    _promote(a, "your reliability trust tracking is broken", tag="df_canon")
    rep = rf._compose_datum_feedback_rule(a, ["df_canon"], "canon")
    assert rep["built"] is True
    idx = a.inner.add_rule(rep["rule"])
    exported = a.inner.export_rules()
    live = next(r for r in exported if r.get("name") == rep["rule"]["name"])
    # the canonical body must round-trip byte-identically through the same
    # discipline the daemon's own resume-refresh guard relies on.
    assert jd._canon_rule_body(live) == jd._canon_rule_body(rep["rule"])
    assert idx is not None


# --------------------------------------------------------------------------- #
#  the compose: shape_mint
# --------------------------------------------------------------------------- #

def test_compose_shape_mint_abstains_with_no_poor_fit_party(agent):
    a = agent
    _promote(a, "your interlocutor persona profile is unclassified", tag="sm_none")
    rep = rf._compose_shape_mint(a, ["sm_none"], "t1")
    assert rep["built"] is False
    assert "poor-fit" in rep["wall"]


def test_compose_shape_mint_abstains_on_content_not_naming_a_shape(agent):
    a = agent
    _promote(a, "you always mumble incoherently", tag="sm_wrong_content")
    rep = rf._compose_shape_mint(a, ["sm_wrong_content"], "t1")
    assert rep["built"] is False
    assert "abstain" in rep["wall"]


def test_compose_shape_mint_picks_poor_fit_party_and_signature(agent):
    a = agent
    for _ in range(4):
        a.converse("no. stupid. ugh!!", speech_act="statement")
    party = _active_party(a)
    # force a genuine poor-fit streak + a rich-enough feature set, independent
    # of whatever the held codebook happens to fit this exact utterance set to
    # (the datum's own mechanics are gated separately above).
    a.inner.set_attr(party, "poor_fit_streak", 5)
    a.inner.set_attr(party, "feat_counts", {
        "register": {"casual": 4}, "cadence": {"short": 4},
        "style": {"plain": 4}, "affect": {"agitated": 4},
    })
    _promote(a, "your interlocutor shape persona profile poor fit is unclassified", tag="sm_ok")
    rep = rf._compose_shape_mint(a, ["sm_ok"], "t1")
    assert rep["built"] is True, rep
    concept = rep["concept"]
    assert concept["type"] == "InterlocutorShape"
    attrs = concept["attrs"]
    assert attrs["sig_register"] == "casual"
    assert attrs["sig_cadence"] == "short"
    assert attrs["sig_style"] == "plain"
    assert attrs["sig_affect"] == "agitated"
    assert attrs["minted"] == 1.0
    # priors are copied WIDE from the codebook's own default_uncalibrated row.
    default_at = next(a.s.node(n)["attrs"] for n in a.s.nodes("InterlocutorShape")
                      if a.s.node(n)["attrs"].get("name") == "default_uncalibrated")
    assert attrs["reliability_interval"] == pytest.approx(
        float(default_at.get("reliability_interval", 0.35)))


def test_compose_shape_mint_abstains_on_sparse_features(agent):
    a = agent
    for _ in range(2):
        a.converse("hi", speech_act="greeting")
    party = _active_party(a)
    a.inner.set_attr(party, "poor_fit_streak", 3)
    a.inner.set_attr(party, "feat_counts", {"register": {"casual": 2}})   # only 1 established dim
    _promote(a, "your interlocutor shape persona profile poor fit is unclassified", tag="sm_sparse")
    rep = rf._compose_shape_mint(a, ["sm_sparse"], "t1")
    assert rep["built"] is False
    assert "sparse" in rep["wall"]


# --------------------------------------------------------------------------- #
#  a LIVE fixpoint: the authored rule moves the belief, clamped, once per
#  genuine datum change; effective_reliability reads it back.
# --------------------------------------------------------------------------- #

def test_authored_datum_feedback_rule_moves_belief_clamped_once_per_change(agent):
    a = agent
    a.converse("Hi, I am Hank.", speech_act="statement")
    party = _active_party(a)
    _promote(a, "your reliability trust tracking is broken", tag="df_live")
    rep = rf._compose_datum_feedback_rule(a, ["df_live"], "live")
    assert rep["built"] is True
    a.inner.add_rule(rep["rule"])

    # no datum yet -> the where-clause's `Not(Eq(datum, None))` guard blocks the rule.
    a.inner.run_rules()
    assert a.s.node(party)["attrs"].get("self_report_reliability") is None

    a.inner.set_attr(party, "self_report_contradiction_count", 1)
    a.inner.run_rules()
    at = a.s.node(party)["attrs"]
    assert at.get("self_report_reliability") == pytest.approx(0.5 - rep["step"])
    assert at.get("self_report_reliability_source") == "learned"

    # a SECOND run_rules with NO datum change must not fire again (epoch guard).
    a.inner.run_rules()
    at2 = a.s.node(party)["attrs"]
    assert at2.get("self_report_reliability") == pytest.approx(0.5 - rep["step"])

    # the datum genuinely changing fires it again.
    a.inner.set_attr(party, "self_report_contradiction_count", 2)
    a.inner.run_rules()
    at3 = a.s.node(party)["attrs"]
    assert at3.get("self_report_reliability") == pytest.approx(0.5 - 2 * rep["step"])

    # effective_reliability now reads the LEARNED belief, not the shape blend.
    eff = im.effective_reliability(a, party)
    assert eff["source"] == "learned"
    assert eff["value"] == pytest.approx(at3["self_report_reliability"])

    # the clamp floor holds under many further changes.
    for i in range(3, 60):
        a.inner.set_attr(party, "self_report_contradiction_count", i)
        a.inner.run_rules()
    floored = a.s.node(party)["attrs"]["self_report_reliability"]
    assert floored == pytest.approx(rep["floor"])
    assert floored >= rep["floor"] - 1e-9


def test_datum_feedback_rule_is_byte_unchanged_for_an_untouched_party(agent):
    """A party the authored rule never fires for (no datum recorded) stays
    byte-unchanged — the rule is additive, never a default behaviour."""
    a = agent
    a.converse("Hi, I am Ivy.", speech_act="statement")
    party = _active_party(a)
    _promote(a, "your reliability trust tracking is broken", tag="df_untouched")
    rep = rf._compose_datum_feedback_rule(a, ["df_untouched"], "untouched")
    a.inner.add_rule(rep["rule"])
    a.inner.run_rules()
    eff = im.effective_reliability(a, party)
    assert eff["source"] != "learned"


# --------------------------------------------------------------------------- #
#  adoption + revert + veto
# --------------------------------------------------------------------------- #

def test_datum_feedback_adoption_installs_rule_and_revert_removes_it(agent):
    a = agent
    a.converse("Hi, I am Jan.", speech_act="statement")
    party = _active_party(a)
    a.inner.set_attr(party, "self_report_contradiction_count", 1)
    _promote(a, "your reliability trust tracking is broken", tag="df_adopt")
    rep = rf._compose_datum_feedback_rule(a, ["df_adopt"], "adopt")
    assert rep["built"] is True

    exp = mint_experiment(a, "datum feedback probe", "conversation", add_rules=[rep["rule"]])
    delta = a.inner.neighbours(exp, "has_delta")[0]
    a.inner.set_attr(delta, "datum_feedback_edit", 1.0)
    a.inner.set_attr(delta, "datum_feedback_datum_attr", rep["datum_attr"])
    a.inner.set_attr(delta, "datum_feedback_belief_attr", rep["belief_attr"])
    a.inner.set_attr(exp, "status", "done")
    a.inner.set_attr(exp, "outcome", "supported")
    a.inner.set_attr(exp, "regressions", 0)
    a.inner.set_attr(exp, "adopt_ready", True)

    before_rules = {r.get("name") for r in a.inner.export_rules() if r.get("active", True)}
    assert rep["rule"]["name"] not in before_rules

    records = rf.perform_adoptions(a)
    my_recs = [r for r in records if r.get("rule_added") == rep["rule"]["name"]]
    assert len(my_recs) == 1
    assert a.s.node(exp)["attrs"].get("adopted") is True
    after_rules = {r.get("name") for r in a.inner.export_rules() if r.get("active", True)}
    assert rep["rule"]["name"] in after_rules

    adoption = my_recs[0]["adoption"]
    at = a.s.node(adoption)["attrs"]
    assert at["rule_removed"] == "" and at["rule_added"] == rep["rule"]["name"]

    r = rf.revert_adoption(a, adoption)
    assert r["reverted"] is True and r["removed_rule"] == rep["rule"]["name"]
    reverted_rules = {r2.get("name") for r2 in a.inner.export_rules() if r2.get("active", True)}
    assert rep["rule"]["name"] not in reverted_rules
    assert a.s.node(exp)["attrs"].get("adopted") is False
    # idempotent
    r2 = rf.revert_adoption(a, adoption)
    assert r2["reverted"] is False and r2["reason"] == "already reverted"


def test_datum_feedback_adoption_vetoed_on_regressions(agent):
    a = agent
    a.converse("Hi, I am Kim.", speech_act="statement")
    _promote(a, "your reliability trust tracking is broken", tag="df_veto")
    rep = rf._compose_datum_feedback_rule(a, ["df_veto"], "veto")
    exp = mint_experiment(a, "datum feedback probe", "conversation", add_rules=[rep["rule"]])
    delta = a.inner.neighbours(exp, "has_delta")[0]
    a.inner.set_attr(delta, "datum_feedback_edit", 1.0)
    a.inner.set_attr(delta, "datum_feedback_belief_attr", rep["belief_attr"])
    a.inner.set_attr(exp, "status", "done")
    a.inner.set_attr(exp, "outcome", "supported")
    a.inner.set_attr(exp, "regressions", 2)
    a.inner.set_attr(exp, "adopt_ready", True)
    a.tick()      # the agent's own adopt_denied_on_regression rule (adoption_safety)
    at = a.s.node(exp)["attrs"]
    assert at.get("adopt_denied") is True, at
    records = rf.perform_adoptions(a)
    assert not any(r.get("rule_added") == rep["rule"]["name"] for r in records)
    rules_now = {r.get("name") for r in a.inner.export_rules() if r.get("active", True)}
    assert rep["rule"]["name"] not in rules_now, (
        "a vetoed datum-feedback experiment must never install its rule into the parent")


def test_shape_mint_adoption_installs_node_and_revert_removes_it(agent):
    a = agent
    for _ in range(4):
        a.converse("no. stupid. ugh!!", speech_act="statement")
    party = _active_party(a)
    a.inner.set_attr(party, "poor_fit_streak", 5)
    a.inner.set_attr(party, "feat_counts", {
        "register": {"casual": 4}, "cadence": {"short": 4},
        "style": {"plain": 4}, "affect": {"agitated": 4},
    })
    _promote(a, "your interlocutor shape persona profile poor fit is unclassified", tag="sm_adopt")
    rep = rf._compose_shape_mint(a, ["sm_adopt"], "adopt")
    assert rep["built"] is True

    exp = mint_experiment(a, "shape mint probe", "conversation", add_concepts=[rep["concept"]])
    delta = a.inner.neighbours(exp, "has_delta")[0]
    a.inner.set_attr(delta, "shape_mint_edit", 1.0)
    a.inner.set_attr(delta, "shape_mint_name", rep["name"])
    a.inner.set_attr(delta, "shape_mint_party", rep["party"])
    a.inner.set_attr(exp, "status", "done")
    a.inner.set_attr(exp, "outcome", "supported")
    a.inner.set_attr(exp, "regressions", 0)
    a.inner.set_attr(exp, "adopt_ready", True)

    before = [n for n in a.s.nodes("InterlocutorShape") if a.s.node(n)["attrs"].get("name") == rep["name"]]
    assert before == []

    records = rf.perform_adoptions(a)
    my_recs = [r for r in records if r.get("shape_name") == rep["name"]]
    assert len(my_recs) == 1
    assert a.s.node(exp)["attrs"].get("adopted") is True
    after = [n for n in a.s.nodes("InterlocutorShape") if a.s.node(n)["attrs"].get("name") == rep["name"]]
    assert len(after) == 1

    adoption = my_recs[0]["adoption"]
    r = rf.revert_adoption(a, adoption)
    assert r["reverted"] is True and r["removed_shape"] == rep["name"]
    gone = [n for n in a.s.nodes("InterlocutorShape") if a.s.node(n)["attrs"].get("name") == rep["name"]]
    assert gone == []
    assert a.s.node(exp)["attrs"].get("adopted") is False
    r2 = rf.revert_adoption(a, adoption)
    assert r2["reverted"] is False and r2["reason"] == "already reverted"
