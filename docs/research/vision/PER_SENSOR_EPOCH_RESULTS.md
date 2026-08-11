# PER-SENSOR EPOCH — the global clock is cut out of the eye, and the 67% match was never the clock's fault (results)

**Block 188000.** Prereg `PER_SENSOR_EPOCH_PREREG.md`, committed **ALONE**
(`311f2544c7153794b9ccaf8123ba7539c8c39503`) BEFORE any number here.
Base `main` @ `f3cc8a482b2a7502c0d09556a77dc39f8662e36a` (the 187000 ledger).
Seed block **188000–188999**, `seed_claim` **CLEAN** (verbatim in prereg §6).
**This rung BUILDS Rust. CANONICAL NEEDS REBUILD ON MERGE.**

---

## Headline

> **The global clock is CUT — and the clock was never what the time was going
> in.** Two mechanisms, built separately, measured separately, and they do not
> help each other:
>
> **PART 1 — per-sensor epoch (SEMANTIC, default OFF).** 187000's isolation probe
> — settle the eye, then make exactly ONE write, the retina root's clock — went
> **0 → 8 dirty rules across 6 areas.** With each sensor's clock carrying its own
> KEY it goes **0 → 0 dirty rules, 0 areas.** On the shipped 160×120 Doom
> accelerator the dirty-area count falls from a flat **6 of 6 to 2 of 2**
> (`retina`, `v1_onset`) at **every** scene-change fraction, 0% through 100%.
> Every observable is identical — the landed carve is exactly **4 / 0.1215 /
> 0.9784 / 0**, the onset stream digest is unchanged, and the whole-graph
> attribute diff has **`changed_value: []`: NOT ONE attribute value moves.** The
> only delta is the epoch attribute's NAME, on exactly three sensor node types.
>
> **PART 2 — the expensive match (a DROPPABLE BYTE-IDENTICAL MIRROR, default
> OFF).** 187000's 67.1% rule, `ct_area_effort_tracks_live_salience`, **binds
> `task` and references it in NEITHER its where-clause NOR its effects** — so it
> re-derives one O(tasks) `MaxOver` once per task: **O(tasks²), per area, per
> tick.** Deduplicating the binding set on the variables a rule actually
> references collapses it to O(tasks): its cost falls **15,161 → 813 µs
> (18.6×)**, its share of rule time **67.0% → 9.8%**, and the per-tick settlement
> on 187000's own workload falls **2.86 ms → 1.03 ms (2.77×)** — byte-identical
> on 5/5 workloads.
>
> **AND THE PREREGISTERED PREDICTION HELD.** The prereg stated, from the seed
> source and BEFORE any measurement, that `ct_area_effort_tracks_live_salience`
> is **not** an epoch reader and therefore **Part 1 cannot fix Part 2**.
> Measured: with per-sensor epoch ON and projection OFF the rule still takes
> **68.5%**. It cannot; it doesn't.
>
> **AND THE DECLARED NEGATIVE IS ALSO THE RESULT.** Cutting the accel path's
> dirty areas 6 → 2 buys **NO time** (11.2 → 12.5 ms/tick, slightly WORSE),
> because the areas that stopped waking were nearly free and the ones left are
> the expensive ones. The attribution names the next object exactly: **three
> rules, woken every tick, each enumerating O(cells), each `progressed 0`** —
> and one of them, `photon_column_synthesizes_retinal_percept`, **CANNOT MATCH
> ON THE 2-D SHEET AT ALL** (prereg prediction P1, confirmed) yet burns 22% of
> the settlement.

---

## §1 THE MAP — the 8 epoch-reading rules, and which NODE each reads

Read off the committed seeds BEFORE building anything (prereg §1). `input_epoch`
was ONE key spanning **five distinct node roles**:

| # | rule | area | reads `input_epoch` on | writes it on |
|---|---|---|---|---|
| 1 | `ct_area_input_epoch_tracks_completed_material` | `scheduler` | `task`, `area` | `area` |
| 2 | `ct_rearm_stale_on_area_epoch` | `scheduler` | `task`, `area` | `task` |
| 3 | `photon_apply_receptor_transduction` | `retina` | `task` | `receptor` (rod) |
| 4 | `photon_column_synthesizes_retinal_percept` | `retina` | `column`, `percept`, `rod`, `l`, `m`, `s` | `percept` |
| 5 | `retinal_mint_onset_2d` | `v1_onset` | `rod` | — |
| 6 | `retinal_mint_carve_2d` | `mt_carve` | `task` | — |
| 7 | `retinal_mint_motion_2d` | `mt_motion` | `task` | — |
| 8 | `retinal_mint_salience_2d` | `lip_salience` | `task` | — |

Rule 4's where-clause is, verbatim, a four-receptor **synchronisation barrier on
a shared clock** (`rod.input_epoch == column.input_epoch ∧ l == column ∧ m ==
column ∧ s == column`). The global clock, written as a rule.

**P1 (preregistered, CONFIRMED): rule 4 cannot match on the 2-D sheet.**
`_build_2d` mints no `RetinalPercept` and no `l/m/s` receptors. It is woken every
tick and can never fire — and it costs **22.1% of the shipped path's settlement**
(§6).

**P2 (preregistered, CONFIRMED): `ct_area_effort_tracks_live_salience` is not in
this table, so Part 1 cannot fix Part 2** (§5).

After the split (`per_sensor_epoch` ON), measured with `rules_reading_attr`:

| key | readers | areas |
|---|---|---|
| `input_epoch` | **6** (was 8) | scheduler ×2, retina, mt_carve, mt_motion, lip_salience |
| `rod_epoch` | 2 | retina, **v1_onset** |
| `column_epoch` | 1 | retina |
| `percept_epoch` | 1 | retina |

---

## §2 WHAT WAS BUILT — three pieces, all DEFAULT OFF

### Part 1 — `per_sensor_epoch` (eye context flag; SEMANTIC)

1. **The retina root's clock is the RETINA's** — written as `retina_epoch`.
   No rule reads the root's epoch at all; that one write was 187000's whole
   isolation probe.
2. **The rod's clock is the ROD's** — key `rod_epoch`, and in
   `retina_onset_batch` it is stamped **only when the cell is NOT settled** by
   185000's exact four-clause bitwise predicate (EMA at its float fixed point ∧
   drive bit-equal ∧ response bit-equal ∧ **no onset would mint**).
   *Why that is exact, not a shed:* on a settled cell the onset rule's own
   threshold clause is false, so the epoch it reads there is unobservable.
   **Nothing is frozen or deferred** — the cell is fully processed and every
   state attribute is written; only the bookkeeping stamp is withheld, and only
   where withholding it is provably invisible. This is NOT 185000's Branch B.
3. **The cell's clock is the CELL's** — key `column_epoch`; the percept's is
   `percept_epoch`.
4. **Seed variants** `photon_retina_per_sensor` / `retinal_onset_2d_per_sensor`,
   emitted by `tools/build_per_sensor_epoch_seeds.py` (a mechanical key rewrite
   of the committed seeds — no rule added, removed, reordered or otherwise
   altered) and loaded INSTEAD of their base under the flag, exactly as
   `visual_motion` already selects `retinal_motion_2d`.
5. **`photon_retina_wrong_epoch`** — the FALSIFIER variant, in which the rod's
   clock is a CONSTANT.

### Part 2 — `binding_projection` (engine flag; a DROPPABLE BYTE-IDENTICAL MIRROR)

`RewriteRule::project_vars` is `Some(vars)` iff (a) at least one match variable
is referenced by **neither** the where-clause **nor** any effect, and (b) every
effect is `SetAttr` / `SetAttrIfDifferent`. With the flag on, the binding set is
deduplicated on that projection.

