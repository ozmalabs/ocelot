//! Typed graph G — paper Axioms 1 + 3.
//!
//! Memory layout (the "custom efficient" part of the project brief):
//!
//! * Nodes live in a single `Vec<Option<NodeData>>` slab with a freelist —
//!   O(1) deref by `NodeID`, no per-node allocation, deletes leave a
//!   tombstone (Option::None) so existing NodeID handles stay valid until
//!   their slot is recycled by the freelist.
//! * Edges live in a parallel `Vec<Option<EdgeData>>` slab + freelist.
//! * Adjacency lives in `SmallVec`, not `HashSet`. Typical out-degrees in
//!   the substrate's actual workloads are 1–8 (Conway cells, chess
//!   squares, Doom percepts), so an inline SmallVec dominates a hash
//!   set both on memory (a HashSet of 4 entries is ~150 bytes; a
//!   SmallVec<[EdgeIdx; 4]> is 36 bytes) and on iteration speed
//!   (linear scan of contiguous u32s beats pointer-chasing).
//! * The `(node, edge_type)` index uses a finer SmallVec (cap 4) since
//!   per-edge-type degrees are even smaller.
//! * The `_edges` global is the slab itself; an `_edge_index` map gives
//!   `has_edge(src, edge_type, tgt)` an O(1) answer when needed but is
//!   skipped for the iteration-heavy hot paths.
//!
//! Snapshot iterators: the Python version `tuple()`-copies the key set
//! at iter start so concurrent mutation doesn't blow up the iterator.
//! Here we just clone the SmallVec (cheap: usually inline). New edges
//! appear on the *next* iteration call, matching Python semantics.

use crate::sym::Sym;
use crate::value::Value;
use roaring::RoaringBitmap;
use rustc_hash::{FxHashMap, FxHashSet};
use smallvec::SmallVec;

/// Dense node index. 4 bytes — fits next to `Sym` in EdgeKey without
/// growing the struct, and 4G nodes is plenty for any plausible
/// substrate workload.
#[derive(Copy, Clone, Debug, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub struct NodeID(pub u32);

impl NodeID {
    #[inline]
    pub fn value(self) -> u32 {
        self.0
    }
}

/// Dense edge index — same shape and rationale as NodeID. Used as the
/// SmallVec payload for adjacency lists; resolving to the actual
/// EdgeKey / EdgeData goes through `TypedGraph::_edges[idx]`.
#[derive(Copy, Clone, Debug, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub struct EdgeIdx(pub u32);

/// (src, edge_type, tgt) triple — the structural key of an edge.
/// `Sym` for edge_type so look-ups are u32 compares on the hot path.
#[derive(Copy, Clone, Debug, PartialEq, Eq, Hash)]
pub struct EdgeKey {
    pub src: NodeID,
    pub edge_type: Sym,
    pub tgt: NodeID,
}

/// Opt-in set of graph locations touched through TypedGraph mutation APIs.
/// It intentionally over-approximates no-op mutable accesses, while keeping
/// node and edge identities deduplicated during one observed operation.
#[derive(Clone, Debug, Default)]
pub struct GraphMutationLog {
    pub changed_nodes: FxHashSet<NodeID>,
    pub changed_edges: FxHashSet<EdgeKey>,
    /// Type observed before the first mutation access in this log. Retained
    /// across deletion/retyping so callers can route nodes that no longer
    /// have a live graph record (for example a deleted Microtheory root).
    pub node_types: FxHashMap<NodeID, Sym>,
}

/// Attribute store — `Vec`-backed, linear-scan lookup. Replaces the
/// per-node/per-edge `FxHashMap<Sym, Value>` that was eating ~32 bytes
/// header per slot regardless of attr count. For the substrate's typical
/// attr counts (0-5 per node, 0-1 per edge), a linear scan over u32
/// `Sym` comparisons beats the hashmap probe + key hash. Memory: empty
/// Attrs = 24 bytes (lazy heap allocation); populated = 24 + 32*N.
#[derive(Clone, Debug, Default)]
pub struct Attrs(pub Vec<(Sym, Value)>);

impl Attrs {
    #[inline]
    pub fn new() -> Self {
        Self(Vec::new())
    }
    #[inline]
    pub fn with_capacity(c: usize) -> Self {
        Self(Vec::with_capacity(c))
    }
    #[inline]
    pub fn len(&self) -> usize {
        self.0.len()
    }
    #[inline]
    pub fn is_empty(&self) -> bool {
        self.0.is_empty()
    }
    pub fn get(&self, key: &Sym) -> Option<&Value> {
        self.0.iter().find(|(k, _)| k == key).map(|(_, v)| v)
    }
    pub fn contains_key(&self, key: &Sym) -> bool {
        self.0.iter().any(|(k, _)| k == key)
    }
    pub fn insert(&mut self, key: Sym, value: Value) -> Option<Value> {
        if let Some(pos) = self.0.iter().position(|(k, _)| *k == key) {
            Some(std::mem::replace(&mut self.0[pos].1, value))
        } else {
            self.0.push((key, value));
            None
        }
    }
    pub fn remove(&mut self, key: &Sym) -> Option<Value> {
        if let Some(pos) = self.0.iter().position(|(k, _)| k == key) {
            Some(self.0.swap_remove(pos).1)
        } else {
            None
        }
    }
    pub fn values(&self) -> impl Iterator<Item = &Value> {
        self.0.iter().map(|(_, v)| v)
    }
    pub fn iter(&self) -> impl Iterator<Item = (&Sym, &Value)> {
        self.0.iter().map(|(k, v)| (k, v))
    }
}

impl From<FxHashMap<Sym, Value>> for Attrs {
    fn from(map: FxHashMap<Sym, Value>) -> Self {
        let mut v = Vec::with_capacity(map.len());
        v.extend(map.into_iter());
        Self(v)
    }
}

impl<'a> IntoIterator for &'a Attrs {
    type Item = (&'a Sym, &'a Value);
    type IntoIter = std::iter::Map<
        std::slice::Iter<'a, (Sym, Value)>,
        fn(&'a (Sym, Value)) -> (&'a Sym, &'a Value),
    >;
    fn into_iter(self) -> Self::IntoIter {
        fn pair<'b>(p: &'b (Sym, Value)) -> (&'b Sym, &'b Value) {
            (&p.0, &p.1)
        }
        self.0.iter().map(pair)
    }
}

/// Per-node payload — type + Attrs.
#[derive(Clone, Debug)]
pub struct NodeData {
    pub type_: Sym,
    pub attrs: Attrs,
}

/// Per-edge payload — src + edge_type + tgt, no inline attrs.
///
/// Edges with attributes are RARE in the substrate's typical workloads:
/// Conway / chess / Doom graphs have zero, audio pipelines have a few
/// per-stage. So storing attrs INLINE in every EdgeData (even an empty
/// 24-byte Vec header) was wasted bytes on the dominant case. Edge attrs
/// now live in `TypedGraph::edge_attrs`, a sparse `FxHashMap<EdgeIdx,
/// Attrs>` — only populated entries cost memory. For 4M Conway edges
/// with zero attrs, that's a 24-bytes-per-edge saving (96 MiB). For
/// audio edges with attrs, the cost is a hashmap entry (~48 bytes total)
/// vs the old inline Vec header (24 bytes) + heap — net wash.
#[derive(Clone, Debug)]
pub struct EdgeData {
    pub src: NodeID,
    pub edge_type: Sym,
    pub tgt: NodeID,
}

impl EdgeData {
    /// Recover the `EdgeKey` for callers that want the structural triple.
    /// Cheap — just packs three fields.
    #[inline]
    pub fn key(&self) -> EdgeKey {
        EdgeKey {
            src: self.src,
            edge_type: self.edge_type,
            tgt: self.tgt,
        }
    }
}

/// Lookup-table view of an edge's attrs that callers can use anywhere
/// the old `edge.attrs` field worked. Returns `&Attrs` (possibly empty
/// — a static reference to a never-populated Attrs so the .get / .iter
/// path is uniform whether the edge has attrs or not).
fn empty_attrs_ref() -> &'static Attrs {
    use std::sync::OnceLock;
    static EMPTY: OnceLock<Attrs> = OnceLock::new();
    EMPTY.get_or_init(Attrs::new)
}

/// The typed graph itself. All mutation goes through `_insert_node` /
/// `_insert_edge` / `_delete_*`; public mutation flows through
/// `Substrate` (Π) so the admissibility check fires.
pub struct TypedGraph {
    /// Monotonic content revision. Every mutable graph access or successful
    /// structural mutation advances this counter, allowing pure native
    /// analyses to validate memoized results in O(1). The counter is
    /// deliberately conservative: a mutation outside an analysis' read set
    /// may cause a miss, but no mutation can leave a stale hit.
    mutation_version: u64,
    /// Allocated only for an explicitly observed operation. Mutation methods
    /// append their targets here; the normal graph path retains `None`.
    mutation_log: Option<GraphMutationLog>,
    /// Slab of nodes — Option so freed slots can be reused without
    /// invalidating existing NodeID handles that nobody holds anymore.
    nodes: Vec<Option<NodeData>>,
    /// Reusable NodeID indices. LIFO so the most-recently-freed slot
    /// is the next to be reused — keeps the arena dense.
    node_freelist: Vec<u32>,

