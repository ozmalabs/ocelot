"""solve_for_n — the GENERAL solve-for-N machine (domain-agnostic analysis-by-synthesis).

THE THESIS (memory: ozma_solve_for_n_is_general_not_speech +
ozma_order_n_analysis_by_synthesis). Perception = INVERTING a forward model. Don't
read a linear transform off the signal; instead HYPOTHESISE params -> SYNTHESISE the
signal the forward model would produce -> MATCH against the input -> REFINE, iterated
("n passes"). The engine is the agent's cognition: a principled owned SEARCH + MATCH +
a weighted-admissibility COLLAPSE. The FORWARD MODEL is a PLUG-IN that carries all the
domain knowledge. Swap the plug-in (damped-sinusoids -> speech source-filter) and the
SAME engine perceives the new domain unchanged.

THE INTERFACE (so speech swaps in). A forward model is any object with:
    fm.synthesise(params)            -> signal (np.ndarray, length T)
    fm.propose(residual, t)          -> iterable of candidate single-component params
                                        (the domain's "what could explain this residual")
    fm.refine(params, signal, t)     -> locally-polished params (the domain's calculus)
    fm.merge(component_param_list)    -> full params dict for synthesise
where `params` for the whole signal is fm.merge([c1, c2, ...]) of K single components.
The engine NEVER inspects the inside of a component — it only synthesises, matches,
and asks the plug-in to propose/refine. That is the clean boundary.

THE ENGINE (owned search + match + collapse — NO net, NO fit, NO gradient-descent
training). solve_for_n is MATCHING PURSUIT to order N + a coordinate refinement:
  1. residual <- input
  2. for pass in 1..N:
       ask the plug-in to PROPOSE candidate single components for the residual
       (it returns several — e.g. peaks of |FFT(residual)|, the over-complete menu);
       for each candidate, REFINE it and SYNTHESISE it; the candidate's admissibility
       is how much of the residual energy it explains (soft excluder, not a dot
       product). COLLAPSE the candidate menu by WEIGHTED ADMISSIBILITY: each candidate
       gets a weight = its above-floor reliability (variance-explained, normalised),
       and we admit the single best-weighted one, SUBTRACT it, recurse on the residual.
  3. a final JOINT refinement pass re-fits every admitted component against the input
     with the others held (back-fitting / order-N co-refinement) until the match-error
     converges. This is the "n passes" — co-refine all components jointly.

The match metric is ||synthesise(params) - input|| (the exact-model fit), NOT a linear
read-off. That is the whole reason it can SUPER-RESOLVE: two close sinusoids that the
FFT merges into one bin are TWO components in the model; analysis-by-synthesis peels
the first, and the residual still carries the second, so the second is recovered where
a peak-pick sees only one bump.

WEIGHTED-ADMISSIBILITY COLLAPSE (the project's combine rule, soft excluders not a dot
product; cf. domains/weighted_admissibility.py). For the menu of candidate components
{c_i} with raw variance-explained v_i, the weight is the above-floor reliability
    weight_i = max(0, (v_i - v_floor) / (1 - v_floor)),  v_floor = median(v) (the
chance/noise floor of the menu), and admissibility(c_i) = v_i ** (1 - weight penalty);
a candidate at the floor gets weight 0 -> admissibility^0 = abstain (cannot win on
noise); a candidate that explains the residual gets full say. We admit argmax_i of the
weighted admissibility. NO free knob fit: the floor is the menu median (derived), the
map is the fixed reliability normalisation.

DONKEY AUDIT. Engine = owned numpy search (matching pursuit + back-fitting) + match
(L2 to the synthesised signal) + weighted-admissibility collapse. NO neural net, NO
.fit(), NO gradient-descent TRAINING. The refinement is a bounded local coordinate
polish (Gauss-Newton / golden-section on a SINGLE component's continuous param against
the EXACT forward model) — that is the analysis-by-synthesis calculus the brain runs,
not weight training. The FORWARD MODEL is an exact owned generative function. The TEST
domain is synthetic with KNOWN ground truth.

PREDICTION (to be killed if false). AbS recovers the K-component params AND
super-resolves (beats FFT on sinusoids closer than 1/T) because it fits the exact
model. If it does NOT recover or does NOT beat the FFT, report it plainly + why.

Run:  python -m scripts.solve_for_n            (full acceptance: a,b,c + verdict)
      python -m scripts.solve_for_n --quick    (small, for a smoke test)
"""
from __future__ import annotations

