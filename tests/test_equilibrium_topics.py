"""eq-tax-0.8.0 AMENDMENT A: questions open TOPICS (T3g).

Two relations per turn, each held open with the same strict cue-superset dominance:
  * reply (responds_to / candidates): the local sequential prior. An open question is a
    reply rival only when the turn has the (type-conforming, polar) answer form or sits
    in the question's conditional-relevance slot (Schegloff 2007).
  * topic (topic_id / topic_candidates): the live issue(s) the turn is under (Roberts
    1996; Ginzburg 2012). A question stays live while people say other things; answers
    are free form (user direction). A turn decided under q by another actor that is not
    backchannel-only / nonanswer / dismissive ENGAGES q: q is not unanswered.

Speech-style windows use kind "meeting" (no platform replies, adjacency only); text-style
windows use kind "channel" (declared replies / platform threads). Synthetic data only
(pseudonyms ana / bea / cy / dov); no corpus, no LLM.
"""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("OZMA_NO_LLM", "1")

from equilibrium_delta_fold import TOPIC_CUE_CODES  # noqa: E402

import test_equilibrium_tracking as trk  # noqa: E402
from domains import equilibrium_classify as eq  # noqa: E402

HELLO = trk.HELLO
base = trk.base
srv_svc = trk.srv_svc
_disc, _rows, _cands, _topic, _q, _turns, _conv, _fold = (
    trk._disc, trk._rows, trk._cands, trk._topic, trk._q, trk._turns, trk._conv, trk._fold)

# SPEECH (meeting): ana opens a complex room question; bea's first turn after it is in its
# slot (a free-form answer); the others talk on -- adjacency replies, all under the topic.
COMPLEX = HELLO + [("m1", "ana", "How should we structure the new remote control design?"),
                   ("m2", "bea", "I think the buttons should be big."),
                   ("m3", "cy", "Yeah."),
                   ("m4", "dov", "And maybe a scroll wheel for the channels."),
                   ("m5", "bea", "The wheel would cost more though."),
                   ("m6", "cy", "We could use rubber for the buttons.")]
# TEXT (channel): a simple polar question answered in the answer form, then other talk
POLAR = HELLO + [("s1", "ana", "Bea, is the build green?"), ("s2", "bea", "Yes, it passed."),
                 ("s3", "cy", "Lunch is at noon.")]
# TEXT: a polar answer form OUTSIDE the slot (bea took it) keeps the question a reply rival
POLAR_LATE = HELLO + [("r1", "ana", "Is the cache warm?"), ("r2", "bea", "Dov, check the logs please."),
                      ("r3", "cy", "Yes, it is warm.")]
# TEXT: two live issues for bea -- ana's question to her (k1) and cy's room question k2
# (cy's k2 is a declared reply to a greeting, so cy is under no topic) -- then cy, the
# asker of k2, settles a reply onto bea's k3 (topic uptake)
TWO = HELLO + [("k1", "ana", "Bea, what is blocking the release?"),
               ("k2", "cy", "What time is the demo?", {"reply_to": "h3"}),
               ("k3", "bea", "The demo is at three."),
               ("k4", "cy", "Bea, great, thanks.")]
# TEXT: two live room issues (ana's v1, cy's v2; cy's v2 is a declared self-continuation,
# so it is under no topic itself). T3h: the room's topic source is its MaxQUD (the most
# recent live room issue, KoS), so dov's turn has v2 as its room issue; it is in v2's slot
# and collapses onto it (tracked, via_reply). v1 stays live and is top again once v2 is
# downdated.
VIA = HELLO + [("v1", "ana", "What is blocking the release?"),
               ("v2", "cy", "What time is the demo?", {"reply_to": "h3"}),
               ("v3", "dov", "At three.")]
# SPEECH: a room question met only by backchannels is unanswered; a later free-form
# contribution engages it
ENGAGE = HELLO + [("e1", "ana", "What do people think about moving the standup to Thursdays?"),
                  ("e2", "bea", "Hmm."), ("e3", "cy", "Okay."),
                  ("e4", "dov", "Thursdays clash with the release train for me.")]


