#!/usr/bin/env python3
"""Generate the integer-native, body-plan-neutral development lifecycle."""
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.gen_humanoid_adaptation_seed import (  # noqa: E402
    A,
    And,
    Argmin,
    Count,
    Eq,
    Exists,
    Filter,
    Gt,
    If,
    L,
    Lt,
    Max,
    Minus,
    Neg,
    Neighbours,
    Not,
    Or,
    Pick,
    PI0,
    Plus,
    SetT,
    StringConcat,
    T,
    ToJsonString,
    V,
)


P0 = PI0


def declared(name, key):
    """Is this attribute PRESENT, as opposed to present-and-zero?

    The engine distinguishes them — a raw `Attr` on a missing key evaluates to
    None and `Eq(Attr, Lit None)` is true only then — but the `P0` idiom used
    throughout this seed coalesces the two. Where an ABSENT value must not be
    allowed to satisfy a guard, test for presence with this first.

    This is not a style point here. `development_evidence_window` was written
    by nothing anywhere in any seed, so two of the three guards in the
    retention gate compared against a coalesced 0 and passed unconditionally,
    while the rule's comment claimed it required "a body-derived receipt
    window". A comment asserting a check the code does not perform is the worst
    form of this bug: it stops anyone looking.
    """
    return Not(Eq(A(name, key), L(None)))


ACTIVE_RESET_REQUESTS = Neighbours(
    "episode", "has_active_embodied_reset_request"
)


def reset_scenarios():
    return Neighbours("episode", "has_embodied_reset_scenario")


# These are capability hypotheses, not an age clock.  Their prerequisite
# relation is deliberately a DAG: support mapping and configuration control
# can develop concurrently, and both enable several later affordances.
CAPABILITIES = (
    {
        "name": "spontaneous_general_movement",
        "goal": "spontaneous_variation",
        "evidence": "spontaneous_configuration_change",
        "ecology": "floor",
        "human_analogue": "spontaneous_general_movements",
        "requires": (),
    },
    {
        "name": "effector_consequence_survey",
        "goal": "effector_discovery",
        "evidence": "effector_coverage",
        "ecology": "floor",
        "human_analogue": "supine_limb_exploration",
        "requires": ("spontaneous_general_movement",),
    },
    {
        "name": "reversible_configuration_control",
        "goal": "configuration_reversal",
        "evidence": "configuration_reversal",
        "ecology": "floor",
        "human_analogue": "repeated_reversible_limb_action",
        "requires": ("effector_consequence_survey",),
    },
    {
        "name": "surface_contact_mapping",
        "goal": "surface_contact_mapping",
        "evidence": "support_topology_change",
        "ecology": "floor",
        "human_analogue": "body_surface_contact_discovery",
        "requires": ("spontaneous_general_movement",),
    },
    {
        "name": "antigravity_segmental_control",
        "goal": "segmental_stabilization",
        "evidence": "stable_partial_motion",
        "ecology": "floor",
        "human_analogue": "head_and_trunk_control",
        "requires": (
            "effector_consequence_survey",
            "surface_contact_mapping",
        ),
    },
    {
        "name": "side_lying_transition",
        "goal": "orientation_change",
        "evidence": "supported_quarter_turn",
        "ecology": "floor",
        "human_analogue": "supine_to_side_lying",
        # Define the acceptable body-relative manifold shape so the generic
        # order-N motor-program machinery can preserve and extend a path
        # across actions.  This is a consequence relation, not a pose or an
        # authored actuator sequence; analysis by synthesis still discovers
        # which opaque effectors realize it on the situated body.
        "desired_body_state_signature": [
            ["support_relation", "preserved"],
            ["orientation_change", "quarter_turn"],
        ],
        "desired_orientation_units": 1,
        "requires": (
            "surface_contact_mapping",
            "antigravity_segmental_control",
        ),
    },
    {
        "name": "supine_prone_rolling",
        "goal": "rolling",
        "evidence": "supported_half_turn",
        "ecology": "floor",
        "human_analogue": "rolling_supine_and_prone",
        # A body-relative consequence question, not a pose or joint script.
        # The repeated relation keys express a transition through several
        # support/energy states; ShapeDecode may retrieve any overlapping
        # observed topology as an analogy while local AbS supplies effectors.
        "desired_body_state_signature": [
            ["support_topology_change", "required"],
            ["orientation_change", "half_turn"],
            ["angular_momentum", "redirected"],
            ["effector_coupling", "compound"],
            ["height_energy_relation", "decreasing"],
            ["height_energy_relation", "increasing"],
        ],
        # A half-turn is two observed body-relative quarter-turn classes.
        "desired_orientation_units": 2,
        "requires": (
            "reversible_configuration_control",
            "side_lying_transition",
        ),
    },
    {
        "name": "prone_forelimb_support",
        "goal": "support_discovery",
        "evidence": "support_gain",
        "ecology": "floor",
        "human_analogue": "prone_forearm_and_hand_support",
        "requires": (
            "surface_contact_mapping",
            "antigravity_segmental_control",
        ),
    },
    {
        "name": "prone_reach_and_pivot",
        "goal": "supported_translation",
        "evidence": "supported_translation",
        "ecology": "floor",
        "human_analogue": "prone_reaching_and_pivoting",
        "requires": (
            "reversible_configuration_control",
            "prone_forelimb_support",
        ),
    },
    {
        "name": "independent_sitting",
        "goal": "bounded_equilibrium",
        "evidence": "bounded_equilibrium",
        "ecology": "floor",
        "human_analogue": "sitting_without_support",
        "clinical_milestone": 1,
        "requires": (
            "antigravity_segmental_control",
            "supine_prone_rolling",
        ),
    },
    {
        "name": "sit_floor_transition",
        "goal": "orientation_change",
        "evidence": "supported_orientation_change",
        "ecology": "floor",
        "human_analogue": "moving_into_and_out_of_sitting",
        "requires": (
            "supine_prone_rolling",
            "independent_sitting",
        ),
    },
    {
        "name": "belly_crawling",
        "goal": "locomotion",
        "evidence": "translated_support_cycle",
        "ecology": "floor",
        "human_analogue": "commando_crawling",
        "requires": (
            "prone_reach_and_pivot",
            "reversible_configuration_control",
        ),
    },
    {
        "name": "quadruped_support",
        "goal": "support_discovery",
        "evidence": "support_gain",
        "ecology": "floor",
        "human_analogue": "hands_and_knees_support",
        "requires": (
            "prone_forelimb_support",
            "independent_sitting",
        ),
    },
    {
        "name": "quadruped_rocking",
        "goal": "configuration_reversal",
        "evidence": "configuration_reversal",
        "ecology": "floor",
        "human_analogue": "hands_and_knees_rocking",
        "requires": (
            "quadruped_support",
            "reversible_configuration_control",
        ),
    },
    {
        "name": "hands_knees_crawling",
        "goal": "locomotion",
        "evidence": "translated_support_cycle",
        "ecology": "floor",
        "human_analogue": "hands_and_knees_crawling",
        "clinical_milestone": 1,
        "optional_route": 1,
        "requires": ("quadruped_rocking", "prone_reach_and_pivot"),
    },
    {
        "name": "kneeling_transition",
        "goal": "height_gain",
        "evidence": "supported_elevation",
        "ecology": "transitional",
        "human_analogue": "kneeling_and_half_kneeling",
        "requires": ("sit_floor_transition", "quadruped_support"),
    },
    {
        "name": "pull_to_stand",
        "goal": "support_reducing_elevation",
        "evidence": "support_reducing_elevation",
        "ecology": "transitional",
        "human_analogue": "standing_with_assistance",
        "clinical_milestone": 1,
        "requires": ("kneeling_transition", "antigravity_segmental_control"),
    },
    {
        "name": "cruising",
        "goal": "locomotion",
        "evidence": "translated_support_cycle",
        "ecology": "supported_upright",
        "human_analogue": "sideways_cruising_with_support",
        "requires": ("pull_to_stand", "surface_contact_mapping"),
    },
    {
        "name": "independent_standing",
        "goal": "reduced_support_equilibrium",
        "evidence": "reduced_support_equilibrium",
        "ecology": "upright",
        "human_analogue": "standing_alone",
        "clinical_milestone": 1,
        "requires": ("pull_to_stand", "antigravity_segmental_control"),
    },
    {
        "name": "controlled_lowering",
        "goal": "configuration_reversal",
        "evidence": "configuration_reversal",
        "ecology": "transitional",
        "human_analogue": "controlled_squat_and_lowering",
        "requires": ("independent_standing", "reversible_configuration_control"),
    },
    {
        "name": "assisted_stepping",
        "goal": "locomotion",
        "evidence": "translated_support_cycle",
        "ecology": "supported_upright",
        "human_analogue": "walking_with_assistance",
        "clinical_milestone": 1,
        "requires": ("cruising", "independent_standing"),
    },
    {
        "name": "independent_walking",
        "goal": "locomotion",
        "evidence": "reduced_support_cycle",
        "ecology": "upright",
        "human_analogue": "walking_alone",
        "clinical_milestone": 1,
        "requires": ("controlled_lowering", "assisted_stepping"),
    },
    {
        "name": "running",
        "goal": "locomotion",
        "evidence": "novel_locomotor_phenotype",
        "ecology": "upright",
        "human_analogue": "running_with_flight_phase",
        "requires": ("independent_walking",),
    },
    {
        "name": "two_foot_jump",
        "goal": "support_reducing_elevation",
        "evidence": "support_reducing_elevation",
        "ecology": "upright",
        "human_analogue": "two_foot_takeoff_and_landing",
        "requires": ("independent_walking", "controlled_lowering"),
    },
    {
        "name": "stairs",
        "goal": "locomotion",
        "evidence": "novel_locomotor_phenotype",
        "ecology": "upright",
        "human_analogue": "stair_ascent_and_descent",
        "requires": ("independent_walking",),
    },
    {
        "name": "single_leg_balance",
        "goal": "reduced_support_equilibrium",
        "evidence": "reduced_support_equilibrium",
        "ecology": "upright",
        "human_analogue": "single_leg_stance",
        "requires": ("independent_walking",),
    },
    {
        "name": "hopping",
        "goal": "locomotion",
        "evidence": "novel_locomotor_phenotype",
        "ecology": "upright",
        "human_analogue": "single_leg_hopping",
        "requires": ("two_foot_jump", "single_leg_balance"),
    },
)


def instances():
    return Neighbours("episode", "has_embodied_developmental_capability")


def templates(instance="instance"):
    return Neighbours(instance, "instantiates_embodied_developmental_capability")


def instance_for_template(template_var):
    return Filter(
        instances(),
        "candidate_instance",
        Exists(
            templates("candidate_instance"),
            "candidate_template",
            Eq(V("candidate_template"), V(template_var)),
        ),
    )


def unresolved_prerequisites(instance="candidate"):
    required_templates = Neighbours(
        instance, "requires_embodied_developmental_capability"
    )
    return Filter(
        required_templates,
        "required_instance",
        Not(Eq(A("required_instance", "status"), L("mastered"))),
    )


def locomotor_profiles():
    return Neighbours("episode", "has_embodied_locomotor_pareto_profile")


def neighbours_of(node, edge_type):
    return {
        "type": "Neighbours",
        "node": node,
        "edge_type": edge_type,
        "any_type": False,
    }


def locomotor_phenotypes():
    return Neighbours("episode", "has_embodied_locomotor_phenotype")


def verified_locomotor_frontier():
    profile = Pick(locomotor_profiles())
    return Filter(
        neighbours_of(profile, "has_pareto_candidate"),
        "locomotor_candidate",
        And(
            Eq(P0("locomotor_candidate", "verified"), L(1)),
            Eq(Count(Neighbours(
                "locomotor_candidate", "is_dominated_by_pareto_candidate"
            )), L(0)),
        ),
    )
def capability_success(instance="instance", receipt="receipt"):
    kind = A(instance, "evidence_kind")
    supported = Or(
        Gt(P0(receipt, "development_post_support_count"), L(0)),
        # Protective support is an observed exafferent force in the actual
        # world, not developmental permission or child motor credit.  During
        # safe learning it legitimately satisfies the support relation; the
        # evidence-fading rule removes it before retention competence can be
        # demonstrated independently.
        Eq(P0(receipt, "caregiver_protective_support_applied"), L(1)),
    )
    trajectory_half_turn_reached = And(
        Not(Eq(
            P0(instance, "trajectory_origin_orientation_class"), L(0)
        )),
        Eq(
            P0(receipt, "development_post_orientation_class"),
            Neg(P0(instance, "trajectory_origin_orientation_class")),
        ),
    )
    return Or(
        And(
            Eq(kind, L("spontaneous_configuration_change")),
            Eq(P0(receipt, "development_configuration_changed"), L(1)),
            Eq(P0(receipt, "development_external_event"), L(0)),
        ),
        And(
            Eq(kind, L("effector_coverage")),
            # Coverage competence is accumulated one newly exercised body
            # affordance at a time. Requiring whole-body completeness here
            # made every partial survey receipt fail, so a body with more
            # effectors than the retry window could never earn progress.
            Or(
                Gt(
                    P0("episode", "development_effector_covered_count"),
                    P0(instance, "effector_coverage_scored_count"),
                ),
                Eq(
                    P0("episode", "development_effector_coverage_complete"),
                    L(1),
                ),
            ),
            Eq(P0(receipt, "development_configuration_changed"), L(1)),
        ),
        And(
            Eq(kind, L("configuration_reversal")),
            Eq(P0(receipt, "development_reversal"), L(1)),
        ),
        And(
            Eq(kind, L("support_topology_change")),
            Eq(P0(receipt, "development_support_topology_changed"), L(1)),
        ),
        And(
            Eq(kind, L("supported_orientation_change")),
            supported,
            Gt(P0(receipt, "development_orientation_units"), L(0)),
        ),
        And(
            Eq(kind, L("supported_quarter_turn")),
            supported,
            Or(
                Eq(
                    P0(receipt, "development_quarter_turn_transition"),
                    L(1),
                ),
                # Orientation is continuous.  A supported transition from a
                # gravity-relative class to its antipode necessarily crosses
                # a perpendicular (side-lying) class even when the temporal
                # receipt aperture samples only the two endpoints.  Preserve
                # that entailed path evidence instead of falsely treating an
                # overshooting half-turn as zero quarter-turn evidence.
                Eq(P0(receipt, "development_half_turn_transition"), L(1)),
                Eq(P0(instance, "trajectory_half_turn_complete"), L(1)),
                # Tracker and learner can match on the same fixpoint pass.
                # Read this receipt against the retained origin directly so
                # the boundary is not lost to a one-pass attribute-update
                # race after the learner advances its receipt sequence.
                trajectory_half_turn_reached,
            ),
        ),
        And(
            Eq(kind, L("supported_half_turn")),
            supported,
            Or(
                Eq(P0(receipt, "development_half_turn_transition"), L(1)),
                Eq(P0(instance, "trajectory_half_turn_complete"), L(1)),
                trajectory_half_turn_reached,
            ),
        ),
        And(
            Eq(kind, L("support_gain")),
            Or(
                Gt(P0(receipt, "development_support_gain"), L(0)),
                Eq(P0(receipt, "development_support_extent_gain"), L(1)),
            ),
        ),
        And(
            Eq(kind, L("stable_partial_motion")),
            supported,
            Eq(P0(receipt, "development_configuration_changed"), L(1)),
            Eq(P0(receipt, "development_motion_nonamplifying"), L(1)),
        ),
        And(
            Eq(kind, L("supported_translation")),
            supported,
            Gt(P0(receipt, "development_translation_units"), L(0)),
        ),
        And(
            Eq(kind, L("supported_elevation")),
            supported,
            Gt(P0(receipt, "development_elevation_units"), L(0)),
        ),
        And(
            Eq(kind, L("bounded_equilibrium")),
            supported,
            Eq(P0(receipt, "development_motion_nonamplifying"), L(1)),
            Eq(P0(receipt, "development_support_topology_changed"), L(0)),
            Eq(P0(receipt, "development_external_event"), L(0)),
        ),
        And(
            Eq(kind, L("translated_support_cycle")),
            Gt(P0(receipt, "development_translation_units"), L(0)),
            Eq(P0(receipt, "development_support_topology_changed"), L(1)),
        ),
        And(
            Eq(kind, L("support_reducing_elevation")),
            supported,
            Gt(P0(receipt, "development_elevation_units"), L(0)),
            Lt(P0(receipt, "development_support_gain"), L(0)),
        ),
        And(
            Eq(kind, L("reduced_support_equilibrium")),
            supported,
            Gt(P0("episode", "development_sparse_support_ceiling"), L(0)),
            Not(Gt(
                P0(receipt, "development_post_support_count"),
                P0("episode", "development_sparse_support_ceiling"),
            )),
            Eq(P0(receipt, "development_motion_nonamplifying"), L(1)),
            Eq(P0(receipt, "development_support_topology_changed"), L(0)),
        ),
        And(
            Eq(kind, L("reduced_support_cycle")),
            Gt(P0("episode", "development_sparse_support_ceiling"), L(0)),
            Not(Gt(
                P0(receipt, "development_post_support_count"),
                P0("episode", "development_sparse_support_ceiling"),
            )),
            Gt(P0(receipt, "development_translation_units"), L(0)),
            Eq(P0(receipt, "development_support_topology_changed"), L(1)),
        ),
        And(
            Eq(kind, L("novel_locomotor_phenotype")),
            Eq(P0(receipt, "development_locomotor_phenotype_novel"), L(1)),
        ),
        And(
            Eq(kind, L("pareto_locomotor_repertoire")),
            Eq(P0(receipt, "development_locomotor_cycle_evidence"), L(1)),
            Gt(Count(verified_locomotor_frontier()), Count(
                Neighbours(
                    instance,
                    "requires_embodied_developmental_capability",
                )
            )),
        ),
    )


def _walk_term(term):
    """Every sub-term in a term tree, in no particular order."""
    if isinstance(term, dict):
        yield term
        for value in term.values():
            yield from _walk_term(value)
    elif isinstance(term, list):
        for item in term:
            yield from _walk_term(item)


def _receipt_attrs_read(branch, receipt):
    """The attributes one criterion branch reads OFF THE RECEIPT.

    Receipt attributes only, deliberately. The receipt is the node being
    ENRICHED asynchronously — minted by one rule, then annotated by others in
    the same fixpoint — so it is the only place where "absent" reliably means
    "not written YET" rather than "not applicable". Episode and instance
    attributes are long-lived state whose absence is a different fact, and
    requiring them present would turn this guard into a boot-order deadlock.
    """
    target = V(receipt)
    keys = []
    for sub in _walk_term(branch):
        if sub.get("type") == "Attr" and sub.get("node") == target:
            if sub.get("key") not in keys:
                keys.append(sub.get("key"))
    return keys


def _readiness(term, receipt):
    """Readiness MIRRORS THE CRITERION'S OWN BOOLEAN STRUCTURE.

    `None` means "needs no receipt measurement", which is not the same as
    "false" and must not be flattened into one — an `Or` with a disjunct that
    reads nothing off the receipt is satisfiable without any measurement at all,
    so demanding the other disjunct's field would make the criterion STRICTER
    than it is. `supported_half_turn` is exactly that case: it succeeds on
    `receipt.development_half_turn_transition` OR on the instance's own
    `trajectory_half_turn_complete`, and a flat conjunction of every field read
    anywhere in the branch would refuse trials the criterion accepts.

      And -> every child that needs something must have it
      Or  -> any child that needs nothing makes the whole thing ready
    """
    if isinstance(term, dict) and term.get("type") in ("And", "Or"):
        children = [_readiness(item, receipt) for item in term["items"]]
        if term["type"] == "Or":
            if any(child is None for child in children):
                return None
            return Or(*children) if len(children) > 1 else children[0]
        needed = [child for child in children if child is not None]
        if not needed:
            return None
        return And(*needed) if len(needed) > 1 else needed[0]
    keys = _receipt_attrs_read(term, receipt)
    if not keys:
        return None
    tests = [declared(receipt, key) for key in keys]
    return And(*tests) if len(tests) > 1 else tests[0]


