//! Modality-independent future-manifold projection.
//!
//! A caller supplies a graph-resident predicted continuation and the current
//! episode supplies the observed/allowed continuation.  This module owns the
//! temporal coverage, shape residual, retention, escape, and fail-closed
//! accounting.  It deliberately knows nothing about motors, speech, bodies,
//! or words.
//!
//! Graph contract (all fields are additive attributes; callers may use any
//! node type):
//!
//! * `source.future_manifold_values` — list of time slices, each a numeric
//!   list.  Optional `future_manifold_times` supplies integer times.
//! * `episode.future_manifold_target` — observed/desired slices.  It may be a
//!   prefix of the source trajectory; only its covered horizon is audited.
//! * `episode.future_manifold_bounds` — non-negative per-cell tolerance,
//!   matching the observed prefix.  Missing bounds are unsupported rather
//!   than guessed.
//! * `source.future_manifold_widths` — optional additional predictive width,
//!   same shape; this is the source's own tube, not a host-side margin.
//! * `policy.future_manifold_projection_budget` — maximum audited slices.
//! * `policy.future_manifold_physical_horizon` — optional required final time.
//!
//! The result is evidence only.  `resolved` means the requested projection
//! was completely audited (or an escape was located); it never commits a
//! caller's semantic object.

use crate::graph::{NodeID, TypedGraph};
use crate::sym::{Interner, Sym};
use crate::value::Value;

fn attr<'a>(
    graph: &'a TypedGraph,
    interner: &Interner,
    node: NodeID,
    key: &str,
) -> Option<&'a Value> {
    let sym = interner.lookup(key)?;
    if !graph.has_node(node) {
        return None;
    }
    graph.node(node).attrs.get(&sym)
}

fn number(value: &Value) -> Option<f64> {
    match value {
        Value::Int(v) => Some(*v as f64),
        Value::Float(v) if v.is_finite() => Some(*v),
        Value::Bool(v) => Some(if *v { 1.0 } else { 0.0 }),
        Value::Rational(n, d) if *d != 0 => Some(*n as f64 / *d as f64),
        _ => None,
    }
}

fn sequence(value: &Value) -> Option<Vec<&Value>> {
    match value {
        Value::List(values) | Value::Tuple(values) => Some(values.iter().collect()),
        _ => None,
    }
}

fn matrix(
    graph: &TypedGraph,
    interner: &Interner,
    node: NodeID,
    key: &str,
) -> Option<Vec<Vec<f64>>> {
    let rows = sequence(attr(graph, interner, node, key)?)?;
    let mut out = Vec::with_capacity(rows.len());
    for row in rows {
        let cells = sequence(row)?;
        let mut parsed = Vec::with_capacity(cells.len());
        for cell in cells {
            parsed.push(number(cell)?);
        }
        out.push(parsed);
    }
    Some(out)
}

fn scalar(graph: &TypedGraph, interner: &Interner, node: NodeID, key: &str) -> Option<f64> {
    number(attr(graph, interner, node, key)?)
}

fn flat_shape(m: &[Vec<f64>]) -> Option<(usize, usize)> {
    let width = m.first()?.len();
    if width == 0 || m.iter().any(|row| row.len() != width) {
        return None;
    }
    Some((m.len(), width))
}

fn width(m: &[Vec<f64>]) -> Option<usize> {
    flat_shape(m).map(|(_, width)| width)
}

fn all_finite(m: &[Vec<f64>]) -> bool {
    m.iter().flatten().all(|v| v.is_finite())
}

fn time_coordinates(
    graph: &TypedGraph,
    interner: &Interner,
    node: NodeID,
    rows: usize,
) -> Option<Vec<usize>> {
    let values = match attr(graph, interner, node, "future_manifold_times") {
        Some(value) => sequence(value)?,
        None => return Some((1..=rows).collect()),
    };
    if values.len() != rows {
        return None;
    }
    let mut times = Vec::with_capacity(rows);
    for value in values {
        let time = number(value)?;
        if !time.is_finite() || time < 1.0 || time.fract() != 0.0 {
            return None;
        }
        times.push(time as usize);
    }
    if times.first().copied() != Some(1)
        || times.windows(2).any(|window| window[1] != window[0] + 1)
    {
        return None;
    }
    Some(times)
}

