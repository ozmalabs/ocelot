"""SESAME STREET SPEECH WORLD — a transport-controlled audio world over any Sesame Street
episode, built for the agent to LEARN SPEECH toward 100% (Sesame is engineered to teach it:
clear enunciation, direct address, deliberate REPETITION of a small vocabulary).

The world adapter (Python = I/O only, per CLAUDE.md) gives the agent:
  play(t0,t1)      — hear a selection (extract audio over HTTP; cochlea -> features)
  seek / rewind / stop — transport over the episode (study a hard bit again)
  whisper(t0,t1)   — the HELP BUTTON: a Whisper transcript (+ word timestamps) of a selection,
                     the supervision the agent asks for when it needs the answer.

The agent LEARNS: from Whisper-labelled words it grounds an acoustic exemplar per word (the held
cochlea SHAPE front-end = the cross-speaker lever), building a grounded word lexicon. It then
RECOGNISES held-out words by 1-NN over that lexicon (its own recogniser). Sesame's repetition
means the recurring words get many exemplars -> recognition climbs toward 100% on the studied
vocabulary. Metric: word accuracy / WER of the AGENT vs the Whisper reference.

Run: python scripts/sesame_speech_world.py [n_study_min] [episode_idx]
"""
from __future__ import annotations
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import re
import subprocess
import sys
import tempfile
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

import soundfile as sf
from scipy.signal import resample_poly

from scripts.jellyfin_world import JellyfinWorld
from substrate_rs import Substrate
from substrate_rs.speech import _audio

N_BANDS = 24
HOP, WIN = 240, 400      # held cochleagram framing @ 8kHz (30ms hop / 50ms window)


def _norm_word(w):
    return re.sub(r"[^a-z']", "", w.lower())


