# TIME AS AN INFERRED DIMENSION — results

**Time is now an INFERRED DIMENSION in this substrate, bounded to the motion
class {integer-linear transition ∪ constant integer-velocity translation}.**
The exponent `k` of the transition generator `G` carrying `frame(t)→frame(t+1)`
IS the time axis — a minted `latent:time` `LatentDimension`, the SAME operation
as spatial generator discovery (`GenInfer`), one level up, on a temporal orbit.
Time and space are now the same KIND of thing: inferred latent dimensions
indexing discovered generators.

Pre-registration `VISION_TIME_PREREG.md` committed at **`848eae0b`** BEFORE the
confirmatory run. Engine **`2063cf2a44a3`** (this worktree's OWN build — the rung
adds Rust). Seed block **26000–26999**; confirmatory floor consumed **26100–26499**
(400 shuffles), **26000–26099 + 26500 exploratory** (pilots/retina),
**26501–26999 CLEAN**. **12000–25999 untouched.**

## The two findings, in order (the coordinator's first ask)

**1. Is a translation orbit in the CURRENT linear class? — NO, measured
(`scripts/time_pilot.py`).** A pure translation is recognized at RUNG 1 as a
uniform per-frame shift (byte-identical ON/OFF; no generator, no exponent, no
`dim_infer`), and it is worse than merely affine: translation is
**GROUP-CLOSED** — any two frames of a constant-velocity orbit are mutual
translates PAIRWISE, so "is this pair explainable?" is vacuously yes for ANY
ordering. Even a HELD `{translate, offset}` generator is pre-empted by rung 1
per frame (measured). **So the discriminator for translation is CONSTANT
VELOCITY across the whole orbit — an orbit-level property, not a per-frame
one.** The linear-transition motions (rotate/scale/shear per tick) were ALREADY
in-class: the existing sd loop mints a `LatentDimension` whose coordinate is the
exponent `k` (measured: a shear orbit mints `latent:genlin_base_L` at k=1,2,3,4;
rotation90 at k=2), zero new decode code.

**2. The minimal extension that removes exactly that wall.** Two Rust deltas,
both the same shape as `apply_linear_once`:
- **`apply_translate_once`** — a `{kind:"translate", offset}` generator whose
  transform is an integer OFFSET carried as GRAPH DATA (`v→v+offset`, no wrap,
  no origin-normalization). The ONE new dispatch arm; its `k`-th power is
  `+k·δ`, so a translate generator's exponent is a displacement quantum along
  `latent:time`, uniform with the linear generators.
- **`TimeInfer`** (Term) — `GenInfer` one level up: infer `G` from the first
  consecutive pair (translate preferred, else the SAME integer-2×2
  enumerate-and-test), then VERIFY by EXACT equality that `G` carries EVERY
  remaining pair. A shuffled / varying-velocity sequence is not an orbit and
  grounds unexplained.
- seed `time_axis.json` (flag `time_infer_enabled`, OFF by default, §9):
  `time_infer_mint` mints `latent:time` + records the downstream prediction;
  `time_infer_floor` grounds a non-orbit at enumeration.

## Confirmatory arms (`scripts/time_measure.py`) — 6/6 PASS, every prediction held

