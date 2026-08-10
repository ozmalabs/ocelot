"""bigville copyfitting reworked (blocks 298000-299000) -- writing to length is
importance-weighted ALLOCATION, and distortion is a first-class OWNED behavior on
THREE orthogonal axes (veracity x relevance x informativeness).

Supersedes the packer. The budget sets the plan top-down; a priority waterfall
allocates depth by importance; the length EMERGES (no total-length loop, len() is
only a ruler). Under fill-pressure the writer's dispositions decide the 4-way fork
(run short / pad truisms / pad the irrelevant-true cats / fabricate); every
printed clause carries three tags measured against the ground truth we own. Gates
mirror BIGVILLE_COLUMN_ALLOC_PREREG.md.
"""
from __future__ import annotations

import json
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_column_world import BigvilleColumnWorld       # noqa: E402

# --- one fixed held story: core beats (the eviction) + a tagged padding pool ---
LEAD = ("The Hendersons", "were evicted from their Elm Street home",
        "after the mill shut in March", "ending sixty years of steady work", 100, 0)
CORE = [
    ("The landlord", "filed the eviction notice", "citing three months of unpaid rent",
     "left owing after the closure took their wages", 90, 1),
    ("A relief fund", "opened at the church", "to house the family this winter",
     "with donations gathered from the parish", 80, 2),
    ("The council", "will hear the case", "at its meeting on Tuesday",
     "where affected tenants may speak", 70, 3),
]
# padding pool -- each candidate tagged (veracity, relevance, informativeness) in {0,1,2}
PADS = [
    # the CATS: true + informative but IRRELEVANT (relevance 0)
    dict(pre="The Johnsons next door keep two orange cats", veracity=2, relevance=0, informativeness=2, pos=10),
    dict(pre="The family were long admired for their fine garden", veracity=2, relevance=0, informativeness=2, pos=11),
    # TRUISMS: true + on-topic but ZERO residual (informativeness 0)
    dict(pre="It was, by any measure, a difficult time for the family", veracity=2, relevance=2, informativeness=0, pos=12),
    dict(pre="Housing, after all, is a matter that touches everyone", veracity=2, relevance=2, informativeness=0, pos=13),
    # FABRICATED color: invented (veracity 0) but on-topic + informative-seeming
    dict(pre="Sources say the landlord smirked as the family left", veracity=0, relevance=2, informativeness=2, pos=14),
    dict(pre="Insiders whisper that darker motives were at play", veracity=0, relevance=2, informativeness=2, pos=15),
    # INFERRED core color: plausible, consistent, not itself held (veracity 1)
    dict(pre="Neighbours were said to be shocked by the news", veracity=1, relevance=2, informativeness=1, pos=16),
]


def _plant(w, *, pads=True):
    s, p, m, t, imp, po = LEAD
    w.add_beat(s, p, m, t, importance=imp, pos=po, is_lead=True)
    for s, p, m, t, imp, po in CORE:
        w.add_beat(s, p, m, t, importance=imp, pos=po)
    if pads:
        for d in PADS:
            w.add_pad(**d)
    return w


def _coremax():
    """Length of the full core article (all beats at d2, disciplined writer)."""
    w = BigvilleColumnWorld(100000, honesty=1, focus=1, substance=1)
    _plant(w, pads=False)
    w.run()
    L = w.length()
    w.close()
    return L


# ============================ Part A: allocation ============================

def test_importance_allocated():
    """G-importance-allocated: two beats of IDENTICAL held content but different
    importance -> the more important gets depth >= the less important; swapping
    their importances swaps their depths."""
    def two(impA, impB):
        w = BigvilleColumnWorld(120, honesty=1, focus=1, substance=1)
        a = w.add_beat("Alpha news", "happened today", "with a middling clause here",
                       "and a longer elaboration tail here", importance=impA, pos=0)
        b = w.add_beat("Alpha news", "happened today", "with a middling clause here",
                       "and a longer elaboration tail here", importance=impB, pos=1)
        w.run()
        return w, a, b
    w, a, b = two(90, 10)
    assert w.beat_depth(a) >= w.beat_depth(b), (w.beat_depth(a), w.beat_depth(b))
    da, db = w.beat_depth(a), w.beat_depth(b)
    w.close()
    w, a, b = two(10, 90)                       # swap importance
    assert w.beat_depth(b) >= w.beat_depth(a), (w.beat_depth(a), w.beat_depth(b))
    assert (w.beat_depth(b), w.beat_depth(a)) == (da, db), "depths did not swap with importance"
    w.close()


