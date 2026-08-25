//! MotorCompose — the embodied motor composer's search, native.
//!
//! The seed-rule composer (gen_embodied_motor_program_seed.py: open best
//! singleton → snapshot-parallel per-group expansion rounds → close when no
//! candidate improves) is correct but interpreted: at 8 quantization
//! intervals its per-request cost is ~300-600 ms of Term-tree evaluation,
//! quadratic in the candidate alphabet (measured 294/82/44 ms at 8/4/2
//! intervals).  This module is the SAME selection as one pure function —
//! the "primitive in Rust, composition in graph" move: the graph still
//! decides WHEN to compose and what to do with the result (seed rules mark
//! the chosen members and assemble the program); Rust only answers the
//! membership question.
//!
//! Parity contract (each item mirrors its Python-named source):
//!   * attr reads default to 0.0 exactly like the seed's P0 (attr-or-zero);
//!   * candidate iteration is ordinal-ascending with first-wins argmin,
//!     matching engine Argmin over the NodeID-sorted Filter set for models
//!     created in ordinal order;
//!   * expansion rounds are SNAPSHOT-parallel (all groups judged against
//!     the pre-round plan, then every improving group-winner added),
//!     matching batch_apply_rule's bind-all-then-apply semantics;
//!   * the improvement guard is strict: cost(plan, c) +
//!     minimum_composition_improvement < cost(plan).
//!
//! All per-model predictions (model_prediction / structural_model_
//! prediction) are plan-independent, so they are computed ONCE into a
//! matrix and every cost is pure arithmetic over it — the property the
//! Term-tree composer cannot express, and the whole speedup.

use crate::graph::{NodeID, TypedGraph};
use crate::sym::{Interner, Sym};
use crate::value::Value;
use std::cell::RefCell;
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

const COMPONENTS: [&str; 7] = [
    "forward",
    "lateral",
    "vertical",
    "roll",
    "pitch",
    "turn",
    "normal_load",
];
const FLOW_FEATURES: [&str; 4] = [
    "flow_forward",
    "flow_lateral",
    "flow_vertical",
    "power_state",
];
const STRUCTURAL_LOADS: [&str; 11] = [
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
];
/// COMPONENTS + drag + energy + the structural loads not already present
/// (mirrors ALL_CONSEQUENCES = dict.fromkeys(COMPONENTS, drag, energy,
/// *STRUCTURAL_LOADS): normal_load dedups).
const PREDICTED_KEYS: [&str; 19] = [
    "forward",
    "lateral",
    "vertical",
    "roll",
    "pitch",
    "turn",
    "normal_load",
    "drag",
    "energy",
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
];
const N_KEYS: usize = PREDICTED_KEYS.len();
const N_LOADS: usize = STRUCTURAL_LOADS.len();

fn key_index(key: &str) -> usize {
    PREDICTED_KEYS.iter().position(|k| *k == key).unwrap()
}

fn fattr(graph: &TypedGraph, interner: &Interner, node: NodeID, key: &str) -> f64 {
    let Some(sym) = interner.lookup(key) else {
        return 0.0;
    };
    if !graph.has_node(node) {
        return 0.0;
    }
    match graph.node(node).attrs.get(&sym) {
        Some(Value::Float(f)) => *f,
        Some(Value::Int(i)) => *i as f64,
        Some(Value::Bool(b)) => {
            if *b {
                1.0
            } else {
                0.0
            }
        }
        _ => 0.0,
    }
}

fn sattr(graph: &TypedGraph, interner: &Interner, node: NodeID, key: &str) -> Option<Sym> {
    let sym = interner.lookup(key)?;
    match graph.node(node).attrs.get(&sym) {
        Some(Value::Str(value)) => Some(*value),
        _ => None,
    }
}

fn active_humanoid_basin_members(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
) -> Vec<NodeID> {
    let desired_context = if fattr(graph, interner, episode, "self_takeoff_drive_active") > 0.5 {
        interner.lookup("self_takeoff")
    } else {
        interner.lookup("locomotion")
    };
    let mut members = Vec::new();
    if let (Some(seed_edge), Some(member_edge), Some(desired_context)) = (
        interner.lookup("has_humanoid_motor_program_basin_seed"),
        interner.lookup("includes_humanoid_phase_action_model"),
        desired_context,
    ) {
        for program in graph.neighbours(episode, Some(seed_edge)) {
            if sattr(graph, interner, program, "motor_task_context") != Some(desired_context) {
                continue;
            }
            members.extend(graph.neighbours(program, Some(member_edge)));
        }
    }

    // Observed motion contributes a dynamic, consequence-specific search
    // basin.  Walk the held graph instead of materialising every
    // stage×program pair: considered hint -> currently realizable source
    // support -> observed transition -> categorical consequence shape <-
    // receipt-grounded local program.  This grants no authority; compose()
    // still uses membership only as an exact-cost tie-break.
    let topology_edges = (
        interner.lookup("considers_humanoid_motor_plan_hint"),
        interner.lookup("has_embodied_motor_plan_hint_stage"),
        interner.lookup("can_transition_to_embodied_motor_plan_hint_stage"),
        interner.lookup("targets_embodied_motor_consequence_shape"),
        interner.lookup("realizes_embodied_motor_consequence_shape"),
        interner.lookup("includes_humanoid_phase_action_model"),
        desired_context,
    );
    if let (
        Some(considered_edge),
        Some(stage_edge),
        Some(transition_edge),
        Some(target_shape_edge),
        Some(realizes_shape_edge),
        Some(member_edge),
        Some(desired_context),
    ) = topology_edges
    {
        let support_0 = fattr(graph, interner, episode, "state_support_0_force") > 0.0;
        let support_1 = fattr(graph, interner, episode, "state_support_1_force") > 0.0;
        let paired = interner.lookup("paired_lower_support");
        let single = interner.lookup("single_lower_support");
        let unsupported = interner.lookup("unsupported");
        for hint in graph.neighbours(episode, Some(considered_edge)) {
            if fattr(graph, interner, hint, "output_authority") != 0.0 {
                continue;
            }
            for source_stage in graph.neighbours(hint, Some(stage_edge)) {
                let support = sattr(graph, interner, source_stage, "support_topology");
                let support_matches = (support == paired && support_0 && support_1)
                    || (support == single && support_0 != support_1)
                    || (support == unsupported && !support_0 && !support_1);
                if !support_matches {
                    continue;
                }
                for target_stage in graph.neighbours(source_stage, Some(transition_edge)) {
                    for shape in graph.neighbours(target_stage, Some(target_shape_edge)) {
                        for program in graph.in_neighbours(shape, Some(realizes_shape_edge)) {
                            if sattr(graph, interner, program, "motor_task_context")
                                != Some(desired_context)
                            {
                                continue;
                            }
                            members.extend(graph.neighbours(program, Some(member_edge)));
                        }
                    }
                }
            }
        }
    }
    members.sort_unstable();
    members.dedup();
    members
}

#[allow(dead_code)]
fn humanoid_composition_input_signature(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
    policy: NodeID,
    model_nodes: &[NodeID],
) -> u64 {
    let mut hasher = DefaultHasher::new();
    for key in [
        "request_seq",
        "state_seq",
        "selected_primary_context_id",
        "current_support_phase",
        "response_frames",
        "manifold_bounds_ready",
        "manifold_bound_dzx",
        "manifold_bound_dzy",
        "manifold_bound_dwx",
        "manifold_bound_dwy",
        "manifold_bound_dvx",
        "manifold_bound_dvy",
        "manifold_bound_dvz",
        "state_qx",
        "state_qy",
        "state_qz",
        "state_qw",
        "state_wx",
        "state_wy",
        "state_vx",
        "state_vy",
        "state_vz",
        "state_x",
        "state_y",
        "state_z",
        "standing_reference_z",
        "lateral_offset",
        "recovery_mode",
        "locomotion_drive_active",
        "state_support_0_force",
        "state_support_1_force",
        "state_support_0_x",
        "state_support_0_y",
        "state_support_1_x",
        "state_support_1_y",
        "support_sensor_count",
        "learned_gait_tilt_envelope",
        "self_takeoff_drive_active",
        "self_takeoff_target_velocity_scale",
        "self_takeoff_compression_scale",
        "body_mass",
        "physics_time_step",
        "lifetime_completed_progress",
        "directed_progress",
        "target_directed_progress_m",
        "active_residual_regime_ordinal",
        "active_gait_attractor_ordinal",
        "motor_effector_group_count",
        "state_contact_force_newtons",
    ] {
        fattr(graph, interner, episode, key)
            .to_bits()
            .hash(&mut hasher);
    }
    sattr(graph, interner, episode, "selected_primary_token").hash(&mut hasher);
    for key in [
        "gravity_acceleration",
        "target_froude_speed",
        "support_phase_prior_strength",
        "minimum_upright_height_fraction",
        "persistent_task_residual_authority",
        "support_geometry_preview_authority",
        "takeoff_motor_compression_authority",
        "future_manifold_enabled",
        "future_manifold_temporal_anchors_enabled",
    ] {
        fattr(graph, interner, policy, key)
            .to_bits()
            .hash(&mut hasher);
    }
    for node in model_nodes {
        node.hash(&mut hasher);
        sattr(graph, interner, *node, "token").hash(&mut hasher);
        for key in [
            "actuator_group",
            "support_phase",
            "context_id",
            "initialized",
            "mean_input_energy_joules",
            "mean_dzx",
            "mean_dzy",
            "mean_dwx",
            "mean_dwy",
            "mean_dvx",
            "mean_dvy",
            "mean_dvz",
            "anchor_z_x",
            "anchor_z_y",
            "anchor_wx",
            "anchor_wy",
            "anchor_vx",
            "anchor_vy",
            "anchor_vz",
            "anchor_lateral_offset",
        ] {
            fattr(graph, interner, *node, key)
                .to_bits()
                .hash(&mut hasher);
        }
        // The cost-of-transport residual reads regime-conditioned capability
        // evidence attached to this model; a changed capability value must
        // invalidate the cache exactly like a changed model attr does.
        if let Some(cap_edge) = interner.lookup("has_embodied_effector_capability") {
            let mut capabilities = graph.neighbours(*node, Some(cap_edge));
            capabilities.sort_unstable();
            for capability in capabilities {
                capability.hash(&mut hasher);
                for key in [
                    "coupling_regime",
                    "vertical_regime",
                    "translation_per_joule",
                    "experience_count",
                ] {
                    fattr(graph, interner, capability, key)
                        .to_bits()
                        .hash(&mut hasher);
                }
            }
        }
    }
    if let Some(edge) = interner.lookup("has_humanoid_synergy_model") {
        let mut synergies = graph.neighbours(episode, Some(edge));
        synergies.sort_unstable();
        for node in synergies {
            node.hash(&mut hasher);
            sattr(graph, interner, node, "token_a").hash(&mut hasher);
            sattr(graph, interner, node, "token_b").hash(&mut hasher);
            for key in [
                "ordinal",
                "approved",
                "residual_dzx",
                "residual_dzy",
                "residual_dwx",
                "residual_dwy",
                "residual_dvx",
                "residual_dvy",
                "residual_dvz",
            ] {
                fattr(graph, interner, node, key)
                    .to_bits()
                    .hash(&mut hasher);
            }
        }
    }
    hasher.finish()
}

struct ModelRow {
    node: NodeID,
    group: f64,
    activation_magnitude: f64,
    log_authority: f64,
    /// Action at which this member was last commanded ALONE.  Absent reads 0,
    /// which is the right polarity: never measured is most worth measuring.
    last_singleton_exercise_seq: f64,
    /// The regime this model is FOR, or 0 for a global model.  This is what
    /// makes shapes INDEX models rather than merely copy them.
    shape_ordinal: f64,
    eligible: bool,
    /// model_prediction per PREDICTED_KEYS entry.
    prediction: [f64; N_KEYS],
    /// structural_model_prediction per STRUCTURAL_LOADS entry.
    structural: [f64; N_LOADS],
}

struct Composer<'a> {
    graph: &'a TypedGraph,
    interner: &'a Interner,
    episode: NodeID,
    policy: NodeID,
    models: Vec<ModelRow>,
    baseline: [f64; N_KEYS],
    targets: [f64; 7],
    weights: [f64; 7],
    drag_weight: f64,
    energy_weight: f64,
    activation_weight: f64,
    /// THE MARGIN, in actions: how long until the nearest region the episode
    /// must not reach.  In-frame and integral by construction (it is a count
    /// of actions); 0 means unpublished, which prices no margin at all.
    margin_actions: f64,
    /// The budget the margin is compared AGAINST.  A margin is meaningless
    /// alone -- `reference / margin` is what makes it a weight, and a weight
    /// is only ever defined in comparison to something else.
    margin_reference_actions: f64,
    margin_weight: f64,
    /// The price of NOT KNOWING a member, and the reference it is measured
    /// against.  Same shape as the margin: a ratio, absent-inert, declared by
    /// the policy.
    attribution_weight: f64,
    attribution_reference_actions: f64,
    request_seq: f64,
    /// The regime the episode is in right now, read from the surprise index.
    current_surprise_ordinal: f64,
    minimum_improvement: f64,
    limits_enabled: bool,
    authority_escape: bool,
    interrupt_required: bool,
    safe_loads: [f64; N_LOADS],
    current_loads: [f64; N_LOADS],
}

impl<'a> Composer<'a> {
    fn build(
        graph: &'a TypedGraph,
        interner: &'a Interner,
        episode: NodeID,
        policy: NodeID,
        model_nodes: &[NodeID],
    ) -> Composer<'a> {
        let ep = |key: &str| fattr(graph, interner, episode, key);
        let po = |key: &str| fattr(graph, interner, policy, key);
        let contextual = po("contextual_effector_prediction_enabled") > 0.5;
        let flow_speed_squared = ep("state_flow_speed_squared");
        let state_features: Vec<f64> = FLOW_FEATURES
            .iter()
            .map(|f| ep(&format!("state_{f}")))
            .collect();

        let mut models: Vec<ModelRow> = Vec::with_capacity(model_nodes.len());
        for node in model_nodes {
            let m = |key: &str| fattr(graph, interner, *node, key);
            // model_prediction, vectorised over keys.
            let position = m("state_effector_position");
            let max_change = m("specified_maximum_position_change_per_action");
            let position_error = m("specified_command_level") - position;
            let bounded = if position_error.abs() > max_change {
                if position_error > 0.0 {
                    max_change
                } else {
                    -max_change
                }
            } else {
                position_error
            };
            let predicted_position = position + bounded;
            let use_specification = m("specified_actuator_dynamics_enabled") > 0.5
                && m("specified_effect_prior_confidence") > 0.5
                && max_change > 0.0;
            let mut prediction = [0.0; N_KEYS];
            for (ki, key) in PREDICTED_KEYS.iter().enumerate() {
                if use_specification {
                    prediction[ki] = m(&format!("specified_passive_mean_{key}"))
                        + m(&format!("specified_position_gain_{key}")) * predicted_position;
                } else {
                    let mut learned = m(&format!("mean_{key}"));
                    if contextual {
                        learned += m(&format!("flow_gain_{key}"))
                            * (flow_speed_squared - m("mean_flow_speed_squared"));
                        for (fi, feature) in FLOW_FEATURES.iter().enumerate() {
                            learned += m(&format!("{feature}_gain_{key}"))
                                * (state_features[fi] - m(&format!("mean_{feature}")));
                        }
                    }
                    prediction[ki] = learned;
                }
            }
            // structural_model_prediction, vectorised over loads.
            let certified = m("structural_certified_default") > 0.5;
            let experienced = m("experience_count") > 0.0;
            let mut structural = [0.0; N_LOADS];
            for (li, load) in STRUCTURAL_LOADS.iter().enumerate() {
                let specified = m(&format!("specified_{load}")).abs();
                structural[li] = if certified {
                    specified
                } else if experienced {
                    prediction[key_index(load)].abs().max(specified)
                } else {
                    specified
                };
            }
            models.push(ModelRow {
                node: *node,
                group: m("actuator_group"),
                activation_magnitude: m("activation_magnitude"),
                log_authority: m("log_authority"),
                last_singleton_exercise_seq: m("last_singleton_exercise_seq"),
                shape_ordinal: m("shape_ordinal"),
                eligible: m("experience_count") > 0.5 && m("available") > 0.5,
                // Filled below: eligibility also depends on the episode's
                // current regime, which is not known per-model.
                prediction,
                structural,
            });
        }

        // SHAPES INDEX MODELS.  A fork carries the regime it was minted for,
        // and is eligible ONLY in that regime; a global model (ordinal 0) is
        // eligible always.  Without this the fork is just an extra candidate
        // competing everywhere on cost, which is a copy rather than an index --
        // and it would let a model learned in a departure be selected in calm
        // flight purely because its numbers happened to fit the target.
        //
        // Absent-inert twice over: with no surprise index the episode publishes
        // no ordinal, so `current` is 0, no model carries a `shape_ordinal`,
        // and every model is eligible exactly as before.
        let current = ep("current_surprise_ordinal");
        for row in models.iter_mut() {
            if row.shape_ordinal > 0.0 && row.shape_ordinal != current {
                row.eligible = false;
            }
        }

        // baseline_prediction per key (uses the precomputed predictions of
        // low-activation experienced models — plan-independent).
        let mut baseline = [0.0; N_KEYS];
        {
            let refs: Vec<&ModelRow> = model_nodes
                .iter()
                .enumerate()
                .filter(|(_, node)| {
                    fattr(graph, interner, **node, "activation_magnitude") < 0.5
                        && fattr(graph, interner, **node, "experience_count") > 0.5
                })
                .map(|(i, _)| &models[i])
                .collect();
            if !refs.is_empty() {
                for ki in 0..N_KEYS {
                    baseline[ki] =
                        refs.iter().map(|row| row.prediction[ki]).sum::<f64>() / refs.len() as f64;
                }
            }
        }

        let mut targets = [0.0; 7];
        let mut weights = [0.0; 7];
        for (ci, key) in COMPONENTS.iter().enumerate() {
            targets[ci] = ep(&format!("target_{key}"));
            weights[ci] = po(&format!("{key}_weight"));
        }
        let mut safe_loads = [0.0; N_LOADS];
        let mut current_loads = [0.0; N_LOADS];
        for (li, load) in STRUCTURAL_LOADS.iter().enumerate() {
            safe_loads[li] = ep(&format!("state_safe_{load}"));
            current_loads[li] = ep(&format!("state_current_{load}")).abs();
        }
        Composer {
            graph,
            interner,
            episode,
            policy,
            models,
            baseline,
            targets,
            weights,
            drag_weight: po("drag_weight"),
            energy_weight: po("energy_weight"),
            activation_weight: po("activation_weight"),
            margin_actions: ep("margin_actions"),
            margin_reference_actions: po("margin_reference_actions"),
            margin_weight: po("margin_weight"),
            attribution_weight: po("attribution_weight"),
            attribution_reference_actions: po("attribution_reference_actions"),
            request_seq: ep("program_request_seq"),
            current_surprise_ordinal: ep("current_surprise_ordinal"),
            minimum_improvement: po("minimum_composition_improvement"),
            limits_enabled: ep("structural_limits_enabled") > 0.5,
            authority_escape: ep("authority_escape_mode") > 0.5,
            interrupt_required: ep("structural_interrupt_required") > 0.5,
            safe_loads,
            current_loads,
        }
    }

    /// structural_model_admissible (model-level, for the singleton open).
    fn model_admissible(&self, mi: usize) -> bool {
        if !self.limits_enabled {
            return true;
        }
        let row = &self.models[mi];
        let within = (0..N_LOADS).all(|li| {
            self.safe_loads[li] > 0.0
                && !(self.current_loads[li] + row.structural[li] > self.safe_loads[li])
        });
        if within {
            return true;
        }
        self.interrupt_required && (0..N_LOADS).all(|li| !(row.structural[li] > 0.0))
    }

    /// structural_program_admissible (plan-level, for expansion).
    fn program_admissible(&self, plan: &[usize], addition: usize) -> bool {
        if !self.limits_enabled {
            return true;
        }
        if self.authority_escape {
            return true;
        }
        (0..N_LOADS).all(|li| {
            if !(self.safe_loads[li] > 0.0) {
                return false;
            }
            let mut predicted = self.current_loads[li];
            for mi in plan {
                predicted += self.models[*mi].structural[li];
            }
            predicted += self.models[addition].structural[li];
            !(predicted > self.safe_loads[li])
        })
    }

    /// prediction(plan, key, addition) over the precomputed matrix.
    fn prediction(&self, plan: &[usize], ki: usize, addition: Option<usize>) -> f64 {
        let mut value = self.baseline[ki];
        for mi in plan {
            value += self.models[*mi].prediction[ki] - self.baseline[ki];
        }
        if let Some(ai) = addition {
            value += self.models[ai].prediction[ki] - self.baseline[ki];
        }
        value
    }

    /// THE PRICE OF TIME.  What `program_cost` could not say until now.
    ///
    /// Every other term in the cost prices the STATE a program produces: how
    /// close to the goal, how much drag, how much energy, how much authority
    /// it spends.  None of them can say "take this one because it buys more
    /// time", so a candidate that was worse on the goal but extended the
    /// margin could never win, no matter how short the margin got.  That is
    /// the whole gap: a reflex buys time, and the composer had no way to spend
    /// it.
    ///
    /// The shape is a RATIO, and deliberately not a linear ramp.  Urgency is
    /// `reference / margin`, so it is ~0 when the budget is long and grows
    /// without bound as the budget closes -- a hyperbola in time-to-go, which
    /// is the actual shape of "it is closing in".  A linear penalty would
    /// price the last ten actions the same as the first ten, and the last ten
    /// are the only ones that matter.
    ///
    /// The derivative used is the VERTICAL rate: climbing buys terrain
    /// margin, sinking spends it.  Stated plainly because it is an
    /// approximation -- the margin is a min over ALL regions to avoid, and
    /// only the terrain region has vertical rate as its derivative.  A stall
    /// or overspeed region closes along a different axis and is not
    /// differentiated here.
    ///
    /// ABSENCE IS DECIDED BY THE POLICY, NOT BY THE MARGIN.  Measured: on
    /// `damaged_wing` the margin reaches 0 -- no actions of budget left -- and
    /// a guard of `margin_actions > 0` reads that identically to "no margin
    /// published", switching the term OFF at exactly the moment it exists for.
    /// So the faculty is gated on the POLICY declaring it (`margin_weight`,
    /// `margin_reference_actions`), and the EPISODE only supplies the value.
    /// An agent that declares neither prices what it always priced.
    ///
    /// THERE IS NO MARGIN OF ZERO.  If the margin is zero it is too late, and
    /// that is a different STATE, not a larger weight.  An earlier version of
    /// this floored the divisor at one action so that zero became maximum
    /// urgency; that is a category error.  Urgency prices how to SPEND a
    /// budget, and at zero there is no budget to spend -- what answers there
    /// is the escape path (`authority_escape` / `f16_propose_viability_escape`,
    /// reached through viability rung 0), not a bigger number in the cost.
    /// Pricing it would also be actively harmful: it would let the composer
    /// keep choosing between programs at the exact moment its job is to stop
    /// choosing and go.
    ///
    /// So the term's domain is a STRICTLY POSITIVE margin, and absence is
    /// decided one level up, by the policy.
    fn urgency(&self) -> Option<f64> {
        if !(self.margin_weight > 0.0) || !(self.margin_reference_actions > 0.0) {
            return None;
        }
        if !(self.margin_actions > 0.0) {
            return None;
        }
        Some(self.margin_reference_actions / self.margin_actions)
    }

    fn margin_price(&self, plan: &[usize], addition: Option<usize>) -> f64 {
        let Some(urgency) = self.urgency() else {
            return 0.0;
        };
        let vertical = self.prediction(plan, key_index("vertical"), addition);
        -self.margin_weight * urgency * vertical
    }

    /// The singleton form: one model, no plan.
    fn margin_price_single(&self, mi: usize) -> f64 {
        let Some(urgency) = self.urgency() else {
            return 0.0;
        };
        -self.margin_weight * urgency * self.models[mi].prediction[key_index("vertical")]
    }

    /// program_cost(plan, addition).
    fn program_cost(&self, plan: &[usize], addition: Option<usize>) -> f64 {
        let mut cost = 0.0;
        for ci in 0..7 {
            let residual = self.targets[ci] - self.prediction(plan, ci, addition);
            cost += self.weights[ci] * residual * residual;
        }
        cost += self.drag_weight * self.prediction(plan, key_index("drag"), addition);
        cost += self.energy_weight * self.prediction(plan, key_index("energy"), addition);
        let mut activation = 0.0;
        let mut negative_log_authority = 0.0;
        for mi in plan {
            activation += self.models[*mi].activation_magnitude;
            negative_log_authority -= self.models[*mi].log_authority;
        }
        if let Some(ai) = addition {
            activation += self.models[ai].activation_magnitude;
            negative_log_authority -= self.models[ai].log_authority;
        }
        cost + self.activation_weight * activation
            + self.activation_weight * negative_log_authority
            + self.margin_price(plan, addition)
    }

    /// THE PRICE OF NOT KNOWING A MEMBER.
    ///
    /// MEASURED, and this term exists because of the number rather than the
    /// theory.  On damaged_wing the loop spends 319 of 1000 actions commanding
    /// a single effector alone -- a huge attribution budget -- and after
    /// action 250 all 231 of those go to ONE member, 100% of the late budget.
    /// The consequence is that 36 of 37 effector models are frozen at
    /// `experience_count` 201 for the last 750 actions, which is the entire
    /// departure. The budget is not missing; it is spent on the member that
    /// already knows the most.
    ///
    /// WHY IT BELONGS IN THE COST rather than in a scheduler.  The singleton
    /// open picks whichever member minimises `singleton_cost`, the state
    /// barely moves, so the same member wins every time. That is the
    /// convergence BV part 1 named: "a composer that settles on one program is
    /// efficient and unobservable -- it stops generating the variation its own
    /// learners need". Pricing staleness here fixes both halves at once,
    /// because rotating the primary IS composition variation. A separate
    /// scheduler would impose exercise from outside and leave the cost still
    /// preferring the same member.
    ///
    /// The shape is a RATIO, like the margin, for the same reason: a member
    /// unexercised for ten windows is worth ten times more than one unexercised
    /// for one, and a linear offset would price them the same. Absence reads 0,
    /// so a never-exercised member is maximally stale -- never measured is most
    /// worth measuring.
    fn attribution_price(&self, mi: usize) -> f64 {
        if !(self.attribution_weight > 0.0) || !(self.attribution_reference_actions > 0.0) {
            return 0.0;
        }
        let stale = (self.request_seq - self.models[mi].last_singleton_exercise_seq).max(0.0);
        -self.attribution_weight * (stale / self.attribution_reference_actions)
    }

    /// singleton_cost(candidate).
    fn singleton_cost(&self, mi: usize) -> f64 {
        let row = &self.models[mi];
        let mut cost = 0.0;
        for ci in 0..7 {
            let residual = self.targets[ci] - row.prediction[ci];
            cost += self.weights[ci] * residual * residual;
        }
        cost += self.drag_weight * row.prediction[key_index("drag")];
        cost += self.energy_weight * row.prediction[key_index("energy")];
        cost + self.activation_weight * row.activation_magnitude
            + self.activation_weight * (-row.log_authority)
            + self.margin_price_single(mi)
            + self.attribution_price(mi)
    }

    /// The gate is deliberately outside the legacy search.  When it is off,
    /// or while bounds are still being established, execution enters the old
    /// method without even evaluating a projection.  That makes gate-off an
    /// identity control rather than merely an intended equivalence.
    fn manifold_gate_active(&self) -> bool {
        fattr(
            self.graph,
            self.interner,
            self.policy,
            "future_manifold_enabled",
        ) > 0.5
            && fattr(
                self.graph,
                self.interner,
                self.episode,
                "manifold_bounds_ready",
            ) > 0.5
    }

    fn manifold_report(&self, plan: &[usize]) -> (bool, bool, f64, f64) {
        let members: Vec<NodeID> = plan.iter().map(|mi| self.models[*mi].node).collect();
        let report = future_manifold_projection_for_members(
            self.graph,
            self.interner,
            self.episode,
            self.policy,
            &members,
            false,
        );
        (
            report.support,
            report.resolved,
            report.loss,
            report.information_loss,
        )
    }

    /// Existing open → snapshot-parallel expansion rounds → close.
    /// Kept as a separate method so the disabled gate cannot perturb it.
    fn compose_legacy(&self) -> Vec<usize> {
        let mut best: Option<(usize, f64)> = None;
        for mi in 0..self.models.len() {
            if self.models[mi].eligible && self.model_admissible(mi) {
                let cost = self.singleton_cost(mi);
                if best.map_or(true, |(_, c)| cost < c) {
                    best = Some((mi, cost));
                }
            }
        }
        let Some((primary, _)) = best else {
            return Vec::new();
        };
        let mut plan = vec![primary];
        loop {
            let plan_cost = self.program_cost(&plan, None);
            let groups_in_plan: Vec<f64> = plan.iter().map(|mi| self.models[*mi].group).collect();
            let mut winners: Vec<(f64, usize, f64)> = Vec::new();
            for mi in 0..self.models.len() {
                let group = self.models[mi].group;
                if groups_in_plan.iter().any(|g| *g == group) {
                    continue;
                }
                if !(self.models[mi].eligible && self.program_admissible(&plan, mi)) {
                    continue;
                }
                let cost = self.program_cost(&plan, Some(mi));
                match winners.iter_mut().find(|(g, _, _)| *g == group) {
                    Some(entry) => {
                        if cost < entry.2 {
                            entry.1 = mi;
                            entry.2 = cost;
                        }
                    }
                    None => winners.push((group, mi, cost)),
                }
            }
            let mut grew = false;
            for (_, mi, cost) in winners {
                if cost + self.minimum_improvement < plan_cost {
                    plan.push(mi);
                    grew = true;
                }
            }
            if !grew {
                break;
            }
        }
        plan
    }

    /// Shape-first native composition over complete proposed plans.  A
    /// projection is never run on an isolated membership binding: every call
    /// receives the complete singleton or compound plan that could be
    /// published.  Supported/resolved plans are ordered by preserved future
    /// topology before the existing motor cost; stable model order supplies
    /// the final deterministic tie break.
    fn compose_manifold(&self) -> Vec<usize> {
        let mut best: Option<(usize, f64, f64, f64)> = None;
        for mi in 0..self.models.len() {
            if !(self.models[mi].eligible && self.model_admissible(mi)) {
                continue;
            }
            let (support, resolved, loss, information_loss) = self.manifold_report(&[mi]);
            if !(support && resolved) {
                continue;
            }
            let cost = self.singleton_cost(mi);
            let improves = best.map_or(true, |(_, bi, bl, bc)| {
                (information_loss, loss, cost) < (bi, bl, bc)
            });
            if improves {
                best = Some((mi, information_loss, loss, cost));
            }
        }
        let Some((primary, mut current_information_loss, mut current_loss, _)) = best else {
            return Vec::new();
        };
        let mut plan = vec![primary];

        loop {
            let plan_cost = self.program_cost(&plan, None);
            let groups_in_plan: Vec<f64> = plan.iter().map(|mi| self.models[*mi].group).collect();
            let mut best_addition: Option<(usize, f64, f64, f64)> = None;
            for mi in 0..self.models.len() {
                if groups_in_plan.iter().any(|g| *g == self.models[mi].group)
                    || !(self.models[mi].eligible && self.program_admissible(&plan, mi))
                {
                    continue;
                }
                let mut proposed = plan.clone();
                proposed.push(mi);
                let (support, resolved, loss, information_loss) = self.manifold_report(&proposed);
                let cost = self.program_cost(&plan, Some(mi));
                if !(support && resolved)
                    || !((information_loss, loss) <= (current_information_loss, current_loss))
                    || !(cost + self.minimum_improvement < plan_cost)
                {
                    continue;
                }
                let improves = best_addition.map_or(true, |(_, bi, bl, bc)| {
                    (information_loss, loss, cost) < (bi, bl, bc)
                });
                if improves {
                    best_addition = Some((mi, information_loss, loss, cost));
                }
            }
            let Some((mi, information_loss, loss, _)) = best_addition else {
                break;
            };
            plan.push(mi);
            current_information_loss = information_loss;
            current_loss = loss;
        }
        plan
    }

    fn compose(&self) -> Vec<usize> {
        if self.manifold_gate_active() {
            self.compose_manifold()
        } else {
            self.compose_legacy()
        }
    }
}

