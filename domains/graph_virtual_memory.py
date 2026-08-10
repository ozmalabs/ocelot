"""graph_virtual_memory — OS-style DEMAND PAGING for the agent's GROWN corpus.

The Jabberwock is its own OS, and its memory faculty is already an OS memory
hierarchy: a byte-bounded working tier (`memory_bound` / `forget_over_budget`),
hot/cold tracking (`HotCounter`), a `never_forget` KERNEL (lexicon/concepts stay
resident), and per-cluster page-out. The mmap BULK STORE is
`domains/reference_slab` (an on-disk, mmap'd, index-addressed key->value slab —
query-time RSS is the WORKING SET, not the corpus).

THE SEAM THIS CLOSES. The Rust memory faculty's per-cluster page-out
(`MemoryFaculty::consolidate` / `page_in_cluster`) writes each record through
`persist`'s durable-JSON encoder into a *heap of per-node JSON files*, and reads
them back with `std::fs::read_to_string`. For the agent's GROWN corpus (the
consumed Wikipedia microtheories + their concepts) that is a JSON hack, not a
smooth page-out/in: paging a cold microtheory out is a directory of JSON blobs,
paging it in is a linear file read. This module wires the SAME loop to the mmap
BULK STORE instead:

    PAGE-OUT  (over budget): take a COLD cluster (a consumed Microtheory + its
              has_concept Concepts, keyed by topic), serialize it through the
              substrate's OWN wire format (`graph_to_dict`, the exact save
              encoder — restricted to the cluster's induced subgraph), APPEND
              it to the corpus `reference_slab` (key=topic, value=the encoded
              cluster), then EVICT those nodes from the live graph. The
              knowledge is now mmap'd on disk, NOT lost.

    PAGE-IN   (on foveation — a topic comes into focus): look the topic up in
              the corpus slab (mmap O(log n) index + one value page), decode the
              wire bytes, and re-install the cluster into the live graph. Round-
              trips through the SAME wire format `graph_to_dict` produced.

COMPOSED FROM EXISTING FACULTIES — nothing reinvented:
  · `reference_slab` (build_slab / Slab.lookup)   — the mmap bulk store (corpus).
  · `Substrate.graph_to_dict`                     — the wire/save encoder (value).
  · `Substrate.memory_bound` + `memory_total_bytes` — the resident cap (node +
    byte budget) that DRIVES page-out.
  · a last-access recency mirror of `HotCounter`  — LRU eviction order (which
    cold cluster to page out first). The Rust HotCounter still drives the
    faculty's own forget path; the page-out TARGET here lives Python-side (the
    slab), so the adapter mirrors last-access for the selection — admissible
    adapter bookkeeping (CLAUDE.md: "Python may cache for performance").
  · the `never_forget` KERNEL (lexicon)           — never registered as a cluster
    and guarded by type, so it is never paged out.

WORLD-ADAPTER DISCIPLINE (CLAUDE.md). This module owns NO agent decision. It is
mechanical host I/O: it MOVES bytes between the live graph and the mmap store
under a cap the agent configured (`memory_bound`), in LRU order. Serialize,
evict, look up, re-install. The knowledge, the categories, the values-for-
compute all live in the substrate / the memory faculty; this only pages them.

BYTE-IDENTICAL. The value stored in the slab is the cluster's induced subgraph in
CANONICAL wire form: node ids remapped to cluster-local indices by a
deterministic sort (type, attrs), so the stored bytes are independent of the live
graph's id allocation. Page-in re-installs (fresh live ids) and re-canonicalizes
to the SAME bytes -> a paged-out cluster round-trips with no data loss.
"""
from __future__ import annotations

import contextlib
import json
from pathlib import Path
from typing import Any, Iterable, Optional

from domains import reference_slab as rs

# Node types that are the never_forget KERNEL (the resident lexicon). A kernel
# node is never registered as a page-able cluster AND is guarded by type, so it
# is never evicted. The consumed-corpus clusters are Microtheory + Concept.
KERNEL_TYPES = frozenset({"LexEntry", "Lexicon", "Lexeme"})


# --------------------------------------------------------------------------- #
#  Canonical wire form — id-independent, deterministic, byte-stable.
# --------------------------------------------------------------------------- #

def _attrs_key(attrs: dict) -> str:
    return json.dumps(attrs, sort_keys=True, ensure_ascii=False, default=str)


