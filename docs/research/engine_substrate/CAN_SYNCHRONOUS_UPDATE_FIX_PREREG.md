# Fixing the synchronous/Jacobi update in `mt_mean_field_marginal` — PREREG

**Status: PREREG. Written BEFORE any code change**, per house discipline.
Worktree `/home/matt/ozmadev/ocelot-worktrees/can-synchronous-update-fix`,
branch `can-synchronous-update-fix`, base `main @ cf53784` ("Merge
can-solver-theoretical-limits: theoretical limits of the CAN mean-field
solver, GO"), verified via `git log --oneline -1 main` immediately before
`git worktree add --detach`.

**Charter, this rung**: execute `CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md`'s
own top-ranked, unhedged §9 recommendation — fix the synchronous/Jacobi
update rule in `can_ops.rs::mt_mean_field_marginal` before anything else in
that document's ranked list, because (per that document's own final
paragraph) "every other fix... would inherit the same oscillation pathology
if built on top of it unfixed."

---

## 1. What is being fixed, read from source

`runners/dsl/src/can_ops.rs::mt_mean_field_marginal` (confirmed by direct
read this session, lines ~195-254) iterates

```
σ_i ← tanh(β (Σ_j J_ij σ_j + h_i))
```

**fully synchronously (Jacobi-style)**: every node's `new_state` at
iteration `t+1` is computed entirely from the full `state` map as it stood
at iteration `t` (`new_state.insert(c, new_sigma)` never feeds back into
`state` until the whole sweep completes and `state = new_state` runs,
confirmed at the loop's closing line). `CAN_BELIEF_QUANTIZATION_RESULTS.md`
§3.1 measured this directly producing a **persistent period-2 limit cycle**
on a real network (N=8, β=2.0, fine-resolution coupling, nonzero fixed
external field): `max_iter=400` vs `max_iter=401` (opposite parity) differ
by a large L2 gap (~5.6 in an 8-dimensional σ-space), while `max_iter=400`
vs `max_iter=402` (same parity) differ by <0.001 — a true 2-cycle, not slow
convergence, confirmed via the same-parity control the prior rung itself
pre-registered.

`can_ops.rs::mt_mean_field_with_h_override` (lines ~452-515) is a **second,
independent copy of the identical Jacobi loop** — the "what-if" evaluator
used by predictive insight-seeking. It was not named in
`CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md`'s own read (which cited only
`:227-246`), but it is, read directly, the exact same defect duplicated: a
`new_state` map built from a stale `state` snapshot, swapped in whole at
sweep end. Left unfixed, the what-if evaluator would inherit the identical
oscillation pathology on the same class of frustrated networks while the
main marginal computation does not — an inconsistency the task's own scope
line ("the actual call sites" plural) supports closing in the same rung
rather than leaving a second, unfixed sibling of the bug this rung exists to
fix. **In scope, alongside `mt_mean_field_marginal`/`relax_to_marginal`.**

`can_ops.rs::relax_to_marginal` (lines ~848-861) calls
`mt_mean_field_marginal` internally and writes the result back to the
graph — fixing the marginal function fixes this transitively, no separate
loop to touch.

**Confirmed out of scope, not touched**: `mt_energy`, `mt_frustration_given_state`,
`audit_basin`'s own energy/frustration arithmetic (they consume a finished
`state`/marginal map; they contain no fixed-point iteration of their own —
confirmed by direct read, no coupled bug found). `hebbian_update_J`,
`decay_J`, `decay_h`, `update_identity_dynamics`, `apply_evidence_h`,
`nudge_identity` — one-shot graph-attribute mutations, no iteration, no
synchrony question applies.

---

## 2. Chosen fix, and why, decided against the specific call sites and
existing caller expectations rather than defaulting to the first option

