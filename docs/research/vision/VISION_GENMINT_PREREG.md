# GEN-MINT — pre-registration

*The residual of the whole sd-loop arc, stated as one operation: **mint a NEW
generator from an orbit — DISCOVER a transformation, not select a held one.***
Committed BEFORE the confirmatory noise run (§3). Seed block **25000–25999**
declared; **12000–24999 untouched.**

## 0. The operation and where it sits

The five-rung analysis established both learning mechanisms fail at exactly one
operation: Oja/Hebbian fits second-order statistics (no orientation); the sd
loop **composes what it holds and does not discover what it lacks** —
`DimInfer` (`shape_decode.rs::eval_dim_infer`) SELECTS from a HELD
`DimensionGenerator` codebook (rotation90 / reflection_r / reflection_c /
scale2 / modular=cycle4) and never mints a new generator. Verified by reading:
`apply_generator_once` is a closed `match kind` over five hardcoded Rust
functions; `coord_dims`/`params`/`modulus` only PARAMETERIZE them — graph data
cannot define a new transform.

**The delta:** at the exact point `sd_infer_dimension` fails
(`dim_checked==1, dim_explained!=1`) and the residual today falls through to
`sd_mint_quantum` (a flat point), INFER the generator that relates the orbit,
mint it as a new `DimensionGenerator{kind:"linear", matrix:…}` (graph data),
grow the codebook, and re-decode — collapsing the orbit to one signature + one
generator.

## 1. The seed (representation + inference) — and its SIZE

- **Representation:** a general integer **2×2 linear map** on the coordinate
  lattice, `kind:"linear"`, the 4-entry `matrix` carried as **graph data**;
  applied by the new Rust `apply_linear_once` (the ONE new dispatch arm — every
  discovered map rides in as data, none as code). Class = **`GL(2,ℤ)` within a
  data-derived bound** — rotation, reflection, shear, scale, glide-linear-part
  alike, uniform across shapes.
- **Inference (`GenInfer` Term):** DimInfer-native generate-and-test over the
  PARAMETERIZED family (every integer 2×2 matrix with entries in `[-B,B]`),
  applied via the SAME `apply_linear_once` a mint uses and verified via the
  SAME `build_candidate` check DimInfer runs. The identity is excluded. Occam:
  fewest residual dims, then smallest `Σ|entry|`, then lexicographic.
- **SEED SIZE (reported axis, per the genomic-bottleneck argument): 4 integer
  parameters.** This is *minimally general*, NOT a rich container: it **cannot
  express one of the HELD generators** (the modular/cycle4 wrap is nonlinear),
  nor any nonlinear warp, nor an arbitrary lattice permutation. A rich seed
  that trivially contains every target would make "it discovered X" weak; a
  4-parameter linear seed must **identify** which map the orbit implies.
- **Bound `B` (§13):** the maximum absolute normalized coordinate over base ∪
  goal — **read from the data** (a map carrying the base's own lattice steps
  into the goal cannot place a coordinate outside the extent it produces). Not
  a knob; a target needing entries beyond the observed extent is an
  identifiability scope limit (§8), a false-NEGATIVE (safe) direction.
- **Orbit/novelty threshold (§13): STRUCTURAL, zero constants** — a success is
  `build_candidate.transforms.len() == dims_needed.len()` (an EXACT,
  zero-residual whole-orbit fit), the same `!= 0` structural condition the sd
  mint already uses. There is no coherence float to tune.

## 2. Off by default (§9)

Gated on the graph-data agent flag `gen_infer_enabled` (absent ⇒ OFF), exactly
like `bcm=0`/`oja=0`. All rules ship in `seeds/shape_decode_loop.json` v1.7.0 in
ONE tier (`sd_gen_check_mark` OFF-path, `sd_gen_check`/`sd_mint_generator`
ON-path); `sd_mint_quantum`/`sd_dedup_existing` gain `gen_checked==1 &&
gen_explained!=1` (the exact mirror of the dim-rung guards, satisfied
byte-identically when OFF via the Term-free mark). The `GenInfer` Rust Term is
compiled in but fires no rule by default.

## 3. Hypotheses, statistics, decision rule

