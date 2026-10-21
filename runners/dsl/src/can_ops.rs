//! Causal Attitude Network operations on the substrate's typed graph.
//!
//! The substrate's grounding model rests on:
//!   - Axiom 0 (philosophy): truth is frame-relative
//!   - grounding_theory: therefore grounding is a vector, not a boolean
//!   - causal_attitude_networks: the vector is σ + J + h + β + H
//!   - mt_target_equilibria: each Mt's admissibility grammar IS its
//!     Hamiltonian
//!
//! PHASE A (native-backend cutover): the continuous mean-field / Ising
//! engine (tanh self-consistency relaxation, Hebbian J updates, J/h decay,
//! identity dynamics, basin audit, cross-Mt conflict/similarity that relied
//! on independent relaxation) was REMOVED. The discrete-native graph rules
//! (seeds/can_native_reimplementation.json + seeds/can_decay_identity.json)
//! are the sole CAN dynamics; the diagnostics that read committed discrete
//! state live in domains/can_native_orchestration.py.
//!
//! What survives here are representation-agnostic, non-iterative READS +
//! one evidence-injection write:
//!   - energy H(σ) under Mt's Hamiltonian (closed-form scorer over a
//!     caller-supplied state map)
//!   - frustration index given a state map (closed-form scorer)
//!   - distance from committed state to target (vector + magnitude)
//!   - per-Concept target read
//!   - committed-state read helper
//!   - apply_evidence_h: evidence injection into `external_field` (NOT
//!     Ising dynamics), used by the native self-worth bridge.
//!
//! Sym keys for attrs + edge types are passed in by the caller (the
//! Substrate owns the interner; we don't).

use crate::graph::{EdgeIdx, NodeID, TypedGraph};
use crate::sym::{Interner, Sym};
use crate::value::Value;
use rustc_hash::FxHashMap;
use std::sync::Arc;

/// Bundle of interned Sym keys + edge types this module reads. Built
/// once by the caller from the live interner and passed in to every op.
#[derive(Clone, Debug)]
pub struct CanKeys {
    /// Concept attr: σ ∈ [-1, +1], the current state of the node.
    pub state_attr: Sym,
    /// Concept attr: h ∈ R, the current external field on the node.
    /// Time-varying — evidence from world adapters writes here; decay
    /// reduces this term over time (recency bias).
    pub external_field_attr: Sym,
    /// Concept attr: identity field h_id ∈ R, the long-standing
    /// structural commitment. The relax + energy use h_eff = external +
    /// identity. Identity is NEVER frozen — strong-enough external
    /// evidence still overcomes it — but it resists ordinary
    /// perturbations and survives h-decay. Default 0 = no identity
    /// commitment.
    pub identity_field_attr: Sym,
    /// Concept attr: target σ* this Mt wants for the node (per-Mt encoding
    /// would be richer; for now we read a single attr).
    pub target_state_attr: Sym,
    /// Microtheory attr: β = inverse temperature (= attention on Mt).
    pub temperature_attr: Sym,
    /// Edge attr on causal_influence edges: J (signed coupling).
    pub weight_attr: Sym,
    /// Edge type connecting Mt → Concept.
    pub has_concept_edge: Sym,
    /// Edge type connecting Concept → Concept (signed coupling).
    pub causal_influence_edge: Sym,
}

/// Displacement from current ⟨σ⟩ to target ⟨σ⟩*. Per-node deviations,
/// total magnitude, and the dominant deviating node — the diagnostic
/// the substrate's "how wrong" queries return.
#[derive(Clone, Debug, Default)]
pub struct Displacement {
    pub per_node: Vec<(NodeID, f32)>,
    pub magnitude: f32,
    pub max_dev: Option<(NodeID, f32)>,
}

/// Write a float-typed node attribute (creates or updates).
fn set_node_float_attr(g: &mut TypedGraph, nid: NodeID, key: Sym, value: f32) {
    g.set_node_attr(nid, key, Value::Float(value as f64));
}

/// Read a float-typed node attribute, falling back to default if absent
/// or non-numeric.
fn node_float_attr(g: &TypedGraph, nid: NodeID, key: Sym, default: f32) -> f32 {
    for (k, v) in g.node(nid).attrs.iter() {
        if *k == key {
            return match v {
                Value::Float(f) => *f as f32,
                Value::Int(i) => *i as f32,
                _ => default,
            };
        }
    }
    default
}

