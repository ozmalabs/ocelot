"""test_browser_world — end-to-end exercise of the dual-level BrowserWorld
(worlds/browser.py) and the browse-dispatch mechanism (domains/browse_dispatch.py)
against a LOCAL stdlib http.server (no real internet). Mirrors
tests/test_fetch_dispatch.py's shape (local server fixture, mint -> scan/act ->
assert on the graph) one level up: BrowserWorld drives a real headless
Chromium tab via Playwright and mirrors BOTH the DOM (native level) and a
screenshot segmentation (human-equivalent level) into the agent's graph.

Covers:
  (a) reset  -> Elements w/ bboxes + Affordances + visual Regions + renders_as
  (b) apply(click link)   -> navigation, incremental re-ingest, session records it
  (c) apply(click button) -> incremental ingest: a ChangeEvent is minted for the
      mutated element, unchanged elements are NOT re-minted (small node delta)
  (d) apply(type) + apply(submit) -> form interaction works
  (e) close() -> Element/Region/Affordance counts under the session drop to
      zero; BrowserSession root survives with summary attrs
  (f) scan_and_browse end-to-end on a BrowseRequest, agent with NO browsing
      rules seeded -> perceives the first page only, status "done"

REQUIRES the `region_grouping` seed (see worlds/browser.py's module
docstring): `segment`'s has_region/within edges are Γ-checked and
region_grouping's generic WorldInstance->Region productions are what admit
them. Found this the hard way while building the module -- without it
`segment` still mints Region nodes but every has_region/within edge
silently fails admissibility, so the regions are unreachable from the
session (birthed but orphaned). See test_reset_without_region_grouping_seed
below, which pins that exact failure mode.
"""
from __future__ import annotations

import http.server
import threading

import pytest

from substrate.world_adapter import WorldAdapter
from worlds.browser import BrowserWorld
from domains.browse_dispatch import mint_browse_request, scan_and_browse

# Small, fast-booting seed set (mirrors test_fetch_dispatch.py's CHAT_SEEDS,
# but region_grouping replaces the language seeds -- BrowserWorld needs
# perception, not conversation, to exercise its own contract).
BROWSER_SEEDS = ("decision_core", "learning_core", "perception_core", "region_grouping",
                  "browser_affordance_reach")

INDEX_HTML = """<!doctype html>
<html><head><title>Home</title></head>
<body>
<h1>Welcome to the Test Site</h1>
<p>This is a paragraph with enough text to be kept by the significance filter.</p>
<nav><a href="page2.html" id="link2">Go to page two</a></nav>
<button id="mutate-btn" onclick="document.getElementById('mutable').innerText='The button was clicked and this text changed considerably.'">Click me to mutate</button>
<p id="mutable">Original unmutated paragraph text goes here for testing purposes.</p>
<form id="theform" method="get">
<input type="text" name="q" id="q" />
<input type="submit" value="Submit the form" />
</form>
</body></html>"""

PAGE2_HTML = """<!doctype html>
<html><head><title>Page Two</title></head>
<body>
<h1>This Is Page Two</h1>
<p>You navigated here by clicking the link on the home page, well done indeed.</p>
</body></html>"""


@pytest.fixture()
def adapter():
    a = WorldAdapter(seeds=BROWSER_SEEDS)
    return a


@pytest.fixture()
def local_site(tmp_path):
    """A local stdlib http.server on an ephemeral port, serving a tiny
    multi-page site (headings, paragraphs, a cross-page link, a button that
    mutates the DOM via inline JS, and a text input + submit form). No real
    network access."""
    (tmp_path / "index.html").write_text(INDEX_HTML)
    (tmp_path / "page2.html").write_text(PAGE2_HTML)

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(tmp_path), **kw)

        def log_message(self, fmt, *a):  # quiet
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    port = srv.server_port
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        yield f"http://127.0.0.1:{port}/"
    finally:
        srv.shutdown()
        srv.server_close()


def _by_world_type(S, wtype):
    return [n for n in S.nodes("WorldInstance")
            if S.node(n)["attrs"].get("world_type") == wtype]


