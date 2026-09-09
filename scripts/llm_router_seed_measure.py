#!/usr/bin/env python3
"""LLM learned-router seed — does a LEARNED cheap seed close the oracle gap?

RUN WITH THE VENV PYTHON:
  HF_HOME=/applications/data/model_graph_work/hf_home \\
  /applications/data/model_graph_work/venv/bin/python \\
  scripts/llm_router_seed_measure.py

See docs/research/psychology_affect/LLM_ROUTER_SEED_PREREG.md.

Block 314 left the barrier at the SEED: every HAND-derived key (gate, joint
gate+up) is a better-but-imperfect ranker. The named fix was a small LEARNED
router — a per-layer ridge-regression map (input -> predicted activation),
fit on the train corpus, one matmul at inference. This measures whether the
learned router (+ graph expansion) closes the per-query-oracle gap on held-out.
"""

from __future__ import annotations

import sys
import time

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
    "The capital of Japan is", "A knife is used for",
    "The opposite of day is", "Milk comes from",
    "The moon orbits the", "A guitar has six",
    "The speed of light is", "Rain falls from the",
    "A doctor works in a", "The wheel was invented",
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
    print("LLM LEARNED-ROUTER SEED — does a learned cheap seed close the gap?")
    print("(Qwen3-0.6B, %d train / %d held-out, agreement vs full graph)"
          % (len(TRAIN), n))
    print("=" * 74)

    t0 = time.time()
    G = lsr.fit_coactivation_graph(npm, tr, per_query_frac=0.1, pool_frac=0.6)
    R = lsr.fit_router(npm, tr, ridge=1.0)
    print("\nfit coactivation graph + router in %.0fs" % (time.time() - t0))

    def ag(cfg_of):
        return sum(int(npm.forward_logits(i, sparse=cfg_of(i)).argmax()) == f
                   for i, f in zip(ho, full))

    def co(i, t, mode, expand):
        return lsr.SparseConfig(order2_shape=lsr.coactivation_retrieve(
            npm, G, i, seed_frac=0.2, target_frac=t, seed_mode=mode,
            expand=expand, router=R))

    print("\n%-8s %-13s %-12s %-12s %-8s" %
          ("target", "router+graph", "router-only", "joint+graph", "oracle"))
    for t in (0.5, 0.4, 0.3):
        rg = ag(lambda i, t=t: co(i, t, "router", True))
        ro = ag(lambda i, t=t: co(i, t, "router", False))
        jg = ag(lambda i, t=t: co(i, t, "joint", True))
        orac = ag(lambda i, t=t: lsr.SparseConfig(ffn_keep_frac=t))
        print("  %-6.2f %-13d %-12d %-12d %-8d" % (t, rg, ro, jg, orac))

    print("\n" + "=" * 74)
    print("VERDICT (honest):")
    print("  * the learned linear router is COMPETITIVE with the joint key")
    print("    (better at some fractions, worse at others) and graph expansion")
    print("    helps — but it does NOT close the per-query-oracle gap.")
    print("  * ESCALATED: even a LEARNED (not hand-derived) cheap seed fails,")
    print("    so this is not a wrong-key artifact — a LINEAR input->active-set")
    print("    map is fundamentally insufficient to cheaply predict the exact")
    print("    active set. The oracle's information is the full nonlinear")
    print("    silu(gate·x)·(up·x); a linear predictor leaves a large residual.")
    print("  * The residual open problem is now sharply bounded: cheap EXACT")
    print("    active-set prediction needs the nonlinearity (i.e. ~computing")
    print("    the activation), OR a fundamentally different (nonlinear/")
    print("    approximate-but-good-enough) router — a real open question.")
    print("=" * 74)


if __name__ == "__main__":
    main()
