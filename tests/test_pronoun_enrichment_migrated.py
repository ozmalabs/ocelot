"""test_pronoun_enrichment_migrated — Deep-Reader Wave 4 (final wave of the
unification), mission 3: CONVERSATION PRONOUN ENRICHMENT.

The conversation layer's OWN pronoun/anaphora path
(`seeds/conversation_topic_tracking.json::resolve_anaphor_to_current_topic`)
resolves a bare pronoun/possessive ONLY against the tracked `current_topic`,
and simply ABSTAINS (mints nothing) when there is no tracked topic yet.
Meanwhile every shadow-read turn (Wave 2, `WorldAdapter._shadow_read_turn`)
runs the REAL deep-reader coref chain (SmMention -refers_to-> SmEntity, a
pool resident across turns) and, when it resolved a pronoun this turn,
`_shadow_read_turn` records the winner mechanically as `shadow_referent` on
the Message — a plain readback, never a decision.

`seeds/conversation_pronoun_enrichment.json::resolve_pronoun_from_shadow` is
the DECISION: it fires ONLY in the routed-nowhere case (nothing else claimed
the turn -- the explicit-topic route, the elliptical-shift route, and the old
anaphor-to-current-topic route are all excluded BY THEIR OWN PRECONDITIONS,
never a fixpoint race) and ONLY when the shadow referent is SAFE (the armed
deictic-centre speaker/addressee, or its name matches a held `Concept`) —
anything else stays honestly unresolved. On a match it mints the SAME
`Goal{kind:answer_topic}` the conversation layer's own routes mint, so the
EXISTING topic-answer machinery renders it: no new reply machinery.

`note_pronoun_referent_divergence` is a pure DATUM (the `speech_act_divergence`
precedent, Wave 3): when the OLD route's own preconditions held and its
target differs from the shadow referent, this records the disagreement for a
future retirement decision — it never changes the turn's reply.

The conversation reference path is NOT retired this wave.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter                       # noqa: E402
from substrate.boot_all import load_all_seeds                          # noqa: E402
from substrate.seed_loader import manifest_for                         # noqa: E402
from domains import dictionary_lexicon as dl                           # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


def _fresh(shadow_read=True):
    a = WorldAdapter(seeds=(), shadow_read=shadow_read)
    load_all_seeds(a)
    return a


def _goals(a):
    return [a.s.node(g)["attrs"] for g in a.inner.neighbours(a.agent, "has_goal")]


# --------------------------------------------------------------------------- #
#  THE GAP-FILL — old path abstains (no tracked topic), shadow read resolved
#  the pronoun to a SAFE (Concept-known) entity -> the rule fills the gap.
# --------------------------------------------------------------------------- #
def test_pronoun_enrichment_fills_gap_when_old_path_abstains():
    a = _fresh(shadow_read=True)
    # SAFE precondition (mission spec): the referent's name matches a held
    # Concept, and the agent already holds an answer about it.
    a.s.add_node("Concept", {"name": "saturn"})
    a._persist_held_answer("saturn", "Saturn is a gas giant with prominent rings.")

    reply = a.converse("Saturn has rings. What is it made of?", speech_act="question")
    mid = a._last_turn_inbound
    attrs = a.s.node(mid)["attrs"]

    assert attrs.get("shadow_referent") == "saturn"
    assert attrs.get("pronoun_referent_source") == "shadow_enrichment"
    # The OLD path's own detector saw the pronoun (comp_anaphor) but never
    # routed it (no topic_pending -- it genuinely abstained; no tracked topic).
    assert attrs.get("comp_anaphor") == 1.0
    assert not attrs.get("topic_pending")

    assert any(g.get("kind") == "answer_topic" and g.get("concept") == "saturn"
              and g.get("source") == "pronoun_shadow_enrichment" for g in _goals(a)), _goals(a)
    assert "gas giant" in reply.lower()


def test_unsafe_shadow_referent_stays_unresolved():
    """The shadow read may resolve a pronoun to SOME entity, but with no
    Concept match and no deictic match, the rule must NOT use it -- honest
    abstention, matching the old behaviour exactly (no Concept minted here)."""
    a = _fresh(shadow_read=True)
    # No Concept named "zorblat" -- the safety gate must decline. (Since the
    # tranche-15 lexical qualia index, a word WordNet knows -- "saturn" --
    # becomes a held word with qualia when it is first heard, so the unsafe
    # case needs a token with no sense: it stays unheld.)
    reply = a.converse("Zorblat has rings. What is it made of?", speech_act="question")
    mid = a._last_turn_inbound
    attrs = a.s.node(mid)["attrs"]
    assert attrs.get("shadow_referent") == "zorblat", "the shadow read itself still resolves it"
    assert attrs.get("pronoun_referent_source") is None, (
        "unsafe (no Concept/deictic match) referent must not be used")
    assert not any(g.get("source") == "pronoun_shadow_enrichment" for g in _goals(a))
    assert "don't hold" in reply.lower() or "don't know" in reply.lower() or reply


# --------------------------------------------------------------------------- #
#  OLD WINS ON DISAGREEMENT — the old anaphor-to-current-topic route's own
#  preconditions hold (comp_anaphor + a tracked current_topic): the new rule
#  must NOT fire (structural exclusion, not a race), and the reply must be
#  the OLD route's answer. The disagreement is recorded as a pure datum.
# --------------------------------------------------------------------------- #
def test_old_anaphor_route_wins_and_divergence_is_recorded_as_a_datum():
    a = _fresh(shadow_read=True)
    a.s.add_node("Concept", {"name": "saturn"})
    a.s.add_node("Concept", {"name": "jupiter"})
    a._persist_held_answer("saturn", "Saturn is a gas giant with prominent rings.")
    a._persist_held_answer("jupiter", "Jupiter is the largest planet in the Solar System.")

    # Turn 1: establish current_topic == jupiter via the OLD explicit route.
    r1 = a.converse("What do you know about Jupiter?", speech_act="question")
    assert "jupiter" in r1.lower()
    cts = list(a.inner.neighbours(a.agent, "current_topic"))
    assert cts and a.s.node(cts[0])["attrs"].get("name") == "jupiter"

    # Turn 2: the shadow read resolves "it" to saturn (introduced earlier in
    # THIS turn's own text), but the OLD anaphor-to-current-topic route's own
    # preconditions hold (comp_anaphor + a tracked current_topic) -- it wins.
    r2 = a.converse("Saturn has rings. What is it made of?", speech_act="question")
    mid2 = a._last_turn_inbound
    attrs2 = a.s.node(mid2)["attrs"]

    assert attrs2.get("shadow_referent") == "saturn"
    assert attrs2.get("comp_anaphor") == 1.0
    assert attrs2.get("pronoun_referent_divergence") == 1.0, (
        "old route's target (jupiter) disagrees with the shadow referent "
        "(saturn) -- must be recorded as a datum")

    # The OLD route claimed the turn -- no pronoun_shadow_enrichment goal.
    goals2 = _goals(a)
    assert not any(g.get("source") == "pronoun_shadow_enrichment" for g in goals2)
    assert any(g.get("kind") == "answer_topic" and g.get("concept") == "jupiter"
              and g.get("source") == "conversation" for g in goals2), goals2
    # The datum never changed the reply -- it is still about jupiter/Jupiter's
    # topic thread, never saturn.
    assert "saturn" not in r2.lower()


# --------------------------------------------------------------------------- #
#  SHADOW OFF -> nothing recorded, rule never fires.
# --------------------------------------------------------------------------- #
def test_shadow_off_records_nothing_and_rule_never_fires():
    a = _fresh(shadow_read=False)
    a.s.add_node("Concept", {"name": "saturn"})
    a._persist_held_answer("saturn", "Saturn is a gas giant with prominent rings.")
    a.converse("Saturn has rings. What is it made of?", speech_act="question")
    mid = a._last_turn_inbound
    attrs = a.s.node(mid)["attrs"]
    assert "shadow_referent" not in attrs
    assert "pronoun_referent_source" not in attrs
    assert "pronoun_referent_divergence" not in attrs
    assert not any(g.get("source") == "pronoun_shadow_enrichment" for g in _goals(a))


# --------------------------------------------------------------------------- #
#  EXISTING PRONOUN/ANAPHORA SUITES BYTE-GREEN -- a representative battery
#  through the conversation layer, shadow on vs off, replies unaffected
#  (mirrors test_shadow_read_migrated's own headline proof, extended with a
#  pronoun-carrying turn).
# --------------------------------------------------------------------------- #
_BATTERY = [
    ("What do you know about the moon?", "question"),
    ("How do you learn?", "question"),
    ("the sky is blue", "statement"),
    ("hello", "greeting"),
    ("What about it?", "question"),
    ("Tell me more.", "request"),
]


def test_existing_conversation_replies_byte_identical_shadow_on_off():
    off = _fresh(shadow_read=False)
    on = _fresh(shadow_read=True)
    for text, sa in _BATTERY:
        r_off = off.converse(text, speech_act=sa)
        r_on = on.converse(text, speech_act=sa)
        assert r_off == r_on, (
            "pronoun enrichment changed converse()'s reply for %r:\n  off=%r\n  on=%r"
            % (text, r_off, r_on))


# --------------------------------------------------------------------------- #
#  CANON ROUND-TRIP + REFRESHABLE-SEED MEMBERSHIP (the daemon's "edit a rule,
#  restart, it applies" workflow requires this).
# --------------------------------------------------------------------------- #
def test_seed_rules_canon_roundtrip_and_refreshable():
    from jabberwock_daemon import _canon_rule_body, _REFRESHABLE_SEEDS
    assert "conversation_pronoun_enrichment" in _REFRESHABLE_SEEDS
    rules = manifest_for("conversation_pronoun_enrichment").get("rules") or []
    assert {r["name"] for r in rules} == {
        "resolve_pronoun_from_shadow", "note_pronoun_referent_divergence"}
    for r in rules:
        body = _canon_rule_body(r)
        assert body, f"{r['name']} does not canonicalise"
        assert _canon_rule_body(json.loads(body)) == body, (
            f"{r['name']} canon body is not stable")
