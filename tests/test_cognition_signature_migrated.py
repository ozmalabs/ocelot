"""Mechanism tests for typed, versioned native signature descriptors."""
import json

from substrate_rs import _native
from scripts.gen_cognition_signature_seed import OUT, build_seed
from scripts.gen_qualia_shape_mint_seed import build_seed as build_shape_seed


def _boot(enabled=False):
    substrate = _native.Substrate()
    agent = substrate.add_node("Agent", {})
    shape_summary = substrate.load_seed_manifest(build_shape_seed(), agent)
    assert shape_summary.get("rules_skipped") == [], shape_summary
    summary = substrate.load_seed_manifest(build_seed(), agent)
    assert summary.get("rules_skipped") == [], summary
    policy = substrate.nodes("CognitionSignaturePolicy")[0]
    substrate.set_attr(policy, "enabled", 1.0 if enabled else 0.0)
    return substrate, agent


def _enable(s):
    s.set_attr(s.nodes("CognitionSignaturePolicy")[0], "enabled", 1.0)


def _source(s, ag, *, key, source_id, kind, epoch, dimensions, coords, standing=(), live=()):
    source = s.add_node("CognitionSignatureSource", {
        "schema_version": 1, "signature_key": key, "source_id": source_id,
        "source_kind": kind, "source_epoch": epoch, "owner_id": "owner-a",
        "frame_id": "frame-a", "evidence_status": "observed",
        "dimension_ids": list(dimensions), "coordinates": list(coords),
        "standing_coordinates": list(standing), "live_overlay": list(live),
    })
    s.add_edge(ag, "has_signature_source", source)
    return source


def _tick(s):
    for _ in range(20):
        if not s.run_rules(1000):
            break
    else:
        raise AssertionError("signature rules did not reach a fixpoint")


def test_three_source_kinds_are_readable_and_generator_reproduces_seed():
    s, ag = _boot()
    assert json.loads(OUT.read_text()) == build_seed()
    _enable(s)
    _source(s, ag, key="n", source_id="numeric", kind="numeric_shape", epoch=1,
            dimensions=["numeric:shape_rank:2:0"], coords=[("numeric:shape_rank:2:0", "ordinal_rank", 0, False, 0)])
    _source(s, ag, key="q", source_id="qualia", kind="qualia_dimensions", epoch=2,
            dimensions=["qualia:lexical:formal"], coords=[("qualia:lexical:formal", "token", "device", False, 0)])
    _source(s, ag, key="v", source_id="valence", kind="valence", epoch=3,
            dimensions=["observer:valence"], coords=[("observer:valence", "integer", 0, False, 0)])
    _tick(s)
    descriptors = [s.node(n)["attrs"] for n in s.nodes("CognitionSignatureDescriptor")]
    assert {d["source_kind"] for d in descriptors} == {"numeric_shape", "qualia_dimensions", "valence"}
    assert len(descriptors) == 3


def test_signature_projection_is_disabled_until_policy_is_enabled():
    s, ag = _boot(enabled=False)
    _source(s, ag, key="v", source_id="valence", kind="valence", epoch=1,
            dimensions=["observer:valence"], coords=[("observer:valence", "integer", 0, False, 0)])
    _tick(s)
    assert s.nodes("CognitionSignatureDescriptor") == []


def test_dimension_tags_remain_attached_to_values():
    s, ag = _boot()
    _enable(s)
    _source(s, ag, key="formal", source_id="concept-a", kind="qualia_dimensions", epoch=1,
            dimensions=["qualia:lexical:formal"], coords=[("qualia:lexical:formal", "token", "same", False, 0)])
    _source(s, ag, key="telic", source_id="concept-b", kind="qualia_dimensions", epoch=1,
            dimensions=["qualia:lexical:telic"], coords=[("qualia:lexical:telic", "token", "same", False, 0)])
    _tick(s)
    descriptors = [s.node(n)["attrs"] for n in s.nodes("CognitionSignatureDescriptor")]
    assert {tuple(d["dimension_ids"]) for d in descriptors} == {
        ("qualia:lexical:formal",), ("qualia:lexical:telic",)}
    assert len({tuple(d["coordinates"]) for d in descriptors}) == 2


