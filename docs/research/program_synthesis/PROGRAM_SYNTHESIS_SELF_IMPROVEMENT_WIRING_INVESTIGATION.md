# Program synthesis and the self-improvement pipeline — is the gap-awareness claim in `docs/features/program-synthesis.md` actually true, end to end?

**Purpose.** `docs/features/program-synthesis.md` (lines 42-43) makes a specific
architectural claim: when the synthesis loop cannot build a program, it "gap
(files a `SelfConcern`, closing the human-gated self-improvement loop described
in `CLAUDE.md`'s gap-awareness section)." This is the same claim CLAUDE.md
makes for the conversation domain ("THE AGENT FINDS ITS OWN GAPS") and its
graph-native self-repair extension ("THE AGENT FIXES ITSELF WHERE IT IS
GRAPH-NATIVE"), applied to a domain — program synthesis — those sections were
never checked against. This document verifies the claim directly against code:
does synthesis failure actually mint a `SelfConcern`; can that node actually
reach `StandingConcern` and the `Experiment`→judge→adopt spine; has this ever
happened on a real boot; and is the separately-built ARC6 `ArcGoal`/
`ax_impotent` machinery the same mechanism, a parallel one, or something else.
No code is changed by this document — read-only investigation, one file added.

**Scope discipline, stated up front.** This note verifies the specific claim
above against the code as of `main`'s tip (`003a121`). It does not evaluate
whether the program-synthesis arc's other claims (the P0→P7 trajectory table,
the ARC6 amendments) are correctly measured — those are out of scope except
where they bear on gap-filing specifically.

---

## 0. The honest answer, up front

**The claim is true, but narrower than a reader would assume, and the narrowing
matters.** Program synthesis failure genuinely mints a `SelfConcern` in the
*exact* node shape (`status`, `source`, `kind`, `content`) that CLAUDE.md's
gap-awareness section documents, and that node genuinely reaches
`StandingConcern{status:'pending'}` through the *same* human-gated
`promote_self_concern` function every conversation-domain concern uses
(`seeds/program_synthesis.json:5209-5358`, `ps_gap_file`, minting
`SelfConcern{kind:'code_write', ...}` — the identical shape
`seeds/code_write_gap.json`'s own `note_code_write_gap` mints, verified
end-to-end live in `tests/test_prog_synthesis_selfimprove_migrated.py:138-205`,
a real `WorldAdapter` boot running real `run_rules` fixpoints, not a mock).
**But the downstream closure is not the `Experiment`→judge→adopt spine
CLAUDE.md documents for conversation concerns — it is a second, parallel,
domain-specific synchronous mechanism** (`_process_code_write_standing` →
`code_write_growth.work_on_code_write_gap`, `scripts/jabberwock_daemon.py:2472-2506`)
that the daemon's `_concern_tick` routes to *instead of*
`induce_concern`/`ground_concern` whenever a `StandingConcern`'s `kind` equals
`code_write` (`scripts/jabberwock_daemon.py:2525-2528`) — the generic
Experiment-minting composer is never invoked for this kind, by an explicit
`if` branch, not an oversight. This is closer to scenario **(c)** than to
"fully wired" **(d)**: the promote hand-off is real and general, but what
receives a promoted program-synthesis concern is a bespoke pipeline built
specifically for `code_write`, not the `Experiment`/adopt machinery the
architectural claim's own wording ("closing... the self-improvement loop") most
naturally reads as referring to. A second, sibling gap kind the same pipeline
files (`prog_read`, blocked-read capability gaps — `seeds/prog_read_gap.json`)
mints and surfaces correctly but **has never been exercised through promotion
by any test**, and reading the promotion code shows it would fall through to a
generic `comprehend_first` default relation set
(`scripts/jabberwock_daemon.py:2122-2128`) that has no structural connection to
extending a reading frame — an honest, load-bearing residual named precisely
in §4 below. A third population — the decomposition-tier-2/3/4 blockers and the
dormant `arc6_import_impedance` survey the task brief named — **is never
represented as a `SelfConcern` at all**; it exists only as `ArcGoal`/
`GoalResidual` graph structure in a *different* subsystem and as prose in
`docs/research/program_synthesis/`, confirmed by a repo-wide search (§5). And
`ArcGoal`/`ax_impotent` (the ARC6 goal-pool-impotence machinery) is
**demonstrably a different mechanism serving a different purpose** — it detects
a stuck *dispatch/scheduling* loop over a competing goal pool and asks a human
a testimony-shaped question about *that*, never mints or reads a `SelfConcern`,
and has only a one-directional, cost-penalized ingestion bridge *from*
`SelfConcern` (§5) — not a substitute for gap-awareness and not redundant with
it.

---

## 1. The actual "gap" step in the program-synthesis pipeline

**`ps_gap_file` (`seeds/program_synthesis.json:5208-5359`) is the rule.** It
fires on `["ag", "has_goal", "g"]` where `g.kind=='synth_program'` and
`g.status=='gapped'` (lines 5222-5250), guarded against re-filing
(`ps_gap_filed` mint-once, lines 5251-5268) and against duplicate content
(`Not(Exists(SelfConcern, content==g.request))`, lines 5269-5298) and scoped to
top-level goals only (`Not(Gte(ps_depth, 1.0))`, lines 5299-5317 — a descent
sub-goal's hole failing is descent-internal working state, not a standalone
concern, per the rule's own comment at line 5210). Its effect (lines
5319-5358):

```json
["add_node", "sc", "SelfConcern", {
  "status": "noted",
  "source": "implicit",
  "kind": "code_write",
  "content": {"__term__": {"type": "Attr", "node": {"type": "Var", "name": "g"}, "key": "request"}}
}],
["add_edge", "ag", "has_self_concern", "sc"],
["add_edge", "sc", "about_goal", "g"]
```

The rule's own comment (line 5210) states the shape choice explicitly: *"the
EXACT node shape `seeds/code_write_gap.json` mints, so the surfacing reader and
the human-gated promote spine find it with zero new plumbing."* Comparing
directly against `seeds/code_write_gap.json:33-79`'s `note_code_write_gap`
effect — `SelfConcern{status:'noted', source:'implicit', kind:'code_write',
content:<request text>}` — the shapes are attr-for-attr identical, and
`seeds/gap_awareness.json:15`'s own description (the mechanism CLAUDE.md's
"THE AGENT FINDS ITS OWN GAPS" section documents) confirms this is the *same*
node shape `note_unresolved_topic_gap`/`note_reported_gap` mint for the
conversation domain. So: **yes, unambiguously — synthesis failure mints a real
`SelfConcern`, in the confirmed-real shape.**

