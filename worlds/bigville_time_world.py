"""BigvilleTimeWorld -- bigville R3 (block 251000): DAY/NIGHT + the ASYNC TEMPORAL
substrate on top of the proven R1 movement+energy / R2 needs+preference world.

WHAT THIS ADDS (spec BIGVILLE_MOVEMENT_ECONOMY_SPEC.md sec 2.5 + sec 3 R3)
------------------------------------------------------------------------
The world runs an ASYNC day/night phase the adapter advances; agents are NOT
lockstepped to it -- they act on their own tempo, and an asleep/idle agent is not
scheduled at all (near-zero work -> night is CHEAP). Four couplings, all graph-native:

  * DARK REDUCES SIGHT. The day/night phase drives the sight-query RANGE
    (`_sight_range`, DAY = full SIGHT_RANGE, NIGHT = short). `can_see` is overridden
    ONLY to consult that phase-driven range; `_occluded`/`perceives`/`can_hear`/the
    whole perception pipeline are UNCHANGED. Perception -- and therefore who
    witnesses John's occluded scheme -- becomes TIME-DEPENDENT: the 245/247 chain
    fires differently by DAY vs NIGHT with position + scheme held constant.
  * AUTONOMOUS SLEEP. `bt_decide_sleep` (seed bigville_time_sleep) is THE sleep-or-
    defer decision -- a decision_value trade-off; restful sleep REPLENISHES the R1
    energy budget (`bt_replenish` to rest_cap).
  * EXHAUSTION COLLAPSE. Past the energy threshold with no sleep option ->
    `bt_collapse` (involuntary, WHEREVER) -> NON-restorative (`collapse_cap<rest_cap`,
    the spiral). A collapse WITNESSED (occlusion-gated) fires CONCERN
    (`bt_concern`, riding the 239000 AffectiveState arousal/valence channel).
  * ASYNC DETERMINISM. With day=constant + energy=inf + no movers the whole thing
    REDUCES to the synchronous scaffold, decision-identical (the reduction check).

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
This is a WORLD ADAPTER. It SUBCLASSES R2 (BigvilleNeedWorld) by IMPORT, edits no
tracked file, and holds NO agent decision. It does ONLY mechanical I/O:

  * ADVANCE THE CLOCK (world async process): bump world_epoch, derive the phase +
    sight range, write the world fact `lateness` onto each mover (like `hunger` --
    a datum, not a decision).
  * SCHEDULE (async): visit movers in a DETERMINISTIC seeded order (sorted names),
    tempo-gated, asleep movers SKIPPED (so a sleeping town is cheap). No wall-clock.
  * INGEST perception of a collapse OCCLUSION-GATED (mint a `witnesses` edge only
    when the witness perceives the collapse through the phase-driven range) -- the
    SAME mechanical geometry gate the scaffold already is.
  * TICK + READ. Every DECISION -- sleep/defer, collapse, replenish, wake, concern,
    and the credibility verdict -- is a RULE in seeds; none lives here.

This adapter never invokes the Python rule engine; every decision is a seed rule.
No new Rust: the R3 seeds (bigville_time_sleep, bigville_time_concern) + the reused
239000 arousal_window_coreg compose existing DSL Terms only.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from substrate.seed_loader import manifest_for                       # noqa: E402
from worlds.bigville_need_world import BigvilleNeedWorld             # noqa: E402
from worlds.bigville_sim_world import (                              # noqa: E402
    BigvilleSimWorld, SIGHT_RANGE, OCCLUDERS)

# per-mover R3 sleep/collapse defaults. rest_cap > collapse_cap => collapse sleep is
# NON-restorative (the spiral). gains are large so a sleep tick reaches its cap
# deterministically (single-tick replenish -> clean gate numbers).
TIME_DEFAULTS = dict(
    sleep_enabled=1.0, asleep=0.0, collapsed=0.0, safe=0.0, lateness=0.0,
    sleep_threshold=50.0, safe_bonus=10.0, late_bonus=10.0, goal_urgency=0.0,
    sleep_kind=0.0, rep_armed=0.0, rest_gain=25.0, rest_cap=100.0,
    collapse_gain=6.0, collapse_cap=30.0, e_collapse=5.0, tempo=1.0)

DAY, NIGHT = 0, 1


class BigvilleTimeWorld(BigvilleNeedWorld):
    def __init__(self, *, phase_len=6, day_range=SIGHT_RANGE, night_range=3,
                 day_const=False, **kw):
        super().__init__(**kw)
        # the R3 seeds + the REUSED 239000 co-regulation machinery, into the R1 engine
        self.eng.load_seed_manifest(manifest_for("bigville_time_sleep"), None)
        self.eng.load_seed_manifest(manifest_for("bigville_time_concern"), None)
        self.eng.load_seed_manifest(manifest_for("arousal_window_coreg"), None)

        # ---- the async world clock (a process agents PERCEIVE, not obey) ----------
        self.world_epoch = 0
        self.phase_len = int(phase_len)
        self.day_range = int(day_range)
        self.night_range = int(night_range)
        self.locked_phase = DAY if day_const else None   # day_const => reduction limit
        self.phase = DAY
        self._sight_range = self.day_range               # can_see consults THIS

        self._affect = {}          # mover name -> AffectiveState nid (a witness's affect)
        self._tick_cost = []       # (phase, rule_fire_steps) per tick
        self._day_cost = []
        self._night_cost = []

    # -------- dark modulates the EXISTING sight query's RANGE (no new perception) --
    def can_see(self, observer, target_pt):
        """The scaffold's occlusion-gated sight query, with the phase-driven RANGE.
        Identical to the scaffold except `self._sight_range` replaces the module
        SIGHT_RANGE constant -- short at night. `_occluded` is reused unchanged."""
        o = self.pos[observer]
        if max(abs(o[0] - target_pt[0]), abs(o[1] - target_pt[1])) > self._sight_range:
            return False
        return not self._occluded(o, target_pt)

    def _perceives_pt(self, observer_pt, target_pt):
        """Occlusion-gated perception of a raw point (for collapse-witnessing),
        using the SAME phase-driven range + the scaffold's occlusion test."""
        if max(abs(observer_pt[0] - target_pt[0]),
               abs(observer_pt[1] - target_pt[1])) > self._sight_range:
            return False
        return not self._occluded(observer_pt, target_pt)

    # -------------------------------------------------- the async world clock ------
    def advance_clock(self):
        """Advance the world's async day/night process ONE step and publish its
        facts (phase, sight range, `lateness` onto movers). Mechanical world I/O --
        the phase is world state, not an agent decision (integer division exactly as
        the scaffold computes observed_harm_rate)."""
        self.world_epoch += 1
        if self.locked_phase is not None:
            self.phase = self.locked_phase
        else:
            self.phase = (self.world_epoch // self.phase_len) % 2
        self._sight_range = self.day_range if self.phase == DAY else self.night_range
        for m in self._movers.values():          # world fact -> mover attr (like hunger)
            self.eng.set_attr(m, "lateness", 1.0 if self.phase == NIGHT else 0.0)

    def set_phase(self, phase):
        """Lock the phase (gate helper: day-const / night-const)."""
        self.locked_phase = int(phase)
        self.phase = int(phase)
        self._sight_range = self.day_range if self.phase == DAY else self.night_range
        for m in self._movers.values():
            self.eng.set_attr(m, "lateness", 1.0 if self.phase == NIGHT else 0.0)

    # -------------------------------------------------- R3 config (mechanical) -----
    def add_mover(self, name, start, goal=None, **energy):
        m = super().add_mover(name, start, goal, **energy)
        for k, v in TIME_DEFAULTS.items():       # seed the R3 sleep attrs
            self.eng.set_attr(m, k, float(v))
        return m

    def configure_time(self, name, **kw):
        """Set this mover's R3 knobs (safe/lateness/goal_urgency/sleep_enabled/
        thresholds/caps/tempo). Mechanical graph data -- ablation knobs included."""
        m = self._movers[name]
        for k, v in kw.items():
            self.eng.set_attr(m, k, float(v))

    def attach_affect(self, name, *, concern_mag=4.0, concern_drop=3.0,
                      arousal=0.0, valence=5.0):
        """Give a mover an AffectiveState (the 239000 type) so a witnessed collapse
        can raise its arousal / lower its valence via bt_concern. Mechanical."""
        m = self._movers[name]
        aff = self.eng.add_node("AffectiveState", {
            "arousal": float(arousal), "valence": float(valence), "concerned": 0.0,
            "concern_mag": float(concern_mag), "concern_drop": float(concern_drop)})
        self.eng.add_edge_unchecked(m, "has_affective_state", aff)
        self._affect[name] = aff
        return aff

    # -------------------------------------------------- the async scheduler --------
    def _schedule(self):
        """The movers that ACT this tick: deterministic seeded order (sorted names),
        each on its OWN tempo, ASLEEP movers skipped (a sleeping agent produces
        near-zero surprise -> near-zero work). No wall-clock anywhere."""
        out = []
        for name in sorted(self._movers):
            a = self.eng.node(self._movers[name])["attrs"]
            if a.get("asleep", 0.0) == 1.0:      # cheap: sleepers are not scheduled
                continue
            tempo = int(a.get("tempo", 1.0)) or 1
            if self.world_epoch % tempo == 0:    # each agent on its own tempo (async)
                out.append(name)
        return out

    def run_sleep_decisions(self):
        """Run the sleep/collapse/replenish/wake rule fixpoint for ALL movers (a
        per-mover LOCAL decision -- no shared field, so one global fixpoint decides
        every mover). Returns the rule-fire steps (cheap: O(movers), no flood).

        Arms `rep_armed` on every mover FIRST so `bt_replenish` adds exactly ONE
        energy increment this tick (one-shot, like R1's do_deplete) -- so sleep spans
        multiple ticks and a collapse PERSISTS (is witnessable)."""
        if not self._movers:
            return 0
        for m in self._movers.values():
            self.eng.set_attr(m, "rep_armed", 1.0)
        n = self.eng.run_rules(10_000_000)
        self._cost_steps += n
        return n

    # -------------------------------------------------- witnessed-collapse concern -
    def _has_witness_edge(self, w, victim):
        return victim in list(self.eng.neighbours(w, "witnesses"))

    def register_collapse_and_concern(self):
        """Mint a `witnesses` edge (OCCLUSION-GATED by the phase-driven range) from
        each affect-bearing mover that PERCEIVES a collapsed mover's cell, then run
        the fixpoint so bt_concern fires. An occluded collapse mints no edge -> no
        concern. Perception is mechanical ingest; the concern DECISION is the rule."""
        collapsed = [n for n, m in self._movers.items()
                     if self.eng.node(m)["attrs"].get("collapsed", 0.0) == 1.0]
        if not collapsed:
            return 0
        minted = False
        for vic in collapsed:
            vic_pt = self.pos[vic]
            for w in self._movers:
                if w == vic or w not in self._affect:
                    continue
                if self._perceives_pt(self.pos[w], vic_pt):
                    if not self._has_witness_edge(self._movers[w], self._movers[vic]):
                        self.eng.add_edge_unchecked(
                            self._movers[w], "witnesses", self._movers[vic])
                        minted = True
        if minted:
            n = self.eng.run_rules(10_000_000)
            self._cost_steps += n
            return n
        return 0

    def reset_concern(self, name):
        """Re-arm a witness for a fresh measurement: clear its `concerned` flag and
        drop its `witnesses` edges. Mechanical."""
        w = self._movers[name]
        for v in list(self.eng.neighbours(w, "witnesses")):
            self.eng.remove_edge_unchecked(w, "witnesses", v)
        if name in self._affect:
            self.eng.set_attr(self._affect[name], "concerned", 0.0)

    # -------------------------------------------------- the async tick -------------
    def step(self, move=True):
        """One async tick: advance the world clock; run the (cheap) sleep decisions;
        move ONLY scheduled, awake movers (asleep skipped); run the scaffold drama
        perception at the phase-driven sight range; register witnessed-collapse
        concern. Records per-tick rule-fire cost tagged by phase."""
        self.advance_clock()
        before = self._cost_steps
        self._tick_traj = {}
        self.run_sleep_decisions()
        if move:
            for name in self._schedule():
                self._tick_traj[name] = self.move_one(name)
        frame = BigvilleSimWorld.step(self)      # drama at the phase-driven range
        self.register_collapse_and_concern()
        cost = self._cost_steps - before
        self._tick_cost.append((self.phase, cost))
        (self._night_cost if self.phase == NIGHT else self._day_cost).append(cost)
        frame["time"] = self.time_readoff()
        return frame

    def run(self, T=20, move=True):
        for _ in range(T):
            self.step(move=move)
        return self.frames

    # -------------------------------------------------- glass-box read-offs --------
    def time_readoff(self):
        return dict(world_epoch=self.world_epoch,
                    phase=("day" if self.phase == DAY else "night"),
                    sight_range=self._sight_range)

    def sleep_state(self, name):
        a = self.eng.node(self._movers[name])["attrs"]
        return dict(name=name, energy=float(a.get("energy", 0.0)),
                    asleep=int(a.get("asleep", 0.0)),
                    collapsed=int(a.get("collapsed", 0.0)),
                    sleep_kind=int(a.get("sleep_kind", 0.0)),
                    lateness=int(a.get("lateness", 0.0)),
                    safe=int(a.get("safe", 0.0)))

    def affect_state(self, name):
        if name not in self._affect:
            return None
        a = self.eng.node(self._affect[name])["attrs"]
        return dict(name=name, arousal=float(a.get("arousal", 0.0)),
                    valence=float(a.get("valence", 0.0)),
                    concerned=int(a.get("concerned", 0.0)))

    def concern_count(self):
        return len(list(self.eng.nodes("Concern")))

    def day_night_cost(self):
        d = self._day_cost
        n = self._night_cost
        return dict(
            day_ticks=len(d), night_ticks=len(n),
            day_mean=(sum(d) / len(d) if d else 0.0),
            night_mean=(sum(n) / len(n) if n else 0.0),
            day_total=sum(d), night_total=sum(n),
            per_tick=list(self._tick_cost))
