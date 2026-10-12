#!/usr/bin/env python3
"""Paired fresh-worker capture for held-topic natural-language request forms."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_HELD_TOPIC_REQUEST_FORM_PANEL_V1_PREREG_20260928.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_HELD_TOPIC_REQUEST_FORM_PANEL_V1_AMENDMENT_20260928.md"
DRIVER = Path(__file__).resolve()
BASE_RUNNER = ROOT / "scripts/substrate_live_held_topic_evidence_v1_6.py"
LOCK = ROOT / "evaluation/substrate_capability/held_topic_request_form_panel_v1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/held_topic_request_form_panel_v1_20260928.json"
DATA = ROOT / "data"
TASKS = (
    ("Tell me about copper.", "copper", "request_form_panel"),
    ("Please tell me about copper.", "copper", "request_form_panel"),
    ("What can you tell me about copper?", "copper", "request_form_panel"),
    ("Can you tell me about copper?", "copper", "honest_capability"),
    ("What do you know about copper?", "copper", "meta"),
    ("What is copper?", "copper", "table"),
    ("What do you know about unobtainium?", "unobtainium", "meta"),
)
FACTS = {
    "copper": "Copper conducts electricity and heat.",
    "basalt": "Basalt is a fine-grained igneous rock formed when lava cools quickly.",
    "hexagon": "A hexagon has six straight sides and six angles.",
}


def effective_pythonpath() -> str:
    configured = os.environ.get("PYTHONPATH", "")
    prefix = []
    if os.environ.get("SUBSTRATE_NATIVE_PACKAGE"):
        prefix.append(str(Path(os.environ["SUBSTRATE_NATIVE_PACKAGE"]).resolve().parent))
    prefix.extend((str(ROOT), str(ROOT / "runners/dsl/python")))
    if configured.split(os.pathsep)[:len(prefix)] == prefix:
        return configured
    paths = []
    if os.environ.get("SUBSTRATE_NATIVE_PACKAGE"):
        paths.append(str(Path(os.environ["SUBSTRATE_NATIVE_PACKAGE"]).resolve().parent))
    paths.extend((str(ROOT), str(ROOT / "runners/dsl/python")))
    if configured:
        paths.append(configured)
    return os.pathsep.join(paths)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def changed_paths(left, right, prefix="") -> list[str]:
    if isinstance(left, dict) and isinstance(right, dict):
        changes = []
        for key in sorted(set(left) | set(right)):
            child = f"{prefix}.{key}" if prefix else str(key)
            if key not in left or key not in right:
                changes.append(child)
            else:
                changes.extend(changed_paths(left[key], right[key], child))
        return changes
    return [] if left == right else [prefix]


def data_fingerprint() -> dict:
    digest = hashlib.sha256()
    count = total = 0
    for path in sorted(DATA.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT).as_posix().encode()
        digest.update(len(relative).to_bytes(8, "big")); digest.update(relative)
        size = path.stat().st_size
        digest.update(size.to_bytes(8, "big"))
        with path.open("rb") as source:
            while block := source.read(1024 * 1024):
                digest.update(block)
        count += 1; total += size
    return {"path": "data", "files": count, "bytes": total,
            "sha256": digest.hexdigest()}


def inputs() -> dict:
    from scripts import substrate_live_held_topic_evidence_v1_6 as base
    from substrate_rs import _native
    return {
        "protocol_sha256": sha(PROTOCOL), "amendment_sha256": sha(AMENDMENT),
        "driver_sha256": sha(DRIVER),
        "base_runner_sha256": sha(BASE_RUNNER),
        "base_fingerprint": base.fingerprint(),
        "native_extension_sha256": sha(Path(_native.__file__).resolve()),
        "native_build_manifest_sha256": sha(
            ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "python": sys.version, "platform": platform.platform(),
        "cwd": os.getcwd(),
        "environment": {key: os.environ.get(key) for key in (
            "OZMA_NO_LLM", "OZMA_SEED_PERSIST_DISABLED",
            "SUBSTRATE_NATIVE_PACKAGE")},
        "effective_pythonpath": effective_pythonpath(),
    }


def worker(replicate: int) -> dict:
    from scripts import substrate_live_held_topic_evidence_v1_6 as base
    locked = json.loads(LOCK.read_text())
    before = {"inputs": inputs(), "runtime_data": data_fingerprint()}
    if before != {"inputs": locked["inputs"],
                  "runtime_data": locked["runtime_data"]}:
        raise SystemExit("worker inputs differ from preregistered run lock")
    base.TASKS = TASKS
    result = base.worker(replicate)
    after = {"inputs": inputs(), "runtime_data": data_fingerprint()}
    result["request_panel_lock_before"] = before
    result["request_panel_lock_after"] = after
    result["request_panel_changed_input_paths"] = changed_paths(before, after)
    result["request_panel_worker_inputs_stable"] = after == {
        "inputs": locked["inputs"], "runtime_data": locked["runtime_data"]}
    return result


def main() -> None:
    if sys.argv[1:] == ["--lock"]:
        locked = {"inputs": inputs(), "runtime_data": data_fingerprint(),
                  "tasks": TASKS, "facts": FACTS}
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps(locked, indent=2, sort_keys=True) + "\n")
        print(LOCK)
        return
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True, default=str))
        return
    locked = json.loads(LOCK.read_text())
    if (locked.get("inputs") != inputs()
            or locked.get("runtime_data") != data_fingerprint()
            or locked.get("tasks") != [list(task) for task in TASKS]
            or locked.get("facts") != FACTS):
        raise SystemExit("stale lock or changed workload")
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    path = [str(ROOT), str(ROOT / "runners/dsl/python")]
    if env.get("SUBSTRATE_NATIVE_PACKAGE"):
        path.insert(0, str(Path(env["SUBSTRATE_NATIVE_PACKAGE"]).resolve().parent))
    if env.get("PYTHONPATH"):
        path.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(path)
    runs = []
    for replicate in range(2):
        completed = subprocess.run(
            [sys.executable, str(DRIVER), "--worker", str(replicate)],
            cwd=ROOT, env=env, text=True, capture_output=True, check=True)
        runs.append(json.loads(completed.stdout))
    post = {"inputs": inputs(), "runtime_data": data_fingerprint()}
    raw = {"schema_version": 1,
           "run_id": "held-topic-request-form-panel-v1-20260928",
           "locked_inputs": locked, "post_run_inputs": post, "runs": runs,
           "worker_source_stable": all(
               run["request_panel_worker_inputs_stable"] for run in runs),
           "source_post_matches_lock": post == {
               "inputs": locked["inputs"], "runtime_data": locked["runtime_data"]}}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(raw, indent=2, sort_keys=True, default=str) + "\n")
    pids = {run["pid"] for run in runs}
    summaries = []
    for run in runs:
        summaries.append({"pid": run["pid"], "boot_ns": run["boot_ns"],
            "turns": [{"prompt": turn["prompt"], "reply": turn["reply"],
                       "dispatch": (turn["comprehension"] or {}).get("dispatch"),
                       "message": turn["message"],
                       "goal_count": len(turn["goals"]),
                       "held_answer_count": len(turn["held_answers"]),
                       "evidence_count": len(turn["evidence"]),
                       "receipt_count": len(turn["receipts"])}
                      for turn in run["turns"]]})
    print(json.dumps({"raw": str(RAW.relative_to(ROOT)),
                      "fresh_processes": len(pids),
                      "worker_source_stable": raw["worker_source_stable"],
                      "source_post_matches_lock": raw["source_post_matches_lock"],
                      "runs": summaries},
                     indent=2, default=str))
    if len(pids) != 2 or not raw["worker_source_stable"] or not raw["source_post_matches_lock"]:
        raise SystemExit("capture retained, but freshness or source-stability gate failed")


if __name__ == "__main__":
    main()
