"""BABBLE PRODUCER — the agent CHOOSES a word repertoire and PRODUCES it as CONNECTED speech.

This is the "bone-conduction" forward model: a controllable, realistic synth (XTTS, many speaker
voices) produces clean audio for KNOWN text -> the phone labels are FREE+EXACT (the agent chose the
words; the CMU pronunciation is the per-word phone target).

CONNECTED SPEECH (not isolated words): each repertoire word is embedded in a CARRIER sentence so it
is produced at a natural connected-speech rate with real coarticulation, then MMS_FA force-aligns the
KNOWN carrier text and the target word's span is extracted. (Isolated-word synthesis nulled: XTTS
says a lone word ~5x slower than a connected-speech word segment -> a timescale mismatch that breaks
the context+delta feature. Carrier extraction matches the real LibriSpeech word-segment pipeline.)

DATA PRODUCER (a world-side scaffold, like a teacher during bootstrap), NOT the agent. The learned
recogniser (scripts/babble_transfer.py) runs with 0 XTTS/piper/MMS calls at inference. MMS_FA only
provides WORD boundaries for the KNOWN carrier text (the labeller), like the phonebank pipeline; the
agent's per-phone labels come from its own EM/Viterbi over the known phone sequence.

Conditions written (16 kHz mono wav, <word>__<tag>.wav):
  xtts/   : each word, connected speech, MANY XTTS speaker voices  (strong, realistic synth)
  piper/  : each word, connected speech, one piper voice           (WEAK-synth control)

Run (XPU venv on the B580):
  /home/matt/babble_work/xpuvenv/bin/python scripts/babble_synth.py [instances_per_word]
"""
import os
import re
import sys
import time

import numpy as np
import soundfile as sf

OUT = os.environ.get("BABBLE_OUT", "/home/matt/babble_work/babble")
FS = 16000

VOCAB = [
    "water", "because", "yellow", "through", "around", "people", "father", "mother",
    "number", "letter", "morning", "evening", "country", "machine", "picture", "nature",
    "second", "answer", "follow", "common", "reason", "season", "window", "summer",
    "winter", "garden", "market", "doctor", "teacher", "farmer", "writer", "singer",
    "danger", "finger", "hunger", "anger", "color", "honor", "labor", "favor",
    "ocean", "music", "money", "honey", "study", "story", "early", "happy",
    "city", "body", "lady", "baby", "ready", "heavy", "every", "carry",
    "value", "issue", "voice", "noise", "house", "mouse", "horse", "force",
    "place", "space", "price", "piece", "peace", "choice", "juice", "bridge",
    "judge", "change", "charge", "large", "strange", "orange", "village", "thought",
    "though", "throw", "three", "thank", "think", "thing", "shadow", "shower",
    "should", "shoulder", "fashion", "passion", "mission", "nation", "measure", "treasure",
    "pleasure", "leisure", "vision", "decision", "occasion", "usual", "quick", "queen",
    "quiet", "square", "language", "question", "require", "equal", "yesterday", "young",
    "beyond", "lawyer", "loyal", "royal", "enjoy", "between", "beneath", "beside",
    "behind", "before", "again", "agree", "alone", "almost", "always", "animal",
    "family", "memory", "history", "company", "energy",
]
VOCAB = list(dict.fromkeys(VOCAB))

# carrier sentences (the target word goes at {w}); varied left/right context -> coarticulation
CARRIERS = [
    "i said the {w} again",
    "we saw a {w} today",
    "he told me about the {w} once",
    "there is a {w} over there",
    "she will keep the {w} for now",
    "they found another {w} nearby",
]


