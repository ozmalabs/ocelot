# MOOD R1 — the autocorrelation adaptive gate — RESULTS (block 236000)

*Measured on the pre-registered design (`MOOD_R1_PREREG.md`), pinned config, no
post-hoc change to the headline. Isolated worktree off `main` `7ee7b7f5e9`. Own
engine build (`provenance_stamp` = **own**, `_native.abi3.so` md5
`10f65be659e0d9a9290aff39f7f5b92a`); canonical shared engine md5
`e75bc65021b6be0740abeee63662e21b` UNCHANGED. NO Rust — `runners/dsl/src` diff
EMPTY. Measured by `scripts/mood_r1_measure.py`; pinned by
`tests/test_mood_r1_migrated.py` (11 passed).*

## BOTTOM LINE — the pre-registered headline is a HONEST NULL/NEGATIVE

**At the pinned config (lr = 0.3, gain = 1.0) mood-momentum did NOT earn reward
in the autocorrelated world, and it hurt roughly EQUALLY in the i.i.d. world.**
The pre-registered adaptive gate is FALSIFIED as stated. This is the
mood-as-noise outcome the i.i.d. control was built to detect, and it is reported
straight — a real null beats a dressed-up positive.

| world (K=200 episodes, N=200 trials) | WITH−WITHOUT cumulative-reward gap | 95% bootstrap CI | verdict |
|---|---|---|---|
| **autocorrelated** (AR(1), φ=0.9, lag-1 measured 0.877) | **−1.02** | **[−1.35, −0.69]** | CI **below 0** — mood HURTS |
| **i.i.d.** (same multiset permuted; lag-1 −0.008) | **−1.39** | [−2.09, −0.69] | CI below 0 — mood HURTS |

The two worlds share an EXACTLY matched marginal (per-episode mean/variance
differ by `1.7e-16 / 4.4e-16` — a permutation of the same stream), so
autocorrelation is the ONLY difference. Baseline WITHOUT-mood cumulative reward:
auto 69.1, i.i.d. 17.8. The autocorrelated gap is −1.5% of baseline.

**The pre-registered honest-risk #4 BIT, precisely as named.** "Does mood's
adaptive value survive when the fast layer already tracks value well?" — No. At
lr = 0.3 the fast delta-rule value estimate already tracks the φ=0.9 signal well
enough that the additive momentum bias only **overshoots at turning points** (a
mean-reverting AR(1) punishes momentum-style extrapolation at reversals). The
post-hoc value-prediction diagnostic confirms it: at this config mood **increases**
the value-prediction error in BOTH worlds (MSE improvement auto −0.054
[−0.061, −0.048], i.i.d. −0.089 [−0.097, −0.081]) — the momentum feedback made
the estimate worse, so worse choices, hence the negative reward gap.

## What DID hold — the mechanism and the discipline (all gated green)

**G-momentum — the momentum signal is a correct leaky signed-RPE tracker.**
`Mood.momentum` rises in a good run (+0.166) and falls in a bad run (−0.331); the
trended good−bad separation is +0.497, 95% CI [0.485, 0.510] (CI-above-0), and
the **shuffled-stream control kills it**: separation +0.021, CI [−0.020, 0.062]
(contains 0). The momentum IS the leaky EMA of the signed RPE it integrates — the
pinned RPE choice `(r − v)`, the paper's `(r − v^s)`.

**G-glass-box.** `Mood` is a readable node (`momentum`, `gain`, `enabled`);
`bias` is a readable `MoodTask` attr; every update is a named rule
(`mood_momentum`, `mood_bias`, `mt_decide`, `mt_accrue`, `mt_rpe`, `mt_learn`);
source audit clean — the adapter runs no Python rule engine and takes no `if`/
`else` over a mood value.

**G-discipline.** NO new Rust Term — the momentum EMA uses only atoms `sd_blend`
already uses (`Plus / Times / Minus / IfThenElse / Gt / Eq / And / Attr / Lit`,
plus the structural `Var`); `runners/dsl/src` diff EMPTY. Default-OFF
byte-identical (no `MoodTask`/`Mood` node on the default path; 5-frame photon
fingerprint equal with/without the two seeds loaded). Engine provenance **own**.