def canonicalize(nodes: list[dict], edges: list[dict]) -> str:
    """Induced-subgraph -> canonical wire bytes. `nodes` are
    ``{id,type,attrs}`` and `edges` are ``{src,type,tgt,attrs}`` (both from
    `graph_to_dict`, restricted to the cluster). Node ids are remapped to
    cluster-local indices by a deterministic sort on (type, attrs) so the
    output is independent of the live graph's global id counter."""
    order = sorted(nodes, key=lambda n: (n["type"], _attrs_key(n["attrs"]), n["id"]))
    id2local = {n["id"]: i for i, n in enumerate(order)}
    cn = [{"local": i, "type": n["type"], "attrs": n["attrs"]}
          for i, n in enumerate(order)]
    ce = sorted(
        ({"src": id2local[e["src"]], "type": e["type"],
          "tgt": id2local[e["tgt"]], "attrs": e.get("attrs", {})}
         for e in edges if e["src"] in id2local and e["tgt"] in id2local),
        key=lambda e: (e["src"], e["type"], e["tgt"], _attrs_key(e["attrs"])))
    return json.dumps({"nodes": cn, "edges": ce},
                      sort_keys=True, ensure_ascii=False)


# --------------------------------------------------------------------------- #
#  The paging faculty.
# --------------------------------------------------------------------------- #

