#!/usr/bin/env python3
"""Compare suppressed effect-only Attr replay with a conservative full rescan."""
from __future__ import annotations

import hashlib
import itertools
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_effect_only_attr_replay_safety_20260925.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def var(name: str) -> dict:
    return {"type": "Var", "name": name}


def attr(node: str, key: str) -> dict:
    return {"type": "Attr", "node": var(node), "key": key}


def run_case(effect_kind: str) -> dict:
    from substrate_rs import Substrate, _native

    _native.stage_a_compare_enable(True)
    _native.stage_a_compare_reset()
    s = Substrate()
    inner = s._inner
    source = inner.add_node("ReplayRoot", {"watched": 0})
    target = inner.add_node("ReplayTarget", {})
    inner.add_edge_unchecked(source, "trigger", target, {})
    value = {"__term__": attr("x", "watched")}
    if effect_kind == "set_attr":
        reader_effect = ["set_attr", "y", "observed", value]
    elif effect_kind == "add_edge":
        reader_effect = ["add_edge", "x", "derived", "y", {"value": value}]
    elif effect_kind == "add_node":
        reader_effect = ["add_node", "born", "ReplayBorn", {"value": value}]
    else:
        raise ValueError(effect_kind)
    inner.add_rule({"name": f"effect_only_{effect_kind}_reader",
                    "match": [["x", "trigger", "y"]], "effects": [reader_effect]})
    inner.add_rule({"name": f"effect_only_{effect_kind}_writer",
                    "match": [["x", "trigger", "y"]],
                    "effects": [["set_attr", "x", "watched", 7]]})

    initial_progress = inner.run_rules(100)
    suppressed_graph = inner.graph_to_dict()
    if effect_kind == "set_attr":
        suppressed_value = next(n["attrs"].get("observed") for n in suppressed_graph["nodes"] if n["id"] == target.value)
        suppressed_expected = 7
        effect_count_before = len(suppressed_graph["nodes"])
    elif effect_kind == "add_edge":
        matching = [e for e in suppressed_graph["edges"] if e["type"] == "derived"]
        suppressed_value = matching[0]["attrs"].get("value") if matching else None
        suppressed_expected = 7
        effect_count_before = len(matching)
    else:
        matching = [n for n in suppressed_graph["nodes"] if n["type"] == "ReplayBorn"]
        suppressed_value = matching[0]["attrs"].get("value") if matching else None
        suppressed_expected = 7
        effect_count_before = len(matching)

    inner.force_all_dirty()
    full_rescan_progress = inner.run_rules(100)
    rescanned_graph = inner.graph_to_dict()
    terminal_progress = inner.run_rules(1)
    stage_a_compare = _native.stage_a_compare_stats()
    if effect_kind == "set_attr":
        rescanned_value = next(n["attrs"].get("observed") for n in rescanned_graph["nodes"] if n["id"] == target.value)
        effect_count_after = len(rescanned_graph["nodes"])
    elif effect_kind == "add_edge":
        matching = [e for e in rescanned_graph["edges"] if e["type"] == "derived"]
        rescanned_value = matching[0]["attrs"].get("value") if matching else None
        effect_count_after = len(matching)
    else:
        matching = [n for n in rescanned_graph["nodes"] if n["type"] == "ReplayBorn"]
        # The first minted result is retained to make duplicate/stale outputs visible.
        rescanned_value = [n["attrs"].get("value") for n in matching]
        effect_count_after = len(matching)
    if effect_kind == "add_node":
        rescan_matches_oracle = rescanned_value == [7]
    else:
        rescan_matches_oracle = rescanned_value == suppressed_expected
    return {
        "effect_kind": effect_kind,
        "initial_progress": initial_progress,
        "full_rescan_progress": full_rescan_progress,
        "terminal_progress": terminal_progress,
        "suppressed_value": suppressed_value,
        "expected_after_attribute_mutation": suppressed_expected,
        "suppressed_reader_is_stale": suppressed_value != suppressed_expected,
        "effect_count_before_full_rescan": effect_count_before,
        "effect_count_after_full_rescan": effect_count_after,
        "full_rescan_value": rescanned_value,
        "full_rescan_matches_single_effect_oracle": rescan_matches_oracle,
        "full_rescan_changes_graph": suppressed_graph != rescanned_graph,
        "stage_a_compare_stats": stage_a_compare,
        "graph_before_rescan": suppressed_graph,
        "graph_after_rescan": rescanned_graph,
    }


