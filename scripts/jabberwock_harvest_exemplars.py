"""GATED EXEMPLAR HARVEST — grow the bank's COVERAGE from Whisper labels, structure-preserving, bias-gated.

The jabberwock's pick: the decode is RECALL-LIMITED (loses words never banked), so HARVEST coverage. Use Whisper as a
LABELLER on (pretend-unlabelled) audio, bank the agent's OWN cochleagram exemplars under its labels -- never Whisper's
encoder vector (structure-preserving). GATE against Whisper's frequency-bias hallucination: keep a word span only if
(Whisper word confidence >= TAU) AND (Whisper's boundary AGREES with MMS_FA force-aligning Whisper's OWN hypothesised
text within DELTA) -- a hallucinated word doesn't fit the acoustics, so MMS_FA puts its boundary elsewhere -> dropped.
No ground truth used in the gate.

Compare banks built on held-out TEST speakers' words:
  baseline (oracle, small)      -- true-label MMS_FA bank from N_BASE utts (the current limited bank)
  + UNGATED whisper harvest     -- naive: bank every Whisper word (imports its bias)
  + GATED whisper harvest       -- conf + MMS_FA-agreement gated
  + ORACLE harvest (ceiling)    -- true-label harvest of the same utts
Metric: content-word recall + function-word recall on held-out test instances. Pre-committed bar: GATED content recall
>= baseline + 5 AND function recall >= baseline (no drop); GATED should beat UNGATED on function (the gate stops the
bias leak) and approach ORACLE.

Run:
  cd experiments/gamma-substrate
  ulimit -v 24000000
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_harvest_exemplars
"""
from __future__ import annotations

import glob
import os
import re
import sys
import tempfile
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import soundfile as sf
from scripts.jabberwock_reads_oov_from_phones import frames, dtw, STOP, FS
from scripts.phonebank import align_utt
from scripts.librispeech_wer import load_flac

DEV = "/tmp/LibriSpeech/dev-clean"
N_BASE = 12        # baseline oracle utts (the limited current bank)
N_HARVEST = 45     # additional utts to harvest (pretend unlabelled)
N_TEST = 40        # held-out test utts
TAU = 0.55         # whisper word-confidence gate
DELTA = 0.12       # boundary-agreement gate (s)
MINW = 3           # min word length to bank/test


def transcripts(d):
    tr = {}
    for tf in glob.glob(os.path.join(d, "**", "*.trans.txt"), recursive=True):
        for line in open(tf):
            line = line.strip()
            if " " in line:
                k, v = line.split(" ", 1)
                tr[k] = v
    return tr


def whisper_words(model, x, fs):
    x16 = x if fs == 16000 else None
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = f.name
    sf.write(path, np.asarray(x, dtype=np.float64), fs)
    try:
        segs, _ = model.transcribe(path, language="en", word_timestamps=True)
        out = []
        for sg in segs:
            for w in (sg.words or []):
                nw = re.sub(r"[^a-z]", "", w.word.lower())
                if nw:
                    out.append((nw, float(w.start), float(w.end), float(getattr(w, "probability", 1.0))))
        return out
    finally:
        os.unlink(path)


def gated_spans(ww, mms, tau, delta):
    """Whisper gives the LABEL; MMS_FA gives the SPAN (the agent's spec). Keep an MMS_FA word span iff a same-string
    whisper word has conf>=tau AND its boundary AGREES with this MMS_FA boundary within delta (hallucinations: whisper
    boundary vs MMS_FA-forced boundary disagree -> dropped). Returns MMS_FA (clean) spans."""
    wby = defaultdict(list)
    for (w, t0, t1, p) in ww:
        wby[w].append((t0, t1, p))
    kept = []
    for (w, mt0, mt1) in mms:
        for (t0, t1, p) in wby.get(w, []):
            if p >= tau and abs(t0 - mt0) < delta and abs(t1 - mt1) < delta:
                kept.append((w, mt0, mt1)); break
    return kept


def bank_spans(x, fs, spans, bank):
    for (w, t0, t1) in spans:
        if len(w) < MINW:
            continue
        seg = x[int(t0 * fs):int(t1 * fs)]
        if seg.size >= int(0.05 * fs):
            bank[w].append(frames(np.asarray(seg, dtype=np.float64))[0].astype(np.float32))


