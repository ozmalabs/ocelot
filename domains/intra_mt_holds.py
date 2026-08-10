"""Refactor K: wire concepts WITHIN each Mt to each other.

Per jabberwock's deeper survey (scripts/ask_jabberwock_deeper.out §3):
every one of 151 Mts is a FLAT list of concepts — 0 / 151 Mts have any
intra-Mt Holds connectivity. The largest FLAT Mts:

    engineering              129 concepts, all isolated
    video_coding_theory      128 concepts, all isolated
    computer_architecture    122 concepts, all isolated
    mathematics              117 concepts, all isolated
    databases_and_storage    112 concepts, all isolated
    ... (12 Mts with >=10 concepts, all isolated)

Concept definitions DO reference each other by name in prose — what's
missing is the structural wiring. This module mechanically walks each
concept's definition for word-boundary matches against the names of
its sibling concepts in the same Mt, and:

  1. Registers a Term-tree on the source concept:
       · if the concept ALREADY has a Term-tree (e.g. via
         concept_grounding / concept_promotion_rules), wrap it as
            And(existing, SetT([Holds(ref1, x), Holds(ref2, x), ...]))
         — preserves the equation/identity Term, extends with the
         structural references.
       · if the concept has NO Term-tree yet, register
            SetT([Holds(ref1, x), Holds(ref2, x), ...])
         — meaning "this concept references these other concepts in
         its Mt." Structural definition only.

  2. Adds depends_on edges from source Concept node to each
     intra-Mt referent Concept node — mirrors the
     concept_depends_on pattern so the cortex's
     compositional_reuse measure picks up the new structure (it
     counts depends_on incoming on a Mt's concepts).

WORD-MATCHING STRATEGY

For each concept name, search the definition with:

    \\b<name>\\b                   ← canonical snake_case
    \\b<name with _ → space>\\b    ← human form ("black hole" matches "black_hole")
    \\b<last word of name>\\b      ← last-word fallback (refactor F style)

Skip self-references (concept's name in its own definition). Skip when
the source concept and target concept differ only in case. Strict
under-matching is preferred — false positives are worse than misses.

Names with fewer than 4 characters are skipped for the fallback (too
many false positives — "ar", "io", etc.). Single-word names of length
< 4 also skip the canonical pass (still too noisy).

WHAT THIS MODULE DOES NOT DO

  · It does NOT modify the seed JSONs. Like concept_depends_on, the
    edges and Term-trees are added at runtime after seed install.
  · It does NOT replace the equation Term-tree. The original grounded
    equation (when present) is preserved in the left position of And.
  · It does NOT walk dependencies across Mts. Inter-Mt references
    are concept_depends_on's job.

USAGE

    from domains.intra_mt_holds import install_intra_mt_holds
    report = install_intra_mt_holds(substrate)
    # report['edges_added'], report['terms_registered'],
    # report['terms_extended'], report['per_mt_breakdown']
"""
from __future__ import annotations

import re
from typing import Iterable


# ---------------------------------------------------------------------------
# Helpers — Term-tree walking + JSON form.
# ---------------------------------------------------------------------------

def _holds_refs_in_term(term_json) -> set[str]:
    """Walk a Term-tree (dict-shaped JSON); collect every Holds concept name."""
    out: set[str] = set()
    if isinstance(term_json, dict):
        if term_json.get("type") == "Holds":
            c = term_json.get("concept")
            if isinstance(c, str):
                out.add(c)
        for v in term_json.values():
            if isinstance(v, (dict, list)):
                out |= _holds_refs_in_term(v)
    elif isinstance(term_json, list):
        for x in term_json:
            out |= _holds_refs_in_term(x)
    return out


def _holds_term(concept: str) -> dict:
    """Make a Holds(concept, Var("x")) Term-tree dict."""
    return {
        "type": "Holds",
        "concept": concept,
        "node": {"type": "Var", "name": "x"},
        "node2": None,
    }


def _set_t_term(items: list[dict]) -> dict:
    return {"type": "SetT", "items": items}


def _and_term(items: list[dict]) -> dict:
    return {"type": "And", "items": items}


# ---------------------------------------------------------------------------
# Match a sibling concept name inside a definition string.
# ---------------------------------------------------------------------------

# Words we never want to match as fallback last-words — extremely common
# English words that would false-positive on most definitions.
_STOPWORDS = frozenset({
    "a", "an", "the", "of", "and", "or", "to", "in", "on", "at", "is",
    "are", "be", "for", "by", "with", "as", "from", "this", "that",
    "it", "its", "we", "you", "they", "i", "he", "she", "but", "if",
    "then", "than", "so", "do", "does", "not", "no", "all", "any",
    "some", "one", "two", "three", "set", "type", "kind", "rate",
    "time", "value", "name", "key", "data", "node", "edge", "use",
    "uses", "form", "way", "case", "state", "size", "level", "step",
    "model", "method", "system", "process", "object", "function",
    "result", "input", "output", "code", "field", "list", "map",
    "row", "column", "table", "page", "line", "block", "point",
    "part", "test", "info", "main", "high", "low", "new", "old",
    "good", "bad", "big", "small", "long", "short", "true", "false",
})


