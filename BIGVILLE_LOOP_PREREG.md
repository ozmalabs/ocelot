# BIGVILLE R5 — THE LOOP CLOSES + emergent cascades — PRE-REGISTRATION

**Block 253000. Pre-registered BEFORE any recorded number.** Spec:
`BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` §0 (grounded / propagating / felt — the
anti-bullshit capstone), §2 (economy + supply + debt), §2.5 (async time/energy),
§3 R5 (this gate), §4 (risks). Builds ON R1 `bigville_move_world` (movement+energy),
R2 `bigville_need_world` (needs+preference/satisficing), R3 `bigville_time_world`
(day/night + sleep + exhaustion collapse), R4 `bigville_econ_world` + its 5 econ
seeds (production / exchange / supply / debt / expectation), and the scaffold
`bigville_sim_world` + the 245/247/248 drama cast (`bigville_townspeople_30.json`,
`bigville_drama_social.json`). Reuse ALL by import; edit no tracked file.

R5 is the INTEGRATION rung: run the full day loop over MULTIPLE days with the
30-cast, the economy (R4), the clock (R3), movement (R1), needs+preference (R2),
AND the John/Mary drama (245) live together. Every decision stays a RULE; the
adapter only sequences ticks + reads. **Measure-first — a sustained loop AND a
surfaced breakdown are BOTH valid results. Do NOT force a "success".**

## Seed-claim (verbatim `check_claim`, run before anything)