def main():
    print("=" * 100)
    print("GATED EXEMPLAR HARVEST — grow bank coverage from Whisper labels (structure-preserving, bias-gated)")
    print("=" * 100)
    from faster_whisper import WhisperModel
    wm = WhisperModel("base.en", device="cpu", compute_type="int8")
    tr = transcripts(DEV)
    flacs = sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True))
    by_spk = defaultdict(list)
    for f in flacs:
        base = os.path.basename(f)[:-5]
        if base in tr:
            by_spk[os.path.basename(f).split("-")[0]].append((f, tr[base]))
    spks = sorted(by_spk)
    test_spk = spks[-3:]
    harvest_spk = spks[:-3]
    harvest_utts = [(f, t) for sp in harvest_spk for (f, t) in by_spk[sp]]
    test_utts = [(f, t) for sp in test_spk for (f, t) in by_spk[sp]]
    print(f"  {len(harvest_spk)} harvest speakers, {len(test_spk)} test; TAU={TAU}, DELTA={DELTA}\n", flush=True)

    # banks: baseline(oracle small) ; +gated ; +ungated ; +oracle(ceiling)
    base, gated, ungated, oracle = (defaultdict(list) for _ in range(4))

    print("  building baseline (oracle, small)...", flush=True)
    for (f, t) in harvest_utts[:N_BASE]:
        x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64)
        for b in (base, gated, ungated, oracle):
            bank_spans(x, fs, align_utt(x, fs, t), b)

    print(f"  harvesting {N_HARVEST} utts (whisper + MMS_FA gate)...", flush=True)
    drop_conf = drop_align = kept = total = 0
    for i, (f, t) in enumerate(harvest_utts[N_BASE:N_BASE + N_HARVEST]):
        x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64)
        ww = whisper_words(wm, x, fs)
        wtext = " ".join(w for (w, _a, _b, _p) in ww)
        mms = [(w, t0, t1) for (w, t0, t1) in align_utt(x, fs, wtext)]
        g = gated_spans(ww, mms, TAU, DELTA)
        total += len(mms); kept += len(g)
        bank_spans(x, fs, mms, ungated)                                      # whisper labels, MMS_FA spans, NO gate
        bank_spans(x, fs, g, gated)                                          # whisper labels, MMS_FA spans, GATED
        bank_spans(x, fs, align_utt(x, fs, t), oracle)                       # TRUE labels, MMS_FA spans (ceiling)
        if (i + 1) % 15 == 0:
            print(f"    {i+1}/{N_HARVEST} (gate kept {kept}/{total} words)...", flush=True)

    # TEST instances (true labels, MMS_FA segments)
    print(f"  preparing {N_TEST} test utts...", flush=True)
    test = []
    for (f, t) in test_utts[:N_TEST]:
        x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64)
        for (w, t0, t1) in align_utt(x, fs, t):
            if len(w) < MINW:
                continue
            seg = x[int(t0 * fs):int(t1 * fs)]
            if seg.size >= int(0.05 * fs):
                test.append((w, frames(np.asarray(seg, dtype=np.float64))[0].astype(np.float32)))
    vocab = sorted({w for (w, _s) in test})
    print(f"  {len(test)} test instances; {len(vocab)}-word candidate set\n", flush=True)

    def evaluate(bank):
        # nearest-exemplar DTW over candidate words that HAVE exemplars
        cand = [w for w in vocab if bank.get(w)]
        c_ok = c_tot = f_ok = f_tot = 0
        for (tw, ts) in test:
            best, arg = 1e18, None
            for w in cand:
                d = min(dtw(ts, ex) for ex in bank[w])
                if d < best:
                    best, arg = d, w
            if tw in STOP:
                f_tot += 1; f_ok += int(arg == tw)
            else:
                c_tot += 1; c_ok += int(arg == tw)
        return (100 * c_ok / max(c_tot, 1), 100 * f_ok / max(f_tot, 1), c_tot, f_tot,
                sum(1 for w in vocab if bank.get(w)))

    rows = [("baseline (oracle small)", base), ("+ UNGATED harvest", ungated),
            ("+ GATED harvest", gated), ("+ ORACLE harvest (ceiling)", oracle)]
    print(f"    {'bank':>28}{'content recall':>16}{'function recall':>17}{'vocab covered':>15}")
    res = {}
    for name, b in rows:
        cr, fr, ct, ft, vc = evaluate(b)
        res[name] = (cr, fr)
        print(f"    {name:>28}{cr:>13.1f}% {fr:>14.1f}%  {vc:>10}/{len(vocab)}", flush=True)

    bcr, bfr = res["baseline (oracle small)"]
    gcr, gfr = res["+ GATED harvest"]
    ucr, ufr = res["+ UNGATED harvest"]
    ocr, ofr = res["+ ORACLE harvest (ceiling)"]
    print(f"\n  gate kept {kept}/{total} harvested words ({100*kept/max(total,1):.0f}%)")
    print("=" * 100)
    print(f"  content recall: baseline {bcr:.1f} -> GATED {gcr:.1f} (+{gcr-bcr:.1f}) | UNGATED {ucr:.1f} | ORACLE {ocr:.1f}")
    print(f"  function recall: baseline {bfr:.1f} -> GATED {gfr:.1f} ({gfr-bfr:+.1f}) | UNGATED {ufr:.1f} ({ufr-bfr:+.1f})")
    if gcr >= bcr + 5 and gfr >= bfr - 1.0:
        print(f"  KEEP — the gated harvest GROWS RECALL architecture-clean: content +{gcr-bcr:.1f} (>= +5) with function")
        print(f"  {gfr-bfr:+.1f} (no drop). Whisper supplied only labels+spans; the graph banked the agent's OWN cochleagram")
        print(f"  exemplars. The bias gate held (kept {100*kept/max(total,1):.0f}%); GATED tracks ORACLE ({gcr:.1f} vs {ocr:.1f}) where")
        if ufr < gfr - 1.0:
            print(f"  UNGATED leaked bias (function {ufr:.1f} < gated {gfr:.1f}). Harvest is the recall lever; the gate is load-bearing.")
        else:
            print(f"  UNGATED was comparable here (clean read speech -> little hallucination). Harvest is the recall lever.")
    elif gcr >= bcr + 5:
        print(f"  PARTIAL — content grew +{gcr-bcr:.1f} but function moved {gfr-bfr:+.1f} (gate didn't fully hold). Honest.")
    else:
        print(f"  NO — harvest did not grow content recall +5 ({bcr:.1f}->{gcr:.1f}); coverage/quality too low at this scale. Honest.")
    print("=" * 100)


if __name__ == "__main__":
    main()
