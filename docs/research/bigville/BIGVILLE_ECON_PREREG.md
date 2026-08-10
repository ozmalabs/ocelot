# BIGVILLE R4 — ECONOMY (block 252000) — PRE-REGISTRATION

**Status: pre-registered, nothing measured. 2026-07-29.** This document is
committed BEFORE any number exists (separate prereg commit). It fixes the gates,
the failing controls, the instrument, and the discipline ledger for R4 —
*production + LOCAL exchange + supply NETWORK + debt + store hours as
EXPECTATION* — the fourth sub-rung of the bigville movement/economy ladder
(`BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` §2, §2.5, §3 R4, §4).

Built ON, by IMPORT only (no tracked file edited): R1 `bigville_move_world`
(nav/energy), R2 `bigville_need_world` (drive→goal, the preference Argmax →
*buy the PREFERRED good*), R3 `bigville_time_world` (day/night clock → store
hours; a collapsed keeper doesn't open), the 245/247/248 scaffold, and the
248000 scale harness `worlds/bigville_scale_world.py` /
`scripts/bigville_scale_run.py` (re-run with economy ON for the scale gate).
REUSES the economy substrate seeds (`economics`, `net_economy`, `langsim_build`)
and the affect seeds (204000 `core_emotions`, 239000 `arousal_window_coreg`,
via the R3 `bigville_time_concern` AffectiveState channel) for the debt→affect
flip.

## Seed-block claim (verbatim `check_claim(252000, 252999)`)

```
SEED CLAIM 252000-252999: CLEAN -- no collision DETECTED.
  Scope: 971 files with seed sinks; 681 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

`check_claim(252000, 252999)` returned `True`. Block 252000–252999 is claimed by
this rung.

## Architecture commitment (the whole point)

Every DECISION is a graph RULE evaluated by the Rust engine's `run_rules`
fixpoint; the Python world adapter only INGESTS graph data, ARMS a one-shot
flag, ticks, and READS state back. No `if buyer.coin >= price: sell` in Python —
that is `be_exchange`. No new Rust: the R4 seeds compose existing DSL Terms
(`Argmax`, `Sum`, `IfThenElse`, `Plus/Minus/Times`, `Eq/Gt/Gte/Lt`, `And/Or/Not`,
`Neighbours`, `NodesOfType`, `Attr`, `Var`, `Lit`). `runners/dsl` diff MUST be
empty. Source-audit gate below.

### The graph model (all in the isolated R1 movement substrate `self.eng`)

- **Goods** are integer-coded: `COIN`=1, `GRAIN`=10, `BREAD`=11, `FISH`=12,
  `BAIT`=13, `ALE`=14. Coin is a scalar attr `coin` on a Mover (price
  comparisons are in-frame integers). A held good is a `Mover -has-> Good{good,
  qty}` node; a shop's stock is `Shop -stocks-> Good{good,qty}`, its inputs
  `Shop -has_input-> Good{good,qty}`.
- **Shop** `{good, price, open, open_scheduled, activity, input_good, produce_armed,
  cx, cy}` with edges `at_cell -> MoveCell`, `kept_by -> Mover (keeper)`,
  `supplied_by -> Shop (up-chain supplier)`. A shop is a tradesperson's stall AND
  workplace.
- **Skill** `Mover -has_skill-> Skill{activity, level}`. Production yield =
  `Sum` over the keeper's skills of `IfThenElse(skill.activity==shop.activity,
  level, 0)` — exactly one matches; off-specialty yields 0 (grounds
  specialization). Seeded heterogeneously.
- **Obligation** `Mover -owes-> Owe{amount, due_epoch, now_epoch, paid, defaulted,
  affect_done}`, `Owe -creditor-> Mover (keeper)`.
- **Expectation** `Mover(customer) -expects-> Expect{open_due}`, `Expect
  -about_shop-> Shop`. A violation mints `customer -surprised-> Surprise{residual}`
  — predict-and-residual, a DISTINCT register from law/censure (247).

## GATES (pre-registered predicates)

### G-buy — a hungry agent with coin buys bread locally, hunger drops
A hungry buyer WITH coin, co-located at the baker's shop DURING opening hours
(R3 day phase, keeper awake), fires `be_exchange`: `coin -= price`, keeper
`coin += price`, `stocks.qty -= 1`, the buyer's `has->Good{bread}.qty += 1`, and
`hunger_level` DROPS. Read off the graph.

**Failing controls (each must actually fail):**
- **no coin** (coin < price, credit disabled) → NO purchase (coin/stock/hunger
  unchanged), UNLESS credit is extended → an `owes` edge is minted instead
  (the debt path, below).
- **no baker at post** (keeper not co-located at the shop cell) → no exchange.
- **baker with no grain** (`has_input{grain}.qty == 0`) → `be_produce` cannot
  fire → no bread produced.
- **stall CLOSED / keeper collapsed** (R3 collapse → `be_shop_shut` sets
  `open=0`) → NO exchange even though the shop/stock is present.

### G-supply+debt (the material chain — HEADLINE)
Three-tier sparse supply graph `fishmonger -supplied_by-> fisherman
-supplied_by-> baitseller`. A shop restocks its input UP-CHAIN from its supplier
(`be_restock`, needs coin; `be_restock_credit`, mints an `owes` when short and
the supplier extends credit — a `decision_value` trust decision).

- **Material propagation:** the fishmonger with no coin CANNOT pay the fisherman
  → the fisherman goes UNPAID (keeper `coin` does not rise) → the fisherman
  cannot buy BAIT up-chain next cycle → the fisherman's FISH output FALLS next
  cycle (< a PAID fisherman's output) → *his* customers get less. Measured:
  UNPAID-fisherman next-cycle fish output `<` PAID-fisherman next-cycle output.
- **Default → affect flip:** an `Owe` unpaid past its term (`now_epoch >
  due_epoch`) → `be_default` marks it defaulted → `be_default_affect` flips the
  CREDITOR's AffectiveState (arousal UP, valence DOWN — 204000/239000 channel),
  LOWERS the creditor's credit trust below threshold, and sets `demand_cash=1`,
  so the creditor's NEXT credit decision (`be_restock_credit` /`be_credit`)
  REFUSES.

**Failing controls:**
- **debtor pays** (`be_repay` before term) → owe `paid=1` → no default, no affect
  flip, no output gap.
- **sever the `supplied_by` edge** → the up-chain purchase/owe is never minted
  along the (now absent) edge → the creditor is never defaulted-upon → NO affect
  flip and NO downstream shortfall at the fisherman (proves the propagation is
  along the GRAPH, not scripted). With the edge present the flip/shortfall
  appears; with it severed it does not.

### G-expectation (predict-and-residual, NOT censure)
The town HOLDS "the stall opens at 8" (`Expect{open_due}`). A keeper who
collapsed at night (R3) → `be_shop_shut` keeps `open=0` at the scheduled open
epoch → `be_expect_surprise` mints a `Surprise{residual}` for each would-be
customer holding that expectation. This is the substrate's predict-and-residual
loop at the social level — a DIFFERENT register from a LAW violation (247), which
draws CENSURE. The two registers are kept distinct:
- **source-audit:** the expectation seed references NO enforcement/censure rule
  (no `censure`, `Violation`, `enforce`, `bl_*` law rule); it mints only
  `Surprise`/`residual`, no backing/credibility/penalty effect.
- **Control:** keeper OPENS on time (`open=1` at the due epoch) →
  `be_expect_surprise` where-clause fails → NO surprise.

### G-scale (LOAD-BEARING — the all-pairs trap)
Re-run the 248000 scale probe with movement+economy ON (subclass
`BigvilleScaleWorld`; add the realized EXCHANGE-op census). Two arms over the
same N grid `[5,10,15,20,25,30]`, R=30 placements, constant density:
- **local (HEADLINE):** exchange-ops = co-located buyer×shop pairs only (a buyer
  transacts only with a shop AT ITS CELL). Constant shop/buyer density ⇒ realized
  exchange-ops = N·k. Pre-registered gate: **fitted log-log slope < 1.5**.
- **all_pairs (CONTROL / falsifier):** a global market clear — every buyer
  compared to every shop = N_buyer × N_shop ⇒ **slope ~2.0** (`1.8 ≤ slope ≤
  2.2`), and CI-separated ABOVE the local arm (`local_hi < allpairs_lo`).

**If the economy-on (local) arm measures ~2.0, that is a real all-pairs bug to
REPORT, not hide.** Slope = OLS on `log(mean_ops) ~ log(N)`; CI = 2000-sample
bootstrap over placements (identical instrument to 248000).

### G-discipline
- **Base SHA** `51ecd0d7bf5b6ac4a300ad9f67905b9cbf00b9d2` (merge-base verified).
- **Own engine** built here (`cargo build --release`), `source_match == own`,
  own `.so` md5 `10f65be659e0d9a9290aff39f7f5b92a` (byte-identical to the
  245/246 reference build — no Rust changed). INVARIANT asserted:
  `source_match in {own, shared}`, never a pinned md5.
- **`runners/dsl` diff EMPTY** (no Rust). If a new primitive seems needed, STOP
  and report.
- **Canonical `.so` UNTOUCHED:** start md5 `fd82dc2978dbb055496dd82390ac2ebe`
  (a peer's divergent 2026-07-28 build — the pre-existing main provenance red,
  NOT mine); start == end.
- **Oracles** `rung7_vision_bench.sh` + `per_area_settlement_regression.sh`:
  fail-set ⊆ the enumerated `results/failure_baseline.json`;
  `test_failure_baseline_migrated` green; ZERO new reds.
- **Additive only:** all-new files prefixed `bigville_econ_`
  (`seeds/bigville_econ_*.json`, `worlds/bigville_econ_world.py`,
  `worlds/bigville_econ_scale_world.py`, `scripts/bigville_econ_run.py`,
  `scripts/bigville_econ_scale_run.py`, `tests/test_bigville_econ_migrated.py`,
  this file, `BIGVILLE_ECON_RESULTS.md`, `results/bigville_econ/*`). No tracked
  file edited; R1/R2/R3 + scaffold + 248 harness reused by import/subclass.
- **Source-audit:** the world adapter calls NO Python rule engine
  (`graph_rewrite`, `gr.run`, `make_rule`, `gr._match`, `gr._apply` absent) and
  holds no economy decision; every production/exchange/credit/default/
  expectation decision is a named seed rule.

## Pre-registered RISKS (spec §4)
- **All-pairs trap** — economy MUST be local exchange; the G-scale gate is the
  hard falsifier (an economy-on ~2.0 slope is a bug to fix).
- **Two-register confusion** — store-hours is an EXPECTATION (surprise), NOT a
  law (censure). The expectation seed is source-audited to touch no enforcement
  rule.
- **Architecture-rule drift** — no Python economy decision; source-audit gate.

## Gate count (pre-registered): 8 test gates
`test_buy_local_exchange_and_hunger_drops`,
`test_buy_failing_controls`,
`test_supply_debt_default_and_affect_flip`,
`test_supply_sever_edge_no_propagation`,
`test_expectation_violation_is_surprise_not_censure`,
`test_scale_economy_on_is_subquadratic`,
`test_decisions_are_rules_not_python`,
`test_no_new_rust_and_engine_invariant`.
