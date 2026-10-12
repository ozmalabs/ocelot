# CAN grid boundary-width scale v1.1 harness amendment (2026-09-29)

The v1 runner's initial locked invocation stopped before worker launch because `domains.engine_provenance` was not importable when Python executed the runner by absolute path. No benchmark workers ran and no raw result capture was produced. The v1 lock is retained as the record of this failed preflight.

The corrected runner explicitly adds the repository root to `sys.path` before importing the provenance checker. Workload, model generation, oracle, dimensions, timings, and correctness gates are unchanged. V1.1 uses a new runner, lock, and output name; its source lock is created only after this amendment and corrected runner are frozen.

