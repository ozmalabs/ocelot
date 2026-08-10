"""Regression test for the CapabilityAxis novelty guard (2026-07-03, creator
directive "salience for axes"): `sd_mint_quantum` (seeds/shape_decode_loop.json)
minted a fresh CapabilityAxis for EVERY decoded Observation with a non-empty
residual, guarded only by "no `minted` edge yet on THIS Observation" —
idempotent PER-OBSERVATION but with NO DEDUP ACROSS Observations. A live
autonomous run showed CapabilityAxis count growing ~100/tick, monotonic,
never converging (28 -> 3674 over 38 ticks), because per-frame perception
(and the uncoverable metascience standing concern) repeatedly observe the
SAME uncovered residual and each observation minted its OWN axis.

The fix adds a final And-item to `sd_mint_quantum`'s where-clause:
`Not(Exists(NodesOfType('CapabilityAxis'), induced==1 AND
capability_keys==obs.key))` — mint only if no existing INDUCED axis already
carries the same identity. The mirror rule `sd_dedup_existing` handles the
suppressed case, setting a distinct terminal status (`recognized_duplicate`)
so `induce_concern` reads back the EXISTING axis instead of erroring or
fabricating a fresh mint.

This test is DISCRIMINATIVE: a genuinely-novel residual still mints (twice,
for two DISTINCT keys -> two DISTINCT axes); a REPEATED identical residual
(same key) mints exactly once — every subsequent call reads back the same
existing axis, no growth.
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")


def test_repeated_residual_dedups_but_distinct_residuals_each_mint():
    from substrate.boot_core import boot_core
    from domains import reflective_faculty as rf

    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)

    baseline_axes = len(list(s.nodes("CapabilityAxis")))

    # --- first observation of a genuinely-novel residual: mints ONE axis ---
    r1 = rf.induce_concern(s, [["zzzalpha", "X"]], name_hint="probe_dedup_alpha")
    assert r1["minted"] is True, "a genuinely-uncoverable residual must still mint"
    axis1_id = r1["axis_id"]
    assert len(list(s.nodes("CapabilityAxis"))) == baseline_axes + 1

    # --- SAME residual/key observed again (recurring per-frame-style
    #     re-observation): must NOT mint a second axis, must read the
    #     EXISTING one back via the recognized_duplicate terminal status ---
    r2 = rf.induce_concern(s, [["zzzalpha", "X"]], name_hint="probe_dedup_alpha")
    assert r2["minted"] is False, (
        "a duplicate residual (same capability_keys as an already-induced "
        "axis) must be suppressed, not minted again")
    assert r2.get("covered_by_existing_axis") == axis1_id, (
        "the suppressed-mint caller must read back the EXISTING covering "
        "axis, not a fresh/None value")
    assert len(list(s.nodes("CapabilityAxis"))) == baseline_axes + 1, (
        "no new axis from the duplicate observation")

    # --- observed a THIRD time: still dedups, still zero growth ---
    r3 = rf.induce_concern(s, [["zzzalpha", "X"]], name_hint="probe_dedup_alpha")
    assert r3["minted"] is False
    assert r3.get("covered_by_existing_axis") == axis1_id
    assert len(list(s.nodes("CapabilityAxis"))) == baseline_axes + 1, (
        "repeated re-observation must NOT grow the axis count (the bug this "
        "guard fixes: ~100 new axes/tick, monotonic)")

    # --- a DISTINCT novel residual (different key): mints its OWN axis ---
    r4 = rf.induce_concern(s, [["zzzbeta", "Y"]], name_hint="probe_dedup_beta")
    assert r4["minted"] is True, "a genuinely-distinct novel residual must still mint"
    axis4_id = r4["axis_id"]
    assert axis4_id != axis1_id, "distinct concerns must get distinct axes"
    assert len(list(s.nodes("CapabilityAxis"))) == baseline_axes + 2

    # --- and the distinct axis dedups on its own repeats too ---
    r5 = rf.induce_concern(s, [["zzzbeta", "Y"]], name_hint="probe_dedup_beta")
    assert r5["minted"] is False
    assert r5.get("covered_by_existing_axis") == axis4_id
    assert len(list(s.nodes("CapabilityAxis"))) == baseline_axes + 2, (
        "final count: exactly two axes for two distinct concerns, no matter "
        "how many times each was re-observed")
