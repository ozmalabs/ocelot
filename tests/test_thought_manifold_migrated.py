"""E2.1 parity and grounding-cut fixtures for the legacy thought trajectory."""

from substrate_rs import _native
from domains import regulated_train_of_thought as rtot
from domains import self_dialogue as sd
from domains import train_of_thought as tot
from scripts.gen_thought_manifold_seed import OUT as THOUGHT_OUT, build_seed


def _enable_funded_controller(graph):
    rtot._native_controller_graph(graph)
    budget = graph.nodes("ThinkingBudget")[0]
    graph.set_attr(budget, "enabled", 1.0)
    graph.set_attr(budget, "remaining", 16.0)
    graph.set_attr(budget, "capacity", 16.0)


def test_graph_controller_accounts_segment_and_steers_without_grounding():
    import json

    graph = _native.Substrate()
    agent = graph.add_node("Agent", {})
    seed = build_seed()
    assert json.loads(THOUGHT_OUT.read_text()) == seed
    loaded = graph.load_seed_manifest(seed, agent)
    assert loaded.get("rules_skipped") == []
    policy = graph.nodes("ThoughtManifoldPolicy")[0]
    graph.set_attr(policy, "enabled", 1.0)
    manifold = graph.add_node("ThoughtManifold", {
        "status": "running", "topic": "topic-a", "tube_region": ["topic-a"],
        "region_explicit": True,
        "width": 2, "widen_step": 1, "narrow_step": 1,
        "deviation_wide_quanta": 1, "deviation_converge_quanta": 0,
        "segment_index": 0, "max_segments": 4, "seen_topics": [],
        "detached_buffer": [], "detached_buffer_capacity": 64,
    })
    graph.add_edge(agent, "has_thought_manifold", manifold)
    segment = graph.add_node("ThoughtSegmentInput", {
        "status": "ready", "topics_thought": ["topic-a", "detached-image"],
        "stop_reason": "continue",
    })
    graph.add_edge(manifold, "has_pending_thought_segment", segment)

    for _ in range(10):
        if not graph.run_rules(1000):
            break
    else:
        raise AssertionError("ThoughtManifold controller did not reach a fixpoint")

    step = graph.nodes("ThoughtManifoldStep")[0]
    attrs = graph.node(step)["attrs"]
    assert attrs["deviation"] == 1
    assert attrs["width"] == 2
    assert attrs["next_width"] == 3
    assert attrs["frontier_candidates"] == ["detached-image"]
    assert attrs["next_topic"] == "detached-image"
    assert attrs["reached"] == ["topic-a", "detached-image"]
    assert attrs["provenance_kind"] == "candidate_imagery"
    assert graph.node(manifold)["attrs"]["width"] == 3
    assert graph.node(manifold)["attrs"]["topic"] == "detached-image"
    assert set(graph.node(manifold)["attrs"]["seen_topics"]) == {"topic-a", "detached-image"}
    assert graph.node(manifold)["attrs"]["status"] == "running"
    assert graph.node(segment)["attrs"]["status"] == "consumed"
    assert graph.nodes("GroundedReading") == []


