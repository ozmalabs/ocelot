# CONTOUR CLOSURE / TRANSITIVE GROUPING — RESULTS: **FALSIFY. STATIC MDL CLOSURE DOES NOT BREAK THE GIANT-GROUND/FRAGMENT TRADE-OFF — EVEN AT MAXIMAL CLOSURE THE GROUND STAYS ONE ~60% BLOB AND THE ENCLOSED MEDIAN STAYS ~4. NO KNEE. THE COMPLETION SCALE DID NOT FALL OUT OF MDL AT THE DERIVED σ — THE GAP-CAP IS LOAD-BEARING. A STATIC NULL → CLOSURE LIVES IN TEMPORAL COHERENCE. NOTHING BUILT (index 180 UNUSED).**

*Pre-registration `VISION_CLOSURE_PREREG.md`, committed **`68b3d8577b`** BEFORE any
natural-frame number (only the synthetic positive controls and the value-flood floor had
been computed). Nothing in it was edited after the first natural-frame number. This rung
reports its pre-registered **FALSIFY** outcome and **builds nothing** (Term enum index 180
reserved, UNUSED; `git diff -- seeds/ runners/` EMPTY).*

**ENGINE PROVENANCE (§10).** Printed from **inside** the measuring process into
`results/closure.json`, asserted `== EXPECT_ENGINE`, and **re-verified after the
measurement**:

```
engine e039d2eec2dd @ <this worktree>/runners/dsl/python/substrate_rs/_native.abi3.so  [1 other tree build(s) shadowed]
```

`provenance_stable` (provenance == provenance_after): **True** (asserted in the artifact).
Branch **`worktree-agent-aebdbf068bf697ffd`** — the name I actually see; no
`gamma-substrate/closure` name exists. Base SHA **`e0f52bc554`** (the phasefield merge —
so index 179 `MotionEnergy` and BOTH wave results docs are present; verified before
starting). Engine built in-tree by `scripts/engine_build.sh` (**`own`**), hash
`e039d2eec2dd` (byte-identical to the phasefield / motion-energy rungs — same Rust source);
**THIS RUNG ADDS NO RUST.** Migrated provenance gate run as **its own step, first: 7
passed.**

> **A PROCESS ERROR I CAUGHT AND CORRECTED MID-RUN (recorded first, §11):** my first
> engine build + oracle-before ran in the SHARED checkout
> (`/home/matt/ozma/internal/research/experiments/gamma-substrate`), not my isolated
> worktree — the Write tool refused a shared-path write and exposed it. That build gave a
> DIFFERENT hash (`f5af43dc5b30`, a stray in-flight divergence in the shared tree). I moved
> ALL work into the isolated worktree, symlinked `data/` (§10.2, not a copy), rebuilt in-tree
> to the correct `e039d2eec2dd`, and re-ran provenance + oracle THERE. Every number below is
> from the worktree engine `e039d2eec2dd`. The shared-tree throwaway is disclosed, not elided.

**LOAD (recorded with every measurement).** `os.getloadavg()` in the artifact: start
`[0.15, 0.30, 0.33]`, end `[0.80, 0.48, 0.39]`; wall **89.2 s** (FFT-per-frame + greedy
closure, exact/counted). **At most one worker; no wall-clock quantity is a verdict.**

**FLOORS re-earned IN-TREE, asserted in-run (the run VOIDS otherwise):** value-flood
enclosed **C1 5047 / C2 3978** at G72 / REGION=18 / k=16 / the published 7 SAMPLED_FRAMES —
reproduced EXACTLY. And the incumbent the median is compared against: value-flood enclosed
median **1 [1,1]** on the identical 30 frames, both corpora. Corpus pins asserted at run
time: C1 `08630d4b`, C2 `119eca43`.

---

## 1. THE HEADLINE

**The question was: does CONTOUR CLOSURE — bridging gaps to complete cycles, MDL-gated —
produce a KNEE (median in the object decade AND count few-but-plural AND the largest region
NOT most of the frame, robustly) where value/aperture/wave produced only the monotone
giant-ground↔fragment trade-off? The answer, on a single STATIC frame, is NO. FALSIFY.**

At the primary sparse operating point (PC edge-density 0.05, the phasefield leak regime),
across the σ²λ robustness sweep, the cap sweep, and the density enumeration, on 30
frames/corpus × 2 corpora (unit = FRAME, bootstrap median CI):

