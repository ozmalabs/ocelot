# BIGVILLE R11 — THE OPEN WORLD: travellers + the inn + SCOPE-GATING — PRE-REGISTRATION

**Block 259000. Pre-registered BEFORE any recorded number.** Spec:
`BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` §2.7 (THE OPEN WORLD: travellers, the inn, and
SCOPE-GATING — a window into a bigger world, affordably) and §3 R11 (this gate).
Builds ON R8 `bigville_goal_dream` (the Giantville escape DREAM; loaded read-only
alongside the R11 seeds — the departure gate reuses R8's `gg_dream_collapse_path`).
Reuse ALL by import; edit no tracked file.

R11 turns bigville from a closed box into a WINDOW onto a bigger world at the cost
of only what is in view. Every decision is a graph RULE; the adapter only
materializes/dissolves graph data at the frontier boundary, arms one-shots, ticks
the Rust `run_rules` fixpoint, and reads state back.

## Seed-claim (run before anything; block 259 CLEAN)

```
SEED CLAIM 259-259: CLEAN -- no collision DETECTED.
  Scope: 973 files with seed sinks; 681 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from one generator.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN. A CLEAN RESULT MEANS 'NO COLLISION
    DETECTED', NEVER 'NO COLLISION EXISTS'.
```

The full block `seed_claim.py 259000 259999` is also CLEAN. R11 uses no
`default_rng` in the seeds (the timing harness seeds nothing agent-facing) — it is
deterministic and registers no measured draw.

## What R11 adds (graph-native, ZERO new Rust) — four additive `self_load_only` seeds

Composing ONLY existing DSL Terms (`Plus`/`Minus`, the comparators `Eq`/`Lt`/`Gt`/
`Gte`, `And`/`Not`/`Exists`/`Neighbours`, `Attr`/`Var`/`Lit`; effects `set_attr`/
`add_node`/`add_edge`/`del_edge`). No new primitive; no `runners/dsl` diff.

- **`seeds/bigville_world_scope.json`** (2 rules) — SCOPE-GATING (HEADLINE).
  - **`bw_run_in_scope`** — an IN-SCOPE agent RUNS each tick. It matches ONLY
    agents that carry the activity wiring (`active_beat` + `active_clock`); on a
    clock-epoch bump it advances (`last_beat ← clock.epoch`, `age += 1`). An
    OUT-OF-SCOPE agent is a bare PERSISTED node with NO wiring, so the matcher
    never scans it → ~0 compute (DORMANT); its attrs are byte-identical across
    dormant ticks.
  - **`bw_dissolve_on_leave`** — the DEPARTURE → dormant DECISION (ties R8): a
    wired agent with `left==1` (set by R8's dream collapse) has its activity
    wiring DISSOLVED (`del_edge active_beat`, `del_edge active_clock`) and goes
    `in_scope=0`, `dormant=1` — it walks off the edge of scope and dissolves into
    the frontier, state persisted.

- **`seeds/bigville_world_open.json`** (4 rules) — the OPEN ECONOMY + full agents.
  - **`bw_inn_stay`** — a passer-through with `stay_armed` pays `lodging_cost`:
    the inn (internal) GAINS it, the traveller (external) LOSES it, and
    `Ledger.external_influx` LOGS the boundary crossing; `visits += 1`. Σcoin is
    conserved internally EXCEPT at the logged external point — coin INJECTED from
    outside.
  - **`bw_inn_bond_first`** — mints the innkeeper's `knows` edge on the FIRST
    visit (`familiarity = 1`).
  - **`bw_inn_bond_return`** — grows `familiarity` on each RETURN visit (a
    returning trader the innkeeper knows across visits — relationships PERSIST).
  - **`bw_import_buy`** — a resident buys a good bigville CANNOT produce
    (`produced_locally == 0`) from a traveller → coin crosses the boundary OUTWARD
    (`external_outflux` LOGGED), the resident `owns_good` it — not autarkic.

- **`seeds/bigville_world_news.json`** (2 rules) — NEWS from the frontier.
  - **`bw_news_secondhand`** — a traveller's `NewsItem about Giantville` is folded
    by a resident (`comprehend_armed`, no belief yet) into a SECOND-HAND
    `GiantvilleBelief{provenance_hearsay:1}` whose `confidence` is the teller's
    `credibility` (distortable → a less credible teller yields a lower-confidence
    belief).
  - **`bw_belief_grounded`** — a resident who `visited` Giantville grounds it
    FIRST-HAND: `GiantvilleBelief{provenance_grounded:1, confidence:1.0}`.

- **`seeds/bigville_world_depart.json`** (1 rule, `depends_on bigville_goal_dream`).
  - **`bw_recruiter_grounds_path`** — the concrete "recruiter with a grounded_path"
    R8's `gg_dream_collapse_path` already references: a TRAVELLER with
    `is_recruiter==1` who `recruits` a resident holding an un-collapsed Giantville
    Dream and offers (`offer_armed`) MINTS a `grounded_path Dest{to_giantville}` on
    the dream. R8's collapse rule then mints `ActionGoal{leave}` (`left=1`), and
    `bw_dissolve_on_leave` takes the resident out of scope.

The adapter (`worlds/bigville_world_world.py`) holds NO decision: it builds its own
engine, loads the four R11 seeds + R8 `bigville_goal_dream`, materializes/dissolves
frontier graph data (traveller enters = add node + activity wiring; departs =
detach wiring), wires `lodges_at`/`logs`/`hears`/`about`/`visited`/`recruits`/
`has_dream` edges, arms one-shots, bumps the clock, runs `run_rules`, reads back.

## Pre-registered gates (numbers filled in RESULTS after the run)

- **G-scope-gating (HEADLINE — the compute thesis).** With N_in in-scope agents and
  N_out out-of-scope (dormant, unwired) agents, measure per-tick COST (wall-clock
  µs/tick AND the engine's `rule_costs` cost-units for `bw_run_in_scope`) as N_out
  grows for FIXED N_in. **PASS ⟺** with scope-gating ON the per-tick cost is FLAT
  in N_out (compute ∝ N_in only, the total world unbounded and free), a dormant
  agent's state is byte-identical across dormant ticks, and re-entry reactivates
  it. **FALSIFIER (must bite):** ablate scope-gating (wire the whole world) → every
  agent RUNS → per-tick cost GROWS ~linearly with the TOTAL world (ON ≪ OFF at
  large N_out — the cost we must not pay). PASS requires the OFF arm's cost to grow
  and strictly exceed the ON arm's at the largest N_out.

- **G-open-economy.** A passer-through's inn stay INJECTS external coin (inn coin
  up by `lodging_cost`, traveller coin down, `external_influx` logged) and an import
  moves coin ACROSS the boundary outward (`external_outflux` logged, resident owns a
  good it could not produce). **PASS ⟺** internal coin rises by exactly the logged
  influx on a stay; the resident acquires a non-locally-produced good and coin
  leaves via the logged outflux; Σcoin balances once the logged external points are
  counted.

- **G-travellers-are-full-agents.** A traveller is one PERSISTED node with held
  state (coin/story/goal) that REOCCURS remembered: across two visits the SAME node
  accrues `visits` and `familiarity`, and the innkeeper's `knows` edge is minted
  once and persists. **PASS ⟺** visit 2 uses the same node as visit 1,
  `familiarity` grows monotonically with visits, and `inn knows traveller` holds
  across both (no re-roll; relationship persists — via `graph_to_dict` round-trip).

- **G-news-from-the-frontier (Giantville).** A traveller's news yields a SECOND-HAND
  belief (lower confidence, `provenance_hearsay`); a resident who VISITED holds a
  GROUNDED belief (`confidence 1.0`, `provenance_grounded`); a less credible teller
  yields an even lower-confidence hearsay belief. **Control:** no traveller and no
  visit → the resident holds NO Giantville belief (frontier unknown = absence).
  **PASS ⟺** `hearsay.confidence < grounded.confidence`, `low_cred.confidence <
  credible.confidence`, provenance flags read cleanly, and the control resident has
  zero beliefs.

- **G-dream-of-moving → departure (R8 + R11).** An in-scope resident holding an R8
  Giantville Dream, met by a traveller RECRUITER who grounds a path, COLLAPSES the
  dream (R8 `gg_dream_collapse_path` → exactly one `ActionGoal{leave}`, `left=1`)
  and is then taken OUT OF SCOPE by `bw_dissolve_on_leave` (wiring dissolved,
  `in_scope=0`, `dormant=1`) — and may REOCCUR as a returning traveller now
  GROUNDING Giantville (grounded, not hearsay, belief). **Control:** no recruiter →
  no grounded_path → the dream does not collapse and the resident stays in scope.
  **PASS ⟺** recruiter path → collapse → one leave-goal → dissolved to dormant, the
  reoccurring traveller's Giantville belief is grounded, and the no-recruiter
  control neither collapses nor departs.

- **G-no-python-decision (source-audit).** The R11 decisions are exactly the nine
  rule names above (2+4+2+1); the four R11 seeds are all `self_load_only`; the
  adapter runs no Python rule engine (`graph_rewrite`/`gr._match`/`gr._apply`/
  `make_rule` absent) and never branches on a decision output
  (`in_scope`/`dormant`/`collapsed`/`left`/`familiarity`/`confidence` do not appear
  in an adapter `if`).

- **G-discipline.** Base/prereg on merge-base `6de883c92c`; own-engine
  `source_match ∈ {own, shared}` (provenance 7/7); `runners/dsl` diff EMPTY (no
  Rust, incl `term.rs`); canonical shared `.so` md5 UNCHANGED start==end
  (`fd82dc2978dbb055496dd82390ac2ebe`); `test_failure_baseline_migrated` green
  (11/11); `test_bigville_world_migrated` all green; all-new additive
  `bigville_world_*` files only (no tracked file edited). Per SUPERVISOR+USER
  directive (2026-07-29) a purely-additive, no-Rust, `self_load_only` rung cannot
  regress other suites, so the fast baseline gate + additive discipline is
  SUFFICIENT; the ~43-min oracles (`per_area_settlement_regression.sh`,
  `rung7_vision_bench.sh`) are NOT run.

## Honest residuals (pre-declared)

- **Synthetic, small N.** The scope-gating cost curve is a micro-benchmark on
  synthetic agents (a heartbeat as the per-tick "simulation"); the SHAPE (flat ON
  vs linear OFF) is the claim, not an absolute throughput number.
- **Comprehension is a minimal fold.** `bw_news_secondhand` is a graph-native
  stand-in for the full 244/246 comprehension pipeline (which is not a
  `self_load_only` R11 artifact) — it demonstrates the provenance/confidence
  boundary, not the parse.
- **Frontier arrival is adapter I/O.** Materializing a traveller from the frontier
  (adding its node + activity wiring) is an EXTERNAL boundary-crossing event the
  adapter ingests; the DISSOLVE half (departure → dormant) is a rule. This split is
  the honest boundary (you cannot run a rule on a node not yet in the active set).
