# HARVEST — a commons social-dilemma over emotional seeds, with communication (PRE-REGISTRATION)

*Committed ALONE, BEFORE any implementation and BEFORE any measurement.
Isolated worktree off `main` HEAD **`6952055056`** (LEDGER 209000). Engine
canonical **`793ce09ed498a749abb79aeaea44b92e`** (`_native.abi3.so`, shared
build; Rust source identical to this worktree — `source_match` to be reported).
This rung adds **NO Rust** (`term.rs` diff EMPTY, whole `runners/dsl` diff EMPTY)
and **ONE new `self_load_only` seed** (`seeds/harvest_commons.json`) plus a
mechanical multi-agent world adapter + measure. Seed block **212000–212999**
(`default_rng`/derived seeds at the block base).*

Seed-claim check (verbatim, run before any number):

```
$ python3 scripts/seed_claim.py 212000 212999
SEED CLAIM 212000-212999: CLEAN -- no collision DETECTED.
  Scope: 911 files with seed sinks; 615 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

---

## 0. FRAMING — a glass-box, gated instantiation of commons dynamics; NOT new social science

This is a **synthetic MODEL of social dynamics**. It re-derives — it does not
discover — three established bodies of work:

- **Hardin (1968), *The Tragedy of the Commons*** — a shared resource harvested
  by self-interested actors collapses. This is the NO-COMMUNICATION theorem.
- **Ostrom (1990), *Governing the Commons*** — real communities routinely AVOID
  the tragedy when they can **communicate, monitor, and sanction**. Communication
  is the Hardin→Ostrom pivot.
- **Fehr & Gächter (2002), Axelrod (1984)** — costly peer punishment and
  reciprocity sustain cooperation that would otherwise unravel.

**The contribution is NOT the result** (the result is known). It is the
**glass-box, gated, shared-atom instantiation**: every agent's decision — how
much to harvest, whether to punish, what to say — is a **RULE over the agent's
OWN landed value machinery** (block 204000 `core_emotions`: `total_value =
happiness + fulfilment`, with `w_supergraph` gating the collective term), fired
by `run_rules()`. Because the knobs are named and mechanistic, we can **ATTRIBUTE
the collective outcome to a named individual parameter** — a black box can predict
collapse but cannot say *which knob, at what value, in whom* caused it. That
attribution, on the substrate's own emotion economy, wired (not rebuilt) into a
multi-agent commons with real inter-agent communication, is the point.

**Synthetic-proven ≠ real-behaviour.** No human data. We emulate the FUNCTIONAL
dynamics (seed distribution → decisions → collective outcome); we make NO claim
about real populations. Every phase reports the straight null if it fails.

---

## 1. THE ARCHITECTURE INVARIANT — every agent decision is a RULE (load-bearing)

`CLAUDE.md` is the hard constraint. The Harvest WORLD is a mechanical Python
adapter (I/O only). **Every agent decision is graph-native:**

| decision | WHERE it lives | mechanism |
|---|---|---|
| how much to harvest | rule `hv_choose_harvest` (seed `harvest_commons.json`) | `chosen_harvest = harvest_level of Argmax_c total_value(c)` over the agent's candidate Appraisals — restraint FALLS OUT of maximising `benefit + [w>0]·collective_yield`, never hardcoded |
| whether to punish | rule `hv_punish` (seed) | a norm-valuing agent reproaches a violator whose last harvest exceeded the agreed norm; costly to the punisher |
| what to state / agree | rule(s) over Message/Intent (seed + conversation faculty) | proposal → shared norm; stated-intent Message minted from the agent's own target |

The adapter does EXACTLY: publish the commons mechanics as observations (full
information), `run_rules()`, read each agent's `chosen_harvest`/punish/message
off the graph, apply them mechanically to the shared pool, regrow, score, pass
messages. **Source-audit to be reported** (G-graph-native): no `graph_rewrite.run`
/ `_match` / `_apply` / `make_rule`; no Python conditional over agent state that
decides an agent action. The de-risk prototype already confirms the harvest
decision is taken by the `Argmax` RULE, not Python (prosocial→restrain,
selfish→grab, both selected in-graph).

---

## 2. THE WORLD (mechanical adapter, integer-native)

Classic Harvest SSD reduced to a well-mixed shared pool (density-dependent
regrowth is the tragedy's core; the spatial grid is a named follow-on):

- **N = 6** agents share one integer pool `R`; capacity **K = 120**; start
  **R0 = 100**.
- **Regrowth (density-dependent logistic, integer):**
  `regrow(R) = max( (2·R·(K−R)) // K , 0 )`, and `regrow(0) = 0` — an emptied
  commons never recovers (the permanent-collapse absorbing state).
- **Per tick** (T = **40** ticks): each agent chooses `h ∈ {0…Hmax=20}` by rule.
  Total demand `D = Σ h_i`. If `D ≤ R`, each gets `h_i`; else proportional
  rationing `got_i = (h_i·R) // D` (mechanical fair split). `R ← R − Σ got`, then
  `R ← min(K, R + regrow(R))`.
- **Full information (owner requirement):** every agent's candidate Appraisal for
  level `h` carries `supergraph_contribution = future_yield(R, h) =
  regrow(R − N·h)` (clamped ≥ 0) — the PUBLIC commons-response function
  (mean-field: the collective regrowth if all N harvested at rate `h`),
  identical for every agent. The mechanics are KNOWN, like a door is known: a
  defector defects KNOWINGLY. `collective_success`/`_prev` carry the pool
  trajectory (drives the `hit_fulfilment` read-off).

All world constants above are FIXED by this prereg (piloted, then frozen).

---

## 3. THE AGENTS (wired from the LANDED emotion economy — not rebuilt)

Each agent (block 206000 construction pattern, verified):
`EmotionHub -has_emotion_params-> HeldEmotionParams{enabled:1, w_supergraph, mood_bias}`,
`EmotionHub -member_of-> Supergraph` (ONE shared collective node),
`EmotionHub -has_decision-> HarvestDecision`, and `Hmax+1` reused candidate
Appraisals via `has_appraisal` (so `core_emotions` fires) **and** `has_candidate`
(so `hv_choose_harvest`'s `Argmax` ranges over them).

`core_emotions.json` (loaded per-agent, unchanged) computes each tick:
`happiness = (individual_benefit − individual_cost) + mood_bias`;
`fulfilment_value = IfThenElse(w_supergraph>0, supergraph_contribution, 0) + mood_bias`;
`total_value = happiness + fulfilment_value`. **`w_supergraph` is SIGN-identifiable
only** (the 204000 finding: all positive magnitudes give identical decisions), so
it is treated as a **binary cares/doesn't-care knob** (0 = selfish, 1 = prosocial);
per-agent gradation via magnitude is NOT claimed. **mood_bias** is a uniform
value offset that does NOT move the harvest argmax (a constant across candidates);
it is included honestly as a null-by-construction secondary knob and reported as
such. **Population-level gradation comes from the seed DISTRIBUTION**, not from a
per-agent dial.

---

## 4. G-core (Phase 1) — the seed DISTRIBUTION predicts the collective OUTCOME

**Design.** Sweep composition `p = k/6`, `k = 0…6` (fraction of prosocial `w=1`
agents; the rest `w=0`). **40 runs** per level (280 runs), each run randomising
WHICH agents are prosocial and the agent order, run `r` at level `k` seeded
`212000 + 100·k + r` (max 212639, in-block). Metrics per run:

- **final pool** `R_T` (sustainability);
- **total yield** `Σ_i Σ_t got` (collective productivity);
- **sustained** (binary, `R_T ≥ 60` = half capacity);
- **equality** = `1 − Gini` of per-agent cumulative yield.

Report mean + **95% CI** (bootstrap, 2000 resamples) at every level.

**Primary contrast (control-separated):** `p=0` (all selfish) vs `p=1` (all
prosocial) on final pool AND total yield — CIs must be separated.

**Registered predictions.** (i) `p=1`: final pool ≈ K (sustained), total yield
HIGH; `p=0`: final pool LOW (collapsed), total yield LOW; the two CIs are
separated on both metrics. (ii) The relationship is attributable to `w_supergraph`
(the only varied knob). (iii) **Honest, pre-registered:** the middle of the curve
may be NON-MONOTONIC — partial cooperation without coordination can underperform
even all-defection (cooperators subsidise free-riders). We report the full curve
and headline the separated `p=0` vs `p=1` contrast; a non-monotonic middle is a
POSITIVE finding that motivates Phase 2, not a failure of G-core.

**G-core is REFUTED if** `p=0` and `p=1` are not CI-separated on total yield, OR
the all-prosocial population fails to sustain.

---

## 5. G-ostrom (Phase 2) — communication flips a collapsing population to sustaining

**Design.** Add a graph-native communication layer to a population that COLLAPSES
when silent:

1. **Talk → norm.** Agents exchange proposals (Message/Intent faculty); a rule
   establishes a shared restraint **norm `s`** (the socially-optimal per-capita
   harvest) as graph data every agent reads.
2. **Monitor + sanction.** Rule `hv_punish`: an agent that values the norm
   reproaches each violator whose actual harvest exceeded `s` last tick
   (costly to the punisher — Fehr-Gächter). Reproach effect rides the LANDED
   `drives.json` `drive_affiliation_legitimacy` channel where available, else a
   direct `individual_cost` term.
3. **Anticipation shifts the choice.** Full-information sanction cost enters the
   `individual_cost` of over-norm candidate Appraisals, so `hv_choose_harvest`'s
   `Argmax` moves toward `s` — for SELFISH agents too, once over-harvest is
   individually costly. The decision rule is UNCHANGED; communication changes the
   PAYOFF the agent faces, exactly as Ostrom predicts.

**Contrast (paired on seeds).** Same collapsing distributions — `p=0` (all
selfish) and `p=0.5` (mixed) — run **no-comms** vs **with-comms**, 40 paired
seeds each. Metric: final pool + total yield, paired delta + 95% CI.

**Registered prediction.** With-comms raises final pool AND total yield above
no-comms, CI-separated (a silent-collapse population sustains once it can
agree + sanction). **G-ostrom is REFUTED if** with-comms does not improve the
collapsing population's outcome (CI includes 0). We report the straight delta
either way.

---

## 6. G-deception (Phase 3, REACH — only if Phase 2 lands clean)

**The glass-box instrument.** Under a norm, an agent emits a **STATED** intent
(a Message: "I will harvest ≤ s") while its **HELD** intent is the graph
`HarvestDecision.chosen_harvest`. Measure the per-agent gap
`stated_restraint − held_harvest`. **Registered prediction:** low-`w_supergraph`
agents, when a norm makes stated compliance reputationally cheap but a grab still
wins their private `Argmax`, show a LARGER stated-vs-held divergence than
high-`w` agents. Measure the gap distribution by `w`. **If no incentive to
misstate emerges cleanly** (e.g. sanction anticipation already collapses the gap),
we report the NULL and NAME deception-under-reputation as the follow-on — a
solid Phase 1 + honest Phase 2 is the target; Phase 3 is a reach.

---

## 7. G-graph-native + G-discipline (gates, load-bearing)

- **G-graph-native:** a source audit of the world adapter proving every agent
  decision is a rule and the adapter is mechanical I/O only (no rule-engine
  calls; no conditional-over-agent-state that picks an action). Reported with the
  exact location of each decision (table §1).
- **Integer-native:** all agent-decision math uses the integer subset
  (`Plus/Minus/Times/IDiv/Ashr/Max/Min/IfThenElse/Eq/Gt/Lt/And/Or/Not`); every
  literal a whole number.
- **Default-OFF / new-world-isolated byte-identity:** `harvest_commons.json` is
  `self_load_only:true` (skipped by `load_all_seeds`; nothing `depends_on` it),
  so the existing tree is **byte-identical with it absent**. To be demonstrated
  by the unchanged oracle + regression node-id sets.
- **Canonical `.so` md5 stays `793ce09ed498a749abb79aeaea44b92e`**; **`term.rs`
  diff EMPTY**, **whole `runners/dsl` diff EMPTY** (NO Rust; if a primitive
  seemed needed I would STOP and report — it is not).
- **Oracle** `bash scripts/rung7_vision_bench.sh` BEFORE == AFTER.
- **Regression** `bash scripts/per_area_settlement_regression.sh` (34-file)
  BEFORE == AFTER (compared as the SET of failing node ids, never a count).
- **`source_match`** (Rust source vs the canonical build) reported.

---

## 8. NAMED FOLLOW-ONS (explicitly NOT built here)

- the **skill / order-N** second axis (competence to restrain, not just the will);
- the **negative social-value** region — malice / spite / dominance, the mirror
  of the `w_supergraph` term (NOT in the landed set);
- **deferred spite / stockpile-then-destroy** (a held, non-decaying grudge term +
  instrumental sub-goal);
- **recovering seeds from behaviour in the social setting** (block 206000 inverse
  inference applied to the commons transcript);
- the **spatial** Harvest grid (per-cell density regrowth) vs this well-mixed pool.

A solid Phase-1 landing + an honest Phase-2 result + these named is the target —
better than a sprawling half-verified everything.
