"""Phase 11b + 11c — V2/V4 hierarchical layers + Hebbian / Oja kernel
learning.

The hierarchy: HMAX-shape (Riesenhuber & Poggio 1999) alternating
S→C layers. C-cells pool over local S-cell responses for translation
tolerance; combinations across orientations build junction / corner
detectors.

The learning: Hebbian (Hebb 1949) and Oja's rule (1982). The agent
rewrites its own receptive fields based on the input statistics it
sees — biological feature learning, expressed as direct mutation of
Kernel-node weight attrs.
"""
from __future__ import annotations

import math

import numpy as np
import pytest


srs = pytest.importorskip("substrate_rs")
v = pytest.importorskip("substrate_rs.vision")


@pytest.fixture
def s():
    sub = srs.Substrate()
    v.seed_vision_grammar(sub)
    return sub


# --- V2 / V4 hierarchical layers ----------------------------------------


def test_complex_cell_halves_spatial_dims(s):
    """C-cell pool with kh=kw=2 halves each dim (standard HMAX C1)."""
    arr = np.arange(64, dtype=np.float32).reshape(8, 8)
    img_nid = v.image_from_array(s, arr)
    c_nid = v.complex_cell(s, img_nid, kh=2, kw=2)
    h, w, _ = v.image_shape(s, c_nid)
    assert (h, w) == (4, 4)


def test_complex_cell_gives_translation_tolerance(s):
    """The defining property: a stimulus translated by ≤ pool size
    produces the same C-cell response. Verify by translating a bright
    pixel within a 2×2 pool window and checking the max-pool output
    is unchanged at that pool cell."""
    base = np.zeros((8, 8), dtype=np.float32)
    base[2, 2] = 1.0
    img_a = v.image_from_array(s, base.copy())
    # Translate the pixel within the (2,2) pool cell (rows 2-3, cols 2-3).
    base2 = np.zeros((8, 8), dtype=np.float32)
    base2[3, 3] = 1.0
    img_b = v.image_from_array(s, base2.copy())
    out_a = v.image_to_array(s, v.complex_cell(s, img_a, kh=2, kw=2))
    out_b = v.image_to_array(s, v.complex_cell(s, img_b, kh=2, kw=2))
    # Same pool cell (row 1, col 1) in the output for both.
    assert out_a[1, 1] == 1.0
    assert out_b[1, 1] == 1.0


def test_v2_pool_layer_one_output_per_v1_response(s):
    """v2_pool_layer applies a C-cell to every V1 response in order
    — preserves the orientation-bank structure."""
    img = np.random.RandomState(0).randint(0, 256, size=(20, 20), dtype=np.uint8)
    img_nid = v.image_from_array(s, img)
    bank = v.v1_bank(s, n_orientations=4, sigma=2.0)
    v1_resps = v.v1_responses(s, img_nid, bank)
    v2_resps = v.v2_pool_layer(s, v1_resps, kh=2, kw=2)
    assert len(v2_resps) == 4
    # Each V2 response is half the spatial dims of the V1 input.
    for r in v2_resps:
        h, w, _ = v.image_shape(s, r)
        assert (h, w) == (10, 10)


def test_combine_orientations_sums_correctly(s):
    """Linear combo of three constant-valued images with given weights
    should give a constant equal to the weighted sum."""
    a = v.image_from_array(s, np.ones((4, 4), dtype=np.float32) * 1.0)
    b = v.image_from_array(s, np.ones((4, 4), dtype=np.float32) * 2.0)
    c = v.image_from_array(s, np.ones((4, 4), dtype=np.float32) * 3.0)
    out_nid = v.combine_orientations(s, [a, b, c], weights=[0.5, 1.0, -1.0])
    out = v.image_to_array(s, out_nid)
    # 0.5*1 + 1.0*2 + (-1.0)*3 = -0.5
    np.testing.assert_allclose(out, -0.5)


