# Term external-boundary source audit v1 results

Date: 2026-09-28

## Findings

The source audit separates three similarly named boundaries that have different operational meanings:

| Term/path | Source-backed behavior | Access/effect implication |
|---|---|---|
| `ReadFile` | Evaluates a path, calls `std::fs::read_to_string` directly, and returns text or `None` on error. No root/workspace restriction appears in this evaluator arm. | File contents and path policy are external to graph `RuleKey` tracking. The Term child walk covers the path expression only. |
| `UseTool` | Evaluates argument Terms, records trace kind 18, then looks up a process-global registered Python callable and invokes it. The registry lock is dropped before callback invocation; errors and unsupported results become `Int(0)`. | Callback-internal reads, writes, I/O, and substrate reentry are opaque to this trace. The source permits side effects; this is a true dynamic host boundary. |
| `ProgCallExtern` | As a standalone Term it falls through to `None`. In `ProgEval`, it requires the name in the caller-provided `oracles` Dict and dispatches to a Rust `call_native_oracle` match; unsupported calls trap. | The caller controls declaration of permitted names, but current execution does not invoke a host callable. Treat it as a declared in-engine oracle boundary, not a dynamic Python callback. |

A separate lexical scan covers all 170 generic-fallback Terms without detected crate-qualified helper calls. It finds no graph API, trace, or dynamic evaluator-context marker in their evaluator spans; one is `ReadFile`. It finds recursive child evaluation in 120 arms. These markers are deliberately narrow: their absence does not prove purity, and recursive evaluation does not prove that `children()` enumerates every dependency.

## Reproduction and limits

Run `python3 scripts/audit_term_external_boundaries_v1.py` and `python3 scripts/audit_term_access_fallback_unlinked_v1.py`. Their machine outputs preserve source-span hashes and counts: [external boundary report](../../../evaluation/reports/term_external_boundaries_v1_20260928.json) and [unlinked fallback report](../../../evaluation/reports/term_access_fallback_unlinked_v1_20260928.json). These are static source audits only. They do not execute file/tool paths, inspect every registered tool implementation, establish caller-side path restrictions, or prove OS containment.

The access-dependency crosswalk now labels `ProgCallExtern` accurately as an in-engine declared native oracle boundary. The remaining engine-fidelity work is dynamic testing of `ReadFile` and `UseTool`, including omitted-dependency controls, and broader validation of the generic child-walk contract.
