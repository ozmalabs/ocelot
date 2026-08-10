# The Omniglot Drawn-Shape Arc — Consolidation

Status: closed research arc. Commits `26f74039` (2026-07-02, "OMNIGLOT GATE") through
`4d901133` (2026-07-05, "RUN 38"). 38 numbered gated runs, three agent fork-decisions,
one corpus-identity reframe. This document is the arc's record, written against
`git log`, `results/omniglot_gate_run*.log`, `results/transfer_gate_run24.log`, and
the running memory chronicle (`ozma_dynamic_quantization_core_loop.md`).

Every accuracy number below carries n and a 95% Wilson CI where the source run computed
one; where a number is a raw point estimate from an underpowered run, that is stated.
Every number carries the commit hash or log file it came from.

---

## 1. Summary

**What was built.** A graph-native, training-free, drawn-shape recognition and
generation system, running on the Rust substrate (`substrate_rs`) per this project's
architecture rule — no Python agent decisions, decode/growth expressed as `run_rules`
fixpoints over graph data. The core mechanism is **dynamic quantization**: shape
recognition is decode-against-a-held-codebook (dequantization), order-N growth is
the same operation run to grow the codebook (mint a quantum from an unexplained
residual), and the two are literally one Rust `ShapeDecode` Term plus a four-rule
loop (`sd_decode` / `sd_recognize` / `sd_mint_quantum` / `sd_redecode`,
`seeds/shape_decode_loop.json`). On top of that: a four-rung Occam growth ladder
(exact match → transform-in-basis → infer-a-dimension → mint-novelty), stroke-level
quantization/rendering that are exact functional inverses, character-level
composition (arrangement of strokes) as the same loop one level up, Analysis-by-
Synthesis (AbS) as the default read path (generation and reading are one model run
in reverse), and — very late in the arc — a full accounting of the corpus itself as
a physical signal source (mouse-drawn pixels, not pen strokes).

**What it measures, standing numbers (all Omniglot 20-way one-shot unless noted):**

| Quantity | Value | n | CI | Source |
|---|---|---|---|---|
| Full-dwell verdict (parse-marginal SC+TPS) | **80.5%** | 400 | [76.3, 84.1] | `2c669fd1`, confirmed `6da31cee`/run 26 reproduction |
| Coverage@10 after committed-shape proposal | **76.5%** | 400 | [72.1, 80.4] | run 37B, `6c1483b6` |
| Shortlist accuracy after committed-shape proposal | **66.0%** | 400 | [61.2, 70.5] | run 37B |
| Coverage@10, pre-37B baseline | 71.5% | 400 | [66.9, 75.7] | run 26 |
| Shortlist accuracy, pre-37B baseline | 62.0% | 400 | [57.2, 66.6] | run 26 |
| 50-way full-dwell | 84.8% | 250 | [79.8, 88.7] | run 24, `1d4d0fbb` |
| 50-way 3-modality proposal union, accuracy | 70.75% (log rounds 70.8%) | 400 | [66.1, 75.0] | run 38, `4d901133` |
| 50-way 3-modality proposal union, coverage | 78.75% (log rounds 78.8%) | 400 | [74.5, 82.5] | run 38 |
| Zero-adaptation transfer, non-character symbols, one-shot 20-way | **96.7%** | 240 | [93.6, 98.3] | run 24 transfer gate |
| BPL (Lake et al.) reference, human-level one-shot | 96.7% | — | — | cited anchor, entry 11 of the chronicle |
| Unweighted round-trip fidelity ceiling (practice loop) | ~0.84 (0.8356) | 40 chars | — | run 27/29/31 |

**The two headline meta-results:**

(a) **Every corridor this featureset opened was closed by pre-registered
measurement.** Six independent verdict-layer levers null against the 80.5 control
at power (finer theta grid, cross-grain fusion, exemplar-nuisance marginalization,
tuned fusion weights, ensemble members, and the run-15 branch nulls) — the number
is a measured ceiling, not an unexplored plateau. The homework/practice loop closed
the same way from a fifth direction (span-shredding blocks stroke novelty,
calibration ≠ repair, render-side geometry unreachable). The representation itself
was twice put to an agent fork-decision and twice declined a rebuild.

