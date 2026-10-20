//! Native execution of graph-requested pure cognitive tasks.
//!
//! Rules decide which `CognitiveTask` nodes reach `status="requested"`.
//! Workers receive immutable Values and return typed results.  Only this
//! serial owner mutates the live graph, in deterministic task-key order.

use crate::graph::NodeID;
use crate::substrate::Substrate;
use crate::sym::Sym;
use crate::value::Value;
use rustc_hash::FxHashMap;
use std::collections::VecDeque;
use std::sync::{mpsc, Arc, Mutex};
use crate::clock::Instant;

#[derive(Clone, Debug)]
pub(crate) struct TaskSpec {
    node: NodeID,
    kind: String,
    payload: Value,
    input_epoch: i64,
    deadline_epoch: Option<i64>,
    logical_time: i64,
    area: Sym,
    context: Option<NodeID>,
    clock: Option<NodeID>,
    invalid_provenance: bool,
    process_lease: Option<ProcessLeaseSnapshot>,
}

#[derive(Clone, Debug)]
struct ProcessLeaseSnapshot {
    process: NodeID,
    policy: NodeID,
    generation: i64,
    is_checkin: bool,
}

#[derive(Clone, Debug)]
pub(crate) struct TaskCompletion {
    spec: TaskSpec,
    output: Option<Value>,
    error: Option<String>,
    wall_micros: u64,
}

#[derive(Clone, Debug, Default)]
pub struct TaskRunSummary {
    pub requested: usize,
    pub completed: usize,
    pub failed: usize,
    pub stale: usize,
    pub workers_used: usize,
    pub wall_micros: u64,
}

pub(crate) struct PreparedTaskBatch {
    tasks: Vec<TaskSpec>,
    workers_used: usize,
    capacity: usize,
    started: Instant,
}

pub(crate) struct CompletedTaskBatch {
    completions: Vec<TaskCompletion>,
    requested: usize,
    workers_used: usize,
    capacity: usize,
    started: Instant,
}

fn number(v: &Value) -> Option<f64> {
    match v {
        Value::Int(x) => Some(*x as f64),
        Value::Float(x) => Some(*x),
        _ => None,
    }
}

fn numeric_values(value: &Value) -> Result<Vec<f64>, String> {
    let (Value::Tuple(items) | Value::List(items)) = value else {
        return Err("payload must be a numeric tuple".into());
    };
    items
        .iter()
        .map(|v| number(v).ok_or_else(|| "payload contains non-number".into()))
        .collect()
}

/// Mechanical foveated-aperture exposure. The entire receptor sheet crosses
/// PyO3 once and is sampled in compiled code; no receptor selection or policy
/// lives here. Coordinates and apertures are radians in a frame-centred field.
///
/// Each receptor returns the exact area-weighted mean under its rectangular
/// aperture. Integer-aligned apertures therefore reproduce ordinary block
/// means exactly (including one-native-pixel foveal apertures).
pub(crate) fn sample_retinal_layout(
    luma: &[f64],
    source_height: usize,
    source_width: usize,
    gaze_az: &[f64],
    gaze_el: &[f64],
    angular_width: &[f64],
    angular_height: &[f64],
    fov_h: f64,
    fov_v: f64,
) -> Result<Vec<f64>, String> {
    if source_height == 0 || source_width == 0 || luma.len() != source_height * source_width {
        return Err("luma size does not match positive source dimensions".into());
    }
    let n = gaze_az.len();
    if gaze_el.len() != n || angular_width.len() != n || angular_height.len() != n {
        return Err("receptor geometry vectors must have equal length".into());
    }
    if !(fov_h.is_finite() && fov_h > 0.0 && fov_v.is_finite() && fov_v > 0.0) {
        return Err("field of view must be finite and positive".into());
    }
    let mut out = Vec::with_capacity(n);
    for i in 0..n {
        let (az, el, aw, ah) = (gaze_az[i], gaze_el[i], angular_width[i], angular_height[i]);
        if !az.is_finite()
            || !el.is_finite()
            || !aw.is_finite()
            || !ah.is_finite()
            || aw <= 0.0
            || ah <= 0.0
        {
            return Err(format!("invalid receptor geometry at index {i}"));
        }
        let mut x0 = ((az - aw * 0.5) / fov_h + 0.5) * source_width as f64;
        let mut x1 = ((az + aw * 0.5) / fov_h + 0.5) * source_width as f64;
        let mut y0 = ((el - ah * 0.5) / fov_v + 0.5) * source_height as f64;
        let mut y1 = ((el + ah * 0.5) / fov_v + 0.5) * source_height as f64;
        x0 = x0.clamp(0.0, source_width as f64);
        x1 = x1.clamp(0.0, source_width as f64);
        y0 = y0.clamp(0.0, source_height as f64);
        y1 = y1.clamp(0.0, source_height as f64);
        for edge in [&mut x0, &mut x1, &mut y0, &mut y1] {
            let rounded = edge.round();
            if (*edge - rounded).abs() < 1.0e-10 {
                *edge = rounded;
            }
        }
        if x1 <= x0 || y1 <= y0 {
            let x = (((az / fov_h) + 0.5) * source_width as f64)
                .floor()
                .clamp(0.0, (source_width - 1) as f64) as usize;
            let y = (((el / fov_v) + 0.5) * source_height as f64)
                .floor()
                .clamp(0.0, (source_height - 1) as f64) as usize;
            out.push(luma[y * source_width + x]);
            continue;
        }
        let ix0 = x0.floor() as usize;
        let ix1 = x1.ceil().min(source_width as f64) as usize;
        let iy0 = y0.floor() as usize;
        let iy1 = y1.ceil().min(source_height as f64) as usize;
        let mut weighted = 0.0;
        let mut area = 0.0;
        for y in iy0..iy1 {
            let wy = (y1.min((y + 1) as f64) - y0.max(y as f64)).max(0.0);
            for x in ix0..ix1 {
                let wx = (x1.min((x + 1) as f64) - x0.max(x as f64)).max(0.0);
                let weight = wx * wy;
                weighted += luma[y * source_width + x] * weight;
                area += weight;
            }
        }
        out.push(weighted / area);
    }
    Ok(out)
}

/// Mechanically project allocentric surface samples into explicit receptors.
///
/// Surface samples are spherical support regions in world coordinates. For
/// each receptor, the nearest angularly overlapping support wins and therefore
/// occludes farther supports. Unknown space is represented by the absence of a
/// surface sample and remains absent in the returned `present` vector.
#[allow(clippy::too_many_arguments)]
pub(crate) fn project_allocentric_retina(
    surface_x: &[f64],
    surface_y: &[f64],
    surface_z: &[f64],
    surface_radius: &[f64],
    surface_value: &[f64],
    surface_confidence: &[f64],
    pose_x: f64,
    pose_y: f64,
    pose_z: f64,
    pose_yaw: f64,
    pose_pitch: f64,
    receptor_az: &[f64],
    receptor_el: &[f64],
    receptor_width: &[f64],
    receptor_height: &[f64],
) -> Result<(Vec<f64>, Vec<f64>, Vec<bool>, Vec<i64>), String> {
    let n_surface = surface_x.len();
    if surface_y.len() != n_surface
        || surface_z.len() != n_surface
        || surface_radius.len() != n_surface
        || surface_value.len() != n_surface
        || surface_confidence.len() != n_surface
    {
        return Err("allocentric surface vectors must have equal length".into());
    }
    let n_receptor = receptor_az.len();
    if receptor_el.len() != n_receptor
        || receptor_width.len() != n_receptor
        || receptor_height.len() != n_receptor
    {
        return Err("explicit receptor vectors must have equal length".into());
    }
    if ![pose_x, pose_y, pose_z, pose_yaw, pose_pitch]
        .iter()
        .all(|x| x.is_finite())
    {
        return Err("pose must be finite".into());
    }
    for i in 0..n_surface {
        if ![
            surface_x[i],
            surface_y[i],
            surface_z[i],
            surface_radius[i],
            surface_value[i],
            surface_confidence[i],
        ]
        .iter()
        .all(|x| x.is_finite())
            || surface_radius[i] < 0.0
            || surface_confidence[i] < 0.0
        {
            return Err(format!("invalid allocentric surface at index {i}"));
        }
    }
    for i in 0..n_receptor {
        if ![
            receptor_az[i],
            receptor_el[i],
            receptor_width[i],
            receptor_height[i],
        ]
        .iter()
        .all(|x| x.is_finite())
            || receptor_width[i] <= 0.0
            || receptor_height[i] <= 0.0
        {
            return Err(format!("invalid explicit receptor at index {i}"));
        }
    }

    let wrap = |angle: f64| {
        (angle + std::f64::consts::PI).rem_euclid(std::f64::consts::TAU) - std::f64::consts::PI
    };
    let mut values = vec![0.0; n_receptor];
    let mut confidences = vec![0.0; n_receptor];
    let mut present = vec![false; n_receptor];
    let mut source_indices = vec![-1; n_receptor];
    let mut nearest = vec![f64::INFINITY; n_receptor];

    for surface in 0..n_surface {
        let dx = surface_x[surface] - pose_x;
        let dy = surface_y[surface] - pose_y;
        let dz = surface_z[surface] - pose_z;
        let horizontal = dx.hypot(dy);
        let distance = horizontal.hypot(dz);
        let angular_radius = if distance == 0.0 {
            std::f64::consts::PI
        } else {
            (surface_radius[surface] / distance).clamp(0.0, 1.0).asin()
        };
        let az = wrap(dy.atan2(dx) - pose_yaw);
        let el = dz.atan2(horizontal) - pose_pitch;
        let near_distance = (distance - surface_radius[surface]).max(0.0);
        for receptor in 0..n_receptor {
            if wrap(az - receptor_az[receptor]).abs()
                <= receptor_width[receptor] * 0.5 + angular_radius
                && (el - receptor_el[receptor]).abs()
                    <= receptor_height[receptor] * 0.5 + angular_radius
                && near_distance < nearest[receptor]
            {
                nearest[receptor] = near_distance;
                values[receptor] = surface_value[surface];
                confidences[receptor] = surface_confidence[surface];
                present[receptor] = true;
                source_indices[receptor] = surface as i64;
            }
        }
    }
    Ok((values, confidences, present, source_indices))
}

