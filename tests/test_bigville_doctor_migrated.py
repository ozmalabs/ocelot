"""bigville R22 (block 270000) -- THE DOCTOR gates: preventive care + treatment,
health as a MONEY-GATED market good. Gates mirror BIGVILLE_DOCTOR_PREREG.md.

  * G-doctor-is-paid: seeing the doctor MOVES coin patient->doctor (CONSERVED);
    the doctor draws income. Ablate coin -> can't afford -> NO care.
  * G-preventive-detection: a SCREENED patient (checkup before onset) suffers a
    SMALLER acute drop than an unscreened one struck by the SAME disease.
  * G-treatment-reduces-severity/length: a TREATED patient suffers a smaller drop
    AND recovers to full in FEWER ticks; ablate treatment -> full R14 trajectory.
  * G-treatment-prevents-death: a severe disease that KILLS the untreated is
    SURVIVED by the treated (drop reduced below health).
  * G-health-inequality (HEADLINE): the poor can't afford care -> DIE; the rich
    afford it -> SURVIVE the SAME illness. Public health (treasury pays) DISSOLVES
    the gradient -- the systemic lever.
  * ETHICS (induce -> measure -> RESTORE, NO reward/punishment): illness is
    induced + measured, then RESTORED by treatment / public provision.

Every doctor DECISION is a seed rule (bd_*): affordability, the early-detection
effect, the treatment severity / death modulation, recovery rate, and the
public-vs-private branch. The adapter mints nodes, wires edges, arms one-shots,
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

from worlds.bigville_doctor_world import BigvilleDoctorWorld           # noqa: E402
from worlds.bigville_time_world import DAY                             # noqa: E402


def _world():
    w = BigvilleDoctorWorld(day_range=16)
    w.set_phase(DAY)
    return w


def _pool(w):
    return sorted(w._cell_at.keys())


# ============================================== G-doctor-is-paid (market health)
def test_doctor_is_paid_conserved_transfer():
    """HEADLINE of the market: seeing the doctor COSTS coin -- a CONSERVED transfer
    (patient loses exactly what the doctor gains). The doctor DRAWS INCOME."""
    w = _world()
    P = _pool(w)
    w.add_doctor("doc", P[0], checkup_fee=10.0, treat_fee=30.0)
    w.admit("rich", P[10], coin=100.0, health=100.0)
    tot0 = w.total_coin(["rich", "doc"])
    dc0 = w.doctor_coin()
    w.seek_care("rich")
    assert w.treated_of("rich"), "the paying patient is treated"
    assert abs(w.coin_of("rich") - 70.0) < 1e-9, "patient pays the treat_fee"
    assert abs(w.doctor_coin() - dc0 - 30.0) < 1e-9, "the doctor draws the fee as income"
    assert abs(w.total_coin(["rich", "doc"]) - tot0) < 1e-9, "coin CONSERVED (a transfer)"


def test_checkup_is_paid_conserved():
    """A preventive CHECKUP is also fee-for-service (a conserved transfer)."""
    w = _world()
    P = _pool(w)
    w.add_doctor("doc", P[0], checkup_fee=10.0, treat_fee=30.0)
    w.admit("p", P[10], coin=50.0)
    tot0 = w.total_coin(["p", "doc"])
    w.checkup("p")
    assert w.screened_of("p")
    assert abs(w.coin_of("p") - 40.0) < 1e-9 and abs(w.doctor_coin() - 10.0) < 1e-9
    assert abs(w.total_coin(["p", "doc"]) - tot0) < 1e-9


def test_ablate_coin_no_care():
    """CONTROL (money-gating): a patient who CANNOT afford the fee (coin < fee) gets
    NO care -- bd_treat / bd_checkup do not fire, coin unchanged, screened/treated
    stay 0. The marshmallow dissolution: it is AFFORDABILITY, not myopia."""
    w = _world()
    P = _pool(w)
    w.add_doctor("doc", P[0], checkup_fee=10.0, treat_fee=30.0)
    w.admit("pauper", P[10], coin=5.0, health=100.0)
    w.checkup("pauper"); w.seek_care("pauper")
    assert not w.screened_of("pauper"), "can't afford the checkup -> not screened"
    assert not w.treated_of("pauper"), "can't afford treatment -> not treated"
    assert abs(w.coin_of("pauper") - 5.0) < 1e-9, "no fee charged (no care happened)"
    assert abs(w.doctor_coin()) < 1e-9, "the doctor earned nothing from the pauper"


# ============================================== G-preventive-detection (screening)
def test_preventive_detection_smaller_drop():
    """A SCREENED patient (paid checkup before onset) avoids the progression
    penalty -> SMALLER acute drop than an UNSCREENED patient struck by the SAME
    disease. Control: no checkup -> the disease progresses -> LARGER drop."""
    w = _world()
    P = _pool(w)
    w.add_doctor("doc", P[0], checkup_fee=10.0, treat_fee=30.0)
    w.admit("screened", P[10], coin=100.0, health=100.0, progression=30.0)
    w.admit("missed", P[11], coin=100.0, health=100.0, progression=30.0)
    w.checkup("screened")               # pays -> screened=1
    # 'missed' does NOT get a checkup (the control)
    assert w.screened_of("screened") and not w.screened_of("missed")
    w.strike("screened", 20.0); w.strike("missed", 20.0)   # SAME disease
    assert abs(w.health_of("screened") - 80.0) < 1e-9, "early-detected: base drop only (20)"
    assert abs(w.health_of("missed") - 50.0) < 1e-9, "undetected: base + progression (50)"
    assert w.health_of("screened") > w.health_of("missed"), "screening -> better outcome"


# ============================================== G-treatment-reduces-severity/length
def test_treatment_reduces_severity():
    """A TREATED patient suffers a SMALLER acute drop than an untreated one struck
    by the SAME disease (treatment caps the acute arm)."""
    w = _world()
    P = _pool(w)
    w.add_doctor("doc", P[0], checkup_fee=10.0, treat_fee=30.0)
    w.admit("treated", P[10], coin=100.0, health=100.0, progression=0.0, treat_relief=15.0)
    w.admit("untreated", P[11], coin=0.0, health=100.0, progression=0.0, treat_relief=15.0)
    w.seek_care("treated")              # pays -> treated=1
    assert w.treated_of("treated") and not w.treated_of("untreated")
    w.strike("treated", 40.0); w.strike("untreated", 40.0)
    assert abs(w.health_of("treated") - 75.0) < 1e-9, "treated: 40 - 15 relief = 25 drop"
    assert abs(w.health_of("untreated") - 60.0) < 1e-9, "untreated: full 40 drop"
    assert w.health_of("treated") > w.health_of("untreated")


def test_treatment_faster_recovery_length():
    """A TREATED patient recovers to full health in FEWER ticks (shorter illness)
    than an untreated one -- the LENGTH arm (doctor_care fast vs natural_care
    slow). Same acute drop isolated (treat_relief=0) so only recovery differs."""
    w = _world()
    P = _pool(w)
    w.add_doctor("doc", P[0], checkup_fee=10.0, treat_fee=30.0)
    w.admit("t", P[10], coin=100.0, health=100.0, doctor_care=40.0, natural_care=5.0)
    w.admit("u", P[11], coin=0.0, health=100.0, doctor_care=40.0, natural_care=5.0)
    w.seek_care("t")                    # treated (relief 0 -> same drop as u)
    w.strike("t", 60.0, progression=0.0, treat_relief=0.0)
    w.strike("u", 60.0, progression=0.0, treat_relief=0.0)
    assert abs(w.health_of("t") - w.health_of("u")) < 1e-9, "same acute drop"
    t_ticks = w.recover_to_full("t")
    u_ticks = w.recover_to_full("u")
    assert t_ticks < u_ticks, "treated recovers in fewer ticks (shorter illness)"


def test_ablate_treatment_full_trajectory():
    """CONTROL: with treatment ablated (no seek_care) the illness runs the FULL R14
    trajectory -- the acute drop is the base disease, unmodulated."""
    w = _world()
    P = _pool(w)
    w.add_doctor("doc", P[0], checkup_fee=10.0, treat_fee=30.0)
    w.admit("x", P[10], coin=100.0, health=100.0, progression=0.0, treat_relief=40.0)
    w.strike("x", 35.0)                 # no checkup, no treatment
    assert abs(w.health_of("x") - 65.0) < 1e-9, "full base drop, no doctor modulation"


# ============================================== G-treatment-prevents-death
def test_treatment_prevents_death():
    """A SEVERE disease that drives an untreated patient to health<=0 (DIES, R14
    bl_death) is SURVIVED by a treated one (relief keeps the drop below health).
    The R14 death-at-zero, now intervenable by the doctor."""
    w = _world()
    P = _pool(w)
    w.add_doctor("doc", P[0], checkup_fee=10.0, treat_fee=30.0)
    w.admit("saved", P[10], coin=100.0, health=40.0, progression=0.0, treat_relief=40.0)
    w.admit("lost", P[11], coin=0.0, health=40.0, progression=0.0, treat_relief=40.0)
    w.seek_care("saved")               # affords treatment
    w.seek_care("lost")                # can't afford -> untreated
    assert w.treated_of("saved") and not w.treated_of("lost")
    w.strike("saved", 50.0); w.strike("lost", 50.0)   # SAME severe disease
    assert not w.is_dead("saved"), "treatment prevents death (drop 50-40=10 < health 40)"
    assert w.is_dead("lost"), "untreated: full drop 50 >= health 40 -> DIES"
    assert w.death_cause_of("lost") == 2, "death routed as illness (cause 2)"


# ============================================== G-health-inequality (HEADLINE)
def _cohort(w, P, coins, *, health=40.0, base=50.0):
    """A cohort with a WEALTH gradient, otherwise identical. Returns the names."""
    names = []
    for i, c in enumerate(coins):
        nm = "r%d" % i
        w.admit(nm, P[10 + i], coin=float(c), health=health,
                progression=0.0, treat_relief=40.0)
        names.append(nm)
    return names


def test_health_inequality_tracks_wealth():
    """HEADLINE: health is money-gated, so health inequality TRACKS wealth
    inequality. A wealth gradient meets ONE disease striking all: the POOR (coin <
    treat_fee) can't afford care -> DIE; the RICH afford it -> SURVIVE the SAME
    illness. The poor die of a TREATABLE illness, having done nothing wrong."""
    w = _world()
    P = _pool(w)
    w.add_doctor("doc", P[0], checkup_fee=10.0, treat_fee=30.0)
    coins = [0.0, 5.0, 10.0, 20.0, 29.0, 30.0, 50.0, 100.0]
    names = _cohort(w, P, coins)
    for nm in names:
        w.seek_care(nm)
    for nm in names:
        w.strike(nm, 50.0)              # the SAME severe disease for everyone
    for nm, c in zip(names, coins):
        if c >= 30.0:
            assert not w.is_dead(nm), "the rich (coin %s) survive the SAME illness" % c
        else:
            assert w.is_dead(nm), "the poor (coin %s) die of a TREATABLE illness" % c
    dead = sum(w.is_dead(nm) for nm in names)
    alive = len(names) - dead
    # survival is monotone in wealth: the survivors are exactly the wealthiest.
    survivors_wealth = [c for nm, c in zip(names, coins) if not w.is_dead(nm)]
    assert min(survivors_wealth) >= 30.0, "every survivor could afford the fee"
    assert dead == 5 and alive == 3, "5 poor die, 3 rich survive (money-gated health)"


def test_public_health_dissolves_the_gradient():
    """THE STRUCTURAL LEVER (agency/structure bedrock): flip council-funded PUBLIC
    HEALTH on (the treasury pays the doctor) -> the SAME poor cohort meeting the
    SAME disease now ALL survive. The wealth-health gradient VANISHES -- only a
    systemic lever saves the poor, never personal effort."""
    w = _world()
    P = _pool(w)
    w.add_doctor("doc", P[0], checkup_fee=10.0, treat_fee=30.0)
    w.add_treasury(10000.0)
    coins = [0.0, 5.0, 10.0, 20.0, 29.0, 30.0, 50.0, 100.0]
    names = _cohort(w, P, coins)
    w.set_public_health(True, names)   # THE LEVER
    f0 = w.treasury_funds()
    for nm in names:
        w.seek_care(nm)
    for nm in names:
        w.strike(nm, 50.0)
    for nm, c in zip(names, coins):
        assert w.treated_of(nm), "public health treats even the coin-0 poor (%s)" % c
        assert not w.is_dead(nm), "under public health, the poor survive (%s)" % c
    # the poor paid NOTHING out of pocket; the treasury bore the cost (conserved).
    for nm, c in zip(names, coins):
        assert abs(w.coin_of(nm) - c) < 1e-9, "no out-of-pocket fee under public health"
    assert abs(f0 - w.treasury_funds() - 30.0 * len(names)) < 1e-9, \
        "the treasury paid the full cost (a conserved public transfer)"


# ============================================== ETHICS (induce -> measure -> RESTORE)
def test_ethics_illness_is_restored_by_treatment():
    """ETHICS: illness INDUCES a health drop (a harm-analog STATE, measured), then
    is RESTORED by TREATMENT + recovery back to full health (induce -> measure ->
    RESTORE). The restore is care / provision, NOT a reward -- health is a STATE,
    reversed, never a badness."""
    w = _world()
    P = _pool(w)
    w.add_doctor("doc", P[0], checkup_fee=10.0, treat_fee=30.0)
    w.admit("patient", P[10], coin=100.0, health=100.0, max_health=100.0,
            progression=0.0, treat_relief=0.0, doctor_care=40.0)
    w.strike("patient", 60.0)                       # INDUCE
    assert abs(w.health_of("patient") - 40.0) < 1e-9 and not w.is_dead("patient"), "harm induced + measured"
    w.seek_care("patient")                          # RESTORE (treatment)
    ticks = w.recover_to_full("patient")
    assert abs(w.health_of("patient") - 100.0) < 1e-9, "treatment RESTORES health to full"
    assert ticks > 0


def test_ethics_public_provision_restores_the_poor_cohort():
    """ETHICS at the structural scale: the poor cohort left to die (induce +
    measure) is RESTORED not by personal effort but by PUBLIC PROVISION -- the same
    disease, with public health on, no longer kills them. The restore is a systemic
    lever, not reward/punishment."""
    w = _world()
    P = _pool(w)
    w.add_doctor("doc", P[0], checkup_fee=10.0, treat_fee=30.0)
    w.add_treasury(10000.0)
    # INDUCE + MEASURE: a poor cohort with NO public health dies.
    poor = _cohort(w, P, [0.0, 5.0, 10.0])
    for nm in poor:
        w.seek_care(nm)
    for nm in poor:
        w.strike(nm, 50.0)
    assert all(w.is_dead(nm) for nm in poor), "harm induced: the poor die untreated"
    # RESTORE: a fresh IDENTICAL poor cohort under PUBLIC PROVISION survives.
    poor2 = []
    for i, c in enumerate([0.0, 5.0, 10.0]):
        nm = "q%d" % i
        w.admit(nm, P[20 + i], coin=float(c), health=40.0, progression=0.0, treat_relief=40.0)
        poor2.append(nm)
    w.set_public_health(True, poor2)
    for nm in poor2:
        w.seek_care(nm)
    for nm in poor2:
        w.strike(nm, 50.0)
    assert all(not w.is_dead(nm) for nm in poor2), "public provision RESTORES the poor"


# ============================================== source-audit + discipline
def _strip_py(src: str) -> str:
    src = re.sub(r'"""[\s\S]*?"""', "", src)
    src = re.sub(r"'''[\s\S]*?'''", "", src)
    src = re.sub(r"#.*", "", src)
    src = re.sub(r'"[^"\n]*"', '""', src)
    src = re.sub(r"'[^'\n]*'", "''", src)
    return src


def test_no_python_agent_decision_source_audit():
    """Every doctor DECISION is a seed rule, not Python. The adapter mints nodes,
    wires edges, delivers world facts, arms one-shots, ticks and reads -- it never
    COMPUTES whether care happens / a drop / a death / a recovery in Python, and
    runs no Python rule engine. NO reward/punishment token."""
    world_src = open(os.path.join(_ROOT, "worlds", "bigville_doctor_world.py")).read()
    # strip the mechanical DEFAULTS dict (opaque attr names, not decisions).
    world_src = re.sub(r"CARE_DEFAULTS\s*=\s*dict\([\s\S]*?\)\n", "", world_src, count=1)
    code = _strip_py(world_src)
    for banned in ("graph_rewrite", "gr._match", "gr._apply", "make_rule", "add_rule"):
        assert banned not in code, "adapter must not run/author the Python rule engine"
    for token in ("reward", "punish", "penalty", "penalis", "penaliz"):
        assert token not in code.lower(), "NO reward/punishment token (%s)" % token
    # the rule-DECISION outcomes appear only in the seed -- the adapter never
    # branches on them (opaque attrs it sets by name in ingest).
    for param in ("screened", "treated", "public_health", "illness_amount",
                  "disease_armed", "checkup_armed", "treat_armed"):
        assert ("if " + param) not in code, \
            "decision parameter %s must live in a rule `where`, not an adapter branch" % param


def test_seed_is_self_load_only_and_named():
    """Discipline at the source: the doctor seed is self_load_only (loaded ONLY by
    the R22 adapter -> cannot regress another suite), declares no deps, and its rule
    set is EXACTLY the six named doctor decisions. No rule mints/destroys a node
    (conservation); coin never set from a fractional Div; NO new Rust."""
    import json
    s = json.load(open(os.path.join(_ROOT, "seeds", "bigville_doctor_care.json")))
    assert s.get("self_load_only") is True, "the seed must be self_load_only"
    assert s.get("depends_on") == [], "no seed deps (reuse R14/R7/R9 by import)"
    names = {r["name"] for r in s["rules"]}
    assert names == {
        "bd_checkup", "bd_checkup_public",
        "bd_treat", "bd_treat_public",
        "bd_onset", "bd_recover",
    }, "the six doctor decisions are RULES"
    for r in s["rules"]:
        for eff in r.get("effects", []):
            assert eff[0] not in ("add_node", "del_node"), \
                "%s mints/destroys a node (must conserve)" % r["name"]
            if eff[0] == "set_attr" and len(eff) > 2 and eff[2] in ("coin", "funds"):
                assert '"Div"' not in json.dumps(eff), "coin/funds never set from a fractional Div"


def test_no_reward_punishment_in_seed():
    """ETHICS at the seed level: no reward/punishment token in the RULE LOGIC (an
    illness / death is a STATE, never a badness). Scoped to the rules, not the
    seed's prose description (which legitimately discusses the ethics protocol)."""
    import json
    s = json.load(open(os.path.join(_ROOT, "seeds", "bigville_doctor_care.json")))
    blob = json.dumps(dict(rules=s["rules"], nodes=s.get("nodes", []),
                           edges=s.get("edges", []),
                           concepts=s.get("concepts", []))).lower()
    for token in ("reward", "punish", "penalty"):
        assert token not in blob, "rule logic carries a %s token" % token


def test_conserved_transfer_no_node_minting_in_practice():
    """A live check that the fee is CONSERVED: after many checkups + treatments,
    Σ(patient coin + doctor coin) is unchanged (only attrs move; the seed-audit
    test proves no rule mints/destroys a node)."""
    w = _world()
    P = _pool(w)
    w.add_doctor("doc", P[0], checkup_fee=10.0, treat_fee=30.0)
    names = []
    for i in range(5):
        nm = "c%d" % i
        w.admit(nm, P[10 + i], coin=100.0, health=100.0)
        names.append(nm)
    everyone = names + ["doc"]
    tot0 = w.total_coin(everyone)
    for nm in names:
        w.checkup(nm); w.seek_care(nm)
    assert abs(w.total_coin(everyone) - tot0) < 1e-9, "Σcoin conserved across all fees"
    assert all(w.screened_of(nm) and w.treated_of(nm) for nm in names)