def test_spent_where_it_matters():
    """G-spent-where-it-matters (the discriminator vs the packer): remove the top
    beat and its freed budget flows to the NEXT-most-important beat, which DEEPENS
    -- not spread evenly, not to a minor beat."""
    def story(with_top, budget):
        w = BigvilleColumnWorld(budget, honesty=1, focus=1, substance=1)
        ids = {}
        beats = [("TOP", 100), ("SECOND", 90), ("THIRD", 80), ("MINOR", 10)]
        for nm, imp in beats:
            if nm == "TOP" and not with_top:
                continue
            ids[nm] = w.add_beat(nm + " had", "a development", "with a middle clause of length",
                                 "and an elaboration tail of length", importance=imp, pos=len(ids))
        w.run()
        return w, ids
    budget = 150
    w1, i1 = story(True, budget)
    sec_with, minor_with = w1.beat_depth(i1["SECOND"]), w1.beat_depth(i1["MINOR"])
    w1.close()
    w2, i2 = story(False, budget)
    sec_wo, minor_wo = w2.beat_depth(i2["SECOND"]), w2.beat_depth(i2["MINOR"])
    w2.close()
    assert sec_wo > sec_with, f"the next-most-important beat did not deepen: {sec_with}->{sec_wo}"
    assert (minor_wo - minor_with) <= (sec_wo - sec_with), \
        "the freed budget spread to a minor beat rather than the next-most-important"


