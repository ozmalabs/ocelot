# Orientation scope pilot v1.1 amendment

Date: 2026-09-25. V1's raw output is preserved. It yielded zero tuning in every arm and therefore did not validate orientation-task quality.

## Instrument diagnosis
On the same single-sheet fixture and grating input, the normal `tick` call returned zero progress. Applying native `run_rules_report(200000, detect_cycles=True)` to that unchanged graph then made 111 progress applications over 102 passes, reported `repeated_graph_state`, and produced positive SUnit act/rate in all nine units. This is evidence that the direct host input writes used by the grating presenter were not waking the required rules in the default tick schedule. The standard presenter calls `tick` and therefore is not a valid readout under this observed path.

## Corrected pilot
Keep the registered seeds, geometry, frozen weights, 12 orientations, four phases, and OSI criteria. For each stimulus, duplicate the established presenter writes exactly but call native `run_rules_report(200000, detect_cycles=True)` so full graph closure evaluates the input; record every termination status and progress. Before the tuning sweep, compare default tick and full-rescan closure on one identical 0-degree frame, recording tick progress, full-rescan report, and max act/rate. No result from v1 is relabelled. If full-rescan outputs remain silent or hit unclassified failure, task-quality comparison fails.
