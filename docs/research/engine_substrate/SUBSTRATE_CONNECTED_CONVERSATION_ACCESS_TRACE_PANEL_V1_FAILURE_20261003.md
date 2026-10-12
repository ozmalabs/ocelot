# Connected-conversation access-trace panel v1 startup failure

Date: 2026-10-03

The v1 runner acquired its source lock, then stopped in the parent process before starting any worker. The failure was `NameError: name 'datetime' is not defined` while recording the run start time. No task case ran and no output capture was written. The v1 source lock is retained as provenance. V1.1 imports the missing `datetime` and `timezone` names, references the failed v1 runner/lock/method here, and uses a fresh lock. This correction does not change the task cases, instrumentation, metrics, baseline, or acceptance gates.
