"""test_conceptualizer — PHASE 1 of the CONCEPTUALIZER: the formation-of-intent layer that
precedes the utterance (Levelt's conceptualizer->formulator; Searle's illocutionary force +
perlocutionary effect; Grice/Relevance; Clark's audience design). Fast pytest twin of
`scripts/jabberwock_forms_intent.py` (read that script's module docstring for the full
narrative).

THE MACHINERY (read-only here, never modified): `domains/audience_driven_production.py`
(`audience_model` / `residual_vs_audience` / `select_utterance`) stays exactly as the prior
audience-driven-production arc left it. `domains/conceptualizer.py` (new, marshal-only) wires
a communicative Goal to the held ForceCodebookHub and reads the jabberwock's own
composer-authored rules' output back out. `domains/reflective_faculty.py`'s
`_compose_conceptualize_rule` (new) is the composer builder — dispatched via
`induce_concern`/`ground_concern` the SAME way `_compose_communicate_rule` is, gated by TWO
new RelationCue/ComposerCue entries in `seeds/conceptualizer.json`.

Per CLAUDE.md's discipline, no test here hand-installs the `form_intent_<tag>` /
`request_message_shape_<tag>` rules — every test either (a) proves the concern genuinely
WALLS before `seeds/conceptualizer.json` is loaded, or (b) drives
`induce_concern`->`ground_concern` and reads back what the agent's own composer authored, or
(c) drives the full mint->tick->shape->tick pipeline on a real booted agent and reads the
graph state back."""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import boot_core                              # noqa: E402
from substrate.seed_loader import manifest_for                         # noqa: E402
import domains.reflective_faculty as rf                                # noqa: E402
import domains.conceptualizer as cc                                    # noqa: E402
import domains.audience_driven_production as adp                       # noqa: E402

LEXICON = [
    {"form": "a robot", "concept": "a_robot"},
    {"form": "curious", "concept": "curious"},
    {"form": "asks questions", "concept": "asks_questions"},
    {"form": "learns from mistakes", "concept": "learns_from_mistakes"},
]
MEANING = {"a_robot", "curious", "asks_questions", "learns_from_mistakes"}
SHARED = ["a_robot", "curious"]

FORM_CLAUSE = ["form", "INTENT", "before", "UTTERANCE"]
SHAPE_CLAUSE = ["shape", "MESSAGE", "by", "RESIDUAL"]


class _Agent:
    """Minimal duck-typed agent wrapper — identical shape to
    tests/test_audience_production_cognition.py's own `_Agent` (harness glue only, no source
    modified)."""
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


def _base_agent() -> _Agent:
    """A fresh agent with the dispatch machinery loaded but WITHOUT the conceptualizer seed —
    used by the wall-proof test."""
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    ag.s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag.agent)
    ag.s._inner.load_seed_manifest(manifest_for("composer_dispatch"), ag.agent)
    ag.s._inner.load_seed_manifest(manifest_for("autonomy"), ag.agent)
    return ag


def _fresh_agent() -> _Agent:
    """A fresh agent with the conceptualizer seed additionally loaded (ForceCodebook +
    the 'form'/'shape' RelationCue/ComposerCue vocabulary)."""
    ag = _base_agent()
    cc.ensure_conceptualizer_seed(ag)
    return ag


def _ground_conceptualizer(ag, tag="ci_t"):
    ind = rf.induce_concern(ag, [FORM_CLAUSE, SHAPE_CLAUSE], name_hint=tag)
    assert ind.get("minted") is True, ind
    g = rf.ground_concern(ag, [ind["capability_key"]])
    assert g.get("grounded") is True and g.get("served_by") == "python", g
    return g


# ===========================================================================
# 1. the vocabulary genuinely walls before this change (proof, not assumed)
# ===========================================================================
def test_wall_before_conceptualizer_seed():
    ag = _base_agent()
    ind = rf.induce_concern(ag, [FORM_CLAUSE, SHAPE_CLAUSE], name_hint="wall_probe")
    assert ind.get("minted") is True
    res = rf.ground_concern(ag, [ind["capability_key"]])
    assert res.get("grounded") is False
    assert res.get("path") == "predicate_grounding"


