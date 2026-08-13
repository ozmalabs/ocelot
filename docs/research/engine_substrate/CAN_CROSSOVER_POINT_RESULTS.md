# Crossover-point experiment for coarse-vs-fine causal-belief quantization — RESULTS

Prereg: `CAN_CROSSOVER_POINT_PREREG.md`, same worktree/branch, base
`main @ d061b2d`. Worktree
`/home/matt/ozmadev/ocelot-worktrees/can-crossover-point`, branch
`can-crossover-point`.

**Verdict, up front:** **no genuine crossover N\* was found** in the tested
range N ∈ {4, 8, 12, 16, 24, 32}, under the criterion registered in advance
(PREREG §2.4 point 2) — checked exhaustively at every tested N and it never
fires, for either the plain i.i.d. coupling design (Experiment A) or the
structured/blocky coupling design (sharpening (a)). This is reported as the
clean, acceptable, honest null the PREREG registered in advance (§2.4 point
1), not reinterpreted. What the sweep DOES establish, precisely: (a) the
prior rung's small-N reversal (coarse showing MORE, less-concentrated
basins than fine — the opposite of the naive "coarse collapses" intuition)
is real and reproduces at N=4/8 with 5-seed replication, not a one-draw
artifact; (b) the prior rung's N=16 near-parity is confirmed but does NOT
develop into a crossover as N is pushed to 24 and 32 — coarse and fine stay
inside each other's seed-to-seed noise band at every tested N, all the way
to N=32; (c) a genuinely new, clean, well-powered finding this rung
surfaced that the prior rung's design could not see: **the single sharpest
resolution effect found anywhere in this sweep is not "more bins is
better," it is the presence or absence of a NEUTRAL/ZERO option** — a
2-value (no-zero) vocabulary produces 1.6–2× the frustration of every
V≥3 vocabulary tested, at every N, while V=3 through V=11 show no reliable
ordering among themselves; (d) the population-**mixture** design
(Experiment C) does **not** reproduce Experiment A's own near-parity —
floor (coarse-leaning) individuals show a persistent, and by N=16/32
visibly WIDENING, frustration gap over ceiling (fine-leaning) individuals,
a genuine, reportable divergence between the clean matched-pair design and
a realistic independent-population design, traced (§3.3) to a real
methodological difference between the two designs, not asserted as a
contradiction; (e) the oscillation/"abandonment" binary (real, confirmed
again this rung) tracks N/density far more than it tracks basin-count
degradation WITHIN a given N — it is a separate axis, not basin-count
collapse under another name; (f) the structured/blocky coupling generator
built for the tractability sharpening carries a real, honestly-named
confound (deliberately alternating block polarity adds genuine cross-block
antagonism, not merely redundancy) that limits how cleanly it answers the
compression question, reported as a limitation rather than smoothed over.

---

## 1. Reused methodology — exact citations

Per the charter's requirement not to reinvent the prior rung's own
machinery, this rung imports (not reimplements) three functions directly
from `tests/test_can_belief_quantization.py`, loaded via
`importlib.util.spec_from_file_location` in
`tests/test_can_crossover_point.py:33-40`:

- **Multi-start basin discovery**, `_basin_sweep`,
  `tests/test_can_belief_quantization.py:66-116` — re-seed every Concept's
  `state` to an i.i.d. `{-1,+1}` draw, call `mt_mean_field_marginal`,
  cluster converged marginals (L2 < 0.3 merge), return
  `basin_count`/`effective_basin_count` (exp of Shannon entropy over
  cluster occupancy)/`dominant_basin_fraction`/mean frustration/mean
  energy.
- **Network construction**, `_build_complete_network`,
  `tests/test_can_belief_quantization.py:53-63`.
- **Oscillation probe**, `_oscillates`/`_relax_with_fields`,
  `tests/test_can_belief_quantization.py:337-365` — fixed nonzero external
  field per node, fixed all-zero start, max_iter=400-vs-401 parity gap.

