"""bigville R14 (block 262000) -- THE LIFE CYCLE gates: birth -> rearing ->
coming-of-age -> health -> death -> inheritance (the KEYSTONE that makes the town
an ORGANISM). Gates mirror BIGVILLE_LIFE_PREREG.md.

  * G-rearing-sets-priors (HEADLINE): a child's three foundational priors
    (world-safe / others-trust / self-worth) are set by the QUALITY OF CARE via the
    REUSED 239000 window-of-tolerance + co-regulation machinery -- well-reared ->
    SECURE, neglected -> MIS-SET; ablate care variation -> priors don't diverge
    (nurture load-bearing); nature+nurture (inherited temperament modulated).
  * G-health-is-one-mechanism: aging (chronic) = illness (acute) -- ONE health
    variable; care restores; DEATH at zero, routed.
  * G-inheritance: on death the estate (land R13 / house R7 / coin) passes to the
    heir, land conserved; the class partition persists across a generation.
  * G-no-heir -> commons: a heirless estate reverts to the council, never destroyed.
  * ETHICS (induce -> measure -> RESTORE, NO reward/punishment): the neglect arm is
    RESTORED by re-rearing; no reward/punishment token anywhere.

No life-cycle decision lives in Python -- every dysregulation / co-regulation /
widen-vs-narrow (the 239000 rules), the prior mapping (bl_come_of_age), the health
decline / recovery / DEATH (bl_age/_acute/_recover/_death), and every estate
transfer (bl_inherit_*) is a seed rule. The adapter mints nodes at ingest, delivers
world facts, arms one-shots, ticks and reads (source-audit at the foot). NO Plot/
House node is minted or destroyed by any rule; ZERO new Rust.
"""
from __future__ import annotations

import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_life_world import BigvilleLifeWorld               # noqa: E402
from worlds.bigville_time_world import DAY                             # noqa: E402


def _world():
    w = BigvilleLifeWorld(day_range=16)
    w.set_phase(DAY)
    return w


def _pool(w):
    return sorted(w._cell_at.keys())


# ============================================== G-rearing-sets-priors (HEADLINE)
def test_rearing_shapes_priors_secure_vs_misset():
    """HEADLINE: two children with the SAME inherited temperament (nat_* identical)
    -- one WELL-REARED (regulated caregiver present), one NEGLECTED (caregiver
    absent) -- end with DIVERGENT adult priors: the well-reared child SECURE (each
    prior high), the neglected child MIS-SET (each low). The 239000 safety_prior
    (WOT) moves the same direction as glass-box corroboration."""
    w = _world()
    P = _pool(w)
    nat = dict(nat_world_safe=0.5, nat_others_trust=0.5, nat_self_worth=0.5)
    w.make_person("cared", P[10], **nat)
    w.make_person("neglect", P[11], **nat)
    w.rear("cared", caregiver_present=True, regulated_caregiver=True)
    w.rear("neglect", caregiver_present=False, regulated_caregiver=True)
    w.raise_child("cared"); w.raise_child("neglect")
    w.come_of_age("cared"); w.come_of_age("neglect")

    cp, npr = w.priors_of("cared"), w.priors_of("neglect")
    for ax in ("world_safe", "others_trust", "self_worth"):
        assert cp[ax] > 0.5 > npr[ax], (
            "care shapes %s: cared %.3f must be SECURE (>0.5), neglect %.3f MIS-SET"
            % (ax, cp[ax], npr[ax]))
        assert cp[ax] > npr[ax], "the two children's %s priors must DIVERGE" % ax
    # 239000 corroboration: the window widened (secure) vs narrowed (insecure)
    assert w.window_of("cared")["safety_prior"] > w.window_of("neglect")["safety_prior"]
    assert w.window_of("cared")["widen_count"] > 0 and w.window_of("neglect")["narrow_count"] > 0
    assert w.is_adult("cared") and w.is_adult("neglect"), "both came of age"


