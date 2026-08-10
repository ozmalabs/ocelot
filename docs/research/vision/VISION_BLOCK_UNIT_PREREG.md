# RE-ANALYSE EVERY PUBLISHED VIDEO-LINE CONTRAST AT THE BLOCK UNIT — PRE-REGISTRATION

*Committed BEFORE any contrast number is computed. Base pinned below; no range
ends at `HEAD`.*

**Branch:** `worktree-agent-ac3007010de9e265a` — the intended
`gamma-substrate/block-unit-reanalysis` was NOT provisioned. Reporting the
branch I actually see, as instructed. **Sixth rung in a row under an
auto-generated name.**

**Base:** `6b50b97ab3ff49980de6a0704867b578aaac923d` (the K-scope merge).

**Engine (§10):** `25fa11652e83`, read from
`runners/dsl/python/substrate_rs/_native.abi3.so`. This is **the same engine
that produced the data being re-analysed** (the `provenance` field of both raw
files reads `engine 25fa11652e83`). This tree's Rust source is byte-identical
to canonical (`diff -rq runners/dsl/src` reports only an untracked,
uncompiled `py.rs.selfmod.bak`). **This rung never executes the engine** — it
is arithmetic on committed rows.

**This rung adds NO Rust, NO Term, NO seed rule and NO constant**, and alters
**no committed raw datum**. Gated by empty diffs against the base on
`runners/dsl/src`, `seeds`, and `results/` (excluding this rung's own new
output file).

**Seeds:** block **77000–77999 claimed and to be consumed ZERO.** This rung
draws no calibration seed. The only RNG is the bootstrap's own pre-registered
stream, inherited unchanged from the K-scope rung (`20260720`). The block is to
be returned intact, gated by an **AST walk** over integer constants in
executable code (never a substring scan — that has now gone wrong three times
in this arc, including once on a docstring declaring the block).

---

## 1. THE QUESTION

The K-scope rung established that in this corpus **nearly all variance lives
between the five 10-frame held-out blocks, not within them** — block-mean
spread is **20.3× (C1) / 8.4× (C2)** what independent frames could produce, so
the **effective n is nearer 5 than 50** and frame-unit t-CIs are **≈3× too
narrow**. It demonstrated this on ONE contrast, post-hoc: the accumulation
rung's `+0.0360 [+0.0086, +0.0635]` becomes `[−0.0406, +0.1218]` at the block
unit and does not survive.

**Every other published contrast in the video line is a frame-unit interval of
the same construction, and none has been checked.** This rung checks all of
them.

## 2. A STRUCTURAL FACT, STATED IN ADVANCE

The block bootstrap resamples whole blocks and therefore **only ever widens the
interval relative to the frame-unit t-CI.** Consequently:

> **The correction can turn a published PASS into a null. It can NEVER turn a
> published null into a PASS.**

So no contrast that was already null at the frame unit can be rescued here, and
**the entire re-analysis is one-directional.** This is recorded in advance so
that the (many) unchanged nulls are not read as a finding of this rung. Gated
as **G3** below: if any vector's bootstrap interval is *narrower* than its
t-CI, that is an instrument fault and will be reported as one.

## 3. THE STATISTIC, EXACTLY

For each contrast, the unit is the **held-out frame**, n = 50, paired by frame,
in **five contiguous blocks of ten** — `[10–19, 40–49, 70–79, 100–109,
130–139]`, verified identical across both raw files (`held` and `train` lists
compared element-wise).

Let `d` be the length-50 vector of paired per-frame differences.

1. **Frame-unit t-CI** — the published construction: 95% paired t-CI,
   `mean ± t(0.975, 49) · sd/√50`. Used ONLY to reproduce the published
   endpoints (G1). Not a verdict instrument here.
2. **Block bootstrap** — `scripts/k_scope_analyse.py::block_bootstrap_ci`,
   **inherited verbatim**: moving-block bootstrap over the 5 contiguous blocks,
   10,000 reps, `np.random.RandomState(20260720)`, 2.5/97.5 percentiles of the
   resampled mean. **This is the verdict instrument**, unchanged from the rung
   that pre-registered it. Re-deriving or re-tuning it would be §5.
3. **Per-vector resolution floor `δ*(d)`** — the smallest `δ` on the fixed grid
   `{0.005, 0.010, 0.015, …, 0.300}` such that
   `block_bootstrap_ci(d − mean(d) + δ)` excludes zero. This is the K-scope
   positive control (§5 of that rung), **applied per contrast rather than
   once globally.**

### 3.1 WHY THE FLOOR IS PER-VECTOR AND NOT THE INHERITED ≈0.10

