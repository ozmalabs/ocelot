#!/usr/bin/env python3
"""Source-linked audit of Term-level file, tool, and Program IR call boundaries."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TERM = ROOT / "runners/dsl/src/term.rs"
TOOLS = ROOT / "runners/dsl/src/tools.rs"
PROG = ROOT / "runners/dsl/src/prog_eval.rs"
OUT = ROOT / "evaluation/reports/term_external_boundaries_v1_20260928.json"


def lines(path: Path, start: str, end: str | None = None) -> dict:
    source = path.read_text()
    i = source.index(start)
    j = source.index(end, i) if end else len(source)
    body = source[i:j]
    return {
        "path": str(path.relative_to(ROOT)),
        "start_line": source[:i].count("\n") + 1,
        "end_line": source[:j].count("\n") + (1 if j < len(source) else 0),
        "sha256": hashlib.sha256(body.encode()).hexdigest(),
        "source_excerpt": body,
    }


def main() -> None:
    term = TERM.read_text()
    tools = TOOLS.read_text()
    prog = PROG.read_text()
    readfile = lines(TERM, "        TermNode::ReadFile { path } => {", "        TermNode::StringIndexOf {")
    usetool = lines(TERM, "        TermNode::UseTool { tool, args } => {", "        TermNode::SetT {")
    progextern = lines(PROG, "        TermNode::ProgCallExtern { name, recv, args } => {", "        TermNode::ProgAttrGet {")
    tool_dispatch = lines(TOOLS, "pub fn call_tool(", "/// Register the tool-dispatch PyO3 functions")
    oracle_dispatch = lines(PROG, "fn call_native_oracle(", "/// Q1 `string_methods`")
    standalone_prog_arm = lines(TERM, "        | TermNode::ProgCallExtern { .. }", "        | TermNode::ProgAttrGet {")

    sources = [readfile, usetool, progextern, tool_dispatch, oracle_dispatch, standalone_prog_arm]
    for source in sources:
        source.pop("source_excerpt")
    report = {
        "audit_id": "term_external_boundaries_v1_20260928",
        "source_hashes": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (TERM, TOOLS, PROG)
        },
        "findings": {
            "ReadFile": {
                "classification": "unrestricted native filesystem read",
                "facts": [
                    "Evaluates the path child and accepts only an interned string value.",
                    "Passes the resolved path directly to std::fs::read_to_string without a workspace/root allowlist in this arm.",
                    "Returns text on success and Value::None on any read error.",
                    "The path child is in TermNode::children; filesystem contents and path policy are outside RuleKey access tracking.",
                ],
                "source": [readfile],
            },
            "UseTool": {
                "classification": "dynamic registered Python callback; effect and reentry boundary",
                "facts": [
                    "Evaluates argument child Terms before dispatch and records trace event kind 18.",
                    "Dispatches by name through a process-global Mutex<HashMap<String, Py<PyAny>>> registry.",
                    "Drops the registry lock before invoking the handler; handlers may reenter or mutate external state.",
                    "Handler errors, absent handlers, and unsupported return values collapse to Value::Int(0); trace rows do not describe handler-internal reads/writes.",
                ],
                "source": [usetool, tool_dispatch],
            },
            "ProgCallExtern": {
                "classification": "declared, in-engine native oracle dispatch in Program IR",
                "facts": [
                    "A standalone TermNode::ProgCallExtern evaluates to Value::None; executable behavior occurs when nested in ProgEval's Program IR interpreter.",
                    "The interpreter requires the call name to be present in the supplied oracles Dict, then dispatches to call_native_oracle.",
                    "The current oracle implementation is an in-engine match over named Rust operations; unsupported names trap rather than invoking Python, shell, or arbitrary host code.",
                    "The oracles Dict is caller-provided input, but it declares names and does not provide callable values in this implementation.",
                ],
                "source": [standalone_prog_arm, progextern, oracle_dispatch],
            },
        },
        "claim_boundary": "Static source review only. It does not execute these paths, prove caller-side path restrictions, inventory every registered Python handler, or establish OS containment. Source excerpt hashes identify the reviewed spans; full source hashes bind the report to current files.",
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "findings": list(report["findings"]), "source_files": len(report["source_hashes"])}, sort_keys=True))


if __name__ == "__main__":
    main()
