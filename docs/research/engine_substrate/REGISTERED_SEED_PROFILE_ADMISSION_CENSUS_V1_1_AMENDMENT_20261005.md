# Registered seed-root admission census v1.1 amendment

V1 captured all 117 registered IDs, including one missing root manifest and four roots with an unresolved `core.json` dependency. Its independent analyzer failed because it compared the checker's vacuous acceptance of an empty rule list with the candidate-profile definition, which correctly requires a nonempty profile. V1 raw capture and lock are preserved.

V1.1 changes no population, checker, inputs, or profile collection. It fixes the independent analyzer to treat empty profiles as non-candidates while separately validating their explicit empty status, then takes a fresh source lock and repeats the census. Bootable profile decisions and missing-manifest outcomes continue to be independently audited.