def test_same_projection_for_equivalent_inputs():
    """ThoughtManifold and cognition candidates share the native projector."""
    import json

    graph = _native.Substrate()
    agent = graph.add_node("Agent", {})
    seed = build_seed()
    loaded = graph.load_seed_manifest(seed, agent)
    assert loaded.get("rules_skipped") == []
    policy = graph.nodes("ThoughtManifoldPolicy")[0]
    graph.set_attr(policy, "enabled", 1.0)
    graph.set_attr(policy, "future_manifold_projection_budget", 2.0)
    graph.set_attr(policy, "future_manifold_physical_horizon", 2.0)
    manifold = graph.add_node("ThoughtManifold", {
        "status": "running", "topic": "topic-a", "tube_region": ["topic-a"],
        "region_explicit": True, "width": 1, "widen_step": 1,
        "narrow_step": 1, "deviation_wide_quanta": 1,
        "deviation_converge_quanta": 0, "segment_index": 0,
        "max_segments": 1, "seen_topics": [], "detached_buffer": [],
        "detached_buffer_capacity": 8,
        "future_manifold_target": [[1.0], [2.0]],
        "future_manifold_bounds": [[0.5], [0.5]],
    })
    graph.add_edge(agent, "has_thought_manifold", manifold)
    values = [[1.0], [2.0]]
    segment = graph.add_node("ThoughtSegmentInput", {
        "status": "ready", "topics_thought": ["topic-a"],
        "stop_reason": "novelty_stalled", "future_manifold_values": values,
        "future_manifold_times": [1, 2],
        "future_manifold_widths": [[0.0], [0.0]],
        "future_manifold_effort": [0.0, 0.0],
    })
    graph.add_edge(manifold, "has_pending_thought_segment", segment)
    cognition_candidate = graph.add_node("CognitionManifoldCandidate", {
        "future_manifold_values": values,
        "future_manifold_times": [1, 2],
        "future_manifold_widths": [[0.0], [0.0]],
        "future_manifold_effort": [0.0, 0.0],
    })
    for _ in range(10):
        if not graph.run_rules(1000):
            break
    else:
        raise AssertionError("ThoughtManifold controller did not reach a fixpoint")

    step = graph.nodes("ThoughtManifoldStep")[0]
    step_attrs = graph.node(step)["attrs"]
    assert step_attrs["projection_resolved"] == 1.0
    assert step_attrs["projection_support"] == 1.0
    assert step_attrs["projection_loss"] == 0.0
    assert step_attrs["projection_information_loss"] == 0.0
    assert step_attrs["projection_horizon"] == 2.0
    equivalent = graph.evaluate({
        "type": "FutureManifoldProjection", "episode": {"type": "Var", "name": "ep"},
        "policy": {"type": "Var", "name": "po"},
        "source": {"type": "Var", "name": "src"}, "field": "shape_snapshot",
    }, {"ep": manifold, "po": policy, "src": cognition_candidate})
    assert step_attrs["projection_shape"] == equivalent
    assert step_attrs["provenance_kind"] == "candidate_imagery"
    assert graph.nodes("GroundedReading") == []


def test_public_output_parity(monkeypatch):
    graph = _native.Substrate()
    graph.add_node("Agent", {})
    _enable_funded_controller(graph)
    monkeypatch.setattr(sd, "select_curiosity_topic", lambda wa: "topic-a")
    monkeypatch.setattr(rtot, "_region_from_topic",
                        lambda wa, topic: {"topic-a", "topic-b"})
    segments = iter((
        {"topics_thought": ["topic-a", "drift"], "recovered_total": [],
         "stop_reason": "continue"},
        {"topics_thought": ["topic-b"], "recovered_total": [],
         "stop_reason": "novelty_stalled"},
    ))
    monkeypatch.setattr(tot, "run_inner_conversation",
                        lambda *args, **kwargs: next(segments))

    result = rtot.run_regulated_train_of_thought(
        graph, tube_region={"topic-a", "topic-b"}, width0=0,
        deviation_wide_quanta=1, max_segments=3)

    assert result["width_trace"] == [0, 1]
    assert result["deviation_trace"] == [1, 0]
    assert [segment["topic"] for segment in result["segments"]] == ["topic-a", "topic-b"]
    assert result["stop_reason"] == "novelty_stalled"


def test_empty_topic_unresolved(monkeypatch):
    monkeypatch.setattr(sd, "select_curiosity_topic", lambda wa: None)
    called = []
    monkeypatch.setattr(tot, "run_inner_conversation",
                        lambda *args, **kwargs: called.append(True))

    result = rtot.run_regulated_train_of_thought(object())

    assert result["stop_reason"] == "no_topic"
    assert result["segments"] == []
    assert called == []


