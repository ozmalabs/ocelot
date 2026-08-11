# `ground_concern`'s comprehension composer — RESULTS: NO-GO, precisely
# characterized, with live evidence in both directions

**Date:** 2026-08-11/12.
**Prereg:** `GROUND_CONCERN_COMPREHENSION_HONESTY_PREREG.md` (this directory).
**Base commit:** `4563c3a` (`main`'s tip). Worktree
`/home/matt/ocelot-ground-concern-honesty`, branch `ground-concern-honesty`.
**Engine:** `c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567`
(committed `runners/dsl/python/substrate_rs/_native.abi3.so`), verified
resolving from inside the worktree. Coherence probe passed:
`add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` reads back `[1,2,3]` and
`(1,2,3)` distinctly.
**Code change shipped:** **NONE.** `domains/reflective_faculty.py` is
byte-identical to `main`'s tip. This is a NO-GO with a clean, evidenced
block — per this project's own standing culture, a well-characterized null
is the complete result, not a shortfall.

**A note on how this session ran, for the reviewer's benefit.** A shared
multi-tenant box hosting this and other concurrent worktrees hit a severe
OOM mid-session (unrelated runaway process, ~89GB RSS) and rebooted; after
recovery, every test invocation below ran serially, one command at a time,
wrapped in `systemd-run --scope --user -p MemoryMax=... -p MemoryHigh=...`
per the coordinator's post-incident instruction. A second, independent
agent session's test workers held 4 CPU cores pinned near 100% for over an
hour throughout this work, which is the reason several of the wall-clock
times below (up to 5 minutes for suites that would otherwise take seconds)
are inflated — verified NOT a hang: CPU-bound the whole time, RSS stable,
never approached the memory ceiling. No experiment in this document
involved unbounded loops, recursion without depth limits, or
non-terminating fixtures on my own side; the one open-ended live growth
this investigation deliberately triggered (`induce_concern`/`ground_concern`
minting CapabilityAxis nodes and installing rules) is bounded by design —
each `induce_concern` call runs the seeded `run_rules` fixpoint once and
returns.

---

## 0. VERDICTS

| bar | verdict | rests on |
|---|---|---|
| **AR-H-a — locate the discriminator** | **DONE. None exists in the data available to the function.** | §1: three independent, live-measured mechanisms, all pointing the same way. |
| **AR-H-b — GO/NO-GO** | **NO-GO.** | The only data `_compose_comprehension_rule(agent, keys, rels)` receives (`rels`/`rp`) is **structurally identical** between the canonical genuine describe-scene concern, `recount_faculty`'s own legitimate but differently-worded concern, and an arbitrary unrelated concern (prog_read's real shape, or synthetic gibberish) — proven live, not inferred. §1 |
| **AR-H-c — caller-safety survey** | **DONE.** | 9 real call sites read; 3 discard `ground_concern`'s return value entirely and rely on the installed-rule side effect (the ones that would break); 3 already branch correctly on `grounded`; 2 route to a different composer entirely (safe, untouched); 1 is a docstring-only mention (not a real call). §2 |
| **AR-H-d — fix or block** | **BLOCKED, with live evidence.** | A concrete candidate gate was built, applied, and run against the real test suite: it broke a currently-green, currently-relied-upon test (`test_composers_graph.py::test_structural_equivalence_comprehension_describe`) with a clean `KeyError: 'form'`, then reverted. §3 |
| **AR-H-e — regression** | **PASS on everything actually touched (nothing — no code changed).** | ~170 tests across 13 directly-relevant files run clean on the unmodified tree (2 pre-existing, unrelated red items identified and explained, not attributable to this investigation). §4 |

**The one thing worth reading if you read nothing else.** The terminal
branch's own docstring already says what this document proves with live
data: `_compose_comprehension_rule`'s fallback fires on ANY concern whose
grounded relations reduce to bare `{"comprehend"}` (or `{"comprehend",
"decompose"}`), and the concern's own directive word — "describe",
"recount", or anything else — is **discarded by `induce_concern`'s own
residual computation before `_compose_comprehension_rule` ever sees it**.
`domains/recount_faculty.py`'s module docstring already documented this
independently, calling it "HARD-CODED... regardless of the NL tokens
handed to `induce_concern`" and naming the real fix as out of scope for
that build. A25's `prog_read` bug and `recount_faculty`'s legitimate reuse
of the SAME branch are the SAME mechanism, not two different ones — which
is exactly why no gate expressible from what this function receives today
can separate them.