/// Read a float-typed edge attribute, falling back to default if absent.
fn edge_float_attr(g: &TypedGraph, idx: EdgeIdx, key: Sym, default: f32) -> f32 {
    for (k, v) in g.edge_attrs(idx).iter() {
        if *k == key {
            return match v {
                Value::Float(f) => *f as f32,
                Value::Int(i) => *i as f32,
                _ => default,
            };
        }
    }
    default
}

/// Concepts owned by the Mt (via has_concept edges).
pub fn mt_concepts(g: &TypedGraph, mt_id: NodeID, has_concept: Sym) -> Vec<NodeID> {
    g.neighbours(mt_id, Some(has_concept))
}

/// Read a Concept's committed discrete `state` σ (default 0.0). Public
/// so callers (py.rs's native distance-to-target) can read the
/// discrete-async fixed point directly without a mean-field relaxation.
pub fn node_state(g: &TypedGraph, nid: NodeID, keys: &CanKeys) -> f32 {
    node_float_attr(g, nid, keys.state_attr, 0.0)
}

/// Enumerate every undirected coupling within Mt's concept set, deduped
/// across direction. Returns (i, j, J) tuples with i.0 < j.0 by
/// convention so each pair appears once. Walks both out- and in-edges
/// so a single directed edge in either direction is found regardless of
/// which endpoint comes first in NodeID order.
fn enumerate_couplings(
    g: &TypedGraph,
    concepts: &[NodeID],
    keys: &CanKeys,
) -> Vec<(NodeID, NodeID, f32)> {
    let concept_set: rustc_hash::FxHashSet<NodeID> = concepts.iter().copied().collect();
    let mut seen: rustc_hash::FxHashSet<(NodeID, NodeID)> = rustc_hash::FxHashSet::default();
    let mut out: Vec<(NodeID, NodeID, f32)> = Vec::new();
    for &i in concepts {
        for &idx in g.out_edges_slice(i, Some(keys.causal_influence_edge)) {
            let ed = g.edge(idx);
            if !concept_set.contains(&ed.tgt) {
                continue;
            }
            let (a, b) = if i.0 < ed.tgt.0 {
                (i, ed.tgt)
            } else {
                (ed.tgt, i)
            };
            if seen.insert((a, b)) {
                let w = edge_float_attr(g, idx, keys.weight_attr, 1.0);
                out.push((a, b, w));
            }
        }
        for &idx in g.in_edges_slice(i, Some(keys.causal_influence_edge)) {
            let ed = g.edge(idx);
            if !concept_set.contains(&ed.src) {
                continue;
            }
            let (a, b) = if i.0 < ed.src.0 {
                (i, ed.src)
            } else {
                (ed.src, i)
            };
            if seen.insert((a, b)) {
                let w = edge_float_attr(g, idx, keys.weight_attr, 1.0);
                out.push((a, b, w));
            }
        }
    }
    out
}

/// Energy H(σ) = -Σ_{i<j} J_ij σ_i σ_j - Σ_i h_i σ_i under Mt's H.
///
/// Counts each undirected coupling once via enumerate_couplings.
pub fn mt_energy(
    g: &TypedGraph,
    mt_id: NodeID,
    keys: &CanKeys,
    state: &FxHashMap<NodeID, f32>,
) -> f32 {
    let concepts = mt_concepts(g, mt_id, keys.has_concept_edge);
    let mut energy: f32 = 0.0;

    // Field term: -Σ (h_ext + h_id) σ_i — both external + identity
    // contribute to energy. Identity-violating basins cost energy here.
    for &c in &concepts {
        let h_ext = node_float_attr(g, c, keys.external_field_attr, 0.0);
        let h_id = node_float_attr(g, c, keys.identity_field_attr, 0.0);
        let sigma = state.get(&c).copied().unwrap_or(0.0);
        energy -= (h_ext + h_id) * sigma;
    }

    // Coupling term — once per undirected pair, regardless of edge
    // direction.
    for (i, j, w) in enumerate_couplings(g, &concepts, keys) {
        let si = state.get(&i).copied().unwrap_or(0.0);
        let sj = state.get(&j).copied().unwrap_or(0.0);
        energy -= w * si * sj;
    }

    energy
}