def test_rearing_ablate_care_variation_no_divergence():
    """CONTROL (nurture load-bearing): ablate care-quality VARIATION -- give BOTH
    children the SAME inherited temperament AND the SAME (identical) care -> their
    priors are IDENTICAL (no divergence). The divergence above is caused by CARE,
    not the protocol / RNG."""
    w = _world()
    P = _pool(w)
    nat = dict(nat_world_safe=0.5, nat_others_trust=0.5, nat_self_worth=0.5)
    w.make_person("a", P[10], **nat)
    w.make_person("b", P[11], **nat)
    for nm in ("a", "b"):                     # IDENTICAL care for both
        w.rear(nm, caregiver_present=True, regulated_caregiver=True)
        w.raise_child(nm)
        w.come_of_age(nm)
    assert w.priors_of("a") == w.priors_of("b"), (
        "identical nature + identical care -> identical priors (no care divergence)")


def test_rearing_nature_modulates_nurture():
    """NATURE+NURTURE: two children with DIFFERENT inherited temperament, the SAME
    (good) care -> the higher-nature child ends higher on every axis. Care shifts
    both up by the same nurture; the inherited setpoint modulates the result."""
    w = _world()
    P = _pool(w)
    w.make_person("high", P[10], nat_world_safe=0.6, nat_others_trust=0.6, nat_self_worth=0.6)
    w.make_person("low", P[11], nat_world_safe=0.4, nat_others_trust=0.4, nat_self_worth=0.4)
    for nm in ("high", "low"):
        w.rear(nm, caregiver_present=True, regulated_caregiver=True)
        w.raise_child(nm)
        w.come_of_age(nm)
    hp, lp = w.priors_of("high"), w.priors_of("low")
    for ax in ("world_safe", "others_trust", "self_worth"):
        assert hp[ax] > lp[ax], "higher inherited %s -> higher adult %s (nature modulates)" % (ax, ax)


def test_birth_inherits_temperament_from_parent():
    """BIRTH (nature): a child born of a parent inherits the parent's priors as its
    nat_* temperament (population-distribution ~ parents)."""
    w = _world()
    P = _pool(w)
    w.make_person("parent", P[10], nat_world_safe=0.7, nat_others_trust=0.3, nat_self_worth=0.8)
    w.make_person("child", P[11], parent="parent")
    assert abs(w.nat_of("child", "world_safe") - 0.7) < 1e-9
    assert abs(w.nat_of("child", "others_trust") - 0.3) < 1e-9
    assert abs(w.nat_of("child", "self_worth") - 0.8) < 1e-9


def test_coming_of_age_mints_capability_proxy():
    """COMING-OF-AGE: a well-reared child matures with a HIGHER capability proxy
    than a neglected one (R18 school not built -> a rearing-quality PROXY, recorded
    honestly). adult=1 for both."""
    w = _world()
    P = _pool(w)
    w.make_person("cared", P[10]); w.make_person("neglect", P[11])
    w.rear("cared", caregiver_present=True, regulated_caregiver=True)
    w.rear("neglect", caregiver_present=False, regulated_caregiver=True)
    w.raise_child("cared"); w.raise_child("neglect")
    w.come_of_age("cared"); w.come_of_age("neglect")
    assert w.capability_of("cared") > w.capability_of("neglect")


# ============================================== G-health-is-one-mechanism
def test_aging_alone_kills_by_age():
    """CONTROL: with NO acute events, chronic aging ALONE drives health to zero ->
    death by AGING (death_cause=1). One variable, the slow arm."""
    w = _world()
    P = _pool(w)
    w.make_person("elder", P[10]); w.endow_health("elder", health=5.0, age_rate=1.0)
    for _ in range(6):
        w.age_period(["elder"])
        if w.is_dead("elder"):
            break
    assert w.is_dead("elder"), "aging alone reaches death"
    assert w.death_cause_of("elder") == 1, "death by aging is cause 1"


def test_illness_is_acute_and_recoverable():
    """aging = illness: an ACUTE drop uses the SAME health variable (bl_acute), and
    care RESTORES it (bl_recover) -- recoverable, the R3 collapse-spiral shape."""
    w = _world()
    P = _pool(w)
    w.make_person("sick", P[10]); w.endow_health("sick", health=100.0, max_health=100.0)
    w.afflict("sick", 40.0, cause=2.0)
    assert abs(w.health_of("sick") - 60.0) < 1e-9 and not w.is_dead("sick")
    w.treat("sick", 30.0)
    assert abs(w.health_of("sick") - 90.0) < 1e-9, "care restores the SAME variable"
    w.treat("sick", 999.0)
    assert abs(w.health_of("sick") - 100.0) < 1e-9, "capped at max_health"


