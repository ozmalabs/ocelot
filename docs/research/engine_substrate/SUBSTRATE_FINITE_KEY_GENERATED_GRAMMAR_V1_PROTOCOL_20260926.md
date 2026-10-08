# Finite-key generated grammar and native closure v1 protocol

## Question

Across a preregistered set of admitted and refused finite-key syntax variants, does the checker classification match the intended grammar, and do accepted rule programs parse and reach the same terminal graph as an independent interpreter?

## Generated panel

The runner constructs positive programs covering finite scalar mint-key values (`null`, booleans, integers, strings), empty and multi-attribute keys, pre-existing matching witnesses, one/two/three-edge positive matches, repeated variables, fresh-variable edge endpoints, multiple ordered rules, and multiple edge types. The negative panel covers extra rule fields, empty matches, unrestricted `add_node`, computed mint keys, nonempty output-edge attrs, unbound/forward endpoints, reused minted variables, unsupported effects/arity, incomplete node inventories, duplicate facts, and writes to edge types with attributed initial facts.

Every positive case is passed to both the analyzer and the native rule parser/scheduler. A separate monotone closure interpreter enumerates positive edge joins and the admitted insertion effects to fixed point. The full normalized node/edge state, native termination status, and progress bound are compared. Negative cases must be refused by the analyzer; rejected programs are not sent to native execution.

## Provenance and gates

The pre-run lock covers runner, fixture analyzer, checker, protocol, manifest helper, native rule parser/effect/runtime sources, build manifest, and loaded native extension. The shared run manifest includes the nonempty console log and current-build status. The independent analyzer verifies exact fixture inventory, all checker outcomes, positive native/reference closure equality, native fixed-point reports, progress bounds, lock stability, hashes, and logs.

## Claim boundary

This panel samples the stated grammar and rule shapes. It does not exhaust all JSON values, every runtime rule option, arbitrary program sizes, nonmonotone effects, or parser implementations on every platform. A pass strengthens evidence for the named fragment but does not establish general checker completeness or a general engine-wide termination theorem.
