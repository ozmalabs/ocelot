"""Equilibrium conversation TRACKING (track T3c stage O2, pack 0.5.0; T3g, pack 0.8.0).

Seeded turn cursor (seeds/equilibrium_tracking.json): addressees (name mention of an
actor who has already spoken, second person to the last addresser), eq_answers, the
open-question set, thread ids. eq-tax-0.8.0 (T3g): reply attribution is HELD OPEN --
a bounded candidate parent set per turn, each with cues from the closed EqTrkCue
codebook; collapse only when one candidate's cue set strictly contains every
rival's (strong: >= 2 cues, weak: 1); otherwise held, never tiebroken; uptake by a
later turn may collapse a held turn (turns_delta). The 0.7.0 tuples below changed
where adjacency now counts as evidence (weak) or competes with the old forced choice
(held); each changed expectation says why.

Synthetic windows only (pseudonyms ana / bea / cy / dov); no corpus, no LLM.
"""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("OZMA_NO_LLM", "1")

from equilibrium_delta_fold import DeltaFold  # noqa: E402

from domains import equilibrium_classify as eq  # noqa: E402

HELLO = [("h1", "ana", "Morning all."), ("h2", "bea", "Hi there."),
         ("h3", "cy", "Hello."), ("h4", "dov", "Hey.")]


@pytest.fixture(scope="module")
def base():
    s, root = eq.boot()
    return s, root, s.snapshot()


@pytest.fixture(scope="module")
def srv_svc():
    from services.equilibrium_classifier import server
    return server.ClassifierService()



def _turns(rows):
    out = []
    for r in rows:
        i, a, t, *rest = r
        d = {"id": i, "actor_ref": a, "text": t}
        extra = rest[0] if rest else {}
        d.update(extra)
        out.append(d)
    return out


def _disc(base, rows, kind="channel"):
    _, root, snap = base
    return eq.discourse(snap.fork(), root, {"window_id": "w_trk", "kind": kind}, _turns(rows))


def _rows(out, ids=None):
    """(responds_to, basis, confidence, addressees, answers) per turn"""
    return {t["id"]: (t["responds_to"], t["basis"], t["confidence"], t["addressees"], t["answers"])
            for t in out["turns"] if ids is None or t["id"] in ids}


def _cands(out, tid):
    t = next(t for t in out["turns"] if t["id"] == tid)
    return {c["ref"]: c["cues"] for c in t["candidates"]}


def _topic(out, tid):
    t = next(t for t in out["turns"] if t["id"] == tid)
    return t["topic_id"], {c["ref"]: c["cues"] for c in t["topic_candidates"]}


def _q(out):
    return {(q["actor_ref"], q["trait"], q["polarity"], q.get("target_ref")): q for q in out["quanta"]}


ADJ = ["adjacent"]
# HELLO under eq-tax-0.8.0: every greeting has exactly one candidate, the adjacent
# other-speaker turn, so it WEAK-collapses to it (adjacency is now evidence: one cue).
# h1 has no earlier turn (basis none). A weak collapse infers no addressee.
HELLO_WEAK = {"h1": ([], "none", None, [], []), "h2": (["h1"], "tracked", "weak", [], []),
              "h3": (["h2"], "tracked", "weak", [], []), "h4": (["h3"], "tracked", "weak", [], [])}


def test_non_adjacent_answer(base):
    """A asks B; C and D chat; B answers two turns later. 0.8.0: B's answer t4 is HELD
    between the open question t1 (open_question + addressed: B's first turn after it is
    the conditional-relevance slot) and the adjacent turn t3 (adjacent): neither cue set
    contains the other, so the reply is held open, never broken by recency (0.7.0 forced
    t1). Amendment A: t1 is the TOPIC t4 is under (the only live issue for bea), so t1
    is engaged -- not unanswered -- although no reply closed it."""
    out = _disc(base, HELLO + [
        ("t1", "ana", "Bea, what is the status of the build?"),
        ("t2", "cy", "Dov, did you see the release notes?"),
        ("t3", "dov", "Yes, they look fine to me."),
        ("t4", "bea", "The build passed this morning.")])
    assert _rows(out, {"t1", "t2", "t3", "t4"}) == {
        # vocative bea: bea's last turn h2 is t1's only (compatible) candidate -> weak at
        # t1's step; bea's HELD t4 has t1 among its candidates and bea authored h2, so h2
        # gains `uptake` (next-turn proof procedure): strong (late)
        "t1": (["h2"], "tracked", "strong", ["bea"], []),
        # h4 by dov: adjacent AND vocative (dov's last turn) -> strong
        "t2": (["h4"], "tracked", "strong", ["dov"], []),
        # t2 carries four cues (adjacent, open question for dov, pending address, polar
        # yes to a polar question): a sole candidate, strong; it answers t2
        "t3": (["t2"], "tracked", "strong", ["cy"], ["t2"]),
        "t4": ([], "held", "held", [], [])}
    assert _cands(out, "t3") == {"t2": ["addressed", "adjacent", "answer_form", "open_question"]}
    assert _cands(out, "t4") == {"t1": ["addressed", "open_question"], "t3": ADJ}
    assert out["open_questions"] == ["t1"]  # a held turn closes nothing
    assert ("bea", "inquiry.answered", "+", "ana") not in _q(out)
    assert _topic(out, "t4") == ("t1", {"t1": ["open_question"]})
    assert _topic(out, "t3") == ("t2", {"t2": ["answer_form", "open_question", "via_reply"]})
    assert ("ana", "inquiry.unanswered", "+", None) not in _q(out)  # engaged
    th = {t["id"]: t["thread_id"] for t in out["turns"]}
    assert th["t3"] == th["t2"] and th["t4"] == "t4"  # a held turn roots its own thread