The ONLY new piece of engine-adjacent code this rung wrote is a
generalization (not a replacement) of the prior rung's quantizer —
`_round_to_vocab_v` (`tests/test_can_crossover_point.py:71-80`), an
evenly-spaced V-point scale across `[-1,+1]` inclusive of both endpoints,
matching Preston & Colman's own tested 2-11-category design exactly (the
prior rung's centered-integer-`k` scheme can only produce odd,
zero-centered vocabularies and cannot express a 2-, 4-, or other
even-count scale at all). `V=3` is numerically identical to the prior
rung's own "coarse" condition (`{-1,0,+1}`), confirmed by direct
inspection, so every N=4/8/16 coarse-condition number in Experiment A below
is directly comparable to the prior rung's own — not merely internally
consistent with itself. No new Rust, no new `can_ops.rs` function, per the
charter's scope boundary — confirmed sufficient by re-running the prior
rung's own 11/11 test suite in this worktree before writing any new code
(0.38s, unmodified).

**Compute**: the full sweep (Experiments A/B/C, sharpenings (a)/(b)) runs
in **4.08s wall-clock**, confirming the prior rung's own "sub-millisecond
per trial" characterization at this rung's larger scale (≈13,300 real
`mt_mean_field_marginal` calls across all experiments combined).

---

## 2. Experiment A — the N-crossover sweep, primary result

