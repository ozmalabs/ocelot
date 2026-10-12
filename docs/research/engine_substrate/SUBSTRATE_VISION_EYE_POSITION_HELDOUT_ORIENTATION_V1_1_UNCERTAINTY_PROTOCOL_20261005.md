# Position-held-out orientation v1.1 uncertainty analysis

This is a post-hoc, source-locked uncertainty summary of the completed six-seed v1 panel; it does not rerun the substrate or alter the preregistered readout. Treat the seed as the replication unit because eight held-out probes within a seed share the same learned weights.

Report learned-minus-initial correct-count difference per seed, win/loss/tie counts, an exact two-sided sign test on non-tied seeds, and the percentile interval from all 6^6 bootstrap resamples of seed-level accuracy differences, using nearest-rank 2.5th and 97.5th percentiles. Also report class-stratified correct counts and paired probe discordances descriptively; do not treat probes as independent replications. Lock this analyzer, protocol, and the v1 capture/analysis hashes before calculation.

This analysis is exploratory and only quantifies uncertainty for the authored bar task. It cannot upgrade the measured outcome into a general position-invariant learning claim.
