"""BigvilleInteg2World -- bigville R10b (block 273000): THE BALANCE FIX.

R10 (BigvilleIntegWorld) assembled the town and MEASURED it: DEAD_FIXPOINT + a
coin-non-conservation misbalance (total_coin inflated ~35x). R10 diagnosed TWO
genuine defects and, per its prereg, did NOT fix them (fixing = the follow-on). This
rung fixes exactly those two defects -- CORRECTNESS, not tuning -- and RE-MEASURES.

DEFECT 1 -- the coin-conservation LEAK. `af_outcome_work` (R17 affect spiral) credits
a worker +5 coin as a SOURCE with no conserving sink; composed with the R4 economy,
Sigma(coin) grew unbounded. FIX (integration layer, edits no landed seed): a WagePool
employer/output account + the `bigville_integ2_conserve` seed -- every affect-outcome
coin move gets a MATCHING counter-move against the pool (work: pool pays 5; a
withdraw/drink/snap loss returns to the pool), so Sigma(coin) over the WHOLE system is
INVARIANT. The rules fire on an INDEPENDENT `wsink_armed` flag armed here in parallel
with `outcome_armed`, so they NEVER race the landed `af_outcome_*` rules.

DEFECT 2 -- the dormant RENEWAL. In R10 deaths fire ~6x (the founding elderly age out)
then RUN OUT; the R23 fertility / R14 birth path is loaded-but-DORMANT, so the
discrete dynamics MUST relax to a fixpoint. FIX: WIRE the birth path into the tick
loop -- every fertile adult holds a FertilityState (the R23 `bf_*` rules DECIDE the
fertility number), and each new death triggers a REPLACEMENT birth from a fertile
couple whose graph-decided fertility >= 1 (new agents born to replace the dead). The
COUNT/willingness is the graph's decision; the mint is the honest R14 birth boundary.

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
A WORLD ADAPTER. It SUBCLASSES R10 (edits no tracked R10/rung file), and holds NO
agent decision. Every decision stays a seed RULE: the conserving transfer is the
`bi2_*` rules; the fertility number is the `bf_*` rules; grief/snap/age/die/inherit
are the landed rungs. The adapter only ingests (pool, pays edges, FertilityStates,
births), arms flags (wsink_armed, decide_armed), ticks (`run_rules`), and reads. NO
new Rust; the town runs on the canonical own engine.

PRESENTATION (world-setup + read-only, per the supervisor's additions) -- a coherent
NAMED cast (real Pratchett-register names + real seeded params, deterministically
assigned; zero generic `v00`), meaningful positions, and a coherent map are layered
on. These are admissible world-setup (placing/naming, not deciding) + a read-only
export; they may shift movement/perception (a more-correct town, reported), never
agent logic. NO authored prose enters the Live export -- names are seeded, params and
held state are real graph reads.
"""
from __future__ import annotations

import math
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import json                                                             # noqa: E402
import numpy as np                                                     # noqa: E402

from substrate.seed_loader import manifest_for                        # noqa: E402
from worlds.bigville_integ_world import BigvilleIntegWorld, LIFE_PERIOD  # noqa: E402
from worlds.bigville_affect_world import LOSS_BEREAVEMENT             # noqa: E402

# FertilityState mechanism inputs (mirrors bigville_fert_world.FERT_DEFAULTS; NONE is
# wealth/coin/class -- the fertility DECISION is driven only by mechanisms).
_FERT_DEFAULTS = dict(
    decide_armed=0.0, qq_armed=0.0, mort_armed=0.0,
    base_target=2.0, child_labour_benefit=0.0, oldage_value=2.0, safety_net=0.0,
    school_cost=0.0, opp_cost=0.0, mortality=0.0, floor=0.0, eps=0.01,
    oldage_motive=0.0, decision_value=0.0, desired_surviving=0.0,
    survival=0.0, fertility=0.0)

_REGISTER_SEED = "bigville_townspeople_30"

