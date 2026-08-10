# BIGVILLE R9 — INSTITUTIONS & FUNDING — RESULTS

**Block 257000.** Measured AFTER `BIGVILLE_FISC_PREREG.md` (committed first). Every
number below is read straight off the graph by `scripts/bigville_fisc_run.py` →
`results/bigville_fisc/summary.json`; the gates are `tests/test_bigville_fisc_migrated.py`
(**15 passed**). A SYNTHETIC MODEL of a political-economy mechanism — NOT a claim
about real taxation, religion, or politics. Mechanism-proven ≠ benchmark.

## Gate table (all PASS)

| Gate | Measured | PASS |
|---|---|---|
| **G-mayor-paid** | with tax: john coin **20**, paid **1**; ablate tax: coin **0**, unpaid **1**, treasury **0** | ✅ funding load-bearing |
| **G-tax-is-council-policy** | fair rate **1000** → rev **50**; captured rate **3000** → rev **150**; held-control rev equal | ✅ rate is policy |
| **G-redistribution-breaks-fixpoint (HEADLINE)** | levy-only circ `470→260` (monotone), pile **240**; redistrib circ `488→476` (sustained), pile **20** | ✅ pooling broken |
| **G-mayoral-corruption (control)** | corrupt: treasury **0**, john **200**, constable unpaid **1**, depleted **1**; fair: treasury **140**, constable paid **5** | ✅ principal/agent |
| **G-church-by-donation** | income **18** (10 tithe + 8 occasional + 0 none); ablate devotion → income **0**, mary unpaid **1** | ✅ voluntary |
| **G-church-procyclical (HEADLINE)** | good income **40** (funded); downturn income **0** → mary unpaid **1**, charity failed **1**, defunct **1**, homeless **1** | ✅ precarious |
| **G-power-asymmetry** | one crisis: John (tax) paid **1**; Mary (donation) unpaid **1**, charity failed **1** | ✅ compulsory vs voluntary |
| **G-counselling-co-regulation (control)** | safe: arousal `8→5`, valence `1→3`, coreg **1**; unsafe: arousal `8→8`, coreg **0** | ✅ 239 safety load-bearing |

## Glass-box findings

- **The mayor is paid FROM the taxes, and the funding is LOAD-BEARING.** John's
  salary is a `treasury → pays → servant` transfer sourced from tax revenue; ablate
  the tax and the purse is empty, the salary is not paid, the public service fails
  (`unpaid = 1`). Not magic — the money has a source.

