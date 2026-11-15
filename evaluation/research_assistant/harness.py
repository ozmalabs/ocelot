"""Deterministic validation and descriptive scoring for the research pilot."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any


HERE = Path(__file__).resolve().parent
FIXTURE_PATH = HERE / "fixtures_v1.json"
ARMS = ("source_only", "generic_ledger", "research_helper")
SCORES = (
    "source_claim_accuracy",
    "unsupported_assertions",
    "contradiction_recall",
    "limitation_recall",
    "citation_reopenability",
    "citation_hash_match",
    "completion",
)
OPERATIONS = ("tokens", "latency_ms", "tool_cost")
REQUIRED_COVERAGE = {
    "finite_check_vs_universal_claim",
    "contradiction_to_broad_claim",
    "ocelot_failed_or_missing_control",
    "stale_source_or_unavailable_artifact",
    "inapplicable_frame_field",
    "ge_repository",
    "ocelot_repository",
    "non_ge_example",
}


class EvaluationError(ValueError):
    pass


def load_fixtures(path: Path = FIXTURE_PATH) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def validate_fixtures(fixtures: dict[str, Any], repo_root: Path,
                      ge_root: Path | None = None) -> dict[str, Any]:
    errors: list[str] = []
    if fixtures.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if fixtures.get("status") != "pilot_only_burned_not_held_out":
        errors.append("fixture set must be explicitly marked pilot-only/burned")
    sources = {s.get("source_id"): s for s in fixtures.get("source_snapshots", [])}
    if len(sources) != len(fixtures.get("source_snapshots", [])):
        errors.append("source_id values must be unique")
    for source_id, source in sources.items():
        root = ge_root if source.get("repository") == "ge" else repo_root
        if root is None:
            continue
        path = (root / source["path"]).resolve()
        try:
            path.relative_to(root.resolve())
        except ValueError:
            errors.append(f"{source_id}: source path escapes configured root")
            continue
        if not path.is_file():
            errors.append(f"{source_id}: unavailable source {path}")
            continue
        import hashlib
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != source.get("sha256"):
            errors.append(f"{source_id}: stale hash expected {source.get('sha256')} got {actual}")
    tasks = fixtures.get("tasks", [])
    task_ids = [t.get("task_id") for t in tasks]
    if len(task_ids) != len(set(task_ids)):
        errors.append("task_id values must be unique")
    coverage = set()
    for task in tasks:
        coverage.update(task.get("coverage", []))
        if not task.get("prompt", "").startswith("[SYNTHETIC FIXTURE]"):
            errors.append(f"{task.get('task_id')}: prompt needs synthetic marker")
        if task.get("planted_evidence", {}).get("synthetic") is not True:
            errors.append(f"{task.get('task_id')}: planted evidence must be marked synthetic")
        key = task.get("answer_key", {})
        if not key.get("acceptable") or not key.get("required_points"):
            errors.append(f"{task.get('task_id')}: missing answer key or required points")
        unknown = set(key.get("sources", [])) - set(sources)
        if unknown:
            errors.append(f"{task.get('task_id')}: unknown source ids {sorted(unknown)}")
    absent = REQUIRED_COVERAGE - coverage
    if absent:
        errors.append(f"required coverage missing: {sorted(absent)}")
    return {"valid": not errors, "fixture_set_id": fixtures.get("fixture_set_id"),
            "task_count": len(tasks), "source_count": len(sources), "errors": errors,
            "coverage": sorted(coverage)}


def _validate_score_input(data: dict[str, Any], fixtures: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    task_ids = {t["task_id"] for t in fixtures["tasks"]}
    if data.get("fixture_set_id") != fixtures.get("fixture_set_id"):
        errors.append("fixture_set_id does not match the fixture bundle")
    if not data.get("preregistration_id"):
        errors.append("preregistration_id is required; pilot scoring is not a preregistration")
    if data.get("grading_blinded") is not True:
        errors.append("grading_blinded must be true")
    runs = data.get("runs")
    if not isinstance(runs, list):
        return errors + ["runs must be a list"]
    seen: set[tuple[str, str]] = set()
    for i, run in enumerate(runs):
        label = f"runs[{i}]"
        key = (run.get("task_id"), run.get("arm"))
        if key in seen:
            errors.append(f"{label}: duplicate task/arm row {key}")
        seen.add(key)
        if key[0] not in task_ids:
            errors.append(f"{label}: unknown task_id {key[0]}")
        if key[1] not in ARMS:
            errors.append(f"{label}: arm must be one of {ARMS}")
        if not run.get("grader_id") or not run.get("blind_label"):
            errors.append(f"{label}: grader_id and blind_label are required")
        status = run.get("status")
        if status not in ("completed", "missing", "failed"):
            errors.append(f"{label}: status must be completed, missing or failed")
        for field in OPERATIONS:
            value = run.get(field)
            if value is not None and (not isinstance(value, (int, float)) or value < 0 or not math.isfinite(value)):
                errors.append(f"{label}: {field} must be a finite nonnegative number or null")
        if status == "completed":
            scores = run.get("scores", {})
            for field in SCORES:
                value = scores.get(field)
                if type(value) is not int or value not in (0, 1, 2):
                    errors.append(f"{label}: scores.{field} must be integer 0, 1 or 2")
        elif not run.get("failure_reason"):
            errors.append(f"{label}: missing/failed run needs failure_reason")
    return errors


def summarize(data: dict[str, Any], fixtures: dict[str, Any]) -> dict[str, Any]:
    errors = _validate_score_input(data, fixtures)
    if errors:
        raise EvaluationError("; ".join(errors))
    tasks = fixtures["tasks"]
    expected = len(tasks)
    results = {}
    for arm in ARMS:
        rows = [r for r in data["runs"] if r["arm"] == arm]
        completed = [r for r in rows if r["status"] == "completed"]
        summary: dict[str, Any] = {
            "task_denominator": expected,
            "rows_supplied": len(rows),
            "completed": len(completed),
            "missing_or_failed": expected - len(completed),
            "missing_task_ids": sorted(t["task_id"] for t in tasks
                                        if not any(r["task_id"] == t["task_id"] for r in rows)),
            "failed_or_missing": [{"task_id": r["task_id"], "status": r["status"],
                                   "reason": r.get("failure_reason")} for r in rows if r["status"] != "completed"],
            "mean_scores_0_to_2": {},
            "mean_operations": {},
        }
        for field in SCORES:
            values = [r["scores"][field] for r in completed]
            summary["mean_scores_0_to_2"][field] = mean(values) if values else None
        for field in OPERATIONS:
            values = [r[field] for r in rows if r.get(field) is not None]
            summary["mean_operations"][field] = mean(values) if values else None
        results[arm] = summary
    pair_rows = []
    for task in tasks:
        by_arm = {r["arm"]: r for r in data["runs"] if r["task_id"] == task["task_id"]}
        if all(arm in by_arm and by_arm[arm]["status"] == "completed" for arm in ARMS):
            pair_rows.append(task["task_id"])
    return {
        "report_type": "descriptive_pilot_scoring_only",
        "fixture_set_id": fixtures["fixture_set_id"],
        "preregistration_id": data["preregistration_id"],
        "total_task_count": expected,
        "expected_runs": expected * len(ARMS),
        "supplied_runs": len(data["runs"]),
        "complete_paired_task_count": len(pair_rows),
        "complete_paired_task_ids": pair_rows,
        "arms": results,
        "inference_note": "Descriptive pilot summaries only. No benefit claim, hypothesis test, confidence interval, or confirmatory inference is produced.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="validate fixture structure and pinned sources")
    validate.add_argument("--repo-root", type=Path, default=HERE.parents[1])
    validate.add_argument("--ge-root", type=Path, default=HERE.parents[2] / "graphic-equalisation")
    score = sub.add_parser("score", help="summarize a blinded human score file")
    score.add_argument("score_file", type=Path)
    score.add_argument("--out", type=Path)
    options = parser.parse_args(argv)
    fixtures = load_fixtures()
    if options.command == "validate":
        result = validate_fixtures(fixtures, options.repo_root, options.ge_root)
    else:
        with options.score_file.open(encoding="utf-8") as f:
            data = json.load(f)
        try:
            result = summarize(data, fixtures)
        except EvaluationError as exc:
            parser.error(str(exc))
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if options.command == "validate" and not result["valid"]:
        print(rendered, end="")
        return 1
    if options.command == "score" and options.out:
        options.out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