**Chosen: DAMPING (weighted average of old and newly-computed σ), not
asynchronous/Gauss-Seidel scheduling.** Both are real, standard,
literature-documented fixes for exactly this failure mode
(`CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md` §7 item 1, citing Murphy,
Weiss & Jordan 1999; independently re-confirmed this session via
WebSearch — damped BP, `p_new ← (1-δ)·p_old + δ·p_computed`, is described
as routinely used to control loopy-BP oscillation
`[search-synthesis, converging]` — and asynchronous/randomized-order
(Gauss-Seidel-style) scheduling is independently confirmed as the other
standard remedy, with the same search converging on the caveat that
**asynchronous convergence "highly depends on the update schedule"** and
that oblivious (non-randomized) schedules, sync OR async, both still permit
oscillation from contradictory signals `[search-synthesis, converging:
residual-BP / message-scheduling literature]`.

**Reasons damping is the right choice for THIS implementation, checked
against this codebase specifically, not assumed by default:**

1. **No RNG infrastructure exists in the Rust engine for this purpose,
   confirmed by direct check.** `runners/dsl/Cargo.toml`'s full dependency
   list (read in full this session) has no `rand` crate and no other RNG
   dependency anywhere in `runners/dsl/src/*.rs` (`grep -rn "rand::"`
   returns zero hits). The task's own instructions require checking "how
   other parts of this codebase get reproducible randomness" before hand-
   rolling anything — there is no existing pattern to reuse, because there
   is no RNG usage in the Rust engine at all today. Standard practice for
   async/Gauss-Seidel scheduling is *randomized* sweep order specifically
   because a *fixed* (non-random) order is itself a known source of new,
   order-dependent pathologies (a different failure mode, not a strict
   improvement) — confirmed by the same search synthesis above. Adding a
   bespoke RNG source, seeded how, reseeded when, just for this one
   function would be exactly the "inconsistent with existing patterns"
   outcome the task instructions warn against.
2. **Damping is deterministic and order-independent** — it does not
   introduce any new dependency on node iteration order, so it cannot
   introduce a new artifact of that kind. This matters here specifically
   because `mt_mean_field_marginal` iterates `concepts: Vec<NodeID>` in
   whatever order `mt_concepts` (a graph edge walk) happens to return them,
   which is not an order any caller has ever had to reason about before —
   turning that incidental order into a load-bearing convergence factor
   (unrandomized Gauss-Seidel) would be a strictly worse property to add
   than the one being removed.
3. **Damping provably preserves the existing fixed-point set.** At any true
   fixed point, `old_sigma == raw_new_sigma` by definition, so
   `(1-λ)·old + λ·raw_new == old` for ANY `λ ∈ (0,1]` — damping cannot move
   or remove a fixed point, it can only change the trajectory used to reach
   one. This is the direct, mechanical reason requirement 2 below (preserve
   already-correct behaviour) is expected to hold for every case that was
   already genuinely converging, not merely hoped for.
4. **It is the literature's own "cheapest" characterization, and this
   codebase confirms why**: a one-line change to the update formula, no new
   Term, no new dependency, no new call-site contract beyond one additional
   numeric parameter with a backward-compatible default.

**λ = 0.5, reported honestly as a literature-COMMON default, not this
codebase's own tuned value.** Search this session (`[search-synthesis,
converging]`, multiple independent sources) confirms `δ = 0.5` — an equal
weighted average of the old and newly-computed value — is repeatedly
described as the standard/default damping factor in the damped-BP
literature (`p_new(z) = 0.5·p_old(z) + 0.5·p_computed(z)`). The exact value
Murphy, Weiss & Jordan (1999) themselves used could not be independently
re-verified from primary text this session — both a direct `arxiv.org/pdf`
fetch and a Semantic Scholar fetch returned unusable/binary content (the
same failure mode `CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md` §8 point 5
already reported for this exact paper) — so this PREREG reports λ=0.5 at
**search-synthesis confidence as a literature-common default**, not as a
value independently confirmed from the cited paper's own primary text, and
not as a value empirically tuned against this codebase's own networks. This
is registered as the value to test BEFORE code is written, precisely so it
cannot be adjusted after seeing results.

**Implementation shape, registered in advance:**

- `mt_mean_field_marginal(g, mt_id, keys, max_iter, tol, damping: f32)` —
  new trailing parameter. Update step becomes:
  `raw = tanh(β·local); new_sigma = (1.0 - damping)·old_sigma + damping·raw`.
  `damping = 1.0` recovers the OLD update rule byte-for-byte (mathematically
  exact, not approximate: `(1-1.0)·old + 1.0·raw == raw`), which is how the
  live before/after demonstration below reuses ONE binary instead of two —
  though the primary before/after evidence will still be a real two-build
  comparison (old commit vs. this fix), per the task's own emphasis on a
  non-negotiable live demonstration; the `damping=1.0` equivalence is
  reported as a secondary, same-binary cross-check, not a substitute for it.
- `mt_mean_field_with_h_override` gets the identical treatment (same new
  trailing parameter, same formula change), for the reason in §1.
- `relax_to_marginal(g, mt_id, keys, max_iter, tol, damping)` threads the
  parameter through to `mt_mean_field_marginal`.
- Internal Rust call sites that do not expose damping as a caller-facing
  choice (`audit_basin`, `mt_conflicting_nodes`, `mt_pairwise_similarity`,
  all of which call `mt_mean_field_marginal` with hardcoded `(200, 1e-4)`)
  will pass a new `pub const DEFAULT_DAMPING: f32 = 0.5;` — so the fix
  applies by default everywhere these diagnostics are read, not only where
  a caller opts in.
- PyO3 bindings (`mt_mean_field_marginal`, `mt_mean_field_with_h_override`,
  `mt_relax_to_marginal` in `py.rs`) gain `damping=0.5` as a new trailing
  `#[pyo3(signature=...)]` default — every existing Python call site
  (positional or keyword, per the grep done before writing this PREREG)
  passes at most `(mt, max_iter, tol)`, so this is additive and
  backward-compatible at the call-site level; the DEFAULT behaviour changes
  (this is the point of the fix), the call-site CONTRACT does not.

