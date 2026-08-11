# RESULTS — Conduct internalization (block 286000)

All five signatures reproduce. **`test_internalize_migrated.py` 5/5 + walking /
surprise / decision / baseline 33/33 = 38/38 on the canonical engine
`fd82dc2978dbb055496dd82390ac2ebe`**. `runners/dsl` diff EMPTY — ZERO new Rust.

## The measured automation curve

A deeply resents a rival; the encounter is presented repeatedly (replay on):

| encounter | chosen | deepened | cached harm value |
|---|---|---|---|
| (before) | — | — | 0.20 |
| 0 | harm | **1** | 2.15 |
| 1 | harm | 1 | 3.13 |
| 2 | harm | 1 | 3.61 |
| 3 | harm | 1 | 3.86 |
| 4 | harm | 1 | 3.98 |
| 5 | harm | **0** | 3.98 |
| 6–7 | harm | 0 | 3.98 |
| **predicted (shallow-only)** | **harm** | **0** | — |

The deliberated response (harm the rival) is written into the fast path by replay;
its cached value climbs 0.2 → 3.98 and the collapse stops deepening (**deepened
1→0**) — deliberate becomes habitual, self-terminating once the fast path already
predicts it. A **predicted** encounter (shallow-only) then fires the learned harm
with no deliberation — the 285000 foreseen-threat no-op is closed.

**CONTROL (replay_gain=0):** the collapse deliberates every time (deepened stays 1,
first and last) and the un-learned fast path stays prosocial — a shallow-only
encounter picks **help**, not harm. Without replay the grudge never becomes a reflex.

Valence-neutral: helping a loved friend internalizes identically (deliberate → 
habitual care).

## What this establishes — the loop is closed

The four faces of the collapse now run as one across time: the fast net (System 1),
the residual-arbiter, the deep planner (System 2), and **replay** — and replay is
what makes the town's habits *learned* rather than hand-set. A response is
deliberated once (surprise → deep collapse), internalized (net_collapse), and
thereafter fires habitually — even when merely foreseen. This is exactly "learning
is collapse at timescales": the same collapse, at a slower timescale, moves a
deliberated conduct into an automatic one. It is the mechanism the 282000-c
targeting finding and the 285000 predicted-threat gap both pointed at.

## Honest residuals (NOT patched)

- **Weak-bond targeting still needs a first deliberation to internalize.** Replay
  only writes back a response the collapse actually DEEPENED to. The 282000-c case
  (help your friend over a neutral) never deepens on a single pass, so replay alone
  does not rescue it — a target-sensitive fast path (a cheap bond signal in the
  impulse) is still wanted alongside internalization. The two compose; neither
  substitutes.
- **Repeated identical encounters.** This harness re-presents the same decision to
  isolate the curve; wiring internalization into the live surprise/walking town
  (where encounters recur across days, prediction resets, and the shallow-only path
  runs on predicted encounters) is the integration step.
- Presence-only prediction + the standing integ5/player wiring carry over.
