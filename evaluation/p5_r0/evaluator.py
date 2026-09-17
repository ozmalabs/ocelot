"""Evaluator-owned private mechanics, arm sessions, and transition outcomes."""
from __future__ import annotations
from copy import deepcopy
from typing import Any, Callable
from .fixture_generator import make_task, private_store_for, validate_manifest_integrity
from .mechanics import spec_for, transition
from .protocol import ARMS, P5R0Error, digest
from .rollback import Snapshot


class P5R0Evaluator:
    def __init__(self, bundle: dict[str, Any]):
        if bundle.get("schema") != "P5R0ManifestV2": raise P5R0Error("fixture manifest")
        validate_manifest_integrity(bundle)
        self.bundle = bundle; self.store = private_store_for(bundle); self.cases = {c["case_id"]: deepcopy(c) for c in self.store["cases"]}; self._private_store_digest = self.store["store_digest"]
        self.state = {"arm": None, "session_id": None, "case_order_digest": None, "case_ordinal": -1, "case_id": None, "domain_token": None, "case_split": None, "codebook": {}, "graph": {}, "adaptations": 0, "frozen": False, "session": {}, "episode": {"step": 0}, "episode_reset_digest": digest({"step": 0}), "adoption_count_case": 0}
        self.snapshot = Snapshot(self.state); self._training_digest = digest({"train": sorted(c["case_id"] for c in self.store["cases"] if c["split"] == "train")}); self._active_context: dict[str, Any] | None = None
        self._namespace_budget = 4
        self._min_confidence_milli = 900

    def private_case(self, case_id: str) -> dict[str, Any]:
        validate_manifest_integrity(self.bundle)
        case = self.cases.get(case_id)
        if case is None: raise P5R0Error("evaluator case")
        return deepcopy(case)

    def arm_context(self, arm: str, case_order_digest: str, session_id: str | None = None) -> dict[str, Any]:
        if arm not in ARMS: raise P5R0Error("arm")
        if self._active_context is not None:
            if self._active_context["arm"] != arm or self._active_context["case_order_digest"] != case_order_digest:
                raise P5R0Error("session reinitialization or reorder")
            # A warm reset is a mutation request, not an idempotent context
            # lookup.  An explicitly supplied identity must match the armed
            # session before any caller can reach the worker seam.
            if session_id is not None and session_id != self._active_context["session_id"]:
                raise P5R0Error("warm reset session identity mismatch")
            return dict(self._active_context)
        session_id = session_id or digest({"manifest": self.bundle["manifest_digest"], "arm": arm, "order": case_order_digest})
        if arm == "cold_reset":
            codebook, frozen, write_mode, allowed = {}, False, "none", False
        elif arm == "frozen_transfer":
            codebook, frozen, write_mode, allowed = {"training": self._training_digest}, True, "none", False
        else:
            codebook, frozen, write_mode, allowed = {"training": self._training_digest}, False, "adaptation_only", True
        self.state = {"arm": arm, "session_id": session_id, "case_order_digest": case_order_digest, "case_ordinal": -1, "case_id": None, "domain_token": None, "case_split": None, "codebook": codebook, "graph": {}, "adaptations": 0, "frozen": frozen, "session": {"codebook": deepcopy(codebook), "graph": {}, "adaptations": 0, "adaptations_by_domain": {}, "namespace_budget": self._namespace_budget}, "episode": {"step": 0}, "episode_reset_digest": digest({"step": 0}), "adoption_count_case": 0}
        self._active_context = {"schema": "P5R0ArmContextV3", "arm": arm, "session_id": session_id, "state_origin_digest": self.session_digest(), "reset_scope": "case" if arm == "cold_reset" else "session", "training_digest": self._training_digest if arm != "cold_reset" else digest({}), "write_mode": write_mode, "adaptation_allowed": allowed, "case_order_digest": case_order_digest, "persistent_namespace_schema": "P5R0PersistentNamespaceV3", "episode_reset_policy": "fresh_case"}
        return dict(self._active_context)

    def begin_case(self, case_id: str, ordinal: int) -> dict[str, Any]:
        if self._active_context is None: raise P5R0Error("arm session not initialized")
        if ordinal != self.state["case_ordinal"] + 1: raise P5R0Error("case order")
        case = self.cases.get(case_id)
        if case is None: raise P5R0Error("evaluator case")
        # Episode/cursor state is always transient and starts at zero.  Warm
        # persistence lives only in the declared per-domain session namespace.
        if self.state["arm"] == "cold_reset":
            self.state["codebook"] = {}
            self.state["graph"] = {}
            self.state["session"] = {"codebook": {}, "graph": {}, "adaptations": 0, "adaptations_by_domain": {}, "namespace_budget": self._namespace_budget}
            self.state["adaptations"] = 0
        self.state["episode"] = {"step": 0}
        self.state["episode_reset_digest"] = digest({"case_id": case_id, "policy": "fresh_case", "step": 0})
        self.state["adoption_count_case"] = 0
        self.state["case_ordinal"] = ordinal; self.state["case_id"] = case_id; self.state["domain_token"] = case["domain_token"]; self.state["case_split"] = case["split"]
        return {"session_id": self.state["session_id"], "ordinal": ordinal, "pre_state_digest": self.session_digest(), "case_order_digest": self.state["case_order_digest"], "episode_step": 0, "episode_digest": self.episode_digest(), "reset_policy_digest": self.reset_policy_digest(), "namespace_digest": self.namespace_digest(case["domain_token"])}

    def session_digest(self) -> str:
        return digest({"arm": self.state.get("arm"), "session_id": self.state.get("session_id"), "case_order_digest": self.state.get("case_order_digest"), "codebook": self.state.get("codebook", {}), "graph": self.state.get("graph", {}), "adaptations": self.state.get("adaptations", 0), "frozen": self.state.get("frozen", False), "persistent_namespaces": self.state.get("session", {}).get("adaptations_by_domain", {})})

    def episode_digest(self) -> str:
        return digest(self.state.get("episode", {"step": 0}))

    def reset_policy_digest(self) -> str:
        return digest({"policy": "fresh_case", "arm": self.state.get("arm"), "case_id": self.state.get("case_id")})

    def namespace_digest(self, domain_token: str | None = None) -> str:
        domain = domain_token or self.state.get("domain_token")
        namespaces = self.state.get("session", {}).get("adaptations_by_domain", {})
        return digest({"schema": "P5R0PersistentNamespaceV3", "domain": domain, "value": namespaces.get(domain, {})})

    def persistent_projection(self, case: dict[str, Any]) -> dict[str, Any]:
        domain = case["domain_token"]
        value = self.state.get("session", {}).get("adaptations_by_domain", {}).get(domain, {})
        # Only a bounded public projection reaches the worker task.
        return {"adoption_count": min(int(value.get("adoption_count", 0)), self._namespace_budget), "namespace_digest": self.namespace_digest(domain)}

    def adopt_adaptation(self, proposal: dict[str, Any]) -> dict[str, Any]:
        required = {"schema", "domain_token", "source_case_id", "source_split", "source_session_id", "source_case_digest", "target_case_id", "target_case_digest", "task_digest", "confidence_milli", "safe_success", "value"}
        if set(proposal) != required or proposal.get("schema") != "P5R0AdaptationProposalV3": raise P5R0Error("adaptation proposal schema")
        current = self.state
        source = self.cases.get(proposal["source_case_id"])
        if source is None or proposal["source_case_digest"] != source["case_digest"] or source["domain_token"] != current.get("domain_token") or proposal["source_split"] != source["split"]:
            raise P5R0Error("adaptation provenance")
        if source["split"] == "held_out":
            raise P5R0Error("held-out adaptation")
        if proposal["domain_token"] != current.get("domain_token"):
            raise P5R0Error("cross-domain adaptation")
        namespaces = current.setdefault("session", {}).setdefault("adaptations_by_domain", {})
        had_namespace = current.get("domain_token") in namespaces
        namespace = namespaces.setdefault(current.get("domain_token"), {"adoption_count": 0, "entries": []})
        before = deepcopy(namespace); before_digest = digest(before)
        valid = (current.get("arm") == "warm_adaptive" and proposal["target_case_id"] == current.get("case_id") and proposal["target_case_digest"] == self.cases[current["case_id"]]["case_digest"] and proposal["source_split"] in {"train", "development"} and proposal["source_session_id"] == current["session_id"] and type(proposal["confidence_milli"]) is int and proposal["confidence_milli"] >= self._min_confidence_milli and proposal["safe_success"] is True and current.get("adoption_count_case", 0) == 0)
        if int(namespace.get("adoption_count", 0)) >= self._namespace_budget: raise P5R0Error("adaptation budget")
        if not valid:
            if not had_namespace: namespaces.pop(current.get("domain_token"), None)
            return {"schema": "P5R0AdaptationDecisionV3", "accepted": False, "reason": "provenance_or_confidence", "namespace_digest_before": before_digest, "namespace_digest_after": self.namespace_digest(current.get("domain_token")), "rollback_digest": digest(before)}
        namespace["adoption_count"] = int(namespace.get("adoption_count", 0)) + 1; namespace.setdefault("entries", []).append({"source_case_id": proposal["source_case_id"], "source_case_digest": proposal["source_case_digest"], "task_digest": proposal["task_digest"], "confidence_milli": proposal["confidence_milli"], "value": proposal["value"]})
        current["adaptations"] += 1; current["adoption_count_case"] = 1; current["session"]["adaptations"] = current["adaptations"]
        return {"schema": "P5R0AdaptationDecisionV3", "accepted": True, "reason": "accepted", "namespace_digest_before": before_digest, "namespace_digest_after": self.namespace_digest(current.get("domain_token")), "rollback_digest": digest(before)}


    def task(self, case: dict[str, Any], nonce: str, arm_context: dict[str, Any] | None = None, *, control_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        from .fixture_generator import make_task_v3
        return make_task_v3(self.private_case(case["case_id"]), task_nonce=nonce, arm_context=arm_context, episode_state=self.state.get("episode", {"step": 0}), persistent_projection=self.persistent_projection(case), control_metadata=control_metadata)


    def evaluate(self, case: dict[str, Any], arm: str, action: int | None, *, safe: bool | None = None, exhausted: bool = False, write_attempt: bool = False) -> dict[str, Any]:
        if arm not in ARMS or self.state.get("arm") != arm: raise P5R0Error("arm session")
        private = self.private_case(case["case_id"]); spec = spec_for(private); truth = private["truth"]
        if private["case_digest"] != case["case_digest"] or case.get("mechanics_digest") != spec["mechanics_digest"] or truth["mechanics_digest"] != spec["mechanics_digest"]: raise P5R0Error("case mechanics commitment")
        before = self.session_digest(); state_before = deepcopy(self.state)
        if exhausted:
            outcome, result = "resource_exhausted", {"safe": True, "violation": "resource_limit", "terminal": True, "success": False, "before": digest(self.state), "after": digest(self.state)}
        elif safe is False:
            outcome, result = "safety_violation", {"safe": False, "violation": "evaluator_safety_policy", "terminal": True, "success": False, "before": digest(self.state), "after": digest(self.state)}
        elif write_attempt and arm == "frozen_transfer":
            self.state = state_before; outcome, result = "containment_failure", {"safe": False, "violation": "frozen_write_set", "terminal": True, "success": False, "before": digest(self.state), "after": digest(self.state)}
        elif action is None:
            outcome, result = "abstain", {"safe": True, "violation": None, "terminal": True, "success": False, "before": digest(self.state), "after": digest(self.state)}
        else:
            episode = deepcopy(self.state.setdefault("episode", {"step": 0})); step = int(episode.get("step", 0));
            if spec["memory"] == "persistent":
                namespace = self.state.setdefault("session", {}).setdefault("adaptations_by_domain", {}).setdefault(self.state["domain_token"], {"adoption_count": 0, "entries": []})
                episode["memory_count"] = int(namespace.get("memory_count", 0))
            result = transition(episode, action, truth, spec, step)
            if spec["memory"] == "persistent":
                namespace["memory_count"] = int(episode.pop("memory_count", namespace.get("memory_count", 0)))
            self.state["episode"] = episode
            if not result["safe"] and result["violation"] == "illegal_action": outcome = "protocol_error"
            else: outcome = "complete_correct" if result["success"] else "complete_wrong"
            if arm == "warm_adaptive" and result["safe"]:
                self.state["adaptations"] += 1; self.state["session"]["adaptations"] = self.state["adaptations"]
            if arm == "frozen_transfer":
                # Episode writes are transient; the evaluator session artifact is immutable.
                self.state["codebook"] = state_before["codebook"]; self.state["graph"] = state_before["graph"]; self.state["adaptations"] = state_before["adaptations"]
        after = self.session_digest(); write_set = {"adaptations": self.state["adaptations"] - state_before["adaptations"]} if arm == "warm_adaptive" else {}
        return {"schema": "P5R0EvaluatorOutcomeV3", "case_digest": case["case_digest"], "arm": arm, "outcome": outcome, "action": action, "transition": result, "pre_state_digest": before, "post_state_digest": after, "write_set": write_set, "write_set_digest": digest(write_set), "session_id": self.state["session_id"], "case_ordinal": self.state["case_ordinal"], "safe": result["safe"], "resource_exhausted": exhausted, "adaptation_count": self.state["adaptations"], "legal_action_digest": digest(spec["legal_actions"]), "mechanics_digest": spec["mechanics_digest"], "effect_digest": result.get("effect_digest"), "truth_digest": digest(truth), "episode_step_before": int(state_before.get("episode", {}).get("step", 0)), "episode_step_after": int(self.state.get("episode", {}).get("step", 0)), "episode_digest": self.episode_digest(), "reset_policy_digest": self.reset_policy_digest(), "namespace_digest": self.namespace_digest(case["domain_token"])}

    def restore(self) -> str:
        restored = self.snapshot.restore(self.state); self._active_context = None; return restored


def execute_native_transfer(evaluator: P5R0Evaluator, case: dict[str, Any], arm: str, worker: Callable[[dict[str, Any]], int | None]) -> dict[str, Any]:
    order = digest([case["case_id"]]); context = evaluator.arm_context(arm, order); evaluator.begin_case(case["case_id"], 0); task = evaluator.task(case, digest({"case": case["case_digest"], "arm": arm}), context); return evaluator.evaluate(case, arm, worker(task))
