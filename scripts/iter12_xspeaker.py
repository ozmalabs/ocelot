"""iter-12 — close the CROSS-SPEAKER INVARIANCE gap (the last inadmissible link).

iter-11 located the binding blocker precisely: on REAL FSDD, full-resolution DTW
word-matching = ~0.78 WITHIN-speaker but ~0.35 CROSS-speaker. The same word from
different speakers does not match. The features are not speaker-invariant enough;
the current invariant_transform (forward-VTLN + CMVN + predict-remove) got the
units past the predictiveness yardstick but left this cross-speaker word-matching
gap.

This probe is the FAST within/cross full-DTW word-matching probe on real FSDD,
per normalization method (ablation). The agent forward-designs a DEEPER speaker
normalization and we ask: does it raise CROSS toward WITHIN, shuffle-controlled?

The matrix substrate is the agent's per-voiced-frame log-mel band matrix
(domains.sound_graph._voiced_frames -> log-mel), the same representation the
cross_speaker_clustering probe uses. Full-resolution DTW (continuous_speech_
recognition.dtw) over the NORMALIZED frames = the richest trajectory metric, zero
resampling loss. This is the iter-11 probe, made standalone + ablatable.

Run:  python -m scripts.iter12_xspeaker  [n_per_speaker]
"""
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scripts.fsdd_learner_world as fl
from scripts.cross_speaker_clustering_probe import logmel_frames
from scripts.continuous_speech_recognition import dtw
import domains.invariant_units as IU
import domains.xspeaker_norm as XN


DIGITS = fl._DIGITS


# --------------------------------------------------------------------------
# Corpus: per-voiced-frame log-mel band matrices, labelled by word + speaker.
# --------------------------------------------------------------------------

def build_corpus(n_per_speaker=6, digits=range(10), seed=0):
    """Balanced subset: n_per_speaker recordings per (digit, speaker). Returns a
    list of (M, word, speaker) — M = frames x bands voiced log-mel matrix."""
    rng = np.random.default_rng(seed)
    files = fl.gather_files()
    buckets = defaultdict(list)
    for path, d, spk, idx in files:
        if d in digits:
            buckets[(d, spk)].append(path)
    corpus = []
    for (d, spk), paths in sorted(buckets.items()):
        paths = sorted(paths)
        rng.shuffle(paths)
        for p in paths[:n_per_speaker]:
            x, fs = fl.load_wav(p)
            M = logmel_frames(x, fs)
            if M.shape[0] >= 2:
                corpus.append((M, DIGITS[d], spk))
    return corpus


# --------------------------------------------------------------------------
# within / cross full-DTW word-matching: for each utterance, find its nearest
# OTHER utterance by full-resolution DTW, ask if it carries the same word —
# split by whether that neighbour is the SAME speaker (within) or a DIFFERENT
# speaker (cross). Chance = 1/n_words. This is the iter-11 metric.
# --------------------------------------------------------------------------

def within_cross_match(mats, words, speakers):
    n = len(mats)
    # nearest WITHIN-speaker and nearest CROSS-speaker neighbour, per utterance.
    win_hit = win_tot = 0
    cross_hit = cross_tot = 0
    for i in range(n):
        best_w = (1e18, None)
        best_c = (1e18, None)
        for j in range(n):
            if i == j:
                continue
            d = dtw(mats[i], mats[j])
            if speakers[j] == speakers[i]:
                if d < best_w[0]:
                    best_w = (d, j)
            else:
                if d < best_c[0]:
                    best_c = (d, j)
        if best_w[1] is not None:
            win_tot += 1
            win_hit += (words[best_w[1]] == words[i])
        if best_c[1] is not None:
            cross_tot += 1
            cross_hit += (words[best_c[1]] == words[i])
    within = win_hit / win_tot if win_tot else 0.0
    cross = cross_hit / cross_tot if cross_tot else 0.0
    return within, cross


# --------------------------------------------------------------------------
# Normalization methods (the ablation). Each maps a raw band matrix -> a
# normalized band matrix; DTW runs on the result. `canonical` is the
# cohort-canonical log-centroid for forward-VTLN (TRAIN-derived, no leakage).
# --------------------------------------------------------------------------

def methods(canonical, corpus):
    """Return {name: fn(M) -> M_norm}. `corpus` lets per-speaker methods see the
    test speaker's own audio (per-speaker statistics estimated at test time)."""
    base = {
        # the iter-11 baseline = the current default invariant_transform.
        "raw": lambda M, spk=None: M,
        "current(VTLN+CMVN+PR)":
            lambda M, spk=None: IU.invariant_transform(M, canonical),
    }
    base.update(XN.methods(canonical, corpus))
    return base


def shuffle_control(mats, words, speakers, seed=0):
    """Shuffle the word labels; the within/cross match must collapse to chance."""
    rng = np.random.default_rng(seed)
    sh = list(words)
    rng.shuffle(sh)
    return within_cross_match(mats, sh, speakers)


# --------------------------------------------------------------------------
# Recognition on held-out SPEAKERS (LOSO): kNN-DTW over the normalized matrices.
# Train = all other speakers' utterances (with their words); test = the held-out
# speaker. Each test utterance -> majority word among its k nearest train
# utterances by full-resolution DTW. Compared to the UNIGRAM baseline (predict the
# most-frequent train word). This is the full-DTW recogniser that matches the
# within/cross probe metric — no clustering, no descriptor, the richest metric.
# --------------------------------------------------------------------------

