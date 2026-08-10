# LS20 FLASH-CONSUME FOLD — PRE-REGISTRATION (block 225000)

**Committed ALONE, BEFORE any gated number.** Folds 223000's flash consume-marking
onto 224000's object-permanence tracker to close ls20's trail/consume residual.

Block `225000-225999` claimed via `scripts/seed_claim.py 225000 225999` — the
verbatim `check_claim` output is recorded at the bottom of this file (NOT a
permanent pytest — that would invert once the ledger row lands, the 223000 mistake).

## THE RESIDUAL THIS ATTACKS

224000's tracker translates the tracked object per-cell and gets live change-set
strict-F1 **0.9639** on real ls20; the honest **~0.036 gap is the TRAIL/CONSUME
residual** — when the avatar moves it drops/consumes cells a rigid-translate model
cannot predict (224's synthetic `trail` scene scored **0.86** for exactly this
reason). 223000's flash rung DETECTS + LOCALISES the consume event on real frames
(the general onset stream fired 50/50, Argmax `fg_pick_flash`) — it was never wired
into prediction. This rung FOLDS them.

## THE MECHANISM (compose 223 + 224; graph-native)

The 224 `LiveObjectTracker` is reused UNCHANGED (translate the tracked object,
graph shift Hypothesis). ADDED: a flash-consume marking. The flash onset (223's
general onset stream) coarsely localises WHERE the consume happened this step; the
tracker supplies the VACATED footprint (old object positions the translate leaves);
the model marks the flash-localised VACATED cells as consumed → a DISCOVERED trail
value T (a graph `ConsumeHypothesis`). Combined per-cell prediction = translate
(224) + mark the flash-localised consumed cells (225). The flash LOCATION is a
graph rule (`fg_pick_flash`, Argmax onset magnitude, reused from 223); the consume
VALUE is a graph rule (`cm_mint`/`cm_confirm`/`cm_revise`, `seeds/ls20_consume.json`);
the marking render is mechanical adapter I/O — the same split 224 uses for the
translate.

## ANTI-CIRCULARITY (the fatal trap — stated explicitly, kept airtight)

The flash could trivially win if it handed the model the exact consumed set. It
does not:

1. **The flash is a LUMINANCE-only transient** (a soft GLOW blob, `FLASH_COLOUR`
   luminance around the consumed region), NEVER written into the colour grid. The
   colour grid both arms score on is flash-free.
2. **The glow is COARSE, not a pixel-perfect outline of the consumed cells.** Its
   brightest onsets ring the consume (the dim field around it jumps furthest — the
   same 223 phenomenon where the flash lands on background adjacent to the object);
   the model windows the cluster centroid to reach inward, so the flash-localised
   set is measurably IMPRECISE. **HONESTY BOUND (pre-committed): flash consume
   PRECISION < 1.0** — if precision were 1.0 the flash would be an oracle and the
   result worthless.
3. **The consumed region VARIES per step** (a per-step contiguous sub-block of the
   vacated footprint), so a fixed object-relative offset cannot predict it — the
   per-step flash is genuinely needed.
4. **The consumed VALUE T is DISCOVERED from observation** (`ConsumeHypothesis`),
   never handed by the flash, never hardcoded.
5. **The flash region alone is not enough** — it spans FIELD cells; the model must
   intersect it with the tracker's VACATED set (the object model 224 supplies) to
   pin the figure cells. Neither the flash nor 224 alone closes the residual.

## ESTABLISHED BASELINE (224-alone, pre-measured to size the gate)

On the synthetic consume scenario (`ConsumeArena`: solid avatar block roaming a
nested field; each move fully vacates its old footprint and consumes a per-step-
varying `csize×csize` interior sub-block to a trail value; a luminance glow marks
the consume), **224-alone (translate only) scores change-set strict-F1 ≈ 0.78** —
a real trail residual to close (translate misses every consumed cell). This is the
pre-measured baseline the gate is sized against; the OFFICIAL numbers below are
measured AFTER this prereg is committed.

## PRE-COMMITTED GATES (relative / CI-separation — sized before the official run)

- **G-trail-closed (HEADLINE, OFFLINE powered ablation).** Over ≥ 20 seeds, paired
  by step (all arms see IDENTICAL frames + onsets), the PAIRED bootstrap 95% CI of
  `mean(flash_F1 − translate_F1)` has **lower bound > 0** — the flash-folded model's
  change-set strict-F1 BEATS 224-alone, CI-separated. **THE ABLATION IS THE GATE:
  if +flash does NOT beat 224-alone, the flash does not localise the consumed cells
  — report the NULL STRAIGHT** (the trail residual then needs a different mechanism).
- **G-flash-localises-consume.** The flash-localised predicted-consumed set's F1
  (precision/recall vs the ACTUAL consumed set) bootstrap CI **lower bound >** the
  random-flash control's consume-F1 CI **upper bound** — CI-separated above chance,
  proving the flash carries the consume signal, not just any marking.
- **Anti-rig null.** The RANDOM-FLASH control (same fold, flash location randomised)
  does **NOT** beat 224-alone: the paired CI of `mean(random_F1 − translate_F1)`
  includes or lies below 0. Proves the win is the flash's LOCALISATION, not the
  marking mechanism.
- **Over-predict control.** `blind_all` (mark ALL vacated cells as consumed) scores
  BELOW 224-alone — over-prediction is punished, so the discrimination the flash
  provides is what matters.
- **Honesty bound.** Flash consume PRECISION < 1.0 (not an oracle).
- **G-live (real ls20).** Auth verified BEFORE measuring (`ARC_API_KEY` from the
  gitignored `.env`, NEVER printed/committed; `.so` gitignored, NEVER committed).
  Report the flash-folded change-set strict-F1 on real ls20 (`ls20-9607627b`) vs
  224-alone's 0.9639. **If it does NOT beat 224-alone in budget, report the NULL
  STRAIGHT + what the flash localised.** If the API is unreachable/rejected/rate-
  limited, STOP and report — NEVER fabricate/cherry-pick/estimate. State fresh-API
  vs deterministic-replay.
- **G-graph-native + source-audit.** Flash-consume marking = a RULE using the onset
  signal (`fg_pick_flash` + `cm_*`); the 224 tracker UNCHANGED; adapter mechanical.
  No Python deciding the consumed set; no hardcoded consume table.
- **G-discipline.** Integer-native; default-OFF byte-identical (224 tracker + all
  ls20 suites unchanged with the fold off); canonical `.so` md5
  `793ce09ed498a749abb79aeaea44b92e` UNCHANGED (reuse 223 onset + 224 tracker — no
  new Rust); `runners/dsl` diff EMPTY (`term.rs` included); oracle `rung7_vision_
  bench` BEFORE == AFTER; 34-file regression fail-set IDENTICAL before/after.

## FALSIFICATION BAR

The flash-consume marking is GENERAL (the same onset stream that marks any
interaction/consume event — not an ls20 hack); the consumed-cell prediction is
DISCOVERED; the improvement over 224-alone is MEASURED (the fold can fail → honest
null). The gate could fail: if the coarse flash cannot localise the consumed cells
better than chance, +flash ties or loses to 224-alone.

## `check_claim` (verbatim)

```
SEED CLAIM 225000-225999: CLEAN -- no collision DETECTED.
  Scope: 930 files with seed sinks; 633 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```
