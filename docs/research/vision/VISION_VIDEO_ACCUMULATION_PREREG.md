# DOES WATCHING VIDEO CHANGE THE CODEBOOK USEFULLY? — PRE-REGISTRATION

*Written and committed BEFORE any confirmatory number. Branch
`worktree-agent-aa3401683daf142ef`, base `5428104a`.*

**Seed block: 74000–74999.** 74900–74999 are **DECLARED BURNED PILOT** seeds,
consumed before this document by `scripts/video_accum_pilot.py` (bring-up) and
`scripts/video_accum_calibrate.py` (the §1 measure calibration, whose result is
quoted in §2 below and which did **not** run the confirmatory contrast).

**Engine (§10):** `25fa11652e83` @
`runners/dsl/python/substrate_rs/_native.abi3.so`, a **shared build from the
canonical tree, Rust source verified byte-identical**. **This rung adds NO Rust,
NO Term, NO seed rule and NO constant to the engine.** `scripts/engine_build.sh`
is therefore not the operative step; `tests/test_engine_provenance_migrated.py`
+ `tests/test_provenance_endpoint_guard_migrated.py` were run **as their own
step before any number: 630 passed, exit 0.** `data/` symlinked; baseline
oracle `bash scripts/rung7_vision_bench.sh` → **222 passed, exit 0** (149.1 s),
captured before any measurement.

---

## 0. THE QUESTION

**After watching N frames of real video, is the held codebook DIFFERENT, and is
the difference USEFUL?**

Every rung in this arc to date has measured a *comparison*. None has produced an
accumulation event. This rung grows a codebook from video and asks whether the
growth is worth anything — against the controls that make "worth anything"
mean something.

**A rising recognition curve alone proves nothing.** The trivial explanation is
that the codebook got bigger. The controls below are the rung.

---

## 1. THE MECHANISM UNDER TEST — ARM B ONLY, UNMODIFIED

`seeds/vision_identity_seam.json` (the NCC seam), byte-unchanged, armed. **Not
the stock sd loop**: the identity-seam rung measured the stock loop
force-matching **64/64 value-shuffled tiles on both corpora** because
`Count(residual)==0` is vacuous over a compositional decode. A system that
cannot refuse cannot accumulate meaningfully, so the stock loop is out of scope
here and that exclusion is a citation, not a new finding.

Recognition and minting are decided by the five seed rules
(`is_recalib`/`is_score`/`is_calib_done`/`is_decide`/`is_mint`). The accept
decision is `is_max > is_floor`, where `is_floor` is the **measured** maximum
NCC that the same comparator achieves against the same codebook on `G2c`
calibration noise. **No numeric threshold is hand-set anywhere (§13).** The
codebook is the only thing that changes.

The adapter (`domains/video_accumulation_world.py`) adds exactly two mechanical
facilities and no decision:

- **`install_codebook(entries)`** — writes `ShapeSignature` nodes with
  `seam_grown = 1.0`. Input construction, the same class as the seam rung's
  declared "codebook insertion order".
- **`freeze()` / `refreeze()` / `assert_frozen()`** — holds the codebook FIXED
  across an evaluation pass so that held-out observation #800 is scored against
  the same codebook as #1. `refreeze()` demotes (`seam_grown → 0.0`) every held
  signature whose node id is not in the recorded frozen set — an unconditional
  write over a set difference, not a branch on graph state — and re-arms the
  floor by resetting the `G2c` probes' `calib_epoch`. **`assert_frozen()` is the
  gate: K and the measured floor must be bit-identical at the start and end of
  every pass, and it raises otherwise.**

## 2. THE MEASURE IS GATED FIRST (§1) — AND IT CAUGHT A BLIND READ-OUT OF MINE

`scripts/video_accum_calibrate.py`, C1 only, pilot seeds 74902–74904. It
compares an **IDEAL** codebook (the grown one) against a **NULL** codebook (K
entries of pure calibration noise, holding no video content at all). It
deliberately does **not** run the size-matched control, which is the
confirmatory contrast.

**THE FIRST RUN REPORTED `accept = 1.0000` FOR BOTH ARMS — delta `+0.0000`,
zero variance.** That is the §1.1 dead-arm signature exactly. The cause was
**my read-out, not the substrate**: `is_decide` writes `status = "is_held"` or
`"is_novel"`, and `is_mint` then rewrites `"is_novel"` → `"is_minted"`, so the
test `status != "is_novel"` scored every *minted* observation as *recognised*.
Corrected to `status == "is_held"`. **This is recorded because a calibration
pass that had been skipped would have shipped a read-out that reads 1.0 on
noise.**

Corrected calibration (n = 50 held-out frames, K = 37):