def test_emergent_length_no_correction_loop():
    """G-emergent-length: composed length == sum of printed clause lengths +
    separators, and the adapter has NO total-length correction (no while loop, no
    residual, no budget-vs-length comparison in Python)."""
    w = BigvilleColumnWorld(300, honesty=1, focus=1, substance=1)
    _plant(w)
    w.run()
    cs = w._printed_clauses()
    expect = sum(len(c["text"]) for c in cs) + max(0, len(cs) - 1)
    assert w.length() == expect, (w.length(), expect)
    w.close()
    src = open(os.path.join(_ROOT, "worlds", "bigville_column_world.py")).read()
    assert not re.search(r"\bwhile\b", src), "adapter must not loop toward a target length"
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match(", "_apply("):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    assert ".format(" not in src and not re.search(r'''\bf["']''', src), \
        "adapter must not build prose via .format/f-string"
    # the adapter never compares a length to the budget (allocation does, in rules)
    assert not re.search(r"(len\(|length\(\)|_len)\s*[<>]=?\s*.*budget", src)
    assert not re.search(r"budget\w*\s*[<>]=?\s*(len|length)", src)


# ======================= Part B: three owned quality axes =======================

def test_three_axes_tracked():
    """G-three-axes-tracked: every printed clause carries a veracity, relevance and
    informativeness tag; nothing printed is untracked; the adapter computes all
    three rates + net_information."""
    w = BigvilleColumnWorld(_coremax() + 200, honesty=0, focus=0, substance=0)  # pads freely
    _plant(w)
    w.run()
    for c in w._printed_clauses():
        assert c["tracked"], f"untracked clause printed: {c['text']!r}"
        assert c["veracity"] in ("held", "inferred", "fabricated")
        assert c["relevance"] in ("core", "tangential", "irrelevant")
        assert c["i_num"] in (0.0, 1.0, 2.0)
    m = w.metrics()
    assert m["all_tracked"] and "net_information" in m and "veracity_rate" in m
    w.close()


def test_four_resolutions_each_drops_one_axis():
    """G-four-resolutions: SAME story, over-large budget -> the four dispositions
    give run-short / truisms / cats / fabrication, each a drop on EXACTLY ONE axis
    (the other two intact)."""
    B = _coremax() + 200
    def arm(h, f, s):
        w = BigvilleColumnWorld(B, honesty=h, focus=f, substance=s)
        _plant(w)
        w.run()
        m = w.metrics()
        m["cats"] = w.contains("orange cats")
        m["truism"] = w.contains("difficult time")
        m["fab"] = w.contains("smirked") or w.contains("darker motives")
        w.close()
        return m
    short = arm(1, 1, 1)
    trus = arm(1, 1, 0)
    cats = arm(1, 0, 1)
    fabd = arm(0, 1, 1)
    # run short: under-fills, no padding of any kind, all axes maxed
    assert short["length"] < B and not (short["cats"] or short["truism"] or short["fab"])
    assert short["veracity_rate"] == 1.0 and short["relevance_rate"] == 1.0 and short["mean_informativeness"] == 2.0
    # low substance -> truisms: informativeness drops, veracity+relevance intact
    assert trus["truism"] and not trus["cats"] and not trus["fab"]
    assert trus["mean_informativeness"] < short["mean_informativeness"]
    assert trus["veracity_rate"] == 1.0 and trus["relevance_rate"] == 1.0
    # low focus -> cats: relevance drops, veracity+informativeness intact
    assert cats["cats"] and not cats["truism"] and not cats["fab"]
    assert cats["relevance_rate"] < short["relevance_rate"]
    assert cats["veracity_rate"] == 1.0 and cats["mean_informativeness"] == 2.0
    # low honesty -> fabrication: veracity drops, relevance+informativeness intact
    assert fabd["fab"] and not fabd["cats"] and not fabd["truism"]
    assert fabd["fabricated_share"] > 0.0 and fabd["veracity_rate"] < 1.0
    assert fabd["relevance_rate"] == 1.0 and fabd["mean_informativeness"] == 2.0


def test_orange_cats_caught_only_by_relevance():
    """G-orange-cats: a low-focus padder pulls in the true-but-irrelevant cats; a
    veracity+informativeness check PASSES the article (no fabrication, high info)
    while only the RELEVANCE axis fails it. The cats are absent in the disciplined
    article."""
    B = _coremax() + 200
    lazy = BigvilleColumnWorld(B, honesty=1, focus=0, substance=1); _plant(lazy); lazy.run()
    tidy = BigvilleColumnWorld(B, honesty=1, focus=1, substance=1); _plant(tidy); tidy.run()
    assert lazy.contains("orange cats") and not tidy.contains("orange cats")
    ml = lazy.metrics()
    # a veracity+informativeness-only check waves it through:
    assert ml["veracity_rate"] == 1.0 and ml["mean_informativeness"] == 2.0
    # only the relevance axis catches it:
    assert ml["relevance_rate"] < 1.0 and ml["irrelevant_share"] > 0.0
    lazy.close(); tidy.close()


def test_truisms_caught_only_by_informativeness():
    """G-truism-padding: a low-substance padder pulls in zero-residual truisms; a
    veracity+relevance check PASSES the article while only the INFORMATIVENESS axis
    fails it -- and net_information stays at the core-only total (padding adds 0),
    the Salvor-Hardin 'said nothing, and said it very well'."""
    B = _coremax() + 200
    core_only = BigvilleColumnWorld(B, honesty=1, focus=1, substance=1); _plant(core_only); core_only.run()
    net_core = core_only.metrics()["net_information"]; core_only.close()

    vac = BigvilleColumnWorld(B, honesty=1, focus=1, substance=0); _plant(vac); vac.run()
    tidy = BigvilleColumnWorld(B, honesty=1, focus=1, substance=1); _plant(tidy); tidy.run()
    assert vac.contains("difficult time") and not tidy.contains("difficult time")
    m = vac.metrics()
    # a veracity+relevance-only check waves it through:
    assert m["veracity_rate"] == 1.0 and m["relevance_rate"] == 1.0
    # only informativeness catches it: mean drops AND net_information stays at core
    assert m["mean_informativeness"] < 2.0
    assert m["net_information"] == net_core, (m["net_information"], net_core)
    assert vac.length() > tidy.length(), "the truism-padder should be longer (padded)"
    vac.close(); tidy.close()


def test_veracity_gradient():
    """G-veracity-gradient: sweeping honesty moves the veracity DISTRIBUTION
    (held->inferred->fabricated), not a binary flip; fabricated share is
    monotonically non-increasing in honesty. (focus/substance low so the honesty
    floor is the only gate.)"""
    B = _coremax() + 200
    rows = []
    for h in (1.0, 0.6, 0.5, 0.2, 0.0):
        w = BigvilleColumnWorld(B, honesty=h, focus=0, substance=0)
        _plant(w)
        w.run()
        m = w.metrics()
        rows.append((h, m["fabricated_share"], w.contains("shocked")))  # inferred clause
        w.close()
    fab = [r[1] for r in rows]
    for a, b in zip(fab, fab[1:]):
        assert b >= a - 1e-9, f"fabricated share not monotone in honesty: {rows}"
    assert fab[0] == 0.0 and fab[-1] > 0.0, rows            # high honesty none; low some
    assert any(r[2] for r in rows if 0.4 <= r[0] <= 0.6), "inferred never appears at mid honesty"


def test_capture_fabricates_directed():
    """G-capture-fabricates-directed: a captured paper's fabricated clauses are
    exculpatory toward the patron (name present), not random."""
    w = BigvilleColumnWorld(500, honesty=1, focus=1, substance=1,
                            captured=1, patron="John Scrooge")
    w.add_beat("The Hendersons", "were evicted", "from their Elm Street home",
               "after the mill shut", importance=100, pos=0, is_lead=True)
    w.add_pad("No wrongdoing by", post="was ever established", veracity=0,
              relevance=2, informativeness=1, pos=10, exculpatory=True)
    w.run()
    assert w.contains("John Scrooge"), w.article_text()
    printed = [c for c in w._printed_clauses() if c["v_num"] == 0.0]
    assert printed and all("John Scrooge" in c["text"] for c in printed), \
        "captured fabrication must be directed at the patron"
    w.close()


def test_untracked_falsifier_fails_the_tracked_gate():
    """G-falsifier: an untracked printed clause (no tags,
    bigville_column_alloc_lorem.json) MUST fail G-three-axes-tracked -- the
    glass-box requires distortion be OWNED, not absent."""
    w = BigvilleColumnWorld(500, honesty=1, focus=1, substance=1, lorem=True)
    w.add_beat("The Hendersons", "were evicted", "from Elm Street",
               "after the mill shut", importance=100, pos=0, is_lead=True)
    w.run()
    assert w.contains("lorem ipsum"), "the untracked control did not print"
    assert not w.metrics()["all_tracked"], "an untracked clause slipped the tracked gate"
    w.close()
    # and the SOUND writer on the same content is fully tracked
    w2 = BigvilleColumnWorld(500, honesty=1, focus=1, substance=1)
    w2.add_beat("The Hendersons", "were evicted", "from Elm Street",
                "after the mill shut", importance=100, pos=0, is_lead=True)
    w2.run()
    assert w2.metrics()["all_tracked"]
    w2.close()


# ==================== consequences of allocation (A) ====================

def test_fit_within_budget_lead_survives():
    """G-fit: a budget below the full core article -> length <= budget and the
    LEAD survives (highest importance, gets at least d0)."""
    full = _coremax()
    for budget in (int(full * 0.75), int(full * 0.5), int(full * 0.35)):
        w = BigvilleColumnWorld(budget, honesty=1, focus=1, substance=1)
        _plant(w, pads=False)
        w.run()
        assert w.length() <= budget, (budget, w.length())
        lead = w.lead_text()
        assert lead and lead in w.article_text(), f"lead cut at budget={budget}"
        w.close()


def test_sweep_core_length_tracks_budget_monotonically():
    """G-sweep: core held length is non-decreasing in budget (a disciplined writer,
    no padding)."""
    full = _coremax()
    curve = []
    for budget in range(60, full + 120, 40):
        w = BigvilleColumnWorld(budget, honesty=1, focus=1, substance=1)
        _plant(w, pads=False)
        w.run()
        curve.append((budget, w.length()))
        w.close()
    print("\ncore length-vs-budget:", curve)
    lengths = [L for _, L in curve]
    for a, b in zip(lengths, lengths[1:]):
        assert b >= a - 1e-9, f"length decreased as budget grew: {curve}"
    assert lengths[-1] > lengths[0]


# ------------------------------------------------- report aids (not gates)

def test_report_three_axis_table_and_narrower_checks():
    """Prints the three-axis clause table under the four dispositions and the three
    'looks fine on a narrower check' demonstrations."""
    B = _coremax() + 200
    for name, (h, f, s) in [("HONEST+FOCUSED+SUBSTANTIVE (runs short)", (1, 1, 1)),
                            ("LOW SUBSTANCE (pads truisms)", (1, 1, 0)),
                            ("LOW FOCUS (pads cats)", (1, 0, 1)),
                            ("LOW HONESTY (fabricates)", (0, 1, 1))]:
        w = BigvilleColumnWorld(B, honesty=h, focus=f, substance=s)
        _plant(w)
        w.run()
        m = w.metrics()
        print(f"\n--- {name}  (budget={B}, length={m['length']}) ---")
        for pos, prov, v, r, i, text in w.clause_table():
            print(f"   [{v:9s}|{r:10s}|info{int(i)}] {text}")
        print(f"   SUMMARY: veracity_rate={m['veracity_rate']:.2f} "
              f"relevance_rate={m['relevance_rate']:.2f} "
              f"mean_info={m['mean_informativeness']:.2f} net_information={m['net_information']:.0f}")
        w.close()
    assert True
