"""Offline verification for the RoutingCortex refactor (NOT a world adapter;
a throwaway harness). Builds:

  (1) a TINY wall map  A-B-[wall]-C-D  → B/A unreachable THROUGH the wall;
  (2) a 2x3 map with one internal wall → routes AROUND;
  (3) a DENSE 40x40 (=1600-cell) map with scattered walls → exercises the
      live-frame O(N²) cost regime,

and reports, for each axis the task asks for:

  COST       — per-routing-call + per-"tick" time BEFORE (standalone
               passable_distances) vs AFTER (RoutingCortex cache) on the dense
               map; the cache must turn full-map recompute into ~0 on an
               unchanged map.
  PERCEPTION — op_mean_cost("routing") NON-ZERO; compute_pressure() non-None.
  STIMULUS   — a too-slow / over-budget stimulus EXISTS when cost is high
               (present after, absent before).
  CORRECTNESS— the tiny wall test + 2x3 route-around hold under the cortex.
"""
from __future__ import annotations

import sys
import time

sys.path.insert(0, ".")
sys.path.insert(0, "runners/dsl/python")

from substrate import (                                   # noqa: E402
    ConsistencyChecker, Grammar, Substrate, TypedGraph,
)
from domains.curious_agent import CuriousAgent            # noqa: E402
from domains.routing_cortex import ROUTING_OP             # noqa: E402


# ---------------------------------------------------------------------------
# World builders. A wall = a Boundary node bounded_by the cell, passable=False,
# with a ``blocks`` edge to the neighbour it walls off (the gamma contract
# passable_neighbours_term reads). The mirror passable side is plain adjacency.
# ---------------------------------------------------------------------------
def _grid_substrate(cells, adj_edges):
    """cells: [id]; adj_edges: [(a,b)] undirected adjacency. Walls are injected
    into the MIND graph after observe (that's where routing reads)."""
    g = TypedGraph()
    body = g._insert_node("Body", {})
    nids = {n: g._insert_node("SpatialLocation", {"id": n}) for n in cells}
    for a, b in adj_edges:
        g._insert_edge(nids[a], "adjacent_to", nids[b])
        g._insert_edge(nids[b], "adjacent_to", nids[a])
    g._insert_edge(body, "at_location", nids[cells[0]])
    return Substrate(graph=g, checker=ConsistencyChecker(Grammar([])))


def _agent_on(cells, adj, walls, start):
    """Build the agent, observe the adjacency map, then inject the learned
    walls DIRECTLY into the mind graph — a wall = an impassable Boundary
    bounded_by the cell that ``blocks`` the neighbour it walls off, exactly the
    gamma contract ``passable_neighbours_term`` reads (the navigate agent learns
    these by bumping; here we plant the learned state for an offline check)."""
    a = CuriousAgent()
    sub = _grid_substrate(cells, adj)
    a.observe(sub)
    wi = {c: a._world_instance_nodes[("SpatialLocation", c)] for c in cells}
    mg = a.mind_graph
    for x, y in walls:
        bx = mg._insert_node("Boundary", {"passable": False,
                                           "world_type": "Boundary"})
        mg._insert_edge(wi[x], "bounded_by", bx)
        mg._insert_edge(bx, "blocks", wi[y])
        by = mg._insert_node("Boundary", {"passable": False,
                                           "world_type": "Boundary"})
        mg._insert_edge(wi[y], "bounded_by", by)
        mg._insert_edge(by, "blocks", wi[x])
    return a, wi


# ---------------------------------------------------------------------------
print("=" * 72)
print("CORRECTNESS — tiny wall map  A-B-[wall]-C-D")
print("=" * 72)
# A-B adjacent, B-C adjacent BUT WALLED, C-D adjacent. From A: A,B reachable;
# C,D unreachable THROUGH the wall.
a, wi = _agent_on(["A", "B", "C", "D"],
                  [("A", "B"), ("B", "C"), ("C", "D")],
                  walls=[("B", "C")], start="A")
dists_from_d = a._bfs_distances_to_goal(wi["D"], horizon=10)
print(f"  distances to goal D: "
      f"{ {c: dists_from_d.get(wi[c]) for c in ['A','B','C','D']} }")
reach_from_A = wi["A"] in dists_from_d  # A can reach D?
print(f"  A reachable-to-D through wall? {reach_from_A}  (expect False)")
print(f"  C->D (no wall between them)?   {wi['C'] in dists_from_d}  (expect True)")
assert wi["D"] in dists_from_d and dists_from_d[wi["D"]] == 0
assert wi["C"] in dists_from_d and dists_from_d[wi["C"]] == 1
assert wi["A"] not in dists_from_d, "A must be unreachable through the wall"
assert wi["B"] not in dists_from_d, "B must be unreachable through the wall"
print("  PASS: wall blocks A/B from D; C->D open.")

