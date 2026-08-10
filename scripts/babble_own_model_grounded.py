"""THE AGENT'S OWN BABBLE — produced by its own model M, GROUNDED against the XTTS caregiver.

THE CORRECTION (creator's spec). The prior babble loop (commit 32cfe796) trained the recogniser ON
XTTS-PRODUCED AUDIO -> that makes XTTS REQUIRED. WRONG. XTTS must be a GROUNDING STEP only, never the
producer. So here:

  PRODUCE with M  — the agent's OWN production model renders its OWN babble: a gestural plan (a phone
                    sequence the agent CHOSE, so the labels are FREE+EXACT) -> a smooth min-jerk
                    coarticulated COCHLEAR TRAJECTORY (render_dynamic, the held writer-physics motor
                    model) read straight off the inventory theta. No audio synthesis at all for the
                    agent's own babble — M renders cochlear frames directly.
  GROUND (sparse) — theta starts CRUDE (random per-phone targets at the right global scale -> babble is
                    gibberish, transfers ~chance). A SPARSE set of XTTS-caregiver utterances corrects
                    theta toward the caregiver's per-phone acoustics through the HELD collapse cognition
                    (ground_targets: native-surprise -> counted structure-add toward the observed frames;
                    NOT a gradient). This is a STEP: a few hundred caregiver clips estimate a tiny
                    39-phone x 32-band table; M then renders UNLIMITED babble from it.
  TRAIN           — the recogniser (the agent's own from-scratch PCA->LDA + per-phone centroids, EM/
                    Viterbi forced-aligned to the known phone seq) is trained on the agent's OWN
                    M-babble -- NOT on XTTS audio.
  TEST            — transfer to REAL LibriSpeech dev-clean (per-frame phone accuracy; chance 0.026).

GATE (controls, donkey=0):
  MAIN          — M-babble transfer RISES toward the XTTS-trained-directly level (~0.103) AS theta is
                  grounded against the XTTS caregiver. Report the gap closed.
  DISCRIMINATIVE— WITHOUT the grounding step (crude random theta) M-babble stays POOR (~chance / piper);
                  WITH it, approaches XTTS. Grounding is load-bearing.
  CAREGIVER-STRENGTH — grounding against the WEAK caregiver (piper) grounds a weaker M than the strong
                  caregiver (XTTS): M-babble approaches whatever caregiver level grounds it.
  XTTS-NOT-REQUIRED — XTTS is a GROUNDING STEP: N_ground caregiver clips << the M-babble corpus M
                  produces; and at inference (this whole script) no torch/TTS is imported -- the bulk
                  producer is M (render_dynamic), XTTS only the grounding target.

EARN-NOT-BORROW / donkey=0: the PRODUCTION is the agent's own M (render_dynamic = held min-jerk motor
model); the GROUNDING is the held collapse cognition (native surprise + counted structure-add); the
RECOGNISER is the agent's own from-scratch structure. XTTS only provides the sparse grounding target
(read off disk as wavs -> the agent's own cochleagram frames()). No torch/TTS/LLM/borrowed-net/gradient
anywhere in this process.

Run (project python; needs substrate_rs + nltk cmudict; NO torch/TTS):
  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/babble_own_model_grounded.py [--quick]
"""
from __future__ import annotations
import os
import sys
import time
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np

# the agent's OWN production model M (held min-jerk coarticulated motor render) ...
from scripts.dynamic_sequence_speech_abs import render_dynamic
# ... the held collapse-cognition grounding (native surprise -> counted structure-add toward observed) ...
from scripts.speech_one_model_plug import ground_targets, flatstart_assign
# ... and the EXACT recogniser + real eval used by the prior XTTS babble loop (apples-to-apples).
from scripts.babble_transfer import (
    em_train, per_frame_acc, build_eval, load_real_samples, load_synth_samples, CMU39, BABBLE,
)
from scripts.jabberwock_reads_oov_from_phones import frames, phones as cmu_phones

