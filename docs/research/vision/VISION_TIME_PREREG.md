# TIME AS AN INFERRED DIMENSION — pre-registration (§3)

**Committed BEFORE the confirmatory run.** Engine is this worktree's OWN build
(the rung adds Rust: the `translate` generator kind + the `TimeInfer` Term);
provenance pasted into the OUTCOME. Confirmatory RNG seeds **26100–26999**
(the floor shuffles); **26000–26099 are exploratory** (already burned by the
bring-up pilots `scripts/time_pilot.py`/`time_pilot2.py` and the seed
end-to-end check). **12000–25999 untouched.**

## The operation

Infer TIME as a latent dimension from a MOTION orbit — the SAME operation as
the spatial generator discovery (`GenInfer`), one level up, applied to a
temporal sequence. A pattern moving over ticks produces a SEQUENCE; that
sequence is an ORBIT under a transition generator `G` carrying
`frame(t) → frame(t+1)`; the exponent `k` indexing `G⁰,G¹,G²…` **IS** the
inferred time axis — a minted `latent:time` `LatentDimension`, exactly as a
spatial dimension is minted from a spatial orbit. Time lives in
`Hom(frame,frame)`, never in a frame's coordinates (the tree's frame/continuum
invariant): a single tick's state is the present (integer lattice, no stored
`t`); time is the inferred parameter of the generator between frames.

**Mechanism (graph-native — the decision is Rust/seed, never a Python `if`):**
- Rust `TimeInfer` Term (`shape_decode::eval_time_infer`): given the ordered
  frame sequence, infer `G` from the FIRST consecutive pair (affine translate
  preferred, else integer 2×2 linear — the SAME enumerate-and-test as
  `GenInfer`) and VERIFY by EXACT equality that `G` carries EVERY remaining
  consecutive pair. Reports `explained`/`kind`/`offset`/`matrix`/`window`/
  `predicted` (the UNSEEN `G^K(f0)`).
- Rust `translate` generator kind (`apply_translate_once`, `offset` as graph
  data): the affine extension — the one integer-translation the linear class
  cannot express (measured: translation is rung-1, group-closed — see below).
- Seed `time_axis.json` (flag `time_infer_enabled`, absent ⇒ OFF, §9):
  `time_infer_mint` mints `LatentDimension{name:'latent:time', …}` + records
  `obs.predicted` on an explained orbit; `time_infer_floor` grounds a
  non-orbit at enumeration (`status='time_none'`).

## The measured wrinkle this rung establishes first (pilot, exploratory)

**Is a translation orbit in the CURRENT linear class? — NO, measured.** A pure
translation is handled at RUNG 1 as a uniform per-frame shift (identical ON/OFF,
no generator, no exponent, no dimension), and it is worse than merely affine:
translation is **GROUP-CLOSED** — any two frames of a constant-velocity orbit
are mutual translates PAIRWISE, so pairwise-explainability is VACUOUS. The
discriminator for translation is therefore **CONSTANT VELOCITY across the whole
orbit**, not pairwise-explainability. This needs (a) the affine `translate`
generator kind AND (b) an orbit-level (not per-frame) inference — both built.
The linear-transition motions (rotate/scale/shear per tick) ARE in the class
already (their exponent `k` is minted as a `LatentDimension` by the existing sd
loop, zero new decode code).

## Confirmatory arms, statistics, decision rules, predictions

Every arm is DETERMINISTIC except **H_floor** (random shuffles, seeds
26100–26999). Primary readout is the **minted `latent:time` dimension** and its
generator descriptor — a codebook mint, not a tuning curve.

### H_time — IDEAL (§1 clause 2)
- **Stat:** an ORDERED constant-velocity orbit (`translate(2,0)`, K=7 frames)
  mints exactly one `latent:time` dimension with `kind='translate'`,
  `offset=(2,0)`, `window=7`, and it COMPRESSES (MDL: frames-stored `K·ncell`
  vs generator `f0 + offset + window`).
- **Decision:** PASS iff minted, descriptor correct, MDL_with < MDL_without.
- **Prediction:** PASS. **Proviso:** if the orbit re-normalizes per frame the
  translate offset would vanish — it does NOT (translate does not normalize).

### H_multimotion — §13.1 non-privilege
- **Stat:** the FROZEN `TimeInfer` infers the correct DIFFERENT generator for
  5 distinct motions: `translate(2,0)`, `translate(1,3)`, `shear[1,0,1,1]`,
  `rotate90[0,-1,1,0]`, `scale2[2,0,0,2]`.