// The humanoid cortex predates the morphology-neutral effector schema, but it
// performs the same operation: start from a support-local primitive and grow a
// cross-actuator program while forward synthesis strictly improves.  Keeping
// this second schema behind MotorCompose avoids restoring a second interpreted
// System-2 engine merely because its learned consequences have humanoid names.
const HUMANOID_KEYS: [&str; 7] = ["dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz"];

#[derive(Clone)]
struct HumanoidModel {
    node: NodeID,
    token: Option<Sym>,
    group: f64,
    support_phase: f64,
    context_id: f64,
    initialized: bool,
    active: bool,
    exafferent: bool,
    exafferent_scale: f64,
    input_energy_joules: f64,
    effect: [f64; 7],
    /// translation_per_joule of the EmbodiedEffectorCapability node attached
    /// to this model that matches the episode's CURRENT (coupling, vertical)
    /// regime, gated on experience_count > 0.  None when no such evidence
    /// exists yet -- the presence test that keeps the cost-of-transport
    /// residual inert until the agent has actually demonstrated an authority
    /// (never fabricated from a missing-attr default).
    capability_translation_per_joule: Option<f64>,
}

struct HumanoidSynergy {
    token_a: Option<Sym>,
    token_b: Option<Sym>,
    ordinal: f64,
    approved: bool,
    experience_count: f64,
    residual: [f64; 7],
}

/// Per-term cost decomposition of the LAST fully-evaluated humanoid plan.
///
/// Observability only -- the same category as `Counters`, not agent state:
/// nothing reads it back into a decision, and the cost sum is byte-identical
/// with or without it.  `HumanoidComposer::cost` writes every candidate it
/// scores, so the value is only meaningful when the caller re-scores the
/// SELECTED plan last, which `compose` does deliberately before returning.
///
/// Why this exists: `CONTACT_WRENCH_PREREG.md` registered "report per-term
/// contributions; a measure with one live component has replaced one category
/// with another", and rung 3 then changed behaviour drastically by adding ONE
/// of these nine without any way to see which of the nine was deciding.
thread_local! {
    static LAST_COST_TERMS: std::cell::RefCell<[f64; 9]> =
        const { std::cell::RefCell::new([0.0; 9]) };
}

/// Names of the nine, in the order `HumanoidComposer::cost` emits them.
pub const HUMANOID_COST_TERM_NAMES: [&str; 9] = [
    "posture_zx",
    "posture_zy",
    "forward",
    "lateral_error",
    "lateral_position",
    "takeoff",
    "takeoff_compression",
    "support_preview",
    "cost_of_transport",
];

/// The nine components of the last plan scored on this thread.
pub fn last_humanoid_cost_terms() -> [f64; 9] {
    LAST_COST_TERMS.with(|slot| *slot.borrow())
}

struct HumanoidComposer<'a> {
    graph: &'a TypedGraph,
    interner: &'a Interner,
    episode: NodeID,
    policy: NodeID,
    models: Vec<HumanoidModel>,
    synergies: Vec<HumanoidSynergy>,
    basin_members: Vec<NodeID>,
}

#[derive(Clone)]
struct HumanoidCache {
    graph_address: usize,
    episode: NodeID,
    policy: NodeID,
    input_signature: u64,
    request_seq: u64,
    state_seq: u64,
    primary_token: Option<Sym>,
    primary_context: u64,
    takeoff_drive: u64,
    takeoff_compression_scale: u64,
    takeoff_compression_authority: u64,
    expansion_allowed: bool,
    basin_members: Vec<NodeID>,
    model_count: usize,
    members: Vec<NodeID>,
}

#[derive(Clone)]
struct EmbodiedComposeCache {
    graph_address: usize,
    episode: NodeID,
    policy: NodeID,
    request_seq: u64,
    state_seq: u64,
    manifold_enabled: u64,
    bounds_ready: u64,
    model_count: usize,
    members: Vec<NodeID>,
}

/// Current (coupling, vertical) regime for the episode, matching the
/// EmbodiedEffectorCapability seed's own conventions exactly
/// (scripts/gen_embodied_motor_priors_seed.py::open_effector_capability_rule
/// / learn_effector_capability_rule use `pre_contact_force_newtons` /
/// `pre_vz` on a per-trial outcome; the composer reads the live episode
/// state the boundary now publishes each tick, `state_contact_force_newtons`
/// / `state_vz`).
fn current_effector_regime(graph: &TypedGraph, interner: &Interner, episode: NodeID) -> (f64, f64) {
    let coupling = if fattr(graph, interner, episode, "state_contact_force_newtons") > 0.0 {
        1.0
    } else {
        0.0
    };
    let vz = fattr(graph, interner, episode, "state_vz");
    let vertical = if vz > 0.0 {
        1.0
    } else if vz < 0.0 {
        -1.0
    } else {
        0.0
    };
    (coupling, vertical)
}

/// translation_per_joule of the regime-matching EmbodiedEffectorCapability
/// attached to `model_node`, or None when no such DEMONSTRATED authority
/// exists.  Presence is tested on the existence of the neighbour node
/// itself (never on a value read via the attr-or-zero default), so an
/// absent capability and a genuinely-zero rate are never confused.
fn matched_capability_translation_per_joule(
    graph: &TypedGraph,
    interner: &Interner,
    model_node: NodeID,
    coupling_regime: f64,
    vertical_regime: f64,
) -> Option<f64> {
    let cap_edge = interner.lookup("has_embodied_effector_capability")?;
    for capability in graph.neighbours(model_node, Some(cap_edge)) {
        if fattr(graph, interner, capability, "coupling_regime") == coupling_regime
            && fattr(graph, interner, capability, "vertical_regime") == vertical_regime
        {
            if fattr(graph, interner, capability, "experience_count") > 0.0 {
                return Some(fattr(graph, interner, capability, "translation_per_joule"));
            }
            return None;
        }
    }
    None
}

thread_local! {
    /// MotorCompose is evaluated once per candidate binding.  A humanoid can
    /// retain hundreds of context-local phase models, while every binding in
    /// one sensor epoch asks the identical pure composition question.  Cache
    /// that answer for the epoch, not across epochs; graph learning advances
    /// state_seq/request_seq and therefore invalidates it mechanically.
    static HUMANOID_COMPOSE_CACHE: RefCell<Option<HumanoidCache>> =
        const { RefCell::new(None) };
    /// The ordinary native term is likewise bound once per candidate.  A
    /// manifold projection is materially richer than the legacy arithmetic,
    /// so compute the complete selected plan once for the immutable request
    /// snapshot and answer membership from that plan.
    static EMBODIED_COMPOSE_CACHE: RefCell<Option<EmbodiedComposeCache>> =
        const { RefCell::new(None) };
}

impl<'a> HumanoidComposer<'a> {
    fn build(
        graph: &'a TypedGraph,
        interner: &'a Interner,
        episode: NodeID,
        policy: NodeID,
        model_nodes: &[NodeID],
    ) -> Self {
        let (coupling_regime, vertical_regime) = current_effector_regime(graph, interner, episode);
        let models = model_nodes
            .iter()
            .map(|node| {
                let exafferent = fattr(graph, interner, *node, "exafferent") > 0.5;
                let scale_denominator =
                    fattr(graph, interner, *node, "counterfactual_scale_denominator");
                let exafferent_scale = if exafferent && scale_denominator > 0.0 {
                    (fattr(graph, interner, *node, "counterfactual_scale_numerator")
                        / scale_denominator)
                        .clamp(0.0, 1.0)
                } else if exafferent {
                    1.0
                } else {
                    0.0
                };
                HumanoidModel {
                    node: *node,
                    token: sattr(graph, interner, *node, "token"),
                    group: fattr(graph, interner, *node, "actuator_group"),
                    support_phase: fattr(graph, interner, *node, "support_phase"),
                    context_id: fattr(graph, interner, *node, "context_id"),
                    initialized: fattr(graph, interner, *node, "initialized") > 0.5,
                    active: false,
                    exafferent,
                    exafferent_scale,
                    input_energy_joules: fattr(graph, interner, *node, "mean_input_energy_joules"),
                    effect: std::array::from_fn(|i| {
                        fattr(
                            graph,
                            interner,
                            *node,
                            &format!("mean_{}", HUMANOID_KEYS[i]),
                        )
                    }),
                    capability_translation_per_joule: matched_capability_translation_per_joule(
                        graph,
                        interner,
                        *node,
                        coupling_regime,
                        vertical_regime,
                    ),
                }
            })
            .collect();
        let synergy_nodes = interner
            .lookup("has_humanoid_synergy_model")
            .map(|edge| graph.neighbours(episode, Some(edge)))
            .unwrap_or_default();
        let synergies = synergy_nodes
            .iter()
            .map(|node| HumanoidSynergy {
                token_a: sattr(graph, interner, *node, "token_a"),
                token_b: sattr(graph, interner, *node, "token_b"),
                ordinal: fattr(graph, interner, *node, "ordinal"),
                approved: fattr(graph, interner, *node, "approved") > 0.5,
                experience_count: fattr(graph, interner, *node, "experience_count"),
                residual: std::array::from_fn(|i| {
                    fattr(
                        graph,
                        interner,
                        *node,
                        &format!("residual_{}", HUMANOID_KEYS[i]),
                    )
                }),
            })
            .collect();
        let basin_members = active_humanoid_basin_members(graph, interner, episode);
        let mut composer = Self {
            graph,
            interner,
            episode,
            policy,
            models,
            synergies,
            basin_members,
        };
        let distances: Vec<f64> = composer
            .models
            .iter()
            .map(|model| composer.context_distance(model))
            .collect();
        let support_phase = composer.ep("current_support_phase");
        for index in 0..composer.models.len() {
            if composer.models[index].exafferent {
                composer.models[index].active = composer.models[index].initialized;
                continue;
            }
            let model = &composer.models[index];
            if !model.initialized || model.support_phase != support_phase {
                continue;
            }
            let best = composer
                .models
                .iter()
                .enumerate()
                .filter(|(_, peer)| {
                    peer.initialized
                        && peer.token == model.token
                        && peer.support_phase == model.support_phase
                })
                .min_by(|(left, _), (right, _)| {
                    distances[*left]
                        .partial_cmp(&distances[*right])
                        .unwrap_or(std::cmp::Ordering::Equal)
                })
                .map(|(peer, _)| composer.models[peer].context_id);
            composer.models[index].active = best == Some(model.context_id);
        }
        composer
    }

    fn ep(&self, key: &str) -> f64 {
        fattr(self.graph, self.interner, self.episode, key)
    }

    fn po(&self, key: &str) -> f64 {
        fattr(self.graph, self.interner, self.policy, key)
    }

    fn body_z(&self) -> (f64, f64) {
        let qx = self.ep("state_qx");
        let qy = self.ep("state_qy");
        let qz = self.ep("state_qz");
        let qw = self.ep("state_qw");
        (2.0 * (qx * qz + qy * qw), 2.0 * (qy * qz - qx * qw))
    }

    fn context_distance(&self, model: &HumanoidModel) -> f64 {
        let gravity = self.po("gravity_acceleration");
        let height = self.ep("standing_reference_z");
        let velocity_scale = (gravity * height).sqrt();
        let lookahead = (height / gravity).sqrt();
        let (zx, zy) = self.body_z();
        let errors = [
            fattr(self.graph, self.interner, model.node, "anchor_z_x") - zx,
            fattr(self.graph, self.interner, model.node, "anchor_z_y") - zy,
            lookahead
                * (fattr(self.graph, self.interner, model.node, "anchor_wx") - self.ep("state_wx")),
            lookahead
                * (fattr(self.graph, self.interner, model.node, "anchor_wy") - self.ep("state_wy")),
            (fattr(self.graph, self.interner, model.node, "anchor_vx") - self.ep("state_vx"))
                / velocity_scale,
            (fattr(self.graph, self.interner, model.node, "anchor_vy") - self.ep("state_vy"))
                / velocity_scale,
            (fattr(self.graph, self.interner, model.node, "anchor_vz") - self.ep("state_vz"))
                / velocity_scale,
            (fattr(
                self.graph,
                self.interner,
                model.node,
                "anchor_lateral_offset",
            ) - self.ep("lateral_offset"))
                / height,
        ];
        errors.iter().map(|x| x * x).sum()
    }

    fn active(&self, index: usize) -> bool {
        self.models[index].active
    }

    fn synergy(&self, left: usize, right: usize) -> Option<&HumanoidSynergy> {
        let a = self.models[left].token;
        let b = self.models[right].token;
        self.synergies
            .iter()
            .filter(|s| {
                s.approved
                    && ((s.token_a == a && s.token_b == b) || (s.token_a == b && s.token_b == a))
            })
            .min_by(|x, y| {
                x.ordinal
                    .partial_cmp(&y.ordinal)
                    .unwrap_or(std::cmp::Ordering::Equal)
            })
    }

    fn active_related_node(&self, edge: &str, ordinal_attr: &str) -> Option<NodeID> {
        let edge = self.interner.lookup(edge)?;
        let wanted = self.ep(ordinal_attr);
        self.graph
            .neighbours(self.policy, Some(edge))
            .into_iter()
            .filter(|node| fattr(self.graph, self.interner, *node, "ordinal") == wanted)
            .min_by(|a, b| {
                fattr(self.graph, self.interner, *a, "ordinal")
                    .partial_cmp(&fattr(self.graph, self.interner, *b, "ordinal"))
                    .unwrap_or(std::cmp::Ordering::Equal)
            })
    }

    fn support_center(&self, axis: &str) -> f64 {
        let p0 = self.ep("state_support_0_force") > 0.0;
        let p1 = self.ep("state_support_1_force") > 0.0;
        let a = self.ep(&format!("state_support_0_{axis}"));
        let b = self.ep(&format!("state_support_1_{axis}"));
        if p0 && !p1 {
            a
        } else if p1 && !p0 {
            b
        } else {
            (a + b) / 2.0
        }
    }

    fn viability_gate(&self, gait: Option<NodeID>) -> f64 {
        let (zx, zy) = self.body_z();
        let tilt = (zx * zx + zy * zy).sqrt();
        let tilt_budget = self
            .po("target_froude_speed")
            .max(self.ep("learned_gait_tilt_envelope"));
        let tilt_gate = (1.0 - tilt / tilt_budget).clamp(0.0, 1.0);
        let height = self.ep("standing_reference_z");
        let minimum = self.po("minimum_upright_height_fraction") * height;
        let height_gate =
            ((self.ep("state_z") - minimum) / (height - minimum).max(0.001)).clamp(0.0, 1.0);
        let grounded =
            self.ep("state_support_0_force") > 0.0 || self.ep("state_support_1_force") > 0.0;
        let flight = gait.map_or(0.0, |node| {
            fattr(self.graph, self.interner, node, "flight_phase_authority")
        }) > 0.5;
        if (grounded || flight)
            && self.ep("recovery_mode") == 0.0
            && self.ep("locomotion_drive_active") == 1.0
        {
            tilt_gate.min(height_gate)
        } else {
            0.0
        }
    }

    fn forward_cost(&self, predicted_dvx: f64, frames: f64) -> f64 {
        let height = self.ep("standing_reference_z");
        let velocity_scale = (self.po("gravity_acceleration") * height).sqrt();
        let target_velocity =
            self.ep("heading_x") * self.po("target_froude_speed") * velocity_scale;
        let instantaneous =
            (self.ep("state_vx") + predicted_dvx - target_velocity) / velocity_scale;
        if self.po("persistent_task_residual_authority") <= 0.5 {
            return instantaneous * instantaneous;
        }
        let step = self.ep("heading_x")
            * (self.ep("state_vx") + 0.5 * predicted_dvx)
            * frames
            * self.ep("physics_time_step");
        let progress = self.ep("lifetime_completed_progress") + self.ep("directed_progress") + step;
        let residual = (self.ep("target_directed_progress_m") - progress).max(0.0) / height;
        let regime = self.active_related_node(
            "has_humanoid_residual_regime",
            "active_residual_regime_ordinal",
        );
        let gait = self.active_related_node(
            "has_humanoid_gait_attractor",
            "active_gait_attractor_ordinal",
        );
        let prior = self.po("support_phase_prior_strength");
        let residual_gain = regime.map_or(0.0, |node| {
            fattr(self.graph, self.interner, node, "residual_gain_numerator")
        });
        let impulse = gait.map_or(0.0, |node| {
            fattr(self.graph, self.interner, node, "elastic_impulse_numerator")
        });
        (residual_gain / prior)
            * (1.0 + impulse / prior)
            * self.viability_gate(gait)
            * residual
            * residual
    }

    fn support_preview(&self, dvx: f64, dvy: f64) -> f64 {
        let authority = self.po("support_geometry_preview_authority");
        if authority == 0.0
            || !(self.ep("state_support_0_force") > 0.0 || self.ep("state_support_1_force") > 0.0)
        {
            return 0.0;
        }
        let height = self.ep("standing_reference_z");
        let prior = self.po("support_phase_prior_strength");
        let support_count = self.ep("support_sensor_count");
        let lookahead = (height / self.po("gravity_acceleration")).sqrt();
        let capture_x = self.ep("state_x") + lookahead * (self.ep("state_vx") + dvx);
        let capture_y = self.ep("state_y") + lookahead * (self.ep("state_vy") + dvy);
        let regime = self.active_related_node(
            "has_humanoid_residual_regime",
            "active_residual_regime_ordinal",
        );
        let viability = regime.map_or(0.0, |node| {
            fattr(self.graph, self.interner, node, "viability_scale_numerator")
        });
        let forward_margin = viability / (prior * support_count) * height;
        let lateral_margin = viability / (prior * prior) * height
            + (self.ep("state_support_0_y") - self.ep("state_support_1_y")).abs() / support_count;
        let fx = ((capture_x - self.support_center("x")).abs() - forward_margin).max(0.0) / height;
        let fy = ((capture_y - self.support_center("y")).abs() - lateral_margin).max(0.0) / height;
        authority * (support_count * fx * fx + prior * fy * fy)
    }

    fn takeoff_cost(&self, predicted_dvz: f64) -> f64 {
        if self.ep("self_takeoff_drive_active") <= 0.5 {
            return 0.0;
        }
        let height = self.ep("standing_reference_z");
        let velocity_scale = (self.po("gravity_acceleration") * height).sqrt();
        let target = self.ep("self_takeoff_target_velocity_scale") * velocity_scale
            / self.po("support_phase_prior_strength");
        let error = (self.ep("state_vz") + predicted_dvz - target) / velocity_scale;
        self.po("support_phase_prior_strength") * error * error
    }

    fn takeoff_compression_cost(&self, members: &[usize], scale: f64) -> f64 {
        if self.ep("self_takeoff_drive_active") <= 0.5 {
            return 0.0;
        }
        let authority = self.po("takeoff_motor_compression_authority")
            * self.ep("self_takeoff_compression_scale");
        if authority <= 0.0 {
            return 0.0;
        }
        let energy_scale = self.ep("body_mass")
            * self.po("gravity_acceleration")
            * self.ep("standing_reference_z");
        let normalized_energy = scale
            * members
                .iter()
                .map(|index| self.models[*index].input_energy_joules)
                .sum::<f64>()
            / energy_scale.max(f64::EPSILON);
        let mut active_groups: Vec<u64> = self
            .models
            .iter()
            .enumerate()
            .filter(|(index, _)| self.active(*index))
            .map(|(_, model)| model.group.to_bits())
            .collect();
        active_groups.sort_unstable();
        active_groups.dedup();
        let declared_group_count = self.ep("motor_effector_group_count");
        let group_count = if declared_group_count > 0.0 {
            declared_group_count
        } else {
            active_groups.len() as f64
        };
        let recruited_beyond_singleton = members.len().saturating_sub(1) as f64;
        let structural_cost = recruited_beyond_singleton
            / (group_count * self.po("support_phase_prior_strength")).max(1.0);
        authority * (normalized_energy + structural_cost)
    }