One adjacent finding worth naming precisely: `ps_gap_file` always mints
`kind:'code_write'`, never a synthesis-specific kind (no `kind:'synth_program'`
or similar exists anywhere in `seeds/program_synthesis.json`). This is a
deliberate reuse, not an oversight — the same file's rule comment (line 5210)
calls it "the code_write_gap.json node shape verbatim" — but it means every
`ps_gap_file`-filed concern is downstream-indistinguishable from a gap filed
by an ordinary chat write-request that never touched the synthesis
codebook/lattice/enumerate ladder at all (`seeds/code_write_gap.json`'s own
`note_code_write_gap`, fired from `world_adapter.converse`'s
`_write_function_reply`). Both paths converge on one shared gap population.

A second, sibling gap kind exists for a different failure mode:
`seeds/prog_read_gap.json:14-188`'s `note_prog_read_gap` fires when an
uploaded source file's read is blocked (an unsupported AST construct — Lambda,
varargs — confirmed live in `tests/test_prog_read_gap_migrated.py:108-150`),
mints `SelfConcern{status:'noted', source:'implicit', kind:'prog_read',
content:'<frame> read blocked: <blockers>'}` (lines 121-166), again the
identical shape. So the program-synthesis domain files gaps through **two**
kinds, `code_write` (synthesis-failure and NL write-request-failure, unified)
and `prog_read` (blocked-read capability gaps), both real graph rules, neither
a Python decision — the adapter (`domains/prog_synthesis.py`,
`domains/file_ingest.py`) only records facts (`code_write_outcome`,
`read_blocked`, `read_blockers`) per CLAUDE.md's adapter-mechanical-I/O
discipline; every quoted rule above is what decides a gap should be filed.

---

## 2. Can the filed `SelfConcern` actually reach `StandingConcern` and the `Experiment`/adopt spine?

