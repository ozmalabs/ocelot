# `gapped:enumerate_failed` / budget-exhausted bucket survey — RESULTS: reframing landed, `Mod`/`Sqrt` built and measured, NO-GO on the build (real regression), code reverted

Prereg: `PROGRAM_SYNTHESIS_BUDGET_EXHAUSTED_SURVEY_PREREG.md`, same
worktree/branch. Base `main @ 78afd81` ("Merge
progsyn-structural-reject-survey: NO-GO, property-reject fallback pattern
ported and measured, zero conversions"), verified fresh via `git log
--oneline -1 main` before creating the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/progsyn-budget-exhausted-survey`,
branch `progsyn-budget-exhausted-survey` — **not merged to `main`, not
pushed**, left for the orchestrator to independently verify per this
session's explicit instruction.

---

**HEADLINE: the population reframing (§4 of the PREREG) is the durable
finding of this rung and stands independent of the build decision below —
24% of the 82-task budget-exhausted population (20 tasks) is NOT "the
search never found anything," it is "the search found a wrong candidate
cheaply, a downstream verdict correctly rejected it, and the RETRY
exhausted budget" — the same information-theoretic floor this arc's
`STRUCTURAL_REJECT_SURVEY`/`PROPERTY_REJECT_SURVEY` already NO-GO'd, one
level upstream. The remaining 62 tasks are genuine first-attempt
zero-recall gaps, and `Mod`/`Sqrt` — both already-shipped, already-wired
`TermNode` variants absent from `OP_TABLE` entirely, with four
independently live-verified (revealed AND held-out) witnesses (77, 435,
246, 293) — were BUILT, scoped as narrowly as this arc's own Rung-1
precedent taught it to (confined to the bare-scalar branch, structurally
disjoint from the list-shaped branch that carries task 132), and
MEASURED. Result: real, honest NO-GO. The build converts 4 tasks on the
`full`/`content_stripped` arms (92, 171, 246, 435) but ALSO regresses 4
DIFFERENT currently-passing tasks (59, 135, 138, 406) on those same arms
— net task-id churn, not a superset, at equal headline count (73→73,
72→72) — and nets -2 on the `official` arm (99 vs. the 101 baseline, 4
gained / 6 lost). Two DISTINCT regression mechanisms were found and
traced to their exact cause (§5): (a) search-cost inflation WITHIN the
same narrow bare-scalar branch this rung's own PREREG scoped the change
to (task 14, 164 on the `official` arm — adding two ops increases
per-size branching enough to push an already-reachable formula out of the
200,000-candidate budget); (b) a cross-lane reach the PREREG's own
regression pricing did not anticipate needing to check — `domains/
prog_moves.py`'s structural-moves/decomposition probe
(`intermediate_candidates`/`_run_synth_enumerate`) invokes the SAME
Rust-internal typed-default routing this rung's change touched, so
widening the bare branch also widens what THAT probe proposes, silently
changing which candidate a `retrieved_exemplar` hole-filler accepts for
several already-correctly-solved tasks. **The code has been reverted; the
worktree's `synth_enumerate.rs` is byte-identical to `main @ 78afd81`,
confirmed via `git diff --stat`.**

---

## 1. What was measured before any build decision (PREREG §1-6, unchanged, re-confirmed here)

Live baseline, re-confirmed fresh in this worktree, byte-identical to the
task brief's own cited figures and to the PREREG's own §1:

```
full:              73/257  content_stripped: 72/257  official: 101/257
```

`gapped:enumerate_failed`/budget-exhausted: **82 tasks**, byte-identical to
the task brief's cited count and to `CEILING_REASSESSMENT_4`'s original
82. Zero Dict-shaped (the task brief's exclusion instruction confirmed
moot for this specific population). Split by spec shape: 39 list-shaped,
34 bare-scalar, 9 pure-string, 0 set/dict-shaped.

**The central reframing (PREREG §4), reconfirmed unchanged**: a
call-tracing probe substituting a thin proxy for `sub._inner` (recording
every `SynthEnumerate` call's `exclude` length and result before
delegating to the real native `evaluate`) shows **20 of the 82 tasks (24%,
"Group A") already find a real, cheap candidate that fits every revealed
row on an EARLY search attempt, which then gets excluded (by a downstream
verdict, not re-traced to its exact rule) before a RETRY exhausts the
200,000-candidate budget** — this is architecturally the SAME
"underdetermined-by-1-3-rows" floor `STRUCTURAL_REJECT_SURVEY_RESULTS.md`
§4 already characterized and measured a 0/10 conversion rate for, one
level upstream (rejected-before-terminal-`gapped` rather than
terminal-`gapped`-itself). **62 of the 82 ("Group B") are genuine
first-attempt zero-recall gaps** — no candidate is ever proposed, at any
budget, in any trace. Only Group B is a plausible primitive-availability
target.

**The missing-primitive finding (PREREG §5), reconfirmed unchanged**:
`Mod`, `Pow`, `Sqrt`, and all six bitwise ops (`BitAnd`/`BitOr`/`BitXor`/
`Shl`/`Lshr`/`Ashr`) exist as fully-evaluated `TermNode` variants
(`term.rs`) but appear in NEITHER `OP_TABLE` NOR any typed-default bucket
in `synth_enumerate.rs` — confirmed by direct `grep`+read, and
independently corroborated by the module's own pre-existing source comment
(`synth_enumerate.rs:2737`, unprompted by this survey): *"the pool has
`{+, -, *}` and no `Mod`, so a DIVISIBILITY quantifier is not reachable
here."*

**Two clusters, four witnesses, hand-verified against revealed AND
held-out rows using ONLY already-shipped Terms**, reconfirmed unchanged
from the PREREG (§5.2-5.3):

```
77  (divisible by 11):     Eq(Mod(a,11), 0)                       — 3/3 rows exact
435 (last digit):          Mod(a,10)                               — 3/3 rows exact
246 (babylonian sqrt):     Sqrt(a)                                 — 3/3 rows exact
293 (right-triangle side): Sqrt(Plus(Times(a,a), Times(b,b)))      — 3/3 rows exact
```

75/426 (also `Mod`-shaped, but needing a SEPARATE change to
`filter_templates_by_size`, a materially higher-blast-radius touch point)
were named in the PREREG and correctly NOT bundled into this rung's build
— unaffected by this section's findings, still open for a future,
separately-scoped rung.

## 2. The build, exactly as priced in the PREREG §8

Four edits, `runners/dsl/src/synth_enumerate.rs`, zero new `TermNode`
variants (`Mod`/`Sqrt` were pre-existing, already-wired Terms — the
`IntersectAll`/`UnionAll`/`DictFromPairs` op-table-exposure precedent
class):

1. **`OP_TABLE`**: `("Mod", OpKind::Binary)`, `("Sqrt", OpKind::Unary)`.
2. **`build_op`**: `"Mod" => TermNode::Mod{a,b}`, `"Sqrt" =>
   TermNode::Sqrt{arg}`.
3. **`eval_synth_enumerate`'s bare-scalar `else` arm** (NOT the shared
   `DEFAULT_OPS` constant, which the list-shaped branch also consumes):
   `v.push("Mod"); v.push("Sqrt");` — scoped so task 132 (list-shaped) is
   structurally unreachable by this change, confirmed by the mutually
   exclusive `if`/`elif` branch structure, exactly as planned.