    /// Edge slab + freelist, same structure.
    edges: Vec<Option<EdgeData>>,
    edge_freelist: Vec<u32>,
    /// Monotone generation for any edge deletion. Scoped local-candidate
    /// ordering uses EdgeIdx as insertion order only while this is zero; the
    /// freelist can otherwise reuse an index across edge types.
    edge_delete_generation: u64,

    /// Sparse edge attributes — only populated entries cost memory.
    /// Typical substrate edges have zero attrs (Conway, chess, Doom),
    /// so this map stays tiny in the dominant case. Audio pipeline
    /// edges with carry-along scalars pay one entry each.
    edge_attrs: FxHashMap<EdgeIdx, Attrs>,

    /// nodes-of-type index: Sym → contiguous Vec<NodeID>. Linear scan
    /// of a small Vec is hard to beat for typed iteration.
    by_type: FxHashMap<Sym, Vec<NodeID>>,

    /// Per-node full out-edge list (any edge_type).
    out: Vec<SmallVec<[EdgeIdx; 4]>>,
    /// Per-node full in-edge list.
    in_: Vec<SmallVec<[EdgeIdx; 4]>>,
    /// Per-(node, edge_type) out-edges. The hot path:
    /// `Neighbours(node, edge_type="adjacent_to")` resolves here in
    /// one hash lookup.
    out_by_type: FxHashMap<(NodeID, Sym), SmallVec<[EdgeIdx; 4]>>,
    /// Same for in-edges; powers `InNeighbours`.
    in_by_type: FxHashMap<(NodeID, Sym), SmallVec<[EdgeIdx; 4]>>,

    /// Edge-type → all EdgeIdx of that type. The rule engine's
    /// double-unbound match clause `[a, edge_type, b]` reads this to
    /// get O(matches) lookup instead of scanning every edge in the
    /// graph. Maintained automatically across edge insert/delete.
    edges_by_type: FxHashMap<Sym, Vec<EdgeIdx>>,

    /// PER-EDGE-TYPE DELETE VERSION (block 192000 — incremental match, ladder
    /// rung A). Bumped by `delete_edge` (the single deletion choke point;
    /// `delete_node` cascades through it, so node-delete and effect-delete are
    /// covered too) each time an edge of a given type is removed. A per-rule
    /// semi-naive cursor over `edges_by_type[et]` stays VALID across a delete of
    /// a DIFFERENT edge type — that type's `Vec` is untouched, so the cursor
    /// position is still meaningful — but is INVALIDATED by a delete of ITS OWN
    /// type (which `retain`s the array and shifts indices). This replaces the
    /// engine's single GLOBAL `edge_delete_version` sledgehammer (which any
    /// delete anywhere bumps, invalidating every cursor) with type-local
    /// retraction. Always maintained (one hashmap increment per delete; invisible
    /// to `graph_to_dict`); READ only when `Substrate::incremental_match` is on,
    /// so the default engine is byte-unchanged. A type never deleted has version
    /// 0 (absent ⇒ 0).
    edge_delete_version_by_type: FxHashMap<Sym, u64>,

    /// Declared attribute indices (Phase 7b). Maps `(node_type,
    /// attr_key) → value → SmallVec<NodeID>`. Maintained automatically
    /// across `insert_node` / `delete_node` / `set_node_attr` /
    /// `set_node_type` so queries against an indexed (type, key) pair
    /// return in O(1+result). Closes the "Filter(nodes(t), Eq(Attr...))
    /// is O(N)" gap from the gap analysis — declaring an index turns
    /// that into a B-tree-style lookup.
    /// Declared attribute indices, payload as `RoaringBitmap` rather
    /// than `SmallVec<[NodeID; 4]>` so dense sets (e.g. "every AliveCell
    /// in a 1M-node graph") compress ~30× vs a flat Vec and AND/OR/NOT/
    /// popcount run in SIMD. Sparse sets stay efficient via Roaring's
    /// adaptive container choice (array / bitset / run-length).
    attr_indices: FxHashMap<(Sym, Sym), FxHashMap<Value, RoaringBitmap>>,

    /// INTRINSIC SELF-REPAIR queue. A `SetRuleClause` effect cannot mutate the
    /// rule list from inside `apply_rule_full` (it only holds `&mut graph`), so it
    /// QUEUES the edit here as `(rule_name, field, new_clause_value)`; `Substrate::
    /// run_rules` drains this between passes, where it holds `&mut self.rules`
    /// cleanly, and swaps the named rule's `where`/`effect`. Transient (drained to
    /// empty within run_rules); not part of the persisted graph.
    pub pending_rule_edits: Vec<(String, String, Value)>,

    /// Transactional self-modification queue. `ApplyRulePatch` effects push
    /// the bound graph-resident `RulePatch` node here; `Substrate` drains the
    /// queue between passes, where it can stage and atomically replace the
    /// corresponding live rule without borrowing the matcher.
    pub pending_rule_patches: Vec<NodeID>,

    /// PERCEPTION-AS-ACTION queue. An `Effect::FbSample` cannot call
    /// `Substrate::fb_sample` from inside `apply_rule_full` (it only
    /// holds `&mut graph`, not `&mut Substrate` — which owns the
    /// attached-framebuffer registry and the dirty-tracking node/edge
    /// mutation helpers `segment_and_track` needs), so it QUEUES
    /// `(fb_id, game, grid_w, grid_h)` here; `Substrate::run_rules`
    /// drains this each pass (where `&mut self` is free) by calling
    /// `Substrate::fb_sample` — the same fn the PyO3 `fb_sample` method
    /// calls. Transient (drained to empty within `run_rules`); not
    /// part of the persisted graph. Mirrors `pending_rule_edits` above.
    pub pending_fb_samples: Vec<(u32, NodeID, usize, usize)>,

    /// GRAPH LAW #6 queue. An `Effect::TrackIdentity` cannot call
    /// `Substrate::track_identity` from inside `apply_rule_full` (it
    /// only holds `&mut graph`, not `&mut Substrate`), so it QUEUES
    /// `(prev_ids, cur_ids, feature_key, category_key, extent_key,
    /// identity_key, radius)` here; `Substrate::run_rules` drains this
    /// each pass by calling `Substrate::track_identity` — the same fn
    /// a direct/PyO3 call uses. Transient; not part of the persisted
    /// graph. Mirrors `pending_fb_samples` above.
    #[allow(clippy::type_complexity)]
    pub pending_track_identity: Vec<(
        Vec<NodeID>,
        Vec<NodeID>,
        Sym,
        Option<Sym>,
        Option<Sym>,
        Sym,
        f64,
    )>,

    /// SELF-TRAINING queue. An `Effect::NetCollapse` cannot mutate a net's
    /// `WeightTensor` data from inside `apply_rule_full` (it only holds
    /// `&mut graph`, and the collapse reads+writes across the assemblage),
    /// so it QUEUES `(reflex_net, input_vec, target_vec, eta)` here;
    /// `Substrate::run_rules` drains this each pass by calling
    /// `net_forward::net_collapse_step` on the net's assemblage and
    /// recording the surprise back onto the reflex net. Transient; not part
    /// of the persisted graph. Mirrors `pending_fb_samples` above — this is
    /// how "collapse and surprise within the net" runs INSIDE the engine's
    /// run_rules loop rather than a Python observation loop.
    pub pending_net_collapses: Vec<(NodeID, Vec<f64>, Vec<f64>, f64)>,
    /// block 292000 — rule-effect attr-write log for frontier-incremental
    /// predicate retraction. Every rule-effect `SetAttr` (via `set_node_attr`)
    /// pushes `(node, key)` here, but ONLY when `log_attr_writes` is on (a mirror
    /// of `Substrate::predicate_retraction`). The Substrate drains it in
    /// `dirty_by_writeset` to seed `rule_dirty_nodes` for covered consumers,
    /// KEEPING their cursor (re-evaluate only the frontier) instead of clearing it.
    /// Default-off ⇒ the push is gated ⇒ byte- and cost-identical.
    pub attr_write_log: Vec<(NodeID, Sym)>,
    pub log_attr_writes: bool,
}

