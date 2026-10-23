#!/usr/bin/env python3
"""Run a P22 training proposal probe or an explicitly authorized training action."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
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
        help="per-request training-search ceiling")
    parser.add_argument("--global-attempt-ceiling", type=int, default=30000,
        help="cumulative graph-wide search ceiling across restored generations (max 120000)")
    parser.add_argument("--search-ticks", type=int, default=30)
    parser.add_argument("--measure-native-rule-work", action="store_true",
        help="enable isolated per-rule native work counters; development only")
    parser.add_argument("--approved-candidate-binding", type=Path,
        help="structured exact candidate request binding; action requires explicit authorization flags")
    parser.add_argument("--approve-digest",
        help="exact candidate expression digest explicitly approved by the reviewer")
    parser.add_argument("--review-seconds", type=float,
        help="reviewer self-reported time spent reviewing this exact candidate, in seconds")
    parser.add_argument("--execute-approved-adoption", action="store_true",
        help="execute the one candidate-bound guarded simulated adoption")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.validation_count < 0 or args.validation_start < 0 \
            or args.validation_start + args.validation_count > 1000:
        parser.error("validation draw range must be a slice of [0, 1000)")
    approval_flags_used = (args.approved_candidate_binding is not None
        or args.approve_digest is not None or args.review_seconds is not None
        or args.execute_approved_adoption)
    approved_binding = None
    authorization_document_sha256 = None
    if approval_flags_used:
        if (args.approved_candidate_binding is None or args.approve_digest is None
                or args.review_seconds is None or not args.execute_approved_adoption):
            parser.error("candidate adoption requires binding, exact approved digest, reviewer seconds, and --execute-approved-adoption")
        if not math.isfinite(args.review_seconds) or args.review_seconds < 0:
            parser.error("review seconds must be finite and nonnegative")
        if args.validation_count != 0 or args.training_goal_relation != "distinct":
            parser.error("approved candidate adoption is restricted to distinct-goal training-only reconstruction")
        if args.output is None or args.output.exists():
            parser.error("approved candidate adoption requires a new --output path")
        try:
            authorization_document_bytes = args.approved_candidate_binding.read_bytes()
            authorization_document = json.loads(authorization_document_bytes)
        except (OSError, json.JSONDecodeError) as exc:
            parser.error(f"cannot read candidate approval binding: {exc}")
        if (not isinstance(authorization_document, dict)
                or authorization_document.get("schema") != "p22_candidate_approval_request_v1"
                or authorization_document.get("status") != "awaiting_exact_user_approval"
                or authorization_document.get("family") != args.family
                or authorization_document.get("training_draws") != list(args.training_draws)
                or authorization_document.get("training_goal_relation") != "distinct"
                or authorization_document.get("validation_draws") != []
                or not isinstance(authorization_document.get("output_path"), str)
                or not isinstance(authorization_document.get("approval_binding"), dict)):
            parser.error("candidate binding document does not match this training-only request")
        expected_output = (ROOT / authorization_document["output_path"]).resolve()
        if args.output.resolve() != expected_output:
            parser.error("candidate adoption output path must match the bound request output")
        approved_binding = dict(authorization_document["approval_binding"])
        digest = approved_binding.get("expression_digest")
        if (not isinstance(digest, str) or digest != args.approve_digest
                or approved_binding.get("family") != args.family
                or approved_binding.get("status") != "unapproved_candidate"):
            parser.error("approved digest/family does not match the exact candidate binding")
        if "human_review_seconds" in approved_binding:
            parser.error("review seconds must be supplied on the command line, not prefilled in the binding")
        approved_binding["human_review_seconds"] = args.review_seconds
        authorization_document_sha256 = hashlib.sha256(
            authorization_document_bytes).hexdigest()
    elif args.output is not None and args.output.exists():
        parser.error("refusing to overwrite an existing development probe artifact")
    result = run_p22_training_proposal_probe(
        family=args.family,
        training_draws=tuple(args.training_draws),
        training_goal_relation=args.training_goal_relation,
        validation_draws=tuple(range(args.validation_start,
                                     args.validation_start + args.validation_count)),
        per_request_attempt_ceiling=args.per_request_attempt_ceiling,
        global_attempt_ceiling=args.global_attempt_ceiling,
        search_ticks=args.search_ticks,
        measure_native_rule_work=(args.measure_native_rule_work
                                  or approved_binding is not None),
        approved_candidate_binding=approved_binding)
    if approved_binding is not None:
        result["candidate_approval_authorization"] = {
            "expression_digest": args.approve_digest,
            "human_review_seconds": args.review_seconds,
            "human_review_cost_source": "reviewer_self_report",
            "binding_document_sha256": authorization_document_sha256}
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        sys.stdout.write(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
