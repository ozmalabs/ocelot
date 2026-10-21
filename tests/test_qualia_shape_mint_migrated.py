"""Development fixtures for the versioned native Shape signature contract."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
import json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests" / "capability" / "number_qualia" / "runners"))

from substrate_rs import _native
from number_runner import SHAPE_SIG_WIDTH, aperture_signature
from scripts.gen_qualia_shape_mint_seed import OUT, build_seed


def _legacy(coord, order):
    return aperture_signature(coord, order, SimpleNamespace(shape_signature=_native.Substrate.shape_signature))


def test_legacy_signature_parity():
    coord = [0, 1, 5, 14]
    assert _legacy(coord, 0) == [0, 1, 2, 3, 0, 0, 0, 0]
    assert _legacy(coord, 1) == [0, 1, 2, 0, 0, 0, 0, 0]
    assert _legacy(coord, 2) == [0, 1, 0, 0, 0, 0, 0, 0]
    assert _legacy(coord, 3) == [2, 0, 0, 0, 0, 0, 0, 0]


def test_empty_and_zero_order_semantics():
    assert _legacy([], 0) == [0] * SHAPE_SIG_WIDTH
    assert _legacy([3.5], 0) == [3, 0, 0, 0, 0, 0, 0, 0]


def _boot():
    substrate = _native.Substrate()
    agent = substrate.add_node("Agent", {})
    summary = substrate.load_seed_manifest(build_seed(), agent)
    assert summary.get("rules_skipped") == [], summary
    return substrate, agent


def _observe(substrate, agent, outcome_id, valence, reading):
    observation = substrate.add_node("ShapeObservation", {
        "outcome_status": "verified", "outcome_id": outcome_id,
        "coordinate": [0, 1, 5, 14], "order": 2, "owner_id": "owner-a",
        "frame_id": "frame-1", "source_epoch": 4, "valence": valence,
        "reading": reading,
    })
    substrate.add_edge(agent, "observed", observation)
    return observation


def _enable(substrate, agent):
    policy = substrate.nodes("QualiaShapeMintPolicy")[0]
    substrate.set_attr(policy, "enabled", 1.0)
    substrate.run_rules(1000)


def test_dependency_closure_loads_and_generator_reproduces_seed():
    substrate, _ = _boot()
    assert substrate.nodes("QualiaShapeMintPolicy")
    assert json.loads(OUT.read_text()) == build_seed()


def test_repeated_outcome_is_idempotent_and_negative_cannot_ground_reading():
    substrate, agent = _boot()
    _enable(substrate, agent)
    _observe(substrate, agent, "outcome-positive", 1.0, "verified-reading")
    substrate.run_rules(1000)
    assert len(substrate.nodes("QualiaShape")) == 1
    shape = substrate.node(substrate.nodes("QualiaShape")[0])["attrs"]
    assert shape["reading"] == "verified-reading"
    assert len(substrate.nodes("ShapeOutcomeEvidence")) == 1

    substrate.run_rules(1000)
    assert len(substrate.nodes("ShapeOutcomeEvidence")) == 1
    _observe(substrate, agent, "outcome-negative", -1.0, "unverified-reading")
    substrate.run_rules(1000)
    assert len(substrate.nodes("QualiaShape")) == 1
    shape = substrate.node(substrate.nodes("QualiaShape")[0])["attrs"]
    assert shape["valence"] == 0.0
    assert shape["reading"] == "verified-reading"
    negative = [substrate.node(n)["attrs"] for n in substrate.nodes("ShapeOutcomeEvidence")
                if substrate.node(n)["attrs"]["outcome_id"] == "outcome-negative"][0]
    assert negative["reading"] is None


def test_ambiguous_shape_match_does_not_overwrite_either_candidate():
    substrate, agent = _boot()
    _enable(substrate, agent)
    _observe(substrate, agent, "first", 1.0, "first-reading")
    substrate.run_rules(1000)
    original = substrate.node(substrate.nodes("QualiaShape")[0])["attrs"].copy()
    duplicate = substrate.add_node("QualiaShape", dict(original, reading="second-reading"))
    substrate.add_edge(agent, "has_qualia_shape", duplicate)
    _observe(substrate, agent, "ambiguous-negative", -1.0, "should-not-ground")
    substrate.run_rules(1000)
    shapes = [substrate.node(n)["attrs"] for n in substrate.nodes("QualiaShape")]
    assert len(shapes) == 2
    assert all(s["valence"] == 1.0 for s in shapes)
    assert {s["reading"] for s in shapes} == {"first-reading", "second-reading"}


def test_negative_only_outcome_creates_unreadable_anti_shape():
    substrate, agent = _boot()
    _enable(substrate, agent)
    _observe(substrate, agent, "negative-only", -1.0, "must-not-ground")
    substrate.run_rules(1000)
    shape = substrate.node(substrate.nodes("QualiaShape")[0])["attrs"]
    evidence = substrate.node(substrate.nodes("ShapeOutcomeEvidence")[0])["attrs"]
    assert shape["valence"] == -1.0
    assert shape["reading"] is None
    assert evidence["reading"] is None
    assert shape["evidence_status"] == "verified"
