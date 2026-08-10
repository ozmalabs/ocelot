"""BigvilleDoctorWorld -- bigville R22 (block 270000): THE DOCTOR. Health becomes
a MONEY-GATED market good. Built on the proven R14 life world (health / illness /
death) + R7 coin + the R9 treasury-salary shape (public health).

WHAT THIS ADDS (spec BIGVILLE_MOVEMENT_ECONOMY_SPEC.md §3 R22 + §2.9)
--------------------------------------------------------------------
  * A DOCTOR -- a person (a coin-holder) with a price list (checkup_fee /
    treat_fee) and a `sees_doctor` edge from each patient.
  * PREVENTIVE CARE -- a paid CHECKUP (bd_checkup / bd_checkup_public) sets
    `screened=1`, so an early-detected disease avoids the progression penalty.
  * TREATMENT -- paid care (bd_treat / bd_treat_public) sets `treated=1`, which
    reduces the acute drop (severity), prevents death in severe cases, and
    (bd_recover) speeds recovery (length).
  * MONEY-GATING -- the fee is a CONSERVED coin transfer; affordability is the
    rule's `where` gate. Can't afford -> NO care.
  * PUBLIC HEALTH -- the council-funded path (treasury pays the doctor) makes the
    patient's coin irrelevant -> the STRUCTURAL LEVER that dissolves the
    wealth-health gradient.

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
A WORLD ADAPTER. It SUBCLASSES R14 (BigvilleLifeWorld) by IMPORT, edits no tracked
file, and holds NO agent decision. It ONLY does mechanical I/O: mint the doctor /
treasury / patient graph data (ingest), wire `sees_doctor` / `funded_by` edges,
ARM one-shots (checkup_armed / treat_armed / disease_armed / rec_armed), set world
facts (public_health, fees, disease_base), run the Rust `run_rules` fixpoint, and
read state back. EVERY doctor decision -- whether care happens (affordability), the
early-detection effect, the treatment severity / death modulation, the recovery
rate, and the public-vs-private branch -- is a seed RULE (bd_*), never Python. NO
reward/punishment token (illness/death are STATES; the RESTORE is treatment /
public provision). NO new Rust.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.seed_loader import manifest_for                        # noqa: E402
from worlds.bigville_life_world import BigvilleLifeWorld              # noqa: E402

# doctor-interaction attrs on the LifeState (R14 attrs left intact; a rule never
# reads a missing key -- these mirror the missing-tolerant seed reads).
CARE_DEFAULTS = dict(
    checkup_armed=0.0, treat_armed=0.0, disease_armed=0.0, rec_armed=0.0,
    screened=0.0, treated=0.0, public_health=0.0,
    disease_base=0.0, progression=30.0, treat_relief=40.0,
    doctor_care=40.0, natural_care=5.0)


class BigvilleDoctorWorld(BigvilleLifeWorld):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.eng.load_seed_manifest(manifest_for("bigville_doctor_care"), None)
        self._doctor = None      # doctor person name
        self._treasury = None    # Treasury nid

    # ================================================================ ingest
    def add_doctor(self, name, cell, *, checkup_fee=10.0, treat_fee=30.0):
        """Mint the DOCTOR -- a person (a coin-holder) with a price list. The
        doctor DRAWS INCOME from fees (like Scrooge / the schoolmaster), but
        PRIVATE / out-of-pocket. Mechanical graph data."""
        m = self.make_person(name, cell, coin=0.0)
        self.eng.set_attr(m, "checkup_fee", float(checkup_fee))
        self.eng.set_attr(m, "treat_fee", float(treat_fee))
        self._doctor = name
        return m

    def add_treasury(self, funds):
        """Mint the R9 public purse (Treasury.funds) and wire `doc funded_by
        treasury` so the council-funded rules can reach it. Mechanical graph
        data -- reuses R9's conserved treasury-salary shape."""
        assert self._doctor is not None, "add_doctor first"
        t = self.eng.add_node("Treasury", {"funds": float(funds)})
        self.eng.add_edge_unchecked(self._movers[self._doctor], "funded_by", t)
        self._treasury = t
        return t

    def admit(self, name, cell, *, coin=0.0, health=100.0, max_health=100.0,
              progression=30.0, treat_relief=40.0, doctor_care=40.0,
              natural_care=5.0, **kw):
        """Convenience: mint a patient, endow the R14 LifeState, set the
        doctor-interaction defaults, and enroll them with the doctor. Pure
        mechanical ingest."""
        self.make_person(name, cell, coin=coin, **kw)
        self.endow_health(name, health=health, max_health=max_health)
        life = self._life[name]
        attrs = dict(CARE_DEFAULTS)
        attrs.update(progression=float(progression),
                     treat_relief=float(treat_relief),
                     doctor_care=float(doctor_care),
                     natural_care=float(natural_care))
        for k, v in attrs.items():
            self.eng.set_attr(life, k, float(v))
        self.enroll(name)
        return life

    def enroll(self, name):
        """Wire the `sees_doctor` edge patient->doctor (the patient's access to
        the market). Mechanical."""
        assert self._doctor is not None, "add_doctor first"
        self.eng.add_edge_unchecked(self._movers[name], "sees_doctor",
                                    self._movers[self._doctor])

    # ================================================================ world facts
    def set_public_health(self, on, names=None):
        """Flip council-funded PUBLIC HEALTH on/off for a cohort (the STRUCTURAL
        LEVER). A world fact the adapter delivers; which payment rule fires
        (private vs public) is the graph's decision."""
        names = names if names is not None else list(self._life)
        for nm in names:
            self.eng.set_attr(self._life[nm], "public_health", 1.0 if on else 0.0)

    def checkup(self, name):
        """Deliver a preventive CHECKUP request: arm checkup_armed. bd_checkup /
        bd_checkup_public DECIDES whether it happens (affordability / funding)."""
        self.eng.set_attr(self._life[name], "checkup_armed", 1.0)
        return self._run()

    def seek_care(self, name):
        """Deliver a TREATMENT request: arm treat_armed. bd_treat /
        bd_treat_public DECIDES whether it happens (affordability / funding)."""
        self.eng.set_attr(self._life[name], "treat_armed", 1.0)
        return self._run()

    def strike(self, name, base, *, progression=None, treat_relief=None):
        """Deliver a DISEASE of base severity `base`: arm disease_armed. bd_onset
        DECIDES the effective acute drop from the screened/treated state and hands
        it to R14 (bl_acute applies it; bl_death fires or not). Optional per-strike
        overrides of the progression penalty / treatment relief."""
        life = self._life[name]
        self.eng.set_attr(life, "disease_base", float(base))
        if progression is not None:
            self.eng.set_attr(life, "progression", float(progression))
        if treat_relief is not None:
            self.eng.set_attr(life, "treat_relief", float(treat_relief))
        self.eng.set_attr(life, "disease_armed", 1.0)
        return self._run()

    def recover_tick(self, names=None):
        """Deliver ONE recovery tick to each named patient: arm rec_armed.
        bd_recover heals (treated fast / untreated slow)."""
        names = names if names is not None else list(self._life)
        for nm in names:
            self.eng.set_attr(self._life[nm], "rec_armed", 1.0)
        return self._run()

    def recover_to_full(self, name, cap=64):
        """Run recovery ticks until the patient is back at max_health (or cap).
        Returns the tick COUNT -- the LENGTH of the illness. Mechanical loop over
        world delivery; the healing per tick is the rule's decision."""
        life = self._life[name]
        mx = float(self.eng.node(life)["attrs"].get("max_health", 0.0))
        ticks = 0
        while ticks < cap and self.health_of(name) < mx and not self.is_dead(name):
            self.recover_tick([name])
            ticks += 1
        return ticks

    # ================================================================ read-offs
    def screened_of(self, name):
        return self.eng.node(self._life[name])["attrs"].get("screened", 0.0) == 1.0

    def treated_of(self, name):
        return self.eng.node(self._life[name])["attrs"].get("treated", 0.0) == 1.0

    def doctor_coin(self):
        return self.coin_of(self._doctor)

    def treasury_funds(self):
        return float(self.eng.node(self._treasury)["attrs"].get("funds", 0.0))

    def total_coin(self, names):
        """Σcoin over a set of persons (conservation read-off)."""
        return sum(self.coin_of(nm) for nm in names)
