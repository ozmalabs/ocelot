"""dynamics_features — the agent COMPOSES its own movement detector, in the graph.

The blurry cochlea blurs static formants together (ERB bandwidth ~ formant spacing),
but it preserves their MOVEMENT. The agent reasons that the speaker-invariant cue is
whether a band's energy RISES or FALLS across the word, and writes the detector
ITSELF — a Term-tree from its own primitives (`Gt`, `Attr`, `Var`) over the early /
late windowed bands that enrich_sign_windows supplies:

    rises(band i)  ≡  Gt( band_i_late , band_i_early )

No Python computes the movement (np.diff would be the violation). The Term-tree IS
the agent's program and it executes on the substrate's OWN evaluator — exactly the
companion to formant_features (static peaks), but dynamics-over-time. The sign
EXHIBITS the movement features, so the developmental loop's invention + recognition
learn over them like any other feature. See [[ozma_concepts_in_gamma]] /
[[ozma_agent_writes_its_own_code]] / [[ozma_babble_loop]].
"""
from __future__ import annotations

from substrate_rs import Gt, Attr, Var

from .acoustic_resolution import get_resolution


def _rise_term(res: int, i: int):
    """Compose 'band i has more energy LATE than EARLY' (rises over the word) from
    primitives — the agent's program for 'this band moves up in time'."""
    s = Var("s")
    return Gt(a=Attr(s, f"band{res}_{i}_l"), b=Attr(s, f"band{res}_{i}_e"))


def compose_dynamics_features(substrate, resolution: int | None = None) -> int:
    """The agent composes a movement (rise) detector Term-tree for each band, FROM
    its primitives, because the dynamic cue is a band's change over time. Each
    becomes a `feature_kind=movement` Concept carrying the composed predicate.
    Returns the number minted."""
    res = resolution if resolution is not None else get_resolution(substrate)
    existing = {substrate.node(c)["attrs"].get("name")
                for c in substrate.nodes("Concept")
                if substrate.node(c)["attrs"].get("feature_kind") == "movement"}
    minted = 0
    for i in range(res):
        name = f"rise_band{res}_{i}"
        if name in existing:
            continue
        term = _rise_term(res, i)
        substrate.add_node("Concept", {
            "name": name, "feature_kind": "movement",
            "band": f"band{res}_{i}", "res": res, "idx": i,
            "predicate": term.to_dict(), "origin": "phonology",
            "composed_by": "agent"})
        minted += 1
    return minted


def evaluate_dynamics_features(substrate, signs=None) -> int:
    """Run the agent's composed movement Term-trees on signs via the substrate's
    OWN evaluator — the agent's program executes natively — adding an `exhibits`
    edge wherever a sign's band rises over the word. Returns edges added."""
    feats = [(c, substrate.node(c)["attrs"])
             for c in substrate.nodes("Concept")
             if substrate.node(c)["attrs"].get("feature_kind") == "movement"]
    if not feats:
        return 0
    try:
        substrate.add_production({
            "src": {"type": "AcousticSign", "var": "a"},
            "edge_type": "exhibits", "tgt": {"type": "Concept", "var": "b"},
            "provenance": "dynamics_features:exhibits"})
    except Exception:
        pass
    targets = signs if signs is not None else substrate.nodes("AcousticSign")
    added = 0
    for sign in targets:
        present = set(substrate.neighbours(sign, "exhibits"))
        for c, a in feats:
            term = _rise_term(int(a["res"]), int(a["idx"]))
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


def _formant_freq(res: int, lo: int, hi: int, tag: str) -> dict:
    """The formant FREQUENCY (peak bin) over bands [lo,hi) at time window `tag`, via
    the agent's OWN ArgMax primitive (the items-reduction it designed, returning the
    index = the formant frequency)."""
    s = Var("s")
    return {"type": "ArgMax",
            "items": [Attr(s, f"band{res}_{i}_{tag}").to_dict() for i in range(lo, hi)]}


