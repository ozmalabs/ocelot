# WAS THERE A DISAGREEMENT AT ALL? — RESULTS

*Pre-registration: `VISION_K_SCOPE_PREREG.md`, committed BEFORE any headline
number at **`32e1d62bf1f771f1f191fa2a00e1f7ee4fba03f5`** (base
**`609930c52e8fa4efd81ebc42bcf4fc602cf71a3b`**). Both endpoints pinned; no
range ends at `HEAD`.*

**Branch:** `worktree-agent-a939a9119c0d95fe7` — **the intended
`gamma-substrate/k-scope` was NOT provisioned**, and I am reporting the branch
I actually see, as instructed. Fifth rung in a row under an auto-generated
name.

**Engine (§10):** this tree's engine is **`d6097900e8b5`**, built with
`scripts/engine_build.sh` (never a bare `cargo build`); this tree's Rust source
is byte-identical to canonical (`diff -rq runners/dsl/src` reports only an
untracked, uncompiled `py.rs.selfmod.bak`). **The engine that produced every
number re-analysed here is `25fa11652e83`**, read from the `provenance` field
of both raw files. **Phase 1 never executes the engine** — it is arithmetic on
committed rows — so `25fa11652e83` is the provenance that bears on the results
and `d6097900e8b5` is what the gates and the oracle ran against.

**This rung adds NO Rust, NO Term, NO seed rule and NO constant.**
`git diff 609930c5 -- runners/dsl/src` is **empty**; `git diff 609930c5 -- seeds`
is **empty**; `git diff 609930c5 -- results` is **empty** (no committed raw
datum was altered).
`tests/test_engine_provenance_migrated.py` + `test_provenance_endpoint_guard_migrated.py`
were run **as their own step before any number: 632 passed, exit 0.**
`data/` symlinked, so the oracle's condition is the **222/0** one.
**Machine:** AMD Ryzen 5 9600X, 12 logical cores; ran solo.
**Selectors (§12):** `scripts/k_scope_analyse.py` (the pre-registered decision
rule, applied mechanically, with every published value read from a constant
block rather than re-typed from output) · `tests/test_k_scope_migrated.py`
(11 gates, one positive-controlled).
**Raw:** `results/k_scope.json` (8 KB), committed.
**Seeds:** block **76000–76999 claimed and NOT CONSUMED — zero seeds burned.**
Phase 1 draws no calibration seed; the only RNG is the bootstrap's own
`20260720`. **The block is returned intact.**

---

## 0. THE HEADLINE, IN ONE PARAGRAPH

**There was never a disagreement to explain.** The two rungs' contested
numbers — the accumulation rung's **`GROWN − UNIFORM = +0.0360` at K = 32** and
the cut-mint rung's **`−0.0235` at K ≈ 23** — are **NOT STATISTICALLY
DISTINGUISHABLE ON EITHER CORPUS**, under both pre-registered size-matches, by
the decision rule fixed in advance. **Phase 2 is NOT AUTHORISED and was not
run.** The paired difference-of-differences on the same 50 held-out frames is
**+0.0595 on C1** and **+0.0290 on C2**; on the frame-as-unit t-CI C1 separates
(t = +5.54) and C2 does not, but on the **block-as-unit bootstrap neither
does** — and the pre-registered rule requires both. **The reason is not a close
call, and it is the finding.** Virtually all the variance in this measurement
lives **between** the five 10-frame blocks, not within them: the observed
spread of block means is **20.3× (C1) and 8.4× (C2)** what independent frames
could produce. **The effective n is nearer 5 than 50.** Both rungs quoted t-CIs
over n = 50 while stating in their own bounds sections that n = 50 overstates
the effective n — and this rung measures how much: **their intervals are
roughly 3× too narrow** (boot/t width ratio 2.95, 2.70, 1.91, 2.96). **The
sharpest single number is post-hoc and it corrects the record upward of this
rung's own remit: the accumulation rung's `+0.0360 [+0.0086, +0.0635]` C1 PASS
— the one positive clause the whole video line rests on — becomes
`[−0.0406, +0.1218]` under the block bootstrap and DOES NOT SURVIVE.** The
cut-mint rung's "the error is K-scope" is likewise unsupported: it was an
explanation for a difference that is not resolvable, and **no attribution to K
is licensed by this data at all.**

