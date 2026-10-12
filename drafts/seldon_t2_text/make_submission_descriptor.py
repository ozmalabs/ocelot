"""
make_submission_descriptor — PHASE 5: build + seal a valid submission.json.

Produces the C5 canonical descriptor for the Track 2 (forecasting) Development
submission, validated against the REAL 12-key schema and sealed with the REAL
toolkit (qfbench2_common.contracts.descriptor.seal_descriptor_digest) — so the
descriptor item on the readiness checklist is PROVEN valid locally, not merely
specified. Everything traceable is filled from the environment; the two fields
that are genuinely unknowable locally (the final image digest, the team id) are
left as clearly-marked placeholders with the exact remaining action.

Category reasoning (SUBMISSION-DESCRIPTOR.md, this track's callout):
  Our shipped default arm is a DETERMINISTIC, network-free forecaster (rules-only
  text + numeric draws). No enum value is perfectly truthful for "calls no model",
  and the track fixture itself uses `byo-small` + access:"local" for that case and
  says to "start there and say so in your report." We do exactly that. If the
  MODEL_ENDPOINT arm is enabled for the run, category becomes `api` and the model
  entry's access becomes `api` (still no vendor key; the house endpoint via proxy).

Run:
  .bigtmp/t2venv/bin/python drafts/seldon_t2_text/make_submission_descriptor.py \
    --team-id <YOUR_TEAM_ID> --category byo-small \
    --image-digest sha256:<64hex-of-final-image> \
    --out drafts/seldon_t2_text/submission.dev.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from qfbench2_common.contracts.descriptor import (
    seal_descriptor_digest, SubmissionDescriptor,
)

# A syntactically-valid placeholder digest (64 hex) used ONLY so the descriptor
# validates + seals locally. The REAL digest is emitted by `docker build` of the
# final image and MUST be substituted before submission (see readiness checklist).
_PLACEHOLDER_DIGEST = "sha256:" + "0" * 64


def git_rev() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True).strip()[:12]
    except Exception:
        return "unknown-build"


def build(team_id: str, category: str, image_digest: str,
          registry: str, repository: str) -> dict:
    rev = git_rev()
    if category == "api":
        # house-endpoint arm: the model is the organizer's, reached via proxy.
        # version + training_cutoff are NOT published (SUBMISSION-DESCRIPTOR.md):
        # put the most honest values and flag to organizers.
        model = {
            "name": "organizer-house-endpoint",
            "version": "UNPUBLISHED-see-MODEL_NAME",
            "training_cutoff": "UNPUBLISHED-raise-with-organizers",
            "access": "api",
            "revision": rev,
        }
    else:
        # deterministic, network-free default arm (rules-only text + numeric).
        model = {
            "name": "ocelot-seldon-deterministic",
            "version": "t2-ocelot-phase5",
            "training_cutoff": "not-applicable",
            "access": "local",
            "revision": rev,
        }

    desc = {
        "schema_version": "1.0.0",
        "interface_version": "2.0",
        "competition_id": "agenthon2026-forecasting-dev",
        "team_id": team_id,
        "track": "forecasting",
        "phase": "dev",
        "category": category,
        "image": {
            "registry": registry,
            "repository": repository,
            "digest": image_digest,
        },
        "image_access": "public",
        "models": [model],
        "license": "Apache-2.0",
    }
    return desc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--team-id", default="TEAM-ID-PLACEHOLDER",
                    help="your CodaBench team id (cannot be derived locally)")
    ap.add_argument("--category", default="byo-small",
                    choices=["api", "byo-small", "byo-large"])
    ap.add_argument("--image-digest", default=_PLACEHOLDER_DIGEST,
                    help="sha256:<64hex> of the FINAL built image "
                         "(default placeholder — substitute before submit)")
    ap.add_argument("--registry", default="ghcr.io")
    ap.add_argument("--repository", default="your-org/qfb2-t2-ocelot")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    desc = build(args.team_id, args.category, args.image_digest,
                 args.registry, args.repository)

    # validate + seal with the REAL toolkit (schema + parser + JCS digest)
    sealed = seal_descriptor_digest(desc)
    # round-trip through the authoritative parser to prove it is accepted
    SubmissionDescriptor.from_mapping(sealed)

    text = json.dumps(sealed, indent=2)
    print(text)
    placeholders = []
    if args.team_id == "TEAM-ID-PLACEHOLDER":
        placeholders.append("team_id")
    if args.image_digest == _PLACEHOLDER_DIGEST:
        placeholders.append("image.digest")
    if args.category == "api":
        placeholders.append("models[0].version + training_cutoff (unpublished)")
    print("\n# VALIDATED + SEALED by qfbench2_common.contracts "
          "(schema 12-key + parser + JCS digest).")
    if placeholders:
        print(f"# REMAINING placeholders to fill before submit: {placeholders}")
    if args.out:
        Path(args.out).write_text(text)
        print(f"# wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
