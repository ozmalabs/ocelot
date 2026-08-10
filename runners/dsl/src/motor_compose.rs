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
    "forward", "lateral", "vertical", "roll", "pitch", "turn", "normal_load",
];
const FLOW_FEATURES: [&str; 4] = [
    "flow_forward", "flow_lateral", "flow_vertical", "power_state",
];
const STRUCTURAL_LOADS: [&str; 11] = [
    "normal_load", "peak_force", "impulse", "impact_energy", "thermal_load",
    "dynamic_pressure", "roll_moment", "pitch_moment", "yaw_moment",
    "heat_flux", "skin_temperature",
];
/// COMPONENTS + drag + energy + the structural loads not already present
/// (mirrors ALL_CONSEQUENCES = dict.fromkeys(COMPONENTS, drag, energy,
/// *STRUCTURAL_LOADS): normal_load dedups).
const PREDICTED_KEYS: [&str; 19] = [
    "forward", "lateral", "vertical", "roll", "pitch", "turn", "normal_load",
    "drag", "energy", "peak_force", "impulse", "impact_energy",
    "thermal_load", "dynamic_pressure", "roll_moment", "pitch_moment",
    "yaw_moment", "heat_flux", "skin_temperature",
];
const N_KEYS: usize = PREDICTED_KEYS.len();
const N_LOADS: usize = STRUCTURAL_LOADS.len();

fn key_index(key: &str) -> usize {
    PREDICTED_KEYS.iter().position(|k| *k == key).unwrap()
}

