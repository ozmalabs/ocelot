# Finite-key fragment admission-path probe v1 preregistration

Date: 2026-09-28  
Question: do the current rule authoring, checkpoint import, revision, and graph self-mint routes require rules to pass the finite-key closure checker before becoming live?  
Status: frozen before confirmatory capture. This is a bounded admission-path probe, not an engine change or a termination benchmark.

## Rationale

The finite-key closure theorem is conditional on a narrow monotone fragment. Source review found several production routes that parse or revise rules but do not invoke the checker. This probe tests whether that source-level gap is observable at runtime, and records how far each route proceeds. It does not execute the deliberately out-of-fragment rule's closure.

## Locked fixture and routes

The negative rule uses a nonempty positive edge match and a fresh `add_node` effect. The initial graph inventory contains both matched endpoints and one trigger edge. The independent finite-key analyzer must reject the rule because fresh `add_node` is outside its admitted insertion fragment. No worker runs closure on the direct, import, or patched negative rules.

Each fresh worker exercises four isolated substrates:

1. direct `PySubstrate.add_rule`;
2. `import_rules` checkpoint restoration;
3. a valid revision/hash-CAS `apply_rule_patch` that replaces an admitted no-effect clause with the negative `add_node` effect; and
4. graph-resident self-mint via `SetRuleClause("__mint__")`, compiling a `Rule` node with the same out-of-fragment effect into the live struct store. Its match edge is absent, so the newly minted rule cannot fire during the probe.

The primary outcome is whether the runtime route accepts and installs the rule despite the independent checker refusing it. Record rule count, revision metadata where available, route error, graph deltas, and source/native fingerprints. Use three separate worker processes and preserve a row for every route even on error.

## Gates and interpretation

- Three distinct fresh worker PIDs, each completing all four routes.
- Before/after source locks match, including native extension and the finite-key checker.
- The independent checker rejects the negative fixture in every worker.
- Every route reports parser/transaction outcome, installed rule count, and whether the out-of-fragment rule became live.
- No closure call is made on the negative rule; the graph self-mint worker confirms that the new rule's trigger edge is absent.

If all four routes install the rejected rule, the experiment establishes a runtime admission gap for those exact route implementations. It does not prove arbitrary malformed rules are accepted, that the rules terminate, or that all alternative construction paths were covered. A later admission-gate design must validate after the final parsed/revised body and before installation/commit, then preserve compatibility and refusal diagnostics.

## Reproduction and custody

Run `python3 scripts/substrate_mint_fragment_admission_path_probe_v1.py --lock` to emit the frozen input fingerprint, then create the lock at `evaluation/substrate_capability/mint_fragment_admission_path_probe_v1_lock_20260928.json`. Run the parent command only after the lock matches. It writes raw captures to `evaluation/reports/substrate_mint_fragment_admission_path_probe_v1_20260928.json`; the independent analyzer writes `evaluation/reports/substrate_mint_fragment_admission_path_probe_v1_analysis_20260928.json`. The raw result is immutable after capture; corrections require a new version and preserved prior files.
