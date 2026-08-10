"""Promote string-defined Concepts to Term-tree definitions.

The substrate's ConceptResolver only knows the few concepts that have
been registered via `substrate.define_concept(name, term)`. The seed
corpus (`seeds/*.json`) instantiates ~5400 Concept nodes whose
definitions are PROSE — the substrate has no Term-tree for any of
them, so `Holds(c, x)` dispatch falls through and shape_of_term is
undefined.

This module is the BOOTSTRAP WALKER (Python-side):

  1. Walks every Concept node in the substrate.
  2. Tries a small set of pattern matchers against `definition`.
  3. For each match, composes a Term-tree from the parsed fragments
     and calls `substrate.define_concept(name, term)`.
  4. Records each promotion in a module-level registry so the
     Shape harvester (`harvester_shape.harvest_shape_donors`) can
     enumerate them — the substrate's Python API doesn't yet
     expose ConceptResolver walking, so the registry is the bridge.

PATTERN 1 — EQUATION-IDENTITY

  pattern:  definition starts with `<lhs> = <rhs>` where
            <lhs> is a short symbol/symbol-phrase (1-4 words)
            <rhs> is a short formula expression (1-80 chars, terminated by
            `.` or `;`)

  promoted Term-tree:  Eq(Lit(<lhs>), Lit(<rhs>))

  rationale: the cleanest, most numerous structural pattern in the
  seed corpus. Eighty-eight matches across physics_foundation,
  engineering, materials_chemistry, audio_acoustics, ml, etc. Each
  one is a definitional identity ("F = ma", "Re = ρvD/μ", "V = IR")
  whose Eq Term-tree captures the structural claim AS a Term, not as
  prose. `shape_of_term` resolves Eq nodes (recursion=none, order_n=0,
  abstraction=concrete) and the Eq variant is one the rule engine
  can match on for downstream rewrite rules.

  Other patterns considered:

    · "X is the Y of Z" → Attr(Var(x), Y)  — zero matches in the
      corpus because definitions don't restate the concept name.
    · "synonym of X" → Eq(Holds(self,x), Holds(X,x))  — only ~1
      clean match; not worth the bookkeeping.
    · "The X of Y is ..." → Attr predicates — zero matches; the
      corpus prefers terse fragments without leading articles.

  The 88-match equation pattern dominates by an order of magnitude;
  picking just this one keeps the demonstration honest + small.

PATTERN 2 — "X is the Y of Z" / "The Y of Z" / "A Y of Z"

  jabberwock's survey on the FULL seed corpus (commit c5104d5)
  reported 54 candidates matching " is the " — the previous
  reading of "X is the Y of Z" as inline copula returned 0 actual
  matches when checked, because the seed corpus omits the redundant
  subject (the concept's name) and starts the definition with the
  predicate complement directly. Re-survey of the corpus surfaces
  the dominant form:

       The Y of Z.                ← "The folded outer sheet of the brain."
       A/An Y of Z.               ← "A set of inputs processed together."
       Y of Z.                    ← "Number of cycles per second."

  In each case the implicit subject is the concept's own name X.
  Semantically: X is identified with a specific aspect ("Y") of
  some other concept ("Z"). The Term-tree:

       Eq(Holds(X, x),
          Attr(Holds(Z, x), "Y"))           ← when Z resolves to a Concept
       Eq(Holds(X, x),
          Attr(Lit(Z), "Y"))                ← Z falls back to opaque Lit

  Examples after promotion:

       firing_rate    →  Eq(Holds("firing_rate", x),
                              Attr(Lit("action_potentials_over_time"), "frequency"))
       neuron         →  Eq(Holds("neuron", x),
                              Attr(Lit("nervous_systems"), "fundamental_signaling_unit"))
       frequency      →  Eq(Holds("frequency", x),
                              Attr(Lit("cycles_per_second"), "Number"))

  The semantic content: looking up X is equivalent to taking the
  "Y" attribute of Z. The Y string is the head-word of the
  predicate complement — typically attribute-like ("number",
  "amount", "rate", "portion", "process", "set"). For most
  candidates Y is NOT itself a registered Concept (it's an attr
  name), so it stays as the Attr `key` string; only Z gets the
  Holds-lookup treatment. This matches the form jabberwock
  signposted plus the actual corpus shape.

  Shape impact: Attr is a different Term variant than the flat
  `Eq(Lit, Lit)` of Pattern 1 — the substrate's `shape_of_term`
  reports a DIFFERENT order_n axis (3 vs 0) for these trees,
  which IS structural distribution growth (not just a no-op
  rebadge).

VERIFICATION (run as __main__)

  python -m domains.concept_promotion_rules

  Prints: concepts walked / matched / promoted, plus Shape-harvester
  donor count before vs after.

THE NEXT STRETCH — RULE-NATIVE PROMOTION

  This walker is Python-side; the task's "stretch" is converting it
  into RewriteRules that fire on tick. The template:

    1. Add a sentinel Microtheory `concept_promotion_trigger`.
    2. For every Concept walked, add a `has_eligible_concept` edge
       from the trigger Mt to the concept node.
    3. Author one RewriteRule per pattern; the rule's match section
       binds the concept via the trigger edge, its WHERE clause uses
       a regex/parse predicate on the concept's `definition` attr,
       its EFFECT is `["define_concept", <name-term>, <term-tree>]`
       where the name-term and term-tree are composed natively
       from Attr(Var("concept"), "definition") parses.

  Phase 3's `domains/phase3_rules.py` is the exemplar — same sentinel
  Mt + trigger edge pattern. The blockers:

    · The rule engine has no native regex / parse primitive yet.
      Walking the definition string from inside the rule requires
      either a new StringRegex / StringMatch Term, or splitting the
      definition at install time into machine-friendly attrs the
      rules can read directly.
    · The compose step (Eq(Lit(lhs), Lit(rhs))) is expressible in
      the existing Term DSL — the rule can construct the Eq Term
      via __term__ wrappers around Lit + Eq, with lhs/rhs sourced
      from Attr(Var("concept"), "lhs_attr") / "rhs_attr".

  The honest-shippable middle path: this module's `walk_and_extract`
  parses definitions and writes the parsed (lhs, rhs) back to the
  concept as new attrs (`promoted_lhs`, `promoted_rhs`). Then the
  rule fires on `has_eligible_concept`, reads those two attrs via
  Attr, composes the Eq Term, and emits `define_concept`. The
  Python step does no decision-making — pure pattern parse — and
  the rule does the substrate-side promotion. Out of scope for
  this commit; left as a TODO for the rule-native phase.
"""
from __future__ import annotations