4. **`term_json`** (the module's own local candidate-JSON renderer,
   DISTINCT from `jsonio.rs`): missing match arms for `TermNode::Mod`/
   `TermNode::Sqrt` — found live, NOT anticipated in the PREREG, via a
   `pyo3_runtime.PanicException: internal error: entered unreachable
   code: candidates are built only from the op table + leaves` the first
   time the battery's own `run_structural_moves` path rendered a winning
   candidate containing either op. **This is the EXACT same missing-arm
   bug class `DictFromPairs_RESULTS.md` §2 already found and fixed once
   for `TermNode::MkDict`** — a genuinely recurring shape (every new
   op-table exposure whose build function can embed a Term this local
   renderer has never had to serialize before hits this same
   `unreachable!()`), fixed the same way (one additive match arm each,
   field names matching `jsonio.rs`'s own parser for round-trip
   consistency: `"a"`/`"b"` for `Mod`, `"arg"` for `Sqrt`).

**Genuine from-source rebuilds, twice** (the second after the `term_json`
fix): `cargo build --release`, **2m 20s** then **1m 58s** (neither a
cached sub-second no-op, confirmed by touching `synth_enumerate.rs` before
each). `bash scripts/engine_build.sh` installed each build; the documented
benign `python: command not found` PATH quirk hit both times, the two
trailing commands run directly with `python3` per the task's own standing
note.

