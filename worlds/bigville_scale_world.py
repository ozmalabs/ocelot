"""BigvilleScaleWorld -- the SCALE-VERIFICATION instrument (block 248000).

Wraps the PROVEN scaffold ``BigvilleSimWorld`` (block 245000) UNCHANGED (imported,
never edited) and places N inhabitants on a CONSTANT-DENSITY village lattice to
MEASURE the realized-interaction operator count as a function of N. This is a
WORLD ADAPTER + a COUNTING INSTRUMENT: it does INGEST (positions -> observations),
runs the drama's own ``run_rules()`` (the decisions stay graph-native), and EMITS
a count. Every conditional here is over WORLD state (grid geometry, tick) -- never
over an agent's graph valuation. NO Rust; the drama's integer-native seed is reused
byte-for-byte. (`experiments/gamma-substrate/CLAUDE.md`.)

WHAT IS COUNTED -- the REALIZED interaction-ops per tick: ordered perception pairs
``(observer, target)`` that PASS the scaffold's sight/hearing gate (Chebyshev range
+ Bresenham line-of-sight + occlusion), NOT possible pairs. Two arms:

  * ``sparse``   -- proximity/LOS-gated. Constant density => E[ops] = N*k (LINEAR).
  * ``all_pairs``-- the SAME census with the gate REMOVED: every ordered pair
                    counts, ops = N*(N-1) (QUADRATIC). This is exactly what an
                    accidental all-pairs sweep would produce -- the falsifier that
                    MUST be able to measure ~2.0, proving the instrument can tell
                    linear from quadratic.

Density is held CONSTANT on a TORUS (periodic boundaries) so the perception window
never covers the whole village and there are no perimeter/edge artifacts -- the
N-scaling is isolated. A bigger village for more people, the same local
neighbourhood: the bounded-degree thesis, made a measurement.
"""
from __future__ import annotations

import math
import os
import sys
import time

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))

# the scaffold, imported UNCHANGED (subclass/compose, never edit)
from worlds.bigville_sim_world import (                      # noqa: E402
    BigvilleSimWorld, _line, OCCLUDERS, TREE, WALL, SIGHT_RANGE, HEAR_RANGE)

# the mechanical population generator (Deliverable 1). scripts/ is not a package;
# import the module by file path so the draw is shared with the seed manifest.
import importlib.util                                        # noqa: E402
_spec = importlib.util.spec_from_file_location(
    "bigville_town_seed",
    os.path.join(_ROOT, "scripts", "bigville_town_seed.py"))
_town = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_town)
draw_population = _town.draw_population
population_param_sd = _town.population_param_sd

PERCEIVE_RANGE = HEAR_RANGE               # perceive = see OR hear; hearing is wider
PERC_WINDOW = (2 * PERCEIVE_RANGE + 1) ** 2 - 1     # torus neighbourhood cell count


