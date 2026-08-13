# Fixing the synchronous/Jacobi update in `mt_mean_field_marginal` — RESULTS

Prereg: `CAN_SYNCHRONOUS_UPDATE_FIX_PREREG.md`, same worktree/branch, base
`main @ cf53784` ("Merge can-solver-theoretical-limits: theoretical limits
of the CAN mean-field solver, GO"). Worktree
`/home/matt/ozmadev/ocelot-worktrees/can-synchronous-update-fix`, branch
`can-synchronous-update-fix`.

**Verdict, up front:** the fix (damping, λ=0.5 default) is landed, and it
works cleanly on every case tested. The exact scenario
`CAN_BELIEF_QUANTIZATION_RESULTS.md` §3.1 used to establish a persistent
period-2 limit cycle **oscillates under the old code (opposite-parity gap
5.615746) and converges cleanly under the fix (gap 0.000000)**, on the
identical draw, in the same worktree, before vs. after one code change —
confirmed with a `damping=1.0` cross-check that reproduces the old numbers
bit-for-bit. Extending well past the PREREG's own bounded re-check (126
total re-tested cells: the original 24-trial pre-registered sweep, the
30-cell N∈{4,16,32} sharpening, and a 72-cell stress extension to N=64,
β=4.0), **oscillation is not merely reduced, it is eliminated in every
single re-tested case** — a far stronger, more decisive result than the
PREREG's own registered "artifact vs. genuine signal" question anticipated
needing to adjudicate closely. This **partially retracts**
`CAN_BELIEF_QUANTIZATION_RESULTS.md` §3.1's "abandonment" interpretation
(§4 below) — reported precisely, not softened. Two prior findings
re-checked under the bounded subset: the V=2 no-zero-option frustration
cliff **holds and sharpens**; the small-N basin-count reversal's
**direction mostly holds but magnitude and the dominant-fraction sub-claim
change substantially** (§3 below) — both reported with real numbers, not
characterised. The crossover-point rung's own headline "no crossover N\*"
finding is **not re-confirmed or refuted here** — it needs a fresh full
sweep under the corrected solver, named as a follow-on, not attempted (out
of this rung's bounded scope, per the task's explicit instruction).

---

## 1. What was fixed, read from source, before vs. after

**Before** (confirmed by direct read at the start of this rung):
`can_ops.rs::mt_mean_field_marginal` (pre-fix, `:195-254` on `main@cf53784`)
iterated `σ_i ← tanh(β(Σ_j J_ij σ_j + h_i))` fully synchronously
(Jacobi-style — every node's update in a sweep reads the PREVIOUS sweep's
full state; `new_state` is swapped in whole at sweep end).
`mt_mean_field_with_h_override` (`:452-515` pre-fix) carried an
**independent, byte-identical copy** of the same defect — not named in
`CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md`'s own read (which cited only
the first function), found by this rung's own direct read and brought into
scope per the PREREG (§1).

**After** (this rung's change, `can_ops.rs`):

```rust
// can_ops.rs:41
pub const DEFAULT_DAMPING: f32 = 0.5;

// can_ops.rs:220-269 (mt_mean_field_marginal), and the identical change
// at :479-546 (mt_mean_field_with_h_override):
let raw_sigma = (beta * local).tanh();
let old_sigma = state.get(&c).copied().unwrap_or(0.0);
let new_sigma = (1.0 - damping) * old_sigma + damping * raw_sigma;
```

`relax_to_marginal` (`can_ops.rs:877-899`) gained a `damping: f32`
parameter threaded straight through to `mt_mean_field_marginal`. Three
internal call sites that don't expose damping as a caller choice
(`audit_basin:437`, `mt_conflicting_nodes:604-605`,
`mt_pairwise_similarity:636-637`) now pass `DEFAULT_DAMPING` explicitly, so
the fix applies wherever these diagnostics are read, not only where a
caller opts in. PyO3 bindings (`py.rs:2267` `mt_mean_field_marginal`,
`py.rs:2374` `mt_mean_field_with_h_override`, `py.rs:2621`
`mt_relax_to_marginal`) each gained `damping=0.5` as a new trailing
`#[pyo3(signature=...)]` default — every existing Python call site in the
repo (checked exhaustively, §5) passes at most 3 positional args to the
first two and 5 to `mt_mean_field_with_h_override`, all strictly below the
new parameter's position, so this is additive at the call-site contract
level; the DEFAULT *behaviour* changes (that is the point of the fix).

**Sweep scheduling is still synchronous.** Damping does not touch which
node order a sweep visits or whether a sweep reads updated-this-sweep
values — it only blends each freshly-computed σ with its own prior value
before committing it. This was the PREREG's own registered choice (§2
below explains why), not an oversight.