**Soundness.** Two bindings agreeing on `vars` agree on the where-clause's truth
(it reads nothing else that is bound) and produce identical effects on the same
node with the same resolved value; those effects are idempotent, so applying one
is bit-identical to applying all. **It removes a RE-DERIVATION, never a
DECISION.** Variable collection reuses `collect_term_vars`, the generic
`term::children` walk that cannot MISS a `Var` (over-collection merely declines
the optimisation). The effect whitelist is deliberately narrow: `AddNode` mints
one node PER BINDING, so projecting it would genuinely change the graph.

Where it applies: (i) post-match dedup in both match paths; (ii) on the COLD
path, for **one-match-edge rules only**, the enumeration runs with the
where-clause stripped (a single edge scan — a k-edge join would risk a
cross-product blow-up), one representative per projection is kept, and the
where-clause is evaluated on the representatives via a zero-match-edge rule with
the representative pre-bound (the shape the incremental path already uses);
(iii) the same pre-matcher skip on the incremental path's drivers.

**The cold path is the one that matters here, and that is measured, not
assumed:** `SUBSTRATE_TRACE_RULE` shows `ct_area_effort_tracks_live_salience`
takes `FULL re-match (cold/invalidated cursor); bindings found = 0` on **every**
tick, because `prune_settled_tasks` deletes tasks and invalidates its cursor.
The whole 67% is where-clause evaluation inside the matcher.

**NO new Term enum variant. `runners/dsl/src/term.rs` diff is EMPTY.**

### `projection_overaggressive` — the falsifier

Projects on the EMPTY variable set (fire once per visit, however many hubs
match). MUST break byte-identity.

---

## §3 THE PRE-REGISTERED CRITERIA, one by one

| id | threshold | measured | verdict |
|---|---|---|---|
| **C1** | OFF ≡ base engine, whole-graph float-exact, 5/5 | **5/5 IDENTICAL** (base `077e425770bb` vs rung `de3f223a527d`) | ✅ |
| **C2a** | `binding_projection` ON byte-identical, 5/5 | **5/5 IDENTICAL** | ✅ |
| **C2b** | landed 160×120 carve exact under projection | **4 / 0.1215 / 0.9784 / 0**, onset + rod digests identical | ✅ |
| **C3a** | per-sensor ON: every OBSERVABLE identical | landed carve **4 / 0.1215 / 0.9784 / 0**; onset digest `f5375014f2dcb8f2` in all four arms; rod state digest `d777e3d8a7012a55` in all four arms; graph-path onset stream **600 = 600**, same digest | ✅ |
| **C3b** | whole-graph delta CONFINED to the epoch attribute | **`changed_value: []`** — not one value moves; same 38,485 nodes, same ids; only `(Retina,input_epoch)/(RetinalColumn,input_epoch)/(Photoreceptor,input_epoch)` → `retina_epoch`/`column_epoch`/`rod_epoch` | ✅ |
| **C4** | `term.rs` diff empty | empty | ✅ |
| **F1a** | WRONG-EPOCH falsifier breaks an observable | graph-path onsets **600 → 300**, digest `a2e997b4…` → `71d597fe…` | ✅ |
| **F1b** | WRONG-PROJECTION falsifier breaks byte-identity | **DIVERGES on 3/5**, including the VISION workload `vision_carve` | ✅ |
| **F2** | no-free-lunch ratio ≥ 0.95 | **1.009** | ✅ |
| **H1** | dirty AREAS < 6 at ≥1 change fraction | **2 of 6 at EVERY fraction 0%→100%** on the shipped accel path | ✅ |
| **H2** | per-tick ≤ 0.75 × 2.88 ms on 187000's workload | **1.028–1.062 ms** vs committed 2.840–2.859 ms → **ratio 0.364** | ✅ |
| **H3** | expensive rule share < 20% | **67.0% → 9.8%** (15,161 → 813 µs, 18.6×) | ✅ |
| **P2** | per-sensor alone does NOT fix the match (>50%) | **68.5%** | ✅ (prediction held) |

---

## §4 PART 1 — the isolation probe, and the areas

