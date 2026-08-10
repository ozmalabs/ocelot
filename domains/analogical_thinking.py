"""Analogical thinking — Jabberwock's cross-domain SHAPE finder.

Per user: 'part of jabberwock allows it to look for similar shapes -
make this accessible when thinking like this. Thinking needs to be
n-abstractable (eg think harder and more abstractly if you aren't
happy with the answer)'.

Jabberwock already has analogy.py for Term-tree skeletonization and
order_n_concepts.py for finite-difference abstraction. Those work
on perceptual Term-trees. What this module adds: analogical-shape
matching across CONCEPT-LEVEL vocabulary, with a DIAL for abstraction
order n.

The thinking process:
  · Given a directive (a Directive node, or just two Mts to bridge)
  · For each concept in source Mt, scan target Mt for structural match
  · Dial of abstraction order n:
      n=0  exact name overlap
      n=1  category match + definition keyword overlap
      n=2  functional-role match (input/output/regulator/storage/etc.)
      n=3  abstract-principle match (homeostatic, predictive,
           pattern-completing, integrative, gating, selecting)
      n=4  meta-shape match (the principle of how it operates
           regardless of what it operates on)
  · If the agent isn't satisfied with answers at one n, it raises
    n and tries again — abstracting further.

When a match is found, an Analogy graph node is created with the
order_n attr + source + target + rationale. Jabberwock's graph
gains the bridge.
"""
from __future__ import annotations

import re
from typing import Any


# The order-2/3/4 classifier vocabulary (FunctionalRole / ShapePrinciple /
# MetaShape) was here as three Python dicts. It is now GRAPH DATA, seeded in
# seeds/shape_vocabulary.json and read via the helpers below (keyword matching
# is a Term run by Rust). Adding a shape = adding a node to that seed, not
# editing this file.


def _tokens(text: str) -> set[str]:
    """Tokenize text + name. Strip casing + non-letters."""
    return set(re.findall(r"[a-z]{3,}", text.lower()))


def _concept_text(substrate, concept_node) -> tuple[str, str, str]:
    a = substrate.node(concept_node)["attrs"]
    return (
        str(a.get("name", "")).lower(),
        str(a.get("category", "")).lower(),
        str(a.get("definition", "")).lower(),
    )


# ---------------------------------------------------------------------------
# The classifier vocabulary is GRAPH DATA (seeds/shape_vocabulary.json):
# FunctionalRole / ShapePrinciple nodes (each with a `keywords` list) and
# MetaShape nodes wired -has_principle-> their constituent principles. The
# "which keyword is in this text" decision is a Term run by the Rust evaluator
# (substring test), not a Python keyword loop. These helpers are mechanical
# adapter glue: read the vocabulary nodes, hand each to the Term, collect hits.
# ---------------------------------------------------------------------------
def _native_eval(substrate):
    s = getattr(substrate, "s", substrate)
    return getattr(s, "_inner", s)


def _kw_hit_term(text: str) -> dict:
    """Term: does the `keywords` list of the node bound to Var 'v' contain a
    substring of `text`? (StringIndexOf >= 0 over each keyword.)"""
    V = lambda n: {"type": "Var", "name": n}
    L = lambda x: {"type": "Lit", "value": x}
    return {"type": "Exists",
            "source": {"type": "Attr", "node": V("v"), "key": "keywords"},
            "var_name": "kw",
            "predicate": {"type": "Gte",
                          "a": {"type": "StringIndexOf", "haystack": L(text), "needle": V("kw")},
                          "b": L(0)}}


def _vocab_hits(substrate, voc_type: str, text: str) -> set[str]:
    """Names of vocabulary nodes of `voc_type` whose keywords hit `text`."""
    sub = getattr(substrate, "s", substrate)
    native = _native_eval(substrate)
    term = _kw_hit_term(text)
    hits = set()
    try:
        nodes = list(sub.nodes(voc_type))
    except Exception:
        return hits
    for n in nodes:
        if native.evaluate(term, {"v": n}):
            nm = sub.node(n)["attrs"].get("name")
            if nm:
                hits.add(nm)
    return hits


def _concept_functional_roles(substrate, concept_node) -> set[str]:
    """Order-2 abstraction: which functional roles does this concept
    play? Vocabulary + keyword-match are graph data / a Term in Rust."""
    name, _, defn = _concept_text(substrate, concept_node)
    return _vocab_hits(substrate, "FunctionalRole", name + " " + defn)


