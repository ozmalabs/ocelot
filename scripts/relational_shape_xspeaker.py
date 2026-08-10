"""relational_shape_xspeaker — DO-CONTRAST: does the agent's WHOLE-UNIT RELATIONAL
representation beat the SURFACE-acoustic baseline on the cross-speaker venue where
five other levers nulled?

VENUE (identical to scripts/real_speech.py — the venue everything else nulled on):
  Google Speech Commands /tmp/sc, ~2000 speakers, TRAIN and TEST speakers DISJOINT.
  Recognition = nearest-exemplar over the train lexicon. The distance in BOTH arms
  is the agent's native DtwTo Term (substrate.evaluate) — counts not nets, no .fit.

ARMS (same exemplars, same DtwTo decision, only the REPRESENTATION differs):
  A  SURFACE      raw gammatone band trajectory (frames x bands).  The transform-
                  fragile baseline — the thing to beat.
  B  RELATIONAL   the agent's whole-unit relational shape (domains/relational_shape):
                  per-frame ORDINAL band-RANK profile (which band > which — invariant
                  to the talker's per-frame additive level + global gain by
                  construction) ++ a WHOLE-UNIT SELF-SIMILARITY row (each frame's rank
                  agreement with the unit's own phase anchors — a relation internal to
                  the unit, invariant to any uniform talker transform).  Composed from
                  the agent's owned ops (Gt/IfThenElse/Plus/Vec/Minus/Abs); evaluated
                  natively.
  SHUFFLE backstop on B: exemplar word-labels permuted -> must collapse to chance.

READ THE NUMBERS: report k/N and % for every arm; per-clip resolution; B must beat A
by a MARGIN clearly above noise (> ~3 clips AND above the shuffle margin).  An honest
NULL is a genuine result.

Run: python -m scripts.relational_shape_xspeaker [n_words] [n_train] [n_test] [n_anchors]
"""
import os
import sys
import random
import time
import wave
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
import domains.recognition_graph as RG
from scripts.invariant_units_accept import band_trajectory_matrix
from domains.relational_shape import relational_shape

SC = "/tmp/sc"


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def load_real(path):
    w = wave.open(path)
    raw = (np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
           .astype(np.float32) / 32768.0)
    if w.getframerate() == 16000:
        try:
            from scipy.signal import decimate
            raw = decimate(raw, 2)
        except Exception:
            raw = raw[::2]
    return np.ascontiguousarray(raw.astype(np.float32)), 8000


def as_tuple(M):
    return tuple(tuple(float(v) for v in row) for row in np.asarray(M))


# ---------------------------------------------------------------------------
# Native nearest-exemplar recogniser.  The exemplar lexicon is a set of Concept
# nodes (one per train clip) carrying the clip's representation as a graph attr;
# the heard clip's representation is written on a Sign node.  The decision is the
# native DtwTo distance (substrate.evaluate) argmin over exemplars — no numpy in
# the score.  Identical machinery in both arms.
# ---------------------------------------------------------------------------