**Rust suite** (both builds): `RUSTFLAGS="-L
/home/linuxbrew/.linuxbrew/opt/python@3.13/lib -lpython3.13"
LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/opt/python@3.13/lib:
$LD_LIBRARY_PATH" cargo test --lib --release -- --test-threads=1`:
**778 passed; 0 failed; 4 ignored** on both, byte-identical to the
documented current baseline.

## 3. Live re-verification through the REAL pipeline (not just the hand-built term)

After the `term_json` fix, `domains.prog_synthesis.synthesize_from_request`
(not a hand-built term) was re-run for the four witnesses. Results
reported honestly in §4's full battery below rather than duplicated here
— see the exact task-id set diff.

## 4. Full MBPP battery — before/after, all three arms, real set-diff

**Before** (this worktree, unmodified `main @ 78afd81`, freshly measured):

```
full:              73/257  content_stripped: 72/257  official: 101/257
```

**After** (`Mod`/`Sqrt` built and installed, engine rebuilt genuinely
twice as described in §2):

```
full:              73/257  content_stripped: 72/257  official:  99/257
```

**Exact task-id set-diff, all three arms** (direct set computation from
`results/mbpp_endgame.json`'s `runnable_rows`, saved before/after:
`results/mbpp_endgame_BEFORE_this_rung.json` vs. the post-build
`results/mbpp_endgame.json`, both retained in this worktree):

| arm | before (n) | after (n) | newly passing | regressed | net |
|---|---|---|---|---|---|
| `full` | 73 | 73 | `{92, 171, 246, 435}` | `{59, 135, 138, 406}` | 0 (churn, NOT a superset) |
| `content_stripped` | 72 | 72 | `{92, 171, 246, 435}` | `{59, 135, 138, 406}` | 0 (churn, NOT a superset) |
| `official` | 101 | 99 | `{246, 435, 441, 479}` | `{14, 138, 164, 406, 455, 464}` | **-2** |

