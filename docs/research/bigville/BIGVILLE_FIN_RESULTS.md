# BIGVILLE R7 — FINANCE: HOUSING TENURE, THE BANK, INTEREST, RENT — RESULTS

**Block 255000.** Pre-registered in `BIGVILLE_FIN_PREREG.md` (commit `02da85d0e8`)
BEFORE any number here. Spec: `BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` §2 FINANCE + §3 R7.
Built ON R4 `bigville_econ_world` (coin/exchange/debt+creditor-affect), R5
`bigville_loop_world`, R6 `bigville_skill_world`, the scaffold + 245 cast + the
204000/239000 affect seeds — ALL by import, no tracked file edited. **ZERO new Rust**
(`runners/dsl` diff EMPTY): interest is a per-period arithmetic rule over the
PRE-EXISTING `IDiv` Term.

Every finance decision — accrue, set-rate, pay-vs-miss, foreclose, evict, salary,
insolvency, rent-raise — is a seed RULE (`seeds/bigville_fin_bank.json` 4 rules +
`seeds/bigville_fin_tenure.json` 11 rules). The adapter
(`worlds/bigville_fin_world.py`) holds no decision: it registers Bank / House /
Mortgage / Rental graph data, arms one-shots, ticks the Rust `run_rules` fixpoint,
and reads state back. Gates: `tests/test_bigville_fin_migrated.py` **16/16 PASS**.
Glass-box run: `scripts/bigville_fin_run.py` → `results/bigville_fin/summary.json`.

## What R7 lands

Housing is now an **ASSET** held under one of three **TENURES**, the town has a
**BANK run by the banker AGENT Scrooge McBankFace** (funds separate from his
salary), **interest** is the cross-frame multiplicative base read STEPPED as integer
coin, and a missed payment cascades to **foreclosure/eviction → homelessness**. Class
structure, financial-shock-as-housing-shock (leverage), monetary policy with a face,
and a systemic bank failure are all MECHANICAL, glass-box, from the same substrate.

## Gate results (read straight off the graph)

### G-tenure-diverges — a class structure from tenure alone ✔
Over a 6-period run, equity by tenure (an appreciating house, +10/period):

| period | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| **owner** (own outright) | 110 | 120 | 130 | 140 | 150 | 160 |
| **landlord** (owns the rental) | 110 | 120 | 130 | 140 | 150 | 160 |
| **renter** (rents it) | 0 | 0 | 0 | 0 | 0 | 0 |

Owner and landlord equity RISE; the renter's is FLAT at 0 — and the renter DID pay
(coin 1000→970, exactly 6×5), the landlord collected it (1000→1030). The renter
matches NO equity rule; **that absence IS the flat curve** (graph-native, not a
hard-coded zero).

### G-leverage-amplifies (HEADLINE) + the owned-outright failing control ✔
The SAME income collapse (a fishmonger's coin driven to 0), two tenures:

| | mortgagor | owned-outright control |
|---|---|---|
| missed payments | 3 (≥ term) | — |
| **foreclosed** | **1** | 0 |
| loses the house | yes (bank now owns it) | keeps it |
| **homeless** | **1** | **0** |
| social concern filed | 1 | 0 |
| affect (arousal / valence) | 0→4 / 5→2 (distress) | 0 / 5 (unchanged) |

The goods shock becomes a HOUSING CATASTROPHE **through the mortgage** — the bank
seizes the LAND+building (the `owns_house` edge transfers debtor→bank, the ultimate
collateral) → homelessness → the 204000/239000 distress channel fires. The
owned-outright character weathers the identical shock. **Leverage is the amplifier,
isolated.**

### G-interest-is-policy + rate-held control ✔
Identical cast of 4 marginal-income mortgagors, only Scrooge's rate differs:

| Scrooge | rate | foreclosures |
|---|---|---|
| **fair** (fair_rate_bp=1000, premium 0) | 10.0% | **0** |
| **greedy** (premium +1500 bp) | 25.0% | **4** |

A higher rate raises every mortgagor's required payment (interest_due scales with the
rate) → marginal debtors can't pay → MORE foreclosures. The rate is Scrooge's
`decision_value`, not a constant. **Control:** rate held constant → foreclosure count
reproducible (0 == 0).

### G-interest-is-stepped (the frame/continuum invariant) ✔
An interest-only mortgage (principal 1000, r = 0.10) accrued for 8 integer periods:

```
graph balance   : 1100 1210 1331 1464 1610 1771 1948 2143
round(P·1.1^k)  : 1100 1210 1331 1464 1610 1771 1948 2143   → EXACT match
```

Every read is INTEGER-valued; `r` is applied INTENSIONALLY (basis points in the rule,
never stored as a fractional float on a node). A fractional product rounds
half-up **on integers** with no `Round` primitive: 999 · 1.10 = 1098.9 → stored
**1099** via `IDiv(x + 10000/2, 10000)`. A full mixed run (pay/miss/salary/equity)
keeps every coin/balance/reserve/equity read integer-valued. **In-frame is INTEGER;
the continuum lives only in the rate MAP, applied — exactly the CLAUDE.md invariant.**

### G-bank-is-an-entity + salary (funds separate) + no-salary control ✔
Scrooge's personal coin vs the bank's reserves over 5 periods (salary 30):

