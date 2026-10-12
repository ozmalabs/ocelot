#!/usr/bin/env python3
"""Compare native graph mutation targets with the exact snapshot oracle."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runners/dsl/python"))
sys.path.insert(0, str(ROOT))

from domains.engine_provenance import rust_source_fingerprint  # noqa: E402
from substrate_rs import Attr, Eq, Lit, Not, Substrate, Var  # noqa: E402
from substrate_rs.ext import add_rule  # noqa: E402


CASES = {
    "add_edge": [["add_edge", "x", "derived", "y", {}]],
    "del_edge": [["del_edge", "x", "input", "y"]],
    "add_node": [["add_node", "z", "Witness", {}]],
    "del_node_with_incident_edge": [["del_node", "y"]],
    "set_attr": [["set_attr", "y", "flag", 1]],
    "replace_value": [["replace_value", "y", "x"]],
    "add_node_if_absent": [["add_node_if_absent", "z", "Witness", {"key": 1}]],
    "set_attr_if_different": [["set_attr_if_different", "y", "flag", 1]],
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_case(name: str, effects: list, observer: bool) -> dict:
    substrate = Substrate()
    src = substrate.add_node("Source", {})
    tgt = substrate.add_node("Target", {})
    substrate.add_edge_unchecked(src, "input", tgt)
    add_rule(substrate._inner, f"delta_observer_{name}", [("x", "input", "y")], effects)
    method = (
        substrate._inner.run_rules_delta_report
        if observer
        else substrate._inner.run_rules_snapshot_delta_report
    )
    report = method(1000, False)
    return {
        "status": report["status"],
        "progress_steps": report["progress_steps"],
        "node_count_after": substrate._inner.node_count(),
        "edge_exists": substrate._inner.has_edge(src, "input", tgt),
        "observer_targets": report["affected_nodes"],
        "observer_edges": report["affected_edges"],
        "exact_graph_state_diff": report["exact_graph_state_diff"],
    }


def run_ownership_case(name: str, observer: bool) -> dict:
    substrate = Substrate()
    if name == "cross_owner_edge":
        mt_a = substrate.add_node("Microtheory", {})
        mt_b = substrate.add_node("Microtheory", {})
        src = substrate.add_node("Concept", {})
        tgt = substrate.add_node("Concept", {})
        substrate.add_edge_unchecked(mt_a, "has_concept", src)
        substrate.add_edge_unchecked(mt_b, "has_concept", tgt)
        substrate.add_edge_unchecked(src, "input", tgt)
        match = [("x", "input", "y")]
        effects = [["add_edge", "x", "causal_influence", "y", {}]]
        expected = {mt_a.value, mt_b.value}
    elif name == "new_owned_concept":
        mt_a = substrate.add_node("Microtheory", {})
        src = substrate.add_node("Concept", {})
        tgt = substrate.add_node("Concept", {})
        substrate.add_edge_unchecked(mt_a, "has_concept", src)
        substrate.add_edge_unchecked(src, "input", tgt)
        match = [("x", "input", "y")]
        effects = [
            ["add_node", "z", "Concept", {}],
            ["add_edge", "mt", "has_concept", "z", {}],
        ]
        # Bind the owner Microtheory in the match as well.
        substrate.add_edge_unchecked(mt_a, "owner_driver", src)
        match.append(("mt", "owner_driver", "x"))
        expected = {mt_a.value}
    elif name == "delete_owned_concept":
        mt_a = substrate.add_node("Microtheory", {})
        src = substrate.add_node("Concept", {})
        tgt = substrate.add_node("Concept", {})
        substrate.add_edge_unchecked(mt_a, "has_concept", src)
        substrate.add_edge_unchecked(src, "input", tgt)
        match = [("x", "input", "y")]
        effects = [["del_node", "x"]]
        expected = {mt_a.value}
    elif name == "delete_microtheory_root":
        mt_a = substrate.add_node("Microtheory", {})
        concept = substrate.add_node("Concept", {})
        substrate.add_edge_unchecked(mt_a, "has_concept", concept)
        substrate.add_edge_unchecked(mt_a, "input", concept)
        match = [("mt", "input", "c")]
        effects = [["del_node", "mt"]]
        expected = {mt_a.value}
    else:
        raise ValueError(name)
    add_rule(substrate._inner, f"delta_owner_{name}", match, effects)
    method = (
        substrate._inner.run_rules_delta_report
        if observer
        else substrate._inner.run_rules_snapshot_delta_report
    )
    report = method(1000, False)
    return {
        "status": report["status"],
        "progress_steps": report["progress_steps"],
        "affected_microtheories": report["affected_microtheories"],
        "expected_microtheories": sorted(expected),
        "node_count_after": substrate._inner.node_count(),
    }


def run_deferred_identity(observer: bool) -> dict:
    substrate = Substrate()
    prev_mt = substrate.add_node("Microtheory", {})
    cur_mt = substrate.add_node("Microtheory", {})
    prev = substrate.add_node("PrevPercept", {"feat": [0.0, 0.0]})
    cur = substrate.add_node("CurPercept", {"feat": [0.05, 0.05]})
    substrate.add_edge_unchecked(prev_mt, "has_concept", prev)
    substrate.add_edge_unchecked(cur_mt, "has_concept", cur)
    anchor = substrate.add_node("Anchor", {})
    substrate.add_edge_unchecked(anchor, "has_anchor", anchor)
    add_rule(
        substrate._inner,
        "delta_deferred_track_identity",
        [("a", "has_anchor", "a")],
        [[
            "track_identity",
            {"__term__": {"type": "NodesOfType", "node_type": "PrevPercept"}},
            {"__term__": {"type": "NodesOfType", "node_type": "CurPercept"}},
            "feat", None, None, "identity", 1.0,
        ], ["set_attr", "a", "tracking_done", True]],
        where=Not(Eq(Attr(Var("a"), "tracking_done"), Lit(True))),
    )
    method = (
        substrate._inner.run_rules_delta_report
        if observer
        else substrate._inner.run_rules_snapshot_delta_report
    )
    report = method(1000, False)
    return {
        "status": report["status"],
        "progress_steps": report["progress_steps"],
        "affected_nodes": report["affected_nodes"],
        "affected_edges": report["affected_edges"],
        "affected_microtheories": report["affected_microtheories"],
        "expected_microtheories": sorted((prev_mt.value, cur_mt.value)),
        "prev_identity": substrate._inner.get_attr_many([prev], "identity")[0],
        "cur_identity": substrate._inner.get_attr_many([cur], "identity")[0],
    }


def run_scoped_cross_owner() -> dict:
    substrate = Substrate()
    mt_a = substrate.add_node("Microtheory", {})
    mt_b = substrate.add_node("Microtheory", {})
    src = substrate.add_node("Concept", {})
    tgt = substrate.add_node("Concept", {})
    substrate.add_edge_unchecked(mt_a, "has_concept", src)
    substrate.add_edge_unchecked(mt_b, "has_concept", tgt)
    substrate.add_edge_unchecked(src, "input", tgt)
    add_rule(
        substrate._inner,
        "delta_scoped_cross_owner",
        [("x", "input", "y")],
        [["add_edge", "x", "causal_influence", "y", {}]],
    )
    report = substrate._inner.run_rules_scoped_delta_report(mt_a, 1000, False)
    return {
        "progress_steps": report["progress_steps"],
        "hit_progress_budget": report["hit_progress_budget"],
        "deferred_effects_pending": report["deferred_effects_pending"],
        "affected_microtheories": report["affected_microtheories"],
        "expected_microtheories": sorted((mt_a.value, mt_b.value)),
        "affected_edges": report["affected_edges"],
        "expected_edge": [src.value, "causal_influence", tgt.value],
        "edge_exists": substrate._inner.has_edge(src, "causal_influence", tgt),
    }


def run_scoped_deferred_queue() -> dict:
    substrate = Substrate()
    mt = substrate.add_node("Microtheory", {})
    anchor = substrate.add_node("Anchor", {})
    substrate.add_node("PrevPercept", {"feat": [0.0]})
    substrate.add_node("CurPercept", {"feat": [0.0]})
    substrate.add_edge_unchecked(mt, "has_concept", anchor)
    substrate.add_edge_unchecked(anchor, "has_anchor", anchor)
    add_rule(
        substrate._inner,
        "delta_scoped_deferred_track_identity",
        [("mt", "has_concept", "a"), ("a", "has_anchor", "a")],
        [[
            "track_identity",
            {"__term__": {"type": "NodesOfType", "node_type": "PrevPercept"}},
            {"__term__": {"type": "NodesOfType", "node_type": "CurPercept"}},
            "feat", None, None, "identity", 1.0,
        ]],
    )
    report = substrate._inner.run_rules_scoped_delta_report(mt, 1, False)
    return report


def main() -> None:
    output = ROOT / "evaluation/reports/substrate_graph_delta_observer_parity_20260925.json"
    native = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"
    results = {}
    for name, effects in CASES.items():
        observed = run_case(name, effects, True)
        oracle = run_case(name, effects, False)
        observed_nodes = set(observed["observer_targets"])
        oracle_nodes = set(oracle["observer_targets"])
        observed_edges = {tuple(edge) for edge in observed["observer_edges"]}
        oracle_edges = {tuple(edge) for edge in oracle["observer_edges"]}
        gates = {
            "both_fixed_point": observed["status"] == oracle["status"] == "fixed_point",
            "same_progress_steps": observed["progress_steps"] == oracle["progress_steps"],
            "same_node_count": observed["node_count_after"] == oracle["node_count_after"],
            "oracle_nodes_covered": oracle_nodes <= observed_nodes,
            "oracle_edges_covered": oracle_edges <= observed_edges,
            "oracle_exact_flag": oracle["exact_graph_state_diff"] is True,
            "observer_conservative_flag": observed["exact_graph_state_diff"] is False,
        }
        results[name] = {"gates": gates, "observer": observed, "oracle": oracle}
        if not all(gates.values()):
            raise RuntimeError(f"mutation log failed snapshot coverage for {name}: {gates}")

    ownership_results = {}
    for name in (
        "cross_owner_edge",
        "new_owned_concept",
        "delete_owned_concept",
        "delete_microtheory_root",
    ):
        observed = run_ownership_case(name, True)
        oracle = run_ownership_case(name, False)
        gates = {
            "observer_matches_oracle": observed["affected_microtheories"]
            == oracle["affected_microtheories"],
            "observer_matches_expected": set(observed["affected_microtheories"])
            == set(observed["expected_microtheories"]),
            "oracle_matches_expected": set(oracle["affected_microtheories"])
            == set(oracle["expected_microtheories"]),
            "both_fixed_point": observed["status"] == oracle["status"] == "fixed_point",
        }
        ownership_results[name] = {"gates": gates, "observer": observed, "oracle": oracle}
        if not all(gates.values()):
            raise RuntimeError(f"Microtheory ownership mapping failed for {name}: {gates}")

    identity_observer = run_deferred_identity(True)
    identity_oracle = run_deferred_identity(False)
    identity_gates = {
        "both_fixed_point": identity_observer["status"] == identity_oracle["status"] == "fixed_point",
        "same_progress_steps": identity_observer["progress_steps"] == identity_oracle["progress_steps"],
        "oracle_nodes_covered": set(identity_oracle["affected_nodes"]) <= set(identity_observer["affected_nodes"]),
        "oracle_edges_covered": {tuple(x) for x in identity_oracle["affected_edges"]}
        <= {tuple(x) for x in identity_observer["affected_edges"]},
        "same_microtheories": identity_observer["affected_microtheories"]
        == identity_oracle["affected_microtheories"]
        == identity_observer["expected_microtheories"],
        "same_identity_assignments": identity_observer["prev_identity"]
        == identity_oracle["prev_identity"]
        and identity_observer["cur_identity"] == identity_oracle["cur_identity"],
    }
    if not all(identity_gates.values()):
        raise RuntimeError(f"deferred identity observer parity failed: {identity_gates}")

    scoped = run_scoped_cross_owner()
    scoped_gates = {
        "scope_made_progress": scoped["progress_steps"] > 0,
        "step_cap_not_hit": not scoped["hit_progress_budget"],
        "no_deferred_effects_pending": not scoped["deferred_effects_pending"],
        "both_owners_notified": scoped["affected_microtheories"] == scoped["expected_microtheories"],
        "written_edge_reported": scoped["affected_edges"] == [scoped["expected_edge"]],
        "written_edge_exists": scoped["edge_exists"],
    }
    if not all(scoped_gates.values()):
        raise RuntimeError(f"scoped cross-owner notification failed: {scoped_gates}")
    scoped_deferred = run_scoped_deferred_queue()
    scoped_deferred_gates = {
        "queue_is_reported": scoped_deferred["deferred_effects_pending"],
        "budget_exit_is_reported": scoped_deferred["hit_progress_budget"],
        "no_unsupported_frame_claim": scoped_deferred["affected_microtheories"] == [],
    }
    if not all(scoped_deferred_gates.values()):
        raise RuntimeError(f"scoped deferred queue was not surfaced: {scoped_deferred_gates}")

    report = {
        "study": "substrate_graph_delta_observer_parity",
        "date": "2026-09-25",
        "source_families": sorted(CASES),
        "runner_sha256": sha256(Path(__file__)),
        "native_sha256": sha256(native),
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
        "results": results,
        "ownership_results": ownership_results,
        "deferred_track_identity": {
            "gates": identity_gates,
            "observer": identity_observer,
            "oracle": identity_oracle,
        },
        "scoped_cross_owner": {"gates": scoped_gates, "result": scoped},
        "scoped_deferred_queue": {
            "gates": scoped_deferred_gates,
            "result": scoped_deferred,
        },
        "limits": [
            "covers eight direct graph-effect families plus deferred TrackIdentity on generated fixtures",
            "does not exercise deferred framebuffer/net/rule-edit effects, component grouping, or imported rules",
            "oracle coverage is a target superset check; it does not yet prove dependency-component frame scheduling completeness",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
