"""solve_for_n_ladder — probe the GENERAL solve-for-N engine on three qualitatively-
harder well-understood domains by swapping ONLY the forward-model plug-in.

THE ENGINE IS REUSED UNCHANGED (scripts.solve_for_n.solve_for_n). We write only the
new forward-model PLUG-INS (synthesise / propose / refine_component / merge) and the
ground-truth test harnesses. Each domain has an EXACT owned generative function and
KNOWN ground truth, so every break is DIAGNOSABLE (memory: ozma_diagnostic_ladder_method).

The three rungs (skipping the lower ones — sinusoids already PASSED, commit 6af64af7):

  1. NON-LINEAR PHYSICS — a 2-body Kepler orbit (continuous params, non-linear dynamics).
     The "signal" is the observed trajectory r(t)=(x,y). params = (a, e, theta0, t_peri,
     ... ) the orbital elements. The engine must recover them from the trajectory. This
     is a SINGLE non-linear component (n=1) — tests whether the continuous golden-section
     /LSQ refinement survives a non-linear, local-minima landscape. PREDICTION: clears,
     with possible local minima (eccentric-anomaly wrap, periapsis ambiguity).

  2. DISCRETE / SYMBOLIC — an elementary cellular automaton (Wolfram). The signal is the
     evolved space-time pattern; params = (rule in 0..255, initial condition bits). NO
     smooth gradient — the continuous refine_component is a NO-OP here. This is the rung
     the engine is NOT built for: it tests whether analysis-by-synthesis degrades
     gracefully or proposes garbage. PREDICTION: BREAKS — continuous refinement is a
     no-op; matching-pursuit over a continuous menu cannot search a discrete rule space.
     We note the EXACT break and, because it is cheap, add a minimal discrete-search
     refine (the minimal interface extension the lack demands) to show what WOULD fix it.

  3. COMPOSITIONAL — notes-in-a-melody: each note is a sinusoid BURST (a gated tone)
     placed on a rhythm grid. params = the NESTED structure (which notes, at which onset,
     which pitch, which duration). The engine peels components (matching pursuit) but the
     question is whether it recovers the NESTED structure or just an unstructured bag of
     partials. This is the speech-relevant rung. PREDICTION: peels the loud/long notes
     but (a) a windowed burst is NOT a single global sinusoid so each note costs several
     components, and (b) the engine has no grouping operator — it returns a flat bag, not
     the note hierarchy. The break is the missing COMPOSE/GROUP step.

DONKEY AUDIT. Forward models below = owned EXACT generative numpy functions (Kepler
solve via Newton on the eccentric anomaly; ECA rule table; gated-sinusoid synthesis).
Engine = the existing general one, imported UNCHANGED. Ground truth is constructed, so
recovery error is exact. NO net, NO .fit(), NO gradient-descent TRAINING. The only
refinement is bounded local coordinate polish against the exact forward model (and, for
the discrete rung, an explicit small discrete search — flagged as the interface gap).

Run:  python -m scripts.solve_for_n_ladder
"""
from __future__ import annotations

import sys
import time
import numpy as np

from scripts.solve_for_n import solve_for_n  # THE ENGINE, UNCHANGED.


# ===========================================================================
# RUNG 1 — NON-LINEAR PHYSICS: 2-body Kepler orbit (single non-linear component)
# ===========================================================================
#
# A test particle orbits a fixed mass mu at the focus. The bound orbit is an ellipse;
# the position vs time is the EXACT forward model (Kepler's equation, solved by Newton).
# This is non-linear in the orbital elements (eccentric anomaly E couples to e, the
# orbit orientation rotates the ellipse). The observed "signal" is the flattened
# trajectory [x(t_0..t_{N-1}), y(t_0..t_{N-1})]. n=1 (one orbit).
#
# Orbital element param (single component):
#   (a, e, omega, M0, n_mean)
#     a      = semi-major axis
#     e      = eccentricity (0..~0.9)
#     omega  = argument of periapsis (orbit rotation in the plane)
#     M0     = mean anomaly at t=0
#     n_mean = mean motion (rad/time) = sqrt(mu / a^3)  (kept as a free param so the
#              engine can recover the period directly from the trajectory)