# --- (a) reset: dual-level ingest + cross-level grounding --------------------

def test_reset_ingests_both_levels(adapter, local_site):
    w = BrowserWorld(adapter, headless=True)
    try:
        ctx = w.reset(local_site + "index.html")
        S, I = adapter.s, adapter.inner

        assert ctx["cold"] is True
        assert ctx["elements"] >= 7          # h1, p, nav, a, button, p, form, input, input
        assert ctx["affordances"] >= 3        # navigate, click, type, click(submit)
        assert ctx["regions"] > 0             # the human-equivalent level segmented something

        elements = _by_world_type(S, "Element")
        assert len(elements) == ctx["elements"]
        for e in elements:
            a = S.node(e)["attrs"]
            for k in ("bbox_x", "bbox_y", "bbox_w", "bbox_h", "tag", "text"):
                assert k in a, (a, k)

        affordances = _by_world_type(S, "Affordance")
        kinds = {S.node(af)["attrs"]["kind"] for af in affordances}
        assert "navigate" in kinds
        assert "click" in kinds
        assert "type" in kinds

        regions = list(S.nodes("Region"))
        assert len(regions) > 0

        # at least one renders_as edge grounds an Element to a Region.
        renders_as_count = sum(1 for e in elements
                                for _ in I.neighbours(e, "renders_as"))
        assert renders_as_count >= 1

        # legal_actions surfaces the same affordances.
        acts = w.legal_actions()
        assert len(acts) == len(affordances)
    finally:
        w.close()


def test_reset_without_region_grouping_seed_orphans_regions(local_site):
    """Documents the wall found while building this module: without
    region_grouping loaded, segment() still MINTS Region nodes (node
    insertion is unconditional) but has_region/within are Γ-checked and
    silently fail admissibility -- so the regions exist but are unreachable
    from the session. This is why BrowserWorld's docstring requires the seed."""
    bare = WorldAdapter(seeds=("decision_core", "learning_core", "perception_core"))
    w = BrowserWorld(bare, headless=True)
    try:
        ctx = w.reset(local_site + "index.html")
        S, I = bare.s, bare.inner
        sess_wi = w.session_node()
        reachable = list(I.neighbours(sess_wi, "has_region"))
        all_regions = list(S.nodes("Region"))
        assert len(all_regions) > 0            # minted...
        assert reachable == []                  # ...but orphaned (unadmitted edges)
        assert ctx["regions"] == 0               # BrowserWorld counts only reachable ones
    finally:
        w.close()


# --- (b) navigation ------------------------------------------------------------

def test_apply_click_link_navigates_and_reingests(adapter, local_site):
    w = BrowserWorld(adapter, headless=True)
    try:
        w.reset(local_site + "index.html")
        link = next(a[0] for a in w.legal_actions() if "nav" in a[0])
        ctx = w.apply((link,))

        assert ctx["url"].endswith("page2.html")
        assert ctx["cold"] is True             # navigation -> treated as a fresh page
        assert w._pages_visited == 2
        assert w._actions_taken == 1

        S = adapter.s
        sess_wi = w.session_node()
        assert S.node(sess_wi)["attrs"]["url"].endswith("page2.html")
        assert S.node(sess_wi)["attrs"]["pages_visited"] == 2

        texts = {S.node(e)["attrs"]["text"] for e in _by_world_type(S, "Element")}
        assert any("Page Two" in t for t in texts)
        # the old page's link/button/form are gone (pruned on navigation).
        assert not any("mutate" in t.lower() for t in texts)
    finally:
        w.close()


# --- (c) incremental ingest on DOM mutation ------------------------------------

