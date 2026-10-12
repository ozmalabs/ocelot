# CAN width-two ladder inference scale preregistration

**Question.** Does the current exact junction-tree MAP path retain exactness and a bounded-width scaling profile on runtime-extracted binary ladder models, beyond the existing width-one path envelope?

## Generator and oracle

For rung count m, create 2m Concept nodes. Each rung has one vertical pair factor; adjacent rungs have top and bottom rail factors. Generate deterministic seeded unary and pairwise weights on quarter increments. Extract the model through can_network_from_mt and require exact unary/pairwise parity with the generated model.

The independent oracle is a four-state rung dynamic program implemented in this runner. Its state is the pair of binary variables in one rung; it enumerates all four predecessor/current combinations for every adjacent rung. This is separate from the junction-tree implementation.

## Locked sweep

Run fresh workers for m = 16, 32, 64, 128, 256, 512, with three fixed replicates each. Measure graph extraction, generic min-fill ordering, junction-tree MAP using that order, and junction-tree MAP using a fixed rung-order elimination sequence. Record treewidth upper bound, max bag size, traced Python peak, process peak RSS, and independent oracle work count. Require width 2 / bag size 3, exact extraction, and both exact-inference energies to match the rung-DP oracle for every worker.

Source, fixture generator, native artifact/build provenance, protocol, and runner are content-locked before execution. The sweep measures one synthetic topology family and is not natural-task locality evidence.
