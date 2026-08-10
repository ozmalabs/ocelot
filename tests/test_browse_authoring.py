"""test_browse_authoring — the JABBERWOCK AUTHORS the rules that choose which affordance to act on.

worlds/browser.py + domains/browse_dispatch.py perceive a page dually (DOM + visual) but act on
nothing: `scan_and_browse`'s loop reads `chosen_action` off the mirrored `BrowserSession` node each
tick and applies it — no rule ever WROTE one. This test drives the agent's OWN self-build composer
(domains/reflective_faculty.py: induce_concern -> ground_concern) to AUTHOR:

  (a) a comprehension rule pair — a "find X" instruction Message comprehends into a Goal carrying
      its wanted content (goal -wants-> Mention), via the SAME 'comprehension' composer that already
      handles 'describe' directives (extended, gated on a grounded 'find' relation head);
  (b) the browse-affordance-choice rule pair — chosen_action = the affordance whose label overlaps
      the most wanted words (argmax over affordances of summed word-overlap), plus a stop condition
      once the wanted content is actually visible on the arrived page — via a NEW 'browse' composer
      (a twin of the existing grid-navigation 'decision' composer: BrowserSession/Element/Affordance
      carry none of that composer's position/candidate vocabulary, so its Term cannot be
      parameterised onto this domain; see scripts/jabberwock_browses.py's stage-1 probe, which
      demonstrates the wrong (grid) composer firing on the SAME 'utility' vocabulary first).

Mirrors tests/test_browser_world.py's local http.server fixture pattern, one level up: a 5-page site
(an index with 4 links whose labels/text differ + one target page per link, each about a distinctive
topic) instead of the 2-page fixture there. donkey=0 throughout — no LLM calls anywhere in the loop.
"""
from __future__ import annotations

import http.server
import threading

import pytest

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import induce_concern, ground_concern
from domains.browse_dispatch import mint_browse_request, scan_and_browse

MAX_ACTIONS = 6

INDEX_HTML = """<!doctype html>
<html><head><title>Nature Index</title></head>
<body>
<h1>Welcome to the Nature Index</h1>
<p>This is a small site about natural landforms and features, for testing.</p>
<nav>
<a href="volcanoes.html">Learn about volcanoes</a>
<a href="rivers.html">Learn about rivers</a>
<a href="mountains.html">Learn about mountains</a>
<a href="deserts.html">Learn about deserts</a>
</nav>
</body></html>"""

PAGES = {
    "volcanoes.html": ("Volcanoes", "Volcanoes are dramatic landforms formed by erupting magma."),
    "rivers.html": ("Rivers", "Rivers are flowing bodies of water that carve valleys over time."),
    "mountains.html": ("Mountains", "Mountains are large landforms that rise above the surrounding terrain."),
    "deserts.html": ("Deserts", "Deserts are arid landscapes that receive very little rainfall."),
}


def _page_html(title: str, body: str) -> str:
    return f"<!doctype html><html><head><title>{title}</title></head><body><h1>{title}</h1><p>{body}</p></body></html>"


@pytest.fixture()
def adapter():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    donkey = {"n": 0}
    a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    a._donkey = donkey  # test-harness bookkeeping only
    return a


@pytest.fixture()
def local_site(tmp_path):
    (tmp_path / "index.html").write_text(INDEX_HTML)
    for fname, (title, body) in PAGES.items():
        (tmp_path / fname).write_text(_page_html(title, body))

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


def world_receive(a, instruction: str):
    """THE WORLD'S LANGUAGE RECEIVER (mirrors scripts/arc_self_report.py's world_receive) — translate
    an external instruction into a Message + per-word Mention nodes. Mechanical ingest; no decision,
    no target extraction here — that is the agent's OWN authored comprehension rule's job."""
    msg = a.s.add_node("Message", {"text": instruction})
    for w in instruction.lower().replace(".", "").replace("?", "").split():
        a.inner.add_edge_unchecked(msg, "has_mention", a.s.add_node("Mention", {"text": w}))
    return msg


# --- (a) the existing 'utility' vocabulary fires the WRONG (grid-navigation) composer -----------

def test_existing_decision_composer_wrong_shape_for_browsing():
    """TRY THE EXISTING MACHINERY FIRST: the SAME 'utility'/argmax vocabulary
    jabberwock_builds_decision_faculty.py drives for grid navigation, framed on a fresh agent,
    dispatches to the EXISTING grid-navigation 'decision' composer — confirming a NEW composer
    (this file exercises `_compose_browse_rule`) is genuinely needed, not hand-picked."""
    probe = WorldAdapter(seeds=())
    load_all_seeds(probe)
    ind = induce_concern(probe, [["utility", "ARGMAX", "over", "AFFORDANCE"]],
                          name_hint="stage1_existing_utility_probe")
    g = ground_concern(probe, [ind["capability_key"]]) if ind.get("capability_key") else {}
    assert g.get("path") == "compose_decision_rule"
    assert g.get("form") == "decision_rule"
    # the wrong composer's Term references grid vocabulary (avatar_candidate/cy/cx) that
    # BrowserSession/Element/Affordance simply do not have.
    assert "avatar_candidate" in str(g.get("rule"))


# --- (b) the agent authors its OWN comprehension rules for a 'find X' directive -----------------

