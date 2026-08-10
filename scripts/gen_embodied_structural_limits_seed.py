"""Generate morphology-neutral structural-limit and cumulative-damage rules.

Body specifications are graph data supplied from design records, material
libraries, inspection, or trusted simulation.  The graph derives the weakest
load-path envelope and updates remaining capacity from measured receipts.
Nothing here discovers an ultimate limit by destructive exploration.
"""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STRUCTURAL_LOADS = (
    "normal_load",
    "peak_force",
    "impulse",
    "impact_energy",
    "thermal_load",
    "dynamic_pressure",
    "roll_moment",
    "pitch_moment",
    "yaw_moment",
    "heat_flux",
    "skin_temperature",
)


def V(name): return {"type": "Var", "name": name}
def L(value): return {"type": "Lit", "value": value}
def A(var, key): return {"type": "Attr", "node": V(var), "key": key}
def AO(node, key): return {"type": "Attr", "node": node, "key": key}
def P0(var, key): return {"type": "Plus", "items": [A(var, key), L(0.0)]}
def P(node, key): return P0(node, key) if isinstance(node, str) else Plus(AO(node, key), L(0.0))
def Plus(*items): return {"type": "Plus", "items": list(items)}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Times(*items): return {"type": "Times", "items": list(items)}
def Div(a, b): return {"type": "Div", "a": a, "b": b}
def Abs(value): return {"type": "Abs", "arg": value}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def And(*items): return {"type": "And", "items": list(items)}
def Or(*items): return {"type": "Or", "items": list(items)}
def Not(item): return {"type": "Not", "arg": item}
def If(cond, then, other): return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}
def Min(*items): return {"type": "Min", "items": list(items)}
def Max(*items): return {"type": "Max", "items": list(items)}
def Neighbours(var, edge): return {"type": "Neighbours", "node": V(var), "edge_type": edge}
def Filter(source, var, predicate): return {"type": "Filter", "source": source, "var_name": var, "predicate": predicate}
def Count(source): return {"type": "Count", "source": source}
def Argmin(source, var, value, default): return {"type": "Argmin", "source": source, "var_name": var, "value": value, "default": default}
def Argmax(source, var, value, default): return {"type": "Argmax", "source": source, "var_name": var, "value": value, "default": default}
def T(term): return {"__term__": term}


COMPONENTS = Neighbours("episode", "has_structural_body_component")


def carrying_components(metric):
    return Filter(
        COMPONENTS,
        "component",
        And(
            Gt(P0("component", f"allowable_{metric}"), L(0.0)),
            Gt(P0("component", f"load_fraction_{metric}"), L(0.0)),
        ),
    )


def effective_limit(component, metric):
    return Div(
        P(component, f"allowable_{metric}"),
        P(component, f"load_fraction_{metric}"),
    )


def open_envelope_rule():
    envelopes = Neighbours("episode", "has_structural_body_envelope")
    return {
        "name": "esl_open_structural_body_envelope",
        "area": "embodied_structural_limits",
        "order": -40,
        "latency_class": "hard_realtime",
        "match": [["agent", "has_embodied_motor_program_episode", "episode"]],
        "where": Eq(Count(envelopes), L(0.0)),
        "effects": [
            ["add_node", "envelope", "StructuralBodyEnvelope", {
                "last_specification_seq": -1.0,
                "last_receipt_seq": -1.0,
                "last_guard_request_seq": -1.0,
                "capacity_fraction": 1.0,
                "cumulative_fatigue_damage": 0.0,
                "maximum_observed_utilization": 0.0,
                "failure": 0.0,
                "last_mass_receipt_seq": -1.0,
                "mass_evidence_count": 0.0,
                "baseline_mass_kg": 0.0,
                "effective_mass_kg": 0.0,
                "payload_mass_delta_kg": 0.0,
                "observed_weight_newtons": 0.0,
                **{f"rated_{metric}": 0.0 for metric in STRUCTURAL_LOADS},
                **{f"safe_{metric}": 0.0 for metric in STRUCTURAL_LOADS},
                **{
                    f"current_stiffness_{metric}": 0.0
                    for metric in STRUCTURAL_LOADS
                },
                **{
                    f"reference_stiffness_{metric}": 0.0
                    for metric in STRUCTURAL_LOADS
                },
                **{
                    f"stiffness_ratio_{metric}": 1.0
                    for metric in STRUCTURAL_LOADS
                },
                **{
                    f"reversible_limit_lower_{metric}": 0.0
                    for metric in STRUCTURAL_LOADS
                },
                **{
                    f"plastic_limit_upper_{metric}": 0.0
                    for metric in STRUCTURAL_LOADS
                },
                **{
                    f"inferred_rated_{metric}": 0.0
                    for metric in STRUCTURAL_LOADS
                },
                **{
                    f"inferred_confidence_{metric}": 0.0
                    for metric in STRUCTURAL_LOADS
                },
                **{
                    f"response_evidence_{metric}": 0.0
                    for metric in STRUCTURAL_LOADS
                },
                **{
                    f"last_response_receipt_{metric}": -1.0
                    for metric in STRUCTURAL_LOADS
                },
                **{
                    f"maximum_{metric}_utilization": 0.0
                    for metric in STRUCTURAL_LOADS
                },
            }],
            ["add_edge", "episode", "has_structural_body_envelope", "envelope"],
        ],
    }


