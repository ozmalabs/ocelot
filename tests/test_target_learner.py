"""P20 bounded fresh target learner: receipt-bound native transition induction."""
import json
from pathlib import Path

from substrate_rs import _native
from scripts.gen_process_induction_seed import build_seed
from evaluation.process_mastery.target_learner import NativeTargetLearner, build_target_learner
from evaluation.process_mastery.target_learning_worlds import (
    HeatSourceWorld, LatchWorld, LeverSourceWorld, ThermalWorld, WorldReceipt,
    induce_categorical_effect_map, verify_categorical_effect_map,
    verify_induced_map_candidate, verify_source_prior_target_effect,
)

ROOT = Path(__file__).resolve().parents[1]


def _boot(enabled=True):
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    for name in ("default_mode_core", "thinking_budget", "cognition_signature",
                 "experience_signature"):
        s.load_seed_manifest(json.loads((ROOT / "seeds" / f"{name}.json").read_text()), ag)
    result = s.load_seed_manifest(build_seed(), ag)
    assert result["rules_skipped"] == [], result
    for budget in s.nodes("ThinkingBudget"):
        s.set_attr(budget, "enabled", 1.0)
        s.set_attr(budget, "remaining", 100.0)
        s.set_attr(budget, "last_refill_epoch", 10.0)
    s.set_attr(s.nodes("NetworkModeState")[0], "epoch", 10.0)
    s.set_attr(s.nodes("ModelLearningPolicy")[0], "enabled", float(enabled))
    return s, ag


def _observe(s, ag, i, *, after="warm", owner="target", model=2, source=3,
             frame=5, receipt=True):
    episode, event = f"target-episode-{i}", f"target-event-{i}"
    obs = s.add_node("TransitionObservation", {
        "owner_id": owner, "episode_id": episode, "event_id": event,
        "object_id": f"object-{i}", "object_type": "Widget", "action_kind": "warm",
        "feature_key": "temperature", "before_value": "cold", "after_value": after,
        "source_epoch": source, "model_epoch": model, "frame_epoch": frame,
        "status": "observed"})
    action = s.add_node("TransitionActionReceipt", {
        "owner_id": owner, "episode_id": episode, "event_id": event,
        "source_epoch": source, "model_epoch": model, "frame_epoch": frame,
        "status": "observed"})
    s.add_edge(ag, "has_transition_observation", obs)
    s.add_edge(obs, "has_action_receipt", action)
    if receipt:
        outcome = s.add_node("TransitionOutcomeReceipt", {
            "owner_id": owner, "episode_id": episode, "event_id": event,
            "source_epoch": source, "model_epoch": model, "frame_epoch": frame,
            "status": "observed"})
        s.add_edge(obs, "has_outcome_receipt", outcome)
    return obs


def _run(s):
    for _ in range(40):
        if not s.run_rules(2000):
            return
    raise AssertionError("target learner did not reach fixpoint")


def _fund_map_observation(s, ag, pair, pair_id):
    request = s.add_node("ThinkingBudgetRequest", {
        "requester_kind": "target_map_observation", "source_key": pair_id,
        "source_epoch": 3, "requested_epoch": 10.0,
        "operation_id": f"target-map:{pair_id}", "status": "pending", "cost": 1.0})
    s.add_edge(ag, "has_thinking_budget_request", request)
    s.add_edge(request, "draws_on_thinking_budget", s.neighbours(ag, "has_thinking_budget")[0])
    s.add_edge(pair, "funded_by", request)


def test_fresh_has_real_learning_path():
    s, ag = _boot()
    _observe(s, ag, 1)
    _observe(s, ag, 2)
    _run(s)
    hypotheses = s.nodes("ProcessInductionHypothesis")
    assert len(hypotheses) == 1
    attrs = s.node(hypotheses[0])["attrs"]
    assert attrs["status"] == "candidate"
    assert attrs["after_value"] == "warm"
    assert attrs["support_count"] == 2.0
    assert len(s.neighbours(hypotheses[0], "supported_by_transition")) == 2