    /// A candidate composition's predicted forward translation should be
    /// consistent with what each regime-matched effector in it is KNOWN to
    /// deliver per joule.  Contributes exactly 0.0 for any member whose
    /// model carries no demonstrated (regime-matched, experienced)
    /// capability -- this term never fabricates an authority that has not
    /// been earned, so it is a true no-op on a graph (e.g. the F-16) that
    /// has never opened an EmbodiedEffectorCapability node at all.
    fn cost_of_transport_residual(
        &self,
        members: &[usize],
        predicted_dvx: f64,
        frames: f64,
        height: f64,
    ) -> f64 {
        let energy: f64 = members
            .iter()
            .map(|index| self.models[*index].input_energy_joules)
            .sum();
        let predicted_translation =
            (self.ep("state_vx") + 0.5 * predicted_dvx) * frames * self.ep("physics_time_step");
        let mut cost = 0.0;
        for index in members {
            if let Some(rate) = self.models[*index].capability_translation_per_joule {
                let capability_translation = energy * rate;
                let residual = (predicted_translation - capability_translation) / height;
                // RUNG 5 — SHORTFALL ONLY (RUNG5_ONESIDED_TRANSPORT_PREREG.md).
                //
                // Cost of transport means DO NOT WASTE ENERGY, so the error is
                // "spent energy and went nowhere", never "went further than
                // predicted". The symmetric form this replaces punished a plan
                // for outperforming its own prior exactly as hard as for
                // falling short — the F-16 arc's "the corner that gives up the
                // most wins", in algebra.
                //
                // It also disarms the bootstrap loop without any evidence
                // guard. `translation_per_joule` SEEDS AT 0.0 and is learned by
                // EMA from observed travel, so at rate 0 the symmetric form
                // charged every predicted translation as error, the body
                // declined to translate, the EMA saw no travel, and the rate
                // stayed 0 — self-confirming, and rung 3's 600 actions of
                // stepping in place is what that looks like from outside. Here
                // capability_translation is 0, predicted translation is >= 0,
                // so there is no shortfall and the term is silent until it has
                // something to say.
                if residual < 0.0 {
                    cost += residual * residual;
                }
            }
        }
        cost
    }

    fn cost(&self, plan: &[usize], addition: Option<usize>) -> f64 {
        let mut members = plan.to_vec();
        if let Some(index) = addition {
            members.push(index);
        }
        let count = members.len();
        let response_frames = self.ep("response_frames");
        let frames = if count > 1 {
            (response_frames as i64 / 2).max(1) as f64
        } else {
            response_frames
        };
        let scale = frames / response_frames;
        let mut predicted = [0.0; 7];
        for index in &members {
            for key in 0..7 {
                predicted[key] += self.models[*index].effect[key];
            }
        }
        for left in 0..members.len() {
            for right in left + 1..members.len() {
                if let Some(synergy) = self.synergy(members[left], members[right]) {
                    for key in 0..7 {
                        predicted[key] += synergy.residual[key] / scale;
                    }
                }
            }
        }
        for value in &mut predicted {
            *value *= scale;
        }
        let height = self.ep("standing_reference_z");
        let gravity = self.po("gravity_acceleration");
        let velocity_scale = (gravity * height).sqrt();
        let lookahead = (height / gravity).sqrt();
        let (zx, zy) = self.body_z();
        let predicted_zx = zx + predicted[0] + lookahead * (self.ep("state_wy") + predicted[3]);
        let predicted_zy = zy + predicted[1] - lookahead * (self.ep("state_wx") + predicted[2]);
        let lateral_target =
            -(self.ep("lateral_offset") / height) * self.po("target_froude_speed") * velocity_scale;
        let lateral_velocity = self.ep("state_vy") + predicted[5];
        let lateral_error = (lateral_velocity - lateral_target) / velocity_scale;
        let lateral_position = (self.ep("lateral_offset") + lookahead * lateral_velocity) / height;
        // THE NINE TERMS, NAMED AND KEPT SEPARATE.  `CONTACT_WRENCH_PREREG.md`
        // committed to "report per-term contributions; a measure with one live
        // component has replaced one category with another", and until now they
        // were summed on one expression and never individually visible.  The
        // sum is UNCHANGED (same operands, same order), so this is not a
        // behaviour change -- it only stops discarding the decomposition.
        let terms = [
            predicted_zx * predicted_zx,
            predicted_zy * predicted_zy,
            self.forward_cost(predicted[4], frames),
            lateral_error * lateral_error,
            lateral_position * lateral_position,
            self.takeoff_cost(predicted[6]),
            self.takeoff_compression_cost(&members, scale),
            self.support_preview(predicted[4], predicted[5]),
            self.cost_of_transport_residual(&members, predicted[4], frames, height),
        ];
        LAST_COST_TERMS.with(|slot| *slot.borrow_mut() = terms);
        terms[0]
            + terms[1]
            + terms[2]
            + terms[3]
            + terms[4]
            + terms[5]
            + terms[6]
            + terms[7]
            + terms[8]
    }

    fn expansion_allowed(&self) -> bool {
        // The open rule snapshots compound_output_permitted into the plan
        // before it increments decision_count. Reading that graph-held fact is
        // both cheaper and exactly preserves the interpreted cascade's timing.
        let Some(edge) = self.interner.lookup("has_active_humanoid_motor_program") else {
            return false;
        };
        let request_seq = self.ep("request_seq");
        self.graph
            .neighbours(self.episode, Some(edge))
            .into_iter()
            .any(|plan| {
                fattr(self.graph, self.interner, plan, "request_seq") == request_seq
                    && fattr(self.graph, self.interner, plan, "allow_expansion") == 1.0
            })
    }

    fn humanoid_manifold_gate_active(&self) -> bool {
        self.po("future_manifold_enabled") > 0.5
            && self.po("future_manifold_temporal_anchors_enabled") > 0.5
            && self.ep("manifold_bounds_ready") > 0.5
    }

    /// Temporal foveation: dense 1,2,3,4,8,16 anchors followed by the
    /// log-log far field 256,65536,... (saturating square), capped at the
    /// complete held interval.
    /// Invalid horizons are unsupported.
    fn manifold_foveated_frames(&self) -> Option<Vec<f64>> {
        let horizon = self.ep("response_frames");
        if !horizon.is_finite() || horizon < 1.0 || horizon.fract() != 0.0 {
            return None;
        }
        let horizon = horizon as u64;
        let mut frames = Vec::new();
        let mut current = 0u64;
        while current < horizon {
            let requested = match current {
                0 => 1,
                1 => 2,
                2 => 3,
                3 => 4,
                4 => 8,
                8 => 16,
                value => value.saturating_mul(value),
            };
            let next = requested.min(horizon);
            if next <= current {
                break;
            }
            frames.push(next as f64);
            current = next;
        }
        Some(frames)
    }

    fn manifold_bounds(
        &self,
        projected_frame: f64,
        caregiver_counterfactual_scale: f64,
    ) -> Option<[f64; 7]> {
        let safety = learning_safety_evidence(self.graph, self.interner, self.episode);
        let support = situation_support_field(
            self.graph,
            self.interner,
            self.episode,
            self.policy,
            projected_frame,
            true,
            caregiver_counterfactual_scale,
        );
        let mut bounds = [0.0; 7];
        for (index, key) in HUMANOID_KEYS.iter().enumerate() {
            let symbol = self.interner.lookup(&format!("manifold_bound_{key}"))?;
            let value = match self.graph.node(self.episode).attrs.get(&symbol) {
                Some(Value::Float(value)) => *value,
                Some(Value::Int(value)) => *value as f64,
                _ => return None,
            };
            if !value.is_finite() || value < 0.0 {
                return None;
            }
            bounds[index] = safety.bound(value, support.weights[index]);
        }
        Some(bounds)
    }

    fn manifold_anchor_present(&self, node: NodeID) -> bool {
        [
            "anchor_z_x",
            "anchor_z_y",
            "anchor_wx",
            "anchor_wy",
            "anchor_vx",
            "anchor_vy",
            "anchor_vz",
            "anchor_lateral_offset",
        ]
        .iter()
        .all(|key| {
            self.interner
                .lookup(key)
                .is_some_and(|symbol| self.graph.node(node).attrs.contains_key(&symbol))
        })
    }

    /// Complete held-program synthesis. Duplicate or missing synergy evidence
    /// is ambiguous and is rejected rather than converted into authority.
    fn manifold_effect(&self, members: &[usize]) -> Option<[f64; 7]> {
        self.manifold_effect_at_exafferent_scale(members, None)
    }

    /// Additively project an information-gaining program while counting every
    /// as-yet unobserved pair interaction. Conflicting duplicate evidence is
    /// still unsupported. The missing interaction is never invented as zero:
    /// its count is carried into the manifold's information-loss dimension.
    fn manifold_effect_with_unknown_pairs(&self, members: &[usize]) -> Option<([f64; 7], f64)> {
        if members.is_empty()
            || members.iter().any(|index| {
                !self.active(*index)
                    || !self.models[*index].initialized
                    || !self.manifold_anchor_present(self.models[*index].node)
                    || self.models[*index]
                        .effect
                        .iter()
                        .any(|value| !value.is_finite())
            })
        {
            return None;
        }
        let response_frames = self.ep("response_frames");
        let endogenous_count = members
            .iter()
            .filter(|index| !self.models[**index].exafferent)
            .count();
        let endogenous_scale = if endogenous_count > 1 {
            ((response_frames as i64 / 2).max(1) as f64) / response_frames
        } else {
            1.0
        };
        let mut effect = [0.0; 7];
        for index in members {
            let scale = if self.models[*index].exafferent {
                self.models[*index].exafferent_scale.clamp(0.0, 1.0)
            } else {
                endogenous_scale
            };
            for key in 0..7 {
                effect[key] += self.models[*index].effect[key] * scale;
            }
        }
        let mut unknown_pairs = 0.0;
        for left in 0..members.len() {
            for right in left + 1..members.len() {
                if self.models[members[left]].exafferent || self.models[members[right]].exafferent {
                    continue;
                }
                let a = self.models[members[left]].token;
                let b = self.models[members[right]].token;
                let matches: Vec<&HumanoidSynergy> = self
                    .synergies
                    .iter()
                    .filter(|synergy| {
                        synergy.approved
                            && ((synergy.token_a == a && synergy.token_b == b)
                                || (synergy.token_a == b && synergy.token_b == a))
                    })
                    .collect();
                match matches.as_slice() {
                    [] => unknown_pairs += 1.0,
                    [synergy] => {
                        for key in 0..7 {
                            effect[key] += synergy.residual[key];
                        }
                    }
                    _ => return None,
                }
            }
        }
        Some((effect, unknown_pairs))
    }

    fn manifold_effect_at_exafferent_scale(
        &self,
        members: &[usize],
        exafferent_scale_override: Option<f64>,
    ) -> Option<[f64; 7]> {
        self.manifold_effect_at_exafferent_scale_for_frames(
            members,
            exafferent_scale_override,
            self.ep("response_frames"),
        )
    }

    fn manifold_effect_at_exafferent_scale_for_frames(
        &self,
        members: &[usize],
        exafferent_scale_override: Option<f64>,
        response_frames: f64,
    ) -> Option<[f64; 7]> {
        self.manifold_effect_at_scales_for_frames(
            members,
            exafferent_scale_override,
            response_frames,
            1.0,
        )
    }

    fn manifold_effect_at_scales_for_frames(
        &self,
        members: &[usize],
        exafferent_scale_override: Option<f64>,
        response_frames: f64,
        recruitment_scale: f64,
    ) -> Option<[f64; 7]> {
        if members.is_empty()
            || !response_frames.is_finite()
            || response_frames < 1.0
            || response_frames.fract() != 0.0
            || !recruitment_scale.is_finite()
            || recruitment_scale < 1.0
            || members.iter().any(|index| {
                !self.active(*index)
                    || !self.models[*index].initialized
                    || !self.manifold_anchor_present(self.models[*index].node)
                    || self.models[*index].effect.iter().any(|v| !v.is_finite())
            })
        {
            return None;
        }
        let endogenous_count = members
            .iter()
            .filter(|index| !self.models[**index].exafferent)
            .count();
        let endogenous_scale = if endogenous_count > 1 {
            ((response_frames as i64 / 2).max(1) as f64) / response_frames
        } else {
            1.0
        };
        let mut effect = [0.0; 7];
        for index in members {
            // The child program's compound members share its response window.
            // Learned caregiver support is an independent environmental
            // consequence calibrated across the whole window, so adding it to
            // a counterfactual must neither shorten it nor rescale the child.
            let scale = if self.models[*index].exafferent {
                exafferent_scale_override
                    .unwrap_or(self.models[*index].exafferent_scale)
                    .clamp(0.0, 1.0)
            } else {
                endogenous_scale * recruitment_scale
            };
            for key in 0..7 {
                effect[key] += self.models[*index].effect[key] * scale;
            }
        }
        for left in 0..members.len() {
            for right in left + 1..members.len() {
                if self.models[members[left]].exafferent || self.models[members[right]].exafferent {
                    continue;
                }
                let a = self.models[members[left]].token;
                let b = self.models[members[right]].token;
                let matches: Vec<&HumanoidSynergy> = self
                    .synergies
                    .iter()
                    .filter(|s| {
                        s.approved
                            && ((s.token_a == a && s.token_b == b)
                                || (s.token_a == b && s.token_b == a))
                    })
                    .collect();
                if matches.len() != 1 {
                    return None;
                }
                for key in 0..7 {
                    effect[key] += matches[0].residual[key] * recruitment_scale * recruitment_scale;
                }
            }
        }
        Some(effect)
    }

    /// Bounds are hard; learned anchors provide the local refinement score.
    /// The held phase effect is a linear span, so endpoint magnitude certifies
    /// all intervening fractions. This deliberately claims no order
    /// escalation or higher-order authority.
    fn manifold_path(&self, members: &[usize]) -> Option<(f64, f64, [f64; 7], f64)> {
        self.manifold_path_at_exafferent_scale(members, None)
    }

    fn manifold_path_at_exafferent_scale(
        &self,
        members: &[usize],
        exafferent_scale_override: Option<f64>,
    ) -> Option<(f64, f64, [f64; 7], f64)> {
        self.manifold_path_at_scales(members, exafferent_scale_override, 1.0)
    }

    fn manifold_path_at_recruitment_scale(
        &self,
        members: &[usize],
        recruitment_scale: f64,
    ) -> Option<(f64, f64, [f64; 7], f64)> {
        self.manifold_path_at_scales(members, None, recruitment_scale)
    }

    /// Return the greatest recruitment on the connected admissible interval
    /// from normal effort to `upper`.  The learned held-program response is
    /// exactly linear-plus-quadratic in uniform recruitment, so every first
    /// shape-bound intersection is solved analytically rather than approached
    /// with a fixed increment or iteration count.
    fn maximum_admissible_recruitment_scale(&self, members: &[usize], upper: f64) -> Option<f64> {
        if !upper.is_finite() || upper < 1.0 {
            return None;
        }
        if !self
            .manifold_path_at_recruitment_scale(members, 1.0)
            .is_some_and(|(loss, escaped, _, _)| escaped == 0.0 && loss.is_finite())
        {
            return Some(1.0);
        }
        let unit = self.manifold_effect_at_scales_for_frames(
            members,
            None,
            self.ep("response_frames"),
            1.0,
        )?;
        let doubled = self.manifold_effect_at_scales_for_frames(
            members,
            None,
            self.ep("response_frames"),
            2.0,
        )?;
        let frames = self.manifold_foveated_frames()?;
        let horizon = *frames.last()?;
        let mut boundary = upper;
        for frame in frames {
            let fraction = frame / horizon;
            let bounds = self.manifold_bounds(frame, 0.0)?;
            for key in 0..7 {
                let quadratic = (doubled[key] - 2.0 * unit[key]) / 2.0;
                let linear = unit[key] - quadratic;
                let limit = bounds[key] / fraction;
                for target in [limit, -limit] {
                    if quadratic == 0.0 {
                        if linear != 0.0 {
                            let root = target / linear;
                            if root > 1.0 && root < boundary {
                                boundary = root;
                            }
                        }
                        continue;
                    }
                    let discriminant = linear * linear + 4.0 * quadratic * target;
                    if discriminant < 0.0 {
                        continue;
                    }
                    let root = discriminant.sqrt();
                    for candidate in [
                        (-linear - root) / (2.0 * quadratic),
                        (-linear + root) / (2.0 * quadratic),
                    ] {
                        if candidate > 1.0 && candidate < boundary {
                            boundary = candidate;
                        }
                    }
                }
            }
        }
        if self
            .manifold_path_at_recruitment_scale(members, boundary)
            .is_some_and(|(loss, escaped, _, _)| escaped == 0.0 && loss.is_finite())
        {
            return Some(boundary);
        }
        // An analytic boundary can round one representable value outside.
        // Move by exactly one ULP toward normal effort and fail closed if that
        // value is not admissible either.
        let interior = f64::from_bits(boundary.to_bits().saturating_sub(1));
        self.manifold_path_at_recruitment_scale(members, interior)
            .is_some_and(|(loss, escaped, _, _)| escaped == 0.0 && loss.is_finite())
            .then_some(interior)
    }

    fn manifold_path_at_scales(
        &self,
        members: &[usize],
        exafferent_scale_override: Option<f64>,
        recruitment_scale: f64,
    ) -> Option<(f64, f64, [f64; 7], f64)> {
        let frames = self.manifold_foveated_frames()?;
        let effect = self.manifold_effect_at_scales_for_frames(
            members,
            exafferent_scale_override,
            self.ep("response_frames"),
            recruitment_scale,
        )?;
        let caregiver_counterfactual_scale = exafferent_scale_override.unwrap_or_else(|| {
            members
                .iter()
                .filter(|index| self.models[**index].exafferent)
                .map(|index| self.models[*index].exafferent_scale)
                .fold(0.0, f64::max)
        });
        let horizon = *frames.last()?;
        let mut anchor_loss = 0.0;
        for frame in frames {
            let bounds = self.manifold_bounds(frame, caregiver_counterfactual_scale)?;
            let fraction = frame / horizon;
            let mut residual = [0.0; 7];
            for key in 0..7 {
                let projected = fraction * effect[key];
                let excess = projected.abs() - bounds[key];
                if excess > 0.0 {
                    residual[key] = projected.signum() * excess;
                }
            }
            let escaped = residual.iter().filter(|value| **value != 0.0).count() as f64;
            if escaped > 0.0 {
                return Some((f64::INFINITY, escaped, residual, frame));
            }
            for member in members {
                let model = &self.models[*member];
                let anchor = [
                    fattr(self.graph, self.interner, model.node, "anchor_z_x"),
                    fattr(self.graph, self.interner, model.node, "anchor_z_y"),
                    fattr(self.graph, self.interner, model.node, "anchor_wx"),
                    fattr(self.graph, self.interner, model.node, "anchor_wy"),
                    fattr(self.graph, self.interner, model.node, "anchor_vx"),
                    fattr(self.graph, self.interner, model.node, "anchor_vy"),
                    fattr(self.graph, self.interner, model.node, "anchor_vz"),
                    fattr(
                        self.graph,
                        self.interner,
                        model.node,
                        "anchor_lateral_offset",
                    ),
                ];
                let projected = [
                    fraction * effect[0],
                    fraction * effect[1],
                    fraction * effect[3],
                    fraction * effect[2],
                    fraction * effect[4],
                    fraction * effect[5],
                    fraction * effect[6],
                    fraction * effect[5],
                ];
                for component in 0..8 {
                    let residual = projected[component] - anchor[component];
                    anchor_loss += residual * residual;
                }
            }
        }
        Some((anchor_loss, 0.0, [0.0; 7], 0.0))
    }

    /// Project a compound from its own receipt-grounded whole-program model.
    /// Once the complete action has been physically observed, decomposing it
    /// back into members would discard the measured nonlinear interaction and
    /// incorrectly recreate unknown-pair information loss.
    fn manifold_path_for_observed_effect(
        &self,
        members: &[usize],
        effect: [f64; 7],
    ) -> Option<(f64, f64, [f64; 7], f64)> {
        if members.is_empty() || effect.iter().any(|value| !value.is_finite()) {
            return None;
        }
        let frames = self.manifold_foveated_frames()?;
        let caregiver_scale = members
            .iter()
            .filter(|index| self.models[**index].exafferent)
            .map(|index| self.models[*index].exafferent_scale)
            .fold(0.0, f64::max);
        let horizon = *frames.last()?;
        let mut anchor_loss = 0.0;
        for frame in frames {
            let bounds = self.manifold_bounds(frame, caregiver_scale)?;
            let fraction = frame / horizon;
            let mut residual = [0.0; 7];
            for key in 0..7 {
                let projected = fraction * effect[key];
                let excess = projected.abs() - bounds[key];
                if excess > 0.0 {
                    residual[key] = projected.signum() * excess;
                }
            }
            let escaped = residual.iter().filter(|value| **value != 0.0).count() as f64;
            if escaped > 0.0 {
                return Some((f64::INFINITY, escaped, residual, frame));
            }
            for member in members {
                let model = &self.models[*member];
                let anchor = [
                    fattr(self.graph, self.interner, model.node, "anchor_z_x"),
                    fattr(self.graph, self.interner, model.node, "anchor_z_y"),
                    fattr(self.graph, self.interner, model.node, "anchor_wx"),
                    fattr(self.graph, self.interner, model.node, "anchor_wy"),
                    fattr(self.graph, self.interner, model.node, "anchor_vx"),
                    fattr(self.graph, self.interner, model.node, "anchor_vy"),
                    fattr(self.graph, self.interner, model.node, "anchor_vz"),
                    fattr(
                        self.graph,
                        self.interner,
                        model.node,
                        "anchor_lateral_offset",
                    ),
                ];
                let projected = [
                    fraction * effect[0],
                    fraction * effect[1],
                    fraction * effect[3],
                    fraction * effect[2],
                    fraction * effect[4],
                    fraction * effect[5],
                    fraction * effect[6],
                    fraction * effect[5],
                ];
                for component in 0..8 {
                    let delta = projected[component] - anchor[component];
                    anchor_loss += delta * delta;
                }
            }
        }
        Some((anchor_loss, 0.0, [0.0; 7], 0.0))
    }

    fn manifold_path_with_unknown_pairs(
        &self,
        members: &[usize],
    ) -> Option<(f64, f64, [f64; 7], f64, f64)> {
        let frames = self.manifold_foveated_frames()?;
        let (effect, unknown_pairs) = self.manifold_effect_with_unknown_pairs(members)?;
        if unknown_pairs <= 0.0 {
            return None;
        }
        let caregiver_scale = members
            .iter()
            .filter(|index| self.models[**index].exafferent)
            .map(|index| self.models[*index].exafferent_scale)
            .fold(0.0, f64::max);
        let horizon = *frames.last()?;
        let mut anchor_loss = 0.0;
        for frame in frames {
            let bounds = self.manifold_bounds(frame, caregiver_scale)?;
            let fraction = frame / horizon;
            let mut residual = [0.0; 7];
            for key in 0..7 {
                let projected = fraction * effect[key];
                let excess = projected.abs() - bounds[key];
                if excess > 0.0 {
                    residual[key] = projected.signum() * excess;
                }
            }
            let escaped = residual.iter().filter(|value| **value != 0.0).count() as f64;
            if escaped > 0.0 {
                return Some((f64::INFINITY, escaped, residual, frame, unknown_pairs));
            }
            for member in members {
                let model = &self.models[*member];
                let anchors = [
                    "anchor_z_x",
                    "anchor_z_y",
                    "anchor_wx",
                    "anchor_wy",
                    "anchor_vx",
                    "anchor_vy",
                    "anchor_vz",
                    "anchor_lateral_offset",
                ];
                let projected = [
                    fraction * effect[0],
                    fraction * effect[1],
                    fraction * effect[3],
                    fraction * effect[2],
                    fraction * effect[4],
                    fraction * effect[5],
                    fraction * effect[6],
                    fraction * effect[5],
                ];
                for component in 0..8 {
                    let delta = projected[component]
                        - fattr(self.graph, self.interner, model.node, anchors[component]);
                    anchor_loss += delta * delta;
                }
            }
        }
        Some((anchor_loss, 0.0, [0.0; 7], 0.0, unknown_pairs))
    }