def test_detached_trace_cannot_ground(monkeypatch):
    graph = _native.Substrate()
    agent = graph.add_node("Agent", {})
    _enable_funded_controller(graph)
    monkeypatch.setattr(sd, "select_curiosity_topic", lambda wa: "imagined-topic")
    monkeypatch.setattr(rtot, "_region_from_topic",
                        lambda wa, topic: {"imagined-topic"})
    monkeypatch.setattr(tot, "run_inner_conversation", lambda *args, **kwargs: {
        "topics_thought": ["detached-image"], "recovered_total": [],
        "stop_reason": "novelty_stalled",
    })
    before = len(graph.nodes())

    result = rtot.run_regulated_train_of_thought(
        graph, tube_region={"imagined-topic"}, max_segments=1)

    assert result["segments"][0]["reached"] == ["detached-image"]
    assert len(graph.nodes()) > before  # trace is retained as detached imagery
    assert graph.node(agent)["type"] == "Agent"
    assert graph.nodes("GroundedReading") == []
    step = graph.nodes("ThoughtManifoldStep")[0]
    assert graph.node(step)["attrs"]["provenance_kind"] == "candidate_imagery"


def test_adapter_is_mechanical(monkeypatch):
    import inspect
    import ast

    graph = _native.Substrate()
    graph.add_node("Agent", {})
    _enable_funded_controller(graph)
    emitted = iter((
        {"topics_thought": ["topic-a", "outside"], "recovered_total": [],
         "stop_reason": "continue"},
        {"topics_thought": ["topic-b"], "recovered_total": [],
         "stop_reason": "novelty_stalled"},
    ))
    seen = []
    def produce(wa, *, topic, width, **kwargs):
        seen.append((topic, width))
        return next(emitted)
    monkeypatch.setattr(tot, "run_inner_conversation", produce)

    result = rtot.run_regulated_train_of_thought(
        graph, topic="topic-a", tube_region={"topic-a", "topic-b"},
        width0=0, deviation_wide_quanta=1, max_segments=3)

    assert seen == [("topic-a", 0), ("topic-b", 1)]
    assert result["width_trace"] == [0, 1]
    assert result["deviation_trace"] == [1, 0]
    assert [segment["topic"] for segment in result["segments"]] == ["topic-a", "topic-b"]
    assert result["stop_reason"] == "novelty_stalled"
    assert len(graph.nodes("GroundedReading")) == 0
    assert graph.node(graph.nodes("ThoughtManifoldPolicy")[0])["attrs"]["enabled"] == 0.0
    assert graph.node(graph.nodes("ThinkingBudget")[0])["attrs"]["remaining"] == 14.0
    requests = [graph.node(n)["attrs"] for n in graph.nodes("ThinkingBudgetRequest")
                if graph.node(n)["attrs"].get("requester_kind") == "thought_manifold_segment"]
    mode = graph.nodes("NetworkModeState")[0]
    epoch = graph.node(mode)["attrs"]["epoch"]
    assert len(requests) == 2
    assert all(r["status"] == "consumed" and r["debited_epoch"] == epoch
               for r in requests)

    tree = ast.parse(inspect.getsource(rtot.run_regulated_train_of_thought))
    owned = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    assert "_trajectory_deviation" not in owned
    assert "_aperture_deviation" not in owned
    assert "_region_from_topic" not in owned


def test_graph_owns_next_step(monkeypatch):
    graph = _native.Substrate()
    graph.add_node("Agent", {})
    _enable_funded_controller(graph)
    emitted = iter((
        {"topics_thought": ["topic-a", "topic-b"], "recovered_total": [],
         "stop_reason": "continue"},
        {"topics_thought": ["topic-b"], "recovered_total": [],
         "stop_reason": "novelty_stalled"},
    ))
    observed_topics = []
    def produce(wa, *, topic, width, **kwargs):
        observed_topics.append(topic)
        return next(emitted)
    monkeypatch.setattr(tot, "run_inner_conversation", produce)
    rtot.run_regulated_train_of_thought(
        graph, topic="topic-a", tube_region={"topic-a", "topic-b"},
        width0=0, deviation_wide_quanta=3, max_segments=3)
    assert observed_topics == ["topic-a", "topic-b"]


