"""Gates for order-1 -> order-0 condensation, and for its release.

Training is the existence proof that order-0 content is overwhelmingly LEARNED,
so the reflex index has to GROW from the agent's own repeated success -- and it
has to DECAY, or the agent is welded to its own history.  These gates hold both
halves, because condensation without release is the failure mode the design is
against.

Every one of the four defects these gates would have caught was found by
measurement, not by reading the seed, and each is asserted here directly:

  * the ordinal must be a LOG bucket (linear spans seven orders of magnitude
    and mints one shape per encounter);
  * a numeric attr read back and recompared must be integer-coerced;
  * the response identity must be the program's SIGNATURE, not its serial name;
  * a String attr must be read with `A`, never `P0` -- `Plus(Attr, 0.0)` on a
    String never compares equal, which silently forces the vary branch.
"""
from __future__ import annotations

import math

import pytest

from substrate.world_adapter import WorldAdapter


CONDENSE_AFTER = 3.0
QUANTUM = 1.0


def _edge(agent, source, edge_type, target):
    try:
        agent.inner.add_edge_unchecked(source, edge_type, target, {})
    except TypeError:
        agent.inner.add_edge_unchecked(source, edge_type, target)


class _Bench:
    """The smallest graph the condensation rules can run on."""

    def __init__(self, agent, root, episode, program, model):
        self.agent = agent
        self.root = root
        self.episode = episode
        self.program = program
        self.model = model
        self.seq = 0

    def encounter(self) -> None:
        """One verified receipt against the current program."""
        self.seq += 1
        # Outcomes are stamped with the episode's current action seq; the
        # encounter guard requires equality so that exactly one trial binds.
        self.agent.s.set_attr(
            self.episode, "program_request_seq", float(self.seq))
        trial = self.agent.s.add_node("EmbodiedMotorProgramTrial", {})
        outcome = self.agent.s.add_node("EmbodiedMotorProgramOutcome", {
            "receipt_verified": 1.0,
            "request_seq": float(self.seq),
            # `processed` is set so the seed's own learning rule declines
            # this receipt.  It matches the same five-element chain and would
            # otherwise RECOMPUTE `relative_normal_load_error` from an outcome
            # that carries no dynamics, overwriting the residual the bench is
            # controlling.  The condensation rules do not read `processed`.
            "processed": 1.0,
        })
        _edge(self.agent, self.episode,
              "has_embodied_motor_program_trial", trial)
        _edge(self.agent, trial, "enacts_embodied_motor_program", self.program)
        _edge(self.agent, trial,
              "has_embodied_motor_program_outcome", outcome)
        self.agent.inner.run_rules(8)

    def cycle(self) -> dict:
        """One WHOLE engine cycle: autonomous reflexes, then the settle."""
        self.seq += 1
        self.agent.s.set_attr(
            self.episode, "program_request_seq", float(self.seq))
        trial = self.agent.s.add_node("EmbodiedMotorProgramTrial", {})
        outcome = self.agent.s.add_node("EmbodiedMotorProgramOutcome", {
            "receipt_verified": 1.0,
            "request_seq": float(self.seq),
            "processed": 1.0,
        })
        _edge(self.agent, self.episode,
              "has_embodied_motor_program_trial", trial)
        _edge(self.agent, trial, "enacts_embodied_motor_program", self.program)
        _edge(self.agent, trial,
              "has_embodied_motor_program_outcome", outcome)
        return dict(self.agent.inner.run_cycle("default", 8))

    def reflex(self):
        for node in self.agent.inner.neighbours(self.root, "has_reflex"):
            attrs = self.agent.s.node(node)["attrs"]
            if attrs.get("name") == "motor_reflex_buy_time":
                return node
        raise AssertionError("motor_reflex_buy_time is not installed")

    def episode_attrs(self) -> dict:
        return self.agent.s.node(self.episode)["attrs"]

    def shapes(self) -> list[dict]:
        return [
            self.agent.s.node(node)["attrs"]
            for node in self.agent.inner.neighbours(
                self.root, "has_embodied_surprise_shape_library")
        ]

    def only(self) -> dict:
        shapes = self.shapes()
        assert len(shapes) == 1, f"expected one surprise shape, got {shapes}"
        return shapes[0]

    def reflex_epoch(self) -> float:
        return float(
            self.agent.s.node(self.root)["attrs"].get("motor_reflex_epoch", 0.0)
        )


