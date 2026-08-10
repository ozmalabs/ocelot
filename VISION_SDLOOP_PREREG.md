# PRE-REGISTRATION — the substrate's OWN loop on rung 7's ON/OFF channels

*Written and COMMITTED before any confirmatory run (PROTOCOL §3). Seeds **18000–18999**.*

**Engine at authoring:** `366ce5f14eff` @
`<worktree>/runners/dsl/python/substrate_rs/_native.abi3.so`, source verdict **own**
(this tree's build; I add NO Rust, so it is expected to remain byte-identical to the
two-eyes rung's `366ce5f14eff`).
**Base commit:** `07edb50d`.

---

## 0. The question

Every vision rung so far used a **borrowed learning rule** (Oja, BCM, Butts, GCAL) — a
neural network inside a graph engine. `CLAUDE.md` says the substrate's core loop is
**DYNAMIC QUANTIZATION**: `sd_decode → sd_recognize → sd_transform_decode →
sd_infer_dimension → sd_mint_quantum → sd_redecode`. **Vision has never used it.**

Point that loop at rung 7's decorrelated ON/OFF channels. Does visual structure grow with
**no vision-specific machinery**?

**This is NOT an OSI measurement.** The sd loop's readout is a **codebook**, not a cell
with a tuning curve. Rung 8's blind OSI probe is irrelevant to this rung, which is why
this rung does not wait on it.

## 1. What the ladder itself predicts

The sd ladder is Occam-ordered and mint is the LAST resort:

1. `sd_recognize` — exact literal decode;
2. `sd_transform_decode` (rung 1) — ONE uniform per-dimension delta in the existing basis;
3. `sd_infer_dimension` (rung 2) — a residual coupled across observed dims decoded against
   the held `DimensionGenerator` codebook, **minting a `LatentDimension`**;
4. `sd_mint_quantum` — novelty, only after BOTH rungs looked and BOTH failed.

**The paradigm-native prediction:** oriented structure at many orientations should mint
**FEW quanta + ONE orientation `LatentDimension`** — not one quantum per orientation.
Precedent gate: the **rotated tromino zero-mint** test.

**Primary statistic: MINT-COUNT.** Secondary: whether an orientation `LatentDimension` is
minted; whether rotated input reads as a transform (zero-mint) or as novelty.

## 2. THE TWO FACTS FROM SOURCE THAT SHAPE THIS DESIGN

Read off the Rust before predicting (`runners/dsl/src/shape_decode.rs`):

- **`rotation90` is 90° steps ONLY.** `apply_generator_once` dispatches five string kinds;
  `rotate90_once` is a pure integer index swap about the shape's own bbox
  (`new_r = c0; new_c = max_r0 - r0`), and `params` (`k`) is a **repeat count**, not an
  angle. Reachable set: exactly {90°, 180°, 270°}. **No generator has an angle parameter.**
- **`coord_ints` returns `None` on any `Float` slot** — whole-column. Every generator routes
  through it, so **rung 2 is integer-lattice-only BY DESIGN** (CLAUDE.md: this is CORRECT
  and load-bearing, *not* a gap).

**Therefore a 15°/30°/45° rotation is not a lattice permutation of the coordinate columns,
and NO held generator can express it.** This is structural and provable from source, not a
tuning question.

### 2.1 §13.1 — the forced-architecture trap, and how this design escapes it

`cycle4`'s own seed docstring claims it "collapses a PHASE family (**orientation** / hue /
clock-face)". **I do not use it, and using it would be the `x_OFF = 1 − x_ON` disease.**
`cycle4` steps a **categorical slot** around a ring. To point it at orientation I would have
to encode orientation as its own slot (`["edge", r, c, orientation_index]`) — i.e. **hand
the agent the very structure it was supposed to grow** (§0). The retina does not emit an
orientation label; it emits ON/OFF cell activity in retinal coordinates. So the only honest
encoding leaves orientation as a **rotation of the coordinate lattice**.

**The trap, stated so it cannot be sprung silently:**

| if I ran only... | result | why it is worthless |
|---|---|---|
| multiples of 90° | few mints + a `LatentDimension` | **forced POSITIVE** — `rotation90` is *solely responsible*; the model cannot NOT produce it |
| 15° steps | one mint per orientation | **forced NEGATIVE** — no generator can express it; the model cannot NOT fail |

**Running BOTH arms is what makes this a measurement rather than a tautology with error
bars.** The LATTICE arm doubles as §1-clause-2 (ideal exemplar) and as the §13.1
"could this have produced the opposite result?" proof: **it is the arm in which a positive
is achievable.**

