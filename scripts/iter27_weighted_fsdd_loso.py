"""iter-27 FSDD LOSO — does the agent's WEIGHTED RECOGNIZER over the channels (the
recognition_graph weighted Sum over channels, per-contrast weights from the agent's
pairwise-spec over its confusions) BEAT the iter-26 single-DTW-over-concatenation, the
single channels, and approach baseline?

Gated by RECOGNITION ACCURACY (the recognizer is a DECISION). Leave-one-speaker-out.
Front-ends / decision rules, all from raw audio, the agent's iter-25/26 channels:
  BASELINE      : invariant_transform band matrix kNN-DTW (confirmed ~0.785) [~0.544 here]
  CONCAT-DTW    : iter-26 stack (formant++manner) under ONE DTW (the uniform combiner)
  FORMANT-alone : formant-relation channel, kNN-DTW
  MANNER-alone  : manner/voicing channel, kNN-DTW
  WEIGHTED      : the agent's weighted recognizer over the two channels (this turn)
  shuffle / unigram controls.

Per held-out speaker, the WEIGHTED path builds its CONFUSION prior + per-contrast
channel weights from the TRAIN speakers ONLY (no leakage), via the agent's
build_channel_confusions + derive_channel_weights, then classifies the held-out
speaker's clips with recognize_weighted (the agent's graph Term).

LPC order = the agent's waveform-LPC spec rule fs/1000+2. NSPACINGS default 4.
World-adapter only — no tuning of any relation, no hand-picked weight.

Run: python -m scripts.iter27_weighted_fsdd_loso [n_per_speaker]
"""
import os
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import domains.invariant_units as IU
import scripts.fsdd_learner_world as fl
from scripts.iter12_xspeaker import build_corpus, recognise_loso, DIGITS, dtw
from domains.stacked_representation import apply_stacked
from domains.weighted_channel_recognizer import (
    build_channel_confusions, derive_channel_weights, recognize_weighted)
from substrate_rs import Substrate


def build_channel_corpus(n_per_speaker=6, seed=0, nsp=4):
    """Per (digit, speaker): the agent's TWO channels (formant, manner) per clip,
    labelled by word + speaker. Returns [((formant_mat, manner_mat), word, spk)]."""
    rng = np.random.default_rng(seed)
    files = fl.gather_files()
    buckets = defaultdict(list)
    for path, d, spk, idx in files:
        buckets[(d, spk)].append(path)
    corpus = []
    s = Substrate()
    for (d, spk), paths in sorted(buckets.items()):
        paths = sorted(paths)
        rng.shuffle(paths)
        for p in paths[:n_per_speaker]:
            x, fs = fl.load_wav(p)
            fr = apply_stacked(x, fs, n_spacings=nsp, substrate=s,
                               channels="formant", track=True)
            mn = apply_stacked(x, fs, n_spacings=nsp, substrate=s,
                               channels="manner")
            if fr.shape[0] >= 2 and mn.shape[0] >= 2:
                corpus.append(((fr, mn), DIGITS[d], spk))
    return corpus


def _concat(feat):
    fr, mn = feat
    n = min(fr.shape[0], mn.shape[0])
    return np.concatenate([fr[:n], mn[:n]], axis=1)


def loso_concat(corpus, k=3):
    """iter-26 uniform combiner: ONE DTW over the concatenated channels, kNN."""
    speakers = sorted(set(s for _, _, s in corpus))
    accs, unis = [], []
    for held in speakers:
        train = [(_concat(f), w) for f, w, s in corpus if s != held]
        test = [(_concat(f), w) for f, w, s in corpus if s == held]
        tr_m = [m for m, _ in train]; tr_w = [w for _, w in train]
        ok = 0
        for Mt, tw in test:
            ds = sorted((dtw(Mt, Mtr), wtr) for Mtr, wtr in zip(tr_m, tr_w))
            pred = Counter(w for _, w in ds[:k]).most_common(1)[0][0]
            ok += (pred == tw)
        accs.append(ok / len(test) if test else 0.0)
        uni = Counter(tr_w).most_common(1)[0][0]
        unis.append(np.mean([uni == w for _, w in test]) if test else 0.0)
    return float(np.mean(accs)), float(np.mean(unis))


def loso_single(corpus, channel_idx, k=3):
    """Single channel (0=formant, 1=manner) kNN-DTW LOSO."""
    speakers = sorted(set(s for _, _, s in corpus))
    accs = []
    for held in speakers:
        train = [(f[channel_idx], w) for f, w, s in corpus if s != held]
        test = [(f[channel_idx], w) for f, w, s in corpus if s == held]
        tr_m = [m for m, _ in train]; tr_w = [w for _, w in train]
        ok = 0
        for Mt, tw in test:
            ds = sorted((dtw(Mt, Mtr), wtr) for Mtr, wtr in zip(tr_m, tr_w))
            pred = Counter(w for _, w in ds[:k]).most_common(1)[0][0]
            ok += (pred == tw)
        accs.append(ok / len(test) if test else 0.0)
    return float(np.mean(accs))


