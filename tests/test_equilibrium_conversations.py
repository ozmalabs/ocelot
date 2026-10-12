"""Equilibrium conversation tracking plumbing (track T3c stage O1, pack 0.5.0).

/v1/conversations/{id}/turns|close + GET: one RETAINED fork of the frozen base per
conversation, incremental ingest, idle-TTL + LRU eviction, strict order, and
"incremental batches == one-shot". Structure in this stage is declared replies only
(basis "declared" / "none"); tracked inference is the next stage.

Synthetic windows only (pseudonyms actor_a / member_###); no corpus, no LLM
(OZMA_NO_LLM=1). Measurements are printed (run with -s to see them).
"""
from __future__ import annotations

import os
import statistics
import time

import pytest

os.environ.setdefault("OZMA_NO_LLM", "1")

from domains import equilibrium_classify as eq  # noqa: E402
from test_equilibrium_classifier_service import (  # noqa: E402  shared harness
    SECRET, _CODE, _client_parse, _free_port, _req, _start, _stop)
from test_equilibrium_climate import CLIMATE  # noqa: E402
from test_equilibrium_discourse import MEETING, THREAD  # noqa: E402
from test_equilibrium_discourse_service import synthetic_window  # noqa: E402
from test_equilibrium_tracking import WINDOWS as TRK_WINDOWS, _turns as _tracking_turns  # noqa: E402

TAX = "eq-tax-0.5.1"
_TOP = {"ok", "taxonomy_version", "conversation_id", "seq", "turns", "quanta", "episodes",
        "open_questions"}
_TURN = {"id", "labels", "responds_to", "basis", "addressees", "thread_id", "topic_id", "answers"}


def _thread(rows):
    return [{"id": i, "actor_ref": a, "text": t, **({"reply_to": r} if r else {})} for i, a, t, r in rows]


def _meeting_declared():
    return [{"id": i, "actor_ref": a, "text": t, **({"reply_to": MEETING[k - 1][0]} if k else {})}
            for k, (i, a, t) in enumerate(MEETING)]


def client_parse_conversation(doc: dict, cid: str, ids_so_far: set[str], batch: list[dict]) -> None:
    """Shared-contract acceptance for one /v1/conversations response."""
    assert set(doc) == _TOP and doc["ok"] is True and doc["conversation_id"] == cid
    assert doc["taxonomy_version"] == TAX and isinstance(doc["seq"], int)
    assert [t["id"] for t in doc["turns"]] == [t["id"] for t in batch]
    for t in doc["turns"]:
        assert set(t) == _TURN, t
        _client_parse(t["labels"])
        assert t["labels"]["id"] == t["id"]
        assert t["basis"] in ("declared", "tracked", "none")
        assert (t["basis"] == "none") == (t["responds_to"] == [])
        assert set(t["responds_to"]) <= ids_so_far and set(t["answers"]) <= ids_so_far
        assert isinstance(t["thread_id"], str) and t["topic_id"] is None
    for q in doc["quanta"]:
        assert set(q["evidence"]) | set(q["counter_evidence"]) <= ids_so_far
        assert q["match"] in ("exact", "partial", "weak")
        assert all(_CODE.fullmatch(r) and r.endswith(":0.5.1") for r in q["rule_ids"])
    for e in doc["episodes"]:
        assert set(e["turns"]) <= ids_so_far
    assert set(doc["open_questions"]) <= ids_so_far


@pytest.fixture(scope="module")
def srv():
    from services.equilibrium_classifier import server
    return server


@pytest.fixture(scope="module")
def svc(srv):
    return srv.ClassifierService()


class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def _err(fn, *a):
    from services.equilibrium_classifier.server import ApiError
    with pytest.raises(ApiError) as ei:
        fn(*a)
    return ei.value.status, ei.value.code


def _key(q):
    return (q["actor_ref"], q["trait"], q["polarity"], q.get("target_ref", ""))