The K-scope rung measured a resolution floor of **≈0.10** and correctly
observed that every quantity in *its* dispute sat below it. **That floor is a
property of the vector it was measured on** (`D_primary`, whose block-mean sd
is 0.081), **not a constant of the corpus.** Contrasts differ enormously in
between-block variance: the published half-widths in these two rungs span
±0.005 (`GROWN − CUTMATCHED`, ±0.005) to ±0.035 (`C-A` on C2), a factor of
seven, and a tightly paired contrast between two nearly identical codebooks can
have far less block-level variance than a contrast against an independently
drawn control.

**Inheriting 0.10 globally would therefore be an error in the conservative
direction** — it would declare "below resolution" things this instrument can
in fact resolve. The floor is measured per contrast. **This is pre-registered
as a correction to how the inherited number should be used, not as a change to
the instrument**, which is verbatim.

## 4. THE CLASSIFICATION RULE — FIXED HERE, IN ADVANCE

Each contrast is placed in **exactly one** of three classes:

| class | condition |
|---|---|
| **SURVIVES** | the block-bootstrap 95% CI **excludes zero** |
| **AMBIGUOUS** | CI includes zero **AND** `abs(mean) ≥ 0.5 · δ*` |
| **BELOW RESOLUTION** | CI includes zero **AND** `abs(mean) < 0.5 · δ*` |

The `0.5 · δ*` boundary is fixed now and will not be moved. Its rationale: at
`abs(mean) ≥ δ*` a vector separates by construction, so the interesting band is
the one just beneath the floor, where the effect is within a factor of two of
detectable and a modest increase in episodes would plausibly resolve it.

### 4.1 THE DISTINCTION THAT IS GATED, NOT MERELY STATED

**"Below resolution" is NOT "zero", and NOT "absent".** It means *this corpus,
at five effective units, cannot resolve an effect of this size in either
direction.* That is a fact about the **measurement design**, not about the
mechanism. Every below-resolution row must carry that reading.

This is enforced by a gate
(`test_below_resolution_is_never_reported_as_absence`) asserting that no
below-resolution contrast is recorded with a verdict field claiming absence,
zero, refutation or a null effect — the same discipline the K-scope rung gated,
carried forward so no successor can quietly upgrade this null into a
demonstration of absence.

## 5. SCOPE — WHAT IS IN, AND WHAT IS OUT BECAUSE ITS UNIT IS DIFFERENT

**IN (unit = the 50 held-out frames; block structure applies):**

- Accumulation §3.1 `GROWN − UNIFORM`, **all five checkpoints × 2 corpora** (10)
- Accumulation §3.2 `GROWN − CUTMATCHED` and `CUTMATCHED − UNIFORM`, cp = 90 (4)
  — **`GROWN − CUTMATCHED` is the priority contrast (§6)**
- Accumulation §3.3 accept-rate `GROWN − UNIFORM` (2)
- Accumulation §8 `shuffled − in-order` (2)
- Cut-mint §3 `C-A`, `C-B`, `C-C`, `C-D` × 2 corpora (8)
- Cut-mint §3.4 accept-rate `ABSTAIN − UNIFORM`, and `ABSTAIN − NOABSTAIN_SUB` (4)

**OUT — and the reason is that the block correction does not apply, NOT that
the numbers are safe:**

- **Gate 2, mint rate by training quartile.** Unit = *training* frame, 22 per
  quartile; not the held-out 5-block design. Already null at its own unit.
- **Gate 3, refusal (BSDS / NOISE / SHUFFLE / CONTROL).** Unit = probe, n = 64
  per class, **unpaired**, and probes carry no temporal block structure.
- **§7a/§7b, dead entries and near/far usage.** Unit = codebook entry.
- **Cut-mint §5, false-positive marks and prevented mints.** Unit = step /
  codebook entry.

For each of these I will state explicitly that the unit differs and that **this
rung therefore issues no block-unit verdict on it** — rather than forcing an
inapplicable instrument onto it. Where such a contrast was *already null* at
its own unit, §2 applies and it stays null.

## 6. PRIORITY

1. **`GROWN − CUTMATCHED` (+0.0625 C1 / +0.0475 C2)** — the video line's
   strongest claim, CI-separated on **both** corpora, and the entire basis for
   *"MDL tile-selection is real and works everywhere."* The K-scope rung
   explicitly flagged it as un-re-analysed and told a successor to check it
   before quoting it again. **Reported first and prominently.**
2. The cut-mint policy isolated: `C-B` (+0.0507 / +0.0236) and `C-D`
   (+0.0138 / +0.0127).
3. Everything else in scope.

## 7. GATES (STOPPING CONDITIONS)

