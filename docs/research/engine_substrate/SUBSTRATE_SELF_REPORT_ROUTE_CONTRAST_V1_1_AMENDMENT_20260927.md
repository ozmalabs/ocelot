# Self-report route contrast panel v1.1 amendment: lock runtime references

Date: 2026-09-27

## Reason for amendment

The v1 isolated snapshot omitted `data/slabs`. This is a runtime input: `domains/wiktionary_reference.py` reads `data/slabs/wikt_pos_en.*` through `reference_slab`, and `domains/wordplay.py::_known` uses that lookup before labeling a token an OOV affix coinage. Direct comparison confirms the consequence for the target noun: in the workspace `wiktionary_has_en("organisation")` is true with POS `noun` and `detect_coinage` returns `None`; in the v1 snapshot the slab directory is absent, knownness is false, and the token is misclassified as a coinage.

Thus the v1 contrast panel and its follow-up coinage interventions do **not** establish route arbitration or current capability. Their source locks omitted a behaviorally relevant runtime reference asset. A subsequent audit also found that v1.1's compact snapshot omitted `scripts/collapse_engine.py`, required by the held action path; see [v1.2 amendment](SUBSTRATE_SELF_REPORT_ROUTE_CONTRAST_V1_2_AMENDMENT_20260927.md). Preserve v1 and v1.1 records as audit evidence about incomplete locking; do not use their wordplay or no-response outcomes as evidence about the fully provisioned substrate.

## Corrected protocol

The v1.1 confirmatory panel uses a frozen source snapshot with current `boot_all.py` and `boot_profiles.py` at capture, the same other source files and seeds as the snapshot base, and a copy of the full `data/slabs/` directory. The runner records a SHA-256 for every slab file at driver start/end and worker start/end, in addition to the existing source closure. It repeats the same ten utterances in 30 fresh processes, three per item. No production source or runtime data is modified.

Interpret results only for the exact corrected snapshot lock. The loaded reference slabs are treated as executable runtime dependencies, like code and seeds. Future source snapshots must include all external/reference inputs actually read by their evaluation path.
