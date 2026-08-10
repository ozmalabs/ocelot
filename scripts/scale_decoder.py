"""scale_decoder — DOES THE COHERENT DECODER (REL-BAND) SCALE?

The agent's CONFIRMED coherent decoder is REL-BAND: the whole-unit relational
representation (per-frame ORDINAL band-RANK profile ++ whole-unit SELF-SIMILARITY
row over the gammatone bands; domains/relational_shape.relational_shape), matched
by the native DtwTo nearest-exemplar Term (substrate.evaluate). It is multiply-
confirmed on 10 ISOLATED words (cross-speaker +7.75%, voiced->whisper, compounding,
shuffle-clean). The open question (the agent's pick): does it HOLD at scale, or
ceiling? This driver answers it on TWO axes, reusing the owned pieces — it does NOT
rebuild the decoder.

AXIS A — VOCABULARY (clean, no segmentation confound). REL-BAND vs SURFACE on Google
Speech Commands (/tmp/sc), cross-speaker held-out, at GROWING vocab 10 -> 20 -> 35
words. Reports a SCALING CURVE: acc per V for REL-BAND, SURFACE, chance (1/V), plus a
shuffle backstop on the largest V. THE QUESTION: does REL-BAND hold its margin over
surface and stay well above chance as V grows, or does the ordinal-rank discrimination
SATURATE? A ceiling is a genuine result — it says the next lever is sub-lexical
COMPOSITION, not more whole-word templates.

  This axis reuses scripts.relational_shape_xspeaker exactly (same venue, same native
  DtwTo decision, same SURFACE/REL/shuffle arms), called once per V.

AXIS B — CONTINUOUS (the agent's emphasis — links to the segmentation axis). On a
CONNECTED stream (run-on connected-digit strings, real SC clips from ONE held-out
speaker concatenated NO-gap, the construction from scripts.continuous_machine), the
stream is SEGMENTED with the agent's OWNED segmentation (the dissimilarity-PEAK
boundary Term, domains/dissimilarity_segmentation — a graph-resident order-1 sign-
change on the change-rate of the invariant features, the SOTA unsupervised cue) and
each segment is DECODED with REL-BAND (native DtwTo nearest-exemplar over a per-digit
exemplar bank from DISJOINT train speakers). Reports: segmentation quality (boundary
F1 vs the known concatenation boundaries) + connected-word recognition (WER via
Levenshtein of the decoded digit string to truth), cross-speaker. THE QUESTION: does
coherent-decode + the agent's segmentation give a real continuous result, or does
segmentation/coarticulation break it?

DISCIPLINE: reuses domains/relational_shape (decoder), domains/dissimilarity_
segmentation (owned segmenter), scripts/invariant_units_accept.band_trajectory_matrix
+ a duration-PRESERVING band front-end (Axis B needs real frame timing to segment),
scripts/continuous_machine world construction. Recognition native (substrate.evaluate
DtwTo). Donkey-clean: NO .fit/sklearn/gradient/loss/torch/sweep, no fitted model. N is
managed for tractability (native eval is slow) and STATED per cell. We READ THE NUMBERS
— no manufactured or swept gain.

Run: python -m scripts.scale_decoder
"""
from __future__ import annotations

import os
import sys
import math
import time
import random
import wave
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
import domains.recognition_graph as RG
from scripts.mine_whisper import gammatone_env, BANDS
from scripts.invariant_units_accept import band_trajectory_matrix
from domains.relational_shape import relational_shape
from domains.dissimilarity_segmentation import find_peak_boundaries
import scripts.continuous_machine as CM
import scripts.relational_shape_xspeaker as RX

SC = "/tmp/sc"
DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven",
          "eight", "nine"]


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def as_tuple(M):
    return tuple(tuple(float(v) for v in row) for row in np.asarray(M))


# ===========================================================================
# AXIS A — VOCABULARY SCALING CURVE.  Reuse relational_shape_xspeaker per V.
# ===========================================================================