def _kepler_E(M, e, iters=60):
    """Solve Kepler's equation M = E - e sin E for the eccentric anomaly E by Newton.
    Vectorised over M. EXACT to machine precision for e < 1."""
    M = np.mod(M + np.pi, 2 * np.pi) - np.pi
    E = M + e * np.sin(M)  # good initial guess
    for _ in range(iters):
        dE = (E - e * np.sin(E) - M) / (1 - e * np.cos(E))
        E = E - dE
        if np.max(np.abs(dE)) < 1e-14:
            break
    return E


class KeplerOrbitModel:
    """EXACT 2-body orbit forward model as a solve-for-n plug-in. ONE component = one
    orbit (the engine runs at n=1). Carries all the domain knowledge: how to synthesise
    a trajectory from orbital elements, a coarse proposal from the raw trajectory
    geometry, and a bounded local polish of the elements against the exact model."""

    def __init__(self, t):
        self._t = np.asarray(t, dtype=float)

    def merge(self, component_list):
        return {"components": list(component_list)}

    def _orbit_xy(self, comp):
        a, e, omega, M0, n_mean = comp
        t = self._t
        M = M0 + n_mean * t
        E = _kepler_E(M, e)
        # position in the orbital plane (periapsis along +x of the un-rotated frame)
        xp = a * (np.cos(E) - e)
        yp = a * np.sqrt(max(0.0, 1 - e * e)) * np.sin(E)
        # rotate by omega
        co, so = np.cos(omega), np.sin(omega)
        x = co * xp - so * yp
        y = so * xp + co * yp
        return x, y

    def synthesise(self, params):
        # the engine sums components; for orbits there is exactly one, but we support the
        # general additive contract (a second orbit would superpose, which is unphysical
        # but the engine never proposes one because n=1).
        t = self._t
        x = np.zeros_like(t)
        y = np.zeros_like(t)
        for comp in params["components"]:
            cx, cy = self._orbit_xy(comp)
            x = x + cx
            y = y + cy
        return np.concatenate([x, y])

    def propose(self, residual, t):
        """Coarse element guess from the raw trajectory geometry (no fitting yet).
        residual is the flattened [x;y] (on the first pass it IS the observed orbit).
        We read: centre & size of the point cloud -> a, e; orientation -> omega; the
        angular sweep -> n_mean; the starting angle -> M0. Bin-coarse; refine sharpens."""
        self._t = np.asarray(t, dtype=float)  # keep length-N time base (not the 2N axis)
        N = len(residual) // 2
        x = residual[:N]
        y = residual[N:]
        # principal axes of the cloud -> ellipse orientation & semi-axes
        cx, cy = np.mean(x), np.mean(y)
        X = np.stack([x - cx, y - cy], axis=1)
        cov = X.T @ X / max(1, N)
        evals, evecs = np.linalg.eigh(cov)
        # major axis = larger eigenvector
        major = evecs[:, int(np.argmax(evals))]
        omega0 = float(np.arctan2(major[1], major[0]))
        # rough semi-axes from spread; a from the major extent
        ext = X @ evecs
        amaj = (np.max(ext[:, int(np.argmax(evals))]) - np.min(ext[:, int(np.argmax(evals))])) / 2
        amin = (np.max(ext[:, int(np.argmin(evals))]) - np.min(ext[:, int(np.argmin(evals))])) / 2
        a0 = float(max(amaj, 1e-6))
        e0 = float(np.clip(np.sqrt(max(0.0, 1 - (amin / max(amaj, 1e-9)) ** 2)), 0.0, 0.9))
        # mean motion from the total angular sweep about the centre
        ang = np.unwrap(np.arctan2(y - cy, x - cx))
        T_span = float(self._t[-1] - self._t[0]) if N > 1 else 1.0
        n0 = float((ang[-1] - ang[0]) / max(1e-9, T_span))
        if abs(n0) < 1e-6:
            n0 = 2 * np.pi / max(1e-9, T_span)
        M00 = float(ang[0] - omega0)
        # over-complete menu: a few periapsis/orientation hypotheses (the non-linear
        # landscape has periapsis ambiguity; give the search several starts).
        cands = []
        for dom in (0.0, np.pi):
            for de in (0.0, 0.15):
                cands.append((a0, float(np.clip(e0 + de, 0.0, 0.9)),
                              omega0 + dom, M00, n0))
        return cands

    def refine_component(self, comp, target, t):
        """Bounded local polish of the 5 orbital elements against the EXACT model via
        coordinate descent + golden-section on each element (analysis-by-synthesis
        calculus — NOT weight training). target is the flattened [x;y] to match."""
        self._t = np.asarray(t, dtype=float)
        comp = list(comp)

        def err(c):
            s = self.synthesise(self.merge([tuple(c)]))
            return float(np.sum((s - target) ** 2))

        # per-element search half-widths (scaled to the element)
        a, e, omega, M0, n_mean = comp
        spans = [0.5 * max(abs(a), 1e-3), 0.4, np.pi, np.pi, 0.5 * max(abs(n_mean), 1e-3)]
        bounds = [(1e-6, None), (0.0, 0.95), (None, None), (None, None), (None, None)]
        gr = (np.sqrt(5) - 1) / 2
        for _sweep in range(6):
            for idx in range(5):
                base = list(comp)
                center = comp[idx]
                lo = center - spans[idx]
                hi = center + spans[idx]
                blo, bhi = bounds[idx]
                if blo is not None:
                    lo = max(lo, blo)
                if bhi is not None:
                    hi = min(hi, bhi)
                aa, bb = lo, hi
                cc = bb - gr * (bb - aa)
                dd = aa + gr * (bb - aa)

                def ev(val):
                    c2 = list(base)
                    c2[idx] = val
                    return err(c2)

                fc, fd = ev(cc), ev(dd)
                for _ in range(30):
                    if fc < fd:
                        bb, dd, fd = dd, cc, fc
                        cc = bb - gr * (bb - aa)
                        fc = ev(cc)
                    else:
                        aa, cc, fc = cc, dd, fd
                        dd = aa + gr * (bb - aa)
                        fd = ev(dd)
                    if abs(bb - aa) < 1e-10 * (abs(spans[idx]) + 1e-9):
                        break
                comp[idx] = (aa + bb) / 2.0
                spans[idx] *= 0.5  # shrink the search window each sweep
        return tuple(comp)


