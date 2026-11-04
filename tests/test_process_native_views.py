"""Conformance for detached ProcessApply views of native sources."""

PROGRAM_IR = {
    "type": "ProgSeq",
    "stmts": [{"type": "ProgReturn", "value": {"type": "Var", "name": "x"}}],
}


def _program_agent():
    from evaluation.process_mastery.harness import Agent

    agent = Agent(track_i=True, view_enabled=True)
    source = agent.s.add_node("Program", {
        "name": "identity", "owner_agent": agent.ag, "source_epoch": 1,
        "model_epoch": 1, "frame_epoch": 2, "probe_epoch": 3,
    })
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
        "owner_agent": agent.ag, "source_epoch": 1, "frame_epoch": 2, "probe_epoch": 3,
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
    source = agent.s.add_node("CapabilityProgram", {
        "owner_agent": agent.ag, "source_epoch": 1, "frame_epoch": 2, "probe_epoch": 3,
        "order": 2, "model_epoch": 7,
    })
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
    motor = agent.s.add_node("EmbodiedMotorProgram", {
        "owner_agent": agent.ag, "source_epoch": 1, "model_epoch": 4,
        "frame_epoch": 2, "probe_epoch": 3, "predicted_forward": 1.0,
    })
    family = agent.s.add_node("FamilyProgram", {
        "owner_agent": agent.ag, "source_epoch": 1, "model_epoch": 1,
        "frame_epoch": 2, "probe_epoch": 3, "family_epoch": 2, "name": "authored",
    })
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
    source = agent.s.add_node("EmbodiedMotorProgram", {
        "owner_agent": agent.ag, "source_epoch": 1, "model_epoch": 4,
        "frame_epoch": 2, "probe_epoch": 3,
    })
    agent.run(max_ticks=20)
    view = next(s for s in agent.schemas("native:EmbodiedMotorProgram")
                if agent.attrs(s).get("realised_by") == source)
    assert agent.attrs(view)["post"] is None
    assert agent.attrs(view)["effect_evaluation"].startswith("opaque:")


def test_six_forms_have_source_views():
    agent, _, _, _ = _program_agent()
    common = {
        "owner_agent": agent.ag, "source_epoch": 1, "model_epoch": 1,
        "frame_epoch": 2, "probe_epoch": 3,
    }
    sources = {
        "DimensionGenerator": agent.s.add_node("DimensionGenerator", {
            **common, "name": "scale", "kind": "scale2", "coord_dims": [2],
            "modulus": 0, "matrix": [], "offset": [],
        }),
        "CapabilityProgram": agent.s.add_node("CapabilityProgram", {
            **common, "name": "cap", "order": 1,
        }),
        "TransitionHypothesis": agent.s.add_node("TransitionHypothesis", {
            **common, "name": "transition", "source_state_kind": "a",
            "action_kind": "step", "successor_state_kind": "b",
        }),
        "EmbodiedMotorProgram": agent.s.add_node("EmbodiedMotorProgram", {
            **common, "name": "motor",
        }),
        "FamilyProgram": agent.s.add_node("FamilyProgram", {
            **common, "name": "family",
        }),
    }
    agent.run(max_ticks=30)
    # Program was added by _program_agent and is the sixth source form.
    sources["Program"] = next(
        node for node in agent.s.nodes("Program")
        if agent.attrs(node).get("name") == "identity"
    )
    for source_type, source in sources.items():
        views = [s for s in agent.s.nodes("ProcessSchema")
                 if agent.attrs(s).get("realised_by") == source]
        assert len(views) == 1, source_type
        view = agent.attrs(views[0])
        assert view["owner_agent"] == agent.ag
        assert view["source_epoch"] == 1
        assert view["model_epoch"] == 1
        assert view["frame_epoch"] == 2
        assert view["probe_epoch"] == 0
        assert view["source_probe_epoch"] == 3, source_type


def test_probe_collision_retains_alternatives():
    from evaluation.process_mastery.harness import Agent

    agent = Agent(track_i=True, view_enabled=True)
    agent.add_domain("ambiguous", "permutation", [[0, 0, 0, 0]], {
        "first": [1, 0, 2, 3], "second": [0, 2, 1, 3],
    })
    agent.run(max_ticks=30)
    pair = [s for s in agent.schemas("ambiguous") if agent.attrs(s).get("name") in {"first", "second"}]
    assert len(pair) == 2
    assert agent.attrs(pair[0])["fingerprint"] == agent.attrs(pair[1])["fingerprint"]
    assert all(agent.attrs(s)["status"] == "active" for s in pair)
    assert agent.attrs(agent.domains["ambiguous"])["exact_probes"] == 0


