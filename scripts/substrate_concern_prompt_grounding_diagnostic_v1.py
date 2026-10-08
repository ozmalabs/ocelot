#!/usr/bin/env python3
"""Source-locked wording diagnostic for the v1.4 concern-task clarification."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners/dsl/python"))
BASE_PATH = ROOT / "scripts/substrate_live_conversation_capability_panel_v1.py"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_CONCERN_PROMPT_GROUNDING_DIAGNOSTIC_V1_PREREG_20260928.md"
RUNNER = Path(__file__).resolve()
LOCK = ROOT / "evaluation/substrate_capability/concern_prompt_grounding_diagnostic_v1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/concern_prompt_grounding_diagnostic_v1_20260928.json"
ARMS = {
    "baseline_two": "Compare where the two letters differ and judge the trial on that region.",
    "pair_paraphrase": "Compare where the pair of letters differs and judge the trial on that region.",
    "explicit_referents": "Compare where letter A and letter B differ and judge the trial on that region.",
}
SCHEDULE = [(arm, rep) for rep in (0, 1) for arm in ARMS]
SPEC = importlib.util.spec_from_file_location("live_conversation_panel", BASE_PATH)
BASE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(BASE)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def input_lock() -> dict:
    return {
        "base_panel_inputs": BASE.inputs(),
        "protocol_sha256": sha(PROTOCOL),
        "runner_sha256": sha(RUNNER),
        "baseline_runner_sha256": sha(BASE_PATH),
        "arms": ARMS,
        "schedule": [list(row) for row in SCHEDULE],
    }


def one_worker(arm: str, replicate: int, frozen: dict) -> dict:
    before = input_lock()
    if before != frozen:
        raise SystemExit("worker input/source lock mismatch before task")
    BASE.TASKS[arm] = (ARMS[arm], "statement")
    result = BASE.worker(arm, replicate)
    after = input_lock()
    result["diagnostic_arm"] = arm
    result["diagnostic_prompt"] = ARMS[arm]
    result["diagnostic_inputs_before"] = before
    result["diagnostic_inputs_after"] = after
    result["diagnostic_inputs_stable"] = before == after == frozen
    return result


def main() -> None:
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or RAW.exists():
            raise SystemExit("refusing to overwrite lock or raw capture")
        frozen = input_lock()
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps(frozen, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        frozen = json.loads(LOCK.read_text())
        result = one_worker(sys.argv[2], int(sys.argv[3]), frozen)
        print(json.dumps(result, sort_keys=True))
        return
    if RAW.exists():
        raise SystemExit("refusing to overwrite raw capture")
    frozen = input_lock()
    if not LOCK.is_file() or json.loads(LOCK.read_text()) != frozen:
        raise SystemExit("missing or stale source/input lock")
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    runs, errors = [], []
    for arm, replicate in SCHEDULE:
        command = [sys.executable, str(RUNNER), "--worker", arm, str(replicate)]
        cp = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True)
        if cp.returncode == 0 and cp.stdout.strip():
            runs.append(json.loads(cp.stdout))
        else:
            errors.append({"arm": arm, "replicate": replicate, "returncode": cp.returncode,
                           "stdout": cp.stdout[-2000:], "stderr": cp.stderr[-4000:]})
        print(f"completed={arm}/{replicate} rc={cp.returncode}", file=sys.stderr, flush=True)
    post = input_lock()
    report = {
        "schema_version": 1,
        "run_id": "substrate-concern-prompt-grounding-diagnostic-v1-20260928",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "locked_inputs": frozen,
        "post_run_inputs": post,
        "schedule": [list(row) for row in SCHEDULE],
        "errors": errors,
        "runs": runs,
        "capture_status": "complete" if len(runs) == len(SCHEDULE) and not errors else "partial",
    }
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"raw": str(RAW.relative_to(ROOT)), "status": report["capture_status"],
                      "workers": len(runs), "errors": len(errors)}, indent=2))
    if report["capture_status"] != "complete":
        raise SystemExit("diagnostic capture incomplete; retain but do not interpret")


if __name__ == "__main__":
    main()
