# BIGVILLE R13 — LAND: OWNERSHIP, THE MARKET, THE COMMONS — RESULTS

**Block 261000.** Built on base `a6bb0c0b62` (R1–R9 + R11 + R16). Prereg:
`BIGVILLE_LAND_PREREG.md`. Every gate landed with its pre-registered control. All
numbers below are from the committed engine — `source_match = shared`, canonical `.so`
UNCHANGED, `runners/dsl` diff EMPTY, ZERO new Rust.

LAND is the FOUNDATIONAL scarce asset, grounded graph-native: a `Plot` is a node,
OWNERSHIP is an `owns` edge, and **Σ Count(Plot) is INVARIANT** — no rule mints or
destroys a parcel; acquisition only MOVES `owns` edges over a fixed map. R7's mortgage
was "secured on the LAND+building" in PROXY (it moved only the house); R13 GROUNDS the
proxy — foreclosure now moves the LAND.

## Gate results

| Gate | Result |
|---|---|
| `test_bigville_land_migrated` | **16/16 PASS** |
| `test_failure_baseline_migrated` | **11/11 PASS** (enumerated-baseline arbiter) |
| `test_engine_provenance_migrated` | **7/7 PASS** (`source_match = shared`) |

### G-land-is-owned-and-conserved
- **`test_land_is_conserved_through_all_modes`** — a FIXED map of six parcels; Σplots
  stays **6** through BUY, CLAIM, GRANT, TAX-FORFEIT and ENCLOSURE-REVERSAL. No parcel
  minted or destroyed — every transfer is an `owns`-edge move.
- **`test_ownership_partitions_the_map`** — two rivals chase a market + a frontier; every
  parcel resolves to exactly one holder (Σ holdings == Σplots); `owner_of` asserts ≤1
  owner throughout.

### G-acquisition (buy / claim / grant) + the structural-exclusion control
- **BUY** — buyer 300→180, seller 0→120, `owns` moves, plot de-listed.
- **CLAIM (first-come)** — the first claimant takes the frontier parcel; the second is
  BLOCKED (`owned==0` guard); claimed land ceases to be frontier.
- **GRANT** — the council (`is_council`) transfers a council-held parcel to a recipient.
- **CONTROL `test_landless_cannot_acquire_structural_exclusion`** — all land owned,
  nothing listed, no frontier, no grant → a landless resident **with 1000 coin** who
  arms a buy AND a claim acquires **0**. Personal effort (even capital) cannot open land
  that is structurally closed.
- **CONTROL `test_buy_fail_cant_afford_control`** — coin < price → `bl_buy_fail`, no
  transfer, no coin spent.

### G-land-underlies-tenure+build (HEADLINE)
- **`test_build_requires_owning_the_plot`** — the owner builds (`built=1`); a non-owner
  on another's land → TRESPASS, not built; unowned frontier → refused (built stays 0,
  refusal as absence).
- **`test_foreclosure_transfers_the_land`** — a mortgage `secured_on_plot` the debtor's
  parcel + an income collapse → R7 forecloses (its own decision, over the house) and R13
  moves the LAND's `owns` edge debtor→bank. Σplots conserved (the parcel MOVED, was not
  destroyed). **CONTROL `test_owned_outright_keeps_the_land`** — the same shock on an
  owner with NO mortgage keeps his land: leverage on the LAND is the amplifier.
- **`test_tenure_derives_from_land`** — the landlord OWNS the plot (rents to the tenant
  via R7); the homeowner OWNS his plot; the renter owns NO land. R7 tenure is downstream
  of land ownership.

### G-land-concentrates + the structural floor
- **`test_land_concentrates_with_capital`** — the map starts DISTRIBUTED (N=6
  smallholders, one parcel each, `max_share = 1/6 ≈ 0.167`); a rich buyer sweeps the
  market → **`max_share = 1.0`**, the rich hold all six, the poor hold 0. Non-produced +
  finite → once bought, the land cannot be re-created for the poor.
