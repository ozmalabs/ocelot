# IS THERE A DISAGREEMENT AT ALL? — PRE-REGISTRATION

*Written and committed BEFORE any Phase-1 number. Protocol §3.*

**Branch:** `worktree-agent-a939a9119c0d95fe7` (the intended name
`gamma-substrate/k-scope` was NOT provisioned; reporting what I actually see,
as instructed).
**Base commit:** `609930c52e8fa4efd81ebc42bcf4fc602cf71a3b`.
**Seed block claimed:** 76000–76999.
**Seeds consumed by Phase 1: ZERO** — Phase 1 is a re-analysis of raw
per-frame data already committed by the two rungs. It draws no random number,
runs no substrate, and evaluates no codebook. If Phase 2 is reached it will
consume the block and say so.

**Engine (§10).** This tree's engine is **`d6097900e8b5`** @
`runners/dsl/python/substrate_rs/_native.abi3.so`, built with
`scripts/engine_build.sh` (never a bare `cargo build`). This tree's Rust source
is byte-identical to the canonical tree's (`diff -rq runners/dsl/src` reports
only an untracked `py.rs.selfmod.bak`, which is not compiled).
**The engine that produced the data being re-analysed is `25fa11652e83`**,
recorded in the `provenance` field of both `results/video_accum.json` and
`results/cut_mint.json`. **Phase 1 does not execute the engine at all**, so
`25fa11652e83` is the provenance that bears on every Phase-1 number;
`d6097900e8b5` is recorded because the gates and the oracle ran against it.

**Gates run as their own step, BEFORE any number:**
`tests/test_engine_provenance_migrated.py` +
`tests/test_provenance_endpoint_guard_migrated.py` — **632 passed, exit 0**.
`bash scripts/rung7_vision_bench.sh` with `data/` symlinked — **222 passed,
exit 0** (148.8 s).

---

## 0. DISCLOSURE — I AM NOT BLIND, AND THIS SAYS EXACTLY HOW MUCH

Before writing this file I did an arithmetic check on the two rungs' **already
published and committed** CIs, which are on the public record and which any
reader can do:

- C1: `+0.0360 [+0.0086, +0.0635]` vs `−0.0235 [−0.0498, +0.0028]` — the
  intervals do **not** overlap.
- C2: `+0.0054 [−0.0062, +0.0171]` vs `−0.0235 [−0.0606, +0.0135]` — the
  intervals overlap substantially.

Treating the two estimates as independent and reconstructing SEs from the
published half-widths gives roughly **3.1 SE (C1)** and **1.5 SE (C2)**.

**That back-of-envelope is not the test and I am not reporting it as one.** It
throws away the frame-level pairing, it assumes independence between two
contrasts measured on the *same* 50 frames, and it uses a normal approximation
on 5 autocorrelated blocks. The test fixed below uses the per-frame rows, which
the envelope did not touch, and **I do not know its answer.** Disclosing the
envelope is the honest alternative to pretending to a blindness I do not have.

## 1. WHAT IS ACTUALLY BEING COMPARED

Both rungs stored, for every arm, the **per-held-out-frame mean best-NCC**
(`max_rows`, n = 50) — the primary, floor-independent read-out. **Verified: the
held-out frame lists are identical between the two rungs**
(`video_accum.json["held"] == cut_mint.json["held"]`, both `True`, likewise
`train`), namely 5 contiguous blocks of 10 frames:
`[10–19, 40–49, 70–79, 100–109, 130–139]`.

| | accumulation rung (cp = 90) | cut-mint rung (C-C) |
|---|---|---|
| grown arm | `GROWN`, K = **32 / 31** | `NOABSTAIN_SUB`, K = **23 / 25** |
| control | `RAND_UNIFORM`, same K | `UNIFORM`, same K |
| calibration seed | **74000** | **75000 / 75001** |
| published mean | **+0.0360 / +0.0054** | **−0.0235 / −0.0235** |

**These are the same contrast under the same generating process.** The cut-mint
rung gated (its §2.1) that the disarmed `CutMintWorld` and the incumbent
`AccumWorld`, at the same seed on the same frames, grow **identical codebooks
mint-for-mint (24 = 24, 27 = 27)**. So `NOABSTAIN` is the incumbent's own
growth process; what moved between the rungs is **the calibration seed, and
therefore K**.

## 2. GATE THE MEASURE FIRST (§1) — TWO PRE-REGISTERED INSTRUMENT CHECKS

**These run BEFORE the contrast, and either one failing STOPS the rung.**

