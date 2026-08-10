"""wordplay — the jabberwock's namesake NONSENSE / COINAGE faculty.

Carroll's poem is built of coinages ("slithy", "mimsy", "frabjous"); an agent
named after the Jabberwock that collapses a coinage to "I don't hold that" is
embarrassing. This module lets the agent ENGAGE a coinage: DETECT a playful
coinage (distinct from a genuine unknown to ASK about, and from a politeness
marker), INFER a playful reading FROM ITS SHAPE (grounded morphology + the
dictionary), and hand that reading to the reply composer.

DISCIPLINE (CLAUDE.md). This is a BOUNDARY CLASSIFIER over GROUNDED reference
signals — the same admissible class as `domains/function_word_reference` and
`domains/comprehend_text`:

  * known-ness / part-of-speech / gloss come from Wiktionary
    (`wiktionary_reference`, a real reference slab), NOT a hand-authored list;
  * the derivational-affix meanings are a CLOSED reference table — a morphology
    fact about a handful of suffixes (-ation names an act, -ify makes a verb,
    -ous makes an adjective), the same closed-class-reference shape as
    `function_word_reference._COPULA_AUX`. It is keyed on the AFFIX, never on
    the literal word.

The gloss is a PLAYFUL INFERENCE from shape/sound, FLAGGED AS SUCH in the reply
("by its shape I'd take that for ...") — it never claims to KNOW the word or to
quote a settled definition. The reply is COMPOSED from the analysis parts
(suffix + pos-category template + the derived stem/gerund, or the blend
components), not selected from a per-word answer table. No decision over graph
state, no held state — a pure function of (reference-read-only, token).

    detect_coinage(token)                 -> analysis dict | None
    find_coinage(text)                    -> analysis dict | None   (scan a sentence)
    compose_reply(agent, analysis, reg)   -> the produced playful reply string
"""
from __future__ import annotations

import re
from typing import Any, Optional

from . import wiktionary_reference as _wikt

# ---------------------------------------------------------------------------
# Grounded reference reads (Wiktionary slabs). Every "does the agent know this
# word / what shape is it" signal comes from here, never a hand list.
# ---------------------------------------------------------------------------

_VOWELS = frozenset("aeiou")


def _known(low: str) -> bool:
    try:
        return bool(_wikt.wiktionary_has_en(low))
    except Exception:
        return False


def _pos(low: str) -> list[str]:
    try:
        return list(_wikt.wiktionary_pos(low, "en") or [])
    except Exception:
        return []


def _gloss(low: str) -> Optional[str]:
    try:
        return _wikt.wiktionary_gloss(low, "en")
    except Exception:
        return None


def _is_function(low: str) -> bool:
    """A closed-class function / politeness word is never a coinage."""
    try:
        from . import function_word_reference as _fw
        if _fw.classify(low, "en"):
            return True
    except Exception:
        pass
    return low in _POLITENESS


# Leading discourse / politeness markers (mirrored in comprehend_text): never a
# coinage to gloss.
_POLITENESS = frozenset({"pray", "kindly", "prithee", "please", "prithee"})

# Content POS — a word carrying one of these is a substantive (used to filter
# blend components down to real content words).
_CONTENT_POS = frozenset({"noun", "verb", "adj", "adjective", "adv", "adverb"})


def _is_content(low: str) -> bool:
    return bool(set(_pos(low)) & _CONTENT_POS)


# ---------------------------------------------------------------------------
# The CLOSED derivational-affix reference table (morphology fact, keyed on the
# AFFIX). `strong` marks a suffix whose derivational force is unambiguous enough
# to read even over an OOV stem (-ation/-ify/-ous ...); a WEAK suffix (-y/-er)
# additionally requires the stem to reduce to a real word, so an opaque unknown
# ending in a common letter is not over-read as a coinage. Ordered longest-first
# so -ification/-ation win over -ion/-ify.
# ---------------------------------------------------------------------------