fn execute_kernel(kind: &str, payload: &Value) -> Result<Value, String> {
    match kind {
        "identity" => Ok(payload.clone()),
        "vector_sum" => Ok(Value::Float(numeric_values(payload)?.iter().sum())),
        "default_mode_projection" => {
            // Pure, bounded intrinsic simulation envelope. Graph rules choose
            // the source and author the immutable snapshot
            // [input_epoch, deadline_epoch, budget, uncertainty]. The kernel
            // performs no graph reads and returns typed material for the graph
            // to interpret as imagined/prospective, never as an observation.
            let xs = numeric_values(payload)?;
            if xs.len() != 4 {
                return Err(
                    "default_mode_projection expects epoch, deadline, budget, uncertainty".into(),
                );
            }
            let horizon = (xs[1] - xs[0]).max(0.0);
            let passes = xs[2].max(0.0).min(horizon.max(1.0));
            let confidence = (1.0 - xs[3]).clamp(0.0, 1.0);
            Ok(Value::Tuple(Arc::new(
                vec![
                    Value::Float(horizon),
                    Value::Float(passes),
                    Value::Float(confidence),
                ]
                .into(),
            )))
        }
        "abs_diff_energy" => {
            let xs = numeric_values(payload)?;
            Ok(Value::Float(
                xs.windows(2).map(|w| (w[1] - w[0]).abs()).sum(),
            ))
        }
        "vision_convolve" => {
            let xs = numeric_values(payload)?;
            if xs.len() < 5 {
                return Err("vision_convolve payload missing dimensions".into());
            }
            let h = xs[0] as usize;
            let w = xs[1] as usize;
            let kh = xs[2] as usize;
            let kw = xs[3] as usize;
            let stride = xs[4] as usize;
            let image_n = h.saturating_mul(w);
            let kernel_n = kh.saturating_mul(kw);
            if xs.len() != 5 + image_n + kernel_n {
                return Err("vision_convolve payload length mismatch".into());
            }
            let output = crate::vision_primitives::convolve(
                &xs[5..5 + image_n],
                h,
                w,
                &xs[5 + image_n..],
                kh,
                kw,
                stride,
            );
            Ok(Value::Tuple(Arc::new(
                output.into_iter().map(Value::Float).collect(),
            )))
        }
        "dft_energy" => {
            let xs = numeric_values(payload)?;
            let n = xs.len().max(1) as f64;
            let mut energy = 0.0;
            for k in 0..xs.len() {
                let mut re = 0.0;
                let mut im = 0.0;
                for (t, x) in xs.iter().enumerate() {
                    let phase = std::f64::consts::TAU * (k * t) as f64 / n;
                    re += x * phase.cos();
                    im -= x * phase.sin();
                }
                energy += re * re + im * im;
            }
            Ok(Value::Float(energy))
        }
        "photon_transduce" => {
            let xs = numeric_values(payload)?;
            if xs.len() < 6 || (xs.len() - 6) % 2 != 0 {
                return Err(
                    "photon_transduce expects receptor params + wavelength/count pairs".into(),
                );
            }
            let center_nm = xs[0];
            let bandwidth_nm = xs[1].abs().max(1e-9);
            let adaptation = xs[2].max(0.0);
            let adapt_rate = xs[3].clamp(0.0, 1.0);
            let half_saturation = xs[4].max(1e-9);
            let dark_current = xs[5].max(0.0);
            let mut caught = dark_current;
            for packet in xs[6..].chunks_exact(2) {
                let wavelength_nm = packet[0];
                let count = packet[1].max(0.0);
                let z = (wavelength_nm - center_nm) / bandwidth_nm;
                caught += count * (-0.5 * z * z).exp();
            }
            // Naka-Rushton-shaped saturation with light adaptation carried
            // across observations as graph state.
            let response = caught / (caught + half_saturation + adaptation);
            let next_adaptation = adaptation + adapt_rate * (caught - adaptation);
            Ok(Value::Tuple(Arc::new(
                vec![
                    Value::Float(response),
                    Value::Float(next_adaptation),
                    Value::Float(caught),
                ]
                .into(),
            )))
        }
        "photon_transduce_onset" => {
            // Onset-emitting PEER of `photon_transduce`. Its first three
            // outputs (response / next_adaptation / caught) are computed
            // byte-identically, so the shared `photon_apply_receptor_transduction`
            // rule — which reads output[0..2] by index and does not filter on
            // kind — folds it unchanged. It appends a FOURTH value: the dB
            // DEPARTURE of the instantaneous drive (`caught`) from the
            // receptor's OWN adapting floor (`adaptation`, the async low-pass
            // of its past light). This is the visual analog of the cochlear
            // nucleus `detect_onsets` "dB above the local floor" line (eps =
            // 1e-10, 20·log10 of the ratio) — envelope↔`caught`, floor↔the
            // receptor's held `adaptation`. A graph rule thresholds it and
            // enforces a refractory to MINT RetinalOnsetEvent nodes. OFF by
            // default: the retina emits this kind only when the onset path is
            // enabled in the graph; plain `photon_transduce` is byte-unchanged.
            let xs = numeric_values(payload)?;
            if xs.len() < 6 || (xs.len() - 6) % 2 != 0 {
                return Err(
                    "photon_transduce_onset expects receptor params + wavelength/count pairs"
                        .into(),
                );
            }
            let center_nm = xs[0];
            let bandwidth_nm = xs[1].abs().max(1e-9);
            let adaptation = xs[2].max(0.0);
            let adapt_rate = xs[3].clamp(0.0, 1.0);
            let half_saturation = xs[4].max(1e-9);
            let dark_current = xs[5].max(0.0);
            let mut caught = dark_current;
            for packet in xs[6..].chunks_exact(2) {
                let wavelength_nm = packet[0];
                let count = packet[1].max(0.0);
                let z = (wavelength_nm - center_nm) / bandwidth_nm;
                caught += count * (-0.5 * z * z).exp();
            }
            let response = caught / (caught + half_saturation + adaptation);
            let next_adaptation = adaptation + adapt_rate * (caught - adaptation);
            // dB above the adapting floor. `adaptation` is the floor the
            // receptor held BEFORE this observation; a brightening transient
            // drives `caught` above it (departs positive), a sustained hold
            // decays toward ~0 as the floor catches up, a dimming departs
            // negative. Freeze the floor (adapt_rate = 0) and a sustained
            // bright input never silences — the adaptation-OFF control.
            let eps = 1e-10f64;
            let onset_db = 20.0 * ((caught.max(0.0) + eps) / (adaptation + eps)).log10();
            Ok(Value::Tuple(Arc::new(
                vec![
                    Value::Float(response),
                    Value::Float(next_adaptation),
                    Value::Float(caught),
                    Value::Float(onset_db),
                ]
                .into(),
            )))
        }
        "retinal_flow_depth" => {
            let xs = numeric_values(payload)?;
            if xs.len() < 4 {
                return Err("retinal_flow_depth payload missing header".into());
            }
            let h = xs[0] as usize;
            let w = xs[1] as usize;
            let translation = xs[2].abs();
            let max_shift = xs[3].max(1.0) as isize;
            let n = h.saturating_mul(w);
            if xs.len() != 4 + 2 * n {
                return Err("retinal_flow_depth payload length mismatch".into());
            }
            let prev = &xs[4..4 + n];
            let curr = &xs[4 + n..];
            let focal = w as f64 * 0.5;
            let mut out = Vec::with_capacity(w * 2);
            for x in 0..w {
                let mut best_shift = 0isize;
                let mut best_cost = f64::INFINITY;
                for shift in -max_shift..=max_shift {
                    let px = x as isize + shift;
                    if px < 0 || px >= w as isize {
                        continue;
                    }
                    let mut cost = 0.0;
                    for y in 0..h {
                        cost += (curr[y * w + x] - prev[y * w + px as usize]).abs();
                    }
                    if cost < best_cost {
                        best_cost = cost;
                        best_shift = shift;
                    }
                }
                let depth = if translation > 0.0 && best_shift != 0 {
                    translation * focal / (best_shift.unsigned_abs() as f64)
                } else {
                    -1.0
                };
                out.push(Value::Float((x as f64 + 0.5) / w as f64 - 0.5));
                out.push(Value::Float(depth));
            }
            Ok(Value::Tuple(Arc::new(out.into())))
        }
        "retinal_event_motion" => {
            // ASYNC MOTION FROM THE ONSET-EVENT STREAM (Rung 2 of the
            // photon-eye migration). Motion is SETTLED from the accumulated
            // `RetinalOnsetEvent`s available this tick — NOT differenced from
            // two synchronized frames (no `vector_field`, no `retinal_flow_depth`
            // frame diff, no `retinal_field` raster). A moving edge fires onset
            // events in adjacent columns at SUCCESSIVE per-receptor epochs; each
            // event carries its OWN epoch (its own clock). The velocity is the
            // least-squares SLOPE of column position on per-event epoch — the
            // space-time STRUCTURE of the event cloud. Payload:
            // `[n, c_0, e_0, ..., c_{n-1}, e_{n-1}]` (column index, own epoch).
            // Returns `(direction=sign(slope), speed=|slope|, residual=SSE,
            // coherence=|Pearson r|, n)`. A static/instantaneous set (zero
            // temporal spread), a single-column set (zero spatial spread), or
            // `n<2` carries NO direction → `(0,0,·,0,n)`; a SCRAMBLED-epoch set
            // decorrelates to `coherence≈0`. The residual is the unexplained
            // column variance the fit leaves behind — the settlement remainder,
            // never a snapshot difference.
            let xs = numeric_values(payload)?;
            if xs.is_empty() {
                return Err("retinal_event_motion payload missing event count".into());
            }
            let n = xs[0].max(0.0) as usize;
            if xs.len() != 1 + 2 * n {
                return Err("retinal_event_motion payload length mismatch".into());
            }
            if n < 2 {
                return Ok(Value::Tuple(Arc::new(
                    vec![
                        Value::Float(0.0),
                        Value::Float(0.0),
                        Value::Float(0.0),
                        Value::Float(0.0),
                        Value::Float(n as f64),
                    ]
                    .into(),
                )));
            }
            let mut sum_c = 0.0;
            let mut sum_e = 0.0;
            for i in 0..n {
                sum_c += xs[1 + 2 * i];
                sum_e += xs[2 + 2 * i];
            }
            let mean_c = sum_c / n as f64;
            let mean_e = sum_e / n as f64;
            let (mut s_ee, mut s_cc, mut s_ec) = (0.0, 0.0, 0.0);
            for i in 0..n {
                let dc = xs[1 + 2 * i] - mean_c;
                let de = xs[2 + 2 * i] - mean_e;
                s_ee += de * de;
                s_cc += dc * dc;
                s_ec += de * dc;
            }
            // A slope needs BOTH a temporal spread (events across epochs) and a
            // spatial spread (events across columns). Absent either — a flash in
            // one instant, or a stationary flicker in one column — there is no
            // motion to recover.
            if s_ee <= 0.0 || s_cc <= 0.0 {
                return Ok(Value::Tuple(Arc::new(
                    vec![
                        Value::Float(0.0),
                        Value::Float(0.0),
                        Value::Float(s_cc),
                        Value::Float(0.0),
                        Value::Float(n as f64),
                    ]
                    .into(),
                )));
            }
            let slope = s_ec / s_ee;
            let coherence = (s_ec / (s_ee * s_cc).sqrt()).abs();
            let residual = (s_cc - slope * s_ec).max(0.0);
            let direction = if slope > 0.0 {
                1.0
            } else if slope < 0.0 {
                -1.0
            } else {
                0.0
            };
            Ok(Value::Tuple(Arc::new(
                vec![
                    Value::Float(direction),
                    Value::Float(slope.abs()),
                    Value::Float(residual),
                    Value::Float(coherence),
                    Value::Float(n as f64),
                ]
                .into(),
            )))
        }
        "retinal_event_motion_2d" => {
            // ASYNC 2-D MOTION FROM THE ONSET-EVENT STREAM — the 2-D expansion
            // of `retinal_event_motion` (the named 166000 follow-on that CLOSES
            // the 2-D loop). Rungs 1-4 read azimuth (`column_index`) ONLY, so a
            // PURELY VERTICAL mover — all onset events at ONE azimuth column,
            // its rows sweeping over successive epochs — has ZERO azimuth
            // spatial spread and is INVISIBLE to the 1-D kernel (it reports
            // `speed 0`, `coherence 0`). Here the events carry `(col, row,
            // epoch)` and the velocity is recovered in BOTH axes: `v_az` = the
            // least-squares slope of `col` on epoch, `v_el` = the slope of `row`
            // on epoch — the same space-time regression the 2-D carve fits
            // internally, exposed as a percept. A vertical mover recovers its
            // `v_el` (correct sign + magnitude) with `v_az ≈ 0`; a diagonal
            // mover recovers BOTH. NO new DSL Term enum variant — a new pure
            // `CognitiveTask` kind beside the byte-untouched 1-D kind, exactly
            // as 166000 added `retinal_common_fate_carve_2d`.
            //
            // Payload: `[n, c_0, r_0, e_0, …, c_{n-1}, r_{n-1}, e_{n-1}]`.
            // Output tuple:
            //   (v_az, v_el, dir_az=sign(v_az), dir_el=sign(v_el),
            //    speed=|(v_az,v_el)|, residual=unexplained 2-D SSE,
            //    coherence, n).
            // `coherence` is the COMBINED multiple-correlation
            //   sqrt((s_ec² + s_er²) / (s_ee·(s_cc + s_rr))),
            // which reduces EXACTLY to the 1-D `|Pearson r|` when `s_rr = 0`
            // (a horizontal mover) — so the 2-D kernel never loses the 1-D
            // case — and is 1.0 for a noiseless sweep in ANY direction,
            // INCLUDING pure elevation (`s_cc = 0`). `n<2`, zero temporal
            // spread (a flash), or zero spatial spread (a stationary flicker)
            // carries NO motion → coherence 0.
            let xs = numeric_values(payload)?;
            if xs.is_empty() {
                return Err("retinal_event_motion_2d payload missing event count".into());
            }
            let n = xs[0].max(0.0) as usize;
            if xs.len() != 1 + 3 * n {
                return Err("retinal_event_motion_2d payload length mismatch".into());
            }
            if n < 2 {
                return Ok(Value::Tuple(Arc::new(
                    vec![
                        Value::Float(0.0),
                        Value::Float(0.0),
                        Value::Float(0.0),
                        Value::Float(0.0),
                        Value::Float(0.0),
                        Value::Float(0.0),
                        Value::Float(0.0),
                        Value::Float(n as f64),
                    ]
                    .into(),
                )));
            }
            let (mut sum_c, mut sum_r, mut sum_e) = (0.0, 0.0, 0.0);
            for i in 0..n {
                sum_c += xs[1 + 3 * i];
                sum_r += xs[2 + 3 * i];
                sum_e += xs[3 + 3 * i];
            }
            let mean_c = sum_c / n as f64;
            let mean_r = sum_r / n as f64;
            let mean_e = sum_e / n as f64;
            let (mut s_ee, mut s_cc, mut s_rr, mut s_ec, mut s_er) = (0.0, 0.0, 0.0, 0.0, 0.0);
            for i in 0..n {
                let dc = xs[1 + 3 * i] - mean_c;
                let dr = xs[2 + 3 * i] - mean_r;
                let de = xs[3 + 3 * i] - mean_e;
                s_ee += de * de;
                s_cc += dc * dc;
                s_rr += dr * dr;
                s_ec += de * dc;
                s_er += de * dr;
            }
            // Motion needs a temporal spread (events across epochs) AND a
            // spatial spread on at least ONE axis. Absent either, no motion.
            if s_ee <= 0.0 || (s_cc <= 0.0 && s_rr <= 0.0) {
                return Ok(Value::Tuple(Arc::new(
                    vec![
                        Value::Float(0.0),
                        Value::Float(0.0),
                        Value::Float(0.0),
                        Value::Float(0.0),
                        Value::Float(0.0),
                        Value::Float((s_cc + s_rr).max(0.0)),
                        Value::Float(0.0),
                        Value::Float(n as f64),
                    ]
                    .into(),
                )));
            }
            let v_az = s_ec / s_ee;
            let v_el = s_er / s_ee;
            let speed = (v_az * v_az + v_el * v_el).sqrt();
            let dir_az = if v_az > 0.0 {
                1.0
            } else if v_az < 0.0 {
                -1.0
            } else {
                0.0
            };
            let dir_el = if v_el > 0.0 {
                1.0
            } else if v_el < 0.0 {
                -1.0
            } else {
                0.0
            };
            // Combined multiple-correlation over both axes; reduces to the 1-D
            // |Pearson r| when one axis has no spatial spread.
            let explained = (s_ec * s_ec + s_er * s_er) / s_ee;
            let total = s_cc + s_rr;
            let coherence = if total > 0.0 {
                (explained / total).max(0.0).min(1.0).sqrt()
            } else {
                0.0
            };
            // Unexplained 2-D spatial variance (the settlement remainder).
            let residual = (total - explained).max(0.0);
            Ok(Value::Tuple(Arc::new(
                vec![
                    Value::Float(v_az),
                    Value::Float(v_el),
                    Value::Float(dir_az),
                    Value::Float(dir_el),
                    Value::Float(speed),
                    Value::Float(residual),
                    Value::Float(coherence),
                    Value::Float(n as f64),
                ]
                .into(),
            )))
        }
        "retinal_common_fate_carve" => {
            // ASYNC COMMON-FATE CARVE (Rung 3 of the photon-eye migration).
            // Group contiguous retinal columns whose onset events share ONE
            // coherent motion (common fate) into azimuth-span objects — the
            // event-native replacement for the raster carve (`native.segment`
            // on the coarse `retinal_field`). Input is the SAME async event
            // stream Rung 2 reads: `RetinalOnsetEvent` (column index, own
            // epoch); no `retinal_field` raster, no frame diff. Payload:
            // `[n_az, max_gap, vel_tol, k, c_0, e_0, …, c_{k-1}, e_{k-1}]`.
            //
            // A moving object fires onset events across ADJACENT columns at
            // SUCCESSIVE epochs — a clean space-time diagonal (one shared
            // velocity `Δc/Δe`). Two objects of DIFFERENT common fate have
            // DIFFERENT diagonals (a sign flip or a velocity jump between
            // them); a static/incoherent field has no coherent diagonal. The
            // carve SEGMENTS the sorted firing columns into maximal
            // common-fate runs, then fits each run's motion (the Rung-2
            // regression). This is 1-D (an azimuth strip): a TRUE 2-D carve
            // needs the retina extended to elevation columns — a named
            // follow-on, not this kernel.
            //
            // Output is a FIXED per-column layout of stride 7 so a per-column
            // graph rule (Rung-1/Rung-2 house style) can mint exactly one
            // `VisionPolygon` per run, anchored at the run's START column:
            //   [is_group_start, col_min, col_max, direction, speed,
            //    coherence, n_events]  for each column 0..n_az.
            // The run's block is written at its start column's index; every
            // other column is all-zero. The mint rule gates on coherence /
            // n_events (thresholds held as DATA on a params node), so an
            // incoherent fragment carves nothing.
            const STRIDE: usize = 7;
            let xs = numeric_values(payload)?;
            if xs.len() < 4 {
                return Err("retinal_common_fate_carve payload missing header".into());
            }
            let n_az = xs[0].max(0.0) as usize;
            let max_gap = xs[1].max(1.0);
            let vel_tol = xs[2].max(0.0);
            let k = xs[3].max(0.0) as usize;
            if xs.len() != 4 + 2 * k {
                return Err("retinal_common_fate_carve payload length mismatch".into());
            }
            let mut out = vec![0.0f64; n_az * STRIDE];
            // Reduce events to one MEAN epoch per firing column (a moving edge
            // fires a column once; multiple fires average). Sort by column.
            let mut sum: std::collections::BTreeMap<i64, (f64, f64)> =
                std::collections::BTreeMap::new();
            for i in 0..k {
                let c = xs[4 + 2 * i];
                let e = xs[5 + 2 * i];
                let ci = c.round() as i64;
                if ci < 0 || ci as usize >= n_az {
                    continue;
                }
                let entry = sum.entry(ci).or_insert((0.0, 0.0));
                entry.0 += e;
                entry.1 += 1.0;
            }
            let cols: Vec<(f64, f64)> = sum
                .into_iter()
                .map(|(c, (se, ne))| (c as f64, se / ne))
                .collect();
            let m = cols.len();
            // Segment the sorted firing columns into maximal COMMON-FATE runs.
            // A run extends to the next column only if it is spatially
            // contiguous (gap <= max_gap), its local slope Δc/Δe shares the
            // run's SIGN, and its magnitude is within vel_tol (relative) of the
            // run's FIRST local slope. Δe=0 (a simultaneous pair) is an
            // infinite velocity — it closes the run.
            let mut i = 0usize;
            while i < m {
                let start = i;
                let mut ref_v: Option<f64> = None;
                while i + 1 < m {
                    let dc = cols[i + 1].0 - cols[i].0;
                    let de = cols[i + 1].1 - cols[i].1;
                    if dc > max_gap || de == 0.0 {
                        break;
                    }
                    let v = dc / de;
                    match ref_v {
                        None => ref_v = Some(v),
                        Some(rv) => {
                            if (v > 0.0) != (rv > 0.0) {
                                break; // sign flip = different common fate
                            }
                            let rel = (v - rv).abs() / (rv.abs() + 1e-9);
                            if rel > vel_tol {
                                break; // velocity jump = different common fate
                            }
                        }
                    }
                    i += 1;
                }
                // Fit the run [start..=i] (column on epoch), Rung-2 regression.
                let run = &cols[start..=i];
                let rn = run.len();
                let (mut sc, mut se) = (0.0, 0.0);
                for &(c, e) in run {
                    sc += c;
                    se += e;
                }
                let (mc, me) = (sc / rn as f64, se / rn as f64);
                let (mut s_ee, mut s_cc, mut s_ec) = (0.0, 0.0, 0.0);
                for &(c, e) in run {
                    let (dc, de) = (c - mc, e - me);
                    s_ee += de * de;
                    s_cc += dc * dc;
                    s_ec += de * dc;
                }
                let (direction, speed, coherence) = if rn >= 2 && s_ee > 0.0 && s_cc > 0.0 {
                    let slope = s_ec / s_ee;
                    let coh = (s_ec / (s_ee * s_cc).sqrt()).abs();
                    let dir = if slope > 0.0 {
                        1.0
                    } else if slope < 0.0 {
                        -1.0
                    } else {
                        0.0
                    };
                    (dir, slope.abs(), coh)
                } else {
                    (0.0, 0.0, 0.0)
                };
                let col_min = run.first().unwrap().0;
                let col_max = run.last().unwrap().0;
                let anchor = col_min as usize; // start column's index
                let base = anchor * STRIDE;
                out[base] = 1.0; // is_group_start
                out[base + 1] = col_min;
                out[base + 2] = col_max;
                out[base + 3] = direction;
                out[base + 4] = speed;
                out[base + 5] = coherence;
                out[base + 6] = rn as f64;
                i += 1;
            }
            Ok(Value::Tuple(Arc::new(
                out.into_iter().map(Value::Float).collect(),
            )))
        }
        "retinal_residual_salience" => {
            // PER-AREA RESIDUAL SALIENCE ON THE EVENT STREAM (Rung 4 of the
            // photon-eye migration). Salience is computed event-natively as the
            // RESIDUAL of the async onset-event stream AFTER the coherent
            // structure is explained: the salient column is the SURPRISING one,
            // whose onset motion is NOT accounted for by the DOMINANT
            // common-fate motion. compute-∝-surprise made an attention signal —
            // salience = the residual (the under-compressed). This is the
            // event-native re-expression of the RGB residual-salience result
            // (157000): egomotion ⟷ the dominant common-fate velocity `v_dom`;
            // a track's egomotion-cancelled residual ⟷ a column's departure
            // `|v_run − v_dom|` from that dominant flow.
            //
            // Input is the SAME async event stream Rung 2/3 read: `RetinalOnsetEvent`
            // (column index, own epoch); no `retinal_field` raster, no frame
            // diff, no `shape_salience` on the pixel field. Payload (identical
            // header to the carve): `[n_az, max_gap, vel_tol, k, c_0, e_0, …,
            // c_{k-1}, e_{k-1}]`.
            //
            // It: (1) reduces events to one mean epoch per firing column, sorted
            // by column; (2) SEGMENTS the sorted firing columns into maximal
            // COMMON-FATE runs (the SAME segmentation the carve uses); each run's
            // velocity `v_run = Δc/Δe` is its least-squares slope (columns per
            // epoch, the Rung-2 regression); (3) picks the DOMINANT run = the run
            // spanning the MOST firing columns (ties → most total events) — the
            // coherent background; `v_dom` is its velocity (0 when no run reaches
            // ≥2 columns: no coherent motion to cancel); (4) per firing column
            // emits `raw_salience = |v_run|` (the column's own common-fate SPEED —
            // the "swung background" reads HIGH, the FAILING signal) and
            // `residual_salience = |v_run − v_dom|` (its departure from the
            // dominant motion — the background IS the dominant motion so its
            // residual is ~0; an independent mover with a DIFFERENT velocity has
            // a large residual). `v_dom = 0` ⇒ `residual_salience == raw_salience`
            // (nothing to cancel — 157000's no-egomotion identity, event-native).
            //
            // Output is a FIXED per-column layout of stride 3:
            //   [fired, raw_salience, residual_salience]  for each column 0..n_az.
            // A non-firing column is all-zero. The mint rule gates on fired==1 so
            // a per-column graph rule (Rung-1/2/3 house style) mints exactly one
            // `RetinalSalience` per firing column. This is 1-D (an azimuth strip):
            // a TRUE 2-D salience map needs the retina extended to elevation
            // columns — a named follow-on, not this kernel.
            const STRIDE: usize = 3;
            let xs = numeric_values(payload)?;
            if xs.len() < 4 {
                return Err("retinal_residual_salience payload missing header".into());
            }
            let n_az = xs[0].max(0.0) as usize;
            let max_gap = xs[1].max(1.0);
            let vel_tol = xs[2].max(0.0);
            let k = xs[3].max(0.0) as usize;
            if xs.len() != 4 + 2 * k {
                return Err("retinal_residual_salience payload length mismatch".into());
            }
            let mut out = vec![0.0f64; n_az * STRIDE];
            // Reduce events to one MEAN epoch (and event count) per firing
            // column. Sorted by column (BTreeMap).
            let mut sum: std::collections::BTreeMap<i64, (f64, f64)> =
                std::collections::BTreeMap::new();
            for i in 0..k {
                let c = xs[4 + 2 * i];
                let e = xs[5 + 2 * i];
                let ci = c.round() as i64;
                if ci < 0 || ci as usize >= n_az {
                    continue;
                }
                let entry = sum.entry(ci).or_insert((0.0, 0.0));
                entry.0 += e;
                entry.1 += 1.0;
            }
            // (column, mean_epoch, n_events) per firing column.
            let cols: Vec<(f64, f64, f64)> = sum
                .into_iter()
                .map(|(c, (se, ne))| (c as f64, se / ne, ne))
                .collect();
            let m = cols.len();
            // Segment the sorted firing columns into maximal COMMON-FATE runs
            // (identical rule to `retinal_common_fate_carve`), and record for
            // each run its velocity `v_run` plus its member column range and
            // event total, so the dominant run can be chosen.
            struct Run {
                lo: usize, // start index into cols
                hi: usize, // end index into cols (inclusive)
                v: f64,    // fitted velocity (columns per epoch); 0 if degenerate
                n_cols: usize,
                n_events: f64,
            }
            let mut runs: Vec<Run> = Vec::new();
            let mut i = 0usize;
            while i < m {
                let start = i;
                let mut ref_v: Option<f64> = None;
                while i + 1 < m {
                    let dc = cols[i + 1].0 - cols[i].0;
                    let de = cols[i + 1].1 - cols[i].1;
                    if dc > max_gap || de == 0.0 {
                        break;
                    }
                    let v = dc / de;
                    match ref_v {
                        None => ref_v = Some(v),
                        Some(rv) => {
                            if (v > 0.0) != (rv > 0.0) {
                                break; // sign flip = different common fate
                            }
                            let rel = (v - rv).abs() / (rv.abs() + 1e-9);
                            if rel > vel_tol {
                                break; // velocity jump = different common fate
                            }
                        }
                    }
                    i += 1;
                }
                let run = &cols[start..=i];
                let rn = run.len();
                let (mut sc, mut se, mut nev) = (0.0, 0.0, 0.0);
                for &(c, e, ne) in run {
                    sc += c;
                    se += e;
                    nev += ne;
                }
                let (mc, me) = (sc / rn as f64, se / rn as f64);
                let (mut s_ee, mut s_ec) = (0.0, 0.0);
                for &(c, e, _ne) in run {
                    let (dc, de) = (c - mc, e - me);
                    s_ee += de * de;
                    s_ec += de * dc;
                }
                // Velocity = least-squares slope Δc/Δe (columns per epoch); a
                // single-column run or zero temporal spread has no velocity.
                let v = if rn >= 2 && s_ee > 0.0 {
                    s_ec / s_ee
                } else {
                    0.0
                };
                runs.push(Run {
                    lo: start,
                    hi: i,
                    v,
                    n_cols: rn,
                    n_events: nev,
                });
                i += 1;
            }
            // DOMINANT run = the run spanning the MOST columns (ties → most total
            // events) — the coherent background. `v_dom = 0` when no run reaches
            // ≥2 columns (no coherent motion to cancel; residual == raw).
            let mut v_dom = 0.0;
            let mut best: Option<(usize, f64)> = None; // (n_cols, n_events)
            for r in &runs {
                if r.n_cols < 2 {
                    continue;
                }
                let key = (r.n_cols, r.n_events);
                if best.map_or(true, |b| key > b) {
                    best = Some(key);
                    v_dom = r.v;
                }
            }
            // Per firing column: raw = |v_run| (own common-fate speed);
            // residual = |v_run − v_dom| (departure from the dominant motion).
            for r in &runs {
                for idx in r.lo..=r.hi {
                    let c = cols[idx].0.round() as usize;
                    if c >= n_az {
                        continue;
                    }
                    let base = c * STRIDE;
                    out[base] = 1.0; // fired
                    out[base + 1] = r.v.abs();
                    out[base + 2] = (r.v - v_dom).abs();
                }
            }
            Ok(Value::Tuple(Arc::new(
                out.into_iter().map(Value::Float).collect(),
            )))
        }
        "retinal_common_fate_carve_2d" => {
            // ASYNC COMMON-FATE CARVE ON A 2-D az×el RETINA (the 2-D expansion of
            // Rung 3). Rungs 1-4 are 1-D because the photon eye is a 1-D azimuth
            // strip (elevation collapsed). Here the retina is a 2-D
            // azimuth×elevation cell sheet: each onset event carries `(col, row)`,
            // and objects are CARVED as 2-D connected components of firing cells
            // sharing a coherent motion — the event-native 2-D replacement for the
            // 1-D `retinal_common_fate_carve`. Input is the SAME async event stream
            // Rung 2/3 read (`RetinalOnsetEvent`), now `(col, row, own-epoch)`; no
            // `retinal_field` raster, no frame diff. Payload:
            // `[n_az, n_el, max_gap, vel_tol, k, c_0, r_0, e_0, …, c_{k-1}, r_{k-1},
            //  e_{k-1}]`.
            //
            // THE 2-D CAPABILITY (falsifiable): two objects at the SAME azimuth but
            // DIFFERENT elevation (an elevation gap between them) are ONE azimuth
            // span to the 1-D carve — which collapses elevation — and TWO distinct
            // 2-D connected components here, separated at their correct `(az, el)`.
            //
            // It: (1) reduces events to one MEAN epoch per firing cell `(col, row)`;
            // (2) groups firing cells into maximal 8-connected COMPONENTS
            // (Chebyshev-1 adjacency in the `(col, row)` grid — a spatial gap in
            // azimuth OR elevation separates components); (3) fits each component's
            // 2-D motion by least squares (`col` on epoch and `row` on epoch),
            // reporting `direction = sign(col-slope)`, `speed = |2-D velocity|`,
            // `coherence = |Pearson r|` of the axis with the larger spatial spread
            // (the dominant motion axis; 0 when a component has no spatial or no
            // temporal spread — a static flash / a scrambled cloud is incoherent).
            //
            // Output is a FIXED per-cell layout of stride 9 (flat index
            // `f = row*n_az + col`):
            //   [is_group_start, col_min, col_max, row_min, row_max,
            //    direction, speed, coherence, n_events]  for each cell.
            // Each component's block is written at its ANCHOR cell — the member with
            // the smallest flat index (row-major top-left) — every other cell zero.
            // The mint rule gates on coherence / n_events (thresholds held as DATA
            // on a params node) so an incoherent component carves nothing.
            //
            // HONEST SCOPE: components are split by 2-D SPATIAL connectivity +
            // coherence gating. Splitting two SPATIALLY-TOUCHING objects of
            // DIFFERENT common fate (a velocity discontinuity inside one connected
            // blob) is a named follow-on, as is 2-D motion / 2-D salience.
            const STRIDE: usize = 9;
            let xs = numeric_values(payload)?;
            if xs.len() < 5 {
                return Err("retinal_common_fate_carve_2d payload missing header".into());
            }
            let n_az = xs[0].max(0.0) as usize;
            let n_el = xs[1].max(0.0) as usize;
            let _max_gap = xs[2].max(1.0); // reserved; connectivity is Chebyshev-1
            let _vel_tol = xs[3].max(0.0); // reserved for velocity-split follow-on
            let k = xs[4].max(0.0) as usize;
            if xs.len() != 5 + 3 * k {
                return Err("retinal_common_fate_carve_2d payload length mismatch".into());
            }
            let n_cells = n_az.saturating_mul(n_el);
            let mut out = vec![0.0f64; n_cells * STRIDE];
            // Reduce events to one MEAN epoch per firing cell (col, row). Keyed by
            // flat index so the map is deterministic and row-major ordered.
            let mut sum: std::collections::BTreeMap<i64, (f64, f64)> =
                std::collections::BTreeMap::new();
            for i in 0..k {
                let c = xs[5 + 3 * i];
                let r = xs[6 + 3 * i];
                let e = xs[7 + 3 * i];
                let ci = c.round() as i64;
                let ri = r.round() as i64;
                if ci < 0 || ci as usize >= n_az || ri < 0 || ri as usize >= n_el {
                    continue;
                }
                let flat = ri * n_az as i64 + ci;
                let entry = sum.entry(flat).or_insert((0.0, 0.0));
                entry.0 += e;
                entry.1 += 1.0;
            }
            // Firing cells: (flat_index, col, row, mean_epoch), row-major sorted.
            let cells: Vec<(i64, f64, f64, f64)> = sum
                .into_iter()
                .map(|(flat, (se, ne))| {
                    let col = (flat % n_az as i64) as f64;
                    let row = (flat / n_az as i64) as f64;
                    (flat, col, row, se / ne)
                })
                .collect();
            let m = cells.len();
            // Membership lookup: flat index -> position in `cells`.
            let mut pos: FxHashMap<i64, usize> = FxHashMap::default();
            for (idx, &(flat, _, _, _)) in cells.iter().enumerate() {
                pos.insert(flat, idx);
            }
            // 8-connected components (Chebyshev-1 adjacency) over firing cells, by
            // BFS. A spatial gap in azimuth OR elevation separates components — the
            // 2-D capability the 1-D azimuth strip cannot express.
            let mut comp = vec![usize::MAX; m];
            let mut n_comp = 0usize;
            let mut queue: VecDeque<usize> = VecDeque::new();
            for seed in 0..m {
                if comp[seed] != usize::MAX {
                    continue;
                }
                comp[seed] = n_comp;
                queue.push_back(seed);
                while let Some(cur) = queue.pop_front() {
                    let (_flat, cc, rc, _e) = cells[cur];
                    let cc = cc as i64;
                    let rc = rc as i64;
                    for dr in -1..=1i64 {
                        for dc in -1..=1i64 {
                            if dr == 0 && dc == 0 {
                                continue;
                            }
                            let nr = rc + dr;
                            let nc = cc + dc;
                            if nr < 0 || nr as usize >= n_el || nc < 0 || nc as usize >= n_az {
                                continue;
                            }
                            let nflat = nr * n_az as i64 + nc;
                            if let Some(&nidx) = pos.get(&nflat) {
                                if comp[nidx] == usize::MAX {
                                    comp[nidx] = n_comp;
                                    queue.push_back(nidx);
                                }
                            }
                        }
                    }
                }
                n_comp += 1;
            }
            // Fit each component's 2-D motion and write its block at its anchor cell
            // (smallest flat index — row-major top-left member).
            for g in 0..n_comp {
                let members: Vec<usize> = (0..m).filter(|&i| comp[i] == g).collect();
                let rn = members.len();
                let (mut sc, mut sr, mut se) = (0.0, 0.0, 0.0);
                let (mut col_min, mut col_max) = (f64::INFINITY, f64::NEG_INFINITY);
                let (mut row_min, mut row_max) = (f64::INFINITY, f64::NEG_INFINITY);
                let mut anchor_flat = i64::MAX;
                for &i in &members {
                    let (flat, c, r, e) = cells[i];
                    sc += c;
                    sr += r;
                    se += e;
                    col_min = col_min.min(c);
                    col_max = col_max.max(c);
                    row_min = row_min.min(r);
                    row_max = row_max.max(r);
                    anchor_flat = anchor_flat.min(flat);
                }
                let (mc, mr, me) = (sc / rn as f64, sr / rn as f64, se / rn as f64);
                let (mut s_ee, mut s_cc, mut s_rr, mut s_ec, mut s_er) = (0.0, 0.0, 0.0, 0.0, 0.0);
                for &i in &members {
                    let (_flat, c, r, e) = cells[i];
                    let (dc, dr, de) = (c - mc, r - mr, e - me);
                    s_ee += de * de;
                    s_cc += dc * dc;
                    s_rr += dr * dr;
                    s_ec += de * dc;
                    s_er += de * dr;
                }
                // Per-axis slopes (position on epoch); 2-D speed is their norm.
                let (mut dir, mut speed, mut coherence) = (0.0, 0.0, 0.0);
                if rn >= 2 && s_ee > 0.0 && (s_cc > 0.0 || s_rr > 0.0) {
                    let slope_c = s_ec / s_ee;
                    let slope_r = s_er / s_ee;
                    speed = (slope_c * slope_c + slope_r * slope_r).sqrt();
                    dir = if slope_c > 0.0 {
                        1.0
                    } else if slope_c < 0.0 {
                        -1.0
                    } else {
                        0.0
                    };
                    // Coherence on the axis with the larger spatial spread — the
                    // dominant motion axis; noiseless sweeps give |r| = 1.
                    coherence = if s_cc >= s_rr {
                        if s_cc > 0.0 {
                            (s_ec / (s_ee * s_cc).sqrt()).abs()
                        } else {
                            0.0
                        }
                    } else if s_rr > 0.0 {
                        (s_er / (s_ee * s_rr).sqrt()).abs()
                    } else {
                        0.0
                    };
                }
                let anchor = anchor_flat as usize;
                let base = anchor * STRIDE;
                out[base] = 1.0; // is_group_start
                out[base + 1] = col_min;
                out[base + 2] = col_max;
                out[base + 3] = row_min;
                out[base + 4] = row_max;
                out[base + 5] = dir;
                out[base + 6] = speed;
                out[base + 7] = coherence;
                out[base + 8] = rn as f64;
            }
            Ok(Value::Tuple(Arc::new(
                out.into_iter().map(Value::Float).collect(),
            )))
        }
        "retinal_residual_salience_2d" => {
            // PER-AREA RESIDUAL SALIENCE ON A 2-D az×el RETINA — the 2-D
            // expansion of `retinal_residual_salience` (the named 166000
            // follow-on). Salience is the RESIDUAL of the async onset-event
            // stream AFTER the dominant coherent structure is explained — the
            // surprising cell whose motion is NOT accounted for by the DOMINANT
            // common-fate motion. The 1-D kernel reads azimuth only, so a
            // spatially-separated PURELY-VERTICAL mover contributes NOTHING to
            // its azimuth-only velocity and is ranked at the BACKGROUND level —
            // MISSED. Here events carry `(col, row, epoch)`; the residual is the
            // 2-D VECTOR departure `|v_comp − v_dom|` per firing cell, so a
            // vertical mover against an azimuth-sweeping background reads
            // `|(0, v_el) − (v_az, 0)| = |(v_az, v_el)|` ≫ the background's 0 —
            // RANKED. NO new DSL Term enum variant.
            //
            // Payload (identical header to the 2-D carve):
            //   `[n_az, n_el, max_gap, vel_tol, k, c, r, e, …]`.
            // It: (1) reduces events to one mean epoch per firing cell
            // `(col, row)`; (2) groups firing cells into maximal 8-connected
            // COMPONENTS (the SAME Chebyshev-1 grouping the 2-D carve uses);
            // (3) fits each component's 2-D velocity `(v_az, v_el)` by least
            // squares; (4) picks the DOMINANT component = the one spanning the
            // MOST cells (ties → most events) as the coherent background, its
            // velocity `v_dom` (0 when no component reaches ≥2 cells: no coherent
            // motion to cancel); (5) per firing cell emits stride-3
            //   [fired, raw_salience = |v_comp|,
            //    residual_salience = |v_comp − v_dom|]
            // at flat index `f = row*n_az + col`. `v_dom = 0` ⇒ residual == raw
            // (nothing to cancel — 157000's no-egomotion identity, event-native,
            // now 2-D). A non-firing cell is all-zero; the mint rule gates on
            // fired==1 so one `RetinalSalience` per firing cell is minted.
            const STRIDE: usize = 3;
            let xs = numeric_values(payload)?;
            if xs.len() < 5 {
                return Err("retinal_residual_salience_2d payload missing header".into());
            }
            let n_az = xs[0].max(0.0) as usize;
            let n_el = xs[1].max(0.0) as usize;
            let _max_gap = xs[2].max(1.0); // reserved; connectivity is Chebyshev-1
            let _vel_tol = xs[3].max(0.0); // reserved for velocity-split follow-on
            let k = xs[4].max(0.0) as usize;
            if xs.len() != 5 + 3 * k {
                return Err("retinal_residual_salience_2d payload length mismatch".into());
            }
            let n_cells = n_az.saturating_mul(n_el);
            let mut out = vec![0.0f64; n_cells * STRIDE];
            // Reduce events to one MEAN epoch per firing cell (col, row), keyed
            // by flat index so the map is deterministic and row-major ordered.
            let mut sum: std::collections::BTreeMap<i64, (f64, f64)> =
                std::collections::BTreeMap::new();
            for i in 0..k {
                let c = xs[5 + 3 * i];
                let r = xs[6 + 3 * i];
                let e = xs[7 + 3 * i];
                let ci = c.round() as i64;
                let ri = r.round() as i64;
                if ci < 0 || ci as usize >= n_az || ri < 0 || ri as usize >= n_el {
                    continue;
                }
                let flat = ri * n_az as i64 + ci;
                let entry = sum.entry(flat).or_insert((0.0, 0.0));
                entry.0 += e;
                entry.1 += 1.0;
            }
            // Firing cells: (flat_index, col, row, mean_epoch), row-major sorted.
            let cells: Vec<(i64, f64, f64, f64)> = sum
                .into_iter()
                .map(|(flat, (se, ne))| {
                    let col = (flat % n_az as i64) as f64;
                    let row = (flat / n_az as i64) as f64;
                    (flat, col, row, se / ne)
                })
                .collect();
            let m = cells.len();
            // Membership lookup: flat index -> position in `cells`.
            let mut pos: FxHashMap<i64, usize> = FxHashMap::default();
            for (idx, &(flat, _, _, _)) in cells.iter().enumerate() {
                pos.insert(flat, idx);
            }
            // 8-connected components (Chebyshev-1) over firing cells, by BFS —
            // the SAME grouping the 2-D carve uses.
            let mut comp = vec![usize::MAX; m];
            let mut n_comp = 0usize;
            let mut queue: VecDeque<usize> = VecDeque::new();
            for seed in 0..m {
                if comp[seed] != usize::MAX {
                    continue;
                }
                comp[seed] = n_comp;
                queue.push_back(seed);
                while let Some(cur) = queue.pop_front() {
                    let (_flat, cc, rc, _e) = cells[cur];
                    let cc = cc as i64;
                    let rc = rc as i64;
                    for dr in -1..=1i64 {
                        for dc in -1..=1i64 {
                            if dr == 0 && dc == 0 {
                                continue;
                            }
                            let nr = rc + dr;
                            let nc = cc + dc;
                            if nr < 0 || nr as usize >= n_el || nc < 0 || nc as usize >= n_az {
                                continue;
                            }
                            let nflat = nr * n_az as i64 + nc;
                            if let Some(&nidx) = pos.get(&nflat) {
                                if comp[nidx] == usize::MAX {
                                    comp[nidx] = n_comp;
                                    queue.push_back(nidx);
                                }
                            }
                        }
                    }
                }
                n_comp += 1;
            }
            // Fit each component's 2-D velocity (col on epoch, row on epoch) and
            // record its member cell count + event total so the dominant
            // component (coherent background) can be chosen.
            struct Comp {
                members: Vec<usize>,
                v_az: f64,
                v_el: f64,
                n_cells: usize,
                n_events: f64,
            }
            let mut comps: Vec<Comp> = Vec::with_capacity(n_comp);
            for g in 0..n_comp {
                let members: Vec<usize> = (0..m).filter(|&i| comp[i] == g).collect();
                let rn = members.len();
                let (mut sc, mut sr, mut se, mut nev) = (0.0, 0.0, 0.0, 0.0);
                for &i in &members {
                    let (_flat, c, r, e) = cells[i];
                    sc += c;
                    sr += r;
                    se += e;
                    nev += 1.0;
                }
                let (mc, mr, me) = (sc / rn as f64, sr / rn as f64, se / rn as f64);
                let (mut s_ee, mut s_ec, mut s_er) = (0.0, 0.0, 0.0);
                for &i in &members {
                    let (_flat, c, r, e) = cells[i];
                    let (dc, dr, de) = (c - mc, r - mr, e - me);
                    s_ee += de * de;
                    s_ec += de * dc;
                    s_er += de * dr;
                }
                let (v_az, v_el) = if rn >= 2 && s_ee > 0.0 {
                    (s_ec / s_ee, s_er / s_ee)
                } else {
                    (0.0, 0.0)
                };
                comps.push(Comp {
                    members,
                    v_az,
                    v_el,
                    n_cells: rn,
                    n_events: nev,
                });
            }
            // DOMINANT component = the one spanning the MOST cells (ties → most
            // total events) — the coherent background. `v_dom = 0` when no
            // component reaches ≥2 cells (residual == raw).
            let (mut vdom_az, mut vdom_el) = (0.0, 0.0);
            let mut best: Option<(usize, f64)> = None; // (n_cells, n_events)
            for cmp in &comps {
                if cmp.n_cells < 2 {
                    continue;
                }
                let key = (cmp.n_cells, cmp.n_events);
                if best.map_or(true, |b| key > b) {
                    best = Some(key);
                    vdom_az = cmp.v_az;
                    vdom_el = cmp.v_el;
                }
            }
            // Per firing cell: raw = |v_comp| (its own 2-D common-fate speed);
            // residual = |v_comp − v_dom| (2-D vector departure from the
            // dominant motion).
            for cmp in &comps {
                let raw = (cmp.v_az * cmp.v_az + cmp.v_el * cmp.v_el).sqrt();
                let dvx = cmp.v_az - vdom_az;
                let dvy = cmp.v_el - vdom_el;
                let resid = (dvx * dvx + dvy * dvy).sqrt();
                for &idx in &cmp.members {
                    let flat = cells[idx].0 as usize;
                    if flat >= n_cells {
                        continue;
                    }
                    let base = flat * STRIDE;
                    out[base] = 1.0; // fired
                    out[base + 1] = raw;
                    out[base + 2] = resid;
                }
            }
            Ok(Value::Tuple(Arc::new(
                out.into_iter().map(Value::Float).collect(),
            )))
        }
        "multilook_superres" => {
            // MULTI-LOOK DE-ALIASING SUPER-RESOLUTION (Rung 5 of the photon-eye
            // migration — TWO EYES). Two low-resolution eyes offset by a KNOWN
            // sub-receptor amount sample ONE flat textured surface; their offset
            // samples interleave at sub-receptor lattice positions, carrying the
            // PHASE that DE-ALIASES spatial frequencies above either eye's
            // receptor-Nyquist that NEITHER eye can represent alone (Tsai-Huang
            // microscanning; NOT stereo — the surface is flat). This is the
            // FUSION decision, graph-native: a band-limited least-squares
            // reconstruction of the underlying field from samples at known
            // nonuniform positions, through a SINGLE fixed operator — the only
            // independent variable across arms is the SAMPLES (which eye / what
            // offset). A small ridge damps directions the samples do not
            // constrain: with a genuine sub-receptor OFFSET the interleaved
            // positions make the high-harmonic columns full-rank (they are
            // recovered); with ZERO offset the two eyes' positions coincide, the
            // high-harmonic columns are rank-deficient, and the ridge pulls them
            // to ~0 — so the zero-offset control shows NO super-resolution gain.
            // The offset is thus LOAD-BEARING through the conditioning, not
            // bolted on. NO new DSL Term enum variant — a pure CognitiveTask
            // kind. SPACE-OFFSET == TIME-OFFSET: the identical kernel serves the
            // async two-clock TEMPORAL super-resolution win when the positions
            // are TIMES rather than azimuths.
            //
            // Payload: `[n_fine, P, ridge, K_max, m, x_0, y_0, …, x_{m-1}, y_{m-1}]`
            //   n_fine : number of fine-grid reconstruction points (evaluated at
            //            x_j = j * P / n_fine, j = 0..n_fine-1);
            //   P      : the period of the (periodic) field;
            //   ridge  : the least-squares ridge λ (damps unconstrained modes);
            //   K_max  : highest reconstructed harmonic (basis is
            //            [1, cos k·, sin k·] for k = 1..K_max → K = 1 + 2·K_max);
            //   m      : number of (position, value) sample pairs.
            // Output: Tuple `[n_fine, recon_0, …, recon_{n_fine-1}]`.
            let xs = numeric_values(payload)?;
            if xs.len() < 5 {
                return Err("multilook_superres payload too short".into());
            }
            let n_fine = xs[0].max(0.0) as usize;
            let period = xs[1];
            let ridge = xs[2].max(0.0);
            let k_max = xs[3].max(0.0) as usize;
            let m = xs[4].max(0.0) as usize;
            if period.abs() < 1e-12 {
                return Err("multilook_superres period must be non-zero".into());
            }
            if xs.len() != 5 + 2 * m {
                return Err("multilook_superres payload length mismatch".into());
            }
            let k = 1 + 2 * k_max;
            // Basis row φ(x) = [1, cos(2π·1·x/P), sin(2π·1·x/P), …].
            let basis = |x: f64| -> Vec<f64> {
                let mut row = Vec::with_capacity(k);
                row.push(1.0);
                for h in 1..=k_max {
                    let w = 2.0 * std::f64::consts::PI * (h as f64) * x / period;
                    row.push(w.cos());
                    row.push(w.sin());
                }
                row
            };
            // Normal equations: (ΦᵀΦ + ridge·I) c = Φᵀ y.
            let mut mat = vec![vec![0.0f64; k]; k];
            let mut rhs = vec![0.0f64; k];
            for i in 0..m {
                let x = xs[5 + 2 * i];
                let y = xs[6 + 2 * i];
                let phi = basis(x);
                for a in 0..k {
                    rhs[a] += phi[a] * y;
                    for b in 0..k {
                        mat[a][b] += phi[a] * phi[b];
                    }
                }
            }
            for a in 0..k {
                mat[a][a] += ridge;
            }
            let coeffs = gauss_solve(mat, rhs)
                .ok_or_else(|| "multilook_superres normal matrix is singular".to_string())?;
            let mut out = Vec::with_capacity(1 + n_fine);
            out.push(Value::Float(n_fine as f64));
            for j in 0..n_fine {
                let x = (j as f64) * period / (n_fine as f64);
                let phi = basis(x);
                let mut v = 0.0;
                for a in 0..k {
                    v += phi[a] * coeffs[a];
                }
                out.push(Value::Float(v));
            }
            Ok(Value::Tuple(Arc::new(out.into())))
        }
        _ => Err(format!("unknown native cognitive kernel: {kind}")),
    }
}