/// Frustration index given a state σ-map: sum of (actual - ideal)
/// contributions over couplings. Used by predictive insight-seeking to
/// rank candidate perturbations by predicted ΔF rather than ΔE — what
/// the insight detector actually uses. Pure read.
pub fn mt_frustration_given_state(
    g: &TypedGraph,
    mt_id: NodeID,
    keys: &CanKeys,
    state: &FxHashMap<NodeID, f32>,
) -> f32 {
    let concepts = mt_concepts(g, mt_id, keys.has_concept_edge);
    if concepts.is_empty() {
        return 0.0;
    }
    let mut frustration: f32 = 0.0;
    for (i, j, w) in enumerate_couplings(g, &concepts, keys) {
        let si = state.get(&i).copied().unwrap_or(0.0);
        let sj = state.get(&j).copied().unwrap_or(0.0);
        let actual = -w * si * sj;
        let ideal = -w.abs();
        frustration += actual - ideal;
    }
    frustration
}

/// Per-node + total displacement between current and target marginals.
/// Targets that don't have a corresponding current value are treated
/// as current = 0 (consistent with "Unknown = zero vector").
pub fn distance_to_target(
    current: &FxHashMap<NodeID, f32>,
    target: &FxHashMap<NodeID, f32>,
) -> Displacement {
    let mut per_node: Vec<(NodeID, f32)> = Vec::with_capacity(target.len());
    let mut sq_sum: f32 = 0.0;
    let mut max_dev: Option<(NodeID, f32)> = None;

    for (&n, &t) in target.iter() {
        let c = current.get(&n).copied().unwrap_or(0.0);
        let d = c - t;
        per_node.push((n, d));
        sq_sum += d * d;
        let take = match max_dev {
            Some((_, m)) => d.abs() > m.abs(),
            None => true,
        };
        if take {
            max_dev = Some((n, d));
        }
    }

    Displacement {
        per_node,
        magnitude: sq_sum.sqrt(),
        max_dev,
    }
}

/// Read the Mt's declared target ⟨σ⟩* — for now, the per-Concept
/// `target_state_attr`. Falls back to +1.0 for any Concept owned by Mt
/// without a target_state (Mt wants its concepts ON by default).
pub fn mt_target(g: &TypedGraph, mt_id: NodeID, keys: &CanKeys) -> FxHashMap<NodeID, f32> {
    let concepts = mt_concepts(g, mt_id, keys.has_concept_edge);
    concepts
        .into_iter()
        .map(|c| (c, node_float_attr(g, c, keys.target_state_attr, 1.0)))
        .collect()
}

// ============================================================================
// Mutation operations — evidence injection per self_improvement_dynamics Mt.
//
// The graded Hebbian / decay / identity-dynamics mutation ops were removed
// in the Phase A native-backend cutover — the discrete-native graph rules
// (seeds/can_native_reimplementation.json + seeds/can_decay_identity.json)
// are the sole mechanism for those. Only evidence injection
// (`apply_evidence_h`, which writes `external_field` and is NOT Ising
// dynamics) remains here, used by the native path
// (can_self_worth_bridge.record_incident_outcome).
// ============================================================================

/// Apply an evidence delta to a single Concept's external field.
///
///   h_i ← h_i + α · evidence
///
/// Used by world adapters when sensory / testimonial / structural evidence
/// arrives at a specific node. α is the reliability scale of the evidence
/// source.
pub fn apply_evidence_h(
    g: &mut TypedGraph,
    concept_id: NodeID,
    keys: &CanKeys,
    evidence: f32,
    alpha: f32,
) {
    let current = node_float_attr(g, concept_id, keys.external_field_attr, 0.0);
    set_node_float_attr(
        g,
        concept_id,
        keys.external_field_attr,
        current + alpha * evidence,
    );
}

// ============================================================================
// Detached finite SCM evaluation (P5.E3/R1).
// ============================================================================

#[derive(Clone)]
struct ScmEquation {
    target: String,
    parents: Vec<String>,
    exogenous: Vec<String>,
    rows: Vec<(Vec<(String, Value)>, Value)>,
}

fn scm_seq(value: &Value) -> Option<&[Value]> {
    match value {
        Value::List(items) | Value::Tuple(items) => Some(items.as_slice()),
        _ => None,
    }
}