def _safe_match_name(definition: str, target_name: str) -> bool:
    """Does `target_name` appear in `definition` as a word boundary,
    in either snake_case or human-form? Strict — single-token short
    words must be at least 4 chars; multi-token names always permitted.
    """
    if not target_name or not definition:
        return False

    parts = target_name.split("_")
    n_tokens = len(parts)

    # Single-token, < 4 chars: skip (too many false positives).
    if n_tokens == 1 and len(target_name) < 4:
        return False

    # Canonical snake_case form.
    pat_snake = r"\b" + re.escape(target_name) + r"\b"
    if re.search(pat_snake, definition, re.IGNORECASE):
        return True

    # Human form (underscore → space) — only meaningful for multi-token.
    if n_tokens >= 2:
        human = " ".join(parts)
        pat_human = r"\b" + re.escape(human) + r"\b"
        if re.search(pat_human, definition, re.IGNORECASE):
            return True

    return False


def _last_word_fallback(definition: str, target_name: str) -> bool:
    """Fallback: match the LAST word of a multi-token name. Strict —
    last word must be >= 5 chars and not a stopword.
    """
    parts = target_name.split("_")
    if len(parts) < 2:
        return False
    last = parts[-1]
    if len(last) < 5:
        return False
    if last.lower() in _STOPWORDS:
        return False
    pat = r"\b" + re.escape(last) + r"\b"
    return bool(re.search(pat, definition, re.IGNORECASE))


# ---------------------------------------------------------------------------
# Find Mts + concept membership in the substrate.
# ---------------------------------------------------------------------------

def _mt_concept_membership(substrate) -> dict[str, dict]:
    """For every Microtheory:
      {mt_name: {
          'mt_nid': int,
          'concepts': {concept_name: (concept_nid, definition_str)},
       }}
    """
    out: dict[str, dict] = {}
    for mt in substrate.nodes("Microtheory"):
        mt_attrs = substrate.node(mt).get("attrs", {})
        mt_name = mt_attrs.get("name", "?")
        concepts: dict[str, tuple[int, str]] = {}
        for c in substrate.neighbours(mt, "has_concept"):
            cattrs = substrate.node(c).get("attrs", {})
            cn = cattrs.get("name", "")
            if not cn:
                continue
            defn = cattrs.get("definition", "") or ""
            concepts[cn] = (c, str(defn))
        if concepts:
            out[mt_name] = {"mt_nid": mt, "concepts": concepts}
    return out


# ---------------------------------------------------------------------------
# The installer.
# ---------------------------------------------------------------------------