def test_graph_constructs_default_concept_region(monkeypatch):
    graph = _native.Substrate()
    graph.add_node("Agent", {})
    _enable_funded_controller(graph)
    child = graph.add_node("Concept", {"name": "child"})
    parent = graph.add_node("Concept", {"name": "parent"})
    root = graph.add_node("Concept", {"name": "root"})
    graph.add_edge_unchecked(child, "causal_influence", parent)
    graph.add_edge_unchecked(parent, "causal_influence", root)
    monkeypatch.setattr(tot, "run_inner_conversation", lambda *a, **k: {
        "topics_thought": ["child"], "recovered_total": [],
        "stop_reason": "novelty_stalled",
    })
    result = rtot.run_regulated_train_of_thought(
        graph, topic="child", max_segments=1)
    assert set(result["tube_region"]) == {"child", "parent", "root"}


def test_terminal_restore(monkeypatch):
    graph = _native.Substrate()
    graph.add_node("Agent", {})
    _enable_funded_controller(graph)
    monkeypatch.setattr(tot, "run_inner_conversation", lambda *a, **k: (_ for _ in ()).throw(
        RuntimeError("candidate producer failed")))
    try:
        rtot.run_regulated_train_of_thought(
            graph, topic="topic-a", tube_region={"topic-a"}, max_segments=1)
    except RuntimeError as exc:
        assert str(exc) == "candidate producer failed"
    else:
        raise AssertionError("producer error was swallowed")
    policy = graph.nodes("ThoughtManifoldPolicy")[0]
    assert graph.node(policy)["attrs"]["enabled"] == 0.0


def test_budget_disabled_refuses_segment_generation(monkeypatch):
    graph = _native.Substrate()
    graph.add_node("Agent", {})
    rtot._native_controller_graph(graph)
    called = []
    monkeypatch.setattr(tot, "run_inner_conversation", lambda *a, **k: called.append(True))
    result = rtot.run_regulated_train_of_thought(
        graph, topic="topic-a", tube_region={"topic-a"}, max_segments=1)
    assert result["stop_reason"] == "budget_disabled"
    assert result["segments"] == []
    assert called == []
    assert graph.node(graph.nodes("ThinkingBudget")[0])["attrs"]["remaining"] == 16.0


def test_budget_denial_refuses_segment_generation(monkeypatch):
    graph = _native.Substrate()
    graph.add_node("Agent", {})
    _enable_funded_controller(graph)
    budget = graph.nodes("ThinkingBudget")[0]
    graph.set_attr(budget, "remaining", 0.0)
    called = []
    monkeypatch.setattr(tot, "run_inner_conversation", lambda *a, **k: called.append(True))
    result = rtot.run_regulated_train_of_thought(
        graph, topic="topic-a", tube_region={"topic-a"}, max_segments=1)
    assert result["stop_reason"] == "budget_denied"
    assert result["segments"] == []
    assert called == []
    assert graph.nodes("ThinkingBudgetDenial")


def test_epoch_change_expires_segment_before_accounting(monkeypatch):
    graph = _native.Substrate()
    graph.add_node("Agent", {})
    _enable_funded_controller(graph)
    mode = graph.nodes("NetworkModeState")[0]
    def produce(*args, **kwargs):
        graph.set_attr(mode, "epoch", graph.node(mode)["attrs"]["epoch"] + 1)
        return {"topics_thought": ["topic-a"], "recovered_total": [],
                "stop_reason": "continue"}
    monkeypatch.setattr(tot, "run_inner_conversation", produce)
    result = rtot.run_regulated_train_of_thought(
        graph, topic="topic-a", tube_region={"topic-a"}, max_segments=1)
    assert result["stop_reason"] == "stale_funding"
    assert result["segments"] == []
    assert graph.nodes("ThoughtManifoldStep") == []
    assert graph.nodes("GroundedReading") == []


