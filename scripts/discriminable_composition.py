"""discriminable_composition — sub-lexical composition with the NEW DISCRIMINABLE
sub-word inventory (domains/discriminable_units), the upgrade of
scripts/sublexical_composition. THE BAR: composition must now BEAT ITS SHUFFLE clearly
(it tied/lost before — the falsifier), THEN approach / cross whole-word REL-BAND.

Identical do-contrast venue + machinery to sublexical_composition (cross-speaker SC,
disjoint train/test speakers, native DtwTo decisions), with ONE thing changed: the
ALPHABET. The inventory is now the agent's cross-speaker discriminable inventory:
  LEVER 1  syllable-scale chunks (owned segmenter, larger min_sep)
  LEVER 2  cluster on the phase-anchored summary (cluster space = native-DtwTo decision
           space), not the mean-pool
  LEVER 3  categorical inventory selection by cross-speaker consistency (keep only
           units reliably hit from BOTH disjoint train-speaker halves)
selected by the agent's coherence (clean-quantization-margin) selector — NO accuracy.

ARMS per V:
  COMPOSITION   recognise-by-composition over the discriminable inventory (native).
  COMP-SHUFFLE  spellings permuted across words -> MUST collapse (the falsifier).
  WHOLE-WORD    whole-word REL-BAND nearest-exemplar (the saturated baseline; 40%/25%).

READ THE NUMBERS NOT A BOOLEAN:
  (a) composition clearly BEATS shuffle AND scales toward/past whole-word -> the
      alphabet fix WORKS; composition is the vocab-scaler.
  (b) units more discriminable but composition still ~ shuffle -> the BOUNDARY/
      alignment is the residual.
  (c) covered by the discriminability probe (whole-word is the right granularity).

DISCIPLINE: native decisions (substrate.evaluate); label-free inventory; world adapter.

Run: python -m scripts.discriminable_composition [V] [n_train] [n_test] [k_units]
"""
import os
import sys
import random
import time
import wave
from collections import defaultdict, Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
import domains.recognition_graph as RG
from scripts.invariant_units_accept import band_trajectory_matrix
from domains.relational_shape import relational_shape
from domains.discriminable_units import (
    word_chunks, Quantizer, build_discriminable_inventory)

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
    A = np.asarray(M, dtype=np.float32)
    if A.ndim == 1:
        A = A[:, None]
    return tuple(tuple(float(v) for v in row) for row in A)


