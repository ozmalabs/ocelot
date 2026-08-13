# MAC/FAC A8 — `epick`'s applicability-gate precompute — RESULTS

Companion to `MAC_FAC_A8_PREREG.md` (read first — it registers the four flag
names, the precompute function design, the Term-edit mechanism, and the
Class-A/Class-B validation scenario before any code was touched). Closes the
LAST remaining `SHAPE_AUDIT.md` §2.1 site in the `keywords_text`-family
MAC/FAC audit: A1/A2 (`RULE_SIGNATURE_PRODUCTION_WIRING_RESULTS.md`), A3
(`SEED_PICK_STRUCTURAL_FALLBACK_RESULTS.md`), A4
(`EDIT_OP_APPLICABILITY_GATE_RESULTS.md`), A5/A6
(`MAC_FAC_A5_A6_RESULTS.md`), A7/A9 (`MAC_FAC_A7_A9_RESULTS.md`) were already
landed; A8 was found by A7/A9 §5 and sized, precisely, as a follow-on this
rung now builds.

**Worktree:**
`/tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/mac-fac-a8`,
branch `mac-fac-a8`, detached from `main` at `b768b7b` (verified:
`git log --oneline -1 main` → `b768b7b Merge mac-fac-a5-a6: structural
fallback for datum-feedback and rule-literal picks, GO`). No Rust touched.

---

## GO. The precompute closes A8 exactly as A7/A9 §5 sized it; zero measured
regression beyond one PREDICTED, correctly-updated test pair; the whole
`keywords_text`-family MAC/FAC audit (A1-A9) is now closed.

---

## 1. The precompute, as built

`domains/reflective_faculty.py` — two new pieces, immediately after
`_editop_applicable_kinds` (`:4190-4218`, UNTOUCHED, called directly, not
reimplemented):

- `_APPLICABLE_ATTR` (`:4221-4227`): a dict mapping each `_EDIT_OPS` kind
  string to its RuleSummary attr name — the FULL kind string, prefixed
  `applicable_` (`applicable_flip_comparison`, `applicable_swap_term_leaf`,
  `applicable_drop_match_edge`, `applicable_add_match_guard`), not the
  shorter `applicable_flip`/`applicable_swap`/`applicable_drop`/
  `applicable_guard` sketch `MAC_FAC_A7_A9_RESULTS.md` §5 used when merely
  SIZING the follow-on — registered in the PREREG as the deliberate,
  considered choice (unambiguous by construction: `"applicable_" + kind` is
  a pure function of the kind string).
- `_ensure_editop_applicability(sub)` (`:4230-4275`): walks every
  `RuleSummary` node, and for one carrying a `rule_json` but not yet
  stamped (`applicable_flip_comparison is None` as the idempotency guard,
  the SAME presence-check shape `_ensure_reply_rule_provenance` uses for
  `skippable is None`), calls `_editop_applicable_kinds(rule_json, _eo)`
  and `sub.set_attr`s all four flags (`1.0`/`0.0`). Mirrors
  `_ensure_reply_rule_provenance`'s UPGRADE-IN-PLACE precedent
  (`reflective_faculty.py:2968-3050`) — not `_ensure_acting_rule_
  provenance`'s mint-only one — because the target `RuleSummary` nodes
  already exist (minted earlier by `_ensure_acting_rule_provenance`); this
  function only ADDS attrs onto an EXISTING node. Falls back to all-four
  `0.0` on an absent/unparseable `rule_json`, the same honest default
  `_editop_applicable_kinds` itself returns on a degenerate rule.

**Reuse discipline confirmed**: `_editop_applicable_kinds` is called
directly, never reimplemented — grep confirms exactly one definition of the
four predicates in the tree (`domains/reflective_faculty.py:4190`); the
precompute and A4's own `_compose_structural_variant` both call the SAME
function.

**Wiring** — `_route_experiment_composer` (`:6308-6320`), immediately after
the EXISTING `if want_structure: _ensure_edit_ops(sub0)` call (the exact
call site `MAC_FAC_A7_A9_RESULTS.md` §3 already named as A7's own
"one more line" closure point):

```python
    if want_structure:
        try:
            _ensure_edit_ops(sub0)
        except Exception:
            pass
        try:
            _ensure_editop_applicability(sub0)
        except Exception:
            pass
```