def test_same_target_affordances_and_empty_start_for_all_source_conditions():
    # Source availability is represented separately; it does not change the
    # target learner or its affordances before target evidence arrives.
    learners = [NativeTargetLearner() for _ in ("fresh", "matched", "mismatched")]
    learners[1].expose_source(source_id="source-a", relation="matched")
    learners[2].expose_source(source_id="source-b", relation="mismatched")
    for learner in learners:
        assert learner.s.node(learner.s.nodes("ModelLearningPolicy")[0])["attrs"]["enabled"] == 1.0
        assert len(learner.s.nodes("ThinkingBudget")) == 1
        assert not learner.s.nodes("TransitionObservation")
        assert not learner.s.nodes("ProcessInductionHypothesis")


def test_missing_outcome_receipt_cannot_teach_fresh_target():
    s, ag = _boot()
    _observe(s, ag, 1, receipt=False)
    _observe(s, ag, 2, receipt=False)
    _run(s)
    assert not s.nodes("ProcessInductionHypothesis")


def test_wrong_owner_or_epoch_receipt_does_not_create_hypothesis():
    s, ag = _boot()
    obs = _observe(s, ag, 1)
    outcome = s.neighbours(obs, "has_outcome_receipt")[0]
    s.set_attr(outcome, "model_epoch", 99.0)
    _run(s)
    assert not s.nodes("ProcessInductionHypothesis")


def test_disabled_policy_has_no_target_learning_path():
    s, ag = _boot(enabled=False)
    _observe(s, ag, 1)
    _observe(s, ag, 2)
    _run(s)
    assert not s.nodes("ProcessInductionHypothesis")


def test_counterevidence_disputes_target_effect():
    s, ag = _boot()
    _observe(s, ag, 1, after="warm")
    _observe(s, ag, 2, after="warm")
    _run(s)
    hypothesis = s.nodes("ProcessInductionHypothesis")[0]
    _observe(s, ag, 3, after="cold")
    _run(s)
    assert s.node(hypothesis)["attrs"]["status"] == "disputed"


def test_target_adapter_learns_from_two_world_observations_and_predicts_new_binding():
    learner = NativeTargetLearner()
    for i in (1, 2):
        learner.observe_opportunity(event_id=f"observed-{i}", action_kind="warm",
                                    object_id=f"obj-{i}", object_type="Widget",
                                    feature_key="temperature", before_value="cold",
                                    after_value="warm")
    learner.settle()
    assert len(learner.hypotheses()) == 1
    prediction = learner.predict(query_id="new-target", action_kind="warm",
                                 object_type="Widget", feature_key="temperature",
                                 before_value="cold", object_id="obj-new")
    assert prediction["expected_after_value"] == "warm"
    assert prediction["evidence_status"] == "predicted"
    assert learner.accounting.target_actions == 2


def test_source_exposure_is_charged_but_cannot_create_target_hypothesis():
    learner = NativeTargetLearner()
    learner.expose_source(source_id="matched-source-1", relation="matched", units=2.5)
    learner.settle()
    assert learner.accounting.source_information_units == 2.5
    assert learner.accounting.visible_observations == 0
    assert learner.hypotheses() == []


def test_missing_opportunity_is_counted_without_inventing_a_transition():
    learner = NativeTargetLearner()
    assert learner.observe_opportunity(event_id="occluded-1", visible=False) is None
    assert learner.accounting.evidence_opportunities == 1
    assert learner.accounting.missing_observations == 1
    assert learner.accounting.target_actions == 0
    assert learner.hypotheses() == []
    assert learner.learning_records[0]["status"] == "not_observed"


