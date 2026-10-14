#!/usr/bin/env python3
"""HUMAN-RUN (plan P6): apply an approved criterion proposal to the
reply-quality criterion.

  apply_criterion_proposal.py <c6 report.json> <candidate id> --by <name> [--dry]

The candidate's edits (domains/criterion_proposals.apply_edits) are applied
to domains/reply_quality_criteria_v1.json, its minor version is bumped, and an
`adopted_proposals` entry records who approved it and what it measured. The
agent never runs this: criterion adoption is human-only (plan I1, P6).
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CRITERIA = ROOT / "domains/reply_quality_criteria_v1.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("report")
    ap.add_argument("candidate")
    ap.add_argument("--by", required=True)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()
    from domains.criterion_proposals import apply_edits
    rep = json.loads(Path(args.report).read_text())
    cand = next((c for c in rep["all_minted"] if c["id"] == args.candidate), None)
    if cand is None:
        raise SystemExit(f"no candidate {args.candidate!r} in the report")
    if cand.get("verdict") != "recommended":
        raise SystemExit(f"{args.candidate!r} was not recommended by the measurement ({cand.get('verdict')})")
    base = json.loads(CRITERIA.read_text())
    if base.get("version") != rep.get("criteria_version"):
        raise SystemExit(f"the report measured criteria {rep.get('criteria_version')}, the file is {base.get('version')}")
    new = apply_edits(base, cand["edits"])
    major, minor, _patch = (int(x) for x in base["version"].split("."))
    new["version"] = f"{major}.{minor + 1}.0"
    new.setdefault("adopted_proposals", []).append({
        "candidate": cand["id"], "edits": cand["edits"], "approved_by": args.by, "from_version": base["version"],
        "dev_gain": cand["dev_gain"], "test_gain": cand["test_gain"],
        "test_precision0": cand["test"]["precision0"], "success_delta": cand["success_delta"]})
    print(json.dumps({"from": base["version"], "to": new["version"], "edits": cand["edits"]}))
    if not args.dry:
        CRITERIA.write_text(json.dumps(new, indent=1) + "\n")


if __name__ == "__main__":
    main()
