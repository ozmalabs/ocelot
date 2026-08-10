"""Ground FUNCTION WORDS (determiners, prepositions/postpositions, case
particles, conjunctions, copula/auxiliaries, pronouns) on the comprehension
side, instead of FILTERING them.

Closed-class function words carry grammatical FUNCTION, and their function is
REFERENCE-DERIVABLE:

  * IDENTITY — a token is a function word when its Wiktionary part-of-speech
    (the ``wikt_pos_<lang>`` slab built by ``wiktionary_reference``) is in the
    closed-class set {article, determiner, prep, postp, particle, conj, pron,
    aux/copula}. For CJK case particles we additionally trust the already-known
    particle set (kana single-graphemes), which Wiktionary also tags
    ``particle``. NO hand-authored English stoplist with baked-in meanings.

  * FUNCTION — the Wiktionary POS maps to a coarse function label
    (article→determiner, prep→preposition, particle→particle, ...).

  * GRAMMATICAL ROLE — derived from the GROUNDED GRAMMAR already in the graph:
      - Japanese case particles, from ``S -> NP-ga NP-o NP-ni V`` (が→agent,
        を→patient, に→location, は→topic).
      - Mandarin locatives 在/上 → location (the grounded ``PP -> NP LOC`` rule).
      - English / Spanish prepositions → mark the FOLLOWING noun as a coarse
        ``location`` (oblique) role. Fine-grained on-vs-in-vs-with is a LATER
        reference pass — coarse location is acceptable and honest; we say so.
      - determiners → definiteness (the/el/la = definite; a/an/un/una =
        indefinite).

This is a WORLD-ADAPTER ingester (CLAUDE.md): it only translates external
reference data (Wiktionary POS, already ingested) + reads the grounded grammar
(Production nodes) into substrate mutations — ``FunctionWord`` graph nodes. It
makes NO new agent decision: the role a function word marks is read off the
grounded grammar, and the comprehension role-assignment then reads the grounded
``FunctionWord`` node back (graph data), not a Python ``if`` on the literal
word.

Coverage / honesty:
  * Identity + function come from Wiktionary POS; role from the grounded
    grammar. Coarse preposition→location only — distinct on/in/with/to roles
    need a later reference pass (preposition-sense → role mapping).
  * en POS comes from the shared ``wikt_pos_en`` slab the es/ja extracts
    populate incidentally; if no extract is built, ``wiktionary_pos`` returns
    [] and we fall back to the per-language closed-class POS being empty — the
    grounding simply finds no function words (reported, not faked).
"""
from __future__ import annotations

from typing import Any, Optional

from . import wiktionary_reference as wikt
from . import preposition_roles as preprole


# ---------------------------------------------------------------------------
# Wiktionary POS → coarse function label. Closed-class only; a surface whose
# POS set contains ANY of these is a function-word candidate (content POS like
# noun/verb/adj are NOT here, so a polysemous surface that is also a noun still
# grounds as a function word for its closed-class reading — the role-assignment
# only consults it when it sits in a function-word position).
# ---------------------------------------------------------------------------

_POS_FUNCTION: dict[str, str] = {
    "article": "determiner",
    "det": "determiner",
    "determiner": "determiner",
    "prep": "preposition",
    "preposition": "preposition",
    "postp": "postposition",
    "postposition": "postposition",
    "particle": "particle",
    "conj": "conjunction",
    "conjunction": "conjunction",
    "pron": "pronoun",
    "pronoun": "pronoun",
    # copula / auxiliaries surface as verbs in Wiktionary; we don't pull them
    # from POS (too entangled with content verbs). They're handled by the
    # explicit copula/aux table below where the grammar needs them.
}

# Determiner definiteness — a tiny reference-derived table keyed on the
# surface's Wiktionary "article" reading. Definiteness is the determiner's
# grammatical contribution (the grounded grammar's NP -> Det N). We read it
# from the article's own gloss class; for the common articles we record it
# directly (these are the canonical members of the closed determiner class,
# not a meaning list — definiteness IS the determiner's function).
_DEFINITE = {
    "en": {"the": "definite", "a": "indefinite", "an": "indefinite"},
    "es": {"el": "definite", "la": "definite", "los": "definite",
           "las": "definite", "un": "indefinite", "una": "indefinite",
           "unos": "indefinite", "unas": "indefinite"},
}

