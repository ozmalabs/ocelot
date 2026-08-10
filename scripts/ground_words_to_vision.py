"""GROUND WORDS TO VISION (clean phones).

First pass bound coarse whole-utterance signs (~5) to ~4000 cues — too coarse.
This uses the CLEAN guide-trained phone inventory: cartoon speech -> clean phones
(frozen alphabet from the pronunciation guides) -> collapse -> TP-trough WORDS,
each timestamped -> bind each recurring WORD to the high-res visual cue ON SCREEN
at that master-clock moment. Then:
  * REAL? mutual information I(word; cue) vs SHUFFLE (permute the cue timeline).
  * MEANING? within-show held-out: learn word->cue early, predict the cue from the
    word LATE — beats the cue-frequency baseline == a heard word predicts its picture.

Run:  python -m scripts.ground_words_to_vision [n_cartoons] [vision_size] [cue_res]
"""
from __future__ import annotations
import bisect
import glob
import math
import os
import random
import subprocess
import sys
import threading
import time
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, "."); sys.path.insert(0, "runners/dsl/python")
import scripts.watch_jellyfin_cortex as W
W.VISION = True
W.FAST_FORWARD = True
N_CART = int(sys.argv[1]) if len(sys.argv) > 1 else 4
W.VISION_SIZE = int(sys.argv[2]) if len(sys.argv) > 2 else 128
CUE_RES = int(sys.argv[3]) if len(sys.argv) > 3 else 48
HOP_S = 0.05
GUIDES = sorted(glob.glob("pronunciation_corpus/*.opus"))[:4]   # inventory saturates fast

import substrate_rs as srs                                       # noqa: E402
from substrate_rs import audio as A, speech as SP, video as V, vision as VIS  # noqa: E402
from substrate_rs import Production, NodePattern                 # noqa: E402
from domains.auditory_cortex import install_auditory_cortex      # noqa: E402
from scripts.jellyfin_world import JellyfinWorld                 # noqa: E402

random.seed(7)
MIN_WORD_COUNT = 5            # only ground words that recur enough to be reliable


def rank16(v):
    # GRAPH-NATIVE: relational ordinal rank = the held substrate op (Rust).
    return np.asarray(srs.Substrate.shape_signature([float(x) for x in v]),
                      dtype=np.float32)


def collapse_t(pt):
    out = []
    for p, t in pt:
        if not out or out[-1][0] != p:
            out.append((p, t))
    return out


def tp_table(seqs):
    uni, fwd = {}, {}
    for seq in seqs:
        for a, b in zip(seq, seq[1:]):
            uni[a] = uni.get(a, 0) + 1
            fwd.setdefault(a, {})[b] = fwd.setdefault(a, {}).get(b, 0) + 1
    return {a: {b: c / uni[a] for b, c in nx.items()} for a, nx in fwd.items()}


def tp(t, a, b):
    return t.get(a, {}).get(b, 1.0)


def segment_t(pt, table):
    """pt=[(phone,time)] -> [(word_tuple, start_time)] at TP troughs."""
    if len(pt) < 2:
        return [(tuple(p for p, _ in pt), pt[0][1])] if pt else []
    ph = [p for p, _ in pt]
    words, cur, cur_t = [], [ph[0]], pt[0][1]
    for i in range(1, len(ph)):
        here = tp(table, ph[i - 1], ph[i])
        prev = tp(table, ph[i - 2], ph[i - 1]) if i >= 2 else 1.0
        nxt = tp(table, ph[i], ph[i + 1]) if i + 1 < len(ph) else 1.0
        if here < prev and here < nxt:
            words.append((tuple(cur), cur_t)); cur, cur_t = [ph[i]], pt[i][1]
        else:
            cur.append(ph[i])
    words.append((tuple(cur), cur_t))
    return words


def active_cue(ctimes, cids, t):
    i = bisect.bisect_right(ctimes, t) - 1
    return cids[i] if i >= 0 else None


def mutual_information(pairs):
    if not pairs:
        return 0.0
    n = len(pairs)
    pa, pc, pac = Counter(a for a, _ in pairs), Counter(c for _, c in pairs), Counter(pairs)
    return sum((nac / n) * math.log2((nac / n) / ((pa[a] / n) * (pc[c] / n)))
               for (a, c), nac in pac.items())


