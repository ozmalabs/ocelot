"""Load the compiler-theory seed — names + validity arguments for the
families that `rule_inference` discovered structurally.

The seed at `seeds/compiler_theory.json` defines a small set of
`OptimizationConcept` entries, each carrying:

  * `name`                       — human-meaningful concept name
  * `family_fingerprint`         — the structural skeleton it instantiates
  * `definition`                 — what the transformation does
  * `validity_argument`          — WHY semantics are preserved
  * `preconditions`              — what must hold for the rewriting to be sound
  * `category`                   — `denotational_equivalence` or `algebraic_law`
  * (optional) `examples_by_op`  — opcode → English law (for the agent's reference)

The loader installs each concept as an `OptimizationConcept` graph
node and wires it to its `RuleFamily` by fingerprint via an
`instantiates` edge. After loading, an agent inspecting a
`RewriteRule` reaches its named concept by:

    rule  → member_of    → RuleFamily
    rule  ← instantiates ← OptimizationConcept

`Category` nodes capture the broader soundness principle each
concept appeals to (`denotational_equivalence` vs `algebraic_law`).

This module is a *mechanical translator* from JSON into graph data;
no agent decision logic lives here. The substrate-architecture rule
permits this as a thin loader, like `install_passes_seed`.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# grammar
# ---------------------------------------------------------------------------

def _ensure_theory_grammar(substrate) -> None:
    """Open the productions the theory seed needs:

      OptimizationConcept --instantiates--> RuleFamily
      OptimizationConcept --in_category-->  Category
    """
    substrate.add_production({
        "src": {"type": "OptimizationConcept", "var": "src"},
        "edge_type": "instantiates",
        "tgt": {"type": "RuleFamily", "var": "tgt"},
        "where": None,
        "weight": {"type": "Lit", "value": 1.0},
        "provenance": "compiler_theory:instantiates",
    })
    substrate.add_production({
        "src": {"type": "OptimizationConcept", "var": "src"},
        "edge_type": "in_category",
        "tgt": {"type": "Category", "var": "tgt"},
        "where": None,
        "weight": {"type": "Lit", "value": 1.0},
        "provenance": "compiler_theory:in_category",
    })


# ---------------------------------------------------------------------------
# loader
# ---------------------------------------------------------------------------

def load_compiler_theory_seed(path: str | Path) -> dict:
    """Read the JSON manifest. Returns the dict."""
    p = Path(path)
    with p.open("r") as f:
        manifest = json.load(f)
    if "concepts" not in manifest:
        raise ValueError(f"{p}: missing 'concepts' key — not a compiler-theory seed")
    return manifest


def install_compiler_theory_seed(substrate, path: str | Path) -> dict:
    """Install every concept from the seed at `path` into `substrate`.

    Each concept becomes an `OptimizationConcept` graph node; the
    seed's category metadata becomes `Category` nodes. Concepts are
    wired to their `RuleFamily` (resolved by fingerprint match) and
    to their `Category` node.

    Returns a dict with keys:
      `concepts_installed`  — count of OptimizationConcept nodes
      `categories_installed` — count of Category nodes
      `concepts_wired`      — count of concepts that successfully resolved
                              a RuleFamily (depends on llvm_passes seed
                              being installed FIRST)

    Assumes RuleFamily nodes already exist (i.e. `install_passes_seed`
    has run first). Concepts whose fingerprint doesn't resolve are
    still installed as nodes — they just lack the `instantiates` edge,
    so an agent inspecting them sees an unbound concept it can name
    but not yet link to a discovered family.
    """
    _ensure_theory_grammar(substrate)
    manifest = load_compiler_theory_seed(path)

    # Pre-index RuleFamily nodes by fingerprint for O(1) lookup.
    fp_to_family: dict[str, int] = {}
    for fam in substrate.nodes("RuleFamily"):
        attrs = substrate.node(fam)["attrs"]
        fp = attrs.get("fingerprint")
        if isinstance(fp, str):
            fp_to_family[fp] = fam

    # Install categories first so concepts can link to them.
    cat_nodes: dict[str, int] = {}
    for cat_name, cat_data in manifest.get("categories", {}).items():
        cat_node = substrate.add_node("Category", {
            "name": cat_name,
            "description": cat_data.get("description", ""),
            "soundness_principle": cat_data.get("soundness_principle", ""),
        })
        cat_nodes[cat_name] = cat_node

    concepts_wired = 0
    for concept in manifest["concepts"]:
        attrs: dict[str, Any] = {
            "name": concept["name"],
            "definition": concept.get("definition", ""),
            "validity_argument": concept.get("validity_argument", ""),
            "family_fingerprint": concept.get("family_fingerprint", ""),
            "category_name": concept.get("category", ""),
            "preconditions": concept.get("preconditions", []),
        }
        # Optional examples_by_op map — surface as graph data too.
        if "examples_by_op" in concept:
            attrs["examples_by_op"] = concept["examples_by_op"]

        c_node = substrate.add_node("OptimizationConcept", attrs)

        # Wire to RuleFamily by fingerprint, if one exists.
        fp = concept.get("family_fingerprint", "")
        fam = fp_to_family.get(fp)
        if fam is not None:
            substrate.add_edge(c_node, "instantiates", fam, {})
            concepts_wired += 1

        # Wire to Category if specified.
        cat_name = concept.get("category", "")
        if cat_name in cat_nodes:
            substrate.add_edge(c_node, "in_category", cat_nodes[cat_name], {})

    return {
        "concepts_installed": len(manifest["concepts"]),
        "categories_installed": len(cat_nodes),
        "concepts_wired": concepts_wired,
    }


__all__ = [
    "load_compiler_theory_seed",
    "install_compiler_theory_seed",
]
