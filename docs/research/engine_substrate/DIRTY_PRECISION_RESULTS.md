# DIRTY-PROPAGATION PRECISION — the blanket is the over-approximation, and cutting it 7.3× buys NO time (results)

**Block 187000.** Prereg `DIRTY_PRECISION_PREREG.md`, committed ALONE
(`51a44cd1481284fba6ad8fadd038cdc6f85c4f34`) BEFORE any number. `source_match = "own"`, `stale_rust = []`.
**This rung BUILDS Rust** — the canonical `.so` md5 `bb3692fdfa1be1c4aa3664dc1dbffabc`
(mtime Jul 25 12:07) is **UNCHANGED**; every build happened in this worktree only.
**CANONICAL NEEDS REBUILD ON MERGE.**
Seed block **187000–187999**; `python3 scripts/seed_claim.py 187000 187999` → **CLEAN**.

---

## Headline

> **Block 186000 named the wrong culprit — and the measurement says so.**
> `dirty_by_writeset` makes **ZERO** dirty-marks on the real photon path. The
> over-approximation that dominates is `mark_node_mutation`'s **BLANKET over every
> where-clause rule**, fired by every external write: **1,536,016 dirty-marks per tick**
> on the shipped 160×120 Doom path, **100% of them from that one path**.
>
> Key-precise + value-level dirtying cuts that to **211,208 (7.27×)**, and the dirty rule
> set from 16 to 8 — **byte-identically**, including the landed carve (4 polys / IoU
> 0.1215 / precision 0.9784, exact).
>
> **And it buys NO time. The rung's headline H1/H2 are a NEGATIVE.** All six areas stay
> dirty at every scene-change fraction from 0% to 100%, and the per-tick cost is
> **2.88–2.91 ms in every cell of the table, both arms** — 186000's 2.87 ms, unmoved.
>
> **The reason is now NAMED, not guessed: the six areas are coupled by ONE ATTRIBUTE
> KEY.** Exactly eight rules read `Attr("input_epoch")`, they span all six areas, and the
> dirty set on every settled tick is EXACTLY that set of eight. A single `set_attr` of
> `input_epoch` **on the retina ROOT — a node on which no rule reads that key at all** —
> takes the graph from **0 dirty rules to 8, across all 6 areas.** Key-level precision
> cannot see that; only INSTANCE-level precision could.
>
> **And the time was never the waking anyway:** 67.1% of the per-tick rule time is ONE
> rule, `ct_area_effort_tracks_live_salience`, **processed 8 times and progressed 0** — a
> GENUINELY dirty rule with an expensive match, which no dirty-propagation precision can
> skip.

---

## §1 THE DIAGNOSIS — measured FIRST, before anything was built

The engine has **THREE** paths that set `rule_dirty`, not one. A **MARK** is one
`rule_dirty[j] = true`; the `false→true` transitions are counted separately.

### On the shipped Doom path (160×120, `retina_accel` ON), settled plain photon tick

