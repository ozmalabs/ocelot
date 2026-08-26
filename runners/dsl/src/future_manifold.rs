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
//! * `episode.future_manifold_ideal_effort` and
//!   `source.future_manifold_effort` — optional dimensionless learned
//!   normal-case and projected effort ratios. Domain adapters obtain the ratio
//!   by dividing expenditure by a situated characteristic effort scale.
//!   Effort above the ideal is admissible only when
//!   the candidate compresses represented time, width, or information loss.
//!   The corresponding ideal/projected time and ideal width/information
//!   fields are optional; absent effort evidence leaves this gate unsupported
//!   rather than treating zero action as ideal.
//! * `policy.future_manifold_projection_budget` — maximum audited slices.
//! * `policy.future_manifold_physical_horizon` — optional required final time.
//! * `residual_N` reports signed excess in dimension N at the earliest
//!   decisive tick; `shape_residual_T_N` addresses the signed excess at the
//!   actual one-based projected time T. Positive means prediction above the
//!   allowed tube, negative below it, and zero remains inside the tube.
//! * `narrativium_reachable_N` and `narrativium_retained_N` expose the
//!   discrete counting measure for this candidate in dimension N.  A single
//!   supported trace contributes one reachable deformation; it contributes
//!   one retained deformation only when the whole audited trace stays within
//!   the manifold. Candidate-family callers use
//!   [`counting_narrativium_by_dimension`] to deduplicate and count the set.
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
    // Optional orientation of each manifold dimension.  Zero preserves the
    // original symmetric tube; +1 means that larger values preserve at least
    // as much future capacity, and -1 means that smaller values do.  This lets
    // a graph express a partial order (height/support versus load/time) without
    // inventing a scalar score or an arbitrary finite opposite bound.
    let directions = matrix(graph, interner, episode, "future_manifold_directions");
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

    // No longer `mut`: the only thing that used to reassign it was the budget
    // shortfall, which is now `resolved`'s business. Well-posedness is decided
    // once, from the shapes, and does not depend on how far the audit got.
    let support = budget >= 1
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
        && directions.as_ref().map_or(true, |values| {
            flat_shape(values) == flat_shape(&predicted)
                && all_finite(values)
                && values
                    .iter()
                    .flatten()
                    .all(|value| *value == -1.0 || *value == 0.0 || *value == 1.0)
        })
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
    let mut residual_shape: Vec<Vec<f64>> = Vec::new();

    if support {
        let dims = predicted[0].len();
        // APERTURE, at the manifold. `policy.future_manifold_resolved_dims` is a
        // per-dimension 0/1 mask of what this observer can actually resolve;
        // absent, or the wrong length, means all dimensions resolve and the
        // audit is byte-identical to before.
        //
        // An unresolved dimension is not one that fails — it is one that cannot
        // be ASSESSED, which is precisely `information_loss`'s question. So the
        // seed-level quotient (`observer_aperture`: unresolved slots collapse to
        // one constant) and the manifold-level audit are the same limitation
        // expressed at two grains, and a narrow observer is measurably STUPID
        // here rather than merely coarse somewhere else.
        let resolves = matrix(graph, interner, policy, "future_manifold_resolved_dims")
            .and_then(|m| m.into_iter().next())
            .filter(|row| row.len() == dims)
            .map(|row| row.iter().map(|v| *v != 0.0).collect::<Vec<bool>>())
            .unwrap_or_else(|| vec![true; dims]);
        let mut assessed_cells = 0usize;
        retained_by_dim = resolves.clone();
        residual_shape = vec![vec![0.0; dims]; predicted.len()];
        let audit_horizon = requested_horizon.min(budget);
        for (t, time) in times.iter().enumerate().take(audit_horizon) {
            audited += 1;
            for d in 0..dims {
                if !resolves[d] {
                    continue;
                }
                assessed_cells += 1;
                let delta = predicted[t][d] - target[t][d];
                let allowed = bounds[t][d] + widths[t][d];
                let direction = directions.as_ref().map_or(0.0, |values| values[t][d]);
                let excess = if direction > 0.0 {
                    -delta - allowed
                } else if direction < 0.0 {
                    delta - allowed
                } else {
                    delta.abs() - allowed
                };
                if excess > 0.0 {
                    residual_shape[t][d] = delta.signum() * excess;
                    retained_by_dim[d] = false;
                    loss += 1.0;
                    if earliest_decisive_tick == 0.0 {
                        earliest_decisive_tick = *time as f64;
                    }
                }
            }
        }
        // `information_loss` now asks its OWN question. Not "what left the tube"
        // — that is `loss`, and such a cell WAS assessed, so its retention is
        // established, as false — but "what could not be assessed at all".
        //
        // Cells inside the requested horizon that the budget never reached are
        // exactly that. Previously both counters were incremented on this same
        // line and were numerically identical, so an agent that could not tell
        // was indistinguishable from one that told correctly and got bad news.
        // Counted as cells rather than ticks, because there are now two ways for
        // a cell to go unassessed and they compose: the budget never reached its
        // TICK, or the aperture never resolved its DIMENSION.
        information_loss += (requested_horizon * dims).saturating_sub(assessed_cells) as f64;
        let unassessed_ticks = requested_horizon.saturating_sub(audited);
        if unassessed_ticks > 0 {
            // Retention over the REQUESTED horizon is unestablished for every
            // dimension once any tick in it went unaudited. Leaving these `true`
            // claimed retention for ticks nobody looked at — latent until now
            // only because a short audit used to falsify `support` outright.
            for retained in retained_by_dim.iter_mut() {
                *retained = false;
            }
        }
        retained_width = retained_by_dim.iter().filter(|v| **v).count() as f64;
    }

    // A budget shortfall no longer falsifies `support`. `support` asks whether
    // the audit is WELL-POSED (shapes, finiteness, geometry); `resolved` asks
    // whether it COMPLETED. Collapsing them made an under-resourced projection
    // report "could not run" when it had run and could not finish — and left
    // `resolved` derivable from `support`, carrying no information of its own.
    let resolved = if !support {
        false
    } else if loss > 0.0 {
        // Decided early: an escape was located, so the remaining cells cannot
        // change the verdict.
        true
    } else {
        // Everything in the requested horizon was actually ASSESSED. Counting
        // audited TICKS here instead was a real bug found by the aperture tests:
        // a fully-blind observer walks every tick, assesses no cell in any of
        // them, and used to report the projection resolved. `information_loss`
        // is the right quantity because it already counts both ways a cell goes
        // unassessed — a tick the budget never reached, and a dimension the
        // aperture never resolved.
        information_loss == 0.0
    };
    let termination_code = if !support {
        4.0
    } else if !resolved {
        // Supported, undecided. The same code the sibling implementation already
        // uses for this state (`motor_compose.rs`: `if support { 3.0 } else
        // { 4.0 }`), so the two agree rather than inventing a second vocabulary.
        3.0
    } else if loss > 0.0 {
        1.0
    } else {
        6.0
    };
    let horizon = audited as f64;
    let budget = budget as f64;
    let anchor_count = audited as f64;
    let maximum_enclosure_width = widths.iter().flatten().copied().fold(0.0, f64::max);
    let projected_effort = scalar(graph, interner, candidate, "future_manifold_effort");
    let ideal_effort = scalar(graph, interner, episode, "future_manifold_ideal_effort")
        .filter(|ideal| ideal.is_finite() && *ideal > 0.0)
        .or_else(|| {
            scalar(
                graph,
                interner,
                policy,
                "future_manifold_ideal_effort_prior",
            )
            .filter(|ideal| ideal.is_finite() && *ideal > 0.0)
        });
    let effort_supported = matches!(
        (projected_effort, ideal_effort),
        (Some(projected), Some(ideal))
            if projected.is_finite() && ideal.is_finite()
                && projected >= 0.0 && ideal > 0.0
    );
    let effort_residual = if effort_supported {
        (projected_effort.unwrap_or(0.0) - ideal_effort.unwrap_or(0.0)).max(0.0)
    } else {
        0.0
    };
    let time_compression = match (
        scalar(
            graph,
            interner,
            episode,
            "future_manifold_ideal_completion_time",
        ),
        scalar(
            graph,
            interner,
            candidate,
            "future_manifold_completion_time",
        ),
    ) {
        (Some(ideal), Some(projected))
            if ideal.is_finite() && projected.is_finite() && ideal >= 0.0 && projected >= 0.0 =>
        {
            (ideal - projected).max(0.0)
        }
        _ => 0.0,
    };
    let width_compression = scalar(graph, interner, episode, "future_manifold_ideal_width")
        .filter(|ideal| ideal.is_finite() && *ideal >= 0.0)
        .map_or(0.0, |ideal| (ideal - maximum_enclosure_width).max(0.0));
    let inferred_information_compression = scalar(
        graph,
        interner,
        episode,
        "future_manifold_ideal_information_loss",
    )
    .filter(|ideal| ideal.is_finite() && *ideal >= 0.0)
    .map_or(0.0, |ideal| (ideal - information_loss).max(0.0));
    let explicit_information_compression = scalar(
        graph,
        interner,
        candidate,
        "future_manifold_information_compression",
    )
    .filter(|compression| compression.is_finite() && *compression >= 0.0)
    .unwrap_or(0.0);
    let information_compression =
        inferred_information_compression.max(explicit_information_compression);
    // These are unlike dimensions.  Preserve the triangle instead of
    // collapsing seconds, width units and information units into a score.
    let compression_dimension_count = [time_compression, width_compression, information_compression]
        .into_iter()
        .filter(|compression| *compression > 0.0)
        .count() as f64;
    let manifold_compression = compression_dimension_count > 0.0;
    let effort_authorized = !effort_supported || effort_residual <= 0.0 || manifold_compression;
    let field_name = name;
    if field_name == "shape_snapshot" {
        let decisive_row = times
            .iter()
            .position(|time| *time as f64 == earliest_decisive_tick)
            .or_else(|| audited.checked_sub(1));
        let mut fields = Vec::with_capacity(21);
        fields.extend([
            support as i32 as f64,
            resolved as i32 as f64,
            loss,
            information_loss,
            horizon,
            earliest_decisive_tick,
            0.0, // Generic matrix projections have no exafferent addition.
        ]);
        for dimension in 0..7 {
            fields.push(
                decisive_row
                    .and_then(|row| residual_shape.get(row))
                    .and_then(|values| values.get(dimension))
                    .copied()
                    .unwrap_or(0.0),
            );
        }
        for dimension in 0..7 {
            fields.push(
                decisive_row
                    .and_then(|row| Some((bounds.get(row)?, widths.get(row)?)))
                    .and_then(|(bound_row, width_row)| {
                        Some(*bound_row.get(dimension)? + *width_row.get(dimension)?)
                    })
                    .unwrap_or(0.0),
            );
        }
        return Some(Value::Tuple(std::sync::Arc::new(
            fields
                .into_iter()
                .map(Value::Float)
                .collect::<Vec<_>>()
                .into(),
        )));
    }
    if field_name == "snapshot" {
        return Some(Value::Tuple(std::sync::Arc::new(
            vec![
                Value::Float(support as i32 as f64),
                Value::Float(resolved as i32 as f64),
                Value::Float(loss),
                Value::Float(information_loss),
                Value::Float(effort_supported as i32 as f64),
                Value::Float(effort_authorized as i32 as f64),
            ]
            .into(),
        )));
    }
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
        "max_enclosure_width" => maximum_enclosure_width,
        "effort_supported" => effort_supported as i32 as f64,
        "projected_effort" => projected_effort.unwrap_or(0.0),
        "ideal_effort" => ideal_effort.unwrap_or(0.0),
        "effort_residual" => effort_residual,
        "time_compression" => time_compression,
        "width_compression" => width_compression,
        "information_compression" => information_compression,
        "compression_dimension_count" => compression_dimension_count,
        "manifold_compression" => manifold_compression as i32 as f64,
        "effort_authorized" => effort_authorized as i32 as f64,
        "max_shape_order" => 0.0,
        "earliest_decisive_tick" => earliest_decisive_tick,
        key if key.starts_with("residual_") => {
            let idx = key[9..].parse::<usize>().ok();
            let row = times
                .iter()
                .position(|time| *time as f64 == earliest_decisive_tick);
            row.and_then(|t| idx.and_then(|d| residual_shape.get(t)?.get(d)))
                .copied()
                .unwrap_or(0.0)
        }
        key if key.starts_with("shape_residual_") => {
            let indices: Vec<usize> = key[15..]
                .split('_')
                .filter_map(|part| part.parse::<usize>().ok())
                .collect();
            if indices.len() != 2 {
                0.0
            } else {
                times
                    .iter()
                    .position(|time| *time == indices[0])
                    .and_then(|t| residual_shape.get(t)?.get(indices[1]))
                    .copied()
                    .unwrap_or(0.0)
            }
        }
        key if key.starts_with("retained_") => {
            let idx = key[9..].parse::<usize>().ok();
            idx.and_then(|i| retained_by_dim.get(i).copied())
                .map(|v| if v { 1.0 } else { 0.0 })
                .unwrap_or(0.0)
        }
        key if key.starts_with("narrativium_reachable_") => {
            let idx = key[22..].parse::<usize>().ok();
            idx.filter(|dimension| *dimension < retained_by_dim.len())
                .map(|_| if support { 1.0 } else { 0.0 })
                .unwrap_or(0.0)
        }
        key if key.starts_with("narrativium_retained_") => {
            let idx = key[21..].parse::<usize>().ok();
            idx.and_then(|dimension| retained_by_dim.get(dimension).copied())
                .map(|retained| if support && retained { 1.0 } else { 0.0 })
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
    /// Per-dimension retention.  This remains a vector because dimensions
    /// need not share a measure or even comparable units.
    pub retained_dimensions: Vec<bool>,
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
    let (support, resolved, loss, info, retained_width_field, decisive) = (
        interner.intern("support"),
        interner.intern("resolved"),
        interner.intern("loss"),
        interner.intern("information_loss"),
        interner.intern("retained_width"),
        interner.intern("earliest_decisive_tick"),
    );
    let maximum_dimensions = candidates
        .iter()
        .filter_map(|candidate| {
            matrix(graph, interner, *candidate, "future_manifold_values")
                .and_then(|values| width(&values))
        })
        .max()
        .unwrap_or(0);
    let retained_fields: Vec<Sym> = (0..maximum_dimensions)
        .map(|dimension| interner.intern(&format!("retained_{dimension}")))
        .collect();
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
            retained_width: read(candidate, retained_width_field),
            retained_dimensions: {
                let dimensions = matrix(graph, interner, candidate, "future_manifold_values")
                    .and_then(|values| width(&values))
                    .unwrap_or(0);
                (0..dimensions)
                    .map(|dimension| read(candidate, retained_fields[dimension]) != 0.0)
                    .collect()
            },
            earliest_decisive_tick: read(candidate, decisive),
        })
        .collect()
}

