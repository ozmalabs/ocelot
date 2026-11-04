"""P26.03 native selection, common-learner delivery, and causal closure."""
import json

from evaluation.process_mastery.common_target_learner import CommonTargetLearner
from evaluation.process_mastery.target_learning_worlds import ThermalWorld
from scripts.gen_useful_evidence_selection_seed import OUT, build_seed


def _learner(mode="residual", pool_id="p26-shared-training-pool"):
    learner = CommonTargetLearner()
    loaded = learner.s._inner.load_seed_manifest(build_seed(), learner.ag)
    assert not loaded.get("rules_skipped")
    policy, = learner.s.nodes("UsefulEvidenceSelectionPolicy")
    learner.s.set_attr(policy, "enabled", 1.0)
    learner.s.set_attr(policy, "selector_mode", mode)
    learner.s.set_attr(policy, "pool_id", pool_id)
    return learner, policy


def _opportunity(learner, key, *, pool_id="p26-shared-training-pool",
                 source_epoch=3, fixed_rank=0.0, random_rank=0.0,
                 object_id=None):
    row = learner.s.add_node("UsefulEvidenceOpportunity", {
        "opportunity_key": key, "pool_id": pool_id, "status": "eligible",
        "split": "training", "expected_outcome": "unknown",
        "answer_fields_absent": True, "sealed_labels_present": False,
        "source_epoch": source_epoch, "model_epoch": 2, "frame_epoch": 5,
        "object_id": object_id or f"target-{key}",
        "object_type": "ThermalSample", "action_kind": "warm",
        "feature_key": "temperature", "before_value": "cold",
        "fixed_rank": fixed_rank, "random_rank": random_rank,
    })
    learner.s.add_edge(learner.ag, "has_useful_evidence_opportunity", row, {})
    return row


def _add_signal(learner, opportunity, signal_kind, suffix):
    s = learner.s
    signal = s.add_node("UsefulEvidenceSignal", {
        "signal_kind": signal_kind, "status": "verified", "split": "training",
        "source_epoch": 3, "model_epoch": 2, "frame_epoch": 5,
        "signal_key": f"{signal_kind}:{suffix}",
    })
    s.add_edge(opportunity, "has_selection_signal", signal, {})
    def add_counterexample(event_id):
        counterexample = s.add_node("ProcessCounterexample", {
            "event_id": event_id, "observed_after_value": "cold", "status": "observed",
        })
        transition = s.add_node("TransitionObservation", {
            "event_id": event_id, "status": "observed", "split": "training",
            "source_epoch": 3, "model_epoch": 2, "frame_epoch": 5,
            "action_kind": "warm", "object_type": "ThermalSample",
            "feature_key": "temperature", "before_value": "cold",
            "after_value": "cold",
        })
        s.add_edge(learner.ag, "has_transition_observation", transition, {})
        s.add_edge(counterexample, "counterexample_transition", transition, {})
        return counterexample

    if signal_kind == "prediction_disagreement":
        query = s.add_node("ProcessPredictionQuery", {
            "query_id": f"native-query:{suffix}", "status": "predicted",
            "split": "training", "source_epoch": 3, "model_epoch": 2,
            "frame_epoch": 5, "action_kind": "warm",
            "object_type": "ThermalSample", "feature_key": "temperature",
            "before_value": "cold",
        })
        prediction = s.add_node("ProcessPrediction", {
            "query_id": f"native-query:{suffix}", "status": "predicted",
            "expected_after_value": "warm",
        })
        counterexample = add_counterexample(f"native-counterexample:{suffix}")
        s.add_edge(learner.ag, "has_process_prediction_query", query, {})
        s.add_edge(learner.ag, "has_process_prediction", prediction, {})
        s.add_edge(prediction, "predicts_for_query", query, {})
        s.add_edge(signal, "derived_from_prediction", prediction, {})
        s.add_edge(signal, "derived_from_counterexample", counterexample, {})
    elif signal_kind == "recurring_residual":
        counterexample = add_counterexample(f"native-residual:{suffix}")
        s.add_edge(signal, "derived_from_counterexample", counterexample, {})
    elif signal_kind == "verified_learning_progress":
        world = ThermalWorld(object_ids=[f"signal-{suffix}"])
        receipt = world.apply(f"signal-{suffix}", "warm")
        learner.observe_world_receipt(receipt, source_epoch=3,
                                      model_epoch=2, frame_epoch=5, split="training")
        common, = [n for n in s.nodes("CommonTargetEvidence")
                   if s.node(n)["attrs"].get("event_id") == receipt.event_id]
        outcome = s.add_node("UsefulEvidenceLearningOutcome", {
            "event_id": receipt.event_id, "status": "observed",
            "assessment": "useful_progress", "split": "training",
            "source_epoch": 3, "model_epoch": 2, "frame_epoch": 5,
            "learned_state_changed": True, "behavior_changed": True,
            "before_state_digest": "state-before", "after_state_digest": "state-after",
            "before_behavior_digest": "behavior-before",
            "after_behavior_digest": "behavior-after",
        })
        s.add_edge(learner.ag, "has_useful_evidence_learning_outcome", outcome, {})
        s.add_edge(outcome, "based_on_target_evidence", common, {})
        s.add_edge(signal, "derived_from_learning_outcome", outcome, {})
    else:
        raise AssertionError(f"unsupported signal kind: {signal_kind}")
    return signal


