# LOCALITY INDEX ON THE STAR-SCAN PATH — RESULTS

## **VERDICT: STOP. NO INDEX WAS BUILT.**

*Pre-registration: `VISION_LOCALITY_INDEX_PREREG.md`, committed BEFORE any
measurement at `3828356552dad191e99f6039105efd0f98a81683` (base
`81772f82b26fc1d211180a2249229490875ba55c`). Both endpoints pinned; no range
ends at `HEAD`.*

**Engine (§10) — ONE, and this rung ADDS NO RUST:**

| | |
|---|---|
| engine | `b31b5911dcee` |
| path | `/home/matt/ozma/internal/research/experiments/gamma-substrate/runners/dsl/python/substrate_rs/_native.abi3.so` |
| source verdict | **`shared` — Rust source byte-identical to this worktree** |

Legitimate under §10.1 rule 4 precisely *because* nothing here touches `.rs`.
**No engine was rebuilt, in this worktree or the canonical one.**

**Machine:** AMD Ryzen 5 9600X, 12 logical cores. Load 1.33 → 1.30 across the
sweep. **Selector:** `scripts/locality_index_measure.py`.
**Raw:** `results/locality_index.json`. **Seeds:** block 64000–64999 claimed;
**none consumed** — every statistic is a deterministic count.

---

## 0. THE HEADLINE

**The locality index is retired with cause, and the cause is exact rather than
statistical.**

1. **The literal recommendation is worth ZERO — measured, at every grid.**
   Every hot edge type has **hub purity 1.000 with `distinct_srcs = 1`**. On a
   perfect star the hub's neighbourhood *is* the whole edge set, so a locality
   restriction cannot skip one candidate. `locality_saving = 0` at all six
   grids. Not "small". **Zero, by construction.**
2. **A different tool — an attribute index — is real but too small.** Its
   ceiling is **7.75% of whole-system counted operations at 4096 cells**, and
   that ceiling is **FLAT in N** (0.0764 → 0.0775 over a 28× range).
3. **The exponent DOES move, and it does not help.** The scan term is
   **0.9903** and the ideal-index term **0.5755** (Δe = **0.4148**) — the wave
   front really is a ~√N contour. But the whole system is **0.9943**, so the
   saving and the system grow at the same rate and **the share does not
   improve with scale.** An asymptotic win inside a term that is already the
   system's own order is not an asymptotic win for the system.
4. **Maintenance is NOT what kills it, and I will not pretend otherwise.**
   14,606 index-maintenance ops at 4096 against an 819,200-op query ceiling —
   **1.8%**. The share kills it. Reaching for the maintenance cost would have
   been a more comfortable argument and a less honest one.

**Pre-registered decision rule, applied:** headroom `0.0775 < 0.20` (so no GO),
Δe `0.4148 ≥ 0.30` (so not the STOP branch either) ⇒ **INDETERMINATE, which
prereg §4 fixed IN ADVANCE as resolving to STOP under PROTOCOL §9** — a build
requires a positive case, not the absence of a negative one.

