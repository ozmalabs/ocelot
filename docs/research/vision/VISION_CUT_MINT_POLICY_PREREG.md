# DOES ABSTAINING FROM MINTING AT A MARKED CUT BUY BACK THE POLICY DEFICIT? — PRE-REGISTRATION

*Written and COMMITTED before any confirmatory number (§3). Branch
`worktree-agent-abd38ed1c826d103f`, base `17cb3f3d`.*

**Seed block: 75000–75999.** 75900–75999 are **DECLARED BURNED PILOT** seeds.

**Engine (§10):** `25fa11652e83` @
`runners/dsl/python/substrate_rs/_native.abi3.so` — a **shared build from the
canonical tree, Rust source verified byte-identical** (`shared` verdict). **This
rung adds NO Rust, NO Term and NO constant to the engine**; `scripts/engine_build.sh`
is therefore not the operative step. `tests/test_engine_provenance_migrated.py`
+ `tests/test_provenance_endpoint_guard_migrated.py` were run **as their own
step, before any number: 631 passed, exit 0.** `data/` symlinked; baseline
oracle `bash scripts/rung7_vision_bench.sh` → **222 passed, exit 0** (148.5 s),
captured before any measurement.

---

## 0. THE QUESTION, AND WHY IT IS NOT "IMPROVE SELECTION"

`VISION_VIDEO_ACCUMULATION_RESULTS.md` decomposed its own failure into a budget,
CI-separated on **both** corpora at the final checkpoint (K = 32 / 31):

| contrast | C1 | C2 |
|---|---|---|
| **GROWN − CUTMATCHED** (MDL selection, frame distribution held fixed) | **+0.0625** ✅ | **+0.0475** ✅ |
| **CUTMATCHED − UNIFORM** (the cost of WHERE it minted) | **−0.0265** ✅ negative | **−0.0420** ✅ negative |
| GROWN − UNIFORM (the net) | +0.0360 ✅ | +0.0054 ❌ NULL |

*"When it mints is a liability; which tile it picks is the asset."* So the
follow-up is not a better selector — it is **to stop minting at cuts**.

---

## 1. THE INHERITED PREDICTION, WITH ITS NUMBER, FIXED BEFORE THIS RUNG EXISTED

`VISION_VIDEO_ACCUMULATION_RESULTS.md` §12.1, written before this rung was
provisioned:

> *"a minting policy that **abstains at a marked cut** … the prediction is that
> GROWN − UNIFORM rises by roughly the cut-matched deficit, taking C2 off its
> null."*

**Stated numerically, and this value is fixed here and will NOT be adjusted
after looking (§5):**

| corpus | incumbent GROWN − UNIFORM | + cut-matched deficit | **PREDICTED ABSTAIN − UNIFORM** |
|---|---|---|---|
| **C1** | +0.0360 | +0.0265 | **+0.0625** |
| **C2** | +0.0054 | +0.0420 | **+0.0474** |

and, on C2, **the CI must exclude 0** (that is what "off its null" means).

Note the arithmetic identity this makes explicit: (G−U) + (U−CM) = G−CM, so the
inherited prediction is exactly *"removing the policy handicap leaves the pure
selection value"* — **+0.0625 / +0.0475**, the top row of §0. The prediction is
internally coherent, which is why it is worth risking.

## 1.1 MY OWN PREDICTION DISAGREES WITH IT, IN ADVANCE, BY A FACTOR I CAN COMPUTE NOW

**The inherited prediction assumes the WHOLE cut handicap is removed.** It is
not, and the fraction is computable **before running** from the incumbent's
committed mint list (`results/video_accum.json`) — no new measurement:

| corpus | K (incumbent) | mints at frames INCIDENT on a marked step | **f** | which frames |
|---|---|---|---|---|
| C1 | 32 | **6** | **0.188** | all 6 at frame **35** (cut step 34: 34→35) |
| C2 | 31 | **6** | **0.194** | all 6 at frame **24** (cut step 23: 23→24) |

RAND-CUTMATCHED drew **100%** of its entries from the cut-concentrated frame
distribution. The abstaining codebook removes only the fraction **f ≈ 0.19** of
entries that sit on a cut. **If the handicap is proportional to that fraction,
the realised rise is f × deficit:**

| corpus | deficit | **f × deficit = MY PREDICTED RISE** | **MY PREDICTED ABSTAIN − UNIFORM** |
|---|---|---|---|
| **C1** | 0.0265 | **+0.0050** | **+0.0410** |
| **C2** | 0.0420 | **+0.0081** | **+0.0135** |