def knn_dtw_recognise(train, test, words_tr, k=3):
    preds = []
    for Mt in test:
        ds = sorted((dtw(Mt, Mtr), wtr) for Mtr, wtr in zip(train, words_tr))
        top = [w for _, w in ds[:k]]
        preds.append(_majority(top))
    return preds


def _majority(items):
    from collections import Counter
    return Counter(items).most_common(1)[0][0]


def recognise_loso(corpus, norm_fn, k=3, verbose=True):
    """Leave-one-speaker-out recognition. norm_fn(M, speaker) -> normalized M.
    Per held-out speaker: train on the rest, classify the held-out speaker's
    utterances, report word-accuracy vs the unigram baseline."""
    from collections import Counter
    speakers = sorted(set(s for _, _, s in corpus))
    norm = [(norm_fn(M, spk), w, spk) for M, w, spk in corpus]
    accs, unis = [], []
    for held in speakers:
        train = [(M, w) for M, w, s in norm if s != held]
        test = [(M, w) for M, w, s in norm if s == held]
        tr_mats = [M for M, _ in train]
        tr_words = [w for _, w in train]
        te_mats = [M for M, _ in test]
        te_words = [w for _, w in test]
        preds = knn_dtw_recognise(tr_mats, te_mats, tr_words, k=k)
        acc = np.mean([p == t for p, t in zip(preds, te_words)])
        uni_word = Counter(tr_words).most_common(1)[0][0]
        uni = np.mean([uni_word == t for t in te_words])
        accs.append(acc)
        unis.append(uni)
        if verbose:
            print(f"  held-out {held:10s}: acc {acc:.3f}  unigram {uni:.3f}  "
                  f"n_test {len(te_words)}")
    return float(np.mean(accs)), float(np.mean(unis))


def run(n_per_speaker=6, seed=0, verbose=True):
    corpus = build_corpus(n_per_speaker=n_per_speaker, seed=seed)
    words = [w for _, w, _ in corpus]
    speakers = [s for _, _, s in corpus]
    raw_mats = [M for M, _, _ in corpus]
    chance = 1.0 / len(set(words))
    canonical = IU.canonical_log_centroid(raw_mats)

    if verbose:
        spk = sorted(set(speakers))
        print(f"corpus: {len(corpus)} utts, {len(set(words))} words, "
              f"{len(spk)} speakers {spk}, chance {chance:.3f}\n")
        print(f"{'method':28s}  {'WITHIN':>8s}  {'CROSS':>8s}  {'gap':>6s}")

    ms = methods(canonical, corpus)
    res = {"chance": chance}
    for name, fn in ms.items():
        mats = [fn(M, spk) for M, spk in zip(raw_mats, speakers)]
        w, c = within_cross_match(mats, words, speakers)
        res[name] = (w, c)
        if verbose:
            print(f"{name:28s}  {w:8.3f}  {c:8.3f}  {w - c:6.3f}")

    # shuffle control on the strongest cross method
    best = max(ms, key=lambda k: res[k][1])
    mats = [ms[best](M, spk) for M, spk in zip(raw_mats, speakers)]
    sw, sc = shuffle_control(mats, words, speakers, seed=seed)
    res["shuffle_best"] = (sw, sc)
    res["best_method"] = best
    if verbose:
        print(f"\nSHUFFLE control on '{best}': within {sw:.3f} cross {sc:.3f}  "
              f"(must be ~chance {chance:.3f})")

    # --- recognition on held-out speakers (LOSO) IF cross closed (> ~0.6) ----
    best_cross = res[best][1]
    if best_cross > 0.6:
        if verbose:
            print(f"\nCROSS closed ({best_cross:.3f} > 0.6) -> LOSO recognition:")
            print(f"  --- baseline current(VTLN+CMVN+PR) ---")
        cur_acc, cur_uni = recognise_loso(
            corpus, ms["current(VTLN+CMVN+PR)"], verbose=verbose)
        if verbose:
            print(f"  --- deeper '{best}' ---")
        deep_acc, deep_uni = recognise_loso(corpus, ms[best], verbose=verbose)
        res["loso_current"] = (cur_acc, cur_uni)
        res["loso_deep"] = (deep_acc, deep_uni)
        if verbose:
            print(f"\nLOSO recognition (held-out speakers, chance {chance:.3f}):")
            print(f"  current(VTLN+CMVN+PR): acc {cur_acc:.3f}  vs unigram {cur_uni:.3f}")
            print(f"  deeper {best}: acc {deep_acc:.3f}  vs unigram {deep_uni:.3f}")
            print(f"  >>> deeper beats unigram? "
                  f"{'YES' if deep_acc > deep_uni else 'NO'} "
                  f"(+{deep_acc - deep_uni:.3f})")
    elif verbose:
        print(f"\nCROSS did not close ({best_cross:.3f} <= 0.6) -> recognition NOT run.")
    return res


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    run(n_per_speaker=n)


if __name__ == "__main__":
    main()
