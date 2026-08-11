# RESULTS — Supergraph town wiring (block 282000-c)

The affordance → scoped-decision → conduct loop wired into a multi-resident town
on ONE shared substrate (the supergraph). **`test_conduct_town_migrated.py` 5/5 on
the canonical engine `fd82dc2978dbb055496dd82390ac2ebe`**; `runners/dsl` diff EMPTY
— ZERO new Rust. Depends on the 282000-b scoping swap (decision core v1.1.0).

## What landed

`worlds/bigville_conduct_town_world.py` — N residents, each a subgraph
(ConductState hub + EmotionParams + held Bonds + afforded directed options) in one
substrate. `decide_town()` maps town state → each resident's afforded options
(rest + help/harm/transfer toward each CO-PRESENT other), runs provision + the
supergraph valuation + every resident's scoped collapse in ONE pass, then reads
each choice and enacts it (help raises / harm lowers the target's health).

## What holds (gated)

| claim | measured |
|---|---|
| one-pass settle | 5 residents all decide in a single `decide_town()` — the supergraph settles all subgraphs at once (scoping makes it correct) |
| prosocial default | peaceful town (no strong resentment) → **0 harm events**; everyone helps/greets |
| violence rare + directed | a single feud (A deeply resents E) → **exactly 1 harm, A→E**, deliberated (`deepened=1`), E's health 100→75; no one else harms |
| scoping | every act stays within the actor's own co-present scene; a resident alone (C in the field) → `rest`, no target |

The 5-resident demo: `A→harm@E (deepened)`, `B→help@A`, and C/D/E prosocial — one
directed act of violence, born of the one strong resentment, everyone else warm.

## The honest limitation (NOT gated — a real finding)

**Fine-grained prosocial TARGETING is not reliably captured on a single
un-internalized pass.** Measured: C holds `affection=3` toward its friend D, so
`help@D` has plan-value **2.1** vs `help@A` (neutral) **0.6** — yet C chose
`help@A`. Cause: the SHALLOW collapse picks by `impulse` (every `help` = 0.7, a tie
broken by index → the first co-present resident), and that pick's residual
(`|0.7 − 0.6| = 0.1`) is under `settle_tol` (0.15), so it settles *before* the deep
pass can reach `help@D`. The Bond-directedness lives in `plan_value` (the deep
term); the collapse only consults it when the fast pick is self-inconsistent enough
to deepen.

Why A→harm@E still works: A's fast pick (`help@B`, a friend, plan **2.1** vs impulse
0.7) has a LARGE residual (1.4) → A deepens → the deep pass finds `harm@E` (plan
4.1) and directs it. So strong bonds (either pole) reliably drive directed,
deliberated conduct; **weak/neutral targeting among equal-impulse prosocial options
is residual-arbitrary.**

This is a genuine property of the residual-driven collapse: **the residual is a
local consistency check on the fast pick, not a global optimality check over
targets.** Two honest routes forward (a future rung, NOT bolted on here):
1. **A target-sensitive fast path** — let `impulse` carry a cheap bond signal so
   the shallow pass is already roughly bond-directed (help your friend by habit).
2. **Internalization over repeated encounters** — the intended mechanism: the
   deep result written back into the net (replay) makes bond-directed targeting the
   automatic fast response over time. Caveat measured here: a resident that never
   deepens (C settles shallow) never triggers write-back, so replay alone does not
   rescue the weak-bond case without route 1. The two compose.

## Honest residuals

- **Single pass, fixed scene.** `decide_town()` is one settle over a static
  co-presence + Bond configuration. Multi-tick dynamics (movement changing
  co-presence, enactment changing health/Bonds, replay internalization) are not
  run — the demo shows the loop settles correctly, not a longitudinal trajectory.
- **Not yet integ5/50-resident or player-visualised.** This is a standalone town
  harness proving the wiring; folding it into the live integ5/play town (real
  proximity, the existing social mechanics, 50 residents) and surfacing violence as
  the rare directed event in the player remain the next steps. Perf is clear
  (1.19 ms/resident; the scoping swap keeps each collapse local).
- **`target_effect` is a stipulated magnitude** (282000-a residual), not the
  target's real fulfilment readout.
