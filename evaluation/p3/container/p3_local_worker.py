#!/usr/local/bin/python3
"""Minimal fixed worker transport for the finite provisioned P3 image.

The host-side worker client has already verified the evaluator signature, lock,
sequence, nonce, and expiry before this entrypoint is launched.  This process
only accepts the resulting task digest and cannot access any mutable control
plane or host channel under the launcher policy.
"""
import hashlib
import json
import sys

def digest(value):
    # The evaluator/client owns canonical JSON serialization and task signature.
    return "sha256:" + hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def main():
    request = json.load(sys.stdin)
    task = json.load(open("/input/next-task.json", "r", encoding="utf-8"))
    if request.get("schema") != "P3WorkerRequestV1" or request.get("sealed_task_digest") != task.get("task_digest"):
        raise SystemExit(2)
    candidate = open("/agent/candidate.bin", "rb").read()
    candidate_digest = "sha256:" + hashlib.sha256(candidate).hexdigest()
    output = {"schema": "P3WorkerOutputV1", "task_digest": task["task_digest"], "candidate_digest": candidate_digest, "candidate_evidence": {"status": "bounded"}}
    output["worker_output_digest"] = digest(output)
    print(json.dumps(output, separators=(",", ":")))

if __name__ == "__main__":
    main()
