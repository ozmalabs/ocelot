"""Equilibrium conversation scaling (track T3d, pack 0.5.1): the shared batch
contract POST /v1/conversations/_batch, per-conversation concurrency, and the
live (monotone) strata layer. Synthetic pseudonymous data only."""
from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
os.environ.setdefault("OZMA_NO_LLM", "1")

from test_equilibrium_classifier_service import _free_port, _req, _start, _stop  # noqa: E402
from test_equilibrium_conversations import client_parse_conversation  # noqa: E402
from test_equilibrium_discourse_service import synthetic_window  # noqa: E402

TAX = "eq-tax-0.5.1"


@pytest.fixture(scope="module")
def srv():
    from services.equilibrium_classifier import server
    return server


@pytest.fixture(scope="module")
def svc(srv):
    return srv.ClassifierService(workers=4, max_conversations=200)


def _conv(seed, n=60, kind="thread"):
    return synthetic_window(n, seed=seed, kind=kind)[1]


def _sequential(svc, cid, kind, turns, size):
    return [svc.conversation_turns(cid, kind, turns[i:i + size]) for i in range(0, len(turns), size)]


def _strip(doc):
    return {k: v for k, v in doc.items() if k != "taxonomy_version"}


def test_batch_equals_single_calls_in_request_order(svc):
    convs = [(f"b:eq:{i}", "thread" if i % 2 else "meeting", _conv(900 + i, kind="thread" if i % 2 else "meeting"))
             for i in range(6)]
    ref = {cid: _sequential(svc, f"ref:{cid}", kind, turns, 30) for cid, kind, turns in convs}
    for step in range(2):
        items = [{"conversation_id": cid, "kind": kind, "turns": turns[step * 30:(step + 1) * 30],
                  "close": step == 1} for cid, kind, turns in convs]
        out = svc.conversation_batch(items)
        assert out["ok"] is True and out["taxonomy_version"] == TAX
        assert [r["conversation_id"] for r in out["results"]] == [c for c, _, _ in convs]
        for r, (cid, _, _) in zip(out["results"], convs):
            want = _strip(ref[cid][step])
            want["conversation_id"] = cid
            assert r == want, (cid, step)
    # close:true freed the retained forks
    for cid, _, _ in convs:
        assert cid not in svc.sessions


def test_batch_per_item_errors_do_not_fail_the_batch(svc):
    turns = _conv(950, n=10)
    svc.conversation_turns("b:err:dup", "thread", turns[:5])
    svc.conversation_turns("b:err:kind", "thread", turns[:5])
    items = [{"conversation_id": "b:err:ok", "kind": "thread", "turns": turns[:5]},
             {"conversation_id": "b:err:dup", "kind": "thread", "turns": turns[4:6]},
             {"conversation_id": "b:err:kind", "kind": "meeting", "turns": turns[5:7]},
             {"conversation_id": "b:err:order", "kind": "thread",
              "turns": [dict(turns[1], ts_ms=10), dict(turns[2], ts_ms=5)]}]
    res = svc.conversation_batch(items)["results"]
    assert res[0]["ok"] is True and res[0]["seq"] == 1, res[0]
    assert res[1] == {"conversation_id": "b:err:dup", "ok": False, "error": {
        "code": "duplicate_turn", "message": res[1]["error"]["message"], "retryable": False}}
    assert res[2]["ok"] is False and res[2]["error"]["code"] == "bad_request"
    assert res[3]["ok"] is False and res[3]["error"]["code"] == "out_of_order"
    assert "b:err:order" not in svc.sessions  # a refused first batch leaves no state
    assert svc.conversation_get("b:err:dup")["seq"] == 1  # nothing ingested by the refused item


