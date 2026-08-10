# BIGVILLE R9 — INSTITUTIONS & FUNDING: THE STATE (TAXES) + THE CHURCH (DONATION) — PRE-REGISTRATION

**Block 257000. Pre-registered BEFORE any recorded number.** Spec:
`BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` §2 FISCAL (taxes → a `Treasury` purse →
public salaries; the rate a COUNCIL decision_value, TWIN of the bank rate; the
mayor a principal/agent who can graft) + §2 CHURCH / institutional TRIAD (funded
by voluntary DONATION — tithers a committed fraction, others when flush; funds
Mary's stipend + tied parsonage + charity; NO lever; procyclical + precarious;
plus co-regulation counselling) + §3 R9 (this gate). Builds ON R4
`bigville_econ_world` (coin / affect) + R7 `bigville_fin_world` (the BANK /
interest / Treasury-style entity) — imported READ-ONLY (the R9 adapter
SUBCLASSES `BigvilleFinWorld`). Reuse ALL by import; edit no tracked file.

R9 adds the town's TWO FUNDING institutions to R7's bank, completing the
institutional TRIAD: BANK (Scrooge / interest / a rate lever — R7), STATE
(John+council / tax / a tax lever — this rung), CHURCH (Mary / donation / NO
lever — this rung). Every decision — set the rate, collect, pay a salary, graft,
levy, tithe, donate, pay the stipend, give charity, defund the parsonage,
co-regulate — is a seed RULE; the adapter only arms one-shots, wires edges, ticks
and reads.

## Seed-claim (verbatim `scripts/seed_claim.py 257 257`, run before anything)

