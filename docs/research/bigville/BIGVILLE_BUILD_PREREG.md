# BIGVILLE R12 — CONSTRUCTION: the tradesman builds, the town's physical form MUTATES — PRE-REGISTRATION

**Block 260000. Pre-registered BEFORE any recorded number.** Spec:
`BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` §2.8 (CONSTRUCTION / the mutable world) + §3 R12
(this gate). Builds ON R13 `bigville_land_world` (PLOTS / `owns` / build-requires-the-plot
/ trespass) and R7 `bigville_fin_world` (the BANK / reserves / interest) — imported
READ-ONLY (the R12 adapter SUBCLASSES `BigvilleLandWorld`, which subclasses
`BigvilleFinWorld`). Reuse ALL by import; edit no tracked file.

CONSTRUCTION is the physical-growth capstone: a TRADESMAN consumes RAW MATERIALS +
LABOUR over TIME to raise a durable BUILDING on an OWNED plot (R13 precondition — building
on unowned/others' land is refused/trespass), funded PERSONALLY or by a BANK LOAN (R7 — a
construction loan that accrues like a mortgage); existing buildings are MODIFIED/ADDED-ON;
the CHURCH EXPANDS if its donations suffice (a grounded lift of R9's fixed size); and — the
HEADLINE — a new/changed building MUTATES the persistent map-belief so nav RE-ROUTES around
it and perception's OCCLUSION updates. Every decision — consume / raise / trespass / fund /
loan / accrue / addon / wall-off / expand / demolish — is a seed RULE
(`bigville_build_construct` / `bigville_build_mutate`); the adapter only ingests graph data,
arms one-shots, runs the Rust `run_rules` fixpoint, reflects the `built` verdict into the
host grid (occlusion), and reads.

## Seed-claim (verbatim `scripts/seed_claim.py 260 260`, run before anything)

```
SEED CLAIM 260-260: CLEAN -- no collision DETECTED.
  Scope: 974 files with seed sinks; 683 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

(R12 seeds NO RNG — every rule/attr is deterministic graph data — so the claim is a
discipline formality; the rung introduces no stochastic sink.)

## What R12 adds (graph-native, ZERO new Rust)

Two additive, `self_load_only` seeds, composing ONLY existing DSL Terms (`Attr` / `Plus` /
`Minus` / `Times` / `IDiv` / `Eq` / `Gte` / `Gt` / `Lt` / `Not` / `And` / `add_node` /
`del_node` / `add_edge` / `del_edge` / `set_attr`). LAND stays R13-CONSERVED — **no rule
mints or destroys a `Plot`**; construction only ADDS `Building` / `BuildLoan` nodes and
mutates map-cell attrs. No new Rust — `runners/dsl` diff EMPTY; canonical `.so` md5
UNCHANGED.

- **`seeds/bigville_build_construct.json`** (7 rules) — the construction economy.
  - **`bb_loan`** — a construction LOAN from the R7 bank: builder `wants_loan`, principal
    ≤ reserves, no loan yet → reserves −= principal, builder coin += principal, mint a
    `BuildLoan{balance, rate_bp}`.
  - **`bb_loan_accrue`** — interest accrues LIKE A MORTGAGE (the `bf_accrue` mirror):
    `balance' = IDiv(balance·(10000+rate_bp), 10000)` — multiplicative, INTEGER coin (the
    cross-frame base; the rate intensional, the balance observed stepped).
  - **`bb_fund`** — PERSONAL funding: pay `build_cost` from coin (savings OR loan proceeds)
    iff affordable → `funded=1`. DISJOINT control: `coin < build_cost` → no fire → not funded.
  - **`bb_consume`** — ONE construction tick: builder builds an OWNED, FUNDED, unfinished
    plot with a CONSTRUCTION skill (`level ≥ 1`) and enough timber+stone → consume materials,
    `progress += skill.level` (speed ∝ skill), `tick_armed` makes it ONE step per tick
    (multi-tick TIME). Ablate MATERIALS / SKILL / FUNDING → no match → no build.
  - **`bb_raise`** — COMPLETE + mutate the map (HEADLINE): `progress ≥ required` on an owned
    funded plot → `built=1`, mint a `Building`, and MARK the plot's map cell
    `blocked`+`occludes` (the RULE mutating the map-belief).
  - **`bb_trespass`** — building on ANOTHER'S land is refused = TRESPASS (owner ≠ builder →
    flag, build NOT applied; unowned land matches NEITHER → refused as absence).
  - **`bb_addon`** — MODIFY / ADD-ON: the owner extends a building on his own plot with more
    materials → `size`+`capacity` grow.