def _source_prior(learner, *, map_status="verified", target_event="target-transfer-1",
                  exact=True):
    learner.import_source_prior(
        prior_id="source-prior-1", source_id="source-model-1",
        action_kind="warm", object_type="Widget", feature_key="temperature",
        before_value="cold", after_value="warm", source_epoch=3, model_epoch=2,
        frame_epoch=5,
        map_evidence={"map_id": "map-1", "status": map_status,
                      "mapping_kind": "exact_categorical_effect",
                      "target_frame_epoch": 5},
        target_receipt={"receipt_id": "target-verify-1", "source_prior_id": "source-prior-1",
                        "target_event_id": target_event, "status": "verified",
                        "exact_effect_match": exact})


def test_source_uses_same_target_verifier_and_new_binding_predictor():
    learner = NativeTargetLearner(transfer_enabled=True)
    _source_prior(learner)
    learner.expose_source(source_id="source-model-1", relation="matched", units=3.0)
    learner.observe_opportunity(event_id="target-transfer-1", action_kind="warm",
                                object_id="target-object-1", object_type="Widget",
                                feature_key="temperature", before_value="cold",
                                after_value="warm")
    learner.settle()
    assert len(learner.hypotheses()) == 1
    assert learner.hypotheses()[0]["effect_evaluation"] == "exact_source_map_and_target_receipt"
    prediction = learner.predict(query_id="transferred-binding", action_kind="warm",
                                 object_type="Widget", feature_key="temperature",
                                 before_value="cold", object_id="target-object-2")
    assert prediction["expected_after_value"] == "warm"


def test_wrong_map_or_wrong_target_receipt_is_rejected():
    for map_status, event_id, exact in (("stale", "target-transfer-1", True),
                                        ("verified", "different-target-event", True),
                                        ("verified", "target-transfer-1", False)):
        learner = NativeTargetLearner(transfer_enabled=True)
        _source_prior(learner, map_status=map_status, target_event=event_id, exact=exact)
        learner.observe_opportunity(event_id="target-transfer-1", action_kind="warm",
                                    object_id="target-object-1", object_type="Widget",
                                    feature_key="temperature", before_value="cold",
                                    after_value="warm")
        learner.settle()
        assert learner.hypotheses() == []


def test_fresh_learns_unseen_target_in_two_independent_native_worlds():
    cases = (
        (ThermalWorld(object_ids=("t1", "t2", "t3")),
         ("t1", "t2"), "warm", "ThermalSample", "temperature", "cold", "warm"),
        (LatchWorld(latch_ids=("l1", "l2", "l3")),
         ("l1", "l2"), "lift", "Latch", "position", "lowered", "raised"),
    )
    for world, training_ids, action, kind, feature, before, after in cases:
        learner = NativeTargetLearner()
        for object_id in training_ids:
            receipt = (world.apply(object_id, action) if isinstance(world, ThermalWorld)
                       else world.operate(object_id, action))
            learner.observe_world_receipt(receipt)
            learner.settle()
        prediction = learner.predict(
            query_id=f"unseen:{world.family}", action_kind=action,
            object_type=kind, feature_key=feature, before_value=before,
            object_id=f"{world.family}-unseen")
        assert prediction["expected_after_value"] == after
        assert learner.accounting.target_actions == 2
        assert learner.accounting.visible_observations == 2
        assert [row["hypothesis_count"] for row in learner.learning_records] == [0, 1]
        assert all(row["status"] == "settled" for row in learner.learning_records)


def test_world_receipt_replay_and_unauthorized_receipt_are_rejected():
    learner = NativeTargetLearner()
    world = ThermalWorld(object_ids=("sample",))
    receipt = world.apply("sample", "warm")
    learner.observe_world_receipt(receipt)
    try:
        learner.observe_world_receipt(receipt)
    except ValueError as exc:
        assert "already ingested" in str(exc)
    else:
        raise AssertionError("replayed world receipt accepted")
    bad = WorldReceipt("bad", "sample", "ThermalSample", "warm", "temperature",
                       "cold", "warm", "observed", False, 2)
    try:
        learner.observe_world_receipt(bad)
    except ValueError as exc:
        assert "authorized observed action" in str(exc)
    else:
        raise AssertionError("unauthorized world receipt accepted")


