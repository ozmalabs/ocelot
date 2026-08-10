# BIGVILLE R11 — THE OPEN WORLD: travellers + the inn + SCOPE-GATING — RESULTS

**Block 259000.** Prereg: `BIGVILLE_WORLD_PREREG.md` (committed before any number
here). Spec: `BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` §2.7 + §3 R11. Base merge-base
`6de883c92c`. All gates below are the pre-registered ones; numbers are measured.

## Discipline (all green)

| check | result |
|---|---|
| `test_bigville_world_migrated` | **16/16 green** (deterministic across 3 runs) |
| `test_failure_baseline_migrated` (enumerated-baseline arbiter) | **11/11 green** |
| `test_engine_provenance_migrated` | **7/7 green**, `source_match = shared` |
| `git diff 6de883c92c -- runners/dsl` (incl `term.rs`) | **EMPTY** (no Rust) |
| canonical shared `.so` md5 START == END | `fd82dc2978dbb055496dd82390ac2ebe` (**unchanged**) |
| new files | additive `bigville_world_*` only; no tracked file edited |
| seeds | four R11 seeds all `self_load_only` |

Per SUPERVISOR+USER directive (2026-07-29) the ~43-min oracles
(`per_area_settlement_regression.sh`, `rung7_vision_bench.sh`) were NOT run: a
purely-additive, no-Rust, `self_load_only` rung cannot regress other suites, so the
fast baseline gate + additive discipline is sufficient.

## G-scope-gating (HEADLINE — the compute thesis)

Per-tick COST for a FIXED in-scope population (N_in = 10) as the OUT-OF-SCOPE world
grows, ON (dormant = bare persisted node, no activity wiring) vs OFF (ablated: the
whole world wired). Instruments: wall-clock µs/tick AND the engine's `rule_costs`
cost-units for `bw_run_in_scope` (deterministic). `results/bigville_world/summary.json`.

| total world | ON µs/tick | ON cost-units | OFF µs/tick | OFF cost-units |
|---:|---:|---:|---:|---:|
| 10   | 198.5 | 2675 | 162.4 | 1916 |
| 100  | 155.3 | 1847 | 1177.5 | 19649 |
| 500  | 153.6 | 1837 | 5423.5 | 94569 |
| 1000 | 175.6 | 2199 | 11431.7 | 201403 |
| 3000 | 247.8 | 3004 | 31605.2 | 556481 |

- **ON is FLAT in the out-of-scope world.** Growing the total world 10 → 3000
  (300×) barely moves the ON cost: cost-units stay ≈ 1800–3000, µs/tick ≈ 150–250.
  Compute is ∝ the IN-SCOPE population, NOT the total world — an unbounded traveller
  world costs only what is in view. (ON wall-clock growth factor ≈ 1.25; the mild
  cost-unit rise is node-count accounting overhead, ≈ 1.6× over a 300× world.)
- **OFF (ablated) GROWS ~linearly with the TOTAL world.** cost-units 1916 →
  556481 (≈ 290×), µs/tick 162 → 31605 (≈ 195×). This is the falsifier landing:
  remove scope-gating and every out-of-scope agent RUNS, so cost tracks the total
  world — the cost we must NOT pay.
- **At the largest world (total = 3000) OFF is ≈ 127× more expensive per tick than
  ON.** The falsifier bites hard.

Mechanism (glass-box): dormancy is STRUCTURAL, not a `where`-filter. A dormant
agent is a bare persisted node with its activity wiring (`active_beat` /
`active_clock`) dissolved into the frontier, so the matcher for `bw_run_in_scope`
never scans it. (A naive `in_scope==1` `where`-guard was measured to STILL cost
∝ total, because the matcher scans every candidate before the guard filters —
dormancy must remove the agent from the match, which is what dissolving the wiring
does.) A dormant agent's attrs are **byte-identical** across dormant ticks and
survive a `graph_to_dict` snapshot; re-entry re-attaches the wiring and it resumes
running from its persisted state — verified in
`test_dormant_agent_is_byte_identical_and_reactivates` and
`test_the_whole_world_round_trips_as_a_durable_dict`.

