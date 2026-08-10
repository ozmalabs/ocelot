"""BigvilleNeedWorld -- bigville R2 (block 250000): graph-native NEEDS -> GOALS +
PREFERENCE / satisficing on top of the proven R1 movement+energy world.

WHAT THIS ADDS (spec BIGVILLE_MOVEMENT_ECONOMY_SPEC.md sec 3 R2)
---------------------------------------------------------------
A DRIVE above threshold mints a spatial GOAL, and WHICH good the goal targets is
the substrate's OWN `decision_value` Argmax over REACHABLE satisfiers weighted by
a per-villager PREFERENCE minus TRAVEL-COST:

    value(good) = preference[villager][good] * need_urgency - cost_on * travel_cost

Satisficing EMERGES: move the orchard far and its travel_cost dominates so bread
wins DESPITE the higher apple preference -- the choice flips on distance alone,
preference unchanged. The chosen good's source becomes the R1 navigation target.

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
This is a WORLD ADAPTER. It SUBCLASSES R1 (BigvilleMoveWorld) by IMPORT, edits no
tracked file, and holds NO agent decision:

  * The drive->goal->choice runs in the R1 ISOLATED movement substrate (`self.eng`),
    loading the REUSED 207000 `drives` seed (which computes each drive's
    urge=|v_d-c_d|) plus two NEW seed manifests. EVERY decision is a RULE there:
      - `nd_arbitrate`          : the competing-drives decision (Argmax-urge drive
                                  wins; the SAME Argmax family as ss_choose_burn).
      - `nd_form_sustenance_goal` / `nd_form_rest_goal` : the winning need mints its
                                  goal; ablate the drive -> no drive above threshold
                                  -> NO goal (load-bearing).
      - `nd_seed_here` / `nd_relax` / `nd_source_cost` : the choice-distance flood
                                  (a Bellman BFS over the walkable map-belief, a
                                  distinct `cdist` field so R1's gdist is untouched).
      - `nd_choose_good`        : THE preference/satisficing decision -- the
                                  decision_value Argmax over Sources.
    None of those lives in Python.
  * This adapter only does mechanical I/O: register goods/sources/prefs/drives as
    graph data (ingest), run the rule fixpoint in the R1-proven TWO PHASES (flood
    to fixpoint, THEN arm the pick), read the rule's chosen good + target cell, and
    mechanically wire that cell as the R1 `seeks` nav target (exactly like R1's
    adapter applies a rule-chosen hop to host position). No `if`/`else` over agent
    state selects a good -- the Argmax does.

No new Rust: all three seeds compose existing DSL Terms.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from substrate.seed_loader import manifest_for                  # noqa: E402
from worlds.bigville_move_world import BigvilleMoveWorld, BIG    # noqa: E402
import domains.bigville_entities as E                            # noqa: E402  researched diet-affect model

# good codes (integer-native; no string Eq in the rules)
APPLE, BREAD, ALE = 1.0, 2.0, 3.0
GOOD_NAME = {APPLE: "apple", BREAD: "bread", ALE: "ale"}
# need codes
SUSTENANCE, FATIGUE = 1.0, 2.0

# walking is exertion: stamina drawn down per hop (a long errand tires + hungers you -> the body feeds back)
TRAVEL_STAMINA_PER_HOP = 0.1
# the body's STAMINA is the movement range: the R1 move budget is charged from stamina each tick (energy is
# no longer an independent store -- it is a per-tick view of the body). stamina 1.0 -> energy 100 (full pace).
STAMINA_TO_ENERGY = 100.0

# a full Drive attr set the reused 207000 `drives` rules read without error
DRIVE_DEFAULTS = dict(
    v_d=0.0, c_d=0.0, v_0=0.0, scale=1.0, half_life=1.0, now_epoch=0.0,
    last_tend=0.0, c_d_prev=0.0, weight=1.0, decay=0.0, gain=0.0, loss=0.0,
    urge=0.0, urgency=0.0)


class BigvilleNeedWorld(BigvilleMoveWorld):
    def __init__(self, **kw):
        super().__init__(**kw)
        # the reused drive system + the two R2 seeds, into the R1 movement engine
        self.eng.load_seed_manifest(manifest_for("drives"), None)
        self.eng.load_seed_manifest(manifest_for("bigville_need_drive_goal"), None)
        self.eng.load_seed_manifest(manifest_for("bigville_need_choice"), None)
        self.eng.load_seed_manifest(manifest_for("bigville_degradation_learn"), None)   # learn rot from consequence
        self.eng.load_seed_manifest(manifest_for("bigville_diet_affect"), None)         # monotony -> mood
        self.eng.load_seed_manifest(manifest_for("bigville_body"), None)                # World -> Body physiology
        self.eng.load_seed_manifest(manifest_for("bigville_body_choice"), None)         # eat/rest are DECISIONS
        self.eng.load_seed_manifest(manifest_for("bigville_pursuit"), None)             # ONE way to pursue a goal
        self.eng.load_seed_manifest(manifest_for("bigville_household"), None)           # one need, one fetcher
        self.eng.load_seed_manifest(manifest_for("bigville_delegation"), None)          # the asked person's reply
        self._sources = {}          # name -> Source nid
        self._drives = {}           # (mover_name, need_code) -> Drive nid
        self._bodies = {}           # mover_name -> Body nid (World -> Body -> Mind)

    # ------------------------------------------------------ the Body (World -> Body -> Mind)
    def add_mover(self, name, start, goal=None, **energy):
        """A villager is a MIND that HAS a BODY. add_mover mints the Mover (the mind: beliefs,
        preferences, drives, the choice collapse) AND a Body node it `has_body` -- the physiology
        (health, mood, satiety, the palate) the world acts on and the mind reads. Every mover gets a
        body, because the choice collapse now reads its body's appetite (nd_choose_good, has_body)."""
        m = super().add_mover(name, start, goal=goal, **energy)
        body = self.eng.add_node("Body", {
            "health": 1.0,          # physical wellbeing; a spoiled meal harms it (bd_meal_health)
            "mood": 0.5,            # affective baseline; monotony sinks it (af_meal_mood)
            "satiety": 0.0,         # how sated on the last food -> the appetite the mind reads
            "last_food": -1.0, "food_run": 0.0,    # the palate: what/how-often the body last ate
            # physique: base stats (drawn/varied by set_physique) + a trained component that USE grows,
            # + the effective value health modulates (bd_effective_stats). Default = an average body.
            "str_base": 1.0, "sta_base": 1.0, "str_train": 0.0, "sta_train": 0.0,
            "strength": 1.0, "stamina": 1.0, "stats_dirty": 0.0,
            "stamina_reserve": 1.0})   # short-term endurance: exertion depletes, rest recovers (<= stamina capacity)
        self.eng.add_edge_unchecked(m, "has_body", body)
        self._bodies[name] = body
        # the body's ACTION options the agent collapses over (eat=1, rest=2, acquire=3). The world provides
        # the affordance; the agent DECIDES (bigville_body_choice). `alive` is a PERSISTENT property: while
        # alive, the agent reasons + acts on EVERY tick (no turns). Default off -- opt in via set_alive.
        self.eng.set_attr(m, "alive", 0.0)
        self.eng.set_attr(m, "chosen_action", 0.0); self.eng.set_attr(m, "chosen_val", 0.0)
        # the agent's PLANNING self-model: it understands it (and its household) will get hungry over the days
        # ahead, so it provisions. plan_horizon = days it thinks ahead; daily_ration = a mouth's daily food.
        self.eng.set_attr(m, "plan_horizon", 2.0); self.eng.set_attr(m, "daily_ration", 1.0)
        self.eng.set_attr(m, "larder_capacity", 999.0)   # storage you can afford (set_larder); default ~unbounded
        self.eng.set_attr(m, "can_provision", 0.0); self.eng.set_attr(m, "acq_done", 0.0)
        self.eng.set_attr(m, "provision_good", float(BREAD))   # the good it provisions (for a delegated fetch)
        self.eng.set_attr(m, "route_ready", 0.0)              # myself-or-ask route decided fresh each tick
        self.eng.set_attr(m, "self_cost", 999.0); self.eng.set_attr(m, "best_ask_cost", 999.0)
        for kind in (1.0, 2.0, 3.0):     # eat, rest, acquire-for-later
            opt = self.eng.add_node("BodyOption", {"kind": kind, "value": 0.0})
            self.eng.add_edge_unchecked(m, "may_do", opt)
        return m

    def set_household(self, name, dependents=0):
        """Give the agent a HOUSEHOLD -- `dependents` mouths it PROVIDES FOR (kids at home). Its provisioning
        projection covers itself + everyone it feeds, so a parent lays in far more food than a lone adult
        from the SAME understanding. Mechanical graph data (real dependents, not a magic multiplier)."""
        m = self._movers[name]
        for d in list(self.eng.neighbours(m, "provides_for")):
            self.eng.remove_edge_unchecked(m, "provides_for", d)
        for _ in range(int(dependents)):
            dep = self.eng.add_node("Dependent", {})
            self.eng.add_edge_unchecked(m, "provides_for", dep)

    def set_plan(self, name, *, horizon=None, ration=None, rng=None):
        """The agent's planning self-model: how many days ahead it provisions (horizon) and a mouth's daily
        food need (ration). Pass an rng to DRAW a heterogeneous horizon from the population -- some plan a
        week out, some day-to-day."""
        m = self._movers[name]
        if rng is not None:
            horizon = E.draw_plan_horizon(rng)
        if horizon is not None:
            self.eng.set_attr(m, "plan_horizon", float(horizon))
        if ration is not None:
            self.eng.set_attr(m, "daily_ration", float(ration))

    def set_larder(self, name, capacity=None, *, from_coin=None):
        """The agent's LARDER -- how much food it can STORE (bounds provisioning). Pass `from_coin` to size
        it from wealth (E.larder_for_wealth): the poor keep ~a day and buy daily, the rich buffer in bulk."""
        if from_coin is not None:
            capacity = E.larder_for_wealth(from_coin)
        self.eng.set_attr(self._movers[name], "larder_capacity", float(capacity))

    def larder_capacity(self, name):
        return round(float(self.eng.node(self._movers[name])["attrs"].get("larder_capacity", 0.0)), 4)

    def dependents(self, name):
        return len(list(self.eng.neighbours(self._movers[name], "provides_for")))

    def projected_need(self, name):
        """The food the agent PROJECTS it will need: horizon * ration * (self + dependents)."""
        a = self.eng.node(self._movers[name])["attrs"]
        return round(float(a.get("plan_horizon", 0)) * float(a.get("daily_ration", 0)) * (1 + self.dependents(name)), 4)

    def set_alive(self, name, on=True):
        """Mark an agent ALIVE (autonomous) or not -- a persistent property. While alive, the agent perceives,
        decides (its collapse over eat/rest/acquire-self-or-ask), and acts on EVERY tick. There are no turns."""
        self.eng.set_attr(self._movers[name], "alive", 1.0 if on else 0.0)

    def run_ticks(self, n=1):
        """Advance the world n TICKS -- the engine's native step. Each tick: (1) settle the rule fixpoint,
        in which every alive agent reasons + acts (it may decide to HEAD FOR a source -- a going_to intent);
        (2) MOVE -- every agent heading somewhere takes a step toward it on the map (fetching takes time
        because you walk there); (3) settle again so an agent that ARRIVED trades (co-located). The agents
        run on the map -- this is the driver, not a per-agent turn."""
        for _ in range(int(n)):
            for nm, m in self._movers.items():
                p = self.pos.get(nm)
                if p is not None:                        # coords in the graph so rules can estimate distances
                    self.eng.set_attr(m, "cx", float(p[0])); self.eng.set_attr(m, "cy", float(p[1]))
                if float(self.eng.node(m)["attrs"].get("alive", 0.0)) == 1.0:
                    for k in ("can_provision", "acq_done", "route_ready"):
                        self.eng.set_attr(m, k, 0.0)     # per-tick working state, refreshed each tick
            self.eng.force_all_dirty(); self.eng.run_rules(1_000_000)
            self._step_travellers()                      # everyone heading somewhere walks a step
            self.eng.force_all_dirty(); self.eng.run_rules(1_000_000)   # arrivals trade / deliver (co-located)

    def _step_travellers(self):
        """Move every alive agent that is HEADING FOR someone (a going_to intent) one step toward them on the
        map. Mechanical: read the rule-set navigation intent, point the R1 nav at the target's cell, take the
        rule-decided hop. The DECISION to go is the rule; this only applies the movement it implies."""
        for name, m in list(self._movers.items()):
            if float(self.eng.node(m)["attrs"].get("alive", 0.0)) != 1.0:
                continue
            gts = list(self.eng.neighbours(m, "going_to"))
            if not gts:
                continue
            target = self._cell_xy_of(gts[0])       # where the target is (a person OR a household home)
            if target is None:
                continue
            if tuple(self.pos[name]) != target and target in self._cell_at:
                # ONE energy: the R1 move budget is charged FROM the body's stamina this tick -- a tired body
                # (low reserve) moves slowly or not at all; a rested one moves at pace. Stamina IS the range.
                body = self._bodies.get(name)
                if body is not None:
                    reserve = float(self.eng.node(body)["attrs"].get("stamina_reserve", 1.0))
                    self.eng.set_attr(m, "energy", max(0.0, reserve) * STAMINA_TO_ENERGY)
                self.set_goal(name, target)
                traj = self.move_one(name)
                hops = len(traj or [])
                if hops > 0:
                    # WALKING IS EXERTION: each step draws down the body's stamina and makes you hungrier
                    # (reuses bd_exert_cost -- travel tires + hungers you, feeding back into eat/rest). A long
                    # errand exhausts you. Also builds stamina a little over time (uses_stamina).
                    eff = self.eng.add_node("Effort", {
                        "uses_strength": 0.0, "uses_stamina": 1.0,
                        "intensity": min(1.0, hops * 0.1),
                        "stamina_cost": hops * TRAVEL_STAMINA_PER_HOP,
                        "str_done": 0.0, "sta_done": 0.0, "cost_done": 0.0})
                    self.eng.add_edge_unchecked(m, "exerted", eff)

    def live(self, name, ticks=1):
        """Convenience: make `name` alive and advance `ticks` ticks. Being alive is persistent -- the agent
        goes on reasoning + acting each tick; this just brings it to life and steps the world."""
        self.set_alive(name, True)
        self.run_ticks(ticks)
        return {"name": name, "hunger": self.hunger(name),
                "reserve": self.stamina_reserve(name), "mood": self.mood(name)}

    def set_physique(self, name, *, rng=None, str_base=None, sta_base=None):
        """Seed the body's BASE strength/stamina -- either drawn from the population
        (bigville_entities.draw_physique, pass an rng) or given explicitly. Resets the trained component;
        the effective stat = base * health (health is 1.0 at rest). Mechanical graph data."""
        body = self._bodies[name]
        if rng is not None:
            p = E.draw_physique(rng); str_base, sta_base = p["str_base"], p["sta_base"]
        if str_base is not None:
            self.eng.set_attr(body, "str_base", float(str_base))
        if sta_base is not None:
            self.eng.set_attr(body, "sta_base", float(sta_base))
        self.eng.set_attr(body, "str_train", 0.0); self.eng.set_attr(body, "sta_train", 0.0)
        h = float(self.eng.node(body)["attrs"].get("health", 1.0))
        cap = E.effective_stat(self.eng.node(body)["attrs"]["sta_base"], 0.0, h)
        self.eng.set_attr(body, "strength", E.effective_stat(self.eng.node(body)["attrs"]["str_base"], 0.0, h))
        self.eng.set_attr(body, "stamina",  cap)
        self.eng.set_attr(body, "stamina_reserve", cap)   # start rested (reserve at capacity)

    def perform_task(self, name, *, strength=False, stamina=False, intensity=1.0, stamina_cost=0.0):
        """The villager performs a task that USES strength and/or stamina -- a WORLD EVENT on the body.
        The body slowly BUILDS the stat it used (bd_train_strength / bd_train_stamina, toward a base-relative
        ceiling); a `stamina_cost` also DEPLETES the short-term reserve (bd_exert_cost -- tiring now, fitter
        later). Mechanical: mint the Effort + run the rules; the growth/cost are rules. Returns (strength, stamina)."""
        m = self._movers[name]
        effort = self.eng.add_node("Effort", {
            "uses_strength": 1.0 if strength else 0.0, "uses_stamina": 1.0 if stamina else 0.0,
            "intensity": float(intensity), "stamina_cost": float(stamina_cost),
            "str_done": 0.0, "sta_done": 0.0, "cost_done": 0.0})
        self.eng.add_edge_unchecked(m, "exerted", effort)
        self.eng.force_all_dirty(); self.eng.run_rules(1_000_000)
        return self.strength(name), self.stamina(name)

    def rest(self, name, amount=1.0):
        """The villager RESTS -- a world event that RECOVERS the stamina reserve toward capacity
        (bd_rest_recover). Mechanical: mint the Rest + run the rules. Returns the reserve."""
        m = self._movers[name]
        r = self.eng.add_node("Rest", {"amount": float(amount), "rest_done": 0.0})
        self.eng.add_edge_unchecked(m, "rested", r)
        self.eng.force_all_dirty(); self.eng.run_rules(1_000_000)
        return self.stamina_reserve(name)

    def run_days(self, households, days=1, *, daily_hunger=5.0, ticks_per_day=4):
        """Let the agents LIVE over `days`. Each day everyone gets hungry (the perpetual concern -- you work
        out food every single day) and the world TICKS: on each tick every alive agent perceives, decides
        (eat from the larder if hungry, provision toward its projected need bounded by its larder -- itself or
        by asking someone), and acts. Returns each agent's end-of-day hunger (0 = fed; high = went hungry). No
        world call to eat/buy; the agents decide. Larder + wealth + horizon decide who rides out a lean day."""
        for name in households:
            self.set_alive(name, True)
        log = {name: [] for name in households}
        for _ in range(int(days)):
            for name in households:                       # a new day: everyone gets hungry
                m = self._movers[name]
                h = float(self.eng.node(m)["attrs"].get("hunger_level", 0.0))
                self.eng.set_attr(m, "hunger_level", h + float(daily_hunger))
            self.run_ticks(int(ticks_per_day))            # the world ticks; every alive agent lives
            for name in households:
                log[name].append(self.hunger(name))       # what hunger it ended the day on
        return log

    # ------------------------------------------------------ general task delegation
    def _name_of(self, nid):
        for nm, mid in self._movers.items():
            if mid == nid:
                return nm
        return None

    def _cell_xy_of(self, node):
        """The (x,y) of whatever a node is AT -- reads its is_at edge (works for a person or a household home)."""
        if not hasattr(self, "_xy_of_cell"):
            self._xy_of_cell = {nid: xy for xy, nid in self._cell_at.items()}
        cells = list(self.eng.neighbours(node, "is_at"))
        return self._xy_of_cell.get(cells[0]) if cells else None

    def want_done(self, name, task_kind, *, requirement=0, good=None):
        """The agent wants a TASK done (any task -- fetch bread, deliver a note, ...). `requirement` is a
        capability code the task needs (0 = none); `good` is the good a FETCH task acquires (delivered back
        to this wanter). Mechanical graph data."""
        m = self._movers[name]
        attrs = {"kind": float(task_kind), "requirement": float(requirement),
                 "done": 0.0, "fetch_armed": 0.0,
                 "pursued": 0.0, "pursue_ready": 0.0, "self_cost": 0.0, "ask_cost": 0.0}   # unified pursuit
        if good is not None:
            attrs["good"] = float(good)
        task = self.eng.add_node("Task", attrs)
        self.eng.add_edge_unchecked(m, "wants_done", task)
        self._tasks = getattr(self, "_tasks", {}); self._tasks[name] = task
        return task

    def set_relationship(self, a, b, *, kind="friend", strength=1.0, reliability=1.0,
                         expected_ask=1.0, min_ask=1.0, mutual=False):
        """A's RELATIONSHIP (tie) to B, carrying both sides of a delegation between them:
          * strength     -- how close they are (how freely A can ask B, and B help A).
          * reliability  -- A's model of whether B would actually follow through.
          * expected_ask -- A's model of what B would WANT to do a task (so A can decide what to offer).
          * min_ask      -- B's own bar for helping A (relationship + offer must clear it) -- B's side.
        A close bond => low min_ask (helps freely); a stranger/employee => higher (needs an incentive).
        mutual=True mirrors the tie both ways. The offer A makes is A's OWN decision, never an engine knob."""
        t = self.eng.add_node("Tie", {"kind_name": str(kind), "strength": float(strength),
                                      "reliability": float(reliability), "expected_ask": float(expected_ask),
                                      "min_ask": float(min_ask), "value": 0.0})
        self.eng.add_edge_unchecked(self._movers[a], "tie", t)
        self.eng.add_edge_unchecked(t, "toward", self._movers[b])
        if mutual:
            self.set_relationship(b, a, kind=kind, strength=strength, reliability=reliability,
                                  expected_ask=expected_ask, min_ask=min_ask)
        return t

    def set_capability(self, name, cap_kind):
        """The agent CAN DO a capability (a skill a task may require -- e.g. literacy to deliver a note)."""
        c = self.eng.add_node("Cap", {"kind": float(cap_kind)})
        self.eng.add_edge_unchecked(self._movers[name], "can_do", c)
        return c

    def delegate(self, name):
        """Convenience: bring `name` to life and tick once. A general-task delegation (a task it wants done
        and can ask others to do) is decided by the SAME alive reasoning each tick -- the agent weighs whom by
        requirement, expectation, relationship, and model, decides what to offer ITSELF (from its model + what
        it can afford), and asks; the asked person decides. No incentive is passed in -- a conversation between
        two agents. Returns who it asked and the outcome."""
        self.set_alive(name, True)
        self.run_ticks(1)
        return {"asked": self.delegated_to(name), "status": self.delegation_status(name),
                "offered": self.offer_made(name)}

    def offer_made(self, name):
        """What the delegator offered on its latest request -- its own decision, from its model + means."""
        reqs = list(self.eng.neighbours(self._movers[name], "requests"))
        return round(float(self.eng.node(reqs[-1])["attrs"].get("incentive", 0.0)), 4) if reqs else None

    def delegated_to(self, name):
        """Who the agent asked (the person its latest request was made to), or None if it delegated to no one."""
        reqs = list(self.eng.neighbours(self._movers[name], "requests"))
        if not reqs:
            return None
        tos = list(self.eng.neighbours(reqs[-1], "to"))
        return self._name_of(tos[0]) if tos else None

    def delegation_status(self, name):
        """The outcome of the agent's latest delegation request: 0 pending, 1 accepted, -1 declined."""
        reqs = list(self.eng.neighbours(self._movers[name], "requests"))
        return int(round(float(self.eng.node(reqs[-1])["attrs"].get("status", 0.0)))) if reqs else None

    def took_on_task(self, name):
        """Does this person now have a task they agreed to do (will_do)? -- the accepted delegation."""
        return len(list(self.eng.neighbours(self._movers[name], "will_do"))) > 0

    def stamina_reserve(self, name):
        """The body's current stamina RESERVE (endurance) -- depleted by exertion, restored by rest."""
        return round(float(self.eng.node(self._bodies[name])["attrs"].get("stamina_reserve", 1.0)), 4)

    def hunger(self, name):
        """The villager's hunger_level -- exertion raises it (needs more food); a meal/purchase relieves it."""
        return round(float(self.eng.node(self._movers[name])["attrs"].get("hunger_level", 0.0)), 4)

    def strength(self, name):
        """The body's EFFECTIVE strength (base + trained, scaled by health)."""
        return round(float(self.eng.node(self._bodies[name])["attrs"].get("strength", 1.0)), 4)

    def stamina(self, name):
        """The body's EFFECTIVE stamina (base + trained, scaled by health)."""
        return round(float(self.eng.node(self._bodies[name])["attrs"].get("stamina", 1.0)), 4)

    def _body(self, name):
        return self._bodies[name]

    def body_state(self, name):
        """Glass-box read-off of the BODY's physiology (distinct from the mind's beliefs/choice)."""
        a = self.eng.node(self._bodies[name])["attrs"]
        return {"health": round(float(a.get("health", 1.0)), 4),
                "mood": round(float(a.get("mood", 0.5)), 4),
                "satiety": round(float(a.get("satiety", 0.0)), 4),
                "last_food": a.get("last_food"),
                "strength": round(float(a.get("strength", 1.0)), 4),
                "stamina": round(float(a.get("stamina", 1.0)), 4),
                "str_base": round(float(a.get("str_base", 1.0)), 4),
                "sta_base": round(float(a.get("sta_base", 1.0)), 4)}

    # ------------------------------------------------------------------ ingest
    def add_source(self, name, good, cell):
        """A town good-SOURCE at a walkable `cell` (orchard/bakery/alehouse).
        Global (shared by all villagers); the choice Argmax ranges over these."""
        assert cell in self._cell_at, f"source cell {cell} is not walkable"
        s = self.eng.add_node("Source", {
            "good": float(good), "cx": float(cell[0]), "cy": float(cell[1]),
            "need_code": SUSTENANCE, "travel_cost": BIG,
            "freshness": 1.0})               # a stale stall is less preferred (nd_choose_good scales by it)
        self.eng.add_edge_unchecked(s, "at_cell", self._cell_at[cell])
        self._sources[name] = s
        return s

    def set_source_freshness(self, name, freshness):
        """How fresh a source's goods are (1.0 fresh -> 0.0 stale). In the integrated town this tracks
        the shop's stock condition. Whether a shopper WEIGHS it is held knowledge (see teach_degradation)."""
        self.eng.set_attr(self._sources[name], "freshness", float(freshness))

    def believe_food_feeling_matters(self, name):
        """Seed a shopper with the BELIEF that the food-feeling axis matters (spoiled = bad) -- as if
        already learned. Their buy decision then weighs freshness. A shopper without the belief does not;
        and a naive shopper LEARNS the same belief for itself from a bad meal (see eat/dk_learn)."""
        axis = getattr(self, "_food_axis", None)
        if axis is None:
            axis = self.eng.add_node("Axis", {"minted": 0.0}); self._food_axis = axis
        b = self.eng.add_node("Belief", {"valence": -1.0, "weight": 1.0})
        self.eng.add_edge_unchecked(b, "on_axis", axis)
        self.eng.add_edge_unchecked(self._movers[name], "holds_belief", b)

    # kept name for the older gates: seeding the food belief
    teach_degradation = believe_food_feeling_matters

    def knows_degradation(self, name):
        return len(list(self.eng.neighbours(self._movers[name], "holds_belief"))) > 0

    def eat(self, name, condition):
        """The shopper eats a good; its FEELING is how it felt to eat (its freshness). If that feeling
        was much worse than expected, the SURPRISE makes them mint a new axis + form a belief that
        spoiled food is bad (dk_learn) -- self-taught, no named concept. Mechanical: records the meal +
        the naive prior (food is expected to be good); the surprise and the learning are the rule."""
        m = self._movers[name]
        if self.eng.node(m)["attrs"].get("expected_feeling") in (None, 0.0):
            self.eng.set_attr(m, "expected_feeling", 1.0)     # naive prior (MIND): food is expected to feel good
        # the meal is a WORLD EVENT on the BODY: it harms the body's health (bd_meal_health) AND the
        # MIND learns a belief from the surprise (dk_learn) -- both fire on the one meal node.
        meal = self.eng.add_node("Meal", {"feeling": float(condition), "has_feeling": 1.0,
                                          "health_done": 0.0,
                                          "feeds": 5.0, "fed_done": 0.0})   # eating fills you (relieves hunger)
        self.eng.add_edge_unchecked(m, "ate", meal)
        self.eng.force_all_dirty(); self.eng.run_rules(1_000_000)
        return self.knows_degradation(name)

    def set_neophobia(self, name, neophobia):
        """Set a person's food-neophobia trait (0 variety-seeker .. 1 routine-lover) -- how much monotony
        wears on them. A physical trait: it lives on the BODY (it sets how fast the palate satiates).
        Usually DRAWN from the population (bigville_entities.draw_food_neophobia)."""
        self.eng.set_attr(self._bodies[name], "food_neophobia", float(neophobia))

    def mood(self, name):
        """The eater's mood (a BODY wellbeing, ~0..1). A monotonous diet drags it down; variety holds it up."""
        return round(float(self.eng.node(self._bodies[name])["attrs"].get("mood", 0.5)), 4)

    def eat_meal(self, name, food, liking=0.7):
        """Eat a meal of good `food` with base `liking`. Sensory-specific satiety (the researched
        meal_satisfaction model) discounts it by how many times the SAME food has repeated; the resulting
        satisfaction then moves the agent's MOOD (af_meal_mood, the affect loop). Repetition sinks mood;
        variety holds it. The satiety bookkeeping + the felt satisfaction are mechanical (a researched
        model, like a taste sensor); the MOOD dynamic is the rule."""
        body = self._bodies[name]; a = self.eng.node(body)["attrs"]
        neo = a.get("food_neophobia")
        if neo is None:
            neo = float(E.FOOD_NEOPHOBIA["mean"]); self.eng.set_attr(body, "food_neophobia", neo)
        last, run = a.get("last_food"), int(a.get("food_run", 0))
        run = run + 1 if last == float(food) else 0                  # sensory-specific satiety: same food repeats
        sat = E.meal_satisfaction(liking, run, float(neo))
        # the palate + appetite are BODY physiology (a taste sensor); the MOOD dynamic is a rule on the body.
        self.eng.set_attr(body, "last_food", float(food)); self.eng.set_attr(body, "food_run", float(run))
        self.eng.set_attr(body, "satiety", E.satiety_level(run, float(neo)))   # the appetite the mind reads
        meal = self.eng.add_node("Meal", {"food": float(food), "satisfaction": float(sat),
                                          "has_satisfaction": 1.0, "mood_done": 0.0,
                                          "feeds": 5.0, "fed_done": 0.0})   # eating fills you (relieves hunger)
        self.eng.add_edge_unchecked(self._movers[name], "ate", meal)
        self.eng.force_all_dirty(); self.eng.run_rules(1_000_000)   # af_meal_mood moves the BODY's mood
        return self.mood(name)

    def move_source(self, name, cell):
        """Relocate a source (the flip test moves the orchard FAR). Mechanical:
        re-point at_cell + update cx/cy; the flood recomputes travel_cost."""
        assert cell in self._cell_at, f"source cell {cell} is not walkable"
        s = self._sources[name]
        for c in list(self.eng.neighbours(s, "at_cell")):
            self.eng.remove_edge_unchecked(s, "at_cell", c)
        self.eng.add_edge_unchecked(s, "at_cell", self._cell_at[cell])
        self.eng.set_attr(s, "cx", float(cell[0]))
        self.eng.set_attr(s, "cy", float(cell[1]))
        self.eng.set_attr(s, "travel_cost", BIG)

    def set_preferences(self, name, prefs, *, cost_on=1.0, hunger_threshold=5.0):
        """Attach this villager's heterogeneous PREFERENCE weighting (per-good) +
        the ablation knobs. `prefs` maps good code -> weight (seeded ~Normal per
        villager by the caller). Mechanical graph data."""
        m = self._movers[name]
        self.eng.set_attr(m, "enabled", 1.0)
        self.eng.set_attr(m, "cost_on", float(cost_on))
        self.eng.set_attr(m, "hunger_threshold", float(hunger_threshold))
        for k in ("active_need", "active_urge", "choosing", "choose_armed",
                  "chosen_good", "chosen_cost"):
            self.eng.set_attr(m, k, 0.0)
        self.eng.set_attr(m, "target_cx", -1.0)
        self.eng.set_attr(m, "target_cy", -1.0)
        for c in list(self.eng.neighbours(m, "has_pref")):   # replace any prior prefs
            self.eng.remove_edge_unchecked(m, "has_pref", c)
        for good, w in prefs.items():
            p = self.eng.add_node("Pref", {"good": float(good), "weight": float(w)})
            self.eng.add_edge_unchecked(m, "has_pref", p)

    def set_drive(self, name, need_code, v_d, c_d):
        """Seed / update a drive on the villager. urge=|v_d-c_d| is computed by the
        REUSED `drives` seed. A drive is ABLATED by remove_drive (Harlow 233000)."""
        m = self._movers[name]
        key = (name, float(need_code))
        d = self._drives.get(key)
        if d is None:
            attrs = dict(DRIVE_DEFAULTS)
            attrs.update(name="drive_%d" % int(need_code), need_code=float(need_code))
            d = self.eng.add_node("Drive", attrs)
            self.eng.add_edge_unchecked(m, "has_active_drive", d)
            self._drives[key] = d
        self.eng.set_attr(d, "v_d", float(v_d))
        self.eng.set_attr(d, "c_d", float(c_d))
        self.eng.set_attr(d, "c_d_prev", float(c_d))
        return d

    def remove_drive(self, name, need_code):
        """ABLATE a drive: remove the Drive node + its edge -> no urge -> the
        arbitration finds nothing above threshold -> NO goal (load-bearing)."""
        key = (name, float(need_code))
        d = self._drives.pop(key, None)
        if d is None:
            return
        m = self._movers[name]
        self.eng.remove_edge_unchecked(m, "has_active_drive", d)
        self.eng.remove_node(d)

    # ------------------------------------------------- rule-driven decision
    def _clear_cdist(self):
        for nid in self._cell_at.values():
            self.eng.set_attr(nid, "cdist", BIG)

    def decide(self, name):
        """Run the drive->goal->choice rule fixpoint for ONE villager, in the R1
        two-phase pattern (flood to fixpoint, THEN arm the pick). The DECISIONS are
        all rules; this only sequences the phases, reads the verdict, and wires the
        chosen source cell as the R1 nav target. Returns a glass-box read-off."""
        m = self._movers[name]
        # gate the shared choice flood to THIS villager (like R1's active gate)
        for other in self._movers.values():
            self.eng.set_attr(other, "choosing", 1.0 if other == m else 0.0)
            self.eng.set_attr(other, "choose_armed", 0.0)
        self._clear_cdist()
        self.eng.run_rules(10_000_000)          # phase A: urge+arbitrate+goal+flood
        self.eng.set_attr(m, "choose_armed", 1.0)
        self.eng.run_rules(10_000_000)          # phase B: the choice on settled cost
        self.eng.set_attr(m, "choosing", 0.0)
        self.eng.set_attr(m, "choose_armed", 0.0)
        a = self.eng.node(m)["attrs"]
        goal = self.goal_kind(name)
        out = dict(
            name=name, active_need=int(a.get("active_need", 0)),
            active_urge=float(a.get("active_urge", 0.0)), goal=goal,
            chosen_good=(GOOD_NAME.get(a.get("chosen_good")) if goal == "get_food" else None),
            chosen_good_code=(int(a.get("chosen_good", 0)) if goal == "get_food" else None),
            target=((int(a.get("target_cx", -1)), int(a.get("target_cy", -1)))
                    if goal == "get_food" else None),
            travel_cost=(int(a.get("chosen_cost", 0)) if goal == "get_food" else None))
        # MECHANICAL: wire the rule-chosen source cell as the R1 nav seeks target.
        if out["target"] is not None and out["target"] in self._cell_at:
            self.set_goal(name, out["target"])
        return out

    # ------------------------------------------------- glass-box read-offs
    def goal_kind(self, name):
        m = self._movers[name]
        if list(self.eng.neighbours(m, "has_sustenance_goal")):
            return "get_food"
        if list(self.eng.neighbours(m, "has_rest_goal")):
            return "go_home"
        return None

    def urge_of(self, name, need_code):
        d = self._drives.get((name, float(need_code)))
        return float(self.eng.node(d)["attrs"].get("urge", 0.0)) if d is not None else 0.0

    def source_costs(self, name):
        """Read the per-source travel_cost after a decide (distance from villager)."""
        return {nm: int(self.eng.node(s)["attrs"].get("travel_cost", BIG))
                for nm, s in self._sources.items()}