## 3. Encoding — mechanical, and the integer lattice FALLS OUT

Measured on burned pilot seed 18000, before this prereg was written:

- ON channel: **exactly 224 zeros / 32 nonzero**; ON support == stimulus support (32/32).
- OFF channel: **exactly 192 zeros / 64 nonzero** (the surround).
- Nonzeros bounded away from zero: ON min **0.891363**, OFF min **0.008981**. Zeros are
  **exactly** `0.0`.

**So "active" is `!= 0` — the bipolar's own rectification, NOT a threshold I choose.** There
is no continuum near zero to place a cut in. The integer lattice `coord_ints` demands falls
**out** of the retina; it does not go in. (§13.)

Signature per presented stimulus, read off the channels:

```
[["on",  r, c] for cells where on  != 0] +
[["off", r, c] for cells where off != 0]
dim_types = ["pred", "coord:r", "coord:c"]
```

### 3.1 NO `novelty` CONSTANT IS USED — and that is structural, not lucky

`vg_mint_kernel_from_patch`'s scale-aware `|Dot(w,x)| < novelty·|x|` is **rung 6/7 kernel
growth and is NOT on this path.** The sd loop's mint condition is a **structural predicate**,
not a threshold:

```
status=="decoded" AND Count(residual)>0 AND transform_checked==1
AND Not(transform_explained==1) AND dim_checked==1 AND Not(dim_explained==1)
AND Not Exists axis with the same capability_keys
```

**There is no float to tune anywhere in my mint decision.** Mint-count is my primary
statistic AND the sharpest possible conflict of interest — so the honest report is that this
path removes the knob rather than sets it well.

### 3.2 The observation KEY — the one place a fake positive could enter

`sd_dedup_existing` marks an observation `recognized_duplicate` when an axis with the same
`capability_keys` exists. **A key shared across orientations would collapse mint-count to 1
for free — a fake positive with every §1 check passing.** Therefore **every stimulus gets a
UNIQUE key** (`bar_<arm>_<theta>`), so dedup can never manufacture the headline and
mint-count measures only the loop's explanatory power. Declared in advance because it is
exactly the kind of choice that decides a result silently.

## 4. Arms (orientation sets), all on the SAME developed retina

- **LATTICE arm:** θ ∈ {0, 90}, {0, 90, 180, 270} — expressible by `rotation90`.
- **NON-LATTICE arm:** N orientations evenly spanning **[0, 180)** for N ∈ {2, 3, 4, 6, 12}
  ⇒ steps of 90, 60, 45, 30, 15.
  [0,180) exclusive because **a bar at θ and θ+180 are the SAME cell set** — spanning 0..360
  would make half the stimuli exact duplicates (recognized, not minted) and inflate the
  apparent collapse.

Codebook starts **EMPTY**; the loop grows it. A minted axis is promoted to a
`ShapeSignature` + `vision_codebook_epoch` bump **by a seed RULE** (`vq_grow_quantum`,
precedent: `grow_stroke_quantum` + `codebook_epoch`), so `sd_redecode` re-arms and a later
orientation can be recognised as a transform of an earlier one. **Python never decides.**

## 5. PREDICTION, two-sided, stated in advance

**I predict mints(N) ≈ N on the NON-LATTICE arm** (one quantum per orientation) and **NO
orientation `LatentDimension`**, because rung 2 cannot express a non-90° rotation
(§2, from source).

**On the LATTICE arm I predict mints ≈ 1–2 + a `latent:rotation90` LatentDimension IF AND
ONLY IF the retina's response to a 90°-rotated bar is an EXACT lattice rotation of its
response to the bar.** I predict it **is not exact** (surround asymmetry + rasterization),
so I expect the LATTICE arm to mint MORE than the ideal 1 — i.e. **I predict the loop
underperforms even its own best case.**

### 5.1 Provisos (§3.7) — what breaks this, and what each break teaches

1. **Lattice inexactness.** If the developed retina's rotated response is not an exact
   lattice rotation, even 90° mints ⇒ the loop is worse than predicted, and the cause is the
   *retina's* asymmetry, not the ladder's.
2. **Coverage by fragments.** `ShapeDecode` composes up to `max_steps=8` parts; a 45° bar
   might be *partially covered* by pieces of earlier bars, giving mints < N with **no
   dimension at all**. That is fragment-coverage, NOT orientation understanding. **I must
   report plan length / `covered_by` and count `LatentDimension`s SEPARATELY from
   mint-count** — otherwise a low mint-count reads as a false positive.
