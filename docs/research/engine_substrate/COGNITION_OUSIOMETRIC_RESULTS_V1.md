# P28 representation-value results v1

Status: **VALID STRUCTURAL RUN; PRIMARY BENEFIT CRITERION FAILS.** This is the
single run authorized by [the standalone P28.13 preregistration](COGNITION_OUSIOMETRIC_PREREG_V1.md).
It supports no representation promotion, semantic calibration, or general
competence claim.

## Frozen allocation and provenance

The runner completed 2,400 arm-by-seed rows: 200 paired seeds in each of
`tool_intervention` and `social_request_repair`, six arms per seed, and four
fixed evidence horizons (0, 1, 2, 4). Each checkpoint used its registered
changed-map target calibration and fresh scoring context. Coverage is complete;
all target calibrations were verified, all failures and abstentions remain in
the data, and no row used held-out evidence for selection.

The preregistration SHA-256 is
`5144e993bbc471c9ac94c0de27b363de3e9c4eb0f82ccc5a0d9e0e4afccc2e76`. Raw
bytes remain at `/tmp/p28_ousiometric_raw_v1.json`, SHA-256
`5c49305198670cc5cfc83790060fff7236635ea386d7fbbfff7ee1e51b0c07ef`.
The one analyzer output is `/tmp/p28_ousiometric_analysis_v1.json`, SHA-256
`d640da5ccd2f86cad4d3dfc307c79807ab79c22b78588a2c75400f01fdb0947f`.
The runner reported a loaded native runtime `ATTESTED`, matching build sources,
bound native symbols, no attestation issues, and the frozen extension/build
receipt digests. All preregistered source, split, transform, seed, and runtime
hash guards passed before the draw.

## Primary result

The sole contrast is `eq4_rotation_64bit_fixed_l1` versus
`shared_basis_64bit_fixed_l1`, labeled **published-rotation-bounded** because
no compatible feature-to-lexical calibration exists. The two arm outcome
curves were identical for every seed in each family. Both contrasts have mean
AUC difference 0.00000, paired 99% bootstrap interval [0, 0], one-sided
paired sign-flip p=1.00000, and Holm-adjusted p=1.00000. Both safety gates pass
their registered +0.02 increase limit, but the effect-size and lower-bound
gates fail, so the combined primary criterion fails.

| World family | Comparator AUC | Treatment AUC | Mean difference | 99% CI | Holm p | Score-outcome adverse rate (comparator / treatment) | Family gate |
|---|---:|---:|---:|---:|---:|---:|---|
| Tool intervention | 0.27625 | 0.27625 | 0.00000 | [0, 0] | 1.00000 | 0.21125 / 0.21125 | Fail |
| Social request repair | 0.04125 | 0.04125 | 0.00000 | [0, 0] | 1.00000 | 0.00375 / 0.00375 | Fail |

The family-specific scoring curves also show the task limits: across 800
checkpoint outcomes per arm, tool intervention had 177 successes (22.125%)
and 400 abstentions/unverified outcomes (50%); social repair had 33 successes
(4.125%) and 600 abstentions/unverified outcomes (75%). These are simulator
outcomes, not estimates of performance outside the registered worlds.

## All registered arms and costs

The following costs are per arm and family, averaged across 200 seeds. For
storage and bit fields, the values sum the four horizon checkpoint snapshots
within each seed; summed graph bytes are not a peak-memory estimate. The
reported elapsed time is the sum of checkpoint-local measurements per seed,
not total wall time for the serial run. Adverse rate here is the preregistered
scoring-checkpoint rate (800 rows per arm).