def test_interleaved_two_thread_channel(base):
    """Two interleaved room questions: platform_thread keeps them apart (strong, with
    same_thread); a name mention adds vocative; without either, adjacency decides."""
    pa, pb = {"platform_thread": "thr_a"}, {"platform_thread": "thr_b"}
    rows = [("x1", "ana", "Which port does the cache use?", pa),
            ("y1", "cy", "Is the deploy window today?", pb),
            ("x2", "bea", "It uses the default port.", pa),
            ("y2", "dov", "Yes, from two to four.", pb)]
    out = _disc(base, HELLO + rows)
    assert _rows(out, {"x2", "y2"}) == {"x2": (["x1"], "tracked", "strong", ["ana"], ["x1"]),
                                        "y2": (["y1"], "tracked", "strong", ["cy"], ["y1"])}
    # x2 is the first turn by another actor in x1's thread: x1's conditional-relevance
    # slot (interleaved threads keep their own slots); an assertion is no answer FORM
    assert _cands(out, "x2") == {"x1": ["open_question", "same_thread"]}
    assert {t["id"]: t["thread_id"] for t in out["turns"] if t["id"][0] in "xy"} == {
        "x1": "thr_a", "x2": "thr_a", "y1": "thr_b", "y2": "thr_b"}
    named = [(i, a, t.replace("It uses", "Ana, it uses")) for i, a, t, _ in rows]
    out = _disc(base, HELLO + named)
    # the vocative excludes the adjacent turn by cy (incompatible with "Ana, ..."). Without
    # threads cy's y1 was the first turn by another actor after x1 (it took x1's slot), so
    # x1 rests on the vocative alone: weak (Amendment A)
    assert _rows(out, {"x2"}) == {"x2": (["x1"], "tracked", "weak", ["ana"], ["x1"])}
    # y2: the open question y1 vs the adjacent x2 -- incomparable, held
    assert _rows(out, {"y2"})["y2"][1] == "held"
    bare = [(i, a, t) for i, a, t, _ in rows]
    out = _disc(base, HELLO + bare)
    # no thread signal: x2's adjacent turn y1 is also the QUD top -> it wins (0.7.0: same)
    assert _rows(out, {"x2"})["x2"][:3] == (["y1"], "tracked", "strong")


def test_addressee_by_name_mention_only_for_known_actors(base):
    out = _disc(base, HELLO + [("m1", "ana", "Dov, the logs are ready."),
                               ("m2", "ana", "Zed, the logs are ready."),  # zed never spoke
                               ("m3", "dov", "On it.")])
    assert _rows(out, {"m1", "m2", "m3"}) == {
        "m1": (["h4"], "tracked", "strong", ["dov"], []),  # adjacent + vocative
        # no address: adjacency only (weak) at m2's step; dov's held m3 has m2 among its
        # candidates and dov wrote h4: uptake -> strong (late); addressees are causal (no
        # late addressee, Amendment A fix)
        "m2": (["h4"], "tracked", "strong", [], []),
        # m1 addressed dov (pending) vs m2 adjacent: held (0.7.0 forced m1)
        "m3": ([], "held", "held", [], [])}
    assert _cands(out, "m3") == {"m1": ["addressed"], "m2": ADJ}