def test_acute_route_can_kill_and_is_tagged():
    """A large acute event drives health<=0 -> DEATH, routed by cause (starvation=3,
    exhaustion=4) -- the fifth-and-friends routes all funnel through health<=0."""
    w = _world()
    P = _pool(w)
    w.make_person("starved", P[10]); w.endow_health("starved", health=20.0)
    w.afflict("starved", 25.0, cause=3.0)
    assert w.is_dead("starved") and w.death_cause_of("starved") == 3


def test_care_slows_the_decline_control():
    """CONTROL: ablate care (no bl_recover) -> FASTER decline. The cared arm (aging
    + periodic care) survives more periods than the un-cared arm (aging alone)."""
    w = _world()
    P = _pool(w)
    w.make_person("cared", P[10]); w.endow_health("cared", health=10.0, age_rate=2.0)
    w.make_person("uncared", P[11]); w.endow_health("uncared", health=10.0, age_rate=2.0)
    cared_periods = uncared_periods = 0
    for _ in range(20):
        if not w.is_dead("cared"):
            w.age_period(["cared"]); w.treat("cared", 1.0)   # care offsets some decline
            if not w.is_dead("cared"):
                cared_periods += 1
        if not w.is_dead("uncared"):
            w.age_period(["uncared"])                         # no care
            if not w.is_dead("uncared"):
                uncared_periods += 1
    assert cared_periods > uncared_periods, "care slows the decline (survives longer)"


# ============================================== G-inheritance -> intergenerational
def test_inheritance_transfers_land_house_coin_conserved():
    """HEADLINE: on death the estate (LAND R13 + house R7 + coin) passes to the
    heir; Sigma(Plot) is CONSERVED (only owns edges move, no Plot minted/destroyed)."""
    w = _world()
    P = _pool(w)
    w.make_person("council", P[0]); w.set_council("council")
    w.make_person("rich", P[10], coin=500.0); w.endow_health("rich", health=100.0)
    w.make_person("kid", P[11], coin=10.0)
    w.add_plot("estate"); w.own_plot("rich", "estate")
    w.add_house("manor", 200); w.own("rich", "manor")
    w.link_commons("rich"); w.set_heir("rich", "kid")
    N0 = w.total_plots()
    w.die("rich", cause=2.0)
    assert w.is_dead("rich")
    assert w.owner_of("estate") == "kid", "the LAND passes to the heir"
    assert w.owns_house("kid", "manor"), "the HOUSE passes to the heir"
    assert abs(w.coin_of("kid") - 510.0) < 1e-9 and abs(w.coin_of("rich")) < 1e-9, "coin passes"
    assert w.total_plots() == N0, "Sigma(Plot) conserved -- the land moved, not destroyed"


def test_class_partition_persists_across_generation():
    """INTERGENERATIONAL INEQUALITY: a LANDED parent's heir stays LANDED; a LANDLESS
    parent's heir stays LANDLESS -> the land-holding partition (its Gini) PERSISTS
    across the generation (you inherit your class)."""
    w = _world()
    P = _pool(w)
    w.make_person("council", P[0]); w.set_council("council")
    # a landed lineage and a landless lineage
    w.make_person("baron", P[10]); w.endow_health("baron", health=100.0)
    w.make_person("baron_heir", P[11])
    w.make_person("pauper", P[12]); w.endow_health("pauper", health=100.0)
    w.make_person("pauper_heir", P[13])
    for i in range(4):
        w.add_plot("b%d" % i); w.own_plot("baron", "b%d" % i)   # the baron holds all land
    for nm in ("baron", "pauper"):
        w.link_commons(nm)
    w.set_heir("baron", "baron_heir"); w.set_heir("pauper", "pauper_heir")
    gini_before = w.gini_land(["baron", "pauper"])
    w.die("baron", cause=1.0); w.die("pauper", cause=1.0)
    assert w.plots_held("baron_heir") == 4, "the landed heir stays landed"
    assert w.plots_held("pauper_heir") == 0, "the landless heir stays landless"
    gini_after = w.gini_land(["baron_heir", "pauper_heir"])
    assert abs(gini_after - gini_before) < 1e-9, "the class partition (Gini) persists"


