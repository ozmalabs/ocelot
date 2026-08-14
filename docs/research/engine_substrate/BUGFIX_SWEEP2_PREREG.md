# BUGFIX SWEEP 2 — PREREG

Base `main @ c87d065` ("Merge progsyn-dictitems-sortby: DictItems + SortBy
Terms, MBPP 61->62 (task 475), GO") — verified fresh via `git log --oneline
-1 main` immediately before creating the worktree (re-verified per this
task's own instruction not to trust a cached hash; no `bigville_*`/
`solver_dispatch.py`/`problem_shape.py` files touched by anything below).

Worktree: `/tmp/claude-1000/-home-matt-ozmadev-ocelot/272b6058-8f21-4012-b852-d8348df69ff4/scratchpad/bugfix-sweep2`,
branch `bugfix-sweep2`, detached at `c87d065` then branched. `data/`
symlinked to the canonical tree's real directory (confirmed
`data/wiktionary/en.jsonl.gz` resolves to the real 470M file, not a partial
nested directory). No `git stash` used anywhere in this task.

**House-discipline note on `results/`:** confirmed the primary tree
currently carries an UNCOMMITTED, MODIFIED
`runners/dsl/python/substrate_rs/_native.abi3.so` (different sha256/size
than the committed `c87d065` blob) — almost certainly a stray rebuild from
the concurrent sibling solver-focused agent this task's brief warned about.
`git worktree add --detach c87d065` correctly checked out the COMMITTED
`.so`, not that dirty one, so this worktree's engine is exactly `c87d065`'s
own, not contaminated by concurrent work. Nine gitignored `results/*.json`
artifacts + `mbpp_endgame.json` were copied from the primary tree into this
worktree (the same documented "worktree-provisioning gap, not a code
defect" `PROGRAM_SYNTHESIS_DICTITEMS_SORTBY_RESULTS.md §7` already named) —
content-only copies of frozen, regenerable artifacts, never code.

---

## Items being attempted, in the mandated priority order

### 1. `SynthesisOperatorShape` selection-layer Pattern-D bug

**Location, read in full:** `seeds/program_synthesis_grounding.json`'s
`ps_select_synthesis_operator_shape` rule (`local_id` 1/2 nodes = the two
`SynthesisOperatorShape`s, `thresholded_greater_branch` /
`thresholded_lower_branch`). The rule's two `set_attr` effects each embed an
`Argmax` Term over `Filter(Neighbours(agent, has_synthesis_operator_shape),
shape, Gte(matched_trigger_count, shape.minimum_trigger_matches))`, scored
by raw trigger-token match COUNT — the identical shape
`META_SHAPE_FIRST_CLASS_RESULTS.md` diagnosed and fixed for
`recognise_meta_shape` (raw keyword-count scoring, arbitrary tie
resolution), confirmed independently by
`PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_REASSESSMENT_PREREG.md §1.3/§5.5`
("Rung 4 (selection layer, independent, lower priority, optional)").

**The concrete bug, found by reading the two shapes' own token sets, not
asserted:** the two shapes share SIX trigger tokens (`THAN`, `TIMES`,
`THRESHOLD`, `WHEN`, `OTHERWISE`, `ELSE`) against each shape's own
`minimum_trigger_matches: 5`. A message containing ONLY the six shared
tokens — no `MORE`/`GREATER`/`EXCEEDS`/`ABOVE` AND no `LESS`/`BELOW`/
`UNDER`, i.e. a message with NO directional evidence at all — scores 6 on
BOTH shapes, both clear their own threshold, and `Argmax`'s tie-break is
"whichever is encountered first" (graph iteration order over
`has_synthesis_operator_shape` neighbours) — today that is always
`thresholded_greater_branch` (`local_id 1`), so a completely
direction-ambiguous request is silently and deterministically assigned
`Gt` semantics with zero textual justification. This is a real correctness
risk (same class as `recognise_meta_shape`'s alphabetical tie), even though
the reassessment doc's own finding stands: no currently-passing MBPP task
depends on this path firing today (2 shapes, narrow trigger sets, no cited
blocker in `STRUCTURAL_CEILING.md`'s 42-task ledger names it).

**Initial read on the fix, scoped NARROWLY per the brief.** The precedent
(`META_SHAPE_FIRST_CLASS_RESULTS.md`) is "score the item's own signature,
delete the tiebreak." This rung does NOT need a new Rust Term to do that:
`ArgminUnique` (`runners/dsl/src/term.rs:2039`) already exists — "`Argmin`,
BUT IT CAN SAY NO": identical fold to `Argmin`, EXCEPT a tie at the extremum
returns `default` (here: `null`) instead of an arbitrary tied candidate.
There is no `ArgmaxUnique` variant, but negating the value function
(`Neg(Count(...))`) and switching `Argmax` → `ArgminUnique` is
mathematically identical to "maximize count, refuse on tie" and reuses
`ArgminUnique` exactly as already proven safe elsewhere (`Attr(ArgminUnique(...),
key)` is an existing, documented idiom — "at the 85 `Attr(sel, key)` sites
it is a bare `None`", `term.rs:2088-2094`). **Zero new Rust, seed-JSON-only
change**, staying inside this rung's "close a real drift-risk bug, not
redesign the operator-selection system" mandate. On an honest tie, the two
`set_attr` effects both evaluate to `None`; downstream
(`domains/prog_synthesis.py:1179-1181`, `if graph_ops:`) already treats an
unset/`None` `ps_enum_ops` as "no shape selected" and falls back to the
existing `DEFAULT_OPS`/typed-default path — the SAME safety net the
reassessment doc names as already in place. `ps_operator_shape_selected`
still gets marked `1` on a refusal (an honest "decided: nothing", not a
retry loop) — matches the file's own idempotency-guard shape.

If, once inside the JSON, this needs more than swapping `Argmax` →
`ArgminUnique(Neg(...))` in the two `set_attr` effects, I will stop and
report rather than widen scope.

### 2. Task 242 retrieval-ceiling drift

**Read `tests/test_retrieval_migrated.py` in full first.** Confirmed live
(this worktree, `c87d065`, three repeated runs, byte-identical):
`test_ceiling_task_reproduces_measured_outcome_live` is RED for **three**
of the twelve `CEILING_TASK_IDS`, not just 242 — `106`, `115`, `242` all
mismatch their currently-pinned expectation. This test is NOT one of the
"named 9-file suite" files (`test_retrieval_migrated.py` is invoked only as
a subprocess by two OTHER files' meta-tests), which is exactly why it has
sat red since `PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_RUNG1_RESULTS.md`
(2026-08-11) first flagged 242's drift and it was never independently
re-verified or re-pinned across the two subsequent merged rungs
(`progsyn-setlit-dictitems`, `progsyn-dictitems-sortby`).

**What's actually live, read directly, not inferred:**
- **242** (`count total characters in a string`): `status: gapped`,
  `gap_reason: enumerate_failed`, `rung: none`, `exemplar: None` — was
  pinned `gapped`/`rung: d`/`exemplar: 776` (`_KNOWN_S2_STRUCTURAL_REJECT_DRIFT`).
  Still honestly gapped both before and after — no wrong-accept direction
  change — but the retrieval ladder no longer even reaches rung `d`.
- **106** (`append list to tuples`): `status: accepted`, `rung: b`,
  `exemplar: 750`, `holdout_ok: True` — was pinned
  `gapped`/`enumerate_failed`/`rung: none`
  (`_KNOWN_ARC6_TIER0_ENUM_REACH_DRIFT`, itself already a superseding pin
  from an EARLIER drift). This is a further, IMPROVEMENT-direction drift on
  top of an already-superseded pin.
- **115** (the `TypeError` set-value case): `status: accepted`, `rung: a`,
  `exemplar: 741`, `holdout_ok: True` — the `Lit` set/frozenset boundary
  fix (`progsyn-setlit-dictitems`, already merged to `main`) resolved the
  underlying `TypeError`, so this task no longer raises at all.

**Initial read.** All three moves are in the SAME family the file has
reconciled four times already (`_KNOWN_S4_DRIFT`, `_KNOWN_S2_STRUCTURAL_REJECT_DRIFT`,
`_KNOWN_ARC6_PROPERTY_REJECT_DRIFT`, `_KNOWN_ARC6_TIER0_ENUM_REACH_DRIFT`) —
a primitive-layer widening (Rung 1's ten Tier-1 Terms, then the
setlit/dictitems/sortby rungs) changing which rung of the Occam ladder
fires first for a specific pinned id, with the file's own documented
per-id-drift-dict mechanism existing exactly to absorb this. None of the
three moves is a wrong-accept regression (242 stays honestly gapped; 106
and 115 move honest-gapped/error → accepted+holdout_ok=True, the
IMPROVEMENT direction the file's own house style privileges). This reads as
"fine, re-pin to the current measured state" rather than "chase further" or
"redesign the test" — the test's own per-drift-dict design is working
exactly as intended (it caught three genuine behaviour changes; the gap is
that nobody closed the loop on the ALREADY-NAMED one, and two siblings
piggy-backed on the same underlying cause). I will NOT touch
`CAPTURED_TASK_IDS`/the phase-headline count — whether 106/115's new
accepts are genuine (vs. `394`'s already-documented coincidental-fit
precedent, which needed a constructed counter-example witness to settle) is
a materially bigger claim than a live-outcome re-pin and is out of this
item's scope; I will name it for the orchestrator instead of asserting it.

### 3. Re-assessment of `SHAPE_AUDIT_SWEEP2_RESULTS.md`'s three sized-not-fixed items

Read the full RESULTS doc first (already done for this prereg). Initial
reads on each, to be confirmed or corrected during execution:

- **`information_commitment` unweighted sum (§5 of that doc).** Grepped the
  four call sites (`domains/teach.py:203`, `domains/proposal_install.py:313`,
  `domains/fetch_dispatch.py:524`, `domains/voice_world.py:676`) — byte-
  identical line numbers and values to SWEEP2's own citation. The original
  reasoning ("a value-alignment decision this rung shouldn't make
  unilaterally") is a judgment call about WHO gets to set relative weights
  across four independent subsystems, not a stale technical fact — nothing
  found so far changes that. **Initial call: still correctly deferred.**
- **`sd_recognize_dim` per-observation minting (§7.2).** Reading
  `seeds/shape_decode_loop.json`'s CURRENT top-level `version` (1.9.0, not
  the "v1.0.0 through v1.8.0" SWEEP2 says it read) surfaces something SWEEP2
  itself appears to have missed: `dcea7ad` ("Dedup adoption sweep", landed
  2026-08-12, an ANCESTOR of both SWEEP2's own base and this rung's base)
  already changed the `LatentDimension` mint from `add_node` to
  `add_node_if_absent`, WITH a reasoned, already-deferred residual
  (same-generator-different-`k` still mints a second node,
  "moving `k` off `LatentDimension` ... is its own rung"). SWEEP2's
  characterization ("no dedup guard on `LatentDimension` at all") reads as
  stale against the worktree it actually ran in. Separately, the three test
  files SWEEP2 cites as at-risk consumers (`test_stereo_infer_migrated.py`,
  `test_time_infer_migrated.py`, `test_depth_infer_migrated.py`) mint their
  `latent:depth`/`latent:time` nodes via `seeds/depth_axis.json`/
  `seeds/time_axis.json` — SEPARATE seeds from `shape_decode_loop.json`,
  not consumers of `sd_recognize_dim` at all. **Initial call: the
  characterization needs correcting in the RESULTS doc; the underlying
  `sd_recognize_dim` residual dcea7ad already named and deferred is not,
  on current evidence, newly safe to fix in this rung — re-verify during
  execution, but expect DEFER with a corrected record, not a code change.**
- **`stroke_codebook.py:82` `DEFAULT_DTW_THRESHOLD=0.15` (§7.3).** Re-read
  in place — byte-identical to SWEEP2's own citation (same value, same
  calibration comment, same cited regression history at `0.35`). The
  reasoning (needs a genuine MDL-derived coverage criterion for a DTW
  distance, "new machinery, not a same-rung parameter change") is
  unchanged. **Initial call: still correctly deferred.**

---

## What this prereg does NOT establish

Matching every prior rung's own discipline: nothing below this line has
been built yet. The three "initial calls" above are read-only judgments
formed before touching any file and may be revised (in either direction) by
what execution actually finds — any revision will be reported honestly in
the RESULTS doc, not silently reconciled to match this prereg.
