# Finite-key join/topology v1.1 — fresh-process confirmation amendment

**Status: preregistered after the v1 capture and before confirmation.** The v1
matrix completed with all 210 native cases passing; this follow-up checks exact
semantic replication in a second interpreter process without changing the
workload.

## Procedure

- Use a separate versioned runner with the same graph generator, rule forms,
  arities, cell schedule, warmups, and timing regions.
- Repeat all 42 configurations × five fresh substrates; preserve the second raw
  capture separately.
- Run the independent per-capture topology oracle on both raw files.
- Compare case IDs and exact semantic records (binding counts, terminal-node
  counts, graph digests, closure status, progress report, bounds, and checks).
- Require identical non-runner native/source digests. Do not require timing
  equality; retain separate process timing summaries and ranges.

## Claim boundary

This confirms the authored join/topology matrix on the same source/build. It
does not establish a natural workload distribution or general complexity law.
