"""iter-11 — lift the cross-speaker chunk DESCRIPTOR (the binding ceiling).

iter-10 located the recognition wall precisely: with the corpus-starvation
constraint removed (390-403 cross-speaker chunks) and EVEN with oracle labels +
whole-utterance (no over-segmentation), word identity ceilings at ~0.51. No
clustering can beat how well the descriptor separates words; the ceiling IS the
descriptor (the resampled trajectory-shape, which throws word identity away).

This probe lifts the descriptor FORWARD from the agent's OWN invented features:
  - order-2 CURVATURE          (order_n_concepts)
  - per-slot formant-RATIO     (analogy / invariant_units VTL science — VTL-invariant)
  - band-vs-band contrasts     (feature_generator — spectral tilt, level-invariant)
stacked on the order-0 trajectory + order-1 velocity base. See
continuous_speech_recognition.descriptor_components for the science of each.

FAST inner loop: NO lexicon, NO clustering, NO over-segmentation. Whole-utterance
descriptor with ORACLE labels, on HELD-OUT personas (speaker-independent):
  - 1-NN same-word rate   (nearest other-utterance descriptor has the same word?)
  - oracle-centroid acc   (per-word centroid from train, nearest-centroid on test)
Per-feature ABLATION: which component actually lifts the ceiling above 0.512?

Run: python -m scripts.iter11_descriptor_oracle [n_reps]
"""
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scripts.continuous_speech_recognition as CSR
from domains.invariant_units import invariant_transform, canonical_log_centroid
import scripts.iter10_persona_lexicon as IT


# ---- descriptor (whole-utterance, no chunking) ---------------------------

def utt_descriptor(M, components):
    """Whole-utterance descriptor: treat the entire invariant frame matrix as ONE
    chunk (1 chunk = 1 word, no over-segmentation), build the rich descriptor with
    the given components toggled."""
    parts = CSR.descriptor_components(M, components=components)
    return CSR.assemble_descriptor(parts)


def baseline_descriptor(M, mode):
    """iter-9/10 baselines for the before number: 'traj' and 'rate_inv'."""
    return CSR.chunk_traj_vector(M, embed=mode)


# ---- oracle measures ------------------------------------------------------

def one_nn_same_word(vecs, words):
    """1-NN (leave-one-out) same-word rate: for each utterance, does its nearest
    OTHER utterance descriptor carry the same word? Chance = 1/#words."""
    X = np.asarray(vecs)
    n = len(X)
    if n < 2:
        return 0.0
    D = ((X[:, None, :] - X[None, :, :]) ** 2).sum(-1)
    np.fill_diagonal(D, np.inf)
    nn = D.argmin(1)
    hits = sum(words[i] == words[nn[i]] for i in range(n))
    return hits / n


def oracle_centroid_acc(tr_vecs, tr_words, te_vecs, te_words):
    """ORACLE-label centroid accuracy: build one centroid per word from the TRAIN
    descriptors (labels given), classify each TEST utterance by nearest centroid.
    The best the descriptor can do with perfect labels + no over-segmentation."""
    groups = defaultdict(list)
    for v, w in zip(tr_vecs, tr_words):
        groups[w].append(v)
    labels = sorted(groups)
    cen = np.stack([np.mean(groups[w], axis=0) for w in labels])
    X = np.asarray(te_vecs)
    if X.size == 0:
        return 0.0
    D = ((cen[None, :, :] - X[:, None, :]) ** 2).sum(-1)
    pred = D.argmin(1)
    hits = sum(labels[pred[i]] == te_words[i] for i in range(len(te_words)))
    return hits / len(te_words)


# ---- build the held-out persona corpus (whole-utterance, invariant) ------