def capability_measurement_declared(instance="instance", receipt="receipt"):
    """IS THIS RECEIPT READY TO BE JUDGED BY THIS CAPABILITY'S CRITERION?

    THE DEFECT THIS EXISTS TO CLOSE (measured 2026-08-07, growth9): rule
    REGISTRATION ORDER decides which of two rules in one `run_rules` fixpoint
    sees a receipt first, and nothing in a seed's dependency declaration can
    express "run after everything that might still write to my input". On the
    daemon's own `seeds="embodied"` closure the consumers registered 213 rules
    AHEAD of the producer:

        ed_update_learning_plan_step_from_causal_receipt       index 259
        ed_learn_capability_from_causally_closed_receipt       index 260
        els_carry_observed_support_topology_to_causal_receipt  index 473

    So the credit rule read `development_support_topology_changed` while it was
    still ABSENT, `P0` coalesced that absence to 0, a failure was booked, and
    `last_receipt_seq` advanced past the receipt — which makes the credit rule's
    own guard false forever. The carry rule then wrote the true value onto a
    receipt that could never be scored again. `surface_contact_mapping` sat at
    310 attempts / 310 failures / 0 successes with 145 topology changes plainly
    recorded on the receipts it had already consumed.

    AN UNMEASURED TRIAL IS NOT A FAILED TRIAL. Booking one as the other is the
    same flat-zero pathology as pricing an unpriced option at zero: not having a
    measurement must never be scored better OR worse than having it — it must
    not be scored at all. So the consumers now DECLINE the receipt until its
    inputs are present, and pick it up on the next pass once they are. That is
    what makes the result order-independent: a declined receipt is not consumed,
    and `last_receipt_seq` does not advance past it.

    DERIVED, NOT DUPLICATED. The required fields are read out of
    `capability_success()`'s own term tree per evidence-kind branch, so a new
    criterion cannot acquire a field and forget to guard it — the two cannot
    drift apart, because there is only one of them.

    The visible consequence of declining: a capability whose channel is
    genuinely dark now shows `attempt_count == 0` instead of a growing pile of
    fabricated failures, and `ed_note_developmental_receipt_skipped_for_want_of_measurement`
    makes that state loud rather than merely quiet.
    """
    branches = []
    for branch in capability_success(instance, receipt)["items"]:
        # Every branch is And(Eq(kind, Lit(<name>)), ...criterion...). The kind
        # test reads only the instance, so it contributes no readiness of its
        # own and survives as the branch selector.
        kind_test = branch["items"][0]
        ready = _readiness(And(*branch["items"][1:]), receipt)
        branches.append(kind_test if ready is None else And(kind_test, ready))
    return Or(*branches)


def instantiate_capability_rule():
    return {
        "name": "ed_instantiate_capability_in_situated_body",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "Instantiate each ability hypothesis under the currently "
        "sensed body relation system; templates carry no output authority.",
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["agent", "has_embodied_developmental_capability_template", "template"],
        ],
        "where": Eq(Count(instance_for_template("template")), L(0)),
        "effects": [
            ["add_node", "instance", "EmbodiedSituatedDevelopmentalCapability", {
                "name": T(A("template", "name")),
                "ordinal": T(P0("template", "ordinal")),
                "goal": T(A("template", "goal")),
                "evidence_kind": T(A("template", "evidence_kind")),
                "developmental_ecology": T(A("template", "developmental_ecology")),
                "human_analogue": T(A("template", "human_analogue")),
                "desired_body_state_signature": T(A(
                    "template", "desired_body_state_signature"
                )),
                "desired_orientation_units": T(P0(
                    "template", "desired_orientation_units"
                )),
                "clinical_milestone": T(P0("template", "clinical_milestone")),
                "optional_route": T(P0("template", "optional_route")),
                "status": "available",
                "attempt_count": 0,
                "success_count": 0,
                "failure_count": 0,
                "effector_coverage_scored_count": 0,
                "retention_count": 0,
                "last_receipt_seq": 0,
                "activation_receipt_seq": 0,
                "retention_start_seq": 0,
                "q": 0,
                "asym_count": T(P0("episode", "development_evidence_window")),
                "novelty": 0,
                "warm_start_overlap": 0,
                "warm_start_requires_verification": 0,
                "last_reinstantiation_failure_count": 0,
                "output_authority": 0,
                "integer_native": 1,
                "trajectory_origin_orientation_class": 0,
                "trajectory_latest_orientation_class": 0,
                "trajectory_half_turn_complete": 0,
            }],
            ["add_edge", "episode", "has_embodied_developmental_capability", "instance"],
            ["add_edge", "instance", "instantiates_embodied_developmental_capability", "template"],
        ],
    }


def bind_prerequisite_rule():
    return {
        "name": "ed_bind_situated_capability_prerequisite",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_embodied_developmental_capability", "instance"],
            ["instance", "instantiates_embodied_developmental_capability", "template"],
            ["template", "requires_embodied_developmental_capability_template", "required_template"],
            ["episode", "has_embodied_developmental_capability", "required_instance"],
            ["required_instance", "instantiates_embodied_developmental_capability", "required_template"],
        ],
        "where": Not(Exists(
            Neighbours("instance", "requires_embodied_developmental_capability"),
            "bound_requirement",
            Eq(V("bound_requirement"), V("required_instance")),
        )),
        "effects": [[
            "add_edge", "instance",
            "requires_embodied_developmental_capability", "required_instance",
        ]],
    }


def detect_reversal_rule():
    return {
        "name": "ed_detect_situated_configuration_reversal",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "A reversal is an observed return through the same coarse "
        "proprioceptive regions, not exact pose equality, an assumed opposite "
        "actuator, or a canonical configuration.",
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_embodied_development_receipt", "previous"],
            ["episode", "has_embodied_development_receipt", "current"],
        ],
        "where": And(
            Eq(
                P0("current", "development_receipt_seq"),
                Plus(P0("previous", "development_receipt_seq"), L(1)),
            ),
            Eq(A("previous", "development_pre_configuration_region"),
               A("current", "development_post_configuration_region")),
            Eq(A("previous", "development_post_configuration_region"),
               A("current", "development_pre_configuration_region")),
            Eq(P0("current", "development_reversal"), L(0)),
        ),
        "effects": [["set_attr", "current", "development_reversal", 1]],
    }


def track_floor_orientation_trajectory_rule():
    """Retain an interleaved, situated roll trajectory in the graph.

    A roll commonly spans several actions.  The simulator reports only the
    mechanically observed gravity-relative orientation class on each receipt;
    the cognitive graph owns the temporal relation and decides when the body
    has reached the class opposite the one from which this attempt began.
    """
    origin = If(
        Eq(P0("instance", "trajectory_origin_orientation_class"), L(0)),
        P0("receipt", "development_pre_orientation_class"),
        P0("instance", "trajectory_origin_orientation_class"),
    )
    return {
        "name": "ed_track_situated_floor_orientation_trajectory",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_active_embodied_developmental_capability", "instance"],
            ["episode", "has_embodied_development_receipt", "receipt"],
        ],
        "where": And(
            Eq(A("instance", "developmental_ecology"), L("floor")),
            Eq(P0("receipt", "development_receipt_closed"), L(1)),
            Gt(P0("receipt", "development_receipt_seq"),
               P0("instance", "last_receipt_seq")),
        ),
        "effects": [
            ["set_attr", "instance", "trajectory_origin_orientation_class", T(origin)],
            ["set_attr", "instance", "trajectory_latest_orientation_class", T(
                P0("receipt", "development_post_orientation_class")
            )],
            ["set_attr", "instance", "trajectory_half_turn_complete", T(If(
                Eq(
                    P0("receipt", "development_post_orientation_class"),
                    Neg(origin),
                ),
                L(1),
                P0("instance", "trajectory_half_turn_complete"),
            ))],
        ],
    }


def archive_consumed_receipt_rule():
    """Keep the causal working set bounded without deleting evidence nodes.

    Learned contexts, capability statistics, phenotype aggregates, and the
    multi-action orientation trajectory already hold everything cognition has
    extracted.  The transition remains reachable from its humanoid trial for
    audit, while only the latest receipt stays on the hot developmental edge
    so the next action can still detect a reversible two-receipt loop.
    """
    return {
        "name": "ed_archive_consumed_receipt_from_active_working_set",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_embodied_development_receipt", "receipt"],
        ],
        "where": Lt(
            P0("receipt", "development_receipt_seq"),
            P0("episode", "latest_development_receipt_seq"),
        ),
        "effects": [[
            "del_edge", "episode", "has_embodied_development_receipt", "receipt",
        ]],
    }


LOCOMOTOR_PARETO_DIMENSIONS = (
    ("directed_progress", "maximize"),
    ("path_length", "minimize"),
    ("lateral_excursion", "minimize"),
    ("energy", "minimize"),
    ("peak_load", "minimize"),
    ("directed_consistency", "maximize"),
)


def directed_consistency(receipt="receipt"):
    """One integer vote when motion agrees with the situated heading.

    Balance during locomotion is relative to the intended trajectory, not a
    preference for a quiet or canonical upright pose.  The interface already
    quantizes displacement projected onto the episode's current heading as
    ``development_directed_units``.  Cognition therefore needs only its sign:
    recurrent positive projections are evidence of a dynamically maintained
    locomotor basin; zero or contrary motion is not.
    """
    return If(
        Gt(P0(receipt, "development_directed_units"), L(0)),
        L(1),
        L(0),
    )


def instantiate_locomotor_pareto_profile_rule():
    effects = [[
        "add_node", "profile", "ParetoProfile", {
            "name": "situated_locomotor_repertoire",
            "dimension_count": len(LOCOMOTOR_PARETO_DIMENSIONS),
            "scalarized": 0,
            "integer_native": 1,
            "output_authority": 0,
        },
    ], [
        "add_edge", "episode", "has_embodied_locomotor_pareto_profile",
        "profile",
    ]]
    for ordinal, (name, direction) in enumerate(
        LOCOMOTOR_PARETO_DIMENSIONS
    ):
        variable = f"dimension_{ordinal}"
        effects.extend((
            ["add_node", variable, "ParetoDimension", {
                "name": name,
                "ordinal": ordinal,
                "direction": direction,
                "integer_native": 1,
            }],
            ["add_edge", "profile", "has_pareto_dimension", variable],
        ))
    return {
        "name": "ed_instantiate_situated_locomotor_pareto_profile",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [[
            "agent", "has_embodied_development_episode", "episode",
        ]],
        "where": Eq(Count(locomotor_profiles()), L(0)),
        "effects": effects,
    }


def suspend_detached_locomotor_pareto_profile_rule():
    """Retain old locomotor evidence without recomputing its frozen frontier."""
    return {
        "name": "ed_suspend_detached_locomotor_pareto_profile",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["episode", "grounded_in_embodied_simulator_connection", "connection"],
            ["episode", "has_embodied_locomotor_pareto_profile", "profile"],
        ],
        "where": And(
            Eq(A("connection", "current_attachment"), L(0)),
            Not(Eq(A("profile", "pareto_suspended"), L(1))),
        ),
        "effects": [["set_attr", "profile", "pareto_suspended", 1]],
    }


def mint_locomotor_phenotype_rule():
    known = Filter(
        locomotor_phenotypes(),
        "known_phenotype",
        Eq(
            A("known_phenotype", "key"),
            A("receipt", "development_locomotor_phenotype_key"),
        ),
    )
    return {
        "name": "ed_mint_novel_locomotor_phenotype_from_receipt",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_embodied_development_receipt", "receipt"],
        ],
        "where": And(
            Eq(P0("episode", "development_learning_active"), L(1)),
            Eq(P0("receipt", "development_receipt_closed"), L(1)),
            Eq(P0("receipt", "development_locomotor_cycle_evidence"), L(1)),
            Eq(
                P0("receipt", "development_receipt_seq"),
                P0("episode", "latest_development_receipt_seq"),
            ),
            Eq(Count(known), L(0)),
        ),
        "effects": [
            ["add_node", "phenotype", "EmbodiedLocomotorPhenotype", {
                "signature": T(A(
                    "receipt", "development_locomotor_phenotype_signature"
                )),
                "key": T(A(
                    "receipt", "development_locomotor_phenotype_key"
                )),
                "status": "hypothesis",
                "occurrence_count": 1,
                "sum_directed_units": T(P0(
                    "receipt", "development_directed_units"
                )),
                "sum_translation_units": T(P0(
                    "receipt", "development_translation_units"
                )),
                "sum_lateral_units": T(P0(
                    "receipt", "development_lateral_units"
                )),
                "sum_energy_units": T(P0(
                    "receipt", "development_energy_units"
                )),
                "sum_peak_load_units": T(P0(
                    "receipt", "development_peak_load_units"
                )),
                "sum_directed_consistency": T(directed_consistency()),
                "last_receipt_seq": T(P0(
                    "receipt", "development_receipt_seq"
                )),
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "episode", "has_embodied_locomotor_phenotype", "phenotype"],
            ["set_attr", "receipt", "development_locomotor_phenotype_novel", 1],
        ],
    }


def update_locomotor_phenotype_rule():
    fields = (
        ("sum_directed_units", "development_directed_units"),
        ("sum_translation_units", "development_translation_units"),
        ("sum_lateral_units", "development_lateral_units"),
        ("sum_energy_units", "development_energy_units"),
        ("sum_peak_load_units", "development_peak_load_units"),
    )
    return {
        "name": "ed_accumulate_recurrent_locomotor_phenotype",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_embodied_locomotor_phenotype", "phenotype"],
            ["episode", "has_embodied_development_receipt", "receipt"],
        ],
        "where": And(
            Eq(P0("receipt", "development_receipt_closed"), L(1)),
            Eq(P0("receipt", "development_locomotor_cycle_evidence"), L(1)),
            Eq(
                P0("receipt", "development_receipt_seq"),
                P0("episode", "latest_development_receipt_seq"),
            ),
            Eq(A("phenotype", "key"), A(
                "receipt", "development_locomotor_phenotype_key"
            )),
            Gt(P0("receipt", "development_receipt_seq"),
               P0("phenotype", "last_receipt_seq")),
        ),
        "effects": [
            ["set_attr", "phenotype", "occurrence_count", T(Plus(
                P0("phenotype", "occurrence_count"), L(1)
            ))],
            *[
                ["set_attr", "phenotype", target, T(Plus(
                    P0("phenotype", target), P0("receipt", source)
                ))]
                for target, source in fields
            ],
            ["set_attr", "phenotype", "sum_directed_consistency", T(Plus(
                P0("phenotype", "sum_directed_consistency"),
                directed_consistency(),
            ))],
            ["set_attr", "phenotype", "last_receipt_seq", T(P0(
                "receipt", "development_receipt_seq"
            ))],
        ],
    }


def verify_locomotor_basin_rule():
    values = (
        ("sum_directed_units", False),
        ("sum_translation_units", True),
        ("sum_lateral_units", True),
        ("sum_energy_units", True),
        ("sum_peak_load_units", True),
        ("sum_directed_consistency", False),
    )
    effects = [
        ["add_node", "candidate", "ParetoCandidate", {
            "identity": T(StringConcat(
                L("locomotor_basin:"),
                A("phenotype", "key"),
            )),
            "signature": T(A("phenotype", "signature")),
            "verified": 1,
            "dominated": 0,
            "archived": 0,
            "integer_native": 1,
            "output_authority": 0,
        }],
        ["add_edge", "profile", "has_pareto_candidate", "candidate"],
        ["add_edge", "phenotype", "publishes_locomotor_pareto_candidate", "candidate"],
        ["set_attr", "phenotype", "status", "verified_basin"],
        ["set_attr", "profile", "candidate_count", T(Plus(
            P0("profile", "candidate_count"), L(1)
        ))],
        ["add_node", "pareto_task_set", "SystemTwoTaskSet", {
            "area": "cognitive_pareto",
            "enabled": 1,
            "provenance_kind": "locomotor_pareto_relational_evaluation",
        }],
        ["add_node", "pareto_escalation", "SystemTwoEscalation", {
            "status": "requested",
            "reason": "evaluate_locomotor_tradeoff_basis",
            "epoch": T(Plus(P0("profile", "candidate_count"), L(1))),
        }],
        ["add_edge", "pareto_escalation", "about_context", "profile"],
        ["add_edge", "pareto_escalation", "recruits_task_set", "pareto_task_set"],
    ]
    for ordinal, (field, minimize) in enumerate(values):
        variable = f"value_{ordinal}"
        raw = P0("phenotype", field)
        effects.extend((
            ["add_node", variable, "ParetoValue", {
                "dimension_ordinal": ordinal,
                "raw_value": T(raw),
                "signed_value": T(Neg(raw) if minimize else raw),
                "verified": 1,
                "integer_native": 1,
            }],
            ["add_edge", "candidate", "has_pareto_value", variable],
        ))
    return {
        "name": "ed_verify_recurrent_locomotor_basin_on_pareto_basis",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_embodied_locomotor_pareto_profile", "profile"],
            ["episode", "has_embodied_locomotor_phenotype", "phenotype"],
        ],
        "where": And(
            Eq(A("phenotype", "status"), L("hypothesis")),
            Not(Lt(
                P0("phenotype", "occurrence_count"),
                P0("episode", "development_evidence_window"),
            )),
            Eq(Count(Neighbours(
                "phenotype", "publishes_locomotor_pareto_candidate"
            )), L(0)),
        ),
        "effects": effects,
    }


def eligible_instances():
    return Filter(
        instances(),
        "candidate",
        And(
            Or(
                Eq(A("candidate", "status"), L("available")),
                Eq(A("candidate", "status"), L("warm_available")),
                Eq(A("candidate", "status"), L("retention_due")),
            ),
            Eq(Count(unresolved_prerequisites()), L(0)),
        ),
    )


def learning_plans():
    return Neighbours("episode", "has_self_directed_learning_plan")


def learning_plan_steps(plan="plan"):
    return Neighbours(plan, "has_learning_plan_step")


def active_learning_profiles(plan="plan"):
    return Neighbours(plan, "has_active_learning_decision_profile")


def learning_step_for_instance(instance="instance", plan="plan"):
    return Filter(
        learning_plan_steps(plan),
        "candidate_step",
        Exists(
            Neighbours("candidate_step", "plans_learning_capability"),
            "planned_instance",
            Eq(V("planned_instance"), V(instance)),
        ),
    )


def goal_for_learning_step(step="step"):
    return Neighbours(step, "pursues_goal")


def consequence_goal_for_cell(cell="cell"):
    return Neighbours(cell, "has_consequence_goal")


def unresolved_dependents(instance="instance"):
    return Filter(
        instances(),
        "dependent_instance",
        And(
            Not(Eq(A("dependent_instance", "status"), L("mastered"))),
            Exists(
                Neighbours(
                    "dependent_instance",
                    "requires_embodied_developmental_capability",
                ),
                "required_instance",
                Eq(V("required_instance"), V(instance)),
            ),
        ),
    )


