"""bigville R23 (block 271000) -- FERTILITY gates: the quantity-quality decision,
and does "poorer -> more children" EMERGE? Gates mirror BIGVILLE_FERT_PREREG.md.

FERTILITY IS A DECISION, NEVER a rule keyed on wealth. Three staged graph rules
(bf_*) compute a fertility `decision_value` (child benefit vs cost); the wealth ->
fertility gradient is MEASURED, never asserted, and comes THROUGH the mechanisms:

  * G-fertility-is-a-decision: birth emerges from a decision_value (benefit vs
    cost), NOT a fixed ingest; the SOURCE-AUDIT proves NO rule keys fertility on
    wealth.
  * G-quantity-quality (Becker): cheap children (no school, child labour) -> MORE;
    expensive children (schooling R18 + the mother's opp cost) -> FEWER. Ablate the
    school cost -> the tradeoff shifts toward quantity.
  * G-child-mortality-drives-fertility (ties R22): high mortality -> MORE births
    (replacement); ablate mortality (public health, R22's lever) -> fertility FALLS.
  * G-old-age-security (insurance motive): no safety net -> MORE; add a safety net
    (R9) -> FEWER.
  * G-does-"poorer->more-children"-EMERGE (HEADLINE, MEASURE-FIRST, FORWARD): with
    the drivers above and wealth entering ONLY through the mechanisms, the wealth ->
    fertility gradient is negative (poorer -> more) -- convergent validity, NOT
    tuned. Structural levers (public health / free schooling / a safety net) bend it.

Every fertility DECISION is a seed rule (bf_*). The adapter mints nodes, wires
edges, delivers the mechanism inputs by name, arms one-shots, ticks and reads --
no Python decision, no wealth key, no reward/punishment token. ZERO new Rust.
"""
from __future__ import annotations

