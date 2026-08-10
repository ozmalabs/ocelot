# GLASS-BOX SOCIETY R1 — "language is a coordination technology" — PRE-REGISTRATION (CLEAN-ENGINE RE-RUN)

**Written and committed BEFORE any number, before any runner is measured, and
before the gate test is executed.** Implements §6 "THE FIRST RUNG" of
`GLASS_BOX_SOCIETY_SCOPING.md`. Ledger block **234000**.

This is a **RE-RUN** of the same experiment first attempted on branch
`worktree-agent-a4f61a282e96d1b0a`. That attempt's DESIGN was correct but its
measurement rode a **provenance-RED** engine: a peer session had uncommitted
Rust in the shared checkout, so the symlinked `.so` diverged from committed
source and the two oracles had to be run with engine-build self-tests
DESELECTED. **The tree is CLEAN now.** This re-run therefore:

- builds its **OWN** engine from this worktree's committed Rust source
  (`cd runners/dsl && cargo build --release && cp target/release/libsubstrate_rs.so
  python/substrate_rs/_native.abi3.so`) → provenance verdict **`own`**, no
  symlink into the shared checkout, no deselection;
- records the **canonical shared** `.so` md5 at start and re-confirms it
  UNCHANGED at the end (that file is NEVER written through);
- runs both oracles WITHOUT any provenance deselection and reports the actual
  BEFORE pass-counts.

- **branch:** `worktree-agent-aa7a18cfd2c7a6f7f`
- **base SHA:** `3c4666ceba0b0ceef1db4030d941a5cd66b5f949` (current main,
  "add executable cognitive architecture core")
- **engine:** built in THIS worktree from committed source. **This rung adds
  ZERO Rust** — `runners/dsl/src/term.rs` and the whole `runners/dsl` diff MUST
  be EMPTY. This worktree's `runners/dsl/src` is byte-identical to the canonical
  tree's (verified `diff -rq`), so the source fingerprint agrees and provenance
  is CLEAN by construction.
- **canonical shared `.so` md5 (recorded at start, must stay UNCHANGED):**
  `55707cd76a6097c92127b3226109305c` (real file, not a symlink;
  `runners/dsl/python/substrate_rs/_native.abi3.so` in the shared checkout).

## §0 — `check_claim`, VERBATIM