def test_graph_controller_terminates_when_no_fresh_frontier_exists():
    graph = _native.Substrate()
    agent = graph.add_node("Agent", {})
    loaded = graph.load_seed_manifest(build_seed(), agent)
    assert loaded.get("rules_skipped") == []
    policy = graph.nodes("ThoughtManifoldPolicy")[0]
    graph.set_attr(policy, "enabled", 1.0)
    manifold = graph.add_node("ThoughtManifold", {
        "status": "running", "topic": "topic-a", "tube_region": ["topic-a"],
        "region_explicit": True,
        "seen_topics": ["topic-a"], "width": 2, "widen_step": 1,
        "narrow_step": 1, "deviation_wide_quanta": 2,
        "deviation_converge_quanta": 0, "segment_index": 0,
        "max_segments": 4, "detached_buffer": [],
        "detached_buffer_capacity": 64,
    })
    graph.add_edge(agent, "has_thought_manifold", manifold)
    segment = graph.add_node("ThoughtSegmentInput", {
        "status": "ready", "topics_thought": ["topic-a"],
        "stop_reason": "continue",
    })
    graph.add_edge(manifold, "has_pending_thought_segment", segment)
    for _ in range(10):
        if not graph.run_rules(1000):
            break
    else:
        raise AssertionError("ThoughtManifold controller did not reach a fixpoint")
    step = graph.nodes("ThoughtManifoldStep")[0]
    assert graph.node(step)["attrs"]["frontier_candidates"] == []
    assert graph.node(step)["attrs"]["next_topic"] is None
    assert graph.node(manifold)["attrs"]["status"] == "complete"
    assert graph.nodes("GroundedReading") == []


def test_graph_selects_initial_topic_from_in_tube_candidates():
    graph = _native.Substrate()
    agent = graph.add_node("Agent", {})
    loaded = graph.load_seed_manifest(build_seed(), agent)
    assert loaded.get("rules_skipped") == []
    policy = graph.nodes("ThoughtManifoldPolicy")[0]
    graph.set_attr(policy, "enabled", 1.0)
    manifold = graph.add_node("ThoughtManifold", {
        "status": "pending", "topic": None,
        "candidate_topics": ["outside-first", "inside-second"],
        "tube_region": ["inside-second"], "seen_topics": [],
        "region_explicit": True,
        "detached_buffer": [], "detached_buffer_capacity": 64,
    })
    graph.add_edge(agent, "has_thought_manifold", manifold)
    for _ in range(5):
        if not graph.run_rules(100):
            break
    assert graph.node(manifold)["attrs"]["topic"] == "inside-second"
    assert graph.node(manifold)["attrs"]["status"] == "running"
    assert list(graph.node(manifold)["attrs"]["seen_topics"]) == []


