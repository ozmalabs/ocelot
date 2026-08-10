//! `apc` — Autoregressive Predictive Coding: a Rust-native, label-free,
//! context-predictive speech front-end (a from-scratch stand-in for the
//! wav2vec2 self-supervised objective).
//!
//! ## Why
//!
//! The V1–V4 word-shape-fidelity falsification (commit d62abb81) showed
//! multi-speaker word-shape fidelity is bound by TWO co-equal levers:
//!   1. a LEARNED FRONT-END   (a learned filterbank beats the fixed
//!      32-band cochleagram), and
//!   2. full-utterance CONTEXT (the representation at a frame should
//!      depend on the whole utterance, not just the word span).
//!
//! APC captures BOTH by ONE self-supervised objective — predict the
//! acoustic frame `K` steps ahead from a recurrent context state:
//!
//! ```text
//!   h_t  = tanh( x_t W_f + h_{t-1} U + b )         (context state)
//!   xhat = h_t W_p + c   ≈   x_{t+K}               (APC prediction)
//!   L    = mean_t || xhat_t - x_{t+K} ||^2         (label-free)
//! ```
//!
//! * `W_f` (input projection) is the LEARNED FRONT-END lever — it is
//!   trained, not fixed DSP.
//! * `U` (recurrence) carries CONTEXT: `h_t` summarises frames `0..t`,
//!   so a word's state depends on the surrounding utterance.
//! * predicting the FUTURE (not reconstructing the present) forces the
//!   state to encode phonetic dynamics rather than the static spectrum,
//!   which is what makes the representation speaker-robust.
//!
//! The learned REPRESENTATION for a word = the context-state trajectory
//! `h_t` over the word's frames (optionally bidirectional: concat the
//! backward pass `g_t` that predicts `x_{t-K}`). It feeds the held
//! `DtwTo` Term exactly like any other trajectory.
//!
//! ## Shape of things
//!
//! Training is a batch numeric loop (SGD + truncated/full-sequence BPTT
//! + global-norm gradient clipping); it lives here as a Rust primitive
//! (`apc::train`) invoked one-line from the world adapter. The learned
//! ENCODE is the `TermNode::ApcEncode` graph primitive (`apc::encode`),
//! evaluated by the substrate — so the representation is graph-native.
//!
//! Everything is `f32`, single-threaded, no external matrix dep — small
//! dims (`din ~ 64`, `dh ~ 96`) make a naive matmul more than adequate.

/// Banded DTW (Sakoe-Chiba band 8, length-normalised) between two
/// time-normalised trajectories `a`,`b` (each `t` frames of `dim`),
/// IDENTICAL to `TermNode::DtwTo`'s kernel — used by the batched
/// measurement `nn_recall_and_dprime` so the metric matches the held
/// DtwTo Term but avoids per-pair Python marshalling.
fn dtw_flat(a: &[f32], b: &[f32], t: usize, dim: usize, band: usize) -> f64 {
    let fd = |i: usize, j: usize| -> f64 {
        let (fa, fb) = (&a[i * dim..i * dim + dim], &b[j * dim..j * dim + dim]);
        let mut s = 0.0f64;
        for k in 0..dim { let d = (fa[k] - fb[k]) as f64; s += d * d; }
        s.sqrt()
    };
    const INF: f64 = 1e18;
    let (na, nb) = (t, t);
    let mut prev = vec![INF; nb + 1];
    prev[0] = 0.0;
    for i in 1..=na {
        let mut cur = vec![INF; nb + 1];
        let center = i * nb / na.max(1);
        let jl = center.saturating_sub(band).max(1);
        let jh = (center + band).min(nb);
        for j in jl..=jh {
            let d = fd(i - 1, j - 1);
            let best = prev[j].min(cur[j - 1]).min(prev[j - 1]);
            cur[j] = d + best;
        }
        prev = cur;
    }
    prev[nb] / na.max(1) as f64
}

/// Batched cross-speaker NN-recall (invariance) + d' + ROC-AUC over a set
/// of `n` trajectories, each `t` frames × `dim` (flat row-major). Reuses
/// `dtw_flat` (== the held DtwTo kernel). Recall: for each query word
/// spoken by ≥2 speakers, its nearest CROSS-speaker neighbour over the FULL
/// candidate pool (guaranteed-support / V3-hardened) — fraction whose word
/// matches. ROC-AUC = P(diff-word dist > same-word dist) over the sampled
/// pos/neg pairs. Returns [recall, dprime, auc, pos_mean, neg_mean].
#[allow(clippy::too_many_arguments)]
pub fn nn_recall_and_dprime(
    trajs: &[f32], n: usize, t: usize, dim: usize,
    words: &[i64], spk: &[i64], cap_q: usize, n_pos: usize, n_neg: usize, seed: u64,
) -> Vec<f32> {
    let stride = t * dim;
    let tr = |i: usize| &trajs[i * stride..i * stride + stride];
    // words with >=2 distinct speakers
    use std::collections::HashMap;
    let mut wsp: HashMap<i64, std::collections::HashSet<i64>> = HashMap::new();
    let mut byword: HashMap<i64, Vec<usize>> = HashMap::new();
    for i in 0..n {
        wsp.entry(words[i]).or_default().insert(spk[i]);
        byword.entry(words[i]).or_default().push(i);
    }
    let mut q: Vec<usize> = (0..n).filter(|&i| wsp[&words[i]].len() >= 2).collect();
    let mut rng = seed.wrapping_mul(0x9E3779B97F4A7C15).wrapping_add(1);
    let mut rnd = |m: usize| -> usize {
        rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17;
        (rng >> 33) as usize % m.max(1)
    };
    // cap queries
    if q.len() > cap_q {
        for i in (1..q.len()).rev() { let j = rnd(i + 1); q.swap(i, j); }
        q.truncate(cap_q);
    }
    let (mut hit, mut tot) = (0usize, 0usize);
    for &a in &q {
        let mut dmin = f64::INFINITY; let mut arg = usize::MAX;
        for b in 0..n {
            if spk[b] == spk[a] || b == a { continue; }
            let d = dtw_flat(tr(a), tr(b), t, dim, 8);
            if d < dmin { dmin = d; arg = b; }
        }
        if arg != usize::MAX { tot += 1; if words[arg] == words[a] { hit += 1; } }
    }
    let recall = if tot > 0 { hit as f64 / tot as f64 } else { f64::NAN };

    // d': same-word cross-speaker (pos) vs diff-word cross-speaker (neg)
    let mut pos: Vec<f64> = Vec::new();
    let wlist: Vec<i64> = byword.keys().copied().collect();
    let mut guard = 0;
    while pos.len() < n_pos && guard < n_pos * 40 {
        guard += 1;
        let w = wlist[rnd(wlist.len())];
        let idx = &byword[&w];
        if idx.len() < 2 { continue; }
        let i = idx[rnd(idx.len())]; let j = idx[rnd(idx.len())];
        if i != j && spk[i] != spk[j] { pos.push(dtw_flat(tr(i), tr(j), t, dim, 8)); }
    }
    let mut neg: Vec<f64> = Vec::new();
    guard = 0;
    while neg.len() < n_neg && guard < n_neg * 40 {
        guard += 1;
        let i = rnd(n); let j = rnd(n);
        if words[i] != words[j] && spk[i] != spk[j] { neg.push(dtw_flat(tr(i), tr(j), t, dim, 8)); }
    }
    let mean = |v: &[f64]| if v.is_empty() { 0.0 } else { v.iter().sum::<f64>() / v.len() as f64 };
    let var = |v: &[f64], m: f64| if v.len() < 2 { 0.0 } else { v.iter().map(|x| (x - m).powi(2)).sum::<f64>() / v.len() as f64 };
    let (pm, nm) = (mean(&pos), mean(&neg));
    let denom = (0.5 * (var(&pos, pm) + var(&neg, nm))).sqrt() + 1e-9;
    let dprime = (nm - pm) / denom;
    // ROC-AUC = P(neg_dist > pos_dist) (+ ties/2), over the sampled pairs.
    let mut auc = 0.0f64;
    if !pos.is_empty() && !neg.is_empty() {
        let mut wins = 0.0f64;
        for &p in &pos { for &q in &neg {
            if q > p { wins += 1.0; } else if (q - p).abs() < 1e-12 { wins += 0.5; }
        }}
        auc = wins / (pos.len() as f64 * neg.len() as f64);
    }
    vec![recall as f32, dprime as f32, auc as f32, pm as f32, nm as f32]
}

