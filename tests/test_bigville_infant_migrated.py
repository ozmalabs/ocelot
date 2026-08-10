"""bigville R22b (block 272000) -- INFANT MORTALITY: well-baby care drops infant
mortality, the sharpest inequality face. Gates mirror BIGVILLE_INFANT_PREREG.md.

  * G-infant-fragility: an UNSEEN infant dies of a SMALL shock that an adult (and a
    seen baby) survives -- the fragility penalty (elevated baseline mortality).
  * G-well-baby-care-reduces-mortality (HEADLINE): a baby under regular well-baby
    care (well_baby=1) SURVIVES a shock that KILLS an unseen one. The visit MOVES
    coin family->doctor (CONSERVED); ablate coin -> no visit -> not protected.
  * G-infant-mortality-tracks-wealth (the sharpest inequality face): an infant
    cohort with a WEALTH gradient meeting ONE disease -> the POOR can't afford
    regular visits -> their INFANTS die; the RICH afford care -> survive. Infant
    mortality TRACKS wealth (a positive wealth-survival correlation).
  * G-public-health-lever: council-funded public well-baby care (treasury pays) ->
    the SAME poor cohort ALL survive -> the wealth-mortality correlation VANISHES.
  * ETHICS (induce -> measure -> RESTORE, NO reward/punishment): infant illness is
    induced + measured, then RESTORED by public provision.

Every infant-care DECISION is a seed rule (bi_*): affordability, the fragility-
modulated drop, the death. The adapter mints nodes, wires edges, arms one-shots,
ticks and reads -- no Python decision, no reward/punishment token. ZERO new Rust.
"""
from __future__ import annotations

import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_infant_world import BigvilleInfantWorld          # noqa: E402
from worlds.bigville_time_world import DAY                            # noqa: E402


def _world():
    w = BigvilleInfantWorld(day_range=16)
    w.set_phase(DAY)
    return w


def _pool(w):
    return sorted(w._cell_at.keys())


# ============================================== G-infant-fragility
def test_infant_fragility_kills_small_shock_an_adult_survives():
    """An UNSEEN infant (well_baby=0) struck by a SMALL disease takes
    disease_base + infant_fragility and DIES, while an ADULT (R22 admit, no infant
    fragility) survives the SAME small shock (base drop only). Elevated baseline
    infant mortality, from the fragility penalty."""
    w = _world()
    P = _pool(w)
    w.add_doctor("doc", P[0], wellbaby_fee=10.0)
    w.add_baby("baby", P[10], coin=0.0, health=40.0, infant_fragility=40.0)
    w.admit("adult", P[11], coin=0.0, health=40.0, progression=0.0)  # R22 adult
    w.infant_strike("baby", 20.0)              # small shock to the unseen infant
    w.strike("adult", 20.0)                    # SAME small shock to the adult (R22)
    assert w.is_dead("baby"), "the unseen infant dies of a small shock (20 + 40 fragility >= 40)"
    assert w.death_cause_of("baby") == 2, "death routed as illness (cause 2)"
    assert not w.is_dead("adult"), "the adult survives the SAME small shock (drop 20 < 40)"
    assert abs(w.health_of("adult") - 20.0) < 1e-9, "adult: base drop only"


# ============================================== well-baby visit is paid (market)
def test_wellbaby_is_paid_conserved_transfer():
    """A well-baby visit COSTS coin -- a CONSERVED transfer (the family loses
    exactly what the doctor gains). The doctor DRAWS INCOME (R22 fee-for-service)."""
    w = _world()
    P = _pool(w)
    w.add_doctor("doc", P[0], wellbaby_fee=10.0)
    w.add_baby("baby", P[10], coin=100.0, health=100.0)
    tot0 = w.total_coin(["baby", "doc"])
    dc0 = w.doctor_coin()
    w.well_baby_visit("baby")
    assert w.well_baby_of("baby"), "the paying family gets well-baby care"
    assert abs(w.coin_of("baby") - 90.0) < 1e-9, "family pays the wellbaby_fee"
    assert abs(w.doctor_coin() - dc0 - 10.0) < 1e-9, "the doctor draws the fee as income"
    assert abs(w.total_coin(["baby", "doc"]) - tot0) < 1e-9, "coin CONSERVED (a transfer)"


