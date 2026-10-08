# Thoughtexperiment rehearsal memory outcome factorial v1 — preregistration

**Date:** 2026-10-01  
**Question:** Does peak RSS/PSS during actual correction rehearsal differ between a converging repair and a nonconverging candidate at 100k/200k graph sizes, and between scoped deep-copy and shared-graph-page branches?

## Design

Run the existing positive `dedup_identity_fix` and the existing first nonmatching default candidate from the same self-correction fixture at 100,000 and 200,000 unrelated linked graph nodes. Cross both candidate arms with `native_full_copy_scoped` and `native_shared_graph_pages_scoped`; use three fresh processes per size × candidate × backend cell, zero warmups, and a 10 ms `smaps_rollup` sampler during `imagine_and_check_convergence`. The corrected v1 task-input/rule preservation invariants apply; the ordinary durable trace appended to the primary is allowed.

Lock runner/helper/domain/native sources, build record, host, size ladder, candidate labels, backend set, and sample interval before running. Report baseline/peak/current deltas, exact candidate outcome, residual/output signatures, and input/rule preservation for every worker.

## Gates

- Eight factorial cells and 24 unique fresh processes complete under the locked sources.
- The positive candidate converges in every run; the negative candidate does not converge and is not inert in every run.
- Backend semantic signatures match within each size × candidate arm.
- Rewrite rules, noise-node values and chain edges, and original observations remain unchanged.
- Report all memory samples and median PSS/private-dirty peak deltas; preserve each arm even if its memory or outcome differs.

## Interpretation limits

One authored correction family and one host. The two candidates differ in utility but are not a representative candidate distribution. PSS samples every 10 ms and can miss short peaks; no kernel peak or timing advantage is claimed. This extends operation coverage, not cross-family or natural-task prevalence.