This is the ONE place in production Python that unconditionally runs
before `compose_experiment_mint_parametric` fires for a `want_structure`
concern — same reachability shape A7/A9 already established for
`where_signature_json` priming, same honest residual (a cold, un-primed
graph correctly degrades to "no candidate passes the filter," confirmed
live in §4).

---

## 2. The Term edit, and how rule-resolution works inside `epick`'s scope

**Confirmed by direct read, one occurrence in the whole file**
(`grep -n '"node_type": "EditOp"' seeds/composer_experiment_graph.json` →
exactly one hit, pre-edit line 1571). `epick`'s Argmax
(`seeds/composer_experiment_graph.json`, inside `compose_experiment_mint_
parametric`'s single Rule node) had a bare `"source": {"type":
"NodesOfType", "node_type": "EditOp"}` — no `Filter` at all, exactly as
`MAC_FAC_A7_A9_RESULTS.md` §5 found and this rung's PREREG predicted.

**Rule-resolution — confirmed reachable, no restructuring needed.**
`epick` is nested `Let{"op", value: Let{"epick", ...}, body: ...}`, itself
the `other` arm of `IfThenElse(Eq(Var("picked"), Lit(null)), then=<all-empty
MkDict>, other=...)`. `Var("picked")` is the OUTER `Let` binding (line
1123-1502, A7's own two-Argmax structural-fallback pick, already landed and
untouched here) that wraps the ENTIRE rest of this branch's body — `epick`
sits lexically inside it. This was independently re-confirmed (not merely
assumed from A7/A9's own note) by finding `Var: "picked"` already read
later in the SAME scope (`FromJsonString(Attr(Var("picked"),
"rule_json"))`, line 1781 pre-edit) — `Attr(Var("picked"),
"applicable_<kind>")` is therefore a valid read at `epick`'s own `source`
position, using the identical binding, no new plumbing required.

**The edit**: replace the bare `NodesOfType("EditOp")` source with
`Filter(NodesOfType("EditOp"), "s", <applicable-to-picked>)`, where
`<applicable-to-picked>` is
`Or(And(Eq(Attr(s,"kind"), Lit(k1)), Eq(Attr(picked, "applicable_"+k1),
Lit(1.0))), ...)` for all four kinds — a direct Term-algebra
transliteration of A4's own `Or(Eq(Attr(s,"kind"), Lit(k)) for k in
applicable_kinds)`, pushed one level INTO the Term because `applicable_kinds`
cannot be precomputed in Python before the Term is authored here (the
picked rule is itself a fresh graph-resident Argmax result on every fire,
not a fixed Python value at seed-authoring time): each candidate `s` is
kept iff its OWN `kind` matches one of the four strings AND `picked`'s
correspondingly-named flag reads `1.0`. Every Term type used (`Filter`,
`Or`, `And`, `Eq`, `Attr`, `Lit`, `Var`) already appears elsewhere in this
exact file (A7/A9's own edits) — **confirmed, not merely assumed: no new
Rust Term was needed.** The keyword-overlap `overlap(V("s"))` scorer
(`StringIndexOf`/`Sum`) is byte-unchanged — the edit restricts the
candidate set the existing Argmax scores over, it does not replace or
re-weight the relevance signal.

**File-size delta**: `seeds/composer_experiment_graph.json` grew by 41
lines (`git diff --stat`); node/edge counts UNCHANGED (`3` nodes, `0`
edges, confirmed by `json.load` before and after) — a `Filter` wrap changes
one subtree's shape, not the Rule-node count, matching the correctness
invariant A7/A9 already established for this same discipline.

---

## 3. A pre-existing regression risk, found during investigation and
registered in the PREREG BEFORE editing — confirmed live, exactly as
predicted

Two already-green tests pinned the EXACT pre-fix defect this rung fixes,
both reached via the REAL `ground_concern` → graph dispatch path (unlike
A4's Python twin, which the prior rung found DEAD in this exact call path):
`tests/test_experiment_composer_graph.py::test_structure_variant_drop_is_
honestly_inert_via_router` and `tests/test_structural_variant.py::test_
structural_variant_drop_is_honestly_inert_on_hop_descend_gradient`. Both
used residual `["test","send","judge","structure","gradient","drop"]`
against `hop_descend_gradient` (1 match edge — `drop_match_edge`
structurally inapplicable) and asserted the OLD, wasted-attempt outcome
(`sv.get("kind") == "drop_match_edge"`, `"INERT" in wall`).

**Captured live, per-edit, exactly as registered:**

1. **Baseline** (before any edit): `test_experiment_composer_graph.py` +
   `test_composers_graph.py` → **10 failed, 98 passed** (pre-existing,
   unrelated — see §5); both `drop`-honesty tests green.
2. **After the Python precompute alone** (Term not yet touched): SAME
   10 failed/98 passed, byte-identical node-id list — `epick`'s Term hadn't
   moved yet, so behavior is unchanged even though the flags now exist on
   the graph.
3. **After the Term edit** (tests not yet updated): the SAME background run
   captured on the pre-edit test files shows **11 failed** — the 10
   baseline PLUS `test_structure_variant_drop_is_honestly_inert_via_router`
   flipping red, exactly as predicted (`drop_match_edge` now filtered out
   of `epick`'s candidates for `hop_descend_gradient`; the three remaining
   kinds all score 0 against this residual — none of their `keywords_text`
   blurbs contain "drop" — so `epick` abstains honestly instead of picking
   `drop_match_edge` and discovering it inert post-hoc).
4. **After updating both tests' assertions** to the new, honest abstain
   shape (`sv.get("kind") is None`, `"abstained" in wall`,
   `"drop_match_edge" not in wall` — mirroring `test_editop_applicability_
   gate.py`'s own analogous "drop alone" check): synchronous re-run,
   `test_experiment_composer_graph.py` + `test_composers_graph.py` → **10
   failed, 98 passed**, the SAME node-id list as the baseline; the broader
   net (`test_structural_variant.py` + `test_acting_variant.py` +
   `test_experiment_composer.py` + `test_editop_applicability_gate.py`) →
   **2 failed, 44 passed, 3 deselected**, the SAME node-id list as its own
   baseline.

This is the exact class of legitimate behavior change
`EDIT_OP_APPLICABILITY_GATE_RESULTS.md` §3 already documented and accepted
for A4's own "drop alone" case — the difference here is A8's version was
pinned by two LIVE, currently-green tests (A4's was not, because A4 was
dead code at the time this class of change was first found). Both tests
were updated, not deleted or skipped, with an inline comment citing this
doc and explaining why the old assertion described a wasted attempt this
rung correctly eliminates.

---

## 4. The Class-A/Class-B/negative-control demonstration — through the
REAL loaded seed, fired via `rf.ground_concern` (`demo_a8.py`, this
worktree)

**Class A** — `hop_descend_gradient` (1 match edge), residual
`["test","send","judge","structure","gradient","drop"]`. Hand-computed
keyword-overlap scores (reused from `EDIT_OP_APPLICABILITY_GATE_RESULTS.md`
§3's own identical-blurb table — the same residual, same rule, same
blurbs):

| kind | score | structurally applicable to `hop_descend_gradient`? |
|---|---|---|
| `drop_match_edge` | **1** (unique nonzero) | **NO** (1 match edge) |
| `flip_comparison` | 0 | yes |
| `swap_term_leaf` | 0 | yes |
| `add_match_guard` | 0 | yes |

Captured live:

```
served_by: graph
structural_variant: {"built": false, "wall": "the graph-native RuleSummary or
EditOp Argmax abstained (no genuine overlap) — an honest null, not a random
pick"}
[Class A] PASS -- inapplicable op filtered out, honest abstain, never a wasted attempt
hop_descend_gradient RuleSummary applicability flags:
{'applicable_flip_comparison': 1.0, 'applicable_swap_term_leaf': 1.0,
 'applicable_drop_match_edge': 0.0, 'applicable_add_match_guard': 1.0}
[Class A] PASS -- precompute stamped the correct four flags on the picked RuleSummary
```

No `"kind"` key in the result at all — `drop_match_edge` is never named as
a candidate, filtered out BEFORE scoring, not picked-then-discovered-inert.
The RuleSummary's own stamped flags confirm the precompute got the right
answer independently of the pick's own outcome.

**Class B (×3, flip/swap/guard) — byte-identical before/after**, the
keyword-best op is ALSO structurally applicable on this rule, so the filter
never excludes it:

```
[Class B: flip] kind=flip_comparison built=true
[Class B: swap] kind=swap_term_leaf built=true
[Class B: guard] kind=add_match_guard built=true
```

All three match the pre-existing, still-green
`test_served_by_ledger_structure_combo_is_graph_for_flip`/`_swap` and
`test_structural_variant_pick_is_discriminative`'s own flip/swap/guard rows
— unchanged, confirmed by those tests staying green with NO assertion
edits (only the `drop` rows needed updating, §3).

**Negative control** — no `grid_navigation` loaded at all, so `apick`
(the OUTER RuleSummary Argmax, A7) abstains before `epick` is ever reached:

```
structural_variant: {"built": false, "wall": "the graph-native RuleSummary or
EditOp Argmax abstained (no genuine overlap) — an honest null, not a random
pick"}
[Negative control] PASS -- honest abstain, outer pick never reaches epick
```

Confirms the fix does not widen or narrow the OUTER abstain condition —
only the inner (`epick`) one, exactly as scoped.

---

## 5. Regression, captured per-edit (not just once at the end)

**`tests/test_experiment_composer_graph.py` + `tests/test_composers_graph.py`**
(`-k "not slow"`):

| stage | result | node-id list |
|---|---|---|
| baseline (before any edit) | 10 failed, 98 passed | identical to `MAC_FAC_A7_A9_RESULTS.md`'s own final table |
| after precompute (Term untouched) | 10 failed, 98 passed | byte-identical to baseline |
| after Term edit (tests not yet updated) | 11 failed, 97 passed | baseline 10 + `test_structure_variant_drop_is_honestly_inert_via_router` (predicted, §3) |
| after updating the two `drop`-honesty tests | **10 failed, 98 passed** | **byte-identical to baseline**, confirmed synchronously |

The 10 pre-existing failures (unchanged throughout, not investigated
further — pre-existing on the unmodified tip, same as A7/A9's own §6
finding): `test_full_combo_gradient_embed_matches_shift_rule_thresholds_
oracle`, `test_test_alone_graph_rule_mints_experiment_without_host_add_
node`, `test_vary_bare_structurally_matches_python_oracle`,
`test_vary_bare_graph_rule_fires_and_picks_skip_seeds`,
`test_embed_graph_rule_fires_and_embeds_a_real_variant`,
`test_parametric_mint_matches_python_oracle_matrix[bare_vary/embed/
vary_no_send/vary_plus_structure/vary_embed_plus_gradient]`.

**Broader net** (`tests/test_structural_variant.py` +
`tests/test_acting_variant.py` + `tests/test_experiment_composer.py` +
`tests/test_editop_applicability_gate.py`, `-k "not slow"`):

| stage | result |
|---|---|
| baseline (before any edit) | 2 failed, 44 passed, 3 deselected |
| after both edits + both test updates | **2 failed, 44 passed, 3 deselected** — same 2 node ids (`test_close_experiment_loop_names_the_varied_acting_rule`, `test_mint_rule_fires_without_host_add_node`), both independently already documented as pre-existing in `SEED_PICK_STRUCTURAL_FALLBACK_RESULTS.md`'s own AR4 baseline and reconfirmed present, unrelated to this rung's edits, by `MAC_FAC_A7_A9_RESULTS.md` §6 |

`tests/test_editop_applicability_gate.py`'s own 8 tests (A4, dead-in-
production but directly-callable code, untouched by this rung) are part of
the 44 green — all pass, confirming this rung did not disturb A4 itself.

**Zero test anywhere in either regression net went from green to red
without an explicit, predicted, cited update** — the one intentional
exception (§3) was registered in the PREREG before the Term edit, captured
red at the exact predicted moment, then updated back to green with
assertions matching the new, more honest behavior.

---

## 6. What this does NOT establish

- **Does not touch A4** (`_editop_applicable_kinds`/`_compose_structural_
  variant`) — reused by direct call only, logic unmodified, confirmed by
  `test_editop_applicability_gate.py`'s own 8 tests staying green with zero
  edits.
- **Does not touch A5/A6/A7/A9** — their own landed fixes are untouched by
  this rung's diff (confirmed: `git diff --stat` shows only
  `domains/reflective_faculty.py`, `seeds/composer_experiment_graph.json`,
  and the two test files this rung itself edited).
- **Does not make the precompute run at boot or from any path other than
  `_route_experiment_composer`'s own `want_structure` branch** — a cold
  graph that reaches `epick` some other way would find the `applicable_*`
  flags absent on `picked` and degrade to the fully-filtered (empty
  candidate set) case, i.e. an unconditional `epick` abstain — the same
  class of reachability residual A7/A9 already named for
  `where_signature_json`, not solved here, not newly introduced either
  (before this rung, a cold graph produced a WRONG or wasted pick instead
  of an abstain — arguably a worse degrade than this rung's).
- **Does not measure prevalence** — how often, on a real agent's real
  self-experiment concerns, the keyword-best EditOp is genuinely
  inapplicable to the picked rule. A synthetic-proven mechanism, not a
  benchmark value: this closes a real, demonstrated MAC/FAC gap at one
  specific, previously-follow-on-sized graph-resident site, through the
  REAL loaded seed — it says nothing about how often, in production, this
  situation arises. No prevalence measurement was in scope or attempted,
  the same honest boundary every sibling rung in this family has drawn.
- **Does not re-litigate the four flag-naming convention** against
  `writes_chosen_action`/`skippable`/`shiftable`'s shorter style — the
  PREREG registered the full-kind-string naming as the better fit for a
  multi-valued applicability question, not a claim that it is the ONLY
  defensible choice.

---

## 7. Closing status: the WHOLE `keywords_text`-family MAC/FAC audit
(A1-A9) is now closed

| site | what | status |
|---|---|---|
| A1 | `_pick_acting_rule` (Python) | closed — `RULE_SIGNATURE_PRODUCTION_WIRING_RESULTS.md` |
| A2 | `_pick_reply_rule` (Python) | closed — same doc |
| A3 | `_compose_experiment_rule`'s seed-skip Argmax (Python) | closed — `SEED_PICK_STRUCTURAL_FALLBACK_RESULTS.md` |
| A4 | `_compose_structural_variant`'s EditOp Argmax (Python) | closed — `EDIT_OP_APPLICABILITY_GATE_RESULTS.md` (confirmed dead-in-production, shadowed by A8, but fixed correctly and independently) |
| A5 | datum-feedback pick (graph) | closed — `MAC_FAC_A5_A6_RESULTS.md` |
| A6 | rule-literal pick (graph) | closed — same doc |
| A7 | `apick`/`best` RuleSummary Argmax ×2 (graph) | closed — `MAC_FAC_A7_A9_RESULTS.md` |
| A8 | `epick` EditOp Argmax (graph) | **closed by THIS rung** — applicability-gate precompute + Filter, the fix shape A4 needed but A7/A9's structural-fallback shape could not supply |
| A9 | `skip_id`/`best` SeedSummary Argmax ×2 (graph) | closed — `MAC_FAC_A7_A9_RESULTS.md` |

Every `keywords_text`-only Argmax the `SHAPE_AUDIT.md` §2.1 sweep found now
has either a structural fallback (A1/A2/A3/A5/A6/A7/A9, where a comparable
per-candidate structural signature exists to fall back to) or an
applicability gate (A4/A8, where the relevant structural question is not
"which candidate has more where-clause overlap" but "is the keyword-best
candidate even POSSIBLE given what's already been picked"). No open site
remains in this family. This does not mean the codebase is now free of
scalar-knob-shaped defects (`SHAPE_AUDIT.md`'s own 40 confirmed sites and
the wider tree sweep both name many more, unrelated families) — it means
this ONE well-scoped family, opened by `RULES_AS_SHAPE_DESIGN_SPIKE.md`'s
original MAC/FAC diagnosis, is now fully closed, end to end, Python and
graph twins alike.

---

## Worktree / reproduce

```bash
cd /tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/mac-fac-a8
git log --oneline -1                                   # on mac-fac-a8, base b768b7b
python3 -c "import json; json.load(open('seeds/composer_experiment_graph.json'))"   # valid JSON
python3 demo_a8.py                                      # Class A/B + negative control
python3 -m pytest tests/test_experiment_composer_graph.py tests/test_composers_graph.py -q -k "not slow"
python3 -m pytest tests/test_structural_variant.py tests/test_acting_variant.py tests/test_experiment_composer.py tests/test_editop_applicability_gate.py -q -k "not slow"
```