/// DETAIL variant of `nn_recall_and_dprime` for BOOTSTRAP confidence
/// intervals: returns the RAW per-query hit indicators (1.0 = the NN
/// cross-speaker neighbour is the same word) AND the raw sampled
/// same-word-cross-speaker (pos) and diff-word-cross-speaker (neg) distances,
/// so the caller can resample them with replacement to get CIs on
/// recall / d' / AUC. The distance kernel + query/pair selection are
/// IDENTICAL to `nn_recall_and_dprime` (same seed → same samples). Returns a
/// single flat vector `[n_hit, hits..., n_pos, pos..., n_neg, neg...]`.
#[allow(clippy::too_many_arguments)]
pub fn nn_recall_detail(
    trajs: &[f32], n: usize, t: usize, dim: usize,
    words: &[i64], spk: &[i64], cap_q: usize, n_pos: usize, n_neg: usize, seed: u64,
) -> Vec<f32> {
    let stride = t * dim;
    let tr = |i: usize| &trajs[i * stride..i * stride + stride];
    use std::collections::HashMap;
    let mut wsp: HashMap<i64, std::collections::HashSet<i64>> = HashMap::new();
    let mut byword: HashMap<i64, Vec<usize>> = HashMap::new();
    for i in 0..n {
        wsp.entry(words[i]).or_default().insert(spk[i]);
        byword.entry(words[i]).or_default().push(i);
    }
    let mut q: Vec<usize> = (0..n).filter(|&i| wsp[&words[i]].len() >= 2).collect();
    let mut rng = seed.wrapping_mul(0x9E3779B97F4A7C15).wrapping_add(1);
    let mut rnd = |m: usize| -> usize {
        rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17;
        (rng >> 33) as usize % m.max(1)
    };
    if q.len() > cap_q {
        for i in (1..q.len()).rev() { let j = rnd(i + 1); q.swap(i, j); }
        q.truncate(cap_q);
    }
    let mut hits: Vec<f32> = Vec::new();
    for &a in &q {
        let mut dmin = f64::INFINITY; let mut arg = usize::MAX;
        for b in 0..n {
            if spk[b] == spk[a] || b == a { continue; }
            let d = dtw_flat(tr(a), tr(b), t, dim, 8);
            if d < dmin { dmin = d; arg = b; }
        }
        if arg != usize::MAX { hits.push(if words[arg] == words[a] { 1.0 } else { 0.0 }); }
    }
    let mut pos: Vec<f64> = Vec::new();
    let wlist: Vec<i64> = byword.keys().copied().collect();
    let mut guard = 0;
    while pos.len() < n_pos && guard < n_pos * 40 {
        guard += 1;
        let w = wlist[rnd(wlist.len())];
        let idx = &byword[&w];
        if idx.len() < 2 { continue; }
        let i = idx[rnd(idx.len())]; let j = idx[rnd(idx.len())];
        if i != j && spk[i] != spk[j] { pos.push(dtw_flat(tr(i), tr(j), t, dim, 8)); }
    }
    let mut neg: Vec<f64> = Vec::new();
    guard = 0;
    while neg.len() < n_neg && guard < n_neg * 40 {
        guard += 1;
        let i = rnd(n); let j = rnd(n);
        if words[i] != words[j] && spk[i] != spk[j] { neg.push(dtw_flat(tr(i), tr(j), t, dim, 8)); }
    }
    let mut out: Vec<f32> = Vec::with_capacity(3 + hits.len() + pos.len() + neg.len());
    out.push(hits.len() as f32);
    out.extend_from_slice(&hits);
    out.push(pos.len() as f32);
    out.extend(pos.iter().map(|&x| x as f32));
    out.push(neg.len() as f32);
    out.extend(neg.iter().map(|&x| x as f32));
    out
}

/// Batched multi-speaker order-1 PURITY at ~`target` clusters via greedy
/// leader clustering over the DtwTo kernel (matched-granularity: a
/// threshold scan picks the leader radius whose cluster count is closest to
/// `target`). Purity = mean over clusters (≥3 members) of the majority-word
/// fraction. Returns [purity, n_clusters]. Reuses `dtw_flat` (== DtwTo).
#[allow(clippy::too_many_arguments)]
pub fn cluster_purity(
    trajs: &[f32], n: usize, t: usize, dim: usize, words: &[i64], target: usize, seed: u64,
) -> Vec<f32> {
    let stride = t * dim;
    let tr = |i: usize| &trajs[i * stride..i * stride + stride];
    let mut rng = seed.wrapping_mul(0x9E3779B97F4A7C15).wrapping_add(1);
    let mut rnd = |m: usize| -> usize { rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17; (rng >> 33) as usize % m.max(1) };
    // sample a distance scale from random cross pairs
    let mut ds: Vec<f64> = Vec::new();
    for _ in 0..400.min(n * n) { let i = rnd(n); let j = rnd(n); if i != j { ds.push(dtw_flat(tr(i), tr(j), t, dim, 8)); } }
    if ds.is_empty() { return vec![0.0, 0.0]; }
    ds.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let dmin = ds[ds.len() / 20]; let dmax = ds[ds.len() * 19 / 20];
    // greedy leader clustering at radius tau -> (assignments, nclusters)
    let leader = |tau: f64| -> (Vec<usize>, usize) {
        let mut leaders: Vec<usize> = Vec::new();
        let mut asg = vec![usize::MAX; n];
        for i in 0..n {
            let mut best = f64::INFINITY; let mut bl = usize::MAX;
            for (li, &l) in leaders.iter().enumerate() {
                let d = dtw_flat(tr(i), tr(l), t, dim, 8);
                if d < best { best = d; bl = li; }
            }
            if bl != usize::MAX && best <= tau { asg[i] = bl; }
            else { asg[i] = leaders.len(); leaders.push(i); }
        }
        (asg, leaders.len())
    };
    // scan tau; pick nclusters closest to target
    let steps = 12;
    let (mut best_asg, mut best_nc, mut best_gap) = (vec![], usize::MAX, usize::MAX);
    for s in 0..=steps {
        let tau = dmin + (dmax - dmin) * (s as f64) / steps as f64;
        let (asg, nc) = leader(tau);
        let gap = nc.abs_diff(target);
        if gap < best_gap { best_gap = gap; best_nc = nc; best_asg = asg; }
        if nc <= target { break; }
    }
    // purity over clusters with >=3 members
    use std::collections::HashMap;
    let mut byc: HashMap<usize, Vec<i64>> = HashMap::new();
    for i in 0..n { byc.entry(best_asg[i]).or_default().push(words[i]); }
    let mut ps: Vec<f64> = Vec::new();
    for (_, v) in byc.iter() {
        if v.len() < 3 { continue; }
        let mut cnt: HashMap<i64, usize> = HashMap::new();
        for &w in v { *cnt.entry(w).or_default() += 1; }
        let maj = *cnt.values().max().unwrap();
        ps.push(maj as f64 / v.len() as f64);
    }
    let purity = if ps.is_empty() { 0.0 } else { ps.iter().sum::<f64>() / ps.len() as f64 };
    vec![purity as f32, best_nc as f32]
}

/// DISCOVER the nuisance (speaker/accent) SUBSPACE from same-TEXT
/// cross-speaker residuals (the coordinator's text-recovery method).
///
/// Holding recovered TEXT constant, the residual acoustic variation across
/// speakers IS the speaker transform (VTL ∘ accent ∘ channel). Given those
/// residual vectors `resid` (`n` rows × `dim`, already content-cancelled =
/// same-word-cross-speaker per-frame differences), return the top-`k`
/// principal directions of their covariance = the nuisance subspace to
/// QUOTIENT out (project onto its complement). This DISCOVERS the transform
/// dimensions empirically instead of hand-designing them; unlike an LDA
/// metric it is a projection (a transform), so it generalises to UNSEEN
/// speakers. Top-k via power iteration + deflation on C = (1/n) Rᵀ R.
/// Returns k*dim (row-major, unit eigenvectors).
pub fn nuisance_subspace(resid: &[f32], n: usize, dim: usize, k: usize, iters: usize) -> Vec<f32> {
    if n == 0 || dim == 0 { return vec![]; }
    // covariance C = (1/n) Rᵀ R  (dim×dim)
    let mut c = vec![0.0f64; dim * dim];
    for r in 0..n {
        let row = &resid[r * dim..r * dim + dim];
        for i in 0..dim {
            let ri = row[i] as f64;
            if ri == 0.0 { continue; }
            let ci = &mut c[i * dim..i * dim + dim];
            for j in 0..dim { ci[j] += ri * row[j] as f64; }
        }
    }
    let inv = 1.0 / n as f64;
    for v in c.iter_mut() { *v *= inv; }
    let mut rng = 0x2545F4914F6CDD1Du64;
    let mut rnd = || -> f64 { rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17; ((rng >> 40) as f64) / (1u64 << 24) as f64 - 0.5 };
    let mut out = vec![0.0f32; k * dim];
    for comp in 0..k {
        let mut v = vec![0.0f64; dim];
        for x in v.iter_mut() { *x = rnd(); }
        for _ in 0..iters {
            // w = C v
            let mut w = vec![0.0f64; dim];
            for i in 0..dim {
                let ci = &c[i * dim..i * dim + dim];
                let mut s = 0.0; for j in 0..dim { s += ci[j] * v[j]; }
                w[i] = s;
            }
            let nrm = (w.iter().map(|x| x * x).sum::<f64>()).sqrt() + 1e-12;
            for i in 0..dim { v[i] = w[i] / nrm; }
        }
        // eigenvalue lambda = vᵀ C v
        let mut cv = vec![0.0f64; dim];
        for i in 0..dim { let ci = &c[i * dim..i * dim + dim]; let mut s = 0.0; for j in 0..dim { s += ci[j] * v[j]; } cv[i] = s; }
        let lam: f64 = (0..dim).map(|i| v[i] * cv[i]).sum();
        // deflate C -= lam v vᵀ
        for i in 0..dim { for j in 0..dim { c[i * dim + j] -= lam * v[i] * v[j]; } }
        for i in 0..dim { out[comp * dim + i] = v[i] as f32; }
    }
    out
}

