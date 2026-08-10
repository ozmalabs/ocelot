"""nursery_layers — decompose a HANDFUL of sung nursery rhymes into their
LAYERED structure and learn it, using the agent's OWNED native ops.

THE REFRAME this tests: a nursery rhyme is so densely / redundantly
structured (rhythm, melody, harmony, lyric — mutually predictive and
ALIGNED) that a few contain more recoverable structure than hours of
adult cross-speaker speech.  The music is NOT noise to strip; it is the
structure LAYERED, and the layering is OVER-DETERMINED, so the structure
is recoverable where adult cross-speaker speech HID it (the ~40% / 20-word
wall = "structure not recoverable from that signal").

LAYERS — each from owned ops, native where the structure-extraction lives:

  band matrix  (I/O boundary)   cochlea() + a1_responses()  -> per-band
                                envelope -> frames x bands.  Native Rust
                                gammatone bank; numpy only frames the
                                envelope (exactly as cmvn / relational_shape
                                lay a matrix out at the I/O boundary).

  RHYTHM/BEAT   find_peak_boundaries()  — the agent's dissimilarity-peak
                boundary Term evaluated NATIVELY (order-1-time change-rate
                peaks).  Does the beat give CLEAR, REGULAR boundaries (vs
                the coarticulated adult mush that broke segmentation)?

  MELODY/PITCH  _estimate_f0()  — the agent's autocorrelation f0 (the
                SOURCE / pitch), per frame, on the LOG2 (octave) axis = the
                melody / prosody contour.

  SPEECH/LYRIC  relational_shape()  — the agent's whole-unit RELATIONAL
                rep (native rank + self-similarity Terms) of each
                beat-chunk = the lyric units.

  ALIGNMENT     do the layers ALIGN + mutually predict?  beat onsets <->
                energy/pitch reconfiguration; recurring chunks (chorus /
                repetition) recur (lexicon CONDENSES); rhyme positions
                share a rime (the alphabet labeled by the data).

DISCIPLINE: data fetch + layer framing = world-adapter I/O.  The
structure-extraction (peak boundaries, relational rep, recurrence) is the
agent's native ops.  Donkey-clean: NO .fit / sklearn / gradient / loss /
torch / sweep, no fitted model.  Selector = structure recurrence /
alignment, read as NUMBERS not a boolean.
"""
from __future__ import annotations

import sys
import wave
import numpy as np

sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")

import substrate_rs.audio as A
from substrate_rs import Substrate

from domains.dissimilarity_segmentation import find_peak_boundaries, chunk_by_peaks
from domains.relational_shape import relational_shape
from domains.sound_graph import _estimate_f0


# --------------------------------------------------------------------------
# I/O boundary: wav -> samples.
# --------------------------------------------------------------------------

def load_wav(path):
    with wave.open(path, "rb") as w:
        fs = w.getframerate()
        n = w.getnframes()
        ch = w.getnchannels()
        buf = w.readframes(n)
    x = np.frombuffer(buf, dtype=np.int16).astype(np.float32)
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    peak = np.abs(x).max() + 1e-9
    return (x / peak).astype(np.float32), fs


# --------------------------------------------------------------------------
# Band matrix (I/O boundary, native cochlea): cochlea + a1_responses ->
# per-band envelope -> frames x bands.  The gammatone bank + filtering are
# the agent's native Rust audio ops; numpy only frames the envelope.
# --------------------------------------------------------------------------

def band_matrix(x, fs, n_bands=16, low_hz=80, high_hz=6000,
                frame_ms=25, hop_ms=10):
    s = Substrate()
    A.seed_audio_grammar(s)
    buf = A.audio_from_array(s, x.astype(np.float32), sample_rate=fs)
    bank = A.cochlea(s, n_bands=n_bands, fs=fs, low_hz=low_hz, high_hz=high_hz)
    resp = A.a1_responses(s, buf, bank)               # native band filtering
    env = []
    for r in resp:
        y = np.asarray(A.audio_to_array(s, r), dtype=np.float32).reshape(-1)
        env.append(np.abs(y))                          # half-wave/abs envelope
    env = np.stack(env, axis=0)                        # bands x samples
    hop = max(1, int(hop_ms * fs / 1000))
    win = max(hop, int(frame_ms * fs / 1000))
    n = env.shape[1]
    frames = []
    for start in range(0, n - win + 1, hop):
        frames.append(env[:, start:start + win].mean(axis=1))
    M = np.stack(frames, axis=0) if frames else env.T  # frames x bands
    # log-compress (loudness ~ log power), the perceptual axis
    M = np.log1p(M)
    return M, hop, fs


