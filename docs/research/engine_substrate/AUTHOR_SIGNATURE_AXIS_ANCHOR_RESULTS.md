# `author_signature` AXIS-ANCHORING — RESULTS

Prereg: `AUTHOR_SIGNATURE_AXIS_ANCHOR_PREREG.md`, same commit series, base `main` at
`6805175`. Worktree `/home/matt/ozmadev/ocelot-worktrees/author-signature-axis-anchor`,
branch `author-signature-axis-anchor`.

**Verdict: GO.** All three registered predictions (P1, P2, P3) confirmed exactly.
The false positive `SHAPE_KIND_FIELD_RESULTS.md` §2.2 measured live drops from
`fixed=1` to `fixed=0`; a genuine true-positive pairing (two signatures that really
share a named cue) goes from an accidental `fixed=1` to a principled `fixed=8`
(the FULL two shared 4-element relation tuples, not a one-token coincidence); the one
existing pinned agent decision through the two named call sites
(`learn_term_for_concern`/`_run_math_bridge`) is unchanged. Zero regressions: 33/33
pre-fix baseline, 39/39 post-fix (33 pre-existing + 6 new, all green).

---

## 1. The fix, and where it landed (and where it deliberately did not)

`_shared_shape` (`domains/reflective_faculty.py:7170-7207` post-fix) no longer pairs
`sig_a`/`sig_b` by raw list position (`sig_a[:n]` vs `sig_b[:n]`). It now pairs a row
from `sig_a` with a row from `sig_b` **only when both are byte-identical to the same
held `RelationCue.relation` tuple** — looked up via a new cached reverse index,
`_relation_cue_index(substrate)` (`:7137-7167`), `{tuple(relation): cue_name}` built
once from the 52 `RelationCue` nodes. A row that matches no held cue (a
`CapabilityAxis`-residual bare predicate, or a rare hand-authored seed row that isn't
an exact cue-template copy) contributes no axis and is excluded from the comparison —
never force-aligned by position.

**`author_signature`'s own return contract (`:7112-7134`) is untouched — byte-for-byte
identical before and after this rung** (confirmed: `git diff` touches only
`_shared_shape` and the new `_relation_cue_index` helper; `author_signature`'s own
lines are absent from the diff, see §6). This is a registered judgment call
(PREREG §2.1), not an oversight: `author_signature`'s output is consumed by ~10 sites
outside the two named call sites —

- `induce_concern` (the SD-loop dequantize/mint path), reached both from
  `learn_term_for_concern` itself (the induced-residual branch) and directly from
  `conversation_action._act_author_concern` and ~8 `scripts/jabberwock_*.py`
  self-authoring scripts;
- `grow_part_library` (`:7354-7396`), which installs the raw signature verbatim as a
  NEW `ShapeSignature{kind:'authored'}.signature` — a format every other
  `ShapeSignature` in that pool already shares;
- `goal_signature_from_held_concept` (`:7312-7333`) → the beam composer
  (`compose_design_for_goal`).

`_shared_shape` has **exactly two callers in the whole tree** (re-verified this rung:
`grep -n "_shared_shape(" domains/*.py scripts/*.py tests/*.py` → both inside
`reflective_faculty.py`, lines 1131/7135ish → `learn_term_for_concern` and
`_run_math_bridge`, matching the PREREG's earlier grep). Fixing the sole, exclusive
consumption point for both named call sites, instead of rewriting `author_signature`'s
return type to a fixed 52-row `["cue:<name>", tuple-or-ABSENT]` vector (the literal
reading of "make `author_signature`'s output axis-anchored"), avoids corrupting the
~10 other consumers' existing behaviour with a format none of them expect — the exact
"signature format zoo" risk `SHAPE_TYPE_VOCABULARY_SPIKE.md` §3.2 already flagged
earlier in this same-day arc. Every one of those ~10 callers is therefore untouched by
construction, not verified safe after the fact by testing.

A second reason this was the right locus, found while designing the alternative: the
literal `["cue:<name>", tuple-or-ABSENT]` full-vocabulary vector, run through the raw
`FixedCount(AntiUnify(...))` `_shared_shape` already used, would have introduced a
NEW bug — two signatures that share NO real structure but are both missing the SAME
axis would register a spurious shared leaf on the axis-name LABEL itself (`"cue:foo"
== "cue:foo"` even when both values are the absent sentinel). `analogical_thinking`'s
own `_pair_witness` (`analogical_thinking.py:414+`) works around exactly this with an
extra ABSENT-projection step the docstring calls out explicitly ("shared ABSENT is not
shared structure"). The cue-identity-keyed pairing built here never emits an absent
row at all — only cues that fired on BOTH sides ever reach `AntiUnify` — so no such
projection step is needed, and no analogous bug was introduced.

---

## 2. P1 — the false positive, before/after, live

Exact `SHAPE_KIND_FIELD_RESULTS.md` §2.2 repro, re-run through the REAL
`domains.reflective_faculty._shared_shape` (not a standalone reimplementation — the
BEFORE side is a frozen, verbatim copy of the pre-fix function, run against the same
live agent for a true side-by-side; script:
`scripts/author_signature_axis_anchor_probe.py`):

```
concept_a (self-reference/recursion) = [['refers','NEW','to','SELF'], ['build','NEW','from','PRIOR'], ['base','STOP']]
concept_b (symmetry, unrelated)       = [['map','PART','to','PART'], ['invariant','PART','under','TRANSFORM'], ['repeat','PART']]

BEFORE (positional zip):     result=((('·?·',),('·?·',),'to',('·?·',)), (('·?·',),('·?·',),('·?·',),('·?·',)), (('·?·',),('·?·',)))
BEFORE fixed (shared leaves) = 1

AFTER  (cue-identity keyed): result=None
AFTER  fixed (shared leaves) = 0
```

`fixed` drops from **1 → 0**. `concept_a`'s fired cues (`self_reference`,
`build_from_prior`, `base_case`) and `concept_b`'s fired cues (`map_part_to_part`,
`invariant_under`, `repeat`) are disjoint sets — zero shared axes, zero shared leaves,
honestly.

