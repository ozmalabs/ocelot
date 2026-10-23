#!/usr/bin/env python3
"""Run a P22 training proposal probe or an explicitly authorized training action."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.process_mastery.p22_development import run_p22_training_proposal_probe
from evaluation.process_mastery.checkpoint_world_adapter import (
    CheckpointExpression, CheckpointWorldAdapter,
)


def _claim_approval_output(path: Path, *, approved_digest: str,
                           review_seconds: float,
                           binding_document_sha256: str) -> None:
    """Durably reserve the one-shot output before beginning an adoption attempt."""
    marker = {"schema": "p22_candidate_adoption_attempt_v1",
        "status": "attempt_started", "expression_digest": approved_digest,
        "human_review_seconds": review_seconds,
        "human_review_cost_source": "reviewer_self_report",
        "binding_document_sha256": binding_document_sha256}
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(marker, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _parent_checkpoint_from_binding(document: dict) -> CheckpointExpression | None:
    """Load and verify an optional exact parent checkpoint source from a request."""
    spec = document.get("parent_checkpoint")
    if spec is None:
        return None
    required = {"artifact_path", "artifact_sha256", "record_path",
                "checkpoint_digest"}
    if not isinstance(spec, dict) or set(spec) != required:
        raise ValueError("parent checkpoint binding has an invalid schema")
    artifact_path = spec["artifact_path"]
    if not isinstance(artifact_path, str):
        raise ValueError("parent checkpoint artifact path must be a string")
    path = (ROOT / artifact_path).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError("parent checkpoint artifact must be inside the repository") from exc
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != spec["artifact_sha256"]:
        raise ValueError("parent checkpoint artifact hash differs from the approval binding")
    source = json.loads(raw)
    record_path = spec["record_path"]
    if (not isinstance(record_path, list) or not record_path
            or any(not isinstance(key, str) for key in record_path)):
        raise ValueError("parent checkpoint record path must be a nonempty string list")
    record = source
    for key in record_path:
        if not isinstance(record, dict) or key not in record:
            raise ValueError("parent checkpoint record path is absent from its artifact")
        record = record[key]
    if not isinstance(record, dict):
        raise ValueError("parent checkpoint record must be an object")
    fields = set(CheckpointExpression.__dataclass_fields__)
    if set(record) != fields:
        raise ValueError("parent checkpoint record fields do not match the native schema")
    parent = CheckpointExpression(**(record | {"params": tuple(record["params"])}))
    if (parent.checkpoint_digest != spec["checkpoint_digest"]
            or not CheckpointWorldAdapter._checkpoint_digest_valid(parent)):
        raise ValueError("parent checkpoint digest or immutable snapshot is invalid")
    return parent


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
    parent_checkpoint = None
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
        try:
            parent_checkpoint = _parent_checkpoint_from_binding(authorization_document)
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            parser.error(f"invalid parent checkpoint binding: {exc}")
        if parent_checkpoint is not None:
            if parent_checkpoint.generation < 0:
                parser.error("parent checkpoint generation is invalid")
        for field, actual in (("per_request_attempt_ceiling", args.per_request_attempt_ceiling),
                              ("global_attempt_ceiling", args.global_attempt_ceiling),
                              ("search_ticks", args.search_ticks)):
            if field in authorization_document:
                bound = authorization_document[field]
                if (isinstance(bound, bool) or not isinstance(bound, int)
                        or bound != actual):
                    parser.error(f"{field} differs from the candidate approval request")
        expected_output = (ROOT / authorization_document["output_path"]).resolve()
        if args.output.resolve() != expected_output:
            parser.error("candidate adoption output path must match the bound request output")
        approved_binding = dict(authorization_document["approval_binding"])
        parent_spec = authorization_document.get("parent_checkpoint")
        if parent_checkpoint is not None:
            if (not isinstance(parent_spec, dict)
                    or approved_binding.get("parent_checkpoint_digest")
                       != parent_checkpoint.checkpoint_digest):
                parser.error("candidate binding does not name the exact parent checkpoint")
        elif "parent_checkpoint_digest" in approved_binding:
            parser.error("candidate binding requires an unavailable parent checkpoint")
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
    if approved_binding is not None:
        try:
            _claim_approval_output(args.output,
                approved_digest=args.approve_digest,
                review_seconds=args.review_seconds,
                binding_document_sha256=authorization_document_sha256)
        except FileExistsError:
            parser.error("candidate adoption attempt was already claimed for this request")
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
        approved_candidate_binding=approved_binding,
        parent_checkpoint=parent_checkpoint)
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
