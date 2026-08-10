"""order_n_composition — the ONE recursive-composition operator, named.

RECOGNITION + COLLAPSE (not a new mechanism). The agent already holds its
order-N operator in two lifts:

  · domains/order_n_concepts.py   — the finite difference over a SIGNAL: the
    bedrock is sample values, the STEP is SUBTRACTION (`_minus`), order-N is the
    STEP applied N times:   ``t = samples; for _ in range(N): t = step(t)``.
  · domains/order_n_reasoning.py  — the same iterate-to-N over RELATIONS: the
    bedrock is stored facts, the STEP is "compose one more entity-sharing fact",
    order-N = the STEP applied N times.
  · domains/order_n_postulates.py — the same lift to KNOWLEDGE: bedrock is a
    held postulate, the STEP is "transfer an implication-shape", order-N is the
    N-th implication.

The COMPUTE TOWER (compute_grounding / read_and_ground / grounded_representation)
is the SAME operator with yet another STEP — FUNCTION COMPOSITION — and yet
another BEDROCK — held primitives / operations:

  · order-0  = a held primitive / operation (gcd, count, range, plus; a seeded
               basis Concept built_from nothing).
  · order-1  = an operation OVER order-0 parts (divisor_count = count over a
               range; aliquot_sum = divisor_sum - n).
  · order-2  = a concept OVER order-1 operations (is_prime = divisor_count == 2;
               abundant_number = aliquot_sum > n).
  · order-N  = a combination composing over order-(N-1) grounded parts.

So the bespoke "tier" of the compute tower IS the ORDER, and the bespoke
"climb a tier by reading" IS order N -> N+1: synthesizing order-N composes the
combination over order-(N-1) grounded parts; reading+grounding a sub-concept one
level deeper increments the order.

This module is the COLLAPSE: it names ONE recursive-composition operator
``iterate_to_n`` parameterised by (STEP rule, BEDROCK test). Both the
finite-difference order-N (subtraction rule) and the compute-tower order-N
(function-composition rule) are this one operator with the rule swapped — fewer
mechanisms, one principle. It then computes the ORDER (composition depth) of a
grounded concept VIA the inverse of that same recursion (not a bespoke counter)
and stores it on the concept.

HONEST — what stays DISTINCT (named, not hidden):
  · the COMBINATION RULE differs — subtraction for the signal derivative,
    function-composition for the compute tower (and entity-join for relations,
    implication-transfer for knowledge);
  · the BEDROCK differs — sample values vs held primitives/operations vs facts
    vs postulates.
The unification is the recursive-composition SHAPE, parameterised by rule +
bedrock — NOT a claim that the rules or bedrock are the same.

No LLM, no Rust, no new capability. A WORLD ADAPTER / recognition: it reuses
order_n_concepts' recursion shape and reads the agent's own grounding graph.
See [[ozma_order_n_concepts]] / [[ozma_order_n_analysis_by_synthesis]] /
[[ozma_meta_abilities_are_leverage]].
"""
from __future__ import annotations

import json
from typing import Any, Callable, Optional


# ---------------------------------------------------------------------------
# THE ONE OPERATOR — iterate a STEP from a BEDROCK, N times. This is the shape
# order_n_concepts.nth_order_terms and order_n_reasoning.chain_to_order both run:
#     t = bedrock; for _ in range(N): t = step(t)
# The STEP (the COMBINATION RULE) and the bedrock are PARAMETERS — that is the
# whole unification: one recursion, the rule is a knob.
# ---------------------------------------------------------------------------

def iterate_to_n(bedrock: Any, step: Callable[[Any], Any], n: int) -> Any:
    """Apply the COMBINATION-RULE `step` to `bedrock`, `n` times — the agent's
    order-N recursive-composition machine, with the rule as a parameter.

    · order_n_concepts: bedrock = signal samples, step = adjacent SUBTRACTION
      -> the order-N finite difference (nth_order_terms IS this call).
    · the compute tower: bedrock = held primitives, step = FUNCTION COMPOSITION
      -> the order-N composed concept.
    One operator; the STEP is the only thing that changes between the signal
    derivative and the compute tower."""
    t = bedrock
    for _ in range(max(0, n)):
        t = step(t)
    return t


def finite_difference_order_n(samples: list, n: int) -> list:
    """The SIGNAL instance of `iterate_to_n`: the order-N finite difference, the
    SUBTRACTION rule. Identical in shape + result to
    order_n_concepts.nth_order_terms — re-expressed through the one operator to
    make the collapse explicit (the signal derivative IS iterate_to_n with the
    subtraction step). Returns numeric differences for numeric samples; for
    symmetry with order_n_concepts it also accepts the Term-building minus."""
    def _subtract_step(xs):
        return [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]
    return iterate_to_n(list(samples), _subtract_step, n)


