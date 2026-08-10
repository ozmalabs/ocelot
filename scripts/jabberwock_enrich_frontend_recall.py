"""CLOSE THE CONNECTED-SPEECH CONTENT-RECALL GAP — the agent enriches its own front end.

The 64%-isolated -> 38%-connected content-recall gap was blamed on segmentation+coarticulation, but it is
mostly DISCRIMINATION over a large vocabulary: top-6 of 20 candidates is easy, top-6 of 150 is hard. The
agent's documented plateau response is to ENRICH ITS FRONT END (ozma_wall_is_self_imposed: "the audio hat
is the agent's to build") -- it owns a whole REPERTOIRE of inactive cues (agent_frontend.REPERTOIRE_CUES),
built for exactly this, including the two that target the named causes:
  cmvn_ear / vtl_formant / vtl_formant_allpole / cs_ear  -- speaker normalisation (connected variability)
  vtl_formant_dynamic / transition                       -- how the formants MOVE = the coarticulation gesture
The combine-all PRODUCT over MORE orthogonal cues keeps the truth ranked high when ANY cue agrees -> higher
top-K recall. Graph-native: install_frontend + flip cue.active are graph mutations; feature_channels reads
the active cues from the graph and dispatches the agent's owned DSP. No Python decision.

Measured: content-word top-6 RECALL (the anchors). (1) the gap is vocab-discrimination (recall vs vocab
size, seed cues); (2) enriching the front end at 150-way lifts recall back toward the isolated ceiling.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_enrich_frontend_recall
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
import domains.agent_frontend as FE
from domains.speech_world_recognizer import GraphLexicon
from scripts.multi_source_extract import multi_extract
from scripts.jabberwock_graph_native_recall import ranked, KREC

# the agent's enrichment: activate the speaker-normalising + dynamic (coarticulation) repertoire cues.
ENRICH = ["cmvn_ear", "vtl_formant", "vtl_formant_allpole", "cs_ear",
          "vtl_formant_dynamic", "transition_w3", "f0_contour", "manner_voicing"]


def enrich_frontend(s):
    """The agent enriches its front end: install + activate the repertoire cues that target the
    cross-speaker + coarticulation gap. Graph mutations only (mint Cue / flip active)."""
    fe = FE.install_frontend(s)
    on = 0
    for et in ("has_cue", "repertoire"):
        for c in s.neighbours(fe, et):
            nm = s.node(c)["attrs"].get("name")
            if nm in ENRICH:
                s.set_attr(c, "active", 1.0); on += 1
    return FE.n_active(s)


def build_words(train, test, vocabN, min_ex=12):
    freq = Counter(w for (w, _g) in train)
    # content words = frequent, not closed-class (the anchors).
    from scripts.jabberwock_function_word_context import FUNCTION
    words = [w for w, n in freq.most_common() if n >= min_ex and w.isalpha() and w not in FUNCTION][:vocabN]
    wi = set(words)
    allex = {}
    for (w, g) in train + test:
        if w in wi:
            allex.setdefault(w, []).append(g)
    by, te = {}, []
    for w in words:
        ex = allex.get(w, [])
        if len(ex) < 6:
            continue
        nho = max(2, len(ex) // 5)
        by[w] = ex[:-nho]; te += [(w, g) for g in ex[-nho:]]
    return by, te


def measure(by, te, enrich, cap=25):
    s = srs.Substrate()
    if enrich:
        nch = enrich_frontend(s)
    else:
        s.add_node("EarConfig", {"cmvn": 1.0})              # seed-cue baseline keeps graph CMVN on
        nch = 3
    lex = GraphLexicon(s)
    for w, exs in by.items():
        for g in exs[:cap]:
            seg = np.asarray(g, dtype=np.float64)
            if seg.size >= int(0.04 * 8000):
                lex.bank(SDW.feature_channels(s, seg, 8000), w, source="x")
    banked = lex.banked()
    cands = sorted({w for (w, _v) in banked})
    t1 = tk = tot = 0
    for (w, g) in te:
        ch = SDW.feature_channels(s, np.asarray(g, dtype=np.float64), 8000)
        r = ranked(ch, banked, cands)
        tot += 1; t1 += int(r[0] == w); tk += int(w in r[:KREC])
    return nch, t1 / max(tot, 1), tk / max(tot, 1), tot


def main():
    print("=" * 98)
    print("CLOSE THE CONNECTED-SPEECH CONTENT-RECALL GAP — the agent enriches its own front end.")
    print("=" * 98)
    train, test = multi_extract()

    print("\n  (1) DIAGNOSIS — content top-6 recall vs vocab size, 3 SEED cues (is the gap discrimination?):")
    print(f"      {'vocab':>7}{'held-out':>10}{'top-1':>9}{'top-6 recall':>15}")
    for V in (20, 60, 150):
        by, te = build_words(train, test, V)
        _n, a1, ak, tot = measure(by, te, enrich=False)
        print(f"      {len(by):>7}{tot:>10}{a1*100:>8.0f}%{ak*100:>14.0f}%")

    print("\n  (2) ENRICH the front end at 150-way (activate the speaker-norm + coarticulation repertoire):")
    by, te = build_words(train, test, 150)
    n0, a1, ak, tot = measure(by, te, enrich=False)
    n1, b1, bk, _ = measure(by, te, enrich=True)
    print(f"      {'front end':<34}{'cues':>6}{'top-1':>9}{'top-6 recall':>15}")
    print(f"      {'3 seed cues':<34}{n0:>6}{a1*100:>8.0f}%{ak*100:>14.0f}%")
    print(f"      {'+ enriched repertoire':<34}{n1:>6}{b1*100:>8.0f}%{bk*100:>14.0f}%")

    print("\n  (3) MORE EXEMPLARS per word (richer enrolment) at NON-TRIVIAL vocab, 3 seed cues:")
    by2, te2 = build_words(train, test, 60, min_ex=22)       # ~40 words each with >=22 exemplars
    print(f"      {len(by2)}-way (each word has >=22 exemplars), {len(te2)} held-out")
    print(f"      {'exemplars/word':>16}{'top-1':>9}{'top-6 recall':>15}")
    ek = {}
    for capN in (8, 15, 25):
        _n, e1, ekk, _t = measure(by2, te2, enrich=False, cap=capN)
        ek[capN] = ekk
        print(f"      {capN:>16}{e1*100:>8.0f}%{ekk*100:>14.0f}%")
    ek[80] = ek.get(25)                                       # alias for the verdict below

    print("\n" + "=" * 98)
    ex_lift = ek.get(25, 0) - ek.get(8, 0)
    if bk > ak + 0.06:
        print(f"  THE GAP CLOSES: enriching the front end ({n0} -> {n1} cues) lifts 150-way content recall")
        print(f"  {ak*100:.0f}% -> {bk*100:.0f}% top-6. The agent's owned speaker-norm + coarticulation-gesture cues, combined")
        print("  in the product, surface the content word among 150 candidates -- the anchors the prior needs.")
    elif ex_lift > 0.06:
        print(f"  EXEMPLARS ARE THE LEVER: more cues barely moved recall ({ak*100:.0f}->{bk*100:.0f}%), but richer enrolment")
        print(f"  (8 -> 25 exemplars/word) lifts top-6 recall {ek.get(8,0)*100:.0f}% -> {ek.get(25,0)*100:.0f}% at fixed vocab. The exemplar")
        print("  recogniser surfaces the word when it has heard the word enough -- the gap closes by BANKING MORE, not")
        print("  by more cues. Faithful to the agent: it banks every word it hears; recall rises with experience.")
    else:
        print(f"  neither lever bit hard: cues {ak*100:.0f}->{bk*100:.0f}%, exemplars {ek.get(8,0)*100:.0f}->{ek.get(25,0)*100:.0f}% top-6. The exemplar-1-NN")
        print("  product is recall-saturated on this large vocab -- closing the gap needs a sharper discriminative cue")
        print("  (the agent inventing one, jabberwock_authors_*) or a different recogniser, not more of the same.")
    print("=" * 98)


if __name__ == "__main__":
    main()