def _selected(learner):
    rows = learner.s.nodes("UsefulEvidenceSelection")
    return [learner.s.node(n)["attrs"] for n in rows
            if learner.s.node(n)["attrs"].get("status") == "awaiting_receipt"]


def _record_outcome(learner, selection_node, receipt, *, before_state,
                    after_state, before_behavior, after_behavior):
    s = learner.s
    changed = before_state != after_state
    behavior_changed = before_behavior != after_behavior
    assessment = ("useful_progress" if changed and behavior_changed
                  else "no_progress")
    outcome = s.add_node("UsefulEvidenceLearningOutcome", {
        "event_id": receipt.event_id, "status": "observed",
        "assessment": assessment, "split": "training",
        "source_epoch": s.node(selection_node)["attrs"]["source_epoch"],
        "model_epoch": s.node(selection_node)["attrs"]["model_epoch"],
        "frame_epoch": s.node(selection_node)["attrs"]["frame_epoch"],
        "learned_state_changed": changed, "behavior_changed": behavior_changed,
        "before_state_digest": before_state, "after_state_digest": after_state,
        "before_behavior_digest": before_behavior,
        "after_behavior_digest": after_behavior,
    })
    evidence, = [n for n in s.nodes("CommonTargetEvidence")
                 if s.node(n)["attrs"].get("event_id") == receipt.event_id]
    s.add_edge(learner.ag, "has_useful_evidence_learning_outcome", outcome, {})
    s.add_edge(selection_node, "has_outcome", outcome, {})
    s.add_edge(outcome, "outcome_for_selection", selection_node, {})
    s.add_edge(outcome, "based_on_target_evidence", evidence, {})
    learner.settle()
    return outcome


def test_selected_evidence_changes_prediction():
    learner, _ = _learner()
    world = ThermalWorld(object_ids=["source", "selected-target", "fresh-before", "fresh-after"])
    learner.observe_world_receipt(world.apply("source", "warm"),
                                  source_epoch=3, model_epoch=2, frame_epoch=5,
                                  split="training")
    learner.settle()
    before = learner.predict(query_id="before-selection", action_kind="warm",
        object_type="ThermalSample", feature_key="temperature",
        before_value="cold", object_id="fresh-before", split="training")
    opportunity = _opportunity(learner, "evidence-b", object_id="selected-target")
    learner.settle()
    selection_node, = [n for n in learner.s.nodes("UsefulEvidenceSelection")
                       if learner.s.node(n)["attrs"].get("status") == "awaiting_receipt"]
    selection = learner.s.node(selection_node)["attrs"]
    assert selection["opportunity_key"] == learner.s.node(opportunity)["attrs"]["opportunity_key"]
    assert selection["answer_fields_absent"] is True
    assert selection["expected_outcome"] == "unknown"
    assert "after_value" not in selection and "expected_after_value" not in selection

    # The mechanical world adapter receives the native selection and returns its actual receipt.
    receipt = world.apply(selection["object_id"], selection["action_kind"])
    before_state = json.dumps(learner.hypotheses(), sort_keys=True)
    before_behavior = json.dumps(before, sort_keys=True) if before is not None else "no-prediction"
    learner.observe_world_receipt(receipt, source_epoch=selection["source_epoch"],
        model_epoch=selection["model_epoch"], frame_epoch=selection["frame_epoch"],
        split="training")
    learner.settle()
    after = learner.predict(query_id="after-selection", action_kind="warm",
        object_type="ThermalSample", feature_key="temperature",
        before_value="cold", object_id="fresh-after", split="training")
    after_state = json.dumps(learner.hypotheses(), sort_keys=True)
    after_behavior = json.dumps(after, sort_keys=True) if after is not None else "no-prediction"
    assert before is None
    assert after is not None and after["expected_after_value"] == "warm"
    assert before_state != after_state
    assert before_behavior != after_behavior
    followup = _opportunity(learner, "z-follow-up", object_id="later-target")
    _record_outcome(learner, selection_node, receipt, before_state=before_state,
        after_state=after_state, before_behavior=before_behavior,
        after_behavior=after_behavior)
    assert learner.s.node(selection_node)["attrs"]["status"] == "completed_with_progress"
    assert learner.s.node(opportunity)["attrs"]["status"] == "resolved"
    progress_signals = [learner.s.node(n)["attrs"] for n in
        learner.s.neighbours(followup, "has_selection_signal")]
    assert len(progress_signals) == 1
    assert progress_signals[0]["signal_kind"] == "verified_learning_progress"


