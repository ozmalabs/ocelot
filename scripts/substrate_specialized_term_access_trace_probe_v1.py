#!/usr/bin/env python3
"""Paired probes for specialized direct graph reads in term.rs."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

from substrate_rs import _native

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_specialized_term_access_trace_probe_v1_20260926.json"
V = lambda name: {"type": "Var", "name": name}
L = lambda value: {"type": "Lit", "value": value}
PICK_EDGE = {"type": "Pick", "source": {"type": "Edges", "node": V("a"), "edge_type": "probe_edge"}}
CASES = {
    "transform_decode": {"type": "TransformDecode",
                          "goal": L([["m", 3, 1]]), "codebook_type": "EvidenceAxisSample2D",
                          "max_dims": 4, "field": "explained"},
    "dim_infer": {"type": "DimInfer",
                   "goal": L([["cell", 0, 0, "red"], ["cell", 0, 1, "red"],
                              ["cell", 1, 1, "red"]]),
                   "codebook_type": "ShapeSignature", "generator_type": "DimensionGenerator",
                   "max_dims": 2, "field": "explained"},
    "gen_infer": {"type": "GenInfer",
                   "goal": L([["cell", 0, 0, "red"], ["cell", 1, 1, "red"],
                              ["cell", 2, 1, "red"], ["cell", 4, 2, "red"]]),
                   "codebook_type": "ShapeSignature", "max_dims": 2, "field": "matrix"},
    "gen_infer_scaled": {"type": "GenInfer",
                   "goal": L([["cell", 0, 0, "red"], ["cell", 2, 2, "red"],
                              ["cell", 4, 2, "red"], ["cell", 8, 4, "red"]]),
                   "codebook_type": "ShapeSignature", "max_dims": 2, "field": "matrix"},
    "gen_infer_redecode": {"type": "GenInfer",
                   "goal": L([["cell", 0, 0, "red"], ["cell", 1, 1, "red"],
                              ["cell", 2, 1, "red"], ["cell", 4, 2, "red"]]),
                   "codebook_type": "ShapeSignature", "max_dims": 2, "field": "matrix"},
    "gen_infer_noise": {"type": "GenInfer",
                   "goal": L([["cell", 0, 0, "blue"], ["cell", 0, 1, "green"],
                              ["cell", 1, 0, "yellow"], ["cell", 2, 0, "purple"]]),
                   "codebook_type": "ShapeSignature", "max_dims": 2, "field": "matrix"},
    "motor_compose": {"type": "MotorCompose", "episode": V("ep"), "policy": V("po"),
                       "candidate": V("ca")},
    "slide_neighbours": {"type": "SlideNeighbours", "cell": V("a"), "slide": L(1), "ground": L(0)},
    "nodes_where": {"type": "NodesWhere", "node_type": "Probe", "attr_key": "flag", "value": L(1)},
    "nodes_where_indexed": {"type": "NodesWhere", "node_type": "Probe", "attr_key": "flag", "value": L(1)},
    "nodes_of_type": {"type": "NodesOfType", "node_type": "Probe"},
    "scalar_attr_triples": {"type": "ScalarAttrTriples", "skip_prefix": ""},
    "attr_by_name": {"type": "Not", "arg": {"type": "AttrByName", "node": V("a"), "name": L("flag")}},
    "edge_attr": {"type": "EdgeAttr", "edge": PICK_EDGE, "key": "weight"},
    "huffman_table": {"type": "HuffmanDecodeStream", "buffer": {"type": "Attr", "node": V("b"), "key": "buf"},
                       "bitpos": L(0), "table": V("a"), "n_pairs": L(1)},
    "render_subgraph": {"type": "Render", "term": V("a"), "lang": V("b")},
    "lookahead": {"type": "LookaheadValue", "node": V("a"), "child_edge": "child",
                   "score_key": "score", "depth": L(2)},
    "enigma_crib": {"type": "EnigmaCrib", "candidate": V("a")},
    "enigma_bombe": {"type": "EnigmaBombe", "candidate": V("a")},
    "enigma_bombe_witness": {"type": "EnigmaBombeWitness", "candidate": V("a")},
    "track_identity": {
        "type": "TrackIdentityCorrespondence",
        "prev": {"type": "NodesOfType", "node_type": "PrevFrame"},
        "cur": {"type": "NodesOfType", "node_type": "CurFrame"},
        "feature_key": "features", "category_key": "kind", "extent_key": "extent",
        "radius": L(1.0),
    },
    "net_forward": {"type": "NetForward", "assemblage": V("a"), "inputs": L([2.0])},
    "future_manifold_projection": {
        "type": "FutureManifoldProjection", "episode": V("ep"), "policy": V("po"),
        "source": V("src"), "field": "resolved",
    },
    "future_manifold_selection": {
        "type": "FutureManifoldSelection", "episode": V("ep"), "policy": V("po"),
        "candidates": {"type": "NodesOfType", "node_type": "FutureCandidate"},
        "field": "selected",
    },
}
EXPECTED = {
    "transform_decode": {"term_type_read", "term_attr_read"},
    "dim_infer": {"term_type_read", "term_attr_read"},
    "gen_infer": {"term_type_read", "term_attr_read"},
    "gen_infer_scaled": {"term_type_read", "term_attr_read"},
    "gen_infer_redecode": {"term_type_read", "term_attr_read"},
    "gen_infer_noise": {"term_type_read", "term_attr_read"},
    "motor_compose": {"term_edge_read", "term_attr_read"},
    "slide_neighbours": {"term_edge_read", "term_attr_read"},
    "nodes_where": {"term_index_query", "term_type_read", "term_attr_read"},
    "nodes_where_indexed": {"term_index_query", "term_type_read", "term_attr_read"},
    "nodes_of_type": {"term_type_read"},
    "scalar_attr_triples": {"term_type_read", "term_attr_read"},
    "attr_by_name": {"term_attr_read"},
    "edge_attr": {"term_edge_read", "term_edge_attr_read"},
    "huffman_table": {"term_attr_read"},
    "render_subgraph": {"term_type_read", "term_edge_read", "term_attr_read"},
    "lookahead": {"term_attr_read", "term_edge_read"},
    "enigma_crib": {"term_attr_read"},
    "enigma_bombe": {"term_attr_read"},
    "enigma_bombe_witness": {"term_attr_read"},
    "track_identity": {"term_type_read", "term_attr_read"},
    "net_forward": {"term_edge_read", "term_attr_read"},
    "future_manifold_projection": {"term_attr_read"},
    "future_manifold_selection": {"term_type_read", "term_attr_read"},
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(case: str, traced: bool) -> dict:
    sub = _native.Substrate()
    expected_specialized_result = None
    match = ([['ep', 'uses_policy', 'po'], ['ep', 'has_source', 'src']]
             if case == "future_manifold_projection" else
             [['ep', 'uses_policy', 'po']] if case == "future_manifold_selection" else
             [['ep', 'uses_policy', 'po'], ['ep', 'has_embodied_effector_model', 'ca']]
             if case == "motor_compose" else
             [["a", "probe_edge", "b"]])
    sub.add_rule({"name": f"specialized_{case}", "match": match,
                  "where": CASES[case], "effects": []})
    if case == "huffman_table":
        a = sub.add_node("HuffmanTable", {"codes": bytes((0, 0)), "hlens": bytes((1,)),
                                           "linbits": 0, "xlen": 1})
        b = sub.add_node("Buffer", {"buf": bytes((0,))})
    elif case == "render_subgraph":
        a = sub.add_node("Term.Lit", {"value": 1})
        b = sub.add_node("Language", {})
        rule = sub.add_node("RenderRule", {"head": "Lit", "binding_pattern": ["value"]})
        template = sub.add_node("Term.Slot", {"name": "value"})
        sub.add_edge_unchecked(b, "has_rule", rule, {})
        sub.add_edge_unchecked(rule, "template", template, {})
    elif case == "track_identity":
        a = sub.add_node("PrevFrame", {"features": [0.0, 0.0], "kind": "shape", "extent": [1, 2]})
        b = sub.add_node("CurFrame", {"features": [0.1, 0.1], "kind": "shape", "extent": [2, 3]})
    elif case == "future_manifold_projection":
        a = sub.add_node("Episode", {"future_manifold_target": [[0.0], [0.0]],
                                      "future_manifold_bounds": [[1.0], [1.0]]})
        b = sub.add_node("Source", {"future_manifold_values": [[0.0], [0.5]]})
        po = sub.add_node("Policy", {"future_manifold_projection_budget": 2.0,
                                      "future_manifold_physical_horizon": 2.0})
        sub.add_edge_unchecked(a, "uses_policy", po, {})
        sub.add_edge_unchecked(a, "has_source", b, {})
    elif case == "future_manifold_selection":
        a = sub.add_node("Episode", {"future_manifold_target": [[0.0], [0.0]],
                                      "future_manifold_bounds": [[1.0], [1.0]]})
        b = sub.add_node("Policy", {"future_manifold_projection_budget": 2.0,
                                      "future_manifold_physical_horizon": 2.0})
        po = b
        sub.add_edge_unchecked(a, "uses_policy", po, {})
        sub.add_node("FutureCandidate", {"future_manifold_values": [[0.0], [0.5]],
                                         "intervention": 2.0, "goal_rank": 0.5, "withheld": 0})
        selected_candidate = sub.add_node("FutureCandidate", {
            "future_manifold_values": [[0.0], [0.25]], "intervention": 1.0,
            "goal_rank": 0.1, "withheld": 0})
        expected_specialized_result = [str(selected_candidate)]
    elif case == "motor_compose":
        a = sub.add_node("Episode", {"request_seq": 1, "state_seq": 1})
        po = sub.add_node("Policy", {})
        b = po
        ca = sub.add_node("EffectorModel", {"ordinal": 0, "experience_count": 1,
                                             "available": 1, "activation_magnitude": 0})
        sub.add_edge_unchecked(a, "uses_policy", po, {})
        sub.add_edge_unchecked(a, "has_embodied_effector_model", ca, {})
    elif case == "transform_decode":
        a = sub.add_node("Probe", {})
        b = sub.add_node("Probe", {})
        sub.add_node("EvidenceAxisSample2D", {
            "name": "held_zero", "signature": '[ ["m", 0, 0] ]',
            "dim_types": ["pred", "coord:confirm", "coord:disconfirm"]})
    elif case == "dim_infer":
        a = sub.add_node("Probe", {})
        b = sub.add_node("Probe", {})
        held = [["cell", 0, 0, "red"], ["cell", 0, 1, "red"], ["cell", 1, 0, "red"]]
        sub.add_node("ShapeSignature", {
            "name": "base_tromino", "signature": json.dumps(held),
            "kind": "faculty", "dim_types": ["pred", "coord:r", "coord:c", "val"]})
        sub.add_node("DimensionGenerator", {
            "name": "rotation90", "kind": "rotation90", "coord_dims": [1, 2],
            "params": [1, 2, 3]})
    elif case in ("gen_infer", "gen_infer_scaled", "gen_infer_redecode", "gen_infer_noise"):
        a = sub.add_node("Probe", {})
        b = sub.add_node("Probe", {})
        scale = 2 if case == "gen_infer_scaled" else 1
        held = [["cell", 0, 0, "red"], ["cell", 0, scale, "red"],
                ["cell", scale, 0, "red"], ["cell", 2 * scale, 0, "red"]]
        sub.add_node("ShapeSignature", {
            "name": "base_L", "signature": json.dumps(held), "kind": "faculty",
            "faculty": "base_L", "dim_types": ["pred", "coord:r", "coord:c", "val"]})
    else:
        attrs_a = {"flag": 0, "row": 0, "col": 0, "value": 1}
        if case.startswith("enigma_"):
            # Valid historical machine fixture from test_enigma_upgrade.py;
            # successful helper evaluation traverses all candidate attributes.
            attrs_a.update({"rotor_order": "I II III", "ring": "0 0 0", "start": "1 2 3",
                            "stationary_rotors": 0, "reflector": "YRUHQSLDPXNGOKMIEBFZCWVJAT",
                            "plugboard": "AB", "ciphertext": "LMNDSRHXDVCJEQUJ",
                            "crib": "THEQUICKBROWNFOX", "crib_offset": 0})
        a = sub.add_node("Probe", attrs_a)
        b = sub.add_node("Probe", {"flag": 1, "row": 0, "col": 1, "value": 0})
        if case == "lookahead":
            sub.set_attr(a, "score", 2)
            sub.set_attr(b, "score", 3)
    sub.add_edge_unchecked(a, "probe_edge", b, {"weight": 7})
    if case not in ("huffman_table", "render_subgraph"):
        sub.add_edge_unchecked(a, "neighbour", b, {})
        sub.add_node("Aux", {"tag": "scalar"})
    if case == "lookahead":
        sub.add_edge_unchecked(a, "child", b, {})
    if case == "net_forward":
        for order, gain, bias in ((0, 3.0, 1.0), (1, 2.0, 1.0)):
            step = sub.add_node("AssemblageStep", {"order": order, "dim_behavior": "infer"})
            sub.add_edge_unchecked(a, "has_step", step, {})
            tensors = (("W1", [[1.0]]), ("b1", [0.0]), ("W2", [[gain]]), ("b2", [bias]))
            if order == 0:
                tensors += (("loss", []),)  # interns the loss sentinel for skip-loss lookup
            for role, data in tensors:
                weight = sub.add_node("WeightTensor", {"role": role, "data": data})
                sub.add_edge_unchecked(step, "has_weight", weight, {})
    if case == "nodes_where_indexed":
        sub.declare_attr_index("Probe", "flag")
    index_active = bool(sub.has_attr_index("Probe", "flag"))
    _native.Substrate.runtime_access_trace_reset()
    _native.Substrate.runtime_access_trace_set_enabled(traced)
    outcome = sub.run_rules_report(20, False)
    terminal = sub.run_rules(1)
    events, dropped = sub.runtime_access_trace_snapshot()
    specialized_result = None
    if case.startswith("enigma_"):
        specialized_result = sub.evaluate(CASES[case], {"a": a})
    elif case == "track_identity":
        value = sub.evaluate(CASES[case], {})
        specialized_result = {key: [[str(item) for item in pair] for pair in value[key]]
                              if key == "matched" else [str(item) for item in value[key]]
                              for key in ("matched", "births", "deaths")}
    elif case == "net_forward":
        specialized_result = [float(item) for item in sub.evaluate(CASES[case], {"a": a})]
    elif case == "future_manifold_projection":
        specialized_result = float(sub.evaluate(CASES[case], {"ep": a, "po": po, "src": b}))
    elif case == "future_manifold_selection":
        specialized_result = [str(item) for item in sub.evaluate(CASES[case], {"ep": a, "po": po})]
    elif case == "motor_compose":
        specialized_result = bool(sub.evaluate(CASES[case], {"ep": a, "po": po, "ca": ca}))
    elif case == "transform_decode":
        specialized_result = float(sub.evaluate(CASES[case], {}))
    elif case == "dim_infer":
        specialized_result = float(sub.evaluate(CASES[case], {}))
    elif case in ("gen_infer", "gen_infer_scaled", "gen_infer_redecode", "gen_infer_noise"):
        matrix = [int(item) for item in sub.evaluate(CASES[case], {})]
        checked_term = {**CASES[case], "field": "checked"}
        checked = int(sub.evaluate(checked_term, {}))
        if case == "gen_infer_redecode":
            minted_name = "linear_from_gen_infer"
            sub.add_node("DimensionGenerator", {
                "name": minted_name, "kind": "linear", "coord_dims": [1, 2],
                "params": [1], "matrix": matrix})
            decode_term = {"type": "DimInfer", "goal": CASES[case]["goal"],
                           "codebook_type": "ShapeSignature",
                           "generator_type": "DimensionGenerator", "max_dims": 2,
                           "field": "explained"}
            decoded = bool(sub.evaluate(decode_term, {}))
            generator_term = {**decode_term, "field": "generator"}
            generator = sub.evaluate(generator_term, {})
            specialized_result = {"matrix": matrix, "checked": checked,
                                  "decoded": decoded, "generator": str(generator)}
        elif case == "gen_infer_noise":
            explained_term = {**CASES[case], "field": "explained"}
            explained = bool(sub.evaluate(explained_term, {}))
            specialized_result = {"matrix": matrix, "checked": checked, "explained": explained}
        else:
            specialized_result = {"matrix": matrix, "checked": checked}
    mismatches = []
    for uid, kind, node, resource, peer, count in events:
        direction = "read" if kind in {
            "pattern_edge", "term_attr_read", "term_type_read", "jit_attr_read", "jit_type_read",
            "term_edge_read", "term_edge_attr_read", "term_index_query",
        } else "write"
        key = f"{'edge' if kind in ('pattern_edge', 'term_edge_read') else 'attr' if kind in ('term_attr_read', 'jit_attr_read', 'term_edge_attr_read', 'term_index_query') else 'type'}:{resource}"
        access = next((row for row in sub.rule_access_sets() if int(sub.rule_metadata(row[0])["rule_uid"]) == uid), None)
        if access is not None:
            known = set(access[3] if direction == "read" else access[5])
            any_flag = bool(access[6] if direction == "read" else access[7])
            if resource is not None and key not in known and not any_flag:
                mismatches.append({"kind": kind, "resource": resource, "key": key})
    _native.Substrate.runtime_access_trace_set_enabled(False)
    return {"trace_enabled": traced, "progress": int(outcome["progress_steps"]),
            "status": str(outcome["status"]), "terminal_progress": int(terminal),
            "specialized_result": specialized_result,
            "expected_specialized_result": expected_specialized_result,
            "events": [list(row) for row in events], "event_count": sum(row[5] for row in events),
            "dropped": int(dropped), "static_mismatches": mismatches,
            "index_active": index_active}


def main() -> None:
    cells = []
    for case in CASES:
        plain, traced = run(case, False), run(case, True)
        kinds = {row[1] for row in traced["events"]}
        cells.append({"case": case, "expected_event_kinds": sorted(EXPECTED[case]),
                      "plain": plain, "traced": traced,
                      "outcome_match": (plain["progress"], plain["status"], plain["terminal_progress"])
                      == (traced["progress"], traced["status"], traced["terminal_progress"])
                      and plain["specialized_result"] == traced["specialized_result"],
                      "observed_kinds": sorted(kinds), "missing_expected_kinds": sorted(EXPECTED[case] - kinds)})
    checks = {
        "all_twenty_four_direct_read_fixtures_present": len(cells) == 24,
        "paired_outcomes_match_and_settle": all(c["outcome_match"] and c["traced"]["status"] == "fixed_point"
                                                 and c["traced"]["terminal_progress"] == 0 for c in cells),
        "enigma_successful_paths_return_expected_values": all(
            c["plain"]["specialized_result"] is True if c["case"] in ("enigma_crib", "enigma_bombe")
            else isinstance(c["plain"]["specialized_result"], str)
            for c in cells if c["case"].startswith("enigma_")),
        "track_identity_successful_correspondence": all(
            c["plain"]["specialized_result"] == {"matched": [["#0", "#1"]], "births": [], "deaths": []}
            for c in cells if c["case"] == "track_identity"),
        "net_forward_successful_two_step_output": all(
            c["plain"]["specialized_result"] == [15.0]
            and c["traced"]["specialized_result"] == [15.0]
            for c in cells if c["case"] == "net_forward"),
        "future_manifold_supported_projection_resolves": all(
            c["plain"]["specialized_result"] == 1.0
            and c["traced"]["specialized_result"] == 1.0
            for c in cells if c["case"] == "future_manifold_projection"),
        "future_manifold_selection_prefers_lower_intervention": all(
            c["plain"]["specialized_result"] == c["plain"]["expected_specialized_result"]
            and c["traced"]["specialized_result"] == c["traced"]["expected_specialized_result"]
            for c in cells if c["case"] == "future_manifold_selection"),
        "motor_compose_returns_paired_boolean": all(
            isinstance(c["plain"]["specialized_result"], bool)
            and c["plain"]["specialized_result"] == c["traced"]["specialized_result"]
            for c in cells if c["case"] == "motor_compose"),
        "transform_decode_explains_single_relation_delta": all(
            c["plain"]["specialized_result"] == 1.0
            and c["traced"]["specialized_result"] == 1.0
            for c in cells if c["case"] == "transform_decode"),
        "dim_infer_recognizes_generator_orbit": all(
            c["plain"]["specialized_result"] == 1.0
            and c["traced"]["specialized_result"] == 1.0
            for c in cells if c["case"] == "dim_infer"),
        "gen_infer_identifies_unimodular_matrix": all(
            c["plain"]["specialized_result"]["matrix"] == [2, 1, 1, 1]
            and c["traced"]["specialized_result"]["matrix"] == [2, 1, 1, 1]
            and c["plain"]["specialized_result"]["checked"] == 6560
            and c["traced"]["specialized_result"]["checked"] == 6560
            for c in cells if c["case"] == "gen_infer"),
        "gen_infer_scaled_search_count_matches_bound": all(
            c["plain"]["specialized_result"]["matrix"] == [2, 1, 1, 1]
            and c["traced"]["specialized_result"]["matrix"] == [2, 1, 1, 1]
            and c["plain"]["specialized_result"]["checked"] == 83520
            and c["traced"]["specialized_result"]["checked"] == 83520
            for c in cells if c["case"] == "gen_infer_scaled"),
        "gen_infer_minted_generator_redecodes": all(
            c["plain"]["specialized_result"] == c["traced"]["specialized_result"]
            and c["plain"]["specialized_result"]["matrix"] == [2, 1, 1, 1]
            and c["plain"]["specialized_result"]["checked"] == 6560
            and c["plain"]["specialized_result"]["decoded"]
            and c["plain"]["specialized_result"]["generator"] == "linear_from_gen_infer"
            for c in cells if c["case"] == "gen_infer_redecode"),
        "gen_infer_noise_is_rejected": all(
            c["plain"]["specialized_result"] == c["traced"]["specialized_result"]
            and not c["plain"]["specialized_result"]["explained"]
            and c["plain"]["specialized_result"]["matrix"] == []
            for c in cells if c["case"] == "gen_infer_noise"),
        "plain_arms_emit_no_events": all(c["plain"]["event_count"] == 0 for c in cells),
        "all_expected_event_kinds_observed": all(not c["missing_expected_kinds"] for c in cells),
        "nodes_where_indexed_and_fallback_routes_confirmed": all(
            c["traced"]["index_active"] == (c["case"] == "nodes_where_indexed")
            for c in cells if c["case"].startswith("nodes_where")),
        "trace_has_no_overflow_or_static_mismatches": all(c["traced"]["dropped"] == 0
                                                            and not c["traced"]["static_mismatches"] for c in cells),
    }
    extension = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"
    report = {"schema_version": 1, "run_id": "substrate-specialized-term-access-trace-probe-v1-20260926",
              "scope": "twenty-four paired direct graph-read probes: SlideNeighbours, indexed and fallback NodesWhere, NodesOfType, ScalarAttrTriples, AttrByName, Edges plus EdgeAttr, Huffman table access, renderer subgraph traversal, LookaheadValue recursion, successful paths for all three Enigma helper Terms, TrackIdentityCorrespondence, a successful two-step NetForward, supported FutureManifoldProjection, candidate-family FutureManifoldSelection, minimal MotorCompose, successful TransformDecode, generator-backed DimInfer, and GenInfer at two scales plus mint/redecode and value-noise control fixtures",
              "claim_boundary": "Targeted trace-site coverage only; cannot prove omitted dependencies absent or establish natural-task prevalence.",
              "environment": {"python": sys.version, "platform": platform.platform()},
              "provenance": {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                             "native_extension_sha256": sha(extension),
                             "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
                             "source_sha256": {p: sha(ROOT / p) for p in (
                                 "runners/dsl/src/access_trace.rs", "runners/dsl/src/term.rs",
                                 "runners/dsl/src/rewrite.rs", "runners/dsl/src/reflect.rs",
                                 "runners/dsl/src/net_forward.rs",
                                 "runners/dsl/src/future_manifold.rs",
                                 "runners/dsl/src/motor_compose.rs",
                                 "runners/dsl/src/shape_decode.rs",
                                 "scripts/substrate_specialized_term_access_trace_probe_v1.py")}},
              "checks": checks, "cells": cells}
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "cells": len(cells), "output": str(OUT)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("specialized Term trace probe failed")


if __name__ == "__main__":
    main()
