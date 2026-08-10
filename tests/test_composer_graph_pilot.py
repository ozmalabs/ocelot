"""Pytest form of scripts/jabberwock_composer_in_graph.py's assertions, plus a
checkpoint round-trip: the pilot seed (seeds/composer_comprehension_graph.json)
installs a single graph-resident meta-rule that mints TWO DIFFERENT working
comprehension rules from TWO DIFFERENT ComposeRequest triggers, with ZERO
Python authoring at runtime -- and both the meta-rule and its minted rules
survive a save/load cycle as plain graph data.

See tests/test_rule_minting_dialect.py for the capability envelope this pilot
rests on (in particular: `__mint__` is an acceleration not a requirement, and
`graph_to_dict`/`graph_from_dict` only serialise `inner.graph`, never the
struct-rule store -- both re-confirmed here against the ACTUAL seed file
rather than an inline rule).
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest

from substrate.world_adapter import WorldAdapter

SEED_PATH = os.path.join(ROOT, "seeds", "composer_comprehension_graph.json")
SEED_ID = "composer_comprehension_graph"
META_RULE_ID = "compose_comprehension_graph"


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


def _goals_of_kind(a, kind):
    return [n for n in a.s.nodes(type="Goal") if a.s.node(n)["attrs"].get("kind") == kind]


def _rule_node_by_id(a, rule_id):
    for n in a.s.nodes(type="Rule"):
        if a.s.node(n)["attrs"].get("id") == rule_id:
            return n
    return None


@pytest.fixture
def agent_with_seed():
    a = WorldAdapter(seeds=())
    manifest = json.load(open(SEED_PATH))
    a.s.load_seed_manifest(manifest, a.agent)
    return a


def test_seed_file_exists_and_is_valid_json():
    assert os.path.exists(SEED_PATH)
    manifest = json.load(open(SEED_PATH))
    assert manifest["id"] == SEED_ID
    rule_nodes = [n for n in manifest["nodes"] if n["type"] == "Rule"]
    assert len(rule_nodes) == 1
    assert rule_nodes[0]["attrs"]["id"] == META_RULE_ID


def test_seed_installs_exactly_the_meta_rule(agent_with_seed):
    a = agent_with_seed
    rule_ids = [a.s.node(n)["attrs"].get("id") for n in a.s.nodes(type="Rule")]
    assert rule_ids == [META_RULE_ID]


def test_composer_is_inspectable_graph_data(agent_with_seed):
    """The composer's own match/where/effect are readable graph attrs -- the
    agent can dump this node exactly like any Concept/Frame/Microtheory."""
    a = agent_with_seed
    nid = _rule_node_by_id(a, META_RULE_ID)
    assert nid is not None
    attrs = a.s.node(nid)["attrs"]
    assert attrs["match"] == (("agent", "wants_comprehension_rule", "cr"),)
    assert attrs["where"]["type"] == "Lt"
    assert len(attrs["effect"]) == 7
    assert attrs["effect"][0][:3] == ("add_node", "rn", "Rule")
    # the __mint__ effect is present, addressed at the just-built "rn" var.
    mint_effect = attrs["effect"][5]
    assert mint_effect[0] == "set_rule_clause"
    assert mint_effect[2] == "__mint__"


def test_two_compose_requests_mint_two_different_working_rules(agent_with_seed):
    a = agent_with_seed
    _make_compose_request(a, "describe", "describe_scene", "comprehend_describe_directive_graph")
    _make_compose_request(a, "report", "report_intent", "comprehend_report_directive_graph")

    for _ in range(6):
        a.s.tick()

    minted_ids = sorted(
        a.s.node(n)["attrs"].get("id") for n in a.s.nodes(type="Rule")
        if a.s.node(n)["attrs"].get("id") != META_RULE_ID
    )
    assert minted_ids == ["comprehend_describe_directive_graph", "comprehend_report_directive_graph"]

    # each minted rule's dynamic leaves match its OWN trigger, not the other's.
    describe_nid = _rule_node_by_id(a, "comprehend_describe_directive_graph")
    report_nid = _rule_node_by_id(a, "comprehend_report_directive_graph")
    describe_where = a.s.node(describe_nid)["attrs"]["where"]
    report_where = a.s.node(report_nid)["attrs"]["where"]
    assert describe_where["items"][0]["b"]["value"] == "describe"
    assert report_where["items"][0]["b"]["value"] == "report"
    describe_effect = a.s.node(describe_nid)["attrs"]["effect"]
    report_effect = a.s.node(report_nid)["attrs"]["effect"]
    assert describe_effect[0][3]["kind"] == "describe_scene"
    assert report_effect[0][3]["kind"] == "report_intent"

    # exercise both end-to-end.
    _make_message(a, "describe")
    _make_message(a, "report")
    for _ in range(4):
        a.s.tick()
    assert len(_goals_of_kind(a, "describe_scene")) == 1
    assert len(_goals_of_kind(a, "report_intent")) == 1
    # cross-check: a "describe" message must NOT satisfy the "report" rule and
    # vice versa -- each minted rule is genuinely independent, not a shared
    # wildcard.
    assert len(_goals_of_kind(a, "report_intent")) == 1  # not 2


def test_idempotent_reticking_does_not_duplicate(agent_with_seed):
    a = agent_with_seed
    _make_compose_request(a, "describe", "describe_scene", "comprehend_describe_directive_graph")
    _make_message(a, "describe")
    for _ in range(8):
        a.s.tick()
    n_rules_1 = len(a.s.nodes(type="Rule"))
    n_goals_1 = len(_goals_of_kind(a, "describe_scene"))
    assert n_rules_1 == 2  # meta-rule + minted
    assert n_goals_1 == 1
    for _ in range(8):
        a.s.tick()
    assert len(a.s.nodes(type="Rule")) == n_rules_1
    assert len(_goals_of_kind(a, "describe_scene")) == n_goals_1


def test_checkpoint_roundtrip_minted_and_meta_rule_survive_save_load(agent_with_seed):
    """Both the meta-rule AND the rule it minted are graph-resident Rule
    NODES -- ordinary node attrs -- so `graph_to_dict`/`graph_from_dict`
    (which serialise `inner.graph`, confirmed by reading py.rs) round-trip
    them like any other node. Loaded into a completely FRESH WorldAdapter
    (empty struct-rule store), both rules are still live purely via
    `tick()`'s `run_graph_rules` pass over the reloaded Rule nodes -- no
    re-composition, no re-mint, no Python re-authoring."""
    a = agent_with_seed
    _make_compose_request(a, "describe", "describe_scene", "comprehend_describe_directive_graph")
    for _ in range(4):
        a.s.tick()
    assert _rule_node_by_id(a, "comprehend_describe_directive_graph") is not None
    assert a.inner.rule_count() == 1  # minted rule live in A's struct store (via __mint__)

    saved = a.s.graph_to_dict()

    b = WorldAdapter(seeds=())
    assert b.inner.rule_count() == 0
    b.s.graph_from_dict(saved)
    assert b.inner.rule_count() == 0  # struct store NOT restored by graph_from_dict

    b_rule_ids = sorted(b.s.node(n)["attrs"].get("id") for n in b.s.nodes(type="Rule"))
    assert b_rule_ids == [META_RULE_ID, "comprehend_describe_directive_graph"]

    # the reloaded meta-rule's own attrs are byte-identical graph data.
    a_meta_attrs = a.s.node(_rule_node_by_id(a, META_RULE_ID))["attrs"]
    b_meta_attrs = b.s.node(_rule_node_by_id(b, META_RULE_ID))["attrs"]
    assert a_meta_attrs["match"] == b_meta_attrs["match"]
    assert a_meta_attrs["where"] == b_meta_attrs["where"]

    # exercise the reloaded minted rule -- purely from graph data, zero mint.
    _make_message(b, "describe")
    for _ in range(3):
        b.s.tick()
    goals = _goals_of_kind(b, "describe_scene")
    assert len(goals) == 1
    assert b.inner.rule_count() == 0  # confirms run_graph_rules alone did it


def test_full_load_all_seeds_still_boots_with_pilot_seed_present():
    """Regression guard: the pilot seed must not break a full boot. Mirrors
    the project's `pytest tests/ -k migrated` gate but scoped to boot only
    (fast) -- the full regression suite is run separately per CLAUDE.md."""
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=())
    report = load_all_seeds(a)
    assert report["total"] > 0
    assert SEED_ID in report["order"]
    # the pilot seed itself must not be among the failures.
    failed_ids = [f.split(":")[0] for f in report["failed"]]
    assert SEED_ID not in failed_ids
    meta_nodes = [n for n in a.s.nodes(type="Rule") if a.s.node(n)["attrs"].get("id") == META_RULE_ID]
    assert len(meta_nodes) == 1
