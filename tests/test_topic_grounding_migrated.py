"""Phrase-level topic grounding (domains/topic_grounding.py) + the autonomous
SearchRequest search path (domains/fetch_dispatch.scan_and_search).

`answer_about(X)` answers only topics the agent HOLDS; the per-word self-heal
(`ground_unknowns`) grounds only single words, so "three body problem" grounded
just "problem". `ground_topic(agent, phrase)` grounds the WHOLE phrase — local
Wikipedia library first, then a live Wikipedia REST lookup over HTTPS — and
persists it via `learn_from_teacher`, so `answer_about(phrase)` returns it
thereafter. Mechanical I/O only (the source decides the meaning).

The web fallback + `scan_and_search` are tested with a MONKEYPATCHED http_get —
no real network is touched.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

from domains import topic_grounding as tg
from domains.fetch_dispatch import (mint_search_request, scan_and_search,
                                    scan_and_sync_ground)


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def test_missing_wikipedia_snapshot_does_not_import_pyarrow_stack(
        agent, monkeypatch, tmp_path):
    import builtins
    from domains import libraries

    monkeypatch.setattr(libraries, "WIKI_DATA", tmp_path / "no-wikipedia-data")
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name in {"domains.wiki_teacher", "domains.wiki_library"}:
            raise AssertionError(f"unavailable wiki stack imported: {name}")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    assert tg._ground_local(agent, "unavailable local topic") is None


# ---------------------------------------------------------------------------
# canned Wikipedia responses (opensearch + REST summary) — no real network
# ---------------------------------------------------------------------------

def _canned_http_get(title_by_query: dict, extract_by_title: dict):
    """Build an http_get(url, timeout=...) that answers the opensearch and REST
    summary endpoints from the given maps. Raises on any other URL so a stray
    real request can't slip through."""
    from urllib.parse import unquote

    def _get(url, timeout=8):
        if "action=opensearch" in url:
            q = url.split("search=", 1)[1]
            q = unquote(q).lower()
            title = title_by_query.get(q)
            titles = [title] if title else []
            body = json.dumps([q, titles, [""], [""]])
            return {"status": 200, "length": len(body), "text": body, "url": url}
        if "/page/summary/" in url:
            raw = url.split("/page/summary/", 1)[1]
            title = unquote(raw).replace("_", " ")
            extract = extract_by_title.get(title)
            if extract is None:
                body = json.dumps({"type": "not_found"})
                return {"status": 404, "length": len(body), "text": body, "url": url}
            body = json.dumps({"title": title, "extract": extract})
            return {"status": 200, "length": len(body), "text": body, "url": url}
        raise AssertionError(f"unexpected URL in test: {url!r}")

    return _get


# ---------------------------------------------------------------------------
# local wiki (skips gracefully if the WIKI_DATA index is empty)
# ---------------------------------------------------------------------------

def test_ground_topic_local_wiki(agent):
    from domains.libraries import WIKI_DATA
    from domains.wiki_library import WikipediaLibrary

    try:
        lib = WikipediaLibrary(data_dir=WIKI_DATA)
        size = lib.index_size()
    except Exception:
        size = 0
    if not size:
        pytest.skip("local Wikipedia index empty/unavailable")

    # A random real article title is guaranteed present in the library.
    article = lib.random_article()
    if article is None or not (article.abstract or article.description):
        pytest.skip("no usable article in the local index")
    phrase = article.title

    # No web allowed -> this MUST come from the local library.
    ans = tg.ground_topic(agent, phrase, allow_web=False)
    assert ans, "the local library must ground a real article title"
    assert agent.answer_about(phrase) is not None, (
        "after ground_topic, answer_about(phrase) must return the grounding")


# ---------------------------------------------------------------------------
# web fallback (monkeypatched http_get; local forced to miss)
# ---------------------------------------------------------------------------

def test_ground_topic_web_fallback(agent, monkeypatch):
    # Force the local library to miss so the web path is exercised.
    monkeypatch.setattr(tg, "_wiki_teacher", lambda _a: None)

    extract = ("The three-body problem is the problem of taking the initial "
               "positions and velocities of three point masses and solving for "
               "their subsequent motion under Newtonian gravity.")
    monkeypatch.setattr(tg, "_http_get", _canned_http_get(
        {"three body problem": "Three-body problem"},
        {"Three-body problem": extract}))

    ans = tg.ground_topic(agent, "three body problem")
    assert ans == extract, "ground_topic must return the REST summary extract"
    # Persisted: answerable offline, under the PHRASE concept.
    assert agent.answer_about("three body problem") == extract
    assert "taught_three_body_problem" in agent.taught_capabilities(), (
        "a multi-word phrase must persist under its normalised phrase concept")