def test_second_person_reply(base):
    out = _disc(base, HELLO + [
        ("s1", "ana", "Bea, can you check the logs?"),
        ("s2", "bea", "I checked them, you were right about the timeout."),
        ("s3", "cy", "Interesting."),
        ("s4", "ana", "Thanks, could you also restart the worker?"),
        ("s5", "bea", "Done.")])
    assert _rows(out, {"s2", "s3", "s4", "s5"}) == {
        "s2": (["s1"], "tracked", "strong", ["ana"], ["s1"]),
        "s3": (["s2"], "tracked", "weak", [], []),  # 0.7.0: none; now adjacency (weak)
        # second person to the last addresser bea, whose turn s2 is pending for ana
        "s4": (["s2"], "tracked", "strong", ["bea"], []),
        "s5": (["s4"], "tracked", "strong", ["ana"], ["s4"])}
    assert _cands(out, "s2") == {"s1": ["addressed", "adjacent", "open_question", "second_person"]}
    assert _cands(out, "s4") == {"s2": ["addressed", "second_person"]}
    assert out["open_questions"] == []


def test_counter_question_does_not_close(base):
    out = _disc(base, HELLO + [
        ("q1", "ana", "Bea, when will the patch land?"),
        ("q2", "bea", "Which patch do you mean?"),
        ("q3", "ana", "The cache patch."),
        ("q4", "bea", "It lands on Friday.")])
    assert _rows(out, {"q2", "q3", "q4"}) == {
        "q2": (["q1"], "tracked", "strong", ["ana"], []),       # counter-question: q1 stays open
        "q3": (["q2"], "tracked", "strong", ["bea"], ["q2"]),
        # Amendment A: bea spoke since q1 (q2) and q4 has no answer FORM, so q1 is no reply
        # rival of the adjacent q3: q4 replies to q3 locally; q1 stays open (no answer)
        "q4": (["q3"], "tracked", "strong", ["ana"], [])}
    assert _cands(out, "q4") == {"q3": ["addressed", "adjacent"]}
    assert out["open_questions"] == ["q1"]
    # topic: the base question q1 (live for bea) vs the insert question q2 (via q3's
    # topic): incomparable, the topic is HELD (insert expansion, Schegloff 2007)
    assert _topic(out, "q4") == (None, {"q1": ["open_question"], "q2": ["via_reply"]})


def test_dismissal_does_not_close(srv_svc):
    svc = srv_svc
    rows = _turns(HELLO + [("d1", "ana", "Bea, why did the build fail?"),
                           ("d2", "bea", "That is ridiculous, I know what I'm doing."),
                           ("d3", "cy", "The runner ran out of disk."),
                           ("d4", "bea", "The runner ran out of disk space.")])
    a = svc.conversation_turns("trk:dismiss", "channel", rows[:6])
    assert {t["id"]: (t["responds_to"], t["answers"]) for t in a["turns"]}["d2"] == (["d1"], [])
    assert a["open_questions"] == ["d1"]
    b = svc.conversation_turns("trk:dismiss", "channel", rows[6:])
    tb = {t["id"]: (t["responds_to"], t["basis"], t["answers"]) for t in b["turns"]}
    # d4: bea spoke since d1 (d2) and d4 is no answer FORM, so d1 is no reply rival of the
    # adjacent d3 (Amendment A): d4 replies to d3, d1 stays open (0.7.0: d4 was forced onto
    # d1 and closed it); d4 is under the topic d1
    assert tb == {"d3": (["d2"], "tracked", []), "d4": (["d3"], "tracked", [])}
    assert b["open_questions"] == ["d1"]
    assert next(t for t in b["turns"] if t["id"] == "d4")["topic_id"] == "d1"
    fin = svc.conversation_close("trk:dismiss")
    f = DeltaFold()  # the client folds the 0.6.0 evidence deltas
    f.turns(rows)
    for out in (a, b, fin):
        f.apply(out)
    keys = {(q["actor_ref"], q["trait"], q.get("target_ref")) for q in f.quanta()}
    assert ("bea", "response.dismissal", "ana") in keys and ("bea", "inquiry.answered", "ana") not in keys


def test_declared_reply_is_honoured(base):
    out = _disc(base, HELLO + [("r1", "ana", "Bea, is the cache warm?"),
                               ("r2", "cy", "Is the queue empty?"),
                               ("r3", "dov", "Yes, it is warm.", {"reply_to": "r1"})], kind="thread")
    assert _rows(out, {"r3"}) == {"r3": (["r1"], "declared", "declared", ["ana"], ["r1"])}
    assert _cands(out, "r3") == {}  # a declared reply needs no cues
    assert out["open_questions"] == ["r2"]


WINDOWS = {
    "non_adjacent": HELLO + [("t1", "ana", "Bea, what is the status of the build?"),
                             ("t2", "cy", "Dov, did you see the release notes?"),
                             ("t3", "dov", "Yes, they look fine to me."),
                             ("t4", "bea", "The build passed this morning.")],
    "counter": HELLO + [("q1", "ana", "Bea, when will the patch land?"),
                        ("q2", "bea", "Which patch do you mean?"), ("q3", "ana", "The cache patch."),
                        ("q4", "bea", "It lands on Friday."), ("q5", "cy", "However, Friday is a freeze."),
                        ("q6", "bea", "Fair point, Monday then.")],
}


