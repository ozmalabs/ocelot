# BIGVILLE R7 — FINANCE: HOUSING TENURE, THE BANK, INTEREST, RENT — PRE-REGISTRATION

**Block 255000. Pre-registered BEFORE any recorded number.** Spec:
`BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` §2 FINANCE (housing tenure; the BANK as a
BUILDING + entity run by the banker AGENT **Scrooge McBankFace**, funds SEPARATE
from his personal funds, drawing a SALARY; interest = the cross-frame
multiplicative base; LAND is the foundational asset tenure derives from) and §3
R7 (this gate). Builds ON R4 `bigville_econ_world` (coin / exchange / the debt +
creditor-affect channel), R5 `bigville_loop_world`, R6 `bigville_skill_world`, the
scaffold + 245 cast + the 204000/239000 affect seeds (foreclosure/eviction
distress). Reuse ALL by import; edit no tracked file.

R7 makes housing an ASSET held under one of three TENURES, gives the town a BANK
run by a full banker agent whose funds are separate from his salary, and models
interest as a per-period MULTIPLICATIVE rule that respects the frame/continuum
invariant (`CLAUDE.md`: in-frame is INTEGER; non-integer math is CROSS-FRAME;
`coord_ints` refuses floats). Every decision — accrue, set-rate, pay/miss,
foreclose, evict, draw salary, go insolvent, raise rent — is a seed RULE; the
adapter only arms one-shots, wires edges, ticks and reads.

## Seed-claim (verbatim `check_claim(255000, 255999)`, run before anything)

