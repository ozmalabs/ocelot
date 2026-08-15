# `ProblemShape` axis coverage for the three CAN solvers — RESULTS

Prereg: `PROBLEM_SHAPE_CAN_AXES_PREREG.md`, same worktree/branch, base
`main @ 6b6c921` ("Merge solver-can-adapter: grow real CAN edges from
text, GO -- narrowly scoped"), verified via `git log --oneline -1 main`
immediately before creating the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/problem-shape-can-axes`, branch
`problem-shape-can-axes`. Commits: `c358805` (PREREG), `5c38b1e`
(implementation + tests). `data/` was absent in the fresh worktree;
symlinked (`ln -sfn /home/matt/ozmadev/ocelot/data data`) and confirmed
`data/wiktionary/en.jsonl.gz` resolves to the real 492,560,156-byte file.
No `.rs` file touched (`git diff --stat 6b6c921 -- '*.rs'` empty) — no
`cargo build`/`cargo test` run, per house discipline (conditional on a Rust
change, which did not happen).

**Headline: GO.** `solve_can_relax`/`solve_can_exact`/`solve_can_bp` — three
genuinely different CAN-solver algorithms — no longer collapse to the
byte-identical `ProblemShape` key `ps_has_targets_mt=yes`. Two new axes
(`has_k_starts`, `has_combine`), read from attrs each `mint_solve_can_*_goal`
function writes unconditionally (never `kind`, never a caller-optional attr),
discriminate all three. `solve_can_exact` keeps recognizing via the existing
seeded entry (widened, same key, support corrected from a stale 5.0 to an
honest 13.0); `solve_can_relax` and `solve_can_bp` are grown live from real
recurrence over real Bigville CAN networks, mirroring `decompose_shape`'s
own recognize → residual → recurrence → mint → re-decode → recognized loop.
76/76 regression tests green across eight suites; zero new Rust; zero new
Γ productions needed.

---

## 1. Re-verification of the defect (live, before any code was written)

Reproduced `SHAPE_WOBBLE_POSITION_RESULTS.md` §4's own script verbatim, on
THIS worktree's fresh checkout of `6b6c921` (five commits past that
document's own base):

```
relax solve_can_relax ps_has_targets_mt=yes
   attrs: {'status': 'pending', 'raw': 'solve_can_relax', 'kind': 'solve_can_relax', 'k_starts': 1.0}
exact solve_can_exact ps_has_targets_mt=yes
   attrs: {'treewidth_bound': 4.0, 'status': 'pending', 'raw': 'solve_can_exact', 'kind': 'solve_can_exact', 'commit': True}
bp solve_can_bp ps_has_targets_mt=yes
   attrs: {'status': 'pending', 'raw': 'solve_can_bp', 'kind': 'solve_can_bp', 'combine': 'max_product', 'commit': False}
```

**Confirmed still real, not stale.** All three Goals — with genuinely
different real attrs (`k_starts` vs `treewidth_bound`+`commit` vs
`combine`+`commit`) and genuinely different resolver bodies
(`solve_can_relax`/`solve_can_exact`/`solve_can_bp`,
`domains/solver_dispatch.py:920-1030`) — read back the identical
`ProblemShape` signature key. This is the exact defect
`SHAPE_WOBBLE_POSITION_RESULTS.md` §4 found live and explicitly deferred as
"reported, not built" (wrong fix shape for that rung's own charter + wrong,
concurrent-sibling territory at the time).

---

## 2. New axis design, grounded in real Goal attrs, never `kind`

Read directly, `domains/solver_dispatch.py:174-211`:

| function | attrs ALWAYS written (every call) | attrs written only if the caller passes them |
|---|---|---|
| `mint_solve_can_relax_goal` | `k_starts` (float, default `1.0`) | `max_steps` |
| `mint_solve_can_exact_goal` | `commit` (bool, default `True`) | `treewidth_bound`, `max_exact_n` |
| `mint_solve_can_bp_goal` | `combine` (str, default `"max_product"`), `commit` (bool, default `False`) | `max_rounds`, `epsilon` |

Two new axes were added to `_AXES`/`goal_signature`
(`domains/problem_shape.py:61-77`, `_AXES` now 7 entries, alphabetical):

- **`has_k_starts`** — `"yes"` iff `at.get("k_starts") is not None`. Written
  ONLY by `mint_solve_can_relax_goal`.
- **`has_combine`** — `"yes"` iff `at.get("combine")`. Written ONLY by
  `mint_solve_can_bp_goal`.

Jointly sufficient (`solve_can_relax`: `has_k_starts=yes`,
`has_combine=-`; `solve_can_bp`: `has_k_starts=-`, `has_combine=yes`;
`solve_can_exact`: neither) — confirmed live in §5 below, not merely argued.

**Why NOT `treewidth_bound`/`max_rounds`/`commit`, checked against real call
sites, not assumed:**

- `treewidth_bound` is caller-optional. Real, already-committed calls in
  `tests/test_problem_shape_migrated.py:116,135,248`,
  `tests/test_solver_dispatch_migrated.py:191,285,333` never pass it — an
  axis keyed on its presence would leave those real `solve_can_exact`
  observations reading `has_treewidth_bound=-`, indistinguishable from
  `solve_can_relax` again, reproducing the SAME collapse for a real subset
  of cases. Same argument for `max_rounds`/`epsilon` on `solve_can_bp`.
- `commit` is written by BOTH `mint_solve_can_exact_goal` and
  `mint_solve_can_bp_goal` unconditionally (`domains/solver_dispatch.py:190,204`)
  — mere presence does not discriminate exact from bp at all (axis
  extraction here is presence-based, like every existing axis, never
  value-comparing a boolean).
- `kind` was never read — extending `goal_signature` never touches
  `at.get("kind")`; confirmed directly in the new code and re-checked by the
  live signature dump in §5 (no `kind` predicate appears in any signature).

---

## 3. Why the existing seeded entry needed widening, and why the literal
   ShapeDecode mechanism made this non-optional

Read directly, `runners/dsl/src/shape_decode.rs`'s `covers_relation`/
`score_part_for_residual` under `wild_objects=false` (the literal decode
mode `ps_decode` uses, `seeds/problem_shape_growth.json`'s `ps_decode` rule):
a literal codebook part must declare an EXACT relation
(predicate+value) for every relation an observation carries, or that
relation goes to residual. Since `goal_signature` now emits
`has_k_starts`/`has_combine` relations (value `"-"` when absent) on EVERY
observation — including `solve_deduction` and `solve_decompose` ones — both
pre-existing seeded `ProblemShape` nodes (`seeds/problem_shape_growth.json`,
local_id 1 `ps_has_statement=yes`, local_id 2 `ps_has_targets_mt=yes`) had
their `signature` arrays widened with the two new axes as `"-"`. Without
this, EVERY existing recognized shape (not just the CAN ones) would have
regressed to residual on the next observation. `signature_key` skips
`_ABSENT` values, so neither entry's `name`/key changed — local_id 2
continues to be looked up as `ps_has_targets_mt=yes`, and (since
`solve_can_exact` writes neither new attr) now represents `solve_can_exact`
specifically rather than "CAN in general."

`local_id 2`'s `support` was corrected from a stale `5.0` (which, per
`QUESTION_DRIVER_RUNG3_RESULTS.md` §1, was the TOTAL count across all three
CAN kinds as of that rung's own base commit) to `13.0` — a fresh,
`tests/`-only recount of real `solve_can_exact` call sites specifically
(§4). `test_seeded_codebook_has_two_real_shapes`'s own assertion
(`support >= 5.0`) is satisfied either way; this is an honest correction,
not a test-driven number.

---

## 4. Real population count per CAN kind (fresh recount, this worktree)

`grep -n "mint_solve_can_.*_goal(" tests/*.py`, excluding the function
definitions themselves:

| kind | real `tests/` call sites | recurring (≥2)? |
|---|---|---|
| `solve_can_exact` | 13 | yes, well above floor |
| `solve_can_relax` | 3 | yes |
| `solve_can_bp` | 2 | yes, exactly at the floor |

(One further `solve_can_exact` call exists in
`scripts/solver_math_boundary_run.py:214` — a one-off demonstrator script,
not a test; not folded into the `tests/`-only count above, matching
`QUESTION_DRIVER_RUNG3_PREREG.md`'s own counting convention.)

All three kinds independently clear the `support≥2` recurrence floor
`META_SHAPE_FIRST_CLASS_RESULTS.md` §4.1 and `QUESTION_DRIVER_RUNG3_RESULTS.md`
§2.1 already established. `solve_can_bp` sits exactly at the floor, the same
position `decompose_shape` occupied in Rung 3.

---

## 5. Mint discipline followed — real recurring populations only

Mirroring `QUESTION_DRIVER_RUNG3_RESULTS.md`'s own precedent rather than
re-deriving a new policy:

- **`solve_can_exact`** needs no mint — the existing (widened) seeded entry
  already covers it (§3).
- **`solve_can_relax`** (3 real recurring instances) and **`solve_can_bp`**
  (2, at the floor) were DELIBERATELY left unseeded and grown live through
  the SAME recognize → residual → recurrence → mint → re-decode →
  recognized loop `decompose_shape` demonstrated — not because their
  population was insufficient (both clear the floor, §4), but because
  `seeds/problem_shape_growth.json`'s own stated methodology already
  prefers demonstrating the growth mechanism over hand-authoring a seed
  entry when a real, ungrown population is available (`decompose_shape`
  itself was left unseeded at support=2, the same floor `solve_can_bp` sits
  at here). This is also strictly stronger evidence for this rung's own
  live-demonstration requirement than seeding would have been.
- No change was made to `ps_decode`/`ps_recognize`/`ps_residual`/`ps_mint`/
  `ps_redecode`'s rule bodies, and no new Γ production was needed (§6 of the
  PREREG) — the mint mechanism is already fully generic over an
  observation's own `key`; only DATA changed (`_AXES`/`goal_signature` in
  Python, two node attrs in the seed).

---

## 6. Live demonstration

Reproduced directly (`PYTHONPATH=runners/dsl/python:. OZMA_SEED_PERSIST_DISABLED=1`):

```
$ python3 -c "... mint relax/exact/bp on one fresh Microtheory, print signature_key ..."
relax solve_can_relax ps_has_k_starts=yes_has_targets_mt=yes
exact solve_can_exact ps_has_targets_mt=yes
bp    solve_can_bp    ps_has_combine=yes_has_targets_mt=yes
```

Three distinct keys — no longer the old collapsed `ps_has_targets_mt=yes`
shared across all three.

**`tests/test_problem_shape_migrated.py`, two new tests, both real, real
Bigville residents throughout** (`worlds.bigville_can_beliefs.
build_resident_can_mt` via the file's own `_resident_mt` helper, unchanged):

1. **`test_can_relax_and_bp_shapes_mint_from_real_recurrence_and_redecode`**
   — THE GROWTH LOOP, LIVE, for both new kinds independently:
   - `solve_can_relax`: a FIRST real dispatch (resident index 5) stays
     `"residual"` (support=1, asserted — no recurrence yet); a SECOND real
     dispatch (resident index 6) triggers the mint — asserted: exactly ONE
     `ProblemShape` named `ps_has_k_starts=yes_has_targets_mt=yes` is
     minted (not two), `support==2`, `minted==1.0`; BOTH observations end
     up `"recognized"` (obs2 directly; obs1 via `ps_redecode`'s re-arm under
     the bumped epoch — the exact `decompose_shape` pattern).
   - `solve_can_bp`: the SAME loop, independently, over two MORE real
     residents (index 7, 10) — first residual, second mints exactly one
     `ps_has_combine=yes_has_targets_mt=yes` entry (`support==2`,
     `minted==1.0`), both recognized.
   - Asserts the two newly-minted keys are distinct from each other and
     from the pre-existing seeded/minted keys.
2. **`test_three_can_kinds_recognize_as_distinct_shapes_not_collapsed`** —
   THE HEADLINE LIVE DEMONSTRATION, after the growth loop above has grown
   the codebook: one MORE real `solve_can_relax` (resident 12), one real
   `solve_can_exact` (resident 13), one real `solve_can_bp` (resident 14) —
   each over its OWN real Bigville resident CAN network — ALL THREE reach
   `status == "recognized"`, each `covered_by` a DIFFERENT key
   (`ps_has_k_starts=yes_has_targets_mt=yes` /
   `ps_has_targets_mt=yes` / `ps_has_combine=yes_has_targets_mt=yes`);
   `len({...three covered_by values...}) == 3` is asserted directly. A
   fresh real `solve_deduction` Goal, dispatched in the same test, still
   recognizes correctly as `ps_has_statement=yes` — confirming the axis
   widening did not disturb the unrelated deduction-shape family.

```
$ python3 -m pytest tests/test_problem_shape_migrated.py -q -p no:randomly
........                                                                 [100%]
8 passed in 13.41s
```

All 6 pre-existing tests in this file (seeded codebook, deduction
recognition, CAN recognition, cross-cover discrimination,
`decompose_shape`'s own live mint, the two genuine singletons staying
residual/unminted) pass UNCHANGED alongside the 2 new ones — confirming the
widened axis set does not disturb `deduction_shape`, `decompose_shape`, or
the two genuine singletons (`solve_reasoning_bridge`/
`solve_analogical_promote`, which still correctly stay unminted — their real
population is still exactly 1 each, unaffected by anything in this rung).

---

## 7. Regression

Fresh worktree off `main @ 6b6c921` (verified before creating the worktree);
`data/` symlinked fresh, confirmed resolving to the real 492MB file; no
`.rs` file touched (`git diff --stat 6b6c921 -- '*.rs'` empty).

**The task's own named suites, run together, blocked to completion:**

```
$ PYTHONPATH=runners/dsl/python:. OZMA_SEED_PERSIST_DISABLED=1 python3 -m pytest \
    tests/test_problem_shape_migrated.py \
    tests/test_solver_dispatch_migrated.py \
    tests/test_solver_can_adapter.py \
    tests/test_can_junction_tree.py \
    tests/test_can_loopy_bp.py \
    tests/test_solve_gap_awareness_migrated.py \
    -q -p no:randomly
.............................................................            [100%]
61 passed in 336.12s (0:05:36)
```

**Wider CAN-native sweep** (the two suites `SOLVER_CAN_ADAPTER_RESULTS.md`
also gated on, for extra safety though this rung's diff never touches
`can_native_reimplementation.json` or `bigville_can_beliefs.py`):

```
$ PYTHONPATH=runners/dsl/python:. OZMA_SEED_PERSIST_DISABLED=1 python3 -m pytest \
    tests/test_bigville_can_native_migration.py tests/test_can_native_reimplementation.py \
    -q -p no:randomly
...............                                                          [100%]
15 passed in 0.90s
```

**76/76 green across eight suites, zero regressions, zero waivers.**

```
$ git diff --stat 6b6c921 HEAD
 .../PROBLEM_SHAPE_CAN_AXES_PREREG.md               | 268 +++++++++++++++++++++
 domains/problem_shape.py                           |  22 +-
 seeds/problem_shape_growth.json                    |  22 +-
 tests/test_problem_shape_migrated.py               | 155 ++++++++++++
 4 files changed, 462 insertions(+), 5 deletions(-)
```

Purely additive/widening diff — `domains/solver_dispatch.py`, every CAN
resolver body, every rule body in `seeds/problem_shape_growth.json`
(`ps_decode`/`ps_recognize`/`ps_residual`/`ps_mint`/`ps_redecode`), and every
`can_native_*`/`can_junction_tree`/`can_native_bp` file are byte-unchanged.

---

## 8. GO / NO-GO

**GO.** `solve_can_relax`/`solve_can_exact`/`solve_can_bp` now recognize as
three genuinely distinct `ProblemShape`s, grounded in real Goal attrs each
mint function writes unconditionally, never `kind`. Live-demonstrated: a
fresh three-way signature-key dump; a real growth loop (recognize → residual
→ recurrence → mint → re-decode → recognized) for both newly-discriminated
kinds, run over real Bigville CAN networks; a real three-kind
simultaneous-recognition test confirming the old collapsed key never
reappears; and confirmation that `deduction_shape`, `decompose_shape`, and
both genuine singletons are unaffected. 76/76 regression tests green,
fresh, across eight suites. Zero new Rust. Zero new Γ productions (no new
edge type introduced — the two new axes are additional entries inside the
already-existing `signature` JSON-list attr). Not merged, not pushed to
`main` — every commit (`c358805`, `5c38b1e`) lives on the
`problem-shape-can-axes` branch only. The orchestrator performs the merge.

---

## 9. What this document does NOT establish

1. **No pre-mint auto-dispatch or hold-open layer** — unchanged from Rung 3
   (`QUESTION_DRIVER_RUNG3_RESULTS.md` §8); still out of scope, still not
   built here.
2. **Rungs 2/3 of the sd ladder (`TransformDecode`/`DimInfer`) remain
   unwired at this grain** — every axis, old and new, is a categorical
   presence/value string, never an integer coordinate; this rung did not
   change that.
3. **The seven-axis vocabulary is grounded in the CURRENT eight `solve_*`
   mint functions only** (the original five plus the three CAN ones now
   individually addressable). A ninth toolbox facility with a genuinely new
   attr/edge shape would need further axis coverage — not designed here,
   the natural place this codebook grows next via its own loop.
4. **`solve_can_bp`'s support=2 threshold is the same un-validated floor**
   `META_SHAPE_FIRST_CLASS_RESULTS.md` §4.1 and `QUESTION_DRIVER_RUNG3_RESULTS.md`
   §8 already named (not re-swept against a larger real corpus here,
   inherited as the established convention).
5. **`solve_can_exact`'s corrected support=13.0 is a `tests/`-only recount**
   of literal call sites, not a claim about how often each kind dispatches
   in a live daemon's actual history — the SAME "synthetic-proven mechanism
   ≠ benchmark value, report both" caveat this codebase's own standing rule
   requires; this document reports a mechanism demonstration and a
   `tests/`-file census, not production frequency.
6. **The commit-value chosen for `has_k_starts`/`has_combine` is
   presence-only, not value-differentiating** — e.g. `k_starts=1` vs
   `k_starts=5` (`test_solver_dispatch_migrated.py:168,180`, both real) both
   read `has_k_starts=yes` and land on the SAME `ProblemShape`. This
   matches the existing axes' own discipline (`has_bound`/
   `has_targets_mt`/etc. are all presence-checks, never value-comparisons)
   and was a deliberate design choice (§2), not an oversight — a future
   rung could add value-graded axes if a real case needs it, none does
   today.
