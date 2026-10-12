#!/usr/bin/env python3
"""Engineering verification of successful codec manifest installation."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "runners/dsl/src/codec.rs"
NATIVE = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"
LOCK = ROOT / "evaluation/substrate_capability/codec_manifest_install_lock_20260925.json"
OUT = ROOT / "evaluation/reports/substrate_codec_manifest_install_20260925.json"
REPLICATES = 3
EXPECTED_COUNT = 20
EXPECTED_FIRST = "decode_ue"
EXPECTED_LAST = "encode_loop_complete"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def locked_inputs() -> dict:
    return {
        "runner_sha256": sha(Path(__file__)),
        "codec_source_sha256": sha(SOURCE),
        "native_sha256": sha(NATIVE),
        "replicates": REPLICATES,
        "expected_count": EXPECTED_COUNT,
        "expected_first_rule": EXPECTED_FIRST,
        "expected_last_rule": EXPECTED_LAST,
    }


def one_run() -> dict:
    sys.path.insert(0, str(ROOT / "runners/dsl/python"))
    from substrate_rs import Substrate

    s = Substrate()
    added = s._inner.install_field_grammar_rules()
    rows = s._inner.export_rules()
    names = [row.get("name") for row in rows]
    active = [row.get("active", True) for row in rows]
    return {
        "added": added,
        "rule_count": s._inner.rule_count(),
        "exported_count": len(rows),
        "names": names,
        "all_active": all(active),
    }


def main() -> None:
    if sys.argv[1:] == ["--lock"]:
        print(json.dumps({"locked_inputs": locked_inputs()}, indent=2, sort_keys=True))
        return
    current = locked_inputs()
    if json.loads(LOCK.read_text()).get("locked_inputs") != current:
        raise SystemExit("locked inputs changed")
    runs = [one_run() for _ in range(REPLICATES)]
    checks = {
        "all_replicates_install_20": all(
            r["added"] == EXPECTED_COUNT
            and r["rule_count"] == EXPECTED_COUNT
            and r["exported_count"] == EXPECTED_COUNT
            for r in runs
        ),
        "manifest_order_stable": all(
            r["names"][0] == EXPECTED_FIRST and r["names"][-1] == EXPECTED_LAST
            for r in runs
        ),
        "all_rules_active": all(r["all_active"] for r in runs),
        "replicate_outputs_identical": all(r == runs[0] for r in runs[1:]),
    }
    report = {
        "schema_version": 1,
        "run_id": "codec-manifest-install-postfix-20260925",
        "evidence_class": "post-change engineering verification; successful-path control only",
        "locked_inputs": current,
        "checks": checks,
        "runs": runs,
        "failure_injection": "not available through the embedded-manifest runtime API; all-or-nothing failure behavior is source-reviewed but not dynamically exercised",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks}, indent=2))
    if not all(checks.values()):
        raise SystemExit("codec manifest install check failed; report preserved")


if __name__ == "__main__":
    main()