def test_form_shape_cues_load_and_dispatch_to_conceptualize_composer():
    ag = _fresh_agent()
    name = rf._pick_composer(ag.s, ag.inner, ag.agent, {"form", "shape"})
    assert name == "conceptualize"


# ===========================================================================
# 2. the jabberwock AUTHORS the two conceptualizer rules via the composer
# ===========================================================================
def test_agent_authors_two_conceptualizer_rules_via_graph_composer():
    ag = _fresh_agent()
    ind = rf.induce_concern(ag, [FORM_CLAUSE, SHAPE_CLAUSE], name_hint="ci_authors")
    key = ind["capability_key"]
    before = ag.inner.rule_count()
    g = rf.ground_concern(ag, [key])
    after = ag.inner.rule_count()

    assert g.get("grounded") is True, g.get("wall")
    assert g.get("served_by") == "python"
    assert g.get("path") == "compose_conceptualize_rule"
    assert after - before == 2, "exactly two rules authored"

    by_name = {r["name"]: r for r in g["rules"]}
    form_rule = by_name["form_intent_" + key]
    assert form_rule["match"] == [["g", "for_audience", "aud"], ["g", "wants_force", "hub"],
                                   ["hub", "has_template", "ft"]]
    assert form_rule["effects"][0][:3] == ["add_node", "intent", "CommunicativeIntent"]
    assert form_rule["effects"][1] == ["add_edge", "g", "forms_intent", "intent"]
    assert form_rule["effects"][2] == ["add_edge", "intent", "for_audience", "aud"]

    shape_rule = by_name["request_message_shape_" + key]
    assert shape_rule["match"] == [["g", "forms_intent", "intent"]]
    assert shape_rule["effects"][0][:3] == ["add_node", "req", "MessageShapeRequest"]
    assert shape_rule["effects"][1] == ["add_edge", "intent", "requests_shape", "req"]
    assert shape_rule["effects"][2] == ["add_edge", "req", "for_intent", "intent"]


def test_re_grounding_is_idempotent_no_rechurn():
    ag = _fresh_agent()
    ind = rf.induce_concern(ag, [FORM_CLAUSE, SHAPE_CLAUSE], name_hint="ci_idem")
    key = ind["capability_key"]
    rf.ground_concern(ag, [key])
    rc1 = ag.inner.rule_count()
    rf.ground_concern(ag, [key])
    rc2 = ag.inner.rule_count()
    assert rc1 == rc2


# ===========================================================================
# 3. FORMATION IS EXPLICIT — a communicative Goal + an audience -> a
#    CommunicativeIntent carrying an EXPLICIT force + perlocutionary_goal +
#    informative_content.
# ===========================================================================
def test_formation_is_explicit_graph_data():
    ag = _fresh_agent()
    _ground_conceptualizer(ag)
    g = cc.mint_communicative_goal(
        ag, "inform", MEANING, {"id": "visitor", "observed": True, "known_concepts": SHARED})
    ag.inner.run_rules(2000)

    intents = list(ag.s.nodes("CommunicativeIntent"))
    assert len(intents) == 1, "the intent is FORMED graph data, not implicit"
    read = cc.read_intent(ag, g)
    print("FORMED COMMUNICATIVE INTENT:", read)
    assert read["force"] == "assertive"
    assert read["perlocutionary_goal"] == "hearer_knows"
    assert sorted(read["informative_content"]) == sorted(MEANING)


def test_formation_force_varies_by_goal_kind():
    ag = _fresh_agent()
    _ground_conceptualizer(ag)
    g = cc.mint_communicative_goal(
        ag, "request", {"the_door_open"}, {"id": "visitor", "observed": False})
    ag.inner.run_rules(2000)
    read = cc.read_intent(ag, g)
    assert read["force"] == "directive"
    assert read["perlocutionary_goal"] == "hearer_does"


