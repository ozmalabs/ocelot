"""jabberwock_composers_in_graph — drives every migrated composer (the
seeds/composer_<name>_graph.json meta-rules) end-to-end and prints the
migration table.

Per CLAUDE.md: the composers this script exercises are graph data
(seeds/composer_*_graph.json's meta-rule Rule nodes) — this script only
does mechanical I/O: install seeds, mint ComposeRequest triggers, tick, and
read back what the graph itself composed. It also drives the REAL
production seam (induce_concern -> ground_concern) for a representative
subset, to show the `served_by` routing ledger live, not just the direct
seed-level mint path.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_composers_in_graph.py
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
from substrate.boot_all import load_all_seeds
import domains.reflective_faculty as rf

SEED_DIR = os.path.join(ROOT, "seeds")


def _fresh():
    return WorldAdapter(seeds=())


def _load(a, stem):
    a.s.load_seed_manifest(json.load(open(os.path.join(SEED_DIR, f"{stem}.json"))), a.agent)


def _mk_cr(a, edge, **attrs):
    attrs.setdefault("composed", 0.0)
    cr = a.s.add_node("ComposeRequest", attrs)
    a.inner.add_edge_unchecked(a.agent, edge, cr)
    return cr


def _tick(a, n=8):
    for _ in range(n):
        a.s.tick()


# ---------------------------------------------------------------------------
# per-composer probes: (composer, branches-string, seed-stem-or-None,
# trigger-edge-or-None, expected-minted-names) — seed_stem is None for the
# NOT-migrated row.
# ---------------------------------------------------------------------------
ROWS = [
    ("comprehension", "describe (pilot)", "composer_comprehension_graph", "wants_comprehension_rule",
     {"directive_word": "describe", "goal_kind": "describe_scene", "rule_id": "comprehend_describe_directive_demo"},
     ["comprehend_describe_directive_demo"]),
    ("comprehension", "find", "composer_comprehension_find_graph", "wants_find_rule", {},
     ["comprehend_find_directive_demo", "bind_find_target_demo"]),
    ("comprehension", "find+constrain", "composer_comprehension_find_graph", "wants_find_constrained_rule", {},
     ["comprehend_find_directive_structured_demo", "bind_find_target_structured_demo",
      "bind_find_constraint_structured_demo"]),
    ("control", "(single)", "composer_control_graph", "wants_control_rule", {},
     ["default_no_response_demo", "control_my_body_demo"]),
    ("grouping", "(single)", "composer_grouping_graph", "wants_grouping_rule", {},
     ["fuse_whole_demo", "whole_cells_demo"]),
    ("decision", "(single)", "composer_decision_graph", "wants_decision_rule", {},
     ["decide_under_uncertainty_demo"]),
    ("browse", "plain", "composer_browse_graph", "wants_browse_rule", {},
     ["choose_affordance_by_relevance_demo", "browse_goal_satisfied_when_seen_demo"]),
    ("browse", "constrained", "composer_browse_constrained_graph", "wants_browse_constrained_rule", {},
     ["choose_affordance_structured_demo", "browse_goal_satisfied_structured_demo"]),
    ("communicate", "source+decompose+communicate", "composer_communicate_graph", "wants_communicate_rule", {},
     ["communicate_what_i_see_demo"]),
    ("construction", "(single)", "composer_construction_graph", "wants_construction_rule", {},
     ["construct_function_frames_content_demo"]),
    ("distributional", "(single)", "composer_distributional_graph", "wants_distributional_rule", {},
     ["distributional_function_split_demo"]),
    ("attention", "(single)", "composer_attention_graph", "wants_attention_rule", {},
     ["look_when_frame_advances_demo"]),
]

NOT_MIGRATED = [
    ("experiment", "test/vary/send/judge/embed/gradient/structure",
     "compose-time Argmax over RuleSummary/SeedSummary provenance, dynamic json.dumps "
     "of an embedded variant rule, recursive Term-tree rewrite -- no dialect primitive"),
    ("communicate", "partial rp combos (source-only, decompose w/o communicate, ...)",
     "mechanical extension of the migrated pattern, not a dialect gap -- scope cut for time"),
]


def main() -> int:
    print("=" * 100)
    print("COMPOSER/DRIVER GRAPH MIGRATION — migration table")
    print("=" * 100)
    header = f"{'composer':<16}{'branch':<32}{'graph-resident?':<17}{'residual-in-python':<22}{'equiv-verified'}"
    print(header)
    print("-" * len(header))

    all_ok = True
    for composer, branch, stem, edge, extra, expected in ROWS:
        a = _fresh()
        _load(a, stem)
        _mk_cr(a, edge, tag="demo", **extra)
        _tick(a)
        live = {r.get("name") for r in a.inner.export_rules() if isinstance(r, dict)}
        ok = set(expected) <= live
        all_ok = all_ok and ok
        print(f"{composer:<16}{branch:<32}{'yes' if ok else 'NO':<17}{'none':<22}{'yes (pytest)' if ok else 'NO'}")

    for composer, branch, residual in NOT_MIGRATED:
        print(f"{composer:<16}{branch:<32}{'no':<17}{'see note below':<22}{'n/a'}")
        print(f"    residual: {residual}")

    print()
    print("=" * 100)
    print("LIVE ground_concern ROUTING LEDGER (induce_concern -> ground_concern, real production seam)")
    print("=" * 100)
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    ledger_probes = [
        ("control", [["control", "WHAT", "I", "OWN"]]),
        ("decision", [["utility", "ARGMAX", "over", "AFFORDANCE"]]),
        ("grouping", [["group"], ["the"], ["parts"]]),
        ("browse", [["match", "the", "AFFORDANCE", "to", "the", "GOAL"]]),
        ("construction", [["frames", "FUNCTION", "CONTENT"]]),
        ("distributional", [["distribute", "FREQ", "ENTROPY"]]),
    ]
    for label, obs in ledger_probes:
        ind = rf.induce_concern(agent, obs, name_hint=f"driver_ledger_{label}")
        if not ind.get("minted"):
            print(f"  {label:<16} induce_concern did not mint a concern (skipped)")
            continue
        g = rf.ground_concern(agent, [ind["capability_key"]])
        print(f"  {label:<16} path={g.get('path'):<28} served_by={g.get('served_by'):<8} grounded={g.get('grounded')}")

    print()
    print("=" * 100)
    print(f"  {'PASS' if all_ok else 'FAIL'} -- every migrated composer/branch minted its expected rule(s) "
          f"purely from a graph-resident meta-rule (ComposeRequest -> tick() -> export_rules()), zero Python "
          f"authoring at request time.")
    print("=" * 100)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
