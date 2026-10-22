"""Common native target learner adapter for the bounded P20 categorical slice.

The adapter translates world observations into typed graph records and reads
native hypothesis/prediction receipts. It never selects or writes a learned
effect. Source exposure and target interaction accounting remain separate.
"""
from __future__ import annotations

from dataclasses import dataclass

from evaluation.process_mastery.harness import Agent

TARGET_EXPOSURE_MANIFEST = {
    "id": "p20_target_evidence_adapter", "version": "1.0.0", "depends_on": [],
    "productions": [{
        "provenance": "p20:has_target_source_exposure",
        "src": {"type": "Agent", "var": "src"},
        "edge_type": "has_target_source_exposure",
        "tgt": {"type": "TargetSourceExposure", "var": "tgt"},
    }],
}


@dataclass
class LearningAccounting:
    evidence_opportunities: int = 0
    visible_observations: int = 0
    missing_observations: int = 0
    target_actions: int = 0
    source_information_units: float = 0.0
    native_rule_steps: int = 0


class NativeTargetLearner:
    """Fresh empty graph plus the P8 receipt-bound effect learner."""

    def __init__(self, *, owner_id="target-owner", budget=100.0, enabled=True):
        self.owner_id = owner_id
        self.agent = Agent(
            extra_seeds=("process_induction",), track_i=False,
            policy_overrides={"ModelLearningPolicy": {"enabled": float(enabled)}},
            budget={"enabled": 1.0, "remaining": float(budget),
                    "refill_per_epoch": 0.0, "last_refill_epoch": 10.0},
            profile="p20-native-target-learner")
        self.s = self.agent.s
        self.ag = self.agent.ag
        self.s._inner.load_seed_manifest(TARGET_EXPOSURE_MANIFEST, self.ag)
        self.accounting = LearningAccounting()
        for node in self.s.nodes("NetworkModeState"):
            self.s.set_attr(node, "epoch", 10.0)

    def expose_source(self, *, source_id: str, relation: str, units: float = 1.0):
        """Record charged source information without treating it as target data."""
        if relation not in {"matched", "mismatched", "unmapped"}:
            raise ValueError("source relation must be matched, mismatched, or unmapped")
        exposure = self.s.add_node("TargetSourceExposure", {
            "source_id": source_id, "relation": relation, "units": float(units),
            "status": "observed", "source_only": True})
        self.s.add_edge(self.ag, "has_target_source_exposure", exposure, {})
        self.accounting.source_information_units += float(units)
        return exposure

    def observe_opportunity(self, *, event_id: str, owner_id: str | None = None,
                            episode_id: str | None = None, action_kind: str | None = None,
                            object_id: str | None = None, object_type: str | None = None,
                            feature_key: str | None = None, before_value=None,
                            after_value=None, source_epoch=3, model_epoch=2,
                            frame_epoch=5, visible=True, action_occurred=True):
        """Ingest one opportunity; absent observation creates no effect record."""
        self.accounting.evidence_opportunities += 1
        if not visible:
            self.accounting.missing_observations += 1
            return None
        if any(value is None for value in
               (action_kind, object_id, object_type, feature_key, before_value, after_value)):
            raise ValueError("visible target evidence requires the full typed transition")
        owner_id = owner_id or self.owner_id
        episode_id = episode_id or f"target-episode:{event_id}"
        common = {"owner_id": owner_id, "episode_id": episode_id,
                  "event_id": event_id, "source_epoch": int(source_epoch),
                  "model_epoch": int(model_epoch), "frame_epoch": int(frame_epoch),
                  "status": "observed"}
        observation = self.s.add_node("TransitionObservation", {
            **common, "object_id": object_id, "object_type": object_type,
            "action_kind": action_kind, "feature_key": feature_key,
            "before_value": before_value, "after_value": after_value})
        action = self.s.add_node("TransitionActionReceipt", dict(common))
        outcome = self.s.add_node("TransitionOutcomeReceipt", dict(common))
        self.s.add_edge(self.ag, "has_transition_observation", observation, {})
        self.s.add_edge(observation, "has_action_receipt", action, {})
        self.s.add_edge(observation, "has_outcome_receipt", outcome, {})
        self.accounting.visible_observations += 1
        if action_occurred:
            self.accounting.target_actions += 1
        return observation

    def settle(self, *, max_rounds=40, steps_per_round=2000):
        steps = 0
        for _ in range(max_rounds):
            used = int(self.s.tick(steps_per_round))
            steps += used
            if used == 0:
                self.accounting.native_rule_steps += steps
                return steps
        raise RuntimeError("native target learner exceeded rule-step bound")

    def hypotheses(self):
        return [self.s.node(node)["attrs"] for node in self.s.nodes("ProcessInductionHypothesis")]

    def predict(self, *, query_id, action_kind, object_type, feature_key,
                before_value, object_id, source_epoch=3, model_epoch=2, frame_epoch=5):
        query = self.s.add_node("ProcessPredictionQuery", {
            "query_id": query_id, "owner_id": self.owner_id, "object_id": object_id,
            "object_type": object_type, "action_kind": action_kind,
            "feature_key": feature_key, "before_value": before_value,
            "source_epoch": int(source_epoch), "model_epoch": int(model_epoch),
            "frame_epoch": int(frame_epoch), "status": "pending"})
        self.s.add_edge(self.ag, "has_process_prediction_query", query, {})
        self.settle()
        matches = [self.s.node(node)["attrs"] for node in self.s.nodes("ProcessPrediction")
                   if self.s.node(node)["attrs"].get("query_id") == query_id]
        return matches[0] if len(matches) == 1 else None

    def graph_footprint(self):
        import json
        nodes = list(self.s.nodes())
        payload = [self.s.node(node) for node in nodes]
        return {"nodes": len(nodes), "bytes": len(json.dumps(payload, sort_keys=True,
                                                               default=str).encode())}
