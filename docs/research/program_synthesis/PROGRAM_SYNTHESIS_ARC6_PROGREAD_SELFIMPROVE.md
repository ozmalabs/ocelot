# ARC 6 — A25: `prog_read`'s self-improvement wiring — a prediction converted to a measurement, and one live bug it uncovered

**Date:** 2026-08-11/12
**Bars:** `PROGRAM_SYNTHESIS_ARC6_PREREG.md` **amendment A25** (`AR25a`-`AR25d`).
**Base commit:** `a62668d` (detached worktree
`/home/matt/ocelot-arc6-progread-selfimprove`, branch
`arc6-progread-selfimprove`).
**Engine:** `c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567`,
copied into this worktree and **verified resolving from inside it**.
Coherence probe passed before any measurement:
`add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` reads back `[1,2,3]` and
`(1,2,3)` **distinctly**.
**Seed:** `seeds/prog_read_gap.json` **v1.1.0** (bumped from v1.0.0),
**hand-authored** (no emitter tool exists for this file — confirmed by grep
across `tools/*.py`; the same status `seeds/code_write_gap.json`, the file
this amendment mirrors, already has).
**Gate:** `tests/test_prog_read_selfimprove_migrated.py` (new) — **7/7
green**; the five directly-adjacent suites plus a broad `prog_*`/`mbpp_*`
sweep reproduce their own baselines unchanged, one new failure surfaced by
the sweep confirmed **pre-existing** by stash-and-rerun (§5).
**No Rust engine change, no new `ProgEval`/`Term` variant, no touch to
`ArcGoal`/`ax_impotent`/`arc_executor.json`/`arc_goals.json`/
`arc_decompose.json`/`goal_residuals.json`/`arc_magnitude.json`/
`tools/build_arc_*.py`** — confirmed by `git status`/diff, not promised.

**SCOPE: exactly AR25a-AR25d — measure what `promote_self_concern`
actually does with a `prog_read` `SelfConcern` (a prediction in the
source investigation, never run), decide GO/NO-GO on closing it from the
measurement, and build the minimal, code_write-mirroring fix the
measurement justified.** This is self-improvement WIRING
(`scripts/jabberwock_daemon.py`, `seeds/prog_read_gap.json`,
`domains/prog_read_growth.py` new), not the ARC6 `ArcGoal`/`ax_impotent`
goal-pool-impotence machinery A9-A24 built — the source investigation's
§5 already confirmed those are separate mechanisms, and this rung does
not touch them.

---

## 0. VERDICTS

| bar | verdict | what it rests on |
|---|---|---|
| **AR25a — measure what actually happens, live** | **DONE — and worse than the reasoned prediction.** | The source investigation (§2, §4) REASONED that a `prog_read` concern would fall through to the generic `comprehend_first` composer and produce "something structurally mismatched" — a prediction, explicitly flagged as untested. Live measurement (§1 below): the generic composer does not merely mismatch — it INSTALLS A LIVE, PERMANENT, NEVER-FIRING RULE (`comprehend_describe_directive_<tag>`, matched on a literal Mention text `'describe'` about a `Scene` node) and reports `{"grounded": true}` with **zero** record anywhere that anything went wrong. |
| **AR25b — GO/NO-GO, decided from the measurement** | **SPLIT, both halves reported.** **NO-GO** on making a `prog_read` gap actually resolve — grep-confirmed zero engine support for `Lambda`/`Yield`/`Match`/`ClassDef`/... anywhere in `runners/dsl/src/*.rs`; genuinely Rust-engine-level work, named per-blocker. **GO** on fixing the WIRING — the measured bug (dead rule, false success, no record) is real and closeable at the seed/adapter grain, mirroring `code_write`'s own routing shape exactly. §2 |
| **AR25c — build, minimal, mirroring `code_write`'s exact pattern** | **DONE, live-verified.** One new module (`domains/prog_read_growth.py`), one new daemon branch pair (`_promote_relations_for_concern`/`_process_prog_read_standing`/`_concern_tick`), one new seed rule (`note_prog_read_composition_exhausted`). Live: the SAME Lambda-blocked scene now routes to the dedicated pipeline, mints zero dead rules, and records an honest, per-blocker `experiments_exhausted` reason. §3 |
| **AR25d — no regression, node-id lists not counts, fresh baseline this worktree** | **PASS.** Same single pre-existing failure before/after (`test_gap_awareness_migrated.py::test_resolved_topic_files_no_gap`, unrelated). One additional pre-existing failure surfaced by the broader `mbpp_*` sweep, confirmed unrelated by stash-and-rerun on the vanilla commit. §5 |

