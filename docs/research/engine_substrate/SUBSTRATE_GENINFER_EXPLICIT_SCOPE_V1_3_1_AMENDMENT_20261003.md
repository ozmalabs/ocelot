# Explicit GenInfer scope v1.3.1 interpretation amendment (2026-10-03)

The v1.3 result's externally checked `FrameScope` metadata verifies the
benchmark's synthetic assignments; it does not mean the native engine
validates that metadata. A follow-up source-locked 36-worker probe varies the
provenance record while holding matching part/observation `scope_id` tokens
constant. Correct, absent, and contradictory records each lead to 12/12 exact
target acquisitions. Therefore native GenInfer enforces exact token filtering
and missing-token abstention, but does not validate a token's provenance. Any
v1.3 statement that required mode abstains when provenance is unavailable or
invalid describes a desired contract, not current measured behavior.

This amendment preserves all v1.3 locked files and measurements, narrows their
interpretation, and adds the provenance gap to the capability map and next
work. See the [provenance preregistration](SUBSTRATE_GENINFER_SCOPE_PROVENANCE_V1_PREREG_20261003.md), [results](SUBSTRATE_GENINFER_SCOPE_PROVENANCE_V1_RESULTS_20261003.md), and [analysis](../../../evaluation/reports/substrate_geninfer_scope_provenance_v1_analysis_20261003.json).
