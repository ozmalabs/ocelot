//! Audio-pathway primitives — pure Rust functions, no graph state.
//!
//! Per CLAUDE.md, primitives in Rust + composition in graph. This
//! module is the primitive layer the auditory pipeline runtime
//! dispatches into. Each function is a single named operation
//! (gammatone band filter, envelope extraction, onset detection,
//! cross-band coincidence) callable from any pipeline node whose
//! `kind` matches.
//!
//! Nothing here touches the substrate. All graph mutation happens
//! in `pipeline_runtime.rs` after these primitives return.

use rustfft::num_complex::Complex;

// --- gammatone -------------------------------------------------------------

/// One gammatone band: t^(n-1) · exp(-bt) · cos(2π fc t), unit-L2
/// normalised, convolved against the input ("same" mode).
pub fn gammatone_band(samples: &[f32], fs: u32, fc: f32, order: u32) -> Vec<f32> {
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
    // Don't gate on a magnitude threshold — high-fc impulses have
    // legitimately tiny unnormalised energy (~1e-11). Only guard
    // against literal zero (impossible by construction here).
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

// --- hair-cell envelope ---------------------------------------------------

/// Half-wave rectify + one-pole IIR low-pass. What inner hair cells
/// actually do — they release neurotransmitter only on positive
/// cell-membrane swings; post-synaptic targets integrate.
pub fn hair_cell_envelope(band: &[f32], cutoff_hz: f32, fs: u32) -> Vec<f32> {
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

// --- temporal fine structure (phase-locking the envelope throws away) ----

/// Short-time autocorrelation of ONE gammatone band's *fine waveform*
/// (NOT its envelope). This is the temporal/rate code the auditory
/// nerve carries by phase-locking: the inner hair cell's envelope
/// (`hair_cell_envelope`) discards the sub-millisecond timing, but the
/// periodicity of the fine structure within a band is exactly where
/// F0, voicing periodicity, and the periodic-vs-aperiodic distinction
/// live. We recover it by autocorrelating the band waveform in a
/// sliding window and reading the lag of the dominant peak.
///
/// Returns, per analysis frame (hop `hop` samples, window `win`
/// samples), a flat row-major buffer of `n_lags` normalised
/// autocorrelation coefficients per frame (the within-band running
/// autocorrelation, a.k.a. the inter-spike-interval histogram of an
/// idealised phase-locked fibre). `n_lags` is `max_lag` (inclusive of
/// lag 0). This is the place code's missing time-domain sibling.
///
/// Output layout: frame 0's lags [0..n_lags), then frame 1's, ...
/// `n_frames` is `(len - win) / hop + 1` (>=1 when len>=win, else 0).
pub fn band_autocorr(band: &[f32], win: usize, hop: usize, max_lag: usize) -> Vec<f32> {
    if win == 0 || hop == 0 || max_lag == 0 || band.len() < win {
        return Vec::new();
    }
    let n_lags = max_lag + 1;
    let n_frames = (band.len() - win) / hop + 1;
    let mut out: Vec<f32> = Vec::with_capacity(n_frames * n_lags);
    let mut start = 0usize;
    while start + win <= band.len() {
        let frame = &band[start..start + win];
        // Energy at lag 0 (the normaliser); guard against silence.
        let r0: f32 = frame.iter().map(|&x| x * x).sum::<f32>().max(1e-12);
        for lag in 0..n_lags {
            let mut acc = 0.0f32;
            // Unbiased-ish: correlate overlapping span.
            let span = win.saturating_sub(lag);
            for i in 0..span {
                acc += frame[i] * frame[i + lag];
            }
            // Normalise by lag-0 energy → coefficient in [-1, 1].
            out.push(acc / r0);
        }
        start += hop;
    }
    out
}

/// Summary autocorrelogram (Licklider 1951 / Meddis-Hewitt pitch
/// model): pool the per-band running autocorrelations across ALL
/// cochlear bands into one lag profile per frame. A periodicity common
/// across bands (a voiced pitch, the F0) shows up as a strong pooled
/// peak at its period lag; aperiodic energy (frication) does not. This
/// is the temporal-code analogue of summing the place code — a
/// pitch/voicing readout that survives the level/spectral-tilt
/// differences between bands.
///
/// `band_acs` is a slice of per-band autocorrelogram buffers (each the
/// output of `band_autocorr` with the SAME `win`/`hop`/`max_lag`).
/// `n_lags` = `max_lag + 1`. Returns a flat `n_frames × n_lags`
/// row-major buffer: the summed (and per-frame peak-normalised) lag
/// profile. Bands with mismatched frame counts are tolerated by
/// summing over the common frame count.
pub fn summary_autocorrelogram(band_acs: &[&[f32]], n_lags: usize) -> Vec<f32> {
    if band_acs.is_empty() || n_lags == 0 {
        return Vec::new();
    }
    // Common frame count across bands.
    let mut n_frames = usize::MAX;
    for ac in band_acs {
        let frames = ac.len() / n_lags;
        if frames < n_frames {
            n_frames = frames;
        }
    }
    if n_frames == 0 || n_frames == usize::MAX {
        return Vec::new();
    }
    let mut out = vec![0.0f32; n_frames * n_lags];
    for ac in band_acs {
        for f in 0..n_frames {
            let base = f * n_lags;
            for l in 0..n_lags {
                out[base + l] += ac[base + l];
            }
        }
    }
    // Per-frame peak normalisation over lags>=1 (lag 0 is always the
    // self-energy max and carries no pitch information).
    for f in 0..n_frames {
        let base = f * n_lags;
        let mut peak = 1e-12f32;
        for l in 1..n_lags {
            if out[base + l] > peak {
                peak = out[base + l];
            }
        }
        for l in 0..n_lags {
            out[base + l] /= peak;
        }
    }
    out
}

/// Voicing / periodicity strength per frame from a summary
/// autocorrelogram: the height of the strongest pooled peak at a lag
/// in the pitch-plausible range `[min_lag, max_lag]`, and the lag of
/// that peak. A strong, well-defined peak = voiced/periodic; a flat
/// profile = aperiodic (frication, silence). Returns one
/// `(periodicity_strength, period_lag)` pair per frame.
///
/// This is the readout the perception front end actually wants from
/// TFS: a clean periodic-vs-aperiodic axis (manner/voicing) and an F0
/// estimate, both carried in the timing the envelope discarded.
pub fn periodicity_track(
    sacf: &[f32],
    n_lags: usize,
    min_lag: usize,
    max_lag: usize,
) -> Vec<(f32, usize)> {
    if sacf.is_empty() || n_lags == 0 {
        return Vec::new();
    }
    let n_frames = sacf.len() / n_lags;
    let lo = min_lag.max(1);
    let hi = max_lag.min(n_lags.saturating_sub(1));
    let mut out = Vec::with_capacity(n_frames);
    for f in 0..n_frames {
        let base = f * n_lags;
        let mut best = 0.0f32;
        let mut best_lag = 0usize;
        let mut l = lo;
        while l <= hi {
            let v = sacf[base + l];
            if v > best {
                best = v;
                best_lag = l;
            }
            l += 1;
        }
        out.push((best, best_lag));
    }
    out
}

// --- onset detection (envelope → discrete events) ------------------------

/// Detect onset events in one envelope. Returns
/// `(sample_index, magnitude_db_above_floor)` per onset.
///
/// The local floor adapts asymmetrically — latches on dips, decays
/// slowly upward — which mirrors how auditory neurons track quiet
/// background.
pub fn detect_onsets(
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

// --- IIR bandpass --------------------------------------------------------

/// RBJ-cookbook constant-skirt-gain bandpass IIR around `fc`,
/// quality factor `q`. Used to extract a specific modulation-rate
/// channel from an envelope signal.
pub fn bandpass(input: &[f32], fs: u32, fc: f32, q: f32) -> Vec<f32> {
    let fs_f = fs as f32;
    let omega = 2.0 * std::f32::consts::PI * fc / fs_f;
    let (sin_o, cos_o) = (omega.sin(), omega.cos());
    let alpha = sin_o / (2.0 * q.max(0.001));
    let b0 = alpha;
    let b2 = -alpha;
    let a0 = 1.0 + alpha;
    let a1 = -2.0 * cos_o;
    let a2 = 1.0 - alpha;
    let bb0 = b0 / a0;
    let bb2 = b2 / a0;
    let aa1 = a1 / a0;
    let aa2 = a2 / a0;
    let mut out = Vec::with_capacity(input.len());
    let mut x1 = 0.0f32;
    let mut x2 = 0.0f32;
    let mut y1 = 0.0f32;
    let mut y2 = 0.0f32;
    for &x in input {
        // b1 = 0 for this filter family — skip it.
        let y = bb0 * x + bb2 * x2 - aa1 * y1 - aa2 * y2;
        out.push(y);
        x2 = x1;
        x1 = x;
        y2 = y1;
        y1 = y;
    }
    out
}

// --- rectified low-pass (envelope-of-envelope) ---------------------------

/// Full-wave rectify + one-pole IIR LPF. The "envelope of an
/// envelope" — turns a band-passed AC signal into a slow energy
/// signal that peak-picking can act on cleanly. Differs from
/// `hair_cell_envelope` only in using full-wave rectification (the
/// hair-cell model is half-wave).
pub fn rectified_lpf(input: &[f32], fs: u32, cutoff_hz: f32) -> Vec<f32> {
    let alpha = if cutoff_hz <= 0.0 {
        1.0
    } else {
        let tau = 1.0 / (2.0 * std::f32::consts::PI * cutoff_hz);
        1.0 / (1.0 + tau * fs as f32)
    };
    let mut out = Vec::with_capacity(input.len());
    let mut y = 0.0f32;
    for &v in input {
        let r = v.abs();
        y += alpha * (r - y);
        out.push(y);
    }
    out
}

// --- adaptive-floor dB ---------------------------------------------------

/// Convert a signal to dB-above-local-floor with an asymmetric
/// tracker that latches on dips, decays slowly upward. Mirrors how
/// auditory neurons adapt to background.
pub fn floor_dbs(signal: &[f32], fs: u32) -> Vec<f32> {
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

// --- Schmitt-trigger peak-pick -------------------------------------------

/// One peak per crossing-region. When the signal rises above
/// `threshold`, start tracking the maximum; when it drops back
/// below `threshold * 0.7` (hysteresis), emit the in-region max.
/// `refractory_samples` enforces a hard minimum gap between
/// consecutive events.
pub fn schmitt_peaks(
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

// --- A1 patch evaluation -------------------------------------------------

#[derive(Debug, Clone)]
pub struct PatchKernel {
    pub centre_hz: f32,
    pub freq_sigma_hz: f32,
    pub duration_ms: f32,
    pub slope_hz_per_ms: f32,
    pub kind: String, // "sustained" | "burst" | "fm"
}

/// Gaussian weight on a band centre under a stationary patch.
fn freq_weight(band_centre: f32, patch_centre: f32, sigma: f32) -> f32 {
    let s = sigma.max(1.0);
    let d = band_centre - patch_centre;
    (-(d * d) / (2.0 * s * s)).exp()
}

/// Evaluate one A1 patch against a set of cochlear band envelopes.
/// Returns the response signal over time (Audio buffer).
///
/// * Sustained / burst patches: a stationary Gaussian over band
///   frequency × time, evaluated as a weighted sum of envelopes
///   smoothed by a one-pole LPF whose cutoff matches the patch's
///   `duration_ms`.
/// * FM patches: the frequency weight shifts linearly with t to
///   follow the patch's slope (rising / falling spectral
///   centroid).
pub fn patch_evaluate(
    envelopes: &[&[f32]],
    band_centres: &[f32],
    fs: u32,
    patch: &PatchKernel,
) -> Vec<f32> {
    let n = envelopes.first().map(|e| e.len()).unwrap_or(0);
    if n == 0 || envelopes.is_empty() {
        return Vec::new();
    }
    let mut combined = vec![0.0f32; n];

    if patch.kind == "fm" && patch.slope_hz_per_ms.abs() > 1e-6 {
        let slope_per_sample = patch.slope_hz_per_ms / (fs as f32 / 1000.0);
        let mid_t = n as f32 / 2.0;
        for t in 0..n {
            let dt = t as f32 - mid_t;
            let centre_t = patch.centre_hz + slope_per_sample * dt;
            let mut sum = 0.0f32;
            for (band_i, env) in envelopes.iter().enumerate() {
                let w = freq_weight(band_centres[band_i], centre_t,
                                      patch.freq_sigma_hz);
                sum += w * env[t];
            }
            combined[t] = sum;
        }
    } else {
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

    // Temporal integration matched to patch duration:
    // cutoff = 1 / (2π · duration_ms)
    let cutoff_hz = if patch.duration_ms > 1.0 {
        1000.0 / (2.0 * std::f32::consts::PI * patch.duration_ms)
    } else {
        50.0
    };
    // Re-use the one-pole LPF shape (no rectification — patch
    // responses can be negative for FM patches, but for typical
    // sustained/burst patches the envelopes are non-negative).
    let alpha = if cutoff_hz <= 0.0 {
        1.0
    } else {
        let tau = 1.0 / (2.0 * std::f32::consts::PI * cutoff_hz);
        1.0 / (1.0 + tau * fs as f32)
    };
    let mut out = Vec::with_capacity(n);
    let mut y = 0.0f32;
    for &v in &combined {
        y += alpha * (v - y);
        out.push(y);
    }
    out
}

// --- source-filter voicebox ----------------------------------------------

/// 2nd-order RBJ-cookbook bandpass biquad applied in-place to `x`.
/// Constant-skirt, peak gain ~ Q. Used as a single-formant filter
/// over a glottal-pulse or noise source.
fn biquad_bandpass(x: &mut [f32], fs: u32, centre_hz: f32, q: f32) {
    let omega = 2.0 * std::f32::consts::PI * centre_hz / (fs as f32);
    let alpha = omega.sin() / (2.0 * q);
    let cos_o = omega.cos();
    let a0 = 1.0 + alpha;
    let b0 = alpha / a0;
    let b1 = 0.0f32;
    let b2 = -alpha / a0;
    let a1 = (-2.0 * cos_o) / a0;
    let a2 = (1.0 - alpha) / a0;
    let mut x1 = 0.0f32;
    let mut x2 = 0.0f32;
    let mut y1 = 0.0f32;
    let mut y2 = 0.0f32;
    for i in 0..x.len() {
        let xn = x[i];
        let yn = b0 * xn + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2;
        x[i] = yn;
        x2 = x1;
        x1 = xn;
        y2 = y1;
        y1 = yn;
    }
}

/// One per-patch synthesis directive: which centre frequency, how
/// it modulates, and which source to filter.
#[derive(Debug, Clone)]
pub struct VoiceboxPatch {
    pub centre_hz: f32,
    /// Spectral width of the patch — used to derive the formant
    /// filter Q. The cochlear / A1 analysis-time patches are
    /// Gaussian-shaped in frequency; matching the synthesis-time
    /// Q to the patch's sigma reproduces the patch's actual band.
    /// Fixed Q=4 (the previous default) made formant filters
    /// way too narrow for natural speech.
    pub freq_sigma_hz: f32,
    /// "burst" / "sustained" / "fm" — kind drives source pick.
    pub kind: String,
    /// True if patch name contains "sib" — pushes to noise source.
    pub is_sibilant: bool,
}

/// Synthesize audio for one AcousticSign via source-filter voicebox.
///
/// * `traj_flat` — the sign's stored trajectory: a concatenation of
///   `patches.len()` channels, each `spp` floats long.
/// * `patches` — per-channel formant parameters in the same order
///   the trajectory was built (alphabetical by patch name, matching
///   `lexical_access`).
/// * `output_samples` / `fs` — desired output length + sample rate.
/// * `f0_hz` — base voicing pitch (typical male ~120, female ~210).
/// * `q_factor` — formant filter sharpness; ~4 gives speech-like
///   resonance.
///
/// Voiced source: harmonic stack at f0 with -3dB-per-octave tilt.
/// Noise source: deterministic LCG so a given sign synthesises the
/// same audio each time (reproducibility). Per-patch formant
/// bandpasses route the appropriate source, multiply by the
/// resampled envelope channel, and accumulate. Attack/release ramp
/// + peak-normalise applied last.
pub fn synthesize_from_trajectory(
    traj_flat: &[f32],
    patches: &[VoiceboxPatch],
    spp: usize,
    output_samples: usize,
    fs: u32,
    f0_hz: f32,
    // q_clamp_max: per-patch Q is derived as centre_hz / (2 * sigma);
    // clamped to [0.5, q_clamp_max] so very-narrow patches don't ring.
    // ~6 is the upper end of natural-formant Q.
    q_clamp_max: f32,
) -> Vec<f32> {
    let n_patches = patches.len();
    if n_patches == 0
        || spp == 0
        || output_samples == 0
        || traj_flat.len() < n_patches * spp
    {
        return vec![0.0; output_samples];
    }

    // Build voiced source: sum of harmonics at f0 with 1/k amplitude.
    let mut voiced = vec![0.0f32; output_samples];
    let fs_f = fs as f32;
    let mut k = 1usize;
    while (k as f32) * f0_hz < fs_f / 2.0 && k < 40 {
        let omega = 2.0 * std::f32::consts::PI * (k as f32) * f0_hz / fs_f;
        let amp = 0.3 / (k as f32);
        for n in 0..output_samples {
            voiced[n] += amp * (omega * n as f32).sin();
        }
        k += 1;
    }

    // Noise source — deterministic LCG seeded by a hash of patch
    // centres so repeated synthesis of the same sign is identical.
    let seed: u64 = patches
        .iter()
        .map(|p| (p.centre_hz as u64).wrapping_mul(0x9E3779B97F4A7C15))
        .fold(0xCAFE_BABE_DEAD_BEEFu64, |a, b| a.wrapping_add(b));
    let mut state = seed;
    let mut noise = vec![0.0f32; output_samples];
    for v in &mut noise {
        state = state.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        let u = (state >> 33) as u32; // upper 31 bits
        *v = 0.4 * (((u as f32) / (u32::MAX as f32)) * 2.0 - 1.0);
    }

    // Per-patch: resample envelope from spp → output_samples,
    // bandpass the source at centre_hz, multiply by envelope,
    // accumulate.
    let mut out = vec![0.0f32; output_samples];
    let denom = if spp > 1 { (spp - 1) as f32 } else { 1.0 };
    let out_denom = if output_samples > 1 {
        (output_samples - 1) as f32
    } else {
        1.0
    };
    for (i, patch) in patches.iter().enumerate() {
        let chan = &traj_flat[i * spp..(i + 1) * spp];
        // Resample chan -> output_samples via linear interpolation.
        let mut env = vec![0.0f32; output_samples];
        for n in 0..output_samples {
            let src_pos = (n as f32) * denom / out_denom;
            let lo = src_pos as usize;
            let hi = (lo + 1).min(spp - 1);
            let frac = src_pos - lo as f32;
            env[n] = chan[lo] * (1.0 - frac) + chan[hi] * frac;
        }
        // Pick source.
        let unvoiced = patch.kind == "burst"
            || patch.is_sibilant
            || patch.centre_hz > 3500.0;
        let mut filt: Vec<f32> = if unvoiced {
            noise.clone()
        } else {
            voiced.clone()
        };
        // Per-patch Q: bandwidth (Hz) ≈ 2 * sigma → Q = centre / bw.
        // Clamp so very-narrow patches don't ring; clamp_max keeps
        // numeric stability + matches real formant Q (~2-6).
        let sigma = patch.freq_sigma_hz.max(50.0);
        let bw = (2.0 * sigma).max(50.0);
        let q = (patch.centre_hz / bw).clamp(0.5, q_clamp_max);
        biquad_bandpass(&mut filt, fs, patch.centre_hz, q);
        for n in 0..output_samples {
            out[n] += filt[n] * env[n];
        }
    }

    // Attack / release ramp.
    let ramp_n = ((0.015 * fs_f) as usize).min(output_samples / 4);
    if ramp_n > 1 {
        for i in 0..ramp_n {
            let r = i as f32 / ramp_n as f32;
            out[i] *= r;
            out[output_samples - 1 - i] *= r;
        }
    }
    // Peak-normalise to [-0.9, 0.9].
    let peak = out.iter().fold(0.0f32, |a, &b| a.max(b.abs()));
    if peak > 0.0 {
        let scale = 0.9 / peak;
        for v in &mut out {
            *v *= scale;
        }
    }
    out
}

// --- Klatt cascade + Liljencrants-Fant glottal source --------------------
//
// The upgraded forward model (iter-40). Three things the crude voicebox above
// lacks, plus a physically-shaped source:
//
//   * KLATT CASCADE resonators — a chain of 2-pole resonators (the same biquad
//     family as `biquad_bandpass`, here as direct-form-II all-pole resonators
//     `R(z) = 1 / (1 - 2 e^{-πB/fs} cos(2π F/fs) z^-1 + e^{-2πB/fs} z^-2}`).
//     Routed IN SERIES, so the inter-formant amplitude relations fall out of the
//     transfer function automatically — unlike the independent parallel
//     bandpasses above which lose them. This is Klatt (1980) §II.
//   * ANTI-RESONANCE (zero) — a 2-pole-2-zero antiresonator for nasal murmur,
//     which an all-pole / all-bandpass voicebox cannot represent.
//   * PER-FORMANT BANDWIDTH control + a TWO-SOURCE (voiced LF + unvoiced
//     aspiration/frication) mix, instead of the centre>3500Hz heuristic.
//   * LF (Liljencrants-Fant) GLOTTAL SOURCE — the parametric glottal-flow
//     DERIVATIVE replacing the 0.3/k harmonic stack. Carries open-quotient +
//     spectral-tilt (voice-quality) structure = the per-speaker voice identity.
//
// All pure closed-form DSP. No weights, no fit, no trained net.

/// A single two-pole Klatt resonator section, run in cascade. Coefficients
/// from formant frequency F and bandwidth B (Hz) per Klatt (1980):
///   C = -exp(-2π B / fs),  B_coef = 2 exp(-π B / fs) cos(2π F / fs),
///   A = 1 - B_coef - C,    y[n] = A x[n] + B_coef y[n-1] + C y[n-2].
/// A normalises DC gain to 1 so cascaded sections do not blow up.
struct KlattResonator {
    a: f32,
    b: f32,
    c: f32,
    y1: f32,
    y2: f32,
}

impl KlattResonator {
    fn new(f_hz: f32, bw_hz: f32, fs: f32) -> Self {
        let mut r = KlattResonator { a: 1.0, b: 0.0, c: 0.0, y1: 0.0, y2: 0.0 };
        r.set(f_hz, bw_hz, fs);
        r
    }
    /// Update the resonator coefficients to a new formant/bandwidth WITHOUT
    /// resetting the filter state (y1,y2) — used to track moving formants across
    /// frames so the cascade output stays continuous.
    #[inline]
    fn set(&mut self, f_hz: f32, bw_hz: f32, fs: f32) {
        let f = f_hz.clamp(20.0, fs / 2.0 * 0.98);
        let bw = bw_hz.max(20.0);
        let c = -(-2.0 * std::f32::consts::PI * bw / fs).exp();
        let b = 2.0 * (-std::f32::consts::PI * bw / fs).exp()
            * (2.0 * std::f32::consts::PI * f / fs).cos();
        self.a = 1.0 - b - c;
        self.b = b;
        self.c = c;
    }
    #[inline]
    fn step(&mut self, x: f32) -> f32 {
        let y = self.a * x + self.b * self.y1 + self.c * self.y2;
        self.y2 = self.y1;
        self.y1 = y;
        y
    }
}

/// A two-pole-two-zero anti-resonator (nasal zero) per Klatt (1980): the
/// inverse-form of the resonator — zeros at the antiresonance F/BW, poles at
/// DC-normalising positions. Implements the nasal murmur an all-pole tract
/// cannot. y[n] = A' x[n] + B' x[n-1] + C' x[n-2], with the resonator coeffs
/// of the antiformant inverted (A' = 1/A, B' = -B/A, C' = -C/A).
struct KlattAntiResonator {
    ap: f32,
    bp: f32,
    cp: f32,
    x1: f32,
    x2: f32,
}

impl KlattAntiResonator {
    fn new(f_hz: f32, bw_hz: f32, fs: f32) -> Self {
        let f = f_hz.clamp(20.0, fs / 2.0 * 0.98);
        let bw = bw_hz.max(20.0);
        let c = -(-2.0 * std::f32::consts::PI * bw / fs).exp();
        let b = 2.0 * (-std::f32::consts::PI * bw / fs).exp()
            * (2.0 * std::f32::consts::PI * f / fs).cos();
        let a = 1.0 - b - c;
        let ainv = if a.abs() > 1e-9 { 1.0 / a } else { 1.0 };
        KlattAntiResonator {
            ap: ainv,
            bp: -b * ainv,
            cp: -c * ainv,
            x1: 0.0,
            x2: 0.0,
        }
    }
    #[inline]
    fn step(&mut self, x: f32) -> f32 {
        let y = self.ap * x + self.bp * self.x1 + self.cp * self.x2;
        self.x2 = self.x1;
        self.x1 = x;
        y
    }
}

/// LF (Liljencrants-Fant) glottal-flow DERIVATIVE for one pitch period of
/// length `period` samples. Parametrised by:
///   oq  — open quotient (Te/T0), fraction of the period the glottis is open
///         (~0.5 modal, larger = breathier);
///   am  — asymmetry / speed quotient shaping (Tp/Te), peak position within the
///         open phase (~0.7);
///   ta  — return-phase time-constant as a fraction of the period (spectral
///         tilt: larger ta = steeper high-frequency roll-off = softer voice).
/// Returns one period of the glottal-flow derivative (the excitation), L2-ish
/// scaled. Pure closed-form: the open phase is the classic
/// E0 e^{αt} sin(ω_g t) growing sinusoid to the negative peak at Te, then an
/// exponential return e^{-(t-Te)/Ta} to closure. No fit.
fn lf_glottal_period(period: usize, oq: f32, am: f32, ta_frac: f32) -> Vec<f32> {
    let mut g = vec![0.0f32; period.max(1)];
    if period < 4 {
        return g;
    }
    let t0 = period as f32;
    let te = (oq.clamp(0.3, 0.9) * t0).max(2.0); // instant of max excitation (open phase end)
    let tp = (am.clamp(0.55, 0.9) * te).max(1.0); // instant of glottal-flow peak
    let ta = (ta_frac.clamp(0.002, 0.2) * t0).max(0.5); // return-phase time-constant
    // Open-phase growing sinusoid g'(t) = E0 e^{α t} sin(ω_g t), ω_g = π / Tp.
    let wg = std::f32::consts::PI / tp;
    // α from continuity of the LF model (area balance approximation): choose α so
    // the sinusoid reaches its negative peak (the excitation) at Te. A standard
    // closed-form choice α = -ln(0.01) / Te gives a moderate growth; we use the
    // (zero-fit) geometric relation α = (1/Te) * ln(Ee_ratio) with Ee_ratio set
    // by the speed/asymmetry so different voices differ. Keep it bounded.
    let alpha = (-(0.5f32).ln()) / te; // growth s.t. amplitude doubles over open phase
    // Return phase exponential coefficient (closure).
    let eps = 1.0 / ta;
    let mut peak = 1e-6f32;
    for n in 0..period {
        let t = n as f32;
        let v = if t <= te {
            (alpha * t).exp() * (wg * t).sin()
        } else {
            // Return phase: smooth exponential recovery from the -Ee at Te to 0.
            let ee = (alpha * te).exp() * (wg * te).sin();
            ee * (-eps * (t - te)).exp()
        };
        g[n] = v;
        if v.abs() > peak {
            peak = v.abs();
        }
    }
    // Normalise the period to unit peak so f0 / period changes do not change
    // overall level (level is handled by the envelope).
    let inv = 1.0 / peak;
    for v in &mut g {
        *v *= inv;
    }
    g
}

/// Build a full-length LF voiced excitation at f0 by concatenating LF periods.
/// f0 in Hz, fs the sample rate. oq/am/ta as in `lf_glottal_period`.
fn lf_source(output_samples: usize, fs: f32, f0_hz: f32, oq: f32, am: f32, ta_frac: f32) -> Vec<f32> {
    let mut out = vec![0.0f32; output_samples];
    if f0_hz <= 0.0 {
        return out;
    }
    let period = (fs / f0_hz).round().max(2.0) as usize;
    let one = lf_glottal_period(period, oq, am, ta_frac);
    let mut n = 0usize;
    while n < output_samples {
        for (j, &v) in one.iter().enumerate() {
            if n + j >= output_samples {
                break;
            }
            out[n + j] = v;
        }
        n += period;
    }
    out
}

/// Synthesize audio for one AcousticSign via the KLATT cascade + LF glottal
/// source (iter-40 upgraded forward model). Drop-in alternative to
/// `synthesize_from_trajectory` with the same trajectory/patch interface, plus
/// LF source params and a nasal antiformant.
///
/// Topology:
///   voiced LF source ──┐
///                      ├─► [cascade: R1 · R2 · … · Rk] · [nasal antiformant]
///   aspiration noise ──┘                                  ─► × overall envelope
///   (mixed per the voiced fraction of the trajectory)
///
/// The patches' centre frequencies become the cascade RESONATOR formant
/// frequencies (sorted ascending so the chain is F1<F2<…); each patch's sigma
/// sets that formant's BANDWIDTH (bw ≈ 2·sigma, clamped to natural 40–400 Hz).
/// The per-patch envelope channels are summed into one overall vocal-tract
/// excitation envelope (the cascade carries the *spectral* shaping; the envelope
/// carries the *temporal* one) and the voiced/unvoiced mix per frame is the
/// fraction of envelope energy in voiced (centre<3500, non-sibilant) patches.
///
/// `nasal_f` / `nasal_bw` > 0 inserts a nasal antiresonance (zero); 0 disables.
/// `oq` / `am` / `ta_frac` are the LF source shape (voice identity); defaults
/// 0.6 / 0.7 / 0.01 give a modal voice.
pub fn synthesize_klatt_lf(
    traj_flat: &[f32],
    patches: &[VoiceboxPatch],
    spp: usize,
    output_samples: usize,
    fs: u32,
    f0_hz: f32,
    oq: f32,
    am: f32,
    ta_frac: f32,
    nasal_f: f32,
    nasal_bw: f32,
) -> Vec<f32> {
    let n_patches = patches.len();
    if n_patches == 0
        || spp == 0
        || output_samples == 0
        || traj_flat.len() < n_patches * spp
    {
        return vec![0.0; output_samples];
    }
    let fs_f = fs as f32;
    let nyq = fs_f / 2.0 * 0.95;

    // --- two sources ---
    // Voiced: the LF glottal-flow derivative at f0 (physically-shaped, carries
    // voice identity), replacing the 0.3/k harmonic stack.
    let voiced = lf_source(output_samples, fs_f, f0_hz, oq, am, ta_frac);
    // Unvoiced: aspiration / frication noise (deterministic LCG, seeded from the
    // patch centres so synthesis is reproducible — same as the old voicebox).
    let seed: u64 = patches
        .iter()
        .map(|p| (p.centre_hz as u64).wrapping_mul(0x9E3779B97F4A7C15))
        .fold(0xCAFE_BABE_DEAD_BEEFu64, |a, b| a.wrapping_add(b));
    let mut state = seed;
    let mut noise = vec![0.0f32; output_samples];
    for v in &mut noise {
        state = state
            .wrapping_mul(6364136223846793005)
            .wrapping_add(1442695040888963407);
        let u = (state >> 33) as u32;
        *v = ((u as f32) / (u32::MAX as f32)) * 2.0 - 1.0;
    }

    // --- per-patch envelopes (resampled spp -> output_samples), and the
    // voiced/unvoiced split ---
    let denom = if spp > 1 { (spp - 1) as f32 } else { 1.0 };
    let out_denom = if output_samples > 1 { (output_samples - 1) as f32 } else { 1.0 };
    // Sort patches ascending by centre so the cascade is F1 < F2 < ... (cascade
    // ordering is what gives the correct inter-formant amplitude fall-off).
    let mut order: Vec<usize> = (0..n_patches).collect();
    order.sort_by(|&i, &j| {
        patches[i]
            .centre_hz
            .partial_cmp(&patches[j].centre_hz)
            .unwrap_or(std::cmp::Ordering::Equal)
    });

    // Build the overall excitation envelope (sum of all patch envelopes) and the
    // per-sample voiced-fraction (energy in voiced patches / total).
    let mut env_total = vec![0.0f32; output_samples];
    let mut env_voiced = vec![0.0f32; output_samples];
    for (i, patch) in patches.iter().enumerate() {
        let chan = &traj_flat[i * spp..(i + 1) * spp];
        let unvoiced =
            patch.kind == "burst" || patch.is_sibilant || patch.centre_hz > 3500.0;
        for n in 0..output_samples {
            let src_pos = (n as f32) * denom / out_denom;
            let lo = src_pos as usize;
            let hi = (lo + 1).min(spp - 1);
            let frac = src_pos - lo as f32;
            let e = chan[lo] * (1.0 - frac) + chan[hi] * frac;
            let mag = e.abs();
            env_total[n] += mag;
            if !unvoiced {
                env_voiced[n] += mag;
            }
        }
    }

    // --- mixed source per sample: voiced LF where the energy is voiced, noise
    // where it is fricative/burst ---
    let mut excitation = vec![0.0f32; output_samples];
    for n in 0..output_samples {
        let vf = if env_total[n] > 1e-9 {
            (env_voiced[n] / env_total[n]).clamp(0.0, 1.0)
        } else {
            1.0
        };
        excitation[n] = vf * voiced[n] + (1.0 - vf) * 0.4 * noise[n];
    }

    // --- the CASCADE: chain a resonator per formant, in ascending order ---
    let mut resonators: Vec<KlattResonator> = Vec::with_capacity(n_patches);
    for &idx in &order {
        let p = &patches[idx];
        let f = p.centre_hz.min(nyq);
        let bw = (2.0 * p.freq_sigma_hz.max(40.0)).clamp(40.0, 400.0);
        resonators.push(KlattResonator::new(f, bw, fs_f));
    }
    // Optional nasal antiresonance (zero) — Klatt's nasal branch.
    let mut anti = if nasal_f > 0.0 {
        Some(KlattAntiResonator::new(nasal_f.min(nyq), nasal_bw.max(40.0), fs_f))
    } else {
        None
    };

    let mut out = vec![0.0f32; output_samples];
    for n in 0..output_samples {
        let mut s = excitation[n];
        if let Some(a) = anti.as_mut() {
            s = a.step(s);
        }
        for r in resonators.iter_mut() {
            s = r.step(s);
        }
        // Apply the overall temporal envelope (mean per-patch magnitude) so the
        // cascade output is gated by the trajectory's loudness contour.
        let env_gain = env_total[n] / (n_patches as f32);
        out[n] = s * env_gain;
    }

    // Attack / release ramp.
    let ramp_n = ((0.015 * fs_f) as usize).min(output_samples / 4);
    if ramp_n > 1 {
        for i in 0..ramp_n {
            let r = i as f32 / ramp_n as f32;
            out[i] *= r;
            out[output_samples - 1 - i] *= r;
        }
    }
    // Peak-normalise to [-0.9, 0.9].
    let peak = out.iter().fold(0.0f32, |a, &b| a.max(b.abs()));
    if peak > 0.0 {
        let scale = 0.9 / peak;
        for v in &mut out {
            *v *= scale;
        }
    }
    out
}

/// Source-filter synthesis driven by per-frame FORMANT TRACKS (not gammatone
/// patch energy). This is the agent's PRODUCTION forward model in its faithful
/// source-filter form: a glottal SOURCE clock (LF glottal-flow derivative at f0,
/// or aspiration noise when unvoiced) driving a vocal-tract FILTER (Klatt cascade
/// of 2-pole resonators set to the formant frequencies F1..Fk). The formant
/// targets come from the agent's phonetic knowledge (vowel/consonant formant
/// tables) interpolated into a trajectory over the word — supplied here as
/// per-frame F/BW tracks. NO trained net, NO fit: pure closed-form DSP, the same
/// `KlattResonator` + `lf_source` primitives the patch-driven voicebox uses.
///
/// Arguments (all per-FRAME tracks, n_frames long, n_formants wide where noted):
///   * `formants_flat`   — n_frames * n_formants formant frequencies (Hz),
///                          row-major (frame-major): frame f's formants are
///                          formants_flat[f*n_formants .. (f+1)*n_formants].
///   * `bandwidths_flat` — matching n_frames * n_formants formant bandwidths (Hz).
///   * `voiced`          — n_frames voicing fractions in [0,1] (1=fully voiced
///                          vowel, 0=voiceless fricative/stop): mixes LF source
///                          vs aspiration noise per frame.
///   * `amp`             — n_frames overall amplitude envelope (loudness contour;
///                          0 in silent gaps / closures).
///   * `f0_hz`           — the speaker's pitch (glottal source clock rate).
///   The cascade is rebuilt each frame with that frame's formant frequencies, so
///   the resonators TRACK the moving formants (coarticulation falls out of the
///   interpolation). State (y1,y2) carries across frames so the filter is
///   continuous. f0 sets the source clock; VTL scaling is applied by the caller
///   (it scales the formant Hz it passes in — VTL is a multiplicative formant
///   scale = the speaker knob).
#[allow(clippy::too_many_arguments)]
pub fn synthesize_formant_track(
    formants_flat: &[f32],
    bandwidths_flat: &[f32],
    voiced: &[f32],
    amp: &[f32],
    n_formants: usize,
    output_samples: usize,
    fs: u32,
    f0_hz: f32,
    oq: f32,
    am: f32,
    ta_frac: f32,
) -> Vec<f32> {
    let n_frames = voiced.len();
    if n_frames == 0
        || n_formants == 0
        || output_samples == 0
        || formants_flat.len() < n_frames * n_formants
        || bandwidths_flat.len() < n_frames * n_formants
        || amp.len() < n_frames
    {
        return vec![0.0; output_samples];
    }
    let fs_f = fs as f32;
    let nyq = fs_f / 2.0 * 0.95;

    // --- two sources at the full output rate (the glottal clock + aspiration) ---
    let voiced_src = lf_source(output_samples, fs_f, f0_hz, oq, am, ta_frac);
    let seed: u64 = formants_flat
        .iter()
        .take(n_formants)
        .map(|f| (*f as u64).wrapping_mul(0x9E3779B97F4A7C15))
        .fold(0xCAFE_BABE_DEAD_BEEFu64, |a, b| a.wrapping_add(b));
    let mut state = seed;
    let mut noise = vec![0.0f32; output_samples];
    for v in &mut noise {
        state = state
            .wrapping_mul(6364136223846793005)
            .wrapping_add(1442695040888963407);
        let u = (state >> 33) as u32;
        *v = ((u as f32) / (u32::MAX as f32)) * 2.0 - 1.0;
    }

    // Per-formant resonators, coefficients UPDATED each frame to the frame's
    // formant frequency. State persists across frames (continuous filtering).
    let mut resonators: Vec<KlattResonator> = (0..n_formants)
        .map(|i| {
            let f = formants_flat[i].clamp(120.0, nyq);
            let bw = bandwidths_flat[i].clamp(40.0, 400.0);
            KlattResonator::new(f, bw, fs_f)
        })
        .collect();

    let denom = if output_samples > 1 { (output_samples - 1) as f32 } else { 1.0 };
    let mut out = vec![0.0f32; output_samples];
    let mut cur_frame = usize::MAX;
    for n in 0..output_samples {
        // Which frame are we in (linear time map).
        let fpos = (n as f32) / denom * (n_frames - 1).max(1) as f32;
        let lo = (fpos as usize).min(n_frames - 1);
        let hi = (lo + 1).min(n_frames - 1);
        let frac = fpos - lo as f32;
        // Update resonator coefficients to the interpolated formant of this frame
        // (only when the integer frame changes — cheap; sub-frame interpolation of
        // the COEFFICIENTS would be over-engineering for this rate).
        if lo != cur_frame {
            cur_frame = lo;
            for (i, r) in resonators.iter_mut().enumerate() {
                let flo = formants_flat[lo * n_formants + i];
                let fhi = formants_flat[hi * n_formants + i];
                let f = (flo * (1.0 - frac) + fhi * frac).clamp(120.0, nyq);
                let blo = bandwidths_flat[lo * n_formants + i];
                let bhi = bandwidths_flat[hi * n_formants + i];
                let bw = (blo * (1.0 - frac) + bhi * frac).clamp(40.0, 400.0);
                r.set(f, bw, fs_f);
            }
        }
        // Mixed source: voiced fraction of the frame.
        let vf = (voiced[lo] * (1.0 - frac) + voiced[hi] * frac).clamp(0.0, 1.0);
        let a = amp[lo] * (1.0 - frac) + amp[hi] * frac;
        let src = vf * voiced_src[n] + (1.0 - vf) * 0.4 * noise[n];
        // Cascade.
        let mut s = src;
        for r in resonators.iter_mut() {
            s = r.step(s);
        }
        out[n] = s * a;
    }

    // Attack / release ramp.
    let ramp_n = ((0.015 * fs_f) as usize).min(output_samples / 4);
    if ramp_n > 1 {
        for i in 0..ramp_n {
            let r = i as f32 / ramp_n as f32;
            out[i] *= r;
            out[output_samples - 1 - i] *= r;
        }
    }
    // Peak-normalise to [-0.9, 0.9].
    let peak = out.iter().fold(0.0f32, |a, &b| a.max(b.abs()));
    if peak > 0.0 {
        let scale = 0.9 / peak;
        for v in &mut out {
            *v *= scale;
        }
    }
    out
}

// --- sonority valley detector --------------------------------------------

/// One detected sonority valley.
#[derive(Debug, Clone, Copy)]
pub struct SonorityValley {
    pub sample: usize,
    pub depth: f32,   // relative drop from the lower flanking peak, in [0,1]
    pub valley: f32,  // smoothed envelope value at the valley
    pub peak: f32,    // limiting peak (min of left/right peak)
}

/// Box-window moving average via cumulative sum — O(n).
fn moving_average(x: &[f32], n: usize) -> Vec<f32> {
    if n <= 1 || x.is_empty() {
        return x.to_vec();
    }
    let half = n / 2;
    let mut cs = vec![0.0f64; x.len() + 1];
    for i in 0..x.len() {
        cs[i + 1] = cs[i] + x[i] as f64;
    }
    let mut out = vec![0.0f32; x.len()];
    for i in 0..x.len() {
        let lo = i.saturating_sub(half);
        let hi = (i + half + 1).min(x.len());
        out[i] = ((cs[hi] - cs[lo]) / (hi - lo) as f64) as f32;
    }
    out
}

/// Find sonority valleys — local minima of the smoothed total
/// envelope where the relative drop from surrounding peaks exceeds
/// `depth_threshold`. Used by lexical access as word-boundary
/// candidates in continuous speech.
///
/// * `smoothing_ms`: width of the moving-average window applied to
///   the envelope before minima are picked. ~30–50 ms suppresses
///   intra-phoneme jitter while preserving syllable structure.
/// * `min_separation_ms`: a point is a local minimum iff it's the
///   smallest value in a ±half-window of this width. Sets the
///   minimum gap between successive valleys (~80–120 ms is typical
///   for word-rate segmentation).
/// * `depth_threshold`: relative drop `(peak − valley) / peak`
///   required to emit a valley. Higher = fewer, deeper valleys
///   (word boundaries); lower = more (syllable boundaries).
///
/// Returns valleys sorted by sample index.
pub fn detect_sonority_valleys(
    total_env: &[f32],
    fs: u32,
    smoothing_ms: f32,
    min_separation_ms: f32,
    depth_threshold: f32,
) -> Vec<SonorityValley> {
    let n = total_env.len();
    if n < 8 {
        return Vec::new();
    }
    let smooth_n = ((smoothing_ms * 0.001) * fs as f32).max(1.0) as usize;
    let smoothed = moving_average(total_env, smooth_n);

    let sep_n = ((min_separation_ms * 0.001) * fs as f32).max(1.0) as usize;
    let half_w = (sep_n / 2).max(1);

    // 1. Local minima within a ±half_w window.
    let mut minima: Vec<usize> = Vec::new();
    let mut i = half_w;
    while i + half_w < n {
        let v = smoothed[i];
        let lo = i.saturating_sub(half_w);
        let hi = (i + half_w + 1).min(n);
        let mut is_min = true;
        let mut j = lo;
        while j < hi {
            if j != i && smoothed[j] < v {
                is_min = false;
                break;
            }
            j += 1;
        }
        if is_min {
            minima.push(i);
            // Skip ahead by half_w to avoid emitting plateau twins.
            i += half_w;
        } else {
            i += 1;
        }
    }
    if minima.is_empty() {
        return Vec::new();
    }

    // 2. For each minimum, compute relative depth from the lower of
    //    its two flanking peaks. The flanking-peak window for
    //    minimum k runs from the previous minimum (or 0) to the next
    //    minimum (or n).
    let mut out: Vec<SonorityValley> = Vec::new();
    for (k, &m_i) in minima.iter().enumerate() {
        let prev_m = if k > 0 { minima[k - 1] } else { 0 };
        let next_m = if k + 1 < minima.len() { minima[k + 1] } else { n };
        let mut prev_peak = 0.0f32;
        for j in prev_m..m_i {
            if smoothed[j] > prev_peak {
                prev_peak = smoothed[j];
            }
        }
        let mut next_peak = 0.0f32;
        for j in m_i..next_m {
            if smoothed[j] > next_peak {
                next_peak = smoothed[j];
            }
        }
        let limiting = prev_peak.min(next_peak);
        if limiting <= 1e-9 {
            continue;
        }
        let valley_v = smoothed[m_i];
        let depth = ((limiting - valley_v).max(0.0)) / limiting;
        if depth >= depth_threshold {
            out.push(SonorityValley {
                sample: m_i,
                depth,
                valley: valley_v,
                peak: limiting,
            });
        }
    }
    out
}

// --- cross-band coincidence ----------------------------------------------

/// One detected onset, tagged with the band it came from.
#[derive(Debug, Clone, Copy)]
pub struct BandedOnset {
    pub band_index: usize,
    pub sample: usize,
    pub magnitude_db: f32,
}

/// A cluster of onsets that fell within a time window across enough
/// distinct bands. Mirrors octopus-cell broadband-coincidence behaviour.
#[derive(Debug, Clone)]
pub struct BroadbandCluster {
    pub mean_sample: f64,
    pub n_bands: usize,
    pub member_indices: Vec<usize>, // indices into the input onset list
    pub total_magnitude_db: f32,
}

/// Cluster per-band onsets into broadband-coincidence events. Onsets
/// within `window_samples` of each other across `min_bands` distinct
/// bands form one cluster.
pub fn cross_band_coincidence(
    onsets: &[BandedOnset],
    window_samples: usize,
    min_bands: usize,
) -> Vec<BroadbandCluster> {
    if onsets.is_empty() {
        return Vec::new();
    }
    let mut indices: Vec<usize> = (0..onsets.len()).collect();
    indices.sort_by_key(|&i| (onsets[i].sample, onsets[i].band_index));

    let mut clusters = Vec::new();
    let mut i = 0usize;
    while i < indices.len() {
        let start_sample = onsets[indices[i]].sample;
        let mut j = i + 1;
        while j < indices.len()
            && onsets[indices[j]].sample.saturating_sub(start_sample) <= window_samples
        {
            j += 1;
        }
        let member_idxs: Vec<usize> = (i..j).map(|k| indices[k]).collect();
        let mut bands_seen: Vec<usize> = Vec::with_capacity(8);
        for &k in &member_idxs {
            let b = onsets[k].band_index;
            if !bands_seen.contains(&b) {
                bands_seen.push(b);
            }
        }
        if bands_seen.len() >= min_bands {
            let mean_sample: f64 = member_idxs
                .iter()
                .map(|&k| onsets[k].sample as f64)
                .sum::<f64>()
                / member_idxs.len() as f64;
            let total_mag: f32 = member_idxs
                .iter()
                .map(|&k| onsets[k].magnitude_db)
                .sum::<f32>();
            clusters.push(BroadbandCluster {
                mean_sample,
                n_bands: bands_seen.len(),
                member_indices: member_idxs,
                total_magnitude_db: total_mag,
            });
        }
        i = if j > i { j } else { i + 1 };
    }
    clusters
}

// --- stft (the second ear) -------------------------------------------------

/// Short-time Fourier transform magnitude — the frequency-sharp ear.
///
/// Frames the signal with a `hop_size` stride, applies a Hann window to
/// each `window_size`-sample frame, runs a real FFT, and keeps the
/// magnitude of the first `window_size / 2` bins per frame. The result
/// is a flat `frames × (window_size / 2)` row-major buffer (frame 0's
/// bins, then frame 1's, ...).
///
/// Complementary to the gammatone bank: where the gammatone is sharp in
/// time and broad in frequency, the STFT trades the opposite way. Same
/// AudioBuffer, two ways of hearing it.
///
/// Returns an empty Vec if `window_size == 0`, `hop_size == 0`, or the
/// signal is shorter than one window.
pub fn stft(samples: &[f32], window_size: usize, hop_size: usize) -> Vec<f32> {
    use rustfft::FftPlanner;

    if window_size == 0 || hop_size == 0 || samples.len() < window_size {
        return Vec::new();
    }
    let half = window_size / 2;

    // Precompute the Hann window: 0.5 - 0.5·cos(2π n / (N-1)).
    let hann: Vec<f32> = (0..window_size)
        .map(|n| {
            let x = 2.0 * std::f32::consts::PI * n as f32 / (window_size as f32 - 1.0);
            0.5 - 0.5 * x.cos()
        })
        .collect();

    let mut planner = FftPlanner::<f32>::new();
    let fft = planner.plan_fft_forward(window_size);

    let n_frames = (samples.len() - window_size) / hop_size + 1;
    let mut out: Vec<f32> = Vec::with_capacity(n_frames * half);
    let mut scratch: Vec<Complex<f32>> = vec![Complex::new(0.0, 0.0); window_size];

    let mut start = 0usize;
    while start + window_size <= samples.len() {
        for i in 0..window_size {
            scratch[i] = Complex::new(samples[start + i] * hann[i], 0.0);
        }
        fft.process(&mut scratch);
        for bin in scratch.iter().take(half) {
            out.push(bin.norm());
        }
        start += hop_size;
    }
    out
}

// --- LPC / all-pole formant tracking ---------------------------------------
//
// The agent's own self-specified front-end operation (`runtime_design.
// agent_specify_lpc_formants`, OperationSpec `lpc_all_pole_formants`), now
// OWNED NATIVELY rather than stuck in Python (Stage-0 / W1 / Gap 2 of the
// agent's curriculum + self-assessment). The agent's science: the vocal
// tract IS an all-pole filter, so the EXACT inversion of that model by
// linear prediction recovers its resonances directly as pole angles = the
// true formants — cleaner than reading peaks off a blurry spectrum.
//
// The chain mirrors the (now-superseded) Python DSP in
// `domains/lpc_formant_representation.py` exactly:
//   pre-emphasis + Hamming window
//     -> autocorrelation r[0..p]            (`lpc_autocorr`)
//     -> Levinson-Durbin recursion          (`levinson_durbin`)  -> a_k
//     -> roots of A(z) (Durand-Kerner)      (`poly_roots`)
//     -> pole angle * fs / 2pi = formant Hz, bw from |pole|, range-filtered
//                                           (`lpc_roots_formants`)
//
// All pure Rust, no graph state, no net / .fit / gradient — the SAME
// category as `gammatone_band` / `band_autocorr` above.

/// Autocorrelation r[0..=p] of a windowed frame. r[k] = sum_n x[n] x[n+k].
/// Mechanical DSP (was `lpc_formant_representation._autocorr`).
pub fn lpc_autocorr(x: &[f32], p: usize) -> Vec<f64> {
    let n = x.len();
    let mut r = vec![0.0f64; p + 1];
    for (k, rk) in r.iter_mut().enumerate() {
        if k >= n {
            break;
        }
        let mut acc = 0.0f64;
        for i in 0..(n - k) {
            acc += x[i] as f64 * x[i + k] as f64;
        }
        *rk = acc;
    }
    r
}

/// Levinson-Durbin recursion: autocorrelation r[0..=p] -> the all-pole
/// coefficients a[0..=p] of A(z) = 1 - sum_k a_k z^-k (with a[0] = 1.0 in
/// this convention), plus the final prediction-error energy (the gain).
/// Mechanical DSP (was `lpc_formant_representation._levinson`).
pub fn levinson_durbin(r: &[f64], p: usize) -> (Vec<f64>, f64) {
    let mut a = vec![0.0f64; p + 1];
    a[0] = 1.0;
    if r.is_empty() {
        return (a, 0.0);
    }
    let mut e = r[0];
    if e <= 0.0 {
        return (a, 0.0);
    }
    for i in 1..=p {
        if i >= r.len() {
            break;
        }
        let mut acc = r[i];
        for j in 1..i {
            acc += a[j] * r[i - j];
        }
        let k = -acc / e;
        let mut a_new = a.clone();
        for j in 1..i {
            a_new[j] = a[j] + k * a[i - j];
        }
        a_new[i] = k;
        a = a_new;
        e *= 1.0 - k * k;
        if e <= 0.0 {
            break;
        }
    }
    (a, e.max(1e-9))
}

/// Roots of a real polynomial given coefficients in DESCENDING order
/// (coeffs[0] * z^d + ... + coeffs[d]), via the Durand-Kerner (Weierstrass)
/// simultaneous iteration. This is the native replacement for `numpy.roots`
/// in the Python LPC formant extractor (companion-matrix eigenvalues there;
/// Durand-Kerner here — same roots, no LAPACK dependency).
fn poly_roots(coeffs: &[f64]) -> Vec<Complex<f64>> {
    // Strip leading (near-)zeros.
    let mut c = coeffs.to_vec();
    let mut lead = 0usize;
    while lead < c.len() && c[lead].abs() < 1e-12 {
        lead += 1;
    }
    c = c[lead..].to_vec();
    let deg = if c.is_empty() { 0 } else { c.len() - 1 };
    if deg == 0 {
        return Vec::new();
    }
    // Normalise to monic.
    let a0 = c[0];
    for v in c.iter_mut() {
        *v /= a0;
    }
    // Initial guesses on a spiral off the unit circle (the classic
    // 0.4 + 0.9i seed powers — avoids the all-real degenerate start).
    let seed = Complex::new(0.4, 0.9);
    let mut roots: Vec<Complex<f64>> = (0..deg).map(|i| seed.powi(i as i32)).collect();
    let eval = |z: Complex<f64>| -> Complex<f64> {
        let mut acc = Complex::new(0.0, 0.0);
        for &coef in &c {
            acc = acc * z + Complex::new(coef, 0.0);
        }
        acc
    };
    for _ in 0..200 {
        let mut max_delta = 0.0f64;
        for i in 0..deg {
            let zi = roots[i];
            let mut denom = Complex::new(1.0, 0.0);
            for (j, &zj) in roots.iter().enumerate() {
                if j != i {
                    denom *= zi - zj;
                }
            }
            if denom.norm() < 1e-30 {
                continue;
            }
            let delta = eval(zi) / denom;
            roots[i] = zi - delta;
            if delta.norm() > max_delta {
                max_delta = delta.norm();
            }
        }
        if max_delta < 1e-12 {
            break;
        }
    }
    roots
}

/// One frame of raw waveform -> ascending formant frequencies (Hz), exactly
/// as the agent specified (`agent_specify_lpc_formants`): pre-emphasised +
/// Hamming-windowed frame -> autocorrelation -> Levinson-Durbin -> roots of
/// A(z) -> pole angle * fs / 2pi = formant Hz, bandwidth from |pole|; keep
/// resonances in [f_lo, f_hi] Hz with bandwidth < bw_max Hz. Returns the
/// formant frequencies sorted ascending. (Was
/// `lpc_formant_representation._lpc_roots_formants`.)
#[allow(clippy::too_many_arguments)]
pub fn lpc_roots_formants(
    frame: &[f32],
    fs: u32,
    order: usize,
    pre_emph: f32,
    f_lo: f32,
    f_hi: f32,
    bw_max: f32,
) -> Vec<f32> {
    let n = frame.len();
    if n < order + 2 {
        return Vec::new();
    }
    // Pre-emphasis: x[0], x[i] - pre_emph * x[i-1].
    let mut x = vec![0.0f32; n];
    x[0] = frame[0];
    for i in 1..n {
        x[i] = frame[i] - pre_emph * frame[i - 1];
    }
    // Hamming window.
    let denom = (n - 1).max(1) as f32;
    for (i, xi) in x.iter_mut().enumerate() {
        let w = 0.54 - 0.46 * (2.0 * std::f32::consts::PI * i as f32 / denom).cos();
        *xi *= w;
    }
    let r = lpc_autocorr(&x, order);
    if r.is_empty() || r[0] <= 0.0 {
        return Vec::new();
    }
    let (a, _gain) = levinson_durbin(&r, order);
    // A(z) = sum_{k=0}^p a_k z^-k with a[0]=1. The poles of the all-pole tract
    // filter H(z)=1/A(z) are the roots of A(z)=0; multiplying by z^p gives the
    // polynomial a_0 z^p + a_1 z^{p-1} + ... + a_p whose DESCENDING-power coeffs
    // are `a` AS-IS (a[0] first), NOT reversed. (The old a[::-1] solved the
    // RECIPROCAL polynomial, putting every pole OUTSIDE the unit circle so every
    // bandwidth came out negative — the bug that emptied lpc_formants_bw and
    // sign-flipped these bandwidths. Frequencies survived because reciprocation
    // preserves the pole angle.)
    let coeffs: Vec<f64> = a.clone();
    let roots = poly_roots(&coeffs);
    let half_fs = fs as f64 / (2.0 * std::f64::consts::PI);
    let mut fmts: Vec<f32> = Vec::new();
    for z in roots {
        if z.im <= 0.0 {
            continue;
        }
        let ang = z.im.atan2(z.re);
        let f = (ang * fs as f64 / (2.0 * std::f64::consts::PI)) as f32;
        let bw = (-half_fs * (z.norm() + 1e-12).ln()) as f32;
        if f >= f_lo && f <= f_hi && bw > 0.0 && bw < bw_max {
            fmts.push(f);
        }
    }
    fmts.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    fmts
}

// =========================================================================
//  THE IMPRESSIONIST — speaker-config INVERSION from a small real sample.
// =========================================================================
//  A VOICE is a SHORT CODE over the shared source-filter grammar: the
//  vocal-tract FILTER (formant freqs + bandwidths => VTL), and the glottal
//  SOURCE (f0, open-quotient, spectral tilt). "Do an impression from a small
//  sample" = RECOVER that code by INVERTING the forward model, then re-render.
//  The inversion is pure owned DSP: inverse-filter the sample through its own
//  LPC all-pole A(z) and the RESIDUAL that falls out IS an estimate of that
//  speaker's glottal source; the pole angles/radii ARE the formant freqs/bws.
//  NO net, NO embedding, NO .fit — analysis-by-synthesis, not interpolation.

/// Pre-emphasise + Hamming-window a frame (the SAME front-end the LPC formant
/// chain uses, factored out so the residual is computed on the identical x).
fn preemph_window(frame: &[f32], pre_emph: f32) -> Vec<f32> {
    let n = frame.len();
    let mut x = vec![0.0f32; n];
    if n == 0 {
        return x;
    }
    x[0] = frame[0];
    for i in 1..n {
        x[i] = frame[i] - pre_emph * frame[i - 1];
    }
    let denom = (n - 1).max(1) as f32;
    for (i, xi) in x.iter_mut().enumerate() {
        let w = 0.54 - 0.46 * (2.0 * std::f32::consts::PI * i as f32 / denom).cos();
        *xi *= w;
    }
    x
}

/// LPC RESIDUAL of one frame — inverse-filter the (pre-emphasised, windowed)
/// frame through its own all-pole A(z): e[n] = x[n] - sum_k a_k x[n-k]. The
/// residual REMOVES the vocal-tract resonance (the filter), leaving an estimate
/// of the GLOTTAL SOURCE excitation (the voice-identity part: pitch pulses for
/// voiced, white-ish noise for unvoiced). This is the key inversion primitive:
/// the residual of a real speaker's sample IS that speaker's source estimate.
/// `order` LPC order; `pre_emph` the pre-emphasis coefficient. Pure DSP, no fit.
pub fn lpc_residual(frame: &[f32], order: usize, pre_emph: f32) -> Vec<f32> {
    let x = preemph_window(frame, pre_emph);
    let n = x.len();
    if n < order + 2 {
        return vec![0.0; n];
    }
    let r = lpc_autocorr(&x, order);
    if r.is_empty() || r[0] <= 0.0 {
        return vec![0.0; n];
    }
    let (a, _gain) = levinson_durbin(&r, order);
    // e[n] = sum_{k=0}^{order} a_k x[n-k]   (a[0]=1, A(z) = 1 - sum a_k z^-k in
    // Levinson's sign convention here the coeffs already carry the sign so the
    // inverse filter is the direct convolution with a[]).
    let mut e = vec![0.0f32; n];
    for nn in 0..n {
        let mut acc = 0.0f64;
        for (k, &ak) in a.iter().enumerate() {
            if nn >= k {
                acc += ak * x[nn - k] as f64;
            }
        }
        e[nn] = acc as f32;
    }
    e
}

/// Formant frequencies AND bandwidths from one frame, via the LPC pole
/// freq/radius (the SAME chain as `lpc_roots_formants` but it KEEPS the
/// bandwidth — pole radius => bw = -fs/(2π)·ln|z| — which the freq-only
/// extractor discards). Returns a flat [f0,bw0, f1,bw1, ...] sorted by
/// ascending frequency. The bandwidths are a HALF of the speaker's filter
/// code (a breathy/soft voice has WIDE formant bandwidths) — the impressionist
/// needs them to render the right vocal-tract sharpness. Pure DSP, no fit.
pub fn lpc_formants_bw(
    frame: &[f32],
    fs: u32,
    order: usize,
    pre_emph: f32,
    f_lo: f32,
    f_hi: f32,
    bw_max: f32,
) -> Vec<f32> {
    let x = preemph_window(frame, pre_emph);
    let n = x.len();
    if n < order + 2 {
        return Vec::new();
    }
    let r = lpc_autocorr(&x, order);
    if r.is_empty() || r[0] <= 0.0 {
        return Vec::new();
    }
    let (a, _gain) = levinson_durbin(&r, order);
    // Descending-power coeffs of A(z)·z^p are `a` AS-IS (a[0]=1 first) — the
    // poles of the all-pole tract filter, INSIDE the unit circle → positive
    // bandwidths. (See lpc_roots_formants for the a[::-1] reciprocal-root bug.)
    let coeffs: Vec<f64> = a.clone();
    let roots = poly_roots(&coeffs);
    let half_fs = fs as f64 / (2.0 * std::f64::consts::PI);
    let mut pairs: Vec<(f32, f32)> = Vec::new();
    for z in roots {
        if z.im <= 0.0 {
            continue;
        }
        let ang = z.im.atan2(z.re);
        let f = (ang * fs as f64 / (2.0 * std::f64::consts::PI)) as f32;
        let bw = (-half_fs * (z.norm() + 1e-12).ln()) as f32;
        if f >= f_lo && f <= f_hi && bw > 0.0 && bw < bw_max {
            pairs.push((f, bw));
        }
    }
    pairs.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal));
    let mut out = Vec::with_capacity(pairs.len() * 2);
    for (f, bw) in pairs {
        out.push(f);
        out.push(bw);
    }
    out
}

/// F0 (Hz) of a frame by autocorrelation peak-picking on the raw waveform —
/// the speaker's pitch (the glottal CLOCK rate). Searches the lag range
/// [fs/f_hi, fs/f_lo] for the autocorrelation maximum; returns 0.0 if the
/// frame is unvoiced (peak below `voicing_thresh` × r[0]). Owned DSP — the
/// speaker's habitual pitch is part of the short code. No fit.
pub fn f0_autocorr(frame: &[f32], fs: u32, f_lo: f32, f_hi: f32, voicing_thresh: f32) -> f32 {
    let n = frame.len();
    if n < 16 || f_lo <= 0.0 || f_hi <= f_lo {
        return 0.0;
    }
    // remove DC.
    let mean = frame.iter().map(|&v| v as f64).sum::<f64>() / n as f64;
    let x: Vec<f64> = frame.iter().map(|&v| v as f64 - mean).collect();
    let r0 = x.iter().map(|&v| v * v).sum::<f64>().max(1e-12);
    let lag_min = ((fs as f32 / f_hi).floor() as usize).max(2);
    let lag_max = ((fs as f32 / f_lo).ceil() as usize).min(n - 1);
    if lag_max <= lag_min {
        return 0.0;
    }
    let mut best_lag = 0usize;
    let mut best_val = 0.0f64;
    for lag in lag_min..=lag_max {
        let mut acc = 0.0f64;
        for i in 0..(n - lag) {
            acc += x[i] * x[i + lag];
        }
        let norm = acc / r0;
        if norm > best_val {
            best_val = norm;
            best_lag = lag;
        }
    }
    if best_lag == 0 || best_val < voicing_thresh as f64 {
        return 0.0;
    }
    fs as f32 / best_lag as f32
}

/// GLOTTAL SOURCE shape from the LPC residual — estimate the speaker's
/// open-quotient and spectral-tilt the inverse way: pitch-synchronously align
/// the residual to its f0 period and read the source shape that the forward LF
/// model is parametrised by. Returns [oq, ta_frac, tilt_db_per_oct]:
///   * `oq`  — OPEN QUOTIENT estimate = the fraction of the pitch period over
///             which the residual energy is spread (a breathy voice has a long
///             open phase => energy spread across the period => high oq; a
///             pressed voice has a sharp pulse => low oq). Computed as the
///             period-fraction containing the central 80% of |residual|² mass
///             around the peak — a direct, fit-free read of the source pulse
///             width.
///   * `ta_frac` — RETURN-PHASE / spectral-tilt proxy = how fast the residual
///             decays after its peak (a soft voice has a gradual return =>
///             large ta; a sharp voice returns fast). Read as the normalised
///             decay length after the residual peak.
///   * `tilt_db_per_oct` — overall source spectral tilt (high-freq roll-off):
///             10·log10(low-band energy / high-band energy) of the residual,
///             split at fs/4. A softer/breathier voice rolls off faster.
/// If f0<=0 (unvoiced) returns the modal defaults [0.6, 0.01, 0.0]. Pure DSP
/// read of the speaker's OWN source — analysis-by-synthesis, NO fit, NO net.
pub fn glottal_params_from_residual(residual: &[f32], fs: u32, f0_hz: f32) -> Vec<f32> {
    let n = residual.len();
    if n < 8 || f0_hz <= 0.0 {
        return vec![0.6, 0.01, 0.0];
    }
    let period = (fs as f32 / f0_hz).round().max(4.0) as usize;
    if period >= n {
        return vec![0.6, 0.01, 0.0];
    }
    // energy envelope |e|^2.
    let pw: Vec<f64> = residual.iter().map(|&v| (v as f64) * (v as f64)).collect();
    // Find the strongest pulse: the period-window with max energy, then its peak.
    let mut best_start = 0usize;
    let mut best_e = -1.0f64;
    let mut s = 0usize;
    while s + period <= n {
        let e: f64 = pw[s..s + period].iter().sum();
        if e > best_e {
            best_e = e;
            best_start = s;
        }
        s += period / 2;
    }
    let win = &pw[best_start..best_start + period];
    let total: f64 = win.iter().sum::<f64>().max(1e-12);
    // peak index within the window.
    let mut peak_i = 0usize;
    let mut peak_v = -1.0f64;
    for (i, &v) in win.iter().enumerate() {
        if v > peak_v {
            peak_v = v;
            peak_i = i;
        }
    }
    // OPEN QUOTIENT: width (in period fraction) of the central 80% energy band
    // centred on the peak — grow a symmetric window around the peak until it
    // holds 80% of the period energy.
    let mut lo = peak_i;
    let mut hi = peak_i;
    let mut acc = win[peak_i];
    while acc < 0.8 * total && (lo > 0 || hi + 1 < period) {
        let take_lo = if lo > 0 { win[lo - 1] } else { -1.0 };
        let take_hi = if hi + 1 < period { win[hi + 1] } else { -1.0 };
        if take_hi >= take_lo {
            hi += 1;
            acc += win[hi];
        } else {
            lo -= 1;
            acc += win[lo];
        }
    }
    let oq = ((hi - lo + 1) as f32 / period as f32).clamp(0.3, 0.9);
    // RETURN PHASE / ta_frac: normalised decay length after the peak — number of
    // samples for the energy to fall to 1/e of the peak, as a period fraction.
    let mut decay = 1usize;
    let thr = peak_v / std::f32::consts::E as f64;
    let mut i = peak_i;
    while i + 1 < period && win[i] > thr {
        i += 1;
        decay += 1;
    }
    let ta_frac = ((decay as f32 / period as f32) * 0.5).clamp(0.002, 0.2);
    // SPECTRAL TILT (db/oct proxy): low-band vs high-band residual energy, split
    // at fs/4 via a one-pole low/high split (cheap; no FFT). A breathier source
    // has MORE high-freq energy (less tilt) — actually a pressed source has more
    // HF. We report 10log10(low/high): higher = softer/more roll-off.
    let mut prev = 0.0f64;
    let mut low_e = 0.0f64;
    let mut high_e = 0.0f64;
    for &v in residual.iter() {
        let vv = v as f64;
        // simple 1-pole low-pass (alpha for cutoff ~ fs/4).
        let lp = 0.5 * vv + 0.5 * prev;
        prev = lp;
        low_e += lp * lp;
        let hp = vv - lp;
        high_e += hp * hp;
    }
    let tilt = (10.0 * (low_e.max(1e-12) / high_e.max(1e-12)).log10()) as f32;
    vec![oq, ta_frac, tilt]
}

// =========================================================================
//  GENUINE GLOTTAL INVERSE — IAIF + closed-phase covariance LPC + GCI.
//
//  The old `glottal_params_from_residual` reads oq/tilt off the FULL-FRAME
//  LPC residual. That residual is over-whitened: the autocorrelation/Levinson
//  tract is estimated across the WHOLE period (open + closed phase) so it
//  partly absorbs the glottal contribution; the residual collapses to a near-
//  impulse train and the 80%-energy-band oq read SATURATES at the 0.30 floor
//  for every speaker (verified: injected oq 0.45->0.90 all read 0.300). The
//  cue is in the spectrum but the instrument cannot see it.
//
//  This block recovers the speaker's TRUE glottal FLOW (not the whitened
//  residual) by two classical, fit-free inverse-filtering methods, then fits
//  oq/tilt to the recovered flow:
//
//   (1) IAIF (Alku 1992) — iterative adaptive inverse filtering. Cancel the
//       lip-radiation (a fixed 1st-order differentiator => integrate to undo),
//       estimate the vocal tract with a low-order LPC, inverse-filter, estimate
//       the glottal contribution with a 1st/low-order LPC, cancel it, RE-estimate
//       the tract on the glottis-cancelled signal, inverse-filter the original
//       => glottal flow DERIVATIVE; integrate => glottal FLOW.
//
//   (2) GCI detection + CLOSED-PHASE covariance LPC — find the glottal closure
//       instants (the sharp negative excitation peaks of the flow derivative),
//       and estimate the tract by covariance LPC over the CLOSED phase only
//       (source ~ 0 there, so the tract estimate is NOT source-contaminated).
//       Inverse-filter the period with that clean tract => clean glottal flow,
//       and read oq from the flow's open-phase fraction (opening->closure) and
//       tilt from the flow-derivative decay. This is the part the full-frame
//       residual method fundamentally cannot do (it has no closed-phase notion).
//
//  All closed-form linear algebra (autocorrelation, Levinson, covariance normal
//  equations by Cholesky). NO net, NO .fit, NO gradient, NO loss, NO sweep.
// =========================================================================

/// Covariance-method LPC over a segment `x[0..n]` using the rows from index
/// `p..n` (so every predictor x[t-1..t-p] is in-bounds — no windowing, no
/// autocorrelation). Solves the symmetric normal equations Φ a = ψ for the
/// predictor a[1..=p] (a[0]=1, A(z)=1 - sum a_k z^-k → here we return the
/// inverse-filter coeffs c with c[0]=1, c[k]=-a_pred[k] so e[n]=sum c_k x[n-k]).
/// Cholesky on the (small, SPD-by-construction) covariance matrix. Used for the
/// closed-phase tract estimate where the source is ~0.
fn covariance_lpc(x: &[f32], p: usize) -> Vec<f64> {
    let n = x.len();
    let mut c = vec![0.0f64; p + 1];
    c[0] = 1.0;
    if n < p + 2 || p == 0 {
        return c;
    }
    let xf: Vec<f64> = x.iter().map(|&v| v as f64).collect();
    // Φ[i][j] = sum_{t=p}^{n-1} x[t-i] x[t-j],  i,j in 1..=p
    // ψ[i]    = sum_{t=p}^{n-1} x[t]   x[t-i]
    let mut phi = vec![vec![0.0f64; p]; p];
    let mut psi = vec![0.0f64; p];
    for t in p..n {
        for i in 1..=p {
            psi[i - 1] += xf[t] * xf[t - i];
            for j in i..=p {
                phi[i - 1][j - 1] += xf[t - i] * xf[t - j];
            }
        }
    }
    for i in 0..p {
        for j in 0..i {
            phi[i][j] = phi[j][i];
        }
        phi[i][i] += 1e-6 * (phi[i][i].abs() + 1.0); // ridge for conditioning
    }
    // Cholesky Φ = L Lᵀ, solve L y = ψ, Lᵀ a = y.
    let mut l = vec![vec![0.0f64; p]; p];
    for i in 0..p {
        for j in 0..=i {
            let mut s = phi[i][j];
            for k in 0..j {
                s -= l[i][k] * l[j][k];
            }
            if i == j {
                if s <= 0.0 {
                    return c; // not SPD (degenerate segment) — bail to flat.
                }
                l[i][j] = s.sqrt();
            } else {
                l[i][j] = s / l[j][j];
            }
        }
    }
    let mut y = vec![0.0f64; p];
    for i in 0..p {
        let mut s = psi[i];
        for k in 0..i {
            s -= l[i][k] * y[k];
        }
        y[i] = s / l[i][i];
    }
    let mut a_pred = vec![0.0f64; p];
    for i in (0..p).rev() {
        let mut s = y[i];
        for k in (i + 1)..p {
            s -= l[k][i] * a_pred[k];
        }
        a_pred[i] = s / l[i][i];
    }
    // inverse-filter coeffs: e[n] = x[n] - sum a_pred[k] x[n-1-k]
    for k in 0..p {
        c[k + 1] = -a_pred[k];
    }
    c
}

/// Apply an inverse FIR filter `c` (c[0]=1) to `x`: e[n] = sum_k c_k x[n-k].
fn fir_inverse(x: &[f32], c: &[f64]) -> Vec<f32> {
    let n = x.len();
    let mut e = vec![0.0f32; n];
    for nn in 0..n {
        let mut acc = 0.0f64;
        for (k, &ck) in c.iter().enumerate() {
            if nn >= k {
                acc += ck * x[nn - k] as f64;
            }
        }
        e[nn] = acc as f32;
    }
    e
}

/// Autocorrelation-method LPC inverse-filter coeffs (c[0]=1) of order `p` for a
/// segment (Hamming-windowed for a stable estimate). Thin wrapper over the
/// existing autocorr + Levinson. Returns c with e[n]=sum c_k x[n-k].
fn autocorr_lpc_coeffs(x: &[f32], p: usize) -> Vec<f64> {
    let n = x.len();
    if n < p + 2 {
        return vec![1.0];
    }
    let denom = (n - 1).max(1) as f32;
    let mut xw = x.to_vec();
    for (i, xi) in xw.iter_mut().enumerate() {
        let w = 0.54 - 0.46 * (2.0 * std::f32::consts::PI * i as f32 / denom).cos();
        *xi *= w;
    }
    let r = lpc_autocorr(&xw, p);
    if r.is_empty() || r[0] <= 0.0 {
        return vec![1.0];
    }
    let (a, _g) = levinson_durbin(&r, p);
    a
}

/// Leaky integrator (undo lip-radiation differentiation / integrate flow
/// derivative -> flow). y[n] = x[n] + leak * y[n-1], with DC removed after.
fn leaky_integrate(x: &[f32], leak: f64) -> Vec<f32> {
    let n = x.len();
    let mut y = vec![0.0f32; n];
    let mut acc = 0.0f64;
    for i in 0..n {
        acc = x[i] as f64 + leak * acc;
        y[i] = acc as f32;
    }
    // remove mean (the integrator accrues DC).
    let m = y.iter().map(|&v| v as f64).sum::<f64>() / n.max(1) as f64;
    for v in &mut y {
        *v -= m as f32;
    }
    y
}

/// IAIF glottal-flow estimate for ONE pitch-period-aligned frame.
/// Returns the glottal FLOW (integrated derivative), same length as `frame`.
/// `tract_order` ~ fs/1000; `glottal_order` small (2..4). Classical Alku-1992.
fn iaif_glottal_flow(frame: &[f32], fs: u32, tract_order: usize, glottal_order: usize) -> Vec<f32> {
    let n = frame.len();
    if n < tract_order + 4 {
        return vec![0.0; n];
    }
    // Lip radiation L(z) = 1 - 0.99 z^-1 is already (approximately) applied to
    // recorded speech as a +6dB/oct tilt; IAIF works on the recorded (radiated)
    // signal directly and integrates the FINAL derivative. (Stage order per Alku.)
    // --- 1) first tract estimate: low-order (1) LPC to remove gross glottal+lip
    //        spectral tilt, then a `tract_order` LPC on what's left. ---
    let c_g1 = autocorr_lpc_coeffs(frame, glottal_order.max(1));
    let s1 = fir_inverse(frame, &c_g1); // tilt-flattened speech
    let c_v1 = autocorr_lpc_coeffs(&s1, tract_order);
    // --- 2) cancel that first tract from the ORIGINAL -> first glottal estimate. ---
    let g1 = fir_inverse(frame, &c_v1);
    let g1_flow = leaky_integrate(&g1, 0.99); // integrate derivative -> flow
    // --- 3) re-estimate the glottal contribution (low order) on the flow, cancel
    //        it from the original, RE-estimate the tract (now glottis-free). ---
    let c_g2 = autocorr_lpc_coeffs(&g1_flow, glottal_order);
    let s2 = fir_inverse(frame, &c_g2); // speech with glottal tilt removed
    let c_v2 = autocorr_lpc_coeffs(&s2, tract_order);
    // --- 4) inverse-filter the ORIGINAL with the refined tract -> flow derivative;
    //        integrate -> glottal FLOW. leak 0.995 gives a smoother flow for the
    //        amplitude-domain open-quotient read (the GCI detection runs on the
    //        re-differenced flow, so the closure spikes are preserved). ---
    let gd = fir_inverse(frame, &c_v2);
    leaky_integrate(&gd, 0.995)
}

/// Detect glottal closure instants (GCIs) in a flow-derivative signal: the
/// strongest NEGATIVE peaks (maximum excitation), spaced ~ one pitch period
/// apart. Returns sample indices. Period-constrained peak picking (no fit).
fn detect_gci(flow_deriv: &[f32], period: usize) -> Vec<usize> {
    let n = flow_deriv.len();
    let mut gci = Vec::new();
    if n < period || period < 4 {
        return gci;
    }
    // Threshold on the strongest negative excursion (closures are the large
    // negative spikes). A candidate is a LOCAL minimum below -0.30·|global min|.
    let gmin = flow_deriv.iter().cloned().fold(0.0f32, f32::min);
    if gmin >= 0.0 {
        return gci;
    }
    let thr = 0.30 * gmin; // negative
    let guard = (period as f32 * 0.55) as usize; // refractory: >= ~half a period
    // Collect candidate local minima, then greedily pick the strongest with the
    // refractory spacing (so each pitch period contributes exactly one GCI).
    let mut cands: Vec<(usize, f32)> = Vec::new();
    for i in 1..n - 1 {
        if flow_deriv[i] < thr
            && flow_deriv[i] <= flow_deriv[i - 1]
            && flow_deriv[i] <= flow_deriv[i + 1]
        {
            cands.push((i, flow_deriv[i]));
        }
    }
    // Sort by depth (most-negative first) and greedily accept with refractory.
    cands.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal));
    let mut chosen: Vec<usize> = Vec::new();
    for (idx, _) in cands {
        if chosen.iter().all(|&c| (c as i64 - idx as i64).unsigned_abs() as usize >= guard) {
            chosen.push(idx);
        }
    }
    chosen.sort_unstable();
    gci = chosen;
    gci
}

/// THE GENUINE GLOTTAL INVERSE — recover [oq, ta_frac, tilt_db] from a voiced
/// frame by IAIF + closed-phase covariance LPC, fitting oq/tilt to the recovered
/// glottal FLOW (not the over-whitened full-frame residual). This is the drop-in
/// replacement for `glottal_params_from_residual` that does NOT saturate.
///
///   oq      — OPEN QUOTIENT from the recovered glottal flow: per period, the
///             fraction between the glottal OPENING (flow rises from its closed
///             baseline) and the CLOSURE (the flow-derivative negative peak / GCI).
///             A breathy/open voice keeps the glottis open longer => high oq.
///             Read directly off the flow waveform timing — NOT an energy band,
///             so it spans the true 0.3..0.9 range instead of pinning at 0.30.
///   ta_frac — return-phase / tilt from the flow-derivative decay after the GCI
///             (samples to fall to 1/e of the excitation peak, as a period frac).
///   tilt_db — source spectral tilt = H1-H2 surrogate: 10log10(low/high energy)
///             of the recovered glottal FLOW (split at fs/4). A softer voice has
///             a steeper flow tilt.
pub fn glottal_inverse_iaif(frame: &[f32], fs: u32, f0_hz: f32) -> Vec<f32> {
    let n = frame.len();
    if n < 32 || f0_hz <= 0.0 {
        return vec![0.6, 0.01, 0.0];
    }
    let period = (fs as f32 / f0_hz).round().max(8.0) as usize;
    if period * 2 >= n {
        return vec![0.6, 0.01, 0.0];
    }
    let tract_order = ((fs as f32 / 1000.0).round() as usize).clamp(8, 20);
    // --- IAIF glottal flow over the whole frame. ---
    let flow = iaif_glottal_flow(frame, fs, tract_order, 3);
    // flow derivative (for GCI + return-phase) — first difference.
    let mut gd = vec![0.0f32; n];
    for i in 1..n {
        gd[i] = flow[i] - flow[i - 1];
    }
    let gci = detect_gci(&gd, period);
    if gci.len() < 2 {
        // fall back to a single-period IAIF read centred on the max |flow deriv|.
        return fit_oq_tilt_from_flow(&flow, &gd, period, fs, None);
    }

    // --- CLOSED-PHASE covariance LPC CROSS-CHECK (source-free tract): for the
    //     strongest-energy period, find the genuinely-closed stretch (the lowest-
    //     energy window of ~0.15·period — glottis shut, source ~ 0) and estimate the
    //     tract there by covariance LPC, then inverse-filter that period. This is the
    //     principled closed-phase analysis; it AGREES with the IAIF flow derivative
    //     on the closure landmark (verified on the injection control), so we keep the
    //     IAIF flow derivative `gd` as the per-period landmark source (it is the more
    //     stable estimate frame-wide. Per period we ALSO compute a CLOSED-PHASE
    //     covariance LPC flow derivative and prefer it when it yields a clean closure
    //     (the more principled, source-free estimate); otherwise the IAIF gd is used.
    //
    // --- per-period oq/ta/tilt off the flow DERIVATIVE. Each GCI-to-GCI segment is
    //     one pitch period; within it the OPENING is the rising onset of the open-
    //     phase excursion and the CLOSURE is the sharp negative-derivative peak near
    //     the segment end. The open phase (opening→closure) over the period is oq
    //     (LF te = oq·T0 from the cycle/opening start). ---
    let mut oqs = Vec::new();
    let mut tas = Vec::new();
    let mut tilts = Vec::new();
    for w in gci.windows(2) {
        let (g0, g1) = (w[0], w[1]);
        if g1 <= g0 || g1 - g0 < 8 || g1 >= n {
            continue;
        }
        let pp = g1 - g0;
        // PRIMARY: read the period off the IAIF flow derivative (stable frame-wide).
        if let Some((oq, ta, tilt)) = fit_one_period_deriv(&gd[g0..g1], &flow[g0..g1.min(n)]) {
            oqs.push(oq);
            tas.push(ta);
            tilts.push(tilt);
            continue;
        }
        // FALLBACK: CLOSED-PHASE covariance LPC (source-free tract over the lowest-
        // energy ~0.15·period window = the glottis-shut stretch) → period derivative,
        // used only where the IAIF gd left this period without a usable closure.
        let cp_len = ((pp as f32 * 0.15) as usize).max(tract_order + 2);
        if cp_len + 2 < pp && pp >= tract_order + 4 {
            let mut best_s = g0;
            let mut best_e = f64::INFINITY;
            let mut s = g0;
            while s + cp_len <= g1 {
                let e: f64 =
                    frame[s..s + cp_len].iter().map(|&v| (v as f64) * (v as f64)).sum();
                if e < best_e {
                    best_e = e;
                    best_s = s;
                }
                s += cp_len / 3 + 1;
            }
            let c_cp = covariance_lpc(&frame[best_s..(best_s + cp_len).min(n)], tract_order);
            let gd_cp = fir_inverse(&frame[g0..g1], &c_cp);
            if let Some((oq, ta, tilt)) = fit_one_period_deriv(&gd_cp, &flow[g0..g1]) {
                oqs.push(oq);
                tas.push(ta);
                tilts.push(tilt);
            }
        }
    }
    if oqs.is_empty() {
        return fit_oq_tilt_from_flow(&flow, &gd, period, fs, None);
    }
    let med = |v: &mut Vec<f32>| -> f32 {
        v.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
        v[v.len() / 2]
    };
    let oq = med(&mut oqs).clamp(0.3, 0.95);
    let ta = med(&mut tas).clamp(0.002, 0.25);
    let tilt = med(&mut tilts);
    vec![oq, ta, tilt]
}

/// Fit oq/ta/tilt from one GCI-to-GCI flow-derivative segment `gd` (+ the matching
/// glottal FLOW `pf`). The segment is exactly one pitch period (closure at both
/// ends). Open-quotient is read in the AMPLITUDE domain off the recovered FLOW —
/// the period-fraction over which the flow exceeds 50 % of its peak-to-trough
/// range. This is robust to the formant ripple the imperfect tract estimate leaves
/// in the flow (single-sample landmark picking on the derivative was phase-fragile
/// and non-monotone — verified on the injection control); the amplitude OQ is
/// monotone in the injected open-quotient and flat in ta and frame phase. An affine
/// stretch maps the (compressed) amplitude reading onto the LF open-quotient range.
fn fit_one_period_deriv(gd: &[f32], pf: &[f32]) -> Option<(f32, f32, f32)> {
    let pp = gd.len();
    if pp < 8 || pf.len() < 8 {
        return None;
    }
    // --- OPEN QUOTIENT (amplitude domain, robust): fraction of the period where the
    //     recovered glottal flow exceeds 50 % of its peak above the closed baseline. ---
    let fmin = pf.iter().cloned().fold(f32::INFINITY, f32::min);
    let fmax = pf.iter().cloned().fold(f32::NEG_INFINITY, f32::max);
    let rng = (fmax - fmin).max(1e-9);
    if rng <= 1e-6 {
        return None;
    }
    let thr = fmin + 0.50 * rng;
    let above = pf.iter().filter(|&&v| v > thr).count();
    let oq_raw = above as f32 / pp as f32;
    // AFFINE stretch: the amplitude reading is monotone but compressed — injected LF
    // oq 0.40..0.90 reads raw ~0.23..0.56 (injection control). Map raw onto the LF
    // range so the recovered code matches the forward model's parameterisation:
    //   oq_lf = 0.40 + (oq_raw - 0.23) · (0.90 - 0.40) / (0.56 - 0.23).
    let oq = 0.40 + (oq_raw - 0.23) * (0.50 / 0.33);
    // --- RETURN PHASE / ta: decay of the closure at the segment START (the previous
    //     GCI) — samples from index 1 for |derivative| to fall to 1/e of the start
    //     excitation, as a period fraction. (Segment starts AT a GCI.) ---
    let exc0 = gd
        .iter()
        .take((pp / 3).max(2))
        .cloned()
        .fold(0.0f32, |m, v| m.min(v))
        .abs()
        .max(1e-9);
    let mut decay = 1usize;
    let mut i = 1usize;
    while i + 1 < pp && gd[i].abs() > exc0 / std::f32::consts::E {
        i += 1;
        decay += 1;
    }
    let ta = decay as f32 / pp as f32;
    // TILT: low/high energy split of the FLOW at fs/4 (one-pole) — softer voice
    // rolls off faster (more low-band energy).
    let mut prev = 0.0f64;
    let (mut lo_e, mut hi_e) = (0.0f64, 0.0f64);
    for &v in pf {
        let vv = v as f64;
        let lp = 0.5 * vv + 0.5 * prev;
        prev = lp;
        lo_e += lp * lp;
        let hp = vv - lp;
        hi_e += hp * hp;
    }
    let tilt = (10.0 * (lo_e.max(1e-12) / hi_e.max(1e-12)).log10()) as f32;
    Some((oq, ta, tilt))
}

/// Fallback oq/tilt read from the whole-frame flow (no usable GCI pairs): anchor
/// one period at the strongest closure (global derivative min) and read it.
fn fit_oq_tilt_from_flow(
    flow: &[f32],
    gd: &[f32],
    period: usize,
    _fs: u32,
    _hint: Option<usize>,
) -> Vec<f32> {
    let n = flow.len();
    // strongest excitation = global min of derivative = a GCI; anchor a period there.
    let mut clo = 0usize;
    let mut clo_v = f32::INFINITY;
    for (i, &v) in gd.iter().enumerate() {
        if v < clo_v {
            clo_v = v;
            clo = i;
        }
    }
    let s = clo;
    let e = (s + period).min(n);
    if e <= s + 8 {
        return vec![0.6, 0.01, 0.0];
    }
    match fit_one_period_deriv(&gd[s..e], &flow[s..e]) {
        Some((oq, ta, tilt)) => vec![oq.clamp(0.3, 0.95), ta.clamp(0.002, 0.25), tilt],
        None => vec![0.6, 0.01, 0.0],
    }
}

/// CEPSTRAL-ENVELOPE FORMANTS — excitation-robust formant estimation by
/// HOMOMORPHIC DECONVOLUTION (the agent's own named gap: cepstral liftering /
/// cepstrum / homomorphic deconvolution).
///
/// THE PRINCIPLE (ozma_whisper_message_is_the_filter): a speech frame is the
/// CONVOLUTION of the SOURCE (glottal pulses when voiced, noise when whispered)
/// with the FILTER (the vocal-tract resonance envelope). In the log-spectral
/// domain that convolution becomes an ADDITION, and the cepstrum (the IDFT of the
/// log-magnitude spectrum) SEPARATES them along the quefrency axis:
///   * LOW quefrency  = the slowly-varying spectral ENVELOPE = the FILTER.
///   * HIGH quefrency  = the fast spectral ripple (harmonic comb when voiced,
///                       noise texture when whispered) = the SOURCE.
/// LIFTERING (keeping only the low-quefrency cepstral coefficients) and
/// reconstructing the spectrum recovers the SMOOTH FILTER ENVELOPE with the source
/// removed. Peak-picking THAT envelope yields formants that are robust to whether
/// the excitation was a harmonic pulse train (voiced) or noise (whisper) — exactly
/// what the naive LPC pole estimate fails to deliver off this blurry 8 kHz cochlea
/// (the LPC poles chase the harmonic structure / get pulled by the source).
///
/// vs LPC roots: LPC fits an all-pole model whose poles are pulled toward strong
/// harmonics of the source (especially on the under-sampled, harmonically-sparse
/// FSDD data); the liftered cepstral envelope has the source's comb DIVIDED OUT
/// before any peak is read, so the SAME word read voiced vs whispered gives nearly
/// the SAME envelope -> nearly the SAME formants.
///
/// Returns a FLAT vector [f1,bw1, f2,bw2, f3,bw3, ...] ascending by frequency, the
/// SAME layout as `lpc_formants_bw`, so it is a drop-in replacement on the filter
/// path. `n_formants` peaks are returned (zero-padded if fewer real peaks are
/// found in band). `lifter` is the cepstral cutoff quefrency (number of low cepstral
/// coefficients kept = the envelope smoothness; ~ fs/f0_min keeps the envelope but
/// discards the harmonic comb). Bandwidth is read from the half-power width of each
/// envelope peak (sharper peak = narrower bw = more resonance-like).
pub fn cepstral_formants(
    frame: &[f32],
    fs: u32,
    f_lo: f32,
    f_hi: f32,
    n_formants: usize,
    lifter: usize,
) -> Vec<f32> {
    use rustfft::FftPlanner;
    let n = frame.len();
    let out_empty = vec![0.0f32; 2 * n_formants];
    if n < 64 || f_hi <= f_lo || n_formants == 0 {
        return out_empty;
    }
    // FFT size: next power of two >= frame length, for a clean log-spectrum.
    let mut nfft = 1usize;
    while nfft < n {
        nfft <<= 1;
    }
    // Hamming-window the (mean-removed) frame.
    let mean = frame.iter().map(|&v| v as f64).sum::<f64>() / n as f64;
    let denom = (n - 1).max(1) as f64;
    let mut planner = FftPlanner::<f64>::new();
    let fwd = planner.plan_fft_forward(nfft);
    let inv = planner.plan_fft_inverse(nfft);
    let mut buf: Vec<Complex<f64>> = vec![Complex::new(0.0, 0.0); nfft];
    for (i, b) in buf.iter_mut().enumerate().take(n) {
        let w = 0.54 - 0.46 * (2.0 * std::f64::consts::PI * i as f64 / denom).cos();
        b.re = (frame[i] as f64 - mean) * w;
    }
    fwd.process(&mut buf);
    // log-magnitude spectrum (full, symmetric).
    let mut logmag: Vec<Complex<f64>> = buf
        .iter()
        .map(|c| Complex::new((c.norm() + 1e-9).ln(), 0.0))
        .collect();
    // real cepstrum = IDFT(log|X|).
    inv.process(&mut logmag);
    let scale = 1.0 / nfft as f64;
    let mut cep: Vec<Complex<f64>> = logmag.iter().map(|c| c * scale).collect();
    // LIFTER: keep low-quefrency coefficients (the envelope), zero the rest (the
    // source comb / noise ripple). Symmetric lifter (q and nfft-q).
    let cut = lifter.clamp(2, nfft / 2);
    for q in 0..nfft {
        let qq = q.min(nfft - q); // distance to DC, symmetric
        if qq > cut {
            cep[q] = Complex::new(0.0, 0.0);
        }
    }
    // back to the (smooth) log-spectrum envelope.
    fwd.process(&mut cep);
    let half = nfft / 2;
    let env: Vec<f64> = cep.iter().take(half + 1).map(|c| c.re).collect();
    // PEAK-PICK the envelope in [f_lo, f_hi]: local maxima (env[k]>env[k-1] &&
    // env[k]>env[k+1]). bandwidth from the half-power (-3 dB ~ -0.345 in ln-units
    // ... use the points where the envelope falls by `DROP` ln-units either side).
    let bin_hz = fs as f64 / nfft as f64;
    let k_lo = ((f_lo as f64 / bin_hz).floor() as usize).max(1);
    let k_hi = ((f_hi as f64 / bin_hz).ceil() as usize).min(half - 1);
    if k_hi <= k_lo {
        return out_empty;
    }
    const DROP: f64 = 0.3465735; // ln(2)/2 ~ the -3 dB half-power level in ln-magnitude
    let mut peaks: Vec<(f64, f64, f64)> = Vec::new(); // (freq, bw, prominence)
    for k in k_lo..=k_hi {
        if env[k] > env[k - 1] && env[k] >= env[k + 1] {
            // parabolic interpolation for a sub-bin peak frequency.
            let (yl, yc, yr) = (env[k - 1], env[k], env[k + 1]);
            let d = yl - 2.0 * yc + yr;
            let delta = if d.abs() > 1e-12 { 0.5 * (yl - yr) / d } else { 0.0 };
            let f_peak = (k as f64 + delta) * bin_hz;
            // bandwidth: walk left/right until the envelope drops by DROP ln-units.
            let target = yc - DROP;
            let mut kl = k;
            while kl > k_lo && env[kl] > target {
                kl -= 1;
            }
            let mut kr = k;
            while kr < k_hi && env[kr] > target {
                kr += 1;
            }
            let bw = ((kr - kl) as f64 * bin_hz).max(bin_hz);
            // PROMINENCE = height of the peak above the higher of its two flanking
            // VALLEYS (not absolute height): a formant's absolute envelope level
            // falls with frequency (spectral tilt), so absolute height would always
            // rank low formants over high ones and drop F3. Local prominence (how
            // much the peak stands out from its surrounding dips) is the resonance
            // strength independent of the overall tilt — this keeps the genuine
            // higher formants and rejects shallow low-quefrency ripple bumps.
            // left valley:
            let mut vl = k;
            while vl > k_lo && env[vl - 1] < env[vl] {
                vl -= 1;
            }
            // right valley:
            let mut vr = k;
            while vr < k_hi && env[vr + 1] < env[vr] {
                vr += 1;
            }
            let valley = env[vl].max(env[vr]);
            let prom = yc - valley;
            peaks.push((f_peak, bw, prom));
        }
    }
    // keep the n_formants MOST PROMINENT peaks, then re-sort ascending by frequency.
    peaks.sort_by(|a, b| b.2.partial_cmp(&a.2).unwrap_or(std::cmp::Ordering::Equal));
    peaks.truncate(n_formants);
    peaks.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal));
    let mut out = vec![0.0f32; 2 * n_formants];
    for (i, (f, bw, _)) in peaks.iter().enumerate() {
        out[2 * i] = *f as f32;
        out[2 * i + 1] = *bw as f32;
    }
    out
}