/// Dense linear solve `A x = b` by Gaussian elimination with partial pivoting.
/// Returns None on a (numerically) singular system. Small K only — the
/// super-resolution normal matrix is `(1 + 2·K_max)²`, a few tens of rows.
fn gauss_solve(mut a: Vec<Vec<f64>>, mut b: Vec<f64>) -> Option<Vec<f64>> {
    let n = b.len();
    if a.len() != n || a.iter().any(|row| row.len() != n) {
        return None;
    }
    for col in 0..n {
        // Partial pivot: largest-magnitude entry in this column at/below col.
        let mut piv = col;
        let mut best = a[col][col].abs();
        for r in (col + 1)..n {
            let v = a[r][col].abs();
            if v > best {
                best = v;
                piv = r;
            }
        }
        if best < 1e-12 {
            return None;
        }
        a.swap(col, piv);
        b.swap(col, piv);
        let pivot = a[col][col];
        for r in (col + 1)..n {
            let factor = a[r][col] / pivot;
            if factor == 0.0 {
                continue;
            }
            for c in col..n {
                a[r][c] -= factor * a[col][c];
            }
            b[r] -= factor * b[col];
        }
    }
    // Back-substitution.
    let mut x = vec![0.0f64; n];
    for row in (0..n).rev() {
        let mut acc = b[row];
        for c in (row + 1)..n {
            acc -= a[row][c] * x[c];
        }
        x[row] = acc / a[row][row];
    }
    Some(x)
}