187000's probe verbatim: settle the eye to zero dirty rules, then make exactly
ONE write — the retina ROOT's clock, what `submit_photons_2d` does first,
unconditionally, outside every accelerator flag.

| arm | root key | dirty rules | dirty areas |
|---|---|---|---|
| committed | `input_epoch` | **0 → 8** | **6**: scheduler, retina, v1_onset, mt_carve, mt_motion, lip_salience |
| per-sensor | `retina_epoch` | **0 → 0** | **0** |

### The sweep, shipped Doom accelerator (160×120, `retina_accel` ON)

Median of 3 builds × 4 probe ticks; 187000's adapt-then-perturb protocol.

| scene changed | arm | dirty AREAS | dirty rules | ms / tick |
|---|---|---|---|---|
| 0 % | committed / projection | **6** | 8 | 11.73 / 12.09 |
| 0 % | per-sensor / both | **2** | 3 | 12.81 / 12.94 |
| 1 % | committed / projection | **6** | 8 | 12.30 / 12.20 |
| 1 % | per-sensor / both | **2** | 3 | 12.80 / 12.85 |
| 5 % | committed / projection | **6** | 8 | 12.14 / 12.34 |
| 5 % | per-sensor / both | **2** | 3 | 12.63 / 12.78 |
| 25 % | committed / projection | **6** | 8 | 12.17 / 12.18 |
| 25 % | per-sensor / both | **2** | 3 | 12.74 / 13.05 |
| 100 % | committed / projection | **6** | 8 | 11.76 / 12.14 |
| 100 % | per-sensor / both | **2** | 3 | 12.81 / 12.76 |

**The areas decouple; the time does not.** That is prereg §4 outcome (a),
declared in advance, and §6 says exactly where the time is instead.

### Is the rod's clock actually the rod's own time? — measured

On a bit-repeatable input the receptor EMA reaches an exact float64 fixed point
(185000: t\* ≈ 71 at rate 0.4). Past it a settled rod's clock stops advancing:

| ticks held | noiseless sensor | Poisson sensor |
|---|---|---|
| 8 | 0 / 19,200 rod clocks lag | 0 / 19,200 |
| 40 | 0 / 19,200 | 0 / 19,200 |
| **80** | **19,200 / 19,200 (100%)** | 0 / 19,200 |
| 120 | 19,200 / 19,200 (100%) | 0 / 19,200 |

**Reported honestly: under the DEFAULT Poisson photon sensor the per-sensor
clock degenerates to the global one** — no cell is ever bitwise settled, exactly
as 185000 measured for the same exact predicate. On the Poisson path the
per-sensor epoch is therefore a per-sensor NAMING only, and the naming is what
buys the decoupling; the per-sensor TIME is real but only on a bit-repeatable
input. That is also why C3b's `changed_value` is empty: on the measured
protocol every rod is stamped every tick in both arms, so no VALUE differs.

---

## §5 PART 2 — the expensive match, and why Part 1 could not touch it

`ct_area_effort_tracks_live_salience` (`seeds/cognitive_scheduler.json:402`):
match `area -has_task-> task`; where and effects reference **`area` only**.
`MaxOver(Neighbours(area, has_task), salience)` is O(tasks), evaluated once per
binding, and there are O(tasks) bindings.

Per-rule cost on 187000's own settled workload (20×15 six-area retina, 12-tick
hold, 8 probe ticks):

| arm | rule ms/tick | wall ms/tick | `ct_area_effort…` share | its µs |
|---|---|---|---|---|
| committed | **2.830** | 5.704 | **67.0 %** | 15,161 |
| **per_sensor** | **2.833** | 5.704 | **68.5 %** | 15,522 |
| **projection** | **1.032** | 3.834 | **9.8 %** | **813** |
| both | 0.994 | 3.832 | 10.2 % | 815 |

**P2 held.** Per-sensor epoch moves it by nothing, as the prereg said it could
not: the rule is not an epoch reader.

### The settlement sweep, 20×15 GRAPH path — the number 187000 measured flat