/// SPREAD-PRESERVING f0 — octave-robust pitch via the cepstrum, with an
/// autocorrelation cross-check that REJECTS octave errors. The plain autocorr
/// f0 (`f0_autocorr`) octave-doubles on low-male voices (p232 reads 372 Hz);
/// here we take the cepstral peak (the rahmonic of the source quefrency, which
/// does NOT double the way the waveform-autocorr sub-harmonic does) and, if the
/// autocorr and cepstral estimates disagree by ~2x, prefer the LOWER (the true
/// fundamental — an octave error always reads HIGH). Returns f0 Hz, 0 if unvoiced.
pub fn f0_cepstral(frame: &[f32], fs: u32, f_lo: f32, f_hi: f32, voicing_thresh: f32) -> f32 {
    let n = frame.len();
    if n < 64 || f_lo <= 0.0 || f_hi <= f_lo {
        return 0.0;
    }
    // autocorr estimate (reuse the existing, validated routine).
    let ac = f0_autocorr(frame, fs, f_lo, f_hi, voicing_thresh);
    // cepstrum: real cepstrum = IDFT(log|DFT(x)|). Find the peak in the quefrency
    // range [fs/f_hi, fs/f_lo]. Pure DFT (no external FFT dep; n is a frame).
    let mean = frame.iter().map(|&v| v as f64).sum::<f64>() / n as f64;
    // Hamming window for a cleaner log-spectrum.
    let denom = (n - 1).max(1) as f64;
    let xw: Vec<f64> = frame
        .iter()
        .enumerate()
        .map(|(i, &v)| {
            let w = 0.54 - 0.46 * (2.0 * std::f64::consts::PI * i as f64 / denom).cos();
            (v as f64 - mean) * w
        })
        .collect();
    // log-magnitude spectrum over [0, n/2].
    let half = n / 2;
    let mut logmag = vec![0.0f64; half + 1];
    for (k, lm) in logmag.iter_mut().enumerate() {
        let mut re = 0.0f64;
        let mut im = 0.0f64;
        let w = -2.0 * std::f64::consts::PI * k as f64 / n as f64;
        for (t, &xt) in xw.iter().enumerate() {
            let ang = w * t as f64;
            re += xt * ang.cos();
            im += xt * ang.sin();
        }
        *lm = (re * re + im * im + 1e-12).sqrt().ln();
    }
    // real cepstrum c[q] = (1/N) sum_k logmag[k] cos(2π k q / N), symmetric spectrum.
    let lag_min = ((fs as f32 / f_hi).floor() as usize).max(2);
    let lag_max = ((fs as f32 / f_lo).ceil() as usize).min(n / 2);
    if lag_max <= lag_min {
        return ac;
    }
    let mut best_q = 0usize;
    let mut best_v = f64::NEG_INFINITY;
    for q in lag_min..=lag_max {
        let mut acc = logmag[0];
        for k in 1..=half {
            let sign = 2.0; // full spectrum symmetry
            acc += sign * logmag[k] * (2.0 * std::f64::consts::PI * k as f64 * q as f64 / n as f64).cos();
        }
        if acc > best_v {
            best_v = acc;
            best_q = q;
        }
    }
    let cep_f0 = if best_q > 0 { fs as f32 / best_q as f32 } else { 0.0 };
    // OCTAVE-ROBUST FUSION: if autocorr is voiced and reads ~2x the cepstral
    // estimate (or vice versa), the higher one is the octave error -> take lower.
    if ac > 0.0 && cep_f0 > 0.0 {
        let ratio = ac.max(cep_f0) / ac.min(cep_f0);
        if (1.7..2.3).contains(&ratio) {
            return ac.min(cep_f0); // octave error -> the fundamental is the lower
        }
        // otherwise they agree (or cepstrum failed) -> trust autocorr (validated).
        return ac;
    }
    if ac > 0.0 {
        ac
    } else {
        0.0
    }
}

