"""pairwise_recognition — the agent builds the recognition it asked for.

Asked what it wanted, the agent said: its features are GLOBAL thresholds that can't
sharpen one distinction without blurring others; it wants to use a discriminating
feature only WHEN telling a confused pair apart. It already holds everything needed
in its own state — Confusion(A,B) pairs and, per pair, a ConfusionBand with the
discriminating `band` and Fisher-separated means (a_mean, b_mean). So this follows
the agent's own self-build pattern (runtime_design): the agent SPECIFIES from its
state (which band tells which pair apart), a MECHANICAL generator EMITS the
conditional use, as graph Term-trees. The agent decides WHAT; the generator emits HOW.

  tie_break(sign | top2 = {A,B}) = if  |band_b(sign) − a_mean| < |band_b(sign) − b_mean|
                                   then A  else B

i.e. when global recognition is ambiguous between A and B, decide with the one band
the agent found separates them — pairwise, not global. See [[ozma_agent_designs_runtime]]
/ [[ozma_concepts_in_gamma]].
"""
from __future__ import annotations


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def agent_specify_pairwise(substrate, top_k: int = 8) -> list:
    """The agent reads its OWN confusions + the discriminating bands it found and
    specifies the pairwise tie-breaks it wants. Read from its state, not chosen by
    me — for each strong confusion pair, the ConfusionBand with the best Fisher
    separation is the band it would use to tell that pair apart."""
    confs = sorted(
        ((substrate.node(c)["attrs"].get("true_word"),
          substrate.node(c)["attrs"].get("pred_word"),
          int(substrate.node(c)["attrs"].get("count", 0)))
         for c in substrate.nodes("Confusion")),
        key=lambda x: -x[2])[:top_k]
    cbands = {}
    for cb in substrate.nodes("ConfusionBand"):
        a = substrate.node(cb)["attrs"]
        key = (a.get("true_word"), a.get("pred_word"))
        am, bm = a.get("a_mean"), a.get("b_mean")
        asd, bsd = a.get("a_std", 0.0), a.get("b_std", 0.0)
        if am is None or bm is None:
            continue
        fisher = abs(am - bm) / (float(asd) + float(bsd) + 1e-6)
        cbands.setdefault(key, []).append((fisher, a.get("band"), float(am), float(bm)))
    spec = []
    for A, B, n in confs:
        best = max(cbands.get((A, B), []), default=None)
        if best is None:
            continue
        fisher, band, am, bm = best
        spec.append({"A": A, "B": B, "count": n, "band": band,
                     "a_mean": am, "b_mean": bm, "fisher": fisher})
    return spec


def _abs_diff_term(band: str, mean: float) -> dict:
    """|band(sign) − mean| as a Term-tree."""
    attr = {"type": "Attr", "node": {"type": "Var", "name": "s"}, "key": band}
    return {"type": "Abs", "arg": {"type": "Minus", "a": attr,
                                   "b": {"type": "Lit", "value": float(mean)}}}


def tie_break_term(entry: dict) -> dict:
    """Emit the pairwise tie-break for one pair as a graph Term: closer to a_mean → 1
    (pick A), else 0 (pick B). The generator's mechanical HOW from the agent's spec."""
    return {"type": "Lt",
            "a": _abs_diff_term(entry["band"], entry["a_mean"]),
            "b": _abs_diff_term(entry["band"], entry["b_mean"])}


def pairwise_decide(substrate, sign, top2, spec_index):
    """When global recognition's top two are a pair the agent has a tie-break for,
    decide with the agent's band — natively. Returns the chosen word, or top2[0]."""
    a, b = top2
    e = spec_index.get((a, b)) or spec_index.get((b, a))
    if e is None:
        return a
    A, B = e["A"], e["B"]
    try:
        closer_to_A = bool(substrate.evaluate(_Pred(tie_break_term(e)), {"s": sign}))
    except Exception:
        return a
    return A if closer_to_A else B


__all__ = ["agent_specify_pairwise", "tie_break_term", "pairwise_decide"]
