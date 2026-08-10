# THE EYE

*A from-scratch, first-principles eye on the (G, Γ) graph-rewrite substrate.
Written 2026-07-18, at the close of the developmental-vision arc. Every claim
here was believed only because it failed where it had to; every bound is stated;
every retraction is kept. Read `VISION_PROTOCOL.md` for the binding rules and the
burned-seed ledger; this is the synthesis.*

---

## 0. What this is — and what it is not

**This is an EYE.** A retina, an oculomotor system, and the early dimensional
inference an eye feeds — motion, depth, and depth-from-many-eyes. It is built on
the substrate's own core loop (dynamic quantization / generator discovery), not as
a bolted-on vision module. Every dimension of sight it produces is *discovered*
from structured input, not stored as a coordinate; every constant *falls out* of a
measured quantity rather than being chosen.

**It is NOT a visual cortex.** Form and orientation selectivity through Hebbian
learning is a *diagnosed* dead end (§7), closed across five pre-registered rungs
with a measured, eigenspectral reason. Everything the eye does is bounded to the
**integer / in-frame** class the frame invariant blesses; the continuous,
cross-frame structures (real-angle rotation, continuous perspective, a form
cortex) are named as deferred, not faked.

The scope word is deliberate. *"A genuine eye implementation that works is
deliverable and valuable by itself"* was the founding thesis; this is that.

---

## 1. The retina — every constant falls out

| component | what it does | it falls out of | verified |
|---|---|---|---|
| **log receptor** | photon count → log signal; illumination invariance | Weber's law IS a log of the ratio | Weber–Fechner **0.9991**; invariance **0.44% (log) vs 100% (linear)**, ~1000× |
| **fixational drift** | a self-avoiding walk that MOVES the retinal image | Engbert's self-avoiding-walk dynamics | α_short **1.1553** > 1 > α_long **0.7590** (paper 0.79±0.11); load-bearing (§3) |
| **homeostatic setpoint** | per-cell adaptation target `μ_endo` | each cell's OWN endogenous activity | **0.1459** derived per cell; no imported constant |
| **change detection** | fires on change at the cell's own noise floor | the photon **shot-noise floor** `\|ΔI\| > √(I/n_max)` | change on the LOG signal ⇒ Weber-normalised for free |
| **retinal waves** | structured spontaneous activity before sight | random ignition + propagation rules | structure from entropy **0.195 vs 0.000** (same RNG); oriented fronts (front-nb **1.99**, coh_local **0.78**) |
| **centre-surround** | lateral inhibition / predictive coding | Oja competition from a **zero** init | emerged, not designed: CS **1.0839**; σ_ON,ON 1.627 vs σ_ON,OFF 3.264 |