---

## 2. Chosen fix and why — damping, not async/Gauss-Seidel

**Damping (weighted blend of old and newly-computed σ), λ=0.5 default.**
Decided against this codebase's own specifics, not defaulted to the first
option in the theory doc's list:

1. **No RNG infrastructure exists in the Rust engine, confirmed by direct
   check before choosing.** `runners/dsl/Cargo.toml`'s full dependency
   list has no `rand` crate; `grep -rn "rand::" runners/dsl/src/*.rs`
   returns zero hits anywhere in the engine. Standard practice for
   async/Gauss-Seidel scheduling is *randomized* sweep order specifically
   because a *fixed* order is itself a known source of new,
   order-dependent pathologies — confirmed this session via WebSearch
   (residual-BP / message-scheduling literature: asynchronous convergence
   "highly depends on the update schedule" `[search-synthesis,
   converging]`). Building a bespoke RNG source for this one function,
   seeded and reseeded however, would be exactly the "inconsistent with
   existing patterns" outcome the task's own instructions warn against —
   there is no existing pattern to be consistent WITH.
2. **Damping is deterministic and order-independent.**
   `mt_mean_field_marginal` iterates `concepts: Vec<NodeID>` in whatever
   order `mt_concepts` (a graph edge walk) returns them — an order no
   caller has ever had to reason about. Async/Gauss-Seidel without
   randomization would turn that incidental order into a load-bearing
   convergence factor, a strictly worse property to introduce than the one
   being removed.
3. **Damping provably preserves the existing fixed-point set.** At any
   true fixed point, `old_sigma == raw_sigma`, so
   `(1-λ)·old + λ·raw == old` for ANY λ — damping cannot move or remove a
   fixed point, only the trajectory used to reach one. This is the direct
   mechanical reason §5's regression came back clean on every
   already-correctly-converging case.
4. **It is the literature's own "cheapest" characterization**
   (`CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md` §7 item 1), confirmed by
   the diff size: one new constant, one changed line (duplicated once for
   the sibling function), one new threaded parameter — no new Term, no new
   dependency.

**λ=0.5, reported honestly.** WebSearch this session (multiple
independent, converging sources — a direct arXiv/Semantic-Scholar fetch of
Murphy, Weiss & Jordan 1999 itself returned unusable binary/PDF-stream
content both times, the same failure mode `CAN_SOLVER_THEORETICAL_LIMITS_
RESEARCH.md` §8 point 5 already reported for this exact paper) confirms
`δ=0.5` (`p_new = 0.5·p_old + 0.5·p_computed`) is repeatedly described as
the standard/default damping factor in the damped-BP literature. **This is
reported at search-synthesis confidence as a literature-COMMON default,
not as a value independently verified from Murphy/Weiss/Jordan's own
primary text, and not as a value empirically tuned against this
codebase's own networks.** It was registered in the PREREG *before* any
result was seen (§2 there), specifically so it could not be adjusted after
the fact. §3-4 below report that it worked decisively on every case tested
at this value — this rung did not need to search for a better λ, so none
was tried.

**Explicitly not built**: async/Gauss-Seidel scheduling, or an RNG
infrastructure decision for the engine. Named as future work only.

---

## 3. Live before/after demonstration — the exact PREREG §3 scenario

Reused verbatim: N=8 complete graph, `pair_rng = Random(20260813*31+8)`,
`field_rng = Random(20260813*53+8)`, fine (17-value) rounding, β=2.0,
all-zero start, fixed nonzero external field per node.
(`tests/test_can_belief_quantization.py::test_relaxation_shows_a_real_cohere_vs_fail_to_cohere_signature`,
updated this rung — see §6.)

