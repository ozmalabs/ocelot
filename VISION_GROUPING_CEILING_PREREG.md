# THE GROUPING CEILING — pre-registration

**Written and committed BEFORE any number.** Seeds **103000–103999**.
Branch `worktree-agent-ab36b4c2cad253f28`, base `main` HEAD **`91e367f0`**.
Engine **`9931e144d19b`**, `own` build via `scripts/engine_build.sh` (this rung
adds no Rust; the build is this tree's own so provenance reads `own`).

---

## §0.1 SEED CLAIM — VERBATIM (§3 clause 8)

```
$ python3 -c "import sys;sys.path.insert(0,'scripts');from seed_claim import check_claim;print(check_claim(103000,103999)[1])"
SEED CLAIM 103000-103999: CLEAN -- no collision DETECTED.
  Scope: 807 files with seed sinks; 497 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

**497 unresolved sink sites, tree-wide, counted not discarded.** A CLEAN
verdict means *no collision detected*, never *no collision exists*.

---

## §0.2 WHAT THIS RUNG IS, AND WHAT IT REFUSES TO BE

The peer-competition rung established the constraint that ends the mint-predicate
line: **minting is a SELECTION, and the component field's median member is ONE
CELL** (mean 2.06, p90 4–5, largest anywhere 66 = 20% of a 324-cell tile). Four
rungs operated downstream of that ceiling. The named lever is upstream: *"what
makes two cells the same region"* — the exact-value flood at k=16.

The brief's instruction is **CHARACTERISE BEFORE YOU BUILD**, and it names the
legitimate outcome *"no mechanism is warranted, here is why."* This rung is a
**characterisation with no mechanism**. It adds no rule, no flag, no seed byte,
no Rust. Every arm is a read-out over a component field computed outside the
graph and **reconciled against the graph's own labelling before any number from
it is believed**.

The evidence that makes this hard is already on the record and is NOT re-tested
as though it were open: the value-flood rung measured that relaxing admissibility
makes protos **strictly fewer** (234 → 78 → 68 multi-cell). That is a **refuted
hypothesis**, not an untried one. This rung does not propose to loosen the flood.
It asks the prior question: **what shape is the size distribution across the whole
family of value-admissibility relations, and is a few-and-large regime anywhere in
it at all?**

---

## §1 HYPOTHESES (two-sided, per §3 clause 1)

**H1 — THE DEGENERACY HYPOTHESIS.** Over the family of value-admissibility
relations (quantizer coarseness `k`; chaining tolerance `τ`), the component-size
distribution is **degenerate**: every configuration is either a field of
singletons or a single giant component, with no configuration placing the typical
cell in a region of the target size. *Two-sided:* the alternative is that some
configuration lands in the target band, in which case a grouping mechanism IS
warranted and this rung names the configuration it falls out of.

**H2 — THE CHAINING HYPOTHESIS.** The value-flood rung's measured failure of
loosening (`|Δ|≤1`, `|Δ|≤2` → fewer protos) is caused by **transitive chaining**,
not by tolerance as such: a chain of individually-admissible steps spans a value
range far larger than the step it admits, so the background walks into the figure.
*Discriminator:* the **within-component value RANGE**. Under binning it is bounded
by one bin **by construction**; under chaining it is unbounded and **measured**.
*Two-sided:* if chained components' ranges stay near one step, chaining is not the
mechanism and the loosening failure is about tolerance itself.

**H3 — THE MATERIAL HYPOTHESIS.** A target-sized spatial neighbourhood of a
natural frame contains **more internal luminance variation than the contrast at
its own boundary**, so no value-admissibility relation can unify it while
respecting edges. *Two-sided:* if internal spread is well below boundary contrast,
value flooding is adequate material and the failure is in the mechanism's
parameters.

**H4 — THE APERTURE.** Some of the observed ceiling is the 18×18 tile cutting
regions, not the flood fragmenting them. *Two-sided:* if whole-frame components
have the same size distribution as tiled ones, the tile is not implicated.

---

## §2 THE STATISTICS, EXACTLY

Unit of analysis is the **TILE** (§4), never the component. 2 corpora × 7 frames
× 16 tiles = **224 tiles per corpus**, identical to the peer rung's sampling.

For a component field (a partition of a tile's cells):

- `size` — cells per component.
- **`cellsize`** — the **size-biased** distribution: for each CELL, the size of
  the component it belongs to. *This is the statistic the arc has never
  reported.* Median component size is dominated by singletons; the question
  "does a typical cell live in a region" is answered only by `cellsize`.
- **`giant`** — largest component / 324 cells. The percolation order parameter.
- `n_comps` — components per tile.
- **`vrange`** — within-component raw-luminance range (max−min over the
  component's cells, in the frame's own 0–255 units). H2's discriminator.

Reported per configuration as: median / mean / p90 / p99 / max over the pooled
population, **plus per-tile medians with a 10,000-resample bootstrap CI over the
224 tiles.** No pooling across corpora.

### 2.1 The arms (sweep axes, reported IN FULL — §3 clause 6)

Two admissibility families over the same frames:

- **BIN(k)** — the incumbent: exact equality of the per-frame min/max
  `k`-level quantization. `k ∈ {2, 3, 4, 6, 8, 11, 16, 23, 32, 45, 64}`
  (a ≈√2 ladder spanning 5 octaves; k=16 is the incumbent and is IN the ladder).
- **CHAIN(τ)** — admissibility `|Δval| ≤ τ` at the incumbent k=16,
  `τ ∈ {0, 1, 2, 3, 4, 6, 8}`. `τ=0` is byte-identically BIN(16).

**These are SWEEP AXES, not chosen constants.** Every level is reported; no level
is selected by an outcome. Nothing in this rung's decision procedure compares a
measured quantity against a literal (§13; verified by `scripts/gate_audit.py`
against the measurement module, run as its own step).

### 2.2 The target curve — the "60-cell region" made non-arbitrary

The brief asks what would have to change to produce a **60-cell region**. 60 is
the brief's number, and a single target would be a magic number wearing a goal's
clothes. So every target-dependent quantity is reported as a **CURVE** over
`T ∈ {10, 20, 40, 60, 100, 150}` cells, and the 60 is read off the curve rather
than assumed. `T=324` (the whole tile) is the degenerate end and is reported too.

---

## §3 THE MEASUREMENTS

**M0 — RECONCILIATION (runs FIRST; nothing downstream is believed without it).**
The component field is computed in numpy. It is checked against the substrate's
own `glabel` partition on the enclosed cells of live tiles under the standing
G72/k=16 configuration, and against the peer rung's **published** aggregates:
components/frame **721.0 (C1)** and **568.3 (C2)**, component median **1**,
max **66 (C1) / 50 (C2)**. *A diagnostic must not be computed by the component it
checks* — hence numpy vs graph, not graph vs graph. **Any partition disagreement
voids the run.**

**M1 — THE SIZE DISTRIBUTION AT THE STANDING CONFIGURATION.** Full histogram of
`size` and of `cellsize`, both for ALL components of the tile and for the ENCLOSED
subset (what minting selects from). Plus the fraction of cells living in
components of size ≥ T, as a curve over T.

**M2 — THE SWEEP.** `size`, `cellsize`, `giant`, `n_comps` for every BIN(k) and
every CHAIN(τ). The decision object is the **front**: `median(cellsize)` against
`median(giant)` as the admissibility parameter increases monotonically.

**M3 — CHAINING vs BINNING.** `vrange` for every arm. Under BIN it is bounded by
one bin by construction (a structural check, asserted, not measured); under CHAIN
it is measured. Matched-grain comparison: CHAIN(τ) admits a local step of τ/16 of
the dynamic range; BIN(k′) admits any difference inside one bin of width 1/k′.
The two are **not identical** — CHAIN is locally more permissive AND chains — and
that non-identity is stated here rather than hidden in a matching rule.

**M4 — THE APERTURE.** The identical component computation on the whole 72×72
frame vs per-tile. Reported: whole-frame `size`/`cellsize`/`giant`, and the
fraction of tiled components that touch a tile edge (i.e. are candidates for
truncation).

**M5 — THE MATERIAL.** For every cell, the disc of area ≈ T centred on it:
`spread(T)` = max−min RAW luminance inside. Against `step` = the distribution of
|Δ| over 4-adjacent raw-luminance pairs, of which the upper tail is "the edges".
Reported as the **required tolerance ratio** `spread(T) / step_p95` per tile, as
a curve over T — and as the **required k**: the coarsest quantization at which a
T-cell disc could be one exact-value component, `k_req(T) = range / spread(T)`,
whose distribution is then read back against M2's `giant` at that k. If the k
required to unify a T-cell region is a k at which the field has already
percolated, the mechanism is self-contradictory **in its own measured units** and
no parameter rescues it.

---

## §4 CONTROLS — every one of them, and what each protects (§1, §6)

1. **RANDOM INPUT (§1 clause 1).** The identical sweep on iid uniform speckle
   fields (seeds **103000–103099**, 100 fields). If the front is degenerate on
   speckle AND on natural frames identically, the degeneracy is a property of
   value flooding on any field. If they differ, **that difference is the
   structure natural frames actually offer**, and it is the finding.
2. **IDEAL EXEMPLAR (§1 clause 2).** A synthetic field containing a genuine
   T-cell constant-valued region on a different-constant ground. The instrument
   **must** report exactly one T-cell component and a WIDE plateau across the
   sweep. If it does not, a degenerate front on natural frames is my labeller's
   defect and nothing is claimed.
3. **THE GRADED EXEMPLAR — the calibration that puts the answer in units.** The
   same T-cell region with internal noise of increasing amplitude against a fixed
   boundary contrast. The plateau dies at some measured internal-spread /
   boundary-contrast ratio. **That ratio is the instrument's own resolving limit**,
   and M5 measures natural frames in exactly those units. This is what makes H3
   answerable rather than rhetorical.
4. **ARM LIVENESS / EXPOSURE (§1 clause 4; "a null needs exposure").** Every arm
   must produce a partition DISTINCT from its neighbours on real tiles, and every
   reported statistic must be computed over a non-zero population. Counts of
   triggers are reported beside every statistic. A configuration that produces an
   identical partition to another is reported as **structurally inert**, not as a
   null.
5. **§9 BY CONSTRUCTION.** No seed, rule, flag, node, or Rust changes.
   `git diff -- seeds/ runners/` must be EMPTY. Oracle
   `bash scripts/rung7_vision_bench.sh` before and after.
6. **THE SPECKLE FLOOR IS NOT COPIED FORWARD AS A FACT.** The peer rung measured
   2/100 where 0/100 was committed and restated it as **≈0.63% [0.17, 2.25]**.
   This rung inherits the *restated* number. **No `== 0` assertion appears
   anywhere in this rung.**

---

## §5 DECISION RULE, INCLUDING WHAT A NULL MEANS

**The decision object is the front (M2), read against the curve (M5).**

- **OUTCOME A — DEGENERATE (H1 confirmed).** As the admissibility parameter
  increases, `median(cellsize)` **jumps over** the target band — no configuration
  places the median cell in a T-cell region while the giant component is still a
  minority of the tile. Verdict: **NO MECHANISM IS WARRANTED in this family.** No
  tolerance, no quantizer coarseness, and no combination of them produces
  few-and-large, and the lever is not a value-admissibility relation at all.
  **This is a positive finding about where the constraint lives, and it is
  reported as the result, not as a failure.**
- **OUTCOME B — A WINDOW EXISTS.** Some configuration lands the front in the
  band. Then the rung reports the configuration, **and what the configuration
  falls out of** — and if the honest answer is "nothing; I would have to choose
  it against the outcome I wanted", it is reported as a §13 gap in the mechanism
  and **still not built** (§13: the fix for a failed constant is never to tune it).
- **OUTCOME C — THE INSTRUMENT FAILS ITS OWN CONTROLS.** M0 disagrees with the
  graph, or control 2 fails. Nothing is claimed and the rung reports the defect.

**A null here is informative and is stated as such:** it closes the entire
value-admissibility family with a measurement rather than an argument, which is
exactly what four rungs downstream of the mint predicate did not have.

**Exactly the listed measurements. No sweeps beyond §2.1's declared ladders. No
re-runs.** A further attempt needs a new pre-registration with a new
mechanism-level hypothesis.

---

## §6 MY PREDICTIONS, IN ADVANCE, WITH PROVISOS (§3 clause 7)

- **P1 — H1 CONFIRMED, and the transition is SHARP.** I predict the front is
  degenerate: `median(cellsize)` stays ≤ 4 cells until `giant` exceeds half the
  tile, and there is no BIN(k) or CHAIN(τ) at which the median cell lives in a
  40–150 cell region with `giant` below half. *Proviso that would break it:* if
  natural frames have enough piecewise-constant structure at coarse k, there
  could be a genuine plateau around k=4–6. If that plateau exists I expect it on
  C1 (cartoon, cel-shaded, genuinely piecewise-constant) and NOT on C2
  (live-action). **If the two corpora differ here, that difference is the most
  important number in the rung** and it means the ceiling is a property of the
  material, not of the mechanism.
- **P2 — H2 CONFIRMED.** I predict CHAIN's `vrange` at τ=1 already exceeds 4×
  the admitted step, and at τ=2 spans most of the dynamic range — i.e. the
  loosening failure is chaining. *Proviso:* if `vrange` at τ=1 is ≈1 step, I am
  wrong and tolerance itself is the problem.
- **P3 — H3 CONFIRMED at T=60, and this is the load-bearing prediction.** I
  predict `spread(60) / step_p95 > 1` for the majority of tiles on **both**
  corpora — a 60-cell neighbourhood varies internally by more than the strongest
  5% of adjacent-pair steps — and therefore `k_req(60)` lands at a k where M2's
  `giant` is already large. *Proviso:* C1 cartoon may beat this; if C1 passes and
  C2 fails, the honest statement is that value flooding works on cel-shaded
  content and not on photographs, which is a scope claim, not a mechanism.
- **P4 — H4 REFUTED (the aperture is NOT the ceiling).** I predict whole-frame
  components have a size distribution close to the tiled one at k=16 — median
  still 1 — because a field of singletons is not being cut by anything. *Proviso:*
  if whole-frame `giant` is much larger than tiled `giant` at the same k, the tile
  IS doing work and my P1 reading is confounded by the aperture.
- **P5 — SPECKLE AND NATURE DIFFER, BUT NOT ENOUGH.** I predict natural frames
  have visibly more mass in the size tail than speckle at matched k (there IS
  structure), and that the FRONT is nonetheless the same shape (the structure is
  not enough to make a window). *Proviso:* if the fronts are identical, the
  measurement is not seeing image structure at all and I should suspect my
  instrument before believing H1.

**I record now that P1, P3 and P5 are variations of one bet** — that the material
is not piecewise-constant at object scale. They cannot independently confirm each
other. P2 and P4 are separate bets.

---

## §7 SEEDS

| seed | use |
|---|---|
| **103000–103099** | 100 iid uniform speckle fields, control 1 (the random-input floor and the matched-k sweep on noise) |
| 103100 | reserved: graded-exemplar noise draws (control 3) |
| rest of 103000–103999 | not drawn |

Real tiles consume no RNG. Consumption is measured with `scripts/seed_audit.py`
and reported with its `unknown_sinks` count, never asserted.
