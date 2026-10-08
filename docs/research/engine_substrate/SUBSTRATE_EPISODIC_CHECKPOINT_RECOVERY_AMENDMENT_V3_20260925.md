# Episodic checkpoint recovery harness amendment v3 — 2026-09-25

The v2 harness completed the fresh-process workers but attempted to read the intact checkpoint's byte size after leaving the `TemporaryDirectory` scope. The file had already been deleted, so no aggregate report was written. The v3 harness captures checkpoint size while the directory is live. Checkpoint variants, task data, scoring, and reader behavior are unchanged. V1 and v2 locks and failures are retained; this amendment and v3 lock precede the next scored run.
