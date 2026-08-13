# The missing `gamma_production` StandingConcern handler — PREREG

Worktree: `/home/matt/ozmadev/ocelot-worktrees/gamma-production-adopt-handler`, branch
`gamma-production-adopt-handler`, forked at `3719b50` (verified via `git log --oneline -1
main` immediately before `git worktree add`).

Direct follow-on to `GAMMA_COLLAPSE_ALGORITHM_PREREG.md` / `_RESULTS.md` (merged, `3719b50`).
That rung's Q2 finding, quoted verbatim (`GAMMA_COLLAPSE_ALGORITHM_RESULTS.md` §0/§2):
*"`SelfConcern -> promote_self_concern -> StandingConcern` — ZERO code changes, GO bar met
exactly as registered. `StandingConcern -> judge -> adopt` — falls through to the generic
`comprehend_first` default (no `gamma_production` handler exists, mirroring the
`code_write`/`prog_read` precedent that WOULD be needed); reported as a named, out-of-scope
gap, not silently patched."* This rung builds that missing handler.

## 0. What is already true in the code (read directly, not assumed)

- `seeds/gamma_residual.json`'s `note_gamma_production_gap` mints
  `SelfConcern{status:'noted', source:'implicit', kind:'gamma_production', content:'Gamma
  repeatedly rejects (<src_type>) -[<edge_type>]-> (<tgt_type>) -- no admissibility production
  covers it'}` on support >= 2 recurrence of the SAME `Type1NoProduction` triple. No
  `has_self_concern` edge is minted (no reliable single-Agent anchor at this grain — the
  prior rung's own documented, deliberate choice).
- `scripts/jabberwock_daemon.py:2040-2148` (`_promote_relations_for_concern`) special-cases
  exactly two prior kinds (`code_write`, `prog_read`) that need a NON-generic
  `StandingConcern -> judge -> adopt` handler because the generic `comprehend_first`
  default's `induce_concern`/`ground_concern` composer does the structurally wrong thing for
  a non-conversational gap (measured live in ARC6 A25 for `prog_read`: it minted an inert,
  misleadingly-named rule and reported `grounded: true`). Three more kinds
  (`knowledge`/`self_account`/`reply_fix`) got the same treatment later
  (`GROUND_CONCERN_SIX_KINDS_PREREG.md`, `_process_knowledge_standing` /
  `_process_self_account_standing` / `_process_reply_fix_standing`,
  `jabberwock_daemon.py:2585-2666`). `gamma_production` is NOT one of the five —
  `test_promote_self_concern_accepts_the_minted_gap_with_zero_code_changes`
  (`tests/test_gamma_collapse_algorithm_migrated.py:120-156`) asserts explicitly
  `standing["pipeline"] == "comprehend_first"` for it, TODAY.
- `_concern_tick` (`jabberwock_daemon.py:2668-2730+`) is the ACTUAL dispatch mechanism: for
  every `pending` `StandingConcern`, it checks `at.get("kind")` against a fixed ladder of
  `if` branches (`code_write` / `prog_read` / `knowledge` (non-experiment) / `self_account` /
  `reply_fix` (non-experiment)), each routing to a dedicated `_process_<kind>_standing`
  function that calls a corresponding `domains/<kind>_growth.py::work_on_<kind>_gap` and
  records a MECHANICAL outcome datum (`<kind>_compose_ok` / `<kind>_compose_reason`) onto the
  `StandingConcern`, then sets `status = "processed"`. Nothing else about that record is a
  decision — the corresponding seed rule (`note_<kind>_composition_exhausted`, one per kind,
  each the SAME `note_prog_read_composition_exhausted` shape verbatim, `prog_read_gap.json:
  189-217`) reads the outcome datum and DECIDES whether to mark `experiments_exhausted`.
- **The five existing `work_on_<kind>_gap` handlers all install a NON-grammar change on
  success**: `code_write`/`self_account` widen a `ShapeSignature` codebook or recognise an
  existing `SelfProcess` account; `knowledge`/`reply_fix` re-run an existing self-heal chain.
  None of them mutate `Grammar`/`ConsistencyChecker`, and none of them needs a second,
  separately-gated step between "the composer produced a candidate" and "the candidate is
  live" — a taught `ShapeSignature` becomes load-bearing the INSTANT `teach()` writes it
  (`code_write_growth.py:161-228`, no approval gate), because widening a codebook another
  rule reads unconditionally is not the same kind of operation as widening what edges may
  EXIST AT ALL. `checker.rs:1-3`'s own docstring gives that operation its own theorem
  (Theorem XII, reference-monitor containment) for exactly this reason — this is the SAME
  distinction `GAMMA_COLLAPSE_ALGORITHM_RESULTS.md` §3 (Q3) already drew between the sd-loop
  mint gate and the Γ admission gate, one level down: **a `gamma_production` handler cannot
  synchronously "close" its concern inside `_concern_tick` the way the other five do, because
  doing so would be a rule-adjacent Python path calling `add_production` with no human step
  in between — exactly what Theorem XII forbids.**
- `runners/dsl/src/py.rs:7880-7893` — `is_edge_admissible(src: NodeID, edge_type: str,
  candidate_tgt_type: str, candidate_tgt_attrs: Optional[dict]) -> bool`: a REAL grammar
  check against a concrete `src` node instance (not a bare type name) plus a target type
  string. `py.rs:7813-7830` (`add_production`) parses one production JSON and calls
  `inner.checker.grammar.add(p)` directly — confirmed (again, `GAMMA_PYO3_REROUTE_RESULTS.md`,
  `3e3daa5`, merged, NO-GO on rerouting it to mirror) that this does NOT write a
  `GammaProduction` graph mirror; only `checker.grammar` (the struct `check_edge` reads) is
  touched. This is the exact binding `test_manual_adopt_flips_check_edge_and_theorem_xii_holds`
  (`tests/test_gamma_collapse_algorithm_migrated.py:159-192`) already exercises manually.
- `jabberwock_daemon.py:2150-2220` (`promote_self_concern`) and its HTTP surface
  (`POST /api/self_concerns/<id>/promote`, `jabberwock_daemon.py:3618-3631`) is the standing
  precedent for "a human-gated Python function reachable over the daemon's own admin API,
  never invoked automatically." `POST /api/proposals/<id>/approve`
  (`jabberwock_daemon.py:3806`, `_approve_proposal`, a DIFFERENT mechanism —
  `ExtensionProposal`/rung-4 Rust Term proposals, ungated by this rung) is a second, unrelated
  precedent for the same shape: a human clicks approve, a Python function performs the
  irreversible action, never a rule.
- `adapter.inner.in_neighbours(nid, edge_type)` (`py.rs:2074`) exists — needed to walk
  `StandingConcern -> SelfConcern` backwards (the `promoted_to` edge runs
  `SelfConcern -promoted_to-> StandingConcern`, forward-only; no reverse lookup precedent
  exists in `jabberwock_daemon.py` today because every existing caller already holds the
  `sc` node from the promote step itself).

## 1. The shape decision, stated before building

**A `gamma_production` concern needs TWO Python-reachable steps, not one, and this is a real
difference from every existing kind, not an oversight to normalise away:**

1. **JUDGE (synchronous, inside `_concern_tick`, same shape as the other five)** — parse the
   concern's own recorded triple back out of its `content` string (mechanical text-prep, the
   `prog_read_growth._parse_prog_read_content` precedent exactly), probe
   `is_edge_admissible` against a REAL node of `src_type` (an existing one if the live graph
   holds one, else a freshly-minted probe node — documented honestly as a residual, §6 below),
   build a candidate `Production` JSON, and record the mechanical outcome
   (`gamma_production_judge_status` ∈ `{ready_for_adopt, already_admissible,
   unresolvable}`, `_reason`, and — only for `ready_for_adopt` — the candidate production as a
   JSON string) onto the `StandingConcern`. This step calls `is_edge_admissible` (a read-only
   probe) and NEVER `add_production`.