def derive_envelope_rule():
    effects = []
    confidence_terms = []
    for metric in STRUCTURAL_LOADS:
        eligible = carrying_components(metric)
        weakest = Argmin(
            eligible,
            "component",
            effective_limit("component", metric),
            V("episode"),
        )
        has_specification = Gt(Count(eligible), L(0.0))
        rated = If(
            has_specification,
            effective_limit(weakest, metric),
            P0("envelope", f"inferred_rated_{metric}"),
        )
        confidence = If(
            has_specification,
            Plus(AO(weakest, "specification_confidence"), L(0.0)),
            P0("envelope", f"inferred_confidence_{metric}"),
        )
        confidence_terms.append(confidence)
        confidence_derating = If(
            Gt(
                confidence,
                P0("policy", "minimum_specification_confidence"),
            ),
            L(1.0),
            P0("policy", "unknown_capacity_fraction"),
        )
        safe = Times(
            rated,
            P0("envelope", "capacity_fraction"),
            confidence_derating,
            If(
                Gt(P0("envelope", f"response_evidence_{metric}"), L(0.0)),
                Min(L(1.0), P0("envelope", f"stiffness_ratio_{metric}")),
                L(1.0),
            ),
            Div(L(1.0), P0("policy", "structural_safety_factor")),
        )
        effects.extend([
            ["set_attr", "envelope", f"rated_{metric}", T(rated)],
            ["set_attr", "envelope", f"safe_{metric}", T(safe)],
            ["set_attr", "episode", f"state_safe_{metric}", T(safe)],
        ])
    fatigue_candidates = Filter(
        COMPONENTS,
        "component",
        Gt(P0("component", "fatigue_damage_per_second_at_limit"), L(0.0)),
    )
    fastest_fatigue = Argmax(
        fatigue_candidates,
        "component",
        P0("component", "fatigue_damage_per_second_at_limit"),
        V("episode"),
    )
    return {
        "name": "esl_derive_weakest_load_path_envelope",
        "area": "embodied_structural_limits",
        "order": -30,
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_embodied_structural_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_structural_body_envelope", "envelope"],
        ],
        "where": Gt(
            P0("episode", "structural_specification_seq"),
            P0("envelope", "last_specification_seq"),
        ),
        "effects": [
            *effects,
            ["set_attr", "episode", "state_structural_specification_confidence", T(
                Min(*confidence_terms)
            )],
            ["set_attr", "episode", "state_fatigue_damage_per_second_at_limit", T(
                If(
                    Gt(Count(fatigue_candidates), L(0.0)),
                    Plus(
                        AO(
                            fastest_fatigue,
                            "fatigue_damage_per_second_at_limit",
                        ),
                        L(0.0),
                    ),
                    L(0.0),
                )
            )],
            ["set_attr", "episode", "state_structural_capacity_fraction", T(
                P0("envelope", "capacity_fraction")
            )],
            ["set_attr", "envelope", "last_specification_seq", T(
                P0("episode", "structural_specification_seq")
            )],
        ],
    }


