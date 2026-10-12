# Post-hoc analysis v1.2 amendment

The v1.2 report is preserved but invalidated. Reconstructing `set(sorted_mask)` does not preserve the insertion history of the corruption set created by the reference routine. Since floating-point addition follows set iteration order, that scorer's reconstructed values can still differ near ties.

The v1.3 analyzer recreates each corruption set from the original clean mask using the locked deterministic corruption procedure, then sums over that same set object. It has a separate source lock and protocol. Do not use v1.2 exact-max counts as a native parity result.
