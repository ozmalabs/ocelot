#!/usr/bin/env python3
"""Source audit of the computational constructor registry in substrate_extension."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "domains/substrate_extension.py"
OUT = ROOT / "evaluation/reports/extension_construction_registry_v1.json"


def main() -> None:
    raw = SOURCE.read_bytes()
    tree = ast.parse(raw, filename=str(SOURCE))
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    selector = functions["_select_construction"]
    selected = sorted({node.value.value for node in ast.walk(selector)
                       if isinstance(node, ast.Return)
                       and isinstance(node.value, ast.Constant)
                       and isinstance(node.value.value, str)})
    builder = functions["build_primitive"]
    term_builders = sorted({node.func.id for node in ast.walk(builder)
                            if isinstance(node, ast.Call)
                            and isinstance(node.func, ast.Name)
                            and node.func.id.endswith("_term")})
    report = {
        "schema_version": 1,
        "scope": "domains/substrate_extension.py computational build_primitive route only",
        "source": {"path": SOURCE.relative_to(ROOT).as_posix(),
                   "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()},
        "selector_string_return_values": selected,
        "build_primitive_term_builder_calls": term_builders,
        "registered_buildable_family_count": len(selected),
        "interpretation": "The audited extension route has one selected construction family. This does not census other learning, rule-minting, or host-side capability paths.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
