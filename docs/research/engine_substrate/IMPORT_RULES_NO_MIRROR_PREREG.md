# `import_rules_no_mirror` — pre-registration

**Posture:** MEASURE-THEN-BUILD, per this folder's own house discipline and
per `RULE_REFERENCE_LAYER_SIZING_RESULTS.md` §5's own explicit charter for a
future rung: *"`import_rules_no_mirror` (or a mirror-suppression flag on
`import_rules`), the exact analogue of the landed
`add_production_no_mirror` — this is the single change that converts RR2's
NO-GO into a GO."* This doc registers the GO/NO-GO bars, and records the
root-cause investigation, **before** any `py.rs` or `world_adapter.py` edit
is made.

**Charter.** Determine whether `WorldAdapter.load()`'s rule-replay step
(`substrate/world_adapter.py:6187`, `wa.inner.import_rules(blob["rules"])`)
has the same unbounded-checkpoint-growth defect the Γ-production replay had
before `add_production_no_mirror` fixed it (`GAMMA_LOAD_GROWTH_FIX_RESULTS.md`).
If it genuinely does, build the exact analogous fix. If investigation shows
the growth `RULE_REFERENCE_LAYER_SIZING_RESULTS.md` §2.5 measured was a
**simulation of a mechanism that does not exist in `add_rule`/`import_rules`
today** (as that document's own §8 uncertainty #1 states plainly: *"§2.5's
amplification is simulated, not built... exact numbers from a real
mirror-in-`add_rule` build are not [established]"*), then the charter becomes:
determine whether a pre-emptive seam/contract should be added now, or whether
the honest answer is that this charter is premature until a real rule-mirror
mechanism exists.

**Note on why this is not a copy-paste of the Γ fix sight-unseen.** The Γ
fix had two structurally distinct PyO3 methods before the fix even started:
`PySubstrate::add_production` (general binding, `py.rs:7803`) called the
mirroring Rust-inherent `Substrate::add_production`, while `load()`'s replay
also went through that SAME general binding — the fix's whole shape was
*splitting* that one call into a mirroring path and a non-mirroring path.
Whether the Rule side has that same shape, or a different one, is exactly
what §0 below determines by reading, not by assuming the analogy transfers
mechanically.

---

## 0. Root-cause investigation (done before registering the bars below)

**0.1 What `import_rules` actually calls, read directly
(`runners/dsl/src/py.rs:4558-4583`).** For each exported rule dict, it parses
the rule (`parse_rule_json`) and calls `inner.add_rule(rule)` —
the **Rust-inherent** `Substrate::add_rule` (`runners/dsl/src/substrate.rs:2480`),
the exact same function the PyO3 `add_rule` binding (`py.rs:3254`,
`Ok(inner.add_rule(rule).0)`) calls. There is only ONE Rust-inherent
`add_rule` in this codebase (confirmed: `grep -n "fn add_rule"
runners/dsl/src/*.rs` outside `py.rs` returns exactly one hit, `substrate.rs:2480`)
— unlike Γ, where the general PyO3 binding and the Rust-inherent method were
already two distinct mirroring/non-mirroring-capable layers, **the Rule path
has only one layer**, shared by live authoring and checkpoint replay alike.

**0.2 Does `Substrate::add_rule` (`substrate.rs:2480-2633`) write anything to
the graph?** Read in full, every line. It: assigns/dedupes a `RuleUid`; sets
`rule.active = true`; reorders match-edges by a graph-cardinality cost proxy
(`edges_by_type(et).len()` — a *read*, not a write); calls
`self.graph.declare_attr_index(hint.node_type, hint.this_key)` for each
`IndexJoinHint` (confirmed by reading `graph.rs:356-377`: this populates an
in-memory `FxHashMap<(Sym,Sym), FxHashMap<Value, RoaringBitmap>>` index
structure — **zero `Node`/`Edge` writes**, purely bookkeeping over already-
existing nodes); computes `rule.derive_access`, `rule.content_hash`; pushes
into seven parallel `Vec`s that are rule-store bookkeeping
(`rule_readers_by_key`, `rule_edge_type_deps`, `rule_has_where`,
`rule_dirty`, `rule_cost_micros`/`_count`/`_progress`, `rule_cursors`,
`rule_pred_retract_ok`, `rule_where_jit`); pushes `rule` itself into
`self.rules`; bumps `self.gamma_epoch`. **At no point does it call
`self.graph.add_node`, `self.graph.add_edge`, `add_term_subgraph`,
`reflect::term_to_subgraph`, or anything resembling a graph mirror.** There
is no `rule_reflect.rs` in the tree (confirmed: `ls runners/dsl/src/
rule_reflect.rs` → no such file) and no call from `add_rule` into any
mirroring function.

**0.3 What did `RULE_REFERENCE_LAYER_SIZING_RESULTS.md` §2.3/§2.5 actually
measure, then?** Its own §5 states this precisely and this rung independently
confirms it by reading the same source: the sizing rung called the PyO3
`add_term_subgraph` binding **directly, by hand, once per seed rule's `where`
Term**, as a stand-in for what a *hypothetical future* `rule_reflect.rs`-style
mirror on `add_rule` would cost if built — it did not call `add_rule` itself
in a way that mirrors, because `add_rule` does not mirror. The resulting
"+2,557 nodes per checkpoint cycle" figure is a **simulation of a mechanism
that has no counterpart in `add_rule`/`import_rules` on `main` today** — its
own §8 says this plainly (*"§2.5's amplification is simulated, not
built"*). This rung's job is to verify that characterisation against the
CURRENT source (not the prior rung's own account of it) — done in 0.1/0.2
above by reading `py.rs` and `substrate.rs` directly, not by re-reading the
prior doc's prose.

**0.4 Live prediction, registered before running it.** Given 0.1-0.3, the
predicted outcome of a real (not simulated) multi-cycle `WorldAdapter.save()`
→ `WorldAdapter.load()` loop, exercising the REAL `import_rules` →
`Substrate::add_rule` path with no code changes, is: **flat node/edge counts
across every cycle** — because nothing in that call chain writes a graph
node. This is registered here, before running the probe in AR1 below, so the
result is a genuine confirmation or a genuine surprise, not a post-hoc
narrative.

**0.5 Candidates for what the charter becomes if 0.4's prediction holds.**

- **(a) Build `import_rules_no_mirror` anyway, as a defensive no-op sibling.**
  Considered and provisionally disfavoured: a function whose body is
  identical to `import_rules`'s current body, under a new name, protecting
  against a mirror that does not exist, is dead code with a misleading
  docstring — it would claim to fix something and fix nothing, which is
  worse than not having it (a future reader would reasonably assume calling
  it is necessary/sufficient for load-safety once real mirroring exists,
  when in fact whether it actually IS the right shape depends on what the
  real mirroring mechanism turns out to look like — unknowable now).
- **(b) Do nothing beyond documenting the finding.** Matches
  `RULE_REFERENCE_LAYER_SIZING_RESULTS.md`'s own posture when it found
  `rule_reflect.rs` unnecessary to build ("no build is to be forced").
  Considered strong, but leaves the exact hazard shape (0.1's finding that
  Rules have only ONE layer, unlike Γ's two) undocumented at the point in
  the source where a future implementer would actually be working.
- **(c) Add a doc-comment-only contract at `Substrate::add_rule` and
  `import_rules`, landed as a genuine (tiny, non-functional) commit, stating
  the exact hazard precisely: because `import_rules` and the live-authoring
  PyO3 `add_rule` binding share the SAME Rust-inherent function, any future
  rule-mirroring mechanism must NOT be added directly inside
  `Substrate::add_rule` — doing so would make checkpoint replay mirror too,
  by construction, with no way to opt out short of re-splitting the two
  callers apart (exactly the Γ fix's own shape, but needed pre-emptively
  here rather than reactively). This requires a source change (hence an
  engine rebuild, per this project's own provenance discipline) for a
  comment-only, zero-behaviour-change diff.

**Selection deferred to AR2/AR3 below**, gated on 0.4's live measurement
actually confirming the prediction (if it does not — if real cycles show
ANY growth — this whole §0 analysis is wrong and the charter reverts to
building the real analogue of `add_production_no_mirror`, per the original
brief).

---

## 1. AR1 — investigation bar

**Bar:** what `import_rules`/`add_rule` do today is established by reading
the code (§0.1-0.3 above) AND confirmed by a live (not simulated) multi-cycle
save/load measurement using the real `WorldAdapter`/`Substrate` — not
inferred from `RULE_REFERENCE_LAYER_SIZING_RESULTS.md`'s own prose. **Status:
reading done (§0); live measurement is the first thing run under this
PREREG, registered prediction 0.4 (flat, zero growth).**

---

## 2. AR2 — GO/NO-GO on building a real fix today

**GO condition:** the live measurement (AR1) shows non-zero, non-converging
node/edge growth across repeated save/load cycles on the unmodified engine —
i.e., 0.4's prediction is WRONG and a real mirror-shaped defect exists in
`add_rule`/`import_rules` today. In that case: build the direct analogue of
`add_production_no_mirror` (candidate the original brief names), sized and
shaped exactly like `GAMMA_LOAD_GROWTH_FIX_RESULTS.md` §3's AR3.

**NO-GO condition:** the live measurement confirms 0.4 — flat growth, zero
new nodes per cycle, because `add_rule` genuinely does not mirror anything
onto the graph today. In that case, per the brief's own explicit permission
("An honest 'there's nothing to build yet' is a complete, valuable result —
do not force a fix for a mechanism that isn't real yet"), this rung does
**not** build `import_rules_no_mirror` as a functional fix (there is nothing
for it to fix). Instead, AR3 becomes: choose between §0.5's candidates
(a)/(b)/(c) for what, if anything, gets landed to prepare for a future real
mirror mechanism.

---

## 3. AR3 — conditional on AR2's verdict

**If GO:** build `import_rules_no_mirror` (or an equivalent mirror-suppression
path), bars mirroring `GAMMA_LOAD_GROWTH_FIX_PREREG.md` §3 exactly:
content-fidelity (B1), zero redundant growth (B2), no behavioural change to
whatever `add_rule`'s current (mirroring, in this branch) semantics are (B3).

**If NO-GO (the predicted branch):** select among §0.5's (a)/(b)/(c). Working
preference, stated here before the measurement closes it out: **(c)** is the
only option that leaves a durable, source-level trace of the hazard at the
exact place a future implementer would need it, and it costs only a doc
comment (verified zero behavioural diff via the coherence probe + a targeted
regression run) — but this preference is provisional on confirming the
comment-only diff really does rebuild byte-behaviourally-inert, and on
whether the added engine-rebuild risk is proportionate to a documentation-only
change. **(b) is an acceptable fallback** if (c) turns out to need touching
files outside this rung's declared scope, or if the rebuild is judged not
worth it for a comment-only change — this is exactly the kind of judgment
call this PREREG defers to the RESULTS doc rather than forcing in advance.

---

## 4. AR4 — no regression

Whatever gets landed (including "nothing"), re-run and paired-diff (failing
node-id lists, not counts) against the current `main` baseline:

- `tests/test_rules_checkpoint.py`
- `tests/test_persistence_migrated.py`

(the two `RULE_REFERENCE_LAYER_SIZING_RESULTS.md` §6 itself already confirmed
green under the unmodified engine — re-confirming here is the "did I break
anything" check, not a first discovery).

---

## 5. Provenance (to be filled in RESULTS)

Worktree: `/home/matt/ocelot-import-rules-no-mirror`, branch
`import-rules-no-mirror`, detached from `main` at `4f24abb` (verified at
worktree-creation time via `git log --oneline -1 main`). Engine sha256s (if
any rebuild happens), build commands, and coherence-probe output recorded in
the RESULTS doc per this folder's standing template.
