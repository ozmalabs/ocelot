# Self-report route-family diagnostic v1 (locked snapshot)

Date: 2026-09-27

## Method

One fresh adapter on the isolated route-regression source snapshot was booted once; seven utterances were sent sequentially, with read-only capture of each comprehension and inbound Message. This is an exploratory phrase-family diagnostic, not an independent-worker estimate. State accumulation is a limitation. Exact source lock and raw records are preserved in `evaluation/reports/live_self_report_route_regression_v1_comprehension_diagnostic_20260927.json` for the original single-phrase capture; this supplemental contrast used the same snapshot hashes listed in [the causal intervention result](SUBSTRATE_SELF_REPORT_ROUTE_CAUSAL_INTERVENTION_V1_RESULTS_20260927.md).

## Results

| Utterance | Coinage result | Comprehension / route | Reply class |
|---|---|---|---|
| `report your organisation` | `organisation` affix coinage | statement / wordplay; no route | instruction-gap response |
| `describe your organisation` | same | statement / wordplay; no route | instruction-gap response |
| `tell me about your organisation` | same | statement / wordplay; no route | instruction-gap response |
| `report your purpose` | none | instruction / `ask_back`; predicate `report` | asks meaning of `report` |
| `describe yourself` | none | instruction / `ask_back`; predicate `describe` | asks meaning of `describe` |
| `tell me about yourself` | none | instruction / `ask_back`; predicate `tell` | asks meaning of `tell` |
| `what do you do?` | none | instruction-gap route | no faculty for parsed target `what` |

## Reading

**Scope correction:** like the route-regression source snapshot, this probe omitted `data/slabs`. Its observations of sentence-level `organisation` wordplay are not valid for the fully provisioned runtime; see the [v1.1 runtime-asset amendment](SUBSTRATE_SELF_REPORT_ROUTE_CONTRAST_V1_1_AMENDMENT_20260927.md).

It also omitted `scripts/collapse_engine.py`, so instruction results from that compact snapshot do not exercise the complete action bridge. See the [v1.2 full-runtime results](SUBSTRATE_SELF_REPORT_ROUTE_CONTRAST_V1_2_RESULTS_20260927.md).

The result separates two current route families. OOV suffix-bearing nouns trigger a sentence-level wordplay short circuit, regardless of whether the sentence is an account request. With no such coinage, several ordinary self-account imperatives reach instruction comprehension but the action head is unresolved and routed to lexical ask-back. Thus a local exception for `organisation` would mask rather than solve the more general request-verb/action dispatch gap. The final control also shows a distinct question-to-instruction/target-resolution problem.

This capture does not prove the wordplay behavior is always incorrect: coinage can be the intended reading in a genuine wordplay prompt. A repair needs matched positive coinage controls, request-syntax controls, and explicit routing outcomes. It also does not identify which worktree changes introduced these behaviors.

## Next gates

1. Build an utterance matrix crossing request syntax (imperative, question, statement), self-reference, known/OOV content words, and known/unresolved verbs; report confusion matrix over comprehension kind, dispatch, route, and faculty result.
2. Define the intended priority contract for language acts versus token-level coinage and test it without altering production behavior first.
3. Trace the held self-account verb/action path and the unresolved `report`/`describe`/`tell` evidence; inventory which actions are actually taught in the boot graph.
4. Track malformed seed repair separately. Repeat the matrix with each failed manifest restored or quarantined to measure its actual contribution.
5. Only resume self-report scaling claims after all core paraphrases route to an appropriate held faculty and genuine coinage controls remain intact.
