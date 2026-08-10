"""BigvilleFertWorld -- bigville R23 (block 271000): FERTILITY as a graph DECISION.

Built on R22 (BigvilleDoctorWorld -> BigvilleLifeWorld): the doctor / child
mortality driver + the R14 life cycle come in by IMPORT. R18 (schooling cost + the
mother's opportunity cost) and R9 (old-age security / safety net) enter as world
facts the adapter delivers per family -- their wealth->mechanism mapping (a
reduced-form coupling of the four rungs) lives in the MEASUREMENT harness
(scripts/bigville_fert_run.py), never here.

WHAT THIS ADDS (spec BIGVILLE_MOVEMENT_ECONOMY_SPEC.md §3 R23)
-------------------------------------------------------------
  * A FERTILITY DECISION -- each fertile person/couple holds a FertilityState (a
    `has_fertility` edge). Three staged rules (bf_oldage / bf_quantity_quality /
    bf_mortality_replace) compute `fertility` = a desired-births RATE from the
    child benefit vs cost, the old-age-security motive, and the R22 child-mortality
    replacement. `fertility` UPGRADES R14's unconditional birth into an emergent
    `decision_value`.
  * BIRTH FLOWS FROM THE DECISION -- beget() reads the graph's `fertility` and mints
    floor(fertility) children via the honest R14 make_person boundary. Birth is now
    the decision, not a fixed ingest.

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
A WORLD ADAPTER. It SUBCLASSES R22 (BigvilleDoctorWorld) by IMPORT, edits no
tracked file, and holds NO agent decision. It ONLY does mechanical I/O: mint the
FertilityState + wire has_fertility (ingest), deliver world facts (mortality /
school_cost / opp_cost / child_labour_benefit / safety_net -- the mechanism inputs,
set by NAME), arm the one-shot (decide_armed), run the Rust `run_rules` fixpoint,
read state back, and mint children at the honest R14 boundary from the graph's
`fertility`. EVERY fertility decision -- the old-age motive, the quantity-quality
tradeoff (decision_value = benefit - cost), and the mortality replacement -- is a
seed RULE (bf_*), never Python. NO rule (and NO adapter branch) keys fertility on
wealth. NO reward/punishment token. NO new Rust.
"""
from __future__ import annotations

import math
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.seed_loader import manifest_for                        # noqa: E402
from worlds.bigville_doctor_world import BigvilleDoctorWorld          # noqa: E402

# FertilityState attrs -- the mechanism inputs + the staged outputs. A rule never
# reads a missing key; these mirror the missing-tolerant seed reads. NONE of them
# is wealth/coin/class -- the decision is driven ONLY by mechanisms.
FERT_DEFAULTS = dict(
    # one-shot arms (adapter arms decide_armed; the rules chain qq_armed/mort_armed)
    decide_armed=0.0, qq_armed=0.0, mort_armed=0.0,
    # the DECISION inputs (mechanisms, never wealth)
    base_target=2.0,             # the base desired SURVIVING children (a couple)
    child_labour_benefit=0.0,    # child labour useful (cheap kids) -> more
    oldage_value=2.0,            # strength of the old-age-security motive
    safety_net=0.0,              # R9 pension present? (1 -> motive OFF)
    school_cost=0.0,             # R18 schooling investment per child (quality cost)
    opp_cost=0.0,                # the mother's opportunity cost (education) -> fewer
    mortality=0.0,               # R22 child mortality prob [0,1)
    floor=0.0,                   # min desired surviving
    eps=0.01,                    # Div-by-zero guard on survival
    # the staged OUTPUTS (read-offs)
    oldage_motive=0.0, decision_value=0.0, desired_surviving=0.0,
    survival=0.0, fertility=0.0)


class BigvilleFertWorld(BigvilleDoctorWorld):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.eng.load_seed_manifest(manifest_for("bigville_fert_decide"), None)
        self._fert = {}          # person name -> FertilityState nid
        self._begotten = {}      # parent name -> [child names]
        self._cell_cursor = 0    # next free cell for a minted child

    # ================================================================ ingest
    def endow_fertility(self, name, **params):
        """Mint a FertilityState + wire `p has_fertility f`. Mechanical graph data.
        `params` overrides any FERT_DEFAULTS mechanism input (never wealth)."""
        attrs = dict(FERT_DEFAULTS)
        for k, v in params.items():
            assert k in FERT_DEFAULTS, "unknown fertility input %r" % k
            attrs[k] = float(v)
        f = self.eng.add_node("FertilityState", dict(attrs))
        for k, v in attrs.items():
            self.eng.set_attr(f, k, float(v))
        self.eng.add_edge_unchecked(self._movers[name], "has_fertility", f)
        self._fert[name] = f
        return f

    def make_couple(self, name, cell, *, coin=0.0, **params):
        """Convenience: mint a fertile person (R14 make_person) + a FertilityState
        with the given mechanism inputs. Pure mechanical ingest."""
        self.make_person(name, cell, coin=coin)
        return self.endow_fertility(name, **params)

    # ================================================================ world facts
    def set_conditions(self, name, **params):
        """Deliver the mechanism inputs for a family (mortality / school_cost /
        opp_cost / child_labour_benefit / safety_net / ...). A WORLD FACT the
        adapter sets by NAME -- which fertility the graph then decides is the
        rules' call. Set by name only; NO branch on any value."""
        f = self._fert[name]
        for k, v in params.items():
            assert k in FERT_DEFAULTS, "unknown fertility input %r" % k
            self.eng.set_attr(f, k, float(v))

    def decide(self, name):
        """Arm the fertility decision: set decide_armed. The three bf_* rules chain
        in the run_rules fixpoint (old-age -> quantity-quality -> mortality
        replacement) and write `fertility`. The graph decides; this only arms."""
        self.eng.set_attr(self._fert[name], "decide_armed", 1.0)
        return self._run()

    # ================================================================ birth (R14 boundary)
    def beget(self, name, *, parent_link=True):
        """Birth FLOWS FROM THE DECISION: read the graph's `fertility` and mint
        floor(fertility) children at the honest R14 make_person boundary. The COUNT
        is the graph's decision; the mint is mechanical ingest (like R14 birth).
        Returns the number of children minted."""
        n = int(math.floor(self.fertility_of(name)))
        cells = sorted(self._cell_at.keys())
        kids = []
        for i in range(n):
            # a fresh free cell + a fresh name; parent temperament inherited (R14).
            while self._cell_cursor < len(cells):
                cell = cells[self._cell_cursor]
                self._cell_cursor += 1
                nm = "%s_child%d" % (name, i)
                if nm in self._movers:
                    continue
                self.make_person(nm, cell, coin=0.0,
                                 parent=name if parent_link else None)
                kids.append(nm)
                break
        self._begotten[name] = kids
        return len(kids)

    def children_of(self, name):
        return list(self._begotten.get(name, []))

    # ================================================================ read-offs
    def _fattr(self, name, key):
        return float(self.eng.node(self._fert[name])["attrs"].get(key, 0.0))

    def fertility_of(self, name):
        return self._fattr(name, "fertility")

    def decision_value_of(self, name):
        return self._fattr(name, "decision_value")

    def desired_surviving_of(self, name):
        return self._fattr(name, "desired_surviving")

    def oldage_motive_of(self, name):
        return self._fattr(name, "oldage_motive")

    def survival_of(self, name):
        return self._fattr(name, "survival")
