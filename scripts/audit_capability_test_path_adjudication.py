"""Reconcile capability-map test links with the dated source-path audit.

This checks link presence and source-hash freshness. A path mention is not
semantic proof that the linked test supports its capability claim; that
judgement remains in the human-authored audit table.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAP = "evaluation/substrate_capability/capability_map.json"
DEFAULT_AUDIT = "docs/research/engine_substrate/SUBSTRATE_TEST_PATH_RELEVANCE_AUDIT_20260929.md"
DEFAULT_CROSSWALK = "evaluation/reports/substrate_capability_test_relevance_audit_20261003.json"


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_test_path(value: str) -> str | None:
    value = value.strip().split("#", 1)[0]
    marker = "tests/"
    if marker not in value or not value.endswith(".py"):
        return None
    return value[value.rfind(marker):]


def audit(map_path: Path, audit_path: Path, crosswalk_path: Path) -> dict:
    cap_map = json.loads(map_path.read_text(encoding="utf-8"))
    crosswalk = json.loads(crosswalk_path.read_text(encoding="utf-8"))
    audit_text = audit_path.read_text(encoding="utf-8")

    mentions = set()
    for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", audit_text):
        path = _canonical_test_path(target.strip("<>"))
        if path:
            mentions.add(path)
    for code in re.findall(r"`([^`]+)`", audit_text):
        path = _canonical_test_path(code)
        if path:
            mentions.add(path)

    crosswalk_hashes = {}
    for row in crosswalk.get("rows", []):
        for test in row.get("tests", []):
            path = test.get("path")
            if path:
                crosswalk_hashes[(row.get("id"), path)] = test.get("source_sha256")

    links = []
    for capability in cap_map.get("capabilities", []):
        for raw_ref in capability.get("test_refs", []):
            path = _canonical_test_path(raw_ref)
            if path is None:
                links.append({"capability_id": capability.get("id"),
                              "raw_ref": raw_ref, "status": "unparseable_test_ref"})
                continue
            actual = sha256(ROOT / path)
            expected = crosswalk_hashes.get((capability.get("id"), path))
            links.append({
                "capability_id": capability.get("id"),
                "path": path,
                "audit_document_mentions_path": path in mentions,
                "current_sha256": actual,
                "crosswalk_sha256": expected,
                "crosswalk_hash_matches_current": bool(actual and expected and actual == expected),
            })

    missing_mentions = [row for row in links if row.get("path") and not row["audit_document_mentions_path"]]
    stale_hashes = [row for row in links if row.get("path") and not row["crosswalk_hash_matches_current"]]
    return {
        "schema_version": 1,
        "audit_kind": "capability_test_path_adjudication_reconciliation",
        "scope_note": "Path presence and linked Python-test hash freshness only; not semantic coverage or capability validation.",
        "inputs": {
            "capability_map": {"path": map_path.relative_to(ROOT).as_posix(), "sha256": sha256(map_path)},
            "source_path_audit": {"path": audit_path.relative_to(ROOT).as_posix(), "sha256": sha256(audit_path)},
            "ast_crosswalk": {"path": crosswalk_path.relative_to(ROOT).as_posix(), "sha256": sha256(crosswalk_path)},
        },
        "runner": {"path": Path(__file__).resolve().relative_to(ROOT).as_posix(),
                   "sha256": sha256(Path(__file__).resolve())},
        "summary": {
            "capability_rows": len(cap_map.get("capabilities", [])),
            "linked_test_entries": len(links),
            "unique_linked_test_paths": len({row["path"] for row in links if row.get("path")}),
            "entries_mentioned_in_audit": sum(bool(row.get("audit_document_mentions_path")) for row in links),
            "entries_with_current_crosswalk_hash": sum(bool(row.get("crosswalk_hash_matches_current")) for row in links),
            "missing_audit_mentions": len(missing_mentions),
            "stale_or_missing_crosswalk_hashes": len(stale_hashes),
        },
        "missing_audit_mentions": missing_mentions,
        "stale_or_missing_crosswalk_hashes": stale_hashes,
        "links": links,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", default=DEFAULT_MAP)
    parser.add_argument("--audit", default=DEFAULT_AUDIT)
    parser.add_argument("--crosswalk", default=DEFAULT_CROSSWALK)
    parser.add_argument("--output", help="write the full JSON report to this path")
    args = parser.parse_args()
    report = audit(ROOT / args.map, ROOT / args.audit, ROOT / args.crosswalk)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        target = ROOT / args.output
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
        print(f"wrote {target.relative_to(ROOT)}")
    print(json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