- **H_discovery (primary, the §13.1 multi-held-out control):** the FROZEN
  machinery mints the **correct, DIFFERENT** generator for each of THREE
  held-out orbits — shearA `[1,0,1,1]`, shearB `[1,1,0,1]`, unimodular
  `[2,1,1,1]` (det 1; none in the held D4/scale/cycle closure) — each collapsing
  (`status=recognized_transformed`, 0 quanta, the correct linear generator
  minted).
- **H_floor (THE GATE, §1.1 + the altricial long-window guard):** provably-
  structureless value-noise NEVER mints a generator, at the LONGEST window.
  **n = 400** distinct random colourings (seeds **25000–25399**) of the base's
  own coordinates (so no coherent value-substitution exists and only the
  excluded identity fixes the coords ⇒ no linear explanation can exist).
  Statistic: count of the 400 that mint a linear generator. **Decision:
  MUST be 0/400.** ≥1 ⇒ forced/vacuous (§13.1), the operation is a negative.
- **H_occam:** a HELD transform (rotation90 orbit) is SELECTED upstream
  (recognized via the held generator, gen rule never fires, 0 linear generators
  minted).
- **H_downstream (§1 clause 5):** the generator minted from orbit member 1
  recognizes a DIFFERENT member (`M²(base)`, unused for minting) that WITHOUT
  the mint is a quantum — the mint moves a subsequent decode. `max|on−off|`
  measured, must be non-zero.
- **H_nonlinear (names the transform the minter FAILS on):** a genuine
  NON-linear warp (quadratic `c → c + r²`) is NOT recovered (falls to quantum) —
  the minter's class is exactly the integer-linear group, and it correctly
  refuses structure outside it rather than hallucinating.

**OVERTURN (discovery real, bounded to the linear class)** requires ALL of:
H_discovery 3/3, H_floor 0/400, H_occam, H_downstream. **NEGATIVE** if H_floor
fails (forced), or the same generator is minted regardless of orbit (forced),
or H_discovery cannot identify the map (identifiability limit, failure mode 2).
The representation-wall negative (failure mode 1) is already established by the
pilot (a `kind:"linear"` data-generator is INERT on the unextended engine).

## 4. §9 byte-identity (flag OFF)

sd orbit law `{2:1,3:2,4:2,6:2,12:4}` unmoved; scrambled floor mints every
time; `tests/test_dimension_inference_migrated.py`,
`test_transform_decode_migrated.py`, `test_composer_driver_migrated.py`,
`test_sdloop_vision_migrated.py`, `test_engine_provenance_migrated.py` green;
vision bench 200/0 with `data/` (190/10 without). Engine hash + source verdict
on every number.

## 5. Prediction (mine, in advance — §3.7)

I predict **OVERTURN, bounded to the integer-linear class.** Provisos, each a
real break if it fires:
1. The data-derived `B` could miss a general map whose entries exceed the
   observed extent — a false NEGATIVE (safe). If a declared held-out target is
   NOT recovered, this proviso broke and the bound is the wall.
2. Identification is **one-shot** (exact enumerate-and-test on an exactly-
   presented member). A SYMMETRIC base can under-determine the map (several fit,
   Occam-minimal chosen); I predict my asymmetric L-tetromino base avoids this.
   A wrong/ambiguous minted matrix ⇒ this proviso broke (identifiability, and
   the biologically-faithful fix is a multi-member window — noted, not built).
3. I predict noise **NEVER** mints because value-incoherent input has no linear
   explanation *structurally* (not statistically) — so it must hold at ANY
   window, not just n=400.

**Could this produce the opposite?** Yes: if the linear seed were a universal
container it would mint for noise (H_floor) — it is not, and value-noise has no
linear map. The transform it **fails on** is any nonlinear generator
(H_nonlinear: the quadratic warp, and the held modular wrap itself) — recovery
is real only inside the seeded linear generality, which is the correct bounded
scope, not a universal solver.

## 6. Scope (§8)

Synthetic orbits, general integer-linear seed **chosen by me**. This tests only
whether the discovery OPERATION exists at the sd-loop gap — NOT that waves+cortex
is the right seed for biological orientation (a separate downstream question;
the eye already carries oriented-front waves, so the orbit is present in vision).
Non-90° rotation is **cross-frame** (non-integer per this tree's frame/continuum
invariant), so on the integer lattice the discoverable general-linear held-out
targets are shears and other `SL(2,ℤ)` maps, which is what the multi-held-out
set uses.
