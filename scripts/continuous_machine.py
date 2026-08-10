"""continuous_machine — THE FULL CONTINUOUS-SPEECH MACHINE, one integrated pipeline.

THREE STAGES wired end-to-end, tested on RUN-ON (continuous, no-gap) connected-digit
strings, cross-speaker (held-out speakers never banked), with component ablations.

CONSTRAINED CONTINUOUS TASK (stated): CONNECTED-DIGIT STRINGS. A run-on utterance is
built by concatenating real Speech-Commands digit clips (0-9) from ONE held-out
speaker, end-to-end with NO silence gap (genuine continuous run-on; the within-clip
lead/trail silence is trimmed so digits abut). Vocab = the 10 digits (tractable, so
WER is meaningful). The truth is the known digit string. A real LibriSpeech digit
n-gram (counted from the transcripts' spelled-out digit words) is the language model.

  STAGE 1 — RADIO-TELESCOPE FRONT END (domains/radio_telescope_frontend): matched
    filter + incoherent integration + Hogbom CLEAN -> a CLEANED cochleagram read +
    a SHARPENED onset envelope. Owned DSP, no net/fit.
  STAGE 2 — RELAXATION OSCILLATOR (domains/relaxation_oscillator): leaky integrate-
    and-fire with Mirollo-Strogatz pulse-coupled phase reset on the sharp onset ->
    FIRE events = unit boundaries that segment the run-on stream. Owned DSP, no fit.
  STAGE 3 — RUN-ON DECODE (the collapse, the agent's): each segmented unit is read
    acoustically over the Stage-1 CLEANED read (DTW 1-NN to a per-digit banked
    cleaned-cochleagram exemplar bank -> soft excluder) and the sequence is decoded
    by the multi-frame weighted-admissibility collapse (acoustic frame + real
    LibriSpeech digit n-gram context + future-sheaf), Viterbi over the units.

TEST (continuous, cross-speaker):
  (a) END-TO-END: WER / word-accuracy of the integrated machine on the run-on
      strings + n. WER via Levenshtein alignment of the decoded digit string to truth
      (so segmentation errors — insertions/deletions — are counted, the honest
      continuous metric).
  (b) ABLATIONS:
      · SEGMENTATION: relaxation oscillator vs sine entrain_theta — cross-speaker
        syllable/unit-count error (pred/true ratio; the sine's bar ~0.64 from the
        prior Stage-A run on continuous LibriSpeech, here on the run-on digit strings).
      · FRONT END: radio-telescope CLEANED read vs RAW cochleagram — onset sharpness
        (a peakiness measure) + end-to-end decode WER under each.
      · COLLAPSE: segmented-collapse vs a NO-SEGMENTATION baseline (decode the whole
        run-on as one unit / a uniform grid) — does the oscillator segmentation help.

DONKEY: Stage 1 + Stage 2 = owned radio-astronomy + integrate-and-fire DSP (no
net/fit). Stage 3 collapse = the agent's weighted_admissibility (frame_inference_v2).
n-gram = real LibriSpeech digit LM (the world). Held-out speakers never banked.

Run: python -m scripts.continuous_machine [n_train_spk] [n_held_spk] [n_strings] \
        [min_len] [max_len]
"""
from __future__ import annotations

import os
import re
import sys
import time
import random
import collections

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import domains.self_directed_speech_world as W
import domains.frame_inference_v2 as F2
import domains.radio_telescope_frontend as RT
import domains.relaxation_oscillator as RO
import domains.prosody_syllable as P          # entrain_theta (the sine baseline)

FS = W._TARGET_FS
DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven",
          "eight", "nine"]
# spelled-out digit words -> index, for counting the LibriSpeech digit n-gram.
_WORD2IDX = {w: i for i, w in enumerate(DIGITS)}
_LIBRI = "/tmp/LibriSpeech"