def eligible_learning_steps(plan="plan"):
    return Filter(
        learning_plan_steps(plan),
        "eligible_step",
        Exists(
            Neighbours("eligible_step", "plans_learning_capability"),
            "eligible_instance",
            And(
                Or(
                    Eq(A("eligible_instance", "status"), L("available")),
                    Eq(A("eligible_instance", "status"), L("warm_available")),
                    Eq(A("eligible_instance", "status"), L("retention_due")),
                ),
                Eq(Count(unresolved_prerequisites("eligible_instance")), L(0)),
            ),
        ),
    )


def candidates_for_learning_step(profile="profile", step="step"):
    return Filter(
        Neighbours(profile, "has_pareto_candidate"),
        "existing_candidate",
        Exists(
            Neighbours(
                "existing_candidate", "proposes_learning_plan_step"
            ),
            "existing_step",
            Eq(V("existing_step"), V(step)),
        ),
    )


def active_learning_frontier(profile="profile"):
    return Filter(
        Neighbours(profile, "has_pareto_candidate"),
        "frontier_candidate",
        Eq(Count(Neighbours(
            "frontier_candidate", "is_dominated_by_pareto_candidate"
        )), L(0)),
    )


def instantiate_self_directed_learning_plan_rule():
    return {
        "name": "ed_instantiate_self_directed_learning_plan",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "The learner owns a persistent plan over capability "
        "hypotheses. Its decisions, budgets, revisions, and outcomes remain "
        "graph state; the developmental DAG supplies constraints, not an "
        "externally authored schedule.",
        "match": [[
            "agent", "has_embodied_development_episode", "episode",
        ]],
        "where": Eq(Count(learning_plans()), L(0)),
        "effects": [
            ["add_node", "plan", "LearningPlan", {
                "kind": "self_directed_embodied_development",
                "status": "active",
                "decision_count": 0,
                "replan_count": 0,
                "completed_step_count": 0,
                "deferred_step_count": 0,
                "budget_revision_count": 0,
                "active_decision_epoch": 0,
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "episode", "has_self_directed_learning_plan", "plan"],
        ],
    }


def instantiate_learning_plan_step_rule():
    budget = Plus(
        Max(L(1), P0("episode", "development_evidence_window")),
        Count(unresolved_prerequisites("instance")),
    )
    return {
        "name": "ed_plan_every_situated_capability_hypothesis",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "Every situated capability becomes a revisable plan "
        "step. Its initial evidence budget is derived from the body's "
        "evidence window plus its relational prerequisite depth.",
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["episode", "has_embodied_developmental_capability", "instance"],
        ],
        "where": Eq(Count(learning_step_for_instance()), L(0)),
        "effects": [
            ["add_node", "step", "LearningPlanStep", {
                "name": T(A("instance", "name")),
                "goal": T(A("instance", "goal")),
                "ordinal": T(P0("instance", "ordinal")),
                "status": T(If(
                    Eq(Count(unresolved_prerequisites("instance")), L(0)),
                    L("ready"),
                    L("blocked"),
                )),
                "evidence_budget_units": T(budget),
                "evidence_spent_units": T(P0("instance", "attempt_count")),
                "context_evidence_units": T(Count(Neighbours(
                    "instance", "has_embodied_developmental_context"
                ))),
                "successful_evidence_units": T(P0(
                    "instance", "success_count"
                )),
                "failed_evidence_units": T(P0(
                    "instance", "failure_count"
                )),
                "last_receipt_seq": T(P0("instance", "last_receipt_seq")),
                "selection_count": 0,
                "revision_count": 0,
                "last_revision_receipt_seq": 0,
                "last_budget_review_receipt_seq": 0,
                "budget_success_baseline": T(P0(
                    "instance", "success_count"
                )),
                "budget_failure_baseline": T(P0(
                    "instance", "failure_count"
                )),
                "deferred_generation": 0,
                "last_selected_decision_epoch": 0,
                "optional_route": T(P0("instance", "optional_route")),
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "plan", "has_learning_plan_step", "step"],
            ["add_edge", "step", "plans_learning_capability", "instance"],
        ],
    }


def instantiate_generic_goal_for_learning_step_rule():
    return {
        "name": "ed_wire_each_learning_step_to_generic_goal_cognition",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "The developmental plan does not invent a second goal "
        "ontology. Each step pursues the existing generic Goal node used by "
        "the rest of cognition.",
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "instance"],
        ],
        "where": Eq(Count(goal_for_learning_step()), L(0)),
        "effects": [
            ["add_node", "goal", "Goal", {
                "kind": T(A("instance", "goal")),
                "name": T(A("instance", "name")),
                "status": "active",
                "progress_units": T(P0("instance", "success_count")),
                "resolved_units": T(If(
                    Eq(A("instance", "status"), L("mastered")), L(1), L(0)
                )),
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "agent", "has_goal", "goal"],
            ["add_edge", "plan", "has_goal", "goal"],
            ["add_edge", "step", "pursues_goal", "goal"],
            ["add_edge", "goal", "grounds_learning_capability", "instance"],
        ],
    }


def bind_generic_goal_dependency_rule():
    return {
        "name": "ed_express_learning_dependencies_as_order_n_subgoals",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["step", "requires_learning_plan_step", "required_step"],
            ["step", "pursues_goal", "goal"],
            ["required_step", "pursues_goal", "required_goal"],
        ],
        "where": Not(Exists(
            Neighbours("goal", "has_subgoal"), "known_goal",
            Eq(V("known_goal"), V("required_goal")),
        )),
        "effects": [["add_edge", "goal", "has_subgoal", "required_goal"]],
    }


def update_generic_goal_from_learning_evidence_rule():
    return {
        "name": "ed_publish_verified_learning_progress_to_generic_goal",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["step", "plans_learning_capability", "instance"],
            ["step", "pursues_goal", "goal"],
        ],
        "where": Or(
            Not(Eq(P0("goal", "progress_units"),
                   P0("instance", "success_count"))),
            And(
                Eq(A("instance", "status"), L("mastered")),
                Eq(P0("goal", "resolved_units"), L(0)),
            ),
        ),
        "effects": [
            ["set_attr", "goal", "progress_units", T(P0(
                "instance", "success_count"
            ))],
            ["set_attr", "goal", "resolved_units", T(If(
                Eq(A("instance", "status"), L("mastered")), L(1), L(0)
            ))],
            ["set_attr", "goal", "status", T(If(
                Eq(A("instance", "status"), L("mastered")),
                L("resolved"), L("active")
            ))],
        ],
    }


def instantiate_effector_consequence_subgoal_rule():
    return {
        "name": "ed_decompose_effector_discovery_into_observed_channel_goals",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "Each discovered body channel is a genuine Goal child. "
        "This exposes incremental causal learning to generic order-N "
        "supervision without rewarding repeated motion.",
        "match": [
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "instance"],
            ["step", "pursues_goal", "goal"],
            ["episode", "has_somatomotor_wave_field", "field"],
            ["field", "has_somatomotor_wave_cell", "cell"],
            ["cell", "represents_embodied_effector", "effector"],
        ],
        "where": And(
            Eq(A("instance", "goal"), L("effector_discovery")),
            Eq(Count(consequence_goal_for_cell()), L(0)),
        ),
        "effects": [
            ["add_node", "subgoal", "Goal", {
                "kind": "effector_consequence",
                "name": T(StringConcat(
                    L("effector_consequence:"),
                    ToJsonString(P0("effector", "channel_ordinal")),
                )),
                "status": "active",
                "progress_units": 0,
                "resolved_units": 0,
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "goal", "has_subgoal", "subgoal"],
            ["add_edge", "cell", "has_consequence_goal", "subgoal"],
            ["add_edge", "subgoal", "grounds_embodied_effector", "effector"],
        ],
    }


def resolve_effector_consequence_subgoal_rule():
    return {
        "name": "ed_resolve_effector_goal_on_first_verified_consequence",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [["cell", "has_consequence_goal", "goal"]],
        "where": And(
            Gt(P0("cell", "verified_consequence_count"), L(0)),
            Eq(P0("goal", "resolved_units"), L(0)),
        ),
        "effects": [
            ["set_attr", "goal", "progress_units", 1],
            ["set_attr", "goal", "resolved_units", 1],
            ["set_attr", "goal", "status", "resolved"],
        ],
    }


def bind_learning_plan_step_dependency_rule():
    known = Neighbours("step", "requires_learning_plan_step")
    return {
        "name": "ed_bind_learning_plan_step_dependencies",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "instance"],
            ["instance", "requires_embodied_developmental_capability", "required_instance"],
            ["plan", "has_learning_plan_step", "required_step"],
            ["required_step", "plans_learning_capability", "required_instance"],
        ],
        "where": Not(Exists(
            known,
            "known_requirement",
            Eq(V("known_requirement"), V("required_step")),
        )),
        "effects": [[
            "add_edge", "step", "requires_learning_plan_step", "required_step"
        ]],
    }


def refresh_learning_plan_step_readiness_rule():
    return {
        "name": "ed_refresh_learning_plan_step_from_dependency_state",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "instance"],
        ],
        "where": And(
            Eq(A("step", "status"), L("blocked")),
            Eq(Count(unresolved_prerequisites("instance")), L(0)),
            Not(Eq(A("instance", "status"), L("mastered"))),
        ),
        "effects": [["set_attr", "step", "status", "ready"]],
    }


LEARNING_PLAN_DIMENSIONS = (
    ("information_gap", "maximize"),
    ("prerequisite_unlocks", "maximize"),
    ("retention_urgency", "maximize"),
    ("transfer_overlap", "maximize"),
    ("experiment_cost", "minimize"),
)


def open_learning_decision_profile_rule():
    effects = [
        ["add_node", "profile", "ParetoProfile", {
            "kind": "self_directed_learning_decision",
            "status": "collecting_candidates",
            "decision_epoch": T(Plus(
                P0("plan", "decision_count"), L(1)
            )),
            "dimension_count": len(LEARNING_PLAN_DIMENSIONS),
            "scalarized": 0,
            "integer_native": 1,
            "output_authority": 0,
        }],
        ["add_edge", "plan", "has_learning_decision_profile", "profile"],
        ["add_edge", "plan", "has_active_learning_decision_profile", "profile"],
        ["set_attr", "plan", "active_decision_epoch", T(Plus(
            P0("plan", "decision_count"), L(1)
        ))],
    ]
    for ordinal, (name, direction) in enumerate(LEARNING_PLAN_DIMENSIONS):
        variable = f"learning_dimension_{ordinal}"
        effects.extend((
            ["add_node", variable, "ParetoDimension", {
                "name": name,
                "ordinal": ordinal,
                "direction": direction,
                "direction_sign": 1 if direction == "maximize" else -1,
                "integer_native": 1,
            }],
            ["add_edge", "profile", "has_pareto_dimension", variable],
        ))
    return {
        "name": "ed_open_self_directed_learning_decision",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_self_directed_learning_plan", "plan"],
        ],
        "where": And(
            Eq(P0("episode", "development_learning_active"), L(1)),
            Eq(A("plan", "status"), L("active")),
            Eq(Count(Neighbours(
                "episode", "has_active_embodied_developmental_capability"
            )), L(0)),
            Eq(Count(active_learning_profiles()), L(0)),
            Gt(Count(eligible_learning_steps()), L(0)),
        ),
        "effects": effects,
    }


def mint_learning_decision_candidate_rule():
    information_gap = Max(
        L(0),
        Minus(
            P0("step", "evidence_budget_units"),
            P0("instance", "attempt_count"),
        ),
    )
    unlocks = Count(unresolved_dependents("instance"))
    retention = If(
        Eq(A("instance", "status"), L("retention_due")), L(1), L(0)
    )
    transfer = P0("instance", "warm_start_overlap")
    stalled = Not(Lt(
        Minus(
            P0("instance", "failure_count"),
            P0("instance", "last_reinstantiation_failure_count"),
        ),
        Max(L(1), P0("episode", "development_evidence_window")),
    ))
    experiment_cost = Plus(
        P0("instance", "failure_count"),
        If(stalled, P0("episode", "embodiment_reset_cost_units"), L(0)),
    )
    raw = (information_gap, unlocks, retention, transfer, experiment_cost)
    signed = (
        information_gap, unlocks, retention, transfer, Neg(experiment_cost)
    )
    effects = [
        ["add_node", "candidate", "ParetoCandidate", {
            "kind": "learning_plan_step_decision",
            "decision_epoch": T(P0("profile", "decision_epoch")),
            "capability_ordinal": T(P0("instance", "ordinal")),
            "information_gap": T(information_gap),
            "prerequisite_unlocks": T(unlocks),
            "retention_urgency": T(retention),
            "transfer_overlap": T(transfer),
            "experiment_cost": T(experiment_cost),
            "verified": 1,
            "dominated": 0,
            "integer_native": 1,
            "output_authority": 0,
        }],
        ["add_edge", "profile", "has_pareto_candidate", "candidate"],
        ["add_edge", "candidate", "proposes_learning_plan_step", "step"],
    ]
    for ordinal, (raw_value, signed_value) in enumerate(zip(raw, signed)):
        variable = f"learning_value_{ordinal}"
        effects.extend((
            ["add_node", variable, "ParetoValue", {
                "dimension_ordinal": ordinal,
                "raw_value": T(raw_value),
                "signed_value": T(signed_value),
                "verified": 1,
                "integer_native": 1,
            }],
            ["add_edge", "candidate", "has_pareto_value", variable],
        ))
    return {
        "name": "ed_publish_learning_step_as_pareto_candidate",
        "area": "cognitive_pareto",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_active_learning_decision_profile", "profile"],
            ["plan", "has_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "instance"],
        ],
        "where": And(
            Or(
                Eq(A("instance", "status"), L("available")),
                Eq(A("instance", "status"), L("warm_available")),
                Eq(A("instance", "status"), L("retention_due")),
            ),
            Eq(Count(unresolved_prerequisites("instance")), L(0)),
            Eq(Count(candidates_for_learning_step()), L(0)),
        ),
        "effects": effects,
    }


def dominate_learning_decision_candidate_rule():
    non_worse = And(
        Not(Lt(P0("alternative", "information_gap"),
               P0("candidate", "information_gap"))),
        Not(Lt(P0("alternative", "prerequisite_unlocks"),
               P0("candidate", "prerequisite_unlocks"))),
        Not(Lt(P0("alternative", "retention_urgency"),
               P0("candidate", "retention_urgency"))),
        Not(Lt(P0("alternative", "transfer_overlap"),
               P0("candidate", "transfer_overlap"))),
        Not(Gt(P0("alternative", "experiment_cost"),
               P0("candidate", "experiment_cost"))),
    )
    strictly_better = Or(
        Gt(P0("alternative", "information_gap"),
           P0("candidate", "information_gap")),
        Gt(P0("alternative", "prerequisite_unlocks"),
           P0("candidate", "prerequisite_unlocks")),
        Gt(P0("alternative", "retention_urgency"),
           P0("candidate", "retention_urgency")),
        Gt(P0("alternative", "transfer_overlap"),
           P0("candidate", "transfer_overlap")),
        Lt(P0("alternative", "experiment_cost"),
           P0("candidate", "experiment_cost")),
    )
    return {
        "name": "ed_recognize_learning_plan_pareto_dominance",
        "area": "cognitive_pareto",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["plan", "has_active_learning_decision_profile", "profile"],
            ["profile", "has_pareto_candidate", "candidate"],
            ["profile", "has_pareto_candidate", "alternative"],
        ],
        "where": And(
            Not(Eq(V("candidate"), V("alternative"))),
            non_worse,
            strictly_better,
            Eq(Count(Filter(
                Neighbours(
                    "candidate", "is_dominated_by_pareto_candidate"
                ),
                "known_dominator",
                Eq(V("known_dominator"), V("alternative")),
            )), L(0)),
        ),
        "effects": [
            ["add_edge", "alternative", "dominates_pareto_candidate", "candidate"],
            ["add_edge", "candidate", "is_dominated_by_pareto_candidate", "alternative"],
            ["set_attr", "candidate", "dominated", 1],
        ],
    }


def select_learning_plan_step_rule():
    frontier = active_learning_frontier()
    selected = Argmin(
        frontier,
        "frontier_candidate",
        P0("frontier_candidate", "capability_ordinal"),
        V("profile"),
    )
    return {
        "name": "ed_learning_plan_selects_pareto_frontier_experiment",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "The plan selects only after every ready step has a "
        "complete, non-scalar Pareto point. Ordinal resolves genuinely "
        "incomparable frontier ties; it is not an objective weighting.",
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_active_learning_decision_profile", "profile"],
            ["profile", "has_pareto_candidate", "candidate"],
            ["candidate", "proposes_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "instance"],
        ],
        "where": And(
            Eq(
                Count(Neighbours("profile", "has_pareto_candidate")),
                Count(eligible_learning_steps()),
            ),
            Gt(Count(frontier), L(0)),
            Eq(V("candidate"), selected),
            Eq(Count(Neighbours(
                "plan", "has_selected_learning_plan_step"
            )), L(0)),
        ),
        "effects": [
            ["add_edge", "episode", "has_active_embodied_developmental_capability", "instance"],
            ["add_edge", "plan", "has_selected_learning_plan_step", "step"],
            ["add_edge", "plan", "has_selected_learning_decision", "candidate"],
            ["del_edge", "plan", "has_active_learning_decision_profile", "profile"],
            ["set_attr", "profile", "status", "selected"],
            ["set_attr", "candidate", "selected", 1],
            ["set_attr", "step", "status", "active"],
            ["set_attr", "step", "selection_count", T(Plus(
                P0("step", "selection_count"), L(1)
            ))],
            ["set_attr", "step", "last_selected_decision_epoch", T(
                P0("profile", "decision_epoch")
            )],
            ["set_attr", "plan", "decision_count", T(Plus(
                P0("plan", "decision_count"), L(1)
            ))],
            ["set_attr", "plan", "replan_count", T(Plus(
                P0("plan", "replan_count"),
                If(Gt(P0("profile", "decision_epoch"), L(1)), L(1), L(0)),
            ))],
            ["set_attr", "instance", "status", T(If(
                Eq(A("instance", "status"), L("retention_due")),
                L("retention_due"),
                L("active"),
            ))],
            ["set_attr", "episode", "active_embodied_developmental_goal", T(A("instance", "goal"))],
            ["set_attr", "episode", "active_embodied_developmental_capability", T(A("instance", "name"))],
            ["set_attr", "instance", "activation_receipt_seq", T(
                P0("episode", "latest_development_receipt_seq")
            )],
        ],
    }


def update_learning_plan_step_from_receipt_rule():
    return {
        "name": "ed_update_learning_plan_step_from_causal_receipt",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_selected_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "instance"],
            ["episode", "has_embodied_development_receipt", "receipt"],
        ],
        "where": And(
            Eq(P0("receipt", "development_receipt_closed"), L(1)),
            Gt(P0("receipt", "development_receipt_seq"),
               P0("step", "last_receipt_seq")),
            # The step is the second reader of the SAME criterion on the SAME
            # receipt, so it must decline on the same condition — otherwise the
            # plan's evidence tally and the instance's counters disagree about
            # which trials were judged.
            capability_measurement_declared(),
        ),
        "effects": [
            ["set_attr", "step", "last_receipt_seq", T(P0(
                "receipt", "development_receipt_seq"
            ))],
            ["set_attr", "step", "evidence_spent_units", T(Plus(
                P0("instance", "attempt_count"), L(1)
            ))],
            ["set_attr", "step", "context_evidence_units", T(Count(Neighbours(
                "instance", "has_embodied_developmental_context"
            )))],
            ["set_attr", "step", "successful_evidence_units", T(Plus(
                P0("instance", "success_count"),
                If(capability_success(), L(1), L(0)),
            ))],
            ["set_attr", "step", "failed_evidence_units", T(Plus(
                P0("instance", "failure_count"),
                If(capability_success(), L(0), L(1)),
            ))],
        ],
    }