```
SEED CLAIM 255000-255999: CLEAN -- no collision DETECTED.
  Scope: 973 files with seed sinks; 681 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

## What R7 adds (graph-native, ZERO new Rust)

Two additive seeds, composing ONLY existing DSL Terms. **Interest is a per-period
integer arithmetic rule — no new primitive.** The multiplicative step is expressed
with the existing `IDiv` (integer truncating division) + `Times`/`Plus`, giving
round-half-up on integers WITHOUT a `Round` Term:

```
balance' = IDiv( balance·(10000 + rate_bp) + 5000 , 10000 ) − payment
```

`rate_bp` is INTENSIONAL (basis points, a rule parameter / the cross-frame map);
the balance is OBSERVED STEPPED as INTEGER coin every period. No float lives in a
frame.

- **`seeds/bigville_fin_bank.json`** (4 rules) — the BANK ENTITY.
  - **`bf_accrue`** — INTEREST (the invariant headline). A mortgage with
    `accrue_armed=1`, not foreclosed: `balance' = IDiv(balance·(10000+rate_bp)+5000,
    10000)`; `period += 1`; disarm. The multiplicative cross-frame step; the stored
    balance stays INTEGER coin.
  - **`bf_set_rate`** — the RATE IS SCROOGE'S DECISION. On `rate_armed`, the bank's
    `rate_bp` and every issued mortgage's `rate_bp` are set to
    `fair_rate_bp + greed_premium_bp` — the banker's `decision_value` (fair, or
    predatory when the premium is high). Monetary policy with a face.
  - **`bf_salary`** — bank→Scrooge SALARY transfer (funds separate). On
    `salary_armed` with `reserves ≥ salary` and `salary > 0`: `reserves −= salary`,
    Scrooge's PERSONAL `coin += salary`. His personal wealth tracks the salary, NOT
    the reserves.
  - **`bf_insolvent`** — SYSTEMIC. `reserves ≤ 0` → `insolvent = 1` (a town-wide
    credit event), DISTINCT from Scrooge's personal coin (he can stay rich while the
    bank fails).

- **`seeds/bigville_fin_tenure.json`** (11 rules) — TENURE, payments, foreclosure/
  eviction, equity, rentier power.
  - **`bf_mortgage_pay`** — mortgagor with `pay_armed`, not foreclosed,
    `coin ≥ payment`: transfer payment debtor→bank reserves, `balance −= payment`,
    `missed = 0`, disarm.
  - **`bf_mortgage_miss`** — DISJOINT (same arm, `coin < payment`): `missed += 1`, no
    transfer, disarm. (A goods shock → an unpayable mortgage payment.)
  - **`bf_foreclose`** — `missed ≥ term` and not foreclosed: `foreclosed = 1`;
    del_edge debtor→house, add_edge bank→house (the LAND+building is the collateral —
    ownership transfers to the bank); `homeless = 1`, `equity = 0`.
  - **`bf_rent_pay`** — tenant with `rent_armed`, not evicted, `coin ≥ rent`: transfer
    rent tenant→landlord coin, `missed = 0`, disarm. (Tenant builds NO equity — no
    equity rule matches a tenant.)
  - **`bf_rent_miss`** — DISJOINT (`coin < rent`): `missed += 1`, disarm.
  - **`bf_evict`** — `missed ≥ term`, not evicted: `evicted = 1`, tenant `homeless = 1`
    (the landlord keeps the house).
  - **`bf_homeless_affect`** — any Mover `homeless=1` with an AffectiveState, once
    (`homeless_affect_done` guard): arousal += `concern_mag`, valence −= `concern_drop`
    (the 204000/239000 distress channel, exactly like R4 `be_default_affect`);
    `social_concern = 1`.
  - **`bf_owner_equity`** — owner (`tenure=0`, owns a house), `equity_armed`:
    `equity = house.value`.
  - **`bf_mortgagor_equity`** — mortgagor (`tenure=1`), `equity_armed`:
    `equity = max(0, house.value − balance)` (rises as balance falls / value rises).
  - **`bf_appreciate`** — a house with `appreciate_armed`: `value += apprec`. A
    landlord's house appreciates → the landlord's equity rises; a renter owns none.
  - **`bf_rent_raise`** — the RENTIER lever (John-as-slumlord). On `raise_armed`:
    `rent += raise_amount`, `threatened = 1`, and the tenant's affect moves (arousal
    up / valence down — economic coercive control) + `backing_landlord += 1`. Ties to
    239/247.

The adapter (`worlds/bigville_fin_world.py`) subclasses `BigvilleSkillWorld` by
import, holds NO decision: it registers Bank / House / Mortgage / Rental graph data
(ingest), ARMS one-shots (accrue / set-rate / charge / salary / appreciate /
raise), runs the Rust `run_rules` fixpoint, reads state back.

## Pre-registered gates (the numbers to be filled in RESULTS after the run)

- **G-tenure-diverges:** over a multi-day run the OWNER's and LANDLORD's equity
  RISES while the RENTER's stays FLAT at 0 (pays forever, owns no asset) — a
  wealth/class gap EMERGES from tenure alone. PASS ⟺ `owner_equity[-1] >
  owner_equity[0]` AND `landlord_equity[-1] > landlord_equity[0]` AND
  `renter_equity` constant at 0.

- **G-leverage-amplifies (HEADLINE):** a mortgagor whose income collapses (reuse the
  fishmonger shock — coin driven below the payment) MISSES payments until
  `missed ≥ term` → the bank FORECLOSES → `homeless=1` → the affect/social-concern
  distress fires (arousal up, valence down). **Failing control:** the SAME income
  collapse on an OWNED-OUTRIGHT character → he keeps the house, `homeless=0`, no
  distress. PASS ⟺ mortgagor foreclosed+homeless+distress AND owner not.

- **G-interest-is-policy:** a HIGHER `greed_premium_bp` (predatory Scrooge) → larger
  per-period balance growth → more mortgagors breach `term` → MORE foreclosures than
  a FAIR (low-premium) Scrooge on the identical cast. **Control:** rate held constant
  → foreclosure count flat. PASS ⟺ `foreclosures(greedy_rate) > foreclosures(fair_rate)`
  AND `foreclosures(held) == foreclosures(held)`.

- **G-interest-is-stepped (the invariant):** across a multi-period run the balance
  read at INTEGER periods equals `round(principal·(1+r)^k) − Σpayments` with `r`
  applied INTENSIONALLY; the stored `balance` / `coin` / `reserves` are ALWAYS
  integer-valued (`bal == round(bal)` every period) and NO fractional rate is stored
  on any node (only `rate_bp` basis-point integers). Source-audit: the balance is
  computed with `IDiv`, never a `Div`-into-a-stored-attr. PASS ⟺ every period-read
  integer AND the closed-form `round(P·(1+r)^k)` matches the graph balance.

- **G-bank-is-an-entity + salary (funds separate):** the `Bank.reserves` ≠ Scrooge's
  personal `coin`; a SALARY transfers bank→Scrooge each cycle and his personal wealth
  tracks the SALARY, not the reserves. **Control:** `salary=0` → Scrooge's personal
  coin FLAT while the bank still operates (accrues, charges, forecloses). Source-audit:
  no abstract third party — rate/lending/salary are the banker AGENT's rules on the
  `run_by` / `issued` edges. PASS ⟺ Scrooge coin rises by exactly `Σsalary`, is
  independent of reserves, and is FLAT under the no-salary control.

- **G-greedy-banker (failing control):** a GREEDY Scrooge (high salary + high premium)
  drains `reserves` FASTER and causes MORE foreclosures than a FAIR one, while his
  PERSONAL `coin` RISES faster — the principal/agent divergence. PASS ⟺
  `reserves_greedy[-1] < reserves_fair[-1]` AND `foreclosures_greedy > foreclosures_fair`
  AND `scrooge_coin_greedy[-1] > scrooge_coin_fair[-1]`.

- **G-insolvency (systemic):** enough defaults + salary withdrawals → `Bank.reserves`
  hit ≤ 0 → `insolvent = 1`, DISTINCT from Scrooge's personal coin (he stays rich).
  PASS ⟺ `insolvent == 1` AND `scrooge_coin > 0` at the same tick.

- **G-rentier-power:** a landlord raising rent / threatening eviction moves the
  tenant's affect (valence DOWN, arousal UP) and `backing_landlord` UP — economic
  coercive control (John-as-slumlord), ties to 239/247. **Control:** no raise → the
  tenant's affect unchanged. PASS ⟺ post-raise tenant valence < pre AND
  backing_landlord increased AND the no-raise control leaves affect flat.

- **G-discipline:** base/prereg on `1c8ce0e3fe` (verified merge-base); own-engine
  `source_match == own`; `runners/dsl` diff EMPTY (no Rust); canonical `.so` md5
  UNCHANGED start==end; oracles `rung7_vision_bench.sh` + `per_area_settlement_regression.sh`
  fail-set ⊆ enumerated `results/failure_baseline.json`, `test_failure_baseline_migrated`
  green, ZERO new reds; all-new additive `bigville_fin_*` files, no tracked file edited;
  BUILD COMMITTED before finish. Honest scope: synthetic model; N stated;
  mechanism-proven ≠ benchmark.

## Discipline pre-commitments

- **NON-nested worktree** (lesson 15); build + oracles here.
- **NO Rust:** `runners/dsl` (incl `term.rs`) diff EMPTY. Interest is a per-period
  arithmetic rule using the pre-existing `IDiv` Term — no new primitive.
- **Own engine:** `cargo build --release` here; assert `source_match in {own, shared}`.
  Canonical `.so` untouched.
- **Additive only:** all-new `bigville_fin_` files
  (`seeds/bigville_fin_bank.json`, `seeds/bigville_fin_tenure.json`,
  `scripts/bigville_fin_gen_seeds.py`, `worlds/bigville_fin_world.py`,
  `scripts/bigville_fin_run.py`, `tests/test_bigville_fin_migrated.py`,
  `BIGVILLE_FIN_PREREG.md`, `BIGVILLE_FIN_RESULTS.md`, `results/bigville_fin/*`). No
  tracked file edited; subclass/import R4/R5/R6 + scaffold. Explicit `git add <path>`.
  Do NOT merge (supervisor merges).