import sys
import time
import numpy as np


# ===========================================================================
# THE GENERAL ENGINE — domain-agnostic. Knows nothing about sinusoids.
# ===========================================================================

def _match_error(synth: np.ndarray, target: np.ndarray) -> float:
    """L2 match error ||synth - target|| — the exact-model fit (NOT a linear read-off)."""
    return float(np.sqrt(np.sum((synth - target) ** 2)))


def _variance_explained(component_signal: np.ndarray, residual: np.ndarray) -> float:
    """How much of the residual's energy this candidate component explains, in [~0,1].
    = 1 - ||residual - component||^2 / ||residual||^2 (the soft excluder evidence)."""
    denom = float(np.sum(residual ** 2))
    if denom <= 0:
        return 0.0
    return 1.0 - float(np.sum((residual - component_signal) ** 2)) / denom


def _weighted_admissibility_collapse(v: np.ndarray) -> int:
    """COLLAPSE a menu of candidate components by WEIGHTED ADMISSIBILITY (soft
    excluders, NOT a dot product). v = per-candidate variance-explained.

    weight_i = max(0, (v_i - floor) / (1 - floor)),  floor = median(v)  (derived, the
    menu's noise floor). admissibility_i = v_i ** (1 - weight_i*0 ...) — we down-weight
    a floor-level candidate toward abstention: its EFFECTIVE evidence is v_i * weight_i,
    so a candidate at the floor (weight 0) contributes 0 (P^0-style abstain) and cannot
    win on noise; a candidate above the floor keeps its say scaled by reliability.
    Returns the admitted candidate index (argmax of weighted admissibility).
    NO fit: floor is the median, the map is the fixed reliability normalisation."""
    if len(v) == 0:
        return -1
    floor = float(np.median(v))
    denom = max(1e-12, 1.0 - floor)
    weight = np.clip((v - floor) / denom, 0.0, 1.0)
    # effective admissibility: evidence scaled by above-floor reliability. The single
    # strongest candidate always has weight 1 (it is the max), so this never abstains
    # the whole menu; it just refuses to admit a noise-floor candidate over a real one.
    adm = v * weight
    # tie-break degenerate (all equal -> all floor -> weight 0): fall back to raw v.
    if not np.any(adm > 0):
        return int(np.argmax(v))
    return int(np.argmax(adm))