/// DIMENSIONAL LIFT — make the cross-speaker warp a ROTATION, then
/// project it out (the coordinator's homogeneous/Z-rotation principle).
///
/// The cochleagram is LOG-frequency, so the dominant speaker nuisance —
/// vocal-tract-length (VTL) — is approximately a MULTIPLICATIVE frequency
/// scaling = a RIGID SHIFT `Δ` along the band axis. Lift each frame into
/// its Fourier modes along the bands: `C_k = Σ_b c[b] e^{-i2πkb/nb}`,
/// where the (Re,Im) pair of mode `k` is the extra ("Z") dimension. Under
/// a band shift `b→b+Δ`, `C_k → C_k · e^{-i2πkΔ/nb}` — i.e. a pure
/// ROTATION by `θ_k = 2πkΔ/nb` in each mode's plane. The nuisance is now
/// a rotation, not a hard nonlinear warp.
///
/// INVARIANCE = quotient the rotation cheaply and EXACTLY: the magnitude
/// `|C_k|` is rotation-invariant, so `[|C_1|..|C_M|]` is VTL-SHIFT
/// invariant. DISCRIMINATION survives because the magnitudes encode the
/// spectral SHAPE (what distinguishes phones/words) — we separate in the
/// LIFTED space, so there is no invariance-vs-discrimination trade. Output
/// per frame: `M` mode magnitudes (k=1..M; k=0/energy dropped since frames
/// are gain-normalised).
pub fn logfreq_lift(coch_flat: &[f32], n_frames: usize, n_bands: usize, n_modes: usize) -> Vec<f32> {
    let m = n_modes.max(1);
    let mut out = vec![0.0f32; n_frames * m];
    let nb = n_bands.max(1);
    // precompute cos/sin tables
    let mut cs = vec![0.0f32; m * nb];
    let mut sn = vec![0.0f32; m * nb];
    for k in 0..m {
        for b in 0..nb {
            let ang = -2.0 * std::f32::consts::PI * ((k + 1) as f32) * (b as f32) / nb as f32;
            cs[k * nb + b] = ang.cos();
            sn[k * nb + b] = ang.sin();
        }
    }
    for t in 0..n_frames {
        let c = &coch_flat[t * nb..t * nb + nb];
        for k in 0..m {
            let mut re = 0.0f32;
            let mut im = 0.0f32;
            for b in 0..nb {
                re += c[b] * cs[k * nb + b];
                im += c[b] * sn[k * nb + b];
            }
            out[t * m + k] = (re * re + im * im).sqrt(); // rotation-invariant
        }
    }
    out
}

/// COCHLEAGRAM-BAND RENDER — project a phoneme's (F1,F2,F3) formants into
/// the 32-band cochleagram magnitude space `cochleagram` produces.
///
/// The text→transform bridge recovers accent shift-vectors in FORMANT
/// coordinates (F1/F2/F3 Hz). To apply / quotient that transform on REAL
/// cochleagram audio (and the APC representation built on it) the shift
/// must live in the SAME log-frequency BAND space. Each formant excites a
/// Gaussian bump (in log-frequency) at its centre; the bank's band centres
/// are `audio_primitives::coch_band_centers()`. `sigma` is the bump width
/// in natural-log-frequency units (~0.35 ≈ a formant's spectral spread);
/// amplitudes taper F1>F2>F3 (source spectral tilt). Returns 32 band
/// magnitudes. A phoneme→band TEMPLATE; a shift-vector in band space is
/// then `formant_bands(tgt) - formant_bands(src)` — the direction to ADD
/// (inject an accent) or SUBTRACT (quotient it out) on a cochleagram frame.
pub fn formant_bands(f1: f32, f2: f32, f3: f32, sigma: f32) -> Vec<f32> {
    let centers = crate::audio_primitives::coch_band_centers();
    let amps = [1.0f64, 0.7, 0.5];
    let fs = [f1 as f64, f2 as f64, f3 as f64];
    let s = (sigma as f64).max(1e-3);
    let mut out = vec![0.0f32; centers.len()];
    for (b, &cf) in centers.iter().enumerate() {
        let lb = (cf as f64).ln();
        let mut v = 0.0f64;
        for k in 0..3 {
            if fs[k] <= 0.0 { continue; }
            let d = (lb - fs[k].ln()) / s;
            v += amps[k] * (-0.5 * d * d).exp();
        }
        out[b] = v as f32;
    }
    out
}

/// Flat model layout (Vec<f32>):
///   [0]=din  [1]=dh  [2]=bidir(0/1)
///   fwd:  W_f[din*dh]  U[dh*dh]  b[dh]
///   bwd (iff bidir):  W_f2[din*dh]  U2[dh*dh]  b2[dh]
/// The prediction heads (W_p/c) are training-only and NOT stored — the
/// representation is the context state, not the prediction.
const HDR: usize = 3;

#[inline]
fn xavier(rng: &mut u64, fan_in: usize) -> f32 {
    // cheap xorshift uniform in [-1,1) scaled by 1/sqrt(fan_in)
    *rng ^= *rng << 13;
    *rng ^= *rng >> 7;
    *rng ^= *rng << 17;
    let u = ((*rng >> 40) as f32) / (1u64 << 24) as f32; // [0,1)
    (2.0 * u - 1.0) / (fan_in as f32).sqrt()
}

struct Rnn {
    din: usize,
    dh: usize,
    wf: Vec<f32>, // din*dh
    u: Vec<f32>,  // dh*dh
    b: Vec<f32>,  // dh
    wp: Vec<f32>, // dh*din  (prediction head, training only)
    c: Vec<f32>,  // din
}

impl Rnn {
    fn new(din: usize, dh: usize, rng: &mut u64) -> Rnn {
        let mut wf = vec![0.0f32; din * dh];
        for w in wf.iter_mut() { *w = xavier(rng, din); }
        let mut u = vec![0.0f32; dh * dh];
        for w in u.iter_mut() { *w = xavier(rng, dh) * 0.5; } // small recurrence
        let mut wp = vec![0.0f32; dh * din];
        for w in wp.iter_mut() { *w = xavier(rng, dh); }
        Rnn { din, dh, wf, u, b: vec![0.0; dh], wp, c: vec![0.0; din] }
    }

    /// Forward pass over one sequence (`tu` frames of `din`), forward in
    /// time. Returns `h` flat [tu*dh]. `rev` runs backward in time
    /// (used for the bidirectional backward RNN).
    fn forward(&self, x: &[f32], tu: usize, rev: bool) -> Vec<f32> {
        let (din, dh) = (self.din, self.dh);
        let mut h = vec![0.0f32; tu * dh];
        let mut hprev = vec![0.0f32; dh];
        for step in 0..tu {
            let t = if rev { tu - 1 - step } else { step };
            let xt = &x[t * din..t * din + din];
            let ht = &mut h[t * dh..t * dh + dh];
            for j in 0..dh {
                let mut a = self.b[j];
                for i in 0..din { a += xt[i] * self.wf[i * dh + j]; }
                for i in 0..dh { a += hprev[i] * self.u[i * dh + j]; }
                ht[j] = a.tanh();
            }
            hprev.copy_from_slice(ht);
        }
        h
    }
}

/// Train an APC RNN (label-free) on a batch of variable-length
/// sequences. `frames_flat` is all sequences concatenated (each frame
/// `din` floats, row-major); `seq_lens` gives each sequence's frame
/// count. Returns the flat model (see layout above).
///
/// `k_ahead` = prediction horizon (frames). `bidir` also trains a
/// backward-in-time RNN predicting `x_{t-K}`. `shuffle_future` is the
/// CONTROL: predict a *randomly permuted* future frame, destroying the
/// predictive structure — the earned gain must collapse toward raw.
#[allow(clippy::too_many_arguments)]
pub fn train(
    frames_flat: &[f32],
    seq_lens: &[usize],
    din: usize,
    dh: usize,
    k_ahead: usize,
    epochs: usize,
    lr: f32,
    bidir: bool,
    seed: u64,
    shuffle_future: bool,
) -> Vec<f32> {
    let mut rng = seed.wrapping_mul(0x9E3779B97F4A7C15).wrapping_add(1);
    let mut fwd = Rnn::new(din, dh, &mut rng);
    let mut bwd = if bidir { Some(Rnn::new(din, dh, &mut rng)) } else { None };

    // sequence offsets into frames_flat (in frames)
    let mut offs = Vec::with_capacity(seq_lens.len());
    let mut acc = 0usize;
    for &l in seq_lens { offs.push(acc); acc += l; }

    // momentum buffers
    let mom = 0.9f32;
    let mut m_fwf = vec![0.0f32; fwd.wf.len()];
    let mut m_fu = vec![0.0f32; fwd.u.len()];
    let mut m_fb = vec![0.0f32; fwd.b.len()];
    let mut m_fwp = vec![0.0f32; fwd.wp.len()];
    let mut m_fc = vec![0.0f32; fwd.c.len()];
    // backward momentum (only if bidir)
    let mut m_bwf = vec![0.0f32; if bidir { din * dh } else { 0 }];
    let mut m_bu = vec![0.0f32; if bidir { dh * dh } else { 0 }];
    let mut m_bb = vec![0.0f32; if bidir { dh } else { 0 }];
    let mut m_bwp = vec![0.0f32; if bidir { dh * din } else { 0 }];
    let mut m_bc = vec![0.0f32; if bidir { din } else { 0 }];

    let mut order: Vec<usize> = (0..seq_lens.len()).collect();

    for ep in 0..epochs {
        // shuffle sequence order
        for i in (1..order.len()).rev() {
            rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17;
            let j = (rng >> 33) as usize % (i + 1);
            order.swap(i, j);
        }
        let mut tot_loss = 0.0f64;
        let mut tot_n = 0usize;

        for &si in &order {
            let tu = seq_lens[si];
            if tu <= k_ahead + 1 { continue; }
            let x = &frames_flat[offs[si] * din..(offs[si] + tu) * din];

            // ---- FORWARD RNN: predict x_{t+K} ----
            let (dl, dn) = train_one_dir(&mut fwd, x, tu, din, dh, k_ahead, false,
                                         shuffle_future, &mut rng,
                                         lr, mom,
                                         &mut m_fwf, &mut m_fu, &mut m_fb,
                                         &mut m_fwp, &mut m_fc, None);
            tot_loss += dl; tot_n += dn;

            // ---- BACKWARD RNN: predict x_{t-K} ----
            if let Some(bw) = bwd.as_mut() {
                let (dl2, dn2) = train_one_dir(bw, x, tu, din, dh, k_ahead, true,
                                               shuffle_future, &mut rng,
                                               lr, mom,
                                               &mut m_bwf, &mut m_bu, &mut m_bb,
                                               &mut m_bwp, &mut m_bc, None);
                tot_loss += dl2; tot_n += dn2;
            }
        }
        if ep == 0 || ep + 1 == epochs || (ep + 1) % (epochs.max(8) / 8).max(1) == 0 {
            eprintln!("    [apc.train] epoch {:4}: L2 next-frame loss {:.5} (n={})",
                      ep, tot_loss / tot_n.max(1) as f64, tot_n);
        }
    }

    // ---- pack model (encode weights only) ----
    let mut model = Vec::with_capacity(HDR + fwd.wf.len() + fwd.u.len() + fwd.b.len()
        + if bidir { fwd.wf.len() + fwd.u.len() + fwd.b.len() } else { 0 });
    model.push(din as f32);
    model.push(dh as f32);
    model.push(if bidir { 1.0 } else { 0.0 });
    model.extend_from_slice(&fwd.wf);
    model.extend_from_slice(&fwd.u);
    model.extend_from_slice(&fwd.b);
    if let Some(bw) = bwd.as_ref() {
        model.extend_from_slice(&bw.wf);
        model.extend_from_slice(&bw.u);
        model.extend_from_slice(&bw.b);
    }
    model
}

