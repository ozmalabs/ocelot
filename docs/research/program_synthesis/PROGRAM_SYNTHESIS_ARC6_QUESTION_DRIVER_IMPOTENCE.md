# ARC 6 — A23: CANDIDATE (a), BUILT — NOT AS QUESTION_DRIVER, NOT AS A NAIVE `ag_ask` REUSE

**Date:** 2026-08-11/12
**Bars:** `PROGRAM_SYNTHESIS_ARC6_PREREG.md` **amendment A23** (`AR23a`–`AR23d`),
registered **before** this build.
**Base commit:** `c508593` (`main`'s tip at task start; verified before the
worktree was created). Detached worktree
`/home/matt/ocelot-arc6-question-driver-impotence`, branch
`arc6-question-driver-impotence`.
**Engine:** `c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567`
— copied from the canonical tree's committed binary, **the same binary
A17–A22 all measured on**, verified resolving from inside this worktree
(`substrate_rs._native.__file__` is inside
`/home/matt/ocelot-arc6-question-driver-impotence`). Coherence probe passed
before every measurement: `add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})`
reads back `[1,2,3]` and `(1,2,3)` **distinctly**.
**Seed:** `seeds/arc_executor.json` **v1.8.0**, sha256
`f90b4d38eeb74dfb12d2d2611a69c61642b81cc1650e6314940716871cf620ce`, emitted
by `tools/build_arc_executor_seed.py` and gated byte-identical against it
(`--check` passes). `seeds/arc_goals.json` is **byte-identical to `HEAD`**
(sha256 `0aefbb81938212d1da473bce27bbd8bd0a41d870f0e6567104b2f494a1b9f272`,
confirmed by direct diff against the canonical tree) — this rung never
edits `ag_ask`/`tools/build_arc_goals_seed.py`.
**Artifacts:** `results/arc6_question_driver_impotence_ask.json` (AR23c's
own live A/B measurement, two independent full runs, engine + seed
stamped).
**Gate:** the six existing ARC-6 suites (`test_arc_executor_migrated`,
`test_arc_goals_migrated`, `test_goal_residual_migrated`,
`test_arc6_valuelayer_migrated`, `test_arc_magnitude_migrated`,
`test_arc_decompose_migrated`) plus `test_composer_driver_migrated.py` (the
closest thing to a dedicated `question_driver` gate this tree ships — no
`tests/test_question_driver*.py` exists), all measured fresh in this
worktree both **before** any edit and **after** this rung's own build —
**identical failing-node-id lists both times**, plus five new, green,
gated A23 tests (§5).

**SCOPE.** Builds candidate (a) — an impotence-specific question — but
**NOT** as `question_driver.py`'s literal machinery, and **not** as a naive
reuse of `ag_ask`'s own `REGION` fallback. §1 explains why neither of the
two options the task's own brief named is what actually gets built.

---

## 0. VERDICTS

