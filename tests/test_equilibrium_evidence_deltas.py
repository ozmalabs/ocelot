"""Equilibrium conversation EVIDENCE DELTAS (track T3e, pack 0.6.0; contract unchanged in eq-tax-0.7.0).

/turns, /close and every /_batch item carry `quanta_delta` / `episodes_delta`
instead of whole rows; folding them in seq order (tests/equilibrium_delta_fold.py,
the reference client) gives exactly the full read-out at every prefix. Covers
retraction and re-appearance, evidence / counter removal, field-only changes,
the engine's exact-edge-delta primitive, and the HTTP / batch shape.
Synthetic pseudonymous data only."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
os.environ.setdefault("OZMA_NO_LLM", "1")

from equilibrium_delta_fold import DeltaFold, FoldError  # noqa: E402
from test_equilibrium_classifier_service import _free_port, _req, _start, _stop  # noqa: E402
from test_equilibrium_discourse_service import synthetic_window  # noqa: E402

TAX = "eq-tax-0.7.0"


def T(i, a, text, r=None):
    return {"id": i, "actor_ref": a, "text": text, **({"reply_to": r} if r else {})}


# the floor holder keeps the floor while the runner-up changes, then loses it (tie),
# then regains it: counter removal, retraction and re-appearance of ONE quantum
FLOOR = [
    [T("f1", "ana", "The deploy is at noon."), T("f2", "ana", "The cache is cold."),
     T("f3", "bea", "Lunch is at noon."), T("f4", "ana", "The build is green.")],
    [T("f5", "cy", "The runner is slow."), T("f6", "cy", "The disk is full."),
     T("f7", "ana", "The log is long."), T("f8", "ana", "The queue is empty.")],
    [T("f9", "bea", "Nice."), T("f10", "bea", "Good."), T("f11", "bea", "Fine."), T("f12", "bea", "Done.")],
    [T("f13", "ana", "The release is tomorrow."), T("f14", "ana", "The notes are ready.")],
]


@pytest.fixture(scope="module")
def srv():
    from services.equilibrium_classifier import server
    return server


@pytest.fixture(scope="module")
def svc(srv):
    return srv.ClassifierService(workers=2, max_conversations=50)


def _full_wire(srv, svc, cid):
    from domains import equilibrium_classify as ec
    sess = svc.sessions[cid]
    full = ec.conversation_full(sess.branch, svc.root, sess.state)
    return srv.quanta_to_wire(full["quanta"]), srv.episodes_to_wire(full["episodes"])


def _floor(f, actor):
    return [d for d in f if d.get("trait") == "interaction.floor" and d.get("actor_ref") == actor]


def test_retraction_counter_removal_and_reappearance(srv, svc):
    f = DeltaFold()
    outs = []
    for b in FLOOR:
        f.turns(b)
        out = svc.conversation_turns("dl:floor", "channel", b)
        f.apply(out)
        q, e = _full_wire(srv, svc, "dl:floor")
        assert f.quanta() == q and f.episodes() == e
        outs.append(out["quanta_delta"])
    first = _floor(outs[0], "ana")
    assert len(first) == 1
    qid = first[0]["quantum_id"]
    # 0.7.0: bounded anchors -- the holder's first turn / the runner-up's first turn
    assert first[0]["evidence_add"] == ["f1"] and first[0]["counter_add"] == ["f3"]
    assert first[0]["target_ref"] is None and first[0]["match"] == "partial"
    assert first[0]["rule_ids"] == [f"eq.quanta.{r}:0.7.0" for r in (
        "interaction.floor", "interaction.floor.counter", "interaction.floor.evidence",
        "match.partial_by_construction")]
    # batch 2: same quantum, runner-up bea -> cy: one counter ref out, one in (0.6.0: the
    # runner-up's every turn out, the new runner-up's every turn in)
    d2 = [d for d in outs[1] if d["quantum_id"] == qid]
    assert d2 == [{"quantum_id": qid, "op": "upsert", "evidence_add": [], "evidence_remove": [],
                   "counter_add": ["f5"], "counter_remove": ["f3"]}]
    # batch 3: bea ties ana -> the floor quantum no longer holds
    assert {"quantum_id": qid, "op": "retract"} in outs[2]
    # batch 4: it holds again -> a fresh upsert carrying the full (bounded) current lists
    d4 = [d for d in outs[3] if d["quantum_id"] == qid]
    assert len(d4) == 1 and d4[0]["trait"] == "interaction.floor" and d4[0]["evidence_remove"] == []
    assert d4[0]["evidence_add"] == ["f1"] and d4[0]["counter_add"] == ["f3"]
    # the turn shares are the per-actor interaction.floor_share quanta: monotone, never retracted
    share = [d for o in outs for d in o if d.get("trait") == "interaction.floor_share" and d["actor_ref"] == "ana"]
    sid = share[0]["quantum_id"]
    rows = [d for o in outs for d in o if d["quantum_id"] == sid]
    assert [d["evidence_add"] for d in rows] == [["f1", "f2", "f4"], ["f7", "f8"], ["f13", "f14"]]
    assert all(d["op"] == "upsert" and not d["evidence_remove"] and not d["counter_add"] for d in rows)
    fin = svc.conversation_close("dl:floor")
    assert fin["quanta_delta"] == [] and fin["episodes_delta"] == [] and fin["turns"] == []


def test_every_delta_kind_folds_exactly_at_every_prefix(srv, svc):
    """Synthetic windows, small batches: retractions, evidence and counter removal,
    match / rule-id changes and episode field changes all occur, and the fold
    equals the full read after every batch."""
    seen = {"retract": 0, "reappear": 0, "evidence_remove": 0, "counter_remove": 0, "match": 0,
            "episode_field": 0, "episode_turns_add": 0}
    for seed, kind in ((91, "channel"), (92, "thread"), (78, "meeting")):
        cid = f"dl:kinds:{seed}"
        turns = synthetic_window(240, seed=seed, kind=kind)[1]
        f, retracted = DeltaFold(), set()
        f.turns(turns)
        for i in range(0, len(turns), 7):
            out = svc.conversation_turns(cid, kind, turns[i:i + 7])
            for d in out["quanta_delta"]:
                if d["op"] == "retract":
                    seen["retract"] += 1
                    retracted.add(d["quantum_id"])
                    continue
                if d["quantum_id"] in retracted and d["quantum_id"] not in f.q:
                    seen["reappear"] += 1
                    assert "actor_ref" in d and not d["evidence_remove"] and not d["counter_remove"]
                seen["evidence_remove"] += bool(d["evidence_remove"])
                seen["counter_remove"] += bool(d["counter_remove"])
                seen["match"] += d["quantum_id"] in f.q and "match" in d
            for d in out["episodes_delta"]:
                if d["op"] == "upsert" and d["episode_id"] in f.e:
                    seen["episode_field"] += any(k in d for k in ("facets", "generative", "actor_refs", "rule_ids"))
                    seen["episode_turns_add"] += bool(d["turns_add"])
            f.apply(out)
            q, e = _full_wire(srv, svc, cid)
            assert f.quanta() == q and f.episodes() == e, (seed, i)
        svc.conversation_close(cid)
    assert all(v > 0 for v in seen.values()), seen


def test_quantum_ids_are_stable_across_batch_sizes(srv, svc):
    turns = synthetic_window(120, seed=93, kind="thread")[1]
    ids = []
    for size in (5, 120):
        f = DeltaFold()
        f.turns(turns)
        for i in range(0, len(turns), size):
            f.apply(svc.conversation_turns(f"dl:ids:{size}", "thread", turns[i:i + size]))
        svc.conversation_close(f"dl:ids:{size}")
        ids.append({qid: f.quantum_key(qid) for qid in f.q})
        assert len(set(ids[-1].values())) == len(ids[-1])  # one id per quantum key
    assert ids[0] == ids[1]


def test_reference_fold_rejects_contract_violations():
    f = DeltaFold()
    f.turns([{"id": "a"}, {"id": "b"}])
    with pytest.raises(FoldError):  # first upsert must carry the key fields
        f.apply({"quanta_delta": [{"quantum_id": "q:1", "op": "upsert", "evidence_add": ["a"],
                                   "evidence_remove": [], "counter_add": [], "counter_remove": []}],
                 "episodes_delta": []})
    with pytest.raises(FoldError):  # retract of an unknown quantum
        f.apply({"quanta_delta": [{"quantum_id": "q:2", "op": "retract"}], "episodes_delta": []})


def test_engine_exact_edge_delta_equals_graph_diff_oracle(monkeypatch):
    """run_rules_edge_delta reports exactly the NET edge existence changes of the
    requested types (checked against an O(V+E) before/after graph diff around every
    tick of a conversation that adds, retracts and re-adds), and the touched nodes
    of the requested types."""
    from domains import equilibrium_classify as ec
    base, root = ec.boot()
    b = base.snapshot().fork()
    st = ec.conversation_open(b, root, "c", "channel")
    n = ec._native(b)
    types = set(ec.DELTA_EDGE_TYPES)
    tick, checked = ec._tick, []

    def edges():
        return {(e["src"], e["type"], e["tgt"]) for e in n.graph_to_dict()["edges"] if e["type"] in types}

    def oracle_tick(nn, touched):
        before = edges()
        mine = ec.Changes()
        steps = tick(nn, mine)
        after = edges()
        assert {k: now for k, (_, now) in mine.edges.items()} == (
            {k: True for k in after - before} | {k: False for k in before - after})
        assert set(mine.nodes) <= set(ec.DELTA_NODE_TYPES)
        for k, v in mine.edges.items():
            touched.edges.setdefault(k, list(v))[1] = v[1]
        for typ, ids in mine.nodes.items():
            touched.nodes.setdefault(typ, set()).update(ids)
        checked.append(len(mine.edges))
        return steps
    monkeypatch.setattr(ec, "_tick", oracle_tick)
    for batch in FLOOR:
        ec.conversation_ingest(b, root, st, batch)
    assert len(checked) >= 4 * len(FLOOR) and sum(checked) > 0


def test_http_turns_close_and_batch_shape(srv, tmp_path):
    tmp = tmp_path
    port = _free_port()
    proc, _ = _start(tmp, port)
    try:
        f = DeltaFold()
        f.turns(FLOOR[0] + FLOOR[1])
        st, doc, _ = _req(port, "POST", "/v1/conversations/h:1/turns",
                          {"taxonomy_version": TAX, "kind": "channel", "turns": FLOOR[0]})
        assert st == 200 and doc["taxonomy_version"] == TAX
        assert "quanta" not in doc and "episodes" not in doc and doc["quanta_delta"]
        f.apply(doc)
        st, out, _ = _req(port, "POST", "/v1/conversations/_batch",
                          {"taxonomy_version": TAX, "items": [{"conversation_id": "h:1", "kind": "channel",
                                                               "turns": FLOOR[1]}]})
        assert st == 200 and out["results"][0]["ok"] is True
        item = out["results"][0]
        assert set(item) == {"conversation_id", "ok", "seq", "turns", "quanta_delta", "episodes_delta",
                             "open_questions"}
        f.apply(item)
        assert all(r.endswith(":0.7.0") for d in item["quanta_delta"] for r in d.get("rule_ids", ()))
        st, fin, _ = _req(port, "POST", "/v1/conversations/h:1/close")
        assert st == 200 and fin["quanta_delta"] == [] and fin["episodes_delta"] == []
        # /v1/discourse keeps the full rows
        st, disc, _ = _req(port, "POST", "/v1/discourse",
                           {"taxonomy_version": TAX, "window": {"window_id": "h:1", "kind": "channel"},
                            "turns": FLOOR[0] + FLOOR[1]})
        assert st == 200 and "quanta_delta" not in disc
        assert json.loads(json.dumps(disc["quanta"])) == f.quanta()
        assert disc["episodes"] == f.episodes()
    finally:
        _stop(proc)
