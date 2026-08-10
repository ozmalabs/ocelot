#!/usr/bin/env python3
"""hle_conviction_aztec_dominoes — reproduce CONVICTION 4 of the HLE key audit:
question 6724eed8b60e (Mathematics), key 6, certified answer 8.

THE QUESTION. "How many ways can we arrange dominoes to cover an Aztec diamond shape
when the size is 2?"  Official key: 6.

THE CERTIFIED ANSWER: 8, derived two INDEPENDENT ways that must agree exactly:
  · the Aztec-Diamond Theorem (Elkies-Kuperberg-Larsen-Propp, 1992): the number of
    domino tilings of AD(n) is 2^(n(n+1)/2);  n=2 -> 2^3 = 8.
  · an EXHAUSTIVE perfect-matching enumeration of the constructed 12-cell AD(2) region
    (always extend the lexicographically-minimal uncovered cell): 8 tilings.
Both routes are carried by the committed faculty domains.construct_compute_enumerations
.compute_aztec_domino_tilings; the value is emitted ONLY because the two agree.

THE CONVICTION (adversarially rescue-tested here). 6 is not a power of 2, and the
domino-tiling count of EVERY Aztec diamond AD(n) is 2^(n(n+1)/2) -- always a power of 2 --
so 6 cannot be the tiling count of any Aztec diamond under ANY size-indexing convention.
Every rescue reading is tested below and all fail:
  · AD(2) total tilings = 8 (theorem + brute)              != 6
  · up to the D4 symmetry of the diamond                = 3 != 6
  · AD(1) (an off-by-one "size 2" reading)              = 2 != 6
  · plain 2x2 / 2x3 / 3x4 rectangle readings   = 2 / 3 / 11 != 6
  · NO Aztec diamond of any order has 6 tilings (not a power of 2).

The KEY is read at END ONLY, purely to score CERTIFIED -> CONFIRM/CONVICT. It is never
fed into recognise / construct / certify / compute. Zero false accusations is the invariant.

FAITHFUL (CLAUDE.md): a world-adapter shell -- it SEQUENCES the committed faculty and the
rescue-reading enumerations and TALLIES. No per-question compute is hidden here; the
certified value comes from the general faculty. The rescue checks are independent
enumerations whose only job is to prove no reading rescues 6.
"""
from __future__ import annotations
import itertools
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from domains import construct_compute_enumerations as en  # noqa: E402

QID = "6724eed8b60e"
DATA = os.path.join(ROOT, "data", "hle_math.json")
SEP = "=" * 80


def _tile_count(cells) -> int:
    cellset = frozenset(cells)

    def rec(rem):
        if not rem:
            return 1
        c = min(rem)
        a, b = c
        return sum(rec(rem - {c, d}) for d in ((a + 1, b), (a, b + 1)) if d in rem)

    return rec(cellset)


def _aztec_tilings_list(n):
    cells = en._aztec_cells(n)
    cellset = frozenset(cells)

    def rec(rem):
        if not rem:
            yield frozenset()
            return
        c = min(rem)
        a, b = c
        for d in ((a + 1, b), (a, b + 1)):
            if d in rem:
                for rest in rec(rem - {c, d}):
                    yield rest | {frozenset({c, d})}

    return list(rec(cellset))


def _tilings_up_to_d4(n):
    tilings = _aztec_tilings_list(n)

    def apply_sym(g, cell):
        x, y = cell[0] + 0.5, cell[1] + 0.5
        t = [(x, y), (-x, y), (x, -y), (-x, -y),
             (y, x), (-y, x), (y, -x), (-y, -x)][g]
        return (t[0] - 0.5, t[1] - 0.5)

    def key(t):
        return tuple(sorted(tuple(sorted(tuple(c) for c in dom)) for dom in t))

    def transform(g, t):
        return frozenset(frozenset(apply_sym(g, c) for c in dom) for dom in t)

    seen, classes = set(), 0
    for t in tilings:
        canon = min(key(transform(g, t)) for g in range(8))
        if canon not in seen:
            seen.add(canon)
            classes += 1
    return classes


def main():
    print(SEP)
    print("CONVICTION 4 — HLE 6724eed8b60e (Mathematics): Aztec diamond size-2 domino tilings")
    print(SEP)

    # --- the certified answer, from the committed general faculty (NO key) ---
    stem = ("How many ways can we arrange dominoes to cover an Aztec diamond shape "
            "when the size is 2?")
    res = en.compute(stem)
    assert res.value is not None, "faculty must certify the Aztec-diamond family"
    print(f"\nCERTIFIED ANSWER (committed faculty, two independent routes): {res.value}")
    print(f"  {res.detail}")

    # --- adversarial rescue readings — every one must fail to equal 6 ---
    print("\nADVERSARIAL RESCUE READINGS (none may equal the key 6):")
    ad2_total = en._count_domino_tilings(en._aztec_cells(2))
    ad1_total = en._count_domino_tilings(en._aztec_cells(1))
    up_to_sym = _tilings_up_to_d4(2)
    rect = {f"{r}x{c}": _tile_count([(i, j) for i in range(r) for j in range(c)])
            for (r, c) in [(2, 2), (2, 3), (3, 4)]}
    rescues = {
        "AD(2) total tilings": ad2_total,
        "AD(2) up to D4 symmetry": up_to_sym,
        "AD(1) (off-by-one size reading)": ad1_total,
        **{f"plain {k} rectangle": v for k, v in rect.items()},
    }
    for name, val in rescues.items():
        flag = "  <-- equals 6!" if val == 6 else ""
        print(f"  {name:38s} = {val}{flag}")
    # the decisive structural fact:
    powers = {2 ** (n * (n + 1) // 2) for n in range(0, 7)}
    print(f"  domino-tiling counts of AD(0..6)         = {sorted(powers)} "
          f"(always 2^(n(n+1)/2))")
    six_is_power_of_two = (6 & 5) == 0
    print(f"  6 is a power of two?                       {six_is_power_of_two} "
          f"-> 6 is NOT the tiling count of ANY Aztec diamond")
    assert all(v != 6 for v in rescues.values()), "a rescue reading equals 6 — NOT convictable"
    assert not six_is_power_of_two

    # --- read the KEY at END ONLY, to score ---
    key = None
    for q in json.load(open(DATA)):
        if q["id"].startswith(QID):
            key = str(q["answer"]).strip()
            break
    print(f"\nKEY (read END-only, scoring): {key!r}")
    verdict = "CONVICT" if key is not None and key != str(res.value) else "CONFIRM"
    print(f"VERDICT: {verdict}  (certified {res.value} vs key {key}; every rescue reading != 6)")
    print(SEP)
    assert verdict == "CONVICT", "expected CONVICT for the size-2 Aztec key"


if __name__ == "__main__":
    main()
