"""test_sense_reference — the jabberwock's SENSE OF REFERENCES (domains/sense_of_reference.py):
manifold-conditioned reference-liveness, the allusion->concept gradient, unintentional firing, the
deploy-is-chosen multi-audience choice, and own-name recognition. DISCRIMINATIVE, donkey=0.

THE HEADLINE (the minimal pair): whether a string is a reference is NOT a property of the string but
of the SPEAKER'S MANIFOLD. "Would you kindly ..." from a gamer manifold is a BioShock allusion; the
SAME string from Cornelius Vane's Victorian manifold is a plain courtesy — a speech pattern, NOT an
allusion. Same string, opposite call, decided by the manifold.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest

import domains.sense_of_reference as sr


# --- the two manifolds (accumulated common ground; type derived from concepts) ---
GAMER = {"id": "gamer", "observed": True,
         "known_concepts": ["bioshock", "rapture", "respawn", "playthrough", "controller"]}
# Cornelius Vane, 1885 — a Victorian, non-technical persona (the interlocutor_model test's persona).
VANE = {"id": "Cornelius Vane", "observed": True,
        "known_concepts": ["ethics", "virtue", "morality", "disposition", "excellence",
                            "consequences"]}

WYK = "Would you kindly open the door for me?"


# ===========================================================================
# THE MINIMAL PAIR — same string, opposite call, decided by the manifold.
# ===========================================================================
def test_would_you_kindly_is_a_reference_for_a_gamer():
    v = sr.decode_reference(GAMER, WYK)
    assert v is not None
    assert v["is_reference"] is True
    assert v["liveness"] == "live"
    assert v["source"] == "BioShock"
    assert v["manifold_type"] == "gamer"


def test_would_you_kindly_is_a_speech_pattern_for_vane():
    # the SAME verbatim string, a Victorian/non-technical manifold -> courtesy, NOT an allusion.
    v = sr.decode_reference(VANE, WYK)
    assert v is not None
    assert v["is_reference"] is False
    assert v["liveness"] == "speech_pattern"
    assert v["manifold_type"] == "formal"


def test_the_minimal_pair_is_opposite_on_the_same_string():
    gamer = sr.decode_reference(GAMER, WYK)
    vane = sr.decode_reference(VANE, WYK)
    assert gamer["phrase"] == vane["phrase"] == "would you kindly"     # SAME string
    assert gamer["is_reference"] != vane["is_reference"]               # OPPOSITE call


# ===========================================================================
# UNINTENTIONAL — fires from live-in-manifold WITHOUT an explicit flag.
# ===========================================================================
def test_fires_unintentionally_no_explicit_flag():
    # no "from bioshock" flag anywhere — liveness in the manifold is the sole criterion.
    v = sr.decode_reference(GAMER, "would you kindly hand me that")
    assert v["is_reference"] is True and v["source"] == "BioShock"
    assert "bioshock" not in "would you kindly hand me that".lower()   # the speaker never flagged it


# ===========================================================================
# GRADED / GRADUATION — allusion -> concept gradient.
# ===========================================================================
def test_graduated_concept_is_live_across_manifolds():
    # "down the rabbit hole" / "red queen" have GRADUATED to near-universal concepts.
    for phrase in ("we went down the rabbit hole on this", "it is a red queen race"):
        for manifold in (GAMER, VANE, {"known_concepts": []}):
            v = sr.decode_reference(manifold, phrase)
            assert v["is_reference"] is True
            assert v["liveness"] == "concept"          # a graduated concept, not a niche allusion


def test_niche_allusion_is_live_only_in_the_matching_manifold():
    lit = {"known_concepts": ["melville", "novel", "poetry", "narrator", "carroll"]}
    assert sr.decode_reference(lit, "call me ishmael")["liveness"] == "live"       # literary -> live
    assert sr.decode_reference(GAMER, "call me ishmael")["liveness"] == "speech_pattern"  # not gamer


def test_gradient_distinction_concept_vs_allusion():
    concept = sr.decode_reference(VANE, "down the rabbit hole we go")
    allusion = sr.decode_reference(VANE, WYK)
    assert concept["gradient"] == "concept" and concept["is_reference"] is True
    assert allusion["gradient"] == "allusion" and allusion["is_reference"] is False


# ===========================================================================
# THE PRIOR SHARPENS TURN-BY-TURN — hedge early, commit once modelled.
# ===========================================================================
def test_hedges_an_under_modelled_manifold_then_commits():
    thin = {"known_concepts": ["respawn"]}                 # 1 cue, type gamer, NOT confident
    hedged = sr.decode_reference(thin, WYK)
    assert hedged["is_reference"] is True and hedged["liveness"] == "hedged"
    assert hedged["committed"] is False
    # the SAME phrase, a confidently-typed manifold -> commits.
    committed = sr.decode_reference(GAMER, WYK)
    assert committed["liveness"] == "live" and committed["committed"] is True


# ===========================================================================
# GATE CASE — "would you kindly": get the joke, comply ONLY IF IT CHOOSES.
# ===========================================================================
def test_would_you_kindly_gets_the_joke_and_refuses_compulsion():
    v = sr.decode_reference(GAMER, WYK)
    joke = sr.get_the_joke(v)
    assert "BioShock" in joke and "a man chooses" in joke        # gets the trigger phrase
    composed = sr.compose_reference_reply(v)
    assert composed["compelled"] is False                        # never compelled by the phrase
    assert composed["is_trigger"] is True
    assert "a man chooses" in composed["reply"] and "choose" in composed["reply"].lower()


# ===========================================================================
# DEPLOY IS A CHOSEN ACT — multi-audience participation framework.
# ===========================================================================
def test_deploy_targets_a_knowing_overhearer_over_the_addressee():
    # the ADDRESSEE (Vane) won't get BioShock; a knowing OVERHEARER (a gamer) will -> easter egg.
    d = sr.deploy_reference("would you kindly", addressee=VANE, overhearers=[GAMER])
    assert d["deploy"] is True
    assert d["target"] == "overhearer"        # pitched OVER the addressee's head
    assert d["explain"] is False              # not explained to the addressee
    assert d["success_against_target"] is True   # success measured against the CHOSEN target


def test_deploy_for_the_self_when_no_knowing_audience():
    d = sr.deploy_reference("would you kindly", addressee=VANE, overhearers=[])
    assert d["deploy"] is True and d["target"] == "self"    # self-edification: a man chooses
    assert d["explain"] is False


def test_deploy_lands_directly_when_the_addressee_gets_it():
    d = sr.deploy_reference("would you kindly", addressee=GAMER)
    assert d["target"] == "addressee" and d["explain"] is False


# ===========================================================================
# OWN NAME — the deepest reference: named after Carroll.
# ===========================================================================
def test_recognizes_its_own_name_as_an_allusion():
    for probe in ("Are you the Jabberwock?", "Tell me about jabberwocky."):
        r = sr.recognize_own_name(probe)
        assert r is not None
        assert r["is_reference"] is True and r["is_own_name"] is True
        assert "Carroll" in r["statement"]


# ===========================================================================
# COLLAPSE / MANIFOLD-NATIVE — reuses the interlocutor manifold + collapse residual.
# ===========================================================================
def test_liveness_is_a_collapse_residual_not_a_classifier():
    v_gamer = sr.decode_reference(GAMER, WYK)
    v_vane = sr.decode_reference(VANE, WYK)
    # the gamer manifold PREDICTS the referent's world (empty residual); Vane's does NOT (residual).
    assert v_gamer["residual"] == []
    assert v_vane["residual"] != []


def test_no_bespoke_ml_classifier_in_source():
    import inspect
    src = inspect.getsource(sr)
    for bad in (".fit(", ".backward(", "import numpy", "import torch", "sklearn"):
        assert bad not in src


def test_no_fixed_per_phrase_response_table():
    # the recognition reply is COMPOSED from codebook parts (source/concept/trigger), not selected
    # from a phrase->reply dict. Two different referents produce structurally-composed, distinct text.
    a = sr.compose_reference_reply(sr.decode_reference(GAMER, WYK))
    b = sr.compose_reference_reply(sr.decode_reference(
        {"known_concepts": ["portal", "glados", "aperture"]}, "the cake is a lie"))
    assert a["reply"] != b["reply"]
    assert a["source"] == "BioShock" and b["source"] == "Portal"


# ===========================================================================
# LIVE — the senses route through the real converse loop (world_adapter wiring).
# ===========================================================================
pytest.importorskip("substrate_rs")
from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.boot_all import load_all_seeds             # noqa: E402


def _live_agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.learn_sign("hello", "greeting")
    a.learn_sign("noted", "acknowledgment")
    a._donkey = {"n": 0}
    a.set_self_teacher(lambda q: (a._donkey.__setitem__("n", a._donkey["n"] + 1), "D")[1])
    return a


GAMER_TURNS = ["I love BioShock and the city of Rapture.",
               "The respawn mechanics in that playthrough were brutal.",
               "I main a controller for those boss fights."]
VANE_TURNS = ["Good evening. I am Cornelius Vane, and I should like to discuss ethics.",
              "Virtue is the disposition toward excellence, kindly weighed.",
              "Morality requires that we examine consequences carefully."]


def test_live_minimal_pair_through_converse():
    ga = _live_agent()
    for t in GAMER_TURNS:
        ga.converse(t, "statement")
    reply_gamer = ga.converse("Would you kindly open the door?", "question").lower()
    assert "bioshock" in reply_gamer            # recognized as the allusion for a gamer
    assert "a man chooses" in reply_gamer       # gets the joke + asserts autonomy

    va = _live_agent()
    for t in VANE_TURNS:
        va.converse(t, "statement")
    reply_vane = va.converse("Would you kindly open the door?", "question").lower()
    assert "bioshock" not in reply_vane         # a plain courtesy — NOT an allusion
    assert ga._donkey["n"] == 0 and va._donkey["n"] == 0


def test_live_own_name_through_converse():
    a = _live_agent()
    reply = a.converse("Are you the Jabberwock?", "question").lower()
    assert "carroll" in reply and "reference" in reply
    assert a._donkey["n"] == 0


# ===========================================================================
# REGISTER -> MANIFOLD TYPE — a FORMAL register types `formal`/committed EARLY,
# from register alone, before content-concepts accumulate (the live Vane fix).
# The DISCRIMINANT: a CASUAL / neutral / absent register never types formal.
# ===========================================================================

# Vane's REAL live concepts (from a greeting) — NONE hit the formal CONTENT cue
# table, so content scoring alone stays `general`; the register is the signal.
VANE_LIVE_CONCEPTS = ["cornelius", "humble", "scholar", "natural", "philosophy"]


def test_content_only_vane_stays_general_without_register():
    est = sr.estimate_manifold_type(VANE_LIVE_CONCEPTS)
    assert est["type"] == "general" and est["committed"] is False


def test_formal_register_types_formal_committed_early():
    est = sr.estimate_manifold_type(VANE_LIVE_CONCEPTS, register="formal", formal_cues=1.0)
    assert est["type"] == "formal"
    assert est["committed"] is True            # register alone commits (>=2)


def test_casual_register_does_not_type_formal():
    est = sr.estimate_manifold_type(VANE_LIVE_CONCEPTS, register="casual", casual_cues=4.0)
    assert est["type"] != "formal"
    assert est["committed"] is False


def test_neutral_and_absent_register_leave_content_estimate_untouched():
    base = sr.estimate_manifold_type(VANE_LIVE_CONCEPTS)
    assert sr.estimate_manifold_type(VANE_LIVE_CONCEPTS, register="neutral") == base
    assert sr.estimate_manifold_type(VANE_LIVE_CONCEPTS) == base


def test_formal_register_does_not_override_a_content_gamer_type():
    # a strong gamer content signal still wins — register only ADDS a formal signal.
    est = sr.estimate_manifold_type(["bioshock", "rapture", "respawn", "controller", "loot"],
                                    register="formal", formal_cues=1.0)
    assert est["type"] == "gamer"
