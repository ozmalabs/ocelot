# V1.5 amendment: matched timer boundary

The V1.4 six-cell run passed semantic checks, but its treatment timer accidentally included scale-audit snapshot extraction and per-rule name decoding. The baseline timer stops when `observe()` returns and reads instrumentation afterward. The apparent 2× treatment time from that run is therefore instrumentation-readback contamination and is withdrawn as a cost comparison.

This amendment moves the treatment timer stop to immediately after closure and receipt creation, then reads counters outside the timed interval, matching the baseline harness boundary. No task, rule, seed, or semantic check changes. The full six-cell timing comparison is rerun. The contaminated run remains preserved separately for audit.