**So I predict, in advance, that the inherited prediction OVER-PREDICTS BY
ROUGHLY 5× (1/f), and that C2 does NOT come off its null.** Both numbers are
recorded here; both will be reported beside the measured value whichever wins.

**The mechanism this scoping exposes, and it is the finding if it holds:** all
six prevented mints, on **both** corpora, are at a **single frame** — the frame
immediately after the cut. That is a **burst**: at a cut the held codebook
mismatches everything at once and the seam mints a cluster from one moment, so
the "cut-aligned minting policy" is, concretely, *over-representing one frame*.

## 1.2 WHY I AM NOT WIDENING THE WINDOW TO MAKE THE EFFECT BIGGER (§13)

At W = 3 frames (the seam rung's inherited window) the incumbent has **16 (C1)
and 10 (C2)** near-cut entries — f = 0.50 / 0.32, and the predicted effect would
be **2.7× / 1.7× larger**. **W is a magic number.** A window chosen because it
makes the output look right is exactly what §13 forbids, and choosing it after
seeing that f = 0.19 is too small would be §5's metric surgery. The policy
therefore uses the **parameter-free** definition — a frame abstains iff a step
**incident on it** is marked — and the small f is reported as a cost of that
discipline, not designed around.

## 2. THE POLICY — A RULE, NOT A PYTHON CONDITIONAL

New seed `seeds/vision_cut_mint_policy.json`, **one rule**:

| rule | what it decides |
|---|---|
| `cm_abstain_mint` | an Observation the seam has declared `is_novel`, whose frame is incident on a step another rule marked `is_cut`, **does not mint** — status becomes `cm_abstained`, `mint_abstained = 1`, and a `MintAbstention` node records why |

The cut marker is **`seeds/vision_cut_abstention.json`, LOADED UNEDITED** —
`ca_step_mag` / `ca_otsu` / `ca_mark_cut` supply a threshold that falls out of
the sequence's own distribution (§13; gated in that rung by
`test_no_numeric_threshold_is_written_anywhere_in_the_seed`). `ca_abstain`
matches `ObsGroup`, of which this world has none, so it is inert here.

**The adapter (`domains/cut_mint_world.py`) writes and stops:** one `VidFrame`
per decoded frame (`vals` / `rows` / `cols`, verbatim from
`cut_abstention_world`), one `FrameStep` per consecutive pair, and one `at_step`
edge from each Observation to the (≤ 2) steps incident on the frame the runner
just presented. **That interval is one the runner already constructed** — it
knows which frame it handed over — exactly the `spans` precedent. No conditional
over graph state; gated by an **AST walk over `Compare` nodes**
(`test_the_adapter_takes_no_decision_over_graph_state`), reusing the incumbent's
rewritten audit **because its substring predecessor passed a planted decision**,
and positive-controlled with that same mutation.

**RULE ORDER IS LOAD ORDER, and it is load-bearing.** `run_rules` iterates the
rule vector in install order and restarts from index 0 on progress, so a rule
that must pre-empt `is_mint` has to be installed **before** it. `CutMintWorld`
therefore loads `vision_cut_abstention` + `vision_cut_mint_policy` **before**
`vision_identity_seam`. **Gated two ways:** the installed order is asserted
(`test_the_policy_rule_precedes_is_mint`), and **with the policy DISARMED the
grown codebook is byte-identical to the incumbent `AccumWorld`'s** — same K,
same mint list, same frames and regions (`test_disarmed_growth_is_identical_to_the_incumbent`).
That second gate is what makes the duplicated boot sequence trustworthy and is
the §9 defaults check.

## 3. SIZE MATCHING — OR THE MEASUREMENT IS OF SIZE, NOT POLICY

Abstaining mints **fewer** entries, and recognition rises with K in every arm of
the incumbent (its P1, right on both corpora). **Every contrast below is at one
common K = K_a**, the abstaining arm's own final codebook size. Four arms, all
evaluated in **freshly built, identically constructed, frozen** substrates by
the incumbent's unmodified evaluation path:

| arm | K_a entries are… |
|---|---|
| **ABSTAIN** | the K_a mints the abstaining policy made |
| **NOABSTAIN_SUB** *(primary size-match)* | K_a of the K_n non-abstaining mints, drawn uniformly **without replacement** (seed 75200 + ci) |
| **NOABSTAIN_PRE** *(secondary, declared here, reported either way)* | the **first** K_a of the K_n non-abstaining mints in training order |
| **UNIFORM** | K_a training observations drawn uniformly from every (frame, region) seen (seed 75100 + ci) |