**The promote function is domain-general and does admit `kind:'code_write'` —
it never rejects it.** `promote_self_concern`
(`scripts/jabberwock_daemon.py:2131-2201`) takes any `SelfConcern` node id,
reads its `kind`/`content` (lines 2151-2152) with no gate that would refuse an
unrecognised or program-synthesis-shaped kind, and unconditionally mints a
`StandingConcern{status:'pending', kind:<the concern's kind>, about:<content>,
relations:<...>, pipeline:<...>}` (lines 2159-2167) plus a `promoted_to` edge
(line 2168). This is confirmed live: `tests/test_prog_synthesis_selfimprove_migrated.py:158-167`
calls `jd.promote_self_concern(a, str(scs[0]["id"]))` on a real `kind:'code_write'`
concern and asserts a real `StandingConcern{status:'pending', kind:'code_write',
about:REQ}` results. **So the hand-off half of the claim is real, tested, and
general — this is not a hard-coded conversation-domain-only gate.**

**But which `relations`/`pipeline` get attached — and therefore what happens
next — is decided by `_promote_relations_for_concern`
(`scripts/jabberwock_daemon.py:2040-2128`), and it *does* special-case
`code_write` explicitly, routing it away from the generic composer entirely:**

```python
if kind == "code_write":
    # ... _concern_tick routes a StandingConcern of this kind
    # DIRECTLY into domains.code_write_growth.work_on_code_write_gap
    # (see _process_code_write_standing below). These relations are
    # descriptive graph data (never read by induce_concern for this
    # kind) ...
    relations = [["compose", "SHAPE", "from", "PREDICATION"]]
    ...
    return relations, "code_write"
```
(`scripts/jabberwock_daemon.py:2078-2086`, comment and code both quoted
verbatim). Every *other* recognised `kind` (`self_improvement`, `instruction`,
`performance`, `comprehension`, `reply_fix`, `knowledge`, `reported`) gets a
`relations` bundle containing `["test", "HYPOTHESIS", ...]` /
`["adopt", "WINNER", "as", "SELF"]` (lines 2098-2124) — the vocabulary
`induce_concern` reads to author an `Experiment`. `code_write` deliberately
never gets that bundle.

**The dispatcher enforces the same split.** `_concern_tick`
(`scripts/jabberwock_daemon.py:2509-2545`) is the daemon hook that processes
every `pending` `StandingConcern`:

```python
if at.get("kind") == "code_write":
    _process_code_write_standing(adapter, n, at)
    s.set_attr(n, "status", "processed")
    continue
relations = at.get("relations") or []
_ensure_world_for_relations(adapter, relations)
name = at.get("name") or f"standing_concern_{_nid_value(n)}"
ind = rf.induce_concern(adapter, relations, name_hint=name)
if ind.get("minted") and ind.get("capability_key"):
    rf.ground_concern(adapter, [ind["capability_key"]])
s.set_attr(n, "status", "processed")
```
(lines 2524-2534). `rf.induce_concern`/`rf.ground_concern`
(`domains/reflective_faculty.py:1268`, `:6407`) are precisely the functions
that mint `Experiment{status:'requested', hypothesis, game}` nodes
(`domains/reflective_faculty.py:4382`) and later mark adoption
(`:4634-4654`) — **the Experiment→judge→adopt spine CLAUDE.md documents.**
`code_write`-kind `StandingConcern`s never reach this branch — the `continue`
on line 2527 skips it unconditionally. Instead, `_process_code_write_standing`
(`scripts/jabberwock_daemon.py:2472-2506`) calls
`code_write_growth.work_on_code_write_gap` (`domains/code_write_growth.py:387-418`)
directly — a **synchronous, non-`Experiment` compose-then-teach attempt**
(`compose_write_shape_from_predication`, and on failure, an honest pointer to
teach-by-example) — and records a mechanical outcome fact
(`code_write_compose_ok`/`code_write_compose_reason`) that
`seeds/code_write_gap.json`'s `note_code_write_composition_exhausted` rule
(lines 167-201) reads to decide exhaustion, never touching `Experiment` at any
point in the chain. `tests/test_prog_synthesis_selfimprove_migrated.py:171`
asserts this explicitly and by name: `assert a.s.nodes("Experiment") == []`
after promotion, with the comment *"SCOPE HONESTY: the hand-off IS the
demonstration — promotion mints the pending StandingConcern and NOTHING else
runs here (no Experiment is dispatched)"*.

