"""GIVE IT THE PRONUNCIATION GUIDES — clean phonetic data to sharpen the phone units.

The cartoon corpus is noisy (music, effects). Pronunciation / vocal guides are
SLOW, ISOLATED, CONTRASTIVE phonemes — the cleanest phonetic signal. Test whether
a phone inventory learned from the CLEAN guides TRANSFERS to messy real (cartoon)
speech: train the relational phone alphabet + transition model on the guides, then
map held-out CARTOON speech onto that frozen alphabet (match_sign) and measure
coverage (OOV) + next-unit prediction. If clean phones cover + predict cartoons,
the guides gave a better, transferable inventory.

Run:  python -m scripts.learn_speech_pronunciation [n_cartoon_heldout]
"""
from __future__ import annotations
import glob
import os
import random
import subprocess
import sys
import threading
import time

import numpy as np

sys.path.insert(0, "."); sys.path.insert(0, "runners/dsl/python")
import scripts.watch_jellyfin_cortex as W
W.VISION = False
W.FAST_FORWARD = True
N_CARTOON = int(sys.argv[1]) if len(sys.argv) > 1 else 3
HOP_S = 0.05
GUIDES = sorted(glob.glob("pronunciation_corpus/*.opus"))

import substrate_rs as srs                                       # noqa: E402
from substrate_rs import audio as A, speech as SP               # noqa: E402
from scripts.jellyfin_world import JellyfinWorld                # noqa: E402

random.seed(7)


def rank16(v):
    # GRAPH-NATIVE: relational ordinal rank = the held substrate op (Rust).
    return np.asarray(srs.Substrate.shape_signature([float(x) for x in v]),
                      dtype=np.float32)


def collapse(seq):
    out = []
    for u in seq:
        if not out or out[-1] != u:
            out.append(u)
    return out


def dur(path):
    try:
        o = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                            "format=duration", "-of", "csv=p=0", path],
                           capture_output=True, text=True, timeout=60).stdout.strip()
        return float(o) if o else 600.0
    except Exception:
        return 600.0


def bigram_rank(seqs):
    bg = {}
    for seq in seqs:
        for a, b in zip(seq, seq[1:]):
            bg.setdefault(a, {})[b] = bg.setdefault(a, {}).get(b, 0) + 1
    return {a: max(nx.items(), key=lambda kv: kv[1])[0] for a, nx in bg.items()}


def predict_top1(ranked, seqs):
    hit = n = 0
    for seq in seqs:
        for a, b in zip(seq, seq[1:]):
            if a in ranked:
                n += 1; hit += (ranked[a] == b)
    return (hit / n if n else 0.0), n


def freq_top1(seqs):
    from collections import Counter
    fr = Counter(b for seq in seqs for b in seq[1:])
    if not fr:
        return 0.0
    top = fr.most_common(1)[0][0]
    n = sum(max(len(seq) - 1, 0) for seq in seqs)
    hit = sum(1 for seq in seqs for b in seq[1:] if b == top)
    return hit / n if n else 0.0


def shuffled(seqs):
    toks = [t for c in seqs for t in c]; random.shuffle(toks)
    out, i = [], 0
    for L in [len(c) for c in seqs]:
        out.append(toks[i:i + L]); i += L
    return out


