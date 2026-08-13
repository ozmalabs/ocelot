//! Causal Attitude Network operations on the substrate's typed graph.
//!
//! The substrate's grounding model rests on:
//!   - Axiom 0 (philosophy): truth is frame-relative
//!   - grounding_theory: therefore grounding is a vector, not a boolean
//!   - causal_attitude_networks: the vector is the marginal ⟨σ⟩ at
//!     equilibrium of an Ising-style network — σ + J + h + β + H
//!   - mt_target_equilibria: each Mt's admissibility grammar IS its
//!     Hamiltonian
//!
//! This module implements the core operations:
//!   - mean-field marginal ⟨σ⟩_Mt by tanh self-consistency
//!   - energy H(σ) under Mt's Hamiltonian
//!   - distance from current to target (vector + magnitude)
//!   - basin audit (depth, distinctness, coverage, frustration)
//!
//! Pure reads — no graph mutation. Mutation paths (Hebbian J updates,
//! evidence-driven h updates, β reweighting) live elsewhere and go
//! through the substrate's normal admissibility check.
//!
//! Sym keys for attrs + edge types are passed in by the caller (the
//! Substrate owns the interner; we don't).

use crate::graph::{EdgeIdx, NodeID, TypedGraph};
use crate::sym::Sym;
use crate::value::Value;
use rustc_hash::FxHashMap;

/// Default damping factor λ for the mean-field relaxation's update rule
/// (`new_sigma = (1-λ)·old_sigma + λ·tanh(β·local)`). λ=0.5 is a
/// literature-common default for damped fixed-point/loopy-BP iteration
/// (Murphy, Weiss & Jordan 1999 and the broader damped-BP literature;
/// see CAN_SYNCHRONOUS_UPDATE_FIX_PREREG.md §2 — reported at
/// search-synthesis confidence, not independently re-derived from primary
/// text). Used by every internal call site that does not expose damping
/// as a caller-facing parameter (`audit_basin`, `mt_conflicting_nodes`,
/// `mt_pairwise_similarity`), so the fix applies by default wherever these
/// diagnostics are read, not only where a caller opts in. λ=1.0 recovers
/// the OLD fully-synchronous (Jacobi) update rule exactly:
/// `(1-1.0)·old + 1.0·raw == raw`.
pub const DEFAULT_DAMPING: f32 = 0.5;

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

/// Audit of an Mt's basin topology — what mt_target_equilibria +
/// self_improvement_dynamics need to detect failure modes.
#[derive(Clone, Debug)]
pub struct BasinReport {
    pub mt_id: NodeID,
    pub concept_count: usize,
    pub coupling_count: usize,
    /// ⟨σ⟩_Mt at mean-field equilibrium.
    pub marginal: FxHashMap<NodeID, f32>,
    /// H(⟨σ⟩) — lower is deeper basin.
    pub energy: f32,
    /// Number of concepts with |⟨σ_i⟩| > 0.05 (engaged nodes).
    pub coverage: usize,
    /// Frustration index — sum of (actual - ideal) coupling contributions
    /// at the mean-field solution. Higher → more spin-glass frustration.
    pub frustration: f32,
}

impl BasinReport {
    /// Empty report for an Mt with no concepts; carries the mt_id only.
    fn empty(mt_id: NodeID) -> Self {
        Self {
            mt_id,
            concept_count: 0,
            coupling_count: 0,
            marginal: FxHashMap::default(),
            energy: 0.0,
            coverage: 0,
            frustration: 0.0,
        }
    }
}