def archive_learning_decision_candidate_rule():
    return {
        "name": "ed_archive_completed_learning_decision_candidate",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "Completed Pareto alternatives remain auditable graph "
        "history but leave the generic hot comparison edge, preventing past "
        "planning epochs from consuming present cognition budget.",
        "match": [
            ["plan", "has_learning_decision_profile", "profile"],
            ["profile", "has_pareto_candidate", "candidate"],
        ],
        "where": And(
            Eq(A("profile", "status"), L("selected")),
            Eq(P0("candidate", "archived"), L(0)),
        ),
        "effects": [
            ["del_edge", "profile", "has_pareto_candidate", "candidate"],
            ["add_edge", "profile", "archived_learning_decision_candidate", "candidate"],
            ["set_attr", "candidate", "archived", 1],
        ],
    }


def release_dominated_process_at_checkin_rule():
    return {
        "name": "ed_release_dominated_process_for_checkin_replanning",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "The general cognitive supervisor has withdrawn "
        "continuation authority. Release this embodied experiment so the "
        "ordinary Pareto planner, not the host, can select another basin.",
        "match": [
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_selected_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "instance"],
            ["episode", "has_active_embodied_developmental_capability", "instance"],
            ["episode", "has_cognitive_process", "process"],
            ["process", "supervises_learning_plan_step", "step"],
        ],
        "where": And(
            Eq(A("process", "status"), L("replan_required")),
            Eq(P0("process", "continuation_authority"), L(0)),
            Eq(P0("process", "replan_release_complete"), L(0)),
        ),
        "effects": [
            ["del_edge", "episode", "has_active_embodied_developmental_capability", "instance"],
            ["del_edge", "plan", "has_selected_learning_plan_step", "step"],
            ["set_attr", "step", "status", "meta_suspended"],
            ["set_attr", "instance", "status", "meta_suspended"],
            ["set_attr", "process", "replan_release_complete", 1],
            ["set_attr", "plan", "replan_count", T(Plus(
                P0("plan", "replan_count"), L(1)
            ))],
        ],
    }


def reopen_process_released_capability_rule():
    """A SUSPENSION MUST NOT OUTLIVE ITS PREMISE.

    THE LATCH (measured 2026-08-07, growth8 and growth9): ordinal 1
    `effector_consequence_survey` sat at `meta_suspended` for entire runs with no
    path out. `ed_release_dominated_process_for_checkin_replanning` suspends when
    the cognitive supervisor withdraws continuation authority, but it writes no
    `reassess_after_learning_capability` edge — and the ONLY reopen rule in the
    tree, `ml_reopen_suspended_step_after_revision_condition_changes`, MATCHES on
    that edge. So an instance suspended by the embodied path was unreachable by
    the only rule that could revive it. Not a slow recovery: no recovery.

    The premise of that suspension is exactly

        process.status == "replan_required" AND process.continuation_authority == 0

    so the release is its exact negation, on the same discipline as
    `cp_retract_stale_relational_dominance`: a derived state is retracted when the
    thing it was derived from is gone. The supervisor withdrew authority; when the
    supervisor's own state no longer says that, the capability returns to
    `available` and the ordinary Pareto planner may select it again — the planner
    decides whether to, not this rule.

    Deliberately NOT keyed on the dominating alternative mastering, nor on this
    capability's own evidence changing. Both are downstream facts that may never
    occur, and neither is what actually put the instance in this state.

    Matched via `has_learning_plan_step` rather than
    `has_selected_learning_plan_step`, because the suspender DELETES the selected
    edge — keying on it would make this rule unmatchable for exactly the
    instances it exists to release.
    """
    return {
        "name": "ed_reopen_process_released_capability_when_authority_returns",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "The supervisor's withdrawal of continuation authority is "
        "what suspended this capability; when that withdrawal is over the "
        "suspension has no premise left and the capability returns to the "
        "frontier. Whether to select it again is the planner's decision.",
        "match": [
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "instance"],
            ["episode", "has_cognitive_process", "process"],
            ["process", "supervises_learning_plan_step", "step"],
        ],
        "where": And(
            Eq(A("instance", "status"), L("meta_suspended")),
            Eq(A("step", "status"), L("meta_suspended")),
            # The exact negation of the suspending premise.
            Not(And(
                Eq(A("process", "status"), L("replan_required")),
                Eq(P0("process", "continuation_authority"), L(0)),
            )),
        ),
        "effects": [
            ["set_attr", "instance", "status", "available"],
            ["set_attr", "step", "status", "ready"],
            ["set_attr", "instance", "released_from_meta_suspension", 1],
        ],
    }


def publish_structural_surprise_to_cognitive_process_rule():
    """Expose a prediction error, not ordinary experimental failure."""
    return {
        "name": "ed_publish_structural_envelope_departure_to_process_supervisor",
        "area": "cognitive_supervision",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A failed experiment is evidence, not automatically "
        "surprise. Only body destruction or the structural-limit faculty's "
        "explicit interrupt leaves the held expected envelope.",
        "match": [
            ["runtime", "projects_embodied_development", "episode"],
            ["episode", "has_cognitive_process", "process"],
            ["episode", "has_embodied_development_receipt", "receipt"],
        ],
        "where": And(
            Eq(P0("receipt", "development_receipt_closed"), L(1)),
            Eq(P0("receipt", "development_receipt_seq"),
               P0("episode", "latest_development_receipt_seq")),
            Eq(P0("receipt", "cognitive_surprise_published"), L(0)),
            Or(
                Eq(P0("receipt", "embodiment_destroyed"), L(1)),
                Gt(P0("runtime", "structural_interrupt_required"), L(0)),
            ),
        ),
        "effects": [
            ["add_node", "signal", "CognitiveProcessSignal", {
                "kind": T(If(
                    Eq(P0("receipt", "embodiment_destroyed"), L(1)),
                    L("embodiment_integrity"),
                    L("structural_body_envelope"),
                )),
                "observed_units": 1,
                "expected_lower_units": 0,
                "expected_upper_units": 0,
                "receipt_epoch": T(P0(
                    "receipt", "development_receipt_seq"
                )),
                "supervision_processed": 0,
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "process", "observes_process_signal", "signal"],
            ["add_edge", "signal", "grounded_in_causal_receipt", "receipt"],
            ["set_attr", "receipt", "cognitive_surprise_published", 1],
        ],
    }


def release_learning_plan_step_rule():
    active_instances = Neighbours(
        "episode", "has_active_embodied_developmental_capability"
    )
    return {
        "name": "ed_release_learning_plan_step_after_experiment",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_selected_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "instance"],
        ],
        "where": Not(Exists(
            active_instances,
            "active_instance",
            Eq(V("active_instance"), V("instance")),
        )),
        "effects": [
            ["del_edge", "plan", "has_selected_learning_plan_step", "step"],
            ["set_attr", "step", "status", T(If(
                Eq(A("instance", "status"), L("mastered")),
                L("completed"),
                If(
                    Eq(A("instance", "status"), L("plan_deferred")),
                    L("deferred"),
                    If(
                        Eq(Count(unresolved_prerequisites("instance")), L(0)),
                        L("ready"),
                        L("blocked"),
                    ),
                ),
            ))],
        ],
    }


def revise_learning_plan_budget_after_reset_rule():
    return {
        "name": "ed_revise_learning_plan_budget_after_scenario_change",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A graph-authored body/scenario replacement is a plan "
        "revision. It opens one more body-derived evidence window without "
        "erasing the evidence already spent.",
        "match": [
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_selected_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "instance"],
            ["episode", "has_active_embodied_reset_request", "request"],
        ],
        "where": And(
            Gt(
                P0("request", "cause_receipt_seq"),
                P0("step", "last_revision_receipt_seq"),
            ),
            Eq(Count(Filter(
                Neighbours("request", "revises_learning_plan_step"),
                "revised_step",
                Eq(V("revised_step"), V("step")),
            )), L(0)),
        ),
        "effects": [
            ["set_attr", "step", "evidence_budget_units", T(Plus(
                P0("step", "evidence_budget_units"),
                Max(L(1), P0("episode", "development_evidence_window")),
            ))],
            ["set_attr", "step", "revision_count", T(Plus(
                P0("step", "revision_count"), L(1)
            ))],
            ["set_attr", "step", "last_revision_receipt_seq", T(P0(
                "request", "cause_receipt_seq"
            ))],
            ["set_attr", "step", "budget_success_baseline", T(P0(
                "instance", "success_count"
            ))],
            ["set_attr", "step", "budget_failure_baseline", T(P0(
                "instance", "failure_count"
            ))],
            ["set_attr", "plan", "budget_revision_count", T(Plus(
                P0("plan", "budget_revision_count"), L(1)
            ))],
            ["add_edge", "request", "revises_learning_plan_step", "step"],
        ],
    }


def extend_learning_plan_budget_on_progress_rule():
    return {
        "name": "ed_extend_learning_budget_only_from_observed_progress",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Budget exhaustion is a planning event. A step earns "
        "another body-derived evidence window only when the exhausted window "
        "contained new successful evidence; this is an explicit revision, "
        "not an unbounded retry loop.",
        "match": [
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_selected_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "instance"],
        ],
        "where": And(
            Not(Lt(
                P0("step", "evidence_spent_units"),
                P0("step", "evidence_budget_units"),
            )),
            Gt(
                P0("instance", "success_count"),
                P0("step", "budget_success_baseline"),
            ),
            Gt(
                P0("step", "last_receipt_seq"),
                P0("step", "last_budget_review_receipt_seq"),
            ),
            Not(Eq(A("instance", "status"), L("mastered"))),
        ),
        "effects": [
            ["add_node", "revision", "LearningPlanRevision", {
                "kind": "evidence_budget_extension",
                "reason": "observed_learning_progress",
                "receipt_seq": T(P0("step", "last_receipt_seq")),
                "previous_budget_units": T(P0(
                    "step", "evidence_budget_units"
                )),
                "additional_budget_units": T(Max(
                    L(1), P0("episode", "development_evidence_window")
                )),
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "plan", "has_learning_plan_revision", "revision"],
            ["add_edge", "revision", "revises_learning_plan_step", "step"],
            ["set_attr", "step", "evidence_budget_units", T(Plus(
                P0("step", "evidence_budget_units"),
                Max(L(1), P0("episode", "development_evidence_window")),
            ))],
            ["set_attr", "step", "revision_count", T(Plus(
                P0("step", "revision_count"), L(1)
            ))],
            ["set_attr", "step", "last_budget_review_receipt_seq", T(P0(
                "step", "last_receipt_seq"
            ))],
            ["set_attr", "step", "budget_success_baseline", T(P0(
                "instance", "success_count"
            ))],
            ["set_attr", "step", "budget_failure_baseline", T(P0(
                "instance", "failure_count"
            ))],
            ["set_attr", "plan", "budget_revision_count", T(Plus(
                P0("plan", "budget_revision_count"), L(1)
            ))],
        ],
    }


def defer_exhausted_learning_step_without_reset_rule():
    return {
        "name": "ed_defer_exhausted_learning_step_without_progress_or_reset",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "When no new success was observed and the environment "
        "cannot instantiate another experiment, the plan records an honest "
        "deferment instead of silently retrying forever.",
        "match": [
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_selected_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "instance"],
        ],
        "where": And(
            Eq(P0("episode", "embodiment_reset_available"), L(0)),
            Not(Lt(
                P0("step", "evidence_spent_units"),
                P0("step", "evidence_budget_units"),
            )),
            Eq(
                P0("instance", "success_count"),
                P0("step", "budget_success_baseline"),
            ),
            Not(Eq(A("instance", "status"), L("mastered"))),
        ),
        "effects": [
            ["set_attr", "step", "status", "deferred"],
            ["set_attr", "step", "deferred_generation", T(P0(
                "episode", "embodiment_generation"
            ))],
            ["set_attr", "instance", "status", "plan_deferred"],
            ["del_edge", "episode", "has_active_embodied_developmental_capability", "instance"],
            ["set_attr", "plan", "deferred_step_count", T(Plus(
                P0("plan", "deferred_step_count"), L(1)
            ))],
        ],
    }


def reopen_deferred_learning_step_in_new_embodiment_rule():
    return {
        "name": "ed_reopen_deferred_learning_step_in_new_embodiment",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "instance"],
        ],
        "where": And(
            Eq(A("step", "status"), L("deferred")),
            Gt(P0("episode", "embodiment_generation"),
               P0("step", "deferred_generation")),
        ),
        "effects": [
            ["set_attr", "step", "status", T(If(
                Eq(Count(unresolved_prerequisites("instance")), L(0)),
                L("ready"), L("blocked")
            ))],
            ["set_attr", "instance", "status", "available"],
            ["set_attr", "plan", "deferred_step_count", T(Max(
                L(0), Minus(P0("plan", "deferred_step_count"), L(1))
            ))],
        ],
    }


def complete_learning_plan_step_rule():
    return {
        "name": "ed_complete_learning_plan_step_after_retained_mastery",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "instance"],
        ],
        "where": And(
            Eq(A("instance", "status"), L("mastered")),
            Not(Eq(A("step", "status"), L("completed"))),
        ),
        "effects": [
            ["set_attr", "step", "status", "completed"],
            ["set_attr", "plan", "completed_step_count", T(Plus(
                P0("plan", "completed_step_count"), L(1)
            ))],
        ],
    }


def complete_self_directed_learning_plan_rule():
    required_incomplete = Filter(
        learning_plan_steps(),
        "incomplete_step",
        And(
            Eq(P0("incomplete_step", "optional_route"), L(0)),
            Not(Eq(A("incomplete_step", "status"), L("completed"))),
        ),
    )
    return {
        "name": "ed_complete_learning_plan_when_required_frontier_is_mastered",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["episode", "has_self_directed_learning_plan", "plan"],
        ],
        "where": And(
            Eq(A("plan", "status"), L("active")),
            Gt(Count(learning_plan_steps()), L(0)),
            Eq(Count(required_incomplete), L(0)),
        ),
        "effects": [["set_attr", "plan", "status", "completed"]],
    }


def mint_context_rule():
    known = Neighbours("instance", "has_embodied_developmental_context")
    return {
        "name": "ed_mint_novel_successful_capability_context",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_active_embodied_developmental_capability", "instance"],
            ["episode", "has_embodied_development_receipt", "receipt"],
        ],
        "where": And(
            Eq(P0("episode", "development_learning_active"), L(1)),
            Eq(P0("receipt", "development_receipt_closed"), L(1)),
            Gt(P0("receipt", "development_receipt_seq"),
               P0("instance", "last_receipt_seq")),
            Gt(P0("receipt", "development_receipt_seq"),
               P0("instance", "activation_receipt_seq")),
            capability_success(),
            Eq(Count(Filter(
                known,
                "known_context",
                Eq(A("known_context", "signature"),
                   A("receipt", "development_context_signature")),
            )), L(0)),
        ),
        "effects": [
            ["add_node", "context", "EmbodiedDevelopmentalContext", {
                "signature": T(A("receipt", "development_context_signature")),
                "first_receipt_seq": T(P0("receipt", "development_receipt_seq")),
                "integer_native": 1,
            }],
            ["add_edge", "instance", "has_embodied_developmental_context", "context"],
        ],
    }


def learn_receipt_rule():
    success = If(capability_success(), L(1), L(0))
    failure = Minus(L(1), success)
    attempts = Plus(P0("instance", "attempt_count"), L(1))
    failures = Plus(P0("instance", "failure_count"), failure)
    window = Max(L(1), P0("episode", "development_evidence_window"))
    return {
        "name": "ed_learn_capability_from_causally_closed_receipt",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_active_embodied_developmental_capability", "instance"],
            ["episode", "has_embodied_development_receipt", "receipt"],
        ],
        "where": And(
            Eq(P0("episode", "development_learning_active"), L(1)),
            Eq(P0("receipt", "development_receipt_closed"), L(1)),
            Gt(P0("receipt", "development_receipt_seq"),
               P0("instance", "last_receipt_seq")),
            Gt(P0("receipt", "development_receipt_seq"),
               P0("instance", "activation_receipt_seq")),
            # CLOSED IS NOT THE SAME AS MEASURED. A receipt is minted closed and
            # then enriched by other rules in the same fixpoint; consuming it
            # before its inputs land books an unmeasured trial as a failed one
            # and, because the seq guard advances, forecloses ever correcting
            # that. Decline instead — the receipt is picked up on the pass after
            # its measurement arrives, whatever order the rules registered in.
            capability_measurement_declared(),
        ),
        "effects": [
            ["set_attr", "instance", "attempt_count", T(attempts)],
            ["set_attr", "instance", "success_count", T(Plus(
                P0("instance", "success_count"), success,
            ))],
            ["set_attr", "instance", "failure_count", T(failures)],
            ["set_attr", "instance", "q", T(failures)],
            ["set_attr", "instance", "asym_count", T(Max(
                L(0), Minus(window, attempts),
            ))],
            ["set_attr", "instance", "novelty", T(success)],
            ["set_attr", "instance", "effector_coverage_scored_count", T(
                If(
                    Eq(
                        A("instance", "evidence_kind"),
                        L("effector_coverage"),
                    ),
                    P0("episode", "development_effector_covered_count"),
                    P0("instance", "effector_coverage_scored_count"),
                )
            )],
            ["set_attr", "instance", "last_receipt_seq", T(
                P0("receipt", "development_receipt_seq")
            )],
            ["set_attr", "episode", "development_sparse_support_ceiling", T(
                If(
                    And(
                        Eq(
                            A("instance", "evidence_kind"),
                            L("support_reducing_elevation"),
                        ),
                        capability_success(),
                    ),
                    If(
                        Or(
                            Eq(P0("episode", "development_sparse_support_ceiling"), L(0)),
                            Lt(
                                P0("receipt", "development_post_support_count"),
                                P0("episode", "development_sparse_support_ceiling"),
                            ),
                        ),
                        P0("receipt", "development_post_support_count"),
                        P0("episode", "development_sparse_support_ceiling"),
                    ),
                    P0("episode", "development_sparse_support_ceiling"),
                )
            )],
        ],
    }