import json
import math
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT,
           os.path.join(_ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_fert_world import BigvilleFertWorld               # noqa: E402
from worlds.bigville_time_world import DAY                             # noqa: E402
from bigville_fert_run import (                                        # noqa: E402
    wealth_to_conditions, SCHOOL_FEE, PENSION_WEALTH, MORT_RICH)


def _world():
    w = BigvilleFertWorld(day_range=16)
    w.set_phase(DAY)
    return w


def _P(w):
    return sorted(w._cell_at.keys())


# ================================================== G-fertility-is-a-decision
def test_fertility_is_a_decision_value():
    """Fertility emerges from a decision_value = child benefit - cost, NOT a fixed
    ingest and NOT keyed on wealth. A higher-COST family (school + opp cost) reaches
    a LOWER decision_value -> LOWER fertility than an identical lower-cost one."""
    w = _world(); P = _P(w)
    w.make_couple("a", P[0], base_target=2.0, oldage_value=2.0, safety_net=0.0)
    w.make_couple("b", P[1], base_target=2.0, oldage_value=2.0, safety_net=0.0,
                  school_cost=1.0, opp_cost=1.0)
    w.decide("a"); w.decide("b")
    # decision_value = base_target + child_labour + oldage_motive - school - opp.
    assert abs(w.decision_value_of("a") - 4.0) < 1e-9, "benefit 2+2 - cost 0 = 4"
    assert abs(w.decision_value_of("b") - 2.0) < 1e-9, "benefit 2+2 - cost 2 = 2"
    assert w.fertility_of("a") > w.fertility_of("b"), "lower-cost -> more children"
    assert abs(w.fertility_of("a") - 4.0) < 1e-9 and abs(w.fertility_of("b") - 2.0) < 1e-9


def test_birth_flows_from_the_decision():
    """Birth FLOWS FROM THE DECISION: beget() mints floor(fertility) children at the
    honest R14 boundary, so a high-decision_value family begets MORE actual children
    than a low one -- birth is the decision, not a fixed ingest."""
    w = _world(); P = _P(w)
    # high: dv 4 -> fertility 4 ; low: dv 1 -> fertility 1 (school 2 + opp 1 cost).
    w.make_couple("hi", P[0], base_target=2.0, oldage_value=2.0, safety_net=0.0)
    w.make_couple("lo", P[1], base_target=2.0, oldage_value=2.0, safety_net=0.0,
                  school_cost=2.0, opp_cost=1.0)
    w.decide("hi"); w.decide("lo")
    n_hi = w.beget("hi"); n_lo = w.beget("lo")
    assert n_hi == 4 and n_lo == 1, "children minted = floor(fertility)"
    assert n_hi > n_lo, "the higher-decision_value family begets more children"
    assert len(w.children_of("hi")) == 4


# ================================================== G-quantity-quality (Becker)
def test_quantity_quality_tradeoff():
    """Becker: children CHEAP (no school cost, child labour useful) -> MORE desired
    (quantity); children EXPENSIVE (schooling + the mother's opp cost) -> FEWER,
    invested (quality). Old-age + mortality isolated out (safety_net=1, mortality=0)."""
    w = _world(); P = _P(w)
    w.make_couple("cheap", P[0], base_target=2.0, safety_net=1.0, mortality=0.0,
                  child_labour_benefit=2.0, school_cost=0.0, opp_cost=0.0)
    w.make_couple("dear", P[1], base_target=2.0, safety_net=1.0, mortality=0.0,
                  child_labour_benefit=0.0, school_cost=0.5, opp_cost=0.5)
    w.decide("cheap"); w.decide("dear")
    assert abs(w.desired_surviving_of("cheap") - 4.0) < 1e-9, "2 + labour 2 = 4"
    assert abs(w.desired_surviving_of("dear") - 1.0) < 1e-9, "2 - (0.5+0.5) = 1"
    assert w.desired_surviving_of("cheap") > w.desired_surviving_of("dear")


def test_ablate_school_cost_shifts_to_quantity():
    """CONTROL: ablate the school cost -> the quantity-quality tradeoff shifts toward
    QUANTITY (desired_surviving RISES). Isolates the school cost (opp=0)."""
    w = _world(); P = _P(w)
    w.make_couple("x", P[0], base_target=2.0, safety_net=1.0, mortality=0.0,
                  school_cost=2.0, opp_cost=0.0)
    w.decide("x")
    assert abs(w.desired_surviving_of("x") - 0.0) < 1e-9, "2 - 2 = 0 (all quality)"
    w.set_conditions("x", school_cost=0.0)                 # ablate the school cost
    w.decide("x")
    assert abs(w.desired_surviving_of("x") - 2.0) < 1e-9, "school cost gone -> 2"
    assert w.desired_surviving_of("x") > 0.0, "the tradeoff shifted to quantity"


# ============================== G-child-mortality-drives-fertility (ties R22)
def test_high_mortality_raises_fertility():
    """High child mortality -> HIGHER fertility (have more to ensure some survive):
    same desired_surviving, more births. The demographic-transition engine."""
    w = _world(); P = _P(w)
    w.make_couple("hi", P[0], base_target=2.0, safety_net=1.0, mortality=0.5)
    w.make_couple("lo", P[1], base_target=2.0, safety_net=1.0, mortality=0.0)
    w.decide("hi"); w.decide("lo")
    assert abs(w.desired_surviving_of("hi") - w.desired_surviving_of("lo")) < 1e-9, \
        "same desired surviving"
    assert abs(w.fertility_of("hi") - 4.0) < 1e-9, "desired 2 / survival 0.5 = 4"
    assert abs(w.fertility_of("lo") - 2.0) < 1e-9, "desired 2 / survival 1.0 = 2"
    assert w.fertility_of("hi") > w.fertility_of("lo")


def test_ablate_mortality_fertility_falls():
    """CONTROL (the R22 lever): ablate child mortality (free public health / well-
    baby care) -> fertility FALLS to desired_surviving (no replacement needed)."""
    w = _world(); P = _P(w)
    w.make_couple("p", P[0], base_target=2.0, safety_net=1.0, mortality=0.5)
    w.decide("p")
    assert abs(w.fertility_of("p") - 4.0) < 1e-9
    w.set_conditions("p", mortality=0.0)                   # public health lever
    w.decide("p")
    assert abs(w.fertility_of("p") - w.desired_surviving_of("p")) < 1e-9, \
        "no mortality -> fertility == desired surviving"
    assert abs(w.fertility_of("p") - 2.0) < 1e-9, "fertility FELL from 4 to 2"


# ==================================== G-old-age-security (insurance motive)
def test_no_safety_net_raises_fertility():
    """No pension/safety-net -> children as old-age insurance -> the motive is ON ->
    MORE children than an otherwise-identical family with a safety net."""
    w = _world(); P = _P(w)
    w.make_couple("nonet", P[0], base_target=2.0, oldage_value=2.0, safety_net=0.0,
                  mortality=0.0)
    w.make_couple("net", P[1], base_target=2.0, oldage_value=2.0, safety_net=1.0,
                  mortality=0.0)
    w.decide("nonet"); w.decide("net")
    assert abs(w.oldage_motive_of("nonet") - 2.0) < 1e-9, "no net -> motive ON"
    assert abs(w.oldage_motive_of("net") - 0.0) < 1e-9, "net -> motive OFF"
    assert abs(w.fertility_of("nonet") - 4.0) < 1e-9 and abs(w.fertility_of("net") - 2.0) < 1e-9
    assert w.fertility_of("nonet") > w.fertility_of("net")


def test_safety_net_lowers_fertility():
    """CONTROL (the R9 lever): add a safety net -> the old-age-security motive
    weakens (OFF) -> fertility FALLS."""
    w = _world(); P = _P(w)
    w.make_couple("p", P[0], base_target=2.0, oldage_value=2.0, safety_net=0.0,
                  mortality=0.0)
    w.decide("p")
    assert abs(w.fertility_of("p") - 4.0) < 1e-9
    w.set_conditions("p", safety_net=1.0)                  # the R9 safety net
    w.decide("p")
    assert abs(w.fertility_of("p") - 2.0) < 1e-9, "safety net -> fertility FELL"


# ============ G-does-"poorer->more-children"-EMERGE (HEADLINE, FORWARD, town)
def _town(w, coins, *, overrides=None):
    """Build a town where wealth enters ONLY through the mechanism inputs
    (wealth_to_conditions -- the measurement harness, NOT a fertility rule). Returns
    the per-family fertility (the graph's decision)."""
    P = _P(w)
    names = []
    for i, c in enumerate(coins):
        cond = wealth_to_conditions(float(c))
        if overrides:
            cond.update(overrides)
        w.make_couple("f%d" % i, P[i], coin=float(c), **cond)
        names.append("f%d" % i)
    for nm in names:
        w.decide(nm)
    return [w.fertility_of(nm) for nm in names]


def _corr(xs, ys):
    n = len(xs)
    mx = sum(xs) / n; my = sum(ys) / n
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if sx < 1e-12 or sy < 1e-12:
        return 0.0
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)


