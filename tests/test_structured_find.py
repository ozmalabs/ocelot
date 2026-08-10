"""test_structured_find — the JABBERWOCK AUTHORS a STRUCTURED "find X near Y" comprehension.

commit c0288920 named the residual: `_compose_comprehension_rule`'s find-branch (domains/
reflective_faculty.py) used a small CLOSED STOPWORD LIST to decide what a "find X" directive
wants — fine for a single-target directive, but a MULTI-CONSTRAINT one ("find the page about
volcanoes near the diagram") needs the full POS/gap grammar to tell the TARGET ("volcanoes",
the thing named) from the CONSTRAINT ("diagram", where/what it must be near) instead of
flattening both into one undifferentiated word bag.

This test drives the SAME self-build composer (induce_concern -> ground_concern) one register
further: a NEW `constrain_target_directive` RelationCue (seeds/relation_vocabulary.json) grounds
a "constrain" relation head alongside "find"/"comprehend"; `_compose_comprehension_rule`'s
STRUCTURED branch (gated on BOTH being grounded) authors POS-DRIVEN rules — reading `pos`/
`role`/`gov_prep` attrs the mechanical ingest boundary (`domains/browse_dispatch.ingest_
directive`) already stamped on each Mention via the agent's OWN POS faculty
(`construction_grammar.parse_directive_elements`, the SAME classifier the gap-as-part-of-speech
comprehension path uses) — instead of a stopword list. `_compose_browse_rule`'s STRUCTURED twin
then requires BOTH target and constraint content visible before marking the goal satisfied, and
uses constraint words as SECONDARY (weighted) choice evidence.

Site fixture: an index with two links about the same headline topic ("volcanoes") — a DECOY page
that mentions the target but NOT the constraint, and a CORRECT page that mentions BOTH. donkey=0
throughout.
"""
from __future__ import annotations

import http.server
import threading

import pytest

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import induce_concern, ground_concern
from domains.browse_dispatch import mint_browse_request, scan_and_browse, ingest_directive
from domains import construction_grammar as cg

MAX_ACTIONS = 8

INDEX_HTML = """<!doctype html>
<html><head><title>Nature Index</title></head>
<body>
<h1>Welcome to the Nature Index</h1>
<p>This is a small site about natural landforms and features, for testing.</p>
<nav>
<a href="decoy.html">Learn about volcanoes</a>
<a href="correct.html">Volcanoes diagram guide</a>
<a href="mountains.html">Learn about mountains</a>
</nav>
</body></html>"""

# DECOY: mentions the TARGET ("volcanoes") but NOT the constraint ("diagram").
DECOY_HTML = ("<!doctype html><html><head><title>Volcanoes</title></head><body>"
              "<h1>Volcanoes</h1><p>Volcanoes are dramatic landforms formed by erupting magma.</p>"
              "</body></html>")
# CORRECT: mentions BOTH the target ("volcanoes") AND the constraint ("diagram").
CORRECT_HTML = ("<!doctype html><html><head><title>Volcano Diagram</title></head><body>"
                "<h1>Volcano Diagram</h1><p>This diagram explains how volcanoes erupt, "
                "showing the magma chamber below.</p></body></html>")
MOUNTAINS_HTML = ("<!doctype html><html><head><title>Mountains</title></head><body>"
                   "<h1>Mountains</h1><p>Mountains are large landforms that rise above the "
                   "surrounding terrain.</p></body></html>")

DIRECTIVE = "Find the page about volcanoes near the diagram."


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
    (tmp_path / "decoy.html").write_text(DECOY_HTML)
    (tmp_path / "correct.html").write_text(CORRECT_HTML)
    (tmp_path / "mountains.html").write_text(MOUNTAINS_HTML)

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


def _induce_structured_comprehension(a, name_hint="browse_find_constrained_directive"):
    # NOTE: induce_concern itself (first call on a fresh agent) lazily installs the
    # shape_decode_loop seed's OWN rules (a one-time cost, unrelated to ground_concern's
    # composed rules below) — kept OUTSIDE any rule_count() measurement window, mirroring
    # tests/test_browse_authoring.py's induce-then-measure-ground split.
    ind = induce_concern(a, [["comprehend", "a", "DIRECTIVE"], ["find", "the", "TARGET"],
                              ["constrain", "near", "CONSTRAINT"]], name_hint=name_hint)
    assert ind.get("minted") is True
    return ind


