"""SEQUENCE/WORD LEXICON AT SCALE (graph-native) — whole-word reading, measured.

The reading-context piece primed ONE ambiguous symbol from its predecessor. This scales it to the WORD:
a lexicon of known symbol-sequences, where the word as a UNIT constrains all its letters at once. The
whole-word lexical decode (predict_word_term) argmaxes over lexicon words of the summed per-position
visual fit — the known word that best explains ALL positions wins and so dictates each letter, correcting
individually-ambiguous ones (the word-superiority effect at scale). The lexicon is graph data (LexWord
--has_slot--> Slot{pos, template}); the position join (mark at slot.pos) and the decode are held Terms,
no new Rust; the host only builds the lexicon and stages each written word.

The demo builds a lexicon over an alphabet of real Omniglot symbols, then writes each word with a
DIFFERENT writer per letter (so some letters are individually ambiguous) and compares PER-LETTER
independent recognition vs the WHOLE-WORD decode — measuring how many ambiguous letters the lexicon fixes.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_word_lexicon [n_words]
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np

import substrate_rs as srs
from domains import omniglot_world as ow
from domains.recognition_graph import predict_pointset_term, predict_word_term

SEP = "=" * 92
WHOLE_N, ALPHA, WORDLEN = 64, 10, 3


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def main():
    n_words = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    print(SEP)
    print("SEQUENCE/WORD LEXICON AT SCALE (graph-native): whole-word lexical decode — the known word that")
    print("best explains all positions dictates each letter, correcting ambiguous ones (word-superiority).")
    print(SEP)
    if not ow.have_data("evaluation"):
        print(f"\n  Omniglot strokes not found under {ow.DATA}.")
        return 1

    by_alph = {a: ow.characters(a, "evaluation") for a in ow.alphabets("evaluation")}
    by_alph = {a: cs for a, cs in by_alph.items() if len(cs) >= ALPHA}
    alph = sorted(by_alph)[0]
    ch = by_alph[alph]
    wc: dict[str, np.ndarray] = {}

    def whole(p):
        if p not in wc:
            wc[p] = ow.trajectory(p, WHOLE_N, per_stroke=True)
        return wc[p]

    s = srs.Substrate()
    # --- alphabet: ALPHA symbol concepts (the per-letter candidates), writer-0 as the canonical template ---
    sym, c2x = {}, {}
    for x in range(ALPHA):
        c = s.add_node("Concept", {"is_word": 1.0})
        s.set_attr(c, "axs_synth_feat", whole(ow.drawings(ch[x])[0]).tolist()); s.set_attr(c, "name", f"sym{x}")
        sym[x] = c; c2x[c] = x

    # --- lexicon: n_words known sequences, each a LexWord with positioned Slots (template + symbol id) ---
    rng = np.random.default_rng(3)
    words, seen = [], set()
    while len(words) < n_words:
        w = tuple(int(rng.integers(ALPHA)) for _ in range(WORDLEN))
        if w in seen:
            continue
        seen.add(w); words.append(w)
    for w in words:
        W = s.add_node("LexWord", {"is_lexword": 1.0}); s.set_attr(W, "name", "".join(map(str, w)))
        for p, x in enumerate(w):
            slot = s.add_node("Slot", {})
            s.set_attr(slot, "pos", float(p)); s.set_attr(slot, "axs_synth_feat", whole(ow.drawings(ch[x])[0]).tolist())
            s.add_edge_unchecked(slot, "sym", sym[x]); s.add_edge_unchecked(W, "has_slot", slot)

    pt, pw = _Pred(predict_pointset_term()), _Pred(predict_word_term())
    n_drw = min(len(ow.drawings(ch[x])) for x in range(ALPHA))

    tot = ind_ok = word_ok = w_ind = w_word = 0
    fixed = broke = 0
    for wi, w in enumerate(words):
        marks = []
        for p, x in enumerate(w):                                   # write each letter with a different writer
            d = 1 + int(rng.integers(n_drw - 1))
            m = s.add_node("Mark", {}); s.set_attr(m, "axs_heard_feat", whole(ow.drawings(ch[x])[d]).tolist())
            s.set_attr(m, "pos", float(p)); marks.append((p, x, m))
        ind = {}                                                    # PER-LETTER independent recognition
        for p, x, m in marks:
            win = s.evaluate(pt, {"s": m})
            ind[p] = c2x.get(win)
        Wwin = s.evaluate(pw, {})                                   # WHOLE-WORD lexical decode (graph Term)
        wordpred = {}
        for slot in s.neighbours(Wwin, "has_slot"):
            p = int(s.node(slot)["attrs"]["pos"])
            wordpred[p] = c2x.get(s.neighbours(slot, "sym")[0])
        for p, x, m in marks:
            tot += 1
            i_ok, w_ok = (ind[p] == x), (wordpred.get(p) == x)
            ind_ok += i_ok; word_ok += w_ok
            fixed += (w_ok and not i_ok); broke += (i_ok and not w_ok)
            s.remove_node(m)
        w_ind += all(ind[p] == x for p, x, _ in marks)
        w_word += all(wordpred.get(p) == x for p, x, _ in marks)

    print(f"\n  lexicon: {len(words)} words over a {ALPHA}-symbol alphabet ('{alph}'); each word written with a")
    print(f"  different writer per letter ({tot} letters total). per-letter vs whole-word reading:\n")
    print(f"    {'':22}{'LETTER acc':>12}{'WORD acc':>12}")
    print(f"    {'per-letter (vision only)':22}{100*ind_ok/tot:>11.1f}%{100*w_ind/len(words):>11.1f}%")
    print(f"    {'whole-word (lexicon)':22}{100*word_ok/tot:>11.1f}%{100*w_word/len(words):>11.1f}%")
    print(f"\n  the lexicon FIXED {fixed} individually-misread letters (broke {broke}); net letter gain "
          f"{100*(word_ok-ind_ok)/tot:+.1f} pts.")
    print(f"\n  {SEP[:88]}")
    print(f"  whole-word lexical decode (graph Term over LexWord/Slot graph data, no new Rust): the known")
    print(f"  word that best explains all positions corrects ambiguous letters — the word-superiority effect")
    print(f"  at scale, graph-native. The unit of reading is now the WORD, not the isolated symbol.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
