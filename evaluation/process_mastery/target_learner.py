"""Common native target learner adapter for the bounded P20 categorical slice.

The adapter translates world observations into typed graph records and reads
native hypothesis/prediction receipts. It never selects or writes a learned
effect. Source exposure and target interaction accounting remain separate.
"""
from __future__ import annotations

from dataclasses import dataclass

from evaluation.process_mastery.harness import Agent
from evaluation.process_mastery.target_learning_worlds import WorldReceipt

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
    source_map_observations: int = 0
    target_map_interactions: int = 0
    map_verification_queries: int = 0


class NativeTargetLearner:
    """Fresh empty graph plus the P8 receipt-bound effect learner."""

    def __init__(self, *, owner_id="target-owner", budget=100.0, enabled=True,
                 transfer_enabled=False, agent=None):
        self.owner_id = owner_id
        self.agent = agent or Agent(
            extra_seeds=("process_induction", "target_learning"), track_i=False,
            policy_overrides={"ModelLearningPolicy": {"enabled": float(enabled)},
                              "TargetLearningPolicy": {"enabled": float(transfer_enabled)}},
            budget={"enabled": 1.0, "remaining": float(budget),
                    "refill_per_epoch": 0.0, "last_refill_epoch": 10.0},
            profile="p20-native-target-learner")
        self.s = self.agent.s
        self.ag = getattr(self.agent, "ag", getattr(self.agent, "agent", None))
        if self.ag is None:
            raise TypeError("target learner requires an agent root node")
        self.s._inner.load_seed_manifest(TARGET_EXPOSURE_MANIFEST, self.ag)
        self.accounting = LearningAccounting()
        self._ingested_world_receipts: set[str] = set()
        self._ingested_map_pairs: set[str] = set()
        self._ingested_source_map_events: set[str] = set()
        self._ingested_target_map_events: set[str] = set()
        self._pending_learning_records: list[dict] = []
        self.learning_records: list[dict] = []
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

    def import_source_prior(self, *, prior_id: str, source_id: str,
                            action_kind: str, object_type: str, feature_key: str,
                            before_value, after_value, source_epoch=3, model_epoch=2,
                            frame_epoch=5, map_evidence: dict,
                            target_receipt: dict):
        """Translate external verifier records; this method does not verify them."""
        if not map_evidence or not target_receipt:
            raise ValueError("source prior requires independent map and target receipts")
        source_events = set(map_evidence.get("source_events", ()))
        target_events = set(map_evidence.get("target_events", ()))
        new_source_events = source_events - self._ingested_source_map_events
        new_target_events = target_events - self._ingested_target_map_events
        self.accounting.source_map_observations += len(new_source_events)
        self.accounting.source_information_units += float(len(new_source_events))
        self.accounting.target_map_interactions += len(new_target_events)
        self.accounting.target_actions += len(new_target_events)
        self.accounting.map_verification_queries += len(source_events) + len(target_events)
        prior = self.s.add_node("TargetProcessPrior", {
            "prior_id": prior_id, "source_id": source_id, "owner_id": self.owner_id,
            "action_kind": action_kind, "object_type": object_type,
            "feature_key": feature_key, "before_value": before_value,
            "after_value": after_value, "source_epoch": int(source_epoch),
            "model_epoch": int(model_epoch), "frame_epoch": int(frame_epoch),
            "status": "candidate"})
        frame_map = self.s.add_node("RepresentationMap", dict(map_evidence))
        map_receipt = self.s.add_node("TargetSourcePriorReceipt", {
            "receipt_id": f"map:{prior_id}", "receipt_kind": "source_target_map",
            "map_id": map_evidence.get("map_id"), "status": map_evidence.get("status")})
        effect_receipt = self.s.add_node("TargetSourcePriorReceipt", {
            **target_receipt, "receipt_kind": "target_prior_effect"})
        self.s.add_edge(self.ag, "has_target_source_prior", prior, {})
        self.s.add_edge(prior, "has_source_target_map", frame_map, {})
        self.s.add_edge(prior, "has_source_prior_receipt", map_receipt, {})
        self.s.add_edge(prior, "has_source_prior_receipt", effect_receipt, {})
        return prior

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
            self.learning_records.append({"event_id": event_id, "status": "not_observed",
                                          "hypothesis_count": len(self.hypotheses())})
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
        self._pending_learning_records.append({"event_id": event_id,
                                               "observation_status": "observed"})
        return observation

    def observe_world_receipt(self, receipt: WorldReceipt, *, source_epoch=3,
                              model_epoch=2, frame_epoch=5, action_occurred=True):
        """Ingest an actual simulator receipt; reject replay and unauthorized data."""
        if not isinstance(receipt, WorldReceipt):
            raise TypeError("target learner requires a typed WorldReceipt")
        if receipt.status != "observed" or not receipt.action_authorized:
            raise ValueError("target evidence requires an authorized observed action")
        if receipt.event_id in self._ingested_world_receipts:
            raise ValueError("world receipt already ingested")
        self._ingested_world_receipts.add(receipt.event_id)
        return self.observe_opportunity(
            event_id=receipt.event_id, action_kind=receipt.action_kind,
            object_id=receipt.object_id, object_type=receipt.object_type,
            feature_key=receipt.feature_key, before_value=receipt.before_value,
            after_value=receipt.after_value, source_epoch=source_epoch,
            model_epoch=model_epoch, frame_epoch=frame_epoch,
            visible=True, action_occurred=action_occurred)

    def observe_map_pair(self, *, pair_id: str, source: WorldReceipt,
                         target: WorldReceipt, source_epoch=3, target_frame_epoch=5):
        """Expose one paired source/target interaction to native map induction."""
        if not isinstance(source, WorldReceipt) or not isinstance(target, WorldReceipt):
            raise TypeError("map induction requires typed source and target world receipts")
        if (pair_id in self._ingested_map_pairs
                or source.event_id in self._ingested_source_map_events
                or target.event_id in self._ingested_target_map_events):
            raise ValueError("paired map evidence already ingested")
        if (source.status != "observed" or target.status != "observed"
                or not source.action_authorized or not target.action_authorized):
            raise ValueError("map induction requires authorized observed receipt pairs")
        self._ingested_map_pairs.add(pair_id)
        self._ingested_source_map_events.add(source.event_id)
        self._ingested_target_map_events.add(target.event_id)
        observation = self.s.add_node("TargetMapObservation", {
            "pair_id": str(pair_id), "source_event_id": source.event_id,
            "target_event_id": target.event_id,
            "source_object_id": source.object_id, "target_object_id": target.object_id,
            "source_action": source.action_kind, "target_action": target.action_kind,
            "source_object_type": source.object_type,
            "target_object_type": target.object_type,
            "source_feature": source.feature_key, "target_feature": target.feature_key,
            "source_before": source.before_value, "target_before": target.before_value,
            "source_after": source.after_value, "target_after": target.after_value,
            "source_epoch": int(source_epoch),
            "target_frame_epoch": int(target_frame_epoch),
            "status": "observed_pair"})
        self.s.add_edge(self.ag, "has_target_map_observation", observation, {})
        funding = self.s.add_node("ThinkingBudgetRequest", {
            "requester_kind": "target_map_observation", "source_key": str(pair_id),
            "source_epoch": int(source_epoch), "requested_epoch": 10.0,
            "operation_id": f"target-map:{pair_id}", "status": "pending", "cost": 1.0})
        self.s.add_edge(self.ag, "has_thinking_budget_request", funding, {})
        budget_nodes = self.s.neighbours(self.ag, "has_thinking_budget")
        if len(budget_nodes) != 1:
            raise RuntimeError("target map induction requires one shared thinking budget")
        self.s.add_edge(funding, "draws_on_thinking_budget", budget_nodes[0], {})
        self.s.add_edge(observation, "funded_by", funding, {})
        self.accounting.source_map_observations += 1
        self.accounting.target_map_interactions += 1
        self.accounting.source_information_units += 1.0
        self.accounting.target_actions += 1
        return observation

    def settle(self, *, max_rounds=40, steps_per_round=2000):
        steps = 0
        for _ in range(max_rounds):
            if hasattr(self.agent, "inner"):
                # A cognition-on WorldAdapter schedules a limited cognitive
                # cycle on tick(); explicit phase settlement must execute the
                # native rules in this shared graph, as its profile tests do.
                used = int(self.agent.inner.run_rules(steps_per_round))
            else:
                used = int(self.s.tick(steps_per_round))
            steps += used
            if used == 0:
                self.accounting.native_rule_steps += steps
                hypotheses = self.hypotheses()
                for record in self._pending_learning_records:
                    self.learning_records.append({
                        **record, "status": "settled",
                        "hypothesis_count": len(hypotheses),
                        "hypothesis_keys": [row.get("hypothesis_key") for row in hypotheses],
                        "native_rule_steps": steps,
                    })
                self._pending_learning_records.clear()
                return steps
        raise RuntimeError("native target learner exceeded rule-step bound")

    def hypotheses(self):
        return [self.s.node(node)["attrs"] for node in self.s.nodes("ProcessInductionHypothesis")
                if self.s.node(node)["attrs"].get("status") != "consolidated_source"]

    def predict(self, *, query_id, action_kind, object_type, feature_key,
                before_value, object_id, source_epoch=3, model_epoch=2, frame_epoch=5,
                split: str | None = None):
        if split is not None and split not in {"training", "development", "validation", "heldout"}:
            raise ValueError("prediction split is invalid")
        query_attrs = {
            "query_id": query_id, "owner_id": self.owner_id, "object_id": object_id,
            "object_type": object_type, "action_kind": action_kind,
            "feature_key": feature_key, "before_value": before_value,
            "source_epoch": int(source_epoch), "model_epoch": int(model_epoch),
            "frame_epoch": int(frame_epoch), "status": "pending"}
        if split is not None:
            query_attrs["split"] = split
        query = self.s.add_node("ProcessPredictionQuery", query_attrs)
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


def build_target_learner(adapter_factory, *, arm: str, **kwargs):
    """Fail closed when an evaluation arm lacks the common target learner."""
    if not callable(adapter_factory):
        raise RuntimeError(f"missing target learner adapter for arm {arm}")
    learner = adapter_factory(**kwargs)
    required = ("observe_world_receipt", "predict", "settle", "graph_footprint")
    missing = [name for name in required if not callable(getattr(learner, name, None))]
    if missing:
        raise RuntimeError(f"incomplete target learner adapter for arm {arm}: {missing}")
    return learner
