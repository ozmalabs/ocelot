# Live perception self-repair repeatability gate v1 (preregistration)

Question: does the existing live ARC self-repair episode repeatedly complete its measured-regression → graph-minted Fault → deferred rule edit → post-repair recovery gate path in fresh processes on the current source/build?

Run `scripts/jabberwock_live_self_repair.py` unchanged in three fresh Python processes. The wrapper captures raw stdout/stderr, exit status, wall/CPU time, auto-mint/repair frame, and gate outcome. Lock the runner, analyzer, preregistration, live episode script, adapter/boot/seed-generation/world files, Rust/PyO3 engine sources, native build metadata/binary, and every root/generated seed manifest loaded by `load_all_seeds`.

Pass requires all three runs to exit successfully, report an auto-minted fault and auto-repair in the same measured episode, report gate outcome `kept`, and finish with self axis kind `controllable`. Each process must observe identical source/native hashes before and after. This is an execution/repeatability result for an existing hand-configured repair episode. The setup deliberately installs a broken discriminator and configures the CapabilityAxis with the target rule/field and corrected effect; those inputs are not discovered by the substrate. It therefore does not meet target-blind diagnosis or learned self-improvement. No performance comparison is planned.