    fn compose_manifold(&self) -> Vec<usize> {
        let token = sattr(
            self.graph,
            self.interner,
            self.episode,
            "selected_primary_token",
        );
        let context = self.ep("selected_primary_context_id");
        let mut viable: Vec<(usize, f64, f64)> = self
            .models
            .iter()
            .enumerate()
            .filter(|(index, model)| {
                self.active(*index) && model.token == token && model.context_id == context
            })
            .filter_map(|(index, _)| {
                let (anchor_loss, escaped, _, _) = self.manifold_path(&[index])?;
                (escaped == 0.0 && anchor_loss.is_finite()).then_some((
                    index,
                    anchor_loss,
                    self.cost(&[index], None),
                ))
            })
            .collect();
        viable.sort_by(|a, b| {
            (a.1, a.2, a.0)
                .partial_cmp(&(b.1, b.2, b.0))
                .unwrap_or(std::cmp::Ordering::Equal)
        });
        let Some((primary, _, _)) = viable.first().copied() else {
            return Vec::new();
        };
        // Establishing a future manifold does not imply zero momentum. Grow
        // the ordinary analysis-by-synthesis program while each complete
        // candidate remains inside the projected manifold and improves the
        // task cost. This recovers a situated normal-effort action without
        // trading any future bound against a scalar task reward.
        let mut plan = vec![primary];
        loop {
            let current_cost = self.cost(&plan, None);
            let mut best: Option<(usize, f64, f64)> = None;
            for index in 0..self.models.len() {
                if plan.contains(&index)
                    || !self.active(index)
                    || plan
                        .iter()
                        .any(|member| self.models[*member].group == self.models[index].group)
                {
                    continue;
                }
                let mut candidate_plan = plan.clone();
                candidate_plan.push(index);
                let Some((anchor_loss, escaped, _, _)) = self.manifold_path(&candidate_plan) else {
                    continue;
                };
                if escaped > 0.0 || !anchor_loss.is_finite() {
                    continue;
                }
                let cost = self.cost(&candidate_plan, None);
                if !(cost < current_cost) {
                    continue;
                }
                if best.map_or(true, |old| {
                    (cost, anchor_loss, index) < (old.1, old.2, old.0)
                }) {
                    best = Some((index, cost, anchor_loss));
                }
            }
            let Some((candidate, _, _)) = best else {
                break;
            };
            plan.push(candidate);
        }

        // Persistent supported learning may need to cross a locally flat
        // composition surface: no single extra effector improves the task,
        // while a receipt-modelled higher-order assembly does.  Project only
        // as far as failed evidence asks, and commit one member of a rollout
        // only when the complete projected assembly improves on the current
        // normal-effort program.  This preserves meaningful exploration
        // without treating target order itself as output authority.
        let target_order = self.takeoff_exploration_target_order();

        // Compress epistemic width one identifiable relation at a time.  A
        // two-member receipt has exactly one interaction residual, whereas a
        // wider novel mixture cannot assign its error without inventing
        // credit.  Supported learning may therefore spend effort on one
        // previously unseen pair; once observed, its information gain is zero
        // and another relation (or ordinary task action) must win.
        let safety = learning_safety_evidence(self.graph, self.interner, self.episode);
        if plan.len() == 1 && target_order > 1 && safety.active() {
            let primary = plan[0];
            let mut epistemic: Option<(usize, f64)> = None;
            for index in 0..self.models.len() {
                if !self.admissible_new_member(&plan, index) {
                    continue;
                }
                let Some(synergy) = self.synergy(primary, index) else {
                    continue;
                };
                if synergy.experience_count > 0.0 {
                    continue;
                }
                let mut candidate = plan.clone();
                candidate.push(index);
                if !self.manifold_program_admissible(&candidate) {
                    continue;
                }
                let cost = self.cost(&candidate, None);
                if epistemic.map_or(true, |old| (cost, index) < (old.1, old.0)) {
                    epistemic = Some((index, cost));
                }
            }
            if let Some((candidate, _)) = epistemic {
                plan.push(candidate);
            }
        }

        while plan.len() < target_order {
            let current_cost = self.cost(&plan, None);
            let mut best_rollout: Option<(usize, f64)> = None;
            for first in 0..self.models.len() {
                if !self.admissible_new_member(&plan, first) {
                    continue;
                }
                let mut rollout = plan.clone();
                rollout.push(first);
                if !self.manifold_program_admissible(&rollout)
                    || !self.program_interactions_grounded(&rollout)
                {
                    continue;
                }
                while rollout.len() < target_order {
                    let mut next: Option<(usize, f64)> = None;
                    for index in 0..self.models.len() {
                        if !self.admissible_new_member(&rollout, index) {
                            continue;
                        }
                        let mut projected = rollout.clone();
                        projected.push(index);
                        if !self.manifold_program_admissible(&projected)
                            || !self.program_interactions_grounded(&projected)
                        {
                            continue;
                        }
                        let cost = self.cost(&projected, None);
                        if next.map_or(true, |old| (cost, index) < (old.1, old.0)) {
                            next = Some((index, cost));
                        }
                    }
                    let Some((index, _)) = next else { break };
                    rollout.push(index);
                }
                if rollout.len() != target_order {
                    continue;
                }
                let terminal_cost = self.cost(&rollout, None);
                if !(terminal_cost < current_cost) {
                    continue;
                }
                if best_rollout.map_or(true, |old| (terminal_cost, first) < (old.1, old.0)) {
                    best_rollout = Some((first, terminal_cost));
                }
            }
            let Some((first, _)) = best_rollout else {
                break;
            };
            plan.push(first);
        }

        // In a supported learning situation, use any remaining safe width to
        // sample consequence dimensions that the task-optimal program did not
        // already exercise. This is information acquisition, not task force.
        let horizon = self
            .manifold_foveated_frames()
            .and_then(|frames| frames.last().copied())
            .unwrap_or(0.0);
        let support = situation_support_field(
            self.graph,
            self.interner,
            self.episode,
            self.policy,
            horizon,
            true,
            0.0,
        );
        let safety = learning_safety_evidence(self.graph, self.interner, self.episode);
        if safety.active() && support.weights.iter().any(|weight| *weight > 0.0) {
            let mut covered = [false; 7];
            if let Some(effect) = self.manifold_effect(&plan) {
                for key in 0..7 {
                    covered[key] = effect[key].abs() > 0.0;
                }
            }
            loop {
                let mut best: Option<(usize, usize, f64, f64)> = None;
                for index in 0..self.models.len() {
                    if plan.contains(&index)
                        || !self.active(index)
                        || plan
                            .iter()
                            .any(|member| self.models[*member].group == self.models[index].group)
                    {
                        continue;
                    }
                    let newly_covered = (0..7)
                        .filter(|key| {
                            !covered[*key]
                                && support.weights[*key] > 0.0
                                && self.models[index].effect[*key].abs() > 0.0
                                && self.models[index].effect[*key].abs()
                                    <= safety.minimum_width_relaxation * support.weights[*key]
                        })
                        .count();
                    if newly_covered == 0 {
                        continue;
                    }
                    let mut candidate_plan = plan.clone();
                    candidate_plan.push(index);
                    let Some((anchor_loss, escaped, _, _)) = self.manifold_path(&candidate_plan)
                    else {
                        continue;
                    };
                    if escaped > 0.0 || !anchor_loss.is_finite() {
                        continue;
                    }
                    let cost = self.cost(&candidate_plan, None);
                    if best.map_or(true, |old| {
                        newly_covered > old.1
                            || (newly_covered == old.1
                                && (anchor_loss, cost, index) < (old.2, old.3, old.0))
                    }) {
                        best = Some((index, newly_covered, anchor_loss, cost));
                    }
                }
                let Some((candidate, _, _, _)) = best else {
                    break;
                };
                plan.push(candidate);
                if let Some(effect) = self.manifold_effect(&plan) {
                    for key in 0..7 {
                        covered[key] |= effect[key].abs() > 0.0;
                    }
                }
            }
        }
        let _ = self.cost(&plan, None);
        plan
    }

    fn admissible_new_member(&self, plan: &[usize], index: usize) -> bool {
        !plan.contains(&index)
            && self.active(index)
            && !plan
                .iter()
                .any(|member| self.models[*member].group == self.models[index].group)
    }

    fn manifold_program_admissible(&self, plan: &[usize]) -> bool {
        self.manifold_path(plan)
            .is_some_and(|(anchor_loss, escaped, _, _)| escaped == 0.0 && anchor_loss.is_finite())
    }

    fn program_interactions_grounded(&self, plan: &[usize]) -> bool {
        for left in 0..plan.len() {
            for right in left + 1..plan.len() {
                if !self
                    .synergy(plan[left], plan[right])
                    .is_some_and(|synergy| synergy.experience_count > 0.0)
                {
                    return false;
                }
            }
        }
        true
    }

    fn takeoff_exploration_target_order(&self) -> usize {
        if self.ep("self_takeoff_drive_active") <= 0.5 || !self.expansion_allowed() {
            return 1;
        }
        let Some(projects) = self.interner.lookup("projects_embodied_development") else {
            return 1;
        };
        let Some(active) = self
            .interner
            .lookup("has_active_embodied_developmental_capability")
        else {
            return 1;
        };
        let Some(development) = self
            .graph
            .neighbours(self.episode, Some(projects))
            .into_iter()
            .next()
        else {
            return 1;
        };
        let Some(capability) = self
            .graph
            .neighbours(development, Some(active))
            .into_iter()
            .next()
        else {
            return 1;
        };
        if sattr(self.graph, self.interner, capability, "evidence_kind")
            != self.interner.lookup("support_reducing_elevation")
        {
            return 1;
        }
        let window = fattr(
            self.graph,
            self.interner,
            development,
            "development_evidence_window",
        );
        let failures = fattr(self.graph, self.interner, capability, "failure_count");
        if !(window > 0.0 && failures >= window) {
            return 1;
        }
        let evidence_order = 1usize.saturating_add((failures / window).sqrt().floor() as usize);
        let mut groups: Vec<u64> = self
            .models
            .iter()
            .enumerate()
            .filter(|(index, _)| self.active(*index))
            .map(|(_, model)| model.group.to_bits())
            .collect();
        groups.sort_unstable();
        groups.dedup();
        evidence_order.min(groups.len()).max(1)
    }

    fn compose(&self) -> Vec<usize> {
        if self.humanoid_manifold_gate_active() {
            self.compose_manifold()
        } else {
            self.compose_legacy()
        }
    }

    fn compose_legacy(&self) -> Vec<usize> {
        let primary_token = sattr(
            self.graph,
            self.interner,
            self.episode,
            "selected_primary_token",
        );
        let primary_context = self.ep("selected_primary_context_id");
        let Some(primary) = self.models.iter().enumerate().find_map(|(i, model)| {
            (self.active(i) && model.token == primary_token && model.context_id == primary_context)
                .then_some(i)
        }) else {
            return Vec::new();
        };
        let mut plan = vec![primary];
        if !self.expansion_allowed() {
            return plan;
        }
        loop {
            let current = self.cost(&plan, None);
            let mut best: Option<(usize, f64, bool)> = None;
            for index in 0..self.models.len() {
                if plan.contains(&index)
                    || !self.active(index)
                    || plan
                        .iter()
                        .any(|member| self.models[*member].group == self.models[index].group)
                    || (self.ep("self_takeoff_drive_active") <= 0.5
                        && plan
                            .iter()
                            .any(|member| self.synergy(*member, index).is_none()))
                {
                    continue;
                }
                let cost = self.cost(&plan, Some(index));
                if !(cost < current) {
                    continue;
                }
                let hinted = self.basin_members.contains(&self.models[index].node);
                // A prior narrows an equivalent basin; it is not output
                // authority.  Receipt-backed predicted improvement therefore
                // remains primary, with the hint used only to break an exact
                // tie.  Reversing this ordering lets a broad bootstrap prior
                // override better situated evidence.
                if best.map_or(true, |(_, old_cost, old_hinted)| {
                    cost < old_cost || (cost == old_cost && hinted && !old_hinted)
                }) {
                    best = Some((index, cost, hinted));
                }
            }
            let Some((candidate, _, _)) = best else { break };
            plan.push(candidate);
        }
        // Re-score the SELECTED plan last so LAST_COST_TERMS holds the
        // winner's decomposition rather than whichever candidate happened to
        // be evaluated most recently.  Pure observability: the value is
        // discarded, `cost` is a pure function of (graph, plan), and the
        // returned plan is unchanged.
        let _ = self.cost(&plan, None);
        plan
    }
}

/// Term entry point: is `candidate` a member of the composed program for
/// (`episode`, `policy`)?  Pure function of graph state — deterministic,
/// re-evaluable per rule binding.
pub fn motor_compose_member(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
    policy: NodeID,
    candidate: NodeID,
) -> bool {
    let mut model_nodes = interner
        .lookup("has_embodied_effector_model")
        .map(|edge| graph.neighbours(episode, Some(edge)))
        .unwrap_or_default();
    if model_nodes.is_empty() {
        let Some(edge) = interner.lookup("has_humanoid_phase_action_model") else {
            return false;
        };
        model_nodes = graph.neighbours(episode, Some(edge));
        model_nodes.sort_by(|a, b| {
            let oa = fattr(graph, interner, *a, "ordinal");
            let ob = fattr(graph, interner, *b, "ordinal");
            oa.partial_cmp(&ob).unwrap_or(std::cmp::Ordering::Equal)
        });
        let request_seq = fattr(graph, interner, episode, "request_seq");
        let expansion_allowed = interner
            .lookup("has_active_humanoid_motor_program")
            .map(|active_edge| {
                graph
                    .neighbours(episode, Some(active_edge))
                    .into_iter()
                    .any(|plan| {
                        fattr(graph, interner, plan, "request_seq") == request_seq
                            && fattr(graph, interner, plan, "allow_expansion") == 1.0
                    })
            })
            .unwrap_or(false);
        let basin_members = active_humanoid_basin_members(graph, interner, episode);
        let key = HumanoidCache {
            graph_address: graph as *const TypedGraph as usize,
            episode,
            policy,
            // TypedGraph advances this revision at every mutation choke
            // point. It is a conservative, exact O(1) invalidator; unlike
            // the old content hash, validating each candidate no longer
            // rescans every model, capability and synergy.
            input_signature: graph.mutation_version(),
            request_seq: fattr(graph, interner, episode, "request_seq").to_bits(),
            state_seq: fattr(graph, interner, episode, "state_seq").to_bits(),
            primary_token: sattr(graph, interner, episode, "selected_primary_token"),
            primary_context: fattr(graph, interner, episode, "selected_primary_context_id")
                .to_bits(),
            takeoff_drive: fattr(graph, interner, episode, "self_takeoff_drive_active").to_bits(),
            takeoff_compression_scale: fattr(
                graph,
                interner,
                episode,
                "self_takeoff_compression_scale",
            )
            .to_bits(),
            takeoff_compression_authority: fattr(
                graph,
                interner,
                policy,
                "takeoff_motor_compression_authority",
            )
            .to_bits(),
            expansion_allowed,
            basin_members,
            model_count: model_nodes.len(),
            members: Vec::new(),
        };
        if let Some(hit) = HUMANOID_COMPOSE_CACHE.with(|slot| {
            let slot = slot.borrow();
            slot.as_ref()
                .filter(|cached| {
                    cached.graph_address == key.graph_address
                        && cached.episode == key.episode
                        && cached.policy == key.policy
                        && cached.input_signature == key.input_signature
                        && cached.request_seq == key.request_seq
                        && cached.state_seq == key.state_seq
                        && cached.primary_token == key.primary_token
                        && cached.primary_context == key.primary_context
                        && cached.takeoff_drive == key.takeoff_drive
                        && cached.takeoff_compression_scale == key.takeoff_compression_scale
                        && cached.takeoff_compression_authority == key.takeoff_compression_authority
                        && cached.expansion_allowed == key.expansion_allowed
                        && cached.basin_members == key.basin_members
                        && cached.model_count == key.model_count
                })
                .map(|cached| cached.members.contains(&candidate))
        }) {
            return hit;
        }
        let composer = HumanoidComposer::build(graph, interner, episode, policy, &model_nodes);
        let members: Vec<NodeID> = composer
            .compose()
            .iter()
            .map(|mi| composer.models[*mi].node)
            .collect();
        let answer = members.contains(&candidate);
        HUMANOID_COMPOSE_CACHE.with(|slot| {
            *slot.borrow_mut() = Some(HumanoidCache { members, ..key });
        });
        return answer;
    }
    model_nodes.sort_by(|a, b| {
        let oa = fattr(graph, interner, *a, "ordinal");
        let ob = fattr(graph, interner, *b, "ordinal");
        oa.partial_cmp(&ob).unwrap_or(std::cmp::Ordering::Equal)
    });
    let cache_key = EmbodiedComposeCache {
        graph_address: graph as *const TypedGraph as usize,
        episode,
        policy,
        request_seq: fattr(graph, interner, episode, "program_request_seq").to_bits(),
        state_seq: fattr(graph, interner, episode, "state_seq").to_bits(),
        manifold_enabled: fattr(graph, interner, policy, "future_manifold_enabled").to_bits(),
        bounds_ready: fattr(graph, interner, episode, "manifold_bounds_ready").to_bits(),
        model_count: model_nodes.len(),
        members: Vec::new(),
    };
    let cache_active = fattr(graph, interner, policy, "future_manifold_enabled") > 0.5
        && fattr(graph, interner, episode, "manifold_bounds_ready") > 0.5;
    if cache_active {
        if let Some(hit) = EMBODIED_COMPOSE_CACHE.with(|slot| {
            let slot = slot.borrow();
            slot.as_ref()
                .filter(|cached| {
                    cached.graph_address == cache_key.graph_address
                        && cached.episode == cache_key.episode
                        && cached.policy == cache_key.policy
                        && cached.request_seq == cache_key.request_seq
                        && cached.state_seq == cache_key.state_seq
                        && cached.manifold_enabled == cache_key.manifold_enabled
                        && cached.bounds_ready == cache_key.bounds_ready
                        && cached.model_count == cache_key.model_count
                })
                .map(|cached| cached.members.contains(&candidate))
        }) {
            return hit;
        }
    }
    let composer = Composer::build(graph, interner, episode, policy, &model_nodes);
    let members: Vec<NodeID> = composer
        .compose()
        .iter()
        .map(|mi| composer.models[*mi].node)
        .collect();
    let answer = members.contains(&candidate);
    if cache_active {
        EMBODIED_COMPOSE_CACHE.with(|slot| {
            *slot.borrow_mut() = Some(EmbodiedComposeCache {
                members,
                ..cache_key
            });
        });
    }
    answer
}

/// Compact graph-only future-manifold report.  This intentionally keeps the
/// projection arithmetic in Rust so callers do not duplicate recursive ASTs.
/// It reads only learned model/policy/episode attributes; no world adapter is
/// reachable from this evaluator.
pub fn future_manifold_projection_field(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
    policy: NodeID,
    source: NodeID,
    addition: Option<NodeID>,
    field: Sym,
) -> Value {
    if interner
        .lookup("embodied_program_path")
        .is_some_and(|kind| sattr(graph, interner, source, "kind") == Some(kind))
    {
        let name = interner.resolve(field);
        let narrativium_dimension = humanoid_narrativium_dimension(name);
        if name == "narrativium_snapshot" || narrativium_dimension.is_some() {
            let conditional = name.starts_with("conditional_narrativium_");
            let counts = cached_path_family_narrativium(
                graph,
                interner,
                episode,
                policy,
                source,
                addition,
                conditional,
            );
            if name == "narrativium_snapshot" {
                return counts.map_or(Value::None, |(reachable, retained)| {
                    Value::Tuple(std::sync::Arc::new(
                        reachable
                            .into_iter()
                            .chain(retained)
                            .map(Value::Float)
                            .collect::<Vec<_>>()
                            .into(),
                    ))
                });
            }
            let dimension = narrativium_dimension.expect("checked above");
            let retained = name.contains("narrativium_retained_");
            return Value::Float(
                counts
                    .map(|(reachable, retained_counts)| {
                        if retained {
                            retained_counts[dimension]
                        } else {
                            reachable[dimension]
                        }
                    })
                    .unwrap_or(0.0),
            );
        }
        let (report, effort_members, effort_exposure_count, _) =
            future_humanoid_manifold_projection_for_path(
                graph, interner, episode, policy, source, addition,
            );
        if name == "snapshot" {
            return projection_snapshot(
                graph,
                interner,
                episode,
                policy,
                source,
                &effort_members,
                &report,
                Some(effort_exposure_count as f64),
            );
        }
        if name == "shape_snapshot" {
            return projection_shape_snapshot(&report);
        }
        if name == "audit_snapshot" {
            return projection_audit_snapshot(
                graph,
                interner,
                episode,
                policy,
                source,
                &effort_members,
                &report,
                Some(effort_exposure_count as f64),
            );
        }
        if let Some(value) = projection_effort_field(
            graph,
            interner,
            episode,
            policy,
            source,
            &effort_members,
            &report,
            Some(effort_exposure_count as f64),
            name,
        ) {
            return Value::Float(value);
        }
        return Value::Float(report.field(name));
    }
    let member_edge = interner.lookup("includes_embodied_effector_model");
    let mut members = member_edge
        .map(|e| graph.neighbours(source, Some(e)))
        .unwrap_or_default();
    // Generic trajectory replay may certify a previously grounded humanoid
    // program rather than a just-open generic composition plan.  Both are
    // analysis-by-synthesis model collections; only their held edge vocabulary
    // differs.  Prefer the generic edge and fall back to the body-local phase
    // model edge so no simulator/world rollout enters projection.
    let mut humanoid_program = false;
    if members.is_empty() {
        members = interner
            .lookup("includes_humanoid_phase_action_model")
            .map(|e| graph.neighbours(source, Some(e)))
            .unwrap_or_default();
        humanoid_program = !members.is_empty()
            && interner
                .lookup("has_humanoid_phase_action_model")
                .is_some_and(|edge| !graph.neighbours(episode, Some(edge)).is_empty());
    }
    if let Some(a) = addition {
        // `addition` denotes the second source being composed.  It may be an
        // atomic effector model (the original API) or another complete motor
        // program.  Projecting the container node as though it were a learned
        // model discards all of its receipt-grounded dynamics and therefore
        // fails closed with zero support/resolution.  Expand program sources
        // through the same vocabulary used for `source`, while retaining the
        // atomic-model compatibility path.
        let mut addition_members = member_edge
            .map(|e| graph.neighbours(a, Some(e)))
            .unwrap_or_default();
        let mut addition_is_humanoid_program = false;
        if addition_members.is_empty() {
            addition_members = interner
                .lookup("includes_humanoid_phase_action_model")
                .map(|e| graph.neighbours(a, Some(e)))
                .unwrap_or_default();
            addition_is_humanoid_program = !addition_members.is_empty()
                && interner
                    .lookup("has_humanoid_phase_action_model")
                    .is_some_and(|edge| !graph.neighbours(episode, Some(edge)).is_empty());
        }
        if addition_members.is_empty() {
            addition_members.push(a);
        }
        for member in addition_members {
            if !members.contains(&member) {
                members.push(member);
            }
        }
        humanoid_program |= addition_is_humanoid_program;
    }
    let name = interner.resolve(field);
    if humanoid_program {
        if addition.is_none() && name == "takeoff_effort_snapshot" {
            return takeoff_recruitment_snapshot(takeoff_recruitment_projection(
                graph, interner, episode, policy, source,
            ));
        }
        let report = cached_future_humanoid_manifold_projection_for_members(
            graph,
            interner,
            episode,
            policy,
            &members,
            addition.is_none().then_some(source),
        );
        if name == "snapshot" {
            return projection_snapshot(
                graph, interner, episode, policy, source, &members, &report, None,
            );
        }
        if name == "shape_snapshot" {
            return projection_shape_snapshot(&report);
        }
        if name == "audit_snapshot" {
            return projection_audit_snapshot(
                graph, interner, episode, policy, source, &members, &report, None,
            );
        }
        if let Some(value) = projection_effort_field(
            graph, interner, episode, policy, source, &members, &report, None, name,
        ) {
            return Value::Float(value);
        }
        return Value::Float(report.field(name));
    }
    let source_kind = sattr(graph, interner, source, "source");
    let epistemic_probe = source_kind == interner.lookup("factorized_calibration")
        || source_kind == interner.lookup("graph_requested_flow_excitation");
    let report = future_manifold_projection_for_members(
        graph,
        interner,
        episode,
        policy,
        &members,
        epistemic_probe,
    );
    if name == "snapshot" {
        return projection_snapshot(
            graph, interner, episode, policy, source, &members, &report, None,
        );
    }
    if name == "shape_snapshot" {
        return projection_shape_snapshot(&report);
    }
    if name == "audit_snapshot" {
        return projection_audit_snapshot(
            graph, interner, episode, policy, source, &members, &report, None,
        );
    }
    if let Some(value) = projection_effort_field(
        graph, interner, episode, policy, source, &members, &report, None, name,
    ) {
        return Value::Float(value);
    }
    Value::Float(report.field(name))
}

fn future_manifold_episode_models(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
) -> Vec<NodeID> {
    let mut models = interner
        .lookup("has_embodied_effector_model")
        .map(|edge| graph.neighbours(episode, Some(edge)))
        .unwrap_or_default();
    // Humanoid phase-action models are the body-local vocabulary for the
    // same learned analysis-by-synthesis evidence.  A humanoid episode does
    // not duplicate those nodes under the generic edge, so projection must
    // use the same fallback for its neutral reference population that it
    // uses for a program's active members.
    if models.is_empty() {
        models = interner
            .lookup("has_humanoid_phase_action_model")
            .map(|edge| graph.neighbours(episode, Some(edge)))
            .unwrap_or_default();
    }
    models
}

#[derive(Clone)]
struct FutureProjectionReport {
    support: bool,
    resolved: bool,
    termination_code: f64,
    horizon: f64,
    budget: f64,
    loss: f64,
    information_loss: f64,
    anchor_count: f64,
    refinement_count: f64,
    certified_interval_count: f64,
    ambiguous_interval_count: f64,
    max_enclosure_width: f64,
    max_shape_order: f64,
    earliest_decisive_tick: f64,
    minimum_exafferent_scale: f64,
    residual: [f64; 7],
    retained: [f64; 7],
    situated_support: [f64; 7],
    applied_bounds: [f64; 7],
}

#[derive(Clone)]
struct HumanoidProjectionCache {
    graph_address: usize,
    episode: NodeID,
    policy: NodeID,
    input_signature: u64,
    members: Vec<NodeID>,
    observed_program: Option<NodeID>,
    report: FutureProjectionReport,
}

thread_local! {
    /// A release predicate and its audit effects request support, resolution,
    /// loss and information loss separately for the same grounded program.
    /// Those fields are one projection, not four independent simulations.
    /// Cache the complete immutable report and invalidate it from the same
    /// learned-model/bounds/context signature used by native composition.
    static HUMANOID_PROJECTION_CACHE: RefCell<Option<HumanoidProjectionCache>> =
        const { RefCell::new(None) };
}

impl FutureProjectionReport {
    fn field(&self, name: &str) -> f64 {
        match name {
            "support" => {
                if self.support {
                    1.0
                } else {
                    0.0
                }
            }
            "resolved" => {
                if self.resolved {
                    1.0
                } else {
                    0.0
                }
            }
            "termination_code" => self.termination_code,
            "horizon" => self.horizon,
            "budget" => self.budget,
            "loss" => self.loss,
            "information_loss" => self.information_loss,
            "anchor_count" => self.anchor_count,
            "refinement_count" => self.refinement_count,
            "certified_interval_count" => self.certified_interval_count,
            "ambiguous_interval_count" => self.ambiguous_interval_count,
            "max_enclosure_width" => self.max_enclosure_width,
            "max_shape_order" => self.max_shape_order,
            "earliest_decisive_tick" => self.earliest_decisive_tick,
            "minimum_exafferent_scale" => self.minimum_exafferent_scale,
            key if key.starts_with("residual_") => key[9..]
                .parse::<usize>()
                .ok()
                .and_then(|index| self.residual.get(index))
                .copied()
                .unwrap_or(0.0),
            key if key.starts_with("shape_residual_") => {
                let indices: Vec<usize> = key[15..]
                    .split('_')
                    .filter_map(|part| part.parse::<usize>().ok())
                    .collect();
                if indices.len() == 2 && indices[0] as f64 == self.earliest_decisive_tick {
                    self.residual.get(indices[1]).copied().unwrap_or(0.0)
                } else {
                    0.0
                }
            }
            "exploration_authority" => self
                .situated_support
                .iter()
                .copied()
                .reduce(f64::min)
                .unwrap_or(0.0),
            "situated_support_forward" => self.situated_support[0],
            "applied_bound_forward" => self.applied_bounds[0],
            "retained_width" => {
                if self.support {
                    self.retained.iter().sum()
                } else {
                    0.0
                }
            }
            key if key.starts_with("narrativium_reachable_") => {
                let suffix = &key[22..];
                let represented = suffix
                    .parse::<usize>()
                    .ok()
                    .filter(|index| *index < self.retained.len())
                    .or_else(|| COMPONENTS.iter().position(|component| *component == suffix))
                    .or_else(|| {
                        HUMANOID_KEYS
                            .iter()
                            .position(|component| *component == suffix)
                    });
                represented
                    .map(|_| if self.support { 1.0 } else { 0.0 })
                    .unwrap_or(0.0)
            }
            key if key.starts_with("narrativium_retained_") => {
                let suffix = &key[21..];
                suffix
                    .parse::<usize>()
                    .ok()
                    .and_then(|index| self.retained.get(index))
                    .copied()
                    .or_else(|| {
                        COMPONENTS
                            .iter()
                            .position(|component| *component == suffix)
                            .or_else(|| {
                                HUMANOID_KEYS
                                    .iter()
                                    .position(|component| *component == suffix)
                            })
                            .and_then(|index| self.retained.get(index))
                            .copied()
                    })
                    .map(|retained| if self.support { retained } else { 0.0 })
                    .unwrap_or(0.0)
            }
            key if key.starts_with("retained_") => self
                .retained
                .iter()
                .enumerate()
                .find(|(i, _)| COMPONENTS[*i] == &key[9..])
                .map(|(_, value)| *value)
                .unwrap_or(0.0),
            key if key.starts_with("situated_support_") => key[17..]
                .parse::<usize>()
                .ok()
                .and_then(|index| self.situated_support.get(index))
                .copied()
                .unwrap_or(0.0),
            key if key.starts_with("applied_bound_") => key[14..]
                .parse::<usize>()
                .ok()
                .and_then(|index| self.applied_bounds.get(index))
                .copied()
                .unwrap_or(0.0),
            _ => 0.0,
        }
    }
}