def skipped_for_want_of_measurement_rule():
    """DECLINING MUST BE LOUD. A capability that never attempts is not obviously
    different from one that has not started, and the whole point of this repair
    is that a dark channel stops disguising itself as failure — it must not
    instead disguise itself as silence.

    Fires only on a receipt whose chance has demonstrably passed: a NEWER receipt
    already exists (`latest_development_receipt_seq` is ahead of it) and this one
    was still never credited (its seq is still ahead of `last_receipt_seq`). A
    receipt merely waiting for its measurement to land later in the same fixpoint
    is not superseded yet, so the ordinary case never trips this.
    """
    return {
        "name": "ed_note_developmental_receipt_skipped_for_want_of_measurement",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "An unmeasured trial is not a failed trial. It is counted "
        "here, separately, so a channel that is written by nothing is visible "
        "as such instead of accumulating fabricated failures.",
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_active_embodied_developmental_capability", "instance"],
            ["episode", "has_embodied_development_receipt", "receipt"],
        ],
        "where": And(
            Eq(P0("episode", "development_learning_active"), L(1)),
            Eq(P0("receipt", "development_receipt_closed"), L(1)),
            Gt(P0("receipt", "development_receipt_seq"),
               P0("instance", "last_receipt_seq")),
            Gt(P0("receipt", "development_receipt_seq"),
               P0("instance", "activation_receipt_seq")),
            Gt(P0("receipt", "development_receipt_seq"),
               P0("instance", "last_unmeasured_receipt_seq")),
            # Superseded: a later receipt exists, so this one is not merely
            # waiting for an enrichment still to come in this fixpoint.
            Gt(P0("episode", "latest_development_receipt_seq"),
               P0("receipt", "development_receipt_seq")),
            Not(capability_measurement_declared()),
        ),
        "effects": [
            ["set_attr", "instance", "last_unmeasured_receipt_seq", T(
                P0("receipt", "development_receipt_seq")
            )],
            ["set_attr", "instance", "unmeasured_receipt_count", T(Plus(
                P0("instance", "unmeasured_receipt_count"), L(1)
            ))],
            ["set_attr", "instance", "measurement_blocked_on", T(
                A("instance", "evidence_kind")
            )],
        ],
    }


def retain_causally_closed_experience_rule():
    return {
        "name": "ed_retain_every_causally_closed_developmental_experience",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Closure proves that the command and consequence belong "
        "to one receipt. It does not imply success, safety, or replay "
        "authority; adverse tails remain first-class learned evidence.",
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_embodied_development_receipt", "receipt"],
        ],
        "where": And(
            Eq(P0("receipt", "development_receipt_closed"), L(1)),
            Eq(P0("receipt", "development_experience_retained"), L(0)),
        ),
        "effects": [
            ["set_attr", "receipt", "development_experience_retained", 1],
            ["set_attr", "episode", "retained_developmental_experience_count", T(
                Plus(
                    P0("episode", "retained_developmental_experience_count"),
                    L(1),
                )
            )],
            ["set_attr", "episode", "caregiver_buffered_experience_count", T(
                Plus(
                    P0("episode", "caregiver_buffered_experience_count"),
                    P0("receipt", "development_recoverability_units"),
                )
            )],
            ["set_attr", "episode", "unbuffered_experience_count", T(Plus(
                P0("episode", "unbuffered_experience_count"),
                P0("receipt", "development_unbuffered_exposure_units"),
            ))],
        ],
    }


def mark_terminal_embodiment_rule():
    """Close the current body episode without discarding its last evidence."""
    return {
        "name": "ed_mark_destroyed_embodiment_terminal_after_retention",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Destruction terminates the current embodiment, not the "
        "learner. The causal receipt must already be durable before this "
        "state transition can occur.",
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_embodied_development_receipt", "receipt"],
        ],
        "where": And(
            Eq(P0("receipt", "development_receipt_closed"), L(1)),
            Eq(P0("receipt", "development_experience_retained"), L(1)),
            Eq(P0("receipt", "embodiment_destroyed"), L(1)),
            Eq(P0("receipt", "embodiment_terminal_recorded"), L(0)),
        ),
        "effects": [
            ["set_attr", "receipt", "embodiment_terminal_recorded", 1],
            ["set_attr", "episode", "embodiment_terminal", 1],
            ["set_attr", "episode", "terminal_receipt_seq", T(P0(
                "receipt", "development_receipt_seq"
            ))],
        ],
    }


def request_embodiment_reinstantiation_rule():
    """Let the graph request a replacement body after terminal evidence."""
    return {
        "name": "ed_request_reinstantiation_from_retained_terminal_receipt",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "The graph owns the decision to iterate. The environment "
        "adapter only enacts this explicit request. Replacement cost remains "
        "observable evidence rather than becoming a categorical prohibition.",
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_embodied_development_receipt", "receipt"],
        ],
        "where": And(
            Eq(P0("episode", "embodiment_terminal"), L(1)),
            Eq(P0("episode", "embodiment_reset_available"), L(1)),
            Eq(P0("episode", "embodied_reset_requested"), L(0)),
            Eq(Count(ACTIVE_RESET_REQUESTS), L(0)),
            Eq(P0("receipt", "development_experience_retained"), L(1)),
            Eq(P0("receipt", "embodiment_destroyed"), L(1)),
            Eq(
                P0("receipt", "development_receipt_seq"),
                P0("episode", "terminal_receipt_seq"),
            ),
        ),
        "effects": [
            ["add_node", "request", "EmbodiedResetRequest", {
                "status": "requested",
                "cause": "embodiment_destroyed",
                "cause_receipt_seq": T(P0(
                    "receipt", "development_receipt_seq"
                )),
                "departing_generation": T(P0(
                    "episode", "embodiment_generation"
                )),
                "replacement_cost_units": T(P0(
                    "episode", "embodiment_reset_cost_units"
                )),
                "retained_experience_count": T(P0(
                    "episode", "retained_developmental_experience_count"
                )),
                "memory_preservation_required": 1,
                "reinstantiation_spec_ready": 0,
                "integer_native": 1,
                "output_authority": 1,
            }],
            ["add_edge", "episode", "has_embodied_reset_request", "request"],
            ["add_edge", "episode", "has_active_embodied_reset_request", "request"],
            ["add_edge", "request", "caused_by_embodied_receipt", "receipt"],
            ["set_attr", "receipt", "embodied_reset_requested", 1],
            ["set_attr", "episode", "embodied_reset_requested", 1],
            ["set_attr", "episode", "reset_requested", 1],
        ],
    }


def request_new_situated_experiment_rule():
    """End an unproductive experiment and choose another initial condition."""
    return {
        "name": "ed_request_new_situated_experiment_after_failure_window",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A reset is also an epistemic action. After a complete "
        "body-derived evidence window adds no successful evidence, the graph "
        "may spend replacement cost to sample a different situated basin.",
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_active_embodied_developmental_capability", "instance"],
            ["episode", "has_embodied_development_receipt", "receipt"],
        ],
        "where": And(
            Eq(P0("episode", "development_learning_active"), L(1)),
            Eq(P0("episode", "embodiment_reset_available"), L(1)),
            Eq(P0("episode", "embodiment_terminal"), L(0)),
            Eq(P0("episode", "embodied_reset_requested"), L(0)),
            Eq(Count(ACTIVE_RESET_REQUESTS), L(0)),
            Eq(P0("receipt", "development_receipt_closed"), L(1)),
            Eq(P0("receipt", "development_experience_retained"), L(1)),
            Eq(P0("receipt", "embodiment_destroyed"), L(0)),
            Eq(
                P0("receipt", "development_receipt_seq"),
                P0("episode", "latest_development_receipt_seq"),
            ),
            Gt(
                P0("receipt", "development_receipt_seq"),
                P0("instance", "last_receipt_seq"),
            ),
            Not(capability_success()),
            Not(Lt(
                Minus(
                    Plus(P0("instance", "failure_count"), L(1)),
                    P0("instance", "last_reinstantiation_failure_count"),
                ),
                Max(L(1), P0("episode", "development_evidence_window")),
            )),
        ),
        "effects": [
            ["add_node", "request", "EmbodiedResetRequest", {
                "status": "requested",
                "cause": "capability_experiment_stalled",
                "cause_receipt_seq": T(P0(
                    "receipt", "development_receipt_seq"
                )),
                "departing_generation": T(P0(
                    "episode", "embodiment_generation"
                )),
                "replacement_cost_units": T(P0(
                    "episode", "embodiment_reset_cost_units"
                )),
                "retained_experience_count": T(P0(
                    "episode", "retained_developmental_experience_count"
                )),
                "memory_preservation_required": 1,
                "reinstantiation_spec_ready": 0,
                "integer_native": 1,
                "output_authority": 1,
            }],
            ["add_edge", "episode", "has_embodied_reset_request", "request"],
            ["add_edge", "episode", "has_active_embodied_reset_request", "request"],
            ["add_edge", "request", "caused_by_embodied_receipt", "receipt"],
            ["set_attr", "receipt", "embodied_reset_requested", 1],
            ["set_attr", "episode", "embodied_reset_requested", 1],
            ["set_attr", "episode", "reset_requested", 1],
            ["set_attr", "instance", "last_reinstantiation_failure_count", T(
                Plus(P0("instance", "failure_count"), L(1))
            )],
        ],
    }


def select_reinstantiation_scenario_rule():
    """Choose an initial condition that probes the unresolved capability."""
    eligible = Filter(
        reset_scenarios(),
        "candidate_scenario",
        And(
            Eq(P0("candidate_scenario", "enabled"), L(1)),
            Or(
                Eq(A("candidate_scenario", "target_goal"), L("any")),
                Eq(
                    A("candidate_scenario", "target_goal"),
                    A("instance", "goal"),
                ),
            ),
        ),
    )
    selected = Argmin(
        eligible,
        "candidate_scenario",
        P0("candidate_scenario", "selection_count"),
        V("episode"),
    )
    return {
        "name": "ed_select_reinstantiation_scenario_for_active_frontier",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Curiosity selects among interface-declared initial "
        "conditions that can expose the active capability. Reuse count is an "
        "integer exploration cost; the selected condition is one component "
        "of a graph-authored reset act.",
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_active_embodied_developmental_capability", "instance"],
            ["episode", "has_active_embodied_reset_request", "request"],
            ["episode", "has_embodied_reset_scenario", "scenario"],
        ],
        "where": And(
            Eq(A("request", "status"), L("requested")),
            Eq(P0("request", "reinstantiation_spec_ready"), L(0)),
            Gt(Count(eligible), L(0)),
            Eq(V("scenario"), selected),
        ),
        "effects": [
            ["set_attr", "request", "scenario_name", T(A(
                "scenario", "name"
            ))],
            ["set_attr", "request", "scenario_ordinal", T(P0(
                "scenario", "ordinal"
            ))],
            ["set_attr", "request", "fixture_quarter_turn_x", T(P0(
                "scenario", "fixture_quarter_turn_x"
            ))],
            ["set_attr", "request", "fixture_quarter_turn_y", T(P0(
                "scenario", "fixture_quarter_turn_y"
            ))],
            ["set_attr", "request", "fixture_quarter_turn_z", T(P0(
                "scenario", "fixture_quarter_turn_z"
            ))],
            ["set_attr", "request", "target_capability", T(A(
                "instance", "name"
            ))],
            ["set_attr", "request", "reinstantiation_spec_ready", 1],
            ["set_attr", "scenario", "selection_count", T(Plus(
                P0("scenario", "selection_count"), L(1)
            ))],
            ["add_edge", "request", "selects_embodied_reset_scenario", "scenario"],
        ],
    }


def acknowledge_embodiment_reinstantiation_rule():
    """Bind a mechanical reset receipt to the request that caused it."""
    return {
        "name": "ed_continue_learning_in_reinstantiated_embodiment",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A reset advances the situated embodiment generation. "
        "Only body-local terminal state is cleared; learned graph structure "
        "and the destructive receipt remain intact.",
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_active_embodied_reset_request", "request"],
        ],
        "where": Gt(
            P0("episode", "body_reset_seq"),
            P0("episode", "embodied_reset_processed_seq"),
        ),
        "effects": [
            ["add_node", "reset_receipt", "EmbodiedResetReceipt", {
                "status": "enacted",
                "reset_seq": T(P0("episode", "body_reset_seq")),
                "generation": T(Plus(
                    P0("episode", "embodiment_generation"), L(1)
                )),
                "replacement_cost_units": T(P0(
                    "episode", "last_body_reset_cost_units"
                )),
                "retained_experience_count": T(P0(
                    "episode", "retained_developmental_experience_count"
                )),
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "episode", "has_embodied_reset_receipt", "reset_receipt"],
            ["add_edge", "request", "has_embodied_reset_receipt", "reset_receipt"],
            ["set_attr", "request", "status", "enacted"],
            ["del_edge", "episode", "has_active_embodied_reset_request", "request"],
            ["set_attr", "episode", "embodied_reset_processed_seq", T(P0(
                "episode", "body_reset_seq"
            ))],
            ["set_attr", "episode", "embodiment_generation", T(Plus(
                P0("episode", "embodiment_generation"), L(1)
            ))],
            ["set_attr", "episode", "embodiment_reset_iteration_count", T(Plus(
                P0("episode", "embodiment_reset_iteration_count"), L(1)
            ))],
            ["set_attr", "episode", "embodiment_reset_cost_total_units", T(Plus(
                P0("episode", "embodiment_reset_cost_total_units"),
                P0("episode", "last_body_reset_cost_units"),
            ))],
            ["set_attr", "episode", "embodiment_terminal", 0],
            ["set_attr", "episode", "embodied_reset_requested", 0],
            ["set_attr", "episode", "reset_requested", 0],
        ],
    }


def derive_body_receipt_window_rule():
    """THE WINDOW IS THE BODY'S DEGREES OF FREEDOM.

    A magic number is a quantity whose relatum you failed to name, and this
    rule's consumer names the relatum itself: "a BODY-DERIVED receipt window".
    The body-derived quantity that makes "a single milestone event is not
    competence" quantitative is the count of INDEPENDENTLY ACTUATED JOINTS —
    the number of distinct ways this body could have produced the observation
    the milestone is read from. One success says one degree of freedom moved
    once; competence at a whole-body capability means the evidence spans the
    body it is a capability OF. A richer body therefore owes more evidence,
    which is exactly the scaling the phrase asks for.

    Two other candidates were considered and rejected:

    * `LearningPlanStep.evidence_budget_units` — it is written live, but it is
      the plan's SPEND ALLOWANCE, not a competence bar. Using a budget as a
      threshold says "you are competent because you used your allotment", which
      is the same conflation of spending with succeeding this tree keeps
      finding. It is also plan-derived, not body-derived, so it does not answer
      the comment.
    * prerequisite depth — the active capability has zero prerequisites, so
      this would leave the window at 0 and the guard exactly as vacuous as it
      already was. A derivation that changes nothing is not a derivation.

    If the body does not declare its actuated degrees of freedom, this rule
    writes NOTHING. That is deliberate: an underived window must stay ABSENT so
    the retention guard can refuse to open at all, rather than coalescing to 0
    and waving every milestone through. Failing to have a window must not be
    priced as having met it.
    """
    return {
        "name": "ed_derive_body_receipt_window_from_morphology",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": (
            "The receipt window is read off the body's actuated degrees of "
            "freedom — the number of distinct ways the body could have produced "
            "the milestone observation. Body-derived, as its consumer requires, "
            "and carried with its provenance so a derived window is never "
            "confusable with an assumed one. A body that declares no degrees of "
            "freedom leaves the window ABSENT rather than 0."
        ),
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_embodied_body_schema", "body"],
            ["body", "grounded_in_embodied_raw_body", "raw_body"],
        ],
        "where": And(
            declared("raw_body", "actuated_joint_count"),
            Gt(P0("raw_body", "actuated_joint_count"), L(0)),
        ),
        "effects": [
            ["set_attr", "episode", "development_evidence_window",
             T(P0("raw_body", "actuated_joint_count"))],
            ["set_attr", "episode", "development_evidence_window_measured", 1],
            ["set_attr", "episode", "development_evidence_window_relatum",
             "actuated_joint_count"],
        ],
    }


def open_retention_rule():
    contexts = Neighbours("instance", "has_embodied_developmental_context")
    prerequisites = Neighbours(
        "instance", "requires_embodied_developmental_capability"
    )
    return {
        "name": "ed_open_delayed_retention_test_after_varied_competence",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A single milestone event is not competence. Require a "
        "body-derived receipt window and more successful contexts than the "
        "number of prerequisite capabilities before opening retention. The "
        "window is DECLARED-OR-REFUSE: with no window derived for this body "
        "the gate does not open at all, because a window written by nothing "
        "used to coalesce to 0 through the `+0` idiom and made both evidence "
        "guards pass unconditionally -- this comment described a check the "
        "code did not perform.",
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_active_embodied_developmental_capability", "instance"],
        ],
        "where": And(
            Eq(P0("episode", "development_learning_active"), L(1)),
            Eq(A("instance", "status"), L("active")),
            # AN ABSENT WINDOW IS NOT A SATISFIED ONE. Without this the two
            # comparisons below read against a coalesced 0 and are tautologies;
            # with it, a body whose window cannot be derived simply never opens
            # retention, which is the honest failure rather than a silent pass.
            declared("episode", "development_evidence_window"),
            Or(
                Not(Eq(A("instance", "evidence_kind"), L("effector_coverage"))),
                Eq(P0("episode", "development_effector_coverage_complete"), L(1)),
            ),
            Not(Lt(P0("instance", "attempt_count"),
                   P0("episode", "development_evidence_window"))),
            Not(Lt(P0("instance", "success_count"),
                   P0("episode", "development_evidence_window"))),
            Gt(Count(contexts), Count(prerequisites)),
        ),
        "effects": [
            ["set_attr", "instance", "status", "retention_due"],
            ["set_attr", "instance", "retention_start_seq", T(
                P0("instance", "last_receipt_seq")
            )],
            ["set_attr", "instance", "asym_count", T(
                P0("episode", "development_evidence_window")
            )],
            ["del_edge", "episode", "has_active_embodied_developmental_capability", "instance"],
        ],
    }


def release_incomplete_experiment_rule():
    contexts = Neighbours("instance", "has_embodied_developmental_context")
    prerequisites = Neighbours(
        "instance", "requires_embodied_developmental_capability"
    )
    competent = And(
        Not(Lt(P0("instance", "attempt_count"),
               P0("episode", "development_evidence_window"))),
        Not(Lt(P0("instance", "success_count"),
               P0("episode", "development_evidence_window"))),
        Gt(Count(contexts), Count(prerequisites)),
    )
    return {
        "name": "ed_release_incomplete_experiment_back_to_frontier",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "One action has one active developmental question. After "
        "its receipt, return an incomplete ability to the shared curiosity "
        "frontier so concurrently learnable abilities can interleave.",
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_active_embodied_developmental_capability", "instance"],
            ["episode", "has_embodied_development_receipt", "receipt"],
        ],
        "where": And(
            Eq(A("instance", "status"), L("active")),
            Eq(P0("instance", "last_receipt_seq"),
               P0("receipt", "development_receipt_seq")),
            Gt(P0("receipt", "development_receipt_seq"),
               P0("instance", "activation_receipt_seq")),
            Not(competent),
        ),
        "effects": [
            ["del_edge", "episode", "has_active_embodied_developmental_capability", "instance"],
            ["set_attr", "instance", "status", "available"],
        ],
    }


def defer_retention_retest_rule():
    delayed_success = And(
        capability_success(),
        Not(Lt(
            Minus(
                P0("receipt", "development_receipt_seq"),
                P0("instance", "retention_start_seq"),
            ),
            P0("episode", "development_evidence_window"),
        )),
    )
    return {
        "name": "ed_defer_unsatisfied_retention_retest",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_active_embodied_developmental_capability", "instance"],
            ["episode", "has_embodied_development_receipt", "receipt"],
        ],
        "where": And(
            Eq(A("instance", "status"), L("retention_due")),
            Eq(P0("instance", "last_receipt_seq"),
               P0("receipt", "development_receipt_seq")),
            Gt(P0("receipt", "development_receipt_seq"),
               P0("instance", "activation_receipt_seq")),
            Not(delayed_success),
        ),
        "effects": [[
            "del_edge", "episode",
            "has_active_embodied_developmental_capability", "instance",
        ]],
    }