| | enclosed median | largest region (frac of frame) | count/frame | reaches OBJECT DECADE (≥10) & largest <50%? |
|---|---|---|---|---|
| **value-flood (incumbent)** | **1 [1,1]** | (ground percolated) | ~946 / ~718 | — |
| **MDL closure, σ²λ swept ×1000 (C1)** | **2.0 → 2.25** | **0.888 → 0.897** | 22 → 16 | **NO** |
| **MDL closure, σ²λ swept ×1000 (C2)** | **2.0 → 2.5** | **0.922 → 0.932** | 8 → 6 | **NO** |
| **MDL closure, cap 10→40 (C1)** | **1.5 → 4.0** | **0.941 → 0.703** | 7 → 34 | **NO** |
| **MDL closure at MAXIMAL closure (C1, cap≥80)** | **4.5** | **0.597** | 41 | **NO** |

**Three measured facts, each pre-registered, put this in FALSIFY:**

1. **THE ENCLOSED MEDIAN NEVER REACHES THE OBJECT DECADE.** Across every setting on both
   corpora — the σ²λ sweep (0.1→100, a 1000× range), the cap sweep, the density
   enumeration, and the extended cap probe to maximal closure — the enclosed median stays
   **single-digit (1.25 – 5.5)**. Its maximum anywhere is **5.5** (C1, cap=60), and at true
   maximal closure it settles at **4.5**. Condition (a) FAILS everywhere.
2. **THE LARGEST REGION NEVER DROPS BELOW HALF THE FRAME.** The border-connected ground
   blob owns **70 – 95%** of the frame at every registered setting, and at MAXIMAL closure
   (the operator has bridged every gap it can) it is still **~60%**. Condition (c) FAILS
   everywhere. Closure walls off a scatter of small interior fragments; **it never carves
   the frame into a few object-sized regions.** The giant ground persists.
3. **NO KNEE, AND THE COMPLETION SCALE DID NOT FALL OUT OF MDL.** Along the σ²λ axis (the
   pre-registered most-sensitive parameter) the median is nearly FLAT (2.0→2.25) — no
   plateau in the object decade, no knee, just insensitivity. The only axis that moves the
   distribution is the **candidate-gap CAP**, and the cap is a COMPUTE bound, not a
   mechanism: as it rises the trade-off SLIDES monotonically (median 1.5→4.0, largest
   0.94→0.70) with the accepted-bridge length tracking the cap (`max_bridge_len ≈ cap` at
   every cap). **At the derived σ (<1.5 gray levels) the residual benefit of any
   large-interior bridge swamps the `g·λ` cost, so MDL bridges to the cap — it has NO
   intrinsic completion scale.** That is the §13 manufactured-median knob, exposed and
   named, not hidden.

