# THE EMPTY-MATCH-SET PROOF — three rules that could never fire were 99.93% of the tick (results)

**Block 189000.** Prereg `EMPTY_MATCH_PROOF_PREREG.md`, committed **ALONE**
(`2b84243143f6fb3acec12b0823950e8c1b278d66`) BEFORE any performance number.
Base `main` @ `64449cd254a8288add893c2314952eaabb209a9c` (the 188000 ledger).
Seed block **189000–189999**, `seed_claim` **CLEAN** (verbatim in prereg §5).
**This rung BUILDS Rust. CANONICAL NEEDS REBUILD ON MERGE.**

---

## Headline

> **188000 named the lever and it was the whole tick.** On the shipped 160×120
> Doom accelerator path, the three rules 188000 measured as *woken every tick,
> O(cells) each, progressed 0* were **99.93 % of all rule time** — and **all
> three have a match edge type with ZERO live edges in the entire graph.** They
> could not have fired. Not "did not"; **could not.**
>
> Skipping a provably-empty rule's enumeration takes the per-tick settlement
> from **11.953 ms to 0.068 ms — a 176× reduction — byte-identically.** The
> three rules' own cost falls **11,874 µs → 3.8 µs per tick (≈3,200×)**.
>
> **The proof is a statement about the GRAPH, never about a flag.** It reads
> `edges_by_type` — *the same index the matcher itself enumerates* — so there is
> **no new bookkeeping that could go stale**, and any conceivable error is in the
> SAFE direction. On the accelerator-OFF graph path the very same predicate
> **DECLINES** for two of the three rules, because `has_task` is populated there.
> That is not a caveat; it is the mechanism working.
>
> **BYTE-IDENTITY: 6/6 workloads** (two vision, four non-vision), the landed
> carve exactly **4 / 0.1215 / 0.9784 / 0**, the accel onset digest
> `f5375014f2dcb8f2`, the rod digest `d777e3d8a7012a55`, and the graph-path
> onset stream **600 = 600, digest `a2e997b4c13449db`** — all unchanged.
>
> **THE UNSOUND-PREDICATE FALSIFIER BITES HARD.** Weakened to treat a SINGLETON
> edge type as absent, it **diverges on 3/6 workloads including a NON-vision one**,
> takes the landed carve from **4 polygons to 0** (IoU 0.1215 → 0.0), and takes
> the graph-path onset stream from **600 to 0**. A wrong proof destroys the eye,
> loudly — which is what makes the identity claim for the sound one worth
> something.
>
> **AND THERE IS NO FREE LUNCH.** On a control where **not one rule is provably
> empty** (verified, not assumed), the proof costs **1.003 ×**. On the eye's own
> GRAPH path it costs **1.014 ×** — it skips five rules there and buys nothing,
> because the cost on that path is elsewhere. **The win exists exactly where the
> emptiness does.**

---

## §1 THE DIAGNOSIS — the required classification, with a mechanical witness

Measured on the COMMITTED system, on the base engine
`69410e46bfaf7750010987dea947a145`, **before anything was built**, and recorded
verbatim in the prereg's §1. Live edge populations, settled, shipped accel path
(160×120, `retina_accel` ON): 76,808 nodes / 96,005 edges.

### §1.1 THE CLASSIFICATION TABLE

| rule | 188000's share | class | the evidence |
|---|---|---|---|
| `retinal_mint_onset_2d` | **68.3 %** | **(a) STRUCTURALLY EMPTY** | needs `rod -has_task-> task`; **`has_task` has ZERO live edges in the whole graph.** On the graph path it has **4800** and the proof DECLINES. |
| `photon_column_synthesizes_retinal_percept` | **22.1 %** | **(a) STRUCTURALLY EMPTY, permanently on a 2-D sheet** | **four of its five** match edge types have zero population (`l_receptor`=0, `m_receptor`=0, `s_receptor`=0, `has_retinal_percept`=0) on **BOTH** paths. 188000's prereg prediction P1, now with a *counting* witness instead of a source reading. |
| `photon_apply_receptor_transduction` | **9.5 %** | **(a) STRUCTURALLY EMPTY** | needs `receptor -has_task-> task`; same zero `has_task`. Declines on the graph path. |

