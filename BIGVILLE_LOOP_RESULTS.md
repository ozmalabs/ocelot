# BIGVILLE R5 — THE LOOP CLOSES + emergent cascades — RESULTS

**Block 253000.** Prereg: `BIGVILLE_LOOP_PREREG.md` (committed before any number, +
a mid-task creator-refinement addendum committed before these numbers). Build:
`seeds/bigville_loop_reputation.json`, `worlds/bigville_loop_world.py`,
`scripts/bigville_loop_run.py`, `tests/test_bigville_loop_migrated.py`,
`tools/author_bigville_loop_seeds.py`. Everything else (R1 movement+energy, R2
needs+preference, R3 day/night+sleep+collapse, R4 economy/supply/debt/expectation, the
scaffold + 245 drama) reused BY IMPORT — no tracked file edited. ZERO new Rust.

R5 is the INTEGRATION rung, and it is MEASURE-FIRST. Headline findings below; every
number is read straight off the graph (`results/bigville_loop/demo.json`).

---

## G-town-runs — the multi-day loop (measure-first: it SUSTAINS, and the probes bite)

**The DEFAULT living town (viable regime, wage loop on) SUSTAINS a 4-day loop.** Every
consumer is fed every day (`unmet_demand=[]` all 4 days), money is conserved, and the
carrying-capacity margins are non-negative on every staple.

### Marjorie Dough's WHOLE day, phase by phase, off the graph (glass-box)
```
wake  : energy 100, coin 30
open  : shop_open=1  (day phase, business hours; keeper awake)
bake  : grain 2 -> baked 5 loaves to stock   (yield = baker skill = 5)
sell  : sold 4 loaves -> +16 coin            (four consumers buy)
town  : 4 loaves eaten (leave the town)       (consumption destroys the good)
restock: bought grain up-chain from the farm -> grain back to 2
sleep : night, safe at home -> energy 100 (restful)   end coin 38
```
Marjorie earns from bread, buys grain from Ferdinand up-chain, and the coin she takes in
is the coin the wage loop pays back out to the workers — the loop CLOSES.

### Carrying capacity — harvest vs population demand (the measured resource BALANCE)
Per key good: production CAPACITY (Σ producer skill/day) − consumption DEMAND
(population need + downstream input draw) = MARGIN.

| good  | capacity | demand | **margin** | reading |
|-------|:--------:|:------:|:----------:|---------|
| grain | 3 | 3 | **0** | farm feeds baker+brewer, exactly balanced |
| bread | 5 | 4 | **+1** | harvest exceeds population bread-need → all fed, small buffer |
| ale   | 3 | 0 | **+3** | brewed, nobody drinks in the loop → surplus |
| fish  | 4 | 0 | **+4** | caught, no fish-buyer in the loop → surplus |
| bait  | 2 | 2 | **0** | balanced (fisherman draws it) |

The observed day-over-day town-goods balance corroborates this (bread +1/day: 5 baked −
4 eaten). **Positive/zero margins ⇒ the town sustains on the harvest side.**

### Money is CONSERVED (fixed supply)
Σcoin over all agents = **448.0**, INVARIANT across all 4 days (drift 0.0). Every flow —
exchange, wage, restock, repayment — is a TRANSFER of existing coin; `run_town` asserts
the invariant each day. No rule mints or burns currency.

### The town does NOT trivially sustain — two protected probes surface REAL failures

- **PROBE `wages_off` — money POOLS, demand SEIZES though goods are plentiful.** With the
  wage loop off, carrying capacity is unchanged (bread margin still **+1**, goods
  plentiful) and Σcoin is still conserved (448) — but coin drains one-way from consumers
  to producers. By **day 4 ALL four consumers are broke (coin 0) and unmet**, while
  producers have pooled the money (Ferdinand 62, Marjorie 62, fisherman 42, baitseller
  38). **Trade seizes even though the bread exists.** Carrying-capacity viability is
  NECESSARY BUT NOT SUFFICIENT — money must CIRCULATE, not merely be conserved.