**The one thing worth reading if you read nothing else.** The source
investigation named `prog_read`'s promotion path as an honest unknown and
predicted it would "plausibly degrade gracefully." It does not. Measured
live, promoting a `prog_read` concern makes the agent's OWN generic
composer author a permanently-installed, never-firing rule — quietly,
under a name that quotes the concern it was supposed to be about — and
report success. This is not a missing feature; it is active, silent,
measured misbehavior, and it is exactly the kind of thing this project's
own gap-awareness culture exists to catch. The fix that closes it is not
"teach the agent to read Lambda" (that stays honestly NO-GO — no engine
support exists) — it is "give `prog_read` the same dedicated-routing
seatbelt `code_write` already has," and that alone converts a silent lie
into an honest, specific, per-blocker "I can't do this yet, and here is
exactly what would let me."

---

## 1. AR25a — THE LIVE MEASUREMENT

### 1.1 The scene

Mirrors `tests/test_prog_synthesis_selfimprove_migrated.py::
test_gap_promote_teach_accept_full_circle` exactly in shape: real
`substrate.world_adapter.WorldAdapter`, real `load_all_seeds`, real
`run_rules` fixpoints — no mocks, no stubs. The fixture is the SAME one
`tests/test_prog_read_gap_migrated.py` already uses (a two-function Python
source whose second function assigns a `lambda`):

```python
PY_TWO_FUNCTIONS = """
def add_one(x):
    return x + 1

def uses_lambda(v):
    f = lambda y: y + 1
    return f(v)
"""
```

Ingest → `note_prog_read_gap` fires → `SelfConcern{kind:'prog_read',
status:'noted', source:'implicit', content:'python read blocked:
Lambda'}`. `jd.promote_self_concern` → `StandingConcern{kind:'prog_read',
pipeline:'comprehend_first', relations:[["comprehend","DIRECTIVE","mint",
"GOAL"],["python","TARGET","of","SELF"],["read","TARGET","of","SELF"],
["blocked","TARGET","of","SELF"],["lambda","TARGET","of","SELF"]]}` — the
source investigation's §2 prediction confirmed byte-for-byte at this
point.

### 1.2 What `_concern_tick`'s generic branch actually does

`_concern_tick` (pre-fix) discards BOTH `induce_concern`'s and
`ground_concern`'s return values for every `StandingConcern` kind except
`code_write` — so measuring this honestly required calling them directly
and capturing what the daemon itself throws away:

```python
ind = rf.induce_concern(agent, relations, name_hint=name)
# ind: {"minted": True, "capability_key": "promoted_self_concern_<id>", ...}
#      residual = all 5 relations, covered_count: 0 (correctly — no held
#      shape covers "comprehend a directive about reading a blocked frame")

gr = rf.ground_concern(agent, [ind["capability_key"]])
```

`gr` is **not** an honest wall. It is:

```json
{
  "grounded": true,
  "served_by": "graph",
  "path": "compose_comprehension_rule",
  "form": "comprehension_rule",
  "grounded_relations": [["comprehend", "DIRECTIVE", "mint", "GOAL"]],
  "rule": {
    "name": "comprehend_describe_directive_promoted_self_concern_24189",
    "match": [["m", "has_mention", "mention"], ["m", "about", "scene"]],
    "where": {"And": [
      {"Eq": [{"Attr": ["mention", "text"]}, "describe"]},
      {"Not": {"Exists": [{"Neighbours": ["scene", "described_by"]}]}}
    ]},
    "effects": [
      ["add_node", "g", "Goal", {"kind": "describe_scene"}],
      ["add_edge", "g", "describes", "scene"],
      ["add_edge", "scene", "described_by", "g"]
    ]
  }
}
```

