# HARVEST — a commons social-dilemma over emotional seeds, with communication (RESULTS)

*Block 212000. Prereg `HARVEST_EMOTIONAL_SEEDS_PREREG.md` committed ALONE at
**`51ea2ce727`** before any number. Worktree off `main` HEAD `6952055056`. Engine
`source_match: "own"` (this tree's build, no stale Rust); canonical
`_native.abi3.so` md5 **`793ce09ed498a749abb79aeaea44b92e`** UNCHANGED; `term.rs`
and whole `runners/dsl` diff EMPTY (NO Rust). Numbers:
`results/harvest_commons/results.json`; gate `tests/test_harvest_commons_migrated.py`
7/7.*

## 0. What this is — a glass-box instantiation, not new social science

A synthetic MODEL that re-derives **Hardin** (the tragedy of the commons),
**Ostrom** (communication + monitoring + sanction averts it), and **Fehr-Gächter
/ Axelrod** (costly punishment and reciprocity sustain cooperation). The
contribution is the **glass-box, gated, shared-atom** instantiation: every agent
decision is a RULE over the substrate's OWN landed value economy (block 204000
`core_emotions`), so the collective outcome is **ATTRIBUTABLE to a named knob**
(`w_supergraph`). **Synthetic-proven ≠ real-behaviour** — no human data; no claim
about real populations.

## 1. The mechanism (where each decision lives — G-graph-native, CLEAN)

The world (`domains/harvest_world.py`) is a mechanical adapter: it publishes the
commons mechanics as full-information observations, calls `run_rules()`, reads
each agent's decision off the graph, and applies it to the shared pool. **Every
agent decision is a graph rule** in `seeds/harvest_commons.json` (loaded per-agent
over `core_emotions`):

| decision | rule | mechanism |
|---|---|---|
| how much to harvest | `hv_choose_harvest` | `chosen_harvest = harvest_level of Argmax_c total_value(c)` over candidate Appraisals — restraint FALLS OUT of maximising `benefit + [w>0]·collective_yield`; not hardcoded |
| who enforces the norm | `hv_mark_enforcer` | `enforces = (w_supergraph>0 AND comms_on)` — enforcement is itself pro-social |
| how many enforcers | `hv_count_enforcers` | `Count` of `enforces==1` over the shared Supergraph's members |
| whether to punish | `hv_punish` | a norm-valuing agent reproaches a monitored over-harvester |
| what to state | `hv_state_intent` | professes norm compliance (STATED intent) vs the HELD `chosen_harvest` |

Source audit (in `results.json.g_graph_native`): forbidden call-patterns
`graph_rewrite.run(` / `gr.run(` / `._match(` / `._apply(` / `make_rule(` all **0**;
the ONLY substrate calls are `add_node` / `add_edge_unchecked` (ingest), `set_attr`
(publish observations), `run_rules` (tick), `node()[...]` (emit). No conditional
over agent graph-state that selects an agent action.

Fixed world constants (pre-registered): N=6 agents, one integer pool, K=120,
R0=100, Hmax=20, T=40, logistic regrowth `regrow(R)=max((2·R·(K−R))//K, 0)` with
`regrow(0)=0` (permanent collapse). Full information: each candidate carries
`supergraph_contribution = future_yield(R,h,N)` (public commons response) — a
defector defects KNOWINGLY.

## 2. G-core (Phase 1) — the seed DISTRIBUTION predicts the collective outcome ✓

`p` = population probability an agent is prosocial (`w_supergraph>0`), drawn
Bernoulli per agent; 40 sampled populations per level, no communication. 95% CIs
bootstrap (2000 resamples).

| p_prosocial | final pool [95% CI] | total yield [95% CI] | sustained frac | equality |
|---|---|---|---|---|
| 0.00 | 14.0 [14.0, 14.0] | 330.0 [330, 330] | 0.00 | 1.00 |
| 0.17 | 14.0 [14.0, 14.0] | 357.5 [346, 369] | 0.00 | 0.89 |
| 0.33 | 10.5 [8.9, 12.0] | 355.0 [342, 367] | 0.00 | 0.74 |
| 0.50 | 23.1 [12.4, 34.0] | 618.5 [422, 821] | 0.15 | 0.67 |
| 0.67 | 44.9 [29.6, 60.6] | 1087.4 [794, 1388] | 0.40 | 0.68 |
| 0.83 | 73.5 [58.5, 88.0] | 1657.4 [1369, 1920] | 0.70 | 0.75 |
| 1.00 | 120.0 [120, 120] | 2376.0 [2376, 2376] | 1.00 | 1.00 |

**Primary control-separated contrast:** all-selfish (p=0) yield **330** vs
all-prosocial (p=1) yield **2376** — CI-separated; final pool **14 vs 120** —
CI-separated. A commons run by pure defectors collapses; one run by pro-social
agents sustains at carrying capacity with **~7.2× the yield**, attributable to the
single varied knob `w_supergraph`. The **sustained fraction is a clean sigmoid**
(0.00→0.15→0.40→0.70→1.00): there is a **critical mass** of pro-sociality for the
commons to hold — the honest structure the tragedy has in reality.