**Explicitly registered as NOT this rung's fix**: asynchronous/Gauss-Seidel
scheduling is not built, not exposed as an option, and not left half-wired.
If a future rung wants it, it needs the RNG-infrastructure decision this
PREREG explicitly declines to make unilaterally.

---

## 3. The exact reproduction scenario for the live demonstration,
registered before code changes

Reusing `CAN_BELIEF_QUANTIZATION_RESULTS.md`'s own exact, already-
pre-registered scenario — not a new draw, so the "before" run is the
literal historical result, not a re-roll:
`tests/test_can_belief_quantization.py::test_relaxation_shows_a_real_cohere_vs_fail_to_cohere_signature`
plus its two supporting helpers `_relax_with_fields`/`_oscillates`:

- N = 8, complete graph.
- Coupling draw: `pair_rng = random.Random(20260813 * 31 + 8)`, true J ~
  `Uniform(-1, 1)` per pair, rounded to FINE resolution
  (`_round_to_vocab(v, 1/8, 8)` — 17-value vocabulary).
- Field draw: `field_rng = random.Random(20260813 * 53 + 8)`, fixed nonzero
  external field per node, `Uniform(-1, 1)`.
- β = 2.0, all-zero start (`state = 0.0` on every Concept).
- Oscillation probe: `max_iter=400` vs `max_iter=401` (opposite parity) —
  expect large gap under the OLD code; same-parity control `400` vs `402` —
  expect near-zero gap under the OLD code (confirms TRUE 2-cycle, not slow
  convergence).

**Registered procedure**:

1. **Before**: build the worktree at its current (unfixed) state, run this
   exact scenario through the real `mt_mean_field_marginal` PyO3 binding,
   confirm the oscillation (`osc == True`, large opposite-parity gap,
   near-zero same-parity gap) — reproducing `CAN_BELIEF_QUANTIZATION_RESULTS.md`
   §3.1's own finding on this exact draw, on THIS commit, before any edit.
2. Apply the code fix (§2).
3. **After**: rebuild, run the IDENTICAL scenario (same seeds, same N, same
   β, same field/coupling draws) through the same PyO3 binding, this time
   with `damping` at its new default (0.5). Registered expectation: the
   opposite-parity gap collapses to near-zero (clean convergence, no
   oscillation) — if it does NOT, that is reported as a genuine, honest
   negative result for this rung (damping insufficient at this λ on this
   network), not adjusted after the fact.
4. Cross-check (secondary, same binary): call the AFTER binary with
   `damping=1.0` explicitly and confirm it reproduces the BEFORE numbers
   bit-for-bit (validates the `damping=1.0 ≡ old code` algebraic claim in
   §2 directly, on the same build).

---

## 4. Registered plan for re-checking prior findings (bounded subset, not a
full re-sweep)

Per the task's explicit scope line, NOT a full re-run of either prior
rung's factorial. Registered subset, chosen because each piece most
directly diagnosed the specific finding named in the task:

1. **The 2-cycle itself** (§3 above) — the primary before/after.
2. **`CAN_BELIEF_QUANTIZATION_RESULTS.md` §3's small-N reversal** (coarse
   showing MORE effective basins / LESS dominant-fraction than fine at
   N=4 and N=8) — re-run `_basin_sweep` at N=4 and N=8 only (not N=16, not
   the full 2×3 factorial) under the corrected solver, compare against the
   ORIGINAL rung's own recorded numbers at those two N. This is the
   specific finding most directly explained by mean-field's own known
   weakness on frustrated graphs (`CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md`
   §4.2) — a synchronous-update artifact could plausibly have inflated
   basin-count/fragmentation readings if some restarts were landing on
   oscillation-corrupted "fixed points" rather than genuine ones, so this
   is the direct check of whether that specific interpretation survives.
