# PICK UP HERE — the per-term decomposition, and what four rungs did not establish

Written 2026-08-10 at the end of a session. Everything below is committed on
`gamma-substrate/humanoid-language`. Read this before touching the humanoid
motor path.

## The one thing to do first

**Fix the decomposition instrument's placement bug, smoke-test it on a SHORT
episode, and only then spend 80 minutes.** Two full runs have already been lost
to this instrument, both returning a plausible-looking `samples: 0` instead of
an error.

`HumanoidComposer::compose` (`runners/dsl/src/motor_compose.rs`) has **two early
returns before the winner re-score**:

```rust
let Some(primary) = ... else { return Vec::new() };   // early return
let mut plan = vec![primary];
if !self.expansion_allowed() { return plan; }          // early return
loop { ... }
let _ = self.cost(&plan, None);   // <-- the instrumentation, often unreached
plan
```

The walk composes single-member plans, so `expansion_allowed()` is false, the
second return fires, `cost` is never called, `LAST_COST_TERMS` stays at its
initial zeros, and the all-zero filter in `_sample_cost_terms`
(`scripts/jabberwock_humanoid_walk.py`) discards every sample.

Fix: record the terms on **all three exit paths**, or drop the re-score and have
`cost` publish unconditionally with a "did this plan get scored at all" flag.

**Then gate it:** run ~10 actions and assert `samples > 0` BEFORE any long run.
Both failures would have been caught in under a minute.

### The instrument has failed three times, each silently

1. `humanoid_cost_terms` compiled into the `.so` but was never re-exported by
   `runners/dsl/python/substrate_rs/__init__.py` (a hand-maintained shim) —
   every call raised `AttributeError`.
2. A bare `except Exception: return` in `_sample_cost_terms` swallowed that
   into `samples: 0`. Removed; a missing readout now prints once and records
   `unavailable_reason`.
3. The placement bug above. `unavailable_reason: None` with `samples: 0` is the
   signature of this one — the function is reachable, the composer just never
   scored anything.

## The open question, and it is binary

**Does `HumanoidComposer::cost` ever run on the walking protocol?**

Evidence it may not: `motor_compose_member` prefers the GENERIC composer,
falling back to the humanoid one only if `has_embodied_effector_model` yields
nothing:

```rust
let mut model_nodes = interner.lookup("has_embodied_effector_model") ...
if model_nodes.is_empty() { ... "has_humanoid_phase_action_model" ... }
```

If the walk episodes carry `has_embodied_effector_model`, every decision goes
through `Composer::program_cost` (7 consequence terms + drag/energy/activation/
log_authority) and **`HumanoidComposer::cost` — including rung 3's
`cost_of_transport_residual` — never executes at all.**

That is consistent with everything measured: rung 5's one-sided change was a
byte-identical null, and the decomposition read all-zero. **Check this directly
before anything else** — it is one query against a live episode, and it decides
whether rung 3's commit message attributes its result to the right mechanism.

If the humanoid composer is unused, rung 3's upright fix came from the OTHER
changes in `9d068551d2` (the `state_contact_force_newtons` episode cache key,
the `current_effector_regime` plumbing), and **the rung 3 commit message names
the wrong cause** and must be corrected in place, not quietly.

## What is committed and holds

| commit | what |
|---|---|
| `9d068551d2` | RUNG 3 — upright fixed (never falls in 600 actions, com_min 0.1262 → 0.8379, tilt 0.2508 → 0.0354, aerial 144 → 7); travel LOST (directed_progress +0.09524 → −0.01574, lateral drift 2.705e-05 → −0.2346). **Attribution now in doubt — see above.** |
| `b1a6280861` | RUNG 4 — gait taxonomy is decoration for the DECISION path: removing `name`/`gait_name`/`coordination_family` reproduces rung 3 on all 15 fields, 7,043 vs 7,044 CPU-s. Two non-rule readers enumerated. |
| `612f04164d` | P0 on a String is countable — `Value::None` stays silent (the absence idiom), a PRESENT non-numeric bumps `Counters::numeric_op_non_numeric_operand`. Value semantics unchanged. |

Rung 5 (one-sided transport residual, `RUNG5_ONESIDED_TRANSPORT_PREREG.md`) is a
**recorded NULL** — byte-identical to rung 3 on all 15 fields.

### Three of my rung-5 claims are RETRACTED

* "The guard is the wrong guard" — **false**, `matched_capability_translation_per_joule`
  already guards on `experience_count > 0.0`.
* "The regime attrs are strings read as 0.0 by `fattr`" — **false**, `T(...)`
  wraps a Term evaluating to a number.
* "The transport term suppresses travel" — **unsupported**; it may never have
  run.

### And my own gate printed a false pass

`PRED 1 travel > -0.01574 : True` on the value `-0.0157394588926743` — the
identical number rung 3 produced, which compares greater-than a 5-digit
rounding of itself. **Prediction 1 was falsified by a byte-identical result and
the check said it passed.** Use equality against the prior artifact
(as rung 4 did), never a truncated literal.

## Standing facts to reuse, not re-derive

* **Block 0 null (8 runs, 8/8 identical):** first_fall 201, com_min 0.1262,
  tilt_median 0.2508, directed_progress 0.09524, lateral_offset 2.705e-05,
  support_alternations 33, aerial_per_cycle 9.0, load_median 158.3. Determinism
  is why n=1 is defensible here.