- **`test_landless_escapes_only_structurally`** (the agency/structure bedrock, §0) — a
  landless resident's personal effort leaves him at **0**; then each STRUCTURAL lever
  hands him a parcel: **GRANT → 1**, **ENCLOSURE-REVERSAL + claim → 2**, **TAX-FORFEIT →
  GRANT → 3**. Σplots conserved throughout. **CONTROL `test_no_lever_stays_landless`** —
  with NO lever applied he stays at 0: the lever is what moves it.

### G-discipline (source-audit)
- **`test_no_python_agent_decision_source_audit`** — the **ten** land decisions are the
  exact rule-name set; the adapter runs/authors no Python rule engine; decision
  parameters (`for_sale`, `built`, `foreclosed`, `is_council`, `revert_armed`) appear
  only in rule `where` clauses, never an adapter `if`.
- **`test_seeds_are_self_load_only_and_conserve_land`** — both seeds `self_load_only`;
  **no effect uses `add_node`/`del_node`** (Σplots conserved at the SOURCE level); no
  coin attr set from a fractional `Div`; no new Rust.

## Discipline verification

| Check | Value |
|---|---|
| `runners/dsl` diff vs `a6bb0c0b62` | **EMPTY** |
| New Rust | **none** |
| Canonical `.so` md5 START | `fd82dc2978dbb055496dd82390ac2ebe` |
| Canonical `.so` md5 END | `fd82dc2978dbb055496dd82390ac2ebe` (**unchanged**) |
| `source_match` | **shared** (Rust source identical; `engine ada5f2aefc25`) |
| Additive-only, one prefix `bigville_land_` | yes (no tracked file edited) |
| Seeds `self_load_only` | yes (loaded only by the R13 adapter) |
| 43-min oracles (`per_area`, `rung7`) | **NOT run** (per SUPERVISOR+USER directive 2026-07-29: a purely-additive, no-Rust, `self_load_only` rung cannot regress other suites; fast baseline gate + additive discipline is sufficient) |

## The graph-native mechanism (all rules + seed data)

Two `self_load_only` seeds compose ONLY existing DSL Terms. The rules are pinned
`batch: false` (SEQUENTIAL one-match-per-pass, the `retire_duplicate_gap` precedent) so
a market SWEEP respects a shrinking BUDGET and CLAIM is FIRST-COME; the adapter arms ONE
acquisition per fixpoint (the safe primitive). Conservation is structural: no rule mints
a Plot node (audited at source) — the ONLY node minting is `add_plot` at adapter ingest
(the fixed map), never a decision.

- **`bigville_land_market.json`** — `bl_buy` / `bl_buy_fail` / `bl_claim` / `bl_grant`.
- **`bigville_land_tenure.json`** — `bl_build` / `bl_build_trespass` /
  `bl_foreclose_land` / `bl_land_tax` / `bl_tax_forfeit` / `bl_enclosure_reversal`.

## Honest residuals

1. **Engine characteristic (mitigated, not a bug in these seeds).** Within ONE
   `run_rules` fixpoint a budget/first-come-coupled non-batch rule OVER-applies — the
   match set is snapshotted per fixpoint, so a rich buyer armed against many plots at
   once, or two claimants to one parcel in one fixpoint, would over-buy / double-claim.
   The adapter's safe primitive is **one acquisition per fixpoint** (`want_buy` sweeps
   one `_run` per plot; claims arm sequentially). FIRST-COME is therefore TEMPORAL order
   across ticks; a truly simultaneous same-parcel tie is not arbitrated and is avoided by
   construction. Measured and documented, not hidden.
2. **Foreclosure grounds R7 by KEYING OFF R7's own `foreclosed` flag** (house AND land
   transfer in one fixpoint). A land-only mortgage/miss cascade is not independently
   reimplemented — R13 reuses R7's DECISION by design (imports R7 read-only).
3. **The land tax is a per-plot FLAT levy** (a minimal Georgist stand-in), not
   ad-valorem. The lever chain (tax → forfeit → redistribute) is demonstrated, not tuned.
4. **N-scope is SYNTHETIC and tiny** (≤6 parcels, a handful of agents): mechanism-proven,
   NOT a benchmark; no population-scale run. Per the standing rule, synthetic-proven
   mechanism ≠ benchmark value.