fn scm_dict<'a>(value: &'a Value) -> Option<&'a [(Value, Value)]> {
    match value {
        Value::Dict(items) => Some(items.as_ref()),
        _ => None,
    }
}

fn scm_string(value: &Value, interner: &Interner) -> Option<String> {
    match value {
        Value::Str(value) => Some(interner.resolve(*value).to_owned()),
        _ => None,
    }
}

fn scm_get<'a>(value: &'a Value, key: &str, interner: &Interner) -> Option<&'a Value> {
    scm_dict(value)?.iter().find_map(|(k, v)| {
        (scm_string(k, interner).as_deref() == Some(key)).then_some(v)
    })
}

fn scm_record(interner: &mut Interner, fields: Vec<(&str, Value)>) -> Value {
    Value::Dict(Arc::from(fields.into_iter().map(|(key, value)| {
        (Value::Str(interner.intern(key)), value)
    }).collect::<Vec<_>>()))
}

fn scm_strings(value: &Value, interner: &Interner) -> Option<Vec<String>> {
    scm_seq(value)?.iter().map(|item| scm_string(item, interner)).collect()
}

fn scm_unknown(interner: &mut Interner, reason: &str, model: &Value) -> Value {
    let source_ids = scm_get(model, "source_ids", interner).cloned().unwrap_or(Value::None);
    let source_epoch = scm_get(model, "source_epoch", interner).cloned().unwrap_or(Value::None);
    let status = Value::Str(interner.intern("unknown"));
    let reason = Value::Str(interner.intern(reason));
    let empty = || Value::List(Arc::new(smallvec::SmallVec::new()));
    scm_record(interner, vec![
        ("status", status),
        ("values", empty()),
        ("assumptions", empty()),
        ("source_ids", source_ids), ("source_epoch", source_epoch),
        ("reason", reason),
    ])
}

fn scm_invalid(interner: &mut Interner, reason: &str, model: &Value) -> Value {
    let source_ids = scm_get(model, "source_ids", interner).cloned().unwrap_or(Value::None);
    let source_epoch = scm_get(model, "source_epoch", interner).cloned().unwrap_or(Value::None);
    let status = Value::Str(interner.intern("invalid"));
    let reason = Value::Str(interner.intern(reason));
    let empty = || Value::List(Arc::new(smallvec::SmallVec::new()));
    scm_record(interner, vec![
        ("status", status),
        ("values", empty()),
        ("assumptions", empty()),
        ("source_ids", source_ids), ("source_epoch", source_epoch),
        ("reason", reason),
    ])
}

fn scm_parse_named_values(value: &Value, interner: &Interner) -> Option<Vec<(String, Value)>> {
    let mut result = Vec::new();
    for (key, item) in scm_dict(value)? {
        result.push((scm_string(key, interner)?, item.clone()));
    }
    result.sort_by(|a, b| a.0.cmp(&b.0));
    if result.windows(2).any(|pair| pair[0].0 == pair[1].0) {
        return None;
    }
    Some(result)
}

fn scm_assignment_matches(
    row: &[(String, Value)],
    values: &[(String, Value)],
) -> bool {
    row.len() == values.len() && row.iter().all(|(key, value)| {
        values.iter().any(|(other_key, other_value)| key == other_key && value == other_value)
    })
}

fn scm_eval_one(
    order: &[String],
    equations: &[ScmEquation],
    exogenous: &[(String, Value)],
    intervention: &[(String, Value)],
) -> Option<Vec<(String, Value)>> {
    let mut values = exogenous.to_vec();
    for target in order {
        if let Some((_, forced)) = intervention.iter().find(|(key, _)| key == target) {
            values.push((target.clone(), forced.clone()));
            continue;
        }
        let equation = equations.iter().find(|equation| &equation.target == target)?;
        let mut inputs = Vec::new();
        for key in equation.parents.iter().chain(equation.exogenous.iter()) {
            inputs.push((key.clone(), values.iter().find(|(k, _)| k == key)?.1.clone()));
        }
        let output = equation.rows.iter().find(|(row, _)| scm_assignment_matches(row, &inputs))?.1.clone();
        values.push((target.clone(), output));
    }
    Some(values)
}