3. **`CAN_CROSSOVER_POINT_RESULTS.md`'s V=2 (no-zero-option) cliff** — the
   single cleanest, most load-bearing resolution effect either rung found
   (1.6-2× frustration vs. every V≥3 vocabulary, at every tested N). Re-run
   Experiment B's V∈{2,3,7} cells at N=8 and N=16 only (not the full V∈{2,
   3,4,5,7,9,11}×{8,16,32} grid) under the corrected solver.
4. **The oscillation/abandonment-vs-basin-structure question**
   (`CAN_CROSSOVER_POINT_RESULTS.md` §6, "oscillation tracks N/density far
   more than within-N basin-count degradation") — re-run the oscillation
   probe (`_oscillates`) at the SAME N∈{4,16,32}, same 5 seeds, coarse vs.
   fine, under the corrected solver, and compare oscillation RATES to the
   original rung's own table. This is the finding the task explicitly
   flags as possibly needing re-measurement once the artifact is fixed —
   registered here as the direct, bounded check.

**Registered honest-null clause, matching house style**: if the corrected
solver changes any of items 2-4 above in a way that alters the ORIGINAL
rung's interpretive claim (not merely its raw numbers), that is reported
precisely as a genuine correction to a prior rung's interpretation, per the
task's own explicit instruction and `CLAUDE.md`'s standing discipline on
honest self-correction — not softened, not buried in a footnote.

---

## 5. Registered assessment plan for the abandonment hypothesis (point 4 of
the task)

Two possible outcomes, both named in advance so neither can be selected
after seeing the data:

- **Artifact outcome**: under the corrected (damped) solver, the SAME
  network that oscillated before now converges cleanly to a well-defined
  (possibly still high-frustration) fixed point. If this is what happens
  for the §3 reproduction scenario AND for a broader sample of the
  networks in `CAN_BELIEF_QUANTIZATION_RESULTS.md` §3.1's own 24-trial
  sweep, the honest conclusion is that the persistent 2-cycle was AT LEAST
  PARTLY a numerical-scheduling artifact, not a genuine representational-
  overflow signal — weakening (not necessarily zeroing out) the prior
  rung's "abandonment" interpretation, and this will be reported as exactly
  that: a walk-back of an interpretive claim, not merely a re-measurement.
- **Genuine-overflow-survives outcome**: if some networks in the same
  sample still fail to converge within `max_iter` even under damping
  (oscillation ends, but the damped trajectory settles into a genuinely
  different failure — e.g. converges to a degenerate/undefined state, or
  the max-change never drops below `tol` for a reason other than a clean
  2-cycle), that is evidence of a REAL, scheduling-independent limit
  distinguishable from the old artifact — which would STRENGTHEN the
  abandonment hypothesis by cleaning the signal, per the task's own
  registered alternative.
- **Registered check**: re-run `_flatten_oscillation_study`'s own N∈{6,8,
  10,12}×seeds{1,2,3} grid (24 trials, the prior rung's own pre-committed
  sweep, not the larger 40-trial exploratory one) under the corrected
  solver and report the new oscillation rate for fine vs. coarse,
  compared directly against the original 6/12 (50%) fine / 8/12 (66.7%)
  coarse numbers. This determines which outcome above actually obtains,
  rather than assuming one.

---

## 6. Regression plan, registered

1. `cargo test --release --lib -- --test-threads=1`, full run, inside
   `systemd-run --scope --user -p MemoryMax=16G -p MemoryHigh=14G --`.
2. Coherence probe: `add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` →
   list/tuple stay distinct.
3. `tests/test_can_belief_quantization.py`, `tests/test_can_crossover_point.py`,
   `tests/test_can_ops.py`, `tests/test_causal_attitude_networks.py`,
   `tests/test_can_migration.py` — re-examined, not merely re-run; if the
   corrected solver changes measured numbers these tests assert against,
   the assertions are updated honestly to match the corrected, more-
   accurate solver, and this is stated explicitly in the RESULTS doc rather
   than left as a silent diff.

---

## 7. What this PREREG does NOT decide

1. Whether async/Gauss-Seidel scheduling should EVER be built for this
   engine, and if so, how it should source randomness — named as future
   work, not decided here.
2. The exact λ is registered as 0.5 (search-synthesis-grounded literature
   default) BEFORE seeing results; this PREREG does not claim 0.5 is
   optimal for this codebase's own networks, only that it is a defensible,
   literature-common, non-cherry-picked starting point to test the fix
   against, consistent with the task's own honesty requirement about
   whether a chosen value is principled or tuned.
3. Whether the bounded re-check in §4 will fully settle every open question
   the prior two rungs left honest — it is deliberately scoped to the
   items most directly diagnostic of THIS fix's effect, not a full
   re-validation of either prior rung end to end.
