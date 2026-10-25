# P22 D4 full-arm generation-one continuation approval request

Status: **approved and consumed**. This packet requested one candidate-specific
training transition from the registered full-arm D4 generation-one checkpoint.
It does not authorize any later transition.

## Candidate and transfer evidence

Candidate `#9440` has expression digest
`2d2cb9ecda29351e1d0f513498eb6089c0f48b2dc1f8ee8650ebb2bbf39cdc46`, effect
`[[1,0,3,2]]`, and parameters `[1,0,3,2]`. It qualified as `#32385` under
`independent_goal_composition` using distinct training goals `p22:d4-v2:train:0988`
and `p22:d4-v2:train:0003`. The selected training transfer on draw 0003 produced
child `#22382`, digest
`98f1d1a497d5032cf86f405b43cfa96908eecd05ead5fe17d02f1f4867d57e1f`, parameters
`[3,1,2,0]`, and effect `[[3,1,2,0]]`. Both source and child effects are
non-identity and absent from the parent’s active effects under the native
qualification guard.

A separate exact training-only replay reproduced candidate `#9440`, qualification
`#32385`, the same witness pair, and child `#22382` with the same digest and
parameters. Source artifact SHA-256:
`b30b06795498887643b1c325372cf2e90086e0fbb654455ba7d24f0286334792`; replay
SHA-256 `6a73de04a148a0f4b6c319342b043dd70f3caeadf5f46523a4137c0f90b21594`.
The source reserved 30,811 attempts, measured 170 native rule steps, 619.116
seconds wall time, and 937,930,752-byte peak RSS. Native-rule identity coverage is
complete with no unresolved rules. Validation and held-out allocations are empty.

## Resource feasibility

The source snapshot reports 276,603 cumulative primitive work at candidate
qualification. This is below the current 600,000 development ceiling and the
1,000,000 implementation maximum. The output remains unused; the resulting
checkpoint must retain its measured work and pass the shared-ceiling preflight
before it can enter the final manifest.

## Requested transition

If approved, the runner will record reviewer-reported review time, execute exactly
one simulated transition using candidate `#9440` on fresh training world
`p22:d4-v2:train:0002`, verify the resulting receipt, and conditionally capture a
generation-two checkpoint descended from parent `p22-d4-g1-15ab127dc160` (digest
`e83c1fb3b84f589b8ca400b4b39fa03d8c04528aba262adc3b53a4c1eeca9af9`). No
validation or held-out world will be used.

The parent artifact, immutable checkpoint record path, source and replay hashes,
qualification witness pair, candidate expression binding, and output path are
bound in the accompanying JSON request. The output path is currently unused.

Original one-shot approval token (now consumed):

`approve 2d2cb9ecda29351e1d0f513498eb6089c0f48b2dc1f8ee8650ebb2bbf39cdc46; review_seconds=12`

## Consumption record

The exact digest was approved with 12 reviewer-reported seconds. The guarded
runner consumed approval `#32278`, executed exactly one transition on training
world `p22:d4-v2:train:0002`, verified receipt `#32282`, and captured child
checkpoint `p22-d4-g2-2d2cb9ecda29` (generation 2; digest
`2078f32af3e8951d14b7705b38a7f2bfa5074420f3eb105fc9183b6a03919123`) from
parent digest `e83c1fb3b84f589b8ca400b4b39fa03d8c04528aba262adc3b53a4c1eeca9af9`.
The result is `evaluation/process_mastery/results/p22_approved_candidate_d4_full_g1_0002_0003.json`,
SHA-256 `0bfd5df9c522276da17d2fc162fccf7dfb07f222b7152f61e351144ba1b8d39b`.
It contains no validation or held-out worlds. This training transition does not
authorize another action or establish efficacy.
