# MAC/FAC A8 — `epick`'s applicability-gate precompute — pre-registration

Registered BEFORE any edit to `domains/reflective_faculty.py` or
`seeds/composer_experiment_graph.json`. Closes the ONE remaining
`SHAPE_AUDIT.md` §2.1 site the prior two rungs both found and declined:
`EDIT_OP_APPLICABILITY_GATE_RESULTS.md` closed the PYTHON twin (A4,
`_compose_structural_variant`, confirmed DEAD in production — shadowed by
this exact graph-resident rule for every concern shape that would reach
it); `MAC_FAC_A7_A9_RESULTS.md` §5 read `epick`'s actual Term, confirmed the
PREREG's own prediction ("A8 will need the applicability-gate shape, not
structural fallback"), and sized the precompute this rung builds —
**verbatim from that doc**: *"a NEW Python precompute, mirroring
`_ensure_acting_rule_provenance`'s own precedent, that stamps FOUR new
boolean attrs onto each `RuleSummary` node at mint time — one per
`_EDIT_OPS` kind... using the SAME `edit_ops.find_comparison_nodes`/
`find_attr_keys` predicates `_editop_applicable_kinds` already computes in
Python for the A4 fix."*

**Worktree:**
`/tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/mac-fac-a8`,
branch `mac-fac-a8`, detached from `main` at `b768b7b` (verified:
`git log --oneline -1 main` → `b768b7b Merge mac-fac-a5-a6: structural
fallback for datum-feedback and rule-literal picks, GO`).

**Out of scope, explicitly (per the brief):** `_editop_applicable_kinds` /
`_compose_structural_variant` themselves (A4, already correct — REUSED, not
reimplemented, not modified, unless extracted into a shared helper both
call — see §1); A5/A6/A7/A9's own landed fixes (untouched); any new Rust
Term (the existing `Filter`/`Argmax`/`Attr`/`Eq`/`Or`/`And` vocabulary,
already used throughout this exact seed file for A7/A9, is registered here
as sufficient — to be confirmed, not assumed, by §2).

---

## 1. The precompute, registered before it is written

**Reused logic, ONE definition.** `_editop_applicable_kinds(rule_json, eo)`
(`reflective_faculty.py:4190-4218`) is called DIRECTLY by the new
precompute — not reimplemented, not copy-pasted. This satisfies the
brief's own constraint ("do not reimplement the four predicates a second
time... so there is exactly ONE place these four predicates are defined").

**Four flag names, registered before writing the function**:
`applicable_flip_comparison`, `applicable_swap_term_leaf`,
`applicable_drop_match_edge`, `applicable_add_match_guard` — the FULL
`_EDIT_OPS` kind string, prefixed `applicable_`, not an abbreviation.
Chosen over the shorter `applicable_flip`/`applicable_swap`/
`applicable_drop`/`applicable_guard` names `MAC_FAC_A7_A9_RESULTS.md` §5
used when merely SIZING the follow-on (a sketch, not a commitment): the
full-kind-string form is unambiguous by construction (`"applicable_" +
kind` is a pure function of the kind string, no hand-chosen abbreviation
to keep in sync by convention) and greppable against the `_EDIT_OPS`
tuple's own `"kind"` values directly. This does not match
`writes_chosen_action`/`skippable`/`shiftable`'s SHORT-name convention
exactly, but those names describe a single yes/no PROPERTY of the rule
itself; these four describe applicability to four DIFFERENT, enumerable
externally-named things (the `_EDIT_OPS` kinds), so naming each flag after
the specific kind it answers for is the closer fit.

**Function design (registered before writing), mirroring
`_ensure_reply_rule_provenance`'s UPGRADE-IN-PLACE precedent
(`reflective_faculty.py:2968-3050`) more directly than
`_ensure_acting_rule_provenance`'s mint-only precedent, because the target
node here is NOT new** — `RuleSummary` nodes already exist (minted earlier
by `_ensure_acting_rule_provenance`) and this precompute only ADDS four
attrs onto an EXISTING node via `sub.set_attr`, exactly the way
`_ensure_reply_rule_provenance` adds `writes_reply`/`skippable`/`from_seed`
onto an existing `RuleSummary` it did not itself mint:

```python
def _ensure_editop_applicability(sub) -> None:
    from domains import edit_ops as _eo
    import json as _json
    for n in sub.nodes("RuleSummary"):
        attrs = sub.node(n)["attrs"]
        if attrs.get("applicable_flip_comparison") is not None:
            continue   # already stamped -- idempotent skip
        rule_json_str = attrs.get("rule_json")
        try:
            rule_json = _json.loads(rule_json_str) if rule_json_str else {}
        except Exception:
            rule_json = {}
        try:
            kinds = _editop_applicable_kinds(rule_json, _eo) if rule_json else []
        except Exception:
            kinds = []
        try:
            for kind, attr_name in _APPLICABLE_ATTR.items():
                sub.set_attr(n, attr_name, 1.0 if kind in kinds else 0.0)
        except Exception:
            continue
```

