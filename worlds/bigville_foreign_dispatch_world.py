"""BigvilleForeignDispatchWorld -- bigville R28 (block 316000): Word from Giantville
in the paper.

Connects the 259000 wider-world news (a traveller brings a NewsItem about
Giantville; the publisher forms a GiantvilleBelief via bw_news_secondhand,
confidence = the teller's credibility) to the 293000+ newspaper writer: the paper
prints a foreign_dispatch Story rendered by StringConcat, hedged by the belief's
credibility (provenance becomes word choice). With no traveller, no belief forms
and the paper carries no Giantville news (unknown = absence).

A WORLD ADAPTER. No belief/render DECISION in Python -- bw_news_secondhand and the
fd_write_* rules do it. The adapter mints the paper/publisher/traveller/news, ticks,
and reads the printed stories.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs                                     # noqa: E402
from substrate.seed_loader import manifest_for          # noqa: E402


class BigvilleForeignDispatchWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_world_news"), None)
        self.eng.load_seed_manifest(manifest_for("bigville_foreign_dispatch"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville"})
        self._paper = self.eng.add_node("Paper", {"name": "The Bigville Times"})
        self.eng.add_edge_unchecked(self._town, "has_paper", self._paper)
        self._pub = self.eng.add_node("Person", {"name": "Publisher", "comprehend_armed": 1.0})
        self.eng.add_edge_unchecked(self._paper, "employs", self._pub)
        self._giantville = self.eng.add_node("Place", {"name": "Giantville", "place_id": 1.0})
        self._travellers = 0

    # ------------------------------------------------------------------ ingest
    def bring_news(self, content, *, credibility):
        """A traveller arrives and tells the publisher a NewsItem about Giantville.
        credibility>=0.75 -> the paper prints it confirmed; below -> hedged hearsay."""
        self._travellers += 1
        trav = self.eng.add_node("Traveller", {"name": f"Traveller{self._travellers}",
                                               "credibility": float(credibility)})
        news = self.eng.add_node("NewsItem", {"content": content, "credibility": float(credibility)})
        self.eng.add_edge_unchecked(news, "about", self._giantville)
        self.eng.add_edge_unchecked(trav, "brings_news", news)
        self.eng.set_attr(self._pub, "comprehend_armed", 1.0)   # the publisher listens
        self.eng.add_edge_unchecked(self._pub, "hears", news)   # the traveller tells him
        return news

    # ------------------------------------------------------------------ run
    def run(self):
        self.eng.force_all_dirty()
        return self.eng.run_rules(1000000)

    # ------------------------------------------------- glass-box read-offs
    def dispatches(self):
        """The foreign-dispatch stories the paper has printed."""
        out = []
        for st in self.eng.neighbours(self._paper, "prints"):
            a = self.eng.node(st)["attrs"]
            if a.get("kind") == "foreign_dispatch":
                out.append(a.get("text"))
        return out

    def belief_confidence(self):
        for blf in self.eng.neighbours(self._pub, "giantville_belief"):
            return float(self.eng.node(blf)["attrs"].get("confidence", 0.0))
        return None