N ∈ {4, 8, 12, 16, 24, 32}, coarse (V=3) vs fine (V=7), **5 independent
random-coupling seeds per (N, condition) cell** (correcting the prior
rung's single-draw design), 40-restart multi-start basin sweep per cell,
β=2.0, h=0 — 2400 real relaxations. Full table (mean across 5 seeds; ranges
in §2.1):

```
N    coarse?  eff_basin  dom_frac   frustr     energy     basin_ct
4    coarse   4.662      0.335      1.989      -0.011     5.200
4    fine     3.235      0.475      2.443      0.043      4.000
8    coarse   5.808      0.390      14.065     -1.135     8.400
8    fine     4.508      0.365      14.341     -0.459     5.800
12   coarse   14.473     0.205      41.026     6.426      18.800
12   fine     11.508     0.205      37.578     4.111      14.400
16   coarse   18.690     0.160      48.432     -8.968     23.000
16   fine     17.349     0.145      56.135     -2.132     20.200
24   coarse   27.466     0.105      133.526    -6.074     30.600
24   fine     30.920     0.070      136.461    -3.739     32.800
32   coarse   37.919     0.040      246.925    -2.075     38.400
32   fine     34.771     0.060      248.302    2.035      36.200
```

**N=4/8 reversal reproduces under seed replication**: coarse shows MORE
effective basins than fine at both N=4 (4.66 vs 3.24) and N=8 (5.81 vs
4.51) — the SAME direction the prior rung found on its single N=4/8 draws,
now confirmed with 5 independent draws each, not a one-off artifact of the
prior rung's specific seed.

### 2.1 The registered crossover criterion, applied exhaustively

PREREG §2.4 point 2, applied at every tested N (gap = fine minus coarse for
dominant fraction, coarse minus fine for effective-basin-count; "range" =
the larger of the two conditions' own 5-seed min-max spread at that N; MET
requires both gaps to exceed their range):

```
N     domfrac_gap(fine-coarse)   eff_gap(coarse-fine)        CRITERION MET
  4   +0.140  (range 0.375)      +1.427  (range 1.583)       False
  8   -0.025  (range 0.350)      +1.300  (range 7.357)        False
 12   +0.000  (range 0.275)      +2.965  (range 15.247)       False
 16   -0.015  (range 0.175)      +1.341  (range 20.595)       False
 24   -0.035  (range 0.050)      -3.454  (range 13.334)       False
 32   +0.020  (range 0.050)      +3.148  (range 9.427)        False
```

**Never met, at any tested N.** This is the primary result of this rung:
**no crossover N\* exists in the tested range under the pre-registered
operational standard.** The pattern is not even monotonically APPROACHING
the criterion — N=24 briefly shows the predicted-direction sign on
`dominant_basin_fraction` (coarse more concentrated, per the literature's
naive intuition) but N=32 reverses back toward the small-N pattern (coarse
LESS concentrated again), and `effective_basin_count`'s sign flips three
times across the six tested N values (positive at 4/8/12/16/32, negative at
24). Per PREREG §2.4 point 3 ("plateau-not-crossover") and point 1
("primary honest-null clause"), this is reported as **density/frustration
saturation without a resolution-driven crossover, plus small-N noise the
5-seed replication does not fully average out** — not a disguised partial
confirmation.

**A caveat that matters for how to read the near-parity at N=16-24,
surfaced by contrast with Experiment C below (§3.3):** Experiment A's
design feeds the SAME true-coupling draw to both the coarse and fine
condition at a given (N, seed) — apples-to-apples on one instance,
following the prior rung's own logic exactly. This means the apparent
"convergence" at higher N could, in principle, partly reflect that both
conditions are rounding the IDENTICAL underlying frustrated structure
rather than resolution genuinely stopping to matter. §3.3 reports a real,
measured difference when this is tested with independent per-individual
draws instead — named here in advance of that section so the two are read
together rather than as two disconnected results.

---

## 3. Experiment B — continuous resolution sweep (2-11 bins)

N ∈ {8, 16, 32}, V ∈ {2, 3, 4, 5, 7, 9, 11}, 5 seeds, 40 restarts —
3,675 real relaxations, addressing the charter's "resolution levels
spanning roughly 2-12 bins" requirement directly rather than only via the
coarse/fine binary.

```
--- N=8 ---                          --- N=16 ---                         --- N=32 ---
V   eff_basin domfrac frustr         V   eff_basin domfrac frustr         V   eff_basin domfrac frustr
2   9.88      0.305   22.6           2   20.58     0.185   122.9          2   39.19     0.035   501.3
3   5.81      0.390   14.1           3   18.69     0.160   48.4           3   37.92     0.040   246.9
4   8.05      0.280   14.3           4   19.01     0.125   61.9           4   33.48     0.085   275.2
5   6.15      0.350   13.9           5   19.95     0.135   55.3           5   32.75     0.080   260.9
7   4.51      0.365   14.3           7   17.35     0.145   56.1           7   34.77     0.060   248.3
9   5.14      0.370   15.3           9   17.77     0.160   58.5           9   34.25     0.075   251.6
11  4.85      0.375   14.7           11  18.90     0.140   53.4           11  35.86     0.050   249.2
```

**The genuinely new finding: V=2 (no-neutral-option) is a real, clean, sharp
outlier — not a point on a gradient.** At every tested N, the 2-value
(`{-1,+1}`, no zero) vocabulary produces roughly **1.6–2× the frustration**
of EVERY V≥3 vocabulary: 22.6 vs a 13.9-15.3 band at N=8; 122.9 vs a
48.4-61.9 band at N=16; 501.3 vs a 246.9-275.2 band at N=32. This holds
uniformly across all 3 tested N and is not close (the V=2 value sits well
outside the full range spanned by V=3 through V=11 in every case). **The
mechanism, read against `can_ops.rs`'s own "Unknown = zero vector"
convention** (already load-bearing in the prior rung's own §5 test,
`test_ambivalence_rule_flags_only_near_zero_state`): without a zero
option, EVERY coupling in a complete, near-random-sign graph must commit to
a full-magnitude sign, even where the true relationship is weak or
near-neutral — removing the substrate's own "no commitment" default from
the weight vocabulary, not merely coarsening it, and that is what drives
the frustration spike, not "resolution" in the generic bins-per-dimension
sense the charter's other tested V values probe.

**Among V=3 through V=11 (excluding the V=2 outlier), no reliable ordering
exists.** At N=32, frustration ranges narrowly (246.9 to 275.2) with no
monotonic trend by V — V=3 is LOWEST, V=4 is second-HIGHEST, V=7/9/11 sit
in between, in no consistent order across the three N values tested (at
N=16, V=3 is again lowest but V=5 outranks V=4 while at N=8 V=5 is lowest
and V=3 is highest — the ordering is not stable across N). **Per PREREG
§2.4 point 5's own registered honest-null clause: within the literature's
own tested 3-11 range, resolution is not a clean, monotonic lever on this
design's outcome metrics** — the ONE resolution effect that IS real and
clean is qualitative (zero-option present vs absent), not continuous.

---

## 4. Experiment C — population-mixture design

Per PREREG §2.3: a two-component mixture (π=0.5 each) — "floor/naive"
individuals draw V ∈ {2,3} uniformly, "ceiling/exposed" individuals draw
V ∈ {6,7,8} uniformly (component means 2.5 and 7, a 3.5× ratio — same order
of magnitude as, though not tuned to match exactly,
`CAUSAL_GRANULARITY_POPULATION_DISTRIBUTION_RESEARCH.md`'s own measured
~2.5× CRT floor/ceiling swing). K=30 simulated individuals per N, each with
an INDEPENDENT true-coupling draw (unlike Experiment A's shared-per-seed
draw), N ∈ {4, 8, 16, 32}, 15 restarts each — 1,800 real relaxations.

```
N    component  eff_basin  dom_frac   frustr     round_err
4    ceiling    3.646      0.404      3.121      0.084
4    floor      4.906      0.367      4.712      0.356
8    ceiling    4.186      0.412      15.183     0.090
8    floor      6.219      0.303      19.185     0.375
16   ceiling    9.015      0.257      60.089     0.083
16   floor      11.118     0.196      103.190    0.408
32   ceiling    13.987     0.109      255.627    0.086
32   floor      14.239     0.099      447.187    0.453
```

**Manipulation check confirmed** (asserted in the test itself): floor's
mean rounding error (0.084-0.453 depending on N) is consistently higher
than ceiling's (0.083-0.090) — the mixture components really do differ in
resolution as designed.

**The direction found in Experiment A's small-N cells (floor/coarse shows
MORE effective basins, LESS concentration than ceiling/fine) holds at
EVERY tested N here, including N=32** — unlike Experiment A's own clean
two-condition design, which converges toward parity by N=24-32. This is
the sharpest, most load-bearing divergence this rung found between "a
clean matched-pair comparison" and "a realistic independent population":

