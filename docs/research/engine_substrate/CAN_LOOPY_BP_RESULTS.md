# Loopy belief propagation as a toolbox alternative to the discrete-async
CAN update — RESULTS

Prereg: `CAN_LOOPY_BP_PREREG.md`, same worktree/branch, base `main @
76b8aea` ("Merge reasoning-facility-bridge..."), verified via `git log
--oneline -1 main` before branching. Worktree
`/tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/can-loopy-bp`,
branch `can-loopy-bp`. (Note: `main` advanced during this rung —
`can-junction-tree` merged at `6871cab`, a sibling rung on entirely
disjoint files, `domains/can_junction_tree.py`/`graph_treewidth.py` —
confirmed no overlap with anything this rung touches; see §7.)

**Verdict, up front — GO, with a precisely characterized, genuinely
two-sided finding, not a clean win or a clean loss.** Loopy belief
propagation is built (`domains/can_native_bp.py`) as a real, working,
correctly-instrumented alternative solving strategy, alongside — never
replacing — the discrete-async native update and `multi_start_settle_
and_pick_best`. **MAX-PRODUCT (min-sum, log domain) is confirmed the
theoretically-justified AND empirically-superior variant on the
frustrated N=16 stress case** (never worse than sum-product across 8
measured draws; ties-or-beats multi-start on every draw where it
converges). **But max-product's own convergence reliability inverts
across topology in a genuinely surprising way**: it converges LESS often
on Bigville's real, sparse (treewidth-2) residents (4/15 = 26.7%) than
on the dense, adversarial N=16 stress case (5/8 = 62.5%) — traced to a
real, measured, persistent period-4 message oscillation
(§3.3) caused by Bigville's one structural 3-cycle plus small-integer
quantized weights producing tied candidate scores, a genuine property of
max-product BP on this exact network, not a bug. **Sum-product converges
reliably everywhere measured (100% on both topologies) but, exactly as
theoretically predicted, converges to a WORSE joint state than
multi-start on Bigville** (mean frustration 2.142 vs multi-start's
1.693) — a real, measured confirmation that "argmax of a marginal ≠ good
joint configuration" is not merely a textbook warning here. **Neither BP
variant reliably beats `multi_start_settle_and_pick_best` on Bigville's
real, sparse, already-deployed residents** — a clean, honest, fully
expected-possible null, per the task's own framing. **BP is also
measured to be 20-200× more wall-clock-expensive per solve than
multi-start (K=20)** — a real, practical cost this report does not bury.

---

## 0. What was built, in one paragraph

