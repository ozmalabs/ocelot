# The first NL-to-structure adapter for the six unwired `solve_*` resolvers — RESULTS

Base `main @ d92c7d2` ("Merge progsyn-delimjoin-budgetwall: delim-join +
budget-wall sizing, both NO-GO"), verified via `git log --oneline -1 main`
immediately before creating this worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/solver-nl-adapter`, branch
`solver-nl-adapter`, commits `6d36b2b` (PREREG) + `020f105` (implementation +
tests). `data/` was absent in the fresh worktree (not a partial real
directory); symlinked (`ln -sfn /home/matt/ozmadev/ocelot/data data`) and
confirmed `data/wiktionary/en.jsonl.gz` resolves to the real
492,560,156-byte file.

This document reports what was investigated and built against the
already-registered `SOLVER_NL_ADAPTER_PREREG.md` — see that document for the
full per-resolver reading and the argument behind the ranking; this document
reports what was actually RUN, live, against the real toolbox.

**Headline finding:** of the six previously-unwired `solve_*` resolvers,
`solve_reasoning_bridge`'s `deduction_to_can` direction was the ONLY one
whose prerequisite is not a graph NODE the caller must have separately
built (a CAN Microtheory, a `DirectionalCorrespondence`, a candidate list)
but two PLAIN STRINGS — and both extraction steps needed to produce those
strings from real text were pure reuse of already-shipped reader calls, with
zero new parsing capability required. Built exactly one adapter,
`mint_solve_reasoning_bridge_goal_from_text`, live-demonstrated on a real
Bigville resident's real CAN belief network with genuine natural-language
sentences (not synthetic placeholders), correctness verified by hand against
the network's own `external_field` state, not merely `status == "resolved"`.
The other five resolvers remain unwired, named follow-ons — the ranking
below is a complete map of why each is more expensive, not a claim any of
them was attempted.

---

## 1. Per-resolver cost ranking, with the evidence behind each row

Read directly off `domains/solver_dispatch.py` (all seven resolvers) before
ranking anything — see `SOLVER_NL_ADAPTER_PREREG.md` §1 for the full table
of exactly which graph object each of the six reads off its Goal node, with
file:line citations. Restated here with the evidence for WHY each rank is
where it is (not merely repeating the table):

| rank | resolver (direction) | prerequisite | reuse found? | verdict |
|---|---|---|---|---|
| 1 | `solve_reasoning_bridge` (`deduction_to_can`) | two bare strings, `entity`+`attr`, read straight off Goal attrs, no edge | **YES — total.** `situation_model_reader._entity` (get-or-create by name, already called by `coref_entities.py`/`inference_generation.py`/`character_tom.py`/`global_monitoring.py`/`reading_drive.py` — confirmed by grep), `propositional_deduction._norm_attr` (already `solve_deduction`'s own normaliser), `situation_model_reader._is_property_pred` (already reused by 4+ other modules) | **CHEAPEST. Built.** |
| 2 | `solve_analogical_promote` | `targets_correspondence` edge → an already-recorded `DirectionalCorrespondence` node | **PARTIAL.** `analogical_thinking.record_directional_correspondence` is fully mechanical and reusable once given two real `Concept` nodes — but no analogy-shaped sentence parser ("X is like Y"/"X corresponds to Y") exists anywhere in the tree (checked: no such construction in `seeds/reading_constructions.json`) | Moderate — real, unbuilt parsing work on the recognition half |
| 3 | `solve_decompose` | `solve_caps`-staged candidate list from `problem_decomposition.py`'s `project_*` functions | **NO independent reuse** — every `project_*` builder itself requires an already-built CAN Microtheory or already-minted deduction/situation-model nodes (`domains/problem_decomposition.py:99-186`) | Expensive, and strictly downstream of rank 4-6's own cost |
| 4-6 | `solve_can_relax` / `solve_can_exact` / `solve_can_bp` | `targets_mt` edge → a full CAN Microtheory (`Concept` nodes + weighted `causal_influence` edges) | **NO reuse found.** The only builder, `worlds/bigville_can_beliefs.build_resident_can_mt`, is a mechanical translation of an ALREADY-DRAWN numeric `params` dict — there is no path from raw text to a `params` dict anywhere, let alone to a weighted causal edge | Most expensive, tied — a genuinely new capability (causal-relation-with-weight extraction from prose), not a connector |

`solve_reasoning_bridge`'s `can_to_deduction` direction (the reverse
direction of the same resolver) needs a `targets_mt` edge — it inherits
rank 4-6's cost, unlike its own `deduction_to_can` direction. This is why
the ranking is by DIRECTION for this one resolver, not by resolver name
alone — confirmed by reading `solver_dispatch.py:446-489` directly (the two
branches read entirely different Goal attrs).

## 2. Was the ranking guessed, or checked? — the discriminating live test

`SOLVER_NL_ADAPTER_PREREG.md` §3 registered a live check BEFORE finalising
the ranking, per the task's own instruction not to guess from the shape of
the problem alone. Run against a real `WorldAdapter` boot
(`load_all_seeds`) and a real Bigville resident (`seeds/bigville_cast100.json`
resident 0, "Verity Peaseblossom"), via `worlds.bigville_can_beliefs.
build_resident_can_mt` — the SAME hand-built-network pattern
`tests/test_solver_dispatch_migrated.py::_resident_mt` already uses for
`solve_can_exact`'s own P13b demonstration in `SOLVER_MATH_BOUNDARY_
RESULTS.md`:

```
>>> rc.read_clause(a, "Verity Peaseblossom is world safe.", write=False, learn=False)
{'predications': [['is_a', 'verity_peaseblossom', 'world_safe']], 'speech_act': 'statement', ...}
```

The reading pipeline's OWN multi-word-noun-phrase joining already collapses
the two-word predicate complement "world safe" into one underscore-joined
token, `world_safe` — byte-identical to a real Bigville resident's own CAN
topic name (`worlds/bigville_can_beliefs.TOPIC_NAMES`), with
`propositional_deduction._norm_attr` a no-op pass-through on it. This one
live check is what separated rank 1 from rank 2 (`solve_analogical_promote`)
with confidence — the extraction genuinely needed zero new code, confirmed
by running it, not assumed because the resolver's *signature* looked
simpler on paper.

## 3. What was built

`domains/solver_dispatch.py:234-296` (immediately before
`mint_solve_analogical_promote_goal`, alongside the existing
`mint_solve_reasoning_bridge_goal` it composes with):

```python
def mint_solve_reasoning_bridge_goal_from_text(adapter, statement: str, *,
                                               alpha: float = 1.0):
    ...
    from domains import reading_collapse as rc
    from domains import propositional_deduction as pd
    from domains import situation_model_reader as smr
    if not statement or not str(statement).strip():
        return None
    whole = rc.read_clause(adapter, statement, write=False, learn=False)
    if whole.get("speech_act") == "question":
        return None
    preds = whole.get("predications") or []
    if not preds or len(preds[0]) < 3:
        return None
    rel, subj, obj = preds[0][0], preds[0][1], preds[0][2]
    if not smr._is_property_pred(str(rel)):
        return None
    entity = str(subj).strip()
    attr = pd._norm_attr(obj)
    if not entity or entity == "_" or not attr:
        return None
    return mint_solve_reasoning_bridge_goal(
        adapter, "deduction_to_can", entity=entity, attr=attr,
        positive=True, alpha=alpha)
```

Three reused primitives, zero new ones:

1. `reading_collapse.read_clause` — the SAME call
   `propositional_deduction.parse_conditional`'s `bare_universal` branch
   already makes on a raw statement string (`domains/propositional_
   deduction.py:240`), unmodified.
2. `propositional_deduction._norm_attr` — the SAME normaliser
   `solve_deduction`'s own `_relation_and_attr` already uses
   (`domains/propositional_deduction.py:151-158,178,180`), unmodified.
3. `situation_model_reader._is_property_pred` — the SAME property-
   predication gate already imported by `coref_entities.py:835,1738`,
   `inference_generation.py:351`, and `salient_cache.py:243` (confirmed by
   grep before reuse, not assumed available), unmodified.

**Speech-act gate, deliberately mirrored from the Bug 1 fix.** `whole.get(
"speech_act") == "question"` → decline. This is the identical defect class
`SOLVER_MATH_BOUNDARY_BUGFIX_RESULTS.md` §1 fixed inside `parse_conditional`
— a question's own honest fallback grounding can surface an `is_a`-shaped
predication (confirmed live, §4 below: `"Is Verity Peaseblossom
trustworthy?"` still grounds an empty predication list here specifically,
but the SAME risk class as the arithmetic-question bug this rung must not
reintroduce in a new adapter — gated defensively rather than assumed safe).

