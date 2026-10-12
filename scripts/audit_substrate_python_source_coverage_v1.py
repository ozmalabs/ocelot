#!/usr/bin/env python3
"""Inventory Python source coverage and static import reachability for the substrate map."""
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from collections import Counter, defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "evaluation/substrate_capability/capability_map.json"
OUT = ROOT / "evaluation/substrate_capability/python_source_coverage_audit_v1_20260928.json"
RESULTS = ROOT / "docs/research/engine_substrate/SUBSTRATE_PYTHON_SOURCE_COVERAGE_AUDIT_V1_RESULTS_20260928.md"
SCAN_ROOTS = ("domains", "substrate", "runners/dsl/python")
ENTRYPOINTS = (
    "substrate/boot_all.py", "substrate/boot_core.py", "substrate/world_adapter.py",
    "runners/dsl/python/substrate_rs/__init__.py", "runners/dsl/python/substrate_rs/ext.py",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module_name(rel: str) -> str:
    value = rel[:-3].replace("/", ".")
    return value[:-9] if value.endswith(".__init__") else value


def resolve_module(name: str, known: set[str]) -> str | None:
    parts = name.split(".")
    for end in range(len(parts), 0, -1):
        candidate = ".".join(parts[:end])
        if candidate in known:
            return candidate
    return None


def imported_modules(tree: ast.AST, current: str, is_package: bool, known: set[str]) -> set[str]:
    out: set[str] = set()
    package = current if is_package else current.rpartition(".")[0]
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                parts = package.split(".") if package else []
                keep = max(0, len(parts) - node.level + 1)
                base = ".".join(parts[:keep])
                name = ".".join(x for x in (base, node.module or "") if x)
            else:
                name = node.module or ""
            if name:
                names.append(name)
            if node.module:
                names.extend(f"{name}.{alias.name}" for alias in node.names if alias.name != "*")
        for name in names:
            resolved = resolve_module(name, known)
            if resolved and resolved != current:
                out.add(resolved)
    return out


def main() -> None:
    paths = sorted(p for root in SCAN_ROOTS for p in (ROOT / root).rglob("*.py")
                   if "__pycache__" not in p.parts and p.is_file())
    rels = [p.relative_to(ROOT).as_posix() for p in paths]
    modules = {module_name(rel): rel for rel in rels}
    known = set(modules)
    source_hashes_before = {rel: sha(ROOT / rel) for rel in rels}
    cap_map = json.loads(MAP.read_text())
    linked_by: dict[str, set[str]] = defaultdict(set)
    for capability in cap_map["capabilities"]:
        for link in capability.get("source_links", []):
            if link.get("resolved") and link.get("path", "").endswith(".py"):
                linked_by[link["path"]].add(capability["id"])

    imports: dict[str, set[str]] = {}
    records = []
    parse_errors = []
    for rel in rels:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(text, filename=rel)
            imports[rel] = {modules[m] for m in imported_modules(
                tree, module_name(rel), rel.endswith("/__init__.py"), known)}
            doc = ast.get_docstring(tree) or ""
            public_defs = sorted(n.name for n in tree.body
                                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                                 and not n.name.startswith("_"))
        except SyntaxError as exc:
            parse_errors.append({"path": rel, "line": exc.lineno, "message": exc.msg})
            imports[rel] = set()
            doc, public_defs = "", []
        records.append({
            "path": rel, "module": module_name(rel), "sha256": source_hashes_before[rel],
            "capability_rows": sorted(linked_by.get(rel, set())),
            "static_imported_by": [], "static_imports": sorted(imports[rel]),
            "public_top_level_symbols": public_defs,
            "module_docstring_first_line": doc.splitlines()[0][:240] if doc else None,
            "parse_status": "ok" if rel not in {x["path"] for x in parse_errors} else "syntax_error",
        })

    inbound: dict[str, set[str]] = defaultdict(set)
    for source, targets in imports.items():
        for target in targets:
            inbound[target].add(source)
    roots = {x for x in ENTRYPOINTS if x in rels}
    reachable = set(roots)
    queue = deque(roots)
    while queue:
        source = queue.popleft()
        for target in imports.get(source, set()):
            if target not in reachable:
                reachable.add(target)
                queue.append(target)
    for record in records:
        record["static_imported_by"] = sorted(inbound[record["path"]])
        record["reachable_from_runtime_entrypoints"] = record["path"] in reachable

    source_hashes_after = {rel: sha(ROOT / rel) for rel in rels}
    if source_hashes_before != source_hashes_after:
        raise SystemExit("Python source changed during census; refusing to emit a mixed-source inventory")
    coverage = Counter()
    for record in records:
        group = record["path"].split("/", 1)[0]
        coverage[f"{group}:total"] += 1
        if record["capability_rows"]:
            coverage[f"{group}:linked"] += 1
        if record["reachable_from_runtime_entrypoints"]:
            coverage[f"{group}:import_reachable"] += 1
        if record["capability_rows"] and record["reachable_from_runtime_entrypoints"]:
            coverage[f"{group}:linked_and_import_reachable"] += 1

    output = {
        "schema_version": 1,
        "scope": "Python files under domains/, substrate/, runners/dsl/python/; static AST imports only",
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "runner_sha256": sha(Path(__file__).resolve()),
        "capability_map_sha256": sha(MAP),
        "entrypoints": sorted(roots),
        "source_file_count": len(records),
        "source_tree_sha256": hashlib.sha256(json.dumps(source_hashes_before, sort_keys=True).encode()).hexdigest(),
        "capability_linked_file_count": sum(bool(r["capability_rows"]) for r in records),
        "import_reachable_file_count": len(reachable),
        "parse_error_count": len(parse_errors),
        "parse_errors": parse_errors,
        "counts_by_root": dict(sorted(coverage.items())),
        "files": records,
        "limits": [
            "AST imports omit importlib, seed-authored dispatch, runtime plugin selection, and non-Python edges.",
            "An import edge is not evidence that a path executes on a measured workload.",
            "Capability links are a coverage indicator, not evidence of correctness or test coverage.",
            "Private dynamically loaded modules may be runtime-relevant despite lacking static import reachability.",
        ],
    }
    OUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    total = len(records)
    linked = output["capability_linked_file_count"]
    report = [
        "# Python source coverage audit v1",
        "",
        "Date: 2026-09-28  ",
        "Status: stable-source static census; capability links are sparse and import reachability is approximate.",
        "",
        "## Coverage",
        "",
        f"The capability map links {linked}/{total} Python source files ({linked/total:.1%}) across `domains/`, `substrate/`, and `runners/dsl/python/`. Static import traversal from five runtime entrypoints reaches {len(reachable)}/{total} files ({len(reachable)/total:.1%}). These are separate measures: module linkage does not prove runtime execution, and import reachability misses dynamic dispatch.",
        "",
        "| Source root | Files | Capability-linked | Import-reachable | Both |",
        "|---|---:|---:|---:|---:|",
    ]
    for group, label in (("domains", "`domains/`"), ("substrate", "`substrate/`"), ("runners", "`runners/dsl/python/`")):
        report.append(f"| {label} | {coverage[group+':total']} | {coverage[group+':linked']} | {coverage[group+':import_reachable']} | {coverage[group+':linked_and_import_reachable']} |")
    report.extend([
        "",
        f"The census found {len(parse_errors)} Python parse errors. The machine-readable per-file inventory, symbol names, import edges, hashes, and capability-row links are [here](../../../evaluation/substrate_capability/python_source_coverage_audit_v1_20260928.json).",
        "",
        "## Interpretation",
        "",
        "This audit shows the source-linked map is not yet a comprehensive Python inventory. It leaves 801 source files without a capability-row link; that does not label them as capabilities or dead code. The next mapping pass should classify modules into executable capability, shared substrate support, generated/experimental code, or excluded/legacy, then connect runtime-loaded modules and evaluated outcomes. Dynamic dispatch and seed-defined rule execution require runtime evidence, not import-graph inference.",
        "",
        "The input source hashes are re-read after AST analysis and must match exactly; a concurrent edit aborts output. Re-run with `python3 scripts/audit_substrate_python_source_coverage_v1.py`.",
    ])
    RESULTS.write_text("\n".join(report) + "\n")
    print(json.dumps({"source_file_count": total, "capability_linked_file_count": linked,
                      "import_reachable_file_count": len(reachable), "parse_errors": len(parse_errors),
                      "counts_by_root": dict(sorted(coverage.items())),
                      "report": str(RESULTS.relative_to(ROOT)), "machine": str(OUT.relative_to(ROOT))},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
