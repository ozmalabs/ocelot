"""Verify the jabberwock UNDERSTANDS TRANSFORM EFFECTS — generically, on plain
rotate / flip / grow / replace, before pointing it at any game.

For each case: an object's shape changes from BEFORE to AFTER. The agent stamps
its pose/meta signatures and evaluates its OWN authored concepts:
  · shape_transformed  — did the FORM change? (a transform happened)
  · same_meta_shape    — is it still the SAME underlying shape?
The agent should read: rotation/flip = transformed BUT same meta; grow (same
shape bigger) = same meta; a DIFFERENT shape = not same meta (replaced, not
transformed). All via the order-N descriptor — no per-case code.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT), str(ROOT / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains.curious_agent import CuriousAgent  # noqa: E402
from domains.transform_concepts import (  # noqa: E402
    install_transform_concepts, stamp_shape)


def cells(rows):
    out = set()
    for r, line in enumerate(rows):
        for c, ch in enumerate(line):
            if ch == "#":
                out.add((r, c))
    return out


def rot90(s):
    return {(c, -r) for r, c in s}


def flip(s):
    return {(r, -c) for r, c in s}


def grow(s, k=2):
    return {(r * k + dr, c * k + dc) for r, c in s for dr in range(k) for dc in range(k)}


def main():
    agent = CuriousAgent()
    install_transform_concepts(agent)
    # one reusable object node we re-stamp before/after
    nid = agent.mind_graph._insert_node("Shape", {})

    L = cells(["##.", ".#.", ".#."])      # an L/T-ish shape
    other = cells(["###", "#..", "#.."])  # a genuinely different shape

    cases = [
        ("identity (no change)", L, L,            False, True),
        ("rotate 90",            L, rot90(L),      True,  True),
        ("rotate 180",           L, rot90(rot90(L)), True, True),
        ("flip",                 L, flip(L),       True,  True),
        ("grow x2 (same shape)", L, grow(L),       True,  True),
        ("replace (diff shape)", L, other,         True,  False),
    ]
    print("case                      transformed  same_meta   verdict")
    ok = 0
    for name, before, after, exp_t, exp_m in cases:
        stamp_shape(agent, nid, before)   # sets *_prev=before, *=before
        stamp_shape(agent, nid, after)    # now *_prev=before, *=after
        t = bool(agent._concept_holds("shape_transformed", nid))
        m = bool(agent._concept_holds("same_meta_shape", nid))
        passed = (t == exp_t and m == exp_m)
        ok += passed
        verdict = ("same shape, TRANSFORMED" if (t and m)
                   else "REPLACED (different shape)" if (t and not m)
                   else "unchanged")
        print(f"  {name:24s} {str(t):5s}        {str(m):5s}       "
              f"{'PASS' if passed else 'FAIL'}  ({verdict})")
    print(f"\n{ok}/{len(cases)} cases — the agent reads transforms generically "
          f"(its OWN authored concepts over its OWN order-N descriptor)")
    return 0 if ok == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
