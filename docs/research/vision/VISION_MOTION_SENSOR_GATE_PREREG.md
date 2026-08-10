# THE MOTION SENSOR'S ACCURACY GATE — PRE-REGISTRATION

*Written and committed BEFORE any confirmatory number (§3). Seed block
**94000–94999**.*

## Provenance, recorded before anything

- **branch (as observed):** `worktree-agent-acf1e2a2e45c10e00`
- **base SHA (as observed):** `ee0a1af25ef5dea0e9bc8919f85ebe7e8e19f463`
- **engine:** `a1d350bbd23b`, built IN THIS TREE by `scripts/engine_build.sh`
  (`own`; never symlinked from canonical). Rust source verified byte-identical
  to canonical before the build, so the shared-build clause of §10.1 would also
  have been satisfied — the build was done anyway, per the brief.
- **provenance gate as its OWN step, before any number:**
  `python3 -m pytest tests/test_engine_provenance_migrated.py -q` → **7 passed**.
  The measuring process ALSO prints `provenance_line()` from inside itself and
  the two are compared by hand.
- **oracle:** `bash scripts/rung7_vision_bench.sh` → **212 passed, 10 skipped**,
  exit 0. `data/` is absent from this worktree, so 212/10 is the correct §10.2
  reading (222/0 is the with-`data/` figure). This rung needs no corpus: every
  stimulus is synthesised.
- **seed claim:**
  ```
  SEED CLAIM 94000-94999: CLEAN -- no collision DETECTED.
    Scope: 798 files with seed sinks; 482 UNRESOLVED sink sites tree-wide
      (counted, not discarded).
    CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
      one generator. default_rng(S) burns an unbounded stream downstream of
      S; a rung seeding ONCE at its block base measures as ONE seed here.
    CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
      unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
      'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
  ```

## 0 — Why this rung exists

Two independent rungs measured this sensor wrong, neither gated it, and both had
to caveat their headline:

1. **84000–84999**: *"THE MOTION SENSOR IS ~11% WRONG PER BLOCK on a pan whose
   answer is KNOWN and UNIFORM — it finds `dom_v=(4,4)` EXACTLY and then groups
   the WRONG BLOCKS, which explains the global-pan failure and BOUNDS EVERY
   COUNT."*
2. **86000–86999**: *"P1 … predicted `(0,0)` for all S>4 and S=5–7 returns
   `(0,4)`, RIGHT DIRECTION, WRONG MAGNITUDE, confidently wrong and
   INDISTINGUISHABLE DOWNSTREAM FROM A TRUE VECTOR (a sensor defect worth its
   own gate)."*

The standing rule earned from the ventral→writing refutation binds here:
**ABOVE-THE-NULL IS NOT GATE-GRADE — a hard gate is priced by the feature's
ERROR RATE, not its effect size.** The motion signal is used as a HARD grouping
criterion and nobody has priced it. And the second standing rule binds the
design: **a diagnostic must not be computed by the component it checks** —
so the ground truth here is BY CONSTRUCTION.

## 1 — Hypotheses, two-sided, stated in advance

**H1 (the three-way decomposition).** The sensor's error is NOT one number. It
partitions into **silent miss** (reports no motion where motion exists),
**confidently wrong** (a well-formed vector that is wrong and indistinguishable
downstream from a true one) and **correct within tolerance**, and these three
have *different* rates and *different* parameter dependencies. Two-sided: the
null is that the three move together and the decomposition buys nothing.

**H2 (the governing parameter).** The error rate is a function of
**displacement magnitude RELATIVE TO the search aperture** (`radius = block`),
not of displacement magnitude in pixels. Two-sided: the alternative is that
error is set by absolute pixel displacement, in which case a larger block would
not help.

**H3 (the texture disagreement).** The motion rung found the flattest texture
quartile 4× more error-prone on C1 and NO monotone relationship on C2. **I
predict the C1 relationship is a CONFOUND and contrast is NOT the driver** —
on found frames "block std" co-varies with spatial-frequency content, and it is
the latter that matters. Two-sided: if error falls monotonically with contrast
at fixed spectral slope, C1 was right and C2's null needs a different
explanation.

**H4 (the zero field).** On a genuinely static field the Occam tie-break
protects the sensor and false motion is at or near zero. Two-sided: if the
sensor invents motion from a static scene, that is a worse defect than either
recorded one.

## 2 — My predictions, with their provisos (§3.7)