**Three things I got wrong or nearly did, all reported as findings.** (1) **My
P1/P4 predictions are REFUTED** — I predicted C1 would separate and the verdict
would be split; my own conservative rule bit me exactly as its proviso said it
might. (2) **My first effective-n diagnostic was BLIND BY CONSTRUCTION** —
within-block lag-1 ρ demeans each block and therefore cannot see the
block-level effect that dominates; it reported n_eff ≈ 46 for C1 where the
correct decomposition says the block is the unit (§4.1). (3) **My first
seed-block audit was a substring scan and it FAILED ON MY OWN PROSE** — the
docstring declaring the block matched it (§5.2).

---

## 1. WHY THIS WAS ASKED FIRST, AND WHAT IT REPLACES

The brief carried a ready explanation — *codebook size is calibration-seed
sensitive, K is a draw, so sweep K* — and a Phase 2 built on it. **That
explanation was never tested against the null that the two measurements are one
draw from one distribution.** Two point estimates with overlapping-or-adjacent
CIs are not a disagreement, and the cut-mint rung's own §1.1 (the K-sensitivity
observation) is a *mechanism* offered for a *difference* whose existence had not
been established.

The two contrasts are the same contrast under the same generating process. The
cut-mint rung gated (its §2.1) that the disarmed `CutMintWorld` and the
incumbent `AccumWorld`, at the same seed on the same frames, grow **identical
codebooks mint-for-mint (24 = 24, 27 = 27)**. What moved between the rungs is
the calibration seed, and therefore K.

Critically, **both rungs stored the per-held-out-frame primary read-out**
(`max_rows`, n = 50) for every arm, and **the held-out frame lists are
identical** (`video_accum.json["held"] == cut_mint.json["held"]`, likewise
`train`): five contiguous blocks of ten, `[10–19, 40–49, 70–79, 100–109,
130–139]`. So the two rungs can be compared **paired, frame by frame**, which is
strictly more informative than comparing their published intervals — and that
pairing is what makes a real test possible at all.

## 2. THE MEASURE WAS GATED FIRST (§1), AND BOTH GATES WERE STOPPING CONDITIONS

### 2.1 G1 — THE RE-ANALYSIS REPRODUCES WHAT IT RE-ANALYSES. **PASS.**

Recomputed from `max_rows` alone, against values read from a constant block
quoting the two committed docs:

| corpus | contrast | mine | published | |
|---|---|---|---|---|
| C1 | accum `GROWN − UNIFORM` | +0.0360 [+0.0086, +0.0635] | +0.0360 [+0.0086, +0.0635] | ✅ |
| C1 | cut-mint `C-C` | −0.0235 [−0.0498, +0.0028] | −0.0235 [−0.0498, +0.0028] | ✅ |
| C2 | accum `GROWN − UNIFORM` | +0.0054 [−0.0062, +0.0171] | +0.0054 [−0.0062, +0.0171] | ✅ |
| C2 | cut-mint `C-C` | −0.0235 [−0.0606, +0.0135] | −0.0235 [−0.0606, +0.0135] | ✅ |

**All twelve endpoints reproduce.** The re-analysis path is measuring the same
quantity the two rungs measured, so everything below is about the data and not
about my arithmetic.

### 2.2 G2 — THE FLOOR-INDEPENDENCE CLAIM IS VERIFIED, NOT INHERITED. **PASS.**

This is the confound the brief required be handled rather than assumed away:
**a grown codebook raises its own measured noise floor** (0.4973 vs 0.3872 on
C2), so it is *more conservative because it is better stocked*, and the
recognition criterion therefore moves with K. Both rungs assert the primary
read-out is floor-independent. **Assertion is not verification**, so it was
audited from source:

- **`is_max` is written by exactly one rule, `is_score`**, as a `MaxOver` of the
  NCC against codebook entries with `seam_grown == 1.0`. **Its term contains no
  floor reference.**
