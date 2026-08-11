# BIGVILLE R4 — ECONOMY (block 252000) — RESULTS

**Measured 2026-07-29.** Pre-registered in `BIGVILLE_ECON_PREREG.md` (separate
commit `afe7d8c33d`, BEFORE any number). Graph-native, ZERO new Rust. Built ON
R1/R2/R3 + the 245/247/248 scaffold + the 248000 scale harness, all by IMPORT;
no tracked file edited. Every decision is a seed RULE
(`seeds/bigville_econ_{production,exchange,supply,debt,expectation}.json`); the
world adapter (`worlds/bigville_econ_world.py`) only ingests, arms a one-shot flag,
ticks the Rust `run_rules` fixpoint, and reads state.

All 8 pre-registered gates PASS (`tests/test_bigville_econ_migrated.py` 8/8).

## G-buy — a hungry buyer with coin navigates to the baker and buys bread

Glass-box read-off (`results/bigville_econ/demo.json`), every hop a rule verdict:

```
baked 3 bread (be_produce: yield = keeper BAKING skill = 3; 1 grain consumed)
shop open = 1        (be_shop_open: keeper awake + in business hours)
navigated 2 hops to (2,2)   (R1 movement flood -> the baker's cell)
buyer coin 10 -> 6   (be_exchange: paid price 4)
keeper paid: coin 4  (the seller received it)
stock 3 -> 2         (one bread sold)
hunger 8 -> 3        (satiety 5 dropped hunger)
bread held: 1        (buyer inventory Good{bread}.qty)
```

The full R1→R2→R3→R4 chain: navigate (R1) to the baker during opening hours
(R3 clock), LOCAL exchange (R4), hunger drops.

### Failing controls (each verified to actually fail — no sale)
| control | mechanism | result |
|---|---|---|
| **no coin** (2 < price 4, credit off) | `be_exchange` coin≥price fails; `be_credit` TRUST≤0 | coin 2, stock 3 unchanged; **no `owes` edge** |
| **no baker at post** (keeper away from shop cell) | `be_exchange` keeper `is_at cell` fails | stock 3, buyer coin 10 unchanged |
| **baker with no grain** (input qty 0) | `be_produce` input≥1 fails | stock stays 0 (no bread produced) |
| **stall CLOSED / keeper collapsed** (R3 collapse) | `be_shop_shut` sets `open=0` | shop open=0; stock 3, buyer coin 10 unchanged |

## G-supply+debt (HEADLINE) — the material chain + the default affect flip

Three-tier sparse supply graph `fishmonger -supplied_by-> fisherman
-supplied_by-> baitseller`.