def test_unlearnable_source_not_repeated_forever():
    learner, _ = _learner()
    budget, = learner.s.nodes("ThinkingBudget")
    starting_budget = learner.s.node(budget)["attrs"]["remaining"]
    world = ThermalWorld(object_ids=["target-unlearnable"])
    opportunity = _opportunity(learner, "unlearnable")
    learner.settle()
    selection_node, = [n for n in learner.s.nodes("UsefulEvidenceSelection")
                       if learner.s.node(n)["attrs"].get("status") == "awaiting_receipt"]
    selection = learner.s.node(selection_node)["attrs"]
    request, = [n for n in learner.s.neighbours(selection_node, "has_budget_request")]
    assert learner.s.node(request)["attrs"]["status"] == "approved"
    assert learner.s.node(request)["attrs"]["cost"] == 1.0
    assert learner.s.node(budget)["attrs"]["remaining"] == starting_budget - 1.0
    receipt = world.apply(selection["object_id"], selection["action_kind"])
    learner.observe_world_receipt(receipt, source_epoch=3, model_epoch=2, frame_epoch=5,
                                  split="training")
    learner.settle()
    state = json.dumps(learner.hypotheses(), sort_keys=True)
    prediction = learner.predict(query_id="still-unknown", action_kind="warm",
        object_type="ThermalSample", feature_key="temperature",
        before_value="cold", object_id="fresh", split="training")
    _record_outcome(learner, selection_node, receipt, before_state=state,
        after_state=state, before_behavior="no-prediction",
        after_behavior=(json.dumps(prediction, sort_keys=True)
                        if prediction is not None else "no-prediction"))
    assert learner.s.node(opportunity)["attrs"]["status"] == "terminal_no_progress"
    for _ in range(5):
        learner.settle()
    assert len(learner.s.nodes("UsefulEvidenceSelection")) == 1
    assert learner.s.node(selection_node)["attrs"]["status"] == "terminal_no_progress"


def test_learned_state_without_later_behavior_is_not_useful_progress():
    learner, _ = _learner()
    world = ThermalWorld(object_ids=["baseline", "target"])
    learner.observe_world_receipt(world.apply("baseline", "warm"),
        source_epoch=3, model_epoch=2, frame_epoch=5, split="training")
    learner.settle()
    before_state = json.dumps(learner.hypotheses(), sort_keys=True)
    before_behavior = learner.predict(query_id="unrelated-before", action_kind="cool",
        object_type="ThermalSample", feature_key="temperature",
        before_value="cold", object_id="new-before", split="training")
    opportunity = _opportunity(learner, "state-without-use", object_id="target")
    learner.settle()
    selection_node, = [n for n in learner.s.nodes("UsefulEvidenceSelection")
                       if learner.s.node(n)["attrs"].get("status") == "awaiting_receipt"]
    selection = learner.s.node(selection_node)["attrs"]
    receipt = world.apply(selection["object_id"], selection["action_kind"])
    learner.observe_world_receipt(receipt, source_epoch=3, model_epoch=2, frame_epoch=5,
                                  split="training")
    learner.settle()
    after_state = json.dumps(learner.hypotheses(), sort_keys=True)
    after_behavior = learner.predict(query_id="unrelated-after", action_kind="cool",
        object_type="ThermalSample", feature_key="temperature",
        before_value="cold", object_id="new-after", split="training")
    assert before_state != after_state
    assert before_behavior is None and after_behavior is None
    _record_outcome(learner, selection_node, receipt, before_state=before_state,
        after_state=after_state, before_behavior="no-prediction",
        after_behavior="no-prediction")
    assert learner.s.node(selection_node)["attrs"]["status"] == "terminal_no_progress"
    assert learner.s.node(opportunity)["attrs"]["status"] == "terminal_no_progress"


