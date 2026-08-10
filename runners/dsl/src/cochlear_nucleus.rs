//! Cochlear nucleus — first auditory stage above the cochlea.
//!
//! Biology: cochlear-nerve fibres feed the cochlear nucleus, where
//! parallel cell types extract different aspects of the input:
//!
//!   * **Onset cells** fire one spike at sharp amplitude transients
//!     — the brain's "when did something start" signal. Every
//!     consonant onset is a transient; every syllable boundary is
//!     a stronger transient.
//!   * **Sustained-response cells** track the envelope of an
//!     ongoing tone — the "what's happening now" signal in
//!     parallel with onset cells.
//!   * **Octopus cells** fire when many onsets line up across
//!     frequency — syllable-onset detection by broadband
//!     coincidence.
//!
//! Output is graph data, not signal data: per-band OnsetEvent
//! nodes (each a discrete spike), one EnvelopeChannel per band
//! carrying the sustained signal, and one BroadbandOnset per
//! cross-band cluster.
//!
//! Where the DSP differs from a textbook DSP pipeline
//! ---------------------------------------------------
//! Envelope extraction is half-wave-rectified + low-passed — what
//! inner hair cells actually do. We use a one-pole IIR for the
//! low-pass (cheap, causal, biologically realistic). The local
//! floor that the onset threshold rides on top of is an
//! asymmetric tracker — latches fast on dips, decays slow up.
//! Mirrors how real auditory neurons adapt their thresholds.

use crate::graph::NodeID;
use crate::substrate::Substrate;
use crate::sym::Sym;
use crate::value::Value;
use rustc_hash::FxHashMap;
use smallvec::SmallVec;

#[derive(Debug, Clone, Copy)]
pub struct CnConfig {
    /// Low-pass cutoff for envelope extraction (Hz). Speech-relevant
    /// envelope modulations live <50 Hz; 50 Hz is the conservative
    /// default.
    pub envelope_lp_hz: f32,
    /// Minimum dB rise (above the local floor) to count as an
    /// onset. Larger = fewer false positives, more missed weak
    /// onsets.
    pub onset_threshold_db: f32,
    /// Minimum spacing between consecutive onsets in one band.
    /// Real cochlear-nucleus cells have a recovery period; we
    /// enforce one to suppress re-fires on the same transient.
    pub onset_refractory_ms: f32,
    /// Fraction of bands that must fire within `broadband_window_ms`
    /// to count as a broadband onset (octopus-cell event).
    pub broadband_coincidence: f32,
    /// Time window for cross-band coincidence.
    pub broadband_window_ms: f32,
}

impl Default for CnConfig {
    fn default() -> Self {
        Self {
            envelope_lp_hz: 50.0,
            onset_threshold_db: 6.0,
            onset_refractory_ms: 30.0,
            broadband_coincidence: 0.4,
            broadband_window_ms: 25.0,
        }
    }
}

#[derive(Debug, Clone, Copy, Default)]
pub struct CnSummary {
    pub onsets: usize,
    pub envelopes: usize,
    pub broadband: usize,
}

// --- DSP primitives ----------------------------------------------------

/// One gammatone band — FIR built from the cookbook impulse response
/// t^(n-1) * exp(-bt) * cos(2π fc t), then convolved against the
/// input. Mirrors substrate_rs.audio.gammatone's filter but
/// evaluated inline (no AudioBuffer round-trip).
fn gammatone_band(samples: &[f32], fs: u32, fc: f32, order: u32) -> Vec<f32> {
    let fs_f = fs as f32;
    let n_taps = 256usize;
    // ERB scale: b = 2π * 1.019 * (24.7 + 0.108 * fc)
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
    // Normalise.
    let energy: f32 = impulse.iter().map(|x| x * x).sum::<f32>().sqrt();
    // The raw impulse energy can be ~1e-11 at high fc (the
    // gammatone amplitude is tiny but the relative shape is
    // intact). Don't gate the normalisation on a fixed threshold
    // — only skip if energy is literally zero, which would mean
    // an all-zero impulse (impossible by construction).
    if energy > 0.0 {
        for v in impulse.iter_mut() {
            *v /= energy;
        }
    }
    convolve_same(samples, &impulse)
}

/// Discrete convolution in `mode="same"` — output length matches
/// input length, centred. Naive O(NM); fine at 256-tap kernel size.
fn convolve_same(x: &[f32], h: &[f32]) -> Vec<f32> {
    let n = x.len();
    let m = h.len();
    let pad = m / 2;
    let mut out = vec![0.0f32; n];
    for i in 0..n {
        let mut acc = 0.0f32;
        for k in 0..m {
            let xi = i as isize + k as isize - pad as isize;
            if xi >= 0 && (xi as usize) < n {
                acc += x[xi as usize] * h[k];
            }
        }
        out[i] = acc;
    }
    out
}