`solve_reasoning_bridge`'s own internals (`domains/solver_dispatch.py:446-
489`) are byte-unchanged — confirmed by `git diff` (§6): the new function is
inserted between two existing functions, nothing inside either is touched.

## 4. Live demonstration

### 4.1 Success — real sentence, real resident, real CAN network, verified by hand

```
resident: "Verity Peaseblossom" (seeds/bigville_cast100.json, index 0)
sentence: "Verity Peaseblossom is world safe."

goal = mint_solve_reasoning_bridge_goal_from_text(agent, sentence)
goal.attrs: {kind: "solve_reasoning_bridge", direction: "deduction_to_can",
             entity: "verity_peaseblossom", attr: "world_safe", status: "pending"}

after dispatch through the UNCHANGED qd_bind_resolver -> solve_reasoning_bridge:
  status: "resolved"
  answer: {applied: True, entity: "verity_peaseblossom", attr: "world_safe"}
  resolve_with -> Resolver{name: "solve_reasoning_bridge"}   # the JOIN's own effect
```

**Correctness verified by hand, not just "resolved without erroring"**
(mirroring `SOLVER_MATH_BOUNDARY_RESULTS.md`'s own discipline of checking
actual correctness): the `world_safe` Concept's `external_field` attr —
the exact attr `can_ops.rs::apply_evidence_h` documents itself as writing
(`h_i ← h_i + α · evidence`) — moved from `0.0` to `1.0`, EXACTLY
`alpha(1.0) * evidence(+1.0)`, confirmed by direct before/after read, not
inferred from `status`. (An earlier check against `identity_field` — a
DIFFERENT attr, written only by `nudge_identity`, a separate CAN primitive
never called by this path — showed no movement; tracing this to the Rust
source, `can_ops.rs:863-869`, before trusting either reading is itself part
of this rung's own verification discipline, not an aside.) A second
resident/topic pair (`self_worth` on resident 1) additionally confirmed the
evidence write is TARGETED: applying evidence to `claim_credible` left a
sibling `self_worth` Concept's `external_field` completely unchanged
(`0.0 == 0.0`), ruling out an accidental network-wide nudge.

### 4.2 Honest wall — real sentence, resolver-side miss

```
sentence: "Verity Peaseblossom is honest."   (resident 2's real network)
goal.attrs: {entity: "verity_peaseblossom", attr: "honest"}
after dispatch: status: "walled"
  gap_key: "solve_reasoning_bridge:deduction_to_can:verity_peaseblossom:honest"
  note: "Microtheory 'Verity Peaseblossom_beliefs' holds no Concept named 'honest'"
```

The UNMODIFIED `apply_derived_fact_as_can_evidence`'s own honest-miss path
(§ module docstring, `domains/reasoning_can_bridge.py:223-227`) fires
exactly as it already does for a hand-built caller — the adapter's only
contribution here is correctly extracting `(entity, attr)` from real text
and letting the existing resolver decide; Rung 2's `note_solve_exhausted_
gap` gap-filing (unchanged) fired correctly on this wall, confirmed by the
`gap_key` attr being present and content-specific.

### 4.3 Honest decline — the adapter's own gate, unsuitable real input

```
"Is Verity Peaseblossom trustworthy?"    -> None   (speech_act == "question")
"Verity Peaseblossom likes apples."      -> None   (rel="likes", not a property predication)
""  /  "   "  /  None                    -> None   (empty/degenerate statement)
```

Confirmed additionally that a decline mints **zero** Goal nodes at all
(`test_decline_mints_no_goal_node_at_all` — `len(agent.s.nodes("Goal"))`
identical before/after two declined calls), not merely that the return
value is `None` while some half-formed node was left behind — the same
"never mint garbage from unsuitable input" discipline
`SOLVER_MATH_BOUNDARY_BUGFIX_RESULTS.md`'s Bug 1 fix established.

## 5. The old direct-mint path is unaffected

`mint_solve_reasoning_bridge_goal(adapter, "deduction_to_can", entity=...,
attr=..., positive=True)` — the ORIGINAL, hand-supplied-attrs entry point —
still dispatches byte-identically (`test_old_direct_mint_path_unaffected`,
resident 3's real network, topic `trust_mayor`): `status == "resolved"`,
`answer["applied"] is True`. The new function is a pure ADDITION alongside
it, never a replacement.

## 6. Regression

```
$ python3 -m pytest tests/test_solver_dispatch_migrated.py \
    tests/test_solve_gap_awareness_migrated.py \
    tests/test_problem_shape_migrated.py \
    tests/test_solver_math_boundary.py \
    tests/test_solver_nl_adapter.py -q
....................................................                     [100%]
52 passed in 56.58s
```

Extra sweep, adjacent facilities this rung's new function imports from
(`propositional_deduction`, `situation_model_reader`, `reading_collapse`),
run fresh for extra confidence beyond the task's own named list:

```
$ python3 -m pytest tests/test_deduction_extension.py \
    tests/test_deduction_generalization.py tests/test_quantified_deduction.py \
    tests/test_reasoning_facility_bridge.py tests/test_situation_model_wire.py -q
........................................................................ [ 97%]
..                                                                       [100%]
74 passed in 5.60s
```

**126/126 green across all seven suites, zero regressions, zero waivers
needed.**

```
$ git diff --stat d92c7d2 HEAD
 .../engine_substrate/SOLVER_NL_ADAPTER_PREREG.md   | 263 +++++++++++++++++++
 domains/solver_dispatch.py                         |  75 +++++-
 tests/test_solver_nl_adapter.py                    | 190 +++++++++++++++
 3 files changed, 527 insertions(+), 1 deletion(-)
```

Purely additive — `domains/solver_dispatch.py`'s `-1` is the single-line
edit inserting the new function's `__all__` entry beside the existing
`mint_solve_reasoning_bridge_goal` entry; every existing function's body is
byte-unchanged, confirmed by the diff itself, not merely asserted. No Rust
touched; no `cargo build` needed. No seed file was modified — the new Goal
still dispatches through the UNCHANGED `qd_bind_resolver` JOIN and the
already-installed `solve_reasoning_bridge` Resolver
(`seeds/solver_dispatch.json`, untouched).

## 7. GO / NO-GO

**GO.** `solve_reasoning_bridge`'s `deduction_to_can` direction is now
reachable from real natural-language text, via
`mint_solve_reasoning_bridge_goal_from_text` — demonstrated live on a real
Bigville resident's real CAN belief network, both the success path
(correctness verified by hand against the network's own `external_field`
state) and both honest-refusal paths (resolver-side wall with correct
gap-filing; adapter-side decline minting zero nodes on unsuitable input).
126/126 regression tests green, fresh, across the task-named suites plus an
additional adjacent-facility sweep. The diff is purely additive; nothing in
`solve_reasoning_bridge`'s own internals, `qd_bind_resolver`, or any seed
file was touched.

**Not merged, not pushed to `main`.** `main`'s tip was checked fresh
(`d92c7d2`) immediately before creating this worktree, and every commit
(`6d36b2b`, `020f105`) lives on the `solver-nl-adapter` branch only. This
rung did not run any command that touched `main` at any point. The
orchestrator performs the merge.

---

## 8. What this document does NOT establish

1. **The other five resolvers (and `solve_reasoning_bridge`'s own
   `can_to_deduction` direction) still have no NL adapter.** §1's ranking
   names why each is more expensive; none of that cost was paid down here.
   `solve_analogical_promote` (rank 2) is the most plausible next
   candidate — its correspondence-recording half is already mechanical —
   but it needs a genuinely new analogy-shaped sentence parser that does
   not exist anywhere in the tree today, and building that parser was
   explicitly out of scope for "build exactly one, the cheapest."
2. **No NL-to-CAN-network path exists, for any of the three CAN
   resolvers.** The adapter built here reaches an EXISTING CAN network's
   EXISTING Concept via evidence — it does not, and was never intended to,
   build a network from scratch. `worlds/bigville_can_beliefs.build_
   resident_can_mt`'s only input remains an already-drawn numeric `params`
   dict; extracting causal relations WITH WEIGHTS from prose is a
   substantial new capability, not sized or attempted here.
3. **Negation is not handled.** The adapter always mints `positive=True` —
   a real declarative negative fact ("Verity Peaseblossom is not
   trustworthy") would either fail the property-predication gate or (if it
   did ground) be misread as a POSITIVE fact. Checked before building
   (`reading_collapse.py` carries no NEG/negator markup reaching a grounded
   predication's polarity), named as an honest, separate follow-on, not
   attempted here — this is a real limitation of what was shipped, not a
   silent gap.
4. **Only ONE grounding shape is supported: a single declarative copular/
   property clause about ONE named entity.** A compound sentence, a
   multi-fact statement, or an indirect/reported belief ("The mayor thinks
   Verity is trustworthy") is out of scope — the adapter reads only
   `read_clause`'s FIRST predication, mirroring `parse_conditional`'s own
   single-predication scope, not a design decision unique to this rung.
5. **The entity/attr STRING match is exact, not semantic.** "Verity trusts
   the mayor" does NOT resolve to the `trust_mayor` Concept (it grounds to
   `rel="trusts"`, not a property predication at all, so the adapter
   correctly declines) — only a sentence whose predicate NORMALISES
   byte-identically to an existing Concept's name succeeds. This is an
   honest, exact-match boundary, not a semantic mapping from arbitrary
   phrasing to canonical CAN topic names; found live during
   investigation (§2), not glossed over.
6. **The correspondence rules' own named residual is unchanged.**
   `reasoning_can_bridge._run_correspondence`'s own docstring names a
   cross-seed rule-starvation risk on a FULL 600+-seed boot that this
   rung's tests (a `load_all_seeds` boot, but with few concurrently-pending
   Correspondence writes) did not stress — unrelated to this rung's own
   diff, not investigated further here.