def solve_for_n(forward_model, signal, n=None, t=None, max_n=12,
                stop_var_explained=0.9999, joint_passes=6, verbose=False):
    """THE GENERAL SOLVE-FOR-N MACHINE.

    forward_model : plug-in with .synthesise/.propose/.refine/.merge (see module doc).
    signal        : input np.ndarray to be explained.
    n             : order (number of components) to peel; if None, peel until the
                    residual stops shrinking (energy floor) up to max_n.
    t             : time base (np.ndarray); if None, np.arange(len(signal)).
    Returns dict: params (the merged full params), components (list of single-component
    params), residual, match_error, n_used, passes (the n actual AbS passes run).
    """
    signal = np.asarray(signal, dtype=float)
    if t is None:
        t = np.arange(len(signal), dtype=float)

    components = []           # admitted single-component params
    residual = signal.copy()
    target_n = n if n is not None else max_n
    passes = 0

    # ---- MATCHING-PURSUIT to order N: hypothesise -> synthesise -> match -> collapse.
    for k in range(target_n):
        passes += 1
        res_energy = float(np.sum(residual ** 2))
        if res_energy < 1e-12:
            break

        # HYPOTHESISE: the plug-in proposes candidate single components for the residual
        # (the over-complete menu — e.g. several FFT peaks of the residual).
        candidates = list(forward_model.propose(residual, t))
        if not candidates:
            break

        # For each candidate: REFINE locally, SYNTHESISE, score by variance-explained.
        synths = []
        v = []
        refined = []
        for c in candidates:
            c_ref = forward_model.refine_component(c, residual, t)
            cs = forward_model.synthesise(forward_model.merge([c_ref]))
            refined.append(c_ref)
            synths.append(cs)
            v.append(_variance_explained(cs, residual))
        v = np.asarray(v, dtype=float)

        # COLLAPSE the menu by weighted admissibility -> admit the single best component.
        win = _weighted_admissibility_collapse(v)
        if win < 0 or v[win] <= 0:
            break

        components.append(refined[win])
        residual = residual - synths[win]
        if verbose:
            print(f"  pass {passes}: admitted comp {len(components)}, "
                  f"var_explained={v[win]:.4f}, residual_energy={float(np.sum(residual**2)):.4e}")

        # auto-stop: if n was not fixed and the model now explains ~everything, stop.
        if n is None:
            total_explained = 1.0 - float(np.sum(residual ** 2)) / max(1e-12, float(np.sum(signal ** 2)))
            if total_explained >= stop_var_explained:
                break

    # ---- JOINT BACK-FITTING (the order-N co-refinement / "n passes"): re-fit every
    # admitted component against the input with the OTHERS held, iterate until the
    # match-error converges. This co-refines all components jointly — the structural
    # reason close components separate (peeling one frees the other to be re-fit).
    prev_err = np.inf
    for jp in range(joint_passes):
        passes += 1
        for i in range(len(components)):
            others = forward_model.merge([c for j, c in enumerate(components) if j != i])
            others_sig = forward_model.synthesise(others) if any(j != i for j in range(len(components))) else np.zeros_like(signal)
            target_i = signal - others_sig            # residual with comp i removed
            components[i] = forward_model.refine_component(components[i], target_i, t)
        full = forward_model.synthesise(forward_model.merge(components))
        err = _match_error(full, signal)
        if verbose:
            print(f"  joint pass {jp+1}: match_error={err:.6e}")
        if abs(prev_err - err) < 1e-9 * max(1.0, prev_err):
            break
        prev_err = err

    params = forward_model.merge(components)
    full = forward_model.synthesise(params)
    return {
        "params": params,
        "components": components,
        "residual": signal - full,
        "match_error": _match_error(full, signal),
        "n_used": len(components),
        "passes": passes,
    }


# ===========================================================================
# THE FORWARD MODEL PLUG-IN — sum of K damped sinusoids (EXACT, ground truth known).
# This is the ONLY domain-specific code. Replace this class (e.g. with a speech
# source-filter forward model) and solve_for_n above is unchanged.
#   f(t) = sum_i A_i * exp(-d_i * t) * cos(2*pi*f_i*t + phi_i)
#   single-component param = (A, d, f, phi)
# ===========================================================================

