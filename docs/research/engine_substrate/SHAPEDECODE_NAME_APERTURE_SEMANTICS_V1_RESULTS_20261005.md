# ShapeDecode name-aperture semantic controls v1 — results

The paired scan/cache panel passed all 12 checks across 14 fresh processes (seven controls × two cache modes). Every paired Term result was equal, each worker used the locked source manifest, and there were no process failures.

| Control | Scan result | Meaning observed |
|---|---:|---|
| Unique names | 36 | Baseline full-match score |
| Case-varied name | 36 | Folded-name lookup still selects the target |
| Exact duplicate, later signature | 12 | Both matching candidate apertures see the later same-name value |
| Case-fold-equivalent duplicate | 36 | The aperture includes both case variants; full target signature remains selectable |
| Declared scope evaluates to `None` | 36 | Behaves as unrestricted lookup |
| Explicit empty scope | `None` | No usable held part is returned |
| Reversed two-name scope | `['r00']` | Selection preserves codebook insertion order despite reversed requested-name order |

The cache arm returned the same value in every row. These cases support selection and scoring parity for the exercised name semantics. The order case specifically verifies that the selected best part is unchanged when the requested names are reversed; it does not establish ordering for every multi-part plan or every tie pattern.

## Limits and next controls

This panel uses one authored ShapeDecode fixture and a native `MaxOver` query. It does not exercise `Surface(Text)` name/signature attributes, malformed records outside the requested aperture, `exclude`, graph mutation during an EvalCtx, or natural-task data. Those remain required before broader semantic promotion. The panel does not measure timing or establish natural-task prevalence.

The empty-scope native result is Python `None`; the initial analyzer expected a rendered wall string and was corrected in protocol amendment v1.1. Scan and cache agreed before and after that analyzer correction.

## Artifacts

- [Preregistration and amendment](SHAPEDECODE_NAME_APERTURE_SEMANTICS_V1_PREREG_20261005.md)
- [Runner](../../../evaluation/substrate_capability/shapedecode_name_aperture_semantics_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_shapedecode_name_aperture_semantics_v1.py)
- [Raw capture](../../../evaluation/reports/shapedecode_name_aperture_semantics_v1_20261005.json)
- [Analysis](../../../evaluation/reports/shapedecode_name_aperture_semantics_v1_analysis_20261005.json)
- [Source lock](../../../evaluation/substrate_capability/shapedecode_name_aperture_semantics_v1_lock_20261005.json)