/// Evaluate a finite SCM over detached Value records. There is deliberately
/// no graph argument here: intervention is equation replacement, not mutation.
pub fn scm_intervene(
    model: &Value,
    query: &Value,
    intervention_value: &Value,
    assignments_value: &Value,
    assignment_cap_value: &Value,
    interner: &mut Interner,
) -> Value {
    let Some(cap) = (match assignment_cap_value { Value::Int(n) => usize::try_from(*n).ok(), _ => None }) else {
        return scm_invalid(interner, "assignment_cap_must_be_positive_integer", model);
    };
    if cap == 0 { return scm_invalid(interner, "assignment_cap_must_be_positive", model); }
    if cap > 4096 { return scm_unknown(interner, "assignment_cap_exceeds_4096", model); }

    let Some(kind) = scm_get(query, "kind", interner).and_then(|v| scm_string(v, interner)) else {
        return scm_invalid(interner, "query_kind_missing_or_invalid", model);
    };
    if !matches!(kind.as_str(), "effect" | "condition" | "unit_counterfactual") {
        return scm_invalid(interner, "unsupported_query_kind", model);
    }
    let Some(outcome) = scm_get(query, "outcome", interner).and_then(|v| scm_string(v, interner)) else {
        return scm_invalid(interner, "query_outcome_missing_or_invalid", model);
    };

    let Some(variable_values) = scm_get(model, "variables", interner).and_then(scm_seq) else {
        return scm_invalid(interner, "variables_missing_or_invalid", model);
    };
    if variable_values.is_empty() { return scm_unknown(interner, "empty_endogenous_model", model); }
    if variable_values.len() > 16 { return scm_unknown(interner, "endogenous_variable_bound_exceeded", model); }
    let mut domains: Vec<(String, Vec<Value>)> = Vec::new();
    for variable in variable_values {
        let Some(id) = scm_get(variable, "id", interner).and_then(|v| scm_string(v, interner)) else {
            return scm_invalid(interner, "variable_id_missing", model);
        };
        let Some(domain) = scm_get(variable, "domain", interner).and_then(scm_seq) else {
            return scm_invalid(interner, "variable_domain_missing", model);
        };
        if domain.is_empty() || domain.len() > 8 { return scm_unknown(interner, "variable_domain_bound_exceeded", model); }
        if domains.iter().any(|(known, _)| known == &id) { return scm_invalid(interner, "duplicate_variable_id", model); }
        domains.push((id, domain.to_vec()));
    }
    let Some(exogenous_values) = scm_get(model, "exogenous", interner).and_then(scm_seq) else {
        return scm_invalid(interner, "exogenous_variables_missing", model);
    };
    let mut exogenous_domains: Vec<(String, Vec<Value>)> = Vec::new();
    for variable in exogenous_values {
        let Some(id) = scm_get(variable, "id", interner).and_then(|v| scm_string(v, interner)) else {
            return scm_invalid(interner, "exogenous_id_missing", model);
        };
        let Some(domain) = scm_get(variable, "domain", interner).and_then(scm_seq) else {
            return scm_invalid(interner, "exogenous_domain_missing", model);
        };
        if domain.is_empty() || domain.len() > 8 { return scm_unknown(interner, "exogenous_domain_bound_exceeded", model); }
        if domains.iter().any(|(known, _)| known == &id) || exogenous_domains.iter().any(|(known, _)| known == &id) {
            return scm_invalid(interner, "duplicate_variable_id", model);
        }
        exogenous_domains.push((id, domain.to_vec()));
    }
    if !domains.iter().any(|(id, _)| id == &outcome) { return scm_invalid(interner, "outcome_not_endogenous", model); }

    let Some(equation_values) = scm_get(model, "equations", interner).and_then(scm_seq) else {
        return scm_invalid(interner, "equations_missing_or_invalid", model);
    };
    if equation_values.len() != domains.len() { return scm_unknown(interner, "incomplete_equation_set", model); }
    let mut equations = Vec::new();
    for equation in equation_values {
        let Some(target) = scm_get(equation, "target", interner).and_then(|v| scm_string(v, interner)) else {
            return scm_invalid(interner, "equation_target_missing", model);
        };
        if !domains.iter().any(|(id, _)| id == &target) || equations.iter().any(|e: &ScmEquation| e.target == target) {
            return scm_invalid(interner, "unknown_or_duplicate_equation_target", model);
        }
        let Some(parents) = scm_get(equation, "parents", interner).and_then(|v| scm_strings(v, interner)) else {
            return scm_invalid(interner, "equation_parents_invalid", model);
        };
        let Some(used_exogenous) = scm_get(equation, "exogenous", interner).and_then(|v| scm_strings(v, interner)) else {
            return scm_invalid(interner, "equation_exogenous_invalid", model);
        };
        if parents.iter().any(|id| !domains.iter().any(|(known, _)| known == id) || id == &target)
            || used_exogenous.iter().any(|id| !exogenous_domains.iter().any(|(known, _)| known == id)) {
            return scm_invalid(interner, "equation_references_unknown_variable", model);
        }
        let Some(rows) = scm_get(equation, "rows", interner).and_then(scm_seq) else {
            return scm_invalid(interner, "equation_rows_invalid", model);
        };
        let mut parsed_rows: Vec<(Vec<(String, Value)>, Value)> = Vec::new();
        for row in rows {
            let Some(inputs) = scm_get(row, "inputs", interner).and_then(|v| scm_parse_named_values(v, interner)) else {
                return scm_invalid(interner, "equation_row_inputs_invalid", model);
            };
            let Some(output) = scm_get(row, "value", interner).cloned() else {
                return scm_invalid(interner, "equation_row_value_missing", model);
            };
            if inputs.len() != parents.len() + used_exogenous.len()
                || inputs.iter().any(|(id, value)| {
                    if let Some((_, domain)) = domains.iter().find(|(known, _)| known == id) {
                        !parents.contains(id) || !domain.contains(value)
                    } else if let Some((_, domain)) = exogenous_domains.iter().find(|(known, _)| known == id) {
                        !used_exogenous.contains(id) || !domain.contains(value)
                    } else { true }
                })
                || domains.iter().find(|(id, _)| id == &target).is_some_and(|(_, d)| !d.contains(&output)) {
                return scm_invalid(interner, "equation_row_out_of_domain_or_wrong_inputs", model);
            }
            if parsed_rows.iter().any(|(old, _)| scm_assignment_matches(old, &inputs)) {
                return scm_invalid(interner, "duplicate_equation_row", model);
            }
            parsed_rows.push((inputs, output));
        }
        let expected_rows = parents.iter().chain(used_exogenous.iter()).try_fold(1usize, |n, id| {
            let size = domains.iter().chain(exogenous_domains.iter()).find(|(known, _)| known == id)?.1.len();
            n.checked_mul(size)
        });
        let Some(expected_rows) = expected_rows else { return scm_unknown(interner, "equation_table_bound_exceeded", model); };
        if expected_rows > cap { return scm_unknown(interner, "equation_table_bound_exceeded", model); }
        if parsed_rows.len() != expected_rows { return scm_unknown(interner, "incomplete_equation_table", model); }
        equations.push(ScmEquation { target, parents, exogenous: used_exogenous, rows: parsed_rows });
    }

    let mut order = Vec::new();
    while order.len() < domains.len() {
        let next = equations.iter().find(|equation| !order.contains(&equation.target)
            && equation.parents.iter().all(|parent| order.contains(parent))
            && equation.exogenous.iter().all(|id| exogenous_domains.iter().any(|(known, _)| known == id)))
            .map(|equation| equation.target.clone());
        let Some(next) = next else { return scm_unknown(interner, "cyclic_or_unresolved_model", model); };
        order.push(next);
    }

    let Some(intervention) = scm_parse_named_values(intervention_value, interner) else {
        return scm_invalid(interner, "intervention_not_a_dict", model);
    };
    if intervention.iter().any(|(id, value)| !domains.iter().any(|(known, domain)| known == id && domain.contains(value))) {
        return scm_invalid(interner, "intervention_out_of_domain", model);
    }
    let Some(assignments) = scm_seq(assignments_value) else { return scm_invalid(interner, "exogenous_assignments_not_a_list", model); };
    if assignments.is_empty() { return scm_unknown(interner, "empty_exogenous_assignment_set", model); }
    if assignments.len() > cap { return scm_unknown(interner, "assignment_bound_exceeded", model); }
    let mut parsed_assignments = Vec::new();
    for assignment in assignments {
        let Some(parsed) = scm_parse_named_values(assignment, interner) else { return scm_invalid(interner, "exogenous_assignment_invalid", model); };
        if parsed.len() != exogenous_domains.len() || parsed.iter().any(|(id, value)| {
            !exogenous_domains.iter().any(|(known, domain)| known == id && domain.contains(value))
        }) { return scm_invalid(interner, "exogenous_assignment_out_of_domain", model); }
        if parsed_assignments.iter().any(|old: &Vec<(String, Value)>| scm_assignment_matches(old, &parsed)) {
            return scm_invalid(interner, "duplicate_exogenous_assignment", model);
        }
        parsed_assignments.push(parsed);
    }

    let mut output_values = Vec::new();
    for exogenous in &parsed_assignments {
        match kind.as_str() {
            "effect" => {
                let Some(result) = scm_eval_one(&order, &equations, exogenous, &intervention) else {
                    return scm_unknown(interner, "equation_evaluation_failed", model);
                };
                let Some(value) = result.iter().find(|(id, _)| id == &outcome).map(|(_, v)| v.clone()) else {
                    return scm_unknown(interner, "outcome_unavailable", model);
                };
                output_values.push(value);
            }
            "condition" => {
                let Some(result) = scm_eval_one(&order, &equations, exogenous, &[]) else {
                    return scm_unknown(interner, "equation_evaluation_failed", model);
                };
                if intervention.iter().all(|(id, expected)| result.iter().any(|(key, value)| key == id && value == expected)) {
                    let Some(value) = result.iter().find(|(id, _)| id == &outcome).map(|(_, v)| v.clone()) else {
                        return scm_unknown(interner, "outcome_unavailable", model);
                    };
                    output_values.push(value);
                }
            }
            "unit_counterfactual" => {
                let Some(factual) = scm_eval_one(&order, &equations, exogenous, &[]) else {
                    return scm_unknown(interner, "factual_evaluation_failed", model);
                };
                let Some(counterfactual) = scm_eval_one(&order, &equations, exogenous, &intervention) else {
                    return scm_unknown(interner, "counterfactual_evaluation_failed", model);
                };
                let factual = factual.iter().find(|(id, _)| id == &outcome).map(|(_, v)| v.clone()).unwrap_or(Value::None);
                let counterfactual = counterfactual.iter().find(|(id, _)| id == &outcome).map(|(_, v)| v.clone()).unwrap_or(Value::None);
                output_values.push(scm_record(interner, vec![("factual", factual), ("counterfactual", counterfactual)]));
            }
            _ => unreachable!(),
        }
    }
    let source_ids = scm_get(model, "source_ids", interner).cloned().unwrap_or(Value::None);
    let source_epoch = scm_get(model, "source_epoch", interner).cloned().unwrap_or(Value::None);
    let assumption = if kind == "effect" { "uniform_exogenous_assignments" } else { "shared_supplied_exogenous_assignments" };
    let status = Value::Str(interner.intern("identified"));
    let assumption = Value::Str(interner.intern(assumption));
    scm_record(interner, vec![
        ("status", status),
        ("values", Value::List(Arc::new(output_values.into()))),
        ("assumptions", Value::List(Arc::new(smallvec::smallvec![assumption]))),
        ("source_ids", source_ids), ("source_epoch", source_epoch), ("reason", Value::None),
    ])
}

