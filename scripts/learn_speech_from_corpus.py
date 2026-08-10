"""LEARN SPEECH FROM THE CORPUS AT SCALE — and isolate WHY it's hard.

Consume hours of the library's continuous speech fast, then test the agent's
proven strength: SEQUENTIAL STRUCTURE. The first run showed the lexicon condenses
but the held-out next-unit prediction barely beats frequency AND does NOT collapse
under shuffle -> the apparent structure is NOT real order. Diagnosis: the limiter
is UNIT QUALITY (raw cochlear cosine = speaker-variant, noisy), not data quantity.

So this runs a controlled A/B on the SAME captured speech: build the acoustic
lexicon two ways and measure transition structure for each —
  RAW   : raw cochlear features (speaker-variant).
  RANK  : relational-invariance — ordinal band-rank per time window (gain/speaker
          invariant by construction; the rep that beat surface features cross-speaker).
The decisive test is the SHUFFLE control: real sequential structure COLLAPSES when
order is destroyed. If RANK collapses (and RAW doesn't), cleaner units unlocked
real speech structure — the corpus helped, via better units.

Run:  python -m scripts.learn_speech_from_corpus [wall_seconds]
"""
from __future__ import annotations
import math
import random
import sys
import threading
import time

import numpy as np

sys.path.insert(0, "."); sys.path.insert(0, "runners/dsl/python")
import scripts.watch_jellyfin_cortex as W
W.VISION = False
W.FAST_FORWARD = True
RUN_SECONDS = int(sys.argv[1]) if len(sys.argv) > 1 else 300

import substrate_rs as srs                                       # noqa: E402
from substrate_rs import audio as A, speech as SP                # noqa: E402
from scripts.jellyfin_world import JellyfinWorld                 # noqa: E402

random.seed(7)
N_BANDS, N_WIN = 16, 4


def rank_feat(f):
    """Relational-invariance: ordinal rank of bands within each time window
    (invariant to per-window talker gain)."""
    # GRAPH-NATIVE: per-window relational rank = the held substrate op (Rust).
    a = np.asarray(f, dtype=np.float32).reshape(N_WIN, N_BANDS)
    return np.concatenate([srs.Substrate.shape_signature([float(x) for x in row])
                           for row in a]).astype(np.float32)


def entropy(counts):
    tot = sum(counts)
    if tot <= 0:
        return 0.0
    return -sum((c / tot) * math.log2(c / tot) for c in counts if c > 0)


def build_bigrams(seqs):
    bg = {}
    for seq in seqs:
        for a, b in zip(seq, seq[1:]):
            bg.setdefault(a, {}).setdefault(b, 0)
            bg[a][b] = bg[a].get(b, 0) + 1
    return bg


def bigram_top1(train, test, lex_size):
    bg = build_bigrams(train)
    ranked = {a: max(nx.items(), key=lambda kv: kv[1])[0] for a, nx in bg.items()}
    hit = npred = 0
    for seq in test:
        for a, b in zip(seq, seq[1:]):
            if a in ranked:
                npred += 1
                hit += (ranked[a] == b)
    return (hit / npred if npred else 0.0), 1.0 / max(lex_size, 1), npred


def unigram_top1(train, test):
    freq = {}
    for seq in train:
        for b in seq[1:]:
            freq[b] = freq.get(b, 0) + 1
    if not freq:
        return 0.0
    top = max(freq.items(), key=lambda kv: kv[1])[0]
    hit = npred = 0
    for seq in test:
        for b in seq[1:]:
            npred += 1
            hit += (b == top)
    return hit / npred if npred else 0.0


def acquire_seqs(s, feat_chunks, transform):
    """Rebuild a lexicon from captured features via the agent's acquire_sign;
    return (sign-id sequences per chunk, lexicon size)."""
    lex = SP.open_lexicon(s, name=f"abx_{id(transform)}_{random.randint(0,1<<30)}")
    seqs = []
    for fc in feat_chunks:
        seq = []
        for f in fc:
            feat = transform(f) if transform else f
            sign, _ = SP.acquire_sign(s, lex, feat, threshold=0.85)
            if sign is not None:
                seq.append(sign.value if hasattr(sign, "value") else int(sign))
        if seq:
            seqs.append(seq)
    return seqs, len(SP.lexicon_signs(s, lex))


