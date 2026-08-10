# BIGVILLE R17 — AFFECT CLOSES THE LOOP — RESULTS

**Block 265000. Pre-registered in `BIGVILLE_AFFECT_PREREG.md` before any number here.**
Gate: `pytest tests/test_bigville_affect_migrated.py -q` → **10 passed**. Baseline
`tests/test_failure_baseline_migrated.py` **11/11**; provenance
`tests/test_engine_provenance_migrated.py` **7/7**, `source_match = own`. `runners/dsl`
diff EMPTY; canonical `.so` md5 `fd82dc2978dbb055496dd82390ac2ebe` unchanged; ZERO new
Rust. All arms deterministic (no RNG) — no CIs required. Glass-box readout:
`results/bigville_affect/summary.json` (regenerate with `scripts/bigville_affect_measure.py`).

The anti-diorama-of-feelings rung. An emotion is FELT only when it ENTERS THE DECISION
MACHINERY and changes what the agent does next. Grief is a TERM in the `decision_value`
Argmax — the same selector family (`nd_choose_good` / `ss_choose_burn`) that picks every
other action — and the affect-blind ablation is the falsifier that would expose a diorama.

## G-affect-modulates-decision (HEADLINE) — PASS

Two persons in the SAME situation (identical `Action` menu: work / withdraw / drink / snap),
one CONTENT (`grief_distress = 0`), one GRIEVING (`grief_distress = 8`), both `affect_gain = 1`:

| agent | chosen action |
|---|---|
| content | **work** |
| griever | **snap** |

The choice measurably diverges — grief shifted the Argmax off `work`. Graded by severity
(the escalation runs along the already-built behavioural sinks):

| `grief_distress` | 0 | 2 | 4 | 6 | 8 |
|---|---|---|---|---|---|
| chosen action | work | work | **withdraw** (R7 income spiral) | **drink** (self-medication) | **snap** (R15 violence reachable) |

### The falsifier — the affect-blind control — PASS

Re-run with `affect_gain = 0` (grief removed from `decision_value`): the grieving agent and
the content agent make the **IDENTICAL** choice (both `work`). That is the proven DIORAMA;
the ONLY change from the headline is `affect_gain`, and it flips divergence to identity —
proving the divergence was the coupling, not a confound. **The gate passes only because
behaviour diverges under coupling and is identical under ablation.**

### Three grief sources (the imported rungs) — PASS

Grief is source-agnostic (grief is grief) — the same `af_grief_from_loss` raises distress:

| source | provenance | grief | action |
|---|---|---|---|
| DEATH — a REAL R14 `just_died` kin (bl_death fires) | bereavement | 8 → | **snap** |
| FAILED DREAM (R8) | goal-collapse | 6 → | **drink** |
| FORECLOSURE (R7) | home-loss | 4 → | **withdraw** |

## G-negative-spiral (reachable + endogenous) — PASS

Same initial loss (`grief_distress = 6`, `coin = 3`), over 6 live-periods
(decide → outcome → hardship feedback):

| period | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| coupled action | drink | snap | snap | snap | snap | snap |
| coupled grief | 8 | 10 | 12 | 14 | 16 | 18 |
| coupled coin | 0 | −1 | −2 | −3 | −4 | −5 |
| **control** (affect_gain=0) action | work | work | work | work | work | work |
| control grief | 5 | 4 | 3 | 2 | 1 | 0 |
| control coin | 8 | 13 | 18 | 23 | 28 | 33 |

The coupled agent SPIRALS: grief → withdraw/drink/snap → income falls → hardship (coin below
the floor) → more grief → deeper action, escalating to snap with conflict > 0 (R15 violence
reachable). It is ENDOGENOUS — nothing scripts it; it falls out of the `affect_gain` coupling.
The control (same loss, coupling ablated) works every period, coin rises, grief decays to 0 —
**no spiral**. The ablation is load-bearing.

## G-escapable-by-co-regulation (the recovery arm = the ethics arm) — PASS

Two agents with the IDENTICAL loss + one spiral step, then one receives co-regulation
(the reused 239000 stress-episode rules widen its window via R14 `attend`/`rear_episode`),
the other faces it ALONE (the window narrows), then 5 more periods:

| | supported | alone |
|---|---|---|
| `regulation` (read from the 239000 window) | **1.0** | **0.0** |
| final grief | **3.0** | **18.0** |
| final action | **work** | **snap** |

