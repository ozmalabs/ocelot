# Numeric opposition learning v1 analysis amendment (2026-10-03)

The locked v1 runner and raw capture are unchanged. Its initially locked
analyzer could not import the native module when launched as a standalone
script because it omitted the repository's `runners/dsl/python` path. The
capture completed and the runner recorded per-worker held-out confusion
counts, but the analyzer did not produce a valid report. This amendment adds a
separate corrected analyzer that imports the same current native engine and
independently recomputes training fit and all 1,296 held-out predictions from
the captured candidate ASTs. It does not alter candidate generation or use
held-out data for resynthesis. The original analyzer is preserved as captured
in the source lock.
