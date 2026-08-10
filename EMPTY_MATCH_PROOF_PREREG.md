# THE EMPTY-MATCH-SET PROOF — pre-registration

**Block 189000.** Seed block **189000–189999**. Base `main` @
`64449cd254a8288add893c2314952eaabb209a9c` (the 188000 ledger).
This document is committed **ALONE, BEFORE any performance number.**

188000 named the next lever without ambiguity: *"an EMPTY-MATCH-SET proof, which
no dirty precision and no binding projection can reach."* Three rules are woken
every tick on the shipped 160×120 accel path, each enumerates O(cells), and each
**progresses 0**: `retinal_mint_onset_2d` (68.3%),
`photon_column_synthesizes_retinal_percept` (22.1%),
`photon_apply_receptor_transduction` (9.5%).

---

## §0 THE SOUNDNESS DIRECTION — stated first, because it is the whole danger

Dirty-marking over-approximates safely: waking a rule that cannot fire costs
time and nothing else. **An emptiness proof is unsafe in the opposite
direction.** Claiming "empty" when the rule COULD match silently loses work —
and 187000 already refused the `rule_readers_by_key` inverse index for exactly
this reason (its §7.3: *"a stale entry would be an UNDER-approximation — the
unsafe direction — so it was deliberately not used"*).

**The rule adopted here: only ever claim empty when PROVABLY empty; when in
doubt, enumerate.** Every widening of the predicate is a soundness liability,
and this rung's predicate is therefore the narrowest one that reaches the
measured cost. **An unsound predicate that "wins" is a FAILED rung.**

---

## §1 THE DIAGNOSIS — measured on the COMMITTED system, before anything is built

Required by the mission before any build. The measurement is a **structural
property of the graph** (live edge population per edge type) plus a **match-path
trace**, both taken on the base engine `69410e46bfaf7750010987dea947a145` built
from base HEAD in this worktree. No mechanism exists yet; nothing here is a
result of this rung.

### §1.1 Live edge-type populations, settled, shipped accel path (160×120, `retina_accel` ON)

Graph: 76,808 nodes / 96,005 edges after an 8-tick hold on the Doom fixture
frame, `precise_dirty` ON, `run_rules_settle` to fixpoint each tick.

| rule | its match edge types, with live populations | zero-population types |
|---|---|---|
| `retinal_mint_onset_2d` | `has_column`=19200, `rod_receptor`=19200, **`has_task`=0**, `has_onset_params_2d`=1 | **`has_task`** |
| `photon_column_synthesizes_retinal_percept` | `rod_receptor`=19200, **`l_receptor`=0**, **`m_receptor`=0**, **`s_receptor`=0**, **`has_retinal_percept`=0** | **4 of its 5** |
| `photon_apply_receptor_transduction` | `has_receptor`=19200, **`has_task`=0** | **`has_task`** |

The whole graph's edge-type census on that path is
`has_onset_event`=38400, `has_column`=19200, `has_receptor`=19200,
`rod_receptor`=19200, and five singletons. **There is no `has_task` edge
anywhere in the graph, and no `l/m/s_receptor` or `has_retinal_percept` edge
anywhere in the graph.**

### §1.2 The same census on the 20×15 GRAPH path (`retina_accel` OFF) — the control

| rule | populations | zero-population types |
|---|---|---|
| `retinal_mint_onset_2d` | `has_column`=300, `rod_receptor`=300, **`has_task`=4800**, `has_onset_params_2d`=1 | **NONE** |
| `photon_column_synthesizes_retinal_percept` | `rod_receptor`=300, `l_receptor`=0, `m_receptor`=0, `s_receptor`=0, `has_retinal_percept`=0 | 4 of its 5 |
| `photon_apply_receptor_transduction` | `has_receptor`=300, **`has_task`=4800** | **NONE** |

### §1.3 THE CLASSIFICATION TABLE (a) / (b) / (c)

| rule | share | classification | evidence |
|---|---|---|---|
| `retinal_mint_onset_2d` | **68.3%** | **(a) STRUCTURALLY EMPTY** — and see the (b) note below | its match requires `rod -has_task-> task`; the edge type `has_task` has **ZERO live edges in the entire graph** on the accel path. No binding can exist. On the graph path the same type has 4800 edges and the rule is NOT provably empty — the proof correctly declines. |
| `photon_column_synthesizes_retinal_percept` | **22.1%** | **(a) STRUCTURALLY EMPTY, permanently on a 2-D sheet** | `_build_2d` mints no `RetinalPercept` and no l/m/s receptors, so **four of its five match edge types have zero population** on BOTH the accel and the graph path. This is 188000's prereg prediction P1, now given a *mechanical* witness (a population count) rather than a source reading. |
| `photon_apply_receptor_transduction` | **9.5%** | **(a) STRUCTURALLY EMPTY** | its match requires `receptor -has_task-> task`; same zero `has_task` population. Declines on the graph path (4800). |

**On the (b) question, stated plainly and honestly.** The mission asks whether
the 68.3% rule is *"shadowed by the accelerator"*. **Causally, yes** — the
reason `has_task` is empty on the accel path is that `retina_onset_batch`
settles the sheet in Rust and no per-cell `CognitiveTask` is ever minted. **But
the PROOF does not read the accelerator, the config, or any flag: it reads the
graph's own live edge population.** That distinction is the whole design:

* the predicate is sound in *every* configuration, because it is a statement
  about the graph, not about the accelerator;
* on the graph path (accelerator OFF) the very same predicate **declines** for
  this rule, because `has_task` is populated — which is also this rung's
  built-in no-free-lunch control;
* it is therefore **not** a semantic coupling to the accelerator and does **not**
  need a "must not change behaviour when the accelerator is off" caveat: when
  the accelerator is off, the predicate is simply false.

So: classified **(a)**, with the accelerator named as the *cause* of the graph
state that makes (a) hold. It is not classified (b), because nothing in the
mechanism refers to the accelerator. No rule is classified (c).

### §1.4 WHICH MATCH PATH the cost is on — traced, not assumed

`SUBSTRATE_TRACE_RULE=retinal_mint_onset_2d`, 10 accel ticks, every tick:

```
[TRACE-IM]   cursor for edge_type 'has_column' is MISSING (current_dv=57608) -> None (full re-match)
[TRACE-FULL] FULL re-match (cold/invalidated cursor); bindings found = 0
```

**The COLD path runs on every tick** — `precise_dirty` clears a dirtied rule's
own cursor, so the incremental cursor is never valid. The enumeration is
therefore a full `edges_by_type` scan of the rule's FIRST match edge (19,200
`has_column` / `rod_receptor` / `has_receptor` edges) with a per-candidate
backtrack at the empty join. **That is the 68.3 / 22.1 / 9.5 %.**