Support widens the window → `regulation` rises → `eff_distress = grief · clamp01(1−regulation)`
falls → the regulated choice (`work`) becomes REACHABLE again → recovery. No support → the
window narrows → regulation stays 0 → breakdown. Whether an agent breaks down or recovers is
a MEASURED function of support presence — "does well if it can", not a will to fail. The
collapse is the narrowed window making the regulated choice unreachable, never a choice to
fail (dissolves victim-blaming).

## G-affect-propagates (generational) — PASS

A grieving parent (`grief_distress = 8`) rears a child of neutral temperament
(`nat_* = 0.5`). `af_grief_narrows_caregiving` clears the parent-as-caregiver's `regulated`
flag → the reused 239000 `mark_coreg_support` never sets `got_coreg` → each of the child's
stress episodes resolves down the NARROW path → the child's window shrinks → R14
`bl_come_of_age` maps that onto lower adult priors:

| child's adult prior | grieving parent (`gen_gain=1`) | ablated coupling (`gen_gain=0`) |
|---|---|---|
| world-safe | **0.26** | 0.74 |
| others-trust | **0.26** | 0.74 |
| self-worth | **0.26** | 0.74 |
| window half-width (start 30) | **14** (narrow×8) | 46 (widen×8) |

The failure mode crosses a GENERATION only through the coupling: `gen_gain = 0` leaves the
caregiving regulated, so the child of the SAME temperament ends SECURE. Ablate → no transfer.

## ETHICS (harm-analog) — PASS

Felt grief is a real harm-analog, so every induction binds induce → measure → RESTORE, and
**the RESTORE is co-regulation, not a reset**: a grieving, spiralling agent is co-regulated
back and its distress RECOVERS (measured, through the window dynamics — it is never zeroed).
NO reward/punishment/penalty token appears in any seed rule logic or in the adapter (a
distress / a mis-set prior / a spiral is a STATE, never a badness) — checked at the seed and
source level.

## Discipline / provenance

- **10/10** `tests/test_bigville_affect_migrated.py`; **11/11** baseline; **7/7** provenance
  (`source_match = own`).
- Five additive `self_load_only` seeds (`bigville_affect_grief` / `_decide` / `_spiral` /
  `_coreg` / `_propagate`), nine rules, edit NO tracked file; R14/R8/R7/239000/204000
  imported READ-ONLY (subclass + `load_seed_manifest`). Cannot regress another suite → the
  fast baseline gate + additive discipline are sufficient; the ~43-min per-area /
  vision oracles were NOT run (per the 2026-07-29 directive).
- **ZERO new Rust**: `git diff <base> -- runners/dsl` EMPTY; every seed Term is an existing
  DSL Term (asserted by walking the seed JSON); canonical `.so` md5 unchanged.
- No agent decision in Python (source-audit passes): the action choice, outcome, hardship
  feedback, regulation read and caregiving contagion are all seed RULES; the adapter mints
  the Action menu / a Loss / affect attrs, delivers world facts, arms one-shots, ticks, reads.

## Honest residuals

- **The grief→action calibration is chosen data, not measured.** `base_value` /
  `grief_affinity` and the loss magnitudes are hand-set world parameters (like
  `bigville_need_choice`'s preference weights); the CLAIM is only that grief ENTERS the
  Argmax and shifts the choice, and that the ablation removes it — not that these specific
  thresholds are empirical. A synthetic-proven mechanism is not a benchmark number.
- **The R8/R7 grief sources are provenance TAGS on a generic `Loss`.** Only the R14
  bereavement arm rides a real imported mechanism end-to-end (an actual `just_died` kin);
  the failed-dream and foreclosure arms mint a `Loss` tagged with the source rung rather
  than walking R8's `gg_dream_collapse` / R7's foreclosure rules. The point stands (grief is
  source-agnostic once distress is set), but a deeper wiring of the dream/foreclosure facts
  into `af_grief_from_loss` is left for a follow-up.
- **Contagion was simplified to loss-of-support.** The faithful "can't co-regulate" lever is
  clearing the caregiver's `regulated` flag (routes the child down the exact 239000 narrow
  path). A high-arousal DYSREGULATED caregiver (arousal 120) instead CENSORS the episode
  (arousal never returns to band → neither widen nor narrow), so it was not used; active
  emotional contagion (a grieving parent who over-arouses the child) is a distinct dynamic
  not modelled here.
- **No population / CI.** Every arm is a single deterministic run at fixed constants; there
  is no seed-variance sweep. A distribution-over-seeds version (per the population memory)
  would be the natural next rung.