3. **Rung 1 may explain a small rotation as a uniform shift.** A near-0° rotation of a
   short bar could look like a translation ⇒ `recognized_transformed` with a *shift*, not a
   rotation. That is not an orientation dimension either; report `kind` on every Transform.
4. **A degenerate signature.** If a bar's ON support is tiny/near-identical across
   orientations, decode could recognise for the wrong reason. Report support sizes per θ.

## 6. §1 — five clauses, on the MINT-COUNT instrument (new, no history), all measured IN-RUN

1. **Floor (noise/scrambled): MUST MINT.** Permute the ON/OFF support to random cells ⇒ no
   held shape explains ⇒ mint. **A loop that mints nothing is not a success — that is FM-0's
   disease.**
2. **Ideal exemplar:** a synthetic EXACT lattice-rotated held shape (the tromino precedent,
   re-run on MY harness) ⇒ **zero mint + a `LatentDimension`**. Proves my harness reaches
   rung 2 at all.
3. **Duration-stability:** mint-count at retina development 200 vs 800 steps. Duration is
   **NOT** my IV (§1.2), so if mint-count moves with it, every arm comparison is meaningless
   and I must say so.
4. **Arms alive:** EVERY observation must carry `transform_checked==1` AND `dim_checked==1`
   (both rungs looked). If `dim_checked==0`, nothing reached rung 2 and a low mint-count
   means *dead*, not *smart*.
5. **Load-bearing (§13.2):** toggle the codebook (held shape present vs empty) ⇒ mint-count
   must move. `D == 0` exactly ⇒ decorative ⇒ STOP.

## 7. n, seeds, decision rule

**Seed block 18000–18999** (declared; ledger updated in this commit). **12000–17999 untouched.**

| seeds | use |
|---|---|
| 18000 | **BURNED** — bring-up/pilot (channel distribution above). Never confirmatory. |
| 18001–18004 | §1 clauses 1/2/3/5 |
| 18010–18019 | **CONFIRMATORY** — 10 retina seeds × every arm |

**n = 10 retina seeds.** Mint-count is a near-deterministic structural property of the
encoding given a retina; the only stochasticity is retinal development. **Unit of analysis
is the SEED** (§4), never the observation.

**Decision rule:**
- mints(N) grows ~1:1 with N on the non-lattice arm AND no orientation `LatentDimension`
  ⇒ **NEGATIVE**: the core loop does not produce orientation structure from whitened
  retinal input. Diagnosed cause named (rung 2 is integer-lattice-only).
- mints(N) ~ O(1) with an orientation `LatentDimension` on the non-lattice arm
  ⇒ **POSITIVE**, paradigm-native.
- Mixed/fragmentary (proviso 2) ⇒ report as such; **a low mint-count without a
  `LatentDimension` is NOT a positive.**

**A NEGATIVE IS A RESULT (§7).** It would say the substrate's own core loop cannot produce
visual structure *even from decorrelated input* — the paradigm answer this arc was asked to
produce. **I will not tune toward a positive.** There is nothing to tune (§3.1).

## 8. Does rung 7's decorrelation change L0's negative? — prediction

Stage 2's L0 (mint + Oja on natural patches) was negative; its named causes were **no
whitening**, wrong objective, underconverged. Rung 7's channels ARE decorrelated
(σ_ON,ON 1.627 vs σ_ON,OFF 3.264) — whitening is the one live hypothesis `w0` did not kill.

**I predict decorrelation does NOT rescue it, for a reason ORTHOGONAL to whitening:** the
failure I expect is **representational, not statistical**. Rung 2 cannot express a 15°
rotation *no matter how good the input statistics are*. Whitening cannot conjure a generator
that does not exist. **If I am wrong and the non-lattice arm collapses, my model of the
ladder is wrong** — and that is the proviso worth breaking.

## 9. Scope — what this rung will NOT show (§8)

- Nothing about which biological mechanism is correct.
- No map topography; no tuning curves; **no OSI**.
- A `LatentDimension` for orientation would NOT be "the retina grew Gabors" — it is a
  codebook fact about a decode, not a receptive field.
- Only 16×16, one bar stimulus family, one retina.

## 10. Exact gates (§12 — named files, never `-k vision`)

- `tests/test_engine_provenance_migrated.py`
- `tests/test_dimension_inference_migrated.py`
- `scripts/rung7_vision_bench.sh` (20 named files; 173 passed / 10 skipped at `366ce5f14eff`)
- new: `tests/test_sdloop_vision_migrated.py`

**§9:** `seeds/vision_sdloop.json` ships INERT — `load_all_seeds` GLOBS `seeds/*.json`, so it
auto-loads into every boot and MUST be verified to change nothing without my Observations.

