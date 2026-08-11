# THE IDENTITY-COST ANATOMY — PRE-REGISTRATION

*Committed BEFORE any measurement, any implementation, and any engine build is
read for a number. Seeds **78000–78999**. A concurrent rung holds 79000–79999
and is running; every wall-clock number below carries its load state as a FIELD.*

---

## 0. THE QUESTION, AND THE ONE FACT THAT REFRAMES IT

The brief asks: **the sd/identity layer's coefficient is 698 µs/cell, 55× the
drive's 12.6 µs. Where does it go now?**

**The first thing to establish is whether that number is still true — and there
is a specific, checkable reason to think it is not.**

| | |
|---|---|
| `VISION_VIDEO_PROBE_RERUN_RESULTS.md` measured 698 µs/cell on engine | **`4d451d8f6ed0`** |
| `VISION_CODEBOOK_AXIS_RESULTS.md` shipped its fix as engine | **`863706852555`** |
| the fix removed, on the **recognising** path | **91.16%** of `DimInfer` interior units |
| E1's workload (the 698 µs/cell measurement) is | **K=1, literal self-identity** — *the recognising path* |

**The 698 µs/cell coefficient was measured on a binary that predates the fix, on
exactly the path the fix improves.** No rung has re-measured it. The brief's own
framing says so — *"the profile is now unknown"* — but the consequence for the
headline number itself has not been drawn: **the 55× may already be substantially
smaller, and the "60 cells at K=1" real-time affordance with it.**

This rung's first duty is therefore a **replication with one variable changed**,
not a fresh exploration.

---

## 1. STEP 0 — G5 ON *MY* AXES, BEFORE ANY HEADLINE

Two predecessors validated `term_unit` on one axis each and **both had to check
the second**: the term-eval rung validated N at K=1 and recorded `ShapeDecode`'s
own sites INERT; the codebook rung found K RESPONSIVE only by testing it.

**My workload is different again — it varies a third quantity (PATH) and it reads
the profile POST-fix, where the dominant term has been cut 11×.** A counter that
was RESPONSIVE when `DimInfer` carried 99.92% of the work is not thereby
validated on a profile where it may carry much less.

**G5 runs on all three axes before any number is reported**, handed off to
`runners/dsl/src/g5.rs` — never reimplemented in Python.

| axis | varied | held |
|---|---|---|
| **SWEEP-N** | signature cells, 12 → 142 | K=1, path=exact |
| **SWEEP-K** | codebook entries, 1 → 16 | N=58, path=exact |
| **SWEEP-P** | path ∈ {exact, novel} | N=58, K=1 |

**Commitment (binding):** if a counter I intend to report comes back **INERT or
BLIND** on an axis I vary, I will **add the charging site, rebuild, re-verify,
and say so in the results** — exactly as both predecessors did. I will not
report a profile from a counter that has not been shown to move on the axis the
profile is about. **`Inert` is not a pass.**

### 1.1 THE COVERAGE CHECK — the axis where my instrument is most likely blind

The codebook rung recorded, as its own residual: *"7.3× wall against 11.3×
counted — the gap is the fixed rule-matching cost outside `DimInfer`, which this
fix does not touch."*

**Post-fix, that gap is no longer a rounding error — it may be the whole
remaining coefficient.** `term_unit` / `term_eval` count work *inside* Term
evaluation. If the residual cost lives in rule matching, they cannot see it, and
a profile built from them alone would attribute 100% of a coefficient they only
partly cover — the A8 failure in a new costume.

**So attribution is gated on a declared coverage test, run before any share is
quoted:**

> Fit `wall_ms` against `term_units_total` across SWEEP-N. Report **slope**
> (µs per counted unit) and **intercept** (the fixed cost that is NOT interior
> Term work), with r².

| outcome | reading |
|---|---|
| intercept small vs wall at N=142 | interior Term work dominates; per-variant shares are the coefficient |
| **intercept large** | **a fixed cost outside Term evaluation is a first-class term, and my per-variant shares describe only the part I can see** — I will say exactly that and quantify the uncovered fraction |

I am pre-registering the second outcome as a **fully reportable result**, so that
finding it cannot later look like a shortfall.

---

## 2. THE WORKLOAD — stated completely, per the bounds clause

The accumulation line's lesson is that **"K=4" is not a complete description of a
codebook**. Every number in the results will carry all five fields:

| field | value |
|---|---|
| generator | `point_S`-shape: deterministic LCG synthetic cells, seed base **78000** |
| N (signature cells) | 12, 20, 37, 58, 93, 123, 142 |
| K (codebook entries) | 1, 2, 3, 5, 8, 12, 16 |
| codebook **contents** | held[0] = the target itself; held[1..] = independent LCG draws (seeds 78001+) — stated, not summarised as "K" |
| path | `exact` (held[0] == target ⇒ recognised) / `novel` (target absent ⇒ nothing explained) |