### 1.3 Root cause, read from the composer

`ground_concern`'s PATH 1 (`_residual_relations`) grounds our five
relations against the held `RelationCue` lexicon — and only the
`comprehend` head grounds to anything (`python`/`read`/`blocked`/`lambda`
are not held relation vocabulary). The composer dispatch
(`_pick_composer`) therefore sees only `{"comprehend"}` and routes to
`_compose_comprehension_rule` (`domains/reflective_faculty.py:~1905`).
That builder has an ordered set of named branches (`"find X near Y"`,
`"find X"`, ...) and one UNCONDITIONAL terminal fallback — the
`"describe a scene"` rule shape above — for ANY `comprehend`-headed
concern that matched none of the named branches, **regardless of what
word actually followed "comprehend."** It is not that this composer has
no rule for reading a blocked frame; it is that its terminal branch is
hard-coded to a single, unrelated, vision-domain shape and will author
that SAME rule for literally any concern that reaches it — a `prog_read`
gap, or anything else with no closer match.

The installed rule can never fire for anything `prog_read`-related (no
`prog_read` turn ever produces a Mention with literal text `'describe'`
about a `Scene` node) — it is permanent, silently-installed dead cruft,
under a name that quotes the concern's own id, reported as success. This
is measurably worse than the source investigation's own hedge
("plausible the generic composer degrades gracefully... not checked") —
it is a confirmed, active, silent misbehavior, not a graceful null.

---

## 2. AR25b — GO/NO-GO

**Two different questions, two different answers, both from evidence, not
assumption.**

**Q1 — can a `prog_read` gap be made to actually RESOLVE (the
`resolve_code_write_gap` precedent) at the seed/adapter grain, the way
`code_write`'s own predication composer sometimes does? NO-GO.**
`code_write`'s close works because English write-REQUESTS can map onto
Terms the engine ALREADY evaluates (`Times`/`Plus` — arithmetic the
engine has always run). `prog_read`'s blockers are the opposite shape: an
AST construct the emitter's fixed correspondence table
(`domains/prog_ir_emit.py`) has NO case for, because the ENGINE has no
representation for what it would decode to. Confirmed by grep across
`runners/dsl/src/*.rs`: **zero** hits for `Lambda`. Zero for the other
named blockers this module's docstring enumerates (`Yield`, `Match`,
`ClassDef`, `With`, ...). There is no "compose from held vocabulary" move
available for reading an unsupported construct — decoding syntax into IR
the engine can run requires the engine to be ABLE to run it. This is
genuinely Rust-engine-level work, named precisely per blocker (not a
blanket "unsupported"):

| blocker | what it needs (from `domains/prog_read_growth._BLOCKER_RUST_NEED`) |
|---|---|
| `Lambda` | a closure Term carrying a captured environment (function VALUES, not just top-level `DefFn`, are not representable today) |
| `KwargsCall` | a keyword-argument binding Term |
| `StarArgsCall`/`StarArgsParam` | a variadic-argument spread/binding Term |
| `Yield`/`Await` | a generator/suspension evaluation model (`ProgEval` has no resumable-frame representation) |
| `Match` | a structural pattern-matching dispatch Term |
| `ClassDef` | a class/instance object model (no OO value representation exists) |
| `RecvMethod:<name>` | a mutating-call lvalue write-back path (the engine structurally refuses this — no write-back path for a pure `ProgCallExtern`) |
| `TryFinally`/`TryElse`/`MultiExcept`/`TypedExcept` | finer exception-control-flow Terms on top of the existing `TryOr` (which only catches ANY trap) |
| `ComprehensionSet`/`ComprehensionDict` | Set/Dict-typed comprehension results (`ComprehensionList` only ever builds a `List`) |
| (16 more named entries) | see `domains/prog_read_growth._BLOCKER_RUST_NEED` and the classified `RecvMethod:`/`OpExt:`/`GraphRepr:` prefixes |

