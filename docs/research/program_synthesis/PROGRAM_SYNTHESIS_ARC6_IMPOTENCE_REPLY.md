# ARC 6 — A24: THE REPLY SIDE — CLASS-SCOPED, NOT A `gr_move_penalty` REUSE, BECAUSE IT STRUCTURALLY CANNOT BE

**Date:** 2026-08-11
**Bars:** `PROGRAM_SYNTHESIS_ARC6_PREREG.md` **amendment A24** (`AR24a`–`AR24d`),
registered **before** this build.
**Base commit:** `003a121` (`main`'s tip at task start; verified before the
worktree was created — the merge commit for A23). Detached worktree
`/home/matt/ocelot-arc6-impotence-reply`, branch `arc6-impotence-reply`.
**Engine:** `c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567`
— copied from the canonical tree's committed binary, **the same binary
A17–A23 all measured on**, verified resolving from inside this worktree.
Coherence probe passed before every measurement:
`add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` reads back `[1,2,3]` and
`(1,2,3)` **distinctly**.
**Seed:** `seeds/arc_executor.json` **v1.9.0**, sha256
`009531752212b12914d03f579bdb644116bbf28652298eab64eaaac1453ecf0b`,
emitted by `tools/build_arc_executor_seed.py` and gated byte-identical
against it (`--check` passes). `seeds/arc_goals.json`,
`seeds/goal_residuals.json`, `seeds/program_synthesis.json` are
**byte-identical to `HEAD`** (confirmed by direct diff, gated by
`test_a24_AR24b_gr_move_penalty_MATCH_PENALTY_and_AG2_VALUE_are_UNTOUCHED`)
— this rung never edits `gr_move_penalty`, `ag_ask`, or AG-2's `VALUE`.
**Gate:** the six standing ARC-6 suites (`test_arc_executor_migrated`,
`test_arc_goals_migrated`, `test_goal_residual_migrated`,
`test_arc6_valuelayer_migrated`, `test_arc_magnitude_migrated`,
`test_arc_decompose_migrated`), all measured fresh in this worktree both
**before** any edit and **after** this rung's own build — **identical
failing-node-id lists both times** — plus ten new, green, gated A24 tests
in `test_arc_executor_migrated.py` (§5).