def test_batch_validation(srv):
    tax = TAX
    v = srv.validate_batch
    ok_item = {"conversation_id": "c1", "kind": "thread", "turns": []}

    def code(doc):
        with pytest.raises(srv.ApiError) as ei:
            v(doc, tax)
        return ei.value.status, ei.value.code
    assert v({"items": [ok_item]}, tax)[0]["close"] is False
    assert code({"items": []}) == (400, "bad_request")
    assert code({"items": [ok_item] * 2}) == (400, "bad_request")  # repeated conversation_id
    assert code({"items": [dict(ok_item, conversation_id="bad id")]}) == (400, "bad_request")
    assert code({"items": [dict(ok_item, extra=1)]}) == (400, "bad_request")
    assert code({"items": [dict(ok_item, close="yes")]}) == (400, "bad_request")
    assert code({"items": [ok_item], "taxonomy_version": "eq-tax-0.0.0"}) == (409, "taxonomy_mismatch")
    many = [dict(ok_item, conversation_id=f"c{i}") for i in range(65)]
    assert code({"items": many}) == (413, "too_large")
    t = [{"id": f"t{i}", "actor_ref": "a", "text": "x"} for i in range(100)]
    big = [{"conversation_id": f"c{i}", "kind": "thread", "turns": t} for i in range(21)]
    assert code({"items": big}) == (413, "too_large")  # 2,100 > 2,000 turns
    assert code({"items": [dict(ok_item, turns=t + t[:1])]}) == (413, "too_large")  # > 100 per item
    bad_turn = dict(ok_item, turns=[{"id": "t", "actor_ref": "a"}])
    with pytest.raises(srv.ApiError) as ei:
        v({"items": [ok_item, dict(bad_turn, conversation_id="c2")]}, tax)
    assert ei.value.code == "bad_request" and ei.value.message.startswith("$.items[1].turns[0].text")


def test_concurrent_conversations_equal_sequential(srv, svc):
    convs = [(f"cc:{i}", _conv(970 + i, n=80)) for i in range(8)]
    ref = {cid: _sequential(svc, f"ref:{cid}", "thread", t, 20) for cid, t in convs}
    got: dict = {}
    errs = []

    def run(cid, turns):
        try:
            got[cid] = _sequential(svc, cid, "thread", turns, 20)
        except Exception as e:  # pragma: no cover - surfaced below
            errs.append(repr(e))
    th = [threading.Thread(target=run, args=c) for c in convs]
    [t.start() for t in th]
    [t.join() for t in th]
    assert not errs
    for cid, _ in convs:
        assert [_strip(d) | {"conversation_id": "x"} for d in got[cid]] == \
            [_strip(d) | {"conversation_id": "x"} for d in ref[cid]]
    assert tuple(svc.snap.source_revision) == svc.rev0 and svc._strong_check()


def test_same_conversation_batches_serialise(svc):
    """Concurrent batches of ONE conversation are serialised by its lock: every
    batch is ingested exactly once and the seqs are 1..n."""
    turns = _conv(990, n=40)
    chunks = [turns[i:i + 5] for i in range(0, 40, 5)]
    svc.conversation_turns("ser:1", "thread", chunks[0])
    seqs, lock = [], threading.Lock()

    def run(ch):
        try:
            out = svc.conversation_turns("ser:1", "thread", ch)
            with lock:
                seqs.append(out["seq"])
        except srv_api_error() as e:
            with lock:
                seqs.append(e.code)
    th = [threading.Thread(target=run, args=(c,)) for c in chunks[1:]]
    [t.start() for t in th]
    [t.join() for t in th]
    ok = sorted(s for s in seqs if isinstance(s, int))
    assert ok == list(range(2, 2 + len(ok)))  # no lost / doubled batch
    # chunks may arrive out of time order: those are refused atomically
    assert all(s == "out_of_order" for s in seqs if not isinstance(s, int))
    assert svc.conversation_get("ser:1")["seq"] == 1 + len(ok)


def srv_api_error():
    from services.equilibrium_classifier.server import ApiError
    return ApiError