**The frustration gap between floor and ceiling widens, not narrows, with
N**: absolute gap 1.59 (N=4) → 4.00 (N=8) → 43.10 (N=16) → 191.56 (N=32);
ratio floor/ceiling 1.51 → 1.26 → 1.72 → 1.75 — a real, growing cost borne
by the floor/coarse population that the matched-pair design's shared-draw
structure (§2.1's own named caveat) does not surface. **Read precisely,
this is exactly the pattern the charter's own framing anticipated for
"simple people" under a realistic population, and it is Experiment A's
clean, apples-to-apples comparison — not Experiment C's — whose apparent
convergence looks like the more fragile result of the two designs, once
both are run.** This is reported as a genuine, measured divergence between
two legitimate designs answering two subtly different questions (one
resolution-instance vs. one shared true-coupling structure; many
independent resolution-instances vs. many independent true-coupling
structures, which is closer to how a real population of distinct
individuals' belief networks would actually differ), not as one design
being "wrong."

---

## 5. Sharpening (a) — structured vs. unstructured coupling (scoped tractability check)

Per the charter's explicit scope line (no `CausalLinkageShape` codebook, no
compression layer built), this is a smaller, scoped comparison: a
"coherent core + adversarial noise" coupling generator (blocks of ≤4
concepts, within-block couplings clustered around an alternating ±0.7
block anchor plus small noise; across-block couplings stay i.i.d.
`Uniform(-1,1)`) run through the identical N-sweep as Experiment A.

```
N    coarse?  eff_basin  dom_frac   frustr
4    coarse   5.529      0.345      2.977
4    fine     5.290      0.345      1.887
8    coarse   8.431      0.220      18.092
8    fine     5.926      0.275      13.028
12   coarse   8.816      0.315      41.230
12   fine     7.990      0.360      32.701
16   coarse   13.508     0.190      71.981
16   fine     16.761     0.155      62.046
24   coarse   28.570     0.125      167.515
24   fine     26.491     0.100      151.554
32   coarse   35.478     0.065      278.522
32   fine     33.802     0.065      254.235
```

**The registered crossover criterion (PREREG §2.4 point 2), applied
identically to this coupling generator, also never fires at any tested
N** — structure, as generated here, neither produces a crossover the
unstructured design lacks nor removes one (there was none to remove).

**A real, honestly-named confound limits how far this bears on the
tractability question.** Comparing structured to unstructured frustration
at matching (N, condition):

```
N    cond    unstructured_frustr  structured_frustr  ratio
4    coarse  1.99                 2.98                1.50
8    coarse  14.06                18.09               1.29
16   coarse  48.43                71.98                1.49
24   coarse  133.53               167.51               1.25
32   coarse  246.93               278.52               1.13
```

**Structured coupling shows HIGHER frustration than the unstructured
baseline at every N for the coarse condition** (1.13-1.50×), the opposite
of what a "redundancy helps a solver" hypothesis would naively predict.
**Diagnosed, not glossed over**: this generator's block anchors deliberately
ALTERNATE sign (+0.7, -0.7, +0.7, ...) block-to-block, which manufactures a
genuine antiferromagnetic-style antagonism BETWEEN adjacent blocks that the
i.i.d.-random baseline never had by construction (a random draw has no
systematic block-to-block sign correlation at all) — so this specific
generator confounds "recognizable redundancy" (the thing a future shape-
compressor could actually exploit) with "designed additional conflict"
(alternating polarity), and the two pull in opposite directions on
frustration. **Honest conclusion for sharpening (a): this scoped check does
not cleanly support or refute the compression-would-help hypothesis from
`CAN_BELIEF_QUANTIZATION_RESULTS.md` §7** — it demonstrates the STRUCTURED-
VS-UNSTRUCTURED distinction is easy to build in a way that changes the
answer for reasons unrelated to redundancy, which is itself a real,
transferable lesson for the next rung that DOES build the compression
layer: a "structured" test network needs redundancy tested in isolation
from any incidental extra conflict the generator introduces, and this
generator did not achieve that isolation.

---

## 6. Sharpening (b) — is oscillation AT the crossover point the SAME phenomenon as basin-count degradation?

Reusing `_oscillates`/`_relax_with_fields` at N ∈ {4, 16, 32} (the smallest
tested N, the prior rung's own convergence point, and this rung's largest),
across the SAME 5 seeds as Experiment A, cross-referenced against that
seed's own basin-sweep numbers:

```
N    coarse?  osc_rate
4    coarse   0.40
4    fine     0.20
16   coarse   0.60
16   fine     0.60
32   coarse   1.00
32   fine     0.80
```

**Oscillation rate rises steeply with N** (coarse: 40%→60%→100%; fine:
20%→60%→80%) — the same density-dominates-at-large-N pattern the basin/
frustration metrics already show.

**Pooled across all N, oscillating cells show much higher eff_basin_count
(25.20) and frustration (141.7) than non-oscillating cells (10.79 / 39.2)**
— but this is almost entirely an **N-confound**, not evidence oscillation
IS basin-count collapse: both oscillation rate and basin_count/frustration
independently rise with N. **Checked within-N** (the correct test,
registered in the PREREG as the actual question):

- **N=4** (3 oscillating / 5 draws): oscillating cells' eff_basin (5.19,
  2.67, 3.88) show no consistent separation from non-oscillating cells'
  (5.17, 3.72, 2.29, 3.92, 3.87) — overlapping ranges, no visible pattern.