# ---- lifecycle --------------------------------------------------------------
def test_session_lifecycle(svc):
    turns = _thread(THREAD)
    a = svc.conversation_turns("conv:life~1", "thread", turns[:3])
    assert a["seq"] == 1 and [t["id"] for t in a["turns"]] == ["p1", "p2", "p3"]
    client_parse_conversation(a, "conv:life~1", {"p1", "p2", "p3"}, turns[:3])
    g = svc.conversation_get("conv:life~1")
    assert g == {"ok": True, "conversation_id": "conv:life~1", "seq": 1, "idle_ttl_s": 900, "kind": "thread"}
    b = svc.conversation_turns("conv:life~1", "thread", turns[3:])
    assert b["seq"] == 2
    tb = {t["id"]: t for t in b["turns"]}
    # a reply to a turn of an EARLIER batch resolves (id -> node via the attr index)
    assert tb["p4"]["responds_to"] == ["p2"] and tb["p4"]["basis"] == "declared"
    assert tb["p5"]["answers"] == ["p3"] and tb["p5"]["addressees"] == ["member_102"]
    assert a["open_questions"] == ["p3"] and b["open_questions"] == ["p6", "p7"]
    c = svc.conversation_close("conv:life~1")
    assert c["turns"] == [] and c["seq"] == 2 and c["quanta"]
    assert _err(svc.conversation_get, "conv:life~1") == (404, "unknown_conversation")
    assert _err(svc.conversation_close, "conv:life~1") == (404, "unknown_conversation")
    assert "conv:life~1" not in svc.sessions
    # empty batch opens / touches a conversation; kind is fixed at open
    assert svc.conversation_turns("conv:e", "channel", [])["turns"] == []
    assert _err(svc.conversation_turns, "conv:e", "thread", turns[:1]) == (400, "bad_request")
    svc.conversation_close("conv:e")


def test_platform_thread_and_self_reply_threading(svc):
    turns = [{"id": "c1", "actor_ref": "member_1", "text": "Deploy is at noon.", "platform_thread": "T-9"},
             {"id": "c2", "actor_ref": "member_2", "text": "Lunch anyone?"},
             {"id": "c3", "actor_ref": "member_1", "text": "Also the cache.", "reply_to": "c1"},
             {"id": "c4", "actor_ref": "member_3", "text": "Noon works.", "reply_to": "c3"},
             {"id": "c5", "actor_ref": "member_3", "text": "Unknown parent.", "reply_to": "zz"}]
    out = svc.conversation_turns("conv:pt", "channel", turns)
    t = {x["id"]: x for x in out["turns"]}
    assert t["c1"]["thread_id"] == "T-9" and t["c3"]["thread_id"] == "T-9" and t["c4"]["thread_id"] == "T-9"
    assert t["c3"]["responds_to"] == [] and t["c3"]["basis"] == "none"  # self reply: thread, not response
    assert t["c4"]["responds_to"] == ["c3"] and t["c4"]["addressees"] == ["member_1"]
    assert t["c2"]["thread_id"] == "c2" and t["c5"]["thread_id"] == "c5" and t["c5"]["basis"] == "none"
    svc.conversation_close("conv:pt")


# ---- order / duplicates -------------------------------------------------------
def test_out_of_order_and_duplicate_are_atomic(svc):
    cid = "conv:order"
    svc.conversation_turns(cid, "meeting", [{"id": "o1", "actor_ref": "m_a", "text": "hi", "ts_ms": 100}])
    bad_ts = [{"id": "o2", "actor_ref": "m_b", "text": "x", "ts_ms": 150},
              {"id": "o3", "actor_ref": "m_b", "text": "y", "ts_ms": 120}]
    assert _err(svc.conversation_turns, cid, "meeting", bad_ts) == (409, "out_of_order")
    assert _err(svc.conversation_turns, cid, "meeting",
                [{"id": "o2", "actor_ref": "m_b", "text": "x", "ts_ms": 99}]) == (409, "out_of_order")
    assert _err(svc.conversation_turns, cid, "meeting",
                [{"id": "o1", "actor_ref": "m_b", "text": "x", "ts_ms": 200}]) == (409, "duplicate_turn")
    assert _err(svc.conversation_turns, cid, "meeting",
                [{"id": "o9", "actor_ref": "m_b", "text": "x"}, {"id": "o9", "actor_ref": "m_b", "text": "y"}]
                ) == (409, "duplicate_turn")
    assert svc.conversation_get(cid)["seq"] == 1  # nothing was ingested by a rejected batch
    ok = svc.conversation_turns(cid, "meeting", [{"id": "o2", "actor_ref": "m_b", "text": "x", "ts_ms": 100},
                                                 {"id": "o3", "actor_ref": "m_b", "text": "y"}])
    assert ok["seq"] == 2 and [t["id"] for t in ok["turns"]] == ["o2", "o3"]  # ts tie keeps array order
    svc.conversation_close(cid)