def guard_current_envelope_rule():
    safe_violation = Or(*[
        And(
            Gt(P0("envelope", f"safe_{metric}"), L(0.0)),
            Gt(
                Abs(P0("episode", f"state_current_{metric}")),
                P0("envelope", f"safe_{metric}"),
            ),
        )
        for metric in STRUCTURAL_LOADS
    ])
    rated_violation = Or(*[
        And(
            Gt(P0("envelope", f"rated_{metric}"), L(0.0)),
            Gt(
                Abs(P0("episode", f"state_current_{metric}")),
                P0("envelope", f"rated_{metric}"),
            ),
        )
        for metric in STRUCTURAL_LOADS
    ])
    failed = If(
        rated_violation,
        L(1.0),
        P0("envelope", "failure"),
    )
    capacity = If(
        Gt(failed, L(0.5)),
        L(0.0),
        P0("envelope", "capacity_fraction"),
    )
    return {
        "name": "esl_guard_current_structural_envelope_before_release",
        "area": "embodied_structural_limits",
        "order": -20,
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_structural_body_envelope", "envelope"],
        ],
        "where": And(
            Gt(
                P0("episode", "program_request_seq"),
                P0("envelope", "last_guard_request_seq"),
            ),
            Not(Gt(
                P0("episode", "structural_specification_seq"),
                P0("envelope", "last_specification_seq"),
            )),
        ),
        "effects": [
            ["set_attr", "envelope", "failure", T(failed)],
            ["set_attr", "envelope", "capacity_fraction", T(capacity)],
            ["set_attr", "episode", "state_structural_capacity_fraction", T(
                capacity
            )],
            ["set_attr", "episode", "structural_interrupt_required", T(If(
                Or(safe_violation, Gt(failed, L(0.5))),
                L(1.0),
                L(0.0),
            ))],
            ["set_attr", "envelope", "last_guard_request_seq", T(
                P0("episode", "program_request_seq")
            )],
        ],
    }


def infer_dynamic_mass_rule():
    """Track current carried mass separately from the unloaded body prior."""
    direct_mass = P0("outcome", "observed_effective_mass_kg")
    inferred_mass = Div(
        Abs(P0("outcome", "observed_support_force_newtons")),
        Max(
            P0("outcome", "observed_gravity_m_s2"),
            P0("policy", "minimum_gravity_m_s2"),
        ),
    )
    measured_mass = If(Gt(direct_mass, L(0.0)), direct_mass, inferred_mass)
    baseline_mass = If(
        Gt(P0("envelope", "mass_evidence_count"), L(0.0)),
        P0("envelope", "baseline_mass_kg"),
        measured_mass,
    )
    gravity = Max(
        P0("outcome", "observed_gravity_m_s2"),
        P0("policy", "minimum_gravity_m_s2"),
    )
    return {
        "name": "esl_infer_dynamic_mass_and_weight_from_receipt",
        "area": "embodied_structural_plasticity",
        "order": 6,
        "latency_class": "soft_realtime",
        "match": [
            ["agent", "has_embodied_structural_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_structural_body_envelope", "envelope"],
            ["episode", "has_embodied_motor_program_trial", "trial"],
            ["trial", "has_embodied_motor_program_outcome", "outcome"],
        ],
        "where": And(
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("outcome", "structural_response_observed"), L(1.0)),
            Gt(measured_mass, L(0.0)),
            Gt(
                P0("outcome", "request_seq"),
                P0("envelope", "last_mass_receipt_seq"),
            ),
        ),
        "effects": [
            ["set_attr", "envelope", "baseline_mass_kg", T(baseline_mass)],
            ["set_attr", "envelope", "effective_mass_kg", T(measured_mass)],
            ["set_attr", "envelope", "payload_mass_delta_kg", T(Max(
                L(0.0), Minus(measured_mass, baseline_mass)
            ))],
            ["set_attr", "envelope", "observed_weight_newtons", T(Times(
                measured_mass, gravity
            ))],
            ["set_attr", "envelope", "mass_evidence_count", T(Plus(
                P0("envelope", "mass_evidence_count"), L(1.0)
            ))],
            ["set_attr", "envelope", "last_mass_receipt_seq", T(
                P0("outcome", "request_seq")
            )],
        ],
    }


