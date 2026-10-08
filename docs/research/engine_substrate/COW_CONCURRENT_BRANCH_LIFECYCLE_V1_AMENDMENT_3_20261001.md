# Concurrent branch lifecycle v1 amendment 3 (2026-10-01)

The initial preregistration said backend order would be randomized. The implemented fixture instead uses deterministic counterbalancing: shared snapshot then eager copy on even repetitions, and eager copy then shared snapshot on odd repetitions. This preserves paired order control but is not randomization. The captured row order confirms the schedule. This amendment corrects the protocol description; no outcomes or gates are changed.
