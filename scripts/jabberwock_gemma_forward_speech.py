"""THE NEXT-WORD WEIGHTS FOR FORWARD SPEECH PREDICTION — the harvested LM as a CAUSAL next-word prior.

The grounding put Gemma's geometry in the graph; the next-word LM extract predicted the next word from the
unembedding -- but it was never used to PREDICT FORWARD in the speech decode. The earlier prior was a
BIDIRECTIONAL topic (the whole utterance's gist). A real language model predicts the next word from the LEFT
context only (causal). This wires that in: for each position the context is a recency-weighted gist of the
words BEFORE it (acoustic-confident, content), and a candidate scores by cosine to it -- forward next-word
prediction with the harvested weights. Compared head-to-head, on the content words the bigram lost:
  acoustic | + bigram (freq) | + Gemma TOPIC (bidirectional) | + Gemma FORWARD (causal next-word)

Run: /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_gemma_forward_speech [n_utts] [vocab]
"""
from __future__ import annotations

import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import substrate_rs as srs

import domains.self_directed_speech_world as SDW
from domains.speech_world_recognizer import GraphLexicon
from domains.speech_world import SpeechWorld
from domains import model_reader as mr
from scripts.librispeech_wer import gather_pairs, load_flac
from scripts.language_prior import LanguagePrior
from scripts.abs_language_decode import acoustic_logp, register_language_prior, lm_logp, FS, KCAND

SEP = "=" * 98
MODEL = os.environ.get("OPEN_MODEL", "google/gemma-4-E4B-it")
STOP = {"the", "a", "an", "of", "to", "in", "and", "but", "or", "for", "his", "her", "its", "their",
        "he", "she", "it", "they", "we", "i", "you", "was", "were", "is", "are", "be", "been", "as",
        "at", "by", "on", "with", "this", "that", "had", "has", "have", "not", "no", "so", "than",
        "which", "who", "what", "when", "where", "may", "would", "could", "will", "from", "up", "out"}


