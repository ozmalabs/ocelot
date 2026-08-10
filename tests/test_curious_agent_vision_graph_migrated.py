"""CuriousAgent vision graph integration — migrated twin.

Covers every test in test_curious_agent_vision_graph.py on the
seed-booted WorldAdapter (no CuriousAgent).

Coverage map (original -> migrated):

  test_vision_lazy_no_engagement_no_substrate
      -> test_vision_lazy_no_engagement_no_substrate
         (WorldAdapter with no frame: _eye is None, vision_substrate()
         is None, vision_kernels() is {})

  test_vision_built_on_first_frame
      -> test_vision_built_on_first_frame
         (update_vision(screen=...) builds the cortex; Kernel nodes
         appear on the vision substrate)

  test_agent_can_introspect_receptive_fields_via_dsl
      -> test_agent_can_introspect_receptive_fields_via_dsl
         (sobel_x role == "v1_edge_x", name == "sobel:dx=1,dy=0,k=3",
         gauss_center role == "salience_center"; all via vs.evaluate)

  test_agent_can_count_its_visual_kernels_by_role
      -> test_agent_can_count_its_visual_kernels_by_role
         (walk Kernel nodes; filter on role; four distinct roles)

  test_agent_can_inspect_receptive_field_weights
      -> test_agent_can_inspect_receptive_field_weights
         (kernel_to_array on sobel_x == classic 3x3 Sobel matrix)

  test_existing_vision_pipeline_still_drives_attention
      -> test_existing_vision_pipeline_still_drives_attention
         (bright stripe frame -> attention_x/attention_y/
         attention_salience > 0 on agent root)

  test_vision_projection_nodes_match_n_azimuth
      -> test_vision_projection_nodes_match_n_azimuth
         (len(_vision_projection) == _eye.n_az; all VisionPercept nodes)

  test_vision_substrate_excluded_from_persistence
      -> test_vision_substrate_excluded_from_persistence
         (The CuriousAgent._PERSIST_EXCLUDE class-level frozenset is
         specific to the Python CuriousAgent class and retires with it.
         The equivalent WorldAdapter guarantee is structural: save() does
         NOT serialise _eye or _vision_substrate -- this test confirms
         that a round-tripped WorldAdapter starts with _eye is None and
         vision_substrate() is None, i.e. the cortex is rebuilt fresh on
         load rather than being persisted.)
"""
from __future__ import annotations

import json
import os
import tempfile
import time

import numpy as np
import pytest


srs = pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter


@pytest.fixture
def wa():
    a = WorldAdapter()
    yield a
    if a._eye is not None:
        a._eye.stop()


@pytest.fixture
def screen():
    rng = np.random.RandomState(13)
    img = rng.randint(40, 80, size=(40, 80, 3), dtype=np.uint8)
    img[:, 35:45] = 255
    return img


# --- Lifecycle ----------------------------------------------------------


def test_vision_lazy_no_engagement_no_substrate(wa):
    """No vision frame -> no cortex built, no vision substrate.
    The agent that never sees pays nothing.
    Original: test_vision_lazy_no_engagement_no_substrate"""
    wa.update_vision()
    assert wa._eye is None
    assert wa._vision_substrate is None
    assert wa.vision_kernels() == {}
    assert wa.vision_substrate() is None


def test_vision_built_on_first_frame(wa, screen):
    """Engagement: as soon as update_vision receives a screen, the cortex
    builds its adapting rod/cone populations on the vision substrate.
    Original: test_vision_built_on_first_frame"""
    wa.update_vision(screen=screen)
    assert wa._eye is not None
    vs = wa.vision_substrate()
    assert vs is not None
    receptors = wa.vision_kernels()
    assert set(receptors) == {"rod", "l", "m", "s"}
    for population in receptors.values():
        assert len(population) == wa._eye.n_az
        assert all(vs.node(nid)["type"] == "Photoreceptor" for nid in population)


# --- Graph-resident photoreceptor introspection -------------------------


