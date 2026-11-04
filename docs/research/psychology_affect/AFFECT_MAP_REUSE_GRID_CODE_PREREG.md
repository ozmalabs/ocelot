# AFFECT MAP REUSE + GRID-CODE SYMMETRY — does the spatial quanta machinery carry a valence–arousal map unchanged, and does Ocelot's map have a 6-fold code? — PRE-REGISTRATION (block 367000)

**Status: PRE-REGISTRATION, written 1 November 2026 BEFORE the confirmatory test
exists.** Every predicted number below is computed analytically (Appendix A) from
the lattice, the control set and the declared sample sets. None is read from a run
of the substrate. The confirmatory test must reproduce the gated numbers. A
deviation is reported as found: it is either a harness error to fix and declare,
or a finding about the substrate.

## 0. Seed claim (verbatim, run at prereg time)

```
$ python3 scripts/seed_claim.py 367000 367999
SEED CLAIM 367000-367999: CLEAN -- no collision DETECTED.
  Scope: 1373 files with seed sinks; 877 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

Block **367000** (range 367000–367999). The rung is **deterministic**. Every
sample set is a full enumeration fixed below, and no number is drawn from the
block. The block is claimed for hygiene and successor safety.

## 1. The idea

Ma and Kragel (2026, *PLOS Biology*, doi:10.1371/journal.pbio.3003795) report
fMRI evidence from 18 analysed participants. Human ventromedial prefrontal cortex
(vmPFC) encodes emotion concepts in a two-dimensional valence–arousal space with
**hexadirectional (6-fold) modulation**, the fMRI signature of grid-like coding.
Before this, that format was reported for physical space (Doeller, Barry &
Burgess 2010, *Nature* 463:657–661) and for abstract concept spaces
(Constantinescu, O'Reilly & Behrens 2016, *Science* 352:1464–1468). The grid
signal generalised across faces and phrases and was largely shared across people.
It did **not** track choices. A separate **distance** signal in vmPFC predicted
trial-by-trial judgements. The authors state that their design cannot distinguish
Euclidean from city-block distance.

Three properties of Ocelot bear directly on this, and their status differs:

1. **A domain-general map format exists.** `runners/dsl/src/space_quantize.rs`
   decomposes any N-dimensional integer belief into axis-aligned `SpaceQuantum`
   boxes with `portal` edges. Nothing in it is specific to physical space.
   (Implemented.)
2. **Structure and the choice signal are separated by construction.** The box and
   portal geometry is minted by the Rust primitive. Choice is driven only by
   `qdist`, the Bellman distance-to-goal owned by `qf_relax`, with an Argmin in
   `qf_hop_route`, and inside the avatar's own box by the per-dimension sign step
   in `qf_hop_direct` (`seeds/quanta_navigation.json`). (Implemented.)
3. **Affect does not use that map.** Affect lives on one `AffectiveState` node per
   agent (`seeds/affective_state_core.json`). `em_readoff`
   (`seeds/core_emotions.json`) writes valence as a sign in {−1, 0, +1}, with
   arousal as a magnitude borrowed from the appraisal that fired. No affect state
   space is ever navigated, and no transitions between affective states are
   represented. (A gap, stated before the run.)

The rung asks two questions.

- **Part A (grid code).** Does Ocelot's spatial map have a 6-fold directional code?
  **Pre-registered expectation: no.** The lattice is Z^N, and moves run along one
  axis at a time, so the code must be 4-fold.
- **Part B (reuse).** Can the **unchanged** spatial machinery carry a
  valence–arousal map? If it can, what does its distance signal actually encode?
  **Pre-registered expectation:** reuse works with zero mechanism change. In an
  open affect plane, however, `qdist` is constant, so the map is metrically blind,
  and the only distance information is city-block step count from pose
  arithmetic.

**This is a mechanism demonstration on this substrate. It is not an empirical
claim about humans.** The human result fixes what a domain-general cognitive map
would have to show. Whether Ocelot shows it is the measured question.

### 1.1 The source study (read 1 November 2026)

**Citation.** Yumeng Ma and Philip A. Kragel, "Emotion knowledge is structured in
a grid-like coordinate system in the human ventromedial prefrontal cortex",
*PLOS Biology*, Short Report. doi:10.1371/journal.pbio.3003795. Received 20 April
2026, accepted 20 October 2026, published 2 November 2026. When read, the page
was marked "uncorrected proof", so check the final version before citing exact
figures.

**Design.**
- **Participants.** 20 healthy adults were recruited in Atlanta and 18 analysed
  (13 female; age mean 39.56, SD 13.19, range 21–60). One withdrew with
  claustrophobia, and one was excluded for head motion. Of the 18, one did not do
  the post-scan ratings.
- **Power.** For the primary one-tailed comparisons, n = 18 gives 80% power for
  d = 0.61.
- **Face stimuli.** 78 Karolinska (KDEF) photos of 26 identities in 7 categories
  (happy, surprised, angry, afraid, sad, disgusted, neutral). Same-identity pairs
  were morphed into 84 face trajectories.
- **Phrase stimuli.** 126 phrases from 8 everyday settings, used in 124 phrase
  sequences. The candidate phrases were **generated with ChatGPT-4o** and screened
  by a 10-person pilot.
- **Task.** On each trial participants saw one trajectory through affective space
  and judged whether valence, or arousal (probed at random), increased, decreased
  or stayed the same. There were 4 runs and 36.5 minutes of task time.
- **Analysis.** Grid orientation was estimated on held-out data, and pattern
  similarity was compared between trial pairs aligned and misaligned to it
  (mod 60°). A 6-fold model was tested against 3-, 4-, 5-, 7- and 8-fold control
  periodicities. Distance effects were tested with partial-least-squares encoding
  models under leave-one-participant-out cross-validation.

**Findings.**
- **6-fold modulation in vmPFC.** Δr = 0.0072, 95% CI [0.0031, 0.0115], d = 0.78,
  p = .0014. It was specific to 6-fold (6-fold versus other folds: d = 0.92,
  p = .0005). It survived a subsampling control for unequal pair counts, and none
  of the control folds was significant.
- **No grid signal in entorhinal cortex**, which the authors call unexpected.
- **Partial cross-modal generalisation.** A grid orientation estimated from phrase
  ratings predicted faces (d = 0.62, p = .0096), but faces did not predict phrases
  (d = 0.02, p = .47).
- **Shared structure.** The structure was largely shared across people and was
  less well captured by individual post-scan ratings.
- **Grid code separate from choice.** Grid magnitude did not vary with behavioural
  choices. Separate distance-related vmPFC signals predicted trial-by-trial
  judgements.

**Limits the authors state.**
- Single-unit recordings are needed to show periodic tuning in individual neurons.
- The in-scanner task did not require combining valence and arousal, which may
  explain why grid coding and choice came apart.
- The design does not distinguish Euclidean from city-block distance. This is the
  open point G-B2 makes a prediction about.
- fMRI cannot show that vmPFC is necessary.

**Data and code.**
- Data: OpenNeuro ds008948 v1.0.0, and OSF https://osf.io/5fkuy/
- Code: https://github.com/ecco-laboratory/EmotionConceptNavigation and
  doi:10.5281/zenodo.23424201

### 1.2 Context: why this rung, and what was checked before writing it

**How it arose.** The study was raised in the Graphic Equalisation (GE) research
workspace (`../graphic-equalisation`) as bearing on GE's claims. On GE's side it
connects in three ways:

1. **"One core" across domains.** If the brain reuses one map format for physical
   space, concepts and emotion, that is an independent empirical case of reusing a
   format rather than adding a subsystem per domain.
2. **Coordinates are held by the frame.** GE treats space as a belief the frame
   holds, not a grid in the world (GE book, old chapter 7, "Space as a Belief").
   It treats time as constructed from change and ordered records (GE Paper 01j).
   The study's affective "space" is likewise built from learned regularities and
   is held in the brain, not present in the stimuli.
3. **Representation separate from evaluation.** The grid code (structure) and the
   distance code (what drives the judgement) came apart in the study. GE separates
   a representation from the evaluation that uses it.

**Where it does not support GE.** GE's emotion model (GE book, old chapter 10)
builds emotions as couplings of a small basis: arousal, appraisal, attribution,
bond and window of tolerance. The study finds a two-dimensional valence–arousal
map. This is not a contradiction, because the study measures **knowledge of
emotion concepts** judged in faces and phrases, not how emotions arise. But the
study cannot be cited as confirming GE's basis.

**Why Ocelot.** GE uses Ocelot as its executable proving ground. Ocelot already has
the study's two architectural ingredients, a domain-agnostic map and a
structure/choice split, but does not use them for affect. That makes the study a
direct, runnable question for Ocelot rather than an analogy.

**Read-only audit of Ocelot made before writing this prereg (1 November 2026).**

- **Spatial map.** `runners/dsl/src/space_quantize.rs` builds a Z^N integer
  lattice, decomposes it greedily into maximal axis-aligned boxes, and links
  face-adjacent boxes with portals of `cost` = 1. It has no hexagonal lattice, no
  multiple scales and no periodic or phase code. Its Rust tests and
  `tests/test_quanta_navigation_migrated.py` cover corridors, rooms, 3D, two
  bodies, splits, frontiers and focus.
- **Value signal.** `seeds/quanta_navigation.json` holds the value side.
  `qf_relax` performs `Q.qdist ← min(Q.qdist, R.qdist + cost)` over portals with
  `oneway_ok`. `qf_hop_route` takes an Argmin over neighbour `qdist + cost`, and
  `qf_hop_direct` takes a per-dimension sign step inside the avatar's own box.
  `docs/research/ls20/LS20_MAPNAV_RESULTS.md` reports exact route-equivalence to
  Manhattan distance on open maps.
- **Learned axes.** `seeds/affordance_basis.json` and `seeds/principal_axes.json`
  learn each control's displacement and the frame's axes from observed action
  outcomes. This is a motor basis, not a map metric learned from transition
  statistics.
- **Affect.** `seeds/affective_state_core.json` holds the scalar `AffectiveState`
  node. In `seeds/core_emotions.json`, `em_readoff` writes valence as a sign and
  arousal as a magnitude. `seeds/affect_coupling.json` couples affect onto
  affinity-tagged nodes. No `SpaceQuantum` or `space_quantize` call is ever applied
  to affect.
- **Shared concept format.** `seeds/qualia_space.json` puts `dynamical:valence` on
  the same `_round_to_vocab` quantiser (`domains/analogy_search.py`) as other
  concept axes. It is used for analogy matching by equality, with no adjacency,
  distance or navigation.
- **Grid cells appear only as descriptions.** `seeds/neuro_hippocampus.json` holds
  descriptive Concept nodes for grid cells, place cells and entorhinal cortex.
  None is a mechanism.
- **No existing test** measures direction-dependent or periodic structure, or
  navigates an affect space.
- **Not audited:** the window-of-tolerance internals (`scripts/arousal_wot_run.py`)
  and the DimInfer cyclic/modular generator's implementation.

### Prior-art posture

- Grid cells (Hafting, Fyhn, Molden, Moser & Moser 2005, *Nature* 436:801–806), the
  hexadirectional fMRI signature, its extension to concept spaces, and the
  valence–arousal finding belong to their authors. **No neuroscience finding is
  claimed.**
- The valence–arousal circumplex is Russell's (1980, *J. Pers. Soc. Psychol.*
  39:1161–1178).
- That a square lattice with axis moves yields an L1 metric with D4 symmetry is
  elementary geometry. **Part A's interest is as a control, not a discovery:** it
  establishes on the running engine that Ocelot has no grid code, before any
  claim that it could acquire one.
- **The genuine delta** is that the reuse is measured, not argued. The same
  primitive and rules run on a non-spatial domain with **no change to `runners/`
  or `seeds/`**, and the measurement localises what that reused map does and does
  not encode about affective distance.

## 2. Substrate mapping (assemble, do not invent)

Everything below already exists. The confirmatory test is a **world adapter
only**, in the convention of `tests/test_quanta_navigation_migrated.py`. It:

- boots `WorldAdapter(seeds=())`;
- loads `seeds/quanta_navigation.json` through `load_seed_manifest`;
- authors `Cell` belief nodes linked by `has_cell` from a `WorldInstance{world_type:"Game", nav_repr:"quanta", nav_mode:"seek"}`;
- authors the `is_self Region → responds_via → ControlResponse` chain;
- commits a `Goal{world:1}`;
- drives the adapter's two-phase tick (`_tick2`), reading `chosen_action`.

**No Python makes a decision** (CLAUDE.md: the agent is Rust). The Fourier
analysis in §4 is offline measurement of the walks, not agent code.

- **Lattice and moves.** Cells carry integer `row`, `col` and `value`. The
  passable value is `FLOOR`, and a `WALL` ring encloses every belief so that no
  frontier quanta are minted. The controls are the 4 axis vectors (dr, dc) ∈
  {(±1,0), (0,±1)}, except in exploratory arm X-A4.
- **Part B coordinate mapping.** row ↔ arousal and col ↔ valence, on the integer
  lattice v, a ∈ [−4, 4]: 81 cells, held in an 11×11 grid with the wall ring. The
  controls are "valence ±1" and "arousal ±1". The lattice is a **synthetic**
  stand-in for a bounded rating scale. It is not built from the substrate's own
  `em_readoff`, because that readout has 3 valence levels (§7).
- **What a route measures.** Inside one passable box, `qf_hop_direct` takes a
  per-dimension sign step. Each step therefore reduces |Δrow| + |Δcol| by exactly 1,
  and the step count from start to goal is the measured distance. Across boxes,
  `qf_hop_route` minimises `qdist` + `cost`, where `cost` = 1 per portal, a box-hop
  count rather than a cell count.

## 3. Fixed constants

| constant | value |
|---|---|
| Part A belief | 17×17 open FLOOR cells, offsets −8..8 about the centre, plus a WALL ring (19×19). Start = centre. |
| Part A sample set S_sq | every integer offset (dx, dy) with 36 ≤ dx² + dy² ≤ 64: **88 offsets**, symmetric under D4 |
| Angle | θ = atan2(dy, dx), with dx = Δcol and dy = Δrow |
| Analysed quantity | f = steps / √(dx² + dy²) |
| Fourier folds | k = 3, 4, 5, 6, 7, 8, each fitted **separately**: f ≈ c₀ + a cos kθ + b sin kθ (ordinary least squares); amplitude A_k = √(a² + b²) |
| Positive-control sample S_hex | hexagonal lattice points x = i + j/2, y = (√3/2)j for integers i, j, with 6 ≤ √(x² + y²) ≤ 8: **120 points**, symmetric under 60° rotation; f = hexdist/norm, with hexdist = (\|i\| + \|j\| + \|i+j\|)/2 |
| Part B anchors (synthetic placements, NOT empirical norms) | happy (3,2), surprised (1,4), afraid (−2,4), angry (−3,3), disgusted (−3,1), sad (−3,−2), neutral (0,0), as (valence, arousal) |
| Part B3 trajectories | the 4-connected staircase between each of the 21 unordered anchor pairs. Rule: from p to q with Δ = (Δv, Δa), take a valence step iff valence is not finished and i_v·\|Δa\| ≤ i_a·\|Δv\| (exact integers), otherwise an arousal step. |
| B3 belief | the union of the staircase cells (**33 cells**) as FLOOR. Every other lattice cell, and the ring, is WALL: the agent can move only through affect states it has experienced. |
| max_steps | 64 per walk |
| Numeric tolerance | 1e-9 |
| B1 runtime fallback | if the full 6480-pair B1 run exceeds 60 minutes wall time, stop. Rerun with starts restricted to the 9 cells with v, a ∈ {−4, 0, 4} against all 81 goals (648 ordered pairs). Report that the fallback was used and the elapsed time. |

## 4. The analytic oracle (Appendix A reproduces every number)

- **Square lattice, 4 axis moves.** In open space the steps equal |dx| + |dy|. S_sq
  is D4-symmetric and f is D4-invariant. Under a 90° rotation, cos 6θ and sin 6θ
  change sign (6·90° = 540°), so their projection on f is **exactly zero**. The
  same holds for k = 3, 5 and 7. Only multiples of 4 survive. On S_sq:
  - A₄ = **0.180262476027**
  - A₈ = **0.050961235773**
  - A₃ = A₅ = A₆ = A₇ = **0** (|A| ≤ 1e-9)

  For reference, the continuous result is a 4-fold amplitude of 8/(15π) ≈ 0.1698
  on a mean of 4/π, a relative modulation of 2/15. That figure is not gated,
  because the sample is discrete.
- **Hexagonal lattice, hex distance (pipeline positive control, off-graph).** S_hex
  is invariant under 60° rotation, so only multiples of 6 survive:
  - A₆ = **0.068916648906**
  - A₃ = A₄ = A₅ = A₇ = A₈ = **0** (|A| ≤ 1e-9)
- **Part B open plane.** In one passable box covering all 81 cells, the steps from
  p to q equal |Δv| + |Δa| for all 6480 ordered pairs.
- **Part B3 experience map.** In the 33-cell staircase belief, the BFS shortest
  4-connected path equals the Manhattan distance for **all 42 ordered anchor
  pairs**, because each pair's own staircase is a monotone path. The Manhattan
  distance is therefore a tight lower bound on the measured steps.

## 5. Pre-registered gates

| gate | prediction | fails if |
|---|---|---|
| **G-A1** spatial walk | 88/88 arrive; steps = \|dx\| + \|dy\| for every offset | any non-arrival or any step mismatch |
| **G-A2** no grid code | measured A₆, A₃, A₅, A₇ ≤ 1e-9; A₄ = 0.180262476027 ± 1e-9; A₈ = 0.050961235773 ± 1e-9 | any nonzero odd or 6-fold amplitude, or a 4/8-fold mismatch |
| **G-A3** pipeline positive control (off-graph) | the same analysis on S_hex gives A₆ = 0.068916648906 ± 1e-9 and every other fold ≤ 1e-9 | analysis code is wrong. **G-A2 is then uninterpretable and is not reported as passed.** |
| **G-B1** reuse, zero mechanism | `git diff --stat <start-commit> -- runners/ seeds/` is empty at the end of the run; arrival 6480/6480 (or 648/648 under the fallback); steps = Manhattan for every pair | any change needed under `runners/` or `seeds/`, any non-arrival, or any step mismatch |
| **G-B2** metric blindness of the reused map | the open 81-cell affect plane decodes to **exactly 1** passable `SpaceQuantum` covering all 81 cells, **0** portals and **0** frontier quanta; after flooding, every goal's quantum `qdist` = 0.0, identical for all goals | more than one quantum, any portal or frontier, or `qdist` varying with affective distance |
| **G-B3** experience map, consistency | 42/42 ordered anchor pairs arrive; steps ≥ Manhattan for every pair | any non-arrival, or any step count below Manhattan (an impossible result, so a harness or engine bug) |

**Exploratory, with directional expectations stated but no threshold:**

- **X-A4: hexagonal controls on the same machinery.** Use 6 ControlResponses in
  axial coordinates, (±1, 0), (0, ±1), (1, −1), (−1, 1), on the integer belief
  over (i, j), with goals at the 120 S_hex points. Report:
  - arrival rate within 64 steps;
  - the fraction of points with steps = hexdist;
  - the measured A₃ … A₈.

  If steps = hexdist for all 120, the 6-fold code emerges **from the control set
  alone, with unchanged machinery**, and A₆ must then equal 0.068916648906. The
  outcome is not predicted. When the remaining displacement lies on one axis, the
  per-dimension sign vector ties between an axis control and a diagonal control,
  and a diagonal choice makes no progress in hex distance. The Dot-pick tie-break
  therefore decides the result. Report any oscillation or non-arrival as found.
- **X-B3: what `qdist` encodes on the experience map.** Report, across the 42
  pairs:
  - the number of quanta, portals and frontiers in the decoded B3 map;
  - the distribution of excess steps over Manhattan;
  - the Spearman ρ between the start quantum's `qdist` (relative to the goal) and
    the anchors' Euclidean distance, and separately their Manhattan distance.

  Directional expectation: ρ > 0, because box hops grow with separation. Expect it
  to sit below 1, because `qdist` counts box hops, not cells, and so depends on
  the greedy box decomposition.

## 6. What each outcome means for the cross-domain claim

| outcome | reading |
|---|---|
| G-A1–A3 pass | On the running engine, the spatial map has a **4-fold, not 6-fold** code. It does not reproduce the grid code. This is the expected baseline, not a failure of the rung. |
| G-B1 pass | The map format is **domain-general in fact**: the same primitive and rules carry a valence–arousal map with zero mechanism change. This supports the "one core" claim at the level of format. |
| G-B2 pass | The reused map is **metrically blind in open space**: `qdist` is constant, and distance information exists only as L1 step count from pose arithmetic. Ocelot as it stands therefore predicts a **city-block** distance signal, where the paper's design could not separate Euclidean from city-block. It also shows that the substrate's structure and choice signal separate, as in the paper, but that its structural map encodes **reachability, not metric distance**. |
| G-B1 fails (a change under `runners/` or `seeds/` was needed) | The "domain-general map" claim is **weaker than stated**. The change needed is the finding and is reported as the headline. |
| G-B2 fails | The decomposition is not what §2 states. Localise it before interpreting anything else in Part B. |
| X-A4 shows steps = hexdist everywhere | A 6-fold code is available from the control set alone, a candidate route to grid-like structure without a new primitive. This is still only one scale, not a multi-module grid code. |

## 7. Falsifier, and known gaps stated in advance

- **Falsifier of the expected baseline:** a nonzero A₆ in G-A2 with G-A3 passing.
  That would mean the engine's spatial map is not the Z^N axis-move lattice §2
  describes.
- **Falsifier of reuse:** G-B1 needing any edit under `runners/` or `seeds/`.
- **Gap: the substrate's own affect is too coarse for this map.** `em_readoff`
  valence takes only 3 values, so a belief built from the substrate's own
  readout would be at most 3 valence columns wide. The paper implies a graded
  valence representation. This rung therefore uses a synthetic lattice and does
  **not** test Ocelot's affect system. It tests whether Ocelot's map machinery
  could host one.
- **Gap: the B3 map is hand-authored experience.** The staircases are world data
  supplied by the adapter. They are not transitions the agent generated from its
  own affect dynamics.
- **Gap: no multi-scale or modular code.** Grid cells are often modelled as several
  modules, each a periodic code at a different scale, that jointly pin down a
  position (Fiete, Burak & Brookings 2008, *J. Neurosci.* 28:6858–6871). Ocelot's
  dimension-learning step has a cyclic/modular generator, and its frame invariant
  admits integer lattices of any basis, so such a code may be expressible. **This
  rung does not test that**, and it has not been checked against the generator's
  implementation.
- **Not tested here: the human cross-prediction.** G-B2's city-block prediction
  could be tested against the paper's open data (OpenNeuro ds008948, OSF 5fkuy) by
  comparing L1 and L2 distance regressors. That analysis is out of scope for this
  rung.

## 8. Files

- This pre-registration:
  `docs/research/psychology_affect/AFFECT_MAP_REUSE_GRID_CODE_PREREG.md`
- To be written, test (world adapter only):
  `tests/test_affect_map_reuse_gridcode.py`. It uses `pytest.importorskip("substrate_rs")`, and the harness follows `tests/test_quanta_navigation_migrated.py`. There is one test per gate. X-A4 and X-B3 record values and do not assert.
- To be written, results: `docs/research/psychology_affect/AFFECT_MAP_REUSE_GRID_CODE_RESULTS.md`.
  It reports every gate and both exploratory arms, the start commit, the
  `git diff --stat` output for G-B1, wall time, and whether the B1 fallback was used.
- Run with: `python3 -m pytest tests/test_affect_map_reuse_gridcode.py -q`

## 9. Discipline

- Fix the start commit before the run. The G-B1 diff is taken against it.
- No constant in §3 is changed after the run. If a constant was wrong, rerun under
  a new pre-registration and report both.
- Report nulls as headline findings. A G-B1 failure that localises what the map
  machinery lacks for a non-spatial domain is a better result than a pass that
  hides it.
- Report the synthetic-mechanism result and any benchmark meaning separately.
  None of this rung measures a person.

## Appendix A — oracle (pure arithmetic; reproduces every number in §4)

```python
import math
from collections import deque
import numpy as np

