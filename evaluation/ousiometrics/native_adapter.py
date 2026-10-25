"""Opt-in adapter from validated world observations to shared native consumers.

The adapter is mechanical: it checks the external numeric boundary, configures
one explicit frame, and transports graph outputs as typed receipts. It never
chooses a world action. Prediction evidence is read from native P24 nodes.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from numbers import Real
from typing import Iterable

from evaluation.process_mastery.common_target_learner import CommonTargetLearner
from evaluation.process_mastery.harness import Agent
from evaluation.process_mastery.target_learning_worlds import WorldReceipt as TargetReceipt
from evaluation.ousiometrics.worlds import WorldReceipt as OusiometricWorldReceipt

ROOT = Path(__file__).resolve().parents[2]
FRAME_SEED = ROOT / "seeds" / "ousiometric_frames.json"
ACQUISITION_SEED = ROOT / "seeds" / "ousiometric_acquisition.json"
CONSUMER_LINK_MANIFEST = {
    "id": "ousiometric_native_consumer_links", "version": "1.0.0",
    "depends_on": ["ousiometric_frames", "qualia_behavior"],
    "self_load_only": True,
    "productions": [
        {"provenance": "p28:experience_event_uses_frame_projection",
         "src": {"type": "ExperienceEvent", "var": "src"},
         "edge_type": "uses_ousiometric_projection",
         "tgt": {"type": "OusiometricFrameProjection", "var": "tgt"}},
        {"provenance": "p28:experience_feature_derived_from_frame_projection",
         "src": {"type": "ExperienceFeatureObservation", "var": "src"},
         "edge_type": "derived_from_frame_projection",
         "tgt": {"type": "OusiometricFrameProjection", "var": "tgt"}},
    ],
}


def validate_coordinates(values: Iterable[Real]) -> tuple[float, float, float]:
    """Validate the untrusted simulator/API boundary before graph insertion."""
    if isinstance(values, (str, bytes)):
        raise ValueError("coordinates must be a numeric sequence")
    try:
        raw = tuple(values)
    except TypeError as exc:
        raise ValueError("coordinates must be a numeric sequence") from exc
    if len(raw) != 3:
        raise ValueError("exactly three coordinates are required")
    result = []
    for value in raw:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError("coordinates must be real numeric values")
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("coordinates must be finite")
        if number < -0.5 or number > 0.5:
            raise ValueError("coordinates are outside declared [-0.5, 0.5] units")
        result.append(number)
    return tuple(result)  # type: ignore[return-value]


def _manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class ProjectedReceipt:
    event_id: str
    frame_id: str
    raw_node: int
    projection_node: int
    projected: tuple[float, float, float]
    source_coordinates: tuple[float, float, float]
    verified: bool


class NativeOusiometricInvestigation:
    """One explicit frame plus the same P24 learner/consumer in every arm."""

    def __init__(self, frame_id: str, *, owner_id: str = "ousiometric-owner",
                 source_epoch: int = 3, model_epoch: int = 2,
                 budget: float = 1000.0, enabled: bool = True):
        frames = [n["attrs"] for n in _manifest(FRAME_SEED)["nodes"]
                  if n["type"] == "OusiometricFrame"]
        frame = next((f for f in frames if f["frame_id"] == frame_id), None)
        if frame is None:
            raise ValueError(f"unknown registered frame: {frame_id}")
        self.frame = frame
        self.frame_id = frame_id
        self.owner_id = owner_id
        self.source_epoch = int(source_epoch)
        self.model_epoch = int(model_epoch)
        # Explicit non-default profile: P17/P24 dependencies are loaded as
        # closed seeds. The P28 acquisition policy remains unavailable for
        # selection and is only audited as a loaded, disabled policy.
        self.agent = Agent(extra_seeds=("qualia_acquisition", "qualia_behavior",
                                        "thinking_budget", "process_induction",
                                        "target_learning"),
                          track_i=False, profile="p28-ousiometric-investigation",
                          budget={"enabled": 1.0, "remaining": float(budget),
                                  "refill_per_epoch": 0.0, "last_refill_epoch": 10.0})
        self.s, self.ag = self.agent.s, self.agent.ag
        frame_manifest = _manifest(FRAME_SEED)
        acquisition_manifest = _manifest(ACQUISITION_SEED)
        for manifest in (frame_manifest, acquisition_manifest):
            result = self.s._inner.load_seed_manifest(manifest, self.ag)
            if result.get("rules_skipped"):
                raise RuntimeError(f"P28 seed rules skipped: {result['rules_skipped']}")
        result = self.s._inner.load_seed_manifest(CONSUMER_LINK_MANIFEST, self.ag)
        if result.get("rules_skipped"):
            raise RuntimeError(f"P28 consumer links failed to load: {result['rules_skipped']}")
        for policy in self.s.nodes("OusiometricFramePolicy"):
            self.s.set_attr(policy, "enabled", float(bool(enabled)))
            self.s.set_attr(policy, "owner_id", owner_id)
            self.s.set_attr(policy, "source_epoch", float(self.source_epoch))
            self.s.set_attr(policy, "model_epoch", float(self.model_epoch))
            self.s.set_attr(policy, "assigned_frame_id", frame_id)
        for policy in self.s.nodes("OusiometricAcquisitionPolicy"):
            self.s.set_attr(policy, "enabled", 0.0)
        for policy in self.s.nodes("QualiaAcquisitionPolicy"):
            self.s.set_attr(policy, "enabled", 1.0)
        for policy in self.s.nodes("QualiaBehaviorPolicy"):
            self.s.set_attr(policy, "enabled", 1.0)
        self.learner = CommonTargetLearner(owner_id=owner_id, budget=budget,
                                          enabled=True, policy_enabled=True,
                                          agent=self.agent)
        self._events: set[str] = set()
        self._query_index = 0
        self.native_steps = 0
        self._frame_node = next(n for n in self.s.nodes("OusiometricFrame")
                                if self.s.node(n)["attrs"].get("frame_id") == frame_id)

    @property
    def loaded_seed_ids(self) -> set[str]:
        from substrate.boot_core import installed_seeds
        result = set(installed_seeds(self.s))
        result.update(self.s.node(n)["attrs"].get("seed_id")
                      for n in self.s.nodes("SeedSummary"))
        result.discard(None)
        return result

    def _ingest_fixture(self, *, event_id: str, episode_id: str, context_id: str,
               coordinates: Iterable[Real], consequence: Iterable[float],
               action_kind: str, object_id: str, object_type: str,
               split: str = "training", action_authorized: bool = True,
               receipt_verified: bool = True, source_epoch: int | None = None,
               model_epoch: int | None = None, frame_epoch: int = 1) -> ProjectedReceipt:
        """Inject a synthetic fixture row; evaluation panels must use world receipts."""
        if not action_authorized or not receipt_verified:
            raise ValueError("fixture row is marked unauthorized or unverified")
        if split in {"validation", "heldout"}:
            raise ValueError("synthetic fixture rows cannot enter validation or held-out splits")
        if split not in {"training", "development", "validation", "heldout"}:
            raise ValueError("unknown evidence split")
        if event_id in self._events:
            raise ValueError("event replay cannot add evidence")
        raw = validate_coordinates(coordinates)
        outcomes = tuple(float(x) for x in consequence)
        if len(outcomes) != 3 or not all(math.isfinite(x) for x in outcomes):
            raise ValueError("three finite consequence coordinates are required")
        source_epoch = self.source_epoch if source_epoch is None else int(source_epoch)
        model_epoch = self.model_epoch if model_epoch is None else int(model_epoch)
        if source_epoch != self.source_epoch or model_epoch != self.model_epoch:
            raise ValueError("observation owner/source/model scope does not match active profile")
        frame = self.frame
        raw_node = self.s.add_node("OusiometricRawEvidence", {
            "owner_id": self.owner_id, "episode_id": episode_id, "context_id": context_id,
            "event_id": event_id, "coordinates": list(raw),
            "coordinate_encoding": "finite_f64_v1", "evidence_status": "observed",
            "receipt_status": "verified", "action_authorized": True,
            "action_kind": action_kind, "object_id": object_id,
            "object_type": object_type, "source_epoch": float(source_epoch),
            "model_epoch": float(model_epoch), "frame_epoch": float(frame_epoch),
            "split": split,
        })
        self.s.add_edge(self.ag, "has_ousiometric_raw_evidence", raw_node, {})
        self._events.add(event_id)
        # Projection itself is performed by the selected native frame rule.
        used = int(self.agent.native.run_rules(2000))
        self.native_steps += used
        candidates = [n for n in self.s.nodes("OusiometricFrameProjection")
                      if self.s.node(n)["attrs"].get("event_id") == event_id
                      and self.s.node(n)["attrs"].get("frame_id") == self.frame_id]
        if len(candidates) != 1:
            raise RuntimeError("selected native frame did not produce exactly one projection")
        projection_node = candidates[0]
        attrs = self.s.node(projection_node)["attrs"]
        projected = tuple(float(x) for x in attrs["projected_coordinates"])
        source_coords = tuple(float(x) for x in attrs["source_coordinates"])
        if attrs.get("status") != "verified_current" or attrs.get("owner_id") != self.owner_id:
            raise RuntimeError("native projection is stale or owner-mismatched")
        if attrs.get("source_epoch") != float(source_epoch) or attrs.get("model_epoch") != float(model_epoch):
            raise RuntimeError("native projection source/model epoch mismatch")
        memory = self.s.add_node("OusiometricMetricMemory", {
            "owner_id": self.owner_id, "event_id": event_id, "frame_id": self.frame_id,
            "frame_epoch": float(frame_epoch), "projected_coordinates": list(projected),
            "action_id": action_kind, "consequence": list(outcomes),
            "evidence_status": "observed", "source_epoch": float(source_epoch),
            "model_epoch": float(model_epoch), "status": "verified_receipt"})
        self.s.add_edge(self.ag, "has_ousiometric_metric_memory", memory, {})
        self.s.add_edge(memory, "uses_projection", projection_node, {})
        self._ingest_p17_observation(
            event_id=event_id, episode_id=episode_id, context_id=context_id,
            projected=projected, consequences=outcomes, action_kind=action_kind,
            frame_epoch=frame_epoch, split=split)
        # The scored consumer is fed only projected coordinates. The raw node
        # has no edge into the target learner and is retained only for audit.
        for axis, (value, outcome) in enumerate(zip(projected, outcomes)):
            receipt = TargetReceipt(
                event_id=f"{event_id}:axis:{axis}", object_id=f"{object_id}:{episode_id}",
                object_type=object_type, action_kind=action_kind,
                feature_key=f"{self.frame_id}:coordinate:{axis}",
                before_value=repr(value), after_value=repr(outcome),
                status="observed", action_authorized=True, world_epoch=int(frame_epoch))
            ingress = self.learner.observe_world_receipt(
                receipt, source_epoch=source_epoch, model_epoch=model_epoch,
                frame_epoch=frame_epoch, split=split)
            self.s.add_edge(ingress, "uses_ousiometric_projection", projection_node, {})
        return ProjectedReceipt(event_id, self.frame_id, raw_node, projection_node,
                               projected, source_coords, bool(receipt_verified))

    def ingest_verified_world_receipt(self, *, world, receipt: OusiometricWorldReceipt,
                                      before_view: dict, split: str = "training") -> ProjectedReceipt:
        """Ingest one native-simulator receipt after checking it against its world.

        `before_view` is the exact observation captured immediately before the
        action. Its measured state must agree with the world-owned receipt's
        before-state. Outcome coordinates come only from the verified receipt.
        """
        if not isinstance(receipt, OusiometricWorldReceipt):
            raise TypeError("P28 ingestion requires a typed world-issued receipt")
        if not callable(getattr(world, "verify_receipt", None)) or not world.verify_receipt(receipt):
            raise ValueError("world rejected receipt verification")
        if not receipt.action_authorized:
            raise ValueError("unauthorized world actions cannot become learning evidence")
        if (before_view.get("family") != receipt.family
                or before_view.get("owner_id") != receipt.owner_id
                or before_view.get("episode_id") != receipt.episode_id
                or before_view.get("context_id") != receipt.context_id):
            raise ValueError("pre-action observation does not match receipt scope")
        measured = before_view.get("measured_state", {})
        expected = ((float(measured["position"]), float(measured["armed"]))
                    if receipt.family == "tool_intervention" else
                    (float(measured["trust"]), float(measured["acknowledged"]))
                    if receipt.family == "social_request_repair" else None)
        if expected is None or tuple(receipt.before) != expected:
            raise ValueError("pre-action measured state does not match verified receipt")
        return self._ingest_fixture(
            event_id=receipt.event_id, episode_id=receipt.episode_id,
            context_id=receipt.context_id, coordinates=before_view.get("coordinates", ()),
            consequence=receipt.raw_coordinates, action_kind=receipt.action,
            object_id=before_view.get("object_id", receipt.episode_id),
            object_type=receipt.family, split=split,
            action_authorized=receipt.action_authorized, receipt_verified=True,
            source_epoch=receipt.source_epoch, model_epoch=receipt.model_epoch,
            frame_epoch=receipt.frame_epoch)

    def _ingest_p17_observation(self, *, event_id: str, episode_id: str,
                                context_id: str, projected: tuple[float, ...],
                                consequences: tuple[float, ...], action_kind: str,
                                frame_epoch: int, split: str) -> None:
        """Translate only native-projected observed values into P17 evidence."""
        if split not in {"training", "development"}:
            return
        ep = self.s.add_node("ExperienceEpisode", {
            "owner_id": self.owner_id, "episode_id": f"{episode_id}:p17",
            "context_id": context_id, "status": "observed", "split": split})
        self.s.add_edge(self.ag, "has_experience_episode", ep, {})
        ev = self.s.add_node("ExperienceEvent", {
            "owner_id": self.owner_id, "episode_id": f"{episode_id}:p17",
            "event_id": f"{event_id}:p17", "action_id": action_kind,
            "status": "observed", "event_role": "training_observation",
            "world_epoch": float(frame_epoch), "source_epoch": float(self.source_epoch),
            "model_epoch": float(self.model_epoch), "frame_epoch": float(frame_epoch),
            "frame_id": self.frame_id})
        self.s.add_edge(ep, "has_experience_event", ev, {})
        for axis, (value, consequence) in enumerate(zip(projected, consequences)):
            feature_id = f"{event_id}:p17:axis:{axis}"
            feature = self.s.add_node("ExperienceFeatureObservation", {
                "owner_id": self.owner_id, "episode_id": f"{episode_id}:p17",
                "event_id": f"{event_id}:p17", "feature_id": feature_id,
                "feature_key": f"{self.frame_id}:coordinate:{axis}",
                "feature_family": "ousiometric_projected_coordinate",
                "feature_value": value, "value_kind": "number", "grain": 0.0,
                "is_missing": False, "source_epoch": float(self.source_epoch),
                "model_epoch": float(self.model_epoch), "frame_epoch": float(frame_epoch),
                "status": "observed"})
            self.s.add_edge(ev, "has_episode_feature", feature, {})
            receipt = self.s.add_node("ExperienceOutcomeReceipt", {
                "owner_id": self.owner_id, "episode_id": f"{episode_id}:p17",
                "event_id": f"{event_id}:p17", "feature_id": feature_id,
                "receipt_id": f"{event_id}:p17:receipt:{axis}",
                "source_epoch": float(self.source_epoch),
                "model_epoch": float(self.model_epoch), "frame_epoch": float(frame_epoch),
                "status": "observed", "evidence_status": "observed",
                "consequence_kind": "observed_effect", "consequence_value": consequence,
                "goal_effect": consequence})
            self.s.add_edge(feature, "has_outcome_receipt", receipt, {})
        self.native_steps += int(self.agent.native.run_rules(5000))

    def authorize_action(self, *, event_id: str, episode_id: str, context_id: str,
                         coordinates: Iterable[Real], available_actions: Iterable[str],
                         source_epoch: int | None = None,
                         model_epoch: int | None = None, frame_epoch: int = 1) -> dict | None:
        """Ask P17 native prediction/authorization rules for a legal action."""
        legal = tuple(str(a) for a in available_actions)
        if not legal:
            return None
        if event_id in self._events:
            raise ValueError("action-query event already used")
        projected, projection_node = self._project_for_query_with_node(coordinates)
        source_epoch = self.source_epoch if source_epoch is None else int(source_epoch)
        model_epoch = self.model_epoch if model_epoch is None else int(model_epoch)
        if source_epoch != self.source_epoch or model_epoch != self.model_epoch:
            raise ValueError("action context owner/source/model scope mismatch")
        ep = self.s.add_node("ExperienceEpisode", {
            "owner_id": self.owner_id, "episode_id": episode_id,
            "context_id": context_id, "status": "observed", "split": "development"})
        self.s.add_edge(self.ag, "has_experience_episode", ep, {})
        ev = self.s.add_node("ExperienceEvent", {
            "owner_id": self.owner_id, "episode_id": episode_id,
            "event_id": event_id, "action_id": "pending-native-choice",
            "status": "observed", "event_role": "fresh_task", "world_epoch": 0.0,
            "source_epoch": float(source_epoch), "model_epoch": float(model_epoch),
            "frame_epoch": float(frame_epoch), "frame_id": self.frame_id})
        self.s.add_edge(ep, "has_experience_event", ev, {})
        self.s.add_edge(ev, "uses_ousiometric_projection", projection_node, {})
        context = self.s.add_node("QualiaActionContext", {
            "owner_id": self.owner_id, "event_id": event_id,
            "source_epoch": float(source_epoch), "world_id": context_id,
            "world_epoch": 0.0, "legal_actions": list(legal), "status": "active"})
        self.s.add_edge(self.ag, "has_qualia_action_context", context, {})
        for axis, value in enumerate(projected):
            feature = self.s.add_node("ExperienceFeatureObservation", {
                "owner_id": self.owner_id, "episode_id": episode_id, "event_id": event_id,
                "feature_id": f"{event_id}:axis:{axis}",
                "feature_key": f"{self.frame_id}:coordinate:{axis}",
                "feature_family": "ousiometric_projected_coordinate",
                "feature_value": value, "value_kind": "number", "grain": 0.0,
                "is_missing": False, "source_epoch": float(source_epoch),
                "model_epoch": float(model_epoch), "frame_epoch": float(frame_epoch),
                "status": "observed"})
            self.s.add_edge(ev, "has_episode_feature", feature, {})
            self.s.add_edge(feature, "derived_from_frame_projection", projection_node, {})
        self._events.add(event_id)
        for _ in range(30):
            used = int(self.agent.native.run_rules(5000))
            self.native_steps += used
            if used == 0:
                break
        authorizations = [self.s.node(n)["attrs"] for n in self.s.nodes("QualiaActionAuthorization")
                          if self.s.node(n)["attrs"].get("event_id") == event_id
                          and self.s.node(n)["attrs"].get("status") == "authorized"]
        return authorizations[0] if len(authorizations) == 1 else None

    def project_for_query(self, coordinates: Iterable[Real]) -> tuple[float, float, float]:
        """Submit a fresh query through native projection, with no raw bypass."""
        return self._project_for_query_with_node(coordinates)[0]

    def _project_for_query_with_node(self, coordinates: Iterable[Real]) -> tuple[tuple[float, float, float], int]:
        self._query_index += 1
        event = f"query-projection:{self._query_index}:{self.frame_id}"
        raw = validate_coordinates(coordinates)
        node = self.s.add_node("OusiometricRawEvidence", {
            "owner_id": self.owner_id, "episode_id": event, "context_id": event,
            "event_id": event, "coordinates": list(raw),
            "coordinate_encoding": "finite_f64_v1", "evidence_status": "observed",
            "receipt_status": "verified", "action_authorized": True,
            "source_epoch": float(self.source_epoch), "model_epoch": float(self.model_epoch),
            "frame_epoch": 1.0})
        self.s.add_edge(self.ag, "has_ousiometric_raw_evidence", node, {})
        self.native_steps += int(self.agent.native.run_rules(2000))
        projections = [n for n in self.s.nodes("OusiometricFrameProjection")
                       if self.s.node(n)["attrs"].get("event_id") == event
                       and self.s.node(n)["attrs"].get("frame_id") == self.frame_id]
        if len(projections) != 1:
            raise RuntimeError("native frame could not project action query")
        attrs = self.s.node(projections[0])["attrs"]
        if attrs.get("status") != "verified_current" or attrs.get("owner_id") != self.owner_id:
            raise RuntimeError("native frame query projection did not pass source/inverse audit")
        return tuple(float(x) for x in attrs["projected_coordinates"]), projections[0]

    def metric_retrieve(self, *, query_id: str, coordinates: Iterable[Real],
                        legal_actions: Iterable[str]) -> dict | None:
        """Native nearest-receipt retrieval under this frame's declared metric."""
        projected, projection = self._project_for_query_with_node(coordinates)
        legal = tuple(str(action) for action in legal_actions)
        if not legal:
            return None
        query = self.s.add_node("OusiometricMetricQuery", {
            "query_id": query_id, "owner_id": self.owner_id, "frame_id": self.frame_id,
            "frame_epoch": 1.0, "projected_coordinates": list(projected),
            "legal_actions": list(legal),
            "candidate_count_expected": float(sum(
                1 for node in self.s.nodes("OusiometricMetricMemory")
                if self.s.node(node)["attrs"].get("frame_id") == self.frame_id
                and self.s.node(node)["attrs"].get("action_id") in legal)),
            "status": "pending"})
        self.s.add_edge(self.ag, "has_ousiometric_metric_query", query, {})
        self.s.add_edge(query, "uses_projection", projection, {})
        for _ in range(20):
            used = int(self.agent.native.run_rules(5000))
            self.native_steps += used
            if used == 0:
                break
        recalls = [self.s.node(n)["attrs"] for n in self.s.nodes("OusiometricMetricRecall")
                   if self.s.node(n)["attrs"].get("query_id") == query_id
                   and self.s.node(n)["attrs"].get("status") == "consumed"]
        return recalls[0] if len(recalls) == 1 else None

    def select_goal_action(self, *, query_id: str, coordinates: Iterable[Real],
                           legal_actions: Iterable[str], goal_value: float) -> dict | None:
        """Native goal selector over each legal action's nearest verified receipt."""
        if not math.isfinite(float(goal_value)):
            raise ValueError("goal target must be finite")
        if any(self.s.node(n)["attrs"].get("query_id") == query_id
               for n in self.s.nodes("OusiometricMetricQuery")):
            raise ValueError("metric query ID replay")
        projected, projection = self._project_for_query_with_node(coordinates)
        legal = tuple(dict.fromkeys(str(action) for action in legal_actions))
        if not legal:
            return None
        memory_count = sum(1 for node in self.s.nodes("OusiometricMetricMemory")
                           if self.s.node(node)["attrs"].get("frame_id") == self.frame_id
                           and self.s.node(node)["attrs"].get("action_id") in legal)
        query = self.s.add_node("OusiometricMetricQuery", {
            "query_id": query_id, "owner_id": self.owner_id, "frame_id": self.frame_id,
            "frame_epoch": 1.0, "projected_coordinates": list(projected),
            "legal_actions": list(legal), "candidate_count_expected": float(memory_count),
            "expected_action_count": float(len(legal)), "goal_value": float(goal_value),
            "goal_enabled": True, "status": "pending"})
        self.s.add_edge(self.ag, "has_ousiometric_metric_query", query, {})
        self.s.add_edge(query, "uses_projection", projection, {})
        for _ in range(30):
            if self.agent.native.run_rules(5000) == 0:
                break
        decisions = [self.s.node(n)["attrs"] for n in self.s.nodes("OusiometricMetricActionDecision")
                     if self.s.node(n)["attrs"].get("query_id") == query_id
                     and self.s.node(n)["attrs"].get("status") == "consumed"]
        return decisions[0] if len(decisions) == 1 else None

    def predict(self, *, query_id: str, coordinate: int, value: float,
                action_kind: str, object_id: str, object_type: str,
                split: str = "development") -> dict | None:
        if coordinate not in (0, 1, 2):
            raise ValueError("coordinate index must be 0, 1, or 2")
        if not math.isfinite(float(value)):
            raise ValueError("query coordinate must be finite")
        prediction = self.learner.predict(
            query_id=query_id, action_kind=action_kind, object_type=object_type,
            feature_key=f"{self.frame_id}:coordinate:{coordinate}",
            before_value=repr(float(value)), object_id=object_id,
            source_epoch=self.source_epoch, model_epoch=self.model_epoch,
            frame_epoch=1, split=split)
        if prediction is None:
            return None
        return prediction

    def native_predictions(self) -> list[dict]:
        return [self.s.node(n)["attrs"] for n in self.s.nodes("ProcessPrediction")]

    def graph_footprint(self) -> dict:
        return self.learner.graph_footprint()

    def profile_audit(self) -> dict:
        return {
            "profile": self.agent.profile,
            "frame_id": self.frame_id,
            "frame_enabled": [self.s.node(n)["attrs"].get("enabled")
                              for n in self.s.nodes("OusiometricFramePolicy")],
            "acquisition_enabled": [self.s.node(n)["attrs"].get("enabled")
                                    for n in self.s.nodes("OusiometricAcquisitionPolicy")],
            "common_target_enabled": [self.s.node(n)["attrs"].get("enabled")
                                      for n in self.s.nodes("CommonTargetEvidencePolicy")],
            "loaded_seeds": sorted(self.loaded_seed_ids),
            "native_steps": self.native_steps,
            "no_host_action": True,
        }

