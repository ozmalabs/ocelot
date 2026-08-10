"""analogy — generate ideas by TRANSFER from vaguely-similar concepts.

Blind generation (feature_generator) searches the whole grammar uniformly: a huge
space, sparse signal, almost nothing survives selection. That is not how ideas are
found. Creativity is ANALOGY: you reach for something VAGUELY similar you already
know and carry its STRUCTURE into the new problem.

This module abstracts the structural SKELETON of every concept the agent holds —
across ALL its domains (phonology, vision, physics, ...) — by hollowing out the
domain-specific operands (which band / which constant) and keeping the operation
shape. Then it GENERATES candidates in the new domain by re-instantiating those
skeletons over the local features. A vision center-surround ("x minus its
surround") becomes a speech contrast; a physics scale-invariant ("a / b") becomes
a formant ratio. The agent's BREADTH becomes its source of ideas.

"Vaguely similar" = loose STRUCTURAL match, cross-domain, not exact. Transfer
biases generation toward shapes that have worked SOMEWHERE — then the compression
selector ([[ozma_ideas_outside_the_seed]]) keeps the transfers that generalise.
See [[ozma_concepts_in_gamma]] / [[ozma_insight_matches_human_cognition]].
"""
from __future__ import annotations


def _skeletonize(d):
    """Hollow a Term-tree into a reusable SHAPE: drop which-band and which-constant,
    keep the operation structure. This is the analogical 'form' of a concept."""
    if not isinstance(d, dict):
        return d
    ty = d.get("type")
    if ty == "Attr":
        return {"type": "Attr", "node": {"type": "Var", "name": "s"}, "key": "?band"}
    if ty == "Lit":
        return {"type": "Lit", "value": "?lit"}
    out = {}
    for k, v in d.items():
        if k == "items":
            out[k] = [_skeletonize(it) for it in v]
        elif isinstance(v, dict):
            out[k] = _skeletonize(v)
        else:
            out[k] = v
    return out


def _depth(d) -> int:
    if not isinstance(d, dict):
        return 0
    sub = [v for v in d.values() if isinstance(v, dict)]
    sub += [it for v in d.values() if isinstance(v, list) for it in v]
    return 1 + (max((_depth(s) for s in sub), default=0))


def abstract_patterns(substrate, min_depth: int = 2) -> list:
    """Gather the SHAPES of every predicate-bearing concept the agent holds, across
    all microtheories. Returns [(source_name, source_origin, skeleton_dict)],
    de-duplicated by skeleton. These are the vaguely-similar forms to transfer."""
    seen = {}
    out = []
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        pred = a.get("predicate")
        if not isinstance(pred, dict):
            continue
        if _depth(pred) < min_depth:
            continue
        skel = _skeletonize(pred)
        key = str(skel)
        if key in seen:
            continue
        seen[key] = True
        out.append((a.get("name", "?"), a.get("origin", "?"), skel))
    return out


def abstract_patterns_graph(substrate, skel_rules, min_depth: int = 2) -> list:
    """Like abstract_patterns, but the SKELETONISE step is done by the agent's OWN
    composed rewrite RULES over its materialised code (term_graph), not a Python
    walk. Returns [(source_name, source_origin, skeleton_dict)]."""
    from .term_graph import (materialize_term, dematerialize_term,
                             agent_skeletonize)
    seen, out = {}, []
    for c in list(substrate.nodes("Concept")):
        a = substrate.node(c)["attrs"]
        pred = a.get("predicate")
        if not isinstance(pred, dict) or a.get("feature_kind") == "candidate":
            continue
        if _depth(pred) < min_depth:
            continue
        root = materialize_term(substrate, pred)       # code -> graph
        agent_skeletonize(substrate, root, skel_rules)  # agent's rewrite rules
        skel = dematerialize_term(substrate, root)      # graph -> shape
        key = str(skel)
        if key in seen:
            continue
        seen[key] = True
        out.append((a.get("name", "?"), a.get("origin", "?"), skel))
    return out


def instantiate(skeleton, bands, rng):
    """Re-fill a skeleton's holes with THIS domain's features — the transfer step.
    Returns a concrete Term-tree dict (ready to run via the substrate evaluator)."""
    if not isinstance(skeleton, dict):
        return skeleton
    ty = skeleton.get("type")
    if ty == "Attr":
        return {"type": "Attr", "node": {"type": "Var", "name": "s"},
                "key": rng.choice(bands)}
    if ty == "Lit":
        return {"type": "Lit", "value": round(rng.uniform(-0.5, 0.5), 3)}
    out = {}
    for k, v in skeleton.items():
        if k == "items":
            out[k] = [instantiate(it, bands, rng) for it in v]
        elif isinstance(v, dict):
            out[k] = instantiate(v, bands, rng)
        else:
            out[k] = v
    return out


def generate_by_transfer(patterns, bands, rng):
    """Pick a vaguely-similar concept's shape and transfer it into this domain.
    Returns (source_name, source_origin, concrete_term_dict)."""
    name, origin, skel = patterns[rng.randrange(len(patterns))]
    return name, origin, instantiate(skel, bands, rng)


def discover_by_transfer(substrate, by_label_a, by_label_b, bands, n: int = 800,
                         keep: int = 8, lam: float = 0.03, seed: int = 0) -> list:
    """The autonomous idea-engine, ANALOGY-GUIDED: instead of blind composition,
    generate candidates by TRANSFER from the agent's vaguely-similar concepts
    (across all its domains), then SELECT by compression (cross-validated
    discrimination minus complexity). Returns
    [(score, gen, size, term_dict, source_origin, source_name)]."""
    import random
    from .feature_generator import _disc, _size, _Pred

    pats = abstract_patterns(substrate)
    if not pats:
        return []
    rng = random.Random(seed)
    scored = []
    for _ in range(n):
        name, origin, term_dict = generate_by_transfer(pats, bands, rng)
        a = _disc(substrate, _Pred(term_dict), by_label_a)
        b = _disc(substrate, _Pred(term_dict), by_label_b)
        if a is None or b is None:
            continue
        (da, ma), (db, mb) = a, b
        if not (0.05 < (ma + mb) / 2 < 0.95):
            continue
        gen = min(da, db)
        size = _size(term_dict)
        score = gen - lam * size
        if score > 0:
            scored.append((score, gen, size, term_dict, origin, name))
    scored.sort(key=lambda x: -x[0])
    return scored[:keep]


def install_transfer_features(substrate, winners) -> list:
    """Mint the agent's analogically-discovered features as graph-resident
    Concepts, recording which vaguely-similar concept each was drawn from.
    Returns [(concept_id, 'origin:name')]."""
    ids = []
    for k, (score, gen, size, term_dict, origin, name) in enumerate(winners):
        c = substrate.add_node("Concept", {
            "name": f"xfer_{k}_{name}", "feature_kind": "generated",
            "origin": "phonology", "predicate": term_dict,
            "gen_score": float(score), "drawn_from": f"{origin}:{name}",
            "composed_by": "agent_analogy"})
        ids.append((c, f"{origin}:{name}"))
    return ids


__all__ = ["abstract_patterns", "abstract_patterns_graph", "instantiate",
           "generate_by_transfer", "discover_by_transfer",
           "install_transfer_features"]
