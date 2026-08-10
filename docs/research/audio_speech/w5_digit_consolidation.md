# W5 in the digit forward model — consolidation attempt (HONEST: NEUTRAL→REGRESSION)

## VERDICT (lead)

**Wiring the proven W5 A-by-S formant correction (`lpc_formant_set_track`) into the
digit forward model `build_speech_forward` does NOT tighten the Stage-4 grounding
loop — it REGRESSES it.** The hypothesis the brief tested (forward/inverse formant
consistency lets the invariant ear ground DIRECTLY, the `three` sink tightens) is
**falsified by the numbers**:

| signal | closure baseline | W5-in-digit-path | delta |
|---|---|---|---|
| **digit formant re-analysis drift** (F1F2, intended target) | n/a (raw Klatt 621 Hz) | **243 Hz** (40/40 tokens reduced) | **−379 Hz ✓ (the fix WORKS)** |
| **INVARIANT-ear-alone round_trip** | 17.5 % | **17.5 %** | **±0.0 — UNMOVED (no direct grounding)** |
| **FUSED round_trip** | 60.0 % | **20.0 %** | **−40.0 pts ✗** |
| **OLD word-discriminative ear round_trip** | 62.5 % | **20.0 %** | **−42.5 pts ✗ (the regression source)** |
| `three` sink (FUSED) | 9 wrongs | sink moved to `five` (13) / `four` (17) | worse, scattered |
| coherent across personas (every voice > chance) | True (min 40 %) | **False (min 0 %)** | broke |
| babble-refine delta | +12.5 pts | +5.0 pts | weaker |

**The A-by-S correction does exactly what it claims on the formants** (digit F1F2
drift 621→243 Hz, reduced on all 40 tokens — the VCTK result reproduces in the digit
path) **— but that is not what closes the loop.** The loop closes via FUSION whose
ANCHOR is the OLD *word-discriminative* ear, and forcing the rendered formants onto
the per-digit articulatory nomogram targets (via LPC pole-set + cross-resynth) STRIPS
the rich spectral detail that ear depends on, collapsing it 62.5%→20.0%. The invariant
ear — the one the brief predicted would RISE — did not move one token (17.5%→17.5%):
it already VTL-normalises and reads dynamic gestures, so absolute-formant consistency
is **orthogonal** to what it grounds on.

**Action taken:** the wiring is in place and verified, but `axs_correct` defaults to
**False** — the closed loop is preserved; the consolidation is opt-in only. **Not
committed (coordinate).**

Log: `/tmp/w5digit_full.log` (end marker `===W5DIGIT_ALL_COMPLETE===`, pgrep-verified
COMPLETED, 4/4 component markers). Contrast: `/tmp/w5_contrast.py` output below.

---

## (1) Did W5-in-the-digit-path tighten the loop? — NO (honest)

The decisive do-contrast (same forward model, `axs_correct` OFF vs ON, same two ears
on the SAME spoken audio):

```
OLD base round-trip:   axs OFF  62.5%   axs ON  20.0%   delta -42.5
INV base round-trip:   axs OFF  17.5%   axs ON  17.5%   delta  +0.0
```

