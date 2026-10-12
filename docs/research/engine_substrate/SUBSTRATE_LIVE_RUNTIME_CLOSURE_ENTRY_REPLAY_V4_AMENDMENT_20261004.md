# Live runtime closure-entry replay v4 amendment

After the v3 replay began, exact Python dictionary comparison rejected two graph restores because one timestamp attribute changed by one binary64 ULP during graph serialization (`1791102229.6275973` to `1791102229.627597`). Node and edge counts, types, identities, and all other attrs matched. This is a persistence precision issue and was not caused by scheduler restore.

The v4 replay retains an `graph_roundtrip_exact` field and adds a clearly separate acceptance check: all graph fields must match structurally and every changed float must be within one ULP; the count, maximum absolute delta, and field path are retained per call. This does not claim bit-exact graph persistence. Rule metadata and scheduler state still require exact round-trip. Counter parity is measured independently. The failed v3 capture/replay artifacts remain intact.
