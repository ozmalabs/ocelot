# EditOp applicability gate — pre-registration

**CORRECTION, added after the first baseline capture, before the fix was
written — recorded rather than silently edited out (this folder's own
house discipline; see `SHAPE_AUDIT.md`'s own two logged corrections for the
precedent).** §3's demonstration was originally planned to run through
`ground_concern(ag, [key])`, matching how `tests/test_structural_variant.py`
§4-6 exercise the pick. Capturing the OLD-behavior baseline surfaced that
`ground_concern` **does not reach `_compose_structural_variant` at all** for
this concern shape: `ground_concern` tries the graph-resident composer
FIRST (`_try_graph_composer` → `_route_experiment_composer`,
`reflective_faculty.py:5924`), and for any concern whose grounded relations
include `"test"` (which every existing `test_structural_variant_pick_is_*`
row does), `composer_experiment_graph.json`'s `compose_experiment_mint_parametric`
meta-rule handles the ENTIRE structural-edit pick graph-natively and returns
`served_by: "graph"` — confirmed live (`res.get("served_by") == "graph"`,
captured below). `_route_experiment_composer`'s own docstring says as much:
*"`ground_concern` only falls through to `_compose_experiment_rule` any more
when NEITHER test, judge, NOR adopt grounded"* — and the structural-edit
variation op only fires when `test` AND `judge` AND `structure` are ALL
grounded, so that fallback condition can never coincide with a structural-edit
pick. Grepping the whole tree, nothing calls `_compose_structural_variant(`
directly except its own definition and its `_VARIATION_REGISTRY` registration
— **it is live, correct, reachable-by-direct-call code, but it is dead in
today's `ground_concern` production wiring; the graph-resident twin
(A8, `seeds/composer_experiment_graph.json`, out of scope for this rung)
already shadows it for every concern that would otherwise reach it.** This
does not change the fix (the brief's target is explicitly this function, by
name and line range, independent of A8), but it changes two things
downstream: (1) the demonstration below calls `_compose_structural_variant`
DIRECTLY, not through `ground_concern` (the only way to actually exercise
the code being fixed); (2) **no existing test needs to change meaning** —
`test_structural_variant.py`'s `ground_concern`-routed tests (§3-6) are
verifying the graph-resident twin, not this function, so they are
unaffected by this rung's edit; the "one existing test is expected to
change meaning" paragraph in §3 below (written before this was discovered)
is retracted, left in place with this note rather than deleted, because it
was the original prediction and turned out to be based on a wrong premise
about which code path the test suite exercises. Full regression re-run
confirms this (see RESULTS doc).

Companion to `SHAPE_AUDIT.md` §2.1 (site **A4**, `reflective_faculty.py`'s
`_EDIT_OPS` / `_compose_structural_variant`) and
`RULES_AS_SHAPE_DESIGN_SPIKE.md` §4.2 (the MAC/FAC diagnosis this rung closes
for one more site — the fourth of the six `keywords_text`-family
self-modification decisions the audit found; A1 `_pick_acting_rule` and A2
`_pick_reply_rule` already carry a structural fallback, landed earlier today;
A3/A5/A6/A7-A9 are out of scope here). This doc registers the fix shape and
the demonstration case's expected before/after behavior **before the code is
touched**, per this folder's house discipline.

**Worktree:**
`/tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/editop-applicability-gate`,
branch `editop-applicability-gate`, detached from `main` at `6314ebe`
(verified: `git log --oneline -1 main` → `6314ebe Merge
gamma-production-adopt-handler: judge/adopt split, GO`). No Rust change is
expected — see "Term-algebra boundary" below for why the applicability check
can be computed entirely in Python, on data already resolved as a Python
dict at the call site, before the Term is built.

**Out of scope, explicitly:** `_pick_acting_rule` / `_pick_reply_rule` (A1/A2,
done); `_compose_experiment_rule` / the seed-ablation Argmax (A3, lines
~4196-4350 as of this tip — a sibling rung may be running there concurrently,
this rung does not touch it); the `_EDIT_OPS` keyword blurbs themselves (kept
verbatim — the audit's complaint is that the blurb is used ALONE, not that it
is meaningless); A5/A6/A7-A9 (separate sites, not this rung); any new Rust
Term.

---