(b) **The corpus is not handwriting — it is mousewriting.** Omniglot's strokes are
browser/mouse-drawn MTurk traces (median inter-event time 15ms, ~59-65% integer
pixel deltas, ~56-60% exactly-0° turns from Bresenham rasterization). This
retroactively explains most of the arc's stroke-grain findings: the two-thirds
power law (ballistic pen kinematics) is essentially absent (median r² = 0.084 vs
the law's expected slope −0.333); per-stroke identity collapses to one shape family
because a servo-tracked mouse carries almost no per-stroke information; "writer =
style family, not one slant" because person+mouse is a ratchety composite effector.
The corpus-conditional findings are flagged throughout §5. The method-level laws
(composition, AbS, bins-propose/continuous-decides, powered gates, count-matched
nulls) are architecture, not corpus artifacts, and are expected to transfer.

---

## 2. The system

### 2.1 Dynamic quantization as one loop

The creator's reframe (2026-07-02): *"shape matching is dequantisation, and
order-N can be dynamic quantisation."* Recognition decodes an observation
against a held codebook of `ShapeSignature`s; when decode leaves a residual,
growth mints a new codebook quantum from exactly that residual; the next decode
sees the grown codebook. This is one Rust Term (`ShapeDecode`,
`runners/dsl/src/shape_decode.rs`) run inside a `run_rules` fixpoint
(`seeds/shape_decode_loop.json`): `sd_decode` proposes a fit, `sd_recognize`
accepts it if complete, `sd_mint_quantum` fires only on failure, `sd_redecode`
re-fires decode once `codebook_epoch` shows growth. The composer's old beam
search and the concern-inducer's old coverage-then-mint collapsed into this one
Term when the migration landed (`28454782`, prior to this arc).

Two related reframes, same day: **"flood does not occur per pixel, it occurs at
quanta, and if there's a remainder it goes to more detail"** — detail budget is
spent only where decode fails, for ink as much as for space-quantization; and
**"quanta is dynamic per dimension"** — turn angle and segment length quantize
on independently-chosen bin edges, and refinement recurses along whichever
dimension actually carries the residual.

### 2.2 The four-rung Occam growth ladder

**"Transformation isn't transformation. It's quantum change in a specific
dimension."** A rotate/scale/translate/speaker-shift is not a distinct operator
class — it is the object's quantum stepping along one dimension while the
others hold (unifying with ACTION, a controllable dimension); decode must
check identity + a per-dimension delta before minting novelty. **Caveat, same
day:** *"sometimes you need to INFER A DIMENSION before you transform —
rotating a flat 2D rectangle in Z gives you a transform in XY that can't be
replicated without Z."* A residual coupled across observed dimensions (no
uniform per-dim delta, but a 1-parameter family) signals a missing dimension;
the parameter itself is the new dimension. The resulting ladder, gated one rung
at a time by `run_rules`:

1. **Exact recognize** (`sd_recognize`) — literal decode against the codebook.
2. **Transform in the existing basis** (`TransformDecode`) — one uniform delta
   per transformed dimension; identity flagged; predicate slot never transforms.
3. **Infer the dimension** (`DimInfer`) — a coupled residual decodes against a
   held `DimensionGenerator` codebook (rotation90, reflections); a
   `LatentDimension` node is minted.
4. **Mint novelty** (`sd_mint_quantum`) — only after both prior rungs fail.

Landed and gated 9/9 (transform), 7/7 (dimension inference) before this arc
began (`518706ed`, `65f94b70`); the arc's stroke-level work is this ladder
applied to ink.

### 2.3 StrokeQuantize / StrokeRender — exact inverses, and segmentation-by-recognition

**"The physical limits of the writer become implied dimensions."** Ink
quantizes into `seg` relations (signed relative turn + normalized length —
rotation/translation/scale-invariant) plus pose as separate single-slot
relations (`pose_x/y/o/s`), so a similarity transform is always a rung-1 delta.
`StrokeQuantize` and its exact inverse `StrokeRender`
(`runners/dsl/src/strokes.rs`) round-trip: `StrokeQuantize(StrokeRender(sig))
== sig`, proven in `42855d5f`. Writer effector limits (slant, jitter, curvature
cap) pool across one hand's strokes into a minted `WriterStyle` latent — the
ink twin of the speech speaker/VTLN dimension (`seeds/writer_dimensions.json`).
Stroke boundaries are not pre-cut; a Hyp/LatEdge span lattice over arc-length
knots is decoded by the same grain-agnostic Viterbi (`vit_step`/
`vit_backtrace`) used for speech phone segmentation — one mechanism, two
domains.

### 2.4 Composition — the arc's single biggest effect

**Character = arrangement, not stroke shape.** A character's `ShapeSignature` is
built from its constituent stroke quanta plus quantized *relative-pose* relations
between strokes — the same `sd_*` loop one level up (`c1b83669`). This carried
one-shot Omniglot from chance (5.0%, multiset ablation control) to **33.8%**
initially, and the powered re-measurement (`f0fae1fe`, n=400) confirmed
**composition is +21pp over the multiset ablation** — the one fact in the arc's
first ten runs that survived power CI-separated. Composition is the largest single
lever measured anywhere in the arc.

### 2.5 Bins propose, continuous decides — the two-layer synthesis

