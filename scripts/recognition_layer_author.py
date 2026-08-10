"""Author the two recognition-layer capabilities the agent derived from its WER failure
(commit b5d3e5e3), composed from HELD machinery, and measure their core properties:

  (1) COMPOSITIONAL word-generator (open vocabulary): a word is a SEQUENCE of sub-word
      units; the lexicon is realizable by COMPOSING parts (a search over the production
      space), NOT a whole-word table lookup. Win = a word NEVER seen whole is still
      spellable if its sub-word units were seen. Measure OOV coverage: compositional vs
      whole-word lookup, on held-out (unseen) words built from the SAME sub-word alphabet.

  (2) LANGUAGE-MODEL completion: a held bigram transition model (forward+backward TP,
      domains.forward_segmentation.estimate_bidirectional_tp / its forward+backward
      tables) RECOVERS a doubtful/masked unit from its CONTEXT — top-down prediction, not
      read off the (here, erased) item. Measure masked-unit recovery vs chance.

Controlled artificial language isolates each capability (the way Saffran isolated
segmentation). Run: python scripts/recognition_layer_author.py
"""
from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

from scripts.segmentation_saffran import make_language, make_stream, tp_table, bwd_table


def compositional_oov(n_words=40, wlen=3, alphabet=15, seed=0):
    """train on half the words; test words are UNSEEN combinations of the SAME units."""
    words = make_language(n_words, wlen, alphabet, seed, shared=True)
    train_w, test_w = set(words[: n_words // 2]), [w for w in words[n_words // 2:]]
    test_w = [w for w in test_w if w not in train_w]            # genuinely unseen wholes
    train_units = {u for w in train_w for u in w}               # the sub-word inventory
    whole = sum(w in train_w for w in test_w) / len(test_w)     # whole-word lookup
    comp = sum(all(u in train_units for u in w) for w in test_w) / len(test_w)  # compose
    return whole, comp, len(test_w)


def lm_completion(n_words=20, wlen=3, alphabet=12, seed=0):
    """held bigram model; recover a MASKED unit from its neighbours vs chance."""
    words = make_language(n_words, wlen, alphabet, seed, shared=True)
    train_stream, _ = make_stream(words, 600, seed + 1)
    fwd = tp_table([train_stream])                              # held P(next|cur)
    bwd = bwd_table([train_stream])                             # held P(cur|next)
    units = sorted({u for s in [train_stream] for u in s})
    test_stream, _ = make_stream(words, 300, seed + 2)
    correct = total = 0
    for i in range(1, len(test_stream) - 1):
        a, c = test_stream[i - 1], test_stream[i + 1]
        # top-down recovery: argmax_u P(u|a)*P(c|u) — the bigram model fills the mask.
        pred = max(units, key=lambda u: fwd.get(a, {}).get(u, 1e-9) * bwd.get(u, {}).get(c, 1e-9))
        correct += (pred == test_stream[i]); total += 1
    return correct / total, 1.0 / len(units)


def main():
    print("=" * 70)
    print("RECOGNITION-LAYER capabilities (agent-derived, composed from held ops)")
    print("=" * 70)

    print("\n(1) COMPOSITIONAL word-generator — open-vocabulary coverage of UNSEEN words:")
    ws, cs = [], []
    for sd in range(5):
        w, c, n = compositional_oov(seed=sd)
        ws.append(w); cs.append(c)
    import statistics as st
    print(f"    whole-word table lookup : {st.mean(ws):.1%} of unseen words covered")
    print(f"    COMPOSITIONAL (sub-word): {st.mean(cs):.1%} of unseen words spellable")
    print(f"    -> composition turns a closed lexicon into an OPEN one "
          f"({st.mean(cs)-st.mean(ws):+.0%}).")

    print("\n(2) LANGUAGE-MODEL completion — recover a MASKED unit from context:")
    accs, chances = [], []
    for sd in range(5):
        a, ch = lm_completion(seed=sd)
        accs.append(a); chances.append(ch)
    print(f"    chance (uniform guess)  : {st.mean(chances):.1%}")
    print(f"    bigram LM completion    : {st.mean(accs):.1%}   "
          f"({st.mean(accs)/st.mean(chances):.1f}x chance)")
    print(f"    -> the held context model RECOVERS doubtful units top-down.")
    print("=" * 70)


if __name__ == "__main__":
    main()