def measure(seqs, lex_size, tag):
    seqs = [c for c in seqs if len(c) >= 2]
    toks = [t for c in seqs for t in c]
    if len(seqs) < 10 or lex_size < 5:
        print(f"  {tag}: too little data"); return
    random.seed(7); random.shuffle(seqs)
    cut = int(0.8 * len(seqs))
    b1, chance, npred = bigram_top1(seqs[:cut], seqs[cut:], lex_size)
    u1 = unigram_top1(seqs[:cut], seqs[cut:])
    # shuffle control: same tokens, order destroyed
    lengths = [len(c) for c in seqs]
    sh = list(toks); random.shuffle(sh)
    sc, i = [], 0
    for L in lengths:
        sc.append(sh[i:i + L]); i += L
    sc = [c for c in sc if len(c) >= 2]
    scut = int(0.8 * len(sc))
    sb1, _, _ = bigram_top1(sc[:scut], sc[scut:], lex_size)
    collapse = sb1 < 0.7 * b1
    print(f"  {tag:<5} lex={lex_size:>4}  bigram={b1:.3f}  freq={u1:.3f} "
          f"({b1/max(u1,1e-9):.2f}x)  chance={chance:.4f}  "
          f"shuffle={sb1:.3f} -> {'COLLAPSES (real order)' if collapse else 'no collapse'}")
    return dict(lex=lex_size, bigram=b1, freq=u1, shuffle=sb1, collapse=collapse)


def main():
    print("=" * 78)
    print(f"LEARN SPEECH FROM CORPUS — {RUN_SECONDS}s consume, then RAW vs RANK units A/B")
    print("=" * 78)
    s = srs.Substrate()
    A.seed_audio_grammar(s); A.seed_native_codec_grammar(s); SP.seed_speech_grammar(s)
    s.memory_bound(20000, 256 * 1024 * 1024, 3)
    s.memory_disposable_capacity(16 * 1024 * 1024, 2048)
    online_lex = SP.open_lexicon(s, name="online")

    jf = JellyfinWorld().connect(); jf.ingest_catalog(s)
    master = W.MasterClock(fast_forward=True)
    url_box = [None]; commit = threading.Lock()
    acx = W.AudioCortex(s, master, online_lex, url_box, commit)
    acx.heard_chunks = []
    feats = []                                       # capture raw feature vectors in order
    acx.feature_transform = lambda f: (feats.append(np.asarray(f, np.float32)), f)[1]
    acx.start()

    def robust(fn, *a, tries=4, **k):
        for i in range(tries):
            try:
                return fn(*a, **k)
            except Exception:
                time.sleep(2 * (i + 1))
        return None

    watched = []; media = 0.0; t0 = time.time()
    while time.time() - t0 < RUN_SECONDS:
        picks = robust(jf.choose, s, n=1, watched_series=watched)
        if not picks:
            if time.time() - t0 < RUN_SECONDS - 20:
                continue
            break
        title = picks[0]
        eps = robust(jf.episodes, title["id"], limit=1)
        url = robust(jf.stream_url, eps[0]["id"]) if eps else None
        if not url:
            watched.append(title["name"]); continue
        dur = float(eps[0].get("runtime_s") or 0.0) or 600.0
        url_box[0] = url; master.start_title(0.0, duration_s=dur); acx.ff_done = False
        p0 = time.time()
        while not acx.ff_done:
            if time.time() - t0 > RUN_SECONDS or time.time() - p0 > 300:
                break
            time.sleep(0.1)
        media += master.position() or 0.0
        with commit:
            s.memory_forget_type("CortexStamp")
        watched.append(title["name"])
        print(f"  watched {len(watched)}: {title['name'][:34]:<34} "
              f"{(master.position() or 0)/60:5.1f}min  utts={len(feats)}")
        url_box[0] = None
    acx.stop(); time.sleep(0.3)

    # regroup captured features into chunks (same grouping as heard_chunks)
    lengths = [len(c) for c in acx.heard_chunks]
    feat_chunks, i = [], 0
    for L in lengths:
        if i + L <= len(feats):
            feat_chunks.append(feats[i:i + L])
        i += L

    print("\n" + "=" * 78)
    print("WHAT IT LEARNED ABOUT SPEECH  (A/B: raw cochlear vs relational-rank units)")
    print("=" * 78)
    print(f"  consumed {len(watched)} titles, {media/60:.1f} min speech in "
          f"{time.time()-t0:.0f}s ({media/(time.time()-t0):.1f}x); "
          f"{len(feats)} utterances captured\n")
    raw_seqs, raw_n = acquire_seqs(s, feat_chunks, None)
    rank_seqs, rank_n = acquire_seqs(s, feat_chunks, rank_feat)
    print("  held-out next-unit prediction + shuffle control (the decisive test):")
    r = measure(raw_seqs, raw_n, "RAW")
    k = measure(rank_seqs, rank_n, "RANK")
    print()
    if r and k:
        if k["collapse"] and not r["collapse"]:
            print("  VERDICT: cleaner (relational) UNITS unlocked real sequential structure —")
            print("           RANK collapses under shuffle, RAW does not. Unit quality was the wall.")
        elif k["collapse"] and r["collapse"]:
            print("  VERDICT: both show real order; relational units sharpen/condense the lexicon.")
        else:
            print("  VERDICT: neither shows clean order at this unit granularity — the limiter is")
            print("           deeper than gain-invariance (segmentation / sub-word units).")
    print("=" * 78)


if __name__ == "__main__":
    main()
