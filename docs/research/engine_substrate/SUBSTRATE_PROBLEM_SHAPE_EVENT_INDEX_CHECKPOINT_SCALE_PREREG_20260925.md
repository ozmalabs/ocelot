# ProblemShape event/index checkpoint scale preregistration

**Status:** fresh-process graph-checkpoint scale envelope for the all-transition event variant.

## Question

How do full `WorldAdapter` checkpoint size, save/load time, and RSS change as the same recurrent ProblemShape workload grows from N=2 to 32 observations, and does each checkpoint preserve the settled event/index/codebook state in a distinct reader process?

## Design

Run N=2, 8, 16, and 32. Each size has a fresh writer process and a fresh reader process. Writers boot full seeds, install the locked all-transition rules, run the fixed recurrent-residual task sequence to fixed point, and save. Readers call `WorldAdapter.load` in a separate process and verify the graph state before and after an additional rule settle. Use the same candidate runner functions and workload generation as the N=8 recovery result. Record graph node/edge counts, checkpoint bytes, save/load wall times, peak RSS, and exact semantic projections.

## Acceptance

For every size, writer and reader must agree by goal ID on observation key/status/coverage/decode epoch; minted shape key/support; final per-key index support; event counts; codebook epoch; active ProblemShape rule names; and fixed-point status. All observation/index and `about_goal` relations must be exact; all worker PIDs must be distinct. Preserve every size and failure.

## Limits

This is a four-point synthetic checkpoint envelope for the full default adapter graph. It is not corruption recovery, concurrent access, crash consistency, or natural-task scale evidence. It measures serialized whole-adapter cost, not a minimal ProblemShape checkpoint.
