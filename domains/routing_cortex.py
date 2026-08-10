"""RoutingCortex — the agent's PASSABILITY-AWARE distance routing, run AS A
CORTEX so it INHERITS the cognitive-cortex machinery instead of re-implementing
it.

WHY THIS EXISTS. ``domains/spatial_routing.py`` gives the graph-resident
distance recurrence (the fixed-point Term-tree the Rust DSL evaluates). But the
*driver* of that recurrence was a bespoke standalone reader in the agent
(``_bfs_distances_to_goal`` → ``spatial_routing.passable_distances``):

  - it recomputed the WHOLE O(N²) distance field from scratch on EVERY plan
    recompute (no cache), so a dense live frame cost ~10–20 s/tick; and
  - the agent was BLIND to that spend — the cost never flowed through the
    substrate-awareness instrumentation (``measure_tick`` / ``_record_op`` /
    ``compute_pressure``), so ``op_mean_cost(passable_distances)`` read 0 and the
    "too slow / over budget" stimulus had no fuel.

THE MOVE (the user's call): "What it should be is a routingCortex which means it
gets all the machinery of the cortex free." A cortex in this substrate is a
duck-typed module the ``CortexScheduler`` dispatches (the same interface
``MotorCortex`` / ``IntentCortex`` / ``SpeechCortex`` satisfy):

    install() · _installed · tick_period_ms · tick() · wake() ·
    has_pending_work() · attr_interests() · edge_interests() · node_interests()

Registering with the scheduler is what gives a cortex its machinery FOR FREE:

  * COST INSTRUMENTATION + COMPUTE BUDGET — the cortex runs its routing work
    THROUGH the agent's ``measure_tick`` (so the cost accumulates into
    ``total_tick_cost_ms`` → ``compute_pressure``) and records an
    ``op`` sample via ``_record_op`` (so ``op_mean_cost("passable_distances")``
    becomes NON-ZERO and visible to the agent's own assessor). We INHERIT this
    surface; we do not hand-roll a profiler.

  * STAMP / THROTTLE / CONSOLIDATION — the cortex's distance field is CACHED and
    recomputed only when its INPUTS change (the goal cell, the passability /
    Boundary set, or the map topology). A stable map + same goal → cache hit,
    ~0 cost. This is exactly the "stamp-throttle so the cortex doesn't fully
    recompute every tick" behaviour the streaming cortexes get from the master
    clock; here the throttle key is an INPUT FINGERPRINT (the Python ``Substrate``
    shim the agent runs on does not expose the Rust ``register_hook`` surface the
    ``CortexScheduler`` uses for event-driven dirty-tracking, so the cortex
    derives its own cheap O(N+B) fingerprint over {goal, topology, passability}
    and only re-runs the O(N²) fixed point when it moves). The O(N²)-every-tick
    collapses to O(N²)-only-when-the-map-changes.

  * has_pending_work / *_interests — the scheduler can wake the cortex on
    SpatialLocation inserts, ``passable`` attr flips, and ``blocks`` /
    ``bounded_by`` / adjacency edge changes (when hooks ARE available), and
    poll it otherwise. Either way the SAME fingerprint decides recompute.

WHAT STAYS THE SAME. The passability-correctness is unchanged — routing still
runs over PASSABLE adjacency only (a wall is not a neighbour), because the cortex
fires the very same ``spatial_routing.passable_distances`` engine / Term-tree.
The reasoning ("distance = 1 + min over passable neighbours") lives in gamma; the
cortex only schedules + caches + instruments the evaluation.

GENERAL, not ARC-keyed: any SpatialLocation + Boundary domain (doom / walker /
ARC) routes the same way. The only graph facts read are ``world_type`` ==
"SpatialLocation" cells, ``bounded_by`` boundaries with a ``passable`` attr, and
their ``blocks`` edges — identical to ``spatial_routing``.
"""
from __future__ import annotations

import time

# Cortex tick rhythm. Routing perception is a planning-tier process — between
# the speech (2000 ms) and motor (200 ms) cortices. The fingerprint-gated cache
# means an actual O(N²) recompute happens only on map/goal change, so the period
# is just the background re-check cadence.
ROUTING_TICK_MS = 250

# The op name the routing spend is recorded under. ``op_mean_cost("routing")``
# (and the underlying ``passable_distances``) become NON-ZERO once the cortex has
# ticked, so the agent perceives the spend.
ROUTING_OP = "routing"
ROUTING_ENGINE_OP = "passable_distances"


