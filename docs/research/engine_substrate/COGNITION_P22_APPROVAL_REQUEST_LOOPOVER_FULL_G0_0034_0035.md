# P22 Loopover full-arm generation-zero continuation approval request

Status: **awaiting exact user approval**. This packet requests one
candidate-specific transition from the registered full-arm Loopover generation-zero
checkpoint. It does not authorize any later transition.

## Candidate and transfer evidence

Candidate `#1611` has expression digest
`c9f470ba163917fc8061b27fe6a0fc93e1626d6bb435718aa5f3a120403ffc29`, effect
`[[0,1,2,5,3,4,7,8,6]]`, and parameters `[0,1,2,4,5,3,8,6,7]`. It qualified
as `#41560` under `independent_goal_composition` on distinct training worlds
`p22:loopover-v2:train:0034` and `p22:loopover-v2:train:0035`.

The selected transfer on draw 0035 derived child `#16963`, digest
`e5604deb448518c2a11190497120513c1266a8a64081096511385b77aac31aaf`, parameters
`[1,2,3,0,5,7,4,6,8]`, effect `[[3,0,1,2,6,4,7,5,8]]`. Both source and child
effects are non-identity and differ from all twelve active processes in the
registered parent; that parent has no approved-adopted candidates.

Exact replay reproduced candidate `#1611`, qualification `#41560`, the same
witness pair, and child `#16963` with the same digest and effect. Source artifact
SHA-256 `f3b5bafad8bf9e9046500494e79c77effc1039e265812b14a6fe656c5bdda6c8`;
replay SHA-256 `8560eb7903e13fc75150b64da70bfb6356bc5f9cea7dc9341a38ab439446c01a`.
The source reserved 40,000 attempts, recorded 70 native rule steps, 1,219.864
seconds wall-time, and 937,930,752-byte peak RSS. Native-rule identity coverage
is complete with no unresolved rules. Validation and held-out allocations are
empty.

## Requested transition

If approved, the runner will record reviewer-reported review time, execute exactly
one simulated transition using candidate `#1611` on fresh training world
`p22:loopover-v2:train:0034`, verify its receipt, and conditionally capture a
generation-one checkpoint descended from `p22-loopover-full-g0` (digest
`d6d3c24fa68c512767e43d45c79985597d659cd28f726b04786100fa25f52f8c`). No
validation or held-out world will be used.

The parent checkpoint record, source and replay hashes, exact qualification
witnesses, candidate expression binding, and output path are bound in the
accompanying JSON request. The output path is currently unused.

To authorize exactly this transition, reply:

`approve c9f470ba163917fc8061b27fe6a0fc93e1626d6bb435718aa5f3a120403ffc29; review_seconds=12`