// =========================================================================
//  LPC ANALYSIS-RESYNTHESIS — the source-filter chain, run FORWARD from the
//  REAL recovered residual. This is the piece that makes copy-synthesis
//  near-transparent (it is how speech codecs work): we do NOT hand-set a
//  synthetic Klatt source — we KEEP the true LPC residual that falls out of
//  inverse-filtering and drive the recovered all-pole tract filter with it.
//  Source-filter is the actual physics of speech; recovering the true source
//  + true filter and running them forward regenerates the real signal.
// =========================================================================

/// One step of the levinson analysis on a frame: returns (a, residual) where
/// `a` are the all-pole coeffs (a[0]=1) on the PRE-EMPHASISED, UNwindowed frame
/// and `residual` is the inverse-filter output e[n] = sum_k a_k x[n-k] over the
/// SAME pre-emphasised (but here NOT windowed — we want the residual to drive a
/// clean overlap-add resynthesis) samples. The autocorrelation IS computed on a
/// windowed copy (stable LPC estimate), but the residual is produced on the raw
/// pre-emphasised frame so it tiles seamlessly under overlap-add.
fn lpc_frame_analysis(frame: &[f32], order: usize, pre_emph: f32) -> (Vec<f64>, Vec<f32>) {
    let n = frame.len();
    // pre-emphasised (unwindowed) frame — the resynthesis target.
    let mut xpe = vec![0.0f32; n];
    if n == 0 {
        return (vec![1.0], xpe);
    }
    xpe[0] = frame[0];
    for i in 1..n {
        xpe[i] = frame[i] - pre_emph * frame[i - 1];
    }
    if n < order + 2 {
        return (vec![1.0], xpe);
    }
    // windowed copy for a stable autocorrelation estimate.
    let denom = (n - 1).max(1) as f32;
    let mut xw = xpe.clone();
    for (i, xi) in xw.iter_mut().enumerate() {
        let w = 0.54 - 0.46 * (2.0 * std::f32::consts::PI * i as f32 / denom).cos();
        *xi *= w;
    }
    let r = lpc_autocorr(&xw, order);
    if r.is_empty() || r[0] <= 0.0 {
        return (vec![1.0], xpe);
    }
    let (a, _gain) = levinson_durbin(&r, order);
    // residual on the UNwindowed pre-emphasised frame: e[n] = sum_k a_k x[n-k].
    let mut e = vec![0.0f32; n];
    for nn in 0..n {
        let mut acc = 0.0f64;
        for (k, &ak) in a.iter().enumerate() {
            if nn >= k {
                acc += ak * xpe[nn - k] as f64;
            }
        }
        e[nn] = acc as f32;
    }
    (a, e)
}

