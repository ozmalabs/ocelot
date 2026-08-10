"""PILOT: the comprehension composer as PURE GRAPH DATA.

Per CLAUDE.md, the agent's authoring machinery (the `_compose_*` functions in
domains/reflective_faculty.py) is Python the agent cannot see or edit. This
pilot expresses ONE composer -- `_compose_comprehension_rule`'s describe-
branch (domains/reflective_faculty.py:1362, read-only reference, NOT edited,
NOT imported) -- as a single graph-resident Rule NODE: a meta-rule that MINTS
a NEW comprehension rule, splicing the directive word + goal kind from a
`ComposeRequest` trigger node into the minted rule's where/effect via
MkDict + Append + Attr Term composition (not a canned copy). See
tests/test_rule_minting_dialect.py for the capability envelope this design
rests on, and seeds/composer_comprehension_graph.json for the seed itself.

ZERO Python authoring happens at runtime here: this script only (1) loads the
seed (mechanical I/O), (2) creates ComposeRequest trigger nodes (mechanical
I/O -- the graph analogue of calling `_compose_comprehension_rule(agent, keys,
rels)` with an already-grounded concern), (3) calls `tick()`, and (4) reads
the graph back out to print/assert. The authoring itself -- building the
match/where/effect of the minted rule, splicing the trigger's values in, and
compiling it live -- is 100% done BY THE GRAPH (the meta-rule's own effects),
not by this script.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_composer_in_graph.py
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.world_adapter import WorldAdapter

SEED_PATH = os.path.join(ROOT, "seeds", "composer_comprehension_graph.json")


def make_compose_request(a, directive_word, goal_kind, rule_id):
    """Mechanical I/O: create the graph-analogue of an already-grounded
    comprehension concern (what `_compose_comprehension_rule(agent, keys,
    rels)` receives as its `keys`/`rels` args, translated into graph data the
    seeded meta-rule can match). No decision here -- a fixed translation."""
    cr = a.s.add_node("ComposeRequest", {
        "directive_word": directive_word,
        "goal_kind": goal_kind,
        "rule_id": rule_id,
        "composed": 0.0,
    })
    a.inner.add_edge_unchecked(a.agent, "wants_comprehension_rule", cr)
    return cr


def make_message(a, directive_word):
    """Mechanical I/O: a Message carrying one directive Mention `about` a
    Scene -- the same shape browse_dispatch's ingest_directive produces for
    the real composer's minted rule to match against."""
    msg = a.s.add_node("Message", {})
    scene = a.s.add_node("Scene", {})
    mention = a.s.add_node("Mention", {"text": directive_word})
    a.inner.add_edge_unchecked(msg, "has_mention", mention)
    a.inner.add_edge_unchecked(msg, "about", scene)
    return msg, scene, mention


def goals_of_kind(a, kind):
    return [n for n in a.s.nodes(type="Goal") if a.s.node(n)["attrs"].get("kind") == kind]


def dump_rule(a, rule_id):
    for n in a.s.nodes(type="Rule"):
        if a.s.node(n)["attrs"].get("id") == rule_id:
            return n, a.s.node(n)
    return None, None


def main() -> int:
    a = WorldAdapter(seeds=())

    print("=" * 90)
    print("COMPOSER-IN-GRAPH PILOT -- the comprehension composer as pure graph data")
    print("=" * 90)

    # 1) install the seed -- mechanical I/O (load_seed_manifest is the same
    #    Rust-native installer every seed uses; not a rule-engine call).
    manifest = json.load(open(SEED_PATH))
    load_report = a.s.load_seed_manifest(manifest, a.agent)
    print(f"\n1) INSTALLED seed '{manifest['id']}': {load_report}")

    n_rules_before = len(a.s.nodes(type="Rule"))
    print(f"   Rule nodes in graph after install: {n_rules_before} (just the meta-rule itself)")

    # Inspectability: dump the meta-rule's own node -- the composer IS this,
    # literally, graph data the agent can read like any other node.
    meta_nid, meta_node = dump_rule(a, "compose_comprehension_graph")
    print(f"\n2) THE COMPOSER IS GRAPH DATA -- meta-rule node {meta_nid}:")
    print(f"   id:    {meta_node['attrs']['id']!r}")
    print(f"   match: {meta_node['attrs']['match']!r}")
    print(f"   where: {meta_node['attrs']['where']!r}")
    print(f"   effect (first 2 of {len(meta_node['attrs']['effect'])}):")
    for eff in meta_node["attrs"]["effect"][:2]:
        print(f"     {eff!r}")

    # 3) TWO different ComposeRequests -- the same meta-rule must author TWO
    #    DIFFERENT working rules, parameterized purely from graph data.
    print("\n3) TWO DIFFERENT ComposeRequests -> the graph mints TWO DIFFERENT rules:")
    make_compose_request(a, "describe", "describe_scene", "comprehend_describe_directive_graph")
    make_compose_request(a, "report", "report_intent", "comprehend_report_directive_graph")

    for _ in range(6):
        a.s.tick()

    minted_ids = sorted(
        a.s.node(n)["attrs"].get("id") for n in a.s.nodes(type="Rule")
        if a.s.node(n)["attrs"].get("id") != "compose_comprehension_graph"
    )
    print(f"   minted rule ids: {minted_ids}")
    assert minted_ids == ["comprehend_describe_directive_graph", "comprehend_report_directive_graph"], \
        f"expected exactly the two parameterized rules, got {minted_ids}"

    for rid in minted_ids:
        nid, node = dump_rule(a, rid)
        print(f"\n   MINTED RULE '{rid}' (node {nid}):")
        print(f"     match:  {node['attrs']['match']!r}")
        print(f"     where:  {node['attrs']['where']!r}")
        print(f"     effect: {node['attrs']['effect']!r}")

    # 4) exercise BOTH minted rules end-to-end: messages -> goals.
    print("\n4) EXERCISE both minted rules end-to-end (messages -> goals):")
    make_message(a, "describe")
    make_message(a, "report")
    for _ in range(4):
        a.s.tick()

    describe_goals = goals_of_kind(a, "describe_scene")
    report_goals = goals_of_kind(a, "report_intent")
    print(f"   describe_scene Goals: {describe_goals} "
          f"{[a.s.node(g)['attrs'] for g in describe_goals]}")
    print(f"   report_intent Goals:  {report_goals} "
          f"{[a.s.node(g)['attrs'] for g in report_goals]}")

    ok = (
        minted_ids == ["comprehend_describe_directive_graph", "comprehend_report_directive_graph"]
        and len(describe_goals) == 1
        and len(report_goals) == 1
    )

    print("\n" + "=" * 90)
    print(f"  {'PASS' if ok else 'FAIL'} -- the meta-rule (graph data, no Python authoring at "
          f"runtime) composed TWO DIFFERENT parameterized comprehension rules from TWO "
          f"DIFFERENT ComposeRequest triggers, minted both live via set_rule_clause's "
          f"__mint__ path, and both fired end-to-end against real Message/Mention/Scene "
          f"data. The composer is now something the agent can dump, inspect, and (in a "
          f"follow-on) vary -- not Python source it cannot see.")
    print("=" * 90)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