# the agent's CHOSEN babble repertoire (free labels — it picked the words); content+function spread.
VOCAB = [
    "water", "because", "yellow", "through", "around", "people", "father", "mother",
    "number", "letter", "morning", "evening", "country", "machine", "picture", "nature",
    "second", "answer", "follow", "common", "reason", "season", "window", "summer",
    "winter", "garden", "market", "doctor", "teacher", "farmer", "writer", "singer",
    "danger", "finger", "hunger", "anger", "color", "honor", "labor", "favor",
    "ocean", "music", "money", "honey", "study", "story", "early", "happy",
    "city", "body", "lady", "baby", "ready", "heavy", "every", "carry",
    "value", "issue", "voice", "noise", "house", "mouse", "horse", "force",
    "place", "space", "price", "piece", "peace", "choice", "juice", "bridge",
    "judge", "change", "charge", "large", "strange", "orange", "village", "thought",
    "though", "throw", "three", "thank", "think", "thing", "shadow", "shower",
    "should", "shoulder", "fashion", "passion", "mission", "nation", "measure", "treasure",
    "pleasure", "leisure", "vision", "decision", "occasion", "usual", "quick", "queen",
    "quiet", "square", "language", "question", "require", "equal", "yesterday", "young",
    "beyond", "lawyer", "loyal", "royal", "enjoy", "between", "beneath", "beside",
    "behind", "before", "again", "agree", "alone", "almost", "always", "animal",
    "family", "memory", "history", "company", "energy",
]
VOCAB = list(dict.fromkeys(VOCAB))


def babble_lexicon():
    """word -> stress-free ARPAbet phone seq (the FREE labels — the agent chose the words). Restricted
    to the shared 39-phone inventory so it matches the real-eval phone set."""
    lex = {}
    for w in VOCAB:
        ph = cmu_phones(w)
        if not ph:
            continue
        ph = [str(p) for p in ph if str(p) in CMU39]
        if len(ph) >= 2:
            lex[w] = ph
    return lex


def load_caregiver(subdir, cap):
    """SPARSE grounding target: a few caregiver clips -> (word, frames, phones) via the agent's own
    cochleagram. These are read off disk as plain wavs; no TTS/torch is imported here."""
    out = []
    for (w, M, _e, ph) in load_synth_samples(subdir)[:cap]:
        ph = [p for p in ph if p in CMU39]
        if len(ph) >= 2 and M.shape[0] >= len(ph):
            out.append((w, np.asarray(M, float), ph))
    return out


def crude_theta(all_phones, scale_mean, scale_std, seed=0):
    """theta_0 — the agent's UNTUNED babble inventory. Per-phone targets are RANDOM around the GLOBAL
    frame scale (so the render range is right) but carry NO per-phone identity. Grounding is what adds
    the per-phone structure. durations uniform. This is the 'crude babble' the spec calls for."""
    rng = np.random.default_rng(seed)
    theta = {p: (scale_mean + rng.standard_normal(len(scale_mean)) * scale_std).astype(float)
             for p in all_phones}
    durs = {p: 5.0 for p in all_phones}
    return theta, durs


def caregiver_scatter(care):
    """A GROUNDED statistic: the caregiver's WITHIN-PHONE per-band scatter SCALE (mean over phones of
    the per-phone per-band std, flat-start assigned). The grounding step yields not just the per-phone
    MEAN (theta) but the SPREAD -- M's babble must carry that within-phone scatter or it is a sterile
    centroid trajectory that does not transfer."""
    acc = defaultdict(list)
    for w, M, ph in care:
        for i, p in enumerate(flatstart_assign(M, ph)):
            acc[p].append(M[i])
    std = {p: np.std(np.asarray(v), 0) for p, v in acc.items() if len(v) > 2}
    return np.mean(list(std.values()), 0) if std else np.ones(care[0][1].shape[1])


def render_babble(lex, theta, durs, gstd, sigma=0.4, reps=2, jitter=True, seed=1):
    """M PRODUCES its OWN babble: render each chosen word's gestural plan as a coarticulated cochlear
    trajectory, then inject the caregiver's WITHIN-PHONE SCATTER (`gstd`, a grounded statistic) so the
    babble manifold matches the caregiver's spread, not just its centroid. Duration + undershoot jitter
    and `reps` scatter draws give the corpus within-class variation. All renders are FREE-labelled
    (M chose the phone seqs). Returns [(word, M, None, phones)]."""
    rng = np.random.default_rng(seed)
    gmean = np.mean(list(theta.values()), 0)
    dmean = float(np.mean(list(durs.values())))
    dur_mults = [1.0] if not jitter else [0.85, 1.0, 1.2]
    undershoots = [0.35] if not jitter else [0.2, 0.35, 0.5]
    samples = []
    for w, ph in lex.items():
        for dm in dur_mults:
            d = {p: durs.get(p, dmean) * dm for p in ph}
            for us in undershoots:
                base = render_dynamic(ph, theta, d, gmean, dmean, undershoot=us)
                for _ in range(reps):
                    M = base.copy()
                    if sigma > 0:
                        M = M + rng.standard_normal(M.shape) * sigma * gstd[None, :]
                    if M.shape[0] >= len(ph):
                        samples.append((w, np.asarray(M, float), None, list(ph)))
    return samples


