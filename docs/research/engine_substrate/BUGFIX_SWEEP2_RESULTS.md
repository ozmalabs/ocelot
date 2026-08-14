# BUGFIX SWEEP 2 — RESULTS

Per `BUGFIX_SWEEP2_PREREG.md`. Worktree
`/tmp/claude-1000/-home-matt-ozmadev-ocelot/272b6058-8f21-4012-b852-d8348df69ff4/scratchpad/bugfix-sweep2`,
branch `bugfix-sweep2`, off `main @ c87d065` (re-verified fresh
immediately before starting, per the task's own instruction not to trust a
cached hash).

**Honest headline, in one paragraph.** Two of the three items are FIXED,
both with a real live before/after demonstration and a byte-identical
regression signature against the documented historical baseline; the third
item's three sub-items are all DEFERRED — two because the original
`SHAPE_AUDIT_SWEEP2_RESULTS.md` sizing still holds with no new grounds to
reconsider, and one (`sd_recognize_dim`) because investigation found the
sizing itself was STALE — a prior, chronologically-earlier commit
(`dcea7ad`, "Dedup adoption sweep", 2026-08-12) already fixed the specific
defect `SHAPE_AUDIT_SWEEP2_RESULTS.md §7.2` described, with its own
reasoned, already-deferred residual, and `SHAPE_AUDIT_SWEEP2_RESULTS.md`
appears not to have read that commit's content (it says it read "v1.0.0
through v1.8.0"; the file has been at v1.9.0 since before SWEEP2 was
written). That correction is reported here rather than re-diagnosed.

---

## 1. `SynthesisOperatorShape` selection-layer Pattern-D bug — FIXED

**Location.** `seeds/program_synthesis_grounding.json`'s
`ps_select_synthesis_operator_shape` rule, both of its `set_attr` effects
(`ps_enum_ops`, `ps_enum_operator_shape`).

**The bug, demonstrated live before touching anything.** The two seeded
`SynthesisOperatorShape`s (`thresholded_greater_branch`,
`thresholded_lower_branch`) share six trigger tokens (`THAN`, `TIMES`,
`THRESHOLD`, `WHEN`, `OTHERWISE`, `ELSE`) against each shape's own
`minimum_trigger_matches: 5`. A message containing ONLY those six shared
tokens — no `MORE`/`GREATER`/`EXCEEDS`/`ABOVE` and no
`LESS`/`BELOW`/`UNDER`, i.e. zero directional evidence — scores 6 on BOTH
shapes and clears both thresholds. The rule's `Argmax` then resolves the
tie by "whichever candidate is encountered first" (graph iteration order
over `has_synthesis_operator_shape`), which is deterministically
`thresholded_greater_branch`. Live, before the fix:

```
text = "Write a function using threshold times than when otherwise else logic."
ps_tokens: ['USING','THRESHOLD','TIMES','THAN','WHEN','OTHERWISE','ELSE','LOGIC']
ps_enum_operator_shape: thresholded_greater_branch
ps_enum_ops: ('Times', 'Gt', 'IfThenElse')
```

A message with NO textual evidence for either direction is silently and
deterministically assigned `Gt` semantics. This is the same class of
defect `META_SHAPE_FIRST_CLASS_RESULTS.md` fixed for `recognise_meta_shape`
(raw keyword-count scoring, an unprincipled tiebreak) — independently
confirmed as a real, if secondary, alignment target by
`PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_REASSESSMENT_PREREG.md §1.3/§5.5`
("Rung 4 ... optional").

