"""STRENGTHEN THE WORD LAYER (the agent's residual is here).

The phone layer generalizes (held-out next-unit 0.209, shuffle-collapses, OOV
3/7159) — converged. The residual is the WORD layer (held-out next-word 0.068,
overlap 0.59). The agent's own word-building operator is compositional_chunking:
promote frequently-recurring adjacent units into chunks (BPE-style merging). This
builds a compact recurring-word vocabulary from the phone stream, which should
generalize better than per-cut TP-trough segmentation.

A/B on held-out shows: TP-trough segmentation vs chunk-promotion (BPE). Same phone
stream (static relational phone-frames, the winning unit config). The decisive
metrics: held-out next-WORD prediction (collapses under shuffle = real word order)
and held-out word OVERLAP (do the learned words recur in an unseen show).

Run:  python -m scripts.learn_speech_words [wall_seconds] [n_heldout] [n_merges]
"""
from __future__ import annotations
import random
import sys
import threading
import time
from collections import Counter

import numpy as np

sys.path.insert(0, "."); sys.path.insert(0, "runners/dsl/python")
import scripts.watch_jellyfin_cortex as W
W.VISION = False
W.FAST_FORWARD = True
RUN_SECONDS = int(sys.argv[1]) if len(sys.argv) > 1 else 360
N_HELDOUT = int(sys.argv[2]) if len(sys.argv) > 2 else 2
N_MERGES = int(sys.argv[3]) if len(sys.argv) > 3 else 600
HOP_S = 0.05

import substrate_rs as srs                                       # noqa: E402
from substrate_rs import audio as A, speech as SP                # noqa: E402
from scripts.jellyfin_world import JellyfinWorld                 # noqa: E402

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


# ---- TP-trough segmentation (baseline word model) ----
def tp_table(seqs):
    uni, fwd = {}, {}
    for seq in seqs:
        for a, b in zip(seq, seq[1:]):
            uni[a] = uni.get(a, 0) + 1
            fwd.setdefault(a, {})[b] = fwd.setdefault(a, {}).get(b, 0) + 1
    return {a: {b: c / uni[a] for b, c in nx.items()} for a, nx in fwd.items()}


def tp_segment(seq, t):
    if len(seq) < 2:
        return [tuple(seq)] if seq else []
    words, cur = [], [seq[0]]
    for i in range(1, len(seq)):
        here = t.get(seq[i - 1], {}).get(seq[i], 1.0)
        prev = t.get(seq[i - 2], {}).get(seq[i - 1], 1.0) if i >= 2 else 1.0
        nxt = t.get(seq[i], {}).get(seq[i + 1], 1.0) if i + 1 < len(seq) else 1.0
        if here < prev and here < nxt:
            words.append(tuple(cur)); cur = [seq[i]]
        else:
            cur.append(seq[i])
    words.append(tuple(cur))
    return words


# ---- chunk promotion = BPE (the agent's compositional_chunking) ----
def learn_merges(seqs, n_merges, min_count=5):
    seqs = [list(s) for s in seqs]
    merges = []
    nid = 100000
    for _ in range(n_merges):
        pairs = Counter()
        for s in seqs:
            for a, b in zip(s, s[1:]):
                pairs[(a, b)] += 1
        if not pairs:
            break
        (a, b), c = pairs.most_common(1)[0]
        if c < min_count:
            break
        merges.append(((a, b), nid))
        for s in seqs:
            i = 0
            while i < len(s) - 1:
                if s[i] == a and s[i + 1] == b:
                    s[i:i + 2] = [nid]
                else:
                    i += 1
        nid += 1
    return merges


def apply_merges(seqs, merges):
    out = [list(s) for s in seqs]
    for (a, b), nid in merges:
        for s in out:
            i = 0
            while i < len(s) - 1:
                if s[i] == a and s[i + 1] == b:
                    s[i:i + 2] = [nid]
                else:
                    i += 1
    return [[(x,) if not isinstance(x, tuple) else x for x in s] for s in out]


# ---- prediction + controls (word level) ----
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
    fr = Counter(b for seq in seqs for b in seq[1:])
    if not fr:
        return 0.0
    top = fr.most_common(1)[0][0]
    n = sum(len(seq) - 1 for seq in seqs if len(seq) >= 2)
    hit = sum(1 for seq in seqs for b in seq[1:] if b == top)
    return hit / n if n else 0.0


def shuffled(seqs):
    toks = [t for c in seqs for t in c]; random.shuffle(toks)
    out, i = [], 0
    for L in [len(c) for c in seqs]:
        out.append(toks[i:i + L]); i += L
    return out


