"""remainder_classification — the agent LEARNS to classify the words it can't
ground, and captures each kind appropriately. Taught, not seeded.

After the dictionary/wiki/eponym/acronym readers, a residue of words still won't
ground. They are NOT all the same: some are technical ACRONYMS, some CODE
IDENTIFIERS ('argmax', 'alloc'), some PERSON names, some genuine DOMAIN JARGON.
An undifferentiated 'frontier' is the wrong capture — each kind wants different
handling.

The agent does not get a seeded taxonomy. It LEARNS one:
  1. it consults its TEACHER on a SAMPLE of the residue (the teacher_hook 'ask
     when you're stuck' channel) — proposing each word's KIND + how to capture it;
     each reply is recorded as a TaughtHint;
  2. it INDUCES a classifier from the taught examples — generalising the SHAPE
     features (all-caps, code-punctuation, capitalised proper, length, in-WordNet)
     that distinguish the kinds (implied_rule.anti_unify), so it need not ask
     again;
  3. it APPLIES the learned classifier to the WHOLE residue and CAPTURES each word
     as a typed node (Acronym / CodeIdentifier / PersonName / DomainTerm / Unknown)
     it can then reason about — the residue becomes structured, not a flat dark
     list.

The teacher supplies the labels; the agent generalises and captures. No category
is hand-seeded here; the only fixed thing is the world-adapter plumbing.
"""
from __future__ import annotations

import json
import re

from domains.implied_rule import anti_unify, covers, WILD

# the kinds the agent may be taught (the teacher uses these labels; the agent
# learns to RECOGNISE them — it is not seeded with how).
KINDS = ("acronym", "code_identifier", "person_name", "domain_term", "ordinary_word")


def features(word: str, context: str = "") -> dict:
    """The SHAPE features the classifier generalises over — read off the word (and
    the case it appears in, in the prose). Pure surface description, no decision."""
    cased = _cased_form(word, context)
    return {
        "caps": ("ALLCAPS" if cased.isupper() and len(cased) > 1
                 else "Capitalized" if cased[:1].isupper() else "lower"),
        "len": "short" if len(word) <= 5 else "medium" if len(word) <= 9 else "long",
        "punct": ("underscore" if "_" in word else "camel"
                  if _has_camel(cased) else "alpha"),
        "wordnet": "in_wn" if _in_wordnet(word) else "not_wn",
        "vowels": "has_vowel" if re.search(r"[aeiou]", word) else "no_vowel",
    }


def _cased_form(word: str, context: str) -> str:
    """How the word is cased where the prose uses it (ALLCAPS for an acronym,
    Capitalized for a name) — the case is a feature the lowercased token lost."""
    m = re.search(r"\b(" + re.escape(word) + r")\b", context, re.IGNORECASE)
    return m.group(1) if m else word


def _has_camel(s: str) -> bool:
    return bool(re.search(r"[a-z][A-Z]", s))


def _in_wordnet(word: str) -> bool:
    try:
        from domains.dict_teacher import _wordnet
        return bool(_wordnet().synsets(word))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# (1) TEACH — the agent asks the teacher to classify a sample of its residue.
# ---------------------------------------------------------------------------

def teach_sample(substrate, sample, context_of, ask) -> dict:
    """Consult the teacher to classify a SAMPLE of residue words. `sample` is a
    list of words; `context_of(word)` returns a short prose snippet. Records a
    TaughtHint per word. Returns {word: kind}."""
    items = [{"word": w, "context": context_of(w)[:160]} for w in sample]
    q = (
        "I am grounding a technical encyclopedia and these words won't resolve in "
        "my dictionary. Classify EACH into exactly one KIND and nothing else:\n"
        "  acronym        — a technical initialism (AAC, TCP, ALU)\n"
        "  code_identifier— a code/symbol token, not an English word (argmax, alloc, args)\n"
        "  person_name    — a person's name / eponym (Ackermann, Amdahl)\n"
        "  domain_term    — a real technical term, just niche (allostatic, aperiodic)\n"
        "  ordinary_word  — an ordinary English word my dictionary simply missed\n\n"
        + "\n".join(f"{it['word']}\t{it['context']}" for it in items)
        + "\n\nReply ONLY a JSON object {word: kind}, kinds from the five above.")
    reply = ask(q)
    labels = _parse_labels(reply, [w for w in sample])
    for w, kind in labels.items():
        substrate.add_node("TaughtHint", {
            "question": f"classify residue word {w!r}",
            "answer": kind, "for_word": w, "grounded": 0})
    return labels