- **`is_decide` only READS `is_max`.** Its write set is exactly
  `[is_floor, identified_as, status]` — the floor governs *acceptance*, i.e. the
  accept-rate **co-primary**, and nothing else.
- **`eval_pass` collects `is_max` unconditionally** (line 121), *before* and
  outside the `if held_ok:` branch that gates usage.

**So the floor confound is real and it lands on the accept rate, not on the
primary.** Both rungs' claim holds. Gated three ways in
`tests/test_k_scope_migrated.py`, including a structural check that the `is_max`
collection has not moved under the `held_ok` branch. **Had this failed, the
pre-registration required reporting non-comparability instead of any verdict.**

## 3. THE PHASE-1 TEST. **NOT DISTINGUISHABLE, BOTH CORPORA, BOTH SIZE-MATCHES.**

Per held-out frame *i*:
`D_i = [GROWN_i − RAND_UNIFORM_i] − [NOABSTAIN_SUB_i − UNIFORM_i]`.
Under "the two rungs measured the same thing", `E[D] = 0`.

| corpus | size-match | mean D | paired t-CI (n=50) | t | block bootstrap (5 blocks) | **verdict** |
|---|---|---|---|---|---|---|
| **C1** | primary (SUB) | **+0.0595** | **[+0.0380, +0.0811]** ✅ | +5.54 | **[−0.0029, +0.1219]** ❌ | **NOT DISTINGUISHABLE** |
| **C1** | secondary (PRE) | **+0.0226** | **[+0.0086, +0.0367]** ✅ | +3.24 | **[−0.0135, +0.0629]** ❌ | **NOT DISTINGUISHABLE** |
| **C2** | primary (SUB) | +0.0290 | [−0.0028, +0.0608] ❌ | +1.83 | [−0.0586, +0.1166] ❌ | **NOT DISTINGUISHABLE** |
| **C2** | secondary (PRE) | +0.0181 | [−0.0063, +0.0425] ❌ | +1.49 | [−0.0435, +0.0876] ❌ | **NOT DISTINGUISHABLE** |

**The two pre-registered size-matches AGREE on the verdict on both corpora**, so
the pre-registration's disagreement clause never had to be invoked. **0 of 2
corpora distinguishable ⇒ PHASE 2 NOT AUTHORISED. The rung stops here, as the
decision rule required.**

**Reported against myself:** on C1 the frame-unit t-CI separates at t = +5.54,
and had I pre-registered only the t-CI I would now be writing a rung explaining
a K-dependence. **The verdict turns entirely on the second interval I committed
to in advance**, and §4 is why that interval is the right one.

## 4. WHY THE BLOCK IS THE UNIT — THE NUMBER THAT DECIDES THE RUNG

Both rungs state, in their own bounds sections, *"frames are not independent —
blocks of 10 consecutive frames are heavily autocorrelated, so n = 50
overstates the effective n."* **Neither quantified it. This does.**

If frames within a block were independent, the sd of a block mean would be
`sd_within / √10`. Measured:

| corpus | sd of block means, OBSERVED | predicted if frames were iid | **inflation** |
|---|---|---|---|
| **C1** | 0.0806 | 0.0040 | **× 20.3** |
| **C2** | 0.1131 | 0.0135 | **× 8.4** |

**Virtually all the variance is BETWEEN blocks.** Ten consecutive frames of
video are near-duplicates; the corpus contains **five** genuinely distinct
held-out episodes, not fifty. The per-block means of C1's `D_primary` show it
directly — **+0.1194, +0.0590, +0.1560, +0.0041, −0.0408** — three clearly
positive, one at zero, **one negative**. The "disagreement" does not hold its
sign across the corpus's own temporal blocks. C2's are worse:
**+0.0116, −0.0517, −0.1007, +0.1708, +0.1148**.

An inflation of ×20 implies the t-CI overstates precision by roughly
`√(50/5) ≈ 3.2`, which is **exactly** the boot/t width ratios measured
independently (2.95, 2.70, 1.91, 2.96). **Two routes to the same factor.**