def test_detached_buffer_is_bounded():
    graph = _native.Substrate()
    agent = graph.add_node("Agent", {})
    loaded = graph.load_seed_manifest(build_seed(), agent)
    assert loaded.get("rules_skipped") == []
    policy = graph.nodes("ThoughtManifoldPolicy")[0]
    graph.set_attr(policy, "enabled", 1.0)
    manifold = graph.add_node("ThoughtManifold", {
        "status": "running", "topic": "topic-a", "tube_region": ["topic-a"],
        "region_explicit": True,
        "seen_topics": ["topic-a"], "width": 1, "widen_step": 1,
        "narrow_step": 1, "deviation_wide_quanta": 9,
        "deviation_converge_quanta": 0, "segment_index": 0,
        "max_segments": 4, "detached_buffer": ["old-1", "old-2"],
        "detached_buffer_capacity": 3,
    })
    graph.add_edge(agent, "has_thought_manifold", manifold)
    segment = graph.add_node("ThoughtSegmentInput", {
        "status": "ready", "topics_thought": ["topic-a", "new-1", "new-2"],
        "stop_reason": "novelty_stalled",
    })
    graph.add_edge(manifold, "has_pending_thought_segment", segment)
    for _ in range(10):
        if not graph.run_rules(1000):
            break
    else:
        raise AssertionError("ThoughtManifold controller did not reach a fixpoint")
    assert list(graph.node(manifold)["attrs"]["detached_buffer"]) == [
        "topic-a", "new-1", "new-2"]


def test_aperture_grain_deviation_and_frontier_are_graph_owned(monkeypatch):
    graph = _native.Substrate()
    graph.add_node("Agent", {})
    observer = graph.add_node("Observer", {
        "resolves": ["dynamical:valence"],
        "grain": {"dynamical:valence": 1.0}})
    _enable_funded_controller(graph)
    values = {"topic-a": [1], "off-tube": [2], "in-tube": [1, 3]}
    monkeypatch.setattr(rtot, "_signature_projection_inputs", lambda _wa, name: (
        [], [{"dimension": "dynamical:valence", "predicate": "field",
             "raw_value": value, "global_quantum": 1.0, "half_width": 10,
             "projection_status": "pending"} for value in values.get(name, [])]))
    emitted = iter((
        {"topics_thought": ["topic-a", "off-tube", "in-tube"],
         "recovered_total": [], "stop_reason": "continue"},
        {"topics_thought": ["in-tube"], "recovered_total": [],
         "stop_reason": "novelty_stalled"},
    ))
    topics = []
    def produce(_wa, *, topic, width, **_kwargs):
        topics.append((topic, width))
        return next(emitted)
    monkeypatch.setattr(tot, "run_inner_conversation", produce)

    result = rtot.run_regulated_train_of_thought(
        graph, topic="topic-a", setpoint_observer=observer,
        width0=0, deviation_wide_quanta=1, max_segments=3)

    assert topics == [("topic-a", 0), ("in-tube", 1)]
    assert result["deviation_trace"] == [2, 1]
    assert result["width_trace"] == [0, 1]
    assert result["setpoint_topic"] == "topic-a"
    assert graph.nodes("GroundedReading") == []
    steps = [graph.node(node)["attrs"] for node in graph.nodes("ThoughtManifoldStep")]
    assert steps[0]["frontier_candidates"] == ["in-tube"]
    assert steps[0]["deviation"] == 2


def test_unresolved_aperture_axis_is_dark_in_graph_projection(monkeypatch):
    graph = _native.Substrate()
    graph.add_node("Agent", {})
    observer = graph.add_node("Observer", {"resolves": [], "grain": {}})
    _enable_funded_controller(graph)
    monkeypatch.setattr(rtot, "_signature_projection_inputs", lambda _wa, _name: (
        [], [{"dimension": "dynamical:valence", "predicate": "field",
             "raw_value": 3.0, "global_quantum": 1.0, "half_width": 10,
             "projection_status": "pending"}]))
    monkeypatch.setattr(tot, "run_inner_conversation", lambda *_a, **_kw: {
        "topics_thought": ["topic-a"], "recovered_total": [],
        "stop_reason": "novelty_stalled"})

    result = rtot.run_regulated_train_of_thought(
        graph, topic="topic-a", setpoint_observer=observer,
        width0=0, max_segments=1)

    assert result["admitted_size"] == 0
    assert result["deviation_trace"] == [0]
    raw = graph.nodes("ThoughtRawSignatureCoordinate")
    assert raw and all(graph.node(node)["attrs"]["projection_status"] == "dark"
                       for node in raw)
