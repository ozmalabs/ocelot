"""Adapter-level CoW branch isolation for authenticated user namespaces."""
from __future__ import annotations

import pytest

from domains.world_adapter_cow import AdapterForkError, fork_world_adapter
from substrate.world_adapter import WorldAdapter


def test_fork_shares_baseline_then_isolates_graph_and_python_state():
    parent = WorldAdapter()
    parent._concepts["forkable-index"] = parent.agent
    parent._last_message = parent.agent
    child = fork_world_adapter(parent)

    assert child is not parent
    assert child.s.node_count() == parent.s.node_count()
    assert child.agent == parent.agent
    assert child._concepts is not parent._concepts
    assert child._concepts["forkable-index"] == parent.agent
    assert child._last_message == parent._last_message

    parent._seen.add(("parent", "x", 1))
    child._seen.add(("child", "x", 2))
    child._concepts["forkable-index"] = None
    child._last_message = None
    child_node = child.s.add_node("CowBranchTest", {"owner": "child"})

    assert ("parent", "x", 1) not in child._seen
    assert ("child", "x", 2) not in parent._seen
    assert parent._concepts["forkable-index"] == parent.agent
    assert parent._last_message == parent.agent
    assert child.s.has_node(child_node)
    assert not parent.s.has_node(child_node)


def test_fork_fails_closed_with_unforkable_adapter_resources():
    adapter = WorldAdapter()
    adapter._storage_mmap = object()

    with pytest.raises(AdapterForkError, match="storage mmap"):
        fork_world_adapter(adapter)


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("_teacher_threads", [object()], "teacher threads"),
        ("_eye", object(), "_eye"),
        ("_upload_eye", object(), "_upload_eye"),
        ("_vision_substrate", object(), "_vision_substrate"),
    ],
)
def test_fork_refuses_runtime_resources_outside_the_cow_graph(field, value, error):
    adapter = WorldAdapter()
    setattr(adapter, field, value)

    with pytest.raises(AdapterForkError, match=error):
        fork_world_adapter(adapter)


def test_fork_fails_closed_when_native_snapshot_rejects_graph_state(monkeypatch):
    adapter = WorldAdapter()

    class RefusingSnapshot:
        def fork(self):
            raise RuntimeError("ineligible native state")

    monkeypatch.setattr(adapter.s, "snapshot", lambda: RefusingSnapshot())
    with pytest.raises(AdapterForkError, match="ineligible native state"):
        fork_world_adapter(adapter)


def test_fork_rebuilds_graph_bound_discourse_cache_on_branch():
    parent = WorldAdapter()
    parent_store = parent._canonical_discourse_store()

    child = fork_world_adapter(parent)
    assert child._discourse_store is None
    child_store = child._canonical_discourse_store()
    assert child_store is not parent_store
    assert child_store.s is child.s
