# Interacting tree closure scale v1 pilot amendment

Date: 2026-09-28, before the confirmatory source lock.

Three 10k setup workers were run to validate rule parsing, both topology builders, and the indexed terminal-state oracle: balanced/audit-on and star/audit-off plus star/audit-on. All reached fixed point with N active and zero pending/ready nodes. The balanced pilot took 14 passes and recorded 279,972 candidate tests; the star audit-on pilot took 2 passes and recorded 39,996 candidate tests. Both audit-on pilots performed exactly 2(N−1) attr-set attempts.

These pilots are exploratory setup checks. They are excluded from the 36 confirmatory worker count, all estimates, and audit pairing. The confirmatory schedule, topology definitions, gates, and sizes remain unchanged. The pilot disclosure and runner/analyzer are included in the source lock.
