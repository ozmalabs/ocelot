"""gender_shape — GENDER AS A DYNAMIC DECODED SHAPE, not a lookup table.

THE CREATOR'S REFRAME: "gender is about SHAPE — but is also extremely dynamic.
But languages that gender words do so by word dequant and object properties."

Grammatical gender is NOT a static table (he=person-male). It is a SHAPE,
DYNAMICALLY DEQUANTIZED, decoded PER ENTITY from three evidence axes:

  (a) WORD-DEQUANT — the word's own gendered FORM. STRONG in gendered
      languages (Spanish -o/-a; German der/die/das article), WEAK/absent in
      English. This is morphology, DECODED (a suffix/article rule), never a
      per-word table.
  (b) OBJECT-PROPERTIES — natural gender read from the referent's OWN dictionary
      properties: king -> male, queen -> female, cock -> male, hen -> female,
      bull/cow, stallion/mare. DECODED from the WordNet gloss of the word's
      animate sense (the object's definition IS its properties), donkey = 0.
  (c) CONTEXT — the pronouns the story actually USES for the entity. This is the
      DYNAMIC axis and lives in the coref DEQUANT (coref_entities.resolve_pronoun):
      the ass is 'he' in THIS tale because the tale assigns it male; the same word
      takes a different gender by context. Context is NOT decoded here — it is the
      sd-loop mint that establishes an underspecified gender when the first
      gendered pronoun lands (see coref_entities).

This module decodes the STATIC prior (word + object). The RESULT is a gender
SHAPE-SIGNATURE (animate / natural-gender male|female|neuter / number), matched
against a pronoun's own lexical shape by a graph-native Term in coref_entities.

An entity whose word + object give no gender is UNDERSPECIFIED (""), and stays so
until context dequantizes it — the honest, dynamic default.

donkey = 0 (no LLM), no `import re` (plain str.split()/strip()), never git.
"""
from __future__ import annotations

from typing import Optional

# --------------------------------------------------------------------------- #
#  THE PRONOUN'S OWN LEXICAL SHAPE — a closed-class table is EXPLICITLY fine
#  here (this is the PRONOUN's gender, its own lexical property, not the
#  REFERENT's gender, which must be decoded). he/him -> male, she/her -> female;
#  it/they/them carry no natural-gender constraint (number/animacy gate them).
# --------------------------------------------------------------------------- #
PRONOUN_GENDER = {
    "he": "male", "him": "male", "his": "male",
    "she": "female", "her": "female", "hers": "female",
}


def pronoun_gender(surface: str) -> Optional[str]:
    """The gendered pronoun's own male/female shape, or None for it/they (no
    natural-gender constraint). The pronoun's LEXICAL property — a table, which
    is legitimate for the pronoun (unlike the referent, whose gender is decoded)."""
    return PRONOUN_GENDER.get((surface or "").lower())


def opposite_gender(g: Optional[str]) -> Optional[str]:
    if g == "male":
        return "female"
    if g == "female":
        return "male"
    return None


# --------------------------------------------------------------------------- #
#  (a) WORD-DEQUANT — the word's gendered FORM. Language-general morphology,
#  DECODED (a suffix / article rule), never a per-word table. English returns
#  "" (its nouns carry no gender morphology); Spanish/German decode from the
#  word-form / article — the axis the creator names ("languages that gender
#  words do so by word dequant").
# --------------------------------------------------------------------------- #
def _tokens(sentence: str) -> list:
    out = []
    for tok in (sentence or "").split():
        t = tok.strip(".,!?;:\"'()[]¿¡«»").lower()
        if t:
            out.append(t)
    return out


_ES_MASC_ART = {"el", "los", "un", "unos"}
_ES_FEM_ART = {"la", "las", "una", "unas"}
_DE_ART = {"der": "male", "die": "female", "das": "neuter",
           "ein": "male", "eine": "female", "den": "male", "dem": "male"}


def _preceding_article(name: str, sentence: str) -> Optional[str]:
    toks = _tokens(sentence)
    nm = (name or "").lower()
    for i, t in enumerate(toks):
        if t == nm and i > 0:
            return toks[i - 1]
    return None


