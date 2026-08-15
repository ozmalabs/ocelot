# NL construction of CAN network structure for `solve_can_relax`/`solve_can_exact`/`solve_can_bp` — RESULTS

Prereg: `SOLVER_CAN_ADAPTER_PREREG.md`, same worktree/branch, base
`main @ e313a20` ("Scope R6/R7: material barriers to leaving, and the
return cycle"), verified via `git log --oneline -1 main` immediately before
creating the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/solver-can-adapter`, branch
`solver-can-adapter`, commits `98d2013` (PREREG), `cc87408` (implementation
+ tests), `9a38c37` (test fixes found by actually running the suite).
`data/` was absent in the fresh worktree (not a partial real directory);
symlinked (`ln -sfn /home/matt/ozmadev/ocelot/data data`) and confirmed
`data/wiktionary/en.jsonl.gz` resolves to the real 492,560,156-byte file.
`main`'s tip moved to `332feb6` while this rung was in flight (a
concurrent, unrelated session, per the task's own standing warning) — this
rung's own diff (`docs/research/engine_substrate/SOLVER_CAN_ADAPTER_
PREREG.md`, `domains/solver_dispatch.py`, `tests/test_solver_can_adapter.py`)
touches no file that session is expected to land.

**Headline finding: the pessimistic Rung-1 finding for the three CAN
resolvers survives for its two hardest claims — no NL path to a brand-new
Concept, no NL path to a weight READ FROM a sentence — but a narrower,
already-fully-mechanical composition DOES exist for growing genuinely NEW
`causal_influence` EDGE structure on an already-built network, and it is
GO, live-demonstrated, not merely argued for.** Five already-shipped,
UNCHANGED mechanisms compose: the same parse triple the reasoning-bridge
adapter already established (`reading_collapse.read_clause` +
`situation_model_reader._is_property_pred` + `propositional_deduction.
_norm_attr`) → `reasoning_can_bridge.apply_derived_fact_as_can_evidence`
(UNCHANGED) → `seeds/can_native_reimplementation.json`'s discrete-relaxation
+ Hebbian mint-on-recurrence rules (UNCHANGED, `self_load_only`, loaded via
the exact `test_bigville_can_native_migration.py::_run_native` precedent) →
`can_junction_tree.can_network_from_mt` (UNCHANGED, pure read) →
`mint_solve_can_relax_goal`/`exact`/`bp` (all three byte-unchanged).
Live-demonstrated on real Bigville residents, real sentences, a real
before/after edge-set diff, a real CONTROL ruling out "would have happened
anyway," and a real MAP-inference dispatch through the unmodified
`solve_can_exact` resolver whose exact-solved state matches the applied
evidence's own sign.

**This is the arc's fourth self-correction of an original Rung-1 ranking —
but the narrowest one, and the one built with the most explicit
skepticism.** Unlike the prior three (each of which found the FULL
capability was already cheap), this rung's own §11 names, precisely, what
remains genuinely absent: constructing a network's Concepts from nothing,
and reading a relation's polarity/strength off a sentence. Both are
confirmed still unbuilt below, not silently dropped.

---

## 1. What was investigated, and what the investigation actually found

Read directly, per the task's own instruction, before writing any code:

- **`domains/solver_dispatch.py`** — `mint_solve_can_relax_goal`/
  `mint_solve_can_exact_goal`/`mint_solve_can_bp_goal`
  (`:174-211` pre-rung) all require a `targets_mt` edge to an
  already-populated `Microtheory`; the three resolvers (`:686-798`
  pre-rung) read that Mt's LIVE structure at dispatch time — a network
  grown between mint and dispatch is not a stale read, confirmed by direct
  read of all three resolver bodies.
- **`worlds/bigville_can_beliefs.py`** — `build_resident_can_mt` remains the
  ONLY network-FROM-SCRATCH builder in the codebase, and it is STILL a pure
  mechanical translation of an already-drawn numeric `params` dict
  (`TOPIC_NAMES`/`STRUCTURAL_EDGES`, both fixed Python lists) — **this
  finding is unchanged from the prior rung.** No NL entry point exists into
  this function, confirmed again by direct read, not re-litigated as if it
  might have changed.
- **`domains/can_native_orchestration.py`/`domains/can_junction_tree.py`** —
  both are pure, mechanical readers of whatever `has_concept`/
  `causal_influence` structure a Mt has at call time, with no provenance
  check anywhere — confirmed by direct read that a Mt whose edges were
  grown by a DIFFERENT mechanism than `build_resident_can_mt`'s own
  template is an equally valid input.
- **`seeds/can_native_reimplementation.json`'s hebbian-mint mechanism** —
  the task's own named hint. Confirmed by reading the rule bodies directly
  (PREREG §4): `can_native_note_coactivation`/`can_native_hebbian_mint` mint
  a genuinely NEW `causal_influence` edge (fixed +1.0 weight — a Hebbian
  constant, never read from language) between two Concepts once they
  co-activate to the SAME NONZERO sign across ≥2 DISTINCT external ticks.
  The sign a Concept settles to is computed (by a third rule in the same
  seed, `can_native_update_3state`) from `external_field` — the EXACT attr
  `reasoning_can_bridge.apply_derived_fact_as_can_evidence` already writes.
  **This chain — NL evidence → discrete relaxation → Hebbian mint — is the
  load-bearing discovery, and it was confirmed live (§4 below) before being
  relied on for anything.**
- **`domains/reasoning_can_bridge.py`** — `apply_derived_fact_as_can_
  evidence` reweights/adjusts an EXISTING Concept's evidence field; it does
  NOT, and this rung does not claim it does, create a new Concept or a new
  edge by itself. What was checked and confirmed: calling it REPEATEDLY
  over several `(entity, attr)` pairs on the SAME Mt, then driving the
  discrete-async + Hebbian rules, lets the network's OWN dynamics (never a
  new Python decision) determine which Concepts co-activate and therefore
  which new edges the Hebbian mechanism mints — mirroring exactly how
  `solve_decompose`'s own adapter drove multiple sub-goals and let
  `race_projections`'s OWN `Argmin` decide the outcome.

## 2. Live confirmation, before finalising the ranking (PREREG §6,
   reproduced end-to-end via the actually-built function here)

Real `WorldAdapter` boot (`load_all_seeds`), a real Bigville resident
(`seeds/bigville_cast100.json` index 1, "Ida Ditchwater"), `worlds.
bigville_can_beliefs.build_resident_can_mt` (UNCHANGED) +
`seeds/can_native_reimplementation.json`'s engine rules loaded onto the
SAME substrate via the new, idempotent `ensure_can_native_engine_loaded`
(§3).

```
BEFORE growth (scenario evidence + one settle tick + one baseline-growth
tick, exactly matching every existing test/demo's own setup):
  6 of 10 possible undirected Concept pairs connected
  self_worth=0 (ambivalent), debtor_trustworthy=0 (ambivalent)

grow_can_network_from_text(agent, mt,
    ["Ida Ditchwater is self worth.", "Ida Ditchwater is debtor trustworthy."])
  -> {"grown": True, "applied": [("ida_ditchwater","self_worth"),
      ("ida_ditchwater","debtor_trustworthy")],
      "before_edge_count": 6, "after_edge_count": 9,
      "new_edges": [3 new undirected pairs]}

AFTER growth: 9 of 10 possible pairs connected. New pairs:
  (claim_credible, self_worth), (world_safe, debtor_trustworthy),
  (self_worth, debtor_trustworthy)
```

**None of these three pairs are in `build_resident_can_mt`'s own
`STRUCTURAL_EDGES` template** (verified programmatically in
`test_grow_from_text_mints_genuinely_new_edges_not_in_the_template`,
checking every new pair's names against the template's own pair set) — this
is genuinely new network structure, not a reconfirmation of the
hand-authored template.

**Control, run live, same tick schedule, zero evidence applied** (resident
9, "Gristle Bracken" — measured to leave BOTH `self_worth` and
`debtor_trustworthy` at `state=0` after scenario evidence alone, unlike
several other residents whose networks fully self-connect from scenario
evidence with no adapter involvement at all — see §6 item 2 for the
residual this asymmetry left in the test suite): the target pair's own
`causal_influence` edge never appears across `can_tick` 2 through 7.
**The growth is caused by the applied text evidence, not by continued
ticking alone.**

**Downstream resolver dispatch on the grown network** (resident 2, "Garnet
Hollow", `test_grown_network_dispatches_through_solve_can_exact_correctly`):
`mint_solve_can_exact_goal` (UNCHANGED) → `qd_bind_resolver` (UNCHANGED) →
`solve_can_exact` (UNCHANGED) → `junction_tree_exact_settle` (UNCHANGED)
resolves the EXACT global-MAP inference over the grown network:
`status: resolved`, and the exact MAP assignment gives
`self_worth == +1.0` and `debtor_trustworthy == +1.0` — **the two
text-evidenced Concepts land exactly on the sign the applied evidence
pushed them toward**, verified by hand against the resolver's own returned
`state` dict, not merely `status == "resolved"`. `solve_can_relax` and
`solve_can_bp` (both UNCHANGED) were separately confirmed to dispatch and
resolve on a grown network too (resident 8, "Wat Bracken",
`test_grown_network_dispatches_through_solve_can_relax_and_bp`).

## 3. What was built

`domains/solver_dispatch.py` (added after `mint_solve_can_bp_goal`, before
`mint_solve_reasoning_bridge_goal`):

1. **`ensure_can_native_engine_loaded(adapter) -> bool`** — an idempotent
   loader for `seeds/can_native_reimplementation.json`'s engine rules onto
   the live substrate (the file is `self_load_only`, so a normal
   `load_all_seeds()` boot never installs it — the SAME existing
   `_run_native` (`tests/test_bigville_can_native_migration.py:94-110`)
   `engine_rules_only` + `load_seed_manifest` call path, reused, guarded).
   **The guard is load-bearing, not decorative**: confirmed live before
   writing this function that calling `load_seed_manifest` on this
   manifest TWICE on one substrate DOUBLES the rule count (6 → 12) and
   would double-fire every effect. The sentinel is `can_native_hebbian_
   mint`'s presence-by-name in `native.export_rules()` — the same
   `_has_concept`-sentinel idempotency idiom `reasoning_can_bridge.
   _ensure_correspondence_seed` already uses for a structurally identical
   problem, applied to a rule name here because this seed's own natural
   sentinel is a rule, not a Concept.
2. **`_extract_property_fact(adapter, statement) -> tuple | None`** — a
   pure, zero-mutation parse (`(entity, attr)` or `None`), a local "own
   copy" of the SAME three gates `mint_solve_reasoning_bridge_goal_
   from_text` already established (question-shaped decline,
   property-predication gate, non-empty extraction) — a fresh duplicate,
   not a shared import or an edit to that prior rung's own function,
   mirroring the house convention `_would_parse_as_deduction` already set.
3. **`grow_can_network_from_text(adapter, mt, statements, *, alpha=1.0,
   extra_ticks=2) -> dict | None`** — the adapter itself:
   - **Precondition** (honest decline, not silently patched): `mt.
     discrete_mode` must already be `"3state"`/`"2state"`, or is
     mechanically defaulted to `"3state"`/`can_tick=0` if entirely absent;
     an EXPLICITLY different value (e.g. `"static"`, used elsewhere in this
     codebase to isolate item-4 from item-3's relaxation rules) is an
     honest decline (`None`) — this function never overrides a caller's own
     explicit configuration.
   - **Pure pre-check** over every statement via `_extract_property_fact`
     (zero mutation); declines (`None`) if fewer than 2 survive — the same
     "at least 2" floor `solve_decompose`'s own adapter uses, for the
     identical structural reason (growth needs a pair).
   - **Real application** via the UNCHANGED `apply_derived_fact_as_can_
     evidence` for each surviving pair, counted as a hit only if it BOTH
     reports `applied: True` AND resolves to a Concept that is an actual
     `has_concept` member of the CALLER's OWN `mt` (a defensive re-check
     against `apply_derived_fact_as_can_evidence`'s own name-based
     resolution, which — found live during this rung's own investigation,
     not assumed — can resolve ambiguously if two same-named `Resident`
     networks exist on one substrate; scoped around for THIS function's own
     accounting, not fixed at the source). Fewer than 2 real hits returns a
     `{"grown": False, "reason": ..., "applied": [...]}"` dict, not `None`
     — the SAME documented, honest departure from a zero-mutation-on-ANY-
     decline guarantee `SOLVER_DECOMPOSE_ADAPTER_RESULTS.md` §4 already
     made and justified for the identical reason (the suitability signal is
     only knowable by actually applying evidence).
   - **Drive**: `native.force_all_dirty()` (a REAL, found-live engine
     mechanic, not assumed: `concept_apply_evidence` is a host-side PyO3
     write that does NOT mark a Concept dirty for `run_rules()`'s
     incremental matching — confirmed live, `run_rules()` immediately after
     applying evidence reports `steps=0` with no state change; the fix
     reuses an ALREADY-ESTABLISHED house idiom, confirmed by grep to be
     used identically at 20+ existing call sites across `worlds/bigville_
     *_world.py` and several `tests/test_*_migrated.py` files) +
     `run_rules()`, then `extra_ticks` (default 2, the measured-live-
     necessary minimum for genuine cross-tick recurrence) more distinct
     `can_tick` epochs, each mechanically bumped + ticked — a FIXED,
     bounded schedule, never a data-dependent decision.
   - **Report**: before/after edge sets via `can_junction_tree.can_
     network_from_mt` (UNCHANGED, pure read) bracket the drive step;
     returns `{"grown": bool, "new_edges": [...], "applied": [...],
     "before_edge_count": int, "after_edge_count": int}`.

**Composes with, does not touch:** `mint_solve_can_relax_goal`/`exact`/`bp`
(byte-unchanged) — a caller mints one of these on the SAME `mt` AFTER
calling `grow_can_network_from_text`, dispatching through the UNCHANGED
`qd_bind_resolver` exactly as every other caller already does.
`apply_derived_fact_as_can_evidence`, `can_native_reimplementation.json`'s
rule bodies, `can_junction_tree.py`, `can_native_orchestration.py`,
`can_native_bp.py`, and `worlds/bigville_can_beliefs.py` are all
byte-unchanged — confirmed by `git diff` (§5).

## 4. A real bug the investigation itself caught before it shipped, and a
   real test-selection error the FIRST test run caught (not glossed over)

**During PREREG investigation (before any code was written):** building two
CAN networks for two DIFFERENT residents named "Ida Ditchwater" on the same
substrate (an early exploratory mistake) caused `apply_derived_fact_as_can_
evidence`'s own name-based `denotes` resolution to resolve ambiguously,
silently applying evidence to the WRONG network. This is exactly
`ENTITY_RESOLUTION_RESULTS.md`'s own already-documented residual, rediscovered
live rather than assumed away — it is why `grow_can_network_from_text`'s own
step 3 re-verifies the resolved Concept is actually a member of the
CALLER's `mt`, not merely that `apply_derived_fact_as_can_evidence` reported
`applied: True`.

**On the FIRST real test run (not a rehearsal — the actual regression
command, reported honestly rather than silently re-run until green):**
3 of 9 new tests failed, for three distinct, real reasons, all found by
running, not by inspection:

1. `can_junction_tree.can_network_from_mt`'s own edge tuples are plain
   Python ints (its own `node_by_id` convention), not `NodeID` objects —
   `agent.s.node(<int>)` raises `TypeError` (`substrate_rs.Substrate.node`
   requires a real `NodeID`). Fixed by resolving names through the SAME
   `concepts_by_id` reverse-map idiom every other test in the file already
   uses, not by changing the adapter (the adapter itself never had this
   bug — only the test's own name-resolution helper did).
2. Resident 3 ("Alby Marsh") has a real, HONEST reading-pipeline collision:
   "Alby Marsh is self worth." mis-grounds to `[['has_property','l',
   'marsh']]` — "Marsh" hits a common-noun lexicon entry, and the general
   construction grammar picks a different, wrong construction for the whole
   clause. This is not a defect in this rung's adapter; the adapter's own
   honest decline on this unparseable input is CORRECT. Swapped the test to
   a resident without this collision (index 8, "Wat Bracken") and documented
   the finding in the test file rather than silently switching residents.
3. The control test's ORIGINAL resident choice (index 4, "Bryony Turnbull")
   turned out — measured only by actually running the test — to already
   have ALL five Concepts co-activated to the same sign from scenario
   evidence alone, so the target pair minted at the baseline growth tick
   with **zero adapter involvement**, exactly the "would have happened
   anyway" confound the control exists to rule out. Swapped to resident 9
   ("Gristle Bracken"), confirmed live to leave both Concepts genuinely
   ambivalent (`state=0`) without text evidence.

All three fixes are recorded in a separate commit (`9a38c37`) rather than
folded into the implementation commit, so the actual defect-and-fix history
is visible, not smoothed over.

## 5. Regression

```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest tests/test_solver_can_adapter.py -q -p no:randomly
.........
9 passed in 300.02s (0:05:00)

$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
    tests/test_solver_dispatch_migrated.py tests/test_solve_gap_awareness_migrated.py \
    tests/test_problem_shape_migrated.py tests/test_solver_math_boundary.py \
    tests/test_solver_nl_adapter.py tests/test_solver_analogy_adapter.py \
    tests/test_solver_decompose_adapter.py tests/test_can_junction_tree.py \
    tests/test_can_loopy_bp.py tests/test_can_native_reimplementation.py \
    tests/test_bigville_can_native_migration.py tests/test_solver_can_adapter.py \
    -q -p no:randomly
123 passed in 379.82s (0:06:19)
```

**123/123 green across all twelve task-named suites, zero regressions, zero
waivers.**

```
$ git diff --stat e313a20 HEAD
 .../engine_substrate/SOLVER_CAN_ADAPTER_PREREG.md  | 453 ++++++++++++++++++
 domains/solver_dispatch.py                         | 235 +++++++++
 tests/test_solver_can_adapter.py                   | 266 +++++++++++
 3 files changed, 954 insertions(+)

$ git diff --stat e313a20 -- '*.rs'
(empty)
```

No Rust touched — confirmed by diff, not assumed; no `cargo build`/`cargo
test` run (the task's own house discipline names this as conditional on a
Rust change, which did not happen). Purely additive Python diff —
`solve_can_relax`/`solve_can_exact`/`solve_can_bp`, `apply_derived_fact_as_
can_evidence`, every rule body in `can_native_reimplementation.json`, and
`build_resident_can_mt` are all byte-unchanged. No seed file was modified —
the grown network dispatches through the UNCHANGED `qd_bind_resolver` JOIN
and the already-installed `solve_can_relax`/`solve_can_exact`/`solve_can_bp`
Resolvers (`seeds/solver_dispatch.json`, untouched).

## 6. GO / NO-GO

**GO, narrowly scoped** — matching the task's own pre-approved shape:
`grow_can_network_from_text` grows real `causal_influence` EDGE structure
between Concepts an already-built CAN network already has, driven by real
NL evidence sentences composed entirely of already-shipped, unchanged
mechanisms, with the new edges' weight fixed at the Hebbian mechanism's own
+1.0 constant — never extracted from language. Live-demonstrated: a real
before/after edge-set diff on a real Bigville resident from two real
sentences; a real control ruling out "would have happened anyway"; a real
dispatch through the unmodified `solve_can_exact` resolver whose exact
MAP-solved state matches the evidence's own sign, plus separate live
confirmation that `solve_can_relax`/`solve_can_bp` dispatch correctly on a
grown network too. 123/123 regression tests green, fresh, across twelve
suites. The diff is purely additive.

**This is NOT** "construct a whole CAN network from a description" — that
capability (new Concepts from text; a weight read off a sentence's own
polarity/strength) remains genuinely, confirmedly absent, and is named
precisely in §7 below rather than silently claimed solved. The original
Rung-1 finding that a full from-scratch NL→CAN-network path is a
substantial new capability, not a connector, **survives this
investigation** for those two specific claims — this rung found a real,
narrower, honestly-scoped capability sitting one level down from that
claim, not a refutation of it.

**Not merged, not pushed to `main`.** `main`'s tip was checked fresh
(`e313a20`) immediately before creating this worktree, and every commit
(`98d2013`, `cc87408`, `9a38c37`) lives on the `solver-can-adapter` branch
only. `main` has since advanced to `332feb6` via a concurrent, unrelated
session — this branch's own diff touches no file that session is landing.
This rung did not run any command that touched `main` at any point. The
orchestrator performs the merge.

---

## 7. What this document does NOT establish

1. **No NL path to a brand-new Concept.** `grow_can_network_from_text` only
   ever applies evidence to Concepts an already-built Mt already has; it
   never mints a `Concept` node. A sentence about a topic outside the
   resident's fixed 5-topic template (`TOPIC_NAMES`) cannot be represented
   at all — confirmed by construction, not merely asserted.
2. **No NL path to a weight READ from the sentence.** The Hebbian
   mechanism's edge weight is a fixed +1.0 constant, set by the mechanism,
   never by anything in the applied text. "X strongly influences Y" and "X
   slightly influences Y" would (if either parsed as a property predication
   at all — untested, and likely they would not, since neither is a bare
   copular "X is Y" clause the existing reading pipeline's property-
   predication gate accepts) produce the identical +1.0 edge. Real
   relation-polarity/strength extraction from prose remains unbuilt,
   confirmed absent by this investigation, not sized as a follow-on here.
3. **No NL path to build a Mt/network from nothing.** `build_resident_
   can_mt` remains the only from-scratch builder, still entirely
   numeric-params-driven, still with zero NL entry points — re-confirmed,
   not merely inherited from the prior rung's own finding.
4. **Growth topology is emergent, not sentence-specified.** Which NEW
   edges appear is decided by the network's OWN relaxation dynamics (which
   Concepts land on the same sign), never by the adapter or by anything the
   input sentences literally name. "Ida is self worth" and "Ida is debtor
   trustworthy" do not directly assert "self_worth influences
   debtor_trustworthy" — that pairing emerged because both settled to the
   same sign after evidence was applied. This is a real, structural
   difference from a hypothetical direct "X influences Y" parse-to-edge
   adapter (which does not exist and is not what was built), named here
   rather than overclaimed.
5. **Entity/Mt resolution ambiguity is inherited, unmodified, unfixed.**
   `apply_derived_fact_as_can_evidence`'s own name-based `denotes`
   resolution can resolve ambiguously if two same-named `Resident` networks
   exist on one substrate (found live during this rung's OWN investigation,
   §4). This rung's own defensive re-check (step 3, §3) detects and
   excludes a mismatch for its OWN success accounting, but does not fix the
   underlying resolution mechanism — `ENTITY_RESOLUTION_RESULTS.md`'s own
   already-documented, separate concern.
6. **`ensure_can_native_engine_loaded`'s idempotency guard is name-based,
   not content-based.** If a FUTURE edit to `can_native_reimplementation.
   json` renamed `can_native_hebbian_mint`, this guard's sentinel would need
   updating too — a real, small, named coupling, not a hidden one.
7. **Negation, compound statements, and multi-predication sentences are
   out of scope**, inheriting exactly the same boundaries `mint_solve_
   reasoning_bridge_goal_from_text` already documented (only a single
   leading property predication per statement is read; `positive` is
   always applied as `True`).
8. **Synthetic-proven mechanism ≠ benchmark value**, per house standard:
   every number above is a mechanism demonstration on real residents and
   real sentences, not a coverage claim over how often naturally-occurring
   fact sequences would grow a CAN network's structure this way, or over
   how large a growable network this composition scales to (this rung's
   own demonstrations stay at the 5-Concept, single-resident scale
   `build_resident_can_mt` itself produces).

---

## 8. This concludes the six-resolver NL-adapter arc

With this rung, all six of the originally-unwired `solve_*` resolvers
(`SOLVER_NL_ADAPTER_PREREG.md` §1's own table) have been investigated with
real, checked evidence, not shape-of-the-problem guessing:

| resolver (direction) | verdict |
|---|---|
| `solve_reasoning_bridge` (`deduction_to_can`) | **GO, built** (`SOLVER_NL_ADAPTER_RESULTS.md`) |
| `solve_analogical_promote` | **GO, built** — a self-correction of the original ranking (`SOLVER_ANALOGY_ADAPTER_RESULTS.md`) |
| `solve_decompose` | **GO, built** — a second self-correction (`SOLVER_DECOMPOSE_ADAPTER_RESULTS.md`) |
| `solve_can_relax`/`solve_can_exact`/`solve_can_bp` | **GO, built, narrowly scoped** — edge growth on an already-built network, this document |

**This is the honest final state of the arc, not a failure to reach six
full builds.** Three of the four investigated rungs found the original
ranking too pessimistic once actually checked, each for a different,
specific, named reason (a grep on the wrong vocabulary; a cost-inheritance
argument that didn't check whether the true upstream dependency was already
free; a genuinely new-but-narrow composition of an existing co-occurrence
mechanism). The fourth rung's own honest boundary — no new Concepts, no
weight read from language, no whole-network-from-a-description — was
checked with real skepticism, confirmed to still hold for those two
specific claims, and reported as a real, named limit on what was built,
exactly as `CAN_SOLVER_TRACTABILITY_RESULTS.md` and the delimiter-join/
budget-wall investigations earlier in this arc reported their own NO-GOs:
with precise evidence for the boundary, not a vague "too hard."
`solve_reasoning_bridge`'s own `can_to_deduction` direction (the REVERSE
direction of the one resolver already built) still has no NL adapter either
— it inherits the SAME `targets_mt`-a-full-Microtheory prerequisite this
document's own §7 named boundaries apply to, and remains a genuinely open,
unattempted follow-on, named here rather than silently left implicit.
