# `ground_concern`'s comprehension composer, Path 2 — PREREGISTRATION for the six remaining concern kinds

**Date:** 2026-08-12.
**Predecessor:** `GROUND_CONCERN_COMPREHENSION_HONESTY_PREREG.md` /
`GROUND_CONCERN_COMPREHENSION_HONESTY_RESULTS.md` (this directory,
`main`'s tip at the time this rung started, `6427d54`). That investigation's
§5 named two honest paths to close the measured bug and explicitly
recommended the second:

> **Path 2 — Per-caller opt-in at the promotion layer**, mirroring A25's own
> fix exactly: give every concern KIND that currently falls through to the
> generic `comprehend_first`/`ground_concern` path (not just `prog_read`)
> its own dedicated routing check BEFORE it reaches the shared composer —
> the same shape `code_write` and `prog_read` already have. This doesn't
> touch the shared function at all... it closes the false-success-plus-
> dead-rule bug at every OTHER site named in §2's `_concern_tick` row
> (reply_fix, knowledge, self_account, instruction, performance,
> comprehension kinds) without needing a discriminator inside
> `_compose_comprehension_rule` at all.

**Template:** `PROGRAM_SYNTHESIS_ARC6_PROGREAD_SELFIMPROVE.md` (amendment
A25) — `domains/prog_read_growth.py` + `_process_prog_read_standing` +
`seeds/prog_read_gap.json`'s hand-authored `note_prog_read_composition_
exhausted` rule. This rung repeats that SHAPE, not its content, six times
(one investigation + decision per kind), and is explicitly instructed NOT
to force a uniform fix where the evidence doesn't support one.

**Constraint carried forward, unchanged:** `domains/reflective_faculty.py`'s
`_compose_comprehension_rule` is NOT touched in this rung. Every fix here
routes AROUND it, at the daemon's promotion/tick layer, exactly as Path 2
specifies.

**Worktree:** `/home/matt/ocelot-ground-concern-six-kinds`, branch
`ground-concern-six-kinds`, base commit `6427d54`.
**Engine:** `c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567`
(copied from the canonical tree, `runners/dsl/python/substrate_rs/_native.abi3.so`),
verified resolving from inside the worktree. Coherence probe passed:
`add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` reads back `[1,2,3]` and
`(1,2,3)` distinctly (both `list`/`tuple` typed).

---

## 0. A LIVE MEASUREMENT THAT SHAPES EVERY BAR BELOW

Before writing bars, this rung ran a live probe (mirroring the predecessor
investigation's own §1.2 methodology — real `WorldAdapter`, real
`load_all_seeds`, no mocks) feeding each of the six kinds REALISTIC content
(mirroring each kind's actual mint-site content shape) through
`jabberwock_daemon.promote_self_concern` and, for the relations it stamped,
directly through `reflective_faculty.induce_concern`/`ground_concern` (what
`_concern_tick`'s generic branch does today). The result reclassifies the
"six kinds" framing precisely:

| kind | `_promote_relations_for_concern` pipeline (measured) | composer reached | verdict |
|---|---|---|---|
| `knowledge` | `comprehend_first` (content is a bare topic word; essentially never trips `_content_suggests_experiment`) | `compose_comprehension_rule` → **the dead `describe_scene` rule, `grounded:true`** | **BUG CONFIRMED LIVE — needs a fix** |
| `self_account` | `comprehend_first` (content is a stripped faculty noun like "reasoning"; almost never trips the signal set, and even when it does, the ELSE branch of `_promote_relations_for_concern` — the ARC `vary`/`gradient` bundle — is ALSO the wrong shape for a self-account question) | `compose_comprehension_rule` (or, on the rare signal-hit, the ARC self-improvement composer — equally mismatched) | **BUG CONFIRMED LIVE — needs a fix, AND has no safe existing pipeline value to defer to (unlike reply_fix/knowledge)** |
| `reply_fix` | `comprehend_first` when content doesn't name acting/seed/ablation vocabulary (measured true for both real mint-site contents in this tree, `upload_attachment_reply` / `upload_vision_wiring`); `experiment` when it does | `compose_comprehension_rule` (dead rule) on the `comprehend_first` branch; `compose_experiment_rule` (genuine, live-verified) on the `experiment` branch | **BUG CONFIRMED LIVE on the `comprehend_first` branch only — needs a fix scoped to that branch; the `experiment` branch is ALREADY safe and must not be touched** |
| `instruction` | **ALWAYS `experiment`** — `kind in ("self_improvement","instruction","performance","comprehension")` is an unconditional `or`-branch in `_promote_relations_for_concern`, true regardless of content | `compose_experiment_rule` — live-verified: mints a genuine `author_experiment_from_residual_*`/`judge_experiment_outcome_*`/`mark_adopt_ready_*` rule triple AND a real `cue_variant` (reads the unrouted verb, proposes a `comprehend_text` route) | **NO BUG — never reaches the generic comprehend-first fallback, by construction** |
| `performance` | **ALWAYS `experiment`** (same unconditional membership) | `compose_experiment_rule` — live-verified genuine (reply_variant honestly walls on no-overlap, not a lie) | **NO BUG — same as `instruction`** |
| `comprehension` | **ALWAYS `experiment`** (same unconditional membership) | `compose_experiment_rule` — live-verified genuine | **NO BUG — same as `instruction`** |

**This measurement, not reasoning alone, sets this rung's bars.** The task
brief's framing ("six kinds... currently fall through to the generic
fallback") is the predecessor investigation's own §2 table entry, which is
true in the conditional sense it stated ("whenever they don't qualify for
the experiment bundle") — but three of the six kinds (`instruction`,
`performance`, `comprehension`) NEVER fail to qualify, by a structural `or`
in the promotion code, not by chance of content. Reporting them as
"needing a fix" would be inventing work the measurement does not support;
this PREREG registers the true population instead: **three kinds need a
routing fix (`knowledge`, `self_account`, `reply_fix`); three are already
correctly wired and this rung's job for them is to prove that live and stop
(no code change).**

---

## 1. PER-KIND BARS

### 1.1 `knowledge`

- **KN-a — mint site.** `seeds/gap_awareness.json::note_unresolved_topic_gap`
  fires when an `answer_topic` Goal's `outcome=='unresolved'` — i.e. AFTER
  `world_adapter._answer_topic_reply`'s own self-heal (`answer_about` →
  miss → `ground_unknowns` → re-`answer_about`) has ALREADY been tried once,
  synchronously, at ingest time, and failed. `content` = the bare topic
  word/phrase (the Goal's `concept` attr).
- **KN-b — existing mechanism.** YES: `WorldAdapter.ground_unknowns` (the
  self-teacher chain) + `WorldAdapter.answer_about`, already documented in
  `CLAUDE.md`'s "Knowledge gaps self-heal" section. This rung does not
  invent a new grounding mechanism — it re-invokes the SAME one, later, at
  promotion time, when conditions may have changed (a human taught
  something related in the interim; the self-teacher's own backing source
  may now answer where it didn't before).
- **KN-c — GO/NO-GO.** GO on a routing fix that stops the dead rule and
  re-attempts the existing mechanism, honestly recording either genuine
  resolution or a specific re-attempt failure.
- **KN-d — live demonstration required.** Promoting a `knowledge` concern
  no longer installs `comprehend_describe_directive_*`; the StandingConcern
  carries `knowledge_compose_ok`/`knowledge_compose_reason`; a genuinely
  groundable topic resolves the original `SelfConcern` via a seed rule
  reading that outcome (mirroring `resolve_code_write_gap`); an
  ungroundable one honestly exhausts (mirroring
  `note_prog_read_composition_exhausted`).
- **KN-e — regression.** No change to `_promote_relations_for_concern`'s
  existing `comprehend_first`/`experiment` split for `knowledge` (untouched,
  so `_content_suggests_experiment`'s existing behaviour for `knowledge` is
  preserved byte-for-byte); the fix intercepts ONLY the `comprehend_first`
  sub-case in `_concern_tick`.

### 1.2 `self_account`

- **SA-a — mint site.** `seeds/gap_awareness.json::note_self_account_gap`
  fires when a self-reflexive question about a faculty resolves NO held
  account (`self_account_unresolved==1.0` on the Message). `content` =
  `self_account_topic` (a possessive-stripped faculty noun/phrase, e.g.
  "reasoning", "imagination").
- **SA-b — existing mechanism.** YES: `SelfProcess` nodes +
  `domains/self_model.py::find_self_process`/`run_self_process`, documented
  in `CLAUDE.md`'s "self_processes" section — "only faculties with NO held
  account still file a self_account gap." Re-checking `find_self_process`
  at promotion time is the correct existing-mechanism reuse: a `SelfProcess`
  account may have been taught for this faculty SINCE the gap was filed
  (architecture documentation grows over time, per the same section's own
  changelog of newly-accounted faculties).
- **SA-c — GO/NO-GO.** GO on the routing fix (unconditional interception —
  measured, §0: `self_account` has no safe existing pipeline value to defer
  to, unlike `reply_fix`/`knowledge`). NO-GO, precisely, on ever
  auto-authoring a genuine new `SelfProcess` account from the seed/adapter
  grain — an account's `note` prose must describe REAL architecture (the
  collapse loop, the sd loop, the adapter's ingest path); synthesizing one
  mechanically would be exactly the kind of fabricated self-account
  `CLAUDE.md`'s own `run_self_process` docstring explicitly forbids
  ("never fabricates").
- **SA-d — live demonstration required.** Promoting a `self_account`
  concern for an unaccounted faculty (e.g. "reasoning", confirmed
  unaccounted per `CLAUDE.md`'s own self_processes section) no longer
  installs the dead rule; records an honest, specific exhaustion reason
  naming the missing `SelfProcess` account. If a `SelfProcess` for the
  topic already exists (a faculty CLAUDE.md documents as accounted, e.g.
  "collapse"), the routing fix recognises it and resolves the concern
  instead of exhausting — both branches demonstrated live.
- **SA-e — regression.** `_promote_relations_for_concern` untouched.

### 1.3 `reply_fix`

- **RF-a — mint sites.** Two, both `seeds/gap_awareness.json`:
  `note_upload_reply_gap` (content `upload_attachment_reply`, fires when
  the honest floor answers an upload question — measured in
  `tests/test_attachment_reply_migrated.py::test_upload_honest_floor_files_reply_fix_gap`
  to correspond to the `conversation_attachment_route`/
  `conversation_attachment_reply` seeds being unloaded) and
  `note_upload_vision_gap` (content `upload_vision_wiring`, fires when an
  image attachment lacks `vision_summary` at ingest — GraphEye did not run
  on THIS attachment).
- **RF-b — existing mechanism.** SPLIT, per content tag (this is why RF is
  NOT a uniform fix within itself either): (1) `upload_attachment_reply` —
  YES, an existing mechanism: loading the two named seeds
  (`conversation_attachment_route`/`conversation_attachment_reply`) is a
  real, mechanical, already-demonstrated close (the SAME test above proves
  it by hand). (2) `upload_vision_wiring` — NO existing seed/adapter-level
  close: the gap is that GraphEye did not run on a SPECIFIC already-ingested
  attachment; nothing at promotion time can re-run vision on image bytes
  the concern's text does not carry. Also — for BOTH tags — when the
  concern's own content coincidentally names acting/seed/ablation
  vocabulary, `_promote_relations_for_concern` ALREADY routes it correctly
  to the conversation-replay `experiment` composer (live-verified, §0);
  that branch must be left alone.
- **RF-c — GO/NO-GO.** GO on a routing fix scoped to the `comprehend_first`
  sub-case only (discriminated by the StandingConcern's own already-stamped
  `pipeline` attr — a graph fact, not a new decision), which: closes
  `upload_attachment_reply` by ensuring the two named seeds are loaded (and
  reports whether that constituted real NEW progress or the seeds were
  already present, in which case the true cause is something else and
  the concern honestly exhausts); honestly exhausts `upload_vision_wiring`
  every time, naming precisely why (Rust/adapter boundary — no attachment
  bytes reachable from the concern's text); honestly exhausts anything
  outside the two known tags (no correspondence).
- **RF-d — live demonstration required.** Both branches shown live: a
  synthetic `upload_attachment_reply` concern on an agent that has NOT
  loaded the two named seeds gets them loaded and the concern resolves (or,
  if already loaded, exhausts honestly); a synthetic `upload_vision_wiring`
  concern always exhausts, naming the reason.
- **RF-e — regression.** `test_reply_fix_defaults_to_comprehend_first_not_arc`
  and `test_reply_fix_can_include_experiment_when_content_signals_it`
  (`tests/test_self_improvement_visibility_migrated.py`) must stay green
  UNCHANGED — this is the concrete evidence that `_promote_relations_for_
  concern`'s existing conditional split for `reply_fix` is untouched by
  this rung (checked BEFORE any edit, as the baseline these two tests
  already encode).

### 1.4 `instruction`, `performance`, `comprehension`

- **IPC-a — mint sites.** `instruction`: `seeds/gap_awareness.json`'s
  unrouted-verb rule (content = "`<predicate> <content>`"). `performance`/
  `comprehension`: `seeds/comprehension_health.json`'s
  `note_comprehension_latency_gap`/`note_recurring_speech_act_divergence`.
- **IPC-b — existing mechanism.** YES, already CORRECTLY WIRED (§0):
  `_promote_relations_for_concern`'s unconditional `kind in (...)`
  membership routes every concern of these three kinds to the
  conversation-replay `experiment` composer, never to
  `compose_comprehension_rule`. Live-verified this rung (§0 table): a
  genuine `cue_variant` was built for an `instruction` concern (proposing a
  route for the unrouted verb "elaborate"); `performance`/`comprehension`
  concerns produced a genuine `author_experiment_from_residual_*`
  rule-triple with an honestly-walled `reply_variant` (no overlapping reply
  rule — an honest abstention, not a lie).
- **IPC-c — GO/NO-GO.** **NO-GO on building anything for these three** —
  there is no bug to close. Building a dedicated pre-interception module
  for a kind that already avoids the generic fallback by construction would
  be dead code with no path to ever change behaviour (the A25 precedent's
  own discipline: "a resolve rule would be dead code with no path to ever
  fire; the absence is named here rather than filled with speculative
  graph data" — applied here to an entire module, not one rule).
- **IPC-d — what this rung DOES do for these three.** Records the live
  measurement (§0) as the demonstration bar — proof, not assertion, that
  no fix is needed — and leaves ZERO code changes touching their path.
- **IPC-e — regression.** N/A (nothing touched).

---

## 2. REGRESSION SCOPE (aggregate, in addition to the per-kind bars above)

Per-kind pass/fail as NODE ID LISTS, never counts, gathered BEFORE any edit
(fresh worktree baseline) and AFTER:

- `tests/test_composers_graph.py`
- `tests/test_composer_driver_migrated.py`
- `tests/test_gap_awareness_migrated.py`
- `tests/test_self_concern_promote_migrated.py`
- `tests/test_prog_read_selfimprove_migrated.py`
- `tests/test_prog_synthesis_selfimprove_migrated.py`
- `tests/test_self_improvement_visibility_migrated.py` (RF-e's own gate)
- `tests/test_attachment_reply_migrated.py` (RF's own mint-site gate)
- `tests/test_comprehension_self_optimisation_migrated.py` (IPC's own gate)
- `tests/test_self_gaps_surfacing_migrated.py`
- any new `tests/test_ground_concern_six_kinds_migrated.py` (this rung's own
  gate, new)

---

## 3. WHAT THIS RUNG WILL NOT DO

- Will not touch `domains/reflective_faculty.py`'s `_compose_comprehension_rule`.
- Will not touch `domains/prog_read_growth.py`, `seeds/prog_read_gap.json`,
  `seeds/code_write_gap.json`'s existing content, `seeds/arc_*`,
  `seeds/goal_residuals.json`, `tools/build_arc_*.py`, `runners/dsl/src/`.
- Will not widen `_promote_relations_for_concern`'s existing conditional
  logic for ANY kind — every fix here is a `_concern_tick`-layer
  interception, reading already-computed graph facts (`kind`, `pipeline`),
  mirroring `code_write`/`prog_read`'s exact shape.
- Will not force a uniform build across all six kinds — §0's measurement
  already rules that out for three of them.
