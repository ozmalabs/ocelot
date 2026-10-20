#!/usr/bin/env python3
"""Report per-seed boot classification, rule/production counts, guard hints, and broken dependencies.

Classification (COGNITION_BUILD_P0_BASELINE_PLAN.md §P0.H3):
  - C:    in substrate.boot_core.CORE_SEEDS, or in its depends_on closure.
  - OPT:  in substrate.boot_core.OPTIONAL_CORE_SEEDS (or its depends_on closure not in C).
  - Prof: in substrate.boot_profiles.CONVERSATION_SEED_ANCHORS, or in its depends_on closure
          (excluding C, OPT, and self_load_only seeds which load_all_seeds skips).
  - SLO:  manifest has self_load_only: true.
  - Bulk: everything else.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from substrate.boot_core import CORE_SEEDS, OPTIONAL_CORE_SEEDS
from substrate.boot_profiles import CONVERSATION_SEED_ANCHORS

_POLICY_TYPE_RE = re.compile(r"^(Held[A-Za-z0-9_]*Params|[A-Za-z0-9_]*Policy)$")
_POLICY_EDGE_RE = re.compile(r"^has_[a-z0-9_]*(?:policy|params)$")


def _collect_where_guards(node: object, hints: set[str]) -> None:
    if isinstance(node, dict):
        t = node.get("type")
        if t == "Attr" and isinstance(node.get("key"), str):
            k = node["key"]
            if k == "enabled" or k.endswith("_on") or k.endswith("_enabled"):
                hints.add(k)
        elif t == "NodesOfType" and isinstance(node.get("node_type"), str):
            nt = node["node_type"]
            if _POLICY_TYPE_RE.match(nt):
                hints.add(nt)
        for v in node.values():
            _collect_where_guards(v, hints)
    elif isinstance(node, list):
        for item in node:
            _collect_where_guards(item, hints)


def _dependency_closure(anchors: set[str], manifests: dict[str, dict], skip_slo: bool = False) -> set[str]:
    visited: set[str] = set()
    stack = list(anchors)
    while stack:
        sid = stack.pop()
        if sid in visited or sid not in manifests:
            continue
        if skip_slo and manifests[sid].get("self_load_only"):
            continue
        visited.add(sid)
        for dep in manifests[sid].get("depends_on", ()) or ():
            dep_str = str(dep)
            if dep_str not in visited:
                stack.append(dep_str)
    return visited


def build_seed_boot_report(root: Path = ROOT) -> dict[str, dict]:
    seed_dir = root / "seeds"
    manifests: dict[str, dict] = {}
    for path in sorted(seed_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        sid = path.stem
        manifests[sid] = data

    core_closure = _dependency_closure(set(CORE_SEEDS), manifests, skip_slo=False)
    opt_closure = _dependency_closure(set(OPTIONAL_CORE_SEEDS), manifests, skip_slo=False) - core_closure
    prof_closure = (
        _dependency_closure(set(CONVERSATION_SEED_ANCHORS), manifests, skip_slo=True)
        - core_closure
        - opt_closure
    )

    report: dict[str, dict] = {}
    for sid in sorted(manifests.keys()):
        m = manifests[sid]
        is_slo = bool(m.get("self_load_only"))
        if sid in core_closure:
            cls = "C"
        elif sid in opt_closure:
            cls = "OPT"
        elif is_slo:
            cls = "SLO"
        elif sid in prof_closure:
            cls = "Prof"
        else:
            cls = "Bulk"

        deps = [str(d) for d in (m.get("depends_on") or ()) if isinstance(d, str)]
        broken_deps = [d for d in deps if not (seed_dir / f"{d}.json").exists()]

        exec_rules = 0
        decl_principles = len(m.get("principles", ()) or ())
        guard_hints: set[str] = set()

        for node in m.get("nodes", ()) or ():
            if isinstance(node, dict) and isinstance(node.get("type"), str):
                nt = node["type"]
                if _POLICY_TYPE_RE.match(nt):
                    guard_hints.add(nt)

        for rule in m.get("rules", ()) or ():
            if not isinstance(rule, dict):
                continue
            if "match" in rule:
                exec_rules += 1
                for triple in rule.get("match", ()) or ():
                    if isinstance(triple, list) and len(triple) >= 2 and isinstance(triple[1], str):
                        if _POLICY_EDGE_RE.match(triple[1]):
                            guard_hints.add(triple[1])
                _collect_where_guards(rule.get("where"), guard_hints)
            elif any(k in rule for k in ("head", "body", "if", "then")):
                decl_principles += 1

        productions = len(m.get("productions", ()) or ())
        concepts = len(m.get("concepts", ()) or ())

        report[sid] = {
            "id": sid,
            "class": cls,
            "self_load_only": is_slo,
            "depends_on": deps,
            "executable_rules": exec_rules,
            "productions": productions,
            "declarative_principles": decl_principles,
            "concepts": concepts,
            "guard_hints": sorted(guard_hints),
            "broken_deps": broken_deps,
        }
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="Report seed boot status and counts.")
    ap.add_argument("--json", action="store_true", help="Print JSON output to stdout")
    ap.add_argument("--out", default=None, help="Write JSON report to file")
    args = ap.parse_args()

    report = build_seed_boot_report(ROOT)
    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        hdr = f"{'SEED ID':42s} {'CLASS':5s} {'RULES':5s} {'PRODS':5s} {'DECL':5s} {'CONC':5s} {'GUARD HINTS':28s} {'BROKEN DEPS'}"
        print(hdr)
        print("-" * len(hdr))
        for sid, row in report.items():
            guards = ",".join(row["guard_hints"][:2])
            bdeps = ",".join(row["broken_deps"])
            print(
                f"{sid:42s} {row['class']:5s} {row['executable_rules']:5d} "
                f"{row['productions']:5d} {row['declarative_principles']:5d} "
                f"{row['concepts']:5d} {guards:28s} {bdeps}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