def test_poorer_more_children_gradient_emerges():
    """HEADLINE (MEASURE-FIRST, FORWARD): a town with a wealth gradient, wealth
    entering ONLY through the four mechanisms (mortality R22, school+opp R18,
    old-age R9). MEASURE corr(wealth, fertility). The SIGN emerges NEGATIVE
    (poorer -> more children) -- convergent validity with the demographic
    transition, NOT tuned (no rule sees wealth). The magnitude is indicative."""
    w = _world()
    # a spread of wealth from destitute to comfortable (deterministic gradient).
    coins = [0, 5, 10, 15, 20, 25, 30, 35, 45, 55, 65, 80, 100, 130, 160, 200]
    fert = _town(w, coins)
    corr = _corr(coins, fert)
    poor = [f for c, f in zip(coins, fert) if c < SCHOOL_FEE]
    rich = [f for c, f in zip(coins, fert) if c >= PENSION_WEALTH]
    assert corr < 0.0, "poorer -> more children EMERGES (negative corr): %.3f" % corr
    assert corr < -0.5, "the gradient is strong, not marginal: corr=%.3f" % corr
    assert sum(poor) / len(poor) > sum(rich) / len(rich), \
        "poor families have MORE children than rich ones"


def test_structural_levers_bend_the_gradient():
    """The agency/structure counterfactuals: each STRUCTURAL lever (free public
    health, free schooling, a universal safety net) BENDS the emergent gradient --
    only a systemic intervention moves it, mirroring R9/R18/R22's levers."""
    coins = [0, 5, 10, 15, 20, 25, 30, 45, 60, 80, 110, 150]
    base = _town(_world(), coins)
    pub = _town(_world(), coins, overrides=dict(mortality=MORT_RICH))
    sch = _town(_world(), coins, overrides=dict(school_cost=0.0))
    net = _town(_world(), coins, overrides=dict(safety_net=1.0))
    poor = [i for i, c in enumerate(coins) if c < SCHOOL_FEE]
    rich = [i for i, c in enumerate(coins) if c >= PENSION_WEALTH]

    def m(vals, idx):
        return sum(vals[i] for i in idx) / len(idx)

    # public health drops the mortality-replacement -> the poor have fewer.
    assert m(pub, poor) < m(base, poor), "public health -> the poor bear fewer"
    # free schooling removes the quality cost -> the rich shift toward quantity.
    assert m(sch, rich) > m(base, rich), "free schooling -> the rich bear more"
    # a universal safety net removes the old-age motive -> the poor have fewer.
    assert m(net, poor) < m(base, poor), "a safety net -> the poor bear fewer"


