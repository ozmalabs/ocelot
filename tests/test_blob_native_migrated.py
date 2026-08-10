"""Gates for blob-native sampling (`VISION_BLOB_NATIVE_PREREG.md`, df0156a4).

Every test here pins something the rung CLAIMED. In particular
`test_blob_field_raises_when_no_border_is_flagged` is the dead-instrument
control: the silent-absence defect it pins actually occurred during this rung
(the threshold border matched nothing at kappa in {1,2,3}, the bg flood had no
seed, and the mint rule fired vacuously on every frame). A gate that has never
been able to fail has not been tested -- this one has failed, and this is it.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains import blob_sampler as bs  # noqa: E402


# --- the profile's SHAPE is forced, not chosen ------------------------------ #
def test_ring_spacing_is_geometric():
    """e_{n+1} = e_n (1 + 2/kappa) -- forced by self-similarity + isotropy."""
    kappa, R = 4.0, 40.0
    ecc = bs.ring_eccentricities(kappa, R)
    assert len(ecc) >= 3
    growth = 1.0 + 2.0 / kappa
    for a, b in zip(ecc, ecc[1:]):
        assert b == pytest.approx(a * growth, rel=1e-9)


def test_blobs_per_ring_is_constant_and_is_pi_kappa():
    """N_theta = pi * kappa, the same on every ring. Self-similarity means the
    per-ring count cannot depend on the ring."""
    for kappa in (2.0, 4.0, 8.0):
        assert bs.blobs_per_ring(kappa) == max(1, int(math.floor(math.pi * kappa + 0.5)))
    lay = bs.blob_layout(30.0, bs.layout_count(4.0, 30.0))
    by_ring: dict[float, int] = {}
    for dy, dx, _r in lay[1:]:
        by_ring[round(math.hypot(dy, dx), 6)] = by_ring.get(round(math.hypot(dy, dx), 6), 0) + 1
    assert len(set(by_ring.values())) == 1


def test_radius_is_proportional_to_eccentricity_above_the_pixel_limit():
    """r(e) = e/kappa, floored at the one-pixel sampling limit. The floor IS the
    frame/continuum invariant: nothing finer than a pixel can be grounded."""
    kappa, R = 6.0, 40.0
    lay = bs.blob_layout(R, bs.layout_count(kappa, R))
    assert min(r for _y, _x, r in lay) == pytest.approx(bs.PIXEL_LIMIT)
    for dy, dx, r in lay[1:]:
        e = math.hypot(dy, dx)
        if e / kappa > bs.PIXEL_LIMIT:
            assert r == pytest.approx(e / kappa, rel=1e-6)


def test_density_decays_with_eccentricity():
    """Blob AREA grows with eccentricity, i.e. sampling density decays -- the
    recorded principle 'grounding radiates outward and decays with
    eccentricity', realised rather than asserted."""
    lay = bs.blob_layout(40.0, bs.layout_count(4.0, 40.0))
    pairs = sorted((math.hypot(dy, dx), r) for dy, dx, r in lay)
    inner = [r for e, r in pairs if e <= pairs[len(pairs) // 3][0]]
    outer = [r for e, r in pairs if e >= pairs[2 * len(pairs) // 3][0]]
    assert np.mean(outer) > np.mean(inner)


def test_alternate_rings_are_staggered():
    """Consecutive rings must not share a spoke, or the layout re-acquires a
    preferred axis -- the uniformity the principle forbids."""
    kappa, R = 6.0, 40.0
    lay = bs.blob_layout(R, bs.layout_count(kappa, R))
    rings: dict[float, list[float]] = {}
    for dy, dx, _r in lay[1:]:
        rings.setdefault(round(math.hypot(dy, dx), 6), []).append(
            math.atan2(dy, dx) % (2 * math.pi))
    keys = sorted(rings)
    assert len(keys) >= 2
    a = sorted(rings[keys[0]])
    b = sorted(rings[keys[1]])
    assert not any(abs(x - y) < 1e-9 for x in a for y in b)


# --- support is circular and OVERLAPPING, not a tiling ---------------------- #
def test_supports_overlap_rather_than_tile():
    kappa, R = 6.0, 40.0
    lay = bs.blob_layout(R, bs.layout_count(kappa, R))
    n_overlap = sum(
        1
        for i, (yi, xi, ri) in enumerate(lay)
        for j, (yj, xj, rj) in enumerate(lay)
        if i < j and math.hypot(yi - yj, xi - xj) < (ri + rj))
    assert n_overlap > 0


# --- the emitted value is STEPPED (in-frame is INTEGER) --------------------- #
def test_sampled_values_are_integers_in_range():
    rng = np.random.RandomState(80000)
    frame = rng.randint(0, 256, (24, 24)).astype(float)
    lay = bs.blob_layout(11.5, bs.layout_count(4.0, 11.5))
    vals = bs.sample_blobs(frame, lay, k=4)
    assert len(vals) == len(lay)
    assert all(isinstance(v, int) and 0 <= v < 4 for v in vals)


def test_flat_frame_samples_to_one_level():
    lay = bs.blob_layout(11.5, bs.layout_count(4.0, 11.5))
    vals = bs.sample_blobs(np.full((24, 24), 200.0), lay, k=4)
    assert len(set(vals)) == 1


# --- gate 3: the parser defect is gone BY CONSTRUCTION ---------------------- #
def test_signature_identity_is_an_integer_index_not_a_name():
    """The r143 -> 14 defect class cannot occur: there is no name string."""
    vals = list(range(150))
    sig = bs.sig_of_blobs(vals)
    assert len(sig) == 150
    assert sig[143][0] == "blob"
    assert sig[143][1] == 143 and isinstance(sig[143][1], int)
    assert all(isinstance(t[1], int) for t in sig)


def test_group_blobs_refuses_a_short_partition():
    """A short group would be scored against a full one and could not win an
    argmax -- a SELECTION bias, not only a count error."""
    lay = bs.blob_layout(11.5, bs.layout_count(4.0, 11.5))
    with pytest.raises(ValueError, match="SELECTION bias"):
        bs.group_blobs(lay, n_groups=len(lay), per_group=5)


# --- the dead-instrument control -------------------------------------------- #
def test_blob_field_raises_when_no_border_is_flagged():
    """THE DEFECT THIS RUNG ACTUALLY HIT. With no frame cell the bg flood has no
    seed, every blob keeps bg=0, every component reads as enclosed, and the mint
    rule fires vacuously -- 1 proto on every frame of both corpora at every k,
    which briefly read as the sharpest test SUCCEEDING.

    A layout with a single blob at the origin has no outermost ring, so the
    border is empty and the builder must REFUSE rather than return a field that
    looks normal."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "bpm", os.path.join(ROOT, "scripts", "blob_proto_measure.py"))
    bpm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bpm)

    from substrate.boot_core import boot_core

    s, _ag = boot_core()
    with pytest.raises(ValueError, match="NO BORDER"):
        bpm.blob_field(s, [1], [(0.0, 0.0, 1.0)], 7.5)


def test_blob_field_flags_the_outermost_ring():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "bpm", os.path.join(ROOT, "scripts", "blob_proto_measure.py"))
    bpm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bpm)

    from substrate.boot_core import boot_core

    lay = bs.blob_layout(7.5, bs.layout_count(3.0, 7.5))
    s, _ag = boot_core()
    handle = bpm.blob_field(s, [1] * len(lay), lay, 7.5)
    assert handle["n_frame"] == bs.blobs_per_ring(3.0)