2. **ADOPT (a SEPARATE, human-gated function, never called from `_concern_tick`, reachable
   only via an explicit action — the `promote_self_concern` precedent)** — re-reads the
   candidate off the `StandingConcern`, RE-VERIFIES the triple is still inadmissible right
   now (judging on stale data would itself be a bug — the task's own instruction), calls
   `add_production`, then verifies the exact triple flips to admissible while an unrelated
   triple does not. Only this function may call `add_production`, and it is never on any path
   `_concern_tick`/`run_rules` reaches.

This is NOT a redesign of the five-kind dispatch pattern — `_process_gamma_production_standing`
has the EXACT same shape as `_process_prog_read_standing` et al. (parse `about`, call a
`domains/gamma_production_growth.py` function, record a mechanical outcome, set
`status = "processed"`). What's different is that "processed" here can mean "awaiting a human
decision," not "closed" — and closing requires the second, separately-gated call. This is a
genuine, principled asymmetry (named in the task brief itself as an acceptable NO-GO
condition if it didn't fit) — it fits, with this one adjustment.

## 2. Falsifiable predictions, registered before building

**Prediction 1 (fits the dispatch pattern, with the judge/adopt split).** The `_concern_tick`
kind-ladder pattern (`if at.get("kind") == "gamma_production": ...`) extends cleanly to a
sixth kind, reusing every existing precedent (parse-content, mechanical-outcome-recording,
`note_*_composition_exhausted` seed-rule shape) EXCEPT that the "on success, the gap is
closed" assumption baked into the other five does not hold — success here means "ready for a
human," and a genuine close requires the second gated call. **Falsifiable:** if building this
reveals `_concern_tick`'s ladder structurally cannot represent a two-step outcome (e.g. it
assumes `status="processed"` always means terminal), that's a NO-GO on reusing the pattern
as-is and must be reported, not silently worked around.

**Prediction 2 (the judge step needs a real probe node, not a type-only check).**
`is_edge_admissible` takes a concrete `NodeID`, and the substrate exposes no
type-name-only admissibility probe. The judge step will need to find-or-mint a node of
`src_type` to call it. **Falsifiable:** if a type-only check exists somewhere unexamined
(re-grep `py.rs` for a second admissibility binding before concluding this), Prediction 2 is
wrong and the probe-node step is unnecessary complexity.

**Prediction 3 (Theorem XII holds through the split, exactly as in the prior rung).** No rule
in `seeds/gamma_production_adopt.json` (new) calls `add_production`; the ONLY call site in
this entire change is inside the new, explicitly-invoked `adopt_gamma_production_standing`
function. **GO bar:** a test asserts this by construction (grep the new seed file's `effects`
for `add_production` — must be absent) AND behaviourally (judge alone never flips
`is_edge_admissible`; only the adopt call does, and only for the exact triple). **NO-GO
condition:** any path from `run_rules`/`_concern_tick` to `add_production` that does not pass
through the new adopt function's own explicit human/experiment-invoked call.

## 3. The slice, concretely

1. **`domains/gamma_production_growth.py` (new)** — `_parse_gamma_content`,
   `_probe_node_for_type`, `judge_gamma_production_gap`, `adopt_gamma_production`,
   `pending_gamma_production_gaps` (the family reader precedent). No Rust changes; reuses
   `agent.s.is_edge_admissible` / `agent.s.add_production` exactly as
   `tests/test_gamma_collapse_algorithm_migrated.py` already does manually.
2. **`scripts/jabberwock_daemon.py`** — `_process_gamma_production_standing` (the
   `_process_prog_read_standing` precedent), one new branch in `_concern_tick`'s kind ladder,
   and `adopt_gamma_production_standing` (the `promote_self_concern` precedent: human-gated,
   idempotent, checked-before-acted). One new HTTP route,
   `POST /api/standing_concerns/<id>/adopt_gamma_production`, mirroring
   `POST /api/self_concerns/<id>/promote`'s shape exactly. A small, additive readback in
   `domains/reflective_faculty._run_self_improvement_status` (surface `awaiting_adopt`
   alongside the existing `exhausted`/`exhausted_note` readback — same mechanical-render
   status, no new decision).
3. **`seeds/gamma_production_adopt.json` (new)** — three rules, all reading
   `gamma_production_judge_status`/`kind` off a `StandingConcern` reached via
   `[["sc", "promoted_to", "standing"]]` (no `has_self_concern` edge needed — the same
   anchor-free discipline `gamma_residual.json` already established for this kind):
   `note_gamma_production_awaiting_adopt` (sets `awaiting_adopt = true`),
   `resolve_gamma_production_already_admissible` (marks the original `sc` `status="resolved"`
   when the world moved on and the triple is already admissible — no adopt needed), and
   `note_gamma_production_composition_exhausted` (the verbatim
   `note_prog_read_composition_exhausted` shape, for the `unresolvable` outcome — e.g. the
   `content` string didn't parse).
4. **Tests** — `tests/test_gamma_production_adopt_handler_migrated.py` (new), the
   `test_gamma_collapse_algorithm_migrated.py` precedent extended one rung further: recurrence
   → mint → promote → `_concern_tick` judges (status stays open, `awaiting_adopt` set,
   `is_edge_admissible` still False) → explicit `adopt_gamma_production_standing` call →
   `is_edge_admissible` flips True on the exact triple, stays False on an unrelated one,
   `SelfConcern` resolved, Theorem XII re-checked exactly as the prior rung's own test did.

## 4. Safety precondition, hard, not soft (Theorem XII, restated for this rung)

- No rule in `seeds/gamma_production_adopt.json` (or anywhere else touched by this rung) may
  call `add_production`. Checked by construction (grep) and behaviourally (judge-only run
  through `run_rules`/`_concern_tick` never changes `is_edge_admissible`).
- `adopt_gamma_production_standing` re-verifies inadmissibility immediately before calling
  `add_production` (judging on stale data — e.g. a concurrent adopt of the same triple, or a
  vocabulary change since the judge step ran — would itself be a bug this check exists to
  catch), and is idempotent (a `StandingConcern` already `adopted` is rejected, not re-run).
- If any part of this cannot be verified to preserve containment, that part is a hard NO-GO
  and is reverted, not shipped with a caveat.

## 5. GO / NO-GO bar

**GO** requires: the judge step reachable with zero changes to `_promote_relations_for_concern`
NOT NEEDED here (it's already correct, per the prior rung — no promotion-side change at all,
confirmed in §0); the six-kind `_concern_tick` ladder extended cleanly; a live before/after
demonstration of triple-level inadmissible→admissible through the REAL dispatch handler (not
a manual script); Theorem XII holding throughout, checked explicitly; full regression green
(the prior rung's 5/5 `test_gamma_collapse_algorithm_migrated.py` unchanged, plus the new
suite).

**NO-GO** is fully acceptable and will be reported plainly, not forced, if: the judge/adopt
split turns out not to fit `_concern_tick`'s assumptions cleanly (Prediction 1's falsifier);
`is_edge_admissible` cannot be probed without a real node in a way that's honest and
non-fabricating (Prediction 2's falsifier, if no reasonable resolution exists); or Theorem XII
cannot be verified to hold (§4).

## 6. Regression plan

- Python: `tests/test_gamma_production_adopt_handler_migrated.py` (new), plus
  `tests/test_gamma_collapse_algorithm_migrated.py` (must stay 5/5, unchanged file), plus
  `tests/test_gap_awareness_migrated.py` / `tests/test_self_concern_promote_migrated.py`
  (shared surface, must stay green).
- No Rust changes are predicted (§0 — the needed bindings already exist); if the build reveals
  a genuine need for one, it will be justified explicitly in the RESULTS doc before being made,
  per the task's own instruction, and kept minimal.
- Paired failing-node-id lists reported if anything regresses, never bare counts, per house
  discipline.