| bar | verdict | what it rests on |
|---|---|---|
| **AR23a — investigation bar: characterize both mechanisms from their rule bodies** | **DONE — and it CORRECTS A22 §6's own prose** | `question_driver.py`'s "gap-guard" (`qd_gap_guard`) is a recursion-DEPTH bound on grounding ONE question's own NL-comprehension gaps (mint-once per `GapSpec`, scoped to one Goal tree's `gap_depth` attr) — it has no notion of "already asked," no cross-epoch persistence, and never inspects a question for its presupposition. "Contrast" (`qd_contrast_compare`) is a SAME/DIFFERENT comparator over two already-grounded `know` children's `genus` attr — it reports agreement between two resolved things, it does not surface an unresolved presupposition. **Neither rule, read from its actual `where`/`effects`, does what A22 §6's prose claimed they do.** `ag_ask`'s own smuggled presupposition is confirmed exactly as A14 finding 3 named it, and sharpened: `REGION(g)` (`tools/build_arc_goals_seed.py:336-338`) falls back to `g.agid`, so `ag_ask`'s own re-entry gate ("one open question per REGION per epoch") is scoped PER GOAL — and A22 §3's own already-measured testimony chain is the live proof that `nearest_unroutable_agid` drifts across THREE distinct goals inside ONE epoch on an UNCHANGED pool. §2 |
| **AR23b — GO/NO-GO on the wiring cost** | **NO-GO for literal `question_driver.py` reuse. GO for a THIRD, native candidate the task's brief did not name.** | Literal reuse needs a new cross-seed dependency (`arc_goals`/`arc_executor` would have to load `question_driving`'s Resolver/Agent-hub apparatus, a first for either seed chain), a second `Goal` node type parallel to `ArcGoal`, and a non-mechanical Python resolver — clears none of A15 EC3's own thresholds, and per AR23a would not even supply a fixed point (the rule bodies that transfer literally don't solve this problem). The candidate that DOES clear an EC3-shaped bar: `ax_ask_impotent`/`ax_ask_impotent_reply`, keyed to the `AgendaVerdict` node's own identity — the SAME mint-once-by-signature SHAPE `ax_impotent` and `gap_awareness.json`'s content-dedup guard already use, native to this seed. Cost: **2 new rules, 1 new edge type, 0 new node types beyond one distinct question type (forced by a bug found live, §4), 0 changes to `ax_dispatch`/`ROUTE`/`ax_impotent`'s own Terms.** §3 |
| **AR23c — the repricing-loop test, done properly** | **CONFIRMED, LIVE, TWIN-RUN DETERMINISTIC.** Native mints **exactly 1** question across a chain where `nearest_unroutable_agid`/`kind` genuinely visits **3 distinct kinds** (`decomposition_tier → supply_blocker → source_claim`, matching A22 §3's own measured sequence exactly) on a pool whose signature is **constant throughout** (confirmed programmatically). A throwaway naive comparator, built ONLY in the measurement script and never shipped, reusing `ag_ask`'s own `REGION`+`asked_epoch` shape verbatim, mints **3** questions on the SAME chain — one per drift, no fixed point. Both counts identical across two independent live runs. §4 |
| **AR23d — no regression** | **PASS.** Identical failing-node-id lists before/after on all seven suites; five new A23 tests green (including the crux live gate, `test_a23_AR23c_native_ask_is_class_scoped_and_reaches_a_fixed_point`). §5 |

**The one thing worth reading if you read nothing else.** A22 §6 named
`question_driver.py`'s gap-guard/contrast rules as "machinery ALREADY BUILT
in this tree for exactly the class of problem `REGION`'s fallback
creates." Reading those rules' actual `where`/`effects` bodies — not their
names — shows this was an over-read: neither rule does anything close to
presupposition-surfacing or content-scoped deduplication. The mechanism
that DOES generalise correctly was already sitting one function away:
`ax_impotent`'s own mint-once-by-pool-signature guard, the exact shape this
arc's own SHAPES-not-numbers standing rule says to look for. Built native,
it reaches a measured fixed point where a naive reuse of `ag_ask`'s own
re-entry gate does not — on the SAME live chain, twin-run identical. A
second, unplanned finding earned its own regression test: reusing
`ArcQuestion` as the new question's node type would have made it silently
answerable by the EXISTING, unmodified testimony-minting rules — accidentally
building candidate (b) (already NO-GO'd by A22) one reply at a time. Caught
live during this rung's own measurement, fixed with a type change, and now
gated so it cannot regress silently.

---

## 1. WHY NEITHER OF THE BRIEF'S TWO NAMED OPTIONS IS WHAT GOT BUILT

The task's own brief, following A22 §6, named two options: literal
`question_driver.py` reuse, or a naive `ag_ask`-shaped reuse (already
flagged as carrying the repricing-loop risk). This rung's own investigation
(§2) found a third: build the SAME class-scoped fixed-point property
`question_driver`'s machinery was supposed to supply, using a mechanism
**already native to `arc_executor`'s own seed** — `ax_impotent`'s own
mint-once-by-pool-signature guard, one level up. Per the task's own
constraints section ("a clean, honest null is a complete and valuable
result... rather than forcing a build that doesn't hold up"), this
deviation is registered as the headline finding, not buried: **the literal
reading of the brief does not survive contact with the actual rule
bodies.**

---

## 2. AR23a — THE INVESTIGATION, GROUNDED IN THE RULE BODIES

### 2.1 `question_driver.py` / `seeds/question_driving.json`, read in full

The kind-dispatch JOIN (`qd_bind_resolver`: a pending leaf `Goal` binds to
whichever `Resolver` shares its `kind`, both hanging off the same `Agent`
hub) is real and does generalise — it is the same JOIN idiom `ax_dispatch`'s
own `ROUTE()` already uses natively inside `arc_executor` (A15 finding 5).
But the two rules A22 §6 named do not do what their names suggest:

- **`qd_gap_guard`** (`seeds/question_driving.json`) mints ONE `"What is
  <X>?"` KNOW subgoal per `GapSpec` while `goal.gap_depth < 1`, guarded by
  `GapSpec.materialized` — mint-once PER SPEC, within ONE gap frame. It is a
  RECURSION-DEPTH BOUND on grounding a single NL comprehension gap
  (replacing the pre-migration `self._gap_depth` Python counter), not a
  cross-question, cross-epoch "don't re-ask this presupposition" guard. Its
  scope is one `Goal` tree's own `gap_depth` attr.
- **`qd_contrast_compare`** compares the `genus` attr of two already-grounded
  `know`-kind children (populated by `know_ground`'s wiki-lookup resolver)
  and writes `"same"`/`"different"`. It is a SAME/DIFFERENT comparator over
  two ALREADY-RESOLVED concepts' held property — it never inspects a
  QUESTION for what it presupposes before asking it.

**Confirmed empirically, not assumed from the names**, per the task's own
explicit instruction: neither rule, as shipped, prevents re-asking about the
same presupposition, and neither surfaces which assumption a question makes.
A22 §6's own prose over-read the two rule names.

### 2.2 The actual "don't re-file the same thing twice" idiom already in this tree

Two places, neither of them `question_driver.py`:

- `seeds/gap_awareness.json`'s content-dedup `where` guard
  (`note_unresolved_topic_gap`/`note_reported_gap`, both keyed by
  `Not(Exists(...))` over `SelfConcern.content` equality) — file a gap only
  if no EQUAL-CONTENT gap already exists, regardless of which utterance
  triggered it.
- `ax_impotent` itself (`tools/build_arc_executor_seed.py`) already ships
  the CLASS-scoped twin of this idiom, natively, for exactly this pool: its
  mint-once guard is keyed by `pool_agids` — the pool's own SIGNATURE — not
  by which goal is `nearest_unroutable_agid` (a field that visibly DRIFTS
  under testimony, A14 §8). A repeated `attach_reply` chain that reweights
  the pool without changing its membership (A14 group 2, A22 §3) never
  causes a second `AgendaVerdict{kind:'impotent'}` to mint, precisely
  because the guard reads the STABLE identity, never whichever goal
  currently ranks first.

### 2.3 `ag_ask`'s own re-entry gate, cross-checked against A22's own measured chain

`ag_ask`'s guard (`tools/build_arc_goals_seed.py:1198-1202`) is
`Not(Exists(ArcQuestion, region==REGION(g), asked_epoch==MEASURE_EPOCH()))`
— "one open question per REGION per epoch." `REGION(g)` (lines 336-338) is
`g.agid` for every unsignatured goal — true of every `supply_blocker`/
`source_claim`/`decomposition_tier` goal this tree has ever minted (A14
finding 1). This re-entry gate is therefore scoped PER GOAL, not per
pool-state or per capability class. A22 §3's own measured testimony chain
(`missing_structural_primitive` tier child → `budget` → `arc6.claim.seam_b…`,
three distinct live winners inside ONE measurement epoch, on ONE unchanged
10-goal pool) is the live proof that `REGION(nearest_unroutable_goal)`
drifts freely within a single epoch as testimony reprices the pool. A naive
impotence-ask keyed the same way `ag_ask` is keyed would have a fresh,
never-before-asked region at EVERY step of that exact already-measured
chain — three impotence-specific questions about what is, by A14's own
headline finding, the SAME unchanged pool state.

### 2.4 The idiom that generalises correctly

This is exactly this arc's own SHAPES-not-numbers standing rule
(`CLAUDE.md`, 2026-08-06/07): the reusable primitive is "guard re-entry by
the STABLE thing (a pool signature / an `AgendaVerdict` node's own
identity), never by whichever specific goal currently wins a drifting
rank" — a shape this tree already has, natively, in the seed this rung
edits. Importing `question_driver.py`'s Goal/Resolver apparatus to get the
SAME shape would mean: a second, disjoint `Goal` node type bridged across
two currently-independent seed dependency closures (`question_driving`'s
own chain has never depended on, and is never depended on by,
`arc_goals`/`arc_executor`), a new Python resolver callable reading
`ArcGoal`/`AgendaVerdict` state (real new logic, not mechanical
translation), and a repurposing of `qd_contrast_compare`'s `genus`-typed
comparison to apply to `sig_seam`/`pool_agids`-typed data it was never
built to read — for a benefit this seed already supplies more cheaply,
natively, in its own idiom.

---

## 3. AR23b — THE COST TABLE

| candidate | cost | verdict |
|---|---|---|
| **(a-literal)** — route through `question_driver.py`'s `qd_bind_resolver`/`qd_gap_guard`/`qd_contrast_compare` bodies | a new cross-seed dependency edge (first for either chain), a `Goal` node type parallel to `ArcGoal`, a non-mechanical Python resolver, a repurposed `genus`-comparison shape applied to data it was never built to read | **NO-GO.** Clears none of A15 EC3's thresholds (`≤2 new seed rules, ≤1 new runner script, no route-matching Term change`); per §2.1 it would not even supply the fixed-point property it was named for. |
| **(a-naive)** — reuse `ag_ask`'s own `REGION` fallback verbatim, retargeted at the impotence verdict | ~1 rule, but inherits the SAME per-goal re-entry gate | **NO-GO on its own registered risk** — measured live to cycle (§4), exactly as predicted. |
| **(a-native)** — `ax_ask_impotent`/`ax_ask_impotent_reply`, keyed to the `AgendaVerdict` node's own identity | **2 new rules, 1 new edge type** (`ArcImpotenceQuestion -asked_about_verdict-> AgendaVerdict`, mirroring the already-shipped `ArcQuestion -asked_about-> ArcGoal`), **1 new node type forced by a bug found live** (§4 — a distinct question type, not `ArcQuestion`), **0 changes** to `ax_dispatch`/`ROUTE()`/`ax_impotent`'s own route-matching or firing-guard Terms | **GO — built.** |

`ax_ask_impotent` mints its class-scoped question the moment a non-stale
`AgendaVerdict{kind:'impotent'}` exists with no question yet asked about
it — `Not(Exists(InNeighbours(av, asked_about_verdict), qi, True)))`, an
edge-existence check, the cheapest guard this engine has. The question text
itself names the presupposition explicitly (per the task's own suggested
framing), not a bare testimony request:

> *"I hold N goals and NONE of them are currently routable. The nearest
> candidate by rank is `<agid>` (kind `<kind>`), but that ranking is over
> the WHOLE POOL, not a property of that one goal alone — other goals of
> the same kind may or may not share this gap. Is the blocker specific to
> `<agid>`, or does it apply to every `<kind>` goal in this pool? Answering
> either way lets me stop re-asking about whichever goal happens to rank
> first without re-litigating the whole class each time it drifts."*

`ax_ask_impotent_reply` marks the question answered on any interlocutor
reply. **Deliberately mints no `GoalResidual`/testimony** — candidate (b)'s
territory (mint-a-capability-goal-adjacent), already NO-GO'd by A22, and
out of this rule's registered scope: this rule only asks a different
question, it never reprices anything. `test_a23_AR23b_the_new_rules_mint_no_
GoalResidual_or_testimony` gates this statically.

`ax_impotent`/`ag_ask`/`ROUTE`/`_routable`/`_dispatchable` are
**BYTE-UNCHANGED** — confirmed by diff, not asserted
(`test_a23_AR23b_every_prior_rule_body_is_UNCHANGED`).

---

## 4. AR23c — THE REPRICING-LOOP TEST, LIVE

### 4.1 A bug found live, not designed in up front

The first version of `ax_ask_impotent` minted its question as an
`ArcQuestion` node. Running AR23c's own measurement immediately surfaced a
real defect: `ag_reply_mints_testimony_conditioned`/`_unconditioned`
(`seeds/arc_goals.json`, untouched by this rung) are generic over
`TypeOf(q)=='ArcQuestion'` — ANY reply to an `ArcQuestion`-typed node mints
testimony, regardless of which rule minted the question. A reply to the
impotence-ask would therefore have SILENTLY minted a `GoalResidual` via the
existing, unmodified machinery — accidentally building candidate (b)
(already NO-GO'd by A22) one reply at a time, defeating the entire "this
rule only asks, it does not reprice" design intent. **Fixed by minting a
distinct node type, `ArcImpotenceQuestion`** — the cheapest discriminator
this engine has (the same shape A15 finding 5 already relies on to keep two
`ExecClass`es from colliding on a shared route, at the TYPE level instead of
the three-part key level). Now gated:
`test_a23_AR23b_the_new_question_type_is_DISTINCT_from_ArcQuestion` reads
both new rules AND `ag_ask`'s own two reply rules fresh and confirms the
type mismatch is real, not assumed.

The measurement script's own throwaway naive comparator needed the SAME
fix for a DIFFERENT reason: minting it as `ArcQuestion` would let it
satisfy `ag_ask`'s OWN re-entry guard by coincidence (since
`nearest_unroutable_goal` IS one of the pool members `ag_ask` itself
ranks), silently suppressing a genuine `ag_ask` tie-question the chain's
own drift depends on. It mints a THIRD, private type
(`ArcImpotenceQuestionNaiveControl`) for this reason — isolated from both
`ArcQuestion` and `ArcImpotenceQuestion`.

### 4.2 The scene: A22's own construction, A14 group-2's own chain mechanism

`scripts/arc6_question_driver_impotence_ask_measure.py` reuses
`arc6_impotence_resweep_measure.py`'s own `boot()`/`drive_decompose()`
functions directly (imported, not reimplemented) to reach the SAME 10-goal
impotent pool A22 §2–§3 already validated (decompose via a REAL horizon
reply, both `re_measure` goals via the SAME validated `headroom_n → 0`
synthetic exit, A13 §7.1), then drives A14 group-2's own mechanism
(repeated unconditioned `attach_reply` against whatever `ag_ask` question is
open) for up to 6 rounds, installing BOTH the shipped native rule (already
active via the `arc_executor` seed) and the throwaway naive comparator
(constructed via `load_seed_manifest` in the script, never written to a
seed file) side by side, watching both.

### 4.3 The result — twin-run identical

```
run1: native=1 naive=3 kinds=['decomposition_tier', 'supply_blocker', 'source_claim', 'source_claim', 'source_claim']
run2: native=1 naive=3 kinds=['decomposition_tier', 'supply_blocker', 'source_claim', 'source_claim', 'source_claim']

VERDICT:
  native_reached_fixed_point: true
  naive_reached_fixed_point:  false
  n_distinct_kinds_in_chain:  3
  prediction_confirmed:       true
```

Per-step trace (run1):

| step | replies sent | live winner kind | native count | naive count |
|---|---|---|---|---|
| reply_0 (boot) | — | `decomposition_tier` | 1 | 1 |
| reply_1 | 1 | `supply_blocker` | 1 | 2 |
| reply_2 | 1 | `source_claim` | 1 | 3 |
| reply_3 | 1 | `source_claim` (fixed) | 1 | 3 |
| reply_4 | 0 (chain ends) | `source_claim` | 1 | 3 |

`pool_signature_constant: true` (confirmed programmatically across every
step) — the SAME headline fact A14/A22 established: testimony reweights the
pool WITHOUT changing its membership. The native rule's own `av` node
therefore never changes across the whole chain, and its mint-once-by-node-
identity guard is satisfied after the FIRST ask and stays satisfied. The
naive rule's `region` changes at every drift (`missing_structural_primitive`
→ `budget` → `arc6.claim.seam_b_signature_39_of_257`), so its guard is
satisfied fresh each time — exactly the repricing-loop risk A14 finding 3
and A22 §6 named, now measured, not merely argued.

**This directly answers the crux question the whole rung was charter for:
routing through `question_driver`'s literal machinery would NOT have fixed
this (§2.1) — reusing the ALREADY-NATIVE mint-once-by-signature shape
does, measured live, twin-run deterministic.**

`test_a23_AR23c_native_ask_is_class_scoped_and_reaches_a_fixed_point`
(`tests/test_arc_executor_migrated.py`) gates the SAME live property as a
standing regression check (asserts at least 3 distinct kinds and exactly 1
native `ArcImpotenceQuestion`, live, on a fresh boot) — not just the
one-off script's committed artifact.

---

## 5. AR23d — REGRESSION, A LIST OF NODE IDS, NEVER A COUNT

Both arms measured in this worktree, on the same engine
(`c5e50801d48a…`), the BEFORE arm measured first before any file was
touched.

| suite | before | after | failing node ids — **identical before and after** |
|---|---|---|---|
| `test_arc_executor_migrated` | 100 passed, 1 failed (101 collected) | 105 passed, 1 failed (106 collected — 5 new A23 tests, all green) | `test_ex1_the_frozen_artifacts_are_STILL_byte_identical` |
| `test_arc_goals_migrated` | 37 / 37 | 37 / 37 | — |
| `test_goal_residual_migrated` | 29 passed, 1 failed, 1 skipped | 29 passed, 1 failed, 1 skipped | `test_gr4_the_live_mbpp_pass_ids_are_unchanged` |
| `test_arc6_valuelayer_migrated` | 35 / 35 | 35 / 35 | — |
| `test_arc_magnitude_migrated` | 43 / 43 | 43 / 43 | — |
| `test_arc_decompose_migrated` | 28 / 28 | 28 / 28 | — |
| `test_composer_driver_migrated` | 5 passed, 2 failed | 5 passed, 2 failed | `test_ground_concern_dispatch_parity`, `test_question_driver_parity` |

The two ARC-6 reds are the same two node ids every prior rung since A12 has
recorded (`results/` is untracked in this checkout; this engine's short sha
is not in `test_gr4`'s allowlist). The two `test_composer_driver_migrated`
reds are PRE-EXISTING on this exact engine/tree combination, confirmed by
running that suite BEFORE any A23 edit — unrelated to `question_driving.json`
(this rung never touches it, confirmed: `git diff --stat HEAD --
seeds/question_driving.json domains/question_driver.py` is empty).

**One test's own pin required updating, per this arc's own standing
precedent (A19→A20→A21 all did the same thing to their predecessor's
identical test).** `test_a21_AR21d_the_new_rules_are_the_ONLY_addition_to_
the_seed` hardcoded `version=='1.7.0'` and the exact 12-rule list — both now
literally false (14 rules, v1.8.0). Per the WH1/A18/A19/A20 precedent this
file already establishes ("INVERTS THIS PIN TO A PREFIX CHECK, NOT
REMOVES IT"), it now asserts the ORIGINAL twelve names are an unbroken
prefix, in order, unedited; `test_a23_AR23b_the_new_rules_are_the_ONLY_
addition_to_the_seed` (§3) is the new full-list-and-version check. This is
not a regression — it is the SAME test-evolution shape every prior
amendment in this file has used, applied a fifth time.

**Confinement, verified not promised.** `git diff --stat HEAD -- seeds/
domains/ tools/ tests/ runners/ scripts/` touches exactly
`seeds/arc_executor.json`, `tools/build_arc_executor_seed.py`,
`tests/test_arc_executor_migrated.py`, and adds
`scripts/arc6_question_driver_impotence_ask_measure.py` — `seeds/arc_goals.json`,
`domains/*`, `seeds/question_driving.json`, `domains/question_driver.py`,
`seeds/goal_residuals.json`, and every other ARC-6 seed are byte-identical
to `HEAD`. The primary tree (`/home/matt/ozmadev/ocelot`) was re-checked
`git status --porcelain` clean after every write in this rung.

---

## 6. EVERYTHING THAT BROKE

Recorded because the process is the result (A11–A22's own standing
practice).

### 6.1 The type-collision bug (§4.1) — the rung's own genuine finding

Not a process hazard — a real design defect this rung's OWN measurement
caught before it shipped. Recorded in full in §4.1. This is the kind of
thing AR23c was registered to catch: building candidate (a) without
accidentally rebuilding candidate (b).

### 6.2 The structural `re_measure` goal does not exist until forced stale

A22 §8.3's own finding, reproduced here: the FIRST draft of the AR23c
measurement script tried `headroom_n → 0`-exiting the structural
`re_measure` goal before its residual condition was ever forced stale — but
that goal's `ArcGoal` node does not exist until the residual actually goes
stale (a real mint-on-condition rule, not a bug). Fixed by forcing
staleness first via the SAME `axe._put_fact(s,
"arc6_structural_ceiling_present", "0")` poke A22's own step 2a used,
mirrored in both the measurement script and the new pytest gate.

### 6.3 An early, over-cautious exclusion masked the chain's own richness

Before the type-collision fix, the measurement script defensively excluded
the impotence-ask's own `ArcQuestion` from ever being replied to (to avoid
leaking into VALUE ranking) — this produced a genuine but SHALLOWER chain
(2 distinct kinds, not 3), because the exclusion was implemented as a
`kind`-attr filter on a shared type rather than as an actual type
separation. Once the type-collision bug was found and fixed (§4.1), the
exclusion became unnecessary — `s.nodes("ArcQuestion")` naturally never
includes the impotence questions once they carry a different type — and
removing the special-case filter let the chain reach A22's own exact
3-kind sequence. Recorded because the FIX for one bug (§4.1) also
dissolved a SEPARATE, self-inflicted measurement artifact (§6.3), not
because the two were the same defect.

### 6.4 Default Bash-tool timeouts, avoided by explicit generous timeouts throughout

Per A12.2/A14 §7.2/A22 §8.2's own standing rule, every suite run in this
rung used an explicit timeout ≥ 480s (the `test_arc_executor_migrated`
suite alone runs ~144s of real subprocess work). No timeout was tripped
this rung — the rule held.

---

## 7. REMAINING UNCERTAINTIES

Ordered by how much damage being wrong would do.

1. **The native rule's re-entry gate has never been exercised across a real
   MEASUREMENT EPOCH ADVANCE** (only within one, via testimony drift) — does
   a genuinely NEW impotent pool state (a different `AgendaVerdict` node,
   different `pool_agids`) correctly get its own fresh ask? This follows
   from the guard's construction (a NEW `av` node has no incoming
   `asked_about_verdict` edge by definition) but was not measured live
   across an actual epoch bump + pool-composition change in this rung.
2. **The naive comparator's own risk was measured on ONE scene (this rung's
   own 10-goal pool), not swept across A14/A22's full scene catalogue** —
   mirroring A22 §9 uncertainty #1's own honest caveat about IC3's own
   single-scene basis, one level further down. The measured cycling (3
   asks, no fixed point within the scope of THIS chain) is real, not a
   worst case; a longer or differently-ordered chain might cycle further or
   less.
3. **The impotence-ask's question text is a single, fixed template** — it
   does not vary by `nearest_unroutable_kind`'s own semantics (e.g. a
   `decomposition_tier` goal's "class" is its siblings under the same
   `parent_agid`, a `supply_blocker`'s "class" is every goal of that
   `kind`) — the text says "every `<kind>` goal in this pool," which is
   honest but coarser than the `decomposition_tier` case's own natural
   sibling relation. Not fixed here — out of AR23c's own scope, which was
   the fixed-point property, not the question's semantic precision.
4. **Whether a human answering this question in production would actually
   supply information that changes anything** is unmeasured — this rung
   deliberately built ONLY the ask side (no testimony minted from a reply),
   per AR23b's own scope discipline. What a genuine answer should DO once
   the ask side works is a separate, larger question this rung does not
   answer.
5. **`question_driver.py`'s own kind-dispatch JOIN idiom (`qd_bind_resolver`)
   was read and found reusable in SHAPE (§2.1) but was not itself exercised
   or tested by this rung** — the finding is about the two specific rules
   A22 §6 named, not a claim that nothing in `question_driver.py` ever
   generalises to a different domain.

---

## 8. FILES

| file | what |
|---|---|
| `tools/build_arc_executor_seed.py` | v1.8.0 — two new rules (`ax_ask_impotent`, `ax_ask_impotent_reply`), one new edge production, `IN_()` helper (InNeighbours) |
| `seeds/arc_executor.json` | regenerated, byte-gated against the builder |
| `tests/test_arc_executor_migrated.py` | five new A23 tests (§3, §4.1, §4.3); `test_a21_...` inverted to a prefix check per this file's own standing precedent |
| `scripts/arc6_question_driver_impotence_ask_measure.py` | NEW — the AR23c A/B measurement: native vs. a throwaway naive comparator, never shipped |
| `results/arc6_question_driver_impotence_ask.json` | NEW — its artifact, engine + seed stamped, two independent runs |
| `PROGRAM_SYNTHESIS_ARC6_PREREG.md` | amendment A23 appended, registered before this build |
| `PROGRAM_SYNTHESIS_ARC6_QUESTION_DRIVER_IMPOTENCE.md` | this file |

**Nothing else changed.** `seeds/arc_goals.json`, `seeds/question_driving.json`,
`domains/question_driver.py`, `seeds/goal_residuals.json`, and every other
seed/adapter in this tree are byte-identical to `HEAD`.
`runners/dsl/python/substrate_rs/_native.abi3.so` is byte-identical to the
canonical tree's committed binary (only its mtime was touched to clear the
git-worktree false-staleness refusal). `data` and `results` are untracked
symlinks into the canonical tree (gitignored), not staged.

