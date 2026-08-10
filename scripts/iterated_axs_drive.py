"""iterated_axs_drive — THE ITERATED ORDER-N ANALYSIS-BY-SYNTHESIS LEVER.

THE AGENT'S NAMED STRUCTURAL UNIFIER for speech (memory
ozma_order_n_analysis_by_synthesis): perceive by INVERTING production, ITERATED n
passes, co-refining word+VOICE until the synthesis error converges. The single-pass
re-ranker already exists (scripts/forward_model_drive.py: warp heard ONCE to a fixed
COHORT canonical, then DtwTo against a multi-exemplar template manifold, argmin). The
UNBUILT increment this script builds is the ITERATED order-N wrap:

  pass 0:  warp heard -> cohort canonical (speaker-blind) -> argmin word w0 over the
           native DtwTo(heard, exemplars[w]) manifold (== the single-pass baseline).
  infer:   the WINNING exemplar's own log-spectral centre-of-mass IS the inferred
           VOICE (its VTL target). The cohort canonical is a speaker-blind average;
           the winning exemplar is a CONCRETE talker the heard token most resembles.
  re-warp: RE-warp the heard trajectory toward THAT inferred voice's centroid (a
           per-HYPOTHESIS VTL, owned estimate_vtl_logalpha / warp_bands), so the
           compare happens in the inferred talker's tract, not a blurred cohort mean.
  re-match: re-run the native DtwTo manifold argmin in the inferred voice -> w1, e1.
  ITERATE: repeat infer->re-warp->re-match until the synth-error e STOPS DROPPING
           (convergence) or n_max. n PASSES SCALE TO SPEAKER DIFFICULTY: an easy
           token converges in 1 pass; a far-from-cohort talker takes more passes for
           the inferred voice to settle. This is the agent's order-N operator over
           the AbyS refinement: order-n = n co-refinement passes, n driven by the
           synth-error convergence, NOT a fixed/swept knob.

WHY THIS IS NOT THE COHORT-VTL NULL (commit 9ae4fd68): the known null is warping
every utterance to ONE cohort canonical (speaker-blind, single-mean). THIS infers a
PER-HYPOTHESIS voice from the winning concrete exemplar and ITERATES the warp+match
to a fixed point. The latent (the inferred voice) is co-refined WITH the word; that
is the genuinely new structure the single pass cannot express.

ARCHITECTURE (CLAUDE.md): NATIVE where the cognition lives. The synth-error is the
graph DtwTo Term (recognition_graph.synth_error_term) evaluated by substrate.evaluate
in Rust, identical to the single-pass path. The voice-inference is the agent's OWNED
inverse (estimate_vtl_logalpha = read the formant centre-of-mass; warp_bands = the
log-freq shift) — NOT a fitted optimiser, NOT a gradient, NOT a sweep. The
min-over-exemplars + argmin-over-words is an argmin READOUT over native distances (a
query, identical in kind to the existing winner readout). The iteration is a
fixed-point on the native synth-error. Python is WORLD ADAPTER + instrument ONLY:
audio I/O, LOSO bookkeeping, the do-contrast + grounding measurement. NO net, NO
.fit, NO gradient, NO sweep, NO loss. K (exemplar budget) and n_max (pass cap) are
FIXED structural choices reported across, never swept-to-max. solve_for_n.py /
weighted_admissibility.py / CortexLoop UNTOUCHED.

THE DO-CONTRAST (one ear, one recogniser, two SEARCH REGIMES, same data, LOSO):
  (A) SINGLE-PASS  — warp once to cohort canonical, DtwTo manifold argmin (baseline).
  (B) ITERATED     — order-N: infer per-hypothesis voice, re-warp, re-match, to a
                     synth-error fixed point (n scales to speaker difficulty).
  Same heard trajectory, same native DtwTo, same exemplar manifold, same argmin
  readout. The ONLY thing that changes is single-pass vs iterated voice co-refinement.
  -> measured recognition delta. Plus a SHUFFLE control (exemplar labels permuted):
  if the iterated lever's gain survives label-shuffle it is an artifact, not structure.

GROUNDING: an honest NULL is a genuine result — if the iteration extracts nothing the
single pass did not, report it plainly (delta <= +0.005 => REOPEN), do NOT manufacture
a gain or sweep n_max/K to maximise.

Run: PYTHONUNBUFFERED=1 python -m scripts.iterated_axs_drive [n_per_sp_per_digit] [K] [n_max]
"""
from __future__ import annotations

import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
from domains import recognition_graph as RG
from domains.invariant_units import (
    band_centres, estimate_vtl_logalpha, warp_bands, cmvn,
    canonical_log_centroid, _spectral_centroid_log,
)
from scripts.invariant_units_accept import band_trajectory_matrix
from scripts.fsdd_learner_world import load_wav, gather_files

