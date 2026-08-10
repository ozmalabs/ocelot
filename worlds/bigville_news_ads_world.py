"""BigvilleNewsAdsWorld -- bigville R50 (block 361000): the newspaper is AD-SUPPORTED.

Advertisers pay the paper to run ads (the paper's revenue); ads reach the readership; and a
story that would damage a MAJOR advertiser is suppressed -- the ad-supported paper will not
bite the hand that feeds it (the advertiser analogue of patron capture).

A WORLD ADAPTER. No pay/print/see/suppress DECISION in Python -- na_* are seed rules. The
adapter mints the paper/advertisers/readers/stories, arms ad placement and reading, and reads.
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


class BigvilleNewsAdsWorld:
    def __init__(self, *, capture_threshold=5.0):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_news_ads"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville"})
        self._paper = self.eng.add_node("Paper", {"name": "The Bigville Gazette", "coin": 0.0,
                                                  "ad_revenue": 0.0, "capture_threshold": float(capture_threshold)})
        self.eng.add_edge_unchecked(self._town, "has_paper", self._paper)
        self._agents = {}
        self._stories = {}

    def _run(self):
        for _ in range(4):
            self.eng.force_all_dirty(); self.eng.run_rules(1000000)

    # ------------------------------------------------------------------ ingest
    def add_advertiser(self, name, *, coin=100.0, ad_spend=6.0):
        a = self.eng.add_node("Agent", {"name": name, "coin": float(coin), "ad_spend": float(ad_spend),
                                        "ad_armed": 0.0})
        self._agents[name] = a
        return a

    def place_ad(self, name):
        """The advertiser pays to run an ad (the paper's revenue)."""
        self.eng.add_edge_unchecked(self._agents[name], "advertises_in", self._paper)
        self.eng.set_attr(self._agents[name], "ad_armed", 1.0)
        self._run()

    def add_reader(self, name):
        r = self.eng.add_node("Agent", {"name": name})
        self.eng.add_edge_unchecked(self._town, "has_resident", r)
        self._agents[name] = r
        return r

    def read_paper(self, name):
        self.eng.add_edge_unchecked(self._agents[name], "reads", self._paper)
        self._run()

    def add_story(self, key, *, damages=None):
        """A story that (optionally) DAMAGES a named agent (e.g. an advertiser)."""
        s = self.eng.add_node("Story", {"key": key, "suppressed": 0.0})
        if damages is not None:
            self.eng.add_edge_unchecked(s, "damages", self._agents[damages])
        self._stories[key] = s
        self._run()
        return s

    # ------------------------------------------------- glass-box read-offs
    def paper_coin(self): return round(float(self.eng.node(self._paper)["attrs"]["coin"]), 4)
    def ad_revenue(self): return round(float(self.eng.node(self._paper)["attrs"]["ad_revenue"]), 4)
    def coin(self, name): return round(float(self.eng.node(self._agents[name])["attrs"].get("coin", 0.0)), 4)
    def ads_running(self): return len(self.eng.neighbours(self._paper, "runs"))
    def saw_ad(self, reader): return len(self.eng.neighbours(self._agents[reader], "saw")) > 0
    def is_suppressed(self, key): return float(self.eng.node(self._stories[key])["attrs"]["suppressed"]) == 1.0
