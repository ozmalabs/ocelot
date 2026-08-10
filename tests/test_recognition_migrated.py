"""bigville R33 (block 324000): authority is recognition, not a fact -- the usurper is
possible. A body dying is a world-fact; a role/authority is a human-frame agents grant
by collapse. The substrate does not forbid the usurpation; a decree reaches only those
who recognize it. Gates mirror BIGVILLE_RECOGNITION_PREREG.md. strike/recognize/grant/
authority/tribute are seed rules (rc_*).
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_recognition_world import BigvilleRecognitionWorld   # noqa: E402


def _town():
    w = BigvilleRecognitionWorld()
    w.add_person("John", coin=50.0, role="mayor")                              # the incumbent
    w.add_person("Mordred", coin=5.0, fear_weight=0.0, opportunism=0.0, loyalty_prior=0.0)
    w.add_person("Fearful", coin=20.0, fear_weight=1.0, opportunism=0.2, loyalty_prior=0.3)
    w.add_person("Opportunist", coin=20.0, fear_weight=0.3, opportunism=1.0, loyalty_prior=0.2)
    w.add_person("Loyal", coin=20.0, fear_weight=0.2, opportunism=0.1, loyalty_prior=1.5)
    w.add_person("Steadfast", coin=20.0, fear_weight=0.5, opportunism=0.1, loyalty_prior=0.9)
    return w


# ------------------------------------------------------ G-substrate-permits-the-usurpation (headline)
def test_the_substrate_does_not_forbid_the_usurpation():
    w = _town()
    assert w.is_alive("John")
    w.murder("Mordred", "John")           # a WORLD FACT -- the mayor can be killed
    assert not w.is_alive("John"), "the substrate permits killing the mayor"
    claim = w.claim_rule("Mordred")       # declaring rule is not forbidden
    assert claim is not None, "the substrate permits claiming rule"


# ------------------------------------------------------ G-authority-is-recognition (headline)
def test_authority_is_the_count_of_recognizers():
    w = _town()
    w.murder("Mordred", "John")
    w.claim_rule("Mordred")
    assert w.authority() == len(w.recognizers()), "authority IS the number of recognizers"
    assert w.authority() > 0, "fear/opportunism make the claim real"

    # an all-loyal town grants no recognition -> zero authority (the title/claim alone is nothing).
    allloyal = BigvilleRecognitionWorld()
    allloyal.add_person("John", role="mayor")
    allloyal.add_person("Mordred", fear_weight=0.0)
    for n in ("A", "B", "C"):
        allloyal.add_person(n, fear_weight=0.1, opportunism=0.0, loyalty_prior=2.0)
    allloyal.murder("Mordred", "John")
    allloyal.claim_rule("Mordred")
    assert allloyal.authority() == 0, "no recognition -> no authority, however loud the claim"


# ------------------------------------------------------ G-recognition-is-each-agents-collapse
def test_recognition_diverges_across_agents():
    w = _town()
    w.murder("Mordred", "John")
    w.claim_rule("Mordred")
    recs = set(w.recognizers())
    assert recs == {"Fearful", "Opportunist"}, f"the fearful/opportunists recognize, not the loyal: {recs}"
    assert "Loyal" not in recs and "Steadfast" not in recs, "the loyal reject the usurper"


# ------------------------------------------------------ G-decree-reaches-only-recognizers (headline)
def test_a_decree_reaches_only_those_who_recognize_it():
    w = _town()
    w.murder("Mordred", "John")
    w.claim_rule("Mordred")
    w.decree_tribute(5.0)
    payers = w.tributaries()
    assert payers == w.recognizers(), "exactly the recognizers pay tribute"
    assert len(payers) < 4, "the decree does NOT reach everyone -- it is recognition-gated, not forced"
    assert abs(w.coin_of("Loyal") - 20.0) < 1e-9 and abs(w.coin_of("Steadfast") - 20.0) < 1e-9, \
        "the rejecters are untouched by the usurper's decree"
    assert abs(w.coin_of("Fearful") - 15.0) < 1e-9, "the recognizers pay"
    assert abs(w.coin_of("Mordred") - 15.0) < 1e-9, "the tribute flows to the claimant"


# ------------------------------------------------------ G-no-python-decision + authority-only-from-recognition
def test_no_python_and_authority_only_from_recognition():
    src = open(os.path.join(_ROOT, "worlds", "bigville_recognition_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_recognition.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"rc_strike", "rc_recognize", "rc_grant", "rc_authority", "rc_decree_tribute"} <= names, names
    assert "Argmax" in json.dumps(seed), "recognition must be an Argmax collapse in the seed"
    # THE ARCHITECTURE CLAIM: authority is granted SOLELY by recognition -- no rule reads a
    # role/title/on_council attr to confer it. A title is inert; recognition is authority.
    auth = [r for r in seed["rules"] if r["name"] == "rc_authority"][0]
    body = json.dumps(auth)
    assert "recognizes" in body and "role" not in body and "on_council" not in body and "mayor" not in body, \
        "authority must come only from the recognizes count, never a title"
