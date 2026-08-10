"""feature_generator — ideas OUTSIDE the seeded set.

The seed gives the agent an alphabet of primitives (Attr, Gt, Lt, Plus, Minus,
Div, Max, Min) and a grammar (the DSL) for composing them. That grammar generates
an INFINITE space of Term-trees — almost all of which the seed never names. An
"idea outside the seed" is just one of those compositions that the agent's
OBJECTIVE selects as good.

This is the generate-and-select engine of open-ended novelty:
  · generate(): compose a NOVEL Term-tree from primitives (a random walk of the
    grammar) — ratios, differences, nested resonances the seed never wrote.
  · select():   keep the ones the objective (here: digit discrimination) rates —
    the agent's curiosity/compression drive grounding which novelty is an idea.

The kept features are the agent's OWN inventions, not in any seed and not from any
LLM. See [[ozma_curiosity_drive]] / [[ozma_concepts_in_gamma]] /
[[ozma_agent_writes_its_own_code]].
"""
from __future__ import annotations

import random

from substrate_rs import (Attr, Lit, Var, Gt, Lt, Eq, And, Plus, Minus, Div,
                          Max, Min)


def _expr(bands, depth, rng):
    """Compose a scalar expression by walking the DSL grammar from primitives."""
    if depth <= 0 or rng.random() < 0.35:
        if rng.random() < 0.85:
            return Attr(Var("s"), rng.choice(bands))     # read a band
        return Lit(round(rng.uniform(-0.5, 0.5), 3))      # a constant
    a = _expr(bands, depth - 1, rng)
    b = _expr(bands, depth - 1, rng)
    op = rng.choice(("plus", "minus", "div", "max", "min"))
    if op == "plus":
        return Plus(items=(a, b))
    if op == "minus":
        return Minus(a=a, b=b)
    if op == "div":
        return Div(a=a, b=b)
    if op == "max":
        return Max(items=(a, b))
    return Min(items=(a, b))


def generate_feature(bands, rng, max_depth: int = 3):
    """A boolean FEATURE = a comparison of two composed expressions. This is a
    novel Term-tree from the grammar — an idea the seed did not contain."""
    a = _expr(bands, max_depth, rng)
    b = _expr(bands, max_depth, rng)
    return Gt(a=a, b=b) if rng.random() < 0.5 else Lt(a=a, b=b)


def _truth_rate(substrate, term, signs):
    if not signs:
        return None
    t = 0
    for s in signs:
        try:
            if substrate.evaluate(term, {"s": s}):
                t += 1
        except Exception:
            pass
    return t / len(signs)


def discover_features(substrate, signs_by_label, bands, n: int = 400,
                      keep: int = 6, seed: int = 0) -> list:
    """GENERATE n novel features from primitives; SELECT the most discriminative
    (largest spread of truth-rate across labels = it tells labels apart). Returns
    [(discrimination, term, per_label_rates)] for the kept ideas."""
    rng = random.Random(seed)
    scored = []
    for _ in range(n):
        f = generate_feature(bands, rng)
        rates = {}
        for label, signs in signs_by_label.items():
            r = _truth_rate(substrate, f, signs)
            if r is not None:
                rates[label] = r
        if len(rates) < 2:
            continue
        disc = max(rates.values()) - min(rates.values())
        # ignore degenerate always-true / always-false features
        if 0.02 < (sum(rates.values()) / len(rates)) < 0.98:
            scored.append((disc, f, rates))
    scored.sort(key=lambda x: -x[0])
    return scored[:keep]


class _Pred:
    """Thin carrier so a STORED predicate dict (on a Concept) runs on the
    substrate evaluator — the agent's graph-resident program executes natively."""
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def _size(d) -> int:
    """Complexity of a Term-tree = node count. The MDL penalty: simpler ideas are
    preferred (Occam), so overfit baroque compositions lose."""
    if not isinstance(d, dict):
        return 1
    n = 1
    for k, v in d.items():
        if k == "items":
            for it in v:
                n += _size(it)
        elif isinstance(v, dict):
            n += _size(v)
    return n


def _disc(substrate, term, by_label):
    rates = []
    for label, signs in by_label.items():
        r = _truth_rate(substrate, term, signs)
        if r is not None:
            rates.append(r)
    if len(rates) < 2:
        return None
    return (max(rates) - min(rates), sum(rates) / len(rates))


