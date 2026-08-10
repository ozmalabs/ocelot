"""BigvilleGoalWorld -- bigville R8 (block 256000): the IDENTITY / SOUL layer on
top of the proven R4 economy / R5 loop / R6 skill / R7 finance world. A soul is
more than a utility function: it carries a long-horizon GROUNDED **life-goal**
that ORIENTS its sub-goal choices, and an ungrounded high-valence **dream** (an
ESCAPE fantasy) whose job is AFFECT REGULATION and which may one day COLLAPSE
into leaving.

WHAT THIS ADDS (spec BIGVILLE_MOVEMENT_ECONOMY_SPEC.md sec 2.6 + sec 3 R8)
--------------------------------------------------------------------------
  * LIFE-GOAL      -- a `LifeGoal{aim, orient_weight}` at the goal-hierarchy root,
                      GROUNDED (a `path_to` edge in the map-belief). It biases the
                      `decision_value` Argmax over the soul's `considers` sub-
                      options (gg_orient_choice): save > leisure for a
                      become-wealthy soul; ablate the has_life_goal edge -> the
                      bias vanishes -> leisure wins.
  * DREAM          -- a `Dream{relief_valence, relief_arousal, aversive_threshold,
                      collapse_threshold}` held UNGROUNDED (NO grounded_path edge).
                      Under aversive valence it is INVOKED for TEMPORARY RELIEF
                      (gg_dream_relief) without changing any material attr; it
                      COLLAPSES into an ActionGoal{kind:leave} when the present is
                      unbearable (gg_dream_collapse_threshold) OR a recruiter mints
                      a grounded_path (gg_dream_collapse_path); else it stays LATENT
                      (gg_dream_latent -- resignation).

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
A WORLD ADAPTER. It SUBCLASSES R7 (BigvilleFinWorld) by IMPORT (so aversive
valence can be induced through the REAL R7 foreclosure/homeless distress channel),
edits no tracked file, and holds NO agent decision. It ONLY does mechanical I/O:
register LifeGoal / Dream / SubOption / ChoicePoint / Dest graph data + wire the
has_life_goal / has_dream / considers / weighs / path_to / grounded_path edges
(ingest); ARM a one-shot flag for the phase being advanced (orient / audit /
relief / collapse); run the Rust `run_rules` fixpoint; read state back. EVERY
soul-layer decision -- which sub-goal, ungrounded audit, dream-invoked relief,
collapse-into-leaving, latent resignation -- is a seed RULE (bigville_goal_life /
bigville_goal_dream), never Python. No new Rust.
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
from worlds.bigville_fin_world import BigvilleFinWorld               # noqa: E402

# sub-option aim codes (which life-goal aim an option SERVES) + option codes.
AIM_WEALTH = 1.0
SAVE, LEISURE = 1.0, 2.0

# soul-layer attrs set on every soul so a rule never reads a missing key. The
# population variation (life-goal aim/weight, dream valences/thresholds) is set
# by the caller -- ingest, not a decision (the R4/R6/R7 *_DEFAULTS pattern).
GOAL_DEFAULTS = dict(
    orient_armed=0.0, audit_armed=0.0, relief_armed=0.0, collapse_armed=0.0,
    chosen_subgoal=-1.0, left=0.0, resigned=0.0,
)


class BigvilleGoalWorld(BigvilleFinWorld):
    def __init__(self, **kw):
        super().__init__(**kw)
        for sid in ("bigville_goal_life", "bigville_goal_dream"):
            self.eng.load_seed_manifest(manifest_for(sid), None)
        self._life_goals = {}   # soul name -> LifeGoal nid
        self._dreams = {}       # soul name -> Dream nid

    # ---------------------------------------------------------------- ingest
    def make_soul(self, name, start, **kw):
        """A townsperson with an identity (life-goal + dream capable). R7
        make_char (coin + finance attrs) + the soul-layer attrs. Mechanical."""
        m = self.make_char(name, start, **kw)
        for k, v in GOAL_DEFAULTS.items():
            self.eng.set_attr(m, k, float(v))
        return m

    def set_soul_attr(self, name, **kw):
        m = self._movers[name]
        for k, v in kw.items():
            self.eng.set_attr(m, k, float(v))

    def set_life_goal(self, name, *, aim=AIM_WEALTH, orient_weight=3.0):
        """Seed a long-horizon GROUNDED life-goal at the goal-hierarchy root. The
        `path_to` edge is the map-belief path that makes it GROUNDED (the grounded
        side of the boundary), unlike a dream. Mechanical graph data."""
        m = self._movers[name]
        lg = self.eng.add_node("LifeGoal", {
            "aim": float(aim), "orient_weight": float(orient_weight),
            "grounded_flag": 0.0})
        self.eng.add_edge_unchecked(m, "has_life_goal", lg)
        dest = self.eng.add_node("Dest", {"kind": "life_goal_dest"})
        self.eng.add_edge_unchecked(lg, "path_to", dest)     # grounded path
        self._life_goals[name] = lg
        return lg

    def ablate_life_goal(self, name):
        """Drop the has_life_goal edge (the ablation): the orient Argmax loses its
        long-horizon bias -> the base appeal alone decides. Mechanical."""
        self.eng.remove_edge_unchecked(self._movers[name], "has_life_goal",
                                       self._life_goals[name])

    def add_suboption(self, name, code, *, base_appeal, serves_aim):
        """A REACHABLE sub-option the soul `considers` (e.g. SAVE vs LEISURE). Its
        base_appeal is its short-horizon pull; serves_aim says which life-goal aim
        it advances. Mechanical graph data."""
        opt = self.eng.add_node("SubOption", {
            "code": float(code), "base_appeal": float(base_appeal),
            "serves_aim": float(serves_aim)})
        self.eng.add_edge_unchecked(self._movers[name], "considers", opt)
        return opt

    def add_choicepoint(self, name):
        """A ChoicePoint the soul `weighs` (the anchor the orient rule matches on,
        present with or without a life-goal so the ablation still chooses).
        Mechanical."""
        cp = self.eng.add_node("ChoicePoint", {})
        self.eng.add_edge_unchecked(self._movers[name], "weighs", cp)
        return cp

    def set_dream(self, name, *, kind="join_navy", relief_valence=3.0,
                  relief_arousal=2.0, aversive_threshold=5.0,
                  collapse_threshold=0.0):
        """Seed an UNGROUNDED escape dream (NO grounded_path edge -- the ungrounded
        side of the boundary). Under aversive valence it regulates affect; past a
        threshold or given a path it collapses. Mechanical graph data."""
        m = self._movers[name]
        dr = self.eng.add_node("Dream", {
            "kind": kind, "relief_valence": float(relief_valence),
            "relief_arousal": float(relief_arousal),
            "aversive_threshold": float(aversive_threshold),
            "collapse_threshold": float(collapse_threshold),
            "ungrounded": 0.0, "invoked": 0.0, "collapsed": 0.0, "latent": 0.0})
        self.eng.add_edge_unchecked(m, "has_dream", dr)
        self._dreams[name] = dr
        return dr

    def recruiter_arrives(self, name):
        """A recruiter in town: mint a `grounded_path` edge on the dream (a real
        path from here APPEARS). Mechanical ingest; the collapse DECISION is the
        rule (gg_dream_collapse_path)."""
        dr = self._dreams[name]
        dest = self.eng.add_node("Dest", {"kind": "recruiter_dest"})
        self.eng.add_edge_unchecked(dr, "grounded_path", dest)
        return dest

    # ------------------------------------------------- rule-driven one-shots
    def orient(self, name):
        """Arm the sub-goal SELECTION; gg_orient_choice runs the decision_value
        Argmax (life-goal-biased) and writes chosen_subgoal."""
        self.eng.set_attr(self._movers[name], "orient_armed", 1.0)
        return self._run()

    def audit(self, name):
        """Arm the grounding-boundary audit; gg_lifegoal_grounded /
        gg_dream_ungrounded classify the goal vs the dream by edge presence."""
        self.eng.set_attr(self._movers[name], "audit_armed", 1.0)
        return self._run()

    def invoke_relief(self, name):
        """Arm one dream invocation; gg_dream_relief gives temporary affect relief
        iff the present is aversive (and does NOT touch material state)."""
        self.eng.set_attr(self._movers[name], "relief_armed", 1.0)
        return self._run()

    def try_collapse(self, name):
        """Arm the collapse test; exactly one of gg_dream_collapse_threshold /
        gg_dream_collapse_path / gg_dream_latent fires."""
        self.eng.set_attr(self._movers[name], "collapse_armed", 1.0)
        return self._run()

    # ------------------------------------------------- glass-box read-offs
    def chosen_subgoal_of(self, name):
        return float(self.eng.node(self._movers[name])["attrs"].get(
            "chosen_subgoal", -1.0))

    def lifegoal_grounded_of(self, name):
        lg = self._life_goals.get(name)
        return int(self.eng.node(lg)["attrs"].get("grounded_flag", 0.0)) if lg else 0

    def lifegoal_has_path(self, name):
        """Structural read: does the life-goal carry a grounded `path_to` edge?"""
        lg = self._life_goals.get(name)
        return bool(lg and list(self.eng.neighbours(lg, "path_to")))

    def dream_state(self, name):
        dr = self._dreams.get(name)
        if dr is None:
            return None
        a = self.eng.node(dr)["attrs"]
        return dict(
            kind=a.get("kind"),
            ungrounded=int(a.get("ungrounded", 0.0)),
            invoked=int(a.get("invoked", 0.0)),
            collapsed=int(a.get("collapsed", 0.0)),
            latent=int(a.get("latent", 0.0)),
            has_grounded_path=bool(list(self.eng.neighbours(dr, "grounded_path"))))

    def left_of(self, name):
        return int(self.eng.node(self._movers[name])["attrs"].get("left", 0.0))

    def resigned_of(self, name):
        return int(self.eng.node(self._movers[name])["attrs"].get("resigned", 0.0))

    def action_goal_kinds(self, name):
        """The kinds of any minted ActionGoal the soul now holds (a collapse mints
        exactly one ActionGoal{kind:leave})."""
        out = []
        for g in self.eng.neighbours(self._movers[name], "has_goal"):
            n = self.eng.node(g)
            if n["type"] == "ActionGoal":
                out.append(n["attrs"].get("kind"))
        return out
