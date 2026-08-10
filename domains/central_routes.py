"""central_routes — the CENTRAL triangle (orthography <-> phonology <-> semantics) wiring the SPEECH/
language thread's route components into OUR reading/writing pipeline. graph-native, donkey=0.

THE CONVERGENCE: our peripheral pipeline (reading_writing_pipeline, 660fdb0f) had a pass-through
central STUB. This replaces it with the dual-route + triangle CENTRAL stage:

  LEXICAL route   = the language thread's WordNet lexicon (domains.dictionary_lexicon.dictionary_lookup,
                    IMPORTED READ-ONLY) — whole-word orthography -> concept + definition (SEMANTICS).
                    Handles real/IRREGULAR words; returns None for NONWORDS (the lexical failure).
  SEMANTIC route  = the concept/definition that same lookup returns (the meaning space).
  SUBLEXICAL route= grapheme -> phoneme RULE-ASSEMBLY (a domain-neutral g->p rule table HERE, because
                    the speech thread's sub-lexical route is ACOUSTIC frame->phone, not text g->p).
                    Assembles phonology by rule for ANY letter-string; handles NONWORDS; REGULARIZES
                    irregular words (the sublexical's characteristic over-regularization).

DUAL-ROUTE READING aloud = if the LEXICAL route resolves -> its (correct, incl. irregular) phonology;
else fall back to the SUBLEXICAL route (rule-assembled, regularized). Lesions:
  lesion LEXICAL    -> irregular words fall to sublexical -> REGULARIZED (surface dyslexia/dysgraphia).
  lesion SUBLEXICAL -> nonwords cannot be assembled -> FAIL/lexicalize (phonological dyslexia).
  lesion SEMANTIC   -> the meaning is lost / a semantic neighbour returned (deep dyslexia).

IMPORTED READ-ONLY from the speech/language thread: domains.dictionary_lexicon (NOT edited). The
sublexical g->p table + the route wiring are OURS (additive). No LLM. The phonology assembly is a
held mechanical map; the lexical/semantic lookup is the imported component.
"""
from __future__ import annotations
from typing import Optional

# IMPORTED READ-ONLY: the language thread's lexical+semantic component (WordNet sense lookup).
import domains.dictionary_lexicon as _lex


# ---- SUBLEXICAL: a domain-neutral grapheme->phoneme rule table (ours; the speech g->p is audio) ----
# a small regular g->p mapping; multigraph rules first (context-free rule assembly). REGULARIZES
# irregular spellings (e.g. 'island' -> /island/ pronouncing the 's', the surface-dyslexia error).
_G2P_MULTI = [("tch", "tS"), ("sh", "S"), ("ch", "tS"), ("th", "T"), ("ph", "f"),
              ("ck", "k"), ("ng", "N"), ("qu", "kw"), ("ee", "i"), ("oo", "u"),
              ("ai", "eI"), ("ea", "i"), ("ou", "aU")]
_G2P_SINGLE = {"a": "a", "b": "b", "c": "k", "d": "d", "e": "E", "f": "f", "g": "g",
               "h": "h", "i": "I", "j": "dZ", "k": "k", "l": "l", "m": "m", "n": "n",
               "o": "O", "p": "p", "q": "k", "r": "r", "s": "s", "t": "t", "u": "V",
               "v": "v", "w": "w", "x": "ks", "y": "j", "z": "z"}


def sublexical_g2p(letters):
    """SUBLEXICAL route: assemble phonology from graphemes by RULE (multigraph then single). Works on
    ANY letter-string (nonwords too); REGULARIZES — it pronounces the spelling, so irregular words
    come out regularized (the surface-dyslexia signature). A held mechanical rule-assembly."""
    s = "".join(letters).lower()
    out = []
    i = 0
    while i < len(s):
        matched = False
        for g, p in _G2P_MULTI:
            if s.startswith(g, i):
                out.append(p); i += len(g); matched = True; break
        if not matched:
            out.append(_G2P_SINGLE.get(s[i], s[i])); i += 1
    return out