# ===========================================================================
# WORLD — build run-on connected-digit strings from real SC digit clips, and a
# real LibriSpeech spelled-digit n-gram. Owned world construction (no decisions).
# ===========================================================================

def _trim_silence(x, fs=FS, frac=0.06):
    """Trim leading/trailing near-silence so concatenated digits ABUT (a genuine
    run-on, no inter-digit gap). Owned envelope DSP: keep the span where the smoothed
    energy exceeds `frac` of its peak. Mechanical."""
    x = np.asarray(x, dtype=np.float64)
    if x.size == 0:
        return x
    hop = max(1, int(fs * 0.01))
    nfr = max(1, x.size // hop)
    env = np.array([np.sqrt(np.mean(x[i*hop:(i+1)*hop]**2) + 1e-12)
                    for i in range(nfr)])
    if env.max() <= 1e-9:
        return x
    above = np.where(env >= frac * env.max())[0]
    if above.size == 0:
        return x
    s = above[0] * hop
    e = min(x.size, (above[-1] + 1) * hop)
    return x[s:e]


def make_runon(digit_clips, rng, min_len, max_len):
    """Build ONE run-on connected-digit string from a speaker's clip pool.
    digit_clips: {digit_idx -> [waveform,...]} (this held speaker's clips). Returns
    (waveform, truth_indices) — the trimmed digit clips concatenated with NO gap.
    Owned world construction (mechanical)."""
    avail = [d for d in range(10) if digit_clips.get(d)]
    if len(avail) < 2:
        return None, None
    L = rng.randint(min_len, max_len)
    truth = [rng.choice(avail) for _ in range(L)]
    segs = []
    for d in truth:
        x = rng.choice(digit_clips[d])
        segs.append(_trim_silence(np.asarray(x, dtype=np.float64)))
    runon = np.concatenate(segs).astype(np.float64)
    return runon, truth


def count_digit_ngram(libri_dir=_LIBRI):
    """Count the REAL spelled-out digit n-gram from LibriSpeech transcripts: the
    bigram (fwd/bwd) and skip-2 over the digit words (zero..nine), plus the unigram.
    Returns (fwd, bwd, fwd2, bwd2, uni, n_utts). Only digit-word transitions are
    counted (the constrained vocab's real co-occurrence in real English). Owned
    counts (the world's statistics), no fit."""
    fwd = collections.defaultdict(collections.Counter)
    bwd = collections.defaultdict(collections.Counter)
    fwd2 = collections.defaultdict(collections.Counter)
    bwd2 = collections.defaultdict(collections.Counter)
    uni = collections.Counter()
    n_utts = 0
    if not os.path.isdir(libri_dir):
        return fwd, bwd, fwd2, bwd2, uni, 0
    for sub in os.listdir(libri_dir):
        d = os.path.join(libri_dir, sub)
        if not os.path.isdir(d):
            continue
        for root, _dirs, names in os.walk(d):
            for fn in names:
                if not fn.endswith(".trans.txt"):
                    continue
                with open(os.path.join(root, fn)) as f:
                    for line in f:
                        line = line.strip()
                        if not line or " " not in line:
                            continue
                        _utt, txt = line.split(" ", 1)
                        ws = [w for w in re.findall(r"[a-z]+", txt.lower())]
                        # keep only the digit words, in order (the digit subsequence)
                        ds = [w for w in ws if w in _WORD2IDX]
                        if not ds:
                            continue
                        n_utts += 1
                        for w in ds:
                            uni[w] += 1
                        seq = ds
                        for a, b in zip(seq, seq[1:]):
                            fwd[a][b] += 1
                            bwd[b][a] += 1
                        for a, c in zip(seq, seq[2:]):
                            fwd2[a][c] += 1
                            bwd2[c][a] += 1
    return fwd, bwd, fwd2, bwd2, uni, n_utts


def _cond_excluder(counter, add_k=0.3):
    """P(digit | given neighbour) over the 10 digits, add-k smoothed -> soft excluder.
    If the neighbour was never seen with any digit -> uniform (LM abstains). The digit
    n-gram is SPARSE in LibriSpeech (digits are rare), so we BACK OFF to a uniform-ish
    prior via the larger add-k: where the corpus has no digit-bigram evidence the LM
    abstains rather than asserting. Owned (frame_inference_v2 soft-exclude)."""
    counts = np.array([counter.get(w, 0) for w in DIGITS], dtype=np.float64)
    tot = counts.sum()
    if tot <= 0:
        return np.zeros(10, dtype=np.float64)            # abstain (no evidence)
    p = (counts + add_k) / (tot + add_k * 10)
    return F2.soft_exclude_from_score(p)


# ===========================================================================
# SPLIT — train speakers (build the per-digit CLEANED-cochleagram exemplar bank)
# and HELD-OUT speakers (realise the run-on strings; never banked).
# ===========================================================================

def build_split(n_train_spk, n_held_spk, n_per, seed=20240611):
    rng = random.Random(seed)
    speakers = W.sc_speakers(DIGITS)
    rng.shuffle(speakers)
    held_spk = speakers[:n_held_spk]
    train_spk = speakers[n_held_spk:n_held_spk + n_train_spk]
    print(f"[split] {len(train_spk)} TRAIN, {len(held_spk)} HELD-OUT speakers "
          f"(disjoint; held clips NEVER banked)", flush=True)

    def carve(spk_list, n_body):
        out = {}
        for spk in spk_list:
            spk_idx = W.sc_index_for([spk], DIGITS)
            dp = {}
            for d, w in enumerate(DIGITS):
                for p in spk_idx.get(w, []):
                    dp.setdefault(d, []).append(p)
            if len(dp) < 2:
                continue
            # cap per digit per speaker (bounded)
            clips = {}
            for d, paths in dp.items():
                rng.shuffle(paths)
                clips[d] = [W.load_sc_clip(p)[0] for p in paths[:n_body]]
            out[spk] = clips
        return out

    train = carve(train_spk, n_per)
    held = carve(held_spk, n_per)
    print(f"[split] {len(train)} train / {len(held)} held usable speakers", flush=True)
    return train, held


def _clean_track(x):
    """Per-frame L2-normalised CLEANED-cochleagram trajectory of a clip (the Stage-1
    cleaned read, kept as an ordered sequence for DTW). The acoustic frame's
    representation over the radio-telescope cleaned read. Owned DSP."""
    Mc = RT.clean_read(np.asarray(x, dtype=np.float64))
    if Mc.size == 0:
        return np.zeros((0, 1))
    out = []
    for r in range(Mc.shape[0]):
        v = Mc[r]
        nrm = np.linalg.norm(v)
        out.append(v / nrm if nrm > 1e-9 else v)
    return np.asarray(out, dtype=np.float64)


def _raw_track(x):
    """Per-frame L2-normalised RAW-cochleagram trajectory (the Stage-1 ABLATION
    baseline: no integration, no CLEAN). Owned DSP."""
    Mr = RT.raw_read(np.asarray(x, dtype=np.float64))
    if Mr.size == 0:
        return np.zeros((0, 1))
    out = []
    for r in range(Mr.shape[0]):
        v = Mr[r]
        nrm = np.linalg.norm(v)
        out.append(v / nrm if nrm > 1e-9 else v)
    return np.asarray(out, dtype=np.float64)


def _dtw(a, b):
    """DTW distance between two (frames x dim) trajectories, /(na+nb)-normalised
    (the same recogniser mechanic the agent uses). Vectorised inner cost. Owned."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if a.size == 0 or b.size == 0:
        return float("inf")
    na, nb = a.shape[0], b.shape[0]
    C = np.sqrt(((a[:, None, :] - b[None, :, :]) ** 2).sum(-1))
    prev = np.full(nb + 1, np.inf)
    prev[0] = 0.0
    for i in range(1, na + 1):
        cur = np.empty(nb + 1)
        cur[0] = np.inf
        ci = C[i - 1]
        for j in range(1, nb + 1):
            cur[j] = ci[j - 1] + min(prev[j], cur[j - 1], prev[j - 1])
        prev = cur
    return float(prev[nb] / (na + nb))


def build_bank(train, track_fn, cap_per_digit=24, seed=11):
    """Per train speaker, store each digit's CLEANED (or RAW) cochleagram exemplar
    trajectory. Returns {digit -> [track,...]}. Capped per digit (bounded scan).
    The bank is built with the SAME track_fn the test reads -> apples to apples."""
    bank = {d: [] for d in range(10)}
    for spk, clips in train.items():
        for d, xs in clips.items():
            for x in xs:
                tr = track_fn(_trim_silence(np.asarray(x, dtype=np.float64)))
                if tr.shape[0]:
                    bank[d].append(tr)
    rng = random.Random(seed)
    for d in range(10):
        if len(bank[d]) > cap_per_digit:
            rng.shuffle(bank[d])
            bank[d] = bank[d][:cap_per_digit]
    return bank


# ===========================================================================
# STAGE 3 — decode a run-on string. Segment (Stage 2) -> per-unit acoustic excluder
# over the Stage-1 cleaned read -> weighted-admissibility collapse (acoustic + real
# digit n-gram context + future sheaf), Viterbi. The collapse is the agent's.
# ===========================================================================

def unit_acoustic_excluder(unit_track, bank):
    """Soft excluder over the 10 digits from one unit's cleaned-cochleagram track:
    1-NN DTW distance to each digit's banked exemplars -> soft-exclude. Owned DSP +
    the agent's distance->soft-exclude."""
    dist = np.full(10, np.inf, dtype=np.float64)
    if unit_track.shape[0] == 0:
        return F2.soft_exclude_from_distance(dist)
    for d in range(10):
        best = np.inf
        for e in bank[d]:
            dd = _dtw(unit_track, e)
            if dd < best:
                best = dd
        dist[d] = best
    return F2.soft_exclude_from_distance(dist)


def _frame_to_sample(M_frames, n_samples, frame_idx):
    """Map a cochleagram-frame index to a sample index (the cleaned read is ~100 fps
    over the run-on; map proportionally). Mechanical."""
    if M_frames <= 0:
        return 0
    return int(round(frame_idx / M_frames * n_samples))


def decode_runon(runon, bank, fwd, bwd, fwd2, bwd2, lm_weight=1.0, sheaf_depth=2,
                 use_clean=True, segmentation="relax"):
    """Decode ONE run-on string end-to-end. Returns the predicted digit-index list.
      · STAGE 1: cleaned read + sharp onset (or raw, per use_clean).
      · STAGE 2: segment the onset into units (relaxation oscillator, or a no-seg /
        uniform-grid baseline per `segmentation`).
      · STAGE 3: per-unit acoustic excluder over the cleaned read + the real digit
        n-gram collapse (Viterbi). The collapse is the agent's weighted_admissibility.
    """
    runon = np.asarray(runon, dtype=np.float64)
    n = runon.size
    track_fn = _clean_track if use_clean else _raw_track
    # ---- STAGE 1 ----
    Mc = RT.clean_read(runon) if use_clean else RT.raw_read(runon)
    if Mc.size == 0:
        return []
    F = Mc.shape[0]
    if use_clean:
        onset = RT.sharp_onset(runon, M_clean=Mc)
    else:
        onset = RT.raw_onset(runon, M_raw=Mc)
    # full cleaned/raw read as an L2-track for slicing into units
    full_track = []
    for r in range(F):
        v = Mc[r]
        nrm = np.linalg.norm(v)
        full_track.append(v / nrm if nrm > 1e-9 else v)
    full_track = np.asarray(full_track, dtype=np.float64)

    # ---- STAGE 2: segmentation ----
    if segmentation == "relax":
        fires = RO.segment_boundaries(onset)
        spans = RO.segments_from_boundaries(fires, F)
    elif segmentation == "none":
        spans = [(0, F)]                          # the whole stream as ONE unit
    elif segmentation == "grid":
        # uniform grid at the AVERAGE syllable rate (~5/s -> ~20 frames at 100 fps),
        # a no-oscillator fixed-rate baseline (the world's mean rate, not the signal).
        step = 20
        spans = [(s, min(s + step, F)) for s in range(0, F, step)]
    else:
        raise ValueError(segmentation)

    # ---- STAGE 3: per-unit acoustic excluder + collapse ----
    excluders = []
    for (s, e) in spans:
        ut = full_track[s:e]
        excluders.append(unit_acoustic_excluder(ut, bank))
    T = len(excluders)
    if T == 0:
        return []
    # transition (context) frame: real digit bigram log-adm rows over the 10 digits.
    trans = np.zeros((10, 10), dtype=np.float64)
    for a, wa in enumerate(DIGITS):
        trans[a] = _cond_excluder(fwd.get(wa, collections.Counter()))
    # emission = acoustic (+) future-sheaf soft excluders. Future excluder for unit t
    # uses the (decoded-independent) successor n-gram column conditioned on the
    # acoustic argmax of unit t+1 (soft: we use the unit's acoustic excluder's argmax
    # digit word as the real successor — the future-sheaf over the segmented units).
    acou_argmax = [int(np.argmax(ex)) for ex in excluders]
    emis = np.zeros((T, 10), dtype=np.float64)
    for t in range(T):
        excl = [excluders[t]]
        wv = [1.0]
        if sheaf_depth >= 1 and t < T - 1:
            nxt = DIGITS[acou_argmax[t + 1]]
            fe = _cond_excluder(bwd.get(nxt, collections.Counter()))
            excl.append(fe); wv.append(lm_weight)
        if sheaf_depth >= 2 and t < T - 2:
            nxt2 = DIGITS[acou_argmax[t + 2]]
            fe2 = _cond_excluder(bwd2.get(nxt2, collections.Counter()))
            excl.append(fe2); wv.append(lm_weight)
        emis[t] = F2.weighted_admissibility(excl, wv)
    path = F2.viterbi_soft(emis, trans, w_trans=lm_weight)
    return path


# ===========================================================================
# WER — Levenshtein alignment of decoded digit string to truth (sub+ins+del)/len.
# The honest continuous metric: segmentation errors show up as ins/del.
# ===========================================================================

def wer(ref, hyp):
    """Word error rate = Levenshtein(ref, hyp) / len(ref). ref/hyp are index lists."""
    R, H = len(ref), len(hyp)
    if R == 0:
        return (0.0 if H == 0 else 1.0)
    dp = np.zeros((R + 1, H + 1), dtype=np.int64)
    for i in range(R + 1):
        dp[i, 0] = i
    for j in range(H + 1):
        dp[0, j] = j
    for i in range(1, R + 1):
        for j in range(1, H + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            dp[i, j] = min(dp[i - 1, j] + 1, dp[i, j - 1] + 1,
                           dp[i - 1, j - 1] + cost)
    return dp[R, H] / R


# ===========================================================================
# HARNESS — build the cross-speaker run-on test set ONCE; decode under each
# configuration (full machine + ablations). The same strings/banks are reused.
# ===========================================================================

def build_test_strings(held, n_strings, min_len, max_len, seed=7):
    """Build the cross-speaker run-on test set: each string is one HELD speaker's
    concatenated digit clips (held-out, never banked). Returns [(runon, truth)]."""
    rng = random.Random(seed)
    held_items = list(held.items())
    rng.shuffle(held_items)
    out = []
    i = 0
    while len(out) < n_strings and held_items:
        spk, clips = held_items[i % len(held_items)]
        runon, truth = make_runon(clips, rng, min_len, max_len)
        if runon is not None and truth:
            out.append((runon, truth))
        i += 1
        if i > n_strings * 20:
            break
    return out


def main():
    if not W.sc_available():
        print("Speech Commands not found at /tmp/sc — abort.", flush=True)
        print("CONTINUOUS_MACHINE_COMPLETED", flush=True)
        return
    n_train_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    n_held_spk = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    n_strings = int(sys.argv[3]) if len(sys.argv) > 3 else 120
    min_len = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    max_len = int(sys.argv[5]) if len(sys.argv) > 5 else 6
    n_per = 16

    print("=" * 80, flush=True)
    print("THE CONTINUOUS-SPEECH MACHINE — radio-telescope + relaxation oscillator",
          flush=True)
    print("                              + weighted-admissibility collapse", flush=True)
    print("  TASK: run-on connected-digit strings (vocab 10), cross-speaker held-out",
          flush=True)
    print("=" * 80, flush=True)

    # --- DONKEY AUDIT ---
    print("\n[donkey audit]", flush=True)
    print("  Stage 1 (radio-telescope): matched filter + incoherent integration + "
          "Hogbom CLEAN. Owned numpy, frozen constants, NO net/fit.", flush=True)
    print("  Stage 2 (relaxation oscillator): leaky integrate-and-fire + Mirollo-"
          "Strogatz pulse-coupled reset. Owned, frozen, NO net/fit.", flush=True)
    print("  Stage 3 (collapse): the agent's weighted_admissibility "
          "(frame_inference_v2) over the cleaned read + real digit n-gram.", flush=True)
    print("  LM: real LibriSpeech spelled-digit n-gram (the world). Held speakers "
          "NEVER banked.", flush=True)

    # --- the real digit LM ---
    print("\n[LM] counting real spelled-digit n-gram from LibriSpeech ...", flush=True)
    fwd, bwd, fwd2, bwd2, uni, n_utts = count_digit_ngram()
    n_bigrams = sum(sum(c.values()) for c in fwd.values())
    print(f"[LM] {n_utts} utterances contain digit words; {n_bigrams} digit-bigram "
          f"tokens; unigram: {dict(uni)}", flush=True)
    lm_sparse = n_bigrams < 50
    if lm_sparse:
        print("[LM] NOTE: the real digit n-gram is SPARSE (digits are rare in "
              "LibriSpeech read speech) -> the LM mostly ABSTAINS; the decode leans "
              "on the acoustic frame. Reported honestly.", flush=True)

    # --- split + banks (CLEANED and RAW, built once) ---
    train, held = build_split(n_train_spk, n_held_spk, n_per)
    if not train or not held:
        print("Not enough speakers — abort.", flush=True)
        print("CONTINUOUS_MACHINE_COMPLETED", flush=True)
        return
    print("[bank] building CLEANED-read exemplar bank (train speakers) ...", flush=True)
    t0 = time.time()
    bank_clean = build_bank(train, _clean_track)
    print(f"[bank] cleaned bank: {sum(len(v) for v in bank_clean.values())} exemplars "
          f"({time.time()-t0:.0f}s)", flush=True)
    t0 = time.time()
    bank_raw = build_bank(train, _raw_track)
    print(f"[bank] raw bank: {sum(len(v) for v in bank_raw.values())} exemplars "
          f"({time.time()-t0:.0f}s)", flush=True)

    # --- the cross-speaker run-on test set (built once) ---
    test = build_test_strings(held, n_strings, min_len, max_len)
    tot_digits = sum(len(t) for _r, t in test)
    print(f"[test] {len(test)} run-on strings, {tot_digits} digit tokens "
          f"(cross-speaker held-out)", flush=True)
    if not test:
        print("No test strings — abort.", flush=True)
        print("CONTINUOUS_MACHINE_COMPLETED", flush=True)
        return

    # =====================================================================
    # (b) ABLATION 1 — SEGMENTATION: relaxation oscillator vs sine entrain_theta.
    # Cross-speaker unit-count error (pred/true ratio). The oscillator must beat the
    # sine's ~0.64 bar. Run on the SAME run-on strings (sharp onset for both readers).
    # =====================================================================
    print("\n" + "=" * 80, flush=True)
    print("ABLATION 1 — SEGMENTATION: relaxation oscillator vs sine entrain_theta",
          flush=True)
    print("  (cross-speaker unit-count vs true digit count on the run-on strings)",
          flush=True)
    print("-" * 80, flush=True)
    relax_ratios, sine_ratios = [], []
    relax_err, sine_err = [], []
    grid_ratios = []
    for runon, truth in test:
        true_n = len(truth)
        # relaxation oscillator on the SHARP (Stage-1) onset
        onset = RT.sharp_onset(runon)
        relax_n = RO.count_from_onset(onset)
        # sine entrain_theta on the raw waveform (the prior reader, its own envelope)
        sine_n, _ = P.entrain_theta(runon)
        relax_ratios.append(relax_n / true_n); relax_err.append(abs(relax_n - true_n))
        sine_ratios.append(sine_n / true_n); sine_err.append(abs(sine_n - true_n))
    relax_ratio = float(np.mean(relax_ratios)); sine_ratio = float(np.mean(sine_ratios))
    relax_mae = float(np.mean(relax_err)); sine_mae = float(np.mean(sine_err))
    print(f"  {'reader':<26}{'pred/true':>12}{'mean|err|':>12}", flush=True)
    print(f"  {'relaxation oscillator':<26}{relax_ratio:>12.3f}{relax_mae:>12.3f}",
          flush=True)
    print(f"  {'sine entrain_theta':<26}{sine_ratio:>12.3f}{sine_mae:>12.3f}",
          flush=True)
    seg_better = relax_mae < sine_mae
    print(f"  -> relaxation oscillator {'BEATS' if seg_better else 'does NOT beat'} "
          f"sine on count error; pred/true {relax_ratio:.3f} (sine {sine_ratio:.3f}; "
          f"sine bar ~0.64)", flush=True)

    # =====================================================================
    # (b) ABLATION 2 — FRONT END: cleaned read vs raw cochleagram. Onset sharpness
    # (peakiness = peak / mean of the onset) + end-to-end WER under each.
    # =====================================================================
    print("\n" + "=" * 80, flush=True)
    print("ABLATION 2 — FRONT END: radio-telescope CLEANED vs RAW cochleagram",
          flush=True)
    print("-" * 80, flush=True)
    def _peakiness(o):
        o = np.asarray(o, dtype=np.float64)
        m = o.mean()
        return float(o.max() / m) if m > 1e-12 else 0.0
    sharp_pk, raw_pk = [], []
    for runon, _t in test:
        sharp_pk.append(_peakiness(RT.sharp_onset(runon)))
        raw_pk.append(_peakiness(RT.raw_onset(runon)))
    print(f"  onset sharpness (peak/mean): CLEANED {np.mean(sharp_pk):.2f}  "
          f"RAW {np.mean(raw_pk):.2f}", flush=True)

    # =====================================================================
    # (a) END-TO-END + (b) the remaining ablations: decode WER under each config.
    # configs: full machine (clean+relax), raw front end (raw+relax), no-seg, grid.
    # =====================================================================
    print("\n" + "=" * 80, flush=True)
    print("END-TO-END DECODE (WER, lower=better) — full machine + ablations", flush=True)
    print("-" * 80, flush=True)

    def eval_config(use_clean, segmentation, bank):
        wers, accs = [], []
        for runon, truth in test:
            hyp = decode_runon(runon, bank, fwd, bwd, fwd2, bwd2,
                               lm_weight=(1.0 if not lm_sparse else 0.5),
                               sheaf_depth=2, use_clean=use_clean,
                               segmentation=segmentation)
            wers.append(wer(truth, hyp))
            # position-wise accuracy only where lengths match (a secondary read)
            accs.append(1.0 - wers[-1])
        return float(np.mean(wers)), len(wers)

    t0 = time.time()
    wer_full, n_full = eval_config(True, "relax", bank_clean)
    print(f"  FULL MACHINE     (clean read + relaxation seg + collapse): "
          f"WER {wer_full:.3f}  n={n_full}  ({time.time()-t0:.0f}s)", flush=True)
    t0 = time.time()
    wer_raw_fe, _ = eval_config(False, "relax", bank_raw)
    print(f"  RAW FRONT END    (raw cochleagram + relaxation seg + collapse): "
          f"WER {wer_raw_fe:.3f}  ({time.time()-t0:.0f}s)", flush=True)
    t0 = time.time()
    wer_noseg, _ = eval_config(True, "none", bank_clean)
    print(f"  NO SEGMENTATION  (clean read, whole stream as 1 unit + collapse): "
          f"WER {wer_noseg:.3f}  ({time.time()-t0:.0f}s)", flush=True)
    t0 = time.time()
    wer_grid, _ = eval_config(True, "grid", bank_clean)
    print(f"  UNIFORM GRID     (clean read, fixed-rate grid seg + collapse): "
          f"WER {wer_grid:.3f}  ({time.time()-t0:.0f}s)", flush=True)

    # =====================================================================
    # VERDICT
    # =====================================================================
    print("\n" + "=" * 80, flush=True)
    print("VERDICT", flush=True)
    print("=" * 80, flush=True)
    chance_wer = 1.0 - 1.0 / 10                       # random digit per slot ~0.9 WER
    print(f"  TASK: run-on connected-digit strings, vocab 10, cross-speaker held-out.",
          flush=True)
    print(f"  (a) END-TO-END: the integrated machine decodes the continuous stream at "
          f"WER {wer_full:.3f} (word-accuracy {1-wer_full:.3f}); chance WER ~{chance_wer:.2f}; "
          f"n={n_full} strings, {tot_digits} digit tokens.", flush=True)
    recognises = wer_full < 0.5
    verb = "RECOGNISES" if recognises else "does NOT reliably recognise"
    note = "WER below 0.5" if recognises else "WER >= 0.5"
    print(f"      -> the machine {verb} the continuous speech ({note}).", flush=True)
    print(f"  (b) ABLATIONS — which stage carries it:", flush=True)
    print(f"      · segmentation: relaxation oscillator pred/true {relax_ratio:.3f} "
          f"(mae {relax_mae:.2f}) vs sine {sine_ratio:.3f} (mae {sine_mae:.2f}) -> "
          f"{'relaxation BEATS sine' if seg_better else 'sine not beaten'}.", flush=True)
    print(f"      · front end: CLEANED onset sharpness {np.mean(sharp_pk):.2f} vs RAW "
          f"{np.mean(raw_pk):.2f}; decode WER clean {wer_full:.3f} vs raw "
          f"{wer_raw_fe:.3f} -> {'cleaned helps' if wer_full < wer_raw_fe else 'cleaned does not help'}.",
          flush=True)
    print(f"      · segmentation@collapse: relaxation-segmented WER {wer_full:.3f} vs "
          f"no-seg {wer_noseg:.3f} vs grid {wer_grid:.3f} -> "
          f"{'segmentation helps' if wer_full < min(wer_noseg, wer_grid) else 'segmentation does not clearly help'}.",
          flush=True)
    # honest carrier
    best_abl = min([("full", wer_full), ("raw_fe", wer_raw_fe),
                    ("noseg", wer_noseg), ("grid", wer_grid)], key=lambda t: t[1])
    print(f"  CARRIER: lowest-WER config = {best_abl[0]} (WER {best_abl[1]:.3f}).",
          flush=True)
    print("\n[MARKER] CONTINUOUS_MACHINE_COMPLETED", flush=True)


if __name__ == "__main__":
    main()
