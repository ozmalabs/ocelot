"""Bootstrap a handful of text-source concept Term-trees.

USAGE (verified)

  >>> import substrate_rs as srs
  >>> from domains.text_world import open_text_source
  >>> from domains.text_concept_bootstrap import install_text_concept_bootstrap
  >>> s = srs.Substrate()
  >>> install_text_concept_bootstrap(s)
  >>> src = open_text_source(s, 'Hello, world.')
  >>> s.evaluate(srs.Holds(concept='text_is_seekable', node=srs.Lit(src)))
  True



Per user: 'do 1 [concepts get Term-trees] — but only enough to
bootstrap text understanding until we can get the agent to do it.'

This file installs a small set of Concept Term-trees so the
substrate has examples of text-handling concepts AS Term-trees, not
as JSON definitions. The Shape walker can now classify them; the
agent has the pattern; it authors more itself.

WHAT IS BOOTSTRAPPED — 5 concepts

  text_is_seekable(x)       → Attr(Var(x), seekable)
  text_is_ended(x)          → Attr(Var(x), ended)
  text_has_no_lookback(x)   → Attr(Var(x), no_lookback)
  text_at_start(x)          → Eq(Attr(Var(x), position), Lit(0))
  text_at_eof(x)            → Eq(Attr(Var(x), ended), Lit(true))

Variable convention: 'x' is the substrate's Holds-binding name. When
the agent dispatches Holds(concept_name, node), the node is bound to
Var('x') in the concept's evaluation context.

These reason ABOUT a TextSource node (its metadata: seekable,
streaming, no_lookback, position, ended) without touching the text
itself. They're predicates an agent rule can dispatch on:

  IF text_has_no_lookback(s) AND NOT text_at_start(s)
  THEN the substrate cannot seek to revisit content

The pattern: Var + Attr + Eq + Lit, composable. The agent has all
the primitives it needs to author further text-source concepts from
these examples.

WHAT IS NOT BOOTSTRAPPED — INTENTIONAL

  · No string-content primitives (StringLen, StringStartsWith,
    StringContains, StringSplit). The substrate's DSL doesn't yet
    have these; they would be new Rust primitives the agent
    specifies via its runtime_design pattern. NOT my call.

  · No tokenization Term-trees, no sentence-segmentation Term-trees.
    Those depend on string primitives that don't exist yet.

  · No comprehension-side Term-trees (definition recognition,
    theorem identification). Those need string content access too.

The bootstrap stops at TextSource metadata predicates. That's enough
to demonstrate the pattern; the agent picks up from here.
"""
from __future__ import annotations


# Each entry: (concept_name, Term JSON)
# Convention: 'self' is the bound variable referring to the TextSource
# node the concept is being evaluated against.
BOOTSTRAP_CONCEPTS: list[tuple[str, dict]] = [
    # text_is_seekable: read the seekable flag of a TextSource.
    ("text_is_seekable", {
        "type": "Attr",
        "node": {"type": "Var", "name": "x"},
        "key": "seekable",
    }),
    # text_is_ended: read the ended flag.
    ("text_is_ended", {
        "type": "Attr",
        "node": {"type": "Var", "name": "x"},
        "key": "ended",
    }),
    # text_has_no_lookback: read the no_lookback flag.
    ("text_has_no_lookback", {
        "type": "Attr",
        "node": {"type": "Var", "name": "x"},
        "key": "no_lookback",
    }),
    # text_at_start: position equals 0.
    ("text_at_start", {
        "type": "Eq",
        "a": {
            "type": "Attr",
            "node": {"type": "Var", "name": "x"},
            "key": "position",
        },
        "b": {"type": "Lit", "value": 0},
    }),
    # text_at_eof: ended flag is true.
    ("text_at_eof", {
        "type": "Eq",
        "a": {
            "type": "Attr",
            "node": {"type": "Var", "name": "x"},
            "key": "ended",
        },
        "b": {"type": "Lit", "value": True},
    }),
]


def install_text_concept_bootstrap(substrate) -> dict:
    """Install the bootstrap text-source concept Term-trees. Returns a
    summary of what was installed.

    Each bootstrap concept gets BOTH:
      · a substrate.define_concept registration (Term-tree in
        ConceptResolver — what Holds dispatches against)
      · a Concept graph node under the text_bootstrap Mt (what
        synthesize_gaps + harvest_postulates walk)
    """
    # Mint the Mt if absent.
    mt = None
    for n in substrate.nodes("Microtheory"):
        if substrate.node(n)["attrs"].get("name") == "text_bootstrap":
            mt = n; break
    if mt is None:
        mt = substrate.add_node("Microtheory", {
            "name": "text_bootstrap",
            "description": ("Bootstrap text-source concept Term-trees. "
                              "Each concept here has BOTH a Concept "
                              "graph node and a registered Term-tree, "
                              "so it's matchable by synthesize_gaps + "
                              "shape_of_term."),
            "origin": "text_bootstrap",
        })

    from .code_authoring import _install_concept
    installed = []
    for name, term_json in BOOTSTRAP_CONCEPTS:
        try:
            substrate.define_concept(name, term_json)
            cid = _install_concept(substrate, mt, name,
                f"Predicate over a TextSource node: term-tree {term_json}")
            substrate.set_attr(cid, "category", "text_predicate")
            substrate.set_attr(cid, "origin", "text_bootstrap")
            installed.append(name)
        except Exception as e:
            print(f"  WARNING: failed to install {name}: {e}")
    return {
        "installed": installed,
        "total":     len(BOOTSTRAP_CONCEPTS),
        "mt_id":     mt,
    }