impl TypedGraph {
    pub fn new() -> Self {
        Self {
            mutation_version: 0,
            mutation_log: None,
            nodes: Vec::with_capacity(256),
            node_freelist: Vec::new(),
            edges: Vec::with_capacity(512),
            edge_freelist: Vec::new(),
            edge_delete_generation: 0,
            edge_attrs: FxHashMap::default(),
            by_type: FxHashMap::default(),
            out: Vec::with_capacity(256),
            in_: Vec::with_capacity(256),
            out_by_type: FxHashMap::default(),
            in_by_type: FxHashMap::default(),
            edges_by_type: FxHashMap::default(),
            edge_delete_version_by_type: FxHashMap::default(),
            attr_indices: FxHashMap::default(),
            pending_rule_edits: Vec::new(),
            pending_rule_patches: Vec::new(),
            pending_fb_samples: Vec::new(),
            pending_track_identity: Vec::new(),
            pending_net_collapses: Vec::new(),
            attr_write_log: Vec::new(),
            log_attr_writes: false,
        }
    }

    /// Edge IDs of `edge_type`. O(1) hash lookup. Used by the rule
    /// engine's double-unbound match path so it doesn't iterate the
    /// entire edge list each time. Returns a slice the caller can
    /// iterate without copying.
    /// PER-EDGE-TYPE DELETE VERSION (block 192000). See the field doc. Absent ⇒
    /// 0 (a type never deleted). O(1) hash lookup; READ only by the incremental
    /// matcher when `Substrate::incremental_match` is on.
    pub fn edge_delete_version_by_type(&self, edge_type: Sym) -> u64 {
        self.edge_delete_version_by_type
            .get(&edge_type)
            .copied()
            .unwrap_or(0)
    }

    /// Global edge-deletion generation, used by algorithms whose ordering
    /// proof depends on the edge freelist never having been used.
    pub fn edge_delete_generation(&self) -> u64 { self.edge_delete_generation }

    pub fn edges_by_type(&self, edge_type: Sym) -> &[EdgeIdx] {
        self.edges_by_type
            .get(&edge_type)
            .map(|v| v.as_slice())
            .unwrap_or(&[])
    }

    // --- attribute indices (Phase 7b) ---

    /// Declare an attribute index on `(node_type, attr_key)`. Indexes
    /// any existing nodes of `node_type` whose attrs include `attr_key`.
    /// Idempotent — re-declaring is a no-op.
    pub fn declare_attr_index(&mut self, node_type: Sym, attr_key: Sym) {
        if self.attr_indices.contains_key(&(node_type, attr_key)) {
            return;
        }
        let mut bucket: FxHashMap<Value, RoaringBitmap> = FxHashMap::default();
        // Back-fill: walk every node of this type that already has the
        // attr so the index is consistent the moment it's declared.
        if let Some(nids) = self.by_type.get(&node_type) {
            for &nid in nids {
                if let Some(slot) = self.nodes.get(nid.0 as usize) {
                    if let Some(node) = slot.as_ref() {
                        if let Some(v) = node.attrs.get(&attr_key) {
                            bucket
                                .entry(v.clone())
                                .or_insert_with(RoaringBitmap::new)
                                .insert(nid.0);
                        }
                    }
                }
            }
        }
        self.attr_indices.insert((node_type, attr_key), bucket);
    }

    /// O(1) lookup: NodeIDs of nodes typed `node_type` whose
    /// `attr_key` attribute equals `value`. Returns an empty Vec if
    /// the index hasn't been declared (caller falls back to Filter).
    pub fn nodes_where(&self, node_type: Sym, attr_key: Sym, value: &Value) -> Vec<NodeID> {
        self.attr_indices
            .get(&(node_type, attr_key))
            .and_then(|b| b.get(value))
            .map(|bm| bm.iter().map(NodeID).collect())
            .unwrap_or_default()
    }

    /// Direct bitmap access to a declared attr index. Returns the
    /// Roaring bitmap for `(node_type, attr_key) == value` or `None`
    /// if the index hasn't been declared. Bitmap callers do their own
    /// AND/OR/NOT/popcount — much faster than materialising a Vec.
    pub fn nodes_where_bitmap(
        &self,
        node_type: Sym,
        attr_key: Sym,
        value: &Value,
    ) -> Option<&RoaringBitmap> {
        self.attr_indices
            .get(&(node_type, attr_key))
            .and_then(|b| b.get(value))
    }

    /// True iff `(node_type, attr_key)` has a declared index. Lets
    /// callers know whether `nodes_where` is going to be O(1) vs
    /// always-empty.
    pub fn has_attr_index(&self, node_type: Sym, attr_key: Sym) -> bool {
        self.attr_indices.contains_key(&(node_type, attr_key))
    }

    /// Bitmap intersection across multiple declared indexes. Each input
    /// is a `(node_type, attr_key, value)` triple resolving to a Roaring
    /// bitmap; the result is their AND. Indexes that aren't declared
    /// return `None`. SIMD-accelerated intersection — for the canonical
    /// "all alive cells whose state is `excited`" multi-condition query,
    /// this is microseconds vs the previous quadratic Filter-of-Filter.
    pub fn intersect_attr_indexes(
        &self,
        conditions: &[(Sym, Sym, &Value)],
    ) -> Option<RoaringBitmap> {
        let mut iter = conditions.iter();
        let first = iter.next()?;
        let mut acc = self.nodes_where_bitmap(first.0, first.1, first.2)?.clone();
        for cond in iter {
            let Some(bm) = self.nodes_where_bitmap(cond.0, cond.1, cond.2) else {
                return None;
            };
            acc &= bm;
            if acc.is_empty() {
                return Some(acc);
            }
        }
        Some(acc)
    }

    /// Internal: add `nid` (typed `node_type`, with attrs `attrs`) to
    /// every applicable declared index.
    fn index_node(&mut self, nid: NodeID, node_type: Sym, attrs: &Attrs) {
        // Collect the (key, value) pairs to insert first so we don't
        // alias the borrow on self.attr_indices while iterating.
        let mut additions: SmallVec<[(Sym, Sym, Value); 4]> = SmallVec::new();
        for (k, v) in attrs {
            if self.attr_indices.contains_key(&(node_type, *k)) {
                additions.push((node_type, *k, v.clone()));
            }
        }
        for (t, k, v) in additions {
            self.attr_indices
                .entry((t, k))
                .or_default()
                .entry(v)
                .or_insert_with(RoaringBitmap::new)
                .insert(nid.0);
        }
    }

    /// Internal: remove `nid` from every index that may contain it.
    fn unindex_node(&mut self, nid: NodeID, node_type: Sym) {
        // Walk indices declared for this type; for each value bucket,
        // drop occurrences of nid.
        let keys: SmallVec<[(Sym, Sym); 4]> = self
            .attr_indices
            .keys()
            .filter(|(t, _)| *t == node_type)
            .copied()
            .collect();
        for key in keys {
            if let Some(bucket) = self.attr_indices.get_mut(&key) {
                bucket.retain(|_, bm| {
                    bm.remove(nid.0);
                    !bm.is_empty()
                });
            }
        }
    }

    // --- queries ---

    /// Current graph-content revision for conservative native memoization.
    #[inline]
    pub fn mutation_version(&self) -> u64 {
        self.mutation_version
    }

    #[inline]
    fn bump_mutation_version(&mut self) {
        self.mutation_version = self.mutation_version.wrapping_add(1);
    }

    /// Begin opt-in write-target collection. Nested collection is a caller
    /// error because each report must have one unambiguous closure boundary.
    pub fn begin_mutation_log(&mut self) {
        assert!(self.mutation_log.is_none(), "graph mutation log already active");
        self.mutation_log = Some(GraphMutationLog::default());
    }

    /// Finish collection and return the deduplicated targets. Returns an
    /// empty log when collection was not active.
    pub fn finish_mutation_log(&mut self) -> GraphMutationLog {
        self.mutation_log.take().unwrap_or_default()
    }

    fn log_node_mutation(&mut self, nid: NodeID) {
        let node_type = self
            .nodes
            .get(nid.0 as usize)
            .and_then(|slot| slot.as_ref())
            .map(|node| node.type_);
        if let Some(log) = self.mutation_log.as_mut() {
            log.changed_nodes.insert(nid);
            if let Some(node_type) = node_type {
                log.node_types.entry(nid).or_insert(node_type);
            }
        }
    }

    fn log_edge_mutation(&mut self, key: EdgeKey) {
        if let Some(log) = self.mutation_log.as_mut() {
            log.changed_edges.insert(key);
            log.changed_nodes.insert(key.src);
            log.changed_nodes.insert(key.tgt);
        }
    }

    pub fn node(&self, nid: NodeID) -> &NodeData {
        self.nodes[nid.0 as usize]
            .as_ref()
            .expect("node id refers to a freed slot")
    }

    pub fn node_mut(&mut self, nid: NodeID) -> &mut NodeData {
        self.bump_mutation_version();
        self.log_node_mutation(nid);
        self.nodes[nid.0 as usize]
            .as_mut()
            .expect("node id refers to a freed slot")
    }

    pub fn has_node(&self, nid: NodeID) -> bool {
        self.nodes
            .get(nid.0 as usize)
            .map(|s| s.is_some())
            .unwrap_or(false)
    }

    pub fn edge(&self, idx: EdgeIdx) -> &EdgeData {
        self.edges[idx.0 as usize]
            .as_ref()
            .expect("edge idx refers to a freed slot")
    }

