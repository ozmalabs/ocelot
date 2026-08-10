"""introspect_primitives — walk the agent's vocabulary, lift each
primitive-naming concept into a PrimitiveSpec the mechanical emitter
can compile.

Per user: 'build the introspection pipeline.'

THE PATTERN (extends domains/runtime_design.py)

The agent's runtime_design pattern is:
  · agent specifies a primitive as a PrimitiveSpec graph node
  · emit_primitive_rust mechanically emits the Rust

Until now, agent_specify_primitive was ONE hardcoded function returning
ONE spec (ArgMax — historical, from the speech-science pivot). This
file replaces that single hardcoded specifier with a pipeline that
WALKS THE SUBSTRATE'S CONCEPT VOCABULARY and produces a PrimitiveSpec
for every concept whose category names a primitive operation.

THE CONTRACT THIS FILE HONORS

  · The pipeline makes NO decisions about WHAT primitives the agent
    needs. It just walks the agent's own concepts and translates
    category → semantic_kind via a data table.
  · The data table (CATEGORY_TO_SEMANTIC_KIND) is the world adapter's
    contract: it maps the agent's vocabulary categories (process,
    operation, parser_kind, math_command, etc.) to the
    runtime_design emitter's semantic_kind labels.
  · The pipeline does NOT decide if a primitive is 'new' — that's
    determined by whether the existing emitter has a template (which
    is the substrate's current capability).

NO READING LOGIC. NO INVENTION OF PRIMITIVES. The agent's vocabulary
NAMES THE PRIMITIVES; the pipeline mechanically lifts that naming
into PrimitiveSpec output the existing emitter consumes.
"""
from __future__ import annotations


# Data table: the agent's vocabulary CATEGORIES → runtime_design
# semantic_kind labels. Each entry says: 'a Concept in category X
# is the agent's specification of a primitive of semantic_kind Y'.
#
# The KEYS come from the new vocabulary seeds (language_foundation,
# text_comprehension, scientific_writing, parsing_concepts, latex)
# AND from the existing speech_science / signal_processing / runtime
# Mts that already use the runtime_design pattern.
#
# The VALUES are semantic_kind labels — coarse categories of how the
# primitive evaluates. They become the dispatch key in
# emit_primitive_rust. When a semantic_kind has no template, emission
# reports the gap (the agent's next design move would be to add the
# template, or to author a finer-grained mapping).
CATEGORY_TO_SEMANTIC_KIND: dict[str, str] = {
    # parsing_concepts
    "process":             "transduction_kind",   # tokenization, lex_analysis
    "component":           "transduction_kind",   # parser
    "structure":           "data_kind",            # AST, parse_tree
    "formalism":           "grammar_kind",         # grammar, production_rule
    "grammar_class":       "grammar_kind",         # CFG, regular_grammar
    "parsing_strategy":    "control_flow_kind",    # top_down, bottom_up
    "parser_kind":         "control_flow_kind",    # LL, LR, PEG, recursive_descent
    "grammar_property":    "predicate_kind",       # ambiguity, left_recursion
    "parser_property":     "predicate_kind",       # lookahead
    "parser_capability":   "capability_kind",      # error_recovery
    "lexer_concept":       "transduction_kind",    # tokenizer_rule, whitespace
    "lexical_unit":        "data_kind",            # token, lexeme
    # latex
    "syntax":              "data_kind",            # latex_command, latex_environment
    "mode":                "state_kind",           # math_mode, text_mode
    "math_delimiter":      "predicate_kind",       # inline_math, display_math
    "math_environment":    "data_kind",            # equation, align, gather
    "math_command":        "operation_kind",       # math_operator, math_function
    "math_syntax":         "transduction_kind",    # subscript_superscript, math_escape
    "structural_environment": "data_kind",         # theorem, proof, itemize
    "structure_command":   "data_kind",            # sectioning
    "reference_command":   "transduction_kind",    # cite, ref, label, eqref
    "macro_command":       "transduction_kind",    # newcommand
    "bibliography":        "data_kind",            # bibitem
    # scientific_writing
    "claim_kind":          "data_kind",            # theorem_statement, definitional_sentence
    "structural_marker":   "predicate_kind",       # proof_completion_marker
    "citation_form":       "data_kind",            # citation_year_author, etc.
    "imrad_section":       "data_kind",            # abstract, methods, results
    "stance_marker":       "predicate_kind",       # hedging, certainty
    "cross_reference":     "transduction_kind",    # forward, backward
    "math_form":           "data_kind",            # equation_inline, display, numbered
    # text_comprehension
    "meaning_layer":       "data_kind",            # literal, speaker
    "inference":           "operation_kind",       # presupposition, entailment, implicature
    "reference":           "operation_kind",       # anaphora, deixis, coreference
    "information_structure": "data_kind",          # topic, focus, given/new
    "discourse":           "data_kind",            # coherence
    "rhetorical_relation_kind": "data_kind",       # elaboration, contrast, causation
    "failure_mode":        "predicate_kind",       # unknown_term, ambiguous_referent
    # language_foundation
    "unit":                "data_kind",            # phoneme, morpheme, sentence
    "subfield":            "discipline_kind",      # syntax, semantics, pragmatics
    "pos":                 "data_kind",            # noun, verb, etc.
    "role":                "data_kind",            # subject, object
    "feature":             "data_kind",            # tense, aspect
    "sentence_type":       "data_kind",            # declarative, interrogative
}


