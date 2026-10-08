# Fully bound edge matcher differential v2 failure amendment

The preregistered v2 panel exposed a repeat-variable error during incremental matching. At the first closure, all four rule shapes match the oracle. After new relation edges are added, the semi-naive driver incorrectly seeds repeated-variable clauses from non-self edges using only the source endpoint. The independent analyzer confirms false self-loop witnesses in the final phase; its overall result is correctly failed. The raw failed capture and analysis are retained.

Source inspection confirms both incremental seeding paths (`try_incremental_match` and predicate retraction) reject equal endpoints only for distinct variables but do not reject unequal endpoints when both edge endpoints name the same variable. The targeted correction must require endpoint equality exactly when the two pattern endpoints use the same variable. After correcting both sites, repeat the four-shape gate under a new engine build, lock, and fresh seed set. No outcome or claim from this failed capture is promoted as a passing semantic result.

