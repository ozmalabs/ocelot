"""Equilibrium conversation TRACKING (track T3c stage O2, pack 0.5.0).

Seeded turn cursor (seeds/equilibrium_tracking.json): addressees (name mention of an
actor who has already spoken, second person to the last addresser), tracked
responds_to (most recent compatible open question, else pending address, plus a
contrasted / conceded claim), eq_answers, the open-question set, thread ids.

Synthetic windows only (pseudonyms ana / bea / cy / dov); no corpus, no LLM.
"""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("OZMA_NO_LLM", "1")

from domains import equilibrium_classify as eq  # noqa: E402
from equilibrium_delta_fold import DeltaFold  # noqa: E402

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
    return {t["id"]: (t["responds_to"], t["basis"], t["addressees"], t["answers"])
            for t in out["turns"] if ids is None or t["id"] in ids}


def _q(out):
    return {(q["actor_ref"], q["trait"], q["polarity"], q.get("target_ref")): q for q in out["quanta"]}


def test_non_adjacent_answer(base):
    """A asks B; C and D chat; B answers two turns later."""
    out = _disc(base, HELLO + [
        ("t1", "ana", "Bea, what is the status of the build?"),
        ("t2", "cy", "Dov, did you see the release notes?"),
        ("t3", "dov", "Yes, they look fine to me."),
        ("t4", "bea", "The build passed this morning.")])
    assert _rows(out, {"t1", "t2", "t3", "t4"}) == {
        "t1": ([], "none", ["bea"], []), "t2": ([], "none", ["dov"], []),
        "t3": (["t2"], "tracked", ["cy"], ["t2"]), "t4": (["t1"], "tracked", ["ana"], ["t1"])}
    assert out["open_questions"] == []
    assert _q(out)[("bea", "inquiry.answered", "+", "ana")]["evidence"] == ["t1", "t4"]
    th = {t["id"]: t["thread_id"] for t in out["turns"]}
    assert th["t4"] == th["t1"] == "t1" and th["t3"] == th["t2"] == "t2"


def test_interleaved_two_thread_channel(base):
    """Two interleaved room questions: platform_thread keeps them apart; without it,
    a name mention does; without either, the most recent open question wins."""
    pa, pb = {"platform_thread": "thr_a"}, {"platform_thread": "thr_b"}
    rows = [("x1", "ana", "Which port does the cache use?", pa),
            ("y1", "cy", "Is the deploy window today?", pb),
            ("x2", "bea", "It uses the default port.", pa),
            ("y2", "dov", "Yes, from two to four.", pb)]
    out = _disc(base, HELLO + rows)
    assert _rows(out, {"x2", "y2"}) == {"x2": (["x1"], "tracked", ["ana"], ["x1"]),
                                        "y2": (["y1"], "tracked", ["cy"], ["y1"])}
    assert {t["id"]: t["thread_id"] for t in out["turns"] if t["id"][0] in "xy"} == {
        "x1": "thr_a", "x2": "thr_a", "y1": "thr_b", "y2": "thr_b"}
    named = [(i, a, t.replace("It uses", "Ana, it uses")) for i, a, t, _ in rows]
    out = _disc(base, HELLO + named)
    assert _rows(out, {"x2"}) == {"x2": (["x1"], "tracked", ["ana"], ["x1"])}
    bare = [(i, a, t) for i, a, t, _ in rows]
    out = _disc(base, HELLO + bare)
    assert _rows(out, {"x2"})["x2"][0] == ["y1"]  # adjacency-free, but no thread signal


def test_addressee_by_name_mention_only_for_known_actors(base):
    out = _disc(base, HELLO + [("m1", "ana", "Dov, the logs are ready."),
                               ("m2", "ana", "Zed, the logs are ready."),  # zed never spoke
                               ("m3", "dov", "On it.")])
    assert _rows(out, {"m1", "m2", "m3"}) == {
        "m1": ([], "none", ["dov"], []), "m2": ([], "none", [], []),
        "m3": (["m1"], "tracked", ["ana"], [])}


def test_second_person_reply(base):
    out = _disc(base, HELLO + [
        ("s1", "ana", "Bea, can you check the logs?"),
        ("s2", "bea", "I checked them, you were right about the timeout."),
        ("s3", "cy", "Interesting."),
        ("s4", "ana", "Thanks, could you also restart the worker?"),
        ("s5", "bea", "Done.")])
    assert _rows(out, {"s2", "s3", "s4", "s5"}) == {
        "s2": (["s1"], "tracked", ["ana"], ["s1"]), "s3": ([], "none", [], []),
        "s4": (["s2"], "tracked", ["bea"], []), "s5": (["s4"], "tracked", ["ana"], ["s4"])}
    assert out["open_questions"] == []


def test_counter_question_does_not_close(base):
    out = _disc(base, HELLO + [
        ("q1", "ana", "Bea, when will the patch land?"),
        ("q2", "bea", "Which patch do you mean?"),
        ("q3", "ana", "The cache patch."),
        ("q4", "bea", "It lands on Friday.")])
    assert _rows(out, {"q2", "q3", "q4"}) == {
        "q2": (["q1"], "tracked", ["ana"], []),       # counter-question: q1 stays open
        "q3": (["q2"], "tracked", ["bea"], ["q2"]),
        "q4": (["q1"], "tracked", ["ana"], ["q1"])}   # QUD: q1 is the top again
    assert out["open_questions"] == []


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
    assert tb == {"d3": ([], "none", []), "d4": (["d1"], "tracked", ["d1"])}
    assert b["open_questions"] == []
    fin = svc.conversation_close("trk:dismiss")
    f = DeltaFold()  # the client folds the 0.6.0 evidence deltas
    f.turns(rows)
    for out in (a, b, fin):
        f.apply(out)
    keys = {(q["actor_ref"], q["trait"], q.get("target_ref")) for q in f.quanta()}
    assert ("bea", "response.dismissal", "ana") in keys and ("bea", "inquiry.answered", "ana") in keys


def test_declared_reply_is_honoured(base):
    out = _disc(base, HELLO + [("r1", "ana", "Bea, is the cache warm?"),
                               ("r2", "cy", "Is the queue empty?"),
                               ("r3", "dov", "Yes, it is warm.", {"reply_to": "r1"})], kind="thread")
    assert _rows(out, {"r3"}) == {"r3": (["r1"], "declared", ["ana"], ["r1"])}
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