def test_ablate_coin_no_wellbaby():
    """CONTROL (money-gating): a family that CANNOT afford the fee (coin < fee) gets
    NO well-baby care -- bi_wellbaby does not fire, coin unchanged, well_baby stays
    0. The marshmallow dissolution: it is AFFORDABILITY, not myopia."""
    w = _world()
    P = _pool(w)
    w.add_doctor("doc", P[0], wellbaby_fee=10.0)
    w.add_baby("pauper", P[10], coin=5.0, health=100.0)
    w.well_baby_visit("pauper")
    assert not w.well_baby_of("pauper"), "can't afford the visit -> not protected"
    assert abs(w.coin_of("pauper") - 5.0) < 1e-9, "no fee charged (no visit happened)"
    assert abs(w.doctor_coin()) < 1e-9, "the doctor earned nothing from the pauper"


# ============================================== G-well-baby-care-reduces-mortality
def test_wellbaby_care_reduces_mortality():
    """HEADLINE: a baby under regular well-baby care (well_baby=1, via a paid visit)
    SURVIVES a shock that KILLS an unseen one (well_baby=0). Control: no visit ->
    the same shock kills. Well-baby care drops infant mortality significantly."""
    w = _world()
    P = _pool(w)
    w.add_doctor("doc", P[0], wellbaby_fee=10.0)
    w.add_baby("seen", P[10], coin=100.0, health=40.0, infant_fragility=40.0)
    w.add_baby("unseen", P[11], coin=100.0, health=40.0, infant_fragility=40.0)
    w.well_baby_visit("seen")                  # seen: pays -> well_baby=1
    # 'unseen' does NOT get a visit (the control)
    assert w.well_baby_of("seen") and not w.well_baby_of("unseen")
    w.infant_strike("seen", 20.0); w.infant_strike("unseen", 20.0)   # SAME shock
    assert not w.is_dead("seen"), "regular well-baby care -> survives the shock"
    assert abs(w.health_of("seen") - 20.0) < 1e-9, "seen: base drop only (20)"
    assert w.is_dead("unseen"), "unseen: base + fragility (60 >= 40) -> DIES"


# ============================================== G-infant-mortality-tracks-wealth
def _cohort(w, P, coins, *, health=40.0, infant_fragility=40.0, start=10, prefix="b"):
    """An infant cohort with a WEALTH gradient (household coin), else identical."""
    names = []
    for i, c in enumerate(coins):
        nm = "%s%d" % (prefix, i)
        w.add_baby(nm, P[start + i], coin=float(c), health=health,
                   infant_fragility=infant_fragility)
        names.append(nm)
    return names


def test_infant_mortality_tracks_wealth():
    """The sharpest inequality face: infant mortality is money-gated, so it TRACKS
    wealth. A wealth gradient meets ONE disease striking all babies: the POOR (coin
    < wellbaby_fee) can't afford regular visits -> their INFANTS die; the RICH
    afford care -> their infants survive the SAME disease. The babies dying is the
    most damning point of the inequality spine."""
    w = _world()
    P = _pool(w)
    w.add_doctor("doc", P[0], wellbaby_fee=30.0)
    coins = [0.0, 5.0, 10.0, 20.0, 29.0, 30.0, 50.0, 100.0]
    names = _cohort(w, P, coins)
    for nm in names:
        w.well_baby_visit(nm)
    for nm in names:
        w.infant_strike(nm, 20.0)              # the SAME disease for every baby
    for nm, c in zip(names, coins):
        if c >= 30.0:
            assert not w.is_dead(nm), "rich family (coin %s) -> baby survives" % c
        else:
            assert w.is_dead(nm), "poor family (coin %s) -> infant dies" % c
    dead = sum(w.is_dead(nm) for nm in names)
    alive = len(names) - dead
    assert dead == 5 and alive == 3, "5 poor babies die, 3 rich survive (money-gated)"
    survivors_wealth = [c for nm, c in zip(names, coins) if not w.is_dead(nm)]
    assert min(survivors_wealth) >= 30.0, "every survivor's family could afford care"
    corr = w.wealth_mortality_corr(names, coins)
    assert corr >= 0.5, "infant SURVIVAL is strongly positively correlated with wealth (%.3f)" % corr


