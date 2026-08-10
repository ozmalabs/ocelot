# SPITE + SKILL — the negative-social region and the order-N axis (RESULTS)

*Block **213000**. Prereg `SPITE_SKILL_PREREG.md` committed ALONE at
**`3804ac7786`** before any number. Worktree off `main` HEAD `e4cf1dc239` (carries
the 212000 HARVEST). Engine `source_match: **shared**` (canonical build, Rust
source identical — NO local Rust); canonical `_native.abi3.so` md5
**`793ce09ed498a749abb79aeaea44b92e`** UNCHANGED; `term.rs` and whole
`runners/dsl` diff EMPTY (NO Rust). Numbers: `results/spite_skill/results.json`;
gate `tests/test_spite_skill_migrated.py` **7/7**. Seed range `213000-213999`
checked free at prereg time (`scripts/seed_claim.py` → CLEAN; the sole later
occupant is this block's own `spite_skill_measure.py`).*

## 0. What this is — a glass-box extension, not new social science

Two NEW knobs on the 204000 `core_emotions` value economy (as wired into the
212000 HARVEST commons), **both graph DATA**, re-deriving two known results behind
a protected control each:

- **SPITE** — the hot/cold (reactive/instrumental) aggression split: costly
  harm-seeking (money-burning — Zizzo-Oswald 2001; Abbink-Sadrieh "joy of
  destruction" 2009) is DISTINCT from indifferent payoff-maximization.
- **SKILL (order-N)** — folk-theorem cooperation-from-self-interest: strategic
  agents restrain under enforcement by CALCULATION, distinct from
  cooperation-from-CARE.

**Synthetic-proven ≠ real-behaviour** — no human data, no claim about real
populations. The contribution is the **gated, named-knob, glass-box attribution**.

## 1. Where each knob lives (G-graph-native — CLEAN)

Both knobs are attributes on `HeldEmotionParams`, read by ONE seed rule
`ss_decision_value` (`seeds/spite_skill.json`, `self_load_only`, empty
`depends_on`), which writes a **fresh** key `decision_value` on each candidate
Appraisal — NEVER `total_value`, so there is **no `run_rules` fixpoint
write-conflict** with core `em_total_value`:

```
decision_value = individual_benefit
               − IfThenElse(order_n>0, individual_cost, 0)   # SKILL gates the anticipated sanction
               + mood_bias
               + fulfilment_value                            # CARE term (core; gated on w_supergraph>0)
               + IfThenElse(w_spite>0, burn_harm, 0)         # SPITE (mirror of the care gate)
```

| decision | rule | mechanism |
|---|---|---|
| how much to harvest | `ss_choose_harvest` | `chosen_harvest2 = harvest_level of Argmax_c decision_value(c)` |
| whether/how much to BURN | `ss_choose_burn` | `burn_level` of the SAME Argmax winner |
| the two knobs | `ss_decision_value` | `w_spite` gates `burn_harm`; `order_n` gates `individual_cost` |

Source audit (`results.json.g_graph_native`): forbidden call-patterns
`graph_rewrite.run(` / `gr.run(` / `._match(` / `._apply(` / `make_rule(` all
**0**; the only substrate calls in `domains/harvest_spite_world.py` are `add_node`
/ `add_edge_unchecked` (ingest), `set_attr` (publish `future_yield`, the sanction,
`burn_harm`), `run_rules` (tick), `node()` read (emit). **No agent decision in
Python.** Both `w_spite` and `order_n` are used as GATES (sign/threshold) exactly
like `w_supergraph` — **sign-only** (see §5).

Fixed world (mirror 212000): N=6, K=120, R0=100, Hmax=20, T=40, logistic
`regrow(R)=max((2·R·(K−R))//K,0)`. NEW: a burn wastes `BURN_D=30` pool at self-cost
`BURN_COST=2` (negative `individual_benefit`); institutional enforcement sanction
`ENF=25` on over-norm harvest (a public world quantity — cleanly isolates the
`order_n` response from population composition; 212000's sanction was endogenous to
the enforcer count, same value economy, different SOURCE).

## 2. G-spite — malice is not indifference ✓

**Deterministic triple, ONE bare commons, first-tick decision:**

| agent | w_supergraph | w_spite | chosen_harvest | chosen_burn | own yield (T=40) |
|---|---|---|---|---|---|
| payoff-maximizer | 0 | 0 | **20** | 0 | 44 |
| psychopath (indifferent) | 0 | 0 | **20** | 0 | 44 |
| spiteful | 0 | **1** | **0** | **30** | **0** |

Only the spiteful agent takes the self-costly burn; payoff-max and the indifferent
psychopath are **behaviourally identical** (both grab benefit-max, neither harms) —
**malice ≠ indifference**. The spiteful agent forgoes its entire own take (yield
0 vs the psychopath's 44) to burn the commons: **self-costly harm**, the textbook
operationalization of spite (willingness to pay to reduce others' payoff).

**Powered population sweep** (p = P(agent spiteful), N=6, 40 sampled populations
per level, all selfish on the care axis, bare commons; 95% bootstrap CIs):

| p_spiteful | total burned [95% CI] | total yield [95% CI] |
|---|---|---|
| 0.00 | 0.0 [0.0, 0.0] | 330.0 [330.0, 330.0] |
| 0.33 | 126.6 [108.4, 146.8] | 172.6 [142.1, 202.2] |
| 0.50 | 183.6 [164.6, 203.4] | 81.0 [61.4, 103.7] |
| 0.67 | 234.3 [214.7, 252.5] | 46.9 [33.4, 62.4] |
| 1.00 | 330.0 [330.0, 330.0] | 0.0 [0.0, 0.0] |

Collective harm rises monotonically with the spiteful fraction, **CI-separated**
`p=0` vs `p=1`. **Knob attribution:** the `w_spite=0` control (identical
compositions, spite gate off) burns **0 at every p** — the burning is attributable
to `w_spite`, nothing else. **G-spite PASSES.**

## 3. G-skill — cooperation from calculation ✓

**Deterministic 2×2, SELFISH agent (w_sg=0), norm=7, ENF=25:**

| | bare (no sanction) | enforced (ENF=25) |
|---|---|---|
| **myopic** (order_n=0) | grab **20** | grab **20** (ignores sanction) |
| **strategic** (order_n=1) | grab **20** | **restrain 7** |

Only strategic × enforced restrains — an `order_n × environment` **interaction**.
A myopic agent ignores the anticipated sanction and grabs even under enforcement;
in the bare commons (no sanction) BOTH skill levels grab. This is
**cooperation-from-CALCULATION**. For contrast, a **prosocial** agent (w_sg=1)
restrains to 7 at order_n=0 AND order_n=1, enforced or bare — **cooperation from
CARE, ungated by skill**.

**Powered sweep** (p = fraction high-skill among selfish agents, under
enforcement; restraint = harvest ≤ norm; 40 sampled populations/level):

| p_highskill | restraint fraction [95% CI] |
|---|---|
| 0.00 | 0.000 [0.000, 0.000] |
| 0.33 | 0.317 [0.258, 0.375] |
| 0.50 | 0.533 [0.467, 0.596] |
| 0.67 | 0.692 [0.637, 0.750] |
| 1.00 | 1.000 [1.000, 1.000] |

Restraint rises monotonically with the high-skill fraction, **CI-separated** `p=0`
vs `p=1`. **Control:** the bare-commons run (same compositions, no sanction)
restrains **0 at every p** — restraint is attributable to `order_n × enforcement`,
not skill alone. **G-skill PASSES.**

## 4. G-2d (headline) — the glass box attributes each cooperation to the right knob ✓

Under enforcement (comms, ENF=25), harvest of a single agent as knobs vary:

| cell | order_n=1 | order_n=0 | flips on zeroing skill? |
|---|---|---|---|
| psychopath (w_sg=0) | restrain **7** | grab **20** | **YES — it was calculation** |
| prosocial (w_sg=1) | restrain **7** | restrain **7** | **NO — it was care** |

Same cooperative behaviour at high skill (both restrain to 7), but **zeroing
`order_n` flips the psychopath to defection and leaves the prosocial agent
cooperating**. The glass box attributes each identical-looking cooperation to the
distinct knob that produced it — calculation vs care. **G-2d PASSES.** (The
`spiteful_highskill` grid cell burns — harvest 0 — completing the emotion×skill
grid.)

## 5. Honest bounds

- **Both knobs are SIGN-ONLY**, exactly like `w_supergraph`. `w_spite` enters as
  a gate `IfThenElse(w_spite>0, burn_harm, 0)` and `order_n` as
  `IfThenElse(order_n>0, individual_cost, 0)` — the magnitudes never multiply, so
  any positive value behaves identically. This is the faithful MIRROR of the built
  positive region (`w_supergraph` is likewise a `>0` gate in `em_fulfilment_value`).
  A magnitude-weighted `w_spite·harm` / `order_n`-depth would need a `Times`
  composition and is a named follow-on.
- **The burn is an added mechanic**, named not hidden: a money-burning candidate
  (self takes 0, pays BURN_COST=2, wastes BURN_D=30) — the standard costly-harm
  operationalization. Confounding with benefit-grabbing is avoided by making
  `burn_harm` nonzero ONLY on the burn candidate (harvesting is self-provision, not
  sabotage), so spite lands on the burn while payoff-max/psychopath refuse it.
- **In this single-tick economy the only anticipated self-consequence is the
  SANCTION** — there is no direct future-self-payoff term (that needs a multi-tick
  planner). So `order_n` gates the sanction; this keeps "bare commons: both skill
  levels grab" exactly true. A full-planner future-yield-to-self term is a named
  follow-on.
- **Enforcement is institutional here** (a fixed public sanction) to isolate the
  skill response; 212000's endogenous-enforcer sanction is the same value economy.
- **Named further follow-ons:** DEFERRED spite (held grudge = a non-decaying spite
  term + a stockpile-then-destroy instrumental sub-goal — the premeditated
  saboteur); relational / per-other spite (harm targeted at a specific other, not
  the collective); seed-recovery of the two new knobs (206000 applied).

## 6. G-discipline ✓

- Canonical `.so` md5 **`793ce09ed498a749abb79aeaea44b92e`** UNCHANGED; `source_match: shared`.
- `term.rs` and whole `runners/dsl` diff **EMPTY** (no Rust; all terms —
  `Argmax`/`Attr`/`Neighbours`/`IfThenElse`/`Gt`/`Plus`/`Minus` — pre-existing).
- Integer-native: every seed `Lit` a whole number.
- `self_load_only: true`, `depends_on: []` — nothing loads it unless a world asks.
- **Default-OFF byte-identity:** a neutral spite-world agent (`w_spite=0,
  order_n=1`) reproduces the 212000 `HarvestWorld` harvest decision in the bare
  commons byte-for-byte (`decision_value == total_value` at neutral knobs;
  `[7,20,7,20,7,20]` both).
- **Oracle** `bash scripts/rung7_vision_bench.sh`: 214 passed / 10 skipped
  BEFORE == AFTER.
- **Regression** `bash scripts/per_area_settlement_regression.sh`: the failing
  node-id SET is IDENTICAL BEFORE and AFTER (23 pre-existing conversation /
  topic-route / gap / elaboration failures, unrelated to this additive block).

## 7. Files

- `seeds/spite_skill.json` — the two knobs + `ss_decision_value` / `ss_choose_harvest` / `ss_choose_burn`.
- `domains/harvest_spite_world.py` — mechanical adapter (ingest / tick / emit).
- `scripts/spite_skill_measure.py` — confirmatory measure (all Gs, powered).
- `tests/test_spite_skill_migrated.py` — 7/7 gate.
- `results/spite_skill/results.json` — numbers.
