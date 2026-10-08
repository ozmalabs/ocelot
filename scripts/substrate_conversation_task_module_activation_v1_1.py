#!/usr/bin/env python3
"""Source-locked per-task domain call-path observation for the five-route panel."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners/dsl/python"))
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_CONVERSATION_TASK_MODULE_ACTIVATION_V1_1_PREREG_20260928.md"
BASE_PATH = ROOT / "scripts/substrate_live_conversation_capability_panel_v1.py"
RUNNER = Path(__file__).resolve()
ANALYZER = ROOT / "scripts/analyze_substrate_conversation_task_module_activation_v1_1.py"
LOCK = ROOT / "evaluation/substrate_capability/conversation_task_module_activation_v1_1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/conversation_task_module_activation_v1_1_20260928.json"
SPEC = importlib.util.spec_from_file_location("conversation_panel_base", BASE_PATH)
BASE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(BASE)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wordnet_inputs() -> dict:
    from domains import wordnet_membership as wm
    found = wm._find_corpus()
    if found is None:
        raise SystemExit("WordNet corpus unavailable; cannot satisfy v1.1 external-input lock")
    source, zipped = found
    digest = wm._source_digest(source, zipped)
    uid = getattr(os, "getuid", lambda: 0)()
    database = Path(tempfile.gettempdir()) / f"ocelot-wordnet-membership-v{wm._SCHEMA}-{uid}" / f"{digest}.sqlite3"
    if not database.is_file():
        raise SystemExit("the preregistered warmed WordNet database is absent")
    try:
        probe = sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)
        metadata = probe.execute("SELECT schema, digest FROM metadata").fetchone()
        probe.close()
    except sqlite3.Error as exc:
        raise SystemExit(f"WordNet cache is unreadable: {exc}") from exc
    if metadata != (wm._SCHEMA, digest):
        raise SystemExit("WordNet cache metadata does not match corpus schema/digest")
    return {
        "corpus_path": str(source.resolve()), "corpus_zipped": bool(zipped),
        "corpus_source_digest": digest, "corpus_file_sha256": sha(source),
        "corpus_bytes": source.stat().st_size,
        "nltk_data_env": os.environ.get("NLTK_DATA"),
        "temp_directory": tempfile.gettempdir(),
        "cache_path": str(database.resolve()), "cache_sha256": sha(database),
        "cache_bytes": database.stat().st_size,
        "cache_metadata": list(metadata),
    }


def input_lock() -> dict:
    return {
        "base_panel_inputs": BASE.inputs(),
        "wordnet_external_inputs": wordnet_inputs(),
        "protocol_sha256": sha(PROTOCOL),
        "runner_sha256": sha(RUNNER),
        "analyzer_sha256": sha(ANALYZER),
        "schedule": [list(row) for row in BASE.SCHEDULE],
    }


def worker(condition: str, replicate: int) -> dict:
    before = input_lock()
    frozen = json.loads(LOCK.read_text())
    if before != frozen:
        raise SystemExit("worker input lock differs from preregistered lock")

    from_frame = None
    active = False
    conversation_root_calls = 0
    domain_functions: Counter[str] = Counter()
    module_calls: Counter[str] = Counter()
    call_edges: Counter[tuple[str, str]] = Counter()
    domain_call_event_count = 0

    def profiler(frame, event, arg):
        nonlocal from_frame, active, conversation_root_calls, domain_call_event_count
        if event == "call" and not active:
            module = frame.f_globals.get("__name__", "")
            if module == "substrate.world_adapter" and frame.f_code.co_name == "converse":
                active = True
                from_frame = frame
                conversation_root_calls += 1
            else:
                return
        if not active:
            return
        if event == "call":
            module = frame.f_globals.get("__name__", "")
            if module.startswith("domains."):
                target = f"{module}:{frame.f_code.co_qualname}"
                domain_functions[target] += 1
                module_calls[module] += 1
                domain_call_event_count += 1
                caller_frame = frame.f_back
                caller_module = caller_frame.f_globals.get("__name__", "") if caller_frame else "<unknown>"
                caller_fn = caller_frame.f_code.co_qualname if caller_frame else "<unknown>"
                caller = f"{caller_module}:{caller_fn}"
                call_edges[(caller, target)] += 1
        elif event == "return" and frame is from_frame:
            active = False
            from_frame = None

    sys.setprofile(profiler)
    try:
        outcome = BASE.worker(condition, replicate)
    finally:
        sys.setprofile(None)
    after = input_lock()
    outcome["module_activation"] = {
        "conversation_extent_count": conversation_root_calls,
        "domain_call_event_count": domain_call_event_count,
        "module_call_counts": dict(sorted(module_calls.items())),
        "function_call_counts": dict(sorted(domain_functions.items())),
        "domain_call_edges": [
            {"caller": caller, "callee": callee, "calls": count}
            for (caller, callee), count in sorted(call_edges.items())],
    }
    outcome["module_activation_inputs_before"] = before
    outcome["module_activation_inputs_after"] = after
    outcome["module_activation_inputs_stable"] = before == after == frozen
    return outcome


def main() -> None:
    args = sys.argv[1:]
    if args == ["--lock"]:
        if LOCK.exists() or RAW.exists():
            raise SystemExit("refusing to overwrite lock or raw output")
        locked = input_lock()
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps(locked, indent=2, sort_keys=True) + "\n")
        print(LOCK)
        return
    if len(args) == 3 and args[0] == "--worker":
        result = worker(args[1], int(args[2]))
        print(json.dumps(result, sort_keys=True, default=str))
        return
    if RAW.exists():
        raise SystemExit("refusing to overwrite raw capture")
    frozen = input_lock()
    if not LOCK.is_file() or json.loads(LOCK.read_text()) != frozen:
        raise SystemExit("missing or stale source lock")
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    runs = []
    errors = []
    for condition, replicate in BASE.SCHEDULE:
        cp = subprocess.run([sys.executable, str(RUNNER), "--worker", condition, str(replicate)],
                            cwd=ROOT, env=env, text=True, capture_output=True)
        if cp.returncode == 0 and cp.stdout.strip():
            runs.append(json.loads(cp.stdout))
        else:
            errors.append({"condition": condition, "replicate": replicate,
                           "returncode": cp.returncode, "stderr": cp.stderr[-4000:]})
        print(f"completed={condition}/{replicate} rc={cp.returncode}", file=sys.stderr, flush=True)
    post = input_lock()
    status = "complete" if post == frozen and not errors and len(runs) == len(BASE.SCHEDULE) else "censored"
    raw = {"schema_version": 1, "run_id": "conversation-task-module-activation-v1_1-20260928",
           "capture_status": status, "started_utc": datetime.now(timezone.utc).isoformat(),
           "locked_inputs": frozen, "post_run_inputs": post, "schedule": BASE.SCHEDULE,
           "errors": errors, "runs": runs}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(raw, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"capture_status": status, "workers": len(runs), "errors": len(errors),
                      "raw": str(RAW.relative_to(ROOT))}, indent=2))
    if status != "complete":
        raise SystemExit("capture was censored; partial data retained")


if __name__ == "__main__":
    main()
