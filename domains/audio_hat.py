"""audio_hat — the EXISTING audio sense behind the Hat interface.

This is the Phase-A/B/C audio, unchanged in substance, exposed as a swappable
sense-hat for the universal CortexLoop:

  · encode(raw=(x, fs))    -> cmvn cochleagram trajectory (learned_voice_shape,
                              empty library = per-utterance CMVN). The agent's OWN
                              front end, the SAME feature the DtwTo recognizer reads.
  · synth(word, voice)     -> the espeak-ng voicebox the agent CONTROLS and HEARS,
                              re-rendered to the same cmvn trajectory. The forward
                              model; never inverted by a net, only re-voiced.
  · compare(a, b)          -> the agent's graph-resident DtwTo, evaluated natively
                              in Rust (no net, no fit). The loop's residual.

Style = the voice V (variant x pitch x rate), derived from the agent's own VTL /
pitch / rate knowledge. The coarse-to-fine style_neighbours reproduce Phase-C's
coordinate descent (pitch & rate continuous axes + the vocal-tract variant
hill-climb). Producing the SAME Phase-C audio number through the general loop is the
no-regression check.

The KNOWN limitation (commit da783064, REFUTED "mouth is the wall"): the audio
compare carries a synthetic-vs-real DOMAIN GAP — espeak-rendered candidates vs real
SC recordings — so the true-word residual barely separates from wrong-word. That
gap lives ENTIRELY in this hat's compare/synth, NOT in the cortex loop. The clean
toy hat (no domain gap) is the control that quarantines it.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import wave
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np

from domains.hat import Hat
from domains.fuzzy_smooth import smooth_traj
import domains.learned_voice_shape as LVS
from scripts.dtw_trajectory_loso import (
    _Pred, _V, _Attr, _DtwTo, _traj_tuple,
    QUERY_NODE_TYPE, QUERY_TRAJ_ATTR, EX_TRAJ_ATTR)

_DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven",
           "eight", "nine"]


def _espeak_variants() -> List[str]:
    """Named voice variants espeak-ng ships (en+<variant>) — the vocal-tract pool."""
    try:
        out = subprocess.run(["espeak-ng", "--voices=variant"],
                             capture_output=True, text=True, check=True).stdout
    except Exception:
        return []
    vs = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 5 and parts[4].startswith("!v/"):
            vs.append(parts[4].split("/", 1)[1])
    return vs


class AudioHat(Hat):
    """The existing audio sense as a Hat. Holds a substrate for the native DtwTo
    compare + scratch nodes + a synth cache. Style = voice dict {variant,pitch,rate}."""

    name = "audio"

    def __init__(self, substrate, fs: int, grid: int = 60, seed: int = 20240610,
                 words: List[str] = None, smooth_t: float = 0.0, smooth_f: float = 0.0,
                 whiten: "np.ndarray" = None):
        self.s = substrate
        self.fs = int(fs)
        self.words = list(words) if words else list(_DIGITS)
        # WHITENED MATCHED FILTER (signal-from-noise). `whiten` is a (bands x bands)
        # matrix W = S_n^{-1/2} estimated on TRAIN real speakers (the within-word /
        # word-INDEPENDENT nuisance covariance = speaker + residual domain gap). When
        # set, each smoothed frame vector is mapped f -> f @ W.T BEFORE the trajectory
        # is formed, so the loop's unchanged DtwTo (Euclidean per-frame inside DTW)
        # computes the Mahalanobis residual ||W(a - b)|| — down-weighting the
        # high-nuisance directions. Owned linear algebra (no net, no fit, no gradient);
        # fit on TRAIN only and applied identically to held-out (no leakage). The
        # CortexLoop and the Rust DtwTo are untouched; whitening lives only here, in the
        # hat's encode/synth, exactly like the smoothing.
        self.whiten = None if whiten is None else np.asarray(whiten, dtype=np.float64)
        # FUZZY compare: blur the cmvn cochleagram over time (sigma frames) x freq
        # (sigma bands) before the DtwTo residual. 0/0 == the rigid (un-smoothed)
        # compare. Freq-blur tolerates the synthetic-vs-real SPECTRAL grain (the
        # domain gap); time-blur tolerates rate/alignment jitter. Swept to find the
        # scale that shrinks the gap without erasing the word.
        self.smooth_t = float(smooth_t)
        self.smooth_f = float(smooth_f)
        self.variants = _espeak_variants()
        self._resid_term = _Pred(_DtwTo(_Attr(_V("q"), QUERY_TRAJ_ATTR),
                                        _Attr(_V("c"), EX_TRAJ_ATTR)))
        self.qn = substrate.add_node(QUERY_NODE_TYPE, {"origin": "audiohat_q"})
        self.cn = substrate.add_node("AudioHatCand", {"origin": "audiohat_c"})
        self._cache: Dict[Tuple, Any] = {}
        self._library: List[Tuple[str, Dict[str, Any], Any]] = []
        self._build_library(grid, seed)

    # ---- the three core methods ----
    def _smooth(self, feats):
        """FUZZY: blur the (frames x bands) residual cochleagram over time x freq
        before it becomes the DtwTo trajectory. Owned DSP (Gaussian), no net. 0/0
        scales -> pass-through (the rigid compare)."""
        if not feats or (self.smooth_t <= 0 and self.smooth_f <= 0):
            return feats
        a = np.asarray(feats, dtype=np.float64)
        if a.ndim != 2:
            return feats
        a = smooth_traj(a, self.smooth_t, self.smooth_f)
        return [list(map(float, row)) for row in a]

    def _features(self, feats):
        """Smooth then (optionally) WHITEN each frame vector. The whitening maps every
        per-frame band vector f -> W f (W = S_n^{-1/2}), so the loop's unchanged DtwTo
        — a Euclidean per-frame distance inside the DTW alignment — becomes the
        Mahalanobis whitened matched filter ||W(a-b)||. Owned linear algebra; identical
        on encode (real held-out) and synth (candidates). No frame-count change, so DTW
        alignment is untouched."""
        sm = self._smooth(feats)
        if self.whiten is None or not sm:
            return sm
        a = np.asarray(sm, dtype=np.float64)
        if a.ndim != 2 or a.shape[1] != self.whiten.shape[0]:
            return sm
        w = a @ self.whiten.T                      # (frames x bands) f -> W f per frame
        return [list(map(float, row)) for row in w]

    def encode(self, raw: Tuple[Any, float]) -> Any:
        x, fs = raw
        feats = LVS.residual_track(np.asarray(x, dtype=np.float64), float(fs), [])
        return _traj_tuple(self._features(feats))

    def synth(self, word: str, voice: Dict[str, Any]) -> Any:
        key = (word, voice["variant"], int(round(voice["pitch"])),
               int(round(voice["rate"])))
        f = self._cache.get(key)
        if f is not None:
            return f if f else None
        feats = self._espeak(word, key[1], key[2], key[3])
        traj = _traj_tuple(self._features(feats)) if feats else None
        self._cache[key] = traj if traj is not None else []
        return traj

    def compare(self, a: Any, b: Any) -> float:
        if a is None or b is None:
            return float("inf")
        self.s.set_attr(self.qn, QUERY_TRAJ_ATTR, a)
        self.s.set_attr(self.cn, EX_TRAJ_ATTR, b)
        d = self.s.evaluate(self._resid_term, {"q": self.qn, "c": self.cn})
        return float(d) if d is not None else float("inf")

    # ---- search scaffolding ----
    def contents(self):
        return self.words

    def style_init(self) -> Dict[str, Any]:
        v = self.variants[0] if self.variants else "m1"
        return {"variant": v, "pitch": 50, "rate": 160}

    def n_stages(self) -> int:
        return 2

    def style_neighbours(self, style: Dict[str, Any], stage: int) -> Iterable[Dict[str, Any]]:
        pitch_steps = [20, 8]
        rate_steps = [25, 10]
        ps, rs = pitch_steps[stage], rate_steps[stage]
        out = []
        for dp in (ps, -ps):
            c = dict(style); c["pitch"] = min(99, max(0, style["pitch"] + dp))
            if c["pitch"] != style["pitch"]:
                out.append(c)
        for dr in (rs, -rs):
            c = dict(style); c["rate"] = min(300, max(80, style["rate"] + dr))
            if c["rate"] != style["rate"]:
                out.append(c)
        if self.variants:
            vidx = (self.variants.index(style["variant"])
                    if style["variant"] in self.variants else 0)
            for dv in (1, -1):
                ni = (vidx + dv) % len(self.variants)
                c = dict(style); c["variant"] = self.variants[ni]
                out.append(c)
        return out

    def library(self):
        return self._library

    def close(self):
        self.s.remove_node(self.qn)
        self.s.remove_node(self.cn)

    # ---- world I/O: espeak voicebox ----
    def _espeak(self, word: str, variant: str, pitch: int, rate: int):
        with tempfile.TemporaryDirectory() as d:
            raw = os.path.join(d, "r.wav")
            out = os.path.join(d, "o.wav")
            subprocess.run(["espeak-ng", "-v", f"en+{variant}", "-p", str(pitch),
                            "-s", str(rate), "-w", raw, word],
                           check=True, capture_output=True)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw,
                            "-ar", str(self.fs), "-ac", "1", "-sample_fmt", "s16", out],
                           check=True, capture_output=True)
            with wave.open(out, "rb") as wv:
                x = (np.frombuffer(wv.readframes(wv.getnframes()), dtype=np.int16)
                     .astype(np.float64) / 32768.0)
        if x.size == 0:
            return None
        return LVS.residual_track(x, float(self.fs), [])

    def _build_library(self, grid: int, seed: int):
        import random
        rng = random.Random(seed)
        if not self.variants:
            return
        pitch_grid = [20, 40, 60, 80, 99]
        rate_grid = [130, 160, 190]
        combos = [(v, p, r) for v in self.variants for p in pitch_grid for r in rate_grid]
        rng.shuffle(combos)
        voices = [{"variant": v, "pitch": p, "rate": r} for (v, p, r) in combos[:grid]]
        for w in self.words:
            for v in voices:
                traj = self.synth(w, v)
                if traj is not None:
                    self._library.append((w, dict(v), traj))