- **Decision:** PASS iff all 5 `explained` AND all 5 descriptors correct AND
  the 5 descriptors are DISTINCT (no forced signature — a mechanism that always
  emits the same generator regardless of input is falsified).
- **Prediction:** PASS, 5 distinct correct generators. **Proviso:** rotate90 is
  ALSO a held generator — its exponent path would still work with no `translate`
  build, which is the point: linear transitions were already in-class.

### H_floor — THE GATE (§1 clause 1, LONGEST window)
- **Stat:** for n random shuffles (seeds 26100+) of a K=8 shear orbit AND a K=8
  translate orbit, count how many mint a `latent:time` dimension. Also the
  deterministic accelerating sequence.
- **n FIXED IN ADVANCE:** n=200 per orbit-type (400 shuffles), at the LONGEST
  window K=8 (a forced minter shows here — §1.1 in the time domain).
- **Decision:** PASS iff spurious mints = 0 (report as "no transition generator
  shorter than enumeration found at these seeds, this window" — provisional,
  NOT "shuffle refused"). A mint that IS an exact monotone reversal/rearrangement
  is a GENUINE orbit (time's arrow reversed), reported as such, not a floor
  failure.
- **Prediction:** 0/400 spurious. **Proviso:** P(random K=8 perm is monotone)
  = 2/8! ≈ 5×10⁻⁵, so ~0 expected; if one appears it will be a reversal
  (legitimate), which I will check and report explicitly.

### H_varying — the specifically-TEMPORAL control
- **Stat:** an ACCELERATING translate sequence (steps 1,2,3,…) — frames are
  pairwise mutual-translates but velocity is NOT constant — grounds `time_none`.
- **Decision:** PASS iff NO `latent:time` minted. **Prediction:** PASS. This is
  the discrimination pairwise-explainability cannot make: it isolates that the
  axis requires a CONSISTENT transition, not merely mutually-reachable frames.

### H_downstream — LOAD-BEARING (§1 clause 5, §13.2)
- **Stat:** the minted axis predicts an UNSEEN later frame `G^K(f0)`; compare to
  a WITHHELD actual (`translate(2,0)`, shown f0..f6, withhold f7=base+(14,0)).
  Toggle the mechanism: `D = |on − off|` on (mint-count, predicted-present).
- **Decision:** PASS iff ON predicts f7 EXACTLY AND mints the dimension, OFF does
  neither, and `D > 0`. **Prediction:** PASS, `predicted==withheld`, D>0. A
  minted-but-unused axis (D=0) would be FM-0 decoration — STOP, burn no seed.

### H_offday — §9 byte-identity
- **Stat:** flag OFF ⇒ ordered orbit does NOT mint (inert, `status` unchanged);
  the sd orbit law `{2:1,3:2,4:2,6:2,12:4}` unmoved; genmint 6 H-arms PASS;
  gen_infer gate 7/7; provenance 7/7; bench 200/0 with `data/`.
- **Decision:** PASS iff all committed oracles reproduce. **Prediction:** PASS
  (translate is inert without a translate generator; TimeInfer fires no rule at
  the defaults; both match only `status=='motion_seq'`, which the decode ladder
  never produces).

## What each failure means
- H_time fails ⇒ the orbit→dimension mint is broken; time is not inferred; STOP.
- H_multimotion not-all-distinct ⇒ forced signature (§13.1); the mechanism is
  privileging the motion, not inferring it; retract.
- H_floor > 0 (non-reversal) ⇒ a forced minter hallucinating time from noise
  (§1.1); the operation over-reaches; report as a negative about its floor.
- H_varying mints ⇒ the discriminator is pairwise-explainability not
  constant-velocity; the "shuffled has no time" control is confounded; retract
  the translation claim.
- H_downstream D=0 ⇒ the axis is decoration (FM-0); STOP, burn no seed.
- H_offday moves ⇒ §9 violated; the build perturbed a committed result; revert.

## Global prediction, stated in advance
Time BECOMES an inferred dimension in this substrate, **bounded to the motion
class {integer-linear transition ∪ constant integer-velocity translation}** —
the same integer/in-frame boundary the gen-mint rung proved for space. Rotate/
scale/shear were already in-class (exponent k on a `LatentDimension`, zero new
code); translation needed exactly ONE affine extension (the `translate` kind)
PLUS the orbit-level constant-velocity inference (because translation is
group-closed). Shuffled and varying-velocity sequences ground at enumeration at
the longest window. The minted axis predicts an unseen frame. Non-constant /
non-integer / cross-frame motion (real-angle rotation, acceleration) is OUT —
correctly refused, not hallucinated.
