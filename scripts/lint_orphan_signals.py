#!/usr/bin/env python3
"""Orphan-signal lint for seed rules and substrate/domain code.

SPECIFICATION (COGNITION_BUILD_P0_BASELINE_PLAN.md §P0.H2)
----------------------------------------------------------
This script loads every ``seeds/*.json`` manifest and extracts all signal
WRITES and READS across the seed library and the Rust/Python codebase.

1. WRITES: ``(kind, name)``, where ``kind`` is ``attr``, ``edge`` or ``node_type``.
   Extracted from rule ``effects`` in ``seeds/*.json``:
   - ``set_attr`` effects: ``attr`` = arg 2 (``effect[2]``).
   - ``add_edge`` effects: ``edge`` = arg 2 (``effect[2]``).
   - ``add_node`` / ``add_node_if_absent`` effects: ``node_type`` = arg 2
     (``effect[2]``), plus ``attr`` for every key in arg 3 (``effect[3]``).

2. READS in seeds (``seeds/*.json``):
   - ``match`` triples: ``edge`` = middle element (``triple[1]``);
   - every ``{"type": "Attr", "key": K}`` anywhere in ``where`` and in
     effect ``__term__`` values (and nested Term trees);
   - ``Neighbours`` / ``InNeighbours`` / ``MapNeighbours`` ``edge_type``;
   - ``NodesOfType`` ``node_type``.
   Note: A rule reading its own write (e.g., as a fixpoint guard in ``where``)
   counts as a read by design.

3. READS in code, by regex over ``runners/dsl/src/**/*.rs``, ``domains/**/*.py``
   and ``substrate/**/*.py``:
   - ``intern\\("([A-Za-z_][A-Za-z0-9_]*)"\\)``
   - ``\\.get\\("([A-Za-z_][A-Za-z0-9_]*)"\\)`` (and single-quoted equivalent)
   - ``\\["attrs"\\]\\["([A-Za-z_][A-Za-z0-9_]*)"\\]`` (and single-quoted equivalent)
   - ``\\.nodes\\("([A-Za-z_][A-Za-z0-9_]*)"\\)`` (and single-quoted equivalent)
   - ``neighbours\\([^,]+,\\s*"([A-Za-z_][A-Za-z0-9_]*)"\\)`` (and single-quoted equivalent)

4. ORPHAN DEFINITION:
   A WRITE whose ``name`` never appears as a READ in any seed or code file.
   When a name is written as multiple kinds (e.g., ``needs_decomposition``
   written as both an ``edge`` and an ``attr``), ``kind`` records the primary
   kind (or ``/``-joined sorted kinds if multiple) and ``writers`` lists all
   ``seed:rule`` writers in deterministic sorted order.

5. ALLOWLIST POLICY:
   ``scripts/orphan_signal_allowlist.json`` maps ``{name: reason}`` for known
   terminal, diagnostic, or provenance-only signals (such as ``provenance_kind``,
   ``terminal_reason``, or redundant witnesses like ``obs_established``).
   Allowlisted entries retain their ``reason`` in the JSON output and can be
   filtered in the human report while remaining auditable.

6. OUTPUT:
   JSON ``{name: {"kind": kind, "writers": [seed:rule, ...], "reason": ...}}``
   (``reason`` present when allowlisted), plus a human-readable summary table.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ALLOWLIST = ROOT / "scripts" / "orphan_signal_allowlist.json"

_CODE_READ_PATTERNS = (
    re.compile(r'intern\("([A-Za-z_][A-Za-z0-9_]*)"\)'),
    re.compile(r'\.get\(\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']'),
    re.compile(r'\[["\']attrs["\']\]\[\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']\s*\]'),
    re.compile(r'\.nodes\(\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']\s*\)'),
    re.compile(r'neighbours\([^,]+,\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']'),
)


def _walk_term_reads(node: object, reads: set[tuple[str, str]]) -> None:
    if isinstance(node, dict):
        t = node.get("type")
        if t == "Attr" and isinstance(node.get("key"), str):
            reads.add(("attr", node["key"]))
        elif t in ("Neighbours", "InNeighbours", "MapNeighbours") and isinstance(node.get("edge_type"), str):
            reads.add(("edge", node["edge_type"]))
        elif t == "NodesOfType" and isinstance(node.get("node_type"), str):
            reads.add(("node_type", node["node_type"]))
        for v in node.values():
            _walk_term_reads(v, reads)
    elif isinstance(node, list):
        for item in node:
            _walk_term_reads(item, reads)


def _extract_seed_writes_and_reads(
    seed_dir: Path,
    exclude_seeds: set[str] | None = None,
) -> tuple[dict[tuple[str, str], set[str]], set[tuple[str, str]]]:
    writes: dict[tuple[str, str], set[str]] = {}
    reads: set[tuple[str, str]] = set()
    excluded = exclude_seeds or set()

    def record_write(kind: str, name: str, writer: str) -> None:
        if not name:
            return
        writes.setdefault((kind, name), set()).add(writer)

    for path in sorted(seed_dir.glob("*.json")):
        if path.stem in excluded:
            continue
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(manifest, dict):
            continue
        seed_id = str(manifest.get("id") or path.stem)
        if seed_id in excluded:
            continue
        production_endpoint_types: dict[str, set[tuple[str, str]]] = {}
        for production in manifest.get("productions", ()) or ():
            if not isinstance(production, dict):
                continue
            edge_type = production.get("edge_type")
            src = production.get("src", {})
            tgt = production.get("tgt", {})
            if (isinstance(edge_type, str) and isinstance(src, dict)
                    and isinstance(tgt, dict) and isinstance(src.get("type"), str)
                    and isinstance(tgt.get("type"), str)):
                production_endpoint_types.setdefault(edge_type, set()).add(
                    (src["type"], tgt["type"]))
        for rule in manifest.get("rules", ()) or ():
            if not isinstance(rule, dict):
                continue
            rule_name = str(rule.get("name") or "<unnamed>")
            writer = f"{seed_id}:{rule_name}"

            for triple in rule.get("match", ()) or ():
                if isinstance(triple, list) and len(triple) >= 2 and isinstance(triple[1], str):
                    reads.add(("edge", triple[1]))
                    # A matched edge admitted by Γ also constrains the source
                    # and target node types. Count those endpoint types as
                    # consumed so rule-produced graph objects are not reported
                    # as orphans solely because type matching is implicit.
                    for src_type, tgt_type in production_endpoint_types.get(triple[1], ()):
                        reads.add(("node_type", src_type))
                        reads.add(("node_type", tgt_type))

            _walk_term_reads(rule.get("where"), reads)

            for eff in rule.get("effects", ()) or ():
                if not isinstance(eff, list) or len(eff) < 3:
                    continue
                op = eff[0]
                if op == "set_attr":
                    if isinstance(eff[2], str):
                        record_write("attr", eff[2], writer)
                    if len(eff) >= 4:
                        _walk_term_reads(eff[3], reads)
                elif op == "add_edge":
                    if isinstance(eff[2], str):
                        record_write("edge", eff[2], writer)
                elif op in ("add_node", "add_node_if_absent"):
                    if isinstance(eff[2], str):
                        record_write("node_type", eff[2], writer)
                    if len(eff) >= 4 and isinstance(eff[3], dict):
                        for k, v in eff[3].items():
                            if isinstance(k, str):
                                record_write("attr", k, writer)
                            _walk_term_reads(v, reads)
                else:
                    for arg in eff[1:]:
                        _walk_term_reads(arg, reads)

    return writes, reads


def _extract_code_reads(root: Path) -> set[str]:
    reads: set[str] = set()
    scan_Files = (
        list(sorted((root / "runners" / "dsl" / "src").rglob("*.rs")))
        + list(sorted((root / "domains").rglob("*.py")))
        + list(sorted((root / "substrate").rglob("*.py")))
    )
    for path in scan_Files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for pat in _CODE_READ_PATTERNS:
            reads.update(pat.findall(text))
    return reads


def _load_allowlist(allowlist_path: Path | None) -> dict[str, str]:
    if allowlist_path is None or not allowlist_path.exists():
        return {}
    try:
        data = json.loads(allowlist_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items() if str(k) != "_comment"}
    except Exception:
        pass
    return {}


def scan_orphan_signals(
    root: Path = ROOT,
    allowlist_path: Path | None = DEFAULT_ALLOWLIST,
    include_code_reads: bool = True,
    exclude_seeds: set[str] | None = None,
) -> dict[str, dict]:
    """Return deterministic mapping of orphan signal names to metadata."""
    writes, seed_reads = _extract_seed_writes_and_reads(root / "seeds", exclude_seeds=exclude_seeds)
    code_reads = _extract_code_reads(root) if include_code_reads else set()
    allowlist = _load_allowlist(allowlist_path)

    grouped: dict[str, dict[str, set[str]]] = {}
    for (kind, name), writers in writes.items():
        if (kind, name) in seed_reads or name in code_reads:
            continue
        entry = grouped.setdefault(name, {"kinds": set(), "writers": set()})
        entry["kinds"].add(kind)
        entry["writers"].update(writers)

    orphans: dict[str, dict] = {}
    for name in sorted(grouped.keys()):
        kinds = sorted(grouped[name]["kinds"])
        kind_str = "/".join(kinds)
        writers = sorted(grouped[name]["writers"])
        item: dict[str, object] = {
            "kind": kind_str,
            "writers": writers,
        }
        reason = allowlist.get(name)
        if reason is None:
            for k, v in allowlist.items():
                if k.startswith(f"{name} ("):
                    reason = v
                    break
        if reason is not None:
            item["reason"] = reason
        orphans[name] = item
    return orphans


def main() -> int:
    ap = argparse.ArgumentParser(description="Lint orphan signals written by seed rules.")
    ap.add_argument("--json", action="store_true", help="Emit JSON output to stdout")
    ap.add_argument("--out", default=None, help="Write JSON output to file")
    ap.add_argument("--allowlist", default=str(DEFAULT_ALLOWLIST), help="Path to allowlist JSON")
    ap.add_argument("--seed-only", action="store_true", help="Only scan seed reads (skip Rust/Python regex scan)")
    ap.add_argument("--exclude-allowlisted", action="store_true", help="Omit allowlisted signals from output")
    args = ap.parse_args()

    allowlist_path = Path(args.allowlist) if args.allowlist else None
    orphans = scan_orphan_signals(
        root=ROOT,
        allowlist_path=allowlist_path,
        include_code_reads=not args.seed_only,
    )
    if args.exclude_allowlisted:
        orphans = {k: v for k, v in orphans.items() if "reason" not in v}

    if args.out:
        Path(args.out).write_text(json.dumps(orphans, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(orphans, indent=2, sort_keys=True))
    else:
        print(f"{'SIGNAL':40s} {'KIND':12s} {'WRITERS':8s} {'FIRST WRITER / REASON'}")
        print("-" * 100)
        for name, info in orphans.items():
            writers = info["writers"]
            first = writers[0] if writers else ""
            suffix = f" [allowlisted: {info['reason']}]" if "reason" in info else ""
            print(f"{name:40s} {info['kind']:12s} {len(writers):8d} {first}{suffix}")
        print(f"\nTotal orphans: {len(orphans)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
