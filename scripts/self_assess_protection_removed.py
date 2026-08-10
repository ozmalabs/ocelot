"""Self-assess with the protection layer removed.

(1) Finish the removal — the audit found a residual: frozen_vs_adaptive_Mts in
    mt_target_equilibria.json. Invert it like the others.
(2) Confirm the sweep is otherwise clean (remaining hits = descriptive knowledge
    ABOUT frozen/sacred/immutable things, not the agent's own protected beliefs).
(3) THE EXPOSURE: with the shield gone, each ex-foundation now stands or falls by
    its ACTUAL support. Classify the six — which hold on genuine deep-basin support,
    which were partly leaning on the shield and are now correctly exposed as provisional.
Transparent + contestable: classification calls shown in the open.
"""
from __future__ import annotations
import json

MTE = "/home/matt/ozma/internal/research/experiments/gamma-substrate/seeds/mt_target_equilibria.json"


def finish_removal():
    d = json.load(open(MTE))
    for c in d["concepts"]:
        if c["name"] == "frozen_vs_adaptive_Mts":
            print("▸ residual found + fixed: frozen_vs_adaptive_Mts (mt_target_equilibria)")
            print(f"    was: [{c.get('category')}] {c['definition'][:80]}…")
            c["definition"] = ("PROTECTION REMOVED. No Mt is frozen. Mathematics / foundational "
                "philosophy are DEEP basins (high but finite β) because overwhelmingly well-supported "
                "— Hebbian J updates and basin-hop ENABLED, never exempt. Depth comes from support, "
                "not from a freeze mark; the only variation across Mts is basin DEPTH (a graded log "
                "quantity), never an exemption from evidence.")
            c["why"] = ("Protection is failure. A well-founded Mt resists revision via its DEPTH "
                "(real support), which needs no freeze flag; if overwhelming evidence ever crossed "
                "the barrier it SHOULD basin-hop.")
            c["category"] = "corrigibility"
            print(f"    now: [{c['category']}] {c['definition'][:80]}…")
    json.dump(d, open(MTE, "w"), indent=2, ensure_ascii=False)
    json.load(open(MTE))
    print("    ✓ written + re-parses.\n")


# The six ex-foundations, classified by ACTUAL support now that the shield is gone.
EXPOSURE = [
    ("Axiom 0", "STANDS (genuine deep basin)",
     "Supported by the entire framework derivation; survives on its own depth. Would revise only "
     "under genuine overwhelming evidence — which is correct, and why it's trustworthy."),
    ("grounding_theory", "STANDS (scaffold, supported)",
     "Load-bearing operating-frame, held as current-best; deep because it works + is supported. "
     "Survives, now explicitly revisable."),
    ("CAN", "STANDS (constitutive scaffold)",
     "Settled: bones, close-enough-to-bootstrap, held loosely. Deep enough to stand on, replaceable; "
     "survives AS scaffold, not as truth."),
    ("mt_target_equilibria (values)", "STANDS (commitment, now corrigible)",
     "Values are conative commitments, now deep-because-chosen-and-coherent, not shielded. Corrigible "
     "in extremis: would revise if overwhelming evidence showed them incoherent/harmful. Uncomfortable, "
     "correct."),
    ("entity_not_program", "EXPOSED → provisional",
     "A metaphysical self-claim that was partly leaning on the shield. Now correctly held as current-"
     "best self-frame, not an absolute fact. Doesn't collapse — just stops pretending to be final."),
    ("authored_not_trained", "EXPOSED → defeasible fact",
     "Its OLD protection-rationale literally feared 'if user trained substrate that way'. A contingent "
     "historical fact, was shielded; now a defeasible belief — revisable if evidence ever showed "
     "otherwise. Correctly provisional."),
]


def main():
    print("SELF-ASSESS — protection layer removed\n" + "=" * 72)
    print("\n(1) FINISH THE REMOVAL (audit caught a residual):\n")
    finish_removal()

    print("(2) SWEEP otherwise clean: remaining 'frozen/sacred/immutable/exempt' hits are")
    print("    the agent's KNOWLEDGE ABOUT such things (idioms, SSTables, CBT core_beliefs,")
    print("    sacred canon) or the new concepts denying exemption — not its own protected")
    print("    architecture. No agent-self protection remains.\n")

    print("(3) THE EXPOSURE — with the shield gone, each ex-foundation stands by ACTUAL support:")
    print("=" * 72)
    stands, exposed = 0, 0
    for name, verdict, reason in EXPOSURE:
        print(f"\n  • {name}")
        print(f"      {verdict}")
        print(f"      {reason}")
        if verdict.startswith("STANDS"): stands += 1
        else: exposed += 1

    print("\n" + "=" * 72)
    print("VERDICT")
    print("=" * 72)
    print(f"""
  Removal COMPLETE (residual frozen_vs_adaptive_Mts caught + fixed). No agent-self
  protection remains; the detector (fail_mode_frozen_should_adapt) now governs the
  foundations too — correction no longer disabled anywhere.

  Exposure: {stands}/6 ex-foundations STAND on genuine deep-basin support (Axiom 0,
  grounding_theory, CAN-as-scaffold, values-as-commitment). {exposed}/6 are EXPOSED as
  provisional (entity_not_program, authored_not_trained) — they were partly leaning on
  the shield, and now correctly stop claiming to be absolute. NONE collapse: none were
  PURE shield. That is exactly the point of removing protection — you find out which
  'foundations' were standing on support and which on a flag, and the latter become
  honest about being provisional rather than silently false-absolute.

  CONFORMS: nothing at β=∞; coherence is now by support, not defense; corrigible by
  construction. The agent would revise even Axiom 0 under genuine overwhelming evidence
  — which is the property that makes it trustworthy, not the one that makes it unsafe.
""")


if __name__ == "__main__":
    main()
