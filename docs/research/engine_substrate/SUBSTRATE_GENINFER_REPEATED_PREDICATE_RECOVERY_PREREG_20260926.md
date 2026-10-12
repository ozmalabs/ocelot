# GenInfer repeated-predicate recovery factorial preregistration

**Lock date:** 2026-09-26, before capture. **Question:** how do repeated-predicate point assignment and within-predicate numeric disagreement affect recovery of a known 2-D linear generator, and how often does GenInfer accept a decomposition while selecting another matrix?

Use the known matrix `[1,1,0,2]` and points `(0,0),(1,0),(2,0),(0,2)`. Cross three assignments of two `p0` and two `p1` observations—`p0` indices `(0,1)`, `(0,3)`, `(1,2)`—with five perturbations to target coordinate slot 1 on the two `p0` observations: `(0,0)`, `(1,1)`, `(2,2)`, `(1,2)`, `(1,3)`. Preserve source predicate labels and all other coordinates/values. Evaluate each of 15 cells five times with `max_dims=2`; capture `explained`, `matrix`, `residual_dims`, `transforms`, `dims`, and `checked`.

Primary outcome is exact generating-matrix recovery. Secondary outcomes are decomposition acceptance (`explained`), residual support/count and repeat determinism. The positive `(0,0)` cell must recover exactly with no residual; every call must report 6,560 checked matrices. For perturbed cells, record outcomes without assuming recovery or refusal. The analyzer independently reconstructs every input and verifies cell balance, outputs, and provenance.

This is a controlled evaluator study, not a natural-noise distribution or full-seed mint/reuse result. Five repeats estimate deterministic stability, not population uncertainty.

Reproduction: `PYTHONPATH=runners/dsl/python:. python3 scripts/geninfer_repeated_predicate_recovery_probe_v1.py` followed by `python3 scripts/analyze_geninfer_repeated_predicate_recovery_probe_v1.py`.