/// SupCon-style multi-positive InfoNCE loss + gradient over a BATCH of
/// pooled word embeddings (`emb`, `m` rows x `dh`, UNnormalized mean-pooled
/// RNN states). `ids` = word identity per occurrence (the positive/negative
/// structure: same id, different occurrence = positive; different id =
/// negative — in-batch negatives, standard softmax/cross-entropy over
/// cosine similarity at temperature `tau`).
///
/// For anchor `i` with positive set `P(i) = {j != i : ids[j]==ids[i]}`
/// (skipped if empty):
///   L_i = -1/|P(i)| * sum_{p in P(i)} log( exp(sim_ip/tau) / sum_{a!=i} exp(sim_ia/tau) )
///   dL_i/d sim_ia = (1/tau) * ( softmax_i(a) - 1[a in P(i)]/|P(i)| )     (a != i)
/// then chained through the cosine-similarity Jacobian back to the raw
/// (unnormalized) embeddings `e_i`. Returns (mean loss over anchors with
/// >=1 positive, grad flat `[m*dh]` w.r.t. the raw pooled embeddings).
fn infonce_grad(emb: &[f32], ids: &[i64], m: usize, dh: usize, tau: f32) -> (f64, Vec<f32>) {
    let mut grad_e = vec![0.0f32; m * dh];
    if m < 2 { return (0.0, grad_e); }
    let tau = tau.max(1e-3);
    // unit-normalize
    let mut z = vec![0.0f32; m * dh];
    let mut norms = vec![0.0f32; m];
    for i in 0..m {
        let e = &emb[i * dh..i * dh + dh];
        let n = e.iter().map(|v| v * v).sum::<f32>().sqrt().max(1e-8);
        norms[i] = n;
        for d in 0..dh { z[i * dh + d] = e[d] / n; }
    }
    // full cosine-similarity matrix (symmetric)
    let mut sim = vec![0.0f32; m * m];
    for i in 0..m {
        for j in (i + 1)..m {
            let mut s = 0.0f32;
            for d in 0..dh { s += z[i * dh + d] * z[j * dh + d]; }
            sim[i * m + j] = s; sim[j * m + i] = s;
        }
    }
    let mut grad_z = vec![0.0f32; m * dh];
    let mut loss = 0.0f64;
    let mut n_anchors = 0usize;
    for i in 0..m {
        let pos: Vec<usize> = (0..m).filter(|&j| j != i && ids[j] == ids[i]).collect();
        if pos.is_empty() { continue; }
        n_anchors += 1;
        let np = pos.len() as f32;
        // stable softmax over a != i
        let mut mx = f32::NEG_INFINITY;
        for a in 0..m { if a != i { mx = mx.max(sim[i * m + a] / tau); } }
        let mut denom = 0.0f32;
        let mut p = vec![0.0f32; m];
        for a in 0..m {
            if a != i {
                let e = ((sim[i * m + a] / tau) - mx).exp();
                p[a] = e; denom += e;
            }
        }
        let denom = denom.max(1e-12);
        for a in 0..m { if a != i { p[a] /= denom; } }
        for &pp in &pos {
            let logp = (sim[i * m + pp] / tau - mx) - denom.ln();
            loss -= (logp as f64) / (np as f64);
        }
        for a in 0..m {
            if a == i { continue; }
            let ispos = pos.contains(&a);
            let coeff = (p[a] - if ispos { 1.0 / np } else { 0.0 }) / tau;
            if coeff == 0.0 { continue; }
            for d in 0..dh {
                grad_z[i * dh + d] += coeff * z[a * dh + d];
                grad_z[a * dh + d] += coeff * z[i * dh + d];
            }
        }
    }
    // chain rule: z_i = e_i/||e_i|| -> grad_e_i = (grad_z_i - (grad_z_i.z_i) z_i) / ||e_i||
    for i in 0..m {
        let gz = &grad_z[i * dh..i * dh + dh];
        let zi = &z[i * dh..i * dh + dh];
        let dot: f32 = gz.iter().zip(zi.iter()).map(|(a, b)| a * b).sum();
        let inv_n = 1.0 / norms[i];
        for d in 0..dh { grad_e[i * dh + d] = (gz[d] - dot * zi[d]) * inv_n; }
    }
    let mean_loss = if n_anchors > 0 { loss / n_anchors as f64 } else { 0.0 };
    (mean_loss, grad_e)
}

