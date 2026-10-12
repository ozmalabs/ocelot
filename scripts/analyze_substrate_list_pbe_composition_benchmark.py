#!/usr/bin/env python3
"""Recover full held-out outputs from accepted IRs in the composition benchmark."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "evaluation/reports/substrate_list_pbe_composition_benchmark_amended_20260925.json"
FIXTURE = ROOT / "tests/fixtures/substrate_list_pbe_confirmatory/tasks.json"
OUT = ROOT / "evaluation/reports/substrate_list_pbe_composition_analysis_20260925.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "runners/dsl/python")]
    import prog_synthesis_battery as p4
    from substrate_rs import _native

    report = json.loads(REPORT.read_text(encoding="utf-8"))
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    task_by_id = {t["id"]: t for t in fixture["tasks"]}
    rows = []
    for arm, cases in report["cases"].items():
        for case in cases:
            if case.get("status") != "accepted":
                continue
            ir = case.get("ir")
            if ir is None:
                raise RuntimeError(f"accepted case lacks IR: {arm}/{case['task_id']}")
            task = task_by_id[case["task_id"]]
            detail = []
            for example in task["held_out_rows"]:
                evaluated = p4.prog_eval(ir, dict(example["inputs"]))
                got = evaluated.get("result")
                equal = (evaluated.get("halted") is True and evaluated.get("trap") is None
                         and p4.agree(got, example["expected"]))
                detail.append({"inputs": example["inputs"], "expected": example["expected"],
                               "got": got, "halted": evaluated.get("halted"),
                               "trap": evaluated.get("trap"), "exact_match": bool(equal)})
            rows.append({"arm": arm, "task_id": case["task_id"], "outcome": case["outcome"],
                         "held_out": detail, "all_ok": all(r["exact_match"] for r in detail)})

    extension = Path(_native.__file__).resolve()
    payload = {
        "schema_version": 1,
        "analysis_id": "substrate-list-pbe-composition-analysis-20260925-v1",
        "analysis_scope": "Re-evaluates stored accepted IRs only; no synthesis or outcome-policy change. Restores list-valued outputs omitted by the original row formatter.",
        "accepted_ir_count": len(rows),
        "cases": rows,
        "provenance": {
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "python": sys.version, "platform": platform.platform(),
            "raw_report_sha256": sha(REPORT), "fixture_sha256": sha(FIXTURE),
            "analyzer_sha256": sha(Path(__file__).resolve()),
            "p4_runner_sha256": sha(ROOT / "scripts/prog_synthesis_battery.py"),
            "native_extension_path": str(extension), "native_extension_sha256": sha(extension),
        },
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT), "accepted_ir_count": len(rows),
                      "accepted_holdout_fail": sum(not r["all_ok"] for r in rows)}, indent=2))


if __name__ == "__main__":
    main()