| id | gate | if it fails |
|---|---|---|
| **G1** | every published t-CI endpoint in scope reproduces from raw rows to the published precision | that contrast is reported **NOT RECOMPUTABLE**, with no verdict issued |
| **G2** | the block bootstrap is positive-controlled **per vector**: `δ*` exists on the grid, and a zero-mean null of matched sd does not separate | no verdict from that vector |
| **G3** | for every vector, bootstrap CI width ≥ t-CI width (§2, one-directional) | reported as an instrument fault |
| **G4** | this rung consumes no seed from 77000–77999 (**AST walk** over integer constants in executable code, positive-controlled) | halt |

**G1 is a stopping condition per contrast, not for the rung**: a published
number that cannot be recomputed from committed data is **itself a finding**
about what was preserved, and will be reported as such rather than silently
dropped.

## 8. THE FORWARD-LOOKING HALF — THE EPISODE-COUNT DESIGN SPEC

Within-block sd is 0.004–0.014; between-block sd is 0.081–0.113. The binding
constraint on this whole line is **five effective units per corpus.**

I will compute, and report as a table, **how many independent episodes `B` are
required to resolve an effect of size `δ`** at the block unit, under the
standard two-sided normal/t design at 80% power:

```
B such that  δ  ≥  (t(0.975, B−1) + t(0.80, B−1)) · σ_b / √B
```

solved for `B` at `δ ∈ {0.01, 0.02, 0.03, 0.05, 0.10, 0.15, 0.20}` and at
`σ_b` spanning the observed between-block range, **plus the σ_b measured on
this rung's own priority contrasts**, so the spec is anchored to real numbers
rather than to a round guess.

**The headline this is designed to support, stated in advance: POWER COMES FROM
MORE EPISODES, NOT MORE FRAMES.** Adding frames inside an episode buys almost
nothing — within-block sd is an order of magnitude below between-block sd — so
**any future video rung must sample episodes, not frames**, and must state its
n in blocks.

This table is **labelled as a design projection, not a measurement**, and its
assumption (that new episodes are exchangeable with these five, with the same
σ_b) is stated as the assumption it is. Five blocks is a very thin base from
which to estimate σ_b, and the resulting `B` is correspondingly uncertain.

## 9. MY PREDICTIONS, IN ADVANCE (§3.7)

| # | prediction | held how strongly |
|---|---|---|
| **P1** | **`GROWN − CUTMATCHED` SURVIVES on both corpora.** Its published half-width (±0.005) is 5–7× tighter than gate 1's, which implies genuinely small block-level variance in a contrast holding the frame distribution fixed — the block correction should hurt it far less than it hurt `GROWN − UNIFORM` | moderately |
| **P2** | `C-B` survives on both corpora; `C-D` survives on at least C1 | moderately |
| **P3** | **every `GROWN − UNIFORM` gate-1 contrast fails**, at every checkpoint, on both corpora | strongly |
| **P4** | **the per-vector floor `δ*` spans more than an order of magnitude** across the table — the inherited "≈0.10" is not a corpus constant, and treating it as one would mis-classify the tightly paired contrasts | strongly; this is the methodological point of §3.1 |
| **P5** | both accept-rate contrasts fail | moderately |
| **P6** | resolving δ = 0.03 at the gate-1 between-block sd requires **B in the high tens to low hundreds** of episodes | weakly — the arithmetic is certain, my sense of the magnitude is not |

**P1 is the one I hold most weakly relative to its importance, and its
refutation would be the most informative outcome in this rung** — if the line's
strongest claim also dissolves, the honest summary is that *"MDL selection
works everywhere"* was never resolvable on this corpus.

## 10. WHAT A NULL MEANS HERE (§3.5)

If most of the table lands **below resolution**, this rung has shown that **this
corpus cannot resolve effects of this size** — it has **NOT** shown the
mechanisms are absent. The correct successor action is a corpus with more
episodes (§8), not a retraction of the mechanisms.

If something **survives**, that is genuinely informative: it identifies which
effects in this line are large enough relative to episode-level variance to be
real *here*, and those are the ones worth carrying forward.

**Neither outcome will be softened, and no p-value will be quoted anywhere.**

## 11. VERIFICATION PLANNED

- `tests/test_engine_provenance_migrated.py` + endpoint guard, **own step,
  before any number** (both endpoints pinned; the guard fails any range ending
  at `HEAD`).
- `bash scripts/rung7_vision_bench.sh` before and after → **222 passed, exit 0**
  (`data/` symlinked).
- `tests/test_block_unit_migrated.py` — the gates of §7 plus the §4.1
  below-resolution discipline gate.
- Empty diffs on `runners/dsl/src`, `seeds`, and on every pre-existing file in
  `results/`.