/// Run the all-pole synthesis filter 1/A(z) forward over an excitation block,
/// carrying the filter state `hist` (the last `order` output samples) ACROSS
/// frames so the resynthesis is continuous. y[n] = e[n] - sum_{k>=1} a_k y[n-k].
fn all_pole_filter(exc: &[f32], a: &[f64], hist: &mut Vec<f32>) -> Vec<f32> {
    let order = a.len().saturating_sub(1);
    let mut y = vec![0.0f32; exc.len()];
    for n in 0..exc.len() {
        let mut acc = exc[n] as f64;
        for k in 1..=order {
            // y[n-k]: from this block if available, else from carried history.
            let yv = if n >= k {
                y[n - k]
            } else {
                let idx = hist.len() as isize - (k as isize - n as isize);
                if idx >= 0 && (idx as usize) < hist.len() {
                    hist[idx as usize]
                } else {
                    0.0
                }
            };
            acc -= a[k] * yv as f64;
        }
        y[n] = acc as f32;
    }
    // update history with the tail of this block.
    let keep = order;
    let mut newh: Vec<f32> = Vec::with_capacity(keep);
    if y.len() >= keep {
        newh.extend_from_slice(&y[y.len() - keep..]);
    } else {
        let need = keep - y.len();
        if hist.len() >= need {
            newh.extend_from_slice(&hist[hist.len() - need..]);
        }
        newh.extend_from_slice(&y);
    }
    *hist = newh;
    y
}