fn read_i64(attrs: &crate::graph::Attrs, key: Sym, default: i64) -> i64 {
    match attrs.get(&key) {
        Some(Value::Int(v)) => *v,
        Some(Value::Float(v)) => *v as i64,
        _ => default,
    }
}

fn read_str<'a>(
    substrate: &'a Substrate,
    attrs: &'a crate::graph::Attrs,
    key: Sym,
) -> Option<&'a str> {
    match attrs.get(&key) {
        Some(Value::Str(v)) => Some(substrate.interner.resolve(*v)),
        _ => None,
    }
}

/// Snapshot the strict graph-authored continuation lease for a process-bound
/// task. Tasks without either process edge predate supervision and retain
/// their legacy behavior. Once a task opts in through an edge, malformed or
/// ambiguous supervision state fails closed and the task remains requested.
fn snapshot_process_lease(
    substrate: &mut Substrate,
    task: NodeID,
) -> Result<Option<ProcessLeaseSnapshot>, ()> {
    let continues = substrate.interner.intern("continues_cognitive_process");
    let checks = substrate.interner.intern("checks_cognitive_process");
    let governed_by = substrate
        .interner
        .intern("governed_by_cognitive_supervision_policy");
    let policy_type = substrate.interner.intern("CognitiveSupervisionPolicy");
    let enabled_key = substrate.interner.intern("enabled");
    let epoch_key = substrate.interner.intern("cognitive_epoch");
    let authority_key = substrate.interner.intern("continuation_authority");
    let generation_key = substrate.interner.intern("lease_generation");
    let renew_key = substrate.interner.intern("renew_before_epoch");

    let continuation_processes = substrate.graph.neighbours(task, Some(continues));
    let checkin_processes = substrate.graph.neighbours(task, Some(checks));
    if continuation_processes.is_empty() && checkin_processes.is_empty() {
        return Ok(None);
    }
    let (process, is_checkin) = match (
        continuation_processes.as_slice(),
        checkin_processes.as_slice(),
    ) {
        ([process], []) => (*process, false),
        ([], [process]) => (*process, true),
        _ => return Err(()),
    };
    if !substrate.graph.has_node(process) {
        return Err(());
    }
    let policies = substrate.graph.neighbours(process, Some(governed_by));
    if policies.len() != 1 {
        return Err(());
    }
    let policy = policies[0];
    if !substrate.graph.has_node(policy) {
        return Err(());
    }
    let policy_node = substrate.graph.node(policy);
    if policy_node.type_ != policy_type
        || policy_node.attrs.get(&enabled_key) != Some(&Value::Int(1))
    {
        return Err(());
    }
    let policy_attrs = &policy_node.attrs;
    let Some(Value::Int(epoch)) = policy_attrs.get(&epoch_key) else {
        return Err(());
    };
    let process_attrs = &substrate.graph.node(process).attrs;
    let Some(Value::Int(authority)) = process_attrs.get(&authority_key) else {
        return Err(());
    };
    let Some(Value::Int(process_generation)) = process_attrs.get(&generation_key) else {
        return Err(());
    };
    let Some(Value::Int(renew_before)) = process_attrs.get(&renew_key) else {
        return Err(());
    };
    let Some(Value::Int(task_generation)) = substrate.graph.node(task).attrs.get(&generation_key)
    else {
        return Err(());
    };
    if task_generation != process_generation {
        return Err(());
    }
    let held = *authority == 0 || *epoch >= *renew_before;
    if (is_checkin && !held) || (!is_checkin && (*authority != 1 || *epoch >= *renew_before)) {
        return Err(());
    }
    Ok(Some(ProcessLeaseSnapshot {
        process,
        policy,
        generation: *process_generation,
        is_checkin,
    }))
}

