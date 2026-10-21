"""Mechanism tests for bounded, candidate-only signature recall."""
import json

from substrate_rs import _native
from scripts.gen_similarity_recall_seed import OUT, build_seed
from scripts.gen_qualia_shape_mint_seed import build_seed as build_shape_seed


def _boot():
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    shape = build_shape_seed()
    sig = json.loads((OUT.parent / "cognition_signature.json").read_text())
    recall = build_seed()
    assert s.load_seed_manifest(shape, ag).get("rules_skipped") == []
    assert s.load_seed_manifest(sig, ag).get("rules_skipped") == []
    assert s.load_seed_manifest(recall, ag).get("rules_skipped") == []
    for typ in ("CognitionSignaturePolicy", "SimilarityRecallPolicy"):
        s.set_attr(s.nodes(typ)[0], "enabled", 1.0)
    return s, ag


def _record(s, ag, key, value, *, source="shape", owner="owner", epoch=2, live=True):
    sig = s.add_node("CognitionSignatureDescriptor", {
        "record_key": key, "signature_key": key, "schema_version": "1",
        "owner_id": owner, "source_id": source, "frame_id": "frame",
        "source_epoch": epoch, "live": live, "status": "current",
        "coordinates": [("rank", "ordinal_rank", value, False, 2)],
    })
    s.add_edge(ag, "has_cognition_signature", sig)
    return sig


def _tick(s):
    for _ in range(30):
        if not s.run_rules(1000):
            break
    else:
        raise AssertionError("similarity recall did not reach a fixpoint")


def _attach_executor(s, ag):
    for seed_id in ("thinking_budget", "extended_thinking"):
        manifest = json.loads((OUT.parent / f"{seed_id}.json").read_text())
        loaded = s.load_seed_manifest(manifest, ag)
        assert loaded.get("rules_skipped") == []
    policy = s.nodes("ExtendedThinkingPolicy")[0]
    s.set_attr(policy, "enabled", 1.0)
    mode = s.add_node("NetworkModeState", {"epoch": 1.0, "mode": "awake"})
    s.add_edge(ag, "has_network_mode_state", mode)
    s.set_attr(ag, "codebook_epoch", 0.0)
    budget = s.nodes("ThinkingBudget")[0]
    s.set_attr(budget, "enabled", 1.0)
    s.set_attr(budget, "remaining", 4.0)
    s.set_attr(budget, "refill_per_epoch", 0.0)
    s.set_attr(budget, "last_refill_epoch", 1.0)
    return budget


def _escalation_observation(s, ag, key):
    obs = s.add_node("Observation", {
        "key": key, "status": "decoded", "dim_checked": 1,
        "dim_explained": 0, "gen_explained": 0, "dim_types": ["rank"],
        "et_settled_epoch": -1.0, "decoded_epoch": 2, "frame_id": "frame",
        "signature": [("rank", "ordinal_rank", 5)],
    })
    s.add_edge(ag, "observed", obs)
    return obs


def _query(s, ag, key="q", *, source="shape", owner="owner", epoch=2, value=5):
    obs = s.add_node("Observation", {"key": f"observation:{key}", "status": "decoded"})
    s.add_edge(ag, "observed", obs)
    q = s.add_node("CognitionSignatureQuery", {
        "query_key": key, "schema_version": "1", "owner_id": owner,
        "source_id": source, "frame_id": "frame", "source_epoch": epoch,
        "live": True, "coordinates": [("rank", "ordinal_rank", value, False, 2)],
        "observation_key": f"observation:{key}",
        "k": 3, "candidate_cap": 100, "status": "ready",
    })
    s.add_edge(ag, "has_similarity_query", q)
    s.add_edge(q, "projects_observation", obs)
    return q


def _query_source(s, ag, key="q-source", *, source="shape", owner="owner", epoch=2, value=5):
    obs = s.add_node("Observation", {
        "key": f"observation:{key}", "status": "decoded", "decoded_epoch": epoch,
        "frame_id": "frame", "signature": [("rank", "ordinal_rank", value)],
    })
    s.add_edge(ag, "observed", obs)
    return obs


