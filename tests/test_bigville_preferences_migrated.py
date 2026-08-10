"""bigville: NATURAL PREFERENCE DISTRIBUTIONS -- the researched reference a population is seeded from.

Innate preferences (taste, colour) are drawn per-person from population distributions grounded in real
research: bitter-taster status 25/50/25 (Bartoshuk, TAS2R38 -- VERIFIED via Wikipedia/Supertaster this
session), cilantro 'soapy' as an OR6A2 minority (Eriksson et al. 2012 -- VERIFIED), blue the most common
favourite colour (Eysenck 1941 + later; ordering robust, fractions approximate), sweet innately liked /
bitter innately rejected (Steiner). The individual varies; the DISTRIBUTION is the grounded fact.
"""
from __future__ import annotations

import os
import sys
from collections import Counter

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import domains.bigville_entities as E   # noqa: E402


# ------------------------------------------------------ G-distributions-are-well-formed + cited (data)
def test_the_distributions_are_well_formed_and_carry_their_provenance():
    assert abs(sum(E.COLOUR_PREFERENCE.values()) - 1.0) < 1e-9, "colour distribution is a probability"
    assert sum(E.BITTER_TASTER_STATUS.values()) == 1.0, "taster split is a probability"
    assert E.BITTER_TASTER_STATUS == {"non_taster": 0.25, "medium": 0.50, "supertaster": 0.25}, \
        "VERIFIED taster split (Bartoshuk / Supertaster) -- 25/50/25"
    # the seed carries its own citations, with VERIFIED vs APPROX flagged honestly
    assert "TAS2R38" in E.PREFERENCE_RESEARCH["bitter_taster"] and "VERIFIED" in E.PREFERENCE_RESEARCH["bitter_taster"]
    assert "OR6A2" in E.PREFERENCE_RESEARCH["cilantro_soapy"]
    assert "APPROX" in E.PREFERENCE_RESEARCH["colour_blue_first"], "colour fractions are honestly flagged approximate"


# ------------------------------------------------------ G-research-ordering-holds (headline)
def test_the_means_follow_the_research_direction():
    assert max(E.COLOUR_PREFERENCE, key=E.COLOUR_PREFERENCE.get) == "blue", "blue is the most common favourite"
    assert E.TASTE_PREFERENCE["sweet"]["mean"] > E.TASTE_PREFERENCE["bitter"]["mean"], "sweet liked, bitter rejected"
    assert E.BITTER_LIKING_BY_STATUS["supertaster"] < E.BITTER_LIKING_BY_STATUS["non_taster"], \
        "a supertaster is far more averse to bitter than a non-taster"
    assert 0.0 < E.CILANTRO_SOAPY_FRACTION < 0.5, "cilantro 'soapy' is a minority (OR6A2)"


# ------------------------------------------------------ G-population-reproduces-the-distribution (headline)
def test_a_drawn_population_reproduces_the_researched_distribution():
    rng = np.random.default_rng(20260801)
    pop = [E.draw_person_preferences(rng) for _ in range(4000)]
    status = Counter(p["bitter_status"] for p in pop)
    assert abs(status["supertaster"] / 4000 - 0.25) < 0.03, "~25% supertasters (the verified split)"
    col = Counter(p["favourite_colour"] for p in pop)
    assert col.most_common(1)[0][0] == "blue", "blue comes out the most common favourite colour"
    sweet = np.mean([p["taste"]["sweet"] for p in pop]); bitter = np.mean([p["taste"]["bitter"] for p in pop])
    assert sweet > bitter + 0.2, "the population likes sweet far more than bitter"
    bit_sup = np.mean([p["taste"]["bitter"] for p in pop if p["bitter_status"] == "supertaster"])
    bit_non = np.mean([p["taste"]["bitter"] for p in pop if p["bitter_status"] == "non_taster"])
    assert bit_sup < bit_non - 0.2, "supertasters dislike bitter much more than non-tasters (the taster axis bites)"
    soapy = np.mean([p["cilantro_soapy"] for p in pop])
    assert abs(soapy - E.CILANTRO_SOAPY_FRACTION) < 0.03, "the cilantro-soapy minority reproduces"