def loso_weighted(corpus, k=3, shuffle=False, seed=0):
    """The agent's WEIGHTED recognizer. Per held-out speaker: build the confusion
    prior + per-contrast channel weights from the TRAIN speakers (the agent's
    pairwise-spec), classify the held-out speaker's clips with the agent's graph Term.
    `shuffle` shuffles the train labels (control: must collapse toward unigram)."""
    speakers = sorted(set(s for _, _, s in corpus))
    accs = []
    spec_sizes = []
    rng = np.random.default_rng(seed)
    for held in speakers:
        tr = [(f, w) for f, w, s in corpus if s != held]
        te = [(f, w) for f, w, s in corpus if s == held]
        tr_feats = [f for f, _ in tr]
        tr_words = [w for _, w in tr]
        if shuffle:
            tr_words = list(tr_words)
            rng.shuffle(tr_words)
        # the agent builds its confusion prior + per-contrast weights from TRAIN only
        sub = Substrate()
        build_channel_confusions(sub, tr_feats, tr_words, k=k)
        per_pair, default, spec = derive_channel_weights(sub, top_k=45)
        spec_sizes.append(len(spec))
        ok = 0
        for feat, tw in te:
            pred = recognize_weighted(sub, feat, tr_feats, tr_words,
                                      per_pair, default, k=k)
            ok += (pred == tw)
        accs.append(ok / len(te) if te else 0.0)
    return float(np.mean(accs)), float(np.mean(spec_sizes))


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    nsp = int(os.environ.get("NSPACINGS", "4"))

    # BASELINE on the band-matrix corpus (the confirmed path)
    corpus_b = build_corpus(n_per_speaker=n_per, seed=0)
    canonical = IU.canonical_log_centroid([M for M, _, _ in corpus_b])
    words = [w for _, w, _ in corpus_b]
    chance = 1.0 / len(set(words))
    unigram = Counter(words).most_common(1)[0][0]
    uni_acc = np.mean([w == unigram for w in words])

    print("=== iter-27 FSDD LOSO: the agent's WEIGHTED RECOGNIZER over the channels ===")
    print(f"corpus: {len(corpus_b)} utts, n_per_speaker={n_per}, n_spacings={nsp}, "
          f"chance {chance:.3f}, unigram {uni_acc:.3f}\n")

    print("--- BASELINE invariant_transform kNN-DTW (confirmed ~0.785) ---")
    b_acc, b_uni = recognise_loso(
        corpus_b, lambda M, spk=None: IU.invariant_transform(M, canonical),
        verbose=False)
    print(f"  MEAN acc {b_acc:.3f}  (unigram {b_uni:.3f})\n")

    # the channel corpus (the agent's two iter-26 channels per clip)
    corpus_c = build_channel_corpus(n_per_speaker=n_per, seed=0, nsp=nsp)
    print(f"channel corpus: {len(corpus_c)} utts (formant + manner channels)\n")

    print("--- CONCAT-DTW (iter-26 uniform combiner: ONE DTW over formant++manner) ---")
    cc_acc, cc_uni = loso_concat(corpus_c)
    print(f"  MEAN acc {cc_acc:.3f}\n")

    print("--- FORMANT-alone kNN-DTW ---")
    f_acc = loso_single(corpus_c, 0)
    print(f"  MEAN acc {f_acc:.3f}\n")

    print("--- MANNER-alone kNN-DTW ---")
    m_acc = loso_single(corpus_c, 1)
    print(f"  MEAN acc {m_acc:.3f}\n")

    print("--- WEIGHTED RECOGNIZER (agent's graph Term, per-contrast pairwise weights) ---")
    w_acc, spec_sz = loso_weighted(corpus_c)
    print(f"  MEAN acc {w_acc:.3f}  (mean pairwise-spec size {spec_sz:.1f})\n")

    print("--- WEIGHTED, SHUFFLED train labels (control) ---")
    ws_acc, _ = loso_weighted(corpus_c, shuffle=True, seed=1)
    print(f"  MEAN acc {ws_acc:.3f}  (must collapse toward unigram {uni_acc:.3f})\n")

    print("=" * 64)
    print(f"  unigram          {uni_acc:.3f}")
    print(f"  BASELINE         {b_acc:.3f}   (confirmed ~0.785)")
    print(f"  CONCAT-DTW (i26) {cc_acc:.3f}")
    print(f"  FORMANT-alone    {f_acc:.3f}")
    print(f"  MANNER-alone     {m_acc:.3f}")
    print(f"  WEIGHTED (i27)   {w_acc:.3f}   ({w_acc - cc_acc:+.3f} vs concat; "
          f"{w_acc - max(f_acc, m_acc):+.3f} vs best single; {w_acc - b_acc:+.3f} vs baseline)")
    print(f"  WEIGHTED shuffle {ws_acc:.3f}   (control)")
    print("=" * 64)


if __name__ == "__main__":
    main()
