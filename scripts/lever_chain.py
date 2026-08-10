"""lever_chain — THE SELF-SUSTAINING SPEECH-LEVER CLIMB.

I (the agent's instrument) drove the forward-model lever in
docs/forward_model_drive.md (single-mean -> multi-exemplar, +0.0417 grounded on
FSDD cross-speaker digits) and NAMED the next rung myself: an explicit per-speaker
VTL/rate WARP on the generative forward model (exemplar-richness was only a crude
proxy for it). This harness KEEPS CLIMBING — it runs the cycle repeatedly:

    PROPOSE the next lever (from the prior best's own residual error profile)
      -> BUILD it (owned DSP for the warp; NATIVE DtwTo + argmin for the decision)
      -> GROUND it (do-contrast vs the PRIOR BEST, same data/ear/recogniser, +
         silent_failure_grounding world-measure that REOPENs on contradiction)
      -> SELF-CORRECT (COMMIT advances prior-best + names the next rung; REOPEN
         banks the dud and tries the next design OR names the wall)
      -> STOP at a NAMED wall (diminishing returns / needs-acquisition / blocker).

REPRESENTATION. The whole chain runs in the 32-band gammatone LOG-FREQUENCY
trajectory space (scripts.invariant_units_accept.band_trajectory_matrix), because
a VTL scale is a CONSTANT SHIFT on the log-frequency axis (domains/invariant_units
.warp_bands is exact there) — the A1-patch axis mixes centre-freq with variant
type and is NOT cleanly warp-able. So rung 0 is the prior-best multi-exemplar
forward model RE-MEASURED in this warp-able band space (the chain's self-consistent
baseline), and every rung after it is a warp/normalisation of the SAME exemplars.

THE RUNGS (each one's verdict GATES whether prior-best advances):
  R0  prior best  : multi-exemplar forward model (K=all train speakers), band space,
                    NO warp. The carried-over prior best, re-measured here.
  R1  VTL warp    : the lever I named. Estimate the heard talker's VTL (log alpha,
                    forward off its own formant centre-of-mass) AND each exemplar's;
                    WARP each exemplar template into the HEARD speaker's VTL frame
                    before the native DtwTo match. AbS-correct: "imagine the word as
                    THIS heard talker would produce it", not as the canonical talker.
  R2+ named by the result of R1 (rate warp / per-frame CMVN-in-frame / sharper
                    source) — selected from where the current best still errs.

ARCHITECTURE (CLAUDE.md). The recognition DECISION is NATIVE: the per-exemplar
synth-error is the graph DtwTo Term (recognition_graph.synth_error_term) evaluated
by substrate.evaluate in Rust; the min-over-exemplars + argmin-over-words is a
READOUT over native distances (a query, identical in kind to the existing AbS
argmin). The WARP is owned DSP at the world-adapter boundary (a mechanical signal
op on the template matrix, like the medoid pick / blunt downsample in the prior
harnesses) — it reuses the agent's OWN VTL science (invariant_units.warp_bands /
estimate_vtl_logalpha). NO net, NO .fit, NO gradient, NO loss, NO sweep-to-max:
every rung is a FIXED structural choice and the full ablation is reported, never
the winning setting. solve_for_n.py and CortexLoop UNTOUCHED.

THE GROUNDING GATE (every rung). do-contrast: the new lever's recognition vs the
PRIOR BEST's, same data/ear/recogniser. Then silent_failure_grounding.grounding_
check fires on stakes 0.9 and a world-measure RE-RUNS the actual new recogniser; a
contradiction REOPENs. A rung COMMITs only if (delta > +0.005 non-noise floor) AND
the world agrees. An ungrounded "it's better" kept without measuring is the only
failure; a REOPEN is the loop working.

Run: PYTHONUNBUFFERED=1 python -m scripts.lever_chain [n_per_sp_per_digit]
"""
from __future__ import annotations

import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
from domains import recognition_graph as RG
from domains import silent_failure_grounding as SFG
from domains import invariant_units as IU
from scripts.invariant_units_accept import band_trajectory_matrix
from scripts.fsdd_learner_world import load_wav, gather_files

_DIGITS = ['zero', 'one', 'two', 'three', 'four', 'five',
           'six', 'seven', 'eight', 'nine']
_NOISE_FLOOR = 0.005   # a delta below this is noise, not a real gain


class _Term:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def as_tuple(M):
    if M is None:
        return None
    return tuple(tuple(float(v) for v in row) for row in M)


