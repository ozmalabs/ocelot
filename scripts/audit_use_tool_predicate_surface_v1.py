#!/usr/bin/env python3
"""Source-locked inventory of UseTool calls in seed predicates and generation seams."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/use_tool_predicate_surface_v1_20260928.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def walk(value):
    if isinstance(value, dict):
        if value.get("type") == "UseTool":
            yield str(value.get("tool", "<missing>"))
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def tool_handlers(path: Path) -> list[str]:
    tree = ast.parse(path.read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "HANDLERS" for t in node.targets
        ) and isinstance(node.value, ast.Dict):
            return [k.value for k in node.value.keys if isinstance(k, ast.Constant)]
    return []


def main() -> None:
    seed_rows = []
    predicate_tools: dict[str, int] = {}
    effect_tools: dict[str, int] = {}
    for path in sorted((ROOT / "seeds").glob("*.json")):
        try:
            data = json.loads(path.read_text())
        except Exception as exc:
            seed_rows.append({"path": str(path.relative_to(ROOT)), "parse_error": str(exc)})
            continue
        if not isinstance(data, dict):
            continue
        for rule in data.get("rules", []):
            if not isinstance(rule, dict):
                continue
            where = list(walk(rule.get("where")))
            effects = list(walk(rule.get("effects", [])))
            if where or effects:
                seed_rows.append({
                    "path": str(path.relative_to(ROOT)), "seed_id": data.get("id"),
                    "rule": rule.get("name"), "where_calls": where,
                    "effect_calls": effects,
                })
                for name in where:
                    predicate_tools[name] = predicate_tools.get(name, 0) + 1
                for name in effects:
                    effect_tools[name] = effect_tools.get(name, 0) + 1

    handler_path = ROOT / "domains/symbolic_perception.py"
    handlers = tool_handlers(handler_path)
    focus_paths = [
        ROOT / "domains/ast_to_rule.py", ROOT / "scripts/migrate_curious_agent.py",
        ROOT / "substrate/boot_all.py", ROOT / "seeds/figure_grounding.json",
    ]
    source_refs = [{"path": str(p.relative_to(ROOT)), "sha256": sha(p)} for p in focus_paths]
    out = {
        "audit": "UseTool predicate surface v1",
        "scope": "flat seeds/*.json; source inspection of the known AST-to-rule seam and full-corpus loader",
        "seed_files_scanned": len(list((ROOT / "seeds").glob("*.json"))),
        "seed_rule_rows_with_use_tool": seed_rows,
        "predicate_call_count": sum(predicate_tools.values()),
        "predicate_calls_by_tool": dict(sorted(predicate_tools.items())),
        "effect_call_count": sum(effect_tools.values()),
        "effect_calls_by_tool": dict(sorted(effect_tools.items())),
        "registered_symbolic_handlers": handlers,
        "predicate_tools_without_symbolic_handler": sorted(set(predicate_tools) - set(handlers)),
        "source_sha256": source_refs,
        "interpretation": [
            "The inventory counts syntactic UseTool nodes in seed rule where/effects fields, not runtime invocation frequency.",
            "AST migrator expr_term maps nested np.<module>.<function>(...) calls to UseTool; method_to_rule applies it to a no-else if guard via _value(st.test).",
            "migrate_curious_agent.py is the located caller; this is an opt-in conversion route, not evidence of automatic production generation.",
            "load_all_seeds documents no-selection as full-corpus boot; selected/profiled boot routes can differ.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: out[k] for k in ("seed_files_scanned", "predicate_call_count", "predicate_calls_by_tool", "effect_call_count", "effect_calls_by_tool", "predicate_tools_without_symbolic_handler")}, indent=2))
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
