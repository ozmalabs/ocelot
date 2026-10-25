from __future__ import annotations

import numpy as np
from substrate_rs import _native

from scripts.gen_ousiometric_frames_seed import build_seed


def _boot():
    sub = _native.Substrate()
    agent = sub.add_node("Agent", {})
    manifest = build_seed()
    result = sub.load_seed_manifest(manifest, agent)
    assert result["rules_skipped"] == [], result
    return sub, agent, manifest


def _project(sub, agent, frame_id, *, event_id="event-1", coordinates=(0.1, -0.2, 0.3)):
    policy = sub.nodes("OusiometricFramePolicy")[0]
    sub.set_attr(policy, "enabled", 1.0)
    sub.set_attr(policy, "owner_id", "test-agent")
    sub.set_attr(policy, "source_epoch", 4.0)
    sub.set_attr(policy, "model_epoch", 6.0)
    sub.set_attr(policy, "assigned_frame_id", frame_id)
    sub.set_attr(policy, "frame_epoch", 1.0)
    evidence = sub.add_node("OusiometricRawEvidence", {
        "owner_id": "test-agent", "event_id": event_id,
        "source_epoch": 4.0, "model_epoch": 6.0,
        "evidence_status": "observed", "coordinate_encoding": "finite_f64_v1",
        "coordinates": list(coordinates),
    })
    sub.add_edge(agent, "has_ousiometric_raw_evidence", evidence)
    sub.run_rules(1000)
    return evidence


def test_same_raw_evidence_every_frame():
    sub, agent, manifest = _boot()
    evidence = sub.add_node("OusiometricRawEvidence", {
        "owner_id": "test-agent", "event_id": "shared-event",
        "source_epoch": 4.0, "model_epoch": 6.0,
        "evidence_status": "observed", "coordinate_encoding": "finite_f64_v1",
        "coordinates": [0.1, -0.2, 0.3],
    })
    sub.add_edge(agent, "has_ousiometric_raw_evidence", evidence)
    policy = sub.nodes("OusiometricFramePolicy")[0]
    sub.set_attr(policy, "enabled", 1.0)
    sub.set_attr(policy, "owner_id", "test-agent")
    sub.set_attr(policy, "source_epoch", 4.0)
    sub.set_attr(policy, "model_epoch", 6.0)
    sub.set_attr(policy, "frame_epoch", 1.0)
    frames = [node["attrs"]["frame_id"] for node in manifest["nodes"] if node["type"] == "OusiometricFrame"]
    for frame_id in frames:
        sub.set_attr(policy, "assigned_frame_id", frame_id)
        sub.run_rules(1000)
    projections = sub.nodes("OusiometricFrameProjection")
    assert len(projections) == len(frames)
    for projection in projections:
        attrs = sub.node(projection)["attrs"]
        assert attrs["event_id"] == "shared-event"
        assert attrs["owner_id"] == "test-agent"
        assert attrs["source_epoch"] == 4.0 and attrs["model_epoch"] == 6.0
        assert attrs["source_coordinates"] == [0.1, -0.2, 0.3]
        assert sub.neighbours(projection, "retains_source") == [evidence]


def test_frame_inverse_retains_source():
    sub, agent, manifest = _boot()
    for node in manifest["nodes"]:
        if node["type"] != "OusiometricFrame":
            continue
        frame = node["attrs"]
        forward = np.asarray(frame["forward_matrix"], dtype=float)
        inverse = np.asarray(frame["inverse_matrix"], dtype=float)
        assert forward.shape == inverse.shape == (3, 3)
        np.testing.assert_allclose(inverse @ forward, np.eye(3), atol=2e-15, rtol=2e-15)
        evidence = _project(sub, agent, frame["frame_id"], event_id=f"{frame['frame_id']}-event")
        projection = next(p for p in sub.nodes("OusiometricFrameProjection")
                          if sub.node(p)["attrs"]["frame_id"] == frame["frame_id"]
                          and sub.node(p)["attrs"]["event_id"] == f"{frame['frame_id']}-event")
        attrs = sub.node(projection)["attrs"]
        assert attrs["source_coordinates"] == sub.node(evidence)["attrs"]["coordinates"]
        np.testing.assert_allclose(attrs["inverse_matrix"], inverse, atol=2e-15, rtol=2e-15)
        assert sub.neighbours(projection, "retains_source") == [evidence]


