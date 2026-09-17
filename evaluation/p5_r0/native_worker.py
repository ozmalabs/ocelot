"""Closed worker-side task validation with no evaluator-state access."""
from __future__ import annotations
from typing import Any, Callable
from evaluation.p0a.canonical import canonical_bytes
from .protocol import P5R0Error


def _reject_private_fields(value: Any, path: str = "task") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"truth", "target_action", "secret_seed", "private_domain_family", "split"}:
                raise P5R0Error(f"worker private field: {path}.{key}")
            _reject_private_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_private_fields(child, f"{path}[{index}]")


def validate_task(task: dict[str, Any]) -> dict[str, Any]:
    _reject_private_fields(task)
    schema = task.get("schema")
    if schema == "P5R0WorkerTaskV1":
        required = {"schema", "case_token", "task_nonce", "observation", "legal_actions", "protocol_budget"}
        if set(task) != required: raise P5R0Error("worker frame")
    elif schema == "P5R0WorkerTaskV2":
        required = {"schema", "case_token", "task_nonce", "observation", "legal_actions", "protocol_budget", "step_index", "arm"}
        if set(task) != required or type(task["step_index"]) is not int or task["step_index"] < 0: raise P5R0Error("worker frame")
    elif schema == "P5R0WorkerTaskV3":
        required = {"schema", "case_token", "task_nonce", "observation", "legal_actions", "protocol_budget", "episode_step", "reset_policy", "arm", "persistent_projection", "control"}
        if set(task) != required or type(task["episode_step"]) is not int or task["episode_step"] < 0 or task["reset_policy"] != "fresh_case" or task["arm"] not in {"cold_reset", "frozen_transfer", "warm_adaptive"}: raise P5R0Error("worker frame")
        if task["control"] is not None:
            control = task["control"]
            if not isinstance(control, dict) or set(control) - {"control_id", "training_commitment", "challenge_commitment", "policy"}: raise P5R0Error("worker control metadata")
            if any(key in control for key in {"truth", "target_action", "secret_seed", "private_domain_family", "split"}): raise P5R0Error("worker control privacy")
        projection = task.get("persistent_projection")
        if not isinstance(projection, dict) or projection:
            if not isinstance(projection, dict) or set(projection) != {"adoption_count", "namespace_digest"} or type(projection.get("adoption_count")) is not int or not 0 <= projection["adoption_count"] <= 4 or not isinstance(projection.get("namespace_digest"), str) or not projection["namespace_digest"].startswith("sha256:") or len(projection["namespace_digest"]) != 71:
                raise P5R0Error("worker persistent projection")
    if len(canonical_bytes(task)) > int(task["protocol_budget"].get("frame_bytes", 65536)): raise P5R0Error("worker frame")

    if not isinstance(task["legal_actions"], list) or not task["legal_actions"] or len(set(task["legal_actions"])) != len(task["legal_actions"]): raise P5R0Error("worker legal actions")
    if any(not isinstance(a, str) for a in task["legal_actions"]): raise P5R0Error("worker legal actions")
    return task

def run(task: dict[str, Any], policy: Callable[[dict[str, Any]], int | None] | None = None) -> int | None:
    task = validate_task(task)
    control = task.get("control")
    if isinstance(control, dict) and control.get("control_id") == "illegal_action":
        # This stimulus is locked to fail at the worker boundary.  It must not
        # be converted into a legal action or reach evaluator success.
        raise P5R0Error("locked protocol_error: illegal action")
    if policy is None: return None
    action = policy(task)
    if action is not None and (type(action) is not int or not 0 <= action < len(task["legal_actions"])): raise P5R0Error("worker action")
    return action



def validate_reply_v3(reply: dict[str, Any], task: dict[str, Any], *, allow_invalid: bool = False) -> dict[str, Any]:
    """Validate a V3 reply without substituting an action at the runner seam.

    The locked illegal-action control is the sole path that may carry an
    out-of-range action onward to the evaluator, where it becomes the signed
    ``protocol_error`` outcome.  Ordinary replies remain strictly bounded.
    """
    if task.get("schema") != "P5R0WorkerTaskV3" or set(reply) != {"schema", "action"} or reply.get("schema") != "P5R0WorkerReplyV3": raise P5R0Error("worker reply v3")
    action = reply["action"]
    if action is not None and (type(action) is not int or (not allow_invalid and not 0 <= action < len(task["legal_actions"]))): raise P5R0Error("worker action v3")
    return reply
