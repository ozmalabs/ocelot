Design delivered above, and saved to memory. The short of it:

- **Postulate = a reified Rule** with two interpreters — TEST (residual on recorded frames) and DEDUCE (roll forward in a scratch subgraph). Three world-agnostic shapes: transport, kinematic+reflection, contact-consequence (the relational lift of operant `consequence`).
- **Induce = BPL/MDL** over a law-grammar, scored by prediction-minus-observation + description length, generated and selected graph-natively (no donkey). The **action-dependence discriminator** comes free from the no-op frames already in the stream — it's what fixes both generality gaps you named.
- **Deduce = roll held postulates forward in a hypothetical arena** to foresee a death you've never suffered, lead a moving goal, reject a self-sealing plan — reusing navigate_alive/select_action against the rollout instead of the live frame.
- **Complement by coverage**: an uncovered transition returns UNKNOWN, which *is* the existing curiosity/untasted-kind signal → operant runs the one experiment that can't be observed → induces the postulate → never re-suffered.

The one thing I need from you before (c) is composition-only: **does the Rust `run_rules` already accept a node-scope filter?** If yes, no new primitive — I tag the snapshot and restrict. If no, that's my HumanImpasse: `rollout(seed_nodes, rule_ids, n_steps) → deduced_trajectories`.