def test_complex_question_stays_live_and_free_form_contributions_get_its_topic(base):
    """SPEECH. m2 is in m1's slot (first turn by another actor): it replies to and answers
    m1 at reply level, but an assertion is no answer FORM, so the issue stays LIVE. The
    later turns reply locally (adjacency) -- the question is NOT their reply rival (no
    {open_question} vs {adjacent} hold) -- and are all under the topic m1."""
    out = _disc(base, COMPLEX, kind="meeting")
    assert _rows(out, {"m2"})["m2"] == (["m1"], "tracked", "strong", ["ana"], ["m1"])
    for tid, parent in (("m3", "m2"), ("m4", "m3"), ("m5", "m4"), ("m6", "m5")):
        assert _rows(out, {tid})[tid][:3] == ([parent], "tracked", "weak")
        assert _cands(out, tid) == {parent: ["adjacent"]}
        assert _topic(out, tid) == ("m1", {"m1": ["open_question", "via_reply"]})
    assert out["open_questions"] == []  # reply-level: answered by m2
    assert {t["topic_id"] for t in out["turns"] if t["id"][0] == "m"} == {None, "m1"}
    assert _topic(out, "m1") == (None, {})  # a question's topic is the one it is under, not itself


def test_simple_polar_question_answer_form_reply_and_answers(base):
    """TEXT. The type-conforming answer ("Yes") in the slot: reply + answers, strong; the
    question is resolved and downdated, so later other talk is under no topic."""
    out = _disc(base, POLAR)
    assert _rows(out, {"s2"})["s2"] == (["s1"], "tracked", "strong", ["ana"], ["s1"])
    assert _cands(out, "s2") == {"s1": ["addressed", "adjacent", "answer_form", "open_question"]}
    assert _topic(out, "s2") == ("s1", {"s1": ["answer_form", "open_question", "via_reply"]})
    assert _topic(out, "s3") == (None, {})
    assert ("bea", "inquiry.answered", "+", "ana") in _q(out)


def test_answer_form_outside_the_slot_keeps_the_question_a_reply_rival(base):
    out = _disc(base, POLAR_LATE)
    assert _rows(out, {"r3"})["r3"] == ([], "held", "held", [], [])
    assert _cands(out, "r3") == {"r1": ["answer_form", "open_question"], "r2": ["adjacent"]}
    assert _topic(out, "r3") == ("r1", {"r1": ["answer_form", "open_question"]})


def test_question_and_adjacent_are_not_reply_rivals(base):
    """The 0.8.0 dominant hold {open question: open_question, answer_form} vs {adjacent}
    is gone: outside the slot and without an answer form the question is no reply
    candidate at all; it is the TOPIC instead."""
    for rows, kind, later, q in ((COMPLEX, "meeting", ("m3", "m4", "m5", "m6"), "m1"),
                                 (ENGAGE, "meeting", ("e4",), "e1"), (trk.LIVE, "channel", ("l4",), "l1")):
        out = _disc(base, rows, kind=kind)
        assert "held" not in {t["basis"] for t in out["turns"]}
        for tid in later:
            assert q not in _cands(out, tid) and _topic(out, tid)[0] == q, tid


def test_two_live_issues_hold_the_topic(base):
    out = _disc(base, TWO[:-1])
    assert _topic(out, "k3") == (None, {"k1": ["open_question"], "k2": ["open_question"]})
    assert _topic(out, "k2") == (None, {})  # cy's live set is empty (k1 is addressed to bea)


def test_via_reply_decides_the_topic(base):
    out = _disc(base, VIA)
    assert _rows(out, {"v3"})["v3"][:3] == (["v2"], "tracked", "strong")
    assert _topic(out, "v3") == ("v2", {"v2": ["open_question", "via_reply"]})
    # TEXT: a platform-DECLARED reply places the turn in its parent's sequence -- its topic
    # is the parent's (here the parent question itself), never an unrelated live issue
    out = _disc(base, VIA[:-1] + [("v3", "dov", "At three.", {"reply_to": "v2"})])
    assert _topic(out, "v3") == ("v2", {"v2": ["open_question", "via_reply"]})
    out = _disc(base, VIA[:-1] + [("v3", "dov", "Morning!", {"reply_to": "h1"})])
    assert _topic(out, "v3") == (None, {})  # a reply into a topic-less sequence: no topic


def test_topic_uptake_revises_via_turns_delta(srv_svc):
    """cy (asker of k2) settles a reply onto bea's topic-held k3 in a LATER batch: k2 gains
    `uptake`, strictly dominates k1, and k3's topic is decided in that batch's turns_delta
    (full replacement incl. topic fields); its reply stays held (k1's `addressed` is not in
    k2's reply cues). One shot gives the same structure."""
    outs = _conv(srv_svc, "top:uptake", TWO, [len(TWO) - 1, 1])
    first = next(t for t in outs[0]["turns"] if t["id"] == "k3")
    assert first["topic_id"] is None and first["basis"] == "held"
    d = {x["id"]: x for x in outs[1]["turns_delta"]}
    assert set(d) == {"k3"}
    assert d["k3"]["topic_id"] == "k2"
    assert {c["ref"]: c["cues"] for c in d["k3"]["topic_candidates"]} == {
        "k1": ["open_question"], "k2": ["open_question", "uptake"]}
    assert d["k3"]["basis"] == "held"
    fin = srv_svc.conversation_close("top:uptake")
    one = eq.discourse(*trk._fork(srv_svc), {"window_id": "w", "kind": "channel"}, _turns(TWO))
    assert _fold(TWO, outs + [fin]).structure() == trk._structure(srv_svc, one)
    # k2 is engaged now (bea's k3 is under it), so cy's question is not unanswered
    assert ("cy", "inquiry.unanswered", "+", None) not in _q(one)


