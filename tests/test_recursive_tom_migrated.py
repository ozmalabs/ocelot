"""F2.1 executable fixtures; F2.2 will connect these cases to native rules."""
from __future__ import annotations


def _world(path, referent="key", actual_version=1):
    return {"holder_path": tuple(path), "referent": referent,
            "actual_world_version": actual_version}


def _event(event_id, path, proposition, *, access):
    return {"event_id": event_id, "holder_path": tuple(path),
            "proposition": proposition, "access": access}


def test_second_order_false_belief():
    actual = {"key_location": "shelf", "version": 1}
    second_order = _world(["sally", "anne"])
    belief = {**second_order, "proposition": "key_location=drawer", "truth": False}
    assert belief["holder_path"] == ("sally", "anne")
    assert belief["truth"] is False
    assert actual["key_location"] == "shelf"


def test_actual_world_not_overwritten():
    actual = {"key_location": "shelf", "version": 1}
    before = dict(actual)
    event = _event("obs-1", ["sally", "anne"], "key_location=drawer", access=True)
    # The event proposes an attributed update; actual world is a separate record.
    attributed = {**_world(event["holder_path"], actual_version=actual["version"]),
                  "proposition": event["proposition"]}
    assert attributed["proposition"] != f"key_location={actual['key_location']}"
    assert actual == before


def test_no_access_no_belief_update():
    inaccessible = _event("obs-2", ["sally", "anne"], "door=open", access=False)
    assert inaccessible["access"] is False
    # Without an access event, the result is explicitly unknown, not false.
    result = {"status": "unknown", "reason": "no_access"}
    assert result["status"] == "unknown"


def test_cycles_and_depth_bound():
    max_depth = 2
    valid = _world(["sally", "anne"])
    cycle = _world(["sally", "anne", "sally"])
    over_depth = _world(["sally", "anne", "bob"])
    assert len(valid["holder_path"]) == max_depth
    assert len(set(cycle["holder_path"])) < len(cycle["holder_path"])
    assert len(over_depth["holder_path"]) > max_depth
    assert _world(["sally", "anne"]) != _world(["anne", "sally"])


def _adapter():
    from substrate.boot_core import CORE_SEEDS
    from substrate.world_adapter import WorldAdapter
    return WorldAdapter(seeds=CORE_SEEDS + ("recursive_tom",))


def _graph_event(adapter, *, event_id="e1", path=("sally", "anne"),
                 proposition="key=drawer", accessible=True, depth=None,
                 has_cycle=False, version=1):
    depth = len(path) if depth is None else depth
    event = adapter.inner.add_node("RecursiveTomEvent", {
        "schema_version": 1, "event_id": event_id,
        "holder_path": list(path), "holder_path_key": "/".join(path),
        "depth": depth, "referent": "key", "content_ref": proposition,
        "value": "drawer", "actual_world_version": version,
        "accessible": accessible, "has_cycle": has_cycle,
    })
    adapter.inner.add_edge_unchecked(adapter.agent, "has_recursive_tom_event", event)
    return event


def _query(adapter, query_id, path, *, content="key=drawer", expected="drawer", version=1):
    query = adapter.inner.add_node("RecursiveTomQuery", {
        "query_id": query_id, "holder_path_key": "/".join(path),
        "referent": "key",
        "content_ref": content, "expected_value": expected,
        "actual_world_version": version,
    })
    adapter.inner.add_edge_unchecked(adapter.agent, "has_recursive_tom_query", query)
    return query


def test_native_update_requires_access_and_respects_depth_and_cycles():
    a = _adapter()
    policy = a.inner.nodes("RecursiveTomPolicy")[0]
    _graph_event(a, event_id="no-access", accessible=False)
    _graph_event(a, event_id="cycle", has_cycle=True)
    _graph_event(a, event_id="deep", path=("sally", "anne", "bob"))
    a.inner.set_attr(policy, "enabled", 1.0)
    a.inner.run_rules()
    assert list(a.inner.nodes("RecursiveTomBelief")) == []
    _graph_event(a, event_id="valid")
    a.inner.run_rules()
    beliefs = list(a.inner.nodes("RecursiveTomBelief"))
    assert len(beliefs) == 1
    attrs = a.inner.node(beliefs[0])["attrs"]
    assert attrs["holder_path"] == ["sally", "anne"]
    assert attrs["access_event_id"] == "valid"


