#!/usr/bin/env python3
"""Conservative checker for a finite-universe monotone mint rule fragment.

This is a syntactic sufficient condition, not a general chase/WA analyzer.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def analyze(rule_specs: list[dict[str, Any]], initial_node_ids: list[str],
            initial_edges: list[list[Any]]) -> dict[str, Any]:
    reasons: list[str] = []
    if not isinstance(rule_specs, list):
        reasons.append("rule_specs: expected a list of rule objects")
        rule_specs = []
    if not isinstance(initial_edges, list):
        reasons.append("initial_edges: expected a complete list of edge facts")
        initial_edges = []
    if (not isinstance(initial_node_ids, list)
            or any(not isinstance(node_id, str) for node_id in initial_node_ids)):
        reasons.append("initial_node_ids: expected the complete initial node-ID list")
        initial_node_ids = []
    if len(set(initial_node_ids)) != len(initial_node_ids):
        reasons.append("initial_node_ids: duplicate node IDs")
    initial_node_set = set(initial_node_ids)
    initial_nodes = len(initial_node_set)
    signatures: set[str] = set()
    edge_types: set[str] = set()
    initial_edge_attr_types: set[str] = set()
    initial_edge_keys: set[tuple[str, str, str]] = set()
    initial_edge_attrs: dict[tuple[str, str, str], dict[str, Any]] = {}
    observed_node_ids: set[str] = set()
    for ei, edge in enumerate(initial_edges):
        if (not isinstance(edge, list) or len(edge) not in (3, 4)
                or not all(isinstance(value, str) for value in edge[:3])):
            reasons.append(f"initial_edges[{ei}]: expected [source, edge_type, target] with optional attrs object")
            continue
        src, edge_type, tgt = edge[:3]
        edge_types.add(edge_type)
        edge_key = (src, edge_type, tgt)
        observed_node_ids.update((src, tgt))
        duplicate_edge = edge_key in initial_edge_keys
        if duplicate_edge:
            reasons.append(f"initial_edges[{ei}]: duplicate edge fact; provide one canonical initial fact")
        initial_edge_keys.add(edge_key)
        if len(edge) == 4:
            if not isinstance(edge[3], dict):
                reasons.append(f"initial_edges[{ei}]: attrs must be an object")
                attrs: dict[str, Any] = {}
            else:
                attrs = edge[3]
        else:
            attrs = {}
        if not all(isinstance(key, str) for key in attrs):
            reasons.append(f"initial_edges[{ei}]: attribute names must be strings")
        if duplicate_edge and initial_edge_attrs.get(edge_key) != attrs:
            reasons.append(f"initial_edges[{ei}]: duplicate edge fact has conflicting attributes")
        initial_edge_attrs[edge_key] = attrs
        if attrs:
            initial_edge_attr_types.add(edge_type)
    if not observed_node_ids <= initial_node_set:
        reasons.append("initial_edges: endpoint IDs must all occur in initial_node_ids")
    for ri, rule in enumerate(rule_specs):
        if not isinstance(rule, dict) or set(rule) - {"name", "match", "effects"}:
            reasons.append(f"rule[{ri}]: unsupported rule fields; only name, match, and effects are admitted")
            if not isinstance(rule, dict):
                continue
        match = rule.get("match")
        effects = rule.get("effects")
        if not isinstance(match, list) or not match or any(
                not isinstance(p, list) or len(p) != 3 or not all(isinstance(x, str) for x in p)
                for p in match):
            reasons.append(f"rule[{ri}]: match must be a nonempty list of positive variable edge triples")
            match_vars: set[str] = set()
        else:
            # In a rule triple, only source and target positions bind nodes;
            # the middle element is a literal edge type, never a variable.
            match_vars = {v for pattern in match for v in (pattern[0], pattern[2])}
        if not isinstance(effects, list) or not effects:
            reasons.append(f"rule[{ri}]: effects must be a nonempty list")
            continue
        available_vars = set(match_vars)
        for ei, effect in enumerate(effects):
            where = f"rule[{ri}].effects[{ei}]"
            if not isinstance(effect, list) or not effect or not isinstance(effect[0], str):
                reasons.append(f"{where}: malformed effect")
                continue
            op = effect[0]
            if op == "add_node_if_absent" and len(effect) == 4:
                _tag, newvar, node_type, attrs = effect
                if not isinstance(newvar, str) or not isinstance(node_type, str) or not isinstance(attrs, dict):
                    reasons.append(f"{where}: expected literal variable, node type, and attr object")
                    continue
                if newvar in available_vars:
                    reasons.append(f"{where}: minted variable must be fresh in the rule binding")
                    continue
                if not all(isinstance(k, str) and (v is None or isinstance(v, (bool, int, str)))
                           for k, v in attrs.items()):
                    reasons.append(f"{where}: dedup attrs must contain only finite scalar JSON literals")
                    continue
                signatures.add(json.dumps([node_type, attrs], sort_keys=True, separators=(",", ":")))
                available_vars.add(newvar)
            elif op == "add_edge" and len(effect) == 5:
                _tag, src, edge_type, tgt, attrs = effect
                if not all(isinstance(x, str) for x in (src, edge_type, tgt)) or attrs != {}:
                    reasons.append(f"{where}: only variable-endpoint, empty-attribute add_edge is allowed")
                    continue
                if src not in available_vars or tgt not in available_vars:
                    reasons.append(f"{where}: edge endpoints must be bound by the match or an earlier mint effect")
                    continue
                if edge_type in initial_edge_attr_types:
                    reasons.append(f"{where}: AddEdge may replace attributes on a pre-existing edge of this type; outside insertion-only fragment")
                    continue
                edge_types.add(edge_type)
            else:
                reasons.append(f"{where}: effect {op!r} is outside the insertion-only finite-key fragment")

    accepted = not reasons
    possible_nodes = initial_nodes + len(signatures) if accepted else None
    possible_edge_facts = possible_nodes * possible_nodes * len(edge_types) if accepted else None
    initial_edge_facts = len(initial_edge_keys)
    progress_step_upper_bound = (len(signatures) + possible_edge_facts - initial_edge_facts
                                 if accepted else None)
    return {
        "accepted": accepted,
        "fragment": "monotone_finite_key_insertions_v0",
        "reasons": reasons,
        "initial_node_ids": sorted(initial_node_set),
        "initial_node_count": initial_nodes,
        "initial_edge_fact_count": initial_edge_facts,
        "unique_mint_signatures": len(signatures) if accepted else None,
        "edge_type_count": len(edge_types) if accepted else None,
        "possible_node_count_upper_bound": possible_nodes,
        "possible_edge_fact_count_upper_bound": possible_edge_facts,
        "progress_steps_upper_bound": progress_step_upper_bound,
        "bound_basis": ("Each AddNodeIfAbsent with one fixed literal type/key signature can insert at most one node; "
                        "empty-attribute AddEdge can insert only one directed triple per endpoint pair and edge type. "
                        "Positive matching and insertion-only effects preserve a finite graph universe. The bound is "
                        "a coarse O((N+R)^2 E) upper bound on progressing firings, for fixed rules.") if accepted else None,
        "not_claimed": ["weak acyclicity", "arbitrary computed keys", "constructed fresh values", "deletion or replacement effects",
                        "hard CPU/wall-time bound", "polynomial matching cost per firing"],
    }


def self_check() -> dict[str, Any]:
    good = [{"match": [["x", "link", "y"]], "effects": [
        ["add_node_if_absent", "w", "Witness", {"tag": "shared"}],
        ["add_edge", "y", "link", "w", {}]]}]
    bad_fresh = [{"match": [["x", "link", "y"]], "effects": [
        ["add_node", "w", "Witness", {"tag": "fresh"}], ["add_edge", "y", "link", "w", {}]]}]
    bad_computed_key = [{"match": [["x", "link", "y"]], "effects": [
        ["add_node_if_absent", "w", "Witness", {"tag": {"__term__": {"type": "var", "name": "y"}}}]]}]
    bad_replace = [{"match": [["x", "link", "y"]], "effects": [["set_attr", "x", "k", 1]]}]
    bad_clause = [{"match": [["x", "link", "y"]], "where": [["external_predicate", "x"]],
                  "effects": [["add_edge", "x", "link", "y", {}]]}]
    bad_edge_type_binding = [{"match": [["x", "link", "y"]],
                              "effects": [["add_edge", "link", "next", "y", {}]]}]
    bad_edge_attr_replacement = [{"match": [["x", "link", "y"]],
                                  "effects": [["add_edge", "x", "link", "y", {}]]}]
    return {"fixtures": {
        "recursive_finite_key": analyze(good, ["n0", "n1"], [["n0", "link", "n1"]]),
        "recursive_fresh_node": analyze(bad_fresh, ["n0", "n1"], [["n0", "link", "n1"]]),
        "computed_key": analyze(bad_computed_key, ["n0", "n1"], [["n0", "link", "n1"]]),
        "replacement_effect": analyze(bad_replace, ["n0", "n1"], [["n0", "link", "n1"]]),
        "unsupported_condition_clause": analyze(bad_clause, ["n0", "n1"], [["n0", "link", "n1"]]),
        "edge_type_is_not_binding": analyze(bad_edge_type_binding, ["n0", "n1"], [["n0", "link", "n1"]]),
        "preexisting_edge_attribute_replacement": analyze(
            bad_edge_attr_replacement, ["n0", "n1"],
            [["n0", "link", "n1", {"weight": 1}]]),
        "edge_endpoint_missing_from_node_inventory": analyze(
            good, ["n0"], [["n0", "link", "n1"]]),
        "duplicate_initial_edge_fact": analyze(
            good, ["n0", "n1"], [["n0", "link", "n1"], ["n0", "link", "n1"]]),
        "duplicate_initial_node_id": analyze(good, ["n0", "n0"], []),
        "invalid_rule_specs_object": analyze({}, ["n0"], []),
        "invalid_rule_specs_string": analyze("", ["n0"], []),
        "invalid_initial_edges_object": analyze(good, ["n0"], {}),
        "invalid_initial_edges_null": analyze(good, ["n0"], None),
        "isolated_initial_node_counted": analyze(
            good, ["n0", "n1", "isolated"], [["n0", "link", "n1"]]),
    }}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, help="JSON object with rule_specs, complete initial_node_ids, initial_edges")
    ap.add_argument("--output", type=Path)
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        result = self_check()
        fixtures = result["fixtures"]
        expected = {"recursive_finite_key": True, "recursive_fresh_node": False,
                    "computed_key": False, "replacement_effect": False,
                    "unsupported_condition_clause": False,
                    "edge_type_is_not_binding": False,
                    "preexisting_edge_attribute_replacement": False,
                    "edge_endpoint_missing_from_node_inventory": False,
                    "duplicate_initial_edge_fact": False,
                    "duplicate_initial_node_id": False,
                    "invalid_rule_specs_object": False,
                    "invalid_rule_specs_string": False,
                    "invalid_initial_edges_object": False,
                    "invalid_initial_edges_null": False,
                    "isolated_initial_node_counted": True}
        result["checks_pass"] = all(fixtures[k]["accepted"] == value for k, value in expected.items())
    elif args.input:
        payload = json.loads(args.input.read_text())
        result = analyze(payload["rule_specs"], payload["initial_node_ids"], payload["initial_edges"])
    else:
        ap.error("choose --input or --self-check")
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(rendered, end="")
    return 0 if result.get("checks_pass", True) else 2


if __name__ == "__main__":
    raise SystemExit(main())