- **PROBE `shortfall` — carrying-capacity FAMINE, and it spreads.** Turn the named knob
  DOWN (baker skill 5→3, bread capacity 3 < demand 4 → margin **−1**) and a real famine
  appears and COMPOUNDS: unmet demand grows `[Nettie] → [Bram,Nettie] →
  [Agnes,Bram,Nettie] → [all four]` over the four days. The town does **NOT self-correct**
  — no labour reallocation shifts production to the scarce good (that is R6 learning);
  R5 observes the collapse honestly. The knob is the baker's harvest ceiling, not a
  hand-forced number: the viable regime (skill 5) feeds everyone; the shortfall regime
  (skill 3) starves the margin.

**Verdict (measure-first): the default town SUSTAINS; the mechanism is real (turning the
harvest knob down produces famine; turning the wage loop off seizes trade).** Both a
sustained loop and surfaced breakdowns — exactly what R5 asked for.

---

## G-fishmonger-cascade (HEADLINE — the anti-bullshit gate, every hop off the graph)

Induce Doreen Ferrety's (fishmonger, cast #19) exhaustion collapse, then read the full
emergent chain — nothing scripted, each hop a real state change gating the next:

| hop | mechanism | state change (off the graph) |
|---|---|---|
| **drink** | R4 local exchange | Doreen buys ale → **coin 3 → 0**, ale_held 1 (coins really leave her) |
| **collapse** | R3 exhaustion | pushed past threshold, no sleep option → **sleep_kind=2 (involuntary), collapsed=1** |
| **(a) missed opening** | R4 `be_shop_shut` + `be_expect_surprise` | collapsed keeper → **stall_open=0** at the due moment → the town's held expectation is violated → **surprise=1** (predict-and-residual, NOT censure) |
| **(b) down-chain satisfice** | R2 preference Argmax | the fish-preferrer chose **FISH (12)** with fish reachable; the stall shut removes the fish source → the SAME preferrer **satisfices to BREAD (11)** — "wanted fish, took bread, the stall was shut" |
| **(c) up-chain default** | R4 `be_restock_credit`+`be_default` | drank → short of coin → buys fish on credit (owe minted) → **defaults** past term (`default_count=1`) |
| **(c) affect flips** | R4 `be_default_affect` (204000/239000) | fisherman **arousal 0 → 4, valence 5 → 2, demand_cash=1, unpaid=5** — the felt weight is INCURRED |
| **(c) society MOVES** | R5 `bl_badmouth` + `bl_townsfolk_opinion` | soured fisherman **badmouths Doreen** (`badmouthed 0 → 3`, 1 `Badmouth` node) → townsfolk backing of Doreen **flips [1,1,1] → [0,0,0]** (the 245 credibility layer moves) |

**The economy → affect → society loop is CLOSED**: a material default becomes an
affective flip becomes a social-credibility move — each a real number that gates a rule,
none narrated.

## G-propagates-along-the-graph (the falsifier — nothing is authored)

SEVER the `supplied_by` edge (Doreen's stall → fisherman's shop) and the ENTIRE
downstream cascade VANISHES:

| quantity | edge present | **edge severed** |
|---|:---:|:---:|
| owe minted | 1 | **none** |
| Doreen defaulted | 1 | **0** |
| fisherman arousal | 0 → 4 | **0 → 0 (unchanged)** |
| fisherman demand_cash | 1 | **0** |
| Doreen badmouthed | 3 | **0** |
| Badmouth nodes | 1 | **0** |
| townsfolk backing | [0,0,0] | **[1,1,1] (unchanged)** |

Cut the dependency edge and the shortfall, the affect flip, and the society move all
disappear — proving every consequence FLOWS ALONG THE GRAPH.

---

## The multi-debtor `creditor`-edge hazard — PROBED, does NOT bite

The R4 agent flagged that a creditor owed by multiple debtors accrues multiple incoming
`creditor` edges (the CLAUDE.md engine gotcha). **Probed live: two fishmongers each
owing one fisherman → BOTH default, `unpaid=10`, the fisherman's affect flips TWICE
(arousal 0 → 8).** The R4 debt rules and the R5 `bl_badmouth` rule all root their match
at the debtor/owe and traverse `creditor` **OUTGOING** (`owe -creditor-> cred`), so
multiple incoming `creditor` edges on one creditor do NOT break matching. No distinct
edge type was needed; the hazard was avoided by construction, and verified.