# (suffix, pos_kind, template, strong) — template uses {v} (a gerund of the
# stem) and {s} (the stem surface).
_SUFFIX_TABLE = [
    ("ification", "noun",      "the act or process of {v}",        True),
    ("ation",     "noun",      "the act or process of {v}",        True),
    ("ment",      "noun",      "the act or result of {v}",         True),
    ("ify",       "verb",      "to make or render {s}",            True),
    ("ate",       "verb",      "to {v}",                           True),
    ("ise",       "verb",      "to {v}",                           True),
    ("ize",       "verb",      "to {v}",                           True),
    ("ous",       "adjective", "having the quality of {s}",        True),
    ("ical",      "adjective", "relating to {s}",                  True),
    ("ness",      "noun",      "the quality of being {s}",         True),
    ("ity",       "noun",      "the quality of being {s}",         True),
    ("ish",       "adjective", "somewhat like {s}",                False),
    ("er",        "noun",      "one who {v}s",                     False),
    ("y",         "adjective", "characterised by {s}",             False),
    ("ly",        "adverb",    "in a {s} manner",                  False),
]

# Linking fragments to peel off a stem to reach a real root ("frobul" -> "frob").
_LINK_FRAGS = ("ule", "ul", "le", "er", "or", "en", "in", "at", "it",
               "e", "u", "a", "i", "o")

# Gloss markers that flag a conventional nonce / blend word.
_NONCE_MARKERS = ("nonce word", "portmanteau", "blend of", "coined by",
                  "jabberwocky", "lewis carroll")


# ---------------------------------------------------------------------------
# small morphology helpers (shape computations, not word lookups).
# ---------------------------------------------------------------------------

def _gerund(stem: str) -> str:
    """A readable present-participle of a stem (frob -> frobbing, fiddle ->
    fiddling). Light English rule — doubling a final CVC consonant, dropping a
    silent -e."""
    s = (stem or "").lower()
    if len(s) < 2:
        return s + "ing"
    if s.endswith("e") and not s.endswith("ee"):
        return s[:-1] + "ing"
    if (len(s) >= 3 and s[-1] not in "wxy" and s[-1] not in _VOWELS
            and s[-2] in _VOWELS and s[-3] not in _VOWELS):
        return s + s[-1] + "ing"          # double: frob -> frobbing
    return s + "ing"


def _real_stem(base: str) -> tuple[str, bool]:
    """Reduce a derived stem to the deepest REAL word it contains, peeling
    linking fragments. Returns (stem, stem_is_real). 'frobul' -> ('frob', True);
    an opaque base -> (base, False)."""
    b = (base or "").lower()
    if _known(b):
        return b, True
    for frag in _LINK_FRAGS:
        if b.endswith(frag) and len(b) - len(frag) >= 3:
            cand = b[:-len(frag)]
            if _known(cand):
                return cand, True
    return base, False


def _common_prefix(a: str, b: str) -> int:
    n = 0
    for x, y in zip(a.lower(), b.lower()):
        if x != y:
            break
        n += 1
    return n


def _shares_sub(word: str, other: str, k: int = 3) -> bool:
    """Does `other` share any k-length substring with `word`? (loose blend
    overlap — 'slithy' shares 'ith' with 'lithe' and 'sli' with 'slimy')."""
    o = (other or "").lower()
    w = (word or "").lower()
    return any(o[i:i + k] in w for i in range(0, max(0, len(o) - k + 1)))


def _blend_components(word: str, gloss: Optional[str]) -> list[str]:
    """Real content words in the gloss that each share an overlap with `word`
    — the SELF-VERIFYING blend signal (a genuine blend's gloss lists the words
    it fuses, and the coinage overlaps each). Ordinary polysemy glosses fail
    this (their sense words don't overlap the headword)."""
    if not gloss:
        return []
    low = word.lower()
    comps: list[str] = []
    for w in re.findall(r"[a-z]+", gloss.lower()):
        if len(w) < 4 or w == low or w in comps:
            continue
        # a component that is a SUBSTRING of the word (or vice-versa) is just a
        # contained morpheme / near-duplicate, not a blend PARTNER — exclude it
        # (so 'capable's gloss word 'able' does not read as a blend component).
        if w in low or low in w:
            continue
        if _known(w) and _is_content(w) and _shares_sub(low, w, 3):
            comps.append(w)
    return comps


