# Anaphora join-order replay v1.1 current-source replication

This replication reuses the frozen v1 design and oracle unchanged: the same two-turn anaphora input, minimal recursive `intent` seed closure, all 24 match-clause permutations, two fresh workers per permutation, native per-rule/per-clause counters, fixed-point terminal probe, task output, and exact canonical graph parity. It tests the current source snapshot after a post-v1 change to `substrate/world_adapter.py`. It is a source-version replication, not an amendment to task selection or metrics.

The v1 protocol and v1.1 oracle amendment remain part of the locked inputs. Preserve v1 artifacts unchanged and report v1.1 separately. No timing superiority claim is permitted; the primary endpoint remains native candidate-test count.