/// Attach the generic ideal-effort contract to legacy/domain projectors.
///
/// The trajectory projector can read explicit candidate arrays directly. A
/// domain analysis-by-synthesis model instead represents effort on its learned
/// members, so resolve the same fields here without changing its state path.
/// An episode-learned ideal wins; the policy prior exists only for domains
/// that have not yet published receipt-grounded adaptation.
fn projection_effort_field(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
    policy: NodeID,
    source: NodeID,
    members: &[NodeID],
    report: &FutureProjectionReport,
    effort_exposure_count: Option<f64>,
    name: &str,
) -> Option<f64> {
    let learned_ideal = fattr(graph, interner, episode, "future_manifold_ideal_effort");
    let prior_ideal = fattr(
        graph,
        interner,
        policy,
        "future_manifold_ideal_effort_prior",
    );
    let ideal_effort = if learned_ideal > 0.0 {
        learned_ideal
    } else {
        prior_ideal
    };
    let explicit_effort = fattr(graph, interner, source, "future_manifold_effort");
    let source_effort = fattr(graph, interner, source, "mean_input_energy_joules");
    let member_effort = members
        .iter()
        .map(|member| fattr(graph, interner, *member, "mean_input_energy_joules").max(0.0))
        .sum::<f64>();
    let effort_scale = fattr(
        graph,
        interner,
        episode,
        "future_manifold_effort_scale_joules",
    );
    let exposure_count = effort_exposure_count.unwrap_or(1.0);
    let exposure_supported =
        exposure_count.is_finite() && exposure_count >= 1.0 && exposure_count.fract() == 0.0;
    let situated_effort_scale = effort_scale * exposure_count;
    let normalize = |energy: f64| {
        if situated_effort_scale > 0.0 {
            energy / situated_effort_scale
        } else {
            energy
        }
    };
    let explicit_ratio = explicit_effort > 0.0;
    let dimensional_evidence = source_effort > 0.0 || member_effort > 0.0;
    let ratio_comparable =
        explicit_ratio || (effort_scale > 0.0 && exposure_supported && dimensional_evidence);
    let projected_effort = if explicit_ratio {
        explicit_effort
    } else if effort_scale <= 0.0 || !exposure_supported {
        0.0
    } else if source_effort > 0.0 {
        normalize(source_effort)
    } else {
        normalize(member_effort)
    };
    let effort_supported = ideal_effort.is_finite()
        && ideal_effort > 0.0
        && projected_effort.is_finite()
        && projected_effort > 0.0
        && ratio_comparable;
    let effort_residual = if effort_supported {
        (projected_effort - ideal_effort).max(0.0)
    } else {
        0.0
    };

    let ideal_completion = fattr(
        graph,
        interner,
        episode,
        "future_manifold_ideal_completion_time",
    );
    let explicit_completion = fattr(graph, interner, source, "future_manifold_completion_time");
    let projected_completion = if explicit_completion > 0.0 {
        explicit_completion
    } else {
        report.horizon
    };
    // Reaching a manifold boundary early is an escape, not fast completion.
    // Never let a decisive loss manufacture the time compression that would
    // authorize above-normal effort.
    let time_compression =
        if report.loss <= 0.0 && ideal_completion > 0.0 && projected_completion >= 0.0 {
            (ideal_completion - projected_completion).max(0.0)
        } else {
            0.0
        };
    let ideal_width = fattr(graph, interner, episode, "future_manifold_ideal_width");
    let width_compression = if ideal_width > 0.0 {
        (ideal_width - report.max_enclosure_width).max(0.0)
    } else {
        0.0
    };
    let ideal_information = fattr(
        graph,
        interner,
        episode,
        "future_manifold_ideal_information_loss",
    );
    let inferred_information_compression = if ideal_information > 0.0 {
        (ideal_information - report.information_loss).max(0.0)
    } else {
        0.0
    };
    // A domain may already have an exact counterfactual decomposition for a
    // compound receipt.  Publishing its measured reduction in unresolved
    // interaction dimensions is equivalent to the ideal-vs-projected form
    // above, while avoiding a fabricated percentage tolerance on effort.
    let explicit_information_compression = fattr(
        graph,
        interner,
        source,
        "future_manifold_information_compression",
    );
    let information_compression = if explicit_information_compression.is_finite() {
        inferred_information_compression.max(explicit_information_compression.max(0.0))
    } else {
        inferred_information_compression
    };
    let compression_dimension_count = [time_compression, width_compression, information_compression]
        .into_iter()
        .filter(|compression| *compression > 0.0)
        .count() as f64;
    let manifold_compression = compression_dimension_count > 0.0;
    let effort_authorized = !effort_supported || effort_residual <= 0.0 || manifold_compression;

    Some(match name {
        "effort_supported" => effort_supported as i32 as f64,
        "projected_effort" => projected_effort,
        "ideal_effort" => ideal_effort,
        "effort_scale" => situated_effort_scale,
        "effort_residual" => effort_residual,
        "time_compression" => time_compression,
        "width_compression" => width_compression,
        "information_compression" => information_compression,
        "compression_dimension_count" => compression_dimension_count,
        "manifold_compression" => manifold_compression as i32 as f64,
        "effort_authorized" => effort_authorized as i32 as f64,
        _ => return None,
    })
}

fn projection_snapshot(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
    policy: NodeID,
    source: NodeID,
    members: &[NodeID],
    report: &FutureProjectionReport,
    effort_exposure_count: Option<f64>,
) -> Value {
    let effort_supported = projection_effort_field(
        graph,
        interner,
        episode,
        policy,
        source,
        members,
        report,
        effort_exposure_count,
        "effort_supported",
    )
    .unwrap_or(0.0);
    let effort_authorized = projection_effort_field(
        graph,
        interner,
        episode,
        policy,
        source,
        members,
        report,
        effort_exposure_count,
        "effort_authorized",
    )
    .unwrap_or(0.0);
    Value::Tuple(std::sync::Arc::new(
        vec![
            Value::Float(report.field("support")),
            Value::Float(report.field("resolved")),
            Value::Float(report.field("loss")),
            Value::Float(report.field("information_loss")),
            Value::Float(effort_supported),
            Value::Float(effort_authorized),
        ]
        .into(),
    ))
}

/// One immutable view of the projected manifold shape used by audit rules.
/// Keeping the residual and applied-bound vectors together prevents graph
/// writes between scalar field reads from invalidating and recomputing the
/// same analysis-by-synthesis projection.
fn projection_shape_snapshot(report: &FutureProjectionReport) -> Value {
    let mut fields = Vec::with_capacity(21);
    fields.extend([
        report.field("support"),
        report.field("resolved"),
        report.field("loss"),
        report.field("information_loss"),
        report.field("horizon"),
        report.field("earliest_decisive_tick"),
        report.field("minimum_exafferent_scale"),
    ]);
    fields.extend(report.residual);
    fields.extend(report.applied_bounds);
    Value::Tuple(std::sync::Arc::new(
        fields
            .into_iter()
            .map(Value::Float)
            .collect::<Vec<_>>()
            .into(),
    ))
}

fn projection_audit_snapshot(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
    policy: NodeID,
    source: NodeID,
    members: &[NodeID],
    report: &FutureProjectionReport,
    effort_exposure_count: Option<f64>,
) -> Value {
    const FIELDS: [&str; 34] = [
        "support",
        "resolved",
        "loss",
        "information_loss",
        "horizon",
        "anchor_count",
        "refinement_count",
        "termination_code",
        "exploration_authority",
        "effort_supported",
        "projected_effort",
        "ideal_effort",
        "effort_scale",
        "effort_residual",
        "time_compression",
        "width_compression",
        "information_compression",
        "compression_dimension_count",
        "manifold_compression",
        "effort_authorized",
        "situated_support_0",
        "situated_support_1",
        "situated_support_2",
        "situated_support_3",
        "situated_support_4",
        "situated_support_5",
        "situated_support_6",
        "applied_bound_0",
        "applied_bound_1",
        "applied_bound_2",
        "applied_bound_3",
        "applied_bound_4",
        "applied_bound_5",
        "applied_bound_6",
    ];
    let values = FIELDS
        .into_iter()
        .map(|field| {
            projection_effort_field(
                graph,
                interner,
                episode,
                policy,
                source,
                members,
                report,
                effort_exposure_count,
                field,
            )
            .unwrap_or_else(|| report.field(field))
        })
        .map(Value::Float)
        .collect::<Vec<_>>();
    Value::Tuple(std::sync::Arc::new(values.into()))
}

fn support_observability(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
    policy: NodeID,
    horizon: f64,
    humanoid_axes: bool,
    caregiver_counterfactual_scale: f64,
) -> ([f64; 7], [f64; 7]) {
    let safety = learning_safety_evidence(graph, interner, episode);
    let field = situation_support_field(
        graph,
        interner,
        episode,
        policy,
        horizon,
        humanoid_axes,
        caregiver_counterfactual_scale,
    );
    let mut bounds = [0.0; 7];
    let keys = if humanoid_axes {
        &HUMANOID_KEYS
    } else {
        &COMPONENTS
    };
    for (index, key) in keys.iter().enumerate() {
        bounds[index] = safety.bound(
            fattr(graph, interner, episode, &format!("manifold_bound_{key}")),
            field.weights[index],
        );
    }
    (field.weights, bounds)
}

#[derive(Clone)]
struct HumanoidPathSegment {
    transition: NodeID,
    program: NodeID,
    frames: i32,
}

fn unsupported_future_projection_report(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
    policy: NodeID,
) -> FutureProjectionReport {
    let (situated_support, applied_bounds) =
        support_observability(graph, interner, episode, policy, 0.0, true, 0.0);
    FutureProjectionReport {
        support: false,
        resolved: false,
        termination_code: 4.0,
        horizon: 0.0,
        budget: fattr(graph, interner, policy, "future_manifold_projection_budget"),
        loss: 0.0,
        information_loss: 0.0,
        anchor_count: 0.0,
        refinement_count: 0.0,
        certified_interval_count: 0.0,
        ambiguous_interval_count: 0.0,
        max_enclosure_width: 0.0,
        max_shape_order: 0.0,
        earliest_decisive_tick: 0.0,
        minimum_exafferent_scale: 0.0,
        residual: [0.0; 7],
        retained: [0.0; 7],
        situated_support,
        applied_bounds,
    }
}

fn unique_neighbour(
    graph: &TypedGraph,
    interner: &Interner,
    node: NodeID,
    edge: &str,
) -> Option<NodeID> {
    let edge = interner.lookup(edge)?;
    let neighbours = graph.neighbours(node, Some(edge));
    (neighbours.len() == 1).then_some(neighbours[0])
}

/// Recover the path's temporal order from its graph edges. Membership edges
/// are sets, so order is established only by an unambiguous connected chain
/// from the declared origin to the declared terminal. Any fork, gap, cycle,
/// stale depth, or unverified transition is unsupported rather than guessed.
fn humanoid_path_segments(
    graph: &TypedGraph,
    interner: &Interner,
    path: NodeID,
    current_transition: Option<NodeID>,
) -> Option<Vec<HumanoidPathSegment>> {
    let edge = interner.lookup("contains_embodied_program_transition")?;
    let transitions = graph.neighbours(path, Some(edge));
    let depth = fattr(graph, interner, path, "depth");
    if transitions.is_empty()
        || !depth.is_finite()
        || depth < 1.0
        || depth.fract() != 0.0
        || depth as usize != transitions.len()
    {
        return None;
    }
    let mut current = unique_neighbour(graph, interner, path, "starts_from_embodied_program")?;
    let terminal = unique_neighbour(graph, interner, path, "continues_with_embodied_program")?;
    let mut unused = transitions;
    let mut segments = Vec::with_capacity(unused.len());
    while !unused.is_empty() {
        let matching: Vec<(usize, NodeID)> = unused
            .iter()
            .copied()
            .enumerate()
            .filter(|(_, transition)| {
                unique_neighbour(graph, interner, *transition, "starts_from_embodied_program")
                    == Some(current)
            })
            .collect();
        if matching.len() != 1 {
            return None;
        }
        let (index, transition) = matching[0];
        if fattr(graph, interner, transition, "verified") <= 0.5 {
            return None;
        }
        let frames = fattr(graph, interner, transition, "response_frames");
        if !frames.is_finite() || frames < 1.0 || frames.fract() != 0.0 || frames > i32::MAX as f64
        {
            return None;
        }
        current = unique_neighbour(
            graph,
            interner,
            transition,
            "continues_with_embodied_program",
        )?;
        segments.push(HumanoidPathSegment {
            transition,
            program: current,
            frames: frames as i32,
        });
        unused.swap_remove(index);
    }
    if current != terminal {
        return None;
    }
    if let Some(anchor) = current_transition {
        let index = segments
            .iter()
            .position(|segment| segment.transition == anchor)?;
        segments.drain(0..index);
    }
    Some(segments)
}

fn foveated_segment_anchors(horizon: i32) -> Option<Vec<i32>> {
    if horizon < 1 {
        return None;
    }
    let mut frames = Vec::new();
    let mut current = 0i32;
    while current < horizon {
        let requested = match current {
            0 => 1,
            1 => 2,
            2 => 3,
            3 => 4,
            4 => 8,
            8 => 16,
            value => value.saturating_mul(value),
        };
        let next = requested.min(horizon);
        if next <= current {
            return None;
        }
        frames.push(next);
        current = next;
    }
    Some(frames)
}

fn humanoid_narrativium_dimension(field: &str) -> Option<usize> {
    let suffix = field
        .strip_prefix("narrativium_reachable_")
        .or_else(|| field.strip_prefix("narrativium_retained_"))
        .or_else(|| field.strip_prefix("conditional_narrativium_reachable_"))
        .or_else(|| field.strip_prefix("conditional_narrativium_retained_"))?;
    suffix
        .parse::<usize>()
        .ok()
        .filter(|index| *index < HUMANOID_KEYS.len())
        .or_else(|| COMPONENTS.iter().position(|component| *component == suffix))
        .or_else(|| {
            HUMANOID_KEYS
                .iter()
                .position(|component| *component == suffix)
        })
}

/// Count distinct projected future shapes beside `selected`. Projected time
/// remains part of every per-dimension trace key; axes are never collapsed
/// into a scalar. A malformed member leaves the family unknown.
fn path_family_narrativium(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
    policy: NodeID,
    selected: NodeID,
    current_transition: Option<NodeID>,
    selected_projection: (&FutureProjectionReport, &[(i32, [f64; 7])]),
    condition_on_first_transition: bool,
) -> Option<([f64; 7], [f64; 7])> {
    let candidate_edge = interner.lookup("has_pareto_candidate");
    let trajectories = candidate_edge
        .map(|edge| graph.in_neighbours(selected, Some(edge)))
        .unwrap_or_default();
    let mut candidates = if trajectories.is_empty() {
        vec![selected]
    } else {
        if trajectories.len() != 1 {
            return None;
        }
        graph.neighbours(trajectories[0], candidate_edge)
    };
    let selected_depth = fattr(graph, interner, selected, "depth");
    candidates.retain(|candidate| fattr(graph, interner, *candidate, "depth") == selected_depth);
    let decision_anchor = current_transition.or_else(|| {
        condition_on_first_transition
            .then(|| humanoid_path_segments(graph, interner, selected, None))
            .flatten()
            .and_then(|segments| segments.first().map(|segment| segment.transition))
    });
    if let (Some(anchor), Some(contains_edge)) = (
        decision_anchor,
        interner.lookup("contains_embodied_program_transition"),
    ) {
        candidates.retain(|candidate| {
            graph
                .neighbours(*candidate, Some(contains_edge))
                .contains(&anchor)
        });
    }
    if let Some(dominated_edge) = interner.lookup("is_dominated_by_pareto_candidate") {
        candidates.retain(|candidate| {
            graph
                .neighbours(*candidate, Some(dominated_edge))
                .is_empty()
        });
    }
    if let (Some(anchor), Some(blocked_edge)) = (
        decision_anchor,
        interner.lookup("manifold_blocked_from_embodied_program_transition"),
    ) {
        candidates.retain(|candidate| {
            !graph
                .neighbours(*candidate, Some(blocked_edge))
                .contains(&anchor)
        });
    }
    if candidates.is_empty() {
        return None;
    }

    let mut projections = Vec::with_capacity(candidates.len());
    for candidate in candidates {
        if candidate == selected {
            projections.push((
                selected_projection.0.clone(),
                selected_projection.1.to_vec(),
            ));
        } else {
            let (report, _, _, trace) = future_humanoid_manifold_projection_for_path(
                graph,
                interner,
                episode,
                policy,
                candidate,
                current_transition,
            );
            projections.push((report, trace));
        }
    }
    if projections
        .iter()
        .any(|(report, trace)| !report.support || trace.is_empty())
    {
        return None;
    }

    let mut reachable = [0.0; 7];
    let mut retained = [0.0; 7];
    for dimension in 0..7 {
        let mut reachable_traces: Vec<Vec<(i32, u64)>> = Vec::new();
        let mut retained_traces: Vec<Vec<(i32, u64)>> = Vec::new();
        for (report, trace) in &projections {
            let key: Vec<(i32, u64)> = trace
                .iter()
                .map(|(tick, values)| {
                    let value = values[dimension];
                    (
                        *tick,
                        if value == 0.0 {
                            0.0f64.to_bits()
                        } else {
                            value.to_bits()
                        },
                    )
                })
                .collect();
            if !reachable_traces.contains(&key) {
                reachable_traces.push(key.clone());
            }
            if report.retained[dimension] > 0.5 && !retained_traces.contains(&key) {
                retained_traces.push(key);
            }
        }
        reachable[dimension] = reachable_traces.len() as f64;
        retained[dimension] = retained_traces.len() as f64;
    }
    Some((reachable, retained))
}

#[derive(Clone)]
struct PathNarrativiumCacheEntry {
    episode: NodeID,
    policy: NodeID,
    path: NodeID,
    current_transition: Option<NodeID>,
    conditional: bool,
    counts: Option<([f64; 7], [f64; 7])>,
}

thread_local! {
    static PATH_NARRATIVIUM_CACHE: RefCell<(usize, u64, Vec<PathNarrativiumCacheEntry>)> =
        const { RefCell::new((0, 0, Vec::new())) };
}

fn cached_path_family_narrativium(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
    policy: NodeID,
    path: NodeID,
    current_transition: Option<NodeID>,
    conditional: bool,
) -> Option<([f64; 7], [f64; 7])> {
    let graph_address = graph as *const TypedGraph as usize;
    let mutation_version = graph.mutation_version();
    if let Some(counts) = PATH_NARRATIVIUM_CACHE.with(|slot| {
        let slot = slot.borrow();
        (slot.0 == graph_address && slot.1 == mutation_version)
            .then(|| {
                slot.2.iter().find(|entry| {
                    entry.episode == episode
                        && entry.policy == policy
                        && entry.path == path
                        && entry.current_transition == current_transition
                        && entry.conditional == conditional
                })
            })
            .flatten()
            .map(|entry| entry.counts)
    }) {
        return counts;
    }
    let (report, _, _, trace) = future_humanoid_manifold_projection_for_path(
        graph,
        interner,
        episode,
        policy,
        path,
        current_transition,
    );
    let counts = path_family_narrativium(
        graph,
        interner,
        episode,
        policy,
        path,
        current_transition,
        (&report, &trace),
        conditional,
    );
    PATH_NARRATIVIUM_CACHE.with(|slot| {
        let mut slot = slot.borrow_mut();
        if slot.0 != graph_address || slot.1 != mutation_version {
            *slot = (graph_address, mutation_version, Vec::new());
        }
        slot.2.push(PathNarrativiumCacheEntry {
            episode,
            policy,
            path,
            current_transition,
            conditional,
            counts,
        });
    });
    counts
}

fn rebind_humanoid_program_members(
    graph: &TypedGraph,
    interner: &Interner,
    composer: &HumanoidComposer<'_>,
    all_models: &[NodeID],
    program: NodeID,
) -> Option<(Vec<usize>, Vec<NodeID>)> {
    let mut descriptors = Vec::new();
    for edge_name in [
        "includes_humanoid_phase_action_model",
        "includes_humanoid_action_model",
    ] {
        if let Some(member_edge) = interner.lookup(edge_name) {
            for member in graph.neighbours(program, Some(member_edge)) {
                if !descriptors.contains(&member) {
                    descriptors.push(member);
                }
            }
        }
    }
    // A retained trajectory endpoint deliberately remains detached from the
    // warm proposal population.  Its output-null library members are enough
    // to identify the current episode's learned analysis-by-synthesis models;
    // resolving them here does not grant the retained program authority.
    if descriptors.is_empty() {
        if let Some(member_edge) = interner.lookup("has_humanoid_library_motor_member") {
            descriptors = graph.neighbours(program, Some(member_edge));
        }
    }
    if descriptors.is_empty() {
        return None;
    }
    let mut rebound = Vec::with_capacity(descriptors.len());
    let mut rebound_models = Vec::with_capacity(descriptors.len());
    for node in &descriptors {
        let index = if fattr(graph, interner, *node, "exafferent") > 0.5 {
            all_models
                .iter()
                .position(|known| known == node)
                .filter(|index| composer.active(*index))
        } else {
            let token = sattr(graph, interner, *node, "token");
            let ordinal = fattr(graph, interner, *node, "ordinal");
            let support_phase = fattr(graph, interner, *node, "support_phase");
            all_models.iter().enumerate().find_map(|(index, known)| {
                (composer.active(index)
                    && sattr(graph, interner, *known, "token") == token
                    && fattr(graph, interner, *known, "ordinal") == ordinal
                    && fattr(graph, interner, *known, "support_phase") == support_phase)
                    .then_some(index)
            })
        }?;
        if rebound.contains(&index) {
            return None;
        }
        rebound.push(index);
        rebound_models.push(all_models[index]);
    }
    Some((rebound, rebound_models))
}

#[derive(Clone, Copy)]
struct TakeoffRecruitmentProjection {
    supported: bool,
    required_ratio: f64,
    selected_ratio: f64,
    residual_ratio: f64,
    authorized: bool,
    selected_effect: [f64; 7],
}

fn persistent_takeoff_development_evidence(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
) -> bool {
    let Some(projects) = interner.lookup("projects_embodied_development") else {
        return false;
    };
    let Some(active) = interner.lookup("has_active_embodied_developmental_capability") else {
        return false;
    };
    let Some(development) = graph.neighbours(episode, Some(projects)).into_iter().next() else {
        return false;
    };
    let Some(capability) = graph
        .neighbours(development, Some(active))
        .into_iter()
        .next()
    else {
        return false;
    };
    let window = fattr(graph, interner, development, "development_evidence_window");
    sattr(graph, interner, capability, "evidence_kind")
        == interner.lookup("support_reducing_elevation")
        && window > 0.0
        && fattr(graph, interner, capability, "failure_count") >= window
}

