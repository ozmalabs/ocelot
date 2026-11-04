"""Development-only dependence controls on native P22 checkpoints."""
from evaluation.process_mastery.checkpoint_world_adapter import (
    CheckpointWorldAdapter, capture_adopted_checkpoint,
    capture_held_process_checkpoint,
)
from evaluation.process_mastery.native_process_execution import (
    attest_open_process_candidate, execute_open_process_candidate,
)
from tests.test_open_process_adoption import (
    _agent, _approve, _candidate, _tick,
)
from tests.test_open_process_search import _apply


def test_component_ablation_changes_claimed_path():
    """Removing the learned candidate restores ancestor behavior on one control."""
    agent = _agent()
    try:
        candidate = _candidate(agent)
        digest = attest_open_process_candidate(agent, candidate)
        parent = capture_held_process_checkpoint(agent, agent.schemas("search")[0],
            checkpoint_id="ablation-native-ancestor")
        _approve(agent, candidate)
        _tick(agent)
        attrs = agent.attrs(candidate)
        state = list(attrs["guard_state"])
        predicted = _apply(agent, attrs["params"], state)
        execution = execute_open_process_candidate(agent, candidate, state=state,
            authorize=lambda proposal: proposal["expression_digest"] == digest,
            world_transition=lambda action: {"observed_state": predicted})
        assert execution["status"] == "COMPLETED"
        learned = capture_adopted_checkpoint(agent, candidate,
            checkpoint_id="ablation-native-learned", parent=parent, generation=1,
            declared_primitive_work=1)

        adapter = CheckpointWorldAdapter(agent.native, primitive_work_ceiling=8)
        world = {"world_id": "derived-training-control", "initial_state": state,
                 "goal_state": predicted}
        ancestor = adapter.score(parent, **world)
        with_candidate = adapter.score(learned, **world)

        assert ancestor["execution_source"] == "native_checkpoint_graph"
        assert with_candidate["execution_source"] == "native_checkpoint_graph"
        assert (ancestor["score"], with_candidate["score"]) == (0, 1)
        assert ancestor["expression_digest"] != with_candidate["expression_digest"]
    finally:
        close = getattr(agent.s, "close", None)
        if callable(close):
            close()