class DampedSinusoidModel:
    """EXACT parametric generator for a sum of damped sinusoids. The clean plug-in
    interface: synthesise / propose / refine_component / merge. Carries ALL the domain
    knowledge (what a component is, how to read a candidate off a residual, how to
    polish it). The engine treats it as a black-box generator."""

    def __init__(self, fs=1.0, n_propose=6):
        self.fs = float(fs)        # sample rate (Hz); t in seconds when fs given
        self.n_propose = n_propose # menu size (over-complete proposals per pass)

    # -- merge / synthesise -------------------------------------------------
    def merge(self, component_list):
        return {"components": list(component_list)}

    def synthesise(self, params, t=None):
        comps = params["components"]
        if t is None:
            # caller should pass t; default to unit-spaced. We store last t on propose.
            t = self._t
        out = np.zeros_like(t, dtype=float)
        for (A, d, f, phi) in comps:
            out = out + A * np.exp(-d * t) * np.cos(2.0 * np.pi * f * t + phi)
        return out

    # bind t so synthesise(merge(...)) works without threading t everywhere
    def synthesise(self, params):  # noqa: F811  (override to use bound t)
        comps = params["components"]
        t = self._t
        out = np.zeros_like(t, dtype=float)
        for (A, d, f, phi) in comps:
            out = out + A * np.exp(-d * t) * np.cos(2.0 * np.pi * f * t + phi)
        return out

    # -- propose (HYPOTHESISE): read candidate single components off the residual ----
    def propose(self, residual, t):
        """Over-complete menu: the top-n_propose FFT peaks of the residual, each turned
        into an initial (A, d, f, phi). The FFT gives a COARSE frequency guess (bin
        resolution 1/T) and an amplitude/phase from the bin; refine_component sharpens
        it against the exact model. This is the domain's 'what could explain this'."""
        self._t = t
        T = len(residual)
        dt = float(t[1] - t[0]) if T > 1 else 1.0 / self.fs
        # zero-padded FFT for a finer initial grid (still bin-limited; refine sharpens).
        nfft = int(2 ** np.ceil(np.log2(max(8, 4 * T))))
        win = np.hanning(T)
        spec = np.fft.rfft(residual * win, n=nfft)
        freqs = np.fft.rfftfreq(nfft, d=dt)
        mag = np.abs(spec)
        # find local maxima of the magnitude spectrum
        peaks = []
        for i in range(1, len(mag) - 1):
            if mag[i] > mag[i - 1] and mag[i] >= mag[i + 1]:
                peaks.append(i)
        if not peaks:
            peaks = [int(np.argmax(mag))]
        peaks.sort(key=lambda i: mag[i], reverse=True)
        peaks = peaks[: self.n_propose]
        # window coherent-gain correction for amplitude init
        wgain = np.sum(win) / T
        cands = []
        for i in peaks:
            f0 = float(freqs[i])
            # amplitude/phase from the bin (rough); /T*2 for one-sided real spectrum
            A0 = float(2.0 * mag[i] / (T * wgain))
            phi0 = float(np.angle(spec[i]))
            cands.append((A0, 0.0, f0, phi0))  # damping init 0; refine will fit it
        return cands

    # -- refine_component (the AbS calculus): polish ONE component vs a target -------
    def refine_component(self, comp, target, t):
        """Local coordinate polish of a single (A,d,f,phi) against `target` using the
        EXACT model — bounded analysis-by-synthesis, NOT weight training. We:
          1. golden-section search f in a +/- 1.5 bin window (the super-resolution step:
             continuous frequency, not the FFT grid),
          2. for the best f, solve A*cos+B*sin (and damping d by a small 1-D search)
             in CLOSED FORM (linear least squares against the exact basis).
        Returns the refined (A, d, f, phi)."""
        self._t = t
        A0, d0, f0, phi0 = comp
        T = len(target)
        dt = float(t[1] - t[0]) if T > 1 else 1.0 / self.fs
        bin_hz = 1.0 / (T * dt)

        def fit_at(f, d):
            # closed-form least squares of target ~ exp(-d t)[a cos + b sin]
            env = np.exp(-d * t)
            c = env * np.cos(2.0 * np.pi * f * t)
            s = env * np.sin(2.0 * np.pi * f * t)
            M = np.stack([c, s], axis=1)
            coef, *_ = np.linalg.lstsq(M, target, rcond=None)
            a, b = coef
            recon = M @ coef
            err = float(np.sum((target - recon) ** 2))
            A = float(np.hypot(a, b))
            phi = float(np.arctan2(-b, a))
            return err, A, d, f, phi

        def err_of_f(f):
            best = np.inf
            for d in self._damp_grid(d0, t):
                e, *_ = fit_at(f, d)
                if e < best:
                    best = e
            return best

        # golden-section on frequency in +/- 1.5 bins around f0 (continuous f).
        lo, hi = max(0.0, f0 - 1.5 * bin_hz), f0 + 1.5 * bin_hz
        gr = (np.sqrt(5) - 1) / 2
        a, b = lo, hi
        c = b - gr * (b - a)
        d = a + gr * (b - a)
        fc, fd = err_of_f(c), err_of_f(d)
        for _ in range(40):
            if fc < fd:
                b, d, fd = d, c, fc
                c = b - gr * (b - a)
                fc = err_of_f(c)
            else:
                a, c, fc = c, d, fd
                d = a + gr * (b - a)
                fd = err_of_f(d)
            if abs(b - a) < 1e-9 * bin_hz:
                break
        f_best = (a + b) / 2.0
        # refine damping at f_best, then closed-form A,phi
        best = (np.inf, A0, d0, f_best, phi0)
        for dd in self._damp_grid(d0, t, fine=True):
            cand = fit_at(f_best, dd)
            if cand[0] < best[0]:
                best = cand
        _, A, d_out, f_out, phi = best
        return (A, d_out, f_out, phi)

    def _damp_grid(self, d0, t, fine=False):
        # damping search range scaled to the observation length (1/T .. several/T).
        T_total = float(t[-1] - t[0]) if len(t) > 1 else 1.0
        base = 1.0 / max(1e-9, T_total)
        if fine:
            return np.concatenate([[0.0], np.linspace(0.0, 8 * base, 33)])
        return np.concatenate([[0.0], np.linspace(0.0, 8 * base, 9)])