/// A deterministic counting grounding for Narrativium in one dimension.
///
/// `reachable_deformations` counts distinct, supported projected traces in
/// the admissible reachable-set upper bound. `retained_deformations` counts
/// the subset whose complete audited trace remains inside the represented
/// manifold.  Both are cardinalities, not magnitudes in the dimension's
/// units, and no value is combined across dimensions.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DimensionNarrativium {
    pub dimension: usize,
    pub reachable_deformations: usize,
    pub retained_deformations: usize,
}

/// Apply the discrete counting measure to an admissible candidate family.
///
/// This is one explicit grounding of the theory's open `mu`: two candidates
/// contribute once when their projected traces in a dimension are identical.
/// `None` means the requested Narrativium dimension is not established: an
/// empty family, malformed dimensionality, or any unsupported candidate fails
/// closed rather than being reported as zero capacity.
pub fn counting_narrativium_by_dimension(
    graph: &TypedGraph,
    interner: &mut Interner,
    episode: NodeID,
    policy: NodeID,
    candidates: &[NodeID],
) -> Option<Vec<DimensionNarrativium>> {
    if candidates.is_empty() {
        return None;
    }
    let records = reachable_deformation_set(graph, interner, episode, policy, candidates);
    // Requires RESOLVED, not merely supported. `support` no longer implies the
    // audit finished, and reporting an unfinished audit's retention as capacity
    // is exactly the "zero capacity versus not established" confusion this
    // function exists to refuse.
    if records.iter().any(|record| !record.support || !record.resolved) {
        return None;
    }
    let trajectories: Vec<Vec<Vec<f64>>> = candidates
        .iter()
        .map(|candidate| matrix(graph, interner, *candidate, "future_manifold_values"))
        .collect::<Option<_>>()?;
    let dimensions = trajectories.first().and_then(|values| width(values))?;
    let physical_horizon = scalar(graph, interner, policy, "future_manifold_physical_horizon");
    let measured_horizon = match physical_horizon {
        Some(horizon) if horizon.is_finite() && horizon >= 1.0 && horizon.fract() == 0.0 => {
            horizon as usize
        }
        Some(horizon) if horizon <= 0.0 => trajectories.first()?.len(),
        None => trajectories.first()?.len(),
        _ => return None,
    };
    if dimensions == 0
        || measured_horizon == 0
        || trajectories
            .iter()
            .any(|values| width(values) != Some(dimensions) || values.len() < measured_horizon)
    {
        return None;
    }

    Some(
        (0..dimensions)
            .map(|dimension| {
                let mut reachable: Vec<Vec<u64>> = Vec::new();
                let mut retained: Vec<Vec<u64>> = Vec::new();
                for (trajectory, record) in trajectories.iter().zip(&records) {
                    let trace: Vec<u64> = trajectory
                        .iter()
                        .take(measured_horizon)
                        .map(|row| {
                            let value = row[dimension];
                            if value == 0.0 {
                                0.0f64.to_bits()
                            } else {
                                value.to_bits()
                            }
                        })
                        .collect();
                    if !reachable.contains(&trace) {
                        reachable.push(trace.clone());
                    }
                    if record.retained_dimensions[dimension] && !retained.contains(&trace) {
                        retained.push(trace);
                    }
                }
                DimensionNarrativium {
                    dimension,
                    reachable_deformations: reachable.len(),
                    retained_deformations: retained.len(),
                }
            })
            .collect(),
    )
}