```
SEED CLAIM 253000-253999: CLEAN -- no collision DETECTED.
  Scope: 973 files with seed sinks; 681 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

## What R5 adds (graph-native, ZERO new Rust)

The ONLY new mechanism is the economy→affect→SOCIETY closing hop, one additive
seed `seeds/bigville_loop_reputation.json` (2 rules) composing existing DSL Terms:
- **`bl_badmouth`** — a creditor soured by a DEFAULT (R4 `be_default_affect` set
  `demand_cash=1`) BADMOUTHS the defaulting debtor: the debtor's `badmouthed`
  reputation-harm counter rises by the creditor's `badmouth_strength`, a `Badmouth`
  node is minted. One-shot per obligation (`badmouth_done`). Roots at debtor/owe and
  traverses `creditor` **OUTGOING** (`owe -creditor-> cred`) — the SAME safe direction
  `be_default`/`be_default_affect` use, so a creditor owed by MULTIPLE debtors
  (multiple incoming `creditor` edges) does NOT break matching (probed live: 2 debtors
  → both default, `unpaid=10`, affect flips twice — see Results §hazard).
- **`bl_townsfolk_opinion`** — a townsperson's backing of that debtor flips via the
  SAME `standing > testimony` comparison 245's `bd_villager_backs` uses:
  `backs_debtor = (standing > badmouthed·badmouth_weight) ? 1 : 0`. Before any
  default `badmouthed=0 → backs=1`; the cascade raises `badmouthed` past `standing`
  → `backs` flips 1→0.

Everything else reuses R1–R4 by import. No `runners/dsl` change (target: EMPTY diff).

## Pre-registered gates (`tests/test_bigville_loop_migrated.py`)

### G-town-runs (MEASURE-FIRST — sustain OR surface a real failure)
Over a multi-day run of the day-loop (work → produce → buy up/down chain → consume →
tire → sleep → journal) with the cast placed on the grid:
- **Report what emerges either way.** Whether the town SUSTAINS (needs met at steady
  state) or surfaces a REAL failure (a shortage, a hoarder, a keeper who drinks and
  doesn't open) is a MEASUREMENT, not a pass/fail. Both are valid results.
- **Glass-box:** paste ONE villager's whole DAY read straight off the graph —
  Marjorie Dough (baker): wake → bake during hours (yield ∝ skill) → sell bread to a
  hungry buyer (coin in) → buy grain up-chain from the farmer → tire (energy depletes) →
  sleep (energy replenishes) → journal. Every number a graph read-off.
- **Gate (structural, not an outcome):** the loop advances N≥3 days without crashing;
  the day-phases each fire their rules; at least one full producer→consumer exchange and
  one up-chain restock complete; the honest per-day census (hunger / coin / energy /
  stock per agent) is recorded. The measured verdict (sustain vs which breakdown) is
  reported, not asserted.

### G-fishmonger-cascade (HEADLINE — the anti-bullshit gate, every hop off the graph)
Induce the keeper Doreen Ferrety's (fishmonger, cast #19) exhaustion collapse (R3:
she drinks — a real ale exchange drops her coin — and is pushed past the energy
threshold → involuntary collapse), then read the FULL emergent chain, nothing scripted:
- **(a) missed opening → expectation-SURPRISE (R4).** Collapsed keeper → `be_shop_shut`
  → `open=0` at the scheduled open moment → `be_expect_surprise` mints a `Surprise` for
  a would-be customer holding an `Expect` about her stall. **Control:** keeper opens on
  time (`open=1`) → NO surprise.
- **(b) DOWN-chain: no fish → fish-preferrers satisfice elsewhere (R2 preference) →
  ripple.** A villager who PREFERS fish runs the R2 `decide()` Argmax: fish source
  reachable → picks fish; fish source removed-because-the-stall-is-shut → the same
  villager satisfices to BREAD (the choice flips on availability, preference unchanged —
  R2's proven distance/reachability flip). Glass-box: "wanted fish, took bread — the
  stall was shut."
- **(c) UP-chain: coins on drink → can't pay the fisherman → fisherman UNPAID → his
  AFFECT flips → he refuses further credit / BADMOUTHS Doreen → the 245 credibility/
  social layer MOVES.** Doreen short of coin buys fish on CREDIT from the fisherman
  (R4 `be_restock_credit` → `owes` minted), DEFAULTS past term (R4 `be_default`), the
  default flips the fisherman's AffectiveState (R4 `be_default_affect`: arousal ↑,
  valence ↓, `credit_trust` < 0, `demand_cash=1`), and the soured fisherman BADMOUTHS
  Doreen (R5 `bl_badmouth`: `doreen.badmouthed` rises, `Badmouth` node minted) →
  townsfolk who opine on Doreen flip their backing 1→0 (R5 `bl_townsfolk_opinion`).
- **The gate that makes it non-bullshit:** EVERY consequence above is a real STATE
  change (a number that gates a rule) that CHANGES an affective/backing state — the
  economy→affect→society loop is CLOSED, not narrated.

### G-propagates-along-the-graph (the falsifier — proves nothing is authored)
SEVER the `supplied_by` edge (Doreen's shop → fisherman's shop) BEFORE the restock →
- the up-chain default does NOT occur (no `owes` minted),
- the fisherman's affect does NOT flip (`arousal` unchanged, `demand_cash=0`),
- no badmouth (`doreen.badmouthed=0`, zero `Badmouth` nodes),
- townsfolk backing STAYS 1 (no flip).
Every downstream consequence VANISHES when the dependency edge is cut — proving the
whole cascade FLOWS ALONG THE GRAPH and is not scripted. (Live-validated in dev; the
recorded run is the registered measurement.)

### G-discipline (HARD — every item reported in Results)
- base SHA (merge-base) = `1450c77a80d44789ece12d901a24f8d96d14e7c4` (verified);
  prereg on a SEPARATE commit before any recorded number.
- **NO Rust:** `git diff` on `runners/dsl` is EMPTY (incl. `term.rs`). If a new
  primitive seemed needed, STOP and report — not taken.
- **Own engine:** `cargo build --release` in this worktree; assert
  `source_match ∈ {own, shared}` (INVARIANT — never a pinned `.so` md5). Own `.so`
  md5 recorded; canonical `.so` md5 start==end (UNTOUCHED — the pre-existing peer-build
  main provenance red is NOT mine; the enumerated baseline is the arbiter).
- **Oracles:** `scripts/rung7_vision_bench.sh` + `scripts/per_area_settlement_regression.sh`
  fail-set ⊆ enumerated `results/failure_baseline.json`; `test_failure_baseline_migrated`
  green; ZERO new reds.
- **Additive only:** all-new files prefixed `bigville_loop_`
  (`seeds/bigville_loop_reputation.json`, `worlds/bigville_loop_world.py`,
  `scripts/bigville_loop_run.py`, `tests/test_bigville_loop_migrated.py`,
  `tools/author_bigville_loop_seeds.py`, this prereg, results). NO tracked file edited;
  R1–R4 + scaffold + 245 reused BY IMPORT.
- **Source-audit:** no `if`/`else` over graph state selects an agent action; every
  produce / buy / credit / default / affect-flip / badmouth / opinion / open-shut /
  surprise / satisfice is a seed RULE. The adapter only ingests, arms one-shot flags,
  ticks, and reads.

## Pre-registered RISKS (spec §4)
- **All-pairs trap (economy).** Exchange is LOCAL (co-located only) — R5 does not
  re-run the scale probe (that was R4's gate); it inherits R4's local-exchange design.
- **Energy death-spiral.** Exhaustion collapse must not cascade into an unrecoverable
  all-collapse town; restful sleep is the escape. MEASURE whether the town recovers or
  spirals; a spiral is a FINDING, not a crash to hide.
- **Two-register confusion.** Store-hours is an EXPECTATION (predict→surprise), NOT a
  law (→ censure). The R5 badmouth is a REPUTATION/credibility move (the 245 register),
  distinct from the enforcement (247) register — the reputation seed touches no
  enforcement/censure rule (source-audited).
- **Multi-debtor edge hazard (CLAUDE.md engine gotcha).** A creditor owed by multiple
  debtors accrues multiple incoming `creditor` edges. All debt/reputation rules root at
  debtor/owe and traverse `creditor` OUTGOING, so this does not break matching — probed
  live and reported.

## Addendum — creator refinements (registered mid-task, BEFORE the recorded numbers)

Two SHARPENINGS of G-town-runs arrived from the creator after the base prereg
commit; both are additional MEASUREMENTS (measure-first), not new claims that could be
gamed, and both are registered here before the results doc records any number:

- **Carrying capacity (harvest vs demand).** The town SUSTAINS only if harvest
  (producers × skill × yield) meets consumption (heads × need-rate). G-town-runs now
  MEASURES and reports the resource BALANCE explicitly: per key good, production
  CAPACITY (Σ producer skill/day), consumption DEMAND (population need + downstream
  input draw), and the MARGIN = capacity − demand (positive = sustaining; negative =
  drawing down / famine). The DEFAULT is seeded to a VIABLE regime (a living town that
  sustains) — NOT by fudging: the carrying-capacity knob is NAMED (the baker's skill =
  the town's bread harvest ceiling), and a `shortfall` regime (capacity < demand) is
  ALSO measured, showing the mechanism is real (famine when the knob is turned down).
  Any self-CORRECTION under shortage (labour/production shifting to the scarce good) is
  observed and reported; building learned reallocation is R6 — R5 only observes whether
  the town self-corrects or collapses.
- **Money conservation (FIXED supply).** Total coin is FIXED — every exchange / wage /
  restock / repayment is a TRANSFER of existing coin, never a creation. `run_town`
  ASSERTS Σcoin over all agents is INVARIANT across the whole loop; a drift is a
  currency-minting rule (a bug to surface, not ignore). The consumers' daily income is
  therefore a CONSERVING wage transfer from the producer pool (disclosed abstraction of
  the wage loop), not a mint. Reported as part of G-discipline. Any monetary dynamics
  observed (coin pooling in few hands, circulation thinning, trade seizing though goods
  exist) are noted (a `wages_on=False` probe surfaces exactly this).

## Honest scope (pre-committed)
Synthetic model; N≤30 cast; mechanism-proven ≠ benchmark value. The 30-cast provides
the drama + the economic actors; the fish-supply chain's up-chain **fisherman** is an
added supplier because the shipped cast has a fishmonger (Doreen) but no upstream
fisherman — the DEBTOR whose credibility moves (Doreen) is a real cast member, so the
"245 moves" hop lands on the cast. Measure-first: the town-run verdict is REPORTED
(sustain or the specific breakdown), never forced.