def word_metrics(train_words, held_words, tag):
    train_words = [w for w in train_words if len(w) >= 2]
    held_words = [w for w in held_words if len(w) >= 2]
    wc = Counter(w for seq in train_words for w in seq)
    recurring = {w for w, c in wc.items() if c >= 2}
    mean_len = (sum(len(w if isinstance(w, tuple) else (w,)) for seq in train_words for w in seq)
                / max(sum(len(s) for s in train_words), 1))
    ranked = bigram_rank(train_words)
    hw, npred = predict_top1(ranked, held_words)
    hf = freq_top1(held_words)
    hs, _ = predict_top1(ranked, shuffled(held_words))
    allw = [w for seq in held_words for w in seq]
    ov = sum(1 for w in allw if w in recurring) / max(len(allw), 1)
    vocab = len(wc)
    print(f"  {tag:<10} words: vocab={vocab:>5} recurring={len(recurring):>5} "
          f"mean_len={mean_len:.2f}  held next-word={hw:.3f} ({hw/max(hf,1e-9):.2f}x) "
          f"shuffle={hs:.3f}{' COLLAPSE' if hs<0.7*hw else ''}  overlap={ov:.2f}")
    return dict(next=hw, freq=hf, overlap=ov)


def main():
    print("=" * 84)
    print(f"WORD LAYER A/B (TP-trough vs chunk-promotion) — {RUN_SECONDS}s, hold out {N_HELDOUT}")
    print("=" * 84)
    s = srs.Substrate()
    A.seed_audio_grammar(s); A.seed_native_codec_grammar(s); SP.seed_speech_grammar(s)
    s.memory_bound(20000, 256 * 1024 * 1024, 3)
    s.memory_disposable_capacity(16 * 1024 * 1024, 2048)
    jf = JellyfinWorld().connect(); jf.ingest_catalog(s)
    master = W.MasterClock(fast_forward=True)
    url_box = [None]; commit = threading.Lock()
    acx = W.AudioCortex(s, master, SP.open_lexicon(s, name="online"), url_box, commit)
    acx.frame_chunks = []; acx.frame_hop_s = HOP_S
    acx.start()

    def robust(fn, *a, tries=4, **k):
        for i in range(tries):
            try:
                return fn(*a, **k)
            except Exception:
                time.sleep(2 * (i + 1))
        return None

    titles = []; title_start = []; t0 = time.time()
    while time.time() - t0 < RUN_SECONDS:
        picks = robust(jf.choose, s, n=1, watched_series=titles)
        if not picks:
            if time.time() - t0 < RUN_SECONDS - 20:
                continue
            break
        title = picks[0]
        eps = robust(jf.episodes, title["id"], limit=1)
        url = robust(jf.stream_url, eps[0]["id"]) if eps else None
        if not url:
            titles.append(title["name"]); continue
        dur = float(eps[0].get("runtime_s") or 0.0) or 600.0
        title_start.append(len(acx.frame_chunks))
        url_box[0] = url; master.start_title(0.0, duration_s=dur); acx.ff_done = False
        p0 = time.time()
        while not acx.ff_done:
            if time.time() - t0 > RUN_SECONDS or time.time() - p0 > 300:
                break
            time.sleep(0.1)
        titles.append(title["name"])
        with commit:
            s.memory_forget_type("CortexStamp")
        print(f"  consumed {len(titles)}: {title['name'][:30]:<30} "
              f"frames={sum(len(c) for c in acx.frame_chunks)}")
        url_box[0] = None
    acx.stop(); time.sleep(0.3)

    n_titles = len(titles)
    if n_titles < N_HELDOUT + 2:
        print(f"\n  only {n_titles} titles — run longer."); return
    starts = title_start + [len(acx.frame_chunks)]
    title_frames = []
    for ti in range(n_titles):
        fr = []
        for ci in range(starts[ti], starts[ti + 1]):
            if ci < len(acx.frame_chunks):
                fr.extend(acx.frame_chunks[ci])
        title_frames.append([np.asarray(v, np.float32) for v in fr])
    held = set(range(n_titles - N_HELDOUT, n_titles))

    # frozen relational PHONE lexicon (static units, the winner)
    lex = SP.open_lexicon(s, name="train")
    train_seqs, held_seqs = [], []
    for ti in range(n_titles):
        units = [SP.acquire_sign(s, lex, rank16(v), threshold=0.85)[0] if ti not in held
                 else SP.match_sign(s, lex, rank16(v), threshold=0.85)[0]
                 for v in title_frames[ti]]
        seq = collapse([(x.value if x is not None else -1) for x in units])
        (held_seqs if ti in held else train_seqs).append(seq)
    train_seqs = [c for c in train_seqs if len(c) >= 2]
    held_seqs = [c for c in held_seqs if len(c) >= 2]
    lex_size = len(SP.lexicon_signs(s, lex))
    print(f"\n  PHONE units: {lex_size};  train phones {sum(len(c) for c in train_seqs)}, "
          f"held phones {sum(len(c) for c in held_seqs)}")

    print("\n  WORD-LAYER A/B on held-out shows:")
    # baseline: TP-trough segmentation
    table = tp_table(train_seqs)
    tp_train = [tp_segment(c, table) for c in train_seqs]
    tp_held = [tp_segment(c, table) for c in held_seqs]
    word_metrics(tp_train, tp_held, "TP-trough")
    # chunk promotion (BPE): learn merges on TRAIN, apply to HELD-OUT
    merges = learn_merges(train_seqs, N_MERGES)
    bpe_train = apply_merges(train_seqs, merges)
    bpe_held = apply_merges(held_seqs, merges)
    word_metrics(bpe_train, bpe_held, f"chunk({len(merges)})")
    print("\n" + "=" * 84)


if __name__ == "__main__":
    main()
