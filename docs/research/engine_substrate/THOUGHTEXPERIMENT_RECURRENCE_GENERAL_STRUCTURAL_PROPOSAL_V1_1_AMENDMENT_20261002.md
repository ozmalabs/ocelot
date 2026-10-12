# Recurrence general structural proposal v1.1 amendment

The v1 order capture did not produce worker data. Its runner compared `sys.argv[1:]` (which includes the worker index) with a one-element `--order-worker` list, so it exited with usage text before launching worker 0. The v1 lock is preserved as the source record for this failed attempt; its lock hash must not be used for outcome claims.

V1.1 corrects the command dispatch and writes separate lock, order, score, and analysis paths. The task, cue, worker count, candidate reference, scoring order, and gates are unchanged. The amendment and corrected analyzer/runner are included in the new source lock before capture. No outcomes from the failed v1 attempt are carried forward.