# ---- eviction -----------------------------------------------------------------
def test_idle_ttl_eviction(srv):
    clk = Clock()
    s = srv.ClassifierService(idle_ttl_s=10, max_conversations=8, clock=clk)
    s.conversation_turns("conv:ttl", "thread", _thread(THREAD[:2]))
    clk.t += 9
    assert s.conversation_get("conv:ttl")["seq"] == 1
    s.conversation_turns("conv:ttl", "thread", _thread(THREAD[2:3]))  # touch at t+9
    clk.t += 10
    assert s.conversation_get("conv:ttl")["seq"] == 2                 # GET does not touch...
    clk.t += 1
    assert _err(s.conversation_get, "conv:ttl") == (409, "conversation_evicted")  # ...idle > 10 s
    assert _err(s.conversation_turns, "conv:ttl", "thread", _thread(THREAD[3:4])) == (409, "conversation_evicted")
    assert _err(s.conversation_close, "conv:ttl") == (409, "conversation_evicted")
    assert s.conversations_evicted == {"idle_ttl": 1, "lru": 0} and not s.sessions
    assert s.info()["conversations"]["evicted"] == {"idle_ttl": 1, "lru": 0}


def test_lru_cap_eviction(srv):
    clk = Clock()
    s = srv.ClassifierService(idle_ttl_s=900, max_conversations=3, clock=clk)
    for i in range(3):
        clk.t += 1
        s.conversation_turns(f"conv:l{i}", "thread", _thread(THREAD[:1]))
    clk.t += 1
    s.conversation_turns("conv:l0", "thread", _thread(THREAD[1:2]))   # l0 most recent; l1 is LRU
    s.conversation_turns("conv:l3", "thread", _thread(THREAD[:1]))
    assert list(s.sessions) == ["conv:l2", "conv:l0", "conv:l3"]
    assert _err(s.conversation_get, "conv:l1") == (409, "conversation_evicted")
    assert s.conversations_evicted == {"idle_ttl": 0, "lru": 1}
    assert tuple(s.snap.source_revision) == s.rev0


# ---- incremental == one-shot ----------------------------------------------------
def _run_batches(srv_mod, svc, cid, kind, turns, size):
    rows, deltas = [], []
    for i in range(0, len(turns), size):
        out = svc.conversation_turns(cid, kind, turns[i:i + size])
        rows += out["turns"]
        deltas.append((i + size, out))
    fin = svc.conversation_close(cid)
    return rows, deltas, fin


def _one_shot(svc, kind, turns):
    """Reference: open + ONE ingest + close on a fresh fork (adapter level)."""
    branch = svc.snap.fork()
    st = eq.conversation_open(branch, svc.root, "ref", kind)
    got = eq.conversation_ingest(branch, svc.root, st, turns)
    fin = eq.conversation_close(branch, svc.root, st)
    from services.equilibrium_classifier.server import conversation_to_wire
    return (conversation_to_wire({**got, "conversation_id": "ref"}, TAX)["turns"],
            conversation_to_wire({**fin, "conversation_id": "ref"}, TAX))


@pytest.mark.parametrize("name", ["thread", "climate", "meeting_declared", "synthetic_thread",
                                  "meeting_tracked", "tracked_non_adjacent", "tracked_counter",
                                  "synthetic_meeting"])
def test_incremental_batches_equal_one_shot(srv, svc, name):
    turns, kind = {
        "thread": (_thread(THREAD), "thread"),
        "climate": (_thread(CLIMATE), "thread"),
        "meeting_declared": (_meeting_declared(), "meeting"),
        "synthetic_thread": (synthetic_window(240, seed=77, kind="thread")[1], "thread"),
        # O2: tracked structure (no declared replies) -- causal, so batch-invariant
        "meeting_tracked": ([{"id": i, "actor_ref": a, "text": t} for i, a, t in MEETING], "meeting"),
        "tracked_non_adjacent": (_tracking_turns(TRK_WINDOWS["non_adjacent"]), "channel"),
        "tracked_counter": (_tracking_turns(TRK_WINDOWS["counter"]), "channel"),
        "synthetic_meeting": (synthetic_window(240, seed=78, kind="meeting")[1], "meeting"),
    }[name]
    ref_turns, ref_fin = _one_shot(svc, kind, turns)
    sizes = (1, 3, 100) if len(turns) < 50 else (7, 100)
    for size in sizes:
        rows, deltas, fin = _run_batches(srv, svc, f"conv:inc:{name}:{size}", kind, turns, size)
        assert rows == ref_turns, (name, size)
        assert fin["quanta"] == ref_fin["quanta"] and fin["episodes"] == ref_fin["episodes"], (name, size)
        assert fin["open_questions"] == ref_fin["open_questions"]
        if len(turns) < 50:
            # every emitted quantum / episode equals the one-shot read-out over that
            # prefix, and an unchanged row is never re-emitted
            emitted: dict = {}
            for upto, out in deltas:
                _, pre = _one_shot(svc, kind, turns[:upto])
                pq = {_key(q): q for q in pre["quanta"]}
                pe = {e["episode_id"]: e for e in pre["episodes"]}
                for q in out["quanta"]:
                    assert pq[_key(q)] == q and emitted.get(_key(q)) != q
                    emitted[_key(q)] = q
                for e in out["episodes"]:
                    assert pe[e["episode_id"]] == e
                assert all(emitted.get(k) == v for k, v in pq.items()), "a changed row was not re-emitted"
                assert out["open_questions"] == pre["open_questions"]