**Q2 — is the MEASURED BUG (§1) closeable at the seed/adapter grain,
mirroring `code_write`'s dedicated-routing shape? GO.** This is a
different, smaller, and much better-evidenced question than Q1. The bug
is not "the agent cannot read Lambda" — the agent correctly cannot, and
that is fine and expected. The bug is "the agent's OWN self-improvement
plumbing silently installs dead cruft and lies about success when asked
to work on this gap." That is a routing/honesty defect, not a capability
gap, and `code_write`'s own pipeline already demonstrates the correct
shape for closing exactly this KIND of defect: route the kind to its own
dedicated function, attempt whatever close IS available (for `code_write`
that is sometimes real; for `prog_read` today it is never), and record an
honest, specific outcome either way — `code_write`'s own
`compose_write_shape_from_predication` exhausts for the overwhelming
majority of requests outside its own tiny multiplier/offset family, and
that honest exhaustion (never silent, always a named reason a human can
read) is the accepted, working shape of the pipeline, not a lesser one.
A `prog_read` pipeline that always exhausts today, naming the missing
Rust primitive per blocker, is that SAME shape.

---

## 3. AR25c — THE BUILD

### 3.1 `domains/prog_read_growth.py` (new, 195 lines)

The `code_write_growth.py` sibling, sized to what AR25b's GO actually
supports (not to what a full close would need):

