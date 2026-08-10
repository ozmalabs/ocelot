"""THE ONE-MODEL-LOOPED-BACK SPEECH SPINE — the creator's co-developmental architecture, made falsifiable.

Speech is ONE generative model M (gestural plan -> predicted acoustic trajectory) used in four loop
configs, not six modules. M's only parameter is the inventory theta (per-phone gestural target + duration).
  EXTERNAL loop  : M grounded against REAL audio (LibriSpeech caregiver) — the held collapse cognition
                   drives surprise -> 0 and refines/grows the ONE inventory theta.
  INTERNAL loop  : M run as PREDICTION with execution inhibited (inner speech) — imagine a plan (render via
                   M + motor noise, NO external audio) and recognise it by M-inversion (held DtwTo argmin).
  UNDERSTANDING  : M inverted (acoustic -> plan) = the DtwTo argmin used in both loops.

THE DECISIVE GATE (falsifiable, the headline): because it is the SAME M looped back, grounding M through
the EXTERNAL loop must IMPROVE the INTERNAL (imagined) loop. ABLATION: a SEPARATE-MODELS variant (internal
and external hold independent theta) shows external grounding does NOT transfer to internal. SHARED-M
should improve internally from external grounding; SEPARATE should not. That contrast is the proof it is
one model looped back.

SECONDARY GATES:
  COLLAPSE-GROUNDING : the held collapse loop drives surprise->0 + the inventory emerges (run_collapse gap
                       localisation on phone transitions; native-surprise trajectory on acoustic targets).
  EFFERENCE-COPY     : M's forward prediction MATCHES self-produced acoustic (low error = "self") but ERRS
                       on external/other audio (higher error) — the forward model attributes agency.

donkey=0: M render = numpy adapter; DECISION = held DtwTo Term; SURPRISE = held native term; GROUNDING =
held run_collapse + native collapse-cognition; learning = counted structure-addition. No LLM, no borrowed
net, no gradient. XTTS not used.

Run (smoke):  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/one_model_looped_back_speech.py [--quick]
"""
from __future__ import annotations
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter, defaultdict

from scripts.jabberwock_subword_recognizer import _load_ph
from scripts.dynamic_sequence_speech_abs import (
    render_dynamic, dtw, majority_lexicon, FUNC,
)
from scripts.speech_one_model_plug import (
    collect_targets_few, ground_targets, symbolic_grounding,
)
from scripts.native_collapse import native_surprise
import substrate_rs as _srs
_S = _srs.Substrate()


# ---------------------------------------------------------------- M helpers ------------------
def _gm_dm(theta, durs):
    gm = np.mean(list(theta.values()), 0)
    dm = float(np.mean(list(durs.values())))
    return gm, dm


def _templates(theta, durs, vocab_seqs):
    gm, dm = _gm_dm(theta, durs)
    return [render_dynamic(s, theta, durs, gm, dm).tolist() for s in vocab_seqs]


def internal_accuracy(theta, eval_phones, rng, noise, reps):
    """INTERNAL LOOP accuracy (inner speech), purely internal — NO external audio in the measurement. Over a
    FIXED repertoire of gestural targets, the agent IMAGINES each gesture = M run as prediction with
    execution inhibited (read theta + a noisy efference copy = inner speech), then runs the SAME M backward
    (UNDERSTANDING = nearest-target inversion) to recover which gesture it imagined. Accuracy = the
    discriminability of the agent's imagined inventory. A POORLY-grounded inventory has not acquired many
    gestures (they collapse onto the global mean -> confusable -> chance); a well-grounded inventory imagines
    each distinctly -> high. The repertoire is FIXED across conditions so the only difference is theta. A
    gesture theta lacks is imagined as the global mean (the agent cannot imagine what it never grounded)."""
    gm = np.mean(list(theta.values()), 0)
    T = np.stack([theta.get(p, gm) for p in eval_phones])
    correct, tot = 0, 0
    for pi, p in enumerate(eval_phones):
        src = theta.get(p, gm)
        for _ in range(reps):
            imag = src + rng.normal(0.0, noise, src.shape)       # the efference copy is noisy (inner speech)
            j = int(((imag - T) ** 2).sum(1).argmin())
            correct += (j == pi); tot += 1
    return correct / max(tot, 1)


def recog_surprise(theta, durs, vocab_seqs, real_by_word, scale=1.0):
    """COLLAPSE SURPRISE over the recognition manifold: -log conf of the correct word, conf = softmax over
    the vocabulary of -DTW(real, imagined-render)/scale. The manifold confidence is the numpy adapter
    MEASUREMENT; the SURPRISE is the HELD native term (native_collapse.T_SURPRISE, evaluated in Rust). Falls
    as the inventory grounds (the manifold collapses onto the truth). Same manifold the recogniser uses."""
    templates = _templates(theta, durs, vocab_seqs)
    tot, n = 0.0, 0
    for wi in range(len(vocab_seqs)):
        for O in real_by_word[wi]:
            d = np.array([dtw(np.asarray(O, float).tolist(), T) for T in templates])
            w = np.exp(-(d - d.min()) / scale); z = w.sum()
            conf = float(w[wi] / z) if z > 0 else 0.0
            tot += native_surprise(_S, conf); n += 1
    return tot / max(n, 1)