## 1. The defect, restated precisely from the live code

`_EDIT_OPS` (`reflective_faculty.py:4055-4064`) declares four structural-edit
operator kinds. `_compose_structural_variant` (`:4084-4189`), after picking a
rule via the shared `_pick_acting_rule` Argmax (A1, unchanged here), runs a
SECOND Argmax over `NodesOfType("EditOp")` scored purely by
`StringIndexOf(keywords_text, w)` overlap against the axis's residual
predicates (`:4135-4146`) — **with no structural input at all**. Only AFTER
that pick is made does the code call the winning op's own applicability
scanner:

- `flip_comparison` (`:4150-4153`): applicable iff
  `edit_ops.find_comparison_nodes(rule_json["effects"])` is non-empty.
- `swap_term_leaf` (`:4154-4162`): applicable iff
  `len(edit_ops.find_attr_keys(rule_json["effects"])) >= 2`.
- `drop_match_edge` (`:4163-4166`): applicable iff
  `len(rule_json.get("match") or []) > 1`.
- `add_match_guard` (`:4167-4176`): applicable iff `rule_json["match"]` is
  non-empty and `match[0]` is a list with `len >= 1`.

These four predicates are exactly the same ones `domains/edit_ops.py`'s four
`apply_*` functions already use internally to decide "inert, return None"
(`edit_ops.py:104-113,124-130,141-144(always true given match),155-178`,
esp. `find_comparison_nodes`/`find_attr_keys` at `:49-91`). **The structural
machinery to answer "is this op even possible on this rule" already exists
and already runs — it just runs after the pick, only to find WHERE to apply
the already-chosen op, never to help choose it.** This is the MAC-without-FAC
shape named in `RULES_AS_SHAPE_DESIGN_SPIKE.md` §4.2: a cheap non-structural
overlap score treated as the verdict, with the structural check demoted to
execution-time bookkeeping.

**Consequence, concretely:** a rule with a single match edge (e.g.
`hop_descend_gradient` in `seeds/grid_navigation.json` — confirmed by the
existing test `test_drop_match_edge_inert_on_a_single_edge_match`) is
structurally incompatible with `drop_match_edge`. If a concern's residual
words happen to overlap `drop_match_edge`'s blurb ("drop match edge relax
remove constraint pattern broaden fewer") more than the other three ops'
blurbs, the Argmax still picks `drop_match_edge`, wasting the attempt on a
guaranteed null (`built: False`) even when a different op — say
`flip_comparison` — is both applicable to this rule AND scores nonzero on
the same residual.

---

## 2. The fix shape, registered before the edit

**Filter-then-Argmax, matching A1/A2's own precedent shape ("restrict
candidates, then rank the survivors") rather than a blend or a
post-hoc re-pick.** Concretely:

1. `rule_json` (the already-picked rule, from `_pick_acting_rule`) is a
   resolved Python `dict` at the point `_compose_structural_variant` reaches
   the EditOp pick — it is NOT a graph read, it was already pulled out of
   `RuleSummary.rule_json` earlier in the SAME function, exactly the way
   `axis_preds` (a Python list) is pulled out of `CapabilityAxis` earlier and
   then fed into the Term as a literal (`words = L(list(axis_preds))`).
   Applicability is computed **once, in Python, using the SAME
   `edit_ops.find_comparison_nodes` / `edit_ops.find_attr_keys` functions
   already called post-hoc** (no new structural scanner — reuse, not
   reinvention) — this yields a plain Python `list[str]` of the kinds that
   are genuinely applicable to `rule_json`.