## G-open-economy

- **Inn stay INJECTS external coin, logged.** A passer-through paying `lodging_cost
  = 5`: inn coin 50 → 55 (internal +), traveller coin 100 → 95 (external −),
  `Ledger.external_influx = 5` (the boundary crossing logged). Σcoin conserved
  internally EXCEPT the logged external point.
- **Import moves coin ACROSS the boundary for a good bigville cannot produce.** A
  resident buys a `produced_locally = 0` good (price 12): resident coin 40 → 28,
  traveller coin 100 → 112 (coin leaves town), `external_outflux = 12` logged, the
  resident `owns_good` it — bigville is no longer autarkic.

## G-travellers-are-full-agents

One PERSISTED node with held state (coin/story/goal) REOCCURS remembered: across
two visits the SAME node id accrues `visits` 1 → 2 and `familiarity` 1 → 2, the
innkeeper's `knows` edge is minted once on the first visit and persists, and the
held `story` attr survives both visits (no re-roll). The whole world round-trips as
a durable dict.

## G-news-from-the-frontier (Giantville)

- **Second-hand < grounded.** A traveller's news yields a hearsay belief
  (`provenance_hearsay = 1`, confidence = the teller's credibility 0.7); a resident
  who VISITED holds a grounded belief (`provenance_grounded = 1`, confidence 1.0).
  hearsay 0.7 < grounded 1.0.
- **Credibility distorts.** A less credible teller (0.2) yields a lower-confidence
  hearsay belief than a credible one (0.7) — same place, different teller.
- **Control (absence):** with no traveller and no visit, a resident holds NO
  Giantville belief across 3 ticks — the frontier stays unknown (unknown = absence,
  first-class).

## G-dream-of-moving → departure (R8 + R11)

The full pipeline: an in-scope resident holding an R8 Giantville Dream runs each
tick (age → 2); a traveller RECRUITER `recruits` it and offers →
`bw_recruiter_grounds_path` mints a `grounded_path Dest{to_giantville}` on the
dream (the concrete "recruiter with a grounded_path" R8's `gg_dream_collapse_path`
references); arming R8's collapse fires it → dream `collapsed = 1`, `left = 1`,
exactly one `ActionGoal{leave}` minted; the next tick `bw_dissolve_on_leave`
dissolves the resident's activity wiring → `in_scope = 0`, `dormant = 1` — leaving
for the big city IS the dream → departure → out-of-scope pipeline (emigration tied
to scope-gating). The departed resident REOCCURS as a returning traveller who has
now GROUNDED Giantville: its belief is grounded (first-hand), not hearsay.
**Control:** no recruiter → no grounded_path → the dream does NOT collapse even
when armed, and the resident stays in scope.

## Honest residuals

- **Synthetic, small N.** The scope-gating curve is a micro-benchmark on synthetic
  agents (a heartbeat as the per-tick "simulation"). The claim is the SHAPE (flat
  ON vs ~linear OFF, ≈127× separation at total = 3000), not an absolute throughput.
  ON wall-clock carries GC/measurement noise; the deterministic cost-unit instrument
  is the clean witness.
- **Comprehension is a minimal fold.** `bw_news_secondhand` is a graph-native
  stand-in for the full 244/246 comprehension pipeline (not a `self_load_only` R11
  artifact); it demonstrates the provenance/confidence boundary, not the parse.
- **Frontier arrival is adapter I/O.** Materializing a traveller (add node +
  wiring) is an external boundary-crossing event the adapter ingests; the DISSOLVE
  half (departure → dormant) is a rule — the honest boundary (you cannot run a rule
  on a node not yet in the active set). Re-entry clears the leave-flag mechanically.