def run_multi_binding_edge_case(mixed_effects: bool = False, writer_first: bool = False) -> dict:
    """One of two reader bindings observes an attribute mutation."""
    from substrate_rs import Substrate, _native

    _native.stage_a_compare_enable(True)
    _native.stage_a_compare_reset()
    s = Substrate()
    inner = s._inner
    roots, targets = [], []
    for ordinal in range(2):
        root = inner.add_node("ReplayRoot", {"watched": 0})
        target = inner.add_node("ReplayTarget", {})
        roots.append(root)
        targets.append(target)
        inner.add_edge_unchecked(root, "trigger", target, {})
        inner.add_edge_unchecked(root, "derived", target, {"value": 0})
        if ordinal == 0:
            control = inner.add_node("ReplayControl", {})
            inner.add_edge_unchecked(root, "update", control, {})
    read_value = {"__term__": attr("x", "watched")}
    reader_effects = []
    if mixed_effects:
        reader_effects.append(["set_attr", "y", "observed", read_value])
    reader_effects.append(["add_edge", "x", "derived", "y", {"value": read_value}])
    reader_rule = {"name": "multi_binding_mixed_reader" if mixed_effects else "multi_binding_edge_reader",
                   "match": [["x", "trigger", "y"]], "effects": reader_effects}
    writer_rule = {"name": "multi_binding_edge_writer",
                   "match": [["x", "update", "z"]],
                   "effects": [["set_attr", "x", "watched", 7]]}
    for rule in ((writer_rule, reader_rule) if writer_first else (reader_rule, writer_rule)):
        inner.add_rule(rule)
    initial_progress = inner.run_rules(100)
    before = inner.graph_to_dict()
    before_values = [next(e["attrs"].get("value") for e in before["edges"]
                          if e["src"] == root and e["type"] == "derived") for root in roots]
    before_observed = [next(n["attrs"].get("observed") for n in before["nodes"]
                            if n["id"] == target) for target in targets] if mixed_effects else None
    inner.force_all_dirty()
    rescan_progress = inner.run_rules(100)
    after = inner.graph_to_dict()
    after_values = [next(e["attrs"].get("value") for e in after["edges"]
                         if e["src"] == root and e["type"] == "derived") for root in roots]
    after_observed = [next(n["attrs"].get("observed") for n in after["nodes"]
                           if n["id"] == target) for target in targets] if mixed_effects else None
    terminal_progress = inner.run_rules(1)
    return {
        "effect_kind": "mixed_effect_multi_binding_one_mutated_source" if mixed_effects else "add_edge_multi_binding_one_mutated_source",
        "reader_effects": [effect[0] for effect in reader_effects],
        "writer_rule_first": writer_first,
        "binding_count": len(roots), "mutated_source_index": 0,
        "initial_progress": initial_progress, "full_rescan_progress": rescan_progress,
        "terminal_progress": terminal_progress,
        "suppressed_values": before_values, "full_rescan_values": after_values,
        "oracle_values": [7, 0],
        "suppressed_observed_values": before_observed,
        "full_rescan_observed_values": after_observed,
        "suppressed_outputs_stale": (before_values != [7, 0]
                                      or mixed_effects and before_observed != [7, 0]),
        "full_rescan_matches_oracle": (after_values == [7, 0]
                                       and (not mixed_effects or after_observed == [7, 0])),
        "derived_edge_count_before": sum(e["type"] == "derived" for e in before["edges"]),
        "derived_edge_count_after": sum(e["type"] == "derived" for e in after["edges"]),
        "stage_a_compare_stats": _native.stage_a_compare_stats(),
        "graph_before_rescan": before, "graph_after_rescan": after,
    }


