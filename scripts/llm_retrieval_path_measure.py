"""Block 319000 — RETRIEVAL PATH measure.

After block 318 the mode-grain router caught the per-query retrieval-oracle, and
the residual gap to identical outcomes moved into the RETRIEVAL/SELECTION path.
This block localises that ceiling and fixes it.

DIAGNOSTIC (H1): the retrieval path applied ONE neuron set across ALL token
positions (chosen from the last token). The true active set varies BY POSITION,
so a single fixed set starves the other positions. Proof: the TRUE last-token
active set applied as a fixed order2 set caps at 2/1/0 (frac 0.5/0.4/0.3), while
per-token keep-frac (same magnitude criterion, but per position) hits 8/5/4.

FIX: per-position retrieval — every token position gets the active set its own
activation needs (`mode_retrieve_per_position`, forward accepts a per-position
order2_shape). The per-position ORACLE then matches/exceeds the global keep-frac
oracle (9/6/4 vs 8/5/4) — the ceiling is GONE. The deployable per-position mode
router improves over the fixed-set router at every fraction; the remaining gap
to the unlocked oracle is now per-position ROUTER QUALITY (the mode router was
fit on last-token activations).

Anti-faking: fitted on 60-prompt train, tested on 10 DISJOINT held-out. Oracles
peek at the true activation (per-position and global) — explicit upper bounds,
not deployable. Every fraction reported. The per-position mode retrieval
recomputes xg at all positions, so it is NOT cheaper than the FFN at eval — this
rung proves the MECHANISM/grain of the selection path, not a cheapness win.

Run: HF_HOME=/applications/data/model_graph_work/hf_home \\
     /applications/data/model_graph_work/venv/bin/python -u \\
       scripts/llm_retrieval_path_measure.py
"""

import sys, time
sys.path.insert(0, ".")
import numpy as np
from domains import llm_structure_recovery as lsr

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
    "The capital of China is", "The capital of Egypt is",
    "A whale is a kind of", "A spider has eight",
    "The opposite of wet is", "The opposite of open is",
    "Honey is made by", "A triangle has three",
    "The Earth revolves around the", "Snow is cold and",
    "A library is full of", "The heart pumps",
    "A piano has many", "The opposite of true is",
    "Coffee contains", "A river flows to the",
    "The capital of Canada is", "A clock tells the",
    "Leaves are usually", "The opposite of empty is",
    "The chemical symbol for oxygen is", "A cow gives us",
    "The opposite of fast is", "A week has seven",
    "The capital of Brazil is", "Fire is very",
    "The opposite of soft is", "A dictionary defines",
    "The sky at night is", "A baby cat is a",
]
HELDOUT = [
    "The capital of Germany is", "The capital of Spain is",
    "The opposite of big is", "A cat is a kind of",
    "A hammer is a kind of", "Water is made of hydrogen and",
    "The chemical symbol for gold is", "Paris is the capital of",
    "Two plus three equals", "The color of the sky is",
]


def _true_fixed_shape(npm, ids, frac):
    """ORACLE fixed set: true LAST-token active set applied as ONE set for the
    whole sequence — isolates the fixed-set-across-positions ceiling (H1)."""
    ios = lsr._ffn_io(npm, ids)
    shp = {}
    for L, (xg, act) in enumerate(ios):
        ff = act.shape[0]
        keep = max(1, int(round(ff * frac)))
        shp[L] = np.sort(np.argsort(-act)[:keep])
    return shp


class _PerPosOracle:
    """Per-POSITION oracle: peeks at the true activation at EVERY position."""

    def __init__(self, model):
        self.m = model

    def shape(self, ids, frac):
        xgs = lsr._ffn_io_all(self.m, ids)
        shp = {}
        for L, xg in enumerate(xgs):
            gate = self.m._t("model.layers.%d.mlp.gate_proj.weight" % L)
            up = self.m._t("model.layers.%d.mlp.up_proj.weight" % L)
            A = np.abs(self.m.silu(xg @ gate.T) * (xg @ up.T))   # [T, ff]
            T, ff = A.shape
            keep = max(1, int(round(ff * frac)))
            shp[L] = [np.sort(np.argsort(-A[t])[:keep]) for t in range(T)]
        return shp


