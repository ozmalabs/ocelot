#!/usr/bin/env python3
"""Post-change engineering verification of rule parse/import atomicity."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PY = ROOT / "runners/dsl/src/py.rs"
SOURCE_SYM = ROOT / "runners/dsl/src/sym.rs"
NATIVE = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"
LOCK = ROOT / "evaluation/substrate_capability/rule_import_atomicity_lock_20260925.json"
OUT = ROOT / "evaluation/reports/substrate_rule_import_atomicity_20260925.json"
REPLICATES = 3
ATTEMPTS = 25
GOOD_RULES = [
    {
        "name": "staged_good_rule",
        "match": [["x", "staged_edge", "y"]],
        "where": {"type": "Eq", "a": {"type": "Lit", "value": 1}, "b": {"type": "Lit", "value": 1}},
        "effects": [],
        "active": True,
    },
    {
        "name": "staged_inactive_rule",
        "match": [["x", "staged_edge2", "y"]],
        "effects": [],
        "active": False,
    },
]
BAD_RULE = {
    "name": "malformed_suffix_rule",
    "area": "atomicity_probe_area",
    "match": [["source_var", "atomicity_probe_edge", "target_var"]],
    "where": {
        "type": "Eq",
        "a": {"type": "Lit", "value": 1},
        "b": {"type": "UnknownAtomicityProbeTerm"},
    },
    "effects": [],
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def locked_inputs() -> dict:
    return {
        "runner_sha256": sha(Path(__file__)),
        "py_binding_source_sha256": sha(SOURCE_PY),
        "interner_source_sha256": sha(SOURCE_SYM),
        "native_sha256": sha(NATIVE),
        "replicates": REPLICATES,
        "attempts_per_case": ATTEMPTS,
        "good_rules": GOOD_RULES,
        "bad_rule": BAD_RULE,
    }


def failure_case(case: str) -> dict:
    sys.path.insert(0, str(ROOT / "runners/dsl/python"))
    from substrate_rs import Substrate

    failures = 0
    clean = 0
    first_post_sym = None
    for attempt in range(ATTEMPTS):
        s = Substrate()
        baseline_sym = s._inner.intern(f"baseline_marker_{case}_{attempt}")
        before_terms = s._inner.term_arena_len()
        before_rules = s._inner.rule_count()
        try:
            if case == "add_rule_parse_failure":
                s._inner.add_rule(BAD_RULE)
            else:
                s._inner.import_rules([*GOOD_RULES[:1], BAD_RULE])
        except ValueError:
            failures += 1
        next_sym = s._inner.intern(f"post_failure_marker_{case}_{attempt}")
        if first_post_sym is None:
            first_post_sym = next_sym
        if (
            s._inner.term_arena_len() == before_terms
            and s._inner.rule_count() == before_rules
            and next_sym == baseline_sym + 1
        ):
            clean += 1
    return {
        "case": case,
        "attempts": ATTEMPTS,
        "expected_failures": failures,
        "fully_rolled_back": clean,
        "first_post_failure_sym_id": first_post_sym,
    }


def success_case() -> dict:
    sys.path.insert(0, str(ROOT / "runners/dsl/python"))
    from substrate_rs import Substrate

    s = Substrate()
    count = s._inner.import_rules(GOOD_RULES)
    rows = s._inner.export_rules()
    return {
        "imported_count": count,
        "rule_count": s._inner.rule_count(),
        "names_in_order": [row.get("name") for row in rows],
        "active_in_order": [row.get("active", True) for row in rows],
    }


def main() -> None:
    if sys.argv[1:] == ["--lock"]:
        print(json.dumps({"locked_inputs": locked_inputs()}, indent=2, sort_keys=True))
        return
    if json.loads(LOCK.read_text()).get("locked_inputs") != locked_inputs():
        raise SystemExit("locked inputs changed")
    failures = [failure_case(name) for name in ("add_rule_parse_failure", "import_rules_late_parse_failure")]
    success = success_case()
    checks = {
        "add_rule_failure_atomic": failures[0]["expected_failures"] == ATTEMPTS and failures[0]["fully_rolled_back"] == ATTEMPTS,
        "import_rules_late_failure_atomic": failures[1]["expected_failures"] == ATTEMPTS and failures[1]["fully_rolled_back"] == ATTEMPTS,
        "successful_import_preserves_order_and_tombstone": success == {
            "imported_count": 2,
            "rule_count": 2,
            "names_in_order": ["staged_good_rule", "staged_inactive_rule"],
            "active_in_order": [True, False],
        },
    }
    report = {
        "schema_version": 1,
        "run_id": "rule-import-atomicity-postfix-20260925",
        "evidence_class": "post-change engineering verification; no performance claim",
        "locked_inputs": locked_inputs(),
        "checks": checks,
        "failure_cases": failures,
        "successful_import_control": success,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks}, indent=2))
    if not all(checks.values()):
        raise SystemExit("rule import atomicity verification failed; report preserved")


if __name__ == "__main__":
    main()
