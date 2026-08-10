"""test_composers_graph — the composer/authoring-machinery migration GATE.

Per CLAUDE.md: "self-improvement over ALL parts requires the agent's
AUTHORING MACHINERY itself to be graph data it can inspect and vary." The
pilot (seeds/composer_comprehension_graph.json, tests/test_composer_graph_
pilot.py) proved the SHAPE for one composer/branch (comprehension's
'describe'). This file gates the follow-on migration of the remaining
composers/branches to graph-resident meta-rules
(seeds/composer_<name>_graph.json) — each a Rule NODE that mints the SAME
rules `domains/reflective_faculty.py`'s `_compose_*_rule` Python functions
author, but as graph data the agent can dump/inspect/EDIT (see the
edit_ops demonstration at the bottom), not Python source it cannot see.

Migrated (this file's SECTION order matches the migration table the
companion driver script `scripts/jabberwock_composers_in_graph.py` prints):
  control, grouping, decision, construction, distributional, attention,
  browse (plain + constrained), comprehension (find + find+constrain --
  'describe' was the pilot), communicate (the full source+decompose+
  communicate combo).

FULLY migrated: `experiment` (seeds/composer_experiment_graph.json, tests/
test_experiment_composer_graph.py has the full account). The dialect gap
this docstring used to describe (compose-time `native.evaluate()` of an
Argmax over RuleSummary/SeedSummary provenance, and dynamic JSON-string
construction of a sub-rule embedded as a SeedDelta attr string) was closed
by 4 new Terms (`ToJsonString`/`FromJsonString`/`ShiftThresholdLits`/
`DictGet`, see tests/test_dialect_experiment_terms.py) plus 2 more
(`RewriteTreeNodes`/`ListDrop`, see tests/test_editop_dialect_terms.py) that
closed the STRUCTURAL-EDIT family, and `AttrKeyRanking` (term.rs) closed the
last EditOp residual (`swap_term_leaf`'s SITE — the two most-referenced Attr
keys, by frequency). `_route_experiment_composer` in domains/reflective_
faculty.py now serves EVERY grounded-relation combination that authors
anything from the graph: judge alone, adopt alone, and the FULL 'test'-
anchored family via ONE parametric meta-rule (`compose_experiment_mint_
parametric` — REPLACES the five former exact-combo meta-rules: mint_graph/
full_graph/vary_graph/embed_graph/structure_graph, retired), driven by
has_send/has_vary/has_judge/has_gradient/has_structure/has_embed flags on
the triggering ComposeRequest rather than one meta-rule per exact
relation-set. The ONLY genuine WALLS (both paths author nothing) are
no-'test' combos with NEITHER judge NOR adopt grounded ({vary}, {send},
{vary, send}, ...) — the router honestly declines (returns None) so
`ground_concern` falls through to `_compose_experiment_rule`'s own
`grounded: False` wall, unchanged. NOT a time-boxing shortcut: no combo
that authors an experiment rule is left on Python any more.

Every test here drives EITHER the graph seed directly (mechanical I/O:
install seed, mint a ComposeRequest trigger, tick) or the REAL production
seam (`induce_concern` -> `ground_concern`, which now tries the graph path
FIRST via `reflective_faculty._try_graph_composer` and returns `served_by`
in {"graph","python"} — the migration LEDGER) — never a hand-authored rule,
never a Python reimplementation of what the meta-rule composes.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
import domains.reflective_faculty as rf
from domains import self_model as sm
from domains import edit_ops

SEED_DIR = os.path.join(ROOT, "seeds")


# ---------------------------------------------------------------------------
# shared harness helpers — mechanical graph I/O, no agent decisions.
# ---------------------------------------------------------------------------
def _fresh():
    return WorldAdapter(seeds=())


def _load_seed(a, filename_stem):
    path = os.path.join(SEED_DIR, f"{filename_stem}.json")
    a.s.load_seed_manifest(json.load(open(path)), a.agent)


def _mk_cr(a, edge, **attrs):
    attrs.setdefault("composed", 0.0)
    cr = a.s.add_node("ComposeRequest", attrs)
    a.inner.add_edge_unchecked(a.agent, edge, cr)
    return cr


def _tick(a, n=8):
    for _ in range(n):
        a.s.tick()


def _rule_names_live(a):
    return sorted(r.get("name") for r in a.inner.export_rules() if isinstance(r, dict))


def _by_name(rules):
    return {r["name"]: r for r in rules}


def _norm_effects(effects):
    """Pad a bare 4-element `["add_edge", src, edge_type, tgt]` (the shape
    the Python builders' own dict literals author when an edge carries no
    attrs) to the 5-element `[..., {}]` `export_rules()` always emits (the
    Rust round-trip makes the trailing attrs dict explicit even when empty)
    — an engine-normalization detail, not authored content."""
    out = []
    for e in (effects or []):
        if isinstance(e, list) and len(e) == 4 and e[0] == "add_edge":
            out.append(e + [{}])
        else:
            out.append(e)
    return out


def _unwrap_tuple_markers(node):
    """The PyO3 bridge preserves Python list-vs-tuple across the Rust FFI
    boundary via a `{"__tuple__": [...]}` wrapper (seen on ANY value that
    made a round trip through `Value::Tuple`, e.g. a `Lit` literal list
    embedded in a graph-resident rule's `where`/`effect`) — a Rust-side
    `Value::Tuple` that never left Python (the un-migrated builders' own
    returned dicts) stays a plain `list`. Recursively unwrap for structural
    comparison: both represent the SAME authored literal list."""
    if isinstance(node, dict):
        if set(node.keys()) == {"__tuple__"}:
            return [_unwrap_tuple_markers(v) for v in node["__tuple__"]]
        return {k: _unwrap_tuple_markers(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_unwrap_tuple_markers(v) for v in node]
    return node


def _norm(rule_dict):
    """Restrict to the AUTHORED content (name/match/where/effects) — the
    same 'modulo name suffixes / modulo engine bookkeeping' comparison the
    task calls for: `export_rules()` round-trips add `batch`/`match_type`
    defaults, an explicit trailing `{}` on an attrs-less `add_edge`, and a
    `{"__tuple__": [...]}` wrapper on any literal list — none of which the
    Python builders' own literal dicts carry. `match` is also compared as a
    SORTED set of edges (independent match-edge order is not authored
    content — `_compose_browse_rule`'s structured STOP rule's two
    `sess -contains-> el/el2` edges are interchangeable)."""
    d = {k: rule_dict.get(k) for k in ("name", "match", "where", "effects")}
    d["effects"] = _norm_effects(d["effects"])
    d = _unwrap_tuple_markers(d)
    if isinstance(d.get("match"), list):
        d["match"] = sorted(tuple(e) for e in d["match"])
    return json.loads(json.dumps(d, default=str))


# ---------------------------------------------------------------------------
# SECTION 1 — per-composer: mint + STRUCTURAL EQUIVALENCE vs the Python
# reference builder for the SAME (keys, rels) input.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("composer,keys,rels,rp", [
    ("control", ["eq1"], [("control", "X", "Y")], {"control"}),
    ("grouping", ["eq2"], [("group", "X", "Y")], {"group"}),
    ("decision", ["eq3"], [("utility", "X", "Y")], {"utility"}),
    ("construction", ["eq4"], [("construct", "X", "Y")], {"construct"}),
    ("distributional", ["eq5"], [("distribute", "X", "Y")], {"distribute"}),
    ("attention", ["eq6"], [("watch", "X", "Y")], {"watch"}),
])
def test_structural_equivalence_single_and_multi_rule_composers(composer, keys, rels, rp):
    builder = rf._COMPOSER_REGISTRY[composer]
    py_agent = _fresh()
    py_res = builder(py_agent, keys, rels)
    assert py_res.get("grounded") is True

    gr_agent = _fresh()
    gr_res = rf._try_graph_composer(gr_agent, composer, keys, rels, rp)
    assert gr_res is not None, f"{composer}: graph path produced no result"
    assert gr_res.get("grounded") is True
    assert gr_res.get("served_by") == "graph"
    assert gr_res.get("path") == py_res.get("path")
    assert gr_res.get("form") == py_res.get("form")

    py_rules = py_res["rules"] if "rules" in py_res else [py_res["rule"]]
    gr_rules = gr_res["rules"] if "rules" in gr_res else [gr_res["rule"]]
    py_by_name, gr_by_name = _by_name(py_rules), _by_name(gr_rules)
    assert sorted(py_by_name) == sorted(gr_by_name)
    for name in py_by_name:
        assert _norm(py_by_name[name]) == _norm(gr_by_name[name]), name


def test_structural_equivalence_browse_plain():
    keys, rels, rp = ["eqb1"], [("match", "X", "Y")], {"match"}
    py_res = rf._compose_browse_rule(_fresh(), keys, rels)
    gr_res = rf._try_graph_composer(_fresh(), "browse", keys, rels, rp)
    assert gr_res is not None and gr_res["served_by"] == "graph"
    assert py_res["form"] == gr_res["form"] == "browse_rule"
    for name in _by_name(py_res["rules"]):
        assert _norm(_by_name(py_res["rules"])[name]) == _norm(_by_name(gr_res["rules"])[name])


def test_structural_equivalence_browse_constrained():
    keys, rels, rp = ["eqb2"], [("match", "X", "Y"), ("constrain", "near", "Z")], {"match", "constrain"}
    py_res = rf._compose_browse_rule(_fresh(), keys, rels)
    gr_res = rf._try_graph_composer(_fresh(), "browse", keys, rels, rp)
    assert gr_res is not None and gr_res["served_by"] == "graph"
    assert py_res["form"] == gr_res["form"] == "browse_structured_rule"
    for name in _by_name(py_res["rules"]):
        assert _norm(_by_name(py_res["rules"])[name]) == _norm(_by_name(gr_res["rules"])[name])


def test_structural_equivalence_comprehension_find():
    keys = ["eqc1"]
    rels = [("comprehend", "X"), ("find", "Y")]
    rp = {"comprehend", "find"}
    py_res = rf._compose_comprehension_rule(_fresh(), keys, rels)
    gr_res = rf._try_graph_composer(_fresh(), "comprehension", keys, rels, rp)
    assert gr_res is not None and gr_res["served_by"] == "graph"
    assert py_res["form"] == gr_res["form"] == "find_directive_rule"
    for name in _by_name(py_res["rules"]):
        assert _norm(_by_name(py_res["rules"])[name]) == _norm(_by_name(gr_res["rules"])[name])


def test_structural_equivalence_comprehension_find_constrained():
    keys = ["eqc2"]
    rels = [("comprehend", "X"), ("find", "Y"), ("constrain", "Z")]
    rp = {"comprehend", "find", "constrain"}
    py_res = rf._compose_comprehension_rule(_fresh(), keys, rels)
    gr_res = rf._try_graph_composer(_fresh(), "comprehension", keys, rels, rp)
    assert gr_res is not None and gr_res["served_by"] == "graph"
    assert py_res["form"] == gr_res["form"] == "find_directive_structured_rule"
    for name in _by_name(py_res["rules"]):
        assert _norm(_by_name(py_res["rules"])[name]) == _norm(_by_name(gr_res["rules"])[name])


def test_structural_equivalence_comprehension_describe():
    """The pilot's own describe branch, now ALSO reachable via
    `_try_graph_composer` (routed through the pilot seed) — confirms the
    NEW routing layer reproduces the OLD pilot's proven shape exactly."""
    keys = ["eqc3"]
    rels = [("comprehend", "X")]
    rp = {"comprehend"}
    py_res = rf._compose_comprehension_rule(_fresh(), keys, rels)
    gr_res = rf._try_graph_composer(_fresh(), "comprehension", keys, rels, rp)
    assert gr_res is not None and gr_res["served_by"] == "graph"
    assert py_res["form"] == gr_res["form"] == "comprehension_rule"
    assert _norm(py_res["rule"]) == _norm(gr_res["rule"])


def test_structural_equivalence_communicate_full_combo():
    keys = ["eqcm1"]
    rels = [("source", "X"), ("decompose", "Y"), ("communicate", "Z")]
    rp = {"source", "decompose", "communicate"}
    py_res = rf._compose_communicate_rule(_fresh(), keys, rels)
    gr_res = rf._try_graph_composer(_fresh(), "communicate", keys, rels, rp)
    assert gr_res is not None and gr_res["served_by"] == "graph"
    assert py_res["form"] == gr_res["form"] == "communicate_rule"
    assert _norm(py_res["rule"]) == _norm(gr_res["rule"])


def test_communicate_partial_combo_not_migrated_falls_through():
    """Documents the scope cut honestly: only the FULL source+decompose+
    communicate combo is migrated. Any other combo returns None from the
    graph router (an honest miss), so `ground_concern` falls back to
    Python — verified here at the router level directly."""
    keys, rels, rp = ["eqcm2"], [("decompose", "Y")], {"decompose"}
    assert rf._try_graph_composer(_fresh(), "communicate", keys, rels, rp) is None


def test_experiment_unmigrated_combos_router_declines():
    """`experiment` is now FULLY migrated for every combo that authors
    anything (see this file's module docstring + tests/
    test_experiment_composer_graph.py): `compose_experiment_mint_parametric`
    mints for ANY 'test'-anchored grounded-relation combination, driven by
    boolean flags, not just a fixed exact-combo set. The ONLY genuine walls
    left are no-'test' combos with NEITHER judge NOR adopt grounded (Python
    authors nothing for them either — see `_compose_experiment_rule`'s own
    'grounded: False' wall)."""
    for rp in ({"vary"}, {"send"}, {"vary", "send"}):
        assert rf._try_graph_composer(_fresh(), "experiment", ["x"], [(h, "Y") for h in rp], rp) is None


def test_experiment_migrated_combos_router_serves_graph():
    """The combos composer_experiment_graph.json mints for must be served
    by the graph path — the positive twin of the decline test above.
    Includes the combos THIS commit closed (previously fell to Python: no
    exact per-combo meta-rule minted them) -- test+send+judge+gradient
    without 'adopt', and a bare test+judge partial mix -- proving the
    parametric mint rule, not just the 5 former hard-coded exact combos,
    now serves the router. ('structure'/'gradient' Argmax picks need
    grid_navigation loaded for RuleSummary/EditOp provenance -- see
    tests/test_experiment_composer_graph.py for that combo's own coverage,
    not duplicated here.)"""
    for rp, expected_names in (
        ({"judge"}, {"judge_experiment_outcome_x"}),
        ({"adopt"}, {"mark_adopt_ready_x"}),
        ({"test"}, {"author_experiment_from_residual_x"}),
        ({"test", "judge"}, {"author_experiment_from_residual_x", "judge_experiment_outcome_x"}),
        ({"test", "vary", "send", "judge"},
         {"author_experiment_from_residual_x", "judge_experiment_outcome_x"}),
        ({"test", "vary", "send", "judge", "embed"},
         {"author_experiment_from_residual_x", "judge_experiment_outcome_x"}),
        ({"test", "send", "judge", "gradient"},          # THE RESIDUAL THIS COMMIT CLOSES (no 'adopt')
         {"author_experiment_from_residual_x", "judge_experiment_outcome_x"}),
    ):
        res = rf._try_graph_composer(_fresh(), "experiment", ["x"], [(h, "Y") for h in rp], rp)
        assert res is not None, rp
        assert res.get("served_by") == "graph"
        assert res.get("path") == "compose_experiment_rule"
        names = {r["name"] for r in res.get("rules", [])}
        assert names == expected_names, (rp, names)


# ---------------------------------------------------------------------------
# SECTION 2 — behavioral: the minted rules actually work end-to-end.
# ---------------------------------------------------------------------------
def test_behavioral_control():
    a = _fresh(); _load_seed(a, "composer_control_graph")
    _mk_cr(a, "wants_control_rule", tag="beh_control")
    _tick(a)
    game = a.s.add_node("Game", {})
    f = a.s.add_node("Feature", {"cy": 5.0, "cx": 5.0})
    a.inner.add_edge_unchecked(game, "has_feature", f)
    cand = a.s.add_node("Candidate", {"is_avatar": 1.0, "cy": 5.0, "cx": 5.0})
    a.inner.add_edge_unchecked(game, "has_candidate", cand)
    a.inner.run_rules()
    assert a.s.node(f)["attrs"].get("responds_to_my_action") is True
    assert a.s.node(f)["attrs"].get("selective") is True


def test_behavioral_grouping():
    a = _fresh(); _load_seed(a, "composer_grouping_graph")
    _mk_cr(a, "wants_grouping_rule", tag="beh_grouping")
    _tick(a)
    game = a.s.add_node("Game", {})
    f = a.s.add_node("Feature", {"responds_to_my_action": True})
    a.inner.add_edge_unchecked(game, "has_feature", f)
    reg = a.s.add_node("Region", {})
    a.inner.add_edge_unchecked(reg, "realises", f)
    cell = a.s.add_node("Cell", {})
    a.inner.add_edge_unchecked(cell, "within", reg)
    a.inner.run_rules()
    objs = a.s.nodes(type="Object")
    assert len(objs) == 1
    assert a.s.node(objs[0])["attrs"].get("is_body") == 1.0
    assert objs[0] in list(a.inner.neighbours(cell, "within"))


def test_behavioral_decision():
    a = _fresh(); _load_seed(a, "composer_decision_graph")
    _mk_cr(a, "wants_decision_rule", tag="beh_decision")
    _tick(a)
    game = a.s.add_node("Game", {})
    goal = a.s.add_node("Goal", {"cy": 0.0, "cx": 0.0})
    a.inner.add_edge_unchecked(game, "has_goal", goal)
    c = a.s.add_node("Cand", {"cy": 5.0, "cx": 5.0})
    a.inner.add_edge_unchecked(game, "avatar_candidate", c)
    up = a.s.add_node("Aff", {"name": "up", "drow": -1.0, "dcol": 0.0})
    down = a.s.add_node("Aff", {"name": "down", "drow": 1.0, "dcol": 0.0})
    a.inner.add_edge_unchecked(game, "affordance", up)
    a.inner.add_edge_unchecked(game, "affordance", down)
    a.inner.run_rules()
    assert a.s.node(game)["attrs"].get("chosen_action") == "up"


def test_behavioral_construction():
    a = _fresh(); _load_seed(a, "composer_construction_graph")
    _mk_cr(a, "wants_construction_rule", tag="beh_construction")
    _tick(a)
    f = a.s.add_node("Tok", {"is_function": 1.0})
    c = a.s.add_node("Tok", {"is_content": 1.0})
    a.inner.add_edge_unchecked(f, "precedes", c)
    a.inner.run_rules()
    assert a.s.node(c)["attrs"].get("referent_bearer") == 1.0
    assert f in list(a.inner.neighbours(c, "framed_by"))


def test_behavioral_distributional():
    a = _fresh(); _load_seed(a, "composer_distributional_graph")
    _mk_cr(a, "wants_distributional_rule", tag="beh_distributional")
    _tick(a)
    w = a.s.add_node("WordForm", {"freq_norm": 0.9, "ctx_entropy_norm": 0.9})
    wf_type = a.s.add_node("Concept", {"name": "WordForm"})
    a.inner.add_edge_unchecked(w, "is_a", wf_type)
    lo = a.s.add_node("WordForm", {"freq_norm": 0.1, "ctx_entropy_norm": 0.1})
    a.inner.add_edge_unchecked(lo, "is_a", wf_type)
    a.inner.run_rules()
    assert a.s.node(w)["attrs"].get("is_function") == 1.0
    assert a.s.node(lo)["attrs"].get("is_function") is None


def test_behavioral_browse_plain():
    a = _fresh(); _load_seed(a, "composer_browse_graph")
    _mk_cr(a, "wants_browse_rule", tag="beh_browse")
    _tick(a)
    sess = a.s.add_node("Sess", {})
    goal = a.s.add_node("Goal", {"status": "active"})
    a.inner.add_edge_unchecked(sess, "has_goal", goal)
    wm = a.s.add_node("WM", {"text": "volcanoes"})
    a.inner.add_edge_unchecked(goal, "wants", wm)
    aff1 = a.s.add_node("Aff", {"label_lc": "learn about volcanoes", "world_id": "aff1"})
    aff2 = a.s.add_node("Aff", {"label_lc": "learn about rivers", "world_id": "aff2"})
    a.inner.add_edge_unchecked(sess, "has_affordance", aff1)
    a.inner.add_edge_unchecked(sess, "has_affordance", aff2)
    a.inner.run_rules()
    assert a.s.node(sess)["attrs"].get("chosen_action") == "aff1"


def test_behavioral_browse_constrained():
    a = _fresh(); _load_seed(a, "composer_browse_constrained_graph")
    _mk_cr(a, "wants_browse_constrained_rule", tag="beh_browse_c")
    _tick(a)
    sess = a.s.add_node("Sess", {})
    goal = a.s.add_node("Goal", {"status": "active"})
    a.inner.add_edge_unchecked(sess, "has_goal", goal)
    wm = a.s.add_node("WM", {"text": "volcanoes"})
    a.inner.add_edge_unchecked(goal, "wants", wm)
    cw = a.s.add_node("CW", {"text": "diagram"})
    a.inner.add_edge_unchecked(goal, "constrained_by", cw)
    decoy = a.s.add_node("Aff", {"label_lc": "volcanoes", "world_id": "decoy"})
    correct = a.s.add_node("Aff", {"label_lc": "volcanoes diagram", "world_id": "correct"})
    a.inner.add_edge_unchecked(sess, "has_affordance", decoy)
    a.inner.add_edge_unchecked(sess, "has_affordance", correct)
    a.inner.run_rules()
    assert a.s.node(sess)["attrs"].get("chosen_action") == "correct"


def test_behavioral_comprehension_find():
    a = _fresh(); _load_seed(a, "composer_comprehension_find_graph")
    _mk_cr(a, "wants_find_rule", tag="beh_find")
    _tick(a)
    msg = a.s.add_node("Message", {})
    for w in ["find", "the", "page", "about", "volcanoes"]:
        mn = a.s.add_node("Mention", {"text": w})
        a.inner.add_edge_unchecked(msg, "has_mention", mn)
    a.inner.run_rules()
    goals = [n for n in a.s.nodes(type="Goal") if a.s.node(n)["attrs"].get("kind") == "find"]
    assert len(goals) == 1
    wants = sorted(a.s.node(w)["attrs"].get("text") for w in a.inner.neighbours(goals[0], "wants"))
    assert wants == ["volcanoes"]


def test_behavioral_comprehension_find_constrained():
    a = _fresh(); _load_seed(a, "composer_comprehension_find_graph")
    _mk_cr(a, "wants_find_constrained_rule", tag="beh_findc")
    _tick(a)
    msg = a.s.add_node("Message", {})
    dm = a.s.add_node("Mention", {"text": "find"})
    a.inner.add_edge_unchecked(msg, "has_mention", dm)
    tgt = a.s.add_node("Mention", {"text": "volcanoes", "role": "content", "pos": "noun", "gov_prep": "about"})
    cst = a.s.add_node("Mention", {"text": "diagram", "role": "content", "pos": "noun", "gov_prep": "near"})
    a.inner.add_edge_unchecked(msg, "has_mention", tgt)
    a.inner.add_edge_unchecked(msg, "has_mention", cst)
    a.inner.run_rules()
    goals = [n for n in a.s.nodes(type="Goal") if a.s.node(n)["attrs"].get("kind") == "find"]
    assert len(goals) == 1
    wants = sorted(a.s.node(w)["attrs"].get("text") for w in a.inner.neighbours(goals[0], "wants"))
    constrained = sorted(a.s.node(w)["attrs"].get("text") for w in a.inner.neighbours(goals[0], "constrained_by"))
    assert wants == ["volcanoes"] and constrained == ["diagram"]


def test_behavioral_communicate():
    a = _fresh(); _load_seed(a, "composer_communicate_graph")
    _mk_cr(a, "wants_communicate_rule", tag="beh_communicate")
    _tick(a)
    g = a.s.add_node("Goal", {})
    scene = a.s.add_node("Scene", {})
    a.inner.add_edge_unchecked(g, "describes", scene)
    p = a.s.add_node("Percept", {})
    a.inner.add_edge_unchecked(scene, "has_percept", p)
    con = a.s.add_node("Concept", {})
    a.inner.add_edge_unchecked(p, "is_a", con)
    a.inner.run_rules()
    subgoals = list(a.inner.neighbours(g, "has_subgoal"))
    assert len(subgoals) == 1
    assert a.s.node(subgoals[0])["attrs"].get("action") == "produce_utterance"
    assert con in list(a.inner.neighbours(subgoals[0], "about"))


# ---------------------------------------------------------------------------
# SECTION 3 — idempotency (the starvation bug the pilot found: a meta-rule
# without a real idempotency guard re-grinds its trigger forever).
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("seed_stem,edge,extra", [
    ("composer_control_graph", "wants_control_rule", {}),
    ("composer_grouping_graph", "wants_grouping_rule", {}),
    ("composer_decision_graph", "wants_decision_rule", {}),
    ("composer_construction_graph", "wants_construction_rule", {}),
    ("composer_distributional_graph", "wants_distributional_rule", {}),
    ("composer_attention_graph", "wants_attention_rule", {}),
    ("composer_browse_graph", "wants_browse_rule", {}),
    ("composer_browse_constrained_graph", "wants_browse_constrained_rule", {}),
    ("composer_communicate_graph", "wants_communicate_rule", {}),
])
def test_idempotent_retick_no_duplicate_rules(seed_stem, edge, extra):
    a = _fresh(); _load_seed(a, seed_stem)
    _mk_cr(a, edge, tag="idem", **extra)
    for _ in range(20):
        a.s.tick()
    n1 = len(a.s.nodes(type="Rule"))
    for _ in range(20):
        a.s.tick()
    n2 = len(a.s.nodes(type="Rule"))
    assert n1 == n2 and n1 >= 2   # meta-rule + at least one minted rule, never duplicated


def test_idempotent_retick_comprehension_find_branches():
    a = _fresh(); _load_seed(a, "composer_comprehension_find_graph")
    _mk_cr(a, "wants_find_rule", tag="idemf")
    _mk_cr(a, "wants_find_constrained_rule", tag="idemfc")
    for _ in range(20):
        a.s.tick()
    n1 = len(a.s.nodes(type="Rule"))
    for _ in range(20):
        a.s.tick()
    assert len(a.s.nodes(type="Rule")) == n1


# ---------------------------------------------------------------------------
# SECTION 4 — checkpoint round-trip: meta-rule + minted rule survive
# save/load into a FRESH WorldAdapter (empty struct store).
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("seed_stem,edge,expected_names", [
    ("composer_control_graph", "wants_control_rule",
     ["default_no_response_rt", "control_my_body_rt"]),
    ("composer_decision_graph", "wants_decision_rule",
     ["decide_under_uncertainty_rt"]),
    ("composer_browse_graph", "wants_browse_rule",
     ["choose_affordance_by_relevance_rt", "browse_goal_satisfied_when_seen_rt"]),
])
def test_checkpoint_roundtrip_survives_fresh_reload(seed_stem, edge, expected_names):
    a = _fresh(); _load_seed(a, seed_stem)
    _mk_cr(a, edge, tag="rt")
    for _ in range(8):
        a.s.tick()
    assert a.inner.rule_count() == len(expected_names)

    saved = a.s.graph_to_dict()
    b = WorldAdapter(seeds=())
    assert b.inner.rule_count() == 0
    b.s.graph_from_dict(saved)
    assert b.inner.rule_count() == 0   # struct store not restored -- graph-only, per the pilot's finding

    b_rule_ids = sorted(b.s.node(n)["attrs"].get("id") for n in b.s.nodes(type="Rule"))
    assert set(expected_names) <= set(b_rule_ids)

    # exercise the reloaded minted rule purely via tick() -- zero re-mint.
    trig = b.s.add_node("Trig", {})
    for _ in range(3):
        b.s.tick()
    assert b.inner.rule_count() == 0   # confirms run_graph_rules alone reproduces it


# ---------------------------------------------------------------------------
# SECTION 5 — full boot regression guard: every new seed installs cleanly
# alongside the whole seed inventory (mirrors the pilot's own boot gate).
# ---------------------------------------------------------------------------
_NEW_SEED_IDS = [
    "composer_control_graph", "composer_grouping_graph", "composer_decision_graph",
    "composer_construction_graph", "composer_distributional_graph", "composer_attention_graph",
    "composer_browse_graph", "composer_browse_constrained_graph",
    "composer_comprehension_find_graph", "composer_communicate_graph",
]


def test_full_load_all_seeds_still_boots_with_all_migrated_seeds_present():
    a = WorldAdapter(seeds=())
    report = load_all_seeds(a)
    assert report["total"] > 0
    failed_ids = [f.split(":")[0] for f in report["failed"]]
    for sid in _NEW_SEED_IDS:
        assert sid in report["order"], f"{sid} not installed during full boot"
        assert sid not in failed_ids, f"{sid} failed to install: {report['failed']}"


# ---------------------------------------------------------------------------
# SECTION 6 — ground_concern ROUTING LEDGER: the real production seam
# (induce_concern -> ground_concern) prefers the graph path for a migrated
# composer and reports which path served each request.
# ---------------------------------------------------------------------------
def test_ground_concern_routes_control_through_graph():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    ind = rf.induce_concern(a, [["control", "WHAT", "I", "OWN"]], name_hint="ledger_control")
    assert ind.get("minted") is True
    g = rf.ground_concern(a, [ind["capability_key"]])
    assert g.get("grounded") is True
    assert g.get("path") == "compose_control_rule"
    assert g.get("served_by") == "graph"
    # the ComposeRequest node itself carries the ledger mark -- inspectable
    # graph data, not a Python-only return value.
    crs = [n for n in a.s.nodes("ComposeRequest") if a.s.node(n)["attrs"].get("served_by") == "graph"]
    assert len(crs) >= 1


def test_ground_concern_routes_decision_through_graph():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    ind = rf.induce_concern(a, [["utility", "ARGMAX", "over", "AFFORDANCE"]], name_hint="ledger_decision")
    assert ind.get("minted") is True
    g = rf.ground_concern(a, [ind["capability_key"]])
    assert g.get("grounded") is True
    assert g.get("path") == "compose_decision_rule"
    assert g.get("served_by") == "graph"


def test_ground_concern_routes_grouping_through_graph():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    ind = rf.induce_concern(a, [["group"], ["the"], ["parts"]], name_hint="ledger_grouping")
    assert ind.get("minted") is True
    g = rf.ground_concern(a, [ind["capability_key"]])
    assert g.get("grounded") is True
    assert g.get("path") == "compose_grouping_rule"
    assert g.get("served_by") == "graph"


def test_ground_concern_routes_browse_through_graph():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    ind = rf.induce_concern(a, [["match", "the", "AFFORDANCE", "to", "the", "GOAL"]], name_hint="ledger_browse")
    assert ind.get("minted") is True
    g = rf.ground_concern(a, [ind["capability_key"]])
    assert g.get("grounded") is True
    assert g.get("path") == "compose_browse_rule"
    assert g.get("served_by") == "graph"


def test_ground_concern_experiment_no_test_decorated_combo_routes_through_graph():
    """`vary+send+judge` (no 'test') USED TO be a negative control (router
    declined, `served_by` said 'python') -- that was the exact router-
    coverage gap this migration closes: `_compose_experiment_rule` nests
    vary/send/gradient/structure/embed entirely under `if "test" in rp:`,
    so WITHOUT 'test' they are INERT and the Python oracle's only authored
    output for this combo is the judge rule -- semantically identical to
    judge-alone. `_route_experiment_composer`'s no-'test' branch now fires
    the judge meta-rule (dropping the inert vary/send) so this combo is
    graph-served too. See tests/test_experiment_composer_graph.py's own
    `test_vary_send_judge_no_test_structurally_matches_python_oracle` for
    the byte-level equivalence proof against the Python oracle."""
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": ["ledger_exp"], "induced": 1.0,
        "residual_predicates": ["vary", "send", "judge"], "from_observation": 1.0, "source": "concern_induction",
    })
    g = rf.ground_concern(a, ["ledger_exp"])
    assert g.get("grounded") is True
    assert g.get("path") == "compose_experiment_rule"
    assert g.get("served_by") == "graph"
    names = {r["name"] for r in g.get("rules", [])}
    assert names == {"judge_experiment_outcome_ledger_exp"}


