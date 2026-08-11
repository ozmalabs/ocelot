# BATCH-APPLY THE DRIVE RULES — RESULTS

*Pre-registration: `VISION_BATCH_APPLY_PREREG.md`, committed BEFORE any Rust,
seed or adapter edit and before any measurement, at
`767f085049e81ed08156670e1e8ef11e71d67b5b` (base
`6905ec9bd72fca5a3803f588285305e090625b21`). Both endpoints pinned; no range
ends at `HEAD`.*

**Engines (§10) — TWO, both built in THIS worktree, both pinned:**

| arm | engine | md5 |
|---|---|---|
| `off_baseline` (before) | `0a0b088786df` | `27f511ec7e8617b38c4aa20da4387c58` |
| `off_new` / `on_new` (after) | `4d451d8f6ed0` | `ab01c23ed643a9a406120c08be5fa4b3` |

Both at
`.../agent-abc90c874edf888c9/.../runners/dsl/python/substrate_rs/_native.abi3.so`.
This rung **ADDS RUST**, so a shared canonical binary would have been invalid;
the "before" arm was built and run **before** the source was touched, and the
baseline `.so` was preserved so the comparison is between two known binaries
rather than between a binary and a memory.

**Machine:** AMD Ryzen 5 9600X, 12 logical cores. Load 0.89→2.08
(`off_baseline`), 1.49→2.19 (`off_new`), 2.19→2.41 (`on_new`).
**Selector (§12):** `scripts/batch_apply_measure.py`.
**Raw:** `results/batch_apply_{off_baseline,off_new,on_new}.json`.
**Seeds:** block 63000–63999 claimed; **none consumed** — every statistic is a
deterministic count.

---

## 0. THE HEADLINE

**Batching delivered, and it is exact.** The counted-operation exponent falls
from **1.9549 to 0.9930** (r² 0.99998) — quadratic to linear, reproducing the
predecessor's ablation (0.982) on the REAL path rather than by removing the
drive phase. At 4096 cells, counted operations fall **1,341,314,626 → 8,601,225
(155.9×)**, and Python→Rust drive entries fall **217,213 → 180 (1,207×)**,
**constant in N** across a 28× range of cell counts. **No verdict moved:**
8,400 cells × 14 attributes × 2 pairings = **235,200 exact-repr values
compared, ZERO differing**, plus bench 200/0 and the sd orbit law unmoved.

**Two things I got wrong, both reported below as findings rather than
footnotes.** (1) **The predecessor's recommendation, executed literally, would
have been INERT** — `apply_rule_once` never reads the `batch` flag, so setting
it in the seed alone changes nothing; this was found by reading the code before
touching it and is recorded in the pre-registration (§2). (2) **My prediction
P4 was WRONG**: the scan share and the −1 survival slope did NOT survive
(0.9995 → 0.3425; −0.9928 → −0.0002), which revises how the predecessor's
centralization statistic should be read (§5).

---

## 1. THE INSTRUMENT REPRODUCED THE PREDECESSOR EXACTLY — before any change

The prereg fixed the statistic as "the SAME instrument the scale rung merged".
That was taken literally: `scripts/batch_apply_measure.py` **imports** the
sweep point, bucket definition, log-log `fit`, liveness gate and conservation
asserts from `scripts/scale_split_measure.py` rather than reimplementing them.

The `off_baseline` arm then reproduced **every published number** of
`VISION_SCALE_SPLIT_RESULTS.md`, to the integer:

| cells | ops (this rung) | ops (predecessor) | calls (this rung) | calls (predecessor) |
|---|---|---|---|---|
| 144 | 1,958,347 | 1,958,347 | 7,739 | 7,739 |
| 256 | 5,702,007 | 5,702,007 | 13,517 | 13,517 |
| 576 | 27,813,451 | 27,813,451 | 30,964 | 30,964 |
| 1024 | 86,509,200 | 86,509,200 | 55,049 | 55,049 |
| 2304 | 427,255,115 | 427,255,115 | 122,425 | 122,425 |
| **4096** | **1,341,314,626** | **1,341,314,626** | **217,213** | **217,213** |

