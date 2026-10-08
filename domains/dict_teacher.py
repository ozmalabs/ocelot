"""Dictionary as the cheapest lookup teacher — WordNet via NLTK.

Same callable shape as ``WikiTeacher`` (and the LLM self-teacher): a
``(question_text) -> payload`` callable the agent's impasse-resolver
spawns and learns from. Chain order is dictionary → wiki → LLM, each
falling through on miss. Each link costs roughly one order of magnitude
more than the one before it:

  dictionary (WordNet) :  µs   in-memory hash + synset walk
  wikipedia (parquet)  :  ms   sqlite point-lookup + parquet row read
  LLM                  :  s    api round-trip + tokens

The dictionary covers the long tail of common nouns / verbs / adjectives
(~117 k entries in en wordnet). For those, it's strictly cheaper than
hitting wiki — and wiki sits behind it for everything wordnet doesn't
know (proper nouns, jargon, novel concepts).

The teacher returns ``None`` on miss; chain via the optional ``fallback``
callable.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .question_subject import extract_subject


# Part-of-speech tag → human-readable, used to flavour the answer text.
# WordNet uses 'n', 'v', 'a' (adjective), 's' (satellite adjective), 'r' (adverb).
_POS_NAMES = {
    "n": "noun", "v": "verb", "a": "adjective",
    "s": "adjective", "r": "adverb",
}


# ----------------------------------------------------------------------------
# wordnet wrapper — lazy import so tests don't pay the corpus-load cost
# unless they're actually exercising the dictionary path
# ----------------------------------------------------------------------------

_WN = None


def _wordnet():
    """Open the installed WordNet corpus on first lookup, without downloading."""
    global _WN
    if _WN is None:
        if not is_available():
            return None
        from nltk.corpus import wordnet as wn
        # Force corpus opening here so a broken installation is an honest miss,
        # not a teacher that appears available until its first request.
        wn.synsets("test")
        _WN = wn
    return _WN


def _nltk_data_roots() -> tuple[Path, ...]:
    """Resolve standard NLTK data directories without importing NLTK.

    Importing NLTK's WordNet reader during daemon boot eagerly builds several
    large in-memory indices. Availability is only a filesystem question here;
    the reader itself remains a first-lookup cost.
    """
    roots = [Path(p).expanduser() for p in os.environ.get("NLTK_DATA", "").split(os.pathsep) if p]
    home = Path.home()
    prefix = Path(sys.prefix)
    roots.extend((
        home / "nltk_data",
        prefix / "nltk_data",
        prefix / "share" / "nltk_data",
        prefix / "lib" / "nltk_data",
        Path("/usr/share/nltk_data"),
        Path("/usr/local/share/nltk_data"),
        Path("/usr/lib/nltk_data"),
        Path("/usr/local/lib/nltk_data"),
    ))
    # Preserve order while avoiding duplicate stat calls.
    return tuple(dict.fromkeys(roots))


def is_available() -> bool:
    """Cheap, side-effect-free probe for an installed WordNet corpus."""
    return any(
        (root / "corpora" / "wordnet").is_dir()
        or (root / "corpora" / "wordnet.zip").is_file()
        for root in _nltk_data_roots()
    )


# ----------------------------------------------------------------------------
# data shape
# ----------------------------------------------------------------------------

@dataclass
class Entry:
    """Compact view of one wordnet entry: best-sense definition plus all
    senses bundled so callers that want to expand can."""
    word: str
    pos: str                    # 'n', 'v', 'a', 'r'
    definition: str
    examples: list[str] = field(default_factory=list)
    synonyms: list[str] = field(default_factory=list)
    sense_count: int = 0
    parts_of_speech: list[str] = field(default_factory=list)


# ----------------------------------------------------------------------------
# lookup
# ----------------------------------------------------------------------------

def lookup(word: str) -> Entry | None:
    """Best WordNet entry for ``word``: prefer noun sense first (most
    questions are about WHAT a thing IS), then verb, then adjective.
    Underscore-normalises multi-word phrases ('black hole' →
    'black_hole') since that's how WordNet keys them."""
    from .acronym_expand import suppress_wordnet
    if suppress_wordnet(word):
        return None
    wn = _wordnet()
    if wn is None:
        return None
    candidates: list[str] = []

    def add(w: str) -> None:
        if w and w not in candidates:
            candidates.append(w)

    add(word.lower())
    add(word.lower().replace(" ", "_"))
    add(word.lower().replace("-", "_"))

    for cand in candidates:
        synsets = wn.synsets(cand)
        if not synsets:
            continue
        # prefer noun, then verb, then adjective, then adverb
        order = {"n": 0, "v": 1, "a": 2, "s": 2, "r": 3}
        synsets = sorted(synsets, key=lambda s: order.get(s.pos(), 9))
        first = synsets[0]
        parts_of_speech: list[str] = []
        for synset in synsets:
            category = _POS_NAMES.get(synset.pos(), synset.pos())
            if category not in parts_of_speech:
                parts_of_speech.append(category)
        synonyms: list[str] = []
        seen: set[str] = set()
        for lemma in first.lemmas():
            name = lemma.name().replace("_", " ")
            if name.lower() != cand.replace("_", " ").lower() \
                    and name not in seen:
                seen.add(name)
                synonyms.append(name)
        return Entry(
            word=cand.replace("_", " "),
            pos=first.pos(),
            definition=first.definition(),
            examples=list(first.examples())[:2],
            synonyms=synonyms[:5],
            sense_count=len(synsets),
            parts_of_speech=parts_of_speech,
        )
    return None


