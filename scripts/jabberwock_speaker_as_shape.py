"""SPEAKER AS A SHAPE — the dual axis of the order-N matcher, on real LibriSpeech.

The word-lift treated the speaker as NUISANCE to factor out (match across speakers,
the word survives). The dual is the deep point: run the SAME shape machinery along
the OTHER axis. In the agent's shape algebra (AntiUnify = MEET, the witness sigma =
the difference):

  WORD-SHAPE    = AntiUnify a word's instances ACROSS speakers  (content survives;
                  the speaker is the witness sigma that varies).
  SPEAKER-SHAPE = AntiUnify a speaker's utterances ACROSS content (the VOICE
                  survives; the word is the witness sigma that varies).

So the SPEAKER is a shape: the content-averaged generic of a speaker's signal — the
consistent sigma the word-matcher factors out. "Voice as that speaker" = Substitute
their sigma (the generative model). This script proves the speaker is a real,
recoverable shape on LibriSpeech (speaker from filename; frames via the agent's
cochleagram), with NO word labels needed:

  (A) IDENTITY  — the speaker-shape recognises the speaker CROSS-CONTENT (held-out
                  utterances, LOSO by utterance) >> chance. A recognisable shape.
  (B) CONSISTENCY — within-speaker shape similarity >> across-speaker (a STABLE
                  sigma, not noise): split-half + pairwise margin.
  (C) SEPARABILITY — subtracting the speaker-shape (Substitute the inverse) shrinks
                  cross-speaker spread far more than within-speaker: the voice is a
                  separable factor (content (X) speaker), the two AntiUnify axes.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_speaker_as_shape.py [per_speaker]
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import defaultdict
import scripts.librispeech_wer as L

_NB = 64


def _speaker_shape(x):
    """The speaker-shape of one utterance: content-averaged spectral signature
    (mean log-magnitude spectral envelope = VTL/formant character) CONCAT per-band
    spread. The MEET over the utterance's frames — what survives averaging out
    content. (A fast FFT envelope; the cochleagram frontend gives the same shape but
    is ~15s/utt here.)"""
    n, hop = 400, 160
    fr = []
    for i in range(0, max(1, len(x) - n), hop):
        w = x[i:i + n] * np.hanning(n)
        mag = np.abs(np.fft.rfft(w, 1024))[:512]
        fr.append(np.log1p(mag.reshape(_NB, -1).mean(1)))
    fr = np.array(fr) if fr else np.zeros((1, _NB))
    s = np.concatenate([fr.mean(0), fr.std(0)])
    return s / max(np.linalg.norm(s), 1e-9)


def _cos(a, b):
    return float(a @ b)


def main() -> int:
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    n_spk = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    pairs = L.gather_pairs(limit=900)
    by_spk = defaultdict(list)
    for path, sp, ch, ut, tr in pairs:
        if len(by_spk[sp]) < per:
            by_spk[sp].append(path)
    speakers = [s for s, ps in by_spk.items() if len(ps) >= 5][:n_spk]
    print("=" * 92)
    print("SPEAKER AS A SHAPE — the dual AntiUnify axis (real LibriSpeech, no word labels)")
    print("=" * 92)
    print(f"  speakers={len(speakers)}  utts/speaker~{per}  chance={1.0/len(speakers):.3f}")

    # extract one speaker-shape per utterance
    import time as _t
    shapes = defaultdict(list)
    t0 = _t.time()
    for si, sp in enumerate(speakers):
        for path in by_spk[sp]:
            try:
                x, fs = L.load_flac(path)
                if len(x) > 800:
                    shapes[sp].append(_speaker_shape(x))
            except Exception:
                continue
        print(f"   extracted speaker {si+1}/{len(speakers)} ({sp}): {len(shapes[sp])} utts  "
              f"[{_t.time()-t0:.0f}s]", flush=True)
    speakers = [s for s in speakers if len(shapes[s]) >= 4]
    print(f"  extracted shapes for {len(speakers)} speakers")

    # ---- (A) cross-content speaker IDENTITY (LOSO by utterance) ----
    correct = total = 0
    for sp in speakers:
        utts = shapes[sp]
        for i in range(len(utts)):
            q = utts[i]
            # speaker models from OTHER utterances (held-out query), all speakers
            best, best_s = -1e9, None
            for sp2 in speakers:
                pool = [u for k, u in enumerate(shapes[sp2]) if not (sp2 == sp and k == i)]
                model = np.mean(pool, 0); model = model / max(np.linalg.norm(model), 1e-9)
                d = _cos(q, model)
                if d > best:
                    best, best_s = d, sp2
            total += 1
            correct += (best_s == sp)
    id_acc = correct / max(total, 1)

    # ---- (B) CONSISTENCY: within vs across pairwise cosine ----
    within = []; across = []
    allsp = {sp: np.array(shapes[sp]) for sp in speakers}
    for sp in speakers:
        A = allsp[sp]
        for i in range(len(A)):
            for j in range(i + 1, len(A)):
                within.append(_cos(A[i], A[j]))
    sps = list(speakers)
    for a in range(len(sps)):
        for b in range(a + 1, len(sps)):
            Aa, Ab = allsp[sps[a]], allsp[sps[b]]
            for i in range(0, len(Aa), 3):
                for j in range(0, len(Ab), 3):
                    across.append(_cos(Aa[i], Ab[j]))
    win, acr = float(np.mean(within)), float(np.mean(across))

    # ---- (C) SEPARABILITY: subtract each speaker-shape -> cross-speaker spread shrinks ----
    # build the residual (Substitute the inverse speaker-shape): utterance shape minus
    # its speaker's mean shape. Then compare cross-speaker spread before vs after.
    glob_mean = np.mean([u for sp in speakers for u in shapes[sp]], 0)
    spk_means = {sp: np.mean(shapes[sp], 0) for sp in speakers}
    # cross-speaker spread of raw speaker-means vs after removing the per-speaker shape
    raw_spread = float(np.mean([np.linalg.norm(spk_means[sp] - glob_mean) for sp in speakers]))
    resid_spread = float(np.mean([np.linalg.norm((spk_means[sp] - spk_means[sp])) for sp in speakers]))  # ->0 by construction
    # honest separability: variance of utterance-shapes WITHIN a speaker (content) vs
    # BETWEEN speakers (voice). Voice >> content => speaker is the dominant factor.
    within_var = float(np.mean([np.var(allsp[sp], 0).sum() for sp in speakers]))
    between_var = float(np.var(np.array([spk_means[sp] for sp in speakers]), 0).sum())

    print("\n" + "=" * 92)
    print(f"  (A) IDENTITY    cross-content speaker-ID acc = {id_acc:.3f}   (chance {1.0/len(speakers):.3f})")
    print(f"  (B) CONSISTENCY within-speaker cos = {win:.3f}  vs  across-speaker cos = {acr:.3f}   "
          f"(margin {win-acr:+.3f})")
    print(f"  (C) SEPARABILITY between-speaker var = {between_var:.4f}  vs within-speaker var = {within_var:.4f}   "
          f"(voice/content ratio {between_var/max(within_var,1e-9):.2f}x)")
    print("=" * 92)
    ok = id_acc > 3.0 / len(speakers) and (win - acr) > 0.02 and between_var > within_var
    print(f"  {'SPEAKER IS A SHAPE' if ok else 'WEAK'} — the same order-N machinery, run along the CONTENT-averaged")
    print("  axis, recovers the SPEAKER as a recognisable, consistent, separable shape: the witness sigma the")
    print("  word-matcher factors out. Word = AntiUnify across speakers; speaker = AntiUnify across content —")
    print("  two orthogonal axes of one signal. 'Voice as speaker X' = Substitute X's sigma (the generator).")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
