# K=16 scope multi-seed capture v1.2 amendment

V1.1 established paired response parity but did not capture the preregistered within-arm readout weight-drift check. V1.2 wraps the existing `cell_stats` call in each worker and records the complete ordered `oo_post` weight vectors immediately before and after the readout, along with hashes and maximum absolute change. The independent analyzer recomputes hashes and deltas from those vectors and reconciles each post-readout hash with the arm's returned final-weight hash.

The scope intervention, full-rescan executor, seeds, development/adaptation sequence, K=16 readout, and parity tolerance are unchanged. The v1.1 run remains the response-only result and is not retroactively upgraded by this amendment. V1.2 has separate source lock, runner, raw capture, and analysis artifacts.