def test_source_epoch_invalidates_old_projection_and_builds_new_one():
    s, ag = _boot()
    _enable(s)
    source = _source(s, ag, key="v", source_id="valence", kind="valence", epoch=1,
                     dimensions=["observer:valence"], coords=[("observer:valence", "integer", 0, False, 0)])
    _tick(s)
    s.set_attr(source, "source_epoch", 2)
    s.set_attr(source, "coordinates", [("observer:valence", "integer", 1, False, 0)])
    _tick(s)
    descriptors = [s.node(n)["attrs"] for n in s.nodes("CognitionSignatureDescriptor")]
    assert sorted((d["source_epoch"], d["status"]) for d in descriptors) == [(1, "stale"), (2, "current")]


def test_live_overlay_is_retained_separately_from_commitment():
    s, ag = _boot()
    _enable(s)
    _source(s, ag, key="concept", source_id="concept", kind="qualia_dimensions", epoch=4,
            dimensions=["dynamical:commitment", "dynamical:pull"],
            coords=[("dynamical:commitment", "finite_number", 0.5, False, 0.25),
                    ("dynamical:pull", "finite_number", None, True, 0.25)],
            standing=[("dynamical:commitment", 0.5)], live=[("dynamical:pull", 0.0)])
    _tick(s)
    desc = s.node(s.nodes("CognitionSignatureDescriptor")[0])["attrs"]
    assert desc["standing_coordinates"] == [("dynamical:commitment", 0.5)]
    assert desc["live_overlay"] == [("dynamical:pull", 0.0)]
    assert desc["coordinates"][0][2:] == (0.5, False, 0.25)
    assert desc["coordinates"][1][2:] == (None, True, 0.25)


def test_measured_observation_signature_is_adapted_by_graph_rules():
    s, ag = _boot(enabled=True)
    obs = s.add_node("Observation", {
        "key": "observation-1", "status": "decoded", "decoded_epoch": 7,
        "frame_id": "frame-a", "signature": [("cell", 1, 2), ("cell", 2, 2)],
    })
    s.add_edge(ag, "observed", obs)
    _tick(s)

    sources = [n for n in s.neighbours(obs, "has_signature_source")
               if s.node(n)["attrs"].get("source_id") == "observation.signature"]
    assert len(sources) == 1
    source = s.node(sources[0])["attrs"]
    assert source["evidence_status"] == "observed"
    assert source["source_epoch"] == 7
    assert source["coordinates"] == [("cell", 1, 2, False, 0), ("cell", 2, 2, False, 0)]
    assert len([n for n in s.nodes("CognitionSignatureDescriptor")
                if s.node(n)["attrs"].get("source_id") == "observation.signature"]) == 1

    _tick(s)
    assert len([n for n in s.neighbours(obs, "has_signature_source")
                if s.node(n)["attrs"].get("source_id") == "observation.signature"]) == 1


def test_verified_numeric_shape_is_adapted_from_real_graph_record():
    s, ag = _boot(enabled=True)
    shape = s.add_node("QualiaShape", {
        "owner_id": "owner-a", "frame_id": "frame-a", "source_epoch": 4,
        "schema_version": 1, "order": 2, "signature": [0, 1, 1, 3, 0, 0, 0, 0],
        "evidence_status": "verified", "reading": "pattern-a", "valence": 2.0,
    })
    evidence = s.add_node("ShapeOutcomeEvidence", {
        "outcome_id": "outcome-1", "evidence_status": "verified", "valence": 2.0,
    })
    s.add_edge(ag, "has_qualia_shape", shape)
    s.add_edge(ag, "has_shape_evidence", evidence)
    s.add_edge(shape, "has_shape_evidence", evidence)
    _tick(s)

    sources = [n for n in s.neighbours(shape, "has_signature_source")
               if s.node(n)["attrs"].get("source_id") == "qualia_shape"]
    assert len(sources) == 1
    source = s.node(sources[0])["attrs"]
    assert source["source_kind"] == "numeric_shape"
    assert source["evidence_status"] == "verified"
    assert source["owner_id"] == "owner-a"
    assert source["frame_id"] == "frame-a"
    assert source["source_epoch"] == 4
    assert source["dimension_ids"] == ("numeric:shape_rank:2",)
    assert source["coordinates"] == (
        ("numeric:shape_rank:2", "sequence_ref", [0, 1, 1, 3, 0, 0, 0, 0], False, 0),)
    valence_sources = [n for n in s.neighbours(shape, "has_signature_source")
                       if s.node(n)["attrs"].get("source_id") == "qualia_shape.valence"]
    assert len(valence_sources) == 1
    valence_source = s.node(valence_sources[0])["attrs"]
    assert valence_source["source_kind"] == "valence"
    assert valence_source["source_epoch"] == 5
    assert valence_source["dimension_ids"] == ("qualia:valence",)
    assert valence_source["coordinates"] == (
        ("qualia:valence", "finite_number", 2.0, False, 0),)
    projected = [n for n in s.neighbours(ag, "has_cognition_signature")
                 if s.neighbours(n, "projects_signature_source") == sources]
    assert len(projected) == 1
    desc = s.node(projected[0])["attrs"]
    assert desc["coordinates"] == source["coordinates"]