**SCOPE.** Closes the two cheapest of A23 §7's three ranked remaining
uncertainties: the reply mechanism (§7 item 4) and the epoch-advance
re-entry test (§7 item 1). Item 2 (the naive comparator's own risk swept
across A14/A22's full scene catalogue) is **explicitly not attempted** —
named and left open, per this task's own instruction.

---

## 0. VERDICTS

| bar | verdict | what it rests on |
|---|---|---|
| **AR24a — design investigation: does `gr_move_penalty` apply to the reply?** | **NO — and not merely at the wrong grain. STRUCTURALLY INERT on its own target population.** `MATCH`'s first, non-wildcardable conjunct (`tools/build_goal_residual_seed.py:122-124`) refuses ANY candidate with a null `sig_seam`, unconditionally. Every goal this pool has ever named `nearest_unroutable_kind` (`decomposition_tier`/`supply_blocker`/`source_claim`, A23 §2.3/§4.2, already measured) is exactly the unsignatured population that guard exists to exclude. A `GoalResidual` minted off an impotence reply would be unreadable by `PENALTY()` for every candidate this pool can ever contain — not a mis-scoped reuse, an inert one. §2 |
| **AR24b — build the reply mechanism, minimal, seed-data-first** | **DONE.** One new rule (`ax_ask_impotent_testify`), one new node type (`ArcImpotenceTestimony`, class-scoped by `kind`), one new edge type (`mints_testimony`) + one new production triple reusing the existing `holds_under` edge type. **Zero changes** to `gr_move_penalty`/`MATCH`/`PENALTY`/AG-2's `VALUE`/`ax_ask_impotent`/`ax_ask_impotent_reply` — all confirmed byte-identical to `HEAD` by diff. **No weight field** — per CLAUDE.md's SHAPES-not-numbers standing rule, nothing downstream reads a class-scoped testimony weight yet, so none is authored. §3 |
| **AR24c — the epoch-advance test, live, twin-run deterministic** | **CONFIRMED.** A genuinely new `AgendaVerdict` (different `pool_agids`, reached via a real `agi.bump_measure_epoch` call, not graph churn inside one epoch) gets its OWN fresh `ArcImpotenceQuestion` — the old, already-answered question is untouched and still targets the old, now-stale verdict; the new question is open and targets the new, fresh verdict. Twin-run byte-identical. §4 |
| **AR24d — no regression** | **PASS.** Identical failing-node-id lists before/after on all six suites; ten new A24 tests green. §5 |

**The one thing worth reading if you read nothing else.** The task's own
brief speculated the reply should "reweight the pool… mirroring how
`ag_ask`'s existing testimony mechanism reweights via `gr_move_penalty`."
Reading `gr_move_penalty`'s own `MATCH` term shows this is not just the
wrong grain (per-goal vs. per-class, the brief's own framing) — the
impotent pool's own population is, by this arc's own already-measured
fact (A14 finding 1 / A23 §2.3), *exactly* the unsignatured set `MATCH`'s
first conjunct was built to refuse. A `GoalResidual` minted here would sit
on the graph forever unread, by construction, for every candidate this
pool has ever contained or ever will while it stays unsignatured. The
mechanism this rung ships instead is class-scoped by `kind` — the SAME
dimension A23 already chose for the ask itself — and deliberately carries
no numeric weight, because nothing reads one: an honest, minimal record,
not a fabricated numeric knob standing in for a consumer that does not
exist yet.

---

## 1. WHY THE BRIEF'S OWN SPECULATION DOES NOT SURVIVE CONTACT WITH THE CODE

The task's brief posed the design question directly and asked it to be
answered from the code, not assumed: does the reply reweight via
`gr_move_penalty` (cheap, reuses existing machinery), or does A23's own
class-scoped design mean something structurally different is needed? The
brief's own hedge — "if `gr_move_penalty`'s naive reuse would reintroduce
the single-goal-scoped smuggled presupposition A23 was built to avoid" —
undersold the actual finding. Reading `MATCH` in full (§2 below) shows the
naive path is not merely a re-introduction of a scoping bug; it produces a
node the engine can never read back for this pool's population, at all,
regardless of how the residual's own dimensions are set.

---

## 2. AR24a — THE INVESTIGATION, GROUNDED IN THE RULE BODIES

### 2.1 `gr_move_penalty`'s own `MATCH`/`PENALTY`, read in full

`tools/build_goal_residual_seed.py:116-146`:

```python
def MATCH(r, c):
    items = [
        NOT(EQ(A(r, "stale"), L(1.0))),
        NOT(EQ(A(c, "sig_seam"), L(None))),        # <-- the candidate itself
    ]
    for dim in SIG_DIMS:                            #     must carry sig_seam
        items.append(OR(EQ(A(r, dim), L(None)), EQ(A(r, dim), A(c, dim))))
    return AND(*items)
```

The module's own comment names this on purpose: *"a candidate with NO
`sig_seam` is never matched, so an all-wildcard residual cannot suppress
an unsignatured goal."* `seeds/arc_goals.json`'s own AG-2 comment restates
the same fact as a documented escape hatch: *"An ArcGoal with no
`sig_seam` cannot be matched by ANY `GoalResidual`... so it escapes."*
This is a deliberate, already-shipped design property of the existing
mechanism — not a bug this rung gets to route around, and not something a
residual's own wildcard dimensions can defeat, because the guard on the
CANDIDATE side is checked before any of the residual's own `SIG_DIMS`
comparisons are even reached.

### 2.2 Which goals the impotent pool can actually name

A23 §2.3, quoting `REGION(g)` (`tools/build_arc_goals_seed.py:336-338`):
the fallback to `g.agid` fires *"whenever `sig_seam` is unset — true of
every `supply_blocker`/`source_claim`/`decomposition_tier` goal this tree
has ever minted."* A23 §4.2's own live measurement is not a hypothesis
about this — it is the reproduced trace: the whole
`nearest_unroutable_kind` chain AR23c drove visited exactly
`decomposition_tier → supply_blocker → source_claim`, the three kinds
that are always unsignatured. Confirmed again, freshly, in this rung's own
live scenes (§4 below): every `ArcImpotenceQuestion.region` this worktree
minted was one of those three kinds, never a signatured one.

### 2.3 The consequence, stated precisely

A `GoalResidual` minted off an `ArcImpotenceQuestion` reply — even with
`sig_seam` set to some improvised class token on the RESIDUAL side —
would still fail `MATCH`'s first conjunct for every candidate `c` in this
pool, because `c.sig_seam` is null for all of them. This is stronger than
"wrong grain" (a per-goal mechanism applied where a per-class one
belongs, the framing the brief itself offered as the alternative
hypothesis): it is **inert by construction** — a node the engine's own
`PENALTY()` term can never read back for this population, full stop,
independent of how carefully the residual's own dimensions are chosen.
Building it anyway would be graph data with no possible reader, the
inverse of the SHAPES-not-numbers standing rule's own complaint about
scalar knobs nobody consumes, applied one level down (a *record* nobody
can consume, rather than a *number* nobody consumes — same shape,
different noun).

### 2.4 What the reply mechanism should be instead

A23 already chose the correct class key for this population:
`AgendaVerdict.nearest_unroutable_kind`, copied onto
`ArcImpotenceQuestion.region` at ask time. Unlike `sig_seam`, `kind` is a
plain string every pool member — signatured or not — actually carries.
Building the reply mechanism around `kind` equality is therefore:

- **Structurally sound** for the exact population that can trigger it
  (the impotent pool, by definition, is the only place
  `ArcImpotenceQuestion`s come from).
- **Additive, not a rule-shape change to shared machinery.** `MATCH`/
  `PENALTY`/AG-2's `VALUE` are read by `ps_move_select`
  (`program_synthesis.json`), AG-2 itself (`arc_goals.json`), and
  `ag_ask`'s own `EXISTS_MATCH` guard — three already-measured,
  unrelated properties. Extending `MATCH` to accept a `kind`-keyed
  wildcard path (so it could apply to unsignatured goals) would be a
  change to a Term three seeds depend on, exactly the kind of blast
  radius A15's EC2/EC3 cost discipline (reaffirmed by A23's own AR23b)
  weighs against when a small, additive alternative exists.

---

## 3. AR24b — THE BUILD

### 3.1 The cost table, counted the way A23's AR23b counted it

| item | count | detail |
|---|---|---|
| new rules | **1** | `ax_ask_impotent_testify` |
| new node types | **1** | `ArcImpotenceTestimony` |
| new edge types | **1** | `mints_testimony` (`ArcImpotenceQuestion -> ArcImpotenceTestimony`) |
| new productions on an EXISTING edge type | **1** | `holds_under` (`ArcImpotenceTestimony -> ResidualCondition`) — the edge TYPE already exists (`AgendaVerdict -> ResidualCondition`); this is a new (src-type, edge-type, tgt-type) triple, riding `gr_condition_lapse`'s own type-agnostic match for free |
| changes to `gr_move_penalty`/`MATCH`/`PENALTY` | **0** | confirmed byte-identical to `HEAD` |
| changes to AG-2's `VALUE`, `ag_ask` | **0** | confirmed byte-identical to `HEAD` |
| changes to `ax_ask_impotent`/`ax_ask_impotent_reply` | **0** | confirmed byte-identical to `HEAD` — A23's own "this rule only asks, it does not reprice" statement about `ax_ask_impotent_reply` stays literally true |
| weight/numeric fields on the new node | **0** | deliberate — §2.3/§ investigation finding 5 in the amendment |

### 3.2 The rule, `ax_ask_impotent_testify`

Matched on the SAME `[m, responds_to, q]` pattern
`ax_ask_impotent_reply` already uses, guarded by
`TypeOf(q)=='ArcImpotenceQuestion'` (so it cannot fire on an ordinary
`ag_ask` value-tie reply) and a self-extinguishing edge-existence check
(`Not(Exists(Neigh(q, mints_testimony)))` — the same cheapest-guard shape
`ax_ask_impotent`'s own re-entry gate uses one level up). It mints:

```
ArcImpotenceTestimony{
    kind:          <- q.region        (nearest_unroutable_kind at ask time)
    agid_a:        <- q.agid_a        (which goal was nearest-ranked at ask time — descriptive only)
    scope:         <- m.impotence_scope, or "unspecified" if absent
    asked_epoch:   <- q.asked_epoch
    reply_epoch:   <- MEASURE_EPOCH() at reply time
    evidence_kind: "utterance"
    reach_class:   "testimony"
    stale:         0.0
}
```

`scope` is a structured field the reply's own `Message` node carries,
set the SAME way `cond_kind` already is on
`ag_reply_mints_testimony_conditioned` — that rule's own design note is
explicit: *"the reply's structured condition fields are written by the
world adapter as MECHANICAL TRANSLATION of an external form... the reply
text is never parsed into a signature."* This rung follows the identical
discipline: `domains/arc_goal_ingest.py` (the sibling seed's own protected
adapter) is untouched, and the field is set directly on the `Message`
node in the test/measurement code that plays the adapter's role, exactly
as `_leave_pool_without_retiring`, `_put_fact`, and every other scene-
construction helper in this test file already do.

The new node lapses through the EXISTING, `gr_condition_lapse`/
`gr_condition_hold` (`seeds/goal_residuals.json`, untouched — its `match`
carries no type constraint on the node it lapses, confirmed live in §3.3
below), via a `holds_under` edge to a `fact_equals(arc_measure_epoch)`
`ResidualCondition` — the SAME "expires at the next measurement" idiom
every other testimony in this tree already ships. Zero new lapse
mechanism.

### 3.3 Live confirmation, before the formal test suite

Run directly against a fresh boot, ad hoc, before writing the gated
tests:

```
scope defaults:    'unspecified' when the reply carries no structured field
scope, structured: 'class' when m.impotence_scope='class' is set — carried verbatim
mint-once:         re-running run_rules() after the first mint does NOT double-mint
lapse:             stale: 0.0 -> 1.0 the instant agi.bump_measure_epoch() advances
                   the epoch, with ZERO code changed in gr_condition_lapse
```

All four gated formally in §5 (`test_a24_AR24b_LIVE_*`).

---

## 4. AR24c — THE EPOCH-ADVANCE TEST, LIVE

### 4.1 The scene

A23's own IM1 pool-exit idiom (`_leave_pool_without_retiring`), applied
twice, with a REAL epoch advance between them:

1. Boot; drop `AGID` (the one routable kind) from the pool via
   `headroom_n -> 0`. `ax_impotent` mints `av1`; `ax_ask_impotent` asks
   `q1` about it (`q1 -asked_about_verdict-> av1`).
2. Answer `q1` (`agi.attach_reply`). `ax_ask_impotent_reply` marks it
   answered; `ax_ask_impotent_testify` mints its testimony (unrelated to
   this test's own crux, exercised by §3's own tests).
3. Drop a SECOND, distinct goal (`_SECOND_AGID`) from the pool the same
   way, AND call `agi.bump_measure_epoch(s)` — the SAME mechanical call
   `run_order`/`world_probe_advance_epoch` already make in production —
   so the new state is reached by a genuine measurement-epoch advance,
   not merely by graph churn inside one epoch (the case A23 §4 already
   covered live).
4. `run_rules()` to fixpoint.

### 4.2 The result — measured, not assumed from the guard's construction

```
n_verdicts:            2   (av1: pool_agids P1, stale=1.0 after the epoch bump;
                             av2: pool_agids P2 != P1, stale=0.0, fresh)
n_questions:            2   (q1: answered=1.0, targets av1, UNCHANGED by the epoch bump;
                             q2: answered=0.0, status='open', targets av2)
q1's own target:        av1   (untouched — this rung never revisits an answered question)
q2's own target:        av2   (a GENUINELY NEW question, for the GENUINELY NEW verdict)
targets distinct:       True  (the two questions do not collide on one verdict)
```

**The re-entry gate's per-node `InNeighbours(av, asked_about_verdict)`
check does exactly what its construction predicts**: a brand-new
`AgendaVerdict` node has no incoming `asked_about_verdict` edge by
definition, regardless of how many OTHER verdicts already carry one.
A23 §7 item 1 named this as reasoned-but-unmeasured; it is now measured,
live, across a real epoch boundary, not merely inside one (A23's own
AR23c scene never advanced the epoch — its whole point was that testimony
reprices the SAME pool without an epoch bump). Twin-run: the scene was
built and measured twice independently; `n_questions`, `n_verdicts`, the
sorted `answered` flags, the sorted `pool_agids`, and the sorted `stale`
flags were compared field-by-field and were identical both times.

### 4.3 Why this could plausibly have failed, and didn't

A prior, wrongly-designed reply mechanism (one that gated
`ax_ask_impotent`'s own firing on whether ANY testimony existed for a
`kind`, considered and rejected in the amendment's own design
investigation — see `PROGRAM_SYNTHESIS_ARC6_PREREG.md` amendment A24 §
investigation finding 5) would have put exactly this property at risk:
if `q1`'s reply had suppressed future asks about `supply_blocker`-kind
verdicts in general, `av2` (also `supply_blocker`, per this scene's own
construction) would never have gotten `q2`. Because
`ax_ask_impotent_testify` mints a purely descriptive record with no
consumer anywhere in this tree (§3.1), it cannot interfere with
`ax_ask_impotent`'s own firing guard — confirmed here, not merely argued.

---

## 5. AR24d — REGRESSION, A LIST OF NODE IDS, NEVER A COUNT

Both arms measured in this worktree, on the same engine
(`c5e50801d48a…`), the BEFORE arm measured first before any file was
touched (after recovering from a `Bash`-tool default-timeout SIGKILL
during the first, over-cautious attempt at the BEFORE run — see §6.1).

| suite | before | after | failing node ids — **identical before and after** |
|---|---|---|---|
| `test_arc_executor_migrated` | 105 passed, 1 failed | 115 passed, 1 failed (10 new A24 tests, all green) | `test_ex1_the_frozen_artifacts_are_STILL_byte_identical` |
| `test_arc_goals_migrated` | 37 / 37 | 37 / 37 | — |
| `test_goal_residual_migrated` | 29 passed, 1 failed, 1 skipped | 29 passed, 1 failed, 1 skipped | `test_gr4_the_live_mbpp_pass_ids_are_unchanged` |
| `test_arc6_valuelayer_migrated` | 35 / 35 | 35 / 35 | — |
| `test_arc_magnitude_migrated` | 43 / 43 | 43 / 43 | — |
| `test_arc_decompose_migrated` | 28 / 28 | 28 / 28 | — |

Both reds are the SAME two node ids A23 §5 already recorded, for the
SAME reasons: `test_ex1_the_frozen_artifacts_are_STILL_byte_identical`
compares `results/arc6_verdict_before.json` (an untracked, gitignored
artifact) against `git show HEAD:...`, which is empty by construction in
any checkout — a pre-existing, environment-conditional red, not something
this rung's engine or seed changed. `test_gr4_the_live_mbpp_pass_ids_are_
unchanged` fails because this engine's short sha
(`c5e50801d48a`) is not in that test's own hard-coded allowlist — the
SAME allowlist gap A22 §7 and A23 §5 both already flagged for their own
build of this identical binary. Neither is new to this rung.

**One test's own pin required updating, per this arc's own standing
precedent (A19→A20→A21→A23 all did the same thing to their
predecessor's identical test).**
`test_a23_AR23b_the_new_rules_are_the_ONLY_addition_to_the_seed`
hardcoded `version=='1.8.0'` and the exact 14-rule list — both now
literally false (15 rules, v1.9.0). Per the WH1/A18/A19/A20/A23 precedent
this file already establishes, it now asserts the ORIGINAL fourteen
names are an unbroken prefix, in order, unedited;
`test_a24_AR24b_the_new_rule_is_the_ONLY_addition_to_the_seed` is the new
full-list-and-version check.

**Confinement, verified not promised.** `git diff --stat` against
`003a121` touches exactly `docs/research/program_synthesis/
PROGRAM_SYNTHESIS_ARC6_PREREG.md`, `seeds/arc_executor.json`,
`tests/test_arc_executor_migrated.py`, and
`tools/build_arc_executor_seed.py` — `seeds/arc_goals.json`,
`seeds/goal_residuals.json`, `seeds/program_synthesis.json`,
`domains/arc_goal_ingest.py`, `domains/goal_residual_ingest.py`,
`domains/arc_magnitude_ingest.py`, `domains/arc_executor.py`, and every
other ARC-6 seed/adapter are byte-identical to `HEAD`
(`test_a24_AR24b_gr_move_penalty_MATCH_PENALTY_and_AG2_VALUE_are_
UNTOUCHED`). The primary tree (`/home/matt/ozmadev/ocelot`) was
re-checked `git status --porcelain` clean after every write in this
rung.

---

## 6. EVERYTHING THAT BROKE

### 6.1 The exact timeout hazard the task brief warned about, hit on the first try

The very first BEFORE-baseline measurement attempt used the `Bash` tool's
default two-minute timeout instead of an explicit generous one (an
oversight, not a deliberate test of the warning). It was SIGKILLed mid-way
through `test_ex1`'s own `live_run` fixture, inside
`arc6_remeasure_row_verdict.py`'s protected-file swap window — before its
`finally` block (which cannot run under `SIGKILL`) restored
`seeds/program_synthesis.json`. Recovery, exactly per the task's own
protocol: `git status --porcelain` in the worktree showed
`seeds/program_synthesis.json` modified (the primary tree was confirmed
clean throughout — the mutation is worktree-local, `results/`/`data`
being symlinks into the primary tree did not propagate a git-visible
change there); `PYTHONPATH=... python3 scripts/arc6_verdict_patch.py
status` read back `patched` where it should have read `baseline`,
confirming the runner's own state-detection (which reads the seed file
directly, not a separate stash) agreed with the git diff. `git checkout
-- seeds/program_synthesis.json` restored it byte-for-byte; `status`
immediately read back `baseline` again. No `/tmp` crash-stash was needed
— `arc6_remeasure_row_verdict.py`'s own `tempfile.mkdtemp` stash from the
killed run was leaked (never `rmtree`'d, since that too is in the
unreachable `finally`) but was not needed for recovery, since `git
checkout` alone was sufficient for the one tracked file the runner
protects that actually diverged. Every subsequent measurement in this
rung used an explicit `timeout 480`+ at both the shell-command level and
the `Bash`-tool level, per the task's own instruction, and none tripped
it again (the live suite's own real runtime measured at 206.5s this
rung, consistent with A23's own 144s-plus figure on a possibly busier
host).

### 6.2 A scratch test draft left dead scaffolding, caught before commit

An early draft of `test_a24_AR24c_a_genuinely_new_verdict_after_a_real_
epoch_bump_gets_its_own_fresh_ask` accumulated unused local variables
(`import_s`, a `statuses` comprehension) while the test was being
iterated live against the actual scene output. Caught on re-reading
before the suite was run for the gate — removed; the final version
contains only assertions that read graph state and check it, no dead
code. Recorded because the process is the result (A11–A23's own standing
practice).

---

## 7. REMAINING UNCERTAINTIES

Ordered by how much damage being wrong would do.

1. **The naive comparator's own risk was never swept across A14/A22's
   full scene catalogue** (A23 §7 item 2, explicitly not attempted here,
   per this task's own scope boundary) — still open, still a bigger,
   separate measurement task.
2. **`ArcImpotenceTestimony` has no reader anywhere in this tree.** This
   is a deliberate, argued design choice (§2.3, § investigation finding
   5 in the amendment: no weight without a consumer), not an oversight —
   but it means the reply mechanism this rung built is, today, purely
   observational. Whether and how a future rung should wire it into
   AG-2's `VALUE`, into `ax_ask_impotent`'s own re-entry guard, or into a
   render/query surface a human could inspect ("what have you learned
   about `supply_blocker` goals") is unanswered and was explicitly kept
   out of scope by both the amendment and this build, mirroring A23's
   own deferral of "what should a genuine answer DO" one level down.
3. **`scope` is a two/three-way open string (`"specific"`, `"class"`,
   `"unspecified"`), not a closed, validated vocabulary.** Nothing in
   this rung enforces that a reply's `impotence_scope` field is one of a
   known set — a world adapter that writes an arbitrary string would be
   silently accepted and carried through verbatim. Given there is no
   reader yet (uncertainty 2), this has no live consequence today, but a
   future consumer would need to decide whether to validate it.
4. **The epoch-advance test (§4) exercises exactly one shape of "genuine
   epoch advance"** — a SECOND goal leaving the pool, combined with an
   explicit `bump_measure_epoch` call. It does not test the OTHER
   epoch-advance path this tree already has
   (`world_probe_advance_epoch`, A18's own second, narrower epoch
   producer that never runs anything) against the SAME re-entry-gate
   property. Given the gate reads a plain node-identity edge check with
   no epoch-specific logic in it at all, this is not expected to matter,
   but it was not separately measured.
5. **The testimony's `agid_a` field is descriptive only, copied from the
   question at ask time, and can go stale relative to the LIVE
   `nearest_unroutable_agid` the instant testimony re-prices the pool
   (A22's own already-measured drift).** This mirrors
   `ArcImpotenceQuestion.agid_a`'s own already-accepted staleness (A23
   §3 names it "DESCRIPTIVE ONLY," never read by any firing guard) —
   not a new risk this rung introduces, but worth naming again at the
   testimony grain specifically, since a future reader might be tempted
   to treat `agid_a` as current rather than as-of-ask-time.

---

## 8. FILES

| file | what |
|---|---|
| `tools/build_arc_executor_seed.py` | v1.9.0 — one new rule (`ax_ask_impotent_testify`), one new node type, one new edge type + one new production triple |
| `seeds/arc_executor.json` | regenerated, byte-gated against the builder |
| `tests/test_arc_executor_migrated.py` | ten new A24 tests (§3.3, §4, confinement); `test_a23_AR23b_the_new_rules_are_the_ONLY_addition_to_the_seed` inverted to a prefix check per this file's own standing precedent |
| `PROGRAM_SYNTHESIS_ARC6_PREREG.md` | amendment A24 appended, registered before this build |
| `PROGRAM_SYNTHESIS_ARC6_IMPOTENCE_REPLY.md` | this file |

**Nothing else changed.** `seeds/arc_goals.json`,
`seeds/goal_residuals.json`, `seeds/program_synthesis.json`,
`domains/arc_goal_ingest.py`, `domains/goal_residual_ingest.py`,
`domains/arc_magnitude_ingest.py`, `domains/arc_executor.py`, and every
other seed/adapter in this tree are byte-identical to `HEAD`.
`runners/dsl/python/substrate_rs/_native.abi3.so` is byte-identical to
the canonical tree's committed binary (only its mtime was touched to
clear the git-worktree false-staleness refusal). `data` and `results`
are untracked symlinks into the canonical tree (gitignored), not staged.

---

## 9. REPRODUCE

```bash
# --- the worktree ---------------------------------------------------------
git worktree add --detach /home/matt/ocelot-arc6-impotence-reply 003a121
cd /home/matt/ocelot-arc6-impotence-reply
git checkout -b arc6-impotence-reply
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

# --- the six existing gate suites -- ALWAYS an explicit generous timeout:
#     this bench contains a REAL ~200s fixture (test_ex1's live_run).
for s in test_arc_executor_migrated test_arc_goals_migrated \
         test_goal_residual_migrated test_arc6_valuelayer_migrated \
         test_arc_magnitude_migrated test_arc_decompose_migrated; do
  COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
    PYTHONPATH=runners/dsl/python:. timeout 480 \
    python3 -m pytest tests/$s.py --confcutdir=$PWD -q -p no:randomly -rf
done

# --- just the new A24 tests (cheap: well under a second) -------------------
COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  PYTHONPATH=runners/dsl/python:. timeout 120 \
  python3 -m pytest tests/test_arc_executor_migrated.py -k a24 \
  --confcutdir=$PWD -q -p no:randomly -rf
```

**Engine provenance.** Every number in this document was produced by
`c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567`,
resolving from inside `/home/matt/ocelot-arc6-impotence-reply`.

**Contamination.** No test-split data of any kind is read by this rung's
own new code — `ax_ask_impotent_testify` is pure graph mutation + rule
firing, no MBPP battery invoked. The `test_arc_executor_migrated.py`
suite's own pre-existing `~200s` `live_run` fixture is the ONLY thing in
this rung that touches the battery, and it is unmodified (it was also the
source of the recovered timeout contamination in §6.1, which is fully
resolved and does not affect any reported result).