/// Return a graph-native future-manifold field when the generic contract is
/// present.  `None` means the caller should use its legacy/domain adapter.
pub fn projection_field(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
    policy: NodeID,
    source: NodeID,
    addition: Option<NodeID>,
    field: Sym,
) -> Option<Value> {
    let candidate = addition.unwrap_or(source);
    let predicted = matrix(graph, interner, candidate, "future_manifold_values")?;
    let target = matrix(graph, interner, episode, "future_manifold_target")?;
    let bounds = matrix(graph, interner, episode, "future_manifold_bounds")?;
    let widths = matrix(graph, interner, candidate, "future_manifold_widths")
        .unwrap_or_else(|| vec![vec![0.0; predicted.first().map_or(0, Vec::len)]; predicted.len()]);
    let times = time_coordinates(graph, interner, candidate, predicted.len())?;

    let name = interner.resolve(field);
    let budget_raw =
        scalar(graph, interner, policy, "future_manifold_projection_budget").unwrap_or(0.0);
    let budget = budget_raw.round() as usize;
    let physical_raw =
        scalar(graph, interner, policy, "future_manifold_physical_horizon").unwrap_or(0.0);
    let requested_horizon = if physical_raw > 0.0 {
        physical_raw.round() as usize
    } else {
        times.last().copied().unwrap_or(0)
    };
    let physical_horizon_supported = physical_raw <= 0.0
        || (physical_raw.is_finite() && physical_raw.fract() == 0.0 && physical_raw >= 1.0);

    let mut support = budget >= 1
        && budget_raw.is_finite()
        && (budget as f64 - budget_raw).abs() < f64::EPSILON
        && physical_horizon_supported
        && requested_horizon >= 1
        && target.len() >= requested_horizon
        && times.last().copied().unwrap_or(0) >= requested_horizon
        && bounds.len() >= requested_horizon
        && widths.len() >= requested_horizon
        && flat_shape(&predicted).is_some()
        && flat_shape(&target).is_some()
        && flat_shape(&bounds).is_some()
        && flat_shape(&widths).is_some()
        && width(&predicted) == width(&target)
        && width(&predicted) == width(&bounds)
        && width(&predicted) == width(&widths)
        && all_finite(&predicted)
        && all_finite(&target)
        && all_finite(&bounds)
        && all_finite(&widths)
        && bounds.iter().flatten().all(|v| *v >= 0.0)
        && widths.iter().flatten().all(|v| *v >= 0.0);

    let mut loss = 0.0;
    let mut information_loss = 0.0;
    let mut retained_width = 0.0;
    let mut earliest_decisive_tick = 0.0;
    let mut audited = 0usize;
    let mut retained_by_dim: Vec<bool> = Vec::new();

    if support {
        let dims = predicted[0].len();
        retained_by_dim = vec![true; dims];
        let audit_horizon = requested_horizon.min(budget);
        for (t, time) in times.iter().enumerate().take(audit_horizon) {
            audited += 1;
            for d in 0..dims {
                let residual = (predicted[t][d] - target[t][d]).abs();
                let allowed = bounds[t][d] + widths[t][d];
                if residual > allowed {
                    retained_by_dim[d] = false;
                    loss += 1.0;
                    information_loss += 1.0;
                    if earliest_decisive_tick == 0.0 {
                        earliest_decisive_tick = *time as f64;
                    }
                }
            }
        }
        retained_width = retained_by_dim.iter().filter(|v| **v).count() as f64;
        if audited < requested_horizon {
            support = false;
        }
    }

    let resolved = if !support {
        false
    } else if loss > 0.0 {
        true
    } else {
        audited >= requested_horizon
    };
    let termination_code = if !support {
        4.0
    } else if loss > 0.0 {
        1.0
    } else {
        6.0
    };
    let horizon = audited as f64;
    let budget = budget as f64;
    let anchor_count = audited as f64;
    let field_name = name;
    let value = match field_name {
        "support" => support as i32 as f64,
        "resolved" => resolved as i32 as f64,
        "termination_code" => termination_code,
        "horizon" => horizon,
        "budget" => budget,
        "loss" => loss,
        "information_loss" => information_loss,
        "retained_width" => {
            if support {
                retained_width
            } else {
                0.0
            }
        }
        "anchor_count" => anchor_count,
        "refinement_count" => 0.0,
        "certified_interval_count" => {
            if support && loss == 0.0 {
                audited as f64
            } else {
                0.0
            }
        }
        "ambiguous_interval_count" => {
            if support {
                0.0
            } else {
                1.0
            }
        }
        "max_enclosure_width" => widths.iter().flatten().copied().fold(0.0, f64::max),
        "max_shape_order" => 0.0,
        "earliest_decisive_tick" => earliest_decisive_tick,
        key if key.starts_with("retained_") => {
            let idx = key[9..].parse::<usize>().ok();
            idx.and_then(|i| retained_by_dim.get(i).copied())
                .map(|v| if v { 1.0 } else { 0.0 })
                .unwrap_or(0.0)
        }
        _ => 0.0,
    };
    Some(Value::Float(value))
}

