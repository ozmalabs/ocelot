# Recurrence repair parallel thoughtexperiment wave v2 — GIL-release comparison amendment

The v1 capture measured branch fork bindings that retained the GIL. Current PyO3 full-copy/shared-page fork bindings release the GIL around native branch construction while preserving wrapper eligibility checks and native mutex/fork semantics. V2 holds fixture, rule repair, fanout, oracle, sampler, and mode ordering constant to measure the effect on this distinct recurrence task. Per-branch thread CPU is recorded in addition to existing wave wall and PSS/RSS metrics.