def run_multi_binding_edge_mint_case() -> dict:
    """Exercise EdgeAttrsSet alongside fresh-node undo across two bindings."""
    from substrate_rs import Substrate, _native

    _native.stage_a_compare_enable(True)
    _native.stage_a_compare_reset()
    s = Substrate()
    inner = s._inner
    roots = []
    for ordinal in range(2):
        root = inner.add_node("ReplayRoot", {"watched": 0})
        target = inner.add_node("ReplayTarget", {})
        roots.append(root)
        inner.add_edge_unchecked(root, "trigger", target, {})
        inner.add_edge_unchecked(root, "derived", target, {"value": 0})
        if ordinal == 0:
            control = inner.add_node("ReplayControl", {})
            inner.add_edge_unchecked(root, "update", control, {})
    read_value = {"__term__": attr("x", "watched")}
    inner.add_rule({"name": "multi_binding_edge_mint_reader",
                    "match": [["x", "trigger", "y"]],
                    "effects": [
                        ["add_edge", "x", "derived", "y", {"value": read_value}],
                        ["add_node", "born", "ReplayBorn", {"value": read_value}],
                    ]})
    inner.add_rule({"name": "multi_binding_edge_mint_writer",
                    "match": [["x", "update", "z"]],
                    "effects": [["set_attr", "x", "watched", 7]]})
    initial_progress = inner.run_rules(100)
    before = inner.graph_to_dict()
    before_edges = [next(e["attrs"].get("value") for e in before["edges"]
                         if e["src"] == root and e["type"] == "derived") for root in roots]
    before_mints = [n["attrs"].get("value") for n in before["nodes"] if n["type"] == "ReplayBorn"]
    inner.force_all_dirty()
    rescan_progress = inner.run_rules(100)
    after = inner.graph_to_dict()
    after_edges = [next(e["attrs"].get("value") for e in after["edges"]
                        if e["src"] == root and e["type"] == "derived") for root in roots]
    after_mints = [n["attrs"].get("value") for n in after["nodes"] if n["type"] == "ReplayBorn"]
    terminal_progress = inner.run_rules(1)
    return {
        "effect_kind": "multi_binding_edge_attribute_and_fresh_mint",
        "binding_count": 2, "mutated_source_index": 0,
        "initial_progress": initial_progress, "full_rescan_progress": rescan_progress,
        "terminal_progress": terminal_progress,
        "suppressed_edge_values": before_edges, "full_rescan_edge_values": after_edges,
        "mint_values_before_full_rescan": before_mints,
        "mint_values_after_full_rescan": after_mints,
        "edge_oracle_values": [7, 0],
        "edge_output_matches_oracle": after_edges == [7, 0],
        "mint_count_before": len(before_mints), "mint_count_after": len(after_mints),
        "stage_a_compare_stats": _native.stage_a_compare_stats(),
        "graph_before_rescan": before, "graph_after_rescan": after,
    }


def run_three_rule_order_cases() -> list[dict]:
    """All permutations of one effect-only reader and two competing writers."""
    from substrate_rs import Substrate, _native

    _native.stage_a_compare_enable(False)
    outcomes = []
    for order in itertools.permutations(("reader", "writer_3", "writer_7")):
        s = Substrate()
        inner = s._inner
        source = inner.add_node("OrderRoot", {"watched": 0})
        target = inner.add_node("OrderTarget", {})
        control_3 = inner.add_node("OrderControl", {})
        control_7 = inner.add_node("OrderControl", {})
        inner.add_edge_unchecked(source, "trigger", target, {})
        inner.add_edge_unchecked(source, "update_3", control_3, {})
        inner.add_edge_unchecked(source, "update_7", control_7, {})
        value = {"__term__": attr("x", "watched")}
        rules = {
            "reader": {"name": "order_reader", "match": [["x", "trigger", "y"]],
                       "effects": [["set_attr", "y", "observed", value]]},
            "writer_3": {"name": "order_writer_3", "match": [["x", "update_3", "z"]],
                         "effects": [["set_attr", "x", "watched", 3]]},
            "writer_7": {"name": "order_writer_7", "match": [["x", "update_7", "z"]],
                         "effects": [["set_attr", "x", "watched", 7]]},
        }
        for name in order:
            inner.add_rule(rules[name])
        progress = inner.run_rules(100)
        graph = inner.graph_to_dict()
        final_source = next(n for n in graph["nodes"] if n["id"] == source.value)
        final_target = next(n for n in graph["nodes"] if n["id"] == target.value)
        expected = final_source["attrs"]["watched"]
        observed = final_target["attrs"].get("observed")
        terminal = inner.run_rules(1)
        outcomes.append({
            "effect_kind": "three_rule_order_permutation",
            "rule_order": list(order), "progress": progress,
            "final_watched": expected, "reader_observed": observed,
            "reader_matches_final_graph_oracle": observed == expected,
            "terminal_progress": terminal, "graph": graph,
        })
    return outcomes