# TIMESCALE HIERARCHY CALIBRATION (priority-2 dynamics fix, on PRINCIPLE).
# R10 ran ~12 ticks/day and aged every 6 ticks, so a life was only ~130-600 ticks --
# ~11-50 "days". At 12 ticks/day a resident cannot even DO a day (walk-to-market +
# buy + a work shift + a conversation + errands + walk-home + journal = dozens of
# actions, each >= 1 tick). The fix is the whole HIERARCHY, not one coefficient:
#   TICK  = the finest action grain (one hop / one utterance / one work-step);
#   DAY   = TICKS_PER_DAY ticks, large enough for a full day's activity budget;
#   slow processes (chronic AGING) are keyed to the DAY cadence at a realistic
#   per-day rate, so a LIFE = many DAYS = many x TICKS_PER_DAY ticks.
# This is a CORRECTNESS calibration (tick=action, day=activity cycle, life=many days),
# NOT a death rate dialled to manufacture a regime. Whatever regime emerges after it
# is MEASURED and reported honestly, and the longer run it forces is the SCALE x TIMING
# datum, reported (never shrink the day to make the run cheap).
PHASE_LEN = 18                       # day = 2*phase_len ticks (day + night)
TICKS_PER_DAY = 2 * PHASE_LEN        # 36 ticks/day (a "dozens" activity budget)
FIN_CADENCE = TICKS_PER_DAY          # finance charged once per day
AGE_CADENCE = TICKS_PER_DAY          # chronic aging applied once per day

# CHRONIC-AGING RATE (per DAY), UNIFORM -- the ACCEPTANCE-BAR calibration.
# R10 killed 6/16 in ~15 game-days from routine "chronic aging" (a ~37% cull in two
# weeks) because it aged every 6 ticks AND accelerated the elderly (x2.5). The base
# death rate of a HEALTHY, normal-age, fed adult over weeks must be ~0: a death should
# be a RARE, CAUSED event (genuine old age at the END of a long life / violence /
# severe untreated illness), never a background toll. So aging is now SLOW, UNIFORM
# (~1 health/day; frailty lives in the age->health starting value, not a rate multiplier)
# and applied once per DAY. A normal adult (health 55-100) then survives ~55-100 DAYS
# -- i.e. does not die over the run; only residents already at genuine end-of-life reach
# the death threshold, after accruing aging over MANY days. Correctness on principle,
# NOT a death rate dialled to a regime.
DAY_AGE_RATE = 1.0                    # health lost per DAY of chronic aging (uniform)
_NEWBORN_AGE_RATE = DAY_AGE_RATE
# A REALISTIC AGE PYRAMID needs a small genuine-elder cohort at end-of-life (R10 drew
# ages 18-72 uniform, UNDER-representing elders). These few, and ONLY these, die of
# genuine old age within a long run -- the rare demographic punctuations that trigger
# renewal. Everyone else (normal-age adults) lives out the run.
N_GENUINE_ELDERS = 3
_ELDER_AGES = (84.0, 88.0, 92.0)     # -> starting health ~38 / 33 / 27 via age->health


