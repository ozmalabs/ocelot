"""P18 contract checks for models induced from observations and receipts."""
import json
from pathlib import Path

from substrate_rs import _native
from scripts.gen_process_induction_seed import build_seed
from evaluation.process_mastery.observed_worlds import ObservedWorld

ROOT = Path(__file__).resolve().parents[1]


def _boot(enabled=True):
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    for name in ("default_mode_core", "thinking_budget", "cognition_signature",
                 "experience_signature", "process_schema"):
        s.load_seed_manifest(json.loads((ROOT / "seeds" / f"{name}.json").read_text()), ag)
    result = s.load_seed_manifest(build_seed(), ag)
    assert result["rules_skipped"] == [], result
    for budget in s.nodes("ThinkingBudget"):
        for key, value in {"enabled": 1.0, "remaining": 100.0,
                           "last_refill_epoch": 10.0}.items():
            s.set_attr(budget, key, value)
    s.set_attr(s.nodes("NetworkModeState")[0], "epoch", 10.0)
    s.set_attr(s.nodes("ModelLearningPolicy")[0], "enabled", float(enabled))
    s.set_attr(s.nodes("ProcessSchemaPolicy")[0], "view_enabled", 1.0)
    return s, ag


def _tick(s):
    for _ in range(40):
        if not s.run_rules(4000):
            return
    raise AssertionError("observed model rules did not reach a fixpoint")


def _ingest(s, ag, *, i, object_id, before, after):
    event = f"event-{i}"
    attrs = {"owner_id": "owner-a", "episode_id": f"episode-{i}",
        "event_id": event, "object_id": object_id, "object_type": "Object",
        "action_kind": "heat", "feature_key": "surface", "before_value": before,
        "after_value": after, "source_epoch": 3, "model_epoch": 2,
        "frame_epoch": 5, "status": "observed"}
    obs = s.add_node("TransitionObservation", attrs)
    action = s.add_node("TransitionActionReceipt", {**{k: attrs[k] for k in
        ("owner_id", "episode_id", "event_id", "source_epoch", "model_epoch", "frame_epoch")},
        "status": "observed", "action_id": "heat"})
    outcome = s.add_node("TransitionOutcomeReceipt", {**{k: attrs[k] for k in
        ("owner_id", "episode_id", "event_id", "source_epoch", "model_epoch", "frame_epoch")},
        "status": "observed", "observed_value": after})
    s.add_edge(ag, "has_transition_observation", obs)
    s.add_edge(obs, "has_action_receipt", action)
    s.add_edge(obs, "has_outcome_receipt", outcome)
    return obs


def test_no_candidate_hypotheses_ingested_and_held_vocabulary_is_fixed():
    s, ag = _boot()
    assert not s.nodes("ProcessInductionHypothesis")
    _ingest(s, ag, i=1, object_id="o1", before="rough", after="warm")
    _ingest(s, ag, i=2, object_id="o2", before="rough", after="warm")
    _tick(s)
    assert len(s.nodes("ProcessInductionHypothesis")) == 1
    assert not any(s.node(n)["attrs"].get("answer_feature") for n in s.nodes())


def test_ambiguous_model_stays_as_an_evidence_bound_portfolio():
    s, ag = _boot()
    for i, outcome in enumerate(("warm", "cold"), 1):
        _ingest(s, ag, i=i, object_id=f"o{i}", before="rough", after=outcome)
    _ingest(s, ag, i=3, object_id="o3", before="rough", after="warm")
    _ingest(s, ag, i=4, object_id="o4", before="rough", after="cold")
    _tick(s)
    candidates = s.nodes("ProcessInductionHypothesis")
    assert {s.node(n)["attrs"]["after_value"] for n in candidates} == {"warm", "cold"}
    assert all(s.node(n)["attrs"]["status"] == "disputed" for n in candidates)
    assert all(s.neighbours(n, "has_counterexample") for n in candidates)


