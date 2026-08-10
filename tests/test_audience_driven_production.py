"""Tests for `domains/audience_driven_production.py` -- the communication loop's THIRD PIECE,
grounded: a speaker-models-listener midpoint (`pragmatic_speaker.choose_encoding`, reused verbatim)
fed by a GROUNDED audience model (`system_model.model_system` foreign_snapshot, reused verbatim)
instead of a hand-set prior.

Fast fixtures only -- `substrate.boot_core.boot_core()`, mirroring `tests/test_system_model.py`'s
own convention (no full `load_all_seeds` boot).
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import boot_core                              # noqa: E402
from domains import audience_driven_production as adp                  # noqa: E402

LEXICON = [
    {"form": "dinner", "concept": "dinner"},
    {"form": "seven pm", "concept": "seven_pm"},
    {"form": "the italian place", "concept": "italian_place"},
    {"form": "a reservation", "concept": "reservation"},
    {"form": "table for two", "concept": "table_for_two"},
]
MEANING = {"dinner", "seven_pm", "italian_place", "reservation", "table_for_two"}
SHARED = ["dinner", "seven_pm", "italian_place"]


@pytest.fixture()
def agent():
    s, ag = boot_core()
    return s


# ===========================================================================
# 1. audience_model -- grounding via system_model's foreign_snapshot path.
# ===========================================================================

def test_observed_interlocutor_grounds(agent):
    m = adp.audience_model(agent, {"id": "spouse", "observed": True, "known_concepts": SHARED})
    assert m["grounded"] is True
    assert m["known"] == frozenset(SHARED)
    assert m["system_model"] is not None
    assert m["system_model"].target_kind == "foreign_snapshot"
    assert m["system_model"].grounded is True


def test_unobserved_interlocutor_does_not_ground(agent):
    m = adp.audience_model(agent, {"id": "stranger", "observed": False})
    assert m["grounded"] is False
    assert m["known"] == frozenset()
    assert m["system_model"] is None


def test_unobserved_hint_is_never_credited_even_if_supplied(agent):
    """The epistemic discipline: passing known_concepts without observed=True must not leak into
    `known` -- grounding is required, a hint alone is not enough."""
    m = adp.audience_model(agent, {"id": "ghost", "observed": False, "known_concepts": SHARED})
    assert m["grounded"] is False
    assert m["known"] == frozenset()


def test_grounding_uses_real_sensor_anchor(agent):
    """The foreign_snapshot audience model is grounded via the SAME SensorAnchor path
    `test_system_model.py` proves for an arbitrary foreign system -- not a bespoke shortcut."""
    m = adp.audience_model(agent, {"id": "spouse", "observed": True, "known_concepts": SHARED})
    assert "SensorAnchor" in m["system_model"].grounding.get("anchors", [])


# ===========================================================================
# 2. residual_vs_audience -- the meaning-minus-shared-model split.
# ===========================================================================

def test_residual_shrinks_for_grounded_rich_audience(agent):
    m = adp.audience_model(agent, {"id": "spouse", "observed": True, "known_concepts": SHARED})
    res = adp.residual_vs_audience(agent, MEANING, m)
    assert set(res["known"]) == set(SHARED)
    assert set(res["new"]) == MEANING - set(SHARED)
    assert 0.0 < res["residual_frac"] < 1.0


def test_residual_is_the_whole_meaning_for_ungrounded_audience(agent):
    m = adp.audience_model(agent, {"id": "stranger", "observed": False})
    res = adp.residual_vs_audience(agent, MEANING, m)
    assert res["known"] == []
    assert set(res["new"]) == MEANING
    assert res["residual_frac"] == 1.0


def test_residual_accepts_nested_meaning_tree(agent):
    """meaning may also be a nested Term-tree (audience._concepts' native shape), not just a flat
    concept set -- both paths land on the same extractor."""
    m = adp.audience_model(agent, {"id": "spouse", "observed": True,
                                    "known_concepts": ["dinner"]})
    tree = {"force": "tell", "plan": {"topic": "dinner", "extra": "reservation"}}
    res = adp.residual_vs_audience(agent, tree, m)
    assert "dinner" in res["known"]
    assert "reservation" in res["new"]


# ===========================================================================
# 3. select_utterance -- the audience-tailored midpoint, actually produced.
# ===========================================================================

def test_spouse_vs_stranger_terseness_contrast(agent):
    spouse = adp.audience_model(agent, {"id": "spouse", "observed": True,
                                         "known_concepts": SHARED})
    stranger = adp.audience_model(agent, {"id": "stranger", "observed": False})

    r_spouse = adp.select_utterance(agent, MEANING, spouse, LEXICON)
    r_stranger = adp.select_utterance(agent, MEANING, stranger, LEXICON)

    assert r_spouse["grounded_used"] is True
    assert r_stranger["grounded_used"] is False
    assert r_spouse["terseness"] > 0.0
    assert r_stranger["terseness"] == 0.0
    assert len(r_spouse["utterance"].split()) < len(r_stranger["utterance"].split())
    assert set(r_stranger["conveyed"]) == MEANING
    assert isinstance(r_spouse["utterance"], str) and r_spouse["utterance"]
    assert isinstance(r_stranger["utterance"], str) and r_stranger["utterance"]


def test_grounded_only_tailoring_is_discriminative(agent):
    """Same known_concepts hint as the spouse, but NOT observed -- must fall back to explicit,
    discriminative against the grounded spouse case."""
    spouse = adp.audience_model(agent, {"id": "spouse", "observed": True,
                                         "known_concepts": SHARED})
    ghost = adp.audience_model(agent, {"id": "ghost", "observed": False,
                                        "known_concepts": SHARED})

    r_spouse = adp.select_utterance(agent, MEANING, spouse, LEXICON)
    r_ghost = adp.select_utterance(agent, MEANING, ghost, LEXICON)

    assert r_ghost["grounded_used"] is False
    assert r_ghost["terseness"] == 0.0
    assert set(r_ghost["conveyed"]) == MEANING
    assert r_ghost["utterance"] != r_spouse["utterance"]


def test_terse_utterance_never_restates_a_shared_concept(agent):
    spouse = adp.audience_model(agent, {"id": "spouse", "observed": True,
                                         "known_concepts": SHARED})
    r = adp.select_utterance(agent, MEANING, spouse, LEXICON)
    assert set(r["conveyed"]).isdisjoint(SHARED)


def test_grounded_rungs_all_recover_fully_when_known_is_credited(agent):
    """Every rung on the grounded spectrum recovers the FULL meaning (known concepts are credited
    regardless of whether they're restated) -- so the argmax is a genuine cost-only tie-break, not
    an accuracy trade -- while cost strictly falls as terseness rises."""
    spouse = adp.audience_model(agent, {"id": "spouse", "observed": True,
                                         "known_concepts": SHARED})
    r = adp.select_utterance(agent, MEANING, spouse, LEXICON)
    assert r["rungs"] is not None
    recs = [rec for _, _, rec, _ in r["rungs"]]
    costs = [c for _, _, _, c in r["rungs"]]
    assert all(rc == pytest.approx(1.0) for rc in recs)
    assert costs == sorted(costs, reverse=True)   # cost falls monotonically as terseness rises
    assert costs[0] > costs[-1]                   # explicit (rung 0) strictly costlier than terse


def test_no_meaning_no_op(agent):
    spouse = adp.audience_model(agent, {"id": "spouse", "observed": True,
                                         "known_concepts": SHARED})
    r = adp.select_utterance(agent, set(), spouse, LEXICON)
    assert r["utterance"] == ""


def test_caller_supplied_candidates_are_honoured(agent):
    spouse = adp.audience_model(agent, {"id": "spouse", "observed": True,
                                         "known_concepts": SHARED})
    cands = [(0.0, MEANING), (1.0, {"reservation"})]
    r = adp.select_utterance(agent, MEANING, spouse, LEXICON, candidates=cands)
    assert set(r["conveyed"]) in (MEANING, {"reservation"})
