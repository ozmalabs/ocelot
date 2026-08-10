"""BigvilleLifeWorld -- bigville R14 (block 262000): the LIFE CYCLE, the KEYSTONE
that turns the town into an ORGANISM. On top of the proven R13 land world (LAND /
owns edges / council / the conserved map) and R7 finance (BANK / House / coin).

WHAT THIS ADDS (spec BIGVILLE_MOVEMENT_ECONOMY_SPEC.md §2.9 + §3 R14)
--------------------------------------------------------------------
  * BIRTH       -- a new resident minted at ingest (the honest boundary, like R11
                   arrival); temperament (nat_*) inherited from a parent (NATURE).
  * REARING     -- the child's three foundational PRIORS (world-safe / others-trust
                   / self-worth) are shaped by the QUALITY OF CARE. The child holds
                   the REUSED 239000 window-of-tolerance + co-regulation machinery
                   (its own AffectiveState + WindowOfTolerance + Stressor,
                   attended_by a caregiver with its OWN affect); rearing IS the
                   239000 stress-episode loop, UNCHANGED. bl_come_of_age maps the
                   239-produced care signal (widen_count - narrow_count) onto the
                   adult priors (NATURE modulated by NURTURE) + a capability PROXY.
  * HEALTH      -- ONE variable, two timescales (aging = illness). bl_age (chronic)
                   + bl_acute (acute, recoverable) + bl_recover (care/doctor) +
                   bl_death (health<=0 -> dead, routed).
  * INHERITANCE -- on death the estate (LAND R13 / house R7 / coin) passes to the
                   heir; with NO heir it reverts to the COUNCIL / commons. Every
                   transfer MOVES an edge (conserved).

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
A WORLD ADAPTER. It SUBCLASSES R13 (BigvilleLandWorld) by IMPORT, edits no tracked
file, and holds NO agent decision. It ONLY does mechanical I/O: mint a person /
LifeState / the 239000 dyad nodes (ingest); deliver world facts (a stressor tick, a
caregiver present + regulated, an aging period, an illness amount, a care amount,
whether a person has kin); arm one-shots; run the Rust `run_rules` fixpoint; read
state back. EVERY life-cycle decision -- dysregulation / co-regulation / widen-vs-
narrow (the REUSED 239000 rules), the prior mapping (bl_come_of_age), health decline
/ recovery / DEATH (bl_age/_acute/_recover/_death), and every estate transfer
(bl_inherit_*) -- is a seed RULE, never Python. NO reward/punishment token anywhere
(a prior / illness / death is a STATE, never a badness). NO new Rust.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from substrate.seed_loader import manifest_for                        # noqa: E402
from worlds.bigville_land_world import BigvilleLandWorld              # noqa: E402
# the 239000 co-regulation constants, imported READ-ONLY (DRY reuse of the
# pre-registered window-of-tolerance dynamics -- no re-implementation).
from worlds.coreg_dyad_world import (                                 # noqa: E402
    SETPOINT, K_SELF, K_CO, CG_REGULATED_AROUSAL, CG_DYSREGULATED_AROUSAL,
    WIDEN_DELTA, NARROW_DELTA, MIN_HALF_WIDTH, SAFETY_STEP, SAFETY_PRIOR0,
    RETURN_CAP)

# LifeState attrs -- one health variable + the aging/illness/recovery knobs.
LIFE_DEFAULTS = dict(
    health=100.0, max_health=100.0, age=0.0, age_rate=1.0, last_cause=0.0,
    age_armed=0.0, illness_armed=0.0, illness_amount=0.0, illness_cause=2.0,
    heal_armed=0.0, care_amount=0.0, dead=0.0)

# life-cycle attrs set on every person so a rule never reads a missing key.
PERSON_DEFAULTS = dict(
    dead=0.0, just_died=0.0, death_cause=0.0, coin_bequeathed=0.0, has_heir=0.0,
    nat_world_safe=0.5, nat_others_trust=0.5, nat_self_worth=0.5,
    prior_world_safe=0.5, prior_others_trust=0.5, prior_self_worth=0.5,
    base_capability=0.5, capability=0.0, matured=0.0, adult=0.0, coa_armed=0.0)


class BigvilleLifeWorld(BigvilleLandWorld):
    def __init__(self, **kw):
        super().__init__(**kw)
        for sid in ("bigville_life_rearing", "bigville_life_health",
                    "bigville_life_inheritance"):
            self.eng.load_seed_manifest(manifest_for(sid), None)
        self._life = {}          # person name -> LifeState nid
        self._window = {}        # child name -> WindowOfTolerance nid
        self._iaff = {}          # child name -> infant AffectiveState nid
        self._stressor = {}      # child name -> Stressor nid
        self._caregiver = {}     # child name -> caregiver Agent nid
        self._caff = {}          # child name -> caregiver AffectiveState nid
        self._council = None     # council person name (for commons reversion)

    # ================================================================ BIRTH
    def make_person(self, name, cell, *, coin=0.0, parent=None,
                    nat_world_safe=0.5, nat_others_trust=0.5, nat_self_worth=0.5,
                    base_capability=0.5, **kw):
        """Mint a resident (the honest birth boundary -- ingest, never a rule). If
        `parent` is given, temperament (nat_*) is INHERITED from the parent's own
        priors (NATURE ~ parent). Mechanical graph data."""
        m = self.make_char(name, cell, coin=coin)
        attrs = dict(PERSON_DEFAULTS)
        if parent is not None:
            pa = self.eng.node(self._movers[parent])["attrs"]
            nat_world_safe = float(pa.get("prior_world_safe", nat_world_safe))
            nat_others_trust = float(pa.get("prior_others_trust", nat_others_trust))
            nat_self_worth = float(pa.get("prior_self_worth", nat_self_worth))
        attrs.update(nat_world_safe=float(nat_world_safe),
                     nat_others_trust=float(nat_others_trust),
                     nat_self_worth=float(nat_self_worth),
                     base_capability=float(base_capability),
                     prior_world_safe=float(nat_world_safe),
                     prior_others_trust=float(nat_others_trust),
                     prior_self_worth=float(nat_self_worth))
        attrs.update(kw)
        for k, v in attrs.items():
            self.eng.set_attr(m, k, float(v))
        return m

    def set_council(self, name):
        """R9 council (the grantor + the commons that receives heirless estates)."""
        super().set_council(name)
        self._council = name

    def link_commons(self, name):
        """Wire the structural `has_council` edge person->council (everyone lives
        under the same council -- a world fact, ingest). Read by the commons-
        reversion rules when a heirless resident dies."""
        assert self._council is not None, "set_council first"
        self.eng.add_edge_unchecked(self._movers[name], "has_council",
                                    self._movers[self._council])

    # ================================================================ REARING
    def rear(self, name, *, caregiver_present=True, regulated_caregiver=True,
             half_width0=30.0, stress_mag=100.0):
        """Attach the REUSED 239000 rearing machinery to a child: its own
        AffectiveState.arousal + a WindowOfTolerance band + a Stressor, and (iff
        present) an `attended_by` caregiver with its OWN affect. Care QUALITY is a
        WORLD fact the adapter delivers (present? regulated?), exactly as
        CoregDyadWorld does -- the widen/narrow DECISION is the 239000 rules."""
        m = self._movers[name]
        iaff = self.eng.add_node("AffectiveState", dict(
            name="%s_affect" % name, baseline=1.0, valence=0.0, arousal=SETPOINT,
            resolution=0.0, selection_threshold=0.0, securing=0.0, competence=0.0,
            epoch=-1.0, tick_epoch=0.0, sr_epoch=0.0, cr_epoch=0.0,
            k_self=K_SELF, k_co=K_CO, setpoint=SETPOINT,
            dysregulated=0.0, dysreg_kind=0.0, in_episode=0.0, got_coreg=0.0))
        self.eng.add_edge_unchecked(m, "has_affective_state", iaff)
        wot = self.eng.add_node("WindowOfTolerance", dict(
            name="%s_window" % name, lo=-half_width0, hi=half_width0,
            half_width=half_width0, widen_delta=WIDEN_DELTA, narrow_delta=NARROW_DELTA,
            min_half_width=MIN_HALF_WIDTH, safety_prior=SAFETY_PRIOR0,
            safety_step=SAFETY_STEP, widen_count=0.0, narrow_count=0.0))
        self.eng.add_edge_unchecked(m, "has_window", wot)
        sx = self.eng.add_node("Stressor", dict(
            name="%s_stressor" % name, magnitude=float(stress_mag), armed=0.0, epoch=0.0))
        self.eng.add_edge_unchecked(m, "has_stressor", sx)
        self._iaff[name] = iaff
        self._window[name] = wot
        self._stressor[name] = sx
        self._rear_epoch = getattr(self, "_rear_epoch", {})
        self._rear_epoch[name] = 0
        if caregiver_present:
            cg_arousal = (CG_REGULATED_AROUSAL if regulated_caregiver
                          else CG_DYSREGULATED_AROUSAL)
            cg = self.eng.add_node("Agent", {"role": "caregiver",
                                             "regulated": 1.0 if regulated_caregiver else 0.0})
            caff = self.eng.add_node("AffectiveState", dict(
                name="%s_caregiver_affect" % name, baseline=1.0, valence=0.0,
                arousal=cg_arousal, resolution=0.0, selection_threshold=0.0,
                securing=0.0, competence=0.0, epoch=-1.0,
                regulated=1.0 if regulated_caregiver else 0.0))
            self.eng.add_edge_unchecked(cg, "has_affective_state", caff)
            self.eng.add_edge_unchecked(m, "attended_by", cg)
            self._caregiver[name] = cg
            self._caff[name] = caff
        self._run()

    def attend(self, name, *, regulated=True):
        """Bring a (regulated or dysregulated) caregiver to a child mid-life -- the
        RESTORE arm of the ethics protocol: a neglected child, re-attended by a
        regulated caregiver, has its window widened BACK by the 239000 co-regulation
        rules. Mechanical world delivery (a caregiver arrives)."""
        cg_arousal = (CG_REGULATED_AROUSAL if regulated else CG_DYSREGULATED_AROUSAL)
        cg = self.eng.add_node("Agent", {"role": "caregiver",
                                         "regulated": 1.0 if regulated else 0.0})
        caff = self.eng.add_node("AffectiveState", dict(
            name="%s_restorer_affect" % name, baseline=1.0, valence=0.0,
            arousal=cg_arousal, epoch=-1.0, resolution=0.0, selection_threshold=0.0,
            securing=0.0, competence=0.0, regulated=1.0 if regulated else 0.0))
        self.eng.add_edge_unchecked(cg, "has_affective_state", caff)
        # drop any prior attend edge, then attach the new caregiver.
        for old in list(self.eng.neighbours(self._movers[name], "attended_by")):
            self.eng.remove_edge_unchecked(self._movers[name], "attended_by", old)
        self.eng.add_edge_unchecked(self._movers[name], "attended_by", cg)
        self._caregiver[name] = cg
        self._caff[name] = caff
        return self._run()

    def _rear_step(self, name, *, stress=False):
        """Advance ONE rearing tick: (optionally) arm the stressor, advance the
        child's tick clock, run the 239000 fixpoint (push / dysreg / co-regulate /
        self-regulate / widen / narrow). NO decision here -- world delivery only."""
        self._rear_epoch[name] += 1
        e = float(self._rear_epoch[name])
        if stress:
            self.eng.set_attr(self._stressor[name], "armed", 1.0)
            self.eng.set_attr(self._stressor[name], "epoch", e)
        self.eng.set_attr(self._iaff[name], "tick_epoch", e)
        self._run()

    def _iaff_attr(self, name, key):
        return float(self.eng.node(self._iaff[name])["attrs"].get(key, 0.0))

    def rear_episode(self, name, cap=RETURN_CAP):
        """One rearing STRESS episode (the 239000 protocol): apply the stressor,
        then advance ticks until the child settles (in_episode back to 0) or the
        cap. The window's plasticity (widen if co-regulated, narrow if not) is
        applied once as the episode resolves -- the graph's decision."""
        self._rear_step(name, stress=True)
        if self._iaff_attr(name, "in_episode") == 0.0 and \
                self._iaff_attr(name, "dysregulated") == 0.0:
            return
        settle = 0
        while self._iaff_attr(name, "in_episode") == 1.0 and settle < cap:
            self._rear_step(name, stress=False)
            settle += 1

    def raise_child(self, name, *, episodes=8, settle=3):
        """Rear a child through N stress episodes, each followed by a few calm
        ticks (the 239000 plasticity settles once per episode). Convenience over
        rear_episode -- pure world delivery."""
        for _ in range(episodes):
            self.rear_episode(name)
            for _ in range(settle):
                self._rear_step(name, stress=False)

    def come_of_age(self, name):
        """Arm coming-of-age; bl_come_of_age maps the 239-produced care signal onto
        the three adult priors + the capability proxy + adult=1. The rule decides."""
        self.eng.set_attr(self._movers[name], "coa_armed", 1.0)
        return self._run()

    # ================================================================ HEALTH
    def endow_health(self, name, *, health=100.0, max_health=100.0, age=0.0,
                     age_rate=1.0):
        """Give a person a LifeState (the ONE health variable + aging/illness/
        recovery knobs). Mechanical graph data."""
        life = self.eng.add_node("LifeState", dict(LIFE_DEFAULTS))
        self.eng.set_attr(life, "health", float(health))
        self.eng.set_attr(life, "max_health", float(max_health))
        self.eng.set_attr(life, "age", float(age))
        self.eng.set_attr(life, "age_rate", float(age_rate))
        self.eng.add_edge_unchecked(self._movers[name], "has_life", life)
        self._life[name] = life
        return life

    def age_period(self, names=None):
        """Deliver ONE aging period (chronic decline) to each named person; bl_age
        applies health -= age_rate, then bl_death fires if health<=0."""
        names = names if names is not None else list(self._life)
        for nm in names:
            self.eng.set_attr(self._life[nm], "age_armed", 1.0)
        return self._run()

    def afflict(self, name, amount, *, cause=2.0):
        """Deliver an ACUTE health drop (illness/injury=2 / starvation=3 /
        exhaustion=4 -- opaque route data). bl_acute applies it (recoverable); if
        it drives health<=0, bl_death fires in the same fixpoint."""
        self.eng.set_attr(self._life[name], "illness_amount", float(amount))
        self.eng.set_attr(self._life[name], "illness_cause", float(cause))
        self.eng.set_attr(self._life[name], "illness_armed", 1.0)
        return self._run()

    def treat(self, name, amount):
        """Deliver care/rest/the doctor: bl_recover restores the SAME health
        variable up to max_health."""
        self.eng.set_attr(self._life[name], "care_amount", float(amount))
        self.eng.set_attr(self._life[name], "heal_armed", 1.0)
        return self._run()

    # ================================================================ DEATH -> INHERIT
    def set_heir(self, dead, heir):
        """Name a person's HEIR (kin) -- a `heir` edge + the has_heir structural
        fact. On death the estate passes to the heir (bl_inherit_*)."""
        self.eng.add_edge_unchecked(self._movers[dead], "heir", self._movers[heir])
        self.eng.set_attr(self._movers[dead], "has_heir", 1.0)

    def die(self, name, *, cause=2.0):
        """Drive a person to DEATH through the health variable (an acute event large
        enough to reach health<=0) -> bl_death -> the inheritance rules fire in the
        SAME fixpoint. Death is a state transition, never a punishment."""
        h = float(self.eng.node(self._life[name])["attrs"].get("health", 0.0))
        return self.afflict(name, h + 1.0, cause=cause)

    # ================================================================ read-offs
    def prior_of(self, name, axis):
        return float(self.eng.node(self._movers[name])["attrs"].get("prior_%s" % axis, 0.0))

    def priors_of(self, name):
        return {ax: self.prior_of(name, ax)
                for ax in ("world_safe", "others_trust", "self_worth")}

    def nat_of(self, name, axis):
        return float(self.eng.node(self._movers[name])["attrs"].get("nat_%s" % axis, 0.0))

    def capability_of(self, name):
        return float(self.eng.node(self._movers[name])["attrs"].get("capability", 0.0))

    def is_adult(self, name):
        return self.eng.node(self._movers[name])["attrs"].get("adult", 0.0) == 1.0

    def window_of(self, name):
        w = self.eng.node(self._window[name])["attrs"]
        return dict(half_width=float(w.get("half_width", 0.0)),
                    safety_prior=float(w.get("safety_prior", 0.0)),
                    widen_count=float(w.get("widen_count", 0.0)),
                    narrow_count=float(w.get("narrow_count", 0.0)))

    def health_of(self, name):
        return float(self.eng.node(self._life[name])["attrs"].get("health", 0.0))

    def age_of(self, name):
        return float(self.eng.node(self._life[name])["attrs"].get("age", 0.0))

    def is_dead(self, name):
        return self.eng.node(self._movers[name])["attrs"].get("dead", 0.0) == 1.0

    def death_cause_of(self, name):
        return int(self.eng.node(self._movers[name])["attrs"].get("death_cause", 0.0))

    def coin_of(self, name):
        return float(self.eng.node(self._movers[name])["attrs"].get("coin", 0.0))

    # ---- inequality read-offs (mechanical measurement, not a decision) ----
    def living(self):
        return [nm for nm in self._movers if not self.is_dead(nm)]

    def gini_land(self, names=None):
        """The land Gini over a set of persons (0 = equal, ->1 = concentrated). A
        pure Count-based measurement over the owns edges."""
        names = names if names is not None else self.living()
        xs = sorted(self.plots_held(nm) for nm in names)
        n = len(xs)
        tot = sum(xs)
        if n == 0 or tot == 0:
            return 0.0
        cum = sum((i + 1) * x for i, x in enumerate(xs))
        return (2.0 * cum) / (n * tot) - (n + 1.0) / n

    def estate_transfers(self):
        """Count of owns/owns_house edges currently held by heirs/council that
        moved from a dead person (a glass-box read of the perturbation)."""
        return sum(self.plots_held(nm) for nm in self.living())