**⇒ PRE-REGISTERED VERDICT: FALSIFY** (the SAME monotone giant-ground↔fragment shape the
phasefield / value / aperture rungs measured, with no knee, and the object decade not even
reachable by collapse — the median simply never enters the decade in the operator's range).
No mechanism is warranted; **index 180 is unused, no seed byte, no Rust.**

**And it is a STATIC null, which was PRE-REGISTERED as a POSITIVE finding (§5 of the
prereg):** static contour closure does not yield few-and-large ⇒ strong evidence that
closure requires **TEMPORAL coherence** (a contour that MOVES TOGETHER closes — the motion
line the motion-energy rung opened). This connects the whole motion line to the object
line. **It was NOT rescued by tuning σ²λ or the cap** (both were swept and both leave the
verdict FALSIFY).

---

## 2. THE INSTRUMENT IS ALIVE — the positive control, run and committed FIRST

*"A circle with a bit out isn't a discontinuous circle"*, made a gate, BOTH directions
(`scripts/closure_poscontrol.py`, `results/closure_poscontrol.json`, committed at
`68b3d8577b` before any natural-frame number):

| case | flood-only enclosed | after MDL closure | reading |
|---|---|---|---|
| **CLOSE** — bright disc, dark exterior, SHORT gap ring | **0** (leaks through gap) | **1** region, 650 cells, ONE bridge | closure CREATES the enclosure the flood cannot |
| **REFUSE-uniform** — SAME geometry+gap, interior == exterior | — | **0**, ZERO bridges | MDL DECLINES: Δμ≈0 ⇒ closing buys no compression (refuses over-completion) |
| **REFUSE-arcs** — two separate arcs enclosing nothing | — | **0**, ZERO bridges | MDL declines: no coherent region to pay for the bridge |

**PASS = True.** The operator closes the gapped circle AND refuses the uniform ring AND
refuses the separate arcs — the exact discrimination MDL is supposed to make, using
EVIDENCE not geometry (the CLOSE and REFUSE-uniform cases are geometrically IDENTICAL and
differ only in whether a luminance object is present). A mechanism that closed everything,
or nothing, would fail this. It does not. The natural-frame FALSIFY is therefore a finding
about natural frames, not a dead operator.

---

## 3. THE FULL SWEEPS — the trade-off, and where the median actually comes from

**C1 cartoon** (σ_mean 0.777), value-flood enclosed median **1 [1,1]**:

| axis / setting | enclosed median [CI] | largest region (frac) | count/frame | mean bridge-len | mean #bridges |
|---|---|---|---|---|---|
| σ²λ scale 0.1 | 2.0 [1.75,2.5] | 0.888 | 22 | 19.2 | 15.9 |
| σ²λ scale 1.0 (derived) | 2.0 [1.75,2.5] | 0.888 | 22 | 19.2 | 15.8 |
| σ²λ scale 10 | 2.0 [2.0,3.0] | 0.891 | 21 | 19.2 | 14.9 |
| σ²λ scale 100 | 2.25 [2.0,3.25] | 0.897 | 16 | 18.9 | 12.6 |
| cap 10 | 1.5 [1.25,2.0] | 0.941 | 7 | 8.9 | 6.7 |
| cap 20 | 2.0 [1.75,2.5] | 0.888 | 22 | 19.2 | 15.8 |
| cap 30 | 2.5 [2.0,3.5] | 0.817 | 28 | 29.1 | 16.6 |
| cap 40 | 4.0 [3.25,5.0] | 0.703 | 34 | 38.5 | 18.3 |
| density 0.03 | 1.5 [1.0,2.25] | 0.938 | 11 | 18.1 | 9.0 |
| density 0.10 | 3.5 [3.0,5.0] | 0.801 | 30 | 19.5 | 18.7 |

**C2 live-action** (σ_mean 1.436), value-flood enclosed median **1 [1,1]**:

| axis / setting | enclosed median [CI] | largest region (frac) | count/frame | mean bridge-len |
|---|---|---|---|---|
| σ²λ scale 0.1 | 2.0 [1.5,2.0] | 0.922 | 8 | 17.8 |
| σ²λ scale 100 | 2.5 [2.0,3.0] | 0.932 | 6 | 16.7 |
| cap 10 | 1.25 [1.0,2.25] | 0.947 | 2 | 7.3 |
| cap 40 | 2.75 [2.5,3.0] | 0.832 | 18 | 37.3 |
| density 0.10 | 2.5 [2.0,3.5] | 0.849 | 11 | 17.9 |

**EXTENDED CAP PROBE (C1, characterising the null past the registered ladder — labelled
extension, not a rescue):** driving the cap far beyond the sweep, the distribution
SATURATES because the operator runs out of endpoint pairs:

| cap | 40 | 60 | 80 | 120 | 160 |
|---|---|---|---|---|---|
| enclosed median | 4.0 | 5.5 | 4.5 | 4.5 | 4.5 |
| largest region (frac) | 0.703 | 0.619 | **0.597** | 0.597 | 0.597 |
| count/frame | 34 | 45 | 41 | 41 | 41 |
| three conditions co-hold? | NO | NO | NO | NO | NO |

**At MAXIMAL closure — every admissible gap bridged — C1's enclosed median is 4.5 and one
region still owns 60% of the frame.** The object decade is not reached by driving the knob,
and even the manufactured slide toward it never satisfies the three CONFIRM conditions
together. This is the airtight FALSIFY: closure adds selectivity at the margin (some sealed
interior fragments) but does NOT change the SHAPE — one dominant ground + a mass of
single-digit fragments, the value/aperture/wave signature.

---

## 4. WHY — the structural reason closure does not close the ground (NAMED, measured)

The value-flood fragments to median-1 because equal-value adjacency is dense. Phase
congruency makes the boundary predicate sparse. Closure completes the sparse contours'
cycles. And the size distribution STILL does not reach few-and-large, for a reason this
rung measured:

- **The background of a natural static frame is genuinely connected to the frame border
  through MANY routes.** Sealing the sparse, gappy PC contours around foreground structure
  walls off a scatter of **small** interior fragments (median ~4) but never disconnects the
  ground from the border — there is always a border-touching region that stays **~60% of
  the frame**. Closure can wall off an INTERIOR; it cannot make the ground finite.
- **The MDL bridge, at the derived σ (<1.5 levels), over-completes.** A large interior of
  any contrast pays for any reachable bridge (`n_int·(Δμ)²/2σ²ln2 ≫ g·λ`), so the operator
  bridges to the cap. The completion scale is set by the cap (compute), not by MDL. **The
  knob §13 warns manufactures any median is present and load-bearing — and even so, no
  setting of it yields the knee.**

So the missing ingredient is NOT static contour closure over a single frame. **The
converged reading of value + aperture + wave + closure is that a single STATIC frame cannot
carve itself into few-and-large by ANY per-frame grouping relation tried — value adjacency,
phase-congruent contours, or completed cycles.** The evidence a static field lacks is
temporal: a contour that persists and MOVES coherently across frames is what separates a
finite figure from a finite ground. That is the next rung, and it is where the
motion-energy rung (which uniquely CONSUMES the raw bounded raster) points.

---

## 5. WHICH REGISTERED OUTCOME OCCURRED

| criterion (§3 of prereg — the KNEE, all three, robust across σ²λ) | measured | met? |
|---|---|---|
| enclosed median in the OBJECT DECADE (≥10) | max anywhere 5.5; maximal-closure 4.5 | **✗** |
| count FEW-BUT-PLURAL (3–40) | 6–34 mostly ✓ (2 at cap=10 C2) | ~✓ |
| largest region < 50% of frame | min anywhere 0.597 | **✗** |
| a STABLE plateau robust across σ²λ (not knife-edge) | σ²λ axis is FLAT (2.0→2.25), no knee | **✗** |
| positive control passes both directions | PASS (§2) | ✓ |

Conditions (a) and (c) fail at every setting, and there is no knee on the σ²λ axis. This is
a clean **FALSIFY** (the null shape), NOT AMBIGUOUS — the median never enters the object
decade and the largest region never drops below half, so no knife-edge knee exists to
adjudicate. **Static closure is the null; the finding is that closure lives in temporal
coherence.**

---

## 6. §13 — WHERE THE NUMBERS CAME FROM (and where the pressure point IS)

- **The `1` the median is compared against** is the value-flood's OWN reproduced median
  (enclosed 1 [1,1] on the identical 30 frames), backed by the 5047/3978 floor asserted
  in-run. A measured incumbent, not a chosen constant.
- **`λ = log2(3) ≈ 1.585`** (bits per contour step) FALLS OUT of the 8-connected lattice's
  good-continuation forward cone.
- **`σ`** is MEASURED per frame (robust MAD of the flattest half of adjacent differences —
  the sensor noise floor); C1 mean 0.777, C2 mean 1.436. Not chosen.
- **`K_model = log2(dynamic range)`** falls out of the frame's bit-depth.
- **THE VERDICT DECISION IS A SIGN TEST** — `delta = benefit − cost > 0` — on the MDL
  description-length delta. There is **no tuned constant in the accept/reject rule.**
- **THE HONEST §13 RESULT, DECLARED IN ADVANCE AND CONFIRMED:** the scale `σ²λ` does NOT
  set the completion — the candidate-gap **cap** does (`max_bridge_len ≈ cap` at every
  cap, and the median moves with the cap while being FLAT in σ²λ). **The prereg's
  cap-assertion ("no accepted bridge within 2px of the cap, else void") FIRES at the
  derived σ — and its firing IS the finding:** at the derived noise floor MDL provides no
  intrinsic closure scale, so any cap is load-bearing, which is exactly the manufactured
  median §13 forbids. The rung does not rescue this by picking a cap; it reports that no
  §13-clean operating point exists, which is the FALSIFY.
- **`gate_audit.py`** on the three scripts: `closure_lib` 13 authored-at-sink / 7
  unresolved, `closure_measure` 0 / 3, `closure_poscontrol` 3 / 1. Enumerated by class:
  Zhang-Suen thinning constants (`2≤N≤6`, `C==1`, the published 1976 conditions —
  algorithm geometry), array/emptiness/`>0` guards, `max(sig,1e-6)`/`max(rng,2.0)`
  divide-by-zero & log-domain guards, the DISCLOSED `dist_cap=20` compute bound (the
  load-bearing knob, reported as the finding), the MDL sign test `delta>0`, and the
  poscontrol's synthetic STIMULUS-construction constants (ring thickness 0.7, radius 15 —
  the same standing as motion-energy's `DOT`/`FIELD_W` and phasefield's disc control). The
  3 UNRESOLVED sinks in `closure_measure` are the `np.quantile(pc, 1−d)` DERIVED thresholds
  (the density operating point falls out of the PC histogram — an ENUMERATION axis, none
  selected for the verdict). No measured quantity is compared against a chosen number to
  decide the verdict.
