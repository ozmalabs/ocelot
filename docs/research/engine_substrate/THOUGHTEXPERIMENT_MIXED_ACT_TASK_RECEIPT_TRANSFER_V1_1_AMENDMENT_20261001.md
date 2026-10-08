# Mixed-act task receipt transfer v1.1 serialization amendment

**Date:** 2026-10-01, after the v1 locked workers completed their task execution but before a valid aggregate capture was produced.

## Disposition

All eight v1 worker processes completed their three task episodes, but the parent runner could not JSON-serialize a native `NodeID` nested in `final_state_attrs`. It retained the failed worker capture; because every worker row contains a serialization error instead of its result, no v1 semantic or timing claim is made from it. The pre-lock development pilot is also excluded.

## Correction

Use explicit JSON fallback serialization for NodeID-valued readback fields and write v1.1 outputs to new paths with a new source lock. Do not overwrite or pool the failed v1 capture. No task fixture, arm, operation order, expected outcome, gate, or timing stage changes. This is a capture-format correction only.
