# BIGVILLE R13 — LAND: OWNERSHIP, THE MARKET, THE COMMONS (the foundational scarce asset) — PRE-REGISTRATION

**Block 261000. Pre-registered BEFORE any recorded number.** Spec:
`BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` §2 LAND (a PLOT is a graph node, OWNERSHIP an
`owns` edge; land FINITE / NON-PRODUCED / CONSERVED — ownership partitions a fixed
map; acquired by BUY / CLAIM / GRANT; the ROOT of tenure R7 / construction R12 /
collateral; land concentrates HARDER than money → the deepest inequality root + the
purest structure) + §3 R13 (this gate). Builds ON R7 `bigville_fin_world` (the BANK /
interest / foreclosure / tenure) — imported READ-ONLY (the R13 adapter SUBCLASSES
`BigvilleFinWorld`). Reuse ALL by import; edit no tracked file.

LAND is the FOUNDATIONAL scarce asset. R7's mortgage was "secured on the LAND+building"
in PROXY (it transferred only the house); R13 GROUNDS that proxy — a `Plot` node, an
`owns` edge, and foreclosure that moves the LAND. Every land decision — buy-vs-fail,
claim (first-come), grant, build-vs-trespass, foreclose, tax, forfeit,
enclosure-reversal — is a seed RULE (`bigville_land_market` / `bigville_land_tenure`);
the adapter only wires transient edges / arms one-shots, runs the Rust `run_rules`
fixpoint, and reads.

## Seed-claim (verbatim `scripts/seed_claim.py 261 261`, run before anything)

