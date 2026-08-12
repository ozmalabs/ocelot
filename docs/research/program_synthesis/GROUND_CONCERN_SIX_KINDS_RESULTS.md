# `ground_concern`'s comprehension composer, Path 2 — RESULTS: three kinds fixed, three already safe, live-verified

**Date:** 2026-08-12.
**Prereg:** `GROUND_CONCERN_SIX_KINDS_PREREG.md` (this directory).
**Predecessor:** `GROUND_CONCERN_COMPREHENSION_HONESTY_RESULTS.md` — proved
LIVE that `domains/reflective_faculty.py::_compose_comprehension_rule`
cannot be safely gated from what it receives, and named Path 2 (per-kind
routing checks at the promotion/tick layer, mirroring `code_write`/
`prog_read`) as the correct, smaller fix. This rung builds Path 2 for the
six kinds its own §2 table named as still exposed.
**Template:** `PROGRAM_SYNTHESIS_ARC6_PROGREAD_SELFIMPROVE.md` (amendment
A25).
**Base commit:** `6427d54` (`main`'s tip at start). Worktree
`/home/matt/ocelot-ground-concern-six-kinds`, branch
`ground-concern-six-kinds`.
**Engine:** `c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567`
(committed `runners/dsl/python/substrate_rs/_native.abi3.so`, copied
verbatim from the canonical tree, unmodified — same sha the predecessor
investigation and A25 both used), verified resolving from inside the
worktree. Coherence probe passed: `add_node("T", {"lst":[1,2,3],
"tup":(1,2,3)})` reads back `[1,2,3]` and `(1,2,3)` distinctly.
**`domains/reflective_faculty.py`'s `_compose_comprehension_rule`:
UNTOUCHED** (`git diff main -- domains/reflective_faculty.py` is empty).
`domains/prog_read_growth.py`, `seeds/prog_read_gap.json`,
`seeds/code_write_gap.json`: also untouched.

---

## 0. VERDICTS

| kind | mint site | existing mechanism found? | verdict | build |
|---|---|---|---|---|
| `knowledge` | `gap_awareness.json::note_unresolved_topic_gap` | YES — `WorldAdapter.ground_unknowns`/`answer_about` (CLAUDE.md's own "self-heal" section) | **GO — routed to it, not rebuilt** | `domains/knowledge_growth.py` + `_process_knowledge_standing` + `seeds/knowledge_gap_resolve.json` |
| `self_account` | `gap_awareness.json::note_self_account_gap` | YES — `SelfProcess`/`find_self_process` (CLAUDE.md's own "self_processes" section) | **GO — routed to it, not rebuilt; NO-GO precisely on auto-authoring a new account (would fabricate a self-account)** | `domains/self_account_growth.py` + `_process_self_account_standing` + `seeds/self_account_gap_resolve.json` |
| `reply_fix` | `gap_awareness.json::note_upload_reply_gap` / `note_upload_vision_gap` | SPLIT — YES for `upload_attachment_reply` (loading two named seeds); NO for `upload_vision_wiring` (no attachment bytes reachable from the concern's text) | **GO on the `comprehend_first` sub-case only; the `experiment` sub-case was already correctly wired and is untouched** | `domains/reply_fix_growth.py` + `_process_reply_fix_standing` + `seeds/reply_fix_gap_resolve.json` |
| `instruction` | `gap_awareness.json` (unrouted-verb rule) | YES — already correctly reached, no fix needed | **NO-GO on building anything — no bug** | nothing |
| `performance` | `comprehension_health.json::note_comprehension_latency_gap` | YES — already correctly reached, no fix needed | **NO-GO on building anything — no bug** | nothing |
| `comprehension` | `comprehension_health.json::note_recurring_speech_act_divergence` | YES — already correctly reached, no fix needed | **NO-GO on building anything — no bug** | nothing |

**The one thing worth reading if you read nothing else.** The task brief's
"six kinds fall through to the fallback" framing was the predecessor
investigation's own conditional statement ("whenever they don't qualify for
the experiment bundle") — true for all six in the abstract, but a LIVE
measurement taken before writing a single line of fix code found the
population splits 3/3: `instruction`/`performance`/`comprehension` never
actually fail to qualify (an unconditional `kind in (...)` in
`_promote_relations_for_concern` routes them to the genuine experiment
composer regardless of content), so building anything for them would have
been dead code with no path to ever run — the same "a resolve rule would be
dead code" discipline A25 already applied to a single rule, applied here to
three entire modules. The three kinds that DO need a fix
(`knowledge`/`self_account`/`reply_fix`) each route to a DIFFERENT existing
mechanism already living elsewhere in this tree — this is not one fix
copy-pasted three times.

---

## 1. LIVE MEASUREMENT THAT SET THE BARS (before any code was written)

A probe (real `WorldAdapter`, real `load_all_seeds`, no mocks) fed each of
the six kinds realistic content through `promote_self_concern` and, for the
stored relations, `reflective_faculty.induce_concern`/`ground_concern`
directly (what `_concern_tick`'s generic branch does):

| kind | content | pipeline (measured) | composer reached |
|---|---|---|---|
| `knowledge` | `"photosynthesis"` | `comprehend_first` | `compose_comprehension_rule` → dead `describe_scene` rule, `grounded:true` |
| `self_account` | `"reasoning"` | `comprehend_first` | same dead rule |
| `reply_fix` | `"upload_attachment_reply"` | `comprehend_first` | same dead rule |
| `instruction` | `"elaborate further details"` | `experiment` (unconditional) | `compose_experiment_rule` — genuine `author_experiment_from_residual_*`/`judge_*`/`mark_adopt_ready_*` triple + a REAL `cue_variant` proposing a route for the unrouted verb |
| `performance` | (`note_comprehension_latency_gap`'s own content) | `experiment` (unconditional) | genuine, `reply_variant` honestly walls (no overlap — an abstention, not a lie) |
| `comprehension` | (`note_recurring_speech_act_divergence`'s own content) | `experiment` (unconditional) | genuine, same shape as `performance` |

This measurement is reproduced in full in
`GROUND_CONCERN_SIX_KINDS_PREREG.md` §0 and is the reason this rung built
three fixes, not six.

---

## 2. THE THREE FIXES, EACH ROUTED TO A DIFFERENT EXISTING MECHANISM

### 2.1 `knowledge` → `WorldAdapter.ground_unknowns`/`answer_about`

`note_unresolved_topic_gap` only fires AFTER `_answer_topic_reply`'s own
self-heal (answer_about → miss → ground_unknowns → re-answer_about) has
already run once, synchronously, at ingest, and failed. `_process_knowledge_
standing` re-invokes the SAME chain at promotion time — genuine work, not
theatre, because conditions can change between ingest and a human
promoting the gap. Live, both branches:

```
knowledge photosynthesis (no teacher payload available)
  -> knowledge_compose_ok = 0.0
  -> reason: "re-attempted the self-teacher chain (ground_unknowns) on
      'photosynthesis'; the teacher still returned no payload -- still
      ungrounded"
  -> dead comprehension rules installed: 0
  -> SelfConcern.status stays 'promoted' (never falsely resolved)

knowledge photosynthesis (a self-teacher now answers, real payload)
  -> knowledge_compose_ok = 1.0
  -> after run_rules: SelfConcern.status == 'resolved'
```

### 2.2 `self_account` → `domains/self_model.find_self_process`

`self_account` has NO safe existing pipeline value to defer to (measured:
even its rare content-triggered escape routes to the equally-mismatched
ARC `vary`/`gradient` bundle), so the interception is unconditional — the
same shape `code_write`/`prog_read` have. `_process_self_account_standing`
re-checks whether a `SelfProcess` account now exists (one may have been
authored, describing REAL architecture, since the gap was filed — CLAUDE.md's
own changelog names several: collapse, imagining, attending). NEVER
auto-authors one — `run_self_process`'s own docstring forbids fabricating a
self-account, and this module holds to that boundary exactly. Live, both
branches:

```
self_account reasoning (no held SelfProcess)
  -> self_account_compose_ok = 0.0
  -> reason: "no held SelfProcess account exists for 'reasoning' --
      closing this honestly requires a SelfProcess{process, account} node
      describing the REAL mechanism ... never a fabricated one --
      authoring one is an architecture-documentation task"
  -> dead comprehension rules installed: 0
  -> SelfConcern.status stays 'promoted'

self_account collapse (a REAL, seeded SelfProcess -- seeds/self_processes.json)
  -> self_account_compose_ok = 1.0
  -> reason: "a held SelfProcess account for 'collapse' now exists
      (process='collapse') -- the gap is answerable"
  -> after run_rules: SelfConcern.status == 'resolved'
```

### 2.3 `reply_fix` → seed presence (per-tag correspondence table)

Split at the `pipeline` attr `_promote_relations_for_concern` ALREADY
stamps (unmodified): a `reply_fix` concern whose content names acting/seed/
ablation vocabulary already gets `pipeline=="experiment"` and is ALREADY
correctly routed to the conversation-replay composer (live-verified
untouched below) — `_process_reply_fix_standing` is called ONLY on the
`comprehend_first` sub-case, which both real mint-site content tags
(`upload_attachment_reply`/`upload_vision_wiring`) always land in. The
`_REPLY_FIX_NEED` correspondence table (mirroring
`prog_read_growth._BLOCKER_RUST_NEED`):

```
reply_fix upload_attachment_reply (the two named seeds NOT yet loaded)
  -> reply_fix_compose_ok = 1.0
  -> reason: "loaded the missing seed(s) conversation_attachment_route,
      conversation_attachment_reply that this tag's known fix requires"
  -> Seed nodes for both now present
  -> after run_rules: SelfConcern.status == 'resolved'

reply_fix upload_attachment_reply (the two named seeds ALREADY loaded)
  -> reply_fix_compose_ok = 0.0
  -> reason: "... ALREADY present -- the underlying reply gap has some
      OTHER cause, outside this correspondence table"

reply_fix upload_vision_wiring (always)
  -> reply_fix_compose_ok = 0.0
  -> reason: "GraphEye did not run on the specific attachment that filed
      this gap -- nothing in the concern's own text carries the original
      image bytes to re-run vision on ... this is a Rust/adapter-boundary
      limit, not a composable fix"
  -> after run_rules: experiments_exhausted == True, exhausted_note names it

reply_fix "ablate conversation seed and test acting variant" (experiment sub-case)
  -> pipeline == "experiment"
  -> reply_fix_compose_ok NEVER SET -- _process_reply_fix_standing never runs
  -> the genuine author_experiment_from_residual_* rule triple installs,
      exactly as before this rung
```

---

## 3. THE THREE "NO BUG" KINDS — WHAT WAS NOT BUILT, AND WHY THAT IS CORRECT

`instruction`/`performance`/`comprehension` all carry unconditional
membership in `_promote_relations_for_concern`'s `kind in ("self_
improvement", "instruction", "performance", "comprehension")` check —
`or`-ed with the content-keyword test, so kind membership ALONE guarantees
the conversation-experiment relations regardless of content. This was
verified two ways: (1) reading the code — the `or` makes this a structural
guarantee, not a probabilistic one; (2) the live probe (§1) — every tested
content string for these three kinds produced a genuine
`author_experiment_from_residual_*` rule triple, never the dead
comprehension rule. Building a `domains/instruction_growth.py`-shaped
interception for a kind that provably never reaches the buggy path would be
dead code with no path to ever fire — A25's own stated reason for omitting
a `resolve_prog_read_gap` rule, applied here to three whole modules instead
of one rule. `tests/test_ground_concern_six_kinds_migrated.py`'s
parametrized `test_instruction_performance_comprehension_never_reach_the_
generic_fallback` gates this live, for all three, in one test.

---

## 4. REGRESSION — NODE ID LISTS, NOT COUNTS

Fresh worktree, BEFORE any edit (PREREG-only commit,
`git diff main -- domains scripts seeds tests` empty):

```
tests/test_composers_graph.py                             — 0 failed
tests/test_composer_driver_migrated.py                     — 1 failed:
    test_ground_concern_dispatch_parity (pre-existing, provenance-metadata
    drift only — the predecessor RESULTS doc §4 already diagnosed this
    exact node id field-by-field)
tests/test_gap_awareness_migrated.py                        — 0 failed
tests/test_self_concern_promote_migrated.py                 — 0 failed
tests/test_prog_read_selfimprove_migrated.py                — 0 failed
tests/test_prog_synthesis_selfimprove_migrated.py            — 0 failed
tests/test_self_improvement_visibility_migrated.py           — 0 failed
tests/test_self_gaps_surfacing_migrated.py                   — 0 failed
tests/test_attachment_reply_migrated.py                      — 7 failed,
    ALL `ModuleNotFoundError: No module named 'cv2'` (domains/vision_graph.py:57)
    — confirmed pre-existing and environmental: `cv2` is absent from the
    CANONICAL tree too (`python3 -c "import cv2"` fails there identically),
    the documented optional-dep class CLAUDE.md's own retracted-note section
    names. Node ids: test_upload_image_detects_text_presence,
    test_web_default_upload_question_routes,
    test_photo_like_upload_uses_foveated_camera,
    test_image_upload_question_uses_grapheye_vision,
    test_describe_uploaded_image_instruction,
    test_missing_upload_vision_files_gap_then_fixes,
    test_upload_honest_floor_files_reply_fix_gap
tests/test_comprehension_self_optimisation_migrated.py       — 4 failed:
    test_performance_experiment_supported_when_faster_and_clean,
    test_performance_experiment_refuted_on_regression_regardless_of_speed,
    test_promoted_performance_concern_reaches_a_dispatched_experiment,
    test_exhausted_experiments_trail_surfaces_in_status
    — confirmed pre-existing (measured on the vanilla PREREG-only commit,
    before ANY of this rung's code existed). Two are subprocess-dispatch
    judging failures (`performance_judged` never set — an experiment-runner
    environment issue, unrelated to concern-kind routing); two are
    `len(exps)==1` assertions expecting a conversation Experiment to already
    exist after `_concern_tick` alone, without the subsequent `run_rules`
    pass the rule needs to actually fire and mint the node (a pre-existing
    test/rule-timing gap, not something this rung's routing changes touch —
    reproduced identically on the vanilla tree).
```

AFTER all edits (the three growth modules, the daemon routing, the three
seeds, `tests/test_ground_concern_six_kinds_migrated.py`):

```
tests/test_composers_graph.py                             — 0 failed
tests/test_composer_driver_migrated.py                     — 1 failed:
    test_ground_concern_dispatch_parity  (IDENTICAL)
tests/test_gap_awareness_migrated.py                        — 0 failed
tests/test_self_concern_promote_migrated.py                 — 0 failed
tests/test_prog_read_selfimprove_migrated.py                — 0 failed
tests/test_prog_synthesis_selfimprove_migrated.py            — 0 failed
tests/test_self_improvement_visibility_migrated.py           — 0 failed
    (RF-e's own gate: test_reply_fix_defaults_to_comprehend_first_not_arc
    and test_reply_fix_can_include_experiment_when_content_signals_it both
    green, unchanged, confirming _promote_relations_for_concern was never
    touched)
tests/test_self_gaps_surfacing_migrated.py                   — 0 failed
tests/test_attachment_reply_migrated.py                      — 7 failed,
    IDENTICAL node ids, identical cv2 ModuleNotFoundError
tests/test_comprehension_self_optimisation_migrated.py       — 4 failed,
    IDENTICAL node ids
tests/test_ground_concern_six_kinds_migrated.py (NEW)         — 0 failed,
    15 passed (all new gates for this rung)
```

**Combined single run** (composers_graph + composer_driver + gap_awareness +
self_concern_promote + prog_read_selfimprove + prog_synthesis_selfimprove +
self_improvement_visibility + comprehension_self_optimisation +
self_gaps_surfacing + ground_concern_six_kinds): **5 failed, 116 passed** —
the SAME 5 pre-existing node ids (1 composer_driver_parity +
4 comprehension_self_optimisation), zero new failures, plus the 15 new
gates all green.

**Total: identical pre-existing failing node-id sets before and after,
zero new failures anywhere, 15 new gates green.**

---

## 5. EVERYTHING THAT BROKE (process is the result)

1. **`self_account_growth.py`'s first draft had a missing closing `}`** on
   the honest-exhaustion return dict (a `)` was written where `}` was
   needed, since the string itself CONTAINS literal `{process, account}`
   text that reads visually similar to a dict close) — caught immediately
   by the live probe as a `SyntaxError`, fixed before any test ran.
2. **The first `test_knowledge_gap_resolves_when_self_teacher_now_grounds_
   it` draft used the wrong teacher payload shape** (`{"concept": ...}`
   instead of the real `WorldAdapter.learn_from_teacher` contract,
   `{"answer": ..., "learn": [{"phrase": ..., ...}]}`) — caught by the test
   itself failing with the honest "still ungrounded" reason (not a false
   pass), fixed to use the real payload shape so the SUCCESS branch is
   actually exercised.
3. **`test_self_account_never_fabricates_an_account`'s first draft passed a
   bare stub object with no `.nodes()` method** to
   `work_on_self_account_gap`, which internally reads `agent.s` (falling
   back to `agent` itself when `.s` is absent) then calls `.nodes(...)` —
   `AttributeError`, not the intended assertion. Fixed to use the real
   `agent` fixture (which HAS `.s`), since the module's own contract is "a
   WorldAdapter or something exposing `.s`", not "anything at all."
4. **`data`/`results` are gitignored via a trailing-slash pattern
   (`data/`, `results/`) that does NOT match a plain symlink** (confirmed:
   `git check-ignore -v data` / `results` both exit 1, "not ignored") —
   they showed as untracked (`??`) rather than invisible in `git status`.
   Staged explicitly by filename (never `git add -A`/`.`) to avoid
   accidentally committing the symlinks.
5. **The first full regression run's output was accidentally piped through
   `tail -80`** inside a backgrounded `systemd-run` invocation, losing every
   individual test's traceback (only the final summary line survived). Two
   of the twelve baseline failures (`test_attachment_reply_migrated.py`'s
   seven, `test_comprehension_self_optimisation_migrated.py`'s four) had to
   be re-run individually, with output redirected to a file instead of
   piped through `tail`, to get the actual error text and confirm they were
   pre-existing/environmental rather than caused by this rung.

---

## 6. REMAINING UNCERTAINTIES

1. **Root cause of `test_comprehension_self_optimisation_migrated.py`'s two
   `len(exps)==1` failures was not investigated further** — confirmed
   pre-existing (reproduced identically on the vanilla PREREG-only commit)
   and out of this rung's scope (it is a timing/environment property of the
   `performance`/`comprehension` experiment-dispatch tests, not of the
   `knowledge`/`self_account`/`reply_fix` routing this rung built). Whether
   this reflects a real, separate self-improvement-pipeline defect worth
   its own investigation is an open question this rung does not answer.
2. **`_REPLY_FIX_NEED`'s correspondence table has exactly two entries** —
   the two real mint-site tags this tree currently has. A `reply_fix`
   concern authored with different freeform content (the human-feedback
   path, `predicate: "reply_fix"` in
   `tests/test_self_improvement_visibility_migrated.py`'s own fixture)
   falls to the generic fallback reason, honestly, per the module's own
   `_GENERIC_REASON` — widening the table for future named tags is safe and
   additive but was not attempted exhaustively here.
3. **Whether `upload_vision_wiring` could ever close via a DIFFERENT
   mechanism** (e.g. re-ingesting the original upload if its bytes are
   still reachable via some document-store path this rung did not survey)
   was not investigated beyond confirming the concern's own text carries no
   such reference — a narrower, possibly closeable sub-case may exist but
   was not searched for exhaustively.

---

## 7. FILES

| file | what |
|---|---|
| `domains/knowledge_growth.py` | **new** — `work_on_knowledge_gap`, `pending_knowledge_gaps` |
| `domains/self_account_growth.py` | **new** — `work_on_self_account_gap`, `pending_self_account_gaps` |
| `domains/reply_fix_growth.py` | **new** — `work_on_reply_fix_gap` (`_CLOSEABLE_SEEDS`/`_NO_GO_REASON` correspondence), `pending_reply_fix_gaps` |
| `scripts/jabberwock_daemon.py` | +110 lines: `_process_knowledge_standing`/`_process_self_account_standing`/`_process_reply_fix_standing` + three `_concern_tick` routing branches |
| `seeds/knowledge_gap_resolve.json` | **new**, hand-authored (no emitter exists) — `resolve_knowledge_gap` + `note_knowledge_composition_exhausted` |
| `seeds/self_account_gap_resolve.json` | **new**, hand-authored — `resolve_self_account_gap` + `note_self_account_composition_exhausted` |
| `seeds/reply_fix_gap_resolve.json` | **new**, hand-authored — `resolve_reply_fix_gap` + `note_reply_fix_composition_exhausted` |
| `tests/test_ground_concern_six_kinds_migrated.py` | **new**, 15 gates |
| `docs/research/program_synthesis/GROUND_CONCERN_SIX_KINDS_PREREG.md` | this rung's PREREG |
| `docs/research/program_synthesis/GROUND_CONCERN_SIX_KINDS_RESULTS.md` | this file |
| `docs/research/program_synthesis/INDEX.md`, `docs/research/INDEX.md` | updated counts/entries (also backfilled the predecessor's own two missing `GROUND_CONCERN_COMPREHENSION_HONESTY_*` entries, which the prior rung never indexed) |

**Not touched, confirmed by empty diffs:** `domains/reflective_faculty.py`,
`domains/prog_read_growth.py`, `seeds/prog_read_gap.json`,
`seeds/code_write_gap.json`, `seeds/arc_executor.json`,
`seeds/arc_goals.json`, `seeds/arc_magnitude.json`,
`seeds/arc_decompose.json`, `seeds/goal_residuals.json`,
`tools/build_arc_*.py`, `runners/dsl/src/`.

**In this worktree's `git status`, not part of the change:** `data`/
`results` (untracked symlinks into the canonical tree, gitignored by intent
though the symlink form doesn't trip `git check-ignore` — never staged);
`runners/dsl/python/substrate_rs/_native.abi3.so` (copied verbatim, sha
unchanged, not modified).

---

## 8. REPRODUCE

```bash
git worktree add --detach /home/matt/ocelot-ground-concern-six-kinds 6427d54
cd /home/matt/ocelot-ground-concern-six-kinds
git checkout -b ground-concern-six-kinds
ln -s /home/matt/ozmadev/ocelot/data    data
ln -s /home/matt/ozmadev/ocelot/results results
cp /home/matt/ozmadev/ocelot/runners/dsl/python/substrate_rs/_native.abi3.so \
   runners/dsl/python/substrate_rs/_native.abi3.so
touch runners/dsl/python/substrate_rs/_native.abi3.so
sha256sum runners/dsl/python/substrate_rs/_native.abi3.so
#   c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567

OZMA_SEED_PERSIST_DISABLED=1 PYTHONPATH=runners/dsl/python:.:scripts \
  python3 -m pytest tests/test_ground_concern_six_kinds_migrated.py \
    --confcutdir=. -q                        # 15 passed

OZMA_SEED_PERSIST_DISABLED=1 PYTHONPATH=runners/dsl/python:.:scripts \
  python3 -m pytest \
    tests/test_composers_graph.py \
    tests/test_composer_driver_migrated.py \
    tests/test_gap_awareness_migrated.py \
    tests/test_self_concern_promote_migrated.py \
    tests/test_prog_read_selfimprove_migrated.py \
    tests/test_prog_synthesis_selfimprove_migrated.py \
    tests/test_self_improvement_visibility_migrated.py \
    tests/test_comprehension_self_optimisation_migrated.py \
    tests/test_self_gaps_surfacing_migrated.py \
    tests/test_ground_concern_six_kinds_migrated.py \
    --confcutdir=. -q               # 5 failed (all pre-existing) / 116 passed

OZMA_SEED_PERSIST_DISABLED=1 PYTHONPATH=runners/dsl/python:.:scripts \
  python3 -m pytest tests/test_attachment_reply_migrated.py -q
    # 7 failed, all ModuleNotFoundError: No module named 'cv2' (pre-existing,
    # environmental — reproduced identically on the canonical tree)
```