# ===========================================================================
# BASELINE — plain FFT peak-pick (the linear read-off solve-for-n must beat).
# ===========================================================================

def fft_peak_pick(signal, t, k, fs=1.0):
    """Plain FFT + top-k magnitude peak frequencies. The linear-transform read-off
    (no model inversion). Returns a list of (A, f) — the standard spectral estimate.
    Cannot resolve two sinusoids inside one FFT bin (1/T)."""
    T = len(signal)
    dt = float(t[1] - t[0]) if T > 1 else 1.0 / fs
    win = np.hanning(T)
    nfft = int(2 ** np.ceil(np.log2(max(8, 4 * T))))
    spec = np.abs(np.fft.rfft(signal * win, n=nfft))
    freqs = np.fft.rfftfreq(nfft, d=dt)
    wgain = np.sum(win) / T
    peaks = []
    for i in range(1, len(spec) - 1):
        if spec[i] > spec[i - 1] and spec[i] >= spec[i + 1]:
            peaks.append(i)
    if not peaks:
        peaks = [int(np.argmax(spec))]
    peaks.sort(key=lambda i: spec[i], reverse=True)
    out = []
    for i in peaks[:k]:
        out.append((float(2.0 * spec[i] / (T * wgain)), float(freqs[i])))
    return out


# ===========================================================================
# TEST HARNESS — synthetic, ground truth KNOWN. Real numbers.
# ===========================================================================

def _make_signal(t, comps, snr_db=None, rng=None):
    """Synthesise sum of damped sinusoids with KNOWN comps; optionally add noise."""
    sig = np.zeros_like(t)
    for (A, d, f, phi) in comps:
        sig = sig + A * np.exp(-d * t) * np.cos(2.0 * np.pi * f * t + phi)
    if snr_db is not None:
        sig_pow = float(np.mean(sig ** 2))
        noise_pow = sig_pow / (10 ** (snr_db / 10.0))
        rng = rng or np.random.default_rng(0)
        sig = sig + rng.normal(0, np.sqrt(noise_pow), size=len(t))
    return sig


def _match_components(true_comps, est_comps):
    """Greedy match estimated->true by frequency, return per-pair (true, est)."""
    true = list(true_comps)
    est = list(est_comps)
    pairs = []
    used = set()
    for (At, dt_, ft, pt) in true:
        best_j, best_df = None, np.inf
        for j, (Ae, de, fe, pe) in enumerate(est):
            if j in used:
                continue
            if abs(fe - ft) < best_df:
                best_df, best_j = abs(fe - ft), j
        if best_j is not None:
            used.add(best_j)
            pairs.append(((At, dt_, ft, pt), est[best_j]))
        else:
            pairs.append(((At, dt_, ft, pt), None))
    return pairs


