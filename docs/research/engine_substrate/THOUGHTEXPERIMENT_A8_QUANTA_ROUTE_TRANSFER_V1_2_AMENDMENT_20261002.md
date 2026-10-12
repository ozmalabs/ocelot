# Thoughtexperiment A8 quantum-route transfer v1.2 — semantic receipt and new mazes

**Date:** 2026-10-02  
**Reason:** v1.1 produced useful path traces but its receipt comparator rejected valid candidates because the native rule replacement API reorders equivalent match edges. The primary-isolation checks passed; candidate/source/fault receipt checks did not. The v1.1 analyzer is retained as failed evidence.

Define a rule receipt over exact target name, match-edge multiset (edge ordering is semantically immaterial, but multiplicity remains significant), exact `where` structure, exact effect sequence, and exact literals/operators. Add a lock-time receipt preflight that replays source and `flip_comparison` candidates into isolated full-copy branches, accepts equivalent match-edge reordering, and rejects changed guards, operators, values, and effect order. No maze outcome is run during preflight.

The amended held-out set retains H1/H2 for diagnostic continuity and adds two unscored mirrored portal worlds: H3 is a vertical wall with the opening at row 1, start `(4,0)`, goal `(4,4)`; H4 is a horizontal wall with the opening at column 3, start `(4,4)`, goal `(0,4)`. Candidate and source/fault scoring covers all four worlds. Since v1.1's path behavior was inspected, the v1.2 outcomes are a source-locked expanded replication rather than a first-look estimate.

Capture a new lock and order file, inspect graph attribution and no-cue abstention again, then score. Preserve all prior versions unchanged. A pass supports transfer to these four authored portal layouts only; route search under arbitrary topology and general self-improvement remain open.
