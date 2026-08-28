//! A1 / belt cortex — spectro-temporal patches (STRFs).
//!
//! Each A1Patch in the graph is a parametrised STRF kernel. The
//! evaluation is a weighted sum over cochlear bands smoothed in
//! time:
//!
//!     R(t) = Σ_band  w_freq(band, t) · env_band(t)  ⊛  G_time
//!
//! For sustained / burst patches `w_freq` is a stationary Gaussian
//! in frequency. For FM patches `w_freq` shifts linearly with time
//! to follow the patch's slope. The temporal smoother G_time is a
//! one-pole IIR whose cutoff tracks the patch's duration.
//!
//! Output: per-patch A1Response summary node + A1Event nodes at
//! each above-threshold response peak. Same shape as the IC layer.

use crate::graph::NodeID;
use crate::substrate::Substrate;
use crate::sym::Sym;
use crate::value::Value;
use rustc_hash::FxHashMap;

#[derive(Debug, Clone, Copy)]
pub struct AcConfig {
    pub envelope_lp_hz: f32,
    pub peak_threshold_db: f32,
    pub peak_refractory_ms: f32,
}

impl Default for AcConfig {
    fn default() -> Self {
        Self {
            envelope_lp_hz: 50.0,
            peak_threshold_db: 4.0,
            peak_refractory_ms: 50.0,
        }
    }
}

#[derive(Debug, Clone)]
pub struct PatchSpec {
    pub nid: NodeID,
    pub name: String,
    pub kind: String,
    pub centre_hz: f32,
    pub freq_sigma_hz: f32,
    pub duration_ms: f32,
    pub slope_hz_per_ms: f32,
}

#[derive(Debug, Clone, Copy, Default)]
pub struct AcSummary {
    pub responses: usize,
    pub events: usize,
}

// --- Gammatone + envelope (mirrors cochlear_nucleus) --------------------

fn gammatone_band(samples: &[f32], fs: u32, fc: f32, order: u32) -> Vec<f32> {
    let fs_f = fs as f32;
    let n_taps = 256usize;
    let b = 2.0 * std::f32::consts::PI * 1.019 * (24.7 + 0.108 * fc);
    let mut impulse: Vec<f32> = (0..n_taps)
        .map(|i| {
            let t = i as f32 / fs_f;
            let p = t.powi(order as i32 - 1);
            let env = (-b * t).exp();
            let car = (2.0 * std::f32::consts::PI * fc * t).cos();
            p * env * car
        })
        .collect();
    let energy: f32 = impulse.iter().map(|x| x * x).sum::<f32>().sqrt();
    // The raw impulse energy can be ~1e-11 at high fc — don't
    // gate normalisation on a fixed threshold.
    if energy > 0.0 {
        for v in impulse.iter_mut() {
            *v /= energy;
        }
    }
    let n = samples.len();
    let m = impulse.len();
    let pad = m / 2;
    let mut out = vec![0.0f32; n];
    for i in 0..n {
        let mut acc = 0.0f32;
        for k in 0..m {
            let xi = i as isize + k as isize - pad as isize;
            if xi >= 0 && (xi as usize) < n {
                acc += samples[xi as usize] * impulse[k];
            }
        }
        out[i] = acc;
    }
    out
}

fn hair_cell_envelope(band: &[f32], cutoff_hz: f32, fs: u32) -> Vec<f32> {
    let alpha = if cutoff_hz <= 0.0 {
        1.0
    } else {
        let tau = 1.0 / (2.0 * std::f32::consts::PI * cutoff_hz);
        1.0 / (1.0 + tau * fs as f32)
    };
    let mut out = Vec::with_capacity(band.len());
    let mut y = 0.0f32;
    for &v in band {
        let rectified = v.max(0.0);
        y += alpha * (rectified - y);
        out.push(y);
    }
    out
}

fn lowpass_iir(x: &[f32], cutoff_hz: f32, fs: u32) -> Vec<f32> {
    let alpha = if cutoff_hz <= 0.0 {
        1.0
    } else {
        let tau = 1.0 / (2.0 * std::f32::consts::PI * cutoff_hz);
        1.0 / (1.0 + tau * fs as f32)
    };
    let mut out = Vec::with_capacity(x.len());
    let mut y = 0.0f32;
    for &v in x {
        y += alpha * (v - y);
        out.push(y);
    }
    out
}

