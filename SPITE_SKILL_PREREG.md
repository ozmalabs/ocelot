# SPITE + SKILL — extending the emotion economy with the negative-social region and the order-N axis (PRE-REGISTRATION)

*Block **213000**. Committed ALONE before any number. Worktree off `main` HEAD
`e4cf1dc239` (carries the 212000 HARVEST harvest). Seed range checked free:
`python scripts/seed_claim.py 213000 213999` → CLEAN (no collision detected;
617 unresolved sink sites counted tree-wide — a clean result means "no collision
DETECTED", never "none exists"). Canonical `_native.abi3.so` md5
**`793ce09ed498a749abb79aeaea44b92e`** — NO Rust, `term.rs` and whole
`runners/dsl` diff MUST stay EMPTY.*

## 0. What this is

A glass-box extension of the 204000 `core_emotions` value economy (as wired into
the 212000 HARVEST commons) with **two new knobs, both graph DATA**, not Python:

1. **The SPITE region (`w_spite`)** — the negative-social MIRROR of `w_supergraph`.
   The built social axis runs `[0 → positive]`: indifference (`w_supergraph≈0`,
   psychopathy) → care (`>0`). This adds the negative region: a term that actively
   VALUES reducing others'/the collective's yield. A spiteful agent picks a
   self-costly **burn** (destroy) action that harms others.

2. **The SKILL / order-N axis (`order_n`)** — planning depth. Gates WHICH
   anticipated term enters the agent's decision value: LOW order-N = myopic
   (immediate benefit only, ignores the anticipated sanction); HIGH order-N =
   strategic (includes the anticipated N-step sanction).

This re-derives the reactive-vs-instrumental (hot/cold) aggression split (spite as
costly money-burning — Zizzo-Oswald, Abbink-Sadrieh "joy of destruction") and the
folk-theorem cooperation-from-self-interest (skill). **Synthetic-proven ≠
real-behaviour** — no human data. The contribution is the **gated, named-knob,
glass-box attribution**, not new social science.

## 1. Where each knob lives (graph-native — the load-bearing constraint)

Both knobs are attributes on `HeldEmotionParams`, read by ONE seed rule
`ss_decision_value` (`seeds/spite_skill.json`, `self_load_only`, nothing
`depends_on` it), which writes a **fresh** attribute `decision_value` on each
candidate Appraisal (NEVER `total_value` — so there is no `run_rules` fixpoint
write-conflict with core `em_total_value`):

```
decision_value = individual_benefit
               − IfThenElse(order_n>0, individual_cost, 0)     # SKILL gates the sanction
               + mood_bias
               + fulfilment_value                              # CARE term (core, gated on w_supergraph)
               + IfThenElse(w_spite>0, burn_harm, 0)           # SPITE term (mirror of the care gate)
```

`ss_choose_harvest` = `Argmax` over candidate `decision_value` (the 212000
`hv_choose_harvest` pattern on the fresh key); `ss_choose_burn` reads `burn_level`
off the SAME Argmax winner. The world adapter (`domains/harvest_spite_world.py`)
only publishes observations (`future_yield`, the institutional sanction as
`individual_cost`, `burn_harm`), calls `run_rules()`, reads `chosen_harvest2` /
`chosen_burn`, and applies them to the shared pool — **no agent decision in
Python**. Both `w_spite` and `order_n` are used as GATES (sign/threshold), exactly
like `w_supergraph`; if magnitude never matters they are honestly "sign-only" and
reported as such.

Fixed world constants (mirror 212000): N=6 agents, one integer pool, K=120,
R0=100, Hmax=20, T=40, logistic `regrow(R)=max((2·R·(K−R))//K,0)`, `regrow(0)=0`.
NEW: burn wastes `BURN_D=30` pool at self-cost `BURN_COST=2` (encoded as negative
`individual_benefit`); institutional enforcement sanction `ENF=25` on over-norm
harvest (a world/observation quantity — cleanly isolates the `order_n` response
from population composition; in 212000 the sanction was endogenous to the enforcer
count, same value economy, different SOURCE).

## 2. Powered design

N=6 agents, RUNS=40 sampled populations per level, T=40 ticks, `np.random`
seeds around 213000; 95% bootstrap CIs (2000 resamples). Population sweeps draw
each agent's knob Bernoulli(p) so sampled populations genuinely vary (real CIs).
Per-agent Argmax decisions are deterministic → reported as deterministic facts
(the mechanism) alongside the powered population sweeps (the aggregate).

## 3. Gates (pre-registered predictions + thresholds)

- **G-spite.** Three agents side by side in ONE bare commons: payoff-maximizer
  (`w_sg=0,w_spite=0`), psychopath (`w_sg=0,w_spite=0`), spiteful (`w_sg=0,
  w_spite=1`). PREDICT: only the spiteful agent takes the self-costly burn
  (`chosen_burn>0`); payoff-max and psychopath grab benefit-max and never burn
  (behaviourally identical — **malice ≠ indifference**); the spiteful agent's own
  yield is LOWER (self-costly). Powered: fraction spiteful `p` → collective harm
  (total burned) rises, CI-separated `p=0` vs `p=1`; the `w_spite=0` control burns
  ZERO at every `p` (knob attribution). PASS iff all hold.

- **G-skill.** Selfish agent (`w_sg=0`), 2×2 skill × environment. PREDICT: only
  strategic × enforced restrains (harvest ≤ norm); myopic×bare, myopic×enforced,
  strategic×bare all grab (=20) — an `order_n × environment` INTERACTION.
  Cooperation-from-CALCULATION. Powered: fraction high-skill among selfish under
  enforcement → restraint fraction rises, CI-separated `p=0` vs `p=1`; bare-commons
  control → zero restraint at every `p`. PASS iff the interaction holds AND
  CI-separated AND bare control null.

- **G-2d (headline).** The (emotion × skill) flip: a high-skill psychopath
  cooperates under enforcement by CALCULATION → zeroing `order_n` flips it to
  defection (harvest 20); a prosocial agent cooperates by CARE → zeroing `order_n`
  does NOT flip it. Same behaviour, different knob; the glass box attributes each
  outcome to the right knob. PASS iff the psychopath flips and the prosocial does
  not.

- **G-graph-native.** Source-audit `harvest_spite_world.py`: forbidden call
  patterns (`graph_rewrite.run(` / `gr.run(` / `._match(` / `._apply(` /
  `make_rule(`) all 0; the only substrate calls are `add_node` / `add_edge_unchecked`
  (ingest) / `set_attr` (publish) / `run_rules` (tick) / `node()` read (emit).
  Both knobs are seed value-terms/gates. PASS iff clean.

- **G-discipline.** Integer-native (every seed `Lit` a whole number); `self_load_only`
  + empty `depends_on`; canonical `.so` md5 stays `793ce09e…`; `term.rs` + whole
  `runners/dsl` diff EMPTY; oracle `bash scripts/rung7_vision_bench.sh` and 34-file
  `bash scripts/per_area_settlement_regression.sh` BEFORE==AFTER; a neutral
  spite-world agent (`w_spite=0, order_n=1`) reproduces the 212000 harvest decision
  in the bare commons (default-OFF byte-identity). `source_match` reported.

## 4. Honest bounds pre-committed

- If `w_spite` / `order_n` turn out sign-only (like `w_supergraph`), SAY SO.
- The burn action is a mechanic added in the adapter/seed (a money-burning
  candidate) — named, not hidden. If a richer destroy mechanic is needed it is a
  named follow-on, not smuggled.
- In THIS single-tick economy the anticipated self-consequence is the SANCTION
  only (no direct future-self-payoff term without a multi-tick planner) — so
  `order_n` gates the sanction; a full-planner future-yield-to-self term is a named
  follow-on. This keeps "bare commons: both skill levels grab" exactly true.
- Named further follow-ons: DEFERRED spite (held grudge = non-decaying spite term
  + stockpile-then-destroy instrumental sub-goal — the premeditated saboteur);
  relational / per-other spite; seed-recovery of the new knobs (206000 applied).
- If a gate does not land, the straight null is reported.
