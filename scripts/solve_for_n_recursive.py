"""solve_for_n_recursive — the RECURSIVE / HIERARCHICAL solve-for-N: the named fix for
the COMPOSITIONAL BREAK found by the diagnostic ladder (commit a2c87ae0, memory
ozma_diagnostic_ladder_method).

THE BREAK (rung 3 of scripts/solve_for_n_ladder.py). The FLAT solve-for-N
(scripts/solve_for_n.solve_for_n) peels low-level components by energy (matching
pursuit) and has NO operator to GROUP them. On a melody of gated harmonic notes it
SHATTERS each note into several partials -> a flat over-complete bag (8 components for
~3 notes, RMSE stuck ~0.18-0.22). The partials of one note are scattered across the bag
instead of being recognised as ONE thing.

THE FIX (this file) — hierarchical analysis-by-synthesis. Solve over NOTES at the TOP
level; each note is itself a gated SUB-SOLVE over its PARTIALS. So the harmonics of one
note are fit TOGETHER as a UNIT (grouped by the recursion), not scattered:

    MELODY  =  sum of NOTES                      (top-level solve-for-N over notes)
      NOTE  =  gated harmonic stack of PARTIALS  (sub-solve over harmonics + envelope)
   PARTIAL  =  one (k*f0) sinusoid amplitude     (the leaf — close to the flat sinusoid)

THE RECURSION (reuses the proven flat engine where it fits; the NEW mechanism is the
note-level PROPOSAL = harmonic-comb grouping + the recursion):

  TOP LEVEL (melody): matching-pursuit over NOTES.
    1. residual <- signal
    2. PROPOSE a note = the strongest FUNDAMENTAL in the residual's local time-frequency
       region. Crucially we score a candidate f0 by its HARMONIC-COMB energy (f0 + 2f0 +
       3f0 + ...), NOT by a lone partial's energy. This is the grouping operator: a real
       note's comb out-scores any single partial, so we propose the FUNDAMENTAL, never a
       stray harmonic.
    3. SUB-SOLVE that note: on the note's local (gated) signal, fit f0 + the partial
       amplitudes + the envelope (onset/dur) as ONE unit. The sub-solve GROUPS the
       partials -> no shattering.
    4. SYNTHESISE the whole note (gated harmonic stack) -> SUBTRACT -> recurse to the
       next note. Stop when the residual stops shrinking (the note count is RECOVERED,
       not fixed in advance).
    5. JOINT back-fitting over the admitted NOTES (the order-N co-refinement at the note
       level) — re-fit each note against the signal with the others held.

DONKEY AUDIT. Recursive solve = owned numpy (matching pursuit at the note level +
back-fitting), reusing the FLAT engine per level: the partial-amplitude sub-fit is a
closed-form least-squares against the EXACT harmonic basis (the same calculus the flat
refine_component uses for a sinusoid), and the leaf f0 polish is golden-section against
the exact model (identical to the flat frequency polish). The two forward models (NOTE =
gated harmonic stack, MELODY = sum of notes) are owned EXACT generative numpy functions.
Ground truth is constructed -> every error is exact. NO neural net, NO .fit(), NO
gradient-descent TRAINING. CortexLoop untouched.

PREDICTION (to be killed if false). The recursion GROUPS the partials of each f0 into a
single note unit -> it recovers the TRUE note count (e.g. 3 notes, not 8 components),
the note params (f0, onset, duration) are accurate, and the fit RMSE COLLAPSES well
below the flat ~0.18-0.22 floor. KILL/HONEST: if it still shatters or MIS-GROUPS (octave
errors folding two notes into one f0, or a note splitting across two f0 candidates),
report it and pinpoint WHICH stage broke (note proposal / sub-solve / stop criterion).

Run:  python -m scripts.solve_for_n_recursive            (full acceptance + verdict)
      python -m scripts.solve_for_n_recursive --quick    (small smoke test)
"""
from __future__ import annotations

import sys
import time
import numpy as np

from scripts.solve_for_n import solve_for_n  # the FLAT engine, reused at the leaf level.


# ===========================================================================
# FORWARD MODELS (owned, EXACT, ground truth known) — the hierarchy.
# ===========================================================================

def _raised_cos_gate(t, onset, dur, ramp_frac=0.15):
    """Smooth on/off gate (raised-cosine ramps) of duration dur starting at onset.
    (Same gate as the ladder's note model — the envelope of a note.)"""
    g = np.zeros_like(t)
    end = onset + dur
    ramp = max(1e-6, ramp_frac * dur)
    inside = (t >= onset) & (t <= end)
    g[inside] = 1.0
    re = (t >= onset) & (t < onset + ramp)
    g[re] = 0.5 * (1 - np.cos(np.pi * (t[re] - onset) / ramp))
    fe = (t > end - ramp) & (t <= end)
    g[fe] = 0.5 * (1 - np.cos(np.pi * (end - t[fe]) / ramp))
    g[(t < onset) | (t > end)] = 0.0
    return g