class SesameSpeechWorld:
    """transport + Whisper-help over one Sesame Street episode. Pure world adapter."""

    def __init__(self, episode_idx=0, model="base.en"):
        jf = JellyfinWorld().connect()
        cat = {it["name"]: it for it in jf.catalog(kinds=("Series",))}
        eps = jf.episodes(cat["Sesame Street"]["id"], limit=episode_idx + 1)
        self.ep = eps[episode_idx]
        self.url = jf.stream_url(self.ep["id"])
        self.duration = float(self.ep.get("runtime_s") or 0.0)
        self.pos = 0.0                                 # transport position (s)
        self.playing = False
        from faster_whisper import WhisperModel
        self._wm = WhisperModel(model, device="cpu", compute_type="int8")
        self.s = Substrate(); _audio.seed_audio_grammar(self.s)
        self.bank = _audio.cochlea(self.s, n_bands=N_BANDS, fs=8000)

    # ---- transport (the agent's controls) -------------------------------
    def seek(self, t):
        self.pos = max(0.0, min(t, self.duration)); return self.pos

    def rewind(self, dt=2.0):
        return self.seek(self.pos - dt)

    def stop(self):
        self.playing = False; return self.pos

    def _extract(self, t0, t1, sr=16000):
        """pull [t0,t1] of the episode's audio over HTTP as mono `sr` samples (no full download)."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = f.name
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{t0:.2f}", "-i", self.url,
                        "-map", "0:a:0", "-t", f"{max(0.1, t1 - t0):.2f}", "-ar", str(sr),
                        "-ac", "1", path], check=True)
        a, _ = sf.read(path); os.unlink(path)
        return a.astype(np.float64)

    def play(self, t0, t1):
        """HEAR a selection: returns the 8kHz audio (what the ear ingests). Advances transport."""
        self.playing = True; self.pos = t1
        a16 = self._extract(t0, t1, sr=16000)
        return resample_poly(a16, 8000, 16000)         # 8k for the held cochlea

    # ---- the HELP BUTTON ------------------------------------------------
    def whisper(self, t0, t1):
        """Whisper transcript of a selection with WORD timestamps (rel. to t0). The supervision
        the agent requests when it needs the answer."""
        path = None
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = f.name
        a16 = self._extract(t0, t1, sr=16000)
        sf.write(path, a16, 16000)
        segs, _ = self._wm.transcribe(path, language="en", word_timestamps=True)
        words = []
        for sg in segs:
            for w in (sg.words or []):
                nw = _norm_word(w.word)
                if nw:
                    words.append((nw, float(w.start), float(w.end)))
        os.unlink(path)
        return words

    # ---- held cochlea SHAPE feature for a word span ---------------------
    def _cochleagram(self, a8):
        buf = _audio.audio_from_array(self.s, a8, sample_rate=8000)
        arrs = []
        for r in _audio.a1_responses(self.s, buf, self.bank):
            a = _audio.audio_to_array(self.s, r).astype(np.float64)
            arrs.append(a.mean(1) if a.ndim > 1 else a)
        L = min(len(a) for a in arrs)
        nf = max(1, (L - WIN) // HOP + 1)
        M = np.zeros((nf, len(self.bank)))
        for fi in range(nf):
            sl = slice(fi * HOP, fi * HOP + WIN)
            for bi, a in enumerate(arrs):
                M[fi, bi] = np.sqrt(np.mean(a[sl] ** 2) + 1e-12)
        return M

    def word_feature(self, a8, wt0, wt1, T0=10):
        """SHAPE front-end (log-band minus per-frame mean = the formant FILTER), time-resampled
        and flattened — the cross-speaker word feature."""
        s0, s1 = int(wt0 * 8000), int(wt1 * 8000)
        seg = a8[max(0, s0):max(s0 + 800, s1)]
        M = self._cochleagram(seg)
        L = np.log(M + 1e-6); shape = L - L.mean(1, keepdims=True)
        idx = np.linspace(0, len(shape) - 1, T0).round().astype(int)
        return shape[idx].flatten()


def wer(ref, hyp):
    d = np.zeros((len(ref) + 1, len(hyp) + 1), int)
    d[:, 0] = np.arange(len(ref) + 1); d[0, :] = np.arange(len(hyp) + 1)
    for i in range(1, len(ref) + 1):
        for j in range(1, len(hyp) + 1):
            d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1,
                          d[i - 1, j - 1] + (ref[i - 1] != hyp[j - 1]))
    return d[len(ref), len(hyp)] / max(len(ref), 1)


def main():
    study_min = float(sys.argv[1]) if len(sys.argv) > 1 else 8.0
    ep_idx = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    w = SesameSpeechWorld(episode_idx=ep_idx)
    print("=" * 76)
    print(f"SESAME STREET SPEECH WORLD — '{w.ep['name']}' ({w.duration/60:.0f} min)")
    print(f"  transport: play/seek/rewind/stop; HELP = Whisper transcript on demand")
    print("=" * 76)

    # STUDY: walk the episode in chunks, ask the HELP BUTTON for the words, ground one acoustic
    # exemplar per word (the agent learning its vocabulary from Whisper-labelled Sesame speech).
    lex = defaultdict(list)
    chunk = 25.0
    study_end = min(study_min * 60, w.duration - 60)
    t = 30.0
    n_words = 0
    while t < study_end:
        words = w.whisper(t, t + chunk)
        if words:
            a8 = w.play(t, t + chunk)
            for word, wt0, wt1 in words:
                lex[word].append(w.word_feature(a8, wt0, wt1)); n_words += 1
        t += chunk
    vocab = {k: np.array(v) for k, v in lex.items() if len(v) >= 1}
    print(f"\n  STUDIED {study_end/60:.1f} min: {n_words} word tokens, "
          f"{len(vocab)} distinct words grounded")
    top = sorted(vocab.items(), key=lambda kv: -len(kv[1]))[:12]
    print("  most-repeated words (Sesame's deliberate repetition):")
    print("   ", ", ".join(f"{k}x{len(v)}" for k, v in top))

    # TEST: a HELD-OUT later stretch. The AGENT recognises each word (1-NN over its grounded
    # exemplars, restricted to words it has studied); Whisper is the reference.
    exX, exW = [], []
    for word, feats in vocab.items():
        for f in feats:
            exX.append(f / (np.linalg.norm(f) + 1e-9)); exW.append(word)
    exX = np.array(exX); exW = np.array(exW)

    correct = total = oov = 0
    ref_seq, hyp_seq = [], []
    t = study_end + 20
    test_end = min(study_end + 240, w.duration - 20)
    while t < test_end:
        words = w.whisper(t, t + chunk)
        if words:
            a8 = w.play(t, t + chunk)
            for word, wt0, wt1 in words:
                ref_seq.append(word)
                if word not in vocab:
                    oov += 1; hyp_seq.append("<oov>"); continue
                q = w.word_feature(a8, wt0, wt1); q = q / (np.linalg.norm(q) + 1e-9)
                pred = exW[int((exX @ q).argmax())]
                hyp_seq.append(pred)
                correct += (pred == word); total += 1
        t += chunk

    print(f"\n  TEST (held-out {(test_end-study_end)/60:.1f} min): {len(ref_seq)} reference words")
    print(f"  in-vocab word accuracy (agent vs Whisper) : {correct/max(total,1):.1%} "
          f"({correct}/{total})")
    print(f"  out-of-vocab (never studied)              : {oov} "
          f"({oov/max(len(ref_seq),1):.0%} of reference)")
    print(f"  overall WER (agent transcript vs Whisper) : {wer(ref_seq, hyp_seq):.1%}")
    print("=" * 76)
    print("  path to 100%: more study (Sesame repeats its vocabulary) shrinks OOV and sharpens")
    print("  the in-vocab exemplars; the HELP BUTTON grounds each new word the first time.")


if __name__ == "__main__":
    main()