#[cfg(test)]
mod scm_intervene_tests {
    use super::*;
    fn value(json: serde_json::Value, interner: &mut Interner) -> Value {
        match json {
            serde_json::Value::Null => Value::None,
            serde_json::Value::Bool(v) => Value::Bool(v),
            serde_json::Value::Number(v) => Value::Int(v.as_i64().unwrap()),
            serde_json::Value::String(v) => Value::Str(interner.intern(&v)),
            serde_json::Value::Array(v) => Value::List(Arc::new(v.into_iter().map(|x| value(x, interner)).collect::<Vec<_>>().into())),
            serde_json::Value::Object(v) => Value::Dict(Arc::from(v.into_iter().map(|(k, x)| (Value::Str(interner.intern(&k)), value(x, interner))).collect::<Vec<_>>())),
        }
    }

    fn fixtures(interner: &mut Interner) -> (Value, Value, Value, Value) {
        let model = serde_json::json!({
            "variables":[{"id":"X","domain":[0,1]},{"id":"Y","domain":[0,1]}],
            "exogenous":[{"id":"U","domain":[0,1]}],
            "equations":[
                {"target":"X","parents":[],"exogenous":["U"],"rows":[{"inputs":{"U":0},"value":0},{"inputs":{"U":1},"value":1}]},
                {"target":"Y","parents":[],"exogenous":["U"],"rows":[{"inputs":{"U":0},"value":0},{"inputs":{"U":1},"value":1}]}
            ],
            "source_ids":["mechanism-1"],"source_epoch":7
        });
        let assignments = serde_json::json!([{"U":0},{"U":1}]);
        let intervention = serde_json::json!({"X":1});
        let query = |kind: &str| serde_json::json!({"kind":kind,"outcome":"Y"});
        (value(model, interner), value(assignments, interner), value(intervention, interner), value(query("effect"), interner))
    }

