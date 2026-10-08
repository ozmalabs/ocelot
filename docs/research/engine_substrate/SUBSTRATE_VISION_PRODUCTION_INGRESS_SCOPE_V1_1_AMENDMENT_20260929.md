# Production visual ingress and frame-scope pilot v1.1 amendment

The initial v1 capture completed 32 workers but is censored: Rust source `runners/dsl/src/rewrite.rs` changed during capture, and the loaded extension became stale relative to that source. Preserve its lock and raw JSON as provenance of the interrupted-source attempt; do not combine its rows with the confirmatory capture.

The current Rust tree was rebuilt with `scripts/engine_build.sh` using the supported safe install path. The rebuilt native extension and build record are included in a new source lock. V1.1 repeats the same preregistered 32-worker design and uses separate lock, raw, analysis, and result paths. The repeated capture begins only after two source-lock probes, 20 seconds apart, agree. It is a procedural repeat, not an independent replication.

The v1 runner and raw report remain unchanged. The v1.1 runner differs only in versioned artifact names and this amendment's protocol hash; all conditions, transformations, checkpoints, metrics, and analysis rules remain the same. Any subsequent source/native drift censors v1.1 as well.