// ---------------------------------------------------------------------------
// Feasible-set selection — making "admissible but never selected" expressible.
// ---------------------------------------------------------------------------

/// One candidate's standing under the selection rule.
///
/// Like [`DeformationRecord`] this is a RECORD. Nothing here is summed into a
/// desirability score: the three questions the theory separates — *can I tell?*,
/// *would it hold?*, *was it taken?* — stay three fields, because collapsing them
/// is exactly what makes an ignorant, a stupid and a stubborn agent look alike.
#[derive(Debug, Clone, PartialEq)]
pub struct SelectionRecord {
    pub candidate: NodeID,
    /// The audit ran to completion, so feasibility is KNOWN — either way.
    /// False is the *stupid* signature: not "it would fail" but "I cannot say".
    pub established: bool,
    /// Established AND the projected tube stayed inside the allowed one.
    pub feasible: bool,
    /// The represented valuation. `None` means the caller never represented one;
    /// it is NOT zero cost, and a feasible candidate carrying `None` fails the
    /// whole selection closed rather than being silently treated as free.
    pub intervention: Option<f64>,
    /// Goal ordering, used only to break equal-intervention ties.
    pub goal_rank: Option<f64>,
    /// The policy declined this candidate for reasons outside the selection rule.
    pub withheld: bool,
}