fn takeoff_recruitment_projection(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
    policy: NodeID,
    program: NodeID,
) -> TakeoffRecruitmentProjection {
    let unsupported = TakeoffRecruitmentProjection {
        supported: false,
        required_ratio: 1.0,
        selected_ratio: 1.0,
        residual_ratio: 0.0,
        authorized: false,
        selected_effect: [0.0; 7],
    };
    if fattr(graph, interner, episode, "self_takeoff_drive_active") <= 0.5
        || !learning_safety_evidence(graph, interner, episode).active()
    {
        return unsupported;
    }
    if !persistent_takeoff_development_evidence(graph, interner, episode) {
        return unsupported;
    }

    let mut all_models = interner
        .lookup("has_humanoid_phase_action_model")
        .map(|edge| graph.neighbours(episode, Some(edge)))
        .unwrap_or_default();
    let Some(member_edge) = interner.lookup("includes_humanoid_phase_action_model") else {
        return unsupported;
    };
    for member in graph.neighbours(program, Some(member_edge)) {
        if !all_models.contains(&member) {
            all_models.push(member);
        }
    }
    if all_models.is_empty() {
        return unsupported;
    }
    let composer = HumanoidComposer::build(graph, interner, episode, policy, &all_models);
    let Some((members, _)) =
        rebind_humanoid_program_members(graph, interner, &composer, &all_models, program)
    else {
        return unsupported;
    };
    let Some(effect) = composer.manifold_effect(&members) else {
        return unsupported;
    };
    let predicted_dvz = effect[6];
    if !predicted_dvz.is_finite() || predicted_dvz <= 0.0 {
        return unsupported;
    }
    let height = fattr(graph, interner, episode, "standing_reference_z");
    let gravity = fattr(graph, interner, policy, "gravity_acceleration");
    let prior = fattr(graph, interner, policy, "support_phase_prior_strength");
    if !(height > 0.0 && gravity > 0.0 && prior > 0.0) {
        return unsupported;
    }
    let target = fattr(
        graph,
        interner,
        episode,
        "self_takeoff_target_velocity_scale",
    ) * (gravity * height).sqrt()
        / prior;
    let target_delta = target - fattr(graph, interner, episode, "state_vz");
    let required_ratio = if target_delta <= predicted_dvz {
        1.0
    } else {
        // Uniform recruitment is exactly quadratic for the learned model:
        // individual effects scale as r and pair synergies as r².  Recover
        // those coefficients from two projections and solve for the least
        // ratio that closes the temporal residual.  This avoids both a magic
        // increment and the systematic over-recruitment of a linear guess.
        let doubled_dvz = composer
            .manifold_effect_at_scales_for_frames(
                &members,
                None,
                composer.ep("response_frames"),
                2.0,
            )
            .map(|scaled| scaled[6])
            .unwrap_or(f64::NAN);
        let quadratic = (doubled_dvz - 2.0 * predicted_dvz) / 2.0;
        let linear = predicted_dvz - quadratic;
        if quadratic == 0.0 {
            if linear > 0.0 {
                target_delta / linear
            } else {
                f64::NAN
            }
        } else {
            let discriminant = linear * linear + 4.0 * quadratic * target_delta;
            if discriminant < 0.0 {
                f64::NAN
            } else {
                let root = discriminant.sqrt();
                [
                    (-linear - root) / (2.0 * quadratic),
                    (-linear + root) / (2.0 * quadratic),
                ]
                .into_iter()
                .filter(|ratio| ratio.is_finite() && *ratio >= 1.0)
                .min_by(|left, right| left.total_cmp(right))
                .unwrap_or(f64::NAN)
            }
        }
    };
    if !required_ratio.is_finite() || required_ratio < 1.0 {
        return unsupported;
    }
    let target_admissible = composer
        .manifold_path_at_recruitment_scale(&members, required_ratio)
        .is_some_and(|(anchor_loss, escaped, _, _)| escaped == 0.0 && anchor_loss.is_finite());
    let selected_ratio = if target_admissible {
        required_ratio
    } else {
        composer
            .maximum_admissible_recruitment_scale(&members, required_ratio)
            .unwrap_or(1.0)
    };
    let selected_effect = composer
        .manifold_effect_at_scales_for_frames(
            &members,
            None,
            composer.ep("response_frames"),
            selected_ratio,
        )
        .unwrap_or(effect);
    TakeoffRecruitmentProjection {
        supported: true,
        required_ratio,
        selected_ratio,
        residual_ratio: (required_ratio - selected_ratio).max(0.0),
        authorized: selected_ratio > 1.0,
        selected_effect,
    }
}

fn takeoff_recruitment_snapshot(projection: TakeoffRecruitmentProjection) -> Value {
    let mut fields = vec![
        Value::Float(projection.supported as i32 as f64),
        Value::Float(projection.required_ratio),
        Value::Float(projection.selected_ratio),
        Value::Float(projection.residual_ratio),
        Value::Float(projection.authorized as i32 as f64),
    ];
    fields.extend(projection.selected_effect.into_iter().map(Value::Float));
    Value::Tuple(std::sync::Arc::new(fields.into()))
}

/// Project a selected order-N path as one continuous learned shape. The
/// simulator is neither read nor advanced: each segment is synthesized from
/// its receipt-grounded program models, cumulative effects carry across
/// program boundaries, and every boundary is an obligatory audit anchor.
fn future_humanoid_manifold_projection_for_path(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
    policy: NodeID,
    path: NodeID,
    current_transition: Option<NodeID>,
) -> (
    FutureProjectionReport,
    Vec<NodeID>,
    usize,
    Vec<(i32, [f64; 7])>,
) {
    let unsupported = || {
        (
            unsupported_future_projection_report(graph, interner, episode, policy),
            Vec::new(),
            0,
            Vec::new(),
        )
    };
    if fattr(
        graph,
        interner,
        policy,
        "future_manifold_temporal_anchors_enabled",
    ) <= 0.5
    {
        return unsupported();
    }
    let Some(segments) = humanoid_path_segments(graph, interner, path, current_transition) else {
        return unsupported();
    };
    let mut all_models = interner
        .lookup("has_humanoid_phase_action_model")
        .map(|edge| graph.neighbours(episode, Some(edge)))
        .unwrap_or_default();
    if let Some(edge) = interner.lookup("has_humanoid_action_model") {
        for model in graph.neighbours(episode, Some(edge)) {
            if !all_models.contains(&model) {
                all_models.push(model);
            }
        }
    }
    if all_models.is_empty() {
        return unsupported();
    }
    // Retained caregiver models may be attached to programs without being in
    // the episode's endogenous model population. Include those exact learned
    // nodes before constructing the analysis-by-synthesis model.
    if let Some(member_edge) = interner.lookup("includes_humanoid_phase_action_model") {
        for segment in &segments {
            for member in graph.neighbours(segment.program, Some(member_edge)) {
                if fattr(graph, interner, member, "exafferent") > 0.5
                    && !all_models.contains(&member)
                {
                    all_models.push(member);
                }
            }
        }
    }
    let composer = HumanoidComposer::build(graph, interner, episode, policy, &all_models);
    let budget_raw = fattr(graph, interner, policy, "future_manifold_projection_budget");
    let budget = budget_raw.round() as usize;
    if !budget_raw.is_finite()
        || !(2..=64).contains(&budget)
        || (budget_raw - budget as f64).abs() >= f64::EPSILON
    {
        return unsupported();
    }

    let mut cumulative = [0.0f64; 7];
    let mut total_tick = 0i32;
    let mut anchor_count = 0usize;
    let mut effort_members = Vec::new();
    let mut maximum_caregiver_scale = 0.0f64;
    let mut loss = 0.0;
    let mut residual = [0.0; 7];
    let mut retained = [1.0; 7];
    let mut decisive = 0.0;
    let mut projected_trace = Vec::new();

    for segment in &segments {
        let Some((members, historical)) = rebind_humanoid_program_members(
            graph,
            interner,
            &composer,
            &all_models,
            segment.program,
        ) else {
            return unsupported();
        };
        for node in historical {
            // Effort is expenditure through time. Preserve repeated use of a
            // learned member in different programs even though the path's
            // graph membership is set-valued.
            effort_members.push(node);
        }
        maximum_caregiver_scale = maximum_caregiver_scale.max(
            members
                .iter()
                .filter(|index| composer.models[**index].exafferent)
                .map(|index| composer.models[*index].exafferent_scale)
                .fold(0.0, f64::max),
        );
        let Some(effect) = composer.manifold_effect_at_exafferent_scale_for_frames(
            &members,
            None,
            segment.frames as f64,
        ) else {
            return unsupported();
        };
        let Some(anchors) = foveated_segment_anchors(segment.frames) else {
            return unsupported();
        };
        for local_frame in anchors {
            anchor_count += 1;
            if anchor_count > budget {
                return unsupported();
            }
            let projected_tick = total_tick + local_frame;
            let Some(bounds) =
                composer.manifold_bounds(projected_tick as f64, maximum_caregiver_scale)
            else {
                return unsupported();
            };
            let fraction = local_frame as f64 / segment.frames as f64;
            let mut anchor_residual = [0.0; 7];
            let mut projected_values = [0.0; 7];
            for component in 0..7 {
                let projected = cumulative[component] + fraction * effect[component];
                projected_values[component] = projected;
                let excess = projected.abs() - bounds[component];
                if excess > 0.0 {
                    anchor_residual[component] = projected.signum() * excess;
                    retained[component] = 0.0;
                }
            }
            projected_trace.push((projected_tick, projected_values));
            let escaped = anchor_residual
                .iter()
                .filter(|value| **value != 0.0)
                .count() as f64;
            if escaped > 0.0 && loss <= 0.0 {
                loss = escaped;
                residual = anchor_residual;
                decisive = projected_tick as f64;
            }
        }
        for component in 0..7 {
            cumulative[component] += effect[component];
        }
        total_tick = total_tick.saturating_add(segment.frames);
    }

    let horizon = if loss > 0.0 {
        decisive
    } else {
        total_tick as f64
    };
    let safety = learning_safety_evidence(graph, interner, episode);
    let (situated_support, applied_bounds) = support_observability(
        graph,
        interner,
        episode,
        policy,
        horizon,
        true,
        maximum_caregiver_scale,
    );
    let information_authority = situated_support
        .iter()
        .copied()
        .reduce(f64::min)
        .unwrap_or(0.0);
    let information_loss =
        (loss - safety.information_loss_allowance * information_authority).max(0.0);
    let effort_exposure_count = segments.len();
    (
        FutureProjectionReport {
            support: true,
            resolved: true,
            termination_code: if loss > 0.0 { 1.0 } else { 6.0 },
            horizon,
            budget: budget as f64,
            loss,
            information_loss,
            anchor_count: anchor_count as f64,
            refinement_count: 0.0,
            certified_interval_count: if loss > 0.0 {
                anchor_count.saturating_sub(1) as f64
            } else {
                anchor_count as f64
            },
            ambiguous_interval_count: 0.0,
            max_enclosure_width: 0.0,
            max_shape_order: if anchor_count > 1 { 1.0 } else { 0.0 },
            earliest_decisive_tick: decisive,
            minimum_exafferent_scale: 0.0,
            residual,
            retained,
            situated_support,
            applied_bounds,
        },
        effort_members,
        effort_exposure_count,
        projected_trace,
    )
}

fn cached_future_humanoid_manifold_projection_for_members(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
    policy: NodeID,
    member_nodes: &[NodeID],
    observed_program: Option<NodeID>,
) -> FutureProjectionReport {
    let mut all_models = interner
        .lookup("has_humanoid_phase_action_model")
        .map(|edge| graph.neighbours(episode, Some(edge)))
        .unwrap_or_default();
    all_models.sort_unstable();
    let mut members = member_nodes.to_vec();
    members.sort_unstable();
    members.dedup();
    let input_signature = graph.mutation_version();
    let graph_address = graph as *const TypedGraph as usize;
    if let Some(report) = HUMANOID_PROJECTION_CACHE.with(|slot| {
        let slot = slot.borrow();
        slot.as_ref()
            .filter(|cached| {
                cached.graph_address == graph_address
                    && cached.episode == episode
                    && cached.policy == policy
                    && cached.input_signature == input_signature
                    && cached.members == members
                    && cached.observed_program == observed_program
            })
            .map(|cached| cached.report.clone())
    }) {
        return report;
    }
    let report = future_humanoid_manifold_projection_for_members(
        graph,
        interner,
        episode,
        policy,
        &members,
        observed_program,
        true,
    );
    HUMANOID_PROJECTION_CACHE.with(|slot| {
        *slot.borrow_mut() = Some(HumanoidProjectionCache {
            graph_address,
            episode,
            policy,
            input_signature,
            members,
            observed_program,
            report: report.clone(),
        });
    });
    report
}

fn future_humanoid_manifold_projection_for_members(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
    policy: NodeID,
    member_nodes: &[NodeID],
    observed_program: Option<NodeID>,
    calculate_minimum_exafferent_scale: bool,
) -> FutureProjectionReport {
    let mut all_models = interner
        .lookup("has_humanoid_phase_action_model")
        .map(|edge| graph.neighbours(episode, Some(edge)))
        .unwrap_or_default();
    let exafferent_nodes: Vec<NodeID> = member_nodes
        .iter()
        .copied()
        .filter(|node| fattr(graph, interner, *node, "exafferent") > 0.5)
        .collect();
    for node in &exafferent_nodes {
        if !all_models.contains(node) {
            all_models.push(*node);
        }
    }
    let composer = HumanoidComposer::build(graph, interner, episode, policy, &all_models);
    // A retained program names opaque action semantics, not a frozen
    // context-node identity.  Rebind each historical member to the currently
    // active learned phase model with the same token and effector group.
    // HumanoidComposer::active already performs nearest-context selection;
    // this is graph-native model recontextualization, not a plant rollout.
    let members: Vec<usize> = member_nodes
        .iter()
        .filter_map(|node| {
            if fattr(graph, interner, *node, "exafferent") > 0.5 {
                return all_models
                    .iter()
                    .position(|known| known == node)
                    .filter(|index| composer.active(*index));
            }
            let token = sattr(graph, interner, *node, "token");
            let group = fattr(graph, interner, *node, "actuator_group");
            all_models.iter().enumerate().find_map(|(index, known)| {
                (composer.active(index)
                    && sattr(graph, interner, *known, "token") == token
                    && fattr(graph, interner, *known, "actuator_group") == group)
                    .then_some(index)
            })
        })
        .collect();
    let caregiver_counterfactual_scale = members
        .iter()
        .filter(|index| composer.models[**index].exafferent)
        .map(|index| composer.models[*index].exafferent_scale)
        .fold(0.0, f64::max);
    let frames = composer.manifold_foveated_frames();
    let safety = learning_safety_evidence(graph, interner, episode);
    let observed_effect = observed_program.and_then(|program| {
        let keys = HUMANOID_KEYS.map(|key| format!("mean_{key}"));
        // A whole-program receipt is situated evidence.  Member token
        // rebinding alone cannot transport its nonlinear residual across a
        // different support geometry, orientation, task, or response horizon.
        // The producing domain must explicitly publish that identity before
        // the projector may prefer the whole model to pair decomposition.
        let complete_model = fattr(
            graph,
            interner,
            program,
            "whole_program_projection_authority",
        ) > 0.5
            && fattr(graph, interner, program, "receipt_learned") > 0.5
            && fattr(graph, interner, program, "experience_count") > 0.0
            && fattr(graph, interner, program, "member_count") == members.len() as f64
            && members.len() == member_nodes.len()
            && sattr(graph, interner, program, "motor_task_context")
                == sattr(graph, interner, episode, "motor_task_context")
            && fattr(graph, interner, program, "receipt_support_phase")
                == fattr(graph, interner, episode, "current_support_phase")
            && fattr(graph, interner, program, "receipt_orientation_class")
                == fattr(
                    graph,
                    interner,
                    episode,
                    "state_gravity_relative_orientation_class",
                )
            && fattr(graph, interner, program, "receipt_response_frames") > 0.0
            && fattr(graph, interner, program, "receipt_response_frames")
                == fattr(graph, interner, program, "response_frames")
            && keys.iter().all(|key| {
                interner
                    .lookup(key)
                    .is_some_and(|symbol| graph.node(program).attrs.contains_key(&symbol))
            });
        complete_model
            .then(|| std::array::from_fn(|index| fattr(graph, interner, program, &keys[index])))
    });
    let exact_path = if let Some(effect) = observed_effect {
        composer.manifold_path_for_observed_effect(&members, effect)
    } else if members.len() == member_nodes.len() {
        composer.manifold_path(&members)
    } else {
        None
    };
    let uncertain_path = if exact_path.is_none()
        && observed_effect.is_none()
        && members.len() == member_nodes.len()
        && safety.active()
        && persistent_takeoff_development_evidence(graph, interner, episode)
    {
        composer.manifold_path_with_unknown_pairs(&members)
    } else {
        None
    };
    let path = exact_path.or_else(|| {
        uncertain_path.map(|(anchor_loss, escaped, residual, decisive, _)| {
            (anchor_loss, escaped, residual, decisive)
        })
    });
    let unknown_pair_information_loss = uncertain_path
        .map(|(_, _, _, _, unknown_pairs)| unknown_pairs)
        .unwrap_or(0.0);
    // Minimum intervention is part of the same pre-decision projection as
    // the supported path.  Only refine its magnitude when the experiment has
    // explicitly granted the counterfactual gate authority, the endogenous
    // program actually crosses the configured severe-loss threshold, and
    // full learned support preserves a path.  This keeps the answer atomic
    // while avoiding a four-point scale search for observational audits and
    // non-severe actions.
    let counterfactual_authority = fattr(
        graph,
        interner,
        episode,
        "caregiver_support_counterfactual_authority",
    ) > 0.5;
    let counterfactual_loss_floor = fattr(
        graph,
        interner,
        episode,
        "caregiver_support_counterfactual_loss_floor",
    )
    .max(1.0);
    let full_support_preserves_path =
        path.as_ref()
            .is_some_and(|(shape_residual, escaped, _, _)| {
                shape_residual.is_finite() && *escaped <= 0.0
            });
    let endogenous_loss_reaches_floor = if calculate_minimum_exafferent_scale
        && counterfactual_authority
        && caregiver_counterfactual_scale > 0.0
        && members.len() == member_nodes.len()
        && full_support_preserves_path
    {
        let endogenous_members: Vec<usize> = members
            .iter()
            .copied()
            .filter(|index| !composer.models[*index].exafferent)
            .collect();
        composer
            .manifold_path(&endogenous_members)
            .is_some_and(|(_, escaped, _, _)| escaped >= counterfactual_loss_floor)
    } else {
        false
    };
    let minimum_exafferent_scale =
        if calculate_minimum_exafferent_scale && endogenous_loss_reaches_floor {
            [0.25, 0.5, 0.75, 1.0]
                .into_iter()
                .find(|scale| {
                    composer
                        .manifold_path_at_exafferent_scale(&members, Some(*scale))
                        .is_some_and(|(shape_residual, escaped, _, _)| {
                            shape_residual.is_finite() && escaped <= 0.0
                        })
                })
                .unwrap_or(0.0)
        } else {
            0.0
        };
    let horizon = frames
        .as_ref()
        .and_then(|anchors| anchors.last().copied())
        .unwrap_or(0.0);
    let situated_support = situation_support_field(
        graph,
        interner,
        episode,
        policy,
        horizon,
        true,
        caregiver_counterfactual_scale,
    );
    let information_authority = situated_support
        .weights
        .iter()
        .copied()
        .reduce(f64::min)
        .unwrap_or(0.0);
    let (support, resolved, loss, shape_information_loss, termination_code, residual, decisive) =
        match path {
            Some((shape_residual, escaped, residual, decisive)) if shape_residual.is_finite() => {
                (true, true, escaped, escaped, 6.0, residual, decisive)
            }
            Some((_shape_residual, escaped, residual, decisive)) if escaped > 0.0 => {
                (true, true, escaped, escaped, 1.0, residual, decisive)
            }
            _ => (false, false, 0.0, 0.0, 4.0, [0.0; 7], 0.0),
        };
    let raw_information_loss = shape_information_loss + unknown_pair_information_loss;
    let information_loss =
        (raw_information_loss - safety.information_loss_allowance * information_authority).max(0.0);
    let anchor_count = frames.as_ref().map_or(0.0, |anchors| anchors.len() as f64);
    let retained_value = if support && loss <= 0.0 { 1.0 } else { 0.0 };
    let (report_support, applied_bounds) = support_observability(
        graph,
        interner,
        episode,
        policy,
        horizon,
        true,
        caregiver_counterfactual_scale,
    );
    FutureProjectionReport {
        support,
        resolved,
        termination_code,
        horizon,
        budget: fattr(graph, interner, policy, "future_manifold_projection_budget"),
        loss,
        information_loss,
        anchor_count,
        refinement_count: 0.0,
        certified_interval_count: if support && loss <= 0.0 {
            anchor_count
        } else {
            0.0
        },
        ambiguous_interval_count: 0.0,
        max_enclosure_width: 0.0,
        max_shape_order: if anchor_count > 1.0 { 1.0 } else { 0.0 },
        earliest_decisive_tick: decisive,
        minimum_exafferent_scale,
        residual,
        retained: [retained_value; 7],
        situated_support: report_support,
        applied_bounds,
    }
}

#[derive(Clone)]
struct ProjectionState {
    context: [f64; 4],
    positions: Vec<f64>,
    reference_positions: Vec<f64>,
}

/// Graph-published recovery evidence consumed by the native risk gate.  A
/// missing or unverified context is the exact historical behavior.  The
/// declared relaxation budgets are in the same units as the manifold bounds;
/// no host-side multiplier is introduced here.
#[derive(Clone, Copy, Default)]
struct LearningSafetyEvidence {
    verified: bool,
    reset_reachable: bool,
    reset_cost_units: f64,
    protective_support_available: bool,
    protective_support_effectiveness: f64,
    required_horizon_units: i32,
    minimum_width_relaxation: f64,
    information_loss_allowance: f64,
    recovery_path_count: f64,
}

impl LearningSafetyEvidence {
    fn active(self) -> bool {
        self.verified
    }

    fn recovery_boundary_available(self) -> bool {
        self.verified
            && (self.reset_reachable
                || (self.protective_support_available
                    && self.protective_support_effectiveness > 0.0))
    }

    fn bound(self, base: f64, situated_support: f64) -> f64 {
        base + self.minimum_width_relaxation * situated_support.clamp(0.0, 1.0)
    }
}

/// Dimension-specific recoverability of the future set at a projected time.
///
/// A safe-learning declaration only makes the declared budgets available. It
/// does not itself widen the manifold.  Widening is earned from the body's
/// current load-bearing contacts, upright margin, independently reachable
/// recovery paths, reset latency, and caregiver effectiveness.  Contact-bound
/// support decays outside the graph-declared near horizon; reset and caregiver
/// paths remain available because they describe futures rather than the
/// current pose.
#[derive(Clone, Copy, Default)]
struct SituationSupportField {
    weights: [f64; 7],
}

fn support_union(a: f64, b: f64) -> f64 {
    1.0 - (1.0 - a.clamp(0.0, 1.0)) * (1.0 - b.clamp(0.0, 1.0))
}

fn situation_support_field(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
    policy: NodeID,
    projected_tick: f64,
    humanoid_axes: bool,
    caregiver_counterfactual_scale: f64,
) -> SituationSupportField {
    let safety = learning_safety_evidence(graph, interner, episode);
    if !safety.active() {
        return SituationSupportField::default();
    }

    let support_0 = fattr(graph, interner, episode, "state_support_0_force").max(0.0);
    let support_1 = fattr(graph, interner, episode, "state_support_1_force").max(0.0);
    let observed_supports = (support_0 > 0.0) as u8 as f64 + (support_1 > 0.0) as u8 as f64;
    let active_supports =
        fattr(graph, interner, episode, "active_support_count").max(observed_supports);
    let sensor_count = fattr(graph, interner, episode, "support_sensor_count")
        .max(observed_supports)
        .max(1.0);
    let topology = (active_supports / sensor_count).clamp(0.0, 1.0);

    let body_weight = fattr(graph, interner, episode, "body_mass")
        * fattr(graph, interner, policy, "gravity_acceleration");
    let total_force =
        fattr(graph, interner, episode, "state_contact_force_newtons").max(support_0 + support_1);
    let load_bearing = if body_weight.is_finite() && body_weight > 0.0 {
        (total_force / body_weight).clamp(0.0, 1.0)
    } else {
        topology
    };

    let qx = fattr(graph, interner, episode, "state_qx");
    let qy = fattr(graph, interner, episode, "state_qy");
    let upright_margin = (1.0 - 2.0 * (qx * qx + qy * qy)).clamp(0.0, 1.0);
    let near_horizon = safety.required_horizon_units.max(1) as f64;
    let temporal_persistence = (near_horizon / projected_tick.max(near_horizon)).clamp(0.0, 1.0);

    let path_count = safety.recovery_path_count.max(
        safety.reset_reachable as u8 as f64 + safety.protective_support_available as u8 as f64,
    );
    let path_diversity = if path_count > 0.0 {
        path_count / (path_count + 1.0)
    } else {
        0.0
    };
    let reset_recovery = if safety.reset_reachable {
        projected_tick.max(near_horizon)
            / (projected_tick.max(near_horizon) + safety.reset_cost_units)
    } else {
        0.0
    };
    let caregiver_engaged = caregiver_counterfactual_scale > 0.0
        || fattr(
            graph,
            interner,
            episode,
            "caregiver_protective_support_requested",
        ) > 0.5
        || fattr(
            graph,
            interner,
            episode,
            "caregiver_scaffold_session_active",
        ) > 0.5;
    let caregiver = if safety.protective_support_available && caregiver_engaged {
        safety.protective_support_effectiveness
            * if caregiver_counterfactual_scale > 0.0 {
                caregiver_counterfactual_scale.clamp(0.0, 1.0)
            } else {
                let enacted_scale = fattr(graph, interner, episode, "caregiver_support_scale");
                if enacted_scale > 0.0 {
                    enacted_scale.clamp(0.0, 1.0)
                } else {
                    // Binary request evidence predates explicit magnitude and
                    // therefore retains its historical full-support meaning.
                    1.0
                }
            }
    } else {
        0.0
    };
    let persistent_recovery = support_union(caregiver, reset_recovery * path_diversity);
    let horizontal = support_union(persistent_recovery, topology * temporal_persistence);
    let vertical = support_union(
        persistent_recovery,
        topology.max(load_bearing) * temporal_persistence,
    );
    let orientation = support_union(
        persistent_recovery,
        topology * upright_margin * temporal_persistence,
    );

    let weights = if humanoid_axes {
        [
            orientation,
            orientation,
            orientation,
            orientation,
            horizontal,
            horizontal,
            vertical,
        ]
    } else {
        [
            horizontal,
            horizontal,
            vertical,
            orientation,
            orientation,
            orientation,
            vertical,
        ]
    };
    SituationSupportField { weights }
}

fn protected_support_authority(
    graph: &TypedGraph,
    interner: &Interner,
    policy: NodeID,
    field: SituationSupportField,
) -> f64 {
    COMPONENTS
        .iter()
        .enumerate()
        .filter(|(_, key)| fattr(graph, interner, policy, &format!("{key}_weight")) > 0.0)
        .map(|(index, _)| field.weights[index])
        .reduce(f64::min)
        .unwrap_or(0.0)
}

