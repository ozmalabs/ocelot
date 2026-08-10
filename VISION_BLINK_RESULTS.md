# THE BLINK — a temporal hole CONFABULATED, grounding CONSTRAINS the guess (RESULTS)

*Pre-registration `VISION_BLINK_PREREG.md`, committed at `2a6d74dd` BEFORE the
confirmatory run (the first cut; the creator's confabulate-by-default correction
is folded into the same file and superseded the mechanism before any confirmatory
seed was consumed — the RNG floor `31100–31499` was run only after). Runner
`scripts/blink_measure.py`; gate `tests/test_blink_bridge_migrated.py`; seed
`seeds/blink_bridge.json` (built by `tools/build_blink_bridge.py`); Rust Term
`BlinkBridge` (`runners/dsl/src/shape_decode.rs::eval_blink_bridge`). Engine
`4ccfea943ac8` (this worktree's OWN build — the rung adds Rust, §10.1). Bench with
`data/` symlinked (§10.2). Seed block **31000–31999**; floor **31100–31499**.*

## Headline

**The eye bridges a TEMPORAL hole by CONFABULATION, and grounding CONSTRAINS the
guess — bounded to the discrete/integer, in-frame motion class.** A blink is a
hole in the temporal orbit (`f0,f1,[BLINK],f4,f5`); the eye ALWAYS fills it with a
best-guess continuation (perception does not go silent — predictive coding: the
prediction stands where there is no data). Grounding decides only how CONSTRAINED
and CONFIDENT the guess is: a CONSISTENT motion pins it to `M^k(last)` (tracks the
motion, invisible) at high confidence; an UNGROUNDED prefix still fills, with the
freeze default at confidence 0 (unconstrained — the seed of hallucination, not
silence). All five discrimination claims PASS; the bridge is LOCAL (fitted
exponent **0.667**, NOT the O(N²) drive). **Every prediction held; no proviso
broke** — except the one I pre-registered as the likely break (correction
saturates once footprints separate, exactly as (d) predicted).

## The creator's correction (folded in before the confirmatory run)

My first cut had the blink REFUSE / hold open when ungrounded. **Wrong.**
*"Confabulation is the DEFAULT… if cognition doesn't know, it takes wild guesses.
That is also what sensory deprivation does."* Perception confabulates by default
(Charles Bonnet, deprivation-tank hallucinations, phantom limbs); grounding only
constrains the guess. So there is **one always-firing fill rule**, not a
bridge/hold pair; "held open" is deleted. DISCOVERY (minting a permanent
dimension, `time_axis`) stays conservative (MDL); PERCEPTION (this bridge) is
liberal (fill by default). The measurement discipline is on the SCIENTIST's
report, never on the eye — the eye confabulates.

## What was built (ONE new Rust Term + one seed rule)

- **`BlinkBridge`** (Rust) — input `[prefix(visible), gap(EMPTY = blink),
  resumed(visible)]`. Infers `G` from the first prefix pair (translate preferred,
  else the SAME integer 2×2 test as `TimeInfer`), VERIFIES it across the prefix
  (`confirm_run` = confirming transitions = the temporal support), and ALWAYS
  produces a continuation: `bridged[j] = G^{prefix_len+j}(f0)` when `constrained`
  (the whole prefix is one orbit), else the FREEZE default (`last` frame). Reports
  `constrained`, `confidence = confirm_run/(confirm_run+gap)` (RELATIVE, falls out
  of support), `frozen` (the persistence baseline), `diverged_at` (first resumed
  tick whose observation ≠ the guess) and `correction` (symmetric-difference cell
  count there — the perceptible jump). Reuses `infer_translate_offset` /
  `apply_linear_once` / `apply_translate_once` / `apply_generator_k` /
  `frames_equal` — no new primitive; the only new free fn is `frames_symdiff`.
- **`blink_bridge.json`** — one rule `blink_bridge_fill` (flag
  `blink_bridge_enabled`, OFF by default §9): on any `blink_seq` Observation it
  ALWAYS confabulates; grounding decides only constraint + confidence, both read
  from `BlinkBridge`'s fields (PROTOCOL §0 — no Python conditional). Loaded only by
  the runner/gate (like `time_axis`), so the bench is untouched.

## The five discrimination claims (confabulate-by-default) — 5/5 PASS

| claim | result | reading |
|---|---|---|
| **H_grounding_constrains** | consistent `translate(1,0)` blink → guess == truth at each blink tick (`[1,1]`), `frozen != truth`, `constrained=1`, `confidence=0.5`; change the motion → the guess changes (tracks M) | grounding CONSTRAINS the confabulation to `M^k(last)` — not a freeze, not a stored default |
| **H_invisible** | consistent-motion blink → `diverged_at=−1`, `correction=0` | the percept is continuous — no shutter, no seam (the headline phenomenology) |
| **H_change_blind** | change DURING the blink (stop@t3) → detected@t5, **latency 2**; change in a VISIBLE frame (stop@t6) → detected@t6, **latency 0** | change blindness FALLS OUT: the confabulated continuation stands through the blink and is revised only when data diverges; a visible change is signalled at once |
| **H_correction** | change during the blink at gaps {1,2,3,5} → **always filled**, `correction` **6→8→8→8** (grows then saturates), `confidence` **0.75→0.60→0.50→0.375** (decays); consistent no-change → `correction=0` at every gap | it does NOT refuse a long gap — it guesses anyway, and the correction on divergence GROWS with how far it guessed blind (the perceptible "jump"), while confidence decays. The saturation at 8 is the footprints fully separating — pre-registered proviso (d) |
| **H_unconstrained** | accelerating prefix → **filled** + `constrained=0`, `confidence=0`; **400** shuffled prefixes (31100–31499) → **all 400 still fill**, **0** non-orbit shuffles falsely `constrained` (0 monotonic draws arose) | without a generator it STILL confabulates (the seed of hallucination, not silence), but UNCONSTRAINED — and the constraint flag is HONEST (never over-claims grounding on noise) |

Plus **H_offday (§9):** flag OFF → the blink sequence is inert (`status` stays
`blink_seq`, no fill). **scaling:** fitted exponent **0.667** in cell count (4→128
cells, boot excluded), NOT the O(N²) drive.

## The instrument — positive-controlled (§1 clauses 4/5, §12.4)

- **the blink is REAL:** the blink frames carry NO data (the input frame IS
  empty) — the bridge fills a genuine temporal hole, verified before every arm.
- **the bridge is GROUNDING, not a freeze:** change the pre-blink motion ⇒ the
  guess changes (tracks `M`), and the guess differs from the persistence baseline
  on every bridged tick.
- **the bridge is GROUNDING, not a stored default:** no-consistent motion ⇒
  `constrained=0`, `confidence=0` (it still fills, but grounding did not pin it —
  the honest low-confidence guess). The 400-shuffle floor confirms the constraint
  flag never fires on noise.

## Every constant falls out (§13)

- the translate offset `δ` / linear matrix `M` are READ from the data (the first
  prefix pair), never chosen;
- `confidence = confirm_run/(confirm_run+gap)` is RELATIVE — the fraction of the
  extrapolation backed by CONFIRMED evidence (the confirmed-transition count is the
  temporal support; the gap is the blind extrapolation). No fixed-K constant; it
  DECAYS with the gap because you are guessing further, blind. Unconstrained ⇒
  support 0 ⇒ confidence 0 (an honest "guessing blind");
- the orbit test is EXACT integer equality (no tolerance);
- `correction` is a measured symmetric-difference cell count, not a threshold;
- the floor's `n=400` was fixed in advance.

## §9 — defaults preserve committed results

Ships INERT (`blink_bridge_enabled=0`): the fill rule never fires and no
Observation is a `blink_seq` in the normal ladder. Verified on engine
`4ccfea943ac8`:

- vision bench **200 passed / 0 failed** with `data/` symlinked (§10.2);
- sibling gates green: time 6/6 · depth 8/8 · stereo 9/9 · vision-ground 11/11 ·
  dimension-inference 8/8 · gen_infer 7/7 · sdloop_vision 15/15 · provenance 7/7;
- the new gate `tests/test_blink_bridge_migrated.py` **9/9**;
- the sd orbit law `{2:1,3:2,4:2,6:2,12:4}` and every depth/time/stereo/ground
  contract are unmoved (the new Rust is purely additive — a new `TermNode` variant
  and its eval arm; no existing evaluation path is touched, and the seed is not
  loaded by boot);
- provenance reads OWN (this tree's Rust source built this engine).

## What is NOT claimed (§8 — the honest bounds)

- **Bounded to the DISCRETE / integer, in-frame motion class** — a SINGLE blink
  block, one transition generator, integer velocity. Multiple blink blocks,
  sub-integer / continuous motion (cross-frame — the frame/continuum invariant),
  and acceleration are OUT.
- **The unconstrained guess degrades to the FREEZE default** (one of the creator's
  "freeze / drift / flicker"). A genuinely noise-SEEDED hallucination (Charles
  Bonnet content) is NOT modelled — the seed of hallucination is reproduced (fill
  by default, unconstrained, low confidence), not its generative texture.
- **`correction` saturates** once the guess and reality footprints fully separate
  (here at 8, one footprint apart). The monotone-growth claim holds up to
  saturation; a continuous displacement metric would not saturate but is
  cross-frame. Pre-registered as proviso (d).
- **The retinal step is at the active-cell/change level** (`scripts/
  blink_retina_probe.py`: a footprint drifting across a 30×30 retina, blinked for
  two ticks, is bridged for 3 velocities — footprint tracked, invisible; a
  shuffled drift still fills but unconstrained). The full center-surround event
  pipeline (a moving blob under adaptation is not an exact-integer-rigid
  translation) is a separate rung, as the TIME/DEPTH rungs bounded theirs.
- **This is a perceptual-filling model, not a claim about the biological locus.**
  It reproduces the perceptual verdict (the blink is invisible; change blindness;
  the perceptible correction; deprivation-style unconstrained filling); it does not
  discriminate retinal vs cortical filling-in.

## The verdict, plainly

**Does the eye bridge a TEMPORAL hole by grounding — invisible, motion-continuing,
change-blind, revisable, filling a long gap with a growing correction and filling
an ungrounded gap unconstrained rather than going silent?** YES — measured, and
bounded to the discrete integer-velocity in-frame class. The blink is invisible
because the field CONTINUES the motion generator through the hole (the guess ==
the frame that would have been seen), not because a sample happened to be there. A
change made during the blink is bridged over by the confabulated continuation and
detected only when data returns and diverges — change blindness, reproduced as a
CONSEQUENCE of the grounding, not built in. The eye does not refuse a long gap or
go silent without a generator: it CONFABULATES by default (the seed of
hallucination), and grounding only CONSTRAINS the guess — tightly to `M^k(last)`
under consistent motion (invisible), loosely to the freeze default without one
(low confidence). And it is LOCAL / O(≤N). **The creator's correction was the
whole result: perception is liberal (fill by default) where discovery is
conservative (refuse false structure) — I had imported the discovery discipline
into perception, and the blink is perception.**

**What I got wrong, and fixed, before believing anything:** my first mechanism
made the blink REFUSE / hold open when ungrounded (a `blink_bridge_hold` rule and
a `gap ≤ confirm_run` decay refusal). The creator corrected it: that is the
silence model, falsified by sensory deprivation. The fix collapsed two rules to
one always-firing fill and moved the whole discrimination FROM "refuses" TO
"reproduces the confabulation phenomena" (change blindness / perceptible
correction / unconstrained guess), with grounding constraining rather than gating
the fill. The M-tracking positive control survived unchanged — it is what proves
grounding constrains the confabulation.
