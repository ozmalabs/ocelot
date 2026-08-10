"""The agent classifies + captures the residue it can't ground — by TEACHING.

Reads the campaign's residue (the ungrounded frontier words) + their prose
context, consults the Claude-teacher to classify a SAMPLE, induces a classifier
from the taught examples, applies it to the whole residue, and captures each word
as its KIND. Prints the structured breakdown the frontier becomes.
"""
from __future__ import annotations

import glob
import json
import re
import sys

from substrate.world_adapter import WorldAdapter
from scripts.claude_teacher import make_ask
from domains import remainder_classification as rc


def _prose():
    out = []
    for f in glob.glob("seeds/*.json"):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        for r in (d.get("rules") or []):
            if isinstance(r, dict):
                out.append(" ".join(str(r.get(k, ""))
                                    for k in ("head", "body", "if", "then", "why")))
    return out


def run():
    rep = json.load(open("var/encyclopedic_campaign_report.json"))
    residue = rep["frontier_sample"]          # the ungrounded words (sample)
    text = " ".join(_prose())

    def context_of(word):
        m = re.search(r".{0,70}\b" + re.escape(word) + r"\b.{0,70}", text, re.IGNORECASE)
        return m.group(0).strip() if m else word

    wa = WorldAdapter()
    ask = make_ask(timeout=300.0, preamble="")
    print(f"residue: {len(residue)} words; teaching on a sample…", flush=True)
    res = rc.classify_and_capture(wa.s, residue, context_of, ask, sample_size=40)

    print(f"\ntaught {res['n_taught']} examples; learned {len(res['learned'])} kinds", flush=True)
    print("\nlearned shape-patterns per kind:")
    for kind, pat in res["learned"].items():
        fixed = {k: v for k, v in pat.items() if v != rc.WILD}
        print(f"  {kind:16s} {fixed}")
    print("\nthe residue, CLASSIFIED + captured:")
    for kind, n in sorted(res["counts"].items(), key=lambda kv: -kv[1]):
        ex = [wa.s.node(x)["attrs"]["surface"]
              for x in wa.s.nodes(rc._CAPTURE_TYPE[kind])
              if wa.s.node(x)["attrs"].get("kind") == kind][:8]
        print(f"  {n:4d}  {kind:16s} e.g. {ex}")


if __name__ == "__main__":
    run()
    sys.exit(0)