/// Train APC WITH a same-word-positive / different-word-negative InfoNCE
/// contrastive head (Lever 2 of the context-predictive front-end push).
/// Same predictive objective as `train`, PLUS: per mini-batch of
/// `batch_size` utterances, (1) a forward-only pass (frozen weights) over
/// each utterance in the batch, (2) MEAN-POOL the resulting `h_t` over each
/// word's `[start,end)` span (the MMS-bootstrap spans, `word_seq_idx` /
/// `word_start` / `word_end` / `word_id`) to get one embedding per word
/// occurrence, (3) an in-batch SupCon/InfoNCE loss+gradient over those
/// pooled embeddings (`infonce_grad`), (4) spread each embedding's gradient
/// UNIFORMLY back over its span's frames as an extra `dh_out` contribution
/// (`train_one_dir`'s `extra_dh`), (5) run the existing predictive-loss
/// BPTT + SGD/momentum update PER UTTERANCE in the batch (so both losses'
/// gradients flow through the SAME backprop sweep and the SAME weight
/// update — the simplification vs. a single averaged batch step is that
/// each utterance's own predictive+NCE-informed update is applied
/// immediately rather than accumulated-then-applied-once; the NCE signal
/// itself is still genuinely batch-computed from a frozen-weight forward
/// pass giving real in-batch negatives).
///
/// `shuffle_word_id` is the CONTROL: permute `ids` WITHIN each batch before
/// computing pos/neg — destroys same-word structure while leaving spans /
/// forward passes untouched, so a real gain must collapse under it.
#[allow(clippy::too_many_arguments)]
pub fn train_contrastive(
    frames_flat: &[f32],
    seq_lens: &[usize],
    din: usize,
    dh: usize,
    k_ahead: usize,
    epochs: usize,
    lr: f32,
    bidir: bool,
    seed: u64,
    shuffle_future: bool,
    word_seq_idx: &[usize],
    word_start: &[usize],
    word_end: &[usize],
    word_id: &[i64],
    lambda_nce: f32,
    tau: f32,
    batch_size: usize,
    shuffle_word_id: bool,
) -> Vec<f32> {
    use std::collections::HashMap;
    let mut rng = seed.wrapping_mul(0x9E3779B97F4A7C15).wrapping_add(1);
    let mut fwd = Rnn::new(din, dh, &mut rng);
    let mut bwd = if bidir { Some(Rnn::new(din, dh, &mut rng)) } else { None };

    let mut offs = Vec::with_capacity(seq_lens.len());
    let mut acc = 0usize;
    for &l in seq_lens { offs.push(acc); acc += l; }

    // group word occurrences by their owning sequence
    let mut by_seq: HashMap<usize, Vec<(usize, usize, i64)>> = HashMap::new();
    for k in 0..word_seq_idx.len() {
        let si = word_seq_idx[k];
        if si >= seq_lens.len() { continue; }
        let (s, e) = (word_start[k], word_end[k].min(seq_lens[si]));
        if e <= s { continue; }
        by_seq.entry(si).or_default().push((s, e, word_id[k]));
    }

    let mom = 0.9f32;
    let mut m_fwf = vec![0.0f32; fwd.wf.len()];
    let mut m_fu = vec![0.0f32; fwd.u.len()];
    let mut m_fb = vec![0.0f32; fwd.b.len()];
    let mut m_fwp = vec![0.0f32; fwd.wp.len()];
    let mut m_fc = vec![0.0f32; fwd.c.len()];
    let mut m_bwf = vec![0.0f32; if bidir { din * dh } else { 0 }];
    let mut m_bu = vec![0.0f32; if bidir { dh * dh } else { 0 }];
    let mut m_bb = vec![0.0f32; if bidir { dh } else { 0 }];
    let mut m_bwp = vec![0.0f32; if bidir { dh * din } else { 0 }];
    let mut m_bc = vec![0.0f32; if bidir { din } else { 0 }];

    let bsz = batch_size.max(1);
    let mut order: Vec<usize> = (0..seq_lens.len()).collect();
    let mut rnd = |rng: &mut u64, m: usize| -> usize {
        *rng ^= *rng << 13; *rng ^= *rng >> 7; *rng ^= *rng << 17;
        (*rng >> 33) as usize % m.max(1)
    };

    for ep in 0..epochs {
        for i in (1..order.len()).rev() { let j = rnd(&mut rng, i + 1); order.swap(i, j); }
        let mut tot_pred_loss = 0.0f64;
        let mut tot_pred_n = 0usize;
        let mut tot_nce_loss = 0.0f64;
        let mut nce_batches = 0usize;

        for chunk in order.clone().chunks(bsz) {
            // ---- phase 1: forward-only pass (frozen weights) over the batch ----
            let mut hf_chunk: Vec<Vec<f32>> = Vec::with_capacity(chunk.len());
            let mut hb_chunk: Vec<Vec<f32>> = Vec::with_capacity(chunk.len());
            for &si in chunk {
                let tu = seq_lens[si];
                let x = &frames_flat[offs[si] * din..(offs[si] + tu) * din];
                hf_chunk.push(fwd.forward(x, tu, false));
                if let Some(bw) = bwd.as_ref() { hb_chunk.push(bw.forward(x, tu, true)); }
            }

            // ---- phase 2: pool word embeddings (fwd, and bwd if bidir) ----
            // records: (chunk_pos, start, end) parallel to the embedding rows
            let mut fwd_rec: Vec<(usize, usize, usize)> = Vec::new();
            let mut fwd_emb: Vec<f32> = Vec::new();
            let mut fwd_ids: Vec<i64> = Vec::new();
            let mut bwd_rec: Vec<(usize, usize, usize)> = Vec::new();
            let mut bwd_emb: Vec<f32> = Vec::new();
            let mut bwd_ids: Vec<i64> = Vec::new();
            for (ci, &si) in chunk.iter().enumerate() {
                let Some(words) = by_seq.get(&si) else { continue };
                for &(s, e, id) in words {
                    let span = (e - s).max(1);
                    let mut pooled = vec![0.0f32; dh];
                    let hf = &hf_chunk[ci];
                    for t in s..e { for d in 0..dh { pooled[d] += hf[t * dh + d]; } }
                    for d in 0..dh { pooled[d] /= span as f32; }
                    fwd_rec.push((ci, s, e)); fwd_emb.extend_from_slice(&pooled); fwd_ids.push(id);
                    if bidir {
                        let hb = &hb_chunk[ci];
                        let mut poolb = vec![0.0f32; dh];
                        for t in s..e { for d in 0..dh { poolb[d] += hb[t * dh + d]; } }
                        for d in 0..dh { poolb[d] /= span as f32; }
                        bwd_rec.push((ci, s, e)); bwd_emb.extend_from_slice(&poolb); bwd_ids.push(id);
                    }
                }
            }

            // ---- shuffled-label control: permute ids WITHIN the batch ----
            if shuffle_word_id {
                let n = fwd_ids.len();
                for i in (1..n).rev() { let j = rnd(&mut rng, i + 1); fwd_ids.swap(i, j); }
                if bidir {
                    let nb = bwd_ids.len();
                    for i in (1..nb).rev() { let j = rnd(&mut rng, i + 1); bwd_ids.swap(i, j); }
                }
            }

            // ---- phase 3: InfoNCE loss + gradient over the batch's pooled embeddings ----
            let mf = fwd_rec.len();
            let (nce_l_f, grad_f) = infonce_grad(&fwd_emb, &fwd_ids, mf, dh, tau);
            let (nce_l_b, grad_b) = if bidir {
                let mb = bwd_rec.len();
                infonce_grad(&bwd_emb, &bwd_ids, mb, dh, tau)
            } else { (0.0, vec![]) };
            if mf > 0 { tot_nce_loss += nce_l_f + nce_l_b; nce_batches += 1; }

            // ---- phase 4: spread embedding gradients back over frames ----
            let mut extra_f: Vec<Vec<f32>> = chunk.iter().map(|&si| vec![0.0f32; seq_lens[si] * dh]).collect();
            for (r, &(ci, s, e)) in fwd_rec.iter().enumerate() {
                let span = (e - s).max(1) as f32;
                let scale = lambda_nce / span;
                for t in s..e {
                    for d in 0..dh { extra_f[ci][t * dh + d] += grad_f[r * dh + d] * scale; }
                }
            }
            let mut extra_b: Vec<Vec<f32>> = if bidir {
                chunk.iter().map(|&si| vec![0.0f32; seq_lens[si] * dh]).collect()
            } else { vec![] };
            if bidir {
                for (r, &(ci, s, e)) in bwd_rec.iter().enumerate() {
                    let span = (e - s).max(1) as f32;
                    let scale = lambda_nce / span;
                    for t in s..e {
                        for d in 0..dh { extra_b[ci][t * dh + d] += grad_b[r * dh + d] * scale; }
                    }
                }
            }

            // ---- phase 5: predictive BPTT + SGD/momentum update, per utterance,
            // with the NCE gradient folded into dh_out via extra_dh ----
            for (ci, &si) in chunk.iter().enumerate() {
                let tu = seq_lens[si];
                if tu <= k_ahead + 1 { continue; }
                let x = &frames_flat[offs[si] * din..(offs[si] + tu) * din];
                let (dl, dn) = train_one_dir(&mut fwd, x, tu, din, dh, k_ahead, false,
                                             shuffle_future, &mut rng, lr, mom,
                                             &mut m_fwf, &mut m_fu, &mut m_fb,
                                             &mut m_fwp, &mut m_fc, Some(&extra_f[ci]));
                tot_pred_loss += dl; tot_pred_n += dn;
                if let Some(bw) = bwd.as_mut() {
                    let (dl2, dn2) = train_one_dir(bw, x, tu, din, dh, k_ahead, true,
                                                   shuffle_future, &mut rng, lr, mom,
                                                   &mut m_bwf, &mut m_bu, &mut m_bb,
                                                   &mut m_bwp, &mut m_bc, Some(&extra_b[ci]));
                    tot_pred_loss += dl2; tot_pred_n += dn2;
                }
            }
        }
        if ep == 0 || ep + 1 == epochs || (ep + 1) % (epochs.max(8) / 8).max(1) == 0 {
            eprintln!("    [apc.train_contrastive] epoch {:4}: pred L2 {:.5} (n={}) | NCE {:.5} (batches={})",
                      ep, tot_pred_loss / tot_pred_n.max(1) as f64, tot_pred_n,
                      tot_nce_loss / nce_batches.max(1) as f64, nce_batches);
        }
    }

    let mut model = Vec::with_capacity(HDR + fwd.wf.len() + fwd.u.len() + fwd.b.len()
        + if bidir { fwd.wf.len() + fwd.u.len() + fwd.b.len() } else { 0 });
    model.push(din as f32);
    model.push(dh as f32);
    model.push(if bidir { 1.0 } else { 0.0 });
    model.extend_from_slice(&fwd.wf);
    model.extend_from_slice(&fwd.u);
    model.extend_from_slice(&fwd.b);
    if let Some(bw) = bwd.as_ref() {
        model.extend_from_slice(&bw.wf);
        model.extend_from_slice(&bw.u);
        model.extend_from_slice(&bw.b);
    }
    model
}

