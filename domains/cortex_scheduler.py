"""CortexScheduler — independent-clock dispatch for cognitive cortices.

The master clock provides absolute time. Cortex clocks are
DECOUPLED from it: each cortex has its own intrinsic period
(`tick_period_ms`) and pulses on its own rhythm, like brain
regions oscillating at theta/alpha/beta/gamma frequencies.

The scheduler:
  - Holds a registry of installed cortices + each one's next-fire
    time in absolute ms.
  - On `advance(now_ms)`, dispatches every cortex whose next-fire
    time has elapsed, then reschedules it for now + its own
    period.
  - Accepts external `wake(cortex)` calls — interrupt-style. The
    cortex's reflex loop fires immediately; its scheduled tick
    cadence is unaffected.

No master walk-all-cortices loop. No global synchronisation. Each
cortex is sovereign over WHEN it processes; the scheduler is just
a clock-time dispatcher.

Wakes come from:
  - World adapters (audio arrived → wake SpeechCortex)
  - Cross-cortex signalling (a graph mutation in one cortex
    surfaces a count attr the other reads — currently driven by
    the world adapter as a thin shim until graph-mutation hooks
    are exposed at the substrate level)
  - The cortex's own reflex effects (a Reflex in cortex A can
    wake cortex B)
"""
from __future__ import annotations