def test_missing_adapter_is_a_hard_error():
    try:
        build_target_learner(None, arm="fresh")
    except RuntimeError as exc:
        assert "missing target learner adapter" in str(exc)
    else:
        raise AssertionError("missing target learner adapter was scored")


def test_evidence_and_work_separate():
    learner = NativeTargetLearner()
    learner.expose_source(source_id="source-exp", relation="matched", units=4.0)
    learner.observe_opportunity(event_id="occluded", visible=False)
    receipt = ThermalWorld(object_ids=("sample",)).apply("sample", "warm")
    learner.observe_world_receipt(receipt)
    assert learner.accounting.source_information_units == 4.0
    assert learner.accounting.evidence_opportunities == 2
    assert learner.accounting.visible_observations == 1
    assert learner.accounting.missing_observations == 1
    assert learner.accounting.target_actions == 1


def test_source_target_maps_are_verified_on_two_independent_domain_pairs():
    cases = (
        (HeatSourceWorld(sample_ids=("s1", "s2")),
         ThermalWorld(object_ids=("t1", "t2")),
         lambda world, key: world.apply_heat(key, "apply_heat"),
         lambda world, key: world.apply(key, "warm"),
         {"apply_heat": "warm"}, {"MetalSample": "ThermalSample"},
         {"heat_level": "temperature"},
         {"chilled": "cold", "tempered": "warm"}, {"s1": "t1", "s2": "t2"}),
        (LeverSourceWorld(lever_ids=("s1", "s2")),
         LatchWorld(latch_ids=("t1", "t2")),
         lambda world, key: world.raise_control(key, "raise_control"),
         lambda world, key: world.operate(key, "lift"),
         {"raise_control": "lift"}, {"ControlLever": "Latch"},
         {"orientation": "position"}, {"down": "lowered", "up": "raised"},
         {"s1": "t1", "s2": "t2"}),
    )
    for (source_world, target_world, source_step, target_step, actions, types,
         features, values, objects) in cases:
        source_receipts = [source_step(source_world, key) for key in ("s1", "s2")]
        target_receipts = [target_step(target_world, key) for key in ("t1", "t2")]
        record = verify_categorical_effect_map(
            source_receipts=source_receipts, target_receipts=target_receipts,
            map_id=f"map:{source_world.__class__.__name__}", action_map=actions,
            object_type_map=types, feature_map=features, value_map=values,
            object_map=objects, target_frame_epoch=5)
        assert record["status"] == "verified"
        assert record["witness_count"] == 2
        proposal = induce_categorical_effect_map(
            source_receipts=source_receipts, target_receipts=target_receipts,
            object_pairs=objects, map_id=f"induced:{source_world.__class__.__name__}",
            target_frame_epoch=5)
        assert proposal["status"] == "candidate"
        assert proposal["action_map"] == actions
        assert proposal["object_type_map"] == types
        assert proposal["feature_map"] == features
        assert proposal["value_map"] == values
        assert verify_categorical_effect_map(
            source_receipts=source_receipts, target_receipts=target_receipts,
            map_id=proposal["map_id"], action_map=proposal["action_map"],
            object_type_map=proposal["object_type_map"],
            feature_map=proposal["feature_map"], value_map=proposal["value_map"],
            object_map=proposal["object_map"], target_frame_epoch=5)["status"] == "verified"
        wrong = verify_categorical_effect_map(
            source_receipts=source_receipts, target_receipts=target_receipts,
            map_id="wrong", action_map=actions, object_type_map=types,
            feature_map=features, value_map={**values, list(values)[-1]: "wrong"},
            object_map=objects, target_frame_epoch=5)
        assert wrong["status"] == "rejected"
        insufficient = verify_categorical_effect_map(
            source_receipts=source_receipts[:1], target_receipts=target_receipts[:1],
            map_id="one-witness", action_map=actions, object_type_map=types,
            feature_map=features, value_map=values, object_map={"s1": "t1"},
            target_frame_epoch=5)
        assert insufficient["status"] == "rejected"