Exponent **1.9549** (r² 0.99992), scan share **0.9995**, survival slope
**−0.9928** — all identical. **A before/after claim is worth nothing if the
"before" is not the thing that was measured before**, and this is the evidence
that it is.

---

## 2. THE INTERVENTION — three parts, because one would have been inert

The predecessor's §9 recommendation was *"set `batch: true` on the five
`vision_change` rules and re-measure"*. **Executed literally, that produces a
null.** `Substrate::apply_rule_once` (`substrate.rs:1389`) calls
`rewrite::match_rule` — which returns ONE binding — and contains **no
`rule.batch` test anywhere**. The dispatch exists only in
`Substrate::run_rules_opts`, and `_drive_phase` deliberately does not use
`run_rules` (it would advance the wave rules an extra time per step and destroy
every committed result). **So the flag would have been set, read by nobody, and
the resulting null would have looked like a refutation of batching.**

This is the arc's eleven-inert-instruments failure arriving one layer up, in a
BUILD rather than in a measurement. It was found by reading the code first and
**recorded in the pre-registration, before the change**, so the null it would
have produced could not have been reported as a result.

The intervention is therefore:

**(A) Rust, purely additive — 83 insertions, 0 deletions.**
`Substrate::apply_rule_batch(idx)` dispatches to the engine's existing
`rewrite::batch_apply_rule` iff `rules[idx].batch`, and **delegates to
`apply_rule_once` verbatim otherwise**. Exposed via a one-line PyO3 handoff.

*Why a new method rather than a `batch` test inside `apply_rule_once`:* two
seed rules already set the flag (`seeds/vision_settle.json`'s `st_settle`,
`st_commit`). Putting the dispatch in `apply_rule_once` would have silently
changed their behaviour for every existing Python caller — a scope widening
disguised as a one-line fix. **With a separate entry point, every path that
does not call it is unchanged BY CONSTRUCTION**, which is what makes §9
structural here rather than merely tested — and §4 below measures that it
actually is.

**(B) Seed data.** `"batch": true` on the five rules, `vision_change` v1.1.0,
with the confluence argument written into each rule's comment.

**(C) Adapter, one line.** `_drive_phase` calls `nat.apply_rule_batch(idx)`,
keeping the `while ... : pass` loop verbatim. No conditional over graph state;
WHICH rules batch is decided by the seed.

### 2.1 One correction I made to my own Rust, before measuring

The prereg named a missing `eval_cache` clear as "the single most likely source
of a byte-identity failure", because `batch_apply_rule` matches with the cache
live and applies with `None`, and `ch_sustained`'s `Sum`/`Count` over
`Neighbours` is exactly such a cached term. `run_rules_opts` clears **after**
its batch dispatch, and I mirrored that — then realised the entry side was also
exposed: `apply_rule_batch` is called immediately after `tick()`, which can
leave entries behind. **The shipped method clears on the way IN as well as
OUT.** The fallback path passes no cache at all, so this makes the batch path
at least as fresh as the path it replaces. Five clears per tick.

---

## 3. THE MONOTONICITY CLASSIFICATION, AND WHAT IT LICENSED

Classified from the rule bodies **before** anything was enabled (prereg §3).

| rule | writes | classification |
|---|---|---|
| `ch_drive_median` | `c.driven`, `c.dstep_med` | non-monotone (mutating), **CONFLUENT** |
| `ch_transient_on` | `c.driven`, `c.dstep_on` | non-monotone (mutating), **CONFLUENT** |
| `ch_transient_off` | `c.driven`, `c.dstep_off` | non-monotone (mutating), **CONFLUENT** |
| `ch_sustained` | `c.driven`, `c.dstep_sus` | non-monotone (mutating), **CONFLUENT** — by (iv), not by locality |
| `ch_adapt_ref` | `c.lum_ref`, `c.ref_n`, `c.ref_step` | non-monotone (mutating, **read-modify-write**), **CONFLUENT** |

