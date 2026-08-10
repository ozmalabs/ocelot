"""SHARPEN LARGE VOCAB — POSITIONALLY-RESOLVED cues (onset / nucleus / coda each its own factor).

The large-vocab top-1 ceiling is acoustic: confusable words differ in the consonant ONSET, but the static
L2-pooled cues are VOWEL-ENERGY-dominated -- the onset is a small, low-energy slice of the pooled vector, so
the vowel drowns the very thing that separates cat/bat/hat/mat. The temporal lever: split each word at its
energy NUCLEUS (the vowel) into onset / nucleus / coda and cue each region SEPARATELY, so the onset consonant
gets EQUAL say as a factor in the combine-all product instead of being averaged away.

  M = sharp-time cochleagram (frames x bands) ; e = per-frame energy ;
  nucleus = contiguous high-energy span ; onset = before it ; coda = after it ;
  each region -> resample to k frames -> L2 = one positional cue.

Tests full cues vs full + positional vs positional-only, cross-speaker LOSO + WCCN, on (a) a deliberately
onset-confusable CVC vocab (where the lever should bite hardest) and (b) the realistic mixed vocab.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_positional_cues
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import substrate_rs as srs
import domains.agent_frontend as FE
import domains.many_settings_recognizer as MS
from domains import wccn
from domains.filter_settings import cochleagram
from domains.speech_world import SpeechWorld
from scripts.jabberwock_largevocab_diag import WORDS, SPEAKERS, RENDS, set_active

FS = 8000
KREC = 6
NF = 48
KSUB = 6                 # frames each region is resampled to

CVC = [
    "cat", "bat", "hat", "mat", "rat", "sat", "fat", "pat",     # _at  (onset family)
    "big", "dig", "fig", "pig", "wig", "rig",                   # _ig
    "bed", "red", "led", "fed", "wed",                          # _ed
    "cap", "map", "nap", "tap", "gap", "lap",                   # _ap
    "ten", "pen", "hen", "den", "men",                          # _en
    "bug", "dug", "hug", "jug", "mug", "rug",                   # _ug
]


def _l2(v):
    v = np.asarray(v, dtype=np.float64)
    return v / (np.linalg.norm(v) + 1e-9)


def positional_cues(x, fs):
    """onset / nucleus / coda regional cues — split at the energy nucleus, each region L2'd separately."""
    M = cochleagram(x, fs, env_cut=120.0, dur_cut=200.0, n_frames=NF)   # (NF, nbands)
    M = np.asarray(M, dtype=np.float64)
    e = M.sum(1)
    if e.max() <= 0:
        nb = M.shape[1]; return [np.zeros(nb * KSUB) for _ in range(3)]
    hi = np.where(e > 0.45 * e.max())[0]
    n0, n1 = (hi[0], hi[-1] + 1) if len(hi) else (0, NF)
    out = []
    for a, b in ((0, n0), (n0, n1), (n1, NF)):
        seg = M[a:b]
        if len(seg) == 0:
            out.append(np.zeros(M.shape[1] * KSUB)); continue
        idx = np.linspace(0, len(seg) - 1, KSUB)
        res = seg[np.round(idx).astype(int)]          # (KSUB, nbands)
        out.append(_l2(res.flatten()))
    return out


def evaluate(feats, words, cue_idx):
    t1 = inK = tot = 0
    for held in SPEAKERS:
        bank = [(w, [feats[(v, w, r)][c] for c in cue_idx]) for v in SPEAKERS if v != held
                for w in words for r in (0, 1) if (v, w, r) in feats]
        cands = sorted({w for (w, _x) in bank})
        Ws = wccn.fit_per_cue(bank)
        bw = [(w, wccn.whiten(v, Ws)) for (w, v) in bank]
        ncue = len(bw[0][1])
        allX = [np.stack([v[c] for (_w, v) in bw]) for c in range(ncue)]
        alllab = [w for (w, _v) in bw]
        for w0 in words:
            for r in range(RENDS):
                if (held, w0, r) not in feats:
                    continue
                q = wccn.whiten([feats[(held, w0, r)][c] for c in cue_idx], Ws)
                logp = {c: 0.0 for c in cands}
                for ci in range(ncue):
                    p = MS.channel_likelihood(np.asarray(q[ci]), allX[ci], alllab, cands)
                    for cc in cands:
                        logp[cc] += np.log(p[cc] + 1e-12)
                rank = sorted(cands, key=lambda cc: -logp[cc])
                tot += 1; t1 += int(rank[0] == w0); inK += int(w0 in rank[:KREC])
    return t1 / max(tot, 1), inK / max(tot, 1)


def run_vocab(label, words, feats, n_full):
    full = list(range(n_full))
    pos = list(range(n_full, n_full + 3))
    print(f"\n  [{label}] {len(words)} words")
    f1, fk = evaluate(feats, words, full)
    p1, pk = evaluate(feats, words, full + pos)
    o1, ok = evaluate(feats, words, pos)
    print(f"    {'full cues':<22}{f1*100:>6.0f}% top-1   {fk*100:>4.0f}% recall")
    print(f"    {'full + positional':<22}{p1*100:>6.0f}% top-1   {pk*100:>4.0f}% recall   ({(p1-f1)*100:+.0f}pt)")
    print(f"    {'positional only':<22}{o1*100:>6.0f}% top-1   {ok*100:>4.0f}% recall")
    return (p1 - f1)


def main():
    print("=" * 96)
    print("POSITIONALLY-RESOLVED CUES — does onset/nucleus/coda resolution break the large-vocab ceiling?")
    print("=" * 96)
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0})
    sw = SpeechWorld(s, source_world=None)
    FE.install_curated_frontend(s)
    fe = next(n for n in s.nodes("FrontEnd"))
    allnames = [s.node(c)["attrs"].get("name") for et in ("has_cue", "repertoire") for c in s.neighbours(fe, et)]
    set_active(s, fe, allnames)
    n_full = len(allnames)

    vocab = sorted(set(CVC) | set(WORDS))
    print(f"  caching audio + full({n_full}) + positional(3) cues for {len(vocab)} words...", flush=True)
    feats = {}
    for v in SPEAKERS:
        for w in vocab:
            for r in range(RENDS):
                out = sw.synth(w, {"variant": v, "pitch": 50, "rate": 175})
                if out is not None:
                    x = np.asarray(out[0], dtype=np.float64)
                    feats[(v, w, r)] = FE.feature_channels(s, x, out[1]) + positional_cues(x, out[1])

    d_cvc = run_vocab("CVC onset-confusable", CVC, feats, n_full)
    d_real = run_vocab("realistic mixed", WORDS, feats, n_full)

    print("\n" + "=" * 96)
    print(f"  positional cues: CVC {d_cvc*100:+.0f}pt | realistic {d_real*100:+.0f}pt top-1")
    if d_cvc > 0.04 or d_real > 0.04:
        print("  THE TEMPORAL LEVER BITES: resolving onset/nucleus/coda gives the consonant equal say in the product,")
        print("  separating confusable words the vowel-dominated pooled cues blur. Add the 3 positional cues to the")
        print("  agent's repertoire -- a no-gradient front-end extension, biggest where words rhyme.")
    else:
        print(f"  positional cues do NOT break the ceiling (CVC {d_cvc*100:+.0f}, real {d_real*100:+.0f}) -- the onset detail")
        print("  is lost upstream (8kHz / coarse frames) or the split is too crude; the ceiling stays the language prior's.")
    print("=" * 96)


if __name__ == "__main__":
    main()