/// Write a float-typed edge attribute (creates or updates).
fn set_edge_float_attr(g: &mut TypedGraph, idx: EdgeIdx, key: Sym, value: f32) {
    g.edge_attrs_mut(idx).insert(key, Value::Float(value as f64));
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

/// Build per-concept coupling table: concept → list of (neighbour, J).
/// Walks both out- and in- causal_influence edges so the table is
/// symmetric for undirected interpretation.
fn build_couplings(
    g: &TypedGraph,
    concepts: &[NodeID],
    keys: &CanKeys,
) -> FxHashMap<NodeID, Vec<(NodeID, f32)>> {
    let mut out: FxHashMap<NodeID, Vec<(NodeID, f32)>> = FxHashMap::default();
    let concept_set: rustc_hash::FxHashSet<NodeID> = concepts.iter().copied().collect();
    for &c in concepts {
        let mut neigh: Vec<(NodeID, f32)> = Vec::new();
        // Out-edges
        for idx in g.out_edges_slice(c, Some(keys.causal_influence_edge)) {
            let ed = g.edge(*idx);
            if concept_set.contains(&ed.tgt) {
                let w = edge_float_attr(g, *idx, keys.weight_attr, 1.0);
                neigh.push((ed.tgt, w));
            }
        }
        // In-edges (for symmetric reading without requiring caller to
        // double-insert each undirected coupling).
        for idx in g.in_edges_slice(c, Some(keys.causal_influence_edge)) {
            let ed = g.edge(*idx);
            if concept_set.contains(&ed.src) {
                let w = edge_float_attr(g, *idx, keys.weight_attr, 1.0);
                // Avoid double-counting if the same edge already appeared
                // (graph might have explicit edges in both directions).
                if !neigh.iter().any(|(n, _)| *n == ed.src) {
                    neigh.push((ed.src, w));
                }
            }
        }
        out.insert(c, neigh);
    }
    out
}

/// Mean-field marginal ⟨σ⟩ under Mt's Hamiltonian.
///
/// Iterates the DAMPED self-consistency equation
///   σ_i ← (1-λ)·σ_i + λ·tanh(β (Σ_j J_ij σ_j + h_i))
/// until either max_iter is reached or the largest single-node change
/// falls below `tol`. The sweep itself is still synchronous (every node's
/// update in one sweep reads the PREVIOUS sweep's full state) — damping
/// does not change that — but blending each step with the prior value is
/// the standard, literature-established fix for the persistent period-2
/// limit cycle a fully synchronous (λ=1.0) fixed-point iteration is prone
/// to on frustrated/loopy networks (Murphy, Weiss & Jordan 1999; see
/// CAN_SYNCHRONOUS_UPDATE_FIX_PREREG.md/_RESULTS.md). Damping cannot move
/// or remove a genuine fixed point (at a fixed point old==raw_new, so the
/// blend is a no-op there for any λ) — it only changes the trajectory used
/// to reach one.
///
/// β is read from the Mt's `temperature_attr` (default 1.0).
/// h_i is read from each Concept's `external_field_attr` (default 0.0).
/// J_ij is read from `causal_influence` edges' `weight_attr` (default 1.0).
/// Initial σ_i is read from each Concept's `state_attr` (default 0.0).
/// `damping` (λ) ∈ (0.0, 1.0]; λ=1.0 recovers the old undamped update
/// exactly. See `DEFAULT_DAMPING`.
pub fn mt_mean_field_marginal(
    g: &TypedGraph,
    mt_id: NodeID,
    keys: &CanKeys,
    max_iter: usize,
    tol: f32,
    damping: f32,
) -> FxHashMap<NodeID, f32> {
    let concepts = mt_concepts(g, mt_id, keys.has_concept_edge);
    if concepts.is_empty() {
        return FxHashMap::default();
    }

    let beta = node_float_attr(g, mt_id, keys.temperature_attr, 1.0);
    // Effective field per node: external_field + identity_field.
    // Identity is part of h for the mean-field; resistance to
    // perturbation is structural, not a frozen flag.
    let fields: FxHashMap<NodeID, f32> = concepts
        .iter()
        .map(|&c| {
            let ext = node_float_attr(g, c, keys.external_field_attr, 0.0);
            let identity = node_float_attr(g, c, keys.identity_field_attr, 0.0);
            (c, ext + identity)
        })
        .collect();
    let couplings = build_couplings(g, &concepts, keys);

    let mut state: FxHashMap<NodeID, f32> = concepts
        .iter()
        .map(|&c| (c, node_float_attr(g, c, keys.state_attr, 0.0)))
        .collect();

    for _ in 0..max_iter {
        let mut new_state: FxHashMap<NodeID, f32> =
            FxHashMap::with_capacity_and_hasher(concepts.len(), Default::default());
        let mut max_change: f32 = 0.0;
        for &c in &concepts {
            let h = *fields.get(&c).unwrap_or(&0.0);
            let mut local = h;
            if let Some(neigh) = couplings.get(&c) {
                for &(j, w) in neigh {
                    let sj = state.get(&j).copied().unwrap_or(0.0);
                    local += w * sj;
                }
            }
            let raw_sigma = (beta * local).tanh();
            let old_sigma = state.get(&c).copied().unwrap_or(0.0);
            let new_sigma = (1.0 - damping) * old_sigma + damping * raw_sigma;
            let change = (new_sigma - old_sigma).abs();
            if change > max_change {
                max_change = change;
            }
            new_state.insert(c, new_sigma);
        }
        state = new_state;
        if max_change < tol {
            break;
        }
    }

    state
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
    let mut seen: rustc_hash::FxHashSet<(NodeID, NodeID)> =
        rustc_hash::FxHashSet::default();
    let mut out: Vec<(NodeID, NodeID, f32)> = Vec::new();
    for &i in concepts {
        for &idx in g.out_edges_slice(i, Some(keys.causal_influence_edge)) {
            let ed = g.edge(idx);
            if !concept_set.contains(&ed.tgt) {
                continue;
            }
            let (a, b) = if i.0 < ed.tgt.0 { (i, ed.tgt) } else { (ed.tgt, i) };
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
            let (a, b) = if i.0 < ed.src.0 { (i, ed.src) } else { (ed.src, i) };
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

/// Audit Mt's basin topology — depth (negative energy at marginal),
/// coverage (engaged concepts), frustration (sum of unsatisfied coupling
/// contributions at mean-field solution).
pub fn audit_basin(g: &TypedGraph, mt_id: NodeID, keys: &CanKeys) -> BasinReport {
    let concepts = mt_concepts(g, mt_id, keys.has_concept_edge);
    if concepts.is_empty() {
        return BasinReport::empty(mt_id);
    }

    // Enumerate undirected couplings once (handles cycles correctly).
    let couplings = enumerate_couplings(g, &concepts, keys);
    let coupling_count = couplings.len();

    let marginal = mt_mean_field_marginal(g, mt_id, keys, 200, 1e-4, DEFAULT_DAMPING);
    let energy = mt_energy(g, mt_id, keys, &marginal);
    let coverage = marginal.values().filter(|v| v.abs() > 0.05).count();

    // Frustration: at the mean-field solution, sum over each coupling
    // of (actual contribution - ideal contribution). Ideal is the most
    // negative possible value -|J|, achieved when sgn(σ_i)·sgn(σ_j) =
    // sgn(J). A perfectly satisfied network has frustration ≈ 0.
    let mut frustration: f32 = 0.0;
    for (i, j, w) in couplings {
        let si = marginal.get(&i).copied().unwrap_or(0.0);
        let sj = marginal.get(&j).copied().unwrap_or(0.0);
        let actual = -w * si * sj;
        let ideal = -w.abs();
        frustration += actual - ideal;
    }

    BasinReport {
        mt_id,
        concept_count: concepts.len(),
        coupling_count,
        marginal,
        energy,
        coverage,
        frustration,
    }
}

// ============================================================================
// Predictive what-if operations — predictive insight-seeking.
//
// To answer "would perturbing h on this node release frustration?", run
// the mean-field with one h substituted, without touching the graph.
// Pure read; no mutation.
// ============================================================================

/// Mean-field marginal with one Concept's external field overridden.
/// The graph isn't modified. Returns the marginal that WOULD result
/// from setting node `override_node`'s external_field to `override_h`
/// and relaxing. Identity_field on the override node STILL applies —
/// only external_field is substituted, since identity is the structural
/// commitment a what-if perturbation doesn't reach into.
pub fn mt_mean_field_with_h_override(
    g: &TypedGraph,
    mt_id: NodeID,
    keys: &CanKeys,
    override_node: NodeID,
    override_h: f32,
    max_iter: usize,
    tol: f32,
    damping: f32,
) -> FxHashMap<NodeID, f32> {
    let concepts = mt_concepts(g, mt_id, keys.has_concept_edge);
    if concepts.is_empty() {
        return FxHashMap::default();
    }

    let beta = node_float_attr(g, mt_id, keys.temperature_attr, 1.0);
    let mut fields: FxHashMap<NodeID, f32> = concepts
        .iter()
        .map(|&c| {
            let ext = node_float_attr(g, c, keys.external_field_attr, 0.0);
            let identity = node_float_attr(g, c, keys.identity_field_attr, 0.0);
            (c, ext + identity)
        })
        .collect();
    // Substitute the override: external_field becomes override_h, but
    // identity_field on this node still contributes.
    let override_identity = node_float_attr(g, override_node,
                                             keys.identity_field_attr, 0.0);
    fields.insert(override_node, override_h + override_identity);

    let couplings = build_couplings(g, &concepts, keys);

    let mut state: FxHashMap<NodeID, f32> = concepts
        .iter()
        .map(|&c| (c, node_float_attr(g, c, keys.state_attr, 0.0)))
        .collect();

    for _ in 0..max_iter {
        let mut new_state: FxHashMap<NodeID, f32> =
            FxHashMap::with_capacity_and_hasher(concepts.len(), Default::default());
        let mut max_change: f32 = 0.0;
        for &c in &concepts {
            let h = *fields.get(&c).unwrap_or(&0.0);
            let mut local = h;
            if let Some(neigh) = couplings.get(&c) {
                for &(j, w) in neigh {
                    let sj = state.get(&j).copied().unwrap_or(0.0);
                    local += w * sj;
                }
            }
            let raw_sigma = (beta * local).tanh();
            let old_sigma = state.get(&c).copied().unwrap_or(0.0);
            let new_sigma = (1.0 - damping) * old_sigma + damping * raw_sigma;
            let change = (new_sigma - old_sigma).abs();
            if change > max_change {
                max_change = change;
            }
            new_state.insert(c, new_sigma);
        }
        state = new_state;
        if max_change < tol {
            break;
        }
    }
    state
}

/// Per-Concept frustration contribution: sum of (actual - ideal) over
/// the node's couplings under current state. High value = node is
/// involved in many unsatisfied constraints.
///
/// Computed as ⟨σ⟩-based: uses node_float_attr(state) — caller is
/// responsible for ensuring state reflects current equilibrium (call
/// relax_to_marginal first).
pub fn node_local_frustration(
    g: &TypedGraph,
    mt_id: NodeID,
    keys: &CanKeys,
    concept_id: NodeID,
) -> f32 {
    let concepts = mt_concepts(g, mt_id, keys.has_concept_edge);
    let concept_set: rustc_hash::FxHashSet<NodeID> = concepts.iter().copied().collect();
    if !concept_set.contains(&concept_id) {
        return 0.0;
    }
    let si = node_float_attr(g, concept_id, keys.state_attr, 0.0);
    let mut local: f32 = 0.0;
    let mut seen: rustc_hash::FxHashSet<NodeID> = rustc_hash::FxHashSet::default();
    // Walk both directions so cycle-closing edges aren't missed.
    for &idx in g.out_edges_slice(concept_id, Some(keys.causal_influence_edge)) {
        let ed = g.edge(idx);
        if concept_set.contains(&ed.tgt) && seen.insert(ed.tgt) {
            let sj = node_float_attr(g, ed.tgt, keys.state_attr, 0.0);
            let w = edge_float_attr(g, idx, keys.weight_attr, 1.0);
            local += (-w * si * sj) - (-w.abs());
        }
    }
    for &idx in g.in_edges_slice(concept_id, Some(keys.causal_influence_edge)) {
        let ed = g.edge(idx);
        if concept_set.contains(&ed.src) && seen.insert(ed.src) {
            let sj = node_float_attr(g, ed.src, keys.state_attr, 0.0);
            let w = edge_float_attr(g, idx, keys.weight_attr, 1.0);
            local += (-w * si * sj) - (-w.abs());
        }
    }
    local
}

/// Cross-Mt conflicting nodes — shared Concepts where mt_a's marginal
/// σ and mt_b's marginal σ have opposite signs AND both magnitudes
/// exceed `magnitude_threshold`. Implements the agent's spec for
/// fail_mode_conflicting_reflexes from self_improvement_dynamics:
/// "Two Mts driving same node h_i in opposite directions, both with
/// high β."
///
/// Returns a Vec of (node, sigma_a, sigma_b) for each conflicted node.
/// Each Mt's marginal is independently re-relaxed so the conflict
/// reflects each Mt's autonomous commitment under its own H.
pub fn mt_conflicting_nodes(
    g: &TypedGraph,
    mt_a: NodeID,
    mt_b: NodeID,
    keys: &CanKeys,
    magnitude_threshold: f32,
) -> Vec<(NodeID, f32, f32)> {
    let marginal_a = mt_mean_field_marginal(g, mt_a, keys, 200, 1e-4, DEFAULT_DAMPING);
    let marginal_b = mt_mean_field_marginal(g, mt_b, keys, 200, 1e-4, DEFAULT_DAMPING);

    let mut conflicts: Vec<(NodeID, f32, f32)> = Vec::new();
    for (c, &sigma_a) in marginal_a.iter() {
        if let Some(&sigma_b) = marginal_b.get(c) {
            if sigma_a * sigma_b < 0.0
                && sigma_a.abs() > magnitude_threshold
                && sigma_b.abs() > magnitude_threshold
            {
                conflicts.push((*c, sigma_a, sigma_b));
            }
        }
    }
    conflicts
}

/// Cross-Mt cosine similarity over the σ vectors restricted to shared
/// Concepts. Each Mt's marginal is recomputed independently (its own
/// Hamiltonian over its own couplings) so the comparison reflects
/// "given the same current evidence, would these two Mts converge to
/// similar commitments on the nodes they share?" — the substrate's
/// own definition of redundancy from self_improvement_dynamics.
///
/// Returns (similarity, shared_concept_count). similarity ∈ [-1, +1];
/// 0.0 if no shared concepts or either norm is degenerate.
pub fn mt_pairwise_similarity(
    g: &TypedGraph,
    mt_a: NodeID,
    mt_b: NodeID,
    keys: &CanKeys,
) -> (f32, usize) {
    let marginal_a = mt_mean_field_marginal(g, mt_a, keys, 200, 1e-4, DEFAULT_DAMPING);
    let marginal_b = mt_mean_field_marginal(g, mt_b, keys, 200, 1e-4, DEFAULT_DAMPING);

    let mut dot: f32 = 0.0;
    let mut norm_a_sq: f32 = 0.0;
    let mut norm_b_sq: f32 = 0.0;
    let mut shared_count: usize = 0;

    for (c, &sigma_a) in marginal_a.iter() {
        if let Some(&sigma_b) = marginal_b.get(c) {
            dot += sigma_a * sigma_b;
            norm_a_sq += sigma_a * sigma_a;
            norm_b_sq += sigma_b * sigma_b;
            shared_count += 1;
        }
    }

    if shared_count == 0 || norm_a_sq < 1e-10 || norm_b_sq < 1e-10 {
        return (0.0, shared_count);
    }
    let similarity = dot / (norm_a_sq.sqrt() * norm_b_sq.sqrt());
    (similarity, shared_count)
}

// ============================================================================
// Mutation operations — dynamic updates per self_improvement_dynamics Mt.
//
// CRUCIAL: policy enforcement (frozen vs adaptive Mts) lives in the Python
// orchestration layer, NOT here. These are pure mechanism. The caller is
// responsible for not invoking Hebbian on a frozen Mt's identity-preserving
// edges.
// ============================================================================

/// Hebbian J update — strengthens couplings between co-active concepts.
///
/// For each causal_influence edge (i, j) within Mt, applies:
///   J_ij ← J_ij + η · σ_i · σ_j
///
/// Reads current state σ from each Concept's `state_attr`. Writes the
/// updated weight back to the edge's `weight_attr`. Returns the number
/// of edges updated.
///
/// Standard learning rule: "fire together, wire together". With σ_i + σ_j
/// of same sign (both ON or both OFF), J grows. Opposite signs: J shrinks
/// (toward negative coupling).
///
/// The caller must verify the Mt's update_policy allows Hebbian — this
/// function performs the mechanism without policy check.
pub fn hebbian_update_J(
    g: &mut TypedGraph,
    mt_id: NodeID,
    keys: &CanKeys,
    eta: f32,
) -> usize {
    let concepts = mt_concepts(g, mt_id, keys.has_concept_edge);
    if concepts.is_empty() {
        return 0;
    }
    let concept_set: rustc_hash::FxHashSet<NodeID> = concepts.iter().copied().collect();

    // Read all current states first (avoid borrow conflict).
    let states: FxHashMap<NodeID, f32> = concepts
        .iter()
        .map(|&c| (c, node_float_attr(g, c, keys.state_attr, 0.0)))
        .collect();

    // Collect (idx, new_weight) pairs by walking each undirected coupling
    // once (i.0 < j.0).
    let mut updates: Vec<(EdgeIdx, f32)> = Vec::new();
    for &i in &concepts {
        for &idx in g.out_edges_slice(i, Some(keys.causal_influence_edge)) {
            let ed = g.edge(idx);
            let j = ed.tgt;
            if !concept_set.contains(&j) || i.0 >= j.0 {
                continue;
            }
            let current = edge_float_attr(g, idx, keys.weight_attr, 1.0);
            let si = *states.get(&i).unwrap_or(&0.0);
            let sj = *states.get(&j).unwrap_or(&0.0);
            let delta = eta * si * sj;
            updates.push((idx, current + delta));
        }
    }

    // Apply updates.
    let count = updates.len();
    for (idx, new_w) in updates {
        set_edge_float_attr(g, idx, keys.weight_attr, new_w);
    }
    count
}

/// Anti-Hebbian J decay — couplings fade absent reinforcement.
///
///   J_ij ← (1 - λ) · J_ij
///
/// Applied to every causal_influence edge in Mt. Returns the number of
/// edges decayed. With Hebbian + decay running together, persistent
/// co-activation maintains J; transient co-activation fades.
pub fn decay_J(
    g: &mut TypedGraph,
    mt_id: NodeID,
    keys: &CanKeys,
    decay_rate: f32,
) -> usize {
    let concepts = mt_concepts(g, mt_id, keys.has_concept_edge);
    if concepts.is_empty() {
        return 0;
    }
    let concept_set: rustc_hash::FxHashSet<NodeID> = concepts.iter().copied().collect();

    let mut updates: Vec<(EdgeIdx, f32)> = Vec::new();
    for &i in &concepts {
        for &idx in g.out_edges_slice(i, Some(keys.causal_influence_edge)) {
            let ed = g.edge(idx);
            let j = ed.tgt;
            if !concept_set.contains(&j) || i.0 >= j.0 {
                continue;
            }
            let current = edge_float_attr(g, idx, keys.weight_attr, 1.0);
            updates.push((idx, current * (1.0 - decay_rate)));
        }
    }

    let count = updates.len();
    for (idx, new_w) in updates {
        set_edge_float_attr(g, idx, keys.weight_attr, new_w);
    }
    count
}

/// Identity dynamics — h_id slowly tracks sustained σ.
///
/// For each Concept owned by Mt:
///   identity_field ← identity_field + α · σ - β · identity_field
///
/// Sustained positive σ → identity grows positive (substrate "becomes"
/// what it consistently is). Sustained negative σ → identity grows
/// negative. Flipping σ averages to near zero → identity decays toward
/// zero (no commitment to either basin).
///
/// The decay term β · identity_field gives identity a slow half-life
/// in the absence of reinforcement. Identity is never frozen — without
/// being reinforced, it fades. With reinforcement, it strengthens.
///
/// Returns the number of Concepts updated.
pub fn update_identity_dynamics(
    g: &mut TypedGraph,
    mt_id: NodeID,
    keys: &CanKeys,
    alpha: f32,
    beta: f32,
) -> usize {
    let concepts = mt_concepts(g, mt_id, keys.has_concept_edge);
    let mut updates: Vec<(NodeID, f32)> = Vec::with_capacity(concepts.len());
    for &c in &concepts {
        let sigma = node_float_attr(g, c, keys.state_attr, 0.0);
        let identity = node_float_attr(g, c, keys.identity_field_attr, 0.0);
        let new_identity = identity + alpha * sigma - beta * identity;
        updates.push((c, new_identity));
    }
    let count = updates.len();
    for (nid, new_id) in updates {
        set_node_float_attr(g, nid, keys.identity_field_attr, new_id);
    }
    count
}

/// Single-Concept identity nudge — used during insight consolidation.
///
/// identity_field ← identity_field + α · target_sigma
///
/// Larger α than the per-step dynamics: when an insight commits the
/// substrate to a new σ, the corresponding identity moves immediately
/// rather than waiting many steps. If the same basin recurs (same
/// fingerprint), the caller can pass a larger α to reflect that the
/// substrate has been here before.
pub fn nudge_identity(
    g: &mut TypedGraph,
    concept_id: NodeID,
    keys: &CanKeys,
    target_sigma: f32,
    alpha: f32,
) {
    let current = node_float_attr(g, concept_id, keys.identity_field_attr, 0.0);
    set_node_float_attr(
        g,
        concept_id,
        keys.identity_field_attr,
        current + alpha * target_sigma,
    );
}

/// External-field decay — evidence loses weight over time.
///
///   h_i ← (1 - γ) · h_i
///
/// Applied to every Concept in Mt. Returns the number of fields decayed.
/// Recency bias built in: old evidence fades unless reinforced.
pub fn decay_h(
    g: &mut TypedGraph,
    mt_id: NodeID,
    keys: &CanKeys,
    decay_rate: f32,
) -> usize {
    let concepts = mt_concepts(g, mt_id, keys.has_concept_edge);
    let mut updates: Vec<(NodeID, f32)> = Vec::with_capacity(concepts.len());
    for &c in &concepts {
        let current = node_float_attr(g, c, keys.external_field_attr, 0.0);
        if current.abs() > f32::EPSILON {
            updates.push((c, current * (1.0 - decay_rate)));
        }
    }
    let count = updates.len();
    for (nid, new_h) in updates {
        set_node_float_attr(g, nid, keys.external_field_attr, new_h);
    }
    count
}

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
    set_node_float_attr(g, concept_id, keys.external_field_attr, current + alpha * evidence);
}

/// Relax the network: write the mean-field marginal back to each
/// Concept's `state_attr`. After this, dynamic ops that read σ see the
/// equilibrium value rather than the stale prior.
pub fn relax_to_marginal(
    g: &mut TypedGraph,
    mt_id: NodeID,
    keys: &CanKeys,
    max_iter: usize,
    tol: f32,
    damping: f32,
) -> usize {
    let marginal = mt_mean_field_marginal(g, mt_id, keys, max_iter, tol, damping);
    let count = marginal.len();
    for (nid, sigma) in marginal {
        set_node_float_attr(g, nid, keys.state_attr, sigma);
    }
    count
}
