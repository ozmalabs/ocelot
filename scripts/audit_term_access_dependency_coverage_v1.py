#!/usr/bin/env python3
"""Generate a source crosswalk for Term variants and rule access derivation."""
from __future__ import annotations

import hashlib
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TERM = ROOT / "runners/dsl/src/term.rs"
REWRITE = ROOT / "runners/dsl/src/rewrite.rs"
TRACE = ROOT / "runners/dsl/src/access_trace.rs"
OUT = ROOT / "evaluation/reports/term_access_dependency_coverage_v1_20260928.json"

# These are source-identified graph-reading helper families reviewed for the
# preceding Term access audit. All remaining variants are explicitly labeled
# unreviewed; presence in the list is not inferred from names.
REVIEWED_DYNAMIC = {
    "ShapeDecode": "shape_decode.rs::eval_shape_decode; codebook node and attribute scans",
    "TransformDecode": "shape_decode.rs::eval_transform_decode; held codebook scans",
    "DimInfer": "shape_decode.rs::eval_dim_infer; codebook scans",
    "GenInfer": "shape_decode.rs::eval_gen_infer; codebook/generator scans",
    "RatioInduce": "shape_decode.rs::eval_ratio_infer; source-audited conservative family",
    "TimeInfer": "shape_decode.rs::eval_time_infer; source-audited conservative family",
    "DepthInfer": "shape_decode.rs::eval_depth_infer; source-audited conservative family",
    "BlinkBridge": "shape_decode.rs::eval_blink_bridge; source-audited conservative family",
    "GapAbduce": "shape_decode.rs::eval_gap_abduce; source-audited conservative family",
    "GapVerify": "shape_decode.rs::eval_gap_verify; source-audited conservative family",
    "SupportInfer": "shape_decode.rs::eval_support_infer; source-audited conservative family",
    "TransferDecode": "shape_decode.rs::eval_transfer_decode; registry/mechanism reads",
    "RecogniseShape": "shape_decode.rs::eval_recognise_shape; cue/codebook population reads",
    "MetaShapeMint": "shape_decode.rs::eval_meta_shape_mint; MetaShape/observation scans",
    "Join": "term.rs::render_source_node; graph-backed render rule resolution for Node elements",
    "ProgEval": "prog_eval.rs::eval_prog_eval; Node-backed programs are decoded from graph subgraphs",
    "Call": "term.rs::TermNode::Call; evaluates a derived body selected at runtime",
    "Holds": "term.rs::TermNode::Holds; evaluates a concept body selected through ConceptResolver",
    "UseTool": "term.rs::TermNode::UseTool; reentrant registered host handler with opaque dependencies",
    "Render": "term.rs::render_source_node; graph-backed render rule resolution",
    "MotorCompose": "motor_compose.rs helper receives EvalCtx graph",
    "FutureManifoldProjection": "future_manifold.rs helper receives EvalCtx graph",
    "FutureManifoldSelection": "future_manifold.rs helper receives EvalCtx graph",
    "NetForward": "net_forward.rs helper receives EvalCtx graph",
    "EnigmaCrib": "enigma.rs helper receives graph",
    "EnigmaBombe": "enigma.rs helper receives graph",
    "EnigmaBombeWitness": "enigma.rs helper receives graph",
    "TrackIdentityCorrespondence": "identity helper receives EvalCtx graph",
    "HuffmanDecodeStream": "term.rs table-node attribute reads",
    "HuffmanEncodeStream": "term.rs table-node attribute reads",
    "EvalSubgraph": "reflect.rs::term_from_subgraph decodes a graph-resident Term subtree",
    "ReadFile": "term.rs::TermNode::ReadFile calls std::fs::read_to_string directly; filesystem state is outside graph RuleKey tracking",
    "ProgCallExtern": "prog_eval.rs::eval_expr gates Program IR calls on caller-declared names and executes the in-engine native oracle whitelist; standalone Term arm returns None",
}