def run_predicate_withdrawal_case() -> dict:
    """Check whether a derived edge is retracted after its guard turns false."""
    from substrate_rs import Substrate, _native

    _native.stage_a_compare_enable(False)
    s = Substrate()
    inner = s._inner
    source = inner.add_node("WithdrawalRoot", {"enabled": 1})
    target = inner.add_node("WithdrawalTarget", {})
    control = inner.add_node("WithdrawalControl", {})
    inner.add_edge_unchecked(source, "trigger", target, {})
    inner.add_edge_unchecked(source, "update", control, {})
    inner.add_rule({
        "name": "guarded_edge_reader",
        "match": [["x", "trigger", "y"]],
        "where": {"type": "Gt", "a": attr("x", "enabled"), "b": {"type": "Lit", "value": 0}},
        "effects": [["add_edge", "x", "derived", "y", {}]],
    })
    inner.add_rule({"name": "disable_guard", "match": [["x", "update", "z"]],
                    "effects": [["set_attr", "x", "enabled", 0]]})
    progress = inner.run_rules(100)
    after_transition = inner.graph_to_dict()
    enabled = next(n["attrs"]["enabled"] for n in after_transition["nodes"] if n["id"] == source.value)
    edge_count = sum(e["type"] == "derived" for e in after_transition["edges"])
    expected_edge_count = 1 if enabled > 0 else 0
    inner.force_all_dirty()
    rescan_progress = inner.run_rules(100)
    after_rescan = inner.graph_to_dict()
    rescan_edge_count = sum(e["type"] == "derived" for e in after_rescan["edges"])
    terminal = inner.run_rules(1)
    return {
        "effect_kind": "predicate_guard_withdrawal",
        "progress": progress, "enabled_after_transition": enabled,
        "derived_edges_after_transition": edge_count,
        "oracle_derived_edge_count": expected_edge_count,
        "output_withdrawal_matches_oracle": edge_count == expected_edge_count,
        "full_rescan_progress": rescan_progress,
        "derived_edges_after_full_rescan": rescan_edge_count,
        "stale_output_survives_full_rescan": rescan_edge_count != expected_edge_count,
        "terminal_progress": terminal,
        "graph_after_transition": after_transition,
        "graph_after_full_rescan": after_rescan,
    }


def run_binding_scale_order_cases(binding_count: int) -> list[dict]:
    """All rule permutations as independent reader binding count increases."""
    from substrate_rs import Substrate, _native

    _native.stage_a_compare_enable(False)
    outcomes = []
    for order in itertools.permutations(("reader", "writer_3", "writer_7")):
        s = Substrate()
        inner = s._inner
        roots, targets = [], []
        controls = []
        for ordinal in range(binding_count):
            root = inner.add_node("TwoOrderRoot", {"watched": 0})
            target = inner.add_node("TwoOrderTarget", {})
            roots.append(root)
            targets.append(target)
            inner.add_edge_unchecked(root, "trigger", target, {})
            if ordinal < 2:
                control = inner.add_node("TwoOrderControl", {})
                controls.append(control)
                inner.add_edge_unchecked(root, "update_3" if ordinal == 0 else "update_7", control, {})
        value = {"__term__": attr("x", "watched")}
        rules = {
            "reader": {"name": "two_order_reader", "match": [["x", "trigger", "y"]],
                       "effects": [["set_attr", "y", "observed", value]]},
            "writer_3": {"name": "two_order_writer_3", "match": [["x", "update_3", "z"]],
                         "effects": [["set_attr", "x", "watched", 3]]},
            "writer_7": {"name": "two_order_writer_7", "match": [["x", "update_7", "z"]],
                         "effects": [["set_attr", "x", "watched", 7]]},
        }
        for name in order:
            inner.add_rule(rules[name])
        progress = inner.run_rules(100)
        graph = inner.graph_to_dict()
        final = [next(n["attrs"]["watched"] for n in graph["nodes"] if n["id"] == root.value)
                 for root in roots]
        observed = [next(n["attrs"].get("observed") for n in graph["nodes"] if n["id"] == target.value)
                    for target in targets]
        terminal = inner.run_rules(1)
        mismatch_count = sum(output != expected for output, expected in zip(observed, final))
        outcomes.append({
            "effect_kind": "binding_scale_three_rule_order_permutation",
            "binding_count": binding_count,
            "rule_order": list(order), "progress": progress,
            "final_watched": final, "reader_observed": observed,
            "reader_matches_final_graph_oracle": observed == final,
            "reader_mismatch_count": mismatch_count,
            "reader_mismatch_fraction": mismatch_count / binding_count,
            "terminal_progress": terminal, "graph": graph,
        })
    return outcomes