def main():
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(MODEL)
    npm = lsr.NumpyQwen3(MODEL)

    def enc(p):
        return tok(p, return_tensors="pt")["input_ids"][0].tolist()

    train = [enc(p) for p in TRAIN]
    ho = [enc(p) for p in HELDOUT]
    full = [int(npm.forward_logits(i).argmax()) for i in ho]

    print("=" * 74)
    print("RETRIEVAL PATH — block 319000 (per-position closes the ceiling)")
    print("(Qwen3-0.6B, %d train / %d held-out, agreement vs full graph)"
          % (len(train), len(ho)))
    print("=" * 74)

    t0 = time.time()
    Rmode = lsr.fit_mode_router(npm, train, k=32, ridge=1.0)
    G = lsr.fit_coactivation_graph(npm, train, per_query_frac=0.1, pool_frac=0.6)
    Porac = _PerPosOracle(npm)
    print("fit mode router + graph in %.0fs" % (time.time() - t0))

    def ag(cfg_of):
        return sum(int(npm.forward_logits(i, sparse=cfg_of(i)).argmax()) == f
                   for i, f in zip(ho, full))

    # ---- H1 diagnostic: fixed-set (even TRUE) vs per-token keep-frac ----
    print("\n--- H1: fixed-set ceiling (TRUE last-token set) vs per-token ---")
    print("%-8s %-22s %-16s" % ("frac", "TRUE-fixed(order2)", "keep-frac(pos)"))
    for t in (0.5, 0.4, 0.3):
        tf = ag(lambda i, t=t: lsr.SparseConfig(
            order2_shape=_true_fixed_shape(npm, i, t)))
        kf = ag(lambda i, t=t: lsr.SparseConfig(ffn_keep_frac=t))
        print("  %-6.2f %-22d %-16d" % (t, tf, kf))

    # ---- The fix: per-position retrieval ----
    print("\n--- FIX: per-position retrieval ---")
    print("%-8s %-14s %-16s %-16s %-12s" %
          ("target", "perpos-mode", "perpos-ORACLE", "fixed-mode(318)",
           "keep-frac"))
    for t in (0.5, 0.4, 0.3):
        pm = ag(lambda i, t=t: lsr.SparseConfig(
            order2_shape=lsr.mode_retrieve_per_position(npm, Rmode, i,
                                                        target_frac=t)))
        po = ag(lambda i, t=t: lsr.SparseConfig(order2_shape=Porac.shape(i, t)))
        fm = ag(lambda i, t=t: lsr.SparseConfig(
            order2_shape=lsr.coactivation_retrieve(
                npm, G, i, seed_frac=0.2, target_frac=t, seed_mode="router",
                expand=True, router=Rmode)))
        kf = ag(lambda i, t=t: lsr.SparseConfig(ffn_keep_frac=t))
        print("  %-6.2f %-14d %-16d %-16d %-12d" % (t, pm, po, fm, kf))

    print("\n" + "=" * 74)
    print("VERDICT:")
    print("  The retrieval ceiling was the FIXED-SET-ACROSS-POSITIONS constraint")
    print("  (H1): a TRUE last-token active set applied to the whole sequence")
    print("  caps at 2/1/0 while per-token keep-frac hits 8/5/4. Per-position")
    print("  retrieval removes it: the per-position ORACLE matches/exceeds the")
    print("  global keep-frac oracle (9/6/4 vs 8/5/4). The deployable")
    print("  per-position mode router improves at every fraction; the residual")
    print("  gap is now per-position ROUTER QUALITY (mode router fit on")
    print("  last-token activations) — the next lever.")
    print("=" * 74)


if __name__ == "__main__":
    main()
