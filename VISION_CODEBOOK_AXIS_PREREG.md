# THE CODEBOOK AXIS (K) — PRE-REGISTRATION

*Committed BEFORE any measurement, per PROTOCOL §3. Branch
`gamma-substrate/codebook-axis`. Base `152ea76a`. Seed block **68000–68999**.
Engine built with `scripts/engine_build.sh`; provenance gate run as its own step
first (**624 passed**, engine `02ad951e4e45`).*

---

## 0. WHY THIS RUNG EXISTS

`VISION_VIDEO_PROBE_RERUN_RESULTS.md` relocated the wall to the sd/identity
layer and found it is **not an exponent**: linear in signature cells (1.0104)
*and* linear in codebook size (0.9394). It is **a coefficient (698 µs/cell, 55×
the drive's 12.6 µs) multiplied by K**. The binding quantity is **N×K**, and
**K has never been measured.**

`VISION_TERM_EVAL_COUNTER_RESULTS.md` then established that **27 of 27 prior
counters are BLIND or INERT on this axis**, built the one family that is not
(`term_unit:*`), and localised the cost: **`DimInfer` is 17 of 424 invocations
(4.0%) and 99.92% of all interior work.**

This rung measures K, measures whether the K loop is exhaustive, and profiles
inside `DimInfer` — then stops or fixes against a rule fixed here in advance.

---

## 1. STEP 0 — CHECK MY OWN INSTRUMENT ON *THIS* WORKLOAD FIRST

The predecessor stated plainly that `ShapeDecode`'s own unit sites are
"committed but unexercised and, by this rung's own standard, **INERT**." Its
`term_unit` charging sites were validated on an **N sweep at K=1 only**. **A
counter validated on one axis is not thereby validated on another** — that is
the exact error G5 exists to catch, and it has already caught one instrument in
this arc (the predecessor's own, §4 of its results).

**Therefore, before any headline: run G5 on BOTH axes of this rung.**

| sweep | axis | held fixed | G5 must return |
|---|---|---|---|
| **SWEEP-N** | signature cells N | K = 1 | RESPONSIVE (replication of the predecessor) |
| **SWEEP-K** | codebook entries K | N fixed | **RESPONSIVE — this is the new, unvalidated one** |

`scripts/g5_responsiveness_sweep.py::point_S` already accepts `k_codebook`, so
SWEEP-K needs no new workload — only a new sweep axis.

**If `term_unit:*` comes back BLIND or INERT on SWEEP-K, my first job is to add
the missing charging sites, re-verify with G5, and SAY SO** — exactly as the
predecessor did, **without redefining the statistic**. Adding a charging site
where work provably happens is a bug fix; changing what counts as a unit to make
a number move is §5 metric surgery and will not be done.

**If I cannot make the instrument responsive on the K axis, I report that and
STOP.** A blind measurement here would repeat the precise failure this whole
sequence exists to prevent.

---

## 2. WHAT I HAVE READ (code, not measurement) AND THE MODEL IT IMPLIES

Declared here so that the Phase-1 numbers are a **test** of a stated model
rather than a description fitted afterwards.

`shape_decode.rs::eval_dim_infer` (`:1868`) is, structurally:

```
parts    = load_parts(codebook_type)          # K entries          (:243 loop)
gens     = load_generators(generator_type)    # G entries
for part in parts:                            # skip unless part.dim_types
    eligible = gens.filter(dims_are_coord)    # (:1930)
    for gen in eligible:            for k in gen.params:   -> build_candidate
    for gen_a in eligible: for k_a: for gen_b != gen_a: for k_b: -> build_candidate
```

`build_candidate` (`:1442`) charges `term_units` in two loops over the aligned
signature: `pairs = N`, then `slot_cmps = N × s` where `s` = slots per relation.

The shipped generator codebook (`seeds/shape_decode_loop.json`) is **G = 5**,
with `params` sizes `[3, 2, 2, 3, 3]`, so `ΣP = 13` and `ΣP² = 35`.

**Attempts per eligible part, closed form, with no chosen constant:**

| arm | count | shipped value |
|---|---|---|
| length 1 | `ΣP` | **13** |
| length 2 (ordered, distinct generators) | `(ΣP)² − ΣP²` | **134** |
| **A = total** | | **147** |

**THE MODEL:** `term_unit:DimInfer  =  I × K_eligible × A × N × (1 + s)`
for `I` invocations.

**It already reproduces the predecessor's committed number exactly.** Its
workload was `I=17`, `K=1`, `N=142`, `s=3` (`DT = [pred, coord:r, coord:c,
val]`): `17 × 1 × 147 × 142 × 4 = 1,419,432` — **the exact figure in its
per-variant table.** I am therefore not proposing an untested model; I am
proposing one that already fits a committed point, and Phase 1 tests whether it
survives a *sweep* of the axis that point held fixed.

---

## 3. PHASE 1 — THE THREE MEASUREMENTS

### 3.1 What is K in practice? (a distribution, and which workloads)

Never measured. I will report, per workload, **both**:

- **K_total** — `ShapeSignature`-typed nodes the codebook loop at `:243` walks;
- **K_eligible** — the subset carrying `dim_types`, i.e. those that actually
  reach the generator loops (`:1930`'s `continue` gate).

**These are different numbers and conflating them would be the whole error.**
Workloads: boot with no optional seeds; boot with each seed that ships
`ShapeSignature` nodes (`stroke_shapes` 263, `character_shapes` 54,
`reading_constructions` 22, `math_capability_shapes` 17, `code_*` 15,
`inference_knowledge` 8 — static counts read from the manifests, to be confirmed
live); and after growth on a workload that mints quanta.

### 3.2 Is the K loop EXHAUSTIVE?

**Statistic:** measured `term_unit:DimInfer`, compared against the §2 model's
prediction at every sweep point.

- **ratio = 1.000 at every point ⇒ EXHAUSTIVE** — every observation is compared
  against every codebook entry, with no early exit.
- **ratio materially below 1 ⇒ something already prunes**, and I must say *what*,
  by locating the divergence rather than reporting the shortfall.

`checked` — already returned in `DimInfer`'s own result dict — gives an
independent attempt count and will be reported beside the derived one, so the
exhaustiveness claim rests on two readouts that could disagree.

### 3.3 Where inside `DimInfer` does the work go?

Profile, not total. The split I will report: **length-1 arm vs length-2 arm**,
predicted at **13 : 134 = 8.8% : 91.2%** of attempts.

---

## 4. THE STOP/GO RULE — FIXED NOW, IN ADVANCE

**GO to Phase 2 iff BOTH hold:**

- **(G-a)** the loop measures **EXHAUSTIVE** (§3.2 ratio ≥ 0.99), i.e. there is
  re-derived work to remove rather than a prune already present; **AND**
- **(G-b)** a skippable fraction **≥ 50% of attempts** is identified for which I
  can state, per fact, a **proof** that the skipped candidate could not have won
  — not a heuristic, not a threshold.

**STOP — "measured, not worth fixing" — if ANY of:**

- **(S-a)** the loop already prunes materially (ratio < 0.99): then the finding
  *is* the prune, and I report what it is;
- **(S-b)** no ≥50% provably-skippable fraction exists: a fix that removes a
  minority of work at the cost of a correctness argument is not worth it;
- **(S-c)** `K_eligible` is ~1 on every real workload **and** the non-K terms are
  small: then K is not the binding axis, and correcting the brief's premise is
  the result.

**A well-measured stop is a complete rung** (the locality-index precedent). I
will report a stop as loudly as a fix.

### 4.1 THE CANDIDATE FIX, DECLARED IN ADVANCE SO IT CANNOT BE INVENTED TO FIT

Occam ranking in `eval_dim_infer` is
`key = (steps.len(), residual_dims, base_name, ks)` — **composition length is
STRICT PRIMARY**. Therefore: **if any length-1 success exists anywhere, no
length-2 attempt can win, for any part.** Hoisting the length-1 pass over *all*
parts ahead of the length-2 pass and skipping length-2 entirely when the
length-1 success set is non-empty is **exact by the comparator's own definition**
— the same shape as batch-apply's fix: work re-derived that need not be, with
the answer untouched.

**THE KNOWN HAZARD, NAMED BEFORE MEASURING:** `checked` is **returned in the
result dict** (`:2031`, `:2046`). Skipping attempts **changes `checked`**, so
**byte-identity on `checked` will FAIL by construction.** This is declared now
so it cannot later be waved through as expected noise. Per §5 I will not redefine
`checked`; I will report exactly which committed assertions move, and treat a
move in any *verdict* field (`explained`, `base`, `generator`, `k`, `length`,
`transforms`, `dims`, `identity`) as a **finding that stops the fix**, not
something to tune.

---

## 5. PREDICTIONS (scored honestly, right or wrong)

| | prediction |
|---|---|
| **P1** | `term_unit:*` is **RESPONSIVE on SWEEP-K** without new charging sites — `build_candidate` is inside the part loop, so K should already flow through it. *If wrong, §1 applies.* |
| **P2** | The §2 model holds: measured/predicted = **1.000** at every point, both axes. |
| **P3** | The loop is **EXHAUSTIVE** — no early exit on success anywhere in `eval_dim_infer`. |
| **P4** | Length-2 is **91.2%** of attempts, so the §4.1 fix removes ~91% of `DimInfer` work **on the recognising path** and **0%** where nothing is explained (the mint path must still try everything — cost still tracks content). |
| **P5** | **`K_eligible` ≪ `K_total`** on real workloads: `dim_types` is optional and most shipped `ShapeSignature` nodes will lack it. If so, **the brief's N×K premise is right in form but the effective K is much smaller than the raw codebook**, and that correction is a Phase-1 result in its own right. |
| **P6** | Wall-clock will be **uninformative** (this machine swings 1.66× on load alone, measured). Counted operations decide; wall-clock is reported with concurrent-load state beside it and decides nothing. |

---

## 6. THE PROPERTY-COST CHECK — DECLARED IN ADVANCE

Batch-apply held verdict byte-identity over 235,200 values **and still destroyed
compute-∝-surprise**, unnoticed for two rungs. **Byte-identity is not
property-identity.**

The property this fix could damage is exactly that one: if length-2 is skipped
whenever length-1 succeeds, then **recognised** observations become cheap while
**unexplained** ones stay expensive — which *strengthens* compute-∝-surprise if
the reasoning is right, and inverts it if it is backwards. **I will measure it,
not assert it:** cost on an observation that recognises vs one that does not,
before and after, reported as a ratio. A fix that flattens that ratio is
rejected even with byte-identity green.

---

## 7. GATES

| gate | requirement |
|---|---|
| provenance | `tests/test_engine_provenance_migrated.py` — **run first, as its own step**, engine hash pinned in results |
| endpoint guard | `tests/test_provenance_endpoint_guard_migrated.py` — both endpoints pinned, never `HEAD` |
| oracle | `bash scripts/rung7_vision_bench.sh` → **222 passed, exit 0**, `data/` symlinked |
| sd orbit law | `{2:1, 3:2, 4:2, 6:2, 12:4}` **unmoved** |
| G5 | run on SWEEP-N **and** SWEEP-K before any headline (§1) |
| byte-identity | verdict fields, if Phase 2 happens; a failure is a **finding**, not a tuning signal |

Seeds: **68000–68999**, no other block.
