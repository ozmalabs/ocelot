"""P18 latent inference from receipts produced by an independent temporal world."""
import json
from pathlib import Path

from substrate_rs import _native
from evaluation.process_mastery.observed_worlds import ObservedWorld
from scripts.gen_process_induction_seed import build_seed as process_seed
from scripts.gen_latent_process_seed import build_seed as latent_seed

ROOT = Path(__file__).resolve().parents[1]


def _boot(enabled=True):
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    for name in ("default_mode_core", "thinking_budget", "cognition_signature",
                 "experience_signature"):
        s.load_seed_manifest(json.loads((ROOT / "seeds" / f"{name}.json").read_text()), ag)
    for seed in (process_seed(), latent_seed()):
        result = s.load_seed_manifest(seed, ag)
        assert result["rules_skipped"] == [], result
    for budget in s.nodes("ThinkingBudget"):
        for key, value in {"enabled": 1.0, "remaining": 100.0,
                           "last_refill_epoch": 10.0}.items():
            s.set_attr(budget, key, value)
    s.set_attr(s.nodes("NetworkModeState")[0], "epoch", 10.0)
    s.set_attr(s.nodes("LatentProcessPolicy")[0], "enabled", float(enabled))
    return s, ag


def _tick(s):
    for _ in range(40):
        if not s.run_rules(4000):
            return
    raise AssertionError("latent observed-world rules did not reach a fixpoint")


def _record(s, ag, receipt, index, *, regular=True, complete=True):
    event = f"temporal-{index:03d}"
    common = {"owner_id": "owner-a", "episode_id": f"episode-{index}",
        "event_id": event, "source_epoch": 3, "model_epoch": 2, "frame_epoch": 5,
        "status": "observed"}
    transition = s.add_node("TransitionObservation", common)
    residual = s.add_node("ObservedPredictionResidual", {**common,
        "window_id": f"window-{index:03d}", "residual_key": "temporal-outcome",
        "feature_key": "visible-cue", "observed_feature_value": receipt["cue"],
        "predicted_outcome": "neutral", "residual_outcome": receipt["observed_outcome"],
        "sampling_interval": receipt["sampling_interval"],
        "regular_sampling": regular, "complete_window": complete})
    s.add_edge(ag, "has_transition_observation", transition)
    s.add_edge(ag, "has_prediction_residual", residual)
    s.add_edge(residual, "residual_from_transition", transition)
    return residual


def test_latent_predicts_new_intervention_from_verified_world_receipts():
    world = ObservedWorld.create("temporal_latent", 8801)
    s, ag = _boot()
    for index in range(3):
        obs = world.observe_temporal(index)
        receipt = world.execute_temporal(obs)
        assert world.verify_temporal_receipt(receipt)
        assert "_latent_map" not in obs and "observed_outcome" not in obs
        _record(s, ag, receipt, index)
        _tick(s)
    candidates = s.nodes("LatentProcessCandidate")
    assert len(candidates) == 1
    assert s.node(candidates[0])["attrs"]["status"] == "proposed"

    fresh = world.observe_temporal(3)
    result = world.execute_temporal(fresh)
    assert world.verify_temporal_receipt(result)
    _record(s, ag, result, 3)
    _tick(s)
    assert s.node(candidates[0])["attrs"]["status"] == "validated"
    assert len(s.neighbours(candidates[0], "has_latent_validation")) == 1


def test_irregular_or_incomplete_temporal_receipts_abstain():
    world = ObservedWorld.create("temporal_latent", 8801)
    s, ag = _boot()
    for index in range(3):
        obs = world.observe_temporal(index)
        receipt = world.execute_temporal(obs)
        assert world.verify_temporal_receipt(receipt)
        _record(s, ag, receipt, index, regular=False if index == 1 else True,
                complete=False if index == 2 else True)
    _tick(s)
    assert not s.nodes("LatentProcessCandidate")
