"""SPEECH ACCENT ARCHIVE (accent.gmu.edu) extraction — REAL per-word-aligned accented corpus.

Every speaker in the Speech Accent Archive reads the SAME fixed elicitation paragraph ("Please
call Stella...") regardless of native language / accent, so the SAME WORD is directly comparable
across a native-English reference group and five L1-accent groups (spanish, mandarin, russian,
arabic, korean) — no synthetic accent injection needed, this is the real thing.

Audio was pre-downloaded (curl, public domain / cited academic corpus, license: research reuse
per accent.gmu.edu) to $SCRATCH/saa_audio/<group>/<slug>.mp3, 38 speakers total (8 native-English-
US reference + 6 speakers each of 5 L1 accent groups). NEVER commit the audio itself.

ISOLATED torch subprocess (MMS_FA, bootstrap/eval-only, same discipline as
apc_context_predictive_frontend.py): force-align each speaker's audio against the FIXED KNOWN
TRANSCRIPT (identical text -> the SAME word list every time, so this is an easier/more reliable
alignment than free transcription) -> per-word (start,end) spans. Then the Rust ear
(`nat.cochleagram`) renders the WHOLE utterance to a 32-band cochleagram at 100fps, natively at
the source sample rate (no resampling needed for the cochleagram; resampling to 16kHz is only
for the wav2vec2/MMS_FA alignment step, which expects 16kHz).

Cache format (mirrors apc_libri_uttframes.pkl exactly so downstream code reuses the same tuple
shape): list of (coch[Tu,32] float16, [(word,f0,f1)], "group:slug", group_name).

Run (extract only, isolated torch):
  /home/matt/ozma/internal/research/.venv/bin/python scripts/saa_corpus_extract.py --extract
"""
from __future__ import annotations
import os, sys, json, glob, pickle, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(ROOT, "runners", "dsl", "python"), ROOT, os.path.join(ROOT, "scripts")):
    if p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)

SCRATCH = os.environ.get(
    "SCRATCH",
    "/tmp/claude-1000/-home-matt-ozma-internal-research-experiments-gamma-substrate/"
    "3ed12bb3-7b58-44c0-b051-98640926c040/scratchpad")
AUDIO_DIR = os.path.join(SCRATCH, "saa_audio")
MANIFEST = os.path.join(SCRATCH, "saa_manifest.json")
CACHE = os.path.join(SCRATCH, "saa_corpus_uttframes.pkl")
FPS = 100.0

# The FIXED elicitation paragraph, IDENTICAL for every Speech Accent Archive speaker.
STELLA_TEXT = (
    "Please call Stella. Ask her to bring these things with her from the store: "
    "Six spoons of fresh snow peas, five thick slabs of blue cheese, and maybe a "
    "snack for her brother Bob. We also need a small plastic snake and a big toy "
    "frog for the kids. She can scoop these things into three red bags, and we "
    "will go meet her Wednesday at the train station."
)


def _extract():
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (10 * 1024 ** 3, 10 * 1024 ** 3))
    import torch
    torch.set_num_threads(os.cpu_count() or 4)
    import torchaudio
    from torchaudio.pipelines import MMS_FA as B
    from scripts.librispeech_wer import load_flac   # av-based decoder, works on mp3 too
    from substrate_rs import _native as nat

    m, tok, aln = B.get_model(), B.get_tokenizer(), B.get_aligner()
    ALIGN_SR = 16000

    words = [re.sub(r"[^a-z]", "", w.lower()) for w in STELLA_TEXT.split()]
    words = [w for w in words if w]

    def align_utt(x, fs):
        """Resample a COPY to 16kHz for MMS_FA (wav2vec2 requirement); cochleagram uses the
        original-rate audio directly (no resample needed there)."""
        wav = torch.tensor(x, dtype=torch.float32).unsqueeze(0)
        if fs != ALIGN_SR:
            wav = torchaudio.functional.resample(wav, fs, ALIGN_SR)
        try:
            with torch.inference_mode():
                emission, _ = m(wav)
                spans = aln(emission[0], tok(words))
        except Exception as e:
            print(f"    align FAILED: {e}", flush=True)
            return []
        ratio = wav.size(1) / emission.size(1)
        return [(w, sp[0].start * ratio / ALIGN_SR, sp[-1].end * ratio / ALIGN_SR)
                for w, sp in zip(words, spans)]

    mf = json.load(open(MANIFEST))
    out = []
    for group, spks in mf.items():
        n = 0
        for sp in spks:
            slug = sp["slug"]
            path = os.path.join(AUDIO_DIR, group, slug + ".mp3")
            if not os.path.exists(path):
                print(f"  [extract] MISSING {path}", flush=True)
                continue
            x, fs = load_flac(path)
            x = np.asarray(x, np.float32)
            spans = align_utt(x, fs)
            if not spans:
                continue
            dur = len(x) / fs
            nfr = max(4, int(round(dur * FPS)))
            flat = nat.cochleagram(x, int(fs), 50.0, 80.0, nfr)
            coch = np.asarray(flat, np.float32).reshape(nfr, 32).astype(np.float16)
            wspans = []
            for (w, t0, t1) in spans:
                if not (w.isalpha() and len(w) >= 2 and (t1 - t0) >= 0.04):
                    continue
                f0 = max(0, int(t0 * FPS)); f1 = min(nfr, int(t1 * FPS))
                if f1 - f0 >= 2:
                    wspans.append((w, f0, f1))
            if wspans:
                out.append((coch, wspans, f"{group}:{slug}", group))
                n += 1
        print(f"  [extract] {group}: {n}/{len(spks)} speakers aligned (total {len(out)})", flush=True)
    pickle.dump(out, open(CACHE, "wb"))
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2
    print(f"  [extract] wrote {len(out)} utts -> {CACHE} [peak {peak:.2f} GiB]", flush=True)


import numpy as np

if __name__ == "__main__":
    if "--extract" in sys.argv:
        _extract()
    else:
        print("usage: saa_corpus_extract.py --extract")