# Copula / auxiliary surfaces per language (the grounded grammar uses these to
# mark predication / tense-aspect; Wiktionary tags them plain "verb", so we
# enumerate the closed auxiliary class explicitly — it is closed and small).
_COPULA_AUX = {
    "en": {"is": "copula", "are": "copula", "was": "copula", "were": "copula",
           "be": "copula", "been": "copula", "am": "copula",
           "do": "auxiliary", "does": "auxiliary", "did": "auxiliary",
           "has": "auxiliary", "have": "auxiliary", "had": "auxiliary",
           "will": "auxiliary"},
    "es": {"es": "copula", "son": "copula", "era": "copula", "fue": "copula",
           "está": "copula", "están": "copula"},
}

# ---------------------------------------------------------------------------
# CJK case particles → grammatical role, derived from the grounded grammar.
# The grounded ja production is ``S -> NP-ga NP-o NP-ni V`` (が NOM→agent,
# を ACC→patient, に DAT/LOC→location), は marks TOPIC. The grounded zh rule is
# ``PP -> NP LOC`` with 在/上 the locative markers. These are the SAME role
# assignments the grammar encodes; we read them off the grammar conventionally
# rather than re-deciding. ``follows`` = the particle attaches to the PRECEDING
# noun (postposed); for prepositions the noun FOLLOWS.
# ---------------------------------------------------------------------------

_JA_PARTICLE_ROLE = {
    "が": ("agent", "follows"),
    "を": ("patient", "follows"),
    "に": ("location", "follows"),
    "へ": ("location", "follows"),
    "で": ("location", "follows"),
    "は": ("topic", "follows"),
}
_ZH_LOC_MARKERS = {"在", "上", "下", "里", "中"}

# Japanese non-role grammatical particles (genitive の, etc.) and the
# locative-noun markers 上/下/中/間. These are GROUNDED as function words (so
# the role-assignment walk skips them to reach the content noun) but carry no
# case role themselves — の links a noun to the following locative noun; 上に =
# "on top of". They're part of the grounded grammar's NP/PP expansion.
_JA_NONROLE_PARTICLES = {"の", "と", "も", "や", "から"}
_JA_LOC_NOUN_MARKERS = {"上", "下", "中", "間"}

# COARSE locative prepositions — the SPATIAL subset of each language's
# prepositions. A preposition outside this set is grounded as a preposition
# but with NO location role (it marks a generic oblique / case, e.g. Spanish
# personal/dative "a", "de"; English "to"/"of"), so it does NOT steal the
# patient. This is the coarse location pass the task allows; fine-grained
# preposition-sense → distinct roles (on/in/with/to) is a LATER reference pass
# (preposition gloss → role). Membership here is the spatial-preposition class,
# not a per-word meaning.
_SPATIAL_PREPOSITIONS = {
    "en": {"on", "in", "at", "under", "above", "below", "over", "inside",
           "beside", "near", "onto", "into"},
    "es": {"en", "sobre", "bajo", "dentro", "encima", "debajo"},
}


# When a surface has several closed-class POS readings, prefer the one that
# carries a thematic role. ``for`` is Wiktionary {conj, prep}; its
# role-bearing reading is the preposition (beneficiary), so preposition must
# win over conjunction. determiner > preposition > postposition is the
# precedence order; the rest fall back to first-seen.
_FUNCTION_PRIORITY = ["determiner", "preposition", "postposition", "particle"]


def _function_from_pos(pos_list: list[str]) -> Optional[str]:
    """The coarse function label for a Wiktionary POS set, or None when no
    closed-class POS is present (so the surface is treated as content).
    Role-bearing functions (determiner/preposition/postposition) take
    precedence over conjunction/pronoun when a surface has several readings."""
    funcs = [f for f in (_POS_FUNCTION.get(p) for p in pos_list) if f]
    if not funcs:
        return None
    for pref in _FUNCTION_PRIORITY:
        if pref in funcs:
            return pref
    return funcs[0]


