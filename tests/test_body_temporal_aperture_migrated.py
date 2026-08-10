"""THE OBSERVATION APERTURE BELONGS TO THE BODY — the migrated gate.

How long you must watch before a movement exceeds one quantization unit is a
fact about the body, not about whichever program happens to be running. Held on
the program it was thrown away at every switch: measured live over 49 trials,
44 of 45 programs sat at 1 frame while the body needs >= 8 to move one
proprioceptive quantum, so the developmental success criterion could never
evaluate true.

The middle gate is the actual repair: a FRESH program inherits the body's
climbed aperture instead of restarting the ladder.
"""
from domains.engine_provenance import engine_preamble
engine_preamble()

from substrate.seed_loader import manifest_for                          # noqa: E402
from substrate.world_adapter import WorldAdapter                        # noqa: E402


MINIMUM_FRAMES = 1
HORIZON_FRAMES = 480


def _agent():
    agent = WorldAdapter()
    agent.inner.load_seed_manifest(manifest_for("embodied_motor_bootstrap"),
                                   agent.agent)
    return agent


def _edge(agent, source, edge_type, target):
    agent.inner.add_edge_unchecked(source, edge_type, target)


def _episode(agent):
    """The minimum graph the aperture rules read: an episode with a body, a
    world contract, and a motor episode to hang candidates off."""
    agent_id = agent.agent
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {})
    _edge(agent, agent_id, "has_embodied_development_episode", episode)
    body = agent.s.add_node("EmbodiedBodySchema", {
        "body_identity": "test_body", "integer_native": 1})
    _edge(agent, episode, "has_embodied_body_schema", body)
    world = agent.s.add_node("EmbodiedLearningWorld", {})
    _edge(agent, episode, "has_embodied_learning_world", world)
    contract = agent.s.add_node("EmbodiedMotorBootstrapContract", {
        "minimum_actuation_frames": MINIMUM_FRAMES,
        "maximum_observation_horizon_frames": HORIZON_FRAMES,
        "integer_native": 1})
    _edge(agent, world, "has_embodied_motor_bootstrap_contract", contract)
    motor = agent.s.add_node("EmbodiedMotorEpisode", {})
    _edge(agent, episode, "has_embodied_motor_episode", motor)
    agent.inner.run_rules()
    return episode, body, motor


def _program(agent, motor, **program_attrs):
    """A candidate proposing a program — the shape the aperture rules match."""
    candidate = agent.s.add_node("EmbodiedMotorBootstrapCandidate", {})
    _edge(agent, motor, "has_embodied_motor_bootstrap_candidate", candidate)
    program = agent.s.add_node("EmbodiedMotorProgram",
                               {"integer_native": 1, **program_attrs})
    _edge(agent, candidate, "proposes_embodied_motor_program", program)
    agent.inner.run_rules()
    return program


def _frames(agent, program):
    return agent.s.node(program)["attrs"]["simulator_frames"]


def _climb(agent, body, steps=1):
    """Raise the body's aperture the way the enact rule does — by incrementing
    the exponent. The rule itself carries a 20-edge supervisory match; what is
    under test here is that the CLIMB IS HELD ON THE BODY and inherited."""
    for _ in range(steps):
        attrs = agent.s.node(body)["attrs"]
        agent.inner.set_attr(body, "temporal_aperture_log_units",
                             int(attrs.get("temporal_aperture_log_units") or 0) + 1)
        agent.inner.set_attr(body, "temporal_aperture_measured", 1)
    agent.inner.run_rules()


# ------------------------------------------------------------- gate 1

def test_the_body_opens_its_aperture_declared_not_measured():
    agent = _agent()
    _episode_id, body, _motor = _episode(agent)
    attrs = agent.s.node(body)["attrs"]
    assert attrs["temporal_aperture_log_units"] == 0
    # Provenance, on the ledger's discipline: a declared floor is usable and is
    # never confusable with a climbed one.
    assert attrs["temporal_aperture_measured"] == 0


def test_the_bodys_aperture_climbs_and_says_it_was_measured():
    agent = _agent()
    _episode_id, body, motor = _episode(agent)
    program = _program(agent, motor)
    assert _frames(agent, program) == 1
    _climb(agent, body, steps=3)
    attrs = agent.s.node(body)["attrs"]
    assert attrs["temporal_aperture_log_units"] == 3
    assert attrs["temporal_aperture_measured"] == 1
    # 2**3 — the same doubling the old rule did, held where it is true.
    assert _frames(agent, program) == 8


# ------------------------------------------- gate 2: THE ACTUAL REPAIR

def test_a_fresh_never_seen_program_inherits_the_bodys_climbed_aperture():
    """THE DEFECT, GATED.

    A program that has never been enacted, proposed AFTER the body climbed,
    must start at the body's aperture — not at the bottom of the ladder. Held
    on the program, this is exactly what did not happen: 44 of 45 live programs
    sat at 1 frame because each switch discarded the climb.
    """
    agent = _agent()
    _episode_id, body, motor = _episode(agent)
    veteran = _program(agent, motor)
    _climb(agent, body, steps=3)
    assert _frames(agent, veteran) == 8

    fresh = _program(agent, motor)
    assert fresh != veteran
    assert _frames(agent, fresh) == 8, "a fresh program restarted the ladder"
    # And it says where the number came from, and that the body earned it.
    fresh_attrs = agent.s.node(fresh)["attrs"]
    assert fresh_attrs["aperture_source"] == "body_scaled_hint"
    assert fresh_attrs["aperture_measured"] == 1


