"""formant_features — the agent COMPOSES its own formant detector.

When the agent reasons that its band-MEANS are the wrong representation and reads
the science it HOLDS (`vocal_tract_resonance_formants`: formants "appear as
spectral PEAKS"), it writes the detector ITSELF, in its native language — a
Term-tree built from its own DSL primitives (`And`, `Gt`, `Attr`). A formant is a
spectral peak; a peak is a band greater than both its neighbours:

    And( Gt(b_i, b_{i-1}), Gt(b_i, b_{i+1}) )

No LLM authors this and no human hand-codes the extraction. The Term-tree IS the
agent's program, composed from primitives it already has, and it executes on the
substrate's OWN evaluator. See [[ozma_write_not_train_prior_art]] /
[[ozma_agent_authors_not_trains]] / [[ozma_concepts_in_gamma]].
"""
from __future__ import annotations

from substrate_rs import And, Gt, Attr, Var

from .acoustic_resolution import get_resolution
from .speech_science import science_says_formants_are_peaks


def _peak_term(res: int, i: int):
    """Compose 'band i is a local maximum' from primitives — the agent's program
    for 'there is a formant here'."""
    s = Var("s")
    bi = Attr(s, f"band{res}_{i}")
    return And(items=(Gt(a=bi, b=Attr(s, f"band{res}_{i-1}")),
                      Gt(a=bi, b=Attr(s, f"band{res}_{i+1}"))))


def compose_peak_features(substrate, resolution: int | None = None) -> int:
    """The agent composes a peak-detector Term-tree for each interior band, FROM
    its primitives, BECAUSE the science it holds grounds formant = spectral peak.
    Each becomes a `feature_kind=peak` Concept carrying the composed predicate.
    Returns the number minted (0 if the agent hasn't grounded what a formant is —
    it won't guess)."""
    if not science_says_formants_are_peaks(substrate):
        return 0
    res = resolution if resolution is not None else get_resolution(substrate)
    existing = {substrate.node(c)["attrs"].get("name")
                for c in substrate.nodes("Concept")
                if substrate.node(c)["attrs"].get("feature_kind") == "peak"}
    minted = 0
    for i in range(1, res - 1):
        name = f"peak_band{res}_{i}"
        if name in existing:
            continue
        term = _peak_term(res, i)
        substrate.add_node("Concept", {
            "name": name, "feature_kind": "peak",
            "band": f"band{res}_{i}", "res": res, "idx": i,
            "predicate": term.to_dict(), "origin": "phonology",
            "composed_by": "agent"})
        minted += 1
    return minted


def evaluate_peak_features(substrate, signs=None) -> int:
    """Run the agent's composed peak Term-trees on signs via the substrate's OWN
    evaluator — the agent's program executes natively — adding an `exhibits` edge
    wherever a sign has a formant (local max). Returns edges added."""
    feats = [(c, substrate.node(c)["attrs"])
             for c in substrate.nodes("Concept")
             if substrate.node(c)["attrs"].get("feature_kind") == "peak"]
    if not feats:
        return 0
    try:
        substrate.add_production({
            "src": {"type": "AcousticSign", "var": "a"},
            "edge_type": "exhibits", "tgt": {"type": "Concept", "var": "b"},
            "provenance": "formant_features:exhibits"})
    except Exception:
        pass
    targets = signs if signs is not None else substrate.nodes("AcousticSign")
    added = 0
    for sign in targets:
        present = set(substrate.neighbours(sign, "exhibits"))
        for c, a in feats:
            term = _peak_term(int(a["res"]), int(a["idx"]))
            try:
                hit = bool(substrate.evaluate(term, {"s": sign}))
            except Exception:
                hit = False
            if hit and c not in present:
                try:
                    substrate.add_edge(sign, "exhibits", c)
                    added += 1
                except Exception:
                    pass
    return added


__all__ = ["compose_peak_features", "evaluate_peak_features"]