**BEFORE** (unfixed engine, built and run first, before any code edit —
`git worktree` at `main@cf53784` unmodified):

```
opposite-parity gap (400 vs 401): 5.615746
same-parity gap     (400 vs 402): 0.000000
oscillating: True
```

Matches `CAN_BELIEF_QUANTIZATION_RESULTS.md` §3.1's own report of this
exact draw ("~5.6" gap, confirmed same-parity control) precisely — this is
a live re-derivation of the historical result, on this commit, not a
quotation of it.

**AFTER** (fixed engine, default `damping=0.5`, same draw, same code
otherwise):

```
opposite-parity gap (400 vs 401): 0.000000
same-parity gap     (400 vs 402): 0.000000
oscillating: False
```

**Cross-check** (fixed engine, `damping=1.0` explicit — the algebraic
claim that `damping=1.0` reproduces the pre-fix update exactly):

```
opposite-parity gap (400 vs 401): 5.615746   <- bit-for-bit identical to BEFORE
same-parity gap     (400 vs 402): 0.000000
oscillating: True
```

Confirms `(1-1.0)·old + 1.0·raw == raw` is not merely an algebraic claim on
paper — it reproduces the historical numbers to the reported precision on
the SAME binary, same build, only the `damping` argument changed. This
cross-check is now a permanent regression test
(`test_relaxation_shows_a_real_cohere_vs_fail_to_cohere_signature`, §6).

**Note on the converged marginal itself**: the damped fixed point
(`{1: 0.988, 2: -0.995, 3: 1.0, 4: -0.995, 5: 0.981, 6: 0.671, 7: -1.0, 8:
-0.9995}`) differs from either phase of the old 2-cycle
(`{1: -0.993, 2: -0.998, ..., 6: 0.994, ...}` at even iteration counts) —
expected and unsurprising: damping changes the TRAJECTORY through the
energy landscape, and a frustrated network can have multiple genuine fixed
points: the damped solver settled into a different one nearby, not "the"
average of the old cycle's two phases. This is a real, honest observation,
not a discrepancy to explain away.

---

## 4. Bounded re-check of prior findings, and the abandonment-hypothesis
assessment

Per the PREREG's registered plan (§4), NOT a full re-sweep. All numbers
below are real engine output, `tests/test_can_crossover_point.py`'s own
helpers reused unmodified (only the now-default damping changes their
behaviour).

### 4.1 The oscillation/abandonment question — the headline finding of this rung

**Every re-tested cell converges cleanly. Zero exceptions, across 126
re-tested networks:**

- The ORIGINAL pre-registered 24-trial sweep
  (`_flatten_oscillation_study`, N∈{6,8,10,12}×3 seeds×{fine,coarse}) —
  previously 6/12 (50%) fine, 8/12 (66.7%) coarse oscillating — is now
  **0/12 (0%) both conditions.**
- `CAN_CROSSOVER_POINT_RESULTS.md`'s own sharpening-(b) cells, N∈{4,16,32}
  × 5 seeds × {coarse V=3, fine V=7} (30 cells; previously up to 100%
  oscillating at N=32) — now **0/30 (0%), every cell, gap exactly 0.0.**
- A stress extension past the PREREG's own registered scope, run to
  determine which of the task's two named outcomes (artifact vs. genuine
  overflow-survives-under-the-fix) actually obtains rather than assuming
  either: N∈{16,32,48,64} × 3 seeds × β∈{2.0,3.0,4.0} × V∈{2,3} (72
  cells, both an opposite-parity gap check AND a 400-vs-2000-iteration
  drift check) — **0/72, every cell, both checks exactly 0.0.**