def run_one_V(words, data, test_spk, n_train, n_test, k_units, n_anchors,
              n_phase, big_min_sep, t0):
    chance = 1.0 / len(words)
    train = [(p, w, s) for w in words for p, s in data[w] if s not in test_spk]
    test = [(p, w, s) for w in words for p, s in data[w] if s in test_spk]
    random.Random(2).shuffle(train)
    random.Random(3).shuffle(test)
    train, test = train[:n_train], test[:n_test]
    print(f"\n{'#'*72}\nV={len(words)}  (chance {100*chance:.1f}%)  "
          f"train {len(train)} test {len(test)} held-out  k={k_units}", flush=True)

    def band_M(path):
        x, fs = load_real(path)
        M = band_trajectory_matrix(x, fs)
        return M if M is not None and len(M) >= 2 else None

    tr_band = [(band_M(p), w, s) for p, w, s in train]
    te_band = [(band_M(p), w, s) for p, w, s in test]
    tr_band = [(M, w, s) for M, w, s in tr_band if M is not None]
    te_band = [(M, w, s) for M, w, s in te_band if M is not None]
    print(f"  bands: {len(tr_band)} train, {len(te_band)} test "
          f"({time.time()-t0:.0f}s)", flush=True)

    # whole-word relational reps (the saturated baseline).
    tr_rel = [(relational_shape(M, n_anchors=n_anchors), w) for M, w, s in tr_band]
    te_rel = [(relational_shape(M, n_anchors=n_anchors), w) for M, w, s in te_band]

    # chunk both train + test into syllable-scale chunks (owned segmenter).
    def chunk_all(band_list):
        out = []
        for i, (M, w, s) in enumerate(band_list):
            seg = Substrate()
            chs = word_chunks(seg, M, f"c{i}", n_anchors, big_min_sep, n_phase)
            out.append((chs, w, s))
            del seg
        return out

    tr_ch = chunk_all(tr_band)
    te_ch = chunk_all(te_band)
    avg = np.mean([len(c) for c, _, _ in tr_ch])
    print(f"  syllable-scale chunks/word {avg:.2f} ({time.time()-t0:.0f}s)",
          flush=True)

    # NEW discriminable inventory: phase-anchored k-means + consistency select.
    tr_spk = sorted({s for _, _, s in tr_band})
    half_a = set(tr_spk[0::2])
    new_a = [[(rs, su) for (rs, su) in chs] for chs, _, s in tr_ch if s in half_a]
    new_b = [[(rs, su) for (rs, su) in chs] for chs, _, s in tr_ch if s not in half_a]
    unit_ids, unit_traj, coh = build_discriminable_inventory(
        (new_a, new_b), k_units, seed=0, consistency=True,
        log=lambda *a: print("   ", *a, flush=True))
    print(f"  inventory: {len(unit_ids)} discriminable units "
          f"(coherence {coh:.4f}, {time.time()-t0:.0f}s)", flush=True)

    # native chunk -> unit quantizer (DtwTo).
    q = Quantizer(unit_ids, unit_traj)

    def spell(chunks):
        return [int(q.quantize(rs)[0]) for (rs, _su) in chunks]

    # spell every train + test word (the construction over units).
    train_spell = [(spell(chs), w) for chs, w, s in tr_ch if chs]
    test_spell = [(spell(chs), w) for chs, w, s in te_ch if chs]
    print(f"  spelled {len(train_spell)} train, {len(test_spell)} test "
          f"({time.time()-t0:.0f}s)", flush=True)
    examples = defaultdict(list)
    for seq, w in train_spell:
        examples[w].append(tuple(seq))
    print("  example spellings:", flush=True)
    for w in words[:8]:
        if examples[w]:
            print(f"    {w:12s} -> {list(Counter(examples[w]).most_common(1)[0][0])}",
                  flush=True)

    # native sequence match — one-hot the unit-IDs so DtwTo's Euclidean per-frame cost
    # IS edit-distance over the spelling (the decision stays native DtwTo).
    uid_pos = {int(u): i for i, u in enumerate(unit_ids)}
    n_u = len(unit_ids)

    def seq_rep(seq):
        if not seq:
            return (tuple([0.0] * n_u),)
        out = []
        for u in seq:
            vec = [0.0] * n_u
            vec[uid_pos[int(u)]] = 1.0
            out.append(tuple(vec))
        return tuple(out)

    seq_sub = Substrate()
    seq_sign = seq_sub.add_node("SeqSign", {})
    seq_err = _Pred(RG._DtwTo(RG._Attr(RG._V("s"), "seq"),
                              RG._Attr(RG._V("w"), "seq")))

    def comp_arm(tag, shuffle=False):
        sp = list(train_spell)
        if shuffle:
            ws = [w for _, w in sp]
            random.Random(7).shuffle(ws)
            sp = [(s, w) for (s, _), w in zip(sp, ws)]
        ex = []
        for seq, w in sp:
            c = seq_sub.add_node("LexEntry", {"word": w})
            seq_sub.set_attr(c, "seq", seq_rep(seq))
            ex.append((c, w))
        corr = tot = 0
        for tseq, w in test_spell:
            seq_sub.set_attr(seq_sign, "seq", seq_rep(tseq))
            best_d, best_w = 1e18, None
            for c, ew in ex:
                d = seq_sub.evaluate(seq_err, {"s": seq_sign, "w": c})
                if d < best_d:
                    best_d, best_w = d, ew
            corr += int(best_w == w)
            tot += 1
        for c, _ in ex:
            seq_sub.remove_node(c)
        acc = corr / max(tot, 1)
        se = (acc * (1 - acc) / max(tot, 1)) ** 0.5
        print(f"  [{tag}] {corr}/{tot} = {100*acc:.2f}% (SE {100*se:.2f}%)",
              flush=True)
        return {"acc": acc, "corr": corr, "tot": tot, "se": se}

    # whole-word arm.
    ww_sub = Substrate()
    ww_sign = ww_sub.add_node("HeardSign", {})
    ww_err = _Pred(RG._DtwTo(RG._Attr(RG._V("s"), "rep"),
                             RG._Attr(RG._V("w"), "rep")))

    def ww_arm():
        exs = []
        for (M, w) in tr_rel:
            if M is None or len(M) < 2:
                continue
            c = ww_sub.add_node("Exemplar", {"word": w})
            ww_sub.set_attr(c, "rep", as_tuple(M))
            exs.append((c, w))
        corr = tot = 0
        for M, w in te_rel:
            if M is None or len(M) < 2:
                continue
            ww_sub.set_attr(ww_sign, "rep", as_tuple(M))
            best_d, best_w = 1e18, None
            for c, ew in exs:
                d = ww_sub.evaluate(ww_err, {"s": ww_sign, "w": c})
                if d < best_d:
                    best_d, best_w = d, ew
            corr += int(best_w == w)
            tot += 1
        for c, _ in exs:
            ww_sub.remove_node(c)
        acc = corr / max(tot, 1)
        se = (acc * (1 - acc) / max(tot, 1)) ** 0.5
        print(f"  [WHOLE-WORD] {corr}/{tot} = {100*acc:.2f}% (SE {100*se:.2f}%)",
              flush=True)
        return {"acc": acc, "corr": corr, "tot": tot, "se": se}

    print("  --- arms ---", flush=True)
    COMP = comp_arm("COMPOSITION")
    SH = comp_arm("COMP-SHUFFLE", shuffle=True)
    WW = ww_arm()

    sh_lift = COMP["corr"] - SH["corr"]
    ww_gap = 100 * (COMP["acc"] - WW["acc"])
    print(f"  V={len(words)}: COMP {100*COMP['acc']:.1f}%  SHUF {100*SH['acc']:.1f}%  "
          f"WW {100*WW['acc']:.1f}%  | COMP-SHUF {sh_lift:+d}clips  "
          f"COMP-WW {ww_gap:+.1f}%  coherence {coh:.3f}", flush=True)
    if sh_lift > 3 and 100*(COMP['acc']-SH['acc']) > \
            100*((COMP['se']**2+SH['se']**2)**0.5):
        print("  >>> COMPOSITION BEATS SHUFFLE (alphabet carries identity).",
              flush=True)
    else:
        print("  >>> composition ~ shuffle (alignment/boundary residual or units "
              "still too confusable).", flush=True)
    return {"V": len(words), "COMP": COMP, "SH": SH, "WW": WW, "coh": coh}


