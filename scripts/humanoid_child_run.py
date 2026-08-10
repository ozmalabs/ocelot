#!/usr/bin/env python3
"""Detached daemon child for graph-directed humanoid development.

The parent graph decides whether to mint the ``Experiment``.  This process is
only the mechanical world boundary: run the declared protocol, persist the
graph-minted motor library, and publish closed-receipt progress for the daemon
to copy back into the parent graph.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from scripts.jabberwock_humanoid_walk import run_experiment  # noqa: E402


DEFAULT_PROTOCOL = ROOT / "protocols" / "humanoid_developmental_curriculum_v1.json"
DEFAULT_MOTOR_LIBRARY = ROOT / "results" / "humanoid_classifier_motor_library.json"


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _configured_path(delta: dict[str, Any], key: str, default: Path) -> Path:
    experiment = delta.get("experiment_attrs") or {}
    raw = experiment.get(key)
    if not isinstance(raw, str) or not raw:
        return default
    candidate = Path(raw)
    return candidate if candidate.is_absolute() else ROOT / candidate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--delta", type=Path, required=True)
    parser.add_argument("--game", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    delta = json.loads(args.delta.read_text(encoding="utf-8"))
    protocol_path = _configured_path(delta, "protocol_path", DEFAULT_PROTOCOL)
    motor_library_path = _configured_path(
        delta, "motor_library_path", DEFAULT_MOTOR_LIBRARY
    )
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    action_count = int(protocol["locomotion"]["actions"])
    progress_path = args.out / "progress.json"
    trace_path = args.out / "trace.jsonl"
    started_ns = time.time_ns()
    closed_receipts = 0

    def observe(_world, event: dict[str, Any]) -> None:
        nonlocal closed_receipts
        phase = str(event.get("phase") or "unknown")
        development = dict(event.get("development") or {})
        if phase == "learning_receipt":
            closed_receipts += 1
        report = {
            "status": "running",
            "game": args.game,
            "phase": phase,
            "action": int(event.get("action") or 0),
            "action_count": int(event.get("action_count") or action_count),
            "closed_receipts": closed_receipts,
            "elapsed_ms": (time.time_ns() - started_ns) // 1_000_000,
            "decision_kind": str(event.get("decision_kind") or ""),
            **development,
        }
        _atomic_json(progress_path, report)
        if phase == "learning_receipt":
            with trace_path.open("a", encoding="utf-8") as trace:
                trace.write(json.dumps({
                    "frame": report["action"],
                    "action": report.get("selected_learning_step", ""),
                    "score": report.get("mastery_count", 0),
                    "reasoning": report.get("active_capability", ""),
                    "self_report": report.get("goal", ""),
                }) + "\n")

    _atomic_json(progress_path, {
        "status": "starting",
        "game": args.game,
        "phase": "boot",
        "action": 0,
        "action_count": action_count,
        "closed_receipts": 0,
        "elapsed_ms": 0,
    })

    try:
        report = run_experiment(
            protocol_path,
            motor_library_path=motor_library_path,
            observer=observe,
        )
        _atomic_json(args.out / "humanoid_result.json", report)
        walking = report["walking"]
        final = {
            "status": "done",
            "frames": len(walking.get("trace") or ()),
            "score": walking.get("directed_progress_graph_assessment", 0),
            "developmental_stage_ordinal": int(
                (walking.get("curriculum") or {}).get("stage_ordinal", 0)
            ),
            "developmental_mastery_count": int(
                (walking.get("curriculum") or {}).get("mastery_count", 0)
            ),
            "retained_experience_count": int(
                (walking.get("curriculum") or {}).get(
                    "retained_experience_count", 0
                )
            ),
            "motor_library_path": str(motor_library_path),
        }
        _atomic_json(args.out / "result.json", final)
        _atomic_json(progress_path, {
            **final,
            "game": args.game,
            "phase": "complete",
            "action": final["frames"],
            "action_count": action_count,
            "closed_receipts": closed_receipts,
            "elapsed_ms": (time.time_ns() - started_ns) // 1_000_000,
        })
        return 0
    except Exception as error:  # noqa: BLE001 - child must report failure to parent
        failure = {
            "status": "failed",
            "frames": closed_receipts,
            "score": 0,
            "error": f"{type(error).__name__}: {error}",
        }
        _atomic_json(args.out / "result.json", failure)
        _atomic_json(progress_path, {
            **failure,
            "game": args.game,
            "phase": "failed",
            "action": closed_receipts,
            "action_count": action_count,
            "closed_receipts": closed_receipts,
            "elapsed_ms": (time.time_ns() - started_ns) // 1_000_000,
        })
        raise


if __name__ == "__main__":
    raise SystemExit(main())
