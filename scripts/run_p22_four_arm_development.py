#!/usr/bin/env python3
"""Run a training-only P22 four-arm native wiring diagnostic."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.process_mastery.p22_four_arm_development import (
    run_p22_four_arm_development,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--family", choices=("d4", "loopover"), required=True)
    parser.add_argument("--training-draws", type=int, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run_p22_four_arm_development(
        family=args.family, training_draws=tuple(args.training_draws))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "family": result["family"],
        "common_worlds": result["common_worlds"],
        "resources_match": result["resource_comparison"][
            "all_resource_dimensions_match"],
        "solved": {arm: data["solved_count"] for arm, data in result["arms"].items()},
        "proposals": {arm: data["proposal_count"] for arm, data in result["arms"].items()},
        "output": str(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