Median of 5 builds × 6 probe ticks. 187000 reported 2.88–2.91 ms in **every cell
of this table, both arms**.

| scene changed | committed | projection | per_sensor | both |
|---|---|---|---|---|
| 0 % | 2.855 ms | **1.044** | 2.841 | **1.029** |
| 1 % | 2.840 ms | **1.060** | 2.847 | **1.040** |
| 5 % | 2.850 ms | **1.045** | 2.851 | **1.028** |
| 25 % | 2.852 ms | **1.062** | 2.855 | **1.038** |
| 100 % | 2.859 ms | **1.055** | 2.853 | **1.036** |

Dirty areas are **6 of 6 and dirty rules 13 in every cell**, unchanged by either
flag. **On the graph path the areas stay coupled — and the SECOND coupling was
preregistered (§4(b)) and is confirmed:** the eye mints one `CognitiveTask` per
cell per tick **carrying `input_epoch` as a birth attribute**, and `add_node`
dirties every rule reading that key. Six of the eight readers legitimately read a
TASK's epoch, so no renaming can decouple them — that epoch genuinely is the
scheduler's clock. The per-sensor split still removes two readers from the
`input_epoch` set (`retinal_mint_onset_2d`, `photon_column_synthesizes_retinal_percept`);
it just cannot get the AREA count below 6 while a task mint wakes five areas.

**H2 is met by Part 2 alone, on the exact workload 187000 measured: 2.86 → 1.03
ms, 2.77×.**

---

## §6 WHERE THE ACCEL PATH'S TIME ACTUALLY IS — the next object, named

Rule costs on the shipped 160×120 accelerator, settled, 4 probe ticks:

| arm | settle ms/tick | share | rule | processed | **progressed** |
|---|---|---|---|---|---|
| committed | 11.22 | **68.3 %** | `retinal_mint_onset_2d` | 4 | **0** |
| | | **22.1 %** | `photon_column_synthesizes_retinal_percept` | 4 | **0** |
| | | 9.5 % | `photon_apply_receptor_transduction` | 4 | **0** |
| per-sensor | 12.54 | 62.1 % | `retinal_mint_onset_2d` | 4 | **0** |
| | | 27.2 % | `photon_column_synthesizes_retinal_percept` | 4 | **0** |
| | | 10.7 % | `photon_apply_receptor_transduction` | 4 | **0** |

**All three progress ZERO, every tick, and all three enumerate O(cells).** On the
accelerator path the sheet is settled in Rust, so there are no per-cell
`CognitiveTask`s at all — `photon_apply_receptor_transduction` and
`retinal_mint_onset_2d` scan 19,200 columns/rods to find no task, and
`photon_column_synthesizes_retinal_percept` **cannot match on a 2-D sheet under
any circumstances** (no percepts, no l/m/s receptors — prereg P1). That is why
cutting the dirty set 8 → 3 buys nothing: the three that remain ARE the cost, and
they are all in the two areas the per-sensor arm keeps awake.

This is the same shape of finding 187000 produced, one level deeper, and it names
the next lever without ambiguity: **an empty-match-set proof.** A rule whose join
is provably empty for the current graph should not be enumerated at all — the
`match_type` / edge-count information to decide that is already in the engine.
Neither dirty-propagation precision nor binding projection can reach it: these
rules are genuinely dirty, and their bindings are genuinely distinct.

---

## §7 Provenance & discipline

- **SEPARATE prereg commit** `311f2544c7153794b9ccaf8123ba7539c8c39503`,
  `PER_SENSOR_EPOCH_PREREG.md` alone, BEFORE any number.
- **Seed block 188000–188999**, `seed_claim` CLEAN.
- **`source_match = "own"`** for every number in this document
  (rung engine `de3f223a527d`, built in THIS worktree); the C1 base-side run
  reports `source_match = "shared"` against the canonical tree, as intended —
  that is what makes it a base measurement.
