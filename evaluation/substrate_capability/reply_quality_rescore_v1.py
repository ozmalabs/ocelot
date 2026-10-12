#!/usr/bin/env python3
"""Rescore a production report's stored retest replies with the CURRENT
ReplyQuality criteria (plan P0). Report-only; writes <report>.quality.json.

Usage: <this> evaluation/reports/endemic_rsi_daemon_v1_..._20261010.json
"""
import collections, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT)]


def main():
    from domains import reply_quality as rq
    src = Path(sys.argv[1])
    d = json.loads(src.read_text())
    turns = [r["text"] for r in d["rows"]]
    after, before = d["retest_post_run_replies"], d["retest_fresh_boot_replies"]
    qa = [rq.assess(t, r) for t, r in zip(turns, after)]
    qb = [rq.assess(t, r) for t, r in zip(turns, before)]
    changed = [i for i, (a, b) in enumerate(zip(after, before)) if a != b]
    rep = {"criteria_version": rq.criteria()["version"], "source": src.name,
           "post_run": rq.summarise([q["score"] for q in qa]),
           "fresh_boot": rq.summarise([q["score"] for q in qb]),
           "changed_turns_n": len(changed),
           "changed_turns_after": rq.summarise([qa[i]["score"] for i in changed]),
           "changed_turns_before": rq.summarise([qb[i]["score"] for i in changed]),
           "drops": sum(1 for x, y in zip(qa, qb) if x["score"] < y["score"]),
           "gains": sum(1 for x, y in zip(qa, qb) if x["score"] > y["score"]),
           "transitions": dict(collections.Counter(f"{qb[i]['reason']} => {qa[i]['reason']}" for i in changed)
                               .most_common()),
           "post_run_by_inbound": {k: rq.summarise([q["score"] for q in qa if q["inbound_class"] == k])
                                   for k in ("greeting", "question", "imperative", "statement")},
           "still_inappropriate_after_change": [{"turn": turns[i], "reply": after[i][:120], "reason": qa[i]["reason"]}
                                                for i in changed if qa[i]["score"] == 0]}
    out = src.with_suffix(".quality.json")
    out.write_text(json.dumps(rep, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({k: v for k, v in rep.items() if k != "still_inappropriate_after_change"}, indent=1,
                     ensure_ascii=False))
    for x in rep["still_inappropriate_after_change"]:
        print("  0:", x["reason"], "|", x["turn"][:60], "=>", x["reply"][:50])


if __name__ == "__main__":
    main()
