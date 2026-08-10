"""Pins the capability envelope of the graph-resident rule-minting dialect
(runners/dsl/src/graph_rules.rs + the `SetRuleClause`/`__mint__` path in
rewrite.rs + substrate.rs), established BEFORE designing the composer pilot
(see seeds/composer_comprehension_graph.json, scripts/jabberwock_composer_in_graph.py).

Findings pinned here (see each test's docstring for the specific claim):

  1. A graph-resident Rule NODE (type="Rule", attrs id/match/where/effect) is
     matched + applied directly by `Substrate::tick()` via `run_graph_rules`,
     which re-derives the rule list from `nodes_of_type("Rule")` FRESH on
     EVERY call. No `add_rule()` Python call is required for such a node to
     be live -- pure graph data, self-driving.

  2. An `Effect::AddNode` inside a Rule node's own effect list can construct
     ANOTHER Rule node (match/where/effect as its attrs) -- "a rule that
     mints a rule." Values from the firing rule's OWN match bindings can be
     SPLICED into the minted rule's where/effect via `Attr(Var(...), key)`
     wrapped in `MkDict`/`Append` Term composition (there is no bulk "build
     me this whole JSON tree with one hole in it" primitive -- the WHOLE
     containing structure must be built as one Term when any leaf is
     dynamic, since a `set_attr` effect argument is EITHER a frozen Literal
     OR ONE Computed Term evaluated at fire time).

  3. `SetRuleClause` with `field="__mint__"` additionally compiles a just-
     built Rule node into the native STRUCT rule store (`Substrate::rules`),
     making it live WITHIN THE SAME `tick()` call (useful when the minted
     rule needs to react to data already present in this tick). It is an
     ACCELERATION, not a requirement: `run_graph_rules` alone (no __mint__)
     makes a freshly-minted Rule node live on the very NEXT `tick()` call,
     with the struct store (`rule_count()`) staying at 0 throughout -- see
     `test_mint_is_acceleration_not_requirement`.

  4. FIXED (was a WALL): `StringConcat` evaluates to `Value::Surface(
     SurfaceKind::Text, ...)`, NOT `Value::Str`. `SetRuleClause`'s applier
     (rewrite.rs, the `Effect::SetRuleClause` arm) and `rule_from_node`'s
     id/name reader (graph_rules.rs's `as_str`) used to require `Value::Str`
     exactly -- a `Surface`-valued id silently failed BOTH the mint-queue
     push (no error printed) and (if it ever reached the parser) the rule's
     `name` (fell back to "<unnamed>"). Both sites now coerce `Value::Str`
     OR `Value::Surface(SurfaceKind::Text, ...)` via a shared helper
     (`value_as_str_like` in rewrite.rs; the `as_str` arm in graph_rules.rs),
     the same coercion `TermNode::TextShape`/`MkDict` already used elsewhere
     in term.rs -- so a dynamically-concatenated rule id now mints and fires
     exactly like a literal one (see
     `test_string_concat_surface_coerces_and_mints`). A genuinely
     untypeable name/field (e.g. an Int or Dict landing where a name is
     expected) is no longer silently dropped either: it prints a loud
     `[self-repair] SetRuleClause: ... did not resolve to a string-shaped
     value ...` diagnostic (rewrite.rs), matching the `[self-repair]` /
     `[self-build]` logging convention `apply_pending_rule_edits`
     (substrate.rs) already uses for this same queue.

  5. Node ids recycle across separate `WorldAdapter()` instances -- every
     test here creates its OWN fresh `WorldAdapter(seeds=())` and never
     assumes a specific NodeID.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest

from substrate.world_adapter import WorldAdapter

# --- Term-JSON builder helpers (test-authoring DATA, not agent logic) -----

V = lambda n: {"type": "Var", "name": n}
L = lambda v: {"type": "Lit", "value": v}
A = lambda nd, k: {"type": "Attr", "node": nd, "key": k}
MK = lambda *kvs: {"type": "MkDict", "items": list(kvs)}
AP = lambda seq, item: {"type": "Append", "seq": seq, "item": item}
EMPTY_TUPLE = L([])


def _describe_where_effect():
    """Builds the (where, effect) Term-pair for the target minted rule:
    match a Mention whose text == <directive_word, spliced from `cr`> over a
    Message `about` a `scene` that isn't already `described_by` something,
    then mint Goal{kind: <goal_kind, spliced from `cr`>}. Mirrors
    domains/reflective_faculty.py's `_compose_comprehension_rule` describe-
    branch (read-only reference; not imported, not edited)."""
    lit_directive = MK(L("type"), L("Lit"), L("value"), A(V("cr"), "directive_word"))
    attr_mention_text = MK(L("type"), L("Attr"), L("node"), MK(L("type"), L("Var"), L("name"), L("mention")),
                            L("key"), L("text"))
    eq_dict = MK(L("type"), L("Eq"), L("a"), attr_mention_text, L("b"), lit_directive)
    nb_scene = MK(L("type"), L("Neighbours"), L("node"), MK(L("type"), L("Var"), L("name"), L("scene")),
                  L("edge_type"), L("described_by"))
    exists_dict = MK(L("type"), L("Exists"), L("source"), nb_scene, L("var_name"), L("_i"),
                      L("predicate"), MK(L("type"), L("Lit"), L("value"), L(True)))
    not_dict = MK(L("type"), L("Not"), L("arg"), exists_dict)
    items_tuple = AP(AP(EMPTY_TUPLE, eq_dict), not_dict)
    where_dict = MK(L("type"), L("And"), L("items"), items_tuple)

    attrs_dict = MK(L("kind"), A(V("cr"), "goal_kind"))
    add_node_tuple = AP(AP(AP(AP(EMPTY_TUPLE, L("add_node")), L("g")), L("Goal")), attrs_dict)
    edge1_tuple = AP(AP(AP(AP(EMPTY_TUPLE, L("add_edge")), L("g")), L("describes")), L("scene"))
    edge2_tuple = AP(AP(AP(AP(EMPTY_TUPLE, L("add_edge")), L("scene")), L("described_by")), L("g"))
    effect_list = AP(AP(AP(EMPTY_TUPLE, add_node_tuple), edge1_tuple), edge2_tuple)
    return where_dict, effect_list


def _make_compose_request(a, directive_word, goal_kind, rule_id):
    cr = a.s.add_node("ComposeRequest", {
        "directive_word": directive_word, "goal_kind": goal_kind,
        "rule_id": rule_id, "composed": 0.0,
    })
    a.inner.add_edge_unchecked(a.agent, "wants_comprehension_rule", cr)
    return cr


def _make_message(a, directive_word):
    msg = a.s.add_node("Message", {})
    scene = a.s.add_node("Scene", {})
    mention = a.s.add_node("Mention", {"text": directive_word})
    a.inner.add_edge_unchecked(msg, "has_mention", mention)
    a.inner.add_edge_unchecked(msg, "about", scene)
    return msg, scene, mention


def _describe_goals(a, kind):
    return [nid for nid in a.s.nodes(type="Goal") if a.s.node(nid)["attrs"].get("kind") == kind]


@pytest.fixture
def agent():
    return WorldAdapter(seeds=())


# ---------------------------------------------------------------------------
# 1) Baseline: a graph-resident Rule node with a __mint__ effect fires live.
# ---------------------------------------------------------------------------

def test_baseline_mint_from_static_rule_node(agent):
    """A Rule NODE (pure graph data, host-authored ONCE as a fixed literal --
    no dynamic splicing) whose effect chain is add_node(Rule)+set_rule_clause
    __mint__ compiles a SECOND rule into the live struct store and it fires
    the SAME tick(). Mirrors scripts/mint_rule_slice.py's proven pattern,
    re-verified fresh here as the dialect's floor capability."""
    a = agent
    anchor = a.s.add_node("Anchor", {})
    probe = a.s.add_node("Probe", {})
    a.inner.add_edge_unchecked(anchor, "trig", probe)

    a.s.add_node("Rule", {
        "id": "minted_test",
        "match": [["anc", "trig", "tg"]],
        "where": L(True),
        "effect": [["set_attr", "tg", "out", {"__term__": L("minted")}]],
        "minted": 0.0,
    })
    minter = a.s.add_node("Minter", {})
    a.inner.add_edge_unchecked(minter, "wants_mint", a.s.nodes(type="Rule")[0])

    a.s.add_node("Rule", {
        "id": "mint_pending_baseline",
        "match": [["m", "wants_mint", "rn"]],
        "where": {"type": "Lt", "a": {"type": "Plus", "items": [A(V("rn"), "minted"), L(0.0)]}, "b": L(0.5)},
        "effect": [
            ["set_rule_clause", {"__term__": A(V("rn"), "id")}, "__mint__", {"__term__": V("rn")}],
            ["set_attr", "rn", "minted", 1.0],
        ],
    })

    n0 = a.inner.rule_count()
    a.s.tick()
    n1 = a.inner.rule_count()
    assert a.s.node(probe)["attrs"].get("out") == "minted"
    assert n1 == n0 + 1