def axis_a(vocab_sizes, n_train, n_test, n_anchors):
    print("#" * 72, flush=True)
    print("# AXIS A — VOCABULARY SCALING (REL-BAND vs SURFACE vs chance)", flush=True)
    print(f"#   cross-speaker held-out SC; n_train={n_train} n_test={n_test} "
          f"n_anchors={n_anchors}", flush=True)
    print("#" * 72, flush=True)
    curve = []
    for V in vocab_sizes:
        print(f"\n{'='*72}\nAXIS-A  V={V} words\n{'='*72}", flush=True)
        # Drive relational_shape_xspeaker.main via argv (it prints its own arms +
        # verdict).  We capture the three accuracies by re-running its core inline so
        # we also get the structured numbers for the curve.
        res = _run_vocab_cell(V, n_train, n_test, n_anchors)
        curve.append(res)
    # ---- the scaling curve, read across V ----
    print(f"\n{'#'*72}\n# AXIS-A SCALING CURVE\n{'#'*72}", flush=True)
    print(f"{'V':>4} {'chance':>8} {'SURFACE':>10} {'REL-BAND':>10} "
          f"{'REL-SURF':>10} {'REL/chance':>11}", flush=True)
    for r in curve:
        print(f"{r['V']:>4} {100*r['chance']:>7.1f}% {100*r['surf']:>9.1f}% "
              f"{100*r['rel']:>9.1f}% {100*(r['rel']-r['surf']):>+9.1f}% "
              f"{r['rel']/r['chance']:>10.1f}x", flush=True)
    print("\nREADING: if REL-BAND holds its margin over SURFACE and stays well above "
          "chance as V grows -> the coherent decoder SCALES. If REL-SURF shrinks "
          "to noise / REL/chance collapses toward 1x -> ordinal-rank discrimination "
          "SATURATES; next lever is sub-lexical composition, not whole-word templates.",
          flush=True)
    return curve


def _run_vocab_cell(V, n_train, n_test, n_anchors):
    """One vocab cell: SURFACE vs REL-BAND vs shuffle, cross-speaker, on V SC words.
    Built directly on the relational_shape_xspeaker machinery (same venue, same native
    DtwTo decision) so the numbers are identical to the confirmed harness."""
    random.seed(1)
    np.random.seed(1)
    avail = [w for w in sorted(os.listdir(SC))
             if os.path.isdir(os.path.join(SC, w)) and not w.startswith("_")
             and len([f for f in os.listdir(os.path.join(SC, w))
                      if f.endswith(".wav")]) > 200]
    words = avail[:V]
    chance = 1.0 / len(words)
    print(f"{len(words)}-way (chance {100*chance:.1f}%): {words}", flush=True)

    data = {}
    for w in words:
        for fn in sorted(os.listdir(os.path.join(SC, w))):
            if fn.endswith(".wav"):
                data.setdefault(w, []).append(
                    (os.path.join(SC, w, fn), fn.split("_")[0]))
    test_spk = set()
    for w in words:
        spks = sorted({s for _, s in data[w]})
        test_spk |= set(spks[::6])
    train = [(p, w) for w in words for p, s in data[w] if s not in test_spk]
    test = [(p, w) for w in words for p, s in data[w] if s in test_spk]
    random.shuffle(train)
    random.shuffle(test)
    train, test = train[:n_train], test[:n_test]

    def band_M(path):
        x, fs = RX.load_real(path)
        M = band_trajectory_matrix(x, fs)
        return M if M is not None and len(M) >= 2 else None

    tr_band = [(band_M(p), w) for p, w in train]
    te_band = [(band_M(p), w) for p, w in test]
    tr_band = [(M, w) for M, w in tr_band if M is not None]
    te_band = [(M, w) for M, w in te_band if M is not None]
    tr_rel = [(relational_shape(M, n_anchors=n_anchors), w) for M, w in tr_band]
    te_rel = [(relational_shape(M, n_anchors=n_anchors), w) for M, w in te_band]
    print(f"  usable {len(tr_band)} train / {len(te_band)} test exemplars",
          flush=True)

    sub = Substrate()
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
        for M, w in te_reprs:
            if M is None or len(M) < 2:
                continue
            sub.set_attr(sign, "rep", as_tuple(M))
            best_d, best_w = 1e18, None
            for c, ew in exs:
                d = sub.evaluate(err, {"s": sign, "w": c})
                if d < best_d:
                    best_d, best_w = d, ew
            corr += int(best_w == w)
            tot += 1
        for c, _ in exs:
            sub.remove_node(c)
        acc = corr / max(tot, 1)
        print(f"  [{tag:18}] {corr}/{tot} = {100*acc:.2f}%", flush=True)
        return acc

    surf = run_arm("SURFACE", tr_band, te_band)
    rel = run_arm("REL-BAND", tr_rel, te_rel)
    shuf = run_arm("REL-BAND-SHUFFLE", tr_rel, te_rel, shuffle=True)
    return {"V": V, "chance": chance, "surf": surf, "rel": rel, "shuf": shuf}