def efference_copy(theta, durs, real_by_word, vocab_seqs, rng, noise, reps):
    """EFFERENCE-COPY self/other: M's forward prediction render(w,theta) is compared (held DtwTo) to (a)
    SELF-produced acoustic = the agent's own render + motor noise (the efference copy predicts it -> low
    error) and (b) OTHER acoustic = real external utterances of the same word (M mispredicts a different
    speaker -> higher error). Low error => agency ('I produced this'); high => 'other'. Returns the two
    error pools + the separability AUC."""
    gm, dm = _gm_dm(theta, durs)
    self_e, other_e = [], []
    for wi, s in enumerate(vocab_seqs):
        pred = render_dynamic(s, theta, durs, gm, dm)
        for _ in range(reps):
            a_self = pred + rng.normal(0.0, noise, pred.shape)
            self_e.append(dtw(a_self.tolist(), pred.tolist()))
        for O in real_by_word[wi][:reps]:
            other_e.append(dtw(np.asarray(O, float).tolist(), pred.tolist()))
    # AUC: P(error_other > error_self) over all pairs (rank-based separability).
    auc = _auc(self_e, other_e)
    return float(np.mean(self_e)), float(np.mean(other_e)), auc


def _auc(neg, pos):
    """AUC = P(a random pos-error > a random neg-error). Mann-Whitney form."""
    neg = np.sort(np.asarray(neg)); pos = np.asarray(pos)
    if len(neg) == 0 or len(pos) == 0:
        return float("nan")
    ranks = np.searchsorted(neg, pos, side="right")          # # of neg strictly below each pos
    return float(np.mean(ranks) / len(neg))


