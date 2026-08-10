"""Phase 10 — OpenCV-as-graph: convolution kernels as graph-resident
primitives.

The biology-faithful posture (Hubel & Wiesel 1959; Daugman 1985; Marr
1980): every receptive field is a kernel; every kernel is a graph
node. The agent OWNS them as graph data — readable, editable,
composable from inside its own substrate.

Tests cover:
* The canonical receptive-field shapes (Gabor / DoG / Sobel /
  Laplacian / Gaussian) match their textbook properties.
* The agent can inspect kernels via the DSL (Attr on Kernel nodes).
* Convolution produces correct edge / orientation responses.
* The cascade wiring (`produced_by` / `from_input`) lets the agent
  trace a percept back to its source image + kernel chain.
* Biology-shaped banks (`v1_bank`, `lgn_pair`) build the right
  number of kernels with the right named orientations.
"""
from __future__ import annotations

import math

import numpy as np
import pytest


srs = pytest.importorskip("substrate_rs")
v = pytest.importorskip("substrate_rs.vision")


# --- Image bridge ---------------------------------------------------------


def test_image_round_trip_through_graph():
    s = srs.Substrate()
    v.seed_vision_grammar(s)
    arr = np.arange(15, dtype=np.uint8).reshape(3, 5)
    nid = v.image_from_array(s, arr)
    back = v.image_to_array(s, nid)
    np.testing.assert_array_equal(back, arr)
    assert v.image_shape(s, nid) == (3, 5, 1)


def test_image_round_trip_multichannel():
    s = srs.Substrate()
    v.seed_vision_grammar(s)
    arr = np.random.RandomState(0).randint(0, 256, size=(4, 5, 3), dtype=np.uint8)
    nid = v.image_from_array(s, arr)
    back = v.image_to_array(s, nid)
    np.testing.assert_array_equal(back, arr)


def test_image_origin_persisted_as_attr():
    s = srs.Substrate()
    v.seed_vision_grammar(s)
    nid = v.image_from_array(s, np.zeros((3, 3), dtype=np.uint8), origin="test")
    node = s.node(nid)
    assert node["attrs"]["origin"] == "test"
    assert node["attrs"]["width"] == 3
    assert node["attrs"]["height"] == 3


# --- Kernel bridge --------------------------------------------------------


def test_kernel_round_trip_and_describe():
    s = srs.Substrate()
    v.seed_vision_grammar(s)
    m = np.array([[1, 0, -1], [2, 0, -2], [1, 0, -1]], dtype=np.float32)
    nid = v.kernel_from_matrix(s, "test_sobel", m)
    back = v.kernel_to_array(s, nid)
    np.testing.assert_array_equal(back, m)
    d = v.kernel_describe(s, nid)
    assert d["name"] == "test_sobel"
    assert d["shape"] == (3, 3)
    assert d["sum"] == 0.0
    assert d["max"] == 2.0
    assert d["min"] == -2.0


def test_kernel_attrs_visible_to_dsl():
    """The agent can ask the substrate about kernel attrs via the
    standard DSL — proves the kernel really is graph data, not opaque."""
    s = srs.Substrate()
    v.seed_vision_grammar(s)
    g = v.gaussian(s, sigma=1.0)
    # Query via the DSL the agent uses for everything else.
    name = s.evaluate(srs.Attr(srs.Lit(g), "name"))
    # Lit(NodeID) → graph node lookup via Attr — same path the agent's
    # introspection uses on any other node type.
    assert name.startswith("gaussian:")
    kh = s.evaluate(srs.Attr(srs.Lit(g), "kh"))
    kw = s.evaluate(srs.Attr(srs.Lit(g), "kw"))
    assert kh == kw  # symmetric kernel
    origin = s.evaluate(srs.Attr(srs.Lit(g), "origin"))
    assert origin == "gaussian"


# --- Canonical kernels match their textbook properties --------------------


