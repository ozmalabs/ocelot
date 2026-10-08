# Primitive-menu query and help policy v1.1 results

## Valid capture and analysis

V1 is retained as a diagnostic because its analyzer did not replay a
selector-abstention reason when the selector emitted no query. The v1.1
amendment corrects that check and reruns all 25 locked panels. Its independent
analyzer passes 7/7 gates, including schedule, transition, help-trigger,
source-binding, and holdout checks. Do not combine v1 and v1.1 summaries.

The task panel has five authored relations and five deterministic draws each:
additive conservation, product conservation, ordering, one-component
opposition, and inequality. The initial menu offers Base (Neg/Eq/And) plus
Plus, Times, and Lt extensions. Every task has eight positive and eight
negative training labels; the policy receives the menu and observations, not
the task label. A teacher callback, invoked only on a registered unresolved
signal, supplies one task-relevant family hint. That hint is an oracle-assisted
upper bound, counted as a separate help call.

## Outcomes

| Task | Entropy query-only | Fixed-order query-only | Help-trigger result |
|---|---|---|---|
| Additive | 5/5 exact singletons; median 2 labels | 5/5; median 2 | No help requested |
| Product | 5/5 exact singletons; median 2 | 5/5; median 2 | No help requested |
| Ordering | 5/5 exact singletons; median 3 | 2/5 exact singletons; 3/5 ambiguous at budget 6 | Lt hint resolves the 3 ambiguous panels |
| Opposition | 5/5 syntactically ambiguous after one label | 5/5 remain ambiguous at budget 6 | Base hint is requested, although all entropy survivors are exact on the expanded finite grid |
| Inequality | Selector abstains with 2 survivors after 0–1 labels in all 5 panels | 6 labels still leave ambiguity in 5/5 | Not hint yields an exact model in all 5 panels |

The entropy policy uses no help on additive, product, or ordering. It requests
five Base hints for opposition and five Not hints for inequality. Across the
initial menu, every inequality panel already contains an exact model expressible
with Lt/Eq compositions; the Not hint therefore helps disambiguate the
hypothesis set but adds no new semantic coverage in this experiment. In the
opposition panels, all four remaining entropy candidates per panel are exact
on the expanded finite grid, so requesting a Base hint adds no measured
behavioral capability there. A selector abstention or syntactic ambiguity
alone is therefore too coarse a help trigger.

## Domain-coverage correction

The preregistered 1,296-case holdout uses six nonzero fractional values. A
post-capture analysis expands the grid to seven values including zero
(2,401 combinations). This confirms the key distinctions above: all four
opposition survivors are exact on that expanded grid; each inequality panel
has one exact and at least one false survivor. The panel's integer training
values also exclude zero. These scores remain finite-grid evidence, not
universal proofs, and were not policy inputs. See the separate
[semantic addendum](../../../evaluation/reports/primitive_menu_help_policy_v1_1_semantic_addendum_20261003.json)
and its [analysis script](../../../evaluation/substrate_capability/analyze_primitive_menu_help_semantic_addendum_v1.py).

## Interpretation and next gate

Entropy selection helps on the ordering family relative to the fixed row order.
For inequality, the selection pool cannot separate surviving candidates even
though one generalizes and another does not; a finite teacher hint resolves
this particular ambiguity. For opposition, the same abstention is harmless on
the checked domain because all remaining candidates agree with the target.
Consequently, a useful meta-policy needs a behavioral adequacy measure that
separates harmful ambiguity from harmless representational ambiguity. The
current finite selector and help trigger do not provide that distinction.

Next measure larger and independently sampled query/audit domains, especially
zero-valued and boundary cases; score all-survivor adequacy separately from
unique-Term identification. Then compare a policy that continues with
challenge probes, requests a teacher/operator hint, or returns an explicit
behavioral-equivalence class. Price label and help resources independently
and report the Pareto tradeoff; do not equate the simulated teacher with a
live LLM or natural task transfer.

## Reproduction artifacts

- [Amendment](PRIMITIVE_MENU_HELP_POLICY_V1_1_AMENDMENT_20261003.md)
- [Original protocol](PRIMITIVE_MENU_HELP_POLICY_V1_PREREG_20261003.md)
- [Runner](../../../evaluation/substrate_capability/primitive_menu_help_policy_v1_1.py)
- [Corrected analyzer](../../../evaluation/substrate_capability/analyze_primitive_menu_help_policy_v1_1.py)
- [Source and panel lock](../../../evaluation/substrate_capability/primitive_menu_help_policy_v1_1_lock_20261003.json)
- [Capture](../../../evaluation/reports/primitive_menu_help_policy_v1_1_20261003.json)
- [Primary analysis](../../../evaluation/reports/primitive_menu_help_policy_v1_1_analysis_20261003.json)
- [Post-capture semantic addendum](../../../evaluation/reports/primitive_menu_help_policy_v1_1_semantic_addendum_20261003.json)
