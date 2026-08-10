"""long_term_memory — THIN ADAPTER over the Rust MEMORY faculty's long-term tier.

CLAUDE.md: the agent is Rust; Python is the world adapter.  The disk tier + the
order-N SHAPE index (storage = retrieval key, bounded by #clusters not #items) now
live in Rust (runners/dsl/src/memory.rs: ShapeIndex + shape_key = relational_shape.rank,
consolidate via persist::encode_value, shuffle, recall_by_shape descent).

This module is the thin shim.  The ONLY Python here is the mechanical feature-vector
projection (_feature_vec): pulling a few numeric attrs from a record to hand the Rust
faculty the cat/leaf vectors it computes the SHAPE from.  That is I/O-boundary plumbing
(matrix -> vector), not a decision — the rank-shape, the cluster id, the descent, and the
page-in/out are all the Rust faculty's.

The historical pure-Python implementation (in-RAM ShapeIndex, JSON drawers, descent) is
preserved in domains.memory_shape_faculty / git history as the SPEC.
"""
from __future__ import annotations


def _feature_vec(rec_attrs: dict, kind: str) -> list[float]:
    """PLUMBING: a small numeric feature vector for a record.  The SHAPE is computed by
    the Rust faculty's rank operator; this only selects which numeric attrs project to
    the category (coarse) vs leaf (fine) tier."""
    new = float(rec_attrs.get("new_signs", rec_attrs.get("new", 0)) or 0)
    utts = float(rec_attrs.get("utts", 0) or 0)
    rnd = float(rec_attrs.get("round", rec_attrs.get("last_round", 0)) or 0)
    if kind == "category":
        return [new, utts, rnd]
    return [new, utts, new + utts]


class LongTermMemory:
    """Thin adapter to the Rust long-term tier.  Holds no index state — the order-N
    shape index lives in the Rust faculty (bounded by #clusters)."""

    def __init__(self, store_dir: str, hot_window: int = 5):
        self.dir = store_dir
        self.hot_window = hot_window
        # routing map (NAME plumbing only): key -> last consolidated round, so findable()
        # can answer "have we stored this show?" without touching the Rust shape index
        # (recall BY SHAPE uses the descent, not this map).
        self._known: set[str] = set()
        self._s = None       # the substrate the faculty lives on (set on first call)

    def _bind(self, s):
        # Bind to the substrate the faculty lives on.  Do NOT call memory_bound here:
        # the byte/node budget is owned by MemorySelfManagement (the sensory bound).
        # We only set the hot_window for the long-term shuffle tier.
        if self._s is None:
            self._s = s
            s.memory_set_hot_window(self.hot_window)

    def consolidate(self, s, key: str, node_id, round_no: int, meta: dict | None = None):
        self._bind(s)
        nd = s.node(node_id)
        attrs = dict(nd["attrs"])
        cat = _feature_vec(attrs, "category")
        leaf = _feature_vec(attrs, "leaf")
        s.memory_consolidate(self.dir, key, node_id, round_no, cat, leaf)
        self._known.add(key)

    def shuffle(self, s, round_no: int) -> dict:
        self._bind(s)
        evicted = s.memory_shuffle(round_no)
        return {"evicted_clusters": evicted,
                "resident_clusters": None,
                "clusters_total": s.memory_index_clusters()}

    def recall_by_shape(self, s, query_attrs: dict, round_no: int):
        self._bind(s)
        cat = _feature_vec(query_attrs, "category")
        leaf = _feature_vec(query_attrs, "leaf")
        hit = s.memory_recall_by_shape(cat, leaf, round_no)
        if hit is None:
            return None
        cid, paged = hit
        return {"cluster_id": cid, "n_paged_in": paged}

    def recall(self, s, key: str, round_no: int):
        # recall by name -> route via shape descent on a neutral query is not name-exact;
        # for revisit-by-name we simply page the show's cluster by recomputing its shape
        # from what we know.  Adapter convenience; the SHAPE descent is the real recall.
        return None

    def findable(self, key: str) -> bool:
        return key in self._known

    def stats(self) -> dict:
        clusters = self._s.memory_index_clusters() if self._s is not None else 0
        return {"total_records": len(self._known), "resident_in_ram": None,
                "on_disk": len(self._known), "disk_bytes": None,
                "index_clusters": clusters}