---

# ADDENDUM — PRE-REGISTRATION 2: THE ORBIT LAW (prospective)

*Written after the exploratory arms on burned seed 18000 and COMMITTED before the
confirmatory run. **This is a NEW mechanism-level hypothesis, not a reinterpretation of
data that failed** (§5): PREREG-1's prediction (mints ≈ N) is **REFUTED** and is reported
as refuted. §5 requires a new prediction be tested **prospectively** — so this is stated
before looking at any of N ∈ {8, 9, 36} or at any confirmatory seed.*

## A. What PREREG-1 got wrong

- **Proviso 1 BROKE (predicted "lattice arm mints > 1"):** the retina's response to a
  90°-rotated bar **IS** an exact lattice rotation. 0° minted, **180° recognized exactly**,
  90°/270° recognized as `rotation90` k=1. Lattice arm: **1 mint + `latent:rotation90`**.
- **The headline prediction (mints ≈ N on the non-lattice arm) is REFUTED.** Observed on
  burned seed 18000: mints = **1, 2, 2, 2, 4** for N = **2, 3, 4, 6, 12**. At N=12 the
  minted orientations are exactly **0°, 15°, 30°, 45°**; the other 8 are recognized as
  transforms of those four.
- **Why I was wrong:** I reasoned "no generator expresses a 15° rotation, therefore each
  15°-stepped orientation is novel." True but irrelevant — the loop never needs to rotate
  by 15°. It only needs **some held generator to map one PRESENTED orientation onto
  another**. `rotation90` maps θ→90−θ and the reflections map θ→−θ, and those act on the
  whole presented set at once.

## B. The law (post-hoc on 18000; PROSPECTIVE from here)

> **mints(N) = the number of ORBITS of the presented orientation set under the group
> generated by the HELD `DimensionGenerator`s** — ⟨θ→θ+90°, θ→−θ⟩, the dihedral symmetry
> of the square lattice, acting on orientation mod 180°.

Orbit of j = {j, j+90°, −j, 90°−j} (mod 180°). Retrodicts 18000 exactly (1,2,2,2,4), and
explains N=3 minting 2 with **only `latent:reflection_r`**: 90° is not a multiple of 60°,
so `rotation90` is **inapplicable** to that set and only negation acts.

## C. PROSPECTIVE PREDICTIONS — stated before looking, on FRESH seeds

| N | step | why | **predicted mints** |
|---|---|---|---|
| **8** | 22.5° | +90° = +4 steps; orbits {0,4}, {1,3,5,7}, {2,6} | **3** |
| **9** | 20° | 90° is NOT a multiple of 20° ⇒ **`rotation90` INAPPLICABLE**, only θ→−θ acts: {0},{1,8},{2,7},{3,6},{4,5} | **5**, and **NO `latent:rotation90`** — only reflections |
| **36** | 5° | +90° = +18; two size-2 orbits ({0,18},{9,27}) + 8 size-4 orbits | **10** |

**N=9 is the risky one:** it predicts a *qualitative* absence (no `rotation90` dimension at
all). A generator-agnostic account predicts no such thing.

**Decision rule:** all three hit on fresh confirmatory seeds ⇒ the law stands. Any miss ⇒
the law is wrong and reported wrong. **Unit of analysis is the SEED (§4).**

## D. What the law MEANS — and the scope that kills the naive positive

**This is NOT "orientation emerged as a dimension."** Orbit size is **at most 4**, so as
orientation sampling gets finer, **mints → N/4**: a **bounded constant-factor fold**, not a
dimensional collapse. A true orientation dimension would give **O(1)** mints at every N.

**`sd_infer_dimension` never mints a NEW generator** — it mints `latent:<held generator>`,
i.e. it *selects* from the held codebook. The ladder's *"the dimension set itself is
dynamic — quanta OF dimensions"* is realised here as **"name which HELD generator applied"**,
NOT as "discover a generator you did not hold". **The 15° step itself was never learned.**

## E. §13.1 — could this have produced the opposite?

**Yes, and that is why it is evidence rather than a tautology:**
- The held generators FORCE the *orbit structure* — that half **went in with the
  architecture** and I claim no credit for it (§13.1's third category).
- But whether the RETINA's ON/OFF output actually **preserves exact lattice symmetry** was
  an open empirical question, and it is the whole result: **PREREG-1 predicted it would
  NOT** (proviso 1) and would give mints = N. The model could have produced 12 and
  produced 4. **The prediction was risked and the retina decided it.**
- **N=9 can falsify the law outright** by minting anything other than 5, or by minting a
  `latent:rotation90` the law says is impossible.