---

## 3. P2 — the true positive, before/after, live

Two signatures that genuinely fire the SAME cues (`self_reference`,
`build_from_prior`), authored in a DIFFERENT row order — exactly what two
independently-scanned concepts (author_signature's own scan-order accident) would
produce:

```
sig_c (fires build_from_prior, self_reference, base_case) = [['build','NEW','from','PRIOR'], ['refers','NEW','to','SELF'], ['base','STOP']]
sig_d (fires self_reference, bounded, build_from_prior)    = [['refers','NEW','to','SELF'], ['bound','SELF','by','UNIT'], ['build','NEW','from','PRIOR']]

BEFORE (positional zip):     result=((('·?·',),'NEW',('·?·',),('·?·',)), (('·?·',),('·?·',),('·?·',),('·?·',)), ('·?·',))
BEFORE fixed (shared leaves) = 1

AFTER  (cue-identity keyed): result=[['build','NEW','from','PRIOR'], ['refers','NEW','to','SELF']]
AFTER  fixed (shared leaves) = 8
```

`fixed` goes from an accidental **1** (the old code happened to align `sig_c[0]` with
`sig_d[0]`, sharing only the `"NEW"` token by position) to a principled **8** — both
of the genuinely shared cues (`build_from_prior`, `self_reference`, 4 elements each)
are recognised in full. **Not a lobotomy: the true positive is not merely preserved,
it is measured MORE accurately** — the old number undercounted real shared structure
by accident in the same motion it overcounted unrelated structure elsewhere.

`tests/test_author_signature_axis_anchor.py::test_pairing_is_order_independent` pins
the general property this demonstrates: reversing `sig_d`'s row order leaves `fixed`
unchanged (axis-anchoring means position carries no information at all, either
direction).

---

## 4. P3 — the pinned agent decision, unchanged

`author_cost_salience` (`scripts/jabberwock_costs_its_frontier.py:151-162`) exercises
`learn_term_for_concern` end-to-end (via `induce_concern`'s induced-residual path) and
is the SAME scenario `tests/test_cost_scheduling.py::
test_authored_donkey_zero_and_matches_residual_recurrence_keystone` pins.

```
author_cost_salience(agent)["term_family"] = 'residual_recurrence'   (before AND after)
```

Unchanged, for a structural reason worth stating rather than assuming: this scenario's
`sig` comes from the `CapabilityAxis`-residual branch (`[[p] for p in preds]`, bare
single-token predicate rows), which — as `SHAPE_KIND_FIELD_RESULTS.md` §2.1 already
measured — pairs against every seeded `kind:'faculty'` signature at `fixed=0` under
BOTH the old (arity-mismatch WILD collapse) and the new (no cue matches a single-token
row) comparison. `Argmax` over an all-zero `[fixed, name]` list is a tie-break, and its
result depends only on `pairs`' construction order (`fac_sigs.items()`, untouched by
this fix) — so this scenario's `term_family` was never actually testing `_shared_shape`
discrimination in the first place. It is reported here as the registered P3 gate
anyway, exactly as chartered, and it holds.

---

## 5. Known, accepted residual (named, not fixed — explicitly out of scope)

Census over every seeded `math_capability_shapes.json` row (`kind in {math, faculty}`,
17 signatures, 53 rows total) against the 52 `RelationCue.relation` tuples by exact
equality: **3 rows have no exact cue match** — `fractal`'s and `self_similarity`'s
`["bound","SELF","by","SCALE"]` (a hand-authored near-variant of the `bounded` cue's
`["bound","SELF","by","UNIT"]` template), and `order_invariant_binding`'s
`["correspond","PARTS"]`. These 3 rows were never produced by `author_signature`
(they are hand-authored directly into the seed JSON) and are part of the SAME
"`RelationCue` placeholder-token reuse" family the charter marks explicitly out of
scope for this rung. Under cue-identity-keyed pairing they simply contribute no axis
wherever they appear — `fractal`/`self_similarity` still connect to
`residual_recurrence`-family faculties via their OTHER 3 exactly-matching rows
(`build_from_prior`, `self_reference`, `base_case`); nothing in the regression suite
locks in an exact `shared_leaves` count for these three concepts, so this residual
changes no tested decision (verified: 39/39 green, §6).

---

## 6. Regression

Both runs use the same three files the PREREG named as touching
`author_signature`/`_shared_shape`/`learn_term_for_concern`
(`tests/test_cost_scheduling.py`, `tests/test_nl_concern_front_door.py`,
`tests/test_compilation_cycle.py`), plus the new pinned file for this fix
(`tests/test_author_signature_axis_anchor.py`, 6 tests: false-positive-gone,
true-positive-preserved, order-independence, CapabilityAxis-residual refusal survives,
`author_signature`'s own return contract is byte-unchanged, and P3).

```
BEFORE (worktree at 6805175, pre-fix):
$ python3 -m pytest tests/test_cost_scheduling.py tests/test_nl_concern_front_door.py \
                     tests/test_compilation_cycle.py -q
33 passed in 277.39s

AFTER (fix applied + new test file added):
$ python3 -m pytest tests/test_cost_scheduling.py tests/test_nl_concern_front_door.py \
                     tests/test_compilation_cycle.py tests/test_author_signature_axis_anchor.py -q
39 passed in 353.35s
```

**No regressions. No failing node ids, before or after — paired list is empty by
construction (33/33 → 39/39, the +6 delta is exactly the new file).**

`git diff --stat` confirms the fix's footprint: `domains/reflective_faculty.py` only,
67 insertions / 5 deletions, entirely inside `_shared_shape` and the new
`_relation_cue_index` helper. `author_signature` itself (`:7112-7134`) does not appear
in the diff.

---

## 7. What this does NOT establish

1. **It does not resolve the `RelationCue` placeholder-token-collision design question**
   named out of scope by the charter (the 52 cues reusing tokens like `"to"`/`"NEW"`/
   `"PART"` across unrelated relations) — that question is about the VOCABULARY's own
   data, not about how signatures are compared, and is untouched here. The 3 near-miss
   seed rows in §5 are a symptom of the same family, named and accepted, not fixed.
2. **`author_signature`'s ~10 other callers were not exercised end-to-end by this
   rung's regression run** beyond the one already-pinned `learn_term_for_concern`
   scenario (P3) — they are safe by CONSTRUCTION (the function they call is
   byte-unchanged), not because this rung ran their own test suites. A future rung
   that DOES want `induce_concern`'s SD-loop or `grow_part_library`'s installed parts
   to benefit from axis-anchoring would need its own, separately-scoped design (see
   §1's note on why a full-vocabulary vector there would need the same ABSENT-
   projection discipline `analogical_thinking._pair_witness` already carries).
3. **No benchmark claim.** Per `CLAUDE.md`'s standing rule, this is a mechanism-level
   fix; no task-score number is reported or implied.
4. **The `kind`-field question remains NO-GO'd**, per `SHAPE_KIND_FIELD_RESULTS.md` —
   this rung's fix is orthogonal to it, exactly as that document's own §2.2 concluded
   before this fix existed.

---

## 8. Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/author-signature-axis-anchor
git log --oneline -1 main   # 6805175, verified before branching

# The live before/after demonstration (P1, P2, P3)
PYTHONPATH=".:runners/dsl/python" python3 scripts/author_signature_axis_anchor_probe.py

# Regression
python3 -m pytest tests/test_cost_scheduling.py tests/test_nl_concern_front_door.py \
                   tests/test_compilation_cycle.py tests/test_author_signature_axis_anchor.py -q
# 39 passed
```
