from __future__ import annotations

from copy import deepcopy
from typing import Any

from .canonical import digest
from .interfaces import Engine, EngineFactory


class RepositoryEngineFactory(EngineFactory):
    """Bridge to the checked-in evaluator while keeping truth server-side."""
    def create(self, manifest: dict[str, Any], private_store: dict[str, Any]) -> Engine:
        from evaluation.p5_r0.evaluator import P5R0Evaluator
        from evaluation.p5_r0.fixture_generator import _PRIVATE_STORES
        _PRIVATE_STORES[manifest["manifest_digest"]] = deepcopy(private_store)
        return RepositoryEngine(P5R0Evaluator, manifest, private_store)


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
            evaluator = self._evaluator_type(self._manifest)
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

    def restore(self) -> str:
        digests = [evaluator.restore() for evaluator in self._evaluators.values()]
        return digest(digests)