- `work_on_prog_read_gap(agent, about_text)` — mechanically reverses
  `note_prog_read_gap`'s own `StringConcat` (`'<frame> read blocked:
  <blockers>'` → `(frame, blockers)`, a fixed text split — the
  `code_write_growth._stem` precedent's exact status, never a decision
  about meaning) and looks each blocker up in `_BLOCKER_RUST_NEED` (a
  FIXED correspondence table — the `prog_ir_emit.py` `NATIVE_ORACLES`/
  `_BINOP_AB` precedent's status) plus three classified prefixes
  (`RecvMethod:`/`OpExt:`/`GraphRepr:`) and a generic fallback. Always
  returns `{ok: False, reason: ..., needs: {<blocker>: <primitive>}}`
  today, by measured construction — not a stub that happens to always
  fail, but a function whose honest job IS naming why it cannot succeed
  yet.
- `pending_prog_read_gaps(agent)` — mirrors `pending_code_write_gaps`,
  kind-swapped.

### 3.2 `scripts/jabberwock_daemon.py`

- `_promote_relations_for_concern` gained an `if kind == "prog_read":`
  branch (immediately after the existing `code_write` branch) returning
  `relations=[["extend","FRAME","from","BLOCKER"], ...]`,
  `pipeline="prog_read"` — so a promoted `prog_read` concern's own
  `StandingConcern` record is self-describing instead of silently
  reusing `"comprehend_first"`.
- `_process_prog_read_standing(adapter, standing_node, at)` (new) mirrors
  `_process_code_write_standing` line for line: calls
  `prg.work_on_prog_read_gap`, records `prog_read_compose_ok`/
  `prog_read_compose_reason` on the `StandingConcern` — a mechanical
  outcome datum, never a decision.
- `_concern_tick` gained one `if at.get("kind") == "prog_read":` branch,
  positioned immediately after the existing `code_write` branch and
  BEFORE the generic fallback — this is the line that stops the wrong
  composer from ever running on a `prog_read` concern again.

### 3.3 `seeds/prog_read_gap.json` v1.0.0 → v1.1.0

One new rule, `note_prog_read_composition_exhausted` —
`note_code_write_composition_exhausted` (`seeds/code_write_gap.json`)
copied verbatim and kind/attr-name-swapped: matches
`["agent","has_self_concern","sc"], ["sc","promoted_to","standing"]`,
gated on `standing.kind=='prog_read'` and
`standing.prog_read_compose_ok==0.0` and `Not(experiments_exhausted)`,
sets `experiments_exhausted:true` and copies
`prog_read_compose_reason` onto `exhausted_note`. No emitter tool exists
for this file (confirmed by grep across `tools/*.py`) — hand-edited, the
same status `code_write_gap.json` itself already has (also hand-authored,
no emitter). **No `resolve_prog_read_gap` rule was added** — per AR25b's
NO-GO, nothing can make a `prog_read` gap resolve today, so a resolve
rule would be dead code with no path to ever fire; the absence is named
here rather than filled with speculative graph data.

### 3.4 Live confirmation (`tests/test_prog_read_selfimprove_migrated.py`, 7/7)

The SAME Lambda-blocked scene, post-fix:

```python
res = jd.promote_self_concern(agent, str(concern["id"]))
assert res["pipeline"] == "prog_read"          # was "comprehend_first"

jd._concern_tick(agent)
sat = agent.s.node(standing_id)["attrs"]
assert sat["status"] == "processed"
assert sat["prog_read_compose_ok"] == 0.0
assert "Lambda" in sat["prog_read_compose_reason"]
assert "closure" in sat["prog_read_compose_reason"].lower()

agent.s._inner.run_rules(400000)
sat2 = agent.s.node(standing_id)["attrs"]
assert sat2["experiments_exhausted"] is True
assert "Lambda" in sat2["exhausted_note"]
```

and, separately, a diff over `CapabilityAxis`/`Observation`/`Experiment`
node sets before/after `_concern_tick` confirms **zero** new nodes tagged
with this concern's own key — the dead-rule mint from §1 is gone, not
merely unobserved. Additional unit gates on `work_on_prog_read_gap`
directly: a multi-blocker request (`"KwargsCall,Lambda"`) names BOTH
blockers' reasons; the `RecvMethod:`/`OpExt:` classified-prefix paths;
the generic fallback for an unnamed blocker; the no-blocker-parsed edge
case; `pending_prog_read_gaps`.

---

## 4. WHY THIS IS THE RIGHT SIZE, NOT A PARTIAL FIX

A larger build was available and explicitly declined: widening
`domains/prog_ir_emit.py`'s correspondence table for the blockers that
might NOT need a new Rust `Term` (e.g. `IsinstanceMultiType` — an
OR-of-type-names argument convention — MIGHT be expressible by emitting
an `Or` of existing `IsOp` checks with no new engine primitive). This
amendment does not attempt that. Two reasons, both load-bearing:

1. **It is out of this rung's stated scope.** The task instructions were
   explicit: minting new correspondence-table coverage in
   `prog_ir_emit.py` is ARC2/ARC5-grain engineering (the emitter's own
   widening history — Q1/Q1.5 — is a multi-document arc in itself), not
   self-improvement WIRING. Even a single narrow widening would blur
   that boundary for a "one amendment" rung.
2. **There is no general mechanism to build, only a case-by-case
   engineering judgment call per blocker** — unlike `code_write`'s
   predication composer, which is a genuinely GENERIC move (any request
   whose predicate resolves to a held multiplier/offset word closes the
   same way). Building a bespoke per-blocker special case inside
   `work_on_prog_read_gap` for `IsinstanceMultiType` alone would be
   exactly the kind of one-off, ungeneralizable patch this project's own
   SHAPES-not-numbers standing rule (`CLAUDE.md`, 2026-08-06/07) warns
   against — a scalar special case standing in for a shape nobody has
   actually designed yet.

The value delivered here is narrower and, on the measured evidence,
worth more: the WIRING no longer lies. A future amendment that lands a
real emitter widening (with or without new Rust) plugs into
`_BLOCKER_RUST_NEED` and `work_on_prog_read_gap` cleanly, at that point —
the registered null reading (`PROGRAM_SYNTHESIS_ARC6_PREREG.md` A25)
states this explicitly.

---

## 5. REGRESSION — A LIST OF NODE IDS, NEVER A COUNT

Fresh baseline, measured in this worktree, **before any edit**:

```
tests/test_program_synthesis_migrated.py
tests/test_prog_synthesis_selfimprove_migrated.py
tests/test_gap_awareness_migrated.py
tests/test_self_concern_promote_migrated.py
tests/test_prog_read_gap_migrated.py
```

First attempt surfaced 24 failures, ALL traced to the fresh worktree
lacking the untracked, gitignored `results`/`data` directories these
suites read from disk (`results/prog_construction_scan.json`, etc.) — the
same "`data`/`results` are untracked symlinks into the canonical tree"
hazard A22/A23's own discipline names. Symlinked both; re-measured:

```
FAILED tests/test_gap_awareness_migrated.py::test_resolved_topic_files_no_gap
1 failed, 39 passed, 2 skipped
```

(a moon-grounding outcome assertion, untouched by this amendment,
unrelated to program synthesis.)

**After this amendment** (same five suites + the new
`tests/test_prog_read_selfimprove_migrated.py`):

```
FAILED tests/test_gap_awareness_migrated.py::test_resolved_topic_files_no_gap
1 failed, 46 passed, 2 skipped
```

**Identical failing node id.** 7 new tests, all green (39 + 7 = 46).

**Broader sweep** (`test_prog_*_migrated.py` / `test_mbpp_*_migrated.py`,
per the task's own instruction to check "whatever other suites exist" —
zero overlap with any file this amendment edited, so not separately
pre-baselined, but swept post-edit and any red cross-checked):

```
tests/test_prog_chunks_migrated.py
tests/test_prog_constructions_migrated.py
tests/test_prog_descent_migrated.py
tests/test_prog_ir_migrated.py
tests/test_prog_moves_migrated.py
tests/test_prog_property_migrated.py
tests/test_prog_read_llvm_migrated.py
tests/test_prog_read_python_migrated.py
tests/test_prog_read_rust_lua_migrated.py
tests/test_prog_repair_migrated.py
  → 267 passed, 2 skipped

tests/test_prog_synthesis_battery_migrated.py
  → 21 passed

tests/test_mbpp_arc3_endgame_migrated.py
tests/test_mbpp_contamination_migrated.py
tests/test_mbpp_endgame_migrated.py
  → 77 passed

tests/test_mbpp_baseline_migrated.py
tests/test_mbpp_diet_migrated.py
tests/test_mbpp_histogram_migrated.py
tests/test_mbpp_spec_migrated.py
  → FAILED tests/test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live
    1 failed, 146 passed
```

**The one new red, cross-checked and confirmed pre-existing.**
`test_three_runnable_tasks_reverify_live` asserts a live MBPP re-run's
`construction` field matches a documented drift table
(`_KNOWN_CONSTRUCTION_DRIFT`); on this box it observes `'sum_of_two'`
where the table expects `'range_sum_spine'` for one task id. This has
**zero conceptual overlap** with anything this amendment touched
(`prog_read`/`code_write`/self-improvement wiring vs. MBPP zero-shot
codebook construction naming). Confirmed pre-existing by `git stash`-ing
this amendment's two edited files (`scripts/jabberwock_daemon.py`,
`seeds/prog_read_gap.json` — the untracked new files don't affect this
test at all) and re-running on vanilla `a62668d`: **same assertion, same
observed value, same task**. Restored immediately after
(`git stash pop`), confirmed byte-identical `seeds/prog_read_gap.json`
(`version: "1.1.0"`, 2 rules) after the pop.