fn floor_dbs(signal: &[f32], fs: u32) -> Vec<f32> {
    let eps = 1e-10f32;
    let floor_win = (0.4 * fs as f32).max(1.0) as usize;
    let mut floor = vec![0.0f32; signal.len()];
    let mut running = signal.first().copied().unwrap_or(0.0).abs() + eps;
    for (i, &v) in signal.iter().enumerate() {
        let v = v.abs();
        if v < running {
            running = v;
        } else {
            running += (v - running) / floor_win as f32;
        }
        floor[i] = running + eps;
    }
    let mut db = vec![0.0f32; signal.len()];
    for i in 0..signal.len() {
        let r = (signal[i].abs() + eps) / floor[i];
        db[i] = 20.0 * r.log10();
    }
    db
}

fn pick_peaks(signal: &[f32], threshold: f32, refractory_samples: usize) -> Vec<(usize, f32)> {
    if signal.len() < 3 {
        return Vec::new();
    }
    let release = threshold * 0.7;
    let mut out: Vec<(usize, f32)> = Vec::new();
    let mut in_region = false;
    let mut peak_idx = 0usize;
    let mut peak_val = f32::NEG_INFINITY;
    let mut last_emit: isize = -(refractory_samples as isize) - 1;
    for i in 0..signal.len() {
        let v = signal[i];
        if !in_region {
            if v >= threshold {
                in_region = true;
                peak_idx = i;
                peak_val = v;
            }
        } else {
            if v > peak_val {
                peak_val = v;
                peak_idx = i;
            }
            if v < release {
                in_region = false;
                if (peak_idx as isize - last_emit) >= refractory_samples as isize {
                    out.push((peak_idx, peak_val));
                    last_emit = peak_idx as isize;
                }
                peak_val = f32::NEG_INFINITY;
            }
        }
    }
    if in_region && (peak_idx as isize - last_emit) >= refractory_samples as isize {
        out.push((peak_idx, peak_val));
    }
    out
}

// --- Patch evaluation ---------------------------------------------------

/// Frequency-domain weight for a band centre under a patch's
/// stationary Gaussian. Used by sustained / burst patches.
fn freq_weight(band_centre: f32, patch_centre: f32, sigma: f32) -> f32 {
    let s = sigma.max(1.0);
    let d = band_centre - patch_centre;
    (-(d * d) / (2.0 * s * s)).exp()
}

/// Compute one A1Patch's response over time, in dB-above-floor
/// terms. Returns (response_signal, peak_value, mean_value).
fn evaluate_patch(
    envelopes: &[Vec<f32>],
    band_centres: &[f32],
    fs: u32,
    patch: &PatchSpec,
) -> (Vec<f32>, f32, f32) {
    let n = envelopes.first().map(|e| e.len()).unwrap_or(0);
    if n == 0 {
        return (Vec::new(), 0.0, 0.0);
    }
    let mut combined = vec![0.0f32; n];

    if patch.kind == "fm" && patch.slope_hz_per_ms.abs() > 1e-6 {
        // FM patch — frequency centre shifts with time. The slope is
        // in Hz/ms; convert to Hz/sample.
        let slope_per_sample = patch.slope_hz_per_ms / (fs as f32 / 1000.0);
        // Centre the FM trajectory on the patch's nominal centre at
        // the middle of the response so the patch fires when the
        // glide passes through.
        let mid_t = n as f32 / 2.0;
        for t in 0..n {
            let dt = t as f32 - mid_t;
            let centre_t = patch.centre_hz + slope_per_sample * dt;
            let mut sum = 0.0f32;
            for (band_i, env) in envelopes.iter().enumerate() {
                let w = freq_weight(band_centres[band_i], centre_t, patch.freq_sigma_hz);
                sum += w * env[t];
            }
            combined[t] = sum;
        }
    } else {
        // Stationary patch: one weight per band.
        let weights: Vec<f32> = band_centres
            .iter()
            .map(|&fc| freq_weight(fc, patch.centre_hz, patch.freq_sigma_hz))
            .collect();
        for t in 0..n {
            let mut sum = 0.0f32;
            for (band_i, env) in envelopes.iter().enumerate() {
                sum += weights[band_i] * env[t];
            }
            combined[t] = sum;
        }
    }

    // Temporal integration: one-pole LPF with cutoff matched to the
    // patch's duration. duration_ms ≈ 1/(2π·cutoff) → cutoff =
    // 1000/(2π·duration_ms).
    let cutoff_hz = if patch.duration_ms > 1.0 {
        1000.0 / (2.0 * std::f32::consts::PI * patch.duration_ms)
    } else {
        50.0
    };
    let smoothed = lowpass_iir(&combined, cutoff_hz, fs);

    let peak = smoothed.iter().cloned().fold(0.0f32, f32::max);
    let mean = if smoothed.is_empty() {
        0.0
    } else {
        smoothed.iter().sum::<f32>() / smoothed.len() as f32
    };
    (smoothed, peak, mean)
}