**Mood rides the real decay machinery (the named reuse).** `mood_momentum` is
`momentum += momentum_lr·(raw_rpe − momentum)` = `(1−momentum_lr)·momentum +
momentum_lr·raw_rpe` — STRUCTURALLY `staleness_decay`'s `sd_blend` Kalman
held-vs-new blend `held + α·(new − held)` (blend coefficient `α = momentum_lr`),
where the `(1−α)` factor IS the leak: the extensional per-tick form of the
`sd_freshness` / `sd_freshness_generic` scale2 half-life decay toward zero. No new
atom, no new Term. It is the eye's order-1 "velocity of value" (`TimeInfer` /
`diff_pyramid`) pointed at reward.

## POST-HOC EXPLORATORY (NOT pre-registered, NOT a gate) — where the gate IS recoverable

Reported as a LEAD for a future pre-registered rung, never as R1's result. A
small lr × gain grid (K=100 episodes) asks: does the adaptive gate (auto gap
CI-above-0 AND i.i.d. gap NOT CI-above-0) separate for any nearby config?

| lr | gain | auto gap (CI) | i.i.d. gap (CI) | adaptive gate separates |
|---|---|---|---|---|
| 0.1 | 0.5 | **+0.65 [0.18, 1.12]** | −0.74 [−1.24, −0.23] | **YES** |
| 0.1 | 1.0 | **+1.28 [0.55, 2.00]** | −1.81 [−2.52, −1.09] | **YES** |
| 0.1 | 2.0 | +0.75 [−0.29, 1.80] | −3.97 [−5.11, −2.76] | no (auto CI touches 0) |
| **0.3** | **1.0** (pinned) | −1.48 [−1.92, −1.02] | −1.46 [−2.45, −0.47] | no |
| 0.6 | any | negative | negative | no |

**When the fast value layer is SLOWER (lr = 0.1 — more lag for momentum to
correct), the mood-as-momentum signature APPEARS:** momentum HELPS in the
autocorrelated world (CI-above-0) and HARMS in the i.i.d. world (CI-below-0) — a
STRONGER form of the adaptive gate than "≈0" (mood is beneficial exactly where
returns carry momentum, and actively harmful where they do not). This directly
corroborates honest-risk #4: the benefit exists but requires the fast layer NOT
already to anticipate the drift. The pinned lr=0.3 sat above that threshold. This
is the deciding structural finding, not a rescue: it says R1's headline is
recoverable by a future rung that PRE-REGISTERS a slower fast layer (or wires
mood over the genuinely-lagging `ModulatorState.valence`), and that the gain must
stay modest (gain=2.0 already over-drives it).

## Discipline ledger

- Prereg committed ALONE before any number (`MOOD_R1_PREREG.md`, commit
  `cd75d4b203`); seed-claim `236000–236999` CLEAN.
- Own engine built from committed source; provenance **own**
  (`10f65be659e0d9a9290aff39f7f5b92a`). Canonical shared engine
  `e75bc65021b6be0740abeee63662e21b` UNCHANGED end-to-end (never written
  through).
- `runners/dsl/src` diff EMPTY (no Rust, no Term).
- Additive new files only (`mood_*` / `MOOD_R1*`), all `self_load_only`.
- Oracle `scripts/rung7_vision_bench.sh` BEFORE == AFTER = 214 passed, 10 skipped
  (data-less worktree). `scripts/per_area_settlement_regression.sh` failing
  node-id SET BEFORE == AFTER (24 pre-existing data-less / live-daemon-reconcile
  reds incl. the known `test_ground_concern_dispatch_parity`); ZERO new reds.
- `tests/test_mood_r1_migrated.py` 11 passed — it PINS the null (auto gap NOT
  CI-above-0) so it cannot silently flip to a claimed positive, while asserting
  the mechanism + discipline that held.

## Honest residuals

- **The headline is a null at the pinned config** — reported as the primary
  result, not softened. The pre-registration was made in good faith; the
  measurement refuted it; the failure mode is the one named up front (risk #4).
- The exploratory grid shows the effect is real at lr=0.1 but this is **not**
  R1's result — it is a labeled lead for a re-pre-registered R1b.
- The mean-reverting nature of a stationary AR(1) means momentum-style
  extrapolation is penalised at reversals; a random-walk / drift-with-momentum
  return process (closer to the paper's "natural momentum") may be a fairer world
  and is a named alternative for R1b.
- The choice metric (accept/decline at threshold 0 on a zero-mean process) is
  noise-heavy near reversals; the value-prediction MSE is a cleaner mechanism
  readout and is recorded as a diagnostic, not substituted for the pre-registered
  cumulative-reward metric.
</content>