Idempotent (presence-of-flag guard, same shape
`_ensure_reply_rule_provenance` uses for `skippable is None`); safe to call
on an empty `RuleSummary` population (loop body never runs); safe on an
unparseable/absent `rule_json` (falls back to all-four-0.0, the same
honest default `_editop_applicable_kinds` itself returns on a degenerate
rule — matches `test_applicable_kinds_empty_on_a_degenerate_rule`'s
already-established semantics in `test_editop_applicability_gate.py`, not
a new convention). No graph decision — every branch either copies an
already-computed Python value onto the graph or safely no-ops.

**Wiring, registered before editing**: called from `_route_experiment_
composer` (`reflective_faculty.py:6243-6247`), immediately after the
EXISTING `if want_structure: _ensure_edit_ops(sub0)` call — the exact call
site `MAC_FAC_A7_A9_RESULTS.md` §3 already named as A7's own "one more
line" closure point, reused here for the same reason: this is the ONE
place in production Python that unconditionally runs before
`compose_experiment_mint_parametric` fires for a `want_structure` concern,
so priming here (not at boot, not inside the Term) matches A7's/A9's own
`where_signature_json` priming precedent exactly — same reachability
shape, same honest residual (a cold, un-primed graph correctly degrades to
"no candidate passes the filter" → an HONEST ABSTAIN of the whole `epick`
pick, not a crash and not a silent wrong answer — registered here as the
predicted degrade-path, to be confirmed in §4).

## 2. The Term edit, registered before editing