def _bench(*, residual: float = 3.0, condense_after: float = CONDENSE_AFTER):
    try:
        agent = WorldAdapter(seeds=("embodied_motor_program",))
    except RuntimeError as exc:  # pragma: no cover - optional native dep
        pytest.skip(f"native substrate unavailable: {exc}")

    root = agent.agent
    policy = agent.inner.neighbours(
        root, "has_embodied_motor_program_policy")[0]
    agent.s.set_attr(policy, "motor_surprise_shape_quantum", QUANTUM)
    agent.s.set_attr(
        policy, "motor_reflex_condensation_encounters", condense_after)

    episode = agent.s.add_node("EmbodiedMotorProgramEpisode", {})
    _edge(agent, root, "has_embodied_motor_program_episode", episode)

    model = agent.s.add_node("EmbodiedEffectorModel", {
        "actuator_group": 0.0, "ordinal": 4.0,
    })
    _edge(agent, episode, "has_embodied_effector_model", model)

    program = agent.s.add_node("EmbodiedMotorProgram", {
        "relative_normal_load_error": float(residual),
        "member_count": 1.0,
        "internalized_epoch": 7.0,
    })
    _edge(agent, episode, "has_default_embodied_motor_program", program)
    _edge(agent, program, "includes_embodied_effector_model", model)
    return _Bench(agent, root, episode, program, model)


def test_an_unvarying_response_condenses_to_order_zero():
    """The headline: N encounters without variation collapse order 1 to 0."""
    bench = _bench()

    bench.encounter()
    first = bench.only()
    assert first["stable_run"] == pytest.approx(1.0)
    assert first["order"] == pytest.approx(1.0), "one encounter is not a reflex"
    assert bench.reflex_epoch() == pytest.approx(0.0)

    bench.encounter()
    assert bench.only()["stable_run"] == pytest.approx(2.0), (
        "the run must LENGTHEN on an unvarying response -- if this is 1 the "
        "response identity is being compared as a serial name, or a String "
        "attr is being read through P0"
    )
    assert bench.only()["order"] == pytest.approx(1.0), "N not reached yet"

    bench.encounter()
    condensed = bench.only()
    assert condensed["stable_run"] == pytest.approx(3.0)
    assert condensed["order"] == pytest.approx(0.0)
    assert condensed["condensed"] == pytest.approx(1.0)
    assert condensed["status"] == "reflex"
    assert bench.reflex_epoch() == pytest.approx(1.0)


def test_a_condensed_reflex_is_released_when_its_outcome_varies():
    """The collapse stays open.  A trained reflex must be untrainable."""
    bench = _bench()
    for _ in range(3):
        bench.encounter()
    assert bench.only()["order"] == pytest.approx(0.0)

    # Same surprise shape, different response: the program's relation system
    # changes while its residual bucket does not.
    bench.agent.s.set_attr(bench.model, "ordinal", 9.0)
    bench.encounter()

    released = bench.only()
    assert released["order"] == pytest.approx(1.0)
    assert released["condensed"] == pytest.approx(0.0)
    assert released["status"] == "released"
    assert released["stable_run"] == pytest.approx(1.0), (
        "the varying encounter is the first of the NEW run"
    )
    assert bench.reflex_epoch() == pytest.approx(2.0), (
        "the epoch counts releases as well as condensations"
    )


def test_a_released_reflex_can_be_retrained():
    """Release is not retirement -- the same shape condenses again."""
    bench = _bench()
    for _ in range(3):
        bench.encounter()
    bench.agent.s.set_attr(bench.model, "ordinal", 9.0)
    bench.encounter()
    assert bench.only()["status"] == "released"

    for _ in range(2):
        bench.encounter()
    retrained = bench.only()
    assert retrained["order"] == pytest.approx(0.0)
    assert retrained["status"] == "reflex"
    assert bench.reflex_epoch() == pytest.approx(3.0)


def test_the_faculty_is_inert_when_neither_parameter_is_declared():
    """Absence must read as current behaviour, not as a threshold of zero."""
    bench = _bench()
    # Zero is what both parameters read as through `P0` when never declared.
    policy = bench.agent.inner.neighbours(
        bench.root, "has_embodied_motor_program_policy")[0]
    bench.agent.s.set_attr(policy, "motor_surprise_shape_quantum", 0.0)
    bench.agent.s.set_attr(
        policy, "motor_reflex_condensation_encounters", 0.0)

    for _ in range(5):
        bench.encounter()
    assert bench.shapes() == [], "an undeclared faculty must index nothing"
    assert bench.reflex_epoch() == pytest.approx(0.0)


def test_the_ordinal_is_a_log_bucket_not_a_linear_one():
    """Measured: the residual runs 0.21..1_591_707 over one nominal episode.

    Linear quantisation puts those in ~6.4M buckets -- one shape per encounter,
    an index that has learned nothing.  The log puts them in ~15.
    """
    small = _bench(residual=3.0)
    small.encounter()
    huge = _bench(residual=1_591_707.0)
    huge.encounter()

    small_ordinal = small.only()["ordinal"]
    huge_ordinal = huge.only()["ordinal"]
    assert small_ordinal == pytest.approx(math.floor(math.log(4.0) / QUANTUM))
    assert huge_ordinal == pytest.approx(
        math.floor(math.log(1_591_708.0) / QUANTUM))
    assert huge_ordinal - small_ordinal < 20.0, (
        "seven orders of magnitude must collapse into a usable number of "
        "buckets -- this is the whole difference between a shape and a number"
    )


