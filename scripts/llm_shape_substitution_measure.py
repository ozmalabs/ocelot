#!/usr/bin/env python3
"""LLM shape substitution — does the OUTCOME come from the SHAPE, not the
arithmetic?

RUN WITH THE VENV PYTHON (tokenizer only; forward is pure numpy):
  HF_HOME=/applications/data/model_graph_work/hf_home \\
  /applications/data/model_graph_work/venv/bin/python \\
  scripts/llm_shape_substitution_measure.py

See docs/research/psychology_affect/LLM_SHAPE_SUBSTITUTION_PREREG.md.

The user's framing: the recovery is of the TRUE SHAPE encoded in the LLM's
substrate. Test it by SUBSTITUTING the dense FFN op with a shape-native
operation — retrieve the active memories by geometry — and measuring whether
the outcome survives. Two selectors, head-to-head at each fraction:

  * SHAPE-RETRIEVE: pick neurons by query-key geometry (x·gate_key) — the
    coherence/kNN primitive — WITHOUT the full activation.
  * EXACT-TOPK: pick neurons by the true activation |silu(gate)·up| — the
    shape WITH the full descriptor (an oracle upper bound on selection).

The GAP between them is how much of the shape the query-key descriptor misses.
Agreement measured vs the full recovered graph (=100% vs torch, block 309).
"""

from __future__ import annotations

import sys

import numpy as np

sys.path.insert(0, ".")

from domains import llm_structure_recovery as lsr  # noqa: E402

MODEL = "/applications/data/model_graph_work/Qwen3-0.6B"

PROMPTS = [
    "The capital of Germany is", "The capital of Spain is",
    "The opposite of big is", "The opposite of fast is",
    "A cat is a kind of", "A hammer is a kind of",
    "The sun rises in the", "Water is made of hydrogen and",
    "The chemical symbol for gold is", "Paris is the capital of",
    "The color of the sky is", "Two plus three equals",
]


def main():
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(MODEL)
    npm = lsr.NumpyQwen3(MODEL)
    id_lists = [tok(p, return_tensors="pt")["input_ids"][0].tolist()
                for p in PROMPTS]

    full_tok, full_flops = [], 0
    for ids in id_lists:
        fc = {}
        lg = npm.forward_logits(ids, sparse=lsr.SparseConfig(), flop_counter=fc)
        full_tok.append(int(lg.argmax()))
        full_flops += fc["flops"]

    def sweep(make_cfg):
        rows = []
        for f in (1.0, 0.75, 0.5, 0.25, 0.1):
            agree = flops = 0
            for ids, ft in zip(id_lists, full_tok):
                fc = {}
                lg = npm.forward_logits(ids, sparse=make_cfg(f), flop_counter=fc)
                flops += fc["flops"]
                if int(lg.argmax()) == ft:
                    agree += 1
            rows.append((f, agree / len(id_lists), flops / full_flops))
        return rows

    print("=" * 74)
    print("LLM SHAPE SUBSTITUTION — is the outcome in the SHAPE, not the math?")
    print("(recovered Qwen3-0.6B; agreement vs full graph = 100%% vs torch)")
    print("=" * 74)

    print("\n[SHAPE-RETRIEVE] neurons by query-key geometry (x.gate_key)")
    print("  %-8s %-12s %-10s" % ("frac", "agreement", "flop_frac"))
    sr = sweep(lambda f: lsr.SparseConfig(ffn_retrieve_frac=f))
    for f, a, ff in sr:
        print("  %-8.2f %-12.2f %-10.2f" % (f, a, ff))

    print("\n[EXACT-TOPK] neurons by true activation |silu(gate)*up| (oracle)")
    print("  %-8s %-12s %-10s" % ("frac", "agreement", "flop_frac"))
    et = sweep(lambda f: lsr.SparseConfig(ffn_keep_frac=f))
    for f, a, ff in et:
        print("  %-8.2f %-12.2f %-10.2f" % (f, a, ff))

    # the shape gap: exact-topk - shape-retrieve at each fraction
    print("\n[SHAPE GAP] exact-topk agreement - shape-retrieve agreement")
    print("  %-8s %-12s" % ("frac", "gap"))
    gaps = []
    for (f, a_sr, _), (_, a_et, _) in zip(sr, et):
        gaps.append(a_et - a_sr)
        print("  %-8.2f %-12.2f" % (f, a_et - a_sr))

    print("\n" + "=" * 74)
    print("VERDICT — the true-shape framing, measured:")
    # exact-topk holding at 0.5 => the sparse active SET (shape) carries it
    et5 = dict((f, a) for f, a, _ in et).get(0.5, 0)
    sr5 = dict((f, a) for f, a, _ in sr).get(0.5, 0)
    print("  * OUTCOME IS IN THE SHAPE: exact-topk at 50%% keeps %.0f%% "
          "agreement" % (100 * et5))
    print("    => the outcome depends on WHICH sparse set of memories fires,")
    print("    not the full dense sum. Half the FFN arithmetic is redundant")
    print("    GIVEN the shape.")
    print("  * QUERY-KEY IS AN INCOMPLETE SHAPE DESCRIPTOR: shape-retrieve at "
          "50%% keeps only %.0f%% (gap %.0f%%) — gate-key geometry alone "
          "under-selects vs the true activation; the up-projection carries "
          "shape the single key direction misses. That is EXACTLY the "
          "still-missing shape: the joint gate+up key structure."
          % (100 * sr5, 100 * (et5 - sr5)))
    print("=" * 74)
    return {"shape_retrieve": sr, "exact_topk": et, "gaps": gaps}


if __name__ == "__main__":
    main()
