# P22 v2 native proposal development probes

**Digest transcription correction (2026-10-23):** The D4 qualified candidate
digest in the original prose table was transcribed incorrectly. It is corrected
below from the archived raw record; the raw JSON itself is unchanged.

**Purpose:** Verify that generic P19 search can generate and independently qualify proposals from varied v2 training tasks, then score every unapproved proposal on a common answer-free validation panel. This is a development diagnostic, not a matched-arm efficacy evaluation.

The runner used two distinct training world IDs with the same generated goal in each family. At least one proposal per family qualified through native verified attempts; other proposals remain explicitly awaiting qualification because the bounded requests had already been terminalized. It evaluated all graph-minted candidates; it did not select a winner. Every candidate remained `unapproved_candidate`. Both runs recorded zero adoption approvals and zero world receipts. The validation scorer was read-only and did not create action records.

| Family | Training worlds | Proposal expression digests | Qualified trials | Validation outcomes |
|---|---|---|---:|---:|
| D4 v2 | `p22:d4-v2:train:0001`, `p22:d4-v2:train:0007` | `8a737c4d9d27d7e97233ddbc57921fb661e088a65fecce23eea884b7a8753788` (qualified); `1042425ae99735840687a3d4b90499e6bd2f5aaf3902f420575ef7d9a832ad71` (awaiting) | 1; 0 | Both proposals solved 16/200 validation worlds (8%). Their per-proposal panel digests are `474e34e428759918738f2b9c585a8b70ce441cbb51bb00ebb7df27216ccc74e2` and `b5dd29925d2bd401318cd9356adaad89229a5d6925ef9f98966b1832bf7d5634`. |
| Loopover v2 | `p22:loopover-v2:train:0001`, `p22:loopover-v2:train:0003` | `4df6b75c23c6dec5e67c45d09e3e2d31ad416fd9202c6b44fd9c0783dfff5711` (qualified); `3c88ebd91e1dcd440418662c9d4858264a745a9f3ac27b0221229e9179a04323` (awaiting) | 1; 0 | Both proposals solved 0/200 validation worlds. Their per-proposal panel digests are `2ec114c0de196bf863158be988476388d8842693dd13d57054851f035a3f51da` and `efde8e788e4afaea3142fba81029e882316b048c82fde141bee24161eafd12aa`. |

These rates are raw proposal success frequencies only. No paired unchanged-ancestor portfolio, adaptive-only learner, invention-only learner, or full learner was run on this panel, so the frequencies do not estimate an improvement effect. The Loopover result is a concrete negative transfer signal for these proposals. D4 results show limited direct coverage, not capability closure. No candidate was approved, adopted, or executed.

The development audit and probe have accessed v2 validation draws `0000`–`0199`; the preregistered validation allocation must use a fresh disjoint draw range. The sealed held-out split remains untouched.

The first proposal in each family qualified on the two distinct training world identities. The second proposal remains awaiting qualification because those bounded search requests had already been terminalized by qualification evidence for the first expression. Both remain unapproved. No candidate or trial was dropped from the report.

Raw outputs are [`p22_v2_candidate_probe_d4.json`](../../../evaluation/process_mastery/results/p22_v2_candidate_probe_d4.json), SHA-256 `cea6d8993d596da8dcbb694dc255573d7577371c758faa24abddd1bafb9a01b2`, and [`p22_v2_candidate_probe_loopover.json`](../../../evaluation/process_mastery/results/p22_v2_candidate_probe_loopover.json), SHA-256 `254d55b7c865318d7d8a6916ecfdea4a9f8d0a76323243d456d80e65dcc3f5e5`.

Reproduce with:

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python scripts/run_p22_development_probe.py \
  --family d4 --training-draws 1 7 --validation-start 0 --validation-count 200 \
  --output evaluation/process_mastery/results/p22_v2_candidate_probe_d4.json
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python scripts/run_p22_development_probe.py \
  --family loopover --training-draws 1 3 --validation-start 0 --validation-count 200 \
  --output evaluation/process_mastery/results/p22_v2_candidate_probe_loopover.json
```