def test_ground_topic_web_miss_returns_none(agent, monkeypatch):
    monkeypatch.setattr(tg, "_wiki_teacher", lambda _a: None)
    # opensearch returns no title -> ungroundable -> None (never raises).
    monkeypatch.setattr(tg, "_http_get", _canned_http_get({}, {}))
    assert tg.ground_topic(agent, "arc agi v3 ls20 nonexistent") is None


@pytest.mark.parametrize("extract", [
    "Route or routes may refer to:Air route, route structure or airway\\nClimbing route, path of ascent.",
    "Body may refer to:\\nHuman body\\nCelestial body",
])
def test_disambiguation_header_with_entries_is_not_grounded(extract):
    assert tg._is_disambiguation_extract(extract)


def test_disambiguation_phrase_in_article_body_is_not_a_header():
    assert not tg._is_disambiguation_extract(
        "In this discussion, a route may refer to a path between two places.")


def test_disambiguation_header_is_not_persisted_as_grounding(agent, monkeypatch):
    monkeypatch.setattr(tg, "_wiki_teacher", lambda _a: None)
    extract = "Route or routes may refer to:Air route, route structure or airway\\nClimbing route, path of ascent."
    monkeypatch.setattr(tg, "_http_get", _canned_http_get(
        {"route": "Route"}, {"Route": extract}))

    assert tg.ground_topic(agent, "route") is None
    assert "taught_route" not in agent.taught_capabilities()


def test_ground_topic_no_web_when_disallowed(agent, monkeypatch):
    monkeypatch.setattr(tg, "_wiki_teacher", lambda _a: None)

    def _boom(url, timeout=8):
        raise AssertionError("web must NOT be called when allow_web=False")

    monkeypatch.setattr(tg, "_http_get", _boom)
    assert tg.ground_topic(agent, "three body problem", allow_web=False) is None


# ---------------------------------------------------------------------------
# autonomous path: scan_and_search over a hand-minted SearchRequest
# ---------------------------------------------------------------------------

def test_scan_and_search_processes_request(agent, monkeypatch):
    monkeypatch.setattr(tg, "_wiki_teacher", lambda _a: None)

    extract = "Photosynthesis is a process used by plants to convert light into chemical energy."
    http_get = _canned_http_get(
        {"photosynthesis": "Photosynthesis"},
        {"Photosynthesis": extract})

    req = mint_search_request(agent, "photosynthesis")
    assert agent.s.node(req)["attrs"]["status"] == "requested"

    touched = scan_and_search(agent, http_get=http_get, timeout=5)
    assert touched == [req]

    a = agent.s.node(req)["attrs"]
    assert a["status"] == "done", a
    assert extract[:20] in a.get("answer", "")
    # Grounded + persisted: answerable offline afterward.
    assert agent.answer_about("photosynthesis") == extract


def test_search_candidate_io_payload_is_graph_free_until_owner_commit(agent, monkeypatch):
    monkeypatch.setattr(tg, "_wiki_teacher", lambda _a: None)
    req = mint_search_request(agent, "photosynthesis")
    before = agent.s.node_count()
    getter = _canned_http_get(
        {"photosynthesis": "Photosynthesis"},
        {"Photosynthesis": "Photosynthesis converts light into energy."})
    attrs = agent.s.node(req)["attrs"]

    payloads = tg.retrieve_search_candidate_payloads(
        "photosynthesis", referent_status=attrs["referent_status"],
        referents=attrs["referents"], http_get=getter)

    assert len(payloads) == 1
    assert payloads[0]["title"] == "Photosynthesis"
    assert agent.s.node_count() == before
    assert list(agent.inner.neighbours(req, "has_candidate")) == []

    assert tg.commit_search_candidate_payloads(agent, req, payloads) == 1
    candidates = list(agent.inner.neighbours(req, "has_candidate"))
    assert len(candidates) == 1
    assert agent.s.node(candidates[0])["attrs"]["extract"].startswith(
        "Photosynthesis converts")


def test_scan_and_search_miss_marks_failed(agent, monkeypatch):
    monkeypatch.setattr(tg, "_wiki_teacher", lambda _a: None)
    http_get = _canned_http_get({}, {})   # opensearch finds nothing

    req = mint_search_request(agent, "utterly unknown topic zzzz")
    touched = scan_and_search(agent, http_get=http_get, timeout=5)
    assert touched == [req]
    assert agent.s.node(req)["attrs"]["status"] == "failed"


def test_scan_and_search_noop_when_nothing_requested(agent):
    assert scan_and_search(agent, timeout=3) == []


def test_successful_aspect_grounding_supersedes_generic_search(agent, monkeypatch):
    monkeypatch.setattr(tg, "ground_topic_aspect", lambda a, q, aspect, **_kw: a.learn_from_teacher(
        f"composition of {q}", {
            "answer": "The Moon is mostly silicate rock.",
            "learn": [{"phrase": f"composition of {q}",
                       "answer": "The Moon is mostly silicate rock."}],
        }))
    ground = agent.s.add_node("GroundRequest", {
        "query": "moon", "aspect": "made_of", "status": "requested"})
    search = mint_search_request(agent, "moon")

    scan_and_sync_ground(agent)

    assert agent.s.node(ground)["attrs"]["status"] == "done"
    assert agent.s.node(search)["attrs"]["status"] == "superseded"
    assert list(agent.inner.neighbours(search, "superseded_by")) == [ground]
    assert "silicate" in agent.s.node(ground)["attrs"]["answer"].lower()