# ===========================================================================
# AXIS B — CONTINUOUS.  Owned segmenter (dissimilarity peaks) + REL-BAND decode.
# ===========================================================================

def duration_band_matrix(x, fs, fps=100.0, max_frames=400):
    """Gammatone band trajectory that PRESERVES real duration (frames proportional
    to clip length), so the segmenter has real timing to cut.  Same gammatone+envelope
    front-end as band_trajectory_matrix, but resampled to a fixed frame RATE rather
    than a fixed COUNT.  Mechanical I/O translation (no decision)."""
    envs = [gammatone_env(x, fs, fc) for fc in BANDS]
    cut = 1000.0 / (2 * math.pi * 80.0)
    tau = 1.0 / (2 * math.pi * cut)
    a = math.exp(-1.0 / (tau * fs))
    smoothed = []
    for env in envs:
        sm = np.empty_like(env)
        acc = 0.0
        for i in range(len(env)):
            acc = a * acc + (1 - a) * env[i]
            sm[i] = acc
        smoothed.append(sm)
    n_src = len(smoothed[0])
    dur_s = n_src / fs
    n_frames = min(max_frames, max(2, int(round(dur_s * fps))))
    rows = []
    for tf in range(n_frames):
        sp = tf * n_src / n_frames
        i0 = int(sp); i1 = min(i0 + 1, n_src - 1); frac = sp - i0
        rows.append([buf[i0] * (1 - frac) + buf[i1] * frac for buf in smoothed])
    return np.array(rows, dtype=np.float32), n_frames, dur_s


def build_digit_split(n_train_spk, n_held_spk, n_per_digit, seed=20240614):
    """Per-digit SC clips split into DISJOINT train speakers (the exemplar bank) and
    held-out speakers (build run-on strings).  Mechanical world construction."""
    rng = random.Random(seed)
    # collect speakers that have several digits
    spk_clips = defaultdict(lambda: defaultdict(list))  # spk -> digit -> [paths]
    for di, w in enumerate(DIGITS):
        d = os.path.join(SC, w)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".wav"):
                spk = fn.split("_")[0]
                spk_clips[spk][di].append(os.path.join(d, fn))
    # speakers with at least 4 distinct digits make usable run-on strings
    good = [s for s, dd in spk_clips.items() if len(dd) >= 4]
    rng.shuffle(good)
    train_spk = good[:n_train_spk]
    held_spk = good[n_train_spk:n_train_spk + n_held_spk]
    # train bank: per-digit paths from train speakers (capped)
    bank_paths = defaultdict(list)
    for s in train_spk:
        for di, paths in spk_clips[s].items():
            for p in paths[:n_per_digit]:
                bank_paths[di].append(p)
    # held: per speaker, the digit->clip pool for run-on construction
    held = []
    for s in held_spk:
        pool = {di: [p for p in paths] for di, paths in spk_clips[s].items()}
        held.append((s, pool))
    return bank_paths, held