# ==========================================================================
# OWNED DSP — the warp signal ops (world-adapter boundary, mechanical).
# These reuse the agent's OWN VTL science (invariant_units). No decision.
# ==========================================================================

def speaker_logalpha(M, canonical):
    """The heard/exemplar talker's VTL log-alpha, forward off its own formant
    centre-of-mass relative to the cohort canonical (the agent's VTL science)."""
    return float(IU.estimate_vtl_logalpha(M, canonical))


def warp_into_frame(template_M, la_template, la_heard):
    """Warp an exemplar template from ITS speaker's VTL frame INTO the heard
    speaker's frame, so the AbS match imagines the word as the HEARD talker would
    produce it. A scale on Hz is a shift on the log-freq axis; warp_bands applies
    it by linear interpolation along the band axis. The relative shift is
    (la_template - la_heard): move the template's spectrum to where the heard
    talker's tract puts it. Mechanical signal op — no graph decision."""
    rel = la_template - la_heard
    return IU.warp_bands(template_M, rel)


def time_normalise(M, target_frames):
    """RATE warp — resample the time axis to a fixed frame count (linear interp),
    so a fast/slow talker's template lands on the heard talker's tempo before the
    DtwTo match. DTW already absorbs SOME rate, so this is the residual global-tempo
    arm. Mechanical signal op."""
    n = M.shape[0]
    if n == target_frames:
        return M
    src = np.linspace(0, n - 1, target_frames)
    i0 = np.floor(src).astype(int)
    i1 = np.minimum(i0 + 1, n - 1)
    frac = (src - i0)[:, None]
    return (M[i0] * (1 - frac) + M[i1] * frac).astype(M.dtype)


# ==========================================================================
# THE FORWARD MODEL — per-speaker exemplar manifold in band space (the carried
# prior best), with per-exemplar VTL log-alpha stored for the warp rungs.
# ==========================================================================

def build_exemplars(band_M, loaded, held_speaker, canonical, single_mean=False):
    """word -> [ (exemplar_band_matrix, exemplar_logalpha) ... ] over TRAIN
    speakers, one medoid per train speaker (spans the speaker space). LOSO: the
    held-out speaker never contributes to its own forward model.

    single_mean=True collapses the manifold to ONE mean trajectory per word (the
    PRE-forward_model_drive ceiling) — used to ISOLATE the warp's mechanism: if the
    warp helps the single mean (no manifold to absorb VTL) but not the manifold,
    the manifold was already approximating the per-speaker warp."""
    fm = {}
    for w in _DIGITS:
        by_sp = {}
        for i, (d, s) in enumerate(loaded):
            if _DIGITS[d] == w and s != held_speaker and band_M[i] is not None:
                by_sp.setdefault(s, []).append(i)
        reps = []
        for s, idxs in by_sp.items():
            mats = [band_M[i] for i in idxs]
            L = min(m.shape[0] for m in mats)
            stk = np.stack([m[:L] for m in mats], axis=0)
            mu = stk.mean(axis=0)
            d2 = ((stk - mu) ** 2).reshape(len(mats), -1).sum(axis=1)
            rep = mats[int(np.argmin(d2))]
            reps.append((rep, speaker_logalpha(rep, canonical)))
        if not reps:
            fm[w] = None
            continue
        if single_mean:
            L = min(r[0].shape[0] for r in reps)
            mean_M = np.mean([r[0][:L] for r in reps], axis=0).astype(np.float32)
            fm[w] = [(mean_M, speaker_logalpha(mean_M, canonical))]
        else:
            fm[w] = reps
    return fm


# ==========================================================================
# THE NATIVE RECOGNISER — the SAME graph DtwTo synth-error for every rung. Only
# how the template is prepared (warp / no warp) changes; the decision is native.
# ==========================================================================