| read-out | IDEAL | NULL | delta | sd (ideal, per frame) |
|---|---|---|---|---|
| accept rate | **0.9988** | **0.3137** | **+0.6850** | 0.0088 |
| mean best-NCC (`is_max`) | **0.8229** | **0.3660** | **+0.4568** | 0.0460 |

and both move with codebook size in the ideal arm:

| K | accept | mean best-NCC |
|---|---|---|
| 9 | 0.7338 | 0.5711 |
| 18 | 0.8512 | 0.6477 |
| 37 | 0.9988 | 0.8229 |

**DECLARED IN ADVANCE FROM THIS TABLE: the accept rate SATURATES near the final
checkpoint (0.9988 at K = 37).** Therefore:

- **PRIMARY read-out: mean best-NCC (`is_max`) on held-out frames.** Graded,
  unsaturated at K = 37, and **independent of floor movement** — it isolates
  codebook quality from the floor's own drift.
- **CO-PRIMARY: accept rate**, reported at every checkpoint **with its measured
  ceiling declared here, before the contrast was seen.** A null on accept at the
  final checkpoint that coexists with a live signal at earlier checkpoints will
  be reported as a **ceiling artifact**, and that reading is fixed now rather
  than after looking.

## 3. THE CONTROLS — FIXED IN ADVANCE

### 3.1 THE SIZE-MATCHED CONTROL IS THE PRIMARY ONE

At every checkpoint the grown codebook has K entries, each minted from a
specific training observation. The controls hold **K identical** and vary
**only which observations are in it**:

- **GROWN** — the K MDL-gated mints, in mint order.
- **RAND-UNIFORM** *(the primary control)* — K training observations drawn
  **uniformly without replacement from every training observation presented up
  to that same checkpoint**. Seed `74100 + corpus_index`. Same frames, same
  regions, same encoder, same eval machinery; the *only* difference is that
  selection was arbitrary rather than MDL-gated.
- **RAND-CUTMATCHED** *(secondary, the decomposition)* — K entries, **one per
  grown mint, drawn from the SAME training frame as that mint but a uniformly
  random region**. Seed `74200 + corpus_index`. This matches the grown arm's
  *temporal* distribution — which is cut-concentrated — while randomising
  *which tile*. **If GROWN ≈ RAND-CUTMATCHED > RAND-UNIFORM, the value is in
  WHEN the system minted, not WHICH tile it chose.**

**If GROWN does not beat RAND-UNIFORM, there is no accumulation, only
accretion. That is stated here, before the run.**

### 3.2 HELD-OUT FRAMES, NOT TRAINING FRAMES

150 frames per corpus (`jellyfin_frames(150, every=2, start_s=300, size=24)`),
split into 15 contiguous blocks of 10. **Held-out = blocks 1, 4, 7, 10, 13**
(50 frames). **Training = the remaining frames MINUS a 1-frame guard band
either side of every held-out block** (90 frames), so no held-out frame is the
temporal neighbour of a training frame it could be recognised *through*.
Verified: `train ∩ held = ∅`, `|train| = 90`, `|held| = 50`.

**No mint ever comes from a held-out frame**, and every evaluation pass is
frozen (§1).

### 3.3 CHECKPOINTS

After **10, 25, 45, 65, 90** training frames. At each, all three arms are
evaluated on all 50 held-out frames, in a **fresh substrate** built the same
way for every arm (boot → 8 `G2c` calibration draws from seed
`74400 + corpus_index`, identical across arms → `install_codebook` → freeze).
Building all three arms identically is what makes the contrast a codebook
contrast.

### 3.4 CUT STRATIFICATION — THE SPECIFIC HAZARD

The seam rung measured mints **16.7× concentrated within 3 frames of a scene
cut**. Cuts are where the frame-to-frame prior is invalid, so the mints may
encode *discontinuity artifacts* rather than content.

Cuts are marked by the **existing parameter-free Otsu rule** on each corpus's
own per-step motion (`cut_flags`, verbatim from the seam rung; C1 marks steps
[34, 47, 79]).

**Tested directly at the final checkpoint:** for every GROWN codebook entry,
count how many held-out observations selected it as the `Argmax` (its
**usage**). An entry with **zero** held-out usage is **DEAD**.

- Reported as a **continuous** quantity — usage against frames-to-nearest-cut —
  so nothing depends on a chosen window;
- and, because the seam rung's window is the incumbent, **also** at its
  inherited **W = 3** split (near-cut vs far-from-cut), declared here rather
  than chosen after looking.

**If the codebook is mostly dead cut artifacts, accumulation is illusory and
that is the finding.**

### 3.5 ORDER

A **SHUFFLED-ORDER** arm: the same 90 training frames presented in a permuted
order (seed `74300 + corpus_index`), grown the same way. Compared on final K and
final held-out primary read-out. A curriculum effect would show order-dependence;
its absence is informative but not fatal.

### 3.6 REFUSAL MUST SURVIVE

