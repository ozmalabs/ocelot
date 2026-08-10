"""Shape-lifted harvester — donor shapes matched by Shape compatibility,
not regex keyword overlap.

Per user: 'lift the harvester to Shape, this is the thesis-correct move.'

The existing harvester (implication_harvester.py) builds donor shapes
from rule if-clauses by extracting keywords and turning them into regex
match_patterns. That's lexical matching — the wrong measure per the
function_shape pivot's thesis.

This module walks the substrate's REAL Term-trees (the concepts with
actual ConceptResolver entries — currently the 5 bootstrap concepts
from commit cdb0062 plus any others the agent has authored) and
produces donor entries keyed by Shape (recursion / order_n /
abstraction). Match is via shapes_compatible — the Cousot abstract-
domain admissibility predicate the function_shape pivot built.

WHAT THIS HARVESTER DOES

  1. Walk all concepts. For each, attempt to find its Term-tree
     (registered via substrate.define_concept).
  2. For concepts with Term-trees, compute Shape via shape_of_term.
  3. Group donors by Shape.
  4. Provide a Shape-based matcher: given a postulate (with its own
     Shape, computed from its Term-tree if available), return donors
     whose Shape is compatible.

  No regex. No keyword overlap. Pure Shape comparison.

WHAT THIS HARVESTER DOES NOT DO

  · It does NOT walk the substrate's 1150 prose Rule nodes. Those
    don't have Term-trees; their Shape is undefined.
  · It does NOT walk concepts without ConceptResolver entries. The
    substrate currently has ~5 such concepts (bootstrap).
  · It does NOT subsume the regex harvester. Both run in parallel
    for now; the agent's runtime_design pattern is what would
    eventually deprecate the regex one.

THE EXPECTED IMMEDIATE RESULT

Small donor catalog (5 donors, all uniformly Shape{none,0,concrete}).
The chicken-and-egg shifts: the harvester is now Shape-correct, but
the substrate doesn't have enough Term-treeified concepts for the
catalog to be rich. Growing that catalog is the agent's runtime-
design move — author more Term-trees, get more donor shapes.
"""
from __future__ import annotations

from typing import Any


