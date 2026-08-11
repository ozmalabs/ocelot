# GEN-MINT — results

**The sd loop can now MINT a new generator from an orbit — the arc's negative
is OVERTURNED, bounded to the integer-linear class.** Pre-registration
`VISION_GENMINT_PREREG.md` committed at `3b014a82` BEFORE the confirmatory run.
Engine `8bf03905bbf3` @ this worktree (OWN build — the rung adds Rust; provenance
gate 7/7). Seed block **25000–25999**; only **25000–25399** consumed (the floor
window). **12000–24999 untouched.**

## The one operation, and it now exists

`DimInfer` (`shape_decode.rs::eval_dim_infer`) SELECTS a transform from a HELD
`DimensionGenerator` codebook and — proven by reading and by the pilot — cannot
mint a new one: `apply_generator_once` is a closed `match kind` over five
hardcoded Rust functions, and `coord_dims`/`params`/`modulus` only parameterize
them. The delta is one new branch at the exact gap where `DimInfer` exhausts the
held codebook without a match:

- **`apply_linear_once`** (Rust) — a `kind:"linear"` generator whose transform
  is a `matrix` carried as **graph data**. The ONE new dispatch arm; it makes
  the whole integer general-linear group `GL(2,ℤ)` expressible as data.
- **`GenInfer`** (Rust Term) — DimInfer-native generate-and-test over the
  PARAMETERIZED family of integer 2×2 maps within a data-derived bound, applied
  via the SAME `apply_linear_once` a mint uses and verified via the SAME
  `build_candidate` check DimInfer runs.
- **`sd_gen_check` / `sd_mint_generator`** (seed rules, flag-gated) — on a
  compressing inference, mint `DimensionGenerator{kind:"linear", matrix}` and
  bump `codebook_epoch`; `sd_redecode` re-arms and the orbit re-decodes THROUGH
  the minted generator.

## Was the target representable? Two findings, in order (the coordinator's ask)

1. **On the UNEXTENDED engine the representation IS the wall** (pilot,
   `scripts/genmint_pilot.py`, engine `559d7f38`): minting a generator AS GRAPH
   DATA is inert — a `DimensionGenerator{kind:"linear", params:[1,1,0,1]}` node
   leaves `DimInfer` explained=False and the shear still mints a flat quantum,
   because there is no Rust arm backing a data-defined transform. **The
   transform was code, not data.** This is the mechanism of the arc's negative,
   measured.
2. **The delta removes exactly that wall** by making the transform data
   (`apply_linear_once` reads the `matrix`). Proven positively:
   `test_data_defined_linear_generator_now_drives_a_decode` — a matrix carried
   purely as graph data now explains the orbit.

## The discrimination — ONE MDL principle, measured across all arms

*Post-prereg reframe (creator): the discriminator is DESCRIPTION LENGTH, not
signal-vs-noise. "Noise doesn't exist — only signals you haven't grounded." The
SAME measured data is reported here under MDL; this sharpens the interpretation,
it does not rescue any failure (§5). Mint a generator IFF it COMPRESSES.*

| arm | result | reading |
|---|---|---|
| **H_discovery** (multi-held-out, §13.1) | shearA→`(1,0,1,1)`, shearB→`(1,1,0,1)`, unimodular→`(2,1,1,1)`; **3/3 correct, all DIFFERENT**; each collapses (`recognized_transformed`, 0 quanta) | the FROZEN seed grounds different orbits to different minimal generators — general, not privileged |
| **H_compression** (MDL headline) | 6-member orbit: WITHOUT 6 quanta; WITH **1 generator + 0 quanta** (6/6 recognized). **MDL 24→12, ratio 2.0×** | the minted generator PAYS for itself — it fell out (compresses), it was not put in |
| **H_floor** (the gate) | **0 / 400** ungrounded presentations (seeds 25000–25399) minted a generator; each grounded at enumeration (1 quantum) | honest floor: "no generator shorter than enumeration found (at these seeds, this window)" — provisional, NOT "noise refused" |
| **H_occam** | held rotation90 orbit → SELECTED upstream (`recognized_transformed`, 0 linear generators) | already-compressed input is not re-minted |
| **H_downstream** (§1 clause 5) | generator minted from member 1 recognizes `M²(base)` (unused for minting); ON=`recognized_transformed` vs OFF=`minted` | the mint MOVES a subsequent decode — load-bearing, not decoration |
| **H_nonlinear** | quadratic warp `c→c+r²` → grounds at enumeration (0 generators) | outside the seeded linear generality; PROVISIONAL — a nonlinear seed might compress it, door open |

Every constant: the entry bound `B` = max normalized coordinate over base∪goal
(**read from the data**); the mint condition = **exact zero-residual whole-orbit
fit** (structural, `transforms.len()==dims_needed.len()`, the sd loop's own
`!= 0` discipline) — **no coherence float, no tuned threshold.** The relocated
§1.1 gate ("no minted generator FAILS to compress") passes: every minted
generator has MDL_with < MDL_without; 0/400 non-paying mints.

