# Live frame-interface capture v1 results

Date: 2026-10-03  
Protocol: [frozen preregistration](SUBSTRATE_LIVE_FRAME_INTERFACE_CAPTURE_V1_PREREG_20261003.md)  
Runner: [capture worker](../../../scripts/substrate_live_frame_interface_capture_v1.py)  
Lock: [source lock](../../../evaluation/substrate_capability/live_frame_interface_capture_v1_lock_20261003.json)  
Raw capture archive: [three workers and full graph, gzip compressed](../../../evaluation/reports/substrate_live_frame_interface_capture_v1_workers_raw_20261003.json.gz)  
Independent audit: [analysis script](../../../scripts/analyze_live_frame_interface_capture_v1.py), [analysis output](../../../evaluation/reports/substrate_live_frame_interface_capture_v1_analysis_20261003.json)

## Result

All ten capture gates pass across three fresh worker processes. Start, finish,
and post-run source locks match. The semantic graph digest, graph summary,
declared task-boundary projection, prompt schedule, first-prompt lifecycle,
second-prompt route shortfall, and five identity/failure controls reproduce.
Every request reports zero dropped access and work trace rows. The retained
full graph has 25,065 nodes and 11,543 typed edges; the capture contains 274,887
access rows and 270 scheduler/work rows.

The non-owner-guided BFS proposal is structurally broad at even small radii.
At radii 0 through 3, the `report your organisation` neighborhood grows from
1 to 962 nodes, with 17 to 599 crossing edge incidences and 16 to 596 distinct
external nodes. It touches 0.36% to 8.17% of the request's weighted access
trace. For `describe who you are`, it grows from 1 to 969 nodes, with 16 to 605
crossings and 15 to 599 external nodes; trace coverage is 0.76% to 17.11%.
At radius 3, 3.84% of the graph's nodes are included for the first prompt and
3.87% for the second, while hundreds of external nodes remain adjacent. This
is not evidence of a low-boundary task cut. The BFS is only a generic proposal
baseline and often omits most traced access weight.

The preregistered runner did not serialize per-proposal observed attribute
summaries or independently recompute each typed cut. Since it retained the
full graph and each proposal's member IDs, the separate post-capture analyzer
reconstructed those summaries without using declared ownership. It verifies
all 24 proposal cuts against independent edge scans, checks member and
external-node resolution, and records observed attribute keys, value kinds,
and up to three value representations per key. This closes the auditability
gap for this capture while preserving the collection deviation in the record.

## Interpretation and next gate

The uncompressed JSON was 727 MB. It is retained losslessly as a 25.5 MB gzip
archive; decompression reproduces the capture summary's raw SHA-256
`dfe06d8862b68b67c07413a6c58d0976aea78739d9d8e88c51c701d8b65fcb0d`.

This result establishes current-source reproducibility and shows that simple
message-root BFS does not find a compact, trace-covering interface on this
authored prompt pair. The trace API is known to omit specialized graph scans
and some host-side work, so its coverage percentages are lower bounds on the
observable accesses in this capture, not completeness scores. Zero dropped
rows only proves the recorder did not hit its cap. The two-prompt fixture does
not estimate how often natural tasks admit cheap cuts.

Next, audit source-level factor scopes and trace omissions for these task
paths, then measure candidate cuts discovered without ownership hints against
the explicit operational task projection. Any proposed partition must be
checked for exact semantic parity against monolithic closure, including shared
state and adversarial cross-frame dependencies, with discovery, interface,
and scheduling costs included. Only after that gate should the programme run a
broader task sample for cheap-cut prevalence or claim frame-local execution
tractability.