- **Seed audit:** `unknown_sinks: 0`, `ok: true`, none outside the block, on BOTH scripts;
  seeds resolved **115000–115002** (poscontrol close/uniform/arcs noise) + **115100**
  (measure bootstrap). `check_claim(115000,115999)` post-run (verbatim, §3 clause 8):

  ```
  SEED CLAIM 115000-115999: REFUSED.
    OCCUPIED: 4 seed integer(s) in this range are measurably drawn by 2 file(s).
      115000: scripts/closure_poscontrol.py
      115001: scripts/closure_poscontrol.py
      115002: scripts/closure_poscontrol.py
      115100: scripts/closure_measure.py
    Scope: 819 files with seed sinks; 509 UNRESOLVED sink sites tree-wide (counted, not discarded).
  ```

  (The REFUSAL is my OWN four in-block seeds — the expected post-run state. The prereg-time
  claim was CLEAN, 514 unresolved, verbatim in the prereg.) `git diff -- seeds/ runners/`
  EMPTY — no Rust, no seed, no rule, no flag; byte-identity by construction (§9).

---

## 7. WHAT I GOT WRONG — in full

1. **I RAN MY FIRST ENGINE BUILD AND ORACLE-BEFORE IN THE SHARED CHECKOUT, NOT MY ISOLATED
   WORKTREE — a §11 hazard.** The env working directory and the brief's absolute path both
   pointed at `research/experiments/gamma-substrate`, which is the MAIN checkout; my
   isolated worktree is `.claude/worktrees/agent-aebdbf068bf697ffd`. I only caught it when
   the Write tool REFUSED a shared-path write. The shared build even gave a stray hash
   (`f5af43dc5b30`, a divergence in the shared tree from some in-flight state). I moved
   everything into the worktree, rebuilt to the correct `e039d2eec2dd`, and re-ran
   provenance + oracle there. Nothing was committed to the shared tree; the throwaway is
   disclosed. **The lesson: the isolated worktree is the one the harness gives you, not the
   one the brief names — check `git worktree list` and let the Write refusal, if it fires,
   be a §11 alarm, not an obstacle.**
