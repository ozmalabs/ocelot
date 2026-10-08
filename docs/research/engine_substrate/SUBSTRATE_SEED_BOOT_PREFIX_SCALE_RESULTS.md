# Full seed-loader nested prefix scale results

Date: 2026-09-25  
Status: 16 fresh processes; exact state parity at every size

## Results

Four nested prefixes of canonical topological seed order were booted twice cold and twice warm. “Size” is indexed seed IDs, not raw JSON files: the frozen 833-file corpus yields 737 bulk-indexed IDs. The 737-ID point includes all 833 files, including 95 `self_load_only` files and one non-dict file that the bulk index excludes. Smaller prefixes contain only the canonical selected path for each indexed ID.

| Indexed seed IDs | Physical files | Nodes | Edges | Active rules | RuleSummary nodes | ProgramSummary nodes | Cold wall, median | Warm wall, median | Peak RSS, observed |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 128 | 128 | 3,725 | 2,898 | 390 | 390 | 0 | 1.29 s | 1.21 s | 584,560 KiB (~571 MiB) |
| 256 | 256 | 6,264 | 4,665 | 615 | 646 | 1 | 1.86 s | 1.55 s | 584,560 KiB (~571 MiB) |
| 512 | 512 | 20,757 | 8,865 | 1,806 | 1,837 | 14 | 26.78 s | 22.70 s | 1,639,372–1,639,760 KiB (~1.56 GiB) |
| 737 | 833 | 24,784 | 11,090 | 2,289 | 2,331 | 25 | 20.84 s | 14.83 s | 1,747,356–1,749,164 KiB (~1.67 GiB) |

Each wall median is based on two points: cold/warm times were 1.270/1.384 and 1.310/1.028 s at N=128; 1.789/1.571 and 1.931/1.528 s at N=256; 26.835/22.350 and 26.730/23.051 s at N=512; 24.257/14.792 and 17.424/14.877 s at N=737. All four processes at each size matched complete graph, grammar, rule/access, rule-order, and load-report fingerprints. All 16 PIDs were distinct. The full corpus consistently reports the same 11 load failures; the smaller prefixes report only the failures present within each prefix.

## Interpretation

This is not a smooth size curve. Moving from 256 to 512 IDs coincides with a jump from 615 to 1,806 active rules and from 6,264 to 20,757 graph nodes; boot rises by over an order of magnitude and peak RSS by about 1 GiB. The 737-ID point is larger yet faster in this run, so wall-time monotonicity is not established. Seed-family composition, process/host variation, the per-boot self-model mirror, and native installation are candidate contributors; this run does not isolate them. The high-water RSS is a process-level Linux `ru_maxrss` value, including Python/native imports, not incremental heap allocation.

The result changes the scale question: node and manifest counts alone are inadequate predictors. The independent source census finds that canonical IDs 257–512 contain 258,992,525 manifest bytes, versus 2,155,115 bytes in IDs 129–256 and 15,174,889 bytes in IDs 513–737. That band includes `grounded_lexicon.json` (110,731,329 bytes, with a nested 2,501-node `graph`), `embodied_motor_program.json` (70,470,063 bytes), and `humanoid_adaptation.json` (31,108,153 bytes). Source inspection confirms `PySubstrate::load_seed_manifest` first converts the entire Python object through generic `pyobj_to_json`; the Rust loader then reads top-level nodes, edges, productions, rules, reflexes, and selected metadata. The nested graph is not among those fields. This makes payload decoding/serialization a concrete candidate contributor to the discontinuity, not an established cause: Python-side code retains and consults original manifest fields, and this census does not demonstrate that dropping nested data preserves all consumers. Track active rule count, graph-resident rules, summary population, and manifest feature composition. Next compare current loading with a controlled, explicitly safe native-boundary projection while retaining the full Python manifest, require complete boot/self-model/capability parity, and repeat upper scale points under controlled host load. No asymptotic or commodity-scale claim follows from this single-host four-point ladder.

## Artifacts

- Protocol: [`preregistration`](SUBSTRATE_SEED_BOOT_PREFIX_SCALE_PREREG_20260925.md)
- Source/corpus lock: [`lock JSON`](../../../evaluation/substrate_capability/seed_boot_prefix_scale_lock_20260925.json)
- Runner: [`prefix scale probe`](../../../scripts/substrate_seed_boot_prefix_scale_v1.py)
- Raw records: [`16-worker report`](../../../evaluation/reports/substrate_seed_boot_prefix_scale_v1_20260925.json)
- Independent analysis: [`validated summary`](../../../evaluation/reports/substrate_seed_boot_prefix_scale_v1_analysis_20260925.json), [`analyzer`](../../../scripts/analyze_substrate_seed_boot_prefix_scale_v1.py)
- Related loader profile: [`boot stage profile`](SUBSTRATE_SEED_BOOT_PROFILE_RESULTS.md)