- **`seeds/bigville_build_mutate.json`** (3 rules) — the MUTABLE WORLD.
  - **`bbnav_wall_off`** — THE mutable-world mechanism: any `adj` edge touching a `blocked`
    cell is removed, so the existing `bigville_move_nav` Bellman flood (`mv_relax`) RE-ROUTES
    around the new building by construction (unknown = absence). Runs in the SAME substrate as
    nav → nav re-queries the mutated belief. Idempotent.
  - **`bb_church_expand`** — INSTITUTIONAL expansion, income-gated: an Institution's
    `capacity`+`size` grow IFF `funds ≥ expand_cost` (a grounded lift of R9's fixed size);
    control `funds < cost` → no expansion.
  - **`bb_demolish`** — remove a building → the cells REVERT (clear `built`/`blocked`/
    `occludes`, drop the `Building`); the adapter re-establishes the cell's walkable
    adjacency (mechanical re-ingest).

The rules are pinned **`batch: false`**. The adapter (`worlds/bigville_build_world.py`)
subclasses `BigvilleLandWorld` by import, holds NO decision: it registers
`Building`/`BuildLoan`/`Institution`/materials graph data + the plot↔map-cell `on_cell` edge
(ingest), arms a one-shot / wires a transient edge, runs `run_rules`, reflects `built` into
the host grid (the `_apply_hop` pattern), re-adds adjacency on demolish, and reads.

## Pre-registered GATES (each with its control + abandon/narrow criterion)

`tests/test_bigville_build_migrated.py`.

### G-build-needs-materials+skill+time
- **`test_build_consumes_materials_skill_time`** — skill=2, required=6 → 3 ticks; mat_cost=2
  → 6 timber+stone consumed; a `Building` minted; the map cell blocked. **Ablations (each
  load-bearing):** **`test_ablate_materials_no_build`**, **`test_ablate_skill_no_build`**,
  **`test_ablate_time_incomplete`** — remove any one → NO complete building.
  - **Abandon/narrow:** if a building rises with a material / skill / time factor missing, that
    factor is NOT load-bearing — report which.

### G-financed-build
- **`test_personal_funding`** — the cost is paid from SAVINGS (coin drops), no loan.
  **`test_loan_funded_build_accrues`** — a no-savings builder takes a BANK LOAN → reserves
  drop, builder coin rises, the build funds from proceeds, and the loan ACCRUES (100 → 110 at
  10%). **CONTROL — `test_no_funds_no_loan_no_build_control`** — insufficient savings + no loan
  → funded 0 → NO build.
  - **Abandon/narrow:** if a build proceeds unfunded, funding is not load-bearing.

### G-mutable-world (HEADLINE)
- **`test_build_reroutes_nav_and_updates_occlusion`** — baseline: a resident inside the office
  reaches the square (nav routes through the door) and Mary sees in. Build a house ON the door
  chokepoint → the resident is SEALED IN (nav re-routes / cannot pass) and Mary's LOS is BROKEN
  (occlusion updated). Demolish → both REVERT.
  - **Abandon/narrow:** if nav still passes a built cell, or occlusion does not update, the
    mutable-world claim is FALSE — report which half fails.

### G-church-expands-if-funded
- **`test_church_expands_when_funded`** — donations tip funds over the cost → capacity+size
  grow, funds drop. **CONTROL — `test_church_no_expand_unfunded_control`** — funds below cost →
  NO expansion.
  - **Abandon/narrow:** if the church expands unfunded, the income gate is not load-bearing.

### G-modify / add-on
- **`test_addon_extends_building`** — extend an existing building → size+capacity grow,
  materials consumed.

### G-trespass
- **`test_build_on_others_land_is_trespass`** — a non-owner on an owned plot → trespass flag,
  NOT built. **`test_build_on_unowned_land_refused`** — no owner → refused as absence.
  - **Abandon/narrow:** if a non-owner builds on land he does not own, the R13 precondition is
    not enforced.

### G-growth-loop (MEASURE-FIRST)
- **`test_growth_loop_raises_carrying_capacity`** — three incoming households each build a
  house → the built stock (carrying-capacity proxy) rises 0 → 3, organically.
  `scripts/bigville_build_run.py` measures a SUSTAINED arm (organic growth, coin conserved)
  and a debt-financed BOOM/BUST arm (interest compounds past what the builders hold — a
  natural punctuation, R10) → `results/bigville_build/summary.json`. **Reported, not tuned.**
  - **Honest residual:** demonstrated at small N on the fixed scaffold town — NOT swept to 200;
    immigration/birth inflow, carrying-capacity balance vs consumption (R5), and a full
    boom→bust→recovery time-series are deferred to the integrative capstone (R10). This rung
    gates the MECHANISM, not the macro dynamics.

### G-discipline (source-audit)
- **`test_no_python_agent_decision_source_audit`** — the TEN construction decisions are the
  exact rule-name set; the adapter runs/authors no Python rule engine; decision parameters
  (`funded`, `trespass`, `progress`, `required`, `expand`, `blocked`) appear only in seeds,
  never an adapter `if`. **`test_seeds_are_self_load_only_and_no_new_rust`** — both seeds
  `self_load_only:true`; no rule mints/destroys a `Plot` (land R13-conserved); only
  `bb_demolish` drops a node (a `Building`); no `Div` into a coin/reserves/balance attr; no
  new Rust.

## Discipline (this rung)

Additive-only, ONE prefix `bigville_build_`. NEW files ONLY (`seeds/bigville_build_*.json`,
`worlds/bigville_build_world.py`, `scripts/bigville_build_*.py`,
`tests/test_bigville_build_migrated.py`, `BIGVILLE_BUILD_PREREG.md`,
`BIGVILLE_BUILD_RESULTS.md`, `results/bigville_build/summary.json`). Edits NO tracked file
(R13/R7 imported read-only). Seeds `self_load_only` → an additive rung cannot regress another
suite. ZERO new Rust (`git diff` on `runners/dsl` EMPTY, incl `term.rs`); canonical shared
`.so` md5 `fd82dc2978dbb055496dd82390ac2ebe` UNCHANGED start→end; no `.so` committed. Own-engine
provenance passes (`source_match ∈ {own, shared}`, never a pinned md5). Gates run inline
(`test_bigville_build_migrated` + `test_failure_baseline_migrated` 11/11 +
`test_engine_provenance_migrated` 7/7); the ~43-min oracle benches are NOT run (an additive
`self_load_only` rung cannot regress them; the fast baseline gate + additive discipline suffice,
per the 2026-07-29 directive).