def master_after_retention_rule():
    return {
        "name": "ed_master_only_after_delayed_successful_retest",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_active_embodied_developmental_capability", "instance"],
            ["episode", "has_embodied_development_receipt", "receipt"],
        ],
        "where": And(
            Eq(P0("episode", "development_learning_active"), L(1)),
            Eq(A("instance", "status"), L("retention_due")),
            Eq(P0("receipt", "development_receipt_closed"), L(1)),
            Eq(P0("instance", "last_receipt_seq"),
               P0("receipt", "development_receipt_seq")),
            Gt(P0("receipt", "development_receipt_seq"),
               P0("instance", "activation_receipt_seq")),
            capability_success(),
            Not(Lt(
                Minus(
                    P0("receipt", "development_receipt_seq"),
                    P0("instance", "retention_start_seq"),
                ),
                P0("episode", "development_evidence_window"),
            )),
        ),
        "effects": [
            ["set_attr", "instance", "status", "mastered"],
            ["set_attr", "instance", "retention_count", T(Plus(
                P0("instance", "retention_count"), L(1),
            ))],
            ["set_attr", "instance", "warm_start_requires_verification", 0],
            ["del_edge", "episode", "has_active_embodied_developmental_capability", "instance"],
            ["set_attr", "episode", "embodied_developmental_mastery_count", T(Plus(
                P0("episode", "embodied_developmental_mastery_count"), L(1),
            ))],
        ],
    }


def clear_exhausted_frontier_rule():
    return {
        "name": "ed_clear_active_label_when_capability_frontier_is_exhausted",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [[
            "agent", "has_embodied_development_episode", "episode",
        ]],
        "where": And(
            Eq(P0("episode", "development_learning_active"), L(1)),
            Eq(Count(Neighbours(
                "episode", "has_active_embodied_developmental_capability"
            )), L(0)),
            Eq(Count(eligible_instances()), L(0)),
            Not(Eq(
                A("episode", "active_embodied_developmental_capability"),
                L("inactive"),
            )),
        ),
        "effects": [
            ["set_attr", "episode", "active_embodied_developmental_goal", "inactive"],
            ["set_attr", "episode", "active_embodied_developmental_capability", "inactive"],
        ],
    }


def capability_memory_name():
    return StringConcat(
        L("developmental_capability:"),
        A("instance", "name"),
        L(":"),
        ToJsonString(A("episode", "body_capability_signature")),
    )


def capability_experience_memory_name():
    return StringConcat(
        L("developmental_experience:"),
        A("instance", "name"),
        L(":"),
        ToJsonString(A("episode", "body_capability_signature")),
    )


def matching_capability_experience_memories():
    return Filter(
        Neighbours(
            "agent", "has_embodied_developmental_experience_memory"
        ),
        "experience_memory",
        And(
            Eq(A("experience_memory", "capability_name"),
               A("instance", "name")),
            Eq(A("experience_memory", "goal"), A("instance", "goal")),
            Eq(
                A("experience_memory", "evidence_kind"),
                A("instance", "evidence_kind"),
            ),
            Eq(
                A("experience_memory", "signature"),
                A("episode", "body_capability_signature"),
            ),
            Not(Eq(A("experience_memory", "status"), L("superseded"))),
        ),
    )


def store_partial_capability_experience_rule():
    return {
        "name": "ed_store_partial_capability_experience_at_lifetime_boundary",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Consolidate unfinished evidence rather than forcing each "
        "fresh embodiment to repeat it. This memory is output-null and is "
        "never itself evidence of mastery.",
        "match": [
            ["agent", "has_humanoid_episode", "motor_episode"],
            ["motor_episode", "projects_embodied_development", "episode"],
            ["episode", "has_embodied_developmental_capability", "instance"],
        ],
        "where": And(
            Eq(P0("motor_episode", "library_consolidation_requested"), L(1)),
            Gt(P0("instance", "attempt_count"), L(0)),
            Not(Eq(A("instance", "status"), L("mastered"))),
            Eq(Count(matching_capability_experience_memories()), L(0)),
        ),
        "effects": [
            ["add_node", "experience_memory",
             "EmbodiedDevelopmentalExperienceMemory", {
                "name": T(capability_experience_memory_name()),
                "signature": T(A("episode", "body_capability_signature")),
                "capability_name": T(A("instance", "name")),
                "goal": T(A("instance", "goal")),
                "evidence_kind": T(A("instance", "evidence_kind")),
                "status": T(A("instance", "status")),
                "attempt_count": T(P0("instance", "attempt_count")),
                "success_count": T(P0("instance", "success_count")),
                "failure_count": T(P0("instance", "failure_count")),
                "effector_coverage_scored_count": T(P0(
                    "instance", "effector_coverage_scored_count"
                )),
                "retention_pending": T(If(
                    Eq(A("instance", "status"), L("retention_due")),
                    L(1), L(0),
                )),
                "output_authority": 0,
                "integer_native": 1,
                "source": "experience",
            }],
            ["add_edge", "agent",
             "has_embodied_developmental_experience_memory",
             "experience_memory"],
            ["add_edge", "instance",
             "stores_as_embodied_developmental_experience_memory",
             "experience_memory"],
        ],
    }


def update_partial_capability_experience_rule():
    return {
        "name": "ed_update_partial_capability_experience_at_lifetime_boundary",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_humanoid_episode", "motor_episode"],
            ["motor_episode", "projects_embodied_development", "episode"],
            ["episode", "has_embodied_developmental_capability", "instance"],
            ["agent", "has_embodied_developmental_experience_memory",
             "experience_memory"],
        ],
        "where": And(
            Eq(P0("motor_episode", "library_consolidation_requested"), L(1)),
            Gt(P0("instance", "attempt_count"), L(0)),
            Not(Eq(A("instance", "status"), L("mastered"))),
            Eq(A("experience_memory", "capability_name"),
               A("instance", "name")),
            Eq(A("experience_memory", "goal"), A("instance", "goal")),
            Eq(A("experience_memory", "evidence_kind"),
               A("instance", "evidence_kind")),
            Eq(A("experience_memory", "signature"),
               A("episode", "body_capability_signature")),
            Not(Eq(A("experience_memory", "status"), L("superseded"))),
            Lt(P0("experience_memory", "attempt_count"),
               P0("instance", "attempt_count")),
        ),
        "effects": [
            ["set_attr", "experience_memory", "status",
             T(A("instance", "status"))],
            ["set_attr", "experience_memory", "attempt_count",
             T(P0("instance", "attempt_count"))],
            ["set_attr", "experience_memory", "success_count",
             T(P0("instance", "success_count"))],
            ["set_attr", "experience_memory", "failure_count",
             T(P0("instance", "failure_count"))],
            ["set_attr", "experience_memory", "effector_coverage_scored_count",
             T(P0("instance", "effector_coverage_scored_count"))],
            ["set_attr", "experience_memory", "retention_pending", T(If(
                Eq(A("instance", "status"), L("retention_due")),
                L(1), L(0),
            ))],
            ["add_edge", "instance",
             "stores_as_embodied_developmental_experience_memory",
             "experience_memory"],
        ],
    }


def store_partial_capability_context_rule():
    known_contexts = Neighbours(
        "experience_memory", "has_embodied_developmental_experience_context"
    )
    return {
        "name": "ed_store_partial_capability_context_at_lifetime_boundary",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_humanoid_episode", "motor_episode"],
            ["motor_episode", "projects_embodied_development", "episode"],
            ["episode", "has_embodied_developmental_capability", "instance"],
            ["instance", "has_embodied_developmental_context", "context"],
            ["agent", "has_embodied_developmental_experience_memory",
             "experience_memory"],
        ],
        "where": And(
            Eq(P0("motor_episode", "library_consolidation_requested"), L(1)),
            Eq(A("experience_memory", "capability_name"),
               A("instance", "name")),
            Eq(A("experience_memory", "goal"), A("instance", "goal")),
            Eq(A("experience_memory", "evidence_kind"),
               A("instance", "evidence_kind")),
            Eq(A("experience_memory", "signature"),
               A("episode", "body_capability_signature")),
            Not(Eq(A("experience_memory", "status"), L("superseded"))),
            Eq(Count(Filter(
                known_contexts,
                "known_context",
                Eq(A("known_context", "signature"), A("context", "signature")),
            )), L(0)),
        ),
        "effects": [
            ["add_node", "context_memory",
             "EmbodiedDevelopmentalExperienceContextMemory", {
                "signature": T(A("context", "signature")),
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "experience_memory",
             "has_embodied_developmental_experience_context",
             "context_memory"],
        ],
    }


def recall_exact_body_experience_rule():
    return {
        "name": "ed_recall_exact_body_partial_experience_without_mastery",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Exact-body experience restores evidence, not authority. "
        "A pending retention state still needs a fresh successful receipt.",
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "instance"],
            ["episode", "has_embodied_developmental_capability", "instance"],
            ["agent", "has_embodied_developmental_experience_memory",
             "experience_memory"],
        ],
        "where": And(
            Eq(P0("instance", "attempt_count"), L(0)),
            Eq(A("instance", "name"),
               A("experience_memory", "capability_name")),
            Eq(A("instance", "goal"), A("experience_memory", "goal")),
            Eq(A("instance", "evidence_kind"),
               A("experience_memory", "evidence_kind")),
            Eq(A("experience_memory", "signature"),
               A("episode", "body_capability_signature")),
            Not(Eq(A("experience_memory", "status"), L("superseded"))),
            Eq(Count(Neighbours(
                "instance", "recalls_exact_embodied_developmental_experience"
            )), L(0)),
        ),
        "effects": [
            ["add_edge", "instance",
             "recalls_exact_embodied_developmental_experience",
             "experience_memory"],
            ["set_attr", "instance", "attempt_count",
             T(P0("experience_memory", "attempt_count"))],
            ["set_attr", "instance", "success_count",
             T(P0("experience_memory", "success_count"))],
            ["set_attr", "instance", "failure_count",
             T(P0("experience_memory", "failure_count"))],
            ["set_attr", "instance", "effector_coverage_scored_count",
             T(P0("experience_memory", "effector_coverage_scored_count"))],
            ["set_attr", "instance", "q",
             T(P0("experience_memory", "failure_count"))],
            ["set_attr", "instance", "status", T(If(
                Eq(P0("experience_memory", "retention_pending"), L(1)),
                L("retention_due"), L("available"),
            ))],
            ["set_attr", "instance", "retention_start_seq", T(Minus(
                P0("episode", "latest_development_receipt_seq"),
                P0("episode", "development_evidence_window"),
            ))],
            ["set_attr", "instance", "warm_start_requires_verification", 1],
            ["set_attr", "step", "evidence_spent_units",
             T(P0("experience_memory", "attempt_count"))],
            ["set_attr", "step", "successful_evidence_units",
             T(P0("experience_memory", "success_count"))],
            ["set_attr", "step", "failed_evidence_units",
             T(P0("experience_memory", "failure_count"))],
        ],
    }


def recall_exact_body_experience_context_rule():
    known = Neighbours("instance", "has_embodied_developmental_context")
    return {
        "name": "ed_recall_exact_body_partial_experience_context",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["instance", "recalls_exact_embodied_developmental_experience",
             "experience_memory"],
            ["experience_memory",
             "has_embodied_developmental_experience_context", "context_memory"],
        ],
        "where": Eq(Count(Filter(
            known,
            "known_context",
            Eq(A("known_context", "signature"),
               A("context_memory", "signature")),
        )), L(0)),
        "effects": [
            ["add_node", "context", "EmbodiedDevelopmentalContext", {
                "signature": T(A("context_memory", "signature")),
                "first_receipt_seq": 0,
                "integer_native": 1,
            }],
            ["add_edge", "instance", "has_embodied_developmental_context",
             "context"],
        ],
    }


def matching_metacognitive_revision_memories():
    return Filter(
        Neighbours("agent", "has_metacognitive_learning_revision_memory"),
        "known_memory",
        And(
            Eq(A("known_memory", "signature"),
               A("episode", "body_capability_signature")),
            Eq(A("known_memory", "suspended_goal"), A("current_step", "goal")),
            Eq(A("known_memory", "redirect_goal"), A("next_step", "goal")),
            Eq(A("known_memory", "suspended_capability"),
               A("current_step", "name")),
            Eq(A("known_memory", "redirect_capability"),
               A("next_step", "name")),
            Not(Eq(A("known_memory", "status"), L("superseded"))),
        ),
    )


def mastered_learning_steps(plan: str = "plan"):
    return Filter(
        Neighbours(plan, "has_learning_plan_step"),
        "mastered_step",
        Exists(
            Neighbours("mastered_step", "plans_learning_capability"),
            "mastered_instance",
            Eq(A("mastered_instance", "status"), L("mastered")),
        ),
    )


def metacognitive_counterexample_context_matches(
    memory: str = "counterexample_memory",
    plan: str = "plan",
):
    members = Neighbours(
        memory, "has_metacognitive_counterexample_context_member"
    )
    mastered = mastered_learning_steps(plan)
    represented_members = Filter(
        members,
        "context_member",
        Exists(
            mastered,
            "represented_step",
            Eq(A("represented_step", "name"),
               A("context_member", "capability_name")),
        ),
    )
    represented_steps = Filter(
        mastered,
        "represented_step",
        Exists(
            members,
            "context_member",
            Eq(A("context_member", "capability_name"),
               A("represented_step", "name")),
        ),
    )
    selected_source = Filter(
        Neighbours(plan, "has_selected_learning_plan_step"),
        "selected_source_step",
        Eq(A("selected_source_step", "name"),
           A(memory, "source_capability")),
    )
    return And(
        Eq(Count(members), P0(memory, "mastery_context_member_count")),
        Eq(Count(mastered), P0(memory, "mastery_context_member_count")),
        Eq(Count(represented_members), Count(members)),
        Eq(Count(represented_steps), Count(mastered)),
        Gt(Count(selected_source), L(0)),
    )


def store_metacognitive_counterexample_memory_rule():
    return {
        "name": "ed_store_failed_learning_revision_with_mastery_context",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A failed revision is retained as a contextual negative "
        "result, not a permanent blacklist. Its relational mastery frontier "
        "defines when the counterexample is applicable.",
        "match": [
            ["agent", "has_humanoid_episode", "motor_episode"],
            ["motor_episode", "projects_embodied_development", "episode"],
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_learning_plan_revision", "revision"],
            ["revision", "revises_learning_plan_step", "source_step"],
            ["revision", "redirects_to_learning_plan_step", "failed_step"],
        ],
        "where": And(
            Eq(P0("motor_episode", "library_consolidation_requested"), L(1)),
            Eq(A("revision", "status"), L("counterexample_observed")),
            Eq(Count(Neighbours(
                "revision", "stores_as_metacognitive_counterexample_memory"
            )), L(0)),
        ),
        "effects": [
            ["add_node", "counterexample_memory",
             "MetacognitiveLearningCounterexampleMemory", {
                "signature": T(A("episode", "body_capability_signature")),
                "source_capability": T(A("source_step", "name")),
                "source_goal": T(A("source_step", "goal")),
                "failed_redirect_capability": T(A("failed_step", "name")),
                "failed_redirect_goal": T(A("failed_step", "goal")),
                "order_n": T(P0("revision", "order_n")),
                "mastery_context_member_count": T(Count(
                    mastered_learning_steps()
                )),
                "status": "retained",
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "agent",
             "has_metacognitive_learning_counterexample_memory",
             "counterexample_memory"],
            ["add_edge", "revision",
             "stores_as_metacognitive_counterexample_memory",
             "counterexample_memory"],
        ],
    }


def store_metacognitive_counterexample_context_rule():
    known = Neighbours(
        "counterexample_memory",
        "has_metacognitive_counterexample_context_member",
    )
    return {
        "name": "ed_store_failed_revision_mastery_context_member",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_humanoid_episode", "motor_episode"],
            ["motor_episode", "projects_embodied_development", "episode"],
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_learning_plan_revision", "revision"],
            ["revision", "stores_as_metacognitive_counterexample_memory",
             "counterexample_memory"],
            ["plan", "has_learning_plan_step", "mastered_step"],
            ["mastered_step", "plans_learning_capability", "mastered_instance"],
        ],
        "where": And(
            Eq(P0("motor_episode", "library_consolidation_requested"), L(1)),
            Eq(A("mastered_instance", "status"), L("mastered")),
            Eq(Count(Filter(
                known,
                "known_member",
                Eq(A("known_member", "capability_name"),
                   A("mastered_step", "name")),
            )), L(0)),
        ),
        "effects": [
            ["add_node", "context_member",
             "MetacognitiveCounterexampleContextMember", {
                "capability_name": T(A("mastered_step", "name")),
                "goal": T(A("mastered_step", "goal")),
                "status": "mastered",
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "counterexample_memory",
             "has_metacognitive_counterexample_context_member",
             "context_member"],
        ],
    }


def activate_metacognitive_counterexample_hold_rule():
    active_for_memory = Filter(
        Neighbours("failed_step", "has_learning_policy_counterexample_hold"),
        "known_hold",
        And(
            Eq(A("known_hold", "status"), L("active")),
            Exists(
                Neighbours(
                    "known_hold", "derived_from_metacognitive_counterexample_memory"
                ),
                "known_memory",
                Eq(V("known_memory"), V("counterexample_memory")),
            ),
        ),
    )
    return {
        "name": "ed_activate_failed_revision_hold_in_exact_mastery_context",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_learning_plan_step", "failed_step"],
            ["agent", "has_metacognitive_learning_counterexample_memory",
             "counterexample_memory"],
        ],
        "where": And(
            Eq(A("counterexample_memory", "signature"),
               A("episode", "body_capability_signature")),
            Eq(A("counterexample_memory", "failed_redirect_capability"),
               A("failed_step", "name")),
            metacognitive_counterexample_context_matches(),
            Eq(Count(active_for_memory), L(0)),
        ),
        "effects": [
            ["add_node", "hold", "LearningPolicyCounterexampleHold", {
                "status": "active",
                "kind": "retained_failed_revision_in_exact_context",
                "order_n": T(P0("counterexample_memory", "order_n")),
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "failed_step",
             "has_learning_policy_counterexample_hold", "hold"],
            ["add_edge", "hold",
             "derived_from_metacognitive_counterexample_memory",
             "counterexample_memory"],
        ],
    }


def release_metacognitive_counterexample_hold_rule():
    return {
        "name": "ed_release_failed_revision_hold_after_context_changes",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_learning_plan_step", "failed_step"],
            ["failed_step", "has_learning_policy_counterexample_hold", "hold"],
            ["hold", "derived_from_metacognitive_counterexample_memory",
             "counterexample_memory"],
        ],
        "where": And(
            Eq(A("hold", "status"), L("active")),
            Not(metacognitive_counterexample_context_matches()),
        ),
        "effects": [["set_attr", "hold", "status", "released"]],
    }


