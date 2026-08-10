"""Gates for ALIGNMENT AS A CONVERSION — one travel reading, two axes.

`EFFECTOR_COMPENSATION_PREREG.md` gates 1-6 and 8. The travel table below is
MEASURED, captured from the live standing MJCF humanoid on 2026-08-07 via
`PyBulletHumanoidWorld.actuator_options()`; the tests run against those numbers
so a rule change that breaks on the real body cannot pass here.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from substrate.seed_loader import manifest_for
from substrate.world_adapter import WorldAdapter

ROOT = Path(__file__).resolve().parents[1]

# (group, command direction, declared travel span units, headroom units),
# milliradians, standing pose, one row per non-tonic affordance token.
# Groups 6 and 12 are the knee pair: headroom 0 in one direction and the full
# span in the other. THE LOCKED KNEE AND THE COMPLIANT KNEE ARE THE TWO TOKENS
# OF ONE JOINT — no test below names either.
STANDING_TRAVEL = (
    (0, +1, 1571, 785), (0, -1, 1571, 785),
    (1, +1, 1833, 524), (1, -1, 1833, 1309),
    (2, +1, 1222, 611), (2, -1, 1222, 611),
    (3, +1, 524, 87), (3, -1, 524, 436),
    (4, +1, 1658, 611), (4, -1, 1658, 1047),
    (5, +1, 2269, 349), (5, -1, 2269, 1920),
    (6, +1, 2758, 0), (6, -1, 2758, 2758),
    (7, +1, 1745, 873), (7, -1, 1745, 873),
    (8, +1, 1745, 873), (8, -1, 1745, 873),
    (9, +1, 524, 87), (9, -1, 524, 436),
    (10, +1, 1658, 611), (10, -1, 1658, 1047),
    (11, +1, 2443, 349), (11, -1, 2443, 2094),
    (12, +1, 2758, 0), (12, -1, 2758, 2757),
    (13, +1, 1745, 873), (13, -1, 1745, 873),
    (14, +1, 1745, 873), (14, -1, 1745, 873),
    (15, +1, 2531, 1047), (15, -1, 2531, 1484),
    (16, +1, 2531, 1047), (16, -1, 2531, 1484),
    (17, +1, 2443, 873), (17, -1, 2443, 1571),
    (18, +1, 2531, 1484), (18, -1, 2531, 1047),
    (19, +1, 2531, 1484), (19, -1, 2531, 1047),
    (20, +1, 2443, 873), (20, -1, 2443, 1571),
)

# (group, command direction, load units) — milli-newton-metres, SAME standing
# pose and same moment as the travel table above. The load is the negation of
# the actuator's own applied torque projected onto the token's command
# direction and floored, so at most one token per joint can be non-zero.
#
# RE-CAPTURED after the body began flying by its asset's per-actuator gear
# (effector_limbs v1.3.0). THE LOAD MOVED, and that is the headline: groups 6
# and 12 still stand ON their stop (headroom 0) but now carry ZERO load there —
# the load sits on the FREE-TRAVEL token (6798 and 7355). Under the previous
# uniform force they were loaded INTO the stop (4651 and 2771).
#
# Same posture, opposite reading, decided by how the body is actuated. POSTURE
# DOES NOT SAY BRACED, measured twice on one body.
STANDING_LOAD = (
    (0, +1, 0), (0, -1, 1),
    (1, +1, 0), (1, -1, 5737),
    (2, +1, 99), (2, -1, 0),
    (3, +1, 4112), (3, -1, 0),
    (4, +1, 0), (4, -1, 453),
    (5, +1, 248), (5, -1, 0),
    (6, +1, 0), (6, -1, 6798),
    (7, +1, 11723), (7, -1, 0),
    (8, +1, 134), (8, -1, 0),
    (9, +1, 4402), (9, -1, 0),
    (10, +1, 0), (10, -1, 462),
    (11, +1, 851), (11, -1, 0),
    (12, +1, 0), (12, -1, 7355),
    (13, +1, 12108), (13, -1, 0),
    (14, +1, 0), (14, -1, 77),
    (15, +1, 10204), (15, -1, 0),
    (16, +1, 0), (16, -1, 4183),
    (17, +1, 3), (17, -1, 0),
    (18, +1, 0), (18, -1, 10199),
    (19, +1, 4198), (19, -1, 0),
    (20, +1, 4), (20, -1, 0),
)

# THE PER-ACTUATOR DECLARED AUTHORITY, read from the body ASSET's `<actuator>`
# gear and published through `declared_joint_force_units`. This is the settle's
# currency (effector_limbs v1.3.0) and the scale alignment is a fraction of.
# It replaced `specified_maximum_position_change_per_action`, which is
# `abs(twitch[1])` quantised and therefore 1000 for EVERY actuator — a currency
# carrying no information, which is why the settle could not tell any two
# members of the body apart.
STANDING_GEAR = {
    0: 200, 1: 200, 2: 200, 3: 200, 4: 200, 5: 600, 6: 400,
    7: 100, 8: 100, 9: 200, 10: 200, 11: 600, 12: 400, 13: 100,
    14: 100, 15: 100, 16: 100, 17: 200, 18: 100, 19: 100, 20: 200,
}
DECLARED_CHANGE = 1000


def _adapter(*seeds):
    adapter = WorldAdapter()
    for seed in seeds:
        adapter.inner.load_seed_manifest(manifest_for(seed), adapter.agent)
    return adapter


def _body(adapter):
    body = adapter.s.add_node("EmbodiedRawBody", {
        "grounded": 1, "integer_native": 1, "output_authority": 0})
    return body


def _affordance(adapter, body, **attrs):
    base = {
        "specified_maximum_position_change_per_action": DECLARED_CHANGE,
        "specified_maximum_position_change_per_action_measured": 0,
        "declared_joint_force_units": 100,
        "declared_joint_force_units_measured": 0,
        "available": 1, "grounded": 1, "integer_native": 1,
        "output_authority": 0,
    }
    base.update(attrs)
    node = adapter.s.add_node("EmbodiedOpaqueActuatorAffordance", base)
    adapter.inner.add_edge_unchecked(
        body, "has_opaque_embodied_actuator_affordance", node)
    return node


def _standing_body(adapter, *, with_load=False):
    """The measured standing pose, one affordance per token."""
    body = _body(adapter)
    load_for = {(g, d): load for g, d, load in STANDING_LOAD}
    nodes = {}
    for group, direction, span, headroom in STANDING_TRAVEL:
        extra = {}
        if with_load:
            extra = {
                "command_direction_load_units": load_for[(group, direction)],
                "command_direction_load_units_measured": 0,
                "command_direction_load_units_inferred": 1,
            }
        nodes[(group, direction)] = _affordance(
            adapter, body,
            opaque_group_ordinal=group,
            declared_joint_force_units=STANDING_GEAR[group],
            declared_joint_travel_span_units=span,
            declared_joint_travel_span_units_measured=0,
            command_direction_travel_headroom_units=headroom,
            command_direction_travel_headroom_units_measured=1,
            **extra,
        )
    return body, nodes


def _attrs(adapter, node):
    return adapter.s.node(node)["attrs"]


def test_one_reading_yields_two_anti_correlated_axes():
    """Gate 1. Both derived quantities trace to a single published headroom,
    and they move in OPPOSITE directions across the body's real configuration.

    Checked as a strict ordering rather than a correlation coefficient: for
    every pair of tokens, more compensation must mean no more alignment. A
    fitted correlation would tolerate exceptions; a structural one cannot have
    any.
    """
    adapter = _adapter("effector_compensation")
    _, nodes = _standing_body(adapter)
    adapter.inner.run_rules()

    readings = []
    for (group, direction), node in nodes.items():
        attrs = _attrs(adapter, node)
        readings.append((
            attrs["plastic_compensation_capacity_units"],
            attrs["structural_alignment_authority_units"],
            group, direction,
        ))
    assert len(readings) == len(STANDING_TRAVEL)

    # Anti-correlation, exceptionless. Compare only within a span: alignment is
    # a FRACTION of the declared change, so two tokens on joints of different
    # travel are not comparable by raw headroom.
    by_span: dict[tuple[int, int], list] = {}
    for capacity, alignment, group, direction in readings:
        span = dict(((g, d), s) for g, d, s, _ in STANDING_TRAVEL)[
            (group, direction)]
        # Alignment is a fraction of the token's OWN declared authority, so two
        # tokens on differently-geared joints are not comparable by it either.
        by_span.setdefault((span, STANDING_GEAR[group]), []).append(
            (capacity, alignment))
    compared = 0
    for rows in by_span.values():
        for capacity_a, align_a in rows:
            for capacity_b, align_b in rows:
                if capacity_a < capacity_b:
                    assert align_a >= align_b, (
                        "more capacity must never mean more alignment")
                    compared += 1
    assert compared > 0, "the measured body must contain comparable pairs"


def test_the_body_standing_at_a_stop_reads_fully_braced():
    """Gate 2. Wherever the standing pose puts a joint against its stop, that
    token derives the FULL declared authority and ZERO capacity to give — and
    every token with travel in hand derives strictly less than full.

    Nothing here names a knee, a leg or a stance. The rows are found by their
    published headroom, which is the only thing the rule reads.
    """
    adapter = _adapter("effector_compensation")
    _, nodes = _standing_body(adapter)
    adapter.inner.run_rules()

    at_stop = [key for key, (*_, headroom) in
               ((k, r) for k, r in zip(nodes, STANDING_TRAVEL)) if headroom == 0]
    assert at_stop, "the measured standing pose must contain a joint at a stop"

    for key, node in nodes.items():
        attrs = _attrs(adapter, node)
        alignment = attrs["structural_alignment_authority_units"]
        capacity = attrs["plastic_compensation_capacity_units"]
        gear = STANDING_GEAR[key[0]]
        if key in at_stop:
            assert alignment == gear
            assert capacity == 0
        else:
            assert alignment < gear
            assert capacity > 0


def test_alignment_never_exceeds_the_declared_change_it_is_scaled_by():
    """Gate 5. Unit safety in the `Max`: a braced joint is uncapped BY its own
    declared authority, never raised ABOVE it.

    This is the trap the prereg records — publishing alignment as an ANGLE would
    have made a braced joint read ~1571 against a declared 1000 and win every
    `Max` for the wrong reason.
    """
    adapter = _adapter("effector_compensation")
    _, nodes = _standing_body(adapter)
    adapter.inner.run_rules()
    for (group, _direction), node in nodes.items():
        alignment = _attrs(adapter, node)["structural_alignment_authority_units"]
        assert 0 <= alignment <= STANDING_GEAR[group]


def test_provenance_survives_the_derivation():
    """Gate 4. Alignment is INFERRED (not measured, not declared); capacity is a
    measured travel. A derived value that cannot say which is a gate failure."""
    adapter = _adapter("effector_compensation")
    _, nodes = _standing_body(adapter)
    adapter.inner.run_rules()
    for node in nodes.values():
        attrs = _attrs(adapter, node)
        assert attrs["structural_alignment_authority_units_measured"] == 0
        assert attrs["structural_alignment_authority_units_inferred"] == 1
        assert attrs["plastic_compensation_capacity_units_measured"] == 1


def test_an_option_naming_no_joint_derives_nothing():
    """An absent headroom must stay absent. Read as zero it would mean "at the
    stop" and hand a tonic hold — which commands no displacement at all — the
    full structural authority of a braced limb."""
    adapter = _adapter("effector_compensation")
    body = _body(adapter)
    tonic = _affordance(
        adapter, body, opaque_group_ordinal=-1, tonic_default=1,
        specified_maximum_position_change_per_action=0)
    adapter.inner.run_rules()
    attrs = _attrs(adapter, tonic)
    assert attrs.get("structural_alignment_authority_units") is None
    assert attrs.get("plastic_compensation_capacity_units") is None


def test_inferred_alignment_reaches_the_settle_before_it_fires():
    """Gate 6. MEASURED, not argued from rule-eligibility.

    `elb_settle_effective_authority_over_reaction_paths` fires once per member
    (`Not(declared(effective_authority_units))`), so an alignment declared after
    it fires would silently never be read. This reproduces §1's measured
    no-reaction-path case — carrier released to 50, child declaring 1000 — and
    asserts the braced child is now UNCAPPED by the carrier while the compliant
    child is still capped by it.

    The two children differ in exactly one published number.
    """
    # Dependency order, exactly as `boot_core.boot` resolves it. The manifest
    # assertion below is what makes that order a property of the seed data
    # rather than of this test.
    limbs = manifest_for("effector_limbs")
    assert "effector_compensation" in limbs["depends_on"], (
        "effector_limbs READS structural_alignment_authority_units, so it must "
        "depend on the seed that declares it — otherwise its settle latches "
        "before the alignment exists and silently ignores it")

    adapter = _adapter("effector_compensation", "effector_limbs")
    body = _body(adapter)
    carrier = _affordance(
        adapter, body, opaque_group_ordinal=0,
        # RELEASED, in the settle's currency: the per-actuator declared
        # authority, not the twitch fraction it used to read.
        declared_joint_force_units=50,
        declared_joint_travel_span_units=1000,
        declared_joint_travel_span_units_measured=0,
        command_direction_travel_headroom_units=500,
        command_direction_travel_headroom_units_measured=1,
        command_direction_load_units=100,
        command_direction_load_units_measured=0,
        command_direction_load_units_inferred=1)
    # At its stop AND the load is going into it: the stop is a reaction path.
    braced = _affordance(
        adapter, body, opaque_group_ordinal=1,
        declared_joint_force_units=1000,
        declared_joint_travel_span_units=2758,
        declared_joint_travel_span_units_measured=0,
        command_direction_travel_headroom_units=0,
        command_direction_travel_headroom_units_measured=1,
        command_direction_load_units=4651,
        command_direction_load_units_measured=0,
        command_direction_load_units_inferred=1)
    # Travel in hand, loaded: nothing braced, so the carrier is the only path.
    compliant = _affordance(
        adapter, body, opaque_group_ordinal=2,
        declared_joint_force_units=1000,
        declared_joint_travel_span_units=2758,
        declared_joint_travel_span_units_measured=0,
        command_direction_travel_headroom_units=2758,
        command_direction_travel_headroom_units_measured=1,
        command_direction_load_units=2771,
        command_direction_load_units_measured=0,
        command_direction_load_units_inferred=1)
    # AT ITS STOP AND BEARING NOTHING — the case v1.2.0 exists to separate.
    unloaded = _affordance(
        adapter, body, opaque_group_ordinal=3,
        declared_joint_force_units=1000,
        declared_joint_travel_span_units=2758,
        declared_joint_travel_span_units_measured=0,
        command_direction_travel_headroom_units=0,
        command_direction_travel_headroom_units_measured=1,
        command_direction_load_units=0,
        command_direction_load_units_measured=0,
        command_direction_load_units_inferred=1)
    for child in (braced, compliant, unloaded):
        adapter.inner.add_edge_unchecked(child, "carried_by", carrier)
    adapter.inner.run_rules()

    # The CAPABILITY reading is identical on `braced` and `unloaded` — same
    # posture, same travel. Only the load tells them apart.
    assert _attrs(adapter, braced)["structural_alignment_authority_units"] == 1000
    assert _attrs(adapter, unloaded)["structural_alignment_authority_units"] == 1000
    assert _attrs(adapter, compliant)["structural_alignment_authority_units"] == 0

    authority = {
        name: _attrs(adapter, node)["effective_authority_units"]
        for name, node in (("braced", braced), ("compliant", compliant),
                           ("unloaded", unloaded))
    }
    assert authority["braced"] == 1000, (
        "a child at its stop WITH THE LOAD GOING INTO IT reacts against the "
        "stop, so the released carrier does not cap it")
    assert authority["compliant"] == 50, (
        "with travel in hand the carrier is the only reaction path and its cap "
        "binds — §1's measured no-reaction-path case, unchanged")
    assert authority["unloaded"] == 50, (
        "AT A STOP IS NOT THE SAME AS BRACED: with nothing pushing into it the "
        "stop is not a reaction path, so the carrier cap binds after all")


def test_exactly_one_token_of_a_joint_bears_the_load():
    """The load is projected onto each token's command direction and floored,
    so a joint's two tokens cannot both be bearing it. Measured on the live
    body: 21 of 21 joints have exactly one, and none have two."""
    adapter = _adapter("effector_compensation")
    _, nodes = _standing_body(adapter, with_load=True)
    adapter.inner.run_rules()

    marked: dict[int, int] = {}
    for (group, _direction), node in nodes.items():
        if _attrs(adapter, node).get("bearing_load") == 1:
            marked[group] = marked.get(group, 0) + 1
    assert marked, "the standing body must bear load somewhere"
    assert all(count == 1 for count in marked.values()), (
        "a joint cannot be loaded in both command directions at once")


def test_the_loaded_readings_appear_only_on_the_loaded_token():
    """THE RESIDUAL THIS CLOSES. A joint on its stop publishes BOTH readings —
    braced one way, fully compliant the other — and until the load channel
    existed, choosing between them was the harness's guess.

    The two tokens of one joint must now be distinguished by the graph: only
    the token the load is actually spending gets the loaded readings.
    """
    adapter = _adapter("effector_compensation")
    _, nodes = _standing_body(adapter, with_load=True)
    adapter.inner.run_rules()

    load_for = {(g, d): load for g, d, load in STANDING_LOAD}
    checked = 0
    for key, node in nodes.items():
        attrs = _attrs(adapter, node)
        loaded_capacity = attrs.get("loaded_compensation_capacity_units")
        loaded_alignment = attrs.get(
            "loaded_structural_alignment_authority_units")
        if load_for[key] > 0:
            assert attrs.get("bearing_load") == 1
            # The loaded reading is the unloaded one, restricted — never a
            # different number.
            assert loaded_capacity == attrs[
                "plastic_compensation_capacity_units"]
            assert loaded_alignment == attrs[
                "structural_alignment_authority_units"]
            checked += 1
        else:
            assert attrs.get("bearing_load") is None
            # ABSENT, not zero: this direction is simply not the loaded one,
            # and a zero here would read as "no capacity" — the opposite claim.
            assert loaded_capacity is None
            assert loaded_alignment is None
    assert checked == 21


def test_a_joint_on_its_stop_is_braced_only_where_the_load_goes_into_it():
    """POSTURE DOES NOT SAY BRACED — the same body says so twice.

    The pair standing on their stop are at headroom 0, which is the entire
    postural fact about them. Under the earlier uniform force they were loaded
    INTO that stop and read braced. Flying by the asset's own per-actuator gear,
    THE SAME POSTURE carries zero load on the stop token and all of it on the
    free-travel one.

    So a token at a stop bearing nothing gets NO loaded reading — braced against
    nothing is not a reaction path — while the opposite token of the SAME joint,
    which is bearing the load, gets one with the whole span still in hand. The
    braced-into-the-stop case is exercised explicitly in the settle gate below;
    it is deliberately NOT asserted from the standing pose, because whether the
    standing pose provides it is exactly what turned out not to be fixed.
    """
    adapter = _adapter("effector_compensation")
    _, nodes = _standing_body(adapter, with_load=True)
    adapter.inner.run_rules()

    load_for = {(g, d): load for g, d, load in STANDING_LOAD}
    on_stop = [(g, d) for g, d, _s, headroom in STANDING_TRAVEL
               if headroom == 0]
    assert on_stop, "the standing pose must put something on a stop"

    for group, direction in on_stop:
        stop_token = _attrs(adapter, nodes[(group, direction)])
        other = _attrs(adapter, nodes[(group, -direction)])

        # Postural facts, unchanged and independent of any load.
        assert stop_token["plastic_compensation_capacity_units"] == 0
        assert stop_token["structural_alignment_authority_units"] == (
            STANDING_GEAR[group])

        assert load_for[(group, direction)] == 0, (
            "the stop token bears nothing in this pose")
        assert stop_token.get("bearing_load") is None
        assert stop_token.get("loaded_structural_alignment_authority_units") is None
        assert stop_token.get("loaded_compensation_capacity_units") is None

        # The load is on the other side of the same joint, which has travel.
        assert load_for[(group, -direction)] > 0
        assert other["bearing_load"] == 1
        assert other["loaded_compensation_capacity_units"] > 0
        assert other["loaded_structural_alignment_authority_units"] == 0


def test_load_provenance_says_inferred_not_measured():
    """The datum is the actuator's own applied torque; the load is its
    negation, exact only quasi-statically. A measured torque must not launder
    itself into a measured load."""
    adapter = _adapter("effector_compensation")
    _, nodes = _standing_body(adapter, with_load=True)
    adapter.inner.run_rules()
    for node in nodes.values():
        attrs = _attrs(adapter, node)
        assert attrs["command_direction_load_units_measured"] == 0
        assert attrs["command_direction_load_units_inferred"] == 1


def test_the_mark_reaches_the_loaded_readings_in_one_fixpoint():
    """Ordering, MEASURED — the lesson of the previous rung applied to this
    one. The two reading rules guard on `bearing_load`, which a third rule
    writes, and all three are fire-once. If the mark registered after them the
    readings would silently never appear.
    """
    adapter = _adapter("effector_compensation")
    _, nodes = _standing_body(adapter, with_load=True)
    adapter.inner.run_rules()          # ONE fixpoint, no second pass
    produced = sum(
        1 for node in nodes.values()
        if _attrs(adapter, node).get("loaded_compensation_capacity_units")
        is not None
    )
    assert produced == 21, (
        "the mark must be registered before the rules that guard on it")


def test_no_rule_combines_the_two_axes():
    """Gate 3. Source audit: the two attributes never appear in one term.

    They are anti-correlated readings of one quantity, which is exactly the
    situation in which adding them looks reasonable and is wrong — a limb is not
    "better" for being braced.
    """
    manifest = json.loads(
        (ROOT / "seeds" / "effector_compensation.json").read_text("utf-8"))
    for rule in manifest["rules"]:
        for effect in rule["effects"]:
            blob = json.dumps(effect)
            assert not (
                "structural_alignment_authority_units" in blob
                and "plastic_compensation_capacity_units" in blob
            ), f"{rule['name']} combines the two axes in one effect"
        written = {
            effect[2] for effect in rule["effects"]
            if effect[0] == "set_attr"
        }
        assert not (
            {"structural_alignment_authority_units",
             "plastic_compensation_capacity_units"} <= written
        ), f"{rule['name']} writes both axes, so one could be derived from the other"


@pytest.mark.parametrize("word", (
    "knee", "stance", "landing", "gait", "leg", "foot", "ankle", "step",
))
def test_no_gait_vocabulary_anywhere_in_the_implementation(word):
    """Gate 8. Standing cheaply and absorbing a footfall are the same knob at
    two settings; a phase detector is a design failure, not a feature."""
    for path in (ROOT / "seeds" / "effector_compensation.json",
                 ROOT / "scripts" / "gen_effector_compensation_seed.py"):
        text = path.read_text("utf-8").lower()
        if path.suffix == ".py":
            # The generator's prose EXPLAINS the physical case it must not
            # encode, so only its emitted rule data is audited for vocabulary.
            continue
        assert word not in text, f"{path.name} names {word!r}"