- **N=16** (6 oscillating / 10 draws): the single HIGHEST effective-basin-
  count draw in the whole N=16 stratum (fine, seed 3, eff_basin=29.92,
  dominant_fraction=0.075) is **non-oscillating** — directly counter to
  "abandonment = collapse to fewer/more-concentrated basins"; conversely
  one of the highest eff_basin draws (coarse, seed 2, eff_basin=24.51) DOES
  oscillate. No clean separation.
- **N=32** (9 oscillating / 10 draws, too few non-oscillating points for a
  within-N comparison to be meaningful — reported honestly as
  underpowered at this N specifically, not force-interpreted).

**Verdict on sharpening (b), precise**: the real cohere-vs-fail-to-cohere
binary this substrate's own math exhibits (confirmed again this rung, same
mechanism as the prior rung's §3.1) is **strongly N/density-driven**, like
every other metric in this sweep, but **does not show a clean within-N
correlation with LOW basin diversity or HIGH concentration** — it is
reported as a **separate axis of the same underlying frustrated-landscape
phenomenon, not "basin-count collapse under a different name."** A network
can hold a rich, spread-out basin structure by the multi-start metric AND
still fail to settle from a fixed cold start, and vice versa. This sharpens
(rather than answers definitively, given the N=32 power limit) the prior
rung's own §9 point 3 open question.