---

## Discipline ledger

| item | value |
|---|---|
| base SHA (merge-base) | `1450c77a80d44789ece12d901a24f8d96d14e7c4` (verified == merge-base) |
| prereg commit SHA | `95dc3cbce4` (base) + `5428439623` (creator-refinement addendum) — both before these numbers |
| own engine `.so` md5 | `10f65be659e0d9a9290aff39f7f5b92a` (byte-identical to the 245/246/R4 reference build) |
| `source_match` | **own** (INVARIANT `source_match ∈ {own, shared}` asserted by `test_engine_provenance_migrated` 7/7; never a pinned md5) |
| `runners/dsl` diff vs base | **EMPTY** (no Rust; the reputation seed composes existing DSL Terms) — asserted by a gate |
| canonical `.so` md5 | `fd82dc2978dbb055496dd82390ac2ebe` start == end (UNTOUCHED; the pre-existing peer-build main provenance red, not mine — the enumerated baseline is the arbiter) |
| `test_failure_baseline_migrated` | green (11/11) |
| oracles (rung7 / per_area) | fail-set ⊆ enumerated `results/failure_baseline.json` — see below |
| gate count | **10/10** (`tests/test_bigville_loop_migrated.py`) |
| money-conservation check | Σcoin invariant (drift 0.0) in ALL regimes — asserted in `run_town` + a gate |
| additive-only | all new files `bigville_loop_` prefix; NO tracked file edited; R1–R4 + scaffold + 245 reused by import |
| source-audit | no `graph_rewrite`/`gr.run`/`_match`/`_apply`/`make_rule` in the adapter; every decision a seed rule (gate) |

### Oracle fail-sets (⊆ enumerated `results/failure_baseline.json`; ZERO new reds)
- **rung7_vision_bench.sh:** **214 passed, 10 skipped, 0 failed** (own engine). Clean.
- **per_area_settlement_regression.sh:** **278 passed, 5 skipped, 23 failed** — all **23
  failing node ids ⊆ the enumerated baseline** (cross-checked against the baseline's 570
  enumerated ids: **0 of my 23 are absent from the baseline** → ZERO new reds). The reds
  are the pre-existing `test_topic_route_selfheal_migrated` / conversation-routing set,
  untouched by this rung. `test_failure_baseline_migrated` green (11/11).

---

## Honest residuals / scope

- **Synthetic model, N≤30 cast.** Mechanism-proven ≠ benchmark value. The town is a
  curated economic sub-network over the shipped cast (farmer→baker/brewer→consumers,
  baitseller→fisherman→fishmonger).
- **The fish-supply up-chain `fisherman` (+ `baitseller`) are ADDED suppliers** — the
  shipped cast has a fishmonger (Doreen) but no upstream fisherman. The DEBTOR whose
  credibility moves (Doreen) is a real cast member, so the "245 moves" hop lands on the
  cast.
- **Keepers do not tire from standing** — only MOVEMENT depletes energy (R1), so
  Marjorie's day shows restful sleep but no movement-fatigue (the walking consumers do
  tire). Honest to the R1 model.
- **The wage loop is a DISCLOSED abstraction** of consumer income (a CONSERVING
  producer→worker transfer, never a mint) — per-trade wage learning is R6. It is a
  transfer, so money conservation holds exactly.
- **No self-correction under shortage** (labour reallocation to a scarce good) — that is
  R6; R5 observes the famine spread honestly rather than papering over it.
- **The 245 John/Mary drama** runs on the scaffold coupled by movement (the R1-proven
  coupling); R5's new society hop is the badmouth→credibility move on the economic cast,
  built with the same testimony>standing arithmetic 245 proved.
- **The town-run and the fishmonger cascade are separate demonstrations** (the cascade is
  a curated registered demonstration, per spec) — both read entirely off the graph.