# ---------------------------------------------------------------------------
# 2) FIX: StringConcat's Surface-typed result is coerced and mints cleanly
#    (was a WALL -- see the module docstring's finding 4 for the history).
# ---------------------------------------------------------------------------

def test_string_concat_surface_coerces_and_mints(agent):
    """StringConcat's result (`Value::Surface(SurfaceKind::Text, ...)`) used
    to silently break both the SetRuleClause mint-queue push (rewrite.rs's
    old `Value::Str`-only guard) and rule_from_node's id/name reader
    (graph_rules.rs's old `Value::Str`-only `as_str`) -- no exception, no
    log, the rule just never minted. FIXED: both sites now coerce
    `Value::Str` OR `Value::Surface(Text)` (mirrors the coercion
    `TermNode::TextShape`/`MkDict` already use in term.rs), so a
    dynamically-concatenated rule id mints into the live struct store and
    is readable back by its real (non-"<unnamed>") name -- exactly like a
    literal id would.

    Gated on `cr.composed` (the same `Lt(composed+0.0, 0.5)` idempotency
    pattern every other composer test in this file uses via
    `_make_compose_request`) rather than the former WALL test's unconditional
    `where: True`: an ungated composer here matches its own trigger edge
    every single pass (each firing legitimately mints a fresh `rn` node, so
    it always counts as "progress"), which starves `run_graph_rules`'s inner
    fixed-point loop for the entire `max_steps` budget and leaves nothing for
    `Substrate::run_rules` (the struct-engine pass that actually drains
    `pending_rule_edits`) to run -- an orthogonal non-termination pitfall,
    independent of the Str-vs-Surface coercion this test is pinning."""
    a = agent
    cr = a.s.add_node("ComposeRequest", {"word": "concat_test", "composed": 0.0})
    a.inner.add_edge_unchecked(a.agent, "wants_thing", cr)

    id_term = {"type": "StringConcat", "parts": [L("prefix_"), A(V("cr"), "word")]}
    a.s.add_node("Rule", {
        "id": "compose_with_concat_id",
        "match": [["agent", "wants_thing", "cr"]],
        "where": {"type": "Lt", "a": {"type": "Plus", "items": [A(V("cr"), "composed"), L(0.0)]}, "b": L(0.5)},
        "effect": [
            ["add_node", "rn", "Rule", {"minted": 0.0}],
            ["set_attr", "rn", "id", {"__term__": id_term}],
            ["set_attr", "rn", "match", [["x", "y", "z"]]],
            ["set_attr", "rn", "where", L(True)],
            ["set_attr", "rn", "effect", []],
            ["set_rule_clause", {"__term__": A(V("rn"), "id")}, "__mint__", {"__term__": V("rn")}],
            ["set_attr", "cr", "composed", 1.0],
        ],
    })
    n0 = a.inner.rule_count()
    a.s.tick()
    a.s.tick()
    n1 = a.inner.rule_count()
    # The Rule NODE was created (add_node/set_attr are plain graph writes --
    # those succeed regardless of value shape)...
    ids = [a.s.node(n)["attrs"].get("id") for n in a.s.nodes(type="Rule")]
    assert any(isinstance(x, str) and x.startswith("prefix_") for x in ids)
    # ...AND it was minted into the struct store: the SetRuleClause
    # applier's guard now coerces the Surface-typed name to a plain string,
    # same as it would a Value::Str literal.
    assert n1 == n0 + 1
    minted_ids = sorted(
        a.s.node(n)["attrs"].get("id") for n in a.s.nodes(type="Rule")
        if a.s.node(n)["attrs"].get("id", "").startswith("prefix_")
    )
    assert minted_ids == ["prefix_concat_test"]