def test_backchannel_does_not_answer(base):
    """0.7.0: a backchannel-only turn (closed-class EqBackchannel codebook: yeah / okay /
    right / mm-hmm / uh-huh ...) may respond to a question but does not answer it; the
    next substantive turn does. Polar answers ("yes") and backchannel + content do.
    0.8.0 Amendment A: b4 ("It uses port 6379.") is no answer FORM and not in b1's slot
    (bea took it), so b1 is no reply rival: b4 replies to the adjacent b3, b1 stays open
    and b4 is under its topic (a free-form contribution: b1 is ENGAGED, not unanswered)."""
    out = _disc(base, HELLO + [
        ("b1", "ana", "Which port does the cache use?"),
        ("b2", "bea", "Yeah."),
        ("b3", "cy", "Mm-hmm, okay right."),
        ("b4", "dov", "It uses port 6379."),
        ("b5", "ana", "Bea, is the deploy today?"),
        ("b6", "bea", "Yes."),
        ("b7", "cy", "Is the queue empty?"),
        ("b8", "dov", "Yeah, it drained at noon."),
        ("b9", "ana", "Does anyone know the build id?"),
        ("b10", "bea", "Uh-huh https://example.org/build/42")], kind="meeting")
    r = _rows(out, {"b2", "b3", "b4", "b6", "b8", "b10"})
    assert r["b2"] == (["b1"], "tracked", "strong", ["ana"], []) and r["b3"][4] == []
    assert r["b4"] == (["b3"], "tracked", "weak", [], [])
    assert _cands(out, "b4") == {"b3": ADJ}
    assert _topic(out, "b4") == ("b1", {"b1": ["open_question", "via_reply"]})
    assert r["b6"][4] == ["b5"] and r["b8"][4] == ["b7"] and r["b10"][4] == ["b9"]
    assert out["open_questions"] == ["b1"]
    q = _q(out)
    assert ("bea", "inquiry.answered", "+", "ana") in q and ("dov", "inquiry.answered", "+", "cy") in q
    assert ("dov", "inquiry.answered", "+", "ana") not in q
    assert ("ana", "inquiry.unanswered", "+", None) not in q  # b1 engaged (b4)
    # a question met ONLY by backchannels stays open (and is unanswered once others posted)
    out = _disc(base, HELLO + [("u1", "ana", "Who owns the cache?"), ("u2", "bea", "Hmm."),
                               ("u3", "cy", "Okay.")], kind="meeting")
    assert out["open_questions"] == ["u1"] and ("ana", "inquiry.unanswered", "+", None) in _q(out)


# ---- 0.8.0 (T3g): held-open collapse ------------------------------------------------
# dov is asked the same kind of question by bea and by cy; ana's interjection p3 is a
# question (no answer form) by an actor dov's reply does not name, so it is no candidate.
TIE = HELLO + [("p1", "bea", "Dov, which port should we use?"), ("p2", "cy", "Dov, which port is open?"),
               ("p3", "ana", "Is lunch at noon?"), ("p4", "dov", "Bea, Cy, port 80 works.")]
TIE_CUES = ["addressed", "open_question", "vocative"]


def _conv(svc, cid, rows, sizes):
    """ingest `rows` in batches of the given sizes (the last size repeats); returns the
    responses and the fold of them"""
    turns, outs, i, k = _turns(rows), [], 0, 0
    while i < len(turns):
        n = sizes[min(k, len(sizes) - 1)]
        outs.append(svc.conversation_turns(cid, "channel", turns[i:i + n]))
        i, k = i + n, k + 1
    return outs


def _fold(rows, outs):
    f = DeltaFold()
    f.turns(_turns(rows))
    for o in outs:
        f.apply(o)
    return f


def test_tie_is_held_open_never_tiebroken(base):
    """Two candidates with EQUAL cue sets: neither strictly dominates, so the turn is
    held -- no recency or alphabetical tiebreak picks one; nothing is answered."""
    out = _disc(base, TIE)
    assert _rows(out, {"p4"}) == {"p4": ([], "held", "held", ["bea", "cy"], [])}
    assert _cands(out, "p4") == {"p1": TIE_CUES, "p2": TIE_CUES}
    assert {"p1", "p2"} <= set(out["open_questions"])