def test_failed_specific_grounding_leaves_generic_search_fallback(agent, monkeypatch):
    monkeypatch.setattr(tg, "ground_topic_aspect", lambda *_args, **_kw: None)
    agent.s.add_node("GroundRequest", {
        "query": "moon", "aspect": "made_of", "status": "requested"})
    search = mint_search_request(agent, "moon")

    scan_and_sync_ground(agent)

    assert agent.s.node(search)["attrs"]["status"] == "requested"
    assert not list(agent.inner.neighbours(search, "superseded_by"))


def test_async_composition_grounding_preserves_detail_and_local_summary_precedence(
        agent, monkeypatch):
    monkeypatch.setattr(tg, "_detail_local", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(tg, "_ground_local",
                        lambda _agent, _phrase: "The Moon is basaltic rock.")
    local = tg.ground_local_attempt(agent, "moon", "made_of")
    assert local == {"settled": False, "answer": None}
    payload = {"detail_chunks": [], "fallback": {
        "answer": "The Moon is made of silicate and basaltic rock."}}
    assert tg.commit_ground_payload(agent, "moon", "made_of", payload) == \
        "The Moon is basaltic rock."

    monkeypatch.setattr(tg, "_ground_local", lambda *_args, **_kwargs: None)
    assert tg.commit_ground_payload(agent, "moon", "made_of", payload) == \
        "The Moon is made of silicate and basaltic rock."
    assert agent.taught_capabilities()["taught_composition_of_moon"](None) == \
        "The Moon is made of silicate and basaltic rock."


def test_graph_selected_search_host_action_fulfills_ground_request_first(
        agent, monkeypatch):
    from scripts import jabberwock_daemon
    from domains import fetch_dispatch as fd

    calls = []
    monkeypatch.setattr(fd, "scan_and_sync_ground",
                        lambda _agent, **_kw: calls.append("ground"))
    monkeypatch.setattr(fd, "scan_and_search",
                        lambda _agent, **_kw: calls.append("search"))

    jabberwock_daemon._search_tick(agent)

    assert calls == ["ground", "search"]


def test_daemon_search_io_is_pending_until_graph_owner_commits(agent, monkeypatch):
    import threading
    from scripts import jabberwock_daemon as daemon

    monkeypatch.setattr(tg, "_wiki_teacher", lambda _a: None)
    req = mint_search_request(agent, "photosynthesis")
    payload = {
        "title": "Photosynthesis",
        "extract": "Photosynthesis converts light into chemical energy.",
        "overlap_ratio": 1.0,
        "is_disambiguation": 0.0,
        "provenance_source": "wikipedia",
        "provenance_query": "photosynthesis",
        "evidence_path": "SearchRequest -> has_candidate -> SearchCandidate",
        "epistemic_status": "candidate",
        "referent_status": "supported",
        "referent_coverage": [True],
        "referent_coverage_complete": 1.0,
        "referent_evidence_path": "SearchRequest -> referent_evidence -> supported",
        "communication_event_claimed": 0.0,
    }
    release_io = threading.Event()

    def slow_retrieve(_query, **_kwargs):
        release_io.wait(timeout=5)
        return [payload]

    monkeypatch.setattr(tg, "retrieve_search_candidate_payloads", slow_retrieve)
    host = agent.s.add_node("HostActionRequest", {
        "action": "search", "status": "requested", "urgency": 1,
        "residual": 0, "estimated_cost": 1, "deadline": 0,
    })
    state = daemon.DaemonState(agent, "test")
    monkeypatch.setattr(
        daemon, "_host_action_handlers",
        lambda _state, _world: {"search": lambda: daemon._search_tick(agent, state)},
    )

    with daemon.AGENT_LOCK:
        assert daemon._execute_host_action_requests(state) == 0
    assert agent.s.node(host)["attrs"]["status"] == "io_pending"
    assert agent.s.node(req)["attrs"]["status"] == "running"
    assert list(agent.inner.neighbours(host, "has_receipt")) == []
    assert daemon.AGENT_LOCK.acquire(timeout=0.1)
    daemon.AGENT_LOCK.release()
    pending = state.pending_search_host_actions[int(host.value)]
    release_io.set()
    pending["jobs"][0]["future"].result(timeout=5)

    with daemon.AGENT_LOCK:
        assert daemon._execute_host_action_requests(state) == 1
    assert agent.s.node(host)["attrs"]["status"] == "done"
    assert agent.s.node(req)["attrs"]["status"] == "done"
    assert len(list(agent.inner.neighbours(req, "has_candidate"))) == 1
    assert len(list(agent.inner.neighbours(host, "has_receipt"))) == 1
    state.search_io_executor.shutdown(wait=True)


def test_daemon_causal_retrieval_runs_off_lock_and_stages_on_graph_owner(
        agent, monkeypatch):
    import threading
    from domains import causal_retrieval as cr
    from scripts import jabberwock_daemon as daemon

    request = agent.s.add_node("CausalRetrievalRequest", {
        "schema": "causal_retrieval_request.v1", "status": "requested",
        "topic": "malaria", "topic_entity_id": "Q12156",
        "relation": "incoming_cause",
        "authority": "none",
    })
    host = agent.s.add_node("HostActionRequest", {
        "action": "causal_retrieval", "source_type": "CausalRetrievalRequest",
        "source": request, "status": "requested", "urgency": 1,
        "residual": 1, "estimated_cost": 1, "deadline": 0,
    })
    candidate = {
        "schema": "causal_retrieval_candidate.v1", "provider": "wikidata",
        "query": "malaria", "source_entity_id": "Q12156",
        "source_label": "malaria", "property_id": "P828",
        "cause_entity_id": "Q133969", "statement_id": "Q12156$claim",
        "rank": "normal", "references": [{"P854": ["https://example.org/ref"]}],
        "source_url": "https://www.wikidata.org/wiki/Q12156",
        "epistemic_status": "candidate_unverified", "authority": "none",
    }
    release_io = threading.Event()

    def retrieve(_topic, **_kwargs):
        release_io.wait(timeout=5)
        return [candidate]

    monkeypatch.setattr(cr, "retrieve_causal_candidate_payloads", retrieve)
    held_before = set(agent.s.nodes("HeldAnswer"))
    state = daemon.DaemonState(agent, "causal-retrieval-test")
    try:
        with daemon.AGENT_LOCK:
            assert daemon._execute_host_action_requests(state) == 0
        assert agent.s.node(host)["attrs"]["status"] == "io_pending"
        assert agent.s.node(request)["attrs"]["status"] == "running"
        assert list(agent.s.nodes("CausalRetrievalCandidate")) == []
        assert daemon.AGENT_LOCK.acquire(timeout=0.1)
        daemon.AGENT_LOCK.release()

        pending = state.pending_search_host_actions[int(host.value)]
        release_io.set()
        pending["jobs"][0]["future"].result(timeout=5)
        with daemon.AGENT_LOCK:
            assert daemon._execute_host_action_requests(state) == 1

        assert agent.s.node(host)["attrs"]["status"] == "done"
        assert agent.s.node(request)["attrs"]["status"] == "candidates_staged"
        staged = list(agent.inner.neighbours(request, "has_candidate"))
        assert len(staged) == 1
        assert agent.s.node(staged[0])["attrs"]["authority"] == "none"
        assert agent.inner.neighbours(staged[0], "causal_influence") == []
        assert set(agent.s.nodes("HeldAnswer")) == held_before
    finally:
        release_io.set()
        state.search_io_executor.shutdown(wait=True, cancel_futures=True)


def test_daemon_requeues_search_io_interrupted_by_restart(agent):
    from scripts import jabberwock_daemon as daemon

    req = mint_search_request(agent, "photosynthesis")
    agent.inner.set_attr(req, "status", "running")
    agent.inner.set_attr(req, "search_io_token", "stale-process-token")
    ground = agent.s.add_node("GroundRequest", {
        "query": "moon", "status": "running",
        "ground_io_token": "stale-ground-token"})
    detail = agent.s.add_node("DetailRequest", {
        "topic": "moon", "status": "running",
        "detail_io_token": "stale-detail-token"})
    host = agent.s.add_node("HostActionRequest", {
        "action": "search", "status": "io_pending"})
    task = agent.s.add_node("Task", {"status": "io_pending"})
    agent.inner.add_edge_unchecked(host, "scheduled_as", task)

    state = daemon.DaemonState(agent, "restart-test")
    try:
        assert agent.s.node(req)["attrs"]["status"] == "requested"
        assert agent.s.node(req)["attrs"]["search_io_token"] is None
        assert agent.s.node(ground)["attrs"]["status"] == "requested"
        assert agent.s.node(ground)["attrs"]["ground_io_token"] is None
        assert agent.s.node(detail)["attrs"]["status"] == "requested"
        assert agent.s.node(detail)["attrs"]["detail_io_token"] is None
        assert agent.s.node(host)["attrs"]["status"] == "requested"
        assert agent.s.node(task)["attrs"]["status"] == "host_requested"
    finally:
        state.search_io_executor.shutdown(wait=True)


def test_daemon_detail_request_retrieves_off_lock_and_commits_on_owner(agent, monkeypatch):
    import threading
    from scripts import jabberwock_daemon as daemon

    detail = agent.s.add_node("DetailRequest", {"topic": "moon", "status": "requested"})
    host = agent.s.add_node("HostActionRequest", {
        "action": "detail", "status": "requested", "source": detail,
        "urgency": 1, "residual": 0, "estimated_cost": 1, "deadline": 0,
    })
    release_io = threading.Event()
    monkeypatch.setattr(tg, "detail_local_chunks", lambda *_args, **_kwargs: [])
    def retrieve_detail(*_args, **_kwargs):
        release_io.wait(timeout=5)
        return ["The Moon is a natural satellite."]
    monkeypatch.setattr(tg, "retrieve_detail_payload", retrieve_detail)
    state = daemon.DaemonState(agent, "detail-async-test")
    monkeypatch.setattr(
        daemon, "_host_action_handlers",
        lambda _state, _world: {"detail": lambda: daemon._detail_tick(agent, state)},
    )
    try:
        with daemon.AGENT_LOCK:
            assert daemon._execute_host_action_requests(state) == 0
        assert agent.s.node(detail)["attrs"]["status"] == "running"
        assert daemon.AGENT_LOCK.acquire(timeout=0.1)
        daemon.AGENT_LOCK.release()
        job = state.pending_search_host_actions[int(host.value)]["jobs"][0]
        assert job["kind"] == "detail"
        release_io.set()
        job["future"].result(timeout=5)
        with daemon.AGENT_LOCK:
            assert daemon._execute_host_action_requests(state) == 1
        assert agent.s.node(detail)["attrs"]["status"] == "done", agent.s.node(detail)["attrs"]
        assert len(list(agent.inner.neighbours(host, "has_receipt"))) == 1
    finally:
        release_io.set()
        state.search_io_executor.shutdown(wait=True)


def test_daemon_specific_grounding_is_async_and_supersedes_generic_search(
        agent, monkeypatch):
    import threading
    from scripts import jabberwock_daemon as daemon

    ground = agent.s.add_node("GroundRequest", {
        "query": "moon", "status": "requested"})
    search = mint_search_request(agent, "moon")
    host = agent.s.add_node("HostActionRequest", {
        "action": "search", "status": "requested", "source": ground,
        "urgency": 1, "residual": 0, "estimated_cost": 1, "deadline": 0,
    })
    release_io = threading.Event()
    monkeypatch.setattr(tg, "ground_local_attempt",
                        lambda *_args, **_kwargs: {"settled": False, "answer": None})

    def retrieve(query, aspect=None, **_kwargs):
        release_io.wait(timeout=5)
        return {"attempts": [{"phrase": query, "answer": "The Moon orbits Earth."}]}

    monkeypatch.setattr(tg, "retrieve_ground_payload", retrieve)
    state = daemon.DaemonState(agent, "ground-async-test")
    monkeypatch.setattr(
        daemon, "_host_action_handlers",
        lambda _state, _world: {"search": lambda: daemon._search_tick(agent, state)},
    )
    try:
        with daemon.AGENT_LOCK:
            assert daemon._execute_host_action_requests(state) == 0
        assert agent.s.node(ground)["attrs"]["status"] == "running"
        assert agent.s.node(search)["attrs"]["status"] == "requested"
        assert daemon.AGENT_LOCK.acquire(timeout=0.1)
        daemon.AGENT_LOCK.release()
        pending = state.pending_search_host_actions[int(host.value)]
        assert pending["jobs"][0]["kind"] == "ground"
        release_io.set()
        pending["jobs"][0]["future"].result(timeout=5)

        with daemon.AGENT_LOCK:
            assert daemon._execute_host_action_requests(state) == 1
        assert agent.s.node(ground)["attrs"]["status"] == "done"
        assert agent.s.node(search)["attrs"]["status"] == "superseded"
        assert list(agent.inner.neighbours(search, "superseded_by")) == [ground]
        assert len(list(agent.inner.neighbours(host, "has_receipt"))) == 1
    finally:
        release_io.set()
        state.search_io_executor.shutdown(wait=True)


def test_daemon_generic_host_action_stages_matching_ground_request_first(
        agent, monkeypatch):
    """The real scheduler mints only a generic SearchRequest host action."""
    import threading
    from scripts import jabberwock_daemon as daemon

    ground = agent.s.add_node("GroundRequest", {
        "query": "moon", "status": "requested"})
    search = mint_search_request(agent, "moon")
    host = agent.s.add_node("HostActionRequest", {
        "action": "search", "status": "requested", "source": search,
        "urgency": 1, "residual": 0, "estimated_cost": 1, "deadline": 0,
    })
    release_io = threading.Event()
    monkeypatch.setattr(tg, "ground_local_attempt",
                        lambda *_args, **_kwargs: {"settled": False, "answer": None})

    def retrieve(query, aspect=None, **_kwargs):
        release_io.wait(timeout=5)
        return {"attempts": [{"phrase": query, "answer": "The Moon orbits Earth."}]}

    monkeypatch.setattr(tg, "retrieve_ground_payload", retrieve)
    state = daemon.DaemonState(agent, "generic-host-ground-priority-test")
    monkeypatch.setattr(
        daemon, "_host_action_handlers",
        lambda _state, _world: {"search": lambda: daemon._search_tick(agent, state)},
    )
    try:
        with daemon.AGENT_LOCK:
            assert daemon._execute_host_action_requests(state) == 0
        assert agent.s.node(host)["attrs"]["status"] == "io_pending"
        assert agent.s.node(ground)["attrs"]["status"] == "running"
        assert agent.s.node(search)["attrs"]["status"] == "requested"
        pending = state.pending_search_host_actions[int(host.value)]
        assert [job["kind"] for job in pending["jobs"]] == ["ground"]
        release_io.set()
        pending["jobs"][0]["future"].result(timeout=5)
        with daemon.AGENT_LOCK:
            assert daemon._execute_host_action_requests(state) == 1
        assert agent.s.node(ground)["attrs"]["status"] == "done"
        assert agent.s.node(search)["attrs"]["status"] == "superseded"
        assert list(agent.inner.neighbours(search, "superseded_by")) == [ground]
        assert len(list(agent.inner.neighbours(host, "has_receipt"))) == 1
    finally:
        release_io.set()
        state.search_io_executor.shutdown(wait=True)


def test_daemon_search_io_commits_in_host_request_order(agent, monkeypatch):
    import threading
    from scripts import jabberwock_daemon as daemon

    first = mint_search_request(agent, "first topic")
    second = mint_search_request(agent, "second topic")
    host_first = agent.s.add_node("HostActionRequest", {
        "action": "search", "status": "requested", "source": first,
        "urgency": 1, "residual": 0, "estimated_cost": 1, "deadline": 0,
    })
    host_second = agent.s.add_node("HostActionRequest", {
        "action": "search", "status": "requested", "source": second,
        "urgency": 1, "residual": 0, "estimated_cost": 1, "deadline": 0,
    })
    release_first = threading.Event()
    second_finished = threading.Event()

    def retrieve(query, **_kwargs):
        if query == "first topic":
            release_first.wait(timeout=5)
        else:
            second_finished.set()
        return []

    monkeypatch.setattr(tg, "retrieve_search_candidate_payloads", retrieve)
    state = daemon.DaemonState(agent, "ordered-search-commit-test")
    monkeypatch.setattr(
        daemon, "_host_action_handlers",
        lambda _state, _world: {"search": lambda: daemon._search_tick(agent, state)},
    )
    try:
        with daemon.AGENT_LOCK:
            assert daemon._execute_host_action_requests(state) == 0
        pending_first = state.pending_search_host_actions[int(host_first.value)]
        pending_second = state.pending_search_host_actions[int(host_second.value)]
        pending_second["jobs"][0]["future"].result(timeout=5)
        assert second_finished.is_set()

        # The later Future has returned, but graph mutation and receipt must
        # wait for the earlier graph-selected request.
        with daemon.AGENT_LOCK:
            assert daemon._execute_host_action_requests(state) == 0
        assert agent.s.node(host_first)["attrs"]["status"] == "io_pending"
        assert agent.s.node(host_second)["attrs"]["status"] == "io_pending"
        assert agent.s.node(second)["attrs"]["status"] == "running"
        assert list(agent.inner.neighbours(host_second, "has_receipt")) == []

        release_first.set()
        pending_first["jobs"][0]["future"].result(timeout=5)
        with daemon.AGENT_LOCK:
            assert daemon._execute_host_action_requests(state) == 2
        assert agent.s.node(host_first)["attrs"]["status"] == "done"
        assert agent.s.node(host_second)["attrs"]["status"] == "done"
        assert len(list(agent.inner.neighbours(host_first, "has_receipt"))) == 1
        assert len(list(agent.inner.neighbours(host_second, "has_receipt"))) == 1
    finally:
        release_first.set()
        state.search_io_executor.shutdown(wait=True)


def test_daemon_failed_specific_grounding_releases_generic_fallback(
        agent, monkeypatch):
    import threading
    from scripts import jabberwock_daemon as daemon

    ground = agent.s.add_node("GroundRequest", {
        "query": "moon", "status": "requested"})
    search = mint_search_request(agent, "moon")
    ground_host = agent.s.add_node("HostActionRequest", {
        "action": "search", "status": "requested", "source": ground,
        "urgency": 1, "residual": 0, "estimated_cost": 1, "deadline": 0,
    })
    search_host = agent.s.add_node("HostActionRequest", {
        "action": "search", "status": "requested", "source": search,
        "urgency": 1, "residual": 0, "estimated_cost": 1, "deadline": 0,
    })
    release_io = threading.Event()
    monkeypatch.setattr(tg, "ground_local_attempt",
                        lambda *_args, **_kwargs: {"settled": False, "answer": None})
    monkeypatch.setattr(tg, "retrieve_ground_payload",
                        lambda *_args, **_kwargs: (release_io.wait(timeout=5) or {})
                        and {"attempts": []})
    monkeypatch.setattr(tg, "retrieve_search_candidate_payloads",
                        lambda *_args, **_kwargs: [])
    state = daemon.DaemonState(agent, "ground-fallback-test")
    monkeypatch.setattr(
        daemon, "_host_action_handlers",
        lambda _state, _world: {"search": lambda: daemon._search_tick(agent, state)},
    )
    try:
        assert daemon._execute_host_action_requests(state) == 0
        assert agent.s.node(ground)["attrs"]["status"] == "running"
        assert agent.s.node(search_host)["attrs"]["status"] == "requested"
        ground_job = state.pending_search_host_actions[int(ground_host.value)]["jobs"][0]
        release_io.set()
        ground_job["future"].result(timeout=5)

        daemon._execute_host_action_requests(state)
        assert agent.s.node(ground)["attrs"]["status"] == "failed"
        assert agent.s.node(search)["attrs"]["status"] == "running"
        assert agent.s.node(search_host)["attrs"]["status"] == "io_pending"
        search_job = state.pending_search_host_actions[int(search_host.value)]["jobs"][0]
        search_job["future"].result(timeout=5)
        daemon._execute_host_action_requests(state)
        assert agent.s.node(search)["attrs"]["status"] == "failed"
    finally:
        release_io.set()
        state.search_io_executor.shutdown(wait=True)


# ---------------------------------------------------------------------------
# the seed rule mints a SearchRequest from a routed-topic goal
# ---------------------------------------------------------------------------

def test_topic_search_seed_mints_request_from_answer_topic(agent):
    # A reflexive topic question routes to Goal{kind:answer_topic, concept:'moon'}
    # (conversation_topic_route); the topic_search seed rule should then mint a
    # SearchRequest for that topic (the autonomous background-grounding hook).
    agent.converse("What do you know about the moon?", speech_act="question")
    reqs = [n for n in agent.s.nodes("SearchRequest")
            if agent.inner.has_node(n)
            and agent.s.node(n)["attrs"].get("query") == "moon"]
    assert reqs, ("the topic_search seed rule must mint a SearchRequest{query:'moon'} "
                  "from the routed answer_topic goal")
    # The request is minted mid-turn and may already have been serviced inline
    # (converse fulfils pending I/O within the turn) or superseded when the
    # in-turn fulfiller answered the goal from held knowledge first — the
    # assertion is that the MINT happened, not that the turn left it pending.
    assert agent.s.node(reqs[0])["attrs"].get("status") in (
        "requested", "running", "candidates_ready", "done", "superseded",
        "failed")


def test_ground_and_search_requests_share_one_remote_lookup(agent, monkeypatch):
    """GroundRequest stays local when its SearchRequest sibling owns web I/O."""
    from domains import fetch_dispatch
    from types import SimpleNamespace
    import sys

    message = agent.s.add_node("Message", {"text": "What is a blorf?"})
    agent.inner.add_edge_unchecked(agent.agent, "received", message)
    goal = agent.s.add_node("Goal", {
        "kind": "answer_topic", "concept": "blorf", "status": "active"})
    agent.inner.add_edge_unchecked(agent.agent, "has_goal", goal)
    agent.inner.add_edge_unchecked(goal, "comprehends", message)
    ground = agent.s.add_node("GroundRequest", {
        "query": "blorf", "status": "requested"})
    agent.inner.add_edge_unchecked(goal, "ground_request", ground)
    search = mint_search_request(agent, "blorf")
    agent.inner.set_attr(search, "source", "answer_topic")

    calls = []
    monkeypatch.setitem(
        sys.modules, "evaluation.p0a.legacy_io_guard",
        SimpleNamespace(deny_direct_io=lambda *_args: None))
    monkeypatch.setattr(
        fetch_dispatch, "scan_and_sync_ground",
        lambda _agent, *, request_ids, allow_web=True:
            calls.append(("ground", request_ids, allow_web)))
    monkeypatch.setattr(
        fetch_dispatch, "scan_and_search",
        lambda _agent, *, request_ids:
            calls.append(("search", request_ids, None)))
    agent._dispatch_pending_io(message)

    assert calls == [
        ("ground", {int(ground.value)}, False),
        ("search", {int(search.value)}, None),
    ]


def test_scan_and_sync_ground_forwards_local_only_evidence(agent, monkeypatch):
    calls = []
    monkeypatch.setattr(
        tg, "ground_topic",
        lambda _agent, _phrase, *, allow_web=True:
            calls.append(allow_web) or None)
    request = agent.s.add_node("GroundRequest", {
        "query": "blorf", "status": "requested"})
    scan_and_sync_ground(
        agent, request_ids=[request], allow_web=False)
    assert calls == [False]
    assert agent.s.node(request)["attrs"]["status"] == "failed"


def test_held_answer_does_not_mint_duplicate_search_request(agent):
    agent._persist_held_answer("moon", "the Moon is Earth's natural satellite")

    reply = agent.converse("What do you know about the moon?",
                           speech_act="question")

    assert "natural satellite" in reply.lower()
    assert not [
        req for kind in ("GroundRequest", "SearchRequest")
        for req in agent.s.nodes(kind)
        if agent.inner.has_node(req)
        and agent.s.node(req)["attrs"].get("query") == "moon"
    ]


def test_topic_resolution_requires_referent_linked_evidence(agent, monkeypatch):
    """A same-key answer without grounding evidence is not a resolution."""
    ha = agent._persist_held_answer("borogove", "an answer about an unrelated referent")
    assert ha is not None
    # Simulate a legacy/poisoned candidate that has the index key but no
    # referent-linked epistemic support.
    agent.inner.set_attr(ha, "grounding_referent", None)
    agent.inner.set_attr(ha, "grounding_status", None)
    agent.inner.set_attr(ha, "grounding_evidence_path", None)
    import domains.topic_grounding as _tg
    monkeypatch.setattr(_tg, "ground_topic", lambda *args, **kwargs: None)

    reply = agent.converse("What do you know about the borogove?",
                           speech_act="question")
    assert "unrelated referent" not in reply.lower()
    goals = [g for g in agent.inner.neighbours(agent.agent, "has_goal")
             if agent.s.node(g)["attrs"].get("kind") == "answer_topic"
             and agent.s.node(g)["attrs"].get("concept") == "borogove"]
    assert goals
    assert agent.s.node(goals[-1])["attrs"].get("outcome") == "unresolved"


def test_blocked_turn_does_not_drain_unrelated_retrieval_requests(agent, monkeypatch):
    from domains import fetch_dispatch

    stale_ground = agent.s.add_node("GroundRequest", {
        "query": "quorplezap the door", "status": "requested",
        "source": "answer_topic",
    })
    stale_search = agent.s.add_node("SearchRequest", {
        "query": "quorplezap the door", "status": "requested",
        "source": "answer_topic",
    })
    stale_detail = agent.s.add_node("DetailRequest", {
        "topic": "gate", "status": "requested",
    })
    calls = []

    def record_dispatch(*_args, **_kwargs):
        calls.append(True)
        return []

    monkeypatch.setattr(fetch_dispatch, "scan_and_sync_ground", record_dispatch)
    monkeypatch.setattr(fetch_dispatch, "scan_and_search", record_dispatch)
    monkeypatch.setattr(fetch_dispatch, "scan_and_ingest_detail", record_dispatch)

    agent.converse(
        "What is beyond the wall?", speech_act="question",
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "standalone",
                 "evidence": ["explicit_uncertainty"]})
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(
        agent.s.node(inbound)["attrs"]["communication_interpretation_id"]
    )["attrs"]

    assert interpretation["cognitive_disposition"] == "blocked"
    assert not calls
    assert agent.s.node(stale_ground)["attrs"]["status"] == "requested"
    assert agent.s.node(stale_search)["attrs"]["status"] == "requested"
    assert agent.s.node(stale_detail)["attrs"]["status"] == "requested"


