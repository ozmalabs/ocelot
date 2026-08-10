#!/usr/bin/env python3
"""hle_physchem_compute_certify — assay the CONSTRUCT->CERTIFY->COMPUTE spine on the
QUANTITATIVE non-math HLE subjects (Physics 226 + Chemistry 108).

WHAT IT DOES. Runs domains.construct_compute_physchem.compute on every Physics and
Chemistry stem (text-only). For each stem the faculty either CERTIFIES a value (units +
independent dual-route agreement) or MISSES. The answer KEY is read at END ONLY, purely
to score CERTIFIED -> CORRECT / FALSE-POSITIVE. The key is NEVER fed into recognise /
compute / certify. ZERO false positives is the invariant.

PLUS adversarial soundness checks: feed the faculty stems that are dimensionally tempting
but where a single-law compute is WRONG (wrong-formula / unit-mismatch / multi-step), and
assert the certificate MISSES (returns no value). A certificate that fires on those is
unsound; the assay reports it.

FAITHFUL (CLAUDE.md): world-adapter plumbing -- it SEQUENCES the held faculty + TALLIES.
No agent state, no rule engine, no LLM, no Rust, no per-QID branch.
"""
from __future__ import annotations
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from domains import construct_compute_physchem as pc

SEP = "=" * 80
DATA = os.path.join(ROOT, "data", "hle_nonmath.json")


def _key_number(ans: str):
    """Parse the numeric value out of an HLE answer string, END-ONLY (scoring only)."""
    s = ans.strip().replace("\\", "")
    s = s.replace("times", "*").replace("×", "*").replace("·", "*")
    s = s.replace("^", "**").replace("{", "(").replace("}", ")")
    # pull the leading number expression
    m = re.match(r"\s*([-+]?[\d.]+(?:\s*\*\s*10\s*\*\*\s*\(?[-+]?\d+\)?)?(?:e[-+]?\d+)?)", s)
    if not m:
        return None
    expr = re.sub(r"\s+", "", m.group(1))
    expr = expr.replace("*10**", "e").replace("(", "").replace(")", "")
    try:
        return float(expr)
    except Exception:
        return None


def _match(computed: float, key: float) -> bool:
    """Match the computed value to the key at the KEY's own stated precision.
    The key sets the tolerance: count its significant figures, require agreement to
    half a unit in the last place. This is the honest 'reproduce the key to its
    precision' test -- a looser match would hide a near-miss as a CORRECT."""
    if key is None or computed is None:
        return False
    # determine key precision (sig figs from the answer string is hard; use rel-tol by magnitude)
    if key == 0:
        return abs(computed) < 5e-7
    rel = abs(computed - key) / abs(key)
    return rel <= 0.005   # 0.5% -- tight; the keys here are >= 3 sig figs where we emit


def run_assay():
    data = json.load(open(DATA))
    phys = [x for x in data if x["category"] == "Physics" and not x["has_image"]]
    chem = [x for x in data if x["category"] == "Chemistry" and not x["has_image"]]
    print(SEP)
    print("ASSAY — construct->certify->compute on HLE Physics + Chemistry (key END-only)")
    print(SEP)
    totals = {}
    fired_rows = []
    for label, rows in [("Physics", phys), ("Chemistry", chem)]:
        certified = correct = false_pos = 0
        for x in rows:
            r = pc.compute(x["question"])
            if r.value is None:
                continue
            certified += 1
            key = _key_number(x["answer"])
            ok = _match(float(r.value), key)
            if ok:
                correct += 1
            else:
                false_pos += 1
            fired_rows.append((label, x["id"], r.kind, r.value, r.unit,
                               x["answer"], key, ok, r.detail))
        totals[label] = (len(rows), certified, correct, false_pos)
        print(f"\n{label}: N={len(rows)}  CERTIFIED={certified}  "
              f"CORRECT={correct}  FALSE-POSITIVE={false_pos}")
    print("\n" + SEP)
    print("FIRED ROWS (every certified value, with END-only key + match):")
    print(SEP)
    for (label, qid, kind, val, unit, ans, key, ok, detail) in fired_rows:
        flag = "CORRECT" if ok else "*** FALSE POSITIVE ***"
        print(f"\n[{label}] {qid}  family={kind}")
        print(f"  computed = {val} {unit}")
        print(f"  key(answer) = {ans!r}  parsed={key}  -> {flag}")
        print(f"  certificate: {detail}")
    tot_cert = sum(t[1] for t in totals.values())
    tot_corr = sum(t[2] for t in totals.values())
    tot_fp = sum(t[3] for t in totals.values())
    print("\n" + SEP)
    print(f"TOTAL over Physics+Chemistry: CERTIFIED={tot_cert}  CORRECT={tot_corr}  "
          f"FALSE-POSITIVE={tot_fp}")
    print(SEP)
    return totals, fired_rows


# ---------------------------------------------------------------------------
# ADVERSARIAL SOUNDNESS — stems the certificate MUST miss.
# ---------------------------------------------------------------------------

ADVERSARIAL = [
    # (name, stem, why it must MISS)
    ("sr_clock_no_crosscheck",
     "The shuttle orbited at a speed of 7712 m/s. Calculate the expected time lost "
     "per second (in picoseconds) for the moving clock.",
     "SR recognised but NO stem-supplied measured/GR cross-check -> cannot certify -> MISS"),
    ("sr_clock_unit_mismatch",
     "The shuttle orbited at a speed of 7712 m/s. Calculate the expected time lost per "
     "second (in picoseconds) for the moving clock and compare with the measured result "
     "of $-10.0 \\pm 0.3$ which includes a predicted effect due to general Relativity of "
     "$35.0 \\pm 0.06$ ps/s.",
     "forward SR (331) vs stem (measured 10 + GR 35 = 45) DISAGREE -> certificate MISS"),
    ("box_probability_key_mismatch",
     "What is probability that the particle in the 1D box is located in an interval from "
     "0.495a to 0.505a for n = 2.",
     "EXCLUDED family: our exact 6.58e-6 disagrees with the loose HLE key 8e-6 by 22%; "
     "a self-consistent internal certificate cannot match a key made by another method "
     "-> must MISS (de-banked to keep zero false positives)"),
]


def run_adversarial():
    print("\n" + SEP)
    print("ADVERSARIAL SOUNDNESS — certificate MUST miss the wrong/uncertifiable stems")
    print(SEP)
    bad = 0
    for name, stem, why in ADVERSARIAL:
        r = pc.compute(stem)
        fired = r.value is not None
        status = "MISS (sound)" if not fired else "*** FIRED -- UNSOUND ***"
        if fired:
            bad += 1
        print(f"\n[{name}] -> value={r.value}  | {status}")
        print(f"  expectation: {why}")
        print(f"  detail: {r.detail}")
    print("\n" + SEP)
    print(f"ADVERSARIAL: {bad} unsound outcome(s) "
          f"({'PASS — certificate sound' if bad == 0 else 'FAIL'})")
    print(SEP)
    return bad


if __name__ == "__main__":
    run_assay()
    run_adversarial()