def infer_material_response_rule(metric):
    """Bound one load envelope from reversible and plastic deformation."""
    load = Abs(P0("outcome", f"observed_{metric}"))
    strain = Abs(P0("outcome", f"observed_strain_{metric}"))
    residual = Abs(P0("outcome", f"observed_residual_strain_{metric}"))
    stiffness = Div(load, strain)
    elastic = Not(Gt(
        residual,
        P0("policy", "plastic_residual_strain_threshold"),
    ))
    prior_reference = P0("envelope", f"reference_stiffness_{metric}")
    reference = If(
        Gt(prior_reference, L(0.0)),
        Max(prior_reference, stiffness),
        stiffness,
    )
    stiffness_ratio = Min(L(1.0), Div(stiffness, reference))
    prior_lower = P0("envelope", f"reversible_limit_lower_{metric}")
    lower = If(elastic, Max(prior_lower, load), prior_lower)
    prior_upper = P0("envelope", f"plastic_limit_upper_{metric}")
    upper = If(
        elastic,
        prior_upper,
        If(Gt(prior_upper, L(0.0)), Min(prior_upper, load), load),
    )
    inferred_rated = If(Gt(lower, L(0.0)), lower, upper)
    evidence = Plus(
        P0("envelope", f"response_evidence_{metric}"), L(1.0)
    )
    confidence = Min(
        L(1.0),
        Div(evidence, P0("policy", "response_samples_for_confidence")),
    )
    return {
        "name": f"esl_infer_{metric}_limit_from_material_response",
        "area": "embodied_structural_plasticity",
        "order": 7,
        "latency_class": "soft_realtime",
        "match": [
            ["agent", "has_embodied_structural_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_structural_body_envelope", "envelope"],
            ["episode", "has_embodied_motor_program_trial", "trial"],
            ["trial", "has_embodied_motor_program_outcome", "outcome"],
        ],
        "where": And(
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("outcome", "structural_response_observed"), L(1.0)),
            Gt(load, L(0.0)),
            Gt(strain, P0("policy", "minimum_observable_strain")),
            Gt(
                P0("outcome", "request_seq"),
                P0("envelope", f"last_response_receipt_{metric}"),
            ),
        ),
        "effects": [
            ["set_attr", "envelope", f"current_stiffness_{metric}", T(stiffness)],
            ["set_attr", "envelope", f"reference_stiffness_{metric}", T(reference)],
            ["set_attr", "envelope", f"stiffness_ratio_{metric}", T(stiffness_ratio)],
            ["set_attr", "envelope", f"reversible_limit_lower_{metric}", T(lower)],
            ["set_attr", "envelope", f"plastic_limit_upper_{metric}", T(upper)],
            ["set_attr", "envelope", f"inferred_rated_{metric}", T(inferred_rated)],
            ["set_attr", "envelope", f"inferred_confidence_{metric}", T(confidence)],
            ["set_attr", "envelope", f"response_evidence_{metric}", T(evidence)],
            ["set_attr", "envelope", f"last_response_receipt_{metric}", T(
                P0("outcome", "request_seq")
            )],
            ["set_attr", "episode", "structural_specification_seq", T(
                Plus(P0("episode", "structural_specification_seq"), L(1.0))
            )],
        ],
    }