def synth_note(t, f0, onset, dur, partial_amps, phases=None):
    """NOTE forward model — a gated harmonic STACK. A note is a fundamental f0 plus
    partials (2 f0, 3 f0, ...) with amplitudes `partial_amps` (partial_amps[0] is the
    fundamental's amplitude), all under one raised-cosine envelope (onset, dur).
    params = [f0, onset, dur, partial_amps]. EXACT owned generative function."""
    g = _raised_cos_gate(t, onset, dur)
    if phases is None:
        phases = np.zeros(len(partial_amps))
    out = np.zeros_like(t)
    for k, amp in enumerate(partial_amps, start=1):
        out = out + amp * np.cos(2 * np.pi * k * f0 * t + phases[k - 1])
    return g * out


def synth_melody(t, notes):
    """MELODY forward model — a SEQUENCE of notes (sum of note syntheses). Each note is
    a dict {f0, onset, dur, partial_amps, [phases]}. EXACT owned generative function."""
    out = np.zeros_like(t)
    for nt in notes:
        out = out + synth_note(t, nt["f0"], nt["onset"], nt["dur"],
                               nt["partial_amps"], nt.get("phases"))
    return out


# ===========================================================================
# THE NOTE SUB-SOLVE — fit ONE note's f0 + partials + envelope as a UNIT.
# This is the recursion's inner level: it GROUPS the partials of one f0 so they are
# never scattered. Reuses the flat engine's calculus (closed-form LSQ on the exact
# harmonic basis + golden-section on f0 — identical to the flat sinusoid polish).
# ===========================================================================

def _fit_partials_lsq(t, gate, f0, n_partials, target):
    """Closed-form least-squares of `target` onto the gated harmonic basis at f0 — fits
    ALL partial amplitudes (and phases, via cos+sin) of ONE note JOINTLY. This is the
    GROUPING: the partials of f0 are a single linear fit, not separate peels. Returns
    (partial_amps, phases, recon, sse). Same closed-form calculus as the flat engine's
    refine_component, applied to the harmonic comb instead of a lone sinusoid."""
    cols = []
    for k in range(1, n_partials + 1):
        cols.append(gate * np.cos(2 * np.pi * k * f0 * t))
        cols.append(gate * np.sin(2 * np.pi * k * f0 * t))
    M = np.stack(cols, axis=1)
    coef, *_ = np.linalg.lstsq(M, target, rcond=None)
    recon = M @ coef
    sse = float(np.sum((target - recon) ** 2))
    amps, phases = [], []
    for k in range(n_partials):
        a, b = coef[2 * k], coef[2 * k + 1]
        amps.append(float(np.hypot(a, b)))
        phases.append(float(np.arctan2(-b, a)))
    return np.asarray(amps), np.asarray(phases), recon, sse


def _refine_envelope(t, f0, onset, dur, n_partials, target):
    """Golden-section coordinate polish of (onset, dur) of ONE note against the exact
    note model, re-fitting the partials (LSQ) at each trial. Bounded local AbS calculus
    (NOT weight training) — same golden-section the flat engine uses, on the envelope."""
    gr = (np.sqrt(5) - 1) / 2
    T_span = float(t[-1] - t[0])

    def sse_at(on, du):
        on = max(1e-4, on)
        du = max(1e-3, du)
        g = _raised_cos_gate(t, on, du)
        _, _, _, sse = _fit_partials_lsq(t, g, f0, n_partials, target)
        return sse

    spans = {"onset": 0.15 * T_span, "dur": 0.25 * T_span}
    for _sweep in range(5):
        # onset
        lo, hi = max(0.0, onset - spans["onset"]), onset + spans["onset"]
        aa, bb = lo, hi
        cc, dd = bb - gr * (bb - aa), aa + gr * (bb - aa)
        fc, fd = sse_at(cc, dur), sse_at(dd, dur)
        for _ in range(28):
            if fc < fd:
                bb, dd, fd = dd, cc, fc; cc = bb - gr * (bb - aa); fc = sse_at(cc, dur)
            else:
                aa, cc, fc = cc, dd, fd; dd = aa + gr * (bb - aa); fd = sse_at(dd, dur)
            if abs(bb - aa) < 1e-7:
                break
        onset = (aa + bb) / 2.0
        spans["onset"] *= 0.5
        # dur
        lo, hi = max(1e-3, dur - spans["dur"]), dur + spans["dur"]
        aa, bb = lo, hi
        cc, dd = bb - gr * (bb - aa), aa + gr * (bb - aa)
        fc, fd = sse_at(onset, cc), sse_at(onset, dd)
        for _ in range(28):
            if fc < fd:
                bb, dd, fd = dd, cc, fc; cc = bb - gr * (bb - aa); fc = sse_at(onset, cc)
            else:
                aa, cc, fc = cc, dd, fd; dd = aa + gr * (bb - aa); fd = sse_at(onset, dd)
            if abs(bb - aa) < 1e-7:
                break
        dur = (aa + bb) / 2.0
        spans["dur"] *= 0.5
    return onset, dur


