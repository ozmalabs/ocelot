"""Prepare blind held-out packets and verify/scored sealed run records.

This module deliberately makes no model or network calls. The orchestrator
receives ``prompts`` and submits each row to its assigned arm; ``assignment_key``
must be kept separately until grading is complete.
"""
from __future__ import annotations

import hashlib
import json
import random
from typing import Any, Iterable

from evaluation.research_assistant.harness import ARMS, SCORES, EvaluationError


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def sha256(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def freeze_assignments(tasks: Iterable[dict[str, Any]], *, seed: int,
                       arms: tuple[str, ...] = ARMS) -> dict[str, Any]:
    """Create deterministic opaque run labels; retain returned key privately."""
    tasks = list(tasks)
    ids = [task.get("task_id") for task in tasks]
    if not ids or any(not isinstance(x, str) or not x for x in ids):
        raise EvaluationError("tasks need nonempty task_id values")
    if len(set(ids)) != len(ids):
        raise EvaluationError("task_id values must be unique")
    if len(set(arms)) != len(arms) or not arms:
        raise EvaluationError("arms must be nonempty and unique")
    rng = random.Random(seed)
    rows = []
    for task_id in sorted(ids):
        task_arms = list(arms)
        rng.shuffle(task_arms)
        for arm in task_arms:
            rows.append({"task_id": task_id, "arm": arm})
    rng.shuffle(rows)
    # Stable opaque labels are unique, contain no arm hint, and are randomized
    # by the frozen order. They are the only identity exposed to graders.
    key = []
    for i, row in enumerate(rows, 1):
        key.append({"blind_label": f"B{i:04d}", **row})
    return {"schema_version": 1, "seed": seed, "assignments": key,
            "assignment_sha256": sha256(canonical_json(key))}


def prepare_packets(tasks: Iterable[dict[str, Any]], frozen: dict[str, Any]) -> dict[str, Any]:
    """Split assistant prompts, blinded grader sheets, and private assignment key."""
    task_by_id = {t["task_id"]: t for t in tasks}
    assignments = frozen.get("assignments", [])
    if sha256(canonical_json(assignments)) != frozen.get("assignment_sha256"):
        raise EvaluationError("assignment digest mismatch")
    if not assignments:
        raise EvaluationError("frozen assignments are empty")
    prompts, blind_sheets = [], []
    seen = set()
    for row in assignments:
        label, task_id, arm = row.get("blind_label"), row.get("task_id"), row.get("arm")
        if not label or (task_id, arm) in seen or task_id not in task_by_id:
            raise EvaluationError("assignment contains duplicate/unknown rows")
        seen.add((task_id, arm))
        if arm not in ARMS:
            raise EvaluationError("assignment contains unknown arm")
        task = task_by_id[task_id]
        prompt = task.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise EvaluationError(f"{task_id}: prompt is empty")
        prompts.append({"blind_label": label, "task_id": task_id, "prompt": prompt,
                        "source_access": task.get("source_access", [])})
        blind_sheets.append({"blind_label": label, "answer": None,
                             "output_sha256": None,
                             "scores": {score: None for score in SCORES},
                             "rationales": {score: None for score in SCORES},
                             "tokens": None, "latency_ms": None,
                             "tool_cost": None})
    return {"prompts": prompts,
            "blind_sheets": blind_sheets,
            "private_assignment_key": assignments,
            "assignment_sha256": frozen["assignment_sha256"],
            "prompt_sha256": sha256(canonical_json(prompts))}


def attach_outputs(packets: dict[str, Any], outputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Attach model outputs and measured operations; unknown metrics stay null."""
    known = {row["blind_label"] for row in packets["blind_sheets"]}
    if set(outputs) - known:
        raise EvaluationError("output has unknown blind labels")
    result = json.loads(json.dumps(packets["blind_sheets"]))
    by_label = {row["blind_label"]: row for row in result}
    for label, output in outputs.items():
        answer = output.get("answer")
        if not isinstance(answer, str):
            raise EvaluationError(f"{label}: answer must be text")
        row = by_label[label]
        row["answer"] = answer
        row["output_sha256"] = sha256(answer)
        for metric in ("tokens", "latency_ms", "tool_cost"):
            val = output.get(metric)
            if val is not None and (type(val) not in (int, float) or val < 0):
                raise EvaluationError(f"{label}: {metric} must be nonnegative or null")
            row[metric] = val
    return {"schema_version": 1, "assignment_sha256": packets["assignment_sha256"],
            "blind_sheets": result}


def score_blind_sheets(record: dict[str, Any], key: list[dict[str, Any]], *,
                       grader_id: str) -> dict[str, Any]:
    """Validate human scores while labels are blind, then join arm identities."""
    if not grader_id:
        raise EvaluationError("grader_id is required")
    sheets = record.get("blind_sheets")
    key_by_label = {r["blind_label"]: r for r in key}
    if not isinstance(sheets, list) or len(sheets) != len(key_by_label):
        raise EvaluationError("blind sheet denominator does not match assignment key")
    seen, runs = set(), []
    for sheet in sheets:
        label = sheet.get("blind_label")
        if label not in key_by_label or label in seen:
            raise EvaluationError("unknown or duplicate blind label")
        seen.add(label)
        scores = sheet.get("scores", {})
        if any(type(scores.get(field)) is not int or scores[field] not in (0, 1, 2)
               for field in SCORES):
            raise EvaluationError(f"{label}: every rubric score must be integer 0, 1 or 2")
        if not sheet.get("answer") or sheet.get("output_sha256") != sha256(sheet["answer"]):
            raise EvaluationError(f"{label}: missing answer or output hash mismatch")
        assignment = key_by_label[label]
        runs.append({"task_id": assignment["task_id"], "arm": assignment["arm"],
                     "grader_id": grader_id, "blind_label": label, "status": "completed",
                     "scores": scores, "rationales": sheet.get("rationales", {}),
                     "tokens": sheet.get("tokens"), "latency_ms": sheet.get("latency_ms"),
                     "tool_cost": sheet.get("tool_cost"),
                     "output_sha256": sheet["output_sha256"]})
    return {"runs": runs, "grading_blinded": True,
            "assignment_sha256": record.get("assignment_sha256")}
