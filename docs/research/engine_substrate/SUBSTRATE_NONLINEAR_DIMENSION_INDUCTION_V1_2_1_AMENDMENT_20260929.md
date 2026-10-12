# Nonlinear dimension induction v1.2.1 analyzer amendment

The v1.2 current-source capture is preserved as diagnostic evidence. Its 60-cell capture is complete, source/native pre/post hashes agree, and all task, schedule, linear-positive-control, nonlinear-shape, transfer, and frozen-arm checks pass. The v1.2 analyzer nevertheless reports `current_non_native_sources_match_lock=false` because it constructed a hard-coded hash map that omitted the preregistration hash stored in the lock. This is an analyzer false negative; no task outcome or capture field caused it.

The v1.2.1 analyzer compares the current hash map over every key present in the locked `source_sha256` object. The v1.2.1 runner, analyzer, and amendment are separately hashed and locked before a fresh repetition of the same 60-case design. No family, point set, arm, sample count, seed, schedule, outcome definition, or threshold changes. The v1.2 capture and failed analysis remain preserved and are not pooled with the corrected run.

Admission still requires all 12 v1.2 integrity/semantic gates. If any gate fails, report an inconclusive run rather than a loss or gain of capability.