    pub fn has_edge(&self, src: NodeID, edge_type: Sym, tgt: NodeID) -> bool {
        self.edge_idx(src, edge_type, tgt).is_some()
    }

    /// O(out_by_type[(src,et)].len()) scan — typically 0-4 entries on
    /// substrate workloads, so faster than a hashmap probe + key hash.
    /// The previous `edge_index: FxHashMap<EdgeKey, EdgeIdx>` cost
    /// ~32 bytes/edge for an O(1) answer this path replaces.
    pub fn edge_idx(&self, src: NodeID, edge_type: Sym, tgt: NodeID) -> Option<EdgeIdx> {
        let candidates = self.out_by_type.get(&(src, edge_type))?;
        for idx in candidates {
            if let Some(ed) = self.edges.get(idx.0 as usize).and_then(|s| s.as_ref()) {
                if ed.tgt == tgt {
                    return Some(*idx);
                }
            }
        }
        None
    }

    /// Iterate nodes (all, or of a specific type). Snapshot-style:
    /// the index Vec is cloned at iter start so concurrent inserts
    /// don't invalidate iteration (matches Python's tuple-snapshot
    /// behaviour).
    pub fn nodes_of_type(&self, type_: Sym) -> Vec<NodeID> {
        self.by_type.get(&type_).cloned().unwrap_or_default()
    }

    pub fn all_nodes(&self) -> Vec<NodeID> {
        let mut out = Vec::with_capacity(self.node_count());
        for (i, slot) in self.nodes.iter().enumerate() {
            if slot.is_some() {
                out.push(NodeID(i as u32));
            }
        }
        out
    }

    /// Out-edges, optionally restricted to `edge_type`. Returns the
    /// snapshot Vec of EdgeIdx; deleted edges (whose slot has been
    /// recycled) are filtered by `edge()`-lookup at the call site.
    pub fn out_edges_idx(&self, nid: NodeID, edge_type: Option<Sym>) -> Vec<EdgeIdx> {
        self.out_edges_slice(nid, edge_type).to_vec()
    }

    pub fn in_edges_idx(&self, nid: NodeID, edge_type: Option<Sym>) -> Vec<EdgeIdx> {
        self.in_edges_slice(nid, edge_type).to_vec()
    }

    /// Zero-alloc slice into the adjacency table. The previous
    /// `out_edges_idx` cloned the SmallVec into a fresh Vec on every
    /// `Neighbours` call (millions of times per Conway tick); the
    /// slice form skips that. Returns `&[]` if the (node, edge_type)
    /// has no entry. The slice is borrowed from `out_by_type` /
    /// `out`; the borrow's lifetime is the graph's. Iteration paths
    /// that don't mutate the graph between read and use take the
    /// slice; paths that may mutate (rule effects) take the owned Vec.
    pub fn out_edges_slice(&self, nid: NodeID, edge_type: Option<Sym>) -> &[EdgeIdx] {
        match edge_type {
            Some(et) => self
                .out_by_type
                .get(&(nid, et))
                .map(|v| v.as_slice())
                .unwrap_or(&[]),
            None => self
                .out
                .get(nid.0 as usize)
                .map(|v| v.as_slice())
                .unwrap_or(&[]),
        }
    }

    pub fn in_edges_slice(&self, nid: NodeID, edge_type: Option<Sym>) -> &[EdgeIdx] {
        match edge_type {
            Some(et) => self
                .in_by_type
                .get(&(nid, et))
                .map(|v| v.as_slice())
                .unwrap_or(&[]),
            None => self
                .in_
                .get(nid.0 as usize)
                .map(|v| v.as_slice())
                .unwrap_or(&[]),
        }
    }

    /// Convenience: out-neighbours (tgt of each out-edge), optionally
    /// restricted to `edge_type`. Yields NodeIDs directly — no
    /// intermediate Edge struct, which is what `Neighbours`-Term wants.
    pub fn neighbours(&self, nid: NodeID, edge_type: Option<Sym>) -> Vec<NodeID> {
        self.out_edges_slice(nid, edge_type)
            .iter()
            .filter_map(|idx| self.edges[idx.0 as usize].as_ref().map(|e| e.tgt))
            .collect()
    }

    pub fn in_neighbours(&self, nid: NodeID, edge_type: Option<Sym>) -> Vec<NodeID> {
        self.in_edges_slice(nid, edge_type)
            .iter()
            .filter_map(|idx| self.edges[idx.0 as usize].as_ref().map(|e| e.src))
            .collect()
    }

    // --- mutation (gated through Substrate / Π) ---

    pub fn insert_node(&mut self, type_: Sym, attrs: impl Into<Attrs>) -> NodeID {
        self.bump_mutation_version();
        let attrs: Attrs = attrs.into();
        // Snapshot attrs for indexing before we move them into the slab.
        let attrs_for_index = attrs.clone();
        let data = NodeData { type_, attrs };
        let nid = if let Some(slot) = self.node_freelist.pop() {
            self.nodes[slot as usize] = Some(data);
            NodeID(slot)
        } else {
            let idx = self.nodes.len() as u32;
            self.nodes.push(Some(data));
            self.out.push(SmallVec::new());
            self.in_.push(SmallVec::new());
            NodeID(idx)
        };
        // Grow out/in slabs if we recycled a slot at the high-water mark.
        while self.out.len() <= nid.0 as usize {
            self.out.push(SmallVec::new());
        }
        while self.in_.len() <= nid.0 as usize {
            self.in_.push(SmallVec::new());
        }
        self.by_type.entry(type_).or_default().push(nid);
        // Maintain declared attr indices — Phase 7b. No-op if no index
        // is declared for any (type_, attr_key) on this node.
        if !self.attr_indices.is_empty() {
            self.index_node(nid, type_, &attrs_for_index);
        }
        self.log_node_mutation(nid);
        nid
    }

    pub fn insert_edge(
        &mut self,
        src: NodeID,
        edge_type: Sym,
        tgt: NodeID,
        attrs: impl Into<Attrs>,
    ) -> Result<EdgeIdx, EdgeInsertError> {
        let attrs: Attrs = attrs.into();
        if !self.has_node(src) {
            return Err(EdgeInsertError::MissingSrc(src));
        }
        if !self.has_node(tgt) {
            return Err(EdgeInsertError::MissingTgt(tgt));
        }
        self.bump_mutation_version();
        let store_attrs = |idx: EdgeIdx, this: &mut Self, attrs: Attrs| {
            if attrs.is_empty() {
                this.edge_attrs.remove(&idx);
            } else {
                this.edge_attrs.insert(idx, attrs);
            }
        };
        if let Some(existing) = self.edge_idx(src, edge_type, tgt) {
            // Python's `_insert_edge` overwrites attrs silently; replicate.
            self.edges[existing.0 as usize] = Some(EdgeData {
                src,
                edge_type,
                tgt,
            });
            store_attrs(existing, self, attrs);
            self.log_edge_mutation(EdgeKey { src, edge_type, tgt });
            return Ok(existing);
        }
        let data = EdgeData {
            src,
            edge_type,
            tgt,
        };
        let idx = if let Some(slot) = self.edge_freelist.pop() {
            self.edges[slot as usize] = Some(data);
            EdgeIdx(slot)
        } else {
            let i = self.edges.len() as u32;
            self.edges.push(Some(data));
            EdgeIdx(i)
        };
        self.out[src.0 as usize].push(idx);
        self.in_[tgt.0 as usize].push(idx);
        self.out_by_type
            .entry((src, edge_type))
            .or_default()
            .push(idx);
        self.in_by_type
            .entry((tgt, edge_type))
            .or_default()
            .push(idx);
        self.edges_by_type.entry(edge_type).or_default().push(idx);
        store_attrs(idx, self, attrs);
        self.log_edge_mutation(EdgeKey { src, edge_type, tgt });
        Ok(idx)
    }

    pub fn delete_edge(&mut self, idx: EdgeIdx) -> Option<EdgeData> {
        let slot = self.edges.get_mut(idx.0 as usize)?;
        let data = slot.take()?;
        self.bump_mutation_version();
        let key = data.key();
        self.log_edge_mutation(key);
        // Remove from every index. SmallVec.retain is O(n) but n is tiny;
        // for the giant-adjacency edge case a swap_remove pattern would
        // help, but profile first.
        if let Some(v) = self.out.get_mut(key.src.0 as usize) {
            v.retain(|e| *e != idx);
        }
        if let Some(v) = self.in_.get_mut(key.tgt.0 as usize) {
            v.retain(|e| *e != idx);
        }
        if let Some(v) = self.out_by_type.get_mut(&(key.src, key.edge_type)) {
            v.retain(|e| *e != idx);
        }
        if let Some(v) = self.in_by_type.get_mut(&(key.tgt, key.edge_type)) {
            v.retain(|e| *e != idx);
        }
        if let Some(v) = self.edges_by_type.get_mut(&key.edge_type) {
            v.retain(|e| *e != idx);
        }
        // Block 192000: the `edges_by_type[et]` array just shifted, so every
        // semi-naive cursor over `et` is now stale. Bump THIS type's delete
        // version (not a global counter) so only cursors reading `et` invalidate.
        *self
            .edge_delete_version_by_type
            .entry(key.edge_type)
            .or_insert(0) += 1;
        self.edge_delete_generation = self.edge_delete_generation.saturating_add(1);
        self.edge_attrs.remove(&idx);
        self.edge_freelist.push(idx.0);
        Some(data)
    }