# ---------------------------------------------------------------------------
# 3) MkDict + Append splice bound trigger values into nested Term-JSON.
# ---------------------------------------------------------------------------

def test_mkdict_and_append_splice_bound_values_into_nested_term_json(agent):
    """The composer's (where, effect) construction (MkDict for JSON objects,
    Append for JSON arrays, both evaluated ONCE at fire time against the
    firing rule's OWN bindings) produces a Rule node whose match/where/effect
    attrs are a byte-for-byte match to the shape `_compose_comprehension_rule`
    hand-authors in Python -- except the directive word and goal kind are
    read off the trigger node, not baked in as Python string literals."""
    a = agent
    where_dict, effect_list = _describe_where_effect()
    _make_compose_request(a, "describe", "describe_scene", "comprehend_describe_directive_graph")

    a.s.add_node("Rule", {
        "id": "compose_probe",
        "match": [["agent", "wants_comprehension_rule", "cr"]],
        "where": {"type": "Lt", "a": {"type": "Plus", "items": [A(V("cr"), "composed"), L(0.0)]}, "b": L(0.5)},
        "effect": [
            ["add_node", "rn", "Rule", {"minted": 0.0}],
            ["set_attr", "rn", "id", {"__term__": A(V("cr"), "rule_id")}],
            ["set_attr", "rn", "match", [["m", "has_mention", "mention"], ["m", "about", "scene"]]],
            ["set_attr", "rn", "where", {"__term__": where_dict}],
            ["set_attr", "rn", "effect", {"__term__": effect_list}],
            ["set_attr", "cr", "composed", 1.0],
        ],
    })
    a.s.tick()

    minted = [n for n in a.s.nodes(type="Rule")
              if a.s.node(n)["attrs"].get("id") == "comprehend_describe_directive_graph"]
    assert len(minted) == 1
    attrs = a.s.node(minted[0])["attrs"]
    # the dynamic leaf is the ACTUAL runtime string, not a further reference.
    where = attrs["where"]
    lit_leaf = where["items"][0]["b"]
    assert lit_leaf == {"type": "Lit", "value": "describe"}
    effect = attrs["effect"]
    goal_attrs = effect[0][3]
    assert goal_attrs == {"kind": "describe_scene"}