---

## 7. Sharpening (c) — resolution alone, or density/structure too?

Read together, §2-6 support one clear answer, stated without hedging:
**density/N is the dominant lever at every scale tested, and resolution's
effect on top of it is real but narrow and mostly qualitative, not a smooth
"more bins is better" gradient.** Specifically:

- Frustration and basin_count/eff_basin_count both grow roughly
  monotonically with N regardless of resolution or condition (Experiment
  A's own table, §2) — density is never NOT the dominant driver of the raw
  magnitude of these metrics across the tested range.
- Resolution's effect, isolated by the coarse-vs-fine gap at each N
  (§2.1), is never large enough to clear the registered crossover bar
  against the SAME density-driven background variance — i.e., resolution
  does not act as an independent second axis strong enough to overcome
  density's own noise floor in this design.
- The one clean, large, resolution-driven effect found (§3, the V=2
  no-zero cliff) is present at EVERY tested N with similar RELATIVE
  magnitude (roughly 1.6-2×) — i.e., it is a resolution effect that is
  itself N-INVARIANT in its relative size, distinguishing it sharply from
  the noise-dominated V=3-11 comparisons.
- Structure (sharpening (a)) changes the absolute frustration level
  substantially (§5) but does not change WHETHER a crossover is found —
  still never met — and the specific structure tested confounds redundancy
  with designed antagonism, so this rung cannot cleanly attribute its
  effect to "structure" in the sense a future compressor would exploit.
- The population-mixture design (§4) shows that DRAW INDEPENDENCE (many
  distinct true-coupling structures, one per individual, vs. one shared
  structure quantized two ways) changes the qualitative answer at high N —
  persistent widening divergence vs. apparent convergence — which is
  itself evidence that how the "population" of comparisons is constructed
  matters at least as much as resolution or N alone.

**Honest combined verdict**: this sweep does not support "resolution alone
explains a crossover" (none was found), and it does not support "density
alone determines everything regardless of resolution" either (the V=2 cliff
and the mixture-vs-matched-pair divergence are both real, resolution-linked
effects). The most defensible reading, stated precisely: **density/N sets
the scale of every metric; resolution's effect rides on top of that scale
as a smaller, structurally-specific perturbation (an all-or-nothing
zero-option effect, and a population-composition effect visible only under
independent sampling) rather than as a smooth, monotonic, N-crossing
degradation curve** — which is a genuinely different, more precise claim
than either "resolution collapses under NxM" (the original charter
intuition, not confirmed here) or "resolution doesn't matter" (also not
what the data shows).