**G1 — REPRODUCTION.** Recompute both published contrasts from `max_rows`
alone. `mean(GROWN − RAND_UNIFORM)` must reproduce the accumulation rung's
published `+0.0360 / +0.0054`, and `mean(NOABSTAIN_SUB − UNIFORM)` must
reproduce the cut-mint rung's published `−0.0235 / −0.0235`, **each to ≥ 6
decimal places, together with their published CI endpoints.** If my re-analysis
path cannot reproduce the numbers it is re-analysing, it is measuring something
else and **I stop and report that instead.**

**G2 — THE FLOOR-INDEPENDENCE CLAIM IS VERIFIED, NOT ASSUMED.** Both rungs
assert the primary read-out is floor-independent and both document that a grown
codebook **raises its own measured floor** (0.4973 vs 0.3872 on C2) — the
confound the brief requires me to handle rather than assume away. The floor
gates `is_held` / `is_novel`, i.e. the **accept-rate** co-primary. Whether it
also enters `is_max` is a fact about the measurement code, so **I will audit
`eval_pass` in `scripts/video_accum_measure.py` and establish by reading the
code path whether the floor value participates in producing `max_rows`.**
- If the floor does **not** enter `max_rows`: the Phase-1 contrast is
  floor-independent, as both rungs claimed, and I record that the claim was
  checked rather than inherited.
- If the floor **does** enter `max_rows`: the entire Phase-1 comparison is
  confounded by a quantity that moves with K, **I say so, and no verdict of
  "distinguishable" may be issued** — the correct report becomes "these two
  numbers are not comparable at all", which is a different and equally
  publishable result.

## 3. THE STATISTIC, EXACTLY

Per corpus, for each held-out frame *i* = 1…50:

```
D_i  =  [ GROWN_i − RAND_UNIFORM_i ]  −  [ NOABSTAIN_SUB_i − UNIFORM_i ]
```

a **paired difference-of-differences on the same frame**. The estimand is
`mean(D)`; under "the two rungs measured the same thing" its expectation is 0.

- **Primary interval:** 95% paired t-CI on `mean(D)`, df = 49.
- **Robustness interval:** **moving-block bootstrap over the 5 contiguous
  blocks of 10 held-out frames** — resample the 5 blocks with replacement,
  10 000 replicates, fixed RNG seed **`20260720`** (a bootstrap seed, not a
  substrate calibration seed; it draws from no seed block), percentile CI.
  This exists because **both rungs state in their own bounds that n = 50
  overstates the effective n** (blocks of 10 consecutive frames are heavily
  autocorrelated). The effective n is nearer **5** than 50, and the block
  bootstrap is the instrument that respects that.

**Reported per corpus. NEVER pooled.** (Five corpus disagreements and counting
in this arc; pooling would manufacture a sixth.)

## 4. DECISION RULE, FIXED IN ADVANCE

**A corpus is DISTINGUISHABLE iff BOTH the paired t-CI AND the block-bootstrap
CI on `mean(D)` exclude zero.**

Requiring **both** is deliberately conservative and is the whole point: the
t-CI at n = 50 is known to be anti-conservative here by the rungs' own
admission, and a result that survives only the interval its authors already
disclaimed is not a result. **If the two intervals disagree, the verdict is NOT
DISTINGUISHABLE** for that corpus.

| outcome | verdict | action |
|---|---|---|
| NOT distinguishable on **both** corpora | **the two rungs were never in conflict** | **STOP. Phase 1 is the result.** No Phase 2. Report as loudly as a positive. |
| distinguishable on **exactly one** corpus | **corpus-specific inconsistency** | **GO**, but Phase 2 is scoped to the corpus that separated, and the report must state that the other corpus shows no inconsistency to explain. |
| distinguishable on **both** | **genuine inconsistency** | **GO** to Phase 2 in full. |

**What a null means, stated in advance:** a null does **not** mean the two
rungs measured the same number. It means **the data cannot tell them apart**,
and therefore that *both headlines over-read a single draw* — the accumulation
rung's `+0.0360` and the cut-mint rung's `−0.0235` would both be quotable only
with their uncertainty, and the K-sweep would be unmotivated. That is a
correction to the record, not an absence of a finding.

**No sweeps, no re-runs (§3.6).** Exactly the intervals listed above. If
Phase 1 nulls, I do not go looking for a contrast that separates.

## 5. SECONDARY CONTRAST — DECLARED NOW, NOT AFTERWARDS

The cut-mint rung documented (its §3.3, post-hoc but committed) that its
**primary size-match was crippled by its own one-entry draw**: on C1
`NOABSTAIN_SUB` discarded an entry improving **112 / 800** held-out
observations, while the secondary `NOABSTAIN_PRE` discarded one improving
**0 / 800**. `NOABSTAIN_SUB` is therefore **biased downward on C1 by a known,
measured amount**, which would inflate `mean(D)` and bias Phase 1 *toward*
declaring a disagreement.

