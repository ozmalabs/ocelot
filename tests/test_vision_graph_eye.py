"""Deprecated RGBEye graph-resident fixed-kernel compatibility tests.

The deprecated :class:`domains.vision.Eye` (and the bit-identical
parity comparison against it, plus the numpy ``refresh_kernels``
weight cache) retired with ``domains/vision.py`` — the convolve math
now runs in the Rust ``ChangeDetect`` Term against graph-resident
Kernel nodes, so there is no cv2.filter2D path and no weight cache to
refresh. What remains here is the GRAPH-RESIDENCE contract: the
RGBEye's receptive fields are first-class graph data the agent can
read via the DSL, edit live (the next frame sees new weights with no
refresh step), and count by role.
"""
from __future__ import annotations

import time
import inspect

import numpy as np
import pytest


srs = pytest.importorskip("substrate_rs")

from domains.vision_graph import RGBEye, PERCEPT, POLYGON  # noqa: E402


@pytest.fixture
def screen_frame():
    """A 40x80 RGB frame with a bright vertical stripe centred at
    col 40 - produces non-trivial edge / salience responses."""
    rng = np.random.RandomState(7)
    img = rng.randint(40, 80, size=(40, 80, 3), dtype=np.uint8)
    img[:, 35:45] = 255           # bright stripe
    img[10:30, 10:25] = 30        # dim block
    return img


def test_generic_cognitive_tasks_produce_snapshot(screen_frame):
    """End-to-end: GraphEye emits generic native receptive-field tasks."""
    s = srs.Substrate()
    g = RGBEye(substrate=s, n_az=8, context={"worker_capacity": 2}).build()
    try:
        g.submit(screen=screen_frame, posture_deg=0.0)
        snap = g.latest()
        assert snap is not None
        assert len(snap["percepts"]) == 8
    finally:
        g.stop()


def test_eye_output_is_identical_across_generic_worker_counts(screen_frame):
    snapshots = []
    for workers in (1, 2, 4):
        eye = RGBEye(
            substrate=srs.Substrate(), n_az=8,
            context={"worker_capacity": workers}).build()
        eye.submit(screen=screen_frame, posture_deg=0.0)
        snapshots.append(eye.latest())
        eye.stop()
    assert snapshots[0] == snapshots[1] == snapshots[2]


def test_eye_has_no_bespoke_worker_thread():
    source = inspect.getsource(RGBEye)
    assert "def _worker(" not in source
    assert "threading.Thread" not in source
    assert "run_cognitive_tasks" in source


# --- Graph-residence -----------------------------------------------------


def test_grapheye_kernels_exist_as_graph_nodes():
    s = srs.Substrate()
    g = RGBEye(substrate=s).build()
    g.stop()
    kernels = g.kernels()
    # Four canonical receptive fields lifted to graph data.
    assert set(kernels.keys()) == {"sobel_x", "sobel_y", "gauss_center", "gauss_surround"}
    # Each is a real Kernel node on the substrate.
    for name, nid in kernels.items():
        node = s.node(nid)
        assert node["type"] == "Kernel"
        # Role attr is what makes them discoverable by purpose.
        assert "role" in node["attrs"]


def test_agent_can_query_kernels_via_dsl():
    """The agent's standard DSL can read kernel attrs the same way
    it reads any other node - proves the receptive fields are graph
    data, not opaque cv2 hidden state. And the ChangeDetect Term
    reads ``Attr(k, "weights")`` on this same surface to run the
    convolve math, so the agent's receptive fields ARE the cortex's."""
    s = srs.Substrate()
    g = RGBEye(substrate=s).build()
    g.stop()
    sobel_x = g.kernels()["sobel_x"]
    role = s.evaluate(srs.Attr(srs.Lit(sobel_x), "role"))
    assert role == "v1_edge_x"
    kh = s.evaluate(srs.Attr(srs.Lit(sobel_x), "kh"))
    kw = s.evaluate(srs.Attr(srs.Lit(sobel_x), "kw"))
    assert (kh, kw) == (3, 3)
    name = s.evaluate(srs.Attr(srs.Lit(sobel_x), "name"))
    assert name.startswith("sobel:dx=1,dy=0")
    # weights are a graph-resident List[f64] the Term reads live.
    weights = s.evaluate(srs.Attr(srs.Lit(sobel_x), "weights"))
    assert len(weights) == 9


def test_agent_can_count_kernels_by_role():
    """An agent looking at its own visual cortex can ask 'how many
    edge detectors do I have?' - by walking the Kernel nodes and
    filtering on role."""
    s = srs.Substrate()
    g = RGBEye(substrate=s).build()
    g.stop()
    all_kernels = s.nodes("Kernel")
    by_role = {}
    for k in all_kernels:
        role = s.node(k)["attrs"].get("role", "unknown")
        by_role[role] = by_role.get(role, 0) + 1
    assert by_role == {
        "v1_edge_x": 1,
        "v1_edge_y": 1,
        "salience_center": 1,
        "salience_surround": 1,
    }


def test_edits_to_kernel_weights_are_seen_live_by_next_frame(screen_frame):
    """The weight cache + refresh_kernels are gone because they're
    obsolete: the ChangeDetect Term reads kernel weights via
    ``Attr(k, "weights")`` straight off the graph, so an edit to a
    Kernel node is visible to the very next frame with no refresh
    step. Overwrite sobel_x's weights with zeros; the edge_density
    on the bright stripe must drop sharply (only sobel_y remains)."""
    from substrate_rs import vision as v
    s = srs.Substrate()
    g = RGBEye(substrate=s, n_az=8).build()
    g.stop()
    time.sleep(0.01)
    sx = g.kernels()["sobel_x"]
    before = max(p["edge_density"] for p in
                 g._process_frame(None, screen_frame, 0.0)["percepts"])
    # Zero the x-gradient kernel in place (graph-resident source of truth).
    s.set_attr(sx, "weights", [0.0] * 9)
    after = max(p["edge_density"] for p in
               g._process_frame(None, screen_frame, 0.0)["percepts"])
    assert after < before * 0.5, (
        f"live edit not seen: edge_density {before:.2f} -> {after:.2f}")


def test_grapheye_namespace_isolates_types():
    """Two GraphEyes on the same substrate, one with a namespace, one
    without - their type names don't collide."""
    s = srs.Substrate()
    g1 = RGBEye(substrate=s, namespace="left").build()
    g1.stop()
    g2 = RGBEye(substrate=s, namespace="right").build()
    g2.stop()
    # Both Eyes added 4 kernels each - 8 total, of two types.
    all_kernels = s.nodes("Kernel")  # un-namespaced (g1 went through default)
    left_kernels = s.nodes("left:Kernel")
    right_kernels = s.nodes("right:Kernel")
    # left/right both got 4 namespaced ones.
    assert len(left_kernels) == 4
    assert len(right_kernels) == 4
    # No accidental Kernel nodes outside the namespaces.
    assert len(all_kernels) == 0