/// The outcome of applying the selection rule to a reachable set.
///
/// # Why this is set-valued
///
/// `minimal` and `selected` are families, not winners. The premise of an
/// admissibility grammar is that a single fixpoint need not be chosen, and a
/// selector that returned one candidate would re-impose exactly the choice the
/// grammar exists to avoid. `tie_breadth` is published so a caller can see how
/// much freedom it actually had.
///
/// # What makes stubbornness visible
///
/// `withheld_minimal` is the set of candidates that were established, feasible,
/// minimal under the represented valuation, and best under goals — and were still
/// not taken. That is the theory's *"always-admissible but never-selected
/// candidate contributes no realised reachability"*, as a countable set rather
/// than a sentence. An agent with a large `withheld_minimal` is not ignorant (its
/// candidates exist), not stupid (their feasibility was established): it is
/// declining futures that would have worked and cost no more.
///
/// The substrate does not decide that this is a pathology. It makes the
/// difference between what would have worked and what was taken legible, and
/// leaves the reading to the caller.
#[derive(Debug, Clone, PartialEq)]
pub struct FeasibleSelection {
    pub records: Vec<SelectionRecord>,
    /// Candidates whose feasibility could not be established — the STUPID axis.
    pub unestablished: Vec<NodeID>,
    /// Established and would leave the tube. Correctly rejected, not a deficit.
    pub infeasible: Vec<NodeID>,
    pub feasible: Vec<NodeID>,
    /// Feasible, minimum-intervention, goal-best — before withholding.
    pub minimal: Vec<NodeID>,
    /// `minimal` less whatever the policy withheld.
    pub selected: Vec<NodeID>,
    /// Minimal-and-would-have-worked, yet not taken — the STUBBORN axis.
    pub withheld_minimal: Vec<NodeID>,
    /// `minimal.len()` — how set-valued the decision genuinely was.
    pub tie_breadth: usize,
}

/// Apply the substrate's own decision rule to a reachable deformation set.
///
/// The rule is not invented here; it is the engine-wide boundary stated in
/// `CLAUDE.md`: *"Execution chooses the minimum sufficient action/intervention
/// that keeps the projected tube inside it; goals break equal-intervention
/// ties."* Read literally, in that order:
///
/// 1. FEASIBLE — the projected tube stays inside the allowed tube (`loss == 0`),
///    that was actually established (`support && resolved`), and represented
///    above-normal effort is authorized by compression of the manifold;
/// 2. MINIMUM SUFFICIENT — least represented `intervention` among the feasible;
/// 3. GOALS BREAK TIES — among those, greatest `goal_rank`, and only among those.
///    Goals never override intervention; they order what intervention left equal.
///
/// Ties are kept, not broken arbitrarily. Intervention equality is EXACT on the
/// represented value: a tolerance would be a scalar knob standing in for a shape,
/// and a caller wanting one quantises its own valuation, where it has the units.
///
/// Fails closed (`None`) on an empty family, an unsupported candidate, or a
/// feasible candidate with no represented valuation — the last because "minimum
/// sufficient" over an unrepresented cost is not a smaller number, it is not a
/// question. This mirrors [`counting_narrativium_by_dimension`], which refuses to
/// report unestablished reachability as zero capacity.
pub fn feasible_selection(
    graph: &TypedGraph,
    interner: &mut Interner,
    episode: NodeID,
    policy: NodeID,
    candidates: &[NodeID],
) -> Option<FeasibleSelection> {
    let snapshot_field = interner.intern("snapshot");
    feasible_selection_with_snapshot(
        graph,
        interner,
        episode,
        policy,
        candidates,
        snapshot_field,
    )
}

/// Read-only selection entry used by graph Term evaluation.  Its parser owns
/// interning the snapshot field; evaluation itself must not mutate the symbol
/// table hidden behind an immutable graph context.
pub(crate) fn feasible_selection_with_snapshot(
    graph: &TypedGraph,
    interner: &Interner,
    episode: NodeID,
    policy: NodeID,
    candidates: &[NodeID],
    snapshot_field: Sym,
) -> Option<FeasibleSelection> {
    feasible_selection_with_projector(graph, interner, candidates, |candidate| {
        projection_field(
            graph,
            interner,
            episode,
            policy,
            candidate,
            None,
            snapshot_field,
        )
    })
}

/// Apply feasible-set selection to snapshots supplied by the active synthesis
/// adapter.  The generic matrix contract and domain analysis-by-synthesis
/// adapters therefore share one selection law; only their projection source
/// differs.
pub(crate) fn feasible_selection_with_projector<F>(
    graph: &TypedGraph,
    interner: &Interner,
    candidates: &[NodeID],
    mut snapshot: F,
) -> Option<FeasibleSelection>
where
    F: FnMut(NodeID) -> Option<Value>,
{
    if candidates.is_empty() {
        return None;
    }
    // Selection needs only support, resolution and loss.  Asking
    // `reachable_deformation_set` for them used to recompute the same shape for
    // every published field and retained dimension.  The native snapshot is
    // deliberately a single audit, so candidate-family arbitration remains
    // O(candidates * shape) rather than O(candidates * shape * dimensions).
    let records: Vec<SelectionRecord> = candidates
        .iter()
        .map(|candidate| {
            let snapshot = snapshot(*candidate)?;
            let fields = sequence(&snapshot)?;
            let support = number(fields.first()?)? != 0.0;
            let resolved = number(fields.get(1)?)? != 0.0;
            let loss = number(fields.get(2)?)?;
            let effort_supported = fields
                .get(4)
                .and_then(|value| number(value))
                .is_some_and(|value| value != 0.0);
            let effort_authorized = fields
                .get(5)
                .and_then(|value| number(value))
                .is_some_and(|value| value != 0.0);
            if !support {
                return None;
            }
            let established = resolved;
            Some(SelectionRecord {
                candidate: *candidate,
                established,
                feasible: established
                    && loss == 0.0
                    && (!effort_supported || effort_authorized),
                intervention: scalar(graph, interner, *candidate, "intervention"),
                goal_rank: scalar(graph, interner, *candidate, "goal_rank"),
                withheld: scalar(graph, interner, *candidate, "withheld")
                    .map(|v| v != 0.0)
                    .unwrap_or(false),
            })
        })
        .collect::<Option<Vec<_>>>()?;

    let pick = |f: &dyn Fn(&SelectionRecord) -> bool| -> Vec<NodeID> {
        records.iter().filter(|r| f(r)).map(|r| r.candidate).collect()
    };
    let unestablished = pick(&|r| !r.established);
    let infeasible = pick(&|r| r.established && !r.feasible);
    let feasible = pick(&|r| r.feasible);

    // A feasible candidate with no represented valuation makes "minimum
    // sufficient" unanswerable. Refuse rather than rank it as free.
    if records.iter().any(|r| r.feasible && r.intervention.is_none()) {
        return None;
    }

    let minimum = records
        .iter()
        .filter(|r| r.feasible)
        .filter_map(|r| r.intervention)
        .fold(None::<f64>, |acc, v| Some(match acc {
            Some(best) if best <= v => best,
            _ => v,
        }));

    let minimal: Vec<NodeID> = match minimum {
        None => Vec::new(),                     // nothing feasible: honest, not a failure
        Some(min) => {
            let at_min: Vec<&SelectionRecord> = records
                .iter()
                .filter(|r| r.feasible && r.intervention == Some(min))
                .collect();
            // Goals order only what intervention left equal.
            let best_goal = at_min.iter().filter_map(|r| r.goal_rank).fold(
                None::<f64>,
                |acc, v| Some(match acc {
                    Some(best) if best >= v => best,
                    _ => v,
                }),
            );
            match best_goal {
                None => at_min.iter().map(|r| r.candidate).collect(),
                Some(best) => at_min
                    .iter()
                    .filter(|r| r.goal_rank == Some(best))
                    .map(|r| r.candidate)
                    .collect(),
            }
        }
    };

    let withheld_of = |id: NodeID| {
        records.iter().any(|r| r.candidate == id && r.withheld)
    };
    let selected: Vec<NodeID> = minimal.iter().copied().filter(|id| !withheld_of(*id)).collect();
    let withheld_minimal: Vec<NodeID> =
        minimal.iter().copied().filter(|id| withheld_of(*id)).collect();

    Some(FeasibleSelection {
        tie_breadth: minimal.len(),
        records,
        unestablished,
        infeasible,
        feasible,
        minimal,
        selected,
        withheld_minimal,
    })
}