def word_dequant_gender(name: str, sentence: str, language: str) -> str:
    """The word's gendered FORM -> male/female/neuter/"". Morphological decode,
    per language. English: "" (no gender morphology). Spanish: article (el/la...)
    then -o/-a suffix. German: der/die/das article. DECODED rules, not tables.

    HONEST: the Spanish -o/-a rule has lexical exceptions (el día, la mano);
    the German 'die' is also the plural article. These are the known coarse-
    edges of a morphological decode — reported, not hidden."""
    lang = (language or "en").lower()
    if lang.startswith("es"):
        art = _preceding_article(name, sentence)
        if art in _ES_MASC_ART:
            return "male"
        if art in _ES_FEM_ART:
            return "female"
        nm = (name or "").lower()
        if nm.endswith("o"):
            return "male"
        if nm.endswith("a"):
            return "female"
        return ""
    if lang.startswith("de"):
        art = _preceding_article(name, sentence)
        if art in _DE_ART:
            return _DE_ART[art]
        return ""
    return ""


# --------------------------------------------------------------------------- #
#  (b) OBJECT-PROPERTIES — natural gender from the referent's OWN dictionary
#  definition. The word's animate (noun.person / noun.animal) sense whose GLOSS
#  is definitionally gendered ('a male sovereign' / 'adult female chicken') ->
#  male / female. The object's DEFINITION is its property; this reads it, it does
#  not table it. High precision: only the definitional adjectives 'male'/'female'
#  count (so 'a dog ... domesticated by man' does NOT read male off the stray
#  'man'); an ambiguous or absent marker -> "" (underspecified, context decides).
# --------------------------------------------------------------------------- #
def object_property_gender(name: str) -> str:
    """Natural gender decoded from WordNet: king/cock/bull/stallion -> male,
    queen/hen/cow/mare -> female, ass/dog/cat/crow/wolf -> "" (no natural gender,
    context decides). Reads the FIRST animate (person/animal) sense's gloss —
    the object's own dictionary definition. donkey = 0."""
    try:
        from nltk.corpus import wordnet as wn
    except Exception:
        return ""
    nm = (name or "").replace("_", " ")
    try:
        syns = wn.synsets(nm.replace(" ", "_"), pos=wn.NOUN)
    except Exception:
        return ""
    for s in syns:
        try:
            if s.lexname() not in ("noun.person", "noun.animal"):
                continue
            defn = s.definition() or ""
        except Exception:
            continue
        toks = set(defn.replace(";", " ").replace(",", " ")
                   .replace(":", " ").replace("(", " ").replace(")", " ").split())
        m = "male" in toks
        f = "female" in toks
        if m and not f:
            return "male"
        if f and not m:
            return "female"
        return ""            # first animate sense is the decode; ambiguous -> underspecified
    return ""


# --------------------------------------------------------------------------- #
#  THE DECODE — word-dequant first (strong in gendered languages), then
#  object-properties (the fallback natural gender). Returns male/female/neuter/""
#  ("" = UNDERSPECIFIED, the honest dynamic default that context dequantizes).
# --------------------------------------------------------------------------- #
def decode_gender(name: str, sentence: str = "", language: str = "en") -> str:
    """Decode an entity's natural-gender PRIOR from evidence (word-dequant +
    object-properties). "" when neither axis fires — UNDERSPECIFIED, to be
    established dynamically by the first gendered pronoun (context), the sd-loop
    dequant in coref_entities. NOT a per-referent table: every value comes from a
    morphological rule or the word's own dictionary definition."""
    if not isinstance(name, str) or not name:
        return ""
    g = word_dequant_gender(name, sentence, language)
    if g:
        return g
    # object-properties natural gender is English-WordNet-grounded; for a
    # gendered-language token the word-dequant above already carried it.
    if (language or "en").lower().startswith("en"):
        return object_property_gender(name)
    return ""


def gender_shape_signature(name: str, sentence: str, language: str,
                           *, animate: float, number: str) -> dict:
    """The full decoded GENDER SHAPE-SIGNATURE for an entity — animate /
    natural-gender / number. animate + number are supplied by coref_entities
    (which owns the category/whole-animal decode); the natural-gender axis is
    decoded here. A view for the gate/report; the live attrs are written onto the
    SmEntity by coref_entities so the graph-native match Term reads them."""
    return {"animate": float(animate),
            "gender": decode_gender(name, sentence, language) or "",
            "number": number}


__all__ = ["PRONOUN_GENDER", "pronoun_gender", "opposite_gender",
           "decode_gender", "word_dequant_gender", "object_property_gender",
           "gender_shape_signature"]