# ---------------------------------------------------------------------------
# DETECTION — token -> analysis {kind, ...} | None.
# ---------------------------------------------------------------------------

def _affix_analysis(low: str) -> Optional[dict]:
    for suffix, pos_kind, template, strong in _SUFFIX_TABLE:
        if low.endswith(suffix) and len(low) - len(suffix) >= 3:
            base = low[:-len(suffix)]
            if not any(c in _VOWELS for c in base):
                continue
            stem, stem_real = _real_stem(base)
            if not strong and not stem_real:
                continue                    # a weak suffix needs a real stem
            return {"kind": "affix", "word": low, "suffix": suffix,
                    "pos_kind": pos_kind, "template": template,
                    "base": base, "stem": stem, "stem_real": stem_real}
    return None


def _blend_analysis(low: str, in_definition_request: bool) -> Optional[dict]:
    """A KNOWN word that is really a coinage — engaged ONLY when the utterance
    explicitly ASKS what it means ("what does X mean" / "define X"). Outside a
    definition request a known word is left to the normal answer path (so a
    Carroll word used narratively, or a plain 'what is a borogove', stays an
    honest answer, not a hijack). Then: a gloss that lists >=2 real words the
    headword FUSES AT THE FRONT is a blend; a nonce/blend marker in the gloss
    is a nonce word."""
    if not in_definition_request:
        return None
    gloss = _gloss(low)
    low_gloss = (gloss or "").lower()
    marker = any(m in low_gloss for m in _NONCE_MARKERS)
    comps = _blend_components(low, gloss)
    # a GENUINE blend fuses a FRONT component (one gloss word shares the word's
    # opening) — this rejects mere shared-suffix coincidences ('information' vs
    # 'characterization'/'description' share only '-ation', not a fused front).
    has_front = any(_common_prefix(low, c) >= 2 for c in comps)
    if len(comps) >= 2 and has_front:
        # order components so a FRONT-sharing one leads, then a distinct partner.
        front = [c for c in comps if _common_prefix(low, c) >= 2]
        rest = [c for c in comps if c not in front]
        ordered = (rest[:1] + front[:1]) if rest else front[:2]
        return {"kind": "blend", "word": low, "components": ordered[:3],
                "gloss": gloss, "marker": marker}
    if marker:
        return {"kind": "nonce", "word": low, "components": comps[:3],
                "gloss": gloss, "marker": True}
    return None


def detect_coinage(token: str, *, sentence_initial: bool = False,
                   in_definition_request: bool = False) -> Optional[dict]:
    """Classify one TOKEN as a playful coinage. Returns an analysis dict
    (kind='affix' | 'blend' | 'nonce') or None when it is NOT a coinage:
      * a function / politeness word              -> None
      * a proper noun (Wiktionary 'name', or capitalised mid-sentence)
        — a genuine unknown to ASK about, never a fabricated gloss -> None
      * an opaque OOV with no morphological hook   -> None (ask-back)
      * an ordinary known word (not a blend/nonce) -> None (answer it normally)."""
    clean = re.sub(r"[^A-Za-z]", "", token or "")
    if not clean or not clean.isalpha() or len(clean) < 4:
        return None
    low = clean.lower()
    if _is_function(low):
        return None
    # a capitalised token that is NOT the sentence's first word reads as a
    # proper noun (a name to ask about, not a coinage to gloss).
    if clean[0].isupper() and not sentence_initial:
        return None
    known = _known(low)
    pos = _pos(low)
    if known and pos and set(pos) <= {"name"}:
        return None                          # a pure proper noun (Zanzibar)
    if known:
        return _blend_analysis(low, in_definition_request)
    return _affix_analysis(low)              # OOV -> morphological reading