---

## 9. REPRODUCE

```bash
# --- the worktree ---------------------------------------------------------
git worktree add --detach /home/matt/ocelot-arc6-question-driver-impotence c508593
cd /home/matt/ocelot-arc6-question-driver-impotence
git checkout -b arc6-question-driver-impotence
ln -s /home/matt/ozmadev/ocelot/data    data
ln -s /home/matt/ozmadev/ocelot/results results

# --- the engine -------------------------------------------------------------
cp /home/matt/ozmadev/ocelot/runners/dsl/python/substrate_rs/_native.abi3.so \
   runners/dsl/python/substrate_rs/_native.abi3.so
touch runners/dsl/python/substrate_rs/_native.abi3.so
sha256sum runners/dsl/python/substrate_rs/_native.abi3.so
#   c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567

# --- the coherence probe.  STOP if these read back the same. ---------------
PYTHONPATH=runners/dsl/python:. python3 -c "
import substrate_rs as srs; s=srs.Substrate()
a=s.node(s.add_node('T',{'lst':[1,2,3],'tup':(1,2,3)}))['attrs']
print(a['lst'], a['tup'], a['lst']!=a['tup'])"

# --- regenerate the seed ----------------------------------------------------
python3 tools/build_arc_executor_seed.py

# --- the six existing gate suites + the composer/driver suite -- ALWAYS an
#     explicit generous timeout: this bench contains a REAL ~140s fixture.
for s in test_arc_goals_migrated test_goal_residual_migrated \
         test_arc6_valuelayer_migrated test_arc_magnitude_migrated \
         test_arc_decompose_migrated test_composer_driver_migrated; do
  COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
    PYTHONPATH=runners/dsl/python:. timeout 480 \
    python3 -m pytest tests/$s.py --confcutdir=$PWD -q -p no:randomly -rf
done
COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  PYTHONPATH=runners/dsl/python:. timeout 480 \
  python3 -m pytest tests/test_arc_executor_migrated.py --confcutdir=$PWD -q -p no:randomly -rf

# --- the AR23c A/B measurement (cheap: ~0.15s total, two full runs) --------
COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  PYTHONPATH=runners/dsl/python:. timeout 280 \
  python3 scripts/arc6_question_driver_impotence_ask_measure.py
#   -> results/arc6_question_driver_impotence_ask.json
```

**Engine provenance.** Every number in this document was produced by
`c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567`, resolving
from inside `/home/matt/ocelot-arc6-question-driver-impotence`.

**Contamination.** No test-split data of any kind is read by this rung's
own new code — the AR23c measurement is pure graph mutation + rule
firing, no MBPP battery invoked (the `test_arc_executor_migrated.py`
suite's own pre-existing `~144s` fixture is the ONLY thing in this rung
that touches it, and it is unmodified). Nothing entered a codebook, a cue
table, or a route table beyond the two new rules and one new edge type
themselves.