def _ground_structured_comprehension(a, name_hint="browse_find_constrained_directive"):
    ind = _induce_structured_comprehension(a, name_hint)
    g = ground_concern(a, [ind["capability_key"]])
    assert g.get("grounded") is True
    assert g.get("path") == "compose_comprehension_rule"
    assert g.get("form") == "find_directive_structured_rule"
    return g


def _induce_structured_browse(a, name_hint="browse_choice_relevance_constrained"):
    ind = induce_concern(a, [["match", "the", "AFFORDANCE", "to", "the", "GOAL"],
                              ["constrain", "near", "CONSTRAINT"]], name_hint=name_hint)
    assert ind.get("minted") is True
    return ind


def _ground_structured_browse(a, name_hint="browse_choice_relevance_constrained"):
    ind = _induce_structured_browse(a, name_hint)
    g = ground_concern(a, [ind["capability_key"]])
    assert g.get("grounded") is True
    assert g.get("path") == "compose_browse_rule"
    assert g.get("form") == "browse_structured_rule"
    return g


# --- (0) MECHANICAL POS-AT-THE-BOUNDARY: parse_directive_elements types the directive ----------

def test_pos_and_governance_stamped_on_directive():
    """The reused POS faculty (construction_grammar.parse_directive_elements -> parse_with_gaps'
    _pos_token) types every token of the directive + stamps the GOVERNANCE walk's `gov_prep` on
    each content noun: 'page' is a bare direct object (gov_prep None), 'volcanoes' is governed by
    'about' (a target-describing preposition), 'diagram' is governed by 'near' (the constraint)."""
    els = cg.parse_directive_elements(DIRECTIVE)
    by_surface = {e["surface"].strip(".,?!;:").lower(): e for e in els
                  if e["role"] == "content" and e["pos"] == "noun"}
    assert by_surface["page"].get("gov_prep") is None
    assert by_surface["volcanoes"].get("gov_prep") == "about"
    assert by_surface["diagram"].get("gov_prep") == "near"
    # 'near' itself types as a PREPOSITION (function word), not a stray content word — the
    # `_pos_token` ordering fix this task made (function_word_reference's role-bearing preposition
    # reading now wins over Wiktionary's ambiguous dominant sense for 'near').
    near_el = next(e for e in els if e["surface"].lower() == "near")
    assert near_el["role"] == "function" and near_el["pos"] == "preposition"


# --- (1) DISCRIMINATIVE CONTRAST: the OLD flat/stopword parse mis-binds this directive ----------

def test_old_stopword_parse_mis_binds_the_constraint():
    """Pin the residual named in c0288920: ground the PLAIN 'find X' concern (no 'constrain'
    relation grounded) on a throwaway agent and show its stopword-based bind_find_target rule
    flattens BOTH the target ('volcanoes') and the constraint ('diagram') into one undifferentiated
    'wants' bag — and even lets the preposition 'near' itself through (not in its closed stoplist)
    — the exact mis-bind a multi-constraint directive exposes."""
    probe = WorldAdapter(seeds=())
    load_all_seeds(probe)
    ind = induce_concern(probe, [["comprehend", "a", "DIRECTIVE"], ["find", "the", "TARGET"]],
                          name_hint="old_flat_find_directive")
    g = ground_concern(probe, [ind["capability_key"]])
    assert g.get("grounded") is True and g.get("form") == "find_directive_rule"  # the OLD branch

    msg = ingest_directive(probe, DIRECTIVE)
    probe.inner.run_rules()
    goals = [n for n in probe.s.nodes("Goal") if probe.s.node(n)["attrs"].get("kind") == "find"]
    assert len(goals) == 1
    wants = sorted(probe.s.node(w)["attrs"].get("text") for w in probe.inner.neighbours(goals[0], "wants"))
    # the mis-bind: 'near' (a function word, not content) AND 'diagram' (the CONSTRAINT, not the
    # target) both land in the SAME flat 'wants' set as 'volcanoes' (the real target) — no
    # target/constraint distinction is possible downstream from this bag.
    assert wants == ["diagram", "near", "volcanoes"]
    assert not probe.inner.neighbours(goals[0], "constrained_by")  # the old branch has no such edge kind


# --- (2) the NEW structured comprehension separates target from constraint ---------------------