    /// Read-only view of an edge's attributes. Returns a reference to a
    /// static empty `Attrs` when the edge has no attrs stored, so callers
    /// don't need to handle the "edge has zero attrs" path specially.
    /// O(1) — single hashmap lookup.
    pub fn edge_attrs(&self, idx: EdgeIdx) -> &Attrs {
        self.edge_attrs
            .get(&idx)
            .unwrap_or_else(|| empty_attrs_ref())
    }

    /// Mutable access to an edge's attributes. Creates an empty `Attrs`
    /// entry if none exists yet — call `set_edge_attr_clear` after
    /// removing all attrs if you want to free the entry.
    pub fn edge_attrs_mut(&mut self, idx: EdgeIdx) -> &mut Attrs {
        self.bump_mutation_version();
        if let Some(edge) = self.edges.get(idx.0 as usize).and_then(|slot| slot.as_ref()) {
            let key = edge.key();
            self.log_edge_mutation(key);
        }
        self.edge_attrs.entry(idx).or_default()
    }

    pub fn delete_node(&mut self, nid: NodeID) -> Option<NodeData> {
        if !self.has_node(nid) {
            return None;
        }
        self.log_node_mutation(nid);
        // Cascade: delete every adjacent edge first so the indices stay
        // consistent.
        let outs: Vec<EdgeIdx> = self.out[nid.0 as usize].iter().copied().collect();
        for e in outs {
            self.delete_edge(e);
        }
        let ins: Vec<EdgeIdx> = self.in_[nid.0 as usize].iter().copied().collect();
        for e in ins {
            self.delete_edge(e);
        }
        let data = self.nodes[nid.0 as usize].take()?;
        self.bump_mutation_version();
        // Remove from the by_type index. Same retain rationale.
        if let Some(v) = self.by_type.get_mut(&data.type_) {
            v.retain(|n| *n != nid);
        }
        // Phase 7b: drop from any declared attr indices.
        if !self.attr_indices.is_empty() {
            self.unindex_node(nid, data.type_);
        }
        self.node_freelist.push(nid.0);
        Some(data)
    }

    pub fn set_node_attr(&mut self, nid: NodeID, key: Sym, value: Value) {
        let node_type = self.node(nid).type_;
        // Phase 7b: index maintenance. If `(type, key)` is indexed, we
        // need to remove the node from the old-value bucket before
        // overwriting the attr, then add to the new bucket.
        let indexed = self.attr_indices.contains_key(&(node_type, key));
        let old_value = if indexed {
            self.node(nid).attrs.get(&key).cloned()
        } else {
            None
        };
        self.node_mut(nid).attrs.insert(key, value.clone());
        // block 292000: log rule-effect attr writes for frontier-incremental
        // predicate retraction — gated, so default (flag off) is byte/cost-identical.
        if self.log_attr_writes {
            self.attr_write_log.push((nid, key));
        }
        if indexed {
            if let Some(ov) = old_value {
                if let Some(bucket) = self.attr_indices.get_mut(&(node_type, key)) {
                    if let Some(bm) = bucket.get_mut(&ov) {
                        bm.remove(nid.0);
                        if bm.is_empty() {
                            bucket.remove(&ov);
                        }
                    }
                }
            }
            self.attr_indices
                .entry((node_type, key))
                .or_default()
                .entry(value)
                .or_insert_with(RoaringBitmap::new)
                .insert(nid.0);
        }
    }

    /// Remove an attribute key entirely from a node (vs `set_node_attr`
    /// which writes a new value). Updates declared attr indices to
    /// drop the node from the value-bucket. Used by the rewrite-rule
    /// undo path so a rolled-back `SetAttr` on a previously-absent
    /// attr leaves the node identical to its pre-rule state.
    pub fn remove_node_attr(&mut self, nid: NodeID, key: Sym) {
        let node_type = self.node(nid).type_;
        let indexed = self.attr_indices.contains_key(&(node_type, key));
        let old = self.node_mut(nid).attrs.remove(&key);
        if indexed {
            if let Some(ov) = old {
                if let Some(bucket) = self.attr_indices.get_mut(&(node_type, key)) {
                    if let Some(bm) = bucket.get_mut(&ov) {
                        bm.remove(nid.0);
                        if bm.is_empty() {
                            bucket.remove(&ov);
                        }
                    }
                }
            }
        }
    }

    pub fn set_node_type(&mut self, nid: NodeID, new_type: Sym) {
        let old = self.node(nid).type_;
        if old == new_type {
            return;
        }
        if let Some(v) = self.by_type.get_mut(&old) {
            v.retain(|n| *n != nid);
        }
        // Phase 7b: drop from any old-type indices, then re-index under
        // the new type. The attrs are unchanged so we can re-snapshot
        // them from the (still-old-type) node before flipping.
        if !self.attr_indices.is_empty() {
            self.unindex_node(nid, old);
        }
        self.node_mut(nid).type_ = new_type;
        self.by_type.entry(new_type).or_default().push(nid);
        if !self.attr_indices.is_empty() {
            let attrs = self.node(nid).attrs.clone();
            self.index_node(nid, new_type, &attrs);
        }
    }

    // --- diagnostics ---

    pub fn node_count(&self) -> usize {
        self.nodes.iter().filter(|s| s.is_some()).count()
    }

    pub fn edge_count(&self) -> usize {
        self.edges.iter().filter(|s| s.is_some()).count()
    }

    /// Internal accessor for persistence — yields (NodeID, &NodeData)
    /// over the live slabs, skipping tombstones.
    pub fn iter_nodes(&self) -> impl Iterator<Item = (NodeID, &NodeData)> {
        self.nodes
            .iter()
            .enumerate()
            .filter_map(|(i, slot)| slot.as_ref().map(|d| (NodeID(i as u32), d)))
    }

    pub fn iter_edges(&self) -> impl Iterator<Item = (EdgeIdx, &EdgeData)> {
        self.edges
            .iter()
            .enumerate()
            .filter_map(|(i, slot)| slot.as_ref().map(|d| (EdgeIdx(i as u32), d)))
    }

    /// A hash of the graph's ENTIRE mutable state — every live node
    /// (id, type, attrs) and every live edge (src, type, tgt, attrs).
    ///
    /// WHY THIS EXISTS: `run_rules` terminates on EXACT value equality,
    /// which a float relaxation generically cannot reach — a contraction's
    /// fixed point is usually not representable in float64, so the iteration
    /// lands in a PERIOD-2 orbit between the two nearest floats and dithers
    /// there forever (measured: 4.0 ULP at connectivity 4, 1.0 ULP at 8, on
    /// a sheet settled to 1e-16). A period-2 orbit IS a fixed point of the
    /// 2-step map, and a repeated state under a DETERMINISTIC map proves the
    /// trajectory can never reach anything new. So the honest termination
    /// test is not "did the state stop changing" (unsatisfiable) but "has
    /// this exact state been seen before" — which needs EXACT equality and
    /// NO TOLERANCE, hence no epsilon and no magic number (PROTOCOL §13).
    ///
    /// ORDER-INDEPENDENCE IS LOAD-BEARING, NOT A STYLE CHOICE. `Attrs` is a
    /// `Vec` whose `remove` is a `swap_remove`, so two LOGICALLY IDENTICAL
    /// attr sets can be stored in different orders; node/edge slab order can
    /// likewise differ after freelist reuse. Hashing in iteration order would
    /// therefore hash equal states differently and MISS the cycle. Every fold
    /// below is `wrapping_add` over a per-entry hash that already includes its
    /// own key/id, so the combine is commutative and the fingerprint depends
    /// only on the state's CONTENT.
    ///
    /// A hash collision would end a run early; at 64 bits over the ~1e5
    /// states a settling loop visits, that is ~2.7e-10 by birthday bound.
    /// The property is probabilistic, and that is stated rather than hidden.
    pub fn state_fingerprint(&self) -> u64 {
        use std::hash::{Hash, Hasher};

        fn attrs_hash(attrs: &Attrs) -> u64 {
            // XOR-fold: commutative, so Vec order cannot change the result.
            let mut acc: u64 = 0;
            for (k, v) in attrs.iter() {
                let mut h = rustc_hash::FxHasher::default();
                k.hash(&mut h);
                v.hash(&mut h);
                acc ^= h.finish();
            }
            acc
        }

        let mut total: u64 = 0;
        for (nid, data) in self.iter_nodes() {
            let mut h = rustc_hash::FxHasher::default();
            0u8.hash(&mut h);
            nid.0.hash(&mut h);
            data.type_.hash(&mut h);
            attrs_hash(&data.attrs).hash(&mut h);
            total = total.wrapping_add(h.finish());
        }
        for (idx, e) in self.iter_edges() {
            let mut h = rustc_hash::FxHasher::default();
            1u8.hash(&mut h);
            e.src.0.hash(&mut h);
            e.edge_type.hash(&mut h);
            e.tgt.0.hash(&mut h);
            // Edge attrs are sparse — only hash the populated ones.
            if let Some(a) = self.edge_attrs.get(&idx) {
                attrs_hash(a).hash(&mut h);
            }
            total = total.wrapping_add(h.finish());
        }
        total
    }

