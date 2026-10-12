#!/usr/bin/env python3
"""Independent turn-level scoring for the held-topic request-form panel."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/held_topic_request_form_panel_v1_20260928.json"
OUT = ROOT / "evaluation/reports/held_topic_request_form_panel_v1_analysis_20260928.json"
ANSWER = "Copper conducts electricity and heat."
EXPECTED = {
    "Tell me about copper.": "request",
    "Please tell me about copper.": "request",
    "What can you tell me about copper?": "request",
    "Can you tell me about copper?": "request",
    "What do you know about copper?": "held_control",
    "What is copper?": "table_control",
    "What do you know about unobtainium?": "unknown_control",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signature(turn: dict) -> dict:
    comp = turn.get("comprehension") or {}
    dispatch = comp.get("dispatch") or {}
    return {"prompt": turn["prompt"], "reply": turn["reply"],
        "kind": comp.get("kind"), "dispatch_path": dispatch.get("path"),
        "dispatch_strategy": dispatch.get("strategy"),
        "message": turn.get("message"),
        "goals": [goal["attrs"] for goal in turn.get("goals", [])],
        "answer_goal_count": len(turn.get("answer_topic_goal_ids", [])),
        "grounder_calls": len(turn.get("grounder_calls", []))}


def score_turn(turn: dict) -> dict:
    prompt = turn["prompt"]
    role = EXPECTED[prompt]
    inbound = turn["message_id"]
    goals = {goal["id"]: goal["attrs"] for goal in turn.get("goals", [])}
    answer_goal_ids = set(turn.get("answer_topic_goal_ids", []))
    held_ids = {held["id"] for held in turn.get("held_answers", [])}
    held_facts_valid = any(
        held["attrs"].get("topic") == "copper"
        and held["attrs"].get("text") == ANSWER
        and held["attrs"].get("grounding_status") == "supported"
        for held in turn.get("held_answers", []))
    evidence_valid = any(
        evidence["attrs"].get("referent") == "copper"
        and evidence["attrs"].get("status") == "supported"
        and evidence["attrs"].get("kind") == "topic_answer"
        for evidence in turn.get("evidence", []))
    matching_receipts = []
    for receipt in turn.get("receipts", []):
        attrs = receipt.get("attrs", {})
        released = set(receipt.get("released_ids", []))
        if (attrs.get("turn_message_id") == inbound
                and attrs.get("status") == "released"
                and attrs.get("surface") == ANSWER
                and released & (answer_goal_ids | held_ids)):
            matching_receipts.append(receipt)
    exact_retrieval = (turn.get("reply") == ANSWER and held_facts_valid
        and evidence_valid and len(answer_goal_ids) == 1
        and any(goals.get(goal, {}).get("concept") == "copper"
                and goals.get(goal, {}).get("kind") == "answer_topic"
                for goal in answer_goal_ids)
        and len(matching_receipts) == 1)
    if role == "unknown_control":
        goal_valid = any(attrs.get("kind") == "answer_topic"
            and attrs.get("concept") == "unobtainium"
            and attrs.get("outcome") == "unresolved"
            for attrs in goals.values())
        unknown_valid = (goal_valid and not turn.get("held_answers")
            and "copper conducts electricity" not in turn.get("reply", "").lower()
            and "unobtainium" in turn.get("reply", "").lower())
        return {"prompt": prompt, "role": role, "pass": unknown_valid,
            "unresolved_unknown_goal": goal_valid,
            "copper_leak": "copper conducts electricity" in turn.get("reply", "").lower(),
            "reply": turn.get("reply"), "route": turn.get("message", {}).get("comp_dispatch_path")}
    return {"prompt": prompt, "role": role, "pass": exact_retrieval,
        "exact_supported_retrieval": exact_retrieval,
        "reply": turn.get("reply"),
        "route": (turn.get("comprehension") or {}).get("dispatch", {}).get("path"),
        "strategy": (turn.get("comprehension") or {}).get("dispatch", {}).get("strategy"),
        "answer_topic_goal_count": len(answer_goal_ids),
        "matching_turn_receipt_count": len(matching_receipts),
        "graph_holds_expected_fact": held_facts_valid,
        "supported_topic_evidence_present": evidence_valid}


def main() -> None:
    raw = json.loads(RAW.read_text())
    runs = raw["runs"]
    rows = []
    for run in runs:
        by_prompt = {turn["prompt"]: turn for turn in run["turns"]}
        if set(by_prompt) != set(EXPECTED):
            raise SystemExit("worker prompt set differs from preregistration")
        rows.append({"pid": run["pid"],
            "worker_input_stable": run["request_panel_worker_inputs_stable"],
            "changed_input_paths": run["request_panel_changed_input_paths"],
            "turns": [score_turn(by_prompt[prompt]) for prompt in EXPECTED]})
    worker_signatures = [[signature(turn) for turn in run["turns"]]
        for run in runs]
    prompt_rows = []
    for prompt in EXPECTED:
        per_worker = [next(row for row in run["turns"] if row["prompt"] == prompt)
                      for run in rows]
        prompt_rows.append({"prompt": prompt, "role": EXPECTED[prompt],
            "worker_outcomes_agree": len({row["pass"] for row in per_worker}) == 1,
            "pass_count": sum(bool(row["pass"]) for row in per_worker),
            "worker_count": len(per_worker), "outcomes": per_worker})
    checks = {
        "two_distinct_processes": len({run["pid"] for run in runs}) == 2,
        "all_worker_input_locks_stable": all(row["worker_input_stable"] for row in rows),
        "post_run_lock_matches": raw["source_post_matches_lock"],
        "semantic_worker_signatures_repeat": worker_signatures[0] == worker_signatures[1],
        "all_preregistered_prompts_present": all(len(run["turns"]) == len(EXPECTED) for run in rows),
        "unknown_control_passes_both": all(row["pass"] for row in prompt_rows[-1]["outcomes"]),
    }
    result = {"schema_version": 1,
        "run_id": raw["run_id"], "raw_sha256": sha(RAW),
        "analyzer_sha256": sha(Path(__file__)), "checks": checks,
        "all_checks_pass": all(checks.values()),
        "prompt_results": prompt_rows,
        "per_worker": rows,
        "summary": {"request_form_positive_cases": sum(
                row["pass_count"] for row in prompt_rows[:4]),
            "request_form_positive_total": 2 * 4,
            "controls_passed": sum(row["pass_count"] for row in prompt_rows[4:]),
            "controls_total": 2 * 3,
            "claim_boundary": "Two fixed-order fresh processes, seven authored prompts, one held fact, current locked runtime; no natural prevalence or broad language-capability estimate."}}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)),
        "checks": checks, "summary": result["summary"],
        "per_prompt": [{"prompt": row["prompt"], "pass_count": row["pass_count"],
                        "total": row["worker_count"],
                        "routes": [o["route"] for o in row["outcomes"]],
                        "replies": [o["reply"] for o in row["outcomes"]]}
                       for row in prompt_rows]}, indent=2))
    if not result["all_checks_pass"]:
        raise SystemExit("analysis gates failed")


if __name__ == "__main__":
    main()