/// One SGD step (full-sequence BPTT) for a single directional RNN on one
/// sequence. Updates weights in-place; returns (summed loss, count).
///
/// `extra_dh`, when `Some`, is an EXTERNAL per-timestep gradient contribution
/// (flat `[tu*dh]`) ADDED to `dh_out` (the predictive-loss gradient) before
/// the BPTT sweep runs — this is how a contrastive (InfoNCE) loss on a
/// POOLED word embedding is threaded back into the same recurrent weight
/// update as the predictive-coding loss (see `train_contrastive`): the
/// pooled-embedding gradient is spread uniformly across the word's frames
/// and handed in here, then backprop treats it exactly like any other
/// per-timestep target gradient.
#[allow(clippy::too_many_arguments)]
fn train_one_dir(
    net: &mut Rnn,
    x: &[f32],
    tu: usize,
    din: usize,
    dh: usize,
    k: usize,
    rev: bool,
    shuffle_future: bool,
    rng: &mut u64,
    lr: f32,
    mom: f32,
    m_wf: &mut [f32],
    m_u: &mut [f32],
    m_b: &mut [f32],
    m_wp: &mut [f32],
    m_c: &mut [f32],
    extra_dh: Option<&[f32]>,
) -> (f64, usize) {
    let h = net.forward(x, tu, rev);

    let mut g_wf = vec![0.0f32; din * dh];
    let mut g_u = vec![0.0f32; dh * dh];
    let mut g_b = vec![0.0f32; dh];
    let mut g_wp = vec![0.0f32; dh * din];
    let mut g_c = vec![0.0f32; din];
    // dL/dh_t accumulated from the prediction head; the recurrent
    // contribution is added during the BPTT sweep.
    let mut dh_out = vec![0.0f32; tu * dh];

    let mut loss = 0.0f64;
    let mut cnt = 0usize;

    // Visit steps in the network's time order; the "future" target for a
    // forward net is +K, for a backward net is -K (in raw time).
    for step in 0..tu {
        let t = if rev { tu - 1 - step } else { step };
        // target index (raw time)
        let tgt = if rev {
            if t < k { continue; } else { t - k }
        } else {
            if t + k >= tu { continue; } else { t + k }
        };
        let tgt = if shuffle_future {
            // permute the target within valid range -> destroys structure
            *rng ^= *rng << 13; *rng ^= *rng >> 7; *rng ^= *rng << 17;
            (*rng >> 33) as usize % tu
        } else { tgt };

        let ht = &h[t * dh..t * dh + dh];
        // o = h_t Wp + c ; err = o - x_tgt
        let xt = &x[tgt * din..tgt * din + din];
        let mut err = vec![0.0f32; din];
        for d in 0..din {
            let mut o = net.c[d];
            for j in 0..dh { o += ht[j] * net.wp[j * din + d]; }
            let e = o - xt[d];
            err[d] = e;
            loss += (e * e) as f64;
        }
        cnt += 1;
        // grads for prediction head + dL/dh_t
        for d in 0..din {
            let e = 2.0 * err[d];
            g_c[d] += e;
            for j in 0..dh {
                g_wp[j * din + d] += ht[j] * e;
                dh_out[t * dh + j] += e * net.wp[j * din + d];
            }
        }
    }
    if cnt == 0 { return (0.0, 0); }

    // ---- external gradient injection (e.g. InfoNCE on a pooled word
    // embedding, spread uniformly over its span) — added BEFORE the BPTT
    // sweep so it flows through the same recurrent backprop as the
    // predictive-loss gradient. ----
    if let Some(ed) = extra_dh {
        for i in 0..dh_out.len() { dh_out[i] += ed[i]; }
    }

    // ---- BPTT sweep (reverse of the forward time order) ----
    // dh_next = recurrent gradient flowing into the *previous* forward step.
    let mut dh_next = vec![0.0f32; dh];
    for step in (0..tu).rev() {
        let t = if rev { tu - 1 - step } else { step };
        let ht = &h[t * dh..t * dh + dh];
        // total dh_t = head grad + recurrent grad from the next step
        let mut da = vec![0.0f32; dh];
        for j in 0..dh {
            let g = dh_out[t * dh + j] + dh_next[j];
            da[j] = g * (1.0 - ht[j] * ht[j]); // tanh'
        }
        // grads: g_b += da; g_wf += x_t^T da; g_u += h_{prev}^T da
        let xt = &x[t * din..t * din + din];
        for j in 0..dh {
            g_b[j] += da[j];
            let waj = &mut g_wf[..]; // borrow helper
            for i in 0..din { waj[i * dh + j] += xt[i] * da[j]; }
        }
        // h_prev is the state at the previous *network* step
        let prev_t: Option<usize> = if step == 0 {
            None
        } else if rev { Some((tu - 1 - step) + 1) } else { Some(t - 1) };
        if let Some(pt) = prev_t {
            let hprev = &h[pt * dh..pt * dh + dh];
            for j in 0..dh {
                for i in 0..dh { g_u[i * dh + j] += hprev[i] * da[j]; }
            }
        }
        // recurrent grad into previous step: dh_prev = da U^T
        let mut dprev = vec![0.0f32; dh];
        for i in 0..dh {
            let mut s = 0.0f32;
            for j in 0..dh { s += da[j] * net.u[i * dh + j]; }
            dprev[i] = s;
        }
        dh_next = dprev;
    }

    // ---- global-norm gradient clip ----
    let clip = 5.0f32;
    let mut nrm = 0.0f64;
    for v in g_wf.iter().chain(g_u.iter()).chain(g_b.iter())
        .chain(g_wp.iter()).chain(g_c.iter()) { nrm += (*v as f64) * (*v as f64); }
    let nrm = nrm.sqrt() as f32;
    let scale = if nrm > clip { clip / (nrm + 1e-8) } else { 1.0 };
    let inv = scale / cnt as f32;

    // ---- SGD + momentum update ----
    upd(&mut net.wf, m_wf, &g_wf, lr, mom, inv);
    upd(&mut net.u, m_u, &g_u, lr, mom, inv);
    upd(&mut net.b, m_b, &g_b, lr, mom, inv);
    upd(&mut net.wp, m_wp, &g_wp, lr, mom, inv);
    upd(&mut net.c, m_c, &g_c, lr, mom, inv);

    (loss, cnt * din)
}

#[inline]
fn upd(w: &mut [f32], m: &mut [f32], g: &[f32], lr: f32, mom: f32, inv: f32) {
    for i in 0..w.len() {
        m[i] = mom * m[i] + g[i] * inv;
        w[i] -= lr * m[i];
    }
}

/// Query–key InfoNCE (CPC-style) over a batch of `m` (query, key) pairs, each
/// `dt`-dim. `pos_idx[i]` = the index of query `i`'s POSITIVE key (identity by
/// default; a permutation is the shuffled-target CONTROL). Cosine-similarity
/// logits at temperature `tau`, softmax over ALL keys (in-batch negatives).
/// Returns (mean loss, grad_q [m*dt], grad_k [m*dt]). This is the FRAME-level
/// contrastive signal wav2vec2 uses (predict a masked frame's target from
/// bidirectional context) — distinct from `infonce_grad`'s pooled-word,
/// class-structured SupCon.
fn infonce_qk_grad(q: &[f32], k: &[f32], pos_idx: &[usize], m: usize, dt: usize, tau: f32)
    -> (f64, Vec<f32>, Vec<f32>) {
    let mut grad_q = vec![0.0f32; m * dt];
    let mut grad_k = vec![0.0f32; m * dt];
    if m < 2 { return (0.0, grad_q, grad_k); }
    let tau = tau.max(1e-3);
    // unit-normalize q and k
    let (mut qh, mut kh) = (vec![0.0f32; m * dt], vec![0.0f32; m * dt]);
    let (mut qn, mut kn) = (vec![0.0f32; m], vec![0.0f32; m]);
    for i in 0..m {
        let (qi, ki) = (&q[i * dt..i * dt + dt], &k[i * dt..i * dt + dt]);
        let a = qi.iter().map(|v| v * v).sum::<f32>().sqrt().max(1e-8);
        let b = ki.iter().map(|v| v * v).sum::<f32>().sqrt().max(1e-8);
        qn[i] = a; kn[i] = b;
        for d in 0..dt { qh[i * dt + d] = qi[d] / a; kh[i * dt + d] = ki[d] / b; }
    }
    // similarity + softmax per query row over all keys
    let mut grad_qh = vec![0.0f32; m * dt];
    let mut grad_kh = vec![0.0f32; m * dt];
    let mut loss = 0.0f64;
    let mut sim = vec![0.0f32; m];
    for i in 0..m {
        // sim_ij = <qh_i, kh_j>
        let mut mx = f32::NEG_INFINITY;
        for j in 0..m {
            let mut s = 0.0f32;
            for d in 0..dt { s += qh[i * dt + d] * kh[j * dt + d]; }
            sim[j] = s / tau; if sim[j] > mx { mx = sim[j]; }
        }
        let mut denom = 0.0f32;
        let mut p = vec![0.0f32; m];
        for j in 0..m { let e = (sim[j] - mx).exp(); p[j] = e; denom += e; }
        let denom = denom.max(1e-12);
        for j in 0..m { p[j] /= denom; }
        let pj = pos_idx[i].min(m - 1);
        loss -= ((p[pj].max(1e-12)).ln()) as f64;
        // dL/dsim_ij = (1/tau)(p_j - 1[j==pos]); dsim/dqh_i = kh_j; dsim/dkh_j = qh_i
        for j in 0..m {
            let coeff = (p[j] - if j == pj { 1.0 } else { 0.0 }) / tau;
            if coeff == 0.0 { continue; }
            for d in 0..dt {
                grad_qh[i * dt + d] += coeff * kh[j * dt + d];
                grad_kh[j * dt + d] += coeff * qh[i * dt + d];
            }
        }
    }
    // chain through the unit-normalization: grad_x = (grad_xh - <grad_xh,xh> xh)/||x||
    // and divide by m so the returned gradient matches the returned MEAN loss.
    let invm = 1.0f32 / m as f32;
    for i in 0..m {
        let (gq, qi) = (&grad_qh[i * dt..i * dt + dt], &qh[i * dt..i * dt + dt]);
        let dotq: f32 = gq.iter().zip(qi).map(|(a, b)| a * b).sum();
        for d in 0..dt { grad_q[i * dt + d] = (gq[d] - dotq * qi[d]) / qn[i] * invm; }
        let (gk, ki) = (&grad_kh[i * dt..i * dt + dt], &kh[i * dt..i * dt + dt]);
        let dotk: f32 = gk.iter().zip(ki).map(|(a, b)| a * b).sum();
        for d in 0..dt { grad_k[i * dt + d] = (gk[d] - dotk * ki[d]) / kn[i] * invm; }
    }
    (loss / m as f64, grad_q, grad_k)
}