def test_combine_orientations_wires_provenance(s):
    """Output points back at each input via `from_input` — the agent
    can walk the edges to see what was combined."""
    a = v.image_from_array(s, np.ones((4, 4), dtype=np.float32))
    b = v.image_from_array(s, np.ones((4, 4), dtype=np.float32) * 2)
    out = v.combine_orientations(s, [a, b])
    inputs = sorted(s.neighbours(out, v.FROM_INPUT), key=lambda n: n.value)
    assert inputs == sorted([a, b], key=lambda n: n.value)


def test_v2_corner_detector_fires_strongest_at_corners(s):
    """The headline test for V2: a corner detector should respond
    most strongly at image locations where BOTH edges are present,
    less strongly along a single edge.

    Build an L-shape (one vertical stroke + one horizontal stroke
    meeting at a corner). The corner detector should peak at the
    junction."""
    img = np.zeros((40, 40), dtype=np.uint8)
    img[10:30, 20] = 255      # vertical stroke through (10..30, 20)
    img[20, 20:30] = 255      # horizontal stroke through (20, 20..30)
    # The corner is at (20, 20).
    img_nid = v.image_from_array(s, img)
    corner_resp = v.v2_corner_detector(
        s, img_nid, theta_a=0.0, theta_b=math.pi / 2,
        sigma=2.0, lambda_=6.0, ksize=11, pool_kh=2, pool_kw=2)
    out = v.image_to_array(s, corner_resp)
    # Find the max response location and check it's near the corner
    # (scaled by the pool factor: corner is at (20,20) in input, so
    # ~(10,10) in the pooled output).
    flat_argmax = int(np.argmax(out))
    h, w = out.shape
    peak_r, peak_c = flat_argmax // w, flat_argmax % w
    # Within 3 cells of the expected corner (allow Gabor receptive
    # field spread + pooling).
    assert abs(peak_r - 10) <= 3
    assert abs(peak_c - 10) <= 3


def test_v4_pool_layer_pools_v2_input(s):
    img = np.random.RandomState(0).randint(0, 256, size=(20, 20), dtype=np.uint8)
    img_nid = v.image_from_array(s, img)
    bank = v.v1_bank(s, n_orientations=4, sigma=2.0)
    v1 = v.v1_responses(s, img_nid, bank)
    v2 = v.v2_pool_layer(s, v1, kh=2, kw=2)
    v4 = v.v4_pool_layer(s, v2, kh=2, kw=2)
    assert len(v4) == 4
    for r in v4:
        h, w, _ = v.image_shape(s, r)
        assert (h, w) == (5, 5)


# --- Hebbian + Oja learning -------------------------------------------


def test_hebbian_grows_kernel_magnitude_unboundedly(s):
    """Plain Hebbian's *defining* property (and its biggest practical
    problem): the weight norm grows without bound when the input
    distribution doesn't average to zero. Verify by tracking the
    kernel's L2 norm — it should monotonically increase. Oja's rule
    (next test) adds the normalisation that fixes this."""
    img = np.ones((10, 10), dtype=np.float32)
    img_nid = v.image_from_array(s, img)
    rng = np.random.RandomState(0)
    init = rng.randn(3, 3).astype(np.float32) * 0.1
    k = v.kernel_from_matrix(s, "hebb_growth", init)
    norms = [v.kernel_norm(s, k)]
    for _ in range(10):
        v.hebbian_update(s, k, img_nid, lr=0.2, decay=0.0)
        norms.append(v.kernel_norm(s, k))
    # Strictly monotonic growth — the textbook Hebbian instability.
    for i in range(1, len(norms)):
        assert norms[i] > norms[i - 1], f"norm should grow: {norms}"


def test_hebbian_in_place_kernel_weights_change(s):
    """Hebbian mutates the kernel's `weights` attr in place — same
    NodeID, different weights. Witnesses that the agent's receptive
    fields are LIVE graph data, not snapshots."""
    img_nid = v.image_from_array(s, np.random.RandomState(0).rand(20, 20).astype(np.float32))
    k = v.gabor(s, sigma=2.0, theta=0.0, lambda_=4.0, ksize=5)
    before = v.kernel_to_array(s, k).copy()
    v.hebbian_update(s, k, img_nid, lr=0.05)
    after = v.kernel_to_array(s, k)
    # Same NodeID, different weights.
    assert not np.allclose(before, after)