def test_dominance_strong_vs_weak(base):
    """strong = the winner strictly dominates every rival with >= 2 distinct cues; weak =
    exactly one cue (then it is necessarily the sole candidate)."""
    out = _disc(base, TIE)
    assert _rows(out, {"h2", "p1", "p2"}) == {
        "h2": (["h1"], "tracked", "weak", [], []),           # adjacency only
        "p1": (["h4"], "tracked", "strong", ["dov"], []),    # adjacent + vocative
        # vocative only (weak) at p2's step; dov's held p4 takes it up (dov wrote h4): strong
        "p2": (["h4"], "tracked", "strong", ["dov"], [])}
    assert _cands(out, "h2") == {"h1": ADJ} and _cands(out, "p1") == {"h4": ["adjacent", "vocative"]}
    for t in out["turns"]:
        if t["confidence"] == "weak":
            assert len(t["candidates"]) == 1 and len(t["candidates"][0]["cues"]) == 1


def test_uptake_collapses_a_held_turn_via_turns_delta(srv_svc):
    """bea (author of candidate p1) takes up dov's held p4: p1 gains `uptake`, now
    strictly dominates p2, so p4 collapses (strong) in a turns_delta of the LATER batch;
    the late collapse answers p1 and closes it. One shot over the same turns gives the
    same structure directly."""
    rows = TIE + [("p5", "bea", "Thanks Dov, that works.")]
    outs = _conv(srv_svc, "trk:uptake", rows, [len(TIE), 1])
    assert outs[0]["turns_delta"] == [] and outs[0]["open_questions"][:2] == ["p1", "p2"]
    d = {x["id"]: x for x in outs[1]["turns_delta"]}
    assert set(d) == {"p4"}
    assert (d["p4"]["responds_to"], d["p4"]["basis"], d["p4"]["confidence"], d["p4"]["answers"]) == \
        (["p1"], "tracked", "strong", ["p1"])
    assert {c["ref"]: c["cues"] for c in d["p4"]["candidates"]} == {
        "p1": ["addressed", "open_question", "uptake", "vocative"], "p2": TIE_CUES}
    assert d["p4"]["addressees"] == ["bea", "cy"]  # a late collapse infers no address
    assert "p1" not in outs[1]["open_questions"] and "p2" in outs[1]["open_questions"]
    fin = srv_svc.conversation_close("trk:uptake")
    f = _fold(rows, outs + [fin])
    one = eq.discourse(*_fork(srv_svc), {"window_id": "w", "kind": "channel"}, _turns(rows))
    assert f.structure() == _structure(srv_svc, one)
    assert _rows(one, {"p4"}) == {"p4": (["p1"], "tracked", "strong", ["bea", "cy"], ["p1"])}


def test_author_speaking_again_freezes_a_held_turn(srv_svc):
    """dov speaks again before anyone takes p4 up: p4 leaves the frontier, FROZEN and
    still held (re-emitted once, unchanged); bea's later reply cannot revise it."""
    rows = TIE + [("p5", "dov", "Also the cache is warm."), ("p6", "bea", "Thanks Dov, that works.")]
    outs = _conv(srv_svc, "trk:freeze", rows, [len(TIE), 1])
    held = next(t for t in outs[0]["turns"] if t["id"] == "p4")
    d1 = {x["id"]: x for x in outs[1]["turns_delta"]}
    assert d1["p4"] == {k: held[k] for k in d1["p4"]}  # unchanged, now final
    # Amendment A: dov's p5 settles a reply onto ana's p3 and dov is a member of p3's
    # topic p2 (his p4 is under it): TOPIC uptake revises p3 (its reply is unchanged)
    assert set(d1) == {"p3", "p4"}
    assert (d1["p3"]["topic_id"], d1["p3"]["topic_candidates"]) == ("p2", [{"ref": "p2", "cues": ["uptake", "via_reply"]}])
    assert all(x["id"] != "p4" for x in outs[2]["turns_delta"])
    fin = srv_svc.conversation_close("trk:freeze")
    assert all(x["id"] != "p4" for x in fin["turns_delta"])
    f = _fold(rows, outs + [fin])
    assert f.structure()["p4"]["basis"] == "held"


