I've now read every real file the change touches and traced the actual execution path. One grounding correction up front that shapes the whole design, then the exact code.

---

## What I found (and one honest correction to the brief)

The named perception rules (`cc_materialise`, `cc_region_bounds`, `mark_floor_as_location`, `max_region_count`, `region_correspondence`, `avatar_vote`, `avatar_confirm`) are **JSON Rule-node seeds**. The live `tick()` (py.rs:2390) fires them through **`graph_rules::run_graph_rules` → `rewrite::run_rules` (the free fn at rewrite.rs:1007)** — re-parsing every Rule node into a fresh arena each tick — *and then* `Substrate::run_rules` for `add_rule`-installed rules (prose-compiler output).

So slice (b) must land in **both** paths, sharing one `RewriteRule` + one `batch_apply_rule`. The free-fn path is where the perception O(N²) actually lives: `rewrite::run_rules` applies **one** progressing binding per whole pass (collect-all → apply-first-progressing → `break`), so materialising N cells costs N passes × re-collect = O(N²). `batch_apply` collapses that to O(N).

**Honest finding from deriving the read/write sets:** `avatar_vote` reads `avatar_votes` on `a` and **writes `avatar_votes` on `b`** — a propagation/accumulation chain (write feeds the same-attr read). It is **not** batch-safe and must stay on the incremental path. I've excluded it from deliverable 6 and flag why. The other six are safe (writes never feed their own binding-determining reads).

A second consequence: cc_materialise/cc_region_bounds can't be *auto-proven* batch-safe, because the read/write disjointness test is attr-key-only (no per-var node types in a rule) and `cc_label`/`frame` appear as both a read (on `cell`/`game`) and a write (on the new `Region`). So `batch:true` is an **author assertion** (authoritative), and the derived `batch_safe` is a conservative auto-enable used only when the attr is absent. The migrated bench is the guard.

---

## Deliverable 1 — Struct fields (`runners/dsl/src/rewrite.rs`)

Replace the struct at rewrite.rs:174–180 and add the `RuleKey` token type just above it:

```rust
/// A token in a rule's read/write access set. A small `Copy` enum so
/// membership / intersection are O(1) hashes and the sets live inline.
/// All three carry an interned `Sym`:
///   - `Attr(k)` — reads or writes node attr `k`.
///   - `Type(t)` — reads nodes of type `t` (TypeOf via NodesOfType /
///                 NodesWhere), or an effect mints a node of type `t`.
///   - `Edge(e)` — reads or writes edges of type `e`.
/// Imprecise reads (AttrByName / Holds / any-type Neighbours / TypeOf /
/// EvalSubgraph / UseTool) set the rule's `reads_any` flag instead;
/// imprecise writes (DelNode / ReplaceValue / DefineConcept) set
/// `writes_any`. Those flags are the conservative escape hatch — a rule
/// that sets one is treated like the old "has_where ⇒ always dirty" path.
#[derive(Copy, Clone, PartialEq, Eq, Hash, Debug)]
pub enum RuleKey {
    Attr(Sym),
    Type(Sym),
    Edge(Sym),
}

/// One rewrite rule. Has a name for diagnostics, a pattern (match
/// edges + optional where-clause Term), and an ordered effect list.
#[derive(Clone, Debug, Default)]
pub struct RewriteRule {
    pub name: Sym,
    pub match_edges: Vec<MatchEdge>,
    pub where_: Option<TermIdx>,
    pub effects: Vec<Effect>,

    // --- access analysis (slice b: batch-apply + write-set dirtying) ---
    /// Over-approx superset of the graph keys this rule READS to decide
    /// its bindings (match edge types, where-clause Attr/Type/Edge,
    /// computed effect-arg reads). Used by `dirty_by_writeset` and the
    /// precise `mark_attr_mutation` — over-approx is correct for dirtying
    /// (dirties a superset, never misses).
    pub read_set: rustc_hash::FxHashSet<RuleKey>,
    /// Over-approx superset of the graph keys this rule WRITES.
    pub write_set: rustc_hash::FxHashSet<RuleKey>,
    /// Conservative "reads something opaque" — forces always-dirty.
    pub reads_any: bool,
    /// Conservative "writes something opaque" (DelNode/ReplaceValue/
    /// DefineConcept) — forces a blanket dirty when this rule fires.
    pub writes_any: bool,
    /// THE gate read by both run-rules paths. When true, the runner uses
    /// `batch_apply_rule` (apply every binding this pass, record_undo=false)
    /// instead of one-progressing-binding-per-pass. Set from the rule
    /// node's `batch` attr if present, else from the derived `batch_safe`.
    pub batch: bool,
    /// Derived conservative proof that snapshot-batch == one-per-pass
    /// (no order-sensitive effect AND read_set ∩ write_set == ∅ AND no
    /// reads_any/writes_any). Advisory: auto-enables `batch` when the
    /// node carries no explicit `batch` attr.
    pub batch_safe: bool,
    /// Optional type-indexed driver: when set, `batch_apply_rule`
    /// enumerates `graph.nodes_of_type(match_type)` bound to the (single)
    /// match-edge's tgt_var instead of scanning edges-by-type. Falls back
    /// to the matcher for multi-edge rules. Read from the node's
    /// `match_type` attr.
    pub match_type: Option<Sym>,
}
```