def axis_b(n_train_spk, n_held_spk, n_per_digit, n_strings, min_len, max_len,
           n_anchors, fps):
    print(f"\n{'#'*72}\n# AXIS B — CONTINUOUS (owned dissimilarity segmenter + "
          f"REL-BAND decode)\n#   connected-digit run-on, cross-speaker; "
          f"fps={fps}\n{'#'*72}", flush=True)
    t0 = time.time()
    bank_paths, held = build_digit_split(n_train_spk, n_held_spk, n_per_digit)
    print(f"  bank: {sum(len(v) for v in bank_paths.values())} clips over "
          f"{len(bank_paths)} digits ({n_train_spk} train spk); "
          f"{len(held)} held-out speakers", flush=True)

    sub = Substrate()

    # ---- build the REL-BAND exemplar bank from DISJOINT train speakers ----
    print("  banking REL-BAND digit exemplars (native relational_shape)...",
          flush=True)
    exs = []  # (node, digit)
    for di, paths in bank_paths.items():
        for p in paths:
            x, fs = RX.load_real(p)
            M = band_trajectory_matrix(x, fs)        # isolated: fixed 32 frames
            if M is None or len(M) < 2:
                continue
            rel = relational_shape(M, n_anchors=n_anchors)
            c = sub.add_node("Exemplar", {"digit": di})
            sub.set_attr(c, "rep", as_tuple(rel))
            exs.append((c, di))
    print(f"  banked {len(exs)} exemplars ({time.time()-t0:.0f}s)", flush=True)

    sign = sub.add_node("HeardSign", {})
    err = _Pred(RG._DtwTo(RG._Attr(RG._V("s"), "rep"),
                          RG._Attr(RG._V("w"), "rep")))

    # DPDP minimum-duration floor: a spoken digit is at least ~150 ms, so two word
    # boundaries cannot be closer than ~0.15 s.  This is a STRUCTURAL constraint from
    # the task (the minimum word duration), derived once — NOT a swept knob.
    min_sep = max(2, int(round(0.15 * fps)))

    def decode_segment(Mseg):
        if Mseg is None or len(Mseg) < 2:
            return None
        rel = relational_shape(Mseg, n_anchors=n_anchors)
        sub.set_attr(sign, "rep", as_tuple(rel))
        best_d, best_di = 1e18, None
        for c, di in exs:
            d = sub.evaluate(err, {"s": sign, "w": c})
            if d < best_d:
                best_d, best_di = d, di
        return best_di

    # ---- build run-on strings from held-out speakers, segment + decode ----
    rng = random.Random(99)
    # boundary-F1 accumulators (tolerance window in frames)
    tol = max(2, int(round(0.05 * fps)))    # 50 ms tolerance
    tp_b = fp_b = fn_b = 0
    # WER accumulators
    tot_ref = tot_edits = 0
    n_done = 0
    per_unit_corr = per_unit_tot = 0
    seg_count_err = []
    print(f"  building+decoding {n_strings} run-on strings "
          f"(len {min_len}-{max_len}, tol {tol} fr)...", flush=True)
    for s, pool in held:
        for _ in range(max(1, n_strings // max(1, len(held)))):
            # construct the run-on, but ALSO keep each digit's trimmed clip so we
            # know the true concatenation boundaries (in samples -> frames).
            avail = [d for d in range(10) if pool.get(d)]
            if len(avail) < 2:
                continue
            L = rng.randint(min_len, max_len)
            truth = [rng.choice(avail) for _ in range(L)]
            segs = []
            for d in truth:
                x = rng.choice(pool[d])
                xx, _fs = RX.load_real(x)
                segs.append(CM._trim_silence(np.asarray(xx, dtype=np.float64),
                                             fs=8000))
            runon = np.concatenate(segs).astype(np.float32)
            # true boundaries in SAMPLES (cumulative seg lengths, interior only)
            cum = np.cumsum([len(s_) for s_ in segs])[:-1]

            M, n_fr, dur_s = duration_band_matrix(runon, 8000, fps=fps)
            if n_fr < 5:
                continue
            # map true sample boundaries to frame index
            true_b = sorted(set(int(round(c / len(runon) * n_fr)) for c in cum))
            true_b = [b for b in true_b if 0 < b < n_fr]

            tag = f"runon_{s}_{n_done}"
            cuts, _d = find_peak_boundaries(sub, M, tag, min_sep=min_sep,
                                            smooth=1, metric="cosine",
                                            gate="prominent")
            pred_b = sorted(c for c in cuts if 0 < c < n_fr)
            seg_count_err.append(abs(len(pred_b) - len(true_b)))

            # boundary F1 with tolerance matching
            matched_t = set()
            for pb in pred_b:
                hit = None
                for j, tb in enumerate(true_b):
                    if j in matched_t:
                        continue
                    if abs(pb - tb) <= tol:
                        hit = j
                        break
                if hit is not None:
                    matched_t.add(hit)
                    tp_b += 1
                else:
                    fp_b += 1
            fn_b += len(true_b) - len(matched_t)

            # decode each segment between boundaries -> digit string
            seg_bounds = [0] + pred_b + [n_fr]
            hyp = []
            for i in range(len(seg_bounds) - 1):
                a, b = seg_bounds[i], seg_bounds[i + 1]
                if b - a < 2:
                    continue
                di = decode_segment(M[a:b])
                if di is not None:
                    hyp.append(di)
            # WER via Levenshtein of hyp digit string vs truth
            ed = _levenshtein(hyp, truth)
            tot_edits += ed
            tot_ref += len(truth)
            # also a 1:1 per-unit accuracy on the matched-count case (diagnostic)
            for h, t in zip(hyp, truth):
                per_unit_corr += int(h == t)
                per_unit_tot += 1
            n_done += 1
            if n_done % 20 == 0:
                print(f"    {n_done} strings ({time.time()-t0:.0f}s)", flush=True)

    # ---- report ----
    prec = tp_b / max(tp_b + fp_b, 1)
    rec = tp_b / max(tp_b + fn_b, 1)
    f1 = 2 * prec * rec / max(prec + rec, 1e-9)
    wer = tot_edits / max(tot_ref, 1)
    mean_seg_err = float(np.mean(seg_count_err)) if seg_count_err else 0.0
    print(f"\n{'='*72}\nAXIS-B RESULTS ({n_done} run-on strings, "
          f"{time.time()-t0:.0f}s)\n{'='*72}", flush=True)
    print(f"  SEGMENTATION (dissimilarity-peak, tol {tol} fr):", flush=True)
    print(f"    boundary P={100*prec:.1f}%  R={100*rec:.1f}%  F1={100*f1:.1f}%  "
          f"(TP {tp_b} FP {fp_b} FN {fn_b})", flush=True)
    print(f"    mean |#pred - #true boundaries| = {mean_seg_err:.2f}", flush=True)
    print(f"  CONTINUOUS RECOGNITION (REL-BAND decode of each segment):", flush=True)
    print(f"    WER = {100*wer:.1f}%  (edits {tot_edits} / ref-digits {tot_ref}; "
          f"chance WER ~ {100*(1-0.1):.0f}%+ for random 10-way)", flush=True)
    if per_unit_tot:
        print(f"    aligned per-unit acc = "
              f"{100*per_unit_corr/per_unit_tot:.1f}% "
              f"({per_unit_corr}/{per_unit_tot}, chance 10%)", flush=True)
    print("\n  READING: high F1 + low WER -> coherent-decode + agent segmentation "
          "give a real continuous result. High F1 but high WER -> boundaries are "
          "fine, the decoder breaks on coarticulated segments. Low F1 -> the "
          "bottleneck is the BOUNDARY, not the decoder.", flush=True)
    return {"f1": f1, "prec": prec, "rec": rec, "wer": wer,
            "seg_err": mean_seg_err, "n": n_done}


def _levenshtein(a, b):
    n, m = len(a), len(b)
    if n == 0:
        return m
    if m == 0:
        return n
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        cur = [i] + [0] * m
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[m]


# ===========================================================================

def main():
    t0 = time.time()
    # --- N MANAGEMENT (stated): native DtwTo eval is O(n_test * n_train) per cell;
    # REL-BAND adds native relational_shape composition.  Kept tractable per cell. ---
    smoke = "--smoke" in sys.argv
    if smoke:
        vocab_sizes = [10, 20]
        n_train, n_test, n_anchors = 60, 40, 6
        b_args = dict(n_train_spk=8, n_held_spk=4, n_per_digit=3, n_strings=8,
                      min_len=3, max_len=5, n_anchors=6, fps=100.0)
    else:
        vocab_sizes = [10, 20, 35]
        n_train, n_test, n_anchors = 300, 250, 6     # A: 300 exemplars, 250 tests/cell
        b_args = dict(n_train_spk=40, n_held_spk=30, n_per_digit=6, n_strings=120,
                      min_len=3, max_len=6, n_anchors=6, fps=100.0)

    print("=" * 72, flush=True)
    print("SCALE-DECODER — does REL-BAND (the coherent decoder) scale?", flush=True)
    print(f"  AXIS A vocab {vocab_sizes}  n_train={n_train} n_test={n_test}", flush=True)
    print(f"  AXIS B continuous {b_args}", flush=True)
    print("=" * 72, flush=True)

    curve = axis_a(vocab_sizes, n_train, n_test, n_anchors)
    bres = axis_b(**b_args)

    print(f"\n{'#'*72}\n# OVERALL ({time.time()-t0:.0f}s)\n{'#'*72}", flush=True)
    print("AXIS A vocab-scaling curve:", flush=True)
    for r in curve:
        print(f"  V={r['V']:>3}: SURFACE {100*r['surf']:.1f}%  "
              f"REL-BAND {100*r['rel']:.1f}%  (chance {100*r['chance']:.1f}%, "
              f"shuffle {100*r['shuf']:.1f}%, REL-SURF {100*(r['rel']-r['surf']):+.1f}%)",
              flush=True)
    print(f"AXIS B continuous: boundary F1 {100*bres['f1']:.1f}%  "
          f"WER {100*bres['wer']:.1f}%  (n={bres['n']})", flush=True)


if __name__ == "__main__":
    main()