### 4.1 MY FIRST DIAGNOSTIC OF THIS WAS BLIND BY CONSTRUCTION, AND I FOUND IT BY CHECKING IT

I first estimated effective n from **within-block lag-1 autocorrelation**,
`n_eff = n(1−ρ)/(1+ρ)`. It returned **ρ = +0.038 → n_eff ≈ 46.3 on C1** —
i.e. "the frames are nearly independent, the t-CI is fine." **That statistic
demeans each block before computing ρ, so it cannot see a block-level random
effect at all.** It is blind to precisely the dependence that dominates here,
and it would have licensed the wrong verdict. The variance decomposition above
is the diagnostic that can see it, and it disagrees by a factor of twenty.

**This is the arc's own recurring failure — an instrument that reports a clean
number about a quantity it is structurally unable to observe** (§12.2's
zero-lag-on-a-travelling-wave, the eighteenth of its kind). It is recorded here
rather than quietly replaced; the misleading number is kept in
`results/k_scope.json` beside the correct one, labelled.

## 5. THE INSTRUMENT THAT ISSUES EVERY VERDICT WAS POSITIVE-CONTROLLED

**Every verdict in §3 is a NOT-separation issued by the block bootstrap**, so
§1 clause 4 applies to it: *an instrument that has never been able to separate
is not an instrument.* C1's own `D_primary` was shifted by a constant:

| shift applied | block-bootstrap CI | separates? |
|---|---|---|
| +0.05 | [−0.0124, +0.1124] | **no** |
| **+0.10** | **[+0.0376, +0.1624]** | **YES** |
| +0.20 | [+0.1376, +0.2624] | **YES** |
| zero-mean null | [−0.0166, +0.0147] | no (correctly) |

**The bootstrap bites at ≥ 0.10 and correctly refuses a null.** It is alive.

### 5.1 AND THIS BOUNDS THE NULL HONESTLY — "BELOW RESOLUTION", NEVER "ZERO"

The control also prices the instrument: **its resolution floor sits at roughly
0.10, and every quantity in this dispute is below it** — the accumulation
rung's `+0.0360`, the cut-mint rung's `−0.0235`, and the `+0.0595` difference
between them. **So the correct statement is that this corpus cannot resolve any
of these effects at the block unit, NOT that they are zero.** That distinction
is gated
(`test_the_block_bootstrap_cannot_resolve_the_disputed_magnitudes`) so no
successor can quietly upgrade this null into a demonstration of absence.

### 5.2 MY SEED-BLOCK AUDIT WAS A SUBSTRING SCAN AND FAILED ON MY OWN PROSE

The first version of `test_this_rung_consumes_no_seed_from_its_block` scanned
the selector's source text for any integer in 76000–76999. **It went red on the
docstring that declares the block.** A substring scan cannot tell a *consumed*
seed from a *mentioned* one — §12's *"a selector that matches by substring is
not a selector"*, and the same defect the accumulation rung found in its own
adapter audit by mutating it. Rewritten as an **AST walk** over integer
constants in executable code plus an audit that every RNG construction uses one
of the two declared bootstrap streams, and **positive-controlled**
(`test_the_seed_block_audit_is_ABLE_to_fail`: a planted
`np.random.RandomState(76000)` is caught, while the same literal in a docstring
is correctly ignored).

## 6. POST-HOC — WHAT THE SAME INSTRUMENT DOES TO THE TWO INPUTS

**NOT pre-registered. Labelled post-hoc. It changes no Phase-1 verdict** — the
verdict is already NOT DISTINGUISHABLE and the rung is already stopping.

It is reported because **suppressing it would be selective**: if the block
bootstrap is the honest instrument for this data, and the pre-registered rule
says it is, then intellectual consistency demands disclosing what that same
instrument does to the two numbers under dispute.

