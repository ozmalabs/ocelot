# Native seed manifest caller audit

Date: 2026-09-25  
Status: static Python AST audit complete; runtime reachability and dataflow not established

## Findings

The Python repository contains 922 direct syntactic calls to `load_seed_manifest` across 633 files. The audit finds 173 call sites in application paths under `domains/`, `substrate/`, and `worlds/`, 356 in tests, 376 in scripts (including six calls in the integration contract probe), and 17 in other top-level areas. Of the calls, 216 use a receiver expression ending in `_inner`, which directly reaches the underlying PyO3 object; other calls also reach that object through adapter attributes such as `inner` or `native`. The source contains one PyO3 implementation, `PySubstrate::load_seed_manifest`, so a projection at that boundary can cover these call shapes without editing each caller.

Before the integration change, the function passed the entire Python manifest through `pyobj_to_json`, then read only ten top-level keys: `nodes`, `edges`, `productions`, `rules`, `reflexes`, `id`, `self_modification_patchable_rules`, `area`, `order`, and `latency_class`. The projection experiment exercised the exact key set at N=512/737 and preserved complete boot/self-model state on the frozen bulk-load corpus.

## Contract and risk audit

The Python facade now documents the ten-key contract, and the PyO3 implementation applies it. Many application routes bypass the facade and call the native object directly, so a facade-only optimization would miss a large part of the repository. The native-boundary projection changes one incidental behavior: the old whole-object `json.dumps` rejected a manifest containing a non-JSON value under an otherwise-unused top-level key; the projection ignores that value. Inputs in consumed fields retain the same serialization and parse path.

The call-site census is syntactic. It does not prove runtime reachability, establish that all dynamically constructed arguments are plain dicts, or show that every application uses the same extension build. The result identifies call breadth and the shared native seam; it is not a complete semantic compatibility audit.

## Decision and next gate

The shared PyO3 boundary now carries the measured implementation. The ignored-key contract is documented, a 28-case optional-field/error matrix passes, release-extension provenance is current, and four uninstrumented cold/warm full-corpus workers match the frozen baseline exactly ([integration results](SUBSTRATE_NATIVE_SEED_PROJECTION_INTEGRATION_RESULTS.md)). Next extend parity into representative domain consumers across direct-call families and collect a quiet-host repeat against a same-source pre-change build before making a durable performance claim.

## Artifacts

- Static inventory and source hashes: [`audit report`](../../../evaluation/reports/native_seed_manifest_caller_audit_v1_20260925.json)
- Reproducer: [`AST caller auditor`](../../../scripts/audit_native_seed_manifest_callers_v1.py)
- Projection experiment: [`protocol`](SUBSTRATE_NATIVE_SEED_PROJECTION_PREREG_20260925.md), [`results`](SUBSTRATE_NATIVE_SEED_PROJECTION_RESULTS.md)
