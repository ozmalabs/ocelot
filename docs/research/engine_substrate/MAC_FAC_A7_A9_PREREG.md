# MAC/FAC A7-A9 — graph-resident structural-fallback wiring — PREREG

Registered BEFORE any edit to `seeds/composer_experiment_graph.json`. Closes
`SHAPE_AUDIT.md` §2.1's three graph-resident sites — the twins, inside a
SEED (not Python), of the already-fixed A1 (`RULE_SIGNATURE_PRODUCTION_
WIRING_RESULTS.md`), A3 (`SEED_PICK_STRUCTURAL_FALLBACK_RESULTS.md`), A4
(`EDIT_OP_APPLICABILITY_GATE_RESULTS.md`).

## 0. What reading the actual file establishes, before any edit — resolving
the apparent A8/A9 label conflict between the two prior RESULTS docs

Both prior docs cite `seeds/composer_experiment_graph.json`'s single Rule
node `compose_experiment_mint_parametric` (`local_id: 8`, starts at file
line 463) but attach DIFFERENT letters to it: `SEED_PICK_STRUCTURAL_
FALLBACK_RESULTS.md` calls it "A9 ... the graph-resident twin of A3";
`EDIT_OP_APPLICABILITY_GATE_RESULTS.md` calls it "A8". Read directly (not
trusted from either doc), the file resolves this: `compose_experiment_
mint_parametric` is ONE Rule node whose single `effect` Term embeds
**three structurally distinct Argmax picks at three different nesting
depths**, matching the audit table's own three line numbers exactly:

| letter | audit line | what it is | var names | resolves to |
|---|---|---|---|---|
| A7 | 1127 | RuleSummary Argmax, twin of A1 (`_pick_acting_rule`) | `apick`/`s` | RuleSummary node or `null` |
| A8 | 1366 | EditOp Argmax, twin of A4 (`_compose_structural_variant`) | `epick`/`op` | EditOp node or `null` |
| A9 | 4712 | SeedSummary Argmax, twin of A3 (`_compose_experiment_rule`'s seed-skip) | `skip_id`/`best` | seed_id string or `""` |

Both prior docs are individually correct — they were each describing the
sub-pick they were personally touching, by the ENCLOSING rule's `id`, not
by the specific nested Argmax. The audit's own line-number table is the
disambiguator and is confirmed correct by direct reading. This PREREG uses
the audit's letters (A7/A8/A9) to mean the specific nested Argmax, not the
enclosing rule.

**Further reading found the seed-pick and rule-pick shapes are each
DUPLICATED once more inside the same rule**, for a second branch
(`has_judge && has_gradient`, the "gradient" variant-family, vs the first
branch's `has_judge && has_structure`), and the seed-pick is duplicated a
second time to produce a differently-wrapped sibling attr
(`skip_seed_id`, raw string, vs `skip_seeds`, a JSON-array-wrapped
string). So the real edit surface is:

- **A7 has two copies**: `apick` (line 1127, `has_judge&&has_structure`
  branch) and a second RuleSummary Argmax named `best` at line 3029
  (`has_judge&&has_gradient` branch) — structurally identical, same
  candidate filter (`writes_chosen_action==1 && skippable==1`), same
  `cr.residual_predicates` word source.
- **A9 has two copies**: `skip_id`/`best` (line 4675, feeds `skip_seeds`)
  and a second SeedSummary Argmax also named `best` at line 4886 (feeds
  `skip_seed_id`) — structurally identical, same candidate filter
  (`skippable==1`), same `axis.residual_predicates` word source.
- **A8 (`epick`, line 1366) has one copy** — it is nested inside the
  `has_judge&&has_structure` branch only (the gradient branch never picks
  an EditOp; it shift-varies the acting rule directly).

**Consequence for scope**: fixing A7 means fixing BOTH its copies (else
the "structure" and "gradient" experiment-variant families would silently
diverge in which acting rule they pick for the identical residual — a
worse, inconsistent state than not fixing it at all). Same for A9 (else
`skip_seeds` and `skip_seed_id` on the SAME `SeedDelta` could name
different seeds for the identical axis). This PREREG registers fixing
BOTH copies of A7 and BOTH copies of A9 as one unit each, not as
independent partial edits.

## 1. Priority order, registered before editing

1. **A9 first** — highest real-world value per the task brief:
   `SEED_PICK_STRUCTURAL_FALLBACK_RESULTS.md` §5 already measured live
   that `compose_experiment_mint_parametric` (containing A9) is the
   ACTIVE/WINNING dispatch path for the common `'test'`-anchored,
   non-`'replay'` self-experiment concern — the Python A3 fix is
   reachable only for the conversation-`'replay'` family; A9 is what real
   concerns hit today. Both copies (`skip_seeds`, `skip_seed_id`).
2. **A7 second** — same fix shape as the already-validated Python A1 fix,
   same precomputed attr (`RuleSummary.where_signature_json`, already
   minted by `_ensure_acting_rule_provenance` + `rule_signature.
   ensure_where_signature`, both already called from live Python paths —
   see §3 reachability note). Both copies (`apick`, the gradient-branch
   `best`).
3. **A8 — expected to be sized as follow-on, not fixed this rung,
   registered as a PREDICTION not yet confirmed.** `EDIT_OP_
   APPLICABILITY_GATE_RESULTS.md` already measured that the Python A4 fix
   is NOT a structural-fallback Argmax at all (that shape was tried and
   declined by the PRIOR rung, verdict NEGLIGIBLE — zero blurb collision
   among the four `EditOp` keyword sets, and no `where`/`match`/`effects`
   object on an `EditOp` node to derive a fallback signature from in the
   first place). The actual A4 fix is an APPLICABILITY GATE: filter
   candidate EditOp kinds by whether they are structurally POSSIBLE on
   the specific picked RULE, computed in Python from the rule's own
   `rule_json` dict via `edit_ops.find_comparison_nodes`/
   `find_attr_keys` — and that same RESULTS doc states explicitly:
   *"there is no Term that walks an arbitrary JSON-shaped attribute
   value (the Term algebra reads the GRAPH, not the internals of one
   string attribute)."* If confirmed on inspection of `epick`'s own Term
   (§2 below), fixing A8 with the SAME rigor as A7/A9 would require
   either a new Rust Term (explicitly out of scope this rung) or a new
   precomputed multi-flag attr design on `RuleSummary` (one boolean per
   EditOp-kind-applicability, mirroring `where_signature_json`'s
   precedent but for a DIFFERENT question than "does the where-clause
   mention this word" — never designed or measured before). This
   PREREG's expectation, stated before opening `epick`'s JSON: **A8 will
   be found to need the applicability-gate shape, not the
   structural-fallback shape, and is sized as a follow-on rather than
   attempted live this rung** — to be confirmed or refuted by §2's actual
   read.

## 2. The design choice for A7/A9 (registered before editing)

Same choice `SEED_PICK_STRUCTURAL_FALLBACK_RESULTS.md` §2 already made
and measured for the Python side: **reuse the EXISTING precomputed
aggregate attrs** (`RuleSummary.where_signature_json` for A7,
`SeedSummary.where_signature_json` for A9) via the identical
`StringIndexOf`-`Sum` overlap shape `keywords_text` already uses, rather
than a live nested Filter/Exists join. No new Rust Term. This mirrors the
already-validated design, not a new one.

**Reachability caveat, registered honestly before editing (not found
after, unlike the prior rung):** neither `where_signature_json` attr is
populated at boot. `rule_signature.ensure_where_signature` /
`domains.seed_signature.ensure_seed_signature` are each called from
exactly one place in production Python
(`reflective_faculty.py:2833`/`:3086` for the rule grain, inside
`_pick_acting_rule`/`_pick_reply_rule`; `:4398` for the seed grain,
inside `_compose_experiment_rule`'s `vary` branch) — never from a boot
path, never from inside a graph-resident Rule (Rules cannot call Python).
For A9 specifically, `SEED_PICK_STRUCTURAL_FALLBACK_RESULTS.md` §5 already
found that the graph path (containing A9) wins dispatch BEFORE the Python
function that primes `where_signature_json` is ever reached — so in a
cold graph, A9's fallback finds the attr absent on every candidate.
**This rung's live demonstration primes the attr explicitly as test
setup** (`ensure_where_signature`/`ensure_seed_signature` called once
before firing the rule via `run_rules()`) — the same precompute step the
already-landed A1/A3 fixes themselves depend on, not a new mechanism.
Whether anything should prime these attrs automatically before a
graph-resident rule fires in a live daemon is registered here as an
honest residual, not solved by this rung (same class of finding as the
prior rung's own `ground_concern`-dispatch-order caveat).

## 3. Edit mechanism (registered before editing)

Each edit is a **wrap, not a rewrite**: the existing collapsed pick
(`apick`'s or `best`'s node-or-null result / `skip_id`'s or the second
`best`'s seed_id-or-`""` result) is renamed into a fresh `Let` binding
and its abstain branch (previously a bare `Lit(null)` / `Lit("")`) is
replaced by a second `Argmax`, over the SAME candidate `Filter`, scored
by `where_signature_json` instead of `keywords_text`, collapsed by the
identical null/zero-overlap-check shape. The interior of the existing
Argmax/collapse block is copied byte-for-byte (extracted by brace-count,
validated as standalone-parseable JSON via `json.loads` before
splicing) — never hand-retyped — to eliminate transcription risk in a
170+-line nested structure. New `Let`/`Var` names are unique per site
(`primary_pick_apick`/`struct_pick_apick`, `primary_pick_grad`/
`struct_pick_grad`, `primary_seed_a`/`struct_seed_a`,
`primary_seed_b`/`struct_seed_b`) to avoid any cross-branch shadowing
risk, even though the branches are mutually exclusive.

Local reindentation of the wrapped interior is NOT performed (it would be
a purely cosmetic, error-prone, whole-block hand-edit for zero semantic
value) — the file already contains a pre-existing, independently
confirmed indentation irregularity elsewhere (found during a round-trip
`json.dumps` check before any edit: a `"tree": {` whose child `"type"`
does not increment indentation), so a locally flat indent at the wrap
point is consistent with, not a regression from, this file's own existing
maintenance history. Every edit is validated by `json.loads` on the WHOLE
file before proceeding.

## 4. Validation steps, run after EACH site's edit (not just at the end)

1. `python3 -c "import json; json.load(open('seeds/composer_experiment_graph.json'))"`
   — still valid JSON.
2. `python3 -c "..."` — the seed still loads via `boot_all`/
   `load_seeds_into` (or the narrowest available loader) with no new
   error, and the edited Rule node's `local_id` / `id` / node count in
   `composer_experiment_graph.json` is unchanged (a wrap changes ONE
   subtree's shape, not the node/edge counts).
3. The Rule still installs (`native.add_rule` on the edited `effect`
   Term does not raise) and still FIRES on an unrelated regression
   probe unchanged (a probe from the existing test suite that does NOT
   touch the specific wrapped branch) — i.e. Class-B-equivalent coverage
   at the granularity of "did I break something totally unrelated in
   this same rule."
4. The relevant existing test files
   (`tests/test_experiment_composer_graph.py`,
   `tests/test_composers_graph.py`) run to completion; failing-node-id
   list captured and diffed against the pre-edit baseline (captured
   once, before ANY edit, on this worktree's tip).
5. The Class-A/Class-B live demonstration for that specific site.

## 5. What "done" looks like, registered before editing

For each of A9 (both copies) and A7 (both copies): a Class-A probe
(where-signature word absent from every candidate's `keywords_text`,
present in the target candidate's `where_signature_json`) recovered by
the wired fallback through the REAL loaded Rule (fired via
`substrate.tick()`/`run_rules()`, not a standalone Term evaluated in
isolation); a Class-B probe (existing `keywords_text` overlap already
nonzero) confirmed byte-identical to pre-fix behavior through the same
real-rule-fire path. For A8: either the same, if §2's read of `epick`
turns out to admit a structural-fallback shape after all (checked, not
assumed), or a precise sizing of why it doesn't, matching this doc's own
§1.3 prediction or correcting it with the reason found.