def run_explicit_retraction_cases() -> list[dict]:
    """Explicit del_edge paired with guard disable under both rule orders."""
    from substrate_rs import Substrate, _native

    _native.stage_a_compare_enable(False)
    outcomes = []
    for order in (("reader", "disable_and_retract"), ("disable_and_retract", "reader")):
        s = Substrate()
        inner = s._inner
        source = inner.add_node("ExplicitRetractRoot", {"enabled": 1})
        target = inner.add_node("ExplicitRetractTarget", {})
        inner.add_edge_unchecked(source, "trigger", target, {})
        rules = {
            "reader": {
                "name": "explicit_retract_guarded_reader",
                "match": [["x", "trigger", "y"]],
                "where": {"type": "Gt", "a": attr("x", "enabled"), "b": {"type": "Lit", "value": 0}},
                "effects": [["add_edge", "x", "derived", "y", {}]],
            },
            "disable_and_retract": {
                "name": "explicit_disable_and_retract",
                "match": [["x", "trigger", "y"]],
                "effects": [
                    ["set_attr", "x", "enabled", 0],
                    ["del_edge", "x", "derived", "y"],
                ],
            },
        }
        for name in order:
            inner.add_rule(rules[name])
        progress = inner.run_rules(100)
        graph = inner.graph_to_dict()
        enabled = next(n["attrs"]["enabled"] for n in graph["nodes"] if n["id"] == source.value)
        derived = sum(e["type"] == "derived" for e in graph["edges"])
        terminal = inner.run_rules(1)
        outcomes.append({
            "effect_kind": "explicit_predicate_output_retraction",
            "rule_order": list(order), "progress": progress,
            "enabled": enabled, "derived_edge_count": derived,
            "oracle_derived_edge_count": 0,
            "matches_oracle": enabled == 0 and derived == 0,
            "terminal_progress": terminal, "graph": graph,
        })
    return outcomes