def main():
    n_words = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    n_train = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    n_test = int(sys.argv[3]) if len(sys.argv) > 3 else 400
    n_anchors = int(sys.argv[4]) if len(sys.argv) > 4 else 6
    random.seed(1)
    np.random.seed(1)

    t0 = time.time()
    avail = [w for w in sorted(os.listdir(SC))
             if os.path.isdir(os.path.join(SC, w)) and not w.startswith("_")
             and len([f for f in os.listdir(os.path.join(SC, w))
                      if f.endswith(".wav")]) > 200]
    words = avail[:n_words]
    chance = 1.0 / len(words)
    print("=" * 72, flush=True)
    print("RELATIONAL-SHAPE vs SURFACE — cross-speaker Speech Commands", flush=True)
    print("=" * 72, flush=True)
    print(f"{len(words)}-way: {words}  (chance {100*chance:.1f}%)", flush=True)

    data = {}
    for w in words:
        for fn in sorted(os.listdir(os.path.join(SC, w))):
            if fn.endswith(".wav"):
                data.setdefault(w, []).append(
                    (os.path.join(SC, w, fn), fn.split("_")[0]))

    # Hold out whole SPEAKERS for test (train/test speakers DISJOINT).
    test_spk = set()
    for w in words:
        spks = sorted({s for _, s in data[w]})
        test_spk |= set(spks[::6])
    train = [(p, w) for w in words for p, s in data[w] if s not in test_spk]
    test = [(p, w) for w in words for p, s in data[w] if s in test_spk]
    random.shuffle(train)
    random.shuffle(test)
    train, test = train[:n_train], test[:n_test]
    print(f"train exemplars {len(train)} (disjoint speakers); "
          f"test {len(test)} from HELD-OUT speakers", flush=True)
    print(f"per-clip resolution: {100.0/len(test):.3f}%  "
          f"(n_anchors={n_anchors})", flush=True)

    # ---- extract band matrices once; derive both representations from them ----
    def band_M(path):
        x, fs = load_real(path)
        M = band_trajectory_matrix(x, fs)
        return M if M is not None and len(M) >= 2 else None

    print(f"\nextracting band matrices ({time.time()-t0:.0f}s)...", flush=True)
    tr_band = [(band_M(p), w) for p, w in train]
    te_band = [(band_M(p), w) for p, w in test]
    tr_band = [(M, w) for M, w in tr_band if M is not None]
    te_band = [(M, w) for M, w in te_band if M is not None]
    print(f"  usable: {len(tr_band)} train, {len(te_band)} test "
          f"({time.time()-t0:.0f}s)", flush=True)

    # Pre-compute the relational shape for every clip (native evaluation).
    print("composing RELATIONAL shapes (native substrate.evaluate)...", flush=True)
    tr_rel = [(relational_shape(M, n_anchors=n_anchors), w) for M, w in tr_band]
    te_rel = [(relational_shape(M, n_anchors=n_anchors), w) for M, w in te_band]
    print(f"  relational shapes composed ({time.time()-t0:.0f}s)", flush=True)

    sub = Substrate()
    sign = sub.add_node("HeardSign", {})
    err = _Pred(RG._DtwTo(RG._Attr(RG._V("s"), "rep"),
                          RG._Attr(RG._V("w"), "rep")))

    def run_arm(tag, tr_reprs, te_reprs, shuffle=False):
        ex_words = [w for _, w in tr_reprs]
        if shuffle:
            ex_words = list(ex_words)
            random.Random(7).shuffle(ex_words)
        # build lexicon
        exs = []
        for (M, _), w in zip(tr_reprs, ex_words):
            if M is None or len(M) < 2:
                continue
            c = sub.add_node("Exemplar", {"word": w})
            sub.set_attr(c, "rep", as_tuple(M))
            exs.append((c, w))
        corr = tot = 0
        per_word = defaultdict(lambda: [0, 0])
        for M, w in te_reprs:
            if M is None or len(M) < 2:
                continue
            sub.set_attr(sign, "rep", as_tuple(M))
            best_d, best_w = 1e18, None
            for c, ew in exs:
                d = sub.evaluate(err, {"s": sign, "w": c})
                if d < best_d:
                    best_d, best_w = d, ew
            ok = int(best_w == w)
            corr += ok
            tot += 1
            per_word[w][0] += ok
            per_word[w][1] += 1
        # tear the exemplar nodes back down so arms don't pool
        for c, _ in exs:
            sub.remove_node(c)
        acc = corr / max(tot, 1)
        se = (acc * (1 - acc) / max(tot, 1)) ** 0.5
        print(f"\n[{tag}]  {corr}/{tot} = {100*acc:.2f}%  "
              f"(SE {100*se:.2f}%, chance {100*chance:.1f}%)", flush=True)
        return {"acc": acc, "corr": corr, "tot": tot, "se": se,
                "per_word": dict(per_word)}

    print("\n" + "=" * 72, flush=True)
    print("ARM A — SURFACE (raw gammatone band trajectory, native DtwTo NN)",
          flush=True)
    print("=" * 72, flush=True)
    A = run_arm("SURFACE", tr_band, te_band)

    print("\n" + "=" * 72, flush=True)
    print("ARM B — RELATIONAL (agent whole-unit relational shape, native DtwTo NN)",
          flush=True)
    print("=" * 72, flush=True)
    B = run_arm("RELATIONAL", tr_rel, te_rel)

    print("\n" + "=" * 72, flush=True)
    print("SHUFFLE backstop on B (exemplar labels permuted -> must collapse)",
          flush=True)
    print("=" * 72, flush=True)
    Bsh = run_arm("RELATIONAL-SHUFFLE", tr_rel, te_rel, shuffle=True)

    # ---- VERDICT — read the numbers, not a boolean ----
    print("\n" + "=" * 72, flush=True)
    print("VERDICT", flush=True)
    print("=" * 72, flush=True)
    print(f"  A SURFACE     {A['corr']}/{A['tot']} = {100*A['acc']:.2f}%  "
          f"(SE {100*A['se']:.2f}%)", flush=True)
    print(f"  B RELATIONAL  {B['corr']}/{B['tot']} = {100*B['acc']:.2f}%  "
          f"(SE {100*B['se']:.2f}%)", flush=True)
    print(f"  B SHUFFLE     {Bsh['corr']}/{Bsh['tot']} = {100*Bsh['acc']:.2f}%  "
          f"(chance {100*chance:.1f}%)", flush=True)
    margin_clips = B["corr"] - A["corr"]
    margin_pct = 100 * (B["acc"] - A["acc"])
    sh_margin_clips = B["corr"] - Bsh["corr"]
    pooled_se = 100 * ((A["se"] ** 2 + B["se"] ** 2) ** 0.5)
    print(f"\n  B - A   = {margin_clips:+d} clips ({margin_pct:+.2f}%)  "
          f"pooled SE {pooled_se:.2f}%", flush=True)
    print(f"  B - shuf= {sh_margin_clips:+d} clips", flush=True)
    if margin_clips > 3 and margin_pct > pooled_se and sh_margin_clips > 3:
        print("\n  >>> LIFT: relational-shape beats surface by a margin above noise "
              "AND above shuffle. The whole-unit relational representation survives "
              "the speaker transform where surface acoustics break.", flush=True)
    elif margin_clips > 3 and margin_pct > pooled_se:
        print("\n  >>> PARTIAL: relational beats surface above noise but the shuffle "
              "margin is thin — report with the caveat.", flush=True)
    else:
        print("\n  >>> NULL: relational-shape does NOT beat surface by a resolvable "
              "margin. Honest result — the relations are computed off a blurry "
              "cochlea (so the ordinal ranks/recurrence are themselves noisy across "
              "speakers), and/or the structural match is too permissive. Report "
              "plainly; do NOT sweep a gain.", flush=True)


if __name__ == "__main__":
    main()