def harvest_shape_donors(substrate) -> list[dict]:
    """Walk concepts with Term-tree definitions; produce Shape-tagged
    donor entries. Each entry has:

      · name           — the concept's name
      · shape          — its Shape (recursion/order_n/abstraction dict)
      · term_idx       — the TermIdx of its definition (provenance)

    Returns the donor list. Empty when no concepts have Term-trees.

    The Shape comparison happens in `find_compatible_donors` below.
    """
    out = []
    # Walk all Concept nodes; check if the substrate has a registered
    # ConceptResolver entry for each.
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        name = str(a.get("name", ""))
        if not name:
            continue
        # The substrate's API doesn't expose ConceptResolver directly
        # from Python; we test by attempting Holds dispatch. If the
        # concept has a Term-tree, Holds returns something other than
        # error. If not, it returns Value::None.
        # A cleaner check: try shape_of_term on the concept's
        # registered TermIdx. The substrate doesn't expose that
        # either, but we can attempt to evaluate Holds with a dummy
        # node and see if the concept resolves.
        try:
            # Try to find a Term-tree for the concept by evaluating
            # a Holds with a dummy Lit value. If the concept has a
            # registered Term-tree, dispatch will succeed (returning
            # something) and we can then ask for its Shape.
            #
            # In practice, since substrate's API doesn't expose the
            # ConceptResolver to Python, this harvester is limited to
            # the BOOTSTRAP set we know about — the 5 concepts from
            # text_concept_bootstrap.py.
            pass
        except Exception:
            continue

    # For now, take the known-bootstrap concepts and harvest those.
    # When the substrate's API exposes ConceptResolver walking, this
    # generalises.
    sources: list[tuple[list[tuple[str, dict]], str]] = []
    try:
        from .text_concept_bootstrap import BOOTSTRAP_CONCEPTS
        sources.append((BOOTSTRAP_CONCEPTS, "text_concept_bootstrap"))
    except ImportError:
        pass
    # Equation-identity promotions registered by
    # `concept_promotion_rules.install_concept_promotion_rules`.
    try:
        from .concept_promotion_rules import PROMOTED_CONCEPTS
        sources.append((PROMOTED_CONCEPTS, "concept_promotion_rules"))
    except ImportError:
        pass
    # "X is the Y of Z" promotions registered by
    # `concept_promotion_rules.install_is_the_of_promotion`. These have
    # an Attr-bearing Term-tree (richer than the equation form's flat
    # Eq(Lit,Lit)) and contribute non-uniform Shape axes — the
    # `shape_of_term` walker classifies Attr-Holds chains differently
    # from flat literal Eq. Sourcing AFTER the flat equation registry
    # keeps Pattern 1's entry on the de-dup list, but since the
    # is-the-of walker SKIPS names already in PROMOTED_CONCEPTS there
    # is no overlap to dedupe in practice.
    try:
        from .concept_promotion_rules import IS_THE_OF_PROMOTED
        sources.append((IS_THE_OF_PROMOTED,
                        "concept_promotion_rules.is_the_of"))
    except ImportError:
        pass
    # Conditional promotions registered by
    # `concept_promotion_rules.install_conditional_promotion`. These
    # introduce the IfThenElse Term variant — a structurally distinct
    # shape from the equation form's flat Eq and the is-the-of form's
    # Eq+Attr+Holds chain. Sourced AFTER is-the-of so a name that
    # somehow registered in both keeps the richer is-the-of Term-tree
    # (the walker skips concepts already in IS_THE_OF_PROMOTED, so
    # there's no overlap in practice).
    try:
        from .concept_promotion_rules import CONDITIONAL_PROMOTED
        sources.append((CONDITIONAL_PROMOTED,
                        "concept_promotion_rules.conditional"))
    except ImportError:
        pass
    # Grounded equation promotions registered by
    # `concept_grounding.install_concept_grounding`. These supersede
    # the flat PROMOTED_CONCEPTS entries for the same name — see the
    # `seen` de-dup below — but the conservative Shape axes are
    # identical, so harvester-level treatment is the same. Sourcing
    # grounded entries FIRST means the grounded Term-tree (rich
    # variant signature) is the one the harvester returns.
    try:
        from .concept_grounding import GROUNDED_CONCEPTS
        # Insert before concept_promotion_rules so the de-dup keeps
        # the grounded copy.
        sources.insert(0, (GROUNDED_CONCEPTS, "concept_grounding"))
    except ImportError:
        pass

    seen: set[str] = set()
    for registry, origin in sources:
        for name, term_json in registry:
            if name in seen:
                continue
            seen.add(name)
            try:
                shape = substrate.shape_of_term(term_json)
                out.append({
                    "name":     name,
                    "shape":    shape,
                    "term_json": term_json,
                    "origin":   origin,
                })
            except Exception:
                continue

    return out


def harvest_shape_donors_compatible(substrate) -> list[dict]:
    """Return donors in the regex-harvester-compatible format, with an
    extra `target_shape` field. The `_resolve_shapes` function in
    order_n_postulates.py merges these alongside regex donors; the
    `differentiate` function uses target_shape when present (Shape
    compatibility) instead of match_patterns (regex).

    Each donor dict has the keys differentiate consumes:
      · name, kind='shape_lifted', domain='shape_aware', source_concept
      · target_shape (the donor's Shape — recursion/order_n/abstraction)
      · match_patterns: []     (regex never fires; target_shape decides)
      · consequence            (descriptive: 'Shape transfer from <donor>')
      · match_keys: []         (no keyword-based downstream matching)
      · name_keys: [donor name]
    """
    raw = harvest_shape_donors(substrate)
    out = []
    for d in raw:
        out.append({
            "name":           f"shape_lifted__{d['name']}",
            "kind":           "shape_lifted",
            "domain":         "shape_aware",
            "source_concept": d["name"],
            "target_shape":   d["shape"],
            "match_patterns": [],
            "consequence":    (
                f"Shape transfer from {d['name']}: the postulate's "
                f"structural Shape is compatible with this donor's "
                f"Shape (recursion={d['shape']['recursion']}, "
                f"order_n={d['shape']['order_n']}, "
                f"abstraction={d['shape']['abstraction']}). The "
                f"implication compositions that work on the donor's "
                f"structure work on the postulate's."
            ),
            "match_keys":     [],
            "name_keys":      [d["name"]],
            "match_mode":     "shape",
        })
    return out


# A world-adapter registry: a frame/postulate the agent has expressed as a
# Term-tree (its structural form) registers it here so the Shape-aware branch of
# `differentiate` can compute its postulate_shape. Mirrors the GROUNDED_CONCEPTS /
# BOOTSTRAP_CONCEPTS registries below — same priority-ordered lookup — but for
# postulates expressed as Term-trees at the boundary rather than baked into a seed
# module. Consulted FIRST so an explicitly-registered structural form wins.
POSTULATE_TERMS: dict[str, dict] = {}


