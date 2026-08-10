"""extract_speech_seed — a MECHANICAL extractor that does a COMPLETE extraction of a speech exemplar bank into seeds.

The production form of the validated harvest loop. Pure host I/O, NO agent decisions: walk a corpus, label each
utterance (whisper = the model harvest for unlabelled audio, OR oracle = the true transcript via MMS_FA), force-align
to MMS_FA spans, compute the agent's OWN cochleagram exemplars, and EMIT them as WordExemplar seed manifests (the same
graph-resident form GraphLexicon banks). Sharded by word-initial, capped K exemplars/word (broad coverage, bounded
size), RESUMABLE (checkpointed), idempotent. Architecture-clean: the model supplies only labels+spans; the seed holds
the agent's own structure-preserving exemplars; the Rust loader installs them at boot.

  python -m scripts.extract_speech_seed --labeller whisper --max_utts 500 --k 3
  python -m scripts.extract_speech_seed --labeller oracle  --max_utts 0      # 0 = ALL utts (complete)
  python -m scripts.extract_speech_seed --verify                            # load shards, report coverage + recog

Out: <out>/<initial>.json seed shards; checkpoint at <ckpt>. Re-run resumes.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import pickle
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import substrate_rs as srs
from substrate.world_adapter import WorldAdapter
from domains.speech_world_recognizer import GraphLexicon, N_CHANNELS, _exemplar_attr
from scripts.abs_language_decode import acoustic_logp, FS
import domains.self_directed_speech_world as SDW
from scripts.librispeech_wer import load_flac
from scripts.phonebank import align_utt
from scripts.jabberwock_harvest_exemplars import transcripts, whisper_words, DEV, MINW

OUT = Path("/home/matt/data/speech_seed")
CKPT = Path("/home/matt/data/speech_seed_ckpt.pkl")


def exemplar_attrs(word, channels, source):
    a = {"word": word, "source": source, "hearings": 1}
    for ci in range(N_CHANNELS):
        v = np.asarray(channels[ci]).ravel() if ci < len(channels) else np.zeros(8)
        a[_exemplar_attr(ci)] = [round(float(z), 4) for z in v]
    return a


def write_shards(bank, outdir):
    by_shard = defaultdict(list)
    for w, exs in bank.items():
        sh = w[0] if (w and w[0].isalpha()) else "_"
        by_shard[sh].extend(exs)
    outdir.mkdir(parents=True, exist_ok=True)
    for sh, nodes in by_shard.items():
        m = {"id": f"speech_seed_{sh}", "version": "1.0.0", "depends_on": [],
             "nodes": [{"local_id": i, "type": "WordExemplar", "attrs": a} for i, a in enumerate(nodes)],
             "edges": [], "productions": []}
        (outdir / f"{sh}.json").write_text(json.dumps(m))


def verify(outdir, n_test=40):
    print("  [VERIFY] loading all shards into a fresh boot...", flush=True)
    fresh = WorldAdapter()
    nodes = 0
    for sf in sorted(outdir.glob("*.json")):
        m = json.loads(sf.read_text())
        fresh.inner.load_seed_manifest(m, fresh.agent); nodes += len(m["nodes"])
    lex = GraphLexicon(fresh.s); banked = lex.banked()
    cands = sorted({w for (w, _v) in banked})
    sz = sum(f.stat().st_size for f in outdir.glob("*.json"))
    print(f"  [VERIFY] {nodes} exemplar nodes -> banked {len(banked)} ({len(cands)} words); {sz//1024//1024} MB across "
          f"{len(list(outdir.glob('*.json')))} shards", flush=True)
    # recognise held-out test-speaker instances of seeded words
    tr = transcripts(DEV)
    flacs = sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True))
    by_spk = defaultdict(list)
    for f in flacs:
        b = os.path.basename(f)[:-5]
        if b in tr:
            by_spk[os.path.basename(f).split("-")[0]].append((f, tr[b]))
    test_spk = sorted(by_spk)[-3:]
    sw = set(cands); ok = tot = 0; seen = 0
    for sp in test_spk:
        for (f, t) in by_spk[sp]:
            if seen >= n_test:
                break
            x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64); seen += 1
            for (w, t0, t1) in align_utt(x, fs, t):
                if w in sw and len(w) >= MINW:
                    seg = x[int(t0 * fs):int(t1 * fs)]
                    if seg.size >= int(0.05 * fs):
                        ch = SDW.feature_channels(fresh.s, np.asarray(seg, dtype=np.float64), FS)
                        d = acoustic_logp(ch, banked, cands)
                        if d:
                            tot += 1; ok += int(max(d, key=d.get) == w)
    print(f"  [VERIFY] held-out recognition over the COMPLETE bank: {ok}/{tot} = {100*ok/max(tot,1):.1f}% "
          f"({len(cands)}-word vocab)", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labeller", choices=["whisper", "oracle"], default="whisper")
    ap.add_argument("--max_utts", type=int, default=500, help="0 = ALL")
    ap.add_argument("--k", type=int, default=3, help="exemplars/word cap")
    ap.add_argument("--ckpt_every", type=int, default=60)
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    print("=" * 100)
    print(f"MECHANICAL SPEECH-SEED EXTRACTOR — labeller={args.labeller}, K={args.k}/word, complete extraction")
    print("=" * 100)
    if args.verify:
        verify(OUT)
        return

    bank = defaultdict(list); done = set()
    if CKPT.exists():
        st = pickle.load(open(CKPT, "rb")); bank = defaultdict(list, st["bank"]); done = st["done"]
        print(f"  resumed: {len(done)} utts done, {len(bank)} words, "
              f"{sum(len(v) for v in bank.values())} exemplars", flush=True)
    wm = None
    if args.labeller == "whisper":
        from faster_whisper import WhisperModel
        wm = WhisperModel("base.en", device="cpu", compute_type="int8")

    tr = transcripts(DEV)
    flacs = sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True))
    # hold out the last 3 speakers (the test set used by verify) -> never extracted
    spks = sorted({os.path.basename(f).split("-")[0] for f in flacs})
    train_spk = set(spks[:-3])
    utts = [(f, tr[os.path.basename(f)[:-5]]) for f in flacs
            if os.path.basename(f)[:-5] in tr and os.path.basename(f).split("-")[0] in train_spk]
    todo = [(f, t) for (f, t) in utts if os.path.basename(f)[:-5] not in done]
    if args.max_utts:
        todo = todo[:args.max_utts]
    print(f"  {len(utts)} train-speaker utts; {len(todo)} to extract this run\n", flush=True)

    t0 = time.time()
    for i, (f, t) in enumerate(todo):
        base = os.path.basename(f)[:-5]
        x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64)
        if args.labeller == "oracle":
            spans = align_utt(x, fs, t)
        else:
            ww = whisper_words(wm, x, fs)
            spans = align_utt(x, fs, " ".join(w for (w, _a, _b, _p) in ww))   # whisper LABEL, MMS_FA SPAN
        s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0})
        for (w, a, b) in spans:
            if len(w) < MINW or len(bank[w]) >= args.k:
                continue
            seg = x[int(a * fs):int(b * fs)]
            if seg.size >= int(0.05 * fs):
                ch = SDW.feature_channels(s, np.asarray(seg, dtype=np.float64), FS)
                bank[w].append(exemplar_attrs(w, ch, args.labeller))
        done.add(base)
        if (i + 1) % args.ckpt_every == 0:
            pickle.dump({"bank": dict(bank), "done": done}, open(CKPT, "wb"))
            write_shards(bank, OUT)
            ex = sum(len(v) for v in bank.values())
            print(f"    {i+1}/{len(todo)} utts | {len(bank)} words | {ex} exemplars | "
                  f"{(time.time()-t0)/(i+1):.2f}s/utt", flush=True)

    pickle.dump({"bank": dict(bank), "done": done}, open(CKPT, "wb"))
    write_shards(bank, OUT)
    ex = sum(len(v) for v in bank.values())
    print(f"\n  EXTRACTION COMPLETE this run: {len(done)} utts -> {len(bank)} distinct words, {ex} exemplars", flush=True)
    verify(OUT)
    print("\n" + "=" * 100)
    print(f"  the COMPLETE bank is seeded: {len(bank)} words across {len(list(OUT.glob('*.json')))} shards in {OUT}.")
    print("  Mechanical, resumable (re-run continues), idempotent (K/word cap). The agent boots with the whole bank.")
    print("=" * 100)


if __name__ == "__main__":
    main()