def store_metacognitive_revision_memory_rule():
    return {
        "name": "ed_store_metacognitive_plan_revision_at_lifetime_boundary",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Retain a verified plan counterexample by exact body shape. "
        "The memory is output-null: recall changes experiment allocation, "
        "never actuator authority or competence evidence.",
        "match": [
            ["agent", "has_humanoid_episode", "motor_episode"],
            ["motor_episode", "projects_embodied_development", "episode"],
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_learning_plan_revision", "revision"],
            ["revision", "revises_learning_plan_step", "current_step"],
            ["revision", "redirects_to_learning_plan_step", "next_step"],
        ],
        "where": And(
            Eq(P0("motor_episode", "library_consolidation_requested"), L(1)),
            Eq(A("revision", "status"), L("enacted")),
            Eq(Count(matching_metacognitive_revision_memories()), L(0)),
        ),
        "effects": [
            ["add_node", "memory", "MetacognitiveLearningRevisionMemory", {
                "signature": T(A("episode", "body_capability_signature")),
                "suspended_goal": T(A("current_step", "goal")),
                "redirect_goal": T(A("next_step", "goal")),
                "suspended_capability": T(A("current_step", "name")),
                "redirect_capability": T(A("next_step", "name")),
                "order_n": T(P0("revision", "order_n")),
                "status": "retained",
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "agent", "has_metacognitive_learning_revision_memory",
             "memory"],
            ["add_edge", "revision", "stores_as_metacognitive_learning_revision_memory",
             "memory"],
        ],
    }


def update_metacognitive_revision_memory_order_rule():
    return {
        "name": "ed_retain_highest_metacognitive_policy_order_at_lifetime_boundary",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Retain reflective practice as the highest demonstrated "
        "policy order for this exact body and plan counterexample.",
        "match": [
            ["agent", "has_humanoid_episode", "motor_episode"],
            ["motor_episode", "projects_embodied_development", "episode"],
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_active_metacognitive_learning_policy", "policy"],
            ["plan", "has_learning_plan_revision", "revision"],
            ["revision", "revises_learning_plan_step", "current_step"],
            ["revision", "redirects_to_learning_plan_step", "next_step"],
            ["agent", "has_metacognitive_learning_revision_memory", "memory"],
        ],
        "where": And(
            Eq(P0("motor_episode", "library_consolidation_requested"), L(1)),
            Eq(A("memory", "signature"), A("episode", "body_capability_signature")),
            Eq(A("memory", "suspended_capability"), A("current_step", "name")),
            Eq(A("memory", "redirect_capability"), A("next_step", "name")),
            Lt(P0("memory", "order_n"), P0("policy", "order_n")),
        ),
        "effects": [[
            "set_attr", "memory", "order_n", T(P0("policy", "order_n"))
        ]],
    }


def recall_metacognitive_revision_memory_rule():
    recalled = Neighbours(
        "current_instance", "reassess_after_learning_capability"
    )
    return {
        "name": "ed_recall_exact_body_metacognitive_plan_revision",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "An exact-shape plan counterexample warm-starts allocation "
        "but remains conditional: mastering the redirect target reopens the "
        "suspended experiment.",
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_active_metacognitive_learning_policy", "policy"],
            ["plan", "has_learning_plan_step", "current_step"],
            ["current_step", "plans_learning_capability", "current_instance"],
            ["plan", "has_learning_plan_step", "next_step"],
            ["next_step", "plans_learning_capability", "next_instance"],
            ["agent", "has_metacognitive_learning_revision_memory", "memory"],
        ],
        "where": And(
            Eq(A("memory", "signature"), A("episode", "body_capability_signature")),
            Eq(A("memory", "suspended_goal"), A("current_step", "goal")),
            Eq(A("memory", "redirect_goal"), A("next_step", "goal")),
            Eq(A("memory", "suspended_capability"), A("current_step", "name")),
            Eq(A("memory", "redirect_capability"), A("next_step", "name")),
            Not(Eq(A("current_instance", "status"), L("mastered"))),
            Not(Eq(A("next_instance", "status"), L("mastered"))),
            Eq(Count(Filter(
                recalled, "known_condition",
                Eq(V("known_condition"), V("next_instance")),
            )), L(0)),
        ),
        "effects": [
            ["add_node", "recalled_revision", "LearningPlanRevision", {
                "kind": "recalled_exact_body_learning_plan_revision",
                "reason": "retained_verified_pareto_counterexample",
                "status": "enacted",
                "order_n": T(P0("memory", "order_n")),
                "redirect_success_baseline": T(P0(
                    "next_instance", "success_count"
                )),
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "plan", "has_learning_plan_revision",
             "recalled_revision"],
            ["add_edge", "recalled_revision", "revises_learning_plan_step",
             "current_step"],
            ["add_edge", "recalled_revision", "redirects_to_learning_plan_step",
             "next_step"],
            ["add_edge", "memory", "instantiates_learning_plan_revision",
             "recalled_revision"],
            ["del_edge", "episode", "has_active_embodied_developmental_capability",
             "current_instance"],
            ["del_edge", "plan", "has_selected_learning_plan_step", "current_step"],
            ["add_edge", "current_instance", "reassess_after_learning_capability",
             "next_instance"],
            ["add_edge", "memory", "recalled_by_learning_plan", "plan"],
            ["set_attr", "current_step", "status", "meta_suspended"],
            ["set_attr", "current_instance", "status", "meta_suspended"],
            ["set_attr", "next_step", "status", "ready"],
            ["set_attr", "policy", "order_n", T(Max(
                P0("policy", "order_n"), P0("memory", "order_n")
            ))],
        ],
    }


def supersede_partial_experience_after_mastery_rule():
    return {
        "name": "ed_supersede_partial_experience_after_mastery",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_embodied_developmental_capability", "instance"],
            ["agent", "has_embodied_developmental_experience_memory",
             "experience_memory"],
        ],
        "where": And(
            Eq(A("instance", "status"), L("mastered")),
            Eq(A("experience_memory", "capability_name"),
               A("instance", "name")),
            Eq(A("experience_memory", "goal"), A("instance", "goal")),
            Eq(A("experience_memory", "evidence_kind"),
               A("instance", "evidence_kind")),
            Eq(A("experience_memory", "signature"),
               A("episode", "body_capability_signature")),
            Not(Eq(A("experience_memory", "status"), L("superseded"))),
        ),
        "effects": [["set_attr", "experience_memory", "status", "superseded"]],
    }


def record_unstorable_mastery_memory_rule():
    """THE SKIP, MADE VISIBLE.

    `ed_store_mastered_capability_by_structural_body_shape` now refuses to mint
    a capability memory when the episode carries no
    `body_capability_signature` to key it by. A refusal nobody can see is the
    same disease as the malformed part it replaces -- a part silently dropped
    from a codebook is precisely what this tree spent a day removing -- so the
    refusal is written onto the instance where an operator and a later rule can
    both find it.

    It records WHY, not merely that: the key is missing, and the memory that
    would have been stored is therefore unaddressable.
    """
    return {
        "name": "ed_record_unstorable_mastery_memory_for_want_of_a_body_key",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": (
            "A mastered capability whose episode declares no body capability "
            "signature cannot be stored as a shape-addressed memory. The "
            "refusal is recorded on the instance rather than dropped, so an "
            "absent cross-body transfer is legible as a stated gap instead of "
            "looking like a capability that was never mastered."
        ),
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_embodied_developmental_capability", "instance"],
        ],
        "where": And(
            Eq(A("instance", "status"), L("mastered")),
            Not(declared("episode", "body_capability_signature")),
            Not(Eq(A("instance", "mastery_memory_withheld"), L(1))),
        ),
        "effects": [
            ["set_attr", "instance", "mastery_memory_withheld", 1],
            ["set_attr", "instance", "mastery_memory_withheld_reason",
             "episode declares no body_capability_signature to key the memory by"],
        ],
    }


def Sum(source, var, value):
    return {"type": "Sum", "source": source, "var_name": var, "value": value}


def InNeighbours(name, edge):
    return {"type": "InNeighbours", "node": V(name), "edge_type": edge}


def effector_survey_coverage_rules():
    """THE EFFECTOR SURVEY'S OWN COMPLETENESS, DERIVED FROM THE BODY.

    Stage 1 (`effector_consequence_survey`, `evidence_kind: effector_coverage`)
    scores a receipt as successful only when
    `episode.development_effector_coverage_complete == 1` AND the receipt moved
    the body. The second half was wired earlier today; the first was in the dark
    list -- read by six rules, written by none -- so stage 1 sat at 118 attempts
    and 0 successes, exactly as stage 0 sat before its own field was written.

    WHAT COMPLETE MEANS, read off the consumers rather than assumed: the stage
    is a SURVEY of effector consequences, so it is complete when every effector
    THE BODY ITSELF DECLARES has been exercised by at least one grounded
    receipt. Both halves are already in the graph and neither is invented here:

      * declared -- `body -has_opaque_embodied_actuator_affordance->`, the
        body schema's published actuator affordances;
      * exercised -- a candidate that `models_opaque_affordance` an affordance
        and carries `experience_units > 0`, which is incremented only by
        `emb_retire_settled_motor_selection_and_reopen_pareto_frontier` against
        GROUNDED evidence. Exercise therefore means a real trial happened, not
        that one was proposed.

    THE TRAP, and it is today's pathology in its nastiest form: if completeness
    were `covered == declared` and the declared count were absent or zero, then
    0 == 0 and the survey would read COMPLETE having surveyed nothing --
    handing stage 1 a free pass exactly as a vacuous window would have handed
    retention one. So the declared count must be PRESENT and POSITIVE before
    completeness can be asserted at all, and a body that declares no effectors
    is recorded as UNMEASURABLE rather than complete. A body with no declared
    effectors is not fully surveyed; there is nothing to survey it against.
    """
    affordances = Filter(
        Neighbours("body", "has_opaque_embodied_actuator_affordance"),
        "survey_affordance",
        Eq(P0("survey_affordance", "tonic_default"), L(0)),
    )
    declared_count = P0("episode", "development_effector_declared_count")
    covered_count = P0("episode", "development_effector_covered_count")
    return [
        {
            "name": "ed_mark_exercised_effector_affordance",
            "area": "general_cognition",
            "latency_class": "hard_realtime",
            "batch": False,
            "comment": (
                "An affordance is EXERCISED when some candidate modelling it "
                "has grounded experience. `experience_units` is incremented "
                "only against grounded evidence, so this reads real trials "
                "rather than proposals. Unconditional and a pure function of "
                "the candidate set, so re-firing rewrites the same flag."
            ),
            "match": [
                ["body", "has_opaque_embodied_actuator_affordance", "affordance"],
            ],
            "where": L(True),
            "effects": [
                ["set_attr", "affordance", "exercised", T(If(
                    Or(
                        Exists(
                            InNeighbours(
                                "affordance", "models_opaque_affordance"
                            ),
                            "candidate",
                            Gt(P0("candidate", "experience_units"), L(0)),
                        ),
                        Exists(
                            InNeighbours(
                                "affordance",
                                "exercises_opaque_embodied_actuator_affordance",
                            ),
                            "receipt",
                            And(
                                Eq(P0("receipt", "causal_receipt_closed"), L(1)),
                                Eq(P0("receipt", "development_receipt_closed"), L(1)),
                            ),
                        ),
                    ),
                    L(1), L(0),
                ))],
            ],
        },
        {
            "name": "ed_count_effector_survey_coverage",
            "area": "general_cognition",
            "latency_class": "hard_realtime",
            "batch": False,
            "comment": (
                "Declared and covered effector counts, both read off the body. "
                "UNCONDITIONAL by necessity: `Count`/`Sum` over `Neighbours` "
                "evaluate to their identity inside a `where` while being "
                "correct in an effect, measured in this tree, so the "
                "aggregation cannot be guarded on its own value."
            ),
            "match": [
                ["agent", "has_embodied_development_episode", "episode"],
                ["episode", "has_embodied_body_schema", "body"],
            ],
            "where": L(True),
            "effects": [
                ["set_attr", "episode", "development_effector_declared_count",
                 T(Count(affordances))],
                ["set_attr", "episode", "development_effector_covered_count",
                 T(Sum(affordances, "affordance", P0("affordance", "exercised")))],
            ],
        },
        {
            "name": "ed_assert_effector_survey_complete_only_against_a_declared_body",
            "area": "general_cognition",
            "latency_class": "hard_realtime",
            "batch": False,
            "comment": (
                "Completeness is asserted ONLY against a body that declares a "
                "positive number of effectors. An absent or zero declared count "
                "makes `covered >= declared` trivially true, which would read "
                "as a fully surveyed body having surveyed nothing -- the free "
                "pass this guard exists to refuse. Such a body is recorded "
                "UNMEASURABLE, which is a different statement from incomplete."
            ),
            "match": [
                ["agent", "has_embodied_development_episode", "episode"],
            ],
            "where": L(True),
            "effects": [
                ["set_attr", "episode", "development_effector_coverage_complete",
                 T(If(And(
                     # Null-tested beside every coalesced read, so absence can
                     # never reach the comparison as a measured zero.
                     declared("episode", "development_effector_declared_count"),
                     declared("episode", "development_effector_covered_count"),
                     Gt(declared_count, L(0)),
                     Not(Lt(covered_count, declared_count)),
                 ), L(1), L(0)))],
                ["set_attr", "episode", "development_effector_coverage_unmeasurable",
                 T(If(And(
                     declared("episode", "development_effector_declared_count"),
                     Gt(declared_count, L(0)),
                 ), L(0), L(1)))],
            ],
        },
    ]


def store_mastered_capability_rule():
    existing = Filter(
        Neighbours(
            "agent", "has_embodied_developmental_capability_memory"
        ),
        "existing_memory",
        And(
            Eq(A("existing_memory", "capability_name"),
               A("instance", "name")),
            Eq(A("existing_memory", "goal"), A("instance", "goal")),
            Eq(
                A("existing_memory", "evidence_kind"),
                A("instance", "evidence_kind"),
            ),
            Eq(
                A("existing_memory", "signature"),
                A("episode", "body_capability_signature"),
            ),
        ),
    )
    return {
        "name": "ed_store_mastered_capability_by_structural_body_shape",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_embodied_developmental_capability", "instance"],
        ],
        "where": And(
            Eq(A("instance", "status"), L("mastered")),
            # A CODEBOOK PART WITHOUT A SIGNATURE IS NOT A PART. This memory is
            # keyed BY STRUCTURAL BODY SHAPE, and its key is read from
            # `episode.body_capability_signature` -- which NOTHING in any seed
            # writes. Minted anyway, the part carried `name` (a StringConcat,
            # always a present string) beside a `signature` of None, which is
            # exactly `load_parts`'s malformed case: it panics, poisons the
            # substrate mutex, and kills the process.
            #
            # Measured: that panic fires AT THE MOMENT OF MASTERY, because this
            # rule's own guard is `status == 'mastered'`. It is why no run in
            # this line has ever recorded an ordinal advance -- runs 4, 5 and 6
            # all reached `retention_due`/`mastered` at 142-146 trials and died
            # there. Mastery itself was killing the process.
            #
            # Refusing to mint is legitimate here and not a silent drop: a
            # memory with no key is meaningless to a codebook addressed by key,
            # and the refusal is RECORDED on the instance by the sibling rule
            # below rather than vanishing. Mastery itself is unaffected -- it is
            # set elsewhere; only the cross-body transfer memory is withheld,
            # and it is withheld visibly.
            declared("episode", "body_capability_signature"),
            Eq(Count(Neighbours(
                "instance", "stores_as_embodied_developmental_capability_memory"
            )), L(0)),
            Eq(Count(existing), L(0)),
        ),
        "effects": [
            ["add_node", "memory", "EmbodiedDevelopmentalCapabilityMemory", {
                "name": T(capability_memory_name()),
                "signature": T(A("episode", "body_capability_signature")),
                "capability_name": T(A("instance", "name")),
                "goal": T(A("instance", "goal")),
                "evidence_kind": T(A("instance", "evidence_kind")),
                "success_count": T(P0("instance", "success_count")),
                "failure_count": T(P0("instance", "failure_count")),
                "mastery_receipt_seq": T(P0("instance", "last_receipt_seq")),
                "context_count": T(Count(Neighbours(
                    "instance", "has_embodied_developmental_context"
                ))),
                "retention_count": T(P0("instance", "retention_count")),
                "output_authority": 0,
                "integer_native": 1,
                "source": "experience",
            }],
            ["add_edge", "agent", "has_embodied_developmental_capability_memory", "memory"],
            ["add_edge", "instance", "stores_as_embodied_developmental_capability_memory", "memory"],
        ],
    }


def memory_shape(memory, field):
    return {
        "type": "ShapeDecode",
        "goal": A("episode", "body_capability_signature"),
        "codebook_type": "EmbodiedDevelopmentalCapabilityMemory",
        "codebook_scope": SetT(A(memory, "name")),
        "beam": 1,
        "max_steps": 1,
        "cand_k": 1,
        "field": field,
        "wild_objects": False,
    }


def warm_start_similar_body_rule():
    covered = memory_shape("memory", "covered_count")
    residual = memory_shape("memory", "residual")
    return {
        "name": "ed_warm_start_capability_from_similar_body_shape",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Initialization-time shape recall must settle before the "
        "first receipt makes attempt_count nonzero; background starvation "
        "would permanently erase an otherwise valid prior. Transfer only an "
        "output-null capability/search prior when "
        "shared morphology motifs outnumber the residual. The new body must "
        "still earn a complete local competence and delayed-retention window.",
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_embodied_developmental_capability", "instance"],
            ["agent", "has_embodied_developmental_capability_memory", "memory"],
        ],
        "where": And(
            Eq(A("instance", "name"), A("memory", "capability_name")),
            Eq(A("instance", "goal"), A("memory", "goal")),
            Eq(
                A("instance", "evidence_kind"),
                A("memory", "evidence_kind"),
            ),
            Eq(P0("instance", "attempt_count"), L(0)),
            Eq(Count(Neighbours(
                "instance", "warm_starts_from_embodied_developmental_capability"
            )), L(0)),
            Gt(covered, L(0)),
            Gt(covered, Count(residual)),
            Not(Eq(A("memory", "signature"),
                   A("episode", "body_capability_signature"))),
        ),
        "effects": [
            ["add_edge", "instance", "warm_starts_from_embodied_developmental_capability", "memory"],
            ["set_attr", "instance", "status", "warm_available"],
            ["set_attr", "instance", "warm_start_overlap", T(covered)],
            ["set_attr", "instance", "warm_start_requires_verification", 1],
            ["set_attr", "episode", "developmental_cross_body_warm_start_count", T(Plus(
                P0("episode", "developmental_cross_body_warm_start_count"), L(1),
            ))],
        ],
    }


def recall_exact_body_capability_rule():
    return {
        "name": "ed_recall_exact_body_capability_for_local_reverification",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "An exact structural body can reopen a retained ability "
        "at the verification boundary. Recall has zero output authority and "
        "requires a fresh successful receipt before mastery is restored.",
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_embodied_developmental_capability", "instance"],
            ["agent", "has_embodied_developmental_capability_memory", "memory"],
        ],
        "where": And(
            Eq(A("instance", "name"), A("memory", "capability_name")),
            Eq(A("instance", "goal"), A("memory", "goal")),
            Eq(
                A("instance", "evidence_kind"),
                A("memory", "evidence_kind"),
            ),
            Eq(P0("instance", "attempt_count"), L(0)),
            Eq(A("memory", "signature"),
               A("episode", "body_capability_signature")),
            Eq(Count(Neighbours(
                "instance", "recalls_exact_embodied_developmental_capability"
            )), L(0)),
        ),
        "effects": [
            [
                "add_edge", "instance",
                "recalls_exact_embodied_developmental_capability", "memory",
            ],
            ["set_attr", "instance", "status", "retention_due"],
            ["set_attr", "instance", "retention_start_seq", T(Minus(
                P0("episode", "latest_development_receipt_seq"),
                P0("episode", "development_evidence_window"),
            ))],
            ["set_attr", "instance", "warm_start_requires_verification", 1],
            ["set_attr", "episode", "developmental_exact_body_recall_count", T(
                Plus(
                    P0("episode", "developmental_exact_body_recall_count"),
                    L(1),
                )
            )],
        ],
    }