def register_postulate_term(name: str, term_json: dict) -> None:
    """Register a postulate's Term-tree (its structural form) so the Shape-aware
    transfer path in synthesize_gaps can compute its shape. World-adapter I/O."""
    POSTULATE_TERMS[name] = term_json


def lookup_postulate_term(name: str) -> dict | None:
    """Return the Term-tree JSON for a concept that has a registered
    Term-tree definition, or None if it doesn't.

    Sources (in priority order):
      0. `POSTULATE_TERMS` — frames/postulates registered at the boundary
         (register_postulate_term).
      1. `concept_grounding.GROUNDED_CONCEPTS` — the 50 grounded
         equation Term-trees (Eq/Times/Plus/Holds compositions).
         These are richer (structural depth, Holds chains) and
         are preferred when the same name appears in both.
      2. `text_concept_bootstrap.BOOTSTRAP_CONCEPTS` — the 5 hand-
         authored bootstrap Term-trees.

    Returns the first match in priority order, or None if the name has
    no registered Term-tree. Without this, `synthesize_gaps` cannot
    feed the Shape-aware branch of `differentiate` on grounded
    postulates (e.g. Newton_second_law), and the regex/keyword
    fallback dominates — biasing against grounded postulates whose
    names don't share text with their consequences. Per
    Jabberwock's change 3."""
    if name in POSTULATE_TERMS:
        return POSTULATE_TERMS[name]
    try:
        from .concept_grounding import GROUNDED_CONCEPTS
        for nm, term_json in GROUNDED_CONCEPTS:
            if nm == name:
                return term_json
    except ImportError:
        pass
    try:
        from .concept_promotion_rules import IS_THE_OF_PROMOTED
        for nm, term_json in IS_THE_OF_PROMOTED:
            if nm == name:
                return term_json
    except ImportError:
        pass
    try:
        from .concept_promotion_rules import CONDITIONAL_PROMOTED
        for nm, term_json in CONDITIONAL_PROMOTED:
            if nm == name:
                return term_json
    except ImportError:
        pass
    try:
        from .text_concept_bootstrap import BOOTSTRAP_CONCEPTS
        for nm, term_json in BOOTSTRAP_CONCEPTS:
            if nm == name:
                return term_json
    except ImportError:
        pass
    return None


def find_compatible_donors(substrate, postulate_term_json,
                             donors: list[dict]) -> list[dict]:
    """Given a postulate's Term-tree JSON, return donors whose Shape is
    compatible (via the substrate's shapes_compatible predicate).

    Returns the subset of donors that pass.

    If postulate_term_json is None, returns the empty list — Shape
    matching requires both sides to have Term-trees. (This is the
    honest limit: postulates without Term-trees can't be Shape-matched.
    Growing the substrate's Term-treeification is the path forward.)
    """
    if postulate_term_json is None:
        return []
    try:
        target = substrate.shape_of_term(postulate_term_json)
    except Exception:
        return []
    out = []
    for donor in donors:
        try:
            if substrate.shapes_compatible(donor["shape"], target):
                out.append(donor)
        except Exception:
            continue
    return out


def harvest_report_shape(substrate) -> dict:
    """Honest summary of the Shape-lifted harvester's current state.

    The `shape_distribution` field uses the conservative three-axis
    Shape (recursion/order_n/abstraction) and collapses arithmetic
    Term variants — most equation Term-trees classify to
    {none, 0, concrete}. The `structural_distribution` field
    breaks that down by bag-of-variants + max-depth, which DOES
    diversify once concepts are grounded via `Holds` chains
    (concept_grounding.install_concept_grounding).
    """
    donors = harvest_shape_donors(substrate)
    shape_counts: dict = {}
    structural_counts: dict = {}
    for d in donors:
        key = (d["shape"]["recursion"], d["shape"]["order_n"],
               d["shape"]["abstraction"])
        shape_counts[key] = shape_counts.get(key, 0) + 1
        # structural signature — bag-of-variants + max depth
        try:
            from .concept_grounding import structural_signature
            sig = structural_signature(d["term_json"])
            structural_counts[sig] = structural_counts.get(sig, 0) + 1
        except Exception:
            pass
    return {
        "n_donors":               len(donors),
        "shape_distribution":     shape_counts,
        "structural_distribution": structural_counts,
        "n_distinct_shapes":      len(shape_counts),
        "n_distinct_structural":  len(structural_counts),
        "donors":                 donors,
    }