def _resample_to_16k(x, sr):
    if sr == FS:
        return x.astype(np.float32)
    from math import gcd
    g = gcd(sr, FS)
    try:
        from scipy.signal import resample_poly
        return resample_poly(x, FS // g, sr // g).astype(np.float32)
    except Exception:
        n = int(round(len(x) * FS / sr))
        return np.interp(np.linspace(0, 1, n), np.linspace(0, 1, len(x)), x).astype(np.float32)


class Aligner:
    """MMS_FA word force-aligner — the labeller for the KNOWN carrier text (word boundaries only)."""
    def __init__(self):
        import torch
        from torchaudio.pipelines import MMS_FA as B
        self.torch = torch
        self.m, self.tok, self.aln = B.get_model(), B.get_tokenizer(), B.get_aligner()

    def word_span(self, x16k, carrier_words, target_idx):
        torch = self.torch
        wav = torch.tensor(np.asarray(x16k), dtype=torch.float32).unsqueeze(0)
        try:
            with torch.inference_mode():
                emission, _ = self.m(wav)
                spans = self.aln(emission[0], self.tok(carrier_words))
        except Exception:
            return None
        ratio = wav.size(1) / emission.size(1)
        sp = spans[target_idx]
        t0 = sp[0].start * ratio / FS
        t1 = sp[-1].end * ratio / FS
        a, b = int(max(0, t0) * FS), int(min(len(x16k), t1) * FS)
        if b - a < int(0.05 * FS):
            return None
        return x16k[a:b]


def synth_xtts(instances, aligner):
    import torch
    os.environ["COQUI_TOS_AGREED"] = "1"
    import torchaudio
    def _load(p, *a, **k):
        x, sr = sf.read(str(p), dtype="float32"); x = x[None, :] if x.ndim == 1 else x.T
        return torch.from_numpy(np.ascontiguousarray(x)), sr
    def _save(p, t, sr, *a, **k):
        arr = t.detach().cpu().numpy(); arr = arr.T if arr.ndim == 2 else arr; sf.write(str(p), arr, sr)
    torchaudio.load = _load; torchaudio.save = _save
    from TTS.api import TTS
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False)
    dev = "cpu"
    try:
        tts = tts.to("xpu"); dev = "xpu"
    except Exception:
        pass
    allspk = tts.synthesizer.tts_model.speaker_manager.speaker_names
    sel = [allspk[i] for i in np.linspace(0, len(allspk) - 1, max(2, instances)).astype(int)]
    d = os.path.join(OUT, "xtts"); os.makedirs(d, exist_ok=True)
    print(f"  XTTS on {dev}: {len(VOCAB)} words x {instances} connected-speech instances "
          f"({len(sel)} speakers, {len(CARRIERS)} carriers)", flush=True)
    t0 = time.time(); n = 0; tmp = os.path.join(OUT, "_tmp.wav")
    for wi, w in enumerate(VOCAB):
        for k in range(instances):
            outp = os.path.join(d, f"{w}__s{k}.wav")
            if os.path.exists(outp):
                n += 1; continue
            carrier = CARRIERS[(wi + k) % len(CARRIERS)]
            spk = sel[k % len(sel)]
            words = carrier.format(w=w).split()
            tgt = words.index(w)
            try:
                tts.tts_to_file(text=carrier.format(w=w) + ".", speaker=spk, language="en", file_path=tmp)
                x, sr = sf.read(tmp, dtype="float32")
                if x.ndim > 1:
                    x = x.mean(1)
                x16 = _resample_to_16k(x, sr)
                seg = aligner.word_span(x16, words, tgt)
                if seg is None:
                    continue
                sf.write(outp, seg, FS); n += 1
            except Exception as e:
                print(f"    [skip] {w} k{k}: {str(e)[:60]}", flush=True)
        if (wi + 1) % 20 == 0:
            print(f"    {wi+1}/{len(VOCAB)} words, {n} clips, {time.time()-t0:.0f}s", flush=True)
    print(f"  XTTS done: {n} clips in {time.time()-t0:.0f}s", flush=True)


def synth_piper(instances, aligner):
    import wave
    from piper import PiperVoice
    v = PiperVoice.load("/home/matt/babble_work/piper_voices/en_US-lessac-medium.onnx")
    d = os.path.join(OUT, "piper"); os.makedirs(d, exist_ok=True)
    print(f"  PIPER (weak-synth control): {len(VOCAB)} words x {instances} connected-speech instances", flush=True)
    t0 = time.time(); n = 0; tmp = os.path.join(OUT, "_tmpp.wav")
    for wi, w in enumerate(VOCAB):
        for k in range(instances):
            outp = os.path.join(d, f"{w}__p{k}.wav")
            if os.path.exists(outp):
                n += 1; continue
            carrier = CARRIERS[(wi + k) % len(CARRIERS)]
            words = carrier.format(w=w).split()
            tgt = words.index(w)
            try:
                with wave.open(tmp, "wb") as wf:
                    v.synthesize_wav(carrier.format(w=w) + ".", wf)
                x, sr = sf.read(tmp, dtype="float32")
                if x.ndim > 1:
                    x = x.mean(1)
                x16 = _resample_to_16k(x, sr)
                seg = aligner.word_span(x16, words, tgt)
                if seg is None:
                    continue
                sf.write(outp, seg, FS); n += 1
            except Exception as e:
                print(f"    [skip] {w} k{k}: {str(e)[:60]}", flush=True)
    print(f"  PIPER done: {n} clips in {time.time()-t0:.0f}s", flush=True)


def main():
    instances = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    os.makedirs(OUT, exist_ok=True)
    aligner = Aligner()
    synth_xtts(instances, aligner)
    synth_piper(max(2, instances // 2 + 1), aligner)
    print("BABBLE PRODUCED ->", OUT)


if __name__ == "__main__":
    main()
