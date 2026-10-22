"""End-to-end native model disagreement, probe, receipt and revision tests."""
import json
from pathlib import Path

from substrate_rs import _native
from evaluation.process_mastery.observed_worlds import ObservedWorld
from scripts.gen_process_induction_seed import build_seed as process_seed
from scripts.gen_experiment_design_seed import build_seed as experiment_seed

ROOT = Path(__file__).resolve().parents[1]


def _boot():
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    for name in ("default_mode_core", "thinking_budget", "cognition_signature",
                 "experience_signature", "cognition_manifold"):
        s.load_seed_manifest(json.loads((ROOT / "seeds" / f"{name}.json").read_text()), ag)
    for manifest in (process_seed(), experiment_seed()):
        result = s.load_seed_manifest(manifest, ag)
        assert result["rules_skipped"] == [], result
    for budget in s.nodes("ThinkingBudget"):
        for key, value in {"enabled": 1.0, "capacity": 100.0,
            "capacity_ceiling": 100.0, "remaining": 100.0,
            "last_refill_epoch": 10.0, "refill_per_epoch": 0.0}.items():
            s.set_attr(budget, key, value)
    s.set_attr(s.nodes("NetworkModeState")[0], "epoch", 10.0)
    s.set_attr(s.nodes("ModelLearningPolicy")[0], "enabled", 1.0)
    s.set_attr(s.nodes("ExperimentDesignPolicy")[0], "enabled", 1.0)
    return s, ag


def _tick(s):
    for _ in range(60):
        if not s.run_rules(5000):
            return
    raise AssertionError("native observed-world rules did not reach a fixpoint")


def _record(s, ag, *, event, episode, object_id, feature_key, before, after):
    common = {"owner_id": "owner-a", "episode_id": episode,
        "event_id": event, "source_epoch": 3, "model_epoch": 2, "frame_epoch": 5}
    obs = s.add_node("TransitionObservation", {**common, "object_id": object_id,
        "object_type": "Object", "action_kind": "heat", "feature_key": feature_key,
        "before_value": before, "after_value": after, "status": "observed"})
    action = s.add_node("TransitionActionReceipt", {**common, "status": "observed",
        "action_id": "heat"})
    outcome = s.add_node("TransitionOutcomeReceipt", {**common, "status": "observed",
        "observed_value": after})
    s.add_edge(ag, "has_transition_observation", obs)
    s.add_edge(obs, "has_action_receipt", action)
    s.add_edge(obs, "has_outcome_receipt", outcome)
    return obs


def _record_world_action(s, ag, world, object_id, index):
    observation = world.observe(object_id)
    receipt = world.execute(observation, "heat")
    assert world.verify_receipt(receipt)
    for feature_key, value in observation["features"].items():
        _record(s, ag, event=f"{index}-{feature_key}", episode=f"episode-{index}",
            object_id=object_id, feature_key=feature_key, before=value,
            after=receipt["observed_state"])
    return observation, receipt


def _query(s, ag, *, object_id, feature_key, before, query_id):
    query = s.add_node("ProcessPredictionQuery", {"query_id": query_id,
        "owner_id": "owner-a", "object_id": object_id, "object_type": "Object",
        "action_kind": "heat", "feature_key": feature_key, "before_value": before,
        "source_epoch": 3, "model_epoch": 2, "frame_epoch": 5, "status": "pending"})
    s.add_edge(ag, "has_process_prediction_query", query)
    return query


def test_agent_probe_changes_world_state_and_receipt_verifies_transition():
    s, ag = _boot()
    world = ObservedWorld.create("object_mechanism", 44)
    for i, object_id in enumerate(("object-0", "object-2", "object-1", "object-3"), 1):
        _record_world_action(s, ag, world, object_id, i)
        _tick(s)

    fresh = world.observe("object-4")
    _query(s, ag, object_id="object-4", feature_key="surface",
        before=fresh["features"]["surface"], query_id="fresh:surface")
    _query(s, ag, object_id="object-4", feature_key="material",
        before=fresh["features"]["material"], query_id="fresh:material")
    projection = s.add_node("WorldModelProjection", {"owner_id": "owner-a",
        "model_epoch": 2, "version": 0.0, "status": "current"})
    s.add_edge(ag, "has_world_model_projection", projection)
    _tick(s)

    predictions = s.nodes("ProcessPrediction")
    assert {s.node(p)["attrs"]["expected_after_value"] for p in predictions} == {"cool", "warm"}
    probes = s.nodes("ExperimentProbe")
    assert len(probes) == 1
    assert s.node(probes[0])["attrs"]["candidate_source"] == "observed_model_disagreement"
    assert s.node(probes[0])["attrs"]["action_id"] == "heat"
    selected = [n for n in s.nodes("SelectedExperiment")
        if s.node(n)["attrs"].get("status") == "selected"]
    assert len(selected) == 1
    probe = s.neighbours(selected[0], "selects_experiment_probe")[0]

    # The host transports the graph-authored legal action; the world alone
    # computes and signs the consequence.
    action = s.node(probe)["attrs"]["action_id"]
    before_state = world.observe("object-4")
    receipt = world.execute(before_state, action)
    assert world.verify_receipt(receipt)
    assert receipt["observed_state"] != before_state["state"]
    result = s.add_node("ObservedExperimentResult", {"result_id": "result:fresh",
        "probe_id": s.node(probe)["attrs"]["probe_id"], "owner_id": "owner-a",
        "model_epoch": 2, "status": "observed",
        "observed_outcome": receipt["observed_state"],
        "world_id": receipt["world_id"], "world_epoch": receipt["world_epoch"],
        "receipt_sha256": receipt["receipt_sha256"]})
    s.add_edge(ag, "has_experiment_result", result)
    s.add_edge(result, "result_for_experiment", selected[0])
    _tick(s)
    assert s.node(selected[0])["attrs"]["status"] == "completed"
    assert s.node(projection)["attrs"]["version"] == 1.0
    assert len([a for a in s.nodes("ExperimentRevisionAudit")
        if s.node(a)["attrs"].get("result_id") == "result:fresh"]) == 3
    assert any(s.node(h)["attrs"].get("status") == "disputed"
        for h in s.nodes("ProcessInductionHypothesis"))


def test_no_information_probe_is_declined():
    s, ag = _boot()
    world = ObservedWorld.create("object_mechanism", 44)
    for i, object_id in enumerate(("object-0", "object-2"), 1):
        _record_world_action(s, ag, world, object_id, i)
        _tick(s)
    known = world.observe("object-0")
    _query(s, ag, object_id="object-0", feature_key="surface",
        before=known["features"]["surface"], query_id="known:surface")
    _query(s, ag, object_id="object-0", feature_key="material",
        before=known["features"]["material"], query_id="known:material")
    _tick(s)
    assert {s.node(p)["attrs"]["expected_after_value"] for p in s.nodes("ProcessPrediction")} == {"warm"}
    assert not s.nodes("ExperimentProbe")
    assert not s.nodes("SelectedExperiment")