    /// Restore from persistence with explicit NodeID preservation —
    /// callers must hand pre-existing ids back in monotonic order, and
    /// freed slots in between become tombstones (matches Python's
    /// `graph_from_dict` which keeps the original `_next_id` counter).
    pub fn restore_node(&mut self, nid: NodeID, type_: Sym, attrs: impl Into<Attrs>) {
        self.bump_mutation_version();
        let idx = nid.0 as usize;
        while self.nodes.len() <= idx {
            self.nodes.push(None);
            self.out.push(SmallVec::new());
            self.in_.push(SmallVec::new());
        }
        self.nodes[idx] = Some(NodeData {
            type_,
            attrs: attrs.into(),
        });
        self.by_type.entry(type_).or_default().push(nid);
        self.log_node_mutation(nid);
    }

    pub fn restore_edge(
        &mut self,
        src: NodeID,
        edge_type: Sym,
        tgt: NodeID,
        attrs: impl Into<Attrs>,
    ) {
        let _ = self.insert_edge(src, edge_type, tgt, attrs);
    }
}

impl Default for TypedGraph {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum EdgeInsertError {
    MissingSrc(NodeID),
    MissingTgt(NodeID),
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::sym::Interner;

    fn setup() -> (TypedGraph, Interner) {
        (TypedGraph::new(), Interner::new())
    }

    #[test]
    fn insert_node_and_query() {
        let (mut g, mut i) = setup();
        let alive = i.intern("AliveCell");
        let nid = g.insert_node(alive, FxHashMap::default());
        assert!(g.has_node(nid));
        assert_eq!(g.node(nid).type_, alive);
        assert_eq!(g.nodes_of_type(alive), vec![nid]);
        assert_eq!(g.node_count(), 1);
    }

    #[test]
    fn mutation_version_is_stable_on_reads_and_advances_on_writes() {
        let (mut g, mut i) = setup();
        let cell = i.intern("Cell");
        let state = i.intern("state");
        let edge = i.intern("next");
        let initial = g.mutation_version();
        let a = g.insert_node(cell, FxHashMap::default());
        let after_insert = g.mutation_version();
        assert!(after_insert > initial);
        let _ = g.node(a);
        assert_eq!(g.mutation_version(), after_insert);
        g.set_node_attr(a, state, Value::Int(1));
        let after_attr = g.mutation_version();
        assert!(after_attr > after_insert);
        let b = g.insert_node(cell, FxHashMap::default());
        g.insert_edge(a, edge, b, FxHashMap::default()).unwrap();
        assert!(g.mutation_version() > after_attr);
    }

    #[test]
    fn edges_indexed_by_type() {
        let (mut g, mut i) = setup();
        let t = i.intern("Cell");
        let adj = i.intern("adjacent_to");
        let next = i.intern("transitions_to");
        let a = g.insert_node(t, FxHashMap::default());
        let b = g.insert_node(t, FxHashMap::default());
        g.insert_edge(a, adj, b, FxHashMap::default()).unwrap();
        g.insert_edge(a, next, b, FxHashMap::default()).unwrap();
        assert_eq!(g.neighbours(a, Some(adj)), vec![b]);
        assert_eq!(g.neighbours(a, Some(next)), vec![b]);
        assert_eq!(g.neighbours(a, None).len(), 2);
        assert!(g.has_edge(a, adj, b));
        assert!(!g.has_edge(b, adj, a));
    }

    #[test]
    fn delete_node_cascades_edges() {
        let (mut g, mut i) = setup();
        let t = i.intern("X");
        let e = i.intern("e");
        let a = g.insert_node(t, FxHashMap::default());
        let b = g.insert_node(t, FxHashMap::default());
        g.insert_edge(a, e, b, FxHashMap::default()).unwrap();
        g.delete_node(a);
        assert!(!g.has_node(a));
        assert_eq!(g.edge_count(), 0);
        // b still alive
        assert!(g.has_node(b));
    }

    #[test]
    fn nodeid_recycled_after_delete() {
        let (mut g, mut i) = setup();
        let t = i.intern("X");
        let a = g.insert_node(t, FxHashMap::default());
        g.delete_node(a);
        let b = g.insert_node(t, FxHashMap::default());
        // freelist gave us back the same slot
        assert_eq!(a, b);
    }

    #[test]
    fn set_node_type_rewrites_index() {
        let (mut g, mut i) = setup();
        let alive = i.intern("Alive");
        let dead = i.intern("Dead");
        let n = g.insert_node(alive, FxHashMap::default());
        assert_eq!(g.nodes_of_type(alive), vec![n]);
        g.set_node_type(n, dead);
        assert_eq!(g.nodes_of_type(alive), vec![]);
        assert_eq!(g.nodes_of_type(dead), vec![n]);
    }

    #[test]
    fn attr_index_lookup_returns_indexed_nodes() {
        let (mut g, mut i) = setup();
        let cell = i.intern("Cell");
        let state = i.intern("state");
        let alive = i.intern("alive");
        let dead = i.intern("dead");
        // Pre-existing nodes — index back-fills them on declaration.
        let mut a_attrs = FxHashMap::default();
        a_attrs.insert(state, Value::Str(alive));
        let a = g.insert_node(cell, a_attrs);
        let mut b_attrs = FxHashMap::default();
        b_attrs.insert(state, Value::Str(dead));
        let b = g.insert_node(cell, b_attrs);
        g.declare_attr_index(cell, state);
        // New post-declaration node also gets indexed.
        let mut c_attrs = FxHashMap::default();
        c_attrs.insert(state, Value::Str(alive));
        let c = g.insert_node(cell, c_attrs);
        let mut alive_nodes = g.nodes_where(cell, state, &Value::Str(alive));
        alive_nodes.sort();
        let mut expected = vec![a, c];
        expected.sort();
        assert_eq!(alive_nodes, expected);
        assert_eq!(g.nodes_where(cell, state, &Value::Str(dead)), vec![b]);
    }

    #[test]
    fn attr_index_updated_on_set_attr() {
        let (mut g, mut i) = setup();
        let cell = i.intern("Cell");
        let state = i.intern("state");
        let alive = i.intern("alive");
        let dead = i.intern("dead");
        g.declare_attr_index(cell, state);
        let mut attrs = FxHashMap::default();
        attrs.insert(state, Value::Str(alive));
        let nid = g.insert_node(cell, attrs);
        assert_eq!(g.nodes_where(cell, state, &Value::Str(alive)), vec![nid]);
        // Flip state alive → dead; the index should re-route.
        g.set_node_attr(nid, state, Value::Str(dead));
        assert!(g.nodes_where(cell, state, &Value::Str(alive)).is_empty());
        assert_eq!(g.nodes_where(cell, state, &Value::Str(dead)), vec![nid]);
    }

    #[test]
    fn attr_index_drops_node_on_delete() {
        let (mut g, mut i) = setup();
        let cell = i.intern("Cell");
        let state = i.intern("state");
        let alive = i.intern("alive");
        g.declare_attr_index(cell, state);
        let mut attrs = FxHashMap::default();
        attrs.insert(state, Value::Str(alive));
        let nid = g.insert_node(cell, attrs);
        assert_eq!(g.nodes_where(cell, state, &Value::Str(alive)), vec![nid]);
        g.delete_node(nid);
        assert!(g.nodes_where(cell, state, &Value::Str(alive)).is_empty());
    }

    #[test]
    fn attr_index_handles_type_change() {
        let (mut g, mut i) = setup();
        let live = i.intern("LiveCell");
        let dead = i.intern("DeadCell");
        let state = i.intern("state");
        let val = i.intern("x");
        g.declare_attr_index(live, state);
        g.declare_attr_index(dead, state);
        let mut attrs = FxHashMap::default();
        attrs.insert(state, Value::Str(val));
        let nid = g.insert_node(live, attrs);
        assert_eq!(g.nodes_where(live, state, &Value::Str(val)), vec![nid]);
        g.set_node_type(nid, dead);
        assert!(g.nodes_where(live, state, &Value::Str(val)).is_empty());
        assert_eq!(g.nodes_where(dead, state, &Value::Str(val)), vec![nid]);
    }