def _polish_f0(t, f0, onset, dur, n_partials, target, half_window_hz):
    """Golden-section on the FUNDAMENTAL f0 against the exact gated harmonic model
    (re-fitting partials by LSQ at each trial). The leaf-level continuous frequency
    polish — IDENTICAL in form to the flat engine's frequency golden-section, but the
    error is over the WHOLE comb (so the whole note's harmonics constrain f0 jointly =
    the grouping, and it locks onto the true fundamental, resisting octave slips)."""
    gr = (np.sqrt(5) - 1) / 2
    g = _raised_cos_gate(t, onset, dur)

    def sse_at(f):
        if f <= 0:
            return np.inf
        _, _, _, sse = _fit_partials_lsq(t, g, f, n_partials, target)
        return sse

    lo, hi = max(1.0, f0 - half_window_hz), f0 + half_window_hz
    aa, bb = lo, hi
    cc, dd = bb - gr * (bb - aa), aa + gr * (bb - aa)
    fc, fd = sse_at(cc), sse_at(dd)
    for _ in range(48):
        if fc < fd:
            bb, dd, fd = dd, cc, fc; cc = bb - gr * (bb - aa); fc = sse_at(cc)
        else:
            aa, cc, fc = cc, dd, fd; dd = aa + gr * (bb - aa); fd = sse_at(dd)
        if abs(bb - aa) < 1e-6:
            break
    return (aa + bb) / 2.0


def sub_solve_note(t, fs, f0_init, onset_init, dur_init, target, n_partials=6, sweeps=3,
                   f0_min=120.0):
    """THE RECURSIVE SUB-SOLVE (note level). Given a coarse (f0, onset, dur) proposal and
    the LOCAL target signal, fit ONE note's f0 + partial amplitudes + envelope as a UNIT.
    Returns a note dict. The partials are GROUPED (joint LSQ), never peeled separately.

    Coordinate AbS: alternate (polish f0 | polish envelope | re-fit partials) for a few
    sweeps until it settles — the note-level 'n passes' of analysis-by-synthesis."""
    bin_hz = fs / len(t)
    f0, onset, dur = float(f0_init), float(onset_init), float(dur_init)

    # --- FUNDAMENTAL CORRECTION (kills the sub-multiple proposal). A sub-multiple f0
    # (e.g. true/2, true/1.5) fits the note's energy into its EVEN/sparse partials, so its
    # OWN fundamental amplitude is near-zero while a higher partial dominates. Detect that
    # degenerate amplitude profile and snap f0 UP to the partial that actually carries the
    # energy (its true fundamental), accepting the snap only if the fit stays as good. This
    # is the leaf-level grouping check — a note is the HIGHEST f0 whose comb explains it.
    # OCTAVE / SUB-MULTIPLE CORRECTION — find the TRUE fundamental of this note. A note's
    # true f0 is the HIGHEST f whose harmonic comb (f,2f,3f,...) explains the local energy
    # with NO empty in-between partials. A proposal can land on either side of it:
    #   - a SUB-multiple (true/m): only every m-th partial carries energy (empty-gap tell)
    #     -> snap UP to m*f.
    #   - a SUPER-multiple (m*true): its comb is a SUBSET of the real series, so the LOWER
    #     fundamental fits AT LEAST AS WELL while filling the in-between partials -> snap
    #     DOWN to f/m (accept only if it does not worsen the fit, so two real notes an
    #     octave apart are never merged — merging would leave the upper note's odd partials
    #     mis-explained and worsen sse).
    # Iterate the snap until f0 settles on the highest gap-free fundamental.
    def _gate_fit(ff, on, du):
        g = _raised_cos_gate(t, on, du)
        a, _, _, sse = _fit_partials_lsq(t, g, ff, n_partials, target)
        return a, sse

    for _ in range(4):
        amps0, sse0 = _gate_fit(f0, onset, dur)
        if float(np.sum(amps0)) <= 1e-9:
            break
        snapped = False
        # snap UP (sub-multiple -> empty in-between partials)
        for m in (2, 3):
            if n_partials < m + 1:
                continue
            on_grid = amps0[m - 1::m]
            off_grid = np.array([a for i, a in enumerate(amps0) if (i + 1) % m != 0])
            if len(off_grid) == 0 or float(np.sum(on_grid)) <= 0:
                continue
            if float(np.max(off_grid)) < 0.08 * float(np.max(on_grid)):
                _, sse_up = _gate_fit(f0 * m, onset, dur)
                if sse_up <= sse0 * 1.10:
                    f0 *= m; snapped = True; break
        if snapped:
            continue
        # snap DOWN (super-multiple -> a denser real comb fits AS WELL, and the in-between
        # partials it adds actually carry energy — otherwise the lower comb is spurious and
        # we must NOT merge two distinct notes). Require both: fit not worse AND the newly-
        # added (in-between) partials are non-negligible.
        for m in (2, 3):
            f_down = f0 / m
            if f_down < f0_min:                  # a real note never sits below the f0 floor
                continue
            amps_dn, sse_dn = _gate_fit(f_down, onset, dur)
            if sse_dn > sse0 * 1.001:
                continue
            # the in-between partials of f_down (those NOT multiples of m) must carry energy
            inbtw = np.array([a for i, a in enumerate(amps_dn) if (i + 1) % m != 0])
            ongrid = amps_dn[m - 1::m]
            if len(inbtw) and len(ongrid) and \
               float(np.max(inbtw)) > 0.05 * float(np.max(ongrid)):
                f0 = f_down; snapped = True; break
        if not snapped:
            break

    for sweep in range(sweeps):
        win = (3.0 if sweep == 0 else 1.0) * bin_hz
        f0 = _polish_f0(t, f0, onset, dur, n_partials, target, half_window_hz=win)
        onset, dur = _refine_envelope(t, f0, onset, dur, n_partials, target)
    g = _raised_cos_gate(t, onset, dur)
    amps, phases, _, _ = _fit_partials_lsq(t, g, f0, n_partials, target)
    return {"f0": f0, "onset": onset, "dur": dur,
            "partial_amps": amps, "phases": phases}