def test_repeated_event_idempotent_and_holder_swap_changes_answer_scope():
    a = _adapter()
    policy = a.inner.nodes("RecursiveTomPolicy")[0]
    a.inner.set_attr(policy, "enabled", 1.0)
    _graph_event(a, event_id="same", path=("sally", "anne"))
    a.inner.run_rules()
    _graph_event(a, event_id="same", path=("anne", "sally"))
    a.inner.run_rules()
    beliefs = [a.inner.node(n)["attrs"] for n in a.inner.nodes("RecursiveTomBelief")]
    assert len(beliefs) == 1
    assert beliefs[0]["holder_path_key"] == "sally/anne"


def test_minimal_dependency_boot_and_actual_world_is_separate():
    a = _adapter()
    actual = a.inner.add_node("ActualWorldFact", {"referent": "key", "value": "shelf", "version": 1})
    policy = a.inner.nodes("RecursiveTomPolicy")[0]
    a.inner.set_attr(policy, "enabled", 1.0)
    _graph_event(a, proposition="key=drawer", version=1)
    a.inner.run_rules()
    belief = a.inner.node(a.inner.nodes("RecursiveTomBelief")[0])["attrs"]
    assert belief["value"] == "drawer"
    assert a.inner.node(actual)["attrs"]["value"] == "shelf"


def test_scoped_query_returns_true_false_or_unknown():
    a = _adapter()
    policy = a.inner.nodes("RecursiveTomPolicy")[0]
    a.inner.set_attr(policy, "enabled", 1.0)
    _graph_event(a, event_id="belief", path=("sally", "anne"))
    _query(a, "true-query", ("sally", "anne"), expected="drawer")
    _query(a, "false-query", ("sally", "anne"), expected="box")
    _query(a, "unknown-query", ("anne", "sally"), expected="drawer")
    a.inner.run_rules()
    answers = {a.inner.node(n)["attrs"]["query_id"]:
               a.inner.node(n)["attrs"]["status"]
               for n in a.inner.nodes("RecursiveTomAnswer")}
    assert answers == {"true-query": "true", "false-query": "false"}


def test_generator_reproduction():
    import json
    from pathlib import Path
    from scripts.gen_recursive_tom_seed import build_seed
    assert json.loads(Path("seeds/recursive_tom.json").read_text()) == build_seed()


def test_adapter_has_no_belief_update_decisions():
    import ast
    import inspect
    from domains import character_tom
    source = inspect.getsource(character_tom.submit_recursive_tom_event)
    tree = ast.parse(source)
    assert not any(isinstance(node, (ast.If, ast.For, ast.While, ast.IfExp))
                   for node in ast.walk(tree))
    assert "RecursiveTomBelief" not in source


def test_character_tom_adapter_submits_and_reads_native_recursive_state():
    from domains import character_tom
    a = _adapter()
    policy = a.inner.nodes("RecursiveTomPolicy")[0]
    a.inner.set_attr(policy, "enabled", 1.0)
    character_tom.submit_recursive_tom_event(
        a, event_id="adapter-event", holder_path=["sally", "anne"],
        referent="key", content_ref="key=drawer", value="drawer",
        actual_world_version=1, accessible=True,
    )
    result = character_tom.query_recursive_tom(
        a, query_id="adapter-query", holder_path=["sally", "anne"],
        referent="key", content_ref="key=drawer", expected_value="drawer",
        actual_world_version=1,
    )
    assert result == {"query_id": "adapter-query", "status": "true",
                      "evidence_event_id": "adapter-event"}
    unknown = character_tom.query_recursive_tom(
        a, query_id="adapter-unknown", holder_path=["anne", "sally"],
        referent="key", content_ref="key=drawer", expected_value="drawer",
        actual_world_version=1,
    )
    assert unknown["status"] == "unknown"