**Verdict for point 2:** `promote_self_concern` itself is domain-general and
does not exclude program-synthesis concerns. But the `Experiment`/adopt spine
specifically is bypassed by design for `code_write` — a **different, working,
independently-tested pipeline** exists in its place. Whether that pipeline is
"the self-improvement loop described in CLAUDE.md's gap-awareness section"
depends on how literally that phrase is read: it *is* the same
`SelfConcern`→human-gate→`StandingConcern` shape gap-awareness defines; it is
*not* the `Experiment`/adopt machinery a reader familiar with the conversation
domain's concerns (`reply_fix`, `knowledge`, `instruction`) would likely
picture. `docs/features/program-synthesis.md`'s own wording (lines 42-43) is
narrow enough to be technically accurate — it names "the human-gated
self-improvement loop," not the Experiment spine specifically — but a reader
relying on CLAUDE.md's framing of that loop (which foregrounds
`Experiment`→judge→adopt) would form a wrong mental model without this
investigation's §2.

**`prog_read` is the harder case, and it is untested.** `kind:'prog_read'`
matches *none* of the special-cased branches in `_promote_relations_for_concern`
— not `code_write` (line 2078), not the `want_experiment` set
(`self_improvement`/`instruction`/`performance`/`comprehension`, line 2092),
not the conversation-replay subset (`reply_fix`/`knowledge`/`instruction`/
`performance`/`comprehension`/`reported`, lines 2102-2103). It therefore falls
through to the unconditional default (lines 2125-2128):

```python
relations = [["comprehend", "DIRECTIVE", "mint", "GOAL"]]
for w in content_words[:4]:
    relations.append([w, "TARGET", "of", "SELF"])
return relations, "comprehend_first"
```

which, per `_concern_tick`'s branch structure above, routes into the *generic*
`induce_concern`/`ground_concern` path (the `Experiment` spine) — not the
`code_write` bypass. This is structurally odd: `["comprehend", "DIRECTIVE",
"mint", "GOAL"]` is the relation shape meant for a conversation-comprehension
fix (per the function's own docstring at lines 2075-2077: "reply_fix/knowledge
defaults to comprehend-first"), and nothing in the codebase connects it to
authoring a new `ProgIR`-reading capability (a Lambda-handling emitter, a
varargs walker). **No test exercises `promote_self_concern` on a `prog_read`
concern anywhere in the repo** — confirmed by grep across `tests/*.py` for
`prog_read` combined with `promot*`, zero hits, and by reading
`tests/test_prog_read_gap_migrated.py` in full (218 lines): every test there
stops at mint/dedup/surfacing (`_run_self_gaps`), never calls
`promote_self_concern`. This is a real, uncharacterized residual — see §4(iii).

---

## 3. A real, live instance — not just an architectural claim

**Yes — and it is a genuinely strong instance, not a synthetic one built for
this investigation.** `tests/test_prog_synthesis_selfimprove_migrated.py:138-205`,
`test_gap_promote_teach_accept_full_circle`, runs the *entire* chain on a real
`WorldAdapter` (`substrate.world_adapter.WorldAdapter`, the same class the
live daemon uses) with real `run_rules` fixpoints, not mocks or stubs:

1. `psy.synthesize_from_request(a.s, a.agent, REQ, ROWS)` where `REQ` is a
   request ("weighted pair") deliberately chosen to be outside both the
   starter codebook and `SynthEnumerate`'s reach (line 112-121 documents why:
   probed deterministic, `halt_reason='budget'`, `tested=200000`,
   `found=False`) → `r["status"] == "gapped"` (line 143).
2. `cwg.pending_code_write_gaps(a)` reads back exactly one
   `SelfConcern{kind:'code_write', source:'implicit', status:'noted',
   content:REQ}` (lines 149-153) — the rule from §1 firing for real.
3. `jd.promote_self_concern(a, str(scs[0]["id"]))` (line 160) produces a real
   `StandingConcern{status:'pending', kind:'code_write', about:REQ}` (lines
   162-167), with the `Experiment`-emptiness assertion from §2 (line 171).
4. `cwg.teach_write_shape_from_example(a, EXAMPLE, request_text=REQ, ...)`
   (line 175) — the CODE-4 teach-by-example facility, a human-supplied real
   example function, read via `code_reading.read_function` and taught as a new
   `code_write_construction` `ShapeSignature`.
5. The *same* `synthesize_from_request` call, re-run, now `status=='accepted'`
   (line 184), producing exactly one `Program` node whose IR is verified
   against a **held-out row never in the original example set** (line 192,
   `a=5, b=6` → `56`, never in `ROWS`).
