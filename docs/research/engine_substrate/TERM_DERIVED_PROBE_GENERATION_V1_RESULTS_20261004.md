# Term-derived probe generation v1 — results

The locked study completed 120 cells: five source panels, two task relations,
three hidden thresholds, and four syntax encodings. The bound was available
only inside the candidate Term tree. The structural extractor recovered the
effective boundary for all 120 cells. The native selector selected a generated
boundary probe, one task-oracle label rejected the bounded candidate, and both
commuted exact Terms remained in every cell. The independent analyzer passed
source and panel binding, extracted-bound replay, probe membership, label,
survivor, and seeded wide-domain checks.

Across 61,440 relation-valid wide examples, the bounded candidates disagreed
with the task oracle 17,726 times; both exact Terms were correct on all these
examples. Each encoding used 270 candidate/probe evaluations and one label per
cell. Median selector latency ranged from 0.262 to 0.350 ms across encodings.
These values describe the bounded fixture and native selector only.

The result shows transfer across four hand-authored encodings of one affine
comparison fragment. It does not establish general Term interpretation: the
extractor explicitly recognizes a small set of operators, and the candidate
pool, variable, task relation, oracle, and held panel family are supplied.
Candidate invention and end-to-end correction adoption remain unmeasured.

Artifacts: [preregistration](TERM_DERIVED_PROBE_GENERATION_V1_PREREG_20261004.md), [runner](../../../evaluation/substrate_capability/term_derived_probe_generation_v1.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_term_derived_probe_generation_v1.py), [source lock](../../../evaluation/substrate_capability/term_derived_probe_generation_v1_lock_20261004.json), [capture](../../../evaluation/reports/term_derived_probe_generation_v1_20261004.json), and [analysis](../../../evaluation/reports/term_derived_probe_generation_v1_analysis_20261004.json).