# ------------------------------------------------------ G-monotony-wears-out-pleasure (headline)
def test_eating_the_same_food_wears_out_its_pleasure_variety_renews_it():
    likings = {"bread": 0.7, "fish": 0.7}
    same = E.simulate_diet(["bread"] * 5, likings, neophobia=0.3)
    assert all(same[i] > same[i + 1] for i in range(4)), "sensory-specific satiety: the same food declines each meal"
    varied = E.simulate_diet(["bread", "fish", "bread", "fish"], likings, neophobia=0.3)
    assert all(abs(s - 0.7) < 1e-9 for s in varied), "variety renews the pleasure -- every meal is fresh"


# ------------------------------------------------------ G-the-trait-modulates-monotony (headline)
def test_a_routine_lover_tolerates_monotony_a_variety_seeker_suffers():
    likings = {"bread": 0.7}
    seeker = E.simulate_diet(["bread"] * 5, likings, neophobia=0.1)     # variety-seeker
    lover = E.simulate_diet(["bread"] * 5, likings, neophobia=0.8)      # routine-lover
    assert seeker[-1] < lover[-1] - 0.15, "the variety-seeker's pleasure collapses; the routine-lover barely dips"


# ------------------------------------------------------ G-poverty-x-trait (headline)
def test_a_monotonous_poor_diet_costs_the_variety_seeking_poor_the_most():
    import numpy as np
    likings = {"bread": 0.7, "fish": 0.7, "ale": 0.7, "cheese": 0.7}
    poor, rich = ["bread"] * 6, ["bread", "fish", "ale", "cheese", "bread", "fish"]
    poor_seeker = np.mean(E.simulate_diet(poor, likings, 0.1))
    poor_lover = np.mean(E.simulate_diet(poor, likings, 0.8))
    rich_seeker = np.mean(E.simulate_diet(rich, likings, 0.1))
    assert poor_seeker < poor_lover, "on the same poor monotonous diet, the variety-seeker is worse off"
    assert poor_seeker < rich_seeker - 0.2, "and far worse off than if he could afford variety -- the welfare cost of poverty's monotony"


# ------------------------------------------------------ G-mere-exposure-and-novelty (headline)
def test_familiarity_builds_liking_and_neophobia_shifts_novelty():
    grow = [E.mere_exposure_liking(0.4, n) for n in range(6)]
    assert all(grow[i] < grow[i + 1] for i in range(5)) and grow[-1] > grow[0], "a new food grows on you (mere exposure)"
    neophilic = E.meal_satisfaction(0.5, 0, 0.1, novel=True)
    neophobic = E.meal_satisfaction(0.5, 0, 0.8, novel=True)
    assert neophilic > neophobic, "a variety-seeker enjoys a novel dish; a routine-lover is wary of it"


# ------------------------------------------------------ G-neophobia-is-a-drawn-trait (data)
def test_food_neophobia_is_a_drawn_population_trait():
    import numpy as np
    rng = np.random.default_rng(11)
    pop = [E.draw_person_preferences(rng)["food_neophobia"] for _ in range(3000)]
    assert 0.0 <= min(pop) and max(pop) <= 1.0, "a bounded 0..1 trait"
    assert abs(float(np.mean(pop)) - E.FOOD_NEOPHOBIA["mean"]) < 0.03, "reproduces the population mean neophobia"
    assert float(np.std(pop)) > 0.1, "and real spread -- routine-lovers AND variety-seekers, not clones"


# ------------------------------------------------------ G-deterministic (glass-box)
def test_the_draw_is_deterministic_in_the_seed():
    a = E.draw_person_preferences(np.random.default_rng(7))
    b = E.draw_person_preferences(np.random.default_rng(7))
    assert a == b, "same seed -> same person (a distribution over seeds, not hidden randomness)"