def test_verified_shape_observation_is_a_live_query_source():
    s, ag = _boot(enabled=True)
    s.set_attr(s.nodes("QualiaShapeMintPolicy")[0], "enabled", 1.0)
    obs = s.add_node("ShapeObservation", {
        "key": "outcome-query-1", "outcome_status": "verified",
        "outcome_id": "outcome-query-1", "coordinate": [0, 1, 5, 14],
        "order": 2, "owner_id": "owner-a", "frame_id": "frame-a",
        "source_epoch": 4, "valence": 1.0, "reading": "verified-reading",
    })
    s.add_edge(ag, "observed", obs)
    _tick(s)

    shape = s.nodes("QualiaShape")[0]
    stored_source = next(n for n in s.neighbours(shape, "has_signature_source")
                        if s.node(n)["attrs"].get("source_id") == "qualia_shape")
    stored = next(n for n in s.neighbours(ag, "has_cognition_signature")
                  if s.node(n)["attrs"].get("source_id") == "qualia_shape"
                  and s.neighbours(n, "projects_signature_source") == [stored_source])
    query_source = next(n for n in s.neighbours(obs, "has_signature_source")
                        if s.node(n)["attrs"].get("source_id") == "qualia_shape")
    query_descriptor = next(n for n in s.neighbours(ag, "has_cognition_signature")
                            if s.neighbours(n, "projects_signature_source") == [query_source])
    stored_attrs = s.node(stored)["attrs"]
    query_attrs = s.node(query_descriptor)["attrs"]
    assert stored_attrs["source_id"] == query_attrs["source_id"] == "qualia_shape"
    assert stored_attrs["owner_id"] == query_attrs["owner_id"] == "owner-a"
    assert stored_attrs["frame_id"] == query_attrs["frame_id"] == "frame-a"
    assert stored_attrs["source_epoch"] == query_attrs["source_epoch"] == 4
    assert stored_attrs["coordinates"] == query_attrs["coordinates"]


def test_verified_qualia_valence_revision_retires_old_descriptor():
    s, ag = _boot(enabled=True)
    shape = s.add_node("QualiaShape", {
        "owner_id": "owner-a", "frame_id": "frame-a", "source_epoch": 4,
        "schema_version": 1, "order": 2, "signature": [0, 1, 1, 3, 0, 0, 0, 0],
        "evidence_status": "verified", "reading": "pattern-a", "valence": 1.0,
    })
    first = s.add_node("ShapeOutcomeEvidence", {
        "outcome_id": "outcome-1", "evidence_status": "verified", "valence": 1.0,
    })
    s.add_edge(ag, "has_qualia_shape", shape)
    s.add_edge(ag, "has_shape_evidence", first)
    s.add_edge(shape, "has_shape_evidence", first)
    _tick(s)
    s.set_attr(shape, "valence", 0.0)
    second = s.add_node("ShapeOutcomeEvidence", {
        "outcome_id": "outcome-2", "evidence_status": "verified", "valence": -1.0,
    })
    s.add_edge(ag, "has_shape_evidence", second)
    s.add_edge(shape, "has_shape_evidence", second)
    _tick(s)
    descriptors = [s.node(n)["attrs"] for n in s.nodes("CognitionSignatureDescriptor")
                   if s.node(n)["attrs"].get("source_id") == "qualia_shape.valence"]
    assert sorted((d["source_epoch"], d["status"], d["coordinates"][0][2])
                  for d in descriptors) == [(5, "stale", 1.0), (6, "current", 0.0)]