**NOT ONE OF THE FIVE IS MONOTONE.** Every one mutates attributes; calling them
add-only would have been false, and monotonicity is not what licensed batching.
**Confluence** did, on four facts, each of which could have failed:

- **(i) No retraction.** All ten effects are `set_attr` — zero `del_edge`,
  `del_node`, `add_node`, `add_edge`. The match structure is invariant across
  the phase, so the binding set cannot grow or shrink.
- **(ii) Self-narrowing only.** Each rule sets its own phase key to `r.step`,
  falsifying its OWN guard. An applied binding can only LEAVE the admissible
  set; **no effect makes any guard TRUE.**
- **(iii) Binding-disjoint writes.** One `Retina` hub (`wave_world.py:126`),
  one `has_cell` edge per cell (`wave_world.py:158`), lateral seeds use
  distinct edge types ⇒ **bindings biject with cells** ⇒ every write targets a
  `c` no other binding touches.
- **(iv) The one cross-binding read is of an attribute no rule writes.**
  `ch_sustained` sums `lum_raw` over neighbours; `lum_raw` is written by the
  ADAPTER before the phase and by no rule during it.

**`ch_adapt_ref` was flagged in advance as the one that would break first and
in the last decimal place** if (iii) ever failed — it accumulates
`lum_ref += (lum_raw − lum_ref)/max(ref_n,1)` against live graph state, so a
genuine shared accumulator WOULD be order-sensitive. It has its own assertion
in the durable gate rather than being folded into a cell count.

**All five were batched; none withheld. Coverage of the named target: 5/5.**

---

## 4. BYTE-IDENTITY — the gate, and it HELD

### 4.1 The §9 inertness control: the new Rust changes nothing when unused

`off_new` runs the NEW engine and the NEW adapter (`_drive_phase` calls
`apply_rule_batch`) with the flag **stripped from the seed data**:

| cells | ops identical? | state digest identical? |
|---|---|---|
| 144 / 256 / 576 / 1024 / 2304 / 4096 | **MATCH at all six** | **MATCH at all six** |

Exponent, r², scan share and survival slope are identical to `off_baseline` to
every reported digit (1.9549 / 0.99992 / 0.9995 / −0.9928). **The delegation
path is `apply_rule_once` verbatim, measured, not asserted.**

### 4.2 The intervention moves no verdict

| check | result |
|---|---|
| **full per-cell record, all six grids, `off_baseline` vs `on_new`** — 14 attributes per cell, exact `repr`, **no rounding, no tolerance** | **8,400 cells / 117,600 values — ZERO differing** |
| the same for `off_baseline` vs `off_new` | **117,600 values — ZERO differing** |
| **235,200 values compared overall** | **0 differ** |
| `bash scripts/rung7_vision_bench.sh`, `data/` symlinked (§10.2) | **200 passed, 0 failed, 0 skipped, exit 0** |
| `tests/test_sdloop_vision_migrated.py` — orbit law `{2:1, 3:2, 4:2, 6:2, 12:4}` | **8 passed, law unmoved** |
| `tests/test_batch_apply_migrated.py` (new, durable) | **8 passed** |

The 200/0 figure confirms the `data/` symlink was live and the 10 BSDS-gated
tests actually ran rather than silently skipping.

**The attribute set was fixed in the prereg before any comparison**, and
includes three attributes the drive phase does NOT write (`state`,
`activated_at`, `last_burst`) specifically to catch drift ESCAPING the phase
into `tick()`. It also includes the adapter-written `lum_raw`/`lum_prev`/
`lum_seen` so a corrupted READ side would show up. **The gate could not be
narrowed to whatever happened to match.**

---

## 5. THE EFFECT

### 5.1 Counted operations and the exponent

