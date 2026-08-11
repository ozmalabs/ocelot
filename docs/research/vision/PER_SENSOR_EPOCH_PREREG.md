# PER-SENSOR EPOCH — cut the global clock out of the eye (PRE-REGISTRATION)

**Block 188000.** Committed **ALONE**, BEFORE any number of this rung is produced.
Base `main` @ `f3cc8a482b2a7502c0d09556a77dc39f8662e36a` (the 187000 ledger).

---

## §0 The two prior rungs that point at the same object

* **187000** (`DIRTY_PRECISION_RESULTS.md`) measured that key-level dirty precision cuts
  marks 7.27× byte-identically and buys **ZERO** time, because *"the six areas are coupled
  by ONE SHARED ATTRIBUTE KEY — `Attr("input_epoch")`"*: 8 rules read it, they span all six
  areas, and **one `set_attr(retina_root,"input_epoch",…)` — on a node no rule reads that
  key on — takes 0 dirty rules to 8 across 6 areas.** It also measured that **67.1% of
  per-tick rule time is ONE rule, `ct_area_effort_tracks_live_salience`, processed 8 /
  progressed 0.**
* **185000** (`VISION_DIRTY_INDEX_RESULTS.md`) recorded the same object from the other
  side: the `input_epoch` stamp is the last O(cells) term, dropping it is exact on
  everything OBSERVABLE, and it *"means the rod's OWN per-sensor time … arguably the
  architecturally correct reading, but a SEMANTIC choice."*

This rung makes the semantic choice, and attacks the match.

---

## §1 THE MAP — the 8 epoch-reading rules, their areas, and WHICH NODE each reads

Read off the committed seed sources (`seeds/*.json`) before any measurement. `input_epoch`
is one KEY spanning **five distinct node roles**:

| # | rule | area (186000 relabel) | reads `input_epoch` on | writes it on |
|---|---|---|---|---|
| 1 | `ct_area_input_epoch_tracks_completed_material` | `scheduler` | `task`, `area` | `area` |
| 2 | `ct_rearm_stale_on_area_epoch` | `scheduler` | `task`, `area` | `task` |
| 3 | `photon_apply_receptor_transduction` | `retina` | `task` | `receptor` (rod) |
| 4 | `photon_column_synthesizes_retinal_percept` | `retina` | `column`, `percept`, `rod`, `l`, `m`, `s` | `percept` |
| 5 | `retinal_mint_onset_2d` | `v1_onset` | `rod` | — |
| 6 | `retinal_mint_carve_2d` | `mt_carve` | `task` | — |
| 7 | `retinal_mint_motion_2d` | `mt_motion` | `task` | — |
| 8 | `retinal_mint_salience_2d` | `lip_salience` | `task` | — |

Two structural facts follow, and both are pre-registered as PREDICTIONS to be confirmed or
refuted by measurement:

* **P1 — rule 4 CANNOT MATCH on the 2-D sheet.** `_build_2d` mints no `RetinalPercept` and
  no `l/m/s` receptors, so `has_retinal_percept` / `l_receptor` / … do not exist there.
  It is woken every tick and can never fire. (Its where-clause is, verbatim, a
  four-receptor **synchronisation barrier on a shared clock** — the global clock written as
  a rule.)
* **P2 — `ct_area_effort_tracks_live_salience` IS NOT AN EPOCH READER.** It appears nowhere
  in the table. **Therefore Part 1 CANNOT fix Part 2**, and this rung predicts, before
  measuring, that per-sensor epoch leaves the 67.1% exactly where it is. The mission asks
  this question first; the seed source answers it, and the measurement will check it.

**What that rule actually is** (`seeds/cognitive_scheduler.json:402`): it matches
`area -has_task-> task`, and its where-clause and its effects **reference `area` only —
`task` is bound and never used.** Each of the N bindings then evaluates
`MaxOver(Neighbours(area, has_task), salience)`, which is O(N). The rule is therefore
**O(tasks²) per area, per tick**, and re-derives the *same* decision N times.

---

## §2 WHAT WILL BE BUILT — three mechanisms, all DEFAULT OFF

### Part 1 — `per_sensor_epoch` (a SEMANTIC change; NO whole-graph byte-identity claimed)