**246/435 (the two `Sqrt`/`Mod` witnesses this rung had highest confidence
in, per PREREG §5.3's constant-starvation-free reasoning) DID convert on
ALL THREE arms** — the mathematical/formula-reachability diagnosis was
correct. **77/293 did NOT convert** on any arm despite being
mathematically correct and hand-verified (77's own ungrounded-modulus
constant-starvation risk, named explicitly as uncertain in PREREG §7 item
1, is the most likely cause for 77 specifically, not re-traced to its
exact search trace here — this document does not need that trace to reach
its GO/NO-GO decision, since the regression already settles it). **Two
UNEXPECTED conversions appeared** (92 "undulating number", 171 "perimeter
of a regular pentagon" — the EXACT worked example from PREREG §4, whose
own Group-A "spurious accept, then exclude, then budget-exhaust" trace is
reproduced there in full) — plausible mechanism: with `Mod` newly
available, the RE-search after the spurious-candidate exclusion now finds
a different (in 171's case, presumably the true general `5*a`, unverified
here since 171 is not one of this rung's own named witnesses and its exact
new IR was not re-traced) candidate before exhausting budget. **This is
exactly the "reach is not conversion" AND "a widened op inventory shifts
what a DIFFERENT construction lane accepts" mechanism this arc has
repeatedly documented — cutting BOTH ways this time: it explains some of
the gains AND all of the losses.**

## 5. The two regression mechanisms, traced to their exact cause

### 5.1 Search-cost inflation within the SAME narrow branch (official-arm losses: 14, 164)

Task 14 ("volume of a triangular prism", `a*b*c/2` — reachable with
EXISTING ops, confirmed in the PREREG §5.4's own "constant-starved
arithmetic" row) and task 164 both flip from `pass`/`None`-construction
(direct enumerate) to `gapped:enumerate_failed`/`accepted_holdout_fail` on
the `official` arm specifically. **This is the SAME risk class Rung 1
already measured for task 132 — but Rung 1's finding was scoped to the
LIST-shaped branch (`LIST_EXTRA_OPS`), and this rung's PREREG §6 correctly
noted task 132 itself is structurally unreachable by a bare-branch-only
change. What the PREREG's regression pricing (§6) did NOT price is that
the BARE branch carries the exact same risk WITHIN ITSELF**: adding two
more ops to a 12-op inventory increases the per-size candidate count
enough that an already-in-budget composition (task 14's `a*b*c/2`, a
depth-3 formula) can be pushed past the 200,000-candidate ceiling before
it is reached, on the `official` arm's own (larger, all-rows-revealed)
example set specifically. **The PREREG's own §6 regression list (23
bare-scalar canaries) was the RIGHT population to check — this mechanism
was exactly what it existed to catch, and the RESULTS measurement (this
section) is what makes the catch real, not the PREREG's priced
uncertainty alone.**

### 5.2 Cross-lane reach into the structural-moves/retrieval hole-filler (full/content_stripped losses: 59, 135, 138, 406; official losses: 138, 406, 455, 464)

All four `full`/`content_stripped` regressions are `retrieved_exemplar`-
sourced (`construction: 'retrieved_exemplar'` both before and after) and
flip from `pass` to `accepted_holdout_fail` — the candidate itself
changed. Traced to source: `domains/prog_moves.py::intermediate_candidates`
(called from `run_structural_moves`, the ARC5 decomposition-move
mechanism — *"intermediate problems UNLOCK TRACTABILITY,"* per that
function's own doc comment) calls
`domains/prog_moves.py::_run_synth_enumerate` with **no explicit `ops`
key at all** (confirmed by reading the exact dict literal, `prog_moves.py`
line ~338) — meaning this call ALSO reaches the SAME Rust-internal
typed-default routing this rung's change touched, exactly like the
top-level `run_enumerate` does. **Widening the bare-scalar typed default
therefore widens what THIS probe proposes too, and its proposal feeds
into which candidate the `retrieved_exemplar` construction lane ultimately
accepts** — for task 406 specifically (a=10 → expected `False`, "is the
parity of a odd"), the post-build IR contains a bare `Mod{a,b}`-shaped
node (`got: 0`, not wrapped in the `Eq`-to-bool comparison the CORRECT
program needs) that happens to fit the 2 revealed rows and fails the
held-out row — a spurious fit, structurally identical to task 171's own
"`min(50, a*a)`" case study in the PREREG, just reached through a
different call site. **This is a genuine, previously-unmeasured blast
radius the PREREG's §6 regression pricing did not check, because it only
enumerated the DIRECT bare-scalar canary population (tasks whose OWN spec
reaches the modified branch) — not every task whose `retrieved_exemplar`
acceptance is indirectly influenced by a decomposition PROBE that reaches
the same branch on a DIFFERENT (sub-)spec.** This is a real, structural
gap in how this rung's own regression-pricing scope was drawn, named
honestly rather than smoothed over.

## 6. Why no narrower scoping was attempted to rescue a clean win

Given the two independently-confirmed regression mechanisms, a genuinely
SAFE narrower scoping would need to distinguish, at the Rust call site,
"a top-level `run_enumerate` request" from "a `prog_moves.py`
decomposition-probe sub-request" — no such distinction currently exists in
the `SynthEnumerate` Term's own contract (both omit an `ops` key
identically), so building one would require either (a) a new parameter
threaded through the Term's own JSON contract (genuine new engine surface,
not a same-class op-table exposure any more) or (b) having
`prog_moves.py`'s own call site pass an EXPLICIT `ops` list that excludes
`Mod`/`Sqrt` (a mechanical, non-decision data change at that ONE call
site, in the same spirit as the existing `ps_enum_ops` curated-list
mechanism) — genuinely plausible, but unpriced, untested, and a real scope
expansion beyond this rung's own "expose an already-shipped Term, single
op-table touch" framing. Given CLAUDE.md's explicit instruction not to
force a build that rewards the metric over the underlying finding, and
given the measured regression is real (not hypothetical, not a sampled
estimate — the full 257-task-per-arm battery, exact set diff), this rung
declines to attempt that narrower fix live and instead reports the
finding, reverts, and names the narrower-scoping candidate for a future
rung to price properly (§8).

## 7. Regression discipline on the REVERTED state — confirms clean recovery

After reverting `synth_enumerate.rs` (`git checkout --
runners/dsl/src/synth_enumerate.rs`) and rebuilding genuinely a third time
(**1m 58s**, confirmed non-cached):

- **Rust suite**: 778 passed, 0 failed, 4 ignored — byte-identical.
- **Full MBPP battery, exact task-id set**: `full`/`content_stripped`/
  `official` pass sets are **set-identical** (not just count-identical) to
  `results/mbpp_endgame_BEFORE_this_rung.json`, confirmed by direct
  Python set comparison (`o == n` for all three arms, printed `True`
  three times).
- `git diff --stat` on the worktree: **empty** for
  `runners/dsl/src/synth_enumerate.rs` and for the built `.so`/
  `.build.json` (the rebuilt artifact is byte-identical to what `main`
  already tracks — `git status --short` shows no modification to either).

The worktree's only committed change from `main @ 78afd81` is this
document and its PREREG — no code, no seed, no engine artifact.

Named 9-file regression suite was NOT re-run against the reverted state
(unnecessary: the code is byte-identical to `main`, which the orchestrator
independently verified as green before this rung began, and the exact
task-id-set-identical battery result above is the stronger, more direct
confirmation for this specific revert).

## 8. What this document does NOT establish

1. The exact downstream rule/verdict that excludes Group A's spurious
   first candidate (§1, PREREG §4) was not re-traced to its precise rule
   name — the pattern (structurally identical to `structural_verdict_
   reject`/`property_verdict_reject`) is established by the call-trace
   evidence alone, matching this arc's own standing discipline for
   similar findings.
2. Why 92/171 newly convert while 77/293 do not, exactly — plausible
   mechanisms are named (§4) but neither was traced to its precise IR/rule
   path; not needed for this document's GO/NO-GO decision.
3. Whether the §6-named narrower fix (an explicit `ops` override at
   `prog_moves.py`'s own `_run_synth_enumerate` call site, excluding
   `Mod`/`Sqrt` from the decomposition-probe's own inventory while still
   offering them to the top-level `run_enumerate` call) would actually
   produce a clean, regression-free win — a real, plausible, UNPRICED
   candidate for a future rung, not attempted here.
4. Whether `filter_templates_by_size`'s own Mod-quantifier extension
   (PREREG §5.2, tasks 75/426) carries the SAME cross-lane regression risk
   this document found for the bare-branch exposure — untested, and now a
   MORE urgent question to check first in any future rung that revisits
   this cluster, given this document's own finding that the risk surface
   is broader than the PREREG's own regression-pricing section anticipated.
5. The `Range`/iteration gap (~10 tasks, PREREG §5.4), the bitwise-family
   gap (228, 399, 429), and the string-index-parity gap (226, 437) remain
   exactly as unpriced and unbuilt as the PREREG left them — untouched by
   this rung's build-and-revert cycle.
6. Whether any of this reflects real human program-synthesis cognition
   remains exactly as open as every prior document in this arc left it.

## 9. GO/NO-GO

**NO-GO on the build — reverted.** The population-reframing finding (§1,
PREREG §4: 24% of the budget-exhausted bucket is a reject-then-retry
artifact sharing the arc's already-NO-GO'd information-theoretic floor,
76% is genuine zero-recall) is the durable result of this rung and stands
independent of the build outcome. `Mod`/`Sqrt` exposure was correctly
diagnosed (two ≥2-witness, zero-new-`TermNode` clusters, both hand-verified
against revealed AND held-out rows), correctly scoped against the
ALREADY-KNOWN list-shaped regression risk (Rung 1's task-132 precedent),
built under full house discipline (genuine double rebuild, including a
genuine, independently-discovered `term_json` bug fix in the SAME class as
`DictFromPairs`'s own), and MEASURED to have a real, non-hypothetical net
regression (`official` arm -2; `full`/`content_stripped` arms real
task-id churn at equal count) via two distinct, individually-traced
mechanisms neither anticipated by the PREREG's own regression-pricing
section. The code has been fully reverted; the worktree carries no code
diff from `main @ 78afd81`, confirmed by an exact task-id-set-identical
re-measurement of the full battery post-revert. A narrower,
call-site-scoped fix is named as a real, plausible, unpriced candidate for
a future rung (§6, §8 item 3) — not built here, matching this arc's own
standing discipline against forcing a build once real regression evidence
exists.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-budget-exhausted-survey
git log --oneline -1   # on top of main @ 78afd81
git diff --stat        # empty — the build was reverted
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/ceiling3_diag_sweep.py
```

The `Mod`/`Sqrt` build-and-measure cycle (§2-5) is reproducible by
re-applying the four edits described in §2 (OP_TABLE, build_op, the
bare-scalar `else` arm, and the `term_json` missing-arm fix), rebuilding
genuinely (`cargo build --release` in `runners/dsl/`, confirmed non-cached
by touching `synth_enumerate.rs` first), reinstalling
(`bash scripts/engine_build.sh`), and re-running the battery above — the
exact task-id-set diff table in §4 is the load-bearing artifact, not a
narrative description.

Rust suite:
```bash
cd runners/dsl && RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/opt/python@3.13/lib -lpython3.13" \
  LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/opt/python@3.13/lib:$LD_LIBRARY_PATH" \
  cargo test --lib --release -- --test-threads=1
```