def _observation_record(s, ag, key, signature, *, epoch=2, frame="frame"):
    sig = s.add_node("CognitionSignatureDescriptor", {
        "record_key": key, "signature_key": key, "schema_version": "1",
        "owner_id": "agent-root", "source_id": "observation.signature",
        "frame_id": frame, "source_epoch": epoch, "live": True,
        "status": "current", "coordinates": [tuple(item) + (False, 0) for item in signature],
    })
    s.add_edge(ag, "has_cognition_signature", sig)
    return sig


def test_dependency_closure_and_generator_reproduction():
    assert json.loads(OUT.read_text()) == build_seed()
    s, _ = _boot()
    assert s.nodes("SimilarityRecallPolicy")


def test_candidate_cannot_be_adopted_without_verification_requirement():
    rules = {rule["name"]: rule for rule in build_seed()["rules"]}

    def mentions(value, key):
        if isinstance(value, dict):
            return value.get("key") == key or any(mentions(v, key) for v in value.values())
        if isinstance(value, list):
            return any(mentions(v, key) for v in value)
        return False

    for name in ("sr_mint_receipt_from_verified_shape_outcome",
                 "sr_verify_unique_exact_signature_hit"):
        assert mentions(rules[name]["where"], "requires_verification")
    assert mentions(rules["sr_request_funded_ladder_fallback_on_unverified_miss"]["where"],
                    "requires_verification")
    recall = rules["sr_publish_bounded_candidate_recall"]
    serialized = json.dumps(recall["effects"])
    assert '"requires_verification": true' in serialized
    assert "funding_required_before_adoption" not in serialized


def test_observed_signature_source_projects_from_actual_observation():
    s, ag = _boot()
    obs = _query_source(s, ag)
    _observation_record(s, ag, "exact", s.node(obs)["attrs"]["signature"])
    _tick(s)
    source = s.neighbours(obs, "has_signature_source")[0]
    source_attrs = s.node(source)["attrs"]
    assert source_attrs["source_id"] == "observation.signature"
    assert source_attrs["evidence_status"] == "observed"
    assert source_attrs["source_epoch"] == 2
    assert source_attrs["coordinates"] == [("rank", "ordinal_rank", 5, False, 0)]
    projected = [n for n in s.neighbours(ag, "has_cognition_signature")
                 if s.neighbours(n, "projects_signature_source") == [source]]
    assert len(projected) == 1
    assert len(s.nodes("CognitionSignatureQuery")) == 1
    assert s.neighbours(s.nodes("CognitionSignatureQuery")[0], "projects_observation") == [obs]
    assert s.node(s.nodes("SimilarityRecallResult")[0])["attrs"]["status"] == "fallback_required"
    assert s.node(obs)["attrs"].get("dim_explained") != 1


def test_returns_sorted_candidate_only_results_with_no_adoption():
    s, ag = _boot()
    _record(s, ag, "far", 7)
    _record(s, ag, "near", 6)
    _record(s, ag, "exact", 5)
    q = _query(s, ag)
    obs = s.neighbours(q, "projects_observation")[0]
    receipt = s.add_node("CognitionSignatureVerificationReceipt", {
        "status": "verified", "record_key": "exact",
        "observation_key": "observation:q", "source_epoch": 2,
    })
    s.add_edge(obs, "has_signature_verification_receipt", receipt)
    exact_sig = next(n for n in s.nodes("CognitionSignatureDescriptor")
                     if s.node(n)["attrs"]["record_key"] == "exact")
    s.add_edge(receipt, "verifies_signature", exact_sig)
    _tick(s)
    out = s.node(s.nodes("SimilarityRecallResult")[0])["attrs"]
    candidates, checked, complete = out["candidate_scan"]
    assert [row[0] for row in candidates] == ["exact", "near", "far"]
    assert checked == 3 and complete is True
    assert out["status"] == "accepted_verified_exact"
    assert out["requires_verification"] is True
    assert len(s.neighbours(s.nodes("SimilarityRecallResult")[0], "verified_signature")) == 1
    assert s.node(obs)["attrs"]["dim_explained"] == 1
    assert s.node(obs)["attrs"]["status"] == "recognized_duplicate"
    assert s.nodes("GroundedReading") == []
    assert s.nodes("FundedOperationRequest") == []


