# THE BLINK — a temporal hole bridged by grounding (PRE-REGISTRATION)

*Committed BEFORE the confirmatory run (PROTOCOL §3). The temporal twin of the
blind spot (`VISION_GROUND_RESULTS.md`) and the composition of the grounded-field
fill with the TIME transition generator (`VISION_TIME_RESULTS.md`). Seed block
**31000–31999**; the only RNG arm (H_noconfab's floor) draws the **declared**
confirmatory seeds **31100–31499**. 12000–30999 untouched.*

## The idea

The blind spot proved vision is a grounded FIELD: a SPATIAL hole (no data) is
filled from the surround's belief, so the hole is invisible. **The blink is the
same hole, in TIME.** Every few seconds the eyelid closes for ~100–400 ms and the
retina receives NO input — yet no shutter is perceived. A blink is a hole in the
temporal orbit (`f0,f1,[BLINK],f4,f5`), bridged by CONTINUING the transition
generator `M` that carries `frame(t)→frame(t+1)`: the belief during the blink is
`M^k(last-seen-frame)`. On data return the belief is CONFIRMED or REVISED.

**Composition, not reinvention.** The bridge reuses `TimeInfer`'s infer-and-verify
(the generator) and `apply_generator_k` (the continuation); the blink is a hole
whose "surround" is the *temporal* neighbourhood and whose grounding is the
transition generator rather than the spatial contour. In-frame/integer only
(integer-velocity motion); continuous motion is cross-frame and DEFERRED (the
frame/continuum invariant).

## CONFABULATE BY DEFAULT — the creator's correction (supersedes this file's first cut)

**This pre-registration's first version had the blink REFUSE / hold open when
ungrounded. That was WRONG, corrected by the creator before the confirmatory run:**

> *"Confabulation is the DEFAULT. Because close enough is good enough — that's the
> whole point. If cognition doesn't know, it takes wild guesses. That is also what
> sensory deprivation does."*

Perception does not go silent when ungrounded — it CONFABULATES a best-guess,
because an agent must act now and close-enough beats paralysis. The empirical
proof is the deprivation case: remove input and the brain HALLUCINATES (Charles
Bonnet syndrome in the blind; sensory-deprivation-tank hallucinations; phantom
limbs; hypnagogia). **Ungrounded → confabulation, NOT silence.** Change blindness
is the same thing: the confabulated continuation stands *because* the system
commits to a guess.

**So the blink's DEFAULT is: confabulate the continuation. Grounding does not
decide WHETHER to fill — it only CONSTRAINS the guess:**
- **consistent motion** → grounding constrains the guess tightly to `M^k(last)` →
  a GOOD guess → invisible;
- **inconsistent / absent motion** → the guess is UNCONSTRAINED (the freeze
  default, low confidence) → the deprivation case in miniature: it guesses badly.
  NOT held-open, NOT silence — the seed of hallucination.

**The clean distinction:** DISCOVERY (minting a permanent dimension, `time_axis`)
is CONSERVATIVE (MDL — refuse false structure; a flat scene mints no depth). But
PERCEPTION / filling (this blink bridge) is LIBERAL (confabulate a best-guess,
revisable — because you must act now). This is predictive coding: perception
predicts (confabulates) and corrects on the residual; where there is NO data to
compute a residual (the blink), **the prediction STANDS — that IS change
blindness**, and the unconstrained case IS hallucination. The measurement
discipline (refuse to over-claim) is on the SCIENTIST's report, never on the eye's
behaviour — the eye confabulates.

## Mechanism (built with this pre-registration, committed together)

- **Rust Term `BlinkBridge`** (`runners/dsl/src/shape_decode.rs::eval_blink_bridge`,
  registered at the 8 `TimeInfer`-parallel sites) — input `sequence =
  [prefix(visible), gap(EMPTY = blink), resumed(visible)]`. Infers `G` from the
  first prefix pair (translate preferred, else the SAME integer 2×2 enumerate-and-
  test as `TimeInfer`), VERIFIES it across every prefix pair (`confirm_run` =
  confirming transitions = the TEMPORAL SUPPORT), CONTINUES it through the gap
  (`bridged[j] = G^{prefix_len+j}(f0)`), reports the PERSISTENCE baseline
  (`frozen` = last visible frame repeated), and on resume reports `diverged_at`
  (first resumed tick whose observation ≠ `G^t(f0)`; −1 if none). Reuses
  `infer_translate_offset` / `apply_linear_once` / `apply_translate_once` /
  `apply_generator_k` / `frames_equal` — no new primitive.
- **Seed `blink_bridge.json`** (`tools/build_blink_bridge.py`; flag
  `blink_bridge_enabled`, OFF by default, §9) — a SINGLE always-firing rule
  `blink_bridge_fill` (PROTOCOL §0, no Python conditional): on any `blink_seq`
  Observation it ALWAYS confabulates a continuation. Grounding decides only
  CONSTRAINT + CONFIDENCE, both read from `BlinkBridge`'s fields: a consistent
  motion (`constrained==true`) pins the guess to `G^t(f0)` at
  `confidence = confirm_run/(confirm_run+gap)` (RELATIVE, no constant); an
  ungrounded prefix still fills, with the freeze default at `confidence 0`. Matches
  only `status=='blink_seq'`. There is NO "hold open" rule.
- Loaded only by the runner/gate (like `time_axis`), so the bench is unaffected.

## The discrimination claims (confabulate-by-default; each a two-sided hypothesis)

A naive **persistence** ("freeze the last frame") or **interpolation** ("average
across the gap") must FAIL these; grounding-CONSTRAINED confabulation must pass.
The measurement discipline is on the CLAIM, not on the eye — the eye always fills.

1. **H_grounding_constrains — grounding CONSTRAINS the confabulation to
   `M^k(last)`, not a freeze.** Under consistent motion the filled guess at blink
   tick `t` equals the *predicted* `G^t(f0)` (the position the object would
   occupy), NOT the frozen last-seen position, at `constrained==1`,
   `confidence>0`. **Statistic:** per blink tick, `bridged == truth` (no-blink
   ground truth) AND `frozen != truth` AND `bridged != frozen`; plus TRACKS-M
   (change the pre-blink motion ⇒ the guess changes) AND `constrained==1`.
   **Two-sided:** a guess identical to freeze ⇒ persistence, not grounding (fail);
   a guess independent of the pre-blink motion ⇒ a stored default (fail).
2. **H_invisible — INVISIBLE under consistent motion.** The percept is continuous
   across the blink. **Statistic:** `diverged_at==−1` AND `correction==0` (resume
   matches the continued guess: no seam). **Two-sided:** a seam/void ⇒ the hole is
   perceived (fail).
3. **H_change_blind — CHANGE BLINDNESS is the headline.** A change occurring
   DURING the blink is missed until data diverges (the confabulated continuation
   stands); a change in a VISIBLE frame is signalled at once. **Statistic:**
   latency = `diverged_at − change_tick`; change-in-blink latency `> 0`,
   change-in-visible latency `== 0`. **Two-sided:** if the in-blink change were
   caught immediately, there is no change blindness (the whole point is that
   grounding *reproduces* it — fail).
4. **H_correction — the perceptible JUMP (replaces "refuses a long gap").** It
   does NOT refuse a long gap — it fills (guesses) anyway, and the correction on
   data return GROWS with how far it guessed blind (short gap → imperceptible;
   long gap / big change → the perceptible startle), while confidence DECAYS with
   the gap. **Statistic:** for a change during the blink at gaps {1,2,3,5}, the
   blink is ALWAYS filled, `correction` is monotone non-decreasing and strictly
   larger at the longest gap, `confidence` is monotone decreasing; AND under
   consistent motion (no change) `correction==0` at every gap (invisible).
   **Two-sided:** if a long gap were refused (not filled) ⇒ the old silence model,
   falsified by deprivation (fail); if correction did not grow with the gap ⇒ the
   guess is not a real extrapolation (fail).
5. **H_unconstrained — WITHOUT a generator it STILL confabulates, unconstrained
   (replaces "refuses / holds open").** If the pre-blink prefix has no single
   transition generator (accelerating / shuffled — the TIME rung's `time_none`
   case), the blink is STILL filled (the freeze default), but UNCONSTRAINED
   (`constrained==0`, `confidence==0`) — the seed of hallucination, not silence.
   **Statistic (the FLOOR, the gate):** an accelerating prefix → filled +
   `constrained==0`; and over **400** shuffled prefixes (seeds **31100–31499**),
   **every one STILL fills** AND **0** non-orbit shuffles are FALSELY marked
   `constrained==1` (a shuffle that lands MONOTONIC is a genuine orbit under
   `G`/`G⁻¹` and MAY be honestly constrained, exactly as the TIME rung classified
   its reversals). **Two-sided:** a held-open / silent blink ⇒ the refuted silence
   model (fail); a non-orbit shuffle marked constrained ⇒ the mechanism
   over-claims grounding on noise (fail).

Plus **H_offday (§9):** flag OFF ⇒ the blink sequence is inert (no fill). And
**scaling:** the bridge is LOCAL — fitted exponent in cell count `≤ 1.3` (NOT the
O(N²) global-match drive the assembled-eye scaling condemned).

## Positive controls (§1 clauses 4/5, this arc has caught 18 lying instruments)

- **the blink is REAL** — during the blink the raw sensor returns NO data (the
  input frame IS empty); verify the bridge fills a genuine hole.
- **the bridge is GROUNDING, not a freeze** — change the pre-blink motion ⇒ the
  bridge changes (tracks `M`); the bridge differs from the persistence baseline on
  every bridged tick.
- **the bridge is GROUNDING, not a stored default** — zero/no-consistent motion ⇒
  the guess is UNCONSTRAINED (`constrained==0`, `confidence==0`): it still fills,
  but grounding did not pin it (the honest low-confidence guess).

## Statistic, n, seeds, decision rule

- **n:** the four claims H_grounding_constrains / H_invisible / H_change_blind /
  H_correction, H_offday, the scaling fit and the two positive controls are
  **DETERMINISTIC** (constructed stimuli, no RNG) — no seed consumed, exactly as
  the SHAPE-SELFSEE rung recorded for its deterministic arms. The ONLY RNG arm is
  H_unconstrained's floor: **n = 400** shuffles, fixed in advance. The floor is a
  ZERO-EVENT gate on FALSE-CONSTRAINT (P(a random 6-frame permutation is monotonic)
  = 2/720 ≈ 0.0028; a monotonic draw is a genuine orbit and MAY be honestly
  constrained, verified, not counted false), so any single falsely-constrained
  non-orbit fails it — n=400 gives a tight upper bound (Rule-of-three 95% ≤ 0.75%
  if 0 observed).
- **Seeds:** confirmatory floor **31100–31499** (declared here, never used for
  anything). Mechanism bring-up / this pre-reg's pilot used burned seed 0 and
  deterministic constructions (`scripts/blink_pilot.py`) — burns nothing new.
- **Decision rule:** the headline ("the blink CONFABULATES a temporal hole and
  grounding CONSTRAINS the guess — invisible & motion-continuing under consistent
  motion, change-blind, revisable with a correction that grows with the gap, and
  unconstrained-but-not-silent without a generator, O(≤N)") holds iff ALL five
  claims + H_offday + scaling + the blink-is-real control PASS. **A null on any
  claim is a RESULT, reported not rescued** (§7): a bridge that can only freeze
  (persistence, ignoring `M`) or that goes silent when ungrounded is a clean
  negative about what grounding-in-time can express.
- **Exactly these tests** (`scripts/blink_measure.py`); the gate is
  `tests/test_blink_bridge_migrated.py`. No sweeps; a further attempt needs a NEW
  pre-registration with a new mechanism-level hypothesis (§3 rule 6).

## My prediction, with provisos (§3 rule 7)

**Prediction: all five PASS, bounded to the integer-velocity in-frame motion
class.** The constrained guess is `TimeInfer`'s already-load-bearing continuation,
so under a consistent integer-velocity orbit it MUST equal the ground-truth frame
— H_grounding_constrains and H_invisible follow directly, and I expect
`bridged==truth` exactly (integer lattice, exact equality) with `constrained==1`.
Change blindness is the headline: it falls out because the confabulated
continuation continues the OLD generator regardless of what the (unseen) world
did, so a change inside the blink is invisible until the resumed observation
diverges — I predict latency == the blink duration remaining. H_correction: the
guess keeps moving while a stopped object does not, so their displacement (hence
the symmetric-difference correction) grows with the gap until the footprints fully
separate and it saturates — I predict monotone-up-then-saturate, and confidence
`= support/(support+gap)` monotone down. H_unconstrained: an ungrounded prefix
falls back to the freeze default at `confidence 0` — it STILL fills. The
confidence form (`confirm_run/(confirm_run+gap)`) is a design choice; I claim only
that it FALLS OUT of the confirmed-transition support and imports no constant, not
that this is the unique right law. **Provisos that would break, and what each
would teach:** (a) if `bridged != truth` under clean integer motion, the
continuation composition is wrong (an `apply_generator_k` exponent bug); (b) if a
non-monotonic shuffle reads `constrained==1`, `TimeInfer`'s orbit test is looser
than believed at short prefixes; (c) if the change-in-visible control shows
latency > 0, my "visible = immediate" framing conflates the resume boundary with a
plainly-visible frame (place the visible change well after resume); (d) if
`correction` does not grow with the gap, the footprint saturates before the
smallest gap and I must use a taller stimulus or a centroid metric. **Bound stated
in advance:** a SINGLE blink block, one generator, integer velocity; the
unconstrained guess degrades to the FREEZE default (one of the creator's "freeze /
drift / flicker" — a noise-seeded hallucination is NOT modelled); multiple blink
blocks, sub-integer/continuous motion, and the full center-surround event pipeline
(a moving blob under adaptation is not an exact-integer-rigid translation) are NOT
claimed — the retinal probe reaches only the active-cell/change level, exactly as
the TIME/DEPTH rungs bounded theirs.
