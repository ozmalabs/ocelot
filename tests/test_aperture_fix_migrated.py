"""THE TRUNCATED APERTURE — the two-sided gate.

`VISION_APERTURE_FIX_PREREG.md`, committed at `f48ef9944fe9` BEFORE any
measurement. Seeds 71000-71199.

This is a fix where **byte-identity is expected in some places and NOT in
others**, and BOTH sides are demonstrated here:

  IDENTICAL  at d=0 and at every landed call-site configuration -- proven
             ARRAY-BY-ARRAY against a FROZEN VERBATIM COPY of the pre-fix
             function (`_orbit_windows_PREFIX` below), not against a
             re-description of it.
  CHANGED    at the trailing-edge windows with d>0 and pad=rho -- and the
             change is shown to be in the CORRECTING direction (the new window
             equals the window cut from a sufficiently padded source), not
             merely present.
  LOUD       an insufficiently padded call raises instead of returning a short
             array, and the guard is POSITIVE-CONTROLLED (the frozen pre-fix
             function is shown to return the short array silently on exactly
             the input that now raises -- so the gate is known to bite).

Every comparison is `np.array_equal` on the tiles. A shape bug that produces a
plausible SCALAR is exactly what went unreported for the life of this arc, so
nothing here compares summary statistics.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from domains import invariant_comparator_world as iw  # noqa: E402

REGION = iw.REGION
GRID = iw.GRID
#: A pad large enough that no window in this file can reach the border of a
#: big-padded source. Edge replication by more is the same replication further
#: out, so the big-padded cut is the GROUND TRUTH window.
BIG = 32


# --------------------------------------------------------------------------- #
#  THE FROZEN PRE-FIX IMPLEMENTATION — verbatim, as it stood at 64a9641b.
#  Kept so the "no-op" side of the gate compares against ACTUAL OLD CODE.
# --------------------------------------------------------------------------- #
def _orbit_windows_PREFIX(qsrc_padded, origin, rho, region=REGION):
    r0, c0 = origin
    out = []
    for j, (dr, dc) in enumerate(iw.orbit_offsets(rho)):
        rr, cc = r0 + rho + dr, c0 + rho + dc
        out.append((j, qsrc_padded[rr:rr + region, cc:cc + region]))
    return out


def _src(seed, n=GRID, k=iw.K_LEVELS):
    return np.asarray(np.random.RandomState(seed).randint(0, k, (n, n)), int)


def _truth_window(src, r, c, region=REGION):
    """The GROUND-TRUTH window at unpadded absolute position (r, c), with edge
    replication where it leaves the frame. Computed from a source padded far
    beyond anything this file reaches, so it cannot itself be truncated."""
    big = np.pad(np.asarray(src), BIG, mode="edge")
    return big[r + BIG:r + BIG + region, c + BIG:c + BIG + region]


ORIGINS = iw.region_origins()
EDGE_ORIGINS = [(r, c) for (r, c) in ORIGINS
                if r == GRID - REGION or c == GRID - REGION]
INTERIOR_ORIGINS = [(r, c) for (r, c) in ORIGINS if (r, c) not in EDGE_ORIGINS]


# --------------------------------------------------------------------------- #
#  H2 — THE d=0 NO-OP, RE-ESTABLISHED HERE AND NOT CITED
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("rho", [0, 1, 2, 3])
def test_d0_is_byte_identical_to_the_prefix_function_array_by_array(rho):
    """The verdict rung STATED this fix is a no-op at zero displacement. This
    rung does not inherit that claim -- it re-derives it, element-wise, against
    the frozen pre-fix code, on 24 declared sources x 16 origins x (2rho+1)^2
    shifts."""
    n_compared = 0
    for seed in range(71000, 71024):
        src = _src(seed)
        padded = iw.pad_edge(src, rho)
        old = _orbit_windows_PREFIX(padded, (0, 0), rho)  # warm the shape path
        assert len(old) == (2 * rho + 1) ** 2
        for (r0, c0) in ORIGINS:
            new = iw.orbit_windows(padded, (r0, c0), rho)
            old = _orbit_windows_PREFIX(padded, (r0, c0), rho)
            assert len(new) == len(old)
            for (jn, tn), (jo, to) in zip(new, old):
                assert jn == jo
                assert np.array_equal(tn, to), (
                    f"d=0 MOVED at rho={rho} origin={(r0, c0)} shift={jn}")
                n_compared += 1
    assert n_compared == 24 * len(ORIGINS) * (2 * rho + 1) ** 2


def test_pad_edge_itself_is_semantically_unchanged():
    """The prereg's H2 proviso: the no-op holds only because the fix left
    `pad_edge` alone and touched ONLY the index arithmetic in `orbit_windows`.
    Asserted so a later edit to `pad_edge` cannot silently break d=0."""
    for seed in range(71024, 71030):
        src = _src(seed)
        assert np.array_equal(iw.pad_edge(src, 0), np.asarray(src))
        for rho in (1, 2, 3):
            assert np.array_equal(iw.pad_edge(src, rho),
                                  np.pad(np.asarray(src), rho, mode="edge"))


# --------------------------------------------------------------------------- #
#  H1 — THE FIX IS COMPLETE AND LOUD
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("rho", [0, 1, 2, 3])
@pytest.mark.parametrize("d", [0, 1, 2, 3, 4, 6])
def test_sufficient_pad_yields_a_full_window_everywhere(rho, d):
    """Padded by rho + |d|, EVERY window at EVERY origin and EVERY shift is
    exactly region x region -- and equals the ground-truth window."""
    src = _src(71030 + rho)
    pad = rho + d
    padded = iw.pad_edge(src, pad)
    for (r0, c0) in ORIGINS:
        for j, tile in iw.orbit_windows(padded, (r0 + d, c0 + d), rho, pad=pad):
            assert tile.shape == (REGION, REGION)
            dr, dc = iw.orbit_offsets(rho)[j]
            assert np.array_equal(
                tile, _truth_window(src, r0 + d + dr, c0 + d + dc)), (
                f"full window is not the ground-truth window at rho={rho} "
                f"d={d} origin={(r0, c0)} shift={(dr, dc)}")


@pytest.mark.parametrize("rho,d", [(1, 1), (2, 1), (2, 2), (2, 3), (3, 4), (2, 6)])
def test_insufficient_pad_is_LOUD_and_the_prefix_code_was_SILENT(rho, d):
    """THE POSITIVE CONTROL FOR THE GUARD (§12.3: a gate that has never been
    seen to fail has not been tested).

    On EXACTLY the same input, the frozen pre-fix function returns a SHORT
    array without complaint, and the fixed one raises. Both halves are
    asserted, so this test proves the guard bites AND that there was something
    for it to bite."""
    src = _src(71034)
    padded = iw.pad_edge(src, rho)          # the INSUFFICIENT pad
    # 1. the old code truncates SILENTLY on at least one trailing-edge origin
    short = []
    for (r0, c0) in EDGE_ORIGINS:
        for _j, tile in _orbit_windows_PREFIX(padded, (r0 + d, c0 + d), rho):
            if tile.shape != (REGION, REGION):
                short.append(tile.shape)
    assert short, (
        f"the pre-fix function did NOT truncate at rho={rho} d={d} -- this "
        f"positive control is vacuous and the parametrisation is wrong")
    # 2. the fixed code refuses
    with pytest.raises(ValueError, match="TRUNCATED APERTURE"):
        for (r0, c0) in EDGE_ORIGINS:
            iw.orbit_windows(padded, (r0 + d, c0 + d), rho)


def test_the_guard_is_the_only_thing_standing_between_them():
    """Isolates WHAT changed: with a sufficient pad the fixed function and the
    pre-fix function are the same function. The guard never fires on data the
    old code handled correctly -- so nothing that worked has been narrowed."""
    for seed in range(71035, 71040):
        src = _src(seed)
        for rho in (0, 1, 2, 3):
            padded = iw.pad_edge(src, rho)
            for (r0, c0) in INTERIOR_ORIGINS:
                new = iw.orbit_windows(padded, (r0, c0), rho)
                old = _orbit_windows_PREFIX(padded, (r0, c0), rho)
                for (_jn, tn), (_jo, to) in zip(new, old):
                    assert np.array_equal(tn, to)


# --------------------------------------------------------------------------- #
#  THE CHANGED SIDE — and the change is in the CORRECTING direction
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("d", [1, 2, 3, 4, 6])
def test_edge_windows_at_dgt0_CHANGE_and_change_toward_the_truth(d):
    """A fix that changes nothing anywhere has not been applied.

    At the trailing-edge origins with d>0, the pre-fix code returned a window
    that is NOT the ground-truth window (it is short). The fixed code, padded
    correctly, returns one that IS -- element-wise. Both facts are asserted, so
    the change is shown to be a CORRECTION and not merely a difference."""
    rho = 2
    src = _src(71040 + d)
    old_padded = iw.pad_edge(src, rho)            # what the old caller built
    new_padded = iw.pad_edge(src, rho + d)        # what the fixed caller builds
    n_wrong_before, n_right_after = 0, 0
    for (r0, c0) in EDGE_ORIGINS:
        old = _orbit_windows_PREFIX(old_padded, (r0 + d, c0 + d), rho)
        new = iw.orbit_windows(new_padded, (r0 + d, c0 + d), rho, pad=rho + d)
        for (j, to), (_j, tn) in zip(old, new):
            dr, dc = iw.orbit_offsets(rho)[j]
            truth = _truth_window(src, r0 + d + dr, c0 + d + dc)
            assert np.array_equal(tn, truth)
            n_right_after += 1
            if not np.array_equal(to, truth):
                n_wrong_before += 1
                assert to.shape != (REGION, REGION), (
                    "a full-sized pre-fix window disagreed with the truth -- "
                    "that would be a DIFFERENT defect than the one fixed")
    assert n_wrong_before > 0, (
        f"nothing changed at d={d}: the fix would be unapplied")
    assert n_right_after == len(EDGE_ORIGINS) * (2 * rho + 1) ** 2


def test_a_truncated_window_has_a_strictly_lower_ceiling():
    """WHY the truncation is a SELECTION bias and not only a score error, shown
    on the mechanism rather than asserted in prose: `covered_count` counts goal
    relations present in the candidate, so a 24-cell probe can score at most 24
    where a 36-cell probe can score 36. A short window CANNOT WIN an argmax
    against a full one, whatever the image contains."""
    rho, d = 2, 3
    src = _src(71045)
    padded = iw.pad_edge(src, rho)
    seen_short = False
    for (r0, c0) in EDGE_ORIGINS:
        for _j, tile in _orbit_windows_PREFIX(padded, (r0 + d, c0 + d), rho):
            n = int(np.asarray(tile).size)
            if n < REGION * REGION:
                seen_short = True
                # the ceiling IS the cell count: sig_of emits one tuple per cell
                assert len(iw.sig_of(tile)) == n < REGION * REGION
                assert len(iw.sig_of(np.zeros((REGION, REGION), int))) == 36
    assert seen_short


# --------------------------------------------------------------------------- #
#  H3 — THE LANDED CALL SITES ARE BYTE-IDENTICAL (instrumented, not argued)
# --------------------------------------------------------------------------- #
def test_the_C3_call_site_never_truncated_because_the_source_is_the_full_photo():
    """C3 DOES displace (d up to 6, and diagonally), so the d=0 no-op argument
    does NOT cover it. It is unaffected for a different reason, measured here:
    its source is the full BSDS photo with the 24x24 grid taken at the CENTRE,
    so the photo's own ~150px margin -- not `pad_edge` -- bounds every window.

    Simulated at the exact geometry (a 321x481 source, centred grid) rather
    than by loading BSDS, so the gate does not depend on the corpus."""
    src = _src(71050, n=1)  # placeholder; replaced below with the real shape
    src = np.asarray(np.random.RandomState(71050).randint(
        0, iw.K_LEVELS, (321, 481)), int)
    ar, ac = (321 - GRID) // 2, (481 - GRID) // 2
    origins = [(ar + r, ac + c) for r, c in ORIGINS]
    for rho in (0, 1, 2, 3):
        for d in (0, 1, 2, 3, 4, 6):
            for (dr, dc) in ((0, d), (d, d)):
                pad = rho + max(abs(dr), abs(dc))
                old = iw.pad_edge(src, rho)
                new = iw.pad_edge(src, pad)
                for (r0, c0) in origins:
                    o = _orbit_windows_PREFIX(old, (r0 + dr, c0 + dc), rho)
                    n = iw.orbit_windows(new, (r0 + dr, c0 + dc), rho, pad=pad)
                    for (_j, to), (_k, tn) in zip(o, n):
                        assert to.shape == (REGION, REGION), \
                            "C3 DID truncate -- H3's prediction is wrong"
                        assert np.array_equal(to, tn), \
                            "the C3 windows MOVED -- the C3 result is in scope"


def test_the_video_call_site_never_truncated_because_every_probe_is_at_zero():
    """The video path uses genuine 24x24 frames, where the padding IS the
    binding constraint -- and escapes only because every probe there is
    presented at offset (0,0). Asserted at the real 24x24 geometry."""
    for rho in (0, 1, 2):
        for seed in range(71055, 71060):
            src = _src(seed)
            padded = iw.pad_edge(src, rho)
            for (r0, c0) in ORIGINS:
                o = _orbit_windows_PREFIX(padded, (r0 + 0, c0 + 0), rho)
                n = iw.orbit_windows(padded, (r0 + 0, c0 + 0), rho, pad=rho)
                for (_j, to), (_k, tn) in zip(o, n):
                    assert to.shape == (REGION, REGION)
                    assert np.array_equal(to, tn)


def test_the_migrated_test_call_site_never_truncated_on_its_42x42_source():
    """`test_invariant_comparator_migrated._present_shifted` displaces by d and
    pads by rho, which is the defective combination -- but its source is 42x42
    with the grid centred (margin 9), so it too escapes on source size. That
    file is another rung's and is NOT edited; this asserts it stays green."""
    for rho, d in ((1, 1), (2, 2), (3, 3), (1, 2), (2, 3), (0, 0), (0, 1), (0, 3)):
        src = _src(71060 + rho, n=42)
        ar = (42 - GRID) // 2
        origins = [(ar + r, ar + c) for r, c in ORIGINS]
        padded = iw.pad_edge(src, rho)
        for (r0, c0) in origins:
            o = _orbit_windows_PREFIX(padded, (r0, c0 + d), rho)
            n = iw.orbit_windows(padded, (r0, c0 + d), rho, pad=rho)
            for (_j, to), (_k, tn) in zip(o, n):
                assert to.shape == (REGION, REGION)
                assert np.array_equal(to, tn)


