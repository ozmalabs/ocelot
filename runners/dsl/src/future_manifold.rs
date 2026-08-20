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