`input_epoch` stops being one clock stamped everywhere. Each sensor carries its own time
under its own name, advancing on its OWN change:

1. **The retina root's clock is the RETINA's**, written as `retina_epoch`, not
   `input_epoch`. No rule reads the root's `input_epoch` (187000's isolation probe); this
   removes the single write that took 0 dirty rules to 8.
2. **The rod's clock is the ROD's.** `retina_onset_batch` stamps a rod's epoch **only when
   that cell is NOT settled** by 185000's exact four-clause bitwise predicate (EMA at its
   float fixed point ∧ drive bit-equal ∧ response bit-equal ∧ **no onset would mint**).
   *Correctness argument, pre-registered:* on a settled cell the onset rule's own
   threshold clause is false, so the epoch it reads is unobservable there — the epoch can
   only lag on a cell that provably cannot mint. This is NOT 185000's Branch-B freezing:
   nothing is deferred, no state is frozen, the cell is fully processed; only the
   bookkeeping stamp is withheld, and only when withholding it is provably unobservable.
3. **The rod's epoch gets its own KEY, `rod_epoch`**, in per-sensor seed variants of
   `photon_retina` / `retinal_onset_2d` (loaded INSTEAD of the base seeds, only under the
   flag — the same context-driven seed selection `visual_motion` already uses). A shared
   key IS a shared clock; this is what actually decouples the areas at the dirty index's
   KEY granularity. The 2-D cell's clock likewise becomes `column_epoch`.

### Part 2 — `binding_projection` (a DROPPABLE BYTE-IDENTICAL MIRROR; identity IS claimed)

An engine flag. For a rule where (a) at least one match variable is referenced by
**neither** the where-clause **nor** any effect, and (b) every effect is
`SetAttr` / `SetAttrIfDifferent` / `AddEdge` (no `AddNode`, no `ReplaceValue`, no delete),
the binding set is **deduplicated on the projection to the referenced variables**. Var
collection reuses the existing generic `term::children` walk, which *cannot miss* a `Var`
(over-collection is safe — it only declines the optimisation).

This does **not change what the rule decides**: every dropped binding has identical
where-truth and identical effects to the one kept, and the kept effects are idempotent, so
the resulting graph is bit-identical. It removes the re-derivation, not the decision.

**No new `Term` enum variant. `runners/dsl/src/term.rs` diff MUST be empty.**

---

## §3 PRE-REGISTERED CRITERIA — every threshold fixed HERE, before any number

| id | claim | threshold |
|---|---|---|
| **C1** | **OFF ≡ the committed engine, WHOLE-GRAPH byte-identical** (primary gate) | float-exact dumps identical, base engine vs rung engine, **5/5** workloads (`vision_carve`, `scheduler`, `quiet_areas`, `conversation`, `doom_accel_160x120`) |
| **C2a** | Part 2 alone (`binding_projection` ON, per-sensor OFF) is a **droppable byte-identical mirror** | float-exact whole-graph dumps identical, **5/5** workloads |
| **C2b** | Part 2 preserves the landed 160×120 Doom carve | **exactly 4 polygons / union_iou 0.1215 / carve_precision 0.9784 / 0 false**, onset + rod digests identical |
| **C3a** | Part 1 ON: **every OBSERVABLE output identical** | landed carve exactly 4 / 0.1215 / 0.9784 / 0; onset-event stream digest identical; rod `activation` / `prev_activation` / `adaptation` / `caught_quanta` float-EXACT; held-surface build/decay curves identical |
| **C3b** | Part 1's whole-graph digest delta is **CONFINED TO THE EPOCH ATTRIBUTE** | the enumerated attribute-level diff contains ONLY `input_epoch` / `rod_epoch` / `retina_epoch` / `column_epoch` entries. **Any other key that moves is a FAILURE, not a caveat.** |
| **C4** | no new Term variant | `git diff --stat -- runners/dsl/src/term.rs` **EMPTY** |
| **F1** | **WRONG-EPOCH FALSIFIER** — an incorrect per-sensor epoch (one that fails to advance when its sensor genuinely changed) MUST break an observable output | onset stream **or** carve **DIVERGES** from the committed arm. If it does not, the check is vacuous and C3a is withdrawn. |
| **F2** | **NO FREE LUNCH** — 100% of the scene changing every tick | per-sensor / committed per-tick cost ratio **≥ 0.95** (same or slightly more) |
| **H1** | **dirty AREAS drop below 6 on a partially-changing scene** (187000 measured a flat 6/6) | **< 6 dirty areas at ≥ one change fraction in {0%, 1%, 5%, 25%}** on the shipped accel path; reported at every fraction, both arms |
| **H2** | **the per-tick vision cost ACTUALLY DROPS** vs 187000's 2.88 ms | median per-tick settlement **≤ 0.75 × 2.88 ms = 2.16 ms** on the SAME 20×15 six-area workload 187000 measured, with both parts ON |
| **H3** | the expensive match stops dominating | `ct_area_effort_tracks_live_salience` share of rule time **< 20%** (from 67.1%) |
| **P2** | stated in §1: Part 1 alone does NOT fix Part 2 | measured — the rule's share with per-sensor ON and projection OFF stays **> 50%** |