def test_death_off_immortal_no_transfer_control():
    """CONTROL (death-is-the-reset, ties R10 -- the local perturbation arm): with
    death OFF (immortal, dead never set) the estate NEVER transfers -- the fixpoint
    is immortal; running the rules leaves every owns edge + coin unchanged."""
    w = _world()
    P = _pool(w)
    w.make_person("council", P[0]); w.set_council("council")
    w.make_person("owner", P[10], coin=100.0); w.endow_health("owner", health=100.0)
    w.make_person("kid", P[11], coin=0.0)
    w.add_plot("e"); w.own_plot("owner", "e")
    w.link_commons("owner"); w.set_heir("owner", "kid")
    w._run()                                   # run WITHOUT death
    assert w.owner_of("e") == "owner", "immortal owner keeps the land (no transfer)"
    assert w.coin_of("kid") == 0.0, "no coin passes while the owner lives"


# ============================================== G-no-heir -> commons
def test_no_heir_reverts_to_commons():
    """A dead owner with NO heir -> the estate REVERTS to the council / commons
    (never destroyed); Sigma(Plot) conserved. Ties R13 conservation."""
    w = _world()
    P = _pool(w)
    w.make_person("council", P[0]); w.set_council("council")
    w.make_person("lonely", P[10], coin=99.0); w.endow_health("lonely", health=100.0)
    w.add_plot("waste"); w.own_plot("lonely", "waste")
    w.add_house("hut", 50); w.own("lonely", "hut")
    w.link_commons("lonely")                    # no set_heir -> has_heir stays 0
    N0 = w.total_plots()
    w.die("lonely", cause=3.0)
    assert w.owner_of("waste") == "council", "heirless LAND reverts to the commons"
    assert w.owns_house("council", "hut"), "heirless HOUSE reverts to the commons"
    assert abs(w.coin_of("council") - 99.0) < 1e-9, "heirless coin escheats to the commons"
    assert w.total_plots() == N0, "Sigma(Plot) conserved -- reverted, not destroyed"


def test_heir_beats_commons_branch():
    """CONTROL: the SAME dead owner WITH an heir -> the estate goes to the HEIR, not
    the commons (the heir vs no-heir branch is the rule's decision, disjoint)."""
    w = _world()
    P = _pool(w)
    w.make_person("council", P[0]); w.set_council("council")
    w.make_person("owner", P[10], coin=40.0); w.endow_health("owner", health=100.0)
    w.make_person("kid", P[11], coin=0.0)
    w.add_plot("field"); w.own_plot("owner", "field")
    w.link_commons("owner"); w.set_heir("owner", "kid")
    w.die("owner", cause=2.0)
    assert w.owner_of("field") == "kid", "with an heir the estate goes to the heir"
    assert w.plots_held("council") == 0, "the commons does NOT receive when an heir exists"
    assert abs(w.coin_of("kid") - 40.0) < 1e-9


# ============================================== ETHICS (induce -> measure -> RESTORE)
def test_ethics_neglect_is_restored_by_rerearing():
    """ETHICS: the neglect arm INDUCES a mis-set (narrow window / low safety);
    RESTORE by re-rearing under a regulated caregiver widens the window BACK toward
    secure (induce -> measure -> RESTORE). Dysregulation is a STATE, reversed, never
    a punishment."""
    w = _world()
    P = _pool(w)
    w.make_person("child", P[10])
    w.rear("child", caregiver_present=False, regulated_caregiver=True)   # INDUCE
    w.raise_child("child", episodes=8)
    harmed = w.window_of("child")
    assert harmed["narrow_count"] > 0 and harmed["safety_prior"] < 0.5, "harm induced + measured"
    w.attend("child", regulated=True)                                    # RESTORE
    w.raise_child("child", episodes=12)
    restored = w.window_of("child")
    assert restored["half_width"] > harmed["half_width"], "re-rearing widens the window back"
    assert restored["safety_prior"] > harmed["safety_prior"], "safety prior recovers"


# ============================================== source-audit + discipline
def _strip_py(src: str) -> str:
    src = re.sub(r'"""[\s\S]*?"""', "", src)
    src = re.sub(r"'''[\s\S]*?'''", "", src)
    src = re.sub(r"#.*", "", src)
    src = re.sub(r'"[^"\n]*"', '""', src)
    src = re.sub(r"'[^'\n]*'", "''", src)
    return src