def build_corpus(n_reps, seed):
    sub, pipe = IT.build_agent()
    IT.teach_vocab(sub, pipe, IT.VOCAB)
    personas = IT.install_personas(sub, IT.PERSONA_BANK)
    corpus = IT.make_persona_corpus(sub, pipe, personas, IT.VOCAB, n_reps, seed=seed)
    framed = IT.frame_corpus(corpus)

    names = list(personas)
    n_held = max(1, len(names) // 4)
    test_personas = set(names[:n_held])
    train = [t for t in framed if t[2] not in test_personas]
    test = [t for t in framed if t[2] in test_personas]

    # invariance transform, TRAIN-only canonical (no test leakage)
    canonical = canonical_log_centroid([M for M, *_ in train])
    tr = [(invariant_transform(M, canonical), w[0]) for M, w, *_ in train]
    te = [(invariant_transform(M, canonical), w[0]) for M, w, *_ in test]
    return tr, te, sorted(test_personas), len(IT.VOCAB)


# ---- the probe ------------------------------------------------------------

ALL = ["traj", "velocity", "curvature", "formant_ratio", "band_vs_band"]


def evaluate(tr, te, components):
    tr_vecs = [utt_descriptor(M, components) for M, _ in tr]
    te_vecs = [utt_descriptor(M, components) for M, _ in te]
    tr_words = [w for _, w in tr]
    te_words = [w for _, w in te]
    all_vecs = tr_vecs + te_vecs
    all_words = tr_words + te_words
    nn = one_nn_same_word(all_vecs, all_words)
    oc = oracle_centroid_acc(tr_vecs, tr_words, te_vecs, te_words)
    return nn, oc


def run(n_reps=4, seed=1, verbose=True):
    tr, te, held, n_vocab = build_corpus(n_reps, seed)
    chance = 1.0 / n_vocab
    if verbose:
        print(f"held-out personas (speaker-independent): {held}")
        print(f"  train {len(tr)} utts / test {len(te)} utts / "
              f"{n_vocab} words (chance {chance:.3f})\n")

    # --- BEFORE: the iter-9/10 baselines -----------------------------------
    res = {"chance": chance, "n_vocab": n_vocab}
    for mode in ("traj", "rate_inv"):
        tv = [baseline_descriptor(M, mode) for M, _ in tr]
        ev = [baseline_descriptor(M, mode) for M, _ in te]
        twd = [w for _, w in tr]
        ewd = [w for _, w in te]
        nn = one_nn_same_word(tv + ev, twd + ewd)
        oc = oracle_centroid_acc(tv, twd, ev, ewd)
        res[f"base_{mode}"] = (nn, oc)
        if verbose:
            print(f"BEFORE  {mode:10s}: 1-NN {nn:.3f}   oracle-centroid {oc:.3f}")

    # --- per-feature ablation: each component ALONE, and cumulative add -----
    if verbose:
        print("\nPER-FEATURE (each component on its own):")
    for c in ALL:
        comp = {k: (k == c) for k in ALL}
        nn, oc = evaluate(tr, te, comp)
        res[f"only_{c}"] = (nn, oc)
        if verbose:
            print(f"  only {c:14s}: 1-NN {nn:.3f}   oracle-centroid {oc:.3f}")

    if verbose:
        print("\nCUMULATIVE (add one component at a time, traj->...):")
    on = {k: False for k in ALL}
    for c in ALL:
        on[c] = True
        nn, oc = evaluate(tr, te, dict(on))
        res[f"cum_{c}"] = (nn, oc)
        if verbose:
            added = "+".join(k for k in ALL if on[k])
            print(f"  {added:50s}: 1-NN {nn:.3f}   oracle-centroid {oc:.3f}")

    # --- AFTER: the full rich descriptor (all components) ------------------
    full = {k: True for k in ALL}
    nn, oc = evaluate(tr, te, full)
    res["rich_full"] = (nn, oc)
    if verbose:
        print(f"\nAFTER   rich (all): 1-NN {nn:.3f}   oracle-centroid {oc:.3f}")
        before = res["base_rate_inv"][1]
        print(f"\n>>> ORACLE-CENTROID: before {before:.3f} -> after {oc:.3f}  "
              f"(chance {chance:.3f})")
        print(f">>> clears 0.70? {'YES' if oc > 0.70 else 'NO'}")
    return res


def main():
    n_reps = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    run(n_reps=n_reps)


if __name__ == "__main__":
    main()