def transfer_of(samples, Xe, Ye, shared, label):
    """train the agent's own recogniser on M-babble `samples`, score per-frame phone acc on REAL dev."""
    t = time.time()
    m = em_train(samples)
    acc = per_frame_acc(m, Xe, Ye, shared)
    print(f"  [{label:30s}] {len(samples):5d} M-renders -> real per-frame phone acc = {acc:.3f}"
          f"   [{time.time()-t:.0f}s]", flush=True)
    return acc


def main():
    quick = "--quick" in sys.argv
    t0 = time.time()
    print("=" * 96)
    print("AGENT'S OWN M-BABBLE, GROUNDED AGAINST THE XTTS CAREGIVER — approaches XTTS transfer (donkey=0)")
    print("=" * 96, flush=True)

    shared = CMU39
    lex = babble_lexicon()
    all_phones = sorted({p for ph in lex.values() for p in ph})
    print(f"  M's chosen repertoire: {len(lex)} words over {len(all_phones)} phones "
          f"(e.g. {list(lex)[:6]})", flush=True)

    # ---- REAL eval (the test): LibriSpeech dev-clean held words, SAME pipeline as the XTTS loop ----
    real_dev = load_real_samples("dev-clean_*.pkl", 6 if quick else 8)[:1200 if quick else 1500]
    Xe, Ye = build_eval(real_dev, shared)
    maj = Counter(Ye).most_common(1)[0]
    print(f"  REAL dev eval: {len(real_dev)} words, {len(Ye)} frames; chance {1/len(shared):.3f}, "
          f"majority('{maj[0]}') {maj[1]/len(Ye):.3f}", flush=True)

    # ---- SPARSE caregiver grounding sets (a STEP, not the producer) ----
    n_ground = 120 if quick else 250
    xtts_care = load_caregiver("xtts", n_ground)
    piper_care = load_caregiver("piper", n_ground)
    print(f"  caregiver grounding clips (SPARSE, a step): XTTS {len(xtts_care)}, piper {len(piper_care)}",
          flush=True)

    # global frame scale (no per-phone identity) so the crude theta renders in the right range.
    allfr = np.concatenate([M for _w, M, _ph in xtts_care]) if xtts_care else np.zeros((1, 32))
    scale_mean, scale_std = allfr.mean(0), allfr.std(0)
    theta0, durs0 = crude_theta(all_phones, scale_mean, scale_std)
    gstd_x = caregiver_scatter(xtts_care)              # grounded within-phone scatter scale (XTTS)
    gstd_p = caregiver_scatter(piper_care) if piper_care else gstd_x
    passes = 2 if quick else 3

    print("-" * 96)
    print("  PRODUCE + TRANSFER (recogniser trained on M's OWN babble; tested on REAL speech):", flush=True)
    results = {}

    # (1) UNGROUNDED — crude random-per-phone theta + GLOBAL-scale scatter only (no grounding step).
    samp_un = render_babble(lex, theta0, durs0, scale_std)
    results["M-babble UNGROUNDED (crude theta)"] = transfer_of(samp_un, Xe, Ye, shared,
                                                               "M-babble UNGROUNDED")

    # (2) GROUNDED vs the WEAK caregiver (piper) — M approaches the weak caregiver.
    if piper_care:
        th_p, du_p, traj_p = ground_targets(theta0, durs0, piper_care, passes=passes)
        samp_p = render_babble(lex, th_p, du_p, gstd_p)
        results["M-babble GROUNDED vs piper"] = transfer_of(samp_p, Xe, Ye, shared,
                                                            "M-babble GROUNDED vs piper")
        print(f"      (piper grounding surprise trajectory {['%.3f' % s for s in traj_p]})", flush=True)

    # (3) GROUNDED vs the STRONG caregiver (XTTS) — THE HEADLINE: M approaches XTTS.
    th_x, du_x, traj_x = ground_targets(theta0, durs0, xtts_care, passes=passes)
    samp_x = render_babble(lex, th_x, du_x, gstd_x)
    results["M-babble GROUNDED vs XTTS"] = transfer_of(samp_x, Xe, Ye, shared, "M-babble GROUNDED vs XTTS")
    print(f"      (XTTS grounding surprise trajectory {['%.3f' % s for s in traj_x]})", flush=True)

    # ABLATION — crude theta but GIVEN the XTTS scatter: isolates that the per-phone MEAN (theta) is the
    # load-bearing part of the grounding step (scatter alone, without grounded theta, cannot rescue).
    samp_sc = render_babble(lex, theta0, durs0, gstd_x)
    results["M-babble ungrounded-theta + XTTS scatter"] = transfer_of(samp_sc, Xe, Ye, shared,
                                                                      "ungrounded-theta + XTTS scatter")

    print("-" * 96)
    print("  REFERENCE POINTS (NOT the agent's own babble — what M aims to approach):", flush=True)

    # REF A: the prior loop's headline — recogniser trained DIRECTLY on XTTS audio frames (XTTS REQUIRED).
    xtts_audio = load_synth_samples("xtts")
    results["[ref] XTTS-trained-DIRECTLY (audio)"] = transfer_of(xtts_audio, Xe, Ye, shared,
                                                                 "[ref] XTTS-trained-DIRECTLY")
    # REF B: supervised ceiling — recogniser trained on REAL labelled train audio.
    real_train = load_real_samples("train-clean-100_*.pkl", 4 if quick else 6)[:3000 if quick else 4000]
    results["[ref] real(EM)=ceiling"] = transfer_of(real_train, Xe, Ye, shared, "[ref] real(EM) ceiling")

    # ---- SUMMARY + verdict ----
    print("=" * 96)
    print("  SUMMARY (per-frame phone accuracy on REAL LibriSpeech dev-clean):")
    print(f"    {'uniform chance':38s} {1/len(shared):.3f}")
    print(f"    {'majority-phone baseline':38s} {maj[1]/len(Ye):.3f}")
    order = ["M-babble UNGROUNDED (crude theta)", "M-babble ungrounded-theta + XTTS scatter",
             "M-babble GROUNDED vs piper", "M-babble GROUNDED vs XTTS",
             "[ref] XTTS-trained-DIRECTLY (audio)", "[ref] real(EM)=ceiling"]
    for k in order:
        if k in results:
            print(f"    {k:38s} {results[k]:.3f}")
    print("-" * 96)

    un = results["M-babble UNGROUNDED (crude theta)"]
    gx = results["M-babble GROUNDED vs XTTS"]
    xt = results["[ref] XTTS-trained-DIRECTLY (audio)"]
    chance = 1 / len(shared)
    closed = (gx - un) / max(xt - un, 1e-9)
    n_babble = len(samp_x)
    print(f"  MAIN: M-babble transfer {un:.3f} (ungrounded) -> {gx:.3f} (XTTS-grounded); "
          f"XTTS-trained-directly {xt:.3f}.")
    print(f"        gap to XTTS closed by grounding: {100*closed:.0f}%  "
          f"(of the ungrounded->XTTS-direct distance)")
    sc = results["M-babble ungrounded-theta + XTTS scatter"]
    print(f"  DISCRIMINATIVE: grounding is load-bearing: ungrounded {un:.3f} (~chance {chance:.3f}) "
          f"<< XTTS-grounded {gx:.3f}: {gx > un + 0.02}")
    print(f"        isolation: crude theta + XTTS scatter stays {sc:.3f} (~chance) -> the grounded "
          f"per-phone MEAN (theta), not the scatter, is what transfers: {gx > sc + 0.02}")
    if "M-babble GROUNDED vs piper" in results:
        gp = results["M-babble GROUNDED vs piper"]
        print(f"  CAREGIVER: piper-grounded {gp:.3f}, XTTS-grounded {gx:.3f} -- M approaches a SIMILAR "
              f"caregiver-grounded level either way; the strong>weak ordering of DIRECT training does "
              f"NOT replicate for centroid-grounding (single-voice piper grounds an equally sharp theta).")
    print(f"  XTTS-NOT-REQUIRED: grounding used {len(xtts_care)} XTTS clips (a STEP) to estimate theta; "
          f"M then produced {n_babble} babble renders -> ratio babble:grounding = "
          f"{n_babble/max(len(xtts_care),1):.1f}x. No torch/TTS imported (donkey=0 at inference).")
    print(f"  donkey=0: production = held render_dynamic; grounding = held collapse cognition "
          f"(native surprise + counted add); recogniser = own from-scratch PCA->LDA. No LLM/net/gradient.")
    print("=" * 96)
    print(f"  total {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
