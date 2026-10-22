"""Conformance for detached ProcessApply views of native sources."""

PROGRAM_IR = {
    "type": "ProgSeq",
    "stmts": [{"type": "ProgReturn", "value": {"type": "Var", "name": "x"}}],
}


def _program_agent():
    from evaluation.process_mastery.harness import Agent

    agent = Agent(track_i=True, view_enabled=True)
    source = agent.s.add_node("Program", {"name": "identity", "source_epoch": 1})
    root = agent.native.add_term_subgraph(PROGRAM_IR)
    agent.native.add_edge_unchecked(source, "ir_subgraph", root, {})
    agent.run(max_ticks=20)
    schema = next(
        node for node in agent.schemas("native:Program")
        if agent.attrs(node).get("realised_by") == source
    )
    return agent, source, schema, root


def test_program_view_matches_native():
    agent, source, schema, root = _program_agent()
    native = agent.s._inner.evaluate(
        {"type": "ProgEval", "prog": {"type": "Var", "name": "program"},
         "env": {"type": "Var", "name": "inputs"}, "oracles": None,
         "fuel": 10_000, "field": "result"},
        {"program": root, "inputs": {"x": 41}},
    )
    applied = agent.s._inner.evaluate(
        {"type": "ProcessApply", "p": {"type": "Var", "name": "process"},
         "state": {"type": "Var", "name": "state"}},
        {"process": schema, "state": {"x": 41}},
    )
    assert native == 41
    assert applied == native
    assert agent.attrs(schema)["realised_by"] == source


def test_transition_view_matches_native():
    # TransitionHypothesis has planner predictions but no native finite
    # state-effect evaluator. ProcessApply must leave the view opaque.
    agent, _, _, _ = _program_agent()
    transition = agent.s.add_node("TransitionHypothesis", {
        "source_state_kind": "cold", "action_kind": "heat",
        "successor_state_kind": "warm", "model_epoch": 3,
    })
    agent.run(max_ticks=20)
    views = [s for s in agent.schemas("native:TransitionHypothesis")
             if agent.attrs(s).get("realised_by") == transition]
    assert len(views) == 1
    result = agent.s._inner.evaluate(
        {"type": "ProcessApply", "p": {"type": "Var", "name": "process"},
         "state": {"type": "Var", "name": "state"}},
        {"process": views[0], "state": {"state": "cold"}},
    )
    assert result is None


def test_process_precondition_unknown():
    agent, _, schema, _ = _program_agent()
    assert agent.attrs(schema).get("pre") is None


def test_program_view_rejects_stale_source_epoch():
    agent, source, schema, _ = _program_agent()
    agent.s.set_attr(source, "source_epoch", 2)
    result = agent.s._inner.evaluate(
        {"type": "ProcessApply", "p": {"type": "Var", "name": "process"},
         "state": {"type": "Var", "name": "state"}},
        {"process": schema, "state": {"x": 9}},
    )
    assert result is None


def test_apply_has_no_external_effect():
    agent, _, schema, _ = _program_agent()
    before = agent.s.node_count()
    result = agent.s._inner.evaluate(
        {"type": "ProcessApply", "p": {"type": "Var", "name": "process"},
         "state": {"type": "Var", "name": "state"}},
        {"process": schema, "state": {"x": 9}},
    )
    assert result == 9
    assert agent.s.node_count() == before