def dur(path):
    try:
        o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", path], capture_output=True, text=True,
                           timeout=60).stdout.strip()
        return float(o) if o else 600.0
    except Exception:
        return 600.0


def main():
    print("=" * 80)
    print(f"GROUND WORDS TO VISION (clean phones) — {len(GUIDES)} guides, {N_CART} cartoons, "
          f"vision {W.VISION_SIZE}px / cue {CUE_RES}")
    print("=" * 80)
    if not GUIDES:
        print("  no pronunciation guides."); return
    s = srs.Substrate()
    A.seed_audio_grammar(s); A.seed_native_codec_grammar(s); SP.seed_speech_grammar(s)
    V.seed_video_grammar(s); VIS.seed_vision_grammar(s); install_auditory_cortex(s)
    for a, e, b in [("CortexStamp", "synchronous_with", "CortexStamp"), ("Frame", "follows", "Frame")]:
        try:
            s.add_production(Production(src=NodePattern(type=a, var="a"), edge_type=e,
                                       tgt=NodePattern(type=b, var="b"), where=None,
                                       weight=None, provenance="g").to_dict())
        except Exception:
            pass
    s.memory_bound(20000, 384 * 1024 * 1024, 3)
    s.memory_disposable_capacity(24 * 1024 * 1024, 3072)
    master = W.MasterClock(fast_forward=True)
    url_box = [None]; commit = threading.Lock()
    acx = W.AudioCortex(s, master, SP.open_lexicon(s, name="online"), url_box, commit)
    acx.frame_chunks = []; acx.frame_ts = []; acx.frame_hop_s = HOP_S
    vcx = W.VideoCortex(s, master, url_box, commit)
    vcx.vision_lex = SP.open_lexicon(s, name="vision"); vcx.vis_feat_size = CUE_RES
    vcx.seen_cues = []
    acx.start(); vcx.start()

    def consume(path, dur_s, wait_video):
        url_box[0] = path; master.start_title(0.0, duration_s=dur_s)
        acx.ff_done = vcx.ff_done = False
        p0 = time.time()
        while not acx.ff_done or (wait_video and not vcx.ff_done):
            if time.time() - p0 > 240:
                break
            time.sleep(0.1)
        with commit:
            s.memory_forget_type("CortexStamp")

    # PHASE 1 — clean phone inventory from the guides
    print("\n  guides -> clean phone inventory:")
    for g in GUIDES:
        consume(g, dur(g), wait_video=False)
    guide_end = len(acx.frame_ts)
    lex = SP.open_lexicon(s, name="clean_phones")
    for v, _ in acx.frame_ts[:guide_end]:
        SP.acquire_sign(s, lex, rank16(v), threshold=0.85)
    lex_size = len(SP.lexicon_signs(s, lex))
    print(f"    {lex_size} clean phone units")

    # PHASE 2 — cartoons: timestamped phones + high-res cues
    print("\n  cartoons (bind speech to sight):")
    jf = JellyfinWorld().connect(); jf.ingest_catalog(s)
    watched = []; cart_bounds = []
    for _ in range(N_CART):
        picks = jf.choose(s, n=1, watched_series=watched)
        if not picks:
            break
        t = picks[0]; watched.append(t["name"])
        eps = jf.episodes(t["id"], limit=1)
        if not eps:
            continue
        a0, c0 = len(acx.frame_ts), len(vcx.seen_cues)
        consume(jf.stream_url(eps[0]["id"]), float(eps[0].get("runtime_s") or 0.0) or 600.0, True)
        cart_bounds.append((t["name"], a0, len(acx.frame_ts), c0, len(vcx.seen_cues)))
        print(f"    {t['name'][:34]:<34} phones+={len(acx.frame_ts)-a0} cues+={len(vcx.seen_cues)-c0}")
    acx.stop(); vcx.stop(); time.sleep(0.3)

    # map each cartoon's frames -> clean phones (timestamped) -> collapse -> phone stream
    per_cart = []
    for name, a0, a1, c0, c1 in cart_bounds:
        pt = []
        for v, t in acx.frame_ts[a0:a1]:
            sg, _ = SP.match_sign(s, lex, rank16(v), threshold=0.85)
            if sg is not None:
                pt.append((sg.value, t))
        cues = sorted(vcx.seen_cues[c0:c1], key=lambda x: x[1])
        per_cart.append((name, collapse_t(pt), [t for _, t in cues], [c for c, _ in cues]))

    # TP table over all cartoon phone streams -> words
    table = tp_table([[p for p, _ in pt] for _, pt, _, _ in per_cart])

    print("\n" + "=" * 80)
    print("GROUNDING RESULTS (clean phone-words -> high-res cues)")
    print("=" * 80)
    # bind WORDS to the active cue
    pairs = []; per_cart_words = []
    for name, pt, ctimes, cids in per_cart:
        words = segment_t(pt, table)
        bound = [(w, active_cue(ctimes, cids, t)) for w, t in words]
        bound = [(w, c) for w, c in bound if c is not None]
        per_cart_words.append((name, [(w, c, t) for (w, t), (_, c) in zip(words, bound)] if False else bound))
        pairs.extend(bound)
    wc = Counter(w for w, _ in pairs)
    rec = {w for w, c in wc.items() if c >= MIN_WORD_COUNT}
    rec_pairs = [(w, c) for w, c in pairs if w in rec]
    print(f"  {len(pairs)} word->cue bindings; {len(wc)} word types, "
          f"{len(rec)} recurring (>= {MIN_WORD_COUNT}x); "
          f"{len(set(c for _, c in rec_pairs))} cues")

    mi = mutual_information(rec_pairs)
    cs = [c for _, c in rec_pairs]; random.shuffle(cs)
    mi_sh = mutual_information([(w, c) for (w, _), c in zip(rec_pairs, cs)])
    print(f"  I(word; sight) = {mi:.3f} bits  shuffled = {mi_sh:.3f}  -> "
          f"{'REAL binding' if mi > 1.5 * max(mi_sh, 1e-6) else 'weak'}")

    # within-show held-out: learn word->cue early, predict cue LATE
    hit = tot = base = 0
    for name, pt, ctimes, cids in per_cart:
        words = segment_t(pt, table)
        bound = [(w, active_cue(ctimes, cids, t)) for w, t in words]
        bound = [(w, c) for w, c in bound if c is not None]
        if len(bound) < 40:
            continue
        cut = int(0.7 * len(bound))
        m = defaultdict(Counter)
        for w, c in bound[:cut]:
            m[w][c] += 1
        top = {w: cc.most_common(1)[0][0] for w, cc in m.items()}
        bc = Counter(c for _, c in bound[:cut]).most_common(1)
        bcue = bc[0][0] if bc else None
        for w, c in bound[cut:]:
            tot += 1
            hit += (w in top and top[w] == c)
            base += (c == bcue)
    acc = hit / tot if tot else 0.0
    bacc = base / tot if tot else 0.0
    print(f"\n  WITHIN-SHOW held-out (word predicts its picture LATE): {acc:.3f} "
          f"vs cue-frequency baseline {bacc:.3f} ({acc/max(bacc,1e-9):.2f}x)")

    print("\n  strongest groundings (recurring word -> dominant on-screen cue):")
    co = defaultdict(Counter)
    for w, c in rec_pairs:
        co[w][c] += 1
    for w, cc in sorted(co.items(), key=lambda kv: -sum(kv[1].values()))[:8]:
        n = sum(cc.values()); tc, tn = cc.most_common(1)[0]
        print(f"    word {w}: {n}x, {100*tn/n:.0f}% with cue #{tc} ({len(cc)} cues)")

    print("\n  VERDICT:", end=" ")
    if mi > 1.5 * max(mi_sh, 1e-6) and acc > bacc:
        print("clean phone-WORDS bind to specific sight (MI>>shuffle) AND a word "
              "predicts its picture above baseline -> GROUNDED.")
    elif mi > 1.5 * max(mi_sh, 1e-6):
        print("real word<->sight binding (MI>>shuffle); held-out prediction modest.")
    else:
        print("still weak — see numbers.")
    print("=" * 80)


if __name__ == "__main__":
    main()
