# Shared-prefix adapter compatibility probe v1 preregistration

**Status:** preregistered interface probe; no serving integration claim.

## Question

Can the substrate's consumer-neutral immutable snapshot/fork lifecycle support the ownership and isolation shape of a shared-prefix consumer, independent of snapshot backend, with exact eager-copy parity and predictable cancellation/drop behavior?

## Boundary

This probe uses synthetic fixed-size payloads represented as graph nodes. A small `PrefixStore` adapter owns published prefix references and request handles; the substrate snapshot API supplies the immutable base and isolated mutable continuations. The payload is not model KV data. The probe does not implement a scheduler, batching, token generation, a KV allocator, or a vLLM adapter.

## Protocol

- Compare the public default snapshot backend with the private eager-copy control. The adapter must not branch on backend identity.
- Cross unrelated background graph size `{0, 1,000, 10,000}` nodes with five fresh-process repetitions per backend/size cell; randomize backend order per repetition.
- Build one published prefix of eight deterministic blocks, fork two requests from it, append four distinct continuation blocks to each, read both full sequences, cancel one request while the sibling remains live, fork and read a third request, then cancel all requests and release the snapshot and primary.
- Inject a primary revision change after prefix publication. A request carrying that newer revision as its expected prefix revision must be rejected; the original captured revision remains usable and produces the published prefix exactly.
- In each worker capture `/proc/self/smaps_rollup` at primary baseline, snapshot live, two requests live, one request cancelled, all requests cancelled, snapshot released, and primary released. Report RSS/PSS/private/shared values as whole-process observations, not per-object accounting.
- Retain deterministic receipts containing snapshot ID, captured revision, request IDs, prefix block IDs, continuation block IDs, cancellation state, and visible block digests.

## Gates

1. Prefix content matches the eager oracle before and after each fork.
2. Request continuations are divergent and invisible to the primary, published prefix, sibling, and later request.
3. Cancelling one request does not affect a live sibling; all requests can be cancelled and re-created over the same captured base.
4. A mismatched expected revision is refused before creating a request branch.
5. Receipts and outcomes are deterministic across backend arms for the same worker seed.
6. Adapter allocation accounting returns to zero active request-owned blocks after cancellation; after snapshot/primary drop, no handles remain. PSS deltas are reported descriptively and are not a sole leak oracle.
7. Every worker passes all semantic gates before its row is retained. Any disagreement aborts the panel.

## Interpretation

Passing establishes compatibility with a small shared-prefix-shaped ownership interface, plus the measured isolation and lifecycle properties. It does not establish vLLM compatibility, KV-block layout compatibility, real serving memory efficiency, scheduler correctness, cancellation under concurrency, throughput, or token latency. Performance is descriptive; no speedup is required for the capability gate.

## Reproduction artifacts

The runner, source/native fingerprints, randomized schedule, worker receipts, raw capture, and independent analyzer will be linked from the results report after execution.