def test_ground_concern_experiment_partial_test_anchored_combo_routes_through_graph():
    """FORMER negative control, now closed: 'test+send+judge+gradient'
    (without 'adopt') used to fall through to Python (no exact per-combo
    meta-rule minted this partial shape). `compose_experiment_mint_
    parametric` mints for ANY 'test'-anchored combination via flags, so
    this is graph-served now -- see tests/test_experiment_composer_graph.py
    for the byte-level equivalence proof against the Python oracle."""
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    from substrate.seed_loader import manifest_for as _manifest_for
    a.s._inner.load_seed_manifest(_manifest_for("grid_navigation"), a.agent)
    a.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": ["ledger_exp2"], "induced": 1.0,
        "residual_predicates": ["test", "send", "judge", "gradient"], "from_observation": 1.0,
        "source": "concern_induction",
    })
    g = rf.ground_concern(a, ["ledger_exp2"])
    assert g.get("grounded") is True
    assert g.get("path") == "compose_experiment_rule"
    assert g.get("served_by") == "graph"
    names = {r["name"] for r in g.get("rules", [])}
    assert names == {"author_experiment_from_residual_ledger_exp2", "judge_experiment_outcome_ledger_exp2"}


def test_ground_concern_experiment_no_authoring_wall_stays_on_python_path():
    """Negative control (the ONLY genuine wall left): NEITHER test, judge,
    NOR adopt grounded -- both the graph router and the Python oracle
    author nothing, `served_by` truthfully says 'python' (Python's own
    `grounded: False` path, per `_compose_experiment_rule`'s own wall
    message: 'vary/send/... alone only refine parts, nothing to author')."""
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": ["ledger_exp3"], "induced": 1.0,
        "residual_predicates": ["vary", "send"], "from_observation": 1.0,
        "source": "concern_induction",
    })
    g = rf.ground_concern(a, ["ledger_exp3"])
    assert g.get("grounded") is False
    assert g.get("path") == "compose_experiment_rule"
    assert g.get("served_by") in (None, "python")


