# MOOD R1b — the autocorrelation adaptive gate on a FAIR persistent-regime world — RESULTS (block 237000)

*Measured on the pre-registered design (`MOOD_R1B_PREREG.md`), single pinned
config, ONE run, no post-hoc change to the headline or any parameter. Isolated
worktree off `main` `e742e94d99`. REUSES `seeds/mood_r1.json` +
`seeds/mood_r1_task.json` verbatim (no new mood mechanism, no new seed). Own
engine build (`provenance_stamp` = **own**, `_native.abi3.so` md5
`10f65be659e0d9a9290aff39f7f5b92a`); canonical shared engine md5
`e75bc65021b6be0740abeee63662e21b` UNCHANGED. NO Rust — `runners/dsl/src` diff
EMPTY. Measured by `scripts/mood_r1b_measure.py`; pinned by
`tests/test_mood_r1b_migrated.py` (12 passed).*

## BOTTOM LINE — the pre-registered headline is a NULL, but a QUALITATIVELY DIFFERENT (adaptive-in-direction) one

**On the FAIR persistent-regime world, mood-momentum FLIPPED to the adaptive
direction — it HELPS in the regime world and HARMS in the i.i.d. control — but
the regime effect fell a WHISKER short of the strict CI-above-0 bar (lower CI
bound −0.05). The pre-registered headline does NOT pass. It is another NULL, and
it is reported straight.**

| world (K=200 episodes, N=200 trials, fast lr=0.1) | WITH−WITHOUT cumulative-reward gap | 95% bootstrap CI | verdict |
|---|---|---|---|
| **persistent regime** (2-state, dwell~20, switch p=0.05; lag-1 autocorr 0.691) | **+0.622** | **[−0.050, +1.277]** | mean POSITIVE (mood helps); CI lower bound a whisker below 0 → NOT CI-above-0 |
| **i.i.d.** (same multiset permuted; lag-1 −0.010) | **−1.903** | [−2.661, −1.142] | CI **below 0** — mood HURTS (a valid, correctly-behaving failable control) |

The two worlds share an EXACTLY matched marginal (per-episode mean/var differ by
`2.2e-16 / 4.4e-16` — a permutation of the same stream), so persistence is the
ONLY difference. Baseline WITHOUT-mood cumulative reward: regime 61.0, i.i.d.
18.5. The regime gap is +1.0% of baseline.

**Why this is a much stronger result than R1's null (the fair design worked, in
direction).** R1 (AR(1), lr=0.3) had BOTH worlds NEGATIVE (auto −1.02, i.i.d.
−1.39) — the mood-as-noise signature. R1b's two principled changes moved the
effect to the ADAPTIVE pattern:
- the regime gap went from negative to **POSITIVE (+0.62)** — mood now HELPS
  where returns persist;
- the i.i.d. gap stayed clearly **NEGATIVE (−1.90)** — mood HURTS where they
  don't;
- the two are **CI-separated from EACH OTHER** (regime `[−0.05, +1.28]` vs
  i.i.d. `[−2.66, −1.14]`): mood's effect is **+2.5 reward units MORE positive**
  in the persistent world than in the matched-marginal i.i.d. world.

So the fair world flipped the SIGN of the effect exactly as mood-as-momentum
predicts. What it did NOT do is clear the strict pre-registered bar: the regime
gap's 2.5th-percentile bootstrap bound is −0.05, so `regime_ci_above_0 = False`
and `headline_pass = False`. **This is a near-miss null, not a pass — and it is
recorded as a null.** (t-CI agrees: regime `[−0.049, +1.292]`.)

## What DID hold — the mechanism, the control, and the discipline (all gated green)

**G-momentum — the momentum signal is a correct leaky signed-RPE tracker (at the
pinned lr=0.1).** `Mood.momentum` rises in a good run (+0.500) and falls in a bad
run (−0.995); the trended good−bad separation is +1.495, 95% CI [1.474, 1.517]
(CI-above-0), and the **shuffled-stream control kills it**: separation −0.051,
95% CI [−0.117, +0.015] (contains 0). The momentum IS the leaky EMA of the signed
RPE `(r − v)` — R1's pinned RPE choice, kept verbatim.

**The i.i.d. control is a VALID failable control.** It behaves as designed: mood
does NOT help where returns carry no persistence — it HURTS (CI entirely below
0). Had it helped in i.i.d. too, the effect would have been noise/optimism; it
did not.

**G-glass-box.** `Mood` is a readable node (`momentum`, `gain`, `enabled`);
`bias` is a readable `MoodTask` attr; every update is a named rule
(`mood_momentum`, `mood_bias`, `mt_decide`, `mt_accrue`, `mt_rpe`, `mt_learn`);
source audit clean — the R1b adapter (and the reused R1 adapter) run no Python
rule engine and take no `if`/`else` over a mood value.