def test_gaussian_sums_to_one():
    s = srs.Substrate()
    g = v.gaussian(s, sigma=1.5)
    arr = v.kernel_to_array(s, g)
    assert abs(arr.sum() - 1.0) < 1e-5
    # Peak at the center.
    h, w = arr.shape
    assert arr.argmax() == (h // 2) * w + (w // 2)


def test_dog_sums_to_zero():
    """Difference-of-Gaussians: each Gaussian sums to 1, so DoG = 0
    on average. The defining property of an LGN center-surround
    cell: it responds to LOCAL contrast, ignores uniform regions."""
    s = srs.Substrate()
    on_center = v.dog(s, sigma_center=1.0, sigma_surround=2.0)
    arr = v.kernel_to_array(s, on_center)
    assert abs(arr.sum()) < 1e-4
    # ON-center: positive at the middle.
    h, w = arr.shape
    assert arr[h // 2, w // 2] > 0


def test_sobel_x_detects_vertical_edges():
    """A vertical step in the image should produce a strong response
    in the x-gradient and ~zero elsewhere."""
    s = srs.Substrate()
    v.seed_vision_grammar(s)
    img = np.zeros((20, 20), dtype=np.uint8)
    img[:, 10:] = 255
    img_nid = v.image_from_array(s, img)
    sx = v.sobel(s, dx=1, dy=0)
    edge_nid = v.convolve(s, img_nid, sx)
    edge = v.image_to_array(s, edge_nid)
    # Response peaks at the edge column.
    col_strength = np.abs(edge).mean(axis=0)
    assert col_strength.argmax() in (9, 10, 11)
    # Far from the edge, response is essentially zero.
    assert col_strength[0] < 1.0
    assert col_strength[-1] < 1.0


def test_sobel_y_detects_horizontal_edges():
    s = srs.Substrate()
    v.seed_vision_grammar(s)
    img = np.zeros((20, 20), dtype=np.uint8)
    img[10:, :] = 255
    img_nid = v.image_from_array(s, img)
    sy = v.sobel(s, dx=0, dy=1)
    edge = v.image_to_array(s, v.convolve(s, img_nid, sy))
    row_strength = np.abs(edge).mean(axis=1)
    assert row_strength.argmax() in (9, 10, 11)


def test_gabor_orientation_selectivity():
    """A vertical Gabor (θ=0) should respond strongly to a vertical
    bar and weakly to a horizontal bar — and vice versa. This is the
    defining property of V1 simple cells (Hubel & Wiesel 1959)."""
    s = srs.Substrate()
    v.seed_vision_grammar(s)
    vertical_bar = np.zeros((40, 40), dtype=np.uint8)
    vertical_bar[:, 18:22] = 255
    horizontal_bar = np.zeros((40, 40), dtype=np.uint8)
    horizontal_bar[18:22, :] = 255

    vb_nid = v.image_from_array(s, vertical_bar)
    hb_nid = v.image_from_array(s, horizontal_bar)
    # In cv2's convention θ is the angle of the NORMAL to the
    # carrier's stripes — θ=0 means stripes run vertically, so the
    # kernel responds to VERTICAL bars; θ=π/2 to horizontal bars.
    g_vert = v.gabor(s, sigma=3.0, theta=0.0, lambda_=8.0, ksize=11)
    g_horiz = v.gabor(s, sigma=3.0, theta=math.pi / 2, lambda_=8.0, ksize=11)

    resp_v_to_v = np.abs(v.image_to_array(s, v.convolve(s, vb_nid, g_vert))).mean()
    resp_v_to_h = np.abs(v.image_to_array(s, v.convolve(s, vb_nid, g_horiz))).mean()
    resp_h_to_h = np.abs(v.image_to_array(s, v.convolve(s, hb_nid, g_horiz))).mean()
    resp_h_to_v = np.abs(v.image_to_array(s, v.convolve(s, hb_nid, g_vert))).mean()

    # Each Gabor responds strongly to its preferred orientation,
    # weakly to the orthogonal one.
    assert resp_v_to_v > resp_v_to_h * 1.5
    assert resp_h_to_h > resp_h_to_v * 1.5


def test_v1_bank_returns_n_gabors_at_distinct_orientations():
    s = srs.Substrate()
    bank = v.v1_bank(s, n_orientations=8, sigma=2.0)
    assert len(bank) == 8
    # Each kernel's name carries its theta — extract and verify spread.
    names = [s.node(k)["attrs"]["name"] for k in bank]
    thetas = set()
    for n in names:
        # name shape: "gabor:θ=0.39,σ=2.0,λ=4.0"
        theta_str = n.split("θ=")[1].split(",")[0]
        thetas.add(float(theta_str))
    assert len(thetas) == 8  # all distinct


def test_lgn_pair_on_and_off_center():
    """The two LGN channels: ON-center has positive middle, OFF-center
    has negative middle. Same magnitude, opposite sign."""
    s = srs.Substrate()
    on, off = v.lgn_pair(s, sigma_on=1.0, sigma_off=2.0)
    on_arr = v.kernel_to_array(s, on)
    off_arr = v.kernel_to_array(s, off)
    h, w = on_arr.shape
    assert on_arr[h // 2, w // 2] > 0
    assert off_arr[h // 2, w // 2] < 0


# --- Convolution wires provenance --------------------------------------


def test_convolve_wires_provenance_edges():
    """After `convolve`, the output Image points back to its source
    Image AND the Kernel that produced it. The agent walking these
    edges can trace any percept to its derivation."""
    s = srs.Substrate()
    v.seed_vision_grammar(s)
    img_nid = v.image_from_array(s, np.zeros((10, 10), dtype=np.uint8))
    sx = v.sobel(s, dx=1, dy=0)
    out_nid = v.convolve(s, img_nid, sx)
    # produced_by edge points to the kernel
    produced = s.neighbours(out_nid, v.PRODUCED_BY)
    assert produced == [sx]
    # from_input edge points to the source image
    inputs = s.neighbours(out_nid, v.FROM_INPUT)
    assert inputs == [img_nid]


def test_apply_pipeline_chains_through_kernels():
    """`apply_pipeline` builds a chain image → conv1 → conv2 → ...,
    returning every intermediate. Each intermediate's provenance
    edges link it backwards in the chain."""
    s = srs.Substrate()
    v.seed_vision_grammar(s)
    img = np.zeros((20, 20), dtype=np.uint8)
    img[:, 10:] = 255
    img_nid = v.image_from_array(s, img)
    chain = [
        v.gaussian(s, sigma=1.0),
        v.sobel(s, dx=1, dy=0),
        v.gaussian(s, sigma=0.5),
    ]
    results = v.apply_pipeline(s, img_nid, chain)
    assert len(results) == 3
    # The final result's "from_input" points to the 2nd-to-last, etc.
    inputs_of_final = s.neighbours(results[-1], v.FROM_INPUT)
    assert inputs_of_final == [results[-2]]
    inputs_of_first = s.neighbours(results[0], v.FROM_INPUT)
    assert inputs_of_first == [img_nid]


def test_v1_responses_one_per_kernel():
    """v1_responses applies every bank kernel to the same input,
    producing N parallel response images. Models V1 column output."""
    s = srs.Substrate()
    v.seed_vision_grammar(s)
    img_nid = v.image_from_array(s, np.random.RandomState(0).randint(
        0, 256, size=(20, 20), dtype=np.uint8))
    bank = v.v1_bank(s, n_orientations=4, sigma=2.0)
    responses = v.v1_responses(s, img_nid, bank)
    assert len(responses) == 4
    # Every response points back to the same input.
    for r in responses:
        assert s.neighbours(r, v.FROM_INPUT) == [img_nid]


# --- Pool + threshold --------------------------------------------------


def test_max_pool_halves_each_dimension():
    s = srs.Substrate()
    v.seed_vision_grammar(s)
    arr = np.arange(16, dtype=np.uint8).reshape(4, 4)
    img_nid = v.image_from_array(s, arr)
    pooled = v.pool(s, img_nid, kh=2, kw=2, mode="max")
    out = v.image_to_array(s, pooled)
    assert out.shape == (2, 2)
    # Max-pool of a 2x2 corner is the bottom-right of that corner
    # (because arange is row-major increasing).
    assert out[0, 0] == 5     # max(0,1,4,5)
    assert out[1, 1] == 15    # max(10,11,14,15)


def test_threshold_binary_produces_0_1():
    s = srs.Substrate()
    v.seed_vision_grammar(s)
    arr = np.array([[0, 100, 200], [50, 150, 250]], dtype=np.uint8)
    img_nid = v.image_from_array(s, arr)
    out_nid = v.threshold(s, img_nid, t=128, mode="binary")
    out = v.image_to_array(s, out_nid)
    assert out.dtype == np.float32
    np.testing.assert_array_equal(out, [[0, 0, 1], [0, 1, 1]])


# --- The biology story: agent can introspect its own visual cortex ----


def test_agent_can_count_its_own_kernels_via_dsl():
    """The whole point: the agent's perceptual primitives are graph
    data, queryable by the agent itself. Counting via the standard
    Count-over-nodes-of-type pattern."""
    s = srs.Substrate()
    v.seed_vision_grammar(s)
    v.v1_bank(s, n_orientations=6, sigma=2.0)
    v.lgn_pair(s)
    v.sobel(s, dx=1, dy=0)
    v.sobel(s, dx=0, dy=1)
    # 6 Gabors + 2 DoGs + 2 sobels = 10 kernels.
    kernels = s.nodes(v.KERNEL)
    assert len(kernels) == 10


def test_agent_can_filter_kernels_by_origin():
    """The agent can ask for `all the Gabor cells` by walking node
    attrs — same pattern it uses for any other graph-resident set."""
    s = srs.Substrate()
    v.seed_vision_grammar(s)
    v.v1_bank(s, n_orientations=4, sigma=2.0)
    v.lgn_pair(s)
    v.sobel(s, dx=1, dy=0)
    gabor_count = sum(
        1 for k in s.nodes(v.KERNEL)
        if s.node(k)["attrs"]["origin"] == "gabor"
    )
    dog_count = sum(
        1 for k in s.nodes(v.KERNEL)
        if s.node(k)["attrs"]["origin"] == "dog"
    )
    sobel_count = sum(
        1 for k in s.nodes(v.KERNEL)
        if s.node(k)["attrs"]["origin"] == "sobel"
    )
    assert (gabor_count, dog_count, sobel_count) == (4, 2, 1)
