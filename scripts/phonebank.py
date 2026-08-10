"""PERSISTENT PHONE BANK via FORCED ALIGNMENT — feed the beast, the better way.

Whisper-recognise was the bottleneck (slow) AND gave noisy boundaries. LibriSpeech ships transcripts, so we
FORCE-ALIGN audio to the KNOWN text (torchaudio MMS_FA) -- ~13x real-time on CPU, cleaner word boundaries, no
GPU. Like whisper, the aligner is a help-button LABELLER for banking; the agent's recognition stays its own
cochleagram+DTW. Cache (word, frames32, phones) per word so context units rebuild from the accumulated cache.

  feed <corpus_dir> <max_utts> <is_dev 0|1>   -- force-align a corpus, append phone material to the cache.
  measure                                      -- load all cached words, build triphone back-off units, read the
                                                 held-out targets, report mono vs context top-3.

Run:
  PYTHONPATH=.:runners/dsl/python python -u -m scripts.phonebank feed /home/matt/data/LibriSpeech/dev-clean 3000 1
  PYTHONPATH=.:runners/dsl/python python -u -m scripts.phonebank feed /home/matt/data/LibriSpeech/train-clean-100 30000 0
  PYTHONPATH=.:runners/dsl/python python -u -m scripts.phonebank measure
"""
from __future__ import annotations

import glob
import os
import pickle
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import torch
torch.set_num_threads(os.cpu_count() or 4)
from scripts.librispeech_wer import load_flac
from scripts.jabberwock_reads_oov_from_phones import frames, phones, dtw, STOP, FS, N_TARGET
from scripts.jabberwock_context_units import medoid, pick

DATA = "/home/matt/data/LibriSpeech"
DEV = os.path.join(DATA, "dev-clean")
CACHE = "/home/matt/data/phonebank"
os.makedirs(CACHE, exist_ok=True)
META = os.path.join(CACHE, "meta.pkl")
_AL = {}


def aligner():
    if not _AL:
        from torchaudio.pipelines import MMS_FA as B
        _AL["m"], _AL["t"], _AL["a"] = B.get_model(), B.get_tokenizer(), B.get_aligner()
    return _AL["m"], _AL["t"], _AL["a"]


def _transcripts(d):
    """word-id -> transcript for every chapter dir under d."""
    tr = {}
    for tf in glob.glob(os.path.join(d, "**", "*.trans.txt"), recursive=True):
        for line in open(tf):
            line = line.strip()
            if " " in line:
                k, v = line.split(" ", 1)
                tr[k] = v
    return tr


def align_utt(audio, fs, transcript):
    """force-align -> [(clean_word, t0, t1)] for words that are alpha + in CMUdict."""
    m, tok, aln = aligner()
    words = [re.sub(r"[^a-z]", "", w.lower()) for w in transcript.split()]
    keep = [(i, w) for i, w in enumerate(words) if w]
    if not keep:
        return []
    wav = torch.tensor(np.asarray(audio), dtype=torch.float32).unsqueeze(0)
    try:
        with torch.inference_mode():
            emission, _ = m(wav)
            spans = aln(emission[0], tok([w for _i, w in keep]))
    except Exception:
        return []
    ratio = wav.size(1) / emission.size(1)
    out = []
    for (_i, w), sp in zip(keep, spans):
        out.append((w, sp[0].start * ratio / fs, sp[-1].end * ratio / fs))
    return out


def _meta():
    if os.path.exists(META):
        return pickle.load(open(META, "rb"))
    flacs = sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True))
    tr = _transcripts(DEV)
    test_spk = sorted({os.path.basename(f).split("-")[0] for f in flacs})[-3:]
    tw, clips = Counter(), []
    for f in flacs:
        sp = os.path.basename(f).split("-")[0]
        if sp not in test_spk:
            continue
        base = os.path.basename(f)[:-5]
        if base not in tr:
            continue
        x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64)
        for (w, t0, t1) in align_utt(x, fs, tr[base]):
            ph = phones(w)
            if len(w) >= 3 and ph and w not in STOP and len(ph) >= 3:
                tw[w] += 1
    targets = [w for (w, _c) in tw.most_common(N_TARGET)]; tset = set(targets)
    for f in flacs:
        sp = os.path.basename(f).split("-")[0]
        if sp not in test_spk:
            continue
        base = os.path.basename(f)[:-5]
        if base not in tr:
            continue
        x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64)
        for (w, t0, t1) in align_utt(x, fs, tr[base]):
            if w in tset:
                seg = x[int(t0 * fs):int(t1 * fs)]
                if seg.size >= int(0.05 * fs):
                    clips.append((w, frames(seg)[0].astype(np.float32)))
    meta = (set(test_spk), targets, clips)
    pickle.dump(meta, open(META, "wb"))
    print(f"  meta: {len(targets)} targets, {len(clips)} test clips, test speakers {sorted(test_spk)}", flush=True)
    return meta