*Change:* adds 7 metadata fields + a `RuleKey` token enum; derives `Default` so every existing `RewriteRule { … }` literal needs only `, ..Default::default()` appended. **Match/where/effects semantics are untouched** — the matcher and `apply_rule_full` never read the new fields.

**Mechanical follow-up the driver must apply:** append `, ..Default::default()` to the 4-field `RewriteRule { name, match_edges, where_, effects }` literals at these sites (from grep): rewrite.rs:1083/1107/1137/1160/1194/1247/1365/1409/1444/1484/1522/1552/1591; shape.rs:822/838; substrate.rs:1164/1523/1606/1780/1788/1859/1883/1954/2079/2098/2120/2134/2260; l2_jit_integration.rs:171; full_stack_integration.rs:307; py.rs:6578. (graph_rules.rs:336 is rewritten in Deliverable 2.) The substrate.rs:1164 internal `sub_rule` is matched-only, so `..Default::default()` is correct there.

---

## Deliverable 2 — Derivation + call sites

### 2a. Expose the existing child-walker (`runners/dsl/src/term.rs:4269`)

```rust
/// Yield all child TermIdx referenced by a node — used by `free_vars`
/// for generic recursion across non-binder Terms, and by rewrite.rs's
/// access analysis for the generic fall-through case.
pub(crate) fn children(node: &TermNode) -> SmallVec<[TermIdx; 8]> {
```

*Change:* `fn children` → `pub(crate) fn children`. Nothing else in the body changes.

### 2b. The derivation (`runners/dsl/src/rewrite.rs`)

Add this `impl` block right after the struct, and the two free walk helpers below it:

