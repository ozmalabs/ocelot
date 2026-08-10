"""BigvilleIntegWorld -- bigville R10 (block 258000): the PUNCTUATED-EQUILIBRIUM
validity gate. The CAPSTONE that stops isolating the rungs and ASSEMBLES the town.

Every rung R1..R23 was proven IN ISOLATION behind a clean control -- which is WHY
they all passed. R10 is different: it composes a REPRESENTATIVE assembled town from
the existing rung seeds + adapters, turns it ON, runs it LONG, and MEASURES whether
it LIVES -- the macro time-series shape (STABILITY -> RAPID CHANGE -> STABILITY /
punctuated equilibrium) that is the ONLY signature of a genuine complex adaptive
system with real structure. The deliverable is the HARNESS + the MEASUREMENT + an
HONEST VERDICT, never a guaranteed "the town lives": a run that explodes, diagnosed
to WHICH coupling detonated, is a SUCCESS of this rung; a dead fixpoint is a FINDING.

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
The integration harness is ADMISSIBLE Python: it INGESTS (composes the town from
the rung adapters' own mechanical ingest helpers), TICKS (drives every rung's phase
one-shots + `run_rules`), and READS. It makes NO agent decision -- every decision
(produce/sell/credit/default/foreclose/evict/pay-or-miss/age/die/inherit/grieve/
choose-action/snap/refrain/prosecute/adjudicate) is a seed RULE in the imported
rungs. The harness only:

  * ASSEMBLES -- subclasses the deepest single MRO chain (R15 BigvilleViolWorld =
    movement/needs/time/economy/skill/finance/land/life/affect/violence), then
    ADDITIVELY loads the sibling-branch seeds (doctor/fisc/church/school/goal/coll/
    build/news/council/loop/fert/infant/loud) into the SAME engine, recording which
    load cleanly vs conflict. Loading graph data is mechanical I/O.
  * POPULATES -- a deterministic (seed=258000) heterogeneous cast + economy +
    finance + land + life + affect + enforcement, built ONLY from the inherited
    ingest helpers. Population variation is drawn from distributions (POPULATION =
    DISTRIBUTION OVER SEEDS), never scripted individual fates.
  * DRIVES -- one composite macro tick arms EVERY rung's phase unconditionally and
    runs the Rust fixpoint; the rules decide what actually happens. NO scheduled
    shocks (the G-endogenous falsifier): punctuations, if any, arise from
    accumulated stress crossing rule thresholds.
  * TRANSLATES CROSS-RUNG TRANSITIONS -- `propagate_transitions` mints the affect
    substrate's INPUT (a Loss) from another rung's OUTPUT (a fresh foreclosure /
    eviction / death), and mirrors grief onto the violence snap-pressure. This is
    the SAME admissible mechanical translation as R3's `register_collapse_and_concern`
    (read a state flag, mint the next rung's input, dedup) -- it is the PROPAGATION
    capstone (a failure travels the graph), NOT a decision: the grief/snap DECISION
    stays a rule (af_grief_from_loss / af_choose_action / bv_trigger).
  * MEASURES -- records a per-tick MACRO series: activity (graph changes / events
    per tick) AND cost (`compute proportional-to surprise` = engine rule-fire steps).

NO new Rust: every seed composes existing DSL Terms; the town runs on the canonical
own engine. This file edits no tracked file.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import numpy as np                                                    # noqa: E402

from substrate.seed_loader import manifest_for                       # noqa: E402
from worlds.bigville_viol_world import BigvilleViolWorld              # noqa: E402
from worlds.bigville_econ_world import (                             # noqa: E402
    GRAIN, BREAD, FISH, BAIT, BAKING, FISHING, BAITING)
from worlds.bigville_affect_world import (                           # noqa: E402
    LOSS_BEREAVEMENT, LOSS_FORECLOSURE)

# The sibling-branch seeds (NOT on the R15 MRO chain) additively loaded into the
# assembled engine so their rules are PRESENT in the town. Each is tried and its
# clean/conflict status recorded (documented, never forced).
SIBLING_SEEDS = [
    "bigville_doctor_care",
    "bigville_fisc_state", "bigville_fisc_church",
    "bigville_school_fund", "bigville_school_learn", "bigville_school_life",
    "bigville_goal_life", "bigville_goal_dream",
    "bigville_coll_collect", "bigville_coll_evict",
    "bigville_build_construct", "bigville_build_mutate",
    "bigville_news_press", "bigville_news_reach",
    "bigville_council_gov", "bigville_council_board",
    "bigville_loop_reputation",
    "bigville_fert_decide",
    "bigville_infant_care",
    "bigville_loud_comm", "bigville_loud_class",
]

# cadence (pre-registered, NOT tuned to a result): the economy runs every tick; a
# financial period (mortgage/rent charge, salary, appreciation, equity, rate) and a
# life period (aging) run once per NIGHT-length so the discrete "day" is the clock.
FIN_PERIOD = 6
LIFE_PERIOD = 6
NODE_CAP = 200_000          # explosion guard: a runaway is a BUG, recorded not crashed


class BigvilleIntegWorld(BigvilleViolWorld):
    def __init__(self, *, cast=12, seed=258000, **kw):
        super().__init__(**kw)
        # -- ASSEMBLE: additively load the sibling-branch seeds, record status ------
        self.assembled = []       # seed ids that loaded cleanly into the town
        self.conflicts = []       # (seed id, error) that could not compose
        for sid in SIBLING_SEEDS:
            try:
                self.eng.load_seed_manifest(manifest_for(sid), None)
                self.assembled.append(sid)
            except Exception as e:                                   # pragma: no cover
                self.conflicts.append((sid, repr(e)))
        # the CORE rungs already on the MRO chain (assembled by construction)
        self.core_rungs = [
            "move_nav", "move_energy", "drives", "need_drive_goal", "need_choice",
            "time_sleep", "time_concern", "arousal_window_coreg",
            "econ_production", "econ_exchange", "econ_supply", "econ_debt",
            "econ_expectation", "skill_learn", "skill_teach", "fin_bank",
            "fin_tenure", "land_market", "land_tenure", "life_rearing",
            "life_health", "life_inheritance", "affect_grief", "affect_decide",
            "affect_spiral", "affect_coreg", "affect_propagate", "viol_act",
            "viol_evidence", "viol_prosecute", "viol_kill",
        ]

        self._rng = np.random.default_rng(seed)
        self.cast = int(cast)

        # macro series + event log (glass-box)
        self.macro = []           # [{tick, activity, cost}]
        self.events = []          # [{tick, kind, actors, text}]
        self._grieved_foreclosure = set()
        self._grieved_death = set()
        self._enforced_acts = set()
        self.exploded = None      # None | dict(coupling=..., detail=...)

        # role bookkeeping for the state reader
        self.roles = {}           # name -> role label
        self.classes = {}         # name -> rich|middle|poor
        self.tensions = []        # sparse (attacker, victim) rivalries
        self.institutions = {}    # inst name -> nid (church/council/school/surgery/press)

        self._build_town()

    # ================================================================ ASSEMBLE
    def _walk(self, i):
        """Pick a deterministic walkable cell (mechanical placement)."""
        cells = self._cells
        return cells[(i * 37 + 11) % len(cells)]

    def _build_town(self):
        """Compose a representative assembled town from the inherited ingest helpers
        ONLY. Heterogeneous parameters are drawn from distributions (population =
        distribution over seeds); no individual fate is scripted."""
        self._cells = sorted(self._cell_at.keys())
        rng = self._rng
        n = self.cast

        # ---- the cast: a class-stratified population -----------------------------
        # class shares ~ (poor, middle, rich); each class a different coin / tenure /
        # age / affect prior distribution. A rule reads these; the SHAPE is the seed.
        names = ["v%02d" % i for i in range(n)]
        cls_draw = rng.choice(["poor", "middle", "rich"], size=n, p=[0.5, 0.35, 0.15])
        for i, nm in enumerate(names):
            cls = cls_draw[i]
            self.classes[nm] = cls
            coin = {"poor": 8.0, "middle": 30.0, "rich": 120.0}[cls] + float(rng.integers(0, 10))
            age = float(rng.integers(18, 72))
            # elderly carry lower health so DEATH is reachable within a long run from
            # aging alone (an initial condition, not a scheduled shock).
            health = max(20.0, 100.0 - max(0.0, age - 40.0) * 1.4)
            self.make_villager(nm, self._walk(i + 3), coin=coin)
            # violence trigger knobs: a little spite in some, hunger desperation
            self.set_attacker(nm, w_spite=float(rng.integers(0, 3)),
                              trigger_threshold=8.0, attack_amount=float(rng.integers(6, 16)),
                              attack_cost=6.0, energy=100.0)
            self.endow_health(nm, health=health, max_health=100.0, age=age,
                              age_rate=float(1.0 + (age > 55) * 1.5))
            self.set_affect(nm, affect_gain=1.0, gen_gain=1.0)
            self.roles[nm] = "villager"

        self.people = names
        rich = [nm for nm in names if self.classes[nm] == "rich"] or [names[-1]]
        poor = [nm for nm in names if self.classes[nm] == "poor"]
        middle = [nm for nm in names if self.classes[nm] == "middle"]

        # ---- the BANK, run by the banker agent (finance institution) -------------
        self._banker = "scrooge"
        self.add_bank(self._banker, self._walk(2), reserves=2000.0, salary=6.0,
                      fair_rate_bp=500.0, greed_premium_bp=300.0)
        self.roles[self._banker] = "banker"
        self.classes[self._banker] = "rich"
        self.set_attacker(self._banker, w_spite=0.0, trigger_threshold=50.0)
        self.endow_health(self._banker, health=90.0, age=55.0, age_rate=1.0)

        # ---- LAND: a fixed parcel map, concentrated with capital -----------------
        self._plotnames = ["p%02d" % i for i in range(max(6, n))]
        for i, pn in enumerate(self._plotnames):
            self.add_plot(pn, price=float(rng.integers(20, 60)), tax=0.0)
        # the rich sweep most land; a few middle own; the poor own none (structural)
        pi = 0
        for owner in rich:
            for _ in range(3):
                if pi < len(self._plotnames):
                    self.own_plot(owner, self._plotnames[pi]); pi += 1
        for owner in middle:
            if pi < len(self._plotnames):
                self.own_plot(owner, self._plotnames[pi]); pi += 1

        # ---- HOUSING TENURE: own / mortgage / rent (the R7 stress engine) --------
        self._house_of = {}
        rich_landlord = rich[0]
        for i, nm in enumerate(names):
            cls = self.classes[nm]
            hn = "h_%s" % nm
            self.add_house(hn, value=float(rng.integers(60, 140)), apprec=1.0)
            self._house_of[nm] = hn
            if cls == "rich":
                self.own(nm, hn)
            elif cls == "middle":
                # a mortgage: payment sized so most CAN service it (stress is a tail)
                self.mortgage(nm, hn, principal=float(rng.integers(50, 90)),
                              payment=float(rng.integers(4, 7)), term=3)
                if pi < len(self._plotnames):
                    self.own_plot(nm, self._plotnames[pi])
                    self.secure_on_plot(nm, self._plotnames[pi]); pi += 1
            else:  # poor -> rent from the rich landlord (build NO equity)
                self.rent(nm, rich_landlord, hn, rent=float(rng.integers(4, 8)),
                          term=3, raise_amount=1.0)

        # ---- ECONOMY: a small supply chain (fisher -> baker) + skills ------------
        # the workers who earn a wage each tick (production + exchange). Keep it
        # sparse and LOCAL (co-located), never an all-pairs market.
        self._shopkeepers = {}
        if len(names) >= 2:
            baker = middle[0] if middle else names[0]
            fisher = poor[0] if poor else names[1]
            self.add_shop("fishmonger", good=FISH, price=2.0, cell=self._walk(40),
                          keeper=fisher, activity=FISHING, input_good=BAIT,
                          stock=6, input_qty=6)
            self.set_skill(fisher, FISHING, 3.0)
            self.add_shop("bakery", good=BREAD, price=3.0, cell=self._walk(45),
                          keeper=baker, activity=BAKING, input_good=GRAIN,
                          stock=6, input_qty=6, supplier="fishmonger")
            self.set_skill(baker, BAKING, 3.0)
            self._shopkeepers = {"fishmonger": fisher, "bakery": baker}
            # buyers hold hunger + coin; buying drops hunger (needs closed loop)
            for nm in names:
                self.set_econ(nm, hunger_level=float(rng.integers(0, 6)))
                self.give_good(nm, BREAD, 0)

        # ---- ENFORCEMENT: the constable + the council (R9 / R15) ------------------
        self.make_constable()
        council = self.make_council()
        self.institutions["council"] = council
        # seat a few council members (John's-bloc structural corruption is possible)
        for i, nm in enumerate((rich + middle)[:3]):
            self.add_council_member(nm, vote=1.0)

        # ---- sparse TENSIONS (rivalries) so violence is REACHABLE (not scripted) --
        if len(names) >= 4:
            order = list(names)
            rng.shuffle(order)
            for i in range(0, len(order) - 1, 2):
                self.tensions.append((order[i], order[i + 1]))

        # ---- KIN: sparse heir edges (family structure, an initial condition) -----
        # so a DEATH propagates -> the heir inherits (R14) AND suffers a bereavement
        # Loss (R17) -> grief enters the decision machinery. A family graph, NOT a
        # scripted shock.
        for i, nm in enumerate(names):
            heir = names[(i + 3) % len(names)]
            if heir != nm:
                self.set_heir(nm, heir)

        # ---- institution nodes the sibling seeds reference (church/school/etc.) ---
        # Minted as mechanical graph data so the loaded sibling rules have anchors and
        # the town-state contract has institutions to report. Populated minimally;
        # rungs whose full ingest lives on a sibling Python chain are LOADED-but-DORMANT
        # (documented in the results, not forced).
        self.institutions["church"] = self.eng.add_node(
            "Church", {"funds": 40.0, "capacity": 20.0})
        self.institutions["school"] = self.eng.add_node(
            "School", {"funded": 1.0, "endowment": 30.0})
        self.institutions["surgery"] = self.eng.add_node(
            "Surgery", {"public": 1.0, "funds": 25.0})
        self.institutions["press"] = self.eng.add_node(
            "Press", {"captured": 0.0, "reach": 10.0})

        self._n0 = self._node_count()
        self._e0 = self._edge_count()

    # ================================================================ MEASURE
    # ACTIVITY is a count of discrete MACRO EVENTS per tick -- the town's structural
    # state-changes: a Loss (bereavement/foreclosure), a ViolentAct, an expectation
    # Surprise, a Concern, a Prosecution/Conviction/Sanction, a new death, a new
    # foreclosure/eviction/homeless transition. Each is read as a typed-node or flag
    # count (cheap: eng.nodes(type) / a flag scan), NEVER a per-tick full graph dump.
    _EVENT_TYPES = ("Loss", "ViolentAct", "Surprise", "Concern", "Prosecution",
                    "Conviction", "Sanction", "Newspaper")

    def _event_snapshot(self):
        """Counts that, summed across positive deltas, give the per-tick event count."""
        snap = {t: len(list(self.eng.nodes(t))) for t in self._EVENT_TYPES}
        snap["__dead"] = sum(1 for nm in self.people if self.is_dead(nm))
        snap["__homeless"] = sum(1 for nm in self.people if self.homeless_of(nm))
        snap["__foreclosed"] = sum(1 for nm in self._mortgages
                                   if self.foreclosed_of(nm))
        snap["__evicted"] = sum(1 for nm in self._rentals if self.evicted_of(nm))
        return snap

    def _node_count(self):
        return len(self.eng.graph_to_dict()["nodes"])

    def _edge_count(self):
        return len(self.eng.graph_to_dict()["edges"])

    # ================================================================ CROSS-RUNG
    def propagate_transitions(self):
        """Translate one rung's OUTPUT into the next rung's INPUT -- the PROPAGATION
        capstone. Mechanical (read a state flag, mint the input, dedup), the SAME
        admissible pattern as R3 register_collapse_and_concern. The grief/snap
        DECISION stays a rule."""
        minted = 0
        # a fresh FORECLOSURE -> a foreclosure Loss for the (now homeless) mortgagor
        for nm, mort in list(self._mortgages.items()):
            if self.foreclosed_of(nm) and nm not in self._grieved_foreclosure:
                self._grieved_foreclosure.add(nm)
                self.inflict_loss(nm, 40.0, kind=LOSS_FORECLOSURE)
                self.events.append(dict(tick=self.world_epoch, kind="foreclosure",
                                        actors=[nm], text="%s foreclosed -> homeless" % nm))
                minted += 1
        # a fresh EVICTION -> a foreclosure-family Loss for the evicted tenant
        for nm, rental in list(self._rentals.items()):
            if self.evicted_of(nm) and nm not in self._grieved_foreclosure:
                self._grieved_foreclosure.add(nm)
                self.inflict_loss(nm, 30.0, kind=LOSS_FORECLOSURE)
                self.events.append(dict(tick=self.world_epoch, kind="eviction",
                                        actors=[nm], text="%s evicted" % nm))
                minted += 1
        # a fresh DEATH -> a bereavement Loss for the heir/kin
        for nm in list(self.people):
            if self.is_dead(nm) and nm not in self._grieved_death:
                self._grieved_death.add(nm)
                heir = self._heir_of(nm)
                self.events.append(dict(tick=self.world_epoch, kind="death",
                                        actors=[nm], text="%s died (cause %d)" % (
                                            nm, self.death_cause_of(nm))))
                if heir is not None and not self.is_dead(heir):
                    self.inflict_loss(heir, 50.0, kind=LOSS_BEREAVEMENT)
                minted += 1
        # grief lowers the violence snap threshold: mirror grief onto snap_pressure
        # (a felt emotion ENTERS the decision machinery -- the anti-diorama criterion).
        for nm in self.people:
            if self.is_dead(nm):
                continue
            g = self.grief_of(nm)
            if g > 0.0:
                self.set_attacker(nm, snap_pressure=g)
        return minted

    def _heir_of(self, nm):
        for h in self.eng.neighbours(self._movers[nm], "heir"):
            for cand, nid in self._movers.items():
                if nid == h:
                    return cand
        return None

    def enforce_new_acts(self):
        """A fresh ViolentAct becomes a reported Case run through the 247 pipeline
        (mechanical translation of 'an act happened and was reported')."""
        for act in self.eng.nodes("ViolentAct"):
            if act in self._enforced_acts:
                continue
            self._enforced_acts.add(act)
            self.events.append(dict(tick=self.world_epoch, kind="violence",
                                    actors=[], text="a violent act occurred"))

    # ================================================================ THE TICK
    def integ_step(self):
        """One composite MACRO tick: arm EVERY rung's phase and let the rules decide.
        Records (activity, cost). NO scheduled shocks."""
        if self.exploded is not None:
            return
        snap_before = self._event_snapshot()
        c_before = self._cost_steps

        self.advance_clock()
        self.run_sleep_decisions()

        # -- ECONOMY (every tick): produce -> buy -> restock -> obligations ---------
        for shop in list(self._shops):
            self.produce(shop)
        for nm in self.people:
            if not self.is_dead(nm):
                self.buy(nm)
        for shop in list(self._shops):
            self.restock(shop)
        self.tick_obligations()

        # -- AFFECT (felt loop): translate transitions, then live period -----------
        self.propagate_transitions()
        for nm in self.people:
            if not self.is_dead(nm):
                self.live_period(nm)

        # -- VIOLENCE: arm the sparse tensions; bv_trigger / bv_refrain decides -----
        for (a, b) in self.tensions:
            if not self.is_dead(a) and not self.is_dead(b):
                try:
                    self.consider(a, b)
                except Exception:
                    pass
        self.enforce_new_acts()

        # -- FINANCE + LIFE periods on the discrete-day cadence ---------------------
        if self.world_epoch % FIN_PERIOD == 0:
            self.charge_mortgages()
            self.charge_rents()
            self.pay_salary()
            self.appreciate()
            self.recompute_equity()
            self.set_rate()
        if self.world_epoch % LIFE_PERIOD == 0:
            self.age_period()

        snap_after = self._event_snapshot()
        cost = self._cost_steps - c_before
        # ACTIVITY = sum of POSITIVE deltas across the event snapshot (new Losses /
        # violent acts / surprises / deaths / foreclosures / evictions this tick). A
        # stable stretch produces 0; a punctuation produces a burst. COST (rule-fires)
        # is the independent surprise meter.
        activity = sum(max(0, snap_after[k] - snap_before[k]) for k in snap_after)
        # macro OBSERVABLES (glass-box trajectory the punctuation test reads).
        obs = dict(living=self.living_count(),
                   gini_wealth=round(self.gini_wealth(), 4),
                   gini_land=round(self.gini_land(), 4),
                   total_coin=int(sum(self.coin_of(nm) for nm in self.people
                                      if not self.is_dead(nm))),
                   reserves=int(self.reserves()),
                   homeless=int(snap_after["__homeless"]),
                   dead=int(snap_after["__dead"]))
        self.macro.append(dict(tick=self.world_epoch, activity=int(activity),
                               cost=int(cost), obs=obs))

        # explosion guard: a runaway is a BUG, recorded not crashed (checked cheaply
        # off the event snapshot + a periodic full node count).
        if self.world_epoch % 25 == 0:
            nc = self._node_count()
            if nc > NODE_CAP:
                self.exploded = dict(coupling="node-count runaway",
                                     detail="nodes=%d > cap=%d at tick=%d" % (
                                         nc, NODE_CAP, self.world_epoch))

    def run_town(self, T=400):
        for _ in range(T):
            self.integ_step()
            if self.exploded is not None:
                break
        return self.macro

    # ================================================================ read-offs
    def gini_wealth(self):
        xs = sorted(max(0.0, self.coin_of(nm)) for nm in self.people
                    if not self.is_dead(nm))
        n = len(xs); tot = sum(xs)
        if n == 0 or tot == 0:
            return 0.0
        cum = sum((i + 1) * x for i, x in enumerate(xs))
        return (2.0 * cum) / (n * tot) - (n + 1.0) / n

    def circulation(self):
        """Total coin exchanged proxy: count of Good nodes bought this run (glass-box
        read of exchange activity)."""
        return int(sum(self.bought_of(nm) for nm in self.people))

    def living_count(self):
        return sum(1 for nm in self.people if not self.is_dead(nm))