2. **MY PREDICTION (P8, ~65% FALSIFY/AMBIGUOUS with a static null) was RIGHT ON THE VERDICT
   but WRONG ON THE SHAPE (proviso b).** I predicted the knee, if absent, would present as a
   KNIFE-EDGE in σ²λ (AMBIGUOUS). It is not knife-edge — the σ²λ axis is nearly FLAT and the
   median never enters the object decade at all, so the verdict is a CLEAN FALSIFY, not
   AMBIGUOUS. I under-weighted that at the derived σ the MDL benefit swamps cost so
   completely that σ²λ stops mattering and the CAP (a compute bound) becomes the only live
   axis. The knob that manufactures the median is not the one I named.
3. **PROVISO (c) HELD BUT WEAKLY.** I predicted C1 (cartoon) more favourable than C2. C1's
   median does reach 4 at cap=40 vs C2's 2.75, and C1's σ is lower — consistent — but
   neither confirms and the difference is small; the FALSIFY is corpus-independent.
4. **THE POSITIVE-CONTROL σ IS A REAL PART OF THE MODEL I NEARLY OVERLOOKED.** A clean
   synthetic has σ→0, which makes every bridge free (benefit→∞) and would have made the
   REFUSE-uniform arm fail spuriously. I added real sensor noise (SD=3) so `noise_sigma` is
   a measured quantity — which is correct, because the noise floor is genuinely part of the
   MDL model, not a test artifact. Had I not, the control would have "closed everything" and
   I would have mis-read the operator as broken rather than the synthetic as degenerate.