fn learning_safety_evidence(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
) -> LearningSafetyEvidence {
    let Some(edge) = interner.lookup("has_learning_safety_context") else {
        return LearningSafetyEvidence::default();
    };
    let Some(context) = graph.neighbours(episode, Some(edge)).into_iter().next() else {
        return LearningSafetyEvidence::default();
    };
    let evidence = LearningSafetyEvidence {
        verified: fattr(graph, interner, context, "verified") > 0.5,
        reset_reachable: fattr(graph, interner, context, "reset_reachable") > 0.5,
        reset_cost_units: fattr(graph, interner, context, "reset_cost_units"),
        protective_support_available: fattr(
            graph,
            interner,
            context,
            "protective_support_available",
        ) > 0.5,
        protective_support_effectiveness: fattr(
            graph,
            interner,
            context,
            "protective_support_effectiveness",
        )
        .clamp(0.0, 1.0),
        required_horizon_units: fattr(graph, interner, context, "required_horizon_units")
            .max(0.0)
            .round() as i32,
        minimum_width_relaxation: {
            let budget = fattr(graph, interner, context, "exploration_width_budget");
            if budget > 0.0 {
                budget
            } else {
                fattr(graph, interner, context, "minimum_width_relaxation")
            }
            .max(0.0)
        },
        information_loss_allowance: {
            let budget = fattr(graph, interner, context, "exploration_information_budget");
            if budget > 0.0 {
                budget
            } else {
                fattr(graph, interner, context, "information_loss_allowance")
            }
            .max(0.0)
        },
        recovery_path_count: fattr(graph, interner, context, "recovery_path_count").max(0.0),
    };
    if evidence.reset_cost_units.is_finite()
        && evidence.reset_cost_units >= 0.0
        && evidence.required_horizon_units >= 1
    {
        evidence
    } else {
        LearningSafetyEvidence::default()
    }
}

struct ProjectionIntervalResult {
    end_state: ProjectionState,
    loss: Option<(i32, usize)>,
    certified: bool,
    ambiguous: bool,
    finite: bool,
    width: f64,
    retained: [f64; 7],
    /// Signed, guaranteed excess beyond the allowed tube for each component.
    residual: [f64; 7],
}

fn projection_state_finite(state: &ProjectionState) -> bool {
    state.context.iter().all(|value| value.is_finite())
        && state.positions.iter().all(|value| value.is_finite())
        && state
            .reference_positions
            .iter()
            .all(|value| value.is_finite())
}

fn projection_step_state(
    graph: &TypedGraph,
    interner: &Interner,
    _policy: NodeID,
    state: &mut ProjectionState,
    references: &[NodeID],
    members: &[NodeID],
) -> bool {
    let old_context = state.context;
    let mut baseline_delta = [0.0f64; 4];
    for j in 0..4 {
        if !references.is_empty() {
            baseline_delta[j] = references
                .iter()
                .map(|m| {
                    let mut delta = fattr(
                        graph,
                        interner,
                        *m,
                        &format!("mean_context_delta_{}", FLOW_FEATURES[j]),
                    );
                    for k in 0..4 {
                        delta += fattr(
                            graph,
                            interner,
                            *m,
                            &format!(
                                "context_delta_gain_{}_{}",
                                FLOW_FEATURES[j], FLOW_FEATURES[k]
                            ),
                        ) * (old_context[k]
                            - fattr(graph, interner, *m, &format!("mean_{}", FLOW_FEATURES[k])));
                    }
                    delta
                })
                .sum::<f64>()
                / references.len() as f64;
        }
    }
    for j in 0..4 {
        let member_delta: f64 = members
            .iter()
            .map(|m| {
                if fattr(graph, interner, *m, "context_delta_experience_count") <= 0.0 {
                    return 0.0;
                }
                let mut delta = fattr(
                    graph,
                    interner,
                    *m,
                    &format!("mean_context_delta_{}", FLOW_FEATURES[j]),
                );
                for k in 0..4 {
                    delta += fattr(
                        graph,
                        interner,
                        *m,
                        &format!(
                            "context_delta_gain_{}_{}",
                            FLOW_FEATURES[j], FLOW_FEATURES[k]
                        ),
                    ) * (old_context[k]
                        - fattr(graph, interner, *m, &format!("mean_{}", FLOW_FEATURES[k])));
                }
                delta - baseline_delta[j]
            })
            .sum();
        state.context[j] = old_context[j] + baseline_delta[j] + member_delta;
    }

    for (i, m) in members.iter().enumerate() {
        let max_change = fattr(
            graph,
            interner,
            *m,
            "specified_maximum_position_change_per_action",
        );
        let target = fattr(graph, interner, *m, "specified_command_level");
        if !max_change.is_finite() || !target.is_finite() {
            return false;
        }
        let error = target - state.positions[i];
        state.positions[i] += if error.abs() > max_change {
            if error > 0.0 {
                max_change
            } else {
                -max_change
            }
        } else {
            error
        };
    }
    for (i, m) in references.iter().enumerate() {
        let max_change = fattr(
            graph,
            interner,
            *m,
            "specified_maximum_position_change_per_action",
        );
        let target = fattr(graph, interner, *m, "specified_command_level");
        if !max_change.is_finite() || !target.is_finite() {
            return false;
        }
        let error = target - state.reference_positions[i];
        state.reference_positions[i] += if error.abs() > max_change {
            if error > 0.0 {
                max_change
            } else {
                -max_change
            }
        } else {
            error
        };
    }
    projection_state_finite(state)
}

fn projection_predictions(
    graph: &TypedGraph,
    interner: &Interner,
    _episode: NodeID,
    policy: NodeID,
    state: &ProjectionState,
    references: &[NodeID],
    members: &[NodeID],
) -> Option<[f64; 7]> {
    let contextual = fattr(
        graph,
        interner,
        policy,
        "contextual_effector_prediction_enabled",
    ) > 0.5;
    let mut predicted = [0.0f64; 7];
    for (ci, key) in COMPONENTS.iter().enumerate() {
        if fattr(graph, interner, policy, &format!("{key}_weight")) <= 0.0 {
            continue;
        }
        let predict = |m: NodeID, pos: f64| -> f64 {
            let specified = fattr(graph, interner, m, "specified_actuator_dynamics_enabled") > 0.5
                && fattr(graph, interner, m, "specified_effect_prior_confidence") > 0.5
                && fattr(
                    graph,
                    interner,
                    m,
                    "specified_maximum_position_change_per_action",
                ) > 0.0;
            if specified {
                return fattr(graph, interner, m, &format!("specified_passive_mean_{key}"))
                    + fattr(
                        graph,
                        interner,
                        m,
                        &format!("specified_position_gain_{key}"),
                    ) * pos;
            }
            let mut learned = fattr(graph, interner, m, &format!("mean_{key}"));
            if contextual {
                learned += fattr(graph, interner, m, &format!("flow_gain_{key}"))
                    * (state.context[0] * state.context[0]
                        + state.context[1] * state.context[1]
                        + state.context[2] * state.context[2]
                        - fattr(graph, interner, m, "mean_flow_speed_squared"));
                for j in 0..4 {
                    learned += fattr(
                        graph,
                        interner,
                        m,
                        &format!("{}_gain_{}", FLOW_FEATURES[j], key),
                    ) * (state.context[j]
                        - fattr(graph, interner, m, &format!("mean_{}", FLOW_FEATURES[j])));
                }
            }
            learned
        };
        let baseline = references
            .iter()
            .enumerate()
            .map(|(ri, m)| predict(*m, state.reference_positions[ri]))
            .sum::<f64>()
            / references.len().max(1) as f64;
        predicted[ci] = baseline
            + members
                .iter()
                .enumerate()
                .map(|(i, m)| predict(*m, state.positions[i]) - baseline)
                .sum::<f64>();
    }
    if predicted.iter().all(|value| value.is_finite()) {
        Some(predicted)
    } else {
        None
    }
}

fn projection_context_once(
    graph: &TypedGraph,
    interner: &Interner,
    old_context: [f64; 4],
    _policy: NodeID,
    references: &[NodeID],
    members: &[NodeID],
) -> [f64; 4] {
    let mut next = old_context;
    let mut baseline_delta = [0.0f64; 4];
    for j in 0..4 {
        baseline_delta[j] = references
            .iter()
            .map(|m| {
                let mut delta = fattr(
                    graph,
                    interner,
                    *m,
                    &format!("mean_context_delta_{}", FLOW_FEATURES[j]),
                );
                for k in 0..4 {
                    delta += fattr(
                        graph,
                        interner,
                        *m,
                        &format!(
                            "context_delta_gain_{}_{}",
                            FLOW_FEATURES[j], FLOW_FEATURES[k]
                        ),
                    ) * (old_context[k]
                        - fattr(graph, interner, *m, &format!("mean_{}", FLOW_FEATURES[k])));
                }
                delta
            })
            .sum::<f64>()
            / references.len().max(1) as f64;
    }
    for j in 0..4 {
        let member_delta: f64 = members
            .iter()
            .map(|m| {
                if fattr(graph, interner, *m, "context_delta_experience_count") <= 0.0 {
                    return 0.0;
                }
                let mut delta = fattr(
                    graph,
                    interner,
                    *m,
                    &format!("mean_context_delta_{}", FLOW_FEATURES[j]),
                );
                for k in 0..4 {
                    delta += fattr(
                        graph,
                        interner,
                        *m,
                        &format!(
                            "context_delta_gain_{}_{}",
                            FLOW_FEATURES[j], FLOW_FEATURES[k]
                        ),
                    ) * (old_context[k]
                        - fattr(graph, interner, *m, &format!("mean_{}", FLOW_FEATURES[k])));
                }
                delta - baseline_delta[j]
            })
            .sum();
        next[j] = old_context[j] + baseline_delta[j] + member_delta;
    }
    next
}

fn projection_affine_compose(
    left_matrix: [[f64; 4]; 4],
    left_bias: [f64; 4],
    right_matrix: [[f64; 4]; 4],
    right_bias: [f64; 4],
) -> ([[f64; 4]; 4], [f64; 4]) {
    let mut matrix = [[0.0; 4]; 4];
    let mut bias = left_bias;
    for row in 0..4 {
        for col in 0..4 {
            matrix[row][col] = (0..4)
                .map(|k| left_matrix[row][k] * right_matrix[k][col])
                .sum();
        }
        bias[row] += (0..4)
            .map(|k| left_matrix[row][k] * right_bias[k])
            .sum::<f64>();
    }
    (matrix, bias)
}

fn projection_affine_power(
    matrix: [[f64; 4]; 4],
    bias: [f64; 4],
    mut exponent: i32,
) -> ([[f64; 4]; 4], [f64; 4]) {
    let mut result_matrix = [[0.0; 4]; 4];
    for i in 0..4 {
        result_matrix[i][i] = 1.0;
    }
    let mut result_bias = [0.0; 4];
    let mut base_matrix = matrix;
    let mut base_bias = bias;
    while exponent > 0 {
        if exponent & 1 == 1 {
            (result_matrix, result_bias) =
                projection_affine_compose(base_matrix, base_bias, result_matrix, result_bias);
        }
        exponent >>= 1;
        if exponent > 0 {
            (base_matrix, base_bias) =
                projection_affine_compose(base_matrix, base_bias, base_matrix, base_bias);
        }
    }
    (result_matrix, result_bias)
}

fn projection_position_jump(
    position: f64,
    target: f64,
    max_change: f64,
    ticks: i32,
) -> Option<(f64, (f64, f64))> {
    if !position.is_finite() || !target.is_finite() || !max_change.is_finite() {
        return None;
    }
    if max_change <= 0.0 || (target - position).abs() <= f64::EPSILON {
        return Some((position, (position, position)));
    }
    let error = target - position;
    let required_steps = (error.abs() / max_change).ceil() as i32;
    let steps = required_steps.min(ticks);
    // The dense recurrence clamps the final increment to the target.  A
    // closed-form jump must preserve that behavior for non-multiple errors
    // (e.g. position=.5, target=1.0, max_change=1.0).
    let end = if steps >= required_steps {
        target
    } else {
        position + error.signum() * max_change * steps as f64
    };
    Some((end, (position.min(end), position.max(end))))
}

fn projection_interval_add(left: (f64, f64), right: (f64, f64)) -> (f64, f64) {
    (left.0 + right.0, left.1 + right.1)
}

fn projection_interval_scale(interval: (f64, f64), scale: f64) -> (f64, f64) {
    if scale >= 0.0 {
        (interval.0 * scale, interval.1 * scale)
    } else {
        (interval.1 * scale, interval.0 * scale)
    }
}

fn projection_interval_square(interval: (f64, f64)) -> (f64, f64) {
    let upper = interval.0.abs().max(interval.1.abs()).powi(2);
    let lower = if interval.0 <= 0.0 && interval.1 >= 0.0 {
        0.0
    } else {
        interval.0.powi(2).min(interval.1.powi(2))
    };
    (lower, upper)
}

fn projection_prediction_intervals(
    graph: &TypedGraph,
    interner: &Interner,
    policy: NodeID,
    context: &[(f64, f64); 4],
    positions: &[(f64, f64)],
    reference_positions: &[(f64, f64)],
    references: &[NodeID],
    members: &[NodeID],
) -> Option<[(f64, f64); 7]> {
    let contextual = fattr(
        graph,
        interner,
        policy,
        "contextual_effector_prediction_enabled",
    ) > 0.5;
    let mut predicted = [(0.0, 0.0); 7];
    for (ci, key) in COMPONENTS.iter().enumerate() {
        if fattr(graph, interner, policy, &format!("{key}_weight")) <= 0.0 {
            continue;
        }
        let predict = |model: NodeID, position: (f64, f64)| -> (f64, f64) {
            let specified = fattr(
                graph,
                interner,
                model,
                "specified_actuator_dynamics_enabled",
            ) > 0.5
                && fattr(graph, interner, model, "specified_effect_prior_confidence") > 0.5
                && fattr(
                    graph,
                    interner,
                    model,
                    "specified_maximum_position_change_per_action",
                ) > 0.0;
            if specified {
                return projection_interval_add(
                    (
                        fattr(
                            graph,
                            interner,
                            model,
                            &format!("specified_passive_mean_{key}"),
                        ),
                        fattr(
                            graph,
                            interner,
                            model,
                            &format!("specified_passive_mean_{key}"),
                        ),
                    ),
                    projection_interval_scale(
                        position,
                        fattr(
                            graph,
                            interner,
                            model,
                            &format!("specified_position_gain_{key}"),
                        ),
                    ),
                );
            }
            let mut value = (
                fattr(graph, interner, model, &format!("mean_{key}")),
                fattr(graph, interner, model, &format!("mean_{key}")),
            );
            if contextual {
                let speed = projection_interval_add(
                    projection_interval_square(context[0]),
                    projection_interval_add(
                        projection_interval_square(context[1]),
                        projection_interval_square(context[2]),
                    ),
                );
                value = projection_interval_add(
                    value,
                    projection_interval_scale(
                        projection_interval_add(
                            speed,
                            (
                                -fattr(graph, interner, model, "mean_flow_speed_squared"),
                                -fattr(graph, interner, model, "mean_flow_speed_squared"),
                            ),
                        ),
                        fattr(graph, interner, model, &format!("flow_gain_{key}")),
                    ),
                );
                for j in 0..4 {
                    value = projection_interval_add(
                        value,
                        projection_interval_scale(
                            (
                                context[j].0
                                    - fattr(
                                        graph,
                                        interner,
                                        model,
                                        &format!("mean_{}", FLOW_FEATURES[j]),
                                    ),
                                context[j].1
                                    - fattr(
                                        graph,
                                        interner,
                                        model,
                                        &format!("mean_{}", FLOW_FEATURES[j]),
                                    ),
                            ),
                            fattr(
                                graph,
                                interner,
                                model,
                                &format!("{}_gain_{}", FLOW_FEATURES[j], key),
                            ),
                        ),
                    );
                }
            }
            value
        };
        let baseline = references
            .iter()
            .enumerate()
            .map(|(i, model)| predict(*model, reference_positions[i]))
            .fold((0.0, 0.0), projection_interval_add);
        let baseline = (
            baseline.0 / references.len().max(1) as f64,
            baseline.1 / references.len().max(1) as f64,
        );
        let mut value = baseline;
        for (i, model) in members.iter().enumerate() {
            value = projection_interval_add(
                value,
                projection_interval_add(
                    predict(*model, positions[i]),
                    projection_interval_scale(baseline, -1.0),
                ),
            );
        }
        predicted[ci] = value;
    }
    if predicted
        .iter()
        .all(|(lo, hi)| lo.is_finite() && hi.is_finite())
    {
        Some(predicted)
    } else {
        None
    }
}

fn projection_certify_interval_sparse(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
    policy: NodeID,
    start_tick: i32,
    end_tick: i32,
    start_state: &ProjectionState,
    references: &[NodeID],
    members: &[NodeID],
) -> ProjectionIntervalResult {
    let safety = learning_safety_evidence(graph, interner, episode);
    let situated_support = situation_support_field(
        graph,
        interner,
        episode,
        policy,
        end_tick as f64,
        false,
        0.0,
    );
    let ticks = end_tick - start_tick;
    if ticks == 1 {
        let mut end_state = start_state.clone();
        let step_valid =
            projection_step_state(graph, interner, policy, &mut end_state, references, members);
        if !step_valid || !projection_state_finite(&end_state) {
            return ProjectionIntervalResult {
                end_state,
                loss: None,
                certified: false,
                ambiguous: false,
                finite: false,
                width: f64::INFINITY,
                retained: [0.0; 7],
                residual: [0.0; 7],
            };
        }
        let Some(predicted) = projection_predictions(
            graph, interner, episode, policy, &end_state, references, members,
        ) else {
            return ProjectionIntervalResult {
                end_state,
                loss: None,
                certified: false,
                ambiguous: false,
                finite: false,
                width: f64::INFINITY,
                retained: [0.0; 7],
                residual: [0.0; 7],
            };
        };
        let mut retained = [0.0; 7];
        let mut shape_residual = [0.0; 7];
        let mut loss = None;
        for ci in 0..7 {
            if fattr(
                graph,
                interner,
                policy,
                &format!("{}_weight", COMPONENTS[ci]),
            ) <= 0.0
            {
                continue;
            }
            let delta = predicted[ci]
                - fattr(
                    graph,
                    interner,
                    episode,
                    &format!("target_{}", COMPONENTS[ci]),
                );
            let bound = safety.bound(
                fattr(
                    graph,
                    interner,
                    episode,
                    &format!("manifold_bound_{}", COMPONENTS[ci]),
                ),
                situated_support.weights[ci],
            );
            let excess = delta.abs() - bound;
            if excess > 0.0 {
                shape_residual[ci] = delta.signum() * excess;
                loss = Some((end_tick, loss.map_or(1, |(_, count)| count + 1)));
            } else {
                retained[ci] = 1.0;
            }
        }
        return ProjectionIntervalResult {
            end_state,
            loss,
            certified: loss.is_none(),
            ambiguous: false,
            finite: true,
            width: 0.0,
            retained,
            residual: shape_residual,
        };
    }
    let mut affine = [[0.0; 4]; 4];
    let zero = [0.0; 4];
    let origin = projection_context_once(graph, interner, zero, policy, references, members);
    let bias = origin;
    for col in 0..4 {
        let mut basis = [0.0; 4];
        basis[col] = 1.0;
        let image = projection_context_once(graph, interner, basis, policy, references, members);
        for row in 0..4 {
            affine[row][col] = image[row] - origin[row];
        }
    }
    if !affine.iter().flatten().all(|value| value.is_finite())
        || !bias.iter().all(|value| value.is_finite())
    {
        return ProjectionIntervalResult {
            end_state: start_state.clone(),
            loss: None,
            certified: false,
            ambiguous: false,
            finite: false,
            width: f64::INFINITY,
            retained: [0.0; 7],
            residual: [0.0; 7],
        };
    }
    let (power, jump_bias) = projection_affine_power(affine, bias, ticks);
    let mut end_context = jump_bias;
    for row in 0..4 {
        end_context[row] += (0..4)
            .map(|col| power[row][col] * start_state.context[col])
            .sum::<f64>();
    }
    let norm_a = affine
        .iter()
        .map(|row| row.iter().map(|value| value.abs()).sum::<f64>())
        .fold(0.0, f64::max);
    let norm_x = start_state
        .context
        .iter()
        .map(|value| value.abs())
        .fold(0.0, f64::max);
    let norm_b = bias.iter().map(|value| value.abs()).fold(0.0, f64::max);
    let power_norm = norm_a.powi(ticks).max(1.0);
    let geometric = if (norm_a - 1.0).abs() < f64::EPSILON {
        ticks as f64
    } else if norm_a < 1.0 {
        1.0 / (1.0 - norm_a)
    } else {
        (norm_a.powi(ticks) - 1.0) / (norm_a - 1.0)
    };
    let radius = power_norm * norm_x + geometric * norm_b;
    if !end_context.iter().all(|value| value.is_finite()) || !radius.is_finite() {
        return ProjectionIntervalResult {
            end_state: start_state.clone(),
            loss: None,
            certified: false,
            ambiguous: false,
            finite: false,
            width: f64::INFINITY,
            retained: [0.0; 7],
            residual: [0.0; 7],
        };
    }
    let context_bounds = [(0.0 - radius, radius); 4];
    let mut positions = Vec::with_capacity(members.len());
    let mut position_bounds = Vec::with_capacity(members.len());
    for (i, model) in members.iter().enumerate() {
        let Some((end, bounds)) = projection_position_jump(
            start_state.positions[i],
            fattr(graph, interner, *model, "specified_command_level"),
            fattr(
                graph,
                interner,
                *model,
                "specified_maximum_position_change_per_action",
            ),
            ticks,
        ) else {
            return ProjectionIntervalResult {
                end_state: start_state.clone(),
                loss: None,
                certified: false,
                ambiguous: false,
                finite: false,
                width: f64::INFINITY,
                retained: [0.0; 7],
                residual: [0.0; 7],
            };
        };
        positions.push(end);
        position_bounds.push(bounds);
    }
    let mut reference_bounds = Vec::with_capacity(references.len());
    let mut reference_positions = Vec::with_capacity(references.len());
    for (i, model) in references.iter().enumerate() {
        let Some((end, bounds)) = projection_position_jump(
            start_state.reference_positions[i],
            fattr(graph, interner, *model, "specified_command_level"),
            fattr(
                graph,
                interner,
                *model,
                "specified_maximum_position_change_per_action",
            ),
            ticks,
        ) else {
            return ProjectionIntervalResult {
                end_state: start_state.clone(),
                loss: None,
                certified: false,
                ambiguous: false,
                finite: false,
                width: f64::INFINITY,
                retained: [0.0; 7],
                residual: [0.0; 7],
            };
        };
        reference_bounds.push(bounds);
        reference_positions.push(end);
    }
    let Some(predicted) = projection_prediction_intervals(
        graph,
        interner,
        policy,
        &context_bounds,
        &position_bounds,
        &reference_bounds,
        references,
        members,
    ) else {
        return ProjectionIntervalResult {
            end_state: start_state.clone(),
            loss: None,
            certified: false,
            ambiguous: false,
            finite: false,
            width: f64::INFINITY,
            retained: [0.0; 7],
            residual: [0.0; 7],
        };
    };
    let mut retained = [0.0; 7];
    let mut shape_residual = [0.0; 7];
    let mut loss = None;
    let mut ambiguous = false;
    let mut width: f64 = 0.0;
    for ci in 0..7 {
        if fattr(
            graph,
            interner,
            policy,
            &format!("{}_weight", COMPONENTS[ci]),
        ) <= 0.0
        {
            continue;
        }
        let target = fattr(
            graph,
            interner,
            episode,
            &format!("target_{}", COMPONENTS[ci]),
        );
        let bound = safety.bound(
            fattr(
                graph,
                interner,
                episode,
                &format!("manifold_bound_{}", COMPONENTS[ci]),
            ),
            situated_support.weights[ci],
        );
        let (lo, hi) = predicted[ci];
        width = width.max(hi - lo);
        let residual_lo = if target < lo {
            (target - lo).abs()
        } else if target > hi {
            (target - hi).abs()
        } else {
            0.0
        };
        let residual_hi = (target - lo).abs().max((target - hi).abs());
        if residual_lo > bound {
            shape_residual[ci] = if lo > target {
                lo - target - bound
            } else {
                hi - target + bound
            };
            loss = Some((start_tick + 1, loss.map_or(1, |(_, count)| count + 1)));
        } else if residual_hi <= bound {
            retained[ci] = 1.0;
        } else {
            ambiguous = true;
        }
    }
    ProjectionIntervalResult {
        end_state: ProjectionState {
            context: end_context,
            positions,
            reference_positions,
        },
        loss,
        certified: !ambiguous && loss.is_none(),
        ambiguous,
        finite: true,
        width,
        retained,
        residual: shape_residual,
    }
}

fn projection_certify_interval(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
    policy: NodeID,
    start_tick: i32,
    end_tick: i32,
    start_state: &ProjectionState,
    references: &[NodeID],
    members: &[NodeID],
) -> ProjectionIntervalResult {
    return projection_certify_interval_sparse(
        graph,
        interner,
        episode,
        policy,
        start_tick,
        end_tick,
        start_state,
        references,
        members,
    );
}

#[allow(dead_code)]
fn projection_certify_interval_legacy(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
    policy: NodeID,
    start_tick: i32,
    end_tick: i32,
    start_state: &ProjectionState,
    references: &[NodeID],
    members: &[NodeID],
) -> ProjectionIntervalResult {
    let safety = learning_safety_evidence(graph, interner, episode);
    let situated_support = situation_support_field(
        graph,
        interner,
        episode,
        policy,
        end_tick as f64,
        false,
        0.0,
    );
    let mut state = start_state.clone();
    let mut minima = [f64::INFINITY; 7];
    let mut maxima = [f64::NEG_INFINITY; 7];
    let mut retained = [0.0f64; 7];
    let mut finite = true;
    for _ in (start_tick + 1)..=end_tick {
        projection_step_state(graph, interner, policy, &mut state, references, members);
        if !projection_state_finite(&state) {
            finite = false;
            break;
        }
        let Some(predicted) = projection_predictions(
            graph, interner, episode, policy, &state, references, members,
        ) else {
            finite = false;
            break;
        };
        for ci in 0..7 {
            minima[ci] = minima[ci].min(predicted[ci]);
            maxima[ci] = maxima[ci].max(predicted[ci]);
        }
    }
    let width = if finite {
        minima
            .iter()
            .zip(maxima.iter())
            .enumerate()
            .filter(|(i, _)| {
                fattr(
                    graph,
                    interner,
                    policy,
                    &format!("{}_weight", COMPONENTS[*i]),
                ) > 0.0
            })
            .map(|(_, (lo, hi))| hi - lo)
            .fold(0.0, f64::max)
    } else {
        f64::INFINITY
    };
    if !finite {
        return ProjectionIntervalResult {
            end_state: state,
            loss: None,
            certified: false,
            ambiguous: false,
            finite: false,
            width,
            retained,
            residual: [0.0; 7],
        };
    }

    let exact = end_tick - start_tick == 1;
    let mut certain_loss: Option<(i32, usize)> = None;
    let mut ambiguous = false;
    for ci in 0..7 {
        if fattr(
            graph,
            interner,
            policy,
            &format!("{}_weight", COMPONENTS[ci]),
        ) <= 0.0
        {
            continue;
        }
        let target = fattr(
            graph,
            interner,
            episode,
            &format!("target_{}", COMPONENTS[ci]),
        );
        let bound = safety.bound(
            fattr(
                graph,
                interner,
                episode,
                &format!("manifold_bound_{}", COMPONENTS[ci]),
            ),
            situated_support.weights[ci],
        );
        let residual_lo = if target < minima[ci] {
            (target - minima[ci]).abs()
        } else if target > maxima[ci] {
            (target - maxima[ci]).abs()
        } else {
            0.0
        };
        let residual_hi = (target - minima[ci]).abs().max((target - maxima[ci]).abs());
        if exact {
            if residual_hi > bound {
                let tick = end_tick;
                let count = certain_loss.map_or(1, |(_, count)| count + 1);
                certain_loss = Some((tick, count));
            } else {
                retained[ci] = 1.0;
            }
        } else if residual_lo > bound {
            let count = certain_loss.map_or(1, |(_, count)| count + 1);
            certain_loss = Some((start_tick + 1, count));
        } else if residual_hi <= bound {
            retained[ci] = 1.0;
        } else {
            ambiguous = true;
        }
    }
    ProjectionIntervalResult {
        end_state: state,
        loss: certain_loss,
        certified: !ambiguous && certain_loss.is_none(),
        ambiguous,
        finite: true,
        width,
        retained,
        residual: [0.0; 7],
    }
}