def test_answer_goal_fulfills_only_its_own_retrieval_request(agent, monkeypatch):
    stale_ground = agent.s.add_node("GroundRequest", {
        "query": "unrelated stale topic", "status": "requested",
        "source": "answer_topic",
    })
    stale_search = agent.s.add_node("SearchRequest", {
        "query": "unrelated stale topic", "status": "requested",
        "source": "answer_topic",
    })
    stale_detail = agent.s.add_node("DetailRequest", {
        "topic": "unrelated stale topic", "status": "requested",
    })
    calls = []

    def ground_current(agent, phrase, **_kwargs):
        calls.append(phrase)
        answer = "the Moon is Earth's natural satellite"
        agent.learn_from_teacher(
            phrase, {"answer": answer,
                     "learn": [{"phrase": phrase, "answer": answer}]})
        return answer

    monkeypatch.setattr(tg, "ground_topic", ground_current)
    reply = agent.converse("What do you know about the moon?",
                           speech_act="question")
    current_ground = next(
        req for req in agent.s.nodes("GroundRequest")
        if agent.inner.has_node(req)
        and agent.s.node(req)["attrs"].get("query") == "moon")

    assert calls == ["moon"]
    assert agent.s.node(current_ground)["attrs"]["status"] in ("done", "superseded")
    assert "natural satellite" in reply.lower()
    assert agent.s.node(stale_ground)["attrs"]["status"] == "requested"
    assert agent.s.node(stale_search)["attrs"]["status"] == "requested"
    assert agent.s.node(stale_detail)["attrs"]["status"] == "requested"
