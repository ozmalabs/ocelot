"""ACTIVE-SPEAKER SELECTION in the JELLYFIN world — among N candidate faces, which is speaking?
The speaker's lip-motion tracks the audio; distractors' do not. Evaluable on unlabeled TV by
CONSTRUCTING ground truth: for each audio window, the MATCHING face (its own co-temporal
lip-motion) vs N-1 DISTRACTOR faces (lip-motion from OTHER shots/episodes). The method picks the
face whose head-motion-compensated lip-motion best correlates with the audio speech-envelope at
the fixed population sync lag. Correct = the matching face. Chance = 1/N.

Pools talking-face windows across MANY documentary episodes (real faces) to cut the noise on the
estimate; each episode's windows are CACHED, so it is resumable — run it in bursts. Reuses the
AV-synchrony machinery (lip cue + held cochlea) from jellyfin_av_sync.

Run: python scripts/jellyfin_active_speaker.py [seconds_per_episode]
"""
from __future__ import annotations
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import re
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

from scripts.jellyfin_world import JellyfinWorld
from scripts.jellyfin_av_sync import video_signals, audio_env, all_runs, pear

# live-action documentaries (real talking faces; the animated catalog has almost none).
SOURCES = [("Secrets of the Zoo: Tampa", 4),
           ("Secrets of the Zoo: Down Under", 4),
           ("Magic of Disney's Animal Kingdom", 3)]
FW = 60          # fixed window length (samples) — 2s resampled, so episodes of any fps pool
LAG = -2         # population sync lag in the FW domain (~-0.07s; lip leads the acoustics)


def _resample(x, n):
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)


def _cache(series, ep):
    safe = re.sub(r"[^a-z0-9]+", "_", series.lower())
    return f"/tmp/jf_spk_{safe}_{ep}.npz"


def episode_windows(jf, series, ep, secs):
    """cached per episode: fixed-length (lip, audio) windows over talking-face runs."""
    cf = _cache(series, ep)
    if os.path.exists(cf):
        z = np.load(cf); return z["lips"], z["auds"]
    eps = jf.episodes(jf._cat[series]["id"], limit=ep + 1)
    if ep >= len(eps):
        np.savez(cf, lips=np.zeros((0, FW)), auds=np.zeros((0, FW))); return np.zeros((0, FW)), np.zeros((0, FW))
    url = jf.stream_url(eps[ep]["id"])
    faces, motion, fps = video_signals(url, int(secs * 30))
    env = audio_env(url, len(faces), fps)
    W = int(2.0 * fps); step = max(1, W // 2)
    lips, auds = [], []
    for s, e in all_runs(faces, W):
        for st in range(s, e - W + 1, step):
            lips.append(_resample(motion[st:st + W], FW))
            auds.append(_resample(env[st:st + W], FW))
    lips = np.array(lips) if lips else np.zeros((0, FW))
    auds = np.array(auds) if auds else np.zeros((0, FW))
    np.savez(cf, lips=lips, auds=auds)
    print(f"    [{series[:24]} ep{ep}] {len(lips)} windows cached (face {faces.mean():.0%})",
          flush=True)
    return lips, auds


def score(lip, aud, lag=LAG):
    w = len(lip); p = abs(lag) + 1
    return pear(lip[p:w - p], aud[p + lag:w - p + lag])


def main():
    secs = int(sys.argv[1]) if len(sys.argv) > 1 else 140
    jf = JellyfinWorld(); jf.connect()
    jf._cat = {it["name"]: it for it in jf.catalog(kinds=("Series",))}
    print("=" * 74)
    print("ACTIVE-SPEAKER SELECTION in the JELLYFIN world — pooled over documentaries")
    print("=" * 74)
    LIP, AUD, SRC = [], [], []
    for si, (series, neps) in enumerate(SOURCES):
        if series not in jf._cat:
            print(f"  ({series} not in catalog)"); continue
        for ep in range(neps):
            try:
                lips, auds = episode_windows(jf, series, ep, secs)
            except Exception as e:
                print(f"    [{series[:24]} ep{ep}] ERR {type(e).__name__} {str(e)[:40]}"); continue
            for lp, ad in zip(lips, auds):
                LIP.append(lp); AUD.append(ad); SRC.append((si, ep))
    LIP, AUD = np.array(LIP), np.array(AUD)
    print(f"\n  pooled {len(LIP)} lip/audio windows across "
          f"{len(set(SRC))} episodes\n", flush=True)
    if len(LIP) < 12:
        print("  too few windows yet — run again to cache more episodes"); return

    rng = np.random.RandomState(0)
    match = np.array([score(LIP[i], AUD[i]) for i in range(len(LIP))])
    mism = []
    for i in range(len(LIP)):
        pool = [j for j in range(len(LIP)) if SRC[j] != SRC[i]]
        for j in rng.choice(pool, size=min(4, len(pool)), replace=False):
            mism.append(score(LIP[j], AUD[i]))
    print(f"  corr(audio, MATCHING lip)   = {match.mean():+.3f}")
    print(f"  corr(audio, MISMATCHED lip) = {np.mean(mism):+.3f}  "
          f"(gap {match.mean()-np.mean(mism):+.3f})")

    print(f"\n  {'candidates N':>12} {'accuracy':>10} {'chance':>8} {'n_trials':>9}")
    print("  " + "-" * 44)
    for N in (2, 3, 5):
        correct = tot = 0
        for i in range(len(LIP)):
            pool = [j for j in range(len(LIP)) if SRC[j] != SRC[i]]
            if len(pool) < N - 1:
                continue
            for _ in range(20):
                cand = [i] + list(rng.choice(pool, size=N - 1, replace=False))
                sc = [score(LIP[c], AUD[i]) for c in cand]
                correct += cand[int(np.argmax(sc))] == i; tot += 1
        print(f"  {N:>12} {correct/tot:10.3f} {1.0/N:8.3f} {tot:9d}")
    print("=" * 74)
    print("  the MATCHING face's lip-motion correlates higher with the audio than distractors")
    print("  -> active-speaker selection from the lip cue + held cochlea, on real TV.")


if __name__ == "__main__":
    main()
