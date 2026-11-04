# Ousiometric external data and transformation manifest

Status: source inventory for Phase 28, captured 2026-10-25. The source files
remain outside the repository. In particular, NRC data must not be copied,
checked in, or redistributed. This manifest records measured byte hashes from
the sources listed below.

## Pinned sources

| Key | Exact source/version | Bytes and SHA-256 | License and allowed use |
|---|---|---|---|
| `gpads-v2` | [Zenodo record 18509376](https://zenodo.org/records/18509376), published 2026-02-06, file `ousiometry_GPADS.txt` | 1,124,404 bytes; `1825f9f23b796add681bd6dcd9753e8f1bf68cbf158c4af5e710bbc507b47e0a` | CC BY 4.0; attribution required. |
| `nrc-vad-v1` | [NRC VAD lexicon page](https://saifmohammad.com/WebPages/nrc-vad.html), v1 released 2018, archive file `NRC-VAD-Lexicon/NRC-VAD-Lexicon.txt` | archive SHA-256 `f956a7814823d22b34e67af451a33095f57635f11dae98728dee891a30a83aea`; payload SHA-256 `fd49023f760155c8377424d96ca18d57c6685891d78ba381e47af6f4a1b148a7` | NRC non-commercial research or educational use; citation required; no redistribution. The archive and payload were downloaded to `/tmp` for this audit and are not in the repository. |

The primary article is [Dodds et al., *Science Advances* (2026),
doi:10.1126/sciadv.adr4039](https://doi.org/10.1126/sciadv.adr4039); its open
manuscript is available [from the University of Adelaide repository](https://digital.library.adelaide.edu.au/server/api/core/bitstreams/47ebc745-5678-4864-b538-fa1a8c418720/content).
The paper says it uses the original NRC VAD lexicon of about 20,000 terms,
centers the three dimensions by 0.5, applies a full three-dimensional SVD, and
rotates the goodness/aggression plane by −π/4 for PDS. Eq. 4 prints a rounded
VAD→PDS coefficient matrix. The exact matrix printed by the article is not a
numerical exactness oracle; this investigation freezes those displayed values
as one explicit approximate full-rank mathematical transform and computes its
inverse for the geometry audit. That establishes invariance under that defined
matrix only. It does not reproduce the article's unrounded fitted coordinates.

The GPADS file contains columns, in order: `word`, `goodness`, `power`,
`aggression`, `danger`, `structure`. Its record metadata describes structure
as high = unstructured and low = structured. The five listed columns are
redundant projections of the source's three-dimensional construction; they do
not define five independent axes. The operational PDS view is `power`,
`danger`, `structure`, retaining the source sign convention.

The NRC v1 score file contains `English Word`, `Valence`, `Arousal`,
`Dominance`; scores are in [0,1]. The article's centered input convention is
`score - 0.5`. The v1 instrument is the version named by the paper. NRC v2.1
is a separate source/version and will not be silently substituted.

## Identifier and split audit

Split membership is created from lexical identifiers only, before any heldout
score fields are parsed. IDs are normalized by Unicode NFKC, casefolding, and
trimming. Related lexical identifiers are joined into conservative connected
families by shared WordNet 3.0 synsets from the repository's pinned sense
table (`domain_data/wordnet_senses.sqlite`, SHA-256
`ea734fdff4477157825d7f9bbd0fd93104650b9fc8ded3a873685986672acb5a`). A
cluster is assigned by a namespaced SHA-256 digest; all forms in the cluster
remain in the same split. The label-blind split rule is 50% train, 15%
development, 10% alignment anchors, and 25% heldout by first digest byte.
Concrete cluster membership and disjointness checks must be captured in the
standalone preregistration before the heldout panel opens. This deterministic
partition does not imply that WordNet covers every sense or language.

The identifier-only audit found 19,970 shared IDs between NRC VAD v1 and
GPADS v2, 36 GPADS IDs absent from the VAD v1 source, and one NRC VAD ID absent
from GPADS v2. Those counts were computed from first TSV columns only. This
version/coverage discrepancy is not evidence against mathematical
invertibility. It does prevent an unqualified claim that every GPADS row is
calibrated by the pinned NRC VAD v1 data. Missing concepts remain missing and
must be reported in lexical analysis.

## Verification record

`evaluation/ousiometrics/source_manifest.py` contains the pinned source
records, checksum verifier, transformation metadata, and ID-only cluster
split implementation. `tests/test_ousiometrics_sources.py` checks the license
record, structure sign, rounded-transform limit, ID-only split behavior, and
related-concept grouping. External score bytes are not installed into an agent
graph or seed.
