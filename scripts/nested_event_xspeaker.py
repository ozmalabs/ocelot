"""nested_event_xspeaker — DO-CONTRAST: does parsing each word into its DISCRETE
NESTED ORDER-N EVENT TREE and matching the TREE beat the SURFACE-acoustic wave
baseline on the cross-speaker venue where every wave-lever nulled?

THE REFRAME (domains/nested_event_tree): the acoustic "wave" is the un-parsed
appearance of a NESTED HIERARCHY OF DISCRETE ORDER-N EVENTS.  Recognise the discrete
nested event STRUCTURE (how many events at each order, their TYPES/ORDER/NESTING/
relative ordering — the message), not the continuous trajectory (the realization,
which the talker mangles).

VENUE (identical to scripts/real_speech.py / relational_shape_xspeaker — the venue
everything else nulled on): Google Speech Commands /tmp/sc, ~2000 speakers, TRAIN and
TEST speakers DISJOINT.  Recognition = nearest-exemplar over the train lexicon; the
distance in BOTH arms is the agent's NATIVE DtwTo Term (substrate.evaluate) — counts
not nets, no .fit.

ARMS (same exemplars, same native-DtwTo NN decision; only the REPRESENTATION differs):
  A  SURFACE  raw gammatone band trajectory (frames x bands) — the WAVE baseline,
              the thing to beat.
  B  NESTED-EVENT-TREE  each word parsed into its discrete nested order-N event tree
              (order 0 = syllable nuclei, 1 = gesture on/off-sets, 2 = fast
              transients; nested by containing span), materialised as graph nodes +
              nesting edges, serialised order-major into the event-vector sequence
              [order, sign, rel_time, log_mag_ratio, depth] — NO absolute band
              coordinate — and matched by the native DtwTo (the monotone alignment of
              two discrete event series = the structural tree match).
  SHUFFLE backstop on B: exemplar word-labels permuted -> must collapse to chance.

READ THE NUMBERS: k/N and % for every arm; per-clip resolution; B must beat A by a
MARGIN clearly above noise (> ~3 clips AND above pooled SE AND above shuffle).  An
honest NULL is a genuine result — report it plainly + WHY; do NOT sweep a gain.

Run: python -m scripts.nested_event_xspeaker [n_words] [n_train] [n_test]
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
from domains.nested_event_tree import event_sequence

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
    return tuple(tuple(float(v) for v in row) for row in M)


def main():
    n_words = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    n_train = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    n_test = int(sys.argv[3]) if len(sys.argv) > 3 else 400
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
    print("NESTED-EVENT-TREE vs SURFACE — cross-speaker Speech Commands", flush=True)
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
    print(f"per-clip resolution: {100.0/max(len(test),1):.3f}%", flush=True)

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

    sub = Substrate()

    # ---- parse the discrete nested event tree for every clip (graph structure +
    #      native serialise).  The tree NODES live in the substrate; the serialized
    #      event-vector sequence is the rep the native DtwTo matches. ----
    print("parsing NESTED ORDER-N EVENT TREES (graph nodes + nesting edges)...",
          flush=True)

    def to_events(pairs):
        out = []
        n_ev = []
        for M, w in pairs:
            seq = event_sequence(sub, M)
            if len(seq) >= 2:
                out.append((seq, w))
                n_ev.append(len(seq))
        return out, n_ev

    tr_ev, tr_nev = to_events(tr_band)
    te_ev, te_nev = to_events(te_band)
    if tr_nev:
        print(f"  events/word: train mean {np.mean(tr_nev):.1f} "
              f"(min {min(tr_nev)}, max {max(tr_nev)}); "
              f"test mean {np.mean(te_nev):.1f}", flush=True)
    print(f"  usable trees: {len(tr_ev)} train, {len(te_ev)} test "
          f"({time.time()-t0:.0f}s)", flush=True)

    sign = sub.add_node("HeardSign", {})
    err = _Pred(RG._DtwTo(RG._Attr(RG._V("s"), "rep"),
                          RG._Attr(RG._V("w"), "rep")))

    def run_arm(tag, tr_reprs, te_reprs, shuffle=False):
        ex_words = [w for _, w in tr_reprs]
        if shuffle:
            ex_words = list(ex_words)
            random.Random(7).shuffle(ex_words)
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
        for c, _ in exs:
            sub.remove_node(c)
        acc = corr / max(tot, 1)
        se = (acc * (1 - acc) / max(tot, 1)) ** 0.5
        print(f"\n[{tag}]  {corr}/{tot} = {100*acc:.2f}%  "
              f"(SE {100*se:.2f}%, chance {100*chance:.1f}%)", flush=True)
        return {"acc": acc, "corr": corr, "tot": tot, "se": se,
                "per_word": dict(per_word)}

    print("\n" + "=" * 72, flush=True)
    print("ARM A — SURFACE (raw gammatone band trajectory, native DtwTo NN) [WAVE]",
          flush=True)
    print("=" * 72, flush=True)
    A = run_arm("SURFACE", tr_band, te_band)

    print("\n" + "=" * 72, flush=True)
    print("ARM B — NESTED-EVENT-TREE (discrete event sequence, native DtwTo NN)",
          flush=True)
    print("=" * 72, flush=True)
    B = run_arm("NESTED-EVENT", tr_ev, te_ev)

    print("\n" + "=" * 72, flush=True)
    print("SHUFFLE backstop on B (exemplar labels permuted -> must collapse)",
          flush=True)
    print("=" * 72, flush=True)
    Bsh = run_arm("NESTED-EVENT-SHUFFLE", tr_ev, te_ev, shuffle=True)

    # ---- VERDICT — read the numbers, not a boolean ----
    print("\n" + "=" * 72, flush=True)
    print("VERDICT", flush=True)
    print("=" * 72, flush=True)
    print(f"  A SURFACE       {A['corr']}/{A['tot']} = {100*A['acc']:.2f}%  "
          f"(SE {100*A['se']:.2f}%)", flush=True)
    print(f"  B NESTED-EVENT  {B['corr']}/{B['tot']} = {100*B['acc']:.2f}%  "
          f"(SE {100*B['se']:.2f}%)", flush=True)
    print(f"  B SHUFFLE       {Bsh['corr']}/{Bsh['tot']} = {100*Bsh['acc']:.2f}%  "
          f"(chance {100*chance:.1f}%)", flush=True)
    # arms can drop different unusable clips; compare on RATES with pooled SE.
    margin_pct = 100 * (B["acc"] - A["acc"])
    margin_clips = B["corr"] - A["corr"]
    sh_margin_clips = B["corr"] - Bsh["corr"]
    pooled_se = 100 * ((A["se"] ** 2 + B["se"] ** 2) ** 0.5)
    print(f"\n  B - A   = {margin_pct:+.2f}%  ({margin_clips:+d} clips on "
          f"{A['tot']}/{B['tot']} usable)  pooled SE {pooled_se:.2f}%", flush=True)
    print(f"  B - shuf= {sh_margin_clips:+d} clips", flush=True)
    if margin_clips > 3 and margin_pct > pooled_se and sh_margin_clips > 3:
        print("\n  >>> LIFT: the discrete nested-event-tree match beats the surface "
              "wave by a margin above noise AND above shuffle. The discrete event "
              "STRUCTURE survives the speaker transform where the wave breaks.",
              flush=True)
    elif margin_clips > 3 and margin_pct > pooled_se:
        print("\n  >>> PARTIAL: nested-event beats surface above noise but the "
              "shuffle margin is thin — report with the caveat.", flush=True)
    else:
        print("\n  >>> NULL: the nested-event-tree does NOT beat surface by a "
              "resolvable margin. Honest result — likely the events are LOCATED off "
              "a blurry cochlea (so the discrete event set is itself jittery across "
              "speakers: an extremum appears/vanishes/shifts order), and/or the "
              "monotone event-sequence match is too permissive/strict. Report "
              "plainly; do NOT sweep a gain.", flush=True)


if __name__ == "__main__":
    main()
