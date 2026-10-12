# Bounded program induction for nonlinear 2-D maps v1

**Lock date:** 2026-09-29, before capture. **Question:** can the existing native `SynthEnumerate` route acquire compact executable programs for nonlinear coordinate maps, verify them on withheld inputs, and reuse them, where `GenInfer`'s integer-matrix family refuses?

## Scope and claim boundary

This evaluates the native program synthesizer as a separate learning route. Inputs are scalar integer coordinates `(r,c)` and outputs are typed two-tuples. A found program is returned as native Term JSON and directly reused through the same substrate Term evaluator. It is not counted as a `DimensionGenerator`, a graph-authored rule mint, or adoption by the shape-decode production route. Acquisition/transfer here can show a second bounded induction capability; it does not enlarge GenInfer or establish general nonlinear learning.

## Tasks and splits

Use four deterministic tasks. For every case, training examples are listed in the lock and withheld rows are evaluated only after a candidate is returned.

| Task | Target map | Training input pairs | Held-out input pairs |
|---|---|---|---|
| Linear control | `(r+c, c+c)` | `(0,0),(1,0),(0,1),(1,1),(0,2),(1,2)` | `(0,3),(2,3),(1,4),(4,4),(2,5),(5,5)` |
| Quadratic shear | `(r+c*c, c)` | `(0,0),(1,0),(0,1),(1,1),(0,2),(1,2)` | `(0,3),(2,3),(1,4),(4,4),(2,5),(5,5)` |
| Hinge shear | `(r+max(c-1,0), c)` | `(0,0),(1,0),(0,1),(1,1),(0,2),(1,2)` | `(0,3),(2,3),(1,4),(4,4),(2,5),(5,5)` |
| Absolute-value shear | `(r+abs(c-2), c)` | `(0,0),(1,0),(0,1),(1,1),(0,3),(1,3),(0,4),(1,4)` | `(0,-1),(2,-1),(1,2),(4,2),(2,5),(5,5)` |

The absolute-value training set spans both sides of the kink, so an affine fit on only one side cannot silently count as transfer. The lock also carries an identity-aligned exhaustive finite-bound check showing which families admit an exact integer 2×2 matrix on their training points.

## Search arms and budgets

Evaluate five fresh native substrates per task/grammar cell (40 acquisitions total) with explicit grammar and constant pools:

- `plus_tuple`: `Plus, TupleOf`; no constants; max size 7.
- `plus_times_tuple`: `Plus, Times, TupleOf`; no constants; max size 7.
- `plus_minus_tuple`: `Plus, Minus, TupleOf`; constants `{0,1,2}`; max size 9.
- `plus_minus_max_tuple`: `Plus, Minus, Max, TupleOf`; constants `{0,1}`; max size 9.
- `plus_minus_abs_tuple`: `Plus, Minus, Abs, TupleOf`; constant `{2}`; max size 8.

Run only the preregistered task/grammar pairings: linear under `plus_tuple` and `plus_minus_max_tuple`; quadratic under `plus_tuple` and `plus_times_tuple`; hinge under `plus_minus_tuple` and `plus_minus_max_tuple`; absolute-value under `plus_minus_tuple` and `plus_minus_abs_tuple`. This gives each nonlinear family one grammar with its needed operator and one ablation without it. Each search has a 150,000-candidate cap. The native search's own found/refused/budget/saturation status is retained; no candidate or grammar is added after observing outcomes.

For every found candidate, record the exact Term JSON and apply it to all six withheld rows. Also measure 1/2/5/100 repeated applications over the locked held-out set. Acquisition cost includes the native call and Python binding; application cost includes native evaluator calls and Python validation. Report candidate counts, search halt reason, acquisition wall/CPU time, median per-application time, and process peak RSS. No repeated search should be counted as reuse.

## Integrity and admission gates

The independent analyzer must verify: frozen protocol/runner/analyzer/source/native hashes before and after execution; exact 40-cell task/grammar/repetition coverage; exact training/held-out input tables; one fresh substrate per search; nonnegative, internally consistent candidate accounting; and independent re-evaluation of every returned Term on the locked held-out pairs against independently reconstructed targets. Require the linear positive control to be acquired and exactly transfer in at least 4/5 `plus_tuple` repeats. Report every ablation result, including any unexpected exact transfer; do not silently treat `found` as successful generalization. A failed source, task, or positive-control gate makes the run inconclusive.

## Interpretation limits

Tasks are deterministic synthetic maps, not sampled natural tasks. Grammar, integer constants, term-size limits, and candidate cap define the tested hypothesis class. Successful induction is an executable Term returned by `SynthEnumerate`, not acquisition/adoption of a new shape-decode primitive. The repeated applications measure direct native Term evaluation; they exclude graph boot, long-term storage, rule closure, and end-to-end task orchestration. Repeated measures do not create independent statistical units; report exact task-cell outcomes and cost ranges without population confidence intervals.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_synthenumerate_nonlinear_map_v1.py --lock
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_synthenumerate_nonlinear_map_v1.py
python3 scripts/analyze_substrate_synthenumerate_nonlinear_map_v1.py
```