/// One candidate's audited deformation, as a member of a reachable set.
///
/// This is deliberately a RECORD, not a score. `μ` — the measure over a
/// reachable deformation set — is grounding-open in the theory, and picking
/// one here would install a scalar where a represented structure belongs.
#[derive(Debug, Clone, PartialEq)]
pub struct DeformationRecord {
    /// The candidate node whose projected continuation was audited.
    pub candidate: NodeID,
    /// Whether the audit was supported at all (fail-closed if not).
    pub support: bool,
    /// Whether the requested projection was completely audited.
    pub resolved: bool,
    /// Cells that left the episode's allowed tube.
    pub loss: f64,
    /// Cells whose retention could not be established.
    pub information_loss: f64,
    /// Dimensions still inside tolerance at the audited horizon.
    pub retained_width: f64,
    /// Earliest tick at which the outcome was decided, when one exists.
    pub earliest_decisive_tick: f64,
}

/// The reachable deformation SET over a supplied candidate family.
///
/// # What this is, and what it is not
///
/// The theory defines narrativium as `N(𝒳,T) = μ_𝒳(ℛ^T(𝒳))` — a measure over
/// the set of consequential deformation reachable from here. This function
/// builds `ℛ`, and only `ℛ`. It does not apply `μ`, does not sum, does not
/// average, and does not return a scalar: those are the grounding's business,
/// and the theory is explicit that `μ` is left open.
///
/// # This is the ADMISSIBLE bound, not selectable reachability
///
/// The theory distinguishes sharply between what is admissible and what is
/// actually *selectable*: "an always-admissible but never-selected candidate
/// contributes no realised reachability." Selecting requires the feasible-set
/// machinery — a joint feasible family over subsets, a represented valuation,
/// and a set-tie rule — none of which exists in this substrate today (see
/// `docs/research/theory_convergence/GRAPHIC_EQUALISATION_V22_SUBSTRATE_GAP.md`).
///
/// So what this returns is an UPPER BOUND on the reachable set. A later rung
/// that builds selection must narrow it; a caller that treats this as
/// selectable reachability is overstating its own capability. That distinction
/// is the reason this returns records rather than a number — a scalar here
/// would silently launder the bound into a measurement.
///
/// # Composition
///
/// The two primitives this joins have different input shapes, which is why
/// they were never joined: `Substrate::admissible_moves` enumerates
/// *type-level* moves with Γ weights, while the projection audit needs a
/// candidate that already carries a projected continuation. Bridging them
/// requires a per-move projector, which is domain grounding rather than
/// substrate. This function therefore takes candidates that already carry
/// their continuation, and leaves Γ-filtering to the caller that knows how
/// its moves become trajectories.
///
/// Takes `&mut Interner` because it interns its own field names: a caller
/// working on a fresh graph will not have interned `"support"` and friends,
/// and a `lookup`-only version silently reports every field as zero — i.e.
/// reports a supported audit as unsupported, with no error.
pub fn reachable_deformation_set(
    graph: &TypedGraph,
    interner: &mut Interner,
    episode: NodeID,
    policy: NodeID,
    candidates: &[NodeID],
) -> Vec<DeformationRecord> {
    let (support, resolved, loss, info, width, decisive) = (
        interner.intern("support"),
        interner.intern("resolved"),
        interner.intern("loss"),
        interner.intern("information_loss"),
        interner.intern("retained_width"),
        interner.intern("earliest_decisive_tick"),
    );
    let interner = &*interner;
    let read = |cand: NodeID, field: Sym| -> f64 {
        projection_field(graph, interner, episode, policy, cand, None, field)
            .and_then(|v| match v {
                Value::Float(x) => Some(x),
                Value::Int(i) => Some(i as f64),
                _ => None,
            })
            .unwrap_or(0.0)
    };
    candidates
        .iter()
        .map(|&candidate| DeformationRecord {
            candidate,
            support: read(candidate, support) != 0.0,
            resolved: read(candidate, resolved) != 0.0,
            loss: read(candidate, loss),
            information_loss: read(candidate, info),
            retained_width: read(candidate, width),
            earliest_decisive_tick: read(candidate, decisive),
        })
        .collect()
}

