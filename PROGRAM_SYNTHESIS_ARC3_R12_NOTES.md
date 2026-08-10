# PROGRAM SYNTHESIS ARC 3 R1+R2 — THE EXEMPLAR STORE, RANKED RETRIEVAL,
THE ADAPTATION LADDER, AND A REVERTED SCREEN (notes)

**Date:** 2026-08-01. Companion to `PROGRAM_SYNTHESIS_ARC3_PLAN.md` (R1/R2),
`PROGRAM_SYNTHESIS_ARC3_PREREG.md` / `PROGRAM_SYNTHESIS_ARC3_R0_NOTES.md`
(the 12-task honest oracle ceiling this phase's mechanism is measured
against), `PROGRAM_SYNTHESIS_ARC2_Q4_NOTES.md` (the `exclude`-powered
enumerate contract and the descent/repair guard-widening discipline this
phase inherits), `PROGRAM_SYNTHESIS_P7B.md` (the localize/re-open-one-hole
principle rung (d) adapts). Deliverables: `seeds/program_synthesis.json`
v1.4.0 → v1.5.0 (49 → 54 rules), `domains/prog_synthesis.py` (small,
additive: one import, one `ensure_exemplar_store` call, two new dispatch
entries, a `retrieval` sub-dict on `read_goal`), NEW `domains/prog_
retrieval.py` (the mechanical retrieval/ladder adapter, ~640 lines), NEW
`seeds/mbpp_exemplars.json` (90 whole train-program Exemplar nodes, built
by NEW `scripts/build_exemplar_store.py`), `tests/test_program_synthesis_
migrated.py` (rule-count pin only, 49 → 54), NEW `tests/test_retrieval_
migrated.py` (31 gates).

---

## 1. What landed, and what did not

**Landed, real, measured:**

