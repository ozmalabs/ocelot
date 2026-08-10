"""TRY THE AV MACHINERY IN THE JELLYFIN WORLD — audiovisual SYNCHRONY on real TV. The GRID work
showed the lip-MOTION cue + held cochlea carry speech; here we test, unsupervised on real
content the agent actually watches (a live-action documentary), whether the lip cue is
SPEECH-SYNCHRONIZED: lip-motion vs audio speech-envelope should correlate, MAXIMAL at zero lag
and DROPPING when the audio is time-shifted (the falsifiable control). No labels — the shift
control is the test.

  VISUAL: per-frame face detect -> mouth ROI -> frame-diff lip-MOTION (the GRID raw-motion cue).
  AUDIO : held cochlea -> speech-band energy envelope, resampled to the video frame timeline.
  TEST  : within the longest stable talking-face run, Pearson corr(lip, audio) at lag 0 vs at
          shifted lags; AV sync = a zero-lag peak that the shift control removes.

Run: python scripts/jellyfin_av_sync.py [series] [seconds]
"""
from __future__ import annotations
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

import av
import cv2
cv2.setNumThreads(1)
from scipy.signal import resample_poly

from scripts.jellyfin_world import JellyfinWorld
from substrate_rs import Substrate
from substrate_rs.speech import _audio

CASC = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades,
                                          "haarcascade_frontalface_default.xml"))
HOP, WIN = 240, 400      # 30ms hop / 50ms window @ 8kHz (held cochleagram, inlined to avoid a
#                          transitive import that parses sys.argv at import time)