| # | prediction | proviso |
|---|---|---|
| P1 | **Confidently wrong ≫ silent miss on textured input.** The sensor CONFABULATES rather than abstains. | Fails if the sensor abstains beyond its aperture. |
| P2 | **Silent miss is a property of LOW-EVIDENCE stimuli, not of displacement** — it appears where blocks tie (uniform / near-flat fields), which is exactly the phi rung's stimulus. | Fails if silent miss tracks magnitude on textured input. |
| P3 | **Error collapses onto \|D\|/block.** Below 1 it is small; above 1 it rises steeply toward ~100%. | Fails if block=8 at \|D\|=8 does not beat block=4 at \|D\|=4. |
| P4 | **The recorded ~11% is reproduced at the arc's operating point** (block 4, pan of one block, exact tolerance) on a *completely different* corpus. | If it is not reproduced, either the apparatus or the recorded figure is wrong, and I must say which. |
| P5 | **Contrast is not load-bearing; spectral slope is.** | See H3. |
| P6 | **False motion on a static field ≈ 0**, including under additive noise. | See H4. |
| P7 | **Every error on a block where the true offset is the UNIQUE SAD minimiser is zero** — i.e. the sensor's arithmetic is correct and the error is the OBJECTIVE's, not the implementation's. | If non-zero, there is an implementation bug and that is the finding. |

## 3 — The statistic, exactly

For every block: true vector `t` (an INPUT to the construction), reported
vector `v`, `err = ‖v − t‖₂`. On blocks where **motion exists** (`t ≠ 0`) the
three outcomes are exhaustive and mutually exclusive, and are tested **in this
order**:

1. `silent_miss` — `v == (0,0)`. Tested FIRST and UNCONDITIONALLY, ahead of the
   tolerance. Downstream this is not a slightly-wrong vector, it is the ABSENCE
   of one: a cell that cannot join any common-fate group. The count of silent
   misses that would ALSO have passed the tolerance is reported as a disclosure.
2. `confidently_wrong` — `v ≠ (0,0)` and `err > τ`.
3. `correct` — `v ≠ (0,0)` and `err ≤ τ`.

On blocks where **motion does not exist** (`t == 0`): `false_motion` —
`v ≠ (0,0)`.

**Unit of analysis is the SEED (§4).** Blocks inside one field share input and
compete under one objective; they are not independent. Every rate is computed
per seed and aggregated across seeds with a 95% CI.

## 4 — The tolerance is DERIVED, not chosen (§13)

Three readings, **all** reported, fixed here before any confirmatory number:

- **`τ = 0` (exact).** No number at all — the strongest §13 outcome (cf. §2.1's
  cycle-detect: "not a number that falls out, but *no number*"). **This is the
  primary headline.**
- **`τ = Otsu's split over the observed error magnitudes, restricted to
  displacements within the aperture (`|D| ≤ radius`).** The motion rung's own
  precedent, run on the population the tolerance is *for*: among answers the
  sensor could have got right, where does correct end and wrong begin? Otsu
  needs no binning here — the observed magnitudes are norms of integer vector
  differences, a discrete set, so the candidates are the observed values
  themselves and there is no bin count to choose.
- **`τ = Otsu's split over ALL observed error magnitudes.`** Reported because it
  is informative and because hiding it would be selective: the full pool is
  dominated by the beyond-aperture regime, so the split it returns is a
  statement about THE APERTURE rather than about accuracy.

**Both pools were fixed on the PILOT (burned seeds 0–13) and are recorded here
before the confirmatory run.** Reporting all three, rather than the most
flattering one, is the §5-compliant form: a rate conditional on one pooling
choice is not a result.

## 5 — n, fixed in advance by a pilot on already-burned seeds

Pilot: seeds **0–13** (long since burned; §3.3 requires the pilot be restricted
to burned seeds). Measured seed-level 95% CI half-width on the headline
operating-point rate: **0.00083** at n=14. The synthetic corpus is homogeneous
across seeds, so precision is NOT seed-limited and more seeds buy almost
nothing.

**n = 24 confirmatory seeds, 94000–94023**, giving a half-width below 0.001 on
every headline rate — an order of magnitude finer than the effects at issue
(1–99 pp). The grouping-bound arm uses the first 8 of those seeds (it boots a
substrate per field and is ~100× more expensive per unit).

**This is the honest disclosure about power:** n is not the binding constraint
in this rung, and I am not claiming it as a virtue. What binds is whether the
*constructed stimulus family* is representative — see §9.

## 6 — Exactly these arms. No sweeps, no re-runs.