# ---------------------------------------------------------------------------
# 4) The composer as ONE pure graph node -- no add_rule() Python call at all.
# ---------------------------------------------------------------------------

def test_composer_rule_as_pure_graph_node_mints_and_fires_via_tick(agent):
    """The ENTIRE composer -- match/where/effect, including the __mint__ step
    -- is authored as a single `add_node("Rule", {...})` call (data, not a
    rule-engine call). `tick()` alone (which runs `run_graph_rules` over
    every Rule-typed node each call) discovers it, fires it, mints the
    parameterized comprehension rule, and that minted rule fires end-to-end
    against a real Message/Mention/Scene -- zero `add_rule()` Python calls
    anywhere in this test."""
    a = agent
    where_dict, effect_list = _describe_where_effect()
    _make_compose_request(a, "describe", "describe_scene", "comprehend_describe_directive_graph")

    a.s.add_node("Rule", {
        "id": "compose_comprehension_graph",
        "match": [["agent", "wants_comprehension_rule", "cr"]],
        "where": {"type": "Lt", "a": {"type": "Plus", "items": [A(V("cr"), "composed"), L(0.0)]}, "b": L(0.5)},
        "effect": [
            ["add_node", "rn", "Rule", {"minted": 0.0}],
            ["set_attr", "rn", "id", {"__term__": A(V("cr"), "rule_id")}],
            ["set_attr", "rn", "match", [["m", "has_mention", "mention"], ["m", "about", "scene"]]],
            ["set_attr", "rn", "where", {"__term__": where_dict}],
            ["set_attr", "rn", "effect", {"__term__": effect_list}],
            ["set_rule_clause", {"__term__": A(V("rn"), "id")}, "__mint__", {"__term__": V("rn")}],
            ["set_attr", "cr", "composed", 1.0],
        ],
    })

    assert len(a.s.nodes(type="Rule")) == 1  # only the composer exists so far
    a.s.tick()
    rule_ids = sorted(a.s.node(n)["attrs"].get("id") for n in a.s.nodes(type="Rule"))
    assert rule_ids == ["compose_comprehension_graph", "comprehend_describe_directive_graph"]

    _make_message(a, "describe")
    a.s.tick()
    goals = _describe_goals(a, "describe_scene")
    assert len(goals) == 1