- **The tax rate is the COUNCIL's decision, not a constant — the TWIN of the bank
  rate.** `treasury.tax_rate_bp ← base_rate_bp + capture_premium_bp`. A fair council
  (premium 0) sets 10% → revenue 50; a captured (John's) council (premium 2000) sets
  30% → revenue 150 on the *identical* taxpayer. Rate held → revenue reproducible.
  Same lever shape as R7's `bf_set_rate` (fair + greed premium).

- **Redistribution BREAKS the interest-only pooling fixpoint (the HEADLINE, the
  creator's fixpoint made falsifiable).** With the levy alone (the interest
  attractor's essence), coin pools at the wealthy: worker circulation drains
  monotonically `470 → 260` while the rentier pile climbs to `240`. Switch the
  state's counter-flow ON (tax the pooled wealth → public wage back to the workers)
  and circulation SUSTAINS at `~476` while the pile is held to `20` — the tax claws
  the pooled coin back into circulation. Measured, not tuned; the purse is never
  overdrawn (genuinely load-bearing).

- **Mayoral corruption is the failing control (principal/agent, state twin of the
  greedy banker).** A corrupt John funnels `graft_amount` from the purse to his
  PERSONAL coin (`grafted 200`, personal coin `200`) — the purse drains to `0`
  (`depleted = 1`), the honest constable goes UNPAID (public works fail). A fair
  mayor never grafts: treasury sustains at `140`, constable paid `5` times. His
  incentive diverges from the institution's health, glass-box.

- **The church runs on voluntary donation, and it is procyclical + precarious.**
  Income = Σ donations: a tither gives a committed fraction (10% of 100 = 10), an
  occasional giver gives discretionary surplus when flush (8), a devotion=none
  villager gives nothing — total 18, funding Mary's stipend. Ablate devotion →
  income 0 → Mary unpaid. Induce a downturn (the tither has no income to tithe) →
  the plate is empty → the stipend AND the charity FAIL exactly when needed, the
  church goes defunct, and Mary loses the TIED parsonage (the stipend *and* the
  roof). The voluntary sector breaks first.

- **Power asymmetry, measured.** In ONE crisis: John's compulsory tax-salary is
  SECURE (the wealthy are taxed regardless) while Mary's voluntary donation-stipend
  FAILS (the givers are dry) — same crisis, opposite outcome. The reformer fights
  from the materially weakest base.

- **Counselling is co-regulation.** A distressed resident (arousal 8, valence 1)
  who approaches a SAFE Mary returns toward the window (arousal → 5, valence → 3);
  a dysregulated / judging counsellor (safe = 0) produces NO return — the 239000
  safety signal is load-bearing.

## The institutional TRIAD, complete

BANK (Scrooge / **interest** / a rate lever — R7), STATE (John+council / **tax** /
a tax lever — this rung), CHURCH (Mary / **donation** / **NO lever** — this rung).
Two hold coercive levers, one holds none; whether the town's coin circulates or
pools is the *balance* of the three, read off circulation/velocity. That asymmetry
— the reformer materially weakest — is itself a stake.

## Discipline ledger

- Base / merge-base: `6de883c92c` (verified). Prereg commit precedes this build.
- **No Rust:** `git diff 6de883c92c -- runners/dsl` EMPTY (incl `term.rs`).
- **Own engine:** `source_match = shared` (worktree `runners/dsl` byte-identical to
  canonical → the canonical build is correct-for-this-source and attributable). No
  `.so` committed; no md5 pinned in any test.
- **Canonical `.so` SACRED:** md5 `fd82dc2978dbb055496dd82390ac2ebe` at START ==
  END (unchanged).
- **Gates (run inline):** `test_bigville_fisc_migrated` **15/15**;
  `test_failure_baseline_migrated` **11/11**; `test_engine_provenance_migrated`
  **7/7** (`source_match = own`-or-`shared`). ZERO new reds.
- **Additive only:** all-new `bigville_fisc_*` files; no tracked file edited; both
  seeds `self_load_only` (`depends_on = []`) so they load ONLY for the R9 adapter
  and cannot affect any other suite.
- **43-min oracles NOT run** (`per_area_settlement_regression.sh`,
  `rung7_vision_bench.sh`) — per the 2026-07-29 supervisor+user directive a purely
  additive, no-Rust, `self_load_only` rung cannot regress other suites; the fast
  enumerated-baseline gate + additive discipline is sufficient. The source-audit
  (`test_no_python_institution_decision_source_audit`,
  `test_seeds_are_self_load_only_and_integer_native`) asserts the seeds are
  self_load_only and the adapter holds no decision.

## Honest residuals (built vs deferred)

- **Built:** the two FUNDING institutions (state fiscal loop, church donation loop)
  + counselling co-regulation — the R9 headline funding gates.
- **Deferred, NOT half-built** (separate faculties, would gold-plate a funding
  rung): the composed weekly SERMON (244/246 soft power), the MORAL CODE +
  per-agent adherence/guilt (204/239 internal sanction), weekly ATTENDANCE as a
  class-stratified decision, the confidentiality SEAL + benevolent held≠face
  discriminator (234). Recorded here so a later rung picks them up.
- **`fs_levy` is an honest lightweight stand-in** for R7's full mortgage-interest
  drain (R7 imported read-only): the same direction of flow (workers → the
  wealthy). The circulation gate measures the REDISTRIBUTION counter-flow
  specifically, not the full R7 interest mechanism.
- **Salary serialisation:** `pay_salaries` arms one servant per fixpoint because the
  engine matches all bindings of a pass against pre-pass funds (N servants armed
  together would overdraw one `gte(funds, salary)` guard). Documented in-code; it is
  mechanical scheduling (the async one-mover-per-tick discipline), not a decision.
- **Scope:** N is small (single-digit casts); this proves the MECHANISM, not a
  population-scale claim.