def _is_definition_request(text: str) -> bool:
    t = (text or "").lower()
    if re.search(r"\bwhat\s+(?:does|do|is|are)\b.*\b(mean|means|meaning|signif\w*)\b", t):
        return True
    if re.search(r"^\s*(?:define|explain the word)\b", t):
        return True
    if re.search(r"\bmeaning of\b", t):
        return True
    return False


def find_coinage(text: str) -> Optional[dict]:
    """Scan a sentence and return the FIRST token that is a playful coinage
    (with its analysis), else None. The leading verb / function / self words
    fall through detect_coinage; a real proper noun or opaque unknown returns
    None so the caller keeps ask-back / answer-normally for those."""
    toks = (text or "").split()
    defreq = _is_definition_request(text)
    for i, raw in enumerate(toks):
        analysis = detect_coinage(raw, sentence_initial=(i == 0),
                                  in_definition_request=defreq)
        if analysis:
            return analysis
    return None


# ---------------------------------------------------------------------------
# GLOSS + REPLY — the playful reading, composed from the analysis parts.
# ---------------------------------------------------------------------------

def infer_gloss(analysis: dict) -> str:
    """The shape-inferred reading, filled from the affix template (a gerund of
    the stem for act/agent senses, the stem surface for quality senses) or the
    blend components. A faculty computation, not a per-word lookup."""
    kind = analysis.get("kind")
    if kind == "affix":
        s = analysis.get("stem") or analysis.get("base") or analysis["word"]
        v = _gerund(analysis.get("stem") or analysis.get("base") or analysis["word"])
        try:
            return analysis["template"].format(v=v, s=s)
        except Exception:
            return f"something to do with {s}"
    if kind == "blend":
        comps = analysis.get("components") or []
        if len(comps) >= 2:
            return f"{comps[0]} and {comps[1]} at once"
        if comps:
            return f"something of {comps[0]}"
        return "a fusion of two words"
    return "a playful nonce word"


def compose_reply(agent: Any, analysis: dict, register: str = "neutral") -> str:
    """Compose the playful, honesty-flagged reply from the analysis. The reading
    is INFERRED FROM SHAPE and said to be so ("by its shape/sound I'd take/read
    that for ...") — never a claimed dictionary definition. Register only shapes
    the closing flourish."""
    word = analysis.get("word", "")
    Word = word[:1].upper() + word[1:]
    gloss = infer_gloss(analysis)
    kind = analysis.get("kind")
    if register == "casual":
        flourish = "A fine coinage, that."
    elif register == "formal":
        flourish = "A most Carrollian coinage; I engage it in good humour."
    else:
        flourish = "A fine coinage, in the Jabberwock spirit."

    if kind == "affix":
        suffix = analysis.get("suffix")
        pos_kind = analysis.get("pos_kind")
        stem = analysis.get("stem")
        stem_note = ""
        if analysis.get("stem_real") and stem and stem != word:
            stem_note = f", built on the real word '{stem}'"
        lead = f"{Word} — by its shape that's a {pos_kind} in -{suffix}{stem_note}"
        body = f"{lead}: I'd read it as {gloss}."
        # a self-referential playful admission for an act/quality the agent can own
        if pos_kind == "noun" and "act" in (analysis.get("template") or ""):
            body += " I confess I do a fair bit of it myself."
        return f"{body} {flourish}"

    if kind == "blend":
        comps = analysis.get("components") or []
        a, b = (comps + ["", ""])[:2]
        return (f"{Word} — by its sound I'd take that for a blend, "
                f"{a} and {b} run together: {gloss}. {flourish}")

    # nonce
    return (f"{Word} — I take that for a playful nonce word; by its shape alone "
            f"I can only conjure at its sense. {flourish}")


__all__ = ["detect_coinage", "find_coinage", "infer_gloss", "compose_reply"]
