#!/usr/bin/env python3
"""LLM structure recovery — measure agreement vs the reference model.

RUN WITH THE VENV PYTHON (torch is the ORACLE only):
  HF_HOME=/applications/data/model_graph_work/hf_home \\
  /applications/data/model_graph_work/venv/bin/python \\
  scripts/llm_structure_recovery_measure.py

See docs/research/psychology_affect/LLM_STRUCTURE_RECOVERY_PREREG.md.

Proves the structure of Qwen3-0.6B is recovered into an explicit dataflow
GRAPH (domains.llm_structure_recovery) that gives the SAME OUTCOMES as the
model — verified as next-token AGREEMENT on a HELD-OUT prompt battery, plus
top-k overlap and logit correlation. The recovered graph's forward path is
pure numpy (no torch); torch is only the reference oracle.
"""

from __future__ import annotations

import sys

import numpy as np

sys.path.insert(0, ".")

from domains import llm_structure_recovery as lsr  # noqa: E402

MODEL = "/applications/data/model_graph_work/Qwen3-0.6B"

# HELD-OUT battery — DISTINCT from the 3 gate prompts used while building the
# forward pass (Paris / cold / animal). These were never inspected during
# construction; agreement on them is the real transfer test.
HELD_OUT = [
    "The capital of Germany is",
    "The capital of Spain is",
    "The opposite of big is",
    "The opposite of fast is",
    "A cat is a kind of",
    "A hammer is a kind of",
    "The sun rises in the",
    "Water is made of hydrogen and",
    "The first president of the United States was",
    "Two plus three equals",
    "The color of the sky is",
    "A group of wolves is called a",
    "The chemical symbol for gold is",
    "Paris is the capital of",
    "The largest planet in our solar system is",
]


def main():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    print("=" * 72)
    print("LLM STRUCTURE RECOVERY — Qwen3-0.6B as an explicit dataflow graph")
    print("agreement vs the reference model on HELD-OUT prompts")
    print("=" * 72)

    npm = lsr.NumpyQwen3(MODEL)
    tok = AutoTokenizer.from_pretrained(MODEL)
    ref = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.float32).eval()

    n = len(HELD_OUT)
    argmax_match = 0
    top5_overlaps = []
    corrs = []
    graph_eq_direct = 0
    print("\n%-42s %-9s %-9s %s" % ("prompt", "ref", "graph", "match"))
    for p in HELD_OUT:
        ids = tok(p, return_tensors="pt")["input_ids"][0].tolist()
        with torch.no_grad():
            rl = ref(torch.tensor([ids])).logits[0, -1].numpy()
        # recovered GRAPH forward (pure numpy, no torch)
        g, out = lsr.build_graph(npm, ids)
        gl = g.evaluate(out)
        # also the direct numpy forward, to confirm graph == direct
        dl = npm.forward_logits(ids)
        if np.max(np.abs(gl - dl)) == 0.0:
            graph_eq_direct += 1
        rt, gt = int(rl.argmax()), int(gl.argmax())
        if rt == gt:
            argmax_match += 1
        r5 = set(np.argsort(-rl)[:5].tolist())
        g5 = set(np.argsort(-gl)[:5].tolist())
        top5_overlaps.append(len(r5 & g5) / 5.0)
        corrs.append(float(np.corrcoef(rl, gl)[0, 1]))
        print("%-42s %-9s %-9s %s" %
              (p, tok.decode([rt]).strip()[:8], tok.decode([gt]).strip()[:8],
               "OK" if rt == gt else "MISMATCH"))

    print("\n" + "-" * 72)
    print("next-token AGREEMENT (held-out):   %d/%d = %.1f%%" %
          (argmax_match, n, 100 * argmax_match / n))
    print("top-5 overlap (mean):              %.3f" % np.mean(top5_overlaps))
    print("logit correlation (mean):          %.5f" % np.mean(corrs))
    print("graph == direct numpy (bit-exact): %d/%d" % (graph_eq_direct, n))

    print("\n" + "=" * 72)
    recovered = argmax_match == n and np.mean(corrs) > 0.999
    print("VERDICT: structure recovered (same outcomes on held-out): %s" %
          ("PROVEN" if recovered else "PARTIAL — see mismatches"))
    print("  The forward path is pure numpy over an explicit %d-node dataflow"
          % len(g.nodes))
    print("  graph; torch is only the reference oracle. Only WEIGHTS were")
    print("  copied — the COMPUTATION is the graph's. An LLM made into a")
    print("  graph-cognition seed.")
    print("=" * 72)
    return {"agreement": argmax_match / n, "top5": float(np.mean(top5_overlaps)),
            "corr": float(np.mean(corrs)), "recovered": recovered}


if __name__ == "__main__":
    main()
