# Preregistration: guarded ordering on authored CAN workloads

**Question.** Does the benchmark-only forest detector and leaf order behave as measured on authored/runtime-generated CAN structures, and what does the boundary contract do with duplicate, self-loop, and invalid endpoints?

**Workloads.** (1) All 100 residents in the authored Bigville cast after scenario evidence is applied, using the existing five-concept 3-state CAN builder. (2) The 80 fixed conditions from the current native CAN fixture (2/3-state × coarse/fine weights × 20 seeds), after native asynchronous rule closure and terminal probe. Every graph is extracted through the current CAN network adapter. The exact width gate remains four. Bigville cases admitted by the gate are checked against exhaustive 3^5 enumeration. Complete native CAN cases above the gate are refused; no direct exact solve is attempted.

**Policy.** Normalize extracted edges to local integer endpoints. Use union-find cycle detection; only forests receive leaf elimination. Cyclic graphs reuse min-fill. The selected-order width is computed from the elimination triangulation and determines the same width-4 exact/refusal decision. Separate direct detector controls cover duplicate undirected edges, self-loops, negative endpoints, and out-of-range endpoints. Invalid endpoints are rejected before ordering; duplicates and self-loops conservatively fall back.

**Measures and pass conditions.** Forest/nonforest classifications by source family, min-fill and selected widths, exact gate status, exact MAP parity on admitted Bigville cases, native closure settlement, malformed-input actions, and component timings. Pass requires every exhaustive oracle to agree, every native fixture to settle, complete width-7 graphs to fall back/refuse, and malformed controls to follow the stated actions. No performance threshold is imposed.

**Claim boundary.** These are project-authored deterministic workloads and explicit synthetic controls, not a natural graph sample, production dispatch implementation, or evidence that forest structure is common.

## Transparent harness amendment before scored rerun

The first invocation completed the authored Bigville cases but failed while assembling the native-closure audit row: the runner applied len() to an edge count already stored as an integer. No final artifact was written. The row now copies the integer count directly. Workloads, policy, metrics, and pass criteria are unchanged; the lock is amended before the scored rerun.
