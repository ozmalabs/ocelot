"""Vision integration, migrated — the visual cortex runs on the seed-booted
WorldAdapter (no CuriousAgent). The GraphEye's receptive fields are already
graph-resident Kernel nodes (see tests/test_vision_graph_eye.py); this covers
the AGENT-SIDE integration that CuriousAgent._update_vision used to own:

  * lazy build (a world with no vision frame pays nothing)
  * the cortex's kernels are graph-resident Kernel nodes on a vision substrate
    the adapter owns, introspectable via the standard DSL
  * per-azimuth VisionPercept projection nodes on the main substrate
  * salience pop-out mirrored onto the agent root as attention_* attrs

All mechanical I/O over the GraphEye's graph-resident perception. The orienting
DECISION (turn toward attention when salient) is a seeded Term that reads the
attention_* attrs — not in the adapter.

(The CuriousAgent-internal `_PERSIST_EXCLUDE` test and the old-`Eye` deprecation
guard in test_curious_agent_vision_graph / test_vision_graph_eye are about the
CuriousAgent/Eye objects themselves and retire with them; not migrated here.)
"""
from __future__ import annotations

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
    img[:, 35:45] = 255           # bright vertical stripe -> clear pop-out
    return img


# --- lifecycle ----------------------------------------------------------

def test_vision_lazy_no_engagement_no_substrate(wa):
    """No frame -> no cortex, no vision substrate, no kernels."""
    wa.update_vision()
    assert wa._eye is None
    assert wa.vision_substrate() is None
    assert wa.vision_kernels() == {}


def test_vision_built_on_first_frame(wa, screen):
    """First frame builds the photon retina and its receptor populations."""
    wa.update_vision(screen=screen)
    assert wa._eye is not None
    vs = wa.vision_substrate()
    assert vs is not None
    receptors = wa.vision_kernels()
    assert set(receptors) == {"rod", "l", "m", "s"}
    assert all(len(population) == wa._eye.n_az for population in receptors.values())
    for population in receptors.values():
        for nid in population:
            assert vs.node(nid)["type"] == "Photoreceptor"


# --- graph-resident receptor introspection via the DSL ------------------

def test_kernels_introspectable_via_dsl(wa, screen):
    wa.update_vision(screen=screen)
    vs = wa.vision_substrate()
    receptors = wa.vision_kernels()
    l_cone = receptors["l"][0]
    assert vs.evaluate(srs.Attr(srs.Lit(l_cone), "receptor_class")) == "l"
    assert vs.evaluate(srs.Attr(srs.Lit(l_cone), "sensitivity_center_nm")) == 564.0


def test_count_receptors_by_class(wa, screen):
    wa.update_vision(screen=screen)
    vs = wa.vision_substrate()
    by_class = {}
    for receptor in vs.nodes("Photoreceptor"):
        cls = vs.node(receptor)["attrs"]["receptor_class"]
        by_class[cls] = by_class.get(cls, 0) + 1
    assert by_class == {cls: wa._eye.n_az for cls in ("rod", "l", "m", "s")}


def test_inspect_receptor_spectral_and_adaptation_state(wa, screen):
    wa.update_vision(screen=screen)
    receptor = wa.vision_kernels()["m"][0]
    attrs = wa.vision_substrate().node(receptor)["attrs"]
    assert attrs["sensitivity_center_nm"] == 534.0
    assert attrs["bandwidth_nm"] == 36.0
    assert attrs["adaptation"] >= 0.0


# --- preserved behaviour ------------------------------------------------

def test_vision_projection_nodes_match_n_azimuth(wa, screen):
    """N VisionPercept nodes mirror the cortex's per-azimuth output on the main
    substrate, each perceived by the agent."""
    wa.update_vision(screen=screen)
    assert len(wa._vision_projection) == wa._eye.n_az
    for pid in wa._vision_projection:
        assert wa.s.node(pid)["type"] == "VisionPercept"
    # each projection percept is connected to the agent via `perceives`
    perceived = set(wa.inner.neighbours(wa.agent, "perceives"))
    assert set(wa._vision_projection) <= perceived


def test_vision_pipeline_drives_attention(wa, screen):
    """Salience-driven attention: a bright pop-out stripe sets attention_x/y +
    a >0 SNR attention_salience on the agent root. (The cortex runs on its own
    thread, so submit, let it process, submit again, then read.)"""
    wa.update_vision(screen=screen)
    deadline = time.perf_counter() + 1.0
    while wa._eye.processed_count() == 0 and time.perf_counter() < deadline:
        time.sleep(0.005)
    wa.update_vision(screen=screen)
    ar = wa.s.node(wa.agent)["attrs"]
    assert "attention_x" in ar
    assert "attention_y" in ar
    assert float(ar.get("attention_salience", 0.0)) > 0.0
