"""memory_faculty_ops — the MEMORY-FACULTY leaf ops the composer chains.

Twin of domains/language_faculty_ops.py, for the MEMORY faculty. The self-build
composer (domains/reflective_faculty.py) authors GRAPH DATA from a grounded concern.
The prior consumption-quality fix had to implement its grounding cache as ADAPTER
LOGIC (consumption_quality.GroundingCache — a hot dict over the cold reference slab)
because "the composer does not yet author a cache-aside Program." This module
EXPOSES the memory faculty as a graph-resident store the composer can serve from,
so the jabberwock authors the CACHE-ASIDE control itself.

THE CLEAN SPLIT (mirrors the nominal / sense leaves):

  Boundary / HELD-FACULTY CALL (Python, allowed): external I/O + the raw store
    get/put. The UNDERLYING LOOKUP being memoized (a sense/POS consult that reads
    WordNet / the reference slab) is external lexical I/O. The RAW STORE PUT
    (add_node CacheEntry — write a computed value into the hot tier) is a
    side-effecting store write, mechanical adapter I/O. No Term performs either.

  Store (graph-resident, THE MEMORY FACULTY): a HotStore node whose `has_entry`
    CacheEntry{ckey, cval} neighbours are the hot tier, on a scratch substrate
    with the Rust memory faculty COMPOSED as its bound (`memory_bound` — the same
    node/byte cap the agent uses, so the hot tier stays byte-bounded). The store
    IS graph data, not a Python dict.

  SERVE (the composed Program, authored by the composer): `cache_serve_program`
    — Attr(Pick(Filter(store.has_entry, e, e.ckey == key)), "cval"). Evaluating it
    returns the STORED value for `key` (a cache HIT) or None (a MISS). The
    composer (reflective_faculty._compose_memory_faculty) assembles this and
    installs it as a live Program node; the SERVE-FROM-STORE decision (the
    hit/miss of the cache-aside) is the DECISION the agent authors; the
    underlying compute + the raw put stay held-faculty calls.

Cache-aside control (the harness runs the authored SERVE, the leaves do the I/O):
  on a call for `key`: run the authored SERVE Program -> HIT (return the stored
  value); MISS -> compute via the held leaf + raw-put into the store + return. A
  repeat is a HIT served from the graph store, byte-identical to the uncached
  value, WITHOUT re-running the expensive underlying lookup.

DISCIPLINE (CLAUDE.md): no agent decision lives in Python here. The serve/hit
decision is the Term the evaluator runs; the compute + put are the honest leaf
boundary. The scratch substrate the store lives on is a boundary implementation
detail (same as the sense/nominal scratch), not the locus of the decision.
"""
from __future__ import annotations

import json
from typing import Any, Callable, Optional

# The seed carrying the memory RelationCues + the 'cache' -> memory_faculty
# ComposerCue. Loaded on demand (NOT in the minimal wall fixture) so the wall is
# reproducible; the composer + consumption_quality ensure it before grounding.
MEMORY_FACULTY_CUE_SEED = "memory_faculty_cue"

# The named live Program the composer authors + installs.
CACHE_SERVE_PROGRAM = "cache_serve"

# The hot tier's memory-faculty bound (composed via substrate.memory_bound): the
# same node/byte cap graph_virtual_memory uses for the working set.
_HOT_BUDGET_NODES = 5000
_HOT_BUDGET_BYTES = 67108864
_HOT_WINDOW = 3


# ---------------------------------------------------------------------------
# TERM-JSON helpers — raw-dict Term form, evaluated NATIVELY in Rust.
# ---------------------------------------------------------------------------
def _var(n: str) -> dict:
    return {"type": "Var", "name": n}


def _lit(v: Any) -> dict:
    return {"type": "Lit", "value": v}


def _attr(node: dict, key: str) -> dict:
    return {"type": "Attr", "node": node, "key": key}


def _eq(a: dict, b: dict) -> dict:
    return {"type": "Eq", "a": a, "b": b}


# ---------------------------------------------------------------------------
# THE MEMORY LEAF — the cache-aside SERVE (hit/miss) DECISION as a graph Term.
# ---------------------------------------------------------------------------
def cache_serve_program(store_var: str = "store", key_var: str = "key") -> dict:
    """The composed SERVE Program: return the STORED value for the key bound to
    `key_var`, or None on a miss. Attr(Pick(Filter(store.has_entry, e, e.ckey==key)),
    "cval"). This is the cache-aside HIT decision the composer authors — a HIT serves
    the value from the graph memory store; a MISS (no matching entry) evaluates to
    None, and the harness computes + puts. Pure Term; the DECISION is the Program's."""
    store = _var(store_var)
    matching = {"type": "Filter",
                "source": {"type": "Neighbours", "node": store, "edge_type": "has_entry"},
                "var_name": "e",
                "predicate": _eq(_attr(_var("e"), "ckey"), _var(key_var))}
    return _attr({"type": "Pick", "source": matching}, "cval")