    #[test]
    fn attr_index_returns_roaring_bitmap() {
        let (mut g, mut i) = setup();
        let cell = i.intern("Cell");
        let state = i.intern("state");
        let alive = i.intern("alive");
        let dead = i.intern("dead");
        g.declare_attr_index(cell, state);
        // 100 alive cells, 50 dead.
        for _ in 0..100 {
            let mut attrs: FxHashMap<Sym, Value> = Default::default();
            attrs.insert(state, Value::Str(alive));
            g.insert_node(cell, attrs);
        }
        for _ in 0..50 {
            let mut attrs: FxHashMap<Sym, Value> = Default::default();
            attrs.insert(state, Value::Str(dead));
            g.insert_node(cell, attrs);
        }
        let bm_alive = g
            .nodes_where_bitmap(cell, state, &Value::Str(alive))
            .unwrap();
        let bm_dead = g
            .nodes_where_bitmap(cell, state, &Value::Str(dead))
            .unwrap();
        assert_eq!(bm_alive.len(), 100);
        assert_eq!(bm_dead.len(), 50);
        // No NodeID is both alive and dead.
        assert!((bm_alive & bm_dead).is_empty());
    }

    #[test]
    fn intersect_attr_indexes_finds_common_nodes() {
        // Two attrs, two indexes, intersection finds nodes matching both.
        let (mut g, mut i) = setup();
        let cell = i.intern("Cell");
        let state = i.intern("state");
        let region = i.intern("region");
        let alive = i.intern("alive");
        let dead = i.intern("dead");
        let r1 = i.intern("r1");
        let r2 = i.intern("r2");
        g.declare_attr_index(cell, state);
        g.declare_attr_index(cell, region);
        // 4 cells: (alive,r1), (alive,r2), (dead,r1), (dead,r2)
        let mk = |s, r, g: &mut TypedGraph| {
            let mut a: FxHashMap<Sym, Value> = Default::default();
            a.insert(state, Value::Str(s));
            a.insert(region, Value::Str(r));
            g.insert_node(cell, a)
        };
        let ar1 = mk(alive, r1, &mut g);
        let _ar2 = mk(alive, r2, &mut g);
        let _dr1 = mk(dead, r1, &mut g);
        let _dr2 = mk(dead, r2, &mut g);
        // Query: alive AND r1 → should be just ar1.
        let result = g
            .intersect_attr_indexes(&[
                (cell, state, &Value::Str(alive)),
                (cell, region, &Value::Str(r1)),
            ])
            .unwrap();
        assert_eq!(result.len(), 1);
        assert!(result.contains(ar1.0));
    }

    #[test]
    fn in_neighbours_finds_predecessors() {
        let (mut g, mut i) = setup();
        let t = i.intern("X");
        let e = i.intern("points_at");
        let a = g.insert_node(t, FxHashMap::default());
        let b = g.insert_node(t, FxHashMap::default());
        let c = g.insert_node(t, FxHashMap::default());
        g.insert_edge(a, e, c, FxHashMap::default()).unwrap();
        g.insert_edge(b, e, c, FxHashMap::default()).unwrap();
        let mut preds = g.in_neighbours(c, Some(e));
        preds.sort();
        assert_eq!(preds, vec![a, b]);
    }

