# Blocker A — a native, non-mutating "what-if" counterfactual predictor for the discrete CAN mechanism — PREREG

**Charter.** `CAN_CONSUMER_MIGRATION_RESULTS.md` §1 (row 1, row 3) names
**Blocker A** precisely: *"no native non-mutating counterfactual predictor
exists anywhere in this arc; `run_rules()` always mutates."* Two real
consumers are blocked on it — `domains/drive_curiosity.py::probe_via_what_if`
(`:65-103`) and `domains/insight_seeking.py::predict_perturbation_impact`
(`:69-134`, feeding `find_hot_nodes` `:37-66` and `seek_insights` `:137-180`).
This rung's charter is to design and build the native predictor (or report
precisely why it cannot be built from existing Term-evaluation machinery),
demonstrate it live on the real engine, and sketch — not build — what
migrating the two consumers would look like. `CLAUDE.md`, "SHAPE IS
ACQUISITION, RULE IS EXECUTION" and "BASE-AS-DIMENSION", re-read in full
before writing this document.

**What the two blocked callers actually need, read from their own source,
not assumed:**

- `probe_via_what_if` (`drive_curiosity.py:65-103`): given a Concept and a
  hypothetical `external_field` value, compute `current_marginal` (every
  Concept's σ under the graph's real committed state) and
  `predicted_marginal` (every Concept's σ under the hypothetical override),
  then sum `|Δσ|` across the WHOLE network (`info_gain_total_change`),
  the single largest per-node change (`info_gain_max_node_change`), and a
  flip count (`predicted_flipped_count`). This requires the FULL network's
  new equilibrium under the override — not just the probed node's own
  reaction.
- `predict_perturbation_impact` (`insight_seeking.py:69-134`): same
  full-network predicted marginal, plus `mt_energy`/`mt_frustration_given_
  state` evaluated on it (a field-term correction for the h delta is
  applied by hand, `:88-103`), compared against `mt_audit_basin`'s current
  energy/frustration. `find_hot_nodes` (`:37-66`) and `seek_insights`
  (`:137-180`) both assume `mt_relax_to_marginal`/`node_local_frustration`
  reflect an EQUILIBRIUM state (`seek_insights` calls `mt_relax_to_marginal`
  first, `:157`) — i.e. these consumers are built on the CONTINUOUS
  mechanism's iterative relax-to-fixpoint semantics throughout, not a
  single-shot local read.

**The orchestrating session's lead, investigated, not assumed.** The
log-odds render (`LOGODDS_GENERATOR_RESULTS.md` §2/§4(b)) is a PURE Term
composition (`Log(Div(Plus(confirm,1),Plus(disconfirm,1)))`) evaluated via
`Substrate.evaluate(term, env)`, confirmed live never to write graph state.
`can_native_update_3state`/`_2state` (`seeds/can_native_reimplementation.
json:102,505`) are themselves ordinary Term compositions — `local(c) =
Attr(c,"external_field") + Attr(c,"identity_field") + Sum(Edges(c,
"causal_influence"), e, EdgeAttr(e,"weight")*Attr(Nth(e,2),"state"))`,
thresholded by a hard-coded `IfThenElse` ladder (`ATANH_HALF =
math.atanh(0.5)`, no `Tanh` Term). **Confirmed by reading `runners/dsl/src/
py.rs:3017-3067`'s `evaluate()` binding and `pydict_to_env`
(`py.rs:948-969`): `env` binds a `Var` name to ANY `Value` via `py_to_value`
— a node handle, a float, an int, a string — not only node handles.** This
means a hypothetical override does NOT require editing the term tree at
all: build the SAME local-field/target-state Term ONCE, parametrised with
`Var("h_ovr")` in place of `Attr(c,"external_field")`, and evaluate it
twice — once with `h_ovr` bound to the real current field (the baseline)
and once with `h_ovr` bound to the hypothetical value — both zero-mutation
`Substrate.evaluate()` calls. `_log_odds_term`/`test_log_odds_render_ranks_
evidence_and_never_writes_back` (`tests/test_can_native_reimplementation.py:
363-387,448-486`) is the exact precedent this rung follows for the
single-node case.

**The genuinely open question, registered before any code is written.**
`local(c)`'s `Sum` term reads `Attr(Nth(e,2),"state")` — a NEIGHBOUR's
`state` attr, live off the graph — for every edge, dynamically, via the
existing `Edges` Term. A single evaluation of this formula for node `c`
alone answers "what would `c`'s own next discrete step be, holding every
neighbour's CURRENT (real) state fixed" — an exact, zero-hop prediction.
It does **not** answer what the callers above actually ask for: the
network-WIDE new equilibrium, which requires neighbours to also react to
`c`'s hypothetical new state, and their neighbours to react to that, for
as many rounds as the real asynchronous mechanism needs to reach a fixpoint
(`CAN_NATIVE_REIMPLEMENTATION_RESULTS.md` §2 measured real convergence
taking up to several hundred `run_rules()` steps on N=8 networks, though
Bigville's demo converged in 3). **Registered prediction 1**: a single
`Substrate.evaluate()` call cannot answer the multi-hop question — Term
evaluation is a DAG evaluation of one expression tree, not an iterative
fixpoint solver, and `run_rules()`'s own asynchronous, commit-immediately
semantics is exactly the mechanism the substrate uses to reach one. Building
a genuine network-wide non-mutating predictor therefore needs a BOUNDED,
NON-COMMITTING, MULTI-ROUND procedure: repeatedly evaluate the SAME
target-state Term per Concept, feeding each round's results forward through
an in-memory (not graph-written) override, rather than a single evaluation.

**The design, registered.** Extend the "substitute one Attr with an
env-bound `Var`" idiom to substitute a NEIGHBOUR's `state` read too:
`Attr(Nth(e,2),"state")` becomes a chained `IfThenElse` over
`Eq(Nth(e,2), Lit(override_node))` for each node in a KNOWN (Python-side)
override set, falling back to the live `Attr` read when no override
applies — the override node/value pairs are baked in as `Lit`s at Python
TERM-BUILD time (not resolved via `env`), because the override set is
known to the caller before the term is built (the same "codebook_scope
parametrises the decode, Python decides nothing about the recognition
itself" shape `CAN_NATIVE_REIMPLEMENTATION_RESULTS.md` §0.0.2 already
uses for `ShapeDecode`). A Python driver then runs a bounded number of
rounds, each round re-evaluating this term for every Concept under `mt`
IN SEQUENCE (Gauss-Seidel — matching `run_rules()`'s own "commit
immediately, next read sees the update" cold-path semantics, `rewrite.rs:
2183-2214`, deliberately NOT a synchronous Jacobi sweep, which is exactly
the pathology `CAN_NATIVE_REIMPLEMENTATION_RESULTS.md` §2 built the
discrete-async mechanism to avoid), maintained entirely in an in-memory
Python dict never written to any node attr, until the dict stops changing
or a round cap is hit. **This driver makes zero decisions the Term
evaluator does not already make** — the threshold branch (the actual
Hopfield update rule) is evaluated by the Rust Term evaluator every time;
Python only chooses which node's term to build and evaluate next and when
to stop, the same shape `run_curiosity_all_mts`/`seek_insights`'s existing
loops over Mts/hot-nodes/h-perturbations already have, not a new rule
engine.

**Registered predictions, before any code is written:**

1. The zero-hop, single-node prediction (no other node's state is allowed
   to move) will be EXACT — byte-identical to what actually setting the
   override on the graph and running `run_rules()` a single controlled
   step produces, on an isolated node with no `causal_influence` edges
   (nothing else CAN move).
2. The bounded multi-round predictor will be genuinely NON-MUTATING
   (byte-identical node attrs before/after the predict call) but its
   accuracy against the REAL asynchronous mechanism (predict, then commit
   the same evidence for real and run `run_rules()` to convergence,
   compare) is an OPEN EMPIRICAL QUESTION, not assumed — Gauss-Seidel
   asynchronous updates are guaranteed to converge to A fixed point for a
   Hopfield-shaped energy function regardless of order, but WHICH fixed
   point can in principle depend on visitation order when a network sits
   near more than one attractor. Reported honestly whichever way the
   measurement comes out, on real small networks (matching this arc's own
   `_build_draw` N=8 shape, `tests/test_can_native_reimplementation.py:
   55-84`), with a real predict-then-verify cross-check.
3. If prediction 2 fails badly (predicted state vector diverges from the
   real committed outcome on more than a small minority of probes), that is
   reported as a genuine, valuable NO-GO for the multi-round predictor
   specifically — the zero-hop primitive (prediction 1) still stands on its
   own as a real, useful, exact primitive regardless.

**Scope, registered.** Zero new Rust — every Term used
(`Var`/`Lit`/`Attr`/`Eq`/`IfThenElse`/`Plus`/`Times`/`Gt`/`Lt`/`Gte`/`Sum`/
`Edges`/`EdgeAttr`/`Nth`) already exists and is reused verbatim; if this
rung finds the algebra insufficient, it stops and reports why rather than
adding a Term. `drive_curiosity.py`/`insight_seeking.py`/
`insight_propagation.py` are NOT edited — a migration sketch is written in
the RESULTS doc, not built. `can_ops.rs`, the continuous mechanism, and
`seeds/can_native_reimplementation.json`'s existing rules are untouched
(read-only). The new module is a Python Term-BUILDER + thin orchestration
driver (`domains/can_counterfactual.py`), the same legal category as
`reflective_faculty.py`'s existing shims over `ShapeDecode` — it assembles
and evaluates pre-existing Terms, it does not implement the discrete update
rule's decision logic itself (that stays inside the evaluated `IfThenElse`,
executed by the Rust evaluator).

**Regression discipline.** `tests/test_can_native_reimplementation.py`
stays green, byte-unchanged. A new `tests/test_can_counterfactual.py`
covers: non-mutation (byte-identical attrs before/after every predict
call), the zero-hop exact-match demonstration, the bounded multi-round
predict-then-verify cross-check (both accuracy and the honest failure mode
if found), and a predicted-vs-actual frustration comparison via the
already-reusable `mt_frustration_given_state` closed-form utility (reused
unmodified, the same "pure, non-iterative, O(edges) scoring" idiom the
Bigville migration rung already established as legitimate reuse,
`CAN_CONSUMER_MIGRATION_RESULTS.md` §2.2).

Worktree: `/home/matt/ozmadev/ocelot-worktrees/can-counterfactual-predictor`,
branch `can-counterfactual-predictor`, base `main @ 299ace3` ("Merge
can-consumer-migration: 1/7 migrated (Bigville), 6/7 honestly blocked, GO").
Two sibling worktrees confirmed running concurrently at branch time
(`can-hebbian-materialization` @ 299ace3, `can-synchronous-update-fix` @
b9f4429) — neither touches this rung's files (`domains/can_counterfactual.py`
new, `tests/test_can_counterfactual.py` new, two new docs); `seeds/
can_native_reimplementation.json` is read-only in this rung, so no edit
collision is possible regardless of what the Hebbian-materialization sibling
does to that file.