REVIEWED_ACCESS_BRANCH = {
    "Attr": "finite node-attribute key is encoded by the Term",
    "TypeOf": "runtime-selected node type; conservative reads_any",
    "NodesOfType": "finite node type key",
    "NodesWhere": "finite node type and node-attribute keys, including index fallback",
    "ReachableFrom": "finite edge key or reads_any for any-type traversal",
    "Neighbours": "finite edge key or reads_any for any-type traversal",
    "InNeighbours": "finite edge key or reads_any for any-type traversal",
    "SlideNeighbours": "graph neighborhood traversal with derived lattice reads",
    "MapNeighbours": "finite edge key or reads_any for any-type traversal",
    "Edges": "finite edge key or reads_any for any-type traversal",
    "EdgeAttr": "edge-attribute storage is not a node Attr key; reads_any",
    "AttrByName": "runtime-computed attribute name; reads_any",
    "ScalarAttrTriples": "whole-graph type and scalar-attribute scan; reads_any",
    "LookaheadValue": "finite child-edge and score-attribute keys",
    "ParetoDominates": "finite two-edge and three-attribute key set",
}

EXTERNAL_DEPENDENCIES = {
    "ReadFile": "host filesystem read; not a graph RuleKey dependency",
    "UseTool": "registered host handler may read/write external state or reenter substrate",
    "ProgCallExtern": "Program IR call gated by caller-declared oracle names and implemented by the in-engine native oracle whitelist; no dynamic host callback in the current interpreter",
}