**No new failing node id introduced by this amendment, anywhere.**

---

## 6. EVERYTHING THAT BROKE

Recorded because the process is the result (A11-A17's own standing
practice).

1. **The `data`/`results` untracked-symlink hazard, reproduced again, on
   a fresh worktree's FIRST baseline attempt** — 24 apparent failures
   that were entirely a missing-fixture artifact, not a real regression.
   Recovered by symlinking both directories from the canonical tree (the
   documented A17/WIRE_HANDS precedent), confirmed by re-measuring: the
   true baseline was 1 pre-existing failure, not 24.
2. **A `test_mbpp_baseline_migrated.py` collection error** on the first
   invocation — `ModuleNotFoundError: No module named
   'mbpp_zero_shot_baseline'`. Not a regression: this test file's own
   docstring specifies `PYTHONPATH=runners/dsl/python:.:scripts` (unlike
   most other migrated test files, it does not insert `scripts/` into
   `sys.path` itself at import time). Re-run with the documented
   `PYTHONPATH` resolved cleanly to the single pre-existing failure named
   in §5.
3. **The initial rule-node inspection in the exploratory probe script
   (scratchpad, not committed) found nothing**, briefly looking like the
   composer hadn't minted anything — a false lead. `agent.inner.add_rule`
   installs directly into the Rust engine's live rule table, not as a
   graph-resident `Rule`-typed node, so `sub.nodes("Rule")` was the wrong
   query. Resolved by capturing `ground_concern`'s own return dict
   directly (§1.2) — which is also exactly the datum `_concern_tick`
   itself was silently discarding, the actual root cause of the honesty
   gap this amendment closes.