// --- Main pass ---------------------------------------------------------

pub fn process_audio(
    substrate: &mut Substrate,
    audio_stream_nid: NodeID,
    samples: &[f32],
    sample_rate: u32,
    band_centres: &[f32],
    patches: &[PatchSpec],
    config: &AcConfig,
) -> AcSummary {
    // Recompute per-band envelopes.
    let mut envelopes: Vec<Vec<f32>> = Vec::with_capacity(band_centres.len());
    for &fc in band_centres {
        let band = gammatone_band(samples, sample_rate, fc, 4);
        let env = hair_cell_envelope(&band, config.envelope_lp_hz, sample_rate);
        envelopes.push(env);
    }

    let resp_t = substrate.interner.intern("A1Response");
    let event_t = substrate.interner.intern("A1Event");
    let has_resp_e = substrate.interner.intern("has_a1_response");
    let has_event_e = substrate.interner.intern("has_a1_event");
    let for_patch_e = substrate.interner.intern("for_patch");
    let from_response_e = substrate.interner.intern("from_response");

    let refractory_samples =
        ((config.peak_refractory_ms * 0.001) * sample_rate as f32).max(1.0) as usize;
    let mut summary = AcSummary::default();

    for patch in patches {
        let (response, peak, mean) = evaluate_patch(&envelopes, band_centres, sample_rate, patch);

        let mut attrs = FxHashMap::default();
        let patch_name_sym = substrate.interner.intern(&patch.name);
        set_attr(
            &mut attrs,
            substrate,
            "patch_name",
            Value::Str(patch_name_sym),
        );
        let patch_kind_sym = substrate.interner.intern(&patch.kind);
        set_attr(
            &mut attrs,
            substrate,
            "patch_kind",
            Value::Str(patch_kind_sym),
        );
        set_attr(
            &mut attrs,
            substrate,
            "centre_hz",
            Value::Float(patch.centre_hz as f64),
        );
        set_attr(
            &mut attrs,
            substrate,
            "sample_rate",
            Value::Int(sample_rate as i64),
        );
        set_attr(
            &mut attrs,
            substrate,
            "n_samples",
            Value::Int(response.len() as i64),
        );
        set_attr(&mut attrs, substrate, "peak", Value::Float(peak as f64));
        set_attr(&mut attrs, substrate, "mean", Value::Float(mean as f64));
        let resp_nid = substrate.add_node(resp_t, attrs);
        let _ = substrate.graph.insert_edge(
            audio_stream_nid,
            has_resp_e,
            resp_nid,
            FxHashMap::default(),
        );
        let _ = substrate
            .graph
            .insert_edge(resp_nid, for_patch_e, patch.nid, FxHashMap::default());
        summary.responses += 1;

        let db = floor_dbs(&response, sample_rate);
        let peaks = pick_peaks(&db, config.peak_threshold_db, refractory_samples);
        for (sample, db_val) in peaks {
            let t_s = sample as f64 / sample_rate as f64;
            let mut ea = FxHashMap::default();
            set_attr(&mut ea, substrate, "time_s", Value::Float(t_s));
            let pn = substrate.interner.intern(&patch.name);
            set_attr(&mut ea, substrate, "patch_name", Value::Str(pn));
            set_attr(
                &mut ea,
                substrate,
                "magnitude_db",
                Value::Float(db_val as f64),
            );
            let ev_nid = substrate.add_node(event_t, ea);
            let _ = substrate.graph.insert_edge(
                audio_stream_nid,
                has_event_e,
                ev_nid,
                FxHashMap::default(),
            );
            let _ = substrate.graph.insert_edge(
                ev_nid,
                from_response_e,
                resp_nid,
                FxHashMap::default(),
            );
            summary.events += 1;
        }
    }

    summary
}

fn set_attr(attrs: &mut FxHashMap<Sym, Value>, substrate: &mut Substrate, key: &str, v: Value) {
    let k = substrate.interner.intern(key);
    attrs.insert(k, v);
}
