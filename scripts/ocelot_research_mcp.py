"""Local stdio MCP interface for Ocelot research records.

The server reads configured sources and writes only to its configured session
store. It does not run shell commands, call models, or access the network.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from scripts.ocelot_dev_memory_mcp import _EOF, _read_message, _write_message
from scripts.ocelot_research_service import ResearchService

PROTOCOL_VERSION = "2024-11-05"
OPERATIONS = {
    "init": ("Create an investigation.", {"question": {"type": "string"}, "mode": {"type": "string"}, "roots": {"type": "array", "items": {"type": "object"}}}, ["question"]),
    "context": ("Find cited local research context.", {"session_id": {"type": "string"}, "query": {"type": "string"}, "limit": {"type": "integer"}}, ["session_id", "query"]),
    "native_graph": ("Project the research graph and optionally evaluate a native DSL term.", {"session_id": {"type": "string"}, "query": {"type": "object"}, "env": {"type": "object"}}, ["session_id"]),
    "paper_preview": ("Read a selected paper into source-linked claim candidates without recording.", {"session_id": {"type": "string"}, "root_id": {"type": "string"}, "path": {"type": "string"}, "max_formula_candidates": {"type": "integer"}, "formula_offset": {"type": "integer"}, "latexml_path": {"type": "string"}}, ["session_id", "root_id", "path"]),
    "paper_ingest": ("Record a selected paper's claims and references in the research graph.", {"session_id": {"type": "string"}, "root_id": {"type": "string"}, "path": {"type": "string"}, "max_formula_candidates": {"type": "integer"}, "formula_offset": {"type": "integer"}, "latexml_path": {"type": "string"}}, ["session_id", "root_id", "path"]),
    "formula_parse_candidates": ("Optionally parse supplied LaTeX formulas with SymPy/Lark; returns unverified candidates without execution or recording.", {"session_id": {"type": "string"}, "formulas": {"type": "array", "maxItems": 256, "items": {"type": "string"}}}, ["session_id", "formulas"]),
    "formula_resolve": ("Use scoped research graph context to compare formula interpretations.", {"session_id": {"type": "string"}, "formula": {"type": "string"}, "scope_id": {"type": "string"}}, ["session_id", "formula", "scope_id"]),
    "formula_translate": ("Translate a supported formula into a native executable Term.", {"session_id": {"type": "string"}, "formula": {"type": "string"}, "domain_assumptions": {"type": "object"}}, ["session_id", "formula"]),
    "formula_model": ("Translate a formula and attach it as a reviewable claim model.", {"session_id": {"type": "string"}, "claim_id": {"type": "string"}, "formula": {"type": "string"}, "domain_assumptions": {"type": "object"}, "context_scope_id": {"type": "string"}, "bindings": {"type": "object"}, "assumption_ids": {"type": "array", "items": {"type": "string"}}, "residuals": {"type": "array", "items": {"type": "string"}}, "reviewer": {"type": "string"}, "review_note": {"type": "string"}}, ["session_id", "claim_id", "formula", "reviewer", "review_note"]),
    "model_candidate": ("Attach an explicit native Term model candidate to a sourced claim.", {"session_id": {"type": "string"}, "claim_id": {"type": "string"}, "term": {"type": "object"}, "bindings": {"type": "object"}, "assumption_ids": {"type": "array", "items": {"type": "string"}}, "residuals": {"type": "array", "items": {"type": "string"}}, "reviewer": {"type": "string"}, "review_note": {"type": "string"}, "provenance": {"type": "object"}}, ["session_id", "claim_id", "term", "residuals", "reviewer", "review_note"]),
    "record": ("Append a research record.", {"session_id": {"type": "string"}, "kind": {"type": "string"}, "fields": {"type": "object"}}, ["session_id", "kind", "fields"]),
    "link": ("Link two research records.", {"session_id": {"type": "string"}, "src": {"type": "string"}, "relation": {"type": "string"}, "tgt": {"type": "string"}, "fields": {"type": "object"}}, ["session_id", "src", "relation", "tgt"]),
    "inspect": ("Inspect a session or a record and its links.", {"session_id": {"type": "string"}, "node_id": {"type": "string"}, "transitive": {"type": "boolean"}}, ["session_id"]),
    "trace": ("Trace directed research derivations.", {"session_id": {"type": "string"}, "node_id": {"type": "string"}, "max_depth": {"type": "integer"}}, ["session_id", "node_id"]),
    "execute": ("Run explicit graph-bound native substrate terms.", {"session_id": {"type": "string"}, "node_id": {"type": "string"}, "env": {"type": "object"}, "max_depth": {"type": "integer"}, "max_nodes": {"type": "integer"}}, ["session_id", "node_id"]),
    "check_lean": ("Check generated Lean declarations with the local Lean executable.", {"session_id": {"type": "string"}, "node_id": {"type": "string"}}, ["session_id"]),
    "export_lean": ("Export explicit Boolean terms as Lean definitions.", {"session_id": {"type": "string"}, "node_id": {"type": "string"}}, ["session_id"]),
    "check": ("Check research records and provenance; does not certify truth.", {"session_id": {"type": "string"}}, ["session_id"]),
    "export": ("Export an auditable ledger and JSON bundle.", {"session_id": {"type": "string"}}, ["session_id"]),
}
TOOLS = [{"name": "research_" + name, "description": desc,
          "inputSchema": {"type": "object", "properties": props,
                          "required": required, "additionalProperties": False}}
         for name, (desc, props, required) in OPERATIONS.items()]

class ResearchServer:
    def __init__(self, service: ResearchService):
        self.service = service

    def handle(self, msg):
        method, msg_id = msg.get("method"), msg.get("id")
        params = msg.get("params") or {}
        if "id" not in msg:
            return None
        if method == "initialize":
            result = {"protocolVersion": PROTOCOL_VERSION,
                      "capabilities": {"tools": {"listChanged": False}},
                      "serverInfo": {"name": "ocelot-research", "version": "0.1.0"}}
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            name = params.get("name", "")
            if not name.startswith("research_") or name[9:] not in OPERATIONS:
                return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": "unknown tool"}}
            try:
                value = self.service.call(name[9:], params.get("arguments") or {})
                result = {"content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False)}], "isError": False}
            except Exception as exc:
                result = {"content": [{"type": "text", "text": f"{type(exc).__name__}: {exc}"}], "isError": True}
        else:
            return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": "method not found"}}
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default=os.environ.get("OCELOT_RESEARCH_WORKSPACE", "."))
    args = parser.parse_args(argv)
    server = ResearchServer(ResearchService(Path(args.workspace)))
    while True:
        try:
            message, framing = _read_message(sys.stdin.buffer)
        except (ValueError, json.JSONDecodeError) as exc:
            print(f"[ocelot-research] invalid message: {exc}", file=sys.stderr)
            continue
        if message is _EOF:
            break
        if not isinstance(message, dict):
            _write_message(sys.stdout.buffer, {"jsonrpc": "2.0", "id": None,
                           "error": {"code": -32600, "message": "invalid request"}}, framing)
            continue
        response = server.handle(message)
        if response is not None:
            _write_message(sys.stdout.buffer, response, framing)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