## Seed size — the minimality axis (genomic bottleneck)

**Seed = 4 integer parameters** (the 2×2 matrix), uniform across shapes. This is
minimally general, NOT a rich container:

- it **cannot express a HELD generator** (the modular/cycle4 wrap is nonlinear),
  nor the quadratic warp, nor an arbitrary lattice permutation — so it is
  demonstrably not a universal solver that would trivially contain every target;
- **starvation threshold, measured:** the 5-atom NAMED codebook (the prior seed)
  cannot reach a shear (pilot: quantum) — discovery is OFF below the linear
  family; the 4-parameter linear family discovers shearA/shearB/unimodular —
  discovery is ON. The threshold sits between "finite named atoms" and "a
  4-parameter general family whose specific member is IDENTIFIED from the orbit."

**Achieved: discovery from a MINIMAL general seed, not a rich one** — the
strong form.

## Speed (altricial guard) — descriptive, never a gate

Identification is **one-shot** (presentation 1) because each orbit member is an
exact integer-linear image of the held base, so exact enumerate-and-test
identifies the map immediately. This is a descriptive fact, not a virtue; the
floor gate was verified at the **longest** window (n=400), never a short one.
The biologically-faithful SLOW path — accumulating a map across many partial /
symmetric presentations — is a noted refinement (see scope).

## §9 byte-identity (flag OFF, default)

The machinery is gated on the graph-data agent flag `gen_infer_enabled` (absent
⇒ OFF), like `bcm=0`/`oja=0`. With `data/` symlinked:

- sd orbit law `{2:1,3:2,4:2,6:2,12:4}` **unmoved**; scrambled floor mints every
  time — `test_sdloop_vision_migrated.py` **15/15**.
- `test_dimension_inference_migrated.py`, `test_transform_decode_migrated.py`,
  `test_composer_driver_migrated.py` **32/32**.
- provenance gate **7/7**.
- vision bench **200 passed / 0 failed** (`scripts/rung7_vision_bench.sh`) with
  `data/` symlinked (§10.2: 190/10 without `data/`).

The `GenInfer` Rust Term is compiled in but fires no rule at the defaults.

## Does this OVERTURN the sd loop's negative? — and how strong is the evidence

**Yes — bounded to the integer-linear class.** The negative was "the loop
composes what it holds; it does not discover what it lacks." With the GenInfer
delta the loop DOES mint a general-linear generator it did not hold (a shear),
from the orbit, and re-decodes to collapse it — passing the harshest control
available: the FROZEN, MINIMAL (4-parameter) seed grounds THREE different
held-out orbits to three different correct generators, a genuine nonlinear warp
and 400 ungrounded signals ground at enumeration (0 non-paying mints), and the
mint is load-bearing (moves a later decode) and compresses (MDL 2.0×).

**The weight the evidence bears, stated honestly:**

- It overturns the negative **for the class the seed can represent** (integer
  general-linear maps). It is NOT a universal transformation discoverer: a
  nonlinear generator (the modular wrap, the quadratic warp) is still not
  discoverable — correctly refused to enumeration, not hallucinated. So the
  claim is "the discovery OPERATION exists and discriminates," bounded, not "the
  substrate can discover any transformation."
- **The transform the minter FAILS on** (the required real "could this produce
  the opposite?" answer): any nonlinear map — measured on the quadratic warp
  (→ enumeration) and true of the held modular wrap. Recovery is real ONLY
  inside the seeded linear generality; that boundedness is what keeps it from
  being a universal container, and is exactly why the floor holds.
- **Provisos from the prereg and which broke:** none broke. (1) the data-bound
  recovered every declared target; (2) the asymmetric base avoided
  under-determination (each orbit gave a unique Occam-minimal map); (3) noise
  never minted. The one honest scope not exercised: a SYMMETRIC base where one
  member under-determines the map — the one-shot minter would take the
  Occam-minimal, and disambiguating needs a multi-member window (the slow
  biological path), noted not built.

## Scope (§8) — what is NOT shown

Synthetic orbits, a general integer-linear seed **chosen by me**. This tests
only that the discovery OPERATION exists at the sd-loop gap — NOT that
waves+cortex is the right seed for biological orientation (separate downstream
question; the eye already carries oriented-front waves, so the orbit is present
in vision). Non-90° rotation is cross-frame (non-integer, this tree's
frame/continuum invariant), so the discoverable held-out targets on the integer
lattice are shears and other `SL(2,ℤ)` maps. Dedup is one linear generator per
boot (matrix-keyed multi-generator coexistence, and multi-member accumulation
for symmetric/partial orbits, are noted refinements). "Grounds at enumeration"
is always provisional — a richer seed or longer window may compress what this
one does not, and that would be a finding, not a contradiction.