class BigvilleInteg2World(BigvilleIntegWorld):
    def __init__(self, *, cast=16, seed=273000, **kw):
        # set the DAY length via the base time-world clock (day = 2*phase_len ticks).
        kw.setdefault("phase_len", PHASE_LEN)
        super().__init__(cast=cast, seed=seed, **kw)
        # a SECOND rng stream for R10b-only ingest (fertility params, birth cells),
        # seeded off the block so it is deterministic and does not disturb R10's draws.
        self._rng2 = np.random.default_rng(seed + 1)

        # DEFECT / priority-2 -- realistic demographic timescale (aging keyed to DAY).
        self._calibrate_lifespan()

        # DEFECT 1 -- the conserving seed + the WagePool employer account.
        self.eng.load_seed_manifest(manifest_for("bigville_integ2_conserve"), None)
        self._install_wage_pool()

        # the rich landlord newborn renters rent from (R10 used rich[0]).
        _rich = [nm for nm in self.people if self.classes.get(nm) == "rich"]
        self._rich_landlord = _rich[0] if _rich else self.people[0]

        # DEFECT 2 -- the fertility/birth path, wired into the tick loop.
        self._fert2 = {}          # mover name -> FertilityState nid
        self._fertile_cursor = 0  # round-robins which couple begets a replacement
        self._birth_seq = 0
        self.births = []          # [{tick, parent, child}]
        self.death_log = []       # [{tick, day, name, cause, age, days_lived, elder}]
        self._birth_tick = {nm: 0 for nm in self.people}  # founders born at t0
        self._install_fertility()

        # PRESENTATION -- named cast + params + emoji + coherent positions/map.
        self.display = {}         # mover name -> real display name
        self.emoji = {}           # mover name -> emoji
        self.roles2 = {}          # mover name -> a richer role label
        self.homes = {}           # mover name -> (x, y) home/workplace cell
        self._register = self._load_register()
        self._assign_named_cast()
        self._layout_town()

    # ============================================================ DEFECT 1: CONSERVE
    def _install_wage_pool(self):
        """Mint the WagePool employer/output account and wire `pool -pays-> m` for
        every villager. A pure double-entry ledger account: no rule GATES on it, it may
        run negative (the aggregate employer's net wage deficit), so Sigma(coin) is
        conserved EXACTLY regardless of magnitude -- the conserving sink R10 lacked."""
        self._pool = self.eng.add_node("WagePool", {"coin": 0.0})
        for nm in self.people:
            self.eng.add_edge_unchecked(self._pool, "pays", self._movers[nm])
            self.eng.set_attr(self._movers[nm], "wsink_armed", 0.0)

    def _wire_pays(self, nm):
        self.eng.add_edge_unchecked(self._pool, "pays", self._movers[nm])
        self.eng.set_attr(self._movers[nm], "wsink_armed", 0.0)

    def apply_outcome(self, name):
        """Arm the conservation sink (wsink_armed) in PARALLEL with the landed
        outcome arm (outcome_armed). Both consume independent flags in the same
        fixpoint -> one af_outcome credit, one bi2 counter-move: race-free."""
        self.eng.set_attr(self._movers[name], "wsink_armed", 1.0)
        return super().apply_outcome(name)

    # Node types that hold `coin` / `reserves` in this town (the conserved money).
    # A targeted bulk sum over these replaces a full-graph serialisation every tick
    # (profiled: graph_to_dict was ~9% of the post-batching tick). Gated on identity
    # with the graph_to_dict sum (test_bigville_perf_coin_migrated) -- if a future
    # rung mints coin on a NEW type, that gate reddens and the type is added here.
    _COIN_TYPES = ("Mover", "WagePool", "Servant", "Person", "Child")
    _RESERVE_TYPES = ("Bank",)

    def system_coin(self):
        """The CONSERVED quantity: every `coin` attr + every bank `reserves`. Invariant
        across the run once the leak is closed. Summed via a targeted `get_attr_many`
        over the money-bearing types (cheap) instead of serialising the whole graph."""
        total = 0.0
        for t in self._COIN_TYPES:
            ids = list(self.eng.nodes(t))
            if ids:
                total += sum(float(v or 0.0) for v in self.eng.get_attr_many(ids, "coin"))
        for t in self._RESERVE_TYPES:
            ids = list(self.eng.nodes(t))
            if ids:
                total += sum(float(v or 0.0) for v in self.eng.get_attr_many(ids, "reserves"))
        return total

    def system_coin_via_graph_dict(self):
        """The authoritative whole-graph coin sum (the gate's reference for the cheap
        `system_coin` above). Kept as the ground truth the perf test compares against."""
        d = self.eng.graph_to_dict()
        coin = reserves = 0.0
        for n in d["nodes"]:
            a = n.get("attrs", {})
            coin += float(a.get("coin", 0.0) or 0.0)
            reserves += float(a.get("reserves", 0.0) or 0.0)
        return coin + reserves

    def pool_coin(self):
        return float(self.eng.node(self._pool)["attrs"].get("coin", 0.0))

    # ==================================================== PRIORITY 2: TIMESCALE
    def _calibrate_lifespan(self):
        """Re-key chronic aging to the DAY cadence at a SLOW, UNIFORM per-day rate so a
        healthy normal-age adult does NOT die over the run (base death rate ~0), and add
        a small genuine-ELDER cohort at end-of-life so the only aging deaths are rare,
        caused old-age passings that trigger renewal. World-setup on parameters
        (age_rate / age / health on the LifeState) -- edits no seed, makes no decision.
        Records lifespan BEFORE (R10: every-6-tick, age-accelerated) vs AFTER, in days."""
        # (1) genuine-elder cohort: the N oldest-drawn residents re-endowed to real
        #     end-of-life ages/health (a realistic age pyramid).
        by_age = sorted(((self.age_of(nm), nm) for nm in self._life),
                        key=lambda t: -t[0])
        self.elders = set()
        for i in range(min(N_GENUINE_ELDERS, len(by_age))):
            nm = by_age[i][1]
            age = _ELDER_AGES[i] if i < len(_ELDER_AGES) else 84.0
            health = max(20.0, 100.0 - max(0.0, age - 40.0) * 1.4)
            life = self._life[nm]
            self.eng.set_attr(life, "age", float(age))
            self.eng.set_attr(life, "health", float(health))
            self.elders.add(nm)
        # (2) uniform slow per-day aging for everyone; record lifespans.
        self.lifespan_before = {}          # ticks, R10 regime (for the report)
        self.lifespan_after = {}           # ticks, R10b regime
        self.lifespan_after_days = {}
        for nm, life in list(self._life.items()):
            a = self.eng.node(life)["attrs"]
            r0 = float(a.get("age_rate", 1.0))
            health = float(a.get("health", 0.0))
            self.lifespan_before[nm] = (health / r0) * 6.0 if r0 > 0 else float("inf")
            self.eng.set_attr(life, "age_rate", DAY_AGE_RATE)
            days = (health / DAY_AGE_RATE) if DAY_AGE_RATE > 0 else float("inf")
            self.lifespan_after_days[nm] = days
            self.lifespan_after[nm] = days * AGE_CADENCE

    # ============================================================ DEFECT 2: RENEWAL
    def _install_fertility(self):
        """Give every living ADULT mover a FertilityState (has_fertility) with
        mechanism inputs drawn from distributions (NEVER wealth). The R23 bf_* rules
        decide the fertility number from these."""
        for nm in list(self.people):
            if self.is_dead(nm):
                continue
            self._endow_fertility(nm)

    def _endow_fertility(self, nm):
        r = self._rng2
        attrs = dict(_FERT_DEFAULTS)
        # heterogeneous mechanism inputs (population = distribution over seeds).
        attrs["base_target"] = float(round(r.normal(2.2, 0.4), 3))
        attrs["oldage_value"] = float(round(max(0.0, r.normal(2.0, 0.6)), 3))
        attrs["mortality"] = float(round(min(0.4, max(0.0, r.normal(0.12, 0.06))), 3))
        attrs["child_labour_benefit"] = float(round(max(0.0, r.normal(0.3, 0.2)), 3))
        f = self.eng.add_node("FertilityState", dict(attrs))
        for k, v in attrs.items():
            self.eng.set_attr(f, k, float(v))
        self.eng.add_edge_unchecked(self._movers[nm], "has_fertility", f)
        self._fert2[nm] = f
        return f

    def _fertility_decide(self, nm):
        """Arm the R23 decision; bf_oldage -> bf_quantity_quality ->
        bf_mortality_replace chain in the fixpoint and write `fertility`."""
        self.eng.set_attr(self._fert2[nm], "decide_armed", 1.0)
        self._run()
        return self._fertility_of(nm)

    def _fertility_of(self, nm):
        f = self._fert2.get(nm)
        if f is None:
            return 0.0
        return float(self.eng.node(f)["attrs"].get("fertility", 0.0))

    def _pick_fertile_parent(self):
        """Round-robin a LIVING fertile adult to bear the next replacement (so births
        are not all one couple's). Returns a name or None."""
        pool = [nm for nm in self.people
                if nm in self._fert2 and not self.is_dead(nm)]
        if not pool:
            return None
        self._fertile_cursor = (self._fertile_cursor + 1) % len(pool)
        return pool[self._fertile_cursor]

    def _free_cell(self):
        cells = self._cells
        for _ in range(len(cells)):
            c = cells[self._fertile_cursor * 7 % len(cells)]
            self._fertile_cursor += 1
            return c
        return cells[0]

    def _beget_replacement(self, parent):
        """Birth flows from the graph's fertility decision: mint ONE new villager to
        replace a death, FULLY endowed so it participates (health/affect/attacker/
        rent/fertility/pays/heir). The mint is the honest R14 boundary; the WILLINGNESS
        (fertility >= 1) was the graph's decision. Returns the new name."""
        self._birth_seq += 1
        nm = "born%03d" % self._birth_seq
        cell = self._free_cell()
        r = self._rng2
        # NATURE inherited from the parent (R14 make_person(parent=...)); coin 0 (no
        # coin creation -- newborns hold nothing).
        self.make_villager(nm, cell, coin=0.0, parent=parent)
        self.set_attacker(nm, w_spite=float(r.integers(0, 3)),
                          trigger_threshold=8.0,
                          attack_amount=float(r.integers(6, 16)),
                          attack_cost=6.0, energy=100.0)
        # a newborn: full health, slow (calibrated) aging (dies of old age a lifetime
        # of many ticks later).
        self.endow_health(nm, health=100.0, max_health=100.0, age=0.0,
                          age_rate=_NEWBORN_AGE_RATE)
        self.set_affect(nm, affect_gain=1.0, gen_gain=1.0)
        self.set_econ(nm, hunger_level=float(r.integers(0, 6)))
        self.give_good(nm, __import__("worlds.bigville_econ_world",
                                      fromlist=["BREAD"]).BREAD, 0)
        # housed as a RENTER of the rich landlord (build no equity -> reachable stress).
        hn = "h_%s" % nm
        self.add_house(hn, value=float(r.integers(60, 140)), apprec=1.0)
        self._house_of[nm] = hn
        landlord = self._rich_landlord
        self.rent(nm, landlord, hn, rent=float(r.integers(4, 8)), term=3,
                  raise_amount=1.0)
        # class/role/name/emoji so the export stays coherent (no generic name).
        self.classes[nm] = "poor"
        self.roles[nm] = "villager"
        self.roles2[nm] = "child (born %d)" % self.world_epoch
        self._name_newborn(nm, parent)
        # renewal wiring: pays edge (conserved wages), fertility (can reproduce), heir.
        self._wire_pays(nm)
        self._endow_fertility(nm)
        self.set_heir(nm, parent)             # kin so a later death propagates grief
        self.people.append(nm)
        self._birth_tick[nm] = self.world_epoch
        self.homes[nm] = cell
        return nm

    # death_cause codes (bl_death: death_cause = last_cause + 1): 1 chronic aging ->
    # code 2 old-age; illness last_cause 2 -> code 3; a violent kill routes via bv_kill.
    _CAUSE_LABEL = {1.0: "aging", 2.0: "old_age", 3.0: "illness", 4.0: "exhaustion",
                    5.0: "violence"}

    def _log_deaths(self, new_deaths):
        """Record every new death's CAUSE + decedent age + days-lived + health, the
        acceptance evidence that deaths are old-age / murder / severe-illness, never a
        routine-aging cull of the healthy."""
        for nm in new_deaths:
            cause = float(self.death_cause_of(nm))
            age = self.age_of(nm)
            born = self._birth_tick.get(nm, 0)
            days_lived = (self.world_epoch - born) / float(TICKS_PER_DAY)
            label = self._CAUSE_LABEL.get(cause, "cause_%g" % cause)
            self.death_log.append(dict(
                tick=self.world_epoch, day=int(self.world_epoch // TICKS_PER_DAY),
                name=self.display.get(nm, nm), id=nm, cause_code=cause, cause=label,
                age_years=round(age, 1), days_lived_in_sim=round(days_lived, 1),
                was_genuine_elder=bool(nm in getattr(self, "elders", set()))))

    def _renew(self, dead_before):
        """Each NEW death this tick triggers a replacement birth from a fertile couple
        whose graph-decided fertility >= 1. Returns the number of births."""
        new_deaths = [nm for nm in self.people
                      if self.is_dead(nm) and nm not in dead_before]
        if new_deaths:
            self._log_deaths(new_deaths)
        births = 0
        for _dead in new_deaths:
            parent = self._pick_fertile_parent()
            if parent is None:
                break
            if self._fertility_decide(parent) >= 1.0:
                child = self._beget_replacement(parent)
                self.births.append(dict(tick=self.world_epoch, parent=parent,
                                        child=child,
                                        name=self.display.get(child, child)))
                births += 1
        return births

    # ==================================================== PERF: BATCHED PHASES
    # The per-entity arm-then-run loops (produce/buy/restock/consider) each ran a
    # FULL run_rules fixpoint PER entity -> ~O(people) fixpoints/tick, each re-scanning
    # the whole graph (profiled: run_rules = 92% of wall, buy 48% + consider 25%). These
    # batch the arming and run ONE fixpoint per phase, so per-tick cost scales with the
    # GRAPH, not the POPULATION. A behaviour-preserving optimisation: gated on
    # byte-identity of the macro series (see the perf gate) -- `_batch_phases` toggles
    # the per-entity path for the baseline arm of that gate.
    _batch_phases = True

    def _produce_all(self):
        for sh in self._shops.values():
            self.eng.set_attr(sh, "make_armed", 1.0)   # unified recipe engine (be_produce retired)
        return self._run()

    def _buy_all(self):
        for nm in self.people:
            if not self.is_dead(nm):
                self.eng.set_attr(self._movers[nm], "buy_armed", 1.0)
        return self._run()

    def _restock_all(self):
        for sh in self._shops.values():
            self.eng.set_attr(sh, "restock_armed", 1.0)
        return self._run()

    def _consider_all(self):
        for (a, b) in self.tensions:
            if self.is_dead(a) or self.is_dead(b):
                continue
            av = self._movers[a]
            for old in list(self.eng.neighbours(av, "considers_violence")):
                self.eng.remove_edge_unchecked(av, "considers_violence", old)
            self.eng.add_edge_unchecked(av, "considers_violence", self._movers[b])
            self.eng.set_attr(av, "attacked", 0.0)
            self.eng.set_attr(av, "refrained", 0.0)
            self.eng.set_attr(av, "consider_armed", 1.0)
        return self._run()

    def integ_step(self):
        """One composite MACRO tick under the TICK/DAY/LIFE hierarchy. Every tick runs
        the finest-grain action round (economy + felt affect + violence); FINANCE and
        chronic AGING are keyed to the DAY cadence (once per TICKS_PER_DAY); RENEWAL
        (a replacement birth per new death) closes the demographic loop. Same phases as
        R10 -- the ONLY changes are the day-keyed finance/aging cadence and the wired
        births; every DECISION stays a seed rule. Records (activity, cost); NO scheduled
        shocks. A birth is counted as a structural event, exactly as a death is."""
        if self.exploded is not None:
            return
        snap_before = self._event_snapshot()
        c_before = self._cost_steps
        dead_before = set(nm for nm in self.people if self.is_dead(nm))

        self.advance_clock()
        self.run_sleep_decisions()

        # -- ECONOMY (every tick): produce -> buy -> restock -> obligations ---------
        if self._batch_phases:
            self._produce_all()
            self._buy_all()
            self._restock_all()
        else:
            for shop in list(self._shops):
                self.produce(shop)
            for nm in self.people:
                if not self.is_dead(nm):
                    self.buy(nm)
            for shop in list(self._shops):
                self.restock(shop)
        self.tick_obligations()

        # -- AFFECT: cross-rung grief translation EVERY tick (cheap); the felt life-
        #    DECISION cycle (choose work/withdraw/drink/snap -> the DAY's income /
        #    wellbeing) once per DAY. An affect outcome is a DAY-level event, not a
        #    per-tick one: the R17 loop was designed per-period, and R10 running it
        #    every tick over the day-scaled clock earned a FULL DAY'S WAGE EVERY TICK
        #    (the scale bug behind the runaway worker wealth). Daily makes the +5 work
        #    wage commensurate with finance (salary/rent are ~per-day), so the wealth
        #    distribution coheres. Conservation is unchanged (each outcome still armed
        #    with its wsink counter-move).
        self.propagate_transitions()
        if self.world_epoch % TICKS_PER_DAY == 0:
            for nm in self.people:
                if not self.is_dead(nm):
                    self.live_period(nm)      # -> apply_outcome() arms wsink (conserve)

        # -- VIOLENCE: arm the sparse tensions; bv_trigger / bv_refrain decides -----
        if self._batch_phases:
            self._consider_all()
        else:
            for (a, b) in self.tensions:
                if not self.is_dead(a) and not self.is_dead(b):
                    try:
                        self.consider(a, b)
                    except Exception:
                        pass
        self.enforce_new_acts()

        # -- FINANCE on the DAY cadence --------------------------------------------
        if self.world_epoch % FIN_CADENCE == 0:
            self.charge_mortgages()
            self.charge_rents()
            self.pay_salary()
            self.appreciate()
            self.recompute_equity()
            self.set_rate()
        # -- chronic AGING on the DAY cadence (a life = many days) ------------------
        if self.world_epoch % AGE_CADENCE == 0:
            self.age_period()

        # -- RENEWAL: each NEW death -> a replacement birth (graph fertility decides) -
        births = self._renew(dead_before)

        snap_after = self._event_snapshot()
        cost = self._cost_steps - c_before
        activity = sum(max(0, snap_after[k] - snap_before[k]) for k in snap_after)
        activity += int(births)               # a birth is a structural transition
        obs = dict(living=self.living_count(),
                   day=int(self.world_epoch // max(1, TICKS_PER_DAY)),
                   gini_wealth=round(self.gini_wealth(), 4),
                   gini_land=round(self.gini_land(), 4),
                   total_coin=int(sum(self.coin_of(nm) for nm in self.people
                                      if not self.is_dead(nm))),
                   system_coin=int(round(self.system_coin())),
                   pool_coin=int(round(self.pool_coin())),
                   reserves=int(self.reserves()),
                   born=int(self._birth_seq),
                   homeless=int(snap_after["__homeless"]),
                   dead=int(snap_after["__dead"]))
        self.macro.append(dict(tick=self.world_epoch, activity=int(activity),
                               cost=int(cost), births=int(births), obs=obs))

        if self.world_epoch % 25 == 0:
            nc = self._node_count()
            if nc > 200_000:
                self.exploded = dict(coupling="node-count runaway",
                                     detail="nodes=%d at tick=%d" % (nc, self.world_epoch))

    # ============================================================ PRESENTATION
    def _load_register(self):
        try:
            p = os.path.join(_ROOT, "seeds", "%s.json" % _REGISTER_SEED)
            return json.load(open(p)).get("inhabitants", [])
        except Exception:
            return []

    def _assign_named_cast(self):
        """Deterministically assign each mover a DISTINCT real name from the seeded
        Pratchett register + its real seeded params (w_spite drives violence; the
        rest are held-state the export reads). Zero generic `v00` remains. This is the
        supervisor's permitted fallback to a full register boot; the full 30-person
        register boot is a documented follow-on."""
        reg = list(self._register)
        by_name = {i["name"]: i for i in reg}
        used = set()

        def take(name):
            used.add(name)
            return by_name.get(name)

        # trade/role-matched anchors so the key roles carry the right names.
        shop = getattr(self, "_shopkeepers", {}) or {}
        anchor = {}
        if shop.get("bakery"):
            anchor[shop["bakery"]] = "Marjorie Dough"
        if shop.get("fishmonger"):
            anchor[shop["fishmonger"]] = "Doreen Ferrety"
        # the two richest movers become the mayor (John) and pastor (Mary) foils.
        rich = [nm for nm in self.people if self.classes.get(nm) == "rich"]
        rich_sorted = sorted(rich, key=lambda nm: -self.coin_of(nm))
        if len(rich_sorted) >= 1:
            anchor.setdefault(rich_sorted[0], "John")
        if len(rich_sorted) >= 2:
            anchor.setdefault(rich_sorted[1], "Mary")

        role_of = {"John": "mayor", "Mary": "pastor",
                   "Marjorie Dough": "baker", "Doreen Ferrety": "fishmonger"}
        pool_names = [i["name"] for i in reg
                      if i["name"] not in ("John", "Mary", "Marjorie Dough",
                                           "Doreen Ferrety")]
        pi = 0
        for nm in self.people:
            rn = anchor.get(nm)
            if rn is None:
                while pi < len(pool_names) and pool_names[pi] in used:
                    pi += 1
                rn = pool_names[pi] if pi < len(pool_names) else nm
                pi += 1
            used.add(rn)
            self._apply_persona(nm, take(rn) or by_name.get(rn), rn,
                                 role_of.get(rn, "villager"))
        # the banker keeps his canonical identity (supervisor: banker=Scrooge).
        bk = getattr(self, "_banker", None)
        if bk is not None:
            self.display[bk] = "Scrooge"
            self.emoji[bk] = "\U0001F911"
            self.roles2[bk] = "banker"
            self.eng.set_attr(self._movers[bk], "display_seq", 999.0)

    def _apply_persona(self, nm, inh, rn, role):
        """Set the mover's REAL name + emoji + seeded params as graph attrs. w_spite
        feeds the violence machinery; the others are held-state the export reads."""
        self.display[nm] = rn
        self.roles2[nm] = role
        self.emoji[nm] = (inh or {}).get("emoji", "\U0001F9D1")
        if not inh:
            return
        params = inh.get("params", {})
        m = self._movers[nm]
        # w_spite is a REAL violence-trigger knob (bv_trigger reads it).
        if "w_spite" in params:
            self.set_attacker(nm, w_spite=float(params["w_spite"]))
        # the remaining seeded params: held-state the export reads (real graph data).
        for k in ("w_supergraph", "charm_weight", "hostile_weight", "mood_bias",
                  "cred_on", "claim_weight"):
            if k in params:
                self.eng.set_attr(m, k, float(params[k]))
        for ax in ("world_safe", "others_trust", "self_worth"):
            key = "prior_%s" % ax
            if key in params:
                self.eng.set_attr(m, "reg_%s" % key, float(params[key]))

    def _name_newborn(self, nm, parent):
        """A newborn takes a fresh distinct register name if any remain, else a
        patronymic from the parent's real name (still real, deterministic)."""
        used = set(self.display.values())
        for i in self._register:
            if i["name"] not in used:
                self.display[nm] = i["name"]
                self.emoji[nm] = i.get("emoji", "\U0001F476")
                return
        pn = self.display.get(parent, parent)
        self.display[nm] = "%s child" % pn.split()[0]
        self.emoji[nm] = "\U0001F476"

    def _layout_town(self):
        """Place each resident at a MEANINGFUL cell (home/workplace) for a coherent
        exported map. World-setup only (positions); the base grid tiles are unchanged.
        R10's buyers were never co-located with shops (circulation ~ 0), so repositions
        do not change the exchange path -- a more-correct spatial structure, reported."""
        cells = self._cells
        if not cells:
            return
        w = max(x for (x, y) in cells) + 1
        h = max(y for (x, y) in cells) + 1
        cx, cy = w // 2, h // 2
        # institution anchors around a central square (deterministic, coherent).
        anchors = {
            "townhall": (cx, cy - 2), "noticeboard": (cx + 1, cy - 2),
            "bank": (cx - 3, cy), "church": (cx + 3, cy),
            "school": (cx - 3, cy + 3), "surgery": (cx + 3, cy + 3),
            "inn": (cx, cy + 3), "press": (cx - 1, cy - 2),
        }
        self.map_anchors = {k: self._nearest_cell(v) for k, v in anchors.items()}
        # workplace for the named key roles; everyone else in the housing district.
        home_i = 0
        housing0 = (2, max(2, h - 5))
        for nm in self.people:
            role = self.roles2.get(nm, "villager")
            if role == "baker":
                self.homes[nm] = self.map_anchors["inn"]
            elif role == "fishmonger":
                self.homes[nm] = self._nearest_cell((cx, cy + 5))
            elif role == "mayor":
                self.homes[nm] = self.map_anchors["townhall"]
            elif role == "pastor":
                self.homes[nm] = self.map_anchors["church"]
            else:
                hx = housing0[0] + (home_i % 6) * 2
                hy = housing0[1] - (home_i // 6) * 2
                self.homes[nm] = self._nearest_cell((hx, hy))
                home_i += 1
            self._place(nm, self.homes[nm])
        bk = getattr(self, "_banker", None)
        if bk is not None:
            self.homes[bk] = self.map_anchors["bank"]
            self._place(bk, self.map_anchors["bank"])

    def _nearest_cell(self, xy):
        if xy in self._cell_at:
            return xy
        best, bd = self._cells[0], 1e9
        for c in self._cells:
            d = (c[0] - xy[0]) ** 2 + (c[1] - xy[1]) ** 2
            if d < bd:
                best, bd = c, d
        return best

    def _place(self, nm, cell):
        cell = self._nearest_cell(cell)
        m = self._movers[nm]
        for old in list(self.eng.neighbours(m, "is_at")):
            self.eng.remove_edge_unchecked(m, "is_at", old)
        self.eng.add_edge_unchecked(m, "is_at", self._cell_at[cell])
        self.pos[nm] = tuple(cell)