# ========================================== source-audit + discipline
def _strip_py(src):
    src = re.sub(r'"""[\s\S]*?"""', "", src)
    src = re.sub(r"'''[\s\S]*?'''", "", src)
    src = re.sub(r"#.*", "", src)
    src = re.sub(r'"[^"\n]*"', '""', src)
    src = re.sub(r"'[^'\n]*'", "''", src)
    return src


def test_no_python_agent_decision_source_audit():
    """Every fertility DECISION is a seed rule, not Python. The adapter mints nodes,
    wires edges, delivers the mechanism inputs by NAME, arms one-shots, ticks and
    reads -- it never COMPUTES the fertility / decision_value / desired_surviving in
    Python, runs no Python rule engine, and NEVER branches on a decision attr. NO
    reward/punishment token."""
    src = open(os.path.join(_ROOT, "worlds", "bigville_fert_world.py")).read()
    # strip the mechanical DEFAULTS dict (opaque attr names, not decisions).
    src = re.sub(r"FERT_DEFAULTS\s*=\s*dict\([\s\S]*?\)\n", "", src, count=1)
    code = _strip_py(src)
    for banned in ("graph_rewrite", "gr._match", "gr._apply", "make_rule", "add_rule"):
        assert banned not in code, "adapter must not run/author the Python rule engine"
    for token in ("reward", "punish", "penalty", "penalis", "penaliz"):
        assert token not in code.lower(), "NO reward/punishment token (%s)" % token
    # the DECISION outcomes/inputs live in the rule -- the adapter never branches on
    # them (it sets them by name in ingest / delivers them by name as world facts).
    for param in ("fertility", "decision_value", "desired_surviving", "oldage_motive",
                  "mortality", "safety_net", "school_cost", "decide_armed"):
        assert ("if " + param) not in code, \
            "decision parameter %s must live in a rule `where`, not an adapter branch" % param


def test_no_rule_keys_fertility_on_wealth():
    """THE anti-tuning source-audit (the point of the whole rung): NO bf_* rule reads
    wealth / coin / class in its match, where, or effects. The wealth->fertility
    gradient comes THROUGH the mechanism inputs only -- keying on wealth would beg
    the question."""
    s = json.load(open(os.path.join(_ROOT, "seeds", "bigville_fert_decide.json")))
    blob = json.dumps(s["rules"]).lower()
    for token in ("coin", "wealth", "class", "rich", "poor", "income", "money"):
        assert token not in blob, "a fertility rule keys on %r (forbidden)" % token


def test_seed_is_self_load_only_and_named():
    """Discipline at the source: the fertility seed is self_load_only (loaded ONLY by
    the R23 adapter -> cannot regress another suite), declares no deps, and its rule
    set is EXACTLY the three named fertility decisions. No rule mints/destroys a node
    (conservation of the graph structure); NO new Rust."""
    s = json.load(open(os.path.join(_ROOT, "seeds", "bigville_fert_decide.json")))
    assert s.get("self_load_only") is True, "the seed must be self_load_only"
    assert s.get("depends_on") == [], "no seed deps (reuse R14/R22/R18/R9 by import)"
    names = {r["name"] for r in s["rules"]}
    assert names == {"bf_oldage", "bf_quantity_quality", "bf_mortality_replace"}, \
        "the three fertility decisions are RULES"
    for r in s["rules"]:
        for eff in r.get("effects", []):
            assert eff[0] not in ("add_node", "del_node"), \
                "%s mints/destroys a node (must not)" % r["name"]
