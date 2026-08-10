"""mcu_infer — SELF-CONTAINED, dependency-light inference path for the CONFIRMED
FSDD speaker-invariant digit recognizer (commit 2648ba07, LOSO 0.785).

This is the INFERENCE path ONLY — no training, no grounding, no substrate, no
research scaffolding. Every operation here is an MCU primitive: framing + window,
real FFT, mel filterbank (sparse weighted sums), per-frame vector mean/var/warp,
nearest-of-K codebook (optional), and banded DTW against a prototype lexicon.
numpy is used for the float REFERENCE, but each op is written so it maps 1:1 to
an MCU primitive (a loop of MACs / compares) — NO opaque library calls that
wouldn't port. An int16 FIXED-POINT variant runs alongside the float reference.

The confirmed recognizer pipeline (faithful re-implementation):
  audio (8 kHz int16) -> frame(32ms/16ms, Hanning) -> rFFT(2048) -> |.|
    -> 16 mel log bands -> M (frames x 16 log-mel)
  invariant transform (the winning method `uVTLN+ps_CMVN+PR`):
    (1) per-UTTERANCE forward VTLN warp of the band axis,
    (2) per-SPEAKER CMVN: subtract the test speaker's own pooled per-band
        mean/std (estimated at test time from their unlabelled audio),
    (3) coarticulation predict-remove (k=0.5, window 2).
  recognise: k-NN (k=3) banded-DTW against the train prototype lexicon.

The "model" is just the prototype lexicon (train utterances + their labels) plus,
for the codebook variant, a K=48 k-means codebook. Everything else is fixed DSP.

Run:
  python -m scripts.mcu_infer            # full LOSO, float + int16, all metrics
  python -m scripts.mcu_infer 6          # n_per_speaker = 6 (the commit's setting)
"""
from __future__ import annotations

import math
import os
import sys
import time
import wave
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA_DIR = "/tmp/fsdd/recordings"
DIGITS = ["zero", "one", "two", "three", "four", "five",
          "six", "seven", "eight", "nine"]

# ---- fixed DSP parameters (the confirmed pipeline) -----------------------
FS_TARGET = 8000          # FSDD native sample rate
FRAME_MS = 32.0
HOP_MS = 16.0
N_FFT = 2048
N_MEL = 16
MEL_LO = 80.0
MEL_HI = 3800.0
VOICED_FLOOR_FRAME = 0.05     # framing energy gate (sound_graph._voiced_frames)
VOICED_FLOOR_STAT = 0.25      # CMVN stat gate
PR_K = 0.5                    # predict-remove strength
PR_WINDOW = 2
DTW_BAND_FRAC = 0.25
KNN_K = 3

# ===========================================================================
#  OP COUNTER — every primitive increments this. Counts multiply-accumulates,
#  adds, compares, transcendentals as "ops" (1 op ~= 1 MCU cycle on a M4F with
#  single-cycle MAC / FPU; transcendentals counted at a realistic cost below).
# ===========================================================================

class Ops:
    def __init__(self):
        self.mac = 0      # multiply-accumulate (1 cycle on M4F DSP/FPU)
        self.add = 0      # add / sub / compare (1 cycle)
        self.trans = 0    # log / exp / sqrt / div (counted at TRANS_COST cycles)
        self.fft = 0      # rFFT calls (cost modelled separately)
    TRANS_COST = 20       # cycles for a transcendental on Cortex-M4F (no HW div/log)
    FFT_COST = lambda self, n: int(2.5 * n * math.log2(n))  # radix-2 rFFT ~2.5 N log2 N
    def total_cycles(self):
        return (self.mac + self.add
                + self.trans * self.TRANS_COST
                + self.fft * self.FFT_COST(N_FFT))
    def report(self):
        return (f"mac={self.mac:,} add={self.add:,} trans={self.trans:,} "
                f"ffts={self.fft} -> total ~{self.total_cycles():,} cycles")


# ===========================================================================
#  AUDIO LOAD (world I/O boundary — not counted; an MCU reads the mic DMA buffer)
# ===========================================================================

def load_wav(path):
    with wave.open(path, "rb") as w:
        fs = w.getframerate()
        n = w.getnframes()
        buf = w.readframes(n)
    arr = np.frombuffer(buf, dtype=np.int16).astype(np.float32) / 32768.0
    peak = max(float(np.abs(arr).max()), 1.0)
    return (arr * 0.7 / peak).astype(np.float32), fs


