"""Deterministically audit the consolidated graph-native motor manifests.

No substrate or simulator is booted.  The audit reads checked-in seed JSON,
counts authored scheduling sheets and areas, verifies candidate selectors are
anchored to an actor or episode, and compares hard-sheet population with a Git
baseline derived from history rather than a hand-authored target.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import subprocess
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = ROOT / "protocols" / "motor_core_audit_v1.json"
SHEET_NAMES = {
    "hard_realtime": "hard",
    "soft_realtime": "soft",
    "background": "background",
}


class MotorCoreAuditError(RuntimeError):
    """The audit inputs or Git baseline could not be resolved."""


def _walk(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _match_edges(rule: dict[str, Any]) -> list[tuple[str, str]]:
    edges = []
    for pattern in rule.get("match", []):
        if (
            isinstance(pattern, list)
            and len(pattern) >= 3
            and isinstance(pattern[0], str)
            and isinstance(pattern[2], str)
        ):
            edges.append((pattern[0], pattern[2]))
    return edges


def _scoped_variables(
    rule: dict[str, Any],
    anchor_fragments: tuple[str, ...],
) -> set[str]:
    adjacency: dict[str, set[str]] = defaultdict(set)
    for source, target in _match_edges(rule):
        adjacency[source].add(target)
        adjacency[target].add(source)
    anchors = {
        variable
        for variable in adjacency
        if any(fragment in variable.lower() for fragment in anchor_fragments)
    }
    scoped = set(anchors)
    frontier = list(sorted(anchors))
    while frontier:
        variable = frontier.pop()
        for neighbour in adjacency[variable]:
            if neighbour not in scoped:
                scoped.add(neighbour)
                frontier.append(neighbour)
    return scoped


def _candidate_scope_report(
    seed: dict[str, Any],
    contract: dict[str, Any],
) -> dict[str, Any]:
    selector_types = set(contract["selector_types"])
    forbidden = set(contract["forbidden_global_sources"])
    anchor_fragments = tuple(contract["anchor_variable_fragments"])
    violations = []
    selector_count = 0
    scoped_count = 0
    global_source_count = 0
    for rule in seed.get("rules", []):
        scoped_variables = _scoped_variables(rule, anchor_fragments)
        for ordinal, node in enumerate(_walk(rule)):
            if node.get("type") not in selector_types:
                continue
            selector_count += 1
            source = node.get("source")
            source_nodes = list(_walk(source))
            forbidden_types = sorted({
                item.get("type")
                for item in source_nodes
                if item.get("type") in forbidden
            })
            roots = sorted({
                neighbour["node"]["name"]
                for neighbour in source_nodes
                if neighbour.get("type") == "Neighbours"
                and isinstance(neighbour.get("node"), dict)
                and neighbour["node"].get("type") == "Var"
                and isinstance(neighbour["node"].get("name"), str)
            })
            locally_bound = {
                item["var_name"]
                for item in source_nodes
                if isinstance(item.get("var_name"), str)
            }
            unscoped_roots = [
                variable
                for variable in roots
                if variable not in scoped_variables
                and variable not in locally_bound
            ]
            reasons = []
            if forbidden_types:
                global_source_count += 1
                reasons.append(
                    "global candidate source: " + ",".join(forbidden_types)
                )
            if not roots:
                reasons.append("candidate source has no scoped neighbour root")
            elif unscoped_roots:
                reasons.append(
                    "roots not actor/episode connected: "
                    + ",".join(unscoped_roots)
                )
            if reasons:
                violations.append({
                    "rule": rule.get("name", "<unnamed>"),
                    "selector_ordinal": ordinal,
                    "reasons": reasons,
                    "source_roots": roots,
                })
            else:
                scoped_count += 1
    return {
        "selector_count": selector_count,
        "actor_or_episode_scoped_count": scoped_count,
        "global_source_count": global_source_count,
        "violation_count": len(violations),
        "passed": not violations,
        "violations": violations,
    }


def audit_seed(
    seed: dict[str, Any],
    *,
    role: str,
    path: str,
    scope_contract: dict[str, Any],
) -> dict[str, Any]:
    """Return the stable structural report for one seed manifest."""
    default_latency = seed.get("latency_class")
    default_area = seed.get("area", "<unassigned>")
    sheets = Counter({"hard": 0, "soft": 0, "background": 0})
    unknown_latency_classes = Counter()
    areas: dict[str, Counter[str]] = defaultdict(Counter)
    for rule in seed.get("rules", []):
        latency = rule.get("latency_class", default_latency)
        sheet = SHEET_NAMES.get(latency)
        area = str(rule.get("area", default_area))
        if sheet is None:
            unknown_latency_classes[str(latency)] += 1
            areas[area]["unknown"] += 1
        else:
            sheets[sheet] += 1
            areas[area][sheet] += 1
        areas[area]["total"] += 1
    area_rows = {
        area: {
            "hard": counts["hard"],
            "soft": counts["soft"],
            "background": counts["background"],
            "unknown": counts["unknown"],
            "total": counts["total"],
        }
        for area, counts in sorted(areas.items())
    }
    return {
        "role": role,
        "seed_id": seed.get("id"),
        "version": seed.get("version"),
        "path": path,
        "depends_on": list(seed.get("depends_on", [])),
        "rule_count": len(seed.get("rules", [])),
        "sheets": {
            "hard": sheets["hard"],
            "soft": sheets["soft"],
            "background": sheets["background"],
            "unknown": sum(unknown_latency_classes.values()),
        },
        "unknown_latency_classes": dict(sorted(
            unknown_latency_classes.items()
        )),
        "areas": area_rows,
        "candidate_scope": _candidate_scope_report(seed, scope_contract),
    }


def _git(
    root: Path,
    *args: str,
    required: bool = True,
) -> str | None:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode == 0:
        return completed.stdout.strip()
    if required:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise MotorCoreAuditError(
            f"git {' '.join(args)} failed: {detail}"
        )
    return None


def resolve_baseline_revision(
    root: Path,
    explicit_revision: str | None = None,
) -> dict[str, str]:
    """Resolve an explicit revision or the first parent of current HEAD."""
    if explicit_revision is not None:
        resolved = _git(root, "rev-parse", "--verify", explicit_revision)
        assert resolved is not None
        return {
            "source": "explicit",
            "requested_revision": explicit_revision,
            "resolved_revision": resolved,
        }
    parent_line = _git(root, "rev-list", "--parents", "-n", "1", "HEAD")
    assert parent_line is not None
    parts = parent_line.split()
    if len(parts) < 2:
        raise MotorCoreAuditError(
            "HEAD has no parent; pass --baseline-revision explicitly"
        )
    source = "merge_parent_first" if len(parts) > 2 else "head_parent"
    return {
        "source": source,
        "requested_revision": "HEAD^1",
        "resolved_revision": parts[1],
    }


def _seed_at_revision(
    root: Path,
    revision: str,
    path: str,
) -> dict[str, Any] | None:
    top_level_text = _git(root, "rev-parse", "--show-toplevel")
    assert top_level_text is not None
    top_level = Path(top_level_text)
    try:
        repository_path = (root / path).relative_to(top_level).as_posix()
    except ValueError as exc:
        raise MotorCoreAuditError(
            f"manifest path escapes repository: {path}"
        ) from exc
    rendered = _git(
        root,
        "show",
        f"{revision}:{repository_path}",
        required=False,
    )
    if rendered is None:
        return None
    try:
        return json.loads(rendered)
    except json.JSONDecodeError as exc:
        raise MotorCoreAuditError(
            f"{path} at {revision} is not valid JSON"
        ) from exc


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MotorCoreAuditError(f"cannot load {path}: {exc}") from exc


def build_report(
    *,
    root: Path = ROOT,
    protocol_path: Path = DEFAULT_PROTOCOL,
    baseline_revision: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic report from current files and one Git baseline."""
    root = root.resolve()
    protocol_path = protocol_path.resolve()
    protocol = _load_json(protocol_path)
    contract = protocol["candidate_scope_contract"]
    manifests = []
    baseline = resolve_baseline_revision(root, baseline_revision)
    baseline_rows = []
    identity_violations = []
    for entry in protocol["manifests"]:
        relative_path = entry["path"]
        seed = _load_json(root / relative_path)
        if seed.get("id") != entry["seed_id"]:
            identity_violations.append({
                "role": entry["role"],
                "expected": entry["seed_id"],
                "actual": seed.get("id"),
            })
        current_row = audit_seed(
            seed,
            role=entry["role"],
            path=relative_path,
            scope_contract=contract,
        )
        manifests.append(current_row)
        old_seed = _seed_at_revision(
            root,
            baseline["resolved_revision"],
            relative_path,
        )
        old_hard = None
        if old_seed is not None:
            old_hard = audit_seed(
                old_seed,
                role=entry["role"],
                path=relative_path,
                scope_contract=contract,
            )["sheets"]["hard"]
        baseline_rows.append({
            "role": entry["role"],
            "path": relative_path,
            "available": old_seed is not None,
            "hard": old_hard,
            "current_hard": current_row["sheets"]["hard"],
            "hard_delta": (
                current_row["sheets"]["hard"] - old_hard
                if old_hard is not None
                else None
            ),
        })
    current_hard = sum(row["sheets"]["hard"] for row in manifests)
    comparable_baseline_hard = sum(
        row["hard"]
        for row in baseline_rows
        if row["hard"] is not None
    )
    comparable_current_hard = sum(
        row["current_hard"]
        for row in baseline_rows
        if row["hard"] is not None
    )
    scope_passed = all(
        row["candidate_scope"]["passed"]
        for row in manifests
    )
    no_global_sources = all(
        row["candidate_scope"]["global_source_count"] == 0
        for row in manifests
    )
    latency_passed = all(
        not row["unknown_latency_classes"]
        for row in manifests
    )
    invariants = {
        "manifest_identity_matches_protocol": not identity_violations,
        "latency_classes_are_known": latency_passed,
        "candidate_selectors_are_actor_or_episode_scoped": scope_passed,
        "no_global_candidate_sources": no_global_sources,
    }
    invariants["passed"] = all(invariants.values())
    current_revision = _git(root, "rev-parse", "HEAD")
    assert current_revision is not None
    return {
        "schema_version": 1,
        "benchmark": protocol["protocol"],
        "protocol_path": str(protocol_path.relative_to(root)),
        "current_revision": current_revision,
        "manifests": manifests,
        "totals": {
            "manifest_count": len(manifests),
            "rule_count": sum(row["rule_count"] for row in manifests),
            "sheets": {
                sheet: sum(row["sheets"][sheet] for row in manifests)
                for sheet in ("hard", "soft", "background", "unknown")
            },
            "candidate_selector_count": sum(
                row["candidate_scope"]["selector_count"]
                for row in manifests
            ),
        },
        "baseline_comparison": {
            **baseline,
            "current_hard_all_manifests": current_hard,
            "comparable_current_hard": comparable_current_hard,
            "comparable_baseline_hard": comparable_baseline_hard,
            "comparable_hard_delta": (
                comparable_current_hard - comparable_baseline_hard
            ),
            "missing_manifest_count": sum(
                not row["available"] for row in baseline_rows
            ),
            "manifests": baseline_rows,
        },
        "invariants": invariants,
        "identity_violations": identity_violations,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument(
        "--baseline-revision",
        help="Git revision to compare against; defaults to HEAD's first parent",
    )
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)
    report = build_report(
        protocol_path=args.protocol,
        baseline_revision=args.baseline_revision,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_out is not None:
        args.json_out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["invariants"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