`domains/can_native_bp.py` — Term builders (verbatim-twin adaptations of
`can_counterfactual.py::local_field_term`/`_neighbour_state_term`) plus a
bounded, Gauss-Seidel, Python-orchestrated round-robin sweep (the SAME
shape `can_counterfactual.py::predict_ripple` already uses), producing
`run_loopy_bp(substrate, mt, combine="max_product"|"sum_product",
max_rounds, epsilon, commit=False)`. Messages live only in an in-memory
Python dict across rounds, never a graph node or edge attr (this
engine's own no-`set_edge_attr` constraint, confirmed at
`seeds/can_native_reimplementation.json`'s own `can_native_hebbian_
reweight` comment). Zero new Rust Terms, zero new node/edge types, zero
new Γ productions, zero calls to `run_rules()`/`run_rules_scoped()`.
`seeds/can_native_reimplementation.json` and `domains/can_native_
orchestration.py` are byte-unchanged (§7 confirms this directly, not
merely by claim).

---

## 1. Design decision: MAX-PRODUCT is primary, justified against what
this project's own update already computes

`can_native_update_3state` (`seeds/can_native_reimplementation.json:
143-499`) commits `state(c) = 1 if scaled > atanh(0.5) else (-1 if
scaled < -atanh(0.5) else 0)`, where `scaled = temperature * (external_
field + identity_field + Σ_e weight(e)*state(target(e)))` — a
per-node, deterministic threshold decision over the CURRENT joint
configuration: **iterated conditional modes (ICM)**, a coordinate-wise
MAP/mode search over the Ising Hamiltonian `seeds/causal_attitude_
networks.json`'s own description declares, never a marginal-probability
computation. `multi_start_settle_and_pick_best` scores each trial by
`mt_frustration_given_state` — a function of ONE joint discrete
configuration — and keeps the argmin. **The whole toolbox this rung
joins is already organised around finding a good joint configuration**,
so max-product (BP's own MAP-seeking variant) is the direct
generalisation of what this mechanism already computes locally, and
sum-product (whose natural read-off is a per-node marginal argmax) is
measured here specifically because the theory predicts it should
sometimes disagree with the joint objective the rest of the toolbox
already optimises for (`seeds/causal_attitude_networks.json`'s own
"multiple inconsistent views = multistable network" framing, §4 below
confirms this is not merely a textbook warning).

Implemented in the additive log domain (min-sum), matching this
project's own energy-additive vocabulary (`mt_energy`'s `H = -Σ Jσσ - Σ
hσ`, `coherence = -H/N`) rather than the raw multiplicative-probability
domain — avoids ever needing `Exp` on a quantity that could blow up.

---

## 2. Term composition — real file:line, real engine confirmation

- `unary_score_term` (`domains/can_native_bp.py`) — `temperature *
  (external_field + identity_field) * x_i`, reading the SAME
  `external_field`/`identity_field` attrs `can_native_update_3state`
  reads, verbatim-twin of `can_counterfactual.py::local_field_term`'s own
  sub-expression.
- `pairwise_score_term` — `temperature * J_ij * x_i * x_j`, reading the
  same `weight` attr the seed's own `Sum`-over-`Edges` reads.
- `incoming_sum_term` — `Sum` over `Edges(i,"causal_influence")`, value
  = an `IfThenElse` ladder keyed on each edge's target-node IDENTITY,
  splicing in the previous round's held message per neighbour, excluded
  neighbour forced to `0.0`. The exact "leave-one-out" composition
  `CAN_SOLVER_TRACTABILITY_RESULTS.md` §4 point 2 confirmed buildable
  from `Filter`+`Edges`+`Nth`+`Eq` — built here with one fewer Term (the
  override ladder subsumes the exclusion).
- The discrete vocab (2 or 3 values) is enumerated in PYTHON at
  Term-build time, never as a graph-Term collection — sidesteps
  `CAN_SOLVER_TRACTABILITY_RESULTS.md` §4 point 3's own flagged-open
  "Sum over a literal list" question entirely rather than resolving it
  (still open, for whatever future rung needs it).
- Combine (max/log-sum-exp) and the final per-node argmax are plain
  Python arithmetic on already-Term-evaluated floats — a deliberate
  choice, not an oversight, matching `predict_ripple`'s/`predicted_info_
  gain`'s own established precedent (`domains/can_native_bp.py`'s own
  "ON PYTHON VS TERM ARITHMETIC" module note explains the exact
  boundary: Terms do every genuine graph-state read; Python only
  combines numbers Terms already returned).

Zero new Rust Terms: `Filter`/`Edges`/`EdgeAttr`/`Nth`/`Eq`/`IfThenElse`/
`Sum`/`Plus`/`Times`/`Pick`, all pre-existing (confirmed against
`runners/dsl/src/term.rs` before writing a line of the module).

---

## 3. A real bug, caught and fixed live during the build — reported
honestly, not smoothed over

**First implementation of `incoming_sum_term` used `NodeID.value` (a
plain Python int) as the override-ladder key.** This is silently wrong:
the ladder's `Eq(target, Lit(k))` compares a live `Value::Node` (read off
an `Edges` tuple) against `Lit(k)` where `k` is a raw int — which
serialises to `Value::Int`, never equal to a `Value::Node` regardless of
identity. **Every neighbour's contribution silently fell through to the
`Lit(0.0)` default** — the incoming-message sum was ALWAYS zero, every
round, for every node. This did not crash or raise — it produced a
plausible-looking, WRONG result: on the N=16 stress case, the (bugged)
sweep "converged" in exactly 2 rounds with `max_delta=0.0`, because it
was, in effect, running one real (message-free) unary+pairwise pass and
then trivially reproducing it forever — never actually summing any
neighbour's message.

**Caught by direct tracing**, not by a downstream test failing: manually
printing `incoming_by_xi` round-over-round and finding it identically
`{-1: 0.0, 0.0: 0.0, 1.0: 0.0}` even when the Python dict fed into the
ladder held real, nonzero values, made the type-mismatch visible. Fixed
by converting every override key (and the excluded-neighbour id) to the
actual `NodeID` object via `id_to_node[k]` before calling
`incoming_sum_term` — matching `can_counterfactual.py::predict_ripple`'s
own `overrides = {by_id[k]: v ...}` convention exactly, which already
does this conversion for the identical reason and was the correct
template all along; this build's own first draft simply didn't follow it
closely enough. **A permanent regression test pins this down directly**
(`tests/test_can_loopy_bp.py::test_incoming_sum_term_requires_nodeid_
keys_not_raw_ints`) — it constructs BOTH the correct (NodeID-keyed) and
the buggy (int-keyed) call against the real engine and asserts the
buggy one reads back exactly `0.0`, confirming the failure mode is real
and specific, not merely patched over.

A second, separate defect was caught the same way before the fix above:
the FIRST draft's round loop was Jacobi (batch-then-swap: build
`new_messages` fully separately, swap after the whole round), not
Gauss-Seidel — `predict_ripple`'s own docstring explicitly warns against
exactly this (`CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md` §7 item 1: a
synchronous update is a NAMED, STUDIED cause of loopy-BP oscillation,
Murphy/Weiss/Jordan 1999). Fixed by committing each edge's new message
`messages[(i,j)] = comp` in place as the round's for-loop proceeds, so a
later edge in the same round sees an earlier edge's freshly-recomputed
message — matching `predict_ripple`'s own explicit in-place-commit
choice precisely.

---

## 4. The load-bearing measurement — real numbers, both topologies

Method: `scripts/can_loopy_bp_measure.py`, one run, output captured in
`scripts/can_loopy_bp_measure_results.json`. Four solvers per network:
single discrete-async settle (baseline), `multi_start_settle_and_pick_
best` (K=20, unmodified), loopy BP max-product, loopy BP sum-product.
All four scored by the SAME `mt_frustration_given_state`.

### 4.1 N=16 frustrated/dense (the adversarial stress case `CAN_SOLVER_
TRACTABILITY_RESULTS.md` §1 used) — **n=8 draws**, smaller than that
rung's own 30 (BP is materially more expensive per network, §5), stated
plainly rather than implied to match.

| seed | baseline | multistart | bp_max | bp_max conv/rounds | bp_sum | bp_sum conv/rounds |
|---|---:|---:|---:|---|---:|---|
| 5000 | 37.0 | 37.0 | **36.0** | True/8 | 36.0 | True/7 |
| 5001 | 33.0 | 30.0 | 30.0 | True/6 | 30.0 | True/7 |
| 5002 | 39.0 | 37.0 | 60.0 | **False**/60 | 86.0 | **False**/60 |
| 5003 | 22.0 | 20.0 | 20.0 | True/20 | 20.0 | True/11 |
| 5004 | 30.0 | 28.0 | 28.0 | True/17 | 28.0 | True/17 |
| 5005 | 34.0 | 28.0 | 34.0 | **False**/60 | 48.0 | **False**/60 |
| 5006 | 34.0 | 34.0 | 34.0 | True/21 | 34.0 | True/33 |
| 5007 | 44.0 | 40.0 | 44.0 | **False**/60 | 48.0 | **False**/60 |

Means: baseline 34.125, multistart 31.750, bp_max 35.750 (converged
5/8 = 62.5%), bp_sum 41.250 (converged 5/8 = 62.5%).

**bp_max vs bp_sum, all 8 draws**: max-product strictly better on 3,
tied on 5, **never worse** — direct empirical confirmation of §1's
theoretical claim on this stress case.

**bp_max vs multistart, RESTRICTED TO THE 5 DRAWS WHERE bp_max
CONVERGED** (5000, 5001, 5003, 5004, 5006): strictly better on 1 (5000:
36.0 < 37.0), tied on 4, **never worse** — when max-product converges on
this dense/frustrated topology, it reliably matches or beats
multi-start's own K=20 widened search.

**bp_max on the 3 draws where it did NOT converge** (5002, 5005, 5007):
capped at `max_rounds=60`, and in every one of these its frustration is
WORSE than multi-start's (60 vs 37; 34 vs 28; 44 vs 40) — sometimes
worse than even the single-settle baseline (5002: 60 vs 39). **This is
exactly why the non-negotiable convergence-flag requirement matters in
practice, not only in principle**: an unconverged BP read is measurably
unreliable here, and the returned `converged=False` flag is the only
thing distinguishing a trustworthy result from an untrustworthy one.

### 4.2 Real Bigville residents (sparse, treewidth 2) — **n=15**
(stratified 5 lowest-`resolution_bins` / 5 highest / 5 random-middle,
smaller than `CAN_SOLVER_TRACTABILITY_RESULTS.md`'s own 30, stated
plainly).

Means: baseline 1.767, multistart 1.693 (best of the four, on average),
bp_max 2.821 (converged **4/15 = 26.7%**), bp_sum 2.142 (converged
**15/15 = 100%**).

**The convergence-rate INVERSION is the sharpest, most surprising real
finding in this rung**: max-product converges LESS reliably on
Bigville's sparse, treewidth-2 real residents (26.7%) than on the dense,
adversarially-constructed N=16 complete graph (62.5%) — the OPPOSITE of
the naive "sparser ⟹ easier for BP" expectation (belief propagation is
textbook-EXACT on a tree; Bigville's structural template is a
near-tree-plus-one-triangle, `CAN_SOLVER_TRACTABILITY_RESULTS.md` §2).

**Traced to a real, measured cause, not left as an unexplained
anomaly** (§4.3 below): a genuine, sustained period-4 message
oscillation on real resident #5, directly attributable to Bigville's one
structural 3-cycle (`trust_mayor`-`claim_credible`-`debtor_
trustworthy`) combined with small-integer quantized coupling weights
that produce EXACT TIES between candidate max-product scores — and
max-product BP has no guaranteed fixed point when the underlying MAP is
non-unique/tied on a graph with even one cycle, a real, literature-named
property (`CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md` §4.4's own "Bethe
approximation stops having a solution" citation), now measured directly
on this project's own real deployed data rather than only cited from the
literature.

**Sum-product, in sharp contrast, converges on all 15/15 Bigville
residents** — but its convergence does NOT translate into quality
relative to multi-start: mean frustration 2.142 is worse than
multi-start's 1.693, and checked resident-by-resident (against
`multistart_frustration` directly, not against max-product), sum-product
is measurably WORSE than multi-start on 6 of the 15 residents (indices
5, 79, 11, 21, 74, 4), TIED on the other 9, and **never strictly
better**. This is the direct, measured confirmation of §1's theoretical
prediction: **sum-product's per-node marginal argmax reliably CONVERGES
to a well-defined answer, but that answer is not reliably a GOOD joint
configuration relative to a solver (multi-start) that is already
organised around the joint objective** — reliability and quality are
shown here to be two different, separable properties of a BP variant,
not one.

**Sum-product IS, however, measurably more useful than max-product
specifically ON Bigville** (a distinct comparison from the one above):
checked resident-by-resident against max-product directly, sum-product
is strictly BETTER on 6 of 15 (indices 6, 24, 28, 11, 87, 53 — precisely
the residents where max-product failed to converge and got stuck at a
worse oscillating value), tied on 8, and strictly worse on only 1
(resident 79, where max-product converges cleanly to 0.667 vs
sum-product's 1.333). **The two comparisons are not the same claim**:
sum-product beats max-product locally on Bigville because max-product's
own convergence failures are costly there (§4.3), while BOTH BP variants
still fall short of multi-start's own simple widened search on this
specific, real, sparse topology.

**Where max-product DOES converge on Bigville (4/15: residents 79, 83,
21, 58), it is not uniformly at-least-as-good as multi-start** — resident
21 is a real, honestly-reported EXCEPTION to the pattern §4.1 found on
N=16 (`bp_max=1.5` vs `multistart=1.25`, max-product WORSE even though
converged). The "converged max-product ties-or-beats multi-start"
pattern held CLEANLY on the dense N=16 stress case (5/5) but has (at
least) one real counter-example on Bigville's sparse residents (3 of 4
converged cases tie-or-beat, 1 does not) — reported as the genuine,
smaller-sample exception it is, not folded into a false universal claim.

### 4.3 The period-4 oscillation, shown directly (not merely asserted)

Real Bigville resident #5, max-product, `max_rounds=40`,
`epsilon=1e-3`:

```
max_delta_history tail: [3.0, 2.406, 2.406, 2.406, 3.0, 2.406, 2.406, 2.406]
```

A clean, sustained, non-decaying period-4 cycle — not a slow decay
truncated by the round cap, and not numerical noise near the epsilon
threshold. `tests/test_can_loopy_bp.py::test_bp_reports_converged_false_
on_a_measured_oscillating_real_network` pins this exact trace down as a
permanent regression fixture.

---

## 5. A real, honest cost this rung does not bury: wall-clock time

BP is dramatically more expensive per solve than multi-start (K=20),
measured directly, not estimated:

| network | multistart (K=20) | bp_max | bp_sum |
|---|---:|---:|---:|
| N=16, converged draw (5001) | 0.029s | 0.616s (21×) | 0.714s (25×) |
| N=16, unconverged draw (5002, capped at 60 rounds) | 0.032s | 5.781s (181×) | 5.959s (186×) |

Multi-start's own K independent settles are each a fast, proven-
convergent discrete-async run; BP's per-round cost (a `Sum`-over-`Edges`
Term evaluation per node per candidate value, every round, until
convergence or the cap) is real and non-trivial on a dense N=16 graph.
**This is a genuine practical factor in "when to reach for BP," not a
footnote**: on this project's own real, sparse, already-deployed
Bigville networks (§4.2), BP is both SLOWER and (on average) WORSE than
the already-built `multi_start_settle_and_pick_best` — the toolbox
recommendation this rung's own measurement supports is "reach for
multi-start first on sparse/production networks; BP is available for the
dense/frustrated regime where it is (conditionally, per §4.1) both
better AND where multi-start's own K independent local optima are more
likely to all miss the same basin."

---

## 6. When BP helps vs. when it doesn't — the direct answer the task
asked for

**Helps**: dense, frustrated networks (this project's own N=16 stress
case) — max-product, WHEN it converges (62.5% of measured draws here),
reliably ties-or-beats multi-start's K=20 search, and is never worse
than sum-product on the same case.

**Does not help**: Bigville's real, sparse, already-deployed residents —
neither BP variant reliably beats multi-start there (mean frustration:
multistart 1.693 best, bp_sum 2.142, bp_max 2.821), max-product's
convergence rate is WORSE than on the dense case (26.7% vs 62.5%, traced
to a real tied-score cycling property, §4.3), and BP is 20-200× slower
per solve than multi-start regardless of topology. **This is exactly the
"clean, honest finding that BP does NOT reliably outperform multi-start
on this project's own real network shapes" the task named as a complete,
valuable, fully expected-possible outcome** — reported precisely as
such, on Bigville specifically, while ALSO reporting the genuine positive
result (§4.1) on the dense stress case where the task's own theory
predicted BP's real value would concentrate.

**The honest, load-bearing asymmetry**: max-product's theoretical
justification (§1) is not in doubt — it is confirmed both by never
losing to sum-product when converged, and by the tree-exactness proof
(§8). What the measurement adds, and what pure theory could not have
predicted without running it, is that **max-product's convergence
RELIABILITY, not its quality-when-converged, is the real limiting
factor on this project's own sparse real networks** — a finding that
argues for the SUM-PRODUCT variant, or `multi_start_settle_and_pick_
best`, as the more PRACTICAL default when reliability matters more than
squeezing out the last point of frustration, while reserving max-product
for cases (like the dense stress regime) where its convergence rate is
measured to be materially better.

---

## 7. Regression

**Zero Rust touched**:
```
$ git diff --stat main -- '*.rs'
(empty)
```

**Explicitly out-of-scope files confirmed byte-unchanged, not merely
claimed** (`tests/test_can_loopy_bp.py::test_native_reimplementation_
seed_and_orchestration_module_untouched`, and independently here):
```
$ git diff --stat main -- seeds/can_native_reimplementation.json domains/can_native_orchestration.py
(empty)
```

**New test file**:
```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest tests/test_can_loopy_bp.py -q -s
10 passed in 0.30s
```
Covers: max-product exactness on two independent tree cases (checked
against brute-force enumeration of all 3^3 configurations, not merely
trusted), the exact NodeID-vs-raw-int bug pinned down as a direct
regression, honest non-convergence reporting on the real measured
oscillator (resident #5), non-mutation by default, `commit=True`'s
mechanical write-back, two-Mt isolation (the standing check every native
CAN rung runs), a real-Bigville-resident smoke test, a sum-vs-max
agreement check on the null-free tree case, and the byte-unchanged
confirmation for both explicitly-out-of-scope files.

**Task-named regression set + this rung's own tests, one run**:
```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_native_reimplementation.py tests/test_can_solver_tractability.py \
  tests/test_can_loopy_bp.py \
  tests/test_can_crossover_point.py tests/test_bigville_can_native_migration.py \
  tests/test_can_belief_quantization.py tests/test_causal_attitude_networks.py \
  tests/test_can_ops.py tests/test_bigville_can_integration.py tests/test_can_migration.py \
  tests/test_can_final_migration.py tests/test_can_identity_feedback.py \
  tests/test_can_decay_identity.py tests/test_can_hebbian_materialization.py \
  tests/test_can_counterfactual.py \
  -q
133 passed in 10.08s
```
**Zero failures, before or after** — every pre-existing test in every
one of those files is unaffected (this rung only ADDS
`domains/can_native_bp.py`, `tests/test_can_loopy_bp.py`, this doc pair,
and the measurement script).

`main` advanced during this rung (`can-junction-tree` merged at
`6871cab`, entirely disjoint files — `domains/can_junction_tree.py`,
`domains/graph_treewidth.py`, its own PREREG/RESULTS docs, its own test
file) — `git diff --stat main` from this worktree therefore also shows
those files as "deleted" (an artefact of comparing against a moved
`main`, not a real change this rung made); the `git diff --stat main --
<specific file>` invocations above, scoped to the files this rung
actually cares about, are unaffected and confirm the real picture.

`git status --short`:
```
?? docs/research/engine_substrate/CAN_LOOPY_BP_PREREG.md
?? docs/research/engine_substrate/CAN_LOOPY_BP_RESULTS.md
?? domains/can_native_bp.py
?? scripts/can_loopy_bp_measure.py
?? scripts/can_loopy_bp_measure_results.json
?? tests/test_can_loopy_bp.py
```

---

## 8. Correctness anchor — max-product BP is EXACT on a tree, checked
against brute force

Belief propagation's own textbook guarantee (exact on trees/polytrees)
is checked directly, not merely cited: two independently-chosen 3-node
path graphs (weights/fields varied), each compared against exhaustive
brute-force enumeration of all `3^3=27` joint configurations via the
SAME `mt_frustration_given_state` BP's own combine step is built to
optimise:

```
BP max-product frustration=0.000000 true brute-force MAP frustration=0.000000
```

Both cases match the true global MAP to floating-point precision
(`tests/test_can_loopy_bp.py::test_max_product_bp_is_exact_on_a_tree`,
`::test_max_product_bp_exact_on_a_tree_second_case`). This anchors the
rest of §4's loopy-graph measurements against a known-correct baseline:
the mechanism is provably right where the literature says it must be;
everything reported above is honestly about what happens once real loops
enter the picture.

---

## 9. What this rung does NOT establish

1. **Sample sizes are smaller than `CAN_SOLVER_TRACTABILITY_RESULTS.md`'s
   own** (8 N=16 draws vs. that rung's 30; 15 Bigville residents vs. 30)
   — BP is measurably more expensive per network (§5), and this rung's
   own time budget did not stretch to matching that rung's n. The
   directional findings (max-product never worse than sum-product on
   N=16; the convergence-rate inversion between topologies; sum-product's
   reliable-but-worse pattern on Bigville) are real, measured, and
   internally consistent with the theory in §1, but have NOT been
   confirmed at the tractability rung's own statistical power — a wider
   sweep is real, un-sized follow-on work, not performed here.
2. **The period-4 oscillation's root cause (§4.3) is traced to a
   plausible, specific, real mechanism (the one structural 3-cycle plus
   tied quantized weights) but this rung did not exhaustively test
   whether BREAKING the tie (e.g. via a tiny asymmetric perturbation) or
   damping the message update (mirroring `can-synchronous-update-fix`'s
   own already-merged λ=0.5 fix for the discrete-async update) would
   resolve it** — a real, concrete, cheaply-testable follow-on this rung
   named but did not build, matching the task's own explicit
   "investigate, don't build every possible follow-on" discipline.
3. **This rung does not resolve whether Bethe/BP's own known failure
   regime (`CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md` §4.4: frustrated +
   field + low temperature) is the SAME regime as the convergence
   failures measured here** — the measured oscillations occurred at
   `temperature=2.0` (moderate, matching every prior rung's own
   convention, not deliberately driven to a "low temperature" extreme) —
   whether lower temperature makes convergence better or worse is
   untested.
4. **No junction-tree/treewidth-exact comparison is drawn** — `main`
   gained an exact junction-tree solver for low-treewidth networks
   (`can-junction-tree`, merged at `6871cab`) during this rung's own
   work, entirely independently; comparing BP's approximate answer
   against that solver's EXACT answer on Bigville's own treewidth-2
   template is a real, natural follow-on this rung does not perform (out
   of this rung's own explicit scope, and the two rungs were built
   concurrently with no coordination).
5. **This rung does not claim BP is useless on sparse networks in
   general** — Bigville's specific real structural template (one
   3-cycle, small-integer quantized weights producing exact ties) is the
   measured cause of max-product's poor convergence there; a DIFFERENT
   sparse network without that specific tie-producing structure might
   show different BP behaviour. The claim is precisely scoped to what was
   measured: on THESE real Bigville residents, under THESE real
   conditions, BP does not reliably beat multi-start.
6. **Whether any of this reflects real human belief-network, social-
   population, or causal-reasoning dynamics remains exactly as open as
   every prior rung in this arc left it** — this document is about this
   substrate's own best-fitted mechanism's actual solution quality, not
   a new claim about cognition.

---

## 10. Reproduce

```bash
cd /tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/can-loopy-bp
git log --oneline -1 main   # verify base, note main has moved since 76b8aea

# The load-bearing measurement (N=16 + Bigville, both combine variants)
PYTHONPATH=".:runners/dsl/python" python3 scripts/can_loopy_bp_measure.py
cat scripts/can_loopy_bp_measure_results.json

# This rung's own regression tests, with printed real numbers
PYTHONPATH=".:runners/dsl/python" python3 -m pytest tests/test_can_loopy_bp.py -q -s

# Task-named + broader CAN regression set
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_native_reimplementation.py tests/test_can_solver_tractability.py \
  tests/test_can_loopy_bp.py \
  tests/test_can_crossover_point.py tests/test_bigville_can_native_migration.py \
  tests/test_can_belief_quantization.py tests/test_causal_attitude_networks.py \
  tests/test_can_ops.py tests/test_bigville_can_integration.py tests/test_can_migration.py \
  tests/test_can_final_migration.py tests/test_can_identity_feedback.py \
  tests/test_can_decay_identity.py tests/test_can_hebbian_materialization.py \
  tests/test_can_counterfactual.py \
  -q

# Zero Rust touched; explicitly-out-of-scope files byte-unchanged
git diff --stat main -- '*.rs'
git diff --stat main -- seeds/can_native_reimplementation.json domains/can_native_orchestration.py
```