def test_exact_tie_stays_unresolved():
    s, ag = _boot()
    _record(s, ag, "a", 5)
    _record(s, ag, "b", 5)
    _query(s, ag)
    _tick(s)
    result = s.nodes("SimilarityRecallResult")[0]
    assert s.node(result)["attrs"]["status"] == "fallback_required"
    assert s.neighbours(result, "verified_signature") == []
    assert len(s.nodes("SimilarityRecallFallback")) == 1


def test_nearest_nonexact_candidate_falls_back():
    s, ag = _boot()
    _record(s, ag, "near", 6)
    _query(s, ag, value=5)
    _tick(s)
    result = s.nodes("SimilarityRecallResult")[0]
    assert s.node(result)["attrs"]["status"] == "fallback_required"
    assert len(s.nodes("SimilarityRecallFallback")) == 1


def test_stale_hit_falls_back():
    s, ag = _boot()
    _record(s, ag, "stale", 5, live=False)
    _query(s, ag)
    _tick(s)
    result = s.nodes("SimilarityRecallResult")[0]
    fallback = s.nodes("SimilarityRecallFallback")
    assert s.node(result)["attrs"]["status"] == "fallback_required"
    assert len(fallback) == 1
    assert s.node(fallback[0])["attrs"]["funding_required"] is True
    assert s.nodes("FundedOperationRequest") == []


def test_exact_signature_without_verifier_receipt_falls_back():
    s, ag = _boot()
    obs = _query_source(s, ag, key="no-receipt")
    _observation_record(s, ag, "same-signature", s.node(obs)["attrs"]["signature"])
    _tick(s)
    result = s.nodes("SimilarityRecallResult")[0]
    assert s.node(result)["attrs"]["status"] == "fallback_required"
    assert s.node(obs)["attrs"].get("dim_explained") != 1
    assert s.nodes("GroundedReading") == []


def test_no_unfunded_generation():
    s, ag = _boot()
    budget = _attach_executor(s, ag)
    s.set_attr(budget, "remaining", 0.0)
    obs = _escalation_observation(s, ag, "unfunded-observation")
    _observation_record(s, ag, "same-signature", s.node(obs)["attrs"]["signature"])

    _tick(s)

    assert len(s.neighbours(obs, "has_similarity_recall_fallback")) == 1
    assert s.node(obs)["attrs"].get("dim_explained") != 1
    request = s.nodes("ExtendedThinkingStepRequest")[0]
    assert s.node(request)["attrs"]["status"] == "denied"
    assert s.node(budget)["attrs"]["remaining"] == 0.0


def test_recall_fallback_opens_the_existing_funded_ladder():
    s, ag = _boot()
    _attach_executor(s, ag)
    obs = _escalation_observation(s, ag, "fallback-observation")
    _observation_record(s, ag, "same-signature", s.node(obs)["attrs"]["signature"])

    _tick(s)

    assert len(s.neighbours(obs, "has_similarity_recall_fallback")) == 1
    assert len(s.neighbours(obs, "has_extended_thinking_episode")) == 1
    fallback = s.neighbours(obs, "has_similarity_recall_fallback")[0]
    assert s.node(fallback)["attrs"]["status"] == "funded_ladder_opened"
    assert s.neighbours(fallback, "hands_off_to_episode") == s.neighbours(
        obs, "has_extended_thinking_episode")
    requests = s.nodes("ExtendedThinkingStepRequest")
    assert len(requests) == 1
    assert s.node(requests[0])["attrs"]["status"] in {"approved", "consumed"}
    assert s.node(requests[0])["attrs"]["debited_epoch"] == 1.0