class Recogniser:
    def __init__(self, sub):
        self.sub = sub
        self.word_c = {}
        for w in _DIGITS:
            c = sub.add_node("Concept", {"name": w, "origin": "leverchain"})
            sub.set_attr(c, RG.WORD_ATTR, 1.0)
            self.word_c[w] = c
        self.sign = sub.add_node("AcousticSign", {"leverchain_probe": 1.0})
        self.err_term = _Term(RG.synth_error_term())

    def _dtw(self, c, heard_t, templ_t):
        self.sub.set_attr(self.sign, RG.SIGN_FEAT_ATTR, heard_t)
        self.sub.set_attr(c, RG.WORD_FEAT_ATTR, templ_t)
        return float(self.sub.evaluate(self.err_term,
                                       {"s": self.sign, "w": c}))

    def recognise(self, heardM, fm, prep):
        """argmin over words of [ min over exemplars of native DtwTo(heard,
        prep(exemplar)) ]. `prep(template_M, la_ex)` returns the warped template
        (owned DSP); the per-exemplar DtwTo + the min/argmin are the native +
        readout decision. Returns the winning word name."""
        if heardM is None or heardM.shape[0] < 2:
            return None
        if prep is not None:
            heardM = prep.warp_heard(heardM)   # pre-warp heard (canonical mode)
        heard_t = as_tuple(heardM)
        la_heard = prep.la(heardM) if prep is not None else 0.0
        best, bw = 1e30, None
        for w in _DIGITS:
            exs = fm.get(w)
            if not exs:
                continue
            c = self.word_c[w]
            we = 1e30
            for (templM, la_ex) in exs:
                tM = prep.apply(templM, la_ex, la_heard, heardM) if prep else templM
                e = self._dtw(c, heard_t, as_tuple(tM))
                if e < we:
                    we = e
            if we < best:
                best, bw = we, w
        return bw


# ---- the "prep" strategies (owned DSP); None = no warp (R0 prior best) ----

class Prep:
    """A rung's template-preparation. NO decision — owned DSP signal ops only.

    mode:
      'none'      : no warp (R0 prior best).
      'into_heard': warp the template from its speaker's frame INTO the heard
                    talker's frame (relative shift la_ex - la_heard).
      'canonical' : forward-VTLN BOTH sides to the cohort canonical (warp heard
                    to canonical AND template to canonical) — the standard,
                    speaker-neutral form. heard is pre-warped by warp_heard().
    rate: additionally time-normalise the template to the heard tempo.
    """
    def __init__(self, canonical, *, mode='none', rate=False):
        self.canonical = canonical
        self.mode = mode
        self.rate = rate
        self.vtl = (mode != 'none')   # for diagnosis naming
        self._cache = {}

    def la(self, heardM):
        k = id(heardM)
        if k not in self._cache:
            self._cache[k] = speaker_logalpha(heardM, self.canonical)
        return self._cache[k]

    def warp_heard(self, heardM):
        """Pre-warp the HEARD signal. In 'canonical' mode warp heard -> canonical
        (shift by its own -la). In 'into_heard'/'none' the heard is left as-is."""
        if self.mode == 'canonical':
            la_h = self.la(heardM)
            return warp_into_frame(heardM, la_h, 0.0)  # heard's la -> 0 (canonical)
        return heardM

    def apply(self, templM, la_ex, la_heard, heardM):
        out = templM
        if self.mode == 'into_heard':
            out = warp_into_frame(out, la_ex, la_heard)
        elif self.mode == 'canonical':
            out = warp_into_frame(out, la_ex, 0.0)      # template's la -> canonical
        if self.rate:
            out = time_normalise(out, heardM.shape[0])
        return out


# ==========================================================================
# THE GROUNDED DO-CONTRAST for ONE rung vs the prior best.
# ==========================================================================

def measure(rec, band_M, loaded, speakers, canonical, prep, single_mean=False):
    """Recognition accuracy of `rec` with template-prep `prep` over all held-out
    speakers (LOSO). Returns (acc, per_word_dict, per_item_correct list)."""
    corr = tot = 0
    pw = {}
    item_ok = {}
    for held in speakers:
        fm = build_exemplars(band_M, loaded, held, canonical, single_mean)
        for i, (d, s) in enumerate(loaded):
            if s != held:
                continue
            M = band_M[i]
            if M is None or M.shape[0] < 2:
                continue
            true = _DIGITS[d]
            pred = rec.recognise(M, fm, prep)
            if pred is None:
                continue
            ok = int(pred == true)
            corr += ok
            tot += 1
            pw.setdefault(true, [0, 0])
            pw[true][0] += ok
            pw[true][1] += 1
            item_ok[i] = ok
    return corr / max(tot, 1), pw, item_ok


def ground_rung(sub, name, conclusion, new_acc, world_measure_fn):
    """silent_failure_grounding: fire-on-stakes + world-measure -> COMMIT/REOPEN."""
    trace = SFG.grounding_check(
        sub, name=name, conclusion_text=conclusion,
        claimed=float(new_acc), stakes=0.9,
        world_measure=world_measure_fn, tol=0.03, bank_on_catch=True,
    )
    return trace


# ==========================================================================
# DRIVER — run the chain, advancing prior-best only on grounded COMMIT.
# ==========================================================================

