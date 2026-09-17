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
use crate::sym::Sym;
use crate::value::Value;
use rustc_hash::FxHashMap;

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