def test_ground_concern_experiment_judge_alone_routes_through_graph():
    """Positive control: the judge-alone combo IS migrated -- served_by says
    'graph', and the minted rule is the SAME judge_experiment_outcome_* the
    Python builder would have authored."""
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": ["ledger_exp_judge"], "induced": 1.0,
        "residual_predicates": ["judge"], "from_observation": 1.0, "source": "concern_induction",
    })
    g = rf.ground_concern(a, ["ledger_exp_judge"])
    assert g.get("grounded") is True
    assert g.get("path") == "compose_experiment_rule"
    assert g.get("served_by") == "graph"
    names = {r["name"] for r in g.get("rules", [])}
    assert names == {"judge_experiment_outcome_ledger_exp_judge"}


# ---------------------------------------------------------------------------
# SECTION 7 — EDITABILITY PROOF (a): the agent's own self-model faculty can
# now answer 'what does <meta-rule> do?' for graph-resident composers, not
# only struct-store rules (domains/self_model.py's SECOND pass).
# ---------------------------------------------------------------------------
def test_self_model_mirrors_graph_resident_meta_rules():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    rep = sm.ensure_self_model(a)
    assert rep["rules"]["graph_total"] > 0
    for q, needle in [
        ("what does compose_control_graph do?", "wants_control_rule"),
        ("what does compose_decision_graph do?", "wants_decision_rule"),
        ("what does compose_browse_graph do?", "wants_browse_rule"),
    ]:
        ans = a.answer_question(q)
        assert "found=True" in ans or "found': True" in ans or "I hold" in ans or "my rule" in ans, ans
        assert needle in ans, ans


