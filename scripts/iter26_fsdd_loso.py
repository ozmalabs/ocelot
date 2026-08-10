"""iter-26 FSDD LOSO — does the agent's MULTI-CHANNEL STACK (formant-relation +
manner/voicing, with formant tracking) it DERIVED for itself (iter26_stacked_derive)
recover / improve the FSDD digit recogniser vs the iter-25 formant-relation ALONE?

Same iter-12 kNN-DTW LOSO harness (held-out-speaker). Front-ends, all from raw audio:
  BASELINE      : invariant_transform band matrix (confirmed ~0.785)          [0.544 here]
  FORMANT (i25) : iter-25 spacing over waveform-LPC true formants (no track)  [0.528 here]
  FORMANT+TRACK : iter-25 spacing over TRACKED (continuity-smoothed) formants  -- (c)
  MANNER        : the agent's phonology manner/voicing channel ALONE          -- (b)
  STACK (i26)   : FORMANT+TRACK ++ MANNER  (the agent's full derived stack)   -- (a)

LPC order = the agent's waveform-LPC spec rule fs/1000+2 = 10 at 8 kHz (NOT a
gate-chasing pick). NSPACINGS default 4. World-adapter only — no tuning of any relation.

Run: python -m scripts.iter26_fsdd_loso [n_per_speaker]
"""
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import domains.invariant_units as IU
import scripts.fsdd_learner_world as fl
from scripts.continuous_speech_recognition import frames_of
from scripts.iter12_xspeaker import build_corpus, recognise_loso, DIGITS
from domains.stacked_representation import apply_stacked
from substrate_rs import Substrate


def build_audio_corpus(feat_fn, n_per_speaker=6, seed=0):
    rng = np.random.default_rng(seed)
    files = fl.gather_files()
    buckets = defaultdict(list)
    for path, d, spk, idx in files:
        buckets[(d, spk)].append(path)
    corpus = []
    for (d, spk), paths in sorted(buckets.items()):
        paths = sorted(paths)
        rng.shuffle(paths)
        for p in paths[:n_per_speaker]:
            x, fs = fl.load_wav(p)
            F = feat_fn(x, fs)
            if F.shape[0] >= 2:
                corpus.append((F, DIGITS[d], spk))
    return corpus


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    nsp = int(os.environ.get("NSPACINGS", "4"))

    corpus = build_corpus(n_per_speaker=n_per, seed=0)
    canonical = IU.canonical_log_centroid([M for M, _, _ in corpus])
    print("=== iter-26 FSDD LOSO: agent's multi-channel STACK ===")
    print(f"corpus: {len(corpus)} utts, n_per_speaker={n_per}, n_spacings={nsp}\n")

    print("--- BASELINE invariant_transform (confirmed ~0.785) ---")
    b_acc, _ = recognise_loso(
        corpus, lambda M, spk=None: IU.invariant_transform(M, canonical),
        verbose=True)
    print(f"  MEAN acc {b_acc:.3f}\n")

    def feat_formant(x, fs):
        return apply_stacked(x, fs, n_spacings=nsp, substrate=Substrate(),
                             channels="formant", track=False)

    def feat_track(x, fs):
        return apply_stacked(x, fs, n_spacings=nsp, substrate=Substrate(),
                             channels="formant", track=True)

    def feat_manner(x, fs):
        return apply_stacked(x, fs, n_spacings=nsp, substrate=Substrate(),
                             channels="manner")

    def feat_stack(x, fs):
        return apply_stacked(x, fs, n_spacings=nsp, substrate=Substrate(),
                             channels="both", track=True)

    print("--- FORMANT (i25, no track) ---")
    f25, _ = recognise_loso(build_audio_corpus(feat_formant, n_per, 0),
                            lambda M, spk=None: M, verbose=False)
    print(f"  MEAN acc {f25:.3f}\n")

    print("--- FORMANT+TRACK (c) ---")
    ftr, _ = recognise_loso(build_audio_corpus(feat_track, n_per, 0),
                            lambda M, spk=None: M, verbose=False)
    print(f"  MEAN acc {ftr:.3f}\n")

    print("--- MANNER/VOICING alone (b) ---")
    fmn, _ = recognise_loso(build_audio_corpus(feat_manner, n_per, 0),
                            lambda M, spk=None: M, verbose=False)
    print(f"  MEAN acc {fmn:.3f}\n")

    print("--- STACK (i26: formant+track ++ manner) (a) ---")
    fst, _ = recognise_loso(build_audio_corpus(feat_stack, n_per, 0),
                            lambda M, spk=None: M, verbose=True)
    print(f"  MEAN acc {fst:.3f}\n")

    print("=" * 60)
    print(f"  BASELINE       {b_acc:.3f}   (confirmed ~0.785)")
    print(f"  FORMANT (i25)  {f25:.3f}   (iter-25 formant spacing, no track)")
    print(f"  FORMANT+TRACK  {ftr:.3f}   ({ftr - f25:+.3f} vs i25)")
    print(f"  MANNER alone   {fmn:.3f}")
    print(f"  STACK (i26)    {fst:.3f}   ({fst - f25:+.3f} vs i25; "
          f"{fst - b_acc:+.3f} vs baseline)")
    print("=" * 60)


if __name__ == "__main__":
    main()
