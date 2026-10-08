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
OUT = ROOT / "evaluation/substrate_capability/python_source_coverage_audit_v1_4_20260928.json"
RESULTS = ROOT / "docs/research/engine_substrate/SUBSTRATE_PYTHON_SOURCE_COVERAGE_AUDIT_V1_4_RESULTS_20260928.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_PYTHON_SOURCE_COVERAGE_AUDIT_V1_4_AMENDMENT_20260928.md"
SCAN_ROOTS = ("domains", "substrate", "runners/dsl/python")
ENTRYPOINTS = (
    "substrate/boot_all.py", "substrate/boot_core.py", "substrate/world_adapter.py",
    "substrate/boot_profiles.py",
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
    cap_map_hash_before = sha(MAP)
    cap_map = json.loads(MAP.read_text())
    linked_by: dict[str, set[str]] = defaultdict(set)
    for capability in cap_map["capabilities"]:
        for link in capability.get("source_links", []):
            if link.get("resolved") and link.get("path", "").endswith(".py"):
                linked_by[link["path"]].add(capability["id"])

    imports: dict[str, set[str]] = {}
    declared_runtime_loads: dict[str, set[str]] = defaultdict(set)
    records = []
    parse_errors = []
    for rel in rels:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(text, filename=rel)
            imports[rel] = {modules[m] for m in imported_modules(
                tree, module_name(rel), rel.endswith("/__init__.py"), known)}
            for node in ast.walk(tree):
                if isinstance(node, (ast.Assign, ast.AnnAssign)):
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    value = node.value
                    if any(isinstance(t, ast.Name) and t.id == "CONVERSATION_RUNTIME_MODULES"
                           for t in targets) and isinstance(value, (ast.Tuple, ast.List)):
                        for item in value.elts:
                            if isinstance(item, ast.Constant) and isinstance(item.value, str):
                                resolved = resolve_module(item.value, known)
                                if resolved:
                                    declared_runtime_loads[rel].add(modules[resolved])
                if isinstance(node, ast.Call):
                    fn = node.func
                    is_import_call = ((isinstance(fn, ast.Name) and fn.id == "import_module")
                                      or (isinstance(fn, ast.Attribute) and fn.attr == "import_module"))
                    if is_import_call and node.args and isinstance(node.args[0], ast.Constant):
                        value = node.args[0].value
                        if isinstance(value, str):
                            resolved = resolve_module(value, known)
                            if resolved:
                                declared_runtime_loads[rel].add(modules[resolved])
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
            "declared_runtime_load_sources": [],
            "public_top_level_symbols": public_defs,
            "module_docstring_first_line": doc.splitlines()[0][:240] if doc else None,
            "parse_status": "ok" if rel not in {x["path"] for x in parse_errors} else "syntax_error",
        })

    inbound: dict[str, set[str]] = defaultdict(set)
    for source, targets in imports.items():
        for target in targets:
            inbound[target].add(source)
    roots = {x for x in ENTRYPOINTS if x in rels}
    static_reachable = set(roots)
    queue = deque(roots)
    while queue:
        source = queue.popleft()
        for target in imports.get(source, set()):
            if target not in static_reachable:
                static_reachable.add(target)
                queue.append(target)
    dynamic_edges = {source: targets for source, targets in declared_runtime_loads.items()}
    runtime_reachable = set(roots)
    queue = deque(roots)
    while queue:
        source = queue.popleft()
        for target in imports.get(source, set()) | dynamic_edges.get(source, set()):
            if target not in runtime_reachable:
                runtime_reachable.add(target)
                queue.append(target)
    # Seed manifests define graph-native rules/data rather than Python import hooks.
    # Still inspect their string leaves for exact Python module references so this
    # boundary is evidence-based rather than assumed.
    seed_paths = sorted((ROOT / "seeds").glob("*.json")) + sorted((ROOT / "seeds/generated").glob("*.json"))
    seed_hashes_before = {p.relative_to(ROOT).as_posix(): sha(p) for p in seed_paths}
    # Exclude package names such as ``domains``: a matching folder string in a
    # seed is not evidence that the manifest imports the package.
    module_by_dotted = {module_name(rel): rel for rel in rels if "." in module_name(rel)}
    seed_module_refs: dict[str, set[str]] = defaultdict(set)
    seed_manifest_records = []
    def walk_strings(value):
        if isinstance(value, str):
            if value in module_by_dotted:
                return {value}
            return set()
        if isinstance(value, dict):
            found = set()
            for item in value.values():
                found.update(walk_strings(item))
            return found
        if isinstance(value, list):
            found = set()
            for item in value:
                found.update(walk_strings(item))
            return found
        return set()
    seed_parse_errors = []
    for path in seed_paths:
        rel = path.relative_to(ROOT).as_posix()
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            loader_eligible = isinstance(manifest, dict) and not manifest.get("self_load_only")
            seed_manifest_records.append({"path": rel, "sha256": seed_hashes_before[rel],
                                          "loader_eligible": loader_eligible})
            refs = walk_strings(manifest) if loader_eligible else set()
            for ref in refs:
                seed_module_refs[rel].add(module_by_dotted[ref])
        except (OSError, json.JSONDecodeError) as exc:
            seed_parse_errors.append({"path": rel, "error": type(exc).__name__})
            seed_manifest_records.append({"path": rel, "sha256": seed_hashes_before[rel],
                                          "loader_eligible": False})
    for record in records:
        record["static_imported_by"] = sorted(inbound[record["path"]])
        record["reachable_from_static_entrypoints"] = record["path"] in static_reachable
        record["reachable_from_declared_runtime_loads"] = record["path"] in runtime_reachable
        record["declared_runtime_load_sources"] = sorted(
            source for source, targets in declared_runtime_loads.items() if record["path"] in targets)
        record["exact_seed_module_refs"] = sorted(
            seed for seed, targets in seed_module_refs.items() if record["path"] in targets)

    source_hashes_after = {rel: sha(ROOT / rel) for rel in rels}
    cap_map_hash_after = sha(MAP)
    seed_hashes_after = {p.relative_to(ROOT).as_posix(): sha(p) for p in seed_paths}
    if (source_hashes_before != source_hashes_after
            or seed_hashes_before != seed_hashes_after
            or cap_map_hash_before != cap_map_hash_after):
        raise SystemExit("Python or seed source changed during census; refusing a mixed-source inventory")
    coverage = Counter()
    for record in records:
        group = record["path"].split("/", 1)[0]
        coverage[f"{group}:total"] += 1
        if record["capability_rows"]:
            coverage[f"{group}:linked"] += 1
        if record["reachable_from_static_entrypoints"]:
            coverage[f"{group}:static_reachable"] += 1
        if record["reachable_from_declared_runtime_loads"]:
            coverage[f"{group}:runtime_reachable"] += 1
        if record["capability_rows"] and record["reachable_from_declared_runtime_loads"]:
            coverage[f"{group}:linked_and_runtime_reachable"] += 1
        if record["declared_runtime_load_sources"]:
            coverage[f"{group}:declared_dynamic_load"] += 1
        if record["exact_seed_module_refs"]:
            coverage[f"{group}:seed_exact_module_ref"] += 1

    output = {
        "schema_version": 2,
        "scope": "Python source census plus static imports, literal profile importlib targets, and exact module-name references in loader-eligible boot_all seed manifests",
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "runner_sha256": sha(Path(__file__).resolve()),
        "amendment_sha256": sha(AMENDMENT),
        "capability_map_sha256": cap_map_hash_before,
        "entrypoints": sorted(roots),
        "source_file_count": len(records),
        "source_tree_sha256": hashlib.sha256(json.dumps(source_hashes_before, sort_keys=True).encode()).hexdigest(),
        "capability_linked_file_count": sum(bool(r["capability_rows"]) for r in records),
        "static_import_reachable_file_count": len(static_reachable),
        "declared_runtime_reachable_file_count": len(runtime_reachable),
        "declared_runtime_load_count": sum(len(v) for v in declared_runtime_loads.values()),
        "declared_runtime_load_modules": sorted({p for targets in declared_runtime_loads.values() for p in targets}),
        "seed_manifest_file_count": len(seed_paths),
        "seed_loader_eligible_manifest_count": sum(r["loader_eligible"] for r in seed_manifest_records),
        "seed_manifest_tree_sha256": hashlib.sha256(json.dumps(seed_hashes_before, sort_keys=True).encode()).hexdigest(),
        "seed_manifest_hashes": seed_hashes_before,
        "seed_manifest_records": seed_manifest_records,
        "exact_seed_python_module_reference_count": sum(len(v) for v in seed_module_refs.values()),
        "seed_manifest_parse_error_count": len(seed_parse_errors),
        "seed_manifest_parse_errors": seed_parse_errors,
        "parse_error_count": len(parse_errors),
        "parse_errors": parse_errors,
        "counts_by_root": dict(sorted(coverage.items())),
        "files": records,
        "limits": [
            "Dynamic-load extraction recognizes literal import_module arguments and the literal CONVERSATION_RUNTIME_MODULES tuple; arbitrary computed imports remain unresolved.",
            "Seed manifest matching detects exact dotted Python module names in string values; seed rules may dispatch by other mechanisms not represented as module names.",
            "An import edge is not evidence that a path executes on a measured workload.",
            "Capability links are a coverage indicator, not evidence of correctness or test coverage.",
            "Private dynamically loaded modules may be runtime-relevant despite lacking static import reachability.",
        ],
    }
    OUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    total = len(records)
    linked = output["capability_linked_file_count"]
    report = [
        "# Python source coverage audit v1.4",
        "",
        "Date: 2026-09-28  ",
        "Status: stable-source static census; capability links are sparse and import reachability is approximate.",
        "",
        "## Coverage",
        "",
        f"The capability map links {linked}/{total} Python source files ({linked/total:.1%}) across `domains/`, `substrate/`, and `runners/dsl/python/`. Static imports from six runtime entrypoints reach {len(static_reachable)}/{total}; adding literal profile `importlib` loads reaches {len(runtime_reachable)}/{total}. `CONVERSATION_RUNTIME_MODULES` declares {sum(len(v) for v in declared_runtime_loads.values())} module loads, with {len({p for targets in declared_runtime_loads.values() for p in targets})} distinct Python files. Exact dotted Python module strings occur in {sum(len(v) for v in seed_module_refs.values())} of {sum(r['loader_eligible'] for r in seed_manifest_records)} eligible seed manifests ({len(seed_paths)} discovered). These are navigation and declared-load signals, not proof each module executed in a specific task.",
        "",
        "| Source root | Files | Capability-linked | Static import-reachable | Declared runtime-reachable | Both linked and runtime-reachable |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for group, label in (("domains", "`domains/`"), ("substrate", "`substrate/`"), ("runners", "`runners/dsl/python/`")):
        report.append(f"| {label} | {coverage[group+':total']} | {coverage[group+':linked']} | {coverage[group+':static_reachable']} | {coverage[group+':runtime_reachable']} | {coverage[group+':linked_and_runtime_reachable']} |")
    report.extend([
        "",
        f"The census found {len(parse_errors)} Python parse errors and {len(seed_parse_errors)} malformed loader-selected seed manifests. The machine-readable per-file inventory, symbols, import edges, declared dynamic loads, exact seed module-name references, hashes, and capability-row links are [here](../../../evaluation/substrate_capability/python_source_coverage_audit_v1_4_20260928.json).",
        "",
        "## Interpretation",
        "",
        "This audit shows the source-linked map is not yet a comprehensive Python inventory. Unlinked files are not thereby capabilities or dead code. The next mapping pass should classify modules into executable capability, shared substrate support, generated/experimental code, or excluded/legacy, then connect runtime-loaded modules and evaluated outcomes. Static or declared reachability does not establish execution on a workload.",
        "",
        "Python sources, the exact top-level plus `seeds/generated/*.json` loader manifests, and the capability map are hashed before and after analysis; any concurrent change aborts output. Re-run with `python3 scripts/audit_substrate_python_source_coverage_v1_4.py`.",
    ])
    RESULTS.write_text("\n".join(report) + "\n")
    print(json.dumps({"source_file_count": total, "capability_linked_file_count": linked,
                      "static_import_reachable_file_count": len(static_reachable),
                      "declared_runtime_reachable_file_count": len(runtime_reachable),
                      "declared_runtime_load_count": sum(len(v) for v in declared_runtime_loads.values()),
                      "seed_module_references": sum(len(v) for v in seed_module_refs.values()),
                      "parse_errors": len(parse_errors),
                      "counts_by_root": dict(sorted(coverage.items())),
                      "report": str(RESULTS.relative_to(ROOT)), "machine": str(OUT.relative_to(ROOT))},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