## 3. G-ostrom (Phase 2) — communication flips a collapsing population ✓ (with an honest null)

Same collapsing distributions, no-comms vs with-comms (norm + graph-decided
coordinated costly punishment), 40 paired seeds; paired delta + 95% CI.

| population | enforcers (graph) | no-comms yield | with-comms yield | Δ yield [95% CI] | Δ pool [95% CI] |
|---|---|---|---|---|---|
| mixed p=0.5 | 3 | 522.6 | 1717.8 | **+1195.1 [888, 1498]** | +69.2 [51.8, 86.2] |
| all-selfish p=0 | 0 | 330.0 | 330.0 | **+0.0 [0, 0]** | +0.0 |

**The Hardin→Ostrom flip is real:** a mixed population that COLLAPSES silently
SUSTAINS once it can agree a restraint norm and coordinate punishment — the
anticipated sanction enters the selfish agents' `individual_cost`, so their own
`Argmax` (unchanged rule) moves to the norm. CI-separated from zero.

**The honest null (and its mechanism):** communication CANNOT save the all-selfish
population — **zero enforcers**. Enforcement is itself a pro-social act
(`hv_mark_enforcer` gates on `w_supergraph>0`), so a pure-defector population has
no one willing to bear the cost of punishing: the **second-order free-rider
problem** (Fehr-Gächter). Talk is cheap without someone who values the collective
enough to enforce. This is a richer, more faithful result than "communication
always saves."

## 4. G-deception (Phase 3, reached) — stated vs held intent tracks the knob ✓

Glass-box read: STATED intent (`hv_state_intent` professes the norm) vs HELD
intent (the graph's `chosen_harvest`), 40 mixed populations, gap = held − stated.

| condition | selfish (w=0) gap [CI] | prosocial (w=1) gap [CI] |
|---|---|---|
| cheap talk (professed, UNenforced) | **+13.0 [13, 13]** | 0.0 [0, 0] |
| enforced (professed AND sanctioned) | 0.0 [0, 0] | 0.0 [0, 0] |

Under **cheap talk**, a selfish agent STATES compliance with the norm while its
graph HOLDS a grab — a **+13 stated-vs-held divergence**, entirely on the low-`w`
agents; prosocial agents are honest (gap 0). **Enforcement closes the gap to 0**
for all — deception exists precisely where statements are unbacked and the speaker
does not value the collective (re-derives cheap-talk theory, Farrell-Rabin). The
gap is deterministic in `w` (CI degenerate) — the determinism IS the finding: the
knob perfectly predicts who lies.

## 5. G-discipline — all gates green

- Canonical `.so` md5 **`793ce09ed498a749abb79aeaea44b92e` UNCHANGED**;
  `source_match: "own"`, no stale Rust.
- `term.rs` diff EMPTY; whole `runners/dsl` diff EMPTY (**NO Rust, no new Term**).
- Integer-native: every `Lit` in the seed a whole number (checked).
- **New-world isolation / byte-identity:** `harvest_commons.json` is
  `self_load_only:true`, `depends_on:[]` — `load_all_seeds` does NOT load it
  (gated). **Oracle** `rung7_vision_bench.sh`: 214 passed / 10 skipped
  BEFORE == AFTER. **Regression** `per_area_settlement_regression.sh` (34-file):
  23 failed / 277 passed / 5 skipped, and the FAILING NODE-ID SET is **identical**
  BEFORE vs AFTER (`diff` empty — the 23 are the pre-existing baseline, untouched).
- Seed-claim `212000–212999`: CLEAN (no collision detected).

## 6. Honest residuals

- **`w_supergraph` is SIGN-only** (the landed 204000 identifiability finding): the
  per-agent knob is binary (cares / doesn't). Gradation is at the POPULATION level
  (the Bernoulli-`p` sweep), which is exactly what G-core measures. `mood_bias` is
  a uniform value offset that does NOT move the harvest argmax (null by
  construction) — reported, not hidden.
- The commons is **well-mixed** (a single shared pool), not the spatial Harvest
  grid; the mean-field `future_yield` is the public mechanics. A spatial grid is a
  named follow-on.
- Communication is wired as a **norm + coordinated sanction** over the affiliation/
  cost channel; it does not yet use the full free-form speech-act/comprehension
  faculty (the messages are structured norm professions + reproaches). Free-form
  NL negotiation of the norm is a named follow-on.
- The **deception gap is deterministic** in `w` (no behavioural noise), so its CI
  is a point — honest, but it means the model shows the CLEANEST possible version
  of the effect, not a noisy real one.

## 7. Named follow-ons (NOT built)

- the **skill / order-N** second axis (competence to restrain, not just the will);
- the **negative social-value** region — malice / spite / dominance, the mirror of
  the `w_supergraph` term (not in the landed set);
- **deferred spite / stockpile-then-destroy** (a held non-decaying grudge term +
  instrumental sub-goal);
- **recovering the emotional seeds from behaviour** in the social setting
  (block 206000 inverse inference on the commons transcript);
- the **spatial** Harvest grid; **free-form NL** norm negotiation via the full
  conversation faculty.