TRACE_WRAPPER_CODES = {
    "note_out_edges": [14],
    "note_in_edges": [14],
    "note_node_type_and_attrs": [2, 3],
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def enum_variants(source: str) -> list[tuple[str, int]]:
    start = source.index("pub enum TermNode {")
    end = source.index("\n}\n", start)
    result = []
    for lineno, line in enumerate(source[start:end].splitlines(), 1):
        match = re.match(r"^    ([A-Z][A-Za-z0-9_]*)\s*(?:\{|,)$", line)
        if match:
            # Recover file line numbers from the prefix, not the enum-local line.
            file_line = source[:start].count("\n") + lineno
            result.append((match.group(1), file_line))
    return result


def collector_branches(source: str) -> dict[str, tuple[str, int]]:
    start = source.index("fn collect_term_reads(")
    end = source.index("/// Collect one effect's writes", start)
    body = source[start:end]
    lines = body.splitlines()
    starts = [i for i, line in enumerate(lines)
              if re.match(r"^        T::[A-Za-z0-9_]+", line)]
    branches: dict[str, tuple[str, int]] = {}
    for n, i in enumerate(starts):
        j = starts[n + 1] if n + 1 < len(starts) else len(lines)
        block = "\n".join(lines[i:j])
        first = re.match(r"^        T::([A-Za-z0-9_]+)", lines[i])
        if not first:
            continue
        variants = set(re.findall(r"\bT::([A-Za-z0-9_]+)", block))
        has_wildcard = "*reads_any = true" in block
        has_finite = "reads.insert(RuleKey::" in block
        if has_wildcard and has_finite:
            access_class = "conditional_finite_or_wildcard"
        elif has_wildcard:
            access_class = "wildcard_reads_any"
        elif has_finite:
            access_class = "finite_resource_keys"
        else:
            access_class = "explicit_child_walk_only"
        line_number = source[:start].count("\n") + i + 1
        for variant in variants:
            branches[variant] = (access_class, line_number)
    return branches


def evaluator_helper_paths(source: str, start: int, end: int) -> dict[str, dict]:
    """Associate variants with crate-qualified helpers in their evaluator arm."""
    lines = source[start:end].splitlines()
    arm_starts = [i for i, line in enumerate(lines)
                  if re.match(r"^        TermNode::[A-Za-z0-9_]+", line)]
    result: dict[str, dict] = {}
    for n, i in enumerate(arm_starts):
        j = arm_starts[n + 1] if n + 1 < len(arm_starts) else len(lines)
        block_lines = lines[i:j]
        block = "\n".join(block_lines)
        arm_pattern = "\n".join(block_lines[: next((k + 1 for k, line in enumerate(block_lines) if "=>" in line), 1)])
        variants = set(re.findall(r"\bTermNode::([A-Za-z0-9_]+)", arm_pattern))
        helpers = sorted(set(re.findall(r"\b(crate::[A-Za-z0-9_]+(?:::[A-Za-z0-9_]+)+)(?=\s*\()", block)))
        direct_trace_codes = {int(code) for code in re.findall(r"access_trace::note\s*\(\s*(\d+)", block)}
        for wrapper, codes in TRACE_WRAPPER_CODES.items():
            if f"access_trace::{wrapper}" in block:
                direct_trace_codes.update(codes)
        # This is intentionally a candidate signal: nested child evaluation
        # also carries ctx, so a helper path still requires source review.
        carries_context = "ctx.graph" in block or (bool(helpers) and re.search(r"\bctx\b", block) is not None)
        for variant in variants:
            result[variant] = {
                "crate_helper_paths": helpers,
                "direct_graph_access": "ctx.graph" in block,
                "direct_trace_event_codes": sorted(direct_trace_codes),
                "graph_or_eval_context_present": bool(carries_context),
                "evaluator_arm_line": source[:start].count("\n") + i + 1,
            }
    return result


_FUNCTION_INDEX_CACHE: dict[str, dict[str, tuple[str, int]]] = {}


def function_index(source: str, key: str) -> dict[str, tuple[str, int]]:
    if key in _FUNCTION_INDEX_CACHE:
        return _FUNCTION_INDEX_CACHE[key]
    pattern = re.compile(r"(?m)^(?:pub(?:\([^)]*\))?\s+)?fn\s+([A-Za-z0-9_]+)\s*\(")
    starts = list(pattern.finditer(source))
    found = {}
    for i, match in enumerate(starts):
        stop = starts[i + 1].start() if i + 1 < len(starts) else len(source)
        found[match.group(1)] = (source[match.start():stop], source[:match.start()].count("\n") + 1)
    _FUNCTION_INDEX_CACHE[key] = found
    return found


def inspect_helper(path: str, depth: int = 4, seen: frozenset[str] = frozenset()) -> dict:
    parts = path.split("::")
    if len(parts) < 3 or path in seen or depth < 0:
        return {"source_found": False, "path": path}
    helper_file = ROOT / "runners/dsl/src" / (parts[1] + ".rs")
    if not helper_file.exists():
        return {"source_found": False, "path": path, "source_path": str(helper_file.relative_to(ROOT))}
    source = helper_file.read_text()
    name = parts[-1]
    source_key = str(helper_file)
    all_functions = function_index(source, source_key)
    function = all_functions.get(name)
    if function is None:
        return {"source_found": False, "path": path, "source_path": str(helper_file.relative_to(ROOT))}
    body, line = function
    direct_graph = bool(re.search(
        r"\bctx\.graph\b|\bgraph\.(?:node|nodes|nodes_of_type|nodes_where|edge|edges|out_edges|in_edges|neighbours|edge_idx|iter_nodes)\b",
        body,
    ))
    direct_trace = "access_trace::" in body
    function_names = set(all_functions)
    local_calls = set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", body)) & function_names
    qualified_calls = set(re.findall(r"\b(crate::[A-Za-z0-9_]+(?:::[A-Za-z0-9_]+)+)(?=\s*\()", body))
    children = []
    carries_graph_context = bool(re.search(r"\bctx\b|\bgraph\b|TypedGraph", body))
    if depth and carries_graph_context:
        for child in sorted(qualified_calls)[:12]:
            evidence = inspect_helper(child, depth - 1, seen | {path})
            if evidence.get("source_found"):
                children.append(evidence)
        for child in sorted(local_calls - {name})[:12]:
            evidence = inspect_helper(f"crate::{parts[1]}::{child}", depth - 1, seen | {path})
            if evidence.get("source_found"):
                children.append(evidence)
    own_codes = {int(code) for code in re.findall(r"access_trace::note\s*\(\s*(\d+)", body)}
    own_codes.update(TRACE_WRAPPER_CODES.get(name, []))
    propagated_codes = set(own_codes)
    for child in children:
        propagated_codes.update(child.get("trace_event_codes", []))
    return {
        "source_found": True,
        "path": path,
        "source_path": str(helper_file.relative_to(ROOT)),
        "source_line": line,
        "direct_graph_access": direct_graph,
        "transitive_graph_access": direct_graph or any(x.get("transitive_graph_access", x.get("direct_graph_access", False)) for x in children),
        "runtime_trace_site": direct_trace or any(x.get("runtime_trace_site", False) for x in children),
        "trace_event_codes": sorted(propagated_codes),
        "eval_context_parameter_or_use": bool(re.search(r"\bEvalCtx\b|\bctx\b", body)),
        "callee_evidence": children,
        "source_digest": hashlib.sha256(body.encode()).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUT,
                        help="output JSON path (defaults to the historical v1 path)")
    args = parser.parse_args()
    term_source = TERM.read_text()
    rewrite_source = REWRITE.read_text()
    trace_source = TRACE.read_text()
    variants = enum_variants(term_source)
    branches = collector_branches(rewrite_source)
    eval_start = term_source.index("pub fn evaluate(")
    eval_end = term_source.index("fn python_repr(", eval_start)
    eval_body = term_source[eval_start:eval_end]
    eval_variants = set(re.findall(r"\bTermNode::([A-Za-z0-9_]+)", eval_body))
    helper_map = evaluator_helper_paths(term_source, eval_start, eval_end)
    helper_evidence = sorted({path for item in helper_map.values() for path in item["crate_helper_paths"]})
    helper_inspections = {path: inspect_helper(path) for path in helper_evidence}
    child_start = term_source.index("pub(crate) fn children(")
    child_end = term_source.index("\n}\n", child_start) + 2
    child_body = term_source[child_start:child_end]
    child_variants = set(re.findall(r"\bTermNode::([A-Za-z0-9_]+)", child_body))
    rows = []
    for name, line in variants:
        access_class, collector_line = branches.get(name, ("generic_children_fallback", None))
        review = REVIEWED_DYNAMIC.get(name) or REVIEWED_ACCESS_BRANCH.get(name) or "unreviewed"
        helper_paths = helper_map.get(name, {}).get("crate_helper_paths", [])
        graph_helper_paths = [path for path in helper_paths
                              if helper_inspections.get(path, {}).get("transitive_graph_access")]
        trace_helper_paths = [path for path in helper_paths
                              if helper_inspections.get(path, {}).get("runtime_trace_site")]
        direct_graph = helper_map.get(name, {}).get("direct_graph_access", False)
        direct_trace_codes = helper_map.get(name, {}).get("direct_trace_event_codes", [])
        rows.append({
            "variant": name,
            "enum_line": line,
            "evaluator_arm_present": name in eval_variants,
            "children_walk_case_present": name in child_variants,
            "collector_line": collector_line,
            "access_class": access_class,
            "source_review": review,
            "source_review_kind": "external_boundary" if name in EXTERNAL_DEPENDENCIES else ("dynamic_helper" if name in REVIEWED_DYNAMIC else ("access_branch" if name in REVIEWED_ACCESS_BRANCH else "unreviewed")),
            "external_dependency": EXTERNAL_DEPENDENCIES.get(name),
            "evaluator_helpers": helper_paths,
            "graph_helper_paths": graph_helper_paths,
            "trace_helper_paths": trace_helper_paths,
            "direct_term_graph_access": direct_graph,
            "direct_trace_event_codes": direct_trace_codes,
            "graph_or_eval_context_present": helper_map.get(name, {}).get("graph_or_eval_context_present", False),
            "evaluator_arm_line": helper_map.get(name, {}).get("evaluator_arm_line"),
        })
    event_kinds = re.findall(r'^\s*(\d+) => "([a-z0-9_]+)"', trace_source, re.MULTILINE)
    counts = {
        "term_variants": len(rows),
        "missing_evaluator_arm": sum(not row["evaluator_arm_present"] for row in rows),
        "missing_children_case": sum(not row["children_walk_case_present"] for row in rows),
        "explicit_wildcard": sum(row["access_class"] == "wildcard_reads_any" for row in rows),
        "explicit_finite_keys": sum(row["access_class"] == "finite_resource_keys" for row in rows),
        "conditional_finite_or_wildcard": sum(row["access_class"] == "conditional_finite_or_wildcard" for row in rows),
        "explicit_child_only": sum(row["access_class"] == "explicit_child_walk_only" for row in rows),
        "generic_fallback": sum(row["access_class"] == "generic_children_fallback" for row in rows),
        "source_reviewed_dynamic": sum(row["source_review_kind"] == "dynamic_helper" for row in rows),
        "source_reviewed_access_branches": sum(row["source_review_kind"] == "access_branch" for row in rows),
        "source_reviewed_external_boundaries": sum(row["source_review_kind"] == "external_boundary" for row in rows),
        "helper_linked_variants": sum(bool(row["evaluator_helpers"]) for row in rows),
        "helper_linked_unreviewed": sum(bool(row["evaluator_helpers"]) and row["source_review"] == "unreviewed" for row in rows),
        "transitive_graph_helper_variants": sum(bool(row["graph_helper_paths"]) for row in rows),
        "transitive_graph_helper_unreviewed": sum(bool(row["graph_helper_paths"]) and row["source_review"] == "unreviewed" for row in rows),
        "helper_paths_with_trace_sites": sum(bool(item.get("trace_event_codes")) for item in helper_inspections.values()),
        "direct_graph_term_variants": sum(row["direct_term_graph_access"] for row in rows),
        "direct_graph_term_unreviewed": sum(row["direct_term_graph_access"] and row["source_review"] == "unreviewed" for row in rows),
        "external_dependency_variants": sum(row["external_dependency"] is not None for row in rows),
    }
    graph_reader_rows = [row for row in rows if row["direct_term_graph_access"] or row["graph_helper_paths"]]
    checks = {
        "every_variant_has_evaluator_arm": counts["missing_evaluator_arm"] == 0,
        "every_variant_has_children_case": counts["missing_children_case"] == 0,
        "detected_direct_graph_terms_have_access_declarations": counts["direct_graph_term_unreviewed"] == 0,
        "detected_graph_helpers_have_access_declarations": counts["transitive_graph_helper_unreviewed"] == 0,
        "detected_graph_reader_rows_avoid_generic_fallback": all(
            row["access_class"] != "generic_children_fallback" for row in graph_reader_rows
        ),
    }
    report = {
        "schema_version": 1,
        "audit_id": args.output.stem,
        "audit_runner_sha256": sha(Path(__file__).resolve()),
        "inputs": {
            "term_rs_sha256": sha(TERM),
            "rewrite_rs_sha256": sha(REWRITE),
            "access_trace_rs_sha256": sha(TRACE),
        },
        "counts": counts,
        "checks": checks,
        "trace_event_kinds": [{"code": int(code), "name": name} for code, name in event_kinds],
        "helper_evidence": [{"path": path, **helper_inspections[path]} for path in helper_evidence],
        "trace_code_names": {str(int(code)): name for code, name in event_kinds},
        "rows": rows,
        "claim_boundary": "Mechanical variant/evaluator/child crosswalk with crate-qualified helper candidates. Helper source scan follows same-module calls and qualified crate calls to depth four, with lexical graph/trace markers; it is a navigation aid, not a sound call-graph proof. Generic child traversal is not proof that a Term has no hidden graph or external dependency. Unreviewed rows remain unresolved.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(args.output), "counts": counts,
                      "inputs": report["inputs"]}, indent=2))
    if not all(checks.values()):
        raise SystemExit("Term dependency crosswalk found an unclassified graph-reader path")


if __name__ == "__main__":
    main()
