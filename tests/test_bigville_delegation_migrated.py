"""bigville: GENERAL TASK DELEGATION -- asking someone to do a task for you or the household.

Delegation is not food-specific and not an engine protocol: it is a conversation between two agents. The
delegator decides WHETHER and TO WHOM to delegate -- a collapse over the people it has ties to, weighing the
task's REQUIREMENTS, its EXPECTATIONS, the RELATIONSHIP, and its MODEL of each person -- and decides WHAT TO
OFFER itself, from its model of that person and what it can afford. The asked person then DECIDES to accept
or decline by their own relationship + the offer. A spouse or child helps freely; a stranger only if you
make it worth their while and can afford to; someone who can't do it, or whom you can't reach, you don't ask.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_need_world import BigvilleNeedWorld   # noqa: E402

ERRAND, DELIVER_NOTE, LITERACY = 7.0, 2.0, 5.0  # generic (non-map-fetch) tasks


def _world(names):
    w = BigvilleNeedWorld()
    for i, nm in enumerate(names):
        w.add_mover(nm, (14 + i, 8))
        w.set_plan(nm, horizon=0)      # no food-provisioning need here -- isolate the explicit task delegation
    return w


def _coin(w, name, c):
    w.eng.set_attr(w._movers[name], "coin", float(c))


def _coin_of(w, name):
    return round(float(w.eng.node(w._movers[name])["attrs"].get("coin", 0.0)), 4)


# ------------------------------------------------------ G-delegate-to-a-relation (headline)
def test_you_can_ask_a_close_relation_and_they_help_freely():
    w = _world(["me", "spouse"]); _coin(w, "me", 10)
    w.set_relationship("me", "spouse", kind="spouse", strength=3.0, min_ask=1.0, mutual=True)
    w.want_done("me", ERRAND)
    out = w.delegate("me")
    assert out["asked"] == "spouse" and out["status"] == 1, "the spouse agrees to do the task"
    assert out["offered"] == 0.0, "and needs no incentive -- a close relation helps freely"
    assert w.took_on_task("spouse"), "the spouse now has the task to do (will_do)"


# ------------------------------------------------------ G-offer-is-the-agents-decision (headline)
def test_the_offer_is_the_delegators_own_decision_not_an_engine_knob():
    w = _world(["me", "stranger"]); _coin(w, "me", 10)
    w.set_relationship("me", "stranger", kind="stranger", strength=0.0, expected_ask=1.0, min_ask=1.0, mutual=True)
    w.set_capability("stranger", LITERACY)                 # only the stranger can do it -> I must ask (and pay)
    w.want_done("me", ERRAND, requirement=LITERACY)
    out = w.delegate("me")
    assert out["asked"] == "stranger" and out["status"] == 1, "a stranger will do it -- if it's worth their while"
    assert out["offered"] > 0.0, "the delegator DECIDED to offer something (a stranger, unlike a spouse)"
    assert _coin_of(w, "me") == 10 - out["offered"] and _coin_of(w, "stranger") == out["offered"], \
        "and actually paid it -- the offered coin changed hands"
    # the adapter passes NO incentive; the offer is computed in the rule from the delegator's model + means
    import inspect
    from worlds.bigville_need_world import BigvilleNeedWorld as W
    assert "incentive" not in inspect.signature(W.delegate).parameters, "delegate() takes no incentive parameter"
    pursuit = json.load(open(os.path.join(_ROOT, "seeds", "bigville_pursuit.json")))
    ask = next(x for x in pursuit["rules"] if x["name"] == "pu_do_ask")
    assert "expected_ask" in json.dumps(ask["effects"]), "the offer is derived from the delegator's model (expected_ask - strength)"
    score = next(x for x in pursuit["rules"] if x["name"] == "pu_score_tie")
    assert "coin" in json.dumps(score), "and the ask is only chosen if it can be afforded (bounded by coin)"


def test_a_delegator_who_cannot_afford_it_does_not_secure_a_stranger():
    w = _world(["me", "stranger"]); _coin(w, "me", 0)      # no means to sweeten it
    w.set_relationship("me", "stranger", kind="stranger", strength=0.0, expected_ask=1.0, min_ask=1.0, mutual=True)
    w.want_done("me", ERRAND)
    out = w.delegate("me")
    assert out["asked"] is None, "with no relationship and no means, it asks no one -- it must do it itself"


# ------------------------------------------------------ G-weighs-capability (headline)
def test_delegation_goes_to_someone_who_can_actually_do_it():
    w = _world(["me", "literate", "illiterate"]); _coin(w, "me", 10)
    w.set_relationship("me", "literate", kind="child", strength=3.0, min_ask=1.0, mutual=True)
    w.set_relationship("me", "illiterate", kind="child", strength=3.0, min_ask=1.0, mutual=True)
    w.set_capability("literate", LITERACY)                 # only one can read
    w.want_done("me", DELIVER_NOTE, requirement=LITERACY)  # the note needs literacy
    out = w.delegate("me")
    assert out["asked"] == "literate" and w.took_on_task("literate"), "the note goes to the one who can read it"
    assert not w.took_on_task("illiterate"), "not to the one who can't do it, however close"


# ------------------------------------------------------ G-asks-the-best (headline)
def test_it_asks_the_best_candidate_free_family_over_a_paid_stranger():
    w = _world(["me", "spouse", "stranger"]); _coin(w, "me", 10)
    w.set_relationship("me", "spouse", kind="spouse", strength=3.0, min_ask=1.0, mutual=True)
    w.set_relationship("me", "stranger", kind="stranger", strength=0.0, expected_ask=1.0, min_ask=1.0, mutual=True)
    w.want_done("me", ERRAND)
    out = w.delegate("me")
    assert out["asked"] == "spouse" and out["offered"] == 0.0, "it asks the spouse (free) over the payable stranger"


# ------------------------------------------------------ G-they-can-say-no (headline; two-sided)
def test_the_other_person_can_still_decline_if_the_ask_falls_short():
    # the delegator MODELS the stranger as cheap (expected_ask 1) but they actually want more (min_ask 3)
    w = _world(["me", "stranger"]); _coin(w, "me", 10)
    w.set_relationship("me", "stranger", kind="stranger", strength=0.0, expected_ask=1.0, min_ask=3.0, mutual=True)
    w.set_capability("stranger", LITERACY)                 # only the stranger can do it -> I must ask
    w.want_done("me", ERRAND, requirement=LITERACY)
    out = w.delegate("me")
    assert out["asked"] == "stranger", "it asked (its model said the offer would do)"
    assert out["status"] == -1 and not w.took_on_task("stranger"), \
        "but they DECLINED -- the offer fell short of their bar; asking is not commanding (two-sided)"


# ------------------------------------------------------ G-general-not-food (headline)
def test_delegation_is_general_a_note_delegates_like_bread():
    w = _world(["me", "friend"]); _coin(w, "me", 10)
    w.set_relationship("me", "friend", kind="friend", strength=2.0, min_ask=1.0, mutual=True)
    w.want_done("me", DELIVER_NOTE)                         # a non-food task
    out = w.delegate("me")
    assert out["status"] == 1 and w.took_on_task("friend"), "you can ask a friend to deliver a note -- same faculty"


# ------------------------------------------------------ G-two-decisions (source audit)
def test_the_ask_and_the_answer_are_separate_rules():
    pursuit = json.load(open(os.path.join(_ROOT, "seeds", "bigville_pursuit.json")))
    ask = next(x for x in pursuit["rules"] if x["name"] == "pu_do_ask")   # the ASK is the pursuit's route
    assert not any(e[0] == "set_attr" and e[2] == "coin" for e in ask["effects"]), \
        "the ask itself moves no coin -- payment is on the OTHER party's acceptance"
    deleg = json.load(open(os.path.join(_ROOT, "seeds", "bigville_delegation.json")))
    names = {r["name"] for r in deleg["rules"]}
    assert names == {"dl_accept", "dl_decline"}, "the ANSWER (accept/decline) is the asked person's own separate rules"
    acc = next(x for x in deleg["rules"] if x["name"] == "dl_accept")
    assert ["cand", "tie", "bt"] in acc["match"], "acceptance reads the ASKED person's own relationship to the asker"