- **R1 — the exemplar store.** 90/120 = 75.0% train-emittable programs
  (byte-identical to R0/Q3's own pool), kept WHOLE, as graph-resident
  `Exemplar` nodes (`task_id`, `ir_json`, `params`/`arity`, `prompt_tokens`
  + a per-exemplar TF-IDF weight dict computed over the pool's own train
  prompts, `arg_types`/`return_type` from `mbpp_spec.signature_facts` on
  the train task's own rows — never prose, never a test-split field).
  IR reflected into a subgraph at install (`ir_subgraph` edge, the
  `read_off_accepted` precedent).
- **R1 — ranked retrieval, SELECTION as a rule.** `score_exemplars`
  (adapter, mechanical arithmetic: TF-IDF token-overlap + arity-match +
  type-match bonuses — a fixed formula, the `_row_cmp_ok`/`_trans_logp`
  class) boards one `ScoreLink{score, task_id, picked}` proxy per
  Exemplar; `pr_select_candidate` (seed rule) picks the current best
  UNPICKED ScoreLink via a strict total order (score desc, task_id asc
  tie-break — exactly one winner per fixpoint round, no Argmax-over-
  edge-attribute needed since the engine's `add_edge` effect requires a
  match-bound var, never a Term-computed target — confirmed against
  `graph_rules.rs`), bounded by `pr_topk` (5, the prereg's own "if it
  names one else 5, documented" instruction — the prereg does not name
  one).
- **R2 — the adaptation ladder.** ONE verb (`run_retrieval_ladder`,
  dispatched on a NEW `retrieve_ladder` status) runs rungs (a)-(d) in
  Occam order over the rule-selected top-k candidates, reusing the SAME
  bounded catalogs `scripts/retrieval_oracle_ceiling.py`'s R0 measurement
  used (`BOUNDS`: permutation arity <= 4, leaf-delta numeric offsets/
  absolutes, `{Plus,Minus,Times,Div,Mod}`/`{Eq,Lt,Lte,Gt,Gte}` op
  families): (a) as-is, (b) bounded arg-permutation, (c) single-leaf edit
  at the best near-miss, (d) retrieved-as-skeleton (mask the anchor's own
  final compute statement — R0's rung-(d) masking rule — derive the
  hole's row from each revealed row's own expected output over the
  prefix's live vars, call `SynthEnumerate` on it). **Every rung screens
  the FULL candidate program against the goal's own revealed rows before
  it may be recorded as a pass** — this IS the universal execution screen
  at retrieval grain, and it costs NO `ps_attempts`: `pr_ladder_accept`
  (seed rule) is what bumps `ps_attempts` (by exactly one) and hands the
  screened-and-passing IR to the UNCHANGED `eval_pending` → `evaluated` →
  `ps_row_pass`/`fail` → `ps_verified` → `ps_accept` chain, so a
  retrieval accept is verified by the EXACT SAME execution machinery a
  codebook/enumerate accept is.
- **A real, load-bearing bug found and fixed en route (param renaming).**
  A retrieved exemplar's own parameter names (e.g. `arr`) are NOT the
  goal's canonical request-arg names (e.g. `a`, `b`, ... — `mbpp_spec.
  _row_from_call`'s convention). The FIRST version of this ladder handed
  the exemplar's own-named IR straight to `pr_accept_ir_json`, which
  `eval_and_record` then failed to bind (`trap: 'param:arr'`) since the
  goal's `ExampleRow.inputs_json` is keyed by the CANONICAL names — every
  retrieval accept silently gapped downstream. Fixed by `_to_goal_ir`
  (a mechanical alpha-rename walk, `_rename_vars`, scoped to
  `Var`/`ProgDefFnParam`/`ProgAssignVar` nodes only — never
  `ProgCallExtern`'s own function-name field) applied at every accept
  point, folding the rung-(b) permutation directly into the rename so the
  accepted IR needs no runtime remapping at all.
- **A scope guard (`_is_mbpp_shaped`) — necessary for non-regression, not
  originally planned.** See §2.

**Attempted, measured, and REVERTED — the codebook-side universal screen
(the HR2 mechanism's other half):**

The plan called for ONE screening lane covering BOTH retrieved and
codebook/chunk candidates. A full implementation landed
(`pr_screen_mark`/`pr_screen_admit`/`pr_screen_reject`/
`pr_screen_exhausted`/`pr_screen_none_eligible`, a dry-run
`build_candidate_ir_for_construction` mirroring `splice_binding`'s exact
template→IR logic) and correctly fixed its OWN unit case: a construction
that does not fit the revealed rows at all is excluded and never spends
`ps_attempts`. But live-testing against the REQUIRED regression sweep
surfaced a real, structural incompatibility: **`ps_descend_mark`/
`build_descent` decode PARTIAL COVER directly off the whole codebook via
`ShapeDecode`, entirely independent of `ps_propose`'s Argmax/exclusion
set.** A construction that does not pass every revealed row ALONE (e.g.
`count_of_list` on `la_10_count_positives` — it is a genuine PARTIAL
cover, correct as a descent starting point once one hole is filled in) is
a screen FALSE NEGATIVE under a naive whole-program pass/fail check. The
screen excluded it; `ps_propose` then had no eligible construction left
and never fired (`ps_rung_codebook`/`ps_attempts` stayed at their minted
zeros); descent, which never reads `ps_excluded`, still found and used the
SAME construction via its own independent path — a genuine, measured
regression: `tests/test_prog_repair_migrated.py::
test_headline_la10_converts_to_holdout_ok_via_repair` (a file this phase
does not own and is not permitted to patch) flipped from `attempts==1.0,
rungs.codebook==1.0` to `attempts==0.0, rungs.codebook==None`.

Given (a) `descent`/`repair`/`descent_widening` are named in this phase's
own required sweep with NO pin-drift allowance (unlike `endgame`, which
IS caveated for exactly this reason), and (b) the affected test files are
outside this phase's file ownership (no way to update an assertion even if
the drift were in "the improvement direction" — and here it measurably was
NOT: a previously-accepted, holdout-correct task's PROVENANCE became
unrecoverable, not merely relabelled), the codebook-side screen was
**REVERTED IN FULL**: `pr_screen_*` rules removed from the seed (54 rules
stands at that count WITHOUT them — the retrieval lane's own 5 new rules
are what raised 49→54), `ps_lattice_failed`/`ps_reproposal`'s hand-off
retargeted back to `pending` (their pre-Arc3 value), the `screen_running`
dispatch entry and `screen_construction`/`build_candidate_ir_for_
construction` removed from `domains/prog_retrieval.py`. This is reported
as a genuine, real, honest residual — not smoothed over — per §5 and per
this project's own standing culture ("a status line was reusable as an
excuse" / "report a defect, don't hide it").

**Net HR2 reading:** the decoy-tax mechanism is CONFIRMED at retrieval
grain (§4) — the exact class of fix the plan asked for — but NOT extended
to the codebook/chunk rung in this delivery. The codebook rung's own
decoy-tax exposure (Q5's 24 `gapped:exhausted` rows) is UNCHANGED by this
phase; closing it needs a screen that can DISTINGUISH "wrong candidate"
from "correct partial cover awaiting a hole", which requires threading
descent's OWN partial-cover applicability check into the screen (the
`DESCEND_APPLICABLE` predicate Arc2-Q4 §6 already found duplicated once,
named there as a standing trap) — out of this phase's time budget, named
here as the concrete next step.

## 2. The scope guard, and why it had to exist

`score_exemplars` only scores exemplars for a request whose text is
recognisably MBPP-prompt-shaped (`_is_mbpp_shaped`, a STRICTER, word-
boundary-aware re-check of `mbpp_spec`'s own closed verb-frame vocabulary
— reused, not redefined). Without it, the retrieval ladder — which is
otherwise a genuinely powerful, `SynthEnumerate`-backed search at rung (d)
— non-deterministically "stole" acceptances from dozens of hand-written
descent/repair/battery fixtures whose phrasing happens to share real
MBPP-style vocabulary (e.g. `"double the sum of the first n natural
numbers"`), producing a DIFFERENT (usually less informative, sometimes
outright wrong-but-revealed-row-fitting) accept than the construction
those tests are specifically pinned to. `mbpp_spec.request_facts`'s own
`str.startswith` frame match ALSO has a real, pre-existing, harmless-until-
now false-positive (`"write a function top_pick..."` starts with
`"write a function to"` character-for-character, purely because
`"top_pick"` happens to start with `"to"`) — `_is_mbpp_shaped` closes that
specific gap by requiring the character after a matched frame to be a
non-alphanumeric boundary. This guard is why `descent`/`repair`/
`descent_widening`/`program_synthesis`(-other-than-the-rule-count-pin)/
`battery`/`chunks`/`baseline`/`spec`/`diet` all reproduce BYTE-IDENTICAL
behaviour (§6) — retrieval is a harmless, 2-round no-op fall-through for
every one of their fixtures, verified live, never assumed.

## 3. Ranked retrieval — design notes

- **Scoring is arithmetic; selection is a rule.** `score_exemplars` never
  sets `status`, never mints a `pr_candidate` edge, never picks a winner
  — it records one `score` fact per Exemplar. `pr_select_candidate`
  (seed) is the ONLY thing that ever mints a `pr_candidate` edge, via a
  strict total order over the recorded scores (ties broken by ascending
  `task_id`, deterministic).
- **Why a proxy node (`ScoreLink`), not an edge attribute.** The DSL's
  `add_edge` effect requires a MATCH-bound or freshly-`add_node`'d
  variable for both endpoints (`graph_rules.rs::parse_effect_op`, `intern_
  str` requires a literal `Value::Str` variable name, never a `{"__term__"
  :...}` computed value) — an Argmax over `Edges`/`EdgeAttr` tuples cannot
  be used as an `add_edge` target directly. Minting one `ScoreLink` per
  (goal, exemplar) pair, matched via `match: [[g, pr_score, sl], [sl,
  pr_score_exemplar, ex]]`, gives `ex` as a real bound node var for the
  effect.
- **`pr_topk` = 5**, a minted integer constant on the goal (the
  `ps_max_depth`/`ps_repair_budget` precedent) — the prereg does not name
  a k, so this is documented here as the phase's own choice.

## 4. The ladder — design notes and the decoy-tax proof

- **Every rung screens on revealed rows before recording a pass** — the
  universal execution screen, retrieval half. `test_ladder_accept_spends_
  exactly_one_attempt` (task 138: 5 candidates considered across rungs
  a-d, only the rung-(d) FINAL accept touches `ps_attempts`, and by
  exactly one) is the decoy-tax proof at THIS lane: an arbitrary number of
  failing candidates across 4 rungs cost nothing; only a genuine,
  screened, execution-verified pass ever spends a real attempt.
- **Occam order is enforced by early return**, not by a priority score:
  `run_retrieval_ladder` returns the instant rung (a) finds an exact-pass
  candidate, never even constructing rung (b)'s permutation search
  (`test_occam_order_exact_pass_never_falls_through_to_deeper_rungs`,
  task 105).
- **Rung (d) is ADAPTED from P7-B's principle, not a byte-for-byte reuse**
  of the Hole/`spawn_subgoal` machinery — named honestly, not glossed:
  P7-B's localization is keyed to a codebook `ShapeDecode` cover
  (`ps_cover_parts`, template names looked up via `_template_by_name`);
  a retrieved exemplar's structure is not such a decode. Rung (d)
  therefore re-implements the SAME two ideas (mask the final compute
  statement — R0's own rung-(d) proxy; derive the hole's row from the
  outer row's own expected output; solve via `SynthEnumerate`) as a
  self-contained computation inside `run_retrieval_ladder`, never
  touching the `Hole`/`ps_plan_seq`/`spawn_subgoal` apparatus at all.
  This is a genuine, working mechanism (2/12 ceiling captures both close
  via rung (d) — see §5), just not the literal call graph the plan's
  wording ("verbatim") suggested; the gap is real and is named as a
  residual (§7).
- **`build_candidate_ir_for_construction`/`splice_binding` duplication**
  (§1's REVERTED screen) never shipped, so this particular duplication
  residual is now moot — noted for completeness only.

## 5. Ceiling capture — the headline table

End-to-end (PRIMARY protocol, `psy.synthesize_from_request`, live,
gated by `tests/test_retrieval_migrated.py`'s parametrized re-verify) on
all 12 R0 ceiling task ids:

| task | R0 oracle rung/exemplar | mechanism status | mechanism rung/exemplar | holdout | captured |
|---|---|---|---|---|---|
| 105 | a / 798 | accepted | c / 802 | **fail** | no (trap) |
| 106 | b / 750 | gapped:enumerate_failed | none | — | no |
| 115 | a / 741 | **exception** (pre-existing) | — | — | no |
| 138 | c / 762 | **accepted** | d / 803 | **True** | **YES** |
| 238 | a / 734 | accepted | d / 802 | fail | no (trap) |
| 242 | a / 620 or 792 | accepted | d / 776 | fail | no (trap) |
| 284 | a / 808 | accepted (arc-2 fallthrough) | none | fail | no |
| 394 | c / 741 | gapped:enumerate_failed | none | — | no |
| 405 | a / 808 | accepted | d / 637 | fail | no (trap) |
| 406 | c / 762 | **accepted** | d / 775 | **True** | **YES** |
| 412 | a / 629 | gapped:enumerate_failed | none | — | no |
| 414 | a / 637 | accepted (arc-2 fallthrough) | none | fail | no |

**Captured: 2/12 (105→no, 138→YES, 406→YES).** Below HR1's "weak/marginal"
band (1-5 net passes) at its low end, on this measurement — reported
exactly as measured, no smoothing. Every miss has a concrete, checked
reason, none of them "the mechanism doesn't run":

1. **The R0 oracle exemplar for a coincidental (not semantic) match is
   invisible to token-overlap scoring** (105: `798` is "sum of an array"
   — `sum([True,False,True]) == 2` because Python bools ARE ints;
   `count true booleans` and `sum of an array` share ZERO content
   tokens). 238/405/414's oracle matches are the SAME shape — a shared
   closed-form/combinatorial coincidence (count of non-empty substrings
   of length-n string == sum-of-products-of-sublists' own formula
   family), not a content match a prompt-token ranker can ever surface.
   This is exactly the registered null-reading's own prediction
   (`PROGRAM_SYNTHESIS_ARC3_PREREG.md` §5): "a real R1 ranker ... will
   realistically capture some FRACTION of this 12-task ceiling, not all
   of it."
2. **106/394/412 gap** because NO exemplar (real or coincidental) in the
   top-5 ranked pool reaches ANY rung, and the arc-2 fallthrough (codebook
   + enumerate) also can't build them — unchanged, pre-existing behaviour
   for these tasks either way.
3. **115 is a pre-existing, unrelated defect** — `mbpp_spec.py`'s own
   documented residual (a `set`-valued row is not JSON-serializable via
   `ingest_spec`'s `_add_example_row` until Q1 lands native DSL Set
   support). This crashes BEFORE retrieval ever runs; not a retrieval
   defect, named in that module's own docstring since Q2.
4. **238/242/405 are TRAPS, not misses of the mechanism** — the ladder
   correctly found and screened a candidate that fits EVERY revealed row
   (a genuine accept, verified the same way a codebook accept is), and
   the never-revealed held-out row then disagrees. This is EXACTLY the
   trap-mass phenomenon R0 measured and predicted (55.6%-60.0% of rung
   a-c revealed-passers fail held-out) — reproduced here at the REAL
   mechanism grain, not just the oracle sweep's. The screen (revealed-
   rows-only, by the CEGIS oracle protocol's own design — the loop must
   never peek at unrevealed rows) cannot and must not be expected to
   catch these; only a live verifier's later counterexample feed (P7-B's
   repair lane, already standing, unmodified) can.
5. **284/414 accept via the UNCHANGED arc-2 fallthrough** (retrieval found
   nothing at all — `rung: none` — for these two; the codebook/enumerate
   path, exactly as before Arc3, produced the accept) — these two rows
   are UNCHANGED by this phase in every respect other than having passed
   through a harmless retrieval no-op first.

**The two genuine captures (138, 406) are real, full pipeline
verifications** — not oracle replays: both go through rung (d)
(retrieved-as-skeleton), with a DIFFERENT exemplar than R0's own oracle
anchor (803/775 vs R0's 762) — the mechanism found an independent,
equally-valid solution path R0's single-anchor sweep never measured,
consistent with R0's own honestly-stated residual ("the a-c ceiling
reported ... is itself a slight underestimate of what an exhaustive
multi-anchor search could find").

## 6. Non-regression — the full required sweep

| suite | count | status |
|---|---|---|
| `test_program_synthesis_migrated.py` | 58 | green (rule-count pin 49→54) |
| `test_prog_descent_migrated.py` | 17 | green, byte-identical |
| `test_prog_repair_migrated.py` | 13 | green, byte-identical |
| `test_descent_widening_migrated.py` | 11 | green, byte-identical |
| `test_prog_synthesis_battery_migrated.py` | 21 | green, frozen artifact untouched |
| `test_mbpp_endgame_migrated.py` | 30 | green (frozen artifacts untouched; live-reverify rows unaffected — retrieval's scope guard makes it a no-op for every row in this suite's own live checks) |
| `test_mbpp_diet_migrated.py` | 18 | green |
| `test_prog_chunks_migrated.py` | 11 | green |
| `test_mbpp_spec_migrated.py` | 67 | green |
| `test_code_synthesis_baseline_migrated.py` | 11 | green |
| `test_retrieval_ceiling_migrated.py` | 19 | green |
| `test_prog_synthesis_selfimprove_migrated.py` | 5 | green |
| `test_mbpp_contamination_migrated.py` | shared gate | green |
| `test_render_llvm/python/rust_lua_migrated.py` | 128 | green (transitive `prog_synthesis` import neighbours) |
| **`test_retrieval_migrated.py` (NEW, this phase)** | **31** | **green** |

**Total required + neighbouring sweep: 448 green**, ~16s (well under the
~150s budget). No parks, no stalls.

**One drift, reported not hidden, OUTSIDE this phase's required sweep**
(the ARC2-Q4 precedent for exactly this shape of finding):
`tests/test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_
live` — a Q0-A-owned file (not in this phase's file ownership, not named
in the required list; "baseline 11" in the required list is `test_code_
synthesis_baseline_migrated.py`, confirmed green, a DIFFERENT file) — one
of its three re-verified tasks now records `construction: 'retrieved_
exemplar'` where the frozen artifact recorded `None` for that task's own
recognition path. `status`/`outcome` are UNCHANGED (still whatever the
frozen row said); only the internal construction-provenance string
differs on a task that ALSO passes through the MBPP-shaped scope guard.
Not fixed (the file is outside this phase's ownership), reported here
per the standing "report a defect honestly, don't absorb it into a
net-positive framing" rule.

## 7. Honest residuals

1. **The codebook-side universal screen was reverted (§1)** — HR2 stands
   confirmed at retrieval grain only. The concrete next step (threading
   descent's own partial-cover applicability check into the screen,
   rather than a naive whole-program pass/fail) is named, not attempted.
2. **Rung (d) is adapted from, not identical to, P7-B's Hole/sub-goal
   machinery (§4)** — a self-contained mask-derive-enumerate computation
   inside the adapter, working and verified (2/12 real captures both go
   through it), but a genuinely different call graph than "verbatim."
3. **Ceiling capture is 2/12, below the weak/marginal band's low end on
   this specific measurement** — every miss has a checked, named reason
   (§5); none are silent mechanism failures. The dominant miss class
   (coincidental/combinatorial oracle matches invisible to content-based
   scoring) points at the SAME "corpus scale / ranking density" lever the
   prereg's own registered null-reading names, not a fourth proposal
   mechanism.
4. **No stemming/lemmatization in `_prompt_tokens`/`_goal_tokens`** — a
   plural/singular mismatch (`"tuple"` vs `"tuples"`) can zero out real
   token overlap between a genuinely related request and exemplar (task
   405 vs exemplar 808); a named, cheap future lever.
5. **Task 115's pre-existing `set`-row crash (§5.3)** is unrelated to this
   phase but blocks END-TO-END measurement of that one ceiling task
   entirely; named, not worked around (out of scope — `mbpp_spec.py` is
   not owned by this phase).
6. **`pr_topk` (5) is a minted constant**, not tuned against any corpus
   — same status as `ps_repair_budget`/`ps_max_depth` before it.
7. **The `test_mbpp_baseline_migrated.py` drift (§6)** is reported, not
   fixed (file ownership boundary).

## 8. Files

- `seeds/program_synthesis.json` — v1.4.0 → v1.5.0 (49 → 54 rules): `ps_
  goal` additively scoped to descent sub-goals (`ps_depth != 0`); NEW
  `ps_goal_top` (top-level goals mint at `retrieve_pending`); NEW `pr_
  select_candidate`, `pr_ladder_ready`, `pr_ladder_accept`, `pr_ladder_
  fallthrough`.
- `domains/prog_synthesis.py` — one import, one `ensure_exemplar_store`
  call inside `ensure_program_synthesis`, two new `_DISPATCH` entries
  (`retrieve_pending`, `retrieve_ladder`), a `retrieval` sub-dict on
  `read_goal`.
- NEW `domains/prog_retrieval.py` — the mechanical retrieval/ladder
  adapter (~640 lines): `ensure_exemplar_store`, `score_exemplars`,
  `run_retrieval_ladder`, `_is_mbpp_shaped`, `_to_goal_ir`/`_rename_vars`
  (the param-rename fix), the rung (a)-(d) generate-and-test helpers.
- NEW `scripts/build_exemplar_store.py` → NEW `seeds/mbpp_exemplars.json`
  (90 Exemplar nodes, twin-build deterministic).
- `tests/test_program_synthesis_migrated.py` — rule-count pin only
  (49 → 54).
- NEW `tests/test_retrieval_migrated.py` — 31 gates (store, contamination,
  scoring/selection, scope guard, screen/attempt accounting, Occam order,
  the 12-task ceiling-capture table live-reverified, the no-python-
  decision source audit, and the codebook-screen-reversion regression
  proof).
- `PROGRAM_SYNTHESIS_ARC3_R12_NOTES.md` — this document.

---

## 9. RUNG R2.5 (2026-08-01) — the codebook-side screen LANDS, scoped, redoing §1's revert correctly

§1 named the concrete next step honestly: "closing [the codebook rung's
decoy-tax exposure] needs a screen that can DISTINGUISH 'wrong candidate'
from 'correct partial cover awaiting a hole', which requires threading
descent's OWN partial-cover applicability check into the screen." This rung
does exactly that.

**The discriminator, reused verbatim (not invented).** A goal is
`SCREENABLE` iff it is NOT `DESCEND_APPLICABLE` — the SAME 3-part predicate
(`Exists` a trigger-matching codebook cover, `Or(has_list_input, Exists` a
trigger-matching scalar-fold/branch construction`)`, `depth < max_depth`)
`ps_descend_mark`/`ps_enumerate_mark` already carry as their own embedded
copy (Arc2-Q4 §6 named this exact duplication a standing trap; this rung
makes it a THIRD occurrence, extracted programmatically from the live seed
JSON rather than re-typed by hand, so all three copies are byte-identical
by construction) — AND it carries at least one revealed example row
(`ps_built_unverifiable` stays reachable, untouched) — AND `NOT_SLACK`: its
INITIAL trigger-matching codebook pool (`ps_screen_pool0`, a `Count` frozen
at goal-mint time) is not smaller than its FULL attempt budget
(`ps_screen_engage`, a boolean ALSO frozen at mint, `Gte(pool0, budget)`).

**Every partial-cover-eligible goal is therefore untouched BY
CONSTRUCTION, not by luck** — exactly the property §1's revert showed was
missing. `ps_screen_mark`'s own `where` clause literally cannot fire while
`DESCEND_APPLICABLE` holds, so `la_10_count_positives` (§1's own counter-
example: `count_of_list` on a list-input row) reproduces the pre-Arc3
rungs/attempts byte-for-byte, gated explicitly by
`tests/test_screen_codebook_migrated.py::
test_partial_cover_construction_descends_unscreened` (and re-confirmed by
`tests/test_retrieval_migrated.py::
test_la10_partial_cover_regression_scenario_reproduces_original_rungs`,
already standing).

### 9.1 A SECOND false-positive, found and fixed before landing

A first cut of `NOT_SLACK` compared the pool against the CURRENT remaining
budget (`ps_budget - ps_attempts`), recomputed every round. This measurably
regressed `tests/test_prog_synthesis_battery_migrated.py`'s own FROZEN
`br_19_pick_or_boost` row (`main_p7` arm): 2 trigger-matching mined chunks
(`ck_prog_if_stmt_n1_q0`/`q1`) against a budget of 3 — 1 unit of slack
already exists, and the classic mechanism reaches `enumerate` on its own
(`attempts: 3.0`, `construction: "ck_prog_if_stmt_n1_q1"`). Comparing
against the CURRENT remaining budget let the SECOND chunk get screened for
free once the FIRST chunk's real failed attempt shrank the remaining
budget to match the (unchanged) pool size — flipping the live
reproduction to `attempts: 2.0`, `construction: "ck_prog_if_stmt_n1_q0"` (a
different but still holdout-correct accept — genuinely BETTER, but not
BYTE-IDENTICAL, and this file is frozen and not owned by this rung).
Caught live (not by inspection) before it shipped. **Fixed by freezing the
WHOLE engage/no-engage verdict at goal-mint time**, against the goal's
FULL budget (`ps_goal`/`ps_goal_top` now also mint `ps_screen_engage =
Gte(ps_screen_pool0, ps_budget)`, a boolean, evaluated once): `Gte(2, 3)`
is `False` for `br_19_pick_or_boost` and STAYS `False` for that goal's
entire life, however many real attempts it later spends — both chunks now
take the classic path exactly as frozen. `test_prog_synthesis_battery_
migrated.py` (21 gates, including this exact live-reverify row) is
confirmed green, byte-untouched, unowned.

A related engine-level bug surfaced and was fixed en route: `ps_screen_
mark` does not clear `ps_screen_verdict`/`ps_screen_name` when it arms a
new candidate, so within a single `run_rules` fixpoint call the rule
engine could re-arm candidates #2, #3, ... before the Python dispatcher
ever ran `screen_construction` for candidate #1 — `ps_screen_reject`/
`ps_screen_admit` would then react to a STALE verdict left over from an
EARLIER candidate, wrongly excluding a LATER, never-actually-judged
candidate (caught live: a genuinely correct construction, deliberately
placed last in a specificity-ordered decoy pool, was excluded on the
FIRST decoy's stale FAIL verdict). Fixed with the standing project idiom
for exactly this class of defect (the P6.5 `verdict_attempt < eval_attempt`
precedent, here at screen grain): both rules now additionally require
`ps_screen_name == ps_screen_candidate` (the verb sets `ps_screen_name` to
the exact candidate it judged), so neither rule can fire on a verdict
computed for a different candidate.

### 9.2 What landed

- `seeds/program_synthesis.json` v1.5.0 → v1.5.1 (54 → 57 rules): `ps_
  propose`'s `where`/effects both gain a screen-bypass `Or` (SCREENABLE
  false, OR this candidate already screen-passed); NEW `ps_screen_mark`
  (arms the screen), `ps_screen_reject` (free kill + exclude,
  `screened_failed:1.0`), `ps_screen_admit` (mints `ScreenPass`, hands off
  to the unchanged propose/eval/accept chain). `ps_goal`/`ps_goal_top`
  additively mint `ps_screen_pool0`/`ps_screen_engage`. Three STALE
  comments left over from §1's revert (`ps_lattice_failed`, `ps_
  reproposal`, `ps_goal_top` — all claimed a `pending -> screen_pending`
  hand-off that no shipped effect ever performed) are corrected in place,
  comment-only, no behaviour change.
- `domains/prog_synthesis.py` — NEW `screen_construction` (the
  `screen_running` verb: dry-run `splice_binding`'s own template->IR logic
  against revealed rows via `_build_candidate_ir`/`_screen_eval`, spending
  no `ps_attempts`), registered in `_DISPATCH`; `read_goal` gains a
  `screen` sub-dict (`kills`/`candidate`/`verdict`) and the dead, never-
  written `pr_screen_used`/`pr_screen_budget` retrieval-grain keys (left
  over from Attempt 1, never wired to anything) are removed.
- NEW `tests/test_screen_codebook_migrated.py` — 6 gates: the decoy-kill
  headline (an over-budget chunk pool dies at the screen for free, the
  goal reaches `enumerate` with its full budget); the `screened_failed`
  tag verified directly on the graph; the `la_10` partial-cover byte-
  identity re-proof (`screen.kills == 0`, the screen never engaged); a
  genuinely correct candidate mixed into an over-budget wrong pool passes
  the screen and is accepted spending exactly one real attempt;
  screen-bookkeeping consistency + no-park across every fixture; a
  no-python-decision source audit scoped to `screen_construction` itself.
  Runtime well under 1s.
- `tests/test_program_synthesis_migrated.py` — rule-count pin (54 → 57).
  Two existing decoy fixtures needed reconciling against the new screen:
  `test_budget_bounded_integer_attempts_and_honest_exhaustion`'s 4-decoy
  pool (pool0=4 > budget=3) would otherwise be killed for free and
  ACCEPT instead of exhausting — `_teach_decoy` gained an opt-in `branch`
  parameter (wraps the wrong recipe in a constant-condition `IfThenElse`,
  stamping `tmpl_branch:1.0` directly — the SAME "set the normalised attr
  straight" idiom the helper already uses for `trigger_tokens`, since
  `_normalise_fold_marks` only ever runs once, at `boot()`, before any
  test-taught decoy exists) to stay DESCEND_APPLICABLE and hence
  byte-identical, preserving this test's own "budget honesty" purpose
  unchanged. `test_stall_regression_decoy_then_enumerate_reaches_
  terminal`'s single-decoy fixture (pool0=1 < budget=3) turned out to
  need NO change at all once `NOT_SLACK` was corrected to freeze against
  the FULL budget (§9.1) — it reproduces its original P6.5 numbers
  byte-for-byte, confirmed live, reverted back to its pre-edit form.
- `tests/test_retrieval_migrated.py` (additive) — the reversion-only gate
  (`test_codebook_screen_rules_are_absent_from_the_seed`) is renamed
  `test_attempt1_codebook_screen_rules_stay_absent_from_the_seed` and
  widened: Attempt 1's `pr_screen_*` names stay confirmed absent (never
  resurrected), AND the corrected `ps_screen_*` names are now confirmed
  PRESENT; the version/rule-count pin moves 1.5.0/54 → 1.5.1/57.
- `tests/test_mbpp_baseline_migrated.py` — the ONE previously-reported,
  out-of-scope drift (§6 above: task 479's live `construction` reads
  `retrieved_exemplar` where the frozen Q0-era artifact recorded `None`,
  a consequence of Arc3-R1's retrieval ladder landing, predating this
  rung) is reconciled via the file's OWN existing `_KNOWN_CONSTRUCTION_
  DRIFT` dated-pin mechanism (the same one already carrying task 267's
  Arc2-Q4 drift) — `{267: "range_sum_spine", 479: "retrieved_exemplar"}`.
  `outcome`/`status` are unchanged; only the construction label (and,
  since a retrieval accept spends one `ps_attempts` unit, its attempt
  count: 0.0 → 1.0) moved, in the improvement direction the dated-pin rule
  requires. The frozen artifact itself is untouched.

### 9.3 Non-regression — the full paired sweep

| suite | count | status |
|---|---|---|
| `test_program_synthesis_migrated.py` | 17 | green (rule-count pin 54→57; 2 fixtures reconciled per §9.2, one reverted unchanged) |
| `test_retrieval_migrated.py` | 31 | green (version/count pin + reversion-gate rename, §9.2) |
| **`test_screen_codebook_migrated.py` (NEW)** | **6** | **green** |
| `test_prog_synthesis_battery_migrated.py` | 21 | green, **frozen artifact + every live-reverify row byte-untouched** (including `br_19_pick_or_boost`, §9.1's own regression) |
| `test_prog_descent_migrated.py` | 17 | green, byte-identical |
| `test_prog_repair_migrated.py` | 13 | green, byte-identical |
| `test_descent_widening_migrated.py` | 11 | green, byte-identical |
| `test_mbpp_endgame_migrated.py` | 30 | green, frozen artifacts untouched |
| `test_mbpp_diet_migrated.py` | 18 | green |
| `test_prog_chunks_migrated.py` | 11 | green |
| `test_mbpp_spec_migrated.py` | 67 | green |
| `test_mbpp_baseline_migrated.py` | — | green (the one reported drift reconciled, §9.2; frozen artifact untouched) |
| `test_code_synthesis_baseline_migrated.py` | 11 | green |
| `test_retrieval_ceiling_migrated.py` | 19 | green |
| `test_prog_synthesis_selfimprove_migrated.py` | 5 | green |
| `test_mbpp_contamination_migrated.py` | shared gate | green |
| `test_render_llvm/python/rust_lua_migrated.py` + `test_prog_read_*_migrated.py` + `test_prog_constructions_migrated.py` + `test_prog_ir_migrated.py` | 416 | green (transitive `prog_synthesis` import neighbours) |

**Total: 657+ green** (the two sweeps above overlap on a few files;
counting each file once, 657), ~23s — well under the ~120s budget. No
parks, no stalls.

### 9.4 Honest residuals carried forward

1. **The screen does not catch every Q5 decoy class.** `NOT DESCEND_
   APPLICABLE` exempts ANY goal where SOME trigger-matching construction
   is `tmpl_branch`/`tmpl_scalar_fold`-shaped, REGARDLESS of whether that
   construction is itself right or wrong for the request — Q5's smaller
   "starter codebook shape" decoy class (7/24 of its `gapped:exhausted`
   mass, e.g. a wrongly-cued `max_of_two`/`min_of_two`) is therefore NOT
   killed by this screen (it is, by definition, DESCEND_APPLICABLE via its
   own branch shape). Only the DOMINANT chunk/diet-chunk decoy class
   (17/24 of Q5's mass — `mck_*`/`ck_*`/`ckt_*`, always `mode:
   code_write_stmts`, structurally INCAPABLE of ever satisfying `tmpl_
   branch`/`tmpl_scalar_fold` per `_normalise_fold_marks`'s own `mode ==
   "code_write"` gate) is in scope, and is confirmed killed by `tests/
   test_screen_codebook_migrated.py`'s own headline gate. This is the
   task's own explicit scope ("the Q5 decoy-shaped fixture (chunk-cued
   wrong complete construction...)"), not a shortfall discovered after
   the fact.
2. **`NOT_SLACK` is all-or-nothing per goal, not incremental.** Because
   `ps_screen_pool0`/`ps_screen_engage` are frozen once at mint (§9.1),
   a goal whose initial pool meets or exceeds its budget has EVERY
   eligible candidate screened for free, never a partial mix of screened
   and real; a goal with any initial slack is NEVER screened. This is
   simpler and more predictable than a per-round recomputation (and the
   per-round version is exactly what caused §9.1's regression), at the
   cost of not "just barely" engaging the screen for a goal that starts
   with slack but later runs low — that class is not currently exercised
   by any owned fixture, named here rather than engineered around blind.
3. **The three now-third-duplicated `DESCEND_APPLICABLE` copies remain
   three separate copies** (`ps_descend_mark`, `ps_enumerate_mark`, and
   now `ps_screen_mark`/`ps_propose`'s shared builder-script extraction) —
   Arc2-Q4 §6 already named the FIRST duplication a standing trap; this
   rung's OWN copies are, at least, generated from a single Python
   extraction point in the seed-authoring script (never hand-retyped), so
   a future edit to `ps_descend_mark`'s Or-clause would need the
   authoring script re-run, not three manual edits — a mitigation, not a
   fix. A true fix (a shared, referenceable sub-rule or macro) is out of
   this rung's scope.
4. **HR2's own registered bar ("cued `gapped:exhausted` -> ~0") is
   satisfied for the in-scope (chunk) decoy class and demonstrated on a
   dedicated fixture, not re-measured against the full 257-task MBPP
   endgame battery in this rung** — `test_mbpp_endgame_migrated.py`'s own
   30 gates (frozen artifacts) are confirmed untouched/green, but a fresh
   `mbpp_endgame_battery.py` re-run (which WOULD show the real-corpus
   `gapped:exhausted` count move) is a measurement phase, not this
   mechanism-landing rung's own scope — named as the natural next
   measurement, not attempted here.
