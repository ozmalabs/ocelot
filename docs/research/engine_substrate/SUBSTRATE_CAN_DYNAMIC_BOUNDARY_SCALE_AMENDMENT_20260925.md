# CAN dynamic boundary scale pilot — v1.1 amendment

The initial locked command stopped while serializing the first case result: the new `frame_count` metadata read an undefined local name (`mts`) instead of the returned frame list (`lmts`). The event/full-rescan procedure for the first cell had run, but the exception occurred before any result file was written, so that partial cell is excluded and not counted as evidence.

This adapter-only correction changes the metadata expression to `len(lmts)`. It does not change the frozen N values, frame size, mutation set, budgets, event notification policy, metrics, or decision rule. The original preregistration and lock remain intact. Version 1.1 uses a new runner hash and amended pre-execution lock, then reruns all 16 registered cells from fresh graphs.