| arm | result | reading |
|---|---|---|
| **H_time** (ideal, §1.2) | ordered `translate(2,0)` K=7 → `latent:time{kind:translate, offset:(2,0), window:7}`; **MDL 28→7, 4.0×** | an ordered orbit mints a time dimension AND compresses (one generator + f0 replace K frames) |
| **H_multimotion** (§13.1) | 5 motions → **5 DIFFERENT correct generators**: translate(2,0)/(1,3), shear(1,0,1,1), rotate90(0,-1,1,0), scale2(2,0,0,2); frozen machinery | non-privilege: the mechanism INFERS the motion, it does not emit a forced signature |
| **H_floor** (the gate, LONGEST window) | **0 / 400** random shuffles (seeds 26100–26499, K=8) minted a time dimension; 0 legitimate reversals arose | the honest MDL floor: no transition generator shorter than enumeration found (provisional) — a forced minter would fire here |
| **H_varying** (temporal control) | accelerating translate (steps 1,2,3,…) → **`time_none`** | the specifically-temporal discrimination pairwise-explainability CANNOT make: frames are pairwise mutual-translates yet NOT a constant-velocity orbit |
| **H_downstream** (§1 clause 5 / §13.2) | minted axis predicts the UNSEEN `G⁷(f0)` = withheld f7 EXACTLY; **D_mint=1, D_pred=1** | load-bearing, NOT decoration — toggling the mechanism moves a downstream attribute |
| **H_offday** (§9) | flag OFF → ordered orbit inert (`status` unchanged, no mint) | default preserves committed behaviour |

## The RETINAL step (`scripts/time_retina_probe.py`) — reached, positive

**A rigidly-translating pattern through the retina IS a motion orbit.** An
L-tromino footprint drifting across a 30×30 retina, read as its per-tick
active-cell set, is inferred by `TimeInfer` for THREE velocities — drift(1,2),
drift(2,0), drift(0,1) — each `explained=True, kind=translate` with the correct
offset, and each predicts the UNSEEN 8th frame exactly; a SHUFFLED retinal
drift grounds at enumeration. **Honest scope:** this is the active-cell/change
level (the pattern's retinal footprint). The full center-surround event
pipeline is NOT an exact integer-rigid translation (a moving blob under
center-surround + adaptation distorts), which the exact-equality orbit test
would ground at enumeration — that integration (a tolerance-carrying transition,
or the ON-event centroid as the motion token) is a SEPARATE rung, named not
built (§11.4).

## §9 byte-identity (flag OFF, default)

- **genmint 6 H-arms PASS** (the sd orbit-law regression oracle path — the
  gen-mint negative-overturn reproduces exactly on this engine).
- migrated gates **88/88**: gen_infer 7/7, sdloop_vision 15/15, dimension/
  transform/composer, ink_decode, provenance 7/7.
- vision bench **200 passed / 0 failed** with `data/` symlinked (§10.2:
  `190/10` without `data/`).
- the new gate `tests/test_time_infer_migrated.py` **6/6**.
- The `translate` kind is inert without a translate generator; `TimeInfer`
  fires no rule at the defaults; both `time_axis` rules match only
  `status=='motion_seq'`, which the decode ladder never produces.

## Every constant falls out (§13)

- the translate offset `δ` and the linear matrix `M` are READ from the data (the
  first consecutive pair), never chosen;
- the time coordinate is the exponent `k` (a count, ℕ — the extensive axis),
  not a stored real `t`;
- the orbit test is EXACT equality (`!= 0` discipline, no tolerance, no
  threshold);
- `max_b` is a data-scaled safety cap on the linear search (bounded by the
  frames' own extent, exactly as GenInfer's bound falls out of the data);
- the floor's `n=400` was fixed in advance (P(random K=8 perm is monotone)
  ≈ 5×10⁻⁵ ⇒ ~0 expected).

## Boundedness, stated plainly

**Time is an INFERRED dimension, bounded to {integer-linear transition ∪
constant integer-velocity translation}** — the same integer/in-frame boundary
the gen-mint rung proved for space (in-frame is integer; the continuum lives in
`Hom(frame,frame)`). What is OUT, correctly refused to enumeration, not
hallucinated: real-angle rotation (cross-frame, non-integer), acceleration
(non-constant transition), and any shuffled/non-orbit sequence. A monotone
REVERSAL is a genuine orbit under `G⁻¹` (time's arrow reversed) and is reported
as such, not a floor failure. **The claim is "the temporal-discovery OPERATION
exists and discriminates," bounded — not "the substrate can infer time from any
motion."**
