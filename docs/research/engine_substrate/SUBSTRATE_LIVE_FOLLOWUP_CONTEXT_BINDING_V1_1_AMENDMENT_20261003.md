# Live follow-up context binding v1.1 amendment

Date: 2026-10-03  
Status: post-capture replicate comparison; v1 raw capture and failed raw-digest analysis are preserved.

The v1 raw graph digest gate fails in the known-answer and unknown-fact two-turn conditions. Pairwise inspection shows identical graph-array ordering and directed typed topology across all three workers in each condition. The only differing fields are generated `SystemModel.attrs.runtime_s` and `ts`; the three fresh-control graphs match exactly. The independent v1.1 analyzer retains all raw digests and additionally compares semantic digests after remapping IDs to graph-array positions and excluding only those two fields on `SystemModel` nodes. All other node fields/attrs/order and every directed typed edge remain compared. This amendment does not change capture or retroactively pass the raw digest gate.

Analyzer: [v1.1 analysis code](../../../evaluation/substrate_capability/analyze_live_followup_context_binding_v1_1.py). Raw capture: [gzip JSONL](../../../evaluation/reports/live_followup_context_binding_v1_20261003.jsonl.gz).