**No float was chosen to hit a target.** Matrices, offsets, velocities, and
thresholds are read from the data; setpoints from endogenous activity; the change
threshold from the shot-noise floor. This is the §13 discipline — *magic numbers
fall out of natural processes, they do not go in* — applied without exception. The
one place a constant was *imported* (GCAL's `μ = 0.024`) killed cells in two layers
and was retracted (§8).

**Honest asterisks on biological plausibility.** The architecture maps to real
mechanisms (log photoreceptor, fixational drift, change-detecting ganglion cells,
retinal waves, centre-surround), and the developmental research behind it was
independently verified. But: it is discrete/integer and graph-native, not a spiking
simulation; the Engbert *crossover signature* is partly architectural, not derived
(§13.1); and the per-cell setpoint is individual by construction yet near-uniform in
fact (every cell sees the same wave field). These are named, not hidden.

---

## 2. The core loop — discovery, not fitting

The retina's output is not filtered by a fixed feature bank. It is **decoded
against a codebook the agent grows**, by one operation — *dynamic quantization* /
generator discovery — applied at every level. The operation, in one line:

> Decode the input against what you hold. What compresses, ground. What a held
> generator explains, recognise. What a NEW generator would explain, **mint the
> generator.** What nothing shorter than enumeration explains, ground at
> enumeration (a quantum per point).

The Occam ladder (increasing description length): exact recognise → transform in
the held basis → infer the dimension against held generators → **MINT a new
generator** → mint a flat quantum. The last two are the frontier this arc reached.

**Generator discovery works** (`sd loop's negative OVERTURNED, bounded`). Given a
minimal general seed — a 4-parameter integer matrix carried as **graph data** — the
loop mints a generator it was never given, from an orbit:

- a **frozen** seed recovers **three different correct** held-out generators (two
  shears, a unimodular map), one per orbit — the anti-forced control;
- it **refuses** the nonlinear (a modular wrap, a quadratic warp) to enumeration,
  and **cannot express** a held nonlinear generator — so it is provably **not a
  universal container**. *That failure is the proof it is real.*
- it mints iff it **compresses** (MDL 24→12, 2.0×); ungrounded input mints nothing
  (**0/400**);
- bounded to the integer-linear class GL(2,ℤ), confirmed outside it.

This is the operation the whole arc identified as missing, and it is what the eye's
dimensions are built on.

---

## 3. The dimensional stack — the real headline

Sight's dimensions are not stored. **Time, depth, and depth-from-many-eyes are
DISCOVERED** — each the same operation on more frames, each believed only because
it refuses to hallucinate. All verified on fresh binaries; §9 byte-identical
throughout (the held path never moved).

### 3.1 TIME — the exponent of the transition generator

A moving pattern is an **orbit**; the generator `M` carrying `frame(t)→frame(t+1)`
is the motion; the exponent `k` indexing `M⁰,M¹,M²…` **IS** the inferred time axis
(`latent:time`). Time is not in any frame — it lives in `Hom(frame,frame)`, the map
between them.

- ordered motion → `latent:time` + compression (MDL 28→7);
- **shuffled → enumeration** (0/400 at the longest window); **accelerating →
  `time_none`** (the frames are pairwise-translates yet not a single-generator
  orbit — the group-closed subtlety);
- the minted axis **predicts the unseen frame** `G⁷(f0)` exactly;
- a monotone reversal is a genuine orbit under `G⁻¹` — time's arrow, reversed.
- bounded to integer-velocity, in-frame; real-angle rotation and acceleration are
  cross-frame, correctly refused.

### 3.2 DEPTH — monocular structure from motion

A scene with real depth, dragged past the moving eye, transforms in a way **no
single flat generator explains** — near sweeps faster than far. That unexplained
temporal residual **is depth**: `latent:depth` orders the field by velocity. This is
`DimInfer`'s existing *"mint a dimension when a 2D residual is only explicable by a
third"* — driven by temporal residual.

- **the decisive control: a FLAT scene mints NOTHING** — and so does a multi-colour
  scene at a single velocity. Depth from velocity *variation*, never from region
  presence. A flat plane minting depth would be hallucination; it doesn't.
- multi-depth → `latent:depth` (MDL 36→13); four frozen scenes → four different
  correct orderings; shuffle → enumeration; the minted depth **predicts an unseen
  view**, each surface by its own velocity.
- **monocular** — it needs one *moving* eye, which the eye has. It bypasses the
  shelved binocular/cortex line entirely, because the 3D world was never in a still
  image; it is in the relations between frames.
- bounded to discrete integer-velocity rigid layers; continuous perspective is
  cross-frame, deferred.

### 3.3 STEREO — the same operation on simultaneous frames

`DepthInfer` **generalised across frame-source with no new code** — the diff over
the Rust source is empty. Fed N eyes at one instant instead of one eye over ticks,
the *unchanged* Term mints the *same* `latent:depth`. **Eyes and ticks are the same
resource, proven in code:** an eye is a spatial viewpoint, a tick a temporal one;
both are frames to relate.

- **single-depth mints nothing** (uniform / zero / infinite disparity, at every eye
  count); multi-depth mints (MDL 18→13);
- **built for N, never 2** — the eye count falls out of `Count(Eye hubs)`, no literal
  anywhere; the same frozen machinery runs N=2 and N=3, and **N=3 rejects what N=2
  hallucinates**;
- **additive** (the predator's bet, measured): same dimension as motion (orderings
  agree); **quicker** — one instant vs motion's K ticks (depth *now*); **more
  precise** — more baselines;
- predicts an **unseen eye's** view; shuffle → enumeration (0/400).

**The unification:** motion and stereo are two admissible generators for one depth
dimension, held additively, weighted by how many frames each has. You never choose
parallax *or* stereopsis — you ground the one dimension with both (§6).

---

## 4. Failure modes — the real tell

*"Can we replicate known failure modes? That is the real tell."* Normal function is
cheap to fake; a failure mode is a claim about what a mechanism DRIVES.

- **Troxler fading** replicates (8/8, p=0.0078): a stabilised image fades **to the
  setpoint while 100% alive** (uniform, not dead — a dead sheet can't counterfeit
  it); a drifting one does not. The content is two **independently-derived**
  timescales — `τ_drift = 3` (Engbert's walk) vs `τ_adapt = 160` (`μ_endo`) — landing
  53× apart, neither tuned to the other. **Caveat (§6):** our fade is retinal; the
  biological locus is multi-level (retinal-transient + retinal-sustained + cortical
  filling-in), and the eye is now an *instrument* to weight those contributions, not
  to crown one.
- **Lid-suture worse than dark** reproduces (−0.1458): unstructured drive *actively
  dissolves* structure, because Oja converges to the leading PC of whatever it is
  shown, and noise has no leading PC.
- **Event-camera convergence:** a pure change-detector must move to see a static
  world — the field independently *reinvented the microsaccade* (a wedge prism to
  generate events on static scenes). Which is why the drift being load-bearing was
  the precondition for everything downstream.

---

## 5. Scale — the wall is the boundary, not the ALU

Measured (AMD Ryzen 5 9600X, RELEASE): the curve is **linear, no cache cliff** — the
memory-bus hypothesis is refuted. The wall is the **Python↔Rust FFI** (75–82% of the
tick; Rust only 18–25%). Bulking the boundary gave **5.06×** and inverted the budget
to Rust; predicate pushdown then gave **4.29×** on the dominant rule. **Fovea (~150k
cells): 1317 → 137.8 ms.** A GPU cannot help — it targets ≤25% of the budget, and
that part is enumeration, not float math. **Ceiling that stands regardless:** the
cortical settling operator's spectral radius → 1 as the sheet grows, so a
GCAL-scale sheet settles arbitrarily slowly independent of any fix (and GCAL itself
never demonstrated convergence at scale — *"data not shown"*).

---

## 6. Principles the eye embodies

These were paid for by specific failures; each governs the whole.

1. **Magic numbers fall out of natural processes — they do not go in.** Three
   categories, and only the first is evidence: *fell out* (Weber 0.9991,
   lid-suture from Oja's leading PC); *put in as a constant* (`μ=0.024`, `w0=1.0` —
   fail on distribution shift); *put in as architecture* (a signature one rule is
   *solely responsible for* — silently unfalsifiable, worse than a constant).
2. **Noise does not exist — only signals you have not grounded.** The discrimination
   is DESCRIPTION LENGTH, not signal-vs-noise: mint iff it compresses; ground the
   rest at enumeration, provisionally, never asserting incompressibility.
3. **Tabula rasa is seeded.** No discovery from nothing; the test is a GENERAL seed
   (the target is one of a broad class, identified from data) vs a SPECIFIC one (the
   answer, pre-loaded). Evolution rewards *just enough to bootstrap* — the minimal
   general seed, the altricial bet.
4. **Cardinality is a magic number.** A hardcoded count (2 eyes, 1 cortex) is a
   constant in the architecture. Build N; the count falls out of the graph. Building
   N *proves* generality — if it works for N it cannot have hardcoded a pair.
5. **You don't have to choose — the answer is BOTH.** For every "which level?"
   question the honest answer is co-present admissible mechanisms weighted
   log-relatively. This is the entire point of (G, Γ) + admissibility grammar over a
   single model: the grammar governs *consistency* among mechanisms, not *selection*
   of one. Motion AND stereo; retinal AND cortical; transient AND sustained.
6. **The frame/continuum invariant.** In-frame is integer (the present, the
   lattice); non-integer/continuous structure is cross-frame, living in the map
   between frames. Every dimension of sight the eye grows is minted from
   frames-to-relate — never stored — and is bounded to the integer/in-frame class by
   construction.

---

## 7. The cortex — a diagnosed dead end (not a gap)

Form/orientation through Hebbian learning does not work here, and the reason is
*measured*, not a shrug:

- **H1 null** — composing decorrelated ON/OFF channels does not lift orientation
  selectivity (Δ = −0.0118, CI excludes SESOI by 2.5×), with five artifact routes
  each closed by measurement (blind probe, dead arm, inherited floor, inert
  manipulation, drive-not-selectivity).
- **The cause is the input covariance.** The waves are fine (fronts, locally
  oriented), but `E[xxᵀ]`'s **leading eigenvector is a DC blob**, and removing DC
  leaves a **degenerate** oriented pair — the preferred orientation is a coin flip.
  Oja fits second-order statistics; orientation is not in them. This is *arithmetic*,
  not a tuning failure.
- **The missing cortical layer was BUILT** (Unit→Unit lateral + a settling loop, in
  pure rules, zero constants) to test whether GCAL's actual orientation mechanism
  rescues it. It does not: there is **no η at which the learning rule is both
  convergent and load-bearing**, confirmed across the settling loop with a proper
  fixpoint predicate (cycle detection, zero constants).
- **GCAL verified from the primary:** its orientation comes from neither its
  isotropic-disk stimulus nor its Oja rule — only from its settling steps; and even
  those are a tolerance predicate, not a demonstrated convergence.

**The redirection this forces is the arc's actual finding:** the cortex-through-Oja
line was the dead end of *static, second-order, single-frame* vision. **The 3D world
was never in a still image — it is in the relations between frames, and those the
substrate CAN discover** (§3). Depth comes from motion, monocularly, and stereo adds
to it. Biology agrees: dorsal (motion) is early and central; the ventral
static-form path was the wrong place to start.

---

## 8. Retractions — the honest ledger

Kept in place, each with the measurement that forced it. They are the reason the
rest is trustworthy.

1. **Stage 1's "biology emerged"** — designed kernels + a measure that passed noise.
2. **Rung 1's deprivation asymmetry** — confounded (noise disrupting a running wave
   program, not experience degrading tuning); survived six attempts because all six
   shared one design error.
3. **Rung 2's experience headline** — on the real source `normal` REVERSES below
   `dark`; attempt 10's runner was never committed, so the number is *unattributable*.
   **An uncommitted runner means the result is not a result.**
4. **The Engbert drift was decorative** — it reproduced a published signature to two
   decimals while driving *nothing* (its only consumer was the ruler that measured
   it), until it was wired into the image.
5. **`μ = 0.024`** — an absolute setpoint imported from GCAL's frame, which we do not
   have; killed cells in two layers; replaced by the derived `μ_endo`.

And the method that caught them: **the positive control.** Sixteen inert
instruments were found this arc — a measure that passed noise; a dead cell scoring a
flawless floor; a stocked library reading empty off a wrong dict key; a walk whose
only consumer was its ruler; a §9 bench with ten tests that had never run — and
*not one* was caught by a gate going red. Every one was caught by someone noticing a
result was too clean. The discipline that remains: **verify the fact before you fix
the gate; positive-control the reader, not just the arm; a claim believed only
because it fails where it must.**

---

## 9. What stands, in one paragraph

An eye that measures ratios, not absolutes (log receptor); that moves, and whose
motion is load-bearing (drift → Troxler); that adapts to a floor it measured in
itself (`μ_endo`); that fires on change at its own noise limit; that grows its
structure from endogenous waves; and that **discovers the dimensions of sight —
time, depth, and depth-from-N-eyes — from the relations between frames**, by one
operation, every constant falling out, every dimension refusing to hallucinate,
bounded honestly to the integer/in-frame class. It is not a form cortex; that
remains a diagnosed dead end through the mechanisms tried. It is an eye — and the
early, dorsal, motion-first computation an eye feeds — built from a minimal seed on
the substrate's own core loop. The `git` history is the lab notebook; every number
here reproduces on a fresh binary.