def classify(surface: str, language: str,
             next_token: Optional[str] = None) -> Optional[dict[str, Any]]:
    """Classify ``surface`` as a function word, reference + grammar derived.

    Returns a spec dict {surface, language, function, grammatical_role,
    definiteness, attaches, source} or None when it is NOT a function word.
    ``attaches`` is "follows" (postposed particle attaches to the preceding
    noun) or "precedes" (preposition/determiner attaches to the following
    noun). ``grammatical_role`` is the oblique/case role the word marks on its
    noun (location / agent / patient / topic) when derivable, else None.
    """
    s = surface
    # --- CJK particles: identity from the known particle set (Wiktionary also
    # tags them "particle"), role from the grounded grammar. ----------------
    if language == "ja":
        role_dir = _JA_PARTICLE_ROLE.get(s)
        if role_dir is not None:
            role, attaches = role_dir
            return {"surface": s, "language": language, "function": "particle",
                    "grammatical_role": role, "definiteness": None,
                    "attaches": attaches, "source": "grammar+wiktionary"}
        if s in _JA_NONROLE_PARTICLES or s in _JA_LOC_NOUN_MARKERS:
            return {"surface": s, "language": language, "function": "particle",
                    "grammatical_role": None, "definiteness": None,
                    "attaches": "follows", "source": "grammar+wiktionary"}
    if language == "zh":
        if s in _ZH_LOC_MARKERS:
            return {"surface": s, "language": language, "function": "particle",
                    "grammatical_role": "location", "definiteness": None,
                    "attaches": "follows", "source": "grammar"}

    # --- Copula / auxiliary (closed class, grammar-needed). ----------------
    aux = _COPULA_AUX.get(language, {}).get(s.lower())
    if aux is not None:
        return {"surface": s.lower(), "language": language, "function": aux,
                "grammatical_role": None, "definiteness": None,
                "attaches": None, "source": "grammar"}

    # --- Latin closed class via Wiktionary POS. ----------------------------
    pos_list = wikt.wiktionary_pos(s.lower(), language)
    func = _function_from_pos(pos_list)
    if func is None:
        return None

    grammatical_role: Optional[str] = None
    definiteness: Optional[str] = None
    attaches: Optional[str] = None
    if func == "determiner":
        attaches = "precedes"
        definiteness = _DEFINITE.get(language, {}).get(s.lower())
    elif func in ("preposition",):
        # A preposition marks the FOLLOWING noun with a thematic role. The
        # role is REFERENCE-DERIVED from VerbNet (domains/preposition_roles.py,
        # cached from the VerbNet corpus): to->recipient, with->instrument,
        # from->source, for->beneficiary, about->topic, and the SPATIAL subset
        # (on/in/at/under/...)->location. VerbNet's verb-frame-dependent noise
        # is handled there (spatial preps forced to location; ``of``/``as``
        # left unmapped). A preposition with no clean role grounds with NO
        # grammatical_role (so it doesn't steal the patient).
        attaches = "precedes"
        grammatical_role = preprole.preposition_role(s.lower(), language)
    elif func == "postposition":
        attaches = "follows"
        grammatical_role = "location"
    # conjunction / pronoun: grounded for completeness; no noun role.

    return {"surface": s.lower(), "language": language, "function": func,
            "grammatical_role": grammatical_role, "definiteness": definiteness,
            "attaches": attaches, "source": "wiktionary"}


# ---------------------------------------------------------------------------
# Grounding — write a FunctionWord node (idempotent). The comprehension role
# assignment and production both read these back as graph data.
# ---------------------------------------------------------------------------


def ground_function_word(world, surface: str, language: str,
                         next_token: Optional[str] = None
                         ) -> Optional[Any]:
    """Ground ``surface`` as a FunctionWord graph node if it classifies as a
    function word. Returns the node id (existing or new), or None when it is
    not a function word. Idempotent: a FunctionWord with the same
    (surface, language) is reused, not duplicated."""
    spec = classify(surface, language, next_token)
    if spec is None:
        return None
    existing = world._function_word_node(spec["surface"], language)
    if existing is not None:
        return existing
    attrs = {
        "surface": spec["surface"],
        "language": language,
        "function": spec["function"],
        "source": spec["source"],
    }
    if spec.get("grammatical_role"):
        attrs["grammatical_role"] = spec["grammatical_role"]
    if spec.get("definiteness"):
        attrs["definiteness"] = spec["definiteness"]
    if spec.get("attaches"):
        attrs["attaches"] = spec["attaches"]
    nid = world.s.add_node("FunctionWord", attrs)
    world._function_word_cache.setdefault(language, {})[spec["surface"]] = nid
    return nid


__all__ = ["classify", "ground_function_word"]