class CortexScheduler:
    """Per-cortex tick dispatch with independent clocks PLUS
    event-driven wake routing.

    Each cortex declares its `attr_interests()` and
    `edge_interests()` — attr keys + edge types whose mutation
    can produce work for it. The scheduler registers callbacks
    on the substrate's `attr_set` / `edge_inserted` /
    `edge_deleted` hooks; when a relevant mutation fires, the
    matching cortices are marked dirty. `advance()` then routes
    wakes only to dirty cortices (verified by has_pending_work).

    Same shape as synaptic propagation: a downstream neuron
    fires when an upstream signal arrives, not on a polling
    schedule. The intrinsic clock still produces background
    ticks; the hooks produce event-driven interrupts.
    """

    def __init__(self):
        self._cortices: list[dict] = []
        self._attr_interests: dict[str, set] = {}
        self._edge_interests: dict[str, set] = {}
        self._node_interests: dict[str, set] = {}
        self._dirty: set = set()
        self._hooks_installed_on = None

    def register(self, cortex, start_offset_ms: int = 0) -> None:
        """Register a cortex. Installs hook callbacks on the
        substrate the first time around so subsequent attr/edge
        mutations route wakes automatically."""
        if not getattr(cortex, "_installed", False):
            raise RuntimeError("cortex must be installed first")
        self._cortices.append({
            "cortex": cortex,
            "next_fire": int(start_offset_ms),
            "last_tick": -1,
            "audit": [],
        })
        # Build the interest maps.
        cid = id(cortex)
        if hasattr(cortex, "attr_interests"):
            for key in cortex.attr_interests():
                self._attr_interests.setdefault(key, set()).add(cid)
        if hasattr(cortex, "edge_interests"):
            for et in cortex.edge_interests():
                self._edge_interests.setdefault(et, set()).add(cid)
        if hasattr(cortex, "node_interests"):
            for nt in cortex.node_interests():
                self._node_interests.setdefault(nt, set()).add(cid)
        # Install the underlying substrate hooks once. We need
        # access to the underlying Rust handle: `substrate._inner`
        # exposes register_hook.
        sub = cortex.s
        inner = getattr(sub, "_inner", sub)
        if self._hooks_installed_on is not inner:
            try:
                inner.register_hook("attr_set", self._on_attr_set)
                inner.register_hook("edge_inserted",
                                       self._on_edge_inserted)
                inner.register_hook("edge_deleted",
                                       self._on_edge_deleted)
                inner.register_hook("node_inserted",
                                       self._on_node_inserted)
                self._hooks_installed_on = inner
            except Exception:
                # Hook surface absent or already-registered failure;
                # fall back to polling (still correct, just slower).
                pass

    def _on_node_inserted(self, nid, type_str):
        interested = self._node_interests.get(str(type_str))
        if interested:
            self._dirty.update(interested)

    def _on_attr_set(self, nid, key, old_value, new_value):
        interested = self._attr_interests.get(str(key))
        if interested:
            self._dirty.update(interested)

    def _on_edge_inserted(self, src, edge_type, tgt):
        interested = self._edge_interests.get(str(edge_type))
        if interested:
            self._dirty.update(interested)

    def _on_edge_deleted(self, src, edge_type, tgt):
        interested = self._edge_interests.get(str(edge_type))
        if interested:
            self._dirty.update(interested)

    def advance(self, now_ms: int,
                  vote_counts: dict | None = None) -> dict:
        """Advance the master clock to `now_ms`. Two dispatch
        paths, both respecting cortex sovereignty:

        1. **Scheduled tick** — any cortex whose next-fire time
           has elapsed dispatches once and is rescheduled at
           now + its own period.
        2. **Pending-work wake** — any cortex whose
           `has_pending_work()` returns True is dispatched
           immediately (interrupt) without shifting its
           scheduled cadence. Biology: sensory drive overrides
           background oscillation; the oscillator continues.

        Both paths route through the cortex's own .tick()/.wake()
        API. The scheduler is just a clock-time + interrupt
        router; the cortex decides what to do with the dispatch.

        Returns {cortex_key -> {tick: n, wake: n, fires: n}}.
        """
        fires: dict = {}
        for entry in self._cortices:
            cortex = entry["cortex"]
            cid = id(cortex)
            name = getattr(cortex, "lexicon_name", "")
            key = f"{type(cortex).__name__}[{name}]" \
                      if name else type(cortex).__name__

            ran_tick = False
            ran_wake = False
            audit: list = []

            # Scheduled tick path: cortex's own period elapsed.
            if now_ms >= entry["next_fire"]:
                audit = cortex.tick(vote_counts=vote_counts)
                entry["last_tick"] = now_ms
                entry["next_fire"] = (now_ms
                                          + cortex.tick_period_ms)
                entry["audit"].append((now_ms, audit))
                ran_tick = True
                # The cortex just processed — clear its dirty flag.
                # Anything that fires DURING the tick (cortex's own
                # graph mutations) will re-set it.
                self._dirty.discard(cid)
            # Event-driven wake path: a hook marked this cortex
            # dirty since the last dispatch. Verify it actually has
            # work via has_pending_work (the dirty flag is the
            # cheap signal; pending_work is the truth check).
            elif cid in self._dirty:
                if (hasattr(cortex, "has_pending_work")
                        and cortex.has_pending_work(
                            vote_counts=vote_counts)):
                    audit = cortex.wake(vote_counts=vote_counts)
                    entry["audit"].append((-1, audit))
                    ran_wake = True
                self._dirty.discard(cid)
            # Last fallback: polling — used when hooks aren't
            # installed (e.g. older substrate without the hook
            # surface). Costs a graph walk per cortex per advance.
            elif (self._hooks_installed_on is None
                       and hasattr(cortex, "has_pending_work")
                       and cortex.has_pending_work(
                           vote_counts=vote_counts)):
                audit = cortex.wake(vote_counts=vote_counts)
                entry["audit"].append((-1, audit))
                ran_wake = True

            if ran_tick or ran_wake:
                fires.setdefault(key, {"tick": 0, "wake": 0,
                                            "fires": 0})
                if ran_tick:
                    fires[key]["tick"] += 1
                if ran_wake:
                    fires[key]["wake"] += 1
                fires[key]["fires"] += len(audit)
        return fires

    def wake(self, cortex,
                vote_counts: dict | None = None) -> list:
        """Interrupt fire: the named cortex runs its reflex loop
        immediately, bypassing the schedule. Used when something
        upstream requires the cortex's attention before its next
        intrinsic pulse — sensory drive, cross-cortex signal."""
        for entry in self._cortices:
            if entry["cortex"] is cortex:
                audit = cortex.wake(vote_counts=vote_counts)
                # Don't shift the schedule; intrinsic rhythm
                # continues. (Biology: an interrupt doesn't reset
                # the underlying oscillator.)
                entry["audit"].append((-1, audit))
                return audit
        raise ValueError("cortex not registered with scheduler")

    def registered(self) -> list:
        """All registered cortices in registration order."""
        return [e["cortex"] for e in self._cortices]

    def status(self) -> list[dict]:
        """Per-cortex status snapshot. Useful for debugging the
        dispatch cadence."""
        return [{
            "cortex": getattr(e["cortex"], "cortex_nid", "?"),
            "type": type(e["cortex"]).__name__,
            "period_ms": e["cortex"].tick_period_ms,
            "next_fire_ms": e["next_fire"],
            "last_tick_ms": e["last_tick"],
            "n_fires_total": sum(len(a) for _, a in e["audit"]),
        } for e in self._cortices]


__all__ = ["CortexScheduler"]