_FENCE = re.compile(r"\{.*\}", re.S)


def _parse_labels(reply: str, words) -> dict:
    if not reply:
        return {}
    m = _FENCE.search(reply)
    try:
        raw = json.loads(m.group(0)) if m else {}
    except Exception:
        raw = {}
    wl = {w.lower(): w for w in words}
    out = {}
    for k, v in raw.items():
        kk = wl.get(str(k).lower())
        vv = str(v).strip().lower().replace(" ", "_").replace("-", "_")
        if kk and vv in KINDS:
            out[kk] = vv
    return out


# ---------------------------------------------------------------------------
# (2) LEARN — induce a classifier from the taught (features -> kind) examples.
# ---------------------------------------------------------------------------

def learn_classifier(taught: dict, context_of) -> dict:
    """Generalise the taught examples into one feature-pattern per KIND
    (anti_unify the feature dicts of each kind's taught words). The agent's own
    induction — it now recognises a kind by its shape, no teacher needed."""
    by_kind: dict[str, list] = {}
    for word, kind in taught.items():
        by_kind.setdefault(kind, []).append(features(word, context_of(word)))
    return {kind: anti_unify(feats) for kind, feats in by_kind.items() if feats}


def classify(word: str, context: str, learned: dict) -> str:
    """Apply the learned classifier: the KIND whose induced pattern best covers the
    word's features (most fixed — non-wildcard — feature slots matched). Falls back
    to 'domain_term' (a real word the readers missed) when nothing covers."""
    f = features(word, context)
    best, best_fixed = None, -1
    for kind, pattern in learned.items():
        if isinstance(pattern, dict) and covers(pattern, f):
            fixed = sum(1 for v in pattern.values() if v != WILD)
            if fixed > best_fixed:
                best, best_fixed = kind, fixed
    return best or "domain_term"


# ---------------------------------------------------------------------------
# (3) CAPTURE — each kind as a typed node the agent can reason about.
# ---------------------------------------------------------------------------

_CAPTURE_TYPE = {
    "acronym": "Acronym",
    "code_identifier": "CodeIdentifier",
    "person_name": "PersonName",
    "domain_term": "DomainTerm",
    "ordinary_word": "DomainTerm",
}


def capture(substrate, word: str, kind: str, context: str = "") -> int:
    """Capture a residue word as its KIND — a typed node carrying the surface +
    where it came from. The residue is now structured graph data, classified, not
    a flat dark list. Returns the node id."""
    ntype = _CAPTURE_TYPE.get(kind, "DomainTerm")
    return substrate.add_node(ntype, {
        "surface": word, "kind": kind, "context": context[:200],
        "origin": "remainder_classification"})


def classify_and_capture(substrate, residue, context_of, ask, *,
                         sample_size: int = 40) -> dict:
    """End to end: teach on a sample, induce a classifier, apply + capture the whole
    residue. Returns {counts per kind, learned, taught}."""
    sample = list(residue)[:sample_size]
    taught = teach_sample(substrate, sample, context_of, ask)
    learned = learn_classifier(taught, context_of)
    counts: dict[str, int] = {}
    for w in residue:
        kind = taught.get(w) or classify(w, context_of(w), learned)
        capture(substrate, w, kind, context_of(w))
        counts[kind] = counts.get(kind, 0) + 1
    return {"counts": counts, "learned": learned, "n_taught": len(taught)}
