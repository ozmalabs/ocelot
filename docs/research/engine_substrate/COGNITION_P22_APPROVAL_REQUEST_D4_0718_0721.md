# P22 candidate-specific simulated-adoption request: D4 0718–0721

**Status: awaiting exact user approval. No action has been taken.**

This request covers exactly one guarded D4 training-simulator transition for
candidate `#16750`, followed by capture of its generation-three checkpoint
only if the native receipt verifies. It grants no validation or held-out
access, no later adoption, and no claim of efficacy.

| Binding | Value |
|---|---|
| Family / domain | D4 v2 / `p22-development` |
| Candidate / qualification | `#16750` / `#56758` |
| Expression digest | `75c8a4559ab843b8154bc031dab1f527d18f39595e9fc9f0c6f3c0b9d7a63b73` |
| Expression key | `compose:flip_r:p22-d4-generation-zero-identity` |
| Effect digest | `[[2,3,0,1]]` |
| Parameters | `[2,3,0,1]` |
| Guard state | `[0,1,2,3]` |
| Selected qualification witnesses | `p22:d4-v2:train:0718`, `p22:d4-v2:train:0719` |
| Other qualifying pairs | `0718/0720` (`#56759`) and `0718/0721` (`#56760`); not part of this request |
| Parent checkpoint | `p22-d4-g2-1e3590935d29`, generation 2 |
| Parent digest | `5799cb611c33a58de30c2590bbaa5f294794f0a9f9705707454072645bb694fc` |
| Transition | one D4 permutation action on training draw 0718 |
| Validation / held-out | none |

The effect is non-identity and maps `[0,1,2,3]` to `[2,3,0,1]`. Candidate
`#16750` qualified on three independent-goal pairs in the 0718–0721 training
panel. The selected pair is bound exactly; the other two pairs are not part of
this authorization. This simulator action and conditional checkpoint would
extend lineage only and would not demonstrate improvement.

To authorize exactly this transition and its conditional generation-three
checkpoint, reply with the digest and reviewer-reported time, for example:

`approve 75c8a4559ab843b8154bc031dab1f527d18f39595e9fc9f0c6f3c0b9d7a63b73; review_seconds=12`

The duration will be recorded as `reviewer_self_report`; it will not be
inferred.

## Reproducible execution binding

The machine request is
[`COGNITION_P22_APPROVAL_REQUEST_D4_0718_0721.json`](COGNITION_P22_APPROVAL_REQUEST_D4_0718_0721.json)
(SHA-256 `d0c4c0c689921f3398929757c13ede68dab5ef623d50b44f43f3a0a6ce7d92fb`).
The guarded CLI will restore and hash-check the generation-two checkpoint,
reconstruct the candidate and its bound depth-two qualification from the fresh
training draws, reserve the one-shot output path, and execute only after the
exact approval is supplied. The source artifact is
[`p22_training_panel_continuation_d4_0718_0721.json.gz`](../../../evaluation/process_mastery/results/p22_training_panel_continuation_d4_0718_0721.json.gz);
its decompressed raw SHA-256 is
`f3b1bf771b45e2d1c9d73eaa9efd667f8c0f7f670cbfbb82f1c4e6f94099d614`. The
output path is
`evaluation/process_mastery/results/p22_approved_candidate_d4_0718_0721.json`.

## Read-only request reconstruction check

Before requesting this approval, the exact generation-two parent and training
draws were replayed with no approval flags. The replay reconstructed
`#16750`, this expression digest, qualification `#56758` and witnesses 0718
and 0719. It added no approval or receipt and accessed no validation worlds.
The compressed replay is
[`p22_candidate_approval_replay_d4_0718_0721.json.gz`](../../../evaluation/process_mastery/results/p22_candidate_approval_replay_d4_0718_0721.json.gz),
SHA-256 `db3a6176f5e0e29ecb3eec8da184db62f38e40706a343fc86048f2ff25d57647`;
its decompressed raw SHA-256 is
`21738f213e8c269b8db67b0a797b0fea6d3eeda37f24ed3b828ad1e0c4f95746`.
