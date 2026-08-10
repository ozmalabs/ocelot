"""bigville: the BODY layer -- World -> Body -> Mind.

A villager is a MIND that HAS a BODY. Physiology (health, mood, satiety, the palate) lives on a Body
node the mind `has_body`, NOT on the mind itself. The three layers are distinct and the flow runs one
way and back:

  * World -> Body : a world event (a meal) acts on the body -- a spoiled meal harms the body's HEALTH
                    (bd_meal_health) and moves its MOOD (af_meal_mood). By rule, not by mind decision.
  * Body -> Mind : the mind READS the body's state -- the choice collapse (nd_choose_good) weighs the
                    body's SATIETY as appetite ('what do I feel like'), via the has_body edge.
  * Mind : the mind's own cognition -- beliefs (holds_belief), preferences, the choice -- is separate
           from the body's physiology. The one spoiled meal drives BOTH: the body's health AND a mind
           belief, each on its own node.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_need_world import BigvilleNeedWorld, APPLE, BREAD, SUSTENANCE   # noqa: E402

SQUARE = (14, 8)
BAKERY = (14, 11)
ALEHOUSE = (17, 8)


# ------------------------------------------------------ G-a-mind-has-a-body (structure)
def test_a_villager_is_a_mind_that_has_a_distinct_body():
    w = BigvilleNeedWorld()
    m = w.add_mover("H", SQUARE)
    bodies = list(w.eng.neighbours(m, "has_body"))
    assert len(bodies) == 1, "the mind HAS exactly one body (has_body)"
    body = bodies[0]
    assert body != m, "the body is a DISTINCT node from the mind"
    ba = w.eng.node(body)["attrs"]
    assert "health" in ba and "mood" in ba and "satiety" in ba, "physiology lives on the body"


# ------------------------------------------------------ G-world-acts-on-the-body (headline)
def test_a_spoiled_meal_harms_the_body_a_fresh_one_does_not():
    w = BigvilleNeedWorld(); w.add_mover("H", SQUARE)
    assert w.body_state("H")["health"] == 1.0, "the body starts whole"
    w.eat("H", 0.2)                                   # a badly spoiled good
    assert w.body_state("H")["health"] < 0.8, "eating a spoiled good harms the body's health (World -> Body)"
    # a fresh meal is no injury
    v = BigvilleNeedWorld(); v.add_mover("H", SQUARE)
    v.eat("H", 1.0)
    assert v.body_state("H")["health"] == 1.0, "a fresh good leaves the body whole -- the harm scales with the rot"


def test_the_body_health_dynamic_is_a_seed_rule_not_python():
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_body.json")))
    r = next(x for x in seed["rules"] if x["name"] == "bd_meal_health")
    assert ["agent", "has_body", "body"] in r["match"] and ["agent", "ate", "meal"] in r["match"], \
        "the rule reads the meal and acts on the body via has_body"
    effs = json.dumps(r["effects"])
    assert '"body"' in effs and '"health"' in effs, "it lowers the BODY's health (not the mind's)"
    src = open(os.path.join(_ROOT, "worlds", "bigville_need_world.py")).read()
    assert "set_attr(body, \"health\"" not in src, "the adapter never sets health -- the rule does (no Python decision)"


# ------------------------------------------------------ G-mind-reads-the-body (headline)
def test_the_mind_reads_the_bodys_appetite_in_its_choice_collapse():
    def shopper(loaves):
        w = BigvilleNeedWorld()
        w.add_source("bakery", BREAD, BAKERY); w.add_source("alehouse", APPLE, ALEHOUSE)
        w.add_mover("Hob", SQUARE)
        w.set_preferences("Hob", {APPLE: 1.0, BREAD: 1.3}, cost_on=0.0)      # the MIND prefers bread
        w.set_drive("Hob", SUSTENANCE, v_d=10.0, c_d=0.0)
        for _ in range(loaves):
            w.eat_meal("Hob", float(BREAD), 0.7)                             # fills the BODY's satiety
        w.set_drive("Hob", SUSTENANCE, v_d=10.0, c_d=0.0)
        return w
    # the appetite the choice reads is on the BODY, not the mind
    fed = shopper(3)
    assert fed.body_state("Hob")["satiety"] > 0.3, "eating raises the BODY's satiety"
    assert fed.decide("Hob")["chosen_good"] == "apple", "the mind READS the body's satiety -> craves change"
    assert shopper(0).decide("Hob")["chosen_good"] == "bread", "with the body un-sated it follows its preference"
    # the choice rule reaches the body via has_body
    d = json.load(open(os.path.join(_ROOT, "seeds", "bigville_need_choice.json")))
    r = next(x for x in d["rules"] if x["name"] == "nd_choose_good")
    assert ["m", "has_body", "body"] in r["match"], "the mind's choice reads the body (has_body)"


# ------------------------------------------------------ G-body-and-mind-are-separate-seats (headline)
def test_one_spoiled_meal_drives_both_the_body_and_the_mind_on_their_own_nodes():
    w = BigvilleNeedWorld()
    w.add_source("bakery", BREAD, BAKERY); w.add_source("alehouse", APPLE, ALEHOUSE)
    w.add_mover("Hob", SQUARE)
    w.set_preferences("Hob", {APPLE: 1.0, BREAD: 1.2}, cost_on=0.0)
    w.set_drive("Hob", SUSTENANCE, v_d=10.0, c_d=0.0)
    assert not w.knows_degradation("Hob") and w.body_state("Hob")["health"] == 1.0, "before: whole body, empty mind"
    w.eat("Hob", 0.2)                                  # ONE spoiled meal
    # the BODY carries the physical harm...
    assert w.body_state("Hob")["health"] < 0.8, "the body's health fell (physiology, on the body node)"
    # ...the MIND carries the learned belief -- separate node, separate seat
    beliefs = list(w.eng.neighbours(w._movers["Hob"], "holds_belief"))
    assert len(beliefs) == 1, "the mind learned a belief (cognition, on the mind node)"
    body = list(w.eng.neighbours(w._movers["Hob"], "has_body"))[0]
    assert not list(w.eng.neighbours(body, "holds_belief")), "the body holds no beliefs -- that is the mind's seat"


# ------------------------------------------------------ G-physique-base-with-variation (data)
def test_base_strength_and_stamina_are_drawn_with_population_variation():
    import numpy as np
    import domains.bigville_entities as E
    rng = np.random.default_rng(20260801)
    pop = [E.draw_physique(rng) for _ in range(4000)]
    strs = np.array([p["str_base"] for p in pop]); stas = np.array([p["sta_base"] for p in pop])
    assert abs(float(strs.mean()) - E.PHYSIQUE["mean"]) < 0.05, "base strength centres on the population mean"
    assert float(strs.std()) > 0.1, "and has real spread -- strong bodies AND weak ones, not clones"
    assert strs.min() >= E.PHYSIQUE["floor"] - 1e-9, "nobody is below the floor"
    # strength and stamina share a general-fitness component but vary independently (sprinter vs endurance)
    assert 0.1 < float(np.corrcoef(strs, stas)[0, 1]) < 0.95, "loosely correlated, not one collapsed axis"
    a = E.draw_physique(np.random.default_rng(7)); b = E.draw_physique(np.random.default_rng(7))
    assert a == b, "deterministic in the seed (a distribution over seeds, not hidden randomness)"


# ------------------------------------------------------ G-lower-health-lowers-both (headline)
def test_lower_health_lowers_both_strength_and_stamina():
    w = BigvilleNeedWorld(); w.add_mover("H", SQUARE)
    w.set_physique("H", str_base=1.0, sta_base=1.0)
    assert w.strength("H") == 1.0 and w.stamina("H") == 1.0, "at full health, effective = base potential"
    w.eat("H", 0.2)                                   # a spoiled meal injures the body -> health falls
    b = w.body_state("H")
    assert b["health"] < 1.0, "the spoiled meal lowered health"
    assert w.strength("H") < 1.0 and w.stamina("H") < 1.0, "a sick body is weaker AND tires sooner"
    # effective scales with health: strength ~= base * health
    assert abs(w.strength("H") - 1.0 * b["health"]) < 1e-6, "effective strength = base * health"


# ------------------------------------------------------ G-use-builds-the-stat (headline)
def test_strength_tasks_slowly_build_strength_toward_a_base_relative_ceiling():
    import domains.bigville_entities as E
    w = BigvilleNeedWorld(); w.add_mover("H", SQUARE)
    w.set_physique("H", str_base=1.0, sta_base=1.0)
    seq = [w.strength("H")]
    for _ in range(40):
        seq.append(w.perform_task("H", strength=True, intensity=1.0)[0])
    assert all(seq[i] < seq[i + 1] for i in range(len(seq) - 1)), "each session builds a little more strength"
    first_gain = seq[1] - seq[0]; late_gain = seq[40] - seq[39]
    assert first_gain > late_gain, "diminishing returns -- the early gains are the biggest (a slow approach)"
    ceiling = 1.0 * (1.0 + E.TRAIN_HEADROOM)
    assert seq[-1] < ceiling + 1e-9, "training never exceeds the base-relative ceiling (base * (1+HEADROOM))"
    assert seq[-1] > ceiling - 0.02, "but with enough use it approaches that ceiling"


def test_a_stamina_task_builds_stamina_not_strength():
    w = BigvilleNeedWorld(); w.add_mover("H", SQUARE)
    w.set_physique("H", str_base=1.0, sta_base=1.0)
    for _ in range(20):
        w.perform_task("H", stamina=True, intensity=1.0)
    assert w.strength("H") == 1.0, "a stamina task leaves strength untouched -- the stats are orthogonal"
    assert w.stamina("H") > 1.1, "and builds stamina"


# ------------------------------------------------------ G-relative-to-base (headline)
def test_training_is_relative_to_base_a_stronger_body_trains_higher():
    strong = BigvilleNeedWorld(); strong.add_mover("S", SQUARE); strong.set_physique("S", str_base=1.4, sta_base=1.0)
    weak = BigvilleNeedWorld(); weak.add_mover("W", SQUARE); weak.set_physique("W", str_base=0.7, sta_base=1.0)
    for _ in range(60):
        strong.perform_task("S", strength=True); weak.perform_task("W", strength=True)
    assert strong.strength("S") > weak.strength("W"), "the higher base trains to a higher strength"
    # the ceiling is proportional to base, so the trained ratio tracks the base ratio (relative to base)
    assert abs(strong.strength("S") / weak.strength("W") - 1.4 / 0.7) < 0.05, \
        "both approach base*(1+HEADROOM), so the ratio is the base ratio -- growth is RELATIVE to base"


# ------------------------------------------------------ G-physique-is-rules (source audit)
def test_the_physique_dynamics_are_seed_rules_not_python():
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_body.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"bd_train_strength", "bd_train_stamina", "bd_effective_stats"} <= names, "training + health-modulation are rules"
    eff = next(r for r in seed["rules"] if r["name"] == "bd_effective_stats")
    body = json.dumps(eff["effects"])
    assert '"strength"' in body and '"stamina"' in body and '"health"' in body, "effective = f(base, trained, health) in the rule"
    src = open(os.path.join(_ROOT, "worlds", "bigville_need_world.py")).read()
    body_of = src.split("def perform_task", 1)[1].split("\n    def ", 1)[0]
    assert "str_train" not in body_of and "sta_train" not in body_of, \
        "perform_task never computes the trained gain -- it mints the Effort and runs the rule"
    assert 'set_attr(body, "strength"' not in body_of and 'set_attr(body, "stamina"' not in body_of, \
        "and never sets the effective stat -- bd_effective_stats does (health-modulation is the rule)"


# ------------------------------------------------------ G-stamina-reserve-deplete-recover (headline)
def test_exertion_depletes_the_stamina_reserve_and_rest_restores_it():
    w = BigvilleNeedWorld(); w.add_mover("H", SQUARE)
    w.set_physique("H", str_base=1.0, sta_base=1.0)
    assert w.stamina_reserve("H") == 1.0, "a rested body starts at full reserve (= capacity)"
    w.perform_task("H", strength=True, stamina_cost=0.3)
    assert abs(w.stamina_reserve("H") - 0.7) < 1e-6, "exertion spends stamina from the reserve"
    w.perform_task("H", strength=True, stamina_cost=0.3); w.perform_task("H", strength=True, stamina_cost=0.3)
    assert w.stamina_reserve("H") <= 0.11, "keep working and the reserve runs low"
    w.rest("H", 0.5)
    assert abs(w.stamina_reserve("H") - 0.6) < 1e-6, "rest restores the reserve"


def test_rest_cannot_take_the_reserve_above_capacity():
    w = BigvilleNeedWorld(); w.add_mover("H", SQUARE)
    w.set_physique("H", str_base=1.0, sta_base=1.0)     # capacity 1.0
    w.perform_task("H", strength=True, stamina_cost=0.4)
    w.rest("H", 5.0)                                     # over-rest
    assert abs(w.stamina_reserve("H") - w.stamina("H")) < 1e-6, "you cannot rest above your max endurance (capacity)"


# ------------------------------------------------------ G-exertion-raises-hunger (headline)
def test_exertion_makes_you_hungrier_more_exertion_more_hunger():
    w = BigvilleNeedWorld(); w.add_mover("H", SQUARE); w.set_physique("H", sta_base=2.0)
    assert w.hunger("H") == 0.0, "a body at rest is not made hungry by resting"
    w.perform_task("H", stamina=True, stamina_cost=0.3)
    assert abs(w.hunger("H") - 0.3) < 1e-6, "using stamina raises hunger (needs more food)"
    w.perform_task("H", strength=True, stamina_cost=0.0)
    assert abs(w.hunger("H") - 0.3) < 1e-6, "a no-cost task does not -- it's the stamina spent that makes you hungry"
    light = BigvilleNeedWorld(); light.add_mover("L", SQUARE); light.set_physique("L", sta_base=2.0)
    heavy = BigvilleNeedWorld(); heavy.add_mover("V", SQUARE); heavy.set_physique("V", sta_base=2.0)
    light.perform_task("L", stamina=True, stamina_cost=0.2)
    heavy.perform_task("V", stamina=True, stamina_cost=0.5)
    assert heavy.hunger("V") > light.hunger("L"), "exerting yourself MORE needs MORE food"


def test_the_reserve_and_hunger_dynamics_are_seed_rules():
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_body.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"bd_exert_cost", "bd_rest_recover"} <= names, "deplete + recover are rules"
    exert = next(r for r in seed["rules"] if r["name"] == "bd_exert_cost")
    body = json.dumps(exert["effects"])
    assert '"stamina_reserve"' in body and '"hunger_level"' in body, "one exertion both spends the reserve AND raises hunger"