def compose_formant_transitions(substrate, resolution: int | None = None) -> list:
    """The agent composes the FORMANT TRANSITION as an order-1-over-TIME concept of
    its own ArgMax formant frequency:

        transition(region) = F(late) - F(early),   F(t) = ArgMax(region bands @ t)

    It is the synthesis of two things the agent built itself: ArgMax (the formant
    FREQUENCY primitive it designed when its language lacked an index op) and the
    N-order meta-ability (order-1 over the TIME dimension). The transition is the
    dynamic that carries PLACE of articulation. Graph Term-tree, evaluated natively;
    no Python computes it. Returns [(concept_id, name)]."""
    from .acoustic_resolution import get_resolution
    from .order_n_concepts import nth_order_terms, _as_dict
    res = resolution if resolution is not None else get_resolution(substrate)
    half = max(1, res // 2)
    regions = [("F1", 0, half), ("F2", half, res)]
    existing = {substrate.node(c)["attrs"].get("name")
                for c in substrate.nodes("Concept")
                if substrate.node(c)["attrs"].get("feature_kind") == "formant_transition"}
    created = []
    for name, lo, hi in regions:
        cn = f"{name}_transition_r{res}"
        if cn in existing or hi - lo < 1:
            continue
        f_e = _formant_freq(res, lo, hi, "e")
        f_l = _formant_freq(res, lo, hi, "l")
        term = nth_order_terms([f_e, f_l], 1)[0]      # order-1 over TIME
        c = substrate.add_node("Concept", {
            "name": cn, "feature_kind": "formant_transition",
            "order": 1, "dimension": "time", "region": name, "res": res,
            "predicate": _as_dict(term), "origin": "phonology",
            "composed_by": "agent"})
        created.append((c, cn))
    return created


def compose_transition_features(substrate, resolution: int | None = None) -> list:
    """Exhibitable FORMANT-TRANSITION features for the developmental loop: per
    region (F1, F2), the boolean DIRECTION of the order-1-over-time formant sweep —
        rises ≡ Gt(ArgMax(region @ late), ArgMax(region @ early))
        falls ≡ Lt(...)
    i.e. is the formant FREQUENCY moving up or down across the word. This is the
    place-of-articulation dynamic, composed from the agent's own ArgMax + order-1-
    time — and it REPLACES the crude per-band rise. Stored predicate; evaluated
    natively. Returns [(concept_id, name)]."""
    from .acoustic_resolution import get_resolution
    res = resolution if resolution is not None else get_resolution(substrate)
    half = max(1, res // 2)
    existing = {substrate.node(c)["attrs"].get("name")
                for c in substrate.nodes("Concept")
                if substrate.node(c)["attrs"].get("feature_kind") == "transition"}
    created = []
    for name, lo, hi in (("F1", 0, half), ("F2", half, res)):
        if hi - lo < 1:
            continue
        f_e = _formant_freq(res, lo, hi, "e")
        f_l = _formant_freq(res, lo, hi, "l")
        for direction, op in (("rises", "Gt"), ("falls", "Lt")):
            cn = f"{name}_{direction}_r{res}"
            if cn in existing:
                continue
            pred = {"type": op, "a": f_l, "b": f_e}
            c = substrate.add_node("Concept", {
                "name": cn, "feature_kind": "transition", "region": name,
                "direction": direction, "order": 1, "dimension": "time", "res": res,
                "predicate": pred, "origin": "phonology", "composed_by": "agent"})
            created.append((c, cn))
    return created


def exhibit_predicate_features(substrate, feature_kind: str, signs=None) -> int:
    """Generic: exhibit every Concept of `feature_kind` whose STORED predicate
    Term-tree evaluates true on a sign, via the substrate's own evaluator. Lets the
    loop perceive through composed features (transitions, order-N, …) the same way
    it perceives through hand-written ones."""
    from .order_n_concepts import _Pred
    feats = [(c, substrate.node(c)["attrs"])
             for c in substrate.nodes("Concept")
             if substrate.node(c)["attrs"].get("feature_kind") == feature_kind]
    if not feats:
        return 0
    try:
        substrate.add_production({
            "src": {"type": "AcousticSign", "var": "a"},
            "edge_type": "exhibits", "tgt": {"type": "Concept", "var": "b"},
            "provenance": "dynamics_features:exhibits"})
    except Exception:
        pass
    targets = signs if signs is not None else substrate.nodes("AcousticSign")
    added = 0
    for sign in targets:
        present = set(substrate.neighbours(sign, "exhibits"))
        for c, a in feats:
            try:
                hit = bool(substrate.evaluate(_Pred(a["predicate"]), {"s": sign}))
            except Exception:
                hit = False
            if hit and c not in present:
                try:
                    substrate.add_edge(sign, "exhibits", c)
                    added += 1
                except Exception:
                    pass
    return added


__all__ = ["compose_dynamics_features", "evaluate_dynamics_features",
           "compose_formant_transitions", "compose_transition_features",
           "exhibit_predicate_features"]