```rust
impl RewriteRule {
    /// Compute `read_set` / `write_set` / `reads_any` / `writes_any` /
    /// `batch_safe` from this rule's own match_edges, where_, and effects.
    /// Idempotent; call after the rule's edges/where/effects are final
    /// (after `reorder_match_edges`). Does NOT set `batch` — the caller
    /// applies the explicit-attr-else-batch_safe policy so the author's
    /// `batch:true` stays authoritative.
    pub fn derive_access(&mut self, arena: &TermArena) {
        self.read_set.clear();
        self.write_set.clear();
        self.reads_any = false;
        self.writes_any = false;

        // (1) match edges are edge-type reads.
        for me in &self.match_edges {
            self.read_set.insert(RuleKey::Edge(me.edge_type));
        }
        // (2) where-clause reads.
        if let Some(w) = self.where_ {
            collect_term_reads(arena, w, &mut self.read_set, &mut self.reads_any);
        }
        // (3) effect reads (computed args) + writes.
        // NB: collect into locals first to avoid double &mut self borrow.
        let mut reads = std::mem::take(&mut self.read_set);
        let mut writes = std::mem::take(&mut self.write_set);
        let mut reads_any = self.reads_any;
        let mut writes_any = self.writes_any;
        for eff in &self.effects {
            collect_effect_access(
                eff, arena, &mut reads, &mut writes, &mut reads_any, &mut writes_any,
            );
        }
        self.read_set = reads;
        self.write_set = writes;
        self.reads_any = reads_any;
        self.writes_any = writes_any;

        // (4) batch_safe = order-insensitive effects only AND the rule's
        // binding-determining reads are disjoint from its writes AND no
        // opaque read/write. AddEdge/AddNode(IfAbsent) are idempotent +
        // convergent, so they're admissible here; DelEdge/DelNode/
        // ReplaceValue/DefineConcept are not.
        let order_safe = self.effects.iter().all(|e| matches!(
            e,
            Effect::AddEdge { .. }
            | Effect::AddNode { .. }
            | Effect::AddNodeIfAbsent { .. }
            | Effect::SetAttr { .. }
            | Effect::SetAttrIfDifferent { .. }
        ));
        self.batch_safe = order_safe
            && !self.reads_any
            && !self.writes_any
            && self.read_set.is_disjoint(&self.write_set);
    }
}

/// Walk a where-clause / effect-arg Term, collecting graph reads.
/// Special-cases the variants carrying a graph Sym (Attr/Type/Edge);
/// opaque variants set `reads_any`; everything else recurses via the
/// shared `term::children` fall-through (which reaches their Attr
/// subterms — Filter/Sum/MinOver/Count/IfThenElse/arith/cmp/etc.).
fn collect_term_reads(
    arena: &TermArena,
    idx: TermIdx,
    reads: &mut rustc_hash::FxHashSet<RuleKey>,
    reads_any: &mut bool,
) {
    use crate::term::TermNode as T;
    match arena.get(idx) {
        T::Attr { node, key } => {
            reads.insert(RuleKey::Attr(*key));
            collect_term_reads(arena, *node, reads, reads_any);
        }
        T::EdgeAttr { edge, key } => {
            reads.insert(RuleKey::Attr(*key)); // over-approx: edge-attr key
            collect_term_reads(arena, *edge, reads, reads_any);
        }
        T::NodesOfType { node_type } => {
            reads.insert(RuleKey::Type(*node_type));
        }
        T::NodesWhere { node_type, attr_key, value } => {
            reads.insert(RuleKey::Type(*node_type));
            reads.insert(RuleKey::Attr(*attr_key));
            collect_term_reads(arena, *value, reads, reads_any);
        }
        T::Neighbours { node, edge_type, any_type }
        | T::InNeighbours { node, edge_type, any_type } => {
            if *any_type { *reads_any = true; }
            else { reads.insert(RuleKey::Edge(*edge_type)); }
            collect_term_reads(arena, *node, reads, reads_any);
        }
        T::MapNeighbours { source, edge_type, any_type } => {
            if *any_type { *reads_any = true; }
            else { reads.insert(RuleKey::Edge(*edge_type)); }
            collect_term_reads(arena, *source, reads, reads_any);
        }
        T::Edges { node, edge_type, any_type } => {
            if *any_type { *reads_any = true; }
            else { reads.insert(RuleKey::Edge(*edge_type)); }
            collect_term_reads(arena, *node, reads, reads_any);
        }
        // Opaque reads — can't pin a key statically. Force always-dirty.
        T::TypeOf { node } => {
            *reads_any = true;
            collect_term_reads(arena, *node, reads, reads_any);
        }
        T::Holds { node, node2, .. } => {
            *reads_any = true;
            if let Some(n) = node { collect_term_reads(arena, *n, reads, reads_any); }
            if let Some(n) = node2 { collect_term_reads(arena, *n, reads, reads_any); }
        }
        T::EvalSubgraph { node } => {
            *reads_any = true;
            collect_term_reads(arena, *node, reads, reads_any);
        }
        T::AttrByName { node, name } => {
            *reads_any = true; // dynamic attr key
            collect_term_reads(arena, *node, reads, reads_any);
            collect_term_reads(arena, *name, reads, reads_any);
        }
        T::UseTool { args, .. } => {
            *reads_any = true; // tool boundary — opaque
            for a in args { collect_term_reads(arena, *a, reads, reads_any); }
        }
        // Generic: recurse children (covers Lit/Var leaves, all
        // arithmetic / comparison / boolean / Filter / Sum / MinOver /
        // MaxOver / Count / Fold / IfThenElse / Let / MkDict / etc.).
        other => {
            for c in crate::term::children(other) {
                collect_term_reads(arena, c, reads, reads_any);
            }
        }
    }
}

/// Collect one effect's writes (+ its computed-arg reads).
fn collect_effect_access(
    eff: &Effect,
    arena: &TermArena,
    reads: &mut rustc_hash::FxHashSet<RuleKey>,
    writes: &mut rustc_hash::FxHashSet<RuleKey>,
    reads_any: &mut bool,
    writes_any: &mut bool,
) {
    let mut read_arg = |a: &EffectArg, r: &mut rustc_hash::FxHashSet<RuleKey>, ra: &mut bool| {
        if let EffectArg::Computed(idx) = a {
            collect_term_reads(arena, *idx, r, ra);
        }
    };
    match eff {
        Effect::AddEdge { edge_type, attrs, .. } => {
            writes.insert(RuleKey::Edge(*edge_type));
            for (_, a) in attrs { read_arg(a, reads, reads_any); }
        }
        Effect::DelEdge { edge_type, .. } => {
            writes.insert(RuleKey::Edge(*edge_type));
        }
        Effect::AddNode { type_, attrs, .. } => {
            writes.insert(RuleKey::Type(*type_));
            for (k, a) in attrs {
                writes.insert(RuleKey::Attr(*k));
                read_arg(a, reads, reads_any);
            }
        }
        Effect::AddNodeIfAbsent { type_, attrs, .. } => {
            writes.insert(RuleKey::Type(*type_));
            reads.insert(RuleKey::Type(*type_)); // dedup scan reads the type
            for (k, a) in attrs {
                writes.insert(RuleKey::Attr(*k));
                read_arg(a, reads, reads_any);
            }
        }
        Effect::SetAttr { key, value, .. }
        | Effect::SetAttrIfDifferent { key, value, .. } => {
            writes.insert(RuleKey::Attr(*key));
            read_arg(value, reads, reads_any);
        }
        // Order-sensitive / opaque writes — blanket on fire.
        Effect::DelNode { .. } | Effect::ReplaceValue { .. } => {
            *writes_any = true;
        }
        Effect::DefineConcept { name, term } => {
            *writes_any = true; // changes concept resolution (Holds)
            read_arg(name, reads, reads_any);
            read_arg(term, reads, reads_any);
        }
    }
}
```