def test_physics(n_trials=30, N=120, seed=11):
    rng = np.random.default_rng(seed)
    t = np.linspace(0.0, 1.0, N)
    a_errs, e_errs, n_errs, traj_rmse, recov = [], [], [], [], 0
    for _ in range(n_trials):
        a = float(rng.uniform(1.0, 3.0))
        e = float(rng.uniform(0.0, 0.7))
        omega = float(rng.uniform(-np.pi, np.pi))
        M0 = float(rng.uniform(-np.pi, np.pi))
        # cover ~1 to 2 orbital periods across the window
        periods = float(rng.uniform(1.0, 2.0))
        n_mean = 2 * np.pi * periods / (t[-1] - t[0])
        true = (a, e, omega, M0, n_mean)
        fm = KeplerOrbitModel(t)
        signal = fm.synthesise(fm.merge([true]))
        res = solve_for_n(fm, signal, n=1, t=t)
        est = res["components"][0]
        ea, ee, eo, eM, en = est
        a_errs.append(abs(ea - a) / a)
        e_errs.append(abs(ee - e))
        n_errs.append(abs(en - n_mean) / n_mean)
        traj_rmse.append(res["match_error"] / np.sqrt(len(signal)))
        # recovered = trajectory matched AND elements close
        if (abs(ea - a) / a < 0.02 and abs(ee - e) < 0.02 and abs(en - n_mean) / n_mean < 0.02):
            recov += 1
    return {
        "n_trials": n_trials,
        "recovery_rate": recov / n_trials,
        "median_a_relerr": float(np.median(a_errs)),
        "median_e_abserr": float(np.median(e_errs)),
        "median_n_relerr": float(np.median(n_errs)),
        "median_traj_rmse": float(np.median(traj_rmse)),
        "p95_a_relerr": float(np.percentile(a_errs, 95)),
        "p95_traj_rmse": float(np.percentile(traj_rmse, 95)),
    }