* **Cost is measured in CPU-seconds, never wall-clock** (this box is shared;
  wall-clock measured contention). ~7,044 CPU-s per walk run. `cpusample.sh` in
  the session scratchpad. **These numbers are Zen-5-specific and do not
  transfer** to the 5900X.
* **Moving machines breaks byte-identity claims.** NumPy 2.4.6 dispatches
  `AVX512_ICL`/`AVX512_SPR` at runtime over an `X86_V2` baseline; the 5900X has
  no AVX-512. Either re-baseline Block 0 there, or pin both boxes with
  `NPY_DISABLE_CPU_FEATURES="AVX512_ICL AVX512_SPR"`. The Rust engine is generic
  `x86-64` (verified: zero `%zmm` in the binary) and needs no recompile for ISA
  reasons — but `_native.abi3.so` is gitignored, so it must be built there anyway.
  **Never add `-C target-cpu=native`.**
* **Pre-existing red, not ours:** `test_humanoid_adaptation_migrated.py::
  test_graph_learns_full_humanoid_and_survives_matched_impulse`
  (`first_fall_action` 326). Reproduced on a rebuilt PRE-rung-3 engine, so
  neither rung caused it. Absent from `results/failure_baseline.json` because
  that baseline is pinned at `0e61f60e` (2026-07-21) where the file was swept
  GREEN — **the baseline is stale and this regressed from other work.**

## The architectural frame this sits in

The creator's framing, which the measurements support:

* **A flat scalar objective has exactly one optimum**, so reweighting relocates
  a single fixpoint rather than escaping it. `HumanoidComposer::cost` sums nine
  terms unconditionally and minimises greedily; there is no state-conditionality
  anywhere except a boolean `model_admissible` filter.
* **The entire premise of admissibility grammar is that we don't have to choose
  a single fixpoint.** Γ is substrate foundation (G, Γ, C — `grammar.rs`
  "weighted admissibility grammar"), with productions, where-clauses, weights,
  and `admissible_moves` returning `(type, attrs, weight)` for Boltzmann
  selection. The humanoid deciding path has **no productions at all**, and rule
  effects bypass `check_edge` entirely (`rewrite.rs` writes via
  `graph.insert_edge`; the `gated` flag is reserved and unbuilt).
* **The F-16 arc measured the same collapse independently** and it is the
  strongest external evidence here: its Pareto frontier was CI-separated WORSE
  on all three fault scenarios, and Block H reports *"THE FRONTIER HAS STOPPED
  CHOOSING"* — 48/48 adoptions the same corner pair, 2 of 6 ordinals ever held.
  Named cause: *"a surrendered axis is scored a flat 0.0 while a kept axis is
  scored unbounded-below, so the corner that gives up the most wins."* That is
  rung 3's standing body, in the other body.
* **Set-valued selection alone does NOT fix it** — that is the measured lesson.
  The F-16's state-conditional machinery still collapsed because the RESPONSE
  SET had holes: *"`speed_priority` is unreachable... the region built for it
  admits nothing else... a gate whose middle region is empty is a delay line."*
  The work is in what the productions can GENERATE, not in replacing argmin.
* **The live F-16 direction is the order ladder + condensation**
  (`embodied_motor_program` v1.14.0, `docs/regime_pareto_frontier_results.md`):
  order N = search (`MotorCompose`), order 1 = a held ratio in one multiply,
  order 0 = reflex, involuntary, fired by a SURPRISE SHAPE rather than a clock.
  Condensation mints order-0 from repeated order-1 success and RELEASES on
  variation — measured 11 surprise shapes, 7 order-boundary transitions, one
  reflex standing, in a single 998-action episode. **`MotorCompose` cannot be
  deleted** (interpreted composer: 838 s without completing one episode vs 69 s
  native) but **~84% of its composition re-derives a program already held**
  (234 composed, 160 internalized, 35 distinct shapes, 26 after coverage
  collapse). So: **demote to the mint path, not delete.** `actuator_group` is
  morphology-neutral, so "the humanoid generality falls out".
* **Caveat before importing it:** condensation caches an answer, it does not
  repair a wrong objective. If the humanoid's order-N answer is "stand still",
  what condenses is a reflex for standing still.

## Method rules this session earned the hard way

1. **Never quote a pipeline's exit code** — `pytest ... | tail` returns tail's
   status. Redirect to a file and read the summary line.
2. **Never `pgrep -f`/`pkill -f` a pattern that appears in your own command
   line** — it matches your own shell. Cost 73 minutes once and killed a live
   command another time. Use PID files.
3. **A baseline is a LIST of node ids, never a count or a characterisation.**
4. **Verify a new binding end-to-end (`import`, call it) before spending a long
   run on it.** Compiling and parsing are not connectivity.
5. **An instrument must never swallow its own failure.** Every silent `except`
   turns a wiring fault into a finding-shaped result.
6. **Check the marker is real.** `strings | grep <rust_field_name>` always
   returns 0 — struct fields are not string literals. Use a genuine string
   literal (`state_contact_force_newtons` discriminates the rung-3 engine).
7. **Never modify the tree or reinstall the `.so` while a run is in flight** —
   replacing a loaded `.so` SIGSEGVs the running process. `cargo build` into
   `target/` is safe; the `cp` into `python/substrate_rs/` is not.
