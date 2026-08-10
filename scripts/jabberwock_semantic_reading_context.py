"""COMPREHENSION-IN-READING-CONTEXT (graph-native) — top-down disambiguation, measured.

The reading payoff where denotation meets the language prior: the word-superiority / Interactive-
Activation effect. An individually AMBIGUOUS symbol (its best VISUAL match is the wrong concept) is read
correctly because the reading CONTEXT primes the symbol that fits. Graph-native via SPREADING ACTIVATION:
a recognised symbol activates its concept (activate_recognised), activation spreads along the lexicon
(prime_successors over can_follow edges) to PRIME the symbols that may come next, and the context-aware
reading Term adds lam * the candidate's context_primed to its visual score — so a primed-but-visually-
second symbol can win. The priming IS the Rules (seeds/semantic_reading_context.json); the lexicon is
graph data (can_follow edges); the host only stages the sequence and reads back.

The demo finds a NATURAL confusion (a writer of symbol T whose nearest gallery exemplar is the WRONG
symbol W, with T only second), sets a lexicon where the preceding symbol P expects T (P can_follow T),
reads P (which primes T), then reads the ambiguous mark with and without context — context flips W->T.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_semantic_reading_context
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np

import substrate_rs as srs
from domains import omniglot_world as ow
from domains.recognition_graph import (predict_pointset_term, predict_context_term,
                                        _PointSetDist, _Attr, _V)

SEP = "=" * 92
WHOLE_N, GALLERY = 64, 12


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


_DIST = _Pred(_PointSetDist(_Attr(_V("s"), "axs_heard_feat"), _Attr(_V("w"), "axs_synth_feat")))


def main():
    print(SEP)
    print("COMPREHENSION-IN-READING-CONTEXT (graph-native): a symbol whose best VISUAL match is WRONG is")
    print("read correctly because the context primes the right one — spreading activation, top-down + bottom-up.")
    print(SEP)
    if not ow.have_data("evaluation"):
        print(f"\n  Omniglot strokes not found under {ow.DATA}.")
        return 1

    by_alph = {a: ow.characters(a, "evaluation") for a in ow.alphabets("evaluation")}
    by_alph = {a: cs for a, cs in by_alph.items() if len(cs) >= GALLERY}
    alph = sorted(by_alph)[0]
    ch = by_alph[alph]
    wc: dict[str, np.ndarray] = {}

    def whole(p):
        if p not in wc:
            wc[p] = ow.trajectory(p, WHOLE_N, per_stroke=True)
        return wc[p]

    names = [os.path.relpath(ch[j], ow.split_dir("evaluation")).replace(os.sep, "/") for j in range(GALLERY)]
    short = [n.split("/")[-1] for n in names]

    def fresh_gallery(s):
        cand = {}
        for j in range(GALLERY):
            c = s.add_node("Concept", {"is_word": 1.0})
            s.set_attr(c, "axs_synth_feat", whole(ow.drawings(ch[j])[0]).tolist())
            s.set_attr(c, "name", names[j]); s.set_attr(c, "context_primed", 0.0)
            cand[j] = c
        return cand

    def ranked(s, cand, feat):
        m = s.add_node("Mark", {}); s.set_attr(m, "axs_heard_feat", feat.tolist())
        out = sorted((s.evaluate(_DIST, {"s": m, "w": cand[j]}), j) for j in cand)
        s.remove_node(m)
        return out

    # ---- find a NATURAL confusion: a writer of T whose top-1 visual is W != T, with T second ----
    s_scan = srs.Substrate()
    cand_scan = fresh_gallery(s_scan)
    found = None
    for j in range(GALLERY):
        fs = ow.drawings(ch[j])
        for d in range(1, min(len(fs), 8)):
            r = ranked(s_scan, cand_scan, whole(fs[d]))
            if r[0][1] != j and r[1][1] == j:
                found = {"T": j, "W": r[0][1], "feat": whole(fs[d]),
                         "margin": r[1][0] - r[0][0], "rank": r[:3]}
                break
        if found:
            break
    if not found:
        print("\n  (no natural top-1 confusion in this gallery — try another script)")
        return 0
    T, W = found["T"], found["W"]
    P = next(k for k in range(GALLERY) if k not in (T, W))    # an unambiguous preceding symbol
    print(f"\n  ambiguous symbol: a writer of '{short[T]}' — its ranked VISUAL matches:")
    for di, jj in found["rank"]:
        tag = " <- WRONG (visual best)" if jj == W else (" <- truth (only 2nd)" if jj == T else "")
        print(f"      {short[jj]:>14}  dist {di:.3f}{tag}")
    print(f"  context: lexicon says after '{short[P]}', '{short[T]}' is expected  ('{short[P]}' can_follow '{short[T]}')")

    # ---- stage the read: P primes T via the Rules, then read the ambiguous mark with/without context ----
    s = srs.Substrate()
    sa = s.add_node("Agent", {})
    s._inner.load_seed_manifest(json.loads((Path(ROOT) / "seeds" / "semantic_reading_context.json").read_text()), sa)
    cand = fresh_gallery(s)
    s.add_edge_unchecked(cand[P], "can_follow", cand[T])      # the lexicon (graph data)

    pm = s.add_node("Mark", {}); s.set_attr(pm, "axs_heard_feat", whole(ow.drawings(ch[P])[1]).tolist())
    pw = s.evaluate(_Pred(predict_pointset_term()), {"s": pm})   # read the context symbol P (graph Term)
    s.add_edge_unchecked(pm, "recognised_as", pw)               # mechanical: record the result
    mm = s.add_node("Mark", {}); s.set_attr(mm, "axs_heard_feat", found["feat"].tolist())   # the ambiguous symbol
    s._inner.run_rules(50000)                                    # activate P, spread to PRIME T

    primedT = s.node(cand[T])["attrs"].get("context_primed")
    primedW = s.node(cand[W])["attrs"].get("context_primed")
    print(f"\n  reading '{short[P]}' activated it; priming spread along can_follow -> "
          f"'{short[T]}' primed={primedT}, '{short[W]}' primed={primedW}")

    print(f"\n  now reading the ambiguous symbol (visual + lam * context_primed):\n")
    margin = found["margin"]
    flip = None
    for lam in (0.0, margin * 0.5, margin * 1.5, margin * 3.0):
        w = s.evaluate(_Pred(predict_context_term(lam)), {"s": mm})
        jj = next(k for k in cand if cand[k] == w)
        if lam == 0.0:
            base = jj
        if flip is None and jj == T and lam > 0:
            flip = lam
        tag = "context CORRECTS -> truth" if jj == T else ("visual misread" if jj == W else "")
        print(f"      lam={lam:5.3f}  reads '{short[jj]:>14}'   {tag}")

    print(f"\n  {SEP[:88]}")
    ok = (base == W and flip is not None)
    print(f"  no context (lam=0) MISREADS '{short[base]}' (the visual best); with context the priming Rule")
    print(f"  flips the read to the truth '{short[T]}' at lam={flip}. Top-down context disambiguates an")
    print(f"  ambiguous symbol — graph-native (activation + priming Rules, context-aware Term). corrected: {ok}")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