/// Revalidate the exact lease snapshot before folding an asynchronous result.
/// A withdrawal, renewal (generation change), expiry, edge retarget, or policy
/// ambiguity makes the journal stale. Check-in tasks are the sole exception:
/// they remain lawful only while that same process is held.
fn process_lease_is_current(
    substrate: &mut Substrate,
    task: NodeID,
    snapshot: &ProcessLeaseSnapshot,
) -> bool {
    let continues = substrate.interner.intern("continues_cognitive_process");
    let checks = substrate.interner.intern("checks_cognitive_process");
    let governed_by = substrate
        .interner
        .intern("governed_by_cognitive_supervision_policy");
    let policy_type = substrate.interner.intern("CognitiveSupervisionPolicy");
    let enabled_key = substrate.interner.intern("enabled");
    let epoch_key = substrate.interner.intern("cognitive_epoch");
    let authority_key = substrate.interner.intern("continuation_authority");
    let generation_key = substrate.interner.intern("lease_generation");
    let renew_key = substrate.interner.intern("renew_before_epoch");

    if !substrate.graph.has_node(snapshot.process) || !substrate.graph.has_node(snapshot.policy) {
        return false;
    }
    let expected_edge = if snapshot.is_checkin {
        checks
    } else {
        continues
    };
    let other_edge = if snapshot.is_checkin {
        continues
    } else {
        checks
    };
    if substrate.graph.neighbours(task, Some(expected_edge)) != vec![snapshot.process]
        || !substrate
            .graph
            .neighbours(task, Some(other_edge))
            .is_empty()
        || substrate
            .graph
            .neighbours(snapshot.process, Some(governed_by))
            != vec![snapshot.policy]
    {
        return false;
    }
    let policy_node = substrate.graph.node(snapshot.policy);
    if policy_node.type_ != policy_type
        || policy_node.attrs.get(&enabled_key) != Some(&Value::Int(1))
    {
        return false;
    }
    let policy_attrs = &policy_node.attrs;
    let Some(Value::Int(epoch)) = policy_attrs.get(&epoch_key) else {
        return false;
    };
    let process_attrs = &substrate.graph.node(snapshot.process).attrs;
    let Some(Value::Int(authority)) = process_attrs.get(&authority_key) else {
        return false;
    };
    let Some(Value::Int(generation)) = process_attrs.get(&generation_key) else {
        return false;
    };
    let Some(Value::Int(renew_before)) = process_attrs.get(&renew_key) else {
        return false;
    };
    let task_generation = substrate.graph.node(task).attrs.get(&generation_key);
    if *generation != snapshot.generation
        || task_generation != Some(&Value::Int(snapshot.generation))
    {
        return false;
    }
    let held = *authority == 0 || *epoch >= *renew_before;
    if snapshot.is_checkin {
        held
    } else {
        *authority == 1 && *epoch < *renew_before
    }
}

/// Snapshot immutable task payloads and mark them running. Graph lock required.
fn prepare_requested_matching(
    substrate: &mut Substrate,
    n_workers: usize,
    execution_class: Option<Sym>,
) -> PreparedTaskBatch {
    let started = Instant::now();
    let task_t = substrate.interner.intern("CognitiveTask");
    let status_k = substrate.interner.intern("status");
    let kind_k = substrate.interner.intern("kind");
    let payload_k = substrate.interner.intern("payload");
    let input_epoch_k = substrate.interner.intern("input_epoch");
    let deadline_epoch_k = substrate.interner.intern("deadline_epoch");
    let logical_time_k = substrate.interner.intern("logical_time");
    let area_k = substrate.interner.intern("area");
    let execution_class_k = substrate.interner.intern("execution_class");
    let about_context = substrate.interner.intern("about_context");
    let validated_by_clock = substrate.interner.intern("validated_by_clock");
    let requested_s = substrate.interner.intern("requested");
    let running_s = substrate.interner.intern("running");
    let global_s = substrate.interner.intern("global");

    let mut tasks = Vec::new();
    for node in substrate.graph.nodes_of_type(task_t) {
        let candidate = {
            let attrs = &substrate.graph.node(node).attrs;
            if attrs.get(&status_k) != Some(&Value::Str(requested_s)) {
                continue;
            }
            if let Some(execution_class) = execution_class {
                if attrs.get(&execution_class_k) != Some(&Value::Str(execution_class)) {
                    continue;
                }
            }
            let Some(kind) = read_str(substrate, attrs, kind_k) else {
                continue;
            };
            let contexts = substrate.graph.neighbours(node, Some(about_context));
            let clocks = substrate.graph.neighbours(node, Some(validated_by_clock));
            let has_provenance =
                !contexts.is_empty() || !clocks.is_empty() || attrs.contains_key(&deadline_epoch_k);
            (
                kind.to_owned(),
                attrs.get(&payload_k).cloned().unwrap_or(Value::None),
                read_i64(attrs, input_epoch_k, 0),
                attrs
                    .get(&deadline_epoch_k)
                    .map(|_| read_i64(attrs, deadline_epoch_k, 0)),
                read_i64(attrs, logical_time_k, 0),
                match attrs.get(&area_k) {
                    Some(Value::Str(v)) => *v,
                    _ => global_s,
                },
                if contexts.len() == 1 {
                    contexts.first().copied()
                } else {
                    None
                },
                if clocks.len() == 1 {
                    clocks.first().copied()
                } else {
                    None
                },
                has_provenance
                    && (contexts.len() != 1 || (!clocks.is_empty() && clocks.len() != 1)),
            )
        };
        let Ok(process_lease) = snapshot_process_lease(substrate, node) else {
            continue;
        };
        tasks.push(TaskSpec {
            node,
            kind: candidate.0,
            payload: candidate.1,
            input_epoch: candidate.2,
            deadline_epoch: candidate.3,
            logical_time: candidate.4,
            area: candidate.5,
            context: candidate.6,
            clock: candidate.7,
            invalid_provenance: candidate.8,
            process_lease,
        });
    }
    tasks.sort_by_key(|t| (t.logical_time, t.area.0, t.node.0));
    let area_t = substrate.interner.intern("CognitiveArea");
    let name_k = substrate.interner.intern("name");
    let desired_k = substrate.interner.intern("desired_workers");
    let task_areas: rustc_hash::FxHashSet<Sym> = tasks.iter().map(|task| task.area).collect();
    let desired = substrate
        .graph
        .nodes_of_type(area_t)
        .into_iter()
        .filter_map(|node| {
            let attrs = &substrate.graph.node(node).attrs;
            let Some(Value::Str(name)) = attrs.get(&name_k) else {
                return None;
            };
            if !task_areas.contains(name) {
                return None;
            }
            Some(read_i64(attrs, desired_k, 1).max(1) as usize)
        })
        .max();
    let capacity = n_workers.max(1);
    let effective_workers = desired.map(|n| n.min(capacity)).unwrap_or(capacity);
    let workers_used = effective_workers.min(tasks.len().max(1));
    for task in &tasks {
        substrate.set_attr(task.node, status_k, Value::Str(running_s));
    }
    PreparedTaskBatch {
        tasks,
        workers_used,
        capacity,
        started,
    }
}

/// Snapshot every requested task. The autonomous runner uses this surface.
pub(crate) fn prepare_requested(substrate: &mut Substrate, n_workers: usize) -> PreparedTaskBatch {
    prepare_requested_matching(substrate, n_workers, None)
}

/// Resolve deployment capacity without making a cognitive decision.
///
/// An omitted capacity uses the concurrency the runtime can actually schedule.
/// A supplied value remains an exact caller capacity, which preserves the
/// one-worker reduction arm.  Graph-authored
/// ``CognitiveArea.desired_workers`` still narrows this capacity when the task
/// batch is prepared; hardware availability never chooses what to think about.
pub(crate) fn resolve_worker_capacity(requested: Option<usize>) -> usize {
    if let Some(requested) = requested {
        return requested.max(1);
    }
    std::thread::available_parallelism()
        .map(|parallelism| parallelism.get())
        .unwrap_or(1)
}

/// Snapshot one graph-authored execution class.
///
/// Explicit synchronous cycle calls use this narrower surface to preserve
/// one-call System-2 semantics without unexpectedly consuming unrelated
/// sensory tasks.
pub(crate) fn prepare_requested_class(
    substrate: &mut Substrate,
    n_workers: usize,
    execution_class: &str,
) -> PreparedTaskBatch {
    let execution_class = substrate.interner.intern(execution_class);
    prepare_requested_matching(substrate, n_workers, Some(execution_class))
}

/// Execute pure kernels. No substrate or graph lock is held.
pub(crate) fn execute_prepared(batch: PreparedTaskBatch) -> CompletedTaskBatch {
    let requested = batch.tasks.len();
    let queue = Arc::new(Mutex::new(VecDeque::from(batch.tasks)));
    let (tx, rx) = mpsc::channel();
    std::thread::scope(|scope| {
        for _ in 0..batch.workers_used {
            let queue = Arc::clone(&queue);
            let tx = tx.clone();
            scope.spawn(move || loop {
                let Some(spec) = queue.lock().expect("task queue poisoned").pop_front() else {
                    break;
                };
                let begin = Instant::now();
                let (output, error) = match execute_kernel(&spec.kind, &spec.payload) {
                    Ok(value) => (Some(value), None),
                    Err(err) => (None, Some(err)),
                };
                let _ = tx.send(TaskCompletion {
                    spec,
                    output,
                    error,
                    wall_micros: begin.elapsed().as_micros() as u64,
                });
            });
        }
    });
    drop(tx);
    let mut completed: Vec<_> = rx.into_iter().collect();
    completed.sort_by_key(|c| (c.spec.logical_time, c.spec.area.0, c.spec.node.0));
    CompletedTaskBatch {
        completions: completed,
        requested,
        workers_used: batch.workers_used,
        capacity: batch.capacity,
        started: batch.started,
    }
}

/// Epoch-validate and deterministically fold completed journals. Graph lock required.
pub(crate) fn fold_completed(
    substrate: &mut Substrate,
    batch: CompletedTaskBatch,
) -> TaskRunSummary {
    let result_t = substrate.interner.intern("TaskResult");
    let status_k = substrate.interner.intern("status");
    let input_epoch_k = substrate.interner.intern("input_epoch");
    let logical_time_k = substrate.interner.intern("logical_time");
    let area_k = substrate.interner.intern("area");
    let output_k = substrate.interner.intern("output");
    let error_k = substrate.interner.intern("error");
    let wall_k = substrate.interner.intern("wall_micros");
    let source_epoch_k = substrate.interner.intern("source_epoch");
    let has_result = substrate.interner.intern("has_result");
    let running_s = substrate.interner.intern("running");
    let done_s = substrate.interner.intern("done");
    let failed_s = substrate.interner.intern("failed");
    let stale_s = substrate.interner.intern("stale");
    let interrupted_s = substrate.interner.intern("interrupted");
    let expired_s = substrate.interner.intern("expired");
    let cancelled_s = substrate.interner.intern("cancelled");
    let retired_s = substrate.interner.intern("retired");
    let completed_s = substrate.interner.intern("completed");
    let epoch_k = substrate.interner.intern("epoch");
    let about_context = substrate.interner.intern("about_context");
    let validated_by_clock = substrate.interner.intern("validated_by_clock");
    let mut summary = TaskRunSummary {
        requested: batch.requested,
        workers_used: batch.workers_used,
        ..Default::default()
    };
    for completion in batch.completions {
        if !substrate.graph.has_node(completion.spec.node) {
            summary.stale += 1;
            continue;
        }
        let process_lease_is_current = completion
            .spec
            .process_lease
            .as_ref()
            .map_or(true, |snapshot| {
                process_lease_is_current(substrate, completion.spec.node, snapshot)
            });
        let attrs = &substrate.graph.node(completion.spec.node).attrs;
        let epoch_now = read_i64(attrs, input_epoch_k, 0);
        let still_running = attrs.get(&status_k) == Some(&Value::Str(running_s));
        let context_is_current = completion.spec.context.map_or(true, |context| {
            substrate.graph.has_node(context)
                && substrate
                    .graph
                    .neighbours(completion.spec.node, Some(about_context))
                    == vec![context]
                && read_i64(&substrate.graph.node(context).attrs, epoch_k, i64::MIN)
                    == completion.spec.input_epoch
                && !matches!(
                    substrate.graph.node(context).attrs.get(&status_k),
                    Some(Value::Str(status))
                        if *status == stale_s
                            || *status == interrupted_s
                            || *status == expired_s
                            || *status == cancelled_s
                            || *status == retired_s
                            || *status == completed_s
                )
        });
        let clock_is_current = completion.spec.clock.map_or(true, |clock| {
            substrate.graph.has_node(clock)
                && substrate
                    .graph
                    .neighbours(completion.spec.node, Some(validated_by_clock))
                    == vec![clock]
                && completion.spec.deadline_epoch.map_or(true, |deadline| {
                    read_i64(&substrate.graph.node(clock).attrs, epoch_k, i64::MAX) <= deadline
                })
        });
        let is_stale = epoch_now != completion.spec.input_epoch
            || !still_running
            || completion.spec.invalid_provenance
            || !context_is_current
            || !clock_is_current
            || !process_lease_is_current;

        let mut result_attrs = FxHashMap::default();
        result_attrs.insert(source_epoch_k, Value::Int(completion.spec.input_epoch));
        result_attrs.insert(logical_time_k, Value::Int(completion.spec.logical_time));
        result_attrs.insert(area_k, Value::Str(completion.spec.area));
        result_attrs.insert(wall_k, Value::Int(completion.wall_micros as i64));
        if is_stale {
            result_attrs.insert(status_k, Value::Str(stale_s));
            substrate.set_attr(completion.spec.node, status_k, Value::Str(stale_s));
            summary.stale += 1;
        } else if let Some(error) = completion.error {
            let error_sym = substrate.interner.intern(&error);
            result_attrs.insert(status_k, Value::Str(failed_s));
            result_attrs.insert(error_k, Value::Str(error_sym));
            substrate.set_attr(completion.spec.node, status_k, Value::Str(failed_s));
            substrate.set_attr(completion.spec.node, error_k, Value::Str(error_sym));
            summary.failed += 1;
        } else {
            result_attrs.insert(status_k, Value::Str(done_s));
            let output = completion.output.unwrap_or(Value::None);
            result_attrs.insert(output_k, output.clone());
            substrate.set_attr(completion.spec.node, status_k, Value::Str(done_s));
            substrate.set_attr(completion.spec.node, output_k, output);
            summary.completed += 1;
        }
        let result = substrate.add_node(result_t, result_attrs);
        // Task schemas are core runtime vocabulary. If a caller omitted the
        // seed, the output still lives on the task; do not leak an orphan.
        if substrate
            .add_edge(
                completion.spec.node,
                has_result,
                result,
                FxHashMap::default(),
            )
            .is_err()
        {
            substrate.remove_node(result);
        }
    }
    summary.wall_micros = batch.started.elapsed().as_micros() as u64;
    publish_area_load(substrate, batch.capacity, summary.wall_micros);
    summary
}

