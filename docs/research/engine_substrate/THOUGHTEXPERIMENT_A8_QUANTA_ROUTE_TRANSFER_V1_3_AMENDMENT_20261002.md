# Thoughtexperiment A8 quantum-route transfer v1.3 — corrected portal oracle

**Date:** 2026-10-02  
**Reason:** v1.2's path oracle transposed row and column for off-diagonal portal openings. Its captured outputs and failed analysis remain immutable evidence of an oracle defect; no v1.2 utility conclusion is used.

Correct `crossed_opening`: a vertical wall at column 2 opens at `(opening, 2)`; a horizontal wall at row 2 opens at `(2, opening)`. Define a successful case as reaching its goal within 16 moves, with no wall hit, crossing that opening, zero residual `closed`, no minted hypothesis, a verified rule receipt, and an unchanged primary graph. Lock-time preflight still constructs worlds without running navigation outcomes, and receipt controls remain active.

Keep H1-H4 as diagnostic replication because their behavior was exposed in v1.2. Add fresh primary held-out cases H5 and H6: H5 is a vertical wall with opening row 3, start `(0,4)`, goal `(0,0)`; H6 is a horizontal wall with opening column 1, start `(0,0)`, goal `(4,0)`. Both primary cases use off-diagonal openings and orientations/start-goal directions that differ from the earlier layouts. Score every candidate and source/fault control on all six, but report the preregistered transfer gate on H5/H6 separately from H1-H4 diagnostics.

No target rule, cue, operator, candidate enumeration, receipt definition, or branch isolation method changes. Capture a new source lock, inspect prompted graph attribution, target preservation, no-cue abstention, and held-out blindness before scoring. A pass supports only transfer to these six authored portal layouts; arbitrary topology and general self-improvement remain open.
