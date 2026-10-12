# Thoughtexperiment persistent adoption v1 results

The source-locked panel exercised four workers each for recurrence and
conversation. Each selected repair was installed once, then evaluated on two
sequential batches in the same substrate. All 16 batch outcomes passed. Median
selected-rule activation was 0.189 ms.

A separate controlled rollback panel used the known-bad agent-wide recurrence
guard. All four workers observed the expected recurrence failure, replaced the
successor with the captured source rule under the current revision, and
recovered the task outcome. Median rollback took 0.164 ms. The independent
analyzer passed 5/5 checks, including stable source/build hashes.

This measures persistence across two authored batches and demonstrates a
mechanical rollback path after an observed regression. The task, fault,
candidate family, and failure decision are supplied by the harness; rollback
uses an explicit observed-failure condition. This does not establish autonomous
regression detection, a calibrated adoption threshold, long-run utility, broad
task transfer, or self-improvement. See the
[preregistration](THOUGHTEXPERIMENT_PERSISTENT_ADOPTION_V1_PREREG_20261003.md),
[runner](../../../evaluation/substrate_capability/thoughtexperiment_persistent_adoption_v1.py),
[source lock](../../../evaluation/substrate_capability/thoughtexperiment_persistent_adoption_v1_lock_20261003.json),
[capture](../../../evaluation/reports/thoughtexperiment_persistent_adoption_v1_20261003.json),
and [analysis](../../../evaluation/reports/thoughtexperiment_persistent_adoption_v1_analysis_20261003.json).