# ---------------------------------------------------------------------------
# THE COMPUTE-TOWER INSTANCE — the ORDER of a grounded concept = the composition
# DEPTH of its combination over order-0 bedrock. This is the INVERSE read of the
# same recursion: order-0 bedrock is a held primitive (depth 0); a combination
# composing over order-(N-1) parts is order N. We compute it RECURSIVELY (the
# composition depth IS the recursion depth), reusing iterate_to_n's shape — the
# FUNCTION-COMPOSITION rule, run as a fold over the combination Term-tree — not a
# bespoke counter.
# ---------------------------------------------------------------------------

# Leaf kinds that are order-0 in a combination Term-tree (no further composition):
#   · a Var leaf (a parameter name, a string) — an operand slot, not a head;
#   · a literal (int/float/bool) — a constant.
def _is_term_leaf(node: Any) -> bool:
    return isinstance(node, (str, bool, int, float))


def _subconcept_depth(node: Any, is_bedrock_head: Callable[[str], bool]) -> int:
    """The composition DEPTH of a combination Term-tree counted in TIERS of
    composed (non-bedrock) sub-concepts — the order-N read the examples use:

      · order-0  = a held primitive / operand leaf (count, range, divides, plus,
                   divisor_sum; a Var; a literal). A bedrock head's internal
                   arithmetic does NOT add a tier — it IS the order-0 basis.
      · order-1  = a combination that is ONLY bedrock heads over order-0 operands
                   (divisor_count = count over a range -> one tier of composition).
      · order-N  = a combination that references an order-(N-1) COMPOSED sub-concept
                   (is_prime = divisor_count == 2 -> eq, a bedrock head, over the
                   order-1 sub-concept divisor_count -> order 2).

    This is the FUNCTION-COMPOSITION rule of the one operator (iterate_to_n's
    step), folded over the tree, bottoming out at order-0 BEDROCK — the same
    'apply the step until you hit bedrock' recursion as the finite difference,
    with bedrock = held primitives instead of sample values.

    Returns the tier depth CONTRIBUTED BY composed sub-concept heads under `node`
    (0 if the subtree is pure bedrock). order_of_combination adds the +1 for the
    combination itself."""
    if _is_term_leaf(node):
        return 0
    if not isinstance(node, dict) or not node:
        return 0
    head = next((k for k in node if k != "force"), None)
    if head is None:
        return 0
    spec = node[head]
    children = list(spec.values()) if isinstance(spec, dict) else []
    child = max((_subconcept_depth(c, is_bedrock_head) for c in children),
                default=0)
    # A NON-bedrock head names a COMPOSED sub-concept — it adds a tier (its own
    # order is 1 + the deepest composed thing UNDER it). A bedrock head adds no
    # tier of its own (it is order-0 basis); it only passes through the deepest
    # composed sub-concept among its children.
    if is_bedrock_head(head):
        return child
    return 1 + child


def order_of_combination(combination: Any,
                         is_bedrock_head: Optional[Callable[[str], bool]] = None
                         ) -> int:
    """The ORDER (composition depth) of a combination Term-tree over order-0
    bedrock: 0 for a bedrock primitive (no combination / a bare leaf), else the
    NESTING DEPTH of composed heads. A combination of a single held op over
    operand leaves is order-1; an op over an op is order-2; etc.

    `is_bedrock_head` (optional) is the BEDROCK TEST — which head names are
    order-0 primitives. When given, a tree that is exactly one bedrock head over
    leaves is order-1 (an operation over order-0 operands), matching the
    examples (divisor_count = count over a range -> order-1). Default treats any
    head as a composition level (structural depth)."""
    if combination is None:
        return 0
    tree = combination
    if isinstance(combination, str):
        # a named-string combination ('rel(a,b)') is NOT a runnable tree — it is a
        # single order-1 relational composition over its named parts.
        s = combination.strip()
        if s.startswith("{") or s.startswith("["):
            try:
                tree = json.loads(s)
            except Exception:
                return 1
        else:
            return 1
    if _is_term_leaf(tree):
        return 0
    bh = is_bedrock_head or (lambda _h: False)
    # order = 1 (this combination is itself a composition over operands) + the
    # deepest tier of COMPOSED sub-concepts it references. A pure-bedrock tree
    # (only held primitives over leaves) is order-1; referencing an order-(N-1)
    # sub-concept makes it order-N.
    return 1 + _subconcept_depth(tree, bh)


# ---------------------------------------------------------------------------
# THE GRAPH READ — a grounded concept's ORDER from its built_from CONE, the same
# recursion as the combination depth but over the GROUNDING GRAPH (so a concept
# grounded by built_from edges, whose combination may be a named string, still
# gets an order = the depth of its cone to the seeded primitives). order-0 = a
# primitive (built_from nothing); order(c) = 1 + max(order(part)).
# ---------------------------------------------------------------------------