---

## 8. What this rung does NOT establish

1. **No crossover N\* exists anywhere in the tested range (N ≤ 32) under
   the pre-registered criterion — this does not rule out a crossover
   existing at larger N.** Compute cost is not the limiting factor (this
   whole sweep ran in ~4s); a follow-on could extend to N=64/128 cheaply if
   the question is judged worth pursuing further, though §7's own
   density-dominates finding makes a late-appearing crossover a weaker bet
   than it looked before this rung.
2. **The V=2 no-zero-option finding (§3) is new to this rung and not
   independently replicated against a differently-shaped no-zero
   vocabulary** (e.g., a 4-value vocabulary that also excludes zero was not
   tested) — whether the effect is specifically "no zero" or more broadly
   "even vocabulary size" is not disambiguated here.
3. **Sharpening (a)'s structured generator carries a real, named confound**
   (§5) — it does not cleanly test whether recognizable redundancy alone
   would help an arbitrary solver scale, only that THIS PARTICULAR
   generator (redundancy + designed block antagonism) does not produce a
   different crossover answer than the unstructured baseline.
4. **Sharpening (b)'s N=32 stratum is underpowered for the within-N
   oscillation-vs-basin-structure comparison** (9/10 draws oscillated,
   leaving only 1 non-oscillating point) — the N=4/N=16 within-N findings
   are the load-bearing evidence for "separate phenomenon," not N=32.
5. **Experiment C's mixture weights (π=0.5/0.5) and component ranges
   ({2,3} / {6,7,8}) are this rung's own design choice**, reasoned from but
   not literally handed over by
   `CAUSAL_GRANULARITY_POPULATION_DISTRIBUTION_RESEARCH.md` (which itself
   states no literature source measures a bin-count population directly) —
   a different, equally defensible mixture design could shift Experiment
   C's exact numbers, though the qualitative divergence from Experiment A
   (persistent vs. converging) is unlikely to be an artifact of the exact
   weights chosen, since it shows up at every tested N.
6. **Whether ANY of this reflects real human belief-network dynamics**, as
   opposed to an artifact of the mean-field/complete-graph/β=2.0
   operationalization, remains exactly as open as the prior two rungs left
   it (`CAN_BELIEF_QUANTIZATION_RESULTS.md` §9 point 1,
   `CAUSAL_LINKAGE_DIMENSION_RESEARCH.md` throughout) — this rung is a
   sharper measurement of the SUBSTRATE's own behavior, not a new claim
   about cognition.
7. **The compression/shape-recognition layer itself remains unbuilt**,
   exactly as scoped out by the charter — sharpening (a) is a proxy check,
   not a build or a measurement of that layer's actual performance.
8. **Sparse (non-complete) graph topologies were not tested**, matching the
   prior rung's own same limitation, inherited unchanged.

---

## 9. Regression

`tests/test_can_belief_quantization.py` — **unchanged, 11/11 green**
(reused as a library via `importlib`, not edited).
`tests/test_can_ops.py`, `tests/test_causal_attitude_networks.py`,
`tests/test_can_migration.py`, `tests/test_can_belief_quantization.py`,
`tests/test_can_crossover_point.py` (new, this rung) together:
**47/47 passed, 8.16s.**

---

## 10. Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/can-crossover-point
git log --oneline -1 main   # d061b2d, verified before branching

# Full sweep (all experiments + sharpenings), prints every table above
python3 -m pytest tests/test_can_crossover_point.py -q -s

# Targeted regression (unmodified prior rung + this rung's new file)
python3 -m pytest tests/test_can_ops.py tests/test_causal_attitude_networks.py \
  tests/test_can_migration.py tests/test_can_belief_quantization.py \
  tests/test_can_crossover_point.py -q
```