# ============================================== G-public-health-lever (structural)
def test_public_wellbaby_dissolves_the_gradient():
    """THE STRUCTURAL LEVER (agency/structure bedrock): flip council-funded PUBLIC
    well-baby care on (the treasury pays) -> the SAME poor cohort meeting the SAME
    disease now ALL get care and ALL survive. The wealth-infant-mortality
    correlation VANISHES -- only a systemic lever saves the poor's babies."""
    w = _world()
    P = _pool(w)
    w.add_doctor("doc", P[0], wellbaby_fee=30.0)
    w.add_treasury(10000.0)
    coins = [0.0, 5.0, 10.0, 20.0, 29.0, 30.0, 50.0, 100.0]
    names = _cohort(w, P, coins)
    w.set_public_health(True, names)           # THE LEVER
    f0 = w.treasury_funds()
    for nm in names:
        w.well_baby_visit(nm)
    for nm in names:
        w.infant_strike(nm, 20.0)
    for nm, c in zip(names, coins):
        assert w.well_baby_of(nm), "public care protects even the coin-0 poor (%s)" % c
        assert not w.is_dead(nm), "under public well-baby care, the poor's babies survive (%s)" % c
    # the families paid NOTHING out of pocket; the treasury bore the cost (conserved).
    for nm, c in zip(names, coins):
        assert abs(w.coin_of(nm) - c) < 1e-9, "no out-of-pocket fee under public care"
    assert abs(f0 - w.treasury_funds() - 30.0 * len(names)) < 1e-9, \
        "the treasury paid the full cost (a conserved public transfer)"
    corr = w.wealth_mortality_corr(names, coins)
    assert abs(corr) < 1e-9, "the wealth-mortality correlation VANISHES under the lever (%.3f)" % corr
    assert w.infant_mortality(names) == 0.0, "infant mortality drops to zero across the board"


# ============================================== ETHICS (induce -> measure -> RESTORE)
def test_ethics_infant_mortality_restored_by_public_provision():
    """ETHICS at the structural scale: a poor infant cohort left to die (induce +
    measure) is RESTORED not by personal effort but by PUBLIC PROVISION -- a fresh
    IDENTICAL poor cohort, the SAME disease, with public well-baby care on, survives.
    The restore is a systemic lever, NOT reward/punishment; infant death is a STATE,
    reversed by provision."""
    w = _world()
    P = _pool(w)
    w.add_doctor("doc", P[0], wellbaby_fee=30.0)
    w.add_treasury(10000.0)
    # INDUCE + MEASURE: a poor cohort with NO public care dies.
    poor = _cohort(w, P, [0.0, 5.0, 10.0], start=10, prefix="poor")
    for nm in poor:
        w.well_baby_visit(nm)
    for nm in poor:
        w.infant_strike(nm, 20.0)
    assert w.infant_mortality(poor) == 1.0, "harm induced: the poor's unseen babies all die"
    # RESTORE: a fresh IDENTICAL poor cohort under PUBLIC PROVISION survives.
    poor2 = _cohort(w, P, [0.0, 5.0, 10.0], start=20, prefix="pp")
    w.set_public_health(True, poor2)
    for nm in poor2:
        w.well_baby_visit(nm)
    for nm in poor2:
        w.infant_strike(nm, 20.0)
    assert w.infant_mortality(poor2) == 0.0, "public provision RESTORES the poor's babies"


# ============================================== source-audit + discipline
def _strip_py(src: str) -> str:
    src = re.sub(r'"""[\s\S]*?"""', "", src)
    src = re.sub(r"'''[\s\S]*?'''", "", src)
    src = re.sub(r"#.*", "", src)
    src = re.sub(r'"[^"\n]*"', '""', src)
    src = re.sub(r"'[^'\n]*'", "''", src)
    return src


