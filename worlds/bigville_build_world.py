"""BigvilleBuildWorld -- bigville R12 (block 260000): graph-native CONSTRUCTION and
the MUTABLE WORLD, on top of the proven R13 LAND / R7 FINANCE world.

WHAT THIS ADDS (spec BIGVILLE_MOVEMENT_ECONOMY_SPEC.md sec 2.8 + sec 3 R12)
--------------------------------------------------------------------------
  * BUILD            -- a BUILDER consumes RAW MATERIALS (timber+stone) + LABOUR (a
                        per-tick step whose SPEED = the builder's CONSTRUCTION skill
                        level) over TIME (multi-tick) to raise a durable BUILDING on
                        an OWNED, FUNDED plot (R13 precondition). bb_consume/bb_raise.
  * TRESPASS         -- building on ANOTHER'S land is refused (bb_trespass); unowned
                        land matches nothing -> refused as absence.
  * FUNDING          -- PERSONAL (coin, bb_fund) OR a BANK LOAN (bb_loan: R7 reserves
                        -> builder coin + a BuildLoan that ACCRUES like a mortgage,
                        bb_loan_accrue). Control: no savings + no loan -> no build.
  * MODIFY / ADD-ON  -- an existing building is extended (bb_addon: more materials ->
                        size+capacity grow).
  * INSTITUTIONAL    -- the CHURCH EXPANDS iff its donations/funds suffice
                        (bb_church_expand; income-gated, a grounded lift of R9).
  * THE MUTABLE WORLD-- a new building marks its map cell blocked+occludes (bb_raise,
                        a RULE mutating the map-belief); bbnav_wall_off SEVERS that
                        cell's walkable adjacency so the existing bigville_move_nav
                        flood RE-ROUTES around it, and the adapter reflects `built`
                        into the host grid so occlusion (can_see) re-queries. Remove
                        it (bb_demolish + adjacency re-ingest) -> the cells revert.

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
A WORLD ADAPTER. It SUBCLASSES R13 (BigvilleLandWorld) by IMPORT, edits no tracked
file, and holds NO agent decision. It ONLY does mechanical I/O: register
Building/BuildLoan/Institution/materials graph data + the plot<->map-cell `on_cell`
edge (ingest); ARM a one-shot (funds / wants_loan / builds+tick_armed / extends /
expand_armed / demolish_armed) or wire a transient edge; run the Rust `run_rules`
fixpoint; reflect the `built` verdict into the host grid; re-establish adjacency on
demolish; and read state. EVERY construction decision -- consume, raise, trespass,
fund, loan, accrue, addon, wall-off, expand, demolish -- is a seed RULE
(bigville_build_construct / bigville_build_mutate). No new Rust.
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
from worlds.bigville_land_world import BigvilleLandWorld             # noqa: E402
from worlds.bigville_sim_world import WALL                           # noqa: E402

CONSTRUCTION = 9.0        # skill activity code for building (matches the seed)
TIMBER = 20.0             # material good codes (match the seed)
STONE = 21.0

# construction attrs set on every buildable plot so a rule never reads a missing key
BUILD_PLOT_DEFAULTS = dict(
    progress=0.0, required=0.0, mat_cost=0.0, build_cost=0.0,
    funded=0.0, tick_armed=0.0,
)


class BigvilleBuildWorld(BigvilleLandWorld):
    def __init__(self, **kw):
        super().__init__(**kw)
        for sid in ("bigville_build_construct", "bigville_build_mutate"):
            self.eng.load_seed_manifest(manifest_for(sid), None)
        self._buildings = {}       # plot name -> Building nid (latest raised)
        self._loans = {}           # builder name -> BuildLoan nid
        self._institutions = {}    # inst name -> Institution nid
        self._timber = {}          # builder name -> timber Good nid
        self._stone = {}           # builder name -> stone Good nid
        self._plot_cell = {}       # plot name -> (x,y) map cell it occupies
        self._orig_tile = {}       # (x,y) -> original grid tile (for demolish revert)

    # ---------------------------------------------------------------- ingest
    def add_buildable_plot(self, name, cell, *, required, mat_cost, build_cost,
                           frontier=False):
        """A plot on a walkable map `cell`, buildable: it needs `required` progress
        (accrued at the builder's skill rate over TIME), consuming `mat_cost` timber
        + stone per tick, and `build_cost` coin to FUND. Wires the plot<->cell
        `on_cell` edge (the map coupling). Mechanical graph data."""
        assert cell in self._cell_at, f"plot cell {cell} is not walkable"
        p = self.add_plot(name, frontier=frontier)          # R13 mints the Plot
        for k, v in BUILD_PLOT_DEFAULTS.items():
            self.eng.set_attr(p, k, float(v))
        self.eng.set_attr(p, "required", float(required))
        self.eng.set_attr(p, "mat_cost", float(mat_cost))
        self.eng.set_attr(p, "build_cost", float(build_cost))
        c = self._cell_at[cell]
        self.eng.set_attr(c, "blocked", 0.0)
        self.eng.set_attr(c, "occludes", 0.0)
        self.eng.add_edge_unchecked(p, "on_cell", c)
        self._plot_cell[name] = tuple(cell)
        self._orig_tile[tuple(cell)] = self.grid[cell[1]][cell[0]]
        return p

    def give_materials(self, builder, *, timber=0.0, stone=0.0):
        """Stock a builder's raw materials as inventory Good nodes (has_timber /
        has_stone edges). Mechanical."""
        m = self._movers[builder]
        tw = self._timber.get(builder)
        if tw is None:
            tw = self.eng.add_node("Good", {"good": TIMBER, "qty": float(timber)})
            self.eng.add_edge_unchecked(m, "has_timber", tw)
            self._timber[builder] = tw
        else:
            self.eng.set_attr(tw, "qty", float(timber))
        st = self._stone.get(builder)
        if st is None:
            st = self.eng.add_node("Good", {"good": STONE, "qty": float(stone)})
            self.eng.add_edge_unchecked(m, "has_stone", st)
            self._stone[builder] = st
        else:
            self.eng.set_attr(st, "qty", float(stone))

    def set_construction_skill(self, builder, level):
        """Attach a CONSTRUCTION competence (yield/speed scales with it). Reuses the
        econ Skill node READ-ONLY (activity=CONSTRUCTION). Mechanical."""
        return self.set_skill(builder, CONSTRUCTION, level)

    def add_church(self, name, cell, *, funds, expand_cost, capacity=1.0):
        """The CHURCH as an Institution occupying a map cell, funded by DONATIONS.
        The EXPANSION decision (funds sufficient) is bb_church_expand. Mechanical."""
        assert cell in self._cell_at, f"church cell {cell} not walkable"
        inst = self.eng.add_node("Institution", {
            "funds": float(funds), "expand_cost": float(expand_cost),
            "capacity": float(capacity), "size": 1.0, "expand_armed": 0.0})
        self.eng.add_edge_unchecked(inst, "occupies", self._cell_at[cell])
        self._institutions[name] = inst
        return inst

    def donate(self, name, amount):
        """A DONATION into the church's funds (R9 tie; mechanical -- the giving is
        the donor's decision elsewhere, this is the transfer into the purse)."""
        inst = self._institutions[name]
        self.eng.set_attr(inst, "funds",
                          float(self.eng.node(inst)["attrs"].get("funds", 0.0)) + float(amount))

    # ------------------------------------------------- rule-driven one-shots
    def _zero_active(self):
        # keep the shared nav flood quiescent during a construction fixpoint
        for m in self._movers.values():
            self.eng.set_attr(m, "active", 0.0)

    def _build_run(self):
        self._zero_active()
        n = self._run()
        self._sync_occlusion()
        self._field_owner = None          # the map changed -> nav field is stale
        return n

    def fund(self, builder, plot):
        """PERSONAL funding: wire the `funds` edge; bb_fund pays build_cost from coin
        (savings or loan proceeds) iff affordable (else funded stays 0)."""
        self.eng.add_edge_unchecked(self._movers[builder], "funds", self._plots[plot])
        return self._build_run()

    def take_loan(self, builder, amount):
        """A construction LOAN: set the principal, wire `wants_loan` to the R7 bank;
        bb_loan issues it (reserves -> builder coin + a BuildLoan). The bank must
        exist (add_bank, R7)."""
        assert self._bank is not None, "add_bank first (R7)"
        self.eng.set_attr(self._movers[builder], "loan_principal", float(amount))
        self.eng.add_edge_unchecked(self._movers[builder], "wants_loan", self._bank)
        self._build_run()
        for ln in self.eng.neighbours(self._movers[builder], "has_loan"):
            self._loans[builder] = ln
        return self._loans.get(builder)

    def accrue_loan(self, builder):
        """One interest period on a construction loan (bb_loan_accrue)."""
        self.eng.set_attr(self._loans[builder], "accrue_armed", 1.0)
        return self._build_run()

    def build_tick(self, builder, plot):
        """ONE construction tick: ensure the `builds` edge, arm tick_armed, run.
        bb_consume advances progress by the builder's skill (consuming materials);
        bb_raise completes + mutates the map when progress reaches required;
        bb_trespass fires instead if the builder does not own the plot."""
        m, p = self._movers[builder], self._plots[plot]
        if p not in list(self.eng.neighbours(m, "builds")):
            self.eng.add_edge_unchecked(m, "builds", p)
        self.eng.set_attr(p, "tick_armed", 1.0)
        n = self._build_run()
        for b in self.eng.neighbours(p, "has_building"):
            self._buildings[plot] = b
        return n

    def build_until_done(self, builder, plot, max_ticks=64):
        """Drive construction to completion (or max_ticks): a mechanical loop of
        build_tick, exactly like R1's move budget loop -- the how-many is bounded, the
        per-tick DECISION (consume/raise/refuse) is the rule's."""
        for _ in range(max_ticks):
            self.build_tick(builder, plot)
            if self.is_built(plot):
                break
        return self.is_built(plot)

    def extend(self, builder, plot):
        """MODIFY / ADD-ON: wire `extends` to the plot's building; bb_addon consumes
        materials and grows size+capacity."""
        b = self._buildings[plot]
        self.eng.add_edge_unchecked(self._movers[builder], "extends", b)
        return self._build_run()

    def expand_church(self, name):
        """Arm an institutional expansion; bb_church_expand grows it IFF funded."""
        self.eng.set_attr(self._institutions[name], "expand_armed", 1.0)
        return self._build_run()

    def demolish(self, plot):
        """Remove a building: bb_demolish clears the state; the adapter re-establishes
        the cell's walkable adjacency (mechanical re-ingest) -> the cells revert."""
        b = self._buildings.get(plot)
        if b is not None:
            self.eng.set_attr(b, "demolish_armed", 1.0)
        self._build_run()
        self._reopen_cell(self._plot_cell[plot])
        self._buildings.pop(plot, None)
        self._sync_occlusion()
        self._field_owner = None

    # ---------------------------------------- mechanical map reflection
    def _sync_occlusion(self):
        """Reflect each plot's rule-decided `built` flag into the host grid so the
        scaffold occlusion query (can_see) re-queries the mutated map. This is the
        _apply_hop pattern (a rule decides; the adapter mirrors it into the host
        channel perception reads), NOT a decision."""
        for name, cell in self._plot_cell.items():
            x, y = cell
            if self.is_built(name):
                self.grid[y][x] = WALL
            else:
                self.grid[y][x] = self._orig_tile[cell]

    def _reopen_cell(self, cell):
        """Re-establish a reverted cell's orthogonal walkable adjacency (mechanical
        re-ingest, identical to the R1 initial map build)."""
        c = self._cell_at.get(cell)
        if c is None:
            return
        x, y = cell
        for (nx, ny) in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            n = self._cell_at.get((nx, ny))
            if n is None:
                continue
            if c not in list(self.eng.neighbours(n, "adj")):
                self.eng.add_edge_unchecked(n, "adj", c)
            if n not in list(self.eng.neighbours(c, "adj")):
                self.eng.add_edge_unchecked(c, "adj", n)

    # ---------------------------------------- nav reachability (glass-box read)
    def can_reach(self, name, start, goal, max_ticks=48):
        """Does mover `name` reach `goal` from `start` over the CURRENT map-belief?
        A mechanical query: teleport to start, seek goal, re-flood, run the RULE-driven
        move_one loop, report arrival. (Used to show a build RE-ROUTES / seals nav.)"""
        m = self._movers[name]
        self._apply_hop(name, m, start)
        self.set_goal(name, goal)
        self._field_owner = None
        for _ in range(max_ticks):
            self.move_one(name)
            if self.pos[name] == tuple(goal):
                return True
        return self.pos[name] == tuple(goal)

    # ------------------------------------------------- glass-box read-offs
    def progress_of(self, plot):
        return float(self.eng.node(self._plots[plot])["attrs"].get("progress", 0.0))

    def funded_of(self, plot):
        return int(self.eng.node(self._plots[plot])["attrs"].get("funded", 0.0))

    def cell_blocked(self, plot):
        c = self._cell_at[self._plot_cell[plot]]
        return int(self.eng.node(c)["attrs"].get("blocked", 0.0))

    def cell_occludes(self, plot):
        c = self._cell_at[self._plot_cell[plot]]
        return int(self.eng.node(c)["attrs"].get("occludes", 0.0))

    def building_count(self):
        return len(list(self.eng.nodes("Building")))

    def building_size(self, plot):
        b = self._buildings.get(plot)
        return float(self.eng.node(b)["attrs"].get("size", 0.0)) if b is not None else 0.0

    def building_capacity(self, plot):
        b = self._buildings.get(plot)
        return float(self.eng.node(b)["attrs"].get("capacity", 0.0)) if b is not None else 0.0

    def timber_of(self, builder):
        tw = self._timber.get(builder)
        return float(self.eng.node(tw)["attrs"].get("qty", 0.0)) if tw is not None else 0.0

    def stone_of(self, builder):
        st = self._stone.get(builder)
        return float(self.eng.node(st)["attrs"].get("qty", 0.0)) if st is not None else 0.0

    def loan_balance_of(self, builder):
        ln = self._loans.get(builder)
        return float(self.eng.node(ln)["attrs"].get("balance", 0.0)) if ln is not None else 0.0

    def has_loan(self, builder):
        return int(self.eng.node(self._movers[builder])["attrs"].get("has_build_loan", 0.0))

    def church_capacity(self, name):
        return float(self.eng.node(self._institutions[name])["attrs"].get("capacity", 0.0))

    def church_size(self, name):
        return float(self.eng.node(self._institutions[name])["attrs"].get("size", 0.0))

    def church_funds(self, name):
        return float(self.eng.node(self._institutions[name])["attrs"].get("funds", 0.0))
