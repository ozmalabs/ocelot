"""
extract_snippets — pull candidate forecast-relevant sentences out of the REAL
Track 2 corpus docs so the study set is grounded in real bytes, not paraphrase.

This is a MECHANICAL extraction aid used ONCE to assemble the study set for the
Phase 3 de-risk. It scans a curated list of (unit, file) docs, splits into
sentences, and surfaces sentences that mention monetary-policy / macro guidance
terms. A human then picks the load-bearing sentence(s) per doc and hand-labels
direction. It is NOT part of the typer under test.

Run:  python extract_snippets.py  (prints candidates for each curated doc)
"""
from __future__ import annotations

import os
import re

CORPUS = "/home/matt/ozmadev/ocelot/.bigtmp/track2/units"

# Curated docs to sample from (unit, filename). Chosen to span F1-F4, doc types,
# and the hard cases (action-verb-vs-guidance divergence, backstop language with
# no directional cue, data-release surprises).
CURATED = [
    ("t2-F1-hawkish-cut-2024", "fomc_statement_20241218.txt"),
    ("t2-F1-hawkish-cut-2024", "cpi_2024-12-11.txt"),
    ("t2-F1-liftoff-telegraph-2015", "fomc_statement_20151028.txt"),
    ("t2-F1-patient-dropped-2015", "fomc_statement_20150128.txt"),
    ("t2-F1-patient-dropped-2015", "fomc_statement_20150318.txt"),
    ("t2-F1-third-cut-2019", "fomc_statement_20191030.txt"),
    ("t2-F1-pause-2006", "fomc_statement_20060629.txt"),
    ("t2-F1-measured-pace-2004", "fomc_statement_20040630.txt"),
    ("t2-F1-considerable-period-2003", "fomc_statement_20030812.txt"),
    ("t2-F1-conundrum-2005", "fomc_statement_20050322.txt"),
    ("t2-F1-greater-confidence-2024", "fomc_statement_20240918.txt"),
    ("t2-F2-taper-begins-2013", "fomc_statement_20131218.txt"),
    ("t2-F2-taper-testimony-2013", None),
    ("t2-F2-higher-for-longer-2023", "fomc_statement_20230920.txt"),
    ("t2-F2-whatever-it-takes-2012", "draghi_whatever_it_takes_2012.txt"),
    ("t2-F2-eur-parity-2022", "ecb_lagarde_2022-06-20.txt"),
    ("t2-F2-powell-pivot-2019", None),
    ("t2-F2-cut-sizing-2024", None),
    ("t2-F2-abenomics-2012", None),
    ("t2-F2-draghi-precommit-2014", None),
    ("t2-F2-some-pain-2022", None),
    ("t2-F2-time-has-come-2024", None),
    ("t2-F4-powell-december-2018", "fomc_statement_20181108.txt"),
    ("t2-F4-svb-whiplash-2023", "fomc_statement_20230201.txt"),
    ("t2-F4-taper-warning-2013", None),
    ("t2-F4-cpi-friday-2022", None),
    ("t2-F4-covid-rates-2020", None),
    ("t2-F4-jpy-carry-2007", "fomc_statement_20070628.txt"),
    ("t2-F4-ust-downgrade-watch-2011", None),
    ("t2-F4-hike-cycle-2021Q4b", None),
]

GUIDANCE_TERMS = [
    "target range", "federal funds rate", "raise", "lower", "cut", "hike",
    "increase", "decrease", "accommodat", "restrictive", "tighten", "eas",
    "taper", "asset purchase", "patient", "measured", "considerable",
    "gradual", "pace", "inflation", "whatever it takes", "appropriate",
    "confidence", "downside", "upside", "maintain", "unchanged", "basis point",
    "percentage point", "policy rate", "normalis", "normaliz", "pivot",
    "liftoff", "balance sheet", "reduce", "reducing",
]


def sentences(text: str) -> list[str]:
    # collapse whitespace, split on sentence-ish boundaries
    t = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(])", t)
    return [p.strip() for p in parts if len(p.strip()) > 25]


def score_sentence(s: str) -> int:
    low = s.lower()
    return sum(1 for term in GUIDANCE_TERMS if term in low)


def main():
    for unit, fname in CURATED:
        tdir = os.path.join(CORPUS, unit, "text")
        if fname is None:
            files = sorted(f for f in os.listdir(tdir) if f.endswith(".txt"))
            # prefer an fomc_statement or a speech
            pick = next((f for f in files if "statement" in f), None) or \
                   next((f for f in files if f.endswith(".txt")), None)
            fname = pick
        path = os.path.join(tdir, fname) if fname else None
        print("=" * 90)
        print(f"UNIT {unit}  FILE {fname}")
        if not path or not os.path.exists(path):
            print("  (file not found — listing dir)")
            if os.path.isdir(tdir):
                print("   ", sorted(os.listdir(tdir)))
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        cands = sorted(sentences(text), key=score_sentence, reverse=True)
        for s in cands[:4]:
            sc = score_sentence(s)
            if sc == 0:
                break
            print(f"  [{sc}] {s[:280]}")


if __name__ == "__main__":
    main()