def main():
    print("=" * 80)
    print(f"PRONUNCIATION GUIDES -> phone inventory; transfer to cartoons "
          f"({len(GUIDES)} guides)")
    print("=" * 80)
    if not GUIDES:
        print("  no pronunciation_corpus/*.opus — download first."); return
    s = srs.Substrate()
    A.seed_audio_grammar(s); A.seed_native_codec_grammar(s); SP.seed_speech_grammar(s)
    s.memory_bound(20000, 256 * 1024 * 1024, 3)
    s.memory_disposable_capacity(16 * 1024 * 1024, 2048)
    master = W.MasterClock(fast_forward=True)
    url_box = [None]; commit = threading.Lock()
    acx = W.AudioCortex(s, master, SP.open_lexicon(s, name="online"), url_box, commit)
    acx.frame_chunks = []; acx.frame_hop_s = HOP_S
    acx.start()

    def consume(path, label, dur_s):
        before = len(acx.frame_chunks)
        url_box[0] = path; master.start_title(0.0, duration_s=dur_s); acx.ff_done = False
        p0 = time.time()
        while not acx.ff_done:
            if time.time() - p0 > 200:
                break
            time.sleep(0.1)
        with commit:
            s.memory_forget_type("CortexStamp")
        fr = []
        for ci in range(before, len(acx.frame_chunks)):
            fr.extend(acx.frame_chunks[ci])
        print(f"  {label:<46} {dur_s/60:5.1f}min  frames={len(fr)}")
        return [np.asarray(v, np.float32) for v in fr]

    # PHASE 1 — clean guides -> train frames
    print("\n  CLEAN GUIDES (train the phone inventory):")
    guide_frames = []
    for g in GUIDES:
        guide_frames.extend(consume(g, os.path.basename(g)[:46], dur(g)))

    # PHASE 2 — cartoons -> held-out frames
    print("\n  CARTOONS (held-out — messy real speech):")
    cart_frames = []
    try:
        jf = JellyfinWorld().connect(); jf.ingest_catalog(s)
        watched = []
        for _ in range(N_CARTOON):
            picks = jf.choose(s, n=1, watched_series=watched)
            if not picks:
                break
            t = picks[0]; watched.append(t["name"])
            eps = jf.episodes(t["id"], limit=1)
            if not eps:
                continue
            url = jf.stream_url(eps[0]["id"])
            d = float(eps[0].get("runtime_s") or 0.0) or 600.0
            cart_frames.append(consume(url, t["name"][:46], d))
    except Exception as e:
        print(f"  (cartoon held-out skipped: {e})")
    acx.stop(); time.sleep(0.3)

    # frozen phone lexicon from CLEAN guides; collapse runs
    lex = SP.open_lexicon(s, name="guide_phones")
    train = [SP.acquire_sign(s, lex, rank16(v), threshold=0.85)[0] for v in guide_frames]
    train_seq = collapse([x.value for x in train if x is not None])
    # split train into chunks for bigram train/test stability
    train_seqs = [train_seq[i:i + 400] for i in range(0, len(train_seq), 400)]
    train_seqs = [c for c in train_seqs if len(c) >= 2]
    lex_size = len(SP.lexicon_signs(s, lex))

    print("\n" + "=" * 80)
    print("RESULT")
    print("=" * 80)
    print(f"  CLEAN-guide phone inventory: {lex_size} units "
          f"(from {len(guide_frames)} frames)")

    ranked = bigram_rank(train_seqs)
    # transfer: map each CARTOON onto the guide alphabet, measure
    print(f"\n  TRANSFER to cartoons (map onto the clean-guide alphabet, no minting):")
    all_held = []
    for ci, frames in enumerate(cart_frames):
        seq, oov = [], 0
        for v in frames:
            sg, _ = SP.match_sign(s, lex, rank16(v), threshold=0.85)
            if sg is None:
                oov += 1; seq.append(-1)
            else:
                seq.append(sg.value)
        seq = collapse(seq)
        chunks = [seq[i:i + 400] for i in range(0, len(seq), 400)]
        chunks = [c for c in chunks if len(c) >= 2]
        all_held.extend(chunks)
        hu, npred = predict_top1(ranked, chunks)
        hf = freq_top1(chunks)
        cover = 1.0 - oov / max(len(frames), 1)
        print(f"    cartoon {ci+1}: coverage={cover:.3f} (OOV {oov}/{len(frames)})  "
              f"guide-model next-unit={hu:.3f} vs baseline {hf:.3f} ({hu/max(hf,1e-9):.2f}x)")
    if all_held:
        hu, _ = predict_top1(ranked, all_held)
        hf = freq_top1(all_held)
        hs, _ = predict_top1(ranked, shuffled(all_held))
        print(f"\n  OVERALL transfer: guide-trained model predicts cartoon next-unit "
              f"{hu:.3f} vs baseline {hf:.3f} ({hu/max(hf,1e-9):.2f}x), chance "
              f"{1/max(lex_size,1):.4f}, shuffle {hs:.3f}"
              f"{' COLLAPSES' if hs < 0.7*hu else ''}")
        print(f"\n  VERDICT: clean pronunciation phones "
              f"{'TRANSFER to real speech (cover + predict cartoons above baseline)' if (hu>hf) else 'transfer weakly (see numbers)'}.")
    print("=" * 80)


if __name__ == "__main__":
    main()