print()
print("=" * 72)
print("CORRECTNESS — 2x3 grid, one internal wall, routes AROUND")
print("=" * 72)
# Grid:  P0 P1 P2
#        P3 P4 P5
# adjacency: rows + columns. Wall between P1 and P4 (vertical block in the
# middle column). Route from P0 to P5 must go AROUND via P2 (not straight down
# through the walled P1-P4).
cells = ["P0", "P1", "P2", "P3", "P4", "P5"]
adj = [("P0", "P1"), ("P1", "P2"),
       ("P3", "P4"), ("P4", "P5"),
       ("P0", "P3"), ("P1", "P4"), ("P2", "P5")]
a2, wi2 = _agent_on(cells, adj, walls=[("P1", "P4")], start="P0")
d_to_P5 = a2._bfs_distances_to_goal(wi2["P5"], horizon=20)
named = {c: d_to_P5.get(wi2[c]) for c in cells}
print(f"  distances to P5: {named}")
# Straight path P0-P1-P4-P5 = 3 is BLOCKED at P1-P4. Route P0-P3-P4-P5 = 3,
# or P0-P1-P2-P5 = 3. P4's only open neighbours are P3 and P5, so P4 dist = 1.
# The KEY assertion: P1 cannot use P4 (walled) → P1 reaches P5 via P2 (dist 2),
# and P0's shortest is 3, NOT through the P1-P4 wall.
path = a2._compute_path_to(wi2["P0"], wi2["P5"], 20)
named_path = [next(c for c in cells if wi2[c] == p) for p in path]
print(f"  path P0->P5: {named_path}")
assert wi2["P5"] in d_to_P5 and d_to_P5[wi2["P5"]] == 0
assert wi2["P0"] in d_to_P5, "P0 must still reach P5 (around the wall)"
# the path must NOT contain the walled hop P1->P4
hops = list(zip(["P0"] + named_path, named_path))
assert ("P1", "P4") not in hops and ("P4", "P1") not in hops, \
    "path must route AROUND the P1-P4 wall"
print("  PASS: routes around the wall, never crosses P1-P4.")


# ---------------------------------------------------------------------------
print()
print("=" * 72)
print("DENSE MAP — 40x40 = 1600 cells, scattered walls (live-frame regime)")
print("=" * 72)
N = 40
dense_cells = [f"c{r}_{col}" for r in range(N) for col in range(N)]
dense_adj = []
for r in range(N):
    for col in range(N):
        if col + 1 < N:
            dense_adj.append((f"c{r}_{col}", f"c{r}_{col+1}"))
        if r + 1 < N:
            dense_adj.append((f"c{r}_{col}", f"c{r+1}_{col}"))
# scatter some walls (every 7th interior horizontal edge) so passability matters
dense_walls = []
for r in range(1, N - 1, 7):
    for col in range(0, N - 1, 3):
        dense_walls.append((f"c{r}_{col}", f"c{r+1}_{col}"))
print(f"  cells={len(dense_cells)}  adj_edges={len(dense_adj)}  "
      f"walls={len(dense_walls)}")

a3, wi3 = _agent_on(dense_cells, dense_adj, dense_walls, start="c0_0")
goal = wi3[f"c{N-1}_{N-1}"]
horizon = len(dense_cells)

# --- BEFORE: the standalone driver (no cache, no instrumentation) ---
from domains.spatial_routing import passable_distances           # noqa: E402
relax = a3._passable_distance_relax_term()
t0 = time.perf_counter()
_ = passable_distances(a3.mind_graph, a3._spatial_cells(), goal, horizon, relax)
before_ms = (time.perf_counter() - t0) * 1000.0
print(f"  BEFORE (standalone passable_distances): {before_ms:9.1f} ms / call")

# --- AFTER: the RoutingCortex. First call = recompute (cache miss); second =
# cache hit on the unchanged map. ---
cx = a3._routing()
t0 = time.perf_counter()
d1 = a3._bfs_distances_to_goal(goal, horizon)
after_miss_ms = (time.perf_counter() - t0) * 1000.0
t0 = time.perf_counter()
d2 = a3._bfs_distances_to_goal(goal, horizon)      # SAME map + goal → cache hit
after_hit_ms = (time.perf_counter() - t0) * 1000.0
print(f"  AFTER  (cortex, cache MISS = first plan):  {after_miss_ms:9.1f} ms")
print(f"  AFTER  (cortex, cache HIT  = unchanged):   {after_hit_ms:9.4f} ms")
print(f"  cortex recomputes={cx.n_recomputes}  cache_hits={cx.n_cache_hits}")
assert d1 == d2, "cache hit must return the identical field"
speedup = before_ms / max(after_hit_ms, 1e-6)
print(f"  CACHE WIN: unchanged-map recompute avoided — "
      f"{speedup:,.0f}x cheaper on the hit.")