```
SEED CLAIM 257-257: CLEAN -- no collision DETECTED.
  Scope: 973 files with seed sinks; 681 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

(R9 seeds NO RNG — every rule/attr is deterministic graph data — so the claim is
a discipline formality; the rung introduces no stochastic sink.)

## What R9 adds (graph-native, ZERO new Rust)

Two additive, `self_load_only` seeds, composing ONLY existing DSL Terms. A tax
RATE and a tithe FRACTION are INTENSIONAL (basis points, the cross-frame map — the
CLAUDE.md frame/continuum invariant, exactly as R7's interest); every
collected/paid amount is OBSERVED STEPPED as INTEGER coin via the pre-existing
`IDiv` Term (round-half-up = `IDiv(x + denom/2, denom)`), never a fractional float
in a frame. No `Round`/`Floor`/`Div`-into-a-coin-attr anywhere.

- **`seeds/bigville_fisc_state.json`** (7 rules) — the STATE / FISCAL entity.
  - **`fs_set_tax`** — the RATE IS THE COUNCIL'S DECISION. `treasury.tax_rate_bp ←
    base_rate_bp + capture_premium_bp` (a FAIR council premium=0; a CAPTURED
    John's council premium>0). The TWIN of R7's `bf_set_rate`.
  - **`fs_collect`** — TAX collection (per-payer arm). `tax_due =
    IDiv(taxable·rate_bp + 5000, 10000)`, INTEGER coin; paid iff affordable →
    `treasury.funds`/`revenue += tax_due`.
  - **`fs_pay_salary`** — the MAYOR/CONSTABLE are paid FROM the purse (per-servant
    arm), iff `funds ≥ salary` and `salary > 0` (the ablation). Money RE-ENTERS
    circulation when spent.
  - **`fs_salary_unfunded`** — DISJOINT (`funds < salary`): the public service
    FAILS (`unpaid = 1`).
  - **`fs_treasury_empty`** — SYSTEMIC: a treasury that has COLLECTED revenue
    (`revenue > 0`) and been drained to `funds ≤ 0` → `depleted = 1` (public works
    fail). The `revenue > 0` guard excludes the trivial boot-empty purse.
  - **`fs_graft`** — MAYORAL CORRUPTION, gated on `corrupt = 1`: a corrupt mayor
    funnels `graft_amount` from the purse to his PERSONAL coin (a fair mayor never
    matches). The state twin of the greedy banker's principal/agent divergence.
  - **`fs_levy`** — the POOLING force: coin flows worker→the wealthy rentier each
    period (the R7 interest-attractor's essence, an honest lightweight stand-in for
    R7's full mortgage-interest drain), which the redistribution loop BREAKS.

- **`seeds/bigville_fisc_church.json`** (9 rules) — the CHURCH (donation) entity.
  - **`fc_tithe`** — a TITHER gives a COMMITTED FRACTION: `tithe_due =
    IDiv(income·tithe_bp + 5000, 10000)`, INTEGER coin (the cross-frame fraction,
    the invariant shared with interest/tax).
  - **`fc_donate_occasional`** — DISJOINT (`tithe_bp = 0`): discretionary giving
    WHEN FLUSH (`coin > flush_threshold`). devotion=none (tithe_bp=0 AND
    occasional=0) matches NEITHER → income 0 (ablate devotion → 0).
  - **`fc_stipend`** / **`fc_stipend_unfunded`** — pay Mary FROM funds iff
    donations sufficed, else mark her `unpaid = 1` (precarity, NO lever).
  - **`fc_charity`** / **`fc_charity_unfunded`** — redistribute to the poor iff
    funded, else `charity_failed = 1` (procyclical — the plate is empty in a
    downturn exactly when the poor need it).
  - **`fc_church_defunct`** (`funds ≤ 0`) + **`fc_parsonage_precarious`** — a
    defunct church costs Mary the TIED parsonage (`homeless = 1`, `del_edge
    houses`): the stipend AND the roof.
  - **`fc_counsel`** — private CO-REGULATION (reuse the 239000 safety channel): a
    distressed resident approaching a SAFE Mary returns toward the window (arousal
    down / valence up); a dysregulated counsellor (`safe = 0`) → no return.

The adapter (`worlds/bigville_fisc_world.py`) subclasses `BigvilleFinWorld` by
import, holds NO decision: it registers Council/Treasury/Church/servant/giver/poor
graph data (ingest), ARMS one-shots, runs the Rust `run_rules` fixpoint, reads
state back. `pay_salaries` arms ONE servant per fixpoint (the purse is a shared,
decreasing resource — the engine matches all bindings of a pass against pre-pass
funds, so N servants armed together would overdraw one `gte(funds, salary)` check;
one-per-pass makes the purse genuinely load-bearing — mechanical scheduling, the
async scheduler's one-mover-per-tick discipline, no decision).

## Pre-registered gates (numbers to be filled in RESULTS after the run)

Each gate names its PASS predicate + its CONTROL + an ABANDON/NARROW criterion.

- **G-mayor-paid:** John's salary flows FROM the treasury funded by taxes. PASS ⟺
  with-tax: revenue collected AND `john.coin` rises by exactly the salary AND
  `paid_count = 1`. **FAILING CONTROL:** ablate the tax (collect nothing) → empty
  treasury → `john.coin = 0` AND `unpaid = 1`. **ABANDON/NARROW:** if the mayor is
  paid with an empty treasury (funding not load-bearing) → the treasury is
  decorative; NARROW to "the rule fires but the purse is not a constraint" and
  report it.

- **G-tax-is-council-policy:** the rate is the council's decision_value, not a
  constant. PASS ⟺ `captured_rate_bp > fair_rate_bp` (= base+premium) AND
  `revenue(captured) > revenue(fair)` on the identical taxpayer. **CONTROL:** rate
  held (premium=0 twice) → `revenue(a) == revenue(b)`. **ABANDON/NARROW:** if the
  captured rate does not change revenue → the lever is inert; report the null.

- **G-redistribution-breaks-the-fixpoint (HEADLINE):** with the levy alone coin
  POOLS at the wealthy and circulation drains; with taxes + public spending ON coin
  CIRCULATES and the pooling attractor is BROKEN. PASS ⟺ levy-only circulation is
  MONOTONE decreasing (pools) AND `circulation(ON, final) > circulation(OFF, final)`
  AND `pile(OFF) > pile(ON)` (the wealth pile broken by the tax) AND the purse is
  never overdrawn. **CONTROL:** the levy-only arm IS the interest-only control.
  **ABANDON/NARROW:** if redistribution does NOT sustain circulation (ON ≤ OFF) →
  a DEAD-fixpoint finding (redistribution insufficient at this dosage); report the
  velocities honestly rather than tuning.

- **G-mayoral-corruption (failing control):** a corrupt John drains the purse to
  his personal coin while a public service fails. PASS ⟺ `treasury(corrupt) <
  treasury(fair)` AND `john.coin(corrupt) > john.coin(fair)` AND
  `constable.unpaid(corrupt) = 1` AND `constable.paid(fair) > 0` AND
  `depleted(corrupt) = 1`. **CONTROL:** a fair mayor (corrupt=0) never grafts.
  **ABANDON/NARROW:** if graft does not starve a public service at any dosage →
  narrow to "graft transfers coin but does not break provision" and report.

- **G-church-by-donation:** church income = Σ voluntary donations (tithe +
  occasional); devotion=none gives nothing. PASS ⟺ `income = tithe + occasional`,
  the none-villager's coin unchanged, Mary's stipend paid. **ABLATION:** all-none
  givers → `income = 0` → Mary `unpaid = 1`. **ABANDON/NARROW:** if a none-villager
  donates → the devotion axis is not load-bearing; report.

- **G-church-procyclical (HEADLINE for the church):** a downturn dries donations so
  the stipend AND charity FAIL when needed, and Mary loses the tied parsonage. PASS
  ⟺ downturn `income = 0` AND `mary.unpaid = 1` AND `charity_failed = 1` AND (on
  parsonage check) `defunct = 1` AND `mary.homeless = 1`. **CONTROL:** good times
  (flush giver) → stipend + charity both funded. **ABANDON/NARROW:** if the church
  survives a total donation collapse → the funding is not precarious; report.

- **G-power-asymmetry (measured):** in ONE crisis John's compulsory tax-salary is
  SECURE while Mary's voluntary donation-stipend is NOT. PASS ⟺ same crisis:
  `john.paid = 1` AND `john.unpaid = 0` AND `mary.unpaid = 1` AND `mary.paid = 0`
  AND `charity_failed = 1`. **ABANDON/NARROW:** if both are paid or both fail →
  the compulsory/voluntary distinction is not material; report.

- **G-counselling-is-co-regulation:** a distressed resident approaching a SAFE Mary
  returns toward the window. PASS ⟺ safe: `arousal(after) < arousal(before)` AND
  `valence(after) > valence(before)` AND `co_regulated = 1`. **CONTROL:**
  dysregulated counsellor (`safe = 0`) → affect flat, `co_regulated = 0`.
  **ABANDON/NARROW:** if co-regulation fires without the safety signal → the 239
  safety channel is not load-bearing; report.

- **G-discipline:** base/prereg on `6de883c92c` (verified merge-base); own-engine
  `source_match ∈ {own, shared}`; `runners/dsl` diff EMPTY (no Rust, incl
  `term.rs`); canonical `.so` md5 `fd82dc2978dbb055496dd82390ac2ebe` UNCHANGED
  start==end; `test_failure_baseline_migrated` 11/11 green;
  `test_engine_provenance_migrated` 7/7 green; all-new additive `bigville_fisc_*`
  files, no tracked file edited; PREREG committed BEFORE any measured number, BUILD
  committed after. Honest scope: a SYNTHETIC MODEL of a political-economy
  mechanism, N stated; mechanism-proven ≠ benchmark; NOT a claim about real
  taxation, religion, or politics.

## Discipline pre-commitments

- **NON-nested isolated worktree**; build + gates here; DO NOT merge (supervisor merges).
- **NO Rust:** `runners/dsl` (incl `term.rs`) diff EMPTY. Every rate/fraction is a
  per-period arithmetic rule using the pre-existing `IDiv` Term — no new primitive.
- **Own engine:** `source_match ∈ {own, shared}` (the worktree's `runners/dsl` is
  byte-identical to canonical → `shared`; the canonical `.so` is never touched).
- **Additive only:** all-new `bigville_fisc_` files
  (`seeds/bigville_fisc_state.json`, `seeds/bigville_fisc_church.json`,
  `scripts/bigville_fisc_gen_seeds.py`, `worlds/bigville_fisc_world.py`,
  `scripts/bigville_fisc_run.py`, `tests/test_bigville_fisc_migrated.py`,
  `BIGVILLE_FISC_PREREG.md`, `BIGVILLE_FISC_RESULTS.md`, `results/bigville_fisc/*`).
  No tracked file edited; subclass/import R4/R7 + scaffold. Explicit `git add <path>`.
- **Seeds `self_load_only`** so they cannot affect any other suite (a purely
  additive, no-Rust, self_load_only rung CANNOT regress others — the fast baseline
  gate + additive discipline is sufficient; the ~43-min oracles are NOT run, per
  the 2026-07-29 supervisor+user directive).

## Honest residuals pre-committed (built vs deferred)

R9 builds the two FUNDING institutions (state fiscal loop + church donation loop)
and the counselling co-regulation gate — the gates named in the spec's R9 headline
list and the ones that make the institutional TRIAD's funding real. DEFERRED, and
reported as honest residuals, NOT half-built: the spec's larger adjacent church
FACULTIES — the composed weekly SERMON (soft power, the 244/246 language faculty),
the MORAL CODE + per-agent adherence/guilt (204/239 internal sanction), weekly
ATTENDANCE as a class-stratified decision, and the confidentiality SEAL + the
benevolent held≠face discriminator (234). Those are separate faculties, not
funding mechanisms; folding them in here would gold-plate the funding rung. The
`fs_levy` pooling force is an honest lightweight stand-in for R7's full
mortgage-interest drain (R7 imported read-only); the circulation gate measures the
REDISTRIBUTION counter-flow specifically.