def amp(points, k):
    th = np.array([math.atan2(y, x) for x, y, _ in points])
    f = np.array([p[2] for p in points])
    X = np.column_stack([np.ones_like(th), np.cos(k*th), np.sin(k*th)])
    c, *_ = np.linalg.lstsq(X, f, rcond=None)
    return math.hypot(c[1], c[2])

sq = [(dx, dy, (abs(dx)+abs(dy))/math.hypot(dx, dy))
      for dx in range(-8, 9) for dy in range(-8, 9) if 36 <= dx*dx+dy*dy <= 64]
hx = []
for i in range(-12, 13):
    for j in range(-12, 13):
        x, y = i + 0.5*j, (math.sqrt(3)/2)*j
        r = math.hypot(x, y)
        if 6 - 1e-9 <= r <= 8 + 1e-9:
            hx.append((x, y, ((abs(i)+abs(j)+abs(i+j))/2)/r))
print(len(sq), len(hx))                                   # 88 120
for k in range(3, 9):
    print(k, round(amp(sq, k), 12), round(amp(hx, k), 12))
# k=4: 0.180262476027 (sq); k=8: 0.050961235773 (sq); k=6: 0.068916648906 (hex); all others 0

anch = {"happy": (3, 2), "surprised": (1, 4), "afraid": (-2, 4), "angry": (-3, 3),
        "disgusted": (-3, 1), "sad": (-3, -2), "neutral": (0, 0)}

def stair(p, q):
    dv, da = q[0]-p[0], q[1]-p[1]; Dv, Da = abs(dv), abs(da)
    sv, sa = (dv > 0)-(dv < 0), (da > 0)-(da < 0)
    iv = ia = 0; cur = list(p); out = [p]
    while iv < Dv or ia < Da:
        if iv < Dv and (Da == 0 or iv*Da <= ia*Dv): iv += 1; cur[0] += sv
        else: ia += 1; cur[1] += sa
        out.append(tuple(cur))
    return out

names = list(anch); vis = set()
for a in range(len(names)):
    for b in range(a+1, len(names)):
        vis.update(stair(anch[names[a]], anch[names[b]]))

def bfs(s, t):
    dq, seen = deque([(s, 0)]), {s}
    while dq:
        c, d = dq.popleft()
        if c == t: return d
        for m in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (c[0]+m[0], c[1]+m[1])
            if n in vis and n not in seen: seen.add(n); dq.append((n, d+1))

pairs = [(x, y) for x in names for y in names if x != y]
print(len(vis), len(pairs), sum(bfs(anch[x], anch[y]) ==
      abs(anch[x][0]-anch[y][0]) + abs(anch[x][1]-anch[y][1]) for x, y in pairs))
# 33 42 42
```