def test_switching_programs_never_costs_the_body_its_climb():
    agent = _agent()
    _episode_id, body, motor = _episode(agent)
    _climb(agent, body, steps=2)
    apertures = [_frames(agent, _program(agent, motor)) for _ in range(5)]
    assert apertures == [4, 4, 4, 4, 4]
    assert agent.s.node(body)["attrs"]["temporal_aperture_log_units"] == 2


# ------------------------------------------------------------- gate 3

def test_a_program_hint_scales_the_bodys_aperture_without_mutating_it():
    agent = _agent()
    _episode_id, body, motor = _episode(agent)
    _climb(agent, body, steps=3)
    baseline = _program(agent, motor)
    slower = _program(agent, motor, aperture_hint_log_units=1)
    quicker = _program(agent, motor, aperture_hint_log_units=-1)
    assert (_frames(agent, baseline), _frames(agent, slower),
            _frames(agent, quicker)) == (8, 16, 4)
    # The hint is a SCALING, not an aperture: the body's value is untouched.
    assert agent.s.node(body)["attrs"]["temporal_aperture_log_units"] == 3


def test_a_hinted_program_still_inherits_every_later_climb():
    """A hint is relative, so it cannot strand a program below the body."""
    agent = _agent()
    _episode_id, body, motor = _episode(agent)
    hinted = _program(agent, motor, aperture_hint_log_units=-1)
    _climb(agent, body, steps=1)
    assert _frames(agent, hinted) == 1      # 2**0, floored at the minimum
    _climb(agent, body, steps=3)
    assert _frames(agent, hinted) == 8      # 2**(4-1)


def test_the_aperture_stays_inside_the_worlds_declared_bounds():
    """The exponent is the body's adaptation; the contract remains the bound."""
    agent = _agent()
    _episode_id, body, motor = _episode(agent)
    deep = _program(agent, motor, aperture_hint_log_units=-9)
    assert _frames(agent, deep) == MINIMUM_FRAMES
    _climb(agent, body, steps=12)
    assert _frames(agent, _program(agent, motor)) == HORIZON_FRAMES


def test_the_neutral_hint_is_declared_and_means_no_scaling():
    """0 is the honest neutral in this log dimension, and it is DECLARED.

    Left absent it would still read as no scaling, but the mechanism would be
    invisible in the graph. Declaring it must not be able to erase a hint that
    was already set — that is what the absent-vs-zero guard on the initializer
    is for.
    """
    agent = _agent()
    _episode_id, body, motor = _episode(agent)
    _climb(agent, body, steps=2)
    program = _program(agent, motor)
    assert agent.s.node(program)["attrs"]["aperture_hint_log_units"] == 0
    assert _frames(agent, program) == 4

    preset = _program(agent, motor, aperture_hint_log_units=1)
    assert agent.s.node(preset)["attrs"]["aperture_hint_log_units"] == 1


def test_the_exponent_scales_the_declared_minimum_not_an_absolute_frame_count():
    """A DEFECT FOUND AND FIXED WHILE BUILDING THIS, gated so it cannot return.

    The exponent was first written as an absolute `2 ** k`. Against a world
    declaring a minimum actuation of 13 frames, the first four climbs were
    absorbed entirely by the floor clamp: the body climbed and the aperture did
    not move. Anchoring the ladder AT the declared minimum makes k mean
    "doublings above the mechanical baseline" at every contract, not only at a
    contract whose minimum happens to be 1.
    """
    agent = _agent()
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {})
    _edge(agent, agent.agent, "has_embodied_development_episode", episode)
    body = agent.s.add_node("EmbodiedBodySchema", {"integer_native": 1})
    _edge(agent, episode, "has_embodied_body_schema", body)
    world = agent.s.add_node("EmbodiedLearningWorld", {})
    _edge(agent, episode, "has_embodied_learning_world", world)
    contract = agent.s.add_node("EmbodiedMotorBootstrapContract", {
        "minimum_actuation_frames": 13,
        "maximum_observation_horizon_frames": HORIZON_FRAMES,
        "integer_native": 1})
    _edge(agent, world, "has_embodied_motor_bootstrap_contract", contract)
    motor = agent.s.add_node("EmbodiedMotorEpisode", {})
    _edge(agent, episode, "has_embodied_motor_episode", motor)
    agent.inner.run_rules()

    program = _program(agent, motor)
    assert _frames(agent, program) == 13
    # ONE climb must be ONE doubling — the semantics of the rule it replaced.
    _climb(agent, body, steps=1)
    assert _frames(agent, program) == 26
    _climb(agent, body, steps=1)
    assert _frames(agent, program) == 52
