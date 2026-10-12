# Numeric opposition active query v1 implementation amendment

Date: 2026-10-03

Before the final source lock and scored capture, inspection of the independent
replay showed that an initial harness draft treated every numeric prediction
as a boolean. `select_discriminating_input` instead preserves exact output
types when partitioning hypotheses and when applying observations. The
initial capture failed the independent prediction-partition check and was not
used for results. The runner was changed to apply observations with exact
Python type and value equality, and the analyzer now independently checks
prediction partitions, query choice, stopping rules, source/build hashes, and
held-out scores. The training panel was also aligned to the preregistered
orthogonal-negative case. The final lock includes the corrected runner and
analyzer hashes plus all five training/query panels; only the final capture is
reported in the results document.