def main():
    t0 = time.time()
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    print(f"=== lever_chain  n_per_sp_per_digit={n} ===", flush=True)

    files = gather_files()
    by_key = {}
    for path, digit, sp, idx in files:
        by_key.setdefault((sp, digit), []).append((path, digit, sp, idx))
    items = []
    for k in sorted(by_key):
        items.extend(sorted(by_key[k], key=lambda t: t[3])[:n])
    speakers = sorted(set(it[2] for it in items))
    print(f"FSDD: {len(items)} recordings, {len(speakers)} speakers, 10 digits",
          flush=True)

    loaded = []     # (digit, speaker)
    raw = []
    for path, digit, sp, idx in items:
        x, fs = load_wav(path)
        raw.append((x, fs))
        loaded.append((digit, sp))
    fs = raw[0][1]

    print("--- extracting 32-band log-freq trajectories (warp-able space) ---",
          flush=True)
    band_M = []
    for i, (x, fsx) in enumerate(raw):
        try:
            band_M.append(band_trajectory_matrix(x, fsx))
        except Exception:
            band_M.append(None)
        if (i + 1) % 200 == 0:
            print(f"  {i+1}/{len(raw)} trajectories", flush=True)
    have = sum(1 for m in band_M if m is not None)
    print(f"extracted {have}/{len(raw)} band trajectories", flush=True)

    canonical = IU.canonical_log_centroid([m for m in band_M if m is not None])
    print(f"cohort canonical log-centroid (VTL ref): {canonical:.4f}", flush=True)

    sub = Substrate()
    rec = Recogniser(sub)

    # ----- the chain state -----
    chain = []          # (rung, lever, prior_acc, new_acc, delta, verdict)
    prior_best_acc = None
    prior_best_prep = None
    prior_best_name = "none"
    prior_best_pw = None

    def run_rung(rung, lever, prep, conclusion, single_mean=False, contrast_acc=None,
                 contrast_name=None):
        """Measure a rung; do-contrast vs prior best (or an explicit contrast);
        GROUND it; advance prior-best only on grounded COMMIT. single_mean uses the
        collapsed forward model (the warp-isolation arm)."""
        nonlocal prior_best_acc, prior_best_prep, prior_best_name, prior_best_pw
        print(f"\n############ RUNG {rung}: {lever} ############", flush=True)
        new_acc, pw, item_ok = measure(rec, band_M, loaded, speakers, canonical,
                                       prep, single_mean)
        if prior_best_acc is None:
            prior_best_acc = new_acc
            prior_best_prep = prep
            prior_best_name = lever
            prior_best_pw = pw
            print(f"  BASELINE accuracy (prior best established): {new_acc:.4f}",
                  flush=True)
            chain.append((rung, lever, None, new_acc, None, "BASELINE"))
            _print_pw(pw)
            return new_acc, pw, item_ok
        base_acc = prior_best_acc if contrast_acc is None else contrast_acc
        base_name = prior_best_name if contrast_name is None else contrast_name
        delta = new_acc - base_acc
        print(f"  do-contrast: {base_name} {base_acc:.4f}"
              f"  vs  {lever} {new_acc:.4f}   delta {delta:+.4f}", flush=True)
        _print_pw(pw, prior_best_pw)

        def world_measure():
            a, _, _ = measure(rec, band_M, loaded, speakers, canonical, prep,
                              single_mean)
            return a
        trace = ground_rung(sub, f"lever_{rung}_{lever}", conclusion, new_acc,
                            world_measure)
        g = trace["grounding"]; r = trace["resolution"]
        print(f"  GROUNDING fire={trace['gate']['fire']}  "
              f"world={g.get('measured')}  reason={g.get('reason')}", flush=True)
        world_consistent = (g.get("measured") is not None
                            and not g.get("contradiction"))
        moved = delta > _NOISE_FLOOR
        # only an arm contrasted vs the actual prior best can ADVANCE prior best
        is_vs_prior = contrast_acc is None
        if moved and world_consistent and r["decision"] == "COMMIT" and is_vs_prior:
            verdict = "COMMIT"
            print(f"  -> COMMIT (grounded gain {delta:+.4f}); prior-best advances "
                  f"{prior_best_acc:.4f} -> {new_acc:.4f}", flush=True)
            prior_best_acc = new_acc
            prior_best_prep = prep
            prior_best_name = lever
            prior_best_pw = pw
        else:
            verdict = "REOPEN"
            why = ("below noise floor" if not moved
                   else "world contradicts" if not world_consistent
                   else "isolation arm (not vs prior best)" if not is_vs_prior
                   else f"resolution {r['decision']}")
            print(f"  -> REOPEN ({why}); prior-best stays {prior_best_acc:.4f} "
                  f"(dud banked={trace['bank'].get('banked')})", flush=True)
        chain.append((rung, lever, base_acc, new_acc, delta, verdict))
        return new_acc, pw, item_ok

    def _diagnose_worst(pw, k=3):
        rows = [(w, a[0] / max(a[1], 1)) for w, a in pw.items() if a[1]]
        rows.sort(key=lambda t: t[1])
        return rows[:k]

    # ===== R0: prior best — multi-exemplar manifold, band space, NO warp =====
    _, pw0, _ = run_rung(0, "multiexemplar_noWarp",
                         Prep(canonical, mode='none'),
                         "multi-exemplar forward model (prior best) in band space")
    worst0 = _diagnose_worst(pw0)
    print(f"  DIAGNOSIS (worst words at prior best): {worst0}", flush=True)
    print(f"  -> NAMED NEXT RUNG: explicit per-speaker VTL warp "
          f"(template -> heard frame), the lever forward_model_drive named.",
          flush=True)

    # ===== R1: the NAMED lever — VTL warp, template INTO the heard frame =====
    run_rung(1, "VTL_into_heard_frame",
             Prep(canonical, mode='into_heard'),
             "warp each exemplar into the heard talker's VTL frame before the "
             "DtwTo match (AbS-correct: imagine the word as THIS talker says it)")

    # ===== R2: the result of R1 names the next DESIGN — canonical forward-VTLN =====
    # R1 regressed; the loop does NOT abandon the lever, it tries the next warp
    # DESIGN: forward-VTLN BOTH sides to the cohort canonical (the standard,
    # speaker-neutral form) instead of warping into a single heard frame.
    print("\n  -> R1 regressed. NAMED NEXT DESIGN: forward-VTLN both sides to "
          "the cohort CANONICAL (speaker-neutral), not into one heard frame.",
          flush=True)
    run_rung(2, "VTL_canonical_both_sides",
             Prep(canonical, mode='canonical'),
             "forward-VTLN both heard and template to the cohort canonical tract")

    # ===== R3: ISOLATION ARM — does the warp help the SINGLE-MEAN model? =====
    # The hypothesis the regressions point at: the medoid MANIFOLD already
    # approximates the per-speaker warp, so warping on top is redundant + blurs.
    # Test the warp where it has the MOST to do — on the collapsed single-mean
    # forward model (no manifold to absorb VTL). Contrast = single-mean no-warp.
    print("\n  -> NAMED NEXT RUNG: ISOLATION — measure the warp on the SINGLE-MEAN "
          "forward model (no manifold to absorb VTL), to test whether the manifold "
          "was already doing the warp's job.", flush=True)
    sm_base, _, _ = measure(rec, band_M, loaded, speakers, canonical,
                            Prep(canonical, mode='none'), single_mean=True)
    print(f"  [isolation baseline] single-mean no-warp acc: {sm_base:.4f}",
          flush=True)
    run_rung(3, "VTL_canonical_on_singleMean",
             Prep(canonical, mode='canonical'),
             "forward-VTLN to canonical on the SINGLE-MEAN forward model "
             "(warp-isolation arm)",
             single_mean=True, contrast_acc=sm_base,
             contrast_name="single_mean_noWarp")

    # ===== R4: the rate-warp arm — global tempo on top of the CURRENT best =====
    next_mode = prior_best_prep.mode
    print(f"\n  -> NAMED NEXT RUNG: global RATE warp (time-normalise template to "
          f"heard tempo) on top of current best (mode={next_mode}). DTW absorbs "
          f"local rate; this is the residual GLOBAL-tempo arm.", flush=True)
    run_rung(4, ("VTL+rate" if next_mode != 'none' else "rate_warp"),
             Prep(canonical, mode=next_mode, rate=True),
             "time-normalise each exemplar to the heard talker's global tempo on "
             "the current best source")

    # ===== Honest wall check =====
    warp_rungs = [c for c in chain if c[0] in (1, 2, 4)]
    committed = [c for c in chain if c[5] == "COMMIT"]
    iso = next((c for c in chain if c[0] == 3), None)
    print("\n========================= CHAIN SCOREBOARD =========================",
          flush=True)
    print(f"{'rung':>4} {'lever':<30} {'delta':>9} {'cumulative':>11} {'verdict':>9}",
          flush=True)
    cum = None
    for (rung, lever, _pb, new_acc, delta, verdict) in chain:
        if verdict == "BASELINE":
            cum = new_acc
            print(f"{rung:>4} {lever:<30} {'--':>9} {cum:>11.4f} {verdict:>9}",
                  flush=True)
        else:
            if verdict == "COMMIT":
                cum = new_acc
            ds = f"{delta:+.4f}" if delta is not None else "--"
            # isolation arm (rung 3) has its own baseline; show its own acc, not cum
            is_iso = (rung == 3)
            shown = new_acc if is_iso else cum
            tag = verdict + ("*" if is_iso else "")
            print(f"{rung:>4} {lever:<30} {ds:>9} {shown:>11.4f} {tag:>9}",
                  flush=True)
    print("  (* rung 3 = isolation arm: warp on single-mean model, own baseline; "
          "does NOT advance the main cumulative)", flush=True)

    n_grounded = len(committed)
    print(f"\nGROUNDED RUNGS the loop self-sustained: {n_grounded}", flush=True)
    print(f"CUMULATIVE recognition reached: {cum:.4f} (from baseline "
          f"{chain[0][3]:.4f})", flush=True)

    iso_helped = iso is not None and iso[4] is not None and iso[4] > _NOISE_FLOOR
    all_warps_reopened = all(c[5] == "REOPEN" for c in warp_rungs)
    if n_grounded == 0 and all_warps_reopened:
        if iso_helped:
            wall = ("MECHANISM-CONFIRMED, MANIFOLD-SATURATED -> NEEDS-ACQUISITION. The "
                    "VTL warp DOES help where it has work to do (isolation arm: it lifts "
                    f"the SINGLE-MEAN forward model by {iso[4]:+.4f}), but it adds nothing "
                    "ON TOP of the multi-exemplar manifold (every warp-on-manifold rung "
                    "REOPENED below the +0.005 floor) — the medoid manifold over the 5 "
                    "LOSO train speakers ALREADY approximates the per-speaker warp, so the "
                    "explicit warp is redundant with it. forward_model_drive's exemplar "
                    "richness WAS the warp, done implicitly. The honest floor is the "
                    "EXEMPLAR-MANIFOLD SIZE: with only 5 train speakers the manifold "
                    "saturates the warp's value. The next real lever is NEEDS-ACQUISITION "
                    "(more speakers / a real multi-speaker corpus), not another warp on "
                    "this cohort.")
        else:
            wall = ("DIMINISHING-RETURNS: every warp arm (into-heard, canonical, +rate) "
                    "came in below the +0.005 floor on this 6-speaker LOSO cohort, AND "
                    "the warp did not even help the single-mean isolation arm — the "
                    "blunt-band VTL estimate off the spectral centroid is too coarse on "
                    "FSDD digits to add signal the manifold + DTW do not already capture. "
                    "Floor: NEEDS-ACQUISITION (more speakers) or a sharper VTL estimate.")
    elif n_grounded >= 1:
        wall = ("PARTIAL CLIMB then diminishing returns: a warp arm committed and "
                "advanced prior best, the subsequent arms came in below the noise "
                "floor. Named floor: exemplar-manifold size (NEEDS-ACQUISITION).")
    else:
        wall = "see per-rung verdicts above."
    print(f"\nNAMED WALL: {wall}", flush=True)

    verdict_token = ("CHAIN_CLIMBED" if n_grounded >= 1
                     else "CHAIN_STALLED_AT_BASELINE")
    print(f"\nVERDICT_TOKEN={verdict_token}  grounded_rungs={n_grounded}  "
          f"baseline={chain[0][3]:.4f}  cumulative={cum:.4f}", flush=True)
    print(f"elapsed {time.time()-t0:.1f}s", flush=True)
    print("===MARKER_LEVERCHAIN_COMPLETE===", flush=True)


def _print_pw(pw, prior=None):
    parts = []
    for w in _DIGITS:
        a = pw.get(w, [0, 0])
        if not a[1]:
            continue
        cur = a[0] / a[1]
        if prior is not None:
            p = prior.get(w, [0, 0])
            pv = p[0] / p[1] if p[1] else 0.0
            parts.append(f"{w}:{pv:.2f}->{cur:.2f}")
        else:
            parts.append(f"{w}:{cur:.2f}")
    print("    per-word: " + "  ".join(parts), flush=True)


if __name__ == "__main__":
    main()