/// Synchronous compatibility path over the same prepare/compute/fold phases.
pub fn run_requested(substrate: &mut Substrate, n_workers: usize) -> TaskRunSummary {
    let prepared = prepare_requested(substrate, n_workers);
    let completed = execute_prepared(prepared);
    fold_completed(substrate, completed)
}

fn publish_area_load(substrate: &mut Substrate, capacity: usize, wall_micros: u64) {
    let task_t = substrate.interner.intern("CognitiveTask");
    let area_t = substrate.interner.intern("CognitiveArea");
    let load_t = substrate.interner.intern("AreaLoad");
    let status_k = substrate.interner.intern("status");
    let area_k = substrate.interner.intern("area");
    let name_k = substrate.interner.intern("name");
    let has_load = substrate.interner.intern("has_area_load");
    let pending_s = substrate.interner.intern("pending");
    let requested_s = substrate.interner.intern("requested");
    let running_s = substrate.interner.intern("running");
    let done_s = substrate.interner.intern("done");
    let failed_s = substrate.interner.intern("failed");
    let stale_s = substrate.interner.intern("stale");
    let shed_s = substrate.interner.intern("shed");

    #[derive(Default)]
    struct Counts {
        pending: i64,
        requested: i64,
        running: i64,
        completed: i64,
        failed: i64,
        stale: i64,
        shed: i64,
    }
    let mut by_area: FxHashMap<Sym, Counts> = FxHashMap::default();
    for task in substrate.graph.nodes_of_type(task_t) {
        let attrs = &substrate.graph.node(task).attrs;
        let Some(Value::Str(area)) = attrs.get(&area_k) else {
            continue;
        };
        let counts = by_area.entry(*area).or_default();
        match attrs.get(&status_k) {
            Some(Value::Str(s)) if *s == pending_s => counts.pending += 1,
            Some(Value::Str(s)) if *s == requested_s => counts.requested += 1,
            Some(Value::Str(s)) if *s == running_s => counts.running += 1,
            Some(Value::Str(s)) if *s == done_s => counts.completed += 1,
            Some(Value::Str(s)) if *s == failed_s => counts.failed += 1,
            Some(Value::Str(s)) if *s == stale_s => counts.stale += 1,
            Some(Value::Str(s)) if *s == shed_s => counts.shed += 1,
            _ => {}
        }
    }

    let queued_k = substrate.interner.intern("queued");
    let running_k = substrate.interner.intern("running");
    let completed_k = substrate.interner.intern("completed");
    let failed_k = substrate.interner.intern("failed");
    let stale_k = substrate.interner.intern("stale");
    let shed_k = substrate.interner.intern("shed");
    let capacity_k = substrate.interner.intern("capacity_workers");
    let wall_k = substrate.interner.intern("service_wall_micros");
    let conflicts_k = substrate.interner.intern("fold_conflicts");
    for (area_sym, counts) in by_area {
        let Some(area_node) = substrate
            .graph
            .nodes_of_type(area_t)
            .into_iter()
            .find(|node| {
                substrate.graph.node(*node).attrs.get(&name_k) == Some(&Value::Str(area_sym))
            })
        else {
            continue;
        };
        let load_node = substrate
            .graph
            .neighbours(area_node, Some(has_load))
            .first()
            .copied()
            .unwrap_or_else(|| {
                let load = substrate.add_node(load_t, FxHashMap::default());
                let _ = substrate.add_edge(area_node, has_load, load, FxHashMap::default());
                load
            });
        substrate.set_attr(
            load_node,
            queued_k,
            Value::Int(counts.pending + counts.requested),
        );
        substrate.set_attr(load_node, running_k, Value::Int(counts.running));
        substrate.set_attr(load_node, completed_k, Value::Int(counts.completed));
        substrate.set_attr(load_node, failed_k, Value::Int(counts.failed));
        substrate.set_attr(load_node, stale_k, Value::Int(counts.stale));
        substrate.set_attr(load_node, shed_k, Value::Int(counts.shed));
        substrate.set_attr(load_node, capacity_k, Value::Int(capacity as i64));
        substrate.set_attr(load_node, wall_k, Value::Int(wall_micros as i64));
        substrate.set_attr(load_node, conflicts_k, Value::Int(counts.stale));
    }
}

/// ACCELERATOR (block 184000) — a DROPPABLE, BYTE-IDENTICAL vectorized mirror
/// of the 2-D retina's per-cell transduce+onset sheet.
///
/// The graph path per tick is: `submit_photons_2d` mints ONE
/// `photon_transduce_onset` CognitiveTask per cell → `run_cognitive_tasks`
/// executes each kernel + folds a TaskResult → `run_rules` fires
/// `photon_apply_receptor_transduction` (writes the rod's activation /
/// adaptation / caught_quanta / input_epoch from output[0..2]) and
/// `retinal_mint_onset_2d` (thresholds output[3], enforces the per-cell
/// refractory, MINTS a `RetinalOnsetEvent`). That last rule's per-tick match
/// scan is the residual O(cells²) the 183000 prune left standing.
///
/// This function computes the SAME per-cell outputs and mints the SAME onset
/// events in ONE O(cells) Rust pass, holding the graph lock once — NO
/// CognitiveTask / TaskResult nodes, NO `run_rules` join. It reuses
/// `execute_kernel("photon_transduce_onset", …)` VERBATIM (the shared oracle
/// kernel), so the transduced values are bit-for-bit those the graph path
/// folds; it mirrors the two rules' effects with the same interned keys and
/// Value types, so the resulting graph state (rod attrs + RetinalOnsetEvent
/// set + column input/column epoch + last_onset_epoch) is byte-identical. Turn the accelerator OFF
/// (the adapter branches on `retina_accel`) and the graph path runs as the
/// correctness oracle. NO new Term enum variant — a batch graph op only.
///
/// `perturb` injects a WRONG mirror (a large offset onto onset_db that fires
/// every cell) so the byte-identity check can be shown NON-VACUOUS: ON with
/// `perturb=true` must DIVERGE from the graph path.
///
/// Payload i is the SAME `[center, bandwidth, adaptation, adapt_rate,
/// half_sat, dark_current, (wavelength,count)*]` the adapter packs for the
/// graph task. `rod_ids[i]` / `col_ids[i]` are the cell's rod + column nodes.
///
/// DIRTY-INDEX (block 185000). The arrays above are the WORK LIST, not
/// necessarily the whole sheet: the adapter passes only the cells it must
/// process this tick (the sensor's change report ∪ the cells not yet settled),
/// which is what makes per-tick cost O(SURPRISE) instead of O(cells).
///   * `cell_idx[i]` is work item i's FLAT CELL INDEX (None ⇒ identity, the
///     184000 full-sweep call shape — byte-unchanged).
///   * `track_settled` computes the EXACT skippability predicate per processed
///     cell and returns the flat indices that are NOT settled. A cell is
///     "settled" only when re-processing it with the SAME input would be
///     BIT-IDENTICAL to skipping it — the conjunction of three bitwise
///     equalities (the EMA floor is at its exact float fixed point; the drive
///     `caught` is bit-equal to the stored `caught_quanta`; the response is
///     bit-equal to the stored `activation`, which also makes `prev_activation`
///     safe) plus "no onset would mint". This is BRANCH A: skipping is then
///     PROVABLY byte-identical, not an approximation.
///   * `stamp_rod_ids` writes `input_epoch = epoch` on EVERY rod of the sheet —
///     the one attribute a skipped cell would otherwise leave stale — so the
///     whole-graph state is exactly a full sweep's.
///   * `naive_skip` is the WRONG-PREDICATE FALSIFIER: it marks a cell settled on
///     the input-unchanged clause ALONE, ignoring the still-moving EMA. That is
///     precisely the naive "skip quiet cells" design; it MUST break the
///     byte-identity check, proving the exact predicate is doing real work.
#[allow(clippy::too_many_arguments)]
pub(crate) fn retina_onset_batch(
    substrate: &mut Substrate,
    rod_ids: &[u32],
    col_ids: &[u32],
    payloads: Vec<Vec<f64>>,
    epoch: i64,
    threshold_db: f64,
    refractory_epochs: f64,
    perturb: bool,
    cell_idx: Option<&[u32]>,
    track_settled: bool,
    stamp_rod_ids: Option<&[u32]>,
    naive_skip: bool,
    per_sensor_epoch: bool,
) -> (usize, Vec<u32>) {
    // Intern every key/type ONCE (mirrors the two rules' vocabulary).
    let event_t = substrate.interner.intern("RetinalOnsetEvent");
    let has_onset_event = substrate.interner.intern("has_onset_event");
    let activation_k = substrate.interner.intern("activation");
    let prev_activation_k = substrate.interner.intern("prev_activation");
    let adaptation_k = substrate.interner.intern("adaptation");
    let caught_quanta_k = substrate.interner.intern("caught_quanta");
    let input_epoch_k = substrate.interner.intern("input_epoch");
    // PER-SENSOR EPOCH (block 188000). The rod's clock is the ROD'S — its own
    // KEY (`rod_epoch`, read by `retinal_mint_onset_2d` in the per-sensor seed
    // variant and by nothing else), advancing on the ROD's own change rather
    // than on a global submission. Off ⇒ `input_epoch`, stamped every tick,
    // byte-unchanged.
    let rod_epoch_k = substrate.interner.intern("rod_epoch");
    let epoch_key = if per_sensor_epoch {
        rod_epoch_k
    } else {
        input_epoch_k
    };
    let column_epoch_k = substrate.interner.intern("column_epoch");
    let column_epoch_key = if per_sensor_epoch {
        column_epoch_k
    } else {
        input_epoch_k
    };
    let last_onset_k = substrate.interner.intern("last_onset_epoch");
    let col_k = substrate.interner.intern("col");
    let row_k = substrate.interner.intern("row");
    let column_index_k = substrate.interner.intern("column_index");
    let row_index_k = substrate.interner.intern("row_index");
    let magnitude_db_k = substrate.interner.intern("magnitude_db");
    let epoch_k = substrate.interner.intern("epoch");
    let logical_time_k = substrate.interner.intern("logical_time");

    let n = rod_ids.len().min(col_ids.len()).min(payloads.len());
    let mut minted = 0usize;
    let mut unsettled: Vec<u32> = Vec::new();
    for i in 0..n {
        let rod = NodeID(rod_ids[i]);
        let col = NodeID(col_ids[i]);
        let flat = match cell_idx {
            Some(ix) if i < ix.len() => ix[i],
            _ => i as u32,
        };

        // ---- READ (drop the borrow before any mutation) ----
        let (old_activation, old_caught, rod_ok) = if substrate.graph.has_node(rod) {
            let a = &substrate.graph.node(rod).attrs;
            (
                a.get(&activation_k).cloned().unwrap_or(Value::Float(0.0)),
                a.get(&caught_quanta_k)
                    .cloned()
                    .unwrap_or(Value::Float(f64::NAN)),
                true,
            )
        } else {
            (Value::Float(0.0), Value::Float(f64::NAN), false)
        };
        let (col_val, row_val, last_onset, col_ok) = if substrate.graph.has_node(col) {
            let a = &substrate.graph.node(col).attrs;
            (
                a.get(&col_k).cloned().unwrap_or(Value::Int(0)),
                a.get(&row_k).cloned().unwrap_or(Value::Int(0)),
                read_i64(a, last_onset_k, i64::MIN) as f64,
                true,
            )
        } else {
            (Value::Int(0), Value::Int(0), f64::NEG_INFINITY, false)
        };
        if !rod_ok || !col_ok {
            if track_settled {
                unsettled.push(flat);
            }
            continue;
        }

        // ---- COMPUTE (reuse the shared oracle kernel VERBATIM) ----
        let payload_tuple = Value::Tuple(Arc::new(
            payloads[i].iter().map(|&x| Value::Float(x)).collect(),
        ));
        let out = match execute_kernel("photon_transduce_onset", &payload_tuple) {
            Ok(Value::Tuple(items) | Value::List(items)) if items.len() >= 4 => items,
            _ => {
                if track_settled {
                    unsettled.push(flat);
                }
                continue;
            }
        };
        let response = number(&out[0]).unwrap_or(0.0);
        let next_adapt = number(&out[1]).unwrap_or(0.0);
        let caught = number(&out[2]).unwrap_or(0.0);
        let onset_db = number(&out[3]).unwrap_or(0.0);
        // WRONG-mirror injection for the non-vacuity falsifier only.
        let onset_db_eff = if perturb { onset_db + 1000.0 } else { onset_db };

        // ---- EXACT SKIPPABILITY (block 185000, BRANCH A) ----
        // Would re-processing this cell with the SAME input be a genuine no-op?
        // Every clause is a BITWISE float comparison — nothing is "close enough".
        //   1. the EMA floor is at its exact float fixed point
        //      (`a + rate·(caught−a)` rounds back to `a`): at rate 0.4 this is
        //      reached after ~71 ticks of bit-repeatable input, and after it the
        //      adaptation write is a genuine no-op;
        //   2. the drive is bit-equal to the stored `caught_quanta` (the input
        //      really is the one already folded);
        //   3. the response is bit-equal to the stored `activation` — which also
        //      makes `prev_activation` safe, because after this tick
        //      `prev_activation == activation`, exactly what a further processed
        //      tick would write;
        //   4. no onset would mint (so the refractory / event stream cannot move).
        // `naive_skip` keeps ONLY clause 2 — the naive "skip quiet cells" design
        // that freezes a still-moving floor. It is the FALSIFIER.
        // The EXACT four-clause predicate, computed whenever ANY consumer needs
        // it — the 185000 work list (`track_settled`) or the 188000 per-sensor
        // epoch. `naive_skip` perturbs only the work list; the epoch decision
        // always uses the exact form.
        let exact_settled = if track_settled || per_sensor_epoch {
            let adaptation_in = payloads[i].get(2).copied().unwrap_or(f64::NAN);
            let old_caught_f = number(&old_caught).unwrap_or(f64::NAN);
            let old_act_f = number(&old_activation).unwrap_or(f64::NAN);
            let input_same = caught.to_bits() == old_caught_f.to_bits();
            let exact = next_adapt.to_bits() == adaptation_in.to_bits()
                && input_same
                && response.to_bits() == old_act_f.to_bits()
                && !(onset_db_eff > threshold_db);
            if track_settled {
                let settled = if naive_skip { input_same } else { exact };
                if !settled {
                    unsettled.push(flat);
                }
            }
            exact
        } else {
            false
        };

        // ---- APPLY transduction (mirror photon_apply_receptor_transduction) ----
        substrate.set_attr(rod, prev_activation_k, old_activation);
        substrate.set_attr(rod, activation_k, Value::Float(response));
        substrate.set_attr(rod, adaptation_k, Value::Float(next_adapt));
        substrate.set_attr(rod, caught_quanta_k, Value::Float(caught));
        // The graph path stamps the RetinalColumn before dispatching its task.
        // Mirror that clock too: downstream graph compositions such as held
        // prediction fresh-guard on rod_epoch == column_epoch.  Omitting this
        // made the otherwise byte-identical accelerator silently starve those
        // consumers even though transduction and onset outputs matched.
        substrate.set_attr(col, column_epoch_key, Value::Int(epoch));
        // PER-SENSOR EPOCH: the rod's clock advances on the ROD's own change.
        // A cell that is EXACTLY settled (EMA at its float fixed point, drive
        // and response bit-equal, AND no onset would mint) cannot mint an
        // onset, so the epoch the onset rule reads there is unobservable —
        // withholding the stamp is provably invisible. NOTHING is frozen or
        // deferred: the cell was fully processed, every state attr was written.
        if !(per_sensor_epoch && exact_settled) {
            substrate.set_attr(rod, epoch_key, Value::Int(epoch));
        }

        // ---- MINT onset (mirror retinal_mint_onset_2d) ----
        if onset_db_eff > threshold_db && (epoch as f64 - last_onset) > refractory_epochs {
            let mut attrs = FxHashMap::default();
            attrs.insert(column_index_k, col_val);
            attrs.insert(row_index_k, row_val);
            attrs.insert(magnitude_db_k, Value::Float(onset_db));
            attrs.insert(epoch_k, Value::Int(epoch));
            attrs.insert(logical_time_k, Value::Int(epoch));
            let event = substrate.add_node(event_t, attrs);
            if substrate
                .add_edge(col, has_onset_event, event, FxHashMap::default())
                .is_err()
            {
                substrate.remove_node(event);
                continue;
            }
            substrate.set_attr(col, last_onset_k, Value::Int(epoch));
            minted += 1;
        }
    }
    // The one attribute a SKIP would otherwise leave stale. Stamping it for the
    // whole sheet is pure bookkeeping (no kernel, no payload, no mint) and
    // restores exact whole-graph identity with a full sweep.
    // With the per-sensor epoch on there is nothing to restore: a skipped cell's
    // clock is SUPPOSED to lag, because that is what "the rod's own time" means.
    if let Some(all_rods) = stamp_rod_ids {
        if !per_sensor_epoch {
            for &rid in all_rods {
                let rod = NodeID(rid);
                if substrate.graph.has_node(rod) {
                    substrate.set_attr(rod, input_epoch_k, Value::Int(epoch));
                }
            }
        }
    }
    (minted, unsettled)
}