**G-discipline.** NO new Rust Term — the momentum EMA uses only atoms `sd_blend`
already uses; `runners/dsl/src` diff EMPTY; NO new seed (both seeds reused
verbatim). Default-OFF byte-identical (no `MoodTask`/`Mood` node on the default
path; 5-frame photon fingerprint equal with/without the two seeds loaded). Engine
provenance **own** (`source_match = own`).

## LABELED NON-GATE diagnostic (NOT a pre-registered gate) — value-prediction MSE

Reported for interpretation only, never as R1b's result. Does momentum improve
the raw value-prediction MSE (mean `raw_rpe²`)?

| world | MSE improvement (without−with, >0 = mood helps) | 95% boot CI |
|---|---|---|
| regime | **−0.012** | [−0.023, −0.001] |
| i.i.d. | **−0.048** | [−0.052, −0.045] |

Momentum slightly WORSENS the raw prediction MSE in BOTH worlds (more so in
i.i.d.), yet HELPS the cumulative-REWARD choice metric in the regime world
(+0.62). The reconciliation: the accept/decline choice cares about getting the
SIGN of `v` right FASTER at a regime switch, not about minimising per-trial
squared error — momentum accelerates the post-switch sign-crossing (adaptive
where switches persist) at the cost of a little extra overshoot on within-regime
noise (which the MSE penalises but the thresholded choice largely ignores). This
is why the pre-registered metric is cumulative reward, not MSE.

## Discipline ledger

- Prereg committed ALONE before any number (`MOOD_R1B_PREREG.md`, commit
  `f9660a40be`); seed-claim `237000–237999` CLEAN.
- Own engine built from committed source; provenance **own**
  (`10f65be659e0d9a9290aff39f7f5b92a`). Canonical shared engine
  `e75bc65021b6be0740abeee63662e21b` UNCHANGED end-to-end (never written
  through).
- `runners/dsl/src` diff EMPTY (no Rust, no Term). NO new seed (R1 seeds reused).
- Additive new files only (`mood_r1b_*` / `MOOD_R1B*`); explicit `git add` of
  each path; no existing tracked file touched.
- Oracle `scripts/rung7_vision_bench.sh` BEFORE == AFTER = `214 passed, 10
  skipped` (data-less worktree — `data/` not symlinked). `scripts/per_area_settlement_regression.sh`
  failing node-id SET BEFORE == AFTER (23 pre-existing data-less
  elaboration/topic-route reds; the composer test is FIXED on this base and is
  NOT in the set); ZERO new reds from R1b's additive files (the per-area list is
  a fixed file set that does not include the new test).
- `tests/test_mood_r1b_migrated.py` 12 passed — it PINS the null (regime gap NOT
  CI-above-0, `headline_pass` False) so it cannot silently flip to a claimed
  positive, while pinning the adaptive DIRECTION that DID emerge (regime gap
  > 0 > i.i.d. gap, regime CI-separated above i.i.d.) plus the mechanism +
  discipline that held.

## Honest residuals

- **The headline is a NULL at the pinned config** — reported as the primary
  result, not softened into a pass. The regime CI lower bound (−0.05) is below
  the strict CI-above-0 bar. The pre-registration named this exact possibility
  (§6: "R1b may come out null too"), and it did — a near-miss, correct in
  direction, short on separation.
- **But it is a materially different null from R1's.** The FAIR world (persistence
  without mean-reversion) + the lagging fast layer moved the effect from
  "hurts equally in both worlds" to "helps in the regime world, hurts in i.i.d.,
  the two CI-separated from each other." The mechanism the paper describes is
  present in DIRECTION and in the regime-vs-i.i.d. contrast; it is only the
  absolute-CI-from-zero separation that is missing, by a whisker.
- **Why it fell short of CI-separation (measured, not speculated).** The
  per-episode gap has high variance because the benefit is concentrated in the
  ~10 post-switch transients per episode while the ~90% within-regime steady
  state contributes near-zero signed momentum (correctly) but non-zero choice
  noise. The MSE diagnostic shows momentum adds a little within-regime overshoot,
  which erodes the transient gain enough to keep the lower CI bound at the
  boundary. A NAMED (not run) future rung could test whether a slightly longer
  dwell (fewer, cleaner transients) or a modestly lower gain CI-separates it —
  but that is a fresh pre-registration, not a re-pin of this one.
- **No sweep was run.** One pinned config, measured once. `lr=0.1` was pinned by
  principle (the lagging condition) before any number; `momentum_lr`, `gain`,
  `accept_thresh`, and the RPE were carried over from R1 unchanged. No parameter
  was tuned to move the result.