def discover_features_mdl(substrate, by_label_a, by_label_b, bands, n: int = 800,
                          keep: int = 8, lam: float = 0.03, seed: int = 0) -> list:
    """GENERATE n novel features; SELECT by COMPRESSION, not raw fit. A feature
    scores well only if it discriminates on BOTH cross-validation halves
    (generalises — kills the spread=1.0 overfit) AND is simple (MDL: gen -
    lam*size). This is the curiosity/compression drive as the selector. Returns
    [(score, gen, size, term)]."""
    rng = random.Random(seed)
    scored = []
    for _ in range(n):
        f = generate_feature(bands, rng)
        a = _disc(substrate, f, by_label_a)
        b = _disc(substrate, f, by_label_b)
        if a is None or b is None:
            continue
        (da, mean_a), (db, mean_b) = a, b
        if not (0.05 < (mean_a + mean_b) / 2 < 0.95):          # not degenerate
            continue
        gen = min(da, db)                  # must hold on BOTH halves to count
        size = _size(f.to_dict())
        score = gen - lam * size
        if score > 0:
            scored.append((score, gen, size, f))
    scored.sort(key=lambda x: -x[0])
    return scored[:keep]


def install_generated_features(substrate, winners) -> list:
    """Mint the agent's discovered features as graph-resident Concepts — its OWN
    inventions, outside any seed, written in its native Term-tree form."""
    ids = []
    for k, (score, gen, size, term) in enumerate(winners):
        c = substrate.add_node("Concept", {
            "name": f"gen_feat_{k}", "feature_kind": "generated",
            "origin": "phonology", "predicate": term.to_dict(),
            "gen_score": float(score), "composed_by": "agent_generate_select"})
        ids.append(c)
    return ids


def evaluate_composed_features(substrate, signs=None) -> int:
    """Run every graph-resident COMPOSED predicate (peak + generated) on signs via
    the substrate evaluator (rebuilt from the stored dict), adding `exhibits`."""
    feats = [(c, substrate.node(c)["attrs"]) for c in substrate.nodes("Concept")
             if substrate.node(c)["attrs"].get("feature_kind") in ("peak", "generated")
             and substrate.node(c)["attrs"].get("predicate")]
    if not feats:
        return 0
    try:
        substrate.add_production({
            "src": {"type": "AcousticSign", "var": "a"},
            "edge_type": "exhibits", "tgt": {"type": "Concept", "var": "b"},
            "provenance": "composed:exhibits"})
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


def _compression_root(substrate):
    for n in substrate.nodes("CompressionRoot"):
        return n
    # dials would normally be a seed; defaults here
    return substrate.add_node("CompressionRoot",
                              {"lam": 0.03, "threshold": 0.0, "origin": "agent"})


def compose_selection_rule(substrate) -> dict:
    """The agent WRITES its own selection RULE — graph-native, from primitives.
    The compression decision 'keep a candidate iff it GENERALISES (min of its two
    cross-validation discriminations) beats its COMPLEXITY cost' is composed as a
    Term-tree the agent authors:
        Gt( Minus( Min(disc_a, disc_b), Div(size, 1/lam) ), threshold )
    and installed as a graph Rule. No Python keep/drop — the substrate runs the
    agent's composed decision. Returns {'rule_index', 'term'}."""
    root = _compression_root(substrate)
    a = substrate.node(root)["attrs"]
    lam = float(a.get("lam", 0.03))
    thr = float(a.get("threshold", 0.0))
    C = Var("C")
    generalises = Min(items=(Attr(C, "disc_a"), Attr(C, "disc_b")))
    cost = Div(a=Attr(C, "size"), b=Lit(1.0 / lam))          # = lam * size
    compresses = Gt(a=Minus(a=generalises, b=cost), b=Lit(thr))   # the decision
    # ...only over candidates not yet judged, so firing the rule converges.
    where = And(items=(compresses, Eq(a=Attr(C, "kept"), b=Lit(0))))
    nat = substrate._inner if hasattr(substrate, "_inner") else substrate
    try:
        substrate.add_production({
            "src": {"type": "CompressionRoot", "var": "a"},
            "edge_type": "candidate", "tgt": {"type": "Concept", "var": "b"},
            "provenance": "compression:candidate"})
    except Exception:
        pass
    idx = nat.add_rule({
        "name": "select_by_compression",
        "match": [["R", "candidate", "C"]],
        "where": where.to_dict(),
        "effects": [["set_attr", "C", "kept",
                     {"__term__": Lit(1).to_dict()}]],
    })
    return {"rule_index": idx, "term": where, "root": root}


def agent_select_candidates(substrate, rule_index: int, candidates) -> list:
    """Wire candidate features under the compression root and fire the agent's OWN
    composed selection rule. Returns the kept candidates."""
    root = _compression_root(substrate)
    nat = substrate._inner if hasattr(substrate, "_inner") else substrate
    for c in candidates:
        try:
            substrate.add_edge(root, "candidate", c)
        except Exception:
            pass
    for _ in range(len(candidates) + 1):       # fire to fixed point
        nat.apply_rule_once(rule_index)
    return [c for c in candidates
            if substrate.node(c)["attrs"].get("kept") == 1]


__all__ = ["generate_feature", "discover_features", "discover_features_mdl",
           "install_generated_features", "evaluate_composed_features",
           "compose_selection_rule", "agent_select_candidates"]