def cochleagram(s, bank, a8):
    buf = _audio.audio_from_array(s, a8, sample_rate=8000)
    arrs = []
    for r in _audio.a1_responses(s, buf, bank):
        a = _audio.audio_to_array(s, r).astype(np.float64)
        arrs.append(a.mean(1) if a.ndim > 1 else a)
    L = min(len(a) for a in arrs)
    nf = max(1, (L - WIN) // HOP + 1)
    M = np.zeros((nf, len(bank)))
    for fi in range(nf):
        sl = slice(fi * HOP, fi * HOP + WIN)
        for bi, a in enumerate(arrs):
            M[fi, bi] = np.sqrt(np.mean(a[sl] ** 2) + 1e-12)
    return M


def iou(a, b):
    ax, ay, aw, ah = a; bx, by, bw, bh = b
    ix, iy = max(ax, bx), max(ay, by)
    ix2, iy2 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    inter = max(0, ix2 - ix) * max(0, iy2 - iy)
    return inter / (aw * ah + bw * bh - inter + 1e-9)


def video_signals(url, max_frames, scale_w=640):
    """per-frame: face bbox (or None) + mouth frame-diff lip-MOTION within stable face runs."""
    c = av.open(url)
    vs = c.streams.video[0]; vs.thread_type = "NONE"
    fps = float(vs.average_rate)
    faces, motion = [], []
    prev_mouth = prev_upper = prev_box = None
    n = 0
    for fr in c.decode(vs):
        img = fr.to_ndarray(format="rgb24")
        h, w = img.shape[:2]
        sc = scale_w / w
        g = cv2.cvtColor(cv2.resize(img, (scale_w, int(h * sc))), cv2.COLOR_RGB2GRAY)
        fc = CASC.detectMultiScale(g, 1.1, 5, minSize=(40, 40))
        box = max(fc, key=lambda f: f[2] * f[3]) if len(fc) else None
        m = 0.0
        if box is not None:
            x, y, ww, hh = box
            mouth = cv2.resize(g[y + int(0.60 * hh):y + int(0.95 * hh),
                                 x + int(0.20 * ww):x + int(0.80 * ww)], (32, 24)).astype(np.float64)
            upper = cv2.resize(g[y + int(0.10 * hh):y + int(0.45 * hh),
                                 x + int(0.15 * ww):x + int(0.85 * ww)], (32, 24)).astype(np.float64)
            if prev_mouth is not None and prev_box is not None and iou(box, prev_box) > 0.4:
                # lip-SPECIFIC motion = mouth frame-diff MINUS upper-face (eyes/forehead) frame-
                # diff, which removes the common head/camera motion that isn't speech.
                m = max(0.0, float(np.mean(np.abs(mouth - prev_mouth)))
                        - float(np.mean(np.abs(upper - prev_upper))))
            prev_mouth, prev_upper = mouth, upper
        else:
            prev_mouth = prev_upper = None
        prev_box = box
        faces.append(box is not None); motion.append(m)
        n += 1
        if n >= max_frames:
            break
    return np.array(faces), np.array(motion), fps


def audio_env(url, n_frames, fps):
    """held cochlea -> speech-band (mid) energy envelope, resampled to the video frame timeline."""
    s = Substrate(); _audio.seed_audio_grammar(s)
    bank = _audio.cochlea(s, n_bands=24, fs=8000)
    c = av.open(url)
    aud = c.streams.audio[0]; aud.thread_type = "NONE"
    fsr = aud.codec_context.sample_rate
    blocks = []
    dur_needed = n_frames / fps + 1.0
    for f in c.decode(aud):
        a = f.to_ndarray()
        blocks.append(a.mean(0) if a.ndim == 2 else a)
        if sum(len(b) for b in blocks) / fsr > dur_needed:
            break
    a = np.concatenate(blocks)
    a8 = resample_poly(a, 8000, fsr)
    M = cochleagram(s, bank, a8.astype(np.float64))             # (T, 24) held cochleagram
    env = np.log(M[:, 4:16].sum(1) + 1e-6)                      # speech-band (mid) energy
    idx = np.linspace(0, len(env) - 1, n_frames).round().astype(int)
    return env[idx]


def all_runs(faces, min_len):
    runs = []; start = None
    for i, f in enumerate(list(faces) + [False]):
        if f and start is None:
            start = i
        elif not f and start is not None:
            if i - start >= min_len:
                runs.append((start, i))
            start = None
    return runs


def pear(a, b):
    a = a - a.mean(); b = b - b.mean()
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def main():
    series = sys.argv[1] if len(sys.argv) > 1 else "Secrets of the Zoo: Tampa"
    secs = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    jf = JellyfinWorld(); jf.connect()
    cat = {it["name"]: it for it in jf.catalog(kinds=("Series",))}
    eps = jf.episodes(cat[series]["id"], limit=3)
    url = jf.stream_url(eps[0]["id"])
    print("=" * 74)
    print(f"AV SYNCHRONY in the JELLYFIN world — '{series}' / '{eps[0]['name']}'")
    print("=" * 74)
    faces, motion, fps = video_signals(url, int(secs * 30))
    print(f"  decoded {len(faces)} frames @ {fps:.1f}fps; face present in "
          f"{faces.mean():.0%}", flush=True)
    env = audio_env(url, len(faces), fps)

    maxlag = max(3, int(0.33 * fps))
    runs = [(s, e) for s, e in all_runs(faces, int(1.2 * fps)) if e - s > 2 * maxlag + 6]
    if not runs:
        print("  no talking-face runs found"); return
    total = sum(e - s for s, e in runs)
    print(f"  {len(runs)} talking-face runs (>= 1.2s), {total/fps:.1f}s total\n", flush=True)

    rng = np.random.RandomState(0)

    def corr_at(L):                     # length-weighted mean Pearson across runs at lag L
        num = den = 0.0
        for s, e in runs:
            lip = motion[s:e]; aud = env[s:e]; w = e - s
            num += w * pear(lip[maxlag:w - maxlag], aud[maxlag + L:w - maxlag + L]); den += w
        return num / den

    cc = {L: corr_at(L) for L in range(-maxlag, maxlag + 1)}
    best_lag = max(cc, key=cc.get)
    shuf = np.mean([np.mean([pear(motion[s:e], rng.permutation(env[s:e])) for s, e in runs])
                    for _ in range(20)])
    print(f"  {'lag(s)':>8} {'corr(lip,audio)':>16}")
    for L in (-maxlag, -maxlag // 2, 0, maxlag // 2, maxlag):
        mark = "  <- zero lag" if L == 0 else ("  <- peak" if L == best_lag else "")
        print(f"  {L/fps:8.2f} {cc[L]:16.3f}{mark}")
    print("-" * 44)
    print(f"  zero-lag corr           : {cc[0]:+.3f}")
    print(f"  peak corr (lag {best_lag/fps:+.2f}s) : {cc[best_lag]:+.3f}")
    print(f"  shuffled-audio control  : {shuf:+.3f}  (chance)")
    print("=" * 74)
    verdict = ("AV-SYNCHRONOUS" if cc[0] - shuf > 0.05 and abs(best_lag) <= 0.2 * fps
               else "weak/none")
    print(f"  -> lip-motion vs speech-envelope: {verdict} "
          f"(zero-lag {cc[0]:+.2f} vs shuffled {shuf:+.2f}; peak at lag {best_lag/fps:+.2f}s)")


if __name__ == "__main__":
    main()