- **Oracle** `bash scripts/rung7_vision_bench.sh` — **BEFORE 214 passed / 10
  skipped / 0 failed**, **AFTER 214 / 10 / 0**. BEFORE == AFTER. (Documented
  worktree-without-`data/` condition, identical to 187000's; `main` reports
  224/0 with `data/` present.) The BEFORE arm is a genuine base run: base Rust
  source + base `photon_eye.py` checked out, worktree artifact removed, engine
  resolving to the canonical build with `Rust source identical`.
- **Cross-domain regression** `scripts/per_area_settlement_regression.sh`
  (34 named files, never a `-k` selector) — **BEFORE 23 failed / 277 passed /
  5 skipped**, **AFTER 23 / 277 / 5**, and the SET of failing node ids is
  IDENTICAL — the sorted `diff` of the two lists differs in exactly one line,
  the summary's own wall-clock (`293.18s` vs `290.40s`), and in **no node id**.
  The set is identical to 186000's and 187000's list:
  3 in `test_cortices_tick.py`,
  `test_composer_driver_migrated::test_question_driver_parity`, 5 in
  `test_gap_awareness_migrated.py`, 5 in `test_elaboration_migrated.py`, 9 in
  `test_topic_route_selfheal_migrated.py`.
- **Gate** `tests/test_per_sensor_epoch_migrated.py` — **9 passed**.
- **Rust built in this worktree ONLY.** Canonical `.so` md5
  **`5e9de8eb43f9c7cff8b97374d652bf59` before and after**; rung engine md5
  `69410e46bfaf7750010987dea947a145`. **See §9 residual 6 — a symlink incident
  occurred and was detected and repaired by exactly this check.**
  **CANONICAL NEEDS REBUILD ON MERGE.**
- **NO new Term enum variant** — `git diff --stat -- runners/dsl/src/term.rs`
  is EMPTY.
- Raw: `results/per_sensor_epoch/per_sensor_epoch.json`.

---

## §8 Proposed VISION_PROTOCOL ledger row

`188000 | PER-SENSOR EPOCH (each sensor's clock gets its own KEY + advances on its own change; per_sensor_epoch, seed variants, default OFF) + BINDING PROJECTION (dedup a rule's bindings on the vars its where+effects actually reference; binding_projection, default OFF, droppable byte-identical mirror) | 187000 measured the six areas welded by ONE shared attribute key input_epoch (one root write = 0->8 dirty rules / 6 areas) AND 67.1% of rule time in one rule that never fires | THE CLOCK IS CUT: isolation probe 0->8/6 areas becomes 0->0/0 areas; shipped 160x120 accel dirty areas 6->2 at EVERY change fraction 0-100%; observables EXACT (landed carve 4/0.1215/0.9784/0, onset digest and rod-state digest identical in all four arms, graph-path onsets 600=600) and the whole-graph attribute diff has changed_value=[] — the ONLY delta is the epoch attribute's NAME on 3 sensor types. AND THE MATCH: ct_area_effort_tracks_live_salience binds `task` and uses it NOWHERE — O(tasks^2); projection makes it O(tasks), 15161->813us (18.6x), 67.0%->9.8%, settlement 2.86->1.03 ms (2.77x) on 187000's own workload, byte-identical 5/5 | PREREGISTERED PREDICTION P2 HELD: the 67% rule is not an epoch reader, so Part 1 CANNOT fix Part 2 — measured 68.5% with per-sensor alone. FALSIFIERS BOTH BIT: wrong rod clock 600->300 onsets; over-aggressive projection diverges 3/5 incl. a VISION workload. F2 no-free-lunch 1.009. DECLARED NEGATIVE: cutting accel dirty areas 6->2 buys NO time (11.2->12.5 ms) | Rust built in worktree (canonical .so md5 5e9de8eb UNCHANGED, REBUILD ON MERGE); term.rs EMPTY; gate test_per_sensor_epoch_migrated 9/9; oracle BEFORE==AFTER 214/10/0; 34-file regression 23/277/5 with an IDENTICAL failing-id set; source_match own | the time on the accel path is THREE rules woken every tick, each O(cells), each progressed 0 — one of which (photon_column_synthesizes_retinal_percept, a four-receptor synchronisation barrier on a shared clock) CANNOT MATCH on a 2-D sheet at all and still burns 22%; the next lever is an EMPTY-MATCH-SET proof, which no dirty precision and no binding projection can reach. On the GRAPH path a SECOND coupling holds the areas: the per-cell CognitiveTask mint carries input_epoch as a birth attribute, and six of the eight readers legitimately read a TASK's epoch. Under the Poisson sensor the per-sensor CLOCK degenerates to the global one (no cell is ever bitwise settled) — the naming decouples, the timing does not bite there`