    fn status<'a>(result: &'a Value, interner: &'a Interner) -> String {
        scm_get(result, "status", interner).and_then(|v| scm_string(v, interner)).unwrap()
    }

    #[test]
    fn scm_do_cuts_equation_and_condition_filters_population() {
        let mut interner = Interner::new();
        let (model, assignments, intervention, query) = fixtures(&mut interner);
        let effect = scm_intervene(&model, &query, &intervention, &assignments, &Value::Int(16), &mut interner);
        assert_eq!(status(&effect, &interner), "identified");
        assert_eq!(scm_get(&effect, "values", &interner).and_then(scm_seq).unwrap(),
                   &[Value::Int(0), Value::Int(1)]);
        let condition_query = value(serde_json::json!({"kind":"condition","outcome":"Y"}), &mut interner);
        let condition = scm_intervene(&model, &condition_query, &intervention, &assignments, &Value::Int(16), &mut interner);
        assert_eq!(scm_get(&condition, "values", &interner).and_then(scm_seq).unwrap(),
                   &[Value::Int(1)]);
    }

    #[test]
    fn scm_counterfactual_reuses_each_exogenous_assignment() {
        let mut interner = Interner::new();
        let (model, assignments, intervention, _) = fixtures(&mut interner);
        let query = value(serde_json::json!({"kind":"unit_counterfactual","outcome":"Y"}), &mut interner);
        let result = scm_intervene(&model, &query, &intervention, &assignments, &Value::Int(16), &mut interner);
        let values = scm_get(&result, "values", &interner).and_then(scm_seq).unwrap();
        assert_eq!(scm_get(&values[0], "factual", &interner), Some(&Value::Int(0)));
        assert_eq!(scm_get(&values[0], "counterfactual", &interner), Some(&Value::Int(0)));
        assert_eq!(scm_get(&values[1], "factual", &interner), Some(&Value::Int(1)));
        assert_eq!(scm_get(&values[1], "counterfactual", &interner), Some(&Value::Int(1)));
    }

    #[test]
    fn scm_empty_malformed_cyclic_and_bounded_inputs_abstain_or_refuse() {
        let mut interner = Interner::new();
        let (valid, assignments, intervention, query_effect) = fixtures(&mut interner);
        let empty = scm_intervene(&valid, &query_effect, &intervention, &Value::List(Arc::new(smallvec::SmallVec::new())),
                                  &Value::Int(16), &mut interner);
        assert_eq!(status(&empty, &interner), "unknown");
        let cyc = value(serde_json::json!({
            "variables":[{"id":"X","domain":[0,1]},{"id":"Y","domain":[0,1]}],
            "exogenous":[],
            "equations":[
                {"target":"X","parents":["Y"],"exogenous":[],"rows":[{"inputs":{"Y":0},"value":0},{"inputs":{"Y":1},"value":1}]},
                {"target":"Y","parents":["X"],"exogenous":[],"rows":[{"inputs":{"X":0},"value":0},{"inputs":{"X":1},"value":1}]}
            ], "source_ids":[],"source_epoch":1
        }), &mut interner);
        let cycle_result = scm_intervene(&cyc, &query_effect, &intervention, &assignments,
            &Value::Int(16), &mut interner);
        assert_eq!(status(&cycle_result, &interner), "unknown");
        let bounded = scm_intervene(&valid, &query_effect, &intervention, &assignments,
            &Value::Int(1), &mut interner);
        assert_eq!(status(&bounded, &interner), "unknown");
        let malformed = scm_intervene(&Value::None, &query_effect, &intervention,
            &assignments, &Value::Int(16), &mut interner);
        assert_eq!(status(&malformed, &interner), "invalid");
    }
}