/// GRAPH-NATIVE EVENT PATH (block 191000) — the event-consumer analogue of
/// `retina_onset_batch`. The eye's carve / motion / salience settle used to
/// marshal every `RetinalOnsetEvent` OUT of the graph one node at a time in
/// Python (`for node in nodes("RetinalOnsetEvent"): node(node)["attrs"]`),
/// crossing the PyO3 boundary once PER EVENT, per stage, per frame — the
/// quadratic-in-receptors cost the 184000 receptor accelerator left behind.
/// The onset events are minted by a Rust rule and consumed by Rust kernels;
/// they should never round-trip through Python.
///
/// This does the WHOLE marshalling in ONE in-Rust `nodes_of_type` sweep: read
/// each event's `(column_index, [row_index,] epoch)` off the graph, filter by
/// the host observation window (`since_epoch`), sort by the SAME deterministic
/// key the Python used (`sort_mode`), build the `CognitiveTask.payload`, and
/// mint the task node + its retina edge — replicating byte-for-byte the node
/// the Python `add_node` built (same attr `Value` types, verified against
/// `py_to_value`). The `run_rules` mint rules + kernels are UNCHANGED — they
/// bind and reduce the identical task. NO new Term enum variant.
///
/// `dims` is 2 (1-D paths: `(col, epoch)`) or 3 (2-D paths: `(col, row,
/// epoch)`). `sort_mode` 0 = spatial-first (carve / salience), 1 = epoch-first
/// (motion). `prefix` is the per-stage payload header BEFORE the event count
/// (`[n_az]`/`[n_az,n_el,max_gap,vel_tol]`/empty for motion). `perturb=true`
/// is the non-vacuity FALSIFIER — it injects a wrong read (`col + 1000`) so the
/// byte-identity digest MUST break. Returns the minted `CognitiveTask` node id.
#[allow(clippy::too_many_arguments)]
pub(crate) fn retina_event_task_batch(
    substrate: &mut Substrate,
    retina_id: u32,
    edge_type: &str,
    kind: &str,
    marker_key: &str,
    dims: u8,
    sort_mode: u8,
    prefix: &[f64],
    input_epoch: i64,
    logical_time: i64,
    order: i64,
    since_epoch: Option<f64>,
    perturb: bool,
) -> u32 {
    // ---- Intern EVERY key up front (mirrors retina_onset_batch), so the
    //      immutable graph sweep below borrows nothing mutable. ----
    let event_t = substrate.interner.intern("RetinalOnsetEvent");
    let column_index_k = substrate.interner.intern("column_index");
    let row_index_k = substrate.interner.intern("row_index");
    let epoch_k = substrate.interner.intern("epoch");
    let cognitive_task_t = substrate.interner.intern("CognitiveTask");
    let status_k = substrate.interner.intern("status");
    let requested_s = substrate.interner.intern("requested");
    let kind_k = substrate.interner.intern("kind");
    let kind_s = substrate.interner.intern(kind);
    let payload_k = substrate.interner.intern("payload");
    let input_epoch_k = substrate.interner.intern("input_epoch");
    let logical_time_k = substrate.interner.intern("logical_time");
    let area_k = substrate.interner.intern("area");
    let retina_s = substrate.interner.intern("retina");
    let order_k = substrate.interner.intern("order");
    let salience_k = substrate.interner.intern("salience");
    let marker_k = substrate.interner.intern(marker_key);
    let edge_s = substrate.interner.intern(edge_type);
    // ATTENTION-DIRECTED EVENT FOCUS.  The focus is graph DATA linked to the
    // retina, not a host-selected rectangle.  Its absence (the default) leaves
    // the committed event sweep and task bytes unchanged.
    let has_focus_window_e = substrate.interner.intern("has_focus_window");
    let focus_active_k = substrate.interner.intern("active");
    let center_col_k = substrate.interner.intern("center_col");
    let center_row_k = substrate.interner.intern("center_row");
    let half_width_k = substrate.interner.intern("half_width");
    let half_height_k = substrate.interner.intern("half_height");
    let source_epoch_k = substrate.interner.intern("source_epoch");
    let focus_event_count_k = substrate.interner.intern("focus_event_count");
    let focus_total_event_count_k = substrate.interner.intern("focus_total_event_count");
    let focus_source_epoch_k = substrate.interner.intern("focus_source_epoch");
    // Multi-resolution pathway allocation is graph data on the Retina.
    // Absent/"all" preserves the legacy event bytes exactly.
    let event_pathway_k = substrate.interner.intern("event_pathway");
    let fovea_receptors_k = substrate.interner.intern("fovea_receptors");
    let n_columns_k = substrate.interner.intern("n_columns");
    let (event_pathway, fovea_receptors, n_columns) = if substrate.graph.has_node(NodeID(retina_id))
    {
        let attrs = &substrate.graph.node(NodeID(retina_id)).attrs;
        let mode = match attrs.get(&event_pathway_k) {
            Some(Value::Str(sym)) => substrate.interner.resolve(*sym).to_owned(),
            _ => "all".to_owned(),
        };
        (
            mode,
            attrs
                .get(&fovea_receptors_k)
                .and_then(number)
                .unwrap_or(0.0) as usize,
            attrs.get(&n_columns_k).and_then(number).unwrap_or(0.0) as usize,
        )
    } else {
        ("all".to_owned(), 0, 0)
    };

    let focus = substrate
        .graph
        .neighbours(NodeID(retina_id), Some(has_focus_window_e))
        .first()
        .and_then(|&node| {
            if !substrate.graph.has_node(node) {
                return None;
            }
            let attrs = &substrate.graph.node(node).attrs;
            let active = attrs.get(&focus_active_k).and_then(number).unwrap_or(0.0);
            if active != 1.0 {
                return None;
            }
            Some((
                attrs.get(&center_col_k).and_then(number).unwrap_or(-1.0),
                attrs.get(&center_row_k).and_then(number).unwrap_or(-1.0),
                attrs
                    .get(&half_width_k)
                    .and_then(number)
                    .unwrap_or(0.0)
                    .max(0.0),
                attrs
                    .get(&half_height_k)
                    .and_then(number)
                    .unwrap_or(0.0)
                    .max(0.0),
                attrs.get(&source_epoch_k).and_then(number).unwrap_or(-1.0),
            ))
        });

    // ---- ONE in-Rust sweep of the async event stream (was the Python loop). ----
    let ids = substrate.graph.nodes_of_type(event_t);
    let mut events: Vec<(f64, f64, f64)> = Vec::with_capacity(ids.len());
    for nid in ids {
        if !substrate.graph.has_node(nid) {
            continue;
        }
        let a = &substrate.graph.node(nid).attrs;
        let e = a.get(&epoch_k).and_then(number).unwrap_or(0.0);
        if let Some(se) = since_epoch {
            if e < se {
                continue;
            }
        }
        let c = a.get(&column_index_k).and_then(number).unwrap_or(0.0);
        let r = if dims == 3 {
            a.get(&row_index_k).and_then(number).unwrap_or(0.0)
        } else {
            0.0
        };
        events.push((c, r, e));
    }
    if dims == 3
        && n_columns > 0
        && fovea_receptors > 0
        && matches!(event_pathway.as_str(), "fovea" | "periphery")
    {
        events.retain(|(col, row, _)| {
            let flat = (*row as usize)
                .saturating_mul(n_columns)
                .saturating_add(*col as usize);
            let is_fovea = flat < fovea_receptors;
            if event_pathway == "fovea" {
                is_fovea
            } else {
                !is_fovea
            }
        });
    }
    let total_event_count = events.len();
    if let Some((center_col, center_row, half_width, half_height, _)) = focus {
        events.retain(|(col, row, _)| {
            (*col - center_col).abs() <= half_width
                && (dims != 3 || (*row - center_row).abs() <= half_height)
        });
    }
    // Deterministic serialisation — replicate the Python sort key EXACTLY so the
    // payload is byte-identical (the kernels are order-invariant, but matching
    // the order makes the identity trivially provable at the payload grain).
    let epoch_first = sort_mode != 0;
    if dims == 3 {
        if epoch_first {
            // 2-D motion: (epoch, row, col)
            events.sort_by(|a, b| {
                a.2.total_cmp(&b.2)
                    .then(a.1.total_cmp(&b.1))
                    .then(a.0.total_cmp(&b.0))
            });
        } else {
            // 2-D carve / salience: (row, col, epoch)
            events.sort_by(|a, b| {
                a.1.total_cmp(&b.1)
                    .then(a.0.total_cmp(&b.0))
                    .then(a.2.total_cmp(&b.2))
            });
        }
    } else if epoch_first {
        // 1-D motion: (epoch, col)
        events.sort_by(|a, b| a.2.total_cmp(&b.2).then(a.0.total_cmp(&b.0)));
    } else {
        // 1-D carve / salience: (col, epoch)
        events.sort_by(|a, b| a.0.total_cmp(&b.0).then(a.2.total_cmp(&b.2)));
    }
    // ---- Build the payload as the Python path did: prefix ++ [count] ++ flat.
    //      Every element is a Value::Float (Python builds them with float()). ----
    let mut payload: smallvec::SmallVec<[Value; 4]> = smallvec::SmallVec::new();
    for &p in prefix {
        payload.push(Value::Float(p));
    }
    payload.push(Value::Float(events.len() as f64));
    for (c, r, e) in &events {
        let cc = if perturb { c + 1000.0 } else { *c };
        payload.push(Value::Float(cc));
        if dims == 3 {
            payload.push(Value::Float(*r));
        }
        payload.push(Value::Float(*e));
    }

    // ---- Mint the CognitiveTask node BYTE-IDENTICALLY to the Python add_node.
    //      Python str->Str(Sym), int->Int, float->Float, list->Tuple. ----
    let mut attrs: FxHashMap<Sym, Value> = FxHashMap::default();
    attrs.insert(status_k, Value::Str(requested_s));
    attrs.insert(kind_k, Value::Str(kind_s));
    attrs.insert(payload_k, Value::Tuple(Arc::new(payload)));
    attrs.insert(input_epoch_k, Value::Int(input_epoch));
    attrs.insert(logical_time_k, Value::Int(logical_time));
    attrs.insert(area_k, Value::Str(retina_s));
    attrs.insert(order_k, Value::Int(order));
    attrs.insert(salience_k, Value::Float(1.0));
    attrs.insert(marker_k, Value::Float(1.0));
    if let Some((_, _, _, _, source_epoch)) = focus {
        attrs.insert(focus_event_count_k, Value::Int(events.len() as i64));
        attrs.insert(
            focus_total_event_count_k,
            Value::Int(total_event_count as i64),
        );
        attrs.insert(focus_source_epoch_k, Value::Int(source_epoch as i64));
    }
    let task = substrate.add_node(cognitive_task_t, attrs);
    let _ = substrate.add_edge(NodeID(retina_id), edge_s, task, FxHashMap::default());
    task.0
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::checker::ConsistencyChecker;
    use crate::grammar::Grammar;
    use std::sync::Arc;

    #[test]
    fn retinal_layout_uniform_is_exact_block_mean() {
        let luma: Vec<f64> = (0..24).map(|v| v as f64).collect();
        let fov_h = 1.5;
        let fov_v = 1.0;
        let gaze_az = vec![-0.5, 0.0, 0.5, -0.5, 0.0, 0.5];
        let gaze_el = vec![-0.25, -0.25, -0.25, 0.25, 0.25, 0.25];
        let out = sample_retinal_layout(
            &luma,
            4,
            6,
            &gaze_az,
            &gaze_el,
            &vec![0.5; 6],
            &vec![0.5; 6],
            fov_h,
            fov_v,
        )
        .unwrap();
        assert_eq!(out, vec![3.5, 5.5, 7.5, 15.5, 17.5, 19.5]);
    }

    #[test]
    fn retinal_layout_native_pixel_apertures_do_not_oversample() {
        let width = 320usize;
        let height = 240usize;
        let luma: Vec<f64> = (0..width * height).map(|v| v as f64).collect();
        let fov_h = std::f64::consts::FRAC_PI_2;
        let fov_v = std::f64::consts::FRAC_PI_3;
        let px_w = fov_h / width as f64;
        let px_h = fov_v / height as f64;
        let x = 103usize;
        let y = 77usize;
        let az = -fov_h * 0.5 + px_w * (x as f64 + 0.5);
        let el = -fov_v * 0.5 + px_h * (y as f64 + 0.5);
        let out = sample_retinal_layout(
            &luma,
            height,
            width,
            &[az],
            &[el],
            &[px_w],
            &[px_h],
            fov_h,
            fov_v,
        )
        .unwrap();
        assert_eq!(out, vec![luma[y * width + x]]);
    }

    #[test]
    fn allocentric_projection_nearest_occludes_and_unknown_stays_absent() {
        let (values, confidence, present, source) = project_allocentric_retina(
            &[10.0, 5.0],
            &[0.0, 0.0],
            &[0.0, 0.0],
            &[0.2, 0.2],
            &[40.0, 90.0],
            &[12.0, 55.0],
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            &[0.0, 1.0],
            &[0.0, 0.0],
            &[0.1, 0.1],
            &[0.1, 0.1],
        )
        .unwrap();
        assert_eq!(values, vec![90.0, 0.0]);
        assert_eq!(confidence, vec![55.0, 0.0]);
        assert_eq!(present, vec![true, false]);
        assert_eq!(source, vec![1, -1]);
    }

    #[test]
    fn allocentric_projection_applies_pose_yaw_and_pitch() {
        let (values, _, present, _) = project_allocentric_retina(
            &[0.0],
            &[10.0],
            &[10.0],
            &[0.1],
            &[77.0],
            &[1.0],
            0.0,
            0.0,
            0.0,
            std::f64::consts::FRAC_PI_2,
            std::f64::consts::FRAC_PI_4,
            &[0.0],
            &[0.0],
            &[0.05],
            &[0.05],
        )
        .unwrap();
        assert_eq!(values, vec![77.0]);
        assert_eq!(present, vec![true]);
    }

    #[test]
    fn pure_kernel_is_deterministic() {
        let payload = Value::Tuple(Arc::new(
            vec![Value::Int(1), Value::Int(4), Value::Int(2)].into(),
        ));
        assert_eq!(
            execute_kernel("abs_diff_energy", &payload).unwrap(),
            Value::Float(5.0),
        );
    }

    fn supervised_identity_task(
        authority_value: Value,
        epoch_value: Value,
        renew_value: Value,
        is_checkin: bool,
    ) -> (Substrate, NodeID, NodeID, NodeID) {
        let mut substrate = Substrate::new(ConsistencyChecker::new(Grammar::new()));
        let status = substrate.interner.intern("status");
        let kind = substrate.interner.intern("kind");
        let payload = substrate.interner.intern("payload");
        let input_epoch = substrate.interner.intern("input_epoch");
        let lease_generation = substrate.interner.intern("lease_generation");
        let continuation_authority = substrate.interner.intern("continuation_authority");
        let renew_before_epoch = substrate.interner.intern("renew_before_epoch");
        let cognitive_epoch = substrate.interner.intern("cognitive_epoch");
        let enabled = substrate.interner.intern("enabled");
        let requested = substrate.interner.intern("requested");
        let identity = substrate.interner.intern("identity");
        let task_t = substrate.interner.intern("CognitiveTask");
        let process_t = substrate.interner.intern("CognitiveProcess");
        let policy_t = substrate.interner.intern("CognitiveSupervisionPolicy");

        let mut policy_attrs = FxHashMap::default();
        policy_attrs.insert(enabled, Value::Int(1));
        policy_attrs.insert(cognitive_epoch, epoch_value);
        let policy = substrate.add_node(policy_t, policy_attrs);
        let mut process_attrs = FxHashMap::default();
        process_attrs.insert(continuation_authority, authority_value);
        process_attrs.insert(lease_generation, Value::Int(3));
        process_attrs.insert(renew_before_epoch, renew_value);
        let process = substrate.add_node(process_t, process_attrs);
        let mut task_attrs = FxHashMap::default();
        task_attrs.insert(status, Value::Str(requested));
        task_attrs.insert(kind, Value::Str(identity));
        task_attrs.insert(payload, Value::Int(17));
        task_attrs.insert(input_epoch, Value::Int(0));
        task_attrs.insert(lease_generation, Value::Int(3));
        let task = substrate.add_node(task_t, task_attrs);

        let governed_by = substrate
            .interner
            .intern("governed_by_cognitive_supervision_policy");
        let process_edge = substrate.interner.intern(if is_checkin {
            "checks_cognitive_process"
        } else {
            "continues_cognitive_process"
        });
        substrate
            .graph
            .insert_edge(process, governed_by, policy, FxHashMap::default())
            .expect("process policy edge");
        substrate
            .graph
            .insert_edge(task, process_edge, process, FxHashMap::default())
            .expect("task process edge");
        (substrate, task, process, policy)
    }

    #[test]
    fn legacy_unbound_task_is_unaffected_by_supervision_contract() {
        let mut substrate = Substrate::new(ConsistencyChecker::new(Grammar::new()));
        let status = substrate.interner.intern("status");
        let kind = substrate.interner.intern("kind");
        let payload = substrate.interner.intern("payload");
        let requested = substrate.interner.intern("requested");
        let identity = substrate.interner.intern("identity");
        let task_t = substrate.interner.intern("CognitiveTask");
        let mut attrs = FxHashMap::default();
        attrs.insert(status, Value::Str(requested));
        attrs.insert(kind, Value::Str(identity));
        attrs.insert(payload, Value::Int(29));
        let task = substrate.add_node(task_t, attrs);

        let summary = run_requested(&mut substrate, 1);

        assert_eq!(summary.completed, 1);
        let done = substrate.interner.intern("done");
        assert_eq!(
            substrate.graph.node(task).attrs.get(&status),
            Some(&Value::Str(done)),
        );
    }

    #[test]
    fn supervised_task_requires_strict_integer_lease_fields() {
        let (mut substrate, task, _, _) =
            supervised_identity_task(Value::Float(1.0), Value::Int(4), Value::Int(8), false);
        let prepared = prepare_requested(&mut substrate, 1);

        assert!(prepared.tasks.is_empty());
        let status = substrate.interner.intern("status");
        let requested = substrate.interner.intern("requested");
        assert_eq!(
            substrate.graph.node(task).attrs.get(&status),
            Some(&Value::Str(requested)),
        );
    }

    #[test]
    fn supervised_task_uses_its_process_local_policy_clock() {
        let (mut substrate, task, _, _) =
            supervised_identity_task(Value::Int(1), Value::Int(4), Value::Int(8), false);
        let policy_t = substrate.interner.intern("CognitiveSupervisionPolicy");
        let enabled = substrate.interner.intern("enabled");
        let epoch = substrate.interner.intern("cognitive_epoch");
        let mut other_attrs = FxHashMap::default();
        other_attrs.insert(enabled, Value::Int(1));
        other_attrs.insert(epoch, Value::Int(100));
        substrate.add_node(policy_t, other_attrs);

        let summary = run_requested(&mut substrate, 1);

        assert_eq!(summary.completed, 1);
        let status = substrate.interner.intern("status");
        let done = substrate.interner.intern("done");
        assert_eq!(
            substrate.graph.node(task).attrs.get(&status),
            Some(&Value::Str(done)),
        );
    }

    #[test]
    fn asynchronous_fold_rejects_withdrawn_renewed_and_expired_leases() {
        for mutation in ["withdraw", "renew", "expire"] {
            let (mut substrate, task, process, policy) =
                supervised_identity_task(Value::Int(1), Value::Int(4), Value::Int(8), false);
            let prepared = prepare_requested(&mut substrate, 1);
            assert_eq!(prepared.tasks.len(), 1);
            let completed = execute_prepared(prepared);
            match mutation {
                "withdraw" => {
                    let authority = substrate.interner.intern("continuation_authority");
                    substrate.set_attr(process, authority, Value::Int(0));
                }
                "renew" => {
                    let generation = substrate.interner.intern("lease_generation");
                    substrate.set_attr(process, generation, Value::Int(4));
                }
                "expire" => {
                    let epoch = substrate.interner.intern("cognitive_epoch");
                    substrate.set_attr(policy, epoch, Value::Int(8));
                }
                _ => unreachable!(),
            }

            let summary = fold_completed(&mut substrate, completed);

            assert_eq!(summary.stale, 1, "mutation {mutation}");
            let status = substrate.interner.intern("status");
            let stale = substrate.interner.intern("stale");
            assert_eq!(
                substrate.graph.node(task).attrs.get(&status),
                Some(&Value::Str(stale)),
                "mutation {mutation}",
            );
        }
    }

    #[test]
    fn matching_checkin_task_runs_only_while_its_process_is_held() {
        let (mut held, task, _, _) =
            supervised_identity_task(Value::Int(0), Value::Int(4), Value::Int(8), true);
        let summary = run_requested(&mut held, 1);
        assert_eq!(summary.completed, 1);
        let status = held.interner.intern("status");
        let done = held.interner.intern("done");
        assert_eq!(
            held.graph.node(task).attrs.get(&status),
            Some(&Value::Str(done))
        );

        let (mut active, active_task, _, _) =
            supervised_identity_task(Value::Int(1), Value::Int(4), Value::Int(8), true);
        let prepared = prepare_requested(&mut active, 1);
        assert!(prepared.tasks.is_empty());
        let active_status = active.interner.intern("status");
        let requested = active.interner.intern("requested");
        assert_eq!(
            active.graph.node(active_task).attrs.get(&active_status),
            Some(&Value::Str(requested)),
        );
    }

    #[test]
    fn context_bound_completion_is_stale_after_its_graph_clock_deadline() {
        let mut substrate = Substrate::new(ConsistencyChecker::new(Grammar::new()));
        let status = substrate.interner.intern("status");
        let epoch = substrate.interner.intern("epoch");
        let kind = substrate.interner.intern("kind");
        let payload = substrate.interner.intern("payload");
        let input_epoch = substrate.interner.intern("input_epoch");
        let deadline_epoch = substrate.interner.intern("deadline_epoch");
        let logical_time = substrate.interner.intern("logical_time");
        let area = substrate.interner.intern("area");
        let execution_class = substrate.interner.intern("execution_class");
        let requested = substrate.interner.intern("requested");
        let active = substrate.interner.intern("active");
        let kernel = substrate.interner.intern("default_mode_projection");
        let system_two = substrate.interner.intern("system_two");
        let intrinsic = substrate.interner.intern("intrinsic");
        let context_t = substrate.interner.intern("InternallyGeneratedContext");
        let clock_t = substrate.interner.intern("NetworkModeState");
        let task_t = substrate.interner.intern("CognitiveTask");
        let mut context_attrs = FxHashMap::default();
        context_attrs.insert(status, Value::Str(active));
        context_attrs.insert(epoch, Value::Int(1));
        let context = substrate.add_node(context_t, context_attrs);
        let mut clock_attrs = FxHashMap::default();
        clock_attrs.insert(epoch, Value::Int(1));
        let clock = substrate.add_node(clock_t, clock_attrs);
        let mut task_attrs = FxHashMap::default();
        task_attrs.insert(status, Value::Str(requested));
        task_attrs.insert(kind, Value::Str(kernel));
        task_attrs.insert(
            payload,
            Value::Tuple(Arc::new(
                vec![
                    Value::Int(1),
                    Value::Int(2),
                    Value::Int(1),
                    Value::Float(0.25),
                ]
                .into(),
            )),
        );
        task_attrs.insert(input_epoch, Value::Int(1));
        task_attrs.insert(deadline_epoch, Value::Int(2));
        task_attrs.insert(logical_time, Value::Int(1));
        task_attrs.insert(area, Value::Str(intrinsic));
        task_attrs.insert(execution_class, Value::Str(system_two));
        let task = substrate.add_node(task_t, task_attrs);
        let about_context = substrate.interner.intern("about_context");
        let validated_by_clock = substrate.interner.intern("validated_by_clock");
        substrate
            .graph
            .insert_edge(task, about_context, context, FxHashMap::default())
            .expect("task context edge");
        substrate
            .graph
            .insert_edge(task, validated_by_clock, clock, FxHashMap::default())
            .expect("task clock edge");

        let prepared = prepare_requested_class(&mut substrate, 1, "system_two");
        let completed = execute_prepared(prepared);
        substrate.set_attr(clock, epoch, Value::Int(3));
        let summary = fold_completed(&mut substrate, completed);

        assert_eq!(summary.stale, 1);
        let stale = substrate.interner.intern("stale");
        assert_eq!(
            substrate.graph.node(task).attrs.get(&status),
            Some(&Value::Str(stale)),
        );
    }

    #[test]
    fn onset_kernel_shares_transduce_outputs_and_appends_db() {
        // Fresh receptor (adaptation 0) meets a bright drive: the first three
        // outputs must equal `photon_transduce` byte-for-byte (the shared
        // apply rule reads them by index), and the 4th is a LARGE positive dB
        // departure from the (near-zero) floor — an onset.
        let payload = Value::Tuple(Arc::new(
            vec![
                Value::Float(498.0),  // center_nm
                Value::Float(42.0),   // bandwidth_nm
                Value::Float(0.0),    // adaptation (floor before this obs)
                Value::Float(0.12),   // adapt_rate
                Value::Float(1024.0), // half_saturation
                Value::Float(0.15),   // dark_current
                Value::Float(500.0),
                Value::Float(2000.0), // one bright packet
            ]
            .into(),
        ));
        let base = execute_kernel("photon_transduce", &payload).unwrap();
        let onset = execute_kernel("photon_transduce_onset", &payload).unwrap();
        let (Value::Tuple(b) | Value::List(b), Value::Tuple(o) | Value::List(o)) = (&base, &onset)
        else {
            panic!("both kernels return tuples");
        };
        assert_eq!(o.len(), 4, "onset kernel appends the dB departure");
        assert_eq!(b.len(), 3, "transduce kernel is byte-unchanged (3 outputs)");
        for i in 0..3 {
            assert_eq!(b[i], o[i], "shared output {i} must be byte-identical");
        }
        let Value::Float(db) = o[3] else {
            panic!("db is a float")
        };
        assert!(
            db > 6.0,
            "a bright step off a zero floor is an onset (db={db})"
        );
    }

    #[test]
    fn onset_db_falls_silent_when_the_floor_has_adapted() {
        // Fully adapted: the floor equals the drive, so the dB departure is
        // ~0 — silence. This is the mechanism that makes a held bright scene
        // go quiet, and it is entirely the floor's doing.
        let payload = Value::Tuple(Arc::new(
            vec![
                Value::Float(498.0),
                Value::Float(42.0),
                Value::Float(2000.0), // adaptation already == the drive
                Value::Float(0.12),
                Value::Float(1024.0),
                Value::Float(0.0),
                Value::Float(498.0),
                Value::Float(2000.0),
            ]
            .into(),
        ));
        let out = execute_kernel("photon_transduce_onset", &payload).unwrap();
        let (Value::Tuple(o) | Value::List(o)) = out else {
            panic!()
        };
        let Value::Float(db) = o[3] else { panic!() };
        assert!(
            db.abs() < 1.0,
            "an adapted floor silences the onset (db={db})"
        );
    }

    #[test]
    fn event_motion_recovers_slope_and_decorrelates_when_scrambled() {
        // A clean L->R diagonal (column advances +2 per epoch) recovers
        // direction +1, speed 2, coherence 1, zero residual. The SAME columns
        // with epochs shuffled decorrelate (coherence < 1) — motion is the
        // space-time STRUCTURE of the events, not a static column bias.
        let diag = Value::Tuple(Arc::new(
            vec![
                Value::Float(4.0),
                Value::Float(0.0),
                Value::Float(0.0),
                Value::Float(2.0),
                Value::Float(1.0),
                Value::Float(4.0),
                Value::Float(2.0),
                Value::Float(6.0),
                Value::Float(3.0),
            ]
            .into(),
        ));
        let (Value::Tuple(o) | Value::List(o)) =
            execute_kernel("retinal_event_motion", &diag).unwrap()
        else {
            panic!("motion kernel returns a tuple")
        };
        assert_eq!(o[0], Value::Float(1.0), "L->R direction is +1");
        assert_eq!(o[1], Value::Float(2.0), "slope equals the step (2)");
        assert_eq!(o[3], Value::Float(1.0), "a clean diagonal is coherent");

        // Same columns (0,2,4,6), epochs permuted (0,2,1,3): slope shrinks and
        // coherence drops below 1 — the diagonal is broken.
        let scrambled = Value::Tuple(Arc::new(
            vec![
                Value::Float(4.0),
                Value::Float(0.0),
                Value::Float(0.0),
                Value::Float(2.0),
                Value::Float(2.0),
                Value::Float(4.0),
                Value::Float(1.0),
                Value::Float(6.0),
                Value::Float(3.0),
            ]
            .into(),
        ));
        let (Value::Tuple(o2) | Value::List(o2)) =
            execute_kernel("retinal_event_motion", &scrambled).unwrap()
        else {
            panic!()
        };
        let (Value::Float(c_clean), Value::Float(c_scr)) = (&o[3], &o2[3]) else {
            panic!()
        };
        assert!(
            c_scr < c_clean,
            "scrambling the epochs must reduce coherence"
        );
    }

    #[test]
    fn event_motion_is_silent_without_temporal_or_spatial_spread() {
        // All events at one epoch (a flash) — no temporal spread, no direction.
        let flash = Value::Tuple(Arc::new(
            vec![
                Value::Float(3.0),
                Value::Float(0.0),
                Value::Float(5.0),
                Value::Float(1.0),
                Value::Float(5.0),
                Value::Float(2.0),
                Value::Float(5.0),
            ]
            .into(),
        ));
        let (Value::Tuple(o) | Value::List(o)) =
            execute_kernel("retinal_event_motion", &flash).unwrap()
        else {
            panic!()
        };
        assert_eq!(o[0], Value::Float(0.0), "a flash has no direction");
        assert_eq!(o[3], Value::Float(0.0), "a flash has no coherence");

        // Fewer than two events — nothing to fit.
        let one = Value::Tuple(Arc::new(
            vec![Value::Float(1.0), Value::Float(3.0), Value::Float(0.0)].into(),
        ));
        let (Value::Tuple(o2) | Value::List(o2)) =
            execute_kernel("retinal_event_motion", &one).unwrap()
        else {
            panic!()
        };
        assert_eq!(o2[0], Value::Float(0.0));
        assert_eq!(o2[4], Value::Float(1.0), "the event count is reported");
    }

    // The `retinal_residual_salience` kernel (Rung 4) is exercised end-to-end
    // by the Python migrated gate `tests/test_residual_salience_event_migrated.py`
    // through `run_cognitive_tasks` (the same `execute_kernel` entry). A native
    // #[test] is intentionally omitted here: this crate's cfg(test) target does
    // not currently compile (pre-existing `o[3]` moves out of the SmallVec-backed
    // `Value::Tuple` in the retinal_event_motion tests above), and cfg(test) code
    // is excluded from the release cdylib the engine is built from either way.

    #[test]
    fn empty_runtime_is_a_noop() {
        let mut substrate = Substrate::new(ConsistencyChecker::new(Grammar::new()));
        let summary = run_requested(&mut substrate, 4);
        assert_eq!(summary.requested, 0);
    }

    #[test]
    fn worker_capacity_keeps_explicit_reduction_and_resolves_auto() {
        assert_eq!(resolve_worker_capacity(Some(1)), 1);
        assert_eq!(resolve_worker_capacity(Some(3)), 3);
        assert!(resolve_worker_capacity(None) >= 1);
    }
}