def test_unknown_and_stale_model_requests_abstain():
    s, ag = _boot()
    _ingest(s, ag, i=1, object_id="o1", before="rough", after="warm")
    _ingest(s, ag, i=2, object_id="o2", before="rough", after="warm")
    _tick(s)
    query = s.add_node("ProcessPredictionQuery", {"query_id": "stale", "owner_id": "owner-a",
        "object_id": "o3", "object_type": "Object", "action_kind": "heat",
        "feature_key": "surface", "before_value": "rough", "source_epoch": 3,
        "model_epoch": 99, "frame_epoch": 5, "status": "pending"})
    s.add_edge(ag, "has_process_prediction_query", query)
    _tick(s)
    assert not s.nodes("ProcessPrediction")


def test_actual_world_receipt_refines_prediction_for_unseen_object():
    world = ObservedWorld.create("object_mechanism", 44)
    s, ag = _boot()
    observed = []
    # These actions are executed by the world. The learner receives only the
    # public features and signed consequence fields from the returned receipt.
    for i, object_id in enumerate(("object-0", "object-2"), 1):
        before = world.observe(object_id)
        receipt = world.execute(before, "heat")
        assert world.verify_receipt(receipt)
        assert "_mechanism" not in before and "hidden_truth" not in before
        obs = _ingest(s, ag, i=i, object_id=object_id,
                      before=before["features"]["surface"],
                      after=receipt["observed_state"])
        observed.append((before, receipt, obs))
        _tick(s)

    models = s.nodes("TransitionHypothesis")
    assert len(models) == 1
    model = s.node(models[0])["attrs"]
    assert model["status"] == "candidate"
    assert len(s.neighbours(models[0], "has_model_receipt")) == 1

    fresh = world.observe("object-4")
    query = s.add_node("ProcessPredictionQuery", {"query_id": "fresh-object",
        "owner_id": "owner-a", "object_id": "object-4", "object_type": "Object",
        "action_kind": "heat", "feature_key": "surface",
        "before_value": fresh["features"]["surface"], "source_epoch": 3,
        "model_epoch": 2, "frame_epoch": 5, "status": "pending"})
    s.add_edge(ag, "has_process_prediction_query", query)
    _tick(s)
    prediction = s.nodes("ProcessPrediction")
    assert len(prediction) == 1
    predicted = s.node(prediction[0])["attrs"]["expected_after_value"]

    actual = world.execute(fresh, "heat")
    assert world.verify_receipt(actual)
    _ingest(s, ag, i=3, object_id="object-4",
            before=fresh["features"]["surface"], after=actual["observed_state"])
    _tick(s)
    learned = s.nodes("ProcessInductionHypothesis")[0]
    if actual["observed_state"] == predicted:
        assert s.node(learned)["attrs"]["support_count"] == 3.0
        assert any(s.node(n)["attrs"].get("event_id") == "event-3"
                   for n in s.neighbours(learned, "supported_by_transition"))
    else:
        assert s.node(learned)["attrs"]["status"] == "disputed"
        assert any(s.node(n)["attrs"].get("event_id") == "event-3"
                   for n in s.neighbours(learned, "has_counterexample"))
        assert s.node(models[0])["attrs"]["status"] == "disputed"


def test_counterexample_retires_transition_view_and_receipt():
    s, ag = _boot()
    _ingest(s, ag, i=1, object_id="o1", before="rough", after="warm")
    _ingest(s, ag, i=2, object_id="o2", before="rough", after="warm")
    _tick(s)
    model = s.nodes("TransitionHypothesis")[0]
    _ingest(s, ag, i=3, object_id="o3", before="rough", after="cold")
    _tick(s)
    assert s.node(model)["attrs"]["status"] == "disputed"
    receipt = s.neighbours(model, "has_model_receipt")[0]
    assert s.node(receipt)["attrs"]["status"] == "disputed_by_counterexample"