# ===========================================================================
# 4. MESSAGE SHAPE == RESIDUAL — pin the identity vs residual_vs_audience,
#    and the grounded/ungrounded contrast.
# ===========================================================================
def test_message_shape_focus_ground_equal_residual_vs_audience_identity():
    ag = _fresh_agent()
    _ground_conceptualizer(ag)
    g = cc.mint_communicative_goal(
        ag, "inform", MEANING, {"id": "visitor", "observed": True, "known_concepts": SHARED})
    ag.inner.run_rules(2000)
    results = cc.scan_and_conceptualize(ag, LEXICON)
    assert len(results) == 1
    residual = results[0]["residual"]
    ag.inner.run_rules(2000)

    read = cc.read_intent(ag, g)
    print("MESSAGE SHAPE:", {"focus": read["focus"], "ground": read["ground"]})
    assert read["focus"] == residual["new"]
    assert read["ground"] == residual["known"]


def test_grounded_audience_smaller_focus_ungrounded_audience_full_focus():
    ag_g = _fresh_agent()
    _ground_conceptualizer(ag_g, "ci_disc_g")
    g_g = cc.mint_communicative_goal(
        ag_g, "inform", MEANING, {"id": "spouse", "observed": True, "known_concepts": SHARED})
    ag_g.inner.run_rules(2000)
    cc.scan_and_conceptualize(ag_g, LEXICON)
    ag_g.inner.run_rules(2000)
    read_g = cc.read_intent(ag_g, g_g)

    ag_u = _fresh_agent()
    _ground_conceptualizer(ag_u, "ci_disc_u")
    g_u = cc.mint_communicative_goal(
        ag_u, "inform", MEANING, {"id": "stranger", "observed": False})
    ag_u.inner.run_rules(2000)
    cc.scan_and_conceptualize(ag_u, LEXICON)
    ag_u.inner.run_rules(2000)
    read_u = cc.read_intent(ag_u, g_u)

    print("GROUNDED focus:", read_g["focus"], "vs UNGROUNDED focus:", read_u["focus"])
    assert len(read_g["focus"]) < len(MEANING), "a grounded audience credits SOME concepts as ground"
    assert set(read_u["focus"]) == MEANING, "an ungrounded audience credits NOTHING — focus == full meaning"
    assert len(read_g["focus"]) < len(read_u["focus"])


def test_conceptualize_reply_entrypoint_returns_native_committed_result():
    """Exercise the public phase-3 entrypoint, not only its component steps."""
    ag = _fresh_agent()
    result = cc.conceptualize_reply(
        ag, "inform", MEANING,
        {"id": "visitor", "observed": True, "known_concepts": SHARED},
        LEXICON,
    )

    assert result["goal"] is not None
    assert result["intent"]["intent"] is not None
    assert result["intent"]["force"] == "assertive"
    assert sorted(result["intent"]["informative_content"]) == sorted(MEANING)
    assert result["committed"]["committed"] is not None
    assert result["committed"]["utterance"] == result["intent"]["utterance"]
    assert result["committed"]["grounded_used"] is True


# ===========================================================================
# 5. AUDIENCE-DESIGNED FORMULATION — the formulated utterance differs by
#    audience via select_utterance (verbatim contrast).
# ===========================================================================
def test_audience_designed_formulation_grounded_terser_ungrounded_explicit():
    ag_g = _fresh_agent()
    _ground_conceptualizer(ag_g, "ci_form_g")
    g_g = cc.mint_communicative_goal(
        ag_g, "inform", MEANING, {"id": "spouse", "observed": True, "known_concepts": SHARED})
    ag_g.inner.run_rules(2000)
    cc.scan_and_conceptualize(ag_g, LEXICON)
    ag_g.inner.run_rules(2000)
    read_g = cc.read_intent(ag_g, g_g)

    ag_u = _fresh_agent()
    _ground_conceptualizer(ag_u, "ci_form_u")
    g_u = cc.mint_communicative_goal(
        ag_u, "inform", MEANING, {"id": "stranger", "observed": False})
    ag_u.inner.run_rules(2000)
    cc.scan_and_conceptualize(ag_u, LEXICON)
    ag_u.inner.run_rules(2000)
    read_u = cc.read_intent(ag_u, g_u)

    print("GROUNDED utterance:", repr(read_g["utterance"]))
    print("UNGROUNDED utterance:", repr(read_u["utterance"]))
    assert read_g["grounded_used"] is True
    assert read_u["grounded_used"] is False
    assert read_g["utterance"] != read_u["utterance"]
    assert len(read_g["utterance"].split()) < len(read_u["utterance"].split())
    # the tailored (grounded) utterance never restates a shared (known) concept's surface form
    assert "a robot" not in read_g["utterance"]
    assert "curious" not in read_g["utterance"]
    # the ungrounded explicit fallback restates the FULL meaning
    for w in ("a robot", "curious", "asks questions", "learns from mistakes"):
        assert w in read_u["utterance"]