# ----------------------------------------------------------------------------
# entry → teach payload
# ----------------------------------------------------------------------------

def entry_to_answer(entry: Entry) -> str:
    """Plain-text rendering of a dictionary entry — the string the agent
    memoises + the user sees."""
    pos_label = _POS_NAMES.get(entry.pos, entry.pos)
    parts = [f"({pos_label}) {entry.definition}"]
    if entry.examples:
        parts.append(f"e.g. {entry.examples[0]}")
    if entry.synonyms:
        parts.append("synonyms: " + ", ".join(entry.synonyms))
    if entry.sense_count > 1:
        parts.append(f"+{entry.sense_count - 1} other senses")
    return "; ".join(parts)


def entry_to_payload(entry: Entry, subject: str,
                     microtheory: str = "dictionary",
                     genl_mt: str = "general_knowledge") -> dict:
    """``learn_from_teacher``-shaped payload — installs the subject as a
    predicate Frame in the dictionary Mt; capability returns the answer."""
    answer = entry_to_answer(entry)
    phrase = subject.lower().strip()
    return {
        "answer": answer,
        "learn": [{
            "phrase": phrase,
            "microtheory": microtheory,
            "genl_mt": genl_mt,
            "description": f"wordnet [{_POS_NAMES.get(entry.pos, entry.pos)}]",
            # Structured world evidence for graph-native lexical reasoning.
            # The graph must never recover POS by parsing the rendered gloss.
            "parts_of_speech": list(entry.parts_of_speech or [
                _POS_NAMES.get(entry.pos, entry.pos)]),
            "binding_pattern": "predicate_of_subject",
            "slot_name": "of",
            "source": "dictionary",
        }],
    }


# ----------------------------------------------------------------------------
# the callable
# ----------------------------------------------------------------------------

@dataclass
class DictionaryTeacher:
    """WordNet-backed lookup teacher.

    Cheapest link in the impasse-resolver chain: in-memory hash lookups
    + synset walk run in microseconds. Wire it as the agent's
    self-teacher with a ``WikiTeacher`` (or LLM) as the fallback, so the
    chain consults the dictionary first and falls through only on miss.

    Knobs:
      - ``microtheory`` — Mt newly-taught phrases land in (default
        ``dictionary`` under ``general_knowledge``).
      - ``fallback`` — optional second callable when wordnet has no
        match (proper nouns, jargon, novel concepts).
    """
    microtheory: str = "dictionary"
    genl_mt: str = "general_knowledge"
    fallback: Callable[[str], Any] | None = None
    # diagnostics
    hits: int = field(default=0, init=False)
    misses: int = field(default=0, init=False)
    last_subject: str | None = field(default=None, init=False)
    last_entry: Entry | None = field(default=None, init=False)

    def lookup(self, subject: str) -> Entry | None:
        return lookup(subject)

    def __call__(self, question_text: str) -> Any:
        subject = extract_subject(question_text)
        self.last_subject = subject
        entry = self.lookup(subject)
        if entry is None:
            self.misses += 1
            self.last_entry = None
            if self.fallback is not None:
                return self.fallback(question_text)
            return None
        self.hits += 1
        self.last_entry = entry
        return entry_to_payload(entry, subject=subject,
                                 microtheory=self.microtheory,
                                 genl_mt=self.genl_mt)


__all__ = [
    "DictionaryTeacher",
    "Entry",
    "entry_to_answer",
    "entry_to_payload",
    "is_available",
    "lookup",
]