# a tiny IRREGULAR-pronunciation lexicon: the LEXICAL route's stored (correct) phonology for words
# whose spelling does NOT regularize correctly. The lexical route returns THESE; the sublexical route
# would regularize them (the dissociation). Domain-neutral seed of the lexical phonology store.
_IRREGULAR_PHON = {
    "island": ["aI", "l", "@", "n", "d"],     # silent 's' (sublexical would sound it)
    "yacht": ["j", "Q", "t"],
    "colonel": ["k", "3", "n", "@", "l"],
    "two": ["t", "u"],
}


def lexical_route(word, slot="patient", language="en"):
    """LEXICAL+SEMANTIC route (the IMPORTED language-thread component): whole-word -> concept +
    definition (meaning) via WordNet sense lookup. Returns {concept, definition, phonology} or None
    (None = the word is not in the lexicon = a NONWORD for this route). Irregular phonology comes from
    the stored lexical phonology; regular words get rule phonology (still correct)."""
    info = _lex.dictionary_lookup(word, slot, language)         # IMPORTED READ-ONLY
    if info is None:
        return None
    w = "".join(word).lower() if isinstance(word, (list, tuple)) else str(word).lower()
    phon = _IRREGULAR_PHON.get(w) or sublexical_g2p(w)          # stored irregular, else rule
    return {"concept": info["concept"], "definition": info["definition"], "phonology": phon,
            "source": "lexical"}


def read_aloud(word, *, lesion=None, slot="patient", language="en"):
    """DUAL-ROUTE reading aloud: the LEXICAL route (whole-word, correct/irregular phonology + meaning)
    with the SUBLEXICAL route (rule-assembled, regularized) as the fallback for nonwords. Returns
    {phonology, meaning, route, ok}. lesion in {None,'lexical','sublexical','semantic'} knocks out one
    route -> its characteristic dissociation in the output."""
    w = "".join(word).lower() if isinstance(word, (list, tuple)) else str(word).lower()
    lex = None if lesion == "lexical" else lexical_route(w, slot, language)
    if lex is not None:
        meaning = None if lesion == "semantic" else lex["concept"]
        # SEMANTIC lesion: meaning lost; deep-route may emit a semantic NEIGHBOUR (here: None -> error)
        return {"phonology": lex["phonology"], "meaning": meaning, "route": "lexical",
                "ok": meaning is not None}
    # fall back to the SUBLEXICAL route (rule assembly). lesion sublexical -> cannot assemble nonword.
    if lesion == "sublexical":
        return {"phonology": None, "meaning": None, "route": "sublexical", "ok": False}
    phon = sublexical_g2p(w)
    # the sublexical route has NO meaning (it only assembles sound) -> nonwords have no semantics
    return {"phonology": phon, "meaning": None, "route": "sublexical", "ok": True}


def spell(word, *, lesion=None, slot="patient", language="en"):
    """DUAL-ROUTE spelling (WRITING central stage): the LEXICAL spelling route (stored orthography for
    a known/irregular word) with the SUBLEXICAL phoneme->grapheme route (rule, regularized) fallback.
    Returns {graphemes, route, ok}. lesion lexical -> irregular words spelled by rule (regularized,
    e.g. island->iland-style errors); lesion sublexical -> nonwords cannot be spelled."""
    w = "".join(word).lower() if isinstance(word, (list, tuple)) else str(word).lower()
    known = None if lesion == "lexical" else _lex.dictionary_lookup(w, slot, language)
    if known is not None:
        return {"graphemes": list(w), "route": "lexical", "ok": True}     # correct stored spelling
    if lesion == "sublexical":
        return {"graphemes": None, "route": "sublexical", "ok": False}
    # sublexical spelling: regularize the spelling by RULE (drop a silent leading 's' before a
    # consonant) — the canonical surface-dysgraphia regularization, e.g. island -> iland.
    regularized = list(w)
    if len(w) >= 3 and w[0] == "i" and w[1] == "s" and w[2] not in "aeiou":
        regularized = [w[0]] + list(w[2:])
    return {"graphemes": regularized, "route": "sublexical", "ok": True}