@pytest.mark.parametrize("kind,seed", [("thread", 1201), ("meeting", 1202)])
def test_incremental_engine_flags_equal_committed_engine(srv, monkeypatch, kind, seed):
    """The four evaluation flags (semi-naive batch rules, isolated-node exemption,
    incremental_match, precise_dirty, empty-match proof) reach the same read-out as
    the committed engine (all flags off) on a multi-batch conversation."""
    from domains import equilibrium_classify as ec
    turns = _conv(seed, n=150, kind=kind)
    on = srv.ClassifierService(workers=1)
    got_on = _sequential(on, "f", kind, turns, 50) + [on.conversation_close("f")]
    monkeypatch.setattr(ec, "incremental_engine", lambda n: None)
    off = srv.ClassifierService(workers=1)
    got_off = _sequential(off, "f", kind, turns, 50) + [off.conversation_close("f")]
    assert got_on == got_off


def test_new_engine_flags_default_off():
    from domains import equilibrium_classify as ec
    base, root = ec.boot()
    b = base.snapshot().fork()
    n = ec._native(b)
    # defaults: no exemption, no semi-naive batch path -> a batch rule re-enumerates;
    # the setters exist and are idempotent
    for name in ("set_fresh_node_exempt", "set_batch_incremental"):
        getattr(n, name)(False)
        getattr(n, name)(False)
    st = ec.conversation_open(b, root, "c", "thread")  # turns the flags on for this fork
    out = ec.conversation_ingest(b, root, st, _conv(1203, n=5))
    assert out["seq"] == 1 and len(out["turns"]) == 5


def test_busy_session_is_never_evicted(srv):
    s = srv.ClassifierService(max_conversations=1, workers=2)
    s.conversation_turns("ev:a", "thread", _conv(991, n=5))
    sess = s.sessions["ev:a"]
    sess.lock.acquire()  # simulate a running batch
    try:
        s.conversation_turns("ev:b", "thread", _conv(992, n=5))  # over the cap, a is busy
        assert "ev:a" in s.sessions and "ev:b" in s.sessions
    finally:
        sess.lock.release()
    s.conversation_turns("ev:c", "thread", _conv(993, n=5))  # now a and b are idle
    assert list(s.sessions) == ["ev:c"] and s.conversations_evicted["lru"] == 2


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("eqbatch")
    port = _free_port()
    proc, _ = _start(tmp, port)
    yield port
    _stop(proc)


def test_http_batch_contract(server):
    st, info, _ = _req(server, "GET", "/v1/info")
    assert st == 200 and info["endpoints"]["/v1/conversations/_batch"] == "ok"
    assert info["taxonomy_version"] == TAX and info["limits"]["max_batch_items"] == 64
    assert info["conversations"]["concurrency"] == "per_conversation_locks"
    convs = [(f"h:{i}", _conv(995 + i, n=20)) for i in range(3)]
    body = {"taxonomy_version": TAX,
            "items": [{"conversation_id": c, "kind": "thread", "turns": t} for c, t in convs]}
    st, doc, _ = _req(server, "POST", "/v1/conversations/_batch", body)
    assert st == 200 and doc["ok"] is True and set(doc) == {"ok", "taxonomy_version", "results"}
    for r, (cid, turns) in zip(doc["results"], convs):
        assert r["conversation_id"] == cid and r["ok"] is True, r
        client_parse_conversation({**r, "taxonomy_version": TAX}, cid, {t["id"] for t in turns}, turns)
    # a conversation literally named "_batch" still has its own /turns route
    st, doc, _ = _req(server, "POST", "/v1/conversations/_batch/turns",
                      {"kind": "thread", "turns": convs[0][1][:2]})
    assert st == 200 and doc["conversation_id"] == "_batch"
    st, doc, _ = _req(server, "POST", "/v1/conversations/_batch", {"items": []})
    assert st == 400 and doc["error"]["code"] == "bad_request"