# ---------------------------------------------------------------------------
# 5) __mint__ is an acceleration, not a requirement.
# ---------------------------------------------------------------------------

def test_mint_is_acceleration_not_requirement(agent):
    """Drop the set_rule_clause/__mint__ effect entirely. The minted Rule
    node still becomes live -- on the NEXT tick() call, purely because
    `run_graph_rules` re-derives its rule list from `nodes_of_type("Rule")`
    fresh every call. The struct store (`rule_count()`) stays at 0 for the
    WHOLE test: this path never touches `Substrate::rules` at all."""
    a = agent
    where_dict, effect_list = _describe_where_effect()
    _make_compose_request(a, "describe", "describe_scene", "comprehend_describe_directive_graph")

    a.s.add_node("Rule", {
        "id": "compose_comprehension_graph_no_mint",
        "match": [["agent", "wants_comprehension_rule", "cr"]],
        "where": {"type": "Lt", "a": {"type": "Plus", "items": [A(V("cr"), "composed"), L(0.0)]}, "b": L(0.5)},
        "effect": [
            ["add_node", "rn", "Rule", {"minted": 0.0}],
            ["set_attr", "rn", "id", {"__term__": A(V("cr"), "rule_id")}],
            ["set_attr", "rn", "match", [["m", "has_mention", "mention"], ["m", "about", "scene"]]],
            ["set_attr", "rn", "where", {"__term__": where_dict}],
            ["set_attr", "rn", "effect", {"__term__": effect_list}],
            ["set_attr", "cr", "composed", 1.0],
        ],
    })
    a.s.tick()  # composes the new Rule node
    assert a.inner.rule_count() == 0

    _make_message(a, "describe")
    a.s.tick()  # picks the new Rule node up fresh + fires it
    assert a.inner.rule_count() == 0
    assert len(_describe_goals(a, "describe_scene")) == 1


# ---------------------------------------------------------------------------
# 6) Two different triggers mint two independently-working rules.
# ---------------------------------------------------------------------------

def test_two_different_triggers_mint_two_independently_working_rules(agent):
    a = agent
    where_dict, effect_list = _describe_where_effect()
    _make_compose_request(a, "describe", "describe_scene", "comprehend_describe_directive_graph")
    _make_compose_request(a, "report", "report_intent", "comprehend_report_directive_graph")

    a.s.add_node("Rule", {
        "id": "compose_comprehension_graph",
        "match": [["agent", "wants_comprehension_rule", "cr"]],
        "where": {"type": "Lt", "a": {"type": "Plus", "items": [A(V("cr"), "composed"), L(0.0)]}, "b": L(0.5)},
        "effect": [
            ["add_node", "rn", "Rule", {"minted": 0.0}],
            ["set_attr", "rn", "id", {"__term__": A(V("cr"), "rule_id")}],
            ["set_attr", "rn", "match", [["m", "has_mention", "mention"], ["m", "about", "scene"]]],
            ["set_attr", "rn", "where", {"__term__": where_dict}],
            ["set_attr", "rn", "effect", {"__term__": effect_list}],
            ["set_rule_clause", {"__term__": A(V("rn"), "id")}, "__mint__", {"__term__": V("rn")}],
            ["set_attr", "cr", "composed", 1.0],
        ],
    })
    for _ in range(6):
        a.s.tick()

    rule_ids = sorted(a.s.node(n)["attrs"].get("id") for n in a.s.nodes(type="Rule"))
    assert rule_ids == ["compose_comprehension_graph", "comprehend_describe_directive_graph",
                         "comprehend_report_directive_graph"]

    _make_message(a, "describe")
    _make_message(a, "report")
    for _ in range(3):
        a.s.tick()
    assert len(_describe_goals(a, "describe_scene")) == 1
    assert len(_describe_goals(a, "report_intent")) == 1


# ---------------------------------------------------------------------------
# 7) Idempotency: re-driving the composer never double-mints / double-fires.
# ---------------------------------------------------------------------------