```
SEED CLAIM 261-261: CLEAN -- no collision DETECTED.
  Scope: 973 files with seed sinks; 681 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

(R13 seeds NO RNG — every rule/attr is deterministic graph data — so the claim is a
discipline formality; the rung introduces no stochastic sink.)

## What R13 adds (graph-native, ZERO new Rust)

Two additive, `self_load_only` seeds, composing ONLY existing DSL Terms. LAND is
FINITE / NON-PRODUCED / CONSERVED: **no rule mints or destroys a Plot node** (no
`add_node`/`del_node` in any effect); every acquisition only MOVES or ADDS an `owns`
edge over a fixed set of pre-existing `Plot` nodes seeded at ingest. Ownership
PARTITIONS the map (≤1 owner per plot). No new Rust — `runners/dsl` diff EMPTY.

- **`seeds/bigville_land_market.json`** (4 rules) — the three ACQUISITION modes.
  - **`bl_buy`** — the seller-priced MARKET. A buyer `wants_to_buy` a `for_sale`
    plot, is not the seller, and can afford it → coin transfers buyer→seller and the
    `owns` edge MOVES seller→buyer (Σ conserved).
  - **`bl_buy_fail`** — the CAN'T-AFFORD control (DISJOINT on `coin < price`): the
    landless/poor buyer cannot buy into the market by wanting to — no transfer.
  - **`bl_claim`** — HOMESTEAD unowned FRONTIER land, FIRST-COME (the `owned==0`
    guard: once one claimant takes a plot, a later claimant to the same plot no
    longer matches). A frontier `Plot` merely GAINS an `owns` edge — no node minted.
  - **`bl_grant`** — the COUNCIL grant (R9): the council (`is_council==1`) holds a
    plot + a `granted_to` edge names the recipient → `owns` MOVES council→recipient.

- **`seeds/bigville_land_tenure.json`** (6 rules) — LAND as the ROOT + the levers.
  - **`bl_build`** — construction REQUIRES owning the plot (the R12 precondition):
    builder-owns-plot + `wants_to_build` → `built=1`.
  - **`bl_build_trespass`** — building on ANOTHER'S land is refused = TRESPASS
    (owner≠builder → flag, build NOT applied). Building on unowned frontier matches
    NEITHER → `built` stays 0 (refusal as absence).
  - **`bl_foreclose_land`** — FORECLOSURE transfers the LAND. Keys off R7's OWN
    `foreclosed` flag (R7 decided, over the house) and MOVES the `owns` edge of the
    plot the same mortgage is `secured_on_plot` from debtor→bank — grounding R7's
    proxied land-as-ultimate-collateral. Once-only via `land_transferred`.
  - **`bl_land_tax`** — the GEORGIST land-tax lever: an owner pays `tax` per owned
    plot to the jurisdiction (`taxed_by`), iff affordable. Integer coin.
  - **`bl_tax_forfeit`** — can't pay the tax (DISJOINT `coin < tax`) → the plot
    FORFEITS to the council (`owns` moves owner→council): an over-concentrated / idle
    holding returns to the redistribution pool.
  - **`bl_enclosure_reversal`** — an owned plot reverts to unowned FRONTIER commons
    (`owns` removed; `owned→0`, `frontier→1`) → re-claimable by the landless.

The rules are pinned **`batch: false`** (SEQUENTIAL one-match-per-pass, the
`retire_duplicate_gap` precedent) so the market SWEEP respects a shrinking BUDGET and
CLAIM is FIRST-COME. The adapter arms ONE acquisition per fixpoint (the safe
primitive: a match set is snapshotted within a fixpoint).

The adapter (`worlds/bigville_land_world.py`) subclasses `BigvilleFinWorld` by import,
holds NO decision: it registers `Plot` / `owns` graph data (ingest), wires the
transient `wants_to_buy`/`wants_to_claim`/`granted_to`/`wants_to_build`/
`secured_on_plot`/`taxed_by` edges or `*_armed` flags, runs `run_rules`, and reads.

## Pre-registered GATES (each with its control + abandon/narrow criterion)

`tests/test_bigville_land_migrated.py`.

### G-land-is-owned-and-conserved
- **`test_land_is_conserved_through_all_modes`** — buy + claim + grant + tax-forfeit +
  enclosure-reversal + foreclosure, and `total_plots()` (Σ Count(Plot)) is INVARIANT,
  equal to the ingest count, at every step. **`test_ownership_partitions_the_map`** —
  every plot has ≤1 owner throughout (the partition; `owner_of` asserts it).
  - **Abandon/narrow:** if any mode changes Σplots, or a plot ever has 2 owners, the
    conservation claim is FALSE — narrow to a report of which mode leaks.

### G-acquisition (buy / claim / grant) + the structural-exclusion control
- **`test_buy_acquires_seller_priced`** — bl_buy: plot + coin transfer.
  **`test_claim_homesteads_frontier_first_come`** — sequential claims: the first
  claimant gets the frontier plot, the second is blocked (owned).
  **`test_grant_by_council`** — bl_grant transfers a council-held plot.
- **CONTROL — `test_landless_cannot_acquire_structural_exclusion`** — all land owned,
  no frontier, no affordable seller, no grant → a landless resident who ARMS a buy AND
  a claim acquires NOTHING (structurally excluded). **This control MUST leave the
  landless at 0 holdings.** **`test_buy_fail_cant_afford_control`** — coin<price → no
  transfer.
  - **Abandon/narrow:** if the landless acquires land by personal effort with all
    land owned, the structural claim is FALSE.

### G-land-underlies-tenure+build (HEADLINE)
- **`test_build_requires_owning_the_plot`** — owner builds (built=1); a non-owner on
  another's land → trespass, NOT built; unowned frontier → refused (built 0).
  **`test_foreclosure_transfers_the_land`** — a mortgage `secured_on_plot` a plot the
  debtor owns; an income collapse drives R7 to foreclose → the LAND transfers to the
  bank (Σ conserved). **CONTROL — `test_owned_outright_keeps_the_land`** — the same
  shock on an owner with NO mortgage keeps his plot. **`test_tenure_derives_from_land`**
  — the landlord owns the plot (rents to the tenant via R7); the homeowner owns his
  plot; the renter owns NO plot.
  - **Abandon/narrow:** if foreclosure leaves the land with the debtor, R7's
    land-as-collateral is NOT grounded — report it.

### G-land-concentrates + the structural floor
- **`test_land_concentrates_with_capital`** — a rich buyer sweeps a market of N plots
  → `max_share` rises toward 1.0, the poor hold 0: land POOLS with capital.
- **`test_landless_escapes_only_structurally`** — a landless resident's personal
  effort (unaffordable buy + no-frontier claim) leaves him at 0; then EACH structural
  lever — GRANT, ENCLOSURE-REVERSAL + claim, TAX-FORFEIT → GRANT — gives him land.
  **CONTROL — `test_no_lever_stays_landless`** — with NO lever applied he stays at 0
  (the lever is what moved it).
  - **Abandon/narrow:** if the landless gains land with no lever, or a lever fails to
    open land, the agency/structure claim is FALSE.

### G-discipline (source-audit)
- **`test_no_python_agent_decision_source_audit`** — the ten land decisions are the
  exact rule-name set; the adapter runs/authors no Python rule engine; decision
  parameters (`price`, `for_sale`, `frontier`, `foreclosed`, `tax`) appear only in
  seeds, never an adapter `if`. **`test_seeds_are_self_load_only_and_conserve_land`** —
  both seeds `self_load_only:true`; NO effect uses `add_node`/`del_node` (Σplots
  conserved at the SOURCE level); no `Div` into a coin attr; no new Rust.

## Discipline (this rung)

Additive-only, ONE prefix `bigville_land_`; NEW files only; import R7 read-only; edit
no tracked file. Seeds `self_load_only` (loaded only by the R13 adapter) so a
purely-additive, no-Rust, `self_load_only` rung CANNOT regress other suites — the fast
baseline gate + additive discipline is SUFFICIENT (SUPERVISOR+USER directive
2026-07-29); the ~43-min `per_area`/`rung7` oracles are NOT run. `runners/dsl` diff
EMPTY (target no Rust); own-engine provenance (`source_match ∈ {own, shared}`);
canonical `.so` md5 UNCHANGED start==end. Gates run inline: the rung suite +
`test_failure_baseline_migrated` (11/11) + `test_engine_provenance_migrated` (7/7).
Honest scope: synthetic model; N-scope stated; mechanism-proven ≠ benchmark. Two
commits (prereg, build); supervisor merges.