def gather_files():
    import re
    rx = re.compile(r"(\d)_([a-z]+)_(\d+)\.wav")
    out = []
    for fn in sorted(os.listdir(DATA_DIR)):
        m = rx.match(fn)
        if m:
            d, spk, idx = m.groups()
            out.append((os.path.join(DATA_DIR, fn), int(d), spk, int(idx)))
    return out


# ===========================================================================
#  FRONT-END — framing + Hanning + rFFT + mel log bands. Every op an MCU
#  primitive. (FFT counted as a call; the rest as MAC/add/trans.)
# ===========================================================================

_HANN = None
def _hann(flen):
    global _HANN
    if _HANN is None or len(_HANN) != flen:
        _HANN = np.hanning(flen).astype(np.float32)
    return _HANN


def _mel_filterbank(fs):
    """Sparse triangular mel filterbank as (band -> list of (bin, weight)).
    On an MCU this is a precomputed sparse weight table; applying it = a sum of
    weighted FFT-magnitude bins per band. We use a rectangular average matched to
    the confirmed pipeline (mean of |FFT| in [edge[b], edge[b+1])), which is the
    cheapest possible filterbank (uniform weights)."""
    def hz2mel(f): return 2595.0 * math.log10(1.0 + f / 700.0)
    def mel2hz(m): return 700.0 * (10 ** (m / 2595.0) - 1.0)
    mels = np.linspace(hz2mel(MEL_LO), hz2mel(MEL_HI), N_MEL + 1)
    edges = mel2hz(mels)
    freqs = np.fft.rfftfreq(N_FFT, 1.0 / fs)
    table = []
    for b in range(N_MEL):
        bins = np.where((freqs >= edges[b]) & (freqs < edges[b + 1]))[0]
        table.append(bins)
    return table


def front_end(samples, fs, ops):
    """audio -> (frames x N_MEL) log-mel. Voiced frames only (energy gate)."""
    n = len(samples)
    flen = int(fs * FRAME_MS / 1000)
    hop = int(fs * HOP_MS / 1000)
    if flen < 64 or n < flen:
        return np.zeros((0, N_MEL), dtype=np.float32)
    han = _hann(flen)
    fbank = _mel_filterbank(fs)
    starts = list(range(0, n - flen + 1, hop))
    # frame RMS energies for the voicing gate
    energies = []
    for s in starts:
        seg = samples[s:s + flen]
        e = float(np.sqrt(np.mean(seg * seg)) + 1e-9)
        ops.mac += flen          # seg*seg
        ops.add += flen          # sum
        ops.trans += 1           # sqrt
        energies.append(e)
    if not energies:
        return np.zeros((0, N_MEL), dtype=np.float32)
    emax = max(energies); ops.add += len(energies)
    thr = VOICED_FLOOR_FRAME * emax
    rows = []
    for s, e in zip(starts, energies):
        if e < thr:
            continue
        win = samples[s:s + flen] * han
        ops.mac += flen                      # windowing
        mag = np.abs(np.fft.rfft(win, n=N_FFT))
        ops.fft += 1
        ops.add += N_FFT // 2 + 1            # magnitude (abs of complex ~ 1 op approx; +sqrt below)
        ops.trans += N_FFT // 2 + 1          # complex magnitude = sqrt(re^2+im^2)
        row = np.empty(N_MEL, dtype=np.float32)
        for b in range(N_MEL):
            bins = fbank[b]
            if len(bins):
                m = float(np.mean(mag[bins]))
                ops.add += len(bins)
                ops.trans += 1               # division by count
                row[b] = math.log(m + 1e-9)
                ops.trans += 1               # log
            else:
                row[b] = -20.0
        rows.append(row)
    return np.array(rows, dtype=np.float32) if rows else np.zeros((0, N_MEL), np.float32)


# ===========================================================================
#  INVARIANT TRANSFORM — per-utterance VTLN warp, per-speaker CMVN, predict-remove
# ===========================================================================

_LOG_LO, _LOG_HI = math.log(80.0), math.log(7500.0)
def band_centres(n=N_MEL):
    return np.array([math.exp(_LOG_LO + (_LOG_HI - _LOG_LO) * i / (n - 1))
                     for i in range(n)], dtype=np.float64)
