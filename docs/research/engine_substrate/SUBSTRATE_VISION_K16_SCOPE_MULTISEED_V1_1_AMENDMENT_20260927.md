# K=16 scope multi-seed capture v1.1 amendment

The first capture completed all six arms and produced semantic records, but failed its source-stability gate. The worker recorded the dynamic project import closure before calling `engine_preamble()` and before the arm lazily imported the evaluation I/O guard. The end-of-worker closure therefore had three additional source files (`evaluation/__init__.py`, `evaluation/p0a/__init__.py`, and `evaluation/p0a/legacy_io_guard.py`). This is a harness snapshot-timing defect, not a measured rule or response difference.

V1.1 primes the exact evaluator guard module before taking each worker-start fingerprint. No workload, seed, intervention, or numerical criterion changes. The failed v1 raw capture remains preserved and inadmissible for a source-stable claim. V1.1 has separate runner, lock, raw capture, and analysis paths.
