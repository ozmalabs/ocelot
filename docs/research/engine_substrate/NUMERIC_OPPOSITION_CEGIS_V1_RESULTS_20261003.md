# Numeric opposition counterexample-guided synthesis v1 results

Date: 2026-10-03

## Result

The source-locked five-worker run completed with independent analysis passing
all integrity checks. Each worker repeatedly rebuilt the bounded version space
after each selected oracle label. All five reached a singleton that scored
exactly on the disjoint 1,296-case fractional grid. Four workers used two
counterexample labels; one used three, for 11 labels total. Candidate counts
by synthesis round were 9→4→1 in four workers and 10→5→3→1 in one. The run
performed 16 synthesis rounds, with per-round median synthesis wall time of
8.48 seconds. The active query choices were replayed from the recorded
candidate sets and fixed pool.

The analyzer replays label history, verifies every captured candidate against
the examples available at that round, recomputes the entropy query choice, and
rescores the final terms. It does not independently rerun the full enumerative
synthesizer to reconstruct each complete candidate set; synthesis completeness
is therefore supported by the source-locked capture rather than a second
enumerator implementation.

This advances beyond the earlier fixed-version-space query study: labels now
change the examples and the synthesizer runs again, rather than merely
filtering an immutable candidate list. The result is still narrow. It uses one
authored relation, a fixed `Neg`/`Eq`/`And` grammar that contains the target, a
fixed query pool, and labels from a local known-relation oracle. The target was
not supplied to the learner, but the harness has access to it. The result does
not show reliable adequacy detection: a singleton can still be wrong when the
target is outside the grammar, as the separate misspecification study found.
Nor does it demonstrate task or primitive invention, unrelated-family
transfer, or autonomous adoption of improvements.

## Artifacts

- [Preregistration](NUMERIC_OPPOSITION_CEGIS_V1_PREREG_20261003.md)
- [Runner](../../../evaluation/substrate_capability/measure_numeric_opposition_cegis_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_numeric_opposition_cegis_v1.py)
- [Source lock](../../../evaluation/substrate_capability/numeric_opposition_cegis_v1_lock_20261003.json)
- [Capture](../../../evaluation/reports/numeric_opposition_cegis_v1_20261003.json)
- [Analysis](../../../evaluation/reports/numeric_opposition_cegis_v1_analysis_20261003.json)
