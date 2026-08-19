"""THE EFFECTOR SURVEY'S COMPLETENESS IS DERIVED FROM THE BODY — migrated gate.

Stage 1 (`effector_consequence_survey`) scores a receipt successful only when
`episode.development_effector_coverage_complete == 1`. That field was read by
six rules and written by none, so stage 1 sat at 118 attempts / 0 successes —
the same shape that held stage 0 at zero for thirteen hours before its own
field was written.

Complete means: every effector THE BODY DECLARES has been exercised by at
least one GROUNDED receipt. The headline gate is the trap: `covered ==
declared` with a zero declared count is `0 == 0`, which would read as a fully
surveyed body having surveyed nothing.
"""
from domains.engine_provenance import engine_preamble
engine_preamble()

from substrate.seed_loader import manifest_for                          # noqa: E402
from substrate.world_adapter import WorldAdapter                        # noqa: E402


def _agent():
    agent = WorldAdapter()
    agent.inner.load_seed_manifest(manifest_for("embodied_development"),
                                   agent.agent)
    return agent


def _edge(agent, s, e, t):
    agent.inner.add_edge_unchecked(s, e, t)


def _body(agent, *, effectors, exercised=0):
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode",
                               {"development_learning_active": 1})
    _edge(agent, agent.agent, "has_embodied_development_episode", episode)
    schema = agent.s.add_node("EmbodiedBodySchema", {"integer_native": 1})
    _edge(agent, episode, "has_embodied_body_schema", schema)
    raw = agent.s.add_node("EmbodiedRawBodyObservation", {"integer_native": 1})
    _edge(agent, schema, "grounded_in_embodied_raw_body", raw)
    for ordinal in range(effectors):
        affordance = agent.s.add_node("EmbodiedOpaqueActuatorAffordance", {
            "ordinal": ordinal, "integer_native": 1})
        _edge(agent, schema, "has_opaque_embodied_actuator_affordance", affordance)
        candidate = agent.s.add_node("EmbodiedMotorBootstrapCandidate", {
            "actuator_ordinal": ordinal,
            "experience_units": 1 if ordinal < exercised else 0,
            "integer_native": 1})
        _edge(agent, candidate, "models_opaque_affordance", affordance)
    agent.inner.run_rules()
    return episode


def _attrs(agent, episode):
    return agent.s.node(episode)["attrs"]


# ------------------------------------------------------------- the trap

def test_a_body_with_no_declared_effectors_is_unmeasurable_not_complete():
    """THE HEADLINE. `covered == declared` at zero is `0 == 0`, which would
    hand stage 1 a free pass for having surveyed nothing — exactly as a vacuous
    window would have handed retention one."""
    agent = _agent()
    attrs = _attrs(agent, _body(agent, effectors=0))
    assert attrs["development_effector_declared_count"] == 0
    assert attrs["development_effector_coverage_complete"] == 0
    assert attrs["development_effector_coverage_unmeasurable"] == 1


def test_unmeasurable_is_a_different_statement_from_incomplete():
    agent = _agent()
    partial = _attrs(agent, _body(agent, effectors=4, exercised=1))
    assert partial["development_effector_coverage_complete"] == 0
    assert partial["development_effector_coverage_unmeasurable"] == 0


# --------------------------------------------------------- the derivation

def test_coverage_counts_are_read_off_the_bodys_own_declarations():
    agent = _agent()
    attrs = _attrs(agent, _body(agent, effectors=5, exercised=2))
    assert attrs["development_effector_declared_count"] == 5
    assert attrs["development_effector_covered_count"] == 2


def test_verified_humanoid_transition_exercises_its_opaque_affordance():
    agent = _agent()
    episode = _body(agent, effectors=2, exercised=0)
    affordance = list(agent.s.nodes(
        "EmbodiedOpaqueActuatorAffordance"
    ))[0]
    receipt = agent.s.add_node("HumanoidTransition", {
        "causal_receipt_closed": 1,
        "development_receipt_closed": 1,
    })
    _edge(
        agent,
        receipt,
        "exercises_opaque_embodied_actuator_affordance",
        affordance,
    )
    agent.inner.run_rules()

    attrs = _attrs(agent, episode)
    assert attrs["development_effector_covered_count"] == 1
    assert agent.s.node(affordance)["attrs"]["exercised"] == 1


def test_a_partially_surveyed_body_is_not_complete():
    agent = _agent()
    attrs = _attrs(agent, _body(agent, effectors=5, exercised=4))
    assert attrs["development_effector_coverage_complete"] == 0


def test_a_fully_surveyed_body_is_complete():
    agent = _agent()
    attrs = _attrs(agent, _body(agent, effectors=5, exercised=5))
    assert attrs["development_effector_covered_count"] == 5
    assert attrs["development_effector_coverage_complete"] == 1
    assert attrs["development_effector_coverage_unmeasurable"] == 0


