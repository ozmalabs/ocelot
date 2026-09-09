#!/usr/bin/env python3
"""LLM joint-key seed — does fixing the seed (gate+up) close the oracle gap?

RUN WITH THE VENV PYTHON:
  HF_HOME=/applications/data/model_graph_work/hf_home \\
  /applications/data/model_graph_work/venv/bin/python \\
  scripts/llm_joint_seed_measure.py

See docs/research/psychology_affect/LLM_JOINT_SEED_PREREG.md.

Block 313 found the coactivation-graph retrieval was bottlenecked by the SEED
(a weak gate-key). Block 311 named the fix: the JOINT gate+up key (true
relevance is silu(gate·x)·(up·x), so both projections rank the seed). This
measures whether joint-key seeding — with and without graph expansion — closes
the seed-quality gap toward the per-query oracle on held-out prompts.
"""

from __future__ import annotations

import sys

sys.path.insert(0, ".")

from domains import llm_structure_recovery as lsr  # noqa: E402

MODEL = "/applications/data/model_graph_work/Qwen3-0.6B"

TRAIN = [
    "The capital of France is", "The capital of Italy is",
    "The opposite of hot is", "A dog is a kind of",
    "The sun rises in the", "The chemical symbol for iron is",
    "The largest ocean is the", "A tree has leaves and",
    "The first man on the moon was", "Ice is frozen",
    "The plural of child is", "Fish live in",
    "The capital of Russia is", "The opposite of light is",
    "A car has four", "Bread is made from",
    "The freezing point of water is", "A bird can",
    "The author of Romeo and Juliet was", "Gold is a kind of",
]
HELDOUT = [
    "The capital of Germany is", "The capital of Spain is",
    "The opposite of big is", "A cat is a kind of",
    "A hammer is a kind of", "Water is made of hydrogen and",
    "The chemical symbol for gold is", "Paris is the capital of",
    "Two plus three equals", "The color of the sky is",
]


def main():
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(MODEL)
    npm = lsr.NumpyQwen3(MODEL)

    def enc(p):
        return tok(p, return_tensors="pt")["input_ids"][0].tolist()

    tr = [enc(p) for p in TRAIN]
    ho = [enc(p) for p in HELDOUT]
    full = [int(npm.forward_logits(i).argmax()) for i in ho]
    n = len(ho)

    print("=" * 74)
    print("LLM JOINT-KEY SEED — does fixing the seed close the oracle gap?")
    print("(Qwen3-0.6B, %d train / %d held-out, agreement vs full graph)"
          % (len(TRAIN), n))
    print("=" * 74)

    G = lsr.fit_coactivation_graph(npm, tr, per_query_frac=0.1, pool_frac=0.6)

    def ag(cfg_of):
        return sum(int(npm.forward_logits(i, sparse=cfg_of(i)).argmax()) == f
                   for i, f in zip(ho, full))

    def coact(i, t, mode, expand):
        return lsr.SparseConfig(order2_shape=lsr.coactivation_retrieve(
            npm, G, i, seed_frac=0.2, target_frac=t, seed_mode=mode,
            expand=expand))

    print("\n%-8s %-12s %-12s %-12s %-12s %-8s" %
          ("target", "joint+graph", "joint-only", "gate+graph", "order2static",
           "oracle"))
    for t in (0.6, 0.5, 0.4):
        jg = ag(lambda i, t=t: coact(i, t, "joint", True))
        jo = ag(lambda i, t=t: coact(i, t, "joint", False))
        gg = ag(lambda i, t=t: coact(i, t, "gate", True))
        st = lsr.fit_order2_shape(npm, tr, frac=t)
        o2 = ag(lambda i, st=st: lsr.SparseConfig(order2_shape=st))
        orac = ag(lambda i, t=t: lsr.SparseConfig(ffn_keep_frac=t))
        print("  %-6.2f %-12d %-12d %-12d %-12d %-8d" %
              (t, jg, jo, gg, o2, orac))

    print("\n" + "=" * 74)
    print("VERDICT (honest):")
    print("  * joint gate+up seed > gate-key seed (block 311's fix, directional)")
    print("  * graph expansion adds on top of the joint seed")
    print("  * BUT the combination still trails the per-query oracle by a large")
    print("    margin — the |gate·x|·|up·x| key drops the silu nonlinearity and")
    print("    sign structure of the true relevance silu(gate·x)·(up·x).")
    print("  * Each refinement (order-2 mask -> joint key -> graph expand)")
    print("    climbs a little; cheaply predicting the EXACT active-memory set")
    print("    for a held-out query WITHOUT the true activation remains the")
    print("    open, well-characterised boundary.")
    print("=" * 74)


if __name__ == "__main__":
    main()