So I pre-register the same statistic with the other pre-registered size-match:

```
D'_i  =  [ GROWN_i − RAND_UNIFORM_i ]  −  [ NOABSTAIN_PRE_i − UNIFORM_i ]
```

**If D and D' give the same verdict, the verdict stands. If they disagree, the
conservative reading (NOT DISTINGUISHABLE) is taken** and both are reported.
Neither is promoted to primary after the fact (§5).

## 6. WHAT PHASE 1 CANNOT SEPARATE — STATED BEFORE, NOT AFTER

`mean(D)` bundles **three** things that moved together between the two rungs:

1. **K** (32/31 → 23/25);
2. the **calibration seed** (74000 → 75000/75001), which sets the measured
   noise floor, which sets what counts as novel, which sets K;
3. the **particular uniform draw** in each control arm (74100+ vs 75100+).

**Phase 1 asks only whether the two published numbers are mutually
inconsistent. It does not and cannot attribute the difference to K.** Any
attribution is Phase 2's job, and if Phase 1 stops, no attribution is licensed
at all — including the cut-mint rung's own "the error is K-scope", which would
then stand as an unproven hypothesis rather than a finding.

## 7. MY PREDICTIONS, IN ADVANCE, WITH PROVISOS (§3.7)

| # | prediction | confidence | the proviso that would break it |
|---|---|---|---|
| **P1** | **C1 is DISTINGUISHABLE** — both intervals exclude 0 | moderate | The block bootstrap resamples **5 units**. Its percentile CI is very wide by construction, and it may fail to separate even a large mean. If it does, my own conservative rule sends C1 to NOT DISTINGUISHABLE — and I will report that the rule bit me. |
| **P2** | **C2 is NOT DISTINGUISHABLE** | high | Pairing could shrink the SE far more than I expect; if frame difficulty dominates variance, C2's `+0.0054` vs `−0.0235` could separate on the t-CI. |
| **P3** | Pairing **reduces** the SE of `D` relative to the independent-SE envelope, so \|t\| exceeds 3.1 (C1) and 1.5 (C2) | moderate | The two UNIFORM arms are **different draws at different K**. If draw identity, not frame difficulty, dominates per-frame variance, pairing buys nothing and P3 fails. |
| **P4** | The verdict is **SPLIT** → GO, scoped to C1 | moderate | Either corpus moving flips this. |
| **P5** | G2 finds the floor does **not** enter `max_rows`, i.e. both rungs' floor-independence claim is correct | high | If wrong, §2 says no "distinguishable" verdict may be issued and the rung reports non-comparability instead. |

**P1 and P2 together say the disagreement is real on C1 and imaginary on C2** —
i.e. that the arc's sixth corpus disagreement is hiding inside what was
presented as a single cross-rung contradiction. I hold P4 most weakly and its
refutation would be the most informative outcome, since a both-null result
would retire the K-sweep entirely.

## 8. PHASE 2 — PRE-REGISTERED ONLY CONDITIONALLY

**Phase 2 is not authorised unless Phase 1 issues GO.** If it does, it consumes
seed block 76000–76999 and gets its **own** pre-registration section committed
before any Phase-2 number, covering:

1. **NATURAL K** — many calibration seeds, recording the induced K
   distribution and GROWN − UNIFORM at each. This samples the actual generating
   process.
2. **SIZE-MATCHED** — matched K by truncation/extension, with the confound
   stated: **truncation changes WHICH entries are present, not only how many**,
   so this isolates size only under an assumption that must be written down.
3. **The floor confound**, which by both rungs' own measurement **moves with
   codebook diversity** — so the recognition criterion itself moves with K and
   the across-K comparison is not clean. This must be measured, not assumed
   away.
4. Any threshold must **FALL OUT** (§13), never be eyeballed off a curve.

## 9. BOUNDS THAT APPLY TO PHASE 1 REGARDLESS OF OUTCOME (§8)

- **Two corpora, 150 frames each, 24×24 grey, 6×6 regions, k = 4.** Every
  claim is bounded to this corpus and this resolution.
- **Regions are an adapter-chosen grid.** No object label exists anywhere in
  the measurement; "recognition" means region identity against a held codebook.
- **The effect under dispute rested, in the cut-mint rung, on ONE burst at ONE
  frame per corpus** (C1 frame 35, C2 frame 24). The CIs — theirs and mine —
  are over **held-out frames, not over cut events.** No interval in this rung
  licenses a claim about cut events in general.
- **Frames are not independent.** No p-value is quoted anywhere; CIs only.
- **Phase 1 re-analyses committed data and adds no measurement.** It cannot
  discover anything the two rungs did not already record; it can only test
  whether what they recorded is mutually consistent.
- **§9:** no default moves, no committed seed is edited, no Rust is touched.
