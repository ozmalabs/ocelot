# K=16 settle on/off ablation v1.1 amendment

Date: 2026-09-25. Preserve the v1 raw report, including its `pass=false` runner outcome.

The runner incorrectly expected 192 probe calls, counting only the 12×16 tuning samples. `cell_stats` additionally performs 32 baseline presentations and 16 units × 16 preferred-orientation phase-response presentations for F1/F0, for 480 total. The raw arm records contain all 480 exact tick progress values in each condition; all independent call-count and work checks use that observed 480. This harness assertion does not invalidate the measured states or counts.

The preregistered estimand remains the paired settle-on/off response and work change after identical development/adaptation. Report exact tuning parity and work counts. Tick returns are integer progress counts; they do not report fixed-point versus repeated-state reason. Timing is one paired observation only.