def test_weak_upgraded_never_overturned_and_strong_frozen(srv_svc):
    """A weak collapse rests on its SOLE candidate (cues are non-empty, a strict subset of
    one cue is empty), so new cues can only upgrade it to strong on the same parent --
    never overturn it. Strong and declared collapses are frozen: never in turns_delta."""
    rows = HELLO + [("s1", "ana", "Bea, can you check the logs?"), ("s2", "bea", "Yes.", {"reply_to": "s1"})]
    outs = _conv(srv_svc, "trk:weak", rows, [4, 1])
    assert _rows(outs[0], {"h2"})["h2"] == (["h1"], "tracked", "weak", [], [])
    d = {x["id"]: x for x in outs[1]["turns_delta"]}
    # ana (author of h2's candidate h1) took h2 up: weak -> strong, same parent
    assert (d["h2"]["responds_to"], d["h2"]["confidence"]) == (["h1"], "strong")
    assert d["h2"]["candidates"] == [{"ref": "h1", "cues": ["adjacent", "uptake"]}]
    fin = srv_svc.conversation_close("trk:weak")
    strong = {t["id"] for o in outs for t in o["turns"] if t["confidence"] in ("strong", "declared")}
    assert "s2" in strong
    for o in outs[1:] + [fin]:
        assert not strong & {x["id"] for x in o["turns_delta"]}
    _fold(rows, outs + [fin])  # the fold also asserts: no strong / declared revised, no retraction


def test_close_emits_the_frozen_frontier(srv_svc):
    outs = _conv(srv_svc, "trk:close", TIE, [len(TIE)])
    fin = srv_svc.conversation_close("trk:close")
    frontier = {t["id"] for t in outs[0]["turns"] if t["confidence"] in ("held", "weak")}
    # every actor's last held / weak turn is still revisable at close: p4 (dov), p3 (ana);
    # bea's p1 is strong, cy's p2 was upgraded to strong by dov's held p4 (uptake); h2 / h3
    # / h4 were frozen when their authors spoke again
    assert {x["id"] for x in fin["turns_delta"]} == {"p3", "p4"} <= frontier
    assert next(x for x in fin["turns_delta"] if x["id"] == "p4")["basis"] == "held"
    assert fin["turns"] == [] and fin["quanta_delta"] == [] and fin["episodes_delta"] == []


def _fork(svc):
    return svc.snap.fork(), svc.root


def _structure(svc, out):
    from equilibrium_delta_fold import STRUCT

    from services.equilibrium_classifier.server import conversation_to_wire
    wire = conversation_to_wire({**out, "conversation_id": "x", "seq": 1, "turns_delta": [],
                                 "quanta_delta": [], "episodes_delta": []}, eq.TAXONOMY_VERSION)
    return {t["id"]: {k: t[k] for k in STRUCT} for t in wire["turns"]}


REVISING = {
    "uptake": TIE + [("p5", "bea", "Thanks Dov, that works."), ("p6", "cy", "Bea, ok."),
                     ("p7", "dov", "Cy, you can use 81.")],
    "freeze": TIE + [("p5", "dov", "Also the cache is warm."), ("p6", "bea", "Thanks Dov, that works.")],
    "weak": HELLO + [("s1", "ana", "Bea, can you check the logs?"), ("s2", "bea", "Yes.", {"reply_to": "s1"}),
                     ("s3", "cy", "Interesting."), ("s4", "ana", "Thanks, could you also restart the worker?"),
                     ("s5", "bea", "Done.")],
    **WINDOWS,
}


@pytest.mark.parametrize("name", sorted(REVISING))
def test_fold_turns_delta_equals_one_shot_at_every_prefix(srv_svc, name):
    """For every batch size: after every batch, folding turns_delta over the first
    emissions gives exactly the one-shot structure of the same prefix (and the fold
    checks the contract invariants of every emitted row)."""
    rows = REVISING[name]
    revised = 0
    for size in range(1, len(rows) + 1):
        outs = _conv(srv_svc, f"trk:fold:{name}:{size}", rows, [size])
        f = DeltaFold()
        f.turns(_turns(rows))
        for k, o in enumerate(outs, 1):
            f.apply(o)
            revised += len(o["turns_delta"])
            upto = min(k * size, len(rows))
            one = eq.discourse(*_fork(srv_svc), {"window_id": "w", "kind": "channel"}, _turns(rows[:upto]))
            assert f.structure() == _structure(srv_svc, one), (name, size, upto)
        f.apply(srv_svc.conversation_close(f"trk:fold:{name}:{size}"))
    if name in ("uptake", "freeze", "weak"):
        assert revised  # revisions are exercised


def test_cue_codebook_is_closed_and_candidates_bounded(base):
    """The seeded EqTrkCue codebook is exactly the contract's; every emitted cue is a
    codebook code; candidate sets stay bounded (<= 16) on a long synthetic window."""
    from test_equilibrium_discourse_service import synthetic_window

    from services.equilibrium_classifier.server import CUE_CODES
    _, root, snap = base
    n = eq._native(snap.fork())
    codes = {n.node(k)["attrs"]["code"] for k in n.neighbours(root, "eq_has_trk_cue")}
    assert codes == set(CUE_CODES) == {"adjacent", "open_question", "addressed", "vocative", "second_person",
                                       "contrast", "answer_form", "same_thread", "uptake"}
    for kind, seed in (("meeting", 31), ("channel", 32)):
        _, turns = synthetic_window(300, seed=seed, kind=kind)
        out = _disc(base, [(t["id"], t["actor_ref"], t["text"], {k: v for k, v in t.items()
                                                                  if k in ("reply_to", "ts_ms")})
                           for t in turns], kind=kind)
        sizes = [len(t["candidates"]) for t in out["turns"]]
        assert max(sizes) <= 16
        assert {c for t in out["turns"] for x in t["candidates"] for c in x["cues"]} <= codes
        assert {t["basis"] for t in out["turns"]} >= {"tracked", "held"}