**No rule is (b). No rule is (c).**

### §1.2 The (b) question — answered plainly, not dodged

The mission asks whether the 68.3 % rule is *shadowed by the accelerator*.
**Causally, yes**: `has_task` is empty because `retina_onset_batch` settles the
sheet in Rust and no per-cell `CognitiveTask` is ever minted. **But the PROOF
never reads the accelerator, the config, or any flag — it reads the graph's own
live edge population.** The consequences are what matter:

* the predicate is sound in **every** configuration, because it is a statement
  about the graph;
* with the accelerator OFF the same predicate **declines** for this rule
  (measured, §5) — so there is nothing to "turn off when the accelerator is
  off", and no semantic coupling to guard;
* it is therefore **not** a redundancy shim. Classified **(a)**, with the
  accelerator named as the *cause* of the graph state that makes (a) hold.

### §1.3 WHICH PATH the cost was on — traced, not assumed

`SUBSTRATE_TRACE_RULE=retinal_mint_onset_2d`, 10 accel ticks, **every** tick:

```
[TRACE-IM]   cursor for edge_type 'has_column' is MISSING (current_dv=57608) -> None (full re-match)
[TRACE-FULL] FULL re-match (cold/invalidated cursor); bindings found = 0
```

The **COLD** path runs every tick (`precise_dirty` clears a dirtied rule's own
cursor), so the enumeration is a full `edges_by_type` scan of the rule's FIRST
match edge — 19,200 `has_column` / `rod_receptor` / `has_receptor` edges — each
backtracking at a join whose edge type has zero population. That is the 68.3 /
22.1 / 9.5 %.

### §1.4 It is not three rules — it is SIXTEEN

The engine's own `provably_empty_rules()` on the settled accel graph:

| area | rules proved empty | witness |
|---|---|---|
| `retina` | `retinal_mint_onset_2d`, `photon_apply_receptor_transduction` | `has_task` |
| `retina` | `photon_column_synthesizes_retinal_percept` | `has_retinal_percept` |
| `retina` | `retinal_mint_carve_2d` / `_motion_2d` / `_salience_2d` | `has_carve_task_2d` / `has_motion_task_2d` / `has_salience_task_2d` |
| `scheduler` | `ct_advance_area_clock_on_result`, **`ct_area_effort_tracks_live_salience`**, `ct_area_input_epoch_tracks_completed_material`, `ct_ready_when_dependencies_settle`, `ct_rearm_stale_on_area_epoch` | `has_task` |
| `scheduler` | `ct_backoff_workers_on_failure_or_conflict`, `ct_expand_workers_while_backpressure_clean`, `ct_shed_below_max_salience_when_queue_exceeds_capacity` | `has_area_load` |
| `scheduler` | `ct_broadcast_residual_once_per_destination_epoch` | `projects_to` |
| `scheduler` | `ct_supersede_older_uncommitted_task` | `supersedes` |

**16 of the active rules.** Note the fourth row of the scheduler block:
**`ct_area_effort_tracks_live_salience`** — 187000's 67 %-of-rule-time rule and
188000's entire Part 2 — **is provably empty on this path too.** On the accel
path the emptiness proof subsumes what binding projection was built to fix.

---

## §2 WHAT WAS BUILT — one flag, one predicate, three call sites

**`Substrate::empty_match_proof`, DEFAULT FALSE.** Off ⇒ the committed path,
byte-unchanged.

```rust
fn match_set_provably_empty(&self, rule: &RewriteRule) -> bool {
    if !self.empty_match_proof || rule.match_edges.is_empty() { return false; }
    rule.match_edges.iter().any(|me| self.graph.edges_by_type(me.edge_type).is_empty())
}
```

Nothing else. **No node-type population check, no `match_type` check, no
where-clause reasoning, no attribute reasoning** — the mission forbids widening
the predicate to manufacture a win, and it was not widened.

### §2.1 THE SOUNDNESS ARGUMENT, and how it is maintained on every write path