**"The GENERATION and READING model is the same, like speech — AbS is the
default."** The codebook quantum is itself a generative/motor program: its
turns+lengths+pose render straight back to a polyline. Reading reverses the same
engine: propose a fast quantized-index shortlist, render each candidate, compare
via a held continuous comparator (`DtwTo`, later `ShapeContext+TPS+SmoothDeform`),
adjust. Run 16 (`7743c2de`) discovered that the arc's two apparently-contradictory
ceiling numbers (~81% historical vs. 26.8% powered) were both real — the difference
was the verdict comparator, not the featureset. Quantized bins carry the
learning/proposal signal (codebook growth, composition, transforms, writer
dimensions); continuous geometry (ShapeContext + Thin-Plate-Spline + smooth
deformation distance, fused, on raw points, training-free) carries the verdict.
"Bins propose, continuous decides" was re-confirmed end-to-end a second time at
the proposal layer in run 37B (§4): the same signal that failed as a *verdict*
featureset (run 35's coarse program-types, 1.9× vs a 2.0× bar) won as a *proposal*
featureset (+5pp coverage, McNemar-significant).

### 2.6 Frames — N axes with relative weighting

**"All weights are not vectors, they are edges to other nodes — weights are
relative, order-N and log scaled"** (creator, run-30 thread). A scalar weight in
a Python dict is invisible to `run_rules`; reified as a **Frame**
(`seeds/frame_weights.json`), a quantum's signature relations become axis
nodes, and stability becomes log-odds-valued, endpoint-relative weight *edges*
the rule engine can match, decay, compose, and pool. **"A frame is N
dimensions/axes with relative weighting"** unifies the vocabulary: quantum = a
position held in a frame; decode = frame-fit scored by the frame's metric;
DimInfer = frame extension; salience/variable-aperture dwell = the weighting
made dynamic. Preservation-gated exact to 16 significant digits against the
pre-reification baseline (`5b2eb4a6`, run 30).

### 2.7 Stepped-generator reframe (late, run 35)

**"Time is not a dimension, it is a series of collapses. Circles are not
circles, they are a 2D view of a sinusoid, that is itself, stepped."** Two
imports: time as a *collapse sequence* (the tick already is this — run 33's
attempt to import wall-clock time as a coordinate nulled, confirming the
collapse-count framing by elimination), and shape as a *stepped generator
program* whose trace is its shadow (a circle is `repeat(turn=k)×n`; a line is
`repeat(0)`; a hook is a change-point). The never-measured featureset this
implies — the step **program** (run-length/ramp structure across steps,
order-N *within* one stroke) — was gated (run 35, §4) and found real but not
licensed at this corpus's resolution; it stands as the named revival candidate
for true pen data.

---

## 3. Measurement discipline

This is the arc's most transferable product — a set of enforced habits that
repeatedly caught results that would otherwise have shipped wrong.

**Powered gates, n=400, Wilson CIs — after a correction that invalidated the
arc's first ten runs.** Runs 1–13 (composition through instance-conditioning) ran
on a **4-alphabet subset at n≈80** and produced an apparently rising trajectory:
33.8 → 37.5 → 38.8 → 41.2%. Run 15 (`f0fae1fe`) re-ran the identical machinery on
**10 alphabets at n=400** and found the honest ceiling was **26.8% [22.6, 31.3]**
— the 4-alphabet set had been an easy subset, and *every* post-composition delta
(AbS +3.7pp, dwell +1.3pp, appearance +2.5pp, rel2 −3.8pp, sub-stroke −1.2pp) was
1–3 episodes of noise, all arms falling inside each other's CIs at power; rel2 (a
"loser" at n=80) was numerically *top* at n=400. Composition's +21pp was the one
delta that survived CI-separated. **Standing rules minted:** power the gate before
the endgame (deltas within ~3× the per-episode step are not results); a
synthetic/gated mechanism proof is not the same claim as a benchmark-value claim
— report both; an eval-subset's alphabet/domain coverage is part of every
headline, not a footnote.