#[cfg(test)]
pub(crate) mod reachable_set_tests {
    use super::*;
    use rustc_hash::FxHashMap;

    /// Build an episode with a flat target tube and two candidates: one whose
    /// projected continuation stays inside tolerance, one that leaves it.
    pub(crate) fn bench() -> (TypedGraph, Interner, NodeID, NodeID, NodeID, NodeID) {
        let mut g = TypedGraph::new();
        let mut i = Interner::new();
        let ty = i.intern("N");
        let vals = i.intern("future_manifold_values");
        let tgt = i.intern("future_manifold_target");
        let bnd = i.intern("future_manifold_bounds");
        let budget = i.intern("future_manifold_projection_budget");
        let horizon = i.intern("future_manifold_physical_horizon");

        let slice = |xs: &[f64]| {
            let sv: smallvec::SmallVec<[Value; 4]> = xs.iter().map(|x| Value::Float(*x)).collect();
            Value::Tuple(std::sync::Arc::new(sv))
        };
        let traj = |rows: &[&[f64]]| {
            let sv: smallvec::SmallVec<[Value; 4]> = rows.iter().map(|r| slice(r)).collect();
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
        assert_eq!(
            set[0].loss, 0.0,
            "the held candidate stays inside tolerance"
        );
        assert!(
            set[1].loss > 0.0,
            "the escaping candidate must register loss; got {:?}",
            set[1]
        );

        let residual = i.intern("residual_0");
        let temporal = i.intern("shape_residual_3_0");
        assert_eq!(
            projection_field(&g, &i, episode, policy, escaping, None, residual),
            Some(Value::Float(8.0)),
            "earliest decisive residual preserves sign and excess magnitude",
        );
        assert_eq!(
            projection_field(&g, &i, episode, policy, escaping, None, temporal),
            Some(Value::Float(8.0)),
            "time-addressed residual preserves the projected shape",
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

    #[test]
    fn directed_dimensions_express_future_capacity_partial_orders() {
        let (mut g, mut i, episode, policy, held, escaping) = bench();
        let tuple = |values: &[f64]| {
            Value::Tuple(std::sync::Arc::new(
                values
                    .iter()
                    .map(|value| Value::Float(*value))
                    .collect::<smallvec::SmallVec<[Value; 4]>>(),
            ))
        };
        let matrix = |rows: &[&[f64]]| {
            Value::Tuple(std::sync::Arc::new(
                rows.iter()
                    .map(|row| tuple(row))
                    .collect::<smallvec::SmallVec<[Value; 4]>>(),
            ))
        };
        let target = i.intern("future_manifold_target");
        let bounds = i.intern("future_manifold_bounds");
        let directions = i.intern("future_manifold_directions");
        let values = i.intern("future_manifold_values");
        let horizon = i.intern("future_manifold_physical_horizon");
        let loss = i.intern("loss");
        g.set_node_attr(episode, target, matrix(&[&[0.5, 0.5]]));
        g.set_node_attr(episode, bounds, matrix(&[&[0.0, 0.0]]));
        g.set_node_attr(episode, directions, matrix(&[&[1.0, -1.0]]));
        g.set_node_attr(policy, horizon, Value::Float(1.0));

        // More retained height and less load are both inside the directed
        // tube, even though neither is equal to the receipt-backed target.
        g.set_node_attr(held, values, matrix(&[&[0.8, 0.2]]));
        assert_eq!(
            projection_field(&g, &i, episode, policy, held, None, loss),
            Some(Value::Float(0.0)),
        );

        // Less height and more load each remove a future, so both dimensions
        // are reported rather than collapsed into a compensating score.
        g.set_node_attr(escaping, values, matrix(&[&[0.4, 0.6]]));
        assert_eq!(
            projection_field(&g, &i, episode, policy, escaping, None, loss),
            Some(Value::Float(2.0)),
        );
    }

    #[test]
    fn narrativium_counts_distinct_reachable_traces_per_dimension() {
        let (mut g, mut i, episode, policy, held, escaping) = bench();
        let ty = g.node(held).type_;
        let duplicate = g.insert_node(ty, FxHashMap::default());
        let vals = i.intern("future_manifold_values");
        let slice = |xs: &[f64]| {
            let values: smallvec::SmallVec<[Value; 4]> =
                xs.iter().map(|value| Value::Float(*value)).collect();
            Value::Tuple(std::sync::Arc::new(values))
        };
        let rows: smallvec::SmallVec<[Value; 4]> = [&[0.0][..], &[0.2][..], &[0.1][..]]
            .iter()
            .map(|row| slice(row))
            .collect();
        g.set_node_attr(duplicate, vals, Value::Tuple(std::sync::Arc::new(rows)));

        let measure = counting_narrativium_by_dimension(
            &g,
            &mut i,
            episode,
            policy,
            &[held, duplicate, escaping],
        )
        .expect("the dimension is represented and every candidate is auditable");
        assert_eq!(
            measure,
            vec![DimensionNarrativium {
                dimension: 0,
                reachable_deformations: 2,
                retained_deformations: 1,
            }],
            "duplicate programs do not fabricate capacity, while an escaping trace remains reachable but not retained",
        );
    }

    #[test]
    fn narrativium_is_undefined_without_supported_reachability() {
        let (mut g, mut i, episode, policy, held, _escaping) = bench();
        let bare = g.insert_node(g.node(held).type_, FxHashMap::default());
        assert_eq!(
            counting_narrativium_by_dimension(&g, &mut i, episode, policy, &[held, bare],),
            None,
            "unsupported reachability is not zero Narrativium",
        );
        assert_eq!(
            counting_narrativium_by_dimension(&g, &mut i, episode, policy, &[]),
            None,
            "an absent dimension is not a measured zero",
        );
    }
}

#[cfg(test)]
mod feasible_selection_tests {
    use super::*;
    use rustc_hash::FxHashMap;

    /// The reachable-set bench, plus the two represented quantities selection
    /// needs: a valuation, and whatever the policy chose to withhold.
    fn bench() -> (TypedGraph, Interner, NodeID, NodeID, NodeID, NodeID) {
        super::reachable_set_tests::bench()
    }

    fn set(g: &mut TypedGraph, i: &mut Interner, n: NodeID, k: &str, v: f64) {
        let sym = i.intern(k);
        g.set_node_attr(n, sym, Value::Float(v));
    }

    fn ids(v: &[NodeID]) -> Vec<NodeID> {
        let mut out = v.to_vec();
        out.sort();
        out
    }

    #[test]
    fn an_escaping_candidate_is_infeasible_not_unestablished() {
        // The distinction the whole audit turns on: correctly foreseeing that
        // something leaves the tube is not a deficit, and must not read as one.
        let (mut g, mut i, ep, pol, held, esc) = bench();
        set(&mut g, &mut i, held, "intervention", 1.0);
        set(&mut g, &mut i, esc, "intervention", 1.0);
        let sel = feasible_selection(&g, &mut i, ep, pol, &[held, esc]).expect("supported");
        assert_eq!(sel.feasible, vec![held]);
        assert_eq!(sel.infeasible, vec![esc]);
        assert!(sel.unestablished.is_empty(), "nothing was left undecided here");
    }

    #[test]
    fn graph_term_selects_the_set_without_host_arbitration() {
        use crate::jsonio::{term_from_json, term_to_json};
        use crate::term::{evaluate, Env, EvalCtx, TermArena, TermNode};

        let (mut g, mut i, ep, pol, held, esc) = bench();
        set(&mut g, &mut i, held, "intervention", 1.0);
        set(&mut g, &mut i, esc, "intervention", 0.0);
        let selected = i.intern("selected");
        let snapshot = i.intern("snapshot");

        let mut arena = TermArena::new();
        let episode = arena.add(TermNode::Lit {
            value: Value::Node(ep),
        });
        let policy = arena.add(TermNode::Lit {
            value: Value::Node(pol),
        });
        let candidates = arena.add(TermNode::Lit {
            value: Value::Tuple(std::sync::Arc::new(smallvec::smallvec![
                Value::Node(held),
                Value::Node(esc),
            ])),
        });
        let selection = arena.add(TermNode::FutureManifoldSelection {
            episode,
            policy,
            candidates,
            field: selected,
            snapshot_field: snapshot,
        });

        // Exercise the actual seed wire form, not only a directly-constructed
        // enum: the graph owns this decision after JSON loading too.
        let json = term_to_json(&arena, selection, &i);
        let mut loaded = TermArena::new();
        let loaded_selection = term_from_json(&json, &mut loaded, &mut i).unwrap();
        let mut env: Env = smallvec::smallvec![];
        let mut ctx = EvalCtx::new(&g, &i);
        assert_eq!(
            evaluate(&loaded, loaded_selection, &mut env, &mut ctx),
            Value::Tuple(std::sync::Arc::new(smallvec::smallvec![Value::Node(
                held
            )])),
            "the cheaper escaping candidate was selected outside the manifold",
        );

        let mut reflected_graph = TypedGraph::new();
        let reflected = crate::reflect::term_to_subgraph(
            &loaded,
            loaded_selection,
            &mut reflected_graph,
            &mut i,
        );
        let mut rebuilt = TermArena::new();
        let rebuilt_selection = crate::reflect::term_from_subgraph(
            &reflected_graph,
            &i,
            reflected,
            &mut rebuilt,
        )
        .unwrap();
        let mut rebuilt_env: Env = smallvec::smallvec![];
        let mut rebuilt_ctx = EvalCtx::new(&g, &i);
        assert_eq!(
            evaluate(
                &rebuilt,
                rebuilt_selection,
                &mut rebuilt_env,
                &mut rebuilt_ctx,
            ),
            Value::Tuple(std::sync::Arc::new(smallvec::smallvec![Value::Node(
                held
            )])),
            "reflection changed the graph-owned selection",
        );
    }

    #[test]
    fn minimum_sufficient_intervention_wins_and_goals_only_break_ties() {
        // CLAUDE.md's rule, read in order: a goal must NOT buy a more expensive
        // candidate. If it could, "minimum sufficient" would be advisory.
        let (mut g, mut i, ep, pol, cheap, _esc) = bench();
        let vals = i.intern("future_manifold_values");
        let ty = i.intern("N");
        let slice = |xs: &[f64]| {
            let sv: smallvec::SmallVec<[Value; 4]> = xs.iter().map(|x| Value::Float(*x)).collect();
            Value::Tuple(std::sync::Arc::new(sv))
        };
        let traj = |rows: &[&[f64]]| {
            let sv: smallvec::SmallVec<[Value; 4]> = rows.iter().map(|r| slice(r)).collect();
            Value::Tuple(std::sync::Arc::new(sv))
        };
        let dear = g.insert_node(ty, FxHashMap::default());
        g.set_node_attr(dear, vals, traj(&[&[0.0], &[0.1], &[0.0]]));

        set(&mut g, &mut i, cheap, "intervention", 1.0);
        set(&mut g, &mut i, cheap, "goal_rank", 0.0);
        set(&mut g, &mut i, dear, "intervention", 5.0);
        set(&mut g, &mut i, dear, "goal_rank", 99.0);

        let sel = feasible_selection(&g, &mut i, ep, pol, &[cheap, dear]).expect("supported");
        assert_eq!(sel.minimal, vec![cheap],
                   "a high goal rank bought a more expensive intervention");
        assert_eq!(sel.tie_breadth, 1);
    }

    #[test]
    fn ideal_effort_is_part_of_feasibility_not_a_later_advisory_gate() {
        let (mut g, mut i, _ep, _pol, normal, compressed) = bench();
        set(&mut g, &mut i, normal, "intervention", 1.0);
        set(&mut g, &mut i, compressed, "intervention", 2.0);
        let tuple = |effort_authorized: f64| {
            Value::Tuple(std::sync::Arc::new(smallvec::smallvec![
                Value::Float(1.0),
                Value::Float(1.0),
                Value::Float(0.0),
                Value::Float(0.0),
                Value::Float(1.0),
                Value::Float(effort_authorized),
            ]))
        };

        let selection = feasible_selection_with_projector(
            &g,
            &i,
            &[normal, compressed],
            |candidate| Some(tuple(if candidate == compressed { 1.0 } else { 0.0 })),
        )
        .expect("snapshots are supported");

        assert_eq!(selection.infeasible, vec![normal]);
        assert_eq!(selection.selected, vec![compressed]);
    }

    #[test]
    fn equal_intervention_ties_are_kept_not_broken_arbitrarily() {
        // Set-valued by design: a selector that returned one candidate would
        // re-impose the single fixpoint the admissibility grammar exists to avoid.
        let (mut g, mut i, ep, pol, a, _esc) = bench();
        let vals = i.intern("future_manifold_values");
        let ty = i.intern("N");
        let slice = |xs: &[f64]| {
            let sv: smallvec::SmallVec<[Value; 4]> = xs.iter().map(|x| Value::Float(*x)).collect();
            Value::Tuple(std::sync::Arc::new(sv))
        };
        let traj = |rows: &[&[f64]]| {
            let sv: smallvec::SmallVec<[Value; 4]> = rows.iter().map(|r| slice(r)).collect();
            Value::Tuple(std::sync::Arc::new(sv))
        };
        let b = g.insert_node(ty, FxHashMap::default());
        g.set_node_attr(b, vals, traj(&[&[0.0], &[0.3], &[0.0]]));
        set(&mut g, &mut i, a, "intervention", 2.0);
        set(&mut g, &mut i, b, "intervention", 2.0);

        let sel = feasible_selection(&g, &mut i, ep, pol, &[a, b]).expect("supported");
        assert_eq!(ids(&sel.minimal), ids(&[a, b]));
        assert_eq!(sel.tie_breadth, 2, "the tie was collapsed to a single winner");
    }

    #[test]
    fn a_feasible_candidate_with_no_represented_valuation_fails_closed() {
        // "Minimum sufficient" over an unrepresented cost is not a smaller
        // number, it is not a question. Ranking it free would launder the gap.
        let (mut g, mut i, ep, pol, held, esc) = bench();
        set(&mut g, &mut i, esc, "intervention", 1.0);
        assert!(feasible_selection(&g, &mut i, ep, pol, &[held, esc]).is_none(),
                "a feasible candidate with no valuation was ranked anyway");
    }

    #[test]
    fn an_empty_family_fails_closed() {
        let (g, mut i, ep, pol, _held, _esc) = bench();
        assert!(feasible_selection(&g, &mut i, ep, pol, &[]).is_none());
    }

    #[test]
    fn stubbornness_is_visible_as_withheld_minimal() {
        // THE POINT OF THIS MODULE. Before it, a candidate that was established,
        // feasible, minimal, and simply not taken was indistinguishable from one
        // that never existed -- the admissible bound never asks what was chosen.
        // Here the two agents differ in exactly one represented bit and the audit
        // separates them.
        let (mut g, mut i, ep, pol, held, esc) = bench();
        set(&mut g, &mut i, held, "intervention", 1.0);
        set(&mut g, &mut i, esc, "intervention", 1.0);

        let open = feasible_selection(&g, &mut i, ep, pol, &[held, esc]).expect("supported");
        assert_eq!(open.selected, vec![held]);
        assert!(open.withheld_minimal.is_empty());

        set(&mut g, &mut i, held, "withheld", 1.0);
        let stubborn = feasible_selection(&g, &mut i, ep, pol, &[held, esc]).expect("supported");

        assert_eq!(stubborn.minimal, vec![held], "it was still the right move");
        assert!(stubborn.selected.is_empty(), "and it was not taken");
        assert_eq!(stubborn.withheld_minimal, vec![held],
                   "stubbornness is not countable -- the audit cannot see it");
    }

    #[test]
    fn ignorant_stupid_and_stubborn_all_have_distinct_signatures() {
        // The diagnostic claim, now complete. The same observable failure --
        // nothing got selected -- reads three different ways in the record, and
        // no two of them are confusable.
        let (mut g, mut i, ep, pol, held, esc) = bench();
        set(&mut g, &mut i, held, "intervention", 1.0);
        set(&mut g, &mut i, esc, "intervention", 1.0);

        // IGNORANT: nothing to project at all. Fails closed -- "not established",
        // never "zero capacity".
        assert!(feasible_selection(&g, &mut i, ep, pol, &[]).is_none());

        // STUBBORN: established, feasible, minimal -- and not taken.
        set(&mut g, &mut i, held, "withheld", 1.0);
        let stubborn = feasible_selection(&g, &mut i, ep, pol, &[held, esc]).expect("supported");
        assert!(stubborn.selected.is_empty());
        assert_eq!(stubborn.withheld_minimal.len(), 1);
        assert!(stubborn.unestablished.is_empty(),
                "a stubborn agent knew perfectly well; that is what makes it stubborn");

        // STUPID: the audit runs and cannot finish. Starving the budget below the
        // horizon used to falsify `support` outright, so this case was previously
        // unreachable -- the agent reported "could not run" rather than "ran, and
        // could not tell".
        set(&mut g, &mut i, held, "withheld", 0.0);
        let budget = i.intern("future_manifold_projection_budget");
        g.set_node_attr(pol, budget, Value::Float(1.0));
        let stupid = feasible_selection(&g, &mut i, ep, pol, &[held, esc]).expect("well-posed");
        assert_eq!(stupid.unestablished.len(), 2,
                   "an unfinished audit was reported as decided");
        assert!(stupid.feasible.is_empty(),
                "a candidate was called feasible without its retention established");
        assert!(stupid.minimal.is_empty() && stupid.selected.is_empty());
        assert!(stupid.withheld_minimal.is_empty(),
                "stupidity is reading as stubbornness -- nothing was withheld here");
    }

    #[test]
    fn information_loss_counts_what_was_not_assessed_not_what_failed() {
        // The fix, at its source. These are different questions and now have
        // different answers:
        //   * a cell that left the tube WAS assessed -- retention established,
        //     as false -- so it is `loss` and NOT information loss;
        //   * a cell the budget never reached was not assessed at all, so it is
        //     information loss and NOT `loss`.
        let (mut g, mut i, ep, pol, held, esc) = bench();

        // Assessed and outside: pure loss, nothing unestablished.
        let escaping = &reachable_deformation_set(&g, &mut i, ep, pol, &[esc])[0];
        assert!(escaping.loss > 0.0, "fixture no longer escapes the tube");
        assert_eq!(escaping.information_loss, 0.0,
                   "a cell that was assessed and failed is being counted as \
                    unassessable");

        // Never reached: pure information loss, nothing outside.
        let budget = i.intern("future_manifold_projection_budget");
        g.set_node_attr(pol, budget, Value::Float(1.0));
        let starved = &reachable_deformation_set(&g, &mut i, ep, pol, &[held])[0];
        assert!(starved.support, "a short budget falsified well-posedness");
        assert!(!starved.resolved, "an unfinished audit reported as resolved");
        assert_eq!(starved.loss, 0.0, "nothing left the tube in the audited part");
        assert!(starved.information_loss > 0.0,
                "the unreached ticks were not counted as unestablished");
        assert_eq!(starved.retained_width, 0.0,
                   "retention was claimed for ticks nobody audited");
    }

    #[test]
    fn an_unresolved_DIMENSION_is_unassessed_not_failed() {
        // APERTURE AT THE MANIFOLD -- the bridge between the two grains.
        //
        // The escaping candidate leaves the tube in dimension 0. An observer that
        // cannot resolve dimension 0 must NOT report that as a loss: it did not
        // see a failure, it saw nothing. That is the whole difference between
        // being wrong and being unable to tell, and it is what makes a narrow
        // observer measurably stupid here rather than merely coarse elsewhere.
        let (mut g, mut i, ep, pol, _held, esc) = bench();
        let blind = &reachable_deformation_set(&g, &mut i, ep, pol, &[esc])[0];
        assert!(blind.loss > 0.0, "fixture no longer escapes in dimension 0");

        let mask = i.intern("future_manifold_resolved_dims");
        let row: smallvec::SmallVec<[Value; 4]> = smallvec::smallvec![Value::Float(0.0)];
        let outer: smallvec::SmallVec<[Value; 4]> =
            smallvec::smallvec![Value::Tuple(std::sync::Arc::new(row))];
        g.set_node_attr(pol, mask, Value::Tuple(std::sync::Arc::new(outer)));

        let narrow = &reachable_deformation_set(&g, &mut i, ep, pol, &[esc])[0];
        assert!(narrow.support, "an aperture mask falsified well-posedness");
        assert_eq!(narrow.loss, 0.0,
                   "an unresolvable dimension was reported as a failure rather \
                    than as unassessed");
        assert!(narrow.information_loss > 0.0,
                "the unresolved dimension was not counted as unestablished");
        assert_eq!(narrow.retained_width, 0.0,
                   "retention was claimed for a dimension never assessed");
        assert!(!narrow.resolved, "an unassessable audit reported as resolved");
    }

    #[test]
    fn a_full_aperture_mask_is_byte_identical_to_no_mask() {
        // The default must not move. An all-ones mask is the same audit.
        let (mut g, mut i, ep, pol, held, esc) = bench();
        let before = reachable_deformation_set(&g, &mut i, ep, pol, &[held, esc]);
        let mask = i.intern("future_manifold_resolved_dims");
        let row: smallvec::SmallVec<[Value; 4]> = smallvec::smallvec![Value::Float(1.0)];
        let outer: smallvec::SmallVec<[Value; 4]> =
            smallvec::smallvec![Value::Tuple(std::sync::Arc::new(row))];
        g.set_node_attr(pol, mask, Value::Tuple(std::sync::Arc::new(outer)));
        let after = reachable_deformation_set(&g, &mut i, ep, pol, &[held, esc]);
        assert_eq!(before, after, "an all-resolving mask changed the audit");
    }

    #[test]
    fn a_wrong_length_mask_is_ignored_rather_than_half_applied() {
        // Fail SAFE, not closed, and deliberately: a malformed mask must not
        // silently blind one dimension. Length is the only thing that can be
        // checked here, so it is.
        let (mut g, mut i, ep, pol, held, esc) = bench();
        let before = reachable_deformation_set(&g, &mut i, ep, pol, &[held, esc]);
        let mask = i.intern("future_manifold_resolved_dims");
        let row: smallvec::SmallVec<[Value; 4]> =
            smallvec::smallvec![Value::Float(0.0), Value::Float(0.0)];
        let outer: smallvec::SmallVec<[Value; 4]> =
            smallvec::smallvec![Value::Tuple(std::sync::Arc::new(row))];
        g.set_node_attr(pol, mask, Value::Tuple(std::sync::Arc::new(outer)));
        assert_eq!(before, reachable_deformation_set(&g, &mut i, ep, pol, &[held, esc]));
    }

    #[test]
    fn narrowing_the_aperture_makes_an_agent_STUPID_not_ignorant_or_stubborn() {
        // The unified claim, at one grain: compress what an observer resolves and
        // its signature moves to `unestablished` -- not to an empty family
        // (ignorant), not to withheld-minimal (stubborn).
        let (mut g, mut i, ep, pol, held, esc) = bench();
        set(&mut g, &mut i, held, "intervention", 1.0);
        set(&mut g, &mut i, esc, "intervention", 1.0);

        let wide = feasible_selection(&g, &mut i, ep, pol, &[held, esc]).expect("well-posed");
        assert_eq!(wide.selected, vec![held], "the wide observer chooses normally");
        assert!(wide.unestablished.is_empty());

        let mask = i.intern("future_manifold_resolved_dims");
        let row: smallvec::SmallVec<[Value; 4]> = smallvec::smallvec![Value::Float(0.0)];
        let outer: smallvec::SmallVec<[Value; 4]> =
            smallvec::smallvec![Value::Tuple(std::sync::Arc::new(row))];
        g.set_node_attr(pol, mask, Value::Tuple(std::sync::Arc::new(outer)));

        let narrow = feasible_selection(&g, &mut i, ep, pol, &[held, esc]).expect("well-posed");
        assert_eq!(narrow.unestablished.len(), 2, "compression did not read as stupid");
        assert!(narrow.feasible.is_empty(), "feasibility claimed without assessment");
        assert!(narrow.selected.is_empty());
        assert!(narrow.withheld_minimal.is_empty(),
                "compression is reading as stubbornness -- nothing was withheld");
    }

    #[test]
    fn resolved_is_no_longer_derivable_from_support() {
        // The second half of the collapse. Before the fix `resolved == support`
        // always, so the field carried nothing; a starved audit must now be
        // supported AND unresolved, which is the state that never existed.
        let (mut g, mut i, ep, pol, held, _esc) = bench();
        let budget = i.intern("future_manifold_projection_budget");
        g.set_node_attr(pol, budget, Value::Float(1.0));
        let r = &reachable_deformation_set(&g, &mut i, ep, pol, &[held])[0];
        assert!(r.support && !r.resolved,
                "support={} resolved={} -- the two are still collapsed",
                r.support, r.resolved);
    }
}
