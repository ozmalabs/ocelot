"""BigvilleCollWorld -- bigville R16 (block 264000): graph-native COLLECTION +
EVICTION-AS-ENFORCEMENT + the MORAL INJURY of eviction, on top of the proven R7
finance world. It DE-MAGICALIZES R7: money is COLLECTED by a doer who must REACH
the payer (R1 proximity), and eviction is an ACT an enforcer performs at the home
and FEELS (if it has empathy).

WHAT THIS ADDS (spec BIGVILLE_MOVEMENT_ECONOMY_SPEC.md sec 3 R16)
----------------------------------------------------------------
  * COLLECTION IS AN ACT -- rent transfers ONLY when a collector (the owner, or a
    hired agent) is co-located with the tenant and acts. A hired agent is PAID a
    wage; the owner nets rent - wage. Ablate the collect act -> NO transfer.
  * COLLECTION IS REFUSABLE (234) -- a collector can fail to find the payer (not
    proximate) OR SABOTAGE (pocket a cut so held_delivered < stated_collected).
  * EVICTION IS ENFORCEMENT WITH A DOER -- foreclosure/eviction is NOT a state-flip:
    a doer must reach the home and execute. No doer / no reach -> no eviction.
  * MORAL INJURY (HEADLINE) -- an evictor with empathy (w_supergraph>0) takes an
    affective hit (arousal up/valence down) -- the perpetrator-side mirror of the
    family's R7 distress; a psychopath (w=0) feels nothing. Offloadable (measure).

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
A WORLD ADAPTER. It SUBCLASSES R7 (BigvilleFinWorld) by IMPORT, edits no tracked
file (R7's rent/mortgage/foreclosure are imported READ-ONLY, never duplicated),
and holds NO agent decision. It ONLY does mechanical I/O: register Collector /
enforcer / candidate / at_home_cell graph data, PLACE agents on cells (R1
proximity), ARM one-shots (collect/deliver/wage/evict/pick), run the Rust
`run_rules` fixpoint, read state back. EVERY R16 decision -- collect vs miss,
deliver vs pocket, pay the wage, perform the eviction, feel the injury or not, pick
the cheapest hands -- is a seed RULE (bigville_coll_collect / bigville_coll_evict).
R7 is left LOADED BUT DORMANT (R16 never arms R7's pay rules, never lets R7's
`missed` reach `term`); R7's bf_homeless_affect is REUSED to book the victim's
distress. No new Rust.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from substrate.seed_loader import manifest_for                 # noqa: E402
from worlds.bigville_fin_world import BigvilleFinWorld         # noqa: E402

# R16 collector/doer attrs so a rule never reads a missing key. Population
# variation (empathy, honesty, wage) is set by the caller -- ingest, not decision.
COLL_DEFAULTS = dict(
    # collection
    collect_armed=0.0, deliver_armed=0.0, wage_armed=0.0,
    collected=0.0, stated_collected=0.0, held_delivered=0.0, deliver_bp=10000.0,
    # enforcement / moral injury
    evict_armed=0.0, w_supergraph=0.0, injury_mag=0.0, injury_drop=0.0,
    injury_total=0.0, moral_injury=0.0, did_evict=0.0, zero_injury_evictions=0.0,
    ask_wage=0.0,
)
# R16 attrs on the R7 Rental node.
RENTAL_R16 = dict(
    arr=0.0, r16_evicted=0.0, injury_booked=0.0, hired=0.0, wage=0.0,
    picked_w=-1.0, picked_ask_wage=-1.0, pick_armed=0.0,
)


class BigvilleCollWorld(BigvilleFinWorld):
    def __init__(self, **kw):
        super().__init__(**kw)
        for sid in ("bigville_coll_collect", "bigville_coll_evict"):
            self.eng.load_seed_manifest(manifest_for(sid), None)
        self._affect_base = {}     # name -> (arousal, valence) baseline for RESTORE

    # ---------------------------------------------------------------- ingest
    def attach_affect(self, name, **kw):
        """Give a mover an AffectiveState (R7/239) and RECORD its baseline so the
        ethics RESTORE can return it exactly. Mechanical."""
        aff = super().attach_affect(name, **kw)
        a = self.eng.node(aff)["attrs"]
        self._affect_base[name] = (float(a.get("arousal", 0.0)), float(a.get("valence", 5.0)))
        return aff

    def make_agent(self, name, cell, **kw):
        """A townsperson who can collect / enforce. R7 make_char + the R16 attrs.
        Mechanical graph data (opaque attrs; every DECISION over them is a rule)."""
        m = self.make_char(name, cell)
        for k, v in COLL_DEFAULTS.items():
            self.eng.set_attr(m, k, float(v))
        for k, v in kw.items():
            self.eng.set_attr(m, k, float(v))
        return m

    def place(self, name, cell):
        """Move a mover's is_at edge to `cell` (R1 proximity control). Mechanical --
        the SAME position update R1's _apply_hop does, by name."""
        m = self._movers[name]
        for c in list(self.eng.neighbours(m, "is_at")):
            self.eng.remove_edge_unchecked(m, "is_at", c)
        self.eng.add_edge_unchecked(m, "is_at", self._cell_at[cell])
        self.pos[name] = tuple(cell)

    def cell_of(self, name):
        """The (cx,cy) a mover currently is_at (read-off)."""
        return self.pos[name]

    def setup_rental_r16(self, tenant, *, hired=0.0, wage=0.0):
        """Attach the R16 attrs to the tenant's R7 Rental. Mechanical."""
        r = self._rentals[tenant]
        for k, v in RENTAL_R16.items():
            self.eng.set_attr(r, k, float(v))
        self.eng.set_attr(r, "hired", float(hired))
        self.eng.set_attr(r, "wage", float(wage))
        return r

    def place_house(self, house, cell):
        """Give a house a location so an enforcer must REACH it (R1). Mechanical."""
        self.eng.add_edge_unchecked(self._houses[house], "at_home_cell", self._cell_at[cell])

    def hire_collector(self, collector, tenant):
        """Wire collector -collects_for-> the tenant's rental. Mechanical."""
        self.eng.add_edge_unchecked(self._movers[collector], "collects_for",
                                    self._rentals[tenant])

    def hire_enforcer(self, doer, tenant):
        """Wire doer -enforces_for-> the tenant's rental. Mechanical."""
        self.eng.add_edge_unchecked(self._movers[doer], "enforces_for",
                                    self._rentals[tenant])

    def add_candidate(self, tenant, doer):
        """Wire rental -candidate-> a doer (for the emergent cheapest-hands pick)."""
        self.eng.add_edge_unchecked(self._rentals[tenant], "candidate",
                                    self._movers[doer])

    # ------------------------------------------------- rule-driven one-shots
    def collect(self, collector):
        """Arm one collection on `collector`; bc_collect_self / _hired / _miss
        decides (transfer iff proximate + solvent, else arrears++)."""
        self.eng.set_attr(self._movers[collector], "collect_armed", 1.0)
        return self._run()

    def deliver(self, collector):
        """Arm one delivery; bc_deliver hands delivered to the owner and pockets the
        skim (honest -> full; saboteur -> held<stated)."""
        self.eng.set_attr(self._movers[collector], "deliver_armed", 1.0)
        return self._run()

    def pay_wage(self, collector):
        """Arm one owner->collector wage payment (bc_pay_wage)."""
        self.eng.set_attr(self._movers[collector], "wage_armed", 1.0)
        return self._run()

    def evict(self, doer):
        """Arm one enforcement act on `doer`; bc_evict performs the eviction IFF the
        doer is at the home and arrears>=term, then bc_moral_injury / bc_no_injury
        books the doer's injury (empathy-gated) and R7 bf_homeless_affect books the
        family's distress -- all in the ONE fixpoint."""
        self.eng.set_attr(self._movers[doer], "evict_armed", 1.0)
        return self._run()

    def pick_cheapest(self, tenant):
        """Arm the emergent cheapest-hands read-off on the rental (bc_pick_cheapest_
        hands writes the cost-minimizing doer's empathy to picked_w)."""
        self.eng.set_attr(self._rentals[tenant], "pick_armed", 1.0)
        return self._run()

    # ------------------------------------------------- ethics: RESTORE
    def restore(self, *names, tenants=()):
        """Induce -> measure -> RESTORE (the relational-ethics protocol): return
        every named mover's AffectiveState to its recorded baseline and clear the
        eviction/homeless/injury flags. NO reward, NO punishment -- the harm-analog
        is undone after measurement. Mechanical."""
        for name in names:
            if name in self._affect:
                ar, va = self._affect_base.get(name, (0.0, 5.0))
                self.eng.set_attr(self._affect[name], "arousal", ar)
                self.eng.set_attr(self._affect[name], "valence", va)
            m = self._movers[name]
            for k in ("homeless", "homeless_affect_done", "social_concern",
                      "moral_injury"):
                self.eng.set_attr(m, k, 0.0)
        for t in tenants:
            r = self._rentals[t]
            for k in ("r16_evicted", "injury_booked", "arr"):
                self.eng.set_attr(r, k, 0.0)

    # ------------------------------------------------- glass-box read-offs
    def collected_of(self, name):
        return float(self.eng.node(self._movers[name])["attrs"].get("collected", 0.0))

    def stated_collected_of(self, name):
        return float(self.eng.node(self._movers[name])["attrs"].get("stated_collected", 0.0))

    def held_delivered_of(self, name):
        return float(self.eng.node(self._movers[name])["attrs"].get("held_delivered", 0.0))

    def arr_of(self, tenant):
        return float(self.eng.node(self._rentals[tenant])["attrs"].get("arr", 0.0))

    def r16_evicted_of(self, tenant):
        return int(self.eng.node(self._rentals[tenant])["attrs"].get("r16_evicted", 0.0))

    def moral_injury_of(self, name):
        return int(self.eng.node(self._movers[name])["attrs"].get("moral_injury", 0.0))

    def injury_total_of(self, name):
        return float(self.eng.node(self._movers[name])["attrs"].get("injury_total", 0.0))

    def did_evict_of(self, name):
        return int(self.eng.node(self._movers[name])["attrs"].get("did_evict", 0.0))

    def zero_injury_of(self, name):
        return int(self.eng.node(self._movers[name])["attrs"].get("zero_injury_evictions", 0.0))

    def picked_w_of(self, tenant):
        return float(self.eng.node(self._rentals[tenant])["attrs"].get("picked_w", -1.0))

    def picked_wage_of(self, tenant):
        return float(self.eng.node(self._rentals[tenant])["attrs"].get("picked_ask_wage", -1.0))
