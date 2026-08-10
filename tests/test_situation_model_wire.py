"""THE WIRE: TEXTBASE -> SITUATION MODEL (domains/situation_model_reader.py).

The reader was PARSING-COMPLETE + grounding-strong but COMPREHENSION-SHALLOW: it
built a Kintsch TEXTBASE (`drop(john, glass)`) but never the SITUATION MODEL (the
glass is now on the floor, broken). The machinery for the situation model already
existed and was green in isolation (seeds/situation_model.json + event_reasoning),
but NOTHING fed it a node from parsed text. This is the ONE WIRE: it mints the
sm_event / sm_entity nodes those seeds' rules match on, from the reader's own
predications, and lets the EXISTING run_rules fixpoint build the model.

Discriminative gates (donkey = 0, no LLM):

  * HEADLINE — TEXTBASE -> SITUATION MODEL: reading a passage whose text states
    only {glass is fragile, john dropped glass} builds a situation model that
    ADDITIONALLY holds {on_floor, broken, worthless, on the floor} — the state the
    text never stated, materialised by the event_reasoning 3-hop fixpoint over the
    minted nodes. The bare sentence (no fragility) infers on_floor but NOT broken:
    fragility is the world-knowledge premise, an honest residual.
  * FIVE INDICES filled from argument grounding (protagonist<-agent, entity<-theme,
    space<-goal); an unfilled index is a flagged RESIDUAL, not silently blank.
  * MULTI-SENTENCE PERSISTENCE: the sm_entity persists across sentence boundaries —
    the protagonist's LOCATION and an object's post-state survive the boundary
    (contrast the per-clause textbase).
  * CHANGE-OF-STATE IS A CLASS: an UNSEEN change-of-state verb JOINS the COS class
    by adjacency (nearness reported) and triggers a transition; a NON-change-of-
    state verb mints NO spurious transition.
  * GRAPH-NATIVE: the mint is graph nodes/edges; the inference is the existing
    run_rules fixpoint (NOT reimplemented); no `import re`.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_situation_model_wire.py -p no:randomly -q
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core            # noqa: E402
from domains import dictionary_lexicon as dl          # noqa: E402
from domains import situation_model_reader as smr     # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


# --------------------------------------------------------------------------- #
#  HEADLINE — reading builds a situation model that holds the UNSTATED state.
# --------------------------------------------------------------------------- #
def test_headline_textbase_to_situation_model():
    ag = _fresh()
    r = smr.read_into_situation_model(ag, "The glass is fragile. John dropped the glass.")

    # BEFORE — the textbase is grounded predications only; it NEVER says on_floor.
    flat = [tuple(p) for tb in r["textbase"] for p in tb["predications"]]
    assert ("dropped", "john", "glass") in flat
    assert ("is_a", "glass", "fragile") in flat
    stated = {tok for p in flat for tok in p}
    assert "on_floor" not in stated and "broken" not in stated and "worthless" not in stated

    # AFTER — the situation model holds the state the text did NOT state, built by
    # the event_reasoning 3-hop fixpoint (fell -> on_floor -> broken -> worthless).
    glass = r["situation_model"]["glass"]
    assert glass.get("location") == "the floor"       # situation_model sm_drop delta
    assert glass.get("on_floor") == 1                 # event_reasoning hop 1
    assert glass.get("broken") == 1                   # hop 2 (needed fragile)
    assert glass.get("worthless") == 1                # hop 3
    # and these are INFERRED, flagged by the seed's own *_inferred stamps.
    assert glass.get("on_floor_inferred") == 1 and glass.get("broken_inferred") == 1

    # the sm_event was minted with the shape the situation_model rule matches on.
    sm_events = [ag.s.node(n)["attrs"] for n in ag.s.nodes("SmEvent")]
    assert any(e.get("verb") == "drop" and e.get("idx_protagonist") == "john"
               and e.get("idx_entity") == "glass" for e in sm_events)


def test_bare_sentence_infers_on_floor_not_broken():
    # WITHOUT the stated fragility premise, the chain reaches on_floor but NOT
    # broken — fragility is world knowledge, an honest residual (the follow-on).
    ag = _fresh()
    r = smr.read_into_situation_model(ag, "John dropped the glass.")
    glass = r["situation_model"]["glass"]
    assert glass.get("on_floor") == 1 and glass.get("fell") == 1
    assert glass.get("broken") is None and glass.get("worthless") is None


# --------------------------------------------------------------------------- #
#  FIVE INDICES — filled from argument grounding; unfilled = flagged residual.
# --------------------------------------------------------------------------- #
def test_five_indices_and_residual():
    ag = _fresh()
    # a MOTION verb fills the space index from its goal argument.
    ing = smr.ingest_predication(ag, ["entered", "she", "kitchen"], t=1)
    assert ing["canon"] == "move" and ing["object_role"] == "goal"
    assert ing["indices"]["protagonist"] == "she"
    assert ing["indices"]["entity"] == "she"
    assert ing["indices"]["space"] == "kitchen"
    assert ing["indices"]["time"] == 1.0
    # causation + intentionality are not recoverable from a bare clause -> RESIDUAL.
    assert "causation" in ing["residual_indices"]
    assert "intentionality" in ing["residual_indices"]
    assert "space" not in ing["residual_indices"]       # filled for a motion verb

    # a manipulation verb (drop) has NO goal -> space itself is a residual.
    ag2 = _fresh()
    ing2 = smr.ingest_predication(ag2, ["dropped", "john", "glass"], t=1)
    assert ing2["object_role"] == "theme"
    assert ing2["indices"]["protagonist"] == "john" and ing2["indices"]["entity"] == "glass"
    assert "space" in ing2["residual_indices"]


# --------------------------------------------------------------------------- #
#  MULTI-SENTENCE PERSISTENCE — the sm_entity survives the sentence boundary.
# --------------------------------------------------------------------------- #
def test_multi_sentence_persistence():
    ag = _fresh()
    r = smr.read_into_situation_model(
        ag, "The cup is fragile. She entered the kitchen. She dropped the cup.")
    # the protagonist's LOCATION set in sentence 2 survives into sentence 3.
    assert r["situation_model"]["she"].get("location") == "kitchen"
    # the cup's post-state (dropped in sentence 3) is on the floor AND broken
    # (fragility stated in sentence 1 persisted to complete the chain).
    cup = r["situation_model"]["cup"]
    assert cup.get("on_floor") == 1 and cup.get("broken") == 1
    # the textbase is per-clause: no single predication carries she.location across.
    flat = [tuple(p) for tb in r["textbase"] for p in tb["predications"]]
    assert all("location" not in p for p in flat)


# --------------------------------------------------------------------------- #
#  CHANGE-OF-STATE IS A CLASS — join by adjacency; discriminative on non-COS.
# --------------------------------------------------------------------------- #
def test_unseen_verb_joins_by_adjacency():
    ag = _fresh()
    # 'smash' is NOT a seeded COS form; it JOINS by WordNet nearness to 'break'.
    mem = smr.cos_membership(ag, "smashed")
    assert mem["cos"] is True and mem["via"] == "adjacency"
    assert mem["nearness"] >= 0.75 and mem["nearest"] == "break"
    assert mem["canon"] == "shatter"
    # and it triggers a real state transition (situation_model sm_shatter).
    ing = smr.ingest_predication(ag, ["smashed", "john", "glass"], t=1)
    assert ing["cos"] is True
    assert smr.entity_state(ag, "glass").get("intact") == 0


def test_non_change_of_state_mints_no_transition():
    ag = _fresh()
    mem = smr.cos_membership(ag, "likes")
    assert mem["cos"] is False and mem["nearness"] < 0.75
    # GENERIC EVENTIVE (2026-07-07): a non-COS verb is no longer eventless. 'likes'
    # is an EVENTIVE verb (WordNet verb.emotion, not verb.stative), so it mints a
    # GENERIC SmEvent -- but with NO canonical state DELTA (there is no rule for it),
    # so the discriminative property this test guards is UNCHANGED: no entity carries
    # a spurious situation-model TRANSITION attr.
    ing = smr.ingest_predication(ag, ["likes", "john", "glass"], t=1)
    assert ing["cos"] is False and ing["kind"] == "generic_event"
    # NO spurious situation-model change: no entity carries a transition attr.
    st = smr.entity_state(ag, "glass")
    assert "on_floor" not in st and "location" not in st and "intact" not in st


def test_stative_verb_mints_no_event():
    # the DISCRIMINATIVE null under generic eventive: a STATIVE verb (WordNet
    # verb.stative -- be/seem/belong/own) mints NOTHING, while an action verb mints
    # a generic event. The eventive-vs-stative decision is WordNet's own verb
    # lexicographer file, not a seeded verb list.
    ag = _fresh()
    ev = smr.eventive_membership(ag, "resembles")
    assert ev["stative"] is True and ev["eventive"] is False
    ing = smr.ingest_predication(ag, ["resembles", "glass", "ice"], t=1)
    assert ing["cos"] is False and ing["kind"] == "non_change_of_state"
    # an action verb (freed) DOES mint a generic event (the mercy/rescue class).
    act = smr.eventive_membership(ag, "freed")
    assert act["eventive"] is True


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE AUDIT — no regex; the inference is the existing fixpoint.
# --------------------------------------------------------------------------- #
def test_source_audit_no_regex():
    src = open(os.path.join(ROOT, "domains", "situation_model_reader.py")).read()
    # no `import re` (whole-word) and no regex calls.
    import re as _re
    assert not _re.search(r"^\s*import re\b", src, _re.M)
    assert "re.compile(" not in src and "re.match(" not in src and "re.search(" not in src


def test_sm_entity_carries_is_entity_self_edge():
    # the minted sm_entity MUST carry the is_entity self-edge event_reasoning keys
    # on — proven by the chain firing (on_floor materialised) in the headline.
    ag = _fresh()
    smr.ingest_predication(ag, ["dropped", "john", "glass"], t=1)
    # the on_floor inference only fires if [x, is_entity, x] matched -> shape is right.
    assert smr.entity_state(ag, "glass").get("on_floor") == 1