**Why two size-matches, both declared now:** subsampling preserves the training
SPAN and matches size; prefix-truncation preserves the codebook the system
actually held but conflates policy with training duration. Neither is
unambiguously right, so both are fixed in advance and both are reported. **The
primary is NOABSTAIN_SUB.** Choosing between them after looking would be §5.

**The policy is armed during GROWTH ONLY.** Evaluation substrates carry no
`FrameStep` and a disarmed `CutParams`, so the evaluation path is bit-for-bit
the incumbent's and the UNIFORM arm is directly comparable to its published one.

## 4. THE READ-OUT, INHERITED UNCHANGED

**PRIMARY: mean best-NCC (`is_max`) on held-out frames.** Graded, unsaturated at
K ≈ 30, and independent of floor movement — the incumbent's calibration
(IDEAL 0.8229 vs NULL 0.3660, delta +0.4568) is inherited, not re-derived.

**CO-PRIMARY: accept rate**, reported with its declared ceiling (0.9988 at
K = 37) and **with each arm's measured floor beside it**, because the incumbent
established that **a grown codebook raises its own noise floor** (0.4973 vs
0.3872) and is more conservative *because* better stocked. **Accept-rate
contrasts across arms of different diversity are confounded by that**, it is
declared here, and no accept-rate result will be read as a policy effect without
its floors quoted.

Unit of analysis = **held-out frame**, n = 50, paired by frame, 95% paired
t-CI. **Per corpus, never pooled** — the corpora have disagreed five times.

## 5. THE CONTRASTS, AND THE DECISION RULE

| id | contrast | inherited prediction | **my prediction (§1.1)** |
|---|---|---|---|
| **C-A** | **ABSTAIN − UNIFORM** | **+0.0625 / +0.0474**, C2's CI excludes 0 | **+0.0410 / +0.0135**, C2 stays NULL |
| **C-B** | **ABSTAIN − NOABSTAIN_SUB** *(the policy, isolated)* | +0.0265 / +0.0420 | **+0.0050 / +0.0081** |
| C-C | NOABSTAIN_SUB − UNIFORM *(gate 1 re-measured at K_a)* | — | near the incumbent's +0.0360 / +0.0054, but see the proviso |
| C-D | ABSTAIN − NOABSTAIN_PRE *(secondary size-match)* | — | same sign as C-B |

**DECISION RULE, fixed now:**

1. **The inherited prediction is CONFIRMED** iff C-A is within **±0.02** of its
   predicted value on **both** corpora **and** C2's C-A CI excludes 0. Anything
   else is reported as **measured-vs-predicted with the discrepancy stated**,
   and — per the brief — *the decomposition is then wrong somewhere*, which is
   the more informative outcome.
2. **The policy has a demonstrated isolated effect** iff **C-B's CI excludes 0**,
   per corpus.
3. **A C-B null whose CI contains both 0 and the predicted f × deficit is
   reported as UNPOWERED**, not as "no effect". Under the standing rule *(power
   the gate before the endgame — deltas within ~3× the per-episode step are not
   results)*, and with the incumbent's final-checkpoint CI half-widths of
   **±0.0275 (C1) / ±0.0117 (C2)**, **a +0.005 / +0.008 effect is at or below
   this instrument's resolution and I expect C-B to be UNPOWERED on C1.** That
   expectation is recorded before running.
4. **No arm is re-cut, no window is swept, no third size-match is added.** A
   further attempt needs a new pre-registration with a new mechanism-level
   hypothesis.

**PROVISO ON EVERY CROSS-K COMPARISON, stated in advance:** the incumbent's
GROWN − UNIFORM contrast is **not K-invariant** — across its own checkpoints it
runs +0.0742 (K=5), +0.0450 (K=14), +0.0268 (K=22), +0.0802 (K=29), +0.0360
(K=32) on C1. **So comparing this rung's C-A at K_a against the incumbent's
+0.0360 at K=32 is confounded with K**, and that is precisely why C-C
re-measures the incumbent's contrast at K_a inside this run. **C-B and C-C are
the within-run, K-matched quantities; C-A carries the inherited prediction and
its confound.**

## 6. THE FALSE-POSITIVE COST — MEASURED SEPARATELY, NEVER NETTED

The cut-abstention rung's **arm 4 FAILED**: on cut-free footage the marker marks
**5/69 (C1) and 22/61 (C2)** steps, at magnitudes an order of magnitude below a
real cut, with `marked_are_the_top_n` **True** — *Otsu has no free parameter and
also no null hypothesis.* **This rung inherits that defect and must price it.**
Three measurements, reported beside the benefit and never summed into it:

**(a) WHICH STEPS THE POLICY ACTUALLY MARKED, against the committed reference.**
The graph's marked-step set over the full 149-step sequence, compared to the
committed numpy-Otsu cut list — C1 `[34, 47, 79]`, C2 `[23, 85, 143]`. Every
marked step not in that list is a **false positive** and every mint it prevents
is charged to the marker, not to the policy.

**(b) WHAT THE PREVENTED MINTS WERE WORTH.** For each mint the policy prevented,
its value **in the incumbent's own codebook**, computed in numpy outside the
graph (the incumbent's D2 re-derivation method, which reproduced the graph's
mean to six decimals): (i) its per-entry **usage** on held-out observations;
(ii) its **leave-one-out marginal contribution** — the number of held-out
observations whose best-match NCC falls when that entry is removed, and the mean
and max of that fall. **This is the good-mints-lost cost in the read-out's own
units**, and it is reported whether or not the mark was a false positive.

**(c) THE COUNTERFACTUAL FP COST.** The same graph marker run on the **longest
contiguous cut-free run of training frames** (arm 4's population), reporting
steps marked, their magnitudes against a real cut's, and **how many incumbent
mints sit at frames those marks would have vetoed**. That is what the policy
would cost on footage with no cut in it, which is the regime arm 4 showed it
cannot recognise.

## 7. WHAT THIS RUNG DOES NOT MEASURE (§8, declared now)

- **Gate 2 (bounded growth) is NOT re-litigated.** The incumbent established it
  is **UNPOWERED on this corpus** — burstiness destroys the CI (sd 1.07 / 1.58
  against means 0.23 / 0.86). Any mint-rate number here is descriptive only and
  will be labelled unpowered in both directions.
- **Gate 3 (refusal) is not re-run.** It passed on both corpora and nothing here
  changes the refusal path.
- **n = 1 EVENT PER CORPUS.** The entire policy effect on these corpora is the
  removal of **one burst at one frame** (C1 frame 35, C2 frame 24). Two corpora
  × one event is not a sample, and no claim here generalises past it.
- **Toy resolution**: 24×24 grey, 6×6 regions, k = 4, 150 frames, 90 train / 50
  held-out with a 1-frame guard band. No object label enters the measurement;
  "recognition" means region identity against a held codebook and nothing more.
- **Frames are not independent** (blocks of 10 consecutive). No p-value is
  quoted anywhere; CIs only, unit at the frame.
- **The floor confound** (§4) is declared, not solved.
- **§9:** no default moves, no committed seed is edited (byte-hash gated against
  `17cb3f3d`), no Rust is touched (empty-diff gated). The new seed ships
  **disarmed** and is not in the default boot set.

## 8. PREDICTIONS, SCORED AFTERWARDS (§3.7)

| # | prediction |
|---|---|
| **P1** | **The inherited one: C-A = +0.0625 (C1) / +0.0474 (C2), C2 off its null.** I expect this to FAIL, over-predicting by ≈ 1/f ≈ 5×. |
| **P2** | **Mine: C-A = +0.0410 (C1) / +0.0135 (C2); C2 stays NULL.** |
| **P3** | **C-B = +0.0050 (C1) / +0.0081 (C2)**, and **C-B is UNPOWERED on C1** (CI contains 0 and the predicted value). |
| P4 | K_a ≥ K_n − 6 on both corpora — abstaining at frame 35 / 24 will let some later frame mint what that burst would have covered, so the codebook does **not** simply shrink by 6. |
| P5 | The graph's marked-step set equals the committed reference exactly on the full sequence, so the **corpus-level false-positive count is 0** and the lost mints are charged to TRUE cuts. The over-marking is real but lives in the **cut-free-run** regime (§6c), where I expect **≥ 5 (C1) / ≥ 20 (C2)** marks. |
| P6 | The prevented mints are **not worthless** — the incumbent measured 87–88% of all entries used and cut-minted entries **not dead** (its P6, right). I expect a non-zero leave-one-out cost, i.e. **abstention throws away something real**, and the rung's honest form is a trade, not a free win. |
| P7 | The accept-rate contrast will disagree with the primary again, and its driver will again be **floor movement**, not the ceiling. |

**The outcome I consider most likely, recorded before running:** C-A lands near
the incumbent's own +0.0360 / +0.0054 plus a few thousandths; **C2 stays null**;
C-B is a small positive point estimate inside its own CI on C1 and possibly
CI-separated on C2; and the honest headline is *"the decomposition's arithmetic
was right and its SCOPE was not — the deficit was measured at 100% cut-matching
and the policy can only remove 19% of it."* If instead C-A jumps to +0.0625, the
handicap is not proportional to the fraction of cut-minted entries and **my
proportionality assumption is what was wrong**, which is worth as much.