def _concept_abstract_principles(substrate, concept_node) -> set[str]:
    """Order-3 abstraction: which abstract principles does this concept
    embody? Read off the seeded ShapePrinciple vocabulary via a Term."""
    name, _, defn = _concept_text(substrate, concept_node)
    return _vocab_hits(substrate, "ShapePrinciple", name + " " + defn)


def _concept_meta_shapes(substrate, concept_node) -> set[str]:
    """Order-4 abstraction: meta-shapes of operation. A MetaShape is hit when
    any of its has_principle neighbours is among the concept's principles —
    membership read from the graph (has_principle edges), not a Python dict."""
    principles = _concept_abstract_principles(substrate, concept_node)
    if not principles:
        return set()
    sub = getattr(substrate, "s", substrate)
    shapes = set()
    for sh in sub.nodes("MetaShape"):
        prins = {sub.node(p)["attrs"].get("name") for p in sub.neighbours(sh, "has_principle")}
        if principles & prins:
            shapes.add(sub.node(sh)["attrs"].get("name"))
    return shapes


def _list_concepts(substrate, mt_node) -> list:
    return list(substrate.neighbours(mt_node, "has_concept"))


def _find_mt(substrate, name: str):
    for mt in substrate.nodes("Microtheory"):
        if str(substrate.node(mt)["attrs"].get("name", "")) == name:
            return mt
    return None


def shape_hits(substrate, text: str) -> set[str]:
    """The set of MetaShapes whose constituent principles (has_principle edges)
    have a keyword that is a substring of `text`. Vocabulary = graph data;
    keyword match = a Term run by Rust. Public helper for analysis tooling that
    wants the agent's own shape reading of an arbitrary string."""
    text = (text or "").lower()
    if not text:
        return set()
    principles = _vocab_hits(substrate, "ShapePrinciple", text)
    if not principles:
        return set()
    sub = getattr(substrate, "s", substrate)
    shapes = set()
    for sh in sub.nodes("MetaShape"):
        prins = {sub.node(p)["attrs"].get("name") for p in sub.neighbours(sh, "has_principle")}
        if principles & prins:
            shapes.add(sub.node(sh)["attrs"].get("name"))
    return shapes


# ---------------------------------------------------------------------------
# Meta-shape realisation counts — the RELATIVE within-order-4 quantity.
# The seven organising meta-shapes all sit at the SAME abstraction order (n=4);
# order_n cannot separate them. What places one above another is the COUNT of
# concepts that realise it (its feature count over the population) — a relative
# quantity, not a hand-set weight. Read at query time (cached per population
# size, since it scans every Concept) so the agent's self-shape ratio is
# derived, never asserted.
# ---------------------------------------------------------------------------
_METASHAPE_COUNT_CACHE: dict[tuple, dict[str, int]] = {}


def metashape_realisation_counts(substrate) -> dict[str, int]:
    """For each MetaShape, how many of the agent's Concepts realise it
    (has_principle → ShapePrinciple keyword hit). The relative feature count
    that places the meta-shapes against one another at order 4."""
    sub = getattr(substrate, "s", substrate)
    try:
        concepts = list(sub.nodes("Concept"))
    except Exception:
        return {}
    key = (id(sub), len(concepts))
    cached = _METASHAPE_COUNT_CACHE.get(key)
    if cached is not None:
        return cached
    tally: dict[str, int] = {}
    for c in concepts:
        for ms in _concept_meta_shapes(sub, c):
            tally[ms] = tally.get(ms, 0) + 1
    _METASHAPE_COUNT_CACHE[key] = tally
    return tally


