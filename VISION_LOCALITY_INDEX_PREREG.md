# LOCALITY INDEX ON THE STAR-SCAN PATH — PRE-REGISTRATION

*Written and committed BEFORE any measurement (PROTOCOL §3). Base
`81772f82b26fc1d211180a2249229490875ba55c` (the batch-apply merge).
Branch `gamma-substrate/locality-index`. Seed block **64000–64999**
(verified free: the ledger's last allocation is 63000–63999).*

**Engine at pre-registration time:**
`engine b31b5911dcee @ /home/matt/ozma/internal/research/experiments/gamma-substrate/runners/dsl/python/substrate_rs/_native.abi3.so [shared build — Rust source identical]`.

Phase 1 **adds no Rust**, so the shared canonical build is legitimate under
§10.1 rule 4 and the provenance gate reads `shared`. **If Phase 2 proceeds, it
adds Rust, and I will build this worktree's OWN engine
(`scripts/engine_build.sh`) and pin BOTH hashes** — never rebuilding the
canonical tree (§11).

---

## 0. WHY THIS RUNG EXISTS, AND WHY IT IS TWO PHASES

`VISION_SCALE_SPLIT_RESULTS.md` (`6905ec9b`) named a **locality index** as its
second tool. `VISION_BATCH_APPLY_RESULTS.md` (`81772f82`) then **overturned the
statistic that recommendation rested on**: after batching removed the
re-derivation loop, the survival log-slope went **−0.9928 → −0.0002** and
hypothesis (a) flipped ARCHITECTURAL → COMPUTATIONAL. Its own §9.2 says, in
terms: *"re-derive the payoff from these numbers, not from the predecessor's."*

So Phase 1 is **not** a formality before a build I have already decided on. It
is the rung's actual question. **A well-measured "not worth it" is the
complete deliverable if that is what the numbers say**, and I am writing the
stop condition down here, before looking, precisely so that momentum cannot
convert a weak result into a build.

---

## 1. WHAT I READ IN THE CODE BEFORE MEASURING — recorded here, as the batch
rung recorded its inertness finding

The batch rung established the precedent that reading the code *before*
touching it, and recording what you found *in the pre-registration*, is how a
predictable null gets prevented from masquerading as a result. I did the same,
and it changed what I am going to measure.

### 1.1 The star is PERFECT — one hub owns 100% of every hot edge type

`domains/wave_world.py` and `domains/lateral_world.py` mint every hot edge
from the **single** `self.retina` node:

| edge type | minted at | src |
|---|---|---|
| `has_cell` | `wave_world.py:158` | `self.retina` (one node) |
| `has_unit` | `wave_world.py:463` | `self.retina` |
| `has_hcell` | `lateral_world.py:93` | `world.retina` |
| `has_lbipolar` | `lateral_world.py:100` | `world.retina` |

### 1.2 Therefore the LITERAL recommendation has a structurally ZERO payoff

`rewrite.rs::extend_each` reaches a both-unbound `(None, None)` match-edge by
scanning `graph.edges_by_type(edge_type)`. A **locality index** — bind the hub
first, then traverse outward — replaces that scan with
`graph.neighbours(retina, has_cell)`.

**On a perfect star those two sets are IDENTICAL.** The hub's neighbourhood is
the entire edge set. Locality restriction cannot skip a single candidate,
because every candidate is local to the one hub. The saving is not small; it is
**exactly zero, by construction**.

This is the same fact the batch rung already measured from the other side and
did not generalise (§5.3): its type-indexed driver *"visits N nodes per pass
just as the star scan visited N edges per pass; it re-labels the bucket without
reducing the count."* That was reported about `batch_apply_rule`'s driver. I am
claiming it is a property of the **topology**, and therefore binds any
locality-shaped tool. **Phase 1 measures that claim rather than asserting it.**

### 1.3 The selectivity is in the WHERE-CLAUSE, on an ATTRIBUTE — a different tool

The candidates that "could never have won" are rejected by attribute
predicates, not by topology:

| rule | match | the conjunct that rejects |
|---|---|---|
| `wv_refract` | `[r, has_cell, c]` | `c.state == "active"` (equality, categorical) |
| `wv_recover` | `[r, has_cell, c]` | `c.state == "refractory"` (equality, categorical) |
| `wv_propagate` | `[r, has_cell, c]`, `[c, neighbour, n]` | `c.state == "active"` ∧ `c.activated_at == r.step` |
| `lat_pool` | `[r, has_hcell, h]`, `[c, pools_to, h]` | `h.pool_step < r.step` (**range**, and per-tick all-or-nothing) |
| `lat_residual` | `[r, has_hcell, h]`, `[c, pools_to, h]` | `h.resid_step < r.step` ∧ `h.pool_step == r.step` |
| `lat_bipolar` | `[r, has_lbipolar, b]`, `[h, rectifies_to, b]` | `b.bstep < r.step` ∧ `h.resid_step == r.step` |

So there **is** a real second tool here — an **attribute index** with
index-then-verify semantics — and the engine already ships the machinery for
it: `rewrite.rs::IndexJoinHint` (the R10 join-index wave, and the "Rust
join-index need" the deep-reader arc named). Its correctness contract is
already exactly the one this rung would need: *"index-THEN-verify, never
index-and-trust… a stale, absent, or wrong index can only make the search
WIDER, never produce an incorrect match."*

But `IndexJoinHint` probes with a value read off an **already-bound `via_var`**.
The wave rules probe with a **literal** (`"active"`). So it is not directly
applicable, and extending it is a build, not a config change.

**And the lateral rules look unpromising in advance:** their guard is
`step`-relative, so on the pass that matters *every* candidate satisfies it and
an index returns the whole set. I am recording that prediction now so that if
it holds it is not a post-hoc rationalisation.

### 1.4 Consequence: I measure TWO headrooms, not one

Because §1.2 predicts the recommended tool is worth exactly zero and §1.3
identifies a different tool that might not be, reporting only one number would
be misleading in either direction. **Both are pre-registered as primary.**

---

## 2. HYPOTHESES — two-sided

**H1 (attribution).** The residual scan share is genuinely both-unbound hub
enumeration in the wave/lateral rules — *not* a second mechanism wearing the
same shape, which is exactly the error that confounded the predecessor.
- *H1 true:* `cand_enum_scan` is exactly reproduced as a non-negative integer
  combination of hot edge-type cardinalities.
- *H1 false:* it is not — and then **the rung stops here** and the finding is
  that the 34.3% is something else again. That would be the second confounded
  attribution in this arc and worth more than any index.

**H2 (locality headroom, L).** The literal recommendation.
- *H2 null (predicted):* L = 0 — the hub's neighbourhood is the whole edge set.
- *H2 alive:* L > 0 — some hot edge type is not a perfect star.

**H3 (attribute headroom, A).** The tool §1.3 identifies.
- *H3 alive:* an ideal attribute index returns materially fewer candidates than
  the scan.
- *H3 null:* it does not — the where-clauses are not selective on the workload.

**H4 (exponent).** *A share is a snapshot at one N; the exponent is the
property.* This lesson has been paid for twice in this arc.
- *asymptotic:* the residual scan term's exponent exceeds the ideal-index
  term's exponent by a clear margin ⇒ an index changes the SCALING.
- *constant-factor:* both exponents agree ⇒ an index is a constant-factor win
  only, a materially different and much weaker proposition.

---

## 3. THE STATISTICS, EXACTLY

Measured on the **current post-batch engine**, via
`scripts/locality_index_measure.py`, which **imports** the sweep point, grid
list, bucket definition, log-log `fit`, liveness gate and conservation asserts
from `scripts/scale_split_measure.py` — the same instrument, unmodified, on the
batch rung's own precedent, so every number is directly comparable to both
predecessors. **The primary arm is the assembled eye, frame-driven**
(`sweep("constant", driven=True, arm="eye")`) — the object both predecessors
fitted.

Let `N` = cells; at each grid:

- **S** := `cand_enum_scan` — the residual star-scan candidates.
- **T** := `buckets.total` — whole-system counted operations.
- **V** := `leaf_visits` — survivors.
- **L_saving** := S − (candidates a locality restriction would enumerate)
  = S − Σ over scan expansions of `|neighbours(hub_of(edge_type), edge_type)|`.
  On a perfect star this is 0 term-by-term.
- **A_ideal** := Σ over scan expansions of the candidate count an **ideal**
  attribute index on that rule's most-selective *index-eligible* conjunct would
  return. Index-eligible := an equality between an attr of the scanned var and
  a value not depending on any unbound var. `A_saving` := S − A_ideal.

**A_ideal is a lower bound on any real index's output and an upper bound on its
saving** — it charges the index nothing, assumes perfect selectivity, and still
must return a superset of the survivors (index-then-verify). If the *ideal*
index does not pay, no real one can. This is deliberately the direction that
favours building, so that a stop verdict is not an artefact of a pessimistic
model.

**Hub-purity check (the H2 statistic, exact):** for each hot edge type,
`max_hub_outdegree / |edges_by_type|`. A value of 1.0 is a perfect star.

**Exponents:** log-log fits vs cells with r², over the pre-registered
`SIZES = [12,16,24,32,48,64]` (144–4096 cells), `WARMUP=5`, `TICKS=20` —
inherited, not chosen.

---

## 4. THE DECISION RULE — fixed HERE, before any number is seen

Evaluated at the **largest grid (4096 cells)** for shares, and over the whole
sweep for exponents.

Let `headroom := A_saving / T` (the whole-system fraction an ideal attribute
index removes) and `Δe := exponent(S) − exponent(A_ideal)`.

| verdict | condition |
|---|---|
| **GO — asymptotic** | `headroom ≥ 0.20` AND `Δe ≥ 0.30` with both r² ≥ 0.95 |
| **GO — constant factor** | `headroom ≥ 0.40` (regardless of Δe) |
| **STOP** | `headroom < 0.20` AND `Δe < 0.30` |
| **INDETERMINATE** | anything else — **reported as such, and treated as STOP** |

**INDETERMINATE resolves to STOP by PROTOCOL §9**: defaults preserve committed
results, so a build requires a positive case, not the absence of a negative
one. I am fixing that tie-break now rather than discovering a preference for it
later.

**A prior gate that overrides all of the above:** if **H1 fails**, the rung
stops at H1 regardless of L, A or any exponent. An attribution that does not
reproduce exactly is not a headroom measurement.

**What a stop looks like, concretely.** `VISION_LOCALITY_INDEX_RESULTS.md`
reporting the re-derived headroom, both exponents, the hub-purity table, the
predictions scored, and an explicit recommendation to the next rung that the
locality index is retired with cause. **No Rust is written. No seed is
touched. The engine is not rebuilt.** That is a complete rung and I will report
it as loudly as a build.

**No sweeps, no re-runs (§3.6).** One sweep, the pre-registered sizes. If the
verdict lands INDETERMINATE I report INDETERMINATE — I do not widen the grid
range until it moves.

---

## 5. PHASE 2, IF AND ONLY IF THE RULE SAYS GO

Conditions binding the build, written now so they cannot be relaxed later:

1. **Extend `IndexJoinHint`, do not invent a parallel mechanism.** It is the
   prior art, its correctness contract is already index-then-verify, and it is
   keyed by variable NAME so it survives `reorder_match_edges`.
2. **ACCESS PATH ONLY.** The index may change *which candidates are
   enumerated*; it must not change *which bindings match*. **I will state, per
   index, the argument that every skipped candidate was provably unable to
   match** — the way the batch rung stated its confluence argument per fact,
   not as a general appeal to "index-then-verify".
3. **BYTE-IDENTITY IS THE GATE**, checked FIRST, on the batch rung's protocol:
   full per-cell record, exact `repr`, no rounding, no tolerance; bench 200/0
   with `data/` symlinked; sd orbit law `{2:1,3:2,4:2,6:2,12:4}` unmoved.
   **If a verdict moves, I STOP and report it** — an index that changes an
   answer is skipping a candidate that could have matched, which is a
   correctness bug and a finding about the match semantics.
4. **MAINTENANCE IS A COST.** An incrementally-maintained index pays on every
   write. I will report maintenance in **counted ops** alongside the query
   saving and state the **crossover**. Reporting only the read-side win is
   exactly the way an index rung lies.
5. **§9 inertness control.** Ship off by default and measure — not assert —
   that the new Rust changes nothing when unused, as `off_new` did.

---

## 6. MY PREDICTIONS, IN ADVANCE (§3.7)

| # | prediction | basis | what would break it |
|---|---|---|---|
| **P1** | **H1 HOLDS** — `cand_enum_scan` reproduces exactly as an integer combination of edge-type cardinalities | `gate_known_count` already asserts `scan % (g·g) == 0` and passed for the predecessor | a non-integer residual ⇒ a third mechanism ⇒ rung stops at H1 |
| **P2** | **L = 0 EXACTLY**, and hub purity = 1.000 for all four hot edge types | §1.1 — one `add_node("Retina")`, every hot edge minted from it | any hot edge type minted from more than one src |
| **P3** | **A_saving is REAL but the verdict is STOP** — headroom in the 0.05–0.20 band | scan is 34.3% of `cand_enum`, but the buckets' F term is 43.3% of `T` and an index cannot touch it, so even a *perfect* index is bounded well below the scan share | if the wave front is a genuinely sparse contour, A_ideal could be ~√N and headroom could clear 0.20 |
| **P4** | **Δe ≥ 0.30 (asymptotic)** — the wave front is a 1-D contour in a 2-D grid, so active cells go as ~√N while the scan goes as N | wave geometry | if `state` is dominated by `refractory` (a *band*, area-scaling not perimeter-scaling), A_ideal is ∝N and Δe ≈ 0 |

**P3 and P4 point in OPPOSITE directions and I am registering both.** That is
not hedging — it is the actual structure of the decision rule, which is
deliberately conjunctive: an asymptotic win on a term too small to matter is
still a STOP under `GO — asymptotic`'s `headroom ≥ 0.20` clause. **If P4 is
right and P3 is right, the verdict is STOP, and the honest headline is "the
index changes the scaling of a term too small to be worth its maintenance
cost."** I would rather write that down now than discover I preferred the
asymptotic half after seeing it.

The prediction I hold most weakly is **P3's band**. The one I hold most
strongly is **P2**, and it is the one that retires the recommendation as
written.

---

## 7. BOUNDS DECLARED IN ADVANCE (§8)

- **ONE workload** — the retina drive on `vision_waves` + `vision_lateral`,
  frame-driven, `change=1`, `sustain=1`. The identity / sd-loop layer is **not**
  measured and nothing here generalises to it. Inherited from both predecessors.
- **A_ideal is a MODEL**, not a measurement of a built index: it charges zero
  for probe, maintenance and verification. It is an **upper bound on the
  saving**, chosen in the direction that favours GO.
- **Synthetic frames** (`_frames`, a smooth drifting field), inherited.
- The measured range is 144–4096 cells. **No 1080p projection is made.**
- Wall-clock, if quoted at all, is quoted **once**, with load state, and is
  excluded from every share.
- Seeds 64000–64999 are allocated. **Every statistic in Phase 1 is a
  deterministic count, so I expect to consume none** — that will be recorded
  either way in the ledger.