**The fix, scoped narrowly per the brief.** `ArgminUnique`
(`runners/dsl/src/term.rs:2039`, "`Argmin`, BUT IT CAN SAY NO") already
exists in the engine: identical fold to `Argmin`, except a tie at the
extremum returns `default` (here `null`) instead of an arbitrary tied
candidate. There is no `ArgmaxUnique` variant, so the two `Argmax` sites
were changed to `ArgminUnique` over the NEGATED match count
(`Neg(Count(...))`) — mathematically identical to "maximize, refuse on
tie," and reuses the exact `Attr(ArgminUnique(...), key)` idiom the engine
already documents as safe (`term.rs:2088-2094`, "at the 85 `Attr(sel,
key)` sites it is a bare `None`"). **Zero new Rust.** The mechanical
transform (Python script over the parsed JSON, verified to round-trip
byte-identically before any edit) touched exactly the two `"type":
"Argmax"` sites and their `"value"` subterms — `git diff --stat`: one file,
48 insertions / 42 deletions, no other seed touched.

On a genuine tie, both `set_attr` effects now evaluate to `None`; the
existing downstream fallback (`domains/prog_synthesis.py:1179-1181`, `if
graph_ops:`) already treats an unset/`None` `ps_enum_ops` as "no shape
selected," and falls back to `DEFAULT_OPS`/typed defaults — the exact
safety net `PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_REASSESSMENT_PREREG.md`
names as already in place. `ps_operator_shape_selected` still gets marked
`1` on a refusal (an honest "decided: nothing," not a retry loop).

**Live demo, after the fix — same three cases:**

```
AMBIGUOUS (no more/less cues):
  ps_enum_operator_shape: None
  ps_enum_ops: None                                  <- was thresholded_greater_branch/Gt

UNAMBIGUOUS greater cues (regression check):
  ps_enum_operator_shape: thresholded_greater_branch  <- byte-identical to before
  ps_enum_ops: ('Times', 'Gt', 'IfThenElse')

UNAMBIGUOUS less cues (regression check):
  ps_enum_operator_shape: thresholded_lower_branch    <- byte-identical to before
  ps_enum_ops: ('Times', 'Lt', 'IfThenElse')