6. A further `run_rules` pass (line 197) triggers `resolve_code_write_gap`
   (`seeds/code_write_gap.json:124-166`) purely from the taught shape's
   `taught_for` provenance — the `SelfConcern`'s `status` flips to `'resolved'`
   with **no Python status write** (lines 198-201), while the `StandingConcern`
   correctly stays `'pending'` (line 205, "the human-gated record of 'this was
   worth improving' stands").

This is precisely the scene the task brief asked whether it was possible to
construct — and it already exists, committed, gated in CI (the test file's own
header names its provenance: `PROGRAM_SYNTHESIS_PLAN.md §4-P6`,
`PROGRAM_SYNTHESIS_PREREG.md §8`, companion doc
`PROGRAM_SYNTHESIS_P6_SELFIMPROVE.md`). No new scene needed to be built for
this investigation.

**What is *not* demonstrated anywhere, live or in tests:** a `prog_read`
concern promoted (§2's residual); a synthesis-domain concern reaching an
actual `Experiment` node (deliberately out of scope per the test's own "SCOPE
HONESTY" comment, line 23-27 of the test file); and — checked separately —
whether this chain has ever fired on the **live daemon** outside a test
harness. `results/code_curriculum/code_curriculum_report.json` (a real batch
run, 2026-07-13, 560 files / 6252 functions scanned, a 26-item write battery)
records `teach_batch` entries with named failures (e.g. `abs_diff`: *"Call to
'abs' is neither a held leaf... (un-translatable... the named residual)"*,
`count_positives`: *"no Term emitter for this multi-statement shape"*) but the
artifact contains no `SelfConcern`/`StandingConcern` field — it is a scripted
batch-teach run (`scripts/code_curriculum_run.py`), not a daemon chat session,
and the report's schema does not record whether those specific failures ever
passed through `ps_gap_file`/`promote_self_concern`. **This investigation did
not find evidence of the mechanism firing on an actual production daemon
boot** — only the test-harness instance in point 3 above, which is a real
(non-mocked) instantiation of the same code path but not a "in the wild"
occurrence.

---

## 4. Characterizing the gap precisely

Per the task's own four-way disambiguation:

- **(a) — false as a blanket claim.** Synthesis *does* file a `SelfConcern`
  (§1). But (a) is exactly right for the decomposition-tier-2/3/4 population
  and the `arc6_import_impedance` survey — see §5 below; those specific named
  gaps are never represented as `SelfConcern` nodes at all.
- **(b) — false for the shapes that do exist.** Both `code_write` and
  `prog_read` `SelfConcern`s are shape-identical to the confirmed-real
  gap-awareness shape (§1), and `promote_self_concern` matches on `kind`
  generically, never rejecting either (§2).
- **(c) — true, precisely, for `code_write`, and probably true (untested) for
  `prog_read`.** For `code_write`: the promoted `StandingConcern` reaches a
  real closure mechanism, but it is **not** the `Experiment`/adopt spine — it
  is a parallel, purpose-built synchronous pipeline
  (`_process_code_write_standing` / `work_on_code_write_gap`) that the daemon
  routes to *instead of* `induce_concern`/`ground_concern`, by an explicit
  `if kind == "code_write"` branch (§2). This is (c) in the *narrow* sense the
  task brief anticipated — "nothing in the Experiment/adopt spine knows what
  to do with a program-synthesis-shaped StandingConcern" is literally true
  (the spine never sees it), but the fuller picture is that something else,
  built specifically for this, does close it — reported here as its own
  finding rather than folded into a flat "broken" verdict. For `prog_read`:
  the promoted `StandingConcern` would fall into the *generic*
  `induce_concern`/`ground_concern` path with `relations:[["comprehend",
  "DIRECTIVE", "mint", "GOAL"]]` — a relation shape with no structural
  connection to "extend the program-reading frame with a new AST-construct
  handler." Whether this actually produces anything useful or stalls
  honestly is **untested** (§2, §3) — this is the honestly uncertain half of
  (c).
- **(d) — false as the reason nothing has "happened."** The full circle
  (gap → promote → close → resolve) has demonstrably happened, live, on a real
  substrate, in `tests/test_prog_synthesis_selfimprove_migrated.py` (§3). It
  is not merely an aspirational claim awaiting a human `promote` action —
  though whether the *daemon*, running for a real human, has ever actually
  exercised this in production chat is unconfirmed (§3's closing paragraph).

**The single most load-bearing, precise finding:** the program-synthesis arc
did not skip building a self-improvement closure — it built one, and it built
a *different* one than the conversation domain's `Experiment`/adopt spine,
correctly judging (per `_promote_relations_for_concern`'s own comment, line
2083, *"never the comprehend-first path... these relations are... never read
by induce_concern for this kind"*) that composing a new write-shape from a
predication is not naturally an ARC/conversation-replay hypothesis test. This
is a deliberate, working, tested architectural choice — not a stub — but it
means the "same standing pipeline" framing in `docs/features/
program-synthesis.md` undersells how much *domain-specific* machinery was
actually required to make the `code_write` kind close, and is silent about
`prog_read`'s narrower, untested situation.

---

## 5. Is `ArcGoal`/`ax_impotent` the same mechanism, a parallel one, or something else?

**Genuinely different, with one narrow, one-directional bridge — not the same
architecture applied twice, and not redundant.**

`seeds/arc_goals.json:11` describes its own scope: *"ARC-GRAIN GOALS AS GRAPH
DATA... mints `ArcGoal` nodes from MEASURED sources (a STALE ceiling; a
residual's MEASURED BLOCKER SPLIT; the four claims with no measured source;
the agent's own SelfConcerns), extends the closed sig_seam vocabulary...
ranks them in a weighted collapse whose value is ABSOLUTE HEADROOM IN TASKS,
and ASKS — under ignorance, never under refutation."* This is a **goal-pool
prioritization and dispatch scheduler** over competing improvement
opportunities for the ARC-AGI battery specifically (`seeds/arc_executor.json`'s
own top-of-file description: *"the executor: winner -> run -> artifact ->
re-ingest -> epoch bump"*). `ax_impotent`
(`seeds/arc_executor.json:1669-1758`, comment) detects a **stuck dispatch
state**: *"a non-empty pool in which NOTHING is routable, no tie anywhere"* —
quantified over the whole `ArcGoal` pool via `dispatchable` (`ax_dispatch`'s
own routability test, reused verbatim per the comment) — and mints
`AgendaVerdict{kind:'impotent'}`. `ax_ask_impotent`
(`seeds/arc_executor.json:3998-4048`, comment) then asks a human a
*testimony-shaped* question about **why an entire class of goals is
unroutable** — via a distinct node type, `ArcImpotenceQuestion`, deliberately
*not* `ArcQuestion` (the comment at line 3999 explains this was "CAUGHT LIVE
DURING AR23c's OWN MEASUREMENT": an `ArcQuestion`-typed node would collide
with existing testimony-reply rules and silently mint pricing data, which
this rule explicitly must not do — *"this rule only asks, it does not
reprice"*).

**Neither `ax_impotent` nor `ax_ask_impotent` reads or writes `SelfConcern` or
`StandingConcern` anywhere** — confirmed by grep across `seeds/arc_executor.json`
and `seeds/arc_goals.json` for both node-type strings: the only two hits in
`arc_goals.json` are the *ingestion* direction (`ArcGoal` minted *from* an
existing `SelfConcern`, never the reverse). That ingestion is real but
deliberately handicapped: `seeds/arc_goals.json:1425` (comment on the
`self_concern`-sourced mint rule) states *"the goal is minted WITH NO sig_*
ATTRS AT ALL. It can be pursued... but cannot be matched by any residual — and
it pays `w_unsignatured` for that illegibility. Being illegible to the
evidence layer is a COST, not a free pass"* — a `SelfConcern`-sourced `ArcGoal`
is deliberately down-weighted in the ARC-goal collapse specifically *because*
its free-text content was never parsed into the `sig_seam` signature
vocabulary the rest of the executor's evidence layer requires (line 91: *"the
content is NEVER parsed into a signature — that is Seam C's failure exactly"*).

**Conclusion for point 5:** `SelfConcern`/gap-awareness answers *"does the
agent understand this, or can it do this"* (a comprehension/capability
question, surfaced via a human-readable content string). `ArcGoal`/
`ax_impotent` answers *"which of several competing, already-identified
improvement opportunities should the ARC executor work on next, and is the
current ranking stuck"* (a scheduling/prioritization question over a
structured, signature-matched goal pool). They are not the same mechanism
applied twice, and `ArcGoal`/`ax_impotent` is **not** already doing gap-
awareness's job for program synthesis — it is downstream *consumer* of a
narrow slice of gap-awareness's output (any `SelfConcern`, program-synthesis-
sourced or not, can become an unsignatured, cost-penalized `ArcGoal`
candidate), never a substitute for it, and never routes back into
`promote_self_concern`/`StandingConcern` at all.

**Separately, this also settles a question the task brief raised directly:**
the decomposition-tier-2/3/4 blockers and the `arc6_import_impedance` survey
(`results/arc6_import_impedance.json`, `scripts/arc6_import_impedance.py`)
are **not** represented as `SelfConcern` nodes anywhere. A repo-wide grep for
`decomposition_tier` across `seeds/*.json` finds it used only as a `kind`
value inside `seeds/arc_decompose.json:347` (an `ArcGoal`/`GoalResidual`-family
node, part of the *other* mechanism described in this section) — never
co-occurring with `SelfConcern`. A grep for `import_impedance` inside
`seeds/*.json` and `domains/*.py` returns zero hits entirely — the survey
script's own header (`scripts/arc6_import_impedance.py:1-40`) confirms it
"only reads the local repo (read-only)... and writes exactly one artifact:
`results/arc6_import_impedance.json`" — it never touches the graph. These
named capability gaps exist purely as `docs/research/program_synthesis/*.md`
prose and `ArcGoal`-pool structure, invisible to `_run_self_gaps`
(`domains/reflective_faculty.py`), the gap-awareness surfacing reader, and
therefore invisible to a human asking the agent "what gaps do you have."

---

## Scoped recommendations (not implemented — verification rung only)

1. **If the goal is "promote what is already filed" (cheap, uses existing
   machinery): there is nothing filed for decomposition tiers 2-4 or
   `arc6_import_impedance` to promote (§5).** Those are the two named
   candidate gaps in the task brief that motivated this investigation, and
   neither is a `SelfConcern` today — "promote the already-filed gap" does not
   apply to them. What *can* be promoted today, for real, is any
   `code_write`/`prog_read` concern a live daemon session has actually
   accumulated (check `jd.list_self_concerns(adapter)` on a running instance)
   — but per §3's closing paragraph, this investigation found no confirmed
   evidence any have accumulated outside the test harness.

2. **The smallest concrete build that would close the sharpest measured gap
   (§2's `prog_read` residual) is narrow and precisely scoped, in the arc's
   own amendment style:** give `kind:'prog_read'` the same treatment
   `_promote_relations_for_concern`/`_concern_tick` already give
   `kind:'code_write'` (`scripts/jabberwock_daemon.py:2078-2086`,
   `:2524-2528`) — a dedicated `elif at.get("kind") == "prog_read":
   _process_prog_read_standing(...)` branch routing to a new, narrow
   synchronous function in `domains/prog_synthesis.py` or a new
   `domains/prog_read_growth.py` mirroring `code_write_growth.py`'s shape,
   whose job is specifically "given the frame + blocker list a `prog_read`
   `StandingConcern` carries, attempt the mechanically-bounded fix this
   project already has a name for" (e.g., for a `Lambda` blocker: nothing
   automatic exists to compose new AST-emitter coverage from a predication
   the way `code_write_growth` composes a new construction — so the honest
   first version of this build may itself have to be "exhausted immediately,
   naming teach-by-example-equivalent for reading" as its own closing
   message, exactly the `code_write` path's own honest-exhaustion precedent).
   Sized like a single amendment (one new daemon branch, one new domain
   function, one new seed rule mirroring `note_code_write_composition_exhausted`),
   not a rebuild of the promotion spine. A test exercising
   `promote_self_concern` on a `prog_read` concern today (even before any new
   closure code exists) would at minimum convert §2's *reasoned* prediction
   ("falls through to `comprehend_first`, structurally mismatched") into a
   *measured* one — this is cheaper than the full build above and could be
   the very next, smaller step.

3. **If decomposition-tier-2/3/4 visibility to the agent's own gap-awareness
   is judged worth having** (a separate, larger judgment call this
   investigation does not make): the smallest build is a new rule in
   `seeds/arc_decompose.json`, sibling to `ps_gap_file`/`note_prog_read_gap`,
   that fires when a `decomposition_tier`-kind `ArcGoal`/`GoalResidual` is
   measured blocked on a *named, structural* reason (e.g. "needs N new Term
   variants" — already a fact this tree's own investigation docs compute) and
   mints a `SelfConcern{kind:'decomposition_tier', ...}` in the same shape —
   giving `_run_self_gaps` visibility into this population for the first
   time. This would need its own scoping pass (what exactly counts as
   "measured blocked" at the `ArcGoal` grain, and whether double-counting
   against the existing `ArcGoal`/`AgendaVerdict` bookkeeping is a risk) —
   named here as a candidate, not sized to amendment grain, because that
   scoping pass has not been done.

4. **Do not build a generic "connect `SelfConcern` promotion to
   `ArcGoal`/`ax_impotent`" bridge** — §5 found these are answering genuinely
   different questions (comprehension/capability vs. dispatch scheduling),
   and the existing one-directional, cost-penalized ingestion
   (`seeds/arc_goals.json:1425`) is already the considered, correct-weight
   connection between them; strengthening it (e.g., parsing `SelfConcern`
   content into `sig_seam` signatures) is explicitly named in the codebase's
   own comments as the *wrong* move ("Seam C's failure exactly" — parsing
   free text into signatures was tried and measured to over-match).

---

## Remaining uncertainty (numbered, honest)

1. **Whether this mechanism has ever fired on a real, non-test daemon
   session is not established either way.** §3 found strong evidence it works
   correctly in a real (non-mocked) test-harness boot, and found one batch-run
   artifact (`code_curriculum_report.json`) with failures shaped like what
   would trigger it, but that artifact's schema does not record whether
   `SelfConcern`/`StandingConcern` nodes were actually produced during that
   run, and this investigation did not attempt to boot the live daemon and
   drive it through a real chat session to check directly (out of scope for a
   read-only investigation with no build step).

2. **The `prog_read` fall-through-to-`comprehend_first` finding (§2, §4) is a
   reasoned prediction from reading `_promote_relations_for_concern`'s
   control flow, not a measurement.** No test calls `promote_self_concern` on
   a `prog_read`-kind concern anywhere in the repo (confirmed by grep), so
   what `induce_concern`/`ground_concern` would actually *do* with
   `relations:[["comprehend","DIRECTIVE","mint","GOAL"]]` and content words
   drawn from a blocked-read description (e.g. `"python read blocked:
   Lambda"`) was not run and observed — it is plausible the generic composer
   degrades gracefully (mints nothing useful, reports honestly) rather than
   doing something actively wrong, but this was not checked.

3. **This investigation did not exhaustively enumerate every `SelfConcern`
   `kind` value in the repository** to confirm the two named here
   (`code_write`, `prog_read`) are the *only* program-synthesis-adjacent
   ones. A targeted grep for `kind.*prog` / `kind.*synth` / `kind.*decomp`
   across `seeds/*.json` found only these two plus the ARC-goal-pool's
   separate `kind` vocabulary (`supply_blocker`/`source_claim`/
   `decomposition_tier`, which are `ArcGoal`/`GoalResidual` kinds, not
   `SelfConcern` kinds, per §5) — but a determined second pass specifically
   hunting for a third, more obscure `SelfConcern` kind tied to program
   synthesis was not separately attempted after this negative finding.

4. **Whether `docs/features/program-synthesis.md`'s wording should be judged
   "true" or "misleadingly narrow" is partly a judgment call about how a
   reader is expected to interpret "closing the human-gated self-improvement
   loop."** §2 and §4 lay out the precise mechanics so a future reader can
   decide for themselves; this document takes the position that the doc's
   literal wording is accurate (it never claims the `Experiment` spine
   specifically) but declines to adjudicate whether that wording should be
   strengthened with an explicit note about the `code_write`-specific bypass,
   since that is an editorial call for the doc's own maintainers, not a
   factual question this investigation is positioned to close.

5. **The `ArcGoal`/`ax_impotent` reading in §5 rests on the seed-file rule
   comments plus direct reading of the `ax_impotent`/`ax_ask_impotent` match/
   where/effects bodies** (`seeds/arc_executor.json:1669-1758`,
   `:3998-4048`) **and the `arc_goals.json` self-concern-ingestion rule**
   (`:1425` region) **— not a full read of every rule in either file** (both
   files are large; `arc_executor.json` alone defines at least fourteen named
   rules per the grep in this investigation's working notes). The specific
   claim checked — "does anything in either file read or write `SelfConcern`/
   `StandingConcern` beyond the one named ingestion rule" — was verified by
   grep across both full files for both type-name strings, which is a
   reasonably strong negative-finding method, but a rule that referenced
   `SelfConcern` only through an indirect Term-composed string (never the
   literal type name) would not have been caught by this method.
