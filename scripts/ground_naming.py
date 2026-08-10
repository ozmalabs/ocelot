"""GROUND ON NAMING DATA — where the sound NAMES the visible thing.

Cartoon co-occurrence failed to ground (speech isn't about the on-screen scene).
Naming / flashcard videos ARE ostensive: the word is spoken WHILE its object is
shown ("apple" + apple picture), repeatedly. This builds clean phone units from
the naming speech, segments WORDS, binds each timestamped word to the high-res
visual cue on screen, and tests:
  * REAL?  I(word; cue) vs SHUFFLE (permute the cue timeline).
  * MEANING?  within-video held-out: learn word->cue early, predict the cue from
    the word LATE — beats the cue-frequency baseline == the heard word predicts the
    picture of the named thing.

Run:  python -m scripts.ground_naming [vision_size] [cue_res]
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
# read OUR args first, then hide them — watch_jellyfin_cortex parses sys.argv at import.
_a = sys.argv[:]
_VS = int(_a[1]) if len(_a) > 1 else 128
CUE_RES = int(_a[2]) if len(_a) > 2 else 48                 # 48px/0.92 = best (real MI)
CORPUS = _a[3] if len(_a) > 3 else "naming_corpus"
HOP_S = 0.05
VIDEOS = sorted(glob.glob(f"{CORPUS}/*"))
sys.argv = [_a[0]]
import scripts.watch_jellyfin_cortex as W
W.VISION = True
W.FAST_FORWARD = True
W.VISION_SIZE = _VS

import substrate_rs as srs                                       # noqa: E402
from substrate_rs import audio as A, speech as SP, video as V, vision as VIS  # noqa: E402
from substrate_rs import Production, NodePattern                 # noqa: E402
from domains.auditory_cortex import install_auditory_cortex      # noqa: E402

random.seed(7)
MIN_WORD = 4


def rank16(v):
    # GRAPH-NATIVE: relational ordinal rank = the held substrate op
    # (Substrate.shape_signature, Rust), not numpy. World-adapter marshals only.
    return np.asarray(srs.Substrate.shape_signature([float(x) for x in v]),
                      dtype=np.float32)


def collapse_t(pt):
    out = []
    for p, t in pt:
        if not out or out[-1][0] != p:
            out.append((p, t))
    return out


def word_feature(vecs):
    """A WORD's acoustic fingerprint: pool its frames into 4 time windows of 16
    bands, rank each window (gain-invariant) -> the same spoken word maps to the
    same word-sign across repeats, despite phone-segmentation jitter."""
    if not vecs:
        return None
    a = np.stack(vecs)
    T, nb = a.shape[0], 4
    feat = np.empty(16 * nb, dtype=np.float32)
    for w in range(nb):
        seg = a[w * T // nb:(w + 1) * T // nb] if T >= nb else a
        bv = seg.mean(0) if len(seg) else a.mean(0)
        feat[w * 16:(w + 1) * 16] = srs.Substrate.shape_signature([float(x) for x in bv])
    return feat


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


def active_cue(ct, ci, t):
    i = bisect.bisect_right(ct, t) - 1
    return ci[i] if i >= 0 else None


def mi(pairs):
    if not pairs:
        return 0.0
    n = len(pairs)
    pa, pc, pac = Counter(a for a, _ in pairs), Counter(c for _, c in pairs), Counter(pairs)
    return sum((v / n) * math.log2((v / n) / ((pa[a] / n) * (pc[c] / n)))
               for (a, c), v in pac.items())


def dur(p):
    try:
        o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", p], capture_output=True, text=True,
                           timeout=60).stdout.strip()
        return float(o) if o else 600.0
    except Exception:
        return 600.0


def main():
    print("=" * 80)
    print(f"GROUND ON NAMING DATA — {len(VIDEOS)} flashcard/vocab videos, "
          f"vision {W.VISION_SIZE}px / cue {CUE_RES}")
    print("=" * 80)
    if not VIDEOS:
        print("  no naming_corpus/ videos."); return
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
    vcx.vis_match_threshold = 0.90          # cue merge threshold
    vcx.vis_object_isolate = True          # cue = the NAMED object (background subtracted)
    vcx.vis_relational = True              # OBJECT-SIGN: shape_signature(foreground) -> invariant
                                           # object identity (the agent's own audio-invariance op,
                                           # recomposed onto vision now that it owns both)
    vcx.seen_cues = []
    acx.start(); vcx.start()

    per_video = []
    for path in VIDEOS:
        a0, c0 = len(acx.frame_ts), len(vcx.seen_cues)
        url_box[0] = path; master.start_title(0.0, duration_s=dur(path))
        acx.ff_done = vcx.ff_done = False
        p0 = time.time()
        while not (acx.ff_done and vcx.ff_done):
            if time.time() - p0 > 240:
                break
            time.sleep(0.1)
        with commit:
            s.memory_forget_type("CortexStamp")
        per_video.append((os.path.basename(path)[:40], a0, len(acx.frame_ts), c0, len(vcx.seen_cues)))
        print(f"  {os.path.basename(path)[:46]:<46} phones+={len(acx.frame_ts)-a0} "
              f"cues+={len(vcx.seen_cues)-c0}", flush=True)
    acx.stop(); vcx.stop(); time.sleep(0.3)

    # clean phone lexicon from the naming speech
    lex = SP.open_lexicon(s, name="phones")
    for v, _ in acx.frame_ts:
        SP.acquire_sign(s, lex, rank16(v), threshold=0.85)
    lex_size = len(SP.lexicon_signs(s, lex))

    # per video: keep RAW frames + collapsed phones (for TP word boundaries) + cues
    wlex = SP.open_lexicon(s, name="words")
    streams = []
    for name, a0, a1, c0, c1 in per_video:
        raw = list(acx.frame_ts[a0:a1])
        pt = []
        for v, t in raw:
            sg, _ = SP.match_sign(s, lex, rank16(v), threshold=0.85)
            if sg is not None:
                pt.append((sg.value, t))
        cues = sorted(vcx.seen_cues[c0:c1], key=lambda x: x[1])
        streams.append((name, raw, collapse_t(pt),
                        [t for _, t in cues], [c for c, _ in cues]))
    table = tp_table([[p for p, _ in cpt] for _, _, cpt, _, _ in streams])

    print("\n" + "=" * 80)
    print("GROUNDING ON NAMING DATA (acquired word-signs)")
    print("=" * 80)
    # words = TP-trough spans; each acquired as a WORD-SIGN by acoustic similarity
    per_bound = []
    for name, raw, cpt, ct, ci in streams:
        words = segment_t(cpt, table)
        ftimes = [t for _, t in raw]; fvecs = [v for v, _ in raw]
        vb = []
        for i, (_, t0) in enumerate(words):
            t1 = words[i + 1][1] if i + 1 < len(words) else (ftimes[-1] if ftimes else t0)
            lo = bisect.bisect_left(ftimes, t0); hi = max(lo + 1, bisect.bisect_right(ftimes, t1))
            feat = word_feature(fvecs[lo:hi])
            if feat is None:
                continue
            ws, _ = SP.acquire_sign(s, wlex, feat, threshold=0.90)  # word-sign granularity
            cu = active_cue(ct, ci, t0)
            if ws is not None and cu is not None:
                vb.append((ws.value, cu))
        per_bound.append(vb)
    pairs = [p for vb in per_bound for p in vb]
    wc = Counter(w for w, _ in pairs)
    rec = {w for w, c in wc.items() if c >= MIN_WORD}
    rp = [(w, c) for w, c in pairs if w in rec]
    print(f"  {lex_size} phones; {len(pairs)} word->cue bindings; {len(wc)} word types, "
          f"{len(rec)} recurring (>= {MIN_WORD}x); {len(set(c for _, c in rp))} cues")
    m = mi(rp)
    cs = [c for _, c in rp]; random.shuffle(cs)
    msh = mi([(w, c) for (w, _), c in zip(rp, cs)])
    print(f"  I(word; sight) = {m:.3f} bits   shuffled = {msh:.3f}   -> "
          f"{'REAL binding' if m > 1.5 * max(msh, 1e-6) else 'weak'}")

    # PURITY: how concentrated is each recurring word's cue distribution?
    # (a grounded word -> one dominant cue). Mean top-cue fraction vs shuffle.
    cow = defaultdict(Counter)
    for w, c in rp:
        cow[w][c] += 1
    purity = np.mean([cc.most_common(1)[0][1] / sum(cc.values()) for cc in cow.values()])
    shp = defaultdict(Counter)
    for (w, _), c in zip(rp, cs):
        shp[w][c] += 1
    sh_purity = np.mean([cc.most_common(1)[0][1] / sum(cc.values()) for cc in shp.values()])
    print(f"  cue PURITY (mean top-cue fraction per recurring word) = {purity:.3f} "
          f"vs shuffle {sh_purity:.3f}  ({purity/max(sh_purity,1e-9):.2f}x)")

    # within-video held-out (word-sign predicts its picture LATE)
    hit = tot = base = 0
    for bound in per_bound:
        if len(bound) < 30:
            continue
        cut = int(0.7 * len(bound))
        mtop = defaultdict(Counter)
        for w, c in bound[:cut]:
            mtop[w][c] += 1
        top = {w: cc.most_common(1)[0][0] for w, cc in mtop.items()}
        bc = Counter(c for _, c in bound[:cut]).most_common(1)
        bcue = bc[0][0] if bc else None
        for w, c in bound[cut:]:
            tot += 1; hit += (w in top and top[w] == c); base += (c == bcue)
    acc = hit / tot if tot else 0.0
    bacc = base / tot if tot else 0.0
    print(f"\n  WITHIN-VIDEO held-out (word predicts its picture LATE): {acc:.3f} "
          f"vs cue-frequency baseline {bacc:.3f} ({acc/max(bacc,1e-9):.2f}x)")

    co = defaultdict(Counter)
    for w, c in rp:
        co[w][c] += 1
    print("\n  strongest groundings (recurring sound-word -> dominant on-screen cue):")
    for w, cc in sorted(co.items(), key=lambda kv: -max(kv[1].values()))[:10]:
        n = sum(cc.values()); tc, tn = cc.most_common(1)[0]
        print(f"    word {w}: {n}x, {100*tn/n:.0f}% -> cue #{tc} ({len(cc)} cues)")

    print("\n  VERDICT:", end=" ")
    if m > 1.5 * max(msh, 1e-6) and acc > bacc:
        print("on NAMING data the sound binds to the named sight (MI>>shuffle) AND a "
              "word predicts its picture above baseline -> GROUNDED.")
    elif m > 1.5 * max(msh, 1e-6):
        print("real word<->sight binding (MI>>shuffle); held-out modest.")
    else:
        print("still weak — see numbers.")
    print("=" * 80)


if __name__ == "__main__":
    main()