**Pre-registration with STOP branches, refusing outcome-tuning.** Several runs
wrote pass/fail bars *before* running the eval and refused to spend compute or
adjust the mechanism past a failed gate: run 22 hit a pre-registered STOP after
confirming the same identity-collapse wall a fourth way; run 26 hit a
pre-registered P2 STOP (surviving-residual series `[5,5,5,5]`, flat — eval
withheld); run 34a refused to widen a denoiser kernel past its own invertibility
bound to chase a dissolution target it would likely have then passed ("refused
as outcome-tuning"); run 35 stopped at two grains rather than try a third when
coarse missed its bar by ~5pp ("chasing the near-miss with a third grain would
be the metric surgery the arc's laws forbid").

**Control-chain exact reproduction.** Every run that reused a prior run's
control re-derives it and checks CI-overlap or exact-value match first: run
16's control (22.0% [16.8, 28.2], n=200) checked CI-overlap-consistent against
run 15's 26.8% [22.6, 31.3] (n=400); run 17's control reproduced run 15's 26.8%
exactly; run 26's full-dwell control reproduced run 25's 80.5% exactly; run
37C's baseline reproduced byte-identically (0 episodes flipped) confirming its
filter was diagnostic-only.

**Paired McNemar for small effects.** CIs cannot resolve a 2–5pp effect at
n=400 (overlapping bands), so from run 37B onward the arc adopted **paired**
significance testing on the same episode set: run 37B's coverage gain (71.5%→
76.5%) is McNemar 20 fixed/0 broken (structurally impossible to break — a
pure-superset union), shortlist-accuracy gain (62.0%→66.0%) is 18 fixed/2
broken, p=0.0004. Run 38's 50-way union (69.5%→70.75%) is 5 fixed/0 broken on
both metrics, p=0.0625 — one flip short of significance, reported as
underpowered rather than rounded up to a win.

**Count-matched nulls (run 33's density confound).** Naive boundary-agreement
favored velocity-minima segmentation (0.628 vs 0.420 for arc-length), but
velocity minima propose ~4× more candidates and agreement rises mechanically
with density (Monte-Carlo random points at matched density scored ~0.86 with
zero physics). Count-matched excess-over-chance reversed the verdict
(arc-length +0.066 vs. velocity-minima +0.022, robust over 11 configs). **Law:**
count-matched nulls are mandatory for any boundary-agreement claim.

**Engagement-vs-outcome reporting.** Run 31's Mechanism A (render the
stability-preferred parse) is reported as a *vacuous* null, not a negative
result — it never engaged (0 preferred renders fired; real data never produced
the >10/20 majority-alternative the mechanism needed). Distinguishing "the
lever never got pulled" from "the lever was pulled and did nothing" is now
standard; run 37A separately reports engagement breakdown (60.5%/39.5%
one-sided/two-sided) alongside its accuracy delta for the same reason.

**Verdict-wording bugs excised three times.** A `<=`-as-CONFIRMED (should be
strict-fall) bug was fixed at the source three separate times (named
explicitly in run 29's log). Run 34b independently caught an un-pre-registered
"entropy must rise" conjunct that was physically backwards (correct denoising
of a staircase artifact *collapses* fake angular diversity — entropy correctly
falls); the bug had hidden inside run 34a's double failure and was exposed only
once one criterion started passing.

---

## 4. The trajectory

| Run | Commit | 20-way result | What moved it |
|---|---|---|---|
| LEARN gate | `26f74039` | 2.5% (chance 5%) | learning saturates (67 quanta/3000 strokes); OOV exact-match fails |
| Refinement rung | `26df120c` | 3.8% (shuffled 1.2%) | coarse-to-fine tolerance ladder; OOV 81%→0% |
| Composition | `c1b83669` | **33.8%** (multiset control = chance) | character = arrangement, same loop one level up |
| Runs 4–9 (grain/metric probes) | `5f6ba026`…`e6a467e8` | 33.8/26.2/30.0×3 (all null or worse) | strictness-is-the-signal; finer grain fragments |
| AbS default | `42855d5f` | 37.5% | render-compare re-rank; first lever past composition |
| Variable-aperture dwell | `6db362d1` | 38.8% @ mean 2.05 renders | ambiguity-gated shortlist beats fixed K=5, cheaper |
| Second modality | `a6c7740f` | 41.2% | appearance (PointSetDist) proposal union |
| Instance-conditioning | `b1bbaf53` | 41.2% (null) | terminus: representation- and search-saturated |
| Sub-stroke (fork-1 branch A) | `9f10cf74` | 40.0% (null) | sub-stroke codebook collapses to 4 quanta |
| **Run 15 — powered correction** | `f0fae1fe` | **26.8% [22.6,31.3]**, n=400 | 4-alphabet subset was easy; composition +21pp survives |
| Run 16 — reconciliation | `7743c2de` | 73.5% [67.0,79.1], n=200 | verdict comparator, not featureset, explains the gap |
| Run 17 — full-n confirm | `1a10a378` | 68.8% [64.0,73.1], n=400 | tuned fusion/ensemble dead levers again |
| **Run 17b — waypoint** | `2c669fd1` | **80.5% [76.3,84.1]**, n=400 | parse marginalization (Family A's own Term) |
| Runs 19–23 — identity wall | `e43fba60`…`23f76f3e` | all null/harmful | five probes hit the same vocabulary ceiling |
| Fork 2 — representation | `f492c1b1` | decision | both faculties reject a rebuild |
| Run 24 — transfer gate | `1d4d0fbb` | **96.7% [93.6,98.3]**, non-char symbols | general drawn-shape recognizer, proven |
| Run 24 — 50-way residual | `1d4d0fbb` | 84.8% [79.8,88.7], n=250 full dwell | O(way) preprocessing is the scale lever |
| **Run 25 — verdict sealed** | `6da31cee` | 80.0–81.5% (6th null vs control) | ceiling established six ways; union +13pp |
| Runs 26–27 — homework loop | `41afebb7` | 71.5/62.0 flat, both runs | wrong grain (26); reading never mints (27) |
| Run 28 — first import | `9ca19365` | 71.5/62.0 flat | 40 quanta minted; import ≠ consumption |
| Run 29 — consumption wired | `0da44354` | 71.5–72.0/62.0–62.3 (in CI) | calibration ≠ repair; weighted 0.8356→0.8909 |
| Run 30 — frames reified | `5b2eb4a6` | architecture only | weights → graph-matter, exact preservation |
| Run 31 — geometry closed | `bb9e0fe4` | 0.7676 vs 0.8356 (worse) | render-side repair null and harmful |
| Fork 3 — five walls | `df70601e` | decision | tie/disagreement; creator calls option R |
| Run 32 — adaptive bins | `13ebc282` | cov 69.5/69.0 vs 71.5 (null) | entropy revives (0.0014→4.0 bits), instance-grain |
| Run 33 — momentum question | `81e6da1a` | mechanism gate | loader dropped timestamps; velocity null count-matched |
| Runs 34/b/c/d — mouse model | `70bdfc01`,`fb31eacc`,`8323f2a9`,`cc673ee1` | 82.8–83.5 (null vs 80.5); cov 72.0 flat | global smoother dissolves staircase 89.6%; 2×2 closed |
| Run 35 — stepped programs | `a85494d3` | Gate 0 only | coarse types 1.9× vs 2.0× bar — near miss |
| Run 36 — failure taxonomy | `5aa6bcb6` | diagnostic, n=400 | failure is a class property; 1–2-stroke classes fail most |
| Run 37A — contrastive verdict | `cca938fd` | 64.0% [59.2,68.6] (harmful) | focused evidence supplements, never replaces |
| **Run 37B — the win** | `6c1483b6` | cov 71.5→**76.5**, shortlist 62.0→**66.0** | committed-shape proposal (35's signal, redeployed) |
| Run 37C — hygiene | `651fd4a2` | byte-identical (0/0 flipped) | targeted fix confirmed, no production effect |
| **Run 38 — 3-way union, 50-way** | `4d901133` | acc 69.5→70.75, cov 77.5→78.75, n=400 | sign-consistent, zero-harm, under-powered (p=0.0625) |

The trajectory's own shape is the argument for the discipline in §3: point
estimates at n=80 rose monotonically for ten runs (2.5→41.2%) and were wrong by
a factor of ~1.5× on the ceiling; the powered re-measurement dropped to 26.8%,
and only the reconciliation with a stronger verdict comparator (run 16) recovered
a number (80.5%) close to the original informal anchor — for a *different*
mechanistic reason than any of runs 1–14 had proposed.

---

## 5. The corpus finding — mousewriting

**The momentum question (run 33, `81e6da1a`).** The creator asked whether the
arc was "missing something simple and stupid like the conservation of
momentum." Answer: yes, literally. Omniglot's raw motor files are `(x, y, t)`
triples; the loader parsed only `x, y` and silently discarded the timestamp
column for all 32 prior runs. Equal-arc resampling (used throughout to
normalize stroke length) is constant-speed normalization — the arc had
actively flattened the velocity profile and then measured the flattened
dimension as uninformative (run 32's "length = 1/segments exactly" finding was
this artifact's corpse).

**The grid facts** (replicated at 500-file scale, run 34): 65.3% of
point-to-point deltas are exact integers (pixel lattice); 59.5% of raw turn
angles are exactly 0° (Bresenham staircase runs, corroborated 56–60% by two
independent probes); median inter-sample time is exactly 15ms (~60Hz browser
polling). Signature of a mouse cursor sampled by a browser event loop, not a
stylus or ballistic pen. **The two-thirds power law is essentially absent**:
median r² = 0.084 across 20 writers (the ballistic-movement law predicts r²
near 1, slope −0.333; measured slope −0.081) — a dragged cursor has no
momentum; the physical mechanism is real, the corpus doesn't conserve it.

**The observation model is invertible.** Latent smooth intent → integer-pixel
quantization → 15ms event sampling. A local box-filter denoiser fails its own
invertibility bound and cannot dissolve the staircase past collinear Bresenham
runs of ≥3 samples (0.580→0.342 exact-0°, short of the >50% bar). The **global
constrained smoother** (max smoothness within the ±0.5px quantization band,
projected pentadiagonal solve) passes every gate: curved-path invertibility
0.186px RMS, straight-line fidelity 0.153px RMS (no hallucinated curvature),
point-mass dissolution **89.6%** (0.580→0.060). Correct specifically because it
is *global*: a local filter cannot see past a whole straight run to the
curvature underneath; a global smoothness objective can bow through the tube.

**The completed 2×2 (raw/denoised × uniform-bins/adaptive-bins) is the arc's
cleanest single result.** Four cells, each independently gated:

| | uniform bins | adaptive (data-placed) bins |
|---|---|---|
| **raw points** | 2 identities, 0.0014 bits (run 26/28 control) | 83 identities, 4.00 bits (run 32) |
| **denoised points** | 1 identity, ~0 bits (run 34c) | 1 identity, 0.0000 bits (run 34d) |

Run 32's apparent 83-identity revival was **100% pixel-noise artifact** — with
noise correctly removed *and* bins correctly placed, every real stroke at span
grain collapses back to one gently-curved-line family. Coverage@10 is flat across
all four cells (69.0–72.0%, all inside the 71.5% control's CI). **The mousewriting
stroke featureset carries approximately zero class-grain information at the span
level** — not from noise, not from bin placement, not from their interaction.
Identity lives in arrangement, and nowhere else in this featureset — this is the
mechanistic proof of what composition's +21pp (§2.5, §4) already implied
structurally.

**Corpus-conditional vs. robust, stated explicitly (per the task brief):**

- **Corpus-conditional** (true of Omniglot / mousewriting, may not hold for real
  pen data): stroke-grain-dead (~5–7 shape families), the exact 0.84 fidelity
  ceiling value, the identity collapse itself, "arrangement is everything" as a
  *magnitude* claim, "writer = style family not one slant."
- **Robust** (architecture, expected to transfer to any drawn-shape domain):
  composition as a mechanism, AbS as the default read/write model, bins-propose/
  continuous-decides, the homework loop, frames-as-weighted-axes, CFAR novelty
  calibration, count-matched-nulls-are-mandatory, powered-gates-before-endgame,
  and the benchmark comparisons themselves (BPL's own 96.7% is measured on the
  same mousewriting corpus, so the *gap* to BPL is not a corpus artifact).

---

## 6. Failure anatomy (run 36, `5aa6bcb6`, n=400, replay-verified)

**Low arrangement budget is the answer to "what do the failures have in
common."** 1–2-stroke classes carry 41–49% of proposal/shortlist failures vs.
21–24% at 4+ strokes; classes that never fail have a median of 3 strokes vs. 2
for classes that do fail. This is the system's own thesis (identity lives in
arrangement) predicting its own failure set: a glyph with no arrangement to
speak of has no identity in this featureset.

**Failure is a class property, not query noise.** P(fail | failed before) =
0.385 vs. P(fail | passed before) = 0.149 (n=200 classes, two replicates).
Cross-chain per-class failure-rate correlation (run 26 vs. independent run-34
chain, n=200): Pearson r = 0.358. 80 of 200 classes never fail either chain —
the residual concentrates in ~60 chronic classes.

**Two nearly-disjoint failure modes** (class-level Jaccard = 0.242, n=86
proposal-blind vs. n=63 full-dwell error classes, overlap=29):
proposal-blindness is stroke-count-driven (median 2.0–2.25 strokes vs. 3.0 for
neither); verdict errors are near-rank confusions (32.1% pick the rank-1/2
impostor vs. 10.5% chance) and flat across stroke count — but split inside:
multi-stroke confusions genuinely "differ by a hook" (median distinguishing-ink
fraction 0.187, n=30 pairs), 1–2-stroke confusions are whole-shape (ink
fraction 1.0). The dead stroke grain (§5) is fatal exactly there — precisely
where BPL's sub-stroke motor programs earn their edge, and where run 35's
near-miss program-types point as the named, un-built revival candidate.

**Corpus-side effect on the errors is weak** (nearest-impostor distance 0.227
failed vs. 0.239 passed, p≈0.13) — errors are comparator-side on
similar-difficulty geometry, not a doomed subset of episodes.

**Cheap artifact found:** 5/30 top confusion pairs are driven by degenerate
zero-length strokes (single-point strokes, concentrated in Keble/Kannada)
matched as the "distinguishing" element. Fixed by run 37C's hygiene filter — a
zero-effect fix at the eval level (the artifact distorted only run 36's own
per-stroke diagnostic, never the theta-grid verdict) but the cheapest real fix
found in eleven runs.

---

## 7. Laws minted

Each law below is a standing methodological or mechanistic finding, with its
originating provenance:

- **Strictness is the signal** (runs 7–9) — all-or-nothing joint-consistency
  arrangement matching (33.8%) beats every partial-credit relaxation (30.0%).
- **Only architecture moves the frontier** (arc-wide) — metric/verdict surgery
  (tuned fusion, ensembles, theta-grid resolution) never separated from control
  in ~10 attempts; every real gain came from a structural change.
- **Power the gate before the endgame** (run 15) — deltas within ~3× the
  per-episode step are not results; n=80 gave a false monotonic trajectory
  n=400 corrected.
- **Synthetic-proven mechanism ≠ benchmark value** (run 15) — report both, never
  substitute one for the other.
- **Different angles don't overlap** (run 12, re-confirmed runs 25/38) — a
  structurally-different proposal source adds candidates the first cannot reach,
  at 20-way and 50-way alike.
- **Import ≠ consumption** (run 28) — minting new quanta changes nothing
  downstream if nothing reads the new structure.
- **Calibration ≠ repair** (run 29) — a comparator can learn which relations to
  distrust (weighted arrangement 0.8356→0.8909) without the underlying geometry
  improving (unweighted control stays flat at 0.8356).
- **Span-shredding shields a grain from novelty** (run 28) — `min_span=2`
  re-cuts unfamiliar shapes into familiar fragments before rejection sees them.
- **Entropy revival ≠ coverage** (run 32) — reviving identity entropy
  (0.0014→4.0 bits) via bin placement doesn't move coverage when the revived
  identities are instance/writer-grain, not class-grain.
- **Focused evidence supplements, never replaces, integrated evidence** (run
  37A) — a small-region contrastive verdict is discriminative only conditioned
  on full-glyph agreement; alone it is actively harmful (64.0% vs. 80.5%
  control, McNemar p<0.0001, 82 broken vs. 16 fixed).
- **Count-matched nulls are mandatory for boundary-agreement claims** (run 33).
- **Check what the loader drops before declaring a featureset exhausted**
  (run 33) — 32 runs executed on a silently time-stripped trace.
- **Artifact diversity is not signal** (run 34b) — a staircase artifact
  manufactures fake angular diversity; correct denoising collapses entropy, it
  does not raise it.
- **A saved mind = graph + Γ grammar + rule store** (run 27) — `graph_to_dict`
  alone loses the vocabulary the decode side needs to mint.
- **Weak signal fails as a featureset, wins as a proposal** (run 35 → run 37B)
  — coarse program-types missed the verdict-layer bar by ~5pp (1.9× vs. 2.0×)
  but, redeployed as a proposal, delivered a paired-significant gain — same
  signal, two layers, opposite verdicts, both honestly measured.

---

## 8. The machinery inventory

Domain-general, gate-proven components, each usable outside Omniglot:

| Component | What it does | Where it lives |
|---|---|---|
| `ShapeDecode` Term + sd_* rule loop | decode/residual/mint/re-decode fixpoint | `runners/dsl/src/shape_decode.rs`, `seeds/shape_decode_loop.json` |
| `TransformDecode` / `DimInfer` | rung 2/3 of the growth ladder | `runners/dsl/src/term.rs` (Transform/DimInfer variants) |
| `StrokeQuantize` / `StrokeRender` | exact-inverse ink quantization/rendering | `runners/dsl/src/strokes.rs` |
| Committed-shape proposal | commit a program-type string pre-emission, propose by exact/1-edit match | `domains/committed_shape.py` |
| CFAR novelty calibration | adaptive rejection threshold from accepted-span distance distribution | `domains/novelty_calibration.py` |
| Homework loop (mark/assign/babble/cycle) | babble-with-periodic-grounding as the collapse loop at practice-session grain | `domains/homework_loop.py` |
| Ink dynamics / mouse observation model | timestamp-aware loader, velocity-minima segmentation, two-thirds-law fitting, count-matched null machinery, global constrained smoother | `domains/ink_dynamics.py`, `domains/mouse_model.py` |
| AbS read/render/compare | `abs_rerank_targeted`, junction-blend (retired path), the render-compare loop | `domains/abs_read.py` |
| Frame reification | quantum signature + log-odds weight edges as Frame graph data | `seeds/frame_weights.json` |
| Writer-dimension inference | pooled per-stroke Transform deltas → minted `WriterStyle` latent | `seeds/writer_dimensions.json` |
| SC+TPS continuous verdict (Family A) | ShapeContext + Thin-Plate-Spline + SmoothDeform fused comparator, raw points | `domains/recognition_graph.py` |
| Jabberwock decide/plan protocol | symmetric-evidence, two-faculty (coverage/fit + analogical) fork decisions with tie-as-verdict discipline | `scripts/jabberwock_decides_*.py`, e.g. `scripts/jabberwock_decides_five_walls.py` |
| Staged-checkpoint gate skeleton | resumable multi-phase gated runs with pre-registered STOP branches | `scripts/jabberwock_omniglot_*.py` (run-specific), `results/*_checkpoints/` |
| Arrangement/composition codebook | character-level ShapeSignature over stroke-quanta + relative-pose relations | `domains/ink_decode.py` |

---

## 9. Standing predictions and named-but-unpursued levers

**Falsifiable predictions for real pen data** (e.g. IAM-OnDB-class corpora),
not yet tested because the arc had no such corpus: stroke-grain identity
revives (a ballistic pen carries per-stroke information a dragged mouse cursor
does not); the two-thirds power law appears (median r² should rise well above
the measured 0.084, toward slope −0.333); velocity-minima segmentation beats
geometric-corner segmentation once count-matched (`81e6da1a`); coarse
program-types (run 35's near-miss, 1.9× vs. a 2.0× bar) clear the licensing bar
where stroke programs are rich rather than deliberately-traced-simple; per-
stroke identity returns as a usable verdict-layer signal, not just a
proposal-layer one.

**Named but not pursued:** `write_with_mouse` C3 exemplar-nuisance
marginalization retest (low expected value now that run 34b showed the verdict
layer absorbs effector noise upstream); commit-type families / 2-edit fallback
/ richer equivalence at 50-way (run 38 — exact-match rate falls with pool size
because cross-alphabet commit-type diversity outpaces pool size); an additive
contrastive-verdict supplement conditioned on full-evidence agreement (run
37A's law implies a correctly-scoped version might still help — not built).

---

## 10. Honest limitations

**The 20-way ceiling vs. BPL gap is not closed, and its anatomy is only
partially decomposed.** Standing 80.5% [76.3, 84.1] vs. BPL's 96.7% leaves
~16pp unaccounted. Run 36's taxonomy attributes part to single-stroke
whole-shape confusions (where BPL's sub-stroke motor discrimination has no
analogue here) and a sliver to a data-hygiene artifact, but most of the gap has
no measured mechanism — six independent verdict-layer levers all nulled, so
it is not nuisance coverage, proposal recall (coverage@10 76.5% still misses
~23.5% of episodes), or bin placement/noise (§5's 2×2 closed those). Unattacked:
token-refit AbS under a stronger coverage-constrained fit (run 20 proved the
mechanism, accuracy was a wash, a tighter constraint untried), learned spatial
priors surviving the identity-collapse wall (four attempts, runs 19–22, all hit
it), and richer primitives via the grain ladder (never licensed — every
richer-grain probe made things worse on this corpus).

**The agent's own gap-closure plan (run 37) has a thin voice/production
layer.** All three gaps grounded through the agent's own composers without any
host-authored decision logic, but the self-reported voice was "The thing
composes" repeated three times — a scene-description lexicon, not planning
prose. Reported as-is, not dressed up.

**The composer's grounded rules wire to other domains' vocabularies.** Run 37's
honest residual, three-for-three: every grounded rule's *shape* transferred but
its *wiring* bound to another domain's node types (Experiment/Run,
CommunicativeIntent/audience, Session/Affordance) absent from the ink pipeline.
None could fire against ink directly — the host translated each into an
ink-specific script (37A/37B/37C) by hand.

**Every stroke-grain conclusion here is corpus-conditional** (§5): stroke-
grain-dead, the exact 0.84 fidelity number, the identity collapse, and
"arrangement is everything" as a magnitude claim are statements about
Omniglot-as-mousewriting specifically, not handwriting or drawn-shape
recognition in general. The run-24 transfer gate (96.7%, zero adaptation) is
evidence the *architecture* generalizes; it says nothing about whether the
stroke-grain findings would survive on ballistic pen data, and §9 explicitly
predicts several would not.

---

*Written 2026-07-05 against HEAD `4d901133`. Sources: `git log`
(commits `26f74039`…`4d901133`), `results/omniglot_gate_run*.log`,
`results/transfer_gate_run24.log`, `results/jabberwock_decides_five_walls.log`,
and the running memory chronicle
`ozma_dynamic_quantization_core_loop.md`.*

---

## Addendum — the human-gap campaign (runs 39–45, 2026-07-05)

After consolidation, the creator's pen-up insight ("mousewriting only registers
the lines when the button is depressed, but the mouse movement is encoded
within") opened one more channel, and a four-phase campaign was run against the
~15pp gap to typical humans (95.5%, Lake 2015's 4.5% error on this protocol).

**The pen-up channel (runs 39/39b, `6b85f14c`/`825686d7`).** The button-up half
of the motor program is implied by the recorded data: stroke order, direction,
start position, transition vectors, transition durations. Gate 0 — the arc's
first licensing pass — found TRANSITIONS (raw 0.680 vs class-shuffled null
0.229) and START POSITION (0.583 vs 0.284; strongest in the 1-stroke bucket)
class-grain live; order/direction carry population convention, not identity
(the convention lives in the shuffled null); duration is speed. The full gate
split exactly along the arc's two-layer law: as proposal modality #4 it is the
arc's strongest proposal result — coverage@10 76.5→**81.0%** [76.9, 84.5]
(McNemar 18/0, p=7.6e-6), shortlist accuracy 66.0→**69.2%** [64.6, 73.6]
(16/3, p=0.0044), 88.9% conversion — while as a verdict supplement it washed
exactly (7/7, k=322 unchanged).

**The far-tail taxonomy (run 40, `45dc2855`)** re-aimed the campaign:
exemplar-token badness drives the mid/far error bands (~4× enrichment);
parse instability does not (prediction failed, reported); near-band errors are
genuine geometric near-duplicates. **Run 41 (`145d3349`)** exposed the composer
grounding front-end as substring-shallow (a named jabberwock-side defect;
run 37's groundings retroactively qualified — their value was always in the
gates).

**Four phases, all measured, none moved the verdict:**
P1 style normalization HARMED — and minted the writer/script confound law
(aspect is alphabet-consistent across writers; one writer × one alphabet makes
writer and script dimensions unidentifiable; `c95efc96`). P3 exemplar expansion
(background-calibrated writer dims, mouse-forward variants) landed at 81.8%
inside the guard CI with NO enrichment in its own target class — the mild
positive is not its claimed mechanism (`862c6c93`). P2 the learned deformation
metric went catastrophic by scale dominance (34.0%, 7/193; the
spread-matched-entry law), then NULL in its principled 44b form (79.5%,
6 discordant) — with the background-sanity STOP minted in between
(`4990c69e`/`465d57da`). P4 conditional foveation — 37A's three failure causes
each fixed by construction — was stopped by that same sanity gate at zero eval
cost (−6pp on background): the difference-region evidence itself is not
discriminative on this corpus (`1ea5a473`).

**Terminal position.** The verdict bound stands at **80.5% [76.3, 84.1]**
against twelve attempts spanning every class of change. The campaign's yields:
proposal layer +9.5pp coverage / +7.2pp accuracy; the failure taxonomy; four
standing rules (McNemar pairing for small paired effects, count-matched nulls,
spread-matched term entry, background-sanity stop); and the definitive form of
the claim this document's §10 hedged: the remaining ~15pp to human performance
is information — stroke-interior structure and richer exemplar evidence — that
this corpus's single mouse-drawn exemplar does not contain. The armed pen-data
predictions (§9) are the road.

*Addendum written 2026-07-05 against HEAD `1ea5a473`.*

---

## Addendum 2 — the pen-data predictions, tested (run 46, `7930cc6c`)

The §9 predictions were tested on real pen data (UCI Character Trajectories:
200Hz Wacom pen, 20 single-stroke classes, 2,858 samples) and on QuickDraw's
raw stream, device-split by our own grid diagnostics (integer-delta classifier:
17.1% touch / 82.9% mouse over 4,200 samples — the mouse subset serving as the
within-run control, which reproduced the run-33 ordering, validating the
pipeline). **Scoreboard: 3/5 pass, 2/5 fail — and the split redraws the map.**

**The information predictions pass decisively.** The stroke grain revives:
1,826 fine identities at **17.1×** the shuffled null on pen (684 at 3.76× on
touch) versus mousewriting's 1–2 identities at every 2×2 cell. Program-types
clear the 2.0× licensing bar they missed at 1.9× (pen **4.9×**, touch 3.0×).
Single-stroke identity returns (6.0× on the touch single-stroke subset; UCI's
whole corpus is single-stroke at 17×) — the desert is fertile on pen data.

**The kinematic predictions fail honestly.** The two-thirds law is nearly
absent even on true tablet pen (r²=0.092 vs mousewriting's 0.084; QuickDraw
touch's 0.310 is task-confounded — its mouse control failed the guard), and
arc-length corners beat velocity minima count-matched on both pen and touch.
Amended understanding: *deliberate drawing is visually-servoed and
non-ballistic on any effector* — the two-thirds law belongs to rapid
movements, not careful writing; momentum was never the lever. What the
mousewriting reframe got right is the information claim: the mouse killed
stroke-interior information, and real pen/touch traces carry rich class-grain
structure exactly where the BPL gap lives (§6).

**Licensed by this run:** rebuilding the stroke grain — quantization,
programs, codebook — on pen corpora. The identity information the 96.7 target
requires demonstrably exists there.

*Addendum 2 written 2026-07-05 against HEAD `7930cc6c`.*