def test_categorical_map_is_induced_from_paired_interaction_receipts():
    source = HeatSourceWorld(sample_ids=("source-a", "source-b"))
    target = ThermalWorld(object_ids=("target-a", "target-b"))
    source_receipts = [source.apply_heat(key, "apply_heat")
                       for key in ("source-a", "source-b")]
    target_receipts = [target.apply(key, "warm") for key in ("target-a", "target-b")]
    object_pairs = {"source-a": "target-a", "source-b": "target-b"}
    proposal = induce_categorical_effect_map(
        source_receipts=source_receipts, target_receipts=target_receipts,
        object_pairs=object_pairs, map_id="induced:heat-to-thermal",
        target_frame_epoch=5)
    assert proposal["status"] == "candidate"
    assert proposal["action_map"] == {"apply_heat": "warm"}
    assert proposal["object_type_map"] == {"MetalSample": "ThermalSample"}
    assert proposal["feature_map"] == {"heat_level": "temperature"}
    assert proposal["value_map"] == {"chilled": "cold", "tempered": "warm"}
    verified = verify_categorical_effect_map(
        source_receipts=source_receipts, target_receipts=target_receipts,
        map_id=proposal["map_id"], action_map=proposal["action_map"],
        object_type_map=proposal["object_type_map"], feature_map=proposal["feature_map"],
        value_map=proposal["value_map"], object_map=proposal["object_map"],
        target_frame_epoch=proposal["target_frame_epoch"])
    assert verified["status"] == "verified"


def test_categorical_map_induction_rejects_conflicting_pairs():
    from dataclasses import replace

    source = HeatSourceWorld(sample_ids=("source-a", "source-b"))
    target = ThermalWorld(object_ids=("target-a", "target-b"))
    source_receipts = [source.apply_heat(key, "apply_heat")
                       for key in ("source-a", "source-b")]
    target_receipts = [target.apply(key, "warm") for key in ("target-a", "target-b")]
    conflicting = [target_receipts[0], replace(target_receipts[1], after_value="hot")]
    proposal = induce_categorical_effect_map(
        source_receipts=source_receipts, target_receipts=conflicting,
        object_pairs={"source-a": "target-a", "source-b": "target-b"},
        map_id="conflicting-map", target_frame_epoch=5)
    assert proposal["status"] == "rejected"
    assert any("conflicting_value_map" in error for error in proposal["errors"])


def test_native_graph_induces_map_candidate_from_distinct_paired_receipts():
    s, ag = _boot(enabled=True)
    result = s.load_seed_manifest(json.loads((ROOT / "seeds" / "target_learning.json").read_text()), ag)
    assert result["rules_skipped"] == [], result
    policy = s.nodes("TargetLearningPolicy")[0]
    s.set_attr(policy, "enabled", 1.0)
    for ix, source_id, target_id in ((1, "source-a", "target-a"),
                                     (2, "source-b", "target-b")):
        pair = s.add_node("TargetMapObservation", {
            "pair_id": f"map-pair-{ix}", "source_object_id": source_id,
            "target_object_id": target_id, "source_action": "apply_heat",
            "target_action": "warm", "source_object_type": "MetalSample",
            "target_object_type": "ThermalSample", "source_feature": "heat_level",
            "target_feature": "temperature", "source_before": "chilled",
            "target_before": "cold", "source_after": "tempered",
            "target_after": "warm", "source_epoch": 3,
            "target_frame_epoch": 5, "status": "observed_pair"})
        s.add_edge(ag, "has_target_map_observation", pair)
        _fund_map_observation(s, ag, pair, f"map-pair-{ix}")
    _run(s)
    proposals = [s.node(node)["attrs"] for node in s.neighbours(ag, "has_target_map_candidate")]
    assert len(proposals) == 1
    proposal = proposals[0]
    assert proposal["status"] == "candidate"
    assert proposal["mapping_kind"] == "induced_categorical_effect"
    assert proposal["witness_count"] == 2.0
    assert proposal["source_action"] == "apply_heat"
    assert proposal["target_action"] == "warm"
    assert proposal["source_before"] == "chilled"
    assert proposal["target_before"] == "cold"