    /// Layout measurement — run with `cargo test --lib graph::tests::measure_layout -- --nocapture`.
    /// Prints sizeof for every relevant type + counts on representative
    /// loaded seeds. Numbers feed the memory-efficiency decision.
    #[test]
    fn measure_layout() {
        use crate::sym::Sym;
        use crate::value::{SurfaceKind, Value};
        use std::mem::size_of;

        eprintln!("\n=== sizeof (bytes) ===");
        eprintln!("Sym                  {:>4}", size_of::<Sym>());
        eprintln!("NodeID               {:>4}", size_of::<NodeID>());
        eprintln!("EdgeIdx              {:>4}", size_of::<EdgeIdx>());
        eprintln!("EdgeKey              {:>4}", size_of::<EdgeKey>());
        eprintln!("SurfaceKind          {:>4}", size_of::<SurfaceKind>());
        eprintln!("Value                {:>4}", size_of::<Value>());
        eprintln!("Option<Value>        {:>4}", size_of::<Option<Value>>());
        eprintln!("(Sym, Value)         {:>4}", size_of::<(Sym, Value)>());
        eprintln!("NodeData             {:>4}", size_of::<NodeData>());
        eprintln!("Option<NodeData>     {:>4}", size_of::<Option<NodeData>>());
        eprintln!("EdgeData             {:>4}", size_of::<EdgeData>());
        eprintln!("Option<EdgeData>     {:>4}", size_of::<Option<EdgeData>>());
        eprintln!(
            "FxHashMap<Sym,Value> {:>4} (empty header)",
            size_of::<FxHashMap<Sym, Value>>()
        );
        eprintln!(
            "SmallVec<[EdgeIdx;8]>{:>4}",
            size_of::<SmallVec<[EdgeIdx; 4]>>()
        );
        eprintln!(
            "SmallVec<[EdgeIdx;4]>{:>4}",
            size_of::<SmallVec<[EdgeIdx; 4]>>()
        );
        eprintln!(
            "SmallVec<[NodeID;4]> {:>4}",
            size_of::<SmallVec<[NodeID; 4]>>()
        );

        // Load relations.json — the biggest seed at 88K.
        let path = concat!(env!("CARGO_MANIFEST_DIR"), "/../../seeds/relations.json");
        let Ok(text) = std::fs::read_to_string(path) else {
            eprintln!("\n(could not read {}; skipping seed measurement)", path);
            return;
        };
        let json: serde_json::Value = match serde_json::from_str(&text) {
            Ok(v) => v,
            Err(e) => {
                eprintln!("(JSON parse failed: {}; skipping)", e);
                return;
            }
        };
        // Minimal seed-manifest loader (matches py.rs load_seed_manifest).
        let mut interner = crate::sym::Interner::new();
        let mut g = TypedGraph::new();
        let mut local_to_global: FxHashMap<u64, NodeID> = Default::default();
        let m = json.as_object().unwrap();
        if let Some(arr) = m.get("nodes").and_then(|n| n.as_array()) {
            for n in arr {
                let local_id = n.get("local_id").and_then(|v| v.as_u64()).unwrap();
                let type_str = n.get("type").and_then(|v| v.as_str()).unwrap();
                let type_sym = interner.intern(type_str);
                let mut attrs: FxHashMap<Sym, Value> = Default::default();
                if let Some(obj) = n.get("attrs").and_then(|a| a.as_object()) {
                    for (k, av) in obj {
                        let key = interner.intern(k);
                        attrs.insert(key, crate::persist::decode_value(av, &mut interner));
                    }
                }
                let nid = g.insert_node(type_sym, attrs);
                local_to_global.insert(local_id, nid);
            }
        }
        if let Some(arr) = m.get("edges").and_then(|e| e.as_array()) {
            for e in arr {
                let resolve = |v: &serde_json::Value| -> Option<NodeID> {
                    if let Some(obj) = v.as_object() {
                        if let Some(lid) = obj.get("local_id").and_then(|x| x.as_u64()) {
                            return local_to_global.get(&lid).copied();
                        }
                    }
                    None
                };
                let src = match e.get("src").and_then(resolve) {
                    Some(s) => s,
                    None => continue,
                };
                let tgt = match e.get("tgt").and_then(resolve) {
                    Some(t) => t,
                    None => continue,
                };
                let et_str = e.get("type").and_then(|v| v.as_str()).unwrap_or("?");
                let et_sym = interner.intern(et_str);
                let mut attrs: FxHashMap<Sym, Value> = Default::default();
                if let Some(obj) = e.get("attrs").and_then(|a| a.as_object()) {
                    for (k, av) in obj {
                        let key = interner.intern(k);
                        attrs.insert(key, crate::persist::decode_value(av, &mut interner));
                    }
                }
                let _ = g.insert_edge(src, et_sym, tgt, attrs);
            }
        }

        eprintln!("\n=== relations.json loaded ===");
        eprintln!("nodes (slab len)   {}", g.nodes.len());
        let live_nodes = g.nodes.iter().filter(|s| s.is_some()).count();
        eprintln!("nodes (live)       {}", live_nodes);
        eprintln!("edges (slab len)   {}", g.edges.len());
        let live_edges = g.edges.iter().filter(|s| s.is_some()).count();
        eprintln!("edges (live)       {}", live_edges);

        // Attr-count distribution + Value-variant distribution on nodes.
        let mut node_attr_hist: std::collections::BTreeMap<usize, usize> = Default::default();
        let mut total_node_attrs: usize = 0;
        let mut value_variants: std::collections::BTreeMap<&'static str, usize> =
            Default::default();
        let mut str_byte_total: usize = 0;
        for slot in &g.nodes {
            if let Some(nd) = slot {
                let n = nd.attrs.len();
                *node_attr_hist.entry(n).or_default() += 1;
                total_node_attrs += n;
                for v in nd.attrs.values() {
                    let tag = match v {
                        Value::None => "None",
                        Value::Bool(_) => "Bool",
                        Value::Int(_) => "Int",
                        Value::Float(_) => "Float",
                        Value::Str(s) => {
                            str_byte_total += interner.resolve(*s).len();
                            "Str"
                        }
                        Value::Node(_) => "Node",
                        Value::Tuple(_) | Value::List(_) => "Tuple",
                        Value::Set(_) => "Set",
                        Value::FrozenSet(_) => "FrozenSet",
                        Value::Dict(_) => "Dict",
                        Value::Surface(_, _) => "Surface",
                        Value::Rational(_, _) => "Rational",
                    };
                    *value_variants.entry(tag).or_default() += 1;
                }
            }
        }
        let mut edge_attr_hist: std::collections::BTreeMap<usize, usize> = Default::default();
        let mut total_edge_attrs: usize = 0;
        for (i, slot) in g.edges.iter().enumerate() {
            if slot.is_some() {
                let n = g.edge_attrs(EdgeIdx(i as u32)).len();
                *edge_attr_hist.entry(n).or_default() += 1;
                total_edge_attrs += n;
            }
        }
        eprintln!("\n=== node attr-count histogram ===");
        for (k, v) in &node_attr_hist {
            eprintln!("  {:>2} attrs: {:>5} nodes", k, v);
        }
        eprintln!("total node attrs   {}", total_node_attrs);
        eprintln!(
            "avg attrs/node     {:.2}",
            if live_nodes > 0 {
                total_node_attrs as f64 / live_nodes as f64
            } else {
                0.0
            }
        );
        eprintln!("\n=== Value-variant distribution (node attrs only) ===");
        for (tag, n) in &value_variants {
            eprintln!("  {:>10}: {:>5}", tag, n);
        }
        eprintln!(
            "Str payload bytes (sum of interned lengths): {}",
            str_byte_total
        );
        eprintln!("\n=== edge attr-count histogram ===");
        for (k, v) in &edge_attr_hist {
            eprintln!("  {:>2} attrs: {:>5} edges", k, v);
        }
        eprintln!("total edge attrs   {}", total_edge_attrs);
        eprintln!(
            "avg attrs/edge     {:.2}",
            if live_edges > 0 {
                total_edge_attrs as f64 / live_edges as f64
            } else {
                0.0
            }
        );

        // Adjacency stats.
        let mut out_inline: usize = 0;
        let mut out_spilled: usize = 0;
        let mut total_out_edges: usize = 0;
        for sv in &g.out {
            total_out_edges += sv.len();
            if sv.spilled() {
                out_spilled += 1;
            } else {
                out_inline += 1;
            }
        }
        eprintln!("\n=== adjacency ===");
        eprintln!(
            "out lists: {} (inline) + {} (heap)",
            out_inline, out_spilled
        );
        eprintln!("total out edges across lists: {}", total_out_edges);

        // Memory estimate.
        let node_slab_bytes = g.nodes.len() * size_of::<Option<NodeData>>();
        let edge_slab_bytes = g.edges.len() * size_of::<Option<EdgeData>>();
        // hashmap overhead estimate: ~22 bytes per entry (control byte +
        // bucket slot, ~0.75 load factor → 1.33 slots per entry).
        let attr_heap_estimate =
            (total_node_attrs + total_edge_attrs) * (size_of::<(Sym, Value)>() + 8);
        // out + in_ contiguous Vec<SmallVec> — only count spilled lists'
        // heap (inline lists are already in node_slab_bytes-adjacent
        // memory via the Vec itself).
        let out_vec_bytes = g.out.len() * size_of::<SmallVec<[EdgeIdx; 4]>>();
        let in_vec_bytes = g.in_.len() * size_of::<SmallVec<[EdgeIdx; 4]>>();
        eprintln!("\n=== memory estimate ===");
        eprintln!("node slab           {:>10} bytes", node_slab_bytes);
        eprintln!("edge slab           {:>10} bytes", edge_slab_bytes);
        eprintln!("attr heap (est)     {:>10} bytes", attr_heap_estimate);
        eprintln!("out Vec<SmallVec>   {:>10} bytes", out_vec_bytes);
        eprintln!("in_ Vec<SmallVec>   {:>10} bytes", in_vec_bytes);
        eprintln!("------");
        let total =
            node_slab_bytes + edge_slab_bytes + attr_heap_estimate + out_vec_bytes + in_vec_bytes;
        eprintln!(
            "approx total        {:>10} bytes  ({:.1} KiB)",
            total,
            total as f64 / 1024.0
        );

        // Per-node + per-edge ratio.
        if live_nodes > 0 {
            eprintln!(
                "\nbytes per live node ({} live, total est): {:.1}",
                live_nodes,
                total as f64 / live_nodes as f64
            );
        }
        eprintln!();

        // --- Synthetic edge-heavy graph: 10K Conway-style cells, 4 edges each ---
        eprintln!("\n=== synthetic Conway 100x100 grid ===");
        let mut g2 = TypedGraph::new();
        let mut ir2 = crate::sym::Interner::new();
        let cell_ty = ir2.intern("Cell");
        let alive_ty = ir2.intern("AliveCell");
        let adj = ir2.intern("adjacent_to");
        let state_key = ir2.intern("state");
        let alive_val = ir2.intern("alive");
        let n = 100usize;
        let mut grid: Vec<Vec<NodeID>> = Vec::with_capacity(n);
        for i in 0..n {
            let mut row = Vec::with_capacity(n);
            for _ in 0..n {
                let mut attrs: FxHashMap<Sym, Value> = Default::default();
                attrs.insert(state_key, Value::Str(alive_val));
                let ty = if i % 2 == 0 { alive_ty } else { cell_ty };
                row.push(g2.insert_node(ty, attrs));
            }
            grid.push(row);
        }
        // 4-neighbour edges (toroidal).
        for i in 0..n {
            for j in 0..n {
                let me = grid[i][j];
                for (di, dj) in [(-1i32, 0), (1, 0), (0, -1), (0, 1)] {
                    let ni = ((i as i32 + di).rem_euclid(n as i32)) as usize;
                    let nj = ((j as i32 + dj).rem_euclid(n as i32)) as usize;
                    let _ = g2.insert_edge(me, adj, grid[ni][nj], FxHashMap::default());
                }
            }
        }
        let nodes2 = g2.nodes.iter().filter(|s| s.is_some()).count();
        let edges2 = g2.edges.iter().filter(|s| s.is_some()).count();
        let mut out_spilled2 = 0;
        let mut out_max2 = 0;
        for sv in &g2.out {
            if sv.spilled() {
                out_spilled2 += 1;
            }
            out_max2 = out_max2.max(sv.len());
        }
        let node_slab2 = g2.nodes.len() * size_of::<Option<NodeData>>();
        let edge_slab2 = g2.edges.len() * size_of::<Option<EdgeData>>();
        let total_attrs2 = nodes2; // 1 attr per node, 0 per edge
        let attr_heap2 = total_attrs2 * (size_of::<(Sym, Value)>() + 8);
        let out_vec2 = g2.out.len() * size_of::<SmallVec<[EdgeIdx; 4]>>();
        let in_vec2 = g2.in_.len() * size_of::<SmallVec<[EdgeIdx; 4]>>();
        let hashmap_overhead2 = (g2.out_by_type.len() + g2.in_by_type.len())
            * (size_of::<(NodeID, Sym)>() + size_of::<SmallVec<[EdgeIdx; 4]>>() + 16);
        let total2 = node_slab2 + edge_slab2 + attr_heap2 + out_vec2 + in_vec2 + hashmap_overhead2;
        eprintln!("nodes (live)        {}", nodes2);
        eprintln!("edges (live)        {}", edges2);
        eprintln!("out spilled         {} / {}", out_spilled2, g2.out.len());
        eprintln!("out max len         {}", out_max2);
        eprintln!("node slab           {:>10} bytes", node_slab2);
        eprintln!("edge slab           {:>10} bytes", edge_slab2);
        eprintln!("attr heap (est)     {:>10} bytes", attr_heap2);
        eprintln!("out Vec<SmallVec>   {:>10} bytes", out_vec2);
        eprintln!("in_ Vec<SmallVec>   {:>10} bytes", in_vec2);
        eprintln!(
            "out/in_by_type maps {:>10} bytes (estimate)",
            hashmap_overhead2
        );
        eprintln!(
            "approx total        {:>10} bytes  ({:.1} KiB, {:.2} MiB)",
            total2,
            total2 as f64 / 1024.0,
            total2 as f64 / (1024.0 * 1024.0)
        );
        eprintln!("bytes per live node {:.1}", total2 as f64 / nodes2 as f64);
        eprintln!("bytes per live edge {:.1}", total2 as f64 / edges2 as f64);
        eprintln!();
    }
}