/// De-emphasis: invert the pre-emphasis applied at analysis. y[n] = x[n] +
/// pre_emph * y[n-1], state carried in `prev`.
fn deemphasis(x: &[f32], pre_emph: f32, prev: &mut f32) -> Vec<f32> {
    let mut y = vec![0.0f32; x.len()];
    let mut p = *prev;
    for n in 0..x.len() {
        let v = x[n] + pre_emph * p;
        y[n] = v;
        p = v;
    }
    *prev = p;
    y
}

/// COPY-RESYNTHESIS: analyse the whole signal frame-by-frame (hop = frame/2),
/// KEEP the true LPC residual as the excitation, resynthesise by driving the
/// recovered per-frame all-pole tract filter 1/A(z) with that residual, with
/// inter-frame filter-state continuity + de-emphasis. The output should be
/// near-identical to the input (this is the proof the chain is faithful —
/// codec-style analysis-by-synthesis, NOT a synthetic source).
///
/// Frame-by-frame: each NON-overlapping hop region is synthesised with the LPC
/// of the analysis frame CENTRED on it, the residual of that same hop driving
/// the filter, state carried across hops. `pre_emph` the pre-emphasis coeff.
pub fn lpc_copy_resynth(
    signal: &[f32],
    fs: u32,
    order: usize,
    frame_len: usize,
    pre_emph: f32,
) -> Vec<f32> {
    let _ = fs;
    let n = signal.len();
    if n == 0 || frame_len < order + 2 {
        return signal.to_vec();
    }
    let hop = (frame_len / 2).max(1);
    let mut out = vec![0.0f32; n];
    let mut hist: Vec<f32> = Vec::new();
    let mut deemp_prev = 0.0f32;
    let mut pos = 0usize;
    while pos < n {
        // analysis frame centred on the hop: [pos - frame_len/2 .. + frame_len/2]
        let half = frame_len / 2;
        let astart = pos.saturating_sub(half.saturating_sub(hop / 2));
        let aend = (astart + frame_len).min(n);
        let frame = &signal[astart..aend];
        let (a, _) = lpc_frame_analysis(frame, order, pre_emph);
        // residual for THIS hop only (the segment we will emit), pre-emphasised.
        let hop_end = (pos + hop).min(n);
        // build the pre-emphasised excitation of the hop directly (so it tiles).
        let hlen = hop_end - pos;
        let mut exc = vec![0.0f32; hlen];
        for i in 0..hlen {
            let gi = pos + i;
            let xpe = if gi == 0 {
                signal[gi]
            } else {
                signal[gi] - pre_emph * signal[gi - 1]
            };
            // residual e = sum_k a_k * xpe[gi-k]
            let mut acc = 0.0f64;
            for (k, &ak) in a.iter().enumerate() {
                let j = gi as isize - k as isize;
                if j >= 0 {
                    let xj = if j == 0 {
                        signal[0]
                    } else {
                        signal[j as usize] - pre_emph * signal[(j - 1) as usize]
                    };
                    acc += ak * xj as f64;
                }
            }
            exc[i] = acc as f32;
        }
        let yhop = all_pole_filter(&exc, &a, &mut hist);
        let yde = deemphasis(&yhop, pre_emph, &mut deemp_prev);
        for i in 0..hlen {
            out[pos + i] = yde[i];
        }
        pos += hop;
    }
    out
}

