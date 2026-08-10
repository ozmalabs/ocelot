//! Inferior colliculus — modulation-rate analysis above the cochlear
//! nucleus.
//!
//! The IC's job is to tell *what's modulating how fast*. Speech
//! amplitude modulations carry word/syllable/phoneme structure;
//! the 4–8 Hz channel in particular is where syllables live.
//!
//! Pipeline:
//!   1. Recompute per-cochlear-band envelope (gammatone +
//!      hair-cell rectify + LPF — same primitives as
//!      cochlear_nucleus).
//!   2. For each (band × modulation rate), bandpass-filter the
//!      envelope around that modulation rate and take its RMS
//!      over the analysis window. The result is the energy in
//!      that modulation channel — one number per channel.
//!   3. Detect peaks in each channel above threshold → emit
//!      ModulationEvent nodes (sparse spike representation).
//!   4. Cluster syllable-rate events (4–8 Hz channel) across
//!      cochlear bands within a coincidence window → emit
//!      SyllableNucleus nodes.
//!
//! All output lands as graph data the rule engine can query.

use crate::graph::NodeID;
use crate::substrate::Substrate;
use crate::sym::Sym;
use crate::value::Value;
use rustc_hash::FxHashMap;
use smallvec::SmallVec;

#[derive(Debug, Clone, Copy)]
pub struct IcConfig {
    /// Envelope low-pass cutoff (Hz) — same as cochlear_nucleus.
    pub envelope_lp_hz: f32,
    /// Q factor for modulation-rate bandpass filters. Higher Q =
    /// sharper tuning. Biological IC neurons have Q ~1–3.
    pub mod_q: f32,
    /// Per-channel peak threshold (in dB above the channel's local
    /// floor) to count as a ModulationEvent.
    pub peak_threshold_db: f32,
    /// Refractory period for peak-picking inside one channel (ms).
    pub peak_refractory_ms: f32,
    /// Fraction of cochlear bands that must fire a syllable-rate
    /// ModulationEvent within `syllable_window_ms` to count as a
    /// SyllableNucleus.
    pub syllable_coincidence: f32,
    /// Coincidence window for the syllable-nucleus cross-band
    /// aggregation (ms).
    pub syllable_window_ms: f32,
    /// Modulation rate (Hz) at the bottom of the syllable range.
    /// The default 4 Hz is the slow edge of where syllables live.
    pub syllable_low_hz: f32,
    /// Modulation rate (Hz) at the top of the syllable range.
    /// 8 Hz is where syllables shade into faster phoneme rates.
    pub syllable_high_hz: f32,
}

impl Default for IcConfig {
    fn default() -> Self {
        Self {
            envelope_lp_hz: 50.0,
            mod_q: 2.0,
            peak_threshold_db: 4.0,
            peak_refractory_ms: 80.0,
            syllable_coincidence: 0.4,
            syllable_window_ms: 60.0,
            syllable_low_hz: 4.0,
            syllable_high_hz: 8.0,
        }
    }
}

#[derive(Debug, Clone, Copy, Default)]
pub struct IcSummary {
    pub channels: usize,
    pub modulation_events: usize,
    pub syllables: usize,
}

// --- DSP -----------------------------------------------------------------

/// Bandpass IIR around `fc` with quality factor `q`. RBJ cookbook
/// constant-skirt-gain BPF, direct-form-I. Output length = input.
fn bandpass(input: &[f32], fs: f32, fc: f32, q: f32) -> Vec<f32> {
    let omega = 2.0 * std::f32::consts::PI * fc / fs;
    let (sin_o, cos_o) = (omega.sin(), omega.cos());
    let alpha = sin_o / (2.0 * q.max(0.001));
    let b0 = alpha;
    let b1 = 0.0;
    let b2 = -alpha;
    let a0 = 1.0 + alpha;
    let a1 = -2.0 * cos_o;
    let a2 = 1.0 - alpha;
    let bb0 = b0 / a0;
    let bb1 = b1 / a0;
    let bb2 = b2 / a0;
    let aa1 = a1 / a0;
    let aa2 = a2 / a0;
    let mut out = Vec::with_capacity(input.len());
    let mut x1 = 0.0f32;
    let mut x2 = 0.0f32;
    let mut y1 = 0.0f32;
    let mut y2 = 0.0f32;
    for &x in input {
        let y = bb0 * x + bb1 * x1 + bb2 * x2 - aa1 * y1 - aa2 * y2;
        out.push(y);
        x2 = x1;
        x1 = x;
        y2 = y1;
        y1 = y;
    }
    out
}

