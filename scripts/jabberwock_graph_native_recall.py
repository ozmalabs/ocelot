"""GRAPH-NATIVE acoustic recognition, strong enough to SURFACE the words (top-K recall).

No Python recogniser: this uses the agent's OWN graph-native recogniser — Rust feature primitives
(cochleagram / fft_ear / allpole_ear) + graph-native CMVN (the composed CMVN Term) + the combine-all
PRODUCT over the agent's owned cues (each cue's 1-NN exemplar evidence, multiplied — the many_settings
graph Term), over the GraphLexicon exemplar nodes. Python only lays features and evaluates the Terms
(the sanctioned adapter boundary); the recognition DECISION is the graph product/argmax.

The 11% top-K recall (the language faculty had nothing to read) was the single Python embedding. The
agent's combine-all product keeps the true word ranked HIGH when ANY cue agrees, so its TOP-K RECALL
should be far higher — surfacing the word into the lattice for the language faculty. Measured: top-1 and
top-K RECALL on real continuous-speech content words, graph-native CMVN OFF vs ON (the key normalisation).

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_graph_native_recall [topK]
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import substrate_rs as srs
import domains.self_directed_speech_world as SDW
from domains.speech_world_recognizer import GraphLexicon, N_CHANNELS
import domains.many_settings_recognizer as MS
from scripts.multi_source_extract import multi_extract
from scripts.jabberwock_shape_pc_paired import content_words

KREC = 6


def ranked(channels, banked, candidates):
    """The agent's combine-all PRODUCT, returned as a RANKING: per cue the 1-NN exemplar likelihood
    P_c(w|s), summed in log (the product), over the owned cues. Graph-native evidence; rank not argmax.
    Width-agnostic: iterates over the agent's CURRENT front-end cues (len(channels)), so enriching the
    front end (activating repertoire cues) just adds terms to the product."""
    train_words = [w for (w, _v) in banked]
    logp = {w: 0.0 for w in candidates}
    nch = min(len(channels), min(len(v) for (_w, v) in banked)) if banked else 0
    for ci in range(nch):
        Xc = np.stack([vecs[ci] for (_w, vecs) in banked])
        p = MS.channel_likelihood(np.asarray(channels[ci]), Xc, train_words, candidates)
        for w in candidates:
            logp[w] += np.log(p[w] + 1e-12)
    return sorted(candidates, key=lambda w: -logp[w])


def main():
    topK = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    print("=" * 96)
    print("GRAPH-NATIVE recognition (Rust cues + combine-all product Term) — does it SURFACE the words?")
    print("=" * 96)
    train, test = multi_extract()
    words = content_words(train, topK, min_ex=12)
    wi = set(words)
    allex = {}
    for (w, g) in train + test:
        if w in wi:
            allex.setdefault(w, []).append(g)
    by, te = {}, []
    for w in words:
        ex = allex[w]; nho = max(2, len(ex) // 5)
        by[w] = ex[:-nho]; te += [(w, g) for g in ex[-nho:]]
    print(f"  top-{len(words)} CONTENT words (chance {100/max(len(words),1):.0f}%, {len(te)} held-out)\n")
    if len(words) < 6 or len(te) < 25:
        print("  too few."); return

    def evaluate(cmvn):
        s = srs.Substrate()
        if cmvn:
            s.add_node("EarConfig", {"cmvn": 1.0})          # the agent's graph-native CMVN key-normalisation
        lex = GraphLexicon(s)
        for w in words:
            for g in by[w][:25]:
                seg = np.asarray(g, dtype=np.float64)
                if seg.size >= int(0.04 * 8000):
                    lex.bank(SDW.feature_channels(s, seg, 8000), w, source="x")
        banked = lex.banked()
        cands = sorted({w for (w, _v) in banked})
        t1 = tk = tot = 0
        for (w, g) in te:
            ch = SDW.feature_channels(s, np.asarray(g, dtype=np.float64), 8000)
            r = ranked(ch, banked, cands)
            tot += 1
            t1 += int(r[0] == w)
            tk += int(w in r[:KREC])
        return t1 / tot, tk / tot

    a1, ak = evaluate(cmvn=False)
    c1, ck = evaluate(cmvn=True)
    print(f"  {'':<34}{'top-1':>9}{'top-K recall':>16}")
    print(f"  {'graph-native combine-all product':<34}{a1*100:>8.0f}%{ak*100:>15.0f}%")
    print(f"  {'  + graph-native CMVN (key-norm)':<34}{c1*100:>8.0f}%{ck*100:>15.0f}%")

    best_k = max(ak, ck)
    print(f"\n{'=' * 96}")
    if best_k > 0.40:
        print(f"  IT SURFACES THE WORDS: graph-native combine-all product reaches {best_k*100:.0f}% top-{KREC} recall")
        print(f"  (vs 11% from the single Python embedding) — the true word is now in the lattice the language")
        print("  faculty reads. Combining the agent's owned cues, natively, IS the stronger key recovery, no Python.")
    elif best_k > 0.25:
        print(f"  PARTIAL: {best_k*100:.0f}% top-{KREC} recall, well above the 11% Python embedding — the combine-all")
        print("  product surfaces more words, graph-native; richer cues (the FrontEnd repertoire) would lift it further.")
    else:
        print(f"  {best_k*100:.0f}% top-{KREC} recall: even the graph-native combine-all product is recall-bound on this")
        print("  diversity — the 91% key buries the word below K; more cues + speaker normalisation is the lever.")
    print("=" * 96)


if __name__ == "__main__":
    main()