# ===========================================================================
# 6. NO PYTHON DECISION — source audit.
# ===========================================================================
_ALLOWED_IF_PATTERNS = [
    re.compile(r"if native is None:"),
    re.compile(r"if ag_node is None:"),
    re.compile(r"if not sub\.node\(n\)\[.attrs.\]\.get\(.is_class.\):"),
    re.compile(r"if sub\.node\(n\)\[.attrs.\]\.get\(.id.\) == _SEED_ID:"),
    re.compile(r"if hub is not None:"),
    re.compile(r"if ag_node is not None:"),
    re.compile(r"if at\.get\(.status.\) != .requested.:"),
    re.compile(r"if intent is None:"),
    re.compile(r"if bundle\[.system_model.\] is not None:"),
    re.compile(r"if shape_node is not None else"),
    re.compile(r"if intent_node is None:"),
    # Native worklist scheduling from the monitor extension is mechanical.
    re.compile(r"if shaped:"),
    re.compile(r"if native_work_pending:"),
    # Worklist exhaustion only bounds redundant native passes; production/commit
    # outcomes remain exclusively rule-authored.
    re.compile(r"if not shaped and not monitored:"),
    re.compile(r"if __name__"),
]


def test_no_python_decision_source_audit():
    """Grep `domains/conceptualizer.py`: every `if` present is mechanical bookkeeping
    (None-guards, a re-scan idempotency skip, a TypeError fallback) — never a decision that
    picks force / perlocutionary_goal / focus / ground from graph state. Those come from
    `form_intent_<tag>` (an Eq-join over the held ForceCodebookHub) and
    `audience_driven_production.residual_vs_audience`/`select_utterance` (already-approved,
    read-only, reused machinery), never from a new Python conditional in this module."""
    path = os.path.join(ROOT, "domains", "conceptualizer.py")
    with open(path) as f:
        lines = f.readlines()
    offending = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not (stripped.startswith("if ") or stripped == "if native is None:"
                or re.match(r"^\s*if\b", line) and stripped.startswith("if")):
            continue
        if not re.match(r"^\s*if\b.*:$", line.rstrip()):
            continue
        # try/except TypeError fallback line ("except TypeError:") is not an "if" — skip here.
        if any(p.search(stripped) for p in _ALLOWED_IF_PATTERNS):
            continue
        offending.append((i, stripped))
    assert offending == [], f"unexpected conditional(s) in conceptualizer.py: {offending}"
    # also: no forbidden decision keywords anywhere in the file (force/perlocutionary/focus
    # are only ever READ from `iat`/`sat`/`residual`/`res` dicts, never assigned by branch).
    text = "".join(lines)
    assert "elif" not in text
    assert re.search(r'"force"\s*:\s*"', text) is None, "force must never be a Python literal"
    assert re.search(r'"perlocutionary_goal"\s*:\s*"', text) is None


def test_conceptualizer_never_imports_python_rule_engine():
    path = os.path.join(ROOT, "domains", "conceptualizer.py")
    with open(path) as f:
        text = f.read()
    for forbidden in ("graph_rewrite", "gr.make_rule", "gr.run", "gr._match", "gr._apply"):
        assert forbidden not in text