def find_analogies(substrate, source_mt_name: str,
                    target_mt_names: list[str], order_n: int = 2,
                    min_score: int = 1) -> list[dict]:
    """The core thinking primitive. For each concept in source Mt,
    find concepts in target Mts that match at abstraction order n.

    order_n controls how abstract the matching is:
      n=0  exact name overlap
      n=1  shared category + definition keyword overlap
      n=2  shared functional role (scheduler, memory, gate, etc.)
      n=3  shared abstract principle (homeostasis, prediction, ...)
      n=4  shared meta-shape (feedback control, associative recall, ...)

    Higher n = more abstract = more cross-domain analogies.

    RANKING IS RELATIVE, not a fixed cross-order exchange rate. An
    analogy is placed by its POSITION on the abstraction axis — the
    HIGHEST order at which the pair matches (`order_n`) — and, within
    that order, by the COUNT of shared features (`feature_count`, a
    relative within-axis quantity). There is no hand-set "a meta-shape
    match is worth exactly 5x a keyword match" magnitude; a higher-order
    match simply outranks a lower-order one, and same-order matches are
    ordered by how many features they share.

    `min_score` is a floor on the total number of shared features
    (default 1 ⇒ keep any pair that matches at all).

    Returns list of {source_concept, target_concept, source_mt,
    target_mt, order_n, feature_count, features_total, rationale}.
    """
    source_mt = _find_mt(substrate, source_mt_name)
    if source_mt is None:
        return []

    target_mts = []
    for nm in target_mt_names:
        mt = _find_mt(substrate, nm)
        if mt is not None:
            target_mts.append((nm, mt))

    if not target_mts:
        return []

    results = []
    for sc in _list_concepts(substrate, source_mt):
        for tgt_mt_name, tgt_mt in target_mts:
            for tc in _list_concepts(substrate, tgt_mt):
                analogy = _compute_analogy(
                    substrate, sc, tc, order_n,
                    source_mt_name, tgt_mt_name)
                if analogy and analogy["features_total"] >= min_score:
                    results.append(analogy)
    return results


def _compute_analogy(substrate, sc, tc, order_n: int,
                       src_mt_name: str, tgt_mt_name: str
                       ) -> dict | None:
    """Compute the RELATIVE placement of an analogy between two concepts,
    scanning up to abstraction order `order_n`.

    Instead of summing hand-set per-order weights into an absolute score,
    this records, at every order, the COUNT of shared features. The pair's
    placement is then two relative quantities read off that record:

      · order_n      — the HIGHEST order at which the pair matches (its
                        POSITION on the abstraction axis). A meta-shape
                        match sits higher than a name-token match because
                        it is further up the axis, not because it was
                        multiplied by 5.
      · feature_count — how many features are shared AT that highest order
                        (a relative within-axis quantity; the tiebreaker
                        between two analogies that reach the same order).

    `features_total` (sum of shared features over all orders) is kept only
    as the match/no-match floor for `find_analogies`' `min_score`.
    """
    sn, scat, sdef = _concept_text(substrate, sc)
    tn, tcat, tdef = _concept_text(substrate, tc)

    if sn == tn:
        return None  # same concept; not an analogy

    # per_order[k] = number of features the pair shares at order k.
    per_order: dict[int, int] = {}
    rationale_parts = []

    if order_n >= 0:
        # n=0: name token overlap
        st = _tokens(sn)
        tt = _tokens(tn)
        overlap = st & tt
        if overlap:
            per_order[0] = len(overlap)
            rationale_parts.append(
                f"shared name tokens: {sorted(overlap)[:3]}")

    if order_n >= 1:
        # n=1: category overlap + definition keyword overlap
        n1 = 0
        if scat and scat == tcat:
            n1 += 1
            rationale_parts.append(f"shared category '{scat}'")
        sdt = _tokens(sdef)
        tdt = _tokens(tdef)
        common = sdt & tdt
        if len(common) >= 3:
            n1 += len(common)
            rationale_parts.append(
                f"definition overlap ({len(common)} tokens)")
        if n1:
            per_order[1] = n1

    if order_n >= 2:
        # n=2: shared functional roles
        sroles = _concept_functional_roles(substrate, sc)
        troles = _concept_functional_roles(substrate, tc)
        shared_roles = sroles & troles
        if shared_roles:
            per_order[2] = len(shared_roles)
            rationale_parts.append(
                f"shared functional role: "
                f"{', '.join(sorted(shared_roles))}")

    if order_n >= 3:
        # n=3: shared abstract principles
        sp = _concept_abstract_principles(substrate, sc)
        tp = _concept_abstract_principles(substrate, tc)
        shared_p = sp & tp
        if shared_p:
            per_order[3] = len(shared_p)
            rationale_parts.append(
                f"shared abstract principle: "
                f"{', '.join(sorted(shared_p))}")

    if order_n >= 4:
        # n=4: shared meta-shapes
        sm = _concept_meta_shapes(substrate, sc)
        tm = _concept_meta_shapes(substrate, tc)
        shared_m = sm & tm
        if shared_m:
            per_order[4] = len(shared_m)
            rationale_parts.append(
                f"shared meta-shape: "
                f"{', '.join(sorted(shared_m))}")

    if not per_order:
        return None

    top_order = max(per_order)                 # POSITION on the axis
    feature_count = per_order[top_order]        # relative within-axis count
    features_total = sum(per_order.values())    # match/no-match floor only

    return {
        "source_concept": sn,
        "target_concept": tn,
        "source_mt": src_mt_name,
        "target_mt": tgt_mt_name,
        "source_node": sc,
        "target_node": tc,
        "order_n": top_order,
        "feature_count": feature_count,
        "features_total": features_total,
        "rationale": "; ".join(rationale_parts),
    }