# --------------------------------------------------------------------------
# MELODY/PITCH layer: native autocorrelation f0 per frame, log2 (octave).
# --------------------------------------------------------------------------

def f0_contour(x, fs, hop, n_frames, win_ms=40):
    win = int(win_ms * fs / 1000)
    f0 = np.zeros(n_frames, dtype=np.float32)
    for t in range(n_frames):
        c = t * hop
        seg = x[max(0, c - win // 2): c + win // 2]
        if len(seg) < win // 2:
            continue
        f0[t] = _estimate_f0(seg, fs)                  # agent's native f0
    voiced = f0 > 0
    octave = np.zeros_like(f0)
    octave[voiced] = np.log2(f0[voiced])               # LOG (octave) axis
    return f0, octave, voiced


# --------------------------------------------------------------------------
# Structure metrics — read the recovered structure as NUMBERS.
# --------------------------------------------------------------------------

def beat_periodicity(M, hop, fs):
    """The BEAT layer as the PERIODICITY of the agent's order-1-time
    change-rate (its owned op).  A clean metronomic musical pulse makes
    the energy-onset flux REPEAT at a fixed lag, so the autocorrelation of
    the flux has a sharp peak at the beat period.  This reads the beat as
    a periodic STRUCTURE, not a raw peak count (the frame-grain dissimilarity
    peaks are syllable transients, an order finer than the beat).

    Returns the beat lag, bpm, and autocorr strength (0..1).  Adult
    coarticulated speech has NO such periodic pulse -> flat autocorr."""
    E = M.sum(axis=1)                                   # per-frame loudness
    flux = np.diff(E)
    flux[flux < 0] = 0.0                                # positive onset flux
    fc = flux - flux.mean()
    if not np.any(fc):
        return None
    ac = np.correlate(fc, fc, mode="full")[len(fc) - 1:]
    ac = ac / (ac[0] + 1e-9)
    hop_s = hop / fs
    lo = int(0.25 / hop_s)                              # 240 bpm ceiling
    hi = min(int(1.6 / hop_s), len(ac) - 1)            # 37.5 bpm floor
    if hi <= lo:
        return None
    pl = lo + int(np.argmax(ac[lo:hi]))
    period_s = pl * hop_s
    # metrical NESTING: does the autocorr also peak at 2x the beat (a bar)?
    pl2 = 2 * pl
    nest = float(ac[pl2]) if pl2 < len(ac) else 0.0
    return {
        "beat_period_s": float(period_s),
        "bpm": float(60.0 / period_s) if period_s > 0 else 0.0,
        "autocorr_strength": float(ac[pl]),
        "bar_strength_2x": nest,
    }


def chunk_relational_reps(M, cuts, min_len=4):
    """The lyric layer: the agent's relational_shape of each beat-chunk."""
    blocks = chunk_by_peaks(M, cuts)
    reps, lens = [], []
    for (block, n) in blocks:
        if n < min_len:
            continue
        reps.append(relational_shape(block))            # native rank+selfsim
        lens.append(n)
    return reps, lens


def _dtw_dist(a, b, band=8):
    """Banded DTW distance between two frames x feat trajectories — the
    agent's native match shape (banded monotonic DP), mean-normalised by
    path length.  Pure distance, no fitting."""
    na, nb = a.shape[0], b.shape[0]
    if na == 0 or nb == 0:
        return float("inf")
    INF = float("inf")
    prev = np.full(nb + 1, INF)
    prev[0] = 0.0
    for i in range(1, na + 1):
        cur = np.full(nb + 1, INF)
        jlo = max(1, i - band)
        jhi = min(nb, i + band)
        for j in range(jlo, jhi + 1):
            c = np.linalg.norm(a[i - 1] - b[j - 1])
            cur[j] = c + min(prev[j], prev[j - 1], cur[j - 1])
        prev = cur
    return prev[nb] / (na + nb)


def _beat_relational_track(M, beat_period_s, hop, fs):
    """Beat-synchronous lyric track: the agent's relational_shape of the
    whole rhyme, averaged into one relational vector per BEAT.  One row per
    beat = the unit at which a chorus / repeated line recurs."""
    R = relational_shape(M)                              # native rank+selfsim
    bf = max(1, int(round(beat_period_s * fs / hop)))    # frames per beat
    n_beats = R.shape[0] // bf
    if n_beats < 4:
        return None
    rows = np.stack([R[b * bf:(b + 1) * bf].mean(axis=0)
                     for b in range(n_beats)], axis=0)
    return rows                                          # n_beats x feat


def recurrence(M, beat_period_s, hop, fs):
    """Does the lexicon CONDENSE / does the rhyme REPEAT?  Build the
    beat-by-beat SELF-SIMILARITY matrix of the relational lyric track; a
    repeated section (verse / chorus) appears as an OFF-DIAGONAL STRIPE of
    high similarity (the canonical, threshold-free signature of musical
    repetition).  We measure:

      repeat_strength = how much more similar the best off-diagonal lag is
        than a random lag = (chance off-diag distance) / (best-lag distance).
        >1 means a genuine recurring structure; ~1 means none.

    No fitting, no tuned threshold — the diagonal-stripe ratio is read
    directly off the structure (the agent's 'learns from recurrence')."""
    rows = _beat_relational_track(M, beat_period_s, hop, fs)
    if rows is None:
        return None
    n = rows.shape[0]
    # z-score columns so cosine is over relational shape, not magnitude (I/O)
    rows = (rows - rows.mean(0)) / (rows.std(0) + 1e-6)
    # cosine distance self-similarity matrix
    nrm = np.linalg.norm(rows, axis=1, keepdims=True) + 1e-9
    U = rows / nrm
    S = U @ U.T                                          # similarity in [-1,1]
    Dm = 1.0 - S                                         # distance
    # For each lag k (>=2 beats), the mean distance along that diagonal.
    lag_dist = []
    for k in range(2, n - 2):
        diag = np.array([Dm[i, i + k] for i in range(n - k)])
        if diag.size:
            lag_dist.append((k, float(diag.mean())))
    if not lag_dist:
        return None
    lags = np.array([d for _, d in lag_dist])
    best_k, best_d = min(lag_dist, key=lambda t: t[1])
    chance = float(np.median(lags))
    repeat_strength = float(chance / (best_d + 1e-9))
    # how many beats participate in the best-lag stripe (distance < median)?
    diag = np.array([Dm[i, i + best_k] for i in range(n - best_k)])
    in_stripe = int((diag < chance * 0.7).sum())
    return {
        "n_beats": n,
        "best_repeat_lag_beats": int(best_k),
        "best_lag_dist": round(best_d, 3),
        "chance_lag_dist": round(chance, 3),
        "repeat_strength": round(repeat_strength, 3),
        "beats_in_repeat_stripe": in_stripe,
    }


def beat_pitch_alignment(cuts, octave, voiced, hop, fs):
    """ALIGNMENT: does the beat land where the MELODY reconfigures?  At
    each beat boundary measure |Δ octave| across the boundary (a pitch
    step / note change), vs the same statistic at random non-beat frames.
    If beats align with note onsets, boundary Δpitch >> random Δpitch."""
    cuts = sorted([c for c in cuts if 1 < c < len(octave) - 1])
    if len(cuts) < 3:
        return None

    def dpitch(t):
        a, b = octave[t - 1], octave[t]
        if not (voiced[t - 1] and voiced[t]):
            return None
        return abs(b - a)

    bvals = [dpitch(t) for t in cuts]
    bvals = [v for v in bvals if v is not None]
    rng = np.random.RandomState(0)
    rnd = []
    cutset = set(cuts)
    for _ in range(200):
        t = int(rng.randint(2, len(octave) - 1))
        if t in cutset:
            continue
        v = dpitch(t)
        if v is not None:
            rnd.append(v)
    if not bvals or not rnd:
        return None
    return {
        "beat_dpitch_mean": float(np.mean(bvals)),
        "random_dpitch_mean": float(np.mean(rnd)),
        "ratio": float(np.mean(bvals) / (np.mean(rnd) + 1e-9)),
        "n_voiced_beats": len(bvals),
    }


# --------------------------------------------------------------------------
# Driver.
# --------------------------------------------------------------------------

def analyse(path, name):
    x, fs = load_wav(path)
    # decimate to ~8 kHz to keep the native IIR bank fast (speech band intact)
    if fs >= 16000:
        x = x[::2]
        fs = fs // 2
    dur = len(x) / fs
    M, hop, fs2 = band_matrix(x, fs, n_bands=16)
    n_frames = M.shape[0]
    f0, octave, voiced = f0_contour(x, fs, hop, n_frames)

    # syllable/word-grain change-rate boundaries (the agent's native op) —
    # the FINE segmentation layer, an order below the beat.
    s = Substrate()
    cuts, dcurve = find_peak_boundaries(s, M, seq_tag=f"nursery_{name}",
                                        min_sep=4, smooth=1, gate="prominent")
    cuts = sorted(cuts)

    # BEAT layer: periodicity of the order-1 change-rate.
    beat = beat_periodicity(M, hop, fs2)
    beat_period = beat["beat_period_s"] if beat else None

    # RECURRENCE: beat-synchronous relational self-similarity stripes.
    rec = recurrence(M, beat_period, hop, fs2) if beat_period else None

    # ALIGNMENT: do the fine change-rate boundaries land on pitch steps?
    align = beat_pitch_alignment(cuts, octave, voiced, hop, fs2)

    vfrac = float(voiced.mean())
    f0v = f0[voiced]
    pitch_range_oct = float(octave[voiced].max() - octave[voiced].min()) if voiced.any() else 0.0

    return {
        "name": name,
        "duration_s": round(dur, 1),
        "n_frames": n_frames,
        "voiced_frac": round(vfrac, 2),
        "f0_median_hz": round(float(np.median(f0v)), 1) if f0v.size else 0.0,
        "pitch_range_octaves": round(pitch_range_oct, 2),
        "n_fine_boundaries": len(cuts),
        "beat": beat,
        "recurrence": rec,
        "alignment": align,
    }


def main():
    import json
    base = "/tmp/nursery"
    rhymes = [
        ("twinkle.wav", "twinkle"),
        ("baabaa.wav", "baabaa"),
        ("row.wav", "row"),
        ("mary.wav", "mary"),
        ("humpty.wav", "humpty"),
    ]
    results = []
    for fn, nm in rhymes:
        p = f"{base}/{fn}"
        try:
            r = analyse(p, nm)
        except Exception as e:
            import traceback
            r = {"name": nm, "error": repr(e), "tb": traceback.format_exc()}
        results.append(r)
        print(json.dumps(r, indent=2))
        sys.stdout.flush()

    # Aggregate verdict.
    print("\n================ AGGREGATE ================")
    bstr, ratios, rstr = [], [], []
    for r in results:
        if "error" in r:
            continue
        if r.get("beat"):
            bstr.append(r["beat"]["autocorr_strength"])
        if r.get("alignment"):
            ratios.append(r["alignment"]["ratio"])
        if r.get("recurrence"):
            rstr.append(r["recurrence"]["repeat_strength"])
    if bstr:
        print(f"BEAT periodicity (autocorr strength of change-rate): "
              f"mean {np.mean(bstr):.2f}  per-rhyme {[round(x,2) for x in bstr]}")
    if rstr:
        print(f"RECURRENCE (chorus/verse repeat-stripe strength, >1 = repeats): "
              f"mean {np.mean(rstr):.2f}  per-rhyme {[round(x,2) for x in rstr]}")
    if ratios:
        print(f"ALIGNMENT (fine boundary Δpitch / random Δpitch): "
              f"mean {np.mean(ratios):.2f}  per-rhyme {[round(x,2) for x in ratios]}")


if __name__ == "__main__":
    main()
