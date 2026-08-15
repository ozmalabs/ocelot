# `ProblemShape` axis coverage for the three CAN solvers — PREREG

Base `main @ 6b6c921` ("Merge solver-can-adapter: grow real CAN edges from
text, GO -- narrowly scoped"), verified via `git log --oneline -1 main`
immediately before creating the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/problem-shape-can-axes`, branch
`problem-shape-can-axes`, detached from `6b6c921`. `data/` was absent in the
fresh worktree; symlinked (`ln -sfn /home/matt/ozmadev/ocelot/data data`) and
confirmed `data/wiktionary/en.jsonl.gz` resolves to the real
492,560,156-byte file.

This is a narrowly-scoped follow-on to `SHAPE_WOBBLE_POSITION_RESULTS.md` §4,
which found (but explicitly declined to build, citing wrong-territory /
concurrent-sibling-work reasons that have since been resolved by
`SOLVER_CAN_ADAPTER_RESULTS.md` landing) a real, live-constructed defect: the
three CAN solver Goal kinds (`solve_can_relax`/`solve_can_exact`/
`solve_can_bp`) all collapse to the byte-identical `ProblemShape` signature
key `ps_has_targets_mt=yes`, because `_AXES` (`domains/problem_shape.py`)
never reads `treewidth_bound`/`combine`/`max_rounds`/`k_starts` — the attrs
that actually distinguish the three mint functions
(`mint_solve_can_relax_goal`/`mint_solve_can_exact_goal`/
`mint_solve_can_bp_goal`, `domains/solver_dispatch.py:174-211`).

---

## 1. Re-verification of the defect (live, on THIS worktree's current tree)

Reproduced `SHAPE_WOBBLE_POSITION_RESULTS.md` §4's own script verbatim,
fresh, on `6b6c921` (five commits past that document's own base, `fff8555`):

```
relax solve_can_relax ps_has_targets_mt=yes
   attrs: {'status': 'pending', 'raw': 'solve_can_relax', 'kind': 'solve_can_relax', 'k_starts': 1.0}
exact solve_can_exact ps_has_targets_mt=yes
   attrs: {'treewidth_bound': 4.0, 'status': 'pending', 'raw': 'solve_can_exact', 'kind': 'solve_can_exact', 'commit': True}
bp solve_can_bp ps_has_targets_mt=yes
   attrs: {'status': 'pending', 'raw': 'solve_can_bp', 'kind': 'solve_can_bp', 'combine': 'max_product', 'commit': False}
```

**Confirmed still real, unchanged.** All three collapse to
`ps_has_targets_mt=yes`. `relax` carries `k_starts`; `exact` carries
`treewidth_bound`+`commit`; `bp` carries `combine`+`commit` — none of these
are read by `_AXES` (`domains/problem_shape.py:61-62`, current 5-axis tuple:
`has_bound`, `has_direction`, `has_statement`,
`has_targets_correspondence`, `has_targets_mt`).

---

## 2. Reading each mint function's OWN always-written attrs (not the
   caller-optional ones)

Read directly, `domains/solver_dispatch.py:174-211`:

| function | attrs ALWAYS written (every call, regardless of kwargs) | attrs written ONLY if the caller passes them |
|---|---|---|
| `mint_solve_can_relax_goal` | `k_starts` (float, default `1.0`) | `max_steps` |
| `mint_solve_can_exact_goal` | `commit` (bool, default `True`) | `treewidth_bound`, `max_exact_n` |
| `mint_solve_can_bp_goal` | `combine` (str, default `"max_product"`), `commit` (bool, default `False`) | `max_rounds`, `epsilon` |

**Design decision — read `k_starts`/`combine`, NOT `treewidth_bound`/
`max_rounds`/`commit`, and here is why, checked against real call sites, not
assumed:**

- `treewidth_bound` is caller-optional. `grep`-ing every real
  `mint_solve_can_exact_goal(` call site in `tests/` shows several real,
  already-committed calls that never pass it at all (e.g.
  `tests/test_problem_shape_migrated.py:116,135,248`,
  `tests/test_solver_dispatch_migrated.py:191,285,333`) — an axis keyed on
  `treewidth_bound`'s presence would leave those real `solve_can_exact`
  observations indistinguishable from `solve_can_relax` again (both would
  read `has_treewidth_bound=-`), reproducing the SAME collapse this rung
  exists to fix, just for a subset of real cases instead of all of them.
  Same argument applies to `max_rounds`/`epsilon` on `solve_can_bp`.
- `commit` is written by BOTH `mint_solve_can_exact_goal` AND
  `mint_solve_can_bp_goal`, always, regardless of kwargs (`domains/
  solver_dispatch.py:190,204`) — its mere PRESENCE does not discriminate
  exact from bp at all (only its always-boolean VALUE would, and axis
  extraction here is presence-based like every existing axis, not
  value-comparing — mirroring `goal_signature`'s own existing 5-axis idiom,
  none of which reads a boolean's true/false value either).
- `k_starts` (relax) and `combine` (bp) ARE unconditionally written by
  their respective mint function and UNCONDITIONALLY ABSENT from the other
  two — confirmed directly against all three functions' bodies, not
  inferred. Two new boolean-presence axes, `has_k_starts` and
  `has_combine`, are therefore JOINTLY sufficient to discriminate all three
  kinds, with no dependency on which optional kwargs a caller happened to
  pass:

  | kind | `has_k_starts` | `has_combine` |
  |---|---|---|
  | `solve_can_relax` | yes | — |
  | `solve_can_exact` | — | — |
  | `solve_can_bp` | — | yes |

  Three distinct 2-tuples over two axes — the minimum axis count that
  fully separates the three kinds under every real and hypothetical call
  (kwargs or no kwargs), and the ONLY design of the ones considered that
  does not silently degrade back to collapse on the (real, already-
  committed) no-kwargs call sites.

**Never `kind`.** Per `QUESTION_DRIVER_RUNG3_PREREG.md`'s own ruling
(re-confirmed in `domains/problem_shape.py:79-83`'s docstring): reading
`kind` back out would be circular (the Goal already says what it is) and
would give the wrong answer for a future pre-mint dispatch caller that needs
this signature BEFORE `kind` exists. Neither new axis reads `kind` —
`has_k_starts`/`has_combine` are presence-checks on `at.get("k_starts")`/
`at.get("combine")`, mirroring the EXISTING `has_targets_mt`/
`has_targets_correspondence` axes' own `native.neighbours(...)` presence-
check idiom exactly.

---

## 3. Why the existing seeded `ps_has_targets_mt=yes` entry does NOT need a
   rename, and why its `signature` array DOES need widening

Under the new 7-axis extraction, `solve_can_exact` writes neither
`k_starts` nor `combine` — so its signature is UNCHANGED in every respect
except two new `_ABSENT` (`"-"`) relations. `signature_key` skips
`_ABSENT` values (`domains/problem_shape.py:113-116`), so the KEY stays
`ps_has_targets_mt=yes` — the existing seeded entry, once its OWN
`signature` array is widened to include the same two new axes as `"-"`,
continues to represent exactly (and now ONLY) `solve_can_exact`.

**This widening of the seeded entries is not optional — it is required for
correctness**, confirmed by reading the literal-decode residual mechanism
directly (`runners/dsl/src/shape_decode.rs`, `covers_relation`/
`score_part_for_residual`, `wild_objects=false` path): a literal codebook
part must contain an EXACT relation (predicate+value) for every relation an
observation carries, or that relation contributes to a non-empty residual.
Since `goal_signature` will now emit `has_k_starts`/`has_combine` relations
(value `"-"` when absent) on EVERY observation, INCLUDING deduction and
decompose observations, and the two existing seeded `ProblemShape` nodes
(`seeds/problem_shape_growth.json`, local_id 1 and 2) currently declare only
the original 5 relations, leaving them unwidened would break recognition of
BOTH existing shapes for EVERY future observation, not just the CAN ones —
this was checked against the mechanism, not assumed.

`solve_deduction` and `solve_decompose` never write `k_starts`/`combine`
either (confirmed: `_mint_base` for both writes only `statement`/`mode` or
`bound`), so `ps_has_statement=yes` (local_id 1) and the live-minted
`ps_has_bound=yes` (grown at test time, not seeded) also gain two `"-"`
relations each and are otherwise semantically unchanged.

---

## 4. Real population count per CAN kind (re-verified, not assumed from
   `QUESTION_DRIVER_RUNG3_RESULTS.md`'s own stale count)

`QUESTION_DRIVER_RUNG3_RESULTS.md` §1 counted "5 real recurring instances"
for the CAN family as a WHOLE, as of ITS OWN base commit — before
`SOLVER_CAN_ADAPTER_RESULTS.md` (`test_solver_can_adapter.py`) and this
rung's own `test_problem_shape_migrated.py` additions landed. Recounted
fresh on THIS worktree (`grep -n "mint_solve_can_.*_goal(" tests/*.py`,
excluding the function definitions themselves):

| kind | real `tests/` call sites (today) | recurring (>=2)? |
|---|---|---|
| `solve_can_exact` | 13 (`test_solver_math_boundary.py:222`; `test_solver_can_adapter.py:143`; `test_problem_shape_migrated.py:116,135,248`; `test_solve_gap_awareness_migrated.py:144`; `test_solver_dispatch_migrated.py:191,236,259,285,295,305,333`) | yes, well above floor |
| `solve_can_relax` | 3 (`test_solver_can_adapter.py:170`; `test_solver_dispatch_migrated.py:168,180`) | yes |
| `solve_can_bp` | 2 (`test_solver_can_adapter.py:174`; `test_solver_dispatch_migrated.py:315`) | yes, exactly at the floor |

(One additional `solve_can_exact` call exists in `scripts/
solver_math_boundary_run.py:214` — a one-off demonstrator script, not a
test; counted separately here, not folded into the `tests/`-only population
count, mirroring `QUESTION_DRIVER_RUNG3_PREREG.md` §1's own convention of
counting from committed test files.)

**All three kinds independently clear the `support>=2` recurrence floor**
`META_SHAPE_FIRST_CLASS_RESULTS.md` §4.1 and `QUESTION_DRIVER_RUNG3_RESULTS.md`
§2.1 both already established as "the smallest cardinality at which
recurs is defined." This is DIFFERENT from Rung 3's own situation (where
`decompose_shape` was the only one of three candidates at the floor;
`deduction_shape`/`can_shape` were comfortably above it) — here, `bp` sits
exactly at the floor the same way `decompose_shape` did, while `exact` is
comfortably above it and `relax` sits in between.

---

## 5. Mint discipline — design decision, and why

Mirroring `QUESTION_DRIVER_RUNG3_RESULTS.md`'s OWN precedent as closely as
the population shape allows, rather than re-deriving a new policy:

- **`solve_can_exact`** — the EXISTING seeded `ps_has_targets_mt=yes` entry
  already covers it once widened (§3); no new mint needed. Its `support`
  field is updated from the stale `5.0` (which conflated all three CAN
  kinds as of Rung 3's own base commit) to `13.0` (§4's fresh, honest,
  exact-only recount) — leaving it at the old, now-provably-wrong number
  would be exactly the kind of stale claim `CLAUDE.md`'s "DO NOT USE THIS
  NOTE TO DISMISS A RED" / baseline-must-be-a-list discipline warns against
  one level up; `test_seeded_codebook_has_two_real_shapes`'s own assertion
  (`support >= 5.0`) is satisfied either way, so this is a safe, honest
  correction, not a test-driven number.
- **`solve_can_relax`** (3 real recurring instances) and **`solve_can_bp`**
  (2, exactly at the floor) are BOTH deliberately left UNSEEDED, to be
  grown live through the SAME recognize → residual → recurrence → mint →
  re-decode → recognized loop `decompose_shape` demonstrated — not because
  their population is insufficient (both clear the floor, §4), but because
  Rung 3's own stated methodology already prefers demonstrating the growth
  mechanism over hand-authoring a seed entry whenever a real, un-seeded
  population is available to grow it from live (`seeds/
  problem_shape_growth.json`'s own top-level `description`: `decompose_shape`
  "is DELIBERATELY left unseeded to mint live from real recurrence" even
  though its population, at 2, was no larger than `bp`'s here). Growing two
  shapes live from real data is also strictly stronger evidence for THIS
  rung's own live-demonstration requirement than seeding them would be.
- Neither new mint changes `ps_mint`'s rule body, `ps_decode`/
  `ps_recognize`/`ps_residual`/`ps_redecode`'s rule bodies, or the seed's
  Γ productions (§6) — the mint mechanism is already fully generic over
  `key`; only the DATA (two node attrs' `signature`/`support`, plus
  `domains/problem_shape.py`'s `_AXES`/`goal_signature`) changes.

---

## 6. Γ productions — none needed

No new edge type is introduced. The two new axes are additional entries
inside the ALREADY-EXISTING `signature` JSON-list attr (on
`ProblemShapeObservation`/`ProblemShape` nodes) — not a new edge predicate.
`seeds/problem_shape_growth.json`'s existing three productions
(`observed_problem`, `about_goal`, `minted_problem_shape`) already cover
every edge type this grain uses; nothing new is minted at the edge level by
this change, so `"productions": []` growth (the `SHAPES, NOT NUMBERS`
audit's own named defect class) does not apply here — confirmed by reading
the diff design, not asserted.

---

## 7. What will be built

1. `domains/problem_shape.py`: widen `_AXES` to 7 entries (add
   `has_combine`, `has_k_starts`, keeping alphabetical order); widen
   `goal_signature` to compute the two new presence facts from `at.get(...)`
   — mechanical extraction only, same idiom as the existing 5 axes, zero
   branching on `kind`.
2. `seeds/problem_shape_growth.json`: widen both seeded `ProblemShape`
   nodes' `signature` arrays with the two new `_ABSENT` relations (required
   for correctness, §3); update local_id 2's `support` from `5.0` to `13.0`
   (§5, honest recount) and its `source`/comment framing to reflect it now
   representing `solve_can_exact` specifically, not "CAN in general."
3. `tests/test_problem_shape_migrated.py`: new tests — (a) the three-way
   live discrimination (real Bigville CAN networks, `solve_can_relax`/
   `solve_can_exact`/`solve_can_bp`, asserting three DISTINCT recognized/
   residual keys, never the old collapsed one); (b) the live mint-from-
   recurrence loop for BOTH `solve_can_relax` and `solve_can_bp`, mirroring
   `test_decompose_shape_mints_from_real_recurrence_and_redecodes`'s own
   structure (first observation residual, second triggers mint exactly
   once, both recognized after re-decode, a third never-before-seen
   observation recognizes with no further mint); (c) re-confirm the
   existing seeded/minted shapes (`deduction_shape`, `decompose_shape`, the
   two genuine singletons) are unaffected by the widened axis set.
4. Zero Rust changes expected (pure seed-JSON + Python mechanical-
   extraction data change, mirroring Rung 3's own "zero new Rust" scope) —
   `cargo build`/`cargo test` run only if a `.rs` file ends up touched,
   per house discipline.

---

## 8. Regression scope

`tests/test_problem_shape_migrated.py`, `tests/test_solver_dispatch_migrated.py`,
`tests/test_solver_can_adapter.py`, `tests/test_can_junction_tree.py`,
`tests/test_can_loopy_bp.py`, plus the task's own named suites
(`tests/test_solve_gap_awareness_migrated.py`, `tests/
test_bigville_can_native_migration.py`, `tests/
test_can_native_reimplementation.py`) as a wider sweep, fresh baseline
(no prior diff to pair against in this worktree — this is a fresh worktree
off `6b6c921`).
