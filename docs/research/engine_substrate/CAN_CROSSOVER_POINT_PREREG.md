# Crossover-point experiment for coarse-vs-fine causal-belief quantization — PREREG

**Status: PREREG. Written before any sweep in this rung executes.** Per this
session's own standing discipline against post-hoc rationalization —
`CAN_BELIEF_QUANTIZATION_PREREG.md` registered its own N=16 ceiling-effect
concern in advance of running it; this document matches that rigor for the
follow-on question that rung explicitly left open.

## 0. What this rung inherits, and what it corrects

`CAN_BELIEF_QUANTIZATION_RESULTS.md`'s 2×3 factorial (N ∈ {4,8,16}, coarse=3
values vs fine=9 values, ONE true-coupling seed per N) found the primary
"coarse degrades faster than fine as N grows" prediction **reversed** at
N=4/8 (coarse showed MORE, less-concentrated basins — the opposite of the
prediction) and only reaching near-parity at N=16 — flagged in that rung's
own PREREG (§2.3 point 4) in advance as a plausible **ceiling/density
effect** ("a complete graph... may simply be too strongly coupled for EITHER
condition to sustain multiple basins... density, not resolution, [would be]
the dominant lever"), not confirmation of a genuine crossover. That rung
also used only a SINGLE random-coupling draw per N — no seed replication, no
variance estimate — which the charter for this rung addresses directly (§2
below).

This rung's job, per the charter: (1) extend the N range past 16 in both
directions to see whether the observed convergence-at-16 is a genuine
crossover-in-progress or a saturation plateau; (2) replace the prior rung's
arbitrary coarse=3/fine=9 vocabulary with the LITERATURE-GROUNDED anchors
from `CAUSAL_GRANULARITY_POPULATION_DISTRIBUTION_RESEARCH.md` §8 (coarse =
2-3 bins, fine = 7 bins, tested range 2-12 bins straddling the Miller/
Preston-Colman human ceiling); (3) replace the single-seed-per-cell design
with seed replication so a trend can be told apart from per-draw noise; (4)
run a population-MIXTURE design (not a single fixed resolution per
condition) reflecting the CRT floor-heavy/ceiling-heavy split; (5) address
the three inherited sharpenings from the charter (arbitrary-solver
tractability via structure/compression, the oscillation/abandonment
question AT the crossover point specifically, and resolution-vs-density as
separate levers).

## 1. Quantization scheme — literature-grounded, replacing the prior rung's ad hoc vocabulary

Per `CAUSAL_GRANULARITY_POPULATION_DISTRIBUTION_RESEARCH.md` §8 point 3: "a
'coarse' test condition [anchored] to 2-3 bins and a 'fine' test condition to
7 bins, not higher... `CAN_BELIEF_QUANTIZATION_RESULTS.md`'s own 'fine'
condition used 9 values — close to, but one above, this literature's own
optimum; worth noting as a minor retrospective miscalibration."

This rung's quantizer generalizes the prior rung's centered-integer-`k`
scheme (which only produces ODD vocabulary sizes symmetric around zero) to
an **evenly-spaced V-point scale across [-1, +1] including both endpoints**
— the same shape Preston & Colman (2000) actually tested (Likert-type scales
from 2 to 11 response categories, not only odd/zero-centered ones): for a
V-point scale, `values = [-1 + 2*i/(V-1) for i in range(V)]`; a raw value `x`
rounds to its nearest such value. `V=2` gives `{-1, +1}` (no neutral
midpoint, matching Preston & Colman's own lowest tested category count);
`V=3` gives `{-1, 0, +1}` (identical to the prior rung's own "coarse"
condition, preserving continuity); `V=7` gives 7 evenly-spaced values
including 0 (the literature's measured psychometric optimum). This keeps the
in-frame-integer discipline (`CLAUDE.md`'s BASE-AS-DIMENSION section): the
in-frame datum is the integer index `i ∈ [0, V-1]`; the real-valued
`-1 + 2i/(V-1)` map is the cross-frame render, exactly the `scale2`/`modular`
precedent.

**Registered anchors for this rung:**
- **coarse**: V = 3 (the literature's low anchor, and the prior rung's own
  coarse condition — held for continuity).
- **fine**: V = 7 (the literature's measured optimum, correcting the prior
  rung's V=9).
- **resolution-sweep** (Experiment B, §2.2): V ∈ {2, 3, 4, 5, 7, 9, 11} —
  spans the literature's cited 2-11 tested range (Preston & Colman's own
  design), straddling the human ceiling as the charter requires, reported
  as `roughly 2-12` per the charter's own phrasing (11 is the largest V this
  rung tests; the literature's own upper bound in Preston & Colman was also
  11, plus a separate 101-point format not used here since it is not a
  "bin count" in the sense this design tests).

## 2. Experiment design — registered before running

### 2.1 Experiment A — the N-crossover sweep (primary)

**N ∈ {4, 8, 12, 16, 24, 32}.** Justification: {4, 8, 16} replicates the
prior rung's own tested points (bracketing its measured convergence at
N=16); {12} fills the gap between 8 and 16 to see whether the reversal-to-
convergence is smooth or sudden; {24, 32} extend past the prior rung's
ceiling to test whether convergence-at-16 was a genuine crossover-in-
-progress (fine should pull ahead of coarse as N keeps growing) or a
saturation plateau (both stay near-parity, or both degrade together,
regardless of resolution) — this is the literal question the charter poses
and the prior rung's own PREREG flagged as unresolved.

**Coarse (V=3) vs fine (V=7)**, same magnitude range `[-1,+1]`, isolating
resolution as the sole manipulated variable (unchanged from the prior
rung's own logic).

**Seed replication (the correction to the prior rung's single-draw
design):** for each N, **S = 5 independent random-coupling seeds** (not 1).
Each seed draws its own i.i.d. `Uniform(-1,1)` true coupling for every pair,
rounded separately into the coarse and fine vocabularies (same draw feeds
both conditions at that seed, preserving the prior rung's apples-to-apples
logic). Each (N, condition, seed) cell runs the SAME 40-restart multi-start
basin sweep as the prior rung (`tests/test_can_belief_quantization.py::
_basin_sweep`, reused verbatim — see §4 for the exact reuse citation), at
β=2.0, h=0 (matching the prior rung's held-fixed values, so this rung's
results are directly comparable to the prior rung's, not just internally
consistent).

**Total relaxations: 6 N × 2 conditions × 5 seeds × 40 restarts = 2400** —
cheap at the prior rung's own measured sub-millisecond-per-trial rate
(11/11 tests in 0.38s on this worktree, confirmed before writing this
PREREG).

**Reported per (N, condition):** mean and range (min/max across the 5
seeds) of basin_count, effective_basin_count, dominant_basin_fraction, mean
frustration, mean energy, mean absolute rounding error.

### 2.2 Experiment B — continuous resolution sweep (addresses the "2-12 bins" charter requirement directly)

At **N ∈ {8, 16, 32}** (a small, medium, and large anchor spanning
Experiment A's range), sweep **V ∈ {2, 3, 4, 5, 7, 9, 11}** with the SAME
seed-replication (5 seeds) and 40-restart basin sweep as §2.1, to see
whether the coarse/fine binary comparison in Experiment A is consistent
with a genuinely MONOTONIC resolution effect, a KNEE (sharp transition at
some V), a NON-MONOTONIC pattern (as the prior rung's own N=4/8 reversal
would predict if it generalizes: MORE bins sometimes producing MORE
fragmentation, not less), or NO clean pattern at all (noise-dominated).

**Total relaxations: 3 N × 7 V-levels × 5 seeds × 40 restarts = 4200.**

### 2.3 Experiment C — population-mixture design (the charter's required "realistic population spread" check)

Per `CAUSAL_GRANULARITY_POPULATION_DISTRIBUTION_RESEARCH.md` §7 point 4 /
§8 point 2: real populations do NOT look like one Gaussian around a mean
resolution — CRT shows a floor-heavy (novice/low-exposure) subpopulation and
a ceiling-heavy (expert/high-exposure) subpopulation, roughly a **2.5×
swing in mean score** between them, and mixing the two subgroups without
controlling for the split produces an apparent bimodal-leaning population
shape that reflects two coherent regimes, not one smooth continuum.

**Design, registered before running:** the mixture applies to WHICH
RESOLUTION AN INDIVIDUAL AGENT'S WHOLE NETWORK USES, not to individual
edges within one network — this matches how the cited literature actually
measures the construct (CRT, emotional granularity, and numeracy are all
INDIVIDUAL-difference measures: one person has one characteristic
resolution across the belief network being probed, not a different
resolution per belief-pair). Two mixture components:
- **Component 1 ("floor/naive"), weight π₁ = 0.5**: V drawn uniformly from
  `{2, 3}` — the literature's own low/coarse anchor band.
- **Component 2 ("ceiling/exposed"), weight π₂ = 0.5**: V drawn uniformly
  from `{6, 7, 8}` — centered on the literature's optimum, with a small
  spread reflecting real inter-individual variation within the "exposed"
  regime. Component means are 2.5 and 7, a **3.5× ratio** — deliberately
  reported honestly as LARGER than the CRT-literature's own ~2.5× swing
  (§8 point 4 of the population doc), not force-tuned to match it exactly,
  because the two constructs (a 0-3 pass/fail CRT score vs. a resolution
  bin count) are not on a directly transferable scale, exactly as that
  document's own §8 point 4 says ("the MAGNITUDE of the swing is the
  transferable fact, not its precise value" — 2.5-3.5× is the same order of
  magnitude, not a precise match, and this is stated plainly rather than
  massaged to look closer).

**K = 30 simulated individuals per N**, at **N ∈ {4, 8, 16, 32}** (a subset
of Experiment A's range: smallest, two middle, largest — enough to see
whether the mixture reproduces Experiment A's own N-dependent pattern
without the full 6-point sweep at population scale). Each individual draws
its own component (Bernoulli π₁/π₂), its own V from that component, and its
own i.i.d. true-coupling draw (independent per individual — a real
population does not share one coupling structure). Each individual's basin
sweep uses **15 restarts** (reduced from Experiment A's 40, to keep this
experiment's total relaxation count bounded — this is a per-individual
population-level comparison, not a single high-precision estimate, so lower
per-individual precision traded for population breadth is the right
tradeoff, stated as a design choice).

**Total relaxations: 4 N × 30 individuals × 15 restarts = 1800.**

**What counts as "the same crossover structure holds," registered in
advance:** group Experiment C's individuals by which component they were
drawn from at each N; compare component-1 vs component-2 mean
dominant_basin_fraction/effective_basin_count/frustration against
Experiment A's own coarse-vs-fine means at the SAME N. If the direction and
approximate magnitude of the component-1-vs-component-2 gap tracks
Experiment A's coarse-vs-fine gap at each shared N, the fixed-condition
result is confirmed to generalize under a realistic mixed population; if the
mixture's added within-component V variance and pooled random-coupling
variance washes out a pattern Experiment A found cleanly, or produces a
DIFFERENT direction, that is reported as a genuine, informative divergence
between "clean two-condition comparison" and "realistic population spread"
— not smoothed into agreement.

### 2.4 Predictions, registered before running

1. **Primary honest-null clause (fully acceptable, registered as such):** if
   coarse and fine stay within each other's seed-to-seed range at every N in
   {4,...,32} (i.e., no N at which the 5-seed mean gap exceeds roughly one
   pooled seed-SD in a consistent direction), this is reported as **NO
   crossover found in the tested range, noise-dominated or genuinely
   parity** — a complete, acceptable result, not reinterpreted.
2. **Genuine crossover, operationalized precisely:** an N* exists such that
   for all N ≥ N* tested, fine's mean dominant_basin_fraction exceeds
   coarse's by more than the larger of the two conditions' own seed-range at
   that N, AND fine's mean effective_basin_count is lower than coarse's by
   the same non-overlap standard, AND this holds for at least two
   consecutive tested N values (ruling out a single noisy point). If this
   pattern is found, N* is reported as the smallest N meeting it.
3. **Plateau-not-crossover (a specific, named alternative to distinguish
   from #2):** if coarse and fine converge toward each other (as the prior
   rung found at N=16) and STAY converged for all larger N tested, without
   fine ever pulling ahead by the §2.4.2 standard, this is reported
   precisely as "density/frustration saturation, not a resolution
   crossover" — the prior rung's own named candidate explanation, now
   tested past its original ceiling rather than assumed.
4. **Reversal-persists (a third named alternative):** if the small-N
   reversal from the prior rung (coarse MORE basins, LESS concentrated) not
   only fails to reverse-back but continues or strengthens as N grows past
   16, that is reported as "the naive coarse-collapses intuition is wrong
   across the full tested range," a stronger and cleaner null than the
   prior rung could claim from N≤16 alone.
5. **Resolution-sweep (Experiment B) honest-null clause:** if no monotonic
   or knee-shaped trend across V ∈ {2,...,11} is distinguishable from noise
   at any of the three anchor N values, that is reported as "resolution,
   within the literature's own tested range, is not a clean lever on this
   design's outcome metrics" — acceptable and reportable as-is.

## 3. The three inherited sharpenings — registered approach

**(a) Arbitrary-solver tractability — a smaller, scoped check, NOT the
compression layer itself.** Per the charter and per
`CAN_BELIEF_QUANTIZATION_RESULTS.md` §7's own explicit scoping ("building a
real shape-recognising CAN-coupling compressor... is a full rung of its
own... correctly out of this rung's bounded scope"), this rung does NOT
build a `CausalLinkageShape` codebook or any recognize/mint rule pair. What
IS in scope and registered here: a **structured-vs-unstructured coupling
generator comparison**, testing whether a network whose TRUE couplings have
recognizable STRUCTURE (redundancy a future compressor could exploit)
behaves differently under the N-crossover question than the i.i.d.-random-
sign draw Experiment A uses throughout. Structured generator: partition the
N concepts into `ceil(N/4)` blocks of ≤4; within a block, couplings are
`Uniform(-1,1)` draws around one of two block-level anchors (+0.7 or -0.7,
assigned per block) plus small i.i.d. noise (`Uniform(-0.15,+0.15)`);
across-block couplings are i.i.d. `Uniform(-1,1)` as before (representing a
smaller admixture of genuinely unstructured cross-cutting disagreement, per
`CAN_BELIEF_QUANTIZATION_RESULTS.md` §3 point 1's own named next-step: "a
structured-truth design... a 'coherent core + adversarial noise' draw").
This is run at the SAME N range as Experiment A, coarse vs fine, 5 seeds,
40 restarts — structurally identical to Experiment A except for the
coupling generator — so a direct comparison is possible. **Registered
prediction:** if compression/structure recognition would help an arbitrary
solver scale, the structured condition should show a HIGHER N* (crossover
delayed, or basin structure better-preserved at high N) than the
unstructured condition, because a redundant/blocky coupling matrix is
exactly the shape a shape-recognizing compressor could exploit even though
none is built here; if structured and unstructured show the SAME N*/
pattern, that is reported as evidence resolution (not structure) is the
dominant lever at the scales tested, and named as informative either way.

**(b) Oscillation/abandonment AT the crossover point specifically —
distinguishing it from basin-count degradation as a separate phenomenon.**
Reusing `_oscillates`/`_relax_with_fields` verbatim (§4 below cites the
exact file:line), this rung runs the SAME cohere-vs-fail-to-cohere probe
(fixed nonzero external field per node, max_iter=400 vs 401 parity check)
at the SPECIFIC N values Experiment A's own data flags as interesting (the
smallest N tested, the prior rung's N=16 convergence point, and the
largest N tested), for both coarse and fine, across the SAME 5 seeds used
in Experiment A (reusing the identical true-coupling AND field draws so the
oscillation result can be directly cross-referenced against that seed's own
basin-sweep numbers from Experiment A). **Registered question:** does
oscillation (persistent 2-cycle, the "abandonment" signature) correlate
with LOW basin-count/high dominant-fraction (i.e., is abandonment what
happens instead of a well-separated multi-basin landscape — the two
phenomena coincide) or does it occur independently of where a given
(N, seed, condition) cell falls on the basin-count/frustration measures
(i.e., abandonment is a separate axis, not simply "basin-count collapse
under another name")? Both outcomes are informative and will be reported
as measured, not forced toward either reading.

**(c) Resolution vs. density/structure — read off directly from (a) and
the N-sweep itself.** If Experiment A shows the SAME qualitative
coarse-vs-fine pattern (reversed-then-converged, or crossover, or parity)
regardless of N (i.e., resolution's effect is stable across network sizes),
that favors resolution as the dominant lever. If instead the pattern
changes qualitatively with N (e.g., reversed at small N, parity at medium N,
crossover at large N) that is direct, already-partially-established
(prior rung) evidence that DENSITY/graph-scale interacts with resolution
rather than resolution alone driving the outcome — consistent with the
prior rung's own explicit finding that its "N-scaling prediction reversed at
small N." Experiment (a)'s structured-vs-unstructured comparison adds a
THIRD axis (coupling structure, independent of both N and resolution) to
this same question. This rung will report, honestly, which of {resolution
alone, density alone, structure alone, some combination} the combined data
supports — not force a single-cause narrative if the data shows an
interaction.

## 4. Reused methodology — exact citations, not reinvented

- **Multi-start basin discovery** (`_basin_sweep`,
  `tests/test_can_belief_quantization.py:66-116`): re-seed every Concept's
  `state` to an i.i.d. `{-1,+1}` draw, call `mt_mean_field_marginal`,
  cluster converged marginals (L2 < 0.3 merge), report
  `basin_count`/`effective_basin_count` (exp of Shannon entropy over
  cluster occupancy)/`dominant_basin_fraction`/mean frustration/mean
  energy. Reused **verbatim**, imported into this rung's own test file, not
  reimplemented.
- **Network construction** (`_build_complete_network`, same file
  `:53-63`): complete graph, `has_concept` + `causal_influence` edges,
  `external_field=0.0` default. Reused verbatim.
- **Oscillation probe** (`_oscillates`/`_relax_with_fields`, same file
  `:337-365`): fixed nonzero external field per node, fixed all-zero start,
  max_iter parity comparison (400 vs 401 differing-parity gap vs 400 vs 402
  same-parity control). Reused verbatim for §3(b).
- **In-frame-integer/cross-frame-map quantizer discipline**: the prior
  rung's `_round_to_vocab` (centered-integer-`k`) is GENERALIZED (not
  discarded) to the evenly-spaced V-point scheme in §1 above, because the
  literature-grounded target (Preston & Colman's actual 2-11 category
  design) is evenly-spaced-inclusive-of-endpoints, not only odd/zero-
  centered; V=3 is numerically identical to the prior rung's own coarse
  condition, so this is a strict generalization, not a silent redefinition
  that breaks comparability.
- **Engine surface**: `mt_mean_field_marginal`, `mt_frustration_given_state`,
  `mt_energy` (all PyO3-exposed, `runners/dsl/src/py.rs`, confirmed already
  live and unchanged by the prior rung's own read of `can_ops.rs`). No new
  Rust, no new `can_ops.rs` function, per the charter's explicit scope
  boundary — confirmed sufficient before writing this PREREG by re-running
  the prior rung's own test suite (§ above, 11/11 green, 0.38s) in this
  worktree.

## 5. What this rung will NOT establish (named in advance)

1. Whether any measured crossover (or its absence) reflects a REAL
   cognitive fact about human belief networks, as opposed to an artifact of
   this specific mean-field/complete-graph/β=2.0 operationalization — the
   same caveat the prior rung's own §9 named and this rung inherits
   unchanged.
2. The compression/shape-recognition layer itself (explicitly out of
   scope per the charter) — §3(a)'s structured-vs-unstructured check is a
   proxy for whether such a layer WOULD help, not a build or measurement of
   the layer itself.
3. Sparse (non-complete) graph topologies — this rung, like the prior one,
   tests only complete graphs; whether a sparser, more realistic topology
   changes the crossover picture is a named, un-run follow-on.
4. Any connection to Bigville or the Matthew-effects/selection-feedback
   mechanism — both explicitly out of scope per the charter.

## 6. Worktree

`/home/matt/ozmadev/ocelot-worktrees/can-crossover-point`, branch
`can-crossover-point`, base `main @ d061b2d`
(`Merge causal-granularity-population-distribution-research: grounding the
crossover-point PREREG in real numbers`).