class GraphVirtualMemory:
    """Demand-paging over the live substrate + the corpus mmap slab.

    Live graph holds the WORKING SET; the corpus lives mmap'd on disk; the
    never_forget kernel (lexicon) stays resident. The resident cap
    (`memory_bound`) drives page-out; LRU recency (a HotCounter mirror) picks
    the victim; page-in is an mmap O(log n) slab lookup on foveation.
    """

    def __init__(self, sub, *, corpus: str = "corpus",
                 budget_nodes: int = 5000, budget_bytes: int = 67108864,
                 hot_window: int = 3, slab_dir: Optional[Path] = None,
                 kernel_types: Iterable[str] = KERNEL_TYPES):
        self.s = sub
        self.corpus = corpus
        self.budget_nodes = int(budget_nodes)
        self.budget_bytes = int(budget_bytes)
        self.hot_window = int(hot_window)
        self._kernel_types = frozenset(kernel_types)
        # Compose the Rust memory faculty's cap (same node/byte budget the agent
        # uses); we drive page-out off it rather than the delete-path forget.
        self.s.memory_bound(self.budget_nodes, self.budget_bytes, self.hot_window)
        # The slab store dir (else reference_slab's default data/slabs/). We do
        # NOT mutate rs.SLAB_DIR globally — that would leak into other adapters
        # (wiki reads etc.). Instead every rs.* call that reads the module
        # global is wrapped in `_slab_scope`, which sets + RESTORES it.
        self._slab_dir = Path(slab_dir) if slab_dir is not None else None
        # topic -> {"ids": set[int] (live node ids), "resident": bool}
        self._clusters: dict[str, dict] = {}
        # topic -> the canonical value bytes currently in the corpus slab.
        self._pairs: dict[str, str] = {}
        # topic -> round of last access (the HotCounter recency mirror; LRU).
        self._last_access: dict[str, int] = {}
        self._round = 0
        self._slab: Optional[rs.Slab] = None
        # stats
        self.n_page_out = 0
        self.n_page_in = 0

    # -- slab-dir scope (never leaks the module global) ---------------------

    @contextlib.contextmanager
    def _slab_scope(self):
        """Set reference_slab.SLAB_DIR to this store's dir for the duration of a
        slab call, then RESTORE it. reference_slab reads the global at call
        time (build_slab / slab_exists / _paths) or captures it at Slab.__init__
        (absolute paths), so a scoped swap is sufficient and never leaks."""
        if self._slab_dir is None:
            yield
            return
        saved = rs.SLAB_DIR
        rs.SLAB_DIR = self._slab_dir
        try:
            yield
        finally:
            rs.SLAB_DIR = saved

    # -- kernel guard -------------------------------------------------------

    def _is_kernel_type(self, nid) -> bool:
        try:
            return self.s.node(nid).get("type") in self._kernel_types
        except Exception:
            return False

    # -- cluster construction (mechanical adapter I/O) ----------------------

    def install_cluster(self, topic: str, concepts: list[dict]) -> "list":
        """Add a consumed Microtheory + its Concept nodes + has_concept edges to
        the LIVE graph and REGISTER it as a page-able cluster keyed by `topic`.
        Pure graph construction (the seed-loader shape: add_node + unchecked
        edges); no decision. Returns the created NodeIDs."""
        mt = self.s.add_node("Microtheory", {"topic": topic, "name": topic})
        ids = [mt]
        for c in concepts:
            attrs = dict(c)
            attrs.setdefault("part_of", topic)
            cid = self.s.add_node("Concept", attrs)
            self.s.add_edge_unchecked(mt, "has_concept", cid)
            ids.append(cid)
        self.register(topic, ids)
        return ids

    def register(self, topic: str, node_ids: Iterable) -> None:
        """Register live nodes as a page-able cluster keyed by `topic`, and mark
        it freshly accessed. Kernel-typed nodes are refused (never paged)."""
        ids = set()
        for nid in node_ids:
            if self._is_kernel_type(nid):
                continue
            ids.add(nid.value if hasattr(nid, "value") else int(nid))
        self._clusters[topic] = {"ids": ids, "resident": True}
        self._touch(topic)

    def _touch(self, topic: str) -> None:
        self._round += 1
        self._last_access[topic] = self._round

    # -- slab (corpus mmap store) -------------------------------------------

    def _rebuild_slab(self) -> None:
        """(Re)build the corpus slab from the accumulated (topic -> value) pairs.
        build_slab is the mmap bulk-store writer; APPEND = accumulate + rebuild
        (the corpus record count grows unbounded; each rebuild is O(corpus)
        write, page-IN stays mmap O(log n))."""
        with self._slab_scope():
            rs.build_slab(self.corpus, list(self._pairs.items()), force=True)
        # invalidate any open mmap (os.replace swapped the inode underneath it).
        if self._slab is not None:
            self._slab.close()
            self._slab = None
        rs._OPEN_SLABS.pop(self.corpus, None)

    def _open_slab(self) -> Optional[rs.Slab]:
        if self._slab is None:
            with self._slab_scope():
                if rs.slab_exists(self.corpus):
                    # Slab.__init__ captures absolute paths under the scope.
                    self._slab = rs.Slab(self.corpus)
        return self._slab

    def corpus_records(self) -> int:
        s = self._open_slab()
        return len(s) if s is not None else 0

    def _corpus_paths(self):
        with self._slab_scope():
            return rs._paths(self.corpus)

    def corpus_bytes(self) -> int:
        keys_p, vals_p = self._corpus_paths()
        try:
            return keys_p.stat().st_size + vals_p.stat().st_size
        except OSError:
            return 0

    def corpus_is_mmap_slab(self) -> bool:
        """The corpus target is a reference_slab mmap store (a .keys + .vals
        pair), NOT a heap of per-node JSON files."""
        keys_p, vals_p = self._corpus_paths()
        return keys_p.exists() and vals_p.exists()

    # -- extract / install a cluster's induced subgraph ---------------------

    def _extract_cluster(self, topic: str) -> tuple[str, list]:
        """The cluster's induced subgraph -> (canonical wire bytes, [NodeID]).
        Uses `graph_to_dict` (the save encoder) and restricts to the cluster's
        live ids."""
        cl = self._clusters[topic]
        ids = cl["ids"]
        full = self.s.graph_to_dict()
        nodes = [n for n in full["nodes"] if n["id"] in ids]
        edges = [e for e in full["edges"]
                 if e["src"] in ids and e["tgt"] in ids]
        value = canonicalize(nodes, edges)
        # NodeID objects to evict (from the live nodes() list, id in the set).
        to_remove = [nid for nid in self.s.nodes()
                     if (nid.value if hasattr(nid, "value") else int(nid)) in ids]
        return value, to_remove

    def _install_canonical(self, topic: str, value: str) -> set:
        """Decode canonical wire bytes and re-install the cluster into the live
        graph (fresh live ids; add_node + unchecked edges). Returns the new id
        set."""
        d = json.loads(value)
        local2nid = {}
        new_ids = set()
        for n in d["nodes"]:
            nid = self.s.add_node(n["type"], dict(n["attrs"]))
            local2nid[n["local"]] = nid
            new_ids.add(nid.value if hasattr(nid, "value") else int(nid))
        for e in d["edges"]:
            self.s.add_edge_unchecked(local2nid[e["src"]], e["type"],
                                      local2nid[e["tgt"]], dict(e.get("attrs", {})))
        return new_ids

    # -- page out / in ------------------------------------------------------

    def page_out(self, topic: str) -> int:
        """PAGE-OUT: serialize the cold cluster to the corpus mmap slab, then
        evict its nodes from the live graph. Returns nodes evicted."""
        cl = self._clusters.get(topic)
        if cl is None or not cl["resident"]:
            return 0
        value, to_remove = self._extract_cluster(topic)
        # APPEND to the corpus slab (accumulate + rebuild the mmap store).
        self._pairs[topic] = value
        self._rebuild_slab()
        # EVICT the live nodes — the knowledge is now mmap'd on disk.
        n = 0
        for nid in to_remove:
            if self.s.remove_node(nid):
                n += 1
        cl["ids"] = set()
        cl["resident"] = False
        self.n_page_out += 1
        return n

    def page_in(self, topic: str) -> int:
        """PAGE-IN: mmap O(log n) slab lookup, decode, re-install into the live
        graph. Returns nodes paged in."""
        cl = self._clusters.get(topic)
        if cl is not None and cl["resident"]:
            return 0
        s = self._open_slab()
        if s is None:
            return 0
        value = s.lookup(topic)
        if value is None:
            return 0
        new_ids = self._install_canonical(topic, value)
        self._clusters[topic] = {"ids": new_ids, "resident": True}
        self.n_page_in += 1
        return len(new_ids)

    def foveate(self, topic: str) -> int:
        """A topic comes into focus: page it in if resident-absent, then mark it
        freshly accessed (hot). Returns nodes paged in (0 if already resident)."""
        paged = self.page_in(topic)
        self._touch(topic)
        return paged

    def stored_value(self, topic: str) -> Optional[str]:
        """The exact canonical bytes for `topic` in the corpus slab (mmap read).
        Used to prove byte-identical page-out/in."""
        s = self._open_slab()
        return s.lookup(topic) if s is not None else None

    def cluster_fingerprint(self, topic: str) -> Optional[str]:
        """The canonical wire bytes of the currently-RESIDENT cluster (re-
        extracted from the live graph). Equal to `stored_value(topic)` iff the
        round-trip is byte-identical."""
        cl = self._clusters.get(topic)
        if cl is None or not cl["resident"]:
            return None
        value, _ = self._extract_cluster(topic)
        return value

    # -- the cap-driven eviction loop ---------------------------------------

    def resident_nodes(self) -> int:
        return self.s.node_count()

    def _over_budget(self) -> bool:
        return (self.s.node_count() > self.budget_nodes
                or self.s.memory_total_bytes() > self.budget_bytes)

    def _coldest_resident(self) -> Optional[str]:
        cand = [(self._last_access.get(t, 0), t)
                for t, c in self._clusters.items()
                if c["resident"] and c["ids"]]
        if not cand:
            return None
        cand.sort()
        return cand[0][1]

    def enforce(self) -> int:
        """While over the resident cap (node OR byte budget), page out the
        COLDEST resident cluster (LRU) to the corpus mmap slab. The kernel
        (lexicon) is never a cluster, so it is never evicted. Returns clusters
        paged out."""
        paged = 0
        while self._over_budget():
            victim = self._coldest_resident()
            if victim is None:
                break  # only the kernel remains — cannot page it (never_forget)
            self.page_out(victim)
            paged += 1
        return paged

    # -- stats --------------------------------------------------------------

    def stats(self) -> dict:
        resident_clusters = sum(1 for c in self._clusters.values() if c["resident"])
        return {
            "round": self._round,
            "resident_nodes": self.s.node_count(),
            "resident_bytes": self.s.memory_total_bytes(),
            "resident_clusters": resident_clusters,
            "total_clusters": len(self._clusters),
            "corpus_records": self.corpus_records(),
            "corpus_bytes": self.corpus_bytes(),
            "page_out": self.n_page_out,
            "page_in": self.n_page_in,
            "budget_nodes": self.budget_nodes,
        }


# --------------------------------------------------------------------------- #
#  Wikipedia-consumption wiring — flow consumed microtheories through paging.
# --------------------------------------------------------------------------- #

def page_consumed(gvm: GraphVirtualMemory, agent, result: dict) -> bool:
    """Register a `wikipedia_consumption.consume_article` RESULT as a page-able
    cluster: the taught Microtheory (by domain) + its has_concept Concepts. The
    caller then calls `gvm.enforce()` to page out over budget. Thin wiring —
    finds the live nodes and registers; no decision. Returns True if registered."""
    if not result.get("consumed"):
        return False
    sub = agent.s
    domain = result.get("domain")
    # locate the taught Microtheory by topic/name.
    mt = None
    for nid in sub.nodes("Microtheory"):
        a = sub.node(nid)["attrs"]
        if a.get("topic") == domain or a.get("name") == domain:
            mt = nid
            break
    if mt is None:
        return False
    ids = [mt] + list(sub.neighbours(mt, "has_concept"))
    gvm.register(domain, ids)
    return True


__all__ = [
    "GraphVirtualMemory", "canonicalize", "page_consumed", "KERNEL_TYPES",
]
