# Minimal ProblemShape continuation checkpoint preregistration

**Status:** isolated runtime-contract probe; no production/default persistence change.

## Question

Can the all-transition ProblemShape rules continue classification and mint/re-decode from a minimal domain checkpoint instead of serializing the full default adapter graph? What state is required, and how much smaller is it?

## Minimal checkpoint contents

The bundle contains: the Agent node with codebook epoch; already prepared Goal nodes and their `about_goal` relations; all current ProblemShape observations/edges/attrs; the held ProblemShape codebook; the graph-resident support index and index links; pending/decoded/residual events; exactly the five active ProblemShape rules; and only the Γ productions needed for those graph types/relations. It excludes unrelated default faculties, memories, solver-internal graph state, and unrelated rules. Goals are resolved before checkpoint; the resumed contract is to classify those prepared goals, not to continue the general solver or restore a complete WorldAdapter.

## Arms and gate

At N=8 recurrent residual, run one uninterrupted full-adapter arm and one compact-write/compact-read arm in separate processes. Compact write saves immediately after observation 1 reaches residual and its mint-candidate event is live. Compact read restores into a fresh native Substrate, imports selected Γ productions and five rules, reconstructs the host key lookup, then classifies goals 2–8. Compare states keyed by goal ID: observation signature key/status/coverage/decode epoch, minted shapes and support, index support, event counts, codebook epoch, active rule names, and fixed point. Verify `about_goal` and index links and require the compact checkpoint to be below 5% of the full-adapter N=8 checkpoint. Record checkpoint bytes, write/read time, node/edge/rule/production counts, and peak RSS.

## Limits

This is a fixed eight-goal continuation contract for the ProblemShape faculty. It does not restore `WorldAdapter`, solver execution, unrelated faculties, or external Python adapter state. It is not permission to replace full checkpoints. Any future application use must establish that the narrower contract matches its actual restart boundary. No corruption, torn-write, concurrency, migration, or large-scale guarantees follow.