class RoutingCortex:
    """The passable-distance fixed point, run as a scheduler-dispatched cortex.

    Constructed against the agent (``CuriousAgent``) whose substrate-awareness
    machinery (``measure_tick`` / ``_record_op`` / ``compute_pressure``) it runs
    THROUGH — so routing cost becomes perceivable graph-resident state rather
    than invisible Python time. The agent's planner readers
    (``_bfs_distances_to_goal`` etc.) become thin shims onto this cortex's
    cached, instrumented ``distances_to(goal)``.
    """

    def __init__(self, agent, tick_period_ms: int = ROUTING_TICK_MS):
        self.agent = agent
        # The scheduler reads ``cortex.s`` (and ``cortex.s._inner`` for hooks).
        # The agent's own substrate is the cortex's substrate — routing reads and
        # writes the agent's mind graph, nothing separate.
        self.s = agent.mind_substrate
        self.tick_period_ms = int(tick_period_ms)
        self.cortex_nid = None
        self._installed = False
        self._tick_count = 0
        self._wake_count = 0
        # --- the inherited throttle/consolidation: a fingerprint-gated cache ---
        # ``_cache``: {goal_wi: {cell_wi: dist}} for the CURRENT fingerprint.
        # ``_fingerprint``: cheap O(N+B) signature of {topology, passability}.
        # A change in either the goal or the fingerprint forces a recompute; a
        # repeat is a cache HIT (the cortex's "don't fully recompute" reflex).
        self._cache: dict = {}
        self._fingerprint = None
        # bookkeeping the report reads
        self.n_recomputes = 0          # actual O(N²) fixed-point runs
        self.n_cache_hits = 0          # served from cache, ~0 cost
        self.last_recompute_ms = 0.0

    # ---- install: mint the cortex's graph-resident state node ----
    def install(self) -> "RoutingCortex":
        existing = None
        for n in self.s.nodes("RoutingCortex"):
            existing = n.id
            break
        if existing is None:
            self.cortex_nid = self.s.add_node("RoutingCortex", {
                "tick_count": 0,
                "wake_count": 0,
                "tick_period_ms": int(self.tick_period_ms),
                "n_recomputes": 0,
                "n_cache_hits": 0,
                "origin": "routing_cortex",
            })
        else:
            self.cortex_nid = existing
            stored = self.s.node(existing).attrs.get("tick_period_ms")
            if stored is not None:
                self.tick_period_ms = int(stored)
        self._installed = True
        return self

    # ---- CortexScheduler interest declaration (event-driven wake routing) ----
    def attr_interests(self) -> set:
        # A boundary flipping passable/impassable changes the distance field.
        return {"passable"}

    def edge_interests(self) -> set:
        # Adjacency, walling, and the agent's goal edge all change routing.
        return {"blocks", "bounded_by", "leads_to", "adjacent_to",
                "adjacent_location", "wants"}

    def node_interests(self) -> set:
        # A new cell or boundary changes the map.
        return {"SpatialLocation", "Boundary"}

    def has_pending_work(self, vote_counts=None) -> bool:
        """Pending iff the inputs moved since the last recompute (the same
        fingerprint the cache is keyed on). Cheap O(N+B) check — no routing."""
        if not self._installed:
            return False
        return self._current_fingerprint() != self._fingerprint

    # ---- scheduler dispatch ----
    def tick(self, vote_counts=None) -> list:
        if not self._installed:
            raise RuntimeError("RoutingCortex.install() not called")
        self._tick_count += 1
        self.s.set_attr(self.cortex_nid, "tick_count", int(self._tick_count))
        # Re-validate the cache against current inputs. If the map/goal moved,
        # drop the stale field; the next distances_to() pays the recompute and
        # records the spend. A background tick on a stable map is a pure no-op.
        self._revalidate()
        return [("routing", self._tick_count,
                 {"recomputes": self.n_recomputes,
                  "cache_hits": self.n_cache_hits})]

    def wake(self, vote_counts=None) -> list:
        if not self._installed:
            raise RuntimeError("RoutingCortex.install() not called")
        self._wake_count += 1
        self.s.set_attr(self.cortex_nid, "wake_count", int(self._wake_count))
        self._revalidate()
        return [("routing-wake", self._wake_count)]

    # ---- the inherited throttle: input fingerprint over {topology, passability} ----
    def _current_fingerprint(self):
        """A cheap O(N + B) signature of the routing inputs: the cell set, the
        adjacency/wall edge count, and the (boundary, passable) + blocks state.
        Changing any of these changes the distance field; nothing else does. Far
        cheaper than the O(N² × sweeps) fixed point, so the gate is ~free."""
        g = self.agent.mind_graph
        cells = self.agent._spatial_cells()
        n_cells = len(cells)
        # Passability state: only boundaries carry it, and there are O(N) of them
        # (a constant number of sides per cell), so this stays linear. Hash the
        # multiset of (boundary_id, passable_flag) + the count of blocks edges.
        pass_state = 0
        n_blocks = 0
        for node in g.nodes("Boundary"):
            nid = node.id
            flag = 1 if node.attrs.get("passable") else 0
            pass_state ^= hash((nid, flag))
            for _ in g.out_edges(nid, "blocks"):
                n_blocks += 1
        # Boundaries that became WorldInstance nodes (world_type=='Boundary')
        # carry the learned passable attr too — fold those in (general path).
        for (wt, _wid), nid in self.agent._world_instance_nodes.items():
            if wt != "Boundary":
                continue
            flag = 1 if g.node(nid).attrs.get("passable") else 0
            pass_state ^= hash((nid, flag))
            for _ in g.out_edges(nid, "blocks"):
                n_blocks += 1
        # Topology: total edge count over the graph is a cheap proxy for "did the
        # adjacency change" (a new/removed edge moves it); combined with the cell
        # set size it catches map mutations.
        try:
            edge_total = g.edge_count()
        except Exception:
            edge_total = 0
        return (n_cells, n_blocks, edge_total, pass_state)

    def _revalidate(self) -> None:
        """If the inputs moved, invalidate the cache (next read recomputes)."""
        fp = self._current_fingerprint()
        if fp != self._fingerprint:
            self._fingerprint = fp
            self._cache = {}

    # ---- the work, run THROUGH the inherited instrumentation ----
    def distances_to(self, goal_wi, horizon: int) -> dict:
        """``{cell_wi: distance_to_goal}`` over PASSABLE adjacency only.

        Cache HIT (inputs unchanged, goal seen): served in ~0 time — records a
        near-zero op sample so the agent sees the cortex is cheap when the map is
        stable. Cache MISS: runs the graph-resident ``passable_distances`` fixed
        point THROUGH the agent's ``measure_tick`` (cost → compute_pressure) and
        records the real ``op`` sample (cost → op_mean_cost) — the spend the
        standalone router hid.
        """
        agent = self.agent
        cells = agent._spatial_cells()
        if not cells:
            return {}
        # Re-validate against current inputs (drops a stale cache).
        self._revalidate()
        cached = self._cache.get(goal_wi)
        if cached is not None:
            # CACHE HIT — the throttle paying off. Record a ~0 op sample so the
            # agent's assessor sees the cortex is cheap on a stable map.
            self.n_cache_hits += 1
            self.s.set_attr(self.cortex_nid, "n_cache_hits", int(self.n_cache_hits))
            t0 = time.perf_counter()
            result = cached
            elapsed = (time.perf_counter() - t0) * 1000.0
            agent._record_op(ROUTING_OP, elapsed)
            return result

        # CACHE MISS — recompute, instrumented. measure_tick times the work and
        # accumulates total_tick_cost_ms (→ compute_pressure); _record_op records
        # the per-call op cost (→ op_mean_cost). Both inherited from the agent.
        from domains.spatial_routing import passable_distances
        relax = agent._passable_distance_relax_term()

        holder = {}

        def work(_a):
            holder["d"] = passable_distances(
                agent.mind_graph, cells, goal_wi, horizon, relax)

        t0 = time.perf_counter()
        agent.measure_tick(work)
        elapsed = (time.perf_counter() - t0) * 1000.0
        agent._record_op(ROUTING_OP, elapsed)
        agent._record_op(ROUTING_ENGINE_OP, elapsed)

        dists = holder.get("d", {})
        self._cache[goal_wi] = dists
        self.n_recomputes += 1
        self.last_recompute_ms = elapsed
        self.s.set_attr(self.cortex_nid, "n_recomputes", int(self.n_recomputes))
        return dists


__all__ = ["RoutingCortex", "ROUTING_OP", "ROUTING_ENGINE_OP",
           "ROUTING_TICK_MS"]
