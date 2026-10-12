# SynthEnumerate nonlinear-map v1.1 reporting amendment

The v1 raw capture and analysis are preserved as diagnostic evidence. Its 40 acquisition cells completed and semantic/source integrity checks passed, but the analyzer labeled application batch nanoseconds-per-call as milliseconds-per-call without dividing by 1,000,000. The stored batch wall times and call counts are intact; the error affects only the displayed units and any interpretation derived from those labels.

V1.1 corrects the application-cost conversion and reports microseconds per native evaluator call. It repeats the same 40 locked task/grammar/repetition cells in fresh substrates under a new source/native lock. No task points, formula, grammar, constant pool, size/candidate budget, schedule, scoring rule, or gate changes. V1 records are not pooled with v1.1.

The v1.1 admission gate requires the same nine checks as v1, plus an exact conversion check: every reported per-call microsecond statistic must equal the raw `wall_ns / calls / 1000` calculation for its underlying reuse samples. The only result comparison between versions is a descriptive cellwise semantic parity check.