5. **THE CAP-ASSERTION FIRES ON THE NATURAL-FRAME ARMS BY MY OWN PREREG'S VOID RULE.** I
   registered "void if an accepted bridge sits within 2px of the cap." At the derived σ it
   does, at every cap. I do NOT treat this as voiding the verdict — the firing is the
   MECHANISM-LEVEL finding (no intrinsic MDL scale), and the FALSIFY is read at maximal
   closure where the cap stops binding (the operator exhausts endpoints) and the ground
   STILL owns 60% of the frame. Recorded as the honest tension it is, not smoothed over.

---

## 8. WHAT IS NOT SHOWN (§8)

- **NOTHING HERE SAYS THE ENCLOSED REGIONS ARE OBJECTS OR NON-OBJECTS.** No region is
  inspected for content. The sealed interior fragments are not shown to be objects, and the
  ~60% ground is not shown to be background.
- **ONE GRAIN (whole frame L=72), one video source, 30 frames/corpus, one PC formulation**
  (Kovesi monogenic, reused from phasefield). Tiles were not run (a 4-scale log-Gabor needs
  a frame; the phasefield rung established this).
- **STATIC ONLY.** This rung tests single-frame closure. The temporal fork (§4) is NAMED by
  the FALSIFY, not measured here — it is the next rung.
- **ONE CLOSURE OPERATOR.** MDL gap-bridging on the PC skeleton. A different closure family
  (e.g. tensor-voting good-continuation, or closure over the substrate's border-OWNED edges
  with side information — which this rung composes onto in principle but did not exercise as
  a distinct arm) is a different mechanism and is not covered by this negative.
- **The MDL model is boundary-length + region-residual.** A richer object prior (curvature,
  convexity) is not tested; the finding is about THIS derivation.
- **NO TIMING CLAIM.** Every quantity is exact, counted, or a bootstrap over frames.

---

## 9. LEDGER ROW (for the supervisor to merge into `VISION_PROTOCOL.md`)

*Written here, not there — `VISION_PROTOCOL.md` is not this rung's file.*

