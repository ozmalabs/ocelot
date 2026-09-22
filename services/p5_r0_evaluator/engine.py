from __future__ import annotations

from copy import deepcopy
from typing import Any

from .canonical import digest
from .interfaces import Engine, EngineFactory


class RepositoryEngineFactory(EngineFactory):
    """Bridge to the checked-in evaluator while keeping truth server-side."""
    def create(self, manifest: dict[str, Any], private_store: dict[str, Any]) -> Engine:
        from evaluation.p5_r0.evaluator import P5R0Evaluator
        return RepositoryEngine(P5R0Evaluator, manifest, private_store)

    def rehydrate(self, manifest: dict[str, Any], private_store: dict[str, Any], checkpoint: dict[str, Any]) -> Engine:
        from evaluation.p5_r0.evaluator import P5R0Evaluator
        engine = RepositoryEngine(P5R0Evaluator, manifest, private_store)
        engine.restore_checkpoint(checkpoint)
        return engine


class RepositoryEngine(Engine):
    def __init__(self, evaluator_type: Any, manifest: dict[str, Any], private_store: dict[str, Any]):
        # The checked-in evaluator has one active arm context. Keep one isolated
        # evaluator per arm so the service cannot reinitialize or mix sessions.
        self._evaluator_type = evaluator_type
        self._manifest = manifest
        self._private_store = private_store
        self._evaluators: dict[str, Any] = {}
        self.order = digest([row["case_id"] for row in manifest["case_index"]])
        self.contexts: dict[str, dict[str, Any]] = {}

    def _for_arm(self, arm: str) -> Any:
        evaluator = self._evaluators.get(arm)
        if evaluator is None:
            evaluator = self._evaluator_type(self._manifest, self._private_store)
            self._evaluators[arm] = evaluator
        return evaluator

    def issue(self, *, arm: str, case: dict[str, Any], sequence: int,
              task_id: str, nonce: str, control: dict[str, Any] | None) -> dict[str, Any]:
        evaluator = self._for_arm(arm)
        context = self.contexts.get(arm)
        if context is None:
            context = evaluator.arm_context(arm, self.order)
            self.contexts[arm] = context
        evaluator.begin_case(case["case_id"], int(case["ordinal"]))
        return evaluator.task(case, nonce, context, control_metadata=control)

    def evaluate(self, *, arm: str, case: dict[str, Any], task: dict[str, Any],
                 reply: dict[str, Any]) -> dict[str, Any]:
        from evaluation.p5_r0.native_worker import validate_reply_v3
        validate_reply_v3(reply, task)
        return deepcopy(self._for_arm(arm).evaluate(case, arm, reply["action"]))

    def checkpoint(self) -> dict[str, Any]:
        arms = {arm: {"evaluator": evaluator.checkpoint(), "context": deepcopy(self.contexts.get(arm))}
                for arm, evaluator in sorted(self._evaluators.items())}
        return {"schema": "P5R0RepositoryEngineCheckpointV1", "manifest_digest": self._manifest["manifest_digest"],
                "order": self.order, "arms": arms}

    def restore_checkpoint(self, checkpoint: dict[str, Any]) -> None:
        required = {"schema", "manifest_digest", "order", "arms"}
        if not isinstance(checkpoint, dict) or set(checkpoint) != required or checkpoint.get("schema") != "P5R0RepositoryEngineCheckpointV1":
            raise ValueError("engine checkpoint schema")
        if checkpoint.get("manifest_digest") != self._manifest["manifest_digest"] or checkpoint.get("order") != self.order or not isinstance(checkpoint.get("arms"), dict):
            raise ValueError("engine checkpoint binding")
        evaluators: dict[str, Any] = {}; contexts: dict[str, dict[str, Any]] = {}
        for arm, value in checkpoint["arms"].items():
            if arm not in {"cold_reset", "frozen_transfer", "warm_adaptive"} or not isinstance(value, dict) or set(value) != {"evaluator", "context"}:
                raise ValueError("engine checkpoint arm")
            evaluator = self._evaluator_type(self._manifest, self._private_store)
            evaluator.restore_checkpoint(value["evaluator"])
            context = value["context"]
            if not isinstance(context, dict) or context.get("arm") != arm:
                raise ValueError("engine checkpoint context")
            evaluators[arm] = evaluator; contexts[arm] = deepcopy(context)
        self._evaluators = evaluators
        self.contexts = contexts

    def restore(self) -> str:
        digests = [evaluator.restore() for evaluator in self._evaluators.values()]
        return digest(digests)