---

## §2 WHAT WILL BE BUILT — the narrowest sound predicate

One engine flag, **`Substrate::empty_match_proof`, DEFAULT FALSE.** Off ⇒ the
committed code path, byte-unchanged. On, the predicate is:

> **A rule's match set is provably empty iff it has at least one match edge and
> SOME match edge's `edge_type` has ZERO live edges in the graph.**

```rust
fn match_set_provably_empty(&self, rule: &RewriteRule) -> bool {
    if !self.empty_match_proof || rule.match_edges.is_empty() { return false; }
    rule.match_edges.iter().any(|me| self.graph.edges_by_type(me.edge_type).is_empty())
}
```

Nothing else. No node-type population check, no `match_type` check, no
where-clause reasoning, no attribute reasoning. **Deliberately minimal: the
mission forbids widening the predicate to manufacture a win.**

### §2.1 THE SOUNDNESS ARGUMENT, and how it is maintained on every write path

**The proof.** Every binding of a rule assigns, to each match edge
`(src_var, et, tgt_var)`, an actual live edge of type `et` in the graph
(`extend_each` only ever produces candidates from `graph.neighbours`,
`graph.in_neighbours` or `graph.edges_by_type`, all of which return live edges of
exactly that type). Therefore if the set of live edges of type `et` is EMPTY,
no binding exists, the match set is empty, and the rule cannot fire. Skipping the
enumeration is byte-identical to running it.

**Why the bookkeeping cannot go stale — there is NONE.** This is the load-bearing
property, and it is why this predicate was chosen over every richer one:

> **The predicate reads `edges_by_type` — the SAME index the matcher itself
> enumerates.** No new counter, no new index, no new invariant, and therefore no
> new write path to maintain. If `edges_by_type` were ever wrong, the committed
> matcher would already be wrong, in the same direction, on the same rules.

For completeness, the maintenance of that index in `graph.rs` on every write
path that could create or destroy a match:

| write path | what it does to `edges_by_type` |
|---|---|
| `insert_edge` | `edges_by_type.entry(edge_type).or_default().push(idx)` — an edge is in the index the instant it exists |
| `delete_edge` | retains-out the idx from `edges_by_type[edge_type]` (and from `out_by_type` / `in_by_type`) |
| `delete_node` | cascades: deletes every incident edge through `delete_edge`, so the index follows |
| `set_type` (node retype) | touches `by_type` only. **Edges are untouched, so `edges_by_type` is unaffected — and correctly so: the predicate never mentions node types.** |
| `add_node` / `set_attr` | cannot create an edge; `edges_by_type` unaffected — and correctly so: a rule with a zero-population match edge type still cannot bind after any number of node/attr writes |

**Direction of any conceivable error.** A stale *extra* entry would make
`is_empty()` false ⇒ we enumerate ⇒ the committed behaviour ⇒ SAFE. Only a
*missing* live edge could make us wrongly claim empty, and a missing live edge
would mean the matcher itself cannot find it either — the failure would not be
introduced by this rung.

