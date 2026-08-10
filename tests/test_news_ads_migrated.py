"""bigville R50 (block 361000): the newspaper is AD-SUPPORTED. Advertisers pay the paper to run
ads (its revenue); ads reach readers; a story harming a MAJOR advertiser is suppressed (the
paper will not bite the hand that feeds it -- the advertiser analogue of patron capture).
Gates mirror the seed description.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_news_ads_world import BigvilleNewsAdsWorld as News   # noqa: E402


# ------------------------------------------------------ G-ad-supported-revenue (headline)
def test_advertisers_fund_the_paper_and_coin_is_conserved():
    w = News()
    w.add_advertiser("Brewer", coin=100.0, ad_spend=6.0)
    w.add_advertiser("Baker", coin=100.0, ad_spend=3.0)
    w.place_ad("Brewer"); w.place_ad("Baker")
    assert w.paper_coin() == 9.0 and w.ad_revenue() == 9.0, "ad revenue IS the paper's income (6 + 3)"
    assert w.coin("Brewer") == 94.0 and w.coin("Baker") == 97.0, "advertisers paid for their ads"
    assert round((100 - w.coin("Brewer")) + (100 - w.coin("Baker")) - w.paper_coin(), 6) == 0.0, \
        "coin is conserved -- the paper's money came from the advertisers"
    assert w.ads_running() == 2


# ------------------------------------------------------ G-ads-reach-readers
def test_ads_reach_the_readership():
    w = News()
    w.add_advertiser("Brewer", coin=100.0, ad_spend=6.0); w.place_ad("Brewer")
    w.add_reader("Reader")
    assert not w.saw_ad("Reader"), "before reading, the reader has not seen the ad"
    w.read_paper("Reader")
    assert w.saw_ad("Reader"), "a reader of the paper sees the ad it runs"


# ------------------------------------------------------ G-advertiser-capture (headline)
def test_the_paper_will_not_bite_the_hand_that_feeds_it():
    w = News(capture_threshold=5.0)
    w.add_advertiser("Brewer", coin=100.0, ad_spend=6.0)   # major (>= 5)
    w.add_advertiser("Baker", coin=100.0, ad_spend=3.0)    # minor (< 5)
    w.place_ad("Brewer"); w.place_ad("Baker")
    w.add_story("brewer_waters_the_ale", damages="Brewer")
    w.add_story("baker_shortweights", damages="Baker")
    w.add_story("mayor_corruption", damages=None)
    assert w.is_suppressed("brewer_waters_the_ale"), "a story harming a MAJOR advertiser is suppressed"
    assert not w.is_suppressed("baker_shortweights"), "a story harming a MINOR advertiser prints"
    assert not w.is_suppressed("mayor_corruption"), "a story harming a non-advertiser prints freely"


# ------------------------------------------------------ G-capture-off (falsifier)
def test_below_the_threshold_the_story_prints():
    w = News(capture_threshold=10.0)                        # nobody spends enough to capture
    w.add_advertiser("Brewer", coin=100.0, ad_spend=6.0); w.place_ad("Brewer")
    w.add_story("brewer_waters_the_ale", damages="Brewer")
    assert not w.is_suppressed("brewer_waters_the_ale"), \
        "when no advertiser is major enough to capture, the damaging story prints"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_the_ad_business():
    src = open(os.path.join(_ROOT, "worlds", "bigville_news_ads_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_news_ads.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"na_place_ad", "na_see_ad", "na_advertiser_capture"} <= names, names
    cap = json.dumps([r for r in seed["rules"] if r["name"] == "na_advertiser_capture"][0])
    assert "capture_threshold" in cap and "damages" in cap and "suppressed" in cap, \
        "capture keys off a major advertiser being damaged"
