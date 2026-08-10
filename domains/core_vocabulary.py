"""Core vocabulary — top common English words as the agent's starting
lexicon.

Without a baseline vocabulary, the agent's produce() is bounded to a
handful of grammar/conversation/psychology signs and renders most
meanings empty. Pre-grounding the top ~1000 English content words from
Brown corpus + WordNet gives the agent a realistic working lexicon
from session one. Subsequent grounding via the dictionary/wiki/grammar
chain stacks on top; learn_sign dedupes by form so no work is
duplicated.

Source: NLTK Brown corpus (Francis & Kucera 1964, "A Standard Corpus of
Present-Day Edited American English"). Top N by raw frequency, filtered
through WordNet for definitions + part-of-speech. Words without a
WordNet entry (mostly function words already covered by grammar_teacher)
are skipped — no duplication, no garbage.

Each entry installs as a Concept node + a Sign in the agent's default
lexicon. The Sign's args are chosen by POS:

  noun       — standalone (no args)
  verb       — takes 'of'-marked right object
  adjective  — predicate over a left subject
  adverb     — standalone

Persistence: the signs live in the mind graph + round-trip through
CuriousAgent.save/load. The Mt named ``core_vocabulary`` is the marker;
re-running install_core_vocabulary is a no-op once it exists.

Cost: ~1 second on first install (1000 WordNet lookups + graph
mutations). Free thereafter.
"""
from __future__ import annotations

import functools


_CORE_VOCAB_MT = "core_vocabulary"
_DEFAULT_N = 1000


# ---------------------------------------------------------------------------
# frequency-ordered top N from Brown corpus
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=4)
def _top_n_words(n: int) -> tuple[str, ...]:
    """Return the top-``n`` lowercase alpha words from Brown corpus,
    ordered by raw frequency descending. Cached because the corpus
    iteration is the slow part."""
    from collections import Counter
    from nltk.corpus import brown
    try:
        brown.words()
    except LookupError:
        import nltk
        nltk.download("brown", quiet=True)
        from nltk.corpus import brown
    words = (w.lower() for w in brown.words()
              if w.isalpha() and len(w) > 1)
    return tuple(w for w, _ in Counter(words).most_common(n))


# ---------------------------------------------------------------------------
# sign args by part of speech
# ---------------------------------------------------------------------------

def _args_for_pos(pos: str) -> list:
    """Pick canonical sign-args by WordNet POS so produce() has a
    reasonable surface order. WordNet POS codes: n (noun), v (verb),
    a (adjective), s (satellite adjective), r (adverb)."""
    if pos == "v":
        # verb takes an 'of'-marked right object: "X verb of Y" → verb(of=Y)
        return [{"role": "of", "marker": "of", "dir": "R"}]
    if pos in ("a", "s"):
        # adjective is predicate over a left subject: "X is adj" → adj(arg=X)
        return [{"role": "arg", "dir": "L"}]
    # noun + adverb: standalone forms
    return []


# ---------------------------------------------------------------------------
# install
# ---------------------------------------------------------------------------

def install_core_vocabulary(agent, n: int = _DEFAULT_N,
                              force: bool = False) -> int:
    """Install Concept + Sign records for the top ``n`` Brown-corpus
    words, filtered through WordNet. Skips words WordNet doesn't
    cover (mostly function words; the grammar teacher already has
    those).

    Returns the count of newly-grounded signs (0 when already
    installed and ``force=False``).

    The Mt 'core_vocabulary' marks completion. Pass ``force=True`` to
    re-run (idempotent for already-present signs; learn_sign dedups
    by form)."""
    if (not force) and _mt_present(agent, _CORE_VOCAB_MT):
        return 0

    if not _mt_present(agent, _CORE_VOCAB_MT):
        agent.install_microtheory(
            _CORE_VOCAB_MT,
            description=(f"top {n} common English words from Brown corpus"),
            genl="general_knowledge")
    agent.operates_in(_CORE_VOCAB_MT)

    # WordNet lookup
    from nltk.corpus import wordnet as wn

    # Prefer noun → verb → adjective → adverb sense, matching what the
    # dictionary teacher does (most "what is X?" questions are nominal).
    pos_order = {"n": 0, "v": 1, "a": 2, "s": 2, "r": 3}

    installed = 0
    for word in _top_n_words(n):
        synsets = wn.synsets(word)
        if not synsets:
            continue
        synsets = sorted(synsets, key=lambda s: pos_order.get(s.pos(), 9))
        best = synsets[0]
        pos = best.pos()
        definition = best.definition()

        concept_name = word
        args = _args_for_pos(pos)
        desc = f"({pos}) {definition}"
        if hasattr(agent, "mind_substrate"):       # CuriousAgent host
            if concept_name not in agent._concept_nodes:
                with agent.mind_substrate.transform() as tx:
                    cid = tx.add_node("Concept",
                                      {"name": concept_name,
                                       "description": desc, "pos": pos})
                    agent._concept_nodes[concept_name] = cid
            sign: dict = {"form": word, "concept": concept_name}
            if args:
                sign["args"] = args
            agent.learn_sign(sign)
        else:                                      # WorldAdapter host
            agent._ensure_concept(concept_name, description=desc, pos=pos)
            agent.learn_sign(word, concept_name)
        installed += 1

    return installed


def _mt_present(agent, name: str) -> bool:
    """Is Microtheory `name` installed? Host-agnostic — CuriousAgent keeps a
    `_microtheory_nodes` index; the WorldAdapter answers via `microtheory()`."""
    idx = getattr(agent, "_microtheory_nodes", None)
    if idx is not None:
        return name in idx
    return agent.microtheory(name) is not None


def is_installed(agent) -> bool:
    """True iff core_vocabulary has been installed on this agent."""
    return _mt_present(agent, _CORE_VOCAB_MT)


__all__ = ["_CORE_VOCAB_MT", "_DEFAULT_N", "install_core_vocabulary",
            "is_installed"]
