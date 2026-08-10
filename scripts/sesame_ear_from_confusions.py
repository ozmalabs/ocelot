"""WIRE THE SESAME SPEECH WORLD THROUGH THE CONFUSION-DRIVEN EAR-COMPOSITION (the agent's OWN
machinery, domains/ear_composition) — NOT a hand-rolled search.

  1. recognise Sesame words with the UNIFORM band layout over the 128-bin FFT.
  2. harvest the agent's CONFUSIONS (true!=pred pairs, counted) on a held-out split.
  3. the agent COMPOSES ITS EAR: ear_composition.informativeness_vector (per-bin Fisher of the
     confused words, weighted by confusion count) -> equal_information_layout (a NON-uniform
     band layout: FINE bands exactly where it confuses Sesame words, coarse where it doesn't).
  4. re-recognise a fresh TEST split with that composed ear -> does putting resolution where it
     confuses words improve recognition? (same comparison composed_ear_accept makes on FSDD.)

The agent designs its own perceptual resolution map for Sesame's vocabulary, from its own
mistakes. Run: python scripts/sesame_ear_from_confusions.py [study_min] [res_out]
"""
from __future__ import annotations
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import pickle
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

from domains.ear_composition import informativeness_vector, equal_information_layout

CACHE = "/tmp/sesame_fft_words.pkl"
N_BINS = 128
SR = 8000


def word_fft(a8, wt0, wt1, n_fft=256, hop=128):
    """per-clip mean 128-bin linear FFT spectrum (the agent's fft_trajectory analog)."""
    seg = a8[int(wt0 * SR):int(wt1 * SR)]
    if len(seg) < n_fft:
        seg = np.pad(seg, (0, n_fft - len(seg)))
    win = np.hanning(n_fft)
    frames = [np.abs(np.fft.rfft(seg[i:i + n_fft] * win))[:N_BINS]
              for i in range(0, len(seg) - n_fft + 1, hop)]
    if not frames:
        frames = [np.abs(np.fft.rfft(seg[:n_fft] * win))[:N_BINS]]
    return np.asarray(frames).mean(0)                 # (128,)


def collect(study_min):
    if os.path.exists(CACHE):
        with open(CACHE, "rb") as f:
            return pickle.load(f)
    from scripts.sesame_speech_world import SesameSpeechWorld
    w = SesameSpeechWorld(episode_idx=0)
    toks = []
    chunk = 25.0
    end = min(study_min * 60, w.duration - 30)
    t = 30.0
    while t < end:
        words = w.whisper(t, t + chunk)
        if words:
            a8 = w.play(t, t + chunk)
            for word, wt0, wt1 in words:
                toks.append((word, word_fft(a8, wt0, wt1).astype(np.float32)))
        t += chunk
    with open(CACHE, "wb") as f:
        pickle.dump(toks, f)
    print(f"  collected {len(toks)} word tokens -> {CACHE}", flush=True)
    return toks


def band(spec, boundaries):
    """fold the 128-bin spectrum into the layout's bands (log mean energy per band)."""
    out = np.empty(len(boundaries) - 1)
    for j in range(len(boundaries) - 1):
        lo, hi = boundaries[j], max(boundaries[j] + 1, boundaries[j + 1])
        out[j] = np.log(spec[lo:hi].mean() + 1e-6)
    return out


def feat(spec, boundaries):
    f = band(spec, boundaries)
    return f / (np.linalg.norm(f) + 1e-9)


def recognise(train, val, boundaries, k=3):
    """cosine-kNN over band features; returns accuracy (in-vocab) + confusion pairs counted."""
    vocab = set(wd for wd, _ in train)
    Xtr = np.array([feat(sp, boundaries) for _, sp in train])
    Wtr = np.array([wd for wd, _ in train])
    correct = total = 0
    conf = Counter()
    for wd, sp in val:
        if wd not in vocab:
            continue
        q = feat(sp, boundaries)
        top = Wtr[np.argsort(-(Xtr @ q))[:k]]
        pred = max(set(top), key=lambda c: list(top).count(c))
        total += 1; correct += (pred == wd)
        if pred != wd:
            conf[(wd, pred)] += 1
    return (correct / total if total else 0.0), total, conf