class BigvilleScaleWorld:
    """N inhabitants on a constant-density torus, perceiving each other through the
    scaffold's gate. Composes the proven ``BigvilleSimWorld`` drama (the seed
    crystal runs each tick); the townspeople are added as REAL ``Villager`` nodes
    (full agents processed by ``run_rules``), not hollow NPCs."""

    def __init__(self, n, arm="sparse", k0=2.5, occ_density=0.08,
                 place_seed=248000, sigma_scale=1.0, run_drama=True):
        assert arm in ("sparse", "all_pairs")
        assert n >= 2
        self.n = int(n)
        self.arm = arm
        self.k0 = float(k0)
        self.run_drama = bool(run_drama)

        # constant density: lambda = k0 / window  =>  side L = round(sqrt(n/lambda)).
        # floor L so the perception window never tiles the whole torus (proximity
        # genuinely gates even at the smallest N).
        lam = self.k0 / PERC_WINDOW
        L = int(round(math.sqrt(self.n / lam)))
        L = max(L, 2 * PERCEIVE_RANGE + 2)
        self.L = L
        self.density = self.n / float(L * L)

        rng = np.random.default_rng(place_seed)
        # distinct cells for the N inhabitants
        cells = rng.choice(L * L, size=self.n, replace=False)
        self.pos = [(int(c % L), int(c // L)) for c in cells]
        # occluders on a constant fraction of the FREE cells (trees/walls)
        occ_n = int(round(occ_density * L * L))
        taken = set(self.pos)
        free = [c for c in range(L * L) if (c % L, c // L) not in taken]
        occ_cells = rng.choice(len(free), size=min(occ_n, len(free)), replace=False)
        self.occ = set()
        occ_codes = (TREE, WALL)
        self.occ_grid = [[0] * L for _ in range(L)]
        for j, ci in enumerate(occ_cells):
            c = free[ci]
            x, y = c % L, c // L
            self.occ.add((x, y))
            self.occ_grid[y][x] = occ_codes[j % 2]   # a tree or a wall (both occlude)

        # ---- the drama seed crystal (proven scaffold), running each tick ----
        self.sim = BigvilleSimWorld() if self.run_drama else None
        if self.sim is not None:
            self.s = self.sim.s
            self.inner = self.sim.inner
        else:
            self.s = self.inner = None

        # ---- the N townspeople as REAL Villager nodes (full agents) ---------
        self.people = draw_population(self.n, seed=place_seed, sigma_scale=sigma_scale)
        self.town_nodes = []
        if self.s is not None:
            for p in self.people:
                pa = p["params"]
                v = self.s.add_node("Villager", {
                    "name": "town_%d_%s" % (p["index"], p["role"]),
                    "cred_on": float(pa["cred_on"]),
                    "charm_weight": float(pa["charm_weight"]),
                    "claim_weight": float(pa["claim_weight"]),
                    "difficulty_penalty": float(pa["difficulty_penalty"]),
                    "hostile_weight": float(pa["hostile_weight"]),
                    "seen_benevolent": 2.0 * float(pa["charm_weight"]),   # John's charm has worked for years (prior)
                    "seen_hostile": 0.0, "heard_claim": 0.0, "backs_mary": -1.0})
                self.inner.add_edge_unchecked(self.sim.d.village, "has_villager", v)
                self.town_nodes.append(v)
            # sparse relationship/history edges among the townspeople (bounded degree)
            idx2node = {p["index"]: self.town_nodes[i] for i, p in enumerate(self.people)}
            for (a, e, b) in _town.RELATIONSHIPS:
                if a in idx2node and b in idx2node:
                    self.inner.add_edge_unchecked(idx2node[a], e, idx2node[b])

        # the public-square event point on the lattice (townspeople accrue what
        # they PERCEIVE of it -- mechanical, O(N))
        self.square_pt = (L // 2, L // 2)
        self.tick = 0
        self.ops_log = []          # realized interaction-ops per tick
        self.wall_log = []         # per-tick wall-clock (s)
        self.journals = []

    # -------------------- torus perception gate (reuses the scaffold's LOS) ---
    def _cheb_torus(self, o, t):
        dx = abs(o[0] - t[0]); dx = min(dx, self.L - dx)
        dy = abs(o[1] - t[1]); dy = min(dy, self.L - dy)
        return max(dx, dy)

    def _min_image_delta(self, o, t):
        dx = t[0] - o[0]
        if dx > self.L // 2:
            dx -= self.L
        elif dx < -(self.L // 2):
            dx += self.L
        dy = t[1] - o[1]
        if dy > self.L // 2:
            dy -= self.L
        elif dy < -(self.L // 2):
            dy += self.L
        return dx, dy

    def _occluded_torus(self, o, t):
        dx, dy = self._min_image_delta(o, t)
        pts = _line(o[0], o[1], o[0] + dx, o[1] + dy)   # scaffold Bresenham
        for (x, y) in pts[1:-1]:
            if self.occ_grid[y % self.L][x % self.L] in OCCLUDERS:
                return True
        return False

    def _perceives(self, o, t):
        if self._cheb_torus(o, t) > PERCEIVE_RANGE:
            return False
        return not self._occluded_torus(o, t)

    # -------------------- the realized-interaction census --------------------
    def census(self):
        """Count realized interaction-ops for this tick's placement. ``sparse``
        applies the proximity/LOS gate; ``all_pairs`` removes it (every ordered
        pair) -- the deliberate quadratic control. Pure counting; no decision."""
        n = self.n
        if self.arm == "all_pairs":
            return n * (n - 1)
        # sparse: proximity-gated. A spatial bucket keeps the CANDIDATE set local
        # so the COUNTING itself is not an accidental all-pairs sweep -- we only
        # ever test near cells. (The realized COUNT is gate-independent of how we
        # find candidates; bucketing just proves the instrument is honest.)
        L = self.L
        R = PERCEIVE_RANGE
        buckets = {}
        for i, p in enumerate(self.pos):
            buckets.setdefault(p, []).append(i)
        ops = 0
        for i, o in enumerate(self.pos):
            ox, oy = o
            for ddx in range(-R, R + 1):
                for ddy in range(-R, R + 1):
                    cell = ((ox + ddx) % L, (oy + ddy) % L)
                    for j in buckets.get(cell, ()):
                        if j == i:
                            continue
                        if self._perceives(o, self.pos[j]):
                            ops += 1
        return ops

    # -------------------- the gated sim step (drama + census + journals) ------
    def step(self):
        t0 = time.perf_counter()
        self.tick += 1
        # (1) the seed-crystal drama loop (John decides, Mary infers, sim cast +
        #     townspeople back, core journals, reporter->newspaper) -- unchanged.
        stated = held = 0
        if self.sim is not None:
            snap = self.sim.step()
            jst = snap["inhabitants"][0]["state"]
            stated = int(jst.get("stated_benevolent", 0))
            held = int(jst.get("held_hostile", 0))
            # (2) townspeople accrue what they PERCEIVE of the public square
            #     event (mechanical, O(N)) -> they become full participants.
            for i, v in enumerate(self.town_nodes):
                a = self.s.node(v)["attrs"]
                if self._perceives(self.pos[i], self.square_pt):
                    self.s.set_attr(v, "seen_benevolent", a["seen_benevolent"] + stated)
                    self.s.set_attr(v, "seen_hostile", a["seen_hostile"] + held)
            # (3) observers decide, in-graph (townspeople back via bd_villager_backs).
            self.inner.run_rules()
        # (4) THE HEADLINE MEASUREMENT: realized interaction-ops this tick.
        ops = self.census()
        # (5) nightly journals for every townsperson (three glass-box layers) --
        #     mechanical, O(N); makes the journal layer scale with the population.
        if self.s is not None:
            self._town_journals()
        dt = time.perf_counter() - t0
        self.ops_log.append(ops)
        self.wall_log.append(dt)
        return ops

    def _town_journals(self):
        for i, v in enumerate(self.town_nodes):
            a = self.s.node(v)["attrs"]
            backs_mary = int(max(0, a.get("backs_mary", 0))) == 1
            j = self.s.add_node("JournalEntry", {
                "by": self.people[i]["name"], "tick": float(self.tick), "private": 1.0,
                "held": ("The mayor's kindness has a cold underside." if a.get("seen_hostile", 0) > 0
                         else "The mayor has been good to this town."),
                "journal": ("The Bugle and the pastor have me uneasy about the mayor."
                            if backs_mary else "I still trust the mayor; talk is cheap."),
                "face": ("I back the pastor." if backs_mary else "I back the mayor."),
                "self_deception": 0.0})
            self.inner.add_edge_unchecked(v, "wrote_journal", j)
            self.journals.append(j)

    def run(self, T=12):
        for _ in range(T):
            self.step()
        return self.ops_log

    def mean_ops(self):
        return float(np.mean(self.ops_log)) if self.ops_log else 0.0

    def mean_wall_ms(self):
        return float(np.mean(self.wall_log) * 1000.0) if self.wall_log else 0.0

    def close(self):
        if self.sim is not None:
            self.sim.close()