#[cfg(test)]
mod reachable_set_tests {
    use super::*;
    use rustc_hash::FxHashMap;

    /// Build an episode with a flat target tube and two candidates: one whose
    /// projected continuation stays inside tolerance, one that leaves it.
    fn bench() -> (TypedGraph, Interner, NodeID, NodeID, NodeID, NodeID) {
        let mut g = TypedGraph::new();
        let mut i = Interner::new();
        let ty = i.intern("N");
        let vals = i.intern("future_manifold_values");
        let tgt = i.intern("future_manifold_target");
        let bnd = i.intern("future_manifold_bounds");
        let budget = i.intern("future_manifold_projection_budget");
        let horizon = i.intern("future_manifold_physical_horizon");

        let slice = |xs: &[f64]| {
            let sv: smallvec::SmallVec<[Value; 4]> =
                xs.iter().map(|x| Value::Float(*x)).collect();
            Value::Tuple(std::sync::Arc::new(sv))
        };
        let traj = |rows: &[&[f64]]| {
            let sv: smallvec::SmallVec<[Value; 4]> =
                rows.iter().map(|r| slice(r)).collect();
            Value::Tuple(std::sync::Arc::new(sv))
        };

        let episode = g.insert_node(ty, FxHashMap::default());
        g.set_node_attr(episode, tgt, traj(&[&[0.0], &[0.0], &[0.0]]));
        g.set_node_attr(episode, bnd, traj(&[&[1.0], &[1.0], &[1.0]]));

        let policy = g.insert_node(ty, FxHashMap::default());
        g.set_node_attr(policy, budget, Value::Float(8.0));
        g.set_node_attr(policy, horizon, Value::Float(3.0));

        // Inside tolerance at every tick.
        let held = g.insert_node(ty, FxHashMap::default());
        g.set_node_attr(held, vals, traj(&[&[0.0], &[0.2], &[0.1]]));
        // Leaves the tube at the last tick.
        let escaping = g.insert_node(ty, FxHashMap::default());
        g.set_node_attr(escaping, vals, traj(&[&[0.0], &[0.2], &[9.0]]));

        (g, i, episode, policy, held, escaping)
    }

    /// The set is per-candidate and DISCRIMINATES: a candidate that leaves the
    /// tube must not report the same deformation as one that stays in it.
    /// Without this the "set" would be a list of identical rows and the
    /// composition would be decorative.
    #[test]
    fn set_discriminates_retained_from_escaping() {
        let (g, mut i, episode, policy, held, escaping) = bench();
        let set = reachable_deformation_set(&g, &mut i, episode, policy, &[held, escaping]);
        assert_eq!(set.len(), 2, "one record per candidate");
        assert_eq!(set[0].candidate, held);
        assert_eq!(set[1].candidate, escaping);
        assert!(set[0].support && set[1].support, "both audits supported");
        assert_eq!(set[0].loss, 0.0, "the held candidate stays inside tolerance");
        assert!(
            set[1].loss > 0.0,
            "the escaping candidate must register loss; got {:?}",
            set[1]
        );
    }

    /// An empty candidate family yields an empty set, not a zero measurement.
    /// This is the distinction the record type exists to preserve: nothing
    /// reachable is not the same fact as reachable-but-measured-zero.
    #[test]
    fn empty_candidate_family_yields_an_empty_set() {
        let (g, mut i, episode, policy, _held, _escaping) = bench();
        let set = reachable_deformation_set(&g, &mut i, episode, policy, &[]);
        assert!(set.is_empty(), "no candidates means no set members");
    }

    /// Fail-closed: a candidate carrying no projected continuation is reported
    /// as unsupported rather than silently contributing a zero-loss row.
    #[test]
    fn candidate_without_a_continuation_is_unsupported() {
        let (mut g, mut i, episode, policy, held, _escaping) = bench();
        let ty = g.node(held).type_;
        let bare = g.insert_node(ty, FxHashMap::default());
        let set = reachable_deformation_set(&g, &mut i, episode, policy, &[bare]);
        assert_eq!(set.len(), 1);
        assert!(
            !set[0].support,
            "a candidate with no trajectory must fail closed, got {:?}",
            set[0]
        );
    }
}
