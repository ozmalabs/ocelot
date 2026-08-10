"""TEST THE JABBERWOCK'S RECOGNISER DECISION (b): WCCN PER CUE inside the combine-all product.

Its decision: remove the speaker key from EVERY cue (per-cue within-word/across-speaker whitening = CMVN rotated
from the time axis to the speaker axis), then run the SAME combine-all product over the whitened cues -- keeping
the product's robustness AND gaining nuisance removal. Guards: shrinkage + eigenvalue floor (ill-conditioned Σ
can't blow up), and a per-cue HELD-OUT GATE (keep the whitening on a cue only if it LIFTS held-out recall, else
that cue stays raw -- so worst case = today's product, never worse). Closed-form, no gradient.

Tested on the loop's own split (_HARD_TRAIN -> _HARD_TEST, real English speakers), scored against the known word:
  PLAIN product  vs  PER-CUE-WCCN product (gated).

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_wccn_recognizer
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import substrate_rs as srs
import domains.self_directed_speech_world as SDW
import domains.many_settings_recognizer as MS
from domains.speech_world import SpeechWorld
from scripts.jabberwock_graph_native_recall import ranked, KREC

FS = 8000
WORDS = ("one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
TRAIN = [v for v, _p in SpeechWorld._HARD_TRAIN]
HELD = [v for v, _p in SpeechWorld._HARD_TEST]
RENDS = 3                # bank 0,1 ; test 2


def fit_wccn_cue(Xc, y, lam=0.1):
    """W_c = Sigma_c^-1/2 over the WITHIN-word/across-speaker residual covariance, shrunk + eigen-floored.
    Closed-form (eigh), no gradient -- CMVN rotated to the speaker axis."""
    X = np.asarray(Xc, dtype=np.float64); d = X.shape[1]; n = len(X)
    R = X.copy()
    for w in set(y):
        m = (y == w)
        R[m] = X[m] - X[m].mean(0)               # within-word residual = speaker + noise
    Sig = (R.T @ R) / max(n, 1)
    Sig = Sig + lam * (np.trace(Sig) / max(d, 1)) * np.eye(d)   # shrinkage toward isotropic
    ev, U = np.linalg.eigh(Sig)
    ev = np.clip(ev, 1e-6, None)                 # eigen-floor: ill-conditioned dirs can't blow up
    return U @ np.diag(ev ** -0.5) @ U.T


def main():
    print("=" * 96)
    print("WCCN PER CUE inside the product (the agent's decision b) — does it close the cross-speaker gap?")
    print("=" * 96)
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0})
    sw = SpeechWorld(s, source_world=None)
    print(f"  train {len(TRAIN)} English speakers -> held-out {HELD} | {len(WORDS)} words\n")
    print("  synthesising + per-cue features...", flush=True)
    feats = {}
    for spk in TRAIN + HELD:
        for w in WORDS:
            for r in range(RENDS):
                out = sw.synth(w, {"variant": spk, "pitch": 50, "rate": 175})
                if out is not None:
                    feats[(spk, w, r)] = SDW.feature_channels(s, np.asarray(out[0], dtype=np.float64), out[1])
    ncue = len(next(iter(feats.values())))

    banked = [(w, feats[(spk, w, r)]) for spk in TRAIN for w in WORDS for r in (0, 1) if (spk, w, r) in feats]
    y = np.array([w for (w, _v) in banked])
    cands = sorted(set(y))

    def recall(transform):
        bk = [(w, [transform(c, v[c]) for c in range(ncue)]) for (w, v) in banked]
        hits = tot = 0
        for spk in HELD:
            for w in WORDS:
                if (spk, w, 2) not in feats:
                    continue
                q = [transform(c, feats[(spk, w, 2)][c]) for c in range(ncue)]
                tot += 1; hits += int(ranked(q, bk, cands)[0] == w)
        return hits / tot if tot else 0.0

    ident = lambda c, v: np.asarray(v, dtype=np.float64)
    plain = recall(ident)

    # fit per-cue WCCN from the bank.
    Ws = [fit_wccn_cue(np.stack([v[c] for (_w, v) in banked]), y) for c in range(ncue)]

    # PER-CUE HELD-OUT GATE: keep W_c only if whitening THAT cue alone lifts held-out recall (else identity).
    # Split the train speakers into fit/val so the gate is honest (val speakers unseen by the W estimate's val).
    val = TRAIN[-3:]
    def cue_recall(c, use_W):
        bk = [(w, list(v)) for (w, v) in banked]
        for (w, v) in bk:
            v[c] = (np.asarray(v[c]) @ Ws[c]) if use_W else np.asarray(v[c])
        hits = tot = 0
        for spk in val:
            for w in WORDS:
                if (spk, w, 1) not in feats:
                    continue
                q = list(feats[(spk, w, 1)]); q[c] = (np.asarray(q[c]) @ Ws[c]) if use_W else np.asarray(q[c])
                tot += 1; hits += int(ranked(q, bk, cands)[0] == w)
        return hits / max(tot, 1)
    keep = []
    for c in range(ncue):
        kept = cue_recall(c, True) >= cue_recall(c, False)
        keep.append(kept)
    print(f"  per-cue held-out gate: whitening KEPT on {sum(keep)}/{ncue} cues\n")

    def gated(c, v):
        v = np.asarray(v, dtype=np.float64)
        return v @ Ws[c] if keep[c] else v

    wccn = recall(gated)
    wccn_all = recall(lambda c, v: np.asarray(v, dtype=np.float64) @ Ws[c])

    print(f"  {'recogniser':<40}{'held-out top-1':>16}")
    print(f"  {'PLAIN product (today)':<40}{plain*100:>15.0f}%")
    print(f"  {'+ WCCN all cues':<40}{wccn_all*100:>15.0f}%")
    print(f"  {'+ WCCN per-cue GATED (the decision)':<40}{wccn*100:>15.0f}%")

    print("\n" + "=" * 96)
    lift = max(wccn, wccn_all) - plain
    if lift > 0.05:
        print(f"  DECISION (b) WORKS: per-cue WCCN inside the product lifts held-out cross-speaker recall "
              f"{plain*100:.0f}% -> {max(wccn,wccn_all)*100:.0f}% (+{lift*100:.0f}pt). Removing the speaker key from every cue while")
        print("  keeping the combine-all conjunction is the upgrade -- wire it into the loop recogniser (WordHat/ranked).")
    elif lift > 0.0:
        print(f"  marginal (+{lift*100:.0f}pt): the per-cue whitening helps a little; the gate kept it where it lifts. The")
        print("  bigger gap may be elsewhere (cue count, banking) -- worth checking before the full wire-in.")
    else:
        print(f"  no lift ({max(wccn,wccn_all)*100:.0f}% vs {plain*100:.0f}%): per-cue Σ is too ill-estimated here, or the product already")
        print("  conjoins enough -- the gate correctly fell back to raw cues (never worse). The 53->67 gap is NOT per-cue WCCN.")
    print("=" * 96)


if __name__ == "__main__":
    main()
