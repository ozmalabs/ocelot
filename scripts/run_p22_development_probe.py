#!/usr/bin/env python3
"""Run a non-actionable P22 training proposal probe on v2 validation worlds."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.process_mastery.p22_development import run_p22_training_proposal_probe


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family", choices=("d4", "loopover"), required=True)
    parser.add_argument("--training-draws", type=int, nargs=2, required=True)
    parser.add_argument("--training-goal-relation", choices=("same", "distinct"),
                        default="same")
    parser.add_argument("--validation-start", type=int, required=True)
    parser.add_argument("--validation-count", type=int, default=200,
        help="number of nonactionable validation worlds; use 0 for training-only binding reconstruction")
    parser.add_argument("--per-request-attempt-ceiling", type=int, default=5000,
        help="per-request training-search ceiling; global ceiling remains 30000")
    parser.add_argument("--search-ticks", type=int, default=30)
    parser.add_argument("--measure-native-rule-work", action="store_true",
        help="enable isolated per-rule native work counters; development only")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.validation_count < 0 or args.validation_start < 0 \
            or args.validation_start + args.validation_count > 1000:
        parser.error("validation draw range must be a nonempty slice of [0, 1000)")
    result = run_p22_training_proposal_probe(
        family=args.family,
        training_draws=tuple(args.training_draws),
        training_goal_relation=args.training_goal_relation,
        validation_draws=tuple(range(args.validation_start,
                                     args.validation_start + args.validation_count)),
        per_request_attempt_ceiling=args.per_request_attempt_ceiling,
        search_ticks=args.search_ticks,
        measure_native_rule_work=args.measure_native_rule_work)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        sys.stdout.write(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