def order_from_cone(substrate, cid, *, edge_type: str = "built_from",
                    _seen: Optional[set] = None) -> int:
    """The ORDER of a grounded Concept node = the composition depth of its
    built_from cone over the seeded primitives. A primitive (built_from nothing)
    is order-0; a concept built over order-k parts is order k+1. Computed
    RECURSIVELY (the composition depth IS the recursion depth) — the same
    iterate-to-N shape, here as a fold over the grounding graph, NOT a bespoke
    counter. Cycle-safe (a definitional loop contributes 0 at re-entry)."""
    seen = _seen if _seen is not None else set()
    if cid in seen:
        return 0
    try:
        parts = list(substrate.neighbours(cid, edge_type))
    except Exception:
        parts = []
    if not parts:
        return 0                                   # order-0: a primitive.
    seen = seen | {cid}
    return 1 + max(order_from_cone(substrate, p, edge_type=edge_type,
                                   _seen=seen) for p in parts)


def compute_concept_order(substrate, concept_id, *,
                          combination: Any = None,
                          is_bedrock_head: Optional[Callable[[str], bool]] = None
                          ) -> dict[str, Any]:
    """Compute a grounded concept's ORDER (composition depth) two consistent
    ways and store it on the node:

      · cone_order — from the built_from CONE over the grounding graph (works for
        ANY grounded concept, string or tree combination).
      · combination_order — from the runnable combination Term-tree's head nesting
        (works when the combination is an executable tree).

    Both are the SAME order-N recursion (fold the composition rule until you hit
    order-0 bedrock). Returns {order, cone_order, combination_order, is_primitive}
    and sets the `order` + `order_via` attrs on the concept (graph data the agent
    OWNS, the order_n_concepts composed_by=agent idiom). The stored `order` is the
    cone order (the structural ground truth); combination_order is recorded for
    cross-check."""
    if combination is None:
        try:
            combination = substrate.node(concept_id)["attrs"].get("combination")
        except Exception:
            combination = None
    cone_order = order_from_cone(substrate, concept_id)
    # The combination cross-check's BEDROCK TEST defaults to the STRUCTURAL one:
    # a head names an order-0 primitive iff its Concept node is built_from nothing
    # (a seeded basis). This makes combination_order agree with cone_order
    # independent of the transient 'currently-held' caps snapshot — a head that is
    # a COMPOSED sub-concept (built_from something) adds a tier; a primitive head
    # does not. (A caller may override with an explicit is_bedrock_head.)
    if is_bedrock_head is None:
        def _structural_bedrock(head: str, _s=substrate) -> bool:
            try:
                for c in _s.nodes("Concept"):
                    if _s.node(c)["attrs"].get("name") == head:
                        return len(_s.neighbours(c, "built_from")) == 0
            except Exception:
                return True
            return True                       # unknown head -> treat as bedrock.
        bedrock_test = _structural_bedrock
    else:
        bedrock_test = is_bedrock_head
    combo_order = (order_of_combination(combination, bedrock_test)
                   if combination is not None else None)
    is_prim = (cone_order == 0)
    order = cone_order
    try:
        substrate.set_attr(concept_id, "order", int(order))
        substrate.set_attr(concept_id, "order_via",
                           "order_n_composition:cone(built_from)")
        if combo_order is not None:
            substrate.set_attr(concept_id, "combination_order", int(combo_order))
    except Exception:
        pass
    return {"order": order, "cone_order": cone_order,
            "combination_order": combo_order, "is_primitive": is_prim}


def annotate_all_orders(substrate) -> dict[str, int]:
    """Compute + store the ORDER of every grounded Concept (one with a
    combination or built_from edges, plus the primitives at order-0). Returns
    {concept_name: order}. The agent's whole grounded vocabulary, given its
    composition depth — the tower made legible as the order-N it already is."""
    out: dict[str, int] = {}
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        name = a.get("name")
        if not isinstance(name, str):
            continue
        has_combo = a.get("combination") is not None
        try:
            has_parts = len(substrate.neighbours(c, "built_from")) > 0
        except Exception:
            has_parts = False
        if not (has_combo or has_parts):
            # a bare primitive with neither parts nor a combination is still
            # order-0; record only those that are part of the grounding graph
            # (the basis primitives the composed concepts reduce to).
            try:
                grounded = len(substrate.neighbours(c, "grounds")) > 0
            except Exception:
                grounded = False
            if not grounded:
                continue
        res = compute_concept_order(substrate, c)
        out[name] = res["order"]
    return out


__all__ = [
    "iterate_to_n",
    "finite_difference_order_n",
    "order_of_combination",
    "order_from_cone",
    "compute_concept_order",
    "annotate_all_orders",
]
