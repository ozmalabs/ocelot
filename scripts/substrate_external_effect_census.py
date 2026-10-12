#!/usr/bin/env python3
"""Read-only AST census of Python process/network effect call sites.

This is a source inventory, not a reachability proof: it finds syntactic call
sites under selected runtime-owned directories without importing application
modules or executing handlers. Review candidates and dynamic dispatch separately.
"""
from __future__ import annotations

import ast
import hashlib
import json
import platform
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = (ROOT / "domains", ROOT / "substrate", ROOT / "runners/dsl/python")
OUT = ROOT / "evaluation/reports/substrate_external_effect_census_20260925.json"

PROCESS_MODULE_FUNCS = {"run", "Popen", "call", "check_call", "check_output", "system", "popen"}
NETWORK_MODULE_FUNCS = {
    "urllib.request": {"urlopen"},
    "http.client": {"HTTPConnection", "HTTPSConnection"},
    "socket": {"socket", "create_connection"},
    "requests": {"get", "post", "request", "Session"},
    "httpx": {"get", "post", "request", "Client", "AsyncClient"},
}
REGISTRY_CALLS = {"register_tool_handler", "register_handler", "register_real_tools",
                  "register_native_handlers", "register_tool"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dotted(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return type(node).__name__


def enclosing_functions(tree: ast.AST) -> dict[int, str]:
    result: dict[int, str] = {}

    def walk(node: ast.AST, stack: tuple[str, ...]) -> None:
        for child in ast.iter_child_nodes(node):
            new_stack = stack
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                new_stack = (*stack, child.name)
            if isinstance(child, ast.Call):
                result[id(child)] = ".".join(new_stack) or "<module>"
            walk(child, new_stack)

    walk(tree, ())
    return result


def import_aliases(tree: ast.AST) -> tuple[dict[str, str], dict[str, str]]:
    modules: dict[str, str] = {}
    functions: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                local = alias.asname or alias.name.split(".")[0]
                modules[local] = alias.name if alias.asname else alias.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                local = alias.asname or alias.name
                functions[local] = f"{node.module}.{alias.name}"
    return modules, functions


def classify_effect_call(node: ast.Call, modules: dict[str, str],
                         functions: dict[str, str]) -> str | None:
    raw = dotted(node.func)
    parts = raw.split(".")
    if raw in functions:
        normalized = functions[raw]
    elif parts[0] in functions:
        normalized = ".".join((functions[parts[0]], *parts[1:]))
    elif parts[0] in modules:
        normalized = ".".join((modules[parts[0]], *parts[1:]))
    else:
        return None
    normalized_parts = normalized.split(".")
    tail = normalized_parts[-1]
    prefix = ".".join(normalized_parts[:-1])
    if prefix == "subprocess" and tail in PROCESS_MODULE_FUNCS:
        return "process"
    if prefix == "os" and tail in {"system", "popen", "spawnv", "spawnve", "spawnvp", "spawnvpe"}:
        return "process"
    if tail in NETWORK_MODULE_FUNCS.get(prefix, set()):
        return "network"
    return None


def main() -> None:
    files = sorted(p for root in SCAN_ROOTS if root.exists()
                   for p in root.rglob("*.py") if "__pycache__" not in p.parts)
    files += [ROOT / "scripts/jabberwock_daemon.py"]
    files = sorted({p for p in files if p.is_file()})
    sites: list[dict] = []
    parse_errors = []
    hashes = {}
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        hashes[rel] = sha(path)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        except (SyntaxError, UnicodeDecodeError) as exc:
            parse_errors.append({"path": rel, "error": str(exc)})
            continue
        owners = enclosing_functions(tree)
        modules, imported_functions = import_aliases(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = dotted(node.func)
            tail = name.rsplit(".", 1)[-1]
            kind = classify_effect_call(node, modules, imported_functions)
            if kind is None and tail == "deny_direct_io":
                kind = "explicit_guard"
            elif kind is None and tail in REGISTRY_CALLS:
                kind = "tool_registration"
            if kind is None:
                continue
            route = None
            if tail == "deny_direct_io" and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    route = arg.value
            sites.append({"kind": kind, "path": rel, "line": node.lineno,
                          "owner": owners.get(id(node), "<unknown>"),
                          "callee": name, "guard_route": route})

    counts = Counter(site["kind"] for site in sites)
    guard_scopes = {(s["path"], s["owner"]) for s in sites
                    if s["kind"] == "explicit_guard"}
    guard_scope_effects = [s for s in sites
                           if s["kind"] in {"process", "network"}
                           and (s["path"], s["owner"]) in guard_scopes]
    payload = {
        "schema_version": 1,
        "run_id": "substrate-external-effect-census-20260925",
        "scope": [p.relative_to(ROOT).as_posix() for p in SCAN_ROOTS if p.exists()]
                 + ["scripts/jabberwock_daemon.py"],
        "method": "Python AST parse; no module imports, handler invocation, process launch, or network request",
        "limitations": ["Syntactic call sites do not prove reachability or invocation.",
                        "Aliases, reflection, native code, dynamically supplied callables, and effects hidden in dependencies may be missed.",
                        "Filesystem mutation calls are outside this census; include them in a separate capability-specific audit.",
                        "Tool registration call sites are candidates, not a count of handlers active in any runtime."],
        "python": platform.python_version(),
        "census_script_sha256": sha(Path(__file__).resolve()),
        "files_scanned": len(files),
        "parse_errors": parse_errors,
        "source_sha256": hashes,
        "counts": dict(sorted(counts.items())),
        "same_function_guard_effect_candidates": guard_scope_effects,
        "sites": sorted(sites, key=lambda s: (s["path"], s["line"], s["kind"])),
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"files_scanned": len(files), "parse_errors": len(parse_errors),
                      "counts": dict(sorted(counts.items())),
                      "same_function_guard_effect_candidates": len(guard_scope_effects),
                      "output": str(OUT)}, indent=2))
    if parse_errors:
        raise SystemExit("source census incomplete: AST parse errors")


if __name__ == "__main__":
    main()