def main() -> None:
    from substrate_rs import _native

    cases = [run_case(kind) for kind in ("set_attr", "add_edge", "add_node")]
    multi_binding = run_multi_binding_edge_case()
    cases.append(multi_binding)
    mixed_multi_binding = run_multi_binding_edge_case(mixed_effects=True)
    cases.append(mixed_multi_binding)
    edge_mint_multi_binding = run_multi_binding_edge_mint_case()
    cases.append(edge_mint_multi_binding)
    writer_first = run_multi_binding_edge_case(writer_first=True)
    cases.append(writer_first)
    order_permutations = run_three_rule_order_cases()
    cases.extend(order_permutations)
    order_binding_counts = (2, 4, 8, 16, 32)
    two_binding_order_permutations = [
        row for binding_count in order_binding_counts
        for row in run_binding_scale_order_cases(binding_count)
    ]
    cases.extend(two_binding_order_permutations)
    withdrawal = run_predicate_withdrawal_case()
    cases.append(withdrawal)
    explicit_retractions = run_explicit_retraction_cases()
    cases.extend(explicit_retractions)
    checks = {
        "all_single_binding_suppressed_readers_expose_stale_input": all(
            c["suppressed_reader_is_stale"] for c in cases[:3]),
        "set_attr_full_rescan_is_single_effect_correct": cases[0]["full_rescan_matches_single_effect_oracle"],
        "add_edge_full_rescan_is_single_effect_correct": cases[1]["full_rescan_matches_single_effect_oracle"],
        "add_node_full_rescan_exposes_duplicate_and_stale_result": (
            not cases[2]["full_rescan_matches_single_effect_oracle"]
            and cases[2]["effect_count_after_full_rescan"] == cases[2]["effect_count_before_full_rescan"] + 1
            and cases[2]["full_rescan_value"] == [0, 7]),
        "add_edge_attribute_replacement_counts_as_progress": cases[1]["full_rescan_progress"] > 0,
        "edge_and_mint_undo_consumers_compare_without_divergence": all(
            cases[i]["stage_a_compare_stats"]["compared_drains"] > 0
            and cases[i]["stage_a_compare_stats"]["diverged_drains"] == 0
            and cases[i]["stage_a_compare_stats"]["unsound_drains"] == 0
            for i in (1, 2)),
        "multi_binding_edge_replay_matches_oracle_without_duplication": (
            multi_binding["suppressed_outputs_stale"]
            and multi_binding["full_rescan_matches_oracle"]
            and multi_binding["derived_edge_count_before"] == multi_binding["derived_edge_count_after"] == 2
            and multi_binding["stage_a_compare_stats"]["compared_drains"] > 0
            and multi_binding["stage_a_compare_stats"]["diverged_drains"] == 0
            and multi_binding["stage_a_compare_stats"]["unsound_drains"] == 0),
        "multi_binding_mixed_effects_refresh_without_duplication": (
            mixed_multi_binding["suppressed_outputs_stale"]
            and mixed_multi_binding["full_rescan_matches_oracle"]
            and mixed_multi_binding["derived_edge_count_before"] == mixed_multi_binding["derived_edge_count_after"] == 2
            and mixed_multi_binding["stage_a_compare_stats"]["compared_drains"] == 0),
        "multi_binding_edge_and_mint_undo_compares_without_divergence": (
            edge_mint_multi_binding["edge_output_matches_oracle"]
            and edge_mint_multi_binding["mint_count_before"] == 2
            and edge_mint_multi_binding["mint_count_after"] == 4
            and edge_mint_multi_binding["stage_a_compare_stats"]["compared_drains"] > 0
            and edge_mint_multi_binding["stage_a_compare_stats"]["diverged_drains"] == 0
            and edge_mint_multi_binding["stage_a_compare_stats"]["unsound_drains"] == 0),
        "rule_order_changes_initial_staleness_as_predicted": (
            multi_binding["suppressed_values"] == [0, 0]
            and writer_first["suppressed_values"] == [7, 0]
            and writer_first["full_rescan_matches_oracle"]),
        "all_three_rule_order_permutations_match_or_miss_oracle_explicitly": (
            len(order_permutations) == 6
            and all(c["terminal_progress"] == 0 for c in order_permutations)
            and sum(not c["reader_matches_final_graph_oracle"] for c in order_permutations) == 4),
        "binding_scale_order_sweep_records_staleness_by_permutation": (
            len(two_binding_order_permutations) == len(order_binding_counts) * 6
            and all(c["terminal_progress"] == 0 for c in two_binding_order_permutations)
            and all(sum(not c["reader_matches_final_graph_oracle"] for c in two_binding_order_permutations
                        if c["binding_count"] == n) == 4 for n in order_binding_counts)),
        "false_guard_does_not_implicitly_withdraw_prior_effect": (
            withdrawal["enabled_after_transition"] == 0
            and withdrawal["derived_edges_after_transition"] == 1
            and withdrawal["derived_edges_after_full_rescan"] == 1
            and withdrawal["terminal_progress"] == 0),
        "explicit_delete_retracts_guarded_output_in_both_orders": (
            len(explicit_retractions) == 2
            and all(c["matches_oracle"] and c["terminal_progress"] == 0 for c in explicit_retractions)),
        "all_cases_settle_after_rescan": all(c["terminal_progress"] == 0 for c in cases),
    }
    ext_path = Path(_native.__file__).resolve()
    payload = {
        "schema_version": 1,
        "run_id": "substrate-effect-only-attr-replay-safety-20260925",
        "scope": "controlled single- and two-binding replay/undo cases, six permutations of three-rule competing-writer graphs at 1, 2, 4, 8, 16, and 32 reader bindings, and automatic versus explicit false-predicate output withdrawal",
        "claim_boundary": "Small deterministic mechanism probe. Full rescan is a diagnostic stress of replay safety, not a recommended scheduler policy. Order evidence covers one graph generator through 32 bindings; arbitrary workloads, larger rule sets, concurrent frames, and authored tasks remain untested.",
        "environment": {"python": sys.version, "platform": platform.platform()},
        "provenance": {
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
            "native_extension_path": str(ext_path),
            "native_extension_sha256": sha(ext_path),
            "source_sha256": {
                "harness": sha(Path(__file__).resolve()),
                "substrate": sha(ROOT / "runners/dsl/src/substrate.rs"),
                "rewrite": sha(ROOT / "runners/dsl/src/rewrite.rs"),
                "stage_a": sha(ROOT / "runners/dsl/src/stage_a.rs"),
                "py_binding": sha(ROOT / "runners/dsl/src/py.rs"),
                "native_build_manifest": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
            },
        },
        "checks": checks,
        "cases": cases,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"checks": checks, "output": str(OUT)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("effect-only replay safety probe failed")


if __name__ == "__main__":
    main()
