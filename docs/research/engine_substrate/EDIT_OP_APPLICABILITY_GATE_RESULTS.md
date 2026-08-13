# EditOp applicability gate — results

Companion to `EDIT_OP_APPLICABILITY_GATE_PREREG.md` (read first — it
registers the fix shape and the demonstration case's expected before/after
behavior before any code was touched). Closes `SHAPE_AUDIT.md` §2.1 site
**A4** (`reflective_faculty.py`'s `_EDIT_OPS` / `_compose_structural_variant`):
*"the sharpest illustration of the MAC/FAC diagnosis... A FAC stage exists;
it is not used for the selection, only to execute it."*

**Worktree:**
`/tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/editop-applicability-gate`,
branch `editop-applicability-gate`, detached from `main` at `6314ebe`. No
Rust touched — `runners/dsl/python/substrate_rs/_native.abi3.so` sha256
`23ba3f1dbe20459c340440978d379c09d83eba7109b489a56a754ebd9b92a7af`
(unchanged before/after this rung; this tree's own worktree-local artifact,
not the canonical-tree pointer — confirmed present and used by the test
run, per `conftest.py`'s own precedence rule).

---

## GO. Zero measured regression, fix does exactly what it was registered to do.

---

## 1. The fix, as built

`domains/reflective_faculty.py:4084-4112` — new function
`_editop_applicable_kinds(rule_json, eo)`: computes, in Python, from the
ALREADY-RESOLVED `rule_json` dict (the same value `_pick_acting_rule`
already produced earlier in the same call), which of the four `_EDIT_OPS`
kinds are structurally possible on this rule — reusing the EXACT SAME
predicates the post-hoc apply branches already used (`edit_ops.find_comparison_nodes`
for `flip_comparison`, `edit_ops.find_attr_keys` (`>=2`) for `swap_term_leaf`,
`len(match) > 1` for `drop_match_edge`, `match` non-empty + `match[0]` a
non-empty list for `add_match_guard`).

`_compose_structural_variant` (`:4115-4250`) now:

1. Picks the acting rule exactly as before (`_pick_acting_rule`, A1,
   untouched).
2. Computes `applicable_kinds = _editop_applicable_kinds(rule_json, _eo)`.
   If empty, returns an honest abstain **before building any Term at all**
   (a genuinely different diagnosis from "candidates existed but none
   scored," so it gets its own wall message).
3. Builds the EditOp Argmax Term exactly as before, EXCEPT the candidate
   source is now `Filter(NodesOfType("EditOp"), "s", Or(Eq(kind, k1), Eq(kind,
   k2), ...))` instead of the bare `NodesOfType("EditOp")` — restricting
   candidates to `applicable_kinds` before the keyword-overlap Argmax scores
   them. `Or`/`Eq`/`Filter` are pre-existing Term types
   (`runners/dsl/src/jsonio.rs:1534` for `Or`); no new Term, no Rust change.
4. The keyword-overlap scorer (`overlap`, `StringIndexOf`-`Sum`) is
   byte-unchanged — this restricts the CANDIDATE SET, it does not re-weight
   or replace the relevance signal, exactly as the brief specified.
5. The whole pick (applicability filter + keyword Argmax + abstain-on-zero)
   stays inside ONE evaluated Term, mirroring A1/A2's `Filter`-then-`Argmax`
   precedent (`_pick_acting_rule`'s `skippable`-restriction `Filter`) exactly.
6. The four per-kind apply branches (`:4211-4239`) are UNCHANGED — kept as a
   defensive safety net. Under the fix they should no longer normally return
   `None` for a kind already filtered in as applicable (same predicates gate
   both places), but the honest-null path stays reachable rather than
   assumed dead.

**Term-algebra boundary — confirmed, no Rust needed.** `rule_json` is a
plain Python dict, already resolved from a `RuleSummary.rule_json` JSON
string attribute before `_compose_structural_variant` ever reaches the
EditOp pick — not a graph node the Term evaluator could walk. Computing
applicability over that JSON blob IS what `edit_ops.find_comparison_nodes`/
`find_attr_keys` already do, mechanically, in Python; there is no Term that
walks an arbitrary JSON-shaped attribute value (the Term algebra reads the
GRAPH, not the internals of one string attribute). This is the same
precedent `axis_preds`/`words` already sets in this exact function: a
Python-side value, computed once from something already resolved, becomes a
Term literal, while the DECISION (which candidates survive, which one wins)
stays fully inside the Term. GO on this boundary — not a NO-GO, and no
precomputed-`set_attr` alternative was needed.

---

## 2. Discovery made during baseline capture (registered as a correction in
the PREREG, restated here for the record)

`ground_concern`'s "test"-anchored family (`reflective_faculty.py:5924`,
`_route_experiment_composer`) resolves via the GRAPH-RESIDENT twin
(`composer_experiment_graph.json`'s `compose_experiment_mint_parametric`
meta-rule — SHAPE_AUDIT's A8) for every concern this rung's demonstration or
`test_structural_variant.py` construct — confirmed live:
`ground_concern(ag, [key])` on the exact residual/seed setup
`test_structural_variant.py` uses returns `served_by == "graph"`. Grepping
the whole tree: nothing calls `_compose_structural_variant(` directly except
its own definition and its `_VARIATION_REGISTRY["structural_edit"]`
registration.

**Consequence: `_compose_structural_variant` (A4, this rung's target) is
live, correct, directly-callable code, but it is DEAD in today's
`ground_concern` production wiring — the graph-resident twin (A8, out of
scope for this rung) already shadows it for every concern shape that would
otherwise reach it.** This does not change the fix (the brief targets this
exact function, by name and file:line, independent of what shadows it in
one particular caller), but it does mean: (a) the demonstration below calls
`_compose_structural_variant` directly — the only way to exercise the code
this rung actually changed; (b) `test_structural_variant.py`'s
`ground_concern`-routed assertions are unaffected by this edit (confirmed:
identical failing-node-id lists before/after, §5) because they were never
reaching this function; (c) A8 (the graph twin) is a separate, real,
un-fixed instance of the same MAC/FAC defect, named but explicitly out of
scope here.

---

## 3. The live demonstration

**Rule:** `hop_descend_gradient` (`seeds/grid_navigation.json`, real,
seed-sourced) — single match edge (`drop_match_edge` structurally
inapplicable), 4 comparison nodes + row/col each referenced 4× (
`flip_comparison`/`swap_term_leaf` applicable), non-empty `match[0]`
(`add_match_guard` applicable).

**Residual:** `["test", "send", "judge", "structure", "gradient", "drop",
"match", "edge", "gate"]`. Keyword-overlap scores (`StringIndexOf`
substring count against each op's blurb, hand-computed AND reconstructed
in `tests/test_editop_applicability_gate.py::_old_unfiltered_argmax_kind`,
matching):

| kind | score | matched words | structurally applicable to `hop_descend_gradient`? |
|---|---|---|---|
| `drop_match_edge` | **3** | drop, match, edge | **NO** (1 match edge) |
| `flip_comparison` | 1 | gate | yes |
| `swap_term_leaf` | 0 | — | yes |
| `add_match_guard` | 0 | — | yes |

### OLD behavior (captured live, on the unmodified worktree tip `6314ebe`,
direct call `rf._compose_structural_variant(ag, ["demo_gate"], "demo")`)

```json
{
  "built": false,
  "wall": "the picked op 'drop_match_edge' is structurally INERT on the picked rule 'hop_descend_gradient' (n_sites=0) — a discovered null for THIS (op, rule) pairing, not fabricated",
  "kind": "drop_match_edge",
  "rule": "hop_descend_gradient"
}
```

Unfiltered Argmax picks the keyword-best op (`drop_match_edge`, score 3),
attempts it, gets a guaranteed null. Exactly the predicted defect.

### NEW behavior (same call, same residual, fixed code)

```json
{
  "built": true,
  "kind": "flip_comparison",
  "removed_rule": "hop_descend_gradient",
  "site": "all comparison nodes in effects (a homogeneous family — see module docstring)",
  ...
}
```

Candidates are restricted to `{flip_comparison, swap_term_leaf,
add_match_guard}` before scoring (`drop_match_edge` filtered out as
inapplicable to THIS rule); `flip_comparison` wins the restricted Argmax
(score 1, the only nonzero score among applicable candidates) and the edit
succeeds. Both captures reproduced exactly as registered in the PREREG —
no surprises in either direction.

### No-regression case: keyword-best op already applicable

The three existing discriminative rows (`cue_word` in `{flip, swap,
guard}`, each of which already picks an APPLICABLE op under the old code)
stay byte-identical, called directly:

| cue_word | picked kind | built |
|---|---|---|
| flip | flip_comparison | true |
| swap | swap_term_leaf | true |
| guard | add_match_guard | true |

### The one behavior that legitimately changes: `"drop"` alone

Residual `["test", "send", "judge", "structure", "gradient", "drop"]` — no
word besides `"drop"` overlaps ANY op's blurb (not even `flip_comparison`'s,
which needs `"gate"`). OLD: picks `drop_match_edge` (score 1, still the
unique nonzero), built `False`, `"INERT"` wall (the same shape as the main
demonstration, smaller margin). NEW: `drop_match_edge` filtered out as
inapplicable, leaving `{flip_comparison: 0, swap_term_leaf: 0,
add_match_guard: 0}` — all zero, so the (unchanged) abstain-on-zero wrapper
returns `None` — **an honest "nothing applicable scored" abstain, never a
doomed pick.** Captured live:

```json
{"built": false, "wall": "no APPLICABLE EditOp genuinely overlaps this axis's residual predicates (candidates restricted to ['flip_comparison', 'swap_term_leaf', 'add_match_guard'] by structural applicability; abstained — not a random pick)"}
```

This is a strictly more honest outcome than the old one (an abstain instead
of a guaranteed-null attempt), and it does NOT regress
`test_structural_variant.py`'s existing `"drop"` test — that test routes
through `ground_concern`, which (§2) never reaches this function for this
residual shape; it exercises the untouched graph twin instead, confirmed by
the byte-identical failing-node-id comparison in §5.

---

## 4. Relationship to the prior rung's "NEGLIGIBLE" verdict on this same
site — not a contradiction, a different fix shape

`RULE_SIGNATURE_PRODUCTION_WIRING_RESULTS.md` already investigated
`_EDIT_OPS` (AR3, site A4) and declined a fix as **(c) NEGLIGIBLE**:
measured **zero** cross-blurb word-overlap among the four hand-written
`keywords_text` values, and no comparable `where_signature_json`-style
structural OBJECT to extract a fallback signature from (an `EditOp` has no
`where`/`match`/`effects` of its own — it names an operator, not a rule).
That verdict is about the **A1/A2-style structural-FALLBACK** fix shape
(second Argmax over a different signal when the primary abstains) — and it
is correct that this shape doesn't apply here, because there is no
comparable per-EditOp structural signature to fall back to.

**This rung builds a genuinely different fix shape, per the brief's own
framing:** not "does the keyword pick disambiguate ambiguous EditOps
correctly" (the question the prior rung answered NEGLIGIBLE — there's no
ambiguity to disambiguate, the four blurbs never collide with each other)
but "is the keyword-best op even POSSIBLE on the rule it would be applied
to." The relevant structural object is not a per-EditOp signature — it is
the (EditOp, RULE) PAIRING's applicability, which the mechanical appliers
already computed post-hoc and this rung moves to pre-hoc. The two findings
are compatible: zero blurb collision (prior rung, true, still true) and a
real, demonstrated applicability gap (this rung, measured live above) are
different properties of the same site.

---

## 5. Regression

**Paired failing-node-id lists — byte-identical, confirmed via `diff`,
before vs. after, same worktree, same commit base.** Baseline captured by
`git stash` (isolating exactly this rung's `domains/reflective_faculty.py`
edit) and re-running the identical file set + `-k "not slow"` filter,
synchronously, no polling:

```
tests/test_experiment_composer_graph.py::test_full_combo_gradient_embed_matches_shift_rule_thresholds_oracle
tests/test_experiment_composer_graph.py::test_test_alone_graph_rule_mints_experiment_without_host_add_node
tests/test_experiment_composer_graph.py::test_vary_bare_graph_rule_fires_and_picks_skip_seeds
tests/test_experiment_composer_graph.py::test_embed_graph_rule_fires_and_embeds_a_real_variant
tests/test_editop_dialect_terms.py::test_add_match_guard_already_expressible
tests/test_editop_dialect_terms.py::test_flip_comparison_pilot_matches_python_reference
tests/test_editop_dialect_terms.py::test_swap_term_leaf_pilot_matches_python_reference
tests/test_editop_dialect_terms.py::test_drop_match_edge_pilot_matches_python_reference
tests/test_editop_dialect_terms.py::test_swap_site_chain_matches_python_reference_on_hop_descend_gradient
tests/test_frozen_core_invariant.py::test_manifest_matches_live_constants_no_drift
tests/test_frozen_core_invariant.py::test_frozen_seed_ids_closed_folds_in_enact_and_discourse
tests/test_frozen_core_invariant.py::test_frozen_core_set_reports_the_closure_with_no_manifest_drift
```

**Both runs: 12 failed** (BEFORE: 162 passed, 5 deselected; AFTER: 170
passed [+8, exactly `test_editop_applicability_gate.py`'s new count], 5
deselected) **— the exact same 12 node ids, in both directions, `diff`
clean.** None of the 12 are in `test_structural_variant.py` or
`test_composers_graph.py` (both fully green, both before and after); the 12
live in `test_experiment_composer_graph.py` (a real-verb "graph rule fires"
family unrelated to EditOp applicability — these exercise the parametric
mint meta-rule's own host-add_node/skip_seeds/embed wiring), `test_editop_dialect_terms.py`
(Rust-dialect-vs-Python-reference PILOT chain tests — a DIFFERENT
implementation of the flip/swap/drop/guard appliers as Rust dialect Terms,
not `domains/edit_ops.py`), and `test_frozen_core_invariant.py` (an
unrelated seed-closure-drift assertion naming `cognitive_pareto`/
`program_synthesis`/`metacognitive_learning` as unexpected extra closure
members — a environment/seed-manifest-state property, not anything this
rung's diff touches). **Not investigated further here** (out of scope,
pre-existing on the unmodified tip, confirmed present with or without this
rung's one-function edit) — flagged honestly rather than silently
attributed to this change.

**This rung's own files: fully green.**

```
tests/test_editop_applicability_gate.py + tests/test_structural_variant.py
+ tests/test_composers_graph.py, run together:
75 passed, 1 deselected, 1 warning in 148.92s
```
(`tests/test_editop_applicability_gate.py` + `tests/test_structural_variant.py`
+ `tests/test_composers_graph.py` together; the 1 deselected is the
`@pytest.mark.slow` end-to-end dispatch test in `test_structural_variant.py`,
excluded per the `-k "not slow"` filter used throughout this rung, same as
the prior rung's own convention.)

---

## 6. New test file

`tests/test_editop_applicability_gate.py` (8 tests):

1. `test_applicable_kinds_on_hop_descend_gradient` — direct unit check of
   `_editop_applicable_kinds` against the real seed rule.
2. `test_applicable_kinds_on_mark_visited_footprint` — confirms
   `drop_match_edge` IS applicable on a DIFFERENT real rule with 2 match
   edges (the predicate is rule-specific, not a blanket exclusion).
3. `test_applicable_kinds_empty_on_a_degenerate_rule` — the zero-candidate
   edge case, at the unit level.
4. `test_ground_concern_does_not_reach_compose_structural_variant` — pins
   the §2 discovery as a regression trip-wire: if the graph twin ever stops
   shadowing A4, this test starts failing and flags that
   `test_structural_variant.py`'s assertions need re-auditing against this
   function.
5. `test_old_reconstruction_would_pick_the_inapplicable_op` +
   `test_new_behavior_picks_the_applicable_op_and_succeeds` — the live
   demonstration, permanently encoded (old reconstructed from the
   unfiltered-Argmax shape over `_EDIT_OPS` directly, new called live).
6. `test_wall_message_names_the_applicability_restriction_on_pure_abstain` —
   the "drop alone" honest-abstain case.
7. `test_no_applicable_kind_at_all_abstains_before_any_argmax` — the
   all-four-inapplicable defensive path, via a synthetic degenerate
   RuleSummary.

---

## 7. What this does NOT establish

- **Does not fix A8** (`composer_experiment_graph.json`'s graph-native
  twin) — the actual code path `ground_concern` uses in production for
  every concern this rung's own demonstration constructs. A8 is a SEPARATE
  MAC/FAC instance (baked as Rust-evaluated Terms inside a meta-rule, not
  Python), explicitly out of scope, and — per §2 — the one that would need
  fixing for this class of concern to benefit from applicability gating
  in the actual `ground_concern` call path today.
- **Does not investigate whether `_compose_structural_variant` should be
  wired back into `ground_concern`'s dispatch** (e.g. so the fixed Python
  function is reachable again) — an orthogonal question this rung did not
  ask and has no data on.
- **Does not resolve the 12 pre-existing failures** in
  `test_experiment_composer_graph.py`/`test_editop_dialect_terms.py`/
  `test_frozen_core_invariant.py` — confirmed present identically with and
  without this rung's edit, not investigated further (out of scope; a
  possible sibling-rung or environment interaction, not diagnosed here).
- **Does not measure end-to-end behavioral divergence** (the
  `@pytest.mark.slow` dispatched-child-process comparison
  `test_structural_variant.py` has for the OLD code path) for the NEW
  applicability-gated pick — the demonstration here is at the
  `_compose_structural_variant` return-value level, matching the
  house-discipline requirement, not a full dispatched-experiment replay.
- **A synthetic-proven mechanism, not a benchmark value**: this closes a
  real, demonstrated MAC/FAC gap at one specific, currently-dead-in-production
  call site (A4). It says nothing about how often, in practice, a picked
  acting rule's keyword-best EditOp is inapplicable versus applicable —
  only that when it IS inapplicable, the mechanism now avoids the wasted
  attempt. No prevalence measurement was in scope or attempted.