def test_complete_perm_probe_dedups():
    from evaluation.process_mastery.harness import Agent

    agent = Agent(track_i=True, view_enabled=True)
    agent.add_domain("exact", "permutation", [[0, 1, 2, 3]], {
        "cheap": [1, 0, 2, 3],
    })
    duplicate = agent.s.add_node("ProcessSchema", {
        "kind": "permutation", "domain": "exact", "name": "expensive",
        "params": [1, 0, 2, 3], "cost": 4.0, "provenance": "held",
        "status": "active", "owner_agent": agent.ag, "source_epoch": 0,
        "model_epoch": 0, "frame_epoch": 0, "probe_epoch": 0,
            "source_probe_epoch": 0, "invariants": [],
    })
    agent.s.add_edge(agent.ag, "has_process_schema", duplicate)
    agent.run(max_ticks=30)
    cheap = next(s for s in agent.schemas("exact") if agent.attrs(s).get("name") == "cheap")
    assert agent.attrs(cheap)["status"] == "active"
    assert agent.attrs(duplicate)["status"] == "merged"


def test_probe_epoch_change_reopens_prior_dedup():
    from evaluation.process_mastery.harness import Agent

    agent = Agent(track_i=True, view_enabled=True)
    domain = agent.add_domain("reopened", "permutation", [[0, 1, 2, 3]], {
        "cheap": [1, 0, 2, 3],
    })
    duplicate = agent.s.add_node("ProcessSchema", {
        "kind": "permutation", "domain": "reopened", "name": "expensive",
        "params": [1, 0, 2, 3], "cost": 4.0, "provenance": "held",
        "status": "active", "owner_agent": agent.ag, "source_epoch": 0,
        "model_epoch": 0, "frame_epoch": 0, "probe_epoch": 0,
        "source_probe_epoch": 0, "invariants": [],
    })
    agent.s.add_edge(agent.ag, "has_process_schema", duplicate)
    agent.run(max_ticks=30)
    assert agent.attrs(duplicate)["status"] == "merged"
    agent.s.set_attr(domain, "probes", [[0, 0, 0, 0]])
    agent.s.set_attr(domain, "probe_epoch", 1)
    agent.run(max_ticks=30)
    cheap = next(s for s in agent.schemas("reopened") if agent.attrs(s).get("name") == "cheap")
    assert agent.attrs(cheap)["status"] == "active"
    assert agent.attrs(duplicate)["status"] == "active"


def test_stale_view_recomputed():
    agent, source, old_view, _ = _program_agent()
    agent.s.set_attr(source, "source_epoch", 2)
    agent.run(max_ticks=30)
    assert agent.attrs(old_view)["status"] == "stale"
    refreshed = [s for s in agent.s.nodes("ProcessSchema")
                 if agent.attrs(s).get("realised_by") == source
                 and agent.attrs(s).get("source_epoch") == 2]
    assert len(refreshed) == 1


def test_deleted_source_retires_view():
    agent, source, old_view, _ = _program_agent()
    agent.s.remove_node(source)
    agent.run(max_ticks=30)
    assert agent.attrs(old_view)["status"] == "stale"


def test_probe_epoch_recomputes_fingerprint():
    from evaluation.process_mastery.harness import Agent

    agent = Agent(track_i=True, view_enabled=True)
    domain = agent.add_domain("probe_epoch", "permutation", [[0, 1, 2, 3]], {
        "move": [1, 0, 2, 3],
    })
    agent.run(max_ticks=30)
    schema = next(s for s in agent.schemas("probe_epoch") if agent.attrs(s).get("name") == "move")
    before = agent.attrs(schema)["fingerprint"]
    agent.s.set_attr(domain, "probes", [[0, 0, 0, 0]])
    agent.s.set_attr(domain, "probe_epoch", 1)
    agent.run(max_ticks=30)
    attrs = agent.attrs(schema)
    assert attrs["probe_epoch"] == 1
    assert attrs["fingerprint"] != before


def test_cross_owner_view_isolation():
    agent, source, view, _ = _program_agent()
    other = agent.s.add_node("Agent", {})
    policy = agent.s.add_node("ProcessSchemaPolicy", {
        "name": "other_policy", "enabled": 1.0, "view_enabled": 1.0,
    })
    agent.s.add_edge(other, "has_process_schema_policy", policy)
    agent.s.set_attr(source, "owner_agent", agent.ag)
    agent.run(max_ticks=30)
    views = [s for s in agent.s.nodes("ProcessSchema")
             if agent.attrs(s).get("realised_by") == source]
    assert len(views) == 1
    assert agent.attrs(views[0])["owner_agent"] == agent.ag
    assert agent.attrs(views[0])["owner_agent"] != other


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