**This is exactly the joint outcome prereg §6 registered as the awkward one**
(*"If P4 is right and P3 is right, the verdict is STOP, and the honest headline
is 'the index changes the scaling of a term too small to be worth its
maintenance cost'"*). Both were right. **The tie-break was written down before
the numbers existed specifically so that the asymptotic half could not be
promoted after the fact**, and that is the only reason this section reads as a
verdict rather than as a choice.

---

## 1. THE INSTRUMENT REPRODUCED BOTH PREDECESSORS — before any new analysis

`scripts/locality_index_measure.py` **imports** the grid list, `WARMUP`/`TICKS`,
the sweep point, the bucket definition, the log-log `fit`, the liveness gate and
the conservation asserts from `scripts/scale_split_measure.py`. Only the
analysis is new. The batch rung's standard: *a before/after claim is worth
nothing if the "before" is not the thing that was measured before.*

| statistic | this rung | `VISION_BATCH_APPLY_RESULTS.md` |
|---|---|---|
| scan share of `cand_enum` @ 4096 | **0.3425** | **0.3425** (34.3%) |
| residual scan exponent | **0.9903** | **0.9903** |

Both to four decimals, on the same engine family, without either number being
targeted. **The residual this rung is evaluating is demonstrably the same
residual the batch rung handed forward.**

---

## 2. H1 — IS THE RESIDUAL GENUINELY BOTH-UNBOUND HUB ENUMERATION? **YES**

This was the prior gate: the predecessor's centralization statistic was
confounded by another mechanism wearing the star's shape, and the task was
right to ask whether it had happened twice.

**It has not.** Three independent facts, all exact integers, no model:

- **`cand_enum_scan` is an exact integer multiple of the cell count at every
  grid** (quotient `q` = 200, 215, 200, 200, 200, 200), and every hot edge-type
  cardinality is itself an exact multiple of the cell count (asserted in the
  selector, not assumed).
- **The quotient fits inside the star rules' enumeration budget** (200 ≤ 280)
  at every grid — no scan candidate is left over that no star-rule enumeration
  could have produced.
- **Hub purity is 1.000 with `distinct_srcs = 1`** for `has_cell` (4096 edges),
  `has_hcell` (4096) and `has_lbipolar` (8192). Any scan over these types *is*
  hub enumeration; there is no non-hub source of these edges to confound it.

A mechanism other than both-unbound hub enumeration would not produce exact
multiples of hub cardinalities at six grids. `cand_enum_hinted = 0` everywhere,
and the two conservation identities hold at every point.

### 2.1 MY OWN INSTRUMENT FAILED THIS TEST FIRST, AND THE FAILURE IS A FINDING

My first implementation asserted a **per-rule** model — every star rule scans
its full edge set on every enumeration, so
`cand_enum_scan == Σ enumerations × cardinality`. **It failed: 55,040 measured
against 85,760 predicted at 256 cells.** I did not adjust it until it passed;
I went and found out why.

`Substrate` keeps a **per-rule, per-edge-type cursor** (`rule_cursors`,
`substrate.rs:1560`) with an incremental path that drives only edges added
since that rule's last visit. **A rule whose cursor is still valid and whose
driving edge type gained no edges enumerates ZERO candidates — while
`rule_cost_count` still increments.** So an enumeration count is not a scan
count, and *which* enumerations fall back to a full re-match is decided by
cursor validity, not by the topology.

**The pre-registered test was never the per-rule one.** Prereg §3 fixes H1's
statistic as *"a non-negative integer combination of hot edge-type
cardinalities"* — which is the divisibility-plus-budget test above. My script
was **stricter than my pre-registration**, demanding an assignment H1 never
claimed. Correcting the code to compute the statistic actually registered is
not metric surgery (§5): the measure never moved, the code computing it was
wrong. **Both the failure and the correction are reported here rather than
quietly fixed**, and §7 records per-rule attribution as a bound this rung does
**not** establish.

**And the failure turned out to be the most useful thing this rung found** —
see §6.

---

## 3. H2 — THE LOCALITY HEADROOM IS EXACTLY ZERO

| edge type | edges @ 4096 | distinct srcs | max hub out-degree | purity | **locality saving** |
|---|---|---|---|---|---|
| `has_cell` | 4096 | **1** | 4096 | **1.000** | **0** |
| `has_hcell` | 4096 | **1** | 4096 | **1.000** | **0** |
| `has_lbipolar` | 8192 | **1** | 8192 | **1.000** | **0** |
| `has_unit` | 0 | — | — | — | 0 (absent in this arm) |

`locality_saving = 0` at **all six grids**.

`extend_each`'s `(None, None)` branch scans `edges_by_type(t)`. A locality index
substitutes `neighbours(hub, t)`. **These are the same set whenever one node
owns every edge of the type** — and `wave_world.py:158,463` /
`lateral_world.py:93,100` mint every one of them from the single `Retina`.

The batch rung measured the same fact from the other side and did not
generalise it (§5.3: its type-indexed driver *"re-labels the bucket without
reducing the count"*). **It is a property of the topology, not of that
driver**, and it therefore binds any locality-shaped tool. That is now
measured rather than argued.

---

## 4. H3 / H4 — THE ATTRIBUTE INDEX: REAL, ASYMPTOTIC, AND TOO SMALL

| cells | S (scan) | T (all ops) | **S/T (ceiling)** | scan/`cand_enum` | survival |
|---|---|---|---|---|---|
| 144 | 28,800 | 376,796 | **0.0764** | 0.3371 | 0.2692 |
| 256 | 55,040 | 675,055 | **0.0815** | 0.3533 | 0.2596 |
| 576 | 115,200 | 1,493,849 | **0.0771** | 0.3403 | 0.2677 |
| 1024 | 204,800 | 2,651,748 | **0.0772** | 0.3409 | 0.2673 |
| 2304 | 460,800 | 5,950,362 | **0.0774** | 0.3420 | 0.2655 |
| **4096** | **819,200** | **10,567,305** | **0.0775** | **0.3425** | **0.2651** |

**THE CEILING IS MODEL-FREE AND IT DOMINATES EVERYTHING ELSE HERE.** The
pre-registered headroom is `(S − A_ideal)/T` for an index output `A_ideal ≥ 0`.
Its supremum over *every conceivable index* is `S/T`, at `A_ideal = 0` — an
index that removes the entire scan term for free, charging nothing for probe,
verification or maintenance. **That supremum is 7.75%, so no index that could
be built clears the 20% bar.** This is a theorem about the measured counts, not
an estimate from a model of an index.

**And 34.3% is not 7.75%.** The batch rung's residual share is quoted against
`cand_enum`; the decision needs it against whole-system operations. Carrying
the enumeration-relative number into a build decision would have overstated the
case by **4.4×**. Both denominators are in the table so they can never be
confused again.

### 4.1 The exponents — P4 was right, and it changes nothing

| term | exponent | r² |
|---|---|---|
| S — residual scan | **0.9903** | 0.99955 |
| A_attr — ideal attribute-index output | **0.5755** | 0.99595 |
| **T — whole system** | **0.9943** | 0.99999 |

Δe = **0.4148**, comfortably past the pre-registered 0.30. The mechanism is the
one prereg §6 predicted: the wave front is a **1-D contour in a 2-D grid**, so
the indexed candidate set scales as ~√N (0.576 against a perfect perimeter's
0.5) while the scan scales as N.

**Why it does not rescue the case, in one line:** `saving = S − A_attr ~ N^0.99`
and `T ~ N^0.99`, so `saving/T ~ N^-0.004` — **constant**. The measured share
confirms it: 0.0764 at 144 cells, 0.0775 at 4096. **Scaling up does not make
this worth building**, which is the objection that would otherwise have been
raised against a 7.75% number, and it is answered by measurement rather than
by argument.

### 4.2 The model I used is generous past the point of physical possibility

`A_attr` = 18,550 at 4096 cells. **Survivors are 633,941.** Index-then-verify
*must* return a superset of the survivors, so **no real index can output as few
candidates as my model assumes** — `A_attr` is below the physical floor. It was
chosen in the GO direction (prereg §7) and it is still generous by more than an
order of magnitude. **The STOP therefore holds a fortiori**, and the ceiling
(§4) does not depend on the model at all.

### 4.3 Maintenance, reported even though it is not the binding constraint

| cells | state transitions / 20 ticks | maintenance ops (2 per write) | query ceiling | maintenance as % of ceiling |
|---|---|---|---|---|
| 1024 | 3,293 | 6,586 | 204,800 | 3.2% |
| 4096 | 7,303 | 14,606 | 819,200 | **1.8%** |

**An incrementally-maintained `(RetinaCell, state)` index would pay for itself
easily on the read side.** The crossover is not close, and it is not the
reason to stop. Reporting only the read-side win is how an index rung lies;
reporting maintenance as the killer when it is 1.8% would have been the same
sin in the opposite direction.

---

## 5. THE OTHER HALF OF THE PREDECESSOR'S STATISTIC HAS ALSO INVERTED

The scale-split rung's headline was *"99.93% of candidates could never have
won."* The batch rung overturned the **slope** half. **The selectivity half is
gone too:**

**Survival is now 0.2651 and CONSTANT in N** (0.2692 → 0.2651 over 28×). Better
than one candidate in four survives every filter and reaches `visit`. The
enumeration is not mostly waste any more; **it is mostly work that matters.**
That is the deepest reason an index has little to remove here, and it is
measured on the same counters that produced the original 99.93%.

---

## 6. THE MOST USEFUL THING THIS RUNG FOUND CAME OUT OF THE FAILED GATE

**`q` — the number of full-set scans — is 200, CONSTANT in N**, against a
star-rule enumeration budget of 280. `S = q × N` exactly. So the residual scan
term is **not** "the star topology is inherently expensive per pass". It is
**a fixed number of enumerations that fall back to a full re-match**, each
costing a full N, while the rest take the incremental cursor path and cost
nothing (§2.1).

**An index would SHRINK those 200 scans. Making their cursors valid would
REMOVE them.** One is a constant-factor improvement on 7.75% of the system;
the other deletes the term.

**I am naming this as the next question, not as a result.** What I established
is the arithmetic (`S = 200 × N`, constant) and the existence of the cursor
mechanism (read from `substrate.rs:1560`). **What I did NOT establish is which
enumerations fall back or why** — that needs per-rule scan attribution, which
needs Rust the STOP verdict did not license me to write. Anyone picking it up
should measure that first and should not assume from this section that the 200
are reducible.

---

## 7. MY PREDICTIONS, SCORED (PROTOCOL §3.7)

| # | prediction | outcome |
|---|---|---|
| **P1** | H1 holds — scan reproduces as an integer combination of hub cardinalities | **RIGHT** on the statistic (exact at all six grids), but **my implementation of the test was wrong first** and failed (§2.1). Scored as right on the pre-registered measure, with the implementation error reported rather than absorbed. |
| **P2** | L = 0 exactly; hub purity 1.000 on every hot edge type | **RIGHT, exactly.** 0 at all six grids; purity 1.000 with `distinct_srcs = 1`. |
| **P3** | A_saving real but verdict STOP; headroom in 0.05–0.20 | **RIGHT.** 0.0775, inside the band. |
| **P4** | Δe ≥ 0.30 — the wave front is a ~√N contour | **RIGHT.** 0.4148; A_attr exponent 0.576 against a perfect perimeter's 0.5. |

**Four for four, and that deserves a discount rather than a victory lap.**
These predictions were made *after* reading `wave_world.py`, `lateral_world.py`
and `extend_each` closely, so they are informed, not blind — P2 in particular
was near-certain from four lines of adapter code. **The only genuinely
uncertain call was P3's band**, and the value of getting it right in advance is
that the STOP cannot now be read as a preference discovered after the fact.

---

## 8. VERIFICATION (its own step, exit code captured)

| check | result |
|---|---|
| `bash scripts/rung7_vision_bench.sh`, `data/` symlinked (§10.2) | **200 passed, exit 0** |
| `tests/test_sdloop_vision_migrated.py` — orbit law `{2:1,3:2,4:2,6:2,12:4}` | **8 passed, law unmoved** |
| conservation identities (both axes, every grid) | **hold** |
| `cand_enum_hinted` | **0 everywhere** — the indexed branch is untested, as it was for both predecessors |

The 200/0 figure confirms the `data/` symlink was live and the 10 BSDS-gated
tests actually ran rather than silently skipping (190/10 without `data/`).

**Byte-identity is structural here, not merely tested:** this rung added one
measurement script and two markdown files. **No `.rs`, no seed, no adapter, no
default, no engine rebuild.** There is nothing for a verdict to move through.

---

## 9. BOUNDS AND RESIDUALS (§8)

- **ONE workload** — the retina drive on `vision_waves` + `vision_lateral`,
  frame-driven, `change=1`, `sustain=1`, 144–4096 cells, 20 ticks. The
  identity / sd-loop layer is **not** measured and nothing here generalises to
  it. Inherited from both predecessors.
- **Per-rule scan attribution is NOT established** (§2.1). H1 is answered at
  the level it was asked — *is the residual hub enumeration* — not at the level
  of *which rule incurs it*. §6's recommendation depends on that finer
  attribution and is flagged as unmeasured accordingly.
- **`A_attr` is a MODEL**, and a physically impossible one (§4.2). The load-
  bearing number is the model-free ceiling `S/T`.
- **The maintenance figure charges 2 ops per state write** — a declared model
  of index upkeep, not a measurement of a built index. It is immaterial at 1.8%.
- **Synthetic frames** (`_frames`, a smooth drifting field), inherited.
- **No 1080p projection is made.** The measured range is 144–4096 cells; the
  claim that the headroom is flat in N is made over *that* range (28×) and no
  further.
- **The `q = 215` point at 256 cells** is the one grid where the quotient is not
  200; it is inside the enumeration budget and does not affect any fit, but it
  is not explained here.
- **Wall-clock is excluded from every share.** Load was 1.33 → 1.30 throughout
  and is recorded in the raw JSON beside the counts.
- **Seeds 64000–64999: ALLOCATED, NONE CONSUMED.** Every statistic is a
  deterministic count.

---

## 10. WHAT THE NEXT RUNG SHOULD DO

1. **The locality index is RETIRED WITH CAUSE.** Not "unproven", not "deferred"
   — its payoff is exactly zero on a perfect star, measured at six grids. The
   scale-split rung's recommendation 2 should be struck, not re-derived again.
2. **The attribute index is measured and declined**: ceiling 7.75% of the
   system, flat in N, on a term whose exponent (0.990) already matches the
   system's (0.994). Revisit only if the workload changes shape enough to move
   that share — and re-measure `S/T`, never `scan/cand_enum`.
3. **Measure per-rule scan attribution before touching the residual at all**
   (§6). `S = 200 × N` with `q` constant says the term is a fixed count of
   cursor-invalidation fallbacks. If those are reducible, the term goes away
   entirely and no index is needed; if they are not, an index buys 7.75%. **That
   measurement is cheap and it strictly dominates building anything here.**
4. **A share is a snapshot at one N; the exponent is the property — and now the
   converse.** This arc has twice been misled by a share. This rung was nearly
   misled by an **exponent**: Δe = 0.41 is a genuine asymptotic win inside a
   term that is the system's own order, and therefore buys nothing. **Neither a
   share nor an exponent decides alone; the pair does, against the whole
   system's exponent.**
5. **Do not read a per-rule enumeration count as a scan count** (§2.1). The
   incremental cursor path makes them different, silently.
