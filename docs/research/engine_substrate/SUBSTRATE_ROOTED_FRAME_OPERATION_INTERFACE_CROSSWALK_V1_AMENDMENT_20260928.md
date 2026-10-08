# Rooted-frame operation-interface crosswalk v1 amendment

Date: 2026-09-28

## Analyzer input-schema correction

The first offline analysis attempt expected the rooted-panel analysis JSON to expose a top-level `all_checks_pass` field. That artifact instead records each gate in a `checks` object. The attempt consequently marked the input gate false even though every listed rooted-panel check was true; all graph joins, BFS reconstructions, and cut recomputations also passed. The analyzer now requires a nonempty `checks` object with every value true. No source capture, task input, frame proposal, metric definition, or result data changed. The accepted analysis records the corrected analyzer's SHA-256 and reruns all checks.