def integrate_load_receipt_rule():
    utilizations = [
        If(
            Gt(P0("envelope", f"safe_{metric}"), L(0.0)),
            Div(
                Abs(P0("outcome", f"observed_{metric}")),
                P0("envelope", f"safe_{metric}"),
            ),
            L(0.0),
        )
        for metric in STRUCTURAL_LOADS
    ]
    utilization = Max(*utilizations)
    ultimate_utilization = Max(*[
        If(
            Gt(P0("envelope", f"rated_{metric}"), L(0.0)),
            Div(
                Abs(P0("outcome", f"observed_{metric}")),
                P0("envelope", f"rated_{metric}"),
            ),
            L(0.0),
        )
        for metric in STRUCTURAL_LOADS
    ])
    fatigue_increment = Times(
        P0("episode", "state_fatigue_damage_per_second_at_limit"),
        P0("outcome", "action_duration_seconds"),
        utilization,
        utilization,
        utilization,
    )
    cumulative = Plus(
        P0("envelope", "cumulative_fatigue_damage"),
        fatigue_increment,
        Max(L(0.0), P0("outcome", "observed_damage_fraction")),
    )
    failed = If(
        Or(
            Gt(ultimate_utilization, L(1.0)),
            Gt(cumulative, L(1.0)),
        ),
        L(1.0),
        P0("envelope", "failure"),
    )
    capacity = If(
        Gt(failed, L(0.5)),
        L(0.0),
        Max(L(0.0), Minus(L(1.0), cumulative)),
    )
    interrupt = If(
        Or(
            Gt(utilization, L(1.0)),
            Gt(failed, L(0.5)),
        ),
        L(1.0),
        L(0.0),
    )
    return {
        "name": "esl_integrate_structural_load_and_damage_receipt",
        "area": "embodied_structural_plasticity",
        "order": 8,
        "latency_class": "soft_realtime",
        "match": [
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_structural_body_envelope", "envelope"],
            ["episode", "has_embodied_motor_program_trial", "trial"],
            ["trial", "has_embodied_motor_program_outcome", "outcome"],
        ],
        "where": And(
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Gt(
                P0("outcome", "request_seq"),
                P0("envelope", "last_receipt_seq"),
            ),
        ),
        "effects": [
            ["set_attr", "envelope", "cumulative_fatigue_damage", T(cumulative)],
            ["set_attr", "envelope", "maximum_observed_utilization", T(Max(
                P0("envelope", "maximum_observed_utilization"),
                utilization,
            ))],
            *[
                [
                    "set_attr",
                    "envelope",
                    f"maximum_{metric}_utilization",
                    T(Max(
                        P0(
                            "envelope",
                            f"maximum_{metric}_utilization",
                        ),
                        metric_utilization,
                    )),
                ]
                for metric, metric_utilization in zip(
                    STRUCTURAL_LOADS,
                    utilizations,
                )
            ],
            ["set_attr", "envelope", "capacity_fraction", T(capacity)],
            ["set_attr", "envelope", "failure", T(failed)],
            ["set_attr", "envelope", "last_receipt_seq", T(
                P0("outcome", "request_seq")
            )],
            ["set_attr", "episode", "state_structural_capacity_fraction", T(
                capacity
            )],
            ["set_attr", "episode", "structural_interrupt_required", T(
                interrupt
            )],
            ["set_attr", "episode", "structural_specification_seq", T(
                Plus(P0("episode", "structural_specification_seq"), L(1.0))
            )],
        ],
    }


def manifest():
    return {
        "id": "embodied_structural_limits",
        "version": "1.1.0",
        "depends_on": [],
        "area": "embodied_structural_limits",
        "latency_class": "hard_realtime",
        "description": "Specification-grounded component/load-path limits, "
        "online mass and material-response identification, conservative "
        "uncertainty derating and receipt-grounded cumulative damage.",
        "nodes": [{
            "local_id": 1,
            "type": "EmbodiedStructuralPolicy",
            "attrs": {
                "structural_safety_factor": 1.5,
                "minimum_specification_confidence": 0.8,
                "unknown_capacity_fraction": 0.5,
                "minimum_observable_strain": 0.000001,
                "plastic_residual_strain_threshold": 0.002,
                "response_samples_for_confidence": 4.0,
                "minimum_gravity_m_s2": 0.1,
            },
        }],
        "edges": [{
            "src": {"role": "agent_root"},
            "type": "has_embodied_structural_policy",
            "tgt": {"local": 1},
            "attrs": {},
        }],
        "productions": [
            {
                "provenance": "embodied_structural_limits:component",
                "src": {"type": "EmbodiedMotorProgramEpisode", "var": "episode"},
                "edge_type": "has_structural_body_component",
                "tgt": {"type": "StructuralBodyComponent", "var": "component"},
            },
            {
                "provenance": "embodied_structural_limits:load_path",
                "src": {"type": "StructuralBodyComponent", "var": "source"},
                "edge_type": "transfers_structural_load_to",
                "tgt": {"type": "StructuralBodyComponent", "var": "target"},
            },
        ],
        "rules": [
            open_envelope_rule(),
            derive_envelope_rule(),
            guard_current_envelope_rule(),
            infer_dynamic_mass_rule(),
            *[
                infer_material_response_rule(metric)
                for metric in STRUCTURAL_LOADS
            ],
            integrate_load_receipt_rule(),
        ],
    }


def main():
    path = ROOT / "seeds" / "embodied_structural_limits.json"
    payload = manifest()
    path.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)} ({len(payload['rules'])} rules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
