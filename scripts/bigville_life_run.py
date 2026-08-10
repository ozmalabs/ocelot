#!/usr/bin/env python3
"""bigville R14 (block 262000) THE LIFE CYCLE runner: mint -> ingest -> run_rules
-> read-off. Drives `worlds/bigville_life_world.py` through the four gates and
emits `results/bigville_life/summary.json` (the glass-box findings + the honest
residuals + the deferrals). NO decision here -- every life-cycle outcome is a seed
rule; the runner delivers world facts and reads graph state back.

Protocol frozen in BIGVILLE_LIFE_PREREG.md.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from worlds.bigville_life_world import BigvilleLifeWorld              # noqa: E402
from worlds.bigville_time_world import DAY                            # noqa: E402


def _world():
    w = BigvilleLifeWorld(day_range=16)
    w.set_phase(DAY)
    return w


def g_rearing():
    w = _world()
    P = sorted(w._cell_at.keys())
    nat = dict(nat_world_safe=0.5, nat_others_trust=0.5, nat_self_worth=0.5)
    w.make_person("cared", P[10], **nat)
    w.make_person("neglect", P[11], **nat)
    w.rear("cared", caregiver_present=True, regulated_caregiver=True)
    w.rear("neglect", caregiver_present=False, regulated_caregiver=True)
    w.raise_child("cared"); w.raise_child("neglect")
    w.come_of_age("cared"); w.come_of_age("neglect")
    return dict(
        cared_priors=w.priors_of("cared"), neglect_priors=w.priors_of("neglect"),
        cared_window=w.window_of("cared"), neglect_window=w.window_of("neglect"),
        cared_capability=w.capability_of("cared"),
        neglect_capability=w.capability_of("neglect"),
        diverges=all(w.priors_of("cared")[a] > 0.5 > w.priors_of("neglect")[a]
                     for a in ("world_safe", "others_trust", "self_worth")))


def g_rearing_control():
    w = _world()
    P = sorted(w._cell_at.keys())
    nat = dict(nat_world_safe=0.5, nat_others_trust=0.5, nat_self_worth=0.5)
    w.make_person("a", P[10], **nat); w.make_person("b", P[11], **nat)
    for nm in ("a", "b"):
        w.rear(nm, caregiver_present=True, regulated_caregiver=True)
        w.raise_child(nm); w.come_of_age(nm)
    return dict(a_priors=w.priors_of("a"), b_priors=w.priors_of("b"),
                identical=(w.priors_of("a") == w.priors_of("b")))


def g_health():
    w = _world()
    P = sorted(w._cell_at.keys())
    w.make_person("elder", P[10]); w.endow_health("elder", health=5.0, age_rate=1.0)
    aged = 0
    for _ in range(6):
        w.age_period(["elder"]); aged += 1
        if w.is_dead("elder"):
            break
    w.make_person("sick", P[11]); w.endow_health("sick", health=100.0)
    w.afflict("sick", 40.0, cause=2.0); after_illness = w.health_of("sick")
    w.treat("sick", 30.0); after_treat = w.health_of("sick")
    return dict(
        aged_periods_to_death=aged, aging_death_cause=w.death_cause_of("elder"),
        illness_health=after_illness, recovered_health=after_treat,
        recoverable=(after_treat > after_illness),
        aging_equals_illness="one health variable, chronic vs acute delta")


def g_inheritance():
    w = _world()
    P = sorted(w._cell_at.keys())
    w.make_person("council", P[0]); w.set_council("council")
    w.make_person("baron", P[10], coin=500.0); w.endow_health("baron", health=100.0)
    w.make_person("baron_heir", P[11], coin=0.0)
    w.make_person("pauper", P[12], coin=0.0); w.endow_health("pauper", health=100.0)
    w.make_person("pauper_heir", P[13], coin=0.0)
    for i in range(4):
        w.add_plot("b%d" % i); w.own_plot("baron", "b%d" % i)
    w.add_house("manor", 200); w.own("baron", "manor")
    for nm in ("baron", "pauper"):
        w.link_commons(nm)
    w.set_heir("baron", "baron_heir"); w.set_heir("pauper", "pauper_heir")
    N0 = w.total_plots()
    gini_before = w.gini_land(["baron", "pauper"])
    w.die("baron", cause=1.0); w.die("pauper", cause=1.0)
    gini_after = w.gini_land(["baron_heir", "pauper_heir"])
    return dict(
        baron_heir_land=w.plots_held("baron_heir"),
        pauper_heir_land=w.plots_held("pauper_heir"),
        baron_heir_coin=w.coin_of("baron_heir"),
        heir_gets_house=w.owns_house("baron_heir", "manor"),
        plots_before=N0, plots_after=w.total_plots(), land_conserved=(w.total_plots() == N0),
        gini_before=gini_before, gini_after=gini_after,
        class_persists=(abs(gini_after - gini_before) < 1e-9))


def g_no_heir_commons():
    w = _world()
    P = sorted(w._cell_at.keys())
    w.make_person("council", P[0]); w.set_council("council")
    w.make_person("lonely", P[10], coin=99.0); w.endow_health("lonely", health=100.0)
    w.add_plot("waste"); w.own_plot("lonely", "waste")
    w.add_house("hut", 50); w.own("lonely", "hut")
    w.link_commons("lonely")
    N0 = w.total_plots()
    w.die("lonely", cause=3.0)
    return dict(
        waste_owner=w.owner_of("waste"), hut_to_council=w.owns_house("council", "hut"),
        council_coin=w.coin_of("council"), land_conserved=(w.total_plots() == N0),
        reverts_to_commons=(w.owner_of("waste") == "council"))


def g_ethics_restore():
    w = _world()
    P = sorted(w._cell_at.keys())
    w.make_person("child", P[10])
    w.rear("child", caregiver_present=False, regulated_caregiver=True)
    w.raise_child("child", episodes=8)
    harmed = w.window_of("child")
    w.attend("child", regulated=True)
    w.raise_child("child", episodes=12)
    restored = w.window_of("child")
    return dict(induced=harmed, restored=restored,
                recovered=(restored["half_width"] > harmed["half_width"]
                           and restored["safety_prior"] > harmed["safety_prior"]))


def g_death_reset():
    """The local perturbation arm (ties R10 -- the fixpoint-drift claim is DEFERRED
    to R10). Death ON transfers the estate (a perturbation); death OFF (immortal)
    leaves it fixed."""
    on = _world()
    P = sorted(on._cell_at.keys())
    on.make_person("council", P[0]); on.set_council("council")
    on.make_person("owner", P[10], coin=100.0); on.endow_health("owner", health=100.0)
    on.make_person("kid", P[11], coin=0.0)
    on.add_plot("e"); on.own_plot("owner", "e"); on.link_commons("owner")
    on.set_heir("owner", "kid")
    on.die("owner", cause=2.0)
    on_transfer = (on.owner_of("e") == "kid")

    off = _world()
    Q = sorted(off._cell_at.keys())
    off.make_person("council", Q[0]); off.set_council("council")
    off.make_person("owner", Q[10], coin=100.0); off.endow_health("owner", health=100.0)
    off.make_person("kid", Q[11], coin=0.0)
    off.add_plot("e"); off.own_plot("owner", "e"); off.link_commons("owner")
    off.set_heir("owner", "kid")
    off._run()                                   # immortal: no death
    off_transfer = (off.owner_of("e") == "kid")
    return dict(death_on_transfers=on_transfer, death_off_transfers=off_transfer,
                perturbation_is_death=(on_transfer and not off_transfer))


def main():
    out = dict(
        block=262000, rung="R14", base_sha="95f8ef4fe3522227c5b0719916fce4ac98c513e2",
        g_rearing_sets_priors=g_rearing(),
        g_rearing_ablate_control=g_rearing_control(),
        g_health_one_mechanism=g_health(),
        g_inheritance=g_inheritance(),
        g_no_heir_commons=g_no_heir_commons(),
        g_death_is_the_reset_partial=g_death_reset(),
        ethics_restore=g_ethics_restore(),
        deferrals=dict(
            R18_school=("coming-of-age capability is a REARING-QUALITY PROXY, not a "
                        "school-derived capability graph (R18 not built)"),
            R17_affect="not required by the R14 gates; reuse the standing 233/239/204 substrate",
            R10_punctuated_equilibrium=("the local death-perturbation is built + measured; "
                                        "the immortal-fixpoint-drifts-to-DEAD-attractor "
                                        "validity claim is DEFERRED to R10")),
        synthetic_vs_benchmark=(
            "SYNTHETIC glass-box demonstration of the life-cycle MECHANISM (the "
            "developmental arc 233/239 embodied in a society, aging=illness health, "
            "conserved inheritance). Mechanism-proven; NOT a benchmark / clinical number."),
        discipline=dict(seeds_self_load_only=True, new_rust=False,
                        estate_conserved="no add_node/del_node in any inheritance rule",
                        ethics="induce -> measure -> RESTORE, no reward/punishment"))
    os.makedirs(os.path.join(_ROOT, "results", "bigville_life"), exist_ok=True)
    path = os.path.join(_ROOT, "results", "bigville_life", "summary.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
