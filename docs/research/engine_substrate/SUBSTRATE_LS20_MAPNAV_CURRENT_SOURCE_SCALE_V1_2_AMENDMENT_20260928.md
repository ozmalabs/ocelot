# LS20 map-navigation current-source scale panel v1.2 amendment

**Date:** 2026-09-28

V1 was fully executed but censored because `scripts/` and `substrate/` source digests changed. V1.1's first lock attempt stopped before task execution because its broad `scripts/` digest changed. V1.1's second lock passed its initial gate and ran all 150 paired scenarios, but its final lock changed under `domains/`; that 150-pair output is preserved as censored and was not analyzed for outcomes.

A separate representative paired-run import census enumerated 40 Python files loaded by the actual benchmark path, including the quanta route. V1.2 hashes this exact runtime file closure instead of unrelated unimported Python sources, while retaining full Rust/Cargo, native facade/build, and recursive seed-closure hashes. It uses a fresh PCG64 seed block `222200`–`222204`, keeps all v1 task cells and gates unchanged, and writes to an isolated v1.2 output path. The initial v1.2 lock is created only after this amendment and protocol; any mismatch during or after the run censors the data and stops analysis.

V1 and v1.1 remain preserved, separate censored attempts. No outputs from those attempts were inspected for task correctness or used to tune v1.2 conditions, thresholds, or algorithms. V1.2 is the confirmatory source-current sample for this task family, not an independent replication of another accepted result.
