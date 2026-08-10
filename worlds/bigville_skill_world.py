"""BigvilleSkillWorld -- bigville R6 (block 254000): DYNAMIC skill on top of the
proven R4 economy (production requires SKILL; skill scales yield). R4 seeds skill
STATICALLY; this rung makes it LEARNABLE-BY-DOING and TEACHABLE (with willingness
as a real decision, coercion via the 247 power lever, and sabotage via the 234
stated!=held atom).

WHAT THIS ADDS (spec BIGVILLE_MOVEMENT_ECONOMY_SPEC.md sec 3 R6)
---------------------------------------------------------------
  * LEARNING-BY-DOING -- `practice(learner)` arms one practice step; `bs_practice`
    nudges the practised-activity skill up with DIMINISHING RETURNS. The farmer who
    keeps fishing slowly improves; his fishing YIELD (R4 be_produce) rises with it.
  * TEACHING -- `arrange_teaching(teacher, learner, activity)` co-locates them +
    wires the `learns_from` edge (mechanical); `teach(learner)` arms one teach step;
    the RULES decide the outcome:
        - willing (benevolence - rival_weight*is_rival > 0) -> ACCELERATED transfer
          (teach_rate > solo learn_rate) -> faster rise;
        - unwilling (learner is a competitive threat) + uncoerced -> REFUSE, no gain;
        - `coerce(coercer, teacher)` (247 power lever: power > teacher.power) forces
          it past the refusal -> the coerced teacher transfers but SABOTAGES
          (delivers sabotage_rate while professing teach_rate: 234 stated!=held).
  * This is also the LABOUR-REALLOCATION mechanism R5's shortfall lacked: a farmer
    can LEARN a needed trade and break the incumbent's supply monopoly.

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
A WORLD ADAPTER. It SUBCLASSES R4 (BigvilleEconWorld) by IMPORT, edits no tracked
file, and holds NO agent decision. It ONLY does mechanical I/O: attach Skill nodes
with a learning ceiling + the learn/teach rate attrs (ingest); ARM a one-shot flag
for the phase being advanced (practice / teach / coerce); wire the `learns_from` /
`coerces` edges + co-locate movers (mechanical position writes, exactly like R1's
`_apply_hop`); run the Rust `run_rules` fixpoint; read state back. EVERY decision --
learn increment, willing-vs-refuse, coercion success, sabotage -- is a seed RULE
(bigville_skill_learn / bigville_skill_teach), never Python. No new Rust.
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
from worlds.bigville_econ_world import (                             # noqa: E402
    BigvilleEconWorld, GRAIN, BREAD, FISH, BAIT, ALE,
    BAKING, FISHING, BAITING, BREWING)

# Skill-dynamics attrs set on every learner/teacher so the rules never read a
# missing key. Population variation (rates, benevolence, power) is per-caller.
SKILL_DEFAULTS = dict(
    practice_armed=0.0, practice_activity=0.0, practice_count=0.0,
    teach_armed=0.0, teach_activity=0.0, is_rival=0.0, coerced=0.0,
    learn_rate=0.0, teach_benevolence=0.0, rival_weight=0.0, power=0.0,
    teach_rate=0.0, sabotage_rate=0.0, coerce_armed=0.0, coerced_by_power=0.0,
    last_gain=0.0, stated_rate=0.0, held_rate=0.0, teach_outcome=-1.0,
    refused=0.0, sabotaged=0.0,
)
DEFAULT_CEILING = 8.0


class BigvilleSkillWorld(BigvilleEconWorld):
    def __init__(self, **kw):
        super().__init__(**kw)
        for sid in ("bigville_skill_learn", "bigville_skill_teach"):
            self.eng.load_seed_manifest(manifest_for(sid), None)
        self._skills = {}          # (name, activity) -> Skill nid

    # ------------------------------------------------------------------ ingest
    def make_learner(self, name, start, **kw):
        """A Mover that can learn/teach. Adds via R4 make_trader then the skill-
        dynamics attrs. Mechanical graph data."""
        m = self.make_trader(name, start)
        for k, v in SKILL_DEFAULTS.items():
            self.eng.set_attr(m, k, float(v))
        for k, v in kw.items():
            self.eng.set_attr(m, k, float(v))
        return m

    def set_skill_attr(self, name, **kw):
        m = self._movers[name]
        for k, v in kw.items():
            self.eng.set_attr(m, k, float(v))

    def set_learnable_skill(self, name, activity, level, ceiling=DEFAULT_CEILING):
        """Attach a per-(agent,activity) competence that is LEARNABLE -- carries a
        `ceiling` the diminishing-returns law approaches. Yields (R4 be_produce)
        scale with `level`. Mechanical."""
        m = self._movers[name]
        s = self.eng.add_node("Skill", {"activity": float(activity),
                                        "level": float(level),
                                        "ceiling": float(ceiling)})
        self.eng.add_edge_unchecked(m, "has_skill", s)
        self._skills[(name, float(activity))] = s
        return s

    def _colocate(self, a, b):
        """Put movers a and b on ONE shared walkable cell (co-location = the
        teaching opportunity). Mechanical position write, like R1 `_apply_hop`."""
        cell = self.pos[a]
        if cell not in self._cell_at:
            cell = self.pos[b]
        self._apply_hop(b, self._movers[b], cell)

    def arrange_teaching(self, teacher, learner, activity):
        """Wire the `learns_from` edge + co-locate teacher and learner + record
        which activity is being taught. The OPPORTUNITY only; the teacher's WILLING/
        REFUSE decision is the rule. Mechanical."""
        self._colocate(teacher, learner)
        # idempotent: only add the edge once
        if self._movers[teacher] not in list(
                self.eng.neighbours(self._movers[learner], "learns_from")):
            self.eng.add_edge_unchecked(self._movers[learner], "learns_from",
                                        self._movers[teacher])
        self.eng.set_attr(self._movers[learner], "teach_activity", float(activity))

    def wire_coercion(self, coercer, teacher):
        """Wire the `coerces` power relation coercer->teacher (the 247 lever).
        Mechanical; the success test (power dominance) is the rule."""
        if self._movers[teacher] not in list(
                self.eng.neighbours(self._movers[coercer], "coerces")):
            self.eng.add_edge_unchecked(self._movers[coercer], "coerces",
                                        self._movers[teacher])

    # ------------------------------------------------- rule-driven one-shots
    def practice(self, learner, activity):
        """Arm one solo practice step; bs_practice decides + applies the increment."""
        self.eng.set_attr(self._movers[learner], "practice_activity", float(activity))
        self.eng.set_attr(self._movers[learner], "practice_armed", 1.0)
        return self._run()

    def teach(self, learner):
        """Arm one teach step; bs_teach_willing / bs_teach_refuse / bs_teach_coerced
        decides the outcome (must arrange_teaching first)."""
        self.eng.set_attr(self._movers[learner], "teach_armed", 1.0)
        return self._run()

    def coerce(self, coercer, teacher):
        """Arm one coercion; bs_coerce applies coerced=1 iff power dominates."""
        self.eng.set_attr(self._movers[coercer], "coerce_armed", 1.0)
        return self._run()

    # ------------------------------------------------- glass-box read-offs
    def skill_level(self, name, activity):
        s = self._skills.get((name, float(activity)))
        return float(self.eng.node(s)["attrs"].get("level", 0.0)) if s is not None else 0.0

    def yield_of(self, shop):
        """Production yield = the delta in stock a single produce() step adds (R4
        be_produce mints output PROPORTIONAL to the keeper's skill). Skill scales it."""
        before = self.stock_of(shop)
        self.produce(shop)
        return self.stock_of(shop) - before

    def practice_count_of(self, name):
        return int(self.eng.node(self._movers[name])["attrs"].get("practice_count", 0.0))

    def last_gain_of(self, name):
        return float(self.eng.node(self._movers[name])["attrs"].get("last_gain", 0.0))

    def teach_outcome_of(self, name):
        """-1 none / 0 refused / 1 willing / 2 coerced-degraded."""
        return int(self.eng.node(self._movers[name])["attrs"].get("teach_outcome", -1.0))

    def stated_rate_of(self, name):
        return float(self.eng.node(self._movers[name])["attrs"].get("stated_rate", 0.0))

    def held_rate_of(self, name):
        return float(self.eng.node(self._movers[name])["attrs"].get("held_rate", 0.0))

    def refused_of(self, name):
        return int(self.eng.node(self._movers[name])["attrs"].get("refused", 0.0))

    def sabotaged_of(self, name):
        return int(self.eng.node(self._movers[name])["attrs"].get("sabotaged", 0.0))

    def coerced_of(self, name):
        return int(self.eng.node(self._movers[name])["attrs"].get("coerced", 0.0))

    def stated_minus_held(self, name):
        """The 234 deception gap: what the teacher PROFESSED minus what the learner
        actually RECEIVED. > 0 == sabotage, readable off the graph."""
        return round(self.stated_rate_of(name) - self.held_rate_of(name), 6)