---

## 7. REMAINING UNCERTAINTIES

1. **The generic `compose_comprehension_rule` composer's hard-coded
   terminal fallback (§1.3) is not specific to `prog_read`.** ANY
   `StandingConcern` whose relations ground only a bare `comprehend` head
   — any kind this amendment did not touch, promoted through the generic
   path — would hit the SAME unconditional `"describe a scene"` branch.
   This amendment fixes `prog_read` by routing it away entirely (mirroring
   `code_write`); it does NOT fix the composer's own hard-coded fallback,
   which remains a live hazard for any other kind that reaches it. Named
   here, not fixed here — out of this rung's scope (the composer itself
   is shared machinery several other kinds still depend on for their
   OWN, working comprehension-first closes).
2. **Whether any OTHER `StandingConcern` kind in the live system has
   ever actually hit that same terminal fallback is not established.**
   This amendment measured it for `prog_read` specifically; a systematic
   sweep of every kind's grounded-relations shape against
   `_compose_comprehension_rule`'s branch structure was not attempted.
3. **`_BLOCKER_RUST_NEED`'s table is not exhaustive** over every blocker
   `prog_ir_emit.py` can emit (that table itself is large and has grown
   across several arcs) — a blocker absent from it gets the honest
   generic fallback message, not a specific one. Widening the table is
   safe and additive but was not attempted exhaustively here (would be
   restating `prog_ir_emit.py`'s own module docstring blocker-by-blocker,
   a documentation task, not a wiring one).
4. **Whether ANY blocker is closeable via emitter-only widening (no new
   Rust Term) was investigated only for one candidate**
   (`IsinstanceMultiType`, §4) and not built or exhaustively checked
   across all ~40 named blockers — named as a real, smaller, separate
   future rung (ARC2/ARC5 grain, not this one).

---

## 8. FILES

| file | what |
|---|---|
| `domains/prog_read_growth.py` | **new**, 195 lines: `work_on_prog_read_gap`, `pending_prog_read_gaps`, `_BLOCKER_RUST_NEED` |
| `scripts/jabberwock_daemon.py` | +~45 lines: `prog_read` branch in `_promote_relations_for_concern`, new `_process_prog_read_standing`, `prog_read` branch in `_concern_tick` |
| `seeds/prog_read_gap.json` | v1.0.0 → v1.1.0, hand-edited (no emitter exists): +1 rule (`note_prog_read_composition_exhausted`) |
| `tests/test_prog_read_selfimprove_migrated.py` | **new**, 7 gates |
| `PROGRAM_SYNTHESIS_ARC6_PREREG.md` | amendment A25 appended |
| `PROGRAM_SYNTHESIS_ARC6_PROGREAD_SELFIMPROVE.md` | this file |

