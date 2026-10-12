# Phase-0 vision-eye WUnit scaling v1 results — 2026-10-04

All five source, parity, progress, and Argmax gates pass across 12 size/replicate cells. The timed arm disables scale auditing; a separately rebuilt audited twin matches its final graph digest and eight-step progress vector in every cell.

| WUnits | Median closure time | Median time for 8 closures | Median candidates | Median Term evaluations | Graph nodes / edges |
|---:|---:|---:|---:|---:|---:|
| 4 | 8.85 ms | 69.2 ms | 82,176 | 974,748 | 2,031 / 4,008 |
| 16 | 19.8 ms | 163.8 ms | 279,552 | 3,179,104 | 5,115 / 10,164 |
| 64 | 90.9 ms | 742.6 ms | 1,069,056 | 11,996,128 | 17,451 / 34,788 |
| 256 | 370.9 ms | 3.017 s | 4,227,072 | 47,264,224 | 66,795 / 133,284 |

From 4 to 256 WUnits, population size grows 64×, median closure time grows 41.9×, candidate work 51.4×, and Term work 48.5×. Every case reaches the source-authored Argmax rule and has one Argmax cache entry at the terminal boundary. This supports near-linear scaling over this bounded graph family on the measured host; it does not establish an asymptotic class.

The profile is for one authored phase-0 vision family, one fixed 5×5 input patch, fixed 16×16 retina, deterministic all-to-all WUnit wiring, and eight clock steps. Three replicates per size and one host do not estimate natural inputs, unrelated graph topology, broader rule families, cache speedup, or scaling beyond 256 WUnits. Construction and fact input are outside timed closures. Evidence: [protocol](SUBSTRATE_VISION_EYE_WUNIT_SCALE_V1_PREREG_20261004.md), [runner](../../../evaluation/substrate_capability/vision_eye_wunit_scale_v1.py), [source lock](../../../evaluation/substrate_capability/vision_eye_wunit_scale_v1_lock_20261004.json), and [capture](../../../evaluation/reports/vision_eye_wunit_scale_v1_20261004.json).
