"""SPEECH, FINER: phone/syllable-scale units instead of one-sign-per-utterance.

The coarse pipeline gave ~1 unit/sec (phrase scale): held-out next-unit pred 0.095
(1.31x baseline). The limiter is unit GRANULARITY. This captures a per-FRAME
cochleagram (fixed hop) so the stream is phone/syllable scale, collapses steady
runs into a phone-transition stream, then re-runs the SAME held-out generalization
test (train lexicon+model on TRAIN shows, map UNSEEN shows onto the frozen alphabet
via match_sign, test next-unit + TP-trough word segmentation). Did finer units make
speech better?

Run:  python -m scripts.learn_speech_frames [wall_seconds] [n_heldout] [hop_ms]
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
HOP_S = (int(sys.argv[3]) if len(sys.argv) > 3 else 50) / 1000.0

import substrate_rs as srs                                       # noqa: E402
from substrate_rs import audio as A, speech as SP                # noqa: E402
from scripts.jellyfin_world import JellyfinWorld                 # noqa: E402

random.seed(7)


def rank16(v):
    # GRAPH-NATIVE: ordinal spectral shape = the held substrate op (Rust), not numpy.
    return np.asarray(srs.Substrate.shape_signature([float(x) for x in v]),
                      dtype=np.float32)


def collapse(seq):
    out = []
    for u in seq:
        if not out or out[-1] != u:
            out.append(u)
    return out


def tp_table(seqs):
    uni, fwd = {}, {}
    for seq in seqs:
        for a, b in zip(seq, seq[1:]):
            uni[a] = uni.get(a, 0) + 1
            fwd.setdefault(a, {})[b] = fwd.setdefault(a, {}).get(b, 0) + 1
    return {a: {b: c / uni[a] for b, c in nx.items()} for a, nx in fwd.items()}


def tp(t, a, b, d=1.0):
    return t.get(a, {}).get(b, d)


def segment(seq, t):
    if len(seq) < 2:
        return [tuple(seq)] if seq else []
    words, cur = [], [seq[0]]
    for i in range(1, len(seq)):
        here = tp(t, seq[i - 1], seq[i])
        prev = tp(t, seq[i - 2], seq[i - 1]) if i >= 2 else 1.0
        nxt = tp(t, seq[i], seq[i + 1]) if i + 1 < len(seq) else 1.0
        if here < prev and here < nxt:
            words.append(tuple(cur)); cur = [seq[i]]
        else:
            cur.append(seq[i])
    words.append(tuple(cur))
    return words


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


def freq_top1(test_seqs):
    fr = {}
    for seq in test_seqs:
        for b in seq[1:]:
            fr[b] = fr.get(b, 0) + 1
    if not fr:
        return 0.0
    top = max(fr.items(), key=lambda kv: kv[1])[0]
    hit = n = 0
    for seq in test_seqs:
        for b in seq[1:]:
            n += 1; hit += (b == top)
    return hit / n if n else 0.0


def shuffled(seqs):
    toks = [t for c in seqs for t in c]; random.shuffle(toks)
    out, i = [], 0
    for L in [len(c) for c in seqs]:
        out.append(toks[i:i + L]); i += L
    return out


def main():
    print("=" * 80)
    print(f"SPEECH FINER — frame hop {HOP_S*1000:.0f}ms, {RUN_SECONDS}s consume, "
          f"hold out {N_HELDOUT}")
    print("=" * 80)
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
        nfr = sum(len(c) for c in acx.frame_chunks)
        print(f"  consumed {len(titles)}: {title['name'][:32]:<32} "
              f"{(master.position() or 0)/60:5.1f}min  frames={nfr}")
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

    # feature builders over a title's frame list (delta needs the sequence)
    def static_feats(frames):
        return [rank16(f) for f in frames]

    def delta_feats(frames):
        out = []
        for i, f in enumerate(frames):
            d = f - frames[i - 1] if i > 0 else np.zeros_like(f)
            out.append(np.concatenate([rank16(f), rank16(d)]))  # spectral shape + its change
        return out

    def run_condition(feat_fn, tag):
        lex = SP.open_lexicon(s, name=f"cond_{tag}_{random.randint(0,1<<30)}")
        train_seqs = []
        for ti in range(n_titles):
            if ti in held:
                continue
            seq = [SP.acquire_sign(s, lex, v, threshold=0.85)[0] for v in feat_fn(title_frames[ti])]
            train_seqs.append(collapse([x.value for x in seq if x is not None]))
        lex_size = len(SP.lexicon_signs(s, lex))
        held_seqs, oov, tot = [], 0, 0
        for ti in held:
            seq = []
            for v in feat_fn(title_frames[ti]):
                sg, _ = SP.match_sign(s, lex, v, threshold=0.85)
                tot += 1
                if sg is None:
                    oov += 1; seq.append(-1)
                else:
                    seq.append(sg.value)
            held_seqs.append(collapse(seq))
        train_seqs = [c for c in train_seqs if len(c) >= 2]
        held_seqs = [c for c in held_seqs if len(c) >= 2]
        table = tp_table(train_seqs)
        words = [w for sq in train_seqs for w in segment(sq, table)]
        wc = Counter(words); recurring = {w for w, c in wc.items() if c >= 2}
        mean_len = sum(len(w) for w in words) / max(len(words), 1)
        unit_ranked = bigram_rank(train_seqs)
        word_ranked = bigram_rank([segment(sq, table) for sq in train_seqs])
        hu, _ = predict_top1(unit_ranked, held_seqs)
        hf = freq_top1(held_seqs)
        hs, _ = predict_top1(unit_ranked, shuffled(held_seqs))
        hw, wnp = predict_top1(word_ranked, [segment(sq, table) for sq in held_seqs])
        allw = [w for sq in held_seqs for w in segment(sq, table)]
        ov = sum(1 for w in allw if w in recurring) / max(len(allw), 1)
        print(f"  {tag:<7} units={lex_size:>3}  held next-unit={hu:.3f} "
              f"({hu/max(hf,1e-9):.2f}x base, {hu/max(1/max(lex_size,1),1e-9):.0f}x chance)  "
              f"shuffle={hs:.3f}{' COLLAPSE' if hs<0.7*hu else ''}  "
              f"OOV={oov}/{tot}  word: next={hw:.3f} overlap={ov:.2f} len={mean_len:.2f}")
        return dict(lex=lex_size, hu=hu, hf=hf, hs=hs)

    print("\n" + "=" * 80)
    print(f"SPEECH UNIT A/B  train {n_titles-N_HELDOUT} shows / held out {N_HELDOUT} "
          f"(unseen) @ {HOP_S*1000:.0f}ms")
    print("=" * 80)
    print("  coarse baseline (1 sign/utterance): units=69 held next-unit=0.095 (1.31x)\n")
    st = run_condition(static_feats, "STATIC")
    dl = run_condition(delta_feats, "+DELTA")
    print()
    better = "+DELTA" if dl["hu"] > st["hu"] else "STATIC"
    print(f"  VERDICT: best = {better} (held next-unit "
          f"{max(st['hu'], dl['hu']):.3f}); dynamics "
          f"{'helps' if dl['hu'] > st['hu']*1.03 else 'does not clearly help'}.")
    print("=" * 80)


if __name__ == "__main__":
    main()