**Assessment, precise and not softened**: this is not a weak, same-
direction lean of the kind `CAN_BELIEF_QUANTIZATION_RESULTS.md` §3.1
honestly reported (24- and 40-trial samples, "small and noisy," reversed
on the single most dramatic individual draw). It is a **complete,
zero-exception elimination of the phenomenon across every network this
rung tested**, at N up to double the original rung's own upper bound (64
vs. 32) and β up to double the tested value (4.0 vs. 2.0). **This is the
ARTIFACT outcome named in the PREREG's §5 as one of two possible results,
found decisively**: the persistent 2-cycle `CAN_BELIEF_QUANTIZATION_
RESULTS.md` §3.1 measured, and treated as supporting evidence for the
"collapse fails, thought abandoned" hypothesis, was — on every case this
rung could test it against — a **numerical scheduling artifact of the
fully-synchronous update, not a genuine representational-overflow
signal.**

**This partially retracts, precisely, `CAN_BELIEF_QUANTIZATION_
RESULTS.md` §3.1's own interpretive framing**, which read the 2-cycle as
"real, existing, load-bearing evidence for exactly the 'honest
discriminative null' SHAPE" alongside the sd loop's recognize/mint,
`check_edge`'s rejection, and gap-awareness's honest floor. That framing
should be read as **weakened, not as never having been a real
observation** — the 2-cycle itself was real and correctly measured (§3
above reproduces it exactly); what this rung retracts is the
INTERPRETATION that it evidenced a genuine "network fails to settle
regardless of scheduling" phenomenon. Every tested instance of it turned
out to be exactly that scheduling-dependent, and none of it survived a
literature-standard scheduling fix.

**What this does NOT establish, stated as precisely as the retraction
above**: this rung did not find, anywhere it looked, a case where genuine
overflow survives the fix as a distinguishable failure-to-converge (the
PREREG's §5 second named outcome). That is a real, meaningful negative
result on the 126 cells tested — but it is bounded by what was tested:
complete graphs only (the same limitation the prior two rungs both
inherited and named), β≤4.0, N≤64, a single fixed-field/all-zero-start
initial condition per trial. `CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md`
§4.4's own honest caveat — that even Bethe/BP, one rung up the hierarchy,
is known to lose its solution in a sufficiently frustrated+field+low-T
corner — means the theoretical possibility of a genuine, scheduling-
independent non-convergence has not been ruled out in general, only not
found in this rung's (substantially extended) search. A future rung
wanting to close this fully would need to push β and N further, and/or
test non-complete/sparse topologies, which is out of this rung's scope.

### 4.2 The V=2 no-zero-option cliff — holds, and sharpens

`CAN_CROSSOVER_POINT_RESULTS.md` §3's cleanest finding (V=2 vocabulary
producing 1.6-2× the frustration of every V≥3 vocabulary, at every tested
N) re-run at N∈{8,16}, V∈{2,3,7}, 5 seeds, 40 restarts:

```
N    V    eff_basin  dom_frac   frustr     energy
8    2    2.864      0.480      13.338     -14.662
8    3    3.616      0.405      5.645      -9.555
8    7    2.088      0.575      6.274      -8.526
16   2    12.131     0.210      82.206     -37.794
16   3    7.907      0.280      30.363     -27.037
16   7    5.763      0.365      35.400     -22.867
```

V=2/V=3 frustration ratio: **2.36× at N=8** (13.338/5.645), **2.71× at
N=16** (82.206/30.363). V=2/V=7 ratio: **2.13× at N=8**, **2.32× at N=16**.
The original (unfixed-solver) ratios were ~1.6× (N=8) and ~2.0× (N=16) —
**the cliff is not merely preserved under the corrected solver, it is
LARGER.** The V=3-vs-V=7 ordering (no reliable monotonic trend among
V≥3) also holds precisely: V=3 < V=7 at both N=8 (5.645 vs 6.274) and
N=16 (30.363 vs 35.400), matching the original rung's own "V=3 lowest at
N=16" observation. **This finding is CONFIRMED, not merely un-refuted, by
the corrected solver** — it was never an artifact of the scheduling bug.

### 4.3 The small-N basin reversal — direction mostly holds, magnitude and
the dominant-fraction sub-claim change substantially

`CAN_CROSSOVER_POINT_RESULTS.md` §2's Experiment A cells at N=4, N=8
(coarse V=3 vs fine V=7, 5 seeds, 40 restarts each) re-run under the
corrected solver:

```
                    ORIGINAL (unfixed)              CORRECTED (damped, this rung)
N   cond   eff_basin  dom_frac  frustr    |  eff_basin  dom_frac  frustr
4   coarse   4.662     0.335     1.989    |    2.358     0.565     0.265
4   fine     3.235     0.475     2.443    |    2.145     0.560     0.851
8   coarse   5.808     0.390    14.065    |    3.616     0.405     5.645
8   fine     4.508     0.365    14.341    |    2.088     0.575     6.274
```

**What holds**: the qualitative DIRECTION of the reversal (coarse shows
MORE effective basins than fine, the surprising, opposite-of-naive-
intuition finding both prior rungs led with) survives at both N=4
(2.358 vs 2.145) and N=8 (3.616 vs 2.088) — a smaller margin at N=4, a
similar-sized margin at N=8. Frustration stays lower for coarse than fine
at both N under the corrected solver too (0.265<0.851 at N=4;
5.645<6.274 at N=8), same direction as originally reported.

**What changes, reported precisely, not smoothed over**: (1) **absolute
magnitudes collapse substantially** — frustration drops by roughly 7-10×
at N=4 and 2-2.5× at N=8, and effective-basin-count roughly halves at
both N. This is the direct, expected consequence of §4.1: many of the
original "distinct basins" the multi-start clustering counted were almost
certainly restarts landing on DIFFERENT PHASES of an oscillation-corrupted
pseudo-fixed-point, not genuinely different equilibria — the corrected
solver reports the TRUE (lower) frustration and a smaller, more accurate
basin count because it isn't miscounting cycle phases as basins anymore.
(2) **The `dominant_basin_fraction` sub-claim (coarse LESS concentrated
than fine) does not survive at N=4**: original 0.335 (coarse) vs. 0.475
(fine) — coarse clearly less concentrated; corrected 0.565 (coarse) vs.
0.560 (fine) — now essentially IDENTICAL, the claimed asymmetry is gone.
At N=8 the direction outright REVERSES: original 0.390 (coarse) vs. 0.365
(fine) — already a near-tie, coarse slightly MORE concentrated; corrected
0.405 (coarse) vs. 0.575 (fine) — now fine is clearly MORE concentrated, a
real reversal of the (already-marginal) original ordering.

**Assessment**: the *raw/effective basin-count reversal* (the headline
qualitative finding both prior rungs reported) is the most robust part of
this result and survives the fix in direction, though not in the exact
magnitude that fed the (never-met, per `CAN_CROSSOVER_POINT_RESULTS.md`
§2.1) crossover criterion. The *dominant-fraction* reading — used in
`CAN_BELIEF_QUANTIZATION_RESULTS.md` §3's "coarse is unstable/easily
knocked between alternatives" interpretive gloss — does **not** hold up
cleanly under the corrected solver at either tested N, and should be
treated as **needing re-measurement**, not as confirmed, going forward.
This is reported as a genuine partial correction, not a footnote.

### 4.4 What this bounded re-check does NOT settle