At the **final** checkpoint, in the frozen GROWN world, present 64 probes each
of **NOISE**, **SHUFFLE** (value multiset preserved, arrangement destroyed),
**BSDS** (photographs from a different corpus) and **CONTROL** (genuine held
training regions), seed `74500 + corpus_index`. `novel_handled` = minted **or**
refused, exactly as the seam rung defined it. The comparison is CI-separation
above the matched CONTROL.

**This exists so the rung cannot buy a recognition curve by making recognition
permissive** — the failure mode the stock loop already demonstrated.

## 4. THE GATE IS A CONJUNCTION

1. **RECOGNITION IMPROVES ABOVE THE SIZE-MATCHED CONTROL.** At the final
   checkpoint, GROWN's mean best-NCC on held-out frames is **CI-separated above
   RAND-UNIFORM**, on **both** corpora. (Accept rate reported alongside, with
   its declared ceiling.)
2. **THE CODEBOOK DOES NOT GROW WITHOUT BOUND.** Mints per training frame in
   the **last** quartile of training < the **first** quartile, on both corpora.
   A constant mint rate means nothing is being learned, only logged.
3. **REFUSAL SURVIVES.** At the final checkpoint, NOISE and SHUFFLE
   `novel_handled` are **CI-separated above CONTROL** on both corpora.

**All three must hold. Any one failing is reported as a failure of the
conjunction, not rescued by re-cutting the measure (§5).**

## 5. STATISTICS

Unit of analysis = **held-out frame** (mean over its 16 regions), n = 50, paired
across arms by frame, 95% paired t-CI. **Per corpus, NEVER pooled.** Frames
within a block are heavily autocorrelated, so n = 50 overstates the effective n:
**no p-value is quoted anywhere**, only CIs. Probe classes in §3.6 are
independent draws, so their comparison is unpaired, matching the seam rung.

## 6. PREDICTIONS (scored afterwards, right or wrong)

| # | prediction |
|---|---|
| P1 | Both read-outs rise with K in **all three** arms — bigger codebook, more chances to match, no learning required. |
| P2 | **GROWN beats RAND-UNIFORM on mean best-NCC at the final checkpoint, CI-separated, on both corpora.** I expect this one to pass: MDL selection minted each entry *because* nothing held matched it, so the grown set is diverse by construction while a uniform draw contains near-duplicates. |
| P3 | On **accept rate** at the final checkpoint the contrast is **NULL or much smaller**, because GROWN is at the 0.9988 ceiling measured in §2. |
| P4 | **GROWN ≈ RAND-CUTMATCHED** (no CI separation) and both > RAND-UNIFORM — i.e. most of the value is in WHEN the system minted, not WHICH tile it chose. This is the prediction I hold most weakly and the one whose refutation would be most informative. |
| P5 | Mint rate declines from the first to the last training quartile, but **weakly and confounded by cut placement** — the decline will not be a clean saturation curve. |
| P6 | **Cut-minted entries are NOT dead.** I bet against the brief's hypothesis: a tile at a cut frame is still a real video tile, and the post-cut shot is most of the remaining footage. I predict the dead-rate is **similar** for near-cut and far-from-cut entries. |
| P7 | Refusal survives on NOISE and SHUFFLE, and **fails on BSDS**, reproducing the seam rung. The CONTROL false-novel rate stays materially above zero. |
| P8 | Shuffled training order gives a codebook of **similar size** and **similar** final held-out score — no curriculum effect. |

## 7. WHAT WOULD MAKE THIS RUN VOID

- Either corpus's episode id failing its pin (C1
  `08630d4b7b215c469df19b9c42d7b617`, C2 `119eca433329b36b19e5d69fef84966e`).
- `assert_frozen()` raising in any evaluation pass.
- Any edit to `seeds/vision_identity_seam.json`, to any Rust source, or to the
  default boot set.

## 8. BOUNDS DECLARED IN ADVANCE (§8)

- **24×24 grey, 6×6 regions, k=4, two episodes of two series, 150 frames each.**
  This is a demonstration that accumulation does or does not occur **on this
  corpus at this resolution**. It is **not** a claim about learning at scale.
- Regions are an **adapter-chosen grid**. Nothing here routes through
  proto-objects, border ownership or segmentation, and no object label exists
  anywhere in the measurement — so "recognition" means *region identity against
  a held codebook*, nothing more.
- The three arms share the encoder, the eval machinery and the calibration
  draws; they differ **only** in codebook membership. That is the intended
  contrast and also its limit — nothing here tests a different featureset.
- **A clean negative is a full result and will be reported as loudly as a
  positive.** The specifically plausible negative — the codebook grows but
  recognition does not improve above the size-matched control, i.e. the system
  **accretes without accumulating** — is named here so that it cannot be tuned
  away.
