"""Equilibrium conversation scaling (track T3d, pack 0.5.1; 0.6.0 evidence deltas): the shared batch
contract POST /v1/conversations/_batch, per-conversation concurrency, and the
live (monotone) strata layer, and (stage B) the live non-monotone families.
Synthetic pseudonymous data only."""
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
from equilibrium_delta_fold import DeltaFold  # noqa: E402

TAX = "eq-tax-0.7.0"


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
    for name in ("set_fresh_node_exempt", "set_batch_incremental", "set_own_write_exempt",
                 "set_precise_rule_deletes", "set_seeded_join_order", "set_write_frontier",
                 "set_hop_frontier", "set_delete_frontier"):
        getattr(n, name)(False)
        getattr(n, name)(False)
    st = ec.conversation_open(b, root, "c", "thread")  # turns the flags on for this fork
    out = ec.conversation_ingest(b, root, st, _conv(1203, n=5))
    assert out["seq"] == 1 and len(out["turns"]) == 5


@pytest.mark.parametrize("kind,seed", [("thread", 1211), ("meeting", 1212)])
def test_delta_readout_equals_full_readout(srv, kind, seed):
    """0.6.0 evidence deltas: folding the per-batch deltas (only what this batch's
    ticks changed, from the engine's exact-edge-delta report and the ledger marks)
    gives exactly the full re-read after every batch, and the graph-resident
    open-question set (`w -eq_qud-> q`) equals the pre-stage-A turn scan."""
    from domains import equilibrium_classify as ec
    turns = _conv(seed, n=160, kind=kind)
    on = srv.ClassifierService(workers=1)

    def scan_open(n, w):  # the pre-stage-A definition
        qs = [x for x in n.neighbours(w, "eq_has_turn")
              if n.node(x)["attrs"].get(ec.QUESTION_KEY) is True
              and not n.in_neighbours(x, "eq_answers")]
        return ec._refs(n, qs)
    f = DeltaFold()
    f.turns(turns)
    opened = False
    for i in range(0, len(turns), 40):
        out = on.conversation_turns("d", kind, turns[i:i + 40])
        f.apply(out)
        sess = on.sessions["d"]
        full = ec.conversation_full(sess.branch, on.root, sess.state)
        assert f.quanta() == srv.quanta_to_wire(full["quanta"]), i
        assert f.episodes() == srv.episodes_to_wire(full["episodes"]), i
        assert out["open_questions"] == scan_open(ec._native(sess.branch), sess.state.w)
        opened |= bool(out["open_questions"])
    fin = on.conversation_close("d")
    assert fin["quanta_delta"] == [] and fin["episodes_delta"] == []
    assert opened  # the set is exercised


def _s0_candidates(ec, b, root, st, batch, monkeypatch):
    """load-independent matcher work (scale-audit `cand_tested`, every path) of the
    batch's S0 tick on the retained fork -- the msg / cue / window layer"""
    n = ec._native(b)
    S = type(n)
    tick, calls, out = ec._tick, [], {}

    def audited(nn, touched):
        calls.append(1)
        if len(calls) != 1:
            return tick(nn, touched)
        S.scale_audit_reset()
        S.scale_audit_set_enabled(True)
        try:
            return tick(nn, touched)
        finally:
            S.scale_audit_set_enabled(False)
            out.update(S.scale_audit_snapshot())
    monkeypatch.setattr(ec, "_tick", audited)
    try:
        ec.conversation_ingest(b, root, st, batch)
    finally:
        monkeypatch.setattr(ec, "_tick", tick)
    return out["cand_tested"]


def test_s0_msg_rules_do_not_rescan_the_prefix(monkeypatch):
    """Stage A regression: a progressing DelEdge rule (eq.trk.cursor) used to clear
    EVERY rule cursor, msg rules cleared their own on every firing, and an external
    `eq_has_token` edge cleared every rule reading it in a term, so each batch
    re-matched the S0 msg rules over the whole conversation. The S0 matcher work of
    a 50-turn batch must not grow with the prefix (before: ~linear)."""
    from domains import equilibrium_classify as ec
    turns = _conv(1221, n=700)
    base, root = ec.boot()
    b = base.snapshot().fork()
    st = ec.conversation_open(b, root, "s0", "thread")
    work = {}
    for i in range(0, 650, 50):
        if i in (100, 600):
            work[i] = _s0_candidates(ec, b, root, st, turns[i:i + 50], monkeypatch)
        else:
            ec.conversation_ingest(b, root, st, turns[i:i + 50])
    assert work[100] > 0
    assert work[600] < 2.0 * work[100], work  # 6x the prefix, not 6x the work


# ---- stage B: the non-monotone families run live (no scratch fork) -----------------
NM_RULE_KEYS = ("eq.trk.nturns", "eq.trk.unans.", "eq.trk.rsp.", "interaction.floor", "responsiveness",
                "eq.quanta.nm.", "inquiry.unanswered", "competence.grounded", "claim_grounding",
                "eq.ep.gen.", "generative", "facet_match", "eq.quanta.match.", "eq.quanta.compose")