def test_batch_endpoint_carries_turns_delta(srv_svc):
    """/_batch: every item result carries turns_delta; with close:true it also carries the
    close's frozen frontier (the item's own turns excluded, one entry per id)."""
    turns = _turns(TIE + [("p5", "bea", "Thanks Dov, that works.")])
    r1 = srv_svc.conversation_batch([{"conversation_id": "trk:b", "kind": "channel", "turns": turns[:-1]}])
    assert r1["results"][0]["turns_delta"] == []
    r2 = srv_svc.conversation_batch([{"conversation_id": "trk:b", "kind": "channel", "turns": turns[-1:],
                                      "close": True}])["results"][0]
    ids = [x["id"] for x in r2["turns_delta"]]
    assert ids[0] == "p4" and len(ids) == len(set(ids)) and "p5" not in ids
    assert set(ids) == {"p4", "p3"}  # the taken-up p4, then the frozen frontier
    assert "trk:b" not in srv_svc.sessions


# ---- 0.8.0 rev (T3g): held turns take part; a question stays live -------------------
# CHAIN: dov's c4 is HELD between two equal cue sets (c1 by bea, c2 by cy); bea's c6 is
# HELD itself (dov's c4 vs ana's c3, equal sets) but has c4 among its candidates and bea
# wrote c1, so c1 gains `uptake` and c4 collapses (next-turn proof procedure from a held
# turn); dov's c7 then takes c6 up (dov wrote c4), so c6 collapses in turn (chained).
CHAIN = HELLO + [("c1", "bea", "Dov, the port is 80."), ("c2", "cy", "Dov, the port is 81."),
                 ("c3", "ana", "Bea, the cache is warm."), ("c4", "dov", "Bea, Cy, ok."),
                 ("c5", "cy", "Ana, ok."), ("c6", "bea", "Dov, Ana, noted."), ("c7", "dov", "Bea, great.")]
# LIVE: ana asks bea; bea first starts something else (a question to cy, answered by
# cy); bea answers ana later. The question stays open and keeps proposing itself to bea
# (a question opens a topic; the answer is free form and need not come next).
LIVE = HELLO + [("l1", "ana", "Bea, what is the status of the build?"),
                ("l2", "bea", "Cy, are you coming to lunch?"), ("l3", "cy", "Yes, in a minute."),
                ("l4", "bea", "The build passed this morning.")]
# HELDQ: dov's QUESTION p4 is held (equal cue sets on bea's p1 and cy's p2).
HELDQ = HELLO + [("p1", "bea", "Dov, which port should we use?"), ("p2", "cy", "Dov, which port is open?"),
                 ("p3", "ana", "Is lunch at noon?"), ("p4", "dov", "Bea, Cy, is port 80 free?")]


def test_uptake_from_a_held_later_turn_and_chained_resolution(srv_svc):
    outs = _conv(srv_svc, "trk:chain", CHAIN, [len(CHAIN) - 3, 1])
    first = {t["id"]: t for o in outs for t in o["turns"]}
    assert first["c4"]["basis"] == "held" and first["c6"]["basis"] == "held"
    d6 = {x["id"]: x for x in outs[2]["turns_delta"]}  # c6's batch: bea's HELD c6 took c4 up
    assert (d6["c4"]["responds_to"], d6["c4"]["confidence"]) == (["c1"], "strong")
    assert {c["ref"]: c["cues"] for c in d6["c4"]["candidates"]} == {
        "c1": ["addressed", "uptake", "vocative"], "c2": ["addressed", "vocative"]}
    d7 = {x["id"]: x for x in outs[3]["turns_delta"]}  # c7's batch: dov took c6 up (chain)
    assert (d7["c6"]["responds_to"], d7["c6"]["basis"], d7["c6"]["confidence"]) == (["c4"], "tracked", "strong")
    assert {c["ref"]: c["cues"] for c in d7["c6"]["candidates"]} == {
        "c3": ["addressed", "vocative"], "c4": ["addressed", "uptake", "vocative"]}
    fin = srv_svc.conversation_close("trk:chain")
    one = eq.discourse(*_fork(srv_svc), {"window_id": "w", "kind": "channel"}, _turns(CHAIN))
    assert _fold(CHAIN, outs + [fin]).structure() == _structure(srv_svc, one)