/// BPTT for ONE directional RNN driven ONLY by an external per-frame gradient
/// `dh_ext` (flat `[tu*dh]`) — no predictive head. Accumulates weight grads
/// into `g_wf/g_u/g_b` (does NOT update). Mirrors `train_one_dir`'s proven
/// recurrent sweep. Used by `train_masked_cpc` where the upstream gradient is
/// the masked-frame InfoNCE signal at masked positions.
#[allow(clippy::too_many_arguments)]
fn bptt_ext(net: &Rnn, x: &[f32], h: &[f32], tu: usize, din: usize, dh: usize, rev: bool,
            dh_ext: &[f32], g_wf: &mut [f32], g_u: &mut [f32], g_b: &mut [f32]) {
    let mut dh_next = vec![0.0f32; dh];
    for step in (0..tu).rev() {
        let t = if rev { tu - 1 - step } else { step };
        let ht = &h[t * dh..t * dh + dh];
        let mut da = vec![0.0f32; dh];
        for j in 0..dh {
            let g = dh_ext[t * dh + j] + dh_next[j];
            da[j] = g * (1.0 - ht[j] * ht[j]);
        }
        let xt = &x[t * din..t * din + din];
        for j in 0..dh {
            g_b[j] += da[j];
            for i in 0..din { g_wf[i * dh + j] += xt[i] * da[j]; }
        }
        let prev_t: Option<usize> = if step == 0 { None }
            else if rev { Some((tu - 1 - step) + 1) } else { Some(t - 1) };
        if let Some(pt) = prev_t {
            let hprev = &h[pt * dh..pt * dh + dh];
            for j in 0..dh { for i in 0..dh { g_u[i * dh + j] += hprev[i] * da[j]; } }
        }
        let mut dprev = vec![0.0f32; dh];
        for i in 0..dh { let mut s = 0.0f32; for j in 0..dh { s += da[j] * net.u[i * dh + j]; } dprev[i] = s; }
        dh_next = dprev;
    }
}

/// MASKED-FRAME CONTRASTIVE PREDICTIVE CODING (the OBJECTIVE lever, Step C).
///
/// The specific thing wav2vec2 does that AR-APC does NOT: mask a fraction of
/// input frames, encode with BIDIRECTIONAL context, and predict each masked
/// frame's TRUE-frame target CONTRASTIVELY (InfoNCE over frames), not by
/// L2-regressing the next frame. Label-free (no word spans) — so the DATA
/// lever can scale on unlabeled audio cheaply.
///
/// Per masked frame `t`: query `q_t = Wq · ctx_t` where `ctx_t` is the
/// bidirectional context `[h_fwd_t ; h_bwd_t]` over the MASKED input (so `t`'s
/// own value is hidden); key/target `k_t = Wk · x_t` from the TRUE frame.
/// In-batch InfoNCE (positive = own key, negatives = other masked frames'
/// keys). `shuffle_ctrl` permutes the positive assignment = the CONTROL (a
/// real gain must collapse). Emits the SAME model layout as `train` /
/// `train_contrastive`, so the `ApcEncode` Term encodes it unchanged.
#[allow(clippy::too_many_arguments)]
pub fn train_masked_cpc(
    frames_flat: &[f32], seq_lens: &[usize], din: usize, dh: usize,
    epochs: usize, lr: f32, bidir: bool, seed: u64,
    mask_prob: f32, mask_span: usize, dt: usize, tau: f32, batch_size: usize, shuffle_ctrl: bool,
) -> Vec<f32> {
    let mut rng = seed.wrapping_mul(0x9E3779B97F4A7C15).wrapping_add(1);
    let mut fwd = Rnn::new(din, dh, &mut rng);
    let mut bwd = if bidir { Some(Rnn::new(din, dh, &mut rng)) } else { None };
    let cdim = if bidir { 2 * dh } else { dh };
    let mut wq = vec![0.0f32; cdim * dt];
    for w in wq.iter_mut() { *w = xavier(&mut rng, cdim); }
    let mut wk = vec![0.0f32; din * dt];
    for w in wk.iter_mut() { *w = xavier(&mut rng, din); }

    let mut offs = Vec::with_capacity(seq_lens.len());
    let mut acc = 0usize;
    for &l in seq_lens { offs.push(acc); acc += l; }

    let mom = 0.9f32;
    let (mut m_fwf, mut m_fu, mut m_fb) = (vec![0.0f32; din * dh], vec![0.0f32; dh * dh], vec![0.0f32; dh]);
    let (mut m_bwf, mut m_bu, mut m_bb) = (vec![0.0f32; if bidir { din * dh } else { 0 }],
        vec![0.0f32; if bidir { dh * dh } else { 0 }], vec![0.0f32; if bidir { dh } else { 0 }]);
    let mut m_wq = vec![0.0f32; wq.len()];
    let mut m_wk = vec![0.0f32; wk.len()];

    let bsz = batch_size.max(1);
    let mut order: Vec<usize> = (0..seq_lens.len()).collect();
    let mp = mask_prob.clamp(0.02, 0.8);
    let ms = mask_span.max(1);

    for ep in 0..epochs {
        for i in (1..order.len()).rev() {
            rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17;
            let j = (rng >> 33) as usize % (i + 1); order.swap(i, j);
        }
        let mut tot_loss = 0.0f64; let mut nb = 0usize;
        for chunk in order.clone().chunks(bsz) {
            // per-seq masked input + forward, collect masked-frame ctx / true-frame keys
            let mut ci_of: Vec<usize> = Vec::new();      // chunk-local seq index per masked frame
            let mut t_of: Vec<usize> = Vec::new();       // frame index per masked frame
            let mut ctx: Vec<f32> = Vec::new();          // m*cdim
            let mut truex: Vec<f32> = Vec::new();        // m*din
            let mut xmask: Vec<Vec<f32>> = Vec::new();   // per-seq masked input
            let mut hf_c: Vec<Vec<f32>> = Vec::new();
            let mut hb_c: Vec<Vec<f32>> = Vec::new();
            let mut mask_c: Vec<Vec<bool>> = Vec::new();
            for &si in chunk {
                let tu = seq_lens[si];
                let x = &frames_flat[offs[si] * din..(offs[si] + tu) * din];
                // choose masked frames (spans of length ms, avoid the two edges)
                let mut masked = vec![false; tu];
                if tu > ms + 2 {
                    let target = ((tu as f32) * mp).ceil() as usize;
                    let mut placed = 0usize; let mut guard = 0usize;
                    while placed < target && guard < tu * 4 {
                        guard += 1;
                        rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17;
                        let st = 1 + (rng >> 33) as usize % (tu - ms - 1).max(1);
                        for o in 0..ms { if st + o < tu - 1 && !masked[st + o] { masked[st + o] = true; placed += 1; } }
                    }
                }
                // masked input (masked frames -> 0 ~= z-normed mean)
                let mut xm = x.to_vec();
                for t in 0..tu { if masked[t] { for d in 0..din { xm[t * din + d] = 0.0; } } }
                let hf = fwd.forward(&xm, tu, false);
                let hb = if let Some(bw) = bwd.as_ref() { bw.forward(&xm, tu, true) } else { vec![] };
                let cci = xmask.len();
                for t in 0..tu {
                    if !masked[t] { continue; }
                    ci_of.push(cci); t_of.push(t);
                    for d in 0..dh { ctx.push(hf[t * dh + d]); }
                    if bidir { for d in 0..dh { ctx.push(hb[t * dh + d]); } }
                    for d in 0..din { truex.push(x[t * din + d]); }
                }
                xmask.push(xm); hf_c.push(hf); hb_c.push(hb); mask_c.push(masked);
            }
            let m = ci_of.len();
            if m < 2 { continue; }
            // q = ctx·Wq, k = truex·Wk
            let mut q = vec![0.0f32; m * dt];
            let mut kk = vec![0.0f32; m * dt];
            for r in 0..m {
                let cr = &ctx[r * cdim..r * cdim + cdim];
                for d in 0..dt { let mut s = 0.0f32; for c in 0..cdim { s += cr[c] * wq[c * dt + d]; } q[r * dt + d] = s; }
                let xr = &truex[r * din..r * din + din];
                for d in 0..dt { let mut s = 0.0f32; for c in 0..din { s += xr[c] * wk[c * dt + d]; } kk[r * dt + d] = s; }
            }
            let mut pos_idx: Vec<usize> = (0..m).collect();
            if shuffle_ctrl {
                for i in (1..m).rev() { rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17;
                    let j = (rng >> 33) as usize % (i + 1); pos_idx.swap(i, j); }
            }
            let (loss, grad_q, grad_k) = infonce_qk_grad(&q, &kk, &pos_idx, m, dt, tau);
            tot_loss += loss; nb += 1;

            // Wq, Wk grads + grad to ctx
            let mut g_wq = vec![0.0f32; wq.len()];
            let mut g_wk = vec![0.0f32; wk.len()];
            let mut grad_ctx = vec![0.0f32; m * cdim];
            for r in 0..m {
                let cr = &ctx[r * cdim..r * cdim + cdim];
                let gqr = &grad_q[r * dt..r * dt + dt];
                for c in 0..cdim { for d in 0..dt { g_wq[c * dt + d] += cr[c] * gqr[d]; } }
                for c in 0..cdim { let mut s = 0.0f32; for d in 0..dt { s += wq[c * dt + d] * gqr[d]; } grad_ctx[r * cdim + c] = s; }
                let xr = &truex[r * din..r * din + din];
                let gkr = &grad_k[r * dt..r * dt + dt];
                for c in 0..din { for d in 0..dt { g_wk[c * dt + d] += xr[c] * gkr[d]; } }
            }
            // scatter grad_ctx into per-seq per-frame dh_ext (fwd + bwd halves)
            let mut ext_f: Vec<Vec<f32>> = chunk.iter().map(|&si| vec![0.0f32; seq_lens[si] * dh]).collect();
            let mut ext_b: Vec<Vec<f32>> = if bidir {
                chunk.iter().map(|&si| vec![0.0f32; seq_lens[si] * dh]).collect() } else { vec![] };
            for r in 0..m {
                let (cci, t) = (ci_of[r], t_of[r]);
                for d in 0..dh { ext_f[cci][t * dh + d] += grad_ctx[r * cdim + d]; }
                if bidir { for d in 0..dh { ext_b[cci][t * dh + d] += grad_ctx[r * cdim + dh + d]; } }
            }
            // BPTT per seq -> accumulate RNN weight grads
            let (mut g_fwf, mut g_fu, mut g_fb) = (vec![0.0f32; din * dh], vec![0.0f32; dh * dh], vec![0.0f32; dh]);
            let (mut g_bwf, mut g_bu, mut g_bb) = (vec![0.0f32; if bidir { din * dh } else { 0 }],
                vec![0.0f32; if bidir { dh * dh } else { 0 }], vec![0.0f32; if bidir { dh } else { 0 }]);
            for (cci, &si) in chunk.iter().enumerate() {
                let tu = seq_lens[si];
                bptt_ext(&fwd, &xmask[cci], &hf_c[cci], tu, din, dh, false, &ext_f[cci],
                         &mut g_fwf, &mut g_fu, &mut g_fb);
                if let Some(bw) = bwd.as_ref() {
                    bptt_ext(bw, &xmask[cci], &hb_c[cci], tu, din, dh, true, &ext_b[cci],
                             &mut g_bwf, &mut g_bu, &mut g_bb);
                }
            }
            // clip + update (scale by 1/m so the step is invariant to batch masked-count)
            let mut nrm = 0.0f64;
            for v in g_fwf.iter().chain(g_fu.iter()).chain(g_fb.iter())
                .chain(g_bwf.iter()).chain(g_bu.iter()).chain(g_bb.iter())
                .chain(g_wq.iter()).chain(g_wk.iter()) { nrm += (*v as f64) * (*v as f64); }
            let nrm = nrm.sqrt() as f32;
            let clip = 5.0f32;
            let scale = if nrm > clip { clip / (nrm + 1e-8) } else { 1.0 };
            let inv = scale;   // grads already the MEAN-loss gradient (infonce_qk_grad divides by m)
            upd(&mut fwd.wf, &mut m_fwf, &g_fwf, lr, mom, inv);
            upd(&mut fwd.u, &mut m_fu, &g_fu, lr, mom, inv);
            upd(&mut fwd.b, &mut m_fb, &g_fb, lr, mom, inv);
            if let Some(bw) = bwd.as_mut() {
                upd(&mut bw.wf, &mut m_bwf, &g_bwf, lr, mom, inv);
                upd(&mut bw.u, &mut m_bu, &g_bu, lr, mom, inv);
                upd(&mut bw.b, &mut m_bb, &g_bb, lr, mom, inv);
            }
            upd(&mut wq, &mut m_wq, &g_wq, lr, mom, inv);
            upd(&mut wk, &mut m_wk, &g_wk, lr, mom, inv);
        }
        if ep == 0 || ep + 1 == epochs || (ep + 1) % (epochs.max(8) / 8).max(1) == 0 {
            eprintln!("    [apc.masked_cpc] epoch {:4}: InfoNCE-frame loss {:.5} (batches={})",
                      ep, tot_loss / nb.max(1) as f64, nb);
        }
    }
    // pack model (SAME layout as `train` -> ApcEncode reads it unchanged)
    let mut model = Vec::with_capacity(HDR + fwd.wf.len() + fwd.u.len() + fwd.b.len()
        + if bidir { fwd.wf.len() + fwd.u.len() + fwd.b.len() } else { 0 });
    model.push(din as f32); model.push(dh as f32); model.push(if bidir { 1.0 } else { 0.0 });
    model.extend_from_slice(&fwd.wf); model.extend_from_slice(&fwd.u); model.extend_from_slice(&fwd.b);
    if let Some(bw) = bwd.as_ref() {
        model.extend_from_slice(&bw.wf); model.extend_from_slice(&bw.u); model.extend_from_slice(&bw.b);
    }
    model
}