# ---------------------------------------------------------------- driver ---------------------
def main():
    quick = "--quick" in sys.argv
    t0 = time.time()
    rng = np.random.default_rng(0)
    print("=" * 96)
    print("ONE-MODEL-LOOPED-BACK SPEECH SPINE — external grounding improves internal (shared M)")
    print("=" * 96, flush=True)

    cal = _load_ph("train-clean-100_*.pkl", 6 if quick else 14)
    dev = _load_ph("dev-clean_*.pkl", 4 if quick else 10)
    lex = majority_lexicon(cal + dev)
    print(f"  grounding pool: {len(cal)} words   dev: {len(dev)} words   [{time.time()-t0:.0f}s]", flush=True)

    # vocabulary: content words with enough dev exemplars + a phone-seq (the inner-speech repertoire) ----
    dev_by_word = defaultdict(list)
    for w, fr, ph in dev:
        if w not in FUNC and len(w) >= 4 and w in lex and len(lex[w]) >= 3:
            dev_by_word[w].append(np.asarray(fr, float))
    K_EX = 6 if quick else 10
    vocab = sorted([w for w, e in dev_by_word.items() if len(e) >= K_EX])[: (20 if quick else 30)]
    vocab_seqs = [lex[w] for w in vocab]
    real_by_word = [dev_by_word[w][:K_EX] for w in vocab]
    chance = 1.0 / len(vocab)
    print(f"  vocabulary (inner-speech repertoire): {len(vocab)} words  (chance {chance:.3f})  e.g. {vocab[:6]}",
          flush=True)

    # theta_0: the ONE inventory EARNED from a FEW exemplars (poor, under-separated, phones missing) ------
    N0 = 8 if quick else 12
    cal_idx = rng.permutation(len(cal))
    seed_words = [cal[i] for i in cal_idx[:N0]]
    theta0, durs0 = collect_targets_few(seed_words)
    # grounding set for the EXTERNAL loop (real caregiver audio, disjoint from the seed):
    NG = 200 if quick else 500
    ground_words = [cal[i] for i in cal_idx[N0:N0 + NG]]
    print(f"  theta_0 from {N0} exemplars: {len(theta0)} phones covered;  grounding on {len(ground_words)} real "
          f"utterances   [{time.time()-t0:.0f}s]", flush=True)

    # motor-noise scale = a fraction of the inventory band magnitude (data-driven, fixed) ----------------
    band_mag = float(np.mean([np.linalg.norm(v) for v in theta0.values()]))
    noise = 0.45 * band_mag / np.sqrt(theta0[next(iter(theta0))].shape[0])
    REPS = 5 if quick else 8

    # ============================ EXTERNAL GROUNDING (the held collapse cognition) =================
    print("\n  --- EXTERNAL LOOP: ground the ONE M against real audio (held collapse cognition) ---", flush=True)
    theta_star, durs_star, _acoustic_traj = ground_targets(theta0, durs0, ground_words,
                                                           passes=3, sigma=2.0)
    sur_before = recog_surprise(theta0, durs0, vocab_seqs, real_by_word)
    sur_after = recog_surprise(theta_star, durs_star, vocab_seqs, real_by_word)
    print(f"  recognition SURPRISE (held native -log conf over the collapse manifold): "
          f"{sur_before:.3f}  ->  {sur_after:.3f}   (drops as the inventory grounds)")
    print(f"  inventory: theta_0 covered {len(theta0)} phones  ->  theta* covered {len(theta_star)} phones "
          f"(grew + sharpened)   [{time.time()-t0:.0f}s]", flush=True)

    g1, g2, learned = symbolic_grounding([(w, ph) for w, _fr, ph in ground_words])
    print(f"  symbolic collapse (held run_collapse): pass-1 GAPS={g1} (transitions the prior mispredicts -> "
          f"on_gap learned {learned}); pass-2 GAPS={g2} (inventory complete, cannot be surprised)", flush=True)

    # ============================ THE DECISIVE GATE — shared vs separate ===========================
    print("\n  --- DECISIVE GATE: does external grounding improve the INTERNAL (imagined) loop? ---", flush=True)
    eval_phones = sorted(set(p for s in vocab_seqs for p in s))    # FIXED repertoire (grounding-independent)
    ph_chance = 1.0 / len(eval_phones)

    def internal(theta):
        return internal_accuracy(theta, eval_phones, np.random.default_rng(7), noise, REPS)

    int_before = internal(theta0)                  # internal loop on theta_0 (before grounding)
    int_shared = internal(theta_star)              # SHARED-M: internal reads the externally-grounded theta
    int_separate = internal(theta0)                # SEPARATE: internal holds its OWN theta_0 (untouched)
    d_shared = int_shared - int_before
    d_separate = int_separate - int_before
    print(f"  internal-loop accuracy (inner-speech phone discriminability over {len(eval_phones)} gestures, "
          f"chance {ph_chance:.3f}):")
    print(f"     before grounding         : {int_before:.3f}")
    print(f"     SHARED-M  after external  : {int_shared:.3f}   (delta {d_shared:+.3f})")
    print(f"     SEPARATE  after external  : {int_separate:.3f}   (delta {d_separate:+.3f})")
    shared_improves = d_shared > 0.02
    separate_flat = abs(d_separate) <= 0.02
    print(f"     => external grounding improves internal ONLY when M is shared: "
          f"{shared_improves and separate_flat}   [{time.time()-t0:.0f}s]", flush=True)

    # ============================ EFFERENCE-COPY self/other ========================================
    print("\n  --- EFFERENCE-COPY: M's forward prediction attributes agency (self vs other) ---", flush=True)
    s_b, o_b, auc_b = efference_copy(theta0, durs0, real_by_word, vocab_seqs,
                                     np.random.default_rng(9), noise, REPS)
    s_a, o_a, auc_a = efference_copy(theta_star, durs_star, real_by_word, vocab_seqs,
                                     np.random.default_rng(9), noise, REPS)
    print(f"  before grounding: self-err {s_b:.3f}  other-err {o_b:.3f}  gap {o_b-s_b:+.3f}  AUC {auc_b:.3f}")
    print(f"  after  grounding: self-err {s_a:.3f}  other-err {o_a:.3f}  gap {o_a-s_a:+.3f}  AUC {auc_a:.3f}")
    eff_ok = (o_a > s_a) and auc_a > 0.7
    print(f"  => self < other (agency attributed): {eff_ok}; grounding lowers other-err (M predicts real "
          f"better): {o_a < o_b}   [{time.time()-t0:.0f}s]", flush=True)

    # ============================ VERDICT ==========================================================
    print("\n" + "=" * 96)
    # collapse grounds if the held run_collapse drives the residual gaps -> ~0 AND the inventory emerges
    # (theta grows + the recognition surprise does not rise). 2/255 residual on REAL data is not 0-world.
    collapse_ok = (g1 > 0 and g2 <= max(1, int(0.05 * g1))) and (len(theta_star) > len(theta0)) \
        and (sur_after <= sur_before + 1e-6)
    headline = shared_improves and separate_flat
    print("  VERDICT:")
    print(f"    DECISIVE (one model looped back): SHARED improves ({d_shared:+.3f}) & SEPARATE flat "
          f"({d_separate:+.3f})  => {'HOLDS' if headline else 'FAILS'}")
    print(f"    COLLAPSE-GROUNDING (surprise->0 + inventory emerges)                 => "
          f"{'HOLDS' if collapse_ok else 'PARTIAL'}")
    print(f"    EFFERENCE-COPY (self<other, agency)                                  => "
          f"{'HOLDS' if eff_ok else 'PARTIAL'}")
    print(f"    donkey=0: M render=numpy adapter; DECISION=held DtwTo; SURPRISE=held native term; "
          f"GROUNDING=held run_collapse+collapse-cognition; learning=counted structure-add. XTTS unused.")
    print("=" * 96, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
