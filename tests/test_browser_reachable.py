"""test_browser_reachable — pins the GRAPH-NATIVE `sess -has_affordance-> affordance` mirror
worlds/browser.py now maintains via the `seeds/browser_affordance_reach.json` rules (mint on
`ReachableFrom(sess, "contains")` membership + present > 0, drop when present <= 0), replacing
the hand-rolled Python flattening loop the in-file comment used to name.

Drives a REAL headless Chromium tab via Playwright against a local stdlib http.server (no real
internet) -- same fixture shape as tests/test_browser_world.py, one level down: a page built so
its interactive affordances sit at GRAPH depth >= 2 under the session (`<nav>` wraps a link,
`<form>` wraps an input -- neither `<body>` nor the page's `<h1>`/`<p>` are themselves affording,
so `sess -contains-> nav -contains-> a` and `sess -contains-> form -contains-> input` are the
only paths from the session to either affordance).

Covers:
  (a) both nested affordances are reachable + mirrored onto the session via has_affordance;
  (b) DISCRIMINATIVE: the affording elements are NOT in the one-hop `Neighbours(sess, "contains")`
      set (proving depth actually mattered) but ARE in `ReachableFrom(sess, "contains")`;
  (c) incremental correctness: removing the nested link's wrapping `<nav>` via a DOM mutation
      (button click, incremental re-ingest, no navigation) drops the mirror edge and the
      affordance stops being legally choosable -- the other (still-present) nested affordance
      is unaffected.
"""
from __future__ import annotations

import http.server
import threading

import pytest

from substrate.world_adapter import WorldAdapter
from worlds.browser import BrowserWorld

BROWSER_SEEDS = ("decision_core", "learning_core", "perception_core", "region_grouping",
                  "browser_affordance_reach")

INDEX_HTML = """<!doctype html>
<html><head><title>Reach</title></head>
<body>
<h1>Welcome to the Reach Test Site</h1>
<p>This is a paragraph with enough text to be kept by the significance filter.</p>
<nav id="navwrap">
<a href="target.html" id="deep-link">Learn about the deeply nested thing</a>
</nav>
<form id="theform" method="get">
<input type="text" name="q" id="deep-input" />
</form>
<button id="remove-btn" onclick="document.getElementById('navwrap').remove()">Remove the nav</button>
</body></html>"""

TARGET_HTML = """<!doctype html>
<html><head><title>Target</title></head>
<body><h1>You Made It</h1></body></html>"""


@pytest.fixture()
def adapter():
    return WorldAdapter(seeds=BROWSER_SEEDS)


@pytest.fixture()
def local_site(tmp_path):
    (tmp_path / "index.html").write_text(INDEX_HTML)
    (tmp_path / "target.html").write_text(TARGET_HTML)

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


def _find_element(S, pred):
    """The (unique) Element WorldInstance whose attrs satisfy `pred`."""
    for wi in S.nodes("WorldInstance"):
        if not S.has_node(wi):
            continue
        a = S.node(wi)["attrs"]
        if a.get("world_type") == "Element" and pred(a):
            return wi
    return None


def _affordance_of(I, el_wi):
    """The Affordance an Element `-affords->`, or None."""
    return next(iter(I.neighbours(el_wi, "affords")), None)


# --- (a) + (b): nested affordances mirrored + one-hop discriminative -------------------------

def test_nested_affordances_reachable_not_one_hop(adapter, local_site):
    w = BrowserWorld(adapter, headless=True)
    try:
        w.reset(local_site + "index.html")
        S, I = adapter.s, adapter.inner
        sess_wi = w.session_node()

        link_el = _find_element(S, lambda a: "deeply nested" in str(a.get("text", "")).lower())
        input_el = _find_element(S, lambda a: a.get("name") == "q")
        assert link_el is not None, "the nav-wrapped link must be perceived"
        assert input_el is not None, "the form-wrapped input must be perceived"
        link_aff = _affordance_of(I, link_el)
        input_aff = _affordance_of(I, input_el)
        assert link_aff is not None and input_aff is not None

        # (a) the graph-native mirror includes BOTH depth-2 affordances.
        assert I.has_edge(sess_wi, "has_affordance", link_aff)
        assert I.has_edge(sess_wi, "has_affordance", input_aff)

        # (b) DISCRIMINATIVE: a plain one-hop Neighbours(sess, "contains") does NOT reach either
        # affording element -- only their wrapping <nav>/<form> are one hop away -- proving the
        # mirror is doing genuine depth-2 work, not accidentally matching a one-hop shape.
        one_hop = set(I.neighbours(sess_wi, "contains"))
        assert link_el not in one_hop
        assert input_el not in one_hop

        # ReachableFrom itself reaches both (the primitive the mirror rule is built on).
        reached = set(I.evaluate(
            {"type": "ReachableFrom", "node": {"type": "Var", "name": "sess"}, "edge_type": "contains"},
            {"sess": sess_wi}))
        assert link_el in reached
        assert input_el in reached

        # legal_actions() (the world's own external action list) agrees.
        legal = {a[0] for a in w.legal_actions()}
        assert S.node(link_aff)["attrs"]["world_id"] in legal
        assert S.node(input_aff)["attrs"]["world_id"] in legal
    finally:
        w.close()


# --- (c) incremental: the nested element disappears -> mirror edge drops, not choosable ------

def test_nested_affordance_disappears_drops_mirror_edge(adapter, local_site):
    w = BrowserWorld(adapter, headless=True)
    try:
        w.reset(local_site + "index.html")
        S, I = adapter.s, adapter.inner
        sess_wi = w.session_node()

        link_el = _find_element(S, lambda a: "deeply nested" in str(a.get("text", "")).lower())
        input_el = _find_element(S, lambda a: a.get("name") == "q")
        link_aff = _affordance_of(I, link_el)
        input_aff = _affordance_of(I, input_el)
        assert I.has_edge(sess_wi, "has_affordance", link_aff)
        assert I.has_edge(sess_wi, "has_affordance", input_aff)

        remove_btn = next(a[0] for a in w.legal_actions() if "button" in a[0])
        ctx = w.apply((remove_btn,))
        assert ctx["cold"] is False, "a DOM mutation via inline JS is NOT a navigation"

        # the nav (and its child link) are gone from the DOM -> _walk_dom no longer emits either
        # record -> both land in `disappeared` -> present=0 -> the drop rule fires.
        assert S.node(link_el)["attrs"].get("present", 1.0) == 0.0
        assert not I.has_edge(sess_wi, "has_affordance", link_aff), (
            "the mirror edge to the now-absent nested affordance must be dropped")

        legal_after = {a[0] for a in w.legal_actions()}
        assert S.node(link_aff)["attrs"]["world_id"] not in legal_after, (
            "a disappeared affordance must no longer be legally choosable")

        # discriminative: the OTHER nested affordance (untouched by the mutation) is unaffected.
        assert I.has_edge(sess_wi, "has_affordance", input_aff)
        assert S.node(input_aff)["attrs"]["world_id"] in legal_after
    finally:
        w.close()