/// Envelope-of-envelope. Half-wave rectify then one-pole LPF —
/// turns the AC bandpass output into a DC-ish energy signal that
/// peak-picks meaningfully.
fn rectified_lpf(x: &[f32], cutoff_hz: f32, fs: f32) -> Vec<f32> {
    let tau = 1.0 / (2.0 * std::f32::consts::PI * cutoff_hz);
    let alpha = 1.0 / (1.0 + tau * fs);
    let mut out = Vec::with_capacity(x.len());
    let mut y = 0.0f32;
    for &v in x {
        let r = v.abs();
        y += alpha * (r - y);
        out.push(y);
    }
    out
}

/// Schmitt-trigger peak-pick: one (sample, max-value) per
/// crossing-region of the signal above `threshold`. When the signal
/// rises above threshold, start tracking the maximum; when it drops
/// back below `threshold * 0.7` (hysteresis), emit the in-region
/// max as a single event.
///
/// This is the right shape for syllable / event detection on
/// envelope-like signals — one event per energy burst, not one per
/// local oscillation. `refractory_samples` enforces a hard minimum
/// gap between consecutive events on top of the hysteresis logic.
fn pick_peaks(
    signal: &[f32],
    threshold: f32,
    refractory_samples: usize,
) -> Vec<(usize, f32)> {
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
                if (peak_idx as isize - last_emit)
                    >= refractory_samples as isize
                {
                    out.push((peak_idx, peak_val));
                    last_emit = peak_idx as isize;
                }
                peak_val = f32::NEG_INFINITY;
            }
        }
    }
    // Final region — signal stayed above threshold to end of buffer.
    if in_region && (peak_idx as isize - last_emit) >= refractory_samples as isize {
        out.push((peak_idx, peak_val));
    }
    out
}