| corpus | contrast | published t-CI (n=50) | **block bootstrap** | survives? |
|---|---|---|---|---|
| **C1** | **accum `GROWN − UNIFORM` = +0.0360** | **[+0.0086, +0.0635]** ✅ | **[−0.0406, +0.1218]** | **❌ NO** |
| C1 | cut-mint `C-C` = −0.0235 | [−0.0498, +0.0028] ❌ | [−0.0875, +0.0544] ❌ | — |
| C2 | accum `GROWN − UNIFORM` = +0.0054 | [−0.0062, +0.0171] ❌ | [−0.0167, +0.0276] ❌ | — |
| C2 | cut-mint `C-C` = −0.0235 | [−0.0606, +0.0135] ❌ | [−0.1333, +0.0863] ❌ | — |

**The accumulation rung's C1 gate-1 PASS does not survive the block unit.** That
PASS is the single positive clause in a three-clause conjunction that the rung
itself reported as FAILED on both corpora — but it is also the number the
cut-mint rung was written to explain, the number the brief's Phase 2 was
designed to characterise against K, and the load-bearing claim in *"MDL
selection beats uniform."* **At the unit both rungs' own bounds sections say is
correct, it is not separated from zero.**

**This is offered as a measurement, not as a retraction of that rung** (§7).
The rung reported its number correctly at the unit it declared, disclosed the
autocorrelation caveat itself, and quoted no p-value. What is new here is the
*size* of the caveat, which nobody had computed. **The retraction, if one is
warranted, is theirs to make with this number in hand.**

## 7. MY PREDICTIONS, SCORED (§3.7)

| # | prediction | outcome |
|---|---|---|
| **P1** | C1 is DISTINGUISHABLE (both intervals) | **REFUTED.** t-CI yes (t = +5.54), bootstrap no. **The proviso I wrote — that a 5-block bootstrap might fail to separate even a large mean, and that my own rule would then bind — is exactly what happened.** |
| **P2** | C2 is NOT DISTINGUISHABLE | **RIGHT**, on both intervals and both size-matches. |
| **P3** | pairing reduces SE vs the independent-SE envelope; \|t\| > 3.1 (C1), > 1.5 (C2) | **RIGHT**, and by more than expected: t = +5.54 (envelope 3.1) and +1.83 (envelope 1.5). Frame difficulty does dominate, so the pairing was worth doing. |
| **P4** | the verdict is SPLIT → GO, scoped to C1 | **REFUTED.** 0/2, STOP. I held this most weakly and said its refutation would be most informative; **it was, and it retired the K-sweep.** |
| **P5** | G2 finds the floor does not enter `max_rows` | **RIGHT** — verified from source three ways (§2.2). |

**2 refuted, 3 right.** **P1 and P4 are the useful misses**: both were refuted
by the interval I chose *against my own expected outcome*, which is the only
reason the rung reached the right answer. Had I pre-registered the t-CI alone —
the instrument both prior rungs used — I would have confirmed the disagreement
and run a K-sweep to explain an artifact.

## 8. WHAT THIS RUNG DOES **NOT** SHOW (§8)

- **It does not show the two rungs measured the same number.** It shows the
  data **cannot tell them apart**. §5.1 prices the instrument: nothing below
  ≈ 0.10 is resolvable at the block unit here, and all three disputed
  quantities are below that.
- **It does not show MDL selection fails to beat uniform.** It shows the
  evidence offered for *both* answers is beneath the resolution of this corpus.
  The `GROWN − CUTMATCHED` decomposition (+0.0625 / +0.0475, CI-separated on
  both corpora in the accumulation rung) was **not** re-analysed here and is
  **not** covered by this null — though it is a frame-unit t-CI too, and §4's
  factor applies to it identically. **A successor should re-run §6's check on
  it before quoting it.**
- **It licenses NO attribution to K.** The cut-mint rung's "the error is
  K-scope" was an explanation for a difference this rung cannot establish
  exists. K may well matter; **nothing here is evidence either way**, and the
  §6 confound (K, calibration seed, and the particular uniform draw all moved
  together) was declared in advance as inseparable.
- **Phase 2 was not run.** No natural-K sweep, no size-matched sweep, no
  effect-versus-K curve, no threshold. **Seed block 76000–76999 is unconsumed.**
- **Two corpora, 150 frames each, 24×24 grey, 6×6 regions, k = 4.** Regions are
  an adapter-chosen grid; **no object label exists anywhere in the
  measurement**; "recognition" means region identity against a held codebook.