_LOG_BC = np.log(band_centres())
_BPO = (N_MEL - 1) / ((_LOG_HI - _LOG_LO) / math.log(2.0))


def _voiced_stat_mask(M):
    e = M.sum(axis=1)
    if e.max() - e.min() <= 1e-12:
        return np.ones(M.shape[0], dtype=bool)
    e = e - e.min()
    thr = VOICED_FLOOR_STAT * e.max()
    v = e >= thr
    return v if v.sum() >= 2 else np.ones(M.shape[0], dtype=bool)


def estimate_vtl_logalpha(M, canonical, ops):
    fe = M.sum(axis=1); ops.add += M.size
    if fe.max() <= 1e-12:
        return 0.0
    thr = VOICED_FLOOR_STAT * fe.max()
    voiced = fe >= thr
    if voiced.sum() == 0:
        voiced = np.ones(M.shape[0], dtype=bool)
    cents = []
    for f in np.where(voiced)[0]:
        e = np.maximum(M[f], 0.0)
        s = e.sum(); ops.add += N_MEL
        if s <= 1e-12:
            cents.append(float(_LOG_BC.mean())); continue
        c = float((e * _LOG_BC).sum() / s)
        ops.mac += N_MEL; ops.trans += 1
        cents.append(c)
    return float(np.mean(cents)) - canonical


def warp_bands(M, log_alpha, ops):
    if abs(log_alpha) < 1e-9:
        return M.copy()
    shift = (log_alpha / math.log(2.0)) * _BPO
    src = np.clip(np.arange(N_MEL, dtype=np.float64) + shift, 0.0, N_MEL - 1)
    i0 = np.floor(src).astype(int)
    i1 = np.minimum(i0 + 1, N_MEL - 1)
    frac = src - i0
    out = (M[:, i0] * (1.0 - frac) + M[:, i1] * frac).astype(M.dtype)
    ops.mac += M.shape[0] * N_MEL * 2     # linear interp = 2 MACs/sample
    return out


def per_speaker_cmvn(M, mean, std, ops, eps=1e-6):
    out = M - mean
    ops.add += M.size
    out = out / (std + eps)
    ops.trans += M.size          # per-element divide
    return out.astype(M.dtype)


def predict_remove(M, ops, window=PR_WINDOW, k=PR_K):
    n = M.shape[0]
    out = np.empty_like(M)
    for r in range(n):
        ll = max(0, r - window)
        leftmu = M[ll:r + 1].mean(axis=0)
        rr = min(n - 1, r + window)
        rightmu = M[r:rr + 1].mean(axis=0)
        nb = (leftmu + rightmu) / 2.0
        out[r] = M[r] - k * (nb - M[r])
        ops.add += N_MEL * 4
        ops.mac += N_MEL * 2
    return out.astype(M.dtype)


# ===========================================================================
#  PER-SPEAKER STATS (estimated at TEST TIME from the speaker's own audio)
# ===========================================================================

def speaker_stats(mats):
    """Pool a speaker's voiced frames -> per-band (mean, std). No labels."""
    blocks = []
    for M in mats:
        v = _voiced_stat_mask(M)
        blocks.append(M[v])
    frames = np.concatenate(blocks, axis=0)
    return (frames.mean(axis=0, keepdims=True).astype(np.float32),
            frames.std(axis=0, keepdims=True).astype(np.float32))


# ===========================================================================
#  DTW — banded, the confirmed compare path. Pure scalar ops (MCU-mappable).
# ===========================================================================

def dtw(A, B, ops, band_frac=DTW_BAND_FRAC):
    na, nb = A.shape[0], B.shape[0]
    if na == 0 or nb == 0:
        return 1e18
    band = max(4, int(band_frac * max(na, nb)))
    INF = 1e18
    prev = np.full(nb + 1, INF); prev[0] = 0.0
    for i in range(1, na + 1):
        cur = np.full(nb + 1, INF)
        jl = max(1, i - band); jh = min(nb, i + band)
        ai = A[i - 1]
        for j in range(jl, jh + 1):
            diff = ai - B[j - 1]
            d = float(np.sqrt(np.dot(diff, diff)))
            ops.mac += N_MEL          # squared L2
            ops.add += N_MEL
            ops.trans += 1            # sqrt
            best = min(prev[j], cur[j - 1], prev[j - 1])
            ops.add += 3              # 3-way min
            if best >= INF:
                continue
            cur[j] = d + best
            ops.add += 1
        prev = cur
    return prev[nb] / (na + nb)


