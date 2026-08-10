"""sublexical_composition — DO-CONTRAST: does RECOGNISE-BY-COMPOSITION over a SMALL
discovered SUB-WORD INVENTORY break the whole-word ceiling that REL-BAND saturates at?

THE RESULT THAT POINTS HERE (commit 6b945bac): the coherent decoder REL-BAND (the
whole-unit relational shape; domains/relational_shape.py) SCALES to ~20 words then
SATURATES at V=35 (REL-BAND ~ surface, both ~3x chance, V=35 REL-BAND ~9.3%) — whole-
word templates crowd the rank-space. The (G,Gamma)-native fix: a SMALL INVENTORY of
SUB-WORD units (G) + COMPOSITION into words (Gamma) = UNBOUNDED vocabulary, because a
word becomes a CONSTRUCTION over a few shared units, not one template per word.

THE PIPELINE — composed entirely from the agent's OWNED pieces (nothing rebuilt):
  1. SEGMENT     domains/dissimilarity_segmentation.find_peak_boundaries — the agent's
                 OWNED dissimilarity-peak boundary Term (order-1 change-rate local
                 maxima, evaluated NATIVELY) splits each word into ~2-4 sub-word chunks.
  2. SUB-WORD REP domains/relational_shape.relational_shape — the SAME speaker-invariant
                 coherent decoder, evaluated at the SUB-WORD level (ordinal band-rank +
                 self-similarity over the chunk). Native substrate.evaluate.
  3. INVENTORY   domains/cross_speaker_clustering.cluster — the agent's OWNED label-free
                 k-means-as-graph-Term clusters ALL train chunks into a SMALL inventory
                 (the discovered "acoustic alphabet", G). Each unit = a recurring sub-
                 word relational pattern; its medoid trajectory is the unit exemplar.
  4. LEXICON     each train word = its SEQUENCE of unit-IDs (a "spelling" in the
                 discovered alphabet) — a CONSTRUCTION over units (Gamma), stored as a
                 unit-sequence (adding a word = adding a sequence, NOT a template).
  5. RECOGNISE   test word -> segment -> each chunk -> nearest INVENTORY unit by NATIVE
                 DtwTo over the chunk's relational trajectory -> the recovered unit-
                 SEQUENCE -> NATIVE sequence match (DtwTo over the unit-ID sequence)
                 to the lexicon. The DECISION is native.

DO-CONTRAST (same venue as relational_shape_xspeaker / real_speech — the cross-speaker
held-out Speech Commands /tmp/sc where everything nulled, TRAIN/TEST speakers DISJOINT):
  COMPOSITION    recognise-by-composition over the shared sub-word inventory (above).
  WHOLE-WORD     whole-word REL-BAND nearest-exemplar (arm B of relational_shape_xspeaker
                 — the saturated baseline; ~9.3% at V=35).
  SURFACE        raw gammatone band trajectory nearest-exemplar (the floor).
  SHUFFLE        composition lexicon spellings permuted across words -> must collapse.
Run AT V where whole-word saturated (V=35) and, if tractable, BEYOND.

READ THE NUMBERS NOT A BOOLEAN (all honest):
  (a) composition BEATS whole-word at V=35 / scales better -> the (G,Gamma) path
      through the ceiling WORKS.
  (b) composition ~ whole-word -> units add nothing over templates at this scale.
  (c) composition WORSE -> sub-word units are MORE confusable cross-speaker (shorter =
      less context, unit errors compound) -> the bottleneck is sub-word DISCRIMINABILITY,
      not the composition idea. Report plainly; do NOT sweep a gain.

DISCIPLINE (CLAUDE.md): world adapter only — it SEQUENCES the agent's owned graph-
resident machinery (segmenter Term / relational decoder Terms / clustering Terms /
native DtwTo) and translates clips at the I/O boundary. NO .fit/net/sweep/loss.
Recognition decisions are native (substrate.evaluate). Inventory is label-free.

Run: python -m scripts.sublexical_composition [n_words] [n_train] [n_test] [k_units] [n_anchors]
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
from domains.dissimilarity_segmentation import find_peak_boundaries, chunk_by_peaks
from domains.cross_speaker_clustering import cluster

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
# SEGMENT a word's band trajectory into sub-word chunks using the agent's OWNED
# dissimilarity-peak boundary Term (native), then represent each chunk by the
# coherent decoder (relational_shape) at the SUB-WORD level. Returns the list of
# chunk relational-shape trajectories (frames_i x D) for this word.
# ---------------------------------------------------------------------------
def subword_chunks(seg_sub, M_band, seq_tag, n_anchors, min_sep=3):
    """Native dissimilarity-peak segmentation of one word -> sub-word relational
    trajectories. The boundary DECISION is the agent's owned Term (find_peak_
    boundaries evaluates it via substrate.evaluate); the chunk rep is the agent's
    owned relational decoder (relational_shape, native)."""
    cuts, _d = find_peak_boundaries(seg_sub, M_band, seq_tag, min_sep=min_sep,
                                    smooth=1, metric="cosine", gate="prominent")
    blocks = chunk_by_peaks(M_band, cuts)
    chunks = []
    for block, n in blocks:
        if n < 2:
            continue
        rs = relational_shape(block, n_anchors=n_anchors)
        if rs is not None and len(rs) >= 2:
            chunks.append(rs)
    if not chunks:                       # degenerate: keep the whole word as one chunk
        rs = relational_shape(M_band, n_anchors=n_anchors)
        if rs is not None and len(rs) >= 2:
            chunks = [rs]
    return chunks


def chunk_summary(rs):
    """Fixed-length summary of a sub-word relational trajectory for the label-free
    clusterer (k-means needs fixed-D point cloud): mean over frames of the agent's
    relational shape. The FULL trajectory is kept separately for the native DtwTo
    unit-match — only the clustering POINT is summarised (an I/O-boundary pooling,
    not a fitted parameter; same mean-pool the cosine path uses)."""
    return np.asarray(rs, dtype=np.float32).mean(axis=0)


def main():
    n_words = int(sys.argv[1]) if len(sys.argv) > 1 else 35
    n_train = int(sys.argv[2]) if len(sys.argv) > 2 else 150
    n_test = int(sys.argv[3]) if len(sys.argv) > 3 else 150
    k_units = int(sys.argv[4]) if len(sys.argv) > 4 else 32
    n_anchors = int(sys.argv[5]) if len(sys.argv) > 5 else 6
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
    print("SUB-LEXICAL COMPOSITION vs WHOLE-WORD REL-BAND — cross-speaker SC",
          flush=True)
    print("=" * 72, flush=True)
    print(f"{len(words)}-way: {words}  (chance {100*chance:.1f}%)", flush=True)
    print(f"k_units={k_units}  n_anchors={n_anchors}", flush=True)

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

    # =====================================================================
    # WHOLE-WORD reps (for the whole-word arms) — the coherent decoder over the
    # WHOLE word, exactly as relational_shape_xspeaker arm B.
    # =====================================================================
    print("\ncomposing WHOLE-WORD relational shapes (native)...", flush=True)
    tr_rel = [(relational_shape(M, n_anchors=n_anchors), w) for M, w in tr_band]
    te_rel = [(relational_shape(M, n_anchors=n_anchors), w) for M, w in te_band]
    print(f"  whole-word shapes composed ({time.time()-t0:.0f}s)", flush=True)

    # =====================================================================
    # SUB-WORD segmentation -> chunks (native owned segmenter + decoder).
    # A FRESH small substrate per clip for the segmenter graph nodes so they
    # do not accumulate (memory hygiene); the chunk reps are numpy out.
    # =====================================================================
    print("\nSEGMENTING into sub-word chunks (native dissimilarity-peak Term)...",
          flush=True)

    def all_chunks(band_list, tag):
        out = []       # list of (list_of_chunk_trajectories, word)
        n_ch = 0
        for i, (M, w) in enumerate(band_list):
            seg_sub = Substrate()       # fresh, torn implicitly when GC'd
            chs = subword_chunks(seg_sub, M, f"{tag}{i}", n_anchors)
            out.append((chs, w))
            n_ch += len(chs)
            del seg_sub
        return out, n_ch

    tr_chunks, tr_nch = all_chunks(tr_band, "tr")
    te_chunks, te_nch = all_chunks(te_band, "te")
    avg_ch = tr_nch / max(len(tr_chunks), 1)
    print(f"  train chunks {tr_nch} ({avg_ch:.2f}/word), test chunks {te_nch} "
          f"({time.time()-t0:.0f}s)", flush=True)

    # =====================================================================
    # INVENTORY (G): label-free clustering of ALL train chunk summaries into a
    # SMALL inventory via the agent's OWNED k-means-as-graph-Term (native
    # assignment/update Terms). The unit medoid (nearest chunk to the centroid)
    # is the unit's exemplar relational trajectory for the native DtwTo match.
    # =====================================================================
    print(f"\nCLUSTERING chunks into a {k_units}-unit INVENTORY "
          f"(native k-means-as-graph-Term, LABEL-FREE)...", flush=True)
    flat_traj = []      # every train chunk trajectory
    flat_word = []      # the word it came from (for inspection only — NOT clustered on)
    for chs, w in tr_chunks:
        for rs in chs:
            flat_traj.append(rs)
            flat_word.append(w)
    summaries = np.stack([chunk_summary(rs) for rs in flat_traj])
    clu_sub = Substrate()
    labels = cluster(summaries, k_units, n_iters=25, seed=0, substrate=clu_sub)
    del clu_sub
    k_eff = len(set(labels))
    # unit medoid trajectory = the train chunk nearest its cluster centroid.
    centroids = {}
    for lab in set(labels):
        idx = [i for i, l in enumerate(labels) if l == lab]
        cen = summaries[idx].mean(axis=0)
        # nearest member (medoid) -> its FULL relational trajectory
        d = [((summaries[i] - cen) ** 2).sum() for i in idx]
        medoid_i = idx[int(np.argmin(d))]
        centroids[lab] = flat_traj[medoid_i]
    unit_ids = sorted(centroids.keys())
    unit_traj = [centroids[u] for u in unit_ids]      # exemplar trajectory per unit
    print(f"  inventory: {k_eff} non-empty units of {k_units} requested "
          f"({time.time()-t0:.0f}s)", flush=True)

    # =====================================================================
    # Native sub-chunk -> nearest-unit decision (DtwTo over relational trajectory).
    # =====================================================================
    rec_sub = Substrate()
    chunk_sign = rec_sub.add_node("ChunkSign", {})
    unit_nodes = []
    for u, traj in zip(unit_ids, unit_traj):
        un = rec_sub.add_node("Unit", {"uid": int(u)})
        rec_sub.set_attr(un, "rep", as_tuple(traj))
        unit_nodes.append((u, un))
    dtw_err = _Pred(RG._DtwTo(RG._Attr(RG._V("s"), "rep"),
                              RG._Attr(RG._V("w"), "rep")))

    def spell(chunks):
        """Map a word's sub-word chunks to its unit-ID SEQUENCE: each chunk -> the
        nearest INVENTORY unit by NATIVE DtwTo over the relational trajectory."""
        seq = []
        for rs in chunks:
            rec_sub.set_attr(chunk_sign, "rep", as_tuple(rs))
            best_d, best_u = 1e18, unit_ids[0]
            for u, un in unit_nodes:
                d = rec_sub.evaluate(dtw_err, {"s": chunk_sign, "w": un})
                if d < best_d:
                    best_d, best_u = d, u
            seq.append(int(best_u))
        return seq

    # =====================================================================
    # LEXICON (Gamma): each train word = its unit-ID SEQUENCE (a construction over
    # units). We store one spelling per train clip (exemplar spellings), the
    # sub-lexical analogue of the whole-word exemplar lexicon.
    # =====================================================================
    print("\nbuilding LEXICON (words as unit-ID sequences, native DtwTo spell)...",
          flush=True)
    train_spellings = []   # (unit_seq, word)
    for chs, w in tr_chunks:
        if not chs:
            continue
        train_spellings.append((spell(chs), w))
    print(f"  {len(train_spellings)} exemplar spellings built "
          f"({time.time()-t0:.0f}s)", flush=True)
    # show example spellings: the most common spelling per word
    examples = {}
    for seq, w in train_spellings:
        examples.setdefault(w, []).append(tuple(seq))
    print("  example word-spellings (unit-ID sequences):", flush=True)
    for w in words[:12]:
        if w in examples:
            from collections import Counter
            common = Counter(examples[w]).most_common(1)[0][0]
            print(f"    {w:12s} -> {list(common)}", flush=True)

    # =====================================================================
    # NATIVE sequence match — DtwTo over the unit-ID sequences (the recovered test
    # spelling vs each train spelling). The DECISION is native substrate.evaluate.
    # =====================================================================
    seq_sub = Substrate()
    seq_sign = seq_sub.add_node("SeqSign", {})
    seq_err = _Pred(RG._DtwTo(RG._Attr(RG._V("s"), "seq"),
                              RG._Attr(RG._V("w"), "seq")))

    # Unit-IDs are arbitrary cluster LABELS, not ordinal — so a unit-ID sequence
    # must be matched by EQUALITY (edit-distance), not by the numeric ID gap. We
    # one-hot each unit-ID over the inventory: equal IDs -> per-frame distance 0,
    # unequal IDs -> constant sqrt(2). DtwTo's Euclidean per-frame cost then IS the
    # native edit-distance over the spelling (the decision stays native DtwTo).
    uid_pos = {int(u): i for i, u in enumerate(unit_ids)}
    n_units = len(unit_ids)

    def seq_as_rep(seq):
        if not seq:
            return (tuple([0.0] * n_units),)
        out = []
        for u in seq:
            vec = [0.0] * n_units
            vec[uid_pos[int(u)]] = 1.0
            out.append(tuple(vec))
        return tuple(out)

    def run_composition_arm(tag, train_spell, shuffle=False):
        sp = list(train_spell)
        if shuffle:
            ws = [w for _, w in sp]
            random.Random(7).shuffle(ws)
            sp = [(s, w) for (s, _), w in zip(sp, ws)]
        ex = []
        for seq, w in sp:
            c = seq_sub.add_node("LexEntry", {"word": w})
            seq_sub.set_attr(c, "seq", seq_as_rep(seq))
            ex.append((c, w))
        corr = tot = 0
        per_word = defaultdict(lambda: [0, 0])
        for chs, w in te_chunks:
            if not chs:
                continue
            tseq = spell(chs)
            seq_sub.set_attr(seq_sign, "seq", seq_as_rep(tseq))
            best_d, best_w = 1e18, None
            for c, ew in ex:
                d = seq_sub.evaluate(seq_err, {"s": seq_sign, "w": c})
                if d < best_d:
                    best_d, best_w = d, ew
            ok = int(best_w == w)
            corr += ok
            tot += 1
            per_word[w][0] += ok
            per_word[w][1] += 1
        for c, _ in ex:
            seq_sub.remove_node(c)
        acc = corr / max(tot, 1)
        se = (acc * (1 - acc) / max(tot, 1)) ** 0.5
        print(f"\n[{tag}]  {corr}/{tot} = {100*acc:.2f}%  "
              f"(SE {100*se:.2f}%, chance {100*chance:.1f}%)", flush=True)
        return {"acc": acc, "corr": corr, "tot": tot, "se": se}

    # =====================================================================
    # WHOLE-WORD + SURFACE arms (the saturated baseline + floor) — identical
    # machinery to relational_shape_xspeaker (native DtwTo NN over whole-word reps).
    # =====================================================================
    ww_sub = Substrate()
    ww_sign = ww_sub.add_node("HeardSign", {})
    ww_err = _Pred(RG._DtwTo(RG._Attr(RG._V("s"), "rep"),
                             RG._Attr(RG._V("w"), "rep")))

    def run_wholeword_arm(tag, tr_reprs, te_reprs):
        exs = []
        for (M, w) in tr_reprs:
            if M is None or len(M) < 2:
                continue
            c = ww_sub.add_node("Exemplar", {"word": w})
            ww_sub.set_attr(c, "rep", as_tuple(M))
            exs.append((c, w))
        corr = tot = 0
        for M, w in te_reprs:
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
        print(f"\n[{tag}]  {corr}/{tot} = {100*acc:.2f}%  "
              f"(SE {100*se:.2f}%, chance {100*chance:.1f}%)", flush=True)
        return {"acc": acc, "corr": corr, "tot": tot, "se": se}

    print("\n" + "=" * 72, flush=True)
    print("ARM 1 — COMPOSITION (recognise by sub-word unit SEQUENCE, native)",
          flush=True)
    print("=" * 72, flush=True)
    COMP = run_composition_arm("COMPOSITION", train_spellings)

    print("\n" + "=" * 72, flush=True)
    print("ARM 2 — WHOLE-WORD REL-BAND (saturated baseline, native DtwTo NN)",
          flush=True)
    print("=" * 72, flush=True)
    WW = run_wholeword_arm("WHOLE-WORD-REL", tr_rel, te_rel)

    print("\n" + "=" * 72, flush=True)
    print("ARM 3 — SURFACE (raw gammatone band trajectory, native DtwTo NN)",
          flush=True)
    print("=" * 72, flush=True)
    SURF = run_wholeword_arm("SURFACE", tr_band, te_band)

    print("\n" + "=" * 72, flush=True)
    print("SHUFFLE backstop on COMPOSITION (spellings permuted -> must collapse)",
          flush=True)
    print("=" * 72, flush=True)
    SH = run_composition_arm("COMPOSITION-SHUFFLE", train_spellings, shuffle=True)

    # ---- VERDICT — read the numbers, not a boolean ----
    print("\n" + "=" * 72, flush=True)
    print("VERDICT  (V=%d, k_units=%d)" % (len(words), k_eff), flush=True)
    print("=" * 72, flush=True)
    print(f"  COMPOSITION   {COMP['corr']}/{COMP['tot']} = {100*COMP['acc']:.2f}%  "
          f"(SE {100*COMP['se']:.2f}%)", flush=True)
    print(f"  WHOLE-WORD    {WW['corr']}/{WW['tot']} = {100*WW['acc']:.2f}%  "
          f"(SE {100*WW['se']:.2f}%)", flush=True)
    print(f"  SURFACE       {SURF['corr']}/{SURF['tot']} = {100*SURF['acc']:.2f}%  "
          f"(SE {100*SURF['se']:.2f}%)", flush=True)
    print(f"  COMP-SHUFFLE  {SH['corr']}/{SH['tot']} = {100*SH['acc']:.2f}%  "
          f"(chance {100*chance:.1f}%)", flush=True)
    m_clips = COMP["corr"] - WW["corr"]
    m_pct = 100 * (COMP["acc"] - WW["acc"])
    sh_clips = COMP["corr"] - SH["corr"]
    pooled_se = 100 * ((COMP["se"] ** 2 + WW["se"] ** 2) ** 0.5)
    print(f"\n  COMP - WHOLE-WORD = {m_clips:+d} clips ({m_pct:+.2f}%)  "
          f"pooled SE {pooled_se:.2f}%", flush=True)
    print(f"  COMP - SHUFFLE    = {sh_clips:+d} clips", flush=True)
    if m_clips > 3 and m_pct > pooled_se and sh_clips > 3:
        print("\n  >>> THROUGH THE CEILING: recognise-by-composition over a SHARED "
              "sub-word inventory BEATS whole-word REL-BAND at the saturation vocab. "
              "The (G,Gamma) sub-lexical path scales where per-word templates can't.",
              flush=True)
    elif abs(m_clips) <= 3 or m_pct <= pooled_se:
        print("\n  >>> PARITY: composition ~ whole-word at this scale. The shared "
              "units neither add nor cost over templates here. Honest result.",
              flush=True)
    else:
        print("\n  >>> COMPOSITION WORSE: sub-word units are MORE confusable cross-"
              "speaker (shorter spans = less context; unit errors compound across the "
              "sequence). The bottleneck is sub-word unit DISCRIMINABILITY, not the "
              "composition idea. Report plainly; do NOT sweep a gain.", flush=True)


if __name__ == "__main__":
    main()