| path | marks / tick | share |
|---|---|---|
| **P1 `dirty_by_writeset`** (rule effects — 186000's named culprit) | **0** | **0.0 %** |
| P2 `mark_edge_type_dirty` | 0 | 0.0 % |
| **P3 `mark_node_mutation`** — the BLANKET external-write path | **1,536,016** | **100.0 %** |

96,001 external write events, 96,001 attr writes, **19,200 (20.0%) of them writing a value
that was already there**. Rule attempts 16, **progressing steps 0** → spurious fraction
**100%**. Dirty rules 16, dirty areas **6 of 6**.

### On the 20×15 graph retina (186000's own workload), settled plain photon tick

| path | marks / tick | share |
|---|---|---|
| **P1 `dirty_by_writeset`** | **0** | **0.0 %** |
| P2 `mark_edge_type_dirty` | 4,800 | 14.2 % |
| **P3 external blanket** | **28,960** | **85.8 %** |

1,810 external write events, 1,210 attr writes, 8 no-ops (0.66%). Attempts 20,
progressing 3 → **spurious 85%**. Dirty rules 16, areas 6 of 6.

**VERDICT: BRANCH A** (the pre-registered branch for "P3 dominates, >50%"). It is not
close — P3 is 85.8% and 100.0%, and P1, the mechanism 186000 pointed at, contributes
**nothing at all**. It cannot: on a plain photon tick almost no rule fires (0–3 progressing
steps), and `dirty_by_writeset` only runs when a rule fires.

Why 186000 got it wrong is itself simple and worth recording: it inspected the *static*
read/write sets and found that onset writes what carve/motion/salience read. It does — but
**that path never executes on a quiet tick.** The areas were already dirty before any rule
fired, from the host's own writes.

---

## §2 WHAT WAS BUILT (Rust, additive, DEFAULT OFF)

One engine flag, `Substrate::precise_dirty`, **default `false`**. Off ⇒ the committed code
path, unchanged. On:

**A. VALUE-LEVEL.** `set_attr` compares the incoming value to the stored one. **If equal:
mark NOTHING** — no dirty bit, no cursor clear, no `edge_delete_version` bump. `set_node_attr`
re-inserts the same value and removes-then-re-adds the same attr-index bucket entry, so the
graph is **bit-identical either way**; no rule's bindings and no where-clause's truth can
change; running its consumers would be a **genuine no-op**. **Nothing is frozen** — this is
not 185000's Branch B, which deferred a cell against a FROZEN adapted floor and manufactured
onsets.

**B. PER-KEY external dirtying** (`Substrate::mark_external_write`), using **exactly** the
predicate `dirty_by_writeset` already applies to a rule-effect write, so the two paths become
symmetric (which that function's own comment asks for):

| write | dirties rule `j` iff |
|---|---|
| `set_attr(n,k,v)`, `v` changed | `reads_any ∨ (has_where ∧ Attr(k) ∈ read_set)` |
| `add_node(t, attrs)` | `reads_any ∨ Type(t) ∈ read_set ∨ (has_where ∧ ∃k∈attrs. Attr(k) ∈ read_set)` |
| `set_type(n,t')` | `reads_any ∨ Type(t) ∈ read_set` for the OLD **and** NEW type (structural, unconditional) |
| `remove_node(n)` | the same as `add_node`, **plus** `mark_edge_type_dirty(et)` for every INCIDENT edge type, plus the retained `edge_delete_version` bump — a deletion must never be under-approximated |

A dirtied rule gets its OWN cursor cleared (the per-rule form of the blanket's global
version bump). `read_set` is an over-approximate SUPERSET of true reads, so
"not in read_set" ⇒ "provably does not read it" — the safe direction.

**C. Telemetry** (`dirty_telemetry`, default off) + read-only introspection
(`dirty_marks`, `dirty_rule_count`, `dirty_rule_names`, `dirty_area_names`,
`rules_reading_attr`, `force_all_dirty`). **NO new Term enum variant — `term.rs` diff is
EMPTY.** PyO3 setters + engine methods only.

---

## §3 THE PRE-REGISTERED CRITERIA, one by one

| id | threshold | measured | verdict |
|---|---|---|---|
| **C1a** | oracle `rung7_vision_bench.sh` 0 failed, BEFORE == AFTER | see §Provenance | ✅ |
| **C1b** | 34-file regression: IDENTICAL failing node-id SET | see §Provenance | ✅ |
| **C1c** | DEFAULT-path dumps identical, base engine vs rung engine, ≥4 workloads | **5/5 identical** | ✅ |
| **C1d** | `term.rs` diff empty | empty | ✅ |
| **C2a** | precise ≡ over-approximate, full float-exact dump, ≥4 workloads | **4 / 5** — `conversation` **DIVERGES** | ⚠️ **BREACHED, decomposed below** |
| **C2b** | landed 160×120 carve exactly 4 / 0.1215 / 0.9784 | **4 / 0.1215 / 0.9784 / 0 false**, onset + rod digests identical | ✅ |
| **C2c** | dirty-mark reduction ≥ 2× | **7.27×** (160×120 shipped); **1.50×** (20×15) | ✅ on the shipped path, ✗ on the small graph path |
| **F1** | the over-aggressive predicate MUST break byte-identity | **DIVERGES on 2/5 workloads** (+ 2/2 in the gate) — non-vacuous, but **NOT on any vision workload** | ✅ with a finding attached |
| **F2** | no-free-lunch ratio ≥ 0.95 | **1.012** | ✅ |
| **H1** | dirty areas < 6 on a partially-changing scene | **6 of 6 at every change fraction, both arms** | ❌ **NEGATIVE** |
| **H2** | precise/over-approx tick cost ≤ 0.80 | **≈ 1.00** (2.88–2.91 ms either way) | ❌ **NEGATIVE** |
| **H3** | dirty count + cost vs change fraction, monotone non-decreasing | **FLAT** — identical at 0 %, 1 %, 5 %, 25 %, 100 % | reported |

### C2a — the one breach, decomposed rather than characterised

`conversation` (the booted `WorldAdapter`, 4 utterances) is the only workload whose dump
moved. Decomposed:

| | identical? |
|---|---|
| `next_id` | ✅ |
| node list, **in order**, float-exact | ✅ |
| node SET | ✅ |
| **edge list, in order** | ❌ |
| edge SET | ✅ (1,304 = 1,304) |

**No node is minted differently, no attribute differs, and no edge is present in one arm and
absent in the other. The only difference is the ORDER in which two edges were inserted** —
an `expects_response` edge lands before vs after two `refers_to` edges. Reducing the dirty
set changes which rules are in a pass's `to_try`, which changes firing order; the fixpoint
is the same, the insertion order is not. This is the same class 186000 named (its C2c/C2d:
the committed rule system is **not confluent under re-ordering**, there via node-MINT order,
here via edge-INSERTION order).

**And no wake was missed — proved, not asserted.** After each arm reaches its endpoint,
`force_all_dirty()` (mark EVERY rule dirty, invalidate EVERY cursor) followed by the
committed `run_rules()` makes **0 steps and leaves the graph unchanged, in BOTH arms.** The
precise endpoint is a genuine fixpoint of the whole rule system.

Both arms are individually reproducible (`OFF≡OFF`, `ON≡ON`, byte-exact). A control that
pumps the *committed* engine 1/2/3 times per utterance is order-STABLE, so the reorder is
attributable to the changed dirty set and to nothing else.

**Reported as a breach.** `precise_dirty` is byte-identical on the vision and scheduler
paths and **edge-order-divergent (content-identical) on the conversational agent** — which
is exactly why it ships DEFAULT OFF.

### F1 — the falsifier holds, and tells us something bigger

The over-aggressive arm makes two tempting, wrong choices at once: the external-write path
wakes **nobody**, and a float write "within 1e-9" is treated as a no-op (**185000's Branch-B
shape** — a skip of something not genuinely settled).

| workload | over-aggressive vs precise |
|---|---|
| `scheduler` | **DIVERGES** |
| `quiet_areas` | **DIVERGES** |
| gate `chain` | **DIVERGES** |
| `vision_carve` | identical |
| `doom_accel_160x120` | identical |
| `conversation` | identical |

The gate is non-vacuous. But the vision rows are a finding in their own right:
**on the vision path the entire external-write dirty path is REDUNDANT.** Deleting it
outright changes nothing observable there, because `mark_edge_type_dirty` (from the
`has_task` / `has_onset_event` edges) already wakes everything vision needs. The blanket's
1.5 M marks per tick on the Doom path buy **literally nothing** for vision — they are pure
bookkeeping, and they are 100% of the dirty-marks made.

### F2 — no free lunch

64 rules, all reading the written key in a where-clause, 400 changing writes each followed by
`run_rules`: over-approximate **7.92 ms**, precise **8.02 ms**, **ratio 1.012**. When nothing
can be skipped, precision costs slightly more. As predicted.

---

## §4 THE NEGATIVE, and exactly why

### H1/H2/H3 — the sweep

Six-area retina (186000's `set_rule_area` relabelling), adapt-then-perturb protocol: hold a
static frame for 10 ticks until the sheet has SETTLED, change `f` of the cells, measure the
settlement events that follow. Median of 5 builds × 6 probe ticks.

| scene changed | arm | dirty AREAS | dirty rules | rule attempts | median ms / tick |
|---|---|---|---|---|---|
| 0 % | over-approx | **6** | 16 | 20 | 2.880 |
| 0 % | precise | **6** | 13 | 17 | 2.897 |
| 1 % | over-approx | **6** | 16 | 20 | 2.895 |
| 1 % | precise | **6** | 13 | 17 | 2.885 |
| 5 % | over-approx | **6** | 16 | 20 | 2.890 |
| 5 % | precise | **6** | 13 | 17 | 2.888 |
| 25 % | over-approx | **6** | 16 | 20 | 2.886 |
| 25 % | precise | **6** | 13 | 17 | 2.895 |
| 100 % | over-approx | **6** | 16 | 20 | 2.907 |
| 100 % | precise | **6** | 13 | 17 | 2.907 |

**Every area is dirty at every change fraction in both arms, and the cost does not move —
not with precision, and not with how much of the world changed.** 186000's 2.87 ms is
reproduced to three digits and is untouched.

### WHY every area stays awake — ONE ATTRIBUTE KEY

`rules_reading_attr("input_epoch")` returns exactly eight active rules, and they span all six
areas:

| area | rule |
|---|---|
| `scheduler` | `ct_area_input_epoch_tracks_completed_material` |
| `scheduler` | `ct_rearm_stale_on_area_epoch` |
| `retina` | `photon_apply_receptor_transduction` |
| `retina` | `photon_column_synthesizes_retinal_percept` |
| `v1_onset` | `retinal_mint_onset_2d` |
| `mt_carve` | `retinal_mint_carve_2d` |
| `mt_motion` | `retinal_mint_motion_2d` |
| `lip_salience` | `retinal_mint_salience_2d` |

**The dirty set on every settled photon tick, under precision, is EXACTLY that set of
eight.** Not a superset, not a subset.

**The isolation probe.** Settle the eye to zero dirty rules, then make exactly ONE write:
`set_attr(retina_root, "input_epoch", …)` — what `submit_photons_2d` does first,
unconditionally, outside every accelerator flag.

```
0 dirty rules  ->  8 dirty rules, 6 areas
```

**No rule reads `input_epoch` on that node.** They read it on `rod`, `task`, `column`,
`area`, `percept` — verified against the seed sources. The wake is entirely an artefact of
**KEY** granularity. **Instance-level precision (prereg axis 3) is the lever that would cut
it, and it is NOT built here.**

The counterfactual confirms the coupling is structural, not incidental: with 185000's
per-cell epoch STAMP turned OFF (`retina_dirty_stamp_epoch=False` — a diagnostic, not a
claim; 185000 measured that dropping the stamp is exact on everything observable but not
whole-graph byte-identical), the dirty set is **the same eight rules, the same six areas,
the same 153,608 marks.** One root-level write is enough on its own.

This lands precisely on the tree's standing axiom: **the shared epoch is a GLOBAL CLOCK, and
the global clock is what couples the areas.** Per-sensor time is not an aesthetic preference
here; it is the measured unblocking change.

### AND THE TIME WAS NEVER THE WAKING

`rule_costs` on the same settled path (12-tick hold, 8 probe ticks, per-rule micros):

| share of rule time | rule | processed | **progressed** |
|---|---|---|---|
| **67.1 %** | `ct_area_effort_tracks_live_salience` (`scheduler`) | 8 | **0** |
| 7.9 % | `photon_apply_receptor_transduction` | 16 | 8 |
| 7.8 % | `ct_advance_area_clock_on_result` | 16 | 8 |
| 7.1 % | `ct_area_input_epoch_tracks_completed_material` | 16 | 8 |

(precise arm: 67.9 % / 7.8 % / 7.5 % / 7.0 % — the same picture.) Wall 5.5 ms per tick
end-to-end, **2.74 ms of it inside rules** — which is the 2.88 ms the settlement call
measures.

**Two thirds of the tick is a single rule that is woken every tick and NEVER FIRES.** It is
not a spurious wake — it genuinely reads material that genuinely changed — so no
dirty-propagation precision, at any granularity, can skip it. What it needs is a cheaper
MATCH (it enumerates the live task set to recompute area effort), or an instance-level dirty
set that could tell it only one task moved.

### The value-level skip, and 185000's fixed point seen from here

No-op fraction of the per-cell attr writes on the shipped 160×120 path, as the sheet adapts:

| ticks held | attr writes | no-ops | no-op % | external marks |
|---|---|---|---|---|
| 1 | 115,201 | 19,200 | 16.7 % | 249,608 |
| 5–40 | 96,001 | 19,200 | 20.0 % | 211,208 |
| **80** | 96,001 | **76,800** | **80.0 %** | **153,608** |
| 120 | 96,001 | 76,800 | 80.0 % | 153,608 |

Block 185000 measured the receptor EMA reaching an **exact float64 fixed point** at
t\* ≈ 71 ticks. Here is the same fact read through the dirty path: past t\*, **four of the
five per-cell writes** (`prev_activation`, `activation`, `adaptation`, `caught_quanta`) stop
changing anything and are skipped; the fifth, `input_epoch`, never stops changing — **185000
named that stamp as its own last O(cells) residual, and it is also what keeps every cortical
area awake.** Marks against the committed blanket's 1,536,016: **10.0× fewer.**

---

## §5 THE OUTCOME THAT WAS KEPT AVAILABLE, AND IS THE OUTCOME

The prereg said plainly that "the vision pipeline is genuinely all-dirty every tick" was an
acceptable finding. **It is the finding — with a sharper mechanism than the prereg
anticipated:**

> **The eye's six areas are genuinely coupled every tick, but NOT because onset writes what
> carve/motion/salience read. They are coupled by ONE SHARED ATTRIBUTE KEY — the epoch
> stamp — read by eight rules across all six areas. Area-grain parallelism is not the win
> at key granularity. The two measured levers are (1) INSTANCE-level dirty propagation, and
> (2) the expensive match of the one scheduler rule that consumes two thirds of the tick and
> never fires.**

No threshold was loosened, no definition of "dirty" was relaxed, and the win that WAS found
(7.27× fewer marks, 2× fewer dirty rules, byte-identical) is reported for exactly what it is
— a reduction in bookkeeping that does not move the clock.

---

## §6 Provenance & discipline

- **SEPARATE prereg commit** `DIRTY_PRECISION_PREREG.md` alone, BEFORE any number.
- **Seed block 187000–187999**, `seed_claim` CLEAN (verbatim in the prereg §9).
- **Oracle** `bash scripts/rung7_vision_bench.sh` — **BEFORE 214 passed / 10 skipped /
  0 failed**, **AFTER 214 / 10 / 0** — BEFORE == AFTER. (Documented
  worktree-without-`data/` condition; `main` reports 224/0 with data present.)
- **Cross-domain regression** `scripts/per_area_settlement_regression.sh` (34 named files,
  never a `-k` selector) — **BEFORE 23 failed / 277 passed / 5 skipped**, **AFTER 23 / 277 /
  5**, and the **SET of 23 failing node ids is IDENTICAL** (`diff` of the sorted id lists is
  empty), and identical to 186000's list: 3 in `test_cortices_tick.py`,
  `test_composer_driver_migrated::test_question_driver_parity`, 5 in
  `test_gap_awareness_migrated.py`, 5 in `test_elaboration_migrated.py`, 9 in
  `test_topic_route_selfheal_migrated.py`.
- **Gate** `tests/test_dirty_precision_migrated.py` — **10 passed**.
- **Rust built in this worktree ONLY.** Canonical `.so` md5
  `bb3692fdfa1be1c4aa3664dc1dbffabc` verified UNCHANGED before and after.
  Base engine short `c8118425299a` (md5 `fc503e787f38d20788a1bab6c9fd81a9`, reproduced
  exactly on a second build); rung engine short **`8e624b5bfdc6`**.
  **CANONICAL NEEDS REBUILD ON MERGE.**
- `source_match = "own"`, `stale_rust = []`.
- **NO new Term enum variant** — `git diff --stat -- runners/dsl/src/term.rs` is EMPTY.
- Raw + curves: `results/dirty_precision/dirty_precision.json`,
  `results/dirty_precision/dirty_precision.png`.

---

## §7 Honest residuals

1. **C2a is BREACHED on `conversation`** — edge INSERTION ORDER moves, content does not.
   Node ids, `next_id`, node attrs and the edge SET are identical and the endpoint is a
   proved fixpoint, but edge order IS observable (iteration order feeds later matches), so
   this is a real caveat and not a cosmetic one. `precise_dirty` therefore ships DEFAULT
   OFF, and any future rung that turns it on for a conversational agent must re-establish
   order-identity or accept the reorder explicitly.
2. **C2c is met on the shipped Doom path (7.27×) but NOT on the 20×15 graph path (1.50×).**
   The threshold was written for "the photon path" without distinguishing the two; both are
   reported.
3. **The precise path is still O(rules) per external write.** It scans every rule's
   `read_set` exactly as the blanket scans every `has_where` flag. The inverse index
   `rule_readers_by_key` already exists and would make it O(readers), but it is only
   rebuilt at `add_rule` / `set_rule_clause` and a stale entry would be an
   UNDER-approximation — the unsafe direction — so it was deliberately not used. That is why
   precision cuts MARKS 7.3× and cuts wall time by nothing.
4. **Instance-level precision is NOT built** (prereg axis 3). It is the measured lever for
   H1, and this rung establishes that it is the ONLY one that could work at the area grain.
5. **The dominant cost is a MATCH, not a wake** (`ct_area_effort_tracks_live_salience`,
   67 % of rule time, 0 progressions). Nothing here touches it.
6. **`add_node` under precision does not dirty where-less rules on a Type hit through the
   `has_where` gate** — it dirties them on `Type ∈ read_set` unconditionally, matching
   `dirty_by_writeset`. The two paths are now symmetric; if `dirty_by_writeset`'s predicate
   is ever found wrong, both are wrong together. That is a deliberate coupling, recorded.
7. **The F1 falsifier does NOT bite on any vision workload** — the byte-identity claim for
   vision is therefore weaker than for `scheduler`/`quiet_areas`: on vision, the external
   dirty path could be deleted entirely with no observable change, so "identical" there
   tests less than it appears to. Stated rather than glossed.
8. **`force_all_dirty` is a diagnostic** added to the engine. It is never called by the
   committed tree.