### Material propagation (up-chain), read off the graph
| fisherman | income this cycle | fish output NEXT cycle |
|---|---|---|
| **PAID** (fishmonger flush, pays 5) | 5 | **4** (buys bait, `be_produce` yield = FISHING skill 4) |
| **UNPAID** (fishmonger broke, no credit) | 0 | **0** (no coin → can't buy bait → no production) |

The fishmonger's cash shortage propagates UP the `supplied_by` edge: the fisherman
goes unpaid → cannot restock bait → his fish output FALLS next cycle
(`unpaid_out 0 < paid_out 4`). Nothing scripted; it flows the graph.

### Default → creditor affect flip (economy → affect → behaviour)
Fishmonger short of coin; the fisherman EXTENDS credit (`be_restock_credit` mints
`Owe{amount:5, due_epoch:1}` along the supplies edge). Advance past term
(`now_epoch 5 > due_epoch 1`):

```
be_default:        owe.defaulted = 1 ; fisherman.unpaid = 5 (material harm)
be_default_affect: fisherman arousal 0 -> 4 ; valence 5 -> 2   (204000/239000 channel)
                   credit_trust 50 -> -30  (next credit decision now REFUSES)
                   demand_cash = 1
```

The felt weight is INCURRED as real state change and feeds back into the next
credit decision — not narrated.

**Control — debtor pays** (`be_repay` before term): owe `paid=1` → no default, no
affect flip (fisherman arousal 0 / valence 5 unchanged), credit_trust stays 50.

### Sever control — propagation is edge-mediated, not scripted
| `supplied_by` edge | `owes` minted | creditor arousal after term |
|---|---|---|
| **PRESENT** | 1 | 4 (flipped) |
| **SEVERED** | 0 | 0 (untouched) |

Sever the edge and the up-chain obligation is never minted along it → no default →
no affect flip → no downstream shortfall. The effect flows the graph.

## G-expectation — store hours as a HELD PREDICTION (predict-and-residual, NOT censure)

The town holds `Expect{open_due}` about the stall. At the scheduled open moment:

| keeper | `be_shop_shut/open` | `be_expect_surprise` |
|---|---|---|
| **COLLAPSED** overnight | open = 0 (violated) | **1 Surprise{residual}** registered |
| **AWAKE**, opens on time (control) | open = 1 | 0 surprise |

A residual SURPRISE, not a censure. Source-audited: the expectation RULE mints only
`Surprise`/`residual` and references NO enforcement/censure machinery (`censure`,
`Violation`, `enforce`, `backs_mary`, `credibility` all absent from the rule body)
— the two normative registers (expectation-surprise vs law-censure, 247) stay
distinct.

## G-scale (LOAD-BEARING) — the all-pairs trap, economy ON

Re-run of the 248000 scale probe with movement+economy ON
(`results/bigville_econ/scale.json`): N∈{5,10,15,20,25,30}, R=30 placements,
T=12, 2000-sample bootstrap, constant-density torus — the identical instrument to
248000, counting realized EXCHANGE-ops.

| arm | fitted log-log slope | CI95 | per-capita ops |
|---|---|---|---|
| **local** (LOCAL exchange, HEADLINE) | **1.076** | [1.036, 1.108] | ~0.51 (flat = linear) |
| **all_pairs** (global market clear, falsifier) | **2.102** | [2.102, 2.102] | — |

`separated`: local_hi 1.108 < allpairs_lo 2.102 (CI-separated). LOCAL exchange is
sub-quadratic (< 1.5); the deliberate global-market-clear control measures ~2.0,
proving the instrument distinguishes linear from quadratic. **The economy-on arm
did NOT go ~2.0 — no all-pairs bug.**

## Discipline ledger
| item | value |
|---|---|
| base SHA (merge-base) | `51ecd0d7bf5b6ac4a300ad9f67905b9cbf00b9d2` (verified) |
| prereg commit SHA | `afe7d8c33d` (separate, before any number) |
| own engine `.so` md5 | `10f65be659e0d9a9290aff39f7f5b92a` (byte-identical to the 245/246 reference build) |
| `source_match` | **own** (INVARIANT `source_match in {own, shared}` asserted; never a pinned md5) |
| `runners/dsl` diff | **EMPTY** (no Rust; seeds compose existing DSL Terms only) |
| canonical `.so` md5 | `fd82dc2978dbb055496dd82390ac2ebe` start == end (UNTOUCHED; the pre-existing peer-build main red, not mine) |
| `test_failure_baseline_migrated` | green (11/11) |
| oracles (rung7 / per_area) | fail-set ⊆ enumerated `results/failure_baseline.json` (condition: no data/ symlink, own build — matches) — see below |
| gate count | 8/8 (`tests/test_bigville_econ_migrated.py`) |
| additive-only | all new files `bigville_econ_` prefix; no tracked file edited |

## Honest residuals / scope
- **Synthetic model, small N.** The scale gate measures the interaction-op SCALING
  EXPONENT (the all-pairs falsifier), not a benchmark; N≤30. Mechanism proven ≠
  benchmark value.
- **The scale instrument counts exchange-ops, it does not run the full `run_rules`
  economy at N=30 per tick** — exactly as the 248000 instrument counts perception
  pairs rather than running the drama at scale. The claim it establishes is the
  SCALING of the realized LOCAL-exchange interaction (linear) vs a global clear
  (quadratic), the pre-registered falsifier.
- **Production is a per-armed batch** (`produce_armed` one-shot): one production
  event mints `skill`-many units. Learning-by-doing / teaching that makes skill
  DYNAMIC is R6 (block 254000), not here — R4 seeds a few static skills.
- **Credit term / default detection uses an integer `now_epoch`** written onto each
  `Owe` from the world clock (in-frame integer, per the frame/continuum invariant).
- **The 30-cast living-town integration** (the fishmonger cascade running inside the
  full bigville drama over multiple days) is R5 (block 253000); R4 proves each
  mechanism and the material/affect/expectation chains in isolation with protected
  controls.