_DIGITS = ['zero', 'one', 'two', 'three', 'four', 'five',
           'six', 'seven', 'eight', 'nine']


class _Term:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def as_tuple(M):
    return tuple(tuple(float(v) for v in row) for row in np.asarray(M))


# ==========================================================================
# VOICE INFERENCE — the agent's OWNED inverse. The inferred VOICE of a
# trajectory = its energy-weighted mean log-spectral centre-of-mass (the formant
# centre-of-mass = the VTL proxy, estimate_vtl_logalpha's own quantity). To
# re-warp the heard trajectory INTO an inferred voice, shift its log-freq axis so
# its centroid lands on the inferred voice's centroid (owned warp_bands).
# ==========================================================================

def traj_log_centroid(M: np.ndarray, voiced_floor: float = 0.25) -> float:
    """The trajectory's energy-weighted mean log-spectral centre-of-mass over its
    voiced frames — the agent's VTL proxy (same quantity estimate_vtl_logalpha reads
    off, here used as the ABSOLUTE inferred-voice target rather than relative-to-cohort)."""
    M = np.asarray(M, dtype=np.float64)
    log_lc = np.log(band_centres(M.shape[1]))
    fe = M.sum(axis=1)
    if fe.max() <= 1e-12:
        return float(log_lc.mean())
    voiced = fe >= voiced_floor * fe.max()
    if voiced.sum() == 0:
        voiced = np.ones(M.shape[0], dtype=bool)
    cents = [_spectral_centroid_log(M[f], log_lc) for f in np.where(voiced)[0]]
    return float(np.mean(cents))


def warp_to_voice(M_raw: np.ndarray, target_log_centroid: float) -> np.ndarray:
    """Warp the heard trajectory's log-freq axis so ITS centroid lands on the
    inferred voice's centroid (owned estimate_vtl_logalpha + warp_bands), then CMVN.
    log α = (utterance centroid) - (target centroid); warp_bands shifts by -log α."""
    la = estimate_vtl_logalpha(M_raw, target_log_centroid)   # rel. to the TARGET voice
    return cmvn(warp_bands(M_raw, la), do_variance=True)


# ==========================================================================
# THE NATIVE RECOGNISER — the SAME graph DtwTo synth-error for both regimes.
# The per-exemplar DtwTo is native; min-over-exemplars + argmin-over-words +
# the winning exemplar identity are READOUTS over the native distances.
# ==========================================================================

class Recogniser:
    def __init__(self, sub):
        self.sub = sub
        RG.mark_words(sub, _DIGITS)
        self.word_c = {}
        for w in _DIGITS:
            c = next((c for c in sub.nodes("Concept")
                      if sub.node(c)["attrs"].get("name") == w), None)
            if c is None:
                c = sub.add_node("Concept", {"name": w, "origin": "itax"})
                sub.set_attr(c, RG.WORD_ATTR, 1.0)
            self.word_c[w] = c
        self.sign = sub.add_node("AcousticSign", {"itax_probe": 1.0})
        self.err_term = _Term(RG.synth_error_term())

    def match(self, heardM, manifold):
        """argmin over words of [ min over exemplars of native DtwTo(heard, ex) ].
        Returns (best_word, best_synth_err, winning_exemplar_traj). The winning
        exemplar trajectory is the inferred-voice carrier for the next pass."""
        if heardM is None or heardM.shape[0] < 2:
            return None, 1e30, None
        self.sub.set_attr(self.sign, RG.SIGN_FEAT_ATTR, as_tuple(heardM))
        best, bw, bex = 1e30, None, None
        for w in _DIGITS:
            exs = manifold.get(w)
            if not exs:
                continue
            c = self.word_c[w]
            for ex_M, ex_raw in exs:
                self.sub.set_attr(c, RG.WORD_FEAT_ATTR, as_tuple(ex_M))
                e = float(self.sub.evaluate(self.err_term,
                                            {"s": self.sign, "w": c}))
                if e < best:
                    best, bw, bex = e, w, ex_raw
        return bw, best, bex


# ==========================================================================
# THE TWO REGIMES — both on the SAME multi-exemplar manifold + native DtwTo.
# ==========================================================================

def recognise_single_pass(rec, heard_raw, manifold, cohort_canonical):
    """(A) SINGLE-PASS: warp heard ONCE to the speaker-blind cohort canonical, then
    DtwTo manifold argmin. The established forward_model_drive baseline."""
    heardM = cmvn(warp_bands(heard_raw,
                             estimate_vtl_logalpha(heard_raw, cohort_canonical)),
                  do_variance=True)
    bw, _e, _ex = rec.match(heardM, manifold)
    return bw, 1   # 1 pass