/// Compute the local-floor adaptive threshold for one channel, in
/// dB. Used so the peak threshold tracks background variation.
fn floor_dbs(signal: &[f32], fs: f32) -> Vec<f32> {
    let eps = 1e-10f32;
    let floor_win = (0.4 * fs).max(1.0) as usize;
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

// --- Gammatone + envelope reproduction (mirrors cochlear_nucleus) --------

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

// --- Main pass: samples → IC graph nodes --------------------------------

pub fn process_audio(
    substrate: &mut Substrate,
    audio_stream_nid: NodeID,
    samples: &[f32],
    sample_rate: u32,
    band_centres: &[f32],
    mod_rates_hz: &[f32],
    config: &IcConfig,
) -> IcSummary {
    let fs = sample_rate as f32;

    // Recompute per-band envelopes — same as cochlear_nucleus does.
    let mut envelopes: Vec<Vec<f32>> = Vec::with_capacity(band_centres.len());
    for &fc in band_centres {
        let band = gammatone_band(samples, sample_rate, fc, 4);
        let env = hair_cell_envelope(&band, config.envelope_lp_hz, sample_rate);
        envelopes.push(env);
    }

    // Intern symbols once.
    let modch_t = substrate.interner.intern("ModulationChannel");
    let modev_t = substrate.interner.intern("ModulationEvent");
    let syll_t = substrate.interner.intern("SyllableNucleus");
    let has_modch_e = substrate.interner.intern("has_modulation_channel");
    let has_modev_e = substrate.interner.intern("has_modulation_event");
    let has_syll_e = substrate.interner.intern("has_syllable_nucleus");
    let from_channel_e = substrate.interner.intern("from_channel");
    let contributed_by_e = substrate.interner.intern("contributed_by");

    let mut summary = IcSummary::default();
    // Per-channel: (band_index, rate_hz, channel_nid, peaks)
    let mut all_peaks: Vec<(usize, f32, NodeID, Vec<NodeID>)> = Vec::new();
    let refractory_samples =
        ((config.peak_refractory_ms * 0.001) * fs).max(1.0) as usize;

    for (band_i, env) in envelopes.iter().enumerate() {
        for &rate_hz in mod_rates_hz {
            // Bandpass envelope at modulation rate, take energy.
            let bp = bandpass(env, fs, rate_hz, config.mod_q);
            // Envelope-of-envelope. The LPF has to suppress BOTH
            // (a) the 2× rectification ripple and (b) the IIR
            // bandpass's offset-ring (when a burst ends, the BPF
            // keeps oscillating for a few cycles). Cutoff at
            // rate/4 smooths both: each burst produces one bump,
            // not a peak-trough-peak pattern. The cost is some
            // temporal blur (~250 ms for the 4 Hz channel), which
            // is fine — syllable nuclei don't need ms-precise
            // localisation.
            let energy = rectified_lpf(&bp, (rate_hz * 0.25).max(1.0), fs);
            let db = floor_dbs(&energy, fs);

            let peak_idxs = pick_peaks(
                &db,
                config.peak_threshold_db,
                refractory_samples,
            );

            // Channel summary.
            let peak_val = energy.iter().cloned().fold(0.0f32, f32::max);
            let mean_val = if energy.is_empty() {
                0.0
            } else {
                energy.iter().sum::<f32>() / energy.len() as f32
            };
            let mut attrs = FxHashMap::default();
            set_attr(&mut attrs, substrate, "band_index", Value::Int(band_i as i64));
            set_attr(&mut attrs, substrate, "centre_hz",
                       Value::Float(band_centres[band_i] as f64));
            set_attr(&mut attrs, substrate, "modulation_rate_hz",
                       Value::Float(rate_hz as f64));
            set_attr(&mut attrs, substrate, "sample_rate",
                       Value::Int(sample_rate as i64));
            set_attr(&mut attrs, substrate, "peak", Value::Float(peak_val as f64));
            set_attr(&mut attrs, substrate, "mean", Value::Float(mean_val as f64));
            set_attr(&mut attrs, substrate, "n_peaks",
                       Value::Int(peak_idxs.len() as i64));
            let ch_nid = substrate.add_node(modch_t, attrs);
            let _ = substrate.graph.insert_edge(
                audio_stream_nid, has_modch_e, ch_nid, FxHashMap::default(),
            );
            summary.channels += 1;

            // ModulationEvent per peak.
            let mut event_nids: Vec<NodeID> = Vec::with_capacity(peak_idxs.len());
            for (sample, db_val) in &peak_idxs {
                let t_s = *sample as f64 / sample_rate as f64;
                let mut ea = FxHashMap::default();
                set_attr(&mut ea, substrate, "time_s", Value::Float(t_s));
                set_attr(&mut ea, substrate, "band_index",
                           Value::Int(band_i as i64));
                set_attr(&mut ea, substrate, "centre_hz",
                           Value::Float(band_centres[band_i] as f64));
                set_attr(&mut ea, substrate, "modulation_rate_hz",
                           Value::Float(rate_hz as f64));
                set_attr(&mut ea, substrate, "magnitude_db",
                           Value::Float(*db_val as f64));
                let ev_nid = substrate.add_node(modev_t, ea);
                let _ = substrate.graph.insert_edge(
                    audio_stream_nid, has_modev_e, ev_nid, FxHashMap::default(),
                );
                let _ = substrate.graph.insert_edge(
                    ev_nid, from_channel_e, ch_nid, FxHashMap::default(),
                );
                event_nids.push(ev_nid);
                summary.modulation_events += 1;
            }

            all_peaks.push((band_i, rate_hz, ch_nid, event_nids));
        }
    }

    // Syllable-nucleus extraction:
    //
    // The bandpass-then-rectify pipeline above gives us ModulationChannel
    // energy + ModulationEvent peaks (real IC outputs); using its peaks
    // for syllable detection misfires because an IIR bandpass rings
    // symmetrically on burst onsets AND burst offsets — every syllable
    // burst produces two ModulationEvents (one entering the burst, one
    // leaving). That's correct IC behaviour, wrong syllable count.
    //
    // For SyllableNucleus we instead peak-pick the slow band envelope
    // itself — that has one bump per burst by construction. The IC's
    // role is just to GATE: only count a syllable nucleus if the band
    // had non-trivial energy in the 4–8 Hz modulation range during
    // that bump (so a non-syllabic transient like a click doesn't
    // count).

    let syll_threshold_db = config.peak_threshold_db;
    let refractory_samples_syll =
        ((config.peak_refractory_ms * 0.001) * fs).max(1.0) as usize;

    // Per-band: does this band have any syllable-rate channel with
    // peak energy above a sanity floor? Compute once before the
    // envelope peak loop.
    let mut band_in_syllabic_range: Vec<bool> = vec![false; band_centres.len()];
    for (band_i, rate_hz, ch_nid, _ev) in &all_peaks {
        if *rate_hz < config.syllable_low_hz || *rate_hz > config.syllable_high_hz {
            continue;
        }
        // Read the channel's peak attr off the graph node.
        let peak_sym = substrate.interner.intern("peak");
        let attrs = &substrate.graph.node(*ch_nid).attrs;
        if let Some(Value::Float(p)) = attrs.get(&peak_sym) {
            if *p > 0.01 {
                band_in_syllabic_range[*band_i] = true;
            }
        }
    }

    // Envelope peak-picking per band. Reuses the Schmitt-trigger
    // pick_peaks helper on the cochlear band envelope itself.
    let mut syllable_events: Vec<(f64, usize, NodeID)> = Vec::new();
    let onset_ev_t = substrate.interner.intern("OnsetEvent");
    let from_band_e = substrate.interner.intern("from_band");
    for (band_i, env) in envelopes.iter().enumerate() {
        if !band_in_syllabic_range[band_i] {
            continue;
        }
        let db = floor_dbs(env, fs);
        let peaks = pick_peaks(&db, syll_threshold_db, refractory_samples_syll);
        for (sample, db_val) in peaks {
            let t_s = sample as f64 / sample_rate as f64;
            // Synthesize an OnsetEvent-shaped record for the
            // SyllableNucleus to point at. Re-using the OnsetEvent
            // type means downstream rule writers don't need a new
            // node type for "envelope peak"; the node carries band
            // + time + magnitude_db, same shape as cochlear-nucleus
            // onsets.
            let mut ea = FxHashMap::default();
            set_attr(&mut ea, substrate, "time_s", Value::Float(t_s));
            set_attr(&mut ea, substrate, "band_index", Value::Int(band_i as i64));
            set_attr(&mut ea, substrate, "centre_hz",
                       Value::Float(band_centres[band_i] as f64));
            set_attr(&mut ea, substrate, "magnitude_db", Value::Float(db_val as f64));
            let origin_sym = substrate.interner.intern("ic_envelope_peak");
            set_attr(&mut ea, substrate, "origin", Value::Str(origin_sym));
            let ev_nid = substrate.add_node(onset_ev_t, ea);
            let _ = substrate.graph.insert_edge(
                audio_stream_nid,
                substrate.interner.intern("has_onset_event"),
                ev_nid,
                FxHashMap::default(),
            );
            syllable_events.push((t_s, band_i, ev_nid));
            let _ = from_band_e; // suppress unused-var; reserved for
                                 // a future from_band edge.
        }
    }
    syllable_events.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal));

    if !syllable_events.is_empty() {
        let window_s = (config.syllable_window_ms * 0.001) as f64;
        let n_bands = band_centres.len();
        let min_bands =
            ((config.syllable_coincidence * n_bands as f32).round().max(2.0)) as usize;

        let mut i = 0usize;
        while i < syllable_events.len() {
            let t0 = syllable_events[i].0;
            let mut j = i + 1;
            while j < syllable_events.len()
                && syllable_events[j].0 - t0 <= window_s
            {
                j += 1;
            }
            let mut bands_seen: SmallVec<[usize; 16]> = SmallVec::new();
            for k in i..j {
                let band = syllable_events[k].1;
                if !bands_seen.contains(&band) {
                    bands_seen.push(band);
                }
            }
            if bands_seen.len() >= min_bands {
                let mean_t: f64 = (i..j)
                    .map(|k| syllable_events[k].0)
                    .sum::<f64>()
                    / (j - i) as f64;
                let mut sa = FxHashMap::default();
                set_attr(&mut sa, substrate, "time_s", Value::Float(mean_t));
                set_attr(&mut sa, substrate, "n_bands",
                           Value::Int(bands_seen.len() as i64));
                set_attr(&mut sa, substrate, "n_member_events",
                           Value::Int((j - i) as i64));
                let syll_nid = substrate.add_node(syll_t, sa);
                let _ = substrate.graph.insert_edge(
                    audio_stream_nid, has_syll_e, syll_nid, FxHashMap::default(),
                );
                for k in i..j {
                    let _ = substrate.graph.insert_edge(
                        syll_nid,
                        contributed_by_e,
                        syllable_events[k].2,
                        FxHashMap::default(),
                    );
                }
                summary.syllables += 1;
            }
            i = if j > i { j } else { i + 1 };
        }
    }

    summary
}

fn set_attr(
    attrs: &mut FxHashMap<Sym, Value>,
    substrate: &mut Substrate,
    key: &str,
    v: Value,
) {
    let k = substrate.interner.intern(key);
    attrs.insert(k, v);
}