/// CROSS-RESYNTHESIS (the impressionist render): drive a SEQUENCE of all-pole
/// tract filters (the SPEAKER's recovered filters, one per frame) with a given
/// excitation sequence (the CONTENT's residual, or a pitch-rescaled version of
/// the speaker's own residual). `a_frames` is the flat concatenation of per-frame
/// coeff vectors each of length `order+1`; `exc` the full excitation; `hop` the
/// samples per frame. Filter state + de-emphasis carried across frames. This is
/// how we hold the speaker (filter + source character) and swap the content.
pub fn lpc_cross_resynth(
    a_frames: &[f32],
    exc: &[f32],
    order: usize,
    hop: usize,
    pre_emph: f32,
) -> Vec<f32> {
    let stride = order + 1;
    if stride == 0 || hop == 0 || a_frames.len() < stride || exc.is_empty() {
        return exc.to_vec();
    }
    let n_frames = a_frames.len() / stride;
    let mut out = vec![0.0f32; exc.len()];
    let mut hist: Vec<f32> = Vec::new();
    let mut deemp_prev = 0.0f32;
    let mut pos = 0usize;
    let mut fi = 0usize;
    while pos < exc.len() {
        let f = fi.min(n_frames.saturating_sub(1));
        let a: Vec<f64> = a_frames[f * stride..(f + 1) * stride]
            .iter()
            .map(|&v| v as f64)
            .collect();
        let end = (pos + hop).min(exc.len());
        let yblk = all_pole_filter(&exc[pos..end], &a, &mut hist);
        let yde = deemphasis(&yblk, pre_emph, &mut deemp_prev);
        for (i, &v) in yde.iter().enumerate() {
            out[pos + i] = v;
        }
        pos = end;
        fi += 1;
    }
    out
}

/// Per-frame LPC coefficient track of a whole signal: returns the flat
/// concatenation of per-frame `a` vectors (each length order+1, a[0]=1), one
/// frame per `hop`. The SPEAKER's vocal-tract filter trajectory — the filter
/// half of the impression. Pure DSP; the analysis only, no synthesis.
pub fn lpc_coeff_track(
    signal: &[f32],
    order: usize,
    frame_len: usize,
    hop: usize,
    pre_emph: f32,
) -> Vec<f32> {
    let n = signal.len();
    let stride = order + 1;
    if n == 0 || hop == 0 || frame_len < order + 2 {
        return Vec::new();
    }
    let mut out: Vec<f32> = Vec::new();
    let half = frame_len / 2;
    let mut pos = 0usize;
    while pos < n {
        let astart = pos.saturating_sub(half);
        let aend = (astart + frame_len).min(n);
        let (a, _e) = lpc_frame_analysis(&signal[astart..aend], order, pre_emph);
        let mut av: Vec<f32> = a.iter().map(|&v| v as f32).collect();
        av.resize(stride, 0.0);
        out.extend_from_slice(&av);
        pos += hop;
    }
    out
}

/// Whole-signal LPC residual (the excitation track) at the SAME hop/frame as
/// lpc_coeff_track, concatenated frame-by-frame (non-overlapping hop segments,
/// each segment's residual computed under that segment's centred-frame LPC).
/// This is the TRUE recovered source over the whole utterance — the piece that
/// killed Klatt when thrown away. Pure DSP.
pub fn lpc_residual_track(
    signal: &[f32],
    order: usize,
    frame_len: usize,
    hop: usize,
    pre_emph: f32,
) -> Vec<f32> {
    let n = signal.len();
    if n == 0 || hop == 0 || frame_len < order + 2 {
        return vec![0.0; n];
    }
    let mut out = vec![0.0f32; n];
    let half = frame_len / 2;
    let mut pos = 0usize;
    while pos < n {
        let astart = pos.saturating_sub(half);
        let aend = (astart + frame_len).min(n);
        let (a, _e) = lpc_frame_analysis(&signal[astart..aend], order, pre_emph);
        let hop_end = (pos + hop).min(n);
        for gi in pos..hop_end {
            let mut acc = 0.0f64;
            for (k, &ak) in a.iter().enumerate() {
                let j = gi as isize - k as isize;
                if j >= 0 {
                    let xj = if j == 0 {
                        signal[0]
                    } else {
                        signal[j as usize] - pre_emph * signal[(j - 1) as usize]
                    };
                    acc += ak * xj as f64;
                }
            }
            out[gi] = acc as f32;
        }
        pos += hop;
    }
    out
}

// =========================================================================
//  SOURCE-CHARACTER TRANSPLANT — the held-voice factoring.
//
//  To render NEW content in speaker S's HELD voice, the content carries the
//  FILTER TRAJECTORY (the gesture / word) and S carries the SOURCE CHARACTER
//  (f0 + glottal-pulse shape + spectral tilt). The strict-filter-only swap
//  (B') showed identity rides mostly in the SOURCE, not the filter — so the
//  impression must transplant S's source onto the content's excitation while
//  KEEPING the content's per-hop timing so the filter trajectory (the word)
//  still lines up.
//
//  `glottal_warp_residual` does the source transplant on the content's
//  residual (the excitation), pitch-synchronously, with NO net / .fit:
//    1. PITCH TRANSPLANT (PSOLA-style): find the content's pitch pulses
//       (period from the content's per-hop f0 track), and re-lay the source
//       pulses at S's target period (= S's f0). Each content pulse's local
//       shape is preserved (overlap-add of the windowed source grains) but
//       the INTER-pulse spacing becomes S's pitch. Holding the content's
//       grain shape keeps the WORD's fine structure; re-spacing to S's f0
//       sets S's voice pitch.
//    2. SPECTRAL-TILT WARP: a one-pole emphasis that pushes the residual's
//       low/high balance toward S's recovered tilt (breathy vs pressed
//       source colour). Owned 1-pole DSP.
//    3. OPEN-QUOTIENT / softness: a per-pulse grain width set by S's open
//       quotient (a wider open phase = a softer, breathier source).
//  Pure pitch-synchronous overlap-add + one-pole tilt — codec/PSOLA DSP, no
//  fit, no net, no learned parameter. Returns a new excitation of the SAME
//  length as `exc` so the content's filter trajectory drives it hop-for-hop.
pub fn glottal_warp_residual(
    exc: &[f32],
    f0_track: &[f32],
    hop: usize,
    fs: u32,
    tgt_f0: f32,
    tgt_oq: f32,
    tgt_tilt_db: f32,
    src_tilt_db: f32,
) -> Vec<f32> {
    let n = exc.len();
    if n == 0 || hop == 0 || tgt_f0 <= 0.0 {
        return exc.to_vec();
    }
    let fsf = fs as f32;
    let tgt_period = (fsf / tgt_f0).round().max(2.0) as usize;

    let f0_at = |i: usize| -> f32 {
        if f0_track.is_empty() {
            return 0.0;
        }
        let h = (i / hop).min(f0_track.len() - 1);
        f0_track[h]
    };

    // 1) PITCH-SYNCHRONOUS pulse re-laying (PSOLA). Walk the content excitation;
    //    at each pulse instant extract a Hann grain centred on the local energy
    //    peak, then re-place grains spaced by S's target period. Grain CONTENT =
    //    the speaker-independent source detail of the word; SPACING = S's pitch.
    //    Voiceless (f0==0) regions copy through (noise has no pitch).
    let mut out = vec![0.0f32; n];
    let oq = tgt_oq.clamp(0.3, 0.95);
    let grain_half = ((tgt_period as f32) * (0.5 + 0.5 * oq)).round().max(2.0) as usize;

    // Decoupled cursors: the OUTPUT cursor `next_out` advances by S's target
    // period each grain (sets S's pitch); the READ cursor `read_pos` walks the
    // content, advancing one content period only when the output has caught up to
    // it. So when S's pitch is HIGHER (tgt_period < cperiod) a content pulse is
    // REUSED for several output grains (pitch up); when LOWER, content pulses are
    // SKIPPED (pitch down). Either way the word duration ~ the content's (the read
    // cursor sweeps the whole content), so the filter trajectory still aligns.
    let mut read_pos = 0usize;
    let mut next_out = 0usize;
    let mut last_peak: usize = 0;
    while next_out < n {
        let cf0 = f0_at(read_pos.min(n.saturating_sub(1)));
        if cf0 <= 0.0 {
            // unvoiced: copy a hop of content straight through at the output cursor
            // (noise has no pitch to re-space); advance both cursors together.
            let end = (next_out + hop).min(n);
            let rend = (read_pos + hop).min(n);
            for i in 0..(end - next_out).min(rend - read_pos) {
                out[next_out + i] += exc[read_pos + i];
            }
            next_out = end;
            read_pos = rend.min(n);
            if read_pos >= n {
                break;
            }
            continue;
        }
        let cperiod = (fsf / cf0).round().max(2.0) as usize;
        // locate the content pulse peak in [read_pos, read_pos+cperiod).
        let search_end = (read_pos + cperiod).min(n);
        let mut peak_i = read_pos.min(n.saturating_sub(1));
        let mut peak_v = -1.0f32;
        for i in read_pos..search_end {
            let v = exc[i].abs();
            if v > peak_v {
                peak_v = v;
                peak_i = i;
            }
        }
        last_peak = peak_i;
        // place a Hann grain centred on this content peak at the output cursor.
        let g_lo = peak_i.saturating_sub(grain_half);
        let g_hi = (peak_i + grain_half).min(n);
        let glen = g_hi - g_lo;
        if glen >= 2 {
            for k in 0..glen {
                let gi = g_lo + k;
                let w = 0.5 - 0.5 * (2.0 * std::f32::consts::PI * k as f32
                    / (glen as f32 - 1.0).max(1.0)).cos();
                let rel = gi as isize - peak_i as isize;
                let oi = next_out as isize + rel;
                if oi >= 0 && (oi as usize) < n {
                    out[oi as usize] += w * exc[gi];
                }
            }
        }
        next_out += tgt_period;
        // advance the READ cursor toward the OUTPUT cursor: keep the content peak
        // we read roughly in step with where the output has reached, so the whole
        // content is swept exactly once over the utterance (word timing held).
        if next_out > last_peak + cperiod / 2 {
            read_pos = peak_i + cperiod.max(1);
        }
        if read_pos >= n {
            // content exhausted but output not — stop (avoid trailing silence loop).
            break;
        }
    }

    // energy-normalise per hop to the content's local level (keep the word's
    // loudness contour — a content property — so the filter drive is right).
    let n_hops = (n + hop - 1) / hop;
    for h in 0..n_hops {
        let a = h * hop;
        let b = (a + hop).min(n);
        if b <= a {
            continue;
        }
        let e_in: f32 = exc[a..b].iter().map(|&v| v * v).sum();
        let e_out: f32 = out[a..b].iter().map(|&v| v * v).sum();
        if e_out > 1e-12 && e_in > 1e-12 {
            let g = (e_in / e_out).sqrt();
            for v in out[a..b].iter_mut() {
                *v *= g;
            }
        }
    }

    // 2) SPECTRAL-TILT WARP toward S's source colour — warp the DIFFERENCE
    //    (tgt - src): +ve => S softer (LF lean, integrate), -ve => S pressed.
    let dtilt = (tgt_tilt_db - src_tilt_db).clamp(-12.0, 12.0);
    let alpha = (dtilt / 20.0).clamp(-0.6, 0.6);
    if alpha.abs() > 1e-3 {
        let mut prev = 0.0f32;
        for v in out.iter_mut() {
            let y = *v + alpha * prev;
            prev = *v;
            *v = y;
        }
    }

    out
}

/// SOURCE-IMPRINTED EXCITATION TRANSPLANT — the held-voice fix.
///
/// WHY this exists (the 16 kHz diagnosis, docs/voice_impression_16k.md):
/// `glottal_warp_residual` re-lays the CONTENT donor's own residual grains
/// (only re-spacing them to S's f0 + a weak global 1-pole tilt warp). The grain
/// SHAPE stays the donor's, so S's open-quotient and return-phase (spectral
/// tilt) — which are SOURCE-PULSE-SHAPE properties — never enter the excitation.
/// The all-pole resynth then LAUNDERS oq/tilt (they flatten across renders, full
/// 4-D identity collapses to 1/6), and donor-grain REUSE at high f0 (one content
/// pulse placed for several output grains) double-excites the tract and the
/// synthesis RINGS / inflates the measured f0 (170->198, 200->216).
///
/// THE FIX — put the source CHARACTER in the EXCITATION (the f1b75b74 / 133 dB
/// principle: source character lives in the excitation, not the all-pole filter
/// that washes it). Instead of re-laying the donor's grains, SYNTHESIZE a fresh
/// LF (Liljencrants-Fant) glottal-flow-derivative pulse AT S's recovered oq +
/// ta_frac (return phase = spectral tilt) + f0, ONE PULSE PER S-PERIOD (pitch-
/// synchronous, no reuse => no ringing), and MODULATE that pulse train by the
/// CONTENT's per-hop residual ENERGY ENVELOPE so the WORD's loudness contour +
/// voiced/unvoiced structure survive (the word is in the FILTER trajectory + the
/// envelope; the voice is in the LF pulse). Unvoiced hops copy the content
/// residual straight through (frication has no glottal pulse). Pure owned DSP:
/// closed-form LF period + energy modulation + copy-through. NO net / .fit /
/// gradient / loss / sweep.
///
///   exc[n] (S's voice) = LF_period(oq_S, am, ta_S) re-laid every fs/f0_S samples,
///                        scaled per hop to sqrt(content_hop_energy),
///                        on voiced hops; content_residual[n] on unvoiced hops.
///
/// `am` (asymmetry / speed quotient ~0.7) is a fixed modal default — the two
/// carried source identity knobs are oq and ta_frac (recovered per speaker).
///
/// `bw_floor_hz` (>0) widens the all-pole tract bandwidths at SYNTHESIS time for
/// HIGH voices — the order-18 all-pole filter has sharp poles that ring when
/// excited by a sparse high-f0 pulse train. We DO NOT touch the filter here (that
/// stays in lpc_cross_resynth); instead we ensure the excitation itself does not
/// over-drive: the LF return phase (ta_frac) already band-limits the pulse, and
/// the one-pulse-per-period rule removes the reuse double-excitation. The floor
/// is reserved for the resynth caller; this primitive's anti-ring is structural.
pub fn lf_excitation_transplant(
    content_res: &[f32],
    content_f0_track: &[f32],
    hop: usize,
    fs: u32,
    tgt_f0: f32,
    tgt_oq: f32,
    tgt_ta_frac: f32,
    am: f32,
) -> Vec<f32> {
    let n = content_res.len();
    if n == 0 || hop == 0 || tgt_f0 <= 0.0 {
        return content_res.to_vec();
    }
    let fsf = fs as f32;
    let tgt_period = (fsf / tgt_f0).round().max(2.0) as usize;

    // S's source pulse — ONE LF glottal-flow-derivative period, carrying S's open
    // quotient (oq) and spectral tilt (ta_frac = return-phase length). This is the
    // pulse SHAPE the all-pole filter cannot launder: oq/tilt now live in the
    // excitation, exactly as the source-character principle requires.
    let pulse = lf_glottal_period(tgt_period, tgt_oq, am, tgt_ta_frac);

    // content per-hop RMS envelope (the WORD's loudness contour + voiced/unvoiced
    // structure — a content property we keep; the voice is the pulse, the word is
    // the envelope + the filter trajectory driven downstream).
    let n_hops = (n + hop - 1) / hop;
    let mut hop_rms = vec![0.0f32; n_hops];
    for h in 0..n_hops {
        let a = h * hop;
        let b = (a + hop).min(n);
        if b <= a {
            continue;
        }
        let e: f32 = content_res[a..b].iter().map(|&v| v * v).sum();
        hop_rms[h] = (e / (b - a) as f32).sqrt();
    }

    let f0_at = |i: usize| -> f32 {
        if content_f0_track.is_empty() {
            return 0.0;
        }
        let h = (i / hop).min(content_f0_track.len() - 1);
        content_f0_track[h]
    };
    let rms_at = |i: usize| -> f32 {
        let h = (i / hop).min(hop_rms.len().saturating_sub(1));
        hop_rms[h]
    };

    let mut out = vec![0.0f32; n];
    let mut pos = 0usize;
    // Re-lay S's LF pulse every S-period on VOICED stretches; copy content through
    // on UNVOICED stretches (frication is sourceless noise — it must NOT be
    // pulse-replaced or the /s/ / /f/ vanishes and intelligibility drops).
    while pos < n {
        if f0_at(pos.min(n - 1)) <= 0.0 {
            // unvoiced hop: copy the content residual straight through.
            let end = (pos + hop).min(n);
            out[pos..end].copy_from_slice(&content_res[pos..end]);
            pos = end;
            continue;
        }
        // voiced: stamp ONE S-pulse at `pos`, scaled to the local content energy,
        // then advance exactly one S-period (pitch-synchronous, no reuse).
        let scale = rms_at(pos);
        let plen = pulse.len().min(n - pos);
        for k in 0..plen {
            out[pos + k] += pulse[k] * scale;
        }
        pos += tgt_period;
    }

    // Per-hop energy match to the content (keep the word's loudness contour exact;
    // the LF pulse set the SHAPE, the content sets the LEVEL). Skip unvoiced hops
    // (already copy-through at the right level).
    for h in 0..n_hops {
        let a = h * hop;
        let b = (a + hop).min(n);
        if b <= a || f0_at(a.min(n - 1)) <= 0.0 {
            continue;
        }
        let e_in: f32 = content_res[a..b].iter().map(|&v| v * v).sum();
        let e_out: f32 = out[a..b].iter().map(|&v| v * v).sum();
        if e_out > 1e-12 && e_in > 1e-12 {
            let g = (e_in / e_out).sqrt();
            for v in out[a..b].iter_mut() {
                *v *= g;
            }
        }
    }

    out
}

/// BANDWIDTH-FLOOR an LPC coefficient track — the anti-ring for high voices.
///
/// WHY (docs/voice_impression_16k.md): the high-order all-pole tract filter has
/// SHARP poles (narrow bandwidths). When a sparse high-f0 pulse train (a 200 Hz
/// female voice = a pulse every fs/200 samples) excites a near-unit-circle pole,
/// the filter RINGS between pulses and the measured render-f0 inflates (170->198,
/// 200->216 at 16 kHz). The fix is a classic, fit-free DSP move: BANDWIDTH
/// EXPANSION. Scaling the k-th LPC coefficient a[k] by γ^k pulls every pole
/// radially inward by the factor γ (|z| -> γ|z|), which WIDENS each pole's
/// bandwidth by Δbw ≈ -(fs/π)·ln(γ) Hz while leaving its FREQUENCY (the formant)
/// unchanged. A widened (more damped) pole settles within one pitch period, so it
/// cannot ring between sparse high-f0 pulses. We pick γ from a target bandwidth
/// FLOOR in Hz: γ = exp(-π·bw_floor_hz / fs). bw_floor_hz = 0 is a no-op
/// (identity); a few tens of Hz at 48 kHz is enough to kill the ringing without
/// audibly smearing the formants. Pure closed-form coefficient scaling — NO net,
/// NO fit, NO sweep; one exp() and a per-coefficient multiply.
pub fn lpc_bw_expand_track(a_frames: &[f32], order: usize, fs: u32, bw_floor_hz: f32) -> Vec<f32> {
    let stride = order + 1;
    if stride == 0 || bw_floor_hz <= 0.0 || a_frames.len() < stride {
        return a_frames.to_vec();
    }
    let gamma = (-std::f32::consts::PI * bw_floor_hz / fs as f32).exp();
    let mut out = a_frames.to_vec();
    let n_frames = out.len() / stride;
    for f in 0..n_frames {
        let base = f * stride;
        let mut gk = 1.0f32; // γ^0 = 1 (a[0] untouched)
        for k in 0..stride {
            out[base + k] *= gk;
            gk *= gamma;
        }
    }
    out
}

/// BUGGY (historical) lpc_roots_formants — reproduces the PRE-FIX behaviour for
/// an A/B measurement ONLY: the LPC coeffs were passed REVERSED (`a[::-1]`),
/// solving the RECIPROCAL polynomial so every pole landed OUTSIDE the unit
/// circle (bw = -fs/2pi·ln|z| < 0), AND the freq-only extractor filtered just
/// `bw < bw_max` (negative bandwidths slip through). Frequencies survive
/// (reciprocation preserves pole angle) but the bandwidth gate is sign-wrong,
/// so spurious wide poles are NOT rejected and genuine sharp poles can be — the
/// instrument the corrected version replaced. NOT for production: a measurement
/// of how much the bug throttled perception.
pub fn lpc_roots_formants_buggy(
    frame: &[f32],
    fs: u32,
    order: usize,
    pre_emph: f32,
    f_lo: f32,
    f_hi: f32,
    bw_max: f32,
) -> Vec<f32> {
    let x = preemph_window(frame, pre_emph);
    let n = x.len();
    if n < order + 2 {
        return Vec::new();
    }
    let r = lpc_autocorr(&x, order);
    if r.is_empty() || r[0] <= 0.0 {
        return Vec::new();
    }
    let (a, _gain) = levinson_durbin(&r, order);
    // THE BUG: reversed coeffs (reciprocal roots — poles outside the unit circle).
    let coeffs: Vec<f64> = a.iter().rev().copied().collect();
    let roots = poly_roots(&coeffs);
    let half_fs = fs as f64 / (2.0 * std::f64::consts::PI);
    let mut fmts: Vec<f32> = Vec::new();
    for z in roots {
        if z.im <= 0.0 {
            continue;
        }
        let ang = z.im.atan2(z.re);
        let f = (ang * fs as f64 / (2.0 * std::f64::consts::PI)) as f32;
        let bw = (-half_fs * (z.norm() + 1e-12).ln()) as f32;
        // THE BUG: only `bw < bw_max` — negative bandwidths (every pole here) pass.
        if f >= f_lo && f <= f_hi && bw < bw_max {
            fmts.push(f);
        }
    }
    fmts.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    fmts
}

