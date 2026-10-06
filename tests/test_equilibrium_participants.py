"""Equilibrium conversation PARTICIPANTS roster (track T3f, pack 0.7.0).

POST /v1/conversations/{id}/turns and every /_batch item accept an optional
`participants: [{"actor_ref", "aliases"?}]` (<= 500 per call, <= 8 aliases of 1..64
chars; cumulative per conversation). Name-mention addressing (seeded rule
eq.trk.addressee.participant) matches any alias, or the actor_ref name form, of a
participant -- including one who has not spoken yet. Aliases are transient content:
never logged, never returned. Without a roster the output is unchanged.

Synthetic pseudonymous data only (ana / bea / cy / dov, invented aliases)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
os.environ.setdefault("OZMA_NO_LLM", "1")

from equilibrium_delta_fold import DeltaFold  # noqa: E402
from test_equilibrium_classifier_service import _free_port, _req, _start, _stop  # noqa: E402

from services.equilibrium_classifier import server as srv  # noqa: E402

# a token that occurs nowhere else: if it ever reaches a response or log, it leaked
SECRET = "Zorblax Quimby"


def T(i, a, text, **kw):
    return {"id": i, "actor_ref": a, "text": text, **kw}


HELLO = [T("h1", "ana", "Morning all."), T("h2", "bea", "Hi there.")]


@pytest.fixture(scope="module")
def svc():
    return srv.ClassifierService(max_conversations=64)


def _by_id(out):
    return {t["id"]: (t["responds_to"], t["addressees"], t["answers"]) for t in out["turns"]}


def _fold(chunks, outs):
    f = DeltaFold()
    for c, o in zip(chunks, outs):
        f.turns(c)
        f.apply(o)
    return f


# ---- validation ----------------------------------------------------------------------
def _conv(**extra):
    return {"kind": "meeting", "turns": [T("v1", "ana", "hi")], **extra}


def test_roster_validation_paths_only():
    tax = "eq-tax-0.8.0"
    kind, turns, roster = srv.validate_conversation(_conv(), tax)
    assert roster is None
    _, _, roster = srv.validate_conversation(
        _conv(participants=[{"actor_ref": "ana", "aliases": ["Ana B", "@ana"]}, {"actor_ref": "zed"}]), tax)
    assert roster == [{"actor_ref": "ana", "aliases": ["Ana B", "@ana"]}, {"actor_ref": "zed", "aliases": []}]
    bad = [
        ({"participants": {"actor_ref": "x"}}, 400),
        ({"participants": [{"aliases": [SECRET]}]}, 400),
        ({"participants": [{"actor_ref": "x", "aliases": [SECRET], "role": "chair"}]}, 400),
        ({"participants": [{"actor_ref": "bad ref", "aliases": [SECRET]}]}, 400),
        ({"participants": [{"actor_ref": "x", "aliases": [SECRET] * 9}]}, 400),
        ({"participants": [{"actor_ref": "x", "aliases": [""]}]}, 400),
        ({"participants": [{"actor_ref": "x", "aliases": [SECRET * 5]}]}, 400),
        ({"participants": [{"actor_ref": "x", "aliases": [7]}]}, 400),
        ({"participants": [{"actor_ref": f"p{i}"} for i in range(501)]}, 413),
    ]
    for extra, status in bad:
        with pytest.raises(srv.ApiError) as e:
            srv.validate_conversation(_conv(**extra), tax)
        assert e.value.status == status
        assert "orblax" not in e.value.message.lower()  # paths only, never input
    assert len(srv.validate_conversation(
        _conv(participants=[{"actor_ref": f"p{i}", "aliases": ["a" * 64] * 8} for i in range(500)]), tax)[2]) == 500
    items = srv.validate_batch({"items": [
        {"conversation_id": "b1", "kind": "meeting", "turns": [], "participants": [{"actor_ref": "ana"}]},
        {"conversation_id": "b2", "kind": "meeting", "turns": []}]}, tax)
    assert items[0]["participants"] == [{"actor_ref": "ana", "aliases": []}] and "participants" not in items[1]
    with pytest.raises(srv.ApiError) as e:
        srv.validate_batch({"items": [{"conversation_id": "b1", "kind": "meeting", "turns": [],
                                       "participants": [{"actor_ref": "x", "aliases": [SECRET] * 9}]}]}, tax)
    assert e.value.message.startswith("$.items[0].participants[0].aliases") and "orblax" not in e.value.message.lower()


# ---- addressing ------------------------------------------------------------------------
def test_alias_addresses_a_participant_who_has_not_spoken(svc):
    roster = [{"actor_ref": "u7", "aliases": ["Dana Scully", "@dana"]}, {"actor_ref": "cy"}]
    b1 = HELLO + [T("m1", "ana", "Dana Scully, what do you think about the cache?"),
                  T("m2", "ana", "Cy can you check the logs?"),
                  T("m3", "bea", "Fair point, dana."),
                  T("m4", "ana", "Scully alone is only half an alias."),
                  T("m5", "bea", "Did you see that, Ana?")]
    o1 = svc.conversation_turns("pt:alias", "meeting", b1, roster)
    r = _by_id(o1)
    assert r["m1"][1] == ["u7"] and r["m2"][1] == ["cy"]       # alias (2 tokens) / actor_ref name form
    # one-token alias; a partial alias is no match: m4 names nobody. bea's m5 takes up m4
    # (weak on bea's m3 -> strong, late), but addressees are causal (Amendment A fix: no
    # late addressee -- the per-turn evidence read m4's addressee set at m4's own batch)
    assert r["m3"][1] == ["u7"] and r["m4"][1] == []
    assert r["m5"][1] == ["ana"]                               # a speaker's name: T1 as before
    assert o1["open_questions"] == ["m1", "m2", "m5"]
    acks = [d for d in o1["quanta_delta"] if d.get("actor_ref") == "u7"]
    assert [(d["trait"], d["target_ref"], d["evidence_add"], d["match"]) for d in acks] == [
        ("competence.acknowledged", "bea", ["m3"], "partial")]  # a quantum on a participant who never spoke
    # the participant's first turn: the question addressed to it (m1) is a candidate (its
    # conditional-relevance slot: u7's first turn after it), with the pending address m3
    # and the adjacent m5 (bea's question to ana: not for u7, and an assertion is no
    # answer FORM -- Amendment A). m1 dominates m3 but not m5, so m6 is HELD and answers
    # nothing (0.7.0 forced m1 and closed it)
    o2 = svc.conversation_turns("pt:alias", "meeting", [T("m6", "u7", "The cache is fine, I checked it.")])
    m6 = o2["turns"][0]
    assert (m6["basis"], m6["answers"]) == ("held", [])
    assert {c["ref"]: c["cues"] for c in m6["candidates"]} == {
        "m1": ["addressed", "open_question"], "m3": ["addressed"], "m5": ["adjacent"]}
    assert o2["open_questions"] == ["m1", "m2", "m5"]
    # the same turns without a roster: no participant addressing
    o3 = svc.conversation_turns("pt:alias:none", "meeting", b1)
    r3 = _by_id(o3)
    assert r3["m1"][1] == [] and r3["m2"][1] == [] and r3["m3"][1] != ["u7"]


def test_second_person_rules_unchanged(svc):
    roster = [{"actor_ref": "dov", "aliases": ["Dovid"]}]
    rows = HELLO + [T("s1", "ana", "Bea, can you check the logs?"),
                    T("s2", "bea", "I checked them, you were right."),
                    T("s3", "ana", "Could you also ping Dovid?")]
    with_r = _by_id(svc.conversation_turns("pt:2p:r", "channel", rows, roster))
    without = _by_id(svc.conversation_turns("pt:2p:n", "channel", rows))
    assert with_r["s2"] == without["s2"] == (["s1"], ["ana"], ["s1"])  # second person -> last addresser
    assert without["s3"][1] == ["bea"] and with_r["s3"][1] == ["dov"]  # an explicit mention takes precedence


def test_roster_is_cumulative_and_causal(svc):
    """A roster entry applies from its call on: later batches see it; earlier turns are
    never re-addressed (tracked structure is causal)."""
    b1 = HELLO + [T("c1", "ana", "Has Quill seen the report?")]
    b2 = [T("c2", "bea", "Quill, the report is in your inbox.")]
    b3 = [T("c3", "ana", "Thanks Quill.")]
    o1 = svc.conversation_turns("pt:cum", "meeting", b1)
    o2 = svc.conversation_turns("pt:cum", "meeting", b2, [{"actor_ref": "u9", "aliases": ["Quill"]}])
    o3 = svc.conversation_turns("pt:cum", "meeting", b3)  # no roster in this call: still applies
    assert _by_id(o1)["c1"][1] == [] and _by_id(o2)["c2"][1] == ["u9"] and _by_id(o3)["c3"][1] == ["u9"]
    # re-sending an entry (and an alias already held) changes nothing
    o4 = svc.conversation_turns("pt:cum", "meeting", [T("c4", "bea", "Quill?")],
                                [{"actor_ref": "u9", "aliases": ["quill", "QUILL"]}])
    assert _by_id(o4)["c4"][1] == ["u9"]


def test_incremental_equals_one_shot_with_roster(svc):
    roster = [{"actor_ref": "u7", "aliases": ["Dana Scully", "dana"]}, {"actor_ref": "cy", "aliases": ["Cyrus"]}]
    rows = HELLO + [T("i1", "ana", "Dana Scully, can you review the patch?"),
                    T("i2", "bea", "Cyrus, you're right about the cache."),
                    T("i3", "u7", "As a nurse I see this weekly."),
                    T("i4", "ana", "Good point, dana."),
                    T("i5", "cy", "The cache is cold."),
                    T("i6", "bea", "Dana, is the patch ready?"),
                    T("i7", "u7", "It is ready, tests pass.")]
    one = svc.conversation_turns("pt:one", "meeting", rows, roster)
    chunks = [rows[i:i + 3] for i in range(0, len(rows), 3)]
    outs = [svc.conversation_turns("pt:inc", "meeting", c, roster if k == 0 else None) for k, c in enumerate(chunks)]
    f1, f2 = _fold([rows], [one]), _fold(chunks, outs)
    assert f1.quanta() == f2.quanta() and f1.episodes() == f2.episodes()
    # 0.8.0: labels never change; structure equals one shot after folding turns_delta
    static = ("id", "labels")  # Amendment A: topic_id is folded structure (revisable)
    assert [{k: t[k] for k in static} for o in outs for t in o["turns"]] == \
        [{k: t[k] for k in static} for t in one["turns"]]
    assert f1.structure() == f2.structure()
    assert outs[-1]["open_questions"] == one["open_questions"]


def test_roster_without_mentions_changes_nothing(svc):
    """Participants only ADD behaviour: a roster naming the speakers with aliases that
    never occur leaves every response byte-identical."""
    from test_equilibrium_discourse_service import synthetic_window
    turns = synthetic_window(240, seed=78, kind="meeting")[1]
    actors = sorted({t["actor_ref"] for t in turns})
    roster = [{"actor_ref": a, "aliases": [SECRET, "Xq Wibble"]} for a in actors] + [{"actor_ref": "never_speaks"}]
    a = [svc.conversation_turns("pt:none:a", "meeting", turns[i:i + 50]) for i in range(0, 240, 50)]
    b = [svc.conversation_turns("pt:none:b", "meeting", turns[i:i + 50], roster if i == 0 else None)
         for i in range(0, 240, 50)]
    strip = lambda o: json.dumps({k: v for k, v in o.items() if k != "conversation_id"}, sort_keys=True)
    assert [strip(x) for x in a] == [strip(x) for x in b]


def test_aliases_are_never_returned(svc):
    roster = [{"actor_ref": "u5", "aliases": [SECRET, "Zorblax"]}]
    out = svc.conversation_turns("pt:leak", "meeting", HELLO + [T("l1", "ana", "Zorblax, good point.")], roster)
    assert out["turns"][-1]["addressees"] == ["u5"]
    fin = svc.conversation_close("pt:leak")
    for doc in (out, fin, svc.info()):
        assert "orblax" not in json.dumps(doc).lower() and "quimby" not in json.dumps(doc).lower()


def test_http_turns_and_batch_with_roster(tmp_path):
    port = _free_port()
    proc, _ = _start(tmp_path, port)
    try:
        roster = [{"actor_ref": "u7", "aliases": [SECRET]}]
        st, body, _ = _req(port, "POST", "/v1/conversations/pt:h1/turns", {
            "kind": "meeting", "participants": roster,
            "turns": HELLO + [T("x1", "ana", "Zorblax Quimby, is the build green?")]})
        assert st == 200 and body["turns"][-1]["addressees"] == ["u7"] and body["open_questions"] == ["x1"]
        st, body, raw = _req(port, "POST", "/v1/conversations/_batch", {"items": [
            {"conversation_id": "pt:h1", "kind": "meeting", "turns": [T("x2", "u7", "It is green now.")]},
            {"conversation_id": "pt:h2", "kind": "meeting", "participants": roster,
             "turns": HELLO + [T("y1", "bea", "Thanks zorblax quimby.")], "close": True}]})
        assert st == 200 and [r["ok"] for r in body["results"]] == [True, True]
        assert body["results"][0]["turns"][0]["answers"] == ["x1"]
        assert body["results"][1]["turns"][-1]["addressees"] == ["u7"]
        st, body, raw = _req(port, "POST", "/v1/conversations/pt:h3/turns", {
            "kind": "meeting", "turns": [], "participants": [{"actor_ref": "u7", "aliases": [SECRET] * 9}]})
        assert st == 400 and b"orblax" not in raw.lower()
        st, info, raw = _req(port, "GET", "/v1/info")
        assert info["limits"]["max_participants_per_call"] == 500 and b"orblax" not in raw.lower()
    finally:
        _stop(proc)
    logs = b"".join(p.read_bytes() for p in tmp_path.glob("server_*.stderr"))
    assert b"orblax" not in logs.lower()