def test_discourse_is_open_turns_close(srv, svc):
    """/v1/discourse (> 100 turns => several internal batches) == the conversation path."""
    win, turns = synthetic_window(230, seed=5, kind="thread")
    d = svc.discourse(win, turns)
    _, ref = _one_shot(svc, "thread", turns)
    assert d["quanta"] == ref["quanta"] and d["episodes"] == ref["episodes"]
    assert [m["id"] for m in d["messages"]] == [t["id"] for t in turns]
    assert _err(svc.discourse, {"window_id": "w", "kind": "meeting"},
                [{"id": "a", "actor_ref": "x", "text": "", "ts_ms": 5},
                 {"id": "b", "actor_ref": "x", "text": "", "ts_ms": 4}]) == (409, "out_of_order")


# ---- scale: base unchanged, memory, latency -----------------------------------------
def _rss_kib() -> int:
    with open("/proc/self/status") as f:
        return next(int(x.split()[1]) for x in f if x.startswith("VmRSS:"))


def test_base_unchanged_10k_turns_100_conversations_memory_and_p95(srv):
    import gc
    s = srv.ClassifierService(max_conversations=100, strong_every=50)
    convs = [synthetic_window(100, seed=5000 + i, kind="thread" if i % 2 else "meeting") for i in range(100)]
    gc.collect()
    rss0 = _rss_kib()
    lat = []
    for i, (_, turns) in enumerate(convs):
        t0 = time.perf_counter()
        s.conversation_turns(f"conv:scale:{i}", "thread" if i % 2 else "meeting", turns)
        lat.append(time.perf_counter() - t0)
    gc.collect()
    rss1 = _rss_kib()
    assert len(s.sessions) == 100 and s.turns == 10_000
    assert tuple(s.snap.source_revision) == s.rev0
    assert s._strong_check() and s.last_strong["digest"] == s.digest0  # base byte-identical
    lat.sort()
    p95 = lat[int(0.95 * len(lat)) - 1]
    per_conv_kib = (rss1 - rss0) / 100
    for i in range(100):
        s.conversation_close(f"conv:scale:{i}")
    gc.collect()
    rss2 = _rss_kib()
    # closed forks are freed: a second wave of 100 retained conversations reuses
    # that memory (RSS stays flat) instead of growing again
    for i, (_, turns) in enumerate(convs):
        s.conversation_turns(f"conv:scale2:{i}", "thread" if i % 2 else "meeting", turns)
    gc.collect()
    rss3 = _rss_kib()
    for i in range(100):
        s.conversation_close(f"conv:scale2:{i}")
    print(f"\n[O1 scale] 100 retained conversations x 100 turns (one 100-turn batch each, concurrency 1): "
          f"p50 {statistics.median(lat) * 1e3:.0f} ms, p95 {p95 * 1e3:.0f} ms, max {lat[-1] * 1e3:.0f} ms; "
          f"RSS +{(rss1 - rss0) / 1024:.1f} MiB = {per_conv_kib:.0f} KiB/retained conversation "
          f"(upper bound: includes first-use caches); after closing all: +{(rss2 - rss0) / 1024:.1f} MiB "
          f"(allocator-retained); second wave of 100: +{(rss3 - rss2) / 1024:.1f} MiB")
    assert (rss3 - rss2) < 0.25 * (rss1 - rss0)
    assert tuple(s.snap.source_revision) == s.rev0 and s._strong_check()
    assert not s.sessions


def test_long_conversation_batch_latency(srv):
    """Per-batch cost grows with the conversation: the strata re-run over the
    whole prefix on a scratch fork (S0 / tokenisation stays incremental)."""
    s = srv.ClassifierService()
    _, turns = synthetic_window(1500, seed=4242, kind="thread")
    lat = []
    for i in range(0, len(turns), 100):
        t0 = time.perf_counter()
        s.conversation_turns("conv:long", "thread", turns[i:i + 100])
        lat.append(time.perf_counter() - t0)
    t0 = time.perf_counter()
    s.conversation_close("conv:long")
    close = time.perf_counter() - t0
    print(f"\n[O1 long] 1500-turn thread in 15 x 100-turn batches: first {lat[0] * 1e3:.0f} ms, "
          f"last {lat[-1] * 1e3:.0f} ms, p95 {sorted(lat)[13] * 1e3:.0f} ms, close {close * 1e3:.0f} ms")
    assert tuple(s.snap.source_revision) == s.rev0