def manifest() -> dict:
    name_to_id = {
        row["name"]: ordinal + 1
        for ordinal, row in enumerate(CAPABILITIES)
    }
    nodes = [
        {
            "local_id": ordinal + 1,
            "type": "EmbodiedDevelopmentalCapabilityTemplate",
            "attrs": {
                "ordinal": ordinal,
                "name": row["name"],
                "goal": row["goal"],
                "evidence_kind": row["evidence"],
                "developmental_ecology": row["ecology"],
                "human_analogue": row["human_analogue"],
                "desired_body_state_signature": row.get(
                    "desired_body_state_signature"
                ),
                "desired_orientation_units": row.get(
                    "desired_orientation_units", 0
                ),
                "clinical_milestone": row.get("clinical_milestone", 0),
                "optional_route": row.get("optional_route", 0),
                "signature": [
                    ["developmental_goal", row["goal"]],
                    ["evidence_kind", row["evidence"]],
                ],
                "output_authority": 0,
                "integer_native": 1,
            },
        }
        for ordinal, row in enumerate(CAPABILITIES)
    ]
    edges = [
        {
            "src": {"role": "agent_root"},
            "type": "has_embodied_developmental_capability_template",
            "tgt": {"local": ordinal + 1},
            "attrs": {},
        }
        for ordinal in range(len(CAPABILITIES))
    ]
    for row in CAPABILITIES:
        for required in row["requires"]:
            edges.append({
                "src": {"local": name_to_id[row["name"]]},
                "type": "requires_embodied_developmental_capability_template",
                "tgt": {"local": name_to_id[required]},
                "attrs": {},
            })
    return {
        "id": "embodied_development",
        "version": "2.12.0",
        "depends_on": [
            "decision_core", "cognitive_pareto", "metacognitive_learning",
            "metacognitive_program_discrimination",
            "cognitive_supervision",
            "embodied_program_trajectory", "embodied_physics_proposal",
        ],
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "description": "Receipt-grounded developmental capability DAG with "
        "a persistent self-directed learning plan, non-scalar Pareto "
        "experiment selection, order-N metacognitive plan revision, explicit "
        "evidence budgets, causally grounded structural-surprise signals, "
        "generic order-N Goal wiring, per-effector consequence subgoals, "
        "renewable surprise/time-triggered process leases, "
        "capability-keyed delayed retention, and verified similar-morphology "
        "transfer.",
        "nodes": nodes,
        "edges": edges,
        "productions": [
            {
                "provenance": "embodied_development:episode",
                "src": {"type": "Agent", "var": "agent"},
                "edge_type": "has_embodied_development_episode",
                "tgt": {"type": "EmbodiedDevelopmentEpisode", "var": "episode"},
            },
            {
                "provenance": "embodied_development:template",
                "src": {"type": "Agent", "var": "agent"},
                "edge_type": "has_embodied_developmental_capability_template",
                "tgt": {"type": "EmbodiedDevelopmentalCapabilityTemplate", "var": "template"},
            },
            {
                "provenance": "embodied_development:instance",
                "src": {"type": "EmbodiedDevelopmentEpisode", "var": "episode"},
                "edge_type": "has_embodied_developmental_capability",
                "tgt": {"type": "EmbodiedSituatedDevelopmentalCapability", "var": "instance"},
            },
            {
                "provenance": "embodied_development:active",
                "src": {"type": "EmbodiedDevelopmentEpisode", "var": "episode"},
                "edge_type": "has_active_embodied_developmental_capability",
                "tgt": {"type": "EmbodiedSituatedDevelopmentalCapability", "var": "instance"},
            },
            {
                "provenance": "embodied_development:causal_receipt",
                "src": {"type": "EmbodiedDevelopmentEpisode", "var": "episode"},
                "edge_type": "has_embodied_development_receipt",
                "tgt": {"type": "Node", "var": "receipt"},
            },
            {
                "provenance": "embodied_development:process_surprise_signal",
                "src": {"type": "CognitiveProcess", "var": "process"},
                "edge_type": "observes_process_signal",
                "tgt": {"type": "CognitiveProcessSignal", "var": "signal"},
            },
            {
                "provenance": "embodied_development:surprise_receipt_grounding",
                "src": {"type": "CognitiveProcessSignal", "var": "signal"},
                "edge_type": "grounded_in_causal_receipt",
                "tgt": {"type": "Node", "var": "receipt"},
            },
            {
                "provenance": "embodied_development:self_learning_plan",
                "src": {"type": "EmbodiedDevelopmentEpisode", "var": "episode"},
                "edge_type": "has_self_directed_learning_plan",
                "tgt": {"type": "LearningPlan", "var": "plan"},
            },
            {
                "provenance": "embodied_development:learning_plan_step",
                "src": {"type": "LearningPlan", "var": "plan"},
                "edge_type": "has_learning_plan_step",
                "tgt": {"type": "LearningPlanStep", "var": "step"},
            },
            {
                "provenance": "embodied_development:planned_capability",
                "src": {"type": "LearningPlanStep", "var": "step"},
                "edge_type": "plans_learning_capability",
                "tgt": {"type": "EmbodiedSituatedDevelopmentalCapability", "var": "instance"},
            },
            {
                "provenance": "embodied_development:step_goal",
                "src": {"type": "LearningPlanStep", "var": "step"},
                "edge_type": "pursues_goal",
                "tgt": {"type": "Goal", "var": "goal"},
            },
            {
                "provenance": "embodied_development:goal_subgoal",
                "src": {"type": "Goal", "var": "goal"},
                "edge_type": "has_subgoal",
                "tgt": {"type": "Goal", "var": "subgoal"},
            },
            {
                "provenance": "embodied_development:cell_consequence_goal",
                "src": {"type": "SomatomotorWaveCell", "var": "cell"},
                "edge_type": "has_consequence_goal",
                "tgt": {"type": "Goal", "var": "goal"},
            },
            {
                "provenance": "embodied_development:somatomotor_field",
                "src": {"type": "EmbodiedDevelopmentEpisode", "var": "episode"},
                "edge_type": "has_somatomotor_wave_field",
                "tgt": {"type": "SomatomotorWaveField", "var": "field"},
            },
            {
                "provenance": "embodied_development:somatomotor_cell",
                "src": {"type": "SomatomotorWaveField", "var": "field"},
                "edge_type": "has_somatomotor_wave_cell",
                "tgt": {"type": "SomatomotorWaveCell", "var": "cell"},
            },
            {
                "provenance": "embodied_development:cell_effector",
                "src": {"type": "SomatomotorWaveCell", "var": "cell"},
                "edge_type": "represents_embodied_effector",
                "tgt": {"type": "Node", "var": "effector"},
            },
            {
                "provenance": "embodied_development:learning_step_dependency",
                "src": {"type": "LearningPlanStep", "var": "step"},
                "edge_type": "requires_learning_plan_step",
                "tgt": {"type": "LearningPlanStep", "var": "required_step"},
            },
            {
                "provenance": "embodied_development:learning_decision_profile",
                "src": {"type": "LearningPlan", "var": "plan"},
                "edge_type": "has_learning_decision_profile",
                "tgt": {"type": "ParetoProfile", "var": "profile"},
            },
            {
                "provenance": "embodied_development:active_learning_decision_profile",
                "src": {"type": "LearningPlan", "var": "plan"},
                "edge_type": "has_active_learning_decision_profile",
                "tgt": {"type": "ParetoProfile", "var": "profile"},
            },
            {
                "provenance": "embodied_development:learning_candidate_step",
                "src": {"type": "ParetoCandidate", "var": "candidate"},
                "edge_type": "proposes_learning_plan_step",
                "tgt": {"type": "LearningPlanStep", "var": "step"},
            },
            {
                "provenance": "embodied_development:archived_learning_candidate",
                "src": {"type": "ParetoProfile", "var": "profile"},
                "edge_type": "archived_learning_decision_candidate",
                "tgt": {"type": "ParetoCandidate", "var": "candidate"},
            },
            {
                "provenance": "embodied_development:selected_learning_step",
                "src": {"type": "LearningPlan", "var": "plan"},
                "edge_type": "has_selected_learning_plan_step",
                "tgt": {"type": "LearningPlanStep", "var": "step"},
            },
            {
                "provenance": "embodied_development:selected_learning_decision",
                "src": {"type": "LearningPlan", "var": "plan"},
                "edge_type": "has_selected_learning_decision",
                "tgt": {"type": "ParetoCandidate", "var": "candidate"},
            },
            {
                "provenance": "embodied_development:reset_revises_learning_step",
                "src": {"type": "EmbodiedResetRequest", "var": "request"},
                "edge_type": "revises_learning_plan_step",
                "tgt": {"type": "LearningPlanStep", "var": "step"},
            },
            {
                "provenance": "embodied_development:learning_plan_revision",
                "src": {"type": "LearningPlan", "var": "plan"},
                "edge_type": "has_learning_plan_revision",
                "tgt": {"type": "LearningPlanRevision", "var": "revision"},
            },
            {
                "provenance": "embodied_development:revision_revises_learning_step",
                "src": {"type": "LearningPlanRevision", "var": "revision"},
                "edge_type": "revises_learning_plan_step",
                "tgt": {"type": "LearningPlanStep", "var": "step"},
            },
            {
                "provenance": "embodied_development:reset_scenario",
                "src": {"type": "EmbodiedDevelopmentEpisode", "var": "episode"},
                "edge_type": "has_embodied_reset_scenario",
                "tgt": {"type": "EmbodiedResetScenario", "var": "scenario"},
            },
            {
                "provenance": "embodied_development:reset_request",
                "src": {"type": "EmbodiedDevelopmentEpisode", "var": "episode"},
                "edge_type": "has_embodied_reset_request",
                "tgt": {"type": "EmbodiedResetRequest", "var": "request"},
            },
            {
                "provenance": "embodied_development:active_reset_request",
                "src": {"type": "EmbodiedDevelopmentEpisode", "var": "episode"},
                "edge_type": "has_active_embodied_reset_request",
                "tgt": {"type": "EmbodiedResetRequest", "var": "request"},
            },
            {
                "provenance": "embodied_development:reset_cause",
                "src": {"type": "EmbodiedResetRequest", "var": "request"},
                "edge_type": "caused_by_embodied_receipt",
                "tgt": {"type": "Node", "var": "receipt"},
            },
            {
                "provenance": "embodied_development:selected_reset_scenario",
                "src": {"type": "EmbodiedResetRequest", "var": "request"},
                "edge_type": "selects_embodied_reset_scenario",
                "tgt": {"type": "EmbodiedResetScenario", "var": "scenario"},
            },
            {
                "provenance": "embodied_development:episode_reset_receipt",
                "src": {"type": "EmbodiedDevelopmentEpisode", "var": "episode"},
                "edge_type": "has_embodied_reset_receipt",
                "tgt": {"type": "EmbodiedResetReceipt", "var": "reset_receipt"},
            },
            {
                "provenance": "embodied_development:request_reset_receipt",
                "src": {"type": "EmbodiedResetRequest", "var": "request"},
                "edge_type": "has_embodied_reset_receipt",
                "tgt": {"type": "EmbodiedResetReceipt", "var": "reset_receipt"},
            },
            {
                "provenance": "embodied_development:memory",
                "src": {"type": "Agent", "var": "agent"},
                "edge_type": "has_embodied_developmental_capability_memory",
                "tgt": {"type": "EmbodiedDevelopmentalCapabilityMemory", "var": "memory"},
            },
            {
                "provenance": "embodied_development:experience_memory",
                "src": {"type": "Agent", "var": "agent"},
                "edge_type": "has_embodied_developmental_experience_memory",
                "tgt": {"type": "EmbodiedDevelopmentalExperienceMemory", "var": "memory"},
            },
            {
                "provenance": "embodied_development:stored_experience_memory",
                "src": {"type": "EmbodiedSituatedDevelopmentalCapability", "var": "instance"},
                "edge_type": "stores_as_embodied_developmental_experience_memory",
                "tgt": {"type": "EmbodiedDevelopmentalExperienceMemory", "var": "memory"},
            },
            {
                "provenance": "embodied_development:experience_context_memory",
                "src": {"type": "EmbodiedDevelopmentalExperienceMemory", "var": "memory"},
                "edge_type": "has_embodied_developmental_experience_context",
                "tgt": {"type": "EmbodiedDevelopmentalExperienceContextMemory", "var": "context"},
            },
            {
                "provenance": "embodied_development:recalled_experience_memory",
                "src": {"type": "EmbodiedSituatedDevelopmentalCapability", "var": "instance"},
                "edge_type": "recalls_exact_embodied_developmental_experience",
                "tgt": {"type": "EmbodiedDevelopmentalExperienceMemory", "var": "memory"},
            },
            {
                "provenance": "embodied_development:metacognitive_revision_memory",
                "src": {"type": "Agent", "var": "agent"},
                "edge_type": "has_metacognitive_learning_revision_memory",
                "tgt": {"type": "MetacognitiveLearningRevisionMemory", "var": "memory"},
            },
            {
                "provenance": "embodied_development:stored_metacognitive_revision_memory",
                "src": {"type": "LearningPlanRevision", "var": "revision"},
                "edge_type": "stores_as_metacognitive_learning_revision_memory",
                "tgt": {"type": "MetacognitiveLearningRevisionMemory", "var": "memory"},
            },
            {
                "provenance": "embodied_development:recalled_metacognitive_revision_memory",
                "src": {"type": "MetacognitiveLearningRevisionMemory", "var": "memory"},
                "edge_type": "recalled_by_learning_plan",
                "tgt": {"type": "LearningPlan", "var": "plan"},
            },
            {
                "provenance": "embodied_development:instantiated_metacognitive_revision_memory",
                "src": {"type": "MetacognitiveLearningRevisionMemory", "var": "memory"},
                "edge_type": "instantiates_learning_plan_revision",
                "tgt": {"type": "LearningPlanRevision", "var": "revision"},
            },
            {
                "provenance": "embodied_development:metacognitive_counterexample_memory",
                "src": {"type": "Agent", "var": "agent"},
                "edge_type": "has_metacognitive_learning_counterexample_memory",
                "tgt": {"type": "MetacognitiveLearningCounterexampleMemory", "var": "memory"},
            },
            {
                "provenance": "embodied_development:stored_metacognitive_counterexample_memory",
                "src": {"type": "LearningPlanRevision", "var": "revision"},
                "edge_type": "stores_as_metacognitive_counterexample_memory",
                "tgt": {"type": "MetacognitiveLearningCounterexampleMemory", "var": "memory"},
            },
            {
                "provenance": "embodied_development:metacognitive_counterexample_context",
                "src": {"type": "MetacognitiveLearningCounterexampleMemory", "var": "memory"},
                "edge_type": "has_metacognitive_counterexample_context_member",
                "tgt": {"type": "MetacognitiveCounterexampleContextMember", "var": "member"},
            },
            {
                "provenance": "embodied_development:metacognitive_counterexample_hold",
                "src": {"type": "LearningPolicyCounterexampleHold", "var": "hold"},
                "edge_type": "derived_from_metacognitive_counterexample_memory",
                "tgt": {"type": "MetacognitiveLearningCounterexampleMemory", "var": "memory"},
            },
            {
                "provenance": "embodied_development:pareto_escalation_context",
                "src": {"type": "SystemTwoEscalation", "var": "escalation"},
                "edge_type": "about_context",
                "tgt": {"type": "ParetoProfile", "var": "profile"},
            },
            {
                "provenance": "embodied_development:pareto_task_recruitment",
                "src": {"type": "SystemTwoEscalation", "var": "escalation"},
                "edge_type": "recruits_task_set",
                "tgt": {"type": "SystemTwoTaskSet", "var": "task_set"},
            },
            {
                "provenance": "embodied_development:episode_connection",
                "src": {"type": "EmbodiedDevelopmentEpisode", "var": "episode"},
                "edge_type": "grounded_in_embodied_simulator_connection",
                "tgt": {"type": "EmbodiedSimulatorConnection", "var": "connection"},
            },
        ],
        "rules": [
            instantiate_capability_rule(),
            bind_prerequisite_rule(),
            instantiate_self_directed_learning_plan_rule(),
            instantiate_learning_plan_step_rule(),
            instantiate_generic_goal_for_learning_step_rule(),
            bind_learning_plan_step_dependency_rule(),
            bind_generic_goal_dependency_rule(),
            update_generic_goal_from_learning_evidence_rule(),
            instantiate_effector_consequence_subgoal_rule(),
            resolve_effector_consequence_subgoal_rule(),
            refresh_learning_plan_step_readiness_rule(),
            open_learning_decision_profile_rule(),
            mint_learning_decision_candidate_rule(),
            dominate_learning_decision_candidate_rule(),
            select_learning_plan_step_rule(),
            archive_learning_decision_candidate_rule(),
            publish_structural_surprise_to_cognitive_process_rule(),
            release_dominated_process_at_checkin_rule(),
            reopen_process_released_capability_rule(),
            detect_reversal_rule(),
            track_floor_orientation_trajectory_rule(),
            instantiate_locomotor_pareto_profile_rule(),
            suspend_detached_locomotor_pareto_profile_rule(),
            mint_locomotor_phenotype_rule(),
            update_locomotor_phenotype_rule(),
            verify_locomotor_basin_rule(),
            recall_exact_body_experience_rule(),
            recall_exact_body_experience_context_rule(),
            recall_metacognitive_revision_memory_rule(),
            activate_metacognitive_counterexample_hold_rule(),
            release_metacognitive_counterexample_hold_rule(),
            recall_exact_body_capability_rule(),
            warm_start_similar_body_rule(),
            mint_context_rule(),
            retain_causally_closed_experience_rule(),
            mark_terminal_embodiment_rule(),
            request_embodiment_reinstantiation_rule(),
            request_new_situated_experiment_rule(),
            select_reinstantiation_scenario_rule(),
            revise_learning_plan_budget_after_reset_rule(),
            acknowledge_embodiment_reinstantiation_rule(),
            update_learning_plan_step_from_receipt_rule(),
            learn_receipt_rule(),
            skipped_for_want_of_measurement_rule(),
            extend_learning_plan_budget_on_progress_rule(),
            defer_exhausted_learning_step_without_reset_rule(),
            reopen_deferred_learning_step_in_new_embodiment_rule(),
            derive_body_receipt_window_rule(),
            open_retention_rule(),
            release_incomplete_experiment_rule(),
            defer_retention_retest_rule(),
            master_after_retention_rule(),
            complete_learning_plan_step_rule(),
            release_learning_plan_step_rule(),
            complete_self_directed_learning_plan_rule(),
            store_partial_capability_experience_rule(),
            update_partial_capability_experience_rule(),
            store_partial_capability_context_rule(),
            store_metacognitive_revision_memory_rule(),
            update_metacognitive_revision_memory_order_rule(),
            store_metacognitive_counterexample_memory_rule(),
            store_metacognitive_counterexample_context_rule(),
            record_unstorable_mastery_memory_rule(),
            *effector_survey_coverage_rules(),
            store_mastered_capability_rule(),
            supersede_partial_experience_after_mastery_rule(),
            archive_consumed_receipt_rule(),
        ],
    }


def main() -> int:
    output = ROOT / "seeds" / "embodied_development.json"
    payload = manifest()
    output.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {output} ({len(payload['rules'])} rules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
