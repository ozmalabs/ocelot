#!/usr/bin/env python3
"""Source-hashed inventory of native rule access-trace coverage and known gaps."""
from __future__ import annotations

import hashlib
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_runtime_access_trace_coverage_v1_20260926.json"
SOURCES = {
    "access_trace": ROOT / "runners/dsl/src/access_trace.rs",
    "term": ROOT / "runners/dsl/src/term.rs",
    "shape_decode": ROOT / "runners/dsl/src/shape_decode.rs",
    "rewrite": ROOT / "runners/dsl/src/rewrite.rs",
    "jit": ROOT / "runners/dsl/src/jit.rs",
    "world_adapter": ROOT / "substrate/world_adapter.py",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def line_of(path: Path, text: str, occurrence: int = 1) -> int:
    lines = path.read_text().splitlines()
    seen = 0
    for number, line in enumerate(lines, 1):
        if text in line:
            seen += 1
            if seen == occurrence:
                return number
    raise ValueError(f"missing source anchor {text!r} in {path.relative_to(ROOT)}")


def term_variants() -> list[str]:
    source = SOURCES["term"].read_text()
    enum = source.split("pub enum TermNode", 1)[1].split("\n}\n", 1)[0]
    return re.findall(r"^\s{4}([A-Z][A-Za-z0-9_]*)\s*(?:\{|,)", enum, re.MULTILINE)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUT,
                        help="output JSON path (defaults to the historical v1 path)")
    args = parser.parse_args()
    trace = SOURCES["access_trace"]
    term = SOURCES["term"]
    rewrite = SOURCES["rewrite"]
    jit = SOURCES["jit"]
    events = {}
    for kind, name in re.findall(r'^\s*(\d+)\s*=>\s*"([^"]+)"', trace.read_text(), re.MULTILINE):
        events[int(kind)] = name

    trace_call_sites = {
        key: [i for i, row in enumerate(path.read_text().splitlines(), 1)
              if "access_trace::note" in row]
        for key, path in (("term", term), ("rewrite", rewrite), ("jit", jit))
    }
    findings = [
        {
            "status": "instrumented_partial",
            "family": "interpreted and selected JIT node reads",
            "coverage": ["Attr", "TypeOf", "selected JIT attribute/type reads"],
            "evidence": [
                {"path": "runners/dsl/src/term.rs", "line": line_of(term, "crate::access_trace::note(3, nid.0, type_sym.0, crate::access_trace::NO_ID);")},
                {"path": "runners/dsl/src/term.rs", "line": line_of(term, "crate::access_trace::note(2, nid.0, key.0, crate::access_trace::NO_ID);")},
                {"path": "runners/dsl/src/jit.rs", "line": line_of(jit, "access_trace::note(12")},
            ],
        },
        {
            "status": "instrumented_partial",
            "family": "typed adjacency and edge attributes",
            "coverage": ["Neighbours", "ReachableFrom", "InNeighbours", "MapNeighbours", "SlideNeighbours", "Edges", "EdgeAttr", "render child/template traversal"],
            "evidence": [
                {"path": "runners/dsl/src/term.rs", "line": line_of(term, "crate::access_trace::note_out_edges(ctx.graph, cur, et);")},
                {"path": "runners/dsl/src/term.rs", "line": line_of(term, "crate::access_trace::note(15, src.0, key.0, tgt.0);")},
                {"path": "runners/dsl/src/term.rs", "line": line_of(term, "crate::access_trace::note_in_edges(ctx.graph, nid, et);")},
            ],
        },
        {
            "status": "instrumented_partial",
            "family": "type/index population queries",
            "coverage": ["NodesWhere indexed/fallback query markers and rows", "NodesOfType returned rows (population scan not explicitly marked)", "ScalarAttrTriples iteration"],
            "evidence": [
                {"path": "runners/dsl/src/term.rs", "line": line_of(term, "crate::access_trace::note(32,")},
                {"path": "runners/dsl/src/term.rs", "line": line_of(term, "crate::access_trace::note(33,")},
                {"path": "runners/dsl/src/term.rs", "line": line_of(term, "for nid in ctx.graph.nodes_of_type(*node_type) {")},
                {"path": "runners/dsl/src/term.rs", "line": line_of(term, "for (nid, nd) in ctx.graph.iter_nodes() {")},
            ],
            "detail": "NodesWhere records a query marker for both indexed and fallback paths and distinguishes scanned candidates from returned rows. NodesOfType currently records only returned-node type reads; an empty result has no query event, and scanned population size must be obtained from separate work accounting.",
        },
        {
            "status": "instrumented_partial",
            "family": "rule matcher",
            "coverage": ["successful pattern-edge bindings"],
            "limit": "The event is emitted after a binding succeeds; a 1-versus-9 candidate probe showed cand_tested scaling 1-to-9 while successful pattern_edge events stayed at 1. Predicate attribute reads were traced for all candidates, but rejected candidate edge identities and scheduler/index work were not fully represented.",
            "evidence": [{"path": "runners/dsl/src/rewrite.rs", "line": line_of(rewrite, "access_trace::note(1, src.0, edge.edge_type.0, tgt.0)")}],
        },
        {
            "status": "instrumented_partial",
            "family": "shape-decode cache fingerprint and decoder scans",
            "coverage": ["typed-population query marker", "node type and attribute fingerprint reads under an active RuleUid", "partial decoder reads on cache misses"],
            "detail": "sd_cache_key now emits a typed-population query marker and note_node_type_and_attrs for every fingerprinted node, so key-construction reads are visible on both cache hits and misses under an active RuleUid. Direct evaluations without a RuleUid remain unattributed, and the trace does not label hit versus miss. A paired 1-versus-2 computed-effect probe observed exactly 2-versus-4 query markers per type with semantic parity.",
            "evidence": [
                {"path": "runners/dsl/src/term.rs", "line": line_of(term, "fn sd_cache_key(")},
                {"path": "runners/dsl/src/term.rs", "line": line_of(term, "crate::access_trace::note_node_type_and_attrs(graph, nid);")},
                {"path": "runners/dsl/src/term.rs", "line": line_of(term, "for nid in graph.nodes_of_type(*sym)")},
                {"path": "runners/dsl/src/term.rs", "line": line_of(term, "                sym.0,")},
                {"path": "runners/dsl/src/shape_decode.rs", "line": line_of(SOURCES["shape_decode"], "fn trace_scanned_node(")},
                {"path": "runners/dsl/src/shape_decode.rs", "line": line_of(SOURCES["shape_decode"], "trace_scanned_node(ctx, nid);")},
            ],
        },
        {
            "status": "omitted_known",
            "family": "external tool dispatch",
            "detail": "UseTool evaluates arguments and calls the registered Python handler; callback reads, writes, and external side effects are not represented as native graph-access events. A paired probe independently observed one callback invocation in both traced/untraced arms and no tool-kind trace row.",
            "evidence": [
                {"path": "runners/dsl/src/term.rs", "line": line_of(term, "TermNode::UseTool { tool, args }")},
                {"path": "runners/dsl/src/term.rs", "line": line_of(term, "crate::tools::call_tool(name, &arg_vals, ctx.interner)")},
            ],
        },
        {
            "status": "omitted_read_detail",
            "family": "attribute effects",
            "detail": "SetAttrIfDifferent reads the old value before deciding whether it writes; current events record the effect write only on the changed branch, not a separate concrete old-value read. A paired probe confirmed unchanged and changed arms preserve semantics, while only the changed arm emits the target write event. Static writesets remain a separate diagnostic.",
            "evidence": [
                {"path": "runners/dsl/src/rewrite.rs", "line": line_of(rewrite, "let old = graph.node(nid).attrs.get(key).cloned();", 2)},
                {"path": "runners/dsl/src/rewrite.rs", "line": line_of(rewrite, "access_trace::note(4, nid.0, key.0", 2)},
            ],
        },
        {
            "status": "omitted_when_unattributed",
            "family": "host/scheduler work outside a rule UID",
            "detail": "note() returns without recording when the thread-local current rule UID is zero. Adapter work, post-rule queue draining, and other operations outside an entered rule are therefore invisible to this event stream.",
            "evidence": [
                {"path": "runners/dsl/src/access_trace.rs", "line": line_of(trace, "let rule_uid = CURRENT_RULE_UID.with(Cell::get);")},
                {"path": "runners/dsl/src/access_trace.rs", "line": line_of(trace, "if rule_uid == 0 || scope == 0 || scope != ACTIVE_SCOPE.load(Ordering::Relaxed) {")},
            ],
        },
    ]
    payload = {
        "schema_version": 1,
        "run_id": args.output.stem,
        "claim_boundary": "Source audit of known native trace coverage, not a dynamic completeness test. A note site demonstrates instrumentation code exists, not that every caller path or all access classes are covered.",
        "source_sha256": {key: sha(path) for key, path in SOURCES.items()},
        "audit_runner_sha256": sha(Path(__file__).resolve()),
        "term_node_variant_count": len(term_variants()),
        "event_kinds": dict(sorted(events.items())),
        "access_trace_note_callsite_count_by_file": {key: len(value) for key, value in trace_call_sites.items()},
        "findings": findings,
        "next_probe": "Attribute trace work outside active RuleUID/scope pairs, post-rule queued effects, and host callbacks; calibrate scheduler and matcher counters against those event sites. Failed-candidate, SetAttrIfDifferent, and UseTool omissions have bounded probes, but no complete dynamic trace-recall estimate exists. Cache hit/miss labels may aid attribution but do not close these omissions.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(args.output), "term_variants": payload["term_node_variant_count"],
                      "event_kinds": len(events), "findings": len(findings),
                      "source_sha256": payload["source_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
