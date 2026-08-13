# Does the native discrete-async CAN solver find GOOD solutions, or just A
stable one? — PREREG

**Status: PREREG. Registers the measurement design and GO/NO-GO criteria
BEFORE any measurement is run**, per house discipline. Base `main @
19fdddf` ("Merge mac-fac-a8: epick applicability-gate precompute, closes the
A1-A9 audit, GO"), verified via `git log --oneline -1 main` before
branching. Worktree
`/tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/can-solver-tractability`,
branch `can-solver-tractability`.

**Charter, verbatim, from the project's creator:** *"back to the general
concept of reasoning and solving"* → *"both"* — this rung is the SOLVING
half of a two-rung split (the sibling rung handles deduction/analogy/CAN
wiring at the representational level; this rung stays inside
`can_ops.rs`/`shape_decode.rs`-adjacent algorithmic territory).

**The real question, restated precisely**: `CAN_NATIVE_REIMPLEMENTATION_
RESULTS.md` proved the discrete-asynchronous, Hopfield-style native update
(`can_native_update_3state`/`_2state`, `seeds/can_native_reimplementation.
json`) converges to A stable state with zero non-convergent draws across
every sweep run so far (60+60+80+120 real draws across three separate
rungs). That is a proof/measurement of **convergence**, not of **quality**.
Hopfield networks are textbook-known to carry many spurious local minima
under high loading/frustration — the open question this rung answers is
whether THIS substrate's own real, currently-deployed and currently-tested
networks actually land in that regime, or whether the real graphs this
project builds are structurally mild enough that the distinction is moot in
practice.

---

## 0. What is already established, not re-litigated here

1. `CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md` — ranked five gaps; this rung
   executes items 2-4 (no Bethe/loopy-BP Term; no treewidth discipline; the
   low-rank/shared-generator hypothesis untested). Item 1 (synchronous-update
   fix) and item 5 (don't import the ~7-bin number) are already done,
   confirmed by reading `CAN_SYNCHRONOUS_UPDATE_FIX_RESULTS.md` and the
   "BASE-AS-DIMENSION" section of `CLAUDE.md`.
2. `CAN_CONCEPT_REIMPLEMENTATION_SPIKE.md` + `CAN_NATIVE_REIMPLEMENTATION_
   RESULTS.md` — the discrete-async mechanism REPLACED mean-field for the
   native path; proven convergent (Lyapunov argument for the 2-state case,
   empirically clean for the 3-state deadzone case) on N=8 complete-graph
   draws, later re-confirmed on Bigville's real residents
   (`CAN_CONSUMER_MIGRATION_RESULTS.md` §2.2) and under a live identity-
   feedback loop (`CAN_IDENTITY_FEEDBACK_RESULTS.md` §3, 120 draws × 15
   ticks, 0/60 non-convergent both discrete modes). **None of this arc has
   ever run MULTIPLE random initial conditions on the SAME coupling network
   and compared the QUALITY of where each one lands** — every convergence
   sweep so far draws a FRESH coupling network per trial and starts every
   Concept at `state=0.0` (confirmed by re-reading `_build_draw`,
   `tests/test_can_native_reimplementation.py:62-84` — `"state": 0.0`
   literally hard-coded). This is the precise gap this rung closes.
3. `SHAPE_DECODE_LIBRARY_SCALING_RESULTS.md` — methodology precedent only
   (register predictions, measure real scale, report a clean NO-GO as a
   complete result when the data supports it — this rung follows the same
   discipline, applied to a different mechanism).
4. Real populated CAN data now exists and did not exist when the theory
   doc was written: `seeds/bigville_can_beliefs.json` /
   `worlds/bigville_can_beliefs.py` — 100 real residents
   (`seeds/bigville_cast100.json`), each with a real 5-Concept belief
   network (`trust_mayor`, `claim_credible`, `world_safe`, `self_worth`,
   `debtor_trustworthy`) and 5 real structural `causal_influence` couplings
   (symmetric pairs, per `CAN_NATIVE_REIMPLEMENTATION_RESULTS.md` §7's
   named fix, confirmed live in `worlds/bigville_can_beliefs.py:176-194`).

---

## 1. Measurement 1 (load-bearing) — local-minimum-risk, multi-start,
same network, real numbers

### 1.1 Two conditions, chosen to bracket the real structural range this
project actually builds

**Condition A — frustrated/dense (stress case).** N=16 complete graph,
random-sign `causal_influence` couplings drawn `Uniform(-1,1)` then
quantized to a coarse (3-level) or fine (9-level) vocabulary — the EXACT
construction `tests/test_can_belief_quantization.py::_build_complete_
network` / `tests/test_can_native_reimplementation.py::_build_draw` already
use, extended from N=8 to N=16 (both already tested sizes in this arc's own
prior rungs; N=16 is the largest complete graph any prior CAN rung has
built). Complete graph + random sign = the textbook maximally-frustrated
regime, and per `CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md` §4.2, "exactly
the design point where the literature says mean-field's own approximation
error should be largest" — reused here to stress the DISCRETE mechanism
instead. This is a deliberately adversarial synthetic case, not claimed as
representative of real deployed networks.

**Condition B — real, sparse (deployed case).** Bigville's real 5-Concept,
5-structural-edge per-resident network (`worlds/bigville_can_beliefs.py`),
built from real `bigville_cast100.json` resident params, `discrete_mode=
"3state"`, real `SCENARIO_EVIDENCE` applied. This is what is ACTUALLY
deployed and tested in production code today (`CAN_CONSUMER_MIGRATION_
RESULTS.md` §2, `test_bigville_can_native_migration.py`).

### 1.2 Protocol (identical for both conditions)

For each of `D` independent draws (a draw = one fixed coupling network: a
fresh random-sign N=16 network for condition A; one real resident for
condition B):

1. Build the network once (`can_native_reimplementation.json` rules loaded,
   `discrete_mode` set, real evidence/fields applied per condition).
2. For each of `K` independent starts: re-seed every Concept's `state` to
   an i.i.d. draw from `{-1, 0, +1}` (3-state) or `{-1,+1}` (2-state) — NOT
   the zero-init every prior convergence sweep used — then let the SAME,
   UNMODIFIED, already-proven-convergent native rule run to a fixpoint
   (`run_rules`/`run_rules_scoped`, the mechanism itself is NEVER touched by
   this measurement). Record the converged `state` vector and its
   `mt_frustration_given_state` (closed-form, O(edges), the same reused
   scoring utility every prior rung in this arc already uses to score
   native-produced states).
3. Per draw: record `best_frustration` (min across the K starts),
   `worst_frustration` (max), `spread = worst - best`,
   `n_distinct_final_states` (states clustered by exact-equality — cheap
   and exact for a small discrete-state vector, no distance-tolerance
   fudge needed), and `frac_at_best` (fraction of the K starts landing
   within floating-point equality of `best_frustration`).

`D = 30` draws for condition A (15 coarse + 15 fine), `D = 30` real
residents for condition B (a stratified sample: the 10 lowest- and 10
highest-`resolution_bins` residents plus 10 drawn at fixed-seed random from
the middle, so the sample isn't biased toward either extreme of Bigville's
own resolution-bins trait). `K = 20` starts per draw (matching this arc's
own established `N_RESTARTS`/`N_DRAWS` convention,
`scripts/bigville_can_integration_demo.py:38`,
`tests/test_can_native_reimplementation.py:115`).

### 1.3 Registered predictions, stated before running

- **P1 (condition A, frustrated/dense)**: real, measurable spread across
  starts on a MAJORITY of draws — different initial conditions land on
  DIFFERENT quality stable states, not just different but equally-good
  ones. This is the textbook Hopfield-network expectation under high
  loading (N=16 complete graph, every pair coupled, random sign — far above
  the sparse regime where a Hopfield-style network's basins are known to
  stay well-separated and easy to find).
- **P2 (condition B, real sparse)**: LOW spread — most or all of the 20
  starts per resident converge to the SAME frustration value (allowing for
  the known global sign-flip symmetry when `external_field`/`identity_field`
  are near zero, which the real scenario evidence and identity priors mostly
  break, so even that symmetry is not expected to dominate). This follows
  from the real topology (5 nodes, 5 edges — checked precisely in §3 below,
  expected near-tree, at most one small cycle) being far below the
  frustration-inducing density of condition A.

### 1.4 GO / NO-GO criteria, fixed before measuring

**GO (real local-minimum risk exists, build something)** iff, on condition
A: the MEDIAN `spread` across the 30 draws is **> 0.05 × median
`best_frustration`** (a real, non-trivial relative quality gap between the
best- and worst-found stable state on the SAME network) **AND** the median
`frac_at_best` is **< 0.80** (a meaningful fraction of random starts do NOT
find the best available state) **AND** median `n_distinct_final_states` is
**> 1** (multiple genuinely different final configurations are actually
reached, not just one basin with numerical noise).

**NO-GO (current mechanism adequate as measured)** iff condition A fails
any one of the three GO bars above, OR if condition A shows real risk but
condition B (the actually-deployed real networks) shows negligible risk by
the SAME three bars — in which case the honest, complete finding is "the
mechanism the project actually deploys today is fine; the risk is real but
confined to a denser/more-frustrated regime than anything currently built,"
and the report will say so precisely rather than rounding either finding
away.

**Build gate, registered in advance**: if GO on condition A (regardless of
condition B's own result), build **multi-start-and-pick-best** as a
correctness-preserving wrapper (§5) — NOT a redesign of the update rule
itself, and NOT full loopy-BP in this rung (named, investigated, sized in
§2, but a large lift the task explicitly permits deferring if multi-start
is the right-sized fix for the measured risk). If NO-GO on both conditions,
the complete, valuable result is "adequate as-is," and nothing beyond the
measurement is built, per this whole day's own standing precedent
(`SHAPE_DECODE_LIBRARY_SCALING_RESULTS.md`).

---

## 2. Investigation 2 — Bethe/loopy-BP, concretely, for THIS substrate's
own representation

Not a new literature search (the theory doc's citations — Yedidia/Freeman/
Weiss, Murphy/Weiss/Jordan, Pearl — are re-read, not re-fetched). The
question THIS rung answers: is a loopy-BP update expressible as an ordinary
graph Rule (`match`/`where`/`effects`, reusing `run_rules`/`run_rules_
scoped`, the SAME fixpoint every other native CAN rule already uses), the
same way the discrete-async update already is — or does it need real new
Rust machinery? Concretely checked against:

- What a BP MESSAGE actually is for a pairwise Ising model: `μ_{i→j}(σ_j) =
  Σ_{σ_i} ψ_{ij}(σ_i,σ_j) · φ_i(σ_i) · Π_{k∈N(i)\j} μ_{k→i}(σ_i)`, i.e. a
  message is a per-EDGE, per-DIRECTION, per-VALUE (2 or 3 values, this
  substrate's own native vocabulary) quantity — a fundamentally richer
  object than the discrete update's single per-NODE `state` scalar. Whether
  this can be represented as an `EdgeAttr` (one float per message component,
  i.e. 2-3 attrs per directed edge for a 2-3-state variable) or needs a new
  node type is the concrete design question, answered by inspecting
  `term.rs`'s existing `EdgeAttr`/`Sum`/`Prod` vocabulary against this
  exact shape.
- Whether the existing `Sum{source: Edges(...), value: Times(...)}` pattern
  (`CAN_CONCEPT_REIMPLEMENTATION_SPIKE.md` §3.4's own confirmed precedent,
  `term.rs:11011-11044`) generalizes to a PRODUCT over incoming messages
  EXCLUDING one neighbour (the "leave-one-out" product every BP message
  update needs) — checked against whether a `Prod`-over-`Edges`-with-
  exclusion Term exists or would need one new Term.
- Named directly, not hedged: report whichever way this comes out — "same
  shape as the discrete update, zero new Rust" or "needs N new
  attrs/Terms, sized precisely" — as a concrete finding, not a menu.

No Rust is written for this investigation regardless of what is found —
per the task's explicit priority ordering, item 2 is "investigate... report
precisely," not "build," and the build gate (§1.4) is reserved for
multi-start if GO on the local-minimum measurement.

---

## 3. Measurement 3 — low-rank/shared-generator hypothesis, on REAL
`causal_influence` data

`CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md` §6.4's own precise, falsifiable
condition: does the measured pattern-reuse correspond to a small number of
shared LATENT GENERATORS acting additively across many edges (true low
rank — Hopfield/TAP tractability applies), or merely to many edges
independently landing on the same few numeric values (value-alphabet
compression — it does not)?

**Real data, real test**: build the real 5-edge `true_j` (unquantized) and
`quantized_j` matrices for all 100 real Bigville residents (100 × 5,
`worlds/bigville_can_beliefs.py::true_edge_j`/`quantize_j`, unmodified,
read-only). Compute the SVD of the mean-centered `true_j` matrix; report
the singular-value spectrum and an effective rank (participation ratio
`(Σs)² / Σs²`, a standard, argument-free effective-rank statistic — no new
threshold invented). **Registered prediction**: `true_edge_j`'s own
construction (`base_j` fixed per edge + a nuance term drawn from ONE of
only TWO underlying resident params, `mood_bias` or `w_supergraph`,
clipped and scaled) is a genuine, small number of shared generators by
CONSTRUCTION — the SVD should show effective rank close to the number of
distinct generators actually driving variation (at most 2-3: the constant/
mean component plus the two nuance axes), not close to 5 (full rank). This
is checked, not assumed — the registered prediction could be wrong if the
two nuance keys interact with `base_j`'s sign in a way that decorrelates
edges more than expected.

Separately, and reported honestly as a DIFFERENT question per §6.4's own
warning: whether this real low-rank structure is what the sd-loop's own
codebook-reuse mechanism would actually recognize (a `ShapeSignature`-style
correspondence pattern over `quantized_j` values) is NOT re-tested here —
that would require building a `CausalLinkageShape` codebook over Bigville's
real edges, out of this rung's scope (no compressor is being built). This
measurement answers ONLY whether the real coupling matrix HAS the structural
property the tractability result needs, not whether this project's
existing shape-recognition machinery currently exploits it.

---

## 4. Measurement 4 — treewidth/topology, on REAL constructed graphs

Exact treewidth (not an estimate) for two real, already-built topologies,
computed by brute-force minimum induced-width over ALL elimination
orderings (both graphs are tiny — 5 and 16 nodes — exact brute force is
correct and fast, no heuristic needed, no library dependency assumed):

1. **Bigville's real structural template** (`STRUCTURAL_EDGES`,
   `worlds/bigville_can_beliefs.py:61-67`) — 5 nodes, 5 undirected edges,
   fixed for every resident (only edge WEIGHTS vary by resident, never the
   topology). Registered prediction: treewidth 2 (one triangle —
   `trust_mayor`/`claim_credible`/`debtor_trustworthy` — plus a
   `world_safe`-`self_worth` pendant path off `trust_mayor`; by inspection
   this is a "cactus"-like graph with one 3-cycle, which brute force will
   confirm or correct).
2. **The N=16 complete graph** used in Measurement 1's condition A —
   treewidth N−1 = 15 by definition (only one maximal clique after any
   elimination ordering of a complete graph), included for the explicit
   numeric CONTRAST the theory doc's own §6.2/§6.5 already predicted in
   the abstract, now confirmed on the SAME real network this rung's own
   local-minimum measurement uses, not a separately-cited prior number.

This directly answers the theory doc's own §6.2 finding ("this project's
own tested graphs are complete... the worst possible case... a graph-
construction discipline this project does not currently have") against
data that DID NOT EXIST when that finding was written: **is the real,
currently-deployed Bigville topology ALSO worst-case, or does it turn out
to already be sparse/tractable by construction, without anyone having
designed it that way on purpose?**

---

## 5. What "the smallest real improvement" means here, sized in advance

**If GO (§1.4)**: `multi_start_settle_and_pick_best`, a new function in
`domains/can_native_orchestration.py` (the existing, house-compliant
precedent this whole module already establishes — mechanical composition
of existing primitives, zero decision-over-graph-state in Python). Design,
registered before building:

1. For `K` starts: mechanically draw a random initial `state` per Concept
   (world-adapter-shaped I/O, the SAME class of operation as `bigville_can_
   integration_demo.py::multi_start_basin_count`'s own existing `rng.
   choice([-1.0,1.0])` re-seed loop — already a precedent in this exact
   codebase for exactly this kind of mechanical random re-draw).
2. Call `scoped_settle` (existing, unmodified, `can_native_orchestration.
   py:110-118`) — the SAME already-proven-convergent native rule, never
   touched by this change. Preserves the Lyapunov guarantee exactly, per
   the task's explicit instruction and mirroring `CAN_IDENTITY_FEEDBACK_
   RESULTS.md`'s own care in protecting this exact guarantee: this build
   adds an OUTER selection layer around K independent, individually-
   unmodified runs of the existing mechanism; it does not touch `can_
   native_update_3state`/`_2state`'s own rule body at all.
3. Mint one lightweight graph node per trial (`CanMultiStartCandidate`)
   holding the trial's `frustration` (mechanically copied from `mt_
   frustration_given_state`, a pure computation, not a decision) and its
   per-Concept final `state` values (as attrs, one per Concept id — small,
   K ≤ ~30 trials × N ≤ ~16 concepts, bounded and tiny).
4. The SELECTION — which trial's state gets committed back onto the real
   Concepts — is made by the **`Argmin` Term** (`term.rs:382`, already
   used across ~10 other seeds, e.g. `seeds/grid_navigation.json`,
   `seeds/arc_decompose.json`) over `NodesOfType("CanMultiStartCandidate")`
   scored by `Attr(cand, "frustration")` — a graph-native decision, not a
   Python `if`/`min()`, matching `CLAUDE.md`'s standing rule precisely
   ("any `if`/`else` that reads graph state and decides what to do next is
   a Rule, not Python").
5. Committing the winner's stored state back onto the real Concepts is
   mechanical translation (read the winning node's attrs, `set_attr` them
   onto the Concepts already decided by step 4) — no decision left in
   Python.

Zero new Rust Terms needed if this design holds (checked live while
building, reported honestly either way, per this arc's own standing
practice of naming when a design assumption breaks mid-build, e.g. `CAN_
NATIVE_REIMPLEMENTATION_RESULTS.md` §3's starvation finding).

**If NO-GO**: nothing beyond the four measurement scripts and this pair of
docs is built — a complete, valuable result, matching the explicit
permission in the task and the precedent `SHAPE_DECODE_LIBRARY_SCALING_
RESULTS.md` already set today.

---

## 6. Regression scope

Python only unless the Bethe/BP investigation (§2) or the multi-start build
(§5) is found to need new Rust (not expected for either, per the sizing
above — reported honestly if this changes mid-rung). If Rust is touched:
`cargo test --release --lib -- --test-threads=1` + a coherence probe, per
house discipline. Python: `tests/test_can_native_reimplementation.py`,
`tests/test_can_crossover_point.py`, `tests/test_bigville_can_native_
migration.py`, `tests/test_can_belief_quantization.py`,
`tests/test_causal_attitude_networks.py`, `tests/test_can_ops.py`, plus any
new test file this rung adds, must stay green.

---

## 7. What this document does NOT establish (registered in advance)

1. This is a PREREG — no measurement has been run yet. Every prediction
   above is registered before the corresponding script executes.
2. Condition A (N=16 complete, random-sign) is a deliberately adversarial
   synthetic stress case — even a strong GO there does not, by itself,
   establish that TODAY's real deployed networks are at risk; that is
   exactly why condition B is measured separately and both are reported.
3. The Bethe/BP investigation (§2) is a design analysis, not a build — it
   will not resolve whether Bethe/BP, if built, would actually find better
   solutions on this project's own frustrated networks; that would require
   building and running it, out of this rung's scope per the task.
4. The low-rank measurement (§3) tests Bigville's own template-driven
   construction specifically — it does not establish that ALL `causal_
   influence` networks this project could build would show the same
   structure (a hand-authored or adversarially-constructed network could
   easily be full-rank).
5. The treewidth measurement (§4) is exact for the two SPECIFIC graphs
   measured; it does not establish a general claim about "real networks are
   always sparse" — only about the one real template this project has
   actually shipped.