def feed(corpus_dir, max_utts, is_dev):
    test_spk, targets, _clips = _meta(); tset = set(targets)
    name = os.path.basename(corpus_dir.rstrip("/"))
    chunk = len(glob.glob(os.path.join(CACHE, f"{name}_*.pkl")))
    tr = _transcripts(corpus_dir)
    flacs = sorted(glob.glob(os.path.join(corpus_dir, "**", "*.flac"), recursive=True))
    print(f"  feeding {name}: {len(flacs)} flacs, {chunk} chunks cached, max {max_utts} utts (forced-align)", flush=True)
    buf, done = [], 0
    for f in flacs:
        sp = os.path.basename(f).split("-")[0]
        if is_dev and sp in test_spk:
            continue
        base = os.path.basename(f)[:-5]
        if base not in tr:
            continue
        try:
            x, fs = load_flac(f)
        except Exception:
            continue
        x = np.asarray(x, dtype=np.float64)
        for (w, t0, t1) in align_utt(x, fs, tr[base]):
            ph = phones(w)
            if not ph or w in tset:
                continue
            seg = x[int(t0 * fs):int(t1 * fs)]
            if seg.size >= int(0.05 * fs):
                fr, en = frames(seg)   # fr = L2-normalised shape; en = per-frame energy (default-path channel)
                # ADDITIVE 4th element: energy. 3-tuple readers (_load_ph default) ignore it,
                # the energy-augmented default phone model (_load_ph with_energy=True) reads it.
                buf.append((w, fr.astype(np.float32), ph, en.astype(np.float32)))
        done += 1
        if len(buf) >= 4000:
            pickle.dump(buf, open(os.path.join(CACHE, f"{name}_{chunk}.pkl"), "wb"))
            print(f"  [{name}] {done}/{max_utts} utts, chunk {chunk} ({len(buf)} words) saved", flush=True)
            chunk += 1; buf = []
        if done >= max_utts:
            break
    if buf:
        pickle.dump(buf, open(os.path.join(CACHE, f"{name}_{chunk}.pkl"), "wb"))
    print(f"  DONE feeding {name}: {done} utts", flush=True)


def _build(words):
    tri, rbi, lbi, mono = {}, {}, {}, {}
    for (_w, fr, ph) in words:
        nf = len(fr); cuts = np.linspace(0, nf, len(ph) + 1).astype(int)
        for i in range(len(ph)):
            if cuts[i + 1] <= cuts[i]:
                continue
            L = ph[i - 1] if i > 0 else "#"; R = ph[i + 1] if i < len(ph) - 1 else "#"
            sub = fr[cuts[i]:cuts[i + 1]]
            tri.setdefault((L, ph[i], R), []).append(sub)
            rbi.setdefault((ph[i], R), []).append(sub)
            lbi.setdefault((L, ph[i]), []).append(sub)
            mono.setdefault(ph[i], []).append(sub)
    g = lambda b: {k: medoid(v) for k, v in b.items() if len(v) >= 2}
    return g(tri), g(rbi), g(lbi), g(mono)


def measure():
    _ts, targets, clips = _meta()
    chunks = sorted(glob.glob(os.path.join(CACHE, "*_*.pkl")))
    words = []
    for c in chunks:
        words += pickle.load(open(c, "rb"))
    print(f"  loaded {len(words)} banked words from {len(chunks)} chunks; building context units...", flush=True)
    Tri, Rbi, Lbi, Mono = _build(words)

    def read(cf, ctx):
        best = {}
        for w in targets:
            ph = phones(w); parts = []; ok = True
            for i in range(len(ph)):
                L = ph[i - 1] if i > 0 else "#"; R = ph[i + 1] if i < len(ph) - 1 else "#"
                m = pick(L, ph[i], R, Tri, Rbi, Lbi, Mono)[0] if ctx else Mono.get(ph[i])
                if m is None:
                    ok = False; break
                parts.append(m)
            if ok:
                best[w] = dtw(cf, np.concatenate(parts, axis=0))
        return sorted(best, key=best.get)

    m3 = c3 = tot = reach = sl = 0
    for (w, cf) in clips:
        cf = np.asarray(cf, dtype=np.float32)
        rm, rc = read(cf, False), read(cf, True)
        tot += 1; m3 += int(w in rm[:3]); c3 += int(w in rc[:3])
        ph = phones(w)
        for i in range(len(ph)):
            L = ph[i - 1] if i > 0 else "#"; R = ph[i + 1] if i < len(ph) - 1 else "#"
            sl += 1; reach += int((L, ph[i], R) in Tri)
    print("=" * 84)
    print(f"  {len(words)} banked words | {len(Tri)} triphone buckets | {tot} held-out target instances "
          f"(chance top-3 {3/max(len(targets),1)*100:.0f}%)")
    print(f"  monophone top-3: {m3/max(tot,1)*100:.0f}%   |   CONTEXT top-3: {c3/max(tot,1)*100:.0f}%   "
          f"|   triphone reach {reach/max(sl,1)*100:.0f}%")
    print("=" * 84)


def main():
    if len(sys.argv) >= 5 and sys.argv[1] == "feed":
        feed(sys.argv[2], int(sys.argv[3]), sys.argv[4] == "1")
    elif len(sys.argv) >= 2 and sys.argv[1] == "measure":
        measure()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
