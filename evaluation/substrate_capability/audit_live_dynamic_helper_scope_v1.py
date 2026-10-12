#!/usr/bin/env python3
"""Source-audit broad helper paths used by the v1.3 live rule sample."""
from __future__ import annotations

import hashlib
import json
import re
from re import MULTILINE
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "evaluation/reports/term_access_dependency_coverage_v1_2_20261005.json"
JOIN = ROOT / "evaluation/reports/live_frame_term_scope_join_v1_1_20261005.json"
DEFINITIONS = ROOT / "evaluation/reports/live_rule_definitions_v1_20261005.json"
OUT = ROOT / "evaluation/reports/live_dynamic_helper_scope_audit_v1_20261005.json"

FILES = {
    "term": "runners/dsl/src/term.rs",
    "shape_decode": "runners/dsl/src/shape_decode.rs",
    "prog_eval": "runners/dsl/src/prog_eval.rs",
    "reflect": "runners/dsl/src/reflect.rs",
}

SHAPE_HELPERS = {
    "ShapeDecode": "eval_shape_decode",
    "TransformDecode": "eval_transform_decode",
    "DimInfer": "eval_dim_infer",
    "GenInfer": "eval_gen_infer",
    "TimeInfer": "eval_time_infer",
    "DepthInfer": "eval_depth_infer",
    "BlinkBridge": "eval_blink_bridge",
    "GapAbduce": "eval_gap_abduce",
    "GapVerify": "eval_gap_verify",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def line_of(text: str, needle: str) -> int:
    at = text.find(needle)
    if at < 0:
        raise SystemExit(f"source evidence missing: {needle}")
    return text.count("\n", 0, at) + 1


def main() -> None:
    inv = json.loads(INVENTORY.read_text())
    join = json.loads(JOIN.read_text())
    defs = json.loads(DEFINITIONS.read_text())
    if not all(inv["checks"].values()) or not all(join["checks"].values()):
        raise SystemExit("upstream inventory/join failed")
    inv_rows = {row["variant"]: row for row in inv["rows"]}
    live_rows = {row["variant"]: row for row in join["live_term_variant_crosswalk"]}
    runtime_defs = {int(row["rule_uid"]): row for row in defs["rules"]}
    sources = {name: (ROOT / rel).read_text() for name, rel in FILES.items()}
    refs = []

    def evidence(file_key: str, needle: str, finding: str) -> dict:
        text = sources[file_key]
        return {"path": FILES[file_key], "line": line_of(text, needle),
                "needle": needle, "finding": finding}

    common_codebook_evidence = [
        evidence("shape_decode", "for nid in ctx.graph.nodes_of_type(codebook_type)",
                 "Every unscoped codebook load traverses the full current population of the requested node type."),
        evidence("shape_decode", "if let (Some(scope), Some(key)) = (scope_filter, scope_key)",
                 "Scope filtering is evaluated after population enumeration, before signature parsing and candidate work."),
        evidence("shape_decode", "for (k, v) in node.attrs.iter()",
                 "Each selected population member has its attributes traversed to recover codebook fields."),
    ]
    shape_arms = []
    for variant, function in SHAPE_HELPERS.items():
        term_needle = f"TermNode::{variant} {{"
        helper_needle = f"crate::shape_decode::{function}"
        if term_needle not in sources["term"] or helper_needle not in sources["term"]:
            raise SystemExit(f"missing evaluator arm/helper link: {variant} -> {function}")
        fn_needle = f"pub(crate) fn {function}("
        fn_start = sources["shape_decode"].find(fn_needle)
        if fn_start < 0:
            raise SystemExit(f"missing helper implementation: {function}")
        # Restrict the call-site assertion to this free function, ending at
        # the next top-level function declaration (public or private).
        next_fn = re.search(r"^(?:pub\(crate\) )?fn ", sources["shape_decode"][fn_start + len(fn_needle):], MULTILINE)
        body_end = fn_start + len(fn_needle) + next_fn.start() if next_fn else len(sources["shape_decode"])
        body = sources["shape_decode"][fn_start: body_end if body_end >= 0 else None]
        load_kind = "load_parts_with_scope" if function == "eval_gen_infer" else "load_parts"
        if load_kind not in body:
            raise SystemExit(f"expected codebook loader not found in {function}")
        termdef = inv_rows.get(variant, {})
        live = live_rows.get(variant, {})
        shape_arms.append({
            "term_variant": variant,
            "runtime_term_occurrences_in_unique_definitions": live.get("occurrences_across_runtime_definitions", 0),
            "runtime_rule_definition_count": live.get("runtime_rule_count", 0),
            "evaluator_helper": function,
            "loader": load_kind,
            "codebook_scope_behavior": (
                "iterates every codebook_type node, then filters scope_id before parsing/candidate work"
                if function == "eval_gen_infer" else
                "loads every codebook_type node; where a scope term exists, it is applied after loading"
            ),
            "source_review": termdef.get("source_review"),
        })

    relation_cue = evidence("shape_decode", "for nid in ctx.graph.nodes_of_type(cue_type)",
                            "ShapeDecode cache misses additionally enumerate all RelationCueToken nodes to build an index.")
    budget_needle = "let sd_budget: u64"
    shape_budget = evidence("shape_decode", budget_needle,
                            "ShapeDecode expansion work uses a per-call expansion budget (defaulted when nonpositive).")
    budget_value = evidence("shape_decode", "pub(crate) const DEFAULT_SD_BUDGET: i64 = 20_000;",
                            "The default ShapeDecode expansion budget is 20,000 candidate-state expansions.")
    shape_scope_filter = evidence("shape_decode", "apply_scope(&mut parts, scope_idx, arena, env, ctx);",
                                  "ShapeDecode applies an optional scope filter after loading the complete codebook population.")

    gen_loop_needles = ["for m00 in -b..=b", "for m01 in -b..=b", "for m10 in -b..=b", "for m11 in -b..=b"]
    gen_loop_evidence = [evidence("shape_decode", needle,
                                  "GenInfer enumerates one coordinate of each 2x2 integer matrix per nested loop.")
                         for needle in gen_loop_needles]
    gen_dimension_guard = evidence("shape_decode", "if n != 2 {",
                                   "GenInfer admits only two-coordinate bases before the 2x2 matrix enumeration.")

    prog_call = evidence("prog_eval", "crate::reflect::term_from_subgraph(",
                         "When ProgEval receives a graph Node instead of an inline program, it decodes a graph-resident term subtree before execution.")
    reflect_recursive = evidence("reflect", "let child = term_from_subgraph(graph, interner, items[0].1, arena)?;",
                                 "Subgraph decoding recursively follows Term child edges; decode cost depends on reachable term-subgraph size.")
    reflect_edge_scan = evidence("reflect", "crate::access_trace::note_out_edges(graph, root, None);",
                                 "Each decoded node enumerates all of its outgoing edges before selecting child edges.")
    fuel_line = evidence("prog_eval", "let fuel = if fuel <= 0 { DEFAULT_FUEL } else { fuel };",
                         "Execution has a fuel limit, but graph-subtree decoding occurs outside fuel-charged VM execution.")

    render_start = evidence("term", "// A Node element renders via the active Language",
                            "Join's Node elements use the active render language and invoke graph-backed rendering.")
    render_scan = evidence("term", "ctx.graph.neighbours(lang_nid, Some(has_rule))",
                           "Renderer searches the current language's has_rule neighbors for a matching head.")
    render_cap = evidence("term", "if ctx.holds_depth > 256 {",
                          "Recursive source rendering stops beyond a fixed holds_depth ceiling.")
    render_refs = [render_start, render_scan, render_cap,
                   evidence("term", "crate::reflect::term_from_subgraph(ctx.graph, ctx.interner, tmpl_nid, &mut tmp)",
                            "A matched rule's template is decoded from its graph-resident Term subgraph.")]

    audit_rows = [
        {
            "family": "shape_decode_codebook_helpers",
            "term_variants": shape_arms,
            "scope_class": "whole node-type population scan plus data-dependent candidate/search work",
            "source_evidence": common_codebook_evidence + [relation_cue, shape_budget, budget_value, shape_scope_filter, gen_dimension_guard] + gen_loop_evidence,
            "tractability_implication": "A scope filter can reduce parsing or candidate work but does not remove the codebook population traversal. ShapeDecode cache misses also enumerate the relation-cue population and its default expansion budget is 20,000. GenInfer restricts bases to two coordinate dimensions but performs four nested loops over a data-derived numeric bound B: up to (2B+1)^4 matrix candidates per eligible base. This is polynomial in B's numeric magnitude but can be exponential in the bit length of an unrestricted B; actual input distributions and per-call cost are not measured here.",
        },
        {
            "family": "ProgEval_graph_resident_program_decode",
            "term_variants": [{"term_variant": "ProgEval", "runtime_term_occurrences_in_unique_definitions": live_rows.get("ProgEval", {}).get("occurrences_across_runtime_definitions", 0), "runtime_rule_definition_count": live_rows.get("ProgEval", {}).get("runtime_rule_count", 0), "evaluator_helper": "eval_prog_eval"}],
            "scope_class": "recursive child-subgraph traversal rooted at the supplied program node, followed by fuel-bounded execution",
            "source_evidence": [prog_call, reflect_recursive, reflect_edge_scan, fuel_line],
            "tractability_implication": "Execution fuel does not bound graph decoding performed before execution. The decoder recursively follows child edges without an explicit visited-set or node budget in the inspected path; safe size bounds depend on graph-subtree shape/invariants.",
        },
        {
            "family": "Join_render_rule_resolution",
            "term_variants": [{"term_variant": "Join", "runtime_term_occurrences_in_unique_definitions": live_rows.get("Join", {}).get("occurrences_across_runtime_definitions", 0), "runtime_rule_definition_count": live_rows.get("Join", {}).get("runtime_rule_count", 0), "evaluator_helper": "render_source_node"}],
            "scope_class": "per rendered node: language has_rule scan until matching render head, child/attribute binding, recursive template decode/evaluation",
            "source_evidence": render_refs,
            "tractability_implication": "This is local to the source term and render-language neighborhood when the language is well-formed, but per-element scan cost depends on rule count and tuple arity. Nested render is depth-capped; template decoding cost depends on its reachable Term subgraph.",
        },
    ]

    live_dynamic = sorted(variant for variant, row in inv_rows.items()
                          if row.get("source_review_kind") == "dynamic_helper" and variant in live_rows)
    covered = {variant for audit in audit_rows for variant in (row["term_variant"] for row in audit["term_variants"])}
    uncovered = sorted(set(live_dynamic) - covered)
    if uncovered:
        raise SystemExit(f"live dynamic-helper variants lack helper scope audit rows: {uncovered}")

    result = {
        "schema": "LiveDynamicHelperScopeAuditV1",
        "run_id": "live-dynamic-helper-scope-audit-v1-20261005",
        "inventory_path": str(INVENTORY.relative_to(ROOT)), "inventory_sha256": sha(INVENTORY),
        "join_path": str(JOIN.relative_to(ROOT)), "join_sha256": sha(JOIN),
        "definitions_path": str(DEFINITIONS.relative_to(ROOT)), "definitions_sha256": sha(DEFINITIONS),
        "source_hashes": {rel: sha(ROOT / rel) for rel in FILES.values()},
        "summary": {
            "live_dynamic_helper_variants": len(live_dynamic),
            "covered_live_dynamic_helper_variants": len(covered & set(live_dynamic)),
            "uncovered_live_dynamic_helper_variants": uncovered,
            "all_scanned_helpers_present": True,
            "source_evidence_items": sum(len(row["source_evidence"]) for row in audit_rows),
        },
        "checks": {
            "source_inventory_and_join_pass": all(inv["checks"].values()) and all(join["checks"].values()),
            "definition_archive_is_hash_checked": bool(defs["summary"]["matches_independent_runtime_analysis"]),
            "all_live_dynamic_helpers_covered": not uncovered,
            "all_referenced_source_needles_present": True,
        },
        "audits": audit_rows,
        "claim_boundary": "This source audit establishes static graph-access routes in the inspected implementations, not invocation frequency, elapsed cost, complete transitive call graphs, or frame-locality. The codebook population traversal is explicit. ProgEval's graph-resident decode and Join's graph-resident renderer are conditional on runtime values. No factor scopes or task-frame ownership are inferred.",
    }
    result["checks"]["all_checks_pass"] = all(result["checks"].values())
    if not result["checks"]["all_checks_pass"]:
        raise SystemExit(f"source audit failed: {result['checks']}")
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "summary": result["summary"], "checks": result["checks"]}, indent=2))


if __name__ == "__main__":
    main()
