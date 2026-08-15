# NL construction of CAN network structure for `solve_can_relax`/`solve_can_exact`/`solve_can_bp` — PREREG

Base `main @ e313a20` ("Scope R6/R7: material barriers to leaving, and the
return cycle"), verified via `git log --oneline -1 main` immediately before
creating this worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/solver-can-adapter`, branch
`solver-can-adapter`. **`main` is shared with a concurrent, unrelated Bigville
research session today — this branch's own diff touches no file that session
is expected to land (`domains/solver_dispatch.py`, a new test file, this
doc); `main`'s tip will be re-checked at RESULTS time, not assumed static.**

## 0. What this task is checking, and the real skepticism it was assigned with

Three prior rungs (`SOLVER_NL_ADAPTER_PREREG/RESULTS.md`,
`SOLVER_ANALOGY_ADAPTER_PREREG/RESULTS.md`,
`SOLVER_DECOMPOSE_ADAPTER_PREREG/RESULTS.md`) each found the original
Rung-1 cost ranking for a resolver too pessimistic, once actually checked —
each time because a REUSABLE, ALREADY-SHIPPED mechanism existed that a
surface-level ranking missed (a construction seeded in
`reading_constructions.json` but grepped for under the wrong vocabulary; a
driver loop already production code; an adapter (`solve_deduction`) that was
NL-native since Rung 1 and never actually gated behind a graph object at
all). `SOLVER_NL_ADAPTER_PREREG.md` §2's own finding for the three CAN
resolvers was blunt: *"there is no path from raw NL text to a `params`
dict, let alone to a weighted causal edge, anywhere in this codebase...
inventing causal-relation-with-weight extraction from prose... a genuinely
new, large capability, not a small connector."*

This task's job is to check that finding a fourth time, with real
skepticism this time, not an assumed streak — a CAN network needs MULTIPLE
weighted Concept-to-Concept relationships, not one fact, which is
qualitatively different from what the prior three rungs each needed (exactly
ONE extracted relation per statement). **The honest possibility that this is
genuinely the big lift — real relation-polarity extraction, real
strength/weight extraction, real entity disambiguation, none of which has
existing machinery — was taken seriously and checked directly, not assumed
away.**

**Finding, stated up front: the pessimistic finding survives for WEIGHT-FROM-
LANGUAGE and NEW-CONCEPT-FROM-LANGUAGE (still genuinely unbuilt, still a real
lift — confirmed by reading, not re-litigated below) — but a narrower,
already-fully-mechanical composition DOES exist for NEW-EDGE-FROM-LANGUAGE
on an ALREADY-BUILT network's ALREADY-BUILT Concepts, and it was checked
LIVE, not assumed, before this document was finalised (§4-§6 below).** This
is the streak's fourth self-correction, but scoped narrower than any prior
one: it grows EDGES, not the whole network from nothing, and the new edges'
weight is NOT read off the sentence (it is the fixed +1 Hebbian constant an
already-shipped mechanism already mints) — exactly the shape the task's own
prompt named as the acceptable narrow scope, checked to actually be real
before building anything.

## 1. What each of the three CAN resolvers requires — read directly off
   `domains/solver_dispatch.py`

`mint_solve_can_relax_goal`/`mint_solve_can_exact_goal`/
`mint_solve_can_bp_goal` (`domains/solver_dispatch.py:174-211`) all take
`mt` and wire it via a `targets_mt` edge — the SAME graph-object
prerequisite `SOLVER_NL_ADAPTER_PREREG.md` §1 already found (unchanged).
The three resolvers themselves (`:686-798`) each read `targets_mt`, wall
honestly if absent, and otherwise call into `can_native_orchestration.
scoped_settle`/`multi_start_settle_and_pick_best` (relax),
`can_junction_tree.junction_tree_exact_settle` (exact), or
`can_native_bp.run_loopy_bp` (bp) — all three UNCHANGED, all three reading
the Mt's real, live `has_concept`/`causal_influence` graph structure at
dispatch time, not a cached snapshot. **This means: whatever edges exist on
`mt` at the moment the Goal is dispatched are what the resolver sees** — a
network GROWN between mint time and dispatch time is not a stale read, it is
exactly what gets solved.

## 2. `worlds/bigville_can_beliefs.py` — the only network BUILDER, and
   exactly how narrow it is

`build_resident_can_mt` (`worlds/bigville_can_beliefs.py:134-200`) mints one
`Microtheory` + 5 `Concept` nodes (`TOPIC_NAMES`, a FIXED list) +
exactly 5 structural `causal_influence` edges (`STRUCTURAL_EDGES`, a FIXED
`(concept_a, concept_b, base_j, nuance_key)` list) — entirely from an
ALREADY-DRAWN numeric `params` dict on a `bigville_cast100.json` resident
record. Confirmed, unchanged from the prior rung's own finding: **there is
no NL entry point into this function at all** — `resident["params"]` is
drawn by `bigville_town100_world.generate_cast100`, not read from text. This
remains the ONLY network-from-scratch builder in the codebase (grep for
`add_node.*Concept.*causal_influence`-shaped construction elsewhere found
nothing else — `tests/test_can_junction_tree.py::_fresh_resident_mt` and
`tests/test_solver_dispatch_migrated.py::_resident_mt` both call this SAME
function, not a second one). **This finding is UNCHANGED — no NL path exists
to mint a brand-new Concept or to set a structural edge's weight from a
sentence, and this document does not claim otherwise.**

## 3. `domains/can_native_orchestration.py` / `domains/can_junction_tree.py`
   — what a Microtheory needs populated before the resolvers can run

Both modules are pure, mechanical readers of an ALREADY-POPULATED Mt:
`can_junction_tree.can_network_from_mt` (`:79-125`) reads `has_concept`
Concepts and `causal_influence` edges into `(nodes, edges, unary, pairwise,
vocab)` via `Term("Edges"/"EdgeAttr")` evaluation — a pure read, no
mutation, confirmed by its own docstring and by direct read. `scoped_settle`
(`can_native_orchestration.py:128-151`) similarly operates over whatever
`has_concept`/`causal_influence` structure is present. **Neither module
requires the network to have been built any particular way** — a Mt built by
`build_resident_can_mt` and one whose edges were grown later by an entirely
different mechanism are equally valid inputs, confirmed by direct read (no
provenance check anywhere in either module).

## 4. `seeds/can_native_reimplementation.json` — the Hebbian mint-on-
   recurrence mechanism, and why it is the load-bearing discovery here

The task's own hint named this file directly: does `can_native_
reimplementation.json`'s hebbian-mint mechanism mint NEW edges from repeated
co-occurrence rather than from a single parsed sentence, and could a
sequence of extracted facts DRIVE it? **Checked by reading the rule bodies
directly, then confirmed live — yes, precisely that, and it composes.**

Two rules, Occam-ordered (`seeds/can_native_reimplementation.json:841-1306`):

- **`can_native_note_coactivation`** (`:841-1033`): two DISTINCT Concepts
  under the SAME Mt, both committed to the SAME NONZERO `state` sign, no
  `causal_influence` edge between them yet, no `Coactivation` ledger record
  for this pair yet → mints a `Coactivation{noted_tick: mt.can_tick}` record
  (bookkeeping only — first sight, no edge).
- **`can_native_hebbian_mint`** (`:1035-`): the SAME pair, an EXISTING
  `Coactivation` record noted on a STRICTLY EARLIER `mt.can_tick` (genuine
  cross-tick recurrence, not two matches inside one `run_rules()` fixpoint),
  STILL co-activated same-sign, STILL no edge → mints ONE `causal_influence`
  edge, weight **fixed at +1.0** (both directions, symmetric by
  construction) — "same-sign persistent co-activation ⇒ positive coupling."

**This is a real, already-shipped, edge-CREATION mechanism driven by
CO-OCCURRENCE across ≥2 distinct external ticks, not by parsing a relation
out of a sentence.** The weight is a hardcoded Hebbian constant (+1), never
read from language — exactly the "weight NOT extracted from language, just
co-occurrence-driven growth" scope the task's own prompt pre-approved as an
acceptable narrow build. `Concept.state` (the sign the mechanism keys on) is
itself computed by a THIRD rule in the same seed, `can_native_update_3state`
(`:102-`): a discrete-async Hopfield-style threshold update over
`external_field + identity_field + Σ(edge.weight × neighbour.state)`,
temperature-scaled against a fixed ±atanh(0.5) dead-zone. **`external_field`
is exactly the attr `reasoning_can_bridge.apply_derived_fact_as_can_evidence`
already writes** (`SOLVER_NL_ADAPTER_RESULTS.md` §4.1's own verified write
target) — so real NL evidence, applied via the ALREADY-SHIPPED,
ALREADY-UNCHANGED `apply_derived_fact_as_can_evidence`, can determine which
sign a Concept settles to, which in turn determines which PAIRS of Concepts
co-activate, which in turn determines which NEW edges the Hebbian mechanism
grows. **The composition chain is real, not speculative — confirmed live in
§6.**

**One real wrinkle, found and understood, not glossed over:**
`can_native_reimplementation.json` declares `"self_load_only": true`
(`substrate/boot_all.py:39`) — a normal `load_all_seeds()` boot does NOT
install these rules (by design: a data-only/on-demand seed must not pollute
every agent). The existing, ALREADY-SHIPPED precedent for installing it
alongside a real Bigville CAN network on a live substrate is
`tests/test_bigville_can_native_migration.py::_run_native` (`:94-110`):
`s.load_seed_manifest(engine_rules_only(manifest))` on the SAME substrate
`build_resident_can_mt` was called on. Confirmed live (§6) that this
composes unmodified on a FULL `WorldAdapter`+`load_all_seeds()` boot too
(not just the bare `_native.Substrate()` that file's own tests use) — the
reading pipeline (needed for NL extraction) and the CAN native engine rules
(needed for Hebbian growth) coexist on one substrate with zero conflict,
confirmed by direct measurement, not assumed compatible.

## 5. `domains/reasoning_can_bridge.py` — does repeated application drive
   growth the way `solve_decompose`'s adapter drove multiple sub-goals?

`apply_derived_fact_as_can_evidence(agent, entity, attr, positive=True,
alpha=1.0)` (`:187-231`, UNCHANGED, not touched by this rung) resolves the
entity's denoted Microtheory (the general `denotes` correspondence rule,
`ENTITY_RESOLUTION_RESULTS.md`), finds the Concept named `attr` inside it,
and calls the existing `concept_apply_evidence` PyO3 op
(`external_field += alpha * evidence`). It reweights/adjusts an EXISTING
Concept's evidence field — it does **not**, and this document does not
claim it does, create a new Concept or a new edge itself. **The genuinely
new finding is what happens when it is called REPEATEDLY over several
different `(entity, attr)` pairs on the SAME Mt, THEN the discrete-async +
Hebbian rules are ticked**: the network's own dynamics (not this function,
not any new Python decision) determine which Concepts land on the same
sign, and the Hebbian mechanism (§4) mints new edges for whichever pairs do
— exactly mirroring how `solve_decompose`'s own adapter drove multiple
`solve_deduction` sub-goals and let `race_projections`'s OWN `Argmin`
machinery decide the outcome, never a new Python decision about which
edges "should" exist.

**This is the "sequence of extracted facts DRIVING the hebbian-mint
mechanism" the task's own hint named, confirmed to be real composition, not
assumed.**

## 6. Live confirmation, BEFORE finalising anything — a real Bigville
   resident, real sentences, a real new edge, a real control

Run against a real `WorldAdapter` boot (`load_all_seeds`), `worlds.
bigville_can_beliefs.build_resident_can_mt` (UNCHANGED, resident 1, "Ida
Ditchwater", `seeds/bigville_cast100.json`), with `can_native_
reimplementation.json`'s engine rules additionally loaded on the SAME
substrate (`engine_rules_only` + `load_seed_manifest`, the exact
`_run_native` precedent, §4).

**Step 1 — baseline (scenario evidence only, no adapter text yet).** After
`apply_scenario_evidence` (UNCHANGED, the SAME fixed evidence every existing
CAN test/demo applies) + one settle tick (`can_tick=0`) + one growth tick
(`can_tick=1`, letting whatever ALREADY co-activates mint its baseline
Hebbian edges): **6 of the 10 possible undirected Concept pairs are
connected** (`can_junction_tree.can_network_from_mt`, a pure read, confirms
this by direct edge count). `self_worth` and `debtor_trustworthy` are both
ambivalent (`state=0`) at this point — no coactivation possible, no edge.

**Step 2 — real NL evidence, via the UNMODIFIED reasoning-bridge parse
chain.** Two real declarative sentences about the SAME resident:

```
"Ida Ditchwater is self worth."          -> read_clause -> [['is_a','ida_ditchwater','self_worth']]
"Ida Ditchwater is debtor trustworthy."  -> read_clause -> [['is_a','ida_ditchwater','debtor_trustworthy']]
```

(the SAME multi-word noun-phrase joining `SOLVER_NL_ADAPTER_RESULTS.md`
§4.1 already demonstrated for "world safe" → `world_safe`, here for
"debtor trustworthy" → `debtor_trustworthy`.) Both extracted `(entity,
attr)` pairs applied via the UNCHANGED `apply_derived_fact_as_can_evidence`
(`positive=True, alpha=1.0`); both report `applied: True`.

**Step 3 — a real engine mechanic, found live, not assumed.**
`concept_apply_evidence` is a host-side PyO3 write, not a rule effect — it
does **not** automatically mark the touched Concept dirty for `run_rules()`'s
incremental matching (confirmed live: `run_rules()` called immediately after
applying evidence reports `steps=0`, no state change). The fix is
`native.force_all_dirty()` before re-driving — an ALREADY-ESTABLISHED house
idiom, not a new discovery: confirmed by grep, used identically in **20+
existing call sites** across `worlds/bigville_*_world.py` and multiple
`tests/test_*_migrated.py` files (e.g. `worlds/bigville_economy_world.py:99`,
`worlds/bigville_flow_world.py:32`, `tests/test_theft_migrated.py:395`).
This rung's driver reuses the SAME idiom, not a new one.

**Step 4 — two more distinct `can_tick` epochs, mechanically bumped.**
`can_tick=2` (note), `can_tick=3` (mint on recurrence) — matching exactly
the ≥2-distinct-tick recurrence contract §4 read off the rule bodies.

**Result, measured, not assumed:**

```
BEFORE (step 1):  6 undirected edges
AFTER  (step 4):  9 undirected edges
NEW pairs:  (claim_credible, self_worth), (world_safe, debtor_trustworthy),
            (self_worth, debtor_trustworthy)
```

Three genuinely NEW `causal_influence` edges (6 new directed edges,
symmetric pairs), weight +1.0 each, minted by the UNCHANGED Hebbian
mechanism, as a direct, traceable consequence of two real natural-language
sentences. **None of these three pairs are in `build_resident_can_mt`'s own
`STRUCTURAL_EDGES` template** — this is genuinely new network STRUCTURE,
not a reweighting of something the hand-authored template already declared.

**Control, run live, not assumed unnecessary:** the SAME resident, the SAME
tick schedule (`can_tick` 0→1→2→3→...→7), with **no evidence applied at
all** — `self_worth`/`debtor_trustworthy` remain ambivalent (`state=0`)
through every tick out to tick 7, and the `(self_worth, debtor_trustworthy)`
edge never appears. **The growth is caused by the applied text evidence, not
by continued ticking alone** — ruling out the "would have happened anyway"
confound before claiming causation.

**Downstream resolver dispatch, live, on the GROWN network.** After growth,
`mint_solve_can_exact_goal` (UNCHANGED) dispatched through the UNCHANGED
`qd_bind_resolver` → `solve_can_exact` (UNCHANGED) →
`junction_tree_exact_settle` (UNCHANGED) runs the EXACT global-MAP inference
over the now-9-edge network: `status: resolved`, `treewidth: 3.0`, a real
computed `energy`, and an exact MAP assignment
(`self_worth: +1, debtor_trustworthy: +1, claim_credible: +1, world_safe:
+1, trust_mayor: -1`) — the two evidenced Concepts land exactly on the sign
the applied evidence pushed them toward, verified by hand against the
resolver's own returned state, not merely `status == "resolved"`.

## 7. So: GO, narrowly scoped, or NO-GO? — the actual verdict

**GO, narrowly scoped**, matching the task's own pre-approved shape exactly:
grow `causal_influence` EDGES between Concepts an already-built network
already has, driven by real NL evidence sentences feeding the
ALREADY-SHIPPED discrete-relaxation + Hebbian mint-on-recurrence mechanism,
weight fixed at the mechanism's own +1 constant (never extracted from
language). This is **not** "construct a whole CAN network from a
description" — that capability remains genuinely absent (§2, unchanged
finding) and is named as NOT built here, precisely and honestly, in the
RESULTS doc's own "does not establish" section. What IS real: a sequence of
plain declarative fact sentences about an EXISTING resident's EXISTING
belief network can cause that network's own STRUCTURE (not just its
Concepts' evidence fields) to grow, through composition of five
already-shipped, already-tested, UNCHANGED mechanisms:
`reading_collapse.read_clause` + `situation_model_reader._is_property_pred`
+ `propositional_deduction._norm_attr` (the SAME parse triple
`SOLVER_NL_ADAPTER_RESULTS.md` already reused) → `reasoning_can_bridge.
apply_derived_fact_as_can_evidence` (UNCHANGED) → `can_native_
reimplementation.json`'s discrete-async + Hebbian rules (UNCHANGED,
self_load_only, existing `_run_native`-precedented load path) →
`can_junction_tree`/`can_native_orchestration`/`can_native_bp` (all
UNCHANGED, pure readers of whatever structure is live) → `mint_solve_can_
relax_goal`/`exact`/`bp` (all UNCHANGED).

## 8. What will be built

`domains/solver_dispatch.py`, a new function
`grow_can_network_from_text(adapter, mt, statements: list, *, alpha: float =
1.0) -> Optional[dict]`, plus a small idempotent-guarded helper
`ensure_can_native_engine_loaded(adapter) -> bool` (loads `seeds/can_native_
reimplementation.json`'s engine rules onto `adapter.inner` exactly once per
substrate — confirmed live, §6, that calling `load_seed_manifest` on this
manifest TWICE on the same substrate DOUBLES the rule count and would
double-fire every effect; the guard checks `adapter.inner.export_rules()`
for the presence of `can_native_hebbian_mint` by name before loading,
mirroring the `_has_concept`-sentinel idempotency idiom `reasoning_can_
bridge._ensure_correspondence_seed` already uses for a structurally
identical problem).

`grow_can_network_from_text`:

1. **Precondition, not silently patched.** `mt` must already have
   `discrete_mode` set to `"3state"` or `"2state"` (the caller's own,
   already-configured choice — matching `_resident_mt`'s own setup
   contract exactly); an absent `discrete_mode` is mechanically defaulted to
   `"3state"`/`can_tick=0` (matching every existing test/demo's own default
   choice); a `discrete_mode` set to anything ELSE (e.g. `"static"`,
   deliberately used elsewhere in this codebase to isolate item-4 from
   item-3, §6's own control precedent) is an honest DECLINE (`None`) — the
   caller has explicitly opted the Mt out of discrete relaxation, and this
   function must not silently override that.
2. **Pure pre-check, zero mutation** (mirroring `_would_parse_as_deduction`'s
   own precedent exactly): for each statement, `read_clause` → decline this
   ONE statement (not the whole call) if `speech_act=="question"`, no
   predication, or the leading predication is not a property predication
   (`situation_model_reader._is_property_pred`) — the SAME three gates
   `mint_solve_reasoning_bridge_goal_from_text` already established, copied
   here as this rung's OWN small local helper (`_extract_property_fact`,
   "same pattern, own cache — no cross-import", the established house
   convention), not by editing or importing that function (mirrors why
   `_would_parse_as_deduction` is its own copy of `solve_deduction`'s own
   parse ladder rather than a shared import).
3. **Decline (`None`, zero mutation) if fewer than 2 statements survive the
   pre-check** — cannot demonstrate co-occurrence-driven growth from 0-1
   facts (mirrors `solve_decompose`'s own "at least 2" floor for the
   identical structural reason: growth needs a PAIR).
4. **Apply evidence for real**, via the UNCHANGED
   `apply_derived_fact_as_can_evidence`, for each statement that survived
   the pre-check — track which actually reported `applied: True` AND whose
   resolved Concept is a real member of the CALLER's own `mt` (a defensive
   re-check against the entity-resolution machinery's own name-based
   ambiguity risk, `ENTITY_RESOLUTION_RESULTS.md`'s already-documented,
   unchanged residual — verified live in this rung's own investigation that
   two same-named Resident networks on one substrate can resolve
   ambiguously; scoped around, not fixed, by requiring the resolved
   Concept's own `has_concept` membership match the CALLER's `mt`
   explicitly).
5. **Honest, documented departure from a "zero mutation on ANY decline"
   guarantee** — the SAME departure `SOLVER_DECOMPOSE_ADAPTER_RESULTS.md`
   §4 already documented and justified for the identical structural reason
   (the suitability signal is only knowable by actually applying evidence):
   if fewer than 2 of the pre-checked statements actually applied
   (concept-not-found is a REAL, reachable miss,
   `apply_derived_fact_as_can_evidence`'s own honest-miss path), returns a
   dict reporting `grown: False` with the reason — not `None` — because
   real evidence may already have been applied for the ones that DID
   succeed.
6. **Drive the growth loop** — `native.force_all_dirty()` +
   `native.run_rules()` to settle discrete state from the newly-applied
   evidence, then advance `mt.can_tick` by exactly 2 more distinct steps
   (mechanical epoch bumps, matching `shape_decode_loop.json`'s own
   `codebook_epoch` idiom precedent already named throughout this seed's
   own comments), `run_rules()` after each — a FIXED, small, bounded
   schedule (never a data-dependent decision about how many ticks to run),
   mirroring `solve_decompose`'s own `_drive_to_resolution` bounded-loop
   precedent exactly.
7. **Report what actually grew**, measured via `can_junction_tree.
   can_network_from_mt` (UNCHANGED, pure read) BEFORE and AFTER the growth
   loop — `{"grown": bool, "new_edges": [...], "applied": [...],
   "before_edge_count": int, "after_edge_count": int}` — never a claim
   about what "should" have grown, only what a before/after diff of the
   real graph state shows.

**Composes with, does not touch:** `mint_solve_can_relax_goal`/`exact`/`bp`
(all three byte-unchanged) — a caller mints one of these on the SAME `mt`
AFTER calling `grow_can_network_from_text`, dispatching through the
UNCHANGED `qd_bind_resolver` exactly as every other caller already does.

## 9. Live demonstration plan (to run and report in RESULTS)

- **Success**: real resident, real sentences (§6's own Ida
  Ditchwater/self_worth/debtor_trustworthy case, reproduced end-to-end
  through the actual built function, not the exploratory script) → `grown:
  True`, 3 new pairs → `mint_solve_can_exact_goal` on the SAME `mt` →
  `status: resolved`, a real treewidth/energy/MAP state, verified by hand
  against the evidence's own expected sign — reproduced additionally through
  `solve_can_relax` and `solve_can_bp` (both UNCHANGED) on the same grown
  network, to confirm growth composes with all three CAN resolvers, not
  just one.
- **Control**: the identical resident/tick schedule with NO evidence
  applied — confirms the SAME pairs do NOT grow without text, ruling out
  "would have happened anyway."
- **Honest decline (adapter-side, zero mutation)**: fewer than 2 suitable
  statements; a question-shaped statement; a non-property-predication
  statement; an `mt` whose `discrete_mode` is `"static"`.
- **Honest wall (resolver-side, after real partial mutation)**: a statement
  whose attr does not name any Concept in the target Mt (mirrors
  `apply_derived_fact_as_can_evidence`'s own existing honest-miss path,
  unchanged).

## 10. Regression plan

`tests/test_solver_dispatch_migrated.py`, `tests/test_solve_gap_awareness_
migrated.py`, `tests/test_problem_shape_migrated.py`, `tests/test_solver_
math_boundary.py`, `tests/test_solver_nl_adapter.py`, `tests/test_solver_
analogy_adapter.py`, `tests/test_solver_decompose_adapter.py`, `tests/test_
can_junction_tree.py`, `tests/test_can_loopy_bp.py`, `tests/test_can_native_
reimplementation.py`, `tests/test_bigville_can_native_migration.py`, plus a
new `tests/test_solver_can_adapter.py` for this rung's own live
demonstrations — all green, fresh (not from `results/failure_baseline.json`),
before declaring GO final. No Rust touched by this rung (confirmed by diff
before RESULTS is written) — no `cargo build`/`cargo test` needed, but the
task's own house discipline names it as a fallback if that assumption turns
out wrong; will be run if any Rust file changes.

## 11. What this document does NOT establish, named up front rather than
    discovered late

1. **No NL path to a brand-new Concept.** This rung's adapter only applies
   evidence to Concepts an already-built Mt already has; it never mints a
   new `Concept` node. A sentence naming a topic outside the resident's
   fixed 5-topic template cannot be represented at all.
2. **No NL path to a weighted edge whose weight is READ from the sentence.**
   The Hebbian mechanism's +1 constant is fixed by the mechanism, not by
   anything in the text — "X strongly influences Y" and "X slightly
   influences Y" would (if they parsed as property predications at all,
   which they likely would not — untested) produce the identical +1.0 edge.
   Real relation-polarity/strength extraction from prose remains unbuilt,
   confirmed absent, not sized here.
3. **No NL path to build a Mt/network from nothing.** `build_resident_can_mt`
   remains the only from-scratch builder, still entirely numeric-params-
   driven, still with no NL entry point.
4. **Growth topology is emergent, not sentence-specified.** Which NEW edges
   appear is decided by the network's OWN relaxation dynamics (which
   Concepts land on the same sign), not by the adapter or by anything the
   sentence literally names — "Ida is self worth" and "Ida is debtor
   trustworthy" do not directly assert "self_worth influences
   debtor_trustworthy"; that pairing emerges because both settled to the
   same sign. This is a real, structural difference from a hypothetical
   "X influences Y" direct-parse adapter, named honestly rather than
   overclaimed.
5. **Entity/Mt resolution ambiguity is inherited, unmodified, unfixed.**
   `apply_derived_fact_as_can_evidence`'s own name-based `denotes`
   resolution can resolve ambiguously if two same-named Resident networks
   exist on one substrate (found live during this rung's own investigation,
   §6) — this rung's defensive re-check (§8 item 4) detects and excludes a
   mismatch for ITS OWN success accounting, but does not fix the underlying
   resolution mechanism, which is `ENTITY_RESOLUTION_RESULTS.md`'s own
   already-documented, separate concern.
6. **Synthetic-proven mechanism ≠ benchmark value**, per house standard:
   every number in this document is a mechanism demonstration on one real
   resident/sentence pair, not a coverage claim over how often
   naturally-occurring fact sequences would grow a network this way.