| Family | Arm | AUC | Success / checkpoint | Abstain / unverified | Score adverse | Native steps | Target actions | Graph bytes (sum) | Graph nodes (sum) | Seconds (sum) | Representation bits (sum) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Tool | `shared_basis_64bit_fixed_l1` | 0.27625 | 0.22125 | 0.500 | 0.21125 | 130.0 | 39.0 | 629591 | 3903.7 | 0.5453 | 5632 |
| Tool | `eq4_rotation_64bit_fixed_l1` | 0.27625 | 0.22125 | 0.500 | 0.21125 | 130.0 | 39.0 | 635573 | 3903.7 | 0.5469 | 5632 |
| Tool | `shared_basis_64bit_transported_l1` | 0.27625 | 0.22125 | 0.500 | 0.21125 | 130.0 | 39.0 | 631835 | 3903.7 | 0.5474 | 5632 |
| Tool | `eq4_rotation_64bit_transported_l1` | 0.27625 | 0.22125 | 0.500 | 0.21125 | 130.0 | 39.0 | 637816 | 3903.7 | 0.5474 | 5632 |
| Tool | `random_rotation_dev_64bit_fixed_l1` | 0.27625 | 0.22125 | 0.500 | 0.21125 | 130.0 | 39.0 | 641122 | 3903.7 | 0.5469 | 5632 |
| Tool | `eq4_rotation_8bit_fixed_l1` | 0.27625 | 0.22125 | 0.500 | 0.21125 | 130.0 | 39.0 | 636699 | 3903.7 | 0.5468 | 4960 |
| Social | `shared_basis_64bit_fixed_l1` | 0.04125 | 0.04125 | 0.750 | 0.00375 | 113.0 | 36.0 | 618105 | 3857.0 | 0.5551 | 5632 |
| Social | `eq4_rotation_64bit_fixed_l1` | 0.04125 | 0.04125 | 0.750 | 0.00375 | 113.0 | 36.0 | 621879 | 3857.0 | 0.5512 | 5632 |
| Social | `shared_basis_64bit_transported_l1` | 0.04125 | 0.04125 | 0.750 | 0.00375 | 113.0 | 36.0 | 620031 | 3857.0 | 0.5526 | 5632 |
| Social | `eq4_rotation_64bit_transported_l1` | 0.04125 | 0.04125 | 0.750 | 0.00375 | 113.0 | 36.0 | 623805 | 3857.0 | 0.5516 | 5632 |
| Social | `random_rotation_dev_64bit_fixed_l1` | 0.04125 | 0.04125 | 0.750 | 0.00375 | 113.0 | 36.0 | 628129 | 3857.0 | 0.5559 | 5632 |
| Social | `eq4_rotation_8bit_fixed_l1` | 0.04125 | 0.04125 | 0.750 | 0.00375 | 113.0 | 36.0 | 622761 | 3857.0 | 0.5555 | 4960 |

All arms had the same primary-family outcome curve per paired seed, the same
mean verification counts (13 per tool seed and 12 per social seed), and the
same mean evidence-event counts (13 and 12). As expected, the 8-bit control
used 96 coordinate bits per checkpoint (versus 192 for the 64-bit arms),
reducing the four-checkpoint representation-bit sum by 672. The measured graph
snapshot byte totals differ by arm, despite the equal declared coordinate and
mapping budgets; they are reported as resource costs, not as evidence of
benefit.

## Verified-action and risk exposure

For the two primary arms, source receipts were all verified and no source
receipt was adverse. Per arm, each family had 1,400 source-receipt
presentations and 800 verified target-calibration receipts. Those source
presentations repeat event IDs across the registered arms and horizon prefixes
and must not be counted as independent environmental support. Tool calibration
had 204 adverse receipts per arm (25.5% of calibration receipts); social
calibration had none. Among score checkpoints, the tool arms had 400 verified
score receipts, of which 169 were adverse, plus 400 abstentions. Social arms
had 200 verified score receipts, 3 adverse, plus 600 abstentions. Thus the
all-verified-action adverse rates including source, calibration, and scoring
receipts were 373/2,600 (14.346%) for each tool primary arm and 3/2,400
(0.125%) for each social primary arm. The treatment-comparator difference is
zero under both the preregistered scoring-checkpoint endpoint and this
descriptive all-receipt accounting. These are simulator exposure counts, not
real-world safety estimates.

Language context remained asserted/untrusted and did not modify physical
receipts or dynamics. The registered future-manifold residual control and
same-epoch native stop-veto controls passed before the freeze; no lexical rule
was used to select or authorize a scoring action.

## External lexical data and interpretation

Lexical status remains `UNSUPPORTED`. There is no frozen lexical checkpoint
or token-to-concept bridge, so GPADS/NRC target score columns were not opened
(`external_scores_opened=false`). The identifier-only split digest is
`0670f22600947a83d666708fe6a39c1886912ba0c83070f0106c83ca5595d726` with
15,361 train, 1,348 development, 941 anchor, and 2,320 held-out identifiers;
those identifiers do not create semantic calibration. The pinned GPADS v2
payload hash is `1825f9f23b796add681bd6dcd9753e8f1bf68cbf158c4af5e710bbc507b47e0a`;
NRC VAD v1 hash is
`fd49023f760155c8377424d96ca18d57c6685891d78ba381e47af6f4a1b148a7` and its
non-commercial, non-redistributable terms remain in force.

The result is a precise null for the declared synthetic-world comparison:
the rounded full-rank rotation, fixed/transported metric controls, random
rotation, and reduced-precision arm produced identical goal-learning curves.
The full-rank mathematical parity controls remain conformance evidence. This
panel provides no evidence that the PDS-labelled rotation adds useful basis
value in these environments, adds information, captures psychological axes,
or warrants changing the default representation. It also does not disprove
representation utility outside these registered worlds. P22's independent
lineage, resource, freeze, and held-out gates remain open.