/// Evaluate a complete proposed program.  This is the common graph-only
/// analysis-by-synthesis boundary used by both the term-tree wrapper above and
/// native composition; callers cannot accidentally project a single binding
/// when the decision under consideration is a compound plan.
fn future_manifold_projection_for_members(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
    policy: NodeID,
    member_nodes: &[NodeID],
    single_action_certificate: bool,
) -> FutureProjectionReport {
    // The temporal-anchor contract is opt-in.  Keep the historical dense
    // projector as the exact compatibility path for policies that have not
    // enabled it; this also keeps absent seed attributes gate-off inert.
    if fattr(
        graph,
        interner,
        policy,
        "future_manifold_temporal_anchors_enabled",
    ) > 0.5
    {
        future_manifold_projection_for_members_foveated(
            graph,
            interner,
            episode,
            policy,
            member_nodes,
            single_action_certificate,
        )
    } else {
        future_manifold_projection_for_members_legacy(
            graph,
            interner,
            episode,
            policy,
            member_nodes,
            single_action_certificate,
        )
    }
}

#[allow(dead_code)]
fn future_manifold_projection_for_members_legacy(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
    policy: NodeID,
    member_nodes: &[NodeID],
    single_action_certificate: bool,
) -> FutureProjectionReport {
    let safety = learning_safety_evidence(graph, interner, episode);
    let members = member_nodes.to_vec();
    let budget_raw = fattr(graph, interner, policy, "future_manifold_projection_budget");
    let budget = budget_raw.round() as i32;
    // `budget` is a fail-closed ceiling, not the requested horizon.  The
    // projection allocates time one dense slice at a time until the projected
    // path leaves its bounds or the learned transition reaches a fixed point.
    // This is temporal foveation over the learned graph model.
    let budget_valid =
        (2..=64).contains(&budget) && (budget_raw - budget as f64).abs() < f64::EPSILON;
    let fixed_run_raw = fattr(
        graph,
        interner,
        policy,
        "future_manifold_path_fixed_point_run",
    );
    let fixed_run_required = fixed_run_raw.round() as i32;
    let foveation_valid = (1..budget).contains(&fixed_run_required)
        && (fixed_run_raw - fixed_run_required as f64).abs() < f64::EPSILON;
    let protected = COMPONENTS
        .iter()
        .filter(|k| fattr(graph, interner, policy, &format!("{k}_weight")) > 0.0)
        .count() as f64;
    let mut context = [
        fattr(graph, interner, episode, "state_flow_forward"),
        fattr(graph, interner, episode, "state_flow_lateral"),
        fattr(graph, interner, episode, "state_flow_vertical"),
        fattr(graph, interner, episode, "state_power_state"),
    ];
    let all_models = future_manifold_episode_models(graph, interner, episode);
    let references: Vec<NodeID> = all_models
        .iter()
        .copied()
        .filter(|m| {
            fattr(graph, interner, *m, "activation_magnitude") < 0.5
                && fattr(graph, interner, *m, "context_delta_experience_count") > 0.0
        })
        .collect();
    let support = budget_valid
        && foveation_valid
        && !members.is_empty()
        && !references.is_empty()
        && members.iter().all(|m| {
            let learned_transition =
                fattr(graph, interner, *m, "context_delta_experience_count") > 0.0;
            let specified_effect =
                fattr(graph, interner, *m, "specified_actuator_dynamics_enabled") > 0.5
                    && fattr(graph, interner, *m, "specified_effect_prior_confidence") > 0.5
                    && fattr(
                        graph,
                        interner,
                        *m,
                        "specified_maximum_position_change_per_action",
                    ) > 0.0;
            fattr(graph, interner, *m, "experience_count") > 0.0
                && (learned_transition || specified_effect)
        });
    let mut reference_positions: Vec<f64> = references
        .iter()
        .map(|m| fattr(graph, interner, *m, "state_effector_position"))
        .collect();
    let mut positions: Vec<f64> = members
        .iter()
        .map(|m| fattr(graph, interner, *m, "state_effector_position"))
        .collect();
    let mut loss = 0.0;
    let mut horizon = if budget_valid { budget as f64 } else { 0.0 };
    let mut resolved = false;
    // 1 = earliest path-bound loss, 2 = learned transition fixed point,
    // 3 = budget exhausted unresolved, 4 = support unavailable.
    let mut termination_code = if support { 3.0 } else { 4.0 };
    let mut retained = [0.0f64; 7];
    let mut shape_residual = [0.0f64; 7];
    let mut fixed_run = 0;
    for step in 1..=budget {
        if !support {
            break;
        }
        let old_context = context;
        let old_positions = positions.clone();
        let old_reference_positions = reference_positions.clone();
        let mut baseline_delta = [0.0f64; 4];
        for j in 0..4 {
            if !references.is_empty() {
                baseline_delta[j] = references
                    .iter()
                    .map(|m| {
                        let mut d = fattr(
                            graph,
                            interner,
                            *m,
                            &format!("mean_context_delta_{}", FLOW_FEATURES[j]),
                        );
                        for k in 0..4 {
                            d += fattr(
                                graph,
                                interner,
                                *m,
                                &format!(
                                    "context_delta_gain_{}_{}",
                                    FLOW_FEATURES[j], FLOW_FEATURES[k]
                                ),
                            ) * (old_context[k]
                                - fattr(
                                    graph,
                                    interner,
                                    *m,
                                    &format!("mean_{}", FLOW_FEATURES[k]),
                                ));
                        }
                        d
                    })
                    .sum::<f64>()
                    / references.len() as f64;
            }
        }
        for j in 0..4 {
            let member_delta: f64 = members
                .iter()
                .map(|m| {
                    // A specified effector prior supplies its own consequence and
                    // actuator dynamics, but not a fabricated body transition.
                    // Until that transition is learned, it inherits the learned
                    // neutral reference delta, contributing zero differential.
                    if fattr(graph, interner, *m, "context_delta_experience_count") <= 0.0 {
                        return 0.0;
                    }
                    let mut d = fattr(
                        graph,
                        interner,
                        *m,
                        &format!("mean_context_delta_{}", FLOW_FEATURES[j]),
                    );
                    for k in 0..4 {
                        d += fattr(
                            graph,
                            interner,
                            *m,
                            &format!(
                                "context_delta_gain_{}_{}",
                                FLOW_FEATURES[j], FLOW_FEATURES[k]
                            ),
                        ) * (old_context[k]
                            - fattr(graph, interner, *m, &format!("mean_{}", FLOW_FEATURES[k])));
                    }
                    d - baseline_delta[j]
                })
                .sum();
            context[j] = old_context[j] + baseline_delta[j] + member_delta;
        }
        let mut actuators_settled = true;
        for (i, m) in members.iter().enumerate() {
            let max_change = fattr(
                graph,
                interner,
                *m,
                "specified_maximum_position_change_per_action",
            );
            let target = fattr(graph, interner, *m, "specified_command_level");
            let error = target - positions[i];
            positions[i] += if error.abs() > max_change {
                if error > 0.0 {
                    max_change
                } else {
                    -max_change
                }
            } else {
                error
            };
            if (target - positions[i]).abs() > f64::EPSILON {
                actuators_settled = false;
            }
        }
        for (i, m) in references.iter().enumerate() {
            let max_change = fattr(
                graph,
                interner,
                *m,
                "specified_maximum_position_change_per_action",
            );
            let error =
                fattr(graph, interner, *m, "specified_command_level") - reference_positions[i];
            reference_positions[i] += if error.abs() > max_change {
                if error > 0.0 {
                    max_change
                } else {
                    -max_change
                }
            } else {
                error
            };
            if (fattr(graph, interner, *m, "specified_command_level") - reference_positions[i])
                .abs()
                > f64::EPSILON
            {
                actuators_settled = false;
            }
        }
        let mut step_loss = 0.0;
        for (ci, key) in COMPONENTS.iter().enumerate() {
            if fattr(graph, interner, policy, &format!("{key}_weight")) <= 0.0 {
                continue;
            }
            let predict = |m: NodeID, pos: f64| -> f64 {
                let spec = fattr(graph, interner, m, "specified_actuator_dynamics_enabled") > 0.5
                    && fattr(graph, interner, m, "specified_effect_prior_confidence") > 0.5
                    && fattr(
                        graph,
                        interner,
                        m,
                        "specified_maximum_position_change_per_action",
                    ) > 0.0;
                if spec {
                    return fattr(graph, interner, m, &format!("specified_passive_mean_{key}"))
                        + fattr(
                            graph,
                            interner,
                            m,
                            &format!("specified_position_gain_{key}"),
                        ) * pos;
                }
                let mut learned = fattr(graph, interner, m, &format!("mean_{key}"));
                if fattr(
                    graph,
                    interner,
                    policy,
                    "contextual_effector_prediction_enabled",
                ) > 0.5
                {
                    learned += fattr(graph, interner, m, &format!("flow_gain_{key}"))
                        * (context[0] * context[0]
                            + context[1] * context[1]
                            + context[2] * context[2]
                            - fattr(graph, interner, m, "mean_flow_speed_squared"));
                    for j in 0..4 {
                        learned += fattr(
                            graph,
                            interner,
                            m,
                            &format!("{}_gain_{}", FLOW_FEATURES[j], key),
                        ) * (context[j]
                            - fattr(graph, interner, m, &format!("mean_{}", FLOW_FEATURES[j])));
                    }
                }
                learned
            };
            let baseline_prediction = if references.is_empty() {
                0.0
            } else {
                references
                    .iter()
                    .enumerate()
                    .map(|(ri, m)| predict(*m, reference_positions[ri]))
                    .sum::<f64>()
                    / references.len() as f64
            };
            let mut prediction = baseline_prediction;
            for (i, m) in members.iter().enumerate() {
                prediction += predict(*m, positions[i]) - baseline_prediction;
            }
            let target = fattr(graph, interner, episode, &format!("target_{key}"));
            let delta = prediction - target;
            let situated_support =
                situation_support_field(graph, interner, episode, policy, step as f64, false, 0.0);
            let bound = safety.bound(
                fattr(graph, interner, episode, &format!("manifold_bound_{key}")),
                situated_support.weights[ci],
            );
            let excess = delta.abs() - bound;
            if excess > 0.0 {
                shape_residual[ci] = delta.signum() * excess;
                step_loss += 1.0;
                retained[ci] = 0.0;
            } else {
                retained[ci] = 1.0;
            }
        }
        horizon = step as f64;
        if step_loss > 0.0 {
            loss = step_loss;
            resolved = true;
            termination_code = 1.0;
            break;
        }
        // An epistemic probe commits one action and then necessarily returns
        // through a receipt before any further action can be selected.  Its
        // future manifold therefore ends at this action boundary; pretending
        // the probe is held would project an action the engine cannot perform.
        if single_action_certificate && step == 1 {
            resolved = true;
            termination_code = 5.0;
            break;
        }
        // A certificate is about the future MANIFOLD SHAPE, not motion in a
        // latent variable the consequence map does not read.  When contextual
        // prediction is disabled, projected flow context has no causal path
        // to any protected coordinate and cannot invalidate retention.  When
        // it is enabled, retain the stronger complete-context fixed point.
        let contextual = fattr(
            graph,
            interner,
            policy,
            "contextual_effector_prediction_enabled",
        ) > 0.5;
        let transition_fixed = actuators_settled
            && (!contextual || context == old_context)
            && positions == old_positions
            && reference_positions == old_reference_positions;
        if transition_fixed {
            fixed_run += 1;
        } else {
            fixed_run = 0;
        }
        if fixed_run >= fixed_run_required {
            resolved = true;
            termination_code = 2.0;
            break;
        }
    }
    if support
        && !resolved
        && safety.recovery_boundary_available()
        && horizon >= safety.required_horizon_units as f64
        && loss <= 0.0
    {
        // A verified recovery path is an admissible stopping boundary: the
        // remaining projected future is recoverable by the graph-declared
        // reset/scaffold path.  It does not override an observed bound loss.
        resolved = true;
        termination_code = 7.0;
    }
    if !support {
        loss = 0.0;
        retained = [0.0; 7];
        shape_residual = [0.0; 7];
    }
    let retained_cells = retained.iter().sum::<f64>();
    let information_authority = protected_support_authority(
        graph,
        interner,
        policy,
        situation_support_field(graph, interner, episode, policy, horizon, false, 0.0),
    );
    let information_loss = (loss
        + (protected * (protected - 1.0) - retained_cells * (retained_cells - 1.0)) / 2.0
        - safety.information_loss_allowance * information_authority)
        .max(0.0);
    let (situated_support, applied_bounds) =
        support_observability(graph, interner, episode, policy, horizon, false, 0.0);
    FutureProjectionReport {
        support,
        resolved,
        termination_code,
        horizon,
        budget: budget as f64,
        loss,
        information_loss,
        anchor_count: 0.0,
        refinement_count: 0.0,
        certified_interval_count: 0.0,
        ambiguous_interval_count: 0.0,
        max_enclosure_width: 0.0,
        max_shape_order: 0.0,
        earliest_decisive_tick: if loss > 0.0 { horizon } else { 0.0 },
        minimum_exafferent_scale: 0.0,
        residual: shape_residual,
        retained,
        situated_support,
        applied_bounds,
    }
}

/// Temporally foveated projector selected by the explicit temporal-anchor
/// policy flag.  The dense implementation remains the compatibility path when
/// that flag is absent or disabled.
fn future_manifold_projection_for_members_foveated(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
    policy: NodeID,
    member_nodes: &[NodeID],
    single_action_certificate: bool,
) -> FutureProjectionReport {
    let safety = learning_safety_evidence(graph, interner, episode);
    let members = member_nodes.to_vec();
    let budget_raw = fattr(graph, interner, policy, "future_manifold_projection_budget");
    let budget = budget_raw.round() as i32;
    let budget_valid = budget_raw.is_finite()
        && (2..=64).contains(&budget)
        && (budget_raw - budget as f64).abs() < f64::EPSILON;
    let refinement_raw = fattr(graph, interner, policy, "future_manifold_max_refinements");
    let max_refinements = if refinement_raw > 0.0 {
        refinement_raw.round() as i32
    } else {
        // Older direct policies do not publish this optional field.  Their
        // temporal path inherits the anchor budget, while explicit values
        // remain an independent refinement ceiling.
        budget
    };
    let refinements_valid = refinement_raw.is_finite()
        && (refinement_raw <= 0.0
            || ((1..=64).contains(&max_refinements)
                && (refinement_raw - max_refinements as f64).abs() < f64::EPSILON));
    // A physical horizon is distinct from the number of anchors/refinements
    // the evaluator may spend.  Existing policies do not carry it yet, so a
    // missing value falls back to the legacy budget and keeps old fixtures
    // byte-compatible at the public fields.
    let physical_raw = fattr(graph, interner, policy, "future_manifold_physical_horizon");
    let explicit_physical_horizon = physical_raw.is_finite() && physical_raw > 0.0;
    let physical_horizon = if physical_raw > 0.0 {
        physical_raw.round() as i32
    } else {
        budget
    };
    let physical_valid = physical_horizon >= 1
        && physical_horizon <= 4096
        && physical_raw.is_finite()
        && (physical_raw <= 0.0 || (physical_raw - physical_horizon as f64).abs() < f64::EPSILON);
    let fixed_run_raw = fattr(
        graph,
        interner,
        policy,
        "future_manifold_path_fixed_point_run",
    );
    let fixed_run_required = fixed_run_raw.round() as i32;
    let foveation_valid = fixed_run_raw.is_finite()
        && budget_valid
        && refinements_valid
        && (1..budget).contains(&fixed_run_required)
        && (fixed_run_raw - fixed_run_required as f64).abs() < f64::EPSILON;
    let protected = COMPONENTS
        .iter()
        .filter(|key| fattr(graph, interner, policy, &format!("{key}_weight")) > 0.0)
        .count() as f64;
    let context = [
        fattr(graph, interner, episode, "state_flow_forward"),
        fattr(graph, interner, episode, "state_flow_lateral"),
        fattr(graph, interner, episode, "state_flow_vertical"),
        fattr(graph, interner, episode, "state_power_state"),
    ];
    let all_models = future_manifold_episode_models(graph, interner, episode);
    let references: Vec<NodeID> = all_models
        .iter()
        .copied()
        .filter(|model| {
            fattr(graph, interner, *model, "activation_magnitude") < 0.5
                && fattr(graph, interner, *model, "context_delta_experience_count") > 0.0
        })
        .collect();
    let mut positions: Vec<f64> = members
        .iter()
        .map(|model| fattr(graph, interner, *model, "state_effector_position"))
        .collect();
    let mut reference_positions: Vec<f64> = references
        .iter()
        .map(|model| fattr(graph, interner, *model, "state_effector_position"))
        .collect();
    let initial_state = ProjectionState {
        context,
        positions: std::mem::take(&mut positions),
        reference_positions: std::mem::take(&mut reference_positions),
    };
    let finite_bounds = COMPONENTS.iter().all(|key| {
        fattr(graph, interner, policy, &format!("{key}_weight")).is_finite()
            && fattr(graph, interner, episode, &format!("target_{key}")).is_finite()
            && fattr(graph, interner, episode, &format!("manifold_bound_{key}")).is_finite()
    });
    let mut support = budget_valid
        && physical_valid
        && foveation_valid
        && protected > 0.0
        && !members.is_empty()
        && !references.is_empty()
        && finite_bounds
        && projection_state_finite(&initial_state)
        && members.iter().all(|model| {
            fattr(graph, interner, *model, "experience_count") > 0.0
                && (fattr(graph, interner, *model, "context_delta_experience_count") > 0.0
                    || (fattr(
                        graph,
                        interner,
                        *model,
                        "specified_actuator_dynamics_enabled",
                    ) > 0.5
                        && fattr(graph, interner, *model, "specified_effect_prior_confidence")
                            > 0.5
                        && fattr(
                            graph,
                            interner,
                            *model,
                            "specified_maximum_position_change_per_action",
                        ) > 0.0))
        });

    let mut retained = [0.0f64; 7];
    let mut residual = [0.0f64; 7];
    let mut loss = 0.0;
    let mut horizon = 0.0;
    let mut resolved = false;
    let mut termination_code = if support { 3.0 } else { 4.0 };
    let mut earliest_decisive_tick = 0.0;
    let mut anchor_count = 0.0;
    let mut refinement_count = 0.0;
    let mut certified_interval_count = 0.0;
    let mut ambiguous_interval_count = 0.0;
    let mut max_enclosure_width: f64 = 0.0;
    let mut max_shape_order = 0.0;
    let mut seen_anchors: Vec<i32> = Vec::new();
    let mut current_tick = 0i32;
    let mut current_state = initial_state;
    let mut fixed_run = 0i32;

    let note_anchor = |tick: i32, seen: &mut Vec<i32>, count: &mut f64| {
        if !seen.contains(&tick) {
            seen.push(tick);
            *count += 1.0;
        }
    };
    let next_anchor = |tick: i32| -> i32 {
        match tick {
            0 => 1,
            1 => 2,
            2 => 3,
            3 => 4,
            4 => 8,
            8 => 16,
            // After the dense warm-up, square the anchor to keep the
            // evaluated schedule logarithmic in the physical horizon.
            value => value.saturating_mul(value),
        }
    };

    while support && current_tick < physical_horizon {
        let requested = next_anchor(current_tick);
        let target = requested.min(physical_horizon);
        if target <= current_tick {
            break;
        }
        if anchor_count >= budget as f64 {
            break;
        }
        note_anchor(target, &mut seen_anchors, &mut anchor_count);
        let mut work = vec![(current_tick, target, current_state.clone())];
        let mut final_state: Option<ProjectionState> = None;
        let mut interval_failed = false;
        while let Some((start_tick, end_tick, start_state)) = work.pop() {
            let result = projection_certify_interval(
                graph,
                interner,
                episode,
                policy,
                start_tick,
                end_tick,
                &start_state,
                &references,
                &members,
            );
            max_enclosure_width = max_enclosure_width.max(result.width);
            if end_tick - start_tick > 1 && result.finite {
                // This slice uses an affine recurrence plus a norm remainder
                // enclosure.  It is first-order certification, not a claim
                // of quadratic/cubic shape support.
                max_shape_order = 1.0;
            }
            if !result.finite {
                support = false;
                interval_failed = true;
                termination_code = 4.0;
                break;
            }
            if let Some((decisive_tick, count)) = result.loss {
                loss = count as f64;
                earliest_decisive_tick = decisive_tick as f64;
                horizon = decisive_tick as f64;
                retained = result.retained;
                residual = result.residual;
                resolved = true;
                termination_code = 1.0;
                interval_failed = true;
                break;
            }
            if result.ambiguous {
                ambiguous_interval_count += 1.0;
                if end_tick - start_tick <= 1
                    || anchor_count + 1.0 > budget as f64
                    || refinement_count + 1.0 > max_refinements as f64
                {
                    interval_failed = true;
                    break;
                }
                let midpoint = start_tick + (end_tick - start_tick) / 2;
                if midpoint <= start_tick || midpoint >= end_tick {
                    interval_failed = true;
                    break;
                }
                // Advance the inserted anchor with the same affine/jump
                // closed form as certification.  Never walk the skipped
                // physical ticks merely to obtain a refinement state.
                let midpoint_result = projection_certify_interval_sparse(
                    graph,
                    interner,
                    episode,
                    policy,
                    start_tick,
                    midpoint,
                    &start_state,
                    &references,
                    &members,
                );
                if !midpoint_result.finite {
                    support = false;
                    interval_failed = true;
                    termination_code = 4.0;
                    break;
                }
                let midpoint_state = midpoint_result.end_state;
                if !seen_anchors.contains(&midpoint) {
                    seen_anchors.push(midpoint);
                    anchor_count += 1.0;
                }
                refinement_count += 1.0;
                work.push((midpoint, end_tick, midpoint_state));
                work.push((start_tick, midpoint, start_state));
                continue;
            }
            if result.certified {
                certified_interval_count += 1.0;
                retained = result.retained;
                horizon = end_tick as f64;
                final_state = Some(result.end_state);
                continue;
            }
            interval_failed = true;
            break;
        }
        if !support || resolved {
            break;
        }
        if interval_failed {
            break;
        }
        if let Some(state) = final_state {
            let interval_len = target - current_tick;
            let contextual = fattr(
                graph,
                interner,
                policy,
                "contextual_effector_prediction_enabled",
            ) > 0.5;
            let interval_fixed = (!contextual || state.context == current_state.context)
                && state.positions == current_state.positions
                && state.reference_positions == current_state.reference_positions;
            current_state = state;
            current_tick = target;
            if interval_fixed {
                fixed_run += interval_len;
            } else {
                fixed_run = 0;
            }
            if single_action_certificate && current_tick >= 1 {
                resolved = true;
                termination_code = 5.0;
                break;
            }
            if fixed_run >= fixed_run_required {
                resolved = true;
                termination_code = 2.0;
                break;
            }
        } else {
            break;
        }
    }

    // An explicitly published physical horizon is a real certification
    // boundary, distinct from the legacy evaluation-budget fallback.  If the
    // sparse evaluator reached it, every interval on the path was certified
    // (otherwise current_tick would still be short of the horizon), so the
    // bounded result is resolved even without a fixed point.  Preserve the
    // historical unresolved code for budget-only horizons.
    if support && !resolved && explicit_physical_horizon && current_tick >= physical_horizon {
        resolved = true;
        termination_code = 6.0;
        horizon = physical_horizon as f64;
    }

    if !support {
        retained = [0.0; 7];
        residual = [0.0; 7];
        loss = 0.0;
        horizon = 0.0;
        resolved = false;
        termination_code = 4.0;
    }
    if support
        && !resolved
        && safety.recovery_boundary_available()
        && horizon >= safety.required_horizon_units as f64
        && loss <= 0.0
    {
        // The graph has certified the visited prefix and published a
        // reachable recovery path.  Stop at that boundary instead of
        // demanding an arbitrary farther projection.
        resolved = true;
        termination_code = 7.0;
    }
    let retained_cells = retained.iter().sum::<f64>();
    let information_authority = protected_support_authority(
        graph,
        interner,
        policy,
        situation_support_field(graph, interner, episode, policy, horizon, false, 0.0),
    );
    let information_loss = (loss
        + (protected * (protected - 1.0) - retained_cells * (retained_cells - 1.0)) / 2.0
        - safety.information_loss_allowance * information_authority)
        .max(0.0);
    let (situated_support, applied_bounds) =
        support_observability(graph, interner, episode, policy, horizon, false, 0.0);
    FutureProjectionReport {
        support,
        resolved,
        termination_code,
        horizon,
        budget: budget as f64,
        loss,
        information_loss,
        anchor_count,
        refinement_count,
        certified_interval_count,
        ambiguous_interval_count,
        max_enclosure_width,
        max_shape_order,
        earliest_decisive_tick,
        minimum_exafferent_scale: 0.0,
        residual,
        retained,
        situated_support,
        applied_bounds,
    }
}