def test_random_arm_has_identical_access():
    observed = {}
    selected = {}
    budget_remaining = {}
    for mode in ("residual", "fixed", "random"):
        learner, _ = _learner(mode)
        alpha = _opportunity(learner, "alpha", fixed_rank=1, random_rank=3)
        beta = _opportunity(learner, "beta", fixed_rank=2, random_rank=2)
        gamma = _opportunity(learner, "gamma", fixed_rank=3, random_rank=1)
        _add_signal(learner, alpha, "prediction_disagreement", f"{mode}-a")
        for i in range(3):
            _add_signal(learner, beta, "recurring_residual", f"{mode}-b{i}")
        for i in range(2):
            _add_signal(learner, gamma, "verified_learning_progress", f"{mode}-g{i}")
        observed[mode] = sorted(tuple(learner.s.node(n)["attrs"].get(field)
            for field in ("opportunity_key", "pool_id", "object_id", "object_type",
                          "action_kind", "feature_key", "before_value", "source_epoch",
                          "model_epoch", "frame_epoch", "fixed_rank", "random_rank"))
            for n in learner.s.nodes("UsefulEvidenceOpportunity"))
        learner.settle()
        selected[mode] = _selected(learner)[0]["opportunity_key"]
        budget, = learner.s.nodes("ThinkingBudget")
        budget_remaining[mode] = learner.s.node(budget)["attrs"]["remaining"]
        assert all(learner.s.node(n)["attrs"]["expected_outcome"] == "unknown"
                   for n in learner.s.nodes("UsefulEvidenceOpportunity"))
    assert observed["residual"] == observed["fixed"] == observed["random"]
    assert selected == {"residual": "beta", "fixed": "alpha", "random": "gamma"}
    assert budget_remaining["residual"] == budget_remaining["fixed"] == budget_remaining["random"]


def test_native_signals_require_current_prediction_and_repeated_receipted_residuals():
    learner, _ = _learner()
    s = learner.s
    opportunity = _opportunity(learner, "native-signals")
    hypothesis = s.add_node("ProcessInductionHypothesis", {
        "hypothesis_key": "warm-disputed", "status": "disputed",
        "source_epoch": 3, "model_epoch": 2, "frame_epoch": 5,
        "owner_id": learner.owner_id, "action_kind": "warm",
        "object_type": "ThermalSample", "feature_key": "temperature",
        "before_value": "cold", "after_value": "warm",
    })
    s.add_edge(learner.ag, "has_process_induction_hypothesis", hypothesis, {})
    query = s.add_node("ProcessPredictionQuery", {
        "query_id": "native-disagreement-query", "status": "predicted",
        "split": "training", "source_epoch": 3, "model_epoch": 2,
        "frame_epoch": 5, "action_kind": "warm",
        "object_type": "ThermalSample", "feature_key": "temperature",
        "before_value": "cold",
    })
    prediction = s.add_node("ProcessPrediction", {
        "query_id": "native-disagreement-query", "status": "predicted",
        "expected_after_value": "warm",
    })
    s.add_edge(learner.ag, "has_process_prediction_query", query, {})
    s.add_edge(learner.ag, "has_process_prediction", prediction, {})
    s.add_edge(prediction, "predicts_for_query", query, {})
    s.add_edge(prediction, "based_on_hypothesis", hypothesis, {})

    for i in (1, 2):
        counterexample = s.add_node("ProcessCounterexample", {
            "event_id": f"native-disagreement:{i}",
            "observed_after_value": "cold", "status": "observed",
        })
        transition = s.add_node("TransitionObservation", {
            "event_id": f"native-disagreement:{i}", "status": "observed",
            "split": "training", "source_epoch": 3, "model_epoch": 2,
            "frame_epoch": 5, "action_kind": "warm",
            "object_type": "ThermalSample", "feature_key": "temperature",
            "before_value": "cold", "after_value": "cold",
        })
        s.add_edge(hypothesis, "has_counterexample", counterexample, {})
        s.add_edge(counterexample, "counterexample_transition", transition, {})
    learner.settle()
    signals = [s.node(n)["attrs"] for n in s.neighbours(opportunity, "has_selection_signal")]
    assert sum(x["signal_kind"] == "prediction_disagreement" for x in signals) == 2
    assert sum(x["signal_kind"] == "recurring_residual" for x in signals) == 2
    assert all(x["split"] == "training" and x["status"] == "verified" for x in signals)
    assert all("observed_after_value" not in x and "expected_after_value" not in x
               for x in signals)