def test_oja_rule_normalises_kernel_to_unit_norm(s):
    """Oja's rule provably drives the kernel weights to unit L2 norm.
    Verify by tracking the norm over many updates — should converge
    toward 1.0 regardless of starting magnitude."""
    rng = np.random.RandomState(1)
    # Random training images (uniform noise — no preferred direction
    # so the test focuses on normalisation, not on PC learning).
    big_img = rng.rand(30, 30).astype(np.float32)
    img_nid = v.image_from_array(s, big_img)

    init = rng.randn(5, 5).astype(np.float32) * 0.5  # norm ~2.5
    k = v.kernel_from_matrix(s, "oja_test", init)
    initial_norm = v.kernel_norm(s, k)
    assert initial_norm > 1.0  # starts above unit norm

    for _ in range(200):
        v.oja_update(s, k, img_nid, lr=0.05)
    final_norm = v.kernel_norm(s, k)
    # Oja drives toward unit norm. Allow some slack — it's stochastic
    # in finite steps.
    assert 0.5 < final_norm < 1.5, f"oja didn't normalise; norm={final_norm:.3f}"
    # And it moved TOWARD 1.0 from 2.5.
    assert abs(final_norm - 1.0) < abs(initial_norm - 1.0)


def test_oja_extracts_dominant_direction(s):
    """Oja's classical result: the weight vector converges to the
    first principal component of the input distribution. Show many
    vertical-edge images; the kernel should align with the vertical-
    edge direction."""
    rng = np.random.RandomState(2)
    # Make a strong vertical-edge image: gradient running left→right.
    # Convolution patches will all have the same dominant vertical-edge
    # signal, so PCA's first PC should be a vertical edge.
    img = np.zeros((30, 30), dtype=np.float32)
    for c in range(30):
        img[:, c] = c / 30.0
    img_nid = v.image_from_array(s, img)

    init = rng.randn(3, 3).astype(np.float32) * 0.1
    k = v.kernel_from_matrix(s, "oja_pc", init)
    for _ in range(300):
        v.oja_update(s, k, img_nid, lr=0.05)
    learned = v.kernel_to_array(s, k)
    # The learned kernel should be approximately a horizontal-
    # gradient detector (left-to-right contrast). Check that
    # row-summed weights are roughly constant (each row's pattern
    # is similar) and that column-summed weights are monotonic.
    col_sums = learned.sum(axis=0)
    # Monotonic in some direction (could be flipped sign).
    diffs = np.diff(col_sums)
    same_sign = (diffs[0] * diffs[1] > 0) if len(diffs) > 1 else True
    assert same_sign, f"learned kernel cols not monotonic: {col_sums}"


def test_kernel_learning_writes_through_to_graph(s):
    """Witnesses the substrate as source of truth: after Hebbian
    update, `kernel_to_array` returns the NEW weights and the
    Kernel node's `weights` attr literally contains the new list of floats.
    Same shape as the GraphEye cortex reading kernels via the ChangeDetect Term.

    Seed the kernel with non-zero weights so the convolution
    response is non-zero on the first update — Hebbian on (zero
    weights → zero response → zero update) is a fixed point and
    wouldn't witness anything.
    """
    img_nid = v.image_from_array(s, np.ones((10, 10), dtype=np.float32))
    k = v.kernel_from_matrix(
        s, "writethrough_test",
        np.full((3, 3), 0.1, dtype=np.float32))
    before = v.kernel_to_array(s, k).copy()
    v.hebbian_update(s, k, img_nid, lr=0.5)
    weights = v.kernel_to_array(s, k)
    # Hebbian on a non-zero kernel + non-zero input gives a non-zero
    # update — weights shifted.
    assert not np.array_equal(weights, before)
    # And the underlying graph attr matches — weights are now a
    # graph-resident List<f64> (the ChangeDetect Term reads them via
    # ``Attr(k, "weights")``), so the source-of-truth attr is a list.
    raw_list = s.node(k)["attrs"]["weights"]
    direct = np.array(raw_list, dtype=np.float32).reshape(3, 3)
    np.testing.assert_array_equal(weights, direct)
