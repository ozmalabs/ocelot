# Spectral primitive I/O oracle v1.6 analysis amendment

**Amendment timing:** after the v1.6 raw capture and before a valid analysis was produced.

The first analyzer draft contained an invalid integrity assertion: it treated the graph-local `codebook_epoch` (which correctly begins at zero in every fresh graph) as a globally unique graph identifier. The assertion failed before writing an analysis. The raw capture is unchanged and retained. No runner, fixture, source lock, case, or outcome was changed.

The corrected analyzer checks the preregistered 12 unique arm/case combinations rather than inferring graph identity from the epoch. It also evaluates each captured forward Term tree with the current native evaluator and independently compares those outputs against the separately calculated direct-DFT values, strengthening the original oracle check. The original experiment source lock remains authoritative for the runner and implementation used during capture; this amendment locks the corrected analyzer and this amendment text separately. The analyzer must confirm that all captured execution sources other than the analyzer itself remain byte-identical to the v1.6 lock. Any other source drift invalidates this analysis replay.

The correction only repairs the validation procedure and strengthens numerical verification. It does not change the preregistered outcome criteria or interpretation boundary.
