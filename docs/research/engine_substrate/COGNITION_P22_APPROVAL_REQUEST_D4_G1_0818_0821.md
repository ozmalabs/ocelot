# P22 candidate-specific simulated-adoption request: D4 g1 continuation

**Status: awaiting exact user approval.** Candidate `#9458` has digest
`84854777d0e3b48f447ecd04236a794eff39a46546edb3f19e47f506492ce66a` and is
qualified as `#15851` (`independent_goal_composition`). The selected witnesses
are training worlds 0960 and 0818. The verified source transition on fresh
world 0818 derives child candidate `#12174`; both candidate and child effects
are absent from the registered invention-only g1 parent's active effects.

This packet requests exactly one training-simulator transition on D4 training
draw 0818, with a conditional generation-two checkpoint if the native receipt
verifies. If approving, provide the exact candidate digest and reviewer-
reported review seconds. The previously supplied 12-second review duration is
used in the regression fixture only; this request remains unapproved. Approval
would authorize no later action.

The parent is the verified generation-one checkpoint
`p22-d4-g1-2d2cb9ecda29` (digest
`6fabe1c4d1bdaaafa5015c0ac3e4d43cc5759c380445be0df60420d8ac6550c8`). The
source artifact `p22_training_panel_registered_root_d4_g1_0818_0821_ticks60_depth3.json`
has SHA-256 `406d2015fbc8ecf1b74b3349b66618339448add8603adb11c42dac093eaa7798`;
the exact replay
`p22_training_panel_registered_root_d4_g1_0818_0821_ticks60_depth3_replay.json`
has SHA-256 `750b46cc6c2e13ffc8ab36af03c17690408a8814c2eb1ed4e7e651f9259fb8f1`.
Both reproduce the digest and qualification, retain the inherited single
approval/receipt, and have empty validation allocations. No new action has
been executed; no held-out world was accessed.