# --------------------------- (a) RECOVERY ----------------------------------
def test_recovery(n_trials=200, fs=1000.0, T_samples=256, seed=1):
    rng = np.random.default_rng(seed)
    dt = 1.0 / fs
    t = np.arange(T_samples) * dt
    nyq = fs / 2.0
    bin_hz = 1.0 / (T_samples * dt)
    freq_errs, amp_errs, n_hits, npass = [], [], [], []
    for _ in range(n_trials):
        K = int(rng.integers(1, 4))  # 1..3 components
        comps = []
        fs_used = []
        for _k in range(K):
            # keep components separated by > 3 bins so recovery (not super-res) is fair
            for _try in range(50):
                f = float(rng.uniform(0.05 * nyq, 0.45 * nyq))
                if all(abs(f - fo) > 3 * bin_hz for fo in fs_used):
                    break
            fs_used.append(f)
            A = float(rng.uniform(0.5, 2.0))
            d = float(rng.uniform(0.0, 3.0 / (T_samples * dt)))  # mild damping
            phi = float(rng.uniform(-np.pi, np.pi))
            comps.append((A, d, f, phi))
        sig = _make_signal(t, comps)
        fm = DampedSinusoidModel(fs=fs)
        res = solve_for_n(fm, sig, n=K, t=t)
        npass.append(res["passes"])
        pairs = _match_components(comps, res["components"])
        hit = 0
        for (tr, es) in pairs:
            if es is None:
                continue
            df = abs(es[2] - tr[2])
            if df < 0.5 * bin_hz:           # recovered within half a bin
                hit += 1
            freq_errs.append(df / bin_hz)   # error in BINS
            amp_errs.append(abs(es[0] - tr[0]) / max(1e-9, tr[0]))
        n_hits.append(hit / K)
    return {
        "n_trials": n_trials,
        "median_freq_err_bins": float(np.median(freq_errs)),
        "mean_freq_err_bins": float(np.mean(freq_errs)),
        "p95_freq_err_bins": float(np.percentile(freq_errs, 95)),
        "median_amp_relerr": float(np.median(amp_errs)),
        "mean_amp_relerr": float(np.mean(amp_errs)),
        "recovery_rate": float(np.mean(n_hits)),  # frac of components recovered <0.5 bin
        "mean_passes": float(np.mean(npass)),
        "bin_hz": bin_hz,
    }