def test_hit_reverified_before_acceptance():
    s, ag = _boot()
    _attach_executor(s, ag)
    obs = _escalation_observation(s, ag, "verified-observation")
    sig = _observation_record(s, ag, "verified-record", s.node(obs)["attrs"]["signature"])
    receipt = s.add_node("CognitionSignatureVerificationReceipt", {
        "status": "verified", "record_key": "verified-record",
        "observation_key": json.dumps("verified-observation"), "source_epoch": 2,
    })
    s.add_edge(obs, "has_signature_verification_receipt", receipt)
    s.add_edge(receipt, "verifies_signature", sig)

    _tick(s)

    result = s.nodes("SimilarityRecallResult")[0]
    assert s.node(result)["attrs"]["status"] == "accepted_verified_exact"
    assert s.node(obs)["attrs"]["dim_explained"] == 1
    assert s.node(obs)["attrs"]["status"] == "recognized_duplicate"
    assert s.neighbours(obs, "has_extended_thinking_episode") == []
    assert s.nodes("ExtendedThinkingStepRequest") == []


def test_verified_shape_outcome_mints_live_exact_recall_receipt():
    s, ag = _boot()
    obs = s.add_node("ShapeObservation", {
        "key": "observed-shape-outcome", "outcome_status": "verified",
        "outcome_id": "external-verifier-42", "coordinate": [0, 1, 5, 14],
        "order": 2, "owner_id": "owner-a", "frame_id": "frame",
        "source_epoch": 2, "valence": 1.0, "reading": "verified-pattern",
    })
    s.add_edge(ag, "observed", obs)
    s.set_attr(s.nodes("QualiaShapeMintPolicy")[0], "enabled", 1.0)
    signature = [0, 1, 0, 0, 0, 0, 0, 0]
    sig = s.add_node("CognitionSignatureDescriptor", {
        "record_key": "stored-shape", "signature_key": "stored-shape",
        "schema_version": "1", "owner_id": "owner-a", "source_id": "qualia_shape",
        "frame_id": "frame", "source_epoch": 2, "live": True, "status": "current",
        "coordinates": [("numeric:shape_rank:2", "sequence_ref", signature, False, 0)],
    })
    s.add_edge(ag, "has_cognition_signature", sig)

    _tick(s)

    result = s.nodes("SimilarityRecallResult")[0]
    attrs = s.node(result)["attrs"]
    assert attrs["status"] == "accepted_verified_exact"
    receipts = s.neighbours(obs, "has_signature_verification_receipt")
    assert len(receipts) == 1
    receipt = s.node(receipts[0])["attrs"]
    assert receipt["verifier_kind"] == "verified_shape_outcome"
    assert receipt["verifier_evidence_id"] == "external-verifier-42"
    verified = s.neighbours(receipts[0], "verifies_signature")[0]
    assert receipt["record_key"] == s.node(verified)["attrs"]["record_key"]
    query = s.neighbours(s.nodes("CognitionSignatureQuery")[0], "projects_query_source")
    assert s.node(verified)["attrs"]["coordinates"] == s.node(query[0])["attrs"]["coordinates"]
    assert s.node(obs)["attrs"]["status"] == "recognized_duplicate"


def test_incompatible_owner_is_hidden():
    s, ag = _boot()
    _record(s, ag, "ok", 5)
    _record(s, ag, "other-owner", 5, owner="other")
    _record(s, ag, "other-source", 5, source="other")
    _record(s, ag, "old-epoch", 5, epoch=1)
    _query(s, ag)
    _tick(s)
    candidates = s.node(s.nodes("SimilarityRecallResult")[0])["attrs"]["candidate_scan"][0]
    assert [row[0] for row in candidates] == ["ok"]


def test_cap_hit_is_explicitly_incomplete():
    s, ag = _boot()
    for ix in range(3):
        _record(s, ag, f"r{ix}", 5)
    s.set_attr(s.nodes("SimilarityRecallPolicy")[0], "candidate_cap", 2)
    _query(s, ag)
    _tick(s)
    _, checked, complete = s.node(s.nodes("SimilarityRecallResult")[0])["attrs"]["candidate_scan"]
    assert checked == 2 and complete is False


def test_disabled_policy_does_not_publish_recall():
    s, ag = _boot()
    s.set_attr(s.nodes("SimilarityRecallPolicy")[0], "enabled", 0.0)
    _record(s, ag, "r", 5)
    _query(s, ag)
    _tick(s)
    assert s.nodes("SimilarityRecallResult") == []