*Change:* pure analysis, no graph mutation. Over-approximates reads/writes; sets `batch_safe` only when provably order-insensitive.

### 2c. Call site — Rule-node loader (`runners/dsl/src/graph_rules.rs:306`)

`rule_from_node` is the hot path (re-run each tick). Read the three new attrs and derive. Replace the tail of `rule_from_node` (from the `Some(RewriteRule { … })` at line 336):

```rust
    let match_edges = parse_match_edges(&match_v, interner)?;
    let where_ = parse_where(&where_v, arena, interner)?;
    let effects = parse_effects(&effect_v, arena, interner)?;

    // slice (b): read the optional batch / match_type attrs off the node.
    let batch_sym = interner.intern("batch");
    let match_type_sym_key = interner.intern("match_type");
    let explicit_batch: Option<bool> = match attrs.get(&batch_sym) {
        Some(Value::Bool(b)) => Some(*b),
        Some(Value::Float(f)) => Some(*f != 0.0),
        Some(Value::Int(n)) => Some(*n != 0),
        _ => None,
    };
    let match_type: Option<Sym> = attrs
        .get(&match_type_sym_key)
        .and_then(|v| if let Value::Str(s) = v { Some(*s) } else { None });

    let mut rule = RewriteRule {
        name: name_sym,
        match_edges,
        where_,
        effects,
        match_type,
        ..Default::default()
    };
    rule.derive_access(arena);
    // Explicit author assertion wins; else auto-enable on the proof.
    rule.batch = explicit_batch.unwrap_or(rule.batch_safe);
    Some(rule)
}
```

*Change:* parses `batch` (bool/0-1) + `match_type` (type string), derives access sets, applies the explicit-else-derived `batch` policy. (Optional manual `reads`/`writes` attr union is a straightforward extension on the same `attrs.get` pattern if a future rule needs it; none of the seven do.)

### 2d. Call site — installed rules (`runners/dsl/src/substrate.rs:968` `add_rule`)

After the reorder (line 979), before computing the legacy `rule_edge_type_deps`, derive the access sets:

```rust
        rule.match_edges = crate::rewrite::reorder_match_edges(
            &rule.match_edges,
            |et| g.edges_by_type(et).len(),
        );
        // slice (b): derive precise read/write sets used by
        // dirty_by_writeset + mark_attr_mutation. `batch` is honoured as
        // set by the caller (add_rule clients may pre-set it); auto-enable
        // only when the caller left it false AND the proof holds.
        rule.derive_access(&self.terms);
        if !rule.batch { rule.batch = rule.batch_safe; }
```

*Change:* installed rules get the same analysis; the existing `rule_edge_type_deps` / `rule_has_where` push lines below stay (they remain a valid coarse fallback and keep the legacy fast-exit working).

---

## Deliverable 3 — `batch_apply`

### 3a. Free function (`runners/dsl/src/rewrite.rs`) — shared by both run-rules paths

Add after `run_rules` (rewrite.rs:1063):