# ===========================================================================
#  FIXED-POINT (int16) VARIANT — features and prototypes quantised to int16,
#  DTW in integer arithmetic. The MCU-realistic path.
# ===========================================================================

# Global feature scale: log-mel + CMVN-normalised features sit in roughly
# [-6, +6]; we map that to int16 with a fixed Q-format (Q11 -> 1/2048 LSB,
# range +-16). Chosen once, not tuned per-utterance.
Q_FRAC = 11
Q_SCALE = 1 << Q_FRAC          # 2048
Q_MAX = 32767; Q_MIN = -32768

def to_q15(M):
    """Quantise a float feature matrix to int16 (Qx.11)."""
    q = np.round(M * Q_SCALE)
    q = np.clip(q, Q_MIN, Q_MAX)
    return q.astype(np.int16)


def dtw_int(A, B, ops, band_frac=DTW_BAND_FRAC):
    """Integer banded DTW. A,B int16 (Q11). Distances accumulated as int64 of the
    squared-L2 surrogate (we use sum|diff| L1 in int to avoid sqrt — a valid MCU
    metric; cross-checked against float L2 below for accuracy)."""
    na, nb = A.shape[0], B.shape[0]
    if na == 0 or nb == 0:
        return np.iinfo(np.int64).max
    band = max(4, int(band_frac * max(na, nb)))
    INF = np.iinfo(np.int64).max
    A = A.astype(np.int32); B = B.astype(np.int32)
    prev = np.full(nb + 1, INF, dtype=np.int64); prev[0] = 0
    for i in range(1, na + 1):
        cur = np.full(nb + 1, INF, dtype=np.int64)
        jl = max(1, i - band); jh = min(nb, i + band)
        ai = A[i - 1]
        for j in range(jl, jh + 1):
            diff = ai - B[j - 1]
            d = int(np.abs(diff).sum())     # L1, integer — no sqrt, no div
            ops.add += N_MEL * 2
            best = min(prev[j], cur[j - 1], prev[j - 1])
            ops.add += 3
            if best >= INF:
                continue
            cur[j] = d + best
            ops.add += 1
        prev = cur
    # normalise by path length in integer (>> not / on MCU; here exact)
    return int(prev[nb] // (na + nb))


# ===========================================================================
#  FULL PIPELINE per utterance (front-end -> invariant transform). Returns the
#  normalised float feature matrix. Speaker stats supplied (per-speaker CMVN).
# ===========================================================================

def normalise(M, spk_mean, spk_std, canonical, ops, do_vtln=True):
    out = M
    if do_vtln:
        la = estimate_vtl_logalpha(out, canonical, ops)
        out = warp_bands(out, la, ops)
    out = per_speaker_cmvn(out, spk_mean, spk_std, ops)
    out = predict_remove(out, ops)
    return out


# ===========================================================================
#  CORPUS + LOSO RECOGNITION (float reference AND int16)
# ===========================================================================

def build_corpus(n_per_speaker=6, seed=0):
    rng = np.random.default_rng(seed)
    files = gather_files()
    buckets = defaultdict(list)
    for path, d, spk, idx in files:
        buckets[(d, spk)].append(path)
    corpus = []
    ops0 = Ops()
    for (d, spk), paths in sorted(buckets.items()):
        paths = sorted(paths); rng.shuffle(paths)
        for p in paths[:n_per_speaker]:
            x, fs = load_wav(p)
            M = front_end(x, fs, ops0)
            if M.shape[0] >= 2:
                corpus.append((M, DIGITS[d], spk))
    return corpus, ops0


def canonical_log_centroid(mats):
    cents = []
    for M in mats:
        fe = M.sum(axis=1)
        if fe.max() <= 1e-12:
            continue
        voiced = fe >= VOICED_FLOOR_STAT * fe.max()
        if voiced.sum() == 0:
            voiced = np.ones(M.shape[0], dtype=bool)
        for f in np.where(voiced)[0]:
            e = np.maximum(M[f], 0.0); s = e.sum()
            cents.append(float((e * _LOG_BC).sum() / s) if s > 1e-12
                         else float(_LOG_BC.mean()))
    return float(np.mean(cents)) if cents else float(_LOG_BC.mean())


def _majority(items):
    return Counter(items).most_common(1)[0][0]


def _medoid_protos(tr_mats, tr_words, protos_per_digit, dtw_fn):
    """Reduce the train fold to `protos_per_digit` medoid prototypes per word.
    The medoid = the in-class utterance with minimum total DTW to its classmates
    (a pure DTW operation — done offline at lexicon-build time, not on the MCU).
    Returns (reduced_mats, reduced_words)."""
    scratch = Ops()
    by_w = defaultdict(list)
    for M, w in zip(tr_mats, tr_words):
        by_w[w].append(M)
    rm, rw = [], []
    for w, mats in by_w.items():
        if len(mats) <= protos_per_digit:
            rm.extend(mats); rw.extend([w] * len(mats)); continue
        # total in-class DTW per candidate
        tot = []
        for a in range(len(mats)):
            s = sum(dtw_fn(mats[a], mats[b], scratch)
                    for b in range(len(mats)) if b != a)
            tot.append((s, a))
        tot.sort()
        for _, a in tot[:protos_per_digit]:
            rm.append(mats[a]); rw.append(w)
    return rm, rw


def loso(corpus, fixed_point=False, k=KNN_K, verbose=True, protos_per_digit=None):
    """Leave-one-speaker-out. Per-speaker CMVN stats estimated from the held-out
    speaker's OWN audio at test time. Returns (mean_acc, unigram, ops_per_utt,
    n_test_utts, dtw_calls_per_utt).

    protos_per_digit: if set, the train fold is reduced to that many DTW-medoid
    prototypes per digit (the compact deployed lexicon). None = full k-NN over all
    train utterances (the confirmed recognizer's exact form)."""
    speakers = sorted(set(s for _, _, s in corpus))
    canonical = canonical_log_centroid([M for M, _, _ in corpus])

    # normalise every utterance with its speaker's pooled stats
    by_spk = defaultdict(list)
    for M, w, s in corpus:
        by_spk[s].append((M, w))
    stats = {s: speaker_stats([M for M, _ in by_spk[s]]) for s in speakers}

    norm_ops = Ops()
    normed = []   # (featmat, word, speaker)
    for M, w, s in corpus:
        mean, std = stats[s]
        Mn = normalise(M, mean, std, canonical, norm_ops)
        if fixed_point:
            Mn = to_q15(Mn)
        normed.append((Mn, w, s))

    dtw_fn = dtw_int if fixed_point else dtw
    accs, unis = [], []
    rec_ops = Ops()
    dtw_calls = 0; n_test = 0
    last_n_protos = 0
    eff_k = 1 if protos_per_digit == 1 else k
    for held in speakers:
        train = [(M, w) for M, w, s in normed if s != held]
        test = [(M, w) for M, w, s in normed if s == held]
        tr_mats = [M for M, _ in train]; tr_words = [w for _, w in train]
        if protos_per_digit is not None:
            tr_mats, tr_words = _medoid_protos(tr_mats, tr_words,
                                               protos_per_digit, dtw_fn)
        last_n_protos = len(tr_mats)
        preds = []
        for Mt, _ in test:
            ds = sorted((dtw_fn(Mt, Mtr, rec_ops), wtr)
                        for Mtr, wtr in zip(tr_mats, tr_words))
            preds.append(_majority([w for _, w in ds[:eff_k]]))
            dtw_calls += len(tr_mats); n_test += 1
        acc = np.mean([p == t for p, (_, t) in zip(preds, test)])
        uni = np.mean([Counter(tr_words).most_common(1)[0][0] == t
                       for _, t in test])
        accs.append(acc); unis.append(uni)
        if verbose:
            print(f"    held-out {held:10s}: acc {acc:.3f}  unigram {uni:.3f}"
                  f"  n_test {len(test)}  train_protos {len(tr_mats)}")

    # ops per single test utterance = front-end + normalise + (DTW vs all protos)
    fe_per = None  # filled by caller (build_corpus ops / n_corpus)
    dtw_per_utt = dtw_calls / n_test
    norm_per_utt = norm_ops.total_cycles() / len(corpus)
    rec_per_utt = rec_ops.total_cycles() / n_test
    return {
        "acc": float(np.mean(accs)), "uni": float(np.mean(unis)),
        "per_speaker": list(zip(speakers, accs)),
        "norm_per_utt_cycles": norm_per_utt,
        "rec_per_utt_cycles": rec_per_utt,
        "dtw_calls_per_utt": dtw_per_utt,
        "n_train_protos": last_n_protos,   # protos used in the last fold
        "n_test": n_test,
    }


# ===========================================================================
#  MEMORY FOOTPRINT
# ===========================================================================

def memory_report(corpus, n_train_protos, bytes_per_feat_float=4,
                  bytes_per_feat_int=2):
    frame_lens = [M.shape[0] for M, _, _ in corpus]
    mean_frames = float(np.mean(frame_lens))
    max_frames = int(np.max(frame_lens))
    feat = N_MEL

    def model_bytes(bpf):
        lex = n_train_protos * mean_frames * feat * bpf      # prototype lexicon
        return lex
    lex_f = model_bytes(bytes_per_feat_float)
    lex_i = model_bytes(bytes_per_feat_int)
    spk_stats = 2 * N_MEL * 4         # mean+std, float (tiny)
    # working RAM
    frame_buf = N_FFT * 4             # fft scratch (float) / 2 if int
    dtw_mat = 2 * (max_frames + 1) * 8     # two int64/float rows (banded uses 2 rows)
    feat_buf_f = max_frames * feat * bytes_per_feat_float
    feat_buf_i = max_frames * feat * bytes_per_feat_int
    return {
        "mean_frames": mean_frames, "max_frames": max_frames,
        "n_protos": n_train_protos, "feat": feat,
        "lex_float_kb": lex_f / 1024, "lex_int16_kb": lex_i / 1024,
        "spk_stats_b": spk_stats,
        "frame_buf_b": frame_buf, "dtw_mat_b": dtw_mat,
        "feat_buf_float_kb": feat_buf_f / 1024, "feat_buf_int_kb": feat_buf_i / 1024,
        "total_float_kb": (lex_f + spk_stats + frame_buf + dtw_mat + feat_buf_f) / 1024,
        "total_int16_kb": (lex_i + spk_stats + frame_buf // 1 + dtw_mat + feat_buf_i) / 1024,
    }


# ===========================================================================
#  MAIN — measure all three numbers, float + int16
# ===========================================================================

def run(n_per_speaker=6, seed=0):
    print(f"=== SELF-CONTAINED MCU INFERENCE PROOF — FSDD digits, LOSO ===")
    print(f"n_per_speaker={n_per_speaker} seed={seed} "
          f"(matches commit 2648ba07 setting)\n")

    t0 = time.time()
    corpus, fe_ops = build_corpus(n_per_speaker, seed)
    n = len(corpus)
    fe_per_utt = fe_ops.total_cycles() / n
    print(f"corpus: {n} utts, 10 words, 6 speakers")
    print(f"front-end ops (whole corpus): {fe_ops.report()}")
    print(f"front-end per utterance: ~{fe_per_utt:,.0f} cycles\n")

    print("--- FLOAT reference LOSO ---")
    rf = loso(corpus, fixed_point=False)
    print(f"  FLOAT acc {rf['acc']:.3f}  vs unigram {rf['uni']:.3f}\n")

    print("--- INT16 fixed-point LOSO ---")
    ri = loso(corpus, fixed_point=True)
    print(f"  INT16 acc {ri['acc']:.3f}  vs unigram {ri['uni']:.3f}\n")

    # --- COMPACT DEPLOYED LEXICON: P medoid prototypes per digit, int16 ---
    print("--- INT16 + COMPACT LEXICON (medoid protos/digit) LOSO ---")
    reduced = {}
    for P in (1, 3, 5):
        rr = loso(corpus, fixed_point=True, protos_per_digit=P, verbose=False)
        reduced[P] = rr
        print(f"  P={P} protos/digit ({rr['n_train_protos']} total): "
              f"acc {rr['acc']:.3f}  DTW/utt {rr['dtw_calls_per_utt']:.0f}")
    print()

    # --- compute totals per utterance ---
    n_test = rf["n_test"]
    per_utt_float = (fe_per_utt + rf["norm_per_utt_cycles"]
                     + rf["rec_per_utt_cycles"])
    per_utt_int = (fe_per_utt + ri["norm_per_utt_cycles"]
                   + ri["rec_per_utt_cycles"])
    print("=== (2) COMPUTE / REAL-TIME FACTOR ===")
    print(f"  DTW calls per test utterance: {rf['dtw_calls_per_utt']:.0f}  "
          f"(= {rf['n_train_protos']} train prototypes, k-NN over all)")
    print(f"  ops/utt FLOAT: front-end {fe_per_utt:,.0f} + normalise "
          f"{rf['norm_per_utt_cycles']:,.0f} + recognise "
          f"{rf['rec_per_utt_cycles']:,.0f} = {per_utt_float:,.0f} cycles")
    print(f"  ops/utt INT16: front-end {fe_per_utt:,.0f} + normalise "
          f"{ri['norm_per_utt_cycles']:,.0f} + recognise "
          f"{ri['rec_per_utt_cycles']:,.0f} = {per_utt_int:,.0f} cycles")
    utt_dur = 0.5     # FSDD digit ~0.5 s
    for mhz in (150, 80):
        clk = mhz * 1e6
        for label, cyc in (("FLOAT", per_utt_float), ("INT16", per_utt_int)):
            wall = cyc / clk
            rtf = wall / utt_dur
            print(f"  @{mhz}MHz {label}: {wall*1000:.1f} ms/utt  "
                  f"RTF {rtf:.3f}  ({'REAL-TIME' if rtf < 1 else 'NOT real-time'}, "
                  f"{utt_dur/wall:.1f}x faster than audio)" if rtf < 1
                  else f"  @{mhz}MHz {label}: {wall*1000:.1f} ms/utt  RTF {rtf:.3f} "
                       f"NOT real-time")

    # --- memory ---
    mem = memory_report(corpus, rf["n_train_protos"])
    print(f"\n=== (1) MEMORY FOOTPRINT ===")
    print(f"  prototype lexicon: {mem['n_protos']} protos x "
          f"~{mem['mean_frames']:.0f} frames x {mem['feat']} feat")
    print(f"    float (4B): {mem['lex_float_kb']:.1f} KB   "
          f"int16 (2B): {mem['lex_int16_kb']:.1f} KB")
    print(f"  speaker stats: {mem['spk_stats_b']} B")
    print(f"  working RAM: fft scratch {mem['frame_buf_b']} B, "
          f"DTW rows {mem['dtw_mat_b']} B, "
          f"feat buf float {mem['feat_buf_float_kb']:.2f} KB / "
          f"int16 {mem['feat_buf_int_kb']:.2f} KB")
    print(f"  TOTAL float (full lexicon): {mem['total_float_kb']:.1f} KB")
    print(f"  TOTAL int16 (full lexicon): {mem['total_int16_kb']:.1f} KB")

    # compact-lexicon memory + RTF (int16) — the realistic deployed model
    print(f"\n  -- compact deployed lexicon (int16, medoid protos/digit) --")
    rec_per_proto = ri["rec_per_utt_cycles"] / ri["dtw_calls_per_utt"]
    for P, rr in reduced.items():
        m = memory_report(corpus, rr["n_train_protos"])
        rec_cyc = rec_per_proto * rr["dtw_calls_per_utt"]
        per_utt = fe_per_utt + ri["norm_per_utt_cycles"] + rec_cyc
        rtf150 = (per_utt / 150e6) / utt_dur
        rtf80 = (per_utt / 80e6) / utt_dur
        print(f"  P={P}: lexicon int16 {m['lex_int16_kb']:.1f} KB, "
              f"TOTAL int16 {m['total_int16_kb']:.1f} KB | "
              f"ops/utt {per_utt:,.0f} cyc, RTF@150 {rtf150:.3f} RTF@80 {rtf80:.3f} | "
              f"acc {rr['acc']:.3f}")

    print(f"\n=== (3) ACCURACY ===")
    print(f"  FLOAT (full)  {rf['acc']:.3f}   INT16 (full) {ri['acc']:.3f}   "
          f"unigram {rf['uni']:.3f}   confirmed 0.785")
    print(f"  INT16 compact: " +
          "  ".join(f"P{P}={reduced[P]['acc']:.3f}" for P in reduced))
    print(f"\nelapsed {time.time()-t0:.1f}s")
    return {"float": rf, "int16": ri, "reduced": reduced, "mem": mem,
            "fe_per_utt": fe_per_utt,
            "per_utt_float": per_utt_float, "per_utt_int": per_utt_int}


if __name__ == "__main__":
    npr = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    run(n_per_speaker=npr)