/// Half-wave rectify + IIR low-pass = the cochlear-nerve envelope.
/// Matches what inner hair cells do — they release neurotransmitter
/// only on positive cell-membrane swings, then their post-synaptic
/// targets integrate.
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
        let rectified = if v > 0.0 { v } else { 0.0 };
        y += alpha * (rectified - y);
        out.push(y);
    }
    out
}

/// Detect onsets in one band's envelope. Returns
/// (sample_index, dB-above-floor) per onset. The local floor adapts
/// asymmetrically — latches on dips, decays slowly upward — which
/// mirrors how auditory neurons track quiet background.
fn detect_onsets(
    envelope: &[f32],
    fs: u32,
    threshold_db: f32,
    refractory_ms: f32,
) -> Vec<(usize, f32)> {
    if envelope.is_empty() {
        return Vec::new();
    }
    let eps = 1e-10f32;
    let floor_win = (0.2 * fs as f32).max(1.0) as usize;

    // Pass 1: per-sample floor.
    let mut floor = vec![0.0f32; envelope.len()];
    let mut running = envelope[0].max(0.0) + eps;
    for (i, &v) in envelope.iter().enumerate() {
        let v = v.max(0.0);
        if v < running {
            running = v;
        } else {
            running += (v - running) / floor_win as f32;
        }
        floor[i] = running + eps;
    }

    // Pass 2: dB above floor, detect rising threshold crossings.
    let mut db = vec![0.0f32; envelope.len()];
    for i in 0..envelope.len() {
        let r = (envelope[i].max(0.0) + eps) / floor[i];
        db[i] = 20.0 * r.log10();
    }
    let refractory_samples = ((refractory_ms * 0.001) * fs as f32).max(1.0) as usize;
    let mut onsets = Vec::new();
    let mut last_idx: isize = -(refractory_samples as isize) - 1;
    for i in 1..db.len() {
        if db[i] >= threshold_db && db[i] > db[i - 1] {
            let idx = i as isize;
            if idx - last_idx < refractory_samples as isize {
                continue;
            }
            // Peak-pick within the window: walk while db rises.
            let mut peak = i;
            while peak + 1 < db.len()
                && db[peak + 1] > db[peak]
                && (peak - i) < refractory_samples
            {
                peak += 1;
            }
            onsets.push((peak, db[peak]));
            last_idx = peak as isize;
        }
    }
    onsets
}

// --- The main pass: buffer → graph nodes -------------------------------

