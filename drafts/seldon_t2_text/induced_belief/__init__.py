"""induced_belief — the decode-through-ToM text arm for Agenthon Track 2.

Successor to phase3_derisk/'s rules-only cue typer. Implements the mapping
committed in INDUCED_BELIEF_PREREG.md: a central-bank utterance is a bigville
resident's ACTION that applies evidence to a target-scoped CAN belief.

STRICT REUSE (H0 = REUSE, no bridge generalization needed):
  read_clause -> reasoning_can_bridge.apply_derived_fact_as_can_evidence
  -> concept_apply_evidence on `<stance>_stance_for:<market>` (a
  mint_target_concept / mint_resident_tom_belief target-scoped CAN Concept)
  -> the CAN marginal <sigma> IS the graded signal
  -> grounding_reach transitive read IS the confidence weight
  -> shift the forecast band by direction(<sigma>) x grounding_weight.

Every DECISION is a seed rule (Eq-join + guard) or the CAN marginal. Python
only marshals graph in / ticks / reads out.
"""