def test_agent_can_introspect_receptive_fields_via_dsl(wa, screen):
    """The whole point of the migration: the agent's perceptual primitives
    are graph data, queryable via the standard DSL (Attr(Lit(nid), key)) --
    same path the agent uses for any other node.
    Original: test_agent_can_introspect_receptive_fields_via_dsl"""
    wa.update_vision(screen=screen)
    vs = wa.vision_substrate()
    receptor = wa.vision_kernels()["l"][0]
    assert vs.evaluate(
        srs.Attr(srs.Lit(receptor), "receptor_class")) == "l"
    assert vs.evaluate(
        srs.Attr(srs.Lit(receptor), "sensitivity_center_nm")) == 564.0


def test_agent_can_count_its_visual_receptors_by_class(wa, screen):
    """Same pattern the agent uses to count any other graph-resident set --
    walk Kernel nodes, filter on role.
    Original: test_agent_can_count_its_visual_kernels_by_role"""
    wa.update_vision(screen=screen)
    vs = wa.vision_substrate()
    by_class = {}
    for receptor in vs.nodes("Photoreceptor"):
        cls = vs.node(receptor)["attrs"]["receptor_class"]
        by_class[cls] = by_class.get(cls, 0) + 1
    assert by_class == {cls: wa._eye.n_az for cls in ("rod", "l", "m", "s")}


def test_agent_can_inspect_receptor_spectral_state(wa, screen):
    """Spectral sensitivity and adaptation are graph state.
    Original: test_agent_can_inspect_receptive_field_weights"""
    wa.update_vision(screen=screen)
    receptor = wa.vision_kernels()["s"][0]
    attrs = wa.vision_substrate().node(receptor)["attrs"]
    assert attrs["sensitivity_center_nm"] == 420.0
    assert attrs["adaptation"] >= 0.0


# --- Preserved behaviour ------------------------------------------------


def test_existing_vision_pipeline_still_drives_attention(wa, screen):
    """Salience-driven attention: a frame with a bright stripe should set
    attention_x / attention_y on the agent root. Two engages so the cortex
    has time to process before we read.
    Original: test_existing_vision_pipeline_still_drives_attention"""
    wa.update_vision(screen=screen)
    deadline = time.perf_counter() + 1.0
    while wa._eye.processed_count() == 0 and time.perf_counter() < deadline:
        time.sleep(0.005)
    wa.update_vision(screen=screen)
    ar = wa.s.node(wa.agent)["attrs"]
    assert "attention_x" in ar
    assert "attention_y" in ar
    assert float(ar.get("attention_salience", 0.0)) > 0.0


def test_vision_projection_nodes_match_n_azimuth(wa, screen):
    """N VisionPercept nodes mirror the cortex's per-azimuth output in the
    main substrate -- unchanged from the pre-migration layout.
    Original: test_vision_projection_nodes_match_n_azimuth"""
    wa.update_vision(screen=screen)
    assert len(wa._vision_projection) == wa._eye.n_az
    for pid in wa._vision_projection:
        assert wa.s.node(pid)["type"] == "VisionPercept"


# --- Persist exclusion ------------------------------------------------


def test_vision_substrate_excluded_from_persistence(wa, screen):
    """The CuriousAgent._PERSIST_EXCLUDE class-level frozenset is specific to
    the Python CuriousAgent class and retires with it. The equivalent WorldAdapter
    guarantee is structural: save() does NOT serialise _eye or _vision_substrate,
    so a loaded WorldAdapter starts with _eye is None and vision_substrate() is
    None -- the cortex is rebuilt fresh on load.
    Original: test_vision_substrate_excluded_from_persistence"""
    # Build the cortex so there IS a _vision_substrate + _eye to (not) persist.
    wa.update_vision(screen=screen)
    assert wa._eye is not None
    assert wa.vision_substrate() is not None

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        wa.save(path)
        # The saved blob must NOT contain any vision substrate data.
        with open(path) as f:
            blob = json.load(f)
        assert "_eye" not in blob
        assert "_vision_substrate" not in blob
        # A loaded WorldAdapter starts with no cortex -- rebuilt on demand.
        wa2 = WorldAdapter.load(path)
        assert wa2._eye is None
        assert wa2.vision_substrate() is None
        assert wa2.vision_kernels() == {}
    finally:
        os.unlink(path)
        if wa._eye is not None:
            wa._eye.stop()