/// HIGH-RESOLUTION f0 via YIN (de Cheveigné & Kawahara 2002) with PARABOLIC
/// INTERPOLATION — the standard sub-Hz pitch estimator, and the named fix for
/// CLOSELY-SPACED SAME-REGISTER voices (the three male VCTK speakers at 126/132/
/// 153 Hz that the integer-lag autocorr + broad cepstral peak collapse onto a
/// common ~120 Hz). YIN resolves them because it (a) measures the period from a
/// DIFFERENCE function (the squared-error between the frame and its lag-shifted
/// copy) whose minimum is SHARP at the true period — not a broad correlation
/// peak — and (b) refines that integer-lag minimum to a CONTINUOUS lag by fitting
/// a parabola through the difference values at (τ-1, τ, τ+1), giving sub-sample
/// period and therefore sub-Hz f0.
///
/// Steps (all classical, closed-form, NO net / fit / gradient / loss):
///   1. DIFFERENCE FUNCTION  d(τ) = Σ_i (x[i] − x[i+τ])²  over the analysis window.
///   2. CUMULATIVE-MEAN-NORMALISED DIFFERENCE  d'(τ) = d(τ) / [(1/τ)·Σ_{j≤τ} d(j)]
///      with d'(0)=1 — flattens the trivial τ→0 dip and makes an ABSOLUTE
///      threshold meaningful across frames/levels.
///   3. ABSOLUTE THRESHOLD  — the FIRST τ where d'(τ) drops below the YIN threshold
///      and is a local minimum is the period (the first dip, not the global min:
///      avoids the sub-harmonic the global min can prefer). Falls back to the
///      global minimum of d' over the search range if none crosses the threshold.
///   4. PARABOLIC INTERPOLATION around the chosen τ on d' → continuous τ̂ → f0=fs/τ̂.
///   5. VOICING gate — return 0.0 if the dip depth (1 − d'(τ)) is below
///      `voicing_thresh` (an unvoiced/aperiodic frame has no deep dip).
/// `f_lo`/`f_hi` bound the searched lag range τ∈[fs/f_hi, fs/f_lo].
pub fn f0_yin(frame: &[f32], fs: u32, f_lo: f32, f_hi: f32, voicing_thresh: f32) -> f32 {
    let n = frame.len();
    if n < 64 || f_lo <= 0.0 || f_hi <= f_lo {
        return 0.0;
    }
    let tau_min = ((fs as f32 / f_hi).floor() as usize).max(2);
    let tau_max = ((fs as f32 / f_lo).ceil() as usize).min(n / 2 - 1);
    if tau_max <= tau_min + 1 {
        return 0.0;
    }
    // remove DC for a clean difference function.
    let mean = frame.iter().map(|&v| v as f64).sum::<f64>() / n as f64;
    let x: Vec<f64> = frame.iter().map(|&v| v as f64 - mean).collect();
    // integration window length: the bulk of the frame, capped so i+tau_max is in
    // range (W samples summed per lag).
    let w = n - tau_max;
    if w < tau_min * 2 {
        return 0.0;
    }
    // (1) difference function d(tau) over the window [0, W).
    let mut d = vec![0.0f64; tau_max + 1];
    for (tau, dt) in d.iter_mut().enumerate().take(tau_max + 1).skip(1) {
        let mut acc = 0.0f64;
        for i in 0..w {
            let diff = x[i] - x[i + tau];
            acc += diff * diff;
        }
        *dt = acc;
    }
    // (2) cumulative-mean-normalised difference d'(tau).
    let mut dp = vec![1.0f64; tau_max + 1];
    let mut running = 0.0f64;
    for tau in 1..=tau_max {
        running += d[tau];
        dp[tau] = if running > 0.0 {
            d[tau] * tau as f64 / running
        } else {
            1.0
        };
    }
    // (3) absolute threshold: first local-minimum dip below the YIN threshold at or
    // after tau_min.
    let thresh = 0.12f64;
    let mut chosen = 0usize;
    let mut tau = tau_min;
    while tau <= tau_max {
        if dp[tau] < thresh {
            // descend to the local minimum of this dip.
            let mut t = tau;
            while t + 1 <= tau_max && dp[t + 1] < dp[t] {
                t += 1;
            }
            chosen = t;
            break;
        }
        tau += 1;
    }
    // fallback: global minimum of d' over the search range.
    if chosen == 0 {
        let mut best = f64::INFINITY;
        for t in tau_min..=tau_max {
            if dp[t] < best {
                best = dp[t];
                chosen = t;
            }
        }
        if chosen == 0 {
            return 0.0;
        }
    }
    // (5) voicing gate: dip depth must exceed the requested floor.
    let depth = 1.0 - dp[chosen];
    if depth < voicing_thresh as f64 {
        return 0.0;
    }
    // (4) parabolic interpolation around `chosen` on d' for sub-sample period.
    let tau_hat = if chosen > tau_min && chosen < tau_max {
        let y0 = dp[chosen - 1];
        let y1 = dp[chosen];
        let y2 = dp[chosen + 1];
        let denom = y0 - 2.0 * y1 + y2;
        if denom.abs() > 1e-12 {
            let delta = 0.5 * (y0 - y2) / denom; // vertex offset in [-1, 1]
            chosen as f64 + delta.clamp(-1.0, 1.0)
        } else {
            chosen as f64
        }
    } else {
        chosen as f64
    };
    if tau_hat <= 0.0 {
        return 0.0;
    }
    fs as f32 / tau_hat as f32
}

/// WITHIN-REGISTER TRACT-SHAPE WARP — imprint a speaker's OWN per-formant tract
/// signature (formant-SPACE offsets + per-formant bandwidths) onto a content LPC
/// track, so two same-register / same-VTL speakers render with their OWN
/// distinct vocal-tract geometry rather than the content donor's.
///
/// THE WALL THIS CRESTS. The 4-D SOURCE print [f0, oq, tilt, level] genuinely
/// co-locates for same-register males, so it cannot separate them. The cue that
/// SURVIVES f0 overlap is TRACT GEOMETRY: a speaker's idiosyncratic formant-SPACE
/// SHAPE (the per-formant ratios F1:F2:F3 relative to a uniform-VTL tract — which
/// the single VTL scalar throws away) and his per-formant BANDWIDTHS (filter
/// sharpness). These are cleanly tract-geometry = SPEAKER not CONTENT, and they
/// are exactly what makes p227 sound unlike p232 at the same pitch.
///
/// THE WARP (pure owned DSP, NO net / fit / gradient / loss / sweep). For each
/// LPC frame:
///   1. ROOT the frame's A(z) (Durand-Kerner `poly_roots`) → complex pole pairs.
///   2. For each upper-half pole, read its formant freq f = angle·fs/2π and
///      bandwidth bw = -fs/2π·ln|z|. Order the in-band poles ascending = the
///      content's F1,F2,F3,... trajectory at this instant.
///   3. WARP each of the first `n_formant` in-band poles toward the speaker:
///        • FREQUENCY — MULTIPLY the pole angle by `freq_ratio[k]` (the speaker's
///          per-formant offset = speaker_Fk / canonical_Fk). Multiplicative warp
///          preserves the content's formant MOTION (intelligibility) but shifts
///          its formant-space POSITIONS to the speaker's tract shape. The ratio
///          is the SHAPE on top of the uniform VTL already applied by resampling
///          (so VTL is not double-counted — `freq_ratio` is normalised to the
///          speaker's OWN geometric-mean formant offset by the caller).
///        • BANDWIDTH — blend the pole RADIUS toward the radius implied by the
///          speaker's target bandwidth `targ_bw[k]`: r_targ = exp(-π·bw_k/fs),
///          r' = (1-α)·r + α·r_targ. The speaker's filter sharpness.
///   4. Re-form the conjugate pair (mirror the warped upper pole), keep all
///      out-of-band / real poles UNCHANGED, and MULTIPLY OUT the monic polynomial
///      Π(1 - z_i z⁻¹) → the new a[0..=order] (a[0]=1). Real by construction
///      (conjugate pairs); tiny imag parts dropped.
///
/// `freq_ratio` / `targ_bw` have length `n_formant` (per-formant; missing → no
/// warp for that index). `alpha` ∈ [0,1] is the bandwidth blend strength. Poles
/// are kept strictly inside the unit circle (radius clamped ≤ 0.998) so the
/// resynthesis filter stays stable. Returns the warped flat a-track (same shape
/// as the input `a_frames`).
pub fn lpc_formant_warp_track(
    a_frames: &[f32],
    order: usize,
    fs: u32,
    freq_ratio: &[f32],
    targ_bw: &[f32],
    n_formant: usize,
    alpha: f32,
    f_lo: f32,
    f_hi: f32,
) -> Vec<f32> {
    let stride = order + 1;
    if stride == 0 || a_frames.len() < stride || n_formant == 0 {
        return a_frames.to_vec();
    }
    let n_frames = a_frames.len() / stride;
    let mut out = a_frames.to_vec();
    let twopi = 2.0 * std::f64::consts::PI;
    let half_fs = fs as f64 / twopi;
    let r_clamp = 0.998f64;
    for f in 0..n_frames {
        let base = f * stride;
        // Monic A(z) coefficients (a[0]=1 already by construction).
        let coeffs: Vec<f64> = a_frames[base..base + stride]
            .iter()
            .map(|&v| v as f64)
            .collect();
        if coeffs.is_empty() || coeffs[0].abs() < 1e-12 {
            continue;
        }
        let roots = poly_roots(&coeffs);
        if roots.is_empty() {
            continue;
        }
        // Identify upper-half in-band poles, ascending by frequency. Track which
        // root index each came from so we warp the original (and its conjugate).
        let mut inband: Vec<(f64, usize)> = Vec::new(); // (freq, root index)
        for (ri, z) in roots.iter().enumerate() {
            if z.im <= 0.0 {
                continue;
            }
            let ang = z.im.atan2(z.re);
            let fq = ang * fs as f64 / twopi;
            if fq >= f_lo as f64 && fq <= f_hi as f64 {
                inband.push((fq, ri));
            }
        }
        inband.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal));
        // Build the warped root list: start from the originals, then rewrite the
        // formant poles (and their conjugates).
        let mut new_roots = roots.clone();
        for (k, &(_fq, ri)) in inband.iter().enumerate() {
            if k >= n_formant {
                break;
            }
            let z = roots[ri];
            let mut ang = z.im.atan2(z.re); // > 0 (upper half)
            let mut rad = z.norm();
            // FREQUENCY warp: multiply the angle by the speaker's per-formant ratio.
            if k < freq_ratio.len() && freq_ratio[k] > 0.0 {
                ang *= freq_ratio[k] as f64;
                // keep below Nyquist angle.
                ang = ang.clamp(1e-4, std::f64::consts::PI - 1e-4);
            }
            // BANDWIDTH warp: blend the radius toward the speaker's target bw.
            if k < targ_bw.len() && targ_bw[k] > 0.0 && alpha > 0.0 {
                let r_targ = (-std::f64::consts::PI * targ_bw[k] as f64 / fs as f64).exp();
                rad = (1.0 - alpha as f64) * rad + alpha as f64 * r_targ;
            }
            rad = rad.clamp(1e-3, r_clamp);
            let zr = rad * ang.cos();
            let zi = rad * ang.sin();
            new_roots[ri] = Complex::new(zr, zi);
            // mirror onto the conjugate partner (nearest conjugate root).
            let mut best = usize::MAX;
            let mut bestd = f64::INFINITY;
            for (rj, &zz) in roots.iter().enumerate() {
                if rj == ri || zz.im >= 0.0 {
                    continue;
                }
                let d = (zz.re - z.re).powi(2) + (zz.im + z.im).powi(2);
                if d < bestd {
                    bestd = d;
                    best = rj;
                }
            }
            if best != usize::MAX {
                new_roots[best] = Complex::new(zr, -zi);
            }
        }
        // Multiply out the monic polynomial Π (1 - z_i z⁻¹): start [1], for each
        // root multiply by (1 - z_i z⁻¹) → poly[j] -= z_i · poly[j-1].
        let mut poly: Vec<Complex<f64>> = vec![Complex::new(1.0, 0.0)];
        for &zr in &new_roots {
            let mut next = vec![Complex::new(0.0, 0.0); poly.len() + 1];
            for (j, &pj) in poly.iter().enumerate() {
                next[j] += pj;
                next[j + 1] -= zr * pj;
            }
            poly = next;
        }
        // poly has degree = #roots; take the real parts as the new a[]. If the
        // root count differs from `order` (degenerate root solve), keep original.
        if poly.len() == stride {
            // normalise so a[0] = 1 (it already is up to tiny imag/real error).
            let a0 = poly[0].re;
            if a0.abs() > 1e-9 {
                for k in 0..stride {
                    out[base + k] = (poly[k].re / a0) as f32;
                }
            }
        }
    }
    out
}

/// ABSOLUTE-TARGET formant warp — like `lpc_formant_warp_track`, but each of the
/// first `n_formant` in-band formant poles is moved to an ABSOLUTE target
/// frequency `targ_f[k]` (Hz) rather than multiplied by a ratio. This is the
/// primitive the ANALYSIS-BY-SYNTHESIS formant-fix loop drives: the caller
/// renders, RE-ANALYSES the rendered formants, measures the drift from the
/// speaker's REAL formants, and on the next pass sets `targ_f[k]` to the value
/// that — given the measured drift — makes the rendered formant LAND on the real
/// formant (a deterministic inverse / fixed point on the forward model). The
/// target is the speaker's measured real formant print, NOT any score.
///
///   * `targ_f[k]` (Hz): absolute target for the k-th in-band formant pole. A
///     value `<= 0.0` leaves that formant's frequency UNCHANGED (the warp only
///     touches the formants it is given a positive target for).
///   * `targ_bw[k]` (Hz): target bandwidth; the pole radius is blended toward
///     `exp(-π·bw_k/fs)` by `alpha` (same as the ratio warp). `<= 0.0` or
///     `alpha <= 0` leaves the radius unchanged.
///
/// All other poles (out-of-band, real, higher formants) are kept UNCHANGED; the
/// monic polynomial is multiplied back out (a[0]=1). Pole radius clamped ≤ 0.998
/// for filter stability. Pure owned DSP — root-solve, set the angle, re-multiply.
/// No fit, no net, no gradient. Returns the warped flat a-track.
#[allow(clippy::too_many_arguments)]
pub fn lpc_formant_set_track(
    a_frames: &[f32],
    order: usize,
    fs: u32,
    targ_f: &[f32],
    targ_bw: &[f32],
    n_formant: usize,
    alpha: f32,
    f_lo: f32,
    f_hi: f32,
) -> Vec<f32> {
    let stride = order + 1;
    if stride == 0 || a_frames.len() < stride || n_formant == 0 {
        return a_frames.to_vec();
    }
    let n_frames = a_frames.len() / stride;
    let mut out = a_frames.to_vec();
    let twopi = 2.0 * std::f64::consts::PI;
    let r_clamp = 0.998f64;
    for f in 0..n_frames {
        let base = f * stride;
        let coeffs: Vec<f64> = a_frames[base..base + stride]
            .iter()
            .map(|&v| v as f64)
            .collect();
        if coeffs.is_empty() || coeffs[0].abs() < 1e-12 {
            continue;
        }
        let roots = poly_roots(&coeffs);
        if roots.is_empty() {
            continue;
        }
        let mut inband: Vec<(f64, usize)> = Vec::new();
        for (ri, z) in roots.iter().enumerate() {
            if z.im <= 0.0 {
                continue;
            }
            let ang = z.im.atan2(z.re);
            let fq = ang * fs as f64 / twopi;
            if fq >= f_lo as f64 && fq <= f_hi as f64 {
                inband.push((fq, ri));
            }
        }
        inband.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal));
        let mut new_roots = roots.clone();
        for (k, &(_fq, ri)) in inband.iter().enumerate() {
            if k >= n_formant {
                break;
            }
            let z = roots[ri];
            let mut ang = z.im.atan2(z.re); // > 0 (upper half)
            let mut rad = z.norm();
            // FREQUENCY: SET the pole angle to the absolute target (Hz -> angle).
            if k < targ_f.len() && targ_f[k] > 0.0 {
                ang = (twopi * targ_f[k] as f64) / fs as f64;
                ang = ang.clamp(1e-4, std::f64::consts::PI - 1e-4);
            }
            // BANDWIDTH: blend the radius toward the speaker's target bw.
            if k < targ_bw.len() && targ_bw[k] > 0.0 && alpha > 0.0 {
                let r_targ = (-std::f64::consts::PI * targ_bw[k] as f64 / fs as f64).exp();
                rad = (1.0 - alpha as f64) * rad + alpha as f64 * r_targ;
            }
            rad = rad.clamp(1e-3, r_clamp);
            let zr = rad * ang.cos();
            let zi = rad * ang.sin();
            new_roots[ri] = Complex::new(zr, zi);
            // mirror onto the conjugate partner (nearest conjugate root).
            let mut best = usize::MAX;
            let mut bestd = f64::INFINITY;
            for (rj, &zz) in roots.iter().enumerate() {
                if rj == ri || zz.im >= 0.0 {
                    continue;
                }
                let d = (zz.re - z.re).powi(2) + (zz.im + z.im).powi(2);
                if d < bestd {
                    bestd = d;
                    best = rj;
                }
            }
            if best != usize::MAX {
                new_roots[best] = Complex::new(zr, -zi);
            }
        }
        let mut poly: Vec<Complex<f64>> = vec![Complex::new(1.0, 0.0)];
        for &zr in &new_roots {
            let mut next = vec![Complex::new(0.0, 0.0); poly.len() + 1];
            for (j, &pj) in poly.iter().enumerate() {
                next[j] += pj;
                next[j + 1] -= zr * pj;
            }
            poly = next;
        }
        if poly.len() == stride {
            let a0 = poly[0].re;
            if a0.abs() > 1e-9 {
                for k in 0..stride {
                    out[base + k] = (poly[k].re / a0) as f32;
                }
            }
        }
    }
    out
}

// --- TRANSDUCTION: the agent's three "ears" in Rust -------------------------
// Faithful ports of domains/filter_settings.{cochleagram,fft_ear} and
// domains/allpole_spectral_envelope.allpole_ear, so sensory transduction runs in Rust and the
// world adapter only hands off samples. Constants match the Python.

const COCH_NBANDS: usize = 32;
const PI64: f64 = std::f64::consts::PI;

fn coch_bands() -> Vec<f64> {
    let (lo, hi) = (80.0_f64.ln(), 7500.0_f64.ln());
    (0..COCH_NBANDS).map(|i| (lo + (hi - lo) * (i as f64) / 31.0).exp()).collect()
}

/// Public accessor for the cochleagram band CENTRE frequencies (Hz) — the
/// same 32 log-spaced (80 Hz .. 7500 Hz) gammatone centres `cochleagram`
/// uses. Exposed so the text→transform bridge can render a formant
/// shift-vector into THIS band space (see `apc::formant_bands`).
pub fn coch_band_centers() -> Vec<f32> {
    coch_bands().iter().map(|&f| f as f32).collect()
}

/// gammatone_env: order-4 gammatone impulse (0.025 s), L2-normalised, "same" convolution,
/// half-wave rectify, one-pole envelope LPF at env_cut.
fn gammatone_env(x: &[f64], fs: u32, fc: f64, env_cut: f64) -> Vec<f64> {
    let fsf = fs as f64;
    let l = (0.025 * fsf) as usize;
    let n = l.max(1);
    let mut g = vec![0.0f64; n];
    let b = 2.0 * PI64 * 1.019 * (24.7 + 0.108 * fc);
    let mut e2 = 0.0;
    for k in 0..n {
        let t = k as f64 / fsf;
        let v = t.powi(3) * (-b * t).exp() * (2.0 * PI64 * fc * t).cos();
        g[k] = v;
        e2 += v * v;
    }
    let e = e2.sqrt();
    if e > 0.0 {
        for v in g.iter_mut() {
            *v /= e;
        }
    }
    let m = x.len();
    let full_len = m + n - 1;
    let mut full = vec![0.0f64; full_len];
    for j in 0..m {
        let xj = x[j];
        if xj != 0.0 {
            for k in 0..n {
                full[j + k] += xj * g[k];
            }
        }
    }
    let start = (n - 1) / 2; // np.convolve(..., "same") centre slice (m >= n)
    let mut y = vec![0.0f64; m];
    for i in 0..m {
        y[i] = full[start + i].max(0.0); // slice + half-wave rectify
    }
    let tau = 1.0 / (2.0 * PI64 * env_cut);
    let a = (-1.0 / (tau * fsf)).exp();
    let mut acc = 0.0;
    for i in 0..m {
        acc = a * acc + (1.0 - a) * y[i];
        y[i] = acc;
    }
    y
}

/// cochleagram: 32-band gammatone envelopes + per-band sustained-duration LPF + linear resample
/// to n_frames. Returns (n_frames x 32) row-major (frame, band) as f32.
pub fn cochleagram(x: &[f32], fs: u32, env_cut: f32, dur_cut: f32, n_frames: usize) -> Vec<f32> {
    let xf: Vec<f64> = x.iter().map(|&v| v as f64).collect();
    let fsf = fs as f64;
    let cut = 1000.0 / (2.0 * PI64 * dur_cut as f64);
    let tau = 1.0 / (2.0 * PI64 * cut);
    let a = (-1.0 / (tau * fsf)).exp();
    let mut smoothed: Vec<Vec<f64>> = Vec::with_capacity(COCH_NBANDS);
    for &fc in &coch_bands() {
        let env = gammatone_env(&xf, fs, fc, env_cut as f64);
        let mut sm = vec![0.0f64; env.len()];
        let mut acc = 0.0;
        for i in 0..env.len() {
            acc = a * acc + (1.0 - a) * env[i];
            sm[i] = acc;
        }
        smoothed.push(sm);
    }
    let n_src = smoothed[0].len().max(1);
    let mut out = vec![0.0f32; n_frames * COCH_NBANDS];
    for tf in 0..n_frames {
        let sp = (tf * n_src) as f64 / n_frames as f64;
        let i0 = (sp as usize).min(n_src - 1);
        let i1 = (i0 + 1).min(n_src - 1);
        let frac = sp - i0 as f64;
        for (bi, buf) in smoothed.iter().enumerate() {
            out[tf * COCH_NBANDS + bi] = (buf[i0] * (1.0 - frac) + buf[i1] * frac) as f32;
        }
    }
    out
}

