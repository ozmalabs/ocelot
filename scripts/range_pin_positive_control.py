#!/usr/bin/env python3
"""POSITIVE CONTROL for the two range-pinned provenance gates.

*A gate you have only ever seen pass is not a gate you have tested* (protocol 12.3).
Both gates went GREEN after re-pinning. Green is exactly what a gate that no longer
looks at anything would also produce, so each half of each gate is driven RED here
against a range KNOWN to contain the thing it forbids.

The two halves:
  (1) the Rust-diff half  — widen RUNG to HEAD, which demonstrably contains Rust
      merged by LATER rungs. The assertion must fire. (This is the very condition
      that made the un-pinned gates red for ~54 commits, so it is also a
      reproduction of the original false accusation.)
  (2) the seed-blob half  — the two seeds these rungs reuse have never changed
      since their creation, so no real range can drive this red. It is exercised
      against a path that DID change over the same range, proving the comparison
      bites rather than silently comparing two identical reads.

Run: python3 scripts/range_pin_positive_control.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

FAILURES = []


def expect_red(label, fn):
    try:
        fn()
    except AssertionError as e:
        print(f"  RED (correct)   {label}\n                  -> {str(e).splitlines()[0][:110]}")
        return
    print(f"  GREEN (WRONG!)  {label}  -- the gate did NOT bite")
    FAILURES.append(label)


def expect_green(label, fn):
    try:
        fn()
        print(f"  GREEN (correct) {label}")
    except AssertionError as e:
        print(f"  RED (WRONG!)    {label} -> {e}")
        FAILURES.append(label)


def main():
    print("LOADAVG:", os.getloadavg())
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()
    print(f"HEAD = {head}\n")

    import test_cut_mint_policy_migrated as CM
    import test_video_accumulation_migrated as VA

    # ---- as-shipped: both must be GREEN on their own immutable ranges -------
    print("AS SHIPPED (own rung range):")
    expect_green("cut_mint::test_this_rung_adds_no_rust", CM.test_this_rung_adds_no_rust)
    for p in ("seeds/vision_identity_seam.json", "seeds/vision_cut_abstention.json"):
        expect_green(f"cut_mint::seeds_byte_unchanged[{p}]",
                     lambda p=p: CM.test_the_seeds_this_rung_reuses_are_byte_unchanged(p))
    expect_green("video_accum::test_this_rung_edits_no_seed_and_no_rust",
                 VA.test_this_rung_edits_no_seed_and_no_rust)

    # ---- control 1: widen RUNG to HEAD -> later rungs' Rust enters the range -
    print("\nCONTROL 1 — RUNG widened to HEAD (range now contains later rungs' Rust):")
    cm_rung, va_rung = CM.RUNG, VA.RUNG
    try:
        CM.RUNG = head
        expect_red("cut_mint::test_this_rung_adds_no_rust @ BASE..HEAD",
                   CM.test_this_rung_adds_no_rust)
        VA.RUNG = head
        expect_red("video_accum::test_this_rung_edits_no_seed_and_no_rust @ BASE..HEAD",
                   VA.test_this_rung_edits_no_seed_and_no_rust)
    finally:
        CM.RUNG, VA.RUNG = cm_rung, va_rung

    # ---- control 2: the seed-blob comparison itself -------------------------
    # Neither reused seed has EVER changed, so no honest range reddens this half.
    # Drive it with a path that demonstrably moved over the same range, so the
    # comparison is shown to bite rather than to compare a file with itself.
    print("\nCONTROL 2 — the seed-blob comparison, against a path that DID move:")
    moved = "VISION_PROTOCOL.md"
    # cwd is already the gamma-substrate dir, so the pathspec is relative to it.
    d = subprocess.run(["git", "diff", "--name-only", VA.BASE, head, "--", moved],
                       cwd=ROOT, capture_output=True, text=True).stdout.strip()
    assert d, f"{moved} did not change over {VA.BASE}..{head}; pick another path"

    def blob_mismatch():
        assert VA._blob_at(head, moved) == VA._blob_at(VA.BASE, moved), \
            f"{moved} CHANGED between {VA.BASE} and {head}"
    expect_red(f"_blob_at comparison on {moved} ({VA.BASE}..{head})", blob_mismatch)

    def blob_match():
        assert VA._blob_at(VA.BASE, moved) == VA._blob_at(VA.BASE, moved)
    expect_green(f"_blob_at comparison on {moved} (BASE..BASE, identical)", blob_match)

    print()
    if FAILURES:
        print(f"POSITIVE CONTROL FAILED: {FAILURES}")
        return 1
    print("POSITIVE CONTROL PASSED — every half of both gates was driven RED "
          "on a range containing what it forbids, and GREEN on its own range.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