# ===========================================================================
# RUNG 2 — DISCRETE / SYMBOLIC: elementary cellular automaton (no smooth gradient)
# ===========================================================================
#
# An ECA: width-W ring, T_steps rows, rule in 0..255, given initial row of bits. The
# forward model is EXACT. params (single "component") = (rule, init_bits_tuple). The
# observed "signal" is the flattened space-time pattern (T_steps*W floats in {0,1}).
#
# The engine's continuous refine_component is a NO-OP on a discrete space (golden-section
# on an integer rule index is meaningless). This rung tests graceful degradation. We give
# TWO plug-ins:
#   (a) ECAModelContinuous — honours the engine's continuous contract literally (refine is
#       a no-op clamp). This SHOWS the break: the engine cannot search the rule space.
#   (b) ECAModelDiscrete  — the MINIMAL interface extension the lack demands: refine_
#       component does an explicit small DISCRETE search (try all 256 rules at the current
#       init; flip the init bits that reduce error). This is NOT continuous calculus; it
#       is the discrete analogue. We report it as the interface gap + its fix.

def _eca_step(row, rule):
    W = len(row)
    left = np.roll(row, 1)
    right = np.roll(row, -1)
    idx = (left << 2) | (row << 1) | right  # 0..7 neighbourhood
    out = (rule >> idx) & 1
    return out.astype(np.int64)


def _eca_evolve(rule, init_bits, T_steps):
    W = len(init_bits)
    rows = np.zeros((T_steps, W), dtype=np.int64)
    rows[0] = np.asarray(init_bits, dtype=np.int64)
    for r in range(1, T_steps):
        rows[r] = _eca_step(rows[r - 1], rule)
    return rows


class ECAModelContinuous:
    """ECA forward model honouring the engine's CONTINUOUS contract literally — to expose
    the break. refine_component is a no-op (there is no continuous gradient on a rule
    index / bit), propose returns one coarse guess. The engine will run but cannot search
    the discrete space; whatever propose returns is what you get."""

    def __init__(self, T_steps, W):
        self.T_steps = T_steps
        self.W = W

    def merge(self, component_list):
        # only the FIRST component is meaningful (an ECA pattern is one rule+init)
        return {"components": list(component_list)[:1]}

    def synthesise(self, params):
        comps = params["components"]
        if not comps:
            return np.zeros(self.T_steps * self.W)
        rule, init_bits = comps[0]
        rows = _eca_evolve(int(rule) & 255, init_bits, self.T_steps)
        return rows.reshape(-1).astype(float)

    def propose(self, residual, t):
        # the discrete analogue of "read a candidate off the residual": the first row of
        # the residual pattern IS the init (visible), but the RULE is hidden -> we cannot
        # read it off. We guess rule=0 (the continuous machine has no way to find it).
        pat = np.round(residual).astype(np.int64).reshape(self.T_steps, self.W)
        init = tuple(int(b) for b in pat[0])
        return [(0, init)]  # rule 0: the engine has no continuous handle to fix this

    def refine_component(self, comp, target, t):
        # NO-OP: golden-section / LSQ cannot polish an integer rule. This is the break.
        return comp


class ECAModelDiscrete:
    """ECA forward model with the MINIMAL interface extension the discrete rung demands:
    refine_component does an explicit DISCRETE search (exhaustive over 256 rules at the
    current init; greedy bit-flips on the init). Same synthesise/merge/propose contract;
    only the calculus is discrete. This is the cheap extension flagged in the report."""

    def __init__(self, T_steps, W):
        self.T_steps = T_steps
        self.W = W

    def merge(self, component_list):
        return {"components": list(component_list)[:1]}

    def synthesise(self, params):
        comps = params["components"]
        if not comps:
            return np.zeros(self.T_steps * self.W)
        rule, init_bits = comps[0]
        rows = _eca_evolve(int(rule) & 255, init_bits, self.T_steps)
        return rows.reshape(-1).astype(float)

    def propose(self, residual, t):
        pat = np.round(residual).astype(np.int64).reshape(self.T_steps, self.W)
        # the first row is directly observed (it's the init); rule unknown -> placeholder.
        init = tuple(int(b) for b in pat[0])
        return [(0, init)]

    def _err(self, comp, target):
        s = self.synthesise(self.merge([comp]))
        return float(np.sum((s - target) ** 2))

    def refine_component(self, comp, target, t):
        # DISCRETE search (the analogue of the continuous polish):
        #   1. fix init = observed first row; exhaustively pick the rule (256 options).
        #   2. greedy bit-flips on the init to reduce remaining error (handles a noisy or
        #      ambiguous first row), re-selecting the rule after each flip.
        pat = np.round(target).astype(np.int64).reshape(self.T_steps, self.W)
        init = list(int(b) for b in pat[0])

        def best_rule(init_bits):
            best_r, best_e = 0, np.inf
            for r in range(256):
                e = self._err((r, tuple(init_bits)), target)
                if e < best_e:
                    best_e, best_r = e, r
            return best_r, best_e

        rule, err = best_rule(init)
        # greedy init bit-flips (only helps if the first row is corrupted; on clean data
        # the exhaustive rule pick already nails it at err 0 and this loop is a no-op).
        improved = True
        while improved and err > 0:
            improved = False
            for i in range(len(init)):
                init[i] ^= 1
                r2, e2 = best_rule(init)
                if e2 < err:
                    err, rule = e2, r2
                    improved = True
                else:
                    init[i] ^= 1  # revert
        return (rule, tuple(init))