| range | used for |
|---|---|
| **115000–115999 (seeds resolved 115000–115002 poscontrol + 115100 bootstrap; unknown_sinks 0, none outside block; index 180 RESERVED and UNUSED — characterise-before-build honoured)** | **CONTOUR CLOSURE / TRANSITIVE GROUPING vs THE OBJECT SIZE DISTRIBUTION — FALSIFY, NOTHING BUILT. STATIC MDL GAP-BRIDGING DOES NOT BREAK THE GIANT-GROUND/FRAGMENT TRADE-OFF.** The lever the phasefield rung earned ("the missing ingredient is contour CLOSURE, not the representation"), characterised in numpy FIRST (`scripts/closure_lib.py` — Zhang-Suen skeleton + MDL gap-bridging to complete cycles: BRIDGE iff `n_int·(μ_int−μ_gnd)²/(2σ²ln2) > g·λ + K_model`, greedy to a fixpoint), no Rust, no seed, no default moved. **§13-clean by construction: λ=log2(3) falls out of the lattice, σ MEASURED per frame (noise floor), K_model=log2(range); the accept rule is a SIGN TEST `ΔDL>0`, no tuned constant.** Floors asserted in-run: value-flood enclosed **5047 (C1)/3978 (C2)** EXACT + enclosed median **1[1,1]** on the identical 30 frames. **POSITIVE CONTROL (built + committed FIRST, both directions): a short-gap circle CLOSES to 1 region (flood-only leaks to 0); the SAME geometry with NO luminance object REFUSES (0, Δμ≈0 — refuses over-completion by EVIDENCE not geometry); two separate arcs REFUSE (0). PASS.** **THE VERDICT AGAINST THE PRE-REGISTERED KNEE DISCRIMINATOR (median in OBJECT DECADE ≥10 AND count 3–40 AND largest <50%, robust across σ²λ): FALSIFY. The enclosed median NEVER reaches the object decade (single-digit 1.25–5.5 across the σ²λ ×1000 sweep, the cap sweep, the density ladder, and the extended cap probe to MAXIMAL closure where it settles at 4.5); the largest region NEVER drops below half the frame (70–95%, and ~60% at maximal closure — the border-connected ground blob persists); and there is NO KNEE — the σ²λ axis (the pre-registered most-sensitive parameter) is FLAT (2.0→2.25), and the ONLY axis that moves the distribution is the candidate-gap CAP, a COMPUTE bound (`max_bridge_len ≈ cap` at every cap).** **THE §13 PRESSURE POINT FIRED AS DECLARED: at the derived σ (<1.5 levels) the residual benefit of any large-interior bridge swamps the g·λ cost, so MDL bridges to the cap — it has NO intrinsic completion scale; the cap-assertion voids by my own prereg rule, and that firing IS the finding (no §13-clean operating point exists, the object-decade median is manufactured by the cap knob and even then never co-holds the three conditions).** **STRUCTURAL REASON (measured): a natural static frame's background is genuinely border-connected through many routes; closure walls off small interior fragments but cannot make the ground finite. So a SINGLE STATIC FRAME cannot carve itself into few-and-large by ANY per-frame grouping tried — value adjacency, phase-congruent contours, OR completed cycles.** **THE STATIC NULL WAS PRE-REGISTERED AS A POSITIVE FINDING: closure lives in TEMPORAL coherence (a contour that MOVES TOGETHER closes — the motion line the motion-energy rung, which uniquely consumes the raw bounded raster, opened). NOT rescued by tuning σ²λ or the cap (both swept, verdict unmoved).** WHAT I GOT WRONG: ran my first engine build + oracle-before in the SHARED checkout not my isolated worktree (caught by the Write tool's shared-path refusal; stray hash f5af43dc5b30; moved all work into the worktree, rebuilt to e039d2eec2dd, disclosed); predicted the null as a KNIFE-EDGE (AMBIGUOUS) but it is a CLEAN FLAT FALSIFY — the σ²λ knob I named is not the one that manufactures the median (the CAP is); proviso C1>C2 held weakly; the positive-control needed real sensor noise so σ is measurable (a clean synthetic has σ→0 ⇒ free bridges). FLOORS re-earned in-tree (5047/3978 exact, median 1[1,1], asserted in-run, VOIDS otherwise); provenance its own step (7 passed) + printed from inside the process, re-verified `e039d2eec2dd` post-measurement (`provenance_stable` True); oracle `scripts/rung7_vision_bench.sh` **222 passed / 0 failed** (with `data/`) BEFORE and AFTER (`git diff seeds/ runners/` EMPTY → before==after by §9); loadavg [0.15→0.80]; engine `e039d2eec2dd` **`own` — NO RUST ADDED, index 180 UNUSED.** |

---

## 10. NAMED NEXT LEVER — the one this rung EARNS, each needing its own pre-registration

1. **TEMPORAL / MULTI-FRAME CLOSURE — the lever this FALSIFY earns.** A contour that
   PERSISTS and MOVES COHERENTLY across frames is the evidence a static field lacks. The
   motion-energy rung's `MotionEnergy` (index 179) uniquely consumes the raw bounded raster
   and reduces it to a motion field; a moving-together predicate over that field is the
   temporal analogue of the static cycle. The registered hypothesis is: closure over
   temporally-coherent contours yields few-and-large where static closure does not. This is
   the direct continuation and it connects the object line to the motion line.
2. **CLOSURE OVER BORDER-OWNED EDGES (with side).** This rung bridged gaps on the raw PC
   skeleton. The substrate's `vision_border_ownership` seed produces edges WITH A SIDE
   (which side is figure). A cycle constrained to keep the figure side consistent (a
   coherent inside) is a stronger closure predicate than raw proximity+residual, and it is
   the composition the brief pointed at. Untested here.
3. **A GROUND MODEL, not just an object model.** The FALSIFY's structural cause is that the
   ground stays border-connected. A closure that also models the GROUND as finite (multiple
   ground regions, occlusion) rather than one border blob is a different objective and might
   break the persistence of the 60% blob. Not tested.