def test_idempotent_recompose_no_duplicate(agent):
    a = agent
    where_dict, effect_list = _describe_where_effect()
    _make_compose_request(a, "describe", "describe_scene", "comprehend_describe_directive_graph")

    a.s.add_node("Rule", {
        "id": "compose_comprehension_graph",
        "match": [["agent", "wants_comprehension_rule", "cr"]],
        "where": {"type": "Lt", "a": {"type": "Plus", "items": [A(V("cr"), "composed"), L(0.0)]}, "b": L(0.5)},
        "effect": [
            ["add_node", "rn", "Rule", {"minted": 0.0}],
            ["set_attr", "rn", "id", {"__term__": A(V("cr"), "rule_id")}],
            ["set_attr", "rn", "match", [["m", "has_mention", "mention"], ["m", "about", "scene"]]],
            ["set_attr", "rn", "where", {"__term__": where_dict}],
            ["set_attr", "rn", "effect", {"__term__": effect_list}],
            ["set_rule_clause", {"__term__": A(V("rn"), "id")}, "__mint__", {"__term__": V("rn")}],
            ["set_attr", "cr", "composed", 1.0],
        ],
    })
    _make_message(a, "describe")
    for _ in range(10):
        a.s.tick()
    n_rules_1 = len(a.s.nodes(type="Rule"))
    n_goals_1 = len(_describe_goals(a, "describe_scene"))
    for _ in range(10):
        a.s.tick()
    assert len(a.s.nodes(type="Rule")) == n_rules_1
    assert len(_describe_goals(a, "describe_scene")) == n_goals_1 == 1
    assert a.inner.rule_count() == 1  # only the minted rule ever got __mint__'d


# ---------------------------------------------------------------------------
# 8) Checkpoint round-trip: minted + meta rule survive a FRESH reload.
# ---------------------------------------------------------------------------

def test_checkpoint_roundtrip_survives_fresh_reload(agent):
    """Save agent A's graph after minting, load into a BRAND NEW WorldAdapter
    B (empty struct store, `rule_count() == 0`). B's `tick()` alone -- purely
    via `run_graph_rules` re-parsing the persisted Rule nodes -- reproduces
    the SAME behaviour. `graph_to_dict`/`graph_from_dict` only serialise
    `inner.graph` (nodes+edges), never `inner.rules` (the struct store,
    confirmed by reading py.rs's graph_to_dict/graph_from_dict) -- so this is
    the strongest possible round-trip evidence: the struct store is provably
    NOT involved in B's post-reload behaviour."""
    a = agent
    where_dict, effect_list = _describe_where_effect()
    _make_compose_request(a, "describe", "describe_scene", "comprehend_describe_directive_graph")
    a.s.add_node("Rule", {
        "id": "compose_comprehension_graph",
        "match": [["agent", "wants_comprehension_rule", "cr"]],
        "where": {"type": "Lt", "a": {"type": "Plus", "items": [A(V("cr"), "composed"), L(0.0)]}, "b": L(0.5)},
        "effect": [
            ["add_node", "rn", "Rule", {"minted": 0.0}],
            ["set_attr", "rn", "id", {"__term__": A(V("cr"), "rule_id")}],
            ["set_attr", "rn", "match", [["m", "has_mention", "mention"], ["m", "about", "scene"]]],
            ["set_attr", "rn", "where", {"__term__": where_dict}],
            ["set_attr", "rn", "effect", {"__term__": effect_list}],
            ["set_rule_clause", {"__term__": A(V("rn"), "id")}, "__mint__", {"__term__": V("rn")}],
            ["set_attr", "cr", "composed", 1.0],
        ],
    })
    for _ in range(4):
        a.s.tick()
    assert a.inner.rule_count() == 1  # minted rule live in A's struct store

    d = a.s.graph_to_dict()

    b = WorldAdapter(seeds=())
    assert b.inner.rule_count() == 0
    b.s.graph_from_dict(d)
    assert b.inner.rule_count() == 0  # NOT restored by graph_from_dict -- graph-only

    rule_ids_b = sorted(b.s.node(n)["attrs"].get("id") for n in b.s.nodes(type="Rule"))
    assert rule_ids_b == ["compose_comprehension_graph", "comprehend_describe_directive_graph"]

    _make_message(b, "describe")
    for _ in range(3):
        b.s.tick()
    goals = [n for n in b.s.nodes(type="Goal") if b.s.node(n)["attrs"].get("kind") == "describe_scene"]
    assert len(goals) == 1
    assert b.inner.rule_count() == 0  # still never touched the struct store
