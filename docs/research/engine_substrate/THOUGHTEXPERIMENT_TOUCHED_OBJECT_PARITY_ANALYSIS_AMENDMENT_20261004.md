# Touched-object parity analysis amendment — 2026-10-04

The preregistered v1.1 analyzer found that its hard-coded one-changed-node
assumption was false in some retained workers. Raw captures show one or two
changed nodes, and the preregistered protocol requires journal-touched-node
shape and exact full-state reconstruction but does not fix the count at one.
The initial analyzer report is retained with its two failing checks.

The amended analyzer
`analyze_thoughtexperiment_touched_object_parity_v1_1_1.py` compares the
measured touched-node count directly with each worker's selected residual,
requires one or two changed nodes, and retains the node-only/no-edge-change
gate. It reruns all 19 checks over the unchanged capture; all pass. The
amendment changes no worker, schedule, capture, or metric definition. Its
executable SHA-256 is recorded in the corrected analysis artifact.
