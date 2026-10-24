"""P24 opt-in graph-native fan-out of one authorized target receipt."""
from __future__ import annotations

from substrate.boot_core import installed_seeds
from evaluation.process_mastery.target_learner import NativeTargetLearner
from evaluation.process_mastery.target_learning_worlds import WorldReceipt
from scripts.gen_additive_transfer_seed import build_seed as build_additive_seed
from scripts.gen_common_target_evidence_seed import build_seed


class CommonTargetLearner(NativeTargetLearner):
    """Transport receipts into graph ingress nodes; rules create all learning views."""

    def __init__(self, *, owner_id="target-owner", budget=100.0,
                 enabled=True, policy_enabled=True, additive_transfer_enabled=False,
                 agent=None):
        super().__init__(owner_id=owner_id, budget=budget, enabled=enabled,
                         transfer_enabled=additive_transfer_enabled, agent=agent)
        installed = installed_seeds(self.s)
        # cognition-on's full profile records its seed closure as SeedSummary
        # nodes; lightweight evaluation agents use graph-resident Seed nodes.
        installed_ids = set(installed)
        installed_ids.update(self.s.node(n)["attrs"].get("seed_id")
                             for n in self.s.nodes("SeedSummary"))
        existing_rules = {rule.get("name") for rule in self.s._inner.export_rules()
                          if rule.get("name")}
        common_manifest = build_seed()
        common_rule_names = {rule.get("name") for rule in common_manifest.get("rules", ())
                             if rule.get("name")}
        if ("common_target_evidence" not in installed_ids
                and not common_rule_names.issubset(existing_rules)):
            loaded = self.s._inner.load_seed_manifest(common_manifest, self.ag)
            if loaded.get("rules_skipped"):
                raise RuntimeError(f"common target seed rules skipped: {loaded['rules_skipped']}")
        for policy in self.s.nodes("CommonTargetEvidencePolicy"):
            self.s.set_attr(policy, "enabled", float(policy_enabled))
        existing_rules = {rule.get("name") for rule in self.s._inner.export_rules()
                          if rule.get("name")}
        additive_manifest = build_additive_seed()
        additive_rule_names = {rule.get("name") for rule in additive_manifest.get("rules", ())
                               if rule.get("name")}
        if ("additive_transfer" not in installed_ids
                and not additive_rule_names.issubset(existing_rules)):
            additive_loaded = self.s._inner.load_seed_manifest(additive_manifest, self.ag)
            if additive_loaded.get("rules_skipped"):
                raise RuntimeError(f"additive transfer seed rules skipped: {additive_loaded['rules_skipped']}")
        for policy in self.s.nodes("ModelLearningPolicy"):
            self.s.set_attr(policy, "enabled", float(enabled))
        for policy in self.s.nodes("TargetLearningPolicy"):
            self.s.set_attr(policy, "enabled", float(additive_transfer_enabled))
        for policy in self.s.nodes("AdditiveTransferPolicy"):
            self.s.set_attr(policy, "enabled", float(additive_transfer_enabled))

    def observe_world_receipt(self, receipt: WorldReceipt, *, source_epoch=3,
                              model_epoch=2, frame_epoch=5, action_occurred=True,
                              map_view: dict | None = None):
        if not isinstance(receipt, WorldReceipt):
            raise TypeError("target learner requires a typed WorldReceipt")
        if receipt.status != "observed" or not receipt.action_authorized:
            raise ValueError("target evidence requires an authorized observed action")
        event_attrs = {
            "owner_id": self.owner_id, "episode_id": f"target-episode:{receipt.event_id}",
            "event_id": receipt.event_id, "source_epoch": int(source_epoch),
            "model_epoch": int(model_epoch), "frame_epoch": int(frame_epoch),
            "object_id": receipt.object_id, "object_type": receipt.object_type,
            "action_kind": receipt.action_kind, "feature_key": receipt.feature_key,
            "before_value": receipt.before_value, "after_value": receipt.after_value,
            "status": "observed", "action_authorized": True,
            "action_occurred": bool(action_occurred),
            "map_requested": bool(map_view),
        }
        if map_view:
            source_receipt = map_view.get("source_receipt")
            if source_receipt is not None and not isinstance(source_receipt, WorldReceipt):
                raise TypeError("map view source must be a typed WorldReceipt")
            source_fields = ({
                "source_event_id": source_receipt.event_id,
                "source_status": source_receipt.status,
                "source_action_authorized": bool(source_receipt.action_authorized),
                "source_object_id": source_receipt.object_id,
                "source_action": source_receipt.action_kind,
                "source_object_type": source_receipt.object_type,
                "source_feature": source_receipt.feature_key,
                "source_before": source_receipt.before_value,
                "source_after": source_receipt.after_value,
                "map_source_epoch": int(map_view.get("source_epoch", source_epoch)),
            } if source_receipt is not None else {
                key: map_view[key] for key in (
                    "source_event_id", "source_object_id", "source_action",
                    "source_object_type", "source_feature", "source_before",
                    "source_after") if key in map_view
            })
            if source_receipt is None:
                source_fields.update({k: map_view[k] for k in (
                    "source_status", "source_action_authorized", "map_source_epoch")
                    if k in map_view})
            event_attrs.update(source_fields)
            event_attrs.update({
                "map_pair_id": str(map_view["pair_id"]),
            })
        identity_fields = ("owner_id", "episode_id", "event_id", "source_epoch",
                           "model_epoch", "frame_epoch", "object_id", "object_type",
                           "action_kind", "feature_key", "before_value", "after_value")
        existing = [n for n in self.s.nodes("CommonTargetEvidence")
                    if self.s.node(n)["attrs"].get("event_id") == receipt.event_id]
        if existing:
            # Replays cannot add another target action/support item. Optional
            # map transport is attached to the same event node if supplied later.
            attrs = self.s.node(existing[0])["attrs"]
            if any(attrs.get(k) != event_attrs.get(k) for k in identity_fields):
                raise ValueError("event ID replay has conflicting target receipt")
            if map_view:
                if attrs.get("map_requested"):
                    if attrs.get("map_pair_id") != event_attrs["map_pair_id"]:
                        raise ValueError("event ID replay has conflicting map pair")
                else:
                    for key, value in event_attrs.items():
                        if key.startswith("source_") or key in {"map_pair_id", "map_requested"}:
                            self.s.set_attr(existing[0], key, value)
            return existing[0]
        ingress = self.s.add_node("CommonTargetEvidence", event_attrs)
        self.s.add_edge(self.ag, "has_common_target_evidence", ingress, {})
        self.accounting.evidence_opportunities += 1
        self.accounting.visible_observations += 1
        if action_occurred:
            self.accounting.target_actions += 1
        self._pending_learning_records.append({"event_id": receipt.event_id,
                                               "observation_status": "observed"})
        return ingress

    def propose_source_model(self, *, prior_id: str, source_id: str,
                             action_kind: str, object_type: str, feature_key: str,
                             before_value, after_value, map_evidence: dict | None,
                             target_receipt: dict | None, source_epoch=3,
                             model_epoch=2, frame_epoch=5):
        """Mechanically attach a source proposal and verifier records to the graph.

        Eligibility is decided by the opt-in native rule. Missing, rejected or
        pending verifier records remain visible proposals and cannot suppress
        the common ordinary target path.
        """
        proposal = self.s.add_node("SourceModelProposal", {
            "prior_id": str(prior_id), "source_id": str(source_id),
            "owner_id": self.owner_id, "action_kind": action_kind,
            "object_type": object_type, "feature_key": feature_key,
            "before_value": before_value, "after_value": after_value,
            "source_epoch": int(source_epoch), "model_epoch": int(model_epoch),
            "frame_epoch": int(frame_epoch),
            "target_event_id": (target_receipt or {}).get("target_event_id"),
            "status": "candidate"})
        self.s.add_edge(self.ag, "has_source_model_proposal", proposal, {})
        if map_evidence:
            map_attrs = dict(map_evidence)
            map_id = map_attrs.get("map_id")
            map_node = self.s.add_node("RepresentationMap", map_attrs)
            self.s.add_edge(proposal, "uses_verified_map", map_node, {})
            map_receipt = self.s.add_node("TargetSourcePriorReceipt", {
                "receipt_id": f"map:{prior_id}", "receipt_kind": "source_target_map",
                "map_id": map_id, "status": map_attrs.get("status")})
            self.s.add_edge(proposal, "has_map_verification", map_receipt, {})
            self.accounting.map_verification_queries += len(map_attrs.get("source_events", ()))
            self.accounting.map_verification_queries += len(map_attrs.get("target_events", ()))
            self.accounting.source_map_observations += len(map_attrs.get("source_events", ()))
            self.accounting.source_information_units += float(len(map_attrs.get("source_events", ())))
            self.accounting.target_map_interactions += len(map_attrs.get("target_events", ()))
        if target_receipt:
            receipt_attrs = dict(target_receipt)
            receipt_attrs.setdefault("receipt_kind", "target_prior_effect")
            self.s.add_edge(proposal, "has_target_effect_verification",
                            self.s.add_node("TargetSourcePriorReceipt", receipt_attrs), {})
        return proposal


def build_common_target_learner(**kwargs):
    return CommonTargetLearner(**kwargs)