def test_native_graph_does_not_induce_map_from_conflicting_pairs():
    s, ag = _boot(enabled=True)
    result = s.load_seed_manifest(json.loads((ROOT / "seeds" / "target_learning.json").read_text()), ag)
    assert result["rules_skipped"] == [], result
    s.set_attr(s.nodes("TargetLearningPolicy")[0], "enabled", 1.0)
    for ix, target_action in ((1, "warm"), (2, "cool")):
        pair = s.add_node("TargetMapObservation", {
            "pair_id": f"map-pair-{ix}", "source_object_id": f"source-{ix}",
            "target_object_id": f"target-{ix}", "source_action": "apply_heat",
            "target_action": target_action, "source_object_type": "MetalSample",
            "target_object_type": "ThermalSample", "source_feature": "heat_level",
            "target_feature": "temperature", "source_before": "chilled",
            "target_before": "cold", "source_after": "tempered",
            "target_after": "warm", "source_epoch": 3,
            "target_frame_epoch": 5, "status": "observed_pair"})
        s.add_edge(ag, "has_target_map_observation", pair)
        _fund_map_observation(s, ag, pair, f"map-pair-{ix}")
    _run(s)
    assert not s.neighbours(ag, "has_target_map_candidate")


def test_actual_world_map_pairs_flow_through_native_candidate_and_verifier():
    from evaluation.process_mastery.target_learner import NativeTargetLearner

    learner = NativeTargetLearner(transfer_enabled=True)
    learner.s.set_attr(learner.s.nodes("TargetLearningPolicy")[0], "enabled", 1.0)
    budget = learner.s.nodes("ThinkingBudget")[0]
    starting_budget = learner.s.node(budget)["attrs"]["remaining"]
    source = HeatSourceWorld(sample_ids=("source-a", "source-b"))
    target = ThermalWorld(object_ids=("target-a", "target-b"))
    source_receipts, target_receipts = [], []
    for ix, (source_id, target_id) in enumerate(
            (("source-a", "target-a"), ("source-b", "target-b")), 1):
        source_receipt = source.apply_heat(source_id, "apply_heat")
        target_receipt = target.apply(target_id, "warm")
        source_receipts.append(source_receipt)
        target_receipts.append(target_receipt)
        learner.observe_map_pair(pair_id=f"pair-{ix}", source=source_receipt,
                                 target=target_receipt)
    learner.settle()
    assert learner.s.node(budget)["attrs"]["remaining"] == starting_budget - 2.0
    assert all(learner.s.node(request)["attrs"]["status"] == "approved"
               and learner.s.node(request)["attrs"]["debited_epoch"] is not None
               for request in learner.s.nodes("ThinkingBudgetRequest")
               if learner.s.node(request)["attrs"].get("requester_kind") == "target_map_observation")
    candidates = learner.s.nodes("RepresentationMap")
    candidate_nodes = [node for node in candidates
                       if learner.s.node(node)["attrs"].get("mapping_kind") == "induced_categorical_effect"]
    assert len(candidate_nodes) == 1
    candidate = learner.s.node(candidate_nodes[0])
    verification = verify_induced_map_candidate(
        candidate=candidate, source_receipts=source_receipts,
        target_receipts=target_receipts,
        object_pairs={"source-a": "target-a", "source-b": "target-b"})
    assert verification["status"] == "verified"
    assert learner.accounting.source_map_observations == 2
    assert learner.accounting.target_map_interactions == 2
    assert learner.accounting.target_actions == 2