def never_serve_program(store_var: str = "store", key_var: str = "key") -> dict:
    """The KNOWN-FAKE twin the #2 control must REJECT: a NO-STORE cache that NEVER
    serves (always evaluates to None -> every call is a miss). It is byte-correct
    (the harness recomputes every time) but memoizes NOTHING, so it never produces a
    HIT and never saves the underlying lookup — a cache with no store has no teeth."""
    return _lit(None)


# ---------------------------------------------------------------------------
# THE STORE — a graph-resident hot tier bounded by the Rust memory faculty.
# ---------------------------------------------------------------------------
class HotStore:
    """A graph-resident hot tier: a HotStore node whose `has_entry` CacheEntry
    neighbours hold (ckey -> cval) pairs, on a scratch substrate with the Rust
    memory faculty COMPOSED as its bound (`memory_bound`). The DECISION (serve-from-
    store) is the authored Program the harness runs over this store; this class only
    holds the substrate + does the RAW store put (add CacheEntry) — the held leaf."""

    def __init__(self) -> None:
        from substrate_rs import _native
        self.s = _native.Substrate()
        # COMPOSE the memory faculty: bound the hot tier (nodes/bytes/hot-window).
        try:
            self.s.memory_bound(_HOT_BUDGET_NODES, _HOT_BUDGET_BYTES, _HOT_WINDOW)
        except Exception:
            pass
        try:
            self.s.add_production({
                "src": {"type": "HotStore", "var": "a"},
                "edge_type": "has_entry",
                "tgt": {"type": "CacheEntry", "var": "b"},
                "where": None,
                "weight": {"type": "Lit", "value": 1.0},
                "provenance": "memory_faculty_ops",
            })
        except Exception:
            pass
        self.store = self.s.add_node("HotStore", {})
        self._keys: set = set()
        self.hits = 0
        self.misses = 0

    def put(self, key: str, value: Any) -> None:
        """RAW STORE PUT (held leaf): write a computed value into the hot tier as a
        CacheEntry{ckey, cval}. Side-effecting store write — mechanical adapter I/O."""
        if key in self._keys:
            return
        cn = self.s.add_node("CacheEntry", {"ckey": str(key), "cval": json.dumps(value)})
        try:
            self.s.add_edge(self.store, "has_entry", cn, {})
        except Exception:
            try:
                self.s.add_edge_unchecked(self.store, "has_entry", cn)
            except Exception:
                pass
        self._keys.add(key)

    def serve(self, program_term: dict, key: str) -> tuple[bool, Any]:
        """Run the AUTHORED serve `program_term` over the store for `key`. Returns
        (hit, value): hit==True + the parsed stored value on a HIT, (False, None) on
        a MISS. The hit/miss DECISION is the Program's; this reads the result back."""
        raw = self.s.evaluate(program_term, {"store": self.store, "key": str(key)})
        if raw is None:
            return False, None
        try:
            return True, json.loads(raw)
        except Exception:
            return True, raw

    def stats(self) -> dict:
        tot = self.hits + self.misses
        return {"hits": self.hits, "misses": self.misses,
                "hit_rate": round(self.hits / tot, 4) if tot else 0.0,
                "entries": len(self._keys)}


def cached_call(program_term: dict, store: HotStore, key: str,
                compute_leaf: Callable[[str], Any]) -> Any:
    """CACHE-ASIDE, driven by the authored SERVE Program: run the Program to serve
    `key` from the graph store; on a HIT return the stored value (no recompute); on a
    MISS compute via the held `compute_leaf` (external I/O), RAW-PUT it into the store,
    and return. Byte-identical to the uncached value; a repeat is a HIT. The
    hit/miss DECISION is the Program's; the compute + put are the honest leaves."""
    hit, value = store.serve(program_term, key)
    if hit:
        store.hits += 1
        return value
    store.misses += 1
    value = compute_leaf(key)          # HELD LEAF — the underlying lookup (external I/O)
    store.put(key, value)              # HELD LEAF — the raw store put (add CacheEntry)
    return value


__all__ = [
    "MEMORY_FACULTY_CUE_SEED", "CACHE_SERVE_PROGRAM",
    "cache_serve_program", "never_serve_program", "HotStore", "cached_call",
]
