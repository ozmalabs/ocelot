"""P24.03 candidate-only source proposal and ordinary-learning fallback."""
import json

from evaluation.process_mastery.common_target_learner import CommonTargetLearner
from evaluation.process_mastery.target_learning_worlds import HeatSourceWorld, ThermalWorld
from scripts.gen_additive_transfer_seed import OUT, build_seed


def _receipt(i, *, after="warm"):
    if after == "warm":
        world = ThermalWorld(object_ids=[f"sample-{i}"])
        return world.apply(f"sample-{i}", "warm")
    from evaluation.process_mastery.target_learning_worlds import WorldReceipt
    return WorldReceipt(f"thermal:{i}:sample-{i}", f"sample-{i}", "ThermalSample",
                        "warm", "temperature", "cold", after, "observed", True, i)


def _propose(learner, *, effect="warm", verified=True, prior_id="source-prior"):
    learner.propose_source_model(
        prior_id=prior_id, source_id="source-model", action_kind="warm",
        object_type="ThermalSample", feature_key="temperature",
        before_value="cold", after_value=effect,
        map_evidence={"map_id": f"map:{prior_id}",
                      "status": "verified" if verified else "rejected",
                      "mapping_kind": "exact_categorical_effect",
                      "target_frame_epoch": 5,
                      "source_events": ["source:1", "source:2"],
                      "target_events": ["thermal:1:sample-1", "thermal:2:sample-2"]},
        target_receipt={"receipt_id": f"target-prior:{prior_id}",
                        "receipt_kind": "target_prior_effect",
                        "source_prior_id": prior_id,
                        "target_event_id": "thermal:1:sample-1",
                        "status": "verified" if verified else "rejected",
                        "exact_effect_match": bool(verified)},
        source_epoch=3, model_epoch=2, frame_epoch=5)


def _learn_two(learner):
    for i in (1, 2):
        learner.observe_world_receipt(_receipt(i))
    learner.settle()


def test_additive_seed_is_deterministic_and_disabled_by_default():
    assert json.loads(OUT.read_text()) == build_seed()
    learner = CommonTargetLearner()
    assert learner.s.node(learner.s.nodes("AdditiveTransferPolicy")[0])["attrs"]["enabled"] == 0.0


def test_source_changes_candidate_portfolio():
    learner = CommonTargetLearner(additive_transfer_enabled=True)
    learner.observe_world_receipt(_receipt(1))
    _propose(learner)
    learner.settle()
    priors = [learner.s.node(n)["attrs"] for n in learner.s.nodes("TargetProcessPrior")]
    assert len(priors) == 1
    assert priors[0]["prior_id"] == "source-prior"
    source_hypotheses = [h for h in learner.hypotheses()
                         if h.get("source_prior_id") == "source-prior"]
    assert len(source_hypotheses) == 1
    assert source_hypotheses[0]["law_kind"] == "mapped_source_prior_confirmed"


def test_typed_common_map_pairs_induce_a_funded_native_candidate():
    learner = CommonTargetLearner(additive_transfer_enabled=True)
    source = HeatSourceWorld(sample_ids=("source-a", "source-b"))
    target = ThermalWorld(object_ids=("target-a", "target-b"))
    source_receipts, target_receipts = [], []
    for index, (source_id, target_id) in enumerate(
            (("source-a", "target-a"), ("source-b", "target-b")), 1):
        src = source.apply_heat(source_id, "apply_heat")
        tgt = target.apply(target_id, "warm")
        source_receipts.append(src)
        target_receipts.append(tgt)
        learner.observe_world_receipt(tgt, map_view={
            "pair_id": f"common-map-{index}", "source_receipt": src})
    learner.settle()
    candidates = [learner.s.node(n)["attrs"] for n in learner.s.nodes("RepresentationMap")
                  if learner.s.node(n)["attrs"].get("mapping_kind") == "induced_categorical_effect"]
    assert len(candidates) == 1
    assert candidates[0]["status"] == "candidate"
    map_requests = [n for n in learner.s.nodes("ThinkingBudgetRequest")
                    if learner.s.node(n)["attrs"].get("requester_kind")
                    == "target_map_observation"]
    assert len(map_requests) == 2
    assert all(learner.s.node(n)["attrs"]["status"] == "approved"
               for n in map_requests)
    assert learner.accounting.target_actions == 2
    assert len(learner.s.nodes("TransitionObservation")) == 2


def test_target_counterexample_overrides_bad_prior():
    learner = CommonTargetLearner(additive_transfer_enabled=True)
    for i in (1, 2):
        learner.observe_world_receipt(_receipt(i))
    _propose(learner, effect="cold", verified=False, prior_id="bad-prior")
    learner.settle()
    ordinary = [h for h in learner.hypotheses() if not h.get("source_prior_id")]
    assert len(ordinary) == 1
    assert ordinary[0]["after_value"] == "warm"
    learner.observe_world_receipt(_receipt(3, after="cold"))
    learner.settle()
    ordinary = [h for h in learner.hypotheses() if not h.get("source_prior_id")]
    assert ordinary[0]["status"] == "disputed"
    assert not learner.s.nodes("TargetProcessPrior")
    assert any(learner.s.node(n)["attrs"]["status"] == "candidate"
               for n in learner.s.nodes("SourceModelProposal"))


def test_no_map_still_learns():
    learner = CommonTargetLearner(additive_transfer_enabled=True)
    for i in (1, 2):
        learner.observe_world_receipt(_receipt(i))
    learner.propose_source_model(
        prior_id="unmapped", source_id="source-model", action_kind="warm",
        object_type="ThermalSample", feature_key="temperature",
        before_value="cold", after_value="warm", map_evidence=None,
        target_receipt=None)
    learner.settle()
    assert len(learner.hypotheses()) == 1
    assert learner.hypotheses()[0]["after_value"] == "warm"
    assert not learner.s.nodes("TargetProcessPrior")


def test_prior_knockout_changes_only_source_path():
    fresh = CommonTargetLearner()
    mapped = CommonTargetLearner(additive_transfer_enabled=True)
    for learner in (fresh, mapped):
        for i in (1, 2):
            learner.observe_world_receipt(_receipt(i))
        learner.settle()
    _propose(mapped)
    fresh.settle()
    mapped.settle()
    fresh_obs = [fresh.s.node(n)["attrs"] for n in fresh.s.nodes("TransitionObservation")]
    mapped_obs = [mapped.s.node(n)["attrs"] for n in mapped.s.nodes("TransitionObservation")]
    assert fresh_obs == mapped_obs
    assert fresh.accounting.target_actions == mapped.accounting.target_actions == 2
    fresh_ordinary = [h for h in fresh.hypotheses() if not h.get("source_prior_id")]
    mapped_ordinary = [h for h in mapped.hypotheses() if not h.get("source_prior_id")]
    assert fresh_ordinary == mapped_ordinary
    assert len(mapped.s.nodes("TargetProcessPrior")) == 1
    prior = mapped.s.node(mapped.s.nodes("TargetProcessPrior")[0])["attrs"]
    assert prior["status"] == "portfolio_candidate"
    assert len(mapped.hypotheses()) == len(fresh.hypotheses())
    assert len(fresh.s.nodes("TargetProcessPrior")) == 0