| cells | ops OFF | ops ON | ratio | drive entries OFF | ON |
|---|---|---|---|---|---|
| 144 | 1,958,347 | 307,676 | 6.4× | 7,739 | **180** |
| 256 | 5,702,007 | 552,175 | 10.3× | 13,517 | **180** |
| 576 | 27,813,451 | 1,217,369 | 22.8× | 30,964 | **180** |
| 1024 | 86,509,200 | 2,160,228 | 40.0× | 55,049 | **180** |
| 2304 | 427,255,115 | 4,844,442 | 88.2× | 122,425 | **180** |
| **4096** | **1,341,314,626** | **8,601,225** | **155.9×** | **217,213** | **180** |

**THE EXPONENT IS THE RESULT (the predecessor's own lesson):**

| term | exponent OFF | exponent ON |
|---|---|---|
| **total counted ops** | **1.9549** (r² 0.99992) | **0.9930** (r² 0.99998) |
| candidate enumerations | 1.9839 | 0.9914 |
| C — comparison/enumeration | 1.9798 | 0.9967 |
| F — FFI boundary | 0.9976 | 0.9968 |
| R — redundancy (positional) | 0.9473 | 0.9473 |

**Pre-registered verdict: DELIVERS** — 0.9930 < 1.4685 (the midpoint of the
two already-measured endpoints, derived not chosen) with r² 0.99998. The
ratio **grows with N** because the intervention removed a whole factor of N,
which is the point: 6.4× at 144 cells, 155.9× at 4096.

### 5.2 The floor, and the residual — both registered before measurement

**Measured drive entries: 180 at EVERY grid.** The prereg registered the band
`[n_rules × ticks, 2 × n_rules × ticks] = [100, 200]`, and **180 lands inside
it and is exactly explained**: 20 ticks × (5 base passes + 4 firing rules) —
`ch_drive_median` is guarded by `change < 0.5` and never fires at `change = 1`,
so four rules cost a second, empty quiescence pass and one does not.
**Nothing here was chosen: `n_rules` is read from the seed file and `ticks`
from the schedule (§13).**

**The residual is 80 calls (44.4%), and it is the quiescence pass**, not
batching — a property of `while ... : pass`. Dropping the `while` would reach
100, but only by assuming no batch pass can ever enable a new binding. That is
true for these five by their phase guards and **is not the adapter's
assumption to make** on behalf of rules it does not read. Left in place, and
named.

### 5.3 The win is the CALL COUNT, not the changed driver — arithmetic, from measured counters

`batch_apply_rule` changes two things at once, and they had to be separated
before the win could be attributed. Its `(Some(mt), 1)` arm drives from
`nodes_of_type` and pre-binds `c`, so `[r, has_cell, c]` becomes
`(None, Some(t))` → `CandPath::Local` (an `in_neighbours` lookup) instead of
`(None, None)` → `CandPath::Scan` (a full `edges_by_type` scan). That is why
the scan share moved.

**But it is cost-neutral in candidate count**, and the counters say so exactly:

```
drive-phase candidate enumerations  =  drive entries × N   in BOTH arms
  OFF:  217,213 × 4096  =  889,704,448   (measured: 889,704,448)
  ON:       180 × 4096  =      737,280   (measured:     737,280)
```

Both exact. The type-indexed driver visits N nodes per pass just as the star
scan visited N edges per pass; it **re-labels the bucket without reducing the
count**. **So the entire 1,206× reduction is the call-count collapse.** The
driver change is real, and it is not where the win came from.

### 5.4 The shares invert — and the exponents barely move

| at 4096 cells | F | C | R |
|---|---|---|---|
| OFF (positional) | 0.31% | 99.65% | 0.04% |
| **ON (positional)** | **43.28%** | **49.76%** | **6.96%** |

**FFI goes from 0.3% to 43.3% of counted operations while its exponent does not
move at all** (0.9976 → 0.9968) and its absolute value barely moves
(≈4.16×10⁶ → ≈3.72×10⁶). It became the largest single share purely because the
quadratic term next to it collapsed. **This is the predecessor's central
lesson demonstrated live: a share is a snapshot at one N; the exponent is the
result.** F at exponent 0.997 still cannot be a wall at any N, and the async
collapse loop is no more indicated now at 43% than it was at 0.3%.

### 5.5 Wall-clock — CONTAMINABLE, reported once, with its load state

Not a share, not a headline; load was 1.49–2.19 on 12 cores across both arms
with the concurrent-process list recorded in the raw JSON.

| cells | OFF ms/tick | ON ms/tick |
|---|---|---|
| 1024 | 344.68 | 13.34 |
| 2304 | 1766.50 | 29.85 |
| 4096 | 5489.26 | 56.35 |

Quoted only to show the counted result is not an artefact of counting. **The
counted ratio at 4096 is 155.9×; the wall ratio is 97×. They are not equal and
should not be** — a PyO3 crossing and a where-evaluation are both "one
operation" and cost very different amounts (§4.2 of the predecessor).

---

## 6. MY PREDICTIONS, SCORED (PROTOCOL §3.7)

| # | prediction | outcome |
|---|---|---|
| **P1** | Byte-identity HOLDS on all three D1 checks | **RIGHT.** 235,200 values, zero differing; bench 200/0; orbit law unmoved. The structural argument (§3) carried it, and my named self-suspicion — the `eval_cache` clear — was real enough that I hardened it on the way in as well as out before measuring (§2.1). |
| **P2** | DELIVERS, exponent ≈ 1.0 **and** ops within 2× of the ablation's 4.077×10⁶ | **HALF RIGHT, EXACTLY AS FLAGGED.** Exponent **0.9930** — right. Ops at 4096 = **8.60×10⁶ = 2.11×** the ablation — **outside my 2× bound**, by 5%. I predicted in advance that this half was the more likely to break, and gave the reason that turned out to be correct: the ablation performs ZERO drive-phase enumeration, batching still pays 180 full N-visits. Scored separately, as pre-registered. |
| **P3** | Floor approached, lands near 200 not 100 | **RIGHT.** 180, constant in N, inside the registered band, and exactly decomposed as 20 × (5 + 4). |
| **P4** | Scan share and −1 survival slope UNMOVED; hypothesis (a) survives | **WRONG.** Scan share 0.9995 → **0.3425**; slope −0.9928 → **−0.0002**; the pre-registered verdict flips **ARCHITECTURAL → COMPUTATIONAL**. See §7 — this is the rung's most interesting negative. |

**Two of four wrong or half-wrong.** The one that gated the rung (P1) was
right, and the one I flagged in advance as fragile (P2's ops half) is the one
that broke.

---

## 7. THE NEGATIVE THAT MATTERS: the centralization STATISTIC was mostly the re-scan loop

P4 predicted the survival slope would survive because "batching removes
REPEATED scans; it does not make any single scan local". **The slope went to
−0.0002 — survival is now CONSTANT in N.** The predecessor's §3 read a slope of
−0.9928 as "the precise signature of global-by-construction", concluding
**ARCHITECTURAL** and recommending a locality index second.

**What the two arms together now show:** survival fell as 1/N because
`cand_enum` grew as N² (calls ∝ N × scan ∝ N) while survivors grew only as N.
Remove the call factor and survival is flat, **even though every remaining scan
is still a both-unbound star scan through the same single `Retina` hub.**

So the honest revision is a split, not a reversal:

- **The predecessor's MECHANISM claim was right.** `wv_refract`/`wv_recover`
  and the lateral rules still fall to `CandPath::Scan` over all N `has_cell`
  edges; the residual **34.3%** scan share at 4096 is exactly them, and it is
  now linear (exponent 0.9903) because each runs ~10 times per tick rather than
  ∝N times.
- **The predecessor's STATISTIC was confounded.** The −1 slope was dominated by
  the re-scan loop, not by the star topology, so it could not have distinguished
  the two. **A survival slope is not a centralization detector while a
  re-derivation loop is in the path.**
- **Consequence for recommendation 2 (the locality index).** It is *not*
  refuted — the star scans are real and still there — but **its measured
  headroom is now much smaller**: it addresses 34.3% of a term that is already
  linear, where before it appeared to address 99.95% of a quadratic one.
  **Anyone picking up that recommendation should re-derive the payoff from
  these numbers, not from the predecessor's.**

This bears on the shelved async plan in the direction the task anticipated,
though not the way it framed it: **the fixpoint's order-independence held
perfectly** (235,200 values, zero differing), so nothing here counts against
async on correctness grounds. It counts against it on *value*, and more
strongly than before: F is now 43% of a **linear** term.

---

## 8. BOUNDS AND RESIDUALS (§8)

- **ONE workload.** The retina drive (`WaveWorld.step` on `vision_waves` +
  `vision_lateral`, frame-driven, `change=1`, `sustain=1`). **The identity /
  sd-loop layer is NOT measured**; nothing here generalises to it.
- **Confluence is proved for FIVE named rules, not for batching in general.**
  §3's four facts are properties of these rule bodies. A rule that retracts, or
  whose bindings share a written node, is NOT licensed by anything here.
  `batch_apply_rule`'s own contract ("caller guarantees `rule.batch`") is
  unchanged, and the guarantee is still the seed author's.
- **The byte-identity evidence is 8,400 cells over 6 grids on ONE frame
  schedule and 25 ticks.** It is exact where it looks. It is not a proof of
  confluence for all inputs — a longer run, a different `ChangeParams`, or the
  `fovea_radius > 0` path could in principle diverge, and none was measured.
  The durable gate re-runs the comparison but at one small grid.
- **`ch_drive_median` never fires in the measured arm** (`change = 1` falsifies
  its guard). Its batching is therefore licensed by argument and gated by the
  bench's `change = 0` default path, **but its batch path is not exercised by
  the sweep.** Named because it is the one rule whose ON-arm coverage is
  weakest.
- **The 2× miss in P2 is real and unexplained beyond the stated cause.** 180
  N-visits per 20 ticks is the drive phase's irreducible floor under this
  adapter; whether the ablation's 4.077×10⁶ is reachable at all without
  dropping the `while` is not measured.
- **Wall-clock is contaminable** and is excluded from every share (§5.5).
- **The projections in the predecessor's §4.2 are not re-derived here.** This
  rung measured 144–4096 cells and makes no 1080p claim; the measured exponent
  0.9930 is what it measured, over that range.
- **§9:** the Rust is purely additive (83 insertions, 0 deletions) and its
  inertness-when-unused is **measured** (§4.1), not assumed. No default moved
  outside the five named rules.
- **Artifact note:** the committed JSONs carry `state_digest` (sha256 over the
  exact reprs) rather than the ~3 MB full per-cell record. The full-record diff
  was run live across all six grids before compaction — the 235,200-value
  figure in §4.2 — and `--keep-state-record` regenerates it.

---

## 9. WHAT THE NEXT RUNG SHOULD DO

1. **The predecessor's recommendation 1 is DONE and CONFIRMED**, with the
   correction that it required a Rust entry point, not just a seed flag.
2. **Re-derive recommendation 2 (the locality index) from §7's numbers before
   building it.** Its target is now 34.3% of a linear term. It may still be
   worth building — the star scans are genuinely there — but the case is much
   weaker than the predecessor's 99.95%-of-a-quadratic framing implies, and
   that framing is now known to have been confounded.
3. **Do not read the survival slope as a centralization detector** on any path
   that still contains a re-derivation loop (§7).
4. **The `while ... : pass` quiescence pass is 44.4% of the remaining drive
   entries.** Removing it is a small, exactly-bounded win that requires a
   contract change (a rule declaring it cannot self-enable), not a heuristic.
5. **Batching is available to any rule that can argue §3's four facts.** The
   engine side is now wired for `apply_rule_once`-driven phases as well as
   `run_rules` ones; other adapter phase loops (`domains/language.py`,
   `domains/linear_algebra.py`) drive rules the same way and were **not**
   examined here.