# ---- HTTP contract ---------------------------------------------------------------
@pytest.fixture(scope="module")
def server(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("eqconv")
    port = _free_port()
    proc, _ = _start(tmp, port)
    yield port
    _stop(proc)


def test_http_contract_and_errors(server):
    turns = _thread(THREAD)
    st, doc, _ = _req(server, "POST", "/v1/conversations/c.h-1:x~y/turns",
                      {"taxonomy_version": TAX, "kind": "thread", "turns": turns[:4]})
    assert st == 200, doc
    client_parse_conversation(doc, "c.h-1:x~y", {t["id"] for t in turns[:4]}, turns[:4])
    st, doc, _ = _req(server, "POST", "/v1/conversations/c.h-1:x~y/turns", {"kind": "thread", "turns": turns[4:]})
    assert st == 200 and doc["seq"] == 2
    client_parse_conversation(doc, "c.h-1:x~y", {t["id"] for t in turns}, turns[4:])
    st, g, _ = _req(server, "GET", "/v1/conversations/c.h-1:x~y")
    assert st == 200 and g == {"ok": True, "conversation_id": "c.h-1:x~y", "seq": 2, "idle_ttl_s": 900,
                               "kind": "thread"}
    st, info, _ = _req(server, "GET", "/v1/info")
    assert info["conversations"]["open"] == 1 and info["conversations"]["concurrency"] == "per_conversation_locks"
    st, fin, _ = _req(server, "POST", "/v1/conversations/c.h-1:x~y/close")
    assert st == 200 and fin["turns"] == [] and fin["quanta"]
    client_parse_conversation(fin, "c.h-1:x~y", {t["id"] for t in turns}, [])

    def code(st_doc):
        return st_doc[0], st_doc[1]["error"]["code"], st_doc[1]["error"]["retryable"]
    sec = {"id": SECRET, "actor_ref": SECRET, "text": SECRET}
    assert code(_req(server, "GET", "/v1/conversations/c.h-1:x~y")) == (404, "unknown_conversation", False)
    assert code(_req(server, "POST", "/v1/conversations/nope/close")) == (404, "unknown_conversation", False)
    _req(server, "POST", "/v1/conversations/c2/turns", {"kind": "meeting", "turns": [sec]})
    cases = {
        "dup": ("/v1/conversations/c2/turns", {"kind": "meeting", "turns": [sec]}, 409, "duplicate_turn"),
        "order": ("/v1/conversations/c3/turns", {"kind": "meeting", "turns": [
            {**sec, "id": "a1", "ts_ms": 9}, {**sec, "id": "a2", "ts_ms": 8}]}, 409, "out_of_order"),
        "too_many": ("/v1/conversations/c4/turns",
                     {"kind": "thread", "turns": [{**sec, "id": f"i{i}"} for i in range(101)]}, 413, "too_large"),
        "kind": ("/v1/conversations/c5/turns", {"kind": SECRET, "turns": []}, 400, "bad_request"),
        "extra": ("/v1/conversations/c5/turns", {"kind": "thread", "turns": [], SECRET: 1}, 400, "bad_request"),
        "turn_extra": ("/v1/conversations/c5/turns", {"kind": "thread", "turns": [{**sec, "x": 1}]},
                       400, "bad_request"),
        "bad_id": (f"/v1/conversations/{SECRET}%20x/turns", {"kind": "thread", "turns": []}, 400, "bad_request"),
        "long_id": ("/v1/conversations/" + "a" * 201 + "/turns", {"kind": "thread", "turns": []}, 400, "bad_request"),
        "tax": ("/v1/conversations/c5/turns", {"taxonomy_version": "eq-tax-0.4.0", "kind": "thread", "turns": []},
                409, "taxonomy_mismatch"),
    }
    for name, (path, body, want_st, want_code) in cases.items():
        st, doc, raw = _req(server, "POST", path, body)
        assert (st, doc["error"]["code"]) == (want_st, want_code), name
        assert doc["ok"] is False and set(doc["error"]) == {"code", "message", "retryable"}
        assert SECRET.encode() not in raw, name
    st, h, _ = _req(server, "GET", "/healthz")
    assert st == 200 and h == {"ok": True}