def test_self_model_honest_not_found_for_bogus_meta_rule():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    sm.ensure_self_model(a)
    ans = a.answer_question("what does compose_totally_bogus_graph do?")
    assert "don't have" in ans


# ---------------------------------------------------------------------------
# SECTION 8 — EDITABILITY PROOF (b): apply a domain-general EditOp
# (domains/edit_ops.py — NOT written for this composer) to a COPY of the
# decision composer's meta-rule, install the VARIANT on a scratch
# substrate, and show it mints a CORRESPONDINGLY VARIED rule with
# observably different behaviour (inverted goal-seeking).
# ---------------------------------------------------------------------------
def test_edit_op_flip_comparison_varies_the_decision_composer():
    meta = json.load(open(os.path.join(SEED_DIR, "composer_decision_graph.json")))["nodes"][0]["attrs"]
    rule_like = {"name": meta["id"], "match": meta["match"], "where": meta["where"], "effects": meta["effect"]}

    comparisons_before = edit_ops.find_comparison_nodes(rule_like["effects"])
    assert {n["type"] for n in comparisons_before} == {"Gte"}

    varied = edit_ops.apply_flip_comparison(rule_like, "compose_decision_graph_variant")
    assert varied is not None
    assert {n["type"] for n in edit_ops.find_comparison_nodes(varied["effects"])} == {"Lte"}

    varied_attrs = dict(meta)
    varied_attrs["id"] = varied["name"]
    varied_attrs["match"] = [["agent", "wants_decision_rule_variant", "cr"]]
    varied_attrs["effect"] = varied["effects"]

    def _run(agent, trigger_edge, meta_attrs=None, seed_stem=None):
        if meta_attrs is not None:
            agent.s.add_node("Rule", meta_attrs)
        else:
            _load_seed(agent, seed_stem)
        _mk_cr(agent, trigger_edge, tag="editdemo")
        _tick(agent)
        game = agent.s.add_node("Game", {})
        goal = agent.s.add_node("Goal", {"cy": 0.0, "cx": 0.0})
        agent.inner.add_edge_unchecked(game, "has_goal", goal)
        c = agent.s.add_node("Cand", {"cy": 5.0, "cx": 5.0})
        agent.inner.add_edge_unchecked(game, "avatar_candidate", c)
        up = agent.s.add_node("Aff", {"name": "up", "drow": -1.0, "dcol": 0.0})
        down = agent.s.add_node("Aff", {"name": "down", "drow": 1.0, "dcol": 0.0})
        agent.inner.add_edge_unchecked(game, "affordance", up)
        agent.inner.add_edge_unchecked(game, "affordance", down)
        agent.inner.run_rules()
        return agent.s.node(game)["attrs"].get("chosen_action")

    original_choice = _run(_fresh(), "wants_decision_rule", seed_stem="composer_decision_graph")
    varied_choice = _run(_fresh(), "wants_decision_rule_variant", meta_attrs=varied_attrs)

    assert original_choice == "up"      # unmodified composer: moves TOWARD the goal
    assert varied_choice == "down"      # edited composer: moves AWAY from the goal (inverted)
