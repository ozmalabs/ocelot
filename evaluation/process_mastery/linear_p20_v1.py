"""P20 development orchestrator for target transfer and social acquisition.

Held-out execution is deliberately unavailable until the complete protocol,
analyzer, allocation and runtime attestation are frozen in the standalone
P20 preregistration. This runner currently exposes only development checks.
"""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
from pathlib import Path

from evaluation.process_mastery.social_sequence_development import (
    run_development_controls, run_development_panel as run_social_panel,
)
from evaluation.process_mastery.explanation_development import (
    run_development_panel as run_explanation_panel,
)
from evaluation.process_mastery.target_learning_curve import (
    run_development_panel as run_target_panel,
)

PHASE = "linear-p20-v1"


def _commit():
    root = Path(__file__).resolve().parents[2]
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root,
                                       text=True).strip()
    except Exception:
        return "unavailable"


def run_development(*, target_streams_per_pair=4, social_streams_per_arm=2,
                    social_controls_per_kind=1, explanation_streams=2):
    """Run all current P20 development panels without a held-out allocation."""
    target = run_target_panel(streams_per_pair=target_streams_per_pair)
    social = run_social_panel(streams_per_arm=social_streams_per_arm)
    controls = run_development_controls(per_kind=social_controls_per_kind)
    explanations = run_explanation_panel(streams=explanation_streams)
    return {
        "phase": PHASE, "split": "development", "status": "development_only",
        "heldout_accessed": False, "development_commit": _commit(),
        "python": platform.python_version(),
        "allocation": {
            "target_streams_per_pair": target_streams_per_pair,
            "target_domain_pairs": target["domain_pairs"],
            "social_streams_per_arm": social_streams_per_arm,
            "social_arms": social["arms"],
            "social_controls_per_kind": social_controls_per_kind,
            "social_control_count": len(controls),
            "explanation_streams": explanation_streams,
        },
        "target_learning": target,
        "social_acquisition": social,
        "explanation_rebuild": explanations,
        "structural_controls": controls,
        "structural_status": "PASS" if all(row["status"] == "PASS"
                                              for row in controls) else "FAIL",
    }


def run(split, **kwargs):
    if split != "development":
        raise RuntimeError("held-out P20 is closed until standalone preregistration freeze")
    return run_development(**kwargs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("development", "heldout"),
                        default="development")
    parser.add_argument("--target-streams-per-pair", type=int, default=4)
    parser.add_argument("--social-streams-per-arm", type=int, default=2)
    parser.add_argument("--social-controls-per-kind", type=int, default=1)
    parser.add_argument("--explanation-streams", type=int, default=2)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.split,
                 target_streams_per_pair=args.target_streams_per_pair,
                 social_streams_per_arm=args.social_streams_per_arm,
                 social_controls_per_kind=args.social_controls_per_kind,
                 explanation_streams=args.explanation_streams)
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded)
    if result["structural_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