NM_TRAITS = ("interaction.floor", "interaction.responsiveness", "inquiry.unanswered",
             "competence.claim_grounding")


def _full(ec, b, root, st):
    """the complete read-out (a read; the fork stays usable)"""
    got = ec.conversation_full(b, root, st)
    return {"quanta": got["quanta"], "episodes": got["episodes"], "open": got["open_questions"]}


@pytest.mark.parametrize("kind,seed,size", [("thread", 1231, 7), ("meeting", 1232, 5), ("channel", 1233, 11)])
def test_nonmonotone_families_equal_one_shot_at_every_prefix(kind, seed, size):
    """The scratch fork's contract, now kept by rolling state + retraction edges:
    after every batch the conversation's complete read-out equals a fresh one-shot
    run over the same prefix -- including facts a later turn retracted (a floor
    holder overtaken, a question answered after it was counted unanswered / not
    responded to, a claim grounded later, a resolution escalated again)."""
    from domains import equilibrium_classify as ec
    turns = _conv(seed, n=150, kind=kind)
    base, root = ec.boot()
    snap = base.snapshot()
    b = snap.fork()
    st = ec.conversation_open(b, root, "p", kind)
    seen, checked = {}, 0
    for i in range(0, len(turns), size):
        ec.conversation_ingest(b, root, st, turns[i:i + size])
        if (i // size) % 3 and i + size < len(turns):
            continue
        k = min(i + size, len(turns))
        inc = _full(ec, b, root, st)
        one = ec.discourse(snap.fork(), root, {"window_id": "p", "kind": kind}, turns[:k])
        assert inc["quanta"] == one["quanta"], k
        assert inc["episodes"] == one["episodes"], k
        assert inc["open"] == one["open_questions"], k
        for q in inc["quanta"]:
            if q["trait"] in NM_TRAITS:
                seen.setdefault((q["actor_ref"], q["trait"], q["polarity"], q.get("target_ref")), []).append(k)
        checked += 1
    assert checked >= 5
    traits = {key[1] for key in seen}
    assert {"interaction.floor", "inquiry.unanswered"} <= traits, traits
    # some non-monotone quantum existed at one checkpoint and not at a later one
    last = max(v[-1] for v in seen.values())
    assert any(v[-1] < last for v in seen.values()), "no retraction exercised"


def test_stage_b_flags_equal_without(srv, monkeypatch):
    """hop_frontier / delete_frontier are evaluation strategy only: the same
    conversation reads out identically with both off."""
    from domains import equilibrium_classify as ec
    turns = _conv(1241, n=160, kind="meeting")
    on = srv.ClassifierService(workers=1)
    got_on = _sequential(on, "h", "meeting", turns, 20) + [on.conversation_close("h")]
    full = ec.incremental_engine

    def without(n):
        full(n)
        n.set_hop_frontier(False)
        n.set_delete_frontier(False)
    monkeypatch.setattr(ec, "incremental_engine", without)
    off = srv.ClassifierService(workers=1)
    got_off = _sequential(off, "h", "meeting", turns, 20) + [off.conversation_close("h")]
    assert got_on == got_off


def _nm_candidates(ec, b, root, st, batch):
    """load-independent matcher work (scale-audit candidate tests by rule) of the
    stage-B non-monotone rules over one whole batch (every tick)"""
    S = type(ec._native(b))
    S.scale_audit_reset()
    S.scale_audit_per_rule_reset()
    S.scale_audit_set_enabled(True)
    S.scale_audit_set_per_rule_enabled(True)
    try:
        ec.conversation_ingest(b, root, st, batch)
    finally:
        S.scale_audit_set_enabled(False)
        S.scale_audit_set_per_rule_enabled(False)
    names = {r[0]: r[2] for r in S.scale_audit_rule_metadata_snapshot()}
    return sum(c for i, _pos, c in S.scale_audit_match_clause_snapshot()
               if any(k in names.get(i, "") for k in NM_RULE_KEYS))


def test_nonmonotone_families_do_not_rescan_the_prefix():
    """Stage B regression: the six non-monotone families used to be re-derived over
    the whole conversation on a scratch fork every batch. Their matcher work for a
    50-turn batch must not grow with the prefix (6x the prefix, < 1.5x the work;
    measured ~1.0x; with hop_frontier / delete_frontier off it is ~1.7x)."""
    from domains import equilibrium_classify as ec
    turns = _conv(1251, n=700, kind="meeting")
    base, root = ec.boot()
    b = base.snapshot().fork()
    st = ec.conversation_open(b, root, "nm", "meeting")
    work = {}
    for i in range(0, 650, 50):
        if i in (100, 600):
            work[i] = _nm_candidates(ec, b, root, st, turns[i:i + 50])
        else:
            ec.conversation_ingest(b, root, st, turns[i:i + 50])
    assert work[100] > 0
    assert work[600] < 1.5 * work[100], work


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


# ---- 0.7.0 (T3f): corroboration / contest with bounded claim state -----------------
_CLAIMY = [("ana", "As a nurse I see this every week."), ("bea", "Ana, good point."),
           ("ana", "I'm a doctor and the cache is cold."), ("cy", "But ana, see https://example.org/x"),
           ("dov", "Ana, fair point."), ("bea", "The build is green."), ("ana", "As an engineer I built it."),
           ("cy", "Ana, you're right."), ("dov", "But ana, the latency doc says otherwise https://example.org/y"),
           ("bea", "Lunch at noon.")]


def _claimy(n):
    return [{"id": f"c{i:05d}", "actor_ref": _CLAIMY[i % 10][0], "text": _CLAIMY[i % 10][1],
             **({"reply_to": f"c{i - 1:05d}"} if _CLAIMY[i % 10][1].startswith(("Ana", "But")) else {})}
            for i in range(n)]


def _competence_oracle(f, wire_turns):
    """Test-side oracle of the (unchanged) relation, from wire fields only: claims are
    the claimant's competence.claimed evidence; a corroborating reply carries a
    concession / deference label and addresses the claimant; a contest carries a
    reply-leading contrast and grounding and addresses the claimant."""
    pos = {t["id"]: i for i, t in enumerate(wire_turns)}
    claims = {}
    for q in f.quanta():
        if q["trait"] == "competence.claimed" and q["polarity"] == "+":
            claims[q["actor_ref"]] = [pos[m] for m in q["evidence"]]
    want = {}
    for t in wire_turns:
        lab = t["labels"]
        corr = bool(lab.get("concession")) or any("msg.deference" in r for r in lab["rule_ids"])
        cont = any("reply_contrast" in r for r in lab["rule_ids"]) and (
            bool(lab.get("substantive_markers")) or "technical" in lab.get("domains", []))
        for a in t["addressees"]:
            cl = [c for c in claims.get(a, []) if c < pos[t["id"]]]
            for kind, on, tgt in (("competence.corroborated", corr, None), ("competence.contested", cont, t["_author"])):
                if on and cl:
                    e = want.setdefault((a, kind, tgt), set())
                    e.update(cl)
                    e.add(pos[t["id"]])
    return {k: sorted(v) for k, v in want.items()}


def test_competence_pairing_equals_relation_and_work_is_bounded(svc):
    """0.7.0: replies are no longer paired with every earlier claim; the per-actor /
    per-(actor, replier) claim state gives the same evidence (oracle from the wire at
    every prefix) and the matcher work per batch does not grow with the prefix."""
    from domains import equilibrium_classify as ec
    turns = _claimy(420)
    f, seen = DeltaFold(), []
    for i in range(0, len(turns), 60):
        out = svc.conversation_turns("cmp:orc", "thread", turns[i:i + 60])
        f.turns(turns[i:i + 60])
        f.apply(out)
        for t, src in zip(out["turns"], turns[i:i + 60]):
            seen.append({**t, "_author": src["actor_ref"]})
        pos = {t["id"]: k for k, t in enumerate(seen)}
        got = {(q["actor_ref"], q["trait"], q.get("target_ref")): sorted(pos[m] for m in q["evidence"])
               for q in f.quanta() if q["trait"] in ("competence.corroborated", "competence.contested")}
        assert got == _competence_oracle(f, seen)
    assert len(got) == 3 and max(len(v) for v in got.values()) > 100
    keys = ("eq.competence.",)
    base, root = ec.boot()
    b = base.snapshot().fork()
    st = ec.conversation_open(b, root, "cmp:w", "thread")
    T = _claimy(1250)
    S = type(ec._native(b))
    work = {}
    for i in range(0, 1250, 50):
        if i not in (100, 1200):
            ec.conversation_ingest(b, root, st, T[i:i + 50])
            continue
        S.scale_audit_reset(); S.scale_audit_per_rule_reset()
        S.scale_audit_set_enabled(True); S.scale_audit_set_per_rule_enabled(True)
        try:
            ec.conversation_ingest(b, root, st, T[i:i + 50])
        finally:
            S.scale_audit_set_enabled(False); S.scale_audit_set_per_rule_enabled(False)
        names = {r[0]: r[2] for r in S.scale_audit_rule_metadata_snapshot()}
        work[i] = sum(c for k, _p, c in S.scale_audit_match_clause_snapshot()
                      if any(x in names.get(k, "") for x in keys) and "claim_grounding" not in names.get(k, ""))
    assert work[100] > 0 and work[1200] < 1.2 * work[100], work  # measured 1334 / 1334 (12x the prefix)