def install_intra_mt_holds(
    substrate,
    min_mt_size: int = 10,
    max_refs_per_concept: int = 12,
) -> dict:
    """Wire concepts WITHIN each Mt to each other via intra-Mt Holds
    references + depends_on edges, for every Mt with at least
    `min_mt_size` concepts.

    For each source concept, scan its definition for word-boundary
    matches against the names of its sibling concepts in the same Mt;
    for each match:

      · register / extend a Term-tree on the source (SetT of Holds,
        possibly wrapped via And around an existing Term);
      · add a depends_on edge from source Concept to target Concept.

    Args:
      substrate: the Python wrapper or the raw substrate_rs inner.
      min_mt_size: lower bound on Mt size to wire. Default 10
                   (matches refactor K's stated target).
      max_refs_per_concept: cap on how many refs are wired per source
                            concept. Caps over-eager prose.

    Returns:
      {
        'mts_processed':       int,
        'mts_with_refs':       int,    # Mts that produced at least one ref
        'edges_added':         int,    # depends_on edges added
        'terms_registered':    int,    # NEW Term-trees (no prior)
        'terms_extended':      int,    # And(existing, SetT(...)) registrations
        'sample_per_mt':       dict[mt_name, list[(src, [refs])]],  # top 5 Mts
        'per_mt_breakdown':    dict[mt_name, int],  # Mt -> intra-Mt connections
      }
    """
    inner = _unwrap(substrate)

    # Open the depends_on production once. Idempotent.
    try:
        substrate.add_production({
            "src": {"type": "Concept", "var": "src"},
            "edge_type": "depends_on",
            "tgt": {"type": "Concept", "var": "tgt"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "intra_mt_holds",
        })
    except Exception:
        pass

    # Pull existing Term-trees from the registries (the only available
    # source of pre-registered Term-trees; the substrate's concept
    # store isn't introspectable from Python).
    existing_terms: dict[str, dict] = {}
    try:
        from .concept_promotion_rules import PROMOTED_CONCEPTS
        for nm, t in PROMOTED_CONCEPTS:
            existing_terms[nm] = t
    except Exception:
        pass
    try:
        from .concept_grounding import GROUNDED_CONCEPTS, _record as _grounded_record
    except Exception:
        GROUNDED_CONCEPTS = None
        _grounded_record = None
    if GROUNDED_CONCEPTS is not None:
        for nm, t in GROUNDED_CONCEPTS:
            existing_terms[nm] = t

    mt_map = _mt_concept_membership(substrate)

    mts_processed = 0
    mts_with_refs = 0
    edges_added = 0
    terms_registered = 0
    terms_extended = 0
    sample_per_mt: dict[str, list] = {}
    per_mt_breakdown: dict[str, int] = {}

    for mt_name, info in mt_map.items():
        concepts = info["concepts"]
        if len(concepts) < min_mt_size:
            continue
        mts_processed += 1

        # Build list of (name, len) for stable name-ordering — match
        # longer names first to avoid sub-string capture (e.g. match
        # "neural_network" before "network").
        name_order = sorted(concepts.keys(), key=lambda s: -len(s))

        mt_intra_count = 0
        mt_samples: list[tuple[str, list[str]]] = []

        for src_name, (src_nid, defn) in concepts.items():
            if not defn:
                continue

            # Find sibling refs.
            refs: list[str] = []
            seen: set[str] = set()
            for cand in name_order:
                if cand == src_name:
                    continue
                if cand in seen:
                    continue
                # Strict canonical/human match first.
                hit = _safe_match_name(defn, cand)
                # Fallback: last-word match for multi-token names.
                if not hit:
                    hit = _last_word_fallback(defn, cand)
                if hit:
                    refs.append(cand)
                    seen.add(cand)
                if len(refs) >= max_refs_per_concept:
                    break

            if not refs:
                continue

            # 1. Add depends_on edges (source → each ref).
            for ref in refs:
                tgt_nid, _ = concepts[ref]
                try:
                    existing = substrate.neighbours(src_nid, "depends_on")
                    if tgt_nid in existing:
                        continue
                    substrate.add_edge(src_nid, "depends_on", tgt_nid, {})
                    edges_added += 1
                    mt_intra_count += 1
                except Exception:
                    continue

            # 2. Register / extend Term-tree.
            set_t = _set_t_term([_holds_term(r) for r in refs])
            existing_term = existing_terms.get(src_name)
            if existing_term is not None:
                # If existing term already references all these siblings
                # via Holds, no point extending.
                existing_refs = _holds_refs_in_term(existing_term)
                novel = [r for r in refs if r not in existing_refs]
                if not novel:
                    pass  # nothing new structurally
                else:
                    new_set = _set_t_term([_holds_term(r) for r in novel])
                    extended = _and_term([existing_term, new_set])
                    try:
                        inner.define_concept(src_name, extended)
                        terms_extended += 1
                        existing_terms[src_name] = extended
                        if _grounded_record is not None:
                            try:
                                _grounded_record(src_name, extended)
                            except Exception:
                                pass
                    except Exception:
                        pass
            else:
                try:
                    inner.define_concept(src_name, set_t)
                    terms_registered += 1
                    existing_terms[src_name] = set_t
                    if _grounded_record is not None:
                        try:
                            _grounded_record(src_name, set_t)
                        except Exception:
                            pass
                except Exception:
                    pass

            if len(mt_samples) < 4:
                mt_samples.append((src_name, refs[:6]))

        per_mt_breakdown[mt_name] = mt_intra_count
        if mt_intra_count > 0:
            mts_with_refs += 1
            sample_per_mt[mt_name] = mt_samples

    # Sort sample_per_mt by total connections, top 5.
    top_mts = sorted(per_mt_breakdown.items(),
                     key=lambda kv: -kv[1])[:5]
    top_sample = {m: sample_per_mt.get(m, []) for m, _ in top_mts
                  if m in sample_per_mt}

    return {
        "mts_processed":      mts_processed,
        "mts_with_refs":      mts_with_refs,
        "edges_added":        edges_added,
        "terms_registered":   terms_registered,
        "terms_extended":     terms_extended,
        "sample_per_mt":      top_sample,
        "per_mt_breakdown":   dict(sorted(per_mt_breakdown.items(),
                                          key=lambda kv: -kv[1])),
    }


# ---------------------------------------------------------------------------
# Substrate unwrap — mirrors concept_grounding._unwrap.
# ---------------------------------------------------------------------------

def _unwrap(substrate):
    """Return the inner substrate_rs handle with define_concept."""
    if hasattr(substrate, "define_concept") and hasattr(substrate, "nodes"):
        if hasattr(substrate, "_inner"):
            return substrate._inner
        return substrate
    if hasattr(substrate, "_inner"):
        return substrate._inner
    return substrate


__all__ = ["install_intra_mt_holds"]
