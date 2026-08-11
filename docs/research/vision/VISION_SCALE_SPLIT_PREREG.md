# SCALE WALL, SPLIT THREE WAYS — PRE-REGISTRATION

*Written and committed BEFORE any measurement (PROTOCOL §3). Branch
`gamma-substrate/scale-wall-split`. Seed block **61000–61999** (verified free
before launch; high-water 60999; a concurrent redundancy-audit rung holds
59000–59999).*

---

## 0. WHAT IS BEING DECIDED, AND WHY THE SPLIT MATTERS MORE THAN THE TOTAL

`VISION_VIDEO_PROBE_RESULTS.md` (merged `40318951`) measured the wall on real
frames: **exponent 1.887 (r²=0.997)**, real-time affording **18×18**, one 1080p
frame extrapolating to **164 hours**. It named the cause as
*"the PyO3 boundary and then an O(N²) drive, not the ALU."*

**That is two causes, and there is a plausible third.** The three have
*different fixes*, and each fix addresses only its own term:

| term | what it is | the tool that attacks it |
|---|---|---|
| **F — FFI/PyO3 boundary** | marshalling, GIL, per-item crossings | an async Rust-resident collapse loop |
| **C — genuine pairwise comparison** | irreducible work comparing candidates | a proposal net (distillation) |
| **R — redundant recomputation** | work foveation / incremental reuse / caching should have avoided and didn't | foveated + incremental evaluation |

**It would be an expensive mistake to distil a net and discover half the wall
was FFI.** This rung's job is to report the shares with enough confidence that
the next rung can pick its tool. **A lopsided answer is the most useful
outcome**, because it names a single tool (PROTOCOL §7: a negative is a result).

---

## 1. MEASUREMENT DISCIPLINE — COUNTED, NOT WALL-CLOCK

**A concurrent rung is running on this machine.** The precedent is set and
merged: `ENGINE_WINNER_VALUE_RESULTS.md` (`62fadd1a`) reported cost as **counted
operations** (60,253,656 firings / 74,015,366 candidate evaluations) and
*refused* wall-clock, having measured that two verdict-identical runs differed by
**85 s, 1.66×, on machine load alone**. `VISION_VIDEO_PROBE_RESULTS.md` §0.1
recorded the same lesson the hard way: its S2/S5 absolute timings were taken
under another agent's `pytest` and are contaminated.

**So every headline number in this rung is a COUNT.** Counts are:

- **load-independent** — unaffected by the concurrent rung;
- **reproducible** — the same commit + same engine + same inputs give the same
  integer, which a wall-clock number never does;
- **attributable** — an operation is charged to exactly one bucket by a rule
  written down *here*, before it is counted.

**No wall-clock number will appear in a headline or a share.** Wall-clock is
recorded ONLY as a secondary, explicitly-labelled cross-check on whether the
counted decomposition tracks real time at all (§6.3), reported alongside the
concurrent-load state, and marked as the one contaminable number.

---

## 2. THE WORKLOAD, NAMED (PROTOCOL §8 — coverage is part of the claim)

**The drive is `domains/wave_world.py::WaveWorld.step()` on the committed
`vision_waves` seed** — the exact object `VISION_VIDEO_PROBE_RESULTS.md` §S5
fitted to get 1.887, and the exact object `scripts/scale_wall_measure.py` sweeps.
No new world, no new seed, no new rule.

- **Grids:** 12, 16, 24, 32, 48, 64 (cells 144 → 4096, a **28×** range).
  The video probe fitted 4 points over 7.1×; this is 6 points over 28×.