| arm | what it varies | why |
|---|---|---|
| **I1 zero identity** | `b` bit-identical to `a`, with a FLAT region | exact invariant; catches a tie-break bug |
| **I2 unique-minimum fidelity** | blocks where truth is the unique SAD minimum | exact invariant; catches an objective/aperture bug |
| **OP operating point** | block 4, pan of exactly one block | the reproduction check against the recorded ~11% |
| **A1 magnitude** | \|D\| ∈ {0,1,2,3,4,5,6,8,10,12} × 12 directions | H1, H2, P1 |
| **A2 block size** | block ∈ {2,4,8} × \|D\| ∈ {1,2,4,6,8} | H2, P3 |
| **A3 texture** | contrast ∈ {2,4,8,16,32,64} × β ∈ {0,1,2}, ORTHOGONAL | H3, P5 |
| **A4 bodies** | k ∈ {1,2,3,4} true velocities; seam blocks FLAGGED | multi-body |
| **A5 rotation** | θ ∈ {1,2,5,10,90}°; deforming blocks FLAGGED | rotation |
| **A6 zero field** | noise sd ∈ {0,1,2,4} | H4, P6 |
| **A7 bordered pan** | cropped (non-toroidal) pan; border blocks FLAGGED | border fabrication |
| **A8 figure on uniform** | figure ∈ {4,8,16} px × \|D\| ∈ {1,2,4,6,8,12} | P2; the phi rung's exact stimulus class |
| **AMB decomposition** | truth-is-unique-minimum split | P7 — SECONDARY, declared |
| **BOUND** | the REAL grouping pipeline on k known bodies | the bound other rungs cite |

**Directions are 12, 30° apart** — deliberately including off-lattice
directions, so the profile is not read off the four directions a square lattice
flatters.

## 7 — The gate, and its positive control

The gate ships as `scripts/motion_sensor_gate.py`, runnable by any future rung.

**A gate that has never been ABLE to fail has not been tested** — three
provenance gates in this tree sat green for 51 commits and then all fired at
once as false accusations. So the gate is positive-controlled against **three
deliberate degradations of the sensor, all of them REAL bugs rather than
caricatures**:

- `tiebreak_corner` — visit offsets in raw row-major order. **This is exactly
  the footgun `vector_field`'s own docstring claims to avoid.**
- `radius_half` — shrink the search window to `block//2`. Invisible in every
  output except accuracy.
- `sad_coarse` — score SAD on every other pixel. The classic subsampling
  speedup; changes the objective, identical interface.

**Registered decision rule for the control:** each degradation MUST turn the
gate RED, and the unmodified sensor MUST be GREEN. A degradation that passes is
a failed gate and is reported as such.

**The reference implementation is asserted BIT-IDENTICAL to
`mgw.vector_field` on 108 inputs EVERY TIME THE GATE RUNS.** Without that, the
"undegraded" arm could silently drift from the instrument under test and the
control would mean nothing.

## 8 — Decision rule, including what a null means

- **P1–P7 are scored as registered.** A broken proviso is reported as broken and
  tells me what I did not understand (§3.7).
- **The three rates are the deliverable whatever they are.** There is no
  outcome here that counts as "the sensor passed": the rung's product is a
  PRICE, and a low price and a high price are equally publishable (§7).
- **A NULL — all three rates flat across every parameter — would mean the error
  is irreducible and structureless**, which would still bound every landed
  count and would still be the deliverable.
- **If the recorded ~11% does NOT reproduce (P4), I must say whether the
  apparatus or the recorded figure is at fault, and I must not proceed to the
  bound until that is settled.**

## 9 — What this design CANNOT show (§8), stated in advance

- **Constructed stimuli are not found frames.** Fourier-synthesised textures
  have stationary statistics; real scenes have occlusion, non-rigid motion,
  lighting change and compression artefacts. Every rate here is a rate on a
  stimulus family I chose, and the family is the load-bearing assumption of the
  whole rung. The OP arm exists precisely to tie one point of it back to the
  recorded corpus figure.
- **The ambiguity decomposition shares the SAD objective with the sensor** and
  is therefore NOT independent evidence about the arithmetic. It is declared
  secondary and is never the headline. What licenses it at all is that it is
  ground-truth-conditional — it asks about the known `t`, which the sensor has
  no access to.
- **The rotation arm's "true vector" is the displacement of the block CENTRE**,
  which is only a complete description where within-block deformation is below
  half a pixel. Blocks above that are reported separately: there, one vector per
  block is a REPRESENTATION failure, not a sensor failure, and conflating them
  would flatter or damn the sensor at will.
- **No claim about temporal integration.** Everything here is two frames.
- **No Rust, no seed, no change to any existing rung's files.** §9: nothing
  ships on by default; the gate is a new script and adds no default behaviour.

## 10 — §13 gate

No threshold is written into the measurement. The tolerance is Otsu over
observed values (two declared pools) or exactly zero; the CI uses the Gaussian's
own 95% quantile; the classification boundaries are `== 0` and `> τ`. An AST
gate over this rung's own source enforces it, **located BY SHAPE not by
substring**, and — heeding the phi rung's recorded defect, where the first
version counted ARRAY INDICES as thresholds in 3 of 6 flagged sites — **every
flagged site is audited BY HAND before the gate is changed** (§12.3: verify the
fact, then fix the gate, never the reverse).
