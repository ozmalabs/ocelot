# P22 candidate-specific simulated-adoption request: D4 g1 continuation

**Status: consumed.** The user approved the exact digest and reported 12
review seconds. Approval `#45861` and verified receipt `#45865` produced
generation-two checkpoint `p22-d4-g2-84854777d0e3`, digest
`d8a916474c8e3bafd44dda0082fd7c71ccb3dac1c0a2daf9bbe7f759c70fb4df`.
The raw result `p22_approved_candidate_d4_g1_0818_0821.json` has SHA-256
`f72db827c1e05f382ae7fd84c1655f4f0c4d1cac61dbe57823438d092feb1bc7`.
This action authorizes no later transition.

Candidate `#9458` has digest
`84854777d0e3b48f447ecd04236a794eff39a46546edb3f19e47f506492ce66a` and is
qualified as `#15851` (`independent_goal_composition`). The selected witnesses
are training worlds 0960 and 0818. The verified source transition on fresh
world 0818 derives child candidate `#12174`; both candidate and child effects
are absent from the registered invention-only g1 parent's active effects.

The action performed exactly one training-simulator transition on D4 training
draw 0818, with a conditional generation-two checkpoint after the native
receipt verified. No later action is authorized by this approval.

The parent is the verified generation-one checkpoint
`p22-d4-g1-2d2cb9ecda29` (digest
`6fabe1c4d1bdaaafa5015c0ac3e4d43cc5759c380445be0df60420d8ac6550c8`). The
source artifact `p22_training_panel_registered_root_d4_g1_0818_0821_ticks60_depth3.json`
has SHA-256 `406d2015fbc8ecf1b74b3349b66618339448add8603adb11c42dac093eaa7798`;
the exact replay
`p22_training_panel_registered_root_d4_g1_0818_0821_ticks60_depth3_replay.json`
has SHA-256 `750b46cc6c2e13ffc8ab36af03c17690408a8814c2eb1ed4e7e651f9259fb8f1`.
Both reproduce the digest and qualification, retain the inherited single
approval/receipt, and have empty validation allocations. The approved result
adds exactly one approval and receipt, captures the g2 child, and has empty
validation and held-out allocations.