---

## §9 Honest residuals

1. **The two wins are on different paths and neither causes the other.**
   Part 2's 2.77× cost drop is on the 20×15 GRAPH path (187000's own workload);
   Part 1's 6 → 2 area decoupling is on the 160×120 ACCEL path. On the graph
   path the areas stay 6/6; on the accel path the time does not fall. The
   mission's headline — "cost falls AND areas < 6, together, on one path" — is
   **NOT** achieved, and this document does not claim it. Reported as the
   decomposition it is.
2. **Per-sensor epoch makes the accel path ~9–12% SLOWER** (11.2 → 12.5 ms/tick;
   the same three rules cost more micros in the per-sensor arm). The direction is
   consistent with F2 (no free lunch), but the magnitude is not explained here.
   It is not measurement noise: it reproduces across the whole sweep.
3. **Per-sensor TIME is inert under the default Poisson sensor** (0/19,200 rod
   clocks lag at every hold). It is real on a bit-repeatable input (100% lag past
   t\*≈71), which is 185000's domain and not the shipped sensor's. On the shipped
   path what decouples the areas is the per-sensor NAMING alone.
4. **The per-sensor variant seeds duplicate their base seeds.** They are emitted
   mechanically by `tools/build_per_sensor_epoch_seeds.py` and committed so the
   diff is readable, but an edit to `photon_retina.json` will not propagate until
   the tool is re-run. There is no gate on that.
5. **Binding projection's cold-path enumeration is restricted to
   one-match-edge rules.** Multi-edge rules get only the post-match dedup, which
   is correct but buys nothing, because their cost is inside the matcher. A k-edge
   rule with an unused variable is therefore NOT accelerated. Deliberate: stripping
   a pruning where-clause off a k-edge join to enumerate raw bindings risks a
   cross-product blow-up, which would be a much worse bug than the one being fixed.
6. **A SYMLINK INCIDENT OCCURRED, AND THE MANDATED CHECK CAUGHT IT.** During the
   BEFORE run the worktree's `runners/dsl/python/substrate_rs/_native.abi3.so`
   had been moved aside; something in the test path **re-created that name as a
   SYMLINK into the canonical tree**, and a later `cp` wrote THROUGH it,
   clobbering the canonical binary for ~1 minute. It was detected by the required
   md5 comparison and repaired byte-exactly from the canonical tree's own
   `runners/dsl/target/release/libsubstrate_rs.so`, which still held the original
   inode (md5 `5e9de8eb43f9c7cff8b97374d652bf59`, verified after repair). No
   measurement is affected — the BEFORE runs resolved to the base engine
   throughout (`Rust source identical`), and the clobber happened after they
   finished. **The hazard is worse than lesson 9 states: the symlink can appear
   after you have checked for it.** Check the md5, not the inode, and check it
   again at the end.
7. **`ct_ready_when_dependencies_settle`, `ct_supersede_older_uncommitted_task`
   and `photon_apply_receptor_transduction` are also projectable** and are
   therefore also affected by the flag. Byte-identity is gated on 5/5 workloads
   and the 34-file regression, but the tree contains rules this rung never
   exercised. The flag ships DEFAULT OFF.
8. **`quiet_areas` and `scheduler` produce the same dump digest**, inherited
   verbatim from 187000's workload set. Two of the five "workloads" are therefore
   one workload, and the identity claim is really 4-distinct.
