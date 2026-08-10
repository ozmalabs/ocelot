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
from domains.fetch_dispatch import mint_search_request, scan_and_search


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


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


def test_scan_and_search_miss_marks_failed(agent, monkeypatch):
    monkeypatch.setattr(tg, "_wiki_teacher", lambda _a: None)
    http_get = _canned_http_get({}, {})   # opensearch finds nothing

    req = mint_search_request(agent, "utterly unknown topic zzzz")
    touched = scan_and_search(agent, http_get=http_get, timeout=5)
    assert touched == [req]
    assert agent.s.node(req)["attrs"]["status"] == "failed"


def test_scan_and_search_noop_when_nothing_requested(agent):
    assert scan_and_search(agent, timeout=3) == []


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
        "requested", "running", "candidates_ready", "done", "superseded")
