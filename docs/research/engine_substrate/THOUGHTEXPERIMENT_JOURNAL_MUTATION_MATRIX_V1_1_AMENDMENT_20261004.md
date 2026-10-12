# Journal mutation matrix v1.1 execution amendment

Date: 2026-10-04

The original v1 lock named `cargo run --release`, but the available build
completed in Cargo's `dev` profile after the release-profile session stopped
returning output. The resulting uncommitted output was exploratory and is
excluded from confirmatory evidence. V1.1 fixes the execution command to
`cargo run -j 2 --bin thoughtexperiment_journal_mutation_matrix_v1
--manifest-path runners/dsl/Cargo.toml`; no timing is collected, so the
profile change affects only build cost. The amendment, runner, and all source
inputs are locked before the confirmatory rerun. Semantic gates and case
definitions are unchanged.