**In this worktree's `git status`, not part of the change:**

- `data` and `results` appear as untracked **symlinks** into the
  canonical tree (gitignored). Must not be staged.
- `runners/dsl/python/substrate_rs/_native.abi3.so` does not appear as
  modified — copied verbatim from the canonical tree, sha unchanged.

**Nothing in the canonical tree changed.** `/home/matt/ozmadev/ocelot`'s
own `git status --porcelain` was re-verified clean throughout.

---

## 9. REPRODUCE

```bash
# --- the worktree ---------------------------------------------------------
git worktree add --detach /home/matt/ocelot-arc6-progread-selfimprove a62668d
cd /home/matt/ocelot-arc6-progread-selfimprove
git checkout -b arc6-progread-selfimprove
ln -s /home/matt/ozmadev/ocelot/data    data
ln -s /home/matt/ozmadev/ocelot/results results

# --- the engine -------------------------------------------------------------
cp /home/matt/ozmadev/ocelot/runners/dsl/python/substrate_rs/_native.abi3.so \
   runners/dsl/python/substrate_rs/_native.abi3.so
touch runners/dsl/python/substrate_rs/_native.abi3.so   # clear worktree mtime staleness
sha256sum runners/dsl/python/substrate_rs/_native.abi3.so
#   c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567

# --- the coherence probe ---------------------------------------------------
PYTHONPATH=runners/dsl/python:. python3 -c "
import substrate_rs as srs; s=srs.Substrate()
a=s.node(s.add_node('T',{'lst':[1,2,3],'tup':(1,2,3)}))['attrs']
print(a['lst'], a['tup'], type(a['lst']), type(a['tup']))"

# --- seeds/prog_read_gap.json is hand-authored (no emitter exists) --------

# --- the gate ---------------------------------------------------------------
OZMA_SEED_PERSIST_DISABLED=1 PYTHONPATH=runners/dsl/python:.:scripts \
  python3 -m pytest tests/test_prog_read_selfimprove_migrated.py \
    --confcutdir=. -q                       # 7 passed

# --- the regression arms -----------------------------------------------------
OZMA_SEED_PERSIST_DISABLED=1 PYTHONPATH=runners/dsl/python:.:scripts \
  python3 -m pytest tests/test_program_synthesis_migrated.py \
    tests/test_prog_synthesis_selfimprove_migrated.py \
    tests/test_gap_awareness_migrated.py \
    tests/test_self_concern_promote_migrated.py \
    tests/test_prog_read_gap_migrated.py \
    --confcutdir=. -q                       # 1 failed (pre-existing) / 46 passed / 2 skipped

OZMA_SEED_PERSIST_DISABLED=1 PYTHONPATH=runners/dsl/python:.:scripts \
  python3 -m pytest tests/test_prog_chunks_migrated.py tests/test_prog_constructions_migrated.py \
    tests/test_prog_descent_migrated.py tests/test_prog_ir_migrated.py \
    tests/test_prog_moves_migrated.py tests/test_prog_property_migrated.py \
    tests/test_prog_read_llvm_migrated.py tests/test_prog_read_python_migrated.py \
    tests/test_prog_read_rust_lua_migrated.py tests/test_prog_repair_migrated.py \
    tests/test_prog_synthesis_battery_migrated.py \
    --confcutdir=. -q                       # 288 passed, 2 skipped

PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 -m pytest tests/test_mbpp_baseline_migrated.py tests/test_mbpp_diet_migrated.py \
    tests/test_mbpp_histogram_migrated.py tests/test_mbpp_spec_migrated.py \
    tests/test_mbpp_arc3_endgame_migrated.py tests/test_mbpp_contamination_migrated.py \
    tests/test_mbpp_endgame_migrated.py \
    --confcutdir=. -q                       # 1 failed (pre-existing, cross-checked §5) / 223 passed
```