```

Verified by literally swapping the file back to `HEAD`'s pristine content
and re-running the same three probes in the same worktree — the two
unambiguous cases are byte-identical before/after; only the genuinely
ambiguous case changes, from a silent wrong pick to an honest refusal.

**Regression.**

| suite | before (pristine) | after (fixed) |
|---|---|---|
| `test_jabberwock_threshold_classifier_migrated.py` + `test_program_synthesis_grounding_migrated.py` (the only two files referencing `SynthesisOperatorShape`/this rule) | 6 passed | 6 passed |
| named 9-file MBPP suite | — | 3 failed, 241 passed (see §4, identical to the documented historical baseline) |

No MBPP task's live outcome changed (confirmed by the named-suite run in
§4 — the same 3 pre-existing failures, no new ones).

**Status: FIXED.** Commit `9365017`.

---

## 2. Task 242 retrieval-ceiling drift — FIXED (re-pinned, 3 ids not 1)

**What was actually live, not just task 242.**
`test_ceiling_task_reproduces_measured_outcome_live` was red for **three**
of the twelve `CEILING_TASK_IDS`: `106`, `115`, `242` — confirmed with
three repeated live runs, byte-identical each time. This test is not part
of the program-synthesis "named 9-file suite" (it is invoked only as a
subprocess by two other files' own meta-tests), which is exactly why
`PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_RUNG1_RESULTS.md §6` (2026-08-11)
first flagged task 242's drift, explicitly declined to resolve it
("not independently confirmed correct or incorrect... requiring its own
review"), and it sat unreviewed across two further merged rungs
(`progsyn-setlit-dictitems`, `progsyn-dictitems-sortby`) without anyone
re-verifying the leaf test itself.

**The live facts, read directly:**

| id | task | before (pinned) | after (live, now pinned) |
|---|---|---|---|
| 242 | count characters in a string | `gapped` / `rung d` / exemplar 776 (`_KNOWN_S2_STRUCTURAL_REJECT_DRIFT`) | `gapped` / `rung none` / `gap_reason: enumerate_failed` |
| 106 | append list to tuples | `gapped` / `enumerate_failed` / `rung none` (`_KNOWN_ARC6_TIER0_ENUM_REACH_DRIFT`, itself already a superseding pin) | `accepted` / `rung b` / exemplar 750 / `holdout_ok: True` |
| 115 | (the `TypeError` set-value case) | `{"exc": "TypeError"}` | `accepted` / `rung a` / exemplar 741 / `holdout_ok: True` |

**The call, evidence-based, per the brief's three options.** None of the
three is "chase further" or "redesign the test" — this is
"fine, re-pin to the current measured state," for a specific reason in
each direction:

- **242 stays honestly gapped, both before and after — only the
  MECHANISM moved.** Before, the retrieval ladder reached rung `d`
  (exemplar 776 adapted into a candidate the already-landed S2
  structural-verdict rung correctly rejected as wrong-in-general). Now,
  the plain `SynthEnumerate` rung — upstream of retrieval in the Occam
  ladder — proposes its OWN candidate first:
  `fold(items, x, acc, init=0, body=acc+1)`, a syntactically plausible
  length-count. That candidate fails its own row verdict, because a
  string is STILL atomic in this engine (`STRUCTURAL_CEILING.md §3.1`'s
  S1 finding — `fix:StringAsSequence` has not landed — `Fold` over a
  string iterates zero times), which terminates the whole ladder as
  `enumerate_failed` before retrieval is ever reached. Both mechanisms are
  honest failures on a task this engine genuinely cannot yet solve; which
  one gets there first is exactly the Occam-order reshuffling a primitive-
  layer widening (rung 1's ten Tier-1 Terms) is expected to cause. No
  wrong-accept direction change — nothing to chase.
- **106 and 115 moved FURTHER than their own already-superseded pins, in
  the improvement direction, via a real mechanism check.** `rung` is set
  ONLY inside `domains/prog_retrieval.py` (`pr_rung_reached`, grepped:
  every call site is in that one file) — so `rung: "b"`/`rung: "a"` here
  means the RETRIEVAL ladder itself reached those rungs, not the plain
  enumerator mislabeled. 115's `TypeError` is resolved by the already-
  merged `progsyn-setlit-dictitems` rung's `Lit` set/frozenset-boundary
  fix (named but not built as of `STRUCTURAL_CEILING.md §7.4`, landed
  since).

**Deliberately NOT done, named instead of asserted.** Whether 106's and
115's new `holdout_ok: True` accepts are GENUINE captures — as opposed to
a coincidental fit the single held-out row cannot catch, task 394's own
already-documented precedent in this same file, which needed a
CONSTRUCTED counter-example witness to settle — was not independently
re-verified by that same construction method here. This entry pins only
the live, measured outcome; it deliberately does not touch
`CAPTURED_TASK_IDS` or any MBPP headline count. That is a materially
bigger claim than a live re-pin and belongs to a dedicated follow-on rung
(the same method `test_reject_informs_repair_migrated.py`'s
`test_task_92_and_464_frozen_passes_were_already_coincidental_fits`
already uses), not this one.

**The fix.** A new documented drift dict,
`_KNOWN_BUGFIX_SWEEP2_RUNG1_CASCADE_DRIFT`, checked FIRST in the test's
own `if`/`elif` chain — mirroring the file's own established precedent
(four prior instances: `_KNOWN_S4_DRIFT`, `_KNOWN_S2_STRUCTURAL_REJECT_DRIFT`,
`_KNOWN_ARC6_PROPERTY_REJECT_DRIFT`, `_KNOWN_ARC6_TIER0_ENUM_REACH_DRIFT`).
`MEASURED_OUTCOMES` itself is untouched.

**Regression.**

| | before fix | after fix |
|---|---|---|
| `test_ceiling_task_reproduces_measured_outcome_live` (12 ids) | 3 failed, 9 passed | **12 passed** |
| `tests/test_retrieval_migrated.py` (full file) | 3 failed, 31 passed | **34 passed** |
| named 9-file MBPP suite (subprocess-invokes this file) | 9 failed inside the subprocess (6 pre-existing + 106/115/242), top-level 3 failed / 241 passed | 6 failed inside the subprocess (the 6 pre-existing only), **top-level 3 failed / 241 passed, byte-identical to the documented historical baseline** (`test_three_runnable_tasks_reverify_live`, `test_prog_moves_migrated.py::test_named_regression_sweep_only_known_pins_drift`, `test_exact_first_migrated.py::test_named_regression_sweep_only_known_pins_drift` — same 3 names as `PROGRAM_SYNTHESIS_DICTITEMS_SORTBY_RESULTS.md §6`'s own independently-run clean-`main` baseline) |

The two named-9-file-suite meta-tests still fail — but now ONLY because of
the four `test_mbpp_arc3_endgame_migrated.py` ids (the pre-existing,
already-diagnosed "shared mutable output path" fragility,
`PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_RUNG1_RESULTS.md §6`, unrelated to
anything in this rung and explicitly out of scope here) — confirmed by
reading the subprocess's own failure list before and after, not inferred.

**Status: FIXED.** Commit `802a47b`.

---

## 3. `SHAPE_AUDIT_SWEEP2_RESULTS.md`'s three sized-not-fixed items — DEFERRED (all three), one with a corrected record

### 3.1 `information_commitment`'s unweighted sum — still correctly deferred

Re-grepped all four call sites: `domains/teach.py:203`,
`domains/proposal_install.py:313`, `domains/fetch_dispatch.py:524`,
`domains/voice_world.py:676` — byte-identical line numbers and literal
values (`2.0`/`10.0`/`0.0`/`1.0`) to `SHAPE_AUDIT_SWEEP2_RESULTS.md §5`'s
own citation. Nothing has changed since that sizing. Its stated reason for
deferring — *"a genuine fix requires answering a substantive value-
alignment question this rung has no basis to answer unilaterally"* — is a
judgment call about who gets to set relative cross-subsystem weights, not
a stale technical fact, and this rung found no new grounds to override
that judgment. Attempting a "fix" here would mean asserting a replacement
scalar exactly as arbitrary as the four it would replace, which
`SHAPE_AUDIT_SWEEP2_RESULTS.md` already correctly names as WORSE than the
status quo ("this gate gaining a wrong weighting would be WORSE than
today's inconsistency, because it would look principled while still being
asserted"). **No code changed. Status: DEFERRED, reasoning re-confirmed.**

### 3.2 `sd_recognize_dim` per-observation minting — the record needed correcting, not the code

**What `SHAPE_AUDIT_SWEEP2_RESULTS.md §7.2` claims:** "no dedup guard on
`LatentDimension` at all" against a mint keyed only by a per-observation
`has_transform`-edge guard, and names three test files
(`test_stereo_infer_migrated.py`, `test_time_infer_migrated.py`,
`test_depth_infer_migrated.py`) as at-risk consumers of the resulting
`[0]`-indexing fragility. It explicitly states it read
`seeds/shape_decode_loop.json`'s "full accretion history (v1.0.0 through
v1.8.0)."

**What is actually true of the file the audit ran against, checked
directly:** `seeds/shape_decode_loop.json`'s current `version` field is
`1.9.0`, and commit `dcea7ad` ("Dedup adoption sweep: two real fixes, and
the reason 'adopt it more widely' is wrong," 2026-08-12) — chronologically
BEFORE `SHAPE_AUDIT_SWEEP2_RESULTS.md`'s own commit (`4ab9154`,
2026-08-14) and an ancestor of both that commit and this rung's base —
already changed `sd_recognize_dim`'s `LatentDimension` mint from
`add_node` to `add_node_if_absent`, citing "SHAPE_AUDIT 4.4's canonical
scope error" by name and measuring the fix directly: "3 observations of
one rotated shape -> 3 byte-identical nodes, now 1." **The dedup guard
SWEEP2 says doesn't exist, exists, and predates SWEEP2's own investigation
by two days.**

`dcea7ad` also already named, and reasonedly deferred, the ONE remaining
residual: the dedup key is (`name`, `generator`, `k`, `generators`, `ks`,
`source`) — the AUTHOR attrs `add_node_if_absent` matches on — so the SAME
generator recognized at a DIFFERENT `k` still mints a second node. Its own
stated reason for not fixing this further: *"the `k` belongs on the
Transform (where it already is), not on the dimension, but moving it off
the `LatentDimension` would break readers that assert `ld.k`."* Verified
this reason is still accurate, not stale: `grep`, `tests/test_dimension_
inference_migrated.py:271,477,558` all read `ld_at.get("k")` directly off
a `LatentDimension` node's own attrs. Moving `k` off that node today would
break three live assertions. **No new grounds found to override `dcea7ad`'s
own deferral of this specific residual.**

**Separately, the three test files SWEEP2 cites as at-risk `[0]`-indexing
consumers are not consumers of `sd_recognize_dim` at all.** Their
`latent:depth`/`latent:time` `LatentDimension` mints come from
`seeds/depth_axis.json`/`seeds/time_axis.json` — seeds entirely SEPARATE
from `seeds/shape_decode_loop.json` (confirmed: `grep -rl "n_layers"
seeds/*.json` returns `depth_axis.json`/`time_axis.json`, not
`shape_decode_loop.json`), with their own attribute shape (`n_layers`,
`velocities`, `ordering`, `window` — not the generic `generator`/`k` pair
`sd_recognize_dim` mints). Whether THESE seeds have their own independent
per-observation duplicate-mint story is a genuinely separate question this
rung did not investigate (it would be a new audit item, not a
re-assessment of an existing one) — named here so a future reader does not
inherit SWEEP2's mis-attribution.

**Status: DEFERRED — no code changed (the specific residual `dcea7ad`
already named is still correctly deferred for the same, re-verified
reason), but `SHAPE_AUDIT_SWEEP2_RESULTS.md §7.2`'s characterization is
STALE and should be read as corrected by this section: the dedup guard
exists (since 2026-08-12), the cited test files are not at risk from
`sd_recognize_dim` specifically, and the one real remaining residual
(same-generator-different-`k` duplication) was already found and
reasonedly deferred by the commit that fixed the rest of it.**

### 3.3 `stroke_codebook.py:82` `DEFAULT_DTW_THRESHOLD=0.15` — still correctly deferred

Re-read in place: byte-identical value, byte-identical calibration
comment (realistic jitter ≈0.108, a genuinely different shape class ≈0.50,
unrelated noise 0.21–0.39, regression history at a prior `0.35` default)
to `SHAPE_AUDIT_SWEEP2_RESULTS.md §7.3`'s own citation. Its reasoning —
replacing this with a genuine MDL-derived coverage criterion for a DTW
distance is "new machinery, not a same-rung parameter change," because DTW
has no native bit-cost the way `ShapeDecode`'s relation-set cover does —
is unchanged and this rung found no new grounds to reconsider it.
**No code changed. Status: DEFERRED, reasoning re-confirmed.**

---

## 4. Full regression summary

All paired/independent comparisons this rung ran, consolidated:

| item | suite | before | after |
|---|---|---|---|
| #1 SynthesisOperatorShape | `test_jabberwock_threshold_classifier_migrated.py` + `test_program_synthesis_grounding_migrated.py` | 6 passed | 6 passed |
| #2 test_retrieval_migrated | `test_ceiling_task_reproduces_measured_outcome_live` (12 ids) | 3 failed, 9 passed | 12 passed |
| #2 test_retrieval_migrated | full file (34 tests) | 3 failed, 31 passed | 34 passed |
| #1 + #2 combined | named 9-file MBPP suite | (pre-fix: 9 failures inside subprocess) | **3 failed, 241 passed — byte-identical failing-test-name set to the documented historical baseline** (`PROGRAM_SYNTHESIS_DICTITEMS_SORTBY_RESULTS.md §6`'s independently-run clean-`main` numbers) |
| (context only, unchanged by this rung) | `test_reject_informs_repair_migrated.py` | — | 4 failed, 18 passed — the same 4 pre-existing ids `PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_RUNG1_RESULTS.md §6` already named, confirmed still present, not touched by this rung's scope |

**No regression was introduced by either fix.** The named-suite's 3
top-level failures are the exact same 3 test names the project's own
independently-run clean-`main` baseline already carries
(`test_three_runnable_tasks_reverify_live`'s task-267 construction drift,
and the two `test_named_regression_sweep_only_known_pins_drift` meta-tests
— which now fail solely because of the pre-existing, unrelated
`test_mbpp_arc3_endgame_migrated.py` shared-mutable-path fragility, not
because of anything this rung touched).

---

## 5. Per-item status summary

| # | item | status |
|---|---|---|
| 1 | `SynthesisOperatorShape` selection-layer Pattern-D bug | **FIXED** (`9365017`) |
| 2 | Task 242 retrieval-ceiling drift | **FIXED** — re-pinned 3 ids (106, 115, 242), not just 242 (`802a47b`) |
| 3.1 | `information_commitment` unweighted sum | DEFERRED, reasoning re-confirmed, no new grounds |
| 3.2 | `sd_recognize_dim` per-observation minting | DEFERRED — record corrected: partially already fixed (`dcea7ad`, pre-dates SWEEP2), remaining residual already reasonedly deferred, cited test files misattributed |
| 3.3 | `stroke_codebook.py` `DEFAULT_DTW_THRESHOLD` | DEFERRED, reasoning re-confirmed, no new grounds |

**GO** for items 1 and 2 (both fixed, both demonstrated live, both
regression-clean against the documented historical baseline). Item 3 is
correctly all-DEFER per the brief's own explicit allowance for a
well-reasoned "still not worth it" outcome — two sub-items needed no new
work, and the third needed a correction to the record rather than a code
change.

---

## 6. What this document does NOT establish

1. Whether 106's and 115's new retrieval-path accepts (§2) are GENUINE
   captures, as opposed to a coincidental fit the single held-out row
   cannot catch (task 394's own documented precedent in this same file) —
   not independently verified by a constructed counter-example witness
   here. `CAPTURED_TASK_IDS`/the MBPP headline count are deliberately
   untouched.
2. Whether `seeds/depth_axis.json`/`seeds/time_axis.json` (§3.2) have
   their own independent per-observation duplicate-mint story — found to
   be OUT OF SCOPE for `sd_recognize_dim`'s residual, not investigated as
   their own question.
3. Whether the `test_mbpp_arc3_endgame_migrated.py` shared-mutable-output-
   path fragility (unaffected by this rung, confirmed present before and
   after both fixes) should itself be fixed — named, not built, exactly as
   `PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_RUNG1_RESULTS.md §6` already left
   it for the orchestrator.
4. Whether `ArgminUnique`'s tie-refusal behavior (item 1) is the RIGHT
   long-term shape for operator-shape selection generally, versus a fuller
   `Covers`/`AntiUnifyWitness`-based structural match — this fix deletes
   the specific unprincipled tiebreak, exactly the brief's narrow mandate;
   it does not redesign the two-shape selector into a growable codebook
   (`PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_REASSESSMENT_PREREG.md §5.5`'s
   own "Rung 4" full recognize/mint proposal remains unbuilt).
5. Whether either fix moves the MBPP headline pass count — neither item
   was expected to (the reassessment doc's own words: "no MBPP task
   currently fails FOR THIS REASON" for item 1; item 2 is test-pin
   maintenance, not engine behavior) and this document does not claim it
   does.

## 7. Worktree / commits

- Worktree: `/tmp/claude-1000/-home-matt-ozmadev-ocelot/272b6058-8f21-4012-b852-d8348df69ff4/scratchpad/bugfix-sweep2`
- Branch: `bugfix-sweep2`, off `main` at `c87d065`
- Commits (oldest to newest):
  1. `2b573b7` — Prereg
  2. `9365017` — #1 `SynthesisOperatorShape` Argmax-tiebreak fix
  3. `802a47b` — #2 `test_retrieval_migrated` re-pin (3 ids)
- Not merged to `main`, per house discipline.
