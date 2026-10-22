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


def test_source_epoch_invalidates_view():
    agent, source, schema, _ = _program_agent()
    agent.s.set_attr(source, "source_epoch", 2)
    result = agent.s._inner.evaluate(
        {"type": "ProcessApply", "p": {"type": "Var", "name": "process"},
         "state": {"type": "Var", "name": "state"}},
        {"process": schema, "state": {"x": 9}},
    )
    assert result is None


def test_capability_view_matches_native():
    agent, _, _, _ = _program_agent()
    source = agent.s.add_node("CapabilityProgram", {"order": 2, "model_epoch": 7})
    agent.run(max_ticks=20)
    view = next(s for s in agent.schemas("native:CapabilityProgram")
                if agent.attrs(s).get("realised_by") == source)
    assert agent.attrs(view)["effect_evaluation"] == "opaque:no_detached_effect_evaluator"
    result = agent.s._inner.evaluate(
        {"type": "ProcessApply", "p": {"type": "Var", "name": "process"},
         "state": {"type": "Var", "name": "state"}},
        {"process": view, "state": {"capability": "x"}},
    )
    assert result is None


def test_motor_family_model_view():
    agent, _, _, _ = _program_agent()
    motor = agent.s.add_node("EmbodiedMotorProgram", {"model_epoch": 4, "predicted_forward": 1.0})
    family = agent.s.add_node("FamilyProgram", {"family_epoch": 2, "name": "authored"})
    agent.run(max_ticks=20)
    for source, kind, reason in (
        (motor, "native:EmbodiedMotorProgram", "opaque:model_prediction_is_not_observed_effect"),
        (family, "native:FamilyProgram", "opaque:no_safe_family_executor"),
    ):
        view = next(s for s in agent.schemas(kind) if agent.attrs(s).get("realised_by") == source)
        assert agent.attrs(view)["effect_evaluation"] == reason
        result = agent.s._inner.evaluate(
            {"type": "ProcessApply", "p": {"type": "Var", "name": "process"},
             "state": {"type": "Var", "name": "state"}},
            {"process": view, "state": {"state": "start"}},
        )
        assert result is None


def test_unsupported_model_stays_opaque():
    agent, _, _, _ = _program_agent()
    source = agent.s.add_node("EmbodiedMotorProgram", {"model_epoch": 4})
    agent.run(max_ticks=20)
    view = next(s for s in agent.schemas("native:EmbodiedMotorProgram")
                if agent.attrs(s).get("realised_by") == source)
    assert agent.attrs(view)["post"] is None
    assert agent.attrs(view)["effect_evaluation"].startswith("opaque:")


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
