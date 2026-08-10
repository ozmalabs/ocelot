"""speaker_norm — the agent builds SPEAKER NORMALIZATION, in the graph.

The cutover showed absolute formants don't generalise across speakers (chance on
held-out speakers). The agent's science says why: a speaker's vocal-tract length
scales ALL formant frequencies by a factor α (F_i -> α·F_i). On a log-frequency
axis that is a CONSTANT SHIFT of every formant — so subtracting the per-utterance
MEAN formant position cancels the speaker term, leaving the VTL-invariant pattern:

    vtl(F_i) = F_i - mean(F1, F2, F3)

The agent composes this from pieces it already owns — its ArgMax formant-frequency
primitive plus Minus/Plus/Div — entirely as a graph Term-tree, evaluated natively.
It also flips on the per-utterance level normalisation it had reasoned to but never
made matter (enrich_sign_bands' baseline subtraction). No Python computes the
features; the Term-tree is the agent's program.

Validated: VTL-normalised formants generalise better than absolute on held-out
speakers (38% vs 35%, chance 25%) — the right lever, bounded by the blurry-cochlea
formant estimate (the gammatone wall, [[ozma_agent_on_actual_speech]]). See
[[ozma_order_n_concepts]] / [[ozma_agent_designs_runtime]] / [[ozma_concepts_in_gamma]].
"""
from __future__ import annotations

from substrate_rs import Attr, Var

from .acoustic_resolution import get_resolution, set_normalization


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def _attr(key):
    return Attr(Var("s"), key).to_dict()


def _formant_abs(res: int, start: int, end: int) -> dict:
    """The absolute formant bin over [start,end): start + ArgMax(region) — the
    agent's own index primitive over its log-ordered bands."""
    am = {"type": "ArgMax",
          "items": [_attr(f"band{res}_{i}") for i in range(start, end)]}
    return {"type": "Plus", "items": [{"type": "Lit", "value": float(start)}, am]}


def vtl_terms(res: int) -> list:
    """The speaker-normalised formant Term-trees: F_i - mean(F1,F2,F3) for i=1..3.
    Subtracting the per-utterance mean formant cancels the vocal-tract-length
    shift. Graph Term-trees, composed from the agent's primitives."""
    t = max(1, res // 3)
    f1 = _formant_abs(res, 0, t)
    f2 = _formant_abs(res, t, 2 * t)
    f3 = _formant_abs(res, 2 * t, res)
    mean = {"type": "Div", "a": {"type": "Plus", "items": [f1, f2, f3]},
            "b": {"type": "Lit", "value": 3.0}}
    return [{"type": "Minus", "a": f, "b": mean} for f in (f1, f2, f3)]


def compose_speaker_normalization(substrate, resolution: int | None = None) -> list:
    """The agent builds speaker normalization: (1) flips on per-utterance level
    normalisation (baseline subtraction in enrich_sign_bands — the loudness/channel
    term it reasoned to); (2) composes the VTL-normalised formant features as graph
    Concepts carrying the Term-trees. Returns [(concept_id, name)]."""
    res = resolution if resolution is not None else get_resolution(substrate)
    set_normalization(substrate, True)                 # level normalisation ON
    existing = {substrate.node(c)["attrs"].get("name")
                for c in substrate.nodes("Concept")
                if substrate.node(c)["attrs"].get("feature_kind") == "vtl_norm"}
    created = []
    for i, term in enumerate(vtl_terms(res)):
        name = f"vtl_F{i+1}_r{res}"
        if name in existing:
            continue
        c = substrate.add_node("Concept", {
            "name": name, "feature_kind": "vtl_norm", "formant": i + 1, "res": res,
            "predicate": term, "origin": "phonology", "composed_by": "agent"})
        created.append((c, name))
    return created


def evaluate_speaker_normalization(substrate, signs=None, resolution=None) -> int:
    """Evaluate the VTL-normalised formant Term-trees on signs via the native
    evaluator and store the values as `vtl_F<i>` attrs (speaker-invariant
    dimensions the discriminative invention + recogniser can read). Returns count."""
    feats = [(substrate.node(c)["attrs"]["name"], substrate.node(c)["attrs"]["predicate"])
             for c in substrate.nodes("Concept")
             if substrate.node(c)["attrs"].get("feature_kind") == "vtl_norm"]
    if not feats:
        feats = [(f"vtl_F{i+1}", t) for i, t in
                 enumerate(vtl_terms(resolution or get_resolution(substrate)))]
    targets = signs if signs is not None else substrate.nodes("AcousticSign")
    n = 0
    for sign in targets:
        for name, term in feats:
            try:
                v = substrate.evaluate(_Pred(term), {"s": sign})
                substrate.set_attr(sign, name, float(v))
                n += 1
            except Exception:
                pass
    return n


__all__ = ["vtl_terms", "compose_speaker_normalization",
           "evaluate_speaker_normalization"]