**Why synthetic and not the 698 µs/cell rung's Jellyfin frames:** that harness
requires a live media server; it is neither deterministic nor available to a
successor. The cost of that choice is that **my µs/cell is not directly
comparable to 698 µs/cell** — different cell content, same loop. I will
therefore report the **RATIO across engines on MY OWN workload** as the
load-bearing quantity, and the comparison to 698 as **indicative only**,
explicitly labelled.

### 2.1 THE TWO-ENGINE ARM — what makes the ratio a measurement

To turn "the 698 is stale" from an inference into a measurement, the pre-fix
engine is **rebuilt in this worktree** by the codebook rung's own method
(`shape_decode.rs` checked back to `e4852dbc`, `scripts/engine_build.sh`), and
**the identical harness runs on both binaries.** Both engine hashes are pinned in
the results. A before/after ratio against a real binary is a measurement; against
a remembered number it is a story.

---

## 3. PREDICTIONS — scored honestly, including the ones I expect to lose

| | prediction | how it is scored |
|---|---|---|
| **P1** | **The 698 µs/cell is STALE.** Post-fix µs/cell on the recognising path is **≥5× lower** than the same harness on the pre-fix engine | ratio of µs/cell, two real binaries, one workload |
| **P2** | `term_unit:DimInfer` is **RESPONSIVE** on SWEEP-N and SWEEP-K with no new charging sites (replication of the codebook rung) | `g5.rs` verdict |
| **P3** | `term_unit:DimInfer` comes back **INERT or BLIND on SWEEP-P** — the path axis — because the counter aggregates over both arms | `g5.rs` verdict; if it is RESPONSIVE I was wrong and say so |
| **P4** | **`DimInfer` STILL owns the majority of interior units post-fix (>80%)** — the length-1 arm (`ΣP`=13/part) is untouched and still exhaustive | `term_unit:DimInfer / term_units_total` |
| **P5** | **The coverage intercept is LARGE** — ≥25% of wall at N=142 sits outside interior Term work | §1.1 fit |
| **P6** | **The named reducibility candidate is INVOCATION-level, not interior-arithmetic level.** The remaining interior arm is *not* exactly prunable (the codebook rung proved its Occam key discriminates within the arm); the re-derivation is `I`, the **DimInfer invocation count per fixpoint**, measured at **17** and, by that rung's own §8.4, **never explained** | argued from `term_eval:DimInfer` vs the number of distinct decodes the workload contains |

**P6 is the rung's substantive claim and it is pre-registered as a NAMED
CANDIDATE, not a measured saving.**

---

## 4. THE REDUCIBILITY QUESTION — and the instrument discipline that binds it

The brief asks whether the largest remaining term is *work re-derived that need
not be* (the batch-apply / codebook shape — exact, byte-identity-preserving) or
**irreducible arithmetic**.

**The discipline, fixed here before I know the answer:** *"Building an instrument
and using it in the same rung is how a statistic gets defined to suit the
answer."*

**Therefore this rung will NOT build a redundancy counter and then quote a
redundancy fraction from it.** The reducibility verdict will be argued from
counters that **already existed before this rung began** (`term_eval:DimInfer`,
`term_unit:DimInfer`, the model ratio the codebook rung fixed at 1.0000) plus
the loop's own source structure. If those cannot settle it, the honest output is
**"named, not measured"**, with the discriminating test pre-registered for a
successor to run on an instrument built in a separate rung.

**A negative is a full result.** If the remaining coefficient is irreducible
arithmetic with no re-derivation to remove, that is reported plainly — and it
means resolution is capped by real work, and the answer must come from fewer
cells decoded, foveation, or a cheaper recognition path. That conclusion is
worth as much as a saving and will not be softened.

---

## 5. WHAT IS NOT TOUCHED

- **No fix is implemented in this rung.** Measure, attribute, name.
- **No metric is redefined** (§5). `checked`, the sd orbit law, and every
  existing counter keep their meanings.
- `VISION_PROTOCOL.md` is not edited (§11).
- The oracle `scripts/rung7_vision_bench.sh` must read **222 passed, exit 0**;
  the sd orbit law `{2:1, 3:2, 4:2, 6:2, 12:4}` must be **UNMOVED**.
- Provenance gate runs as **its own step, before any number**, on **both**
  engines; both endpoints pinned, never `HEAD`.

---

## 6. GATES THIS RUNG MUST PASS

| gate | requirement |
|---|---|
| provenance | `tests/test_engine_provenance_migrated.py` — pass, run first, per engine |
| endpoint guard | `tests/test_provenance_endpoint_guard_migrated.py` — pass |
| oracle | `scripts/rung7_vision_bench.sh` — **222 passed, exit 0** |
| G5 | RESPONSIVE on every axis a reported counter is reported against, or a charging site added and re-verified |
| sd orbit law | unmoved |
| new gate | `tests/test_identity_cost_anatomy_migrated.py` — the harness's own invariants |