2. That list is fed into the Term as a `Or(Eq(Attr(s,"kind"), L(k1)),
   Eq(Attr(s,"kind"), L(k2)), ...)` predicate (the `Or`/`Eq` Terms already
   exist — `runners/dsl/src/jsonio.rs:1534`, no new Term type), used as the
   predicate of a `Filter(NodesOfType("EditOp"), "s", <applicable-kinds-or>)`
   — mirroring A1/A2's `Filter(NodesOfType("RuleSummary"), "s", And(...
   skippable ...))` pattern exactly: a Filter restricting Argmax candidates,
   not a second Python-side decision.
3. The existing keyword-overlap Argmax (`overlap`, unchanged, `:4133-4134`)
   then runs over `op_candidates = Filter(...)` instead of the bare
   `NodesOfType("EditOp")` — the relevance signal is kept, unmodified;
   only the CANDIDATE SET changes.
4. The whole pick — applicability filter AND keyword Argmax — stays inside
   ONE evaluated Term (the `LetT`/`Ite` abstain-on-zero wrapper is
   unchanged), matching A1/A2's discipline that "nothing about the decision
   moves into Python."
5. If NO kind is applicable to the picked rule at all (a degenerate case:
   defensive-only, not expected to occur for any real seed rule, since
   `add_match_guard` is applicable whenever `match` is non-empty and a valid
   rule always has a non-empty match), `_compose_structural_variant` returns
   an honest abstain with a distinguishing wall message BEFORE building the
   Term at all (no candidates to filter to) — this is a genuinely different
   diagnosis from "candidates existed but none scored," so it gets its own
   message rather than reusing the existing "no EditOp genuinely overlaps"
   text.

**Term-algebra boundary — why this is NOT a Rust gap.** The applicability
predicates read `rule_json["effects"]` / `rule_json["match"]` — a Python
dict already resolved from `RuleSummary.rule_json` (a JSON string attribute)
via `json.loads`, not a graph node the Term evaluator could walk with
`Attr`/`NodesOfType`. Computing "does this JSON blob contain a comparison
node" IS what `edit_ops.find_comparison_nodes` already does, mechanically,
in Python, and there is no Rust Term that walks an arbitrary JSON-shaped
attribute value (the Term algebra operates on the GRAPH, not on the
sub-structure of one string attribute). The precedent this rung follows is
the SAME one `axis_preds`/`words` already sets: real Python-side data
(computed once, mechanically, from something already resolved) becomes a
Term **literal** (`L(...)`), and the DECISION (which candidates survive,
which one wins) stays inside the Term. This is not a "clean NO-GO" — the
decision-making (filter + Argmax) is fully expressible in the Term algebra
once the applicability *data* is computed; only the mechanical JSON-walk
(already existing, already Python, already reused post-hoc) stays where it
already lives.

---

## 3. The demonstration case, registered before it is run

**Rule:** `hop_descend_gradient` (`seeds/grid_navigation.json`) — real,
seed-sourced, matches this test file's existing house discipline (never
hand-written rule text for the applier-level tests). Structural facts,
already asserted by existing tests:
`test_drop_match_edge_inert_on_a_single_edge_match` (`match` has exactly one
edge → `drop_match_edge` inert), `test_find_comparison_nodes_and_find_attr_keys_are_scoped_reads`
(4 comparison nodes, `row`/`col` each referenced 4×  → `flip_comparison` and
`swap_term_leaf` both applicable).

**Residual predicates (concern words):**
`["test", "send", "judge", "structure", "gradient", "drop", "match", "edge",
"gate"]` — the first five are the existing test suite's own scaffold (needed
for `ground_concern`'s relation-cue routing and to let `_pick_acting_rule`'s
own Argmax select `hop_descend_gradient` via `"gradient"` scoring against its
`RuleSummary.keywords_text` = `"hop descend gradient"`, exactly as every
existing `test_structural_variant_pick_is_discriminative` row already does).
`"drop"`, `"match"`, `"edge"` are chosen because they are substrings of
`drop_match_edge`'s blurb ("drop match edge relax remove constraint pattern
broaden fewer") and of no other op's blurb — three-word overlap, the
strongest score any op gets. `"gate"` is chosen because it is a substring of
`flip_comparison`'s blurb ("flip comparison reverse invert direction **gate**
threshold opposite") and of no other op's blurb — one-word overlap.

**Hand-computed keyword-overlap scores (verified by direct string check
before any code is run, reproduced in the RESULTS doc):**

| kind | score | matched words |
|---|---|---|
| `drop_match_edge` | **3** | drop, match, edge |
| `flip_comparison` | **1** | gate |
| `swap_term_leaf` | 0 | — |
| `add_match_guard` | 0 | — |

`drop_match_edge` is the unconditional keyword-Argmax winner (score 3 vs the
field), and it is the ONE op that is structurally INAPPLICABLE to
`hop_descend_gradient` (single match edge). `flip_comparison` is both
structurally APPLICABLE (4 comparison nodes) and the best-scoring applicable
op (score 1 > 0).

**Registered, expected OLD behavior** (current code, unmodified, run first
to confirm the defect is real and not just theorized): `_compose_structural_variant`
picks `drop_match_edge` (Argmax winner), attempts to apply it, gets `None`
back from `edit_ops.apply_drop_match_edge` (inert — single-edge match),
returns `{"built": False, "kind": "drop_match_edge", "wall": "...INERT..."}`
— a wasted pick, discovered null, exactly the audit's predicted failure mode.

**Registered, expected NEW behavior** (after the fix): the Argmax candidates
are restricted to `{flip_comparison, swap_term_leaf, add_match_guard}` before
scoring (`drop_match_edge` filtered out as inapplicable to this rule).
`flip_comparison` wins the restricted Argmax (score 1, the only nonzero
score among applicable candidates). `_compose_structural_variant` returns
`{"built": True, "kind": "flip_comparison", "removed_rule":
"hop_descend_gradient", ...}` — a genuinely successful structural edit, on
the SAME residual predicates that used to waste the pick.

**No-regression case, registered:** the three existing
`test_structural_variant_pick_is_discriminative` rows (`cue_word` in
`{flip, swap, guard}`) each pick an op that is ALREADY applicable to
`hop_descend_gradient` under the OLD code (flip_comparison: 4 comparison
nodes; swap_term_leaf: row/col both ≥2 refs; add_match_guard: non-empty
match). The applicability filter must not change these three picks — they
are registered to stay byte-identical (`built: True`, same `kind`) after the
fix.

**One existing test is expected to change meaning, registered honestly
here rather than silently edited:** `test_structural_variant_drop_is_honestly_inert_on_hop_descend_gradient`
currently asserts the OLD behavior (`kind == "drop_match_edge"`, `built ==
False`, `"INERT" in wall`) for `residual_predicates` ending in `"drop"` alone
(no `"match"`/`"edge"`/`"gate"` words). Under the new gate, with ONLY the
word `"drop"` in the residual, no other op scores > 0 either (per the
existing table above, `"drop"` alone does not appear in any of the other
three blurbs), so filtering `drop_match_edge` out leaves an Argmax over
`{flip_comparison: 0, swap_term_leaf: 0, add_match_guard: 0}` — all zero,
and the abstain-on-zero wrapper (unchanged) returns `None`, i.e. the pick now
**abstains entirely** rather than picking the inapplicable op. This is
correct under the fix (an honest "nothing applicable scored" abstain is a
strictly better outcome than a guaranteed-null pick), and the existing test
is updated in this rung to assert the new, more honest behavior — reported
as a deliberate, registered behavior change, not a silent test edit.

---

## 4. Regression scope

Test files covering `_compose_structural_variant` / the structural-edit
composer path, to be run before (baseline) and after (paired failing-node-id
lists, not counts):

- `tests/test_structural_variant.py` (primary — the file this rung's fix and
  new tests live in)
- `tests/test_composers_graph.py`
- `tests/test_experiment_composer_graph.py`
- `tests/test_editop_dialect_terms.py`
- `tests/test_frozen_core_invariant.py` (references `EditOp`/frozen-provenance
  interaction)

New test file: `tests/test_editop_applicability_gate.py` — the live
demonstration (old-vs-new via direct comparison against `domains.edit_ops`'s
own applicability predicates, plus the full `hop_descend_gradient` case
above) and the no-regression checks.

---

## 5. GO/NO-GO criterion

**GO** iff: (a) the demonstration case reproduces exactly as hand-computed
above on the OLD code (captured as a baseline before editing); (b) the fix,
once built, produces exactly the registered NEW behavior on the same case;
(c) the three no-regression rows stay byte-identical; (d) the whole pick
remains inside one evaluated Term (no new Python-side branching over graph
state); (e) no new Rust Term is needed.

**NO-GO** iff the applicability computation turns out to require information
not available as a plain Python value at the point `_compose_structural_variant`
reaches the EditOp pick (it is not expected to — `rule_json` is already
resolved earlier in the same function) — in which case the smallest
alternative (a precomputed `set_attr` on the EditOp/rule pairing, mirroring
`where_signature_json`'s precomputed-field precedent) will be proposed
instead of forcing a new Term.