def test_discrete(n_trials=40, T_steps=24, W=21, seed=23):
    rng = np.random.default_rng(seed)
    res_cont = {"recovered": 0, "rule_hits": 0}
    res_disc = {"recovered": 0, "rule_hits": 0}
    for _ in range(n_trials):
        rule = int(rng.integers(0, 256))
        init = tuple(int(b) for b in rng.integers(0, 2, size=W))
        true_pat = _eca_evolve(rule, init, T_steps).reshape(-1).astype(float)

        # (a) continuous machine (expected break)
        fmc = ECAModelContinuous(T_steps, W)
        rc = solve_for_n(fmc, true_pat, n=1, t=np.arange(len(true_pat), dtype=float))
        ec = rc["components"][0] if rc["components"] else (None, None)
        if ec[0] is not None:
            if int(ec[0]) == rule:
                res_cont["rule_hits"] += 1
            if rc["match_error"] < 1e-9:
                res_cont["recovered"] += 1

        # (b) discrete-extended machine (the cheap fix)
        fmd = ECAModelDiscrete(T_steps, W)
        rd = solve_for_n(fmd, true_pat, n=1, t=np.arange(len(true_pat), dtype=float))
        ed = rd["components"][0] if rd["components"] else (None, None)
        if ed[0] is not None:
            if int(ed[0]) == rule:
                res_disc["rule_hits"] += 1
            if rd["match_error"] < 1e-9:
                res_disc["recovered"] += 1
    return {
        "n_trials": n_trials,
        "continuous": {
            "rule_recovery_rate": res_cont["rule_hits"] / n_trials,
            "pattern_recovery_rate": res_cont["recovered"] / n_trials,
        },
        "discrete_extension": {
            "rule_recovery_rate": res_disc["rule_hits"] / n_trials,
            "pattern_recovery_rate": res_disc["recovered"] / n_trials,
        },
    }


# ===========================================================================
# RUNG 3 — COMPOSITIONAL: notes-in-a-melody (nested hierarchy, the speech-relevant rung)
# ===========================================================================
#
# A melody = K notes. Each note is a sinusoid BURST: a single pitch f, gated by a smooth
# (raised-cosine) window of duration dur starting at onset on0. The forward model is
# EXACT. The NESTED structure is (note -> onset, pitch, duration, amplitude); the engine
# must recover not just the partials but the GROUPING into notes.
#
# We give the engine a burst-component plug-in: a single component IS a gated tone
# (A, f, onset, dur). propose reads candidate (onset, pitch) from a crude spectrogram
# peak; refine polishes f and the gate timing against the exact model. The crux test: the
# engine peels components by ENERGY (matching pursuit) — does the flat bag it returns
# correspond to the note hierarchy, or does it shatter notes / merge them?

def _raised_cos_gate(t, onset, dur, ramp_frac=0.15):
    """Smooth on/off gate (raised-cosine ramps) of duration dur starting at onset."""
    g = np.zeros_like(t)
    end = onset + dur
    ramp = max(1e-6, ramp_frac * dur)
    inside = (t >= onset) & (t <= end)
    g[inside] = 1.0
    # rising edge
    re = (t >= onset) & (t < onset + ramp)
    g[re] = 0.5 * (1 - np.cos(np.pi * (t[re] - onset) / ramp))
    # falling edge
    fe = (t > end - ramp) & (t <= end)
    g[fe] = 0.5 * (1 - np.cos(np.pi * (end - t[fe]) / ramp))
    g[(t < onset) | (t > end)] = 0.0
    return g