# ===========================================================================
# THE NOTE PROPOSAL — harmonic-comb grouping (the NEW mechanism).
# Score a candidate fundamental by the energy of its WHOLE comb (f0+2f0+3f0+...), not a
# lone partial, so a real note out-scores any stray harmonic and we PROPOSE THE
# FUNDAMENTAL. This is the operator the flat engine lacked.
# ===========================================================================

def propose_fundamental(residual, t, fs, n_partials=6, f0_min=120.0, f0_max=1500.0):
    """Propose a NOTE = the strongest FUNDAMENTAL in the residual (the grouping operator
    the flat engine lacks). Two-stage to be both frequency-precise AND time-localised:

      1. FREQUENCY: a HIGH-RESOLUTION whole-signal magnitude spectrum (the note is gated
         but its comb is visible). Score each candidate f0 by its harmonic-comb energy,
         GATED so a sub-octave/sub-harmonic (whose ODD harmonics fall in the comb gaps and
         stay near the noise floor) is rejected -> the HIGHEST f0 explaining the comb (the
         true fundamental) wins.
      2. TIME: localise onset/dur with the CHOSEN f0's OWN comb-energy envelope (bandpass
         to its harmonics, take the smoothed envelope) -> ties the time window to the SAME
         note as the f0 (decoupling them is the cross-note confusion bug).

    Returns (f0, onset, dur) or None. The sub-solve then sharpens everything continuously."""
    T = len(residual)
    if float(np.sum(residual ** 2)) < 1e-12:
        return None
    # --- high-resolution whole-signal spectrum (frequency precision for f0).
    nfft = int(2 ** np.ceil(np.log2(max(8, 8 * T))))
    win = np.hanning(T)
    spec = np.abs(np.fft.rfft(residual * win, n=nfft))
    freqs = np.fft.rfftfreq(nfft, d=1.0 / fs)
    df = freqs[1] - freqs[0]
    noise_floor = float(np.median(spec)) + 1e-9

    def _harm_energy(f0):
        e = []
        for k in range(1, n_partials + 1):
            fk = k * f0
            if fk >= freqs[-1]:
                e.append(0.0)
                continue
            idx = int(round(fk / df))
            lo, hi = max(0, idx - 3), min(len(spec), idx + 4)
            e.append(float(np.max(spec[lo:hi])))
        return np.asarray(e)

    def comb_score(f0):
        """Comb energy GATED on f0 being a TRUE fundamental, not a sub-multiple. A
        sub-multiple lands its EVEN harmonics on the real comb but leaves its ODD harmonics
        (incl. its own fundamental) near the floor; that empty-odd signature is what
        distinguishes it. Require the fundamental present; weight by the fraction of
        harmonics present, with the ODD harmonics weighted hard (their emptiness is the
        sub-multiple tell). This makes the HIGHEST f0 explaining the comb win."""
        e = _harm_energy(f0)
        present = e > 4.0 * noise_floor
        if not present[0]:
            return 0.0
        frac_present = float(np.mean(present))
        odd_idx = np.arange(0, n_partials, 2)        # k=1,3,5 -> indices 0,2,4
        odd_present = float(np.mean(present[odd_idx])) if len(odd_idx) else 1.0
        # odd_present**2 makes a half/third-octave (odds empty) score collapse.
        return float(np.sum(e)) * frac_present * (odd_present ** 2)

    # candidate fundamentals: spectral peaks within band + their sub-multiples (the comb
    # gate ranks the true fundamental above any sub-multiple).
    cand_set = set()
    for i in range(1, len(spec) - 1):
        f = freqs[i]
        if f < f0_min or f > f0_max:
            continue
        if spec[i] > spec[i - 1] and spec[i] >= spec[i + 1]:
            cand_set.add(round(f, 2))
            for k in (2, 3):
                if f / k >= f0_min:
                    cand_set.add(round(f / k, 2))
    if not cand_set:
        cand_set = set(np.round(np.arange(f0_min, f0_max, df * 2), 2))
    best_f0, best_s = None, -np.inf
    for f0 in sorted(cand_set):
        sc = comb_score(f0)
        if sc > best_s:
            best_s, best_f0 = sc, f0
    if best_f0 is None or best_s <= 0:
        return None

    # --- onset/dur from the chosen f0's COMB-energy envelope (ties time to THIS note).
    full_spec = np.fft.rfft(residual)
    full_freqs = np.fft.rfftfreq(T, d=1.0 / fs)
    fdf = full_freqs[1] - full_freqs[0] if len(full_freqs) > 1 else fs
    mask = np.zeros(len(full_spec))
    bw = max(2.0 * fdf, 0.10 * best_f0)
    for k in range(1, n_partials + 1):
        fk = k * best_f0
        if fk >= full_freqs[-1]:
            break
        mask[np.abs(full_freqs - fk) <= bw] = 1.0
    comb_sig = np.fft.irfft(full_spec * mask, n=T)
    elen = max(8, T // 32)
    env = np.convolve(comb_sig ** 2, np.ones(elen) / elen, mode="same")
    if float(np.max(env)) <= 0:
        return best_f0, float(t[0]), float(t[-1] - t[0]) * 0.3
    thr = 0.2 * float(np.max(env))
    above = env >= thr
    pk = int(np.argmax(env))
    lo = pk
    while lo > 0 and above[lo - 1]:
        lo -= 1
    hi = pk
    while hi < len(above) - 1 and above[hi + 1]:
        hi += 1
    onset0 = float(max(0.0, t[lo]))
    dur0 = float(max(elen / fs, t[min(hi, len(t) - 1)] - t[lo]))
    return best_f0, onset0, dur0


# ===========================================================================
# THE RECURSIVE / HIERARCHICAL SOLVE-FOR-N (the top level — over NOTES).
# ===========================================================================

def recursive_solve_melody(signal, fs, t=None, max_notes=8, n_partials=6,
                           stop_frac=0.999, min_note_gain=0.01, joint_passes=4,
                           verbose=False):
    """SOLVE-FOR-N over NOTES (the top of the hierarchy). Matching pursuit at the note
    level: propose the strongest FUNDAMENTAL (harmonic-comb grouping) -> SUB-SOLVE that
    note (group its partials + envelope as a unit) -> synthesise the whole note ->
    subtract -> recurse. Stop when a new note explains < min_note_gain of the signal
    energy (the note COUNT is recovered, not fixed). Then joint back-fit the notes.

    Returns dict: notes (list of note params), residual, match_error, rmse, n_notes,
    passes. NO net / fit / gradient-descent training — owned AbS."""
    signal = np.asarray(signal, dtype=float)
    if t is None:
        t = np.arange(len(signal)) / fs
    total_energy = float(np.sum(signal ** 2))
    notes = []
    residual = signal.copy()
    passes = 0

    for _k in range(max_notes * 2):     # allow a few skips; stop on the energy floor
        passes += 1
        res_energy = float(np.sum(residual ** 2))
        if res_energy / max(1e-12, total_energy) < (1.0 - stop_frac):
            break                         # residual is at the energy floor -> done
        prop = propose_fundamental(residual, t, fs, n_partials=n_partials)
        if prop is None:
            break
        f0_0, on0, dur0 = prop
        # SUB-SOLVE: group this note's partials + envelope as a UNIT on the residual.
        note = sub_solve_note(t, fs, f0_0, on0, dur0, residual, n_partials=n_partials)
        note_sig = synth_note(t, note["f0"], note["onset"], note["dur"],
                              note["partial_amps"], note["phases"])
        gain = float(np.sum(note_sig ** 2)) / max(1e-12, total_energy)
        new_res = residual - note_sig
        explained = 1.0 - float(np.sum(new_res ** 2)) / max(1e-12, res_energy)
        if verbose:
            print(f"  note {len(notes)+1}: f0={note['f0']:.1f} onset={note['onset']:.3f} "
                  f"dur={note['dur']:.3f} gain={gain:.4f} explained={explained:.4f}")
        # A note is ADMITTED only if it reduces the residual (soft excluder). If a
        # proposal is weak/spurious we DON'T terminate the whole solve (there may be real
        # notes elsewhere) — we subtract its (small) comb energy to move the proposal on,
        # and stop only if the residual stops shrinking at all (no-progress guard).
        if explained <= 0:
            break                         # cannot make progress anywhere -> stop
        if gain < min_note_gain:
            # too weak to be a note, but it does explain a little: peel it WITHOUT
            # admitting it (keeps the proposal from re-finding the same scrap forever).
            residual = new_res
            if len(notes) >= max_notes:
                break
            continue
        notes.append(note)
        residual = new_res
        if len(notes) >= max_notes:
            break

    # JOINT BACK-FITTING over NOTES (order-N co-refinement at the note level): re-fit
    # each note against the signal with the OTHERS held. Reuses the same sub-solve.
    prev_err = np.inf
    for _jp in range(joint_passes):
        passes += 1
        for i in range(len(notes)):
            others = synth_melody(t, [n for j, n in enumerate(notes) if j != i])
            target_i = signal - others
            notes[i] = sub_solve_note(t, fs, notes[i]["f0"], notes[i]["onset"],
                                      notes[i]["dur"], target_i, n_partials=n_partials,
                                      sweeps=2)
        full = synth_melody(t, notes)
        err = float(np.sqrt(np.sum((full - signal) ** 2)))
        if abs(prev_err - err) < 1e-9 * max(1.0, prev_err):
            break
        prev_err = err

    # CONSOLIDATION (the top-level GROUP cleanup) — enforce that a melody is the MINIMAL
    # set of notes that explains the signal. Two cleanups, each re-checked to convergence:
    #   (i)  MERGE notes that are the SAME note split in two: near-equal f0 (or an exact
    #        octave/harmonic ratio) AND overlapping time. A pitch sounding once is ONE
    #        note; a proposal that peeled it in two pieces (wrong onset/dur on the first
    #        peel) leaves a same-f0 twin -> merge into a single jointly-refit note.
    #   (ii) DROP a REDUNDANT note whose removal barely changes the fit (its energy is
    #        already explained by the others — a spurious harmonic left by an octave
    #        ambiguity). A note that adds ~nothing is not a real note.
    if len(notes) > 1:
        sig_norm = np.sqrt(max(1e-12, total_energy))

        def _overlap(a, b):
            lo = max(a["onset"], b["onset"])
            hi = min(a["onset"] + a["dur"], b["onset"] + b["dur"])
            return hi - lo > 0.25 * min(a["dur"], b["dur"])

        # (i) merge same-pitch / octave-related overlapping notes
        merged = True
        while merged and len(notes) > 1:
            merged = False
            for i in range(len(notes)):
                for j in range(i + 1, len(notes)):
                    a, b = notes[i], notes[j]
                    r = max(a["f0"], b["f0"]) / min(a["f0"], b["f0"])
                    # same pitch (a split note) OR an exact octave/harmonic ratio (a
                    # harmonic of one note peeled off as a phantom note) -> one note.
                    same_pitch = abs(r - 1.0) < 0.03
                    octave_rel = any(abs(r - m) < 0.04 for m in (2.0, 3.0))
                    if (same_pitch or octave_rel) and _overlap(a, b):
                        # re-fit ONE note over the union span at the lower f0
                        f0m = min(a["f0"], b["f0"])
                        on = min(a["onset"], b["onset"])
                        du = max(a["onset"] + a["dur"], b["onset"] + b["dur"]) - on
                        new = sub_solve_note(t, fs, f0m, on, du, signal -
                                             synth_melody(t, [n for k, n in enumerate(notes)
                                                              if k not in (i, j)]),
                                             n_partials=n_partials, sweeps=2)
                        notes = [n for k, n in enumerate(notes) if k not in (i, j)] + [new]
                        merged = True
                        break
                if merged:
                    break

        # (ii) drop redundant notes
        changed = True
        while changed and len(notes) > 1:
            changed = False
            full_err = float(np.sqrt(np.sum((synth_melody(t, notes) - signal) ** 2)))
            for i in range(len(notes)):
                without = [n for j, n in enumerate(notes) if j != i]
                err_wo = float(np.sqrt(np.sum((synth_melody(t, without) - signal) ** 2)))
                if err_wo - full_err < 0.01 * sig_norm:
                    notes = without
                    changed = True
                    break

    full = synth_melody(t, notes)
    resid = signal - full
    match_error = float(np.sqrt(np.sum(resid ** 2)))
    return {
        "notes": notes,
        "residual": resid,
        "match_error": match_error,
        "rmse": match_error / np.sqrt(len(signal)),
        "n_notes": len(notes),
        "passes": passes,
    }


# ===========================================================================
# THE FLAT BASELINE on the SAME harmonic melodies — reuse the flat sinusoid engine.
# Each note is a gated harmonic stack; the flat engine sees a sum of (gated) sinusoids
# with NO grouping. We use the BurstNoteModel-style plug-in (a gated single tone is the
# flat engine's note component) so the comparison is the flat solve's own best shot.
# ===========================================================================

class _FlatBurstModel:
    """Flat plug-in for the existing engine: ONE component = ONE gated single tone
    (A, f, onset, dur). This is the flat engine's view of the melody — it peels gated
    tones by energy with NO note grouping (the rung-3 model from the ladder)."""

    def __init__(self, fs, t):
        self.fs = float(fs)
        self._t = np.asarray(t, dtype=float)

    def merge(self, component_list):
        return {"components": list(component_list)}

    def _tone(self, comp):
        A, f, onset, dur = comp
        g = _raised_cos_gate(self._t, onset, dur)
        return A * g * np.cos(2 * np.pi * f * self._t)

    def synthesise(self, params):
        out = np.zeros_like(self._t)
        for c in params["components"]:
            out = out + self._tone(c)
        return out

    def propose(self, residual, t):
        self._t = np.asarray(t, dtype=float)
        T = len(residual)
        fs = self.fs
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
            frames.append((energy, tc, fpk))
        if not frames:
            return []
        frames.sort(key=lambda fr: -fr[0])
        dur0 = win_len / fs * 2
        cands = []
        for energy, tc, fpk in frames[:8]:
            onset0 = max(0.0, tc - dur0 / 2)
            A0 = float(np.sqrt(2 * energy / max(1, win_len)))
            cands.append((A0, fpk, onset0, dur0))
        return cands

    def refine_component(self, comp, target, t):
        self._t = np.asarray(t, dtype=float)
        comp = list(comp)

        def err(c):
            return float(np.sum((self._tone(tuple(c)) - target) ** 2))

        def fit_A(c):
            g = _raised_cos_gate(self._t, c[2], c[3])
            basis = g * np.cos(2 * np.pi * c[1] * self._t)
            denom = float(np.sum(basis ** 2))
            return 0.0 if denom <= 1e-12 else float(np.sum(basis * target) / denom)

        gr = (np.sqrt(5) - 1) / 2
        T_span = float(self._t[-1] - self._t[0])
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
                cc, dd = bb - gr * (bb - aa), aa + gr * (bb - aa)

                def ev(val):
                    c2 = list(base); c2[idx] = val; c2[0] = fit_A(c2); return err(c2)

                fc, fd = ev(cc), ev(dd)
                for _ in range(28):
                    if fc < fd:
                        bb, dd, fd = dd, cc, fc; cc = bb - gr * (bb - aa); fc = ev(cc)
                    else:
                        aa, cc, fc = cc, dd, fd; dd = aa + gr * (bb - aa); fd = ev(dd)
                    if abs(bb - aa) < 1e-9:
                        break
                comp[idx] = (aa + bb) / 2.0
                spans[key] *= 0.5
        comp[0] = fit_A(comp)
        return tuple(comp)


def flat_solve_melody(signal, fs, t, max_n=8):
    """Run the FLAT solve-for-N (the existing engine, UNCHANGED) on the harmonic melody
    via the gated-tone plug-in. Returns component count + rmse — the baseline."""
    fm = _FlatBurstModel(fs, t)
    res = solve_for_n(fm, signal, n=None, max_n=max_n, t=t)
    full = fm.synthesise(fm.merge(res["components"]))
    rmse = float(np.sqrt(np.mean((full - signal) ** 2)))
    return {"n_components": len(res["components"]), "rmse": rmse,
            "components": res["components"]}


# ===========================================================================
# TEST HARNESS — gated-harmonic melodies, GROUND TRUTH KNOWN. Real numbers.
# ===========================================================================

def _random_melody(rng, t, fs, K):
    """Build a K-note melody of gated HARMONIC stacks with known params."""
    T_span = t[-1] - t[0]
    grid = np.linspace(0.05 * T_span, 0.78 * T_span, 4)
    onsets = sorted(rng.choice(grid, size=K, replace=False))
    notes = []
    for on0 in onsets:
        f0 = float(rng.uniform(180, 600))            # musical fundamentals
        dur = float(rng.uniform(0.15, 0.25) * T_span)
        npart = int(rng.integers(3, 6))               # 3..5 partials per note
        # decaying harmonic amplitudes (a real note's spectral roll-off)
        base = float(rng.uniform(0.8, 1.3))
        amps = np.array([base * (1.0 / (k ** rng.uniform(0.7, 1.4)))
                         for k in range(1, npart + 1)])
        phases = rng.uniform(-np.pi, np.pi, size=npart)
        notes.append({"f0": f0, "onset": float(on0), "dur": dur,
                      "partial_amps": amps, "phases": phases})
    return notes


def _match_notes(true_notes, est_notes):
    """Greedy match estimated notes to true notes by (f0, onset) proximity. Returns
    pairs + spurious count + octave-error count (est f0 ~ k*true or true/k)."""
    used = set()
    pairs = []
    octave_errs = 0
    for tn in true_notes:
        ft, ont = tn["f0"], tn["onset"]
        best_j, best_d = None, np.inf
        for j, en in enumerate(est_notes):
            if j in used:
                continue
            d = abs(en["f0"] - ft) / max(1.0, ft) + abs(en["onset"] - ont) * 5.0
            if d < best_d:
                best_d, best_j = d, j
        if best_j is not None and best_d < 0.5:
            used.add(best_j)
            pairs.append((tn, est_notes[best_j]))
        else:
            pairs.append((tn, None))
            # was the closest est an octave away?
            for j, en in enumerate(est_notes):
                r = en["f0"] / ft
                if any(abs(r - m) < 0.05 for m in (0.5, 2.0, 3.0, 1 / 3.0)) and \
                   abs(en["onset"] - ont) < 0.05:
                    octave_errs += 1
                    break
    spurious = len(est_notes) - len(used)
    return pairs, spurious, octave_errs


def test_recursive(n_trials=24, fs=4000.0, T_samples=1024, seed=31):
    rng = np.random.default_rng(seed)
    t = np.arange(T_samples) / fs
    # recursive metrics
    note_recov, f0_errs, onset_errs, dur_errs = [], [], [], []
    n_notes_rec, n_true, spurious_rec, octave_rec, rmse_rec = [], [], [], [], []
    exact_count = 0
    # flat baseline metrics
    n_comp_flat, rmse_flat = [], []

    for _ in range(n_trials):
        K = int(rng.integers(2, 5))  # 2..4 notes
        notes = _random_melody(rng, t, fs, K)
        signal = synth_melody(t, notes)

        # --- RECURSIVE solve
        rec = recursive_solve_melody(signal, fs, t=t, max_notes=8, n_partials=6)
        est = rec["notes"]
        n_notes_rec.append(rec["n_notes"]); n_true.append(K)
        if rec["n_notes"] == K:
            exact_count += 1
        rmse_rec.append(rec["rmse"])
        pairs, spurious, oct_e = _match_notes(notes, est)
        spurious_rec.append(spurious); octave_rec.append(oct_e)
        hit = sum(1 for (_, e) in pairs if e is not None)
        note_recov.append(hit / K)
        T_span = t[-1] - t[0]
        for (tr, es) in pairs:
            if es is not None:
                f0_errs.append(abs(es["f0"] - tr["f0"]) / tr["f0"])
                onset_errs.append(abs(es["onset"] - tr["onset"]) / T_span)
                dur_errs.append(abs(es["dur"] - tr["dur"]) / T_span)

        # --- FLAT baseline on the SAME signal
        fl = flat_solve_melody(signal, fs, t, max_n=8)
        n_comp_flat.append(fl["n_components"]); rmse_flat.append(fl["rmse"])

    return {
        "n_trials": n_trials,
        # composition
        "note_recovery_rate": float(np.mean(note_recov)),
        "exact_note_count_rate": exact_count / n_trials,
        "mean_n_notes_recursive": float(np.mean(n_notes_rec)),
        "mean_true_notes": float(np.mean(n_true)),
        "mean_spurious_recursive": float(np.mean(spurious_rec)),
        "mean_octave_errors": float(np.mean(octave_rec)),
        # params
        "median_f0_relerr": float(np.median(f0_errs)) if f0_errs else None,
        "median_onset_relerr": float(np.median(onset_errs)) if onset_errs else None,
        "median_dur_relerr": float(np.median(dur_errs)) if dur_errs else None,
        "median_rmse_recursive": float(np.median(rmse_rec)),
        "mean_rmse_recursive": float(np.mean(rmse_rec)),
        # flat baseline
        "mean_n_components_flat": float(np.mean(n_comp_flat)),
        "median_rmse_flat": float(np.median(rmse_flat)),
        "mean_rmse_flat": float(np.mean(rmse_flat)),
    }


# ===========================================================================
# RUN
# ===========================================================================

def main():
    quick = "--quick" in sys.argv
    t0 = time.time()
    print("=" * 78)
    print("solve_for_n RECURSIVE — hierarchical solve-for-N (the compositional-break fix)")
    print("forward models: NOTE = gated harmonic stack; MELODY = sum of notes (EXACT)")
    print("=" * 78)

    r = test_recursive(n_trials=8 if quick else 30)

    print(f"\ntrials = {r['n_trials']}   (gated-harmonic melodies, 2..4 notes, ground truth known)")

    print("\n(a) COMPOSITION — does the recursion stop SHATTERING?")
    print(f"  mean NOTES recovered (recursive) : {r['mean_n_notes_recursive']:.2f}  "
          f"(mean TRUE notes {r['mean_true_notes']:.2f})")
    print(f"  EXACT note-count recovery rate    : {r['exact_note_count_rate']*100:.1f}%")
    print(f"  note recovery rate (matched)      : {r['note_recovery_rate']*100:.1f}%")
    print(f"  mean spurious notes               : {r['mean_spurious_recursive']:.2f}")
    print(f"  mean octave/mis-group errors      : {r['mean_octave_errors']:.2f}")
    mf = f"{r['median_f0_relerr']*100:.2f}%" if r['median_f0_relerr'] is not None else "n/a"
    mo = f"{r['median_onset_relerr']*100:.2f}%" if r['median_onset_relerr'] is not None else "n/a"
    md = f"{r['median_dur_relerr']*100:.2f}%" if r['median_dur_relerr'] is not None else "n/a"
    print(f"  median f0 rel err                 : {mf}")
    print(f"  median onset rel err              : {mo}")
    print(f"  median dur rel err                : {md}")
    print(f"  median fit RMSE (recursive)       : {r['median_rmse_recursive']:.4f}")

    print("\n(b) vs the FLAT solve-for-N baseline (same signals, gated-tone plug-in)")
    print(f"  mean COMPONENTS used (flat)       : {r['mean_n_components_flat']:.2f}  "
          f"(for {r['mean_true_notes']:.2f} true notes -> SHATTERS)")
    print(f"  median fit RMSE (flat)            : {r['median_rmse_flat']:.4f}")
    print(f"  median fit RMSE (recursive)       : {r['median_rmse_recursive']:.4f}  "
          f"(flat {r['median_rmse_flat']:.4f})")

    print("\n" + "=" * 78)
    # VERDICT
    composes = (r["exact_note_count_rate"] >= 0.7 and
                r["note_recovery_rate"] >= 0.8 and
                r["mean_spurious_recursive"] <= 0.5)
    rmse_collapses = r["median_rmse_recursive"] < 0.5 * r["median_rmse_flat"]
    no_shatter = r["mean_n_notes_recursive"] <= r["mean_true_notes"] * 1.25
    print("VERDICT")
    print(f"  recovers NOTES as units (no shatter): {'YES' if no_shatter else 'NO'} "
          f"({r['mean_n_notes_recursive']:.1f} notes vs flat {r['mean_n_components_flat']:.1f} comps "
          f"for {r['mean_true_notes']:.1f} true)")
    print(f"  exact note-count + clean           : {'YES' if composes else 'NO'} "
          f"(exact {r['exact_note_count_rate']*100:.0f}%, recovery {r['note_recovery_rate']*100:.0f}%, "
          f"spurious {r['mean_spurious_recursive']:.2f})")
    print(f"  RMSE collapses below flat floor    : {'YES' if rmse_collapses else 'NO'} "
          f"(recursive {r['median_rmse_recursive']:.3f} vs flat {r['median_rmse_flat']:.3f})")
    if composes and rmse_collapses and no_shatter:
        print("  => the RECURSIVE solve COMPOSES: it groups partials into NOTE units, recovers")
        print("     the true note count, and the fit collapses. The compositional break is FIXED.")
    else:
        print("  => HONEST: see numbers above for what did not clear and the pinpoint below.")

    print(f"\nelapsed {time.time()-t0:.1f}s")
    print("SOLVE_FOR_N_RECURSIVE_COMPLETED")


if __name__ == "__main__":
    main()