```
SEED CLAIM 234000-234999: CLEAN -- no collision DETECTED.
  Scope: 953 files with seed sinks; 650 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

The 650 unresolved sinks are PRICED, not waved past: CLEAN means *no collision
detected*, never *no collision exists*. Every seed this rung draws is a DIRECT
ELEMENT of an explicit `range` inside the declared block (never `sd + K`).

---

## §1 — THE ARCHITECTURE (agents are graphs; Python is a mechanical adapter)

The whole social mechanism is the **existing** value economy from HARVEST /
core_emotions (204000), applied to a trade task, plus a small grounded speech-act
set. **No new agent decision logic anywhere.** The lineage is exact:

- **`total_value` = `happiness` + `fulfilment_value`** (core_emotions rules
  `em_happiness`, `em_fulfilment_value`, `em_total_value`, UNCHANGED and reused).
  `happiness = individual_benefit − individual_cost + mood_bias`;
  `fulfilment_value = (w_supergraph>0 ? supergraph_contribution : 0) + mood_bias`.
- **The trade decision is the graph's own `Argmax`** over two candidate
  `Appraisal` nodes (GIVE, KEEP) by `total_value` — rule `gb_choose_give`, an
  exact structural copy of HARVEST's `hv_choose_harvest`. Restraint/cooperation
  FALLS OUT of the value system; it is not scripted.
- **The world adapter (`worlds/glassbox_r1_world.py`) contains NO agent
  decision.** It moves agents (mechanical random walk), forms encounters
  (mechanical co-location), publishes the WORLD's payoff mechanics onto candidate
  Appraisals as full-information observations (exactly as HARVEST publishes
  `future_yield`/`sanction`), calls `run_rules()`, reads `chosen_give` /
  `stated_give` off each `TradeDecision`, and realises transfers. Every
  conditional in the adapter is over WORLD state (position, holding, whether a
  promise node exists), never over an agent's valuation.

## §2 — THE WORLD (mechanical adapter)

- **N = 8 agents** on a **ring of P = 5 positions**, one **random-walk** step per
  tick (mechanical, RNG-seeded). Small persistent spatial world.
- **Complementary resources:** 4 agents hold type X and need Y; 4 hold Y and need
  X. An **encounter** = two complementary agents sharing a cell (mutual need).
  Encounters vary run-to-run with the walk seed → real variance → real CIs.
- **Episode:** **T = 30 ticks.** Welfare is realised at encounters and accumulated.
- Each agent = one `EmotionHub` + `HeldEmotionParams{enabled=1, w_supergraph,
  comms_on, mood_bias=0}` + a `TradeDecision` + two candidate `Appraisal`s, all
  `member_of` one shared `Supergraph`. One substrate, one `run_rules()` fixpoint.

## §3 — THE GROUNDED SPEECH ACTS (readable graph nodes; rules, not Python)

Small, grounded speech-act set. Each is a RULE that fires only under
`comms_on==1`, mirroring HARVEST's `hv_state_intent`:

- **`promise`** — the commissive: agent professes it WILL reciprocate → a readable
  **`Promise` node** with `by`, `to`, `stated_give=1`. **Stating is cheap; only
  holding is decided by value** (the `gb_choose_give` Argmax). A deceptive
  (`w_supergraph==0`) agent MAKES the promise (cheap) but its Argmax HOLDS a KEEP:
  `Promise.stated_give=1` while `TradeDecision.chosen_give=0` — the readable
  stated≠held gap (HARVEST's deception instrument, at the language layer). `inform`
  / `request` are the grounded full-information publish the adapter performs onto
  each candidate (the world fact `promise_in`).

## §4 — THE VALUE ECONOMY (declared CONFIGURATION — bound once, never a verdict threshold)

World payoffs the adapter publishes onto each agent's GIVE/KEEP candidates,
conditioned on whether a `Promise`-to-this-agent exists. All integers; all fixed
config like HARVEST's `K/HMAX/PUNISH_PENALTY`:

| end-holding outcome | value | candidate it feeds |
|---|---|---|
| `V_both` = **7** | hold own + received partner's (defector's prize) | KEEP, when a promise-to-me exists |
| `V_need` = **6** | hold the needed resource (successful trade) | GIVE, when a promise-to-me exists |
| `V_own`  = **4** | hold own unneeded resource (autarky / no-trade) | KEEP, when NO promise-to-me |
| `V_alone`= **0** | gave own, got nothing (the sucker) | GIVE, when NO promise-to-me |
| `G` = **3** | `supergraph_contribution` when my give hands a partner its needed resource | GIVE (both cases) |

Outcome cells (verified by construction, then measured):

- honest (`w>0`), promise present: GIVE `= V_need+G = 9` > KEEP `= V_both = 7` → **gives** (keeps promise).
- psychopath (`w=0`), promise present: GIVE `= V_need = 6` < KEEP `= V_both = 7` → **keeps** (defects → exploits).
- honest, NO promise (comms OFF): GIVE `= V_alone+G = 3` < KEEP `= V_own = 4` → **keeps** (no unilateral give).
- psychopath, NO promise: GIVE `= 0` < KEEP `= 4` → **keeps**.

**Declared sensitivity (the gate is genuinely falsifiable):** the OFF null holds
because `G < V_own − V_alone` (3 < 4) — a pure altruist with large enough `G`
WOULD give unilaterally and cooperation would emerge WITHOUT language, failing the
headline. Declared, not hidden.

## §5 — THE GATES (pre-registered; each has a control that CAN fail)

- **G-language-coordinates (HEADLINE).** Metric = **mean welfare per agent-tick**
  = total realised welfare / (N·T). Compare **comms ON vs comms OFF**, same world,
  same seeds, PAIRED by run seed, on an **all-honest** population (language the
  only lever). Verdict: ON − OFF gap is **> 0 and its 95% bootstrap CI excludes 0**
  (CI-separated). *If cooperation emerges without language (OFF ≈ ON), language
  isn't the lever — reported straight.*
- **G-seed-determines.** Honest-population ON welfare **CI-separated ABOVE**
  psychopath-population ON welfare.
- **G-deception-is-real.** A deceptive agent's `Promise.stated_give=1` while its
  `TradeDecision.chosen_give=0`, readable in the graph. Measure **promise-keeping
  rate BY SEED** (honest vs psychopath). Verdict: honest = 1.0, psychopath = 0.0,
  CI-separated.
- **G-glass-box.** The episode reconstructs from graph data (Promise nodes,
  realised transfers, per-agent `w_supergraph` and `total_value`). Source-audit:
  no `graph_rewrite.run`/`gr.run`/`_match`/`_apply`/`make_rule`; no `if/else` over
  an agent's graph valuation that selects an agent action.
- **G-discipline.** Agents are graphs (core_emotions + glassbox_r1 seeds); world =
  mechanical adapter; canonical shared `.so` md5 UNCHANGED; `term.rs`/`runners/dsl`
  diff EMPTY; oracle before==after WITHOUT deselection; `source_match = own`.

## §6 — WIRING CONTROLS (run FIRST; abort on either)

- **POS:** with a `Promise`-to-agent present and `enabled=1`, an honest agent's
  `chosen_give` = 1 (the give rule CAN fire).
- **NEG:** with NO promise, `chosen_give` = 0.
These prove the machinery is live in both directions, so a null in OFF is
informative, not vacuous.

## §7 — SEEDS (direct elements of explicit ranges; base 234000)

| arm | seeds |
|---|---|
| G-language ON/OFF (all-honest, RUNS=60, PAIRED) | **234000–234099** (uses 234000+r) |
| G-seed-determines (honest vs psychopath population, RUNS=60 each) | **234100–234299** |
| G-deception (mixed, RUNS=60) | **234300–234399** |
| bootstrap-CI RNG | **234900** |

`N=8`, `P=5`, `T=30`, `RUNS=60` are AXES / configuration — iterated or bound once,
never compared against. Bootstrap: 2000 resamples, percentile 2.5/97.5.

## §8 — PREDICTIONS (stated in advance)

| | prediction | forced? |
|---|---|---|
| **P1 (HEADLINE)** | G-language: ON−OFF mean-welfare-per-agent-tick gap ∈ **[+0.5, +2.0]**, strictly > 0, 95% CI excludes 0. The prior (provenance-RED) attempt measured **0.94 [0.92, 0.97]**; a clean-engine result inside the interval and CI-separated reproduces it. A null (OFF ≈ ON) is the registered falsifier and would be the headline. | **no** |
| **P2** | G-seed: honest-population ON welfare CI-separated ABOVE psychopath-population ON welfare | no |
| **P3** | G-deception: honest promise-keeping rate = 1.0; psychopath = 0.0; CI-separated | largely **yes** (forced by the value economy; instrument + glass-box check) |
| **P4** | G-glass-box: source-audit clean (0 forbidden calls; every decision a named rule) | yes (declared) |
| **P5** | Wiring: POS `chosen_give=1`, NEG `chosen_give=0` | yes (declared) |

**Where the evidential weight sits:** **P1 and P2.** P3/P4/P5 are forced /
near-forced and reported as instrument + glass-box checks, not findings.

## §9 — DECISION RULE (including what a null means)

| observed | reading |
|---|---|
| P1 gap > 0, CI-separated | **LANGUAGE COORDINATES.** Grounded conversation enables a cooperative structure the language-OFF control cannot. |
| **P1 null (OFF ≈ ON)** | **LANGUAGE IS NOT THE LEVER** in this world. Report straight. |
| **P1 gap > 0 but P2 null** | Language helps but the seed mix does NOT determine the society. |
| P3 shows psychopath keeping-rate > 0 | Deception weaker than the value economy predicts; re-examine, new prereg. |
| clean-engine gap materially differs from 0.94 | Report the clean number straight; the prior was on a diverged engine. |

## §10 — DISCIPLINE COMPLIANCE (declared before the code)

- **No tolerance parameter, no magic threshold** in any verdict. Every gate verdict
  is an exact equality on a rate (`== 1.0` / `== 0.0`), a count, or a **CI
  comparison between two MEASURED quantities**. The §4 value constants are world
  MECHANICS, never compared against.
- `N`, `P`, `T`, `RUNS` are AXES/config — bound once, never a verdict.
- **ADDITIVE, default-OFF:** new files only —
  `worlds/glassbox_r1_world.py`, `seeds/glassbox_r1_social.json`,
  `scripts/jabberwock_glassbox_r1.py`, `tests/test_glassbox_r1_migrated.py`, this
  doc, `GLASS_BOX_R1_RESULTS.md`, and `results/glassbox_r1/`. The seed is
  `self_load_only`, nothing `depends_on` it, every rule guards on
  `HeldEmotionParams.enabled` — absent it, every existing path is byte-identical.
  **No edit to any existing tracked file** (the adapter loads the seed by
  `manifest_for("glassbox_r1_social")`, which reads `seeds/<id>.json` directly).
- **ZERO Rust.** `runners/dsl` diff empty; canonical shared `.so` md5 re-confirmed
  unchanged; this worktree builds its OWN engine (provenance `own`).
- Oracle (`rung7_vision_bench.sh`, `per_area_settlement_regression.sh`) BEFORE ==
  AFTER, **run WITHOUT any provenance deselection** (the tree is clean), fail-set
  compared as node-id SETS, never counts.