`CAN_CROSSOVER_POINT_RESULTS.md`'s own headline finding — no crossover N\*
in N≤32 under the registered criterion — was **not re-run here** (out of
this rung's explicit scope). Given how much §4.1's basin-count/frustration
MAGNITUDES moved (§4.3), the criterion's own "range" term (seed-to-seed
spread, used as the noise floor the gap must clear) will almost certainly
also move, so **whether "no crossover" still holds under the corrected
solver is a genuinely open, unanswered question this rung explicitly
declines to answer** — named here as a concrete, sized follow-on (a full
re-run of `test_experiment_a_crossover_sweep` under the new default,
comparing against `CAN_CROSSOVER_POINT_RESULTS.md` §2's own table), not
attempted. Experiment C (population-mixture) and sharpening (a)
(structured coupling) were likewise not re-checked — also named as
follow-on, not attempted, consistent with the PREREG's own bounded scope.

---

## 5. Backward-compatibility check — every existing Python call site

`grep -rn "mt_mean_field_marginal(\|mt_mean_field_with_h_override(\|mt_relax_to_marginal("`
across the whole repo (`demos/`, `domains/`, `tests/`) found every call
site passing at most 3 positional arguments to
`mt_mean_field_marginal`/`mt_relax_to_marginal` (both had a maximum of 3
parameters — `mt, max_iter, tol` — before this rung) and at most 3
positional arguments to `mt_mean_field_with_h_override` (`mt, concept,
new_h`, out of what was previously a 5-parameter function) — every one of
these is strictly within the position of the new trailing `damping`
parameter, so no existing call site's positional-argument binding changes.
Confirmed by running the affected non-CAN-research test files directly
under the fixed engine: `tests/test_insight_seeking.py` (11 passed),
`tests/test_identity_field.py` (9 passed), `tests/test_self_improvement_
loop.py` (19 passed) — all unmodified, all still green, no assertion
changes needed.

---

## 6. Test suite changes — updated honestly, not left silently stale

Per the task's explicit instruction, two tests in
`tests/test_can_belief_quantization.py` asserted behaviour the fix
directly changes; both were updated to test the CORRECTED, more accurate
solver, with the historical (pre-fix) behaviour preserved and
re-verifiable via the new `damping=1.0` parameter rather than deleted:

1. **`test_relaxation_shows_a_real_cohere_vs_fail_to_cohere_signature`**
   (previously asserted the exact PREREG §3 draw DOES oscillate) — now
   asserts BOTH halves explicitly: `damping=1.0` reproduces the original
   oscillation (gap 5.615746, same-parity control <0.001) AND the new
   default (`damping=0.5`) converges cleanly (gap <1e-6) — the single test
   now IS the before/after live demonstration from §3, permanently
   checked in CI rather than only reported in this document.
2. **`test_flatten_resolution_sweep_reports_cohere_or_abandon`** —
   previously asserted `any(oscillates)` and `any(not oscillates)` (the
   ORIGINAL mixed 50%/66.7% finding). Now asserts `fine_rate == 0.0` and
   `coarse_rate == 0.0` explicitly, with the docstring stating precisely
   why: the coarse/fine oscillation-rate DIFFERENCE the test used to probe
   no longer exists to be measured, because the fix eliminates the
   underlying phenomenon on this sample entirely.

`_relax_with_fields`/`_oscillates` (the shared helpers, also imported
unmodified by `test_can_crossover_point.py`) gained a `damping=0.5`
default parameter each, documented in their own docstrings as the fix and
its `damping=1.0` historical-reproduction path. No other test file's
assertions needed changes (§7 confirms — `test_can_crossover_point.py`,
`test_can_ops.py`, `test_causal_attitude_networks.py`,
`test_can_migration.py` assert only structural sanity — `basin_count >= 1`,
row counts, bounded-value checks — none of which depend on the specific
numeric values the fix changes).

---

## 7. Regression

**Full Rust suite**: `cargo test --release --lib -- --test-threads=1`
(inside `systemd-run --scope --user -p MemoryMax=16G -p MemoryHigh=14G`)
— **774 passed, 0 failed, 4 ignored** (no `can_ops`-specific `#[cfg(test)]`
module exists in the Rust source itself — all CAN-solver testing lives in
the Python test files below, confirmed by `cargo test ... can_ops`
matching 0 tests).

**Coherence probe**: `add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` →
`lst` stays a `list`, `tup` stays a `tuple`, `lst != tup` — confirmed.

**Targeted Python regression, 86/86 passed**, real per-file counts:

```
tests/test_can_belief_quantization.py    11 passed  (2 updated, see S6)
tests/test_can_crossover_point.py         5 passed  (unmodified)
tests/test_can_ops.py                    12 passed  (unmodified)
tests/test_causal_attitude_networks.py   11 passed  (unmodified)
tests/test_can_migration.py               8 passed  (unmodified)
tests/test_insight_seeking.py            11 passed  (unmodified)
tests/test_identity_field.py              9 passed  (unmodified)
tests/test_self_improvement_loop.py      19 passed  (unmodified)
```

**Build**: `scripts/engine_build.sh`, rustup toolchain
(`RUSTFLAGS`/`LD_LIBRARY_PATH` per the task's exact prescribed
environment), inside the same `systemd-run` memory ceiling. Build
provenance recorded via `domains.engine_provenance.record_build()` (the
script's own `python` invocation fails on this box — no `python` binary,
only `python3` — a pre-existing environment quirk unrelated to this rung's
change; worked around by invoking the same provenance call directly via
`python3`, both times, before AND after the fix, so both the before and
after engines are provenance-clean).

---

## 8. What this rung does NOT establish

1. **Whether `CAN_CROSSOVER_POINT_RESULTS.md`'s "no crossover N\*" finding
   still holds under the corrected solver** — not re-run, named as a
   concrete, sized follow-on (§4.4), not attempted here per the task's
   explicit scope boundary against a full re-sweep.
2. **Experiment C (population-mixture) and sharpening (a) (structured
   coupling) from `CAN_CROSSOVER_POINT_RESULTS.md`** — not re-checked,
   also named as follow-on only.
3. **Genuine, scheduling-independent non-convergence was not found
   anywhere this rung looked (§4.1), but this is not a proof that no such
   case exists.** Complete graphs only, β≤4.0, N≤64, one fixed-field/
   all-zero-start initial condition per trial — all inherited limitations
   from the prior two rungs, none newly introduced, none closed by this
   rung.
4. **λ=0.5 is reported at search-synthesis confidence as a
   literature-common default, not independently verified from Murphy,
   Weiss & Jordan (1999)'s own primary text** (both direct fetch attempts
   this session returned unusable binary/PDF-stream content — the same
   failure mode already reported for this paper in
   `CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md` §8). It was not tuned
   against this codebase's own networks — it worked decisively at this
   value on every case tested, so no tuning was attempted or needed.