# many cache hits = the per-tick cost on a STABLE map collapses to ~0
t0 = time.perf_counter()
for _ in range(50):
    a3._bfs_distances_to_goal(goal, horizon)
fifty_ms = (time.perf_counter() - t0) * 1000.0
print(f"  50 plan recomputes on a STABLE map: {fifty_ms:.3f} ms total "
      f"(~{fifty_ms/50:.4f} ms each) — was ~{before_ms:.0f} ms EACH before.")

# --- cache INVALIDATION: flip a boundary's passability → next call recomputes
some_boundary = next(iter(a3.mind_graph.nodes("Boundary"))).id
a3.mind_graph.node(some_boundary).attrs["passable"] = True
n_before = cx.n_recomputes
_ = a3._bfs_distances_to_goal(goal, horizon)
print(f"  after a passability flip: recomputes "
      f"{n_before} -> {cx.n_recomputes} (cache correctly invalidated: "
      f"{cx.n_recomputes > n_before})")


# ---------------------------------------------------------------------------
print()
print("=" * 72)
print("PERCEPTION — the agent can now SEE the routing spend")
print("=" * 72)
op_mean = a3.runtime_capabilities()["op_mean_cost"]({"of": ROUTING_OP})
op_count = a3.op_stats(ROUTING_OP)["count"]
print(f"  op_mean_cost('routing') = {op_mean:.4f} ms  (count={op_count})")
print(f"  op_mean_cost('passable_distances') = "
      f"{a3.runtime_capabilities()['op_mean_cost']({'of':'passable_distances'}):.4f} ms")
assert op_mean > 0.0, "routing op cost must be NON-ZERO (agent perceives it)"
root_attrs = a3.mind_graph.node(a3.agent_root).attrs
print(f"  agent_root op_routing_mean_ms = "
      f"{root_attrs.get('op_routing_mean_ms')}")
print(f"  agent_root total_tick_cost_ms = "
      f"{root_attrs.get('total_tick_cost_ms'):.1f}  "
      f"(accumulated via the inherited measure_tick)")
assert root_attrs.get("op_routing_mean_ms", 0) > 0

cp_before_limit = a3.compute_pressure()
print(f"  compute_pressure() before a limit is set: {cp_before_limit} "
      f"(None until a budget engages)")


# ---------------------------------------------------------------------------
print()
print("=" * 72)
print("STIMULUS / REFLEX — a too-slow / over-budget stimulus now EXISTS")
print("=" * 72)
# BEFORE engaging the inherited budget: no compute ceiling → no pressure → no
# stimulus possible. (compute_pressure is None.)
print(f"  STIMULUS ABSENT (no budget): compute_pressure() = "
      f"{a3.compute_pressure()}  -> over_budget stimulus cannot fire.")

# Engage the INHERITED budget (set_compute_limit on agent_root). With routing
# cost already accumulated in total_tick_cost_ms, set a tight ceiling so the
# spend exceeds it — compute_pressure goes > 1.0 and a too-slow stimulus EXISTS.
spent = root_attrs.get("total_tick_cost_ms", 0.0)
a3.set_compute_limit(spent * 0.5)     # tight budget — already over it
cp = a3.compute_pressure()
print(f"  STIMULUS PRESENT (budget engaged): compute_pressure() = {cp:.3f}")
assert cp is not None and cp > 1.0, \
    "with routing cost counted + a tight budget, pressure must exceed 1.0"
over_budget = (cp is not None and cp > 1.0)
# the per-op cost is also above any sane per-call budget on the dense map
slow_op = op_mean > 1.0   # >1ms per routing call = slow for a per-tick loop
print(f"  over_budget stimulus present:  {over_budget}")
print(f"  slow-routing-op stimulus present (mean>1ms): {slow_op}  "
      f"(op_mean={op_mean:.3f} ms)")
assert over_budget, "the over-budget stimulus must EXIST when cost is high"
print("  PASS: the agent can perceive routing cost AND a too-slow/over-budget")
print("        stimulus now EXISTS (the agent's own reflex/selector decides).")

print()
print("=" * 72)
print("ALL VERIFICATION AXES GREEN.")
print("=" * 72)