def main():
    study_min = float(sys.argv[1]) if len(sys.argv) > 1 else 8.0
    res_out = int(sys.argv[2]) if len(sys.argv) > 2 else 32
    min_ex = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    toks = collect(study_min)
    # the ear-composition needs DENSE confusions; Sesame's huge vocab is too sparse. Focus on
    # the LEARNABLE CORE — the frequent words (Sesame's deliberate repetition gives them many
    # exemplars) — the regime that matches FSDD's 10 dense digit classes.
    cnt = Counter(wd for wd, _ in toks)
    core = {wd for wd, c in cnt.items() if c >= min_ex}
    toks = [(wd, sp) for wd, sp in toks if wd in core]
    print(f"  core vocabulary (>= {min_ex} exemplars): {len(core)} words, {len(toks)} tokens")
    rng = np.random.RandomState(0)
    idx = rng.permutation(len(toks))
    n = len(toks); a, b = n * 60 // 100, n * 80 // 100
    train = [toks[i] for i in idx[:a]]           # exemplars
    valc = [toks[i] for i in idx[a:b]]           # harvest confusions
    test = [toks[i] for i in idx[b:]]            # final eval
    print("=" * 78)
    print("SESAME EAR FROM CONFUSIONS — the agent composes its ear via ear_composition")
    print(f"  {n} word tokens ({len(set(w for w,_ in toks))} words); "
          f"{len(train)} train / {len(valc)} conf-harvest / {len(test)} test", flush=True)
    print("=" * 78)

    uni = list(np.linspace(0, N_BINS, res_out + 1).round().astype(int))   # uniform layout

    # 1+2: recognise with the uniform ear; harvest the agent's Sesame confusions.
    acc_u_val, _, conf = recognise(train, valc, uni)
    pairs = sorted(((X, Y, c) for (X, Y), c in conf.items()), key=lambda t: -t[2])
    print(f"\n  uniform-{res_out} ear: harvested {sum(c for *_ , c in pairs)} confusions "
          f"over {len(pairs)} word-pairs")
    print("  top confused Sesame word-pairs:")
    print("   ", ", ".join(f"{X}->{Y}x{c}" for X, Y, c in pairs[:8]))

    # 3: the agent COMPOSES its ear from those confusions.
    spectra = defaultdict(list)
    for wd, sp in train + valc:
        spectra[wd].append(sp)
    spectra = {wd: np.asarray(v) for wd, v in spectra.items() if len(v) >= 2}
    info, used = informativeness_vector(spectra, pairs, N_BINS)
    comp = equal_information_layout(info, res_out)
    # show where it put its resolution (narrowest bands, in Hz)
    widths = [(comp[j + 1] - comp[j], comp[j], comp[j + 1]) for j in range(len(comp) - 1)]
    fine = sorted(widths)[:4]
    hz = lambda k: k / N_BINS * (SR / 2)
    print(f"\n  agent composed a {len(comp)-1}-band ear from {len(used)} confused pairs; "
          f"narrowest bands (where it put resolution):")
    for wbins, lo, hi in fine:
        print(f"    {hz(lo):4.0f}-{hz(hi):4.0f} Hz (width {wbins} bins)")

    # 4: re-recognise the fresh TEST split — uniform ear vs the agent's composed ear.
    acc_u, n_u, _ = recognise(train, test, uni)
    acc_c, n_c, _ = recognise(train, test, comp)
    print("\n  " + "=" * 70)
    print(f"  TEST recognition ({n_u} in-vocab words):")
    print(f"    uniform-{res_out} ear           : {acc_u:.1%}")
    print(f"    agent-COMPOSED-{res_out} ear     : {acc_c:.1%}   ({acc_c-acc_u:+.1%})")
    print("=" * 78)
    print("  the agent designed its Sesame ear from its OWN confusions (ear_composition),")
    print("  putting fine resolution exactly where it confuses Sesame words.")


if __name__ == "__main__":
    main()
