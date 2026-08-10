"""GATE — appearance-tracked stability (block 151000-151999).

H1: an appearance-tracked template holds an object as ONE trajectory >=6 frames
    on a synthetic FRAGMENTATION-INDUCING fixture where the plain (Region-id)
    tracker fragments — and the held trajectory graph-mints order-2. ABLE TO
    FAIL: a distractor object is present every frame, so the association must
    SELECT the target by appearance; a wrong pick corrupts cy and kills order-2.
Controls: const-velocity -> order-1 not 2 (no manufactured curvature); static
    -> nothing; noise -> floors; two disjoint objects -> two runs, NOT merged.
BYTE-IDENTITY-OFF (§9): `longest_run(track, enabled=False)` is byte-identical to
    the existing `longest_run_indexed(track)`.
INVARIANT (§ frame/continuum): patches are read at INTEGER centroids; no float is
    written into an in-frame coordinate.

The order verdict is ALWAYS read from the GRAPH mint (`fw.discover_order` ->
`latent:time` order), NEVER from an exact d2 assertion (148000's flaky-gate
lesson). Deterministic: the synthetic textures draw already-burned 149xxx seeds.
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains import appearance_track as at
from domains import falling_world as fw
from scripts.subcell_crossframe_measure import longest_run_indexed

OBJ = 10
GH, GW = 200, 96


# ── graph-minted order verdict (read from the GRAPH, never exact d2) ───────────

def mint_order(cy_seq, cx_seq=None):
    """Max order of the `latent:time` dimension the graph mints from a perceived
    centroid trajectory. None if nothing minted. Pure ingest + read-back."""
    if cx_seq is None:
        cx_seq = [GW // 2] * len(cy_seq)
    s, ag, native = fw.boot_falling()
    _, mints = fw.discover_order(s, ag, native, cy_seq, cx_seq)
    orders = [m[1] for m in mints if m[1] is not None]
    return max(orders) if orders else None


# ── fixtures: a target (+ optional distractor) rendered into ONE grey stack ────
#
# Integer semi-implicit-Euler physics (`v+=g; y+=v`) so the perceived INTEGER
# centroid is an EXACT order-N sequence the graph witness reads cleanly: g>0 ->
# constant 2nd difference (order-2); g=0,v>0 -> constant 1st difference
# (order-1); g=0,v=0 -> static. (The real pipeline recovers sub-cell accel via
# 149000's registration; the gate uses integer positions so it reads the GRAPH
# order verdict without a sub-cell layer.)

def _euler_tops(y0, g, v0, n):
    tops, y, v = [], y0, v0
    for _ in range(n):
        tops.append(y)
        v += g
        y += v
    return tops


def _render_squares(tops_list, cx_list, seeds, n):
    """Render each textured square (DISTINCT texture per object) at its INTEGER
    top position into one grey stack. Returns (frames, [centroids per object])."""
    frames = np.zeros((n, GH, GW), dtype=np.float64)
    texs = [np.random.default_rng(s).integers(64, 256, size=(OBJ, OBJ)).astype(np.float64)
            for s in seeds]
    centroids = [[] for _ in tops_list]
    for t in range(n):
        for oi, (tops, cx, tex) in enumerate(zip(tops_list, cx_list, texs)):
            top = int(tops[t])
            r0, r1 = max(0, top), min(GH, top + OBJ)
            if r1 > r0:
                frames[t, r0:r1, cx:cx + OBJ] += tex[:r1 - r0, :]
            centroids[oi].append(top + OBJ / 2.0)
    return frames, centroids


def _two_object_frames(*, g_target, v_target, g_dist, v_dist, n,
                       cx_target, cx_dist, seed_t=149100, seed_d=149200,
                       y0_target=12, y0_dist=90):
    tops_t = _euler_tops(y0_target, g_target, v_target, n)
    tops_d = _euler_tops(y0_dist, g_dist, v_dist, n)
    frames, cents = _render_squares([tops_t, tops_d], [cx_target, cx_dist],
                                    [seed_t, seed_d], n)
    return frames, cents[0], cents[1]


def _regions(cyc, cx, *, count, ids):
    """Per-frame region dicts at the given centroids, with the given ids."""
    return [{"cy": cyc[t], "cx": float(cx), "count": float(count), "id": ids[t]}
            for t in range(len(cyc))]


# ───────────────────────────────── H1 ────────────────────────────────────────

def test_h1_appearance_holds_where_id_fragments():
    n = 8
    frames, cyc_t, cyc_d = _two_object_frames(
        g_target=2, v_target=0, g_dist=0, v_dist=0,
        cx_target=20, cx_dist=64, n=n)
    # FRESH id every frame for the target => the plain id-chain fragments.
    tgt = _regions(cyc_t, 20, count=OBJ * OBJ, ids=[1000 + t for t in range(n)])
    dst = _regions(cyc_d, 64, count=OBJ * OBJ - 5, ids=[2000 + t for t in range(n)])
    rpf = [(t, [tgt[t], dst[t]]) for t in range(n)]

    # plain tracker: per-frame LARGEST region (target), chained by id -> fragments.
    track = [(t, tgt[t]) for t in range(n)]
    id_run = at.longest_run(track, enabled=False)
    assert len(id_run) < 6, f"plain id tracker must fragment; got {len(id_run)}"

    # APPEARANCE over ALL regions: must SELECT the target and hold >=6.
    ap_run = at.longest_run_all(rpf, frames)
    assert len(ap_run) >= 6, f"appearance must hold >=6; got {len(ap_run)}"
    # it held the TARGET, not the distractor (cy tracks the accelerating object).
    assert all(abs(r["cx"] - 20.0) < 1e-9 for r in ap_run), "appearance jumped to distractor"

    # GRAPH verdict on the held trajectory: order-2 (accelerating).
    assert mint_order([r["cy"] for r in ap_run]) == 2, "held trajectory must mint order-2"


# ─────────────────────────────── controls ────────────────────────────────────

def test_control_const_velocity_no_manufactured_curvature():
    n = 8
    frames, cyc_t, cyc_d = _two_object_frames(
        g_target=0, v_target=3, g_dist=0, v_dist=0,
        cx_target=20, cx_dist=64, n=n)
    tgt = _regions(cyc_t, 20, count=OBJ * OBJ, ids=[1000 + t for t in range(n)])
    dst = _regions(cyc_d, 64, count=OBJ * OBJ - 5, ids=[2000 + t for t in range(n)])
    rpf = [(t, [tgt[t], dst[t]]) for t in range(n)]
    ap_run = at.longest_run_all(rpf, frames)
    assert len(ap_run) >= 6
    # const velocity must mint order-1, NEVER order-2 (no manufactured curvature).
    assert mint_order([r["cy"] for r in ap_run]) == 1


def test_control_static_mints_nothing():
    n = 8
    frames, cyc_t, _ = _two_object_frames(
        g_target=0, v_target=0, g_dist=0, v_dist=0,
        cx_target=20, cx_dist=64, n=n)
    tgt = _regions(cyc_t, 20, count=OBJ * OBJ, ids=[1000 + t for t in range(n)])
    rpf = [(t, [tgt[t]]) for t in range(n)]
    ap_run = at.longest_run_all(rpf, frames)
    # a static object mints no order-2 (order-1 with zero step or nothing).
    assert mint_order([r["cy"] for r in ap_run]) != 2


def test_control_noise_floors():
    n = 8
    rng = np.random.default_rng(149003)
    frames = rng.integers(0, 256, size=(n, GH, GW)).astype(np.float64)
    # regions at a fixed jittery centroid over incoherent frames.
    cyc = [GH // 2 + (t % 2) for t in range(n)]
    regs = _regions(cyc, GW // 2, count=OBJ * OBJ, ids=[3000 + t for t in range(n)])
    rpf = [(t, [regs[t]]) for t in range(n)]
    ap_run = at.longest_run_all(rpf, frames)
    assert mint_order([r["cy"] for r in ap_run]) != 2, "noise must not confabulate order-2"


def test_control_two_objects_not_merged():
    n = 8
    frames, cyc_a, cyc_b = _two_object_frames(
        g_target=2, v_target=0, g_dist=1, v_dist=2,
        cx_target=20, cx_dist=68, n=n, seed_t=149300, seed_d=149400)
    a0 = {"cy": cyc_a[0], "cx": 20.0, "count": OBJ * OBJ, "id": 1}
    b0 = {"cy": cyc_b[0], "cx": 68.0, "count": OBJ * OBJ, "id": 2}
    # fresh ids every frame (would fragment id-tracking); appearance must keep
    # the two objects SEPARATE (greedy one-to-one).
    regs_a = _regions(cyc_a, 20, count=OBJ * OBJ, ids=[100 + t for t in range(n)])
    regs_b = _regions(cyc_b, 68, count=OBJ * OBJ, ids=[200 + t for t in range(n)])
    rpf = [(t, [regs_a[t], regs_b[t]]) for t in range(n)]
    runs = at.track_multi(rpf, frames, [a0, b0])
    assert len(runs) == 2 and len(runs[0]) == n and len(runs[1]) == n
    # object A stayed at cx=20 throughout; B at cx=68 — no swap / merge.
    assert all(abs(r["cx"] - 20.0) < 1e-9 for r in runs[0]), "object A merged/swapped"
    assert all(abs(r["cx"] - 68.0) < 1e-9 for r in runs[1]), "object B merged/swapped"


# ─────────────────────── byte-identity when OFF (§9) ──────────────────────────

def test_byte_identity_off_equals_existing_longest_run():
    # a coherent per-frame track with real id runs + a break + a None gap.
    track = [
        (1, {"cy": 3.0, "cx": 5.0, "count": 100.0, "id": 7}),
        (2, {"cy": 5.0, "cx": 5.0, "count": 100.0, "id": 7}),
        (3, {"cy": 8.0, "cx": 5.0, "count": 100.0, "id": 7}),
        (4, None),
        (5, {"cy": 20.0, "cx": 5.0, "count": 90.0, "id": 9}),
        (6, {"cy": 24.0, "cx": 5.0, "count": 90.0, "id": 9}),
    ]
    off = at.longest_run(track, enabled=False)
    ref = longest_run_indexed(track)
    assert off == ref, "appearance OFF is not byte-identical to longest_run_indexed"


# ─────────────────────── invariant: no in-frame float (§ f/c) ─────────────────

def test_invariant_patch_read_at_integer_centroid():
    frame = np.arange(GH * GW, dtype=np.float64).reshape(GH, GW)
    # any float centroid within +/-0.5 of an integer reads the SAME patch as that
    # integer — the in-frame coordinate is stepped, precision lives only in the
    # cross-frame NCC comparison.
    assert np.array_equal(at.grey_patch(frame, 40.4, 30.4), at.grey_patch(frame, 40.0, 30.0))
    assert np.array_equal(at.grey_patch(frame, 39.6, 29.6), at.grey_patch(frame, 40.0, 30.0))
    # exact-.5 uses Python round (banker's): round(40.5)=40, round(41.5)=42.
    assert np.array_equal(at.grey_patch(frame, 41.5, 31.5), at.grey_patch(frame, 42.0, 32.0))


def test_invariant_run_passes_through_carve_coords():
    # the appearance run must carry the carve's OWN cy/cx unchanged (no new
    # in-frame float introduced by the association layer).
    n = 6
    frames, cyc_t, _ = _two_object_frames(
        g_target=2, v_target=0, g_dist=0, v_dist=0,
        cx_target=20, cx_dist=64, n=n)
    tgt = _regions(cyc_t, 20, count=OBJ * OBJ, ids=[1000 + t for t in range(n)])
    rpf = [(t, [tgt[t]]) for t in range(n)]
    ap_run = at.longest_run_all(rpf, frames)
    for r in ap_run:
        src = tgt[r["fi"]]
        assert r["cy"] == src["cy"] and r["cx"] == src["cx"], "association mutated a coordinate"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
