#!/usr/bin/env python3
"""Small source census of ReachableFrom authoring and evaluator entrypoints."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_reachable_from_cache_usage_v1_20260928.json"
INPUTS = (
    "seeds/browser_affordance_reach.json",
    "domains/self_extend_rust.py",
    "domains/grounding_reach.py",
    "domains/frozen_core.py",
    "worlds/browser.py",
    "runners/dsl/src/term.rs",
    "runners/dsl/src/substrate.rs",
    "runners/dsl/src/py.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "scripts/audit_reachable_from_cache_usage_v1.py",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seed_terms(value, path: str, out: list[dict]) -> None:
    if isinstance(value, dict):
        if value.get("type") == "ReachableFrom":
            out.append({"path": path, "edge_type": value.get("edge_type"), "node": value.get("node")})
        for key, child in value.items():
            seed_terms(child, f"{path}.{key}", out)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            seed_terms(child, f"{path}[{index}]", out)


class LiteralUseVisitor(ast.NodeVisitor):
    def __init__(self):
        self.stack: list[str] = []
        self.uses: list[dict] = []

    def visit_FunctionDef(self, node):
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Constant(self, node):
        if node.value == "ReachableFrom":
            self.uses.append({"line": node.lineno, "function": ".".join(self.stack) or None})


def main() -> int:
    seed = json.loads((ROOT / INPUTS[0]).read_text())
    terms: list[dict] = []
    seed_terms(seed, "$", terms)
    python_uses = {}
    for rel in INPUTS[1:5]:
        path = ROOT / rel
        visitor = LiteralUseVisitor()
        visitor.visit(ast.parse(path.read_text()))
        if visitor.uses:
            python_uses[rel] = visitor.uses
    py_rs = (ROOT / "runners/dsl/src/py.rs").read_text()
    eval_start = py_rs.find("fn evaluate<'py>(")
    cache_pos = py_rs.find("let mut cache = EvalCache::default();", eval_start)
    native_eval = eval_start >= 0 and cache_pos >= eval_start
    py_api = ast.parse((ROOT / INPUTS[-1]).read_text())
    wrapper_methods = {n.name for n in ast.walk(py_api) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    results = {
        "schema_version": 1,
        "scope": "Source census only; no runtime activation, real-page prevalence, or dynamic call graph inferred.",
        "input_sha256": {rel: sha(ROOT / rel) for rel in INPUTS},
        "seed_rule_count": len(seed.get("rules", [])),
        "executable_seed_term_count": len(terms),
        "executable_seed_terms": terms,
        "python_literal_reference_count": sum(map(len, python_uses.values())),
        "python_literal_references": python_uses,
        "native_direct_evaluate_uses_fresh_default_cache": native_eval is not None,
        "high_level_wrapper_has_reachable_cache_toggle": "set_reachable_cache" in wrapper_methods,
        "browser_world_requires_seed": "browser_affordance_reach" in (ROOT / "worlds/browser.py").read_text(),
        "cache_owner": "Substrate.eval_cache is the persistent cache passed through rule rewriting; the opt-in setter is on the native PySubstrate API.",
        "interpretation": "The browser seed supplies one source-authored rule family suitable for persistent same-graph reuse. Direct Python query helpers in grounding_reach and frozen_core call PySubstrate.evaluate, which constructs a fresh default-off EvalCache, so the current setter does not amortize across those separate direct calls. The high-level substrate_rs.Substrate wrapper does not expose the toggle.",
    }
    results["expected_source_shape"] = (results["executable_seed_term_count"] == 1
        and results["python_literal_reference_count"] == 3
        and results["native_direct_evaluate_uses_fresh_default_cache"]
        and not results["high_level_wrapper_has_reachable_cache_toggle"]
        and results["browser_world_requires_seed"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "expected_source_shape": results["expected_source_shape"],
        "seed_terms": results["executable_seed_term_count"], "python_literal_refs": results["python_literal_reference_count"],
        "fresh_direct_cache": results["native_direct_evaluate_uses_fresh_default_cache"],
        "high_level_toggle": results["high_level_wrapper_has_reachable_cache_toggle"]}, indent=2))
    return 0 if results["expected_source_shape"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