- **Regimes:** `constant` (ignite_k=1, the committed schedule — work fixed as N
  grows) AND `density` (ignite_k ∝ area — work scales with N). **Both are
  reported.** Reporting one would answer a different question than was asked
  (`scale_wall_measure.py`'s own standing rule).
- **Ticks:** 20 per point after 5 warm-up ticks, matching the committed sweep.
- **Frames:** the drive channel is exercised with real frames where the fovea
  arm requires it (§5); the confirmatory counted sweep uses the committed
  no-frame schedule so it is comparable to the 1.887 fit.

**Scope this does NOT cover, stated now:** the identity / sd-loop layer
(`ShapeDecode`, `TransformDecode`) is a *different* workload with a *different*
cost profile and is **not measured here**. The 164-hour figure came from the
retina drive, so the retina drive is what is split. Any generalisation to the
identity layer is out of scope and will be labelled as such.

---

## 3. THE ATTRIBUTION RULE — written before counting (this is the crux)

Instrumentation goes in **Rust** (CLAUDE.md: no agent decision logic in Python).
A new module `runners/dsl/src/scale_audit.rs` carries process-global atomic
counters on the `ENGINE_WINNER_VALUE` precedent (`selector_audit.rs`):
**env-gated `OZMA_SCALE_AUDIT=1`, default OFF**, so every committed result
reproduces byte-identically (PROTOCOL §9). When off the cost is one relaxed
atomic load on each instrumented path.

Every counted operation is charged to **exactly one** bucket:

### F — FFI / PyO3 boundary
- `ffi_calls` — entries into a `#[pymethods]` method from Python (**boundary
  crossings**).
- `ffi_items` — per-item units marshalled across: 1 for a scalar call, N for a
  bulk call (`get_attr_many` / `set_attr_many` over N nodes).
- `ffi_pyobjects` — Python objects *constructed* to satisfy a return
  (`value_to_py`, `attrs_to_pydict`). This is the real marshalling cost: `node()`
  materialises a full attribute dict (~10 objects) to read one field.

**Charged to F only what exists BECAUSE the call came from Python** — the
crossing, the argument unmarshalling, the return-object construction. The
underlying graph mutation is *not* charged to F; it would happen anyway.

### C — genuine pairwise comparison
- `where_evals` — where-clause evaluations on **distinct bindings within one
  enumeration pass**. This is the substantive per-candidate test: the
  irreducible pairwise work a proposal net would replace.
- `cand_tested` — `(src, tgt)` candidate pairs tested in `extend_each`.

### R — redundant recomputation
Defined **positionally and conservatively**: within one **epoch** (= one
Python→Rust call into a rule-running method: `tick`, `run_rules`,
`apply_rule_once`), a rule's **first** enumeration is charged to C; every
**later** enumeration of the same rule in the same epoch is charged to **R**.

The mechanism this targets is in `rewrite.rs::run_rules_opts`'s cold path: for a
non-`batch` rule it enumerates **every** binding, applies **one**, `break`s, and
the outer `while` re-enumerates from scratch. **None of the `vision_waves` or
`vision_change` rules carry `batch`** (verified by reading the seeds before
writing this file — declared here rather than discovered later). So a rule with
M progressing bindings costs M full enumerations.

- `cand_enum_first` (→ C) / `cand_enum_repeat` (→ R)
- `where_evals_first` (→ C) / `where_evals_repeat` (→ R)
- `bindings_cloned` — `Binding` clones in the collect-all vector (allocation
  count, reported under R).
- `apply_probe_rollbacks` — `apply_rule_full(record_undo=true)` applications that
  did **not** progress and were undone (probe-then-rollback waste).

**R IS A LOWER BOUND, BY CONSTRUCTION, AND THAT IS DELIBERATE.** Re-enumeration
*across* epochs — the adapter's `while nat.apply_rule_once(idx): pass` drive-phase
loop, where every call after the first re-derives a set the first already had — is
**not** folded into R. It is counted and reported **separately**
(`apply_rule_once` calls and their candidate totals), so the reader can see it
without it silently inflating the headline. **The conservative direction is the
one that argues against my own prediction (§7).**

### What is charged to NOTHING
Graph mutations (`set_attr`, `add_edge`) that a Rust-resident loop would also
perform. These are the true irreducible substrate cost and are counted
(`graph_writes`) but excluded from the three-way split, which is a split of the
**overhead**, not of the total. **This is stated now so it cannot be adjusted
later.**

### The share
`share(X) = X / (F + C + R)` in **counted operations**, reported per grid size
and per regime, with the raw counts alongside so any reader can re-derive a
different split from the same integers. **Operation counts are not
interchangeable units of time** — a PyO3 crossing and a where-evaluation do not
cost the same. §6.3's labelled wall-clock cross-check is the only thing that
speaks to that, and it is explicitly not a headline.

---

## 4. HYPOTHESIS (a) — IS THE O(N²) A SYMPTOM OF **CENTRALIZATION** RATHER THAN OF COMPARISON?

Every candidate is currently reached through a *global* enumeration. If regions
matched against locally-reachable candidates instead, the cost would be local
rather than quadratic-global — which would **dissolve** the term rather than
approximate it.

**The statistic.** `extend_each` reaches candidates by exactly three paths, and
each is counted separately:

- `cand_enum_scan` — the both-unbound case: a full scan of `edges_by_type`
  (**global by construction**);
- `cand_enum_local` — traversal from an already-bound node via
  `neighbours` / `in_neighbours` (**local**);
- `cand_enum_hinted` — the R10 `IndexJoinHint` probe (**indexed**).

Plus **survival**: `leaf_visits / cand_enum`, computed separately for the global
path. A candidate enumerated globally that never reaches a leaf visit is a
comparison that **could never plausibly have won**.

**Decision rule, two-sided, fixed now:**

- **ARCHITECTURAL (global-by-construction)** iff, at the largest grid,
  `cand_enum_scan / cand_enum_total ≥ 0.50` **AND** the global path's survival
  fraction **falls** with N (regression slope of `log survival` on `log cells`
  **< −0.5**, i.e. survivors roughly constant while enumeration grows ∝N).
- **COMPUTATIONAL (global-by-necessity)** iff `cand_enum_scan / cand_enum_total
  < 0.50` **OR** the survival fraction is flat in N (slope **> −0.2**).
- Anything else is **INDETERMINATE** and will be reported as such, not rounded
  into whichever verdict is convenient (§5).

**What each outcome implies.** ARCHITECTURAL ⇒ the wall is a *locality index*
problem; the tool is a locality-restricted candidate set, and a proposal net
would be approximating a term that a join index removes exactly. COMPUTATIONAL ⇒
the comparisons are real, the term is irreducible, and distillation is the right
tool.

---

## 5. HYPOTHESIS (b) — THE 164-HOUR FIGURE IS A **UNIFORM-GRID** NUMBER

164 hours assumes exact treatment everywhere. **This architecture explicitly
rejects that** (foveation; grounding that decays with eccentricity; compute ∝
surprise — `MEMORY: the center is the ungrounded fixed point`).

**The measurement.** `WaveWorld` already carries `fovea_radius` (committed,
default 0 = whole field, so §9 holds). Sweep the same grids at
`fovea_radius ∈ {0, 4, 8}` with a real drive frame, and fit the exponent of
**counted operations** vs cells for each.

**Decision rule, two-sided, fixed now:**

- **FOVEATION CHANGES THE SCALING** iff the counted-op exponent at
  `fovea_radius=4` is **below** the `fovea_radius=0` exponent by **≥ 0.30**
  (with r² ≥ 0.95 on both fits). Then the 164 h re-projects and that is a
  headline.
- **FOVEATION DOES NOT CHANGE THE SCALING** iff the exponents differ by
  **< 0.15**. Then the periphery is still being paid for in full, the
  architecture's own commitment is **not implemented in the drive**, and *that*
  is the finding — a named gap between what the architecture says and what the
  code does.
- Between 0.15 and 0.30: **INDETERMINATE**.

**A known confound, declared in advance.** `scale_wall_measure.py::fovea_node_count`
already establishes that `WaveWorld.__init__` mints h×w `RetinaCell` nodes
**unconditionally**, and `fovea_radius` is read **only inside `drive()`**. So the
node count — and therefore every rule's enumeration set — is **unchanged** by the
fovea. I therefore expect the second branch. **If that is what happens, the
result is not "foveation doesn't work"** — it is *"foveation is not wired to the
term that scales, and wiring it there is the build task."* The re-projection
under a **salience-weighted allocation** (a roughly-constant foveal region at
full exactness, the periphery at cheap-guess cost) will be reported as an
**explicitly counterfactual** projection derived from the measured per-cell
counts, labelled as an extrapolation and never as a measurement.

---

## 6. THE INSTRUMENT MUST BE GATED BEFORE THE AGENT (PROTOCOL §1)

**This arc has caught eleven inert instruments.** The counters are gated
red-then-green before any share is reported:

1. **NON-ZERO ON A LIVE RUN, ZERO WHEN OFF.** With `OZMA_SCALE_AUDIT` unset every
   counter reads 0 and the sweep is byte-identical to the committed one. A
   counter that is never non-zero is not an instrument.
2. **POSITIVE CONTROL — A KNOWN-COUNT WORKLOAD.** A hand-built micro-graph with a
   rule whose binding count is known by construction (k nodes ⇒ exactly k
   candidates on the scan path) must produce **exactly** that integer. A counter
   that has only ever been seen to move has not been tested.
3. **DETERMINISM.** Two independent runs at the same grid must produce
   **byte-identical** counter totals. This is the property wall-clock does not
   have and is the whole reason for counting. **A non-deterministic counter
   invalidates its own bucket** and will be reported as such rather than
   averaged.
4. **CONSERVATION.** `cand_enum_first + cand_enum_repeat == cand_enum_total`, and
   `cand_enum_scan + cand_enum_local + cand_enum_hinted == cand_enum_total`,
   asserted in the harness. A split that does not add up is a broken split.
5. **THE COUNTERS MUST NOT MOVE THE VERDICT.** The sweep's `ms_per_tick` fit with
   the audit ON and OFF is compared; the audit is an instrument, and an
   instrument that changes the exponent it measures is measuring itself.

### 6.3 The one contaminable number, isolated
A single wall-clock sweep is run to check whether the counted decomposition
tracks real time at all. It is reported in its own subsection, with `uptime` load
average and a `ps` scan for concurrent agents recorded next to it, and it is
**excluded from every share**. It can corroborate; it cannot decide.

---

## 7. MY PREDICTIONS, STATED IN ADVANCE (PROTOCOL §3.7)

Stated so that being wrong is informative. **I read `rewrite.rs` and the two
seeds before writing this**, so these are informed predictions, not blind ones —
which raises the bar on them, and the provisos are where I expect to be caught.

1. **R will be the largest term**, > 50% of counted overhead at the largest grid.
   *Reason:* the cold path re-enumerates every binding to apply one, and no
   `vision_waves` / `vision_change` rule is `batch`.
   *Proviso that would break it:* if the fixpoint terminates in very few passes
   (the double-buffered commit may mean only a handful of cells progress per
   tick), M is small and R stays small — and then the quadratic must come from
   somewhere I have not identified, which would be the more interesting result.
2. **F will be the SMALLEST term at large N**, < 20%. *Reason:* the bulk
   accessors (`get_attr_many` / `set_attr_many`) already collapsed the ~4N
   per-cell crossings that made the Python side 82% at 128², as recorded in
   `py.rs`. *Proviso:* `drive()`'s non-fovea path still does a per-cell
   `s.node(n)` + 3 × `set_attr` — **N crossings and a full attr dict per cell** —
   so on frame-driven ticks F could dominate. I predict F is small **on the
   no-frame schedule** and **materially larger on the frame-driven one**, and
   both are measured.
3. **Hypothesis (a): ARCHITECTURAL.** `wv_refract` and `wv_recover` match
   `[r, has_cell, c]` with both vars unbound ⇒ a full scan of all N `has_cell`
   edges to find the few cells in the right state. I predict
   `cand_enum_scan / cand_enum_total > 0.9` and a survival slope steeply
   negative. *Proviso:* `reorder_match_edges` may already be turning some of
   these into bound traversals, which would move share to `cand_enum_local`.
4. **Hypothesis (b): FOVEATION DOES NOT CHANGE THE SCALING** (the second
   branch), for the declared structural reason in §5. I predict exponents within
   0.15. *Proviso:* if the fovea's smaller `driven` set shortens the fixpoint,
   the repeat-enumeration count could fall and the exponent with it — which would
   be evidence that R and the fovea are the *same* lever and would strengthen the
   foveated-evaluation tool.
5. **The tool the evidence will select: foveated/incremental evaluation**
   (batch-apply + a locality index), **not** distillation. If instead C dominates
   and (a) comes back COMPUTATIONAL, the proposal net is the right build and I
   was wrong.

---

## 8. EXACTLY THE LISTED TESTS (PROTOCOL §3.6)

The confirmatory set is: the counted sweep (6 grids × 2 regimes), the (a)
path-share + survival-slope statistic, the (b) fovea exponent comparison, and the
five §6 instrument gates. **No sweeps beyond these, no re-runs, no parameter
search.** Anything further requires a new pre-registration with a new
mechanism-level hypothesis.

**Metric surgery is forbidden (§5).** The bucket definitions in §3, the decision
rules in §4 and §5, and the share formula are fixed by this commit. In
particular: **the split will not be re-defined after the shares are seen**, and
no optimisation will be performed after seeing a number.

## 9. ARTIFACTS

| what | where |
|---|---|
| instrumentation (Rust) | `runners/dsl/src/scale_audit.rs` + call sites in `rewrite.rs`, `py.rs` |
| selector (confirmatory) | `scripts/scale_split_measure.py` |
| raw counts | `results/scale_split.json` |
| results | `VISION_SCALE_SPLIT_RESULTS.md` |
| provenance gate | `tests/test_scale_split_provenance_migrated.py`, pinned to **BOTH** endpoints (never `HEAD` — `tests/test_provenance_endpoint_guard_migrated.py` fails any range ending at `HEAD`) |
| regression oracle | `bash scripts/rung7_vision_bench.sh` → **200 passed, exit 0**; sd orbit law `{2:1, 3:2, 4:2, 6:2, 12:4}` unmoved |

**Engine (§10):** this rung **adds Rust**, so it MUST build and measure its own
`_native.abi3.so` in this worktree. The build hash and the
`rust_source_fingerprint` verdict are recorded on every number.

**Seeds:** block **61000–61999** claimed. The sweep is deterministic under fixed
indices, so the expectation is **none consumed**; whatever is actually consumed
is reported.