- **INVARIANT-ear-alone round_trip: 17.5% → 17.5% (the brief's primary hypothesis).**
  The hoped-for rise from "forward/inverse formant consistency" did NOT occur — exactly
  zero tokens moved. The invariant rep (`AF.vtl_formant_track` = VTL-norm `F_i - mean(F1..F3)`
  in log-Hz + order-1 dynamic gesture) is invariant to the absolute formant level the
  A-by-S correction fixes; driving the rendered formants to the intended absolute targets
  is orthogonal to what this ear reads. The forward↔inverse mismatch the 17.5% reflects is
  NOT an absolute-formant-drift mismatch — it is the rep's central-medoid bias, which the
  fix does not touch. (This is [[ozma_capability_is_binary_admissibility]]: the structure
  the invariant ear needs is either admitted or not — a formant-cleanup that doesn't supply
  it moves the number by exactly zero, not a little.)
- **`three` sink did NOT tighten** — under FUSED the sink moved to `five` (13 wrongs); under
  the invariant base it became `four` (17 wrongs). Scattered, not tightened.
- **FUSED round_trip: 60.0% → 20.0%**, dragged down by the OLD-ear collapse (the OLD ear is
  the fusion's full-weight ANCHOR).

**Why the OLD ear collapses:** the correction analyses the Klatt render's LPC poles, SETS
them to the intended per-digit formant targets (`lpc_formant_set_track`), and re-synthesises
through `lpc_cross_resynth`. This homogenises the spectral envelope toward the nomogram and
launders the fine formant-trajectory + spectral cues the OLD ear's exemplars + mel k-NN
discriminate on. The fix optimises the WRONG objective for the loop that actually closes:
it makes formants re-analyse to target (true, measured) but the closure runs on
word-DISCRIMINATIVE detail, which target-conformance erases. ([[ozma_fix_the_fixer]]: the
17.5% was the probe; "make the formants consistent" fixed the formants, not the thing the
loop grounds on.)

---

## (2) What was wired (file:line; architecture audit)

- **`domains/projection.py`** — new native A-by-S correction + wiring:
  - `_axs_render` (`:209`): the deterministic A-by-S formant correction for the digit path.
    Render → analyse the render's LPC track (`lpc_coeff_track` + `lpc_bw_expand_track`) →
    `lpc_formant_set_track` the poles to the intended targets → `lpc_cross_resynth` with the
    render's own residual (`lpc_residual_track`) → RE-ANALYSE (`lpc_formants_bw`, the SAME
    analyser the inverse uses) → measure drift from the intended trajectory → damped,
    best-tracked fixed point (`_AXS_ITERS=5`, `_AXS_LAM=0.7`). The exact A-by-S pattern of
    `scripts/synth_formant_fix.py:axs_solve`, with the ground truth = the agent's OWN intended
    articulatory formant trajectory (not a real speaker's print — digits are agent-internal).
  - `_measure_rendered_formants` (`:175`), `_resample_targets` (`:160`): mechanical glue.
  - `build_speech_forward.forward` (`:316`): applies the correction after the Klatt synth,
    behind `axs_correct` (DEFAULT FALSE).
- **`scripts/w5_digit_verify.py`** — the digit-path formant re-analysis verification harness.
- **NO Rust added.** `lpc_formant_set_track` and all the LPC primitives already existed
  (`runners/dsl/src/audio_primitives.rs:3387`, py-bound at `py.rs:6176`) — built for the
  proven VCTK W5. CortexLoop / `solve_for_n.py` / runners UNTOUCHED.

### Architecture / donkey audit — CLEAN (per CLAUDE.md "the agent is Rust")

- **Native correction, world-adapter glue only.** Every operator in `_axs_render` is a native
  Rust primitive (`lpc_coeff_track`, `lpc_bw_expand_track`, `lpc_residual_track`,
  `lpc_formant_set_track`, `lpc_cross_resynth`, `lpc_formants_bw` — all module-level
  `substrate_rs._native` functions). Python only marshals arrays and runs the deterministic
  damped fixed point.
- **No new Python cognition / decisions.** No conditional over graph state, no agent decision,
  no agent state. The fixed point's only branch is `if drift < best_drift` (mechanical
  best-tracking on a measured scalar — not a graph decision). Recognition stays native
  (the OLD `NativeRecogniser` / invariant `DtwTo` Argmin — UNCHANGED).
- **DONKEY clean:** owned classical DSP only. NO net, NO `.fit`, NO gradient, NO loss, NO
  sweep-to-fit. The A-by-S constants (`_AXS_*`) are fixed owned scales, NOT tuned to any score;
  the loop's only objective is the rendered formants converging to the intended targets.

---

## (3) The numbers

**Digit-path formant re-analysis (the W5 mechanism — it WORKS):**
```
   dim    OFF (raw Klatt)    ON (A-by-S)     delta
    F1          147.1 Hz        79.6 Hz    +67.5
    F2         1055.9 Hz       412.4 Hz   +643.5
    F3         1659.7 Hz      1058.6 Hz   +601.1
  F1F2 cue-dim drift:  OFF 621.3 Hz  ->  ON 242.6 Hz  (+378.7)
  tokens with F1F2 drift REDUCED by A-by-S: 40/40
```
The residual ~243 Hz is the `lpc_formants_bw` re-analysis floor on short 8 kHz Klatt frames
(more iterations do not reduce it: iters=10 → 283 Hz), not synthesis drift. The relative
reduction (621→243, all 40 tokens) is the W5 signal reproducing in the digit path.

**Stage-4 loop (the consolidation — it REGRESSES):**
```
  FUSED (anchor OLD + aux invariant, ckt)  :  20.0%  (was 60.0%)
  NEW base (Stage-3 invariant) alone       :  17.5%  (was 17.5%)
  OLD base (pre-curriculum) alone          :  20.0%  (was 62.5%)
  coherent across personas                 :  False (min 0.0%)   (was True, min 40%)
  babble-refine delta                      :  +5.0 pts           (was +12.5)
```
Per-persona FUSED: pip 20 / ada 40 / milo 20 / bertram 0. Do-contrast (axs OFF→ON, same audio):
OLD 62.5→20.0 (−42.5), INV 17.5→17.5 (±0.0).

---

## (4) Honest verdict

**W5-in-the-digit-path is NOT a tightening — it is a net regression of the already-closed
loop, and the brief's central hypothesis is falsified.** The A-by-S correction provably drives
the rendered DIGIT formants to re-analyse to the intended targets (621→243 Hz, 40/40 tokens) —
the proven VCTK mechanism reproduces. But:

1. **The invariant ear did not ground directly** (17.5%→17.5%, ±0 tokens). It is invariant to
   absolute formant level; the consistency the fix supplies is orthogonal to the structure it
   needs. The 17.5% is a central-medoid-bias residual, not a formant-drift residual.
2. **The fix collapses the word-discriminative ear** (62.5%→20.0%) — the LPC pole-set +
   cross-resynth launders the spectral detail the OLD ear (the fusion's full-weight anchor)
   discriminates on. So the FUSED closure falls 60.0%→20.0% and persona-coherence breaks.

This is consistent with the closure doc's own caveat: *the loop closes via FUSION, not a single
fixed-forward-model rep; the invariant ear's 17.5% is the wall, not a bug a formant-cleanup
fixes.* The right structural reading: forward/inverse FORMANT consistency is not the missing
piece — the invariant ear reads VTL-normalised dynamic gestures, and the loop's closure lives in
the word-discriminative anchor that target-conformance erases.

**Disposition:** wiring kept (native, clean, opt-in), `axs_correct` DEFAULT FALSE so the closed
loop is preserved. The honest next lever is NOT formant-target conformance but supplying the
invariant ear the *word-discriminative* structure it discards (the fusion is the existing answer;
a single rep that is both invariant and discriminative is the self-imposed wall, not a synth fix).
**Not committed (coordinate).**

*Log: `/tmp/w5digit_full.log` (`===W5DIGIT_ALL_COMPLETE===`, pgrep-verified, 4/4 markers).
Harnesses: `scripts/w5_digit_verify.py`, `scripts/stage4_fusion.py`, `scripts/stage4_grounding.py`.
Contrast: `/tmp/w5_contrast.py`. Wiring: `domains/projection.py:_axs_render` (:209), `forward` (:316).*
