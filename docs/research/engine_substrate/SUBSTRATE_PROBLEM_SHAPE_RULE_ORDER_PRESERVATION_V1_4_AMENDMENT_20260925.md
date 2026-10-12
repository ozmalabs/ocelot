# Amendment V1.4: immutable shared seed snapshot and ordered boot diagnostics

Date: 2026-09-25

V1.3 was invalidated because its transformed seed corpus used symlinks to live source files, the seed corpus changed during setup, and active-rule fingerprints differed between a worker and a standalone boot diagnostic. V1.4 builds read-only copies of every seed file for both arms from one source snapshot. The baseline uses the untouched `problem_shape_growth.json`; the candidate uses an in-place transformed copy of that manifest. All other seed bytes are identical. Snapshot construction hashes source bytes before and after copying and aborts on drift. The runner verifies the complete snapshot digest immediately before and after every worker.

Both worker arms emit the ordered active-rule names after seed load and immediately before observations, seed-load order, and failed seed IDs. The first scheduled pair is a diagnostic gate: semantic outcomes, ordered names, load order, and ProblemShape positions must agree before later pairs can proceed. Final active-rule order remains an outcome, not a validity gate.

The repeated comparison retains V1.3's N=32 recognition and recurrent-residual workloads, 6 randomized baseline/candidate pairs per mix, full per-rule counters, and `PYTHONHASHSEED=0`. The source corpus digest is frozen in the V1.4 corpus lock and rechecked before snapshot creation. Results remain exploratory evidence for these two authored workloads only.