**Confirmed by direct read** (not re-derived from the two prior RESULTS
docs' predictions): `epick`'s Argmax (`seeds/composer_experiment_graph.json:1568-1572`)
has exactly one JSON occurrence of `"node_type": "EditOp"` in the WHOLE
file (grep-confirmed unique) — its `"source"` field is the bare
`{"type": "NodesOfType", "node_type": "EditOp"}`, no `Filter` at all,
exactly as `MAC_FAC_A7_A9_RESULTS.md` §5 already found. `epick` is nested
inside `Let{name:"op", value: Let{name:"epick", ...}, body: ...}`, itself
the `other` arm of `IfThenElse(Eq(Var("picked"), Lit(null)), then=<all-empty
MkDict>, other=...)` — `picked` is the OUTER `Let` binding (line 1123) that
wraps A7's own two-Argmax structural-fallback pick (already landed). `Var:
"picked"` is confirmed already referenced later in the SAME lexical scope
(line 1781, `FromJsonString(Attr(Var("picked"), "rule_json"))`), so
`Attr(Var("picked"), "applicable_<kind>")` is a valid read inside `epick`'s
own `source`/`value` position — no restructuring needed, unlike the
concern A7/A9's own PREREG raised and then resolved for THAT site.

**Fix shape (registered before editing), mirroring A4's Python fix exactly
one level up in the Term algebra**: replace the bare `NodesOfType("EditOp")`
source with `Filter(NodesOfType("EditOp"), "s", <applicable-to-picked>)`,
where `<applicable-to-picked>` is
`Or(And(Eq(Attr(s,"kind"), Lit(k1)), Eq(Attr(picked,"applicable_"+k1), Lit(1.0))), ...)`
for the four kinds — a direct Term-algebra transliteration of A4's own
`Or(Eq(Attr(s,"kind"), Lit(k)) for k in applicable_kinds)`, except here the
`applicable_kinds` list cannot be precomputed in Python before the Term is
built (the picked rule is itself a GRAPH-RESIDENT Argmax result, not a
Python value at Term-authoring time — the seed is fixed data, evaluated
fresh on every fire against whichever rule `apick`'s Argmax happens to
pick), so the check is pushed one level INTO the Term: each candidate `s`
is kept iff its OWN `kind` matches one of the four strings AND `picked`'s
correspondingly-named flag reads `1.0`. Every Term type used (`Filter`,
`Or`, `And`, `Eq`, `Attr`, `Lit`, `Var`) already appears elsewhere in this
exact file (A7/A9's own edits). **No new Rust Term — registered as the
expectation, to be confirmed by loading the edited seed in §4, not assumed
true because A7/A9 found it true for a different site.**

**What does NOT change**: the keyword-overlap `overlap(V("s"))` scorer
(`StringIndexOf`/`Sum`, unchanged) — this restricts the CANDIDATE SET
`epick`'s Argmax scores over, exactly mirroring A4's own framing ("this
restricts the candidate set, it does not replace or re-weight the
relevance score").

## 3. A pre-existing regression risk, found during investigation and
registered here BEFORE editing (not discovered after)

Grepping the existing test suite for `drop_match_edge` + `structure`
surfaced that **two already-green tests pin the EXACT pre-fix defect this
rung fixes**, both reached via the REAL `ground_concern` → graph dispatch
path (unlike A4's Python twin, which the prior rung found to be DEAD in
this exact call path):

- `tests/test_experiment_composer_graph.py::test_structure_variant_drop_is_honestly_inert_via_router`
  (line 889-905): residual `["test","send","judge","structure","gradient","drop"]`
  against `hop_descend_gradient` (1 match edge — `drop_match_edge`
  structurally inapplicable, confirmed by the SAME `_HOP` fixture
  `test_editop_applicability_gate.py`/`test_structural_variant.py` already
  use); asserts `sv.get("kind") == "drop_match_edge"` and `"INERT" in
  sv.get("wall", "")` — i.e. it pins the WASTED-ATTEMPT outcome: `drop`
  wins the unfiltered keyword Argmax (score 1, no other kind's blurb
  contains "drop"), then the graph-native per-kind branch discovers,
  post-hoc, that the pick is structurally inert.
- `tests/test_structural_variant.py::test_structural_variant_drop_is_honestly_inert_on_hop_descend_gradient`
  (line 230-242): the SAME residual, SAME rule, SAME assertions, reached
  via a slightly different axis-construction path but the identical
  `ground_concern` → `_route_experiment_composer` → `epick` call chain.

**Predicted new behavior for both, registered before editing (to be
confirmed live in §4/§5, not assumed):** with the applicability filter
wired, `drop_match_edge` can never be `epick`'s pick for `hop_descend_
gradient` (filtered out before scoring). The three REMAINING applicable
kinds (`flip_comparison`, `swap_term_leaf`, `add_match_guard`) all score
`0` against this residual (none of their `keywords_text` blurbs contain
`"drop"`, confirmed by inspection of `_EDIT_OPS`'s own literal blurb
strings — same check `EDIT_OP_APPLICABILITY_GATE_RESULTS.md` §3 already
made for the identical residual on the Python side). So `epick`'s
`Gt(overlap(best), 0.0)` guard (unchanged) fails for every surviving
candidate → `epick` → `null` → `op` → `null` → the outer `Ite(Eq(op,
null), then=<all-empty MkDict>, ...)` branch fires → `edit_op_kind` reads
`""` → `_route_experiment_composer`'s own downstream decode
(`reflective_faculty.py:6318-6339`) falls to its `else:` branch:
`structural_variant = {"built": False, "wall": "the graph-native
RuleSummary or EditOp Argmax abstained (no genuine overlap) — an honest
null, not a random pick"}` — **no `"kind"` key at all**, an HONEST ABSTAIN
replacing the old WASTED-ATTEMPT-THEN-INERT outcome. This is the exact
same class of legitimate behavior change `EDIT_OP_APPLICABILITY_GATE_
RESULTS.md` §3 already documented and accepted for A4's own "drop alone"
case ("a strictly more honest outcome... an abstain instead of a
guaranteed-null attempt") — the difference here is that A8's version of
this same case is pinned by TWO live, currently-green tests (A4's was not,
because A4 was dead code at the time).

**Disposition, registered before editing**: both tests will be UPDATED (not
deleted, not skipped) to assert the new, honest abstain shape, with an
inline comment citing this doc and explaining why the old assertion
described a wasted attempt this rung correctly eliminates. This is the
SAME test-file discipline `EDIT_OP_APPLICABILITY_GATE_PREREG.md` itself
used for its own "CORRECTION, added after the first baseline capture" —
registering a found fact honestly, before it is acted on, rather than
silently absorbing it into an unexplained diff. The regression bar
(§5 below) is measured explicitly INCLUSIVE of this one predicted,
intentional, from-red-to-updated-and-green change — it is not counted as
an unexplained regression, and no OTHER test is expected to change.

## 4. Validation steps, run after EACH edit (not just at the end) —
mirroring `MAC_FAC_A7_A9_PREREG.md` §4 exactly

1. `python3 -c "import json; json.load(open('seeds/composer_experiment_graph.json'))"`
   — still valid JSON, after the Term edit.
2. The seed still loads (`boot_all`/the narrowest available loader) with no
   new error; node/edge counts for `composer_experiment_graph.json`
   unchanged (a `Filter` wrap changes ONE subtree's shape, not the
   Rule-node count).
3. The Rule still installs (`native.add_rule` on the edited `effect` Term
   does not raise) and still fires correctly on an UNRELATED regression
   probe (a combo that does not touch `has_structure` at all, e.g. the
   gradient-only or judge-alone combos) — confirms the edit did not
   perturb anything outside the `epick` subtree.
4. `tests/test_experiment_composer_graph.py` + `tests/test_composers_graph.py`
   run to completion; failing-node-id list captured and diffed against the
   BEFORE baseline (captured once, before ANY edit, this worktree, this
   commit) — expected diff: exactly the two tests named in §3 change from
   PASS to FAIL immediately after the Term edit (before those two tests
   are themselves updated), and back to PASS once updated. Captured
   per-edit: after the precompute (Python-only, no Term touched yet — the
   two named tests should be UNCHANGED, still green, since `epick`'s Term
   itself hasn't moved yet); after the Term edit (the two named tests flip
   red, predicted); after updating the two tests' assertions (back to
   green, with the NEW assertions).
5. The Class-A/Class-B live demonstration (§5 below).

## 5. The Class-A/Class-B demonstration, registered before it is run

**Class A (structurally-inapplicable op wins the unfiltered keyword
Argmax) — reuses the exact scenario already found in §3, through the REAL
loaded seed, fired via `ground_concern`, not a standalone Term
evaluation:** rule `hop_descend_gradient` (1 match edge), residual
`["test", "send", "judge", "structure", "gradient", "drop"]`.
Hand-computed keyword-overlap scores (same table
`EDIT_OP_APPLICABILITY_GATE_RESULTS.md` §3 already established for the
Python side, reused here because the blurbs and the residual are
identical):

| kind | score | structurally applicable to `hop_descend_gradient`? |
|---|---|---|
| `drop_match_edge` | **1** (unique nonzero) | **NO** (1 match edge) |
| `flip_comparison` | 0 | yes |
| `swap_term_leaf` | 0 | yes |
| `add_match_guard` | 0 | yes |

**OLD (pre-edit) expected**: `epick` picks `drop_match_edge` (only nonzero
score), the graph-native drop branch discovers zero valid drop sites on
this rule, wall names `"INERT"`, `kind == "drop_match_edge"` — captured
live from the two currently-green tests named in §3 before any edit.

**NEW (post-edit) expected**: `drop_match_edge` filtered out of `epick`'s
candidates before scoring (not structurally applicable to the `picked`
rule); the three remaining candidates all score 0; `Gt(overlap(best), 0.0)`
fails; `epick` → `null` → honest abstain, no `"kind"` key, wall names
`"abstained"`/`"no genuine overlap"`, and — the specific negative check
that proves the filter actually excluded it rather than merely failing to
mention it — `"drop_match_edge"` does NOT appear anywhere in the wall
text (mirrors `test_editop_applicability_gate.py`'s own analogous check,
line 190).

**Class B (keyword-best op is ALSO applicable — must stay byte-identical)
— reuses `test_served_by_ledger_structure_combo_is_graph_for_flip`/`_swap`
and `test_structural_variant_pick_is_discriminative`'s existing flip/swap/
guard rows directly**, no new residual needed: `flip`/`swap`/`guard` cues
against `hop_descend_gradient`, where the keyword-best kind is ALSO the
structurally-applicable one (all three are applicable on this rule — only
`drop_match_edge` is not). Predicted: unchanged before/after, confirmed by
these three EXISTING tests staying green with NO assertion changes,
exercised directly, not re-derived.

**Negative control, registered before running**: a residual matching NO
op's blurb at all (e.g. the existing `test_structural_variant_abstains_
without_genuine_rule_overlap` — no `grid_navigation` loaded, so the
RuleSummary Argmax itself abstains before `epick` is ever reached) must
stay an honest abstain both before and after — confirms the fix does not
widen or narrow the OUTER (`apick`) abstain condition, only the inner
(`epick`) one.

## 6. What this will NOT establish (registered before editing, to be
confirmed unchanged in the RESULTS doc)

- Does not touch A4 (`_editop_applicable_kinds`/`_compose_structural_
  variant`) — reused by reference only.
- Does not touch A5/A6/A7/A9.
- Does not measure prevalence (how often, on a real agent's real
  self-experiment concerns, the keyword-best EditOp is genuinely
  inapplicable to the picked rule) — a synthetic-proven mechanism, not a
  benchmark value, same honest boundary every sibling rung in this family
  has drawn.
- Does not make the precompute run at boot or from any path other than
  `_route_experiment_composer`'s own `want_structure` branch — a cold
  graph that reaches `epick` some OTHER way (if one exists) would find the
  `applicable_*` flags absent and degrade to the all-candidates-filtered
  (fully empty) case, i.e. an unconditional abstain — registered here as
  the predicted (not yet the norm-everywhere) reachability shape, same
  class of residual A7/A9 already named for `where_signature_json`.