def test_the_runner_now_pads_by_rho_plus_displacement():
    """The adapter guard is only half the fix -- the caller must pad enough for
    it never to fire. Asserted on the runner's source so the two cannot drift
    apart silently."""
    src = open(os.path.join(ROOT, "scripts",
                            "invariant_comparator_measure.py")).read()
    assert "pad = rho + max(abs(dr), abs(dc))" in src
    assert "iw.pad_edge(qsrc, pad)" in src
    assert "rho, pad=pad)" in src
    assert "iw.pad_edge(qsrc, rho)" not in src, \
        "the runner still builds a rho-padded source"


# --------------------------------------------------------------------------- #
#  ARCHITECTURE — this rung adds no agent logic
# --------------------------------------------------------------------------- #
def test_this_rung_adds_no_rust_and_no_seed():
    """Pinned to THIS RUNG'S OWN COMMIT RANGE, never to HEAD (§12.3 + the
    endpoint guard): both endpoints are explicit shas."""
    import subprocess
    if set(APERTURE_FIX_END) == {"0"}:
        pytest.skip("end sha pinned by the results commit")
    rng = "f48ef9944fe9134e148e279185ebfd30ebabf8de^..%s" % APERTURE_FIX_END
    files = subprocess.run(
        ["git", "diff", "--name-only", rng], cwd=ROOT,
        capture_output=True, text=True).stdout.split()
    assert files, "the pinned range is empty or unreachable"
    for f in files:
        assert not f.endswith(".rs"), f"this rung added Rust: {f}"
        assert not f.startswith("seeds/"), f"this rung touched a seed: {f}"


#: Filled in by the results commit; both provenance endpoints are explicit
#: shas, never `HEAD` (`test_provenance_endpoint_guard_migrated` refuses that).
APERTURE_FIX_END = "11bc0eeb086282a438e7ce01badf395ae3992174"