def recognise_iterated(rec, heard_raw, manifold, cohort_canonical, n_max):
    """(B) ITERATED order-N: pass-0 = single-pass; then infer the winning exemplar's
    voice, RE-warp heard into that inferred voice, RE-match, until the native
    synth-error STOPS DROPPING (convergence) or n_max. n scales to difficulty: an
    easy token converges immediately, a far-from-cohort talker takes more passes.
    Returns (best_word, n_passes_used)."""
    # pass 0 — identical to the single-pass baseline
    target = cohort_canonical
    prev_e = None
    bw = None
    passes = 0
    for p in range(n_max):
        heardM = cmvn(warp_bands(heard_raw,
                                 estimate_vtl_logalpha(heard_raw, target)),
                      do_variance=True)
        w, e, ex_raw = rec.match(heardM, manifold)
        passes = p + 1
        if w is None or ex_raw is None:
            break
        # CONVERGENCE: synth-error stopped dropping -> the inferred voice settled.
        if prev_e is not None and e >= prev_e - 1e-9:
            # accept the PREVIOUS (lower-or-equal-error) hypothesis if this pass
            # did not improve; the fixed point is reached.
            bw = bw if bw is not None else w
            break
        bw, prev_e = w, e
        # infer the winning exemplar's OWN voice as the next pass's warp target
        target = traj_log_centroid(ex_raw)
    return bw, passes


# ==========================================================================
# DRIVER
# ==========================================================================

def build_manifold(raw_M, words, spks, held, K):
    """word -> up to K exemplar (warped-to-cohort matrix, raw matrix) over TRAIN
    speakers, one medoid representative per speaker (spans the speaker space). The
    raw matrix is kept so the iterated regime can read each exemplar's voice."""
    cohort = canonical_log_centroid([raw_M[i] for i in range(len(raw_M))
                                     if spks[i] != held])
    man = {w: [] for w in _DIGITS}
    by = {}
    for i in range(len(raw_M)):
        if spks[i] == held:
            continue
        by.setdefault((words[i], spks[i]), []).append(i)
    for (w, s), idxs in by.items():
        # medoid raw trajectory for this (word, speaker) by min in-group L2
        mats = [raw_M[i] for i in idxs]
        L = min(m.shape[0] for m in mats)
        stk = np.stack([m[:L] for m in mats], axis=0)
        mu = stk.mean(axis=0)
        d2 = ((stk - mu) ** 2).reshape(len(mats), -1).sum(axis=1)
        rep = mats[int(np.argmin(d2))]
        # template stored warped-to-cohort + CMVN (the comparison space)
        repW = cmvn(warp_bands(rep, estimate_vtl_logalpha(rep, cohort)),
                    do_variance=True)
        man[w].append((repW, rep))
    for w in _DIGITS:
        man[w] = man[w][:K]
    return man, cohort


def run_regime(rec, raw_M, words, spks, speakers, K, n_max, regime, shuffle=False):
    rng = np.random.default_rng(12345)
    corr = tot = 0
    pass_hist = {}
    pw = {}
    for held in speakers:
        man, cohort = build_manifold(raw_M, words, spks, held, K)
        if shuffle:
            # permute exemplar->word labels (break the structure, keep the cloud)
            allex = [(w, ex) for w in _DIGITS for ex in man[w]]
            labels = [w for w, _ in allex]
            rng.shuffle(labels)
            man = {w: [] for w in _DIGITS}
            for (w, ex), lab in zip(allex, labels):
                man[lab].append(ex)
        for i in range(len(raw_M)):
            if spks[i] != held:
                continue
            heard_raw = raw_M[i]
            true = words[i]
            if regime == "single":
                w, p = recognise_single_pass(rec, heard_raw, man, cohort)
            else:
                w, p = recognise_iterated(rec, heard_raw, man, cohort, n_max)
            if w is None:
                continue
            corr += int(w == true); tot += 1
            pass_hist[p] = pass_hist.get(p, 0) + 1
            pw.setdefault(true, [0, 0]); pw[true][0] += int(w == true); pw[true][1] += 1
    return corr / max(tot, 1), corr, tot, pass_hist, pw