def test_apply_click_button_incremental_change_event(adapter, local_site):
    w = BrowserWorld(adapter, headless=True)
    try:
        w.reset(local_site + "index.html")
        S = adapter.s
        n_before = len(_by_world_type(S, "Element"))

        btn = next(a[0] for a in w.legal_actions() if "button" in a[0])
        ctx = w.apply((btn,))

        n_after = len(_by_world_type(S, "Element"))
        assert n_after == n_before             # no new/removed elements -> no re-minting
        assert ctx["changed"] == 1              # exactly the mutated paragraph

        changes = _by_world_type(S, "ChangeEvent")
        assert len(changes) == 1
        ce = S.node(changes[0])["attrs"]
        assert ce["kind"] == "changed"
        assert "p[1]" in ce["element_id"]

        mutated = next(e for e in _by_world_type(S, "Element")
                        if S.node(e)["attrs"]["world_id"] == "el_" + ce["element_id"])
        assert "clicked" in S.node(mutated)["attrs"]["text"].lower()
    finally:
        w.close()


# --- (d) form interaction --------------------------------------------------------

def test_apply_type_and_submit(adapter, local_site):
    w = BrowserWorld(adapter, headless=True)
    try:
        w.reset(local_site + "index.html")
        S = adapter.s
        text_input = next(a[0] for a in w.legal_actions()
                           if a[0].endswith("input[0]"))
        submit_btn = next(a[0] for a in w.legal_actions()
                           if a[0].endswith("input[1]"))

        w.apply((text_input, "hello world query"))
        typed = next(e for e in _by_world_type(S, "Element")
                     if S.node(e)["attrs"]["world_id"].endswith("input[0]"))
        assert S.node(typed)["attrs"]["value"] == "hello world query"

        ctx = w.apply((submit_btn,))
        assert "q=hello" in ctx["url"]
        assert ctx["cold"] is True             # GET form submit -> a real navigation
    finally:
        w.close()


# --- (e) close() prunes, session survives -----------------------------------------

def test_close_prunes_percepts_keeps_session(adapter, local_site):
    w = BrowserWorld(adapter, headless=True)
    w.reset(local_site + "index.html")
    S = adapter.s
    sess_wi = w.session_node()
    assert len(_by_world_type(S, "Element")) > 0
    assert len(list(S.nodes("Region"))) > 0

    w.close()

    assert _by_world_type(S, "Element") == []
    assert _by_world_type(S, "Affordance") == []
    # "GridCell" is the OLD screenshot-path pixel node type; the live-eye
    # path (worlds/browser.py's default) never mints it at all -- it mints
    # world_type=="Cell" WorldInstance nodes via fb_sample instead, so this
    # assertion is vacuously true whenever the live eye is active. Assert
    # the live-eye equivalent too, so the check isn't silently vacuous
    # regardless of which pixel-source path this session actually used.
    assert _by_world_type(S, "GridCell") == []
    assert _by_world_type(S, "Cell") == []
    assert list(S.nodes("Region")) == []

    assert S.has_node(sess_wi)
    final = S.node(sess_wi)["attrs"]
    assert final["status"] == "closed"
    assert final["pages_visited"] == 1
    assert final["actions_taken"] == 0


# --- (f) browse-dispatch, no browsing rules seeded -> honest perceive-only ------

def test_scan_and_browse_perceive_only_no_rules(adapter, local_site):
    req = mint_browse_request(adapter, local_site + "index.html", purpose="look around")
    assert adapter.s.node(req)["attrs"]["status"] == "requested"

    touched = scan_and_browse(adapter, max_actions=5, headless=True)
    assert touched == [req]

    a = adapter.s.node(req)["attrs"]
    assert a["status"] == "done", a
    assert not a.get("error")

    S = adapter.s
    sessions = _by_world_type(S, "BrowserSession")
    assert len(sessions) == 1
    sess = S.node(sessions[0])["attrs"]
    assert sess["status"] == "closed"
    assert sess["pages_visited"] == 1
    assert sess["actions_taken"] == 0          # no rules ever wrote chosen_action -> perceive-only

    # the percept subgraph was pruned by close(), same as the direct-API case.
    assert [n for n in S.nodes("WorldInstance")
            if S.node(n)["attrs"].get("world_type") == "Element"] == []


def test_scan_and_browse_noop_when_nothing_requested(adapter):
    assert scan_and_browse(adapter, max_actions=3, headless=True) == []
