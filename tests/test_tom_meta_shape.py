"""Regression for TOM_ATTRIBUTED_MENTAL_STATE_META_SHAPE_PREREG.md --
character_tom's nested belief-world and bigville's controllability_for
ToM belief converge on ONE shared, newly-minted MetaShape via the
already-landed sd-loop recognize/mint ladder.
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import CORE_SEEDS
from substrate.world_adapter import WorldAdapter

from domains.tom_meta_shape import (
    register_character_tom_attitude, register_resident_tom_belief,
)
from domains.meta_shape import observe

_EXISTING_META_SHAPES = {
    "feedback_control", "associative_recall", "competitive_inhibition",
    "prediction_minus_observation", "hierarchical_invariance_buildup",
    "global_message_passing", "selective_gating", "delayed_persistence",
    "modular_isolation", "relational_structure_match", "spatial_dynamics",
}


def _fresh():
    return WorldAdapter(seeds=CORE_SEEDS + ("meta_shape_growth",))


def _new_meta_shapes(inner):
    return [inner.node(n)["attrs"] for n in inner.nodes("MetaShape")
            if inner.node(n)["attrs"].get("name") not in _EXISTING_META_SHAPES]


# ---------------------------------------------------------------------
# 1. A character_tom-shaped observation, alone, lands residual.
# ---------------------------------------------------------------------
def test_character_tom_observation_alone_is_residual():
    a = _fresh()
    oid = register_character_tom_attitude(a, belief_holder="sally", flavor="belief")
    assert oid is not None
    attrs = a.inner.node(oid)["attrs"]
    assert attrs["status"] == "residual"
    assert attrs.get("covered_by") is None


# ---------------------------------------------------------------------
# 2/3. The second (bigville) observation mints exactly one new MetaShape
#      and is recognized under it; the first is retroactively recognized
#      under the SAME shape.
# ---------------------------------------------------------------------
def test_second_observation_mints_one_shared_meta_shape_and_both_converge():
    a = _fresh()
    inner = a.inner
    oid_ct = register_character_tom_attitude(a, belief_holder="sally", flavor="belief")
    oid_bv = register_resident_tom_belief(a, target="alex", aspect="agency_attribution")

    new_shapes = _new_meta_shapes(inner)
    assert len(new_shapes) == 1
    shape = new_shapes[0]
    assert shape["support"] == 2
    assert shape["minted"] == 1

    bv_attrs = inner.node(oid_bv)["attrs"]
    assert bv_attrs["status"] == "recognized"
    assert bv_attrs["covered_by"] == shape["name"]

    ct_attrs_after = inner.node(oid_ct)["attrs"]
    assert ct_attrs_after["status"] == "recognized"
    assert ct_attrs_after["covered_by"] == shape["name"]


# ---------------------------------------------------------------------
# 4. An unrelated observation is not pulled into the new shape.
# ---------------------------------------------------------------------
def test_unrelated_observation_stays_residual():
    a = _fresh()
    inner = a.inner
    register_character_tom_attitude(a, belief_holder="sally", flavor="belief")
    register_resident_tom_belief(a, target="alex", aspect="agency_attribution")

    oid_unrelated = observe(a, "Concept", {"name": "quintuple",
                                           "definition": "multiply by five"})
    unrelated_attrs = inner.node(oid_unrelated)["attrs"]
    assert unrelated_attrs["status"] == "residual"
    assert unrelated_attrs.get("covered_by") is None


# ---------------------------------------------------------------------
# 5. Reproducible: the same shape name mints on a fresh agent.
# ---------------------------------------------------------------------
def test_mint_is_reproducible_on_a_fresh_agent():
    a1 = _fresh()
    register_character_tom_attitude(a1, belief_holder="sally", flavor="belief")
    register_resident_tom_belief(a1, target="alex", aspect="agency_attribution")
    name1 = _new_meta_shapes(a1.inner)[0]["name"]

    a2 = _fresh()
    register_character_tom_attitude(a2, belief_holder="wendy", flavor="knowledge")
    register_resident_tom_belief(a2, target="jo", aspect="agency_attribution")
    name2 = _new_meta_shapes(a2.inner)[0]["name"]

    assert name1 == name2


def test_no_prior_seed_was_edited():
    import subprocess
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain",
             "seeds/meta_shape_growth.json", "seeds/shape_vocabulary.json",
             "seeds/character_tom.json"],
            capture_output=True, text=True, timeout=10, cwd=".",
        )
    except Exception:
        pytest.skip("git unavailable")
    assert out.returncode == 0
    assert out.stdout.strip() == "", out.stdout