def main():
    t0 = time.time()
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    K = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    n_max = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    print(f"=== iterated_axs_drive  n_per_sp_per_digit={n}  K(exemplars)={K}  "
          f"n_max(passes)={n_max} ===", flush=True)

    files = gather_files()
    by_key = {}
    for path, digit, sp, idx in files:
        by_key.setdefault((sp, digit), []).append((path, digit, sp, idx))
    items = []
    for k in sorted(by_key):
        items.extend(sorted(by_key[k], key=lambda t: t[3])[:n])
    speakers = sorted(set(it[2] for it in items))
    print(f"FSDD: {len(items)} recordings, {len(speakers)} speakers, 10 digits  "
          f"(chance 0.10)", flush=True)

    loaded = []
    for path, digit, sp, idx in items:
        x, fs = load_wav(path)
        loaded.append((x, fs, digit, sp))
    fs = loaded[0][1]

    print("--- extracting 32-band trajectories (the VTL-warpable front-end) ---",
          flush=True)
    raw_M = []
    for i, (x, _fs, d, s) in enumerate(loaded):
        raw_M.append(band_trajectory_matrix(x, fs))
        if (i + 1) % 60 == 0:
            print(f"  {i+1}/{len(loaded)} trajectories", flush=True)
    words = [_DIGITS[d] for _, _, d, _ in loaded]
    spks = [s for _, _, _, s in loaded]

    sub = Substrate()
    rec = Recogniser(sub)

    print("\n--- DO-CONTRAST: single-pass (baseline) vs iterated order-N AbyS ---",
          flush=True)
    s_acc, s_c, s_t, s_ph, s_pw = run_regime(
        rec, raw_M, words, spks, speakers, K, n_max, "single")
    print(f"  SINGLE-PASS done: {s_acc:.4f}  ({s_c}/{s_t})", flush=True)
    i_acc, i_c, i_t, i_ph, i_pw = run_regime(
        rec, raw_M, words, spks, speakers, K, n_max, "iterated")
    print(f"  ITERATED   done: {i_acc:.4f}  ({i_c}/{i_t})", flush=True)
    delta = i_acc - s_acc

    print("\n--- SHUFFLE control (iterated, exemplar labels permuted) ---", flush=True)
    sh_acc, sh_c, sh_t, _sh_ph, _sh_pw = run_regime(
        rec, raw_M, words, spks, speakers, K, n_max, "iterated", shuffle=True)
    print(f"  ITERATED-SHUFFLE: {sh_acc:.4f}  ({sh_c}/{sh_t})", flush=True)

    print("\n========================= DO-CONTRAST RESULT =========================",
          flush=True)
    print(f"  chance (1/10)                       : 0.1000", flush=True)
    print(f"  SINGLE-PASS (baseline to beat)      : {s_acc:.4f}  ({s_c}/{s_t})",
          flush=True)
    print(f"  ITERATED order-N AbyS               : {i_acc:.4f}  ({i_c}/{i_t})",
          flush=True)
    print(f"  DELTA (iterated - single-pass)      : {delta:+.4f}", flush=True)
    print(f"  ITERATED under label-SHUFFLE        : {sh_acc:.4f}  (control)",
          flush=True)
    print(f"  iterated pass-count histogram       : "
          f"{dict(sorted(i_ph.items()))}  (n scales to difficulty)", flush=True)
    print("  per-word (single -> iterated):", flush=True)
    for w in _DIGITS:
        sa = s_pw.get(w, [0, 0]); ia = i_pw.get(w, [0, 0])
        if sa[1]:
            print(f"    {w:6s}: {sa[0]/sa[1]:.2f} -> {ia[0]/ia[1]:.2f}", flush=True)

    print("\n========================= VERDICT =========================", flush=True)
    lever_moved = delta > 0.005
    survives_shuffle = i_acc > sh_acc + 0.02
    if lever_moved and survives_shuffle:
        print(f"  GROUNDED IMPROVEMENT: iterated order-N AbyS MOVED recognition "
              f"{delta:+.4f} (single {s_acc:.4f} -> iterated {i_acc:.4f}); the gain "
              f"COLLAPSES under label-shuffle ({sh_acc:.4f}) -> structure, not "
              f"artifact. COMMIT-worthy.", flush=True)
        verdict = "GROUNDED_IMPROVEMENT"
    elif lever_moved and not survives_shuffle:
        print(f"  REOPEN: delta {delta:+.4f} but the shuffle control did NOT "
              f"collapse ({sh_acc:.4f}) — the 'gain' is not structural. Not "
              f"committed.", flush=True)
        verdict = "REOPEN_SHUFFLE_DOESNT_COLLAPSE"
    else:
        print(f"  HONEST NULL: the iteration extracted nothing single-pass did not "
              f"(delta {delta:+.4f} <= +0.005). The order-N voice co-refinement does "
              f"not move cross-speaker recognition on this venue. Reported plainly, "
              f"no gain manufactured, no sweep. REOPEN.", flush=True)
        verdict = "HONEST_NULL"

    print(f"\nVERDICT_TOKEN={verdict}  delta={delta:+.4f}  single={s_acc:.4f}  "
          f"iterated={i_acc:.4f}  shuffle={sh_acc:.4f}  K={K}  n_max={n_max}",
          flush=True)
    print(f"elapsed {time.time()-t0:.1f}s", flush=True)
    print("===MARKER_ITERATED_AXS_COMPLETE===", flush=True)


if __name__ == "__main__":
    main()