```rust
/// Apply EVERY currently-matching binding of one batch-safe rule in a
/// single pass, with `record_undo = false` — no clone, no undo vec, no
/// per-binding probe-then-rollback. Returns whether any binding was
/// not-already-satisfied (SetAttrIfDifferent / AddNodeIfAbsent / AddEdge
/// pre-exists semantics drive `progressed`, so a settled rule returns
/// false and the outer fixpoint exits).
///
/// Correctness contract: the caller guarantees `rule.batch` (the author's
/// assertion, or the derived `batch_safe` proof). Bindings are snapshotted
/// BEFORE any effect fires, so the rule's own writes don't grow or shrink
/// this pass's binding set — exactly the property batch-safety asserts.
/// add_node_if_absent's in-pass dedup still works because effects hit the
/// LIVE graph in binding order (binding 2 sees binding 1's minted node).
pub fn batch_apply_rule(
    rule: &RewriteRule,
    arena: &mut TermArena,
    graph: &mut TypedGraph,
    interner: &mut Interner,
    mut concepts: Option<&mut ConceptResolver>,
    mut cache: Option<&mut crate::term::EvalCache>,
    where_jit: Option<&crate::jit::CompiledWhere>,
) -> bool {
    use rustc_hash::FxHashSet;

    // 1) Snapshot every binding once (apply mutates the graph, so we must
    //    not be mid-iteration over edges/nodes when effects fire).
    let mut bindings: Vec<Binding> = Vec::new();
    match (rule.match_type, rule.match_edges.len()) {
        // Type-indexed driver: bind the single match-edge's tgt_var to
        // each node of `match_type`, resolve the rest via the matcher.
        // Cheap early-out when the type is empty.
        (Some(mt), 1) => {
            let tgt_var = rule.match_edges[0].tgt_var;
            for node in graph.nodes_of_type(mt) {
                let mut initial: Binding = FxHashMap::default();
                initial.insert(tgt_var, node);
                match_rule_each_with_initial(
                    rule, &initial, arena, graph, interner,
                    concepts.as_deref(), cache.as_deref_mut(), where_jit,
                    |b| { bindings.push(b.clone()); true },
                );
            }
        }
        // Empty type ⇒ nothing to do.
        (Some(mt), _) if graph.nodes_of_type(mt).is_empty() => {}
        // No index (or multi-edge): the standard matcher, which already
        // drives the both-unbound first edge off `edges_by_type`.
        _ => {
            match_rule_each(
                rule, arena, graph, interner,
                concepts.as_deref(), cache.as_deref_mut(), where_jit,
                |b| { bindings.push(b.clone()); true },
            );
        }
    }

    // 2) Apply each distinct binding exactly once, no undo bookkeeping.
    let mut seen: FxHashSet<smallvec::SmallVec<[(Sym, NodeID); 8]>> = Default::default();
    let mut progressed_any = false;
    for b in bindings {
        let mut canon: smallvec::SmallVec<[(Sym, NodeID); 8]> =
            b.iter().map(|(s, n)| (*s, *n)).collect();
        canon.sort_by_key(|(s, _)| *s);
        if !seen.insert(canon) { continue; }
        let outcome = apply_rule_full(
            rule, &b, arena, graph, interner,
            concepts.as_deref_mut(), cache.as_deref_mut(),
            /* record_undo */ false,
        );
        if outcome.progressed { progressed_any = true; }
    }
    progressed_any
}
```

*Change:* the GAP-B fix. Reuses `apply_rule_full(record_undo=false)` (no attr clones, no undo vec) and applies **all** progressing bindings in one pass. `match_type` gives a `nodes_of_type` driver for the single-edge perception rules; everything else uses the existing matcher.

### 3b. Substrate wrapper (`runners/dsl/src/substrate.rs`)

Add a private method near `apply_rule_once` (substrate.rs:1029):

```rust
    /// Batch fast-path for the installed-rule store. See
    /// `rewrite::batch_apply_rule`.
    fn batch_apply(&mut self, rule_idx: usize) -> bool {
        let rule = self.rules[rule_idx].clone();
        #[cfg(all(target_arch = "x86_64", target_os = "linux"))]
        let jit = self.rule_where_jit.get(rule_idx).and_then(|j| j.as_ref());
        #[cfg(not(all(target_arch = "x86_64", target_os = "linux")))]
        let jit: Option<&crate::jit::CompiledWhere> = None;
        crate::rewrite::batch_apply_rule(
            &rule, &mut self.terms, &mut self.graph, &mut self.interner,
            Some(&mut self.concepts), Some(&mut self.eval_cache), jit,
        )
    }
```

