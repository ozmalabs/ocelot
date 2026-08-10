# SCALE THE EYE'S RESOLUTION — PRE-REGISTRATION

*Committed BEFORE any headline number (§3). Nothing below this line is a
result. The only numbers quoted here are (a) inherited from committed rungs and
named as inherited, or (b) from a SCOPING PILOT run on the ALREADY-BURNED
`70000` block (§3.3), reported as scoping and NOT as a finding.*

**Branch:** `worktree-agent-a894edf46d0235e74` — the intended
`gamma-substrate/resolution-scale` was **NOT provisioned**, and I report the
branch I actually see. **Sixth rung in a row under an auto-generated name.**

**Engine (§10):** built with `scripts/engine_build.sh` (never a bare
`cargo build`) → **`d6097900e8b5`**. This tree's Rust source is byte-identical
to canonical (`diff -rq runners/dsl/src` reports only the untracked,
uncompiled `py.rs.selfmod.bak` in canonical).
**The provenance gate was run as its own step before any number:
`tests/test_engine_provenance_migrated.py` + `test_provenance_endpoint_guard_migrated.py`
→ 633 passed, exit 0.**
**Oracle:** `bash scripts/rung7_vision_bench.sh` → **222 passed, exit 0**
(`data/` symlinked, so the oracle's condition is the 222/0 one).
**Machine:** AMD Ryzen 5 9600X, 12 logical cores. Load average at pre-reg
0.83. **A concurrent rung is running**; every wall-clock number will be
reported with the load state beside it, and every other quantity is
deterministic under fixed seeds.

**Seeds:** block **79000–79999**. Sub-allocation, fixed here:
**79000–79199** resolution arms (verdict world) · **79200–79399** the K arm
(accumulation world) · **79400–79999 reserved, and any unspent range will be
reported as returned intact.** The concurrent rung's **78000–78999 is not
touched.** The scoping pilot drew **70000 only** — already burned by
`VISION_VERDICT_RESULTS.md`, per §3.3, so **no confirmatory seed was spent on
scoping.**

---

## 1. WHY, AND WHAT THIS RUNG IS NOT

Everything in the video line was measured at **24×24 grey with 6×6 regions**
(`domains/verdict_comparator_world.py`: `REGION = 6`, `GRID = 24`). Two
independent motivations, and they are **different claims that must not be
allowed to rescue each other**:

**STATISTICAL.** `VISION_K_SCOPE_RESULTS.md` (merged `6b50b97a`) found nearly
all variance lives BETWEEN 10-frame blocks — block-mean spread **20.3× (C1)**
and **8.4× (C2)** what independent frames could produce, so **effective n is
nearer 5 than 50** and frame-unit CIs are ~3× too narrow. The motivating
hypothesis is that more distinguishable regions per frame buys back
independence.

**REPRESENTATIONAL.** The salience re-score named its binding limitation as
*"a 4×4 grid of 6×6 tiles cannot express object-level salience"*, and
proto-objects have produced nothing on real frames across two probes.

**This rung is not a proto-object rung.** It measures whether the pipeline
runs at higher resolution, whether effective n rises, whether recognition
survives, and what it costs. Proto-objects are named-not-built here.

### 1.1 NOTHING TRANSFERS BY ASSUMPTION

Every landed number in this line is at 24×24. **The noise floor is already
known to move with codebook size** (0.4973 grown vs 0.3872 uniform,
`VISION_VIDEO_ACCUMULATION_RESULTS.md`), so it will move with resolution.
**Floors are re-measured at every configuration and none is inherited.** Every
constant that IS inherited is named as inherited in §2.3.

---

## 2. THE DESIGN

### 2.1 TWO AXES, SEPARATED, SHARING ONE ORIGIN

**They answer different questions and are reported separately. Conflating them
produces an uninterpretable result.**

* **SCALE** — more regions at fixed region size. Tests whether scale buys
  independence.
* **GRAIN** — larger regions at fixed region count. Tests whether structure
  appears when a region covers more of the image.

The two are defined relative to each other **at fixed `GRID`**: at `GRID = 48`
a SCALE region (6×6) covers 1/64 of the frame and a GRAIN region (12×12)
covers 1/16 of it — 4× the image per region, which is the sense in which a
GRAIN region "covers more image".

| id | GRID | REGION | n_regions | cells/region | chance | axis |
|---|---|---|---|---|---|---|
| **B**   | 24 | 6  | **16**  | 36  | 0.0625 | **origin of both axes — the re-earned baseline** |
| **S48** | 48 | 6  | **64**  | 36  | 0.0156 | SCALE |
| **S72** | 72 | 6  | **144** | 36  | 0.0069 | SCALE |
| **G48** | 48 | 12 | 16      | **144** | 0.0625 | GRAIN |
| **G72** | 72 | 18 | 16      | **324** | 0.0625 | GRAIN |

`GRID` is the frame size the corpus is decoded to
(`jellyfin_frames(..., size=GRID)`), so a larger `GRID` is genuinely more of
the source video's detail, not an upsample.

### 2.2 CORPORA — REPORTED PER CORPUS, NEVER POOLED

**C1** cartoon (`episode_index 0`, pin `08630d4b7b215c469df19b9c42d7b617`,
"Parker Gets Rich") and **C2** live-action (`episode_index 3`, pin
`119eca433329b36b19e5d69fef84966e`, "Penguin SOS"). **The pins are checked at
run time and a mismatch VOIDS the run.** Both pins are the accumulation
rung's, verified already-matching on the cached decodes.

**The corpora have disagreed five times and are never pooled.** C3 (BSDS
photos) is **named-not-built** here: it is a static-photo corpus and carries
no block structure, so it cannot serve the effective-n gate, which is this
rung's primary.

### 2.3 WHAT IS HELD FIXED, AND NAMED AS INHERITED

* **Verdict = V3 / NCC.** Inherited from `VISION_VERDICT_RESULTS.md`, the only
  arm that passed all three of its clauses. **Not varied here.**
* **RHO = 2.** Inherited from `VISION_INVARIANT_COMPARATOR_RESULTS.md`'s
  measured knee. The proposal layer, **not varied here**. Note in advance:
  ρ is in PIXELS, so on the GRAIN axis the orbit covers a smaller fraction of
  a larger tile. **This is a declared limitation of the grain arm, stated
  before the measurement, not after it.**
* **K_LEVELS = 4.** Inherited. NCC scores the raw grey tile, so K bears only
  on the quantized tie statistic.
* **Probe set** — per base frame: `A1|d1`, `A1|d5` (identity at Δ), `A2|d1`
  (distant frame), `A3|d1` (arrangement-destroyed floor), `G1` (identical
  frame ceiling), `G2c` (noise draw that CALIBRATES the refusal floor), `G2t`
  (an INDEPENDENT noise draw that TESTS it). G2c/G2t stay separate draws so
  the refusal control is not the tautology "the max of a set does not exceed
  itself".
* **n_base = 50** frames per corpus, **5 contiguous blocks of 10** — the K-scope
  block structure exactly, so the decomposition is directly comparable.

### 2.4 A DEFECT FOUND IN SCOPING, DECLARED AND FIXED BEFORE MEASURING

The scoping pilot surfaced a **read-back defect that is latent in every rung
built on this adapter**: `verdict_comparator_world.read()` parses the region
name with a fixed 2-digit field (`int(said[1:3])`, `len(ans) == 3`). Region
names are written `f"r{i:02d}"`, so at **≥100 regions the parse is silently
WRONG** — `r143` reads as region 14. It is invisible below 100 regions and
therefore never bit before; **S72 (144 regions) is the first configuration
that reaches it.**

**The fix is a width that is a function of the codebook size** — `max(2,
len(str(n-1)))` — which is **byte-identical below 100 regions** and therefore
cannot move any landed number. **Declared gates:** the oracle re-runs at
**222/0** after the fix, and B reproduces byte-identically against the
pre-fix path.

**`true_is_max` is computed from the reference and does not pass through the
parser, so it is defect-independent; the accuracy read-out is not.** The
primary is therefore stated on `true_is_max` (§2.5) and accuracy is secondary.

### 2.5 THE READ-OUTS

* **PRIMARY — `true_achieves_max`**: does the TRUE region attain the maximum
  score over the whole codebook? Parser-independent; the incumbent's own
  primary; directly comparable to `VISION_VERDICT_RESULTS.md`.
* **SECONDARY — accuracy** (`answer_idx == truth`), after abstention.
* **Refusal rate** on `G2t`, against the floor calibrated on `G2c` **at that
  configuration** (re-measured, never inherited).
* **Cost**: `run_rules` wall-ms, plus the COUNTED quantity
  `n_regions² × 25 × cells` (candidate cell-comparisons per probe), which is
  load-independent.

---

## 3. THE GATES, AND THE DECISION RULES, FIXED NOW

**G1 — THE PIPELINE RUNS.** Every configuration completes retina → identity
without error, and the graph's choice agrees with the independently computed
reference. **Threshold: graph/reference agreement = 1.0000 at every
configuration.** If it does not, the gate FAILS and I name what broke first.

**G2 — THE EFFECTIVE-N GATE. THIS IS THE PRIMARY, AND IT IS A REAL GATE.**
Per configuration and corpus, take the per-frame mean of the primary over its
regions (n = 50, 5 blocks of 10) and decompose between-block against
within-block variance. Report **ICC** and
**n_eff = n / (1 + (m − 1)·ICC)**, m = 10.

> **DECISION RULE, FIXED IN ADVANCE: the statistical motivation for scaling is
> SUPPORTED iff n_eff rises along the SCALE axis (B → S48 → S72) on BOTH
> corpora. Otherwise it is REFUTED, and I will report it in exactly those
> terms — that higher resolution does not buy back independence, and the
> statistical argument for scaling this eye is dead.**

**A refutation here is a first-class finding and is worth more than a working
pipeline.** It is not softened, reinterpreted, or set against any other arm.

**G3 — RECOGNITION DOES NOT DEGRADE**, against the **re-earned B baseline**
measured in this same run under this same engine.
**The scale and grain axes are judged differently, and this is fixed now:**

* On the **GRAIN** axis `n_regions` is fixed at 16, so chance is fixed and the
  raw primary is **directly comparable**. **This is where the degrade verdict
  is binding.**
* On the **SCALE** axis the candidate set grows 16 → 64 → 144, so a raw fall
  is expected from task difficulty alone. **The raw comparison is NOT
  apples-to-apples and will be labelled so.** Both the raw primary and a
  chance-corrected form are reported, and **no pass is claimed on the scale
  axis from the chance-corrected number alone.**

**G4 — COST IS STATED PER CONFIGURATION**, counted, with load beside every
wall-clock figure.

---

## 4. THE K ARM — PERCEIVED RESOLUTION AS A FUNCTION OF THE CODEBOOK

Pre-registered at the coordinator's request, **before any headline of this
rung had been computed** (only the burned-block scoping pilot had run).

**The hypothesis, which may invert this rung's premise:** perceived resolution
is a function of the CODEBOOK, not the SENSOR. The developmental case:
newborn acuity is ~20/400 while the optics mature well ahead of the percept;
the adult case is sharper, since someone shown something genuinely unfamiliar
has a fully mature retina and still cannot resolve it — "I can't tell what I'm
looking at" is the honest report of a decode with a large residual and no held
parts to cover it. This arc already measured the matching asymmetry:
perception went linear and cheap while recognition stayed at **55×** and is
what caps usable resolution.

### 4.1 THE ARM

**Hold input resolution FIXED and vary K.** Configuration: the accumulation
world (`domains/video_accumulation_world.py`) at **fixed `GRID = 72`,
`REGION = 6`** — the highest resolution this rung reaches, so the sensor is
held at its most generous while the codebook varies. Measure, as K grows:

* **(a) DECODED FRACTION OF THE FIELD** — `accept`, the fraction of presented
  regions whose status is `is_held` (already computed by `eval_pass`).
* **(b) PERCEPT FINENESS** — **the number of DISTINCT codebook entries used to
  cover one frame**, and the normalized entropy of that usage distribution
  (both from `eval_pass`'s `usage`). *A finer percept is one covered by more
  distinct parts.* Defined here, in advance, and not changed afterwards.

**Prediction: both track K rather than pixel count — the same input yields a
finer percept as parts accumulate.**

### 4.2 THE TWO KNOWN CONFOUNDS, HANDLED EXPLICITLY

**CONFOUND 1 — K IS A DRAW, NOT A SETTING** (32/31 at seed 74000 vs 24/27 at
75000, same code and frames). **Control: K is NOT swept by re-seeding.** A
SINGLE growth run at ONE seed is truncated to **nested prefixes** of its own
mint order (the checkpoint mechanism `video_accum_measure.py` already uses).
The codebooks are therefore **strictly nested** — every smaller K is a prefix
of every larger one — so **which entries are present varies only by the mint
order the growth itself produced**, never by a different draw. **Truncation
changes which entries are present, not merely how many, and the nesting is
what makes that change interpretable rather than arbitrary.** Stated because
it is a real property of the design, not a disclaimer.

**CONFOUND 2 — A GROWN CODEBOOK RAISES ITS OWN MEASURED NOISE FLOOR** (0.4973
vs 0.3872) and is more conservative because better stocked, so a
decoded-fraction comparison across K rides a **moving criterion**.
**Control: every K is reported TWICE** — once at its **own re-measured floor**,
and once at a **FIXED floor held constant across all K** (the floor measured
at K_max). **The hypothesis is credited only if the effect survives the FIXED
criterion.** If it appears only at the per-K floor, it is a criterion artifact
and will be reported as one.

### 4.3 THE FIREWALL BETWEEN THE K ARM AND G2

**The K arm is a separate question about a different variable. It is not a
reinterpretation of the effective-n result and MUST NOT be used to soften it.**
G2's decision rule (§3) stands exactly as written above and is evaluated
independently. **If G2 refutes the statistical motivation, that refutation is
reported plainly and in full, whatever the K arm shows, and this document
records in advance that the K arm licenses NO change to the G2 verdict.**

---

## 5. PREDICTIONS, RECORDED SO THEY CAN BE REFUTED

* **P1** — the pipeline runs at all five configurations (G1 passes).
* **P2** — n_eff RISES along the SCALE axis on both corpora (G2 supported).
* **P3** — the raw primary FALLS on the scale axis (larger candidate set) and
  does NOT fall on the grain axis.
* **P4** — graph cost grows about quadratically in `n_regions` on the scale
  axis and about linearly in `cells` on the grain axis.
* **P5 (K arm)** — decoded fraction and distinct-parts-used both rise with K
  at fixed input resolution, and survive the fixed criterion.

**I expect at least one of these to be wrong, and the wrong one is the
finding.**

---

## 6. BOUNDS DECLARED IN ADVANCE

* Two corpora, both video, both from one Jellyfin catalogue. **No photo
  corpus, no third domain.**
* `GRID` reaches **72**. 1080p is not attempted and is out of scope.
* ρ = 2 is held in PIXELS across both axes (§2.3) — a declared limitation of
  the grain arm.
* The verdict is fixed at NCC; **no verdict × resolution interaction is
  measured**, and none will be claimed.
* Proto-objects and object-level salience are **named-not-built**.
* n_eff is estimated from **5 blocks**. Five is few, the estimate is
  correspondingly coarse, and it is stated here rather than discovered later.