- **The disputed effect rested, in the cut-mint rung, on ONE burst at ONE frame
  per corpus.** Every CI here — as there — is over **held-out frames, not cut
  events.** Nothing in this rung licenses a claim about cut events in general.
- **The block bootstrap over 5 blocks is itself crude.** Its percentile
  endpoints are estimated from five units and it is conservative by
  construction. The honest bracket is: **frame-unit t-CI (anti-conservative,
  overstates precision ≈ 3.2×) at one end, 5-block bootstrap (conservative) at
  the other** — and the dispute is unresolved across that whole bracket, which
  is why the verdict is a null and not a reversal.
- **No p-value is quoted anywhere.** CIs only.
- **§9:** no default moved, no committed seed was edited (empty diff), no Rust
  was touched (empty diff), **no committed raw datum was altered** (empty diff
  on `results/`).

## 9. VERIFICATION

| check | result | exit |
|---|---|---|
| `tests/test_engine_provenance_migrated.py` + endpoint guard, **own step, before any number** | **632 passed** | **0** |
| `bash scripts/rung7_vision_bench.sh` **before** the rung | **222 passed** (148.8 s) | **0** |
| `bash scripts/rung7_vision_bench.sh` **after** the rung | **222 passed** (147.7 s) | **0** |
| `tests/test_k_scope_migrated.py` | **11 passed** | 0 |
| G1: 12/12 published CI endpoints reproduced from raw rows | **identical** | — |
| G2: `is_max` written only by `is_score`, no floor term; `is_decide` write set unchanged | **verified from seed** | — |
| block-bootstrap positive control (+0.10 separates, null does not) | **alive** | — |
| seed-block audit positive control (planted `RandomState(76000)` caught; docstring literal ignored) | **caught** | — |
| bootstrap determinism (same seed → same endpoints) | **identical** | — |
| `git diff 609930c5 -- runners/dsl/src` / `-- seeds` / `-- results` | **all empty** | — |

## 10. WHAT THE NEXT RUNG SHOULD PRE-REGISTER AGAINST

Ranked by what this evidence supports. **The K-sweep is NOT on this list** — it
was designed to explain a difference that has not been shown to exist, and
running it now would be characterising noise.

1. **FIX THE UNIT, THEN RE-ASK EVERYTHING.** The binding constraint on this
   entire video line is **five effective units per corpus**, not codebook size.
   Every headline in it — `+0.0360`, `−0.0235`, `+0.0625`, `−0.0265` — is a
   frame-unit t-CI, and §4's ×20 inflation applies to all of them. **The cheap,
   decisive next rung is to re-analyse every published contrast in both rungs
   at the block unit and report which survive.** It burns no seeds, needs no new
   measurement, and it will tell you how much of this line is real. **This is
   the one I would run first**, and it is the one this rung deliberately
   stopped short of.
2. **MORE INDEPENDENT EPISODES, NOT MORE FRAMES.** Adding frames to these two
   episodes buys almost nothing (within-block sd is 0.0040–0.0135 against
   between-block 0.0806–0.1131). **Power comes from more distinct episodes.** A
   pre-registered power analysis should be stated in *blocks*, and §5.1's
   ≈ 0.10 resolution floor gives the number to design against.
3. **THE FLOOR TRACKS DIVERSITY, NOT SIZE** — still unmeasured, named by both
   prior rungs as the best unclaimed mechanism, and **untouched by this null**
   because it is a claim about the accept-rate co-primary, which §2.2 confirms
   is the read-out the floor actually governs.
4. **RE-RUN §6 ON `GROWN − CUTMATCHED`** (+0.0625 / +0.0475) before it is
   quoted again. It is the accumulation rung's strongest claim, CI-separated on
   both corpora — **and it is a frame-unit interval like all the others.**

**What should NOT be pre-registered:** anything that treats `+0.0360` and
`−0.0235` as two facts needing reconciliation. **They are one draw, twice, at a
resolution that cannot separate them** — and the mechanism proposed to
reconcile them (calibration-seed sensitivity of K) remains an untested
hypothesis, not a diagnosis.
