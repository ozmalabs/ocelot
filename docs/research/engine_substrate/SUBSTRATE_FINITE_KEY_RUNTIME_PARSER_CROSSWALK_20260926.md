# Finite-key analyzer to runtime parser crosswalk (2026-09-26)

## Scope

This is a source audit of the accepted syntactic fragment in `scripts/analyze_mint_termination_fragment.py` against `runners/dsl/src/py.rs::parse_rule_json` / `parse_effect_json` and `runners/dsl/src/rewrite.rs::Effect`. It narrows the remaining grammar-equivalence question; it does not replace execution evidence or prove the termination theorem.

## Accepted form mapping

| Analyzer-accepted form | Runtime parser contract | Audit result |
|---|---|---|
| Rule object with only `name`, `match`, `effects` | Runtime reads these fields and supplies defaults for omitted metadata. It also accepts optional `where`, `batch`, `match_type`, scheduling fields, IDs/revisions, and index hints. | Analyzer is a strict field subset. Runtime's extra fields are excluded, including `where` even when null. |
| Nonempty `match` list of 3-string triples `[src, edge_type, tgt]` | Parser requires each item to be an array of exactly three strings and compiles every triple as a positive edge match. Empty lists are parser-valid but checker-rejected. | Every checker-accepted match triple has the parser's required representation; checker excludes empty matching. |
| `add_node_if_absent` list of exactly four items with string variable/type and an attrs object of finite JSON scalar literals | Runtime parses the same operation and variable/type positions; object attrs become literal `EffectArg`s unless wrapped in `__term__`. | Checker restricts to literal `null`/boolean/integer/string values and excludes computed terms, non-scalar JSON, and extra array items. |
| `add_edge` list of exactly five items, string endpoints/type, empty attrs | Runtime parses the same operation and requires an attrs object if supplied at position 4; nonempty attrs are accepted by runtime but rejected by checker. | Every checker-accepted add-edge is a parser-compatible insertion-only subset. |
| Initial edge as `[src,type,tgt]` or with an attrs object | The graph loader owns initial graph parsing; rule parser does not consume this inventory. | Checker validates a complete endpoint inventory, uniqueness, and refuses writes to edge types with initial attrs. This is additional proof-side input validation. |

The native effect implementation confirms that `AddNodeIfAbsent` reuses the first same-type node whose attributes contain the authored key/value subset, while `AddEdge` can update attributes on an existing edge. Those semantics justify the checker's fixed-literal mint-signature bound and the refusal to write an edge type that already has attributed initial facts. See [`rewrite.rs`](../../../runners/dsl/src/rewrite.rs) and [`py.rs`](../../../runners/dsl/src/py.rs).

## What is and is not established

The syntactic mapping is compatible by inspection: every operation form the checker can admit is accepted by the runtime parser in the corresponding wire positions, and the checker is stricter about optional fields, lengths, computed arguments, and attributes. The locked checker-hardening probe additionally executes one admitted recursive rule through the parser and native closure, with exact graph/access/status checks. Existing finite-key family and interaction captures execute additional accepted rule forms and compare their terminal graph against independent interpreters.

This is not exhaustive parser equivalence. The native parser has permissive defaults and many effect kinds; no machine-generated cross-product covers every admitted scalar, variable collision, rule sequence, or interaction with runtime scheduling. Before using the analyzer as a general admission gate, add generated accepted/rejected syntax cases and broader native closure oracles, and lock checker/parser versions together on each result.