def test_engaged_question_is_not_unanswered(srv_svc):
    """SPEECH. Backchannels neither answer nor engage: e1 is unanswered after e3. dov's
    free-form e4 (not in the slot, no answer form: it replies to e3) is under the topic
    e1, so e1 is ENGAGED -- the unanswered quantum is retracted in that batch's delta --
    while e1 stays open (no answer) and live."""
    outs = [srv_svc.conversation_turns("top:eng", "meeting", _turns(ENGAGE[:-1])),
            srv_svc.conversation_turns("top:eng", "meeting", _turns(ENGAGE[-1:]))]
    f = _fold(ENGAGE, outs)
    keys0 = {(r["actor_ref"], r["trait"]) for r in _fold(ENGAGE, outs[:1]).quanta()}
    assert ("ana", "inquiry.unanswered") in keys0
    assert ("ana", "inquiry.unanswered") not in {(r["actor_ref"], r["trait"]) for r in f.quanta()}
    e4 = outs[1]["turns"][0]
    assert (e4["responds_to"], e4["topic_id"]) == (["e3"], "e1")
    assert outs[1]["open_questions"] == ["e1"]
    for tid in ("e2", "e3"):  # backchannels are under the topic but do not engage it
        assert f.structure()[tid]["topic_id"] == "e1"
    srv_svc.conversation_close("top:eng")


def test_topic_fields_on_every_turn_and_delta_and_invariants(srv_svc):
    """Wire: every turn object and turns_delta entry carries topic_id / topic_candidates
    (closed topic codebook, <= 4, earlier refs, dominance-consistent); a row violating
    the topic invariants is a 500 (RuntimeError in the re-shape), never repaired."""
    from services.equilibrium_classifier import server
    outs = _conv(srv_svc, "top:wire", TWO, [2])
    outs.append(srv_svc.conversation_close("top:wire"))
    rows = [t for o in outs for t in o["turns"]] + [d for o in outs for d in o["turns_delta"]]
    assert rows and all({"topic_id", "topic_candidates"} <= set(r) for r in rows)
    assert {c for r in rows for x in r["topic_candidates"] for c in x["cues"]} <= TOPIC_CUE_CODES
    assert server.TOPIC_CUE_CODES == TOPIC_CUE_CODES
    good = {"id": "z9", "responds_to": [], "basis": "none", "confidence": None, "candidates": [],
            "addressees": [], "thread_id": "z9", "answers": [],
            "topic_id": "k1", "topic_candidates": [{"ref": "k1", "cues": ["open_question"]}]}
    assert server.structure_violation(good) is None
    bad = [dict(good, topic_id=None),                                            # sole must decide
           dict(good, topic_id="k2"),                                            # not a candidate
           dict(good, topic_candidates=[{"ref": "k1", "cues": ["adjacent"]}]),   # reply cue code
           dict(good, topic_candidates=[{"ref": "z9", "cues": ["open_question"]}], topic_id="z9"),
           dict(good, topic_id="k1", topic_candidates=[{"ref": "k1", "cues": ["open_question"]},
                                                        {"ref": "k2", "cues": ["open_question"]}])]
    for b in bad:
        assert server.structure_violation(b), b
        with pytest.raises(RuntimeError):
            server.structure_to_wire(b)


def test_topic_codebook_is_seeded_and_closed(base):
    _, root, snap = base
    n = eq._native(snap.fork())
    codes = {n.node(k)["attrs"]["code"] for k in n.neighbours(root, "eq_has_top_cue")}
    assert codes == TOPIC_CUE_CODES


@pytest.mark.parametrize("name", ["complex", "two", "via", "engage", "polar_late"])
def test_topic_fold_equals_one_shot_at_every_prefix_and_batch_size(srv_svc, name):
    rows = {"complex": COMPLEX, "two": TWO, "via": VIA, "engage": ENGAGE, "polar_late": POLAR_LATE}[name]
    trk.REVISING[f"top_{name}"] = rows
    try:
        trk.test_fold_turns_delta_equals_one_shot_at_every_prefix(srv_svc, f"top_{name}")
    finally:
        del trk.REVISING[f"top_{name}"]