**Protocol.** 187000's adapt-then-perturb discipline verbatim: hold a static frame until
the sheet has SETTLED, then change exactly `f` of the cells and measure the settlement
event that follows. Median of ≥5 builds × 6 probe ticks, spread reported. **RUN SOLO.**

---

## §4 ALLOWED NEGATIVES — declared in advance, not invented afterwards

All of the following are acceptable outcomes and will be reported plainly if measured:

* **(a)** per-sensor epoch decouples the areas but the time does NOT drop — report which
  term dominates instead;
* **(b)** the areas remain coupled by a **SECOND shared key / write class**. One is already
  suspected: on the NON-accel graph path the eye mints one `CognitiveTask` **carrying
  `input_epoch` as a birth attribute** per cell per tick, and `add_node` dirties every rule
  reading that key. If that is what holds the areas awake, it will be named and isolated
  exactly as 187000 named the root write;
* **(c)** `ct_area_effort_tracks_live_salience` genuinely must run every tick.

**No threshold above will be loosened, no definition of "dirty" relaxed, and no rule's
decision weakened.** A rule that decides differently is a different rule, not an
optimisation. 185000's lesson stands: skipping something not GENUINELY settled fabricates
signal (a frozen reference manufactured spurious onsets; carve precision 0.978 → 0.0).

---

## §5 CONTROLS

* **Oracle** `bash scripts/rung7_vision_bench.sh` — 0 failed, **BEFORE == AFTER**.
  (`main` reports 224/0 with `data/` present; a worktree without `data/` reports
  214/10/0 — both conditions reported.)
* **Cross-domain regression** `scripts/per_area_settlement_regression.sh` (34 named files,
  never a `-k` selector) BEFORE/AFTER, with the **SET of failing node ids compared**, not a
  count. Load-bearing: `input_epoch` is used by `reading_async_areas.json`,
  `literary_analysis_driving.json` and `cognitive_scheduler.json`, so this touches
  NON-VISION domains.
* **Gate** `tests/test_per_sensor_epoch_migrated.py`, self-contained, committed before
  reporting: OFF byte-identity, ON observable identity (incl. the landed carve), the
  wrong-epoch falsifier, no-free-lunch, and the dirty-area / cost claim.
* **Build safety.** Rust is built in THIS WORKTREE ONLY. Canonical
  `_native.abi3.so` md5 **`5e9de8eb43f9c7cff8b97374d652bf59`** verified UNCHANGED before
  and after. If Rust changes: **CANONICAL NEEDS REBUILD ON MERGE**, said loudly.
* Curves + raw under `results/per_sensor_epoch/`.

---

## §6 Seed block

**188000–188999.** No other block is used. Verbatim:

```
$ python3 scripts/seed_claim.py 188000 188999
SEED CLAIM 188000-188999: CLEAN -- no collision DETECTED.
  Scope: 888 files with seed sinks; 603 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

## §7 Provenance

`source_match ∈ {"own","shared"}` will be reported from `domains/engine_provenance.py`,
together with the base-engine and rung-engine fingerprints and the canonical `.so` md5
before and after.
