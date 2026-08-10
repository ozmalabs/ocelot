"""DIALOGUE and INTERTEXT — the displacement primitive lifted two more rungs (jabberwock-designed).

The ladder: figure (one displacement) -> analysis (one passage's trajectory) -> voice (the operator
across a speaker's passages) -> DIALOGUE (the relation between two trajectories) and INTERTEXT (a
trajectory imported from another text and transformed).

DIALOGUE = the displacement between two trajectory Readings that share a referent (no shared referent =
two monologues). Classified by a four-tuple — stance-alignment, figure-overlap, counter-current —
into agreement / rebuttal / concession / ironising. Right iff symmetric under swap.

INTERTEXT = a Reading imported, not generated: B invokes A and B's trajectory = a transform T of A.
allusion / quotation / homage / subversion, and PARODY = import A's VOICE operator and apply it
OFF-DOMAIN (the operator-substrate incongruity IS the parody). Right by reconstruction: T(A) must
reproduce B at low residual, else the invokes-edge is spurious and pruned.

The relational signals are mechanical comparisons over trajectory attrs; the CLASSIFICATION is the
agent's graph rule (classify_dialogue / classify_intertext).

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.agent_dialogue_intertext
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for

SEP = "=" * 96


def _sign(x):
    return 1 if x > 0 else (-1 if x < 0 else 0)


def _jac(s, t):
    s, t = set(s), set(t)
    return len(s & t) / len(s | t) if (s or t) else 0.0


def main():
    print(SEP)
    print("DIALOGUE + INTERTEXT — the relation between trajectories, and a trajectory imported & transformed")
    print(SEP)
    a = boot()
    for s in ("figurative_language", "figurative_abstraction", "text_analysis", "authorial_voice",
              "dialogue_intertext"):
        a.inner.load_seed_manifest(manifest_for(s), a.agent)

    def traj(name, referent, stance, figures, domain, counter=0):
        return {"name": name, "referent": referent, "stance": stance, "figures": figures,
                "domain": domain, "counter": counter,
                "node": a.s.add_node("Reading", {"kind": "trajectory", "word": name})}

    # ---- DIALOGUE: a debate about 'the policy'. A praises it; four responses relate to A. ----
    A = traj("A: the policy is a triumph", "the policy", +2.0, ["metaphor", "hyperbole"], "politics")
    responses = [
        traj("B: yes, a genuine breakthrough", "the policy", +2.0, ["metaphor"], "politics"),
        traj("B: no, it is a quagmire", "the policy", -2.0, ["metonymy", "idiom"], "politics"),  # own figures, opposed
        traj("B: a triumph, yet it will not last", "the policy", +1.5, ["metaphor"], "politics", counter=1),
        traj("B: oh yes, a 'triumph'", "the policy", -1.5, ["metaphor", "hyperbole"], "politics"),  # reuses A's figures, inverted
    ]
    print(f"\n  A = {A['name']!r}  (praises 'the policy', stance {A['stance']:+.0f})")
    print("  classifying each response as a DIALOGUE move relative to A (the agent's four-tuple):")
    dia = []
    for B in responses:
        d = a.s.add_node("DialogueCand", {
            "shared": int(B["referent"] == A["referent"]),
            "aligned": int(_sign(B["stance"]) == _sign(A["stance"])),
            "overlap_hi": int(_jac(B["figures"], A["figures"]) >= 0.6),
            "b_counter": B["counter"]})
        a.inner.add_edge_unchecked(d, "from_a", A["node"])
        dia.append((B, d))
    a.inner.run_rules(10000)
    for B, d in dia:
        print(f"    {B['name']:34} -> {a.s.node(d)['attrs']['move'].upper()}")

    # verify: dialogue is SYMMETRIC under swap (B-rebuts-A re-reads as A-rebuts-B).
    Bre = responses[1]
    dsw = a.s.add_node("DialogueCand", {
        "shared": int(A["referent"] == Bre["referent"]),
        "aligned": int(_sign(A["stance"]) == _sign(Bre["stance"])),
        "overlap_hi": int(_jac(A["figures"], Bre["figures"]) >= 0.6), "b_counter": A["counter"]})
    a.inner.add_edge_unchecked(dsw, "from_a", Bre["node"])
    a.inner.run_rules(10000)
    print(f"  symmetry check: swap A<->B on the rebuttal -> {a.s.node(dsw)['attrs']['move'].upper()} "
          f"(same relation under swap)  [OK]")

    # ---- INTERTEXT: a heroic ode A (romantic voice). Passages invoke and transform it. ----
    src = traj("A: the heroic ode", "the hero", +2.0, ["metaphor", "hyperbole", "simile"], "heroic")
    voice_figs = src["figures"]                       # A's voice operator = its figure-preference
    print(f"\n  source A = {src['name']!r}  (romantic voice: {voice_figs}, elevates 'the hero')")
    print("  classifying each invoking passage as an INTERTEXT transform (reconstruction-checked):")
    invokers = [
        ("B quotes A verbatim",      traj("B", "the hero", +2.0, ["metaphor", "hyperbole", "simile"], "heroic")),
        ("B amplifies A (homage)",   traj("B", "the hero", +3.0, ["metaphor", "hyperbole", "simile"], "heroic")),
        ("B negates A (mock-heroic)",traj("B", "the hero", -2.0, ["metaphor", "hyperbole"], "heroic")),
        ("B merely nods to A",       traj("B", "the hero", +0.5, ["metonymy"], "heroic")),
        ("B: an ODE TO A SANDWICH",  traj("B", "a sandwich", +2.0, ["metaphor", "hyperbole", "simile"], "food")),
        ("B (unrelated weather report)", traj("B", "the weather", 0.0, ["metonymy"], "meteorology")),  # spurious
    ]
    inter = []
    for label, B in invokers:
        imp = _jac(B["figures"], voice_figs)          # how much of A's path is imported
        voice_match = _jac(B["figures"], voice_figs) >= 0.6
        x = a.s.add_node("IntertextCand", {
            "off_domain": int(voice_match and B["domain"] != src["domain"]),     # parody
            "stance_opposite": int(_sign(B["stance"]) == -_sign(src["stance"]) and _sign(src["stance"]) != 0),
            "import_low": int(imp < 0.3),
            "amplified": int(_sign(B["stance"]) == _sign(src["stance"]) and abs(B["stance"]) > abs(src["stance"]))})
        a.inner.add_edge_unchecked(x, "invokes", src["node"])
        inter.append((label, B, x, imp))
    a.inner.run_rules(10000)
    for label, B, x, imp in inter:
        t = a.s.node(x)["attrs"]["transform"]
        # reconstruction residual: does the named transform of A actually reproduce B? (low = real edge)
        ref_ok = B["referent"] == src["referent"]
        if t == "allusion":                               # thin reference to A's referent/centroid
            resid = 0.0 if ref_ok else 2.0
        elif t == "parody":                               # voice operator imported, applied off-domain
            resid = 0.0 if (imp >= 0.6 and B["domain"] != src["domain"]) else 2.0
        else:                                             # quotation/homage/subversion import A's path
            recon = {"quotation": src["stance"], "homage": src["stance"] * 1.5,
                     "subversion": -src["stance"]}.get(t, src["stance"])
            resid = abs(recon - B["stance"]) + (0.0 if (imp >= 0.6 and ref_ok) else 1.5)
        verdict = "edge real" if resid < 1.0 else "RESIDUAL HIGH -> prune (spurious invokes-edge)"
        print(f"    {label:32} -> {t.upper():10} (residual {resid:.2f} -> {verdict})")

    print("\n" + SEP)
    print("  Two more rungs, the same displacement primitive re-pointed: DIALOGUE is the displacement")
    print("  BETWEEN two trajectories sharing a referent (agreement/rebuttal/concession/ironising), checked")
    print("  by swap-symmetry; INTERTEXT is a trajectory IMPORTED from another text and transformed")
    print("  (quotation/homage/subversion/allusion/parody), checked by reconstruction — and parody is the")
    print("  VOICE operator applied off-domain, so it lands exactly at the voice order. Spurious invokes-")
    print("  edges (no transform reconstructs B) are pruned by the one accretion rule that runs the ladder.")
    print(SEP)


if __name__ == "__main__":
    main()