---

## 1. AR-H-a — the discriminator search, live-measured

### 1.1 Every held relation cue for "comprehend" is one relation, content-blind

`seeds/relation_vocabulary.json` has exactly ONE `RelationCue` whose
relation head is `comprehend`: keywords `hear`/`heard`/`comprehend`/
`directive`/`instruction`/`listen`/`understand` → the single relation
`["comprehend", "DIRECTIVE", "mint", "GOAL"]`. There is **no** relation
head `describe` or `scene` anywhere in the 52-relation-head vocabulary
(checked exhaustively — full head list in the transcript this doc is drawn
from). So no version of the `"find" in rp`-style gate can ever exist for
"describe": the vocabulary that would ground it doesn't hold it.

### 1.2 `induce_concern`'s own residual computation discards the content word — proven, not inferred

Live probe (real `WorldAdapter`, `load_all_seeds`, no mocks), feeding the
SAME two-clause template `[["hear","the",X,"DIRECTIVE"], ["mint","a","GOAL"]]`
with four different values of `X`:

| `X` | `residual_predicates` | `grounded_relations` (`rp`) | `grounded` | `form` |
|---|---|---|---|---|
| `"describe"` (arc_self_report's own canonical case) | `['hear','mint']` | `{decompose, comprehend}` | `True` | `comprehension_rule` |
| `"recount"` (recount_faculty's own case) | `['hear','mint']` | `{decompose, comprehend}` | `True` | `comprehension_rule` |
| `"gibberish_unrelated_xyz"` (synthetic control) | `['hear','mint']` | `{decompose, comprehend}` | `True` | `comprehension_rule` |
| `"progread"` (synthetic control) | `['hear','mint']` | `{decompose, comprehend}` | `True` | `comprehension_rule` |

**Byte-identical across all four.** The directive word (`X`) is discarded
during `induce_concern`'s coverage/residual computation — `residual_predicates`
never contains it — before `_residual_relations` (which builds `rels`) even
runs. This is not a lexicon gap that a new `RelationCue` could close: the
signal is gone one layer upstream of the lexicon lookup.

### 1.3 The full observation isn't even persisted on the graph node `ground_concern` reads

`ground_concern` (line ~6423) reads `obs = at.get("observation")` off the
`CapabilityAxis` node — but that attr **does not exist** on any axis minted
by the current (post-migration) `induce_concern`/`sd_mint_quantum` path.
Live-dumped a real minted axis's full attrs: `{'source', 'is_axis',
'capability_keys', 'closest_held_shape', 'residual_predicates',
'from_observation', 'induced', 'description'}` — no `observation` key.
`ground_concern`'s `obs` variable is set and never read again (a dead
read, itself an honest residual of the sd-loop migration, not something
this rung's scope covers). So even a signature change threading a richer
payload into `_compose_comprehension_rule` has nothing to read: the literal
directive word is gone by the time any composer-side code runs, not merely
unpassed.

### 1.4 prog_read's REAL production shape reproduces the same collapse

Feeding `induce_concern` A25's own measured `StandingConcern.relations`
verbatim (`[["comprehend","DIRECTIVE","mint","GOAL"], ["python","TARGET",
"of","SELF"], ["read","TARGET","of","SELF"], ["blocked","TARGET","of",
"SELF"], ["lambda","TARGET","of","SELF"]]`) yields `grounded_relations:
[["comprehend","DIRECTIVE","mint","GOAL"]]` — `rp = {"comprehend"}` only
(no `decompose`, because prog_read's shape never includes an isolated
`"mint"` token the way the two-clause `arc_self_report`/`recount_faculty`
template does). This is a SUBSET of the describe/recount shape, not a
different one — any gate permissive enough to admit describe/recount is
at least as permissive for prog_read's real shape.

### 1.5 The current, frozen, PASSING test suite already encodes bare-`{"comprehend"}` as correct

`tests/test_composers_graph.py::test_structural_equivalence_comprehension_describe`
(currently green): `rels = [("comprehend", "X")]`, `rp = {"comprehend"}` —
**no `"find"`, no other signal at all** — asserts
`py_res["form"] == "comprehension_rule"`. `tests/fixtures/
composer_driver_parity/ground_concern.json`'s `relation_head_cases.comprehend`
entry (the frozen driver-parity fixture) locks in the identical claim:
`grounded_relations: [["comprehend","DIRECTIVE","mint","GOAL"]]` →
`form: "comprehension_rule"`, `grounded: true`. Both are exercised by
currently-green tests on the unmodified tree (§4). Any gate stricter than
bare `{"comprehend"}` breaks tests that are gating CORRECT, intended,
currently-relied-upon behavior — not incidental collateral.

**Conclusion of §1: there is no discriminator.** Three independent
mechanisms (relation-vocabulary content-blindness, residual-computation
content-discarding, and non-persistence of the raw observation) all
converge on the same fact — by the time `_compose_comprehension_rule`
runs, a genuine "describe a scene" concern and an arbitrary unrelated one
are the same data.

---

## 2. AR-H-c — caller survey

| caller | file:function | checks `grounded`? | exposed if terminal branch is gated |
|---|---|---|---|
| `build_describe_faculty` | `scripts/arc_self_report.py:37-66` | **No** — calls `ground_concern(a,[cA["capability_key"]])`, discards return | **YES** — the canonical describe faculty never installs |
| `_ensure_describe` → `build_describe_faculty` | `domains/conversation_action.py:309-329` | No (same root cause) | **YES** — same faculty, reached from the live conversation loop |
| `build_recount_faculty` | `domains/recount_faculty.py:160-179` | No — discards both `ground_a`/`ground_b` | **YES** — live-confirmed (§3): `test_composers_graph.py`'s equivalent shape breaks with a clean `KeyError`; `recount_faculty`'s own docstring independently documents reliance on the exact unconditional behavior |
| `ensure_conceptualizer_rules` | `domains/conceptualizer.py:378-395` | No (discards) | **No** — its concern (`form`/`shape`/`monitor`/`commit` clauses) grounds to the `"conceptualize"` composer, never reaches `_compose_comprehension_rule` (live-verified: `path: compose_conceptualize_rule`) |
| 3 call sites (`filter`/`disambiguate`/`cache` concerns) | `domains/consumption_quality.py:163,247,412` | No (discards) | **No** — route to `language_faculty`/`memory_faculty` composers, structurally distinct relation heads (`filter`/`disambiguate`/`cache`), never `comprehend` |
| `extend_for_gap` | `domains/substrate_extension.py:520-556` | **Yes** — branches on `ground.get("grounded")`, has a genuine `"primitive_request"` fallback for a wall | Safe either way — this caller was ALREADY built to the shape this fix would have produced |
| free-form "author_concern" NL path | `domains/conversation_action.py:445-490` | **Yes** — branches on `gr.get("grounded")`, formats an honest "grounds to no held structure... an honest frontier" reply on False | Safe — already correct |
| `_concern_tick` generic branch | `scripts/jabberwock_daemon.py:2595-2601` | No (discards) | Safe — return value unused either way. **Note:** this is the SAME fallback that reply_fix/knowledge/self_account/instruction/performance/comprehension concerns still route through today (`_promote_relations_for_concern` line 2144, `["comprehend","DIRECTIVE","mint","GOAL"]` + content words) whenever they don't qualify for the experiment bundle — meaning the exact false-success-plus-dead-rule bug A25 found for `prog_read` is ALSO live, today, for any of those other concern kinds that reach this fallback. A working gate would fix them too; that this rung couldn't build one safely is a real, currently-unclosed cost, not merely a hypothetical. |
| `speech_enrollment.py` | docstring/comment only | n/a | n/a — no actual call, confirmed via import grep |

Net: **3 real, currently-tested, currently-relied-upon call sites would
break** (all via the identical mechanism: discard-the-return-value,
depend-on-the-installed-rule); **3 are already safe** (2 route elsewhere
entirely, 1 already checks `grounded` correctly and has a real fallback);
**1 (the daemon's generic path) is safe to change but is exactly the site
that shows the bug's blast radius is wider than `prog_read` alone.**

---

## 3. AR-H-d — the candidate gate, built, applied, and shown to break real tests

Per the prereg's requirement for live evidence over reasoning alone, the
most plausible candidate gate — the one piece of data that happened to
differ between the two examples compared early in this investigation
(`"decompose" in rp`, an accident of `arc_self_report`/`recount_faculty`
both including an isolated `"mint"` token in their two-clause template,
§1.4 already shows this doesn't generalise to prog_read's real shape
either) — was actually implemented, mirroring the file's own `if "find" in
rp:` style exactly:

```python
if "decompose" in rp:
    # ...(unchanged terminal rule body)...
    return {"grounded": True, ...}
return {"grounded": False, "path": "compose_comprehension_rule", "concern": list(keys),
        "grounded_relations": rels,
        "wall": "no describe/scene relation grounded for this concern shape"}
```

Applied to `domains/reflective_faculty.py` in this worktree and run
against the REAL test suite (not a hand-picked repro):

```
tests/test_composers_graph.py::test_structural_equivalence_comprehension_describe FAILED
    keys = ["eqc3"]; rels = [("comprehend", "X")]; rp = {"comprehend"}
    py_res = rf._compose_comprehension_rule(_fresh(), keys, rels)
    ...
>   assert py_res["form"] == gr_res["form"] == "comprehension_rule"
    KeyError: 'form'
```

A clean, structural failure — not a flaky timing issue, not an unrelated
environment gap. `rp = {"comprehend"}` (no `decompose`) is EXACTLY the
shape both a genuine minimal describe concern AND prog_read's real
production shape reduce to (§1.4) — this specific gate, chosen because it
was the only observed difference in the FIRST pair compared, still fails
the moment a third, differently-shaped-but-equally-legitimate case is
checked. This is the general finding, not a fluke of one bad guess: **any**
gate built from `rp` alone either admits prog_read (no fix) or excludes a
currently-tested legitimate case (regression). The change was reverted
before the worktree was left in its final state (`git diff` against `main`
on `domains/reflective_faculty.py` is empty — confirmed below).

---

## 4. AR-H-e — regression (unmodified tree; establishes the baseline any
future real fix would need to hold)

No code changed, so there is no "before" vs "after" to diff — the bar
here is: **is the current tree, unmodified, actually green on everything
this investigation determined matters**, so that (a) the NO-GO rests on a
real baseline, not an assumed one, and (b) a future fix attempt has a
concrete target to preserve. All runs below are on the clean,
post-revert tree (`git diff domains/reflective_faculty.py` against `main`
is empty), run serially, one command at a time, each capped
(`systemd-run --scope --user -p MemoryMax=6-8G`).

| file(s) | result | notes |
|---|---|---|
| `test_composers_graph.py` (full file) | **50 passed** | includes the exact test that broke under the candidate gate (§3) |
| `test_composer_driver_migrated.py` | **6 passed, 1 failed** | `test_ground_concern_dispatch_parity` — **pre-existing, unrelated**: diffed field-by-field against the frozen fixture; the ONLY differences for the `"comprehend"` case are `rule_uid`/`revision`/`content_hash` — provenance metadata the engine now stamps on installed rules that didn't exist when the fixture was frozen. `form`, `grounded`, `grounded_relations`, `path`, and the full rule body (`match`/`where`/`effects`) are byte-identical to the fixture. Not caused by, or related to, this investigation; nothing here was touched to make it pass or fail. |
| `test_prog_read_selfimprove_migrated.py` + `test_prog_synthesis_selfimprove_migrated.py` | **12 passed** | A25's own gate + its sibling — confirms this investigation touched nothing in the `code_write`/`prog_read` dedicated-routing paths (both explicitly off-limits per the task brief and never edited). Required symlinking `results/` (gitignored, absent from this fresh worktree checkout — `results/prog_construction_scan.json` missing) from the primary tree; once symlinked, 12/12 green. |
| `test_substrate_extension.py`, `test_conceptualizer.py`, `test_conceptualizer_monitor.py`, `test_gap_awareness_migrated.py`, `test_self_concern_promote_migrated.py` | **56 passed** | the "safe" callers from §2, plus the self-improvement promotion/gap-filing machinery this composer feeds into |
| `test_structured_find.py`, `test_rule_minting_dialect.py`, `test_browse_authoring.py`, `test_nl_concern_front_door.py` | **23 passed** | the `"find"`/`"find+constrain"` sibling branches and the NL front door into concern authoring |
| `test_recount_migrated.py::test_asking_to_recount_fires_the_faculty_not_a_gap`, `::test_rules_are_composer_authored_not_hand_written` | **2 passed** | the two tests most directly load-bearing for `build_recount_faculty`'s reliance on the unconditional terminal branch |

**Totals: 149 passed, 0 newly-failed, 1 pre-existing-and-explained failure**
across 14 files / ~150 collected test items directly touching
`ground_concern`/`_compose_comprehension_rule`/the composers it dispatches
to or the self-improvement machinery around it.

**What was not completed, and why (honest, not a gloss).** The FULL
`test_recount_migrated.py` file (12 tests) and its `_fluency` sibling could
not be run to completion: two full-file attempts ran 400s+ and 590s+
respectively without finishing, confirmed CPU-bound (not hung — stable
RSS well under the memory cap, 99%+ CPU continuously) and attributable to
sustained contention from a second, independent agent session's test
workers holding 4 cores pinned near 100% for the entire back half of this
session (verified via `ps aux`, not assumed). The two most load-bearing
individual tests from that file were run standalone and passed (above);
the file's OWN docstring plus source-reading of `build_recount_faculty`
(§2) already establish the mechanism independently of running the other
10 tests. A broader ~110-file grep-matched sweep (everything importing
`reflective_faculty` for any reason, most unrelated) was attempted before
the mid-session crash and is not reproduced here — it was the wrong scope
(too broad, too slow, and was running with more parallelism than this
box's other concurrent load could tolerate); the 14-file, ~150-item scope
above is the directly-relevant one and is what this document stands on.

---

## 5. What a real fix would need

Not "can't be done" — "can't be done inside this rung's scope, at this
call site, from this data." Two honest paths forward, neither attempted
here (both larger than a single `_compose_*_rule` builder edit):

1. **Persist and thread the literal directive word.** `induce_concern`
   would need to retain the observation's content word through its
   residual computation (or `sd_mint_quantum` would need to persist
   `observation` on the `CapabilityAxis` the way `ground_concern`'s dead
   `obs` read implies it once did), and `ground_concern` would need to
   pass it to `_compose_comprehension_rule`. This touches core dequantize-
   loop machinery (`induce_concern`, arguably the Rust `sd_mint_quantum`
   rule), not a builder — explicitly out of the sanctioned "`_compose_*_rule`
   builders only assemble Rule JSON" scope this rung operates under.
2. **Per-caller opt-in at the promotion layer**, mirroring A25's own fix
   exactly: give every concern KIND that currently falls through to the
   generic `comprehend_first`/`ground_concern` path (not just `prog_read`)
   its own dedicated routing check BEFORE it reaches the shared composer —
   the same shape `code_write` and `prog_read` already have. This doesn't
   touch the shared function at all (so it can never break `recount_faculty`
   or `build_describe_faculty`, which don't go through the daemon's
   promotion path); it closes the false-success-plus-dead-rule bug at
   every OTHER site named in §2's `_concern_tick` row (reply_fix,
   knowledge, self_account, instruction, performance, comprehension kinds)
   without needing a discriminator inside `_compose_comprehension_rule`
   at all.

Path 2 is the one this project's own precedent (A25) already validates as
safe and minimal; it was out of scope here only because the task brief
scoped this rung to the shared composer function itself, not the daemon's
per-kind routing table.

---

## 6. Reproduce

```bash
cd /home/matt/ocelot-ground-concern-honesty
git log --oneline -1                         # 4563c3a-based, branch ground-concern-honesty
git diff main -- domains/reflective_faculty.py   # empty — no code shipped
PYTHONPATH=runners/dsl/python:.:scripts \
  python3 -m pytest tests/test_composers_graph.py -q
```

To reproduce the candidate-gate breakage (§3): apply the `if "decompose"
in rp:` patch shown there to `_compose_comprehension_rule`'s terminal
block, then re-run
`tests/test_composers_graph.py::test_structural_equivalence_comprehension_describe`.

---

## 7. Worktree / commit

Worktree: `/home/matt/ocelot-ground-concern-honesty`, branch
`ground-concern-honesty`. `domains/reflective_faculty.py` unmodified from
`main`. Committed: this PREREG + RESULTS doc pair only. Not pushed; `main`
untouched.