def test_question_stays_live_through_other_talk(srv_svc):
    """No relevance lapse by intervening talk: bea's l2 (a new question to cy) neither
    answers nor retires l1, which stays open and LIVE. Amendment A: l4 is not in l1's
    slot (bea spoke since) and has no answer form, so l1 is no reply rival of the
    adjacent l3 -- l4 replies to l3 locally -- but l1 is the TOPIC l4 is under (l2 was
    resolved by cy's polar "Yes" and downdated), so l1 is engaged, not unanswered."""
    out = _conv(srv_svc, "trk:live", LIVE, [len(LIVE)])[0]
    assert _rows(out, {"l2"})["l2"][4] == [] and _rows(out, {"l4"}) == {
        "l4": (["l3"], "tracked", "strong", ["cy"], [])}
    assert _cands(out, "l4") == {"l3": ["addressed", "adjacent"]}
    assert _topic(out, "l2") == ("l1", {"l1": ["open_question"]})
    assert _topic(out, "l4") == ("l1", {"l1": ["open_question"]})
    assert "l1" in out["open_questions"]
    sess = srv_svc.sessions["trk:live"]
    n = eq._native(sess.branch)
    assert n.neighbours(sess.state.w, "eq_qud_lapsed") == []  # nothing superseded l1
    srv_svc.conversation_close("trk:live")


def test_superseded_question_is_recorded_and_stays_open(srv_svc):
    """A newer room question by the same asker replaces the asker's QUD-top pointer: the
    older one is recorded as lapsed (`w -eq_qud_lapsed-> q`, eval read-out) but stays in
    the open-question set (its absence of an answer remains noticeable)."""
    rows = HELLO + [("u1", "ana", "Who owns the cache?"), ("u3", "ana", "Which team runs the build?")]
    out = _conv(srv_svc, "trk:lapse", rows, [len(rows)])[0]
    assert {"u1", "u3"} <= set(out["open_questions"])
    sess = srv_svc.sessions["trk:lapse"]
    n = eq._native(sess.branch)
    assert [n.node(x)["attrs"]["eq_ref"] for x in n.neighbours(sess.state.w, "eq_qud_lapsed")] == ["u1"]
    srv_svc.conversation_close("trk:lapse")


def test_held_turn_takes_part_in_turn_dependent_state(base):
    """What depends on the TURN ITSELF applies to a held turn: a held question opens a
    QUD (addressed to its vocatives, so it proposes itself to them), names its
    addressees, and takes its author's pending addresses; only what depends on its
    PARENT (answering, the parent's author as addressee) waits for a collapse."""
    out = _disc(base, HELDQ)
    assert _rows(out, {"p4"}) == {"p4": ([], "held", "held", ["bea", "cy"], [])}  # vocatives
    assert _cands(out, "p4") == {"p1": ["addressed", "open_question", "vocative"],
                                 "p2": ["addressed", "open_question", "vocative"]}
    assert "p4" in out["open_questions"]                                  # a held question is a FPP
    # bea's answer: the held question is her candidate (open question addressed to her)
    out = _disc(base, HELDQ + [("p5", "bea", "Port 80 is free.")])
    assert _cands(out, "p5")["p4"] == ["addressed", "adjacent", "open_question"]
    assert _rows(out, {"p5"})["p5"][4] == ["p4"] and "p4" not in out["open_questions"]
    # dov's held p4 took his pending addresses (p1, p2): his next turn gets no pending
    # candidate (nor an `addressed` cue) -- only the adjacent room question p3 (whose
    # slot dov's own p4 already took: no open_question cue, Amendment A)
    out = _disc(base, HELDQ + [("p5", "dov", "Port 80 then.")])
    assert _cands(out, "p5") == {"p3": ["adjacent"]}


@pytest.mark.parametrize("name", ["chain", "live", "heldq"])
def test_fold_equals_one_shot_with_held_uptake(srv_svc, name):
    """fold(turns_delta) == one shot at every prefix and every batch size, for the windows
    where a HELD later turn takes an earlier held turn up (and chains)."""
    rows = {"chain": CHAIN, "live": LIVE, "heldq": HELDQ + [("p5", "bea", "Port 80 is free.")]}[name]
    REVISING[f"rev_{name}"] = rows
    try:
        test_fold_turns_delta_equals_one_shot_at_every_prefix(srv_svc, f"rev_{name}")
    finally:
        del REVISING[f"rev_{name}"]