def test_an_unexercised_effector_keeps_the_survey_open():
    """A proposal is not a trial: `experience_units` rises only against
    grounded evidence, so an unexercised effector must hold the survey open."""
    agent = _agent()
    episode = _body(agent, effectors=3, exercised=3)
    assert _attrs(agent, episode)["development_effector_coverage_complete"] == 1
    extra = agent.s.add_node("EmbodiedOpaqueActuatorAffordance",
                             {"ordinal": 99, "integer_native": 1})
    schema = list(agent.s.nodes("EmbodiedBodySchema"))[0]
    _edge(agent, schema, "has_opaque_embodied_actuator_affordance", extra)
    agent.inner.run_rules()
    attrs = _attrs(agent, episode)
    assert attrs["development_effector_declared_count"] == 4
    assert attrs["development_effector_covered_count"] == 3
    assert attrs["development_effector_coverage_complete"] == 0


def test_coverage_reopens_when_the_body_grows():
    """Completeness is restated from the body every pass, not latched."""
    agent = _agent()
    episode = _body(agent, effectors=2, exercised=2)
    assert _attrs(agent, episode)["development_effector_coverage_complete"] == 1
    schema = list(agent.s.nodes("EmbodiedBodySchema"))[0]
    grown = agent.s.add_node("EmbodiedOpaqueActuatorAffordance",
                             {"ordinal": 7, "integer_native": 1})
    _edge(agent, schema, "has_opaque_embodied_actuator_affordance", grown)
    agent.inner.run_rules()
    assert _attrs(agent, episode)["development_effector_coverage_complete"] == 0


def test_the_assertion_is_idempotent_under_a_re_run_fixpoint():
    agent = _agent()
    episode = _body(agent, effectors=3, exercised=3)
    for _ in range(4):
        agent.inner.run_rules()
        assert _attrs(agent, episode)["development_effector_coverage_complete"] == 1


def test_partial_effector_coverage_is_incremental_developmental_evidence():
    """A newly exercised affordance earns one success before full coverage."""
    agent = _agent()
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_learning_active": 1,
        "development_evidence_window": 2,
        "latest_development_receipt_seq": 1,
        "development_effector_covered_count": 1,
    })
    _edge(agent, agent.agent, "has_embodied_development_episode", episode)
    survey = agent.s.add_node("EmbodiedSituatedDevelopmentalCapability", {
        "name": "effector_consequence_survey",
        "goal": "effector_discovery",
        "evidence_kind": "effector_coverage",
        "status": "active",
        "attempt_count": 0,
        "success_count": 0,
        "failure_count": 0,
        "effector_coverage_scored_count": 0,
        "activation_receipt_seq": 0,
        "last_receipt_seq": 0,
    })
    _edge(
        agent, episode, "has_embodied_developmental_capability", survey
    )
    _edge(
        agent, episode, "has_active_embodied_developmental_capability", survey
    )
    receipt = agent.s.add_node("EmbodiedDevelopmentReceipt", {
        "development_receipt_seq": 1,
        "development_receipt_closed": 1,
        "development_configuration_changed": 1,
        "development_context_signature": (("effector", 0),),
    })
    _edge(agent, episode, "has_embodied_development_receipt", receipt)
    agent.inner.run_rules()

    attrs = agent.s.node(survey)["attrs"]
    assert attrs["attempt_count"] == 1
    assert attrs["success_count"] == 1
    assert attrs["failure_count"] == 0
    assert attrs["effector_coverage_scored_count"] == 1


def test_complete_effector_coverage_allows_delayed_successful_retest():
    agent = _agent()
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_learning_active": 1,
        "development_evidence_window": 2,
        "latest_development_receipt_seq": 3,
        "development_effector_covered_count": 1,
        "development_effector_coverage_complete": 1,
    })
    _edge(agent, agent.agent, "has_embodied_development_episode", episode)
    survey = agent.s.add_node("EmbodiedSituatedDevelopmentalCapability", {
        "name": "effector_consequence_survey",
        "goal": "effector_discovery",
        "evidence_kind": "effector_coverage",
        "status": "retention_due",
        "attempt_count": 1,
        "success_count": 1,
        "failure_count": 0,
        "effector_coverage_scored_count": 1,
        "activation_receipt_seq": 0,
        "last_receipt_seq": 2,
        "retention_start_seq": 0,
    })
    _edge(
        agent, episode, "has_embodied_developmental_capability", survey
    )
    _edge(
        agent, episode, "has_active_embodied_developmental_capability", survey
    )
    receipt = agent.s.add_node("EmbodiedDevelopmentReceipt", {
        "development_receipt_seq": 3,
        "development_receipt_closed": 1,
        "development_configuration_changed": 1,
        "development_context_signature": (("effector", 0),),
    })
    _edge(agent, episode, "has_embodied_development_receipt", receipt)
    agent.inner.run_rules()

    assert agent.s.node(survey)["attrs"]["status"] == "mastered"
