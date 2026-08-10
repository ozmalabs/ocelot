"""THE LANGUAGE PRIOR — the agent's OWN lexicon + context, as a prior over
its OWN perceptual reading. The top-down half of reading.

Reading is PERCEPTION x CONTEXT — a Bayesian posterior:

    P(word | pixels) ∝ P(pixels | word) · P(word | context)
                       └─ the EYE (analysis-  └─ the LANGUAGE prior (this file)
                          by-synthesis match)

The eye-match (scripts/cursive_analysis_by_synthesis) reads each word in
ISOLATION — eyes only — and on ambiguous strokes it lands on a non-word
(`brown`->`brosc`, `jumps`->`juaqb`). A human reader never notices: their
LANGUAGE corrects it. "brosc" isn't a word; "the quick ___ fox" wants "brown".
This module supplies that correction — the cross-cortex feedback (language ->
vision), top-down — so the isolation-errors fix themselves.

THE PRIOR HAS TWO PARTS (both the agent's own language):

  · LEXICON — is the candidate a KNOWN word? A real word beats a non-word
    string (brosc/juaqb lose to brown/jumps). Plus PREFIX viability: during the
    left-to-right beam, a prefix that can still COMPLETE to a known word
    (`brow`-) is kept alive while a dead-end non-prefix (`bros`-, `juaq`-) is
    down-weighted — this is what lets the narrow beam RETAIN the true word.

  · CONTEXT — does the candidate fit the SURROUNDING read words? A bigram /
    phrase prior over the agent's known phrases: "he ___" wants "ran" (he ran
    >> he run), even though "run" is the commoner word in isolation. The
    neighbours constrain.

SOURCE — NOT an external language model. This is the agent's OWN vocabulary:
the Brown corpus (Francis & Kucera 1964) is exactly what domains/core_vocabulary
grounds the agent's starting lexicon from (top-N Brown words -> Concept + Sign).
We read the SAME corpus for word-membership + word-transition statistics. No
LLM, no neural language model, no Rust. Mechanical corpus statistics = the
likelihood's prior, supplied to the perceptual reader.

HONEST: the prior constrains WITHIN the agent's vocabulary / known context. A
genuinely out-of-lexicon novel word (e.g. `divisors`, not in Brown) has NO prior
to help — perception alone carries it, and that is named, not faked. Perception
stays PRIMARY: a clear confident read overrides a weak prior (we never let the
prior hallucinate over good pixels).
"""
from __future__ import annotations

import functools
import math


# ---------------------------------------------------------------------------
# THE AGENT'S VOCABULARY + CONTEXT STATISTICS — read from the SAME corpus
# domains/core_vocabulary grounds the lexicon from (Brown). Mechanical counts;
# no agent decision lives here — this is the prior the perceptual reader is
# scored by.
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=2)
def _brown_stats(min_len: int = 1):
    """Return (unigram Counter, bigram Counter, prefix set) over the Brown
    corpus — the agent's grounded-vocabulary source. Cached (the corpus pass
    is the slow part)."""
    from collections import Counter
    from nltk.corpus import brown
    from nltk import bigrams
    try:
        brown.words()
    except LookupError:  # pragma: no cover - first-run download
        import nltk
        nltk.download("brown", quiet=True)
        from nltk.corpus import brown

    ws = [w.lower() for w in brown.words() if w.isalpha() and len(w) >= min_len]
    uni = Counter(ws)
    bg = Counter(bigrams(ws))
    # every viable prefix of every known word — for prefix-survival in the beam.
    prefixes: set[str] = set()
    for w in uni:
        for i in range(1, len(w) + 1):
            prefixes.add(w[:i])
    return uni, bg, prefixes


class LanguagePrior:
    """The agent's own language as a prior over its own perceptual reads.

    Bayesian: posterior ∝ eye_likelihood · lexicon_prior · context_prior. All
    three are kept on a comparable [~0,1]-ish scale and COMBINED multiplicatively
    (in log space). Perception is PRIMARY — the prior weights are bounded so a
    confident clear read overrides a weak prior (no hallucination over good
    pixels)."""

    def __init__(self, min_len: int = 1,
                 lex_weight: float = 0.12,
                 ctx_weight: float = 0.10,
                 prefix_weight: float = 0.06,
                 nonword_floor: float = 0.55):
        self.uni, self.bg, self.prefixes = _brown_stats(min_len)
        self.total = sum(self.uni.values())
        self.vocab = set(self.uni)
        self.lex_weight = lex_weight      # pull toward known words at final scoring
        self.ctx_weight = ctx_weight      # pull toward context-fitting words
        self.prefix_weight = prefix_weight  # keep viable prefixes alive in the beam
        self.nonword_floor = nonword_floor  # a non-word is down-weighted, NOT zeroed
        self._maxuni = max(self.uni.values()) if self.uni else 1

    # -- LEXICON --------------------------------------------------------------
    def is_word(self, w: str) -> bool:
        return w in self.vocab

    def lexicon_factor(self, word: str) -> float:
        """Multiplicative prior from lexicon membership + word frequency. A
        known word -> >=1 (commoner words a touch higher); a NON-word -> a floor
        < 1 (down-weighted, not zeroed: perception can still win if confident)."""
        if word in self.vocab:
            # log-frequency bump in (0..1], so 'the' > 'fox' but both >= floor.
            f = self.uni[word] / self._maxuni
            return 1.0 + self.lex_weight * (0.3 + 0.7 * math.log1p(self.uni[word])
                                            / math.log1p(self._maxuni)) * (0.5 + 0.5 * f) ** 0
        return self.nonword_floor

    # -- PREFIX (beam survival) ----------------------------------------------
    def prefix_factor(self, prefix: str) -> float:
        """During the left-to-right beam, reward a prefix that can still COMPLETE
        to a known word and penalise a dead-end. This is what RETAINS the true
        word in a narrow beam (the eye alone prunes `brow`- before it finishes).
        A live word-prefix -> >1; a non-prefix -> a floor < 1."""
        if prefix in self.prefixes:
            # a completed word so far is even better than a mere live prefix.
            bonus = 1.0 + self.prefix_weight * (2.0 if prefix in self.vocab else 1.0)
            return bonus
        return 1.0 - self.prefix_weight

    # -- CONTEXT --------------------------------------------------------------
    def context_factor(self, word: str, prev: str | None) -> float:
        """Multiplicative prior from the PREVIOUS read word (a bigram / phrase
        prior over the agent's known phrases). "he ___" wants "ran" (he ran >>
        he run) even though "run" is commoner alone. Backs off to a neutral 1.0
        when there is no previous word or no signal."""
        if not prev or word not in self.vocab:
            return 1.0
        b = self.bg.get((prev, word), 0)
        if b == 0:
            return 1.0
        # P(word | prev), scaled into a bounded bump so context nudges, not
        # dominates (perception stays primary).
        pprev = self.uni.get(prev, 0)
        if pprev == 0:
            return 1.0
        cond = b / pprev
        return 1.0 + self.ctx_weight * min(1.0, math.log1p(b) / math.log(50)) \
            * (0.5 + 0.5 * min(1.0, cond * 5))

    # -- COMBINE --------------------------------------------------------------
    def posterior(self, eye: float, word: str, prev: str | None = None) -> float:
        """The Bayesian posterior score: eye-likelihood x lexicon x context.
        eye in ~[0,1] (the analysis-by-synthesis match). Returns the combined
        score the beam's final argmax uses."""
        return eye * self.lexicon_factor(word) * self.context_factor(word, prev)


__all__ = ["LanguagePrior"]