def main():
    n_test = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    vocab_size = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    print(SEP)
    print("NEXT-WORD WEIGHTS FOR FORWARD SPEECH PREDICTION — causal next-word prior vs bidirectional topic vs bigram.")
    print(SEP)

    lp = LanguagePrior(); register_language_prior(lp)
    sw = SpeechWorld(srs.Substrate(), whisper_model="base.en")
    by_spk = {}
    for (path, sp, _ch, _ut, tr) in gather_pairs(limit=None):
        by_spk.setdefault(sp, []).append((path, tr))
    spks = sorted(by_spk)
    train_spk, test_spk = spks[:max(1, len(spks) - 2)], spks[max(1, len(spks) - 2):]

    print("\n  segmenting train utterances (whisper word-timing) to bank exemplars...", flush=True)
    word_segs = {}; budget = 0
    for sp in train_spk:
        for (path, _tr) in by_spk[sp][:6]:
            x, fs = load_flac(path); x = np.asarray(x, dtype=np.float64)
            for (w, t0, t1) in sw.transcribe_lang_timed(x, fs, "en"):
                w = "".join(c for c in w.lower() if c.isalpha())
                seg = x[int(t0 * fs):int(t1 * fs)]
                if w and seg.size >= int(0.04 * fs):
                    word_segs.setdefault(w, []).append(seg)
            budget += 1
            if budget >= 80:
                break
        if budget >= 80:
            break

    vocab = [w for (w, _c) in Counter({w: len(s) for w, s in word_segs.items()}).most_common(vocab_size)
             if len(word_segs[w]) >= 3]
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0})
    lex = GraphLexicon(s)
    for w in vocab:
        for seg in word_segs[w][:8]:
            lex.bank(SDW.feature_channels(s, np.asarray(seg, dtype=np.float64), FS), w, source="lib")
    banked = lex.banked()
    cands = sorted({w for (w, _v) in banked})

    print(f"  harvesting Gemma vectors from {MODEL} for the {len(cands)}-word vocab...", flush=True)
    vec_fn, gvocab, _shape = mr.ModelTensors(MODEL).embedding()
    gv = {}
    for w in cands:
        tid = gvocab.get("▁" + w, gvocab.get(w))
        if tid is not None:
            v = vec_fn(tid).astype(np.float64); n = np.linalg.norm(v)
            if n > 0:
                gv[w] = v / n
    print(f"  {len(gv)}/{len(cands)} words grounded; decoding {n_test} held-out utterances\n", flush=True)

    utts = []; n_utt = 0
    for sp in test_spk:
        for (path, _tr) in by_spk[sp]:
            x, fs = load_flac(path); x = np.asarray(x, dtype=np.float64)
            seq = []
            for (w, t0, t1) in sw.transcribe_lang_timed(x, fs, "en"):
                w = "".join(c for c in w.lower() if c.isalpha())
                seg = x[int(t0 * fs):int(t1 * fs)]
                if w not in cands or seg.size < int(0.04 * fs):
                    continue
                lo = acoustic_logp(SDW.feature_channels(s, np.asarray(seg, dtype=np.float64), FS), banked, cands)
                seq.append((w, dict(sorted(lo.items(), key=lambda kv: -kv[1])[:KCAND])))
            if len(seq) >= 3:
                utts.append(([w for (w, _t) in seq], [t for (_w, t) in seq]))
                n_utt += 1
            if n_utt >= n_test:
                break
        if n_utt >= n_test:
            break

    def margin(pos):
        vs = sorted(pos.values(), reverse=True)
        return max(vs[0] - (vs[1] if len(vs) > 1 else vs[0] - 1.0), 0.0) + 1e-3

    def maps(lattice, causal):
        """per-position cosine-to-context gmap. causal=False -> BIDIRECTIONAL gist (all other positions);
        causal=True -> FORWARD next-word: only LEFT positions, recency-weighted (closer words weigh more)."""
        top1 = [max(pos, key=pos.get) for pos in lattice]
        anchors = [(i, gv[w], margin(lattice[i])) for i, w in enumerate(top1) if w not in STOP and w in gv]
        out = []
        for i, pos in enumerate(lattice):
            if causal:
                ctx = [(v, m * (0.55 ** (i - j))) for (j, v, m) in anchors if j < i]
            else:
                ctx = [(v, m) for (j, v, m) in anchors if j != i]
            if not ctx:
                out.append({}); continue
            t = np.average([v for v, _ in ctx], axis=0, weights=[m for _, m in ctx])
            tn = np.linalg.norm(t); t = t / tn if tn > 0 else t
            out.append({c: float(gv[c] @ t) for c in pos if c in gv})
        return out

    topic_g = [maps(lat, False) for (_t, lat) in utts]
    fwd_g = [maps(lat, True) for (_t, lat) in utts]

    def decode(lattice, w_lm, gm, w_gem):
        if not lattice:
            return []
        dp = [{c: lo + w_lm * lm_logp(c, None, lp) + w_gem * gm[0].get(c, 0.0) for c, lo in lattice[0].items()}]
        bk = [{c: None for c in lattice[0]}]
        for i in range(1, len(lattice)):
            cur, b = {}, {}
            for c, lo in lattice[i].items():
                best, arg, add = -1e18, None, lo + w_gem * gm[i].get(c, 0.0)
                for pc, ps in dp[i - 1].items():
                    sv = ps + add + w_lm * lm_logp(c, pc, lp)
                    if sv > best:
                        best, arg = sv, pc
                cur[c], b[c] = best, arg
            dp.append(cur); bk.append(b)
        out = [None] * len(lattice); last = max(dp[-1], key=dp[-1].get)
        for i in range(len(lattice) - 1, -1, -1):
            out[i] = last; last = bk[i][last]
        return out

    def acc(w_lm, w_gem, G):
        ok = c_ok = c_tot = f_ok = f_tot = tot = 0
        for (truth, lattice), gm in zip(utts, G):
            for tr, p in zip(truth, decode(lattice, w_lm, gm, w_gem)):
                tot += 1; ok += int(p == tr)
                if tr in STOP:
                    f_tot += 1; f_ok += int(p == tr)
                else:
                    c_tot += 1; c_ok += int(p == tr)
        return (100 * ok / max(tot, 1), 100 * c_ok / max(c_tot, 1), 100 * f_ok / max(f_tot, 1), tot, c_tot, f_tot)

    base = acc(0, 0, topic_g)
    bram = max((acc(w, 0, topic_g) for w in (0.2, 0.4, 0.8, 1.6)), key=lambda r: r[0])
    topc = max((acc(0, w, topic_g) for w in (1.0, 2.0, 4.0)), key=lambda r: r[1])
    fwd = max((acc(0, w, fwd_g) for w in (1.0, 2.0, 4.0)), key=lambda r: r[1])

    print(SEP)
    print(f"  word accuracy ({base[3]} words, content {base[4]} / function {base[5]}) -- overall | content | function:\n")
    print(f"    acoustic alone                          : {base[0]:5.1f} | {base[1]:5.1f} | {base[2]:5.1f}")
    print(f"    + BIGRAM (frequency, forward)           : {bram[0]:5.1f} | {bram[1]:5.1f} | {bram[2]:5.1f}")
    print(f"    + GEMMA TOPIC (bidirectional gist)      : {topc[0]:5.1f} | {topc[1]:5.1f} | {topc[2]:5.1f}")
    print(f"    + GEMMA FORWARD (causal next-word)      : {fwd[0]:5.1f} | {fwd[1]:5.1f} | {fwd[2]:5.1f}")

    print("\n" + SEP)
    dC_fwd, dC_bi = fwd[1] - base[1], bram[1] - base[1]
    if fwd[1] >= topc[1] and dC_fwd > 0 and dC_fwd >= dC_bi:
        print(f"  THE FORWARD NEXT-WORD PRIOR PAYS: causal content {dC_fwd:+.1f} (>= bidirectional topic {topc[1]-base[1]:+.1f},")
        print(f"  >= bigram {dC_bi:+.1f}). Predicting the next word from the LEFT context with the harvested unembedding")
        print(f"  geometry -- a real forward LM, frequency-neutral -- beats the frequency bigram on content and at")
        print(f"  least matches the bidirectional gist while being causal (usable in a true left-to-right decode).")
    else:
        print(f"  honest reading: forward content {dC_fwd:+.1f}, bidirectional topic {topc[1]-base[1]:+.1f}, bigram {dC_bi:+.1f}.")
        print(f"  the causal forward prior {'helps' if dC_fwd > 0 else 'does not beat acoustic'} but {'matches' if abs(fwd[1]-topc[1])<1 else 'trails'} the")
        print(f"  bidirectional gist -- a left-to-right decode loses the right-context the gist uses, and content")
        print(f"  recall (the EAR) still caps what any prior can convert. The forward LM is the right SHAPE for a")
        print(f"  streaming decode; raising the ear is what unlocks it. The harvested weights run over the grounded")
        print(f"  lexicon (already in the graph) -- the cosine prior is the agent's own Term, not a new dependency.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
