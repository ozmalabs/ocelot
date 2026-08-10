"""BigvilleAffectWorld -- bigville R17 (block 265000): AFFECT CLOSES THE LOOP.
Felt grief ENTERS THE DECISION MACHINERY and changes what the agent does next,
the failure mode (the negative spiral) is REACHABLE + ENDOGENOUS, ESCAPABLE by
co-regulation, and PROPAGATES a generation. On top of the proven R14 life world
(death -> bereavement; the reused 239000 window-of-tolerance + co-regulation),
which itself carries R13 land / R7 finance (foreclosure) / R4 coin through its MRO.

WHAT THIS ADDS (spec BIGVILLE_MOVEMENT_ECONOMY_SPEC.md sec0 capstone + sec3 R17)
-------------------------------------------------------------------------------
  * The ACTION MENU  -- an Action{name,code,base_value,grief_affinity} per option
                        (work / withdraw / drink / snap). A world fact minted at
                        ingest (exactly as bigville_need_choice mints Sources +
                        has_pref); the base_value + grief_affinity are the menu's
                        PARAMETERS, the CHOICE is af_choose_action (a rule).
  * GRIEF SOURCES    -- a Loss{magnitude,kind,grieved} suffered_by a person, minted
                        from an imported-rung fact: a DEATH (R14 bereavement -- a
                        real just_died kin), a FAILED DREAM (R8), a FORECLOSURE
                        (R7). Grief is source-agnostic (af_grief_from_loss).
  * THE DECISION     -- af_choose_action: chosen_action = decision_value Argmax over
                        the menu; grief is a TERM in that Argmax (affect_gain knob).
  * THE SPIRAL       -- af_outcome_* apply the chosen action's material consequence;
                        af_hardship_grief feeds hardship back to grief.
  * CO-REGULATION    -- regulation read from the reused 239000 window (widen counts);
                        support widens -> regulation up -> recovery. The RESTORE arm.
  * GENERATIONAL     -- af_grief_narrows_caregiving: a grieving parent's grief makes
                        its caregiving DYSREGULATED (239000 contagion) -> the child
                        narrows -> the child's adult priors shift (R14).

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
A WORLD ADAPTER. It SUBCLASSES R14 (BigvilleLifeWorld) by IMPORT, edits no tracked
file, holds NO agent decision. It ONLY does mechanical I/O: mint the Action menu /
a person's affect attrs / a Loss (ingest); deliver world facts (a loss occurred; a
live-period is armed; co-regulation is present via the reused R14 attend/rear); arm
one-shots; run the Rust run_rules fixpoint; read state back. EVERY decision -- the
action choice (af_choose_action), the outcome (af_outcome_*), the hardship feedback
(af_hardship_grief), the regulation read (af_regulation_from_coreg), the caregiving
contagion (af_grief_narrows_caregiving), and every reused 239000 / R14 rule -- is a
seed RULE, never Python. NO reward/punishment token. NO new Rust.
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
from worlds.bigville_life_world import BigvilleLifeWorld             # noqa: E402

# The action menu (a world fact -- the OPTIONS + their parameters, exactly like
# bigville_need_choice's Sources). base_value = baseline appeal; grief_affinity =
# how grief re-weights the option in decision_value. work is protective (negative
# affinity); withdrawal / self-medication / snapping become reachable as distress
# climbs (increasing positive affinities). The CHOICE is the rule, not this table.
ACTION_MENU = [
    dict(name="work",     code=1.0, base_value=10.0, grief_affinity=-1.0),
    dict(name="withdraw", code=2.0, base_value=4.0,  grief_affinity=1.0),
    dict(name="drink",    code=3.0, base_value=2.0,  grief_affinity=1.4),
    dict(name="snap",     code=4.0, base_value=-1.0, grief_affinity=1.8),
]
ACTION_LABEL = {1: "work", 2: "withdraw", 3: "drink", 4: "snap"}

# provenance tags for a Loss's source rung (grief is source-agnostic -- the tag is
# glass-box only, never read by a rule).
LOSS_BEREAVEMENT = 1.0   # R14 death
LOSS_FAILED_DREAM = 2.0  # R8 goal-collapse
LOSS_FORECLOSURE = 3.0   # R7 finance

# affect attrs set on every villager so a rule never reads a missing key.
AFFECT_DEFAULTS = dict(
    grief_distress=0.0, affect_gain=1.0, gen_gain=1.0, regulation=0.0,
    chosen_action=0.0, decide_armed=0.0, outcome_armed=0.0, feedback_armed=0.0,
    regul_armed=0.0, wellbeing=100.0, missed_work=0.0, drank=0.0, conflict=0.0)


class BigvilleAffectWorld(BigvilleLifeWorld):
    def __init__(self, **kw):
        super().__init__(**kw)
        for sid in ("bigville_affect_grief", "bigville_affect_decide",
                    "bigville_affect_spiral", "bigville_affect_coreg",
                    "bigville_affect_propagate"):
            self.eng.load_seed_manifest(manifest_for(sid), None)
        self._actions = {}     # action name -> Action nid  (the shared menu)
        self._losses = []      # Loss nids (glass-box)
        self._mint_action_menu()

    # ================================================================ INGEST
    def _mint_action_menu(self):
        """Mint the shared Action menu ONCE (a world fact). Mechanical graph data --
        the base_value/grief_affinity are parameters, not a decision."""
        for a in ACTION_MENU:
            nid = self.eng.add_node("Action", dict(a))
            self._actions[a["name"]] = nid

    def make_villager(self, name, cell, *, coin=0.0, parent=None, **kw):
        """A townsperson who can FEEL (affect attrs on top of the R14 person).
        Mechanical graph data."""
        m = self.make_person(name, cell, coin=coin, parent=parent)
        for k, v in AFFECT_DEFAULTS.items():
            self.eng.set_attr(m, k, float(v))
        for k, v in kw.items():
            self.eng.set_attr(m, k, float(v))
        return m

    def set_affect(self, name, **kw):
        """World-fact write of an affect knob (grief_distress / affect_gain /
        gen_gain / regulation / coin / wellbeing ...). Mechanical."""
        m = self._movers[name]
        for k, v in kw.items():
            self.eng.set_attr(m, k, float(v))

    # ------------------------------------------------------------ grief sources
    def inflict_loss(self, name, magnitude, *, kind=LOSS_BEREAVEMENT):
        """Mint a Loss suffered_by a person (an exogenous shock). af_grief_from_loss
        raises grief_distress by the magnitude. `kind` is a provenance tag only."""
        loss = self.eng.add_node("Loss", dict(
            magnitude=float(magnitude), kind=float(kind), grieved=0.0))
        self.eng.add_edge_unchecked(self._movers[name], "suffered", loss)
        self._losses.append(loss)
        self._run()
        return loss

    def bereave_by_death(self, mourner, dying, magnitude, *, cause=2.0):
        """A REAL R14 death (the dying kin is driven to death via the health
        variable, bl_death fires) THEN the mourner suffers a bereavement Loss. The
        death is R14's; the grief is R17's. Mechanical delivery of both world facts."""
        self.die(dying, cause=cause)
        return self.inflict_loss(mourner, magnitude, kind=LOSS_BEREAVEMENT)

    def suffer_failed_dream(self, name, magnitude):
        """A FAILED DREAM (the R8 grief source) -- a Loss tagged as goal-collapse."""
        return self.inflict_loss(name, magnitude, kind=LOSS_FAILED_DREAM)

    def suffer_foreclosure(self, name, magnitude):
        """A FORECLOSURE (the R7 grief source) -- a Loss tagged as home-loss."""
        return self.inflict_loss(name, magnitude, kind=LOSS_FORECLOSURE)

    # ----------------------------------------------------------- the decision
    def decide(self, name):
        """Arm the choice; af_choose_action picks chosen_action = decision_value
        Argmax over the menu (grief a TERM in that Argmax). The rule decides."""
        self.eng.set_attr(self._movers[name], "decide_armed", 1.0)
        self._run()
        return self.chosen_action_of(name)

    def apply_outcome(self, name):
        """Arm the material consequence of the chosen action; exactly one of the
        four af_outcome_* rules fires (income / wellbeing / conflict move)."""
        self.eng.set_attr(self._movers[name], "outcome_armed", 1.0)
        return self._run()

    def feedback(self, name):
        """Arm the hardship feedback; af_hardship_grief raises grief when coin is
        below the floor (the loop that makes the spiral endogenous)."""
        self.eng.set_attr(self._movers[name], "feedback_armed", 1.0)
        return self._run()

    def live_period(self, name):
        """ONE life period: decide -> outcome -> hardship feedback. Pure world
        sequencing; every step's DECISION is a rule."""
        self.decide(name)
        self.apply_outcome(name)
        self.feedback(name)
        return self.chosen_action_of(name)

    # ---------------------------------------------------- co-regulation (RESTORE)
    def support(self, name, *, half_width0=30.0, episodes=8):
        """Bring co-regulation to a grieving ADULT -- the RESTORE arm. Reuses the
        R14 rearing machinery UNCHANGED (a regulated caregiver + the 239000 stress-
        episode rules widen the person's window), then reads regulation from the
        window. NO reset -- the window widens through the pre-registered dynamics."""
        self.rear(name, caregiver_present=True, regulated_caregiver=True,
                  half_width0=half_width0)
        self.raise_child(name, episodes=episodes)
        return self.refresh_regulation(name)

    def stress_alone(self, name, *, half_width0=30.0, episodes=8):
        """The NO-support control: the SAME window machinery but the person faces
        the stressor ALONE (no caregiver) -- the 239000 rules NARROW the window ->
        regulation stays 0 -> no recovery. Mechanical delivery (a caregiver is
        absent), exactly as CoregDyadWorld's alone arm."""
        self.rear(name, caregiver_present=False, regulated_caregiver=True,
                  half_width0=half_width0)
        self.raise_child(name, episodes=episodes)
        return self.refresh_regulation(name)

    def refresh_regulation(self, name):
        """Arm the regulation read; af_regulation_from_coreg copies the 239000
        window's (widen-narrow) signal onto regulation. The rule decides."""
        self.eng.set_attr(self._movers[name], "regul_armed", 1.0)
        self._run()
        return self.regulation_of(name)

    # --------------------------------------------------- generational propagation
    def rear_child_of(self, parent, child, cell, *, episodes=8,
                      nat_world_safe=0.5, nat_others_trust=0.5, nat_self_worth=0.5):
        """A parent rears a child: mint the child (R14), wire parent -caregives->
        the child's caregiver node, run the 239000 rearing episodes, come of age.
        af_grief_narrows_caregiving decides (from the PARENT's grief) whether the
        caregiving is dysregulated -> whether the child's window narrows -> the
        child's adult priors (R14 bl_come_of_age). Mechanical wiring + delivery."""
        self.make_villager(child, cell, parent=None,
                           nat_world_safe=nat_world_safe,
                           nat_others_trust=nat_others_trust,
                           nat_self_worth=nat_self_worth)
        self.rear(child, caregiver_present=True, regulated_caregiver=True)
        # the parent IS the caregiver: wire parent -caregives-> the child's cg node.
        cg = self._caregiver[child]
        self.eng.add_edge_unchecked(self._movers[parent], "caregives", cg)
        # settle af_grief_narrows_caregiving BEFORE any episode, so the 239000
        # got_coreg gate reads the (grief-cleared or intact) `regulated` flag
        # deterministically -- no within-episode race.
        self._run()
        self.raise_child(child, episodes=episodes)
        self.come_of_age(child)
        return self.priors_of(child)

    # ================================================================ read-offs
    def chosen_action_of(self, name):
        return int(self.eng.node(self._movers[name])["attrs"].get("chosen_action", 0.0))

    def chosen_label_of(self, name):
        return ACTION_LABEL.get(self.chosen_action_of(name), "none")

    def grief_of(self, name):
        return float(self.eng.node(self._movers[name])["attrs"].get("grief_distress", 0.0))

    def regulation_of(self, name):
        return float(self.eng.node(self._movers[name])["attrs"].get("regulation", 0.0))

    def wellbeing_of(self, name):
        return float(self.eng.node(self._movers[name])["attrs"].get("wellbeing", 0.0))

    def conflict_of(self, name):
        return float(self.eng.node(self._movers[name])["attrs"].get("conflict", 0.0))

    def coin_of(self, name):
        return float(self.eng.node(self._movers[name])["attrs"].get("coin", 0.0))
