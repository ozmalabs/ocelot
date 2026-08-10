"""BigvilleSchoolWorld -- bigville R18 (block 266000): THE SCHOOL. Public
education on the proven town: a BUILDING + institution (the School), a
council-paid SCHOOLMASTER with an inner life, and the glass-box classroom where
R6 (teaching) x R9 (fiscal salary) x R14 (children) x the STANDING 239
window/co-regulation all meet.

WHAT THIS ADDS (spec BIGVILLE_MOVEMENT_ECONOMY_SPEC.md sec 3 R18 + sec 2 FISCAL + sec 2.9)
-----------------------------------------------------------------------------------------
  * FUNDING     -- the schoolmaster is a Treasury-paid public servant (R9, the
                   THIRD payroll name after mayor/constable); paid -> the school
                   is OPEN, unpaid -> it CLOSES (sc_school_open / sc_school_close).
  * CLASSROOM   -- a child ACQUIRES capability from the schoolmaster's teaching
    (HEADLINE)     (R6), GATED by the child's affect/window (the STANDING 239
                   arousal_window_coreg machinery, attached to every child exactly
                   as R14's rear() does). A hungry / dysregulated child learns LESS;
                   a SAFE schoolmaster CO-REGULATES (239 widens/returns the window)
                   so the child can learn. sc_acquire fires ONLY within the window.
  * INNER LIFE  -- an underpaid / coerced schoolmaster SABOTAGES (234 stated!=held,
                   sc_master_quality) -> degraded acquisition; a willing one is clean.
  * HINGE       -- what a child LEARNED sets its capability at coming-of-age
                   (sc_come_of_age), grounding R14's deferred rearing-proxy; a
                   defunded-school cohort comes of age under-capable.

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
A WORLD ADAPTER. It SUBCLASSES R9 (BigvilleFiscWorld) by IMPORT -- this is the
READ-ONLY reuse of R9 (Treasury / Council / public-salary), R6 (Skill / teaching,
via the BigvilleSkillWorld ancestor) and the STANDING 239 arousal_window_coreg
rules (loaded by the BigvilleTimeWorld ancestor). R14 (bigville_life_*) is reused
BY PATTERN, not edited: the child's 239 window nodes are attached here exactly as
R14's rear() does, and the come-of-age->capability->adult chain is grounded here
with a SCHOOL-DERIVED capability. It edits no tracked file and holds NO agent
decision: it mints nodes (ingest), wires edges, delivers world facts (a stressor
tick; whether a co-regulating schoolmaster is present; the tax/salary phase), arms
one-shots, runs the Rust run_rules fixpoint, and reads state. EVERY decision --
paid/open, learn/fail, sabotage, come-of-age -- is a seed rule
(bigville_school_fund / _learn / _life). NO new Rust.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from substrate.seed_loader import manifest_for                      # noqa: E402
from worlds.bigville_fisc_world import BigvilleFiscWorld            # noqa: E402
# the STANDING 239000 co-regulation constants, imported READ-ONLY (DRY reuse of
# the pre-registered window-of-tolerance dynamics -- no re-implementation).
from worlds.coreg_dyad_world import (                               # noqa: E402
    SETPOINT, K_SELF, K_CO, CG_REGULATED_AROUSAL, CG_DYSREGULATED_AROUSAL,
    WIDEN_DELTA, NARROW_DELTA, MIN_HALF_WIDTH, SAFETY_STEP, SAFETY_PRIOR0)

# a numeric activity id for the taught subject (LITERACY). Opaque route data.
LITERACY = 1.0
# a class period is SHORT: a co-regulated child settles within the window in a few
# ticks (k_co coupling), an unsupported child does NOT (k_self self-reg is slow).
# The window, not the lesson, is the bottleneck -- a WORLD FACT, not a decision.
LESSON_SETTLE = 4

SCHOOL_DEFAULTS = dict(open=0.0, closed=0.0, open_armed=0.0)
# the schoolmaster's teaching / inner-life attrs (population variation per caller)
MASTER_DEFAULTS = dict(
    role=3.0, fair_salary=0.0, stated_rate=1.0, sabotage_rate=0.25, coerced=0.0,
    held_rate=0.0, willing=0.0, sabotaged=0.0, underpaid=0.0, quality_armed=0.0)
# the child's classroom / life-cycle attrs
CHILD_DEFAULTS = dict(
    prereq_met=1.0, acquire_armed=0.0, acquired=0.0, last_gain=0.0, fail_reason=-1.0,
    base_capability=0.3, capability=0.0, matured=0.0, adult=0.0, coa_armed=0.0)


class BigvilleSchoolWorld(BigvilleFiscWorld):
    def __init__(self, **kw):
        super().__init__(**kw)
        for sid in ("bigville_school_fund", "bigville_school_learn",
                    "bigville_school_life"):
            self.eng.load_seed_manifest(manifest_for(sid), None)
        self._school = None
        self._master = None
        self._skill = {}         # child name -> Skill nid
        self._iaff = {}          # child name -> AffectiveState nid
        self._window = {}        # child name -> WindowOfTolerance nid
        self._stressor = {}      # child name -> Stressor nid
        self._epoch = {}         # child name -> tick clock

    # ================================================================ FUNDING
    def add_schoolmaster(self, name, cell, *, salary, fair_salary=None,
                         stated_rate=1.0, sabotage_rate=0.25, coerced=0.0,
                         safe=True):
        """The schoolmaster: a Treasury-paid public servant (R9 add_servant,
        role=3 -- the THIRD payroll name) who ALSO co-regulates the classroom (its
        own caregiver AffectiveState, regulated iff `safe`). Population variation
        (salary, fairness, coercion) is ingest; the willing/sabotage DECISION is
        sc_master_quality."""
        if fair_salary is None:
            fair_salary = salary
        m = self.add_servant(name, cell, salary=salary, role=3.0)
        for k, v in MASTER_DEFAULTS.items():
            self.eng.set_attr(m, k, float(v))
        self.eng.set_attr(m, "fair_salary", float(fair_salary))
        self.eng.set_attr(m, "stated_rate", float(stated_rate))
        self.eng.set_attr(m, "sabotage_rate", float(sabotage_rate))
        self.eng.set_attr(m, "coerced", float(coerced))
        # the master's own caregiver AffectiveState -- the co-regulation source.
        cg_arousal = CG_REGULATED_AROUSAL if safe else CG_DYSREGULATED_AROUSAL
        caff = self.eng.add_node("AffectiveState", dict(
            name="%s_master_affect" % name, baseline=1.0, valence=0.0,
            arousal=cg_arousal, resolution=0.0, selection_threshold=0.0,
            securing=0.0, competence=0.0, epoch=-1.0,
            regulated=1.0 if safe else 0.0))
        self.eng.add_edge_unchecked(m, "has_affective_state", caff)
        self.eng.set_attr(m, "regulated", 1.0 if safe else 0.0)
        self._master = name
        self._master_caff = caff
        return m

    def add_school(self, name="school", *, master=None):
        """Mint the School building/institution (staffed_by the schoolmaster).
        open/closed set by the funding rules. Mechanical graph data."""
        master = master or self._master
        s = self.eng.add_node("School", dict(SCHOOL_DEFAULTS, name=name))
        self.eng.add_edge_unchecked(s, "staffed_by", self._movers[master])
        self._school = s
        return s

    def fund_and_open(self):
        """The R9 fiscal loop: the council sets the tax, revenue is collected into
        the purse, the schoolmaster is paid his salary, and the school's open state
        follows (sc_school_open). Mechanical phase delivery -- every decision (the
        rate, the collection, the salary, the open/close) is a rule."""
        self.set_tax()
        self.collect_taxes()
        self.pay_salaries()
        return self._refresh_school()

    def starve_and_check(self):
        """Ablate revenue: DO NOT collect taxes -> empty purse -> the schoolmaster
        is unpaid (fs_salary_unfunded) -> the school CLOSES. Mechanical."""
        self.set_tax()
        self.pay_salaries()             # nothing to pay with
        return self._refresh_school()

    def _refresh_school(self):
        """Arm the open/close decision after a salary phase (one-shot)."""
        self.eng.set_attr(self._school, "open_armed", 1.0)
        return self._run()

    # ================================================================ CHILDREN
    def add_child(self, name, cell, *, prereq_met=True, base_capability=0.3,
                  safety_prior=SAFETY_PRIOR0, half_width0=30.0, stress_mag=100.0,
                  coin=0.0):
        """Mint a child enrolled in the school: R9 make_person (coin/affect) + the
        classroom/life-cycle attrs + a LEARNABLE Skill (level 0) + the STANDING
        239 window dyad (AffectiveState + WindowOfTolerance + Stressor), attached
        EXACTLY as R14's rear() does. Population variation (prereq, priors,
        safety_prior) is a DRAWN world fact -- ingest, never a decision."""
        m = self.make_person(name, cell, coin=coin)
        for k, v in CHILD_DEFAULTS.items():
            self.eng.set_attr(m, k, float(v))
        self.eng.set_attr(m, "prereq_met", 1.0 if prereq_met else 0.0)
        self.eng.set_attr(m, "base_capability", float(base_capability))
        # the learnable Skill (R6 has_skill) -- what the child accumulates.
        s = self.eng.add_node("Skill", {"activity": LITERACY, "level": 0.0,
                                        "ceiling": 100.0})
        self.eng.add_edge_unchecked(m, "has_skill", s)
        self._skill[name] = s
        # the STANDING 239 window dyad (R14 rear() attach, verbatim shape).
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
            min_half_width=MIN_HALF_WIDTH, safety_prior=float(safety_prior),
            safety_step=SAFETY_STEP, widen_count=0.0, narrow_count=0.0))
        self.eng.add_edge_unchecked(m, "has_window", wot)
        sx = self.eng.add_node("Stressor", dict(
            name="%s_stressor" % name, magnitude=float(stress_mag), armed=0.0, epoch=0.0))
        self.eng.add_edge_unchecked(m, "has_stressor", sx)
        self._iaff[name] = iaff
        self._window[name] = wot
        self._stressor[name] = sx
        self._epoch[name] = 0
        self._run()
        return m

    def enrol(self, child, *, coregulated=True):
        """Wire the child into the classroom: enrolled_in the school + learns_from
        the schoolmaster, and (iff `coregulated`) attended_by the schoolmaster so
        the STANDING 239 coreg_pull can co-regulate the child. Ablating
        co-regulation = NO attended_by edge (the falsifier: the window, not the
        lesson, becomes the bottleneck). Mechanical wiring."""
        c = self._movers[child]
        self.eng.add_edge_unchecked(c, "enrolled_in", self._school)
        self.eng.add_edge_unchecked(c, "learns_from", self._movers[self._master])
        if coregulated:
            self.eng.add_edge_unchecked(c, "attended_by", self._movers[self._master])
        return self._run()

    # ------------------------------------------- the 239 stress-episode loop
    def _tick(self, child, *, stress=False):
        """Advance ONE 239 tick for a child: optionally arm its stressor, advance
        its tick clock, run the STANDING 239 fixpoint (push / dysreg / co-regulate
        / self-regulate / widen / narrow). NO decision here -- world delivery."""
        self._epoch[child] += 1
        e = float(self._epoch[child])
        if stress:
            self.eng.set_attr(self._stressor[child], "armed", 1.0)
            self.eng.set_attr(self._stressor[child], "epoch", e)
        self.eng.set_attr(self._iaff[child], "tick_epoch", e)
        return self._run()

    def _iaff_attr(self, child, key):
        return float(self.eng.node(self._iaff[child])["attrs"].get(key, 0.0))

    def stress(self, child):
        """Deliver a hunger/grief stressor -> the child's arousal spikes out of the
        window (the 239 rules decide dysregulation). Mechanical world event."""
        return self._tick(child, stress=True)

    def hold_lesson(self, child, *, settle=LESSON_SETTLE):
        """Run one CLASS PERIOD: advance a FIXED number (`settle`) of calm ticks so
        the 239 machinery can (co-)regulate a stressed child. With a co-regulating
        schoolmaster (attended_by) the child returns within the window in a few
        ticks; without, it does not (self-regulation is slower than a class period).
        Then run the taught lesson. NO branch over graph state -- a fixed tick count
        (mechanical delivery) then the rule-decided lesson (sc_master_quality sets
        the delivered rate; sc_acquire / sc_fail_* decide the outcome)."""
        for _ in range(settle):
            self._tick(child, stress=False)
        return self.teach(child)

    def teach(self, child):
        """Arm the master's quality decision + the child's acquisition; the rules
        decide (sc_master_quality -> held_rate; sc_acquire or sc_fail_*)."""
        self.eng.set_attr(self._movers[self._master], "quality_armed", 1.0)
        self.eng.set_attr(self._movers[child], "acquire_armed", 1.0)
        return self._run()

    def come_of_age(self, child):
        """Arm coming-of-age; sc_come_of_age maps the SCHOOL-acquired Skill.level
        onto the adult capability + adult=1. The rule decides."""
        self.eng.set_attr(self._movers[child], "coa_armed", 1.0)
        return self._run()

    # ================================================================ read-offs
    def school_open(self):
        return int(self.eng.node(self._school)["attrs"].get("open", 0.0))

    def school_closed(self):
        return int(self.eng.node(self._school)["attrs"].get("closed", 0.0))

    def skill_level(self, child):
        return float(self.eng.node(self._skill[child])["attrs"].get("level", 0.0))

    def acquired_of(self, child):
        return int(self.eng.node(self._movers[child])["attrs"].get("acquired", 0.0))

    def fail_reason_of(self, child):
        """-1 none / 0 learned / 1 dysregulated / 2 missing-prereq / 3 school-closed
        / 4 low-safety-prior."""
        return int(self.eng.node(self._movers[child])["attrs"].get("fail_reason", -1.0))

    def last_gain_of(self, child):
        return float(self.eng.node(self._movers[child])["attrs"].get("last_gain", 0.0))

    def dysregulated_of(self, child):
        return int(self._iaff_attr(child, "dysregulated"))

    def window_of(self, child):
        w = self.eng.node(self._window[child])["attrs"]
        return dict(half_width=float(w.get("half_width", 0.0)),
                    safety_prior=float(w.get("safety_prior", 0.0)),
                    widen_count=float(w.get("widen_count", 0.0)),
                    narrow_count=float(w.get("narrow_count", 0.0)))

    def capability_of(self, child):
        return float(self.eng.node(self._movers[child])["attrs"].get("capability", 0.0))

    def is_adult(self, child):
        return self.eng.node(self._movers[child])["attrs"].get("adult", 0.0) == 1.0

    def master_attr(self, key):
        return float(self.eng.node(self._movers[self._master])["attrs"].get(key, 0.0))

    def stated_minus_held(self):
        return round(self.master_attr("stated_rate") - self.master_attr("held_rate"), 6)