def emit_analogy_as_graph(substrate, analogy: dict) -> Any | None:
    """Create an Analogy graph node from a found analogy."""
    try:
        node = substrate.add_node("Analogy", {
            "source_concept": analogy["source_concept"],
            "target_concept": analogy["target_concept"],
            "source_mt": analogy["source_mt"],
            "target_mt": analogy["target_mt"],
            # RELATIVE placement: axis position + within-axis feature count.
            # No absolute exchange-rate score is stored.
            "order_n": int(analogy["order_n"]),
            "feature_count": int(analogy["feature_count"]),
            "features_total": int(analogy["features_total"]),
            "rationale": analogy["rationale"],
        })
        # Also add implements edge if the abstraction is high enough
        # (n >= 2). Lower-n matches are coincidence; n >= 2 indicates
        # genuine structural correspondence.
        if analogy["order_n"] >= 2:
            try:
                substrate.add_edge(analogy["source_node"], "implements",
                                   analogy["target_node"], {})
            except Exception:
                pass
        return node
    except Exception:
        return None


def think_harder(substrate, source_mt_name: str,
                  target_mt_names: list[str], start_n: int = 1,
                  max_n: int = 4, want_at_least: int = 5
                  ) -> dict:
    """The n-abstractable thinking process. Start at order start_n;
    if fewer than want_at_least analogies found, dial up the order +
    try again. Continue until satisfied or max_n reached.

    This implements 'think harder and more abstractly if not happy
    with the answer'.

    Returns {order_used, analogies, satisfied, n_emitted}.
    """
    for n in range(start_n, max_n + 1):
        analogies = find_analogies(
            substrate, source_mt_name, target_mt_names, order_n=n)
        if len(analogies) >= want_at_least:
            # Emit the highest-placed analogies as graph data. Ranking is
            # RELATIVE: primary key = order_n (axis position — a higher-order
            # match outranks a lower-order one), tiebreaker = feature_count
            # (shared features at that order), then features_total. No fixed
            # cross-order multiplier decides the order.
            top = sorted(analogies,
                         key=lambda a: (-a["order_n"], -a["feature_count"],
                                        -a["features_total"]))
            n_emitted = 0
            seen = set()
            for a in top[:50]:
                key = (a["source_concept"], a["target_concept"])
                if key in seen:
                    continue
                seen.add(key)
                if emit_analogy_as_graph(substrate, a) is not None:
                    n_emitted += 1
            return {
                "order_used": n,
                "analogies": top,
                "satisfied": True,
                "n_found": len(analogies),
                "n_emitted": n_emitted,
                "start_n": start_n,
                "rationale": (
                    f"Found {len(analogies)} analogies at order n={n}; "
                    f"started at n={start_n}. Satisfied."
                ),
            }
    # Reached max_n without enough analogies
    return {
        "order_used": max_n,
        "analogies": find_analogies(
            substrate, source_mt_name, target_mt_names, order_n=max_n),
        "satisfied": False,
        "n_found": 0,
        "n_emitted": 0,
        "start_n": start_n,
        "rationale": (
            f"Reached max_n={max_n} without finding {5} analogies. "
            f"Either domains are genuinely disjoint or matching "
            f"machinery needs richer keyword vocabulary."
        ),
    }


__all__ = [
    "find_analogies", "emit_analogy_as_graph", "think_harder",
    "metashape_realisation_counts",
]
