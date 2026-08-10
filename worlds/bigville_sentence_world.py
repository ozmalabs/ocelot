"""BigvilleSentenceWorld -- bigville R27 (block 315000): sentencing by collapse,
bounded by law.

Extends BigvilleJailWorld. On a guilty verdict the council DECIDES the custodial
term by collapse (sn_sentence) -- but the Argmax may only choose a SentenceLevel
inside the offence's statutory [min_term, max_term] (a SentenceLaw in the LawBook).
The chosen term feeds jl_imprison. No jail_term is prescribed on the charge; the
council sets it, within the law.

A WORLD ADAPTER. No sentence DECISION or clamping in Python -- sn_sentence is a seed
rule whose option set is the law. The adapter mints the sentence-law + candidate
levels, ticks, and reads.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.seed_loader import manifest_for                # noqa: E402
from worlds.bigville_jail_world import BigvilleJailWorld       # noqa: E402

_MAX_LEVEL = 14   # candidate SentenceLevel days 0.._MAX_LEVEL (covers any legal range within)


class BigvilleSentenceWorld(BigvilleJailWorld):
    def __init__(self):
        super().__init__()
        self.eng.load_seed_manifest(manifest_for("bigville_sentence"), None)
        for d in range(_MAX_LEVEL + 1):
            self.eng.add_node("SentenceLevel", {"days": float(d)})
        self._sentence_laws = {}   # offence -> SentenceLaw nid

    # ------------------------------------------------------------------ ingest
    def add_sentence_law(self, offence, *, min_term, max_term):
        """The statutory sentencing range for an offence -- lives in the LawBook, so
        the council can amend it."""
        law = self.eng.add_node("SentenceLaw", {"offence": offence,
                                                "min_term": float(min_term),
                                                "max_term": float(max_term),
                                                "status": "active"})
        self.eng.add_edge_unchecked(self._book, "has_sentence_law", law)
        self._sentence_laws[offence] = law
        return law

    def amend_sentence_law(self, offence, *, min_term=None, max_term=None):
        """Mechanically move a bound (stands in for a passed amendment bill)."""
        law = self._sentence_laws[offence]
        if min_term is not None:
            self.eng.set_attr(law, "min_term", float(min_term))
        if max_term is not None:
            self.eng.set_attr(law, "max_term", float(max_term))

    def prosecute(self, defendant, offence, *, evidence, penalty=5.0,
                  standing_penalty=1.0, threshold=2, base_days=0.0):
        """As the jail, but NO prescribed jail_term -- the council decides it within
        the law. base_days is the offence's baseline severity the council starts from."""
        charge = super().prosecute(defendant, offence, evidence=evidence, penalty=penalty,
                                   standing_penalty=standing_penalty, threshold=threshold,
                                   jail_term=0.0)
        self.eng.set_attr(charge, "base_days", float(base_days))
        return charge

    # ------------------------------------------------- glass-box read-offs
    def sentence_term(self, charge):
        return int(self.eng.node(charge)["attrs"].get("jail_term", 0.0))