def test_structured_comprehension_separates_target_and_constraint(adapter):
    a = adapter
    ind = _induce_structured_comprehension(a)
    before = a.inner.rule_count()
    g = ground_concern(a, [ind["capability_key"]])
    after = a.inner.rule_count()
    assert g.get("grounded") is True
    assert g.get("path") == "compose_comprehension_rule"
    assert g.get("form") == "find_directive_structured_rule"
    assert after - before == 3
    names = sorted(r["name"] for r in g["rules"])
    assert names == sorted([
        "comprehend_find_directive_structured_browse_find_constrained_directive",
        "bind_find_target_structured_browse_find_constrained_directive",
        "bind_find_constraint_structured_browse_find_constrained_directive"])

    ingest_directive(a, DIRECTIVE)
    a.inner.run_rules()
    goals = [n for n in a.s.nodes("Goal") if a.s.node(n)["attrs"].get("kind") == "find"]
    assert len(goals) == 1
    wants = sorted(a.s.node(w)["attrs"].get("text") for w in a.inner.neighbours(goals[0], "wants"))
    constrained = sorted(a.s.node(w)["attrs"].get("text") for w in a.inner.neighbours(goals[0], "constrained_by"))
    assert wants == ["page", "volcanoes"]        # target: the direct object + the 'about'-governed noun
    assert constrained == ["diagram"]            # constraint: the 'near'-governed noun, alone
    assert "near" not in wants and "near" not in constrained  # the preposition itself is not content


# --- (3) the NEW browse composer authors weighted-choice + both-required-stop rules -------------

def test_structured_browse_rules_authored(adapter):
    a = adapter
    ind = _induce_structured_browse(a)
    before = a.inner.rule_count()
    g = ground_concern(a, [ind["capability_key"]])
    after = a.inner.rule_count()
    assert g.get("grounded") is True
    assert g.get("path") == "compose_browse_rule"
    assert g.get("form") == "browse_structured_rule"
    assert after - before == 2
    names = sorted(r["name"] for r in g["rules"])
    assert names == sorted(["choose_affordance_structured_browse_choice_relevance_constrained",
                             "browse_goal_satisfied_structured_browse_choice_relevance_constrained"])
    choose = next(r for r in g["rules"] if r["name"].startswith("choose_affordance_structured"))
    term_str = str(choose["effects"][0][3])
    assert "Argmax" in term_str and "constrained_by" in term_str and "Times" in term_str
    stop = next(r for r in g["rules"] if r["name"].startswith("browse_goal_satisfied_structured"))
    # the stop rule's match/where reference BOTH `wants` (target) and `constrained_by` — requires
    # both to be visible, not just the target.
    assert "constrained_by" in str(stop["where"]) or any(
        "constrained_by" in str(m) for m in stop["match"])


# --- (4) end-to-end gate: constrained navigation reaches the CORRECT page, not the DECOY --------

def test_structured_find_gate_end_to_end(adapter, local_site):
    a = adapter
    S, I = a.s, a.inner

    g_c = _ground_structured_comprehension(a)
    assert g_c["form"] == "find_directive_structured_rule"
    g_m = _ground_structured_browse(a)
    assert g_m["form"] == "browse_structured_rule"

    ingest_directive(a, DIRECTIVE)
    I.run_rules()
    goal = next(g for g in S.nodes("Goal") if S.node(g)["attrs"].get("kind") == "find")
    wants = sorted(S.node(w)["attrs"].get("text") for w in I.neighbours(goal, "wants"))
    constrained = sorted(S.node(w)["attrs"].get("text") for w in I.neighbours(goal, "constrained_by"))
    print(f"\n  PARSE: wants(target)={wants} constrained_by={constrained}")

    mint_browse_request(a, local_site + "index.html", purpose=DIRECTIVE)
    scan_and_browse(a, max_actions=MAX_ACTIONS, headless=True)

    sessions = [n for n in S.nodes("WorldInstance") if S.node(n)["attrs"].get("world_type") == "BrowserSession"]
    sess = sessions[-1]
    sess_attrs = S.node(sess)["attrs"]
    print(f"  RESULT: url={sess_attrs.get('url')!r} actions_taken={sess_attrs.get('actions_taken')}")

    assert sess_attrs["url"].endswith("correct.html"), (
        "the agent's OWN structured rule must reach the page that satisfies BOTH the target AND "
        "the constraint, not the decoy that only mentions the target")
    assert not sess_attrs["url"].endswith("decoy.html")
    assert S.node(goal)["attrs"]["status"] == "satisfied"
    assert 1 <= sess_attrs["actions_taken"] <= MAX_ACTIONS
    assert a._donkey["n"] == 0, "no LLM calls anywhere in the comprehend -> choose -> act loop"
