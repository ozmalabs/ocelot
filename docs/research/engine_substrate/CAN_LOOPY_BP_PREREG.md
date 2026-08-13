# Loopy belief propagation as a toolbox alternative to the discrete-async
CAN update — PREREG

**Charter**: `CAN_SOLVER_TRACTABILITY_RESULTS.md` measured a real,
structural local-minimum risk in the discrete-async native update
(median relative spread 25.9% on a frustrated N=16 stress case; 46.7% of
real Bigville residents show nonzero spread too) and built
`multi_start_settle_and_pick_best` as the smallest correctness-preserving
fix. That same document's own §4 investigated Bethe/loopy-BP concretely
against this project's real Term vocabulary and found it **structurally
buildable as ordinary Term composition (`Prod`/`Filter`/`Sum`/`EdgeAttr`,
zero new Rust Terms)**, sized at "roughly the complexity class of
`can_counterfactual.py`'s own multi-step Term assembly," and deliberately
NOT built in that rung (task said: investigate, don't build). This rung
builds it — as a genuinely different, complementary TOOL alongside the
discrete-async update and multi-start, not a replacement for either.

Base: `main @ 76b8aea` ("Merge reasoning-facility-bridge..."), verified
via `git log --oneline -1 main` before branching. Worktree
`/tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/can-loopy-bp`,
branch `can-loopy-bp`. Collision check: `git worktree list` at start
showed five sibling worktrees touching CAN/reasoning work
(`can-synchronous-update-fix`, already merged into `main` at `b9f4429`;
`can-solver-tractability`/`can-solver-theoretical-limits`, both at `main`
tip, no divergent commits; three unrelated `mac-fac-*`/`reasoning-bridge`/
`editop-applicability-gate`/`shape-decode-scaling` worktrees). No live
collision on `seeds/can_native_reimplementation.json` or
`domains/can_native_orchestration.py` — this rung never touches either
file (confirmed by design below, not merely by promise).

---

## 1. Design decision 1 — messages are Python-orchestrated, not installed
graph Rules

The task's own instruction: "design and build message-passing as
ordinary graph rules... Express the excluded-neighbour product via the
SAME iteration/aggregation Term shapes `can_counterfactual.py` already
uses for its own bounded multi-round sweep — reuse that orchestration
pattern, don't invent a new one."

Read literally, "ordinary graph rules" and "reuse `can_counterfactual.
py`'s orchestration pattern" name two different things: the FORMULA
shape (Term composition using only existing Terms — `Sum`/`Edges`/
`EdgeAttr`/`Nth`/`Attr`/`IfThenElse`/`Plus`/`Times`, the "ordinary graph
Rule" vocabulary `CAN_SOLVER_TRACTABILITY_RESULTS.md` §4 confirmed
composable) versus the EXECUTION shape (installed `Rule{match, where,
effects}` objects fired inside `run_rules()`, versus Python-orchestrated
`Term.evaluate()` calls in a bounded round-robin, the shape
`can_counterfactual.py::predict_ripple` already uses). This PREREG
registers, before writing the measurement script, that this rung takes
the SECOND reading: the message-passing FORMULA is built from ordinary
Term shapes; the ROUND-ROBIN SWEEP itself is Python orchestration,
exactly mirroring `predict_ripple`, not installed graph Rules.

**Why, concretely, not installed Rules**: `seeds/can_native_
reimplementation.json`'s own `can_native_hebbian_reweight` rule comment
states a real, load-bearing engine fact — **there is no `set_edge_attr`
rule effect; edges cannot carry live-updated attrs**. A BP message is a
per-DIRECTED-EDGE quantity that must be recomputed and re-read every
round. Built as installed Rules, this would force minting one
`BpMessage` NODE per directed edge (mirroring how the Hebbian arc had to
mint a `Coactivation` node just to hold two mutable evidence counters)
plus new Γ productions for that bookkeeping — real, avoidable weight for
a quantity (BP messages) that is recomputed every round and never needs
to outlive one bounded call. Python holding messages in an in-memory
dict across rounds — never a graph node/edge attr, never persisted
mid-sweep — is the shape `predict_ripple`'s own `hyp: dict[int,float]`
already establishes as legitimate, house-compliant orchestration
(`CLAUDE.md`'s own "world adapter... orchestrates WHICH node's term to
evaluate next and WHEN to stop" allowance, and `can_counterfactual.py`'s
own module docstring names this precisely).

**Registered before building**: zero new node types, zero new edge
types, zero new Γ productions, zero calls to `run_rules()`/
`run_rules_scoped()` anywhere in this module. If the measurement below
finds this insufficient, that will be reported as a registered surprise,
not silently patched around.

---

## 2. Design decision 2 — MAX-PRODUCT (min-sum, additive log domain) is
the PRIMARY variant; SUM-PRODUCT (log-sum-exp) is built as the measured
comparison

**The concrete question, asked directly**: does `can_native_update_
3state`'s own threshold decision (`seeds/can_native_reimplementation.
json:143-499`) compute a MARGINAL PROBABILITY, or a MODE/MAP DECISION?
Read directly from the rule: for each Concept `c`, it computes `scaled =
temperature * (external_field + identity_field + Sum_e weight(e) *
state(target(e)))`, then commits `state(c) = 1 if scaled > atanh(0.5)
else (-1 if scaled < -atanh(0.5) else 0)` — **a per-node, deterministic,
zero-temperature-limit THRESHOLD DECISION over the CURRENT joint
configuration**, not a sample from, or an expectation under, a Boltzmann
distribution. This is, precisely, **iterated conditional modes (ICM)**:
each node greedily sets itself to its own locally-best response holding
every neighbour's CURRENTLY COMMITTED state fixed — a coordinate-wise
MAP/mode search over the SAME Ising Hamiltonian `seeds/causal_attitude_
networks.json`'s own description declares (`H = -Σ J_ij σ_i σ_j - Σ h_i
σ_i`), not a marginal-inference procedure.

`multi_start_settle_and_pick_best` (`CAN_SOLVER_TRACTABILITY_RESULTS.md`
§5) confirms this reading structurally: it scores each of its K trials
by `mt_frustration_given_state` — a function of a single JOINT DISCRETE
CONFIGURATION, never a distribution — and keeps the argmin. **The whole
toolbox this rung joins is already organised around finding a good JOINT
CONFIGURATION (a MAP-shaped goal), not around estimating a marginal
distribution.**

**Consequence**: the loopy-BP variant that composes coherently with what
this project already computes and already measures (frustration of a
joint state) is **MAX-PRODUCT** — belief-propagation's own MAP-seeking
variant, where a message `m_{i→j}(x_j)` reports the BEST achievable
score over the rest of the (possibly loopy) sub-network for each
candidate `x_j`, generalising ICM's "best response given neighbours'
CURRENT state" to "best response given neighbours' MESSAGE (their own
uncertainty about what the rest of the network implies)," which is
exactly the "genuinely different tool" the task asks for — not a
marginal/probability computation the toolbox has no other consumer for.
Implemented in the ADDITIVE LOG DOMAIN (min-sum) rather than the raw
multiplicative-probability domain the task's own formula sketch used,
because: (a) it is the textbook-standard, numerically-safe
reformulation (`log(max_x product) = max_x sum(log)`); (b) it composes
directly with this project's OWN existing energy-additive vocabulary
(`mt_energy`'s `H = -Σ J σ σ - Σ h σ` is already additive, not
multiplicative — `coherence = -H/N` per `causal_attitude_networks.json`);
(c) it avoids ever needing `Exp` on a quantity that could blow up
numerically in the probability domain.

**SUM-PRODUCT is also built**, as the deliberately-predicted-to-lose
comparison this investigation's own theory can state precisely, not
merely gesture at: sum-product's natural read-off is a per-node MARGINAL
(the log-sum-exp-combined belief), and the STATE decision from a
marginal is a per-node argmax of THAT marginal — which can pick a joint
configuration inconsistent with any single low-energy basin, precisely
because it never enforces joint coherence between neighbouring
decisions. This is, exactly, `causal_attitude_networks.json`'s own
declared phenomenon: **"multiple inconsistent views = multistable
network."** The measurement in §4 below checks this directly rather than
asserting it.

**What this does NOT resolve** (named up front, not after the
measurement comes back inconvenient): whether MAX-PRODUCT itself HAS a
stable fixed point on this project's own frustrated networks is exactly
`CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md` §4.4's own open literature
question ("in frustrated models with an external field at low
temperatures, the Bethe approximation stops having a solution... it is
still an open problem"). This rung measures whether it converges here,
on real networks; it does not resolve the general open problem.

---

## 3. Term composition design

Reusing `can_counterfactual.py`'s own established shape exactly (see its
own module docstring): Term builders that are verbatim-twin adaptations
of `local_field_term`/`_neighbour_state_term`, applied to MESSAGE
components instead of neighbour STATES.

- `unary_score_term(concept, mt, x_i) = temperature * (external_field +
  identity_field) * x_i` — the SAME `external_field`+`identity_field`
  sub-expression the seed's own threshold rule reads, scaled by
  `temperature` the same way, times the candidate value.
- `pairwise_score_term(weight, mt, x_i, x_j) = temperature * J_ij * x_i *
  x_j` — the SAME coupling term the seed's own `Sum`-over-`Edges` reads,
  generalised from "neighbour's current state" to "a candidate joint
  assignment."
- `incoming_sum_term(i, exclude_j, x_i, incoming_by_k)` — `Sum` over
  `Edges(i, "causal_influence")`, value = an `IfThenElse` ladder keyed on
  each edge's target-node IDENTITY (a `NodeID` `Lit`, never a raw int —
  registered explicitly here because this distinction caused a real,
  caught-before-shipping bug during the build, see
  `CAN_LOOPY_BP_RESULTS.md`), splicing in the PREVIOUS round's held
  message value per neighbour, with the excluded neighbour `j` forced to
  `0.0` (the log-domain identity for "no message") — the exact
  "leave-one-out" composition `CAN_SOLVER_TRACTABILITY_RESULTS.md` §4
  point 2 confirmed buildable from `Filter`+`Edges`+`Nth`+`Eq`, here
  achieved with one fewer Term (the override ladder subsumes the
  exclusion) than that document's own sketch.
- Combine (max-product: `max(...)`; sum-product: `log-sum-exp(...)`) and
  the final per-node argmax are PLAIN PYTHON ARITHMETIC over
  already-Term-evaluated floats — registered explicitly as a design
  choice, not an oversight, matching `predict_ripple`'s/
  `predicted_info_gain`'s own established precedent for exactly this
  class of operation (see the module's own "ON PYTHON VS TERM
  ARITHMETIC" note). No new Rust Term is used or needed anywhere in this
  module — confirmed against the real Term vocabulary during the build
  (`Filter`/`Edges`/`EdgeAttr`/`Nth`/`Eq`/`IfThenElse`/`Sum`/`Plus`/
  `Times`/`Pick`, all pre-existing and already used elsewhere in this
  exact arc).

Genuinely NOT used, and registered as such: the task's own sketch
mentioned `Prod` (multiplicative leave-one-out) and a possible
`Sum{source: Lit([...])}` iteration over the discrete vocab as a graph
Term — `CAN_SOLVER_TRACTABILITY_RESULTS.md` §4 point 3 flagged the
latter as "very likely, not confirmed." This build sidesteps that open
question entirely rather than resolving it: the discrete vocab (2 or 3
values) is enumerated in PYTHON at Term-BUILD time (matching
`target_state_term`'s own fixed, explicit `IfThenElse` ladder style, not
a generic collection-iteration Term), so no Term ever needs to iterate a
literal list of candidate values.

---

## 4. Convergence and quality-comparison measurement design (registered
before running)

**Networks**: the SAME real stress-test networks `CAN_SOLVER_
TRACTABILITY_RESULTS.md` used — (a) N=16 complete-graph, random-sign,
coarse-quantized coupling (the frustrated/dense adversarial case,
`temperature=2.0`, same `_build_n16_draw` seed convention); (b) real
Bigville residents (`seeds/bigville_cast100.json`), sparse,
treewidth-2. Sample sizes are SMALLER than the tractability rung's own
30-draw/30-resident design (this rung's BP sweep is materially more
expensive per network than a single discrete-async settle — real,
measured wall-clock cost, not assumed) — the exact `n` used is reported
plainly in `CAN_LOOPY_BP_RESULTS.md`, per this arc's own standing "a
count can be held; report the real sample size, never imply the prior
rung's n" discipline.

**Per network, four solvers compared**:
1. Single discrete-async settle (baseline, `run_rules`/`scoped_settle`
   from zero-init — the existing, unmodified mechanism).
2. `multi_start_settle_and_pick_best` (K=20, the existing, unmodified
   tool this rung builds ALONGSIDE).
3. Loopy BP, max-product.
4. Loopy BP, sum-product.

Each reports: converged (bool), rounds used, and
`mt_frustration_given_state` on its own final discrete state (the SAME
scoring function every solver in this toolbox is already compared by).

**What counts as GO** (registered before running, not fitted after):
this is toolbox-characterisation work, not a single pass/fail gate — a
GO here means "the tool is built, correctly characterised, and the
comparison is measured and reported honestly," not "BP beats
multi-start." Specifically:
- BP (either variant) converges on a clear majority of the sparse
  Bigville sample (a real solver that fails to converge on the EASY case
  would not be a usable tool at all).
- The max-product vs sum-product comparison is measured, not merely
  argued — if sum-product finds HIGHER (worse) frustration than
  max-product on a measurable fraction of the frustrated N=16 draws,
  that is the predicted, load-bearing confirmation of §2's own
  theoretical claim.
- The BP-vs-multi-start comparison is measured and reported precisely
  whichever way it comes out — a clean null (BP does not reliably beat
  multi-start on this project's own sparse, low-treewidth real networks)
  is an accepted, complete, valuable outcome per the task's own explicit
  framing, not a failure to fix before reporting.

---

## 5. Explicitly out of scope, confirmed before building

- `seeds/can_native_reimplementation.json` — never opened for writing in
  this worktree.
- `domains/can_native_orchestration.py` — never opened for writing;
  imported nowhere by `domains/can_native_bp.py` (zero coupling, per its
  own module docstring), only read (as a reference precedent) during
  design.
- `can_ops.rs`'s continuous mean-field mechanism — untouched.
- Junction-tree/treewidth work — not attempted; `CAN_SOLVER_
  TRACTABILITY_RESULTS.md` §2's own treewidth numbers (Bigville=2,
  N=16-complete=15) are read as context for interpreting WHY BP may or
  may not help on either topology, not re-measured here.
- New Rust Terms — none used; §3 above names the exact vocabulary this
  build stays inside, confirmed against the real engine before the
  measurement script was written.

---

**Worktree**: `/tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/can-loopy-bp`
**Branch**: `can-loopy-bp`
**Base**: `main @ 76b8aea`