**No cursor / bookkeeping divergence.** The skip is placed *inside* each
enumeration site, so that every surrounding piece of engine bookkeeping — cursor
re-establishment (`rule_cursors` ← current `edges_by_type` length + current
`edge_delete_version`), `rule_cost_*` accounting, `dirty_by_writeset`, the
eval-cache clears — runs **exactly as it does today**. The ONLY thing elided is
the enumeration that provably yields zero bindings. Three sites:
`attempt_one_rule`'s cold path, `try_incremental_match`'s driver loop, and the
`batch` call site.

### §2.2 The FALSIFIER — `empty_match_proof_unsound`, default false

A deliberately weakened predicate that claims "empty" when a match edge type has
**≤ 1** live edge. On the 20×15 graph path this claims `retinal_mint_onset_2d`
is empty (its `has_onset_params_2d` type has exactly ONE edge) when it can and
does match. **It MUST break byte-identity and MUST break the onset stream.** If
it does not, the identity check is too weak to be trusted and will be
strengthened before any claim is made.

---

## §3 PRE-REGISTERED CRITERIA AND THRESHOLDS — fixed before measuring

| id | criterion | threshold |
|---|---|---|
| **C1** | flag OFF ≡ base engine, whole-graph float-exact dump | identical on **5/5** workloads |
| **C2a** | flag ON byte-identical, whole-graph float-exact dump | identical on **5/5** workloads, incl. ≥1 NON-VISION workload |
| **C2b** | landed 160×120 Doom carve under the proof | exactly **4 polys / IoU 0.1215 / precision 0.9784 / 0 false** |
| **C2c** | onset-event stream digest + rod-state digest, accel path, ON vs OFF | **identical** |
| **C2d** | graph-path onset stream (20×15), ON vs OFF | identical count AND identical digest |
| **C3** | `runners/dsl/src/term.rs` diff | **EMPTY** (no new Term enum variant) |
| **F1** | UNSOUND predicate breaks byte-identity | **MUST DIVERGE** on ≥1 workload, **and MUST break the graph-path onset stream** |
| **F2** | no-free-lunch: on a workload where the match sets are NON-empty, proof ON / OFF cost ratio | **≥ 0.95** (i.e. ON is not faster; bookkeeping may cost) |
| **H1** | shipped accel path (160×120), settle ms/tick, proof ON vs OFF | ON ≤ **0.60 ×** OFF |
| **H2** | combined share of rule time of the three named rules, accel path, proof ON | < **5 %** (was 68.3 + 22.1 + 9.5 = 99.9 %) |
| **H3** | 20×15 GRAPH path (accelerator OFF): the proof reaches `photon_column_synthesizes_retinal_percept` only | that rule skipped; the other two **NOT** skipped |

**Declared acceptable NEGATIVES** (recorded in advance so they cannot be
reframed later): only the 22.1% rule proves empty; or the bookkeeping costs as
much as it saves; or H1 misses because the accel path's remaining cost is
outside `run_rules`. Whatever the measurement says is what gets reported.

**Declared PREDICTION P1.** From §1.1 alone, before any timing: the proof will
reach **all three** rules on the accel path (all three have a zero-population
match edge type) and **exactly one** of the three on the graph path. If the
measured skip set differs from that, the mechanism is wrong, not the prediction.

---

## §4 CONTROLS, GATES, DISCIPLINE

* **Oracle** `bash scripts/rung7_vision_bench.sh` — 0 failed, **BEFORE == AFTER**.
  (Documented worktree-without-`data/` condition; both figures reported.)
* **Cross-domain regression** `scripts/per_area_settlement_regression.sh`
  (34 named files, never a `-k` selector) BEFORE/AFTER, compared as the **SET of
  failing node ids** — load-bearing here, because this rung touches the matcher
  that every domain runs through.
* **Gate** `tests/test_empty_match_proof_migrated.py` — pins byte-identity, the
  UNSOUND-predicate falsifier, no-free-lunch, and the cost/skip claim.
* **Provenance §10** `source_match in ("own","shared")`.
* Raw data under `results/empty_match_proof/`.
* **Rust is built in THIS worktree ONLY.** Canonical
  `runners/dsl/python/substrate_rs/_native.abi3.so` md5
  **`721648860f6343e9c071ae5bdb513055`** verified BEFORE the first `cp`, AFTER
  EVERY `cp`, and AGAIN at the final commit (lesson 9b — the symlink can appear
  AFTER the check). **CANONICAL NEEDS REBUILD ON MERGE.**
* Timing is measured with the machine verified QUIET (no pytest/cargo running),
  multiple trials, median + spread.

---

## §5 SEED CLAIM — verbatim

```
$ python3 scripts/seed_claim.py 189000 189999
SEED CLAIM 189000-189999: CLEAN -- no collision DETECTED.
  Scope: 889 files with seed sinks; 604 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```