def test_native_source_prior_transfers_through_map_and_fresh_target_receipt():
    cases = (
        (HeatSourceWorld(sample_ids=("s1", "s2")),
         ThermalWorld(object_ids=("t1", "t2", "t3", "t4")),
         lambda world, key: world.apply_heat(key, "apply_heat"),
         lambda world, key: world.apply(key, "warm"),
         {"apply_heat": "warm"}, {"MetalSample": "ThermalSample"},
         {"heat_level": "temperature"},
         {"chilled": "cold", "tempered": "warm"}, {"s1": "t1", "s2": "t2"},
         "apply_heat", "MetalSample", "heat_level", "chilled", "tempered",
         "warm", "ThermalSample", "temperature", "cold", "warm"),
        (LeverSourceWorld(lever_ids=("s1", "s2")),
         LatchWorld(latch_ids=("t1", "t2", "t3", "t4")),
         lambda world, key: world.raise_control(key, "raise_control"),
         lambda world, key: world.operate(key, "lift"),
         {"raise_control": "lift"}, {"ControlLever": "Latch"},
         {"orientation": "position"}, {"down": "lowered", "up": "raised"},
         {"s1": "t1", "s2": "t2"},
         "raise_control", "ControlLever", "orientation", "down", "up",
         "lift", "Latch", "position", "lowered", "raised"),
    )
    for (source_world, target_world, source_step, target_step, actions, types,
         features, values, objects, source_action, source_type, source_feature,
         source_before, source_after, target_action, target_type, target_feature,
         target_before, target_after) in cases:
        source_learner = NativeTargetLearner()
        source_receipts = [source_step(source_world, key) for key in ("s1", "s2")]
        for receipt in source_receipts:
            source_learner.observe_world_receipt(receipt)
        source_learner.settle()
        source_hypothesis = source_learner.hypotheses()[0]
        assert source_hypothesis["action_kind"] == source_action
        assert source_hypothesis["after_value"] == source_after

        target_map_receipts = [target_step(target_world, key) for key in ("t1", "t2")]
        target_learner = NativeTargetLearner(transfer_enabled=True)
        for ix, (source_receipt, target_receipt) in enumerate(
                zip(source_receipts, target_map_receipts), 1):
            target_learner.observe_map_pair(
                pair_id=f"transfer-pair:{source_world.__class__.__name__}:{ix}",
                source=source_receipt, target=target_receipt)
        target_learner.settle()
        candidates = [target_learner.s.node(node) for node
                      in target_learner.s.nodes("RepresentationMap")
                      if target_learner.s.node(node)["attrs"].get("mapping_kind")
                      == "induced_categorical_effect"]
        assert len(candidates) == 1
        map_record = verify_induced_map_candidate(
            candidate=candidates[0], source_receipts=source_receipts,
            target_receipts=target_map_receipts, object_pairs=objects)
        assert map_record["status"] == "verified"
        target_validation_receipt = target_step(target_world, "t3")
        prior_id = f"prior:{source_hypothesis['hypothesis_key']}"
        effect_receipt = verify_source_prior_target_effect(
            prior_id=prior_id, source_hypothesis=source_hypothesis,
            map_record=map_record, target_receipt=target_validation_receipt)
        assert effect_receipt["status"] == "verified"

        target_learner.import_source_prior(
            prior_id=prior_id, source_id="source-model", action_kind=target_action,
            object_type=target_type, feature_key=target_feature,
            before_value=target_before, after_value=target_after,
            source_epoch=3, model_epoch=2, frame_epoch=5,
            map_evidence=map_record, target_receipt=effect_receipt)
        target_learner.observe_world_receipt(target_validation_receipt)
        target_learner.settle()
        assert target_learner.accounting.source_map_observations == 2
        assert target_learner.accounting.source_information_units == 2.0
        assert target_learner.accounting.target_map_interactions == 2
        assert target_learner.accounting.target_actions == 3
        assert target_learner.accounting.map_verification_queries == 4
        assert len(target_learner.hypotheses()) == 1
        prediction = target_learner.predict(
            query_id=f"transfer-unseen:{source_world.__class__.__name__}",
            action_kind=target_action, object_type=target_type,
            feature_key=target_feature, before_value=target_before,
            object_id="t4")
        assert prediction["expected_after_value"] == target_after