def main():
    Vs = [int(x) for x in (sys.argv[1].split(",") if len(sys.argv) > 1
                           else ["10", "20"])]
    n_train = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    n_test = int(sys.argv[3]) if len(sys.argv) > 3 else 200
    k_units = int(sys.argv[4]) if len(sys.argv) > 4 else 32
    n_anchors = 6
    n_phase = 6
    big_min_sep = 8
    random.seed(1)
    np.random.seed(1)
    t0 = time.time()

    avail = [w for w in sorted(os.listdir(SC))
             if os.path.isdir(os.path.join(SC, w)) and not w.startswith("_")
             and len([f for f in os.listdir(os.path.join(SC, w))
                      if f.endswith(".wav")]) > 200]
    data = {}
    for w in avail:
        for fn in sorted(os.listdir(os.path.join(SC, w))):
            if fn.endswith(".wav"):
                data.setdefault(w, []).append(
                    (os.path.join(SC, w, fn), fn.split("_")[0]))

    print("=" * 72, flush=True)
    print("DISCRIMINABLE SUB-LEXICAL COMPOSITION — cross-speaker SC", flush=True)
    print("=" * 72, flush=True)
    print(f"Vs={Vs}  n_train={n_train} n_test={n_test} k_units={k_units}  "
          f"n_phase={n_phase} min_sep={big_min_sep}", flush=True)

    results = []
    for V in Vs:
        words = avail[:V]
        test_spk = set()
        for w in words:
            spks = sorted({s for _, s in data[w]})
            test_spk |= set(spks[::6])
        results.append(run_one_V(words, data, test_spk, n_train, n_test, k_units,
                                 n_anchors, n_phase, big_min_sep, t0))

    print("\n" + "=" * 72, flush=True)
    print("SUMMARY (composition vs shuffle vs whole-word, per V)", flush=True)
    print("=" * 72, flush=True)
    for r in results:
        print(f"  V={r['V']:3d}  COMP {100*r['COMP']['acc']:5.1f}%  "
              f"SHUF {100*r['SH']['acc']:5.1f}%  WW {100*r['WW']['acc']:5.1f}%  "
              f"COMP-SHUF {r['COMP']['corr']-r['SH']['corr']:+4d}clips  "
              f"coherence {r['coh']:.3f}", flush=True)


if __name__ == "__main__":
    main()
