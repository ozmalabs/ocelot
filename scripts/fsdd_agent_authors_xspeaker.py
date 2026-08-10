"""The jabberwock WIRES ITS OWN cross-speaker fix. The agent derived the gap (ratio /
per-source normalisation cancels the vocal-tract scale; agent_derives_xspeaker.py). Its
generate-and-select feature faculty (domains/feature_generator) can AUTHOR exactly that:
generate_feature composes Term-trees from its grammar — including Div, i.e. band RATIOS,
which are gain/VTL-robust by construction — and discover_features_mdl SELECTS the ones
that generalise across a speaker split by its OWN MDL/compression drive. So the agent
composes + selects its own ratio features; this shell only supplies FSDD signs (held
cochlea band attrs) and MEASURES recognition on the agent's features vs raw bands.

The agent's features are scale-free (a ratio cancels the per-utterance gain the raw
bands carry) — the closed-form ratio normalisation it derived, AUTHORED by the agent,
not hand-written.

Run: python scripts/fsdd_agent_authors_xspeaker.py [test_speaker] [n_per] [n_gen]
"""
from __future__ import annotations
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

from substrate_rs import Substrate
from substrate_rs.speech import _audio
from domains.feature_generator import discover_features_mdl
from scripts.speech_analysis_by_synthesis import load_wav, feat, DATA, FN, N_BANDS

N_WIN = 12
BANDS = [f"b{i}_{w}" for i in range(N_BANDS) for w in range(N_WIN)]   # full band x window


def sign_node(s, f):
    """A node carrying the utterance's full (band x window) cochlear cells as attrs the
    agent's feature Term-trees read via Attr(Var('s'), 'bI_W'). The agent composes RATIOS
    over these cells (Div) — gain/VTL-robust by construction (the normalisation it derived)."""
    a = {f"b{i}_{w}": float(f[i, w]) for i in range(N_BANDS) for w in range(f.shape[1])}
    return s.add_node("Concept", a)


def onehot_1nn(train_vecs, train_lab, q):
    d = np.abs(train_vecs - q).sum(axis=1)     # Hamming over the agent's boolean features
    return train_lab[int(d.argmin())]


def raw_1nn(train_vecs, train_lab, q):
    Xn = train_vecs / (np.linalg.norm(train_vecs, axis=1, keepdims=True) + 1e-9)
    qn = q / (np.linalg.norm(q) + 1e-9)
    return train_lab[int((Xn @ qn).argmax())]  # cosine 1-NN on raw bands


def main():
    test_spk = sys.argv[1] if len(sys.argv) > 1 else "george"
    n_per = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    n_gen = int(sys.argv[3]) if len(sys.argv) > 3 else 1200
    files = []
    for fn in sorted(os.listdir(DATA)):
        m = FN.match(fn)
        if m and int(m.group(3)) < n_per:
            files.append((os.path.join(DATA, fn), int(m.group(1)), m.group(2)))

    s = Substrate()
    _audio.seed_audio_grammar(s)
    bank = _audio.cochlea(s, n_bands=N_BANDS, fs=8000)

    # Build signs (held cochlea band attrs) + keep the raw band vector for the baseline.
    rows = []           # (digit, speaker, sign_nid, raw_env)
    for path, digit, spk in files:
        samples, fs = load_wav(path)
        f = feat(s, bank, samples, fs)
        rows.append((digit, spk, sign_node(s, f), f.flatten().astype(np.float64)))

    train = [r for r in rows if r[1] != test_spk]
    test = [r for r in rows if r[1] == test_spk]
    train_spk = sorted({r[1] for r in train})

    # === THE AGENT AUTHORS: split TRAIN speakers into two halves; the agent generates
    # ratio/diff feature Term-trees and SELECTS (MDL + must generalise across the split)
    # — its own compression drive picks the cross-speaker-robust features. ===
    half = set(train_spk[: len(train_spk) // 2])
    by_a, by_b = {}, {}
    for digit, spk, nid, _env in train:
        (by_a if spk in half else by_b).setdefault(digit, []).append(nid)
    print("=" * 78)
    print(f"JABBERWOCK AUTHORS its cross-speaker features (generate-and-select)")
    print(f"  held-out={test_spk}  {n_per}/digit/spk  gen={n_gen}  split={sorted(half)} | "
          f"{sorted(set(train_spk)-half)}")
    print("=" * 78)
    kept = discover_features_mdl(s, by_a, by_b, BANDS, n=n_gen, keep=12, lam=0.03, seed=0)
    print(f"  agent generated {n_gen} feature Term-trees, kept {len(kept)} by MDL+CV:")
    for score, gen, size, term in kept[:6]:
        print(f"    score={score:+.3f} gen={gen:.2f} size={size:2d}")
    feats = [term for (_sc, _g, _sz, term) in kept]
    if not feats:
        print("  agent selected NO generalising features — frozen edge.")
        return

    def agent_vec(nid):
        return np.array([1.0 if s.evaluate(t, {"s": nid}) else 0.0 for t in feats])

    trV = np.array([agent_vec(r[2]) for r in train]); trL = np.array([r[0] for r in train])
    teV = [(r[0], agent_vec(r[2])) for r in test]
    trR = np.array([r[3] for r in train]); teR = [(r[0], r[3]) for r in test]

    n = len(test)
    raw_ok = sum(raw_1nn(trR, trL, q) == d for d, q in teR)
    agt_ok = sum(onehot_1nn(trV, trL, q) == d for d, q in teV)
    print(f"\n  raw bands (cosine 1-NN):              {raw_ok}/{n} = {raw_ok/n:.1%}")
    print(f"  AGENT-AUTHORED ratio features (1-NN):  {agt_ok}/{n} = {agt_ok/n:.1%}   "
          f"(delta {(agt_ok-raw_ok)/n:+.1%})")
    print("=" * 78)


if __name__ == "__main__":
    main()