5. **Async/Gauss-Seidel scheduling remains unbuilt and unassessed** on
   real data — named as a real, literature-standard alternative in the
   PREREG (§2), explicitly not built, with the RNG-infrastructure
   prerequisite named as the reason it wasn't attempted rather than left
   unexplained.
6. **The `dominant_basin_fraction`-based "coarse is unstable, easily
   knocked between alternatives" interpretive gloss**
   (`CAN_BELIEF_QUANTIZATION_RESULTS.md` §3's own reading) **does not
   survive this rung's re-check at N=4/N=8** (§4.3) and should be treated
   as needing fresh measurement, not as still-standing.
7. **Sparse/non-complete graph topologies were not tested** — inherited
   unchanged from both prior rungs' own named limitation.
8. **Whether real human/CAN-attitude-network belief dynamics resemble any
   of this** remains exactly as open as both prior rungs left it — this
   rung is a solver-correctness fix and a re-measurement of the
   SUBSTRATE's own behaviour, not a new claim about cognition.

---

## 9. Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/can-synchronous-update-fix
git log --oneline -1   # this rung's commit, on can-synchronous-update-fix

# Build (rustup toolchain only)
export PATH="/home/matt/.cargo/bin:$PATH"
systemd-run --scope --user -p MemoryMax=16G -p MemoryHigh=14G -- \
  env RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/lib -C link-arg=-lpython3.13" \
  LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/lib:$LD_LIBRARY_PATH" \
  PATH="/home/matt/.cargo/bin:$PATH" \
  bash scripts/engine_build.sh
python3 -c "import sys; sys.path.insert(0,'.'); from domains.engine_provenance import record_build; record_build()"

# Live before/after demonstration (now a permanent regression test)
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_belief_quantization.py -k cohere_vs_fail_to_cohere -q -s

# Eliminated-oscillation demonstration (the pre-registered 24-trial sweep)
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_belief_quantization.py -k flatten_resolution_sweep -q -s

# Targeted regression (86/86)
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_belief_quantization.py tests/test_can_crossover_point.py \
  tests/test_can_ops.py tests/test_causal_attitude_networks.py \
  tests/test_can_migration.py tests/test_insight_seeking.py \
  tests/test_identity_field.py tests/test_self_improvement_loop.py -q

# Full Rust suite
cd runners/dsl && systemd-run --scope --user -p MemoryMax=16G -p MemoryHigh=14G -- \
  env RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/lib -C link-arg=-lpython3.13" \
  LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/lib:$LD_LIBRARY_PATH" \
  PATH="/home/matt/.cargo/bin:$PATH" \
  cargo test --release --lib -- --test-threads=1
```
