# The missing `gamma_production` StandingConcern handler — RESULTS

Worktree: `/home/matt/ozmadev/ocelot-worktrees/gamma-production-adopt-handler`, branch
`gamma-production-adopt-handler`, forked at `3719b50`. PREREG:
`docs/research/engine_substrate/GAMMA_PRODUCTION_ADOPT_HANDLER_PREREG.md`.

Direct follow-on to `GAMMA_COLLAPSE_ALGORITHM_RESULTS.md` (merged, `3719b50`). That rung's Q2
finding: promotion (`SelfConcern -> StandingConcern`) already worked with zero code changes for
a `gamma_production` concern; `StandingConcern -> judge -> adopt` fell through to the generic
`comprehend_first` default because no dedicated handler existed. This rung builds that handler.

## 0. Headline verdicts

| Question | Verdict |
|---|---|
| Does `gamma_production` fit the existing five-kind `_concern_tick` dispatch pattern? | **Yes, with one principled adaptation, registered in advance (PREREG §1, Prediction 1).** The parse/record/seed-rule shape transfers verbatim from `prog_read_growth.py`; the ONE genuine difference is that "processed" here can mean "awaiting a human," not "closed" — a synchronous JUDGE step (read-only, never `add_production`) plus a separate, explicit, human-gated ADOPT step, because a Production changes what edges may exist AT ALL (Theorem XII) while every other kind's close only widens something a rule already reads unconditionally. |
| Is a real, concrete `Production` installed into the live Grammar through this rung's own dispatch code (not a manual script)? | **Yes.** Live before/after in §3: `is_edge_admissible` flips `False -> True` on the exact triple via `jd.adopt_gamma_production_standing`, called directly (not the prior rung's raw-script manual step). |
| Does Theorem XII (reference-monitor containment) hold throughout? | **Yes, checked by construction and behaviourally.** No rule in either seed file mentions `add_production` (grepped, `test_no_seed_rule_effect_calls_add_production`); the ONLY call site in `domains/gamma_production_growth.py` is inside `adopt_gamma_production` (`test_gamma_production_growth_module_has_exactly_one_add_production_call_site`); judge-only runs through the full `_concern_tick` + `run_rules` fixpoint never change admissibility (`test_judge_alone_through_run_rules_never_changes_admissibility`); adoption is scoped to the exact triple (an unrelated, reversed triple stays inadmissible, live-verified). |
| GO or NO-GO? | **GO.** Built, not named-not-built: `domains/gamma_production_growth.py` (new), `seeds/gamma_production_adopt.json` (new, 3 rules), two new functions + one new HTTP route + a two-branch `_concern_tick` addition in `scripts/jabberwock_daemon.py`, a small additive readback in `domains/reflective_faculty.py`. Zero Rust changes (the needed PyO3 bindings — `is_edge_admissible`, `add_production` — already existed and are reused exactly as the prior rung's manual demonstration used them). |

## 1. What was built, and why the split (PREREG §1, confirmed as designed)

**`domains/gamma_production_growth.py` (new, 265 lines).** The `prog_read_growth.py` /
`knowledge_growth.py` sibling, but split into two functions instead of one `work_on_*_gap`,
because closing a `gamma_production` gap is not one kind of operation the way the other five
are:

- `judge_gamma_production_gap(agent, about_text)` — parses the concern's own `content` string
  (`_parse_gamma_content`, the exact reverse of `note_gamma_production_gap`'s StringConcat
  template, the `prog_read_growth._parse_prog_read_content` precedent), probes
  `is_edge_admissible` against a real node of `src_type` (`_probe_node_for_type`: reuse an
  existing node of that type if the graph holds one, else mint a fresh empty-attrs one — the
  exact shape `test_gamma_collapse_algorithm_migrated.py`'s own `_register_vocab_for_clean_type1`
  uses for its `a_node`/`b_node`), and returns one of three honest outcomes:
  `ready_for_adopt` (still inadmissible, a candidate Production JSON attached),
  `already_admissible` (the world moved on — some other production now covers it, nothing to
  adopt), or `unresolvable` (the content string didn't parse). **Never calls
  `add_production`.**
- `adopt_gamma_production(agent, candidate_production, expected_triple=None)` — the ONE
  function in this module that may call `add_production`. RE-VERIFIES the triple is still
  inadmissible immediately before adopting (refuses if it's already admissible — "judging on
  stale data would be a bug," the task's own instruction), calls `add_production`, verifies the
  exact triple flips admissible.

**`scripts/jabberwock_daemon.py`.**

- `_process_gamma_production_standing` (`scripts/jabberwock_daemon.py:2581-2622`) — the
  `_process_prog_read_standing` precedent: called from `_concern_tick`
  (`scripts/jabberwock_daemon.py:2827-2830`, the new branch in the kind ladder), calls
  `judge_gamma_production_gap` synchronously, records the mechanical outcome
  (`gamma_production_judge_status` / `_reason` / `_candidate` JSON) onto the `StandingConcern`,
  sets `status = "processed"` — exactly like every sibling. Never calls adopt.
- `adopt_gamma_production_standing` (`scripts/jabberwock_daemon.py:2625-2680`) — the
  `promote_self_concern` precedent: human-gated, idempotent (refuses an already-`adopted`
  concern), requires `gamma_production_judge_status == "ready_for_adopt"` (refuses otherwise —
  never derives a candidate itself), reads the candidate JSON straight off the `StandingConcern`
  (never re-derived independently, so what's adopted is exactly what was judged), calls
  `gamma_production_growth.adopt_gamma_production`, and on success marks the `StandingConcern`
  `status = "adopted"` and walks the `promoted_to` edge backwards
  (`adapter.inner.in_neighbours`, `py.rs:2074`) to mark the ORIGINAL `SelfConcern`
  `status = "resolved"`.
- `POST /api/standing_concerns/<id>/adopt_gamma_production` — the `POST
  /api/self_concerns/<id>/promote` precedent, one new route calling the function above under
  `AGENT_LOCK`, documented in the route-listing comment alongside the other admin routes.

**`seeds/gamma_production_adopt.json` (new, 3 rules, depends on `gamma_residual`).** Reads the
mechanical outcome the Python side recorded and DECIDES what it means — never a decision in
Python:

- `note_gamma_production_awaiting_adopt` — `ready_for_adopt` → sets `awaiting_adopt = true` (the
  human-visible "ready for a decision" signal).
- `resolve_gamma_production_already_admissible` — `already_admissible` → marks the ORIGINAL
  `SelfConcern` `status = "resolved"` directly, no adopt needed.
- `note_gamma_production_composition_exhausted` — `unresolvable` → the
  `note_prog_read_composition_exhausted` shape verbatim, marks `experiments_exhausted` +
  `exhausted_note`.

All three match on `[["sc", "promoted_to", "standing"]]` alone (no `has_self_concern` edge —
`gamma_residual.json`'s own documented choice, since this kind carries no reliable single-Agent
anchor; `promote_self_concern` always writes `promoted_to` regardless of kind, so this anchor is
never missing).

**`domains/reflective_faculty.py`** — one small, additive readback in
`_run_self_improvement_status`: `awaiting_adopt` is surfaced in the same mechanical way
`exhausted`/`exhausted_note` already are (a pure rendering of a fact a rule already decided,
never a new decision).

**No Rust changes.** Predicted in the PREREG (§0/§6) and confirmed: `is_edge_admissible` and
`add_production` already existed exactly as needed; this rung is Python growth-module + seed
data only, reusing the prior rung's PyO3 surface without modification.

## 2. Live before/after demonstration

Real command, real `WorldAdapter` + `load_all_seeds` boot + the real `jabberwock_daemon`
dispatch functions (not the prior rung's raw-script manual adopt):

```
=== BEFORE: check_edge on the target triple ===
admissible? False
rejected: InadmissibleEdge
rejected: InadmissibleEdge

=== SelfConcern minted ===
Gamma repeatedly rejects (GammaSpikeFoo) -[gp_demo_edge]-> (GammaSpikeBar) -- no admissibility production covers it

=== promote_self_concern (ZERO code changes) ===
pipeline: comprehend_first ok: True

=== _concern_tick (generic comprehend_first path would have fired here pre-rung) ===
status: processed
gamma_production_judge_status: ready_for_adopt
candidate: {"src": {"type": "GammaSpikeFoo", "var": "x"}, "edge_type": "gp_demo_edge", "tgt": {"type": "GammaSpikeBar", "var": "y"}, "provenance": "gamma_production_adopt_handler:judge"}
is_edge_admissible still False? False
awaiting_adopt: True

=== EXPLICIT, HUMAN-GATED adopt call ===
{'ok': True, 'standing_concern': 24182, 'triple': ('GammaSpikeFoo', 'gp_demo_edge', 'GammaSpikeBar'), 'reason': 'add_production made (GammaSpikeFoo) -[gp_demo_edge]-> (GammaSpikeBar) admissible'}

=== AFTER: check_edge on the target triple ===
admissible now? True
add_edge result: ADMITTED

=== unrelated triple (reverse direction) stays inadmissible ===
admissible? False

=== original SelfConcern resolved ===
status: resolved

=== Theorem XII grep check ===
gamma_residual.json -> add_production in rule effects: False
gamma_production_adopt.json -> add_production in rule effects: False
```

Note the `[self-build]` lines preceding this output (visible in the raw run, omitted above) are
`load_all_seeds`'s own unrelated boot-time self-build activity (minting standing motor-intent /
self-improvement rules from other seeds) — confirmed unrelated by name (none mention `gamma` or
`Production`) and by the fact that `test_gamma_collapse_algorithm_migrated.py`'s own prior-rung
demonstration shows the identical boot-time behaviour.

## 3. Theorem XII, explicit

Checked three independent ways, matching the prior rung's own §8 discipline:

1. **By construction (static).** `test_no_seed_rule_effect_calls_add_production` greps the full
   `rules` array of BOTH `seeds/gamma_residual.json` and `seeds/gamma_production_adopt.json` (as
   loaded JSON, not source text) for the string `"add_production"` — absent in both.
   `test_gamma_production_growth_module_has_exactly_one_add_production_call_site` counts literal
   `.add_production(` call sites in `domains/gamma_production_growth.py` — exactly one (inside
   `adopt_gamma_production`).
2. **By behaviour, judge alone.** `test_judge_alone_through_run_rules_never_changes_admissibility`
   runs the FULL judge side of the pipeline (recurrence → mint → promote → `_concern_tick` →
   `run_rules(400000)`, i.e. every rule this rung adds, to fixpoint) and asserts
   `is_edge_admissible` is still `False` afterward.
3. **By behaviour, adopt scoping.** `test_adopt_gamma_production_standing_flips_check_edge_and_resolves_concern`
   (and the live demonstration, §2) confirms the exact triple flips to admissible while an
   unrelated, reversed triple (`GammaSpikeBar -[gp_adopt_edge]-> GammaSpikeFoo`) stays
   inadmissible — adoption is scoped to the exact adopted triple, not a blanket relaxation.

**The reference-monitor invariant held throughout, unconditionally**, and — new in this rung,
not present in the prior one — is now exercised through the REAL dispatch handler
(`_concern_tick` → `adopt_gamma_production_standing`), not a hand-written demonstration script
standing in for one.

## 4. The two other judge outcomes, also gated correctly

- **`already_admissible`** — simulated by installing a competing production for the exact
  triple out-of-band BEFORE the judge step runs (standing in for some other adopt having
  already covered it). The judge step recognises this honestly (no candidate is built — nothing
  to adopt), the seed rule resolves the ORIGINAL `SelfConcern` directly, and a subsequent
  `adopt_gamma_production_standing` call is REFUSED (`gamma_production_judge_status` is
  `already_admissible`, not `ready_for_adopt`) — verified in
  `test_already_admissible_outcome_resolves_the_concern_without_any_adopt_call`.
- **`unresolvable`** — a hand-authored `SelfConcern` whose content does not match
  `note_gamma_production_gap`'s own template (standing in for a future format drift) is
  honestly exhausted (`experiments_exhausted` + a specific `exhausted_note`), never silently
  treated as ready and never crashing the tick loop — verified in
  `test_unresolvable_content_marks_experiments_exhausted`.

## 5. GO / NO-GO, against the PREREG's registered bar

**GO**, on every registered bar (PREREG §5):

- Promotion required zero changes (confirmed again, `res["pipeline"] == "comprehend_first"`
  asserted in every test's own mint-and-promote helper — the SAME assertion the prior rung's
  test made, now proven to still hold after this rung's changes).
- The six-kind `_concern_tick` ladder extended cleanly with the judge/adopt split (PREREG
  Prediction 1, confirmed — no structural fight with the ladder; "processed" already meant
  "the growth module looked at this," never universally "closed," across the existing five
  kinds' own varying `_compose_ok` semantics).
- `is_edge_admissible` needed a real probe node, exactly as predicted (PREREG Prediction 2,
  confirmed — no type-only admissibility binding exists; `_probe_node_for_type` is the honest,
  documented resolution, not a fabrication).
- Theorem XII holds, checked three ways (§3).
- Live before/after through the real dispatch handler (§2).
- Full regression green (§6).

No NO-GO condition from the PREREG was triggered.

## 6. Regression

**New suite.** `tests/test_gamma_production_adopt_handler_migrated.py`: **11/11 passed**
(182.29s) — judge-only outcomes (ready_for_adopt / already_admissible / unresolvable), the
live adopt flip + resolve + Theorem XII checks, idempotency, refusal-before-judge, refusal on
wrong kind / unknown id, and the two static Theorem-XII construction checks.

**Prior rung, unchanged file.** `tests/test_gamma_collapse_algorithm_migrated.py`: **5/5
passed** (68.84s) — byte-identical to the file merged in `3719b50`, confirming this rung did
not need to (and did not) touch it.

**Shared surface (broader diligence sweep beyond the task's own explicit bar, run to
completion, not truncated).**

- `tests/test_gap_awareness_migrated.py` + `tests/test_self_concern_promote_migrated.py` +
  `tests/test_ground_concern_six_kinds_migrated.py` + `tests/test_prog_read_selfimprove_migrated.py`
  (run together): **37 passed, 0 failed** (1237.68s). A worktree environment note, not a code
  defect, matching CLAUDE.md's own documented condition precisely: this worktree's `data/` was
  a near-empty checkout (`git worktree add` does not carry gitignored local caches), which
  first produced spurious `F`s in `test_gap_awareness_migrated.py` until `data/` was symlinked
  from the canonical tree (`ln -s /home/matt/ozmadev/ocelot/data data`) — after which the full
  suite is clean. This reproduces the identical "data/ symlinked vs absent" condition the prior
  rung's own §9 already documented; it is worktree setup, not a regression.
- `tests/test_self_improvement_visibility_migrated.py` + `tests/test_code_curriculum_migrated.py`
  (run together): **23 passed, 0 failed** (1364.99s). One test in this pair
  (`test_published_beyond_boundary_lesson_files_gaps_not_shapes`, unrelated to this rung's own
  `code_write`/`gamma_production` boundary — it exercises the CODE-CURRICULUM published-lesson
  pipeline) accounted for the large majority of this pair's wall-clock time under measured CPU
  contention from an unrelated, concurrently-running heavy pytest job in a different worktree on
  the same machine (confirmed via `ps`) — a real but environment-caused slowdown, not a hang
  (CPU usage stayed pinned near 100% throughout) and not a regression this rung introduced.

No Rust changes were made, so no Rust regression run was needed (PREREG §0/§6's prediction
confirmed).

## 7. What this does NOT establish

- It does not measure how often a real `gamma_production` gap would actually reach
  `ready_for_adopt` in live agent operation — the prior rung's own §10 already noted no
  production traffic was run with `gamma_residual_capture` enabled; this rung inherits that
  same honest gap (still no measurement of real-world recurrence rate).
- It does not build any UI/CLI polish beyond the one HTTP route and the one small
  `awaiting_adopt` readback — a human operator today would call the endpoint directly or use
  `_run_self_improvement_status`'s text rendering; no dashboard/approval-list view was added.
- The `_probe_node_for_type` admissibility check is TYPE-level, matching the granularity the
  underlying `GammaResidual`/`SelfConcern` record already captures (Q1 of the prior rung: a
  `Type1NoProduction` triple is "already a complete, well-typed, atomic 3-tuple" with no
  attr-level specificity recorded) — but if some future production's `where`-clause is
  attr-sensitive, a probe node picked from the live graph (or freshly minted with empty attrs)
  could in principle answer differently than the ORIGINAL rejected instance did. This is not a
  regression this rung introduces; it is inherited from the parent rung's own recording
  granularity, named here rather than silently assumed away.
- It does not address the `add_production` no-mirror drift the prior rung named in its own §7
  (unrelated, unfixed, out of scope here too — `adopt_gamma_production_standing`'s adopted
  productions are real and admission-effective but, like the prior rung's manual demonstration,
  do not write a `GammaProduction` graph mirror).
- It does not sweep or connect to the SHAPE_AUDIT 159/634 population — out of scope per the
  task brief, unrelated to this rung's own change.

## 8. Commit

Committed in this worktree; branch `gamma-production-adopt-handler`, not merged into `main` —
left for the orchestrating session per instruction.
