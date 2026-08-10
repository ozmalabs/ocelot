"""THE RECEIPT WINDOW IS BODY-DERIVED — the migrated gate.

`development_evidence_window` was written by nothing in any seed. Two of the
three guards in `ed_open_delayed_retention_test_after_varied_competence`
compared against it through the `+0` idiom, so they read against 0 and passed
unconditionally — while the rule's comment claimed it required "a body-derived
receipt window". A comment asserting a check the code does not perform is the
most dangerous form of this bug, because it stops anyone looking.

These gates pin the three things that must now hold: the window is derived from
the body, an absent window REFUSES rather than waves through, and the gate
opens only when the derived demand is actually met.
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


def _edge(agent, source, edge_type, target):
    agent.inner.add_edge_unchecked(source, edge_type, target)


def _episode(agent, *, actuated_joint_count=None):
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode",
                               {"development_learning_active": 1})
    _edge(agent, agent.agent, "has_embodied_development_episode", episode)
    if actuated_joint_count is not None:
        body = agent.s.add_node("EmbodiedBodySchema", {"integer_native": 1})
        _edge(agent, episode, "has_embodied_body_schema", body)
        raw = agent.s.add_node("EmbodiedRawBodyObservation", {
            "actuated_joint_count": actuated_joint_count, "integer_native": 1})
        _edge(agent, body, "grounded_in_embodied_raw_body", raw)
    agent.inner.run_rules()
    return episode


def _capability(agent, episode, *, attempts, successes, contexts):
    instance = agent.s.add_node("EmbodiedSituatedDevelopmentalCapability", {
        "name": "spontaneous_general_movement", "ordinal": 0,
        "evidence_kind": "spontaneous_configuration_change", "status": "active",
        "attempt_count": attempts, "success_count": successes,
        "failure_count": attempts - successes, "retention_count": 0,
        "last_receipt_seq": 0, "activation_receipt_seq": 0, "integer_native": 1})
    _edge(agent, episode, "has_active_embodied_developmental_capability", instance)
    for _ in range(contexts):
        ctx = agent.s.add_node("EmbodiedDevelopmentalContext", {"integer_native": 1})
        _edge(agent, instance, "has_embodied_developmental_context", ctx)
    agent.inner.run_rules()
    return instance


def _status(agent, instance):
    return agent.s.node(instance)["attrs"]["status"]


# ------------------------------------------------------- the derivation

def test_the_window_is_read_off_the_bodys_actuated_degrees_of_freedom():
    agent = _agent()
    episode = _episode(agent, actuated_joint_count=21)
    attrs = agent.s.node(episode)["attrs"]
    assert attrs["development_evidence_window"] == 21
    # Provenance, and the relatum named IN THE GRAPH rather than only in prose.
    assert attrs["development_evidence_window_measured"] == 1
    assert attrs["development_evidence_window_relatum"] == "actuated_joint_count"


def test_a_richer_body_owes_more_evidence():
    simple = _agent()
    rich = _agent()
    assert (simple.s.node(_episode(simple, actuated_joint_count=2))["attrs"]
            ["development_evidence_window"]
            < rich.s.node(_episode(rich, actuated_joint_count=21))["attrs"]
            ["development_evidence_window"])


# ------------------------------------- absent is distinguishable from zero

def test_a_body_declaring_no_degrees_of_freedom_leaves_the_window_absent():
    """Not 0 — ABSENT. 0 is what made the guard vacuous in the first place."""
    agent = _agent()
    episode = _episode(agent, actuated_joint_count=0)
    assert "development_evidence_window" not in agent.s.node(episode)["attrs"]


def test_no_body_leaves_the_window_absent_and_retention_refuses_to_open():
    """THE FALSE ASSURANCE, GATED.

    With no window derived, the old guards compared against a coalesced 0 and
    passed, so ONE success opened retention. It must now refuse: failing to
    have a window is not the same as having met it.
    """
    agent = _agent()
    episode = _episode(agent)
    assert "development_evidence_window" not in agent.s.node(episode)["attrs"]
    instance = _capability(agent, episode, attempts=1, successes=1, contexts=1)
    assert _status(agent, instance) == "active"
    assert agent.inner.neighbours(
        episode, "has_active_embodied_developmental_capability")


# --------------------------------------------- the gate enforces the demand

def test_retention_refuses_a_single_success_when_the_window_demands_more():
    agent = _agent()
    episode = _episode(agent, actuated_joint_count=21)
    instance = _capability(agent, episode, attempts=1, successes=1, contexts=1)
    assert _status(agent, instance) == "active"


def test_retention_opens_once_the_windows_demand_is_met():
    agent = _agent()
    episode = _episode(agent, actuated_joint_count=21)
    instance = _capability(agent, episode, attempts=21, successes=21, contexts=1)
    assert _status(agent, instance) == "retention_due"


def test_attempts_alone_do_not_meet_the_window():
    """Both guards are real now: trying 21 times is not succeeding 21 times."""
    agent = _agent()
    episode = _episode(agent, actuated_joint_count=21)
    instance = _capability(agent, episode, attempts=21, successes=3, contexts=1)
    assert _status(agent, instance) == "active"


def test_the_context_guard_still_binds_on_top_of_the_window():
    agent = _agent()
    episode = _episode(agent, actuated_joint_count=3)
    instance = _capability(agent, episode, attempts=5, successes=5, contexts=0)
    assert _status(agent, instance) == "active"