def test_no_python_agent_decision_source_audit():
    """Every life-cycle DECISION is a seed rule, not Python. The adapter mints nodes
    at ingest, delivers world facts, arms one-shots, ticks and reads -- it never
    COMPUTES a prior / health / death / inheritance outcome in Python, and runs no
    Python rule engine. And NO reward/punishment token (a prior/illness/death is a
    STATE, never a badness -- Greene)."""
    import json
    world_src = open(os.path.join(_ROOT, "worlds", "bigville_life_world.py")).read()
    # strip the mechanical DEFAULTS dicts (opaque attr names, not decisions)
    for pat in (r"LIFE_DEFAULTS\s*=\s*dict\([\s\S]*?\)\n",
                r"PERSON_DEFAULTS\s*=\s*dict\([\s\S]*?\)\n"):
        world_src = re.sub(pat, "", world_src, count=1)
    code = _strip_py(world_src)
    for banned in ("graph_rewrite", "gr._match", "gr._apply", "make_rule", "add_rule"):
        assert banned not in code, "adapter must not run/author the Python rule engine"
    for token in ("reward", "punish", "penalty", "penalis", "penaliz"):
        assert token not in code.lower(), "NO reward/punishment token (%s)" % token
    # the DECISION PARAMETERS appear ONLY in the seeds -- the adapter never branches
    # on them (opaque attrs it sets by name in ingest).
    for param in ("widen_count", "narrow_count", "has_heir", "coin_bequeathed",
                  "last_cause", "death_cause"):
        assert ("if " + param) not in code, \
            "decision parameter %s must live in a rule `where`, not an adapter branch" % param


def test_seeds_are_named_self_load_only_and_conserve_estate():
    """Discipline at the source level: the three seeds are self_load_only (loaded
    ONLY by the R14 adapter -> cannot regress another suite); the rule set is exactly
    the eleven named life-cycle decisions; NO inheritance rule mints or destroys a
    node (no add_node/del_node -> the estate is CONSERVED, only edges move); no coin
    attr set from a fractional Div; NO new Rust."""
    import json
    seeds = {sid: json.load(open(os.path.join(_ROOT, "seeds", sid + ".json")))
             for sid in ("bigville_life_rearing", "bigville_life_health",
                         "bigville_life_inheritance")}
    for sid, s in seeds.items():
        assert s.get("self_load_only") is True, "%s must be self_load_only" % sid
        assert s.get("depends_on") == [], "%s declares no seed deps (reuse by import)" % sid
    names = {r["name"] for s in seeds.values() for r in s["rules"]}
    assert names == {
        "bl_come_of_age",
        "bl_age", "bl_acute", "bl_recover", "bl_death",
        "bl_inherit_land", "bl_inherit_house", "bl_inherit_coin",
        "bl_inherit_commons_land", "bl_inherit_commons_house", "bl_inherit_commons_coin",
    }, "the eleven life-cycle decisions are RULES"
    inh = seeds["bigville_life_inheritance"]
    both = json.dumps(inh)
    assert '"add_node"' not in both and '"del_node"' not in both, \
        "no inheritance rule adds/removes a node -- the estate is CONSERVED, edges move"
    for s in seeds.values():
        for r in s["rules"]:
            for eff in r.get("effects", []):
                assert eff[0] not in ("add_node", "del_node"), \
                    "%s mints/destroys a node" % r["name"]
                if eff[0] == "set_attr" and len(eff) > 2 and eff[2] in ("coin", "reserves", "balance"):
                    assert '"Div"' not in json.dumps(eff), "coin never set from a fractional Div"


def test_no_reward_punishment_in_seeds():
    """ETHICS at the seed level: no reward/punishment token in the RULE LOGIC of any
    life seed (a mis-set prior, illness, death are STATES, never a badness). The
    check is scoped to the rules (attr names / effects / Terms), not the seed's prose
    description -- which legitimately DISCUSSES the ethics protocol."""
    import json
    for sid in ("bigville_life_rearing", "bigville_life_health", "bigville_life_inheritance"):
        seed = json.load(open(os.path.join(_ROOT, "seeds", sid + ".json")))
        blob = json.dumps(dict(rules=seed["rules"], nodes=seed.get("nodes", []),
                               edges=seed.get("edges", []),
                               concepts=seed.get("concepts", []))).lower()
        for token in ("reward", "punish", "penalty"):
            assert token not in blob, "%s rule logic carries a %s token" % (sid, token)