pub fn process_audio(
    substrate: &mut Substrate,
    audio_stream_nid: NodeID,
    samples: &[f32],
    sample_rate: u32,
    band_centres: &[f32],
    config: &CnConfig,
) -> CnSummary {
    let n_bands = band_centres.len();
    let mut envelopes: Vec<Vec<f32>> = Vec::with_capacity(n_bands);
    for &fc in band_centres {
        let band = gammatone_band(samples, sample_rate, fc, 4);
        let env = hair_cell_envelope(&band, config.envelope_lp_hz, sample_rate);
        envelopes.push(env);
    }

    // Intern the type / edge symbols once.
    let envelope_t = substrate.interner.intern("EnvelopeChannel");
    let onset_t = substrate.interner.intern("OnsetEvent");
    let broadband_t = substrate.interner.intern("BroadbandOnset");
    let has_envelope_e = substrate.interner.intern("has_envelope");
    let has_onset_e = substrate.interner.intern("has_onset_event");
    let has_broadband_e = substrate.interner.intern("has_broadband_onset");
    let contributed_by_e = substrate.interner.intern("contributed_by");

    let mut summary = CnSummary::default();

    // Mint EnvelopeChannel nodes (one per band) + edges from the
    // stream. We don't ship the full envelope sample-array on the
    // node (it would balloon attr size); a summary (peak, mean)
    // is enough for downstream queries. The samples themselves
    // are recomputable from the audio + band centres.
    for (band_i, env) in envelopes.iter().enumerate() {
        let mut attrs = mk_attrs(substrate);
        attr_set(&mut attrs, substrate, "band_index", Value::Int(band_i as i64));
        attr_set(&mut attrs, substrate, "centre_hz", Value::Float(band_centres[band_i] as f64));
        attr_set(&mut attrs, substrate, "sample_rate", Value::Int(sample_rate as i64));
        attr_set(&mut attrs, substrate, "n_samples", Value::Int(env.len() as i64));
        let peak = env.iter().cloned().fold(0.0f32, f32::max);
        let mean = if env.is_empty() {
            0.0
        } else {
            env.iter().sum::<f32>() / env.len() as f32
        };
        attr_set(&mut attrs, substrate, "peak", Value::Float(peak as f64));
        attr_set(&mut attrs, substrate, "mean", Value::Float(mean as f64));
        let nid = substrate.add_node(envelope_t, attrs);
        let _ = substrate.graph.insert_edge(
            audio_stream_nid,
            has_envelope_e,
            nid,
            FxHashMap::default(),
        );
        summary.envelopes += 1;
    }

    // Per-band onset detection.
    let mut all_onsets: Vec<(usize, usize, f32)> = Vec::new(); // (band_i, sample, magnitude_db)
    for (band_i, env) in envelopes.iter().enumerate() {
        for (sample, mag) in detect_onsets(
            env,
            sample_rate,
            config.onset_threshold_db,
            config.onset_refractory_ms,
        ) {
            all_onsets.push((band_i, sample, mag));
        }
    }
    all_onsets.sort_by_key(|r| (r.1, r.0));

    // Mint OnsetEvent nodes (time-ordered).
    let mut onset_node_by_record: Vec<NodeID> = Vec::with_capacity(all_onsets.len());
    for &(band_i, sample, mag) in &all_onsets {
        let t_s = sample as f64 / sample_rate as f64;
        let mut attrs = mk_attrs(substrate);
        attr_set(&mut attrs, substrate, "time_s", Value::Float(t_s));
        attr_set(&mut attrs, substrate, "band_index", Value::Int(band_i as i64));
        attr_set(&mut attrs, substrate, "centre_hz", Value::Float(band_centres[band_i] as f64));
        attr_set(&mut attrs, substrate, "magnitude_db", Value::Float(mag as f64));
        let nid = substrate.add_node(onset_t, attrs);
        let _ = substrate.graph.insert_edge(
            audio_stream_nid,
            has_onset_e,
            nid,
            FxHashMap::default(),
        );
        onset_node_by_record.push(nid);
        summary.onsets += 1;
    }

    // Cross-band coincidence — BroadbandOnset nodes per cluster.
    if !all_onsets.is_empty() {
        let window_samples =
            ((config.broadband_window_ms * 0.001) * sample_rate as f32).max(1.0) as i64;
        let min_bands = (config.broadband_coincidence * n_bands as f32)
            .round()
            .max(2.0) as usize;

        let mut i = 0usize;
        while i < all_onsets.len() {
            let start_sample = all_onsets[i].1 as i64;
            let mut j = i + 1;
            while j < all_onsets.len()
                && (all_onsets[j].1 as i64) - start_sample <= window_samples
            {
                j += 1;
            }
            // Members are indices i..j; count distinct bands.
            let mut bands_seen: SmallVec<[usize; 16]> = SmallVec::new();
            for k in i..j {
                let band = all_onsets[k].0;
                if !bands_seen.contains(&band) {
                    bands_seen.push(band);
                }
            }
            if bands_seen.len() >= min_bands {
                let mean_sample: f64 = (i..j)
                    .map(|k| all_onsets[k].1 as f64)
                    .sum::<f64>()
                    / (j - i) as f64;
                let total_mag: f64 = (i..j).map(|k| all_onsets[k].2 as f64).sum();
                let mut attrs = mk_attrs(substrate);
                attr_set(
                    &mut attrs,
                    substrate,
                    "time_s",
                    Value::Float(mean_sample / sample_rate as f64),
                );
                attr_set(
                    &mut attrs,
                    substrate,
                    "n_bands",
                    Value::Int(bands_seen.len() as i64),
                );
                attr_set(
                    &mut attrs,
                    substrate,
                    "n_member_onsets",
                    Value::Int((j - i) as i64),
                );
                attr_set(
                    &mut attrs,
                    substrate,
                    "total_magnitude_db",
                    Value::Float(total_mag),
                );
                let broad_nid = substrate.add_node(broadband_t, attrs);
                let _ = substrate.graph.insert_edge(
                    audio_stream_nid,
                    has_broadband_e,
                    broad_nid,
                    FxHashMap::default(),
                );
                for k in i..j {
                    let _ = substrate.graph.insert_edge(
                        broad_nid,
                        contributed_by_e,
                        onset_node_by_record[k],
                        FxHashMap::default(),
                    );
                }
                summary.broadband += 1;
            }
            i = if j > i { j } else { i + 1 };
        }
    }

    summary
}

// --- attr helpers ------------------------------------------------------

fn mk_attrs(_sub: &Substrate) -> FxHashMap<Sym, Value> {
    FxHashMap::default()
}

fn attr_set(
    attrs: &mut FxHashMap<Sym, Value>,
    substrate: &mut Substrate,
    key: &str,
    v: Value,
) {
    let k = substrate.interner.intern(key);
    attrs.insert(k, v);
}