/// cmvn: per-band cepstral mean-variance normalisation over a frames x bands matrix.
/// `m` is row-major (frame, band) flat, length n_frames*n_bands. `voiced` is a per-frame
/// 0/1 mask selecting the stat frames that mu_b/var_b average over (silence excluded).
/// Returns the normalised matrix, same shape/layout, as f32:
///   out[f,b] = (m[f,b] - mu_b) / (sqrt(var_b) + eps)        when do_variance
///   out[f,b] =  m[f,b] - mu_b                               otherwise
/// eps is OUTSIDE the sqrt (Kaldi/CMVN convention). Faithful batched port of the agent's
/// composed cmvn_band_term (domains/cmvn.py) — same Sum/Count/Div aggregation over the
/// stat-frame set, same affine — run in Rust at the I/O boundary like `cochleagram`.
/// f64 accumulation, f32 result (matches the per-cell Term-eval path it replaces).
pub fn cmvn(m: &[f32], n_frames: usize, n_bands: usize, eps: f32, do_variance: bool,
            voiced: &[u8]) -> Vec<f32> {
    let mut out = vec![0.0f32; n_frames * n_bands];
    if n_frames == 0 || n_bands == 0 {
        return out;
    }
    let n_stat = voiced.iter().take(n_frames).filter(|&&v| v != 0).count().max(1) as f64;
    let epsf = eps as f64;
    for b in 0..n_bands {
        let mut sm = 0.0f64;
        for f in 0..n_frames {
            if voiced[f] != 0 {
                sm += m[f * n_bands + b] as f64;
            }
        }
        let mu = sm / n_stat;
        if do_variance {
            let mut sv = 0.0f64;
            for f in 0..n_frames {
                if voiced[f] != 0 {
                    let d = m[f * n_bands + b] as f64 - mu;
                    sv += d * d;
                }
            }
            let denom = (sv / n_stat).sqrt() + epsf;
            for f in 0..n_frames {
                out[f * n_bands + b] = ((m[f * n_bands + b] as f64 - mu) / denom) as f32;
            }
        } else {
            for f in 0..n_frames {
                out[f * n_bands + b] = (m[f * n_bands + b] as f64 - mu) as f32;
            }
        }
    }
    out
}

/// topk_dot: the recogniser's DECISION compiled to Rust — score an embedding against
/// every word-centroid by dot product (the held Dot Term), return the top-k centroid
/// indices and their scores (the argmax loop, generalised to top-k). `cents` is the
/// centroid matrix row-major n_cent x dim. Same numbers as evaluating Dot(emb, cent)
/// per WordCentroid node and sorting; this batches it so a large open vocabulary is
/// one matmul + partial sort instead of n_cent native Term evaluations per chunk.
pub fn topk_dot(emb: &[f32], cents: &[f32], n_cent: usize, dim: usize, k: usize)
    -> (Vec<i64>, Vec<f32>) {
    let mut scores = vec![0.0f32; n_cent];
    for c in 0..n_cent {
        let base = c * dim;
        let mut s = 0.0f64;
        for d in 0..dim {
            s += emb[d] as f64 * cents[base + d] as f64;
        }
        scores[c] = s as f32;
    }
    let kk = k.min(n_cent);
    let mut idx: Vec<usize> = (0..n_cent).collect();
    // descending by score; partial select then sort the prefix for stable top-k order.
    if kk < n_cent {
        idx.select_nth_unstable_by(kk, |&a, &b| {
            scores[b].partial_cmp(&scores[a]).unwrap_or(std::cmp::Ordering::Equal)
        });
        idx.truncate(kk);
    }
    idx.sort_by(|&a, &b| scores[b].partial_cmp(&scores[a]).unwrap_or(std::cmp::Ordering::Equal));
    let out_idx: Vec<i64> = idx.iter().map(|&i| i as i64).collect();
    let out_sc: Vec<f32> = idx.iter().map(|&i| scores[i]).collect();
    (out_idx, out_sc)
}

/// topk_match: the compiled form of the agent's DURATION-AWARE match Term. The agent
/// composes the duration model from its OWN normalisation science (the same move as
/// CMVN/speaker_norm: a characteristic is a constant to subtract, the spread a scale to
/// divide by) applied to the duration dimension:
///   score(c) = Dot(emb, cent_c)  -  0.5 * ((qdur - dmu_c) / dsig_c)^2
/// i.e. shape similarity MINUS the squared duration z-score (a Gaussian duration
/// log-likelihood, the -0.5 z^2 constant — not a tuned knob). dmu_c/dsig_c are the unit's
/// duration mean/std IN FRAMES, derived from its instances (data, not a hand-picked band).
/// A long span (large qdur) pays a large penalty against a short unit and vice versa, so
/// the scale-blind fixed-length shape feature becomes scale-aware. dsig_c<=0 -> no
/// duration term (unknown duration). Returns (top-k indices, scores).
pub fn topk_match(emb: &[f32], cents: &[f32], dmu: &[f32], dsig: &[f32], n_cent: usize,
                  dim: usize, k: usize, qdur: f32) -> (Vec<i64>, Vec<f32>) {
    let mut scores = vec![0.0f32; n_cent];
    for c in 0..n_cent {
        let base = c * dim;
        let mut s = 0.0f64;
        for d in 0..dim {
            s += emb[d] as f64 * cents[base + d] as f64;
        }
        let sig = dsig[c] as f64;
        if sig > 0.0 {
            let z = (qdur as f64 - dmu[c] as f64) / sig;
            s -= 0.5 * z * z;
        }
        scores[c] = s as f32;
    }
    let kk = k.min(n_cent);
    let mut idx: Vec<usize> = (0..n_cent).collect();
    if kk < n_cent {
        idx.select_nth_unstable_by(kk, |&a, &b| {
            scores[b].partial_cmp(&scores[a]).unwrap_or(std::cmp::Ordering::Equal)
        });
        idx.truncate(kk);
    }
    idx.sort_by(|&a, &b| scores[b].partial_cmp(&scores[a]).unwrap_or(std::cmp::Ordering::Equal));
    (idx.iter().map(|&i| i as i64).collect(), idx.iter().map(|&i| scores[i]).collect())
}

/// segment_units: the agent's TP-trough word segmenter, compiled to Rust. Faithful
/// port of domains/forward_segmentation (statistical_learning -> transitional-
/// probability troughs -> chunks). Estimates the TP structure over ALL sequences
/// (corpus statistical learning), then for each sequence reads boundaries off its
/// own TP curve with the chosen boundary rule, and merges the high-TP runs between
/// troughs into chunks. Returns, per input sequence, the chunk LENGTHS in units
/// (== frames when the units are per-frame). No RLE: the prominent rule already
/// pulls the cut rate to word scale on a fine grid.
///
/// `bidirectional`: tp = min(P(nxt|cur), P(cur|nxt)) (the symmetric bond) vs forward
/// P(nxt|cur). `mode`: 0 = median (cut below the running-median level), 1 = local_min
/// (cut at every TP local minimum), 2 = prominent (local minimum AND below median —
/// the AND of the agent's two boundary Terms, the grid-robust word-scale rule).
/// Matches forward_segmentation's _install_transitions sentinels (sequence ends never
/// read as a local minimum) and _median (mean of the two central values when even).
pub fn segment_units(seqs: &[Vec<i64>], bidirectional: bool, mode: u8) -> Vec<Vec<usize>> {
    use std::collections::HashMap;
    const SENTINEL: f64 = 1e9;
    // (1) corpus structure: pair / cur / nxt counts over every sequence.
    let mut pair: HashMap<(i64, i64), u64> = HashMap::new();
    let mut cur_total: HashMap<i64, u64> = HashMap::new();
    let mut nxt_total: HashMap<i64, u64> = HashMap::new();
    for seq in seqs {
        for w in seq.windows(2) {
            *pair.entry((w[0], w[1])).or_insert(0) += 1;
            *cur_total.entry(w[0]).or_insert(0) += 1;
            *nxt_total.entry(w[1]).or_insert(0) += 1;
        }
    }
    let mut tp: HashMap<(i64, i64), f64> = HashMap::with_capacity(pair.len());
    for (&(a, b), &c) in &pair {
        let v = if bidirectional {
            let fwd = c as f64 / cur_total[&a] as f64;
            let bwd = c as f64 / nxt_total[&b] as f64;
            fwd.min(bwd)
        } else {
            c as f64 / cur_total[&a] as f64
        };
        tp.insert((a, b), v);
    }
    // (2) level = median of the observed TP distribution (a statistic OF the data).
    let mut vals: Vec<f64> = tp.values().copied().collect();
    vals.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let level = if vals.is_empty() {
        0.0
    } else {
        let n = vals.len();
        let m = n / 2;
        if n % 2 == 1 { vals[m] } else { 0.5 * (vals[m - 1] + vals[m]) }
    };
    // (3) per sequence: read troughs off its own TP curve, merge runs into chunks.
    let mut out = Vec::with_capacity(seqs.len());
    for seq in seqs {
        if seq.len() < 2 {
            out.push(if seq.is_empty() { vec![] } else { vec![seq.len()] });
            continue;
        }
        let np = seq.len() - 1;
        let tps: Vec<f64> = (0..np).map(|i| *tp.get(&(seq[i], seq[i + 1])).unwrap_or(&0.0)).collect();
        // boundary AFTER position i (between unit i and i+1)
        let mut cut = vec![false; np];
        for i in 0..np {
            let here = tps[i];
            let is_cut = match mode {
                1 => {
                    let prev = if i > 0 { tps[i - 1] } else { SENTINEL };
                    let next = if i + 1 < np { tps[i + 1] } else { SENTINEL };
                    here < prev && here < next
                }
                2 => {
                    let prev = if i > 0 { tps[i - 1] } else { SENTINEL };
                    let next = if i + 1 < np { tps[i + 1] } else { SENTINEL };
                    here < prev && here < next && here < level
                }
                _ => here < level,
            };
            cut[i] = is_cut;
        }
        // merge: a cut at i closes a chunk after unit i.
        let mut lens = Vec::new();
        let mut cur_len = 0usize;
        for i in 0..seq.len() {
            cur_len += 1;
            if i < np && cut[i] {
                lens.push(cur_len);
                cur_len = 0;
            }
        }
        if cur_len > 0 {
            lens.push(cur_len);
        }
        out.push(lens);
    }
    out
}

fn log_edges(lo_hz: f64, hi_hz: f64, nbands: usize) -> Vec<f64> {
    let (lo, hi) = (lo_hz.ln(), hi_hz.ln());
    (0..=nbands).map(|b| (lo + (hi - lo) * b as f64 / nbands as f64).exp()).collect()
}

/// fft_ear: nwin temporal windows, each Hanning-windowed, rfft(nfft), magnitude log-pooled into
/// nbands log-spaced bands 150..3800 Hz. Flat (nwin*nbands,) f64.
pub fn fft_ear(x: &[f64], fs: u32, nbands: usize, nwin: usize, nfft: usize) -> Vec<f64> {
    use rustfft::FftPlanner;
    let fsf = fs as f64;
    let edges = log_edges(150.0, 3800.0, nbands);
    let nf = nfft / 2 + 1;
    let fr: Vec<f64> = (0..nf).map(|i| i as f64 * fsf / nfft as f64).collect();
    let bin_idx: Vec<Vec<usize>> = (0..nbands)
        .map(|b| (0..nf).filter(|&i| fr[i] >= edges[b] && fr[i] < edges[b + 1]).collect())
        .collect();
    let n = x.len();
    let mut out = vec![0.0f64; nwin * nbands];
    if n < 32 {
        return out;
    }
    let bounds: Vec<usize> = (0..=nwin).map(|i| (i as f64 * n as f64 / nwin as f64) as usize).collect();
    let mut planner = FftPlanner::<f64>::new();
    let fft = planner.plan_fft_forward(nfft);
    for wi in 0..nwin {
        let lo_b = bounds[wi];
        let hi_b = (bounds[wi] + 1).max(bounds[wi + 1]).min(n);
        let seg = &x[lo_b..hi_b];
        let sl = seg.len();
        if sl < 16 {
            continue;
        }
        // Analyse at most nfft samples: when a window is longer than the FFT size, truncate to
        // the first nfft samples (standard STFT behaviour) rather than overflowing the buffer.
        let m = sl.min(nfft);
        let mut buf = vec![Complex::new(0.0f64, 0.0f64); nfft];
        for k in 0..m {
            let w = if m > 1 { 0.5 - 0.5 * (2.0 * PI64 * k as f64 / (m as f64 - 1.0)).cos() } else { 1.0 };
            buf[k] = Complex::new(seg[k] * w, 0.0);
        }
        fft.process(&mut buf);
        for b in 0..nbands {
            let idx = &bin_idx[b];
            if idx.is_empty() {
                out[wi * nbands + b] = -18.0;
            } else {
                let mut s = 0.0;
                for &i in idx {
                    s += buf[i].norm();
                }
                out[wi * nbands + b] = (s / idx.len() as f64 + 1e-8).ln();
            }
        }
    }
    out
}

fn ap_autocorr(x: &[f64], p: usize) -> Vec<f64> {
    let n = x.len();
    (0..=p).map(|k| {
        let mut s = 0.0;
        for i in 0..(n - k) {
            s += x[i] * x[i + k];
        }
        s
    }).collect()
}

fn ap_levinson(r: &[f64], p: usize) -> (Vec<f64>, f64) {
    let mut a = vec![0.0f64; p + 1];
    a[0] = 1.0;
    let mut e = r[0];
    if e <= 0.0 {
        return (a, 0.0);
    }
    for i in 1..=p {
        let mut acc = r[i];
        for j in 1..i {
            acc += a[j] * r[i - j];
        }
        let k = -acc / e;
        let mut a_new = a.clone();
        for j in 1..i {
            a_new[j] = a[j] + k * a[i - j];
        }
        a_new[i] = k;
        a = a_new;
        e *= 1.0 - k * k;
        if e <= 0.0 {
            break;
        }
    }
    (a, e.max(1e-9))
}

fn allpole_window(seg: &[f64], fs: u32, edges: &[f64], order: usize) -> Vec<f64> {
    let nbands = edges.len() - 1;
    let fsf = fs as f64;
    if seg.len() < order + 4 || seg.iter().all(|&v| v.abs() < 1e-12) {
        return vec![-18.0; nbands];
    }
    let mut x = vec![0.0f64; seg.len()];
    x[0] = seg[0];
    for i in 1..seg.len() {
        x[i] = seg[i] - 0.97 * seg[i - 1]; // pre-emphasis
    }
    let m = x.len();
    for k in 0..m {
        let w = if m > 1 { 0.54 - 0.46 * (2.0 * PI64 * k as f64 / (m as f64 - 1.0)).cos() } else { 1.0 };
        x[k] *= w; // Hamming
    }
    let r = ap_autocorr(&x, order);
    if r[0] <= 0.0 {
        return vec![-18.0; nbands];
    }
    let (a, gain) = ap_levinson(&r, order);
    let mut out = vec![0.0f64; nbands];
    for b in 0..nbands {
        let centre = (edges[b] * edges[b + 1]).sqrt();
        let w = 2.0 * PI64 * centre / fsf;
        let (mut re, mut im) = (0.0, 0.0);
        for k in 0..a.len() {
            let ph = -w * k as f64;
            re += a[k] * ph.cos();
            im += a[k] * ph.sin();
        }
        let amag = (re * re + im * im).sqrt() + 1e-9;
        let env = gain.max(1e-12).sqrt() / amag;
        out[b] = env.max(1e-8).ln();
    }
    out
}

/// allpole_ear: nwin windows, pre-emphasis + Hamming + autocorr + Levinson all-pole fit, envelope
/// |H(w)|=sqrt(gain)/|A(e^jw)| read on nbands log centres 150..3800. Flat (nwin*nbands,) f64.
pub fn allpole_ear(x: &[f64], fs: u32, nbands: usize, nwin: usize, order: usize) -> Vec<f64> {
    let edges = log_edges(150.0, 3800.0, nbands);
    let n = x.len();
    let mut out = vec![-18.0f64; nwin * nbands];
    if n < 32 {
        return out;
    }
    let bounds: Vec<usize> = (0..=nwin).map(|i| (i as f64 * n as f64 / nwin as f64) as usize).collect();
    for wi in 0..nwin {
        let lo_b = bounds[wi];
        let hi_b = (bounds[wi] + 1).max(bounds[wi + 1]).min(n);
        let seg = &x[lo_b..hi_b];
        if seg.len() < order + 4 {
            continue;
        }
        let row = allpole_window(seg, fs, &edges, order);
        for b in 0..nbands {
            out[wi * nbands + b] = row[b];
        }
    }
    out
}

/// sonority_segment: the jabberwock's word-boundary detector as transduction. Sums gammatone
/// envelopes over a few log-spaced bands into a broadband SONORITY envelope, zero-phase smooths
/// it, and cuts at deep local minima — a sonority valley whose relative prominence (flanked by
/// energy on BOTH sides) >= depth_threshold, greedily accepted deepest-first with >= min_sep_ms
/// spacing. Returns the inter-word cut sample indices. depth_threshold is the graph-resident,
/// self-tuned DECISION (the sonority_valley faculty); this is the mechanical DSP it parameterises.
pub fn sonority_segment(x: &[f64], fs: u32, smoothing_ms: f64, min_sep_ms: f64,
                        depth_threshold: f64, silence_floor: f64, snap_center: f64) -> Vec<usize> {
    let m = x.len();
    if m < 64 {
        return vec![];
    }
    let fsf = fs as f64;
    // Broadband sonority envelope: sum gammatone envelopes over 6 log-spaced bands 150..3500 Hz.
    let edges = log_edges(150.0, 3500.0, 6);
    let mut env = vec![0.0f64; m];
    for bi in 0..6 {
        let fc = (edges[bi] * edges[bi + 1]).sqrt(); // geometric band centre
        let e = gammatone_env(x, fs, fc, 50.0);
        for i in 0..m {
            env[i] += e[i];
        }
    }
    // Zero-phase one-pole smoothing (forward+backward) at the smoothing cutoff.
    let cut = 1000.0 / (2.0 * PI64 * smoothing_ms.max(1.0));
    let tau = 1.0 / (2.0 * PI64 * cut.max(1e-3));
    let a = (-1.0 / (tau * fsf)).exp();
    let mut acc = 0.0;
    for i in 0..m {
        acc = a * acc + (1.0 - a) * env[i];
        env[i] = acc;
    }
    acc = 0.0;
    for i in (0..m).rev() {
        acc = a * acc + (1.0 - a) * env[i];
        env[i] = acc;
    }
    let mx = env.iter().cloned().fold(0.0f64, f64::max);
    if mx <= 0.0 {
        return vec![];
    }
    for v in env.iter_mut() {
        *v /= mx;
    }
    // Local minima -> prominence test. Peaks searched within +/- a syllable (300 ms); a valley
    // counts only if flanked by energy on BOTH sides (min of the two peaks), so utterance edges
    // and shallow dips don't cut.
    let min_sep = ((min_sep_ms / 1000.0) * fsf) as usize;
    let win = (0.30 * fsf) as usize;
    let mut scored: Vec<(usize, f64)> = vec![];
    let mut i = 1;
    while i < m - 1 {
        if env[i] <= env[i - 1] && env[i] <= env[i + 1] {
            let lo = i.saturating_sub(win);
            let hi = (i + win).min(m - 1);
            let lpk = env[lo..=i].iter().cloned().fold(0.0f64, f64::max);
            let rpk = env[i..=hi].iter().cloned().fold(0.0f64, f64::max);
            let pk = lpk.min(rpk);
            if pk > 1e-9 {
                let prom = (pk - env[i]) / pk;
                // SILENCE-GATE cue (silence_floor > 0): a real word gap drops to near-ABSOLUTE
                // silence, a voiced/fricative dip stays well above it. env is peak-normalised to
                // [0,1]; accept the cut only if the valley is below silence_floor. floor <= 0
                // disables the cue (relative-prominence only — the pre-authoring behaviour).
                let silent_enough = silence_floor <= 0.0 || env[i] <= silence_floor;
                if prom >= depth_threshold && silent_enough {
                    scored.push((i, prom));
                }
            }
        }
        i += 1;
    }
    // Greedy deepest-first acceptance enforcing min separation.
    scored.sort_by(|p, q| q.1.partial_cmp(&p.1).unwrap_or(std::cmp::Ordering::Equal));
    let mut accepted: Vec<usize> = vec![];
    for (c, _p) in scored {
        if accepted
            .iter()
            .all(|&b| (b as i64 - c as i64).unsigned_abs() as usize >= min_sep)
        {
            accepted.push(c);
        }
    }
    accepted.sort_unstable();
    // PLACEMENT cue (snap_center > 0): the sonority MINIMUM is offset from the true word gap —
    // the SMOOTHED sonority envelope lags and decays asymmetrically per word, so its minimum sits
    // off-centre. The true inter-word silence is symmetric in RAW energy, so snap each cut to the
    // centre of the contiguous low-RAW-ENERGY run around it (a lag-free short-window RMS, not the
    // smoothed envelope). 0 disables it (cut at the raw sonority minimum).
    if snap_center > 0.0 {
        let half = ((0.006 * fsf) as usize).max(1);
        let mut ps = vec![0.0f64; m + 1];
        for i in 0..m {
            ps[i + 1] = ps[i] + x[i] * x[i];
        }
        let mut rms = vec![0.0f64; m];
        for i in 0..m {
            let lo = i.saturating_sub(half);
            let hi = (i + half + 1).min(m);
            rms[i] = ((ps[hi] - ps[lo]) / (hi - lo) as f64).sqrt();
        }
        let rmx = rms.iter().cloned().fold(0.0f64, f64::max);
        if rmx > 0.0 {
            for v in rms.iter_mut() {
                *v /= rmx;
            }
            for c in accepted.iter_mut() {
                let mut lo = *c;
                while lo > 0 && rms[lo - 1] < snap_center {
                    lo -= 1;
                }
                let mut hi = *c;
                while hi + 1 < m && rms[hi + 1] < snap_center {
                    hi += 1;
                }
                *c = (lo + hi) / 2;
            }
            accepted.sort_unstable();
        }
    }
    accepted
}