def introspect_primitive_specs(substrate, origin_filter=None) -> list:
    """Walk Concepts; create a PrimitiveSpec graph node for each whose
    category is in CATEGORY_TO_SEMANTIC_KIND. Returns a list of dicts
    summarising what was created (node_id, name, semantic_kind, origin,
    purpose, from_concept).

    `origin_filter` (optional): restrict to concepts from these Mts
    (e.g., {'parsing_concepts', 'latex'}) to focus the design pass.
    """
    out = []
    seen_specs = set()
    for c in substrate.nodes("Concept"):
        a = substrate.node(c)["attrs"]
        category = str(a.get("category", ""))
        if category not in CATEGORY_TO_SEMANTIC_KIND:
            continue
        origin = str(a.get("origin", ""))
        if origin_filter is not None and origin not in origin_filter:
            continue
        name = str(a.get("name", ""))
        if not name:
            continue
        # Deduplicate by name — one spec per primitive.
        if name in seen_specs:
            continue
        seen_specs.add(name)

        semantic_kind = CATEGORY_TO_SEMANTIC_KIND[category]
        definition = str(a.get("definition", ""))

        spec = {
            "name":            name,
            "semantic_kind":   semantic_kind,
            "purpose":         definition[:250],
            "from_concept":    name,
            "from_category":   category,
            "from_mt":         origin,
            "origin":          "introspect_primitives",
        }
        nid = substrate.add_node("PrimitiveSpec", spec)
        out.append({
            "node_id":       nid,
            "name":          name,
            "semantic_kind": semantic_kind,
            "from_mt":       origin,
            "from_category": category,
            "purpose":       definition[:120],
        })
    return out


def emission_report(specs: list,
                     known_templates: set[str] | None = None) -> dict:
    """Classify the produced specs by whether the existing emitter has
    a template for their semantic_kind. Returns counts + per-kind lists.

    `known_templates` — set of semantic_kind labels emit_primitive_rust
    handles. The existing emitter knows 'index_of_reduction'; other
    kinds the introspection produces don't yet have templates. The
    gap is reported, not filled."""
    if known_templates is None:
        known_templates = {"index_of_reduction"}
    by_kind: dict[str, list] = {}
    for s in specs:
        by_kind.setdefault(s["semantic_kind"], []).append(s["name"])

    handled = {k: v for k, v in by_kind.items() if k in known_templates}
    needs_template = {k: v for k, v in by_kind.items()
                      if k not in known_templates}
    return {
        "n_total":           len(specs),
        "n_kinds_total":     len(by_kind),
        "n_kinds_handled":   len(handled),
        "n_kinds_needs":     len(needs_template),
        "handled":           handled,
        "needs_template":    needs_template,
    }