#[cfg(test)]
mod cpc_tests {
    use super::infonce_qk_grad;
    #[test]
    fn qk_grad_numeric() {
        // numerical gradient check of infonce_qk_grad (the new frame-level math)
        let (m, dt) = (4usize, 3usize);
        let q: Vec<f32> = (0..m * dt).map(|i| ((i * 7 % 11) as f32 - 5.0) * 0.13).collect();
        let k: Vec<f32> = (0..m * dt).map(|i| ((i * 5 % 13) as f32 - 6.0) * 0.11).collect();
        let pos: Vec<usize> = (0..m).collect();
        let (l0, gq, gk) = infonce_qk_grad(&q, &k, &pos, m, dt, 0.2);
        let eps = 1e-3f32;
        let loss = |qq: &[f32], kk: &[f32]| infonce_qk_grad(qq, kk, &pos, m, dt, 0.2).0;
        let mut max_err = 0.0f64;
        for i in 0..m * dt {
            let mut qp = q.clone(); qp[i] += eps; let lp = loss(&qp, &k);
            let mut qm = q.clone(); qm[i] -= eps; let lm = loss(&qm, &k);
            let num = ((lp - lm) / (2.0 * eps as f64)) as f32;
            max_err = max_err.max((num - gq[i]).abs() as f64);
            let mut kp = k.clone(); kp[i] += eps; let lp = loss(&q, &kp);
            let mut km = k.clone(); km[i] -= eps; let lm = loss(&q, &km);
            let num = ((lp - lm) / (2.0 * eps as f64)) as f32;
            max_err = max_err.max((num - gk[i]).abs() as f64);
        }
        assert!(l0.is_finite());
        assert!(max_err < 2e-2, "grad mismatch {max_err}");
    }
}

/// Run the learned ENCODE: forward the context RNN(s) over the full
/// input sequence, slice frames `[start,end)`, resample to `out_len`.
/// Returns (flat [out_len*rep_dim], rep_dim). rep_dim = dh (unidir) or
/// 2*dh (bidir, concat forward++backward). If `start<0`/`end<0` or out
/// of range, the whole sequence is used.
pub fn encode(
    model: &[f32],
    seq_flat: &[f32],
    tu: usize,
    din_in: usize,
    start: i64,
    end: i64,
    out_len: usize,
) -> (Vec<f32>, usize) {
    if model.len() < HDR { return (vec![], 0); }
    let din = model[0] as usize;
    let dh = model[1] as usize;
    let bidir = model[2] > 0.5;
    if din == 0 || dh == 0 || din != din_in || tu == 0 {
        return (vec![], 0);
    }
    // unpack
    let mut p = HDR;
    let wf = &model[p..p + din * dh]; p += din * dh;
    let u = &model[p..p + dh * dh]; p += dh * dh;
    let b = &model[p..p + dh]; p += dh;
    let fwd = Rnn { din, dh, wf: wf.to_vec(), u: u.to_vec(), b: b.to_vec(),
                    wp: vec![], c: vec![] };
    let hf = fwd.forward(seq_flat, tu, false);
    let hb = if bidir {
        let wf2 = &model[p..p + din * dh]; p += din * dh;
        let u2 = &model[p..p + dh * dh]; p += dh * dh;
        let b2 = &model[p..p + dh];
        let bw = Rnn { din, dh, wf: wf2.to_vec(), u: u2.to_vec(), b: b2.to_vec(),
                       wp: vec![], c: vec![] };
        Some(bw.forward(seq_flat, tu, true))
    } else { None };
    let rep = if bidir { 2 * dh } else { dh };

    // slice range
    let s = if start < 0 { 0 } else { (start as usize).min(tu.saturating_sub(1)) };
    let e = if end < 0 || end as usize > tu { tu } else { end as usize };
    let e = e.max(s + 1);
    let span = e - s;

    // build the sliced trajectory then resample to out_len
    let mk = |idx: usize| -> Vec<f32> {
        let mut v = vec![0.0f32; rep];
        v[..dh].copy_from_slice(&hf[idx * dh..idx * dh + dh]);
        if let Some(hb) = &hb { v[dh..].copy_from_slice(&hb[idx * dh..idx * dh + dh]); }
        v
    };
    let ol = out_len.max(1);
    let mut out = vec![0.0f32; ol * rep];
    for o in 0..ol {
        // linear index into [s,e)
        let pos = if ol == 1 { s as f32 }
                  else { s as f32 + (span - 1) as f32 * (o as f32) / (ol - 1) as f32 };
        let lo = pos.floor() as usize;
        let hi = (lo + 1).min(e - 1);
        let fr = pos - lo as f32;
        let a = mk(lo);
        let bb = mk(hi);
        for d in 0..rep { out[o * rep + d] = a[d] * (1.0 - fr) + bb[d] * fr; }
    }
    (out, rep)
}
