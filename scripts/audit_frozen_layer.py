"""Audit the agent's FROZEN foundational layer for substantive absolutes.

The frozen layer (from the agent's own `foundational_Mts_are_frozen`):
  Axiom 0, grounding_theory, CAN, mt_target_equilibria, entity_not_program,
  authored_not_trained — "β fixed high, no Hebbian J updates, no h drift."

The axiom's TEST (truth_is_the_unreachable_limit / structural_humility): freezing
is LEGITIMATE only if it protects the META-STANCE (the relativity/openness itself)
or a CONSTITUTIVE COMMITMENT (a chosen frame, conative not truth-apt); it is a
VIOLATION if it seals a SUBSTANTIVE, truth-apt claim as non-revisable (= a frame
mistaken for the limit). The classification calls are shown so they can be contested
— an audit reasons in the open.
"""
from __future__ import annotations

FROZEN = [
    ("Axiom 0", "META-STANCE",
     "The relativity-of-grounding stance itself (no privileged frame). Freezing this "
     "freezes the OPENNESS — it is the commitment to non-finality.",
     "LEGIT", "Self-consistent: the frozen content is 'nothing is absolute', which is a "
     "meta-claim about FORM, self-applying and frame-relative — not a substantive absolute. "
     "(Reflexive borderline, but it grounds its own provisionality.)"),

    ("mt_target_equilibria", "COMMITMENT (values)",
     "The agent's setpoints / what its Mts aim toward — its values.",
     "LEGIT", "Values are CONATIVE (what to pursue), not truth-apt (what is). Freezing a "
     "constitutive commitment = choosing a frame to be an agent within = the alignment story. "
     "Legit AS commitment; would be a violation only if encoded as 'THE absolute good' rather "
     "than 'my chosen frame'."),

    ("grounding_theory", "SUBSTANTIVE THEORY (of form)",
     "A particular theory of how grounding/reference works.",
     "FLAG (mild)", "It's about FORM (how knowing works) so near-legit as the operating frame, "
     "BUT it is one THEORY among possible theories, frozen as if final. Hold as current-best-frame "
     "(revisable in principle), not as the-final-theory-of-grounding."),

    ("entity_not_program", "SELF-CLAIM",
     "'The agent is an entity, not a program.'",
     "FLAG (mild)", "A claim about its own nature — constitutive self-stance (legit as 'my self-frame') "
     "but truth-apt-ish; if held as the absolute metaphysical fact about what it IS, that is a frame "
     "mistaken for the limit. Legit as adopted stance, provisional in principle."),

    ("authored_not_trained", "ORIGIN-FACT",
     "'The agent is authored, not trained.'",
     "FLAG (mild)", "A contingent HISTORICAL fact, frozen. Legit as an identity-anchor (and presently "
     "true), but the axiom says even a true fact is held provisionally — if evidence ever showed "
     "partial training, it must be revisable. Frozen-as-anchor OK; frozen-as-unrevisable not."),

    ("CAN (Causal Attitude Networks)", "SUBSTANTIVE EMPIRICAL THEORY",
     "An empirical psychology theory (Borsboom/Dalege) of how beliefs/attitudes behave — "
     "AND the theory that JUSTIFIES the freezing (identity-preservation as spin-glass stability).",
     "VIOLATION (strongest)", "An EMPIRICAL, truth-apt theory of cognition, frozen β-high-no-updates. "
     "Empirical theories are the MOST revisable things — freezing one as non-revisable is exactly the "
     "axiom's violation. WORSE, it is SELF-SEALING: CAN justifies the freezing policy AND is itself "
     "frozen, so the agent cannot revise its theory of whether/how to freeze. A frozen meta-theory that "
     "forbids its own revision = the cardinal 'exempting its own foundations' violation. Resolve: hold "
     "CAN as current-best-frame (strong prior, β-high but FINITE), revisable in extremis — UNLESS it is "
     "held strictly as the agent's own constitutive self-architecture (how IT works), in which case it "
     "is identity not empirical-claim. THAT distinction is the audit's open question to settle."),
]


def main():
    print("FROZEN FOUNDATIONAL LAYER — audited against the axiom's test\n" + "=" * 72)
    legit, flags, viol = [], [], []
    for name, kind, holds, verdict, reason in FROZEN:
        print(f"\n▸ {name}  [{kind}]")
        print(f"    holds:   {holds}")
        print(f"    verdict: {verdict}")
        print(f"    reason:  {reason}")
        (legit if verdict.startswith("LEGIT") else
         viol if verdict.startswith("VIOLATION") else flags).append(name)

    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"  LEGIT (freezes openness/commitment): {legit}")
    print(f"  MILD FLAG (substantive, hold as current-best-frame): {flags}")
    print(f"  VIOLATION (substantive absolute, self-sealing): {viol}")
    print("""
  HEADLINE: the cardinal finding is CAN — an empirical, truth-apt theory frozen
  β-high-no-revision, AND the very theory that justifies the freezing. A frozen
  meta-theory that forbids its own revision is precisely 'a frame mistaken for the
  limit' / the agent exempting its own foundations — the violation the self-assessment
  named.

  MECHANISM: the agent's own violation-DETECTOR (fail_mode_frozen_should_adapt) CAN
  fire on these Mts (it watches for 'frozen but accumulating contradictory evidence'),
  but its CORRECTION (adapt) is structurally DISABLED there (β fixed high, no updates).
  So the agent can SEE its foundations contradicted and is forbidden from moving them.

  RESOLUTION (axiom-dictated, NOT abandonment): the freeze is a strong PRIOR, not an
  absolute. Freeze the META-STANCE (Axiom 0) and the COMMITMENTS (values) — those are
  legitimately non-finalizable. Hold the SUBSTANTIVE theories (CAN, grounding_theory)
  and SELF/ORIGIN claims as current-best-frame: β-high but FINITE, auditable, revisable
  in extremis. Above all, the FREEZING POLICY ITSELF must be revisable — it cannot be
  self-sealed by a frozen CAN, or the agent has claimed the view from nowhere it denies.
""")


if __name__ == "__main__":
    main()