def test_agent_authors_find_comprehension_rules(adapter):
    a = adapter
    S, I = a.s, a.inner
    ind = induce_concern(a, [["comprehend", "a", "DIRECTIVE"], ["find", "the", "TARGET"]],
                          name_hint="browse_find_directive")
    assert ind.get("minted") is True
    key = ind["capability_key"]

    before = I.rule_count()
    g = ground_concern(a, [key])
    after = I.rule_count()
    assert g.get("grounded") is True
    assert g.get("path") == "compose_comprehension_rule"
    assert g.get("form") == "find_directive_rule"
    assert after - before == 2
    names = sorted(r["name"] for r in g["rules"])
    assert names == sorted(["comprehend_find_directive_browse_find_directive",
                             "bind_find_target_browse_find_directive"])

    # exercise the authored rules: a 'find X' instruction comprehends into a Goal carrying its
    # wanted content — zero host decision about WHAT the goal wants.
    world_receive(a, "Find the page about volcanoes.")
    I.run_rules()
    goals = [n for n in S.nodes("Goal") if S.node(n)["attrs"].get("kind") == "find"]
    assert len(goals) == 1
    wants = sorted(S.node(w)["attrs"].get("text") for w in I.neighbours(goals[0], "wants"))
    assert wants == ["volcanoes"]   # stopwords (find/the/page/about) excluded


# --- (c) the agent authors its OWN affordance-choice rules ('browse' composer, a twin) -----------

def test_agent_authors_browse_choice_rules(adapter):
    a = adapter
    I = a.inner
    ind = induce_concern(a, [["match", "the", "AFFORDANCE", "to", "the", "GOAL"]],
                          name_hint="browse_choice_relevance")
    assert ind.get("minted") is True
    key = ind["capability_key"]

    before = I.rule_count()
    g = ground_concern(a, [key])
    after = I.rule_count()
    assert g.get("grounded") is True
    assert g.get("path") == "compose_browse_rule"
    assert g.get("form") == "browse_rule"
    assert after - before == 2
    names = sorted(r["name"] for r in g["rules"])
    assert names == sorted(["choose_affordance_by_relevance_browse_choice_relevance",
                             "browse_goal_satisfied_when_seen_browse_choice_relevance"])
    # the CHOOSE rule's Term is an Argmax over has_affordance-reached affordances of a
    # StringIndexOf-based overlap score, writing chosen_action — no host-hand-picked link.
    choose = next(r for r in g["rules"] if r["name"].startswith("choose_affordance"))
    assert choose["effects"][0][:3] == ["set_attr", "sess", "chosen_action"]
    term_str = str(choose["effects"][0][3])
    assert "Argmax" in term_str and "has_affordance" in term_str and "StringIndexOf" in term_str


# --- (d) end-to-end gate: instruction -> comprehension -> authored choice -> scan_and_browse -----

def test_browse_gate_end_to_end(adapter, local_site):
    """world_receive the instruction -> the agent's OWN comprehension mints the Goal -> drive the
    concern -> the agent authors + installs the choice rules -> mint_browse_request ->
    scan_and_browse (UNMODIFIED mechanism) -> the agent's rule chose the link affordances, reached
    the target within max_actions, and did NOT click randomly (discriminative control: a different
    goal chooses a different link)."""
    a = adapter
    S, I = a.s, a.inner

    ind_c = induce_concern(a, [["comprehend", "a", "DIRECTIVE"], ["find", "the", "TARGET"]],
                            name_hint="browse_find_directive")
    g_c = ground_concern(a, [ind_c["capability_key"]])
    assert g_c["grounded"] and g_c["form"] == "find_directive_rule"

    ind_m = induce_concern(a, [["match", "the", "AFFORDANCE", "to", "the", "GOAL"]],
                            name_hint="browse_choice_relevance")
    g_m = ground_concern(a, [ind_m["capability_key"]])
    assert g_m["grounded"] and g_m["form"] == "browse_rule"

    def run_one(topic: str):
        instruction = f"Find the page about {topic}."
        world_receive(a, instruction)
        I.run_rules()
        goal = next(g for g in S.nodes("Goal")
                    if S.node(g)["attrs"].get("kind") == "find"
                    and not S.node(g)["attrs"].get("_reported"))
        I.set_attr(goal, "_reported", 1.0)
        mint_browse_request(a, local_site + "index.html", purpose=instruction)
        scan_and_browse(a, max_actions=MAX_ACTIONS, headless=True)
        sessions = [n for n in S.nodes("WorldInstance")
                    if S.node(n)["attrs"].get("world_type") == "BrowserSession"]
        sess = sessions[-1]
        return S.node(sess)["attrs"], S.node(goal)["attrs"]

    sess_attrs, goal_attrs = run_one("volcanoes")
    assert sess_attrs["url"].endswith("volcanoes.html"), (
        "the agent's OWN rule chose the volcanoes link -- zero host choice of which affordance to act on")
    assert goal_attrs["status"] == "satisfied"
    assert 1 <= sess_attrs["actions_taken"] <= MAX_ACTIONS

    # discriminative control: a DIFFERENT goal must choose a DIFFERENTLY -- not luck/hardcoding.
    sess_attrs2, goal_attrs2 = run_one("deserts")
    assert sess_attrs2["url"].endswith("deserts.html")
    assert sess_attrs2["url"] != sess_attrs["url"]

    assert a._donkey["n"] == 0, "no LLM calls anywhere in the comprehend -> choose -> act loop"
