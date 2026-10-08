# Instrumentation overhead v1.1 analysis amendment

Date: 2026-10-04

The original post-capture analyzer verified that each arm independently
matched the direct monolithic oracle, then compared only the resulting parity
booleans across paired arms. That was too weak to claim exact pairwise semantic
outcome parity. The capture is unchanged; the amended analyzer compares a
frozen projection of each candidate's identity, grounding outcome/evidence,
grounded-frame count, closure work and quiescence, and residual counts. It also
checks the baseline graph digest and selected candidate across each pair.

All six pairs pass the amended comparison. Continue to use the original
pre-run source lock for capture provenance and cite the v1.1 analysis for
pairwise semantic parity. This is a disclosed post-capture analysis correction;
the paired schedule and captured observations were not changed.