def test_no_python_agent_decision_source_audit():
    """Every infant-care DECISION is a seed rule, not Python. The adapter mints
    nodes, wires edges, delivers world facts, arms one-shots, ticks and reads -- it
    never COMPUTES whether a visit happens / a drop / a death in Python, and runs no
    Python rule engine. NO reward/punishment token."""
    world_src = open(os.path.join(_ROOT, "worlds", "bigville_infant_world.py")).read()
    # strip the mechanical DEFAULTS dict (opaque attr names, not decisions).
    world_src = re.sub(r"INFANT_DEFAULTS\s*=\s*dict\([\s\S]*?\)\n", "", world_src, count=1)
    code = _strip_py(world_src)
    for banned in ("graph_rewrite", "gr._match", "gr._apply", "make_rule", "add_rule"):
        assert banned not in code, "adapter must not run/author the Python rule engine"
    for token in ("reward", "punish", "penalty", "penalis", "penaliz"):
        assert token not in code.lower(), "NO reward/punishment token (%s)" % token
    # the rule-DECISION outcomes appear only in the seed -- the adapter never
    # branches on them (opaque attrs it sets by name in ingest). (infant_fragility,
    # like R22's progression, appears only in a mechanical optional-override
    # None-check -- a keyword-arg guard, not a branch over graph STATE -- so it is
    # not a decision parameter and is excluded here, mirroring R22's audit.)
    for param in ("well_baby", "public_health",
                  "infant_disease_armed", "wellbaby_armed", "disease_base"):
        assert ("if " + param) not in code, \
            "decision parameter %s must live in a rule `where`, not an adapter branch" % param


def test_seed_is_self_load_only_and_named():
    """Discipline at the source: the infant seed is self_load_only (loaded ONLY by
    the R22b adapter -> cannot regress another suite), declares no deps, and its rule
    set is EXACTLY the three named infant decisions. No rule mints/destroys a node
    (conservation); coin never set from a fractional Div; NO new Rust."""
    import json
    s = json.load(open(os.path.join(_ROOT, "seeds", "bigville_infant_care.json")))
    assert s.get("self_load_only") is True, "the seed must be self_load_only"
    assert s.get("depends_on") == [], "no seed deps (reuse R22/R14/R9 by import)"
    names = {r["name"] for r in s["rules"]}
    assert names == {"bi_wellbaby", "bi_wellbaby_public", "bi_onset"}, \
        "the three infant decisions are RULES"
    for r in s["rules"]:
        for eff in r.get("effects", []):
            assert eff[0] not in ("add_node", "del_node"), \
                "%s mints/destroys a node (must conserve)" % r["name"]
            if eff[0] == "set_attr" and len(eff) > 2 and eff[2] in ("coin", "funds"):
                assert '"Div"' not in json.dumps(eff), "coin/funds never set from a fractional Div"


def test_no_reward_punishment_in_seed():
    """ETHICS at the seed level: no reward/punishment token in the RULE LOGIC (an
    infant illness / death is a STATE, never a badness). Scoped to the rules, not
    the seed's prose description (which legitimately discusses the ethics protocol)."""
    import json
    s = json.load(open(os.path.join(_ROOT, "seeds", "bigville_infant_care.json")))
    blob = json.dumps(dict(rules=s["rules"], nodes=s.get("nodes", []),
                           edges=s.get("edges", []),
                           concepts=s.get("concepts", []))).lower()
    for token in ("reward", "punish", "penalty"):
        assert token not in blob, "rule logic carries a %s token" % token


def test_r22_doctor_seed_untouched():
    """Additive discipline: R22's committed seed (bigville_doctor_care.json) is NOT
    edited by this rung -- its six rules are exactly as R22 landed them (the infant
    onset uses a DISJOINT arm, infant_disease_armed, so bd_onset is never disturbed)."""
    import json
    s = json.load(open(os.path.join(_ROOT, "seeds", "bigville_doctor_care.json")))
    names = {r["name"] for r in s["rules"]}
    assert names == {"bd_checkup", "bd_checkup_public", "bd_treat", "bd_treat_public",
                     "bd_onset", "bd_recover"}, "R22's six doctor rules are intact"


def test_conserved_transfer_no_node_minting_in_practice():
    """A live check that the fee is CONSERVED: after many well-baby visits,
    Σ(family coin + doctor coin) is unchanged (only attrs move; the seed-audit test
    proves no rule mints/destroys a node)."""
    w = _world()
    P = _pool(w)
    w.add_doctor("doc", P[0], wellbaby_fee=10.0)
    names = []
    for i in range(5):
        nm = "c%d" % i
        w.add_baby(nm, P[10 + i], coin=100.0, health=100.0)
        names.append(nm)
    everyone = names + ["doc"]
    tot0 = w.total_coin(everyone)
    for nm in names:
        w.well_baby_visit(nm)
    assert abs(w.total_coin(everyone) - tot0) < 1e-9, "Σcoin conserved across all fees"
    assert all(w.well_baby_of(nm) for nm in names)
