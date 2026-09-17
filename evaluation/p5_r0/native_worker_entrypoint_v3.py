#!/usr/bin/env python3
"""Minimal V3 worker entrypoint for the locked native image.

The evaluator remains the only owner of truth and mechanics.  This process
only validates the public frame and returns an opaque action.  The
illegal-action control is deliberately out of range so the runner records a
worker-boundary ``protocol_error`` instead of allowing evaluator success.
"""
from __future__ import annotations
import json
import sys


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def main() -> int:
    raw = sys.stdin.buffer.read()
    frame = json.loads(raw.decode("utf-8"))
    required = {"schema", "case_token", "task_nonce", "observation", "legal_actions", "protocol_budget", "episode_step", "reset_policy", "arm", "persistent_projection", "control"}
    if not raw or canonical(frame) != raw or frame.get("schema") != "P5R0WorkerTaskV3" or set(frame) != required:
        return 2
    if not isinstance(frame["legal_actions"], list) or not frame["legal_actions"]:
        return 2
    control = frame["control"]
    if isinstance(control, dict) and control.get("control_id") == "illegal_action":
        action = len(frame["legal_actions"])
    elif isinstance(control, dict) and control.get("control_id") in {"exact_memorization", "template_memorization"} and control.get("training_commitment") != control.get("challenge_commitment"):
        action = None
    else:
        action = 0
    sys.stdout.buffer.write(canonical({"schema": "P5R0WorkerReplyV3", "action": action}))
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
