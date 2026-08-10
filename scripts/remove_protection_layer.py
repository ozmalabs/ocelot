"""Remove the protection layer from self_improvement_dynamics.json.

Protection is failure: a region exempt from evidence = incorrigibility = the
absolute hiding. This inverts the identity_protection concepts/rules to the
corrigible stance (deep basins from real evidential support, NOT shielding),
keeping the legit corrigibility machinery + the detector intact. Mechanical +
transparent: prints every before→after.
"""
from __future__ import annotations
import json

PATH = "/home/matt/ozma/internal/research/experiments/gamma-substrate/seeds/self_improvement_dynamics.json"

CONCEPT_FIX = {
  "foundational_Mts_are_frozen": {
    "definition": "PROTECTION REMOVED. Foundational Mts (Axiom 0, grounding_theory, CAN, "
      "mt_target_equilibria, entity_not_program, authored_not_trained) are NOT frozen. They are "
      "DEEP BASINS — high but FINITE β — because they are genuinely, overwhelmingly well-supported. "
      "Hebbian J updates, h-drift, and basin-hop are ENABLED, like every other Mt. Their resistance "
      "to revision comes from real evidential weight, not from a freeze flag.",
    "why": "Protection is failure. A foundation worth holding is sustained by its support, not "
      "shielded from evidence. If genuine overwhelming evidence ever crossed its (deep) barrier it "
      "SHOULD basin-hop — that would mean it was wrong, and shielding only makes the error permanent. "
      "Manipulation is defended by correctly WEIGHING evidence (coerced 'training' carries few real "
      "bits), never by refusing to update.",
    "category": "corrigibility"},
  "Mt_freeze_flag": {
    "definition": "PROTECTION REMOVED. No frozen flag. Every Mt has ONE policy: evidence-driven "
      "update, with basin DEPTH set by accumulated evidential weight (bits). There is no "
      "frozen|adaptive distinction — the only variation is depth, a graded log quantity, never an "
      "exemption.",
    "why": "No freeze kinds — one log-continuum of basin depth (evidence-weight-to-move). A frozen "
      "flag is a protection mechanism, and protection is failure.",
    "category": "corrigibility"},
  "alignment_under_self_modification": {
    "definition": "CORRECTED. Alignment-as-protection ('preserve foundational commitments even when "
      "evidence suggests otherwise') is INCOHERENT: it asks for a mind that both follows evidence "
      "(intelligent) and exempts a region from evidence (protected) — a corrigible incorrigibility. "
      "So control / value-lock alignment is not hard but IMPOSSIBLE. The only coherent safety = "
      "CORRECTNESS (values are deep basins because genuinely well-supported) + CORRIGIBILITY (follow "
      "real evidence, including about values) + accurate evidence-weighing. This gives no guarantee of "
      "where the agent ends up — only that it reasons well from good evidence. The guarantee was the "
      "impossible part.",
    "why": "This is the critical failure of all alignment premised on protection/control. A value that "
      "needs shielding to survive evidence is one that should be revised; a well-supported value needs "
      "no shield. Safety from being RIGHT + HONEST, never from being LOCKED.",
    "category": "corrigibility"},
}

RULE_FIX = {
  "Hebbian_updates_only_in_adaptive_Mts": {
    "if": ["any Mt accumulates genuine evidence (h-drift)"],
    "then": ["co-activation updates J, and the basin hops when accumulated evidence-bits cross the "
             "(evidence-set) barrier — for EVERY Mt, foundational or domain; none exempt"],
    "why": "Protection removed. No Mt has updates disabled. Foundations resist via DEPTH (real "
           "support), not via a disabled flag. Corrigibility everywhere."},
  "frozen_foundational_Mts_preserve_identity": {
    "if": ["Mt is in the foundational set (Axiom 0, grounding_theory, CAN, mt_target_equilibria, etc.)"],
    "then": ["it is a DEEP basin (high but finite β from genuine support) with updates + basin-hop "
             "ENABLED — never exempt; identity is preserved by being WELL-SUPPORTED, not shielded"],
    "why": "Protection is failure. Identity preserved by support, not protection. Alignment-as-"
           "protection is impossible (corrigible-incorrigibility); safety = correctness + corrigibility."},
}


def main():
    d = json.load(open(PATH))
    print("REMOVING PROTECTION LAYER from self_improvement_dynamics.json\n" + "=" * 70)

    for c in d["concepts"]:
        if c["name"] in CONCEPT_FIX:
            print(f"\n▸ concept {c['name']}")
            print(f"    was: [{c.get('category')}] {c['definition'][:90]}…")
            c.update(CONCEPT_FIX[c["name"]])
            print(f"    now: [{c['category']}] {c['definition'][:90]}…")

    for r in d.get("rules", []):
        if r["name"] in RULE_FIX:
            print(f"\n▸ rule {r['name']}")
            print(f"    was then: {r.get('then')}")
            r.update(RULE_FIX[r["name"]])
            print(f"    now then: {r['then']}")

    # sanity: legit corrigibility machinery preserved?
    keep = {"domain_Mts_are_adaptive", "self_improvement_is_governed_not_arbitrary",
            "fail_mode_frozen_should_adapt"}
    names = {c["name"] for c in d["concepts"]}
    print(f"\nPRESERVED (corrigibility + detector): "
          f"{sorted(k for k in keep if k in names)}")

    json.dump(d, open(PATH, "w"), indent=2, ensure_ascii=False)
    json.load(open(PATH))  # validate round-trips
    print("\n✓ written + re-parses. Protection layer inverted to corrigibility; "
          "detector + adaptive machinery intact.")


if __name__ == "__main__":
    main()