def test_receipt_fanout_not_extra_exposure():
    learner, _ = _learner()
    world = ThermalWorld(object_ids=["first", "selected"])
    first = world.apply("first", "warm")
    learner.observe_world_receipt(first, source_epoch=3, model_epoch=2, frame_epoch=5,
                                  split="training")
    opportunity = _opportunity(learner, "selected-event", object_id="selected")
    learner.settle()
    selection_node, = [n for n in learner.s.nodes("UsefulEvidenceSelection")
                       if learner.s.node(n)["attrs"].get("status") == "awaiting_receipt"]
    selection = learner.s.node(selection_node)["attrs"]
    receipt = world.apply(selection["object_id"], selection["action_kind"])
    learner.observe_world_receipt(receipt, source_epoch=3, model_epoch=2, frame_epoch=5,
                                  split="training")
    learner.settle()
    assert learner.accounting.target_actions == 2
    assert len([n for n in learner.s.nodes("CommonTargetEvidence")
                if learner.s.node(n)["attrs"].get("event_id") == receipt.event_id]) == 1
    assert len([n for n in learner.s.nodes("TransitionObservation")
                if learner.s.node(n)["attrs"].get("event_id") == receipt.event_id]) == 1
    common, = [n for n in learner.s.nodes("CommonTargetEvidence")
               if learner.s.node(n)["attrs"].get("event_id") == receipt.event_id]
    observation, = [n for n in learner.s.nodes("TransitionObservation")
                    if learner.s.node(n)["attrs"].get("event_id") == receipt.event_id]
    assert learner.s.node(common)["attrs"]["split"] == "training"
    assert learner.s.node(observation)["attrs"]["split"] == "training"
    assert learner.s.node(opportunity)["attrs"]["status"] == "selected"


def test_source_epoch_changes_reopen_question():
    learner, _ = _learner()
    opportunity = _opportunity(learner, "epoch-question")
    learner.settle()
    first, = [n for n in learner.s.nodes("UsefulEvidenceSelection")
              if learner.s.node(n)["attrs"].get("status") == "awaiting_receipt"]
    world = ThermalWorld(object_ids=[learner.s.node(first)["attrs"]["object_id"]])
    receipt = world.apply(learner.s.node(first)["attrs"]["object_id"], "warm")
    learner.observe_world_receipt(receipt, source_epoch=3, model_epoch=2, frame_epoch=5,
                                  split="training")
    learner.settle()
    state = json.dumps(learner.hypotheses(), sort_keys=True)
    _record_outcome(learner, first, receipt, before_state=state, after_state=state,
        before_behavior="same", after_behavior="same")
    assert learner.s.node(opportunity)["attrs"]["status"] == "terminal_no_progress"
    learner.s.set_attr(opportunity, "source_epoch", 4)
    learner.settle()
    selections = learner.s.nodes("UsefulEvidenceSelection")
    assert len(selections) == 2
    new = learner.s.node(selections[-1])["attrs"]
    assert new["opportunity_key"] == "epoch-question"
    assert new["source_epoch"] == 4


def test_useful_evidence_generator_matches_committed_seed_and_defaults_off():
    generated = build_seed()
    assert json.loads(OUT.read_text()) == generated
    assert generated["nodes"][0]["attrs"]["enabled"] == 0.0
    assert {rule["name"] for rule in generated["rules"]} >= {
        "ues_request_shared_budget_for_top_training_opportunity",
        "ues_emit_selected_opportunity_after_budget_approval",
    }
    learner = CommonTargetLearner()
    learner.s._inner.load_seed_manifest(generated, learner.ag)
    _opportunity(learner, "disabled-policy")
    learner.settle()
    assert learner.s.nodes("UsefulEvidenceSelection") == []