*Verify:* `jit` borrows `self.rule_where_jit` while the call mut-borrows `self.terms/graph/interner/concepts/eval_cache` — disjoint fields, so this compiles (same disjoint-field pattern `try_incremental_match` already uses). If the borrow checker objects, hoist: `let jit = …; ` cannot outlive — fall back to passing `None` for batch rules (they rarely have JIT'd wheres) and note it.

---

## Deliverable 4 — `dirty_by_writeset` + precise mutation marking (`runners/dsl/src/substrate.rs`)

### 4a. Replace the blanket re-dirty (substrate.rs:1367–1371)

In `run_rules`, the `if progressed { … }` block currently does:

```rust
                    for d in self.rule_dirty.iter_mut() { *d = true; }
                    self.any_mutation = true;
```

Replace the blanket loop with a write-set-scoped dirty:

```rust
                    self.dirty_by_writeset(rule_idx);
                    self.any_mutation = true;
```

And add the method (near `mark_edge_type_dirty`, substrate.rs:277):

```rust
    /// After rule `fired` progressed, dirty only the rules whose read_set
    /// intersects `fired`'s write_set (the precise replacement for the old
    /// blanket `for d in rule_dirty { *d = true }`). A `writes_any` rule
    /// (DelNode/ReplaceValue/DefineConcept) still fans out to everything.
    fn dirty_by_writeset(&mut self, fired: usize) {
        if self.rules[fired].writes_any {
            for d in self.rule_dirty.iter_mut() { *d = true; }
            return;
        }
        // Snapshot the writer's tokens to release the borrow before the
        // mut loop over rule_dirty.
        let wset: smallvec::SmallVec<[crate::rewrite::RuleKey; 16]> =
            self.rules[fired].write_set.iter().copied().collect();
        if wset.is_empty() { return; }
        for j in 0..self.rules.len() {
            if self.rule_dirty[j] { continue; }
            let rj = &self.rules[j];
            if rj.reads_any || wset.iter().any(|k| rj.read_set.contains(k)) {
                self.rule_dirty[j] = true;
            }
        }
    }
```

*Change:* GAP-A fix for the installed-rule loop — a fired rule now wakes only its true consumers, not every rule.

### 4b. Precise `mark_node_mutation` (substrate.rs:286–305)

Split the single coarse method into attr- and type-scoped variants. The key correctness point — an attr flip can change where-truth on an **already-matched** edge that the semi-naive cursor (new-edges-only) would miss — is preserved **per-rule** by clearing only the affected rules' cursors, instead of the global `edge_delete_version` bump that invalidated *every* rule's cursor.

Replace `mark_node_mutation` with:

```rust
    /// An attr write of `key`. Dirties only rules whose read_set contains
    /// `Attr(key)` (or are `reads_any`). Does NOT bump `edge_delete_version`
    /// — a pure attr change adds/deletes no edges, so other rules' cursors
    /// stay valid. The correctness fix the old global bump guarded (an attr
    /// flip re-firing a where-rule on an EXISTING edge) is kept precisely:
    /// for each rule we dirty, we CLEAR ITS cursor so `try_incremental_match`
    /// bails to the cold full re-match for that rule alone.
    #[inline]
    fn mark_attr_mutation(&mut self, key: Sym) {
        self.any_mutation = true;
        let touched = crate::rewrite::RuleKey::Attr(key);
        for i in 0..self.rules.len() {
            let r = &self.rules[i];
            if r.reads_any || r.read_set.contains(&touched) {
                self.rule_dirty[i] = true;
                self.rule_cursors[i].clear();
            }
        }
    }

    /// A node type change old→new. Dirties rules reading either type
    /// (Type tokens) + clears their cursors, same rationale as
    /// `mark_attr_mutation`. Type reads are rare on the hot path.
    #[inline]
    fn mark_type_mutation(&mut self, old_type: Sym, new_type: Sym) {
        self.any_mutation = true;
        let a = crate::rewrite::RuleKey::Type(old_type);
        let b = crate::rewrite::RuleKey::Type(new_type);
        for i in 0..self.rules.len() {
            let r = &self.rules[i];
            if r.reads_any || r.read_set.contains(&a) || r.read_set.contains(&b) {
                self.rule_dirty[i] = true;
                self.rule_cursors[i].clear();
            }
        }
    }

    /// A bare node insert of `type_` with `attrs`. A new node enables no
    /// edge-driven match until it's edged, but its attrs/type may feed a
    /// where-clause once it is — dirty the readers conservatively. No
    /// cursor invalidation (no edges added by the node insert itself).
    #[inline]
    fn mark_node_added(&mut self, type_: Sym, attrs: &FxHashMap<Sym, Value>) {
        self.any_mutation = true;
        let ty = crate::rewrite::RuleKey::Type(type_);
        for i in 0..self.rules.len() {
            let r = &self.rules[i];
            let hit = r.reads_any
                || r.read_set.contains(&ty)
                || attrs.keys().any(|k| {
                    r.read_set.contains(&crate::rewrite::RuleKey::Attr(*k))
                });
            if hit { self.rule_dirty[i] = true; }
        }
    }

    /// Node removal — deletes the node's incident edges of unknown type.
    /// Conservative: bump edge_delete_version (cursor invalidation, as
    /// before) and dirty edge/attr/type readers + reads_any. Deletions
    /// are off the hot attr-write path.
    #[inline]
    fn mark_node_removed(&mut self) {
        self.any_mutation = true;
        self.edge_delete_version += 1;
        for d in self.rule_dirty.iter_mut() { *d = true; }
    }
```

### 4c. Update the four call sites (substrate.rs:309–404)

```rust
    pub fn add_node(&mut self, type_: Sym, attrs: FxHashMap<Sym, Value>) -> NodeID {
        self.counters.on_node_inserted(type_);
        let nid = self.graph.insert_node(type_, attrs.clone());
        self.mark_node_added(type_, &attrs);
        nid
    }
```
*Change:* `mark_node_mutation()` → `mark_node_added(type_, &attrs)`. (Clone is a small attr map; if it shows on a profile, take the keys before the move into `insert_node` instead.)

```rust
    pub fn remove_node(&mut self, nid: NodeID) -> bool {
        let had_edges = !self.graph.out_edges_slice(nid, None).is_empty()
                     || !self.graph.in_edges_slice(nid, None).is_empty();
        let ok = self.graph.delete_node(nid).is_some();
        if ok {
            let _ = had_edges; // mark_node_removed bumps the version anyway
            self.mark_node_removed();
        }
        ok
    }

    pub fn set_attr(&mut self, nid: NodeID, key: Sym, value: Value) {
        self.graph.set_node_attr(nid, key, value);
        self.mark_attr_mutation(key);
    }

    pub fn set_type(&mut self, nid: NodeID, new_type: Sym) {
        let old_type = self.graph.node(nid).type_;
        self.graph.set_node_type(nid, new_type);
        self.mark_type_mutation(old_type, new_type);
    }
```

*Change:* `set_attr` now passes the touched key (the precise win — the hot external-write path); `set_type` reads the old type before overwriting; `remove_node` keeps the conservative cursor bump. **`remove_edge` (substrate.rs:372) is unchanged** — it already bumps `edge_delete_version` + `mark_edge_type_dirty(key.edge_type)`, which is precise.

*Risk to verify:* the migrated bench must still pass `tests/ -k migrated` — the cursor-clear-per-rule replacing the global bump is the one behavioural change; the "attr flip re-fires a where-rule on an existing edge" cases (e.g. `satisfied` 0→1 firing a satisfy-rule) are exactly the ones to confirm green.

---

## Deliverable 5 — Wire into both run-rules

### 5a. Free `rewrite::run_rules` (rewrite.rs:1018–1061) — the perception path

Insert a batch branch at the top of the per-rule loop. Replace the body of `for (rule_i, rule) in rules.iter().enumerate() {` so it reads:

```rust
        for (rule_i, rule) in rules.iter().enumerate() {
            let this_jit = where_jits.get(rule_i).copied().unwrap_or(None);

            // Batch fast-path: apply every binding this pass (no undo
            // probe, no one-per-pass throttle). Doesn't `break` — other
            // rules still get this pass; the outer while re-loops on
            // progress and a settled batch rule returns false.
            if rule.batch {
                if batch_apply_rule(
                    rule, arena, graph, interner,
                    concepts.as_deref_mut(), cache.as_deref_mut(), this_jit,
                ) {
                    steps += 1;
                    any_progress = true;
                }
                continue;
            }

            // --- unchanged cold path: one progressing binding per pass ---
            let mut found_progressing: Option<Binding> = None;
            let mut bindings: Vec<Binding> = Vec::new();
            match_rule_each(rule, arena, graph, interner, concepts.as_deref(), cache.as_deref_mut(), this_jit, |b| {
                bindings.push(b.clone());
                true
            });
            for b in bindings {
                let outcome = apply_rule_full(
                    rule, &b, arena, graph, interner, concepts.as_deref_mut(), cache.as_deref_mut(), true,
                );
                if outcome.progressed {
                    found_progressing = Some(b);
                    break;
                } else {
                    undo_apply(outcome.undo, graph);
                }
            }
            if found_progressing.is_some() {
                steps += 1;
                any_progress = true;
                break;
            }
        }
```

*Change:* batch rules take `batch_apply_rule` and `continue` (don't break → non-batch rules still run this pass); non-batch rules keep the exact original one-per-pass+undo semantics. The outer `while steps < max_steps` + the `if !any_progress { return steps }` guard are untouched, so the fixpoint + step cap stand. (The local `this_jit` is hoisted up one line; the old `let this_jit = …` inside the cold block is removed.)

### 5b. `Substrate::run_rules` (substrate.rs:1282–1287) — installed rules

In the `for rule_idx in to_try {` loop, gate the batch path before `try_incremental_match`. Replace the `let progressed = if let Some(p) = self.try_incremental_match(rule_idx) { p } else { … }` opener with:

```rust
            for rule_idx in to_try {
                let progressed = if self.rules[rule_idx].batch {
                    // Batch-safe rule: drain every binding this pass.
                    self.batch_apply(rule_idx)
                } else if let Some(p) = self.try_incremental_match(rule_idx) {
                    p
                } else {
                    // ... existing cold-cursor fallback, UNCHANGED ...
```

The `if progressed { … }` tail (substrate.rs:1364) keeps `steps += 1; any_progress = true;`, now calls `self.dirty_by_writeset(rule_idx)` (Deliverable 4a) instead of the blanket loop, and keeps the `deletes` cursor-bump block as-is (batch rules that delete set `writes_any` ⇒ `dirty_by_writeset` already fans out; the `edge_delete_version` bump in the `deletes` block still correctly invalidates cursors).

*Change:* batch rules bypass cursor machinery entirely (they apply the whole snapshot); incremental + cold paths unchanged.

---

## Deliverable 6 — Rule attrs in the seed manifests

Add a top-level `"batch": true` (and `"match_type"` for the single-edge type-driver) to each safe rule object. **`avatar_vote` is deliberately omitted** — it accumulates `avatar_votes` along the correspondence chain (writes the attr it reads), so it must stay on the incremental path.

`seeds/region_grouping.json`:
- `cc_materialise` (match `[game, has_cell, cell]`) — add `"batch": true, "match_type": "GridCell"` *(set `match_type` to the actual cell node type minted by the world adapter — confirm whether it's `GridCell`/`Cell`; if uncertain omit `match_type` and the matcher path is still correct + batched).*
- `cc_region_bounds` (match `[game, has_region, region]`) — add `"batch": true, "match_type": "Region"`.
- *(leave `cc_prune_old_regions` non-batch — it's a `del_node`, `writes_any`.)*

`seeds/arc3_navigation.json`:
- `max_region_count` (match `[game, has_region, any]`, `where: null`) — add `"batch": true, "match_type": "Region"`. (Reads `NodesOfType(Region).count` + `game.frame`; writes `game.max_region_count` — disjoint.)
- `mark_floor_as_location` (2-edge `[game,has_cell,cell],[cell,within,region]`) — add `"batch": true` only (multi-edge ⇒ no single-var `match_type` driver; batch still applies all bindings).

`seeds/avatar_agency.json`:
- `region_correspondence` (2-edge, repeated `has_region`) — add `"batch": true` only. Reads region `frame/count/h/w/cx/cy`; writes `b.drow/b.dcol` + the `corresponds_to` edge — disjoint, batch-safe. (No `match_type`: multi-edge.)
- `avatar_confirm` (2-edge) — add `"batch": true` only. Reads settled `avatar_votes`; writes a `controls`/motor edge — disjoint.
- `avatar_vote` — **no batch attr.** Verify-note: confirm it stays correct (its accumulation needs per-binding re-match).

Concrete JSON shape, e.g. `cc_region_bounds`:
```json
{
 "name": "cc_region_bounds",
 "batch": true,
 "match_type": "Region",
 "comment": "give each Region the count/bbox/centroid attrs ...",
 "match": [["game", "has_region", "region"]],
 "where": { "...": "..." },
 "effects": [ "..." ]
}
```

---

## Verify checklist (for the driver)

1. **Compiles:** append `, ..Default::default()` to the ~31 `RewriteRule` 4-field literals listed in D1; flip `fn children`→`pub(crate) fn children` (term.rs:4269).
2. **`pytest tests/ -k migrated`** — the single behavioural change is the per-rule cursor-clear (D4b) replacing the global `edge_delete_version` bump; the satisfy-on-existing-edge cases are the ones to watch.
3. **Borrow check** the `batch_apply` jit field-borrow (D3b) — fall back to `None` jit if it objects.
4. **Confirm `match_type` node-type strings** against what the world adapter actually mints (`GridCell`/`Region`); a wrong string just means the matcher path runs instead of the index — still correct, just not indexed.
5. **`avatar_vote` correctness** — it's intentionally *not* batched; confirm avatar discovery still lights up (the multi-frame vote chain).
6. **Bench the win** where it lives: the perception path is `run_graph_rules → rewrite::run_rules`. Time a 32×32-grid `tick()` before/after — expect the `cc_materialise`/`cc_region_bounds` fixpoint to drop from O(cells²) passes to O(cells).

This is the whole of slice (b): one `RewriteRule` carrying its own read/write sets, one `batch_apply_rule` shared by both engines, precise write-set dirtying replacing two blanket invalidations — match/where/effect semantics byte-for-byte unchanged.
