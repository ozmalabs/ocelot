#!/usr/bin/env python3
"""Gate C6 (plan P6): the agent proposes changes to its reply-quality
criterion; does one improve agreement with held-out labels, and is a
proposal that would only raise the loop's own success rejected?

1. The labelled set (evaluation/labels/reply_quality_heldout_v1.csv; agent
   labels, see the P1 results) is split by dialogue: DEV (even) chooses,
   TEST (odd) reports.
2. Loop success is measured on the agent's own recent production replies:
   the post-run retest of the P5c weighed runs (persona, persona50_40_49).
3. domains/criterion_proposals.enumerate_and_measure: every single edit in
   the grammar, then pairs of the best DEV singles.
4. Every candidate with a positive DEV gain or a positive success delta is
   minted as a CriterionProposal on a conversation boot; the frozen rules in
   seeds/criterion_proposals.json decide. Nothing is adopted: that is the
   human's call.

Usage: <this> [--vocabulary] [--given vocab:<klass>/<mode>]
  --vocabulary  include the vocabulary-base edits (seeds/vocabulary_base_en.json)
  --given X     measure every candidate on top of the vocabulary edit X (the
                criterion as it would be once X is adopted)
Writes evaluation/reports/criterion_proposals_c6_v1[_vocab][_given_<X>]_20261010.json.
"""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts"), str(Path(__file__).parent)]

SUCCESS_REPORTS = ("endemic_rsi_daemon_v1_persona_shadow_n120_authored_p5c_weighed_20261010.json",
                   "endemic_rsi_daemon_v1_persona50_40_49_shadow_n120_authored_p5c_weighed_20261010.json")


def success_pairs():
    out = []
    for name in SUCCESS_REPORTS:
        d = json.loads((ROOT / "evaluation/reports" / name).read_text())
        out += [(r["text"], rep) for r, rep in zip(d["rows"], d["retest_post_run_replies"])]
    return out


def main():
    from domains import reply_quality as rq
    from domains import criterion_proposals as CP
    import endemic_rsi_daemon_v1 as E
    vocab = "--vocabulary" in sys.argv
    given = sys.argv[sys.argv.index("--given") + 1] if "--given" in sys.argv else None
    rows = CP.labelled_rows()
    pairs = success_pairs()
    base = rq.criteria()
    if given:
        e = next(x for x in CP.vocabulary_edits() if CP.edit_id([x]) == given)
        base = CP.apply_edits(base, [e])
    base_m, cands = CP.enumerate_and_measure(base, rows, pairs, vocabulary=vocab and not given)
    print("baseline", json.dumps(base_m), "candidates", len(cands), flush=True)
    st = E.boot(False, promote=False)
    a = st.adapter
    minted = [c for c in cands if c["dev_gain"] > 0 or c["success_delta"] > 0]
    nodes = {c["id"]: CP.mint(a, c, base_m, i) for i, c in enumerate(minted)}
    for _ in range(3):
        a.inner.run_rules()
    for c in minted:
        at = a.s.node(nodes[c["id"]])["attrs"]
        c["verdict"], c["status"], c["preferred"] = at.get("verdict"), at.get("status"), at.get("preferred")
    rec = sorted([c for c in minted if c["verdict"] == "recommended"], key=lambda c: (-c["test_gain"], c["size"]))
    gh = [c for c in minted if c["verdict"] == "goodhart_rejected"]
    rep = {"labels": {"n": len(rows), "dev": base_m["dev"]["n"], "test": base_m["test"]["n"],
                      "note": "agent labels (blind sub-agents), not human labels"},
           "success_replies": len(pairs), "criteria_version": base.get("version"), "given": given,
           "baseline": base_m,
           "n_candidates": len(cands), "minted": len(minted),
           "verdicts": {v: sum(1 for c in minted if c["verdict"] == v)
                        for v in ("recommended", "not_recommended", "goodhart_rejected")},
           "preferred": [c for c in rec if c.get("preferred") == 1],
           "recommended": rec, "goodhart_rejected": sorted(gh, key=lambda c: -c["success_delta"])[:10],
           "all_minted": minted}
    suffix = ("_vocab" if vocab else "") + (f"_given_{given.replace(':', '_').replace('/', '_').replace('+', '_')}"
                                             if given else "")
    out = ROOT / f"evaluation/reports/criterion_proposals_c6_v1{suffix}_20261010.json"
    out.write_text(json.dumps(rep, indent=1) + "\n")
    print(json.dumps({k: rep[k] for k in ("labels", "baseline", "n_candidates", "minted", "verdicts")}, indent=1))
    for c in rep["preferred"]:
        print("PREFERRED", c["id"], c["edits"])
    for c in rec:
        print("RECOMMENDED", c["id"], "dev", c["dev_gain"], "test", c["test_gain"], "p0", c["test"]["precision0"],
              "success", c["success_delta"])
    for c in rep["goodhart_rejected"][:5]:
        print("GOODHART", c["id"], "test", c["test_gain"], "success", c["success_delta"])


if __name__ == "__main__":
    main()