**The proof.** Every binding assigns to each match edge `(src_var, et, tgt_var)`
an actual live edge of type `et`: `extend_each` draws candidates only from
`graph.neighbours` / `graph.in_neighbours` / `graph.edges_by_type`, all of which
yield live edges of exactly that type. A zero-population `et` ⇒ no binding
exists ⇒ the rule cannot fire ⇒ the enumeration is pure cost.

**WHY THE BOOKKEEPING CANNOT GO STALE: THERE IS NONE.** This is why this
predicate was chosen over every richer one, and it is the answer to 187000's
refusal of `rule_readers_by_key` (*"a stale entry would UNDER-approximate — the
unsafe direction"*):

> **The predicate reads `edges_by_type`, the SAME index the matcher itself
> enumerates.** No new counter, no new index, no new invariant, no new write
> path. If `edges_by_type` were ever wrong, the committed matcher would already
> be wrong, in the same direction, on the same rules.

Verified in `graph.rs`, exhaustively — `edges_by_type` is mutated in exactly two
places in the whole crate, and `self.edges.push` occurs in exactly one:

| write path | effect on `edges_by_type` | why that is correct |
|---|---|---|
| `insert_edge` (the ONLY edge creator) | `entry(edge_type).or_default().push(idx)`, in the same block that pushes `out_by_type` / `in_by_type` | an edge is in the index the instant it exists |
| `delete_edge` | `retain`s the idx out, alongside `out`/`in_`/`out_by_type`/`in_by_type` | lockstep with the adjacency indices the matcher uses |
| `delete_node` | cascades every incident edge through `delete_edge` | no orphan can survive |
| `set_type` (retype a node) | touches `by_type` only — **edges untouched** | correct: the predicate never mentions node types |
| `add_node` / `set_attr` | cannot create an edge | correct: a rule with a zero-population match edge type still cannot bind after any number of node/attr writes |

**Direction of any conceivable error.** A stale *extra* entry ⇒ `is_empty()`
false ⇒ we enumerate ⇒ committed behaviour ⇒ SAFE. Only a *missing live edge*
could make us wrongly claim empty — and a live edge missing from this index is
one the committed matcher could not find either.

### §2.2 PLACEMENT — the skip is inside the enumeration, so nothing else moves

Three call sites, each chosen so that **every** surrounding piece of engine
bookkeeping runs exactly as it does today:

1. **`attempt_one_rule` cold path** — *the one that matters* (§1.3). The skip
   leaves `bindings` empty, which is exactly what the enumeration would have
   produced; the dedup/apply loop and the cursor re-establishment after it run
   UNCHANGED.
2. **`try_incremental_match` driver loop** — skipped after `new_edges_per_pos`
   and `lengths_before` are snapshotted, so it falls through to the identical
   cursor advance. (Evaluated before the `rule_where_jit` borrow so the
   telemetry write does not fight it.)
3. **the `batch` call site** — `batch_apply_rule` with an empty match set
   snapshots zero bindings and returns `false`; the eval-cache clears after it
   still run.

`rule_cost_*`, `dirty_by_writeset`, `fallback_trace`, the cursor writes: all
untouched. **The ONLY thing elided is an enumeration that provably yields zero
bindings.**

### §2.3 The FALSIFIER — `empty_match_proof_unsound`, default false

Claims "empty" when a match edge type has **≤ 1** live edge — i.e. treats a
SINGLETON edge type as absent. That is unsound: `retinal_mint_onset_2d` binds
the retina's single `has_onset_params_2d` edge, and the carve/motion/salience
mint rules bind their single params edge. It must break things, and it does
(§4).

**NO new Term enum variant. `runners/dsl/src/term.rs` diff is EMPTY.**

---

## §3 THE PRE-REGISTERED CRITERIA, one by one

| id | threshold | measured | verdict |
|---|---|---|---|
| **C1** | flag OFF ≡ BASE engine, whole-graph float-exact, 5/5 | **6/6 IDENTICAL** (base engine `69410e46`, which reports it has no 189000 flags, vs rung engine `a9962320` with the flag off) | ✅ |
| **C2a** | flag ON byte-identical, 5/5 incl. ≥1 non-vision | **6/6 IDENTICAL**, of which **4 non-vision** (`scheduler`, `quiet_areas`, `scheduler_wide`, `conversation`) | ✅ |
| **C2b** | landed 160×120 carve exact | **4 polys / IoU 0.1215 / precision 0.9784 / 0 false** | ✅ |
| **C2c** | accel onset + rod digests identical | onset `f5375014f2dcb8f2`, rod `d777e3d8a7012a55`, both arms | ✅ |
| **C2d** | graph-path onset stream identical | **600 = 600**, digest `a2e997b4c13449db` both arms | ✅ |
| **C3** | `term.rs` diff EMPTY | empty | ✅ |
| **F1** | UNSOUND predicate breaks identity AND an observable | **diverges 3/6** (incl. non-vision `conversation`); carve **4 → 0 polygons**, IoU 0.1215 → 0.0; graph onsets **600 → 0** | ✅ |
| **F2** | no-free-lunch ratio ≥ 0.95 on a NOTHING-is-empty control | **1.003**, with `nothing_is_empty = True` verified | ✅ |
| **H1** | accel settle ON ≤ 0.60 × OFF | **0.0057** (11.953 → 0.068 ms/tick, **176×**) | ✅ |
| **H2** | THE THREE < 5 % of rule time with the proof on | **36.6 %** — ❌ **AS WORDED**, decomposed below | ❌ **BREACHED, reported not reframed** |
| **H3** | graph path: the 2-D-sheet rule skipped, the other two NOT | exactly that | ✅ |
| **P1** | proof reaches all 3 on accel, exactly 1 of the 3 on graph | exactly that | ✅ (prediction held) |

### H2 — the one breach, decomposed rather than characterised

The threshold was written as a SHARE, and the share is meaningless once the
denominator collapses. Both figures, so the reader can judge:

| | proof OFF | proof ON | change |
|---|---|---|---|
| total rule time | **11.883 ms/tick** | **0.010 ms/tick** | ÷1188 |
| THE THREE, absolute | **11,874 µs/tick** | **3.8 µs/tick** | **÷3,166** |
| THE THREE, share | **99.93 %** | **36.6 %** | ✗ vs the ≥5 % threshold |

**The criterion as written is not met and is not being re-worded to be met.**
What the residual 3.8 µs actually IS: the proof's own bookkeeping — the rules
are still visited, the predicate is still evaluated, the cursors are still
written; only the 19,200-edge scan is gone. A share of 41 µs is not a fact about
the eye. The prereg should have set an absolute threshold; it set a share, and
the share fails.

---

## §4 THE FALSIFIER — what a WRONG proof does, so the identity claim means something

The mission's critical control: *deliberately weaken the predicate and
demonstrate it BREAKS byte-identity; if a wrong proof breaks nothing, the check
is too weak to trust.*

| workload | proof (sound) | **UNSOUND (≤1)** |
|---|---|---|
| `vision_carve` | `fc69f9d2f526da4e` = base | **`9ddf2cb4eb2cc7cc` DIVERGES** |
| `conversation` (NON-vision) | `f40807219725997e` = base | **`9eec113a790e2726` DIVERGES** |
| `doom_accel_160x120` | `6cf7978cf2f30eca` = base | **`82a9a1be9d261243` DIVERGES** |
| `scheduler` / `quiet_areas` / `scheduler_wide` | = base | identical (no singleton edge type drives a firing rule there) |

And on the two OBSERVABLES that are the eye's actual output:

| observable | base | sound proof | **UNSOUND** |
|---|---|---|---|
| landed 160×120 carve | 4 / 0.1215 / 0.9784 / 0 | **4 / 0.1215 / 0.9784 / 0** | **0 polygons / IoU 0.0 / precision 0.0** |
| graph-path onset stream | 600, `a2e997b4c13449db` | **600, `a2e997b4c13449db`** | **0 onsets, `71857576257465c7`** |

**A wrong emptiness proof destroys the eye, loudly, on both a vision and a
non-vision workload.** This is strictly stronger than 187000's F1, whose
falsifier did **not** bite on any vision workload (its residual 7).

---

## §5 THE COST — and where the win is NOT

### The shipped accelerator (160×120, `retina_accel` ON, 5 builds × 4 probe ticks)

| arm | settle ms/tick (median) | all five trials | rule ms/tick | THE THREE, share |
|---|---|---|---|---|
| **off** | **11.953** | 11.451 / 11.667 / 11.953 / 12.005 / 12.093 | 11.883 | **99.93 %** |
| **proof** | **0.068** | 0.064 / 0.064 / 0.068 / 0.069 / 0.077 | 0.010 | 36.6 % (of 41 µs) |

Per-rule breakdown, the median trial (micros over 4 probe ticks):

| rule | processed | progressed | OFF µs | PROOF µs |
|---|---|---|---|---|
| `retinal_mint_onset_2d` | 4 | **0** | **30,297** | **7** |
| `photon_column_synthesizes_retinal_percept` | 4 | **0** | **12,741** | **4** |
| `photon_apply_receptor_transduction` | 4 | **0** | **4,459** | **4** |
| `ct_area_input_epoch_tracks_completed_material` | 4 | 0 | 18 | 14 |

**Independently reproduced by the gate**, which re-measures with a different
protocol (3 builds × 3 probe ticks) in its own process:
**12.319 → 0.082 ms/tick, ratio 0.007**, THE THREE 99.9 % → 34.4 %. Same
picture, same order of magnitude, different run.

Rules skipped on the accel path, 4 skips each over 4 probe ticks:
`ct_area_input_epoch_tracks_completed_material`, `ct_rearm_stale_on_area_epoch`,
`photon_apply_receptor_transduction`, `photon_column_synthesizes_retinal_percept`,
`retinal_mint_carve_2d`, `retinal_mint_motion_2d`, `retinal_mint_onset_2d`,
`retinal_mint_salience_2d` — **one skip per rule per tick, exactly.**

### WHERE THE WIN IS NOT — two honest negatives, both preregistered as acceptable

**(i) The eye's own GRAPH path (accelerator OFF, 15×20).** The proof reaches
five rules there (`photon_column_synthesizes_retinal_percept`,
`retinal_mint_carve_2d/_motion_2d/_salience_2d`,
`ct_supersede_older_uncommitted_task`) and **DECLINES** for
`retinal_mint_onset_2d` and `photon_apply_receptor_transduction`, whose
`has_task` is populated (4800 edges). Cost: **502.8 → 509.8 ms/tick, ratio
1.014 — the proof costs 1.4 % MORE.** The five it skips were cheap; the cost on
that path is the task machinery. *(This workload holds tasks without pruning and
is therefore NOT comparable to 188000's 2.86 ms figure — only the ON/OFF ratio
at one operating point is claimed.)*

**(ii) The NOTHING-is-empty control.** 64 rules, one match edge each on a
200-edge type, 200 nodes, `force_all_dirty` + `run_rules` × 3, 7 reps.
`provably_empty_rules()` verified **empty** — this is a control, not a second
win. **5.587 ms → 5.602 ms, ratio 1.003.** When nothing can be skipped,
precision costs slightly more. As predicted, and as 187000 (1.012) and 188000
(1.009) also found.

---

## §6 Provenance & discipline

- **SEPARATE prereg commit** `2b84243143f6fb3acec12b0823950e8c1b278d66`,
  `EMPTY_MATCH_PROOF_PREREG.md` **alone**, BEFORE any performance number, and
  containing the DIAGNOSIS classification and the soundness argument as the
  mission required.
- **Seed block 189000–189999**, `seed_claim` CLEAN (verbatim in prereg §5).
- **`source_match = "own"`, `stale_rust = []`** (rung engine built in THIS
  worktree). The C1 base arm ran on the base engine `69410e46`, which reports it
  has no 189000 flags — that is what makes it a base measurement.
- **Oracle** `bash scripts/rung7_vision_bench.sh` — **BEFORE 214 passed / 10
  skipped / 0 failed**, **AFTER 214 / 10 / 0**. BEFORE == AFTER. (Documented
  worktree-without-`data/` condition, identical to 187000's and 188000's; `main`
  reports 224/0 with `data/` present.)
- **Cross-domain regression** `scripts/per_area_settlement_regression.sh` (34
  named files, never a `-k` selector) — **BEFORE 23 failed / 277 passed / 5
  skipped**, **AFTER 23 / 277 / 5**, and the **SET of failing node ids is
  IDENTICAL** (sorted `diff` empty). Same set as 186000 / 187000 / 188000:
  3 in `test_cortices_tick.py`,
  `test_composer_driver_migrated::test_question_driver_parity`, 5 in
  `test_gap_awareness_migrated.py`, 5 in `test_elaboration_migrated.py`, 9 in
  `test_topic_route_selfheal_migrated.py`.
- **Gate** `tests/test_empty_match_proof_migrated.py` — **13 passed.** It pins
  byte-identity (vision + non-vision), the UNSOUND-predicate falsifier on both
  the dump AND the onset stream, the graph-derived re-derivation of the
  predicate, the zero-match-edge soundness boundary, which rules the proof
  reaches and which it DECLINES, the cost claim, and no-free-lunch. It does NOT
  gate H2's share form — see residual 1.
- **Rust built in this worktree ONLY.** Canonical `.so` md5
  **`721648860f6343e9c071ae5bdb513055`** verified BEFORE the first `cp`, AFTER
  **every** `cp` (five of them), and again at the final commit — **UNCHANGED
  throughout**. Rung engine md5 `a99623202e02a0e4a52a3f9dc0712b51`; base engine
  `69410e46bfaf7750010987dea947a145`. **CANONICAL NEEDS REBUILD ON MERGE.**
- **NO new Term enum variant** — `git diff --stat -- runners/dsl/src/term.rs` is
  EMPTY.
- Timing measured with the machine verified QUIET (0 pytest, 0 cargo), 5 trials,
  median + full spread reported.
- Raw: `results/empty_match_proof/empty_match_proof.json`,
  `results/empty_match_proof/c1_base_digests.json`.

---

## §7 Honest residuals

1. **H2 IS BREACHED AS WORDED** (36.6 % vs the < 5 % threshold) and is reported
   as a breach, not re-worded. The threshold was mis-specified: a SHARE of a
   denominator that falls 1188× is not a measurement. The absolute figure
   (11,874 → 3.8 µs/tick) is the one that carries meaning, and it was not the
   preregistered criterion.
2. **The win is configuration-conditional, and the configuration is the shipped
   one.** 176× on the accel path; **1.014× (i.e. slightly worse) on the graph
   path**; 1.003× where nothing is empty. Nothing here claims the matcher got
   faster in general — it claims that enumerating a provably empty join is pure
   waste and that on the shipped path it was ~all of the tick.
3. **The accelerator is why the graph is in that state.** The mechanism does not
   read the accelerator and is sound without it, but a reader should not
   conclude the *graph rule system* was 176× slower than it needed to be
   everywhere. It was 176× slower than it needed to be **when a Rust kernel had
   already done the work and left the graph with no tasks to bind.**
4. **`ct_area_effort_tracks_live_salience` is provably empty on the accel path**
   — 187000's 67 % rule and 188000's whole Part 2 target. On THAT path this
   rung's mechanism subsumes binding projection. It does **not** on 188000's own
   20×15 workload, where the tasks are real; the two mechanisms are complements,
   not substitutes, and this rung did not re-measure their interaction.
5. **The unsound falsifier is VACUOUS on the three scheduler workloads.** It
   bites on `vision_carve`, `conversation` and `doom_accel_160x120` — 3 of 6 —
   because only those have a firing rule that binds a singleton edge type. The
   byte-identity claim for `scheduler` / `quiet_areas` / `scheduler_wide` is
   therefore tested less severely than the other three. Stated rather than
   glossed (this is 187000's residual 7 in the opposite direction).
6. **`scheduler` and `quiet_areas` STILL produce the same dump digest**
   (`658010ae5ce23c14`) — 188000's residual 8, reproduced. `scheduler_wide` was
   added for exactly this reason and IS distinct (`c13737a734e042f2`), so the
   6-workload identity claim is **5-distinct**, up from 188000's 4.
7. **The scale-audit counters differ between arms.** `candidates`,
   `cand_tested`, `where_eval`, `binding_cloned` are all lower with the proof on
   — necessarily, since the enumeration did not happen. They are diagnostics,
   not graph state, and are not in `graph_to_dict`; no identity claim covers
   them.
8. **A cheaper-looking alternative exists and was NOT taken: join reordering.**
   `rewrite::reorder_match_edges` already implements a cardinality-ordered join
   ("pick the first edge by smallest `edges_by_type` cardinality"), which would
   also have made these enumerations free — but it is **dead code**, referenced
   only by its own unit tests and one comment, and it is a per-tick *cost model*
   rather than a *proof*. The emptiness predicate was chosen because it is a
   certainty, not an estimate. Reordering remains an open, orthogonal lever.
9. **The proof is evaluated per rule attempt, i.e. O(k) hash lookups per visit.**
   That is the F2 cost. It is not memoised and does not need to be: `k` is 1–5.
10. **`empty_match_proof` ships DEFAULT OFF**, like every mechanism in this
    lineage. Byte-identity is gated on 6 workloads and the 34-file regression,
    but the tree contains rules this rung never exercised.

---

## §8 Proposed VISION_PROTOCOL ledger row

`189000 | THE EMPTY-MATCH-SET PROOF (do not enumerate a rule whose join is PROVABLY empty — some match edge type has ZERO live edges; empty_match_proof, default OFF, droppable byte-identical mirror) | 188000 measured three rules woken EVERY tick on the shipped 160x120 accel path, each O(cells), each progressed 0, together 99.93% of rule time — and named an empty-match-set proof as the only lever neither dirty precision (187000) nor binding projection (188000) can reach | ALL THREE ARE STRUCTURALLY EMPTY, case (a), with a COUNTING witness: has_task has ZERO live edges in the entire graph (kills the 68.3% and 9.5% rules) and 4 of the 5 match edge types of the 22.1% rule have zero population on a 2-D sheet. 16 active rules are provably empty there, INCLUDING 187000's 67% rule ct_area_effort_tracks_live_salience. Settlement 11.953 -> 0.068 ms/tick (176x); THE THREE 11,874 -> 3.8 us/tick (3,166x); byte-identical 6/6 workloads (4 NON-vision), landed carve exactly 4/0.1215/0.9784/0, accel onset digest f5375014f2dcb8f2 and rod digest d777e3d8a7012a55 unchanged, graph-path onsets 600=600 digest a2e997b4c13449db | SOUNDNESS HAS NO NEW BOOKKEEPING: the predicate reads edges_by_type, the SAME index the matcher enumerates — mutated in exactly two places in the crate (insert_edge / delete_edge), set_type and add_node cannot touch it, and every conceivable staleness is in the SAFE direction. UNSOUND-PREDICATE FALSIFIER BITES HARD: weakened to treat a SINGLETON edge type as absent it diverges 3/6 incl. a NON-vision workload, takes the landed carve 4 polys -> 0 (IoU 0.1215 -> 0.0) and the graph onset stream 600 -> 0. F2 no-free-lunch 1.003 on a control where nothing_is_empty was VERIFIED. PREREGISTERED PREDICTION P1 HELD: all 3 empty on accel, exactly 1 of the 3 on the graph path | Rust built in worktree (canonical .so md5 721648860f UNCHANGED across all five cp's, REBUILD ON MERGE); term.rs EMPTY; oracle BEFORE==AFTER 214/10/0; 34-file regression 23/277/5 with an IDENTICAL failing-id set; source_match own | DECLARED BREACH: H2 was written as a SHARE (<5%) and measures 36.6% — reported as a breach, not re-worded; the denominator fell 1188x so the share is meaningless and the absolute (11,874 -> 3.8 us) is the real number. TWO DECLARED NEGATIVES: on the eye's own GRAPH path the same predicate DECLINES for two of the three rules (has_task = 4800 there) and costs 1.014x — it skips five cheap rules and buys nothing; the win exists exactly where the emptiness does. The accelerator CAUSES the empty graph state but the proof never reads it, which is what makes it sound in every configuration. Named but NOT taken: rewrite::reorder_match_edges (dead code) would also make these joins free — a cost MODEL where this is a PROOF`