def test_a_different_surprise_shape_gets_its_own_entry():
    """The index is keyed on the residual, so distinct residuals do not share
    a history."""
    bench = _bench(residual=3.0)
    bench.encounter()
    bench.encounter()
    assert len(bench.shapes()) == 1

    bench.agent.s.set_attr(
        bench.program, "relative_normal_load_error", 1_000_000.0)
    bench.encounter()
    shapes = bench.shapes()
    assert len(shapes) == 2, "a new residual bucket is a new surprise shape"
    runs = sorted(shape["stable_run"] for shape in shapes)
    assert runs == [pytest.approx(1.0), pytest.approx(2.0)], (
        "the established shape keeps its run; the new one starts at 1"
    )


# --- firing: order 0 is involuntary, so the ENGINE fires it -----------------


def test_the_buy_time_reflex_is_marked_autonomous():
    """`autonomous` is what moves a reflex off the host dispatch loop.

    Without it the reflex is only reachable through `WorldAdapter.
    fire_reflexes`, which the flight loop never calls -- the reflex shipped
    installed and unreachable.
    """
    bench = _bench()
    assert bench.agent.s.node(bench.reflex())["attrs"].get("autonomous") == 1


def test_the_engine_fires_the_reflex_with_no_host_call():
    """The headline: nothing outside the graph fires it, and nothing outside
    the graph responds.

    `run_cycle` is the whole interface. No `fire_reflexes`, no response
    callable, no adapter remembering to pump anything.
    """
    bench = _bench()
    for _ in range(2):
        report = bench.cycle()
        assert report["reflexes_fired"] == 0, "not condensed yet"

    # The third encounter condenses, which arms the reflex in the settle.
    report = bench.cycle()
    assert report["reflexes_fired"] == 0, (
        "arming happens in the settle; firing is the top of the NEXT cycle"
    )
    assert bench.episode_attrs()["motor_reflex_armed"] == pytest.approx(1.0)

    report = bench.cycle()
    assert report["reflexes_fired"] == 1
    assert bench.agent.s.node(bench.reflex())["attrs"]["fire_count"] == 1


def test_the_response_is_a_rule_that_disarms_and_counts():
    """The response is graph-resident, so it is visible and changeable.

    A Python callable would be invisible to the agent -- an order-0 response it
    could never learn to change.
    """
    bench = _bench()
    for _ in range(4):
        bench.cycle()

    episode = bench.episode_attrs()
    assert episode["motor_reflex_held_seq"] == pytest.approx(4.0)
    assert episode["motor_reflex_armed"] == pytest.approx(0.0), "disarmed"
    assert episode["motor_reflex_handled_count"] == pytest.approx(1.0)
    agent_attrs = bench.agent.s.node(bench.root)["attrs"]
    assert agent_attrs["motor_reflex_enactments"] == pytest.approx(1.0)


def test_an_unarmed_reflex_does_not_fire():
    """Order 0 is involuntary, not unconditional.

    Two encounters never reach N, so nothing condenses, nothing arms, and the
    engine pass finds nothing to fire -- across four whole cycles.
    """
    bench = _bench(condense_after=99.0)
    for _ in range(4):
        assert bench.cycle()["reflexes_fired"] == 0
    assert bench.agent.s.node(bench.reflex())["attrs"]["fire_count"] == 0
    assert "motor_reflex_enactments" not in bench.agent.s.node(bench.root)["attrs"]


def test_the_host_dispatch_path_is_untouched():
    """The split must be TOTAL, or every existing reflex changes behaviour.

    A reflex without `autonomous` still dispatches through the host exactly as
    before, and the engine pass must not touch it -- otherwise its Python
    response would fire twice per cycle, or not at all.
    """
    bench = _bench()
    calls = []
    bench.agent._master["reflex_responses"]["probe_response"] = (
        lambda agent: calls.append(1)
    )
    bench.agent.install_reflex(
        "probe_reflex", {"type": "Lit", "value": True},
        "probe_response", refractory_ticks=0)

    assert bench.agent.fire_reflexes() == ["probe_reflex"]
    assert len(calls) == 1

    report = dict(bench.agent.inner.run_cycle("default", 8))
    assert report["reflexes_fired"] == 0, (
        "the engine pass must skip host-dispatched reflexes"
    )
    assert len(calls) == 1, "and must not invoke their Python response"