fn fattr(graph: &TypedGraph, interner: &Interner, node: NodeID, key: &str) -> f64 {
    let Some(sym) = interner.lookup(key) else { return 0.0 };
    if !graph.has_node(node) {
        return 0.0;
    }
    match graph.node(node).attrs.get(&sym) {
        Some(Value::Float(f)) => *f,
        Some(Value::Int(i)) => *i as f64,
        Some(Value::Bool(b)) => {
            if *b { 1.0 } else { 0.0 }
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
    let desired_context = if fattr(
        graph,
        interner,
        episode,
        "self_takeoff_drive_active",
    ) > 0.5
    {
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
            if sattr(graph, interner, program, "motor_task_context")
                != Some(desired_context)
            {
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
        let support_0 = fattr(
            graph, interner, episode, "state_support_0_force"
        ) > 0.0;
        let support_1 = fattr(
            graph, interner, episode, "state_support_1_force"
        ) > 0.0;
        let paired = interner.lookup("paired_lower_support");
        let single = interner.lookup("single_lower_support");
        let unsupported = interner.lookup("unsupported");
        for hint in graph.neighbours(episode, Some(considered_edge)) {
            if fattr(graph, interner, hint, "output_authority") != 0.0 {
                continue;
            }
            for source_stage in graph.neighbours(hint, Some(stage_edge)) {
                let support = sattr(
                    graph, interner, source_stage, "support_topology"
                );
                let support_matches = (support == paired && support_0 && support_1)
                    || (support == single && support_0 != support_1)
                    || (support == unsupported && !support_0 && !support_1);
                if !support_matches {
                    continue;
                }
                for target_stage in graph.neighbours(
                    source_stage, Some(transition_edge)
                ) {
                    for shape in graph.neighbours(
                        target_stage, Some(target_shape_edge)
                    ) {
                        for program in graph.in_neighbours(
                            shape, Some(realizes_shape_edge)
                        ) {
                            if sattr(graph, interner, program, "motor_task_context")
                                != Some(desired_context)
                            {
                                continue;
                            }
                            members.extend(
                                graph.neighbours(program, Some(member_edge))
                            );
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

fn humanoid_composition_input_signature(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
    policy: NodeID,
    model_nodes: &[NodeID],
) -> u64 {
    let mut hasher = DefaultHasher::new();
    for key in [
        "request_seq", "state_seq", "selected_primary_context_id",
        "current_support_phase", "response_frames", "state_qx", "state_qy",
        "state_qz", "state_qw", "state_wx", "state_wy", "state_vx",
        "state_vy", "state_vz", "state_x", "state_y", "state_z",
        "standing_reference_z", "lateral_offset", "recovery_mode",
        "locomotion_drive_active", "state_support_0_force",
        "state_support_1_force", "state_support_0_x", "state_support_0_y",
        "state_support_1_x", "state_support_1_y", "support_sensor_count",
        "learned_gait_tilt_envelope", "self_takeoff_drive_active",
        "self_takeoff_target_velocity_scale", "self_takeoff_compression_scale",
        "body_mass", "physics_time_step", "lifetime_completed_progress",
        "directed_progress", "target_directed_progress_m",
        "active_residual_regime_ordinal", "active_gait_attractor_ordinal",
        "motor_effector_group_count", "state_contact_force_newtons",
    ] {
        fattr(graph, interner, episode, key).to_bits().hash(&mut hasher);
    }
    sattr(graph, interner, episode, "selected_primary_token").hash(&mut hasher);
    for key in [
        "gravity_acceleration", "target_froude_speed",
        "support_phase_prior_strength", "minimum_upright_height_fraction",
        "persistent_task_residual_authority", "support_geometry_preview_authority",
        "takeoff_motor_compression_authority",
    ] {
        fattr(graph, interner, policy, key).to_bits().hash(&mut hasher);
    }
    for node in model_nodes {
        node.hash(&mut hasher);
        sattr(graph, interner, *node, "token").hash(&mut hasher);
        for key in [
            "actuator_group", "support_phase", "context_id", "initialized",
            "mean_input_energy_joules", "mean_dzx", "mean_dzy", "mean_dwx",
            "mean_dwy", "mean_dvx", "mean_dvy", "mean_dvz", "anchor_z_x",
            "anchor_z_y", "anchor_wx", "anchor_wy", "anchor_vx", "anchor_vy",
            "anchor_vz", "anchor_lateral_offset",
        ] {
            fattr(graph, interner, *node, key).to_bits().hash(&mut hasher);
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
                    "coupling_regime", "vertical_regime",
                    "translation_per_joule", "experience_count",
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
                "ordinal", "approved", "residual_dzx", "residual_dzy",
                "residual_dwx", "residual_dwy", "residual_dvx", "residual_dvy",
                "residual_dvz",
            ] {
                fattr(graph, interner, node, key).to_bits().hash(&mut hasher);
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

struct Composer {
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

impl Composer {
    fn build(
        graph: &TypedGraph,
        interner: &Interner,
        episode: NodeID,
        policy: NodeID,
        model_nodes: &[NodeID],
    ) -> Composer {
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
                if position_error > 0.0 { max_change } else { -max_change }
            } else {
                position_error
            };
            let predicted_position = position + bounded;
            let use_specification = m("specified_actuator_dynamics_enabled")
                > 0.5
                && m("specified_effect_prior_confidence") > 0.5
                && max_change > 0.0;
            let mut prediction = [0.0; N_KEYS];
            for (ki, key) in PREDICTED_KEYS.iter().enumerate() {
                if use_specification {
                    prediction[ki] = m(&format!("specified_passive_mean_{key}"))
                        + m(&format!("specified_position_gain_{key}"))
                            * predicted_position;
                } else {
                    let mut learned = m(&format!("mean_{key}"));
                    if contextual {
                        learned += m(&format!("flow_gain_{key}"))
                            * (flow_speed_squared
                                - m("mean_flow_speed_squared"));
                        for (fi, feature) in FLOW_FEATURES.iter().enumerate() {
                            learned += m(&format!("{feature}_gain_{key}"))
                                * (state_features[fi]
                                    - m(&format!("mean_{feature}")));
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
                        && fattr(graph, interner, **node, "experience_count")
                            > 0.5
                })
                .map(|(i, _)| &models[i])
                .collect();
            if !refs.is_empty() {
                for ki in 0..N_KEYS {
                    baseline[ki] = refs
                        .iter()
                        .map(|row| row.prediction[ki])
                        .sum::<f64>()
                        / refs.len() as f64;
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
                && !(self.current_loads[li] + row.structural[li]
                    > self.safe_loads[li])
        });
        if within {
            return true;
        }
        self.interrupt_required
            && (0..N_LOADS).all(|li| !(row.structural[li] > 0.0))
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
        let Some(urgency) = self.urgency() else { return 0.0 };
        let vertical = self.prediction(plan, key_index("vertical"), addition);
        -self.margin_weight * urgency * vertical
    }

    /// The singleton form: one model, no plan.
    fn margin_price_single(&self, mi: usize) -> f64 {
        let Some(urgency) = self.urgency() else { return 0.0 };
        -self.margin_weight * urgency
            * self.models[mi].prediction[key_index("vertical")]
    }

    /// program_cost(plan, addition).
    fn program_cost(&self, plan: &[usize], addition: Option<usize>) -> f64 {
        let mut cost = 0.0;
        for ci in 0..7 {
            let residual = self.targets[ci] - self.prediction(plan, ci, addition);
            cost += self.weights[ci] * residual * residual;
        }
        cost += self.drag_weight * self.prediction(plan, key_index("drag"), addition);
        cost += self.energy_weight
            * self.prediction(plan, key_index("energy"), addition);
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
        if !(self.attribution_weight > 0.0)
            || !(self.attribution_reference_actions > 0.0)
        {
            return 0.0;
        }
        let stale =
            (self.request_seq - self.models[mi].last_singleton_exercise_seq)
                .max(0.0);
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

    /// open → snapshot-parallel expansion rounds → close.
    fn compose(&self) -> Vec<usize> {
        let mut best: Option<(usize, f64)> = None;
        for mi in 0..self.models.len() {
            if self.models[mi].eligible && self.model_admissible(mi) {
                let cost = self.singleton_cost(mi);
                if best.map_or(true, |(_, c)| cost < c) {
                    best = Some((mi, cost));
                }
            }
        }
        let Some((primary, _)) = best else { return Vec::new() };
        let mut plan = vec![primary];
        loop {
            let plan_cost = self.program_cost(&plan, None);
            let groups_in_plan: Vec<f64> =
                plan.iter().map(|mi| self.models[*mi].group).collect();
            let mut winners: Vec<(f64, usize, f64)> = Vec::new();
            for mi in 0..self.models.len() {
                let group = self.models[mi].group;
                if groups_in_plan.iter().any(|g| *g == group) {
                    continue;
                }
                if !(self.models[mi].eligible
                    && self.program_admissible(&plan, mi))
                {
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
}

// The humanoid cortex predates the morphology-neutral effector schema, but it
// performs the same operation: start from a support-local primitive and grow a
// cross-actuator program while forward synthesis strictly improves.  Keeping
// this second schema behind MotorCompose avoids restoring a second interpreted
// System-2 engine merely because its learned consequences have humanoid names.
const HUMANOID_KEYS: [&str; 7] = [
    "dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz",
];

#[derive(Clone)]
struct HumanoidModel {
    node: NodeID,
    token: Option<Sym>,
    group: f64,
    support_phase: f64,
    context_id: f64,
    initialized: bool,
    active: bool,
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
}

impl<'a> HumanoidComposer<'a> {
    fn build(
        graph: &'a TypedGraph,
        interner: &'a Interner,
        episode: NodeID,
        policy: NodeID,
        model_nodes: &[NodeID],
    ) -> Self {
        let (coupling_regime, vertical_regime) =
            current_effector_regime(graph, interner, episode);
        let models = model_nodes.iter().map(|node| HumanoidModel {
            node: *node,
            token: sattr(graph, interner, *node, "token"),
            group: fattr(graph, interner, *node, "actuator_group"),
            support_phase: fattr(graph, interner, *node, "support_phase"),
            context_id: fattr(graph, interner, *node, "context_id"),
            initialized: fattr(graph, interner, *node, "initialized") > 0.5,
            active: false,
            input_energy_joules: fattr(
                graph,
                interner,
                *node,
                "mean_input_energy_joules",
            ),
            effect: std::array::from_fn(|i| {
                fattr(graph, interner, *node, &format!("mean_{}", HUMANOID_KEYS[i]))
            }),
            capability_translation_per_joule: matched_capability_translation_per_joule(
                graph, interner, *node, coupling_regime, vertical_regime,
            ),
        }).collect();
        let synergy_nodes = interner.lookup("has_humanoid_synergy_model")
            .map(|edge| graph.neighbours(episode, Some(edge)))
            .unwrap_or_default();
        let synergies = synergy_nodes.iter().map(|node| HumanoidSynergy {
            token_a: sattr(graph, interner, *node, "token_a"),
            token_b: sattr(graph, interner, *node, "token_b"),
            ordinal: fattr(graph, interner, *node, "ordinal"),
            approved: fattr(graph, interner, *node, "approved") > 0.5,
            residual: std::array::from_fn(|i| {
                fattr(graph, interner, *node, &format!("residual_{}", HUMANOID_KEYS[i]))
            }),
        }).collect();
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
        let distances: Vec<f64> = composer.models.iter()
            .map(|model| composer.context_distance(model)).collect();
        let support_phase = composer.ep("current_support_phase");
        for index in 0..composer.models.len() {
            let model = &composer.models[index];
            if !model.initialized || model.support_phase != support_phase {
                continue;
            }
            let best = composer.models.iter().enumerate()
                .filter(|(_, peer)| peer.initialized
                    && peer.token == model.token
                    && peer.support_phase == model.support_phase)
                .min_by(|(left, _), (right, _)| distances[*left]
                    .partial_cmp(&distances[*right])
                    .unwrap_or(std::cmp::Ordering::Equal))
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
            lookahead * (fattr(self.graph, self.interner, model.node, "anchor_wx") - self.ep("state_wx")),
            lookahead * (fattr(self.graph, self.interner, model.node, "anchor_wy") - self.ep("state_wy")),
            (fattr(self.graph, self.interner, model.node, "anchor_vx") - self.ep("state_vx")) / velocity_scale,
            (fattr(self.graph, self.interner, model.node, "anchor_vy") - self.ep("state_vy")) / velocity_scale,
            (fattr(self.graph, self.interner, model.node, "anchor_vz") - self.ep("state_vz")) / velocity_scale,
            (fattr(self.graph, self.interner, model.node, "anchor_lateral_offset") - self.ep("lateral_offset")) / height,
        ];
        errors.iter().map(|x| x * x).sum()
    }

    fn active(&self, index: usize) -> bool {
        self.models[index].active
    }

    fn synergy(&self, left: usize, right: usize) -> Option<&HumanoidSynergy> {
        let a = self.models[left].token;
        let b = self.models[right].token;
        self.synergies.iter()
            .filter(|s| s.approved && ((s.token_a == a && s.token_b == b)
                || (s.token_a == b && s.token_b == a)))
            .min_by(|x, y| x.ordinal.partial_cmp(&y.ordinal)
                .unwrap_or(std::cmp::Ordering::Equal))
    }

    fn active_related_node(&self, edge: &str, ordinal_attr: &str) -> Option<NodeID> {
        let edge = self.interner.lookup(edge)?;
        let wanted = self.ep(ordinal_attr);
        self.graph.neighbours(self.policy, Some(edge)).into_iter()
            .filter(|node| fattr(self.graph, self.interner, *node, "ordinal") == wanted)
            .min_by(|a, b| fattr(self.graph, self.interner, *a, "ordinal")
                .partial_cmp(&fattr(self.graph, self.interner, *b, "ordinal"))
                .unwrap_or(std::cmp::Ordering::Equal))
    }

    fn support_center(&self, axis: &str) -> f64 {
        let p0 = self.ep("state_support_0_force") > 0.0;
        let p1 = self.ep("state_support_1_force") > 0.0;
        let a = self.ep(&format!("state_support_0_{axis}"));
        let b = self.ep(&format!("state_support_1_{axis}"));
        if p0 && !p1 { a } else if p1 && !p0 { b } else { (a + b) / 2.0 }
    }

    fn viability_gate(&self, gait: Option<NodeID>) -> f64 {
        let (zx, zy) = self.body_z();
        let tilt = (zx * zx + zy * zy).sqrt();
        let tilt_budget = self.po("target_froude_speed")
            .max(self.ep("learned_gait_tilt_envelope"));
        let tilt_gate = (1.0 - tilt / tilt_budget).clamp(0.0, 1.0);
        let height = self.ep("standing_reference_z");
        let minimum = self.po("minimum_upright_height_fraction") * height;
        let height_gate = ((self.ep("state_z") - minimum)
            / (height - minimum).max(0.001)).clamp(0.0, 1.0);
        let grounded = self.ep("state_support_0_force") > 0.0
            || self.ep("state_support_1_force") > 0.0;
        let flight = gait.map_or(0.0, |node| {
            fattr(self.graph, self.interner, node, "flight_phase_authority")
        }) > 0.5;
        if (grounded || flight) && self.ep("recovery_mode") == 0.0
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
        let target_velocity = self.ep("heading_x")
            * self.po("target_froude_speed") * velocity_scale;
        let instantaneous = (self.ep("state_vx") + predicted_dvx
            - target_velocity) / velocity_scale;
        if self.po("persistent_task_residual_authority") <= 0.5 {
            return instantaneous * instantaneous;
        }
        let step = self.ep("heading_x")
            * (self.ep("state_vx") + 0.5 * predicted_dvx)
            * frames * self.ep("physics_time_step");
        let progress = self.ep("lifetime_completed_progress")
            + self.ep("directed_progress") + step;
        let residual = (self.ep("target_directed_progress_m") - progress)
            .max(0.0) / height;
        let regime = self.active_related_node(
            "has_humanoid_residual_regime", "active_residual_regime_ordinal");
        let gait = self.active_related_node(
            "has_humanoid_gait_attractor", "active_gait_attractor_ordinal");
        let prior = self.po("support_phase_prior_strength");
        let residual_gain = regime.map_or(0.0, |node| {
            fattr(self.graph, self.interner, node, "residual_gain_numerator")
        });
        let impulse = gait.map_or(0.0, |node| {
            fattr(self.graph, self.interner, node, "elastic_impulse_numerator")
        });
        (residual_gain / prior) * (1.0 + impulse / prior)
            * self.viability_gate(gait) * residual * residual
    }

    fn support_preview(&self, dvx: f64, dvy: f64) -> f64 {
        let authority = self.po("support_geometry_preview_authority");
        if authority == 0.0 || !(self.ep("state_support_0_force") > 0.0
            || self.ep("state_support_1_force") > 0.0)
        {
            return 0.0;
        }
        let height = self.ep("standing_reference_z");
        let prior = self.po("support_phase_prior_strength");
        let support_count = self.ep("support_sensor_count");
        let lookahead = (height / self.po("gravity_acceleration")).sqrt();
        let capture_x = self.ep("state_x")
            + lookahead * (self.ep("state_vx") + dvx);
        let capture_y = self.ep("state_y")
            + lookahead * (self.ep("state_vy") + dvy);
        let regime = self.active_related_node(
            "has_humanoid_residual_regime", "active_residual_regime_ordinal");
        let viability = regime.map_or(0.0, |node| {
            fattr(self.graph, self.interner, node, "viability_scale_numerator")
        });
        let forward_margin = viability / (prior * support_count) * height;
        let lateral_margin = viability / (prior * prior) * height
            + (self.ep("state_support_0_y") - self.ep("state_support_1_y")).abs()
                / support_count;
        let fx = ((capture_x - self.support_center("x")).abs() - forward_margin)
            .max(0.0) / height;
        let fy = ((capture_y - self.support_center("y")).abs() - lateral_margin)
            .max(0.0) / height;
        authority * (support_count * fx * fx + prior * fy * fy)
    }

    fn takeoff_cost(&self, predicted_dvz: f64) -> f64 {
        if self.ep("self_takeoff_drive_active") <= 0.5 {
            return 0.0;
        }
        let height = self.ep("standing_reference_z");
        let velocity_scale = (self.po("gravity_acceleration") * height).sqrt();
        let target = self.ep("self_takeoff_target_velocity_scale")
            * velocity_scale / self.po("support_phase_prior_strength");
        let error = (self.ep("state_vz") + predicted_dvz - target)
            / velocity_scale;
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
            * members.iter()
                .map(|index| self.models[*index].input_energy_joules)
                .sum::<f64>()
            / energy_scale.max(f64::EPSILON);
        let mut active_groups: Vec<u64> = self.models.iter().enumerate()
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
            / (group_count * self.po("support_phase_prior_strength"))
                .max(1.0);
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
        let predicted_translation = (self.ep("state_vx") + 0.5 * predicted_dvx)
            * frames
            * self.ep("physics_time_step");
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
        if let Some(index) = addition { members.push(index); }
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
            for key in 0..7 { predicted[key] += self.models[*index].effect[key]; }
        }
        for left in 0..members.len() {
            for right in left + 1..members.len() {
                if let Some(synergy) = self.synergy(members[left], members[right]) {
                    for key in 0..7 { predicted[key] += synergy.residual[key] / scale; }
                }
            }
        }
        for value in &mut predicted { *value *= scale; }
        let height = self.ep("standing_reference_z");
        let gravity = self.po("gravity_acceleration");
        let velocity_scale = (gravity * height).sqrt();
        let lookahead = (height / gravity).sqrt();
        let (zx, zy) = self.body_z();
        let predicted_zx = zx + predicted[0]
            + lookahead * (self.ep("state_wy") + predicted[3]);
        let predicted_zy = zy + predicted[1]
            - lookahead * (self.ep("state_wx") + predicted[2]);
        let lateral_target = -(self.ep("lateral_offset") / height)
            * self.po("target_froude_speed") * velocity_scale;
        let lateral_velocity = self.ep("state_vy") + predicted[5];
        let lateral_error = (lateral_velocity - lateral_target) / velocity_scale;
        let lateral_position = (self.ep("lateral_offset")
            + lookahead * lateral_velocity) / height;
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
        terms[0] + terms[1] + terms[2] + terms[3] + terms[4]
            + terms[5] + terms[6] + terms[7] + terms[8]
    }

    fn expansion_allowed(&self) -> bool {
        // The open rule snapshots compound_output_permitted into the plan
        // before it increments decision_count. Reading that graph-held fact is
        // both cheaper and exactly preserves the interpreted cascade's timing.
        let Some(edge) = self.interner.lookup("has_active_humanoid_motor_program")
        else { return false };
        let request_seq = self.ep("request_seq");
        self.graph.neighbours(self.episode, Some(edge)).into_iter().any(|plan| {
            fattr(self.graph, self.interner, plan, "request_seq") == request_seq
                && fattr(self.graph, self.interner, plan, "allow_expansion") == 1.0
        })
    }

    fn compose(&self) -> Vec<usize> {
        let primary_token = sattr(self.graph, self.interner, self.episode,
            "selected_primary_token");
        let primary_context = self.ep("selected_primary_context_id");
        let Some(primary) = self.models.iter().enumerate().find_map(|(i, model)| {
            (self.active(i) && model.token == primary_token
                && model.context_id == primary_context).then_some(i)
        }) else { return Vec::new() };
        let mut plan = vec![primary];
        if !self.expansion_allowed() { return plan; }
        loop {
            let current = self.cost(&plan, None);
            let mut best: Option<(usize, f64, bool)> = None;
            for index in 0..self.models.len() {
                if plan.contains(&index) || !self.active(index)
                    || plan.iter().any(|member| {
                        self.models[*member].group == self.models[index].group
                    })
                    || (self.ep("self_takeoff_drive_active") <= 0.5
                        && plan.iter().any(|member| {
                            self.synergy(*member, index).is_none()
                        }))
                {
                    continue;
                }
                let cost = self.cost(&plan, Some(index));
                if !(cost < current) {
                    continue;
                }
                let hinted = self.basin_members.contains(
                    &self.models[index].node
                );
                // A prior narrows an equivalent basin; it is not output
                // authority.  Receipt-backed predicted improvement therefore
                // remains primary, with the hint used only to break an exact
                // tie.  Reversing this ordering lets a broad bootstrap prior
                // override better situated evidence.
                if best.map_or(true, |(_, old_cost, old_hinted)| {
                    cost < old_cost
                        || (cost == old_cost && hinted && !old_hinted)
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
    let mut model_nodes = interner.lookup("has_embodied_effector_model")
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
                graph.neighbours(episode, Some(active_edge)).into_iter().any(
                    |plan| {
                        fattr(graph, interner, plan, "request_seq") == request_seq
                            && fattr(
                                graph,
                                interner,
                                plan,
                                "allow_expansion",
                            ) == 1.0
                    },
                )
            })
            .unwrap_or(false);
        let basin_members = active_humanoid_basin_members(graph, interner, episode);
        let key = HumanoidCache {
            graph_address: graph as *const TypedGraph as usize,
            episode,
            policy,
            input_signature: humanoid_composition_input_signature(
                graph,
                interner,
                episode,
                policy,
                &model_nodes,
            ),
            request_seq: fattr(graph, interner, episode, "request_seq").to_bits(),
            state_seq: fattr(graph, interner, episode, "state_seq").to_bits(),
            primary_token: sattr(graph, interner, episode, "selected_primary_token"),
            primary_context: fattr(
                graph, interner, episode, "selected_primary_context_id").to_bits(),
            takeoff_drive: fattr(
                graph, interner, episode, "self_takeoff_drive_active").to_bits(),
            takeoff_compression_scale: fattr(
                graph,
                interner,
                episode,
                "self_takeoff_compression_scale",
            ).to_bits(),
            takeoff_compression_authority: fattr(
                graph,
                interner,
                policy,
                "takeoff_motor_compression_authority",
            ).to_bits(),
            expansion_allowed,
            basin_members,
            model_count: model_nodes.len(),
            members: Vec::new(),
        };
        if let Some(hit) = HUMANOID_COMPOSE_CACHE.with(|slot| {
            let slot = slot.borrow();
            slot.as_ref().filter(|cached| {
                cached.graph_address == key.graph_address
                    && cached.episode == key.episode
                    && cached.policy == key.policy
                    && cached.input_signature == key.input_signature
                    && cached.request_seq == key.request_seq
                    && cached.state_seq == key.state_seq
                    && cached.primary_token == key.primary_token
                    && cached.primary_context == key.primary_context
                    && cached.takeoff_drive == key.takeoff_drive
                    && cached.takeoff_compression_scale
                        == key.takeoff_compression_scale
                    && cached.takeoff_compression_authority
                        == key.takeoff_compression_authority
                    && cached.expansion_allowed == key.expansion_allowed
                    && cached.basin_members == key.basin_members
                    && cached.model_count == key.model_count
            }).map(|cached| cached.members.contains(&candidate))
        }) {
            return hit;
        }
        let composer = HumanoidComposer::build(
            graph, interner, episode, policy, &model_nodes);
        let members: Vec<NodeID> = composer.compose().iter()
            .map(|mi| composer.models[*mi].node).collect();
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
    let composer = Composer::build(graph, interner, episode, policy, &model_nodes);
    composer
        .compose()
        .iter()
        .any(|mi| composer.models[*mi].node == candidate)
}