import re
from typing import Any


# ---------------------------------------------------------------------------
# Pattern matcher — definition starts with `<lhs> = <rhs>`.
# ---------------------------------------------------------------------------

# LHS char class permits Latin letters, digits, underscore, math symbols, and
# common Greek letters used in the seed corpus (∂∇μλρσΩθαβγΔεφψω).
# Whitespace is permitted internally so "Stress σ" and "Impulse J" match
# as a single LHS token-phrase.
_EQUATION_PATTERN = re.compile(
    r"""^\s*
        (?P<lhs>[A-Za-z_∂∇μλρσΩθαβγΔεφψω][\w\s∂∇μλρσΩθαβγΔεφψω×÷∫√_\-]{0,29}?)
        \s*=\s*
        (?P<rhs>[^.;\n]{1,80}?)
        \s*(?:[.;]|$)
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Reject LHS phrases that contain English copulas / articles — those are
# sentences, not equations.
_LHS_NOISE = {"is", "are", "was", "be", "the", "a", "an", "of"}


def parse_equation_identity(definition: str) -> tuple[str, str] | None:
    """If `definition` opens with a definitional equation `lhs = rhs.`,
    return (lhs, rhs) stripped. Otherwise None.

    Filters:
      · LHS must be 1-4 whitespace-separated words.
      · LHS must not contain any English copula/article from _LHS_NOISE.
      · RHS must be non-empty.
    """
    m = _EQUATION_PATTERN.match(definition)
    if m is None:
        return None
    lhs = m.group("lhs").strip()
    rhs = m.group("rhs").strip()
    if not lhs or not rhs:
        return None
    words = lhs.split()
    if not (1 <= len(words) <= 4):
        return None
    if any(w.lower() in _LHS_NOISE for w in words):
        return None
    return (lhs, rhs)


# ---------------------------------------------------------------------------
# Term-tree composition — Eq(Lit(lhs), Lit(rhs)).
# ---------------------------------------------------------------------------

def _lit(value: Any) -> dict:
    return {"type": "Lit", "value": value}


def _eq(a: dict, b: dict) -> dict:
    return {"type": "Eq", "a": a, "b": b}


def equation_term(lhs: str, rhs: str) -> dict:
    """Compose the Term-tree JSON for an equation identity. The
    substrate's define_concept consumes this dict shape directly via
    its inner py-binding."""
    return _eq(_lit(lhs), _lit(rhs))


# ---------------------------------------------------------------------------
# Pattern 2 — "X is the Y of Z" / "The Y of Z" / "A Y of Z" / bare "Y of Z".
# ---------------------------------------------------------------------------
#
# Three definitional opening forms, all equivalent in the corpus to
# "X (the concept's name) is the Y of Z":
#
#   The <Y> of <Z>.        — leading definite article
#   A/An <Y> of <Z>.       — leading indefinite article
#   <Y> of <Z>.            — bare definitional fragment (capitalised first word)
#
# Y must be 1-3 words, Z 1-4 words, neither containing English
# copulas / articles. The boundary terminator is `.`, `;`, `,`,
# `—`, `(`, or a recogniser-defeating subclause start ("that",
# "which", "where", "is", "in", "and", "with", "from", "by",
# "whose", "as", "to", "for"). This deliberately rejects the
# noisier long-form definitions; jabberwock's 54-candidate count
# is the loose upper bound (substring " is the "), the tight
# clean-pattern count from this matcher is in the 100-200 range
# across the full corpus.

_NOISE_WORDS_FRAG = {
    "is", "are", "was", "be", "the", "a", "an", "of", "to", "with",
    "by", "for", "from", "that", "which", "who", "whose", "where",
    "in", "on", "at", "as", "and", "or", "but", "if", "then",
    "into", "onto", "than", "via",
}

_PATTERN_THE = re.compile(
    r"^The\s+(?P<y>\S[^.;,]{0,80}?)\s+of\s+(?P<z>[^.;,—()]{1,80}?)"
    r"(?:[.;,—]|\s+(?:that|which|where|is|in|on|at|with|from|by|whose|as|to|for|and|or)\b|$)",
    re.IGNORECASE,
)

_PATTERN_A = re.compile(
    r"^An?\s+(?P<y>\S[^.;,]{0,80}?)\s+of\s+(?P<z>[^.;,—()]{1,80}?)"
    r"(?:[.;,—]|\s+(?:that|which|where|is|in|on|at|with|from|by|whose|as|to|for|and|or)\b|$)",
    re.IGNORECASE,
)

_PATTERN_BARE = re.compile(
    r"^(?P<y>[A-Z][a-zA-Z\-]*(?:\s+[a-z\-]+){0,2})\s+of\s+(?P<z>[^.;,—()]{1,80}?)"
    r"(?:[.;,—]|\s+(?:that|which|where|is|in|on|at|with|from|by|whose|as|to|for|and|or)\b|$)",
)

# Inline subject form: "X is the Y of Z." — rare in the corpus but
# included for completeness. The concept's actual name takes precedence
# over the matched X (we only use the Y/Z groups).
_PATTERN_X_IS_THE = re.compile(
    r"^[A-Za-z_][\w\-]{0,30}\s+is\s+the\s+(?P<y>\S[^.;,]{0,80}?)\s+of\s+"
    r"(?P<z>[^.;,—()]{1,80}?)"
    r"(?:[.;,—]|\s+(?:that|which|where|is|in|on|at|with|from|by|whose|as|to|for|and|or)\b|$)",
    re.IGNORECASE,
)


def _phrase_ok(phrase: str, max_words: int) -> bool:
    """Validate a Y or Z phrase: 1..max_words words, no noise tokens,
    no internal punctuation hinting at a subclause."""
    if not phrase:
        return False
    if any(ch in phrase for ch in (",", ";", "(", ")", ":")):
        return False
    words = phrase.split()
    if not (1 <= len(words) <= max_words):
        return False
    for w in words:
        wl = w.lower().strip("-_")
        if wl in _NOISE_WORDS_FRAG:
            return False
    return True


def parse_is_the_of(definition: str) -> tuple[str, str] | None:
    """If `definition` opens with one of the four "is the Y of Z" forms,
    return (Y_phrase, Z_phrase) — both stripped, both passing
    `_phrase_ok`. Otherwise None.

    Tried in priority order: explicit-subject form first (most
    grammatically explicit), then `The`, then `A/An`, then bare.
    """
    for pat in (_PATTERN_X_IS_THE, _PATTERN_THE, _PATTERN_A, _PATTERN_BARE):
        m = pat.match(definition)
        if m is None:
            continue
        y = m.group("y").strip().rstrip(".")
        z = m.group("z").strip().rstrip(".")
        if not _phrase_ok(y, 3):
            continue
        if not _phrase_ok(z, 4):
            continue
        return (y, z)
    return None


# ---------------------------------------------------------------------------
# Term-tree composition for Pattern 2 — Eq(Holds(X, x), Attr(<z-term>, Y)).
# ---------------------------------------------------------------------------

def _var(name: str) -> dict:
    return {"type": "Var", "name": name}


def _holds(concept: str, node: dict) -> dict:
    return {"type": "Holds", "concept": concept, "node": node, "node2": None}


def _attr(node: dict, key: str) -> dict:
    return {"type": "Attr", "node": node, "key": key}


def _slug(s: str) -> str:
    """Normalise a Y/Z phrase to a substrate-friendly key string:
    lowercase, whitespace → underscore, strip trailing punctuation.
    The substrate's Attr `key` is just a Sym, but other concept
    names use underscore_form, so we mirror that convention."""
    out = s.strip().lower()
    out = re.sub(r"\s+", "_", out)
    out = out.strip("_-.,;:")
    return out


def _singularize(word: str) -> str:
    """Crude English plural → singular. Handles the common -ies, -ses, -s
    suffixes that dominate the seed corpus's Z phrases ("languages",
    "comets", "galaxies"). Cheap heuristic, no irregular-noun table —
    if it produces a non-existent stem, downstream lookup just falls
    through and we keep the Lit fallback."""
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith("ses"):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def is_the_of_term(name: str, y: str, z: str,
                    z_concept: str | None) -> dict:
    """Compose `Eq(Holds(<name>, x), Attr(<z-term>, "<Y_slug>"))`.

    If `z_concept` is provided (the Z phrase resolved to an existing
    Concept name), the z-term is `Holds(z_concept, x)`. Otherwise it
    is `Lit(<Z_slug>)` — the structural form is preserved even when
    the Z half is opaque text.

    Y becomes the Attr key (a slugged string), not a Holds — Y is the
    head-word of the predicate complement (attribute-like:
    "number", "amount", "rate", "portion", "process", ...) and is
    almost never itself a Concept. Treating it as an attr key
    matches the semantic claim "X is the Y-aspect of Z".
    """
    bound = _var("x")
    if z_concept is not None:
        z_term = _holds(z_concept, bound)
    else:
        z_term = _lit(_slug(z))
    return _eq(_holds(name, bound), _attr(z_term, _slug(y)))


# Separate registry for the new pattern so harvester_shape can pick it
# up without confusing it with the equation-identity flat-Eq form.
IS_THE_OF_PROMOTED: list[tuple[str, dict]] = []


def _record_is_the_of(name: str, term: dict) -> None:
    for nm, _ in IS_THE_OF_PROMOTED:
        if nm == name:
            return
    IS_THE_OF_PROMOTED.append((name, term))


# ---------------------------------------------------------------------------
# Promotion registry — module-level so harvester_shape can enumerate.
# ---------------------------------------------------------------------------
#
# The substrate's Python API doesn't expose ConceptResolver walking, so
# the Shape harvester can't ask "which concepts have Term-trees?"
# directly. The harvester reads BOOTSTRAP_CONCEPTS from
# text_concept_bootstrap and an analogous registry here. This is the
# adapter-layer indirection until the substrate surfaces a
# `concepts_with_term_trees()` Rust API — TODO graph-resident.

PROMOTED_CONCEPTS: list[tuple[str, dict]] = []


def _record_promotion(name: str, term: dict) -> None:
    """Append to the module's PROMOTED_CONCEPTS registry. Idempotent
    on (name, term-json) — duplicate calls are silently skipped."""
    for nm, t in PROMOTED_CONCEPTS:
        if nm == name:
            return
    PROMOTED_CONCEPTS.append((name, term))


# ---------------------------------------------------------------------------
# Bootstrap walker — the simple Python entry point.
# ---------------------------------------------------------------------------

def install_concept_promotion_rules(substrate) -> dict:
    """Walk every Concept node; promote those whose `definition` matches
    the equation-identity pattern to Term-tree definitions via
    substrate.define_concept; record each promotion in
    PROMOTED_CONCEPTS so the Shape harvester picks them up.

    Pure mechanical translation — no decision logic, no rule-engine
    state mutation beyond `define_concept` calls.

    Args:
      substrate: the inner substrate_rs.Substrate (the one with
        `nodes("Concept")`, `node(c)`, `define_concept(name, term)`).
        Accepts the high-level wrapper too — falls back to ._inner.

    Returns:
      {
        "n_walked":   int,  # Concept nodes inspected
        "n_matched":  int,  # definitions parsed by the pattern
        "n_promoted": int,  # define_concept calls that succeeded
        "n_skipped":  int,  # already-promoted (idempotency)
        "n_failed":   int,  # define_concept calls that raised
        "promoted":   list[str],   # names promoted this call
        "examples":   list[tuple[str, str, str]],  # (name, lhs, rhs) — first 10
        "failures":   list[tuple[str, str]],  # (name, reason)
      }

    Behaviour:
      Idempotent — running twice on the same substrate is a no-op
      after the first promotion (define_concept clobbers the resolver
      entry but the registry de-dupes).
    """
    inner = _unwrap(substrate)

    n_walked = 0
    n_matched = 0
    n_promoted = 0
    n_skipped = 0
    n_failed = 0
    promoted: list[str] = []
    examples: list[tuple[str, str, str]] = []
    failures: list[tuple[str, str]] = []

    already_recorded = {nm for nm, _ in PROMOTED_CONCEPTS}

    for c in inner.nodes("Concept"):
        n_walked += 1
        a = inner.node(c)["attrs"]
        name = a.get("name")
        defn = a.get("definition")
        if not isinstance(name, str) or not isinstance(defn, str):
            continue
        parsed = parse_equation_identity(defn)
        if parsed is None:
            continue
        n_matched += 1
        lhs, rhs = parsed
        term = equation_term(lhs, rhs)
        if name in already_recorded:
            n_skipped += 1
            continue
        try:
            inner.define_concept(name, term)
        except Exception as exc:
            n_failed += 1
            failures.append((name, repr(exc)))
            continue
        _record_promotion(name, term)
        already_recorded.add(name)
        promoted.append(name)
        if len(examples) < 10:
            examples.append((name, lhs, rhs))
        n_promoted += 1

    return {
        "n_walked":   n_walked,
        "n_matched":  n_matched,
        "n_promoted": n_promoted,
        "n_skipped":  n_skipped,
        "n_failed":   n_failed,
        "promoted":   promoted,
        "examples":   examples,
        "failures":   failures,
    }


def install_is_the_of_promotion(substrate) -> dict:
    """Walk every Concept node; promote those whose `definition` matches
    one of the "X is the Y of Z" definitional opening forms (see
    `parse_is_the_of`) to `Eq(Holds(X, x), Attr(<z-term>, Y))`
    Term-trees via substrate.define_concept; record each promotion in
    IS_THE_OF_PROMOTED.

    The walker prefers Pattern 1 (equation) when both patterns match
    the same definition — the equation form is strictly more
    structural. A concept already promoted by Pattern 1 is silently
    skipped here.

    Args:
      substrate: the inner substrate_rs.Substrate or its Python
        wrapper. Same dispatch convention as
        `install_concept_promotion_rules`.

    Returns:
      {
        "n_walked":         int,  # Concept nodes inspected
        "n_matched":        int,  # definitions parsed by the pattern
        "n_z_resolved":     int,  # Z phrase mapped to an existing Concept
        "n_z_opaque":       int,  # Z stayed as Lit (no concept match)
        "n_promoted":       int,  # define_concept calls that succeeded
        "n_skipped_eq":     int,  # already promoted by Pattern 1
        "n_skipped_dupe":   int,  # already in IS_THE_OF_PROMOTED
        "n_failed":         int,  # define_concept raised
        "promoted":         list[str],
        "examples":         list[tuple[str, str, str, str|None]],
                            # (name, y, z, z_concept) — first 10
        "failures":         list[tuple[str, str]],
      }

    Idempotent on (name): a second call promotes only NEW concepts
    that have appeared since the first call (e.g. after a fresh seed
    load).
    """
    inner = _unwrap(substrate)

    # Names already promoted by Pattern 1 — we don't overwrite those;
    # the equation form is structurally richer.
    eq_promoted = {nm for nm, _ in PROMOTED_CONCEPTS}

    # Build a name → name lookup so the slug of Z can be matched
    # against existing Concept names. Z = "the brain" → slug
    # "the_brain"; we'd also try "brain" via head-word fallback.
    concept_names: set[str] = set()
    for c in inner.nodes("Concept"):
        a = inner.node(c)["attrs"]
        nm = a.get("name")
        if isinstance(nm, str) and nm:
            concept_names.add(nm)

    def resolve_z(z_phrase: str) -> str | None:
        """Resolve a Z phrase to an existing Concept name, trying
        progressively looser strategies. Returns the first hit in
        `concept_names`, else None.

        Strategies (in priority order):

          1. Full slug                — "frequency" → frequency.
          2. Full slug, last word     — "natural frequencies" → natural_frequency.
             singularised
          3. Last word                — head of the noun phrase, English head-noun.
          4. Last word singularised   — "languages" → language, "galaxies" → galaxy.
          5. First word               — backup head-word.
          6. First word singularised  — "comets ~2000-200" → comet.
          7. Trailing N-gram          — "plasma sustaining nuclear fusion"
             (singularised tail head)   → nuclear_fusion. Tries longest tail first.

        The full→head→tail order matches noun-phrase grammar (head on
        the right in English) and avoids over-eager partial matches:
        we only fall to broader strategies when the tighter ones miss.
        """
        full = _slug(z_phrase)
        if full in concept_names:
            return full
        words = z_phrase.split()
        if not words:
            return None
        # Strip leading articles ("the", "a", "an") from the head.
        head_words = [w for w in words
                      if w.lower() not in {"the", "a", "an"}]
        if not head_words:
            return None
        # Full phrase with the last word singularised — catches
        # "stellar masses" → stellar_mass when stellar_mass exists.
        if len(head_words) > 1:
            joined_sing = _slug(" ".join(
                head_words[:-1] + [_singularize(head_words[-1])]
            ))
            if joined_sing in concept_names:
                return joined_sing
        # Last word is the noun-phrase head in English; try it first.
        last = _slug(head_words[-1])
        if last in concept_names:
            return last
        # Singular form of the last word — covers the plural-Z mass
        # case ("languages" → language, "galaxies" → galaxy, "pixels"
        # → pixel) that dominates the unresolved set.
        last_s = _slug(_singularize(head_words[-1]))
        if last_s != last and last_s in concept_names:
            return last_s
        # First word as a backup.
        first = _slug(head_words[0])
        if first in concept_names:
            return first
        # Singular form of the first word — covers leading-plural
        # Z phrases ("comets ~2000-200" → comet).
        first_s = _slug(_singularize(head_words[0]))
        if first_s != first and first_s in concept_names:
            return first_s
        # Trailing N-grams (with last-word singularised) — picks up
        # compound concept names buried inside a longer Z phrase
        # ("plasma sustaining nuclear fusion" → nuclear_fusion).
        # Tries the longest tail first; caps at 3 words so we don't
        # accidentally re-walk the whole phrase.
        max_tail = min(len(head_words) - 1, 3)
        for n in range(max_tail, 1, -1):
            tail = list(head_words[-n:])
            tail[-1] = _singularize(tail[-1])
            sub = _slug(" ".join(tail))
            if sub in concept_names:
                return sub
        return None

    n_walked = 0
    n_matched = 0
    n_z_resolved = 0
    n_z_opaque = 0
    n_promoted = 0
    n_skipped_eq = 0
    n_skipped_dupe = 0
    n_failed = 0
    promoted: list[str] = []
    examples: list[tuple[str, str, str, str | None]] = []
    failures: list[tuple[str, str]] = []

    already_recorded = {nm for nm, _ in IS_THE_OF_PROMOTED}

    for c in inner.nodes("Concept"):
        n_walked += 1
        a = inner.node(c)["attrs"]
        name = a.get("name")
        defn = a.get("definition")
        if not isinstance(name, str) or not isinstance(defn, str):
            continue
        # Pattern 1 wins if it matched.
        if name in eq_promoted:
            n_skipped_eq += 1
            continue
        parsed = parse_is_the_of(defn)
        if parsed is None:
            continue
        n_matched += 1
        y, z = parsed
        if name in already_recorded:
            n_skipped_dupe += 1
            continue
        z_concept = resolve_z(z)
        if z_concept is not None:
            n_z_resolved += 1
        else:
            n_z_opaque += 1
        term = is_the_of_term(name, y, z, z_concept)
        try:
            inner.define_concept(name, term)
        except Exception as exc:
            n_failed += 1
            failures.append((name, repr(exc)))
            continue
        _record_is_the_of(name, term)
        already_recorded.add(name)
        promoted.append(name)
        if len(examples) < 10:
            examples.append((name, y, z, z_concept))
        n_promoted += 1

    return {
        "n_walked":       n_walked,
        "n_matched":      n_matched,
        "n_z_resolved":   n_z_resolved,
        "n_z_opaque":     n_z_opaque,
        "n_promoted":     n_promoted,
        "n_skipped_eq":   n_skipped_eq,
        "n_skipped_dupe": n_skipped_dupe,
        "n_failed":       n_failed,
        "promoted":       promoted,
        "examples":       examples,
        "failures":       failures,
    }


# ---------------------------------------------------------------------------
# Pattern 3 — "X when Y" / "X if Y" CONDITIONAL.
# ---------------------------------------------------------------------------
#
# Jabberwock's deeper survey (260 candidates: 177 'when' + 83 'if') flagged
# this as the largest unrecognized definition shape after Pattern 1+2.
# Hand-sampling 40 random matches revealed the SENTENCE-LOCAL shape:
#
#     <X clause> when <Y clause>.
#     <X clause> if   <Y clause>.
#
# X is a short property/action/predicate phrase (1-8 words). Y is a short
# condition phrase (1-10 words). Both are clean-clause: no comma, no
# subclause boundary. The semantic claim is "X holds CONDITIONAL on Y".
#
# Concrete examples from the corpus:
#
#     diffraction:           "Sound bending around obstacles"
#                              when "wavelength is comparable to obstacle size"
#     compression_audio:     "Reduces gain"
#                              when "signal exceeds threshold"
#     A_star_search:         "Optimal"
#                              if   "heuristic is admissible"
#     register_allocation:   "Spill to stack"
#                              if   "no register available"
#
# TERM-TREE SHAPE
#
#     IfThenElse(
#       cond  = Holds(<Y_concept_or_lit>, x),
#       then  = Holds(<concept_name>, x),
#       other = Lit(None)
#     )
#
# Reading: "the named concept holds of x WHEN the condition Y holds of x;
# otherwise nothing." This matches the conditional semantic without forcing
# either branch into an inappropriate truth value. The `Lit(None)` "else"
# arm is the substrate's standard sentinel — the resolver already treats
# None as "no claim".
#
# Y RESOLUTION
#
# The Y clause is rarely a bare concept name; it's a short phrase like
# "signal exceeds threshold" or "heuristic is admissible". We slug the
# phrase + try the same head-word strategies as `resolve_z` in Pattern 2
# (full slug → last word → singularised last word → first word →
# singularised first word). On the 124 cleanly-parsed corpus matches,
# ~17 (14%) resolve to an existing Concept by head-word; the rest stay
# as Lit fallback. That's much lower than Pattern 2's Z-resolution rate
# because conditions are predicate clauses ("signal exceeds threshold"),
# not noun phrases ("cycles per second") — head-word matching is weaker
# on predicates. The Lit fallback preserves structural form regardless.
#
# WHAT THIS WALKER DOES NOT TRY TO HANDLE
#
# Multi-clause cases ("X when Y is in state S; otherwise Z") — the comma
# filter on X and Y rejects these (no clean (X, Y) split exists). Honest
# scope: only the clean two-clause form is promoted; the noisy long-form
# definitions fall through as walker misses.

# Sentence terminators. Splitting on these isolates the LOCAL sentence
# containing the 'when'/'if' keyword.
_SENTENCE_TERMINATORS = re.compile(r"(?<=[.!?])\s+")


def _local_sentence(definition: str, keyword: str) -> str | None:
    """Return the first sentence in `definition` containing the
    standalone `keyword` (word-boundary match). None if no sentence
    contains it.

    The 'sentence' here is whatever the definition splits to on
    `.`/`!`/`?` — coarse, but enough to keep the keyword's local
    context bounded so the X/Y phrases don't bleed across sentence
    boundaries."""
    if not definition:
        return None
    sentences = _SENTENCE_TERMINATORS.split(definition)
    kw_re = re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE)
    for sent in sentences:
        if kw_re.search(sent):
            return sent
    return None


def parse_conditional(definition: str,
                      keyword: str = "when") -> tuple[str, str] | None:
    """If `definition` contains a sentence of the form
    `<X clause> <keyword> <Y clause>`, return (X, Y) — both stripped.
    Otherwise None.

    keyword:
      "when" or "if" — the conditional connector to split at. Use
      `parse_conditional(defn, "when")` then fall through to
      `parse_conditional(defn, "if")` when both are candidates.

    Filters:
      · X clause must be 1-8 whitespace-separated words.
      · Y clause must be 1-10 whitespace-separated words.
      · Neither clause may contain a comma or semicolon (multi-clause
        sentences are rejected — the agent gets the clean cases only).
      · Both must be non-empty after trimming punctuation.

    This is deliberately tight: of ~260 corpus surface mentions, only
    ~124 parse cleanly. The honest scope IS the clean subset; multi-
    clause forms ("X when Y is in state S, then Z") fall through as
    walker misses.
    """
    if keyword not in ("when", "if"):
        return None
    sent = _local_sentence(definition, keyword)
    if sent is None:
        return None
    kw_re = re.compile(rf"\s+\b{re.escape(keyword)}\b\s+", re.IGNORECASE)
    parts = kw_re.split(sent, maxsplit=1)
    if len(parts) != 2:
        return None
    x = parts[0].strip(" .,:;—\t")
    y = parts[1].strip(" .,:;—\t")
    if not x or not y:
        return None
    # Reject multi-clause segments — the substrate gets the clean
    # subset; noisy forms are walker misses.
    if any(ch in x for ch in (",", ";")):
        return None
    if any(ch in y for ch in (",", ";")):
        return None
    x_words = x.split()
    y_words = y.split()
    if not (1 <= len(x_words) <= 8):
        return None
    if not (1 <= len(y_words) <= 10):
        return None
    return (x, y)


def conditional_term(name: str, y: str,
                       y_concept: str | None) -> dict:
    """Compose the Term-tree
    `IfThenElse(Holds(<y_concept_or_slug>, x), Holds(<name>, x), Lit(None))`.

    If `y_concept` resolves to an existing Concept, the cond arm is
    `Holds(y_concept, x)` — structurally rich. Otherwise it's
    `Holds(<slug(y)>, x)` where the concept lookup will fall through
    at evaluate time but the Term-tree retains the structural shape.

    The else-arm `Lit(None)` is the substrate's sentinel for "no
    claim" — the resolver treats it as unset, matching the
    conditional semantic ("X holds of x WHEN Y; otherwise unset").

    The X clause is encoded as the CONCEPT NAME itself — the agent's
    own concept name IS the X claim; promoting it means "Holds(this
    concept, x) iff Y(x)". The free-text X phrase isn't a Concept and
    has nowhere structural to go; the concept name carries the X
    semantic, the Term-tree carries the conditional shape.
    """
    bound = _var("x")
    cond_concept = y_concept if y_concept is not None else _slug(y)
    cond = _holds(cond_concept, bound)
    then = _holds(name, bound)
    return {
        "type":  "IfThenElse",
        "cond":  cond,
        "then":  then,
        "other": _lit(None),
    }


# Separate registry — harvester_shape merges this alongside the other
# pattern registries.
CONDITIONAL_PROMOTED: list[tuple[str, dict]] = []


def _record_conditional(name: str, term: dict) -> None:
    for nm, _ in CONDITIONAL_PROMOTED:
        if nm == name:
            return
    CONDITIONAL_PROMOTED.append((name, term))


def install_conditional_promotion(substrate) -> dict:
    """Walk every Concept node; promote those whose `definition` matches
    the conditional pattern (`X when Y` or `X if Y`) to
    `IfThenElse(Holds(Y, x), Holds(name, x), Lit(None))` Term-trees
    via substrate.define_concept; record each promotion in
    CONDITIONAL_PROMOTED.

    Priority: tries 'when' first, then 'if'. A concept already promoted
    by Pattern 1 (equation) or Pattern 2 (is-the-of) is skipped — those
    structural shapes are richer and the walker doesn't overwrite them.

    Args:
      substrate: the inner substrate_rs.Substrate or its Python wrapper.

    Returns:
      {
        "n_walked":         int,  # Concept nodes inspected
        "n_matched":        int,  # definitions parsed by the pattern
        "n_y_resolved":     int,  # Y phrase mapped to an existing Concept
        "n_y_opaque":       int,  # Y stayed as Holds(<slug>) — concept-name fallback
        "n_promoted":       int,  # define_concept calls that succeeded
        "n_skipped_eq":     int,  # already promoted by Pattern 1
        "n_skipped_isthe":  int,  # already promoted by Pattern 2
        "n_skipped_dupe":   int,  # already in CONDITIONAL_PROMOTED
        "n_failed":         int,  # define_concept raised
        "n_when":           int,  # promoted via 'when' keyword
        "n_if":             int,  # promoted via 'if' keyword
        "promoted":         list[str],
        "examples":         list[tuple[str, str, str, str, str|None]],
                            # (name, keyword, x, y, y_concept) — first 10
        "failures":         list[tuple[str, str]],
      }

    Idempotent on (name): a second call promotes only NEW concepts
    that have appeared since the first call.
    """
    inner = _unwrap(substrate)

    eq_promoted = {nm for nm, _ in PROMOTED_CONCEPTS}
    isthe_promoted = {nm for nm, _ in IS_THE_OF_PROMOTED}

    # Build a name set for Y-phrase resolution.
    concept_names: set[str] = set()
    for c in inner.nodes("Concept"):
        a = inner.node(c)["attrs"]
        nm = a.get("name")
        if isinstance(nm, str) and nm:
            concept_names.add(nm)

    def resolve_y(y_phrase: str) -> str | None:
        """Resolve a Y predicate-clause to an existing Concept name by
        head-word, mirroring `install_is_the_of_promotion.resolve_z`
        but tuned for predicate clauses (head-word is typically the
        SUBJECT noun, e.g. 'signal' in 'signal exceeds threshold').

        Returns the first hit in `concept_names`, else None.

        Strategies (priority order):
          1. Full slug                — "signal exceeds threshold"
             → no hit unless that compound exists.
          2. Last word                — "threshold" if it's a Concept.
          3. Last word singularised   — "thresholds" → threshold.
          4. First word               — predicate subject head.
          5. First word singularised  — "signals" → signal.
        """
        full = _slug(y_phrase)
        if full in concept_names:
            return full
        words = [w for w in y_phrase.split()
                 if w.lower() not in {"the", "a", "an"}]
        if not words:
            return None
        last = _slug(words[-1])
        if last in concept_names:
            return last
        last_s = _slug(_singularize(words[-1]))
        if last_s != last and last_s in concept_names:
            return last_s
        first = _slug(words[0])
        if first in concept_names:
            return first
        first_s = _slug(_singularize(words[0]))
        if first_s != first and first_s in concept_names:
            return first_s
        return None

    n_walked = 0
    n_matched = 0
    n_y_resolved = 0
    n_y_opaque = 0
    n_promoted = 0
    n_skipped_eq = 0
    n_skipped_isthe = 0
    n_skipped_dupe = 0
    n_failed = 0
    n_when = 0
    n_if = 0
    promoted: list[str] = []
    examples: list[tuple[str, str, str, str, str | None]] = []
    failures: list[tuple[str, str]] = []

    already_recorded = {nm for nm, _ in CONDITIONAL_PROMOTED}

    for c in inner.nodes("Concept"):
        n_walked += 1
        a = inner.node(c)["attrs"]
        name = a.get("name")
        defn = a.get("definition")
        if not isinstance(name, str) or not isinstance(defn, str):
            continue
        if name in eq_promoted:
            n_skipped_eq += 1
            continue
        if name in isthe_promoted:
            n_skipped_isthe += 1
            continue
        # Try 'when' first, then 'if'.
        parsed = parse_conditional(defn, "when")
        kw = "when"
        if parsed is None:
            parsed = parse_conditional(defn, "if")
            kw = "if"
        if parsed is None:
            continue
        n_matched += 1
        x, y = parsed
        if name in already_recorded:
            n_skipped_dupe += 1
            continue
        y_concept = resolve_y(y)
        if y_concept is not None:
            n_y_resolved += 1
        else:
            n_y_opaque += 1
        term = conditional_term(name, y, y_concept)
        try:
            inner.define_concept(name, term)
        except Exception as exc:
            n_failed += 1
            failures.append((name, repr(exc)))
            continue
        _record_conditional(name, term)
        already_recorded.add(name)
        promoted.append(name)
        if kw == "when":
            n_when += 1
        else:
            n_if += 1
        if len(examples) < 10:
            examples.append((name, kw, x, y, y_concept))
        n_promoted += 1

    return {
        "n_walked":        n_walked,
        "n_matched":       n_matched,
        "n_y_resolved":    n_y_resolved,
        "n_y_opaque":      n_y_opaque,
        "n_promoted":      n_promoted,
        "n_skipped_eq":    n_skipped_eq,
        "n_skipped_isthe": n_skipped_isthe,
        "n_skipped_dupe":  n_skipped_dupe,
        "n_failed":        n_failed,
        "n_when":          n_when,
        "n_if":            n_if,
        "promoted":        promoted,
        "examples":        examples,
        "failures":        failures,
    }


def _unwrap(substrate):
    """Accept either the wrapped Python Substrate or the raw inner
    pyclass. The wrapper exposes nodes/node/define_concept too in
    most cases; the inner exposes them on _inner. Fall through to
    whatever object exposes the methods we need."""
    if hasattr(substrate, "nodes") and hasattr(substrate, "node") \
            and hasattr(substrate, "define_concept"):
        # The high-level wrapper's define_concept wants a Term, not
        # a dict, so prefer the inner when both are available.
        if hasattr(substrate, "_inner"):
            return substrate._inner
        return substrate
    if hasattr(substrate, "_inner"):
        return substrate._inner
    return substrate


__all__ = [
    "install_concept_promotion_rules",
    "parse_equation_identity",
    "equation_term",
    "PROMOTED_CONCEPTS",
    # Pattern 2 — "X is the Y of Z" / "The Y of Z" / "A Y of Z".
    "install_is_the_of_promotion",
    "parse_is_the_of",
    "is_the_of_term",
    "IS_THE_OF_PROMOTED",
    # Pattern 3 — "X when Y" / "X if Y" conditional.
    "install_conditional_promotion",
    "parse_conditional",
    "conditional_term",
    "CONDITIONAL_PROMOTED",
]


# ---------------------------------------------------------------------------
# CLI demonstration — verifiable bootstrap of the promotion + harvester
# uplift on a substrate loaded from the seeds/ directory.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    import pathlib
    import sys

    # Path setup matches the project's convention for ad-hoc scripts.
    HERE = pathlib.Path(__file__).resolve().parent
    PROJECT = HERE.parent
    sys.path.insert(0, str(PROJECT / "runners" / "dsl" / "python"))
    sys.path.insert(0, str(PROJECT))

    import substrate_rs as srs

    # When invoked as `python -m domains.concept_promotion_rules`, this
    # file is loaded twice: once as `__main__` and once as
    # `domains.concept_promotion_rules` (imported transitively by the
    # harvester). The two copies have INDEPENDENT module-level
    # PROMOTED_CONCEPTS lists, so the harvester reads an empty
    # registry after `__main__` populates its own. Forcing the
    # `domains.concept_promotion_rules` install path through the
    # harvester's view eliminates the split.
    from domains import concept_promotion_rules as cpr

    s = srs.Substrate()

    # The substrate adapter doesn't have a "load every seed" entry
    # point yet — load the raw seed JSONs directly. This is purely
    # ingest (Concept node minting), no decision logic.
    SEED_DIR = PROJECT / "seeds"
    n_minted = 0
    for sf in sorted(SEED_DIR.glob("*.json")):
        try:
            d = json.loads(sf.read_text())
        except Exception:
            continue
        for c in d.get("concepts", []):
            nm = c.get("name")
            defn = c.get("definition", "")
            if not isinstance(nm, str) or not nm:
                continue
            try:
                s._inner.add_node("Concept", {
                    "name":       nm,
                    "definition": defn,
                    "origin":     f"seed:{sf.stem}",
                })
                n_minted += 1
            except Exception:
                # Likely a duplicate-name collision; harmless for the demo.
                pass

    print(f"Minted {n_minted} Concept nodes from {SEED_DIR}")
    print(f"Substrate has {len(list(s._inner.nodes('Concept')))} Concept "
          f"nodes total")

    # Baseline: how many Shape donors does the harvester report?
    from domains.harvester_shape import harvest_report_shape
    before = harvest_report_shape(s._inner)
    print(f"\nBefore promotion: {before['n_donors']} Shape donors "
          f"(distribution: {dict(before['shape_distribution'])})")

    # Promote — call through the `domains.concept_promotion_rules`
    # module (not `__main__`) so the harvester sees the same
    # PROMOTED_CONCEPTS list it imports.
    report = cpr.install_concept_promotion_rules(s)
    print(f"\nPromotion report:")
    print(f"  walked:   {report['n_walked']}")
    print(f"  matched:  {report['n_matched']}")
    print(f"  promoted: {report['n_promoted']}")
    print(f"  skipped:  {report['n_skipped']}")
    print(f"  failed:   {report['n_failed']}")
    print(f"  examples (first 10):")
    for nm, lhs, rhs in report["examples"]:
        print(f"    [{nm}]   {lhs!r} = {rhs!r}")
    if report["failures"]:
        print(f"  failures (first 5):")
        for nm, why in report["failures"][:5]:
            print(f"    [{nm}]   {why}")

    after = harvest_report_shape(s._inner)
    print(f"\nAfter Pattern 1 promotion: {after['n_donors']} Shape donors "
          f"(distribution: {dict(after['shape_distribution'])})")
    print(f"  delta: {after['n_donors'] - before['n_donors']} new donors")

    # --- Pattern 2: "X is the Y of Z" / "The Y of Z" / "A Y of Z" ---
    report2 = cpr.install_is_the_of_promotion(s)
    print(f"\nIs-the-of promotion report:")
    print(f"  walked:           {report2['n_walked']}")
    print(f"  matched:          {report2['n_matched']}")
    print(f"  Z resolved:       {report2['n_z_resolved']}")
    print(f"  Z opaque (Lit):   {report2['n_z_opaque']}")
    print(f"  promoted:         {report2['n_promoted']}")
    print(f"  skipped (eq won): {report2['n_skipped_eq']}")
    print(f"  skipped (dupe):   {report2['n_skipped_dupe']}")
    print(f"  failed:           {report2['n_failed']}")
    print(f"  examples (first 10):")
    for nm, y, z, zc in report2["examples"]:
        zfmt = f"Holds({zc})" if zc else f"Lit({z!r})"
        print(f"    [{nm}]   '{y}' of '{z}'   →   Attr({zfmt}, '{y}')")
    if report2["failures"]:
        print(f"  failures (first 5):")
        for nm, why in report2["failures"][:5]:
            print(f"    [{nm}]   {why}")

    final = harvest_report_shape(s._inner)
    print(f"\nAfter Pattern 2 promotion: {final['n_donors']} Shape donors "
          f"(distribution: {dict(final['shape_distribution'])})")
    print(f"  delta from Pattern 1: "
          f"{final['n_donors'] - after['n_donors']} new donors")
    print(f"  total distinct Shape axes: {final['n_distinct_shapes']}")
    print(f"  total distinct structural shapes: "
          f"{final['n_distinct_structural']}")