def test_equal_total_aperture_budget():
    _sub, _agent, manifest = _boot()
    frames = [node["attrs"] for node in manifest["nodes"] if node["type"] == "OusiometricFrame"]
    full = [frame for frame in frames if frame["precision_bits_per_coordinate"] == 64.0]
    bounded = [frame for frame in frames if frame["precision_bits_per_coordinate"] == 8.0]
    assert len(full) == len(bounded) == 6
    assert {frame["forward_inverse_map_bits"] for frame in full + bounded} == {1152.0}
    assert {frame["metric_policy_bits"] for frame in full + bounded} == {64.0}
    assert {frame["total_representation_bits"] for frame in full} == {1408.0}
    assert {frame["total_representation_bits"] for frame in bounded} == {1240.0}
    assert {frame["coordinates_bits"] for frame in bounded} == {24.0}
    assert {frame["metric_condition"] for frame in frames} == {"fixed_l1", "transported_l1"}


def test_stale_projection_invalidated():
    sub, agent, _manifest = _boot()
    _project(sub, agent, "eq4_rotation_64bit_transported_l1")
    projection = sub.nodes("OusiometricFrameProjection")[0]
    policy = sub.nodes("OusiometricFramePolicy")[0]
    assert sub.node(projection)["attrs"]["status"] == "verified_current"
    sub.set_attr(policy, "frame_epoch", 2.0)
    sub.run_rules(1000)
    attrs = sub.node(projection)["attrs"]
    assert attrs["status"] == "stale"
    assert attrs["stale_reason"] == "frame_epoch_changed"


def test_malformed_and_out_of_range_sources_stay_unknown():
    sub, agent, _manifest = _boot()
    policy = sub.nodes("OusiometricFramePolicy")[0]
    for key, value in (("enabled", 1.0), ("owner_id", "test-agent"),
                       ("source_epoch", 4.0), ("model_epoch", 6.0),
                       ("assigned_frame_id", "shared_basis_64bit_transported_l1"),
                       ("frame_epoch", 1.0)):
        sub.set_attr(policy, key, value)
    vectors = ([0.1, 0.2], [0.1, 0.6, 0.2])
    for i, vector in enumerate(vectors):
        evidence = sub.add_node("OusiometricRawEvidence", {
            "owner_id": "test-agent", "event_id": f"invalid-{i}",
            "source_epoch": 4.0, "model_epoch": 6.0,
            "evidence_status": "observed", "coordinate_encoding": "finite_f64_v1",
            "coordinates": vector,
        })
        sub.add_edge(agent, "has_ousiometric_raw_evidence", evidence)
    sub.run_rules(1000)
    assert sub.nodes("OusiometricFrameProjection") == []


def test_owner_and_source_model_epochs_must_match():
    sub, agent, _manifest = _boot()
    policy = sub.nodes("OusiometricFramePolicy")[0]
    for key, value in (("enabled", 1.0), ("owner_id", "test-agent"),
                       ("source_epoch", 4.0), ("model_epoch", 6.0),
                       ("assigned_frame_id", "shared_basis_64bit_transported_l1"),
                       ("frame_epoch", 1.0)):
        sub.set_attr(policy, key, value)
    evidence = sub.add_node("OusiometricRawEvidence", {
        "owner_id": "other-owner", "event_id": "foreign",
        "source_epoch": 4.0, "model_epoch": 6.0,
        "evidence_status": "observed", "coordinate_encoding": "finite_f64_v1",
        "coordinates": [0.1, 0.2, 0.3],
    })
    sub.add_edge(agent, "has_ousiometric_raw_evidence", evidence)
    sub.run_rules(1000)
    assert sub.nodes("OusiometricFrameProjection") == []


def test_dependency_boot_no_open_grammar():
    sub, _agent, manifest = _boot()
    assert manifest["self_load_only"] is True
    assert manifest["depends_on"] == ["core"]
    policy = sub.node(sub.nodes("OusiometricFramePolicy")[0])["attrs"]
    assert policy["enabled"] == 0.0
    assert sub.nodes("OusiometricFrameProjection") == []
    assert sub.nodes("Grammar") == []
    from substrate.boot_core import CORE_SEEDS
    assert "ousiometric_frames" not in CORE_SEEDS