```
Scrooge personal coin : 30  60  90  120  150     (= cumulative salary)
Bank reserves         : 4710 4719 4727 4734 4740 (moves with lending/repayment)
```

Two DISTINCT trajectories — his wealth tracks the SALARY, not the reserves.
**Control:** salary = 0 → Scrooge's personal coin FLAT at 0 for all 5 periods while
the bank still OPERATES (lends, is repaid; reserves move). No abstract third party:
every rate/lending/salary decision is the banker AGENT's rule on the `run_by` /
`issued` edges (source-audit).

### G-greedy-banker (the principal/agent divergence) ✔
Greedy vs fair Scrooge on the identical cast:

| | reserves (end) | foreclosures | Scrooge personal coin |
|---|---|---|---|
| **fair** | 1672 | 0 | 120 |
| **greedy** | **440** | **4** | **480** |

The greedy banker drains the bank's reserves FASTER and causes MORE foreclosures,
while his PERSONAL wealth rises FASTER — his incentive diverges from the bank's
health, glass-box.

### G-insolvency (systemic, distinct from Scrooge) ✔
Two never-paying defaulters + a 50/period salary drain: `Bank.reserves` → **0**,
`insolvent = 1` — a town-wide credit event — while Scrooge's PERSONAL coin = **100**.
The bank fails while the banker stays personally rich. The systemic state is a
first-class flag distinct from any individual's wealth.

### G-rentier-power + no-raise control ✔
John-as-slumlord raises the rent / threatens eviction:

| | rent | tenant valence | tenant arousal | backing_landlord |
|---|---|---|---|---|
| **raise** | 5 → 15 | 5 → 2 | 0 → 4 | 0 → 1 |
| **control (no raise)** | 5 | 5 (flat) | 0 (flat) | 0 |

Raising the rent moves the tenant's affect (valence down, arousal up) and shifts
backing toward the landlord — economic coercive control (ties to 239/247). No raise →
affect flat.

## Honest scope / residuals

- **Synthetic model, small N.** Gates are mechanism proofs on hand-built scenarios
  (cohorts of n≤4, runs of ≤8 periods), not a benchmark. Mechanism-proven ≠
  benchmark value.
- **LAND is proxied, not yet foundational.** Per the spec, R7 uses a per-character
  tenure attr + a `House{value}` and a bank-seizes-`owns_house`-edge foreclosure. The
  Plot/parcel land market (buy/claim/grant, enclosure, the landless class) is R13 —
  tenure here is DOWNSTREAM of a land model not yet built. The foreclosure transfers
  the house node (the collateral) but does not yet model plot subdivision.
- **Equity is per-house.** `bf_owner_equity` sets equity to a matched house's value;
  the scenarios give each owner/landlord ONE house. A multi-house landlord would need
  a summing rule (deferred; not needed for the divergence gate).
- **Interest servicing model.** A paid period reduces the balance by the principal
  portion (interest is the bank's revenue); a missed period CAPITALISES the interest
  (`balance' = round(balance·(1+r))`, the debt spiral). `bf_accrue` (pure geometric
  accrual, no amortisation) is retained as the standalone invariant demonstrator.
- **No wall-clock / global market clear** anywhere — periods are adapter-driven
  discrete steps (the R3 clock analog); every transfer is local and rule-mediated.

## Discipline ledger

| item | result |
|---|---|
| base / merge-base | `1c8ce0e3fe` (verified `git merge-base HEAD 1c8ce0e3fe == 1c8ce0e3fe`) |
| prereg commit (before any number) | `02da85d0e8` — `check_claim(255000, 255999)` CLEAN, verbatim in PREREG |
| own engine | `cargo build --release` in THIS worktree; md5 `10f65be659e0d9a9290aff39f7f5b92a`; `source_match == own` (`test_engine_provenance_migrated` 7/7) |
| `runners/dsl` diff | **EMPTY** (`git status --porcelain runners/dsl/src Cargo.toml Cargo.lock` empty; `term.rs` untouched — interest uses the pre-existing `IDiv` Term) |
| canonical shared `.so` | **UNTOUCHED** — md5 `fd82dc2978dbb055496dd82390ac2ebe` start == end (a peer's build; the pre-existing main provenance red, NOT mine) |
| failure baseline | `test_failure_baseline_migrated` — **11/11 PASS** (543 enumerated node-ids) |
| rung7 vision bench | **214 passed, 10 skipped, 0 failed** (3m25s) |
| per-area settlement | **278 passed, 5 skipped, 23 failed** — all **23 failing node-ids ∈ enumerated `results/failure_baseline.json`** (verified set-wise; ZERO new reds; 5 pre-existing red files: `test_cortices_tick`, `test_composer_driver_migrated`, `test_gap_awareness_migrated`, `test_elaboration_migrated`, `test_topic_route_selfheal_migrated`) |
| additive only | 7 all-new `bigville_fin_*` files + PREREG/RESULTS; **zero tracked files edited** (`git status --porcelain | grep '^ ?[MADRC]'` empty); imports R4/R5/R6 + scaffold |
| R7 gates | `tests/test_bigville_fin_migrated.py` **16/16 PASS** |
| worktree | NON-nested (`.claude/worktrees/agent-…`), supervisor merges |
| BUILD COMMITTED | seeds + world + gen + run + tests + results committed before finish; `git status` clean |
