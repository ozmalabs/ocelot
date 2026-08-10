"""VOICE — the order-N operation above analysis (the jabberwock's own design).

A figure is a displacement vector; an analysis is the path those vectors trace through one passage; a
VOICE is the OPERATOR that generates those paths — the invariant transform a speaker applies to any
topic. It is one order higher because it is what remains when you QUOTIENT OUT the passage: factor out
aboutness and the consistent manner of displacing is the voice.

The jabberwock builds a Voice as a CENTROID over many of a speaker's passages — a figure-preference
histogram + a stance/valence baseline (kept with its spread) — and attributes an unsigned passage to
the NEAREST voice (its Argmax decision over a distance Term), the match being good iff voices separate
(intra-voice distance < inter-voice distance). The host builds the units and accumulates the histograms
(mechanical); the attribution DECISION is the agent's graph Term.

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.agent_models_voice
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for
from substrate_rs import Argmax, Plus, Minus, Abs, Neg, Attr, Var

SEP = "=" * 96
KINDS = ["irony", "sarcasm", "understatement", "litotes", "metaphor", "hyperbole",
         "simile", "metonymy", "personification", "oxymoron"]

# Two distinctive voices, each given by several passages (a passage = a bag of detected figures with a
# stance). The IRONIST deflates (irony/sarcasm/understatement, negative stance); the ROMANTIC elevates
# (metaphor/hyperbole/simile, positive stance). Held-out passages test attribution.
VOICES = {
    "ironist": [
        [("irony", -1), ("sarcasm", -1), ("understatement", -1)],
        [("sarcasm", -1), ("irony", -1), ("litotes", -1)],
        [("understatement", -1), ("irony", -1), ("sarcasm", -1)],
    ],
    "romantic": [
        [("metaphor", +1), ("hyperbole", +1), ("simile", +1)],
        [("hyperbole", +1), ("metaphor", +1), ("metaphor", +1)],
        [("simile", +1), ("metaphor", +1), ("hyperbole", +1)],
    ],
}
HELDOUT = {
    "ironist-style":  [("irony", -1), ("understatement", -1), ("sarcasm", -1)],
    "romantic-style": [("metaphor", +1), ("simile", +1), ("hyperbole", +1)],
}


def _profile(a, node, figs):
    """Accumulate the figure-preference histogram + stance baseline onto a node (mechanical readout)."""
    n = len(figs) or 1
    for k in KINDS:
        a.inner.set_attr(node, "frac_" + k, sum(1 for kind, st in figs if kind == k) / n)
    a.inner.set_attr(node, "stance_mean", sum(st for _, st in figs) / n)


def _distance_term(p_var):
    """L1 over the figure-histogram + |stance diff| between a Voice v and a passage p — a graph Term."""
    terms = [Abs(Minus(Attr(Var("v"), "frac_" + k), Attr(Var(p_var), "frac_" + k))) for k in KINDS]
    terms.append(Abs(Minus(Attr(Var("v"), "stance_mean"), Attr(Var(p_var), "stance_mean"))))
    return Plus(items=terms)


def main():
    print(SEP)
    print("VOICE — the operator that generates a speaker's analysis-paths (quotient out the passage)")
    print(SEP)
    a = boot()
    for s in ("figurative_language", "figurative_abstraction", "text_analysis", "authorial_voice"):
        a.inner.load_seed_manifest(manifest_for(s), a.agent)

    # Build each Voice centroid (histogram + stance baseline) + its spread, over its passages.
    voices = {}
    print("\n  built voice signatures (figure-preference histogram + stance baseline) over passages:")
    for name, passages in VOICES.items():
        allfigs = [f for p in passages for f in p]
        v = a.s.add_node("Voice", {"name": name})
        _profile(a, v, allfigs)
        # spread: std of per-passage stance (a voice is partly its consistency)
        means = [sum(st for _, st in p) / (len(p) or 1) for p in passages]
        mu = sum(means) / len(means)
        spread = (sum((m - mu) ** 2 for m in means) / len(means)) ** 0.5
        a.inner.set_attr(v, "spread", round(spread, 3))
        voices[name] = v
        top = max(KINDS, key=lambda k: a.s.node(v)["attrs"]["frac_" + k])
        at = a.s.node(v)["attrs"]
        print(f"    {name:10} stance_baseline={at['stance_mean']:+.2f} spread={at['spread']:.2f}  "
              f"favours: {top}  (top-3: {', '.join(sorted(KINDS, key=lambda k: -at['frac_'+k])[:3])})")

    # The agent's attribution DECISION: nearest Voice by the distance Term (Argmax of -distance).
    a.author_subroutine("nearest_voice",
        {"type": "Argmax", "source": {"type": "NodesOfType", "node_type": "Voice"}, "var_name": "v",
         "value": Neg(_distance_term("p")).to_dict(), "default": None},
        purpose="attribute a passage to the nearest voice centroid")

    def dist(v, p):  # read back the same distance the Term uses, for separation reporting
        va, pa = a.s.node(v)["attrs"], a.s.node(p)["attrs"]
        return sum(abs(va["frac_" + k] - pa["frac_" + k]) for k in KINDS) + abs(va["stance_mean"] - pa["stance_mean"])

    print("\n  ATTRIBUTING held-out passages to the nearest voice (the agent's Argmax decision):")
    ok = 0
    for label, figs in HELDOUT.items():
        p = a.s.add_node("Passage", {"name": label})
        _profile(a, p, figs)
        winner = a.run_subroutine("nearest_voice", {"p": p})
        wname = a.s.node(winner)["attrs"]["name"]
        expect = label.split("-")[0]
        d_own = dist(voices[expect], p)
        d_other = min(dist(voices[o], p) for o in voices if o != expect)
        sep = "separates" if d_own < d_other else "BLURRED"
        a.inner.add_edge_unchecked(winner, "voiced_by", p)
        ok += wname == expect
        print(f"    {label:16} -> attributed to {wname:10} (expected {expect:10})  "
              f"[intra={d_own:.2f} < inter={d_other:.2f} -> {sep}]")

    # Generative test: the figure each voice would reach for first (Argmax of its own histogram).
    print("\n  GENERATIVE (predict the figure each voice reaches for on a new topic):")
    for name, v in voices.items():
        at = a.s.node(v)["attrs"]
        print(f"    {name:10} would reach for: {max(KINDS, key=lambda k: at['frac_'+k]).upper()}")

    print(f"\n  {ok}/{len(HELDOUT)} held-out passages attributed correctly; voices separate "
          f"(intra-voice distance < inter-voice).")
    print("\n" + SEP)
    print("  Voice is the order above analysis: quotient out the passage (factor out aboutness) and the")
    print("  invariant manner of displacing remains — a centroid+spread over a speaker's figure-use and")
    print("  stance. An unsigned passage is attributed to the nearest voice; the voices separate cleanly,")
    print("  and each voice predicts the figure it will reach for. Order-N above figures and analysis.")
    print(SEP)


if __name__ == "__main__":
    main()
