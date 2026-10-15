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
    ap.add_argument("report", nargs="?")
    ap.add_argument("candidate", nargs="?")
    ap.add_argument("--by", required=True)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--human-edits", default=None,
                    help="JSON list of edits a human authored directly (not an agent proposal); "
                         "measured here and recorded as human_authored")
    ap.add_argument("--rationale", default="")
    args = ap.parse_args()
    from domains.criterion_proposals import apply_edits, edit_id, labelled_rows, measure
    if args.human_edits:
        base = json.loads(CRITERIA.read_text())
        edits = json.loads(args.human_edits)
        new = apply_edits(base, edits)
        rows = labelled_rows()
        before, after = measure(base, rows, []), measure(new, rows, [])
        major, minor, _patch = (int(x) for x in base["version"].split("."))
        new["version"] = f"{major}.{minor + 1}.0"
        new.setdefault("adopted_proposals", []).append({
            "candidate": edit_id(edits), "edits": edits, "approved_by": args.by, "human_authored": True,
            "rationale": args.rationale, "from_version": base["version"],
            "test_kappa_before": before["test"]["kappa"], "test_kappa_after": after["test"]["kappa"],
            "test_precision0_after": after["test"]["precision0"]})
        print(json.dumps({"from": base["version"], "to": new["version"], "edits": edits,
                          "test_kappa": [before["test"]["kappa"], after["test"]["kappa"]]}))
        if not args.dry:
            CRITERIA.write_text(json.dumps(new, indent=1) + "\n")
        return
    if not (args.report and args.candidate):
        raise SystemExit("give <report> <candidate>, or --human-edits")
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