# --------------------- (b) SUPER-RESOLUTION --------------------------------
def test_super_resolution(spacings_bins=None, n_trials=60, fs=1000.0,
                          T_samples=256, snr_db=20.0, seed=2):
    """Two equal sinusoids spaced `spacing` apart (in FFT bins, bin = 1/T). Success =
    BOTH frequencies recovered within 0.5 bin AND resolved as two distinct components.
    Report success-rate vs spacing for solve-for-n vs FFT peak-pick, and the min
    resolvable spacing (success >= 0.8) for each."""
    rng = np.random.default_rng(seed)
    dt = 1.0 / fs
    t = np.arange(T_samples) * dt
    bin_hz = 1.0 / (T_samples * dt)
    nyq = fs / 2.0
    if spacings_bins is None:
        spacings_bins = [0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0]
    rows = []
    for sp in spacings_bins:
        df = sp * bin_hz
        abs_hits, fft_hits = 0, 0
        for _ in range(n_trials):
            f1 = float(rng.uniform(0.2 * nyq, 0.4 * nyq))
            f2 = f1 + df
            phi1 = float(rng.uniform(-np.pi, np.pi))
            phi2 = float(rng.uniform(-np.pi, np.pi))
            comps = [(1.0, 0.0, f1, phi1), (1.0, 0.0, f2, phi2)]
            sig = _make_signal(t, comps, snr_db=snr_db, rng=rng)

            # solve-for-n with n=2 (we ask: can two be separated?)
            fm = DampedSinusoidModel(fs=fs, n_propose=8)
            res = solve_for_n(fm, sig, n=2, t=t)
            est_f = sorted(c[2] for c in res["components"])
            ok = (len(est_f) == 2 and
                  min(abs(est_f[0] - f1), abs(est_f[0] - f2)) < 0.5 * bin_hz and
                  min(abs(est_f[1] - f1), abs(est_f[1] - f2)) < 0.5 * bin_hz and
                  abs(est_f[0] - est_f[1]) > 0.25 * bin_hz)
            if ok:
                abs_hits += 1

            # FFT peak-pick asking for 2 peaks
            fft_est = fft_peak_pick(sig, t, k=2, fs=fs)
            fft_f = sorted(f for _A, f in fft_est)
            fok = (len(fft_f) == 2 and
                   min(abs(fft_f[0] - f1), abs(fft_f[0] - f2)) < 0.5 * bin_hz and
                   min(abs(fft_f[1] - f1), abs(fft_f[1] - f2)) < 0.5 * bin_hz and
                   abs(fft_f[0] - fft_f[1]) > 0.25 * bin_hz)
            if fok:
                fft_hits += 1
        rows.append({
            "spacing_bins": sp,
            "spacing_hz": df,
            "abs_success": abs_hits / n_trials,
            "fft_success": fft_hits / n_trials,
        })

    def min_resolvable(key, thresh=0.8):
        ok_sp = [r["spacing_bins"] for r in rows if r[key] >= thresh]
        return min(ok_sp) if ok_sp else None

    return {
        "bin_hz": bin_hz,
        "snr_db": snr_db,
        "rows": rows,
        "abs_min_resolvable_bins": min_resolvable("abs_success"),
        "fft_min_resolvable_bins": min_resolvable("fft_success"),
    }


# --------------------------- (c) NOISE -------------------------------------
def test_noise(snrs_db=None, n_trials=80, fs=1000.0, T_samples=256, seed=3):
    """Recovery success vs SNR. Two well-separated (3-bin) sinusoids; success = both
    freqs within 0.5 bin."""
    rng = np.random.default_rng(seed)
    dt = 1.0 / fs
    t = np.arange(T_samples) * dt
    bin_hz = 1.0 / (T_samples * dt)
    nyq = fs / 2.0
    if snrs_db is None:
        snrs_db = [20, 15, 10, 5, 0, -5]
    rows = []
    for snr in snrs_db:
        hits, ferrs = 0, []
        for _ in range(n_trials):
            f1 = float(rng.uniform(0.15 * nyq, 0.30 * nyq))
            f2 = f1 + 4 * bin_hz
            comps = [(1.0, 0.0, f1, float(rng.uniform(-np.pi, np.pi))),
                     (1.0, 0.0, f2, float(rng.uniform(-np.pi, np.pi)))]
            sig = _make_signal(t, comps, snr_db=snr, rng=rng)
            fm = DampedSinusoidModel(fs=fs)
            res = solve_for_n(fm, sig, n=2, t=t)
            est_f = sorted(c[2] for c in res["components"])
            if len(est_f) == 2:
                e1 = min(abs(est_f[0] - f1), abs(est_f[0] - f2))
                e2 = min(abs(est_f[1] - f1), abs(est_f[1] - f2))
                ferrs.append((e1 + e2) / 2 / bin_hz)
                if e1 < 0.5 * bin_hz and e2 < 0.5 * bin_hz:
                    hits += 1
        rows.append({
            "snr_db": snr,
            "success": hits / n_trials,
            "median_freq_err_bins": float(np.median(ferrs)) if ferrs else None,
        })
    return rows


# ===========================================================================
# RUN
# ===========================================================================