class BurstNoteModel:
    """EXACT gated-sinusoid (note) forward model as a plug-in. ONE component = ONE note:
    (A, f, onset, dur). synthesise sums the notes; propose reads candidate onset+pitch
    off a crude spectrogram; refine polishes f and timing against the exact model. The
    engine peels notes by energy — the test is whether the bag == the note set."""

    def __init__(self, fs, t):
        self.fs = float(fs)
        self._t = np.asarray(t, dtype=float)

    def merge(self, component_list):
        return {"components": list(component_list)}

    def _note(self, comp):
        A, f, onset, dur = comp
        g = _raised_cos_gate(self._t, onset, dur)
        return A * g * np.cos(2 * np.pi * f * self._t)

    def synthesise(self, params):
        out = np.zeros_like(self._t)
        for comp in params["components"]:
            out = out + self._note(comp)
        return out

    def propose(self, residual, t):
        """Candidate notes from a crude STFT: find the (time, freq) cells of peak energy.
        Each becomes an initial (A, f, onset, dur). Over-complete menu (several cells)."""
        self._t = np.asarray(t, dtype=float)
        T = len(residual)
        fs = self.fs
        # short-time analysis: window the residual, find the dominant freq per frame, then
        # pick the frames with the most energy as note onsets.
        win_len = max(8, T // 16)
        hop = max(1, win_len // 2)
        frames = []
        for start in range(0, T - win_len + 1, hop):
            seg = residual[start:start + win_len]
            energy = float(np.sum(seg ** 2))
            spec = np.abs(np.fft.rfft(seg * np.hanning(win_len)))
            freqs = np.fft.rfftfreq(win_len, d=1.0 / fs)
            fpk = float(freqs[int(np.argmax(spec))])
            tc = (start + win_len / 2) / fs
            frames.append((energy, tc, fpk, start))
        if not frames:
            return []
        # group contiguous frames with similar peak-freq into note candidates
        frames_sorted = sorted(frames, key=lambda fr: -fr[0])
        cands = []
        dur0 = win_len / fs * 2
        for energy, tc, fpk, start in frames_sorted[:8]:
            onset0 = max(0.0, tc - dur0 / 2)
            A0 = float(np.sqrt(2 * energy / max(1, win_len)))
            cands.append((A0, fpk, onset0, dur0))
        return cands

    def refine_component(self, comp, target, t):
        """Polish (A, f, onset, dur) against the exact note model: golden-section on f,
        then coordinate golden-section on onset and dur, then closed-form A."""
        self._t = np.asarray(t, dtype=float)
        comp = list(comp)

        def err(c):
            s = self._note(tuple(c))
            return float(np.sum((s - target) ** 2))

        def fit_A(c):
            # closed-form amplitude for fixed (f, onset, dur)
            g = _raised_cos_gate(self._t, c[2], c[3])
            basis = g * np.cos(2 * np.pi * c[1] * self._t)
            denom = float(np.sum(basis ** 2))
            if denom <= 1e-12:
                return 0.0
            return float(np.sum(basis * target) / denom)

        gr = (np.sqrt(5) - 1) / 2
        T_span = float(self._t[-1] - self._t[0])
        # search widths
        spans = {"f": 50.0, "onset": 0.15 * T_span, "dur": 0.3 * T_span}
        for _sweep in range(5):
            for key, idx in (("f", 1), ("onset", 2), ("dur", 3)):
                base = list(comp)
                center = comp[idx]
                lo, hi = center - spans[key], center + spans[key]
                if idx == 1:
                    lo = max(1.0, lo)
                if idx in (2, 3):
                    lo = max(1e-4, lo)
                aa, bb = lo, hi
                cc = bb - gr * (bb - aa)
                dd = aa + gr * (bb - aa)

                def ev(val):
                    c2 = list(base)
                    c2[idx] = val
                    c2[0] = fit_A(c2)
                    return err(c2)

                fc, fd = ev(cc), ev(dd)
                for _ in range(28):
                    if fc < fd:
                        bb, dd, fd = dd, cc, fc
                        cc = bb - gr * (bb - aa)
                        fc = ev(cc)
                    else:
                        aa, cc, fc = cc, dd, fd
                        dd = aa + gr * (bb - aa)
                        fd = ev(dd)
                    if abs(bb - aa) < 1e-9:
                        break
                comp[idx] = (aa + bb) / 2.0
                spans[key] *= 0.5
        comp[0] = fit_A(comp)
        return tuple(comp)


def _match_notes(true_notes, est_notes, fs):
    """Greedy match estimated notes to true notes by (onset, pitch) proximity.
    Returns list of (true, est_or_None) and the count of est that matched no true."""
    used = set()
    pairs = []
    for (At, ft, ont, dt_) in true_notes:
        best_j, best_d = None, np.inf
        for j, (Ae, fe, one, de) in enumerate(est_notes):
            if j in used:
                continue
            d = abs(fe - ft) / max(1.0, ft) + abs(one - ont) * 10.0
            if d < best_d:
                best_d, best_j = d, j
        if best_j is not None and best_d < 0.5:
            used.add(best_j)
            pairs.append(((At, ft, ont, dt_), est_notes[best_j]))
        else:
            pairs.append(((At, ft, ont, dt_), None))
    spurious = len(est_notes) - len(used)
    return pairs, spurious


def test_compositional(n_trials=24, fs=4000.0, T_samples=512, seed=31):
    rng = np.random.default_rng(seed)
    t = np.arange(T_samples) / fs
    T_span = t[-1] - t[0]
    note_recov, pitch_errs, onset_errs = [], [], []
    n_components_used, n_true_notes, spurious_counts = [], [], []
    fit_rmse = []
    for _ in range(n_trials):
        K = int(rng.integers(2, 5))  # 2..4 notes
        # place notes on a coarse rhythm grid, non-overlapping-ish
        grid = np.linspace(0.05 * T_span, 0.75 * T_span, 4)
        onsets = sorted(rng.choice(grid, size=K, replace=False))
        notes = []
        for on0 in onsets:
            f = float(rng.uniform(300, 1200))
            dur = float(rng.uniform(0.15, 0.25) * T_span)
            A = float(rng.uniform(0.7, 1.3))
            notes.append((A, f, float(on0), dur))
        fm = BurstNoteModel(fs, t)
        signal = fm.synthesise(fm.merge(notes))
        # let the engine peel up to a generous number of components (it decides n)
        res = solve_for_n(fm, signal, n=None, max_n=8, t=t)
        est = res["components"]
        n_components_used.append(len(est))
        n_true_notes.append(K)
        pairs, spurious = _match_notes(notes, est, fs)
        spurious_counts.append(spurious)
        hit = sum(1 for (_, e) in pairs if e is not None)
        note_recov.append(hit / K)
        for (tr, es) in pairs:
            if es is not None:
                pitch_errs.append(abs(es[1] - tr[1]) / tr[1])
                onset_errs.append(abs(es[2] - tr[2]) / T_span)
        fit_rmse.append(res["match_error"] / np.sqrt(len(signal)))
    return {
        "n_trials": n_trials,
        "note_recovery_rate": float(np.mean(note_recov)),
        "median_pitch_relerr": float(np.median(pitch_errs)) if pitch_errs else None,
        "median_onset_relerr": float(np.median(onset_errs)) if onset_errs else None,
        "mean_components_used": float(np.mean(n_components_used)),
        "mean_true_notes": float(np.mean(n_true_notes)),
        "mean_spurious": float(np.mean(spurious_counts)),
        "median_fit_rmse": float(np.median(fit_rmse)),
    }


# ===========================================================================
# RUN
# ===========================================================================

def main():
    quick = "--quick" in sys.argv
    t0 = time.time()
    print("=" * 78)
    print("solve_for_n LADDER — three harder rungs, ONE engine (plug-ins only)")
    print("=" * 78)

    # ---- RUNG 1: non-linear physics
    print("\n[RUNG 1] NON-LINEAR PHYSICS — 2-body Kepler orbit (continuous, non-linear)")
    phys = test_physics(n_trials=10 if quick else 30)
    print(f"  trials={phys['n_trials']}")
    print(f"  recovery rate (a,e,n all <2%): {phys['recovery_rate']*100:.1f}%")
    print(f"  median |a| rel err : {phys['median_a_relerr']:.2e}   p95 {phys['p95_a_relerr']:.2e}")
    print(f"  median |e| abs err : {phys['median_e_abserr']:.2e}")
    print(f"  median |n| rel err : {phys['median_n_relerr']:.2e}")
    print(f"  median traj RMSE   : {phys['median_traj_rmse']:.2e}   p95 {phys['p95_traj_rmse']:.2e}")

    # ---- RUNG 2: discrete / symbolic
    print("\n[RUNG 2] DISCRETE / SYMBOLIC — elementary cellular automaton (no gradient)")
    disc = test_discrete(n_trials=12 if quick else 40)
    print(f"  trials={disc['n_trials']}")
    print(f"  CONTINUOUS engine (as-is): rule recovery {disc['continuous']['rule_recovery_rate']*100:.1f}%, "
          f"pattern recovery {disc['continuous']['pattern_recovery_rate']*100:.1f}%")
    print(f"  DISCRETE extension (min fix): rule recovery {disc['discrete_extension']['rule_recovery_rate']*100:.1f}%, "
          f"pattern recovery {disc['discrete_extension']['pattern_recovery_rate']*100:.1f}%")

    # ---- RUNG 3: compositional
    print("\n[RUNG 3] COMPOSITIONAL — notes-in-a-melody (nested hierarchy; speech rung)")
    comp = test_compositional(n_trials=8 if quick else 24)
    print(f"  trials={comp['n_trials']}")
    print(f"  note recovery rate : {comp['note_recovery_rate']*100:.1f}%")
    mp = f"{comp['median_pitch_relerr']:.2e}" if comp['median_pitch_relerr'] is not None else "n/a"
    mo = f"{comp['median_onset_relerr']:.2e}" if comp['median_onset_relerr'] is not None else "n/a"
    print(f"  median pitch rel err: {mp}")
    print(f"  median onset rel err: {mo}")
    print(f"  mean components used: {comp['mean_components_used']:.2f}  (mean true notes {comp['mean_true_notes']:.2f})")
    print(f"  mean spurious comps : {comp['mean_spurious']:.2f}")
    print(f"  median fit RMSE     : {comp['median_fit_rmse']:.2e}")

    # ---- VERDICT
    print("\n" + "=" * 78)
    print("VERDICT")
    phys_ok = phys["recovery_rate"] >= 0.8
    disc_cont_ok = disc["continuous"]["rule_recovery_rate"] >= 0.8
    disc_ext_ok = disc["discrete_extension"]["rule_recovery_rate"] >= 0.8
    comp_recov_ok = comp["note_recovery_rate"] >= 0.8
    comp_clean = comp["mean_components_used"] <= comp["mean_true_notes"] * 1.25 and comp["mean_spurious"] <= 0.5

    print(f"  RUNG 1 physics      : {'CLEARS' if phys_ok else 'BREAKS'} "
          f"(recovery {phys['recovery_rate']*100:.0f}%)")
    print(f"  RUNG 2 discrete     : continuous engine {'CLEARS' if disc_cont_ok else 'BREAKS'} "
          f"({disc['continuous']['rule_recovery_rate']*100:.0f}% rule) | "
          f"discrete-extension {'CLEARS' if disc_ext_ok else 'still BREAKS'} "
          f"({disc['discrete_extension']['rule_recovery_rate']*100:.0f}% rule)")
    print(f"  RUNG 3 compositional: notes {'recovered' if comp_recov_ok else 'NOT recovered'} "
          f"({comp['note_recovery_rate']*100:.0f}%), structure "
          f"{'CLEAN' if comp_clean else 'SHATTERED/flat-bag'} "
          f"({comp['mean_components_used']:.1f} comps for {comp['mean_true_notes']:.1f} notes, "
          f"{comp['mean_spurious']:.1f} spurious)")

    print(f"\nelapsed {time.time()-t0:.1f}s")
    print("SOLVE_FOR_N_LADDER_COMPLETED")


if __name__ == "__main__":
    main()
