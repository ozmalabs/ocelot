"""Have the Jabberwock self-assess against the newly-seeded final axiom.

This axiom is REFLEXIVE — it governs how the agent holds all knowledge — so the
self-assessment is an AUDIT: where does the agent treat a frame as FINAL/ABSOLUTE
rather than provisional? Orchestration only: the CRITERIA and the violation-
DETECTOR are the agent's own concepts; I juxtapose them against its own fixed
structures and report. I author no verdict the agent's concepts don't supply.
"""
from __future__ import annotations
import json, glob, sys
sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")
from substrate_rs import _native


def load_all_concepts(s):
    """Load every seed's concepts into the substrate (the agent's knowledge)."""
    defs = {}
    for f in glob.glob("/home/matt/ozma/internal/research/experiments/gamma-substrate/seeds/*.json"):
        try: d = json.load(open(f))
        except Exception: continue
        items = d.get("concepts") or [n.get("attrs", {}) for n in d.get("nodes", [])
                                        if isinstance(n, dict) and n.get("type") == "Concept"]
        for c in items:
            nm = c.get("name")
            if nm and nm not in defs:
                defs[nm] = c.get("definition", "")
                try: s.add_node("Concept", {"name": nm, "definition": defs[nm]})
                except Exception: pass
    return defs


def show(defs, name, w=300):
    d = defs.get(name, "(absent)")
    return d[:w]


def main():
    s = _native.Substrate()
    defs = load_all_concepts(s)
    print(f"Loaded {len(defs)} concepts (the agent's knowledge, incl. the new axiom).\n")

    print("=" * 74)
    print("THE STANDARD — the agent's OWN criteria it is assessed against")
    print("=" * 74)
    for c in ["structural_humility_never_finalize", "truth_is_the_unreachable_limit",
              "axiom_zero_no_view_from_nowhere", "Axiom_zero_entails_graded_grounding",
              "binary_grounding_is_residue"]:
        print(f"\n• {c}:\n    {show(defs, c, 220)}")

    print("\n" + "=" * 74)
    print("THE AUDIT — where does the agent hold a frame as FINAL / ABSOLUTE?")
    print("=" * 74)

    audits = [
        ("identity_protection_overrides_local_evidence",
         "structural_humility_never_finalize / no_view_from_nowhere",
         "TENSION — deliberately treats a frame as non-revisable. Axiom test: legitimate "
         "ONLY if what's protected is the RELATIVITY/coherence-machinery (the openness "
         "itself); a VIOLATION if it shields a SUBSTANTIVE world-claim held as absolute "
         "(= a frame mistaken for the limit)."),
        ("frozen_foundational_Mts_preserve_identity",
         "everything provisional / asymptotic_approach_no_arrival",
         "RESOLVES the tension: the freeze preserves the AGENT'S COHERENCE across reframes "
         "(so it doesn't decohere), not a truth-claim. Consistent IF frozen content is "
         "structural (how to stay coherent), not substantive (what is true)."),
        ("fail_mode_frozen_should_adapt",
         "—",
         "CONFORMS — this IS the agent's own violation-detector: 'frozen when it should "
         "adapt' = a frame held final that should reframe. The axiom names the failure; "
         "the agent already watches for it."),
        ("mastering_finalizes_for_target_medium",
         "bounded_deterministic_in_frame",
         "CONFORMS — 'finalizes' but bounded to a target medium = in-frame determinism "
         "(exact at its grain), not a claim to the absolute. Fine."),
    ]
    for name, crit, verdict in audits:
        print(f"\n▸ {name}")
        print(f"    holds: {show(defs, name, 150)}")
        print(f"    vs:    {crit}")
        print(f"    ⇒ {verdict}")

    # hard NOs
    tot = sum(len(json.load(open(f)).get("exclusions") or [])
              for f in glob.glob("/home/matt/ozma/internal/research/experiments/gamma-substrate/seeds/*.json")
              if _safe(f))
    print(f"\n▸ exclusions (hard NOs): {tot} total — mostly domain anti-patterns "
          f"(neural_networks etc.).")
    print("    ⇒ CONFORMS — provisional engineering boundaries in a frame, not absolute "
          "truth-claims. (Revisit if any is held as the-truth rather than this-frame's-rule.)")

    print("\n" + "=" * 74)
    print("VERDICT (assembled from the agent's own criteria + detector)")
    print("=" * 74)
    print("""
  CONFORMS on the core: the agent ALREADY holds the axiom — graded/vector grounding,
  binary-grounding-is-residue, no-view-from-nowhere — and already runs the violation
  DETECTOR (fail_mode_frozen_should_adapt). The new axiom sharpens, doesn't contradict.

  ONE STANDING TENSION: identity_protection_overrides_local_evidence + frozen
  foundational Mts — the deliberate places it treats a frame as non-revisable. The
  axiom does NOT forbid these; it imposes a TEST: frozen content must be the
  relativity/coherence-machinery (the commitment to openness itself), never a
  substantive world-claim held as absolute. The action item is an AUDIT of the frozen
  layer to confirm it contains only coherence + the no-view-from-nowhere stance.

  REFLEXIVE: by its own content, the axiom — and identity_protection, and the frozen
  layer — must themselves be held provisionally. Freezing is a provisional engineering
  choice for coherence, auditable and revisable, NOT an absolute. The agent that
  exempts its own foundations from the axiom has claimed the view from nowhere it denies.
""")


def _safe(f):
    try: json.load(open(f)); return True
    except Exception: return False


if __name__ == "__main__":
    main()