def main():
    quick = "--quick" in sys.argv
    t0 = time.time()
    print("=" * 74)
    print("solve_for_n — GENERAL solve-for-N machine (domain-agnostic AbS)")
    print("forward-model plug-in: DampedSinusoidModel (EXACT, ground truth known)")
    print("=" * 74)

    if quick:
        rec = test_recovery(n_trials=20)
        sr = test_super_resolution(spacings_bins=[0.3, 0.5, 1.0], n_trials=15)
        noise = test_noise(snrs_db=[20, 5, -5], n_trials=15)
    else:
        rec = test_recovery(n_trials=200)
        sr = test_super_resolution(
            spacings_bins=[0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0, 1.25, 1.5, 2.0],
            n_trials=60)
        noise = test_noise(n_trials=80)

    print("\n(a) RECOVERY  (K=1..3 damped sinusoids, components > 3 bins apart)")
    print(f"    trials={rec['n_trials']}  bin(1/T)={rec['bin_hz']:.3f} Hz")
    print(f"    freq err (bins): median={rec['median_freq_err_bins']:.4f} "
          f"mean={rec['mean_freq_err_bins']:.4f} p95={rec['p95_freq_err_bins']:.4f}")
    print(f"    amp rel err: median={rec['median_amp_relerr']:.4f} mean={rec['mean_amp_relerr']:.4f}")
    print(f"    recovery rate (<0.5 bin): {rec['recovery_rate']*100:.1f}%")
    print(f"    mean AbS passes (n): {rec['mean_passes']:.1f}")

    print("\n(b) SUPER-RESOLUTION  (two sinusoids, snr={:.0f} dB; success>=0.8 = resolvable)".format(sr["snr_db"]))
    print(f"    bin(1/T)={sr['bin_hz']:.3f} Hz")
    print(f"    {'spacing(bins)':>13} {'spacing(Hz)':>11} {'solve-for-n':>12} {'FFT':>8}")
    for r in sr["rows"]:
        print(f"    {r['spacing_bins']:>13.2f} {r['spacing_hz']:>11.3f} "
              f"{r['abs_success']*100:>11.1f}% {r['fft_success']*100:>7.1f}%")
    print(f"    MIN RESOLVABLE spacing  solve-for-n: {sr['abs_min_resolvable_bins']} bins   "
          f"FFT: {sr['fft_min_resolvable_bins']} bins")

    print("\n(c) NOISE  (two sinusoids 4 bins apart; success = both within 0.5 bin)")
    print(f"    {'SNR(dB)':>8} {'success':>9} {'med freq err(bins)':>20}")
    for r in noise:
        me = f"{r['median_freq_err_bins']:.4f}" if r['median_freq_err_bins'] is not None else "n/a"
        print(f"    {r['snr_db']:>8} {r['success']*100:>8.1f}% {me:>20}")

    # ---- VERDICT
    print("\n" + "=" * 74)
    recovers = rec["recovery_rate"] >= 0.9 and rec["median_freq_err_bins"] < 0.1
    abs_min = sr["abs_min_resolvable_bins"]
    fft_min = sr["fft_min_resolvable_bins"]
    beats_fft = (abs_min is not None and (fft_min is None or abs_min < fft_min))
    print("VERDICT")
    print(f"  recovers structure : {'YES' if recovers else 'NO'} "
          f"(recovery {rec['recovery_rate']*100:.1f}%, median freq err {rec['median_freq_err_bins']:.4f} bins)")
    print(f"  super-resolves     : {'YES' if beats_fft else 'NO'} "
          f"(solve-for-n down to {abs_min} bins vs FFT {fft_min} bins)")
    if recovers and beats_fft:
        print("  => the GENERAL solve-for-n machine RECOVERS structure AND super-resolves.")
        print("     The mechanism is proven domain-agnostically (forward model is a plug-in).")
    else:
        print("  => HONEST KILL: see numbers above for which test failed and why.")
    print(f"\nelapsed {time.time()-t0:.1f}s")
    print("SOLVE_FOR_N_COMPLETED")


if __name__ == "__main__":
    main()